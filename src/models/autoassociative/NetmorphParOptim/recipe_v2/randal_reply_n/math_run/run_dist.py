"""usage: run_dist.py KEY [quick] -> dist_KEY.json. Distributed-cue assemblies (c cue + 2 targets) under the lp_weights constraints. Offline."""
import sys, json, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/math_run')
import mrlib as M, lpw_lib as L
key = sys.argv[1]; quick = len(sys.argv) > 2; G = L.load(key); t0 = time.time(); out = {}
NREST = 2 if quick else 5
for vn, kw in (('primary', L.PRIMARY), ('Hinf', dict(L.PRIMARY, H=1e9))):
    cfg = L.Cfg(G, **kw); out[vn] = {}
    for c in (8, 12, 17, 20):
        cands = M.dist_candidates(cfg, c, nper=2 if quick else 4)
        for k in (0, 2):
            best = None
            for s in range(NREST if cands else 0):
                mem, F = M.pack_dist(cfg, cands, c, k, s, max_rej=600 if quick else 1500)
                if best is None or len(mem) > len(best[0]): best = (mem, F)
            rec = dict(c=c, k=k, n_cands=len(cands), n_mem=len(best[0]) if best else 0, target_cells=len(set(n for C, N, xs in cands for n in N)))
            if best and best[0]:
                rec['design'] = M.design_stats(cfg, best[0], best[1], c); rec['verify'] = M.verify_dist(cfg, best[0], best[1], c)
                rec['mems'] = [dict(cue=list(C), noncue=list(N)) for C, N, Mm in best[0]]
            out[vn]['c%d_k%d' % (c, k)] = rec
            print(key, vn, 'c', c, 'k', k, 'cands', len(cands), 'n_mem', rec['n_mem'], round(time.time() - t0), flush=True)
    json.dump(out, open('dist_%s%s.json' % (key, '_quick' if quick else ''), 'w'))
print(key, 'DONE', round(time.time() - t0), flush=True)
