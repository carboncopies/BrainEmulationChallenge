"""fresh_scout: heavy-tailed per-synapse strengths (mean-preserving lognormal) instead of 0.98 nS per synapse. Pair conductance G' = sum of n lognormal strengths (mean 0.98 nS,
sigma_ln in {0.5, 0.9, 1.3}); n = round(G / 0.98) from the grown E4 graphs. Same primary packer as lp_weights (T 16.5, theta 12.375, H 49.5, pair cap 6.86), 3 restarts, six-cell memories.
One random draw per (model, sigma) (seed 11). Offline, threshold model only; the lognormal sigma is NOT sourced yet (see FRESH.md). Exploratory."""
import sys, json, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
import lpw_lib as L
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
rs = np.random.RandomState(11); out = {}
for sig in (0.0, 0.5, 0.9, 1.3):
    for key in KEYS:
        G = L.load(key); n = np.rint(G / 0.98).astype(int); Gn = np.zeros_like(G); mx = 0.0
        if sig == 0: Gn = G.copy()
        else:
            mu = np.log(0.98) - sig ** 2 / 2
            for i, j in zip(*np.nonzero(n)):
                s = rs.lognormal(mu, sig, n[i, j]); Gn[i, j] = s.sum(); mx = max(mx, s.max())
        cfg = L.Cfg(Gn, **L.PRIMARY); cand = L.candidates(cfg, 2); res = dict(strong_pairs=int((Gn >= 4.125).sum()), n_cand=len(cand), max_single_synapse_nS=mx, mean_pair=float(Gn[Gn > 0].mean()))
        for kk in (0, 2): res['k%d' % kk] = max([len(L.pack(cfg, cand, 2, kk, sd, max_rej=400, max_mem=80)[0]) for sd in range(3)]) if cand else 0
        out['%s_sig%s' % (key, sig)] = res; print(sig, key, res, flush=True)
json.dump(out, open('lognorm.json', 'w'), indent=1)
