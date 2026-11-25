"""C1 volume part: Chebyshev radius + hit-and-run ranges on the 10 lowest-margin cells (P=4 memories, no cap) for s66666 and s77777."""
import json, numpy as np, itertools
from scipy.optimize import linprog
import mtlib as M, c1lib as L
out = {}
for s in (66666, 77777):
    G = M.G(s); rs = np.random.RandomState(s + 5); cands = M.O.candidates(G, 2)
    idx = rs.choice(len(cands), 4, replace=False); mems = [(cands[i][0], tuple(rs.choice(cands[i][1], 2, replace=False))) for i in idx]
    sc = []
    for i in range(96):
        sv, js, x = L.solve_cell(G, i, mems, cap=False); sc.append(sv)
    order = np.argsort(sc)[:10]; cells = []
    for i in order:
        js, A, b = L.cell_rows(G, i, mems); n = len(js); lb = 0.1 * G[js, i]; ub = np.minimum(G[js, i], M.CAP)
        if A.shape[0] == 0: continue
        # polytope: A w <= b, lb<=w<=ub. Chebyshev radius r (L2): max r s.t. A w + r||A_k|| <= b, w-r>=lb, w+r<=ub
        nr = np.linalg.norm(A, axis=1); Aub = np.vstack([np.hstack([A, nr[:, None]]), np.hstack([-np.eye(n), np.ones((n, 1))]), np.hstack([np.eye(n), np.ones((n, 1))])])
        bub = np.r_[b, -lb, ub]; res = linprog(np.r_[np.zeros(n), -1.], A_ub=Aub, b_ub=bub, bounds=[(None, None)] * n + [(0, None)], method='highs')
        if res.status != 0 or res.x[-1] < 1e-9: cells.append(dict(cell=int(i), margin=float(sc[i]), cheb=0.0, dim=n)); continue
        w = res.x[:n].copy(); rad = float(res.x[-1]); Aall = np.vstack([A, -np.eye(n), np.eye(n)]); ball = np.r_[b, -lb, ub]
        lo_seen = w.copy(); hi_seen = w.copy()
        for it in range(20000):
            d = rs.randn(n); d /= np.linalg.norm(d); den = Aall @ d; slack = ball - Aall @ w
            with np.errstate(divide='ignore', invalid='ignore'):
                t = np.where(den > 1e-12, slack / den, np.inf); tn = np.where(den < -1e-12, slack / den, -np.inf)
            tmax = t.min(); tmin = tn.max(); w = w + rs.uniform(tmin, tmax) * d; lo_seen = np.minimum(lo_seen, w); hi_seen = np.maximum(hi_seen, w)
        rng = (hi_seen - lo_seen); box = (ub - lb); free = box > 1e-9; ratio = rng[free] / box[free]
        cells.append(dict(cell=int(i), margin=float(sc[i]), dim=n, cheb=rad, mean_range_over_box=float(ratio.mean()), pinned_pairs=int((ratio < 0.05).sum()), log10_box_frac_upper=float(np.log10(np.clip(ratio, 1e-6, 1)).sum())))
    out[s] = cells; print(s, [(c['cell'], round(c['margin'], 2), c.get('dim'), round(c['cheb'], 3), round(c.get('mean_range_over_box', 0), 2), c.get('pinned_pairs')) for c in cells], flush=True)
json.dump(out, open('c1_vol.json', 'w'), default=float)
