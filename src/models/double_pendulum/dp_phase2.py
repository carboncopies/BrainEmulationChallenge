"""dp_phase2.py: phase 2 evaluation. 180 s, disturbance on, seeds 0,1,2, ctrl_dt 10 ms.
(a) spiking controller (hand-derived weights_recipe.json) and (b) plain LQR 10 ms gain, both
with the same actuation delay (ticks).

  python3 dp_phase2.py [--delay D] [--T 180] [--seeds 3] [--jobs 2]
  python3 dp_phase2.py --latency        # measure the stand-in's step-response latency
Writes output/phase2.json (or output/latency.json).
"""
import argparse
import json
import os
from multiprocessing import Pool

import numpy as np

from dp_env import run, DisturbanceCfg
from dp_lqr import dlqr, StateFeedback
from dp_spiking import SpikingController, load_recipe

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = ['upright_frac', 'rms_th1_deg', 'rms_th2_deg', 'rms_force_N', 'max_abs_force_N',
        'max_cart_drift_m', 'rms_x_m']


def one(job):
    kind, seed, delay, T = job
    if kind == 'spiking':
        ctl = SpikingController(load_recipe(), seed=seed)
    else:
        ctl = StateFeedback(dlqr(ctrl_dt=0.01)[0])
    m = run(ctl, T=T, seed=seed, ctrl_dt=0.01, delay=delay, disturbance=DisturbanceCfg())
    if kind == 'spiking':
        m['enc_clipped_ticks'] = ctl.enc.n_clipped
        m['enc_ticks'] = ctl.enc.n_calls
        m['mean_spikes_per_tick'] = ctl.n_spikes / max(1, ctl.enc.n_calls)
    return kind, seed, m


def latency(trials=200):
    """Step response of the stand-in: state 0 -> s (all six at 0.5 sigma, aligned to give
    a positive force), per-tick mean force over trials, normalised by the steady value."""
    rec = load_recipe()
    K = np.array(rec['K'])
    sg = np.array(rec['sigma'])
    s = 0.5 * sg * np.sign(-K) * 1.0   # each term pushes force the same way
    n = 8
    Y = np.zeros((trials, n))
    for t in range(trials):
        c = SpikingController(rec, seed=t)
        for _ in range(20):
            c(np.zeros(6))
        Y[t] = [c(s) for _ in range(n)]
    y = Y.mean(0)
    steady = y[2:].mean()   # even number of ticks: the 2-tick ripple cancels
    frac = y / steady
    zero = 0.0
    lag_ticks = float(np.sum(1 - frac[:2]))   # extra lag beyond the one-tick window
    return dict(per_tick_fraction=frac.tolist(), steady_force_N=float(steady),
                want_force_N=float(-K @ s), extra_lag_ticks=lag_ticks,
                total_latency_ticks=1.0 + lag_ticks)


def table(res, delay):
    print('delay %d ticks, ctrl_dt 10 ms, disturbance on' % delay)
    print('%-9s %5s %6s %6s %6s %6s %6s %6s  %s' % ('ctrl', 'seed', 'upr', 'th1', 'th2', 'rmsF', 'maxF', 'drift', 'fall s'))
    for kind in ('spiking', 'lqr'):
        for r in sorted([r for r in res if r['kind'] == kind], key=lambda r: r['seed']):
            m = r['m']
            print('%-9s %5d %6.3f %6.2f %6.2f %6.2f %6.2f %6.2f  %s' % (
                kind, r['seed'], m['upright_frac'], m['rms_th1_deg'], m['rms_th2_deg'],
                m['rms_force_N'], m['max_abs_force_N'], m['max_cart_drift_m'],
                '-' if m['fall_time_s'] is None else '%.2f' % m['fall_time_s']))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--delay', type=int, default=None)
    ap.add_argument('--T', type=float, default=180.0)
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--latency', action='store_true')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    os.makedirs(os.path.join(HERE, 'output'), exist_ok=True)
    if a.latency:
        r = latency()
        print(json.dumps(r, indent=1))
        json.dump(r, open(os.path.join(HERE, 'output', 'latency.json'), 'w'), indent=1)
        raise SystemExit
    delay = a.delay if a.delay is not None else load_recipe()['latency_ticks_assumed']
    jobs = [(k, s, delay, a.T) for k in ('spiking', 'lqr') for s in range(a.seeds)]
    with Pool(a.jobs) as p:
        out = p.map(one, jobs)
    res = [dict(kind=k, seed=s, m=m) for k, s, m in out]
    table(res, delay)
    json.dump(dict(delay_ticks=delay, T=a.T, results=res),
              open(a.out or os.path.join(HERE, 'output', 'phase2.json'), 'w'), indent=1)
