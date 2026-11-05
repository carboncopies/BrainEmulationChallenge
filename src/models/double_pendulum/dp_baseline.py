"""dp_baseline.py: LQR baseline table (180 s, 3 seeds per condition).

Usage: python3 dp_baseline.py [--T 180] [--seeds 3] [--jobs 2] [--no-probe]
Writes output/baseline.json and prints tables. Disturbance is the default
DisturbanceCfg (see dp_env.py). 'plain' = gain designed for ctrl_dt, ignores
the actuation delay; 'aware' = delay-augmented design (remembers pending
commands). 'holds' = all seeds: no fall and upright_frac >= 0.99.
"""
import argparse
import json
import os
from multiprocessing import Pool

import numpy as np

from dp_env import DisturbanceCfg, run
from dp_lqr import (dlqr, StateFeedback, DelayAwareLQR, ZeroForce, DEFAULT_Q,
                    DEFAULT_R)

KEYS = ['upright_frac', 'rms_th1_deg', 'rms_th2_deg', 'rms_force_N',
        'max_abs_force_N', 'max_cart_drift_m', 'rms_x_m']


def one(job):
    name, kind, ctrl_ms, delay, dist, seed, T = job
    h = ctrl_ms / 1000.0
    if kind == 'zero':
        ctrl = ZeroForce()
    elif kind == 'plain' or delay == 0:
        ctrl = StateFeedback(dlqr(ctrl_dt=h)[0])
    else:
        ctrl = DelayAwareLQR(dlqr(ctrl_dt=h, delay=delay)[0], delay)
    m = run(ctrl, T=T, seed=seed, ctrl_dt=h, delay=delay,
            disturbance=DisturbanceCfg() if dist else None)
    return job[:5], m


def aggregate(ms):
    out = {k: float(np.mean([m[k] for m in ms])) for k in KEYS}
    ft = [m['fall_time_s'] for m in ms]
    out['fall_times_s'] = ft
    out['n_fell'] = sum(f is not None for f in ft)
    out['holds'] = bool(out['n_fell'] == 0 and all(m['upright_frac'] >= 0.99 for m in ms))
    return out


def fmt_ft(a):
    fs = [('%.2f' % f) if f is not None else '-' for f in a['fall_times_s']]
    return '/'.join(fs)


def table(rows):
    hdr = ('%-34s %6s %6s %6s %6s %6s %6s %6s  %s' %
           ('condition', 'upr', 'th1', 'th2', 'rmsF', 'maxF', 'drift', 'rmsX', 'fall s (per seed)'))
    print(hdr)
    for name, a in rows:
        print('%-34s %6.3f %6.2f %6.2f %6.2f %6.2f %6.2f %6.3f  %s%s' % (
            name, a['upright_frac'], a['rms_th1_deg'], a['rms_th2_deg'],
            a['rms_force_N'], a['max_abs_force_N'], a['max_cart_drift_m'],
            a['rms_x_m'], fmt_ft(a), '' if a['holds'] else '  [FAILS]'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--T', type=float, default=180.0)
    ap.add_argument('--seeds', type=int, default=3)
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--no-probe', action='store_true')
    a = ap.parse_args()
    seeds = range(a.seeds)

    confs = [('lqr, no disturbance', 'plain', 5, 0, False),
             ('lqr, disturbance', 'plain', 5, 0, True),
             ('zero force, disturbance', 'zero', 5, 0, True)]
    main_grid = [(c, d) for c in (5, 10, 20) for d in (0, 1, 2)]
    ceil_grid = [(c, d) for c in (5, 10, 20, 30, 40) for d in (0, 1, 2, 3, 4)]
    grid = main_grid if a.no_probe else ceil_grid
    for c, d in grid:
        confs.append(('plain c%d d%d' % (c, d), 'plain', c, d, True))
        if d > 0:
            confs.append(('aware c%d d%d' % (c, d), 'aware', c, d, True))
    jobs = [(n, k, c, d, ds, s, a.T) for (n, k, c, d, ds) in confs for s in seeds]
    with Pool(a.jobs) as pool:
        res = pool.map(one, jobs, chunksize=1)
    by = {}
    for key, m in res:
        by.setdefault(key, []).append(m)
    agg = {key[0]: (key, aggregate(ms)) for key, ms in by.items()}

    out = {'T_s': a.T, 'seeds': list(seeds), 'Q': np.diag(DEFAULT_Q).tolist(),
           'R': float(DEFAULT_R[0, 0]), 'disturbance': DisturbanceCfg().__dict__,
           'conditions': {}}
    for name, (key, ag) in agg.items():
        ag.update(kind=key[1], ctrl_dt_ms=key[2], delay_ticks=key[3],
                  disturbance_on=key[4])
        out['conditions'][name] = ag
    # ceiling: largest ctrl_dt that holds at each delay, per design kind
    grid_entries = [(k, g) for n, (k, g) in agg.items()
                    if n.startswith(('plain', 'aware'))]
    ceiling = {}
    for kind in ('plain', 'aware'):
        for d in sorted({k[3] for k, _ in grid_entries}):
            ok = [k[2] for k, g in grid_entries if k[3] == d and g['holds']
                  and (k[1] == kind or d == 0)]
            ceiling['%s_delay%d' % (kind, d)] = max(ok) if ok else None
    out['ceiling_max_ctrl_dt_ms_that_holds'] = ceiling
    os.makedirs('output', exist_ok=True)
    with open('output/baseline.json', 'w') as f:
        json.dump(out, f, indent=1)

    print('Q=diag%s R=%s  T=%gs seeds=%d' % (np.diag(DEFAULT_Q).tolist(), DEFAULT_R[0, 0], a.T, a.seeds))
    print('upr = upright fraction (|th|<=10deg), th1/th2 = rms deg, rmsF/maxF in N,'
          ' drift = max|x| m, rmsX m')
    table([(n, g) for n, (k, g) in agg.items() if k[3] == 0 and k[2] == 5])
    for kind in ('plain', 'aware'):
        print('\n-- %s gain, disturbance on, ctrl_dt (ms) x delay (ticks)' % kind)
        table([(n, g) for n, (k, g) in agg.items() if n.startswith(kind)])
    print('\nceiling (max ctrl_dt ms that holds, disturbance on):')
    for k, v in ceiling.items():
        print('  %-16s %s' % (k, v))
    print('wrote output/baseline.json')


if __name__ == '__main__':
    main()
