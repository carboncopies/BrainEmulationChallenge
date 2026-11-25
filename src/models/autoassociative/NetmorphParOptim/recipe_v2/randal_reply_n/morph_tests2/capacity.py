#!/usr/bin/env python3
"""Offline memory-capacity proxy, feas2.py (randal_reply_n) generalised to any number of pyramidal cells.
From a viz dump (gen_autonm_labels -vizdir sample_XXXX.json): pyramidal AMPA conductance matrix P (nS, pre x post).
- strong pairs: P >= 4.125 nS (R3 pair threshold, as in dynamics_c / feas2)
- max disjoint memories: cue sets of 4 cells with >= m common strong targets outside the cue (m = 4: 4+4, m = 2: 4+2);
  300 random-restart greedy packings (same as feas2). Full enumeration when sum C(k_in,4) <= 3e6, else sampled
  (3e6 random 4-cell cue sets; result is a LOWER BOUND, flagged sampled_LB).
- dominant eigenvalue of P (nS) and of the strong-pair submatrix.
usage: capacity.py DUMP [DUMP ...] -> prints one JSON line per dump"""
import sys, itertools, random, json, math
from collections import defaultdict
import numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import recipelib as L
THR = 4.125

def capacity(dump):
    D = L.Dump(dump); n = len(D.pyr); P = D.G[:n, :n].copy(); np.fill_diagonal(P, 0)
    nz = P[P > 0]
    out = dict(dump=dump, n_pyr=n, n_int=D.N - n, pairs=int(len(nz)), p_conn=round(len(nz) / (n * (n - 1)), 4),
               g_mean=float(nz.mean()) if len(nz) else 0.0, pairs_ge_thr=int((P >= THR).sum()),
               strong_out_per_cell=float((P >= THR).sum() / n),
               lambda_max_nS=float(np.max(np.abs(np.linalg.eigvals(P)))),
               lambda_max_strong_nS=float(np.max(np.abs(np.linalg.eigvals(np.where(P >= THR, P, 0))))))
    A = P >= THR
    nb = {t: [c for c in np.where(A[:, t])[0] if c != t] for t in range(n)}
    full = sum(math.comb(len(v), 4) for v in nb.values() if len(v) >= 4)
    sampled = full > 3e6; out['sampled_LB'] = sampled; out['n_4subsets_full'] = full
    def cands(m):
        if not sampled:
            byC = defaultdict(set)
            for t, v in nb.items():
                if len(v) >= 4:
                    for C in itertools.combinations(sorted(v), 4): byC[C].add(t)
            return [(C, sorted(x for x in T if x not in C)) for C, T in byC.items() if len([x for x in T if x not in C]) >= m]
        rs = np.random.RandomState(1); res = []
        for _ in range(30):                                   # 30 x 100k = 3e6 random cue sets
            idx = np.argsort(rs.rand(100000, n), axis=1)[:, :4]
            common = A[idx[:, 0]] & A[idx[:, 1]] & A[idx[:, 2]] & A[idx[:, 3]]
            for r in range(4): common[np.arange(len(idx)), idx[:, r]] = False
            ok = np.where(common.sum(1) >= m)[0][:8000]
            for i in ok: res.append((tuple(sorted(int(x) for x in idx[i])), [int(t) for t in np.where(common[i])[0]]))
        return res
    for m in (4, 2):
        cs = cands(m); rr = random.Random(0); best = []
        for _ in range(300):
            order = cs[:]; rr.shuffle(order); used = set(); ch = []
            for C, T in order:
                if used & set(C): continue
                Tf = [t for t in T if t not in used]
                if len(Tf) >= m:
                    Tf = rr.sample(Tf, m); ch.append((list(C), sorted(Tf))); used |= set(C) | set(Tf)
            if len(ch) > len(best): best = ch
        out['cands_m%d' % m] = len(cs); out['max_disjoint_m%d' % m] = len(best)
    return out

if __name__ == '__main__':
    for d in sys.argv[1:]: print(json.dumps(capacity(d), default=int), flush=True)
