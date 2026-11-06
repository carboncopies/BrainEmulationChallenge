"""dp_nes_equiv.py: drive the phase-2 NES net with a fixed, deterministic observation sequence and
record, per tick, the windowed output spikes (222 outputs), the decoded force and the schedule/run/read
wall times. Run the same script against two NES binaries (private stack 8100 only) and compare with
dp_nes_compare.py.

  ~/BrainGenix/BrainEmulationChallenge/venv/bin/python dp_nes_equiv.py --tag base --ticks 700

Observation sequence (all seeded, identical for every run): ticks 1-300 random 0.5 sigma N(0,1) per tick
(seed 1, as dp_nes_speed.py); ticks 301-450 six static states held 25 ticks each (the calibrate() recipe:
0.5 sigma N(0,1), seed 7); ticks 451-N random again (seed 2).
"""
import argparse
import json
import os
import time

import numpy as np

import dp_nes
from dp_spiking import load_recipe

HERE = os.path.dirname(os.path.abspath(__file__))


def obs_sequence(n, sig):
    r1 = np.random.default_rng(1)
    r7 = np.random.default_rng(7)
    r2 = np.random.default_rng(2)
    static = [0.5 * sig * r7.standard_normal(6) for _ in range(6)]
    out = []
    for k in range(1, n + 1):
        if k <= 300:
            out.append(0.5 * sig * r1.standard_normal(6))
        elif k <= 450:
            out.append(static[(k - 301) // 25])
        else:
            out.append(0.5 * sig * r2.standard_normal(6))
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--ticks', type=int, default=700)
    a = ap.parse_args()
    rec = load_recipe()
    ctl, net = dp_nes.make_controller('johnjose-dp-equiv-' + a.tag, seed=0, rec=rec, read='window')
    print('build %.1f s' % net['build_s'], flush=True)
    obs = obs_sequence(a.ticks, np.array(rec['sigma']))
    forces, sp_tick, sp_nidx, sp_t = [], [], [], []
    out_ids = ctl.loop.out_ids
    t0 = time.perf_counter()
    for k in range(1, a.ticks + 1):
        f = ctl(obs[k - 1])
        forces.append(f)
        for j, nid in enumerate(out_ids):
            for t in ctl.loop.last_window[nid]:
                sp_tick.append(k)
                sp_nidx.append(j)
                sp_t.append(t)
        if k % 50 == 0:
            L = ctl.loop
            w = lambda x: 1000 * float(np.mean(x[k - 50:k]))
            print('tick %d sched %.1f run %.1f read %.1f total %.1f ms wall %.0f s' % (
                k, w(L.t_sched), w(L.t_run), w(L.t_read), w(ctl.t_total), time.perf_counter() - t0), flush=True)
    L = ctl.loop
    np.savez(os.path.join(HERE, 'output', 'equiv_%s.npz' % a.tag), force=np.array(forces),
             sp_tick=np.array(sp_tick), sp_nidx=np.array(sp_nidx), sp_t=np.array(sp_t),
             t_sched=np.array(L.t_sched), t_run=np.array(L.t_run), t_read=np.array(L.t_read),
             t_total=np.array(ctl.t_total), n_pairs=np.array(L.n_pairs))
    print('done wall %.0f s, %d output spikes' % (time.perf_counter() - t0, len(sp_t)), flush=True)
