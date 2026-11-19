"""usage: capacity_ov.py KEY -> cap_<KEY>.json. For m in (2,4), k in (0,1,2,3): max memories with pairwise overlap <= k (role consistent), designs saved."""
import sys, json, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j')
import ovlib as O
key = sys.argv[1]; D, P = O.load(key); out = dict(key=key, targets_ge4=int(sum(1 for n in range(96) if (P[:, n] >= O.THR).sum() - (P[n, n] >= O.THR) >= 4)), pairs_ge_thr=int((P >= O.THR).sum()))
for m in (2, 4):
    t = time.time(); cs = O.candidates(P, m); out['cands_m%d' % m] = len(cs)
    for k in (0, 1, 2, 3):
        g = O.pack(cs, m, k, seed=7, restarts=150); h, ty = O.overlap_hist(g)
        out['m%d_k%d' % (m, k)] = dict(n=len(g), hist=h, types=ty, groups=g)
        print(key, 'm', m, 'k', k, 'n', len(g), 'hist', h, round(time.time() - t), flush=True)
json.dump(out, open('cap_%s.json' % key, 'w'), default=int)
