"""POST-HOC (not preregistered): sensitivity of the distributed-cue result to the silence rule QFRAC and to packer randomness. usage: posthoc_dist.py KEY"""
import sys, json, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/math_run')
import mrlib as M, lpw_lib as L
key = sys.argv[1]; G = L.load(key); cfg = L.Cfg(G, **L.PRIMARY); out = {}; t0 = time.time()
for qf in (0.5, 0.75, 0.875):
    M.QFRAC = qf
    for c in (8, 12, 20):
        cands = M.dist_candidates(cfg, c, nper=4)
        for k in (0, 2):
            counts = []
            for s in range(10):
                mem, F = M.pack_dist(cfg, cands, c, k, 100 + s, max_rej=2000); counts.append(len(mem))
            out['q%.3f_c%d_k%d' % (qf, c, k)] = dict(n_cands=len(cands), counts=counts, best=max(counts), median_restarts=float(np.median(counts)))
            print(key, qf, c, k, len(cands), max(counts), round(time.time() - t0), flush=True)
json.dump(out, open('posthoc_%s.json' % key, 'w'))
