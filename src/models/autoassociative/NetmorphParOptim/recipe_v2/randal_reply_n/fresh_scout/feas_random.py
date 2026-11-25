"""fresh_scout: how many RANDOM patterns could be stored if weights were learned to saturation (weight 1 -> conductance = min(G, 6.86) per pair)?
Monte Carlo on the 10 grown E4 Pyr->Pyr graphs, threshold model only. A pattern = cue set C (c cells) + target set N (n cells), all distinct, random.
feasible_full: every target gets sum_{cue} U >= T   (full cue completes).
feasible_k:    every target gets the SMALLEST k-of-c sum (worst k cue cells present) >= T  (completes from ANY k of the c cue cells = partial-cue completion).
U = min(G, 6.86). No design freedom (no choice of cells, no weight choice), i.e. what STDP-to-saturation on arbitrary presented patterns could at best give. Exploratory."""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
import lpw_lib as L
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
rs = np.random.RandomState(1); NS = 400000; out = {}
CFG = [(4, 2, 4), (4, 4, 4), (8, 2, 4), (8, 2, 8), (12, 2, 6), (17, 2, 9)]   # (c, n, k): k = number of cue cells that must suffice
for Tn in (16.5, 10.0):
    for key in KEYS:
        G = L.load(key); U = np.minimum(G, 6.86); res = {}
        for c, n, k in CFG:
            cnt_full = 0; cnt_k = 0
            for _ in range(NS // 20000):
                P = np.argsort(rs.rand(20000, 96), axis=1)[:, :c + n]; C = P[:, :c]; N = P[:, c:]
                # vals[s, t, i] = U[C[s,i], N[s,t]]
                v = U[C[:, None, :], N[:, :, None]]          # (S, n, c)
                full = (v.sum(2) >= Tn - 1e-9).all(1)
                vs = np.sort(v, axis=2)[:, :, :k].sum(2)      # smallest k contributions
                part = (vs >= Tn - 1e-9).all(1)
                cnt_full += int(full.sum()); cnt_k += int(part.sum())
            res['c%d_n%d_k%d' % (c, n, k)] = dict(full=cnt_full / NS, anyk=cnt_k / NS)
        out['%s_T%s' % (key, Tn)] = res
    print('T', Tn, 'done', flush=True)
json.dump(out, open('feas_random.json', 'w'), indent=1)
