"""dp_nes_run.py: phase 3a step 2. NES controller driving dp_env.run, plus the stand-in on the
same settings for comparison, plus the NES step-response latency.

  python3 dp_nes_run.py --latency [--reps 5]
  python3 dp_nes_run.py --run --T 10 --delay 2 --seed 0 [--budget-min 40]
  python3 dp_nes_run.py --standin --T 10 --delay 2 --seed 0
Private stack only (dp_nes.HOST/PORT = 127.0.0.1:8100). Results in output/ (gitignored).

Budget handling: dp_env.run has no wall-clock limit. When the budget runs out the NES
controller raises StopRun, and the episode is REPLAYED (env and disturbance are seeded and
deterministic) with the recorded forces for the ticks that were completed, T = ticks*ctrl_dt, so
the metrics cover exactly the simulated time reached. The replay checks that the observations
match the recorded ones.
"""
import argparse
import json
import os
import time

import numpy as np

import dp_nes
from dp_env import run, DisturbanceCfg
from dp_spiking import SpikingController, load_recipe

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'output')
KEYS = ['upright_frac', 'rms_th1_deg', 'rms_th2_deg', 'rms_force_N', 'max_abs_force_N',
        'max_cart_drift_m', 'rms_x_m', 'fall_time_s']


class StopRun(Exception):
    pass


class Recorder:
    """Wraps a controller: records obs and force per tick, enforces a wall-clock budget."""

    def __init__(self, ctl, budget_s=None):
        self.ctl, self.budget_s = ctl, budget_s
        self.obs, self.F, self.wall = [], [], []
        self.t0 = time.perf_counter()

    def __call__(self, obs):
        if self.budget_s is not None and time.perf_counter() - self.t0 > self.budget_s:
            raise StopRun()
        t = time.perf_counter()
        f = self.ctl(obs)
        self.obs.append(np.array(obs, float))
        self.F.append(f)
        self.wall.append(time.perf_counter() - t)
        return f


class Replay:
    def __init__(self, obs, F):
        self.obs, self.F, self.k, self.max_err = obs, F, 0, 0.0

    def __call__(self, obs):
        self.max_err = max(self.max_err, float(np.abs(np.array(obs) - self.obs[self.k]).max()))
        f = self.F[self.k]
        self.k += 1
        return f


def latency(reps=5, nzero=6, nstep=8):
    """NES step response: state 0 for nzero ticks, then all six states at 0.5 sigma aligned to
    give a positive force for nstep ticks; repeated reps times on ONE network. Same
    normalisation as dp_phase2.latency (per-tick force / steady force, steady = mean of
    ticks 2..7, an even number so the 2-tick ripple cancels)."""
    rec = load_recipe()
    ctl, net = dp_nes.make_controller('johnjose-dp-latency', seed=0, rec=rec)
    K, sg = np.array(rec['K']), np.array(rec['sigma'])
    s = 0.5 * sg * np.sign(-K)
    Y, Z = [], []
    for _ in range(reps):
        Z += [ctl(np.zeros(6)) for _ in range(nzero)]
        Y.append([ctl(s) for _ in range(nstep)])
    Y = np.array(Y)
    y = Y.mean(0)
    steady = y[2:].mean()
    frac = y / steady
    lag = float(np.sum(1 - frac[:2]))
    res = dict(per_tick_fraction=frac.tolist(), steady_force_N=float(steady),
               want_force_N=float(-K @ s), extra_lag_ticks=lag, total_latency_ticks=1.0 + lag,
               per_rep_first_ticks=Y[:, :3].tolist(), zero_state_force_mean_N=float(np.mean(Z)),
               zero_state_force_sd_N=float(np.std(Z)), reps=reps,
               mean_tick_wall_s=float(np.mean(ctl.t_total)))
    return res


def calibrate(nstates=24, nticks=4, seed=7):  # verification of A2: --calib-seed 8
    """Static gain of the NES net: random states ~ N(0,(0.5 sigma)^2) (the A1 recipe of the
    stand-in, different seed from every eval seed 0,1,2), nticks each, the last 2 ticks averaged
    (the 2-tick ripple cancels in a 2-tick mean). Regression through the origin of measured
    force on the target force -K s. Also 20 zero-state ticks first (clean: nothing preceding)."""
    rec = load_recipe()
    ctl, net = dp_nes.make_controller('johnjose-dp-calib', seed=0, rec=rec)
    K, sg = np.array(rec['K']), np.array(rec['sigma'])
    rng = np.random.default_rng(seed)
    z = np.array([ctl(np.zeros(6)) for _ in range(20)])
    want, got = [], []
    for _ in range(nstates):
        s = 0.5 * sg * rng.standard_normal(6)
        f = [ctl(s) for _ in range(nticks)]
        want.append(float(-K @ s))
        got.append(float(np.mean(f[-2:])))
    want, got = np.array(want), np.array(got)
    slope = float((want @ got) / (want @ want))
    rmse = float(np.sqrt(np.mean((got - slope * want) ** 2)))
    return dict(zero_force_mean_N=float(z[4:].mean()), zero_force_sd_N=float(z[4:].std()),
                slope_measured_over_target=slope, rmse_after_slope_N=float(rmse),
                rmse_raw_N=float(np.sqrt(np.mean((got - want) ** 2))), want=want.tolist(), got=got.tolist(),
                c_N_per_spike=rec['c_N_per_spike'], c_adjust_in_effect=dp_nes.C_NES_ADJUST, seed=seed, mean_tick_wall_s=float(np.mean(ctl.t_total)))


def metrics(m):
    return {k: m[k] for k in KEYS}


def run_nes(T, delay, seed, budget_min, name):
    rec = load_recipe()
    ctl, net = dp_nes.make_controller(name, seed=seed, rec=rec)
    print('built in %.1f s' % net['build_s'], flush=True)
    rc = Recorder(ctl, budget_s=budget_min * 60.0 if budget_min else None)
    t0 = time.perf_counter()
    completed = True
    try:
        m = run(rc, T=T, seed=seed, ctrl_dt=0.01, delay=delay, disturbance=DisturbanceCfg())
    except StopRun:
        completed = False
        n = len(rc.F)
        print('budget reached after %d ticks (%.2f s simulated); replaying' % (n, n * 0.01), flush=True)
        rp = Replay(rc.obs, rc.F)
        m = run(rp, T=n * 0.01, seed=seed, ctrl_dt=0.01, delay=delay, disturbance=DisturbanceCfg())
        assert rp.k == n and rp.max_err < 1e-9, ('replay mismatch', rp.k, n, rp.max_err)
    wall = time.perf_counter() - t0
    ticks = len(rc.F)
    L = ctl.loop
    out = dict(kind='nes', T_requested=T, T_simulated=ticks * 0.01, completed=completed, ticks=ticks,
               delay=delay, seed=seed, wall_s=wall, build_s=net['build_s'], metrics=m,
               enc_clipped_ticks=ctl.enc.n_clipped, mean_spikes_per_tick=ctl.n_spikes / max(1, ticks),
               tick_wall_s_mean=float(np.mean(rc.wall)),
               sched_ms=float(np.mean(L.t_sched) * 1000), run_ms=float(np.mean(L.t_run) * 1000),
               read_ms=float(np.mean(L.t_read) * 1000),
               tick_wall_s_by_100=[float(np.mean(rc.wall[i:i + 100])) for i in range(0, ticks, 100)],
               force=[float(f) for f in rc.F])
    return out


def run_standin(T, delay, seed):
    ctl = SpikingController(load_recipe(), seed=seed)
    t0 = time.perf_counter()
    m = run(ctl, T=T, seed=seed, ctrl_dt=0.01, delay=delay, disturbance=DisturbanceCfg())
    return dict(kind='standin', T_simulated=T, delay=delay, seed=seed, wall_s=time.perf_counter() - t0,
                metrics=m, enc_clipped_ticks=ctl.enc.n_clipped,
                mean_spikes_per_tick=ctl.n_spikes / max(1, ctl.enc.n_calls))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--latency', action='store_true')
    ap.add_argument('--calibrate', action='store_true')
    ap.add_argument('--calib-seed', type=int, default=7)
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--standin', action='store_true')
    ap.add_argument('--T', type=float, default=10.0)
    ap.add_argument('--delay', type=int, default=2)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--reps', type=int, default=5)
    ap.add_argument('--budget-min', type=float, default=40.0)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.latency:
        r = latency(a.reps)
        print(json.dumps(r, indent=1))
        json.dump(r, open(a.out or os.path.join(OUT, 'nes_latency.json'), 'w'), indent=1)
    if a.calibrate:
        r = calibrate(seed=a.calib_seed)
        print(json.dumps(r, indent=1))
        json.dump(r, open(a.out or os.path.join(OUT, 'nes_calib.json'), 'w'), indent=1)
    if a.standin:
        r = run_standin(a.T, a.delay, a.seed)
        print(json.dumps(metrics(r['metrics']), indent=1))
        json.dump(r, open(a.out or os.path.join(OUT, 'standin_T%g_d%d_s%d.json' % (a.T, a.delay, a.seed)), 'w'), indent=1)
    if a.run:
        r = run_nes(a.T, a.delay, a.seed, a.budget_min, 'johnjose-dp-run-s%d' % a.seed)
        print(json.dumps({k: v for k, v in r.items() if k != 'force'}, indent=1))
        json.dump(r, open(a.out or os.path.join(OUT, 'nes_T%g_d%d_s%d.json' % (a.T, a.delay, a.seed)), 'w'), indent=1)
