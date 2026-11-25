"""C2/C8: exact max disjoint 4+2 packing by HiGHS MILP vs greedy (ovlib.pack k=0) and LP-relaxation bound. usage: c2_exact.py SEED TL"""
import sys, json, time, numpy as np, scipy.sparse as sp
from scipy.optimize import milp, LinearConstraint, Bounds, linprog
import mtlib as M
s = int(sys.argv[1]); TL = float(sys.argv[2]); P = M.G(s); out = dict(seed=s)
t0 = time.time(); cands = M.O.candidates(P, 2); out['n_cands'] = len(cands)
best = 0
for r in range(4):
    mem = M.O.pack(cands, 2, 0, seed=r, restarts=8); best = max(best, len(mem)); print('greedy', r, best, round(time.time() - t0), flush=True)
out['greedy'] = best; out['t_greedy'] = round(time.time() - t0)
nC = len(cands); rows = []; cols = []; vals = []; ncol = nC; wcol = []
cr, cc, cv = [], [], []   # cell rows 0..95
er, ec, ev = [], [], []   # equality rows
k = nC
for i, (C, Tg) in enumerate(cands):
    for c in C: cr.append(c); cc.append(i); cv.append(1)
    er.append(i); ec.append(i); ev.append(-2)
    for n in Tg:
        cr.append(n); cc.append(k); cv.append(1); er.append(i); ec.append(k); ev.append(1); k += 1
nv = k
A_cell = sp.csr_matrix((cv, (cr, cc)), shape=(96, nv)); A_eq = sp.csr_matrix((ev, (er, ec)), shape=(nC, nv))
cobj = np.zeros(nv); cobj[:nC] = -1
# LP relaxation
t1 = time.time()
lp = linprog(cobj, A_ub=A_cell, b_ub=np.ones(96), A_eq=A_eq, b_eq=np.zeros(nC), bounds=(0, 1), method='highs', options=dict(time_limit=TL / 3))
out['lp_bound'] = float(-lp.fun) if lp.status == 0 else None; out['lp_status'] = int(lp.status); out['t_lp'] = round(time.time() - t1)
t2 = time.time()
res = milp(cobj, constraints=[LinearConstraint(A_cell, -np.inf, 1), LinearConstraint(A_eq, 0, 0)], integrality=np.ones(nv), bounds=Bounds(0, 1),
           options=dict(time_limit=TL, disp=False, mip_rel_gap=0))
out['milp_status'] = int(res.status); out['milp_msg'] = res.message
out['exact'] = int(round(-res.fun)) if res.x is not None else None
out['dual_bound'] = float(-res.mip_dual_bound) if hasattr(res, 'mip_dual_bound') and res.mip_dual_bound is not None else None
out['t_milp'] = round(time.time() - t2)
json.dump(out, open('c2_s%d.json' % s, 'w')); print(out, flush=True)
