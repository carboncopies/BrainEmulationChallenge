"""fresh_scout: same graphs as prune_p29.py but counted with the R3-equivalent rule set (lp_weights R3EQ: every cue pair >= 4.125, outsiders < 16.4, no input cap) = the counting convention of
headline_i/capacity_d (disjoint = k0). 5 restarts. Exploratory."""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_scout'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
import lpw_lib as L
import importlib.util
src = open('prune_p29.py').read().split("out = {}; rs")[0]; exec(src)
out = {}; rs = np.random.RandomState(7)
for seed in ('33333', '44444'):
    srcs = {'base': H + 'headline_i/grow_V1n20_s%s_p0d0175_i0d03/viz/sample_0000.json' % seed, 'B1': R + 'grow_B1_s%s/viz/sample_0000.json' % seed, 'B2': R + 'grow_B2_s%s/viz/sample_0000.json' % seed}
    for name, p in srcs.items():
        G, n = Gof(p); variants = {'unpruned': G}
        if name != 'base': variants['P29'] = prune(G, n, 0.29, rs)
        for v, Gv in variants.items():
            cfg = L.Cfg(Gv, **L.R3EQ); res = {}
            for m in (2, 4):
                cand = L.candidates(cfg, m)
                for kk in (0, 2):
                    res['m%d_k%d' % (m, kk)] = max([len(L.pack(cfg, cand, m, kk, sd, max_rej=600, max_mem=120)[0]) for sd in range(5)]) if cand else 0
            res.update(stats(Gv, n)); key = '%s_%s_%s' % (seed, name, v); out[key] = res; print(key, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in res.items()}, flush=True)
json.dump(out, open('prune_r3.json', 'w'), indent=1)
