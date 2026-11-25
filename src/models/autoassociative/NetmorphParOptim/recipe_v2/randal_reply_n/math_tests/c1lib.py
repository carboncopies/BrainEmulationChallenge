"""per-cell perceptron LP (threshold model) used by C1/C6/C7. Memory = (cue tuple, target tuple). kc = number of cue cells that must complete all other members; ks = silence cue-subset size (all ks-subsets of the cue <= THETA)."""
import numpy as np, itertools
from scipy.optimize import linprog
import mtlib as M
T, THETA, CAP = M.T, M.THETA, M.CAP
def cell_rows(G, i, mems, kc=4, ks=3, theta=THETA, Tt=T):
    """returns (A_ub, b_ub, comp_rows_mask) for the variables w_ji over in-neighbours js of i (G[j,i]>0), constraint form A w + s*sg <= b where sg=1 (margin)"""
    js = np.where(G[:, i] > 0)[0]; pos = {j: k for k, j in enumerate(js)}; A = []; b = []
    for cue, tg in mems:
        M_ = set(cue) | set(tg)
        if i in tg:
            for sub in itertools.combinations(cue, kc):       # completion from any kc-subset of the cue
                r = np.zeros(len(js));
                for j in sub:
                    if j in pos: r[pos[j]] = -1
                A.append(r); b.append(-Tt)                    # -sum <= -T - s
            if ks:
                for sub in itertools.combinations(cue, ks):    # silence of ks-subsets
                    r = np.zeros(len(js))
                    for j in sub:
                        if j in pos: r[pos[j]] = 1
                    A.append(r); b.append(theta)
        elif i not in cue:                                    # non-member: whole memory silent
            r = np.zeros(len(js))
            for j in M_:
                if j in pos: r[pos[j]] = 1
            A.append(r); b.append(theta)
    return js, (np.array(A) if A else np.zeros((0, len(js)))), np.array(b)
def solve_cell(G, i, mems, cap=True, kc=4, ks=3, lbw=0.1, theta=THETA, smax=10.0):
    js, A, b = cell_rows(G, i, mems, kc, ks, theta)
    n = len(js)
    if A.shape[0] == 0: return smax, js, None
    # sign of s: completion rows (b == -T) have -sum + s <= -T ; silence rows sum + s <= theta
    sg = np.ones(A.shape[0])
    lb = lbw * G[js, i]; ub = np.minimum(G[js, i], CAP)
    Hv = max(3 * T, lb.sum()) if cap else 1e9
    Aub = np.hstack([A, sg[:, None]]); Aub = np.vstack([Aub, np.r_[np.ones(n), 0]]); bub = np.r_[b, Hv]
    c = np.r_[np.zeros(n), -1.0]
    res = linprog(c, A_ub=Aub, b_ub=bub, bounds=[(l, u) for l, u in zip(lb, ub)] + [(-50, smax)], method='highs')
    if res.status != 0: return -50.0, js, None
    return float(res.x[-1]), js, res.x[:-1]
def cells_of(mems):
    S = set()
    for cue, tg in mems: S |= set(cue) | set(tg)
    return S
