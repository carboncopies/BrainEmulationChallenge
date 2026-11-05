"""dp_nes_speed.py: phase 3a step 1. Build the phase-2 network in NES (private stack, 8100),
time the per-control-tick wall cost split into schedule / run / spike-read, check how it grows.

  python3 dp_nes_speed.py [--ticks 300] [--probes 1,50,100,200,300] [--out output/nes_speed.json]
Observations are a seeded random vector 0.5 sigma * N(0,1) per tick, so the outputs fire at
a realistic rate (the exact controller closed loop is dp_nes_run.py / step 2).
"""
import argparse
import json
import os
import time

import numpy as np

import dp_nes
from dp_spiking import load_recipe

HERE = os.path.dirname(os.path.abspath(__file__))


def stats(a):
    a = np.asarray(a) * 1000.0
    return dict(mean_ms=float(a.mean()), p50_ms=float(np.percentile(a, 50)),
                p95_ms=float(np.percentile(a, 95)), max_ms=float(a.max()))


def window(a, lo, hi):
    return float(np.mean(np.asarray(a[lo - 1:hi]))) * 1000.0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--ticks', type=int, default=300)
    ap.add_argument('--probes', default='1,50,100,200,300')
    ap.add_argument('--out', default=os.path.join(HERE, 'output', 'nes_speed.json'))
    ap.add_argument('--name', default='johnjose-dp-speed')
    ap.add_argument('--read', default=None, choices=['full', 'window', 'none'])
    ap.add_argument('--noread', action='store_true', help='diagnostic: never call GetSpikeTimes (does the run time still grow?)')
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    rec = load_recipe()
    ctl, net = dp_nes.make_controller(a.name, seed=0, rec=rec, read=a.read or ('none' if a.noread else 'full'))
    print('build %.1f s: %d neurons, %d receptors, w_eff %.3f..%.3f nS (charge scale %.4f)' % (
        net['build_s'], net['n_neurons'], net['n_receptors'], net['w_eff_min'], net['w_eff_max'],
        dp_nes.CHARGE_SCALE))
    sig = np.array(rec['sigma'])
    rng = np.random.default_rng(1)
    probes = set(int(x) for x in a.probes.split(',') if x)
    probe_out = {}
    sched_total = 0
    t_wall0 = time.perf_counter()
    for k in range(1, a.ticks + 1):
        f = ctl(0.5 * sig * rng.standard_normal(6))
        sched_total += ctl.loop.n_pairs[-1]
        if k in probes and not a.noread and a.read != 'window':
            probe_out[k] = ctl.loop.raw_history_probe()
            print('tick %d: history %s' % (k, probe_out[k]))
        if k % 50 == 0:
            L = ctl.loop
            print('tick %d: last50 sched %.1f run %.1f read %.1f ms, total/tick %.1f ms, force %.2f, spikes %s' % (
                k, window(L.t_sched, k - 49, k), window(L.t_run, k - 49, k), window(L.t_read, k - 49, k),
                window(ctl.t_total, k - 49, k), f, ctl.last))
    L = ctl.loop
    tot = np.array(ctl.t_total)
    res = dict(ticks=a.ticks, build_s=net['build_s'], n_neurons=net['n_neurons'],
               n_receptors=net['n_receptors'], charge_scale=dp_nes.CHARGE_SCALE,
               schedule=stats(L.t_sched), run=stats(L.t_run), read=stats(L.t_read),
               total=stats(tot), pairs_per_tick_mean=float(np.mean(L.n_pairs)),
               windows={}, probes=probe_out)
    n = a.ticks
    for lo, hi in ((1, 50), (n - 49, n)):
        res['windows']['%d-%d' % (lo, hi)] = dict(
            schedule_ms=window(L.t_sched, lo, hi), run_ms=window(L.t_run, lo, hi),
            read_ms=window(L.t_read, lo, hi), total_ms=window(tot, lo, hi))
    # linear fit of total per-tick time vs tick index
    x = np.arange(1, n + 1)
    for name, arr in (('schedule', L.t_sched), ('run', L.t_run), ('read', L.t_read), ('total', tot)):
        slope, icpt = np.polyfit(x, np.asarray(arr) * 1000.0, 1)
        res['fit_' + name] = dict(slope_ms_per_tick=float(slope), intercept_ms=float(icpt))
    # check that every scheduled input spike was recorded
    pr = None if (a.noread or a.read == 'window') else L.raw_history_probe()
    res['final_probe'] = pr
    res['read_mode'] = a.read or ('none' if a.noread else 'full')
    res['window_response_bytes_last'] = getattr(L, 'last_bytes', None)
    res['scheduled_input_spikes'] = int(sched_total)
    res['sim_time_ms'] = L.t_ms
    res['wall_s'] = time.perf_counter() - t_wall0
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'probes'}, indent=1))
