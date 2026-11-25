"""fresh_scout: offline sweep of the firing-threshold requirement T (neuron-parameter lever: Cm, Vth-Vrest). Same R3-like rules as lp_weights
with T scaled: cue pair >= T/4, full cue sum >= T, unintended input limit theta = 0.75 T, hub cap H = 49.5 nS FIXED (not scaled), lower weight bound 0.1.
Greedy packer (3 restarts), disjoint (k=0) and overlap<=2 (k=2), six-cell memories (4 cue + 2 targets). Exploratory, threshold model only, NOT preregistered."""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
import lpw_lib as L
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
out = {}
for Tn in (16.5, 13.0, 10.0, 8.0):
    L.T = Tn
    for k in KEYS:
        G = L.load(k); cfg = L.Cfg(G, theta=0.75 * Tn, H=49.5, lbw=0.1)
        cand = L.candidates(cfg, 2); res = {'strong_frac': float(((G >= Tn / 4) & (G > 0)).sum() / (96 * 95)), 'n_cand': len(cand)}
        for kk in (0, 2):
            best = 0
            if cand:
                for sd in range(3):
                    mem, F = L.pack(cfg, cand, 2, kk, sd, max_rej=400, max_mem=60); best = max(best, len(mem))
            res['k%d' % kk] = best
        out['%s_T%s' % (k, Tn)] = res; print(Tn, k, res, flush=True)
json.dump(out, open('tsweep.json', 'w'), indent=1)
