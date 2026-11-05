"""dp_robust.py: stress tests for the hand-derived spiking controller vs LQR (10 ms gain), both at
the same actuation delay. 180 s, disturbance on, seeds 0-2. Nothing here changes weights, the
recipe, dp_env, dp_spiking or dp_codec; perturbations are applied by wrappers.

  python3 dp_robust.py [--delay 2] [--T 180] [--seeds 3] [--jobs 24] [--only name,name] [--out output/robust.json]

Conditions (name: what):
  base                 nothing (reference, same as phase 2)
  noise_{0.1,0.25,0.5} Gaussian noise on the 6 readings, std = level x sigma_i (sigma_i from
                       weights_recipe.json, the closed-loop std of each state), own rng so the
                       disturbance kicks are identical to the baseline run of the same seed
  jit_{1,3}ms          every input spike moved by round(N(0, s)) ms inside its 10 ms window
                       (clipped to the window, so counts per window are unchanged); spiking only
  poisson              input trains are Bernoulli per 1 ms step at the same rate (count noise too)
  kick_{2,4}x          cart and torque kick impulse std x2, x4
  off_{0.05,0.1}       start offset: th1 = th2 = value rad (baseline starts at 1 deg = 0.0175 rad)
LQR is unaffected by the two input-timing conditions (it has no spikes); they are run for spiking only.
"""
import argparse
import json
import math
import os
from multiprocessing import Pool

import numpy as np

from dp_env import run, DisturbanceCfg
from dp_lqr import dlqr, StateFeedback
from dp_spiking import SpikingController, load_recipe, STEPS
from dp_codec import DifferentialEncoder

HERE = os.path.dirname(os.path.abspath(__file__))


class JitterEncoder(DifferentialEncoder):
    """Regular trains from the parent, then each spike displaced by round(N(0, jit_ms)) ms,
    clipped to the 10 ms window."""

    def __init__(self, *a, jit_ms=1.0, jseed=0, **k):
        super().__init__(*a, **k)
        self.jit = jit_ms
        self.jrng = np.random.default_rng(jseed)

    def spike_trains(self, s, steps):
        reg = super().spike_trains(s, steps)
        idx = np.nonzero(reg)
        d = np.rint(self.jrng.normal(0.0, self.jit, len(idx[0]))).astype(int)
        t = np.clip(idx[1] + d, 0, steps - 1)
        out = np.zeros_like(reg)
        out[idx[0], t] = True       # two spikes landing on one ms step merge (counted once)
        return out


class PoissonEncoder(DifferentialEncoder):
    def __init__(self, *a, jseed=0, **k):
        super().__init__(*a, **k)
        self.jrng = np.random.default_rng(jseed)

    def spike_trains(self, s, steps):
        r = self.rates(s)
        return self.jrng.random((12 * self.n_in, steps)) < np.repeat(r * self.dt * 1e-3, self.n_in)[:, None]


CONDS = {
    'base': {},
    'noise_0.1': dict(noise=0.1), 'noise_0.25': dict(noise=0.25), 'noise_0.5': dict(noise=0.5),
    'jit_1ms': dict(jit=1.0), 'jit_3ms': dict(jit=3.0), 'poisson': dict(poisson=True),
    'kick_2x': dict(kick=2.0), 'kick_4x': dict(kick=4.0),
    'off_0.05': dict(off=0.05), 'off_0.1': dict(off=0.1),
}
INPUT_ONLY = ('jit_1ms', 'jit_3ms', 'poisson')


def one(job):
    kind, cond, seed, delay, T = job
    o = CONDS[cond]
    rec = load_recipe()
    if kind == 'spiking':
        ctl = SpikingController(rec, seed=seed)
        a = (rec['ranges'], rec['r0_hz'], rec['n_in'])
        if 'jit' in o:
            ctl.enc = JitterEncoder(*a, seed=seed, jit_ms=o['jit'], jseed=seed + 7000)
        if o.get('poisson'):
            ctl.enc = PoissonEncoder(*a, seed=seed, jseed=seed + 7000)
        inner = ctl
    else:
        inner = StateFeedback(dlqr(ctrl_dt=0.01)[0])
    if 'noise' in o:
        sd = o['noise'] * np.array(rec['sigma'])
        nrng = np.random.default_rng(seed + 5000)
        ctl_fn = lambda obs: inner(obs + nrng.normal(0.0, 1.0, 6) * sd)
    else:
        ctl_fn = inner
    k = o.get('kick', 1.0)
    base = DisturbanceCfg()
    dist = DisturbanceCfg(cart_impulse=base.cart_impulse * k, torque_impulse=base.torque_impulse * k)
    x0 = None
    if 'off' in o:
        x0 = [0, o['off'], o['off'], 0, 0, 0]
    m = run(ctl_fn, T=T, seed=seed, ctrl_dt=0.01, delay=delay, disturbance=dist, x0=x0)
    if kind == 'spiking':
        m['enc_clipped_ticks'] = inner.enc.n_clipped
        m['enc_ticks'] = inner.enc.n_calls
    return dict(kind=kind, cond=cond, seed=seed, m=m)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--delay', type=int, default=2)
    ap.add_argument('--T', type=float, default=180.0)
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--jobs', type=int, default=24)
    ap.add_argument('--only', default=None)
    ap.add_argument('--out', default=os.path.join(HERE, 'output', 'robust.json'))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    names = a.only.split(',') if a.only else list(CONDS)
    jobs = [(k, c, s, a.delay, a.T) for c in names for k in ('spiking', 'lqr')
            if not (k == 'lqr' and c in INPUT_ONLY) for s in range(a.seeds)]
    with Pool(a.jobs) as p:
        res = p.map(one, jobs, chunksize=1)
    json.dump(dict(delay_ticks=a.delay, T=a.T, results=res), open(a.out, 'w'), indent=1)
    print('wrote', a.out, len(res), 'runs')
