"""lp_weights: offline weight design on grown E4 networks. No NES/API/sim. See PREREGISTRATION.md and DEVIATIONS.md.
Variables = existing Pyr->Pyr pairs (G > 0). Constraints enforced as variable bounds / linear constraints in the LP; greedy packing uses the
closed-form minimal ("water-filling") values of the designed pairs (DEVIATIONS D1) and the final weights come from the real LP."""
import sys, json, itertools, random, math
import numpy as np, scipy.sparse as sp
from scipy.optimize import linprog
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j')
import ovlib as O
NP = 96; T = 16.5; CAP = 6.86
PRIMARY = dict(theta=T - 4.125, H=3 * T, lbw=0.1)   # unintended-input limit, homeostatic cap, lower weight bound
# POST-HOC variant (not preregistered): R3 pair rule (each cue pair >= 4.125) + cascade-threshold criterion (outsiders < 16.5), hubs as targets
R3EQ = dict(theta=16.4, H=3 * T, lbw=0.1, hubmode='waive', gapmin=4.125)
VARIANTS = {'primary': PRIMARY, 'hubs_waived': dict(PRIMARY, hubmode='waive'), 'theta14': dict(PRIMARY, theta=14.0), 'w0': dict(PRIMARY, lbw=0.0),
            'H2T': dict(PRIMARY, H=2 * T), 'H5T': dict(PRIMARY, H=5 * T)}

def load(key):
    D, P = O.load(key); G = np.array(P, dtype=float); np.fill_diagonal(G, 0.0); return G

def waterfill(U):
    """minimal uniform x_c = min(U_c, lam), sum = T. returns None if sum(U) < T. U: array of 4."""
    if U.sum() < T - 1e-12: return None
    lo, hi = 0.0, float(U.max())
    for _ in range(60):
        mid = (lo + hi) / 2
        if np.minimum(U, mid).sum() >= T: hi = mid
        else: lo = mid
    return np.minimum(U, hi)

class Cfg:
    def __init__(self, G, theta, H, lbw, hubmode='exclude', gapmin=None):
        self.G = G; self.theta = theta; self.H = H; self.lbw = lbw; self.gap = T - theta if gapmin is None else gapmin
        self.U = np.minimum(G, CAP); self.LB = lbw * G
        self.base = self.LB.copy()                      # forced values of non-designed pairs
        self.strong = (self.U >= self.gap - 1e-12) & (G > 0)
        self.Hv = np.maximum(H, self.base.sum(0))          # DEVIATIONS D2: cap cannot be below the unavoidable minimum input
        self.hubs = [int(j) for j in np.where(self.base.sum(0) > H + 1e-9)[0]]
        self.hubmode = hubmode
        self.hub_excl = set(self.hubs) if hubmode == 'exclude' else set()
        if hubmode == 'waive': self.Hv[self.hubs] = 1e9   # NON-COMPLIANT with constraint 5; used only as the R3-comparable variant (R3 counts used the hub cells as targets)

def candidates(cfg, m, limit=None):
    """4-cue sets with >= m common targets n (hub cells excluded as targets, DEVIATIONS D2) such that the cue pairs are all >= gap and sum(U) >= T.
    returns list of (C tuple, [targets]); the minimal x values are computed lazily by xvals()."""
    byC = {}; U = cfg.U
    for n in range(NP):
        if n in cfg.hub_excl: continue
        pre = [c for c in range(NP) if c != n and cfg.strong[c, n]]
        if len(pre) < 4: continue
        comb = np.array(list(itertools.combinations(pre, 4)), dtype=np.int16)
        ok = U[comb, n].sum(1) >= T - 1e-9
        for C in comb[ok]: byC.setdefault(tuple(int(c) for c in C), []).append(n)
    out = []
    for C, tl in byC.items():
        tl = [n for n in tl if n not in C]
        if len(tl) >= m: out.append((C, sorted(tl)))
    return out

_wf = {}
def xvals(cfg, C, n):
    key = (id(cfg), C, n)
    if key not in _wf: _wf[key] = waterfill(cfg.U[list(C), n])
    return _wf[key]

def check_mem(F, cfg, M, C):
    M = list(M); C = list(C); s = F[M].sum(0); s[M] = 0.0
    if s.max() > cfg.theta + 1e-9: return False
    Cs = set(C)
    for n in M:
        if n in Cs:
            S = [c for c in C if c != n]; v = F[S, n].sum()
        else:
            col = F[C, n]; v = col.sum() - col.min()
        if v > cfg.theta + 1e-9: return False
    return True

def pack(cfg, cands, m, k, seed, max_rej=800, max_mem=400, bias_reuse=True):
    rs = np.random.RandomState(seed); rr = random.Random(seed)
    idx = np.arange(len(cands)); rs.shuffle(idx)
    F = cfg.base.copy(); mem = []; Mem = np.zeros((0, NP), dtype=np.int8); rej = 0; used_c = np.zeros(NP); used_n = np.zeros(NP)
    for i in idx:
        if rej >= max_rej or len(mem) >= max_mem: break
        C, tl = cands[i]
        cands_n = [n for n in tl]
        ok = False
        for trial in range(8):
            order = cands_n[:]; rr.shuffle(order)
            if bias_reuse and k > 0 and trial % 2 == 0: order.sort(key=lambda n: -used_n[n])
            N = tuple(sorted(order[:m]))
            mv = np.zeros(NP, dtype=np.int8); mv[list(C)] = 1; mv[list(N)] = 1
            if len(mem) and ((Mem @ mv) > k).any(): continue
            F2 = F.copy()
            for n in N:
                for c, x in zip(C, xvals(cfg, C, n)): F2[c, n] = max(F2[c, n], x)
            if (F2[:, list(N)].sum(0) > cfg.Hv[list(N)] + 1e-9).any(): continue
            Mn = sorted(set(C) | set(N)); aff = [a for a in range(len(mem)) if Mem[a][list(C)].any()]
            if not check_mem(F2, cfg, Mn, C): continue
            if not all(check_mem(F2, cfg, mem[a][2], mem[a][0]) for a in aff): continue
            F = F2; mem.append((C, N, Mn)); Mem = np.vstack([Mem, mv]); used_n[list(N)] += 1; used_c[list(C)] += 1; ok = True; break
        rej = 0 if ok else rej + 1
    return mem, F

# ---------- the real LP ----------
def build_lp(cfg, mems):
    G = cfg.G; pairs = [(i, j) for i in range(NP) for j in range(NP) if G[i, j] > 0]
    col = {p: t for t, p in enumerate(pairs)}; nv = len(pairs)
    lb = np.array([cfg.LB[p] for p in pairs]); ub = np.array([cfg.U[p] for p in pairs])
    rows = []; cols = []; vals = []; rhs = []; sense = []   # A x <= b rows
    r = [0]
    def add(coefs, b, ge=False):
        s = -1.0 if ge else 1.0
        for p, v in coefs:
            if p in col: rows.append(r[0]); cols.append(col[p]); vals.append(s * v)
        rhs.append(s * b); r[0] += 1
    for j in range(NP):   # homeostatic cap (4)/(5)
        add([((i, j), 1.0) for i in range(NP) if G[i, j] > 0], cfg.Hv[j])
    for (C, N, M) in mems:
        Cs = set(C)
        for n in N: add([((c, n), 1.0) for c in C], T, ge=True)                      # (i)
        for n in M:                                                                  # (ii)
            subs = [tuple(c for c in C if c != n)] if n in Cs else [tuple(c for c in C if c != c0) for c0 in C]
            for S in subs: add([((c, n), 1.0) for c in S], cfg.theta)
        for o in range(NP):                                                          # (iii)
            if o in M: continue
            add([((f, o), 1.0) for f in M], cfg.theta)
    A = sp.csr_matrix((vals, (rows, cols)), shape=(r[0], nv)); return pairs, lb, ub, A, np.array(rhs)

def solve(cfg, mems):
    pairs, lb, ub, A, b = build_lp(cfg, mems); Gv = np.array([cfg.G[p] for p in pairs]); nv = len(pairs)
    c = 1.0 / Gv                                                                    # stage A: min sum w
    ra = linprog(c, A_ub=A, b_ub=b, bounds=list(zip(lb, ub)), method='highs')
    if ra.status != 0: return dict(status=ra.status, msg=ra.message)
    xa = ra.x; wsum = float((xa / Gv).sum()); raised = (xa > lb + 1e-7)
    # stage B: min t s.t. x_ij <= t G_ij on raised pairs, sum w <= 1.02 wsum
    Ab = sp.hstack([A, sp.csr_matrix((A.shape[0], 1))]).tocsr()
    ridx = np.where(raised)[0]
    Rm = sp.csr_matrix((np.concatenate([np.ones(len(ridx)), -Gv[ridx]]), (np.concatenate([np.arange(len(ridx))] * 2), np.concatenate([ridx, np.full(len(ridx), nv)]))), shape=(len(ridx), nv + 1))
    Sm = sp.csr_matrix((np.concatenate([1.0 / Gv, [0.0]]), (np.zeros(nv + 1, dtype=int), np.arange(nv + 1))), shape=(1, nv + 1))
    A2 = sp.vstack([Ab, Rm, Sm]).tocsr(); b2 = np.concatenate([b, np.zeros(len(ridx)), [1.02 * wsum]])
    c2 = np.zeros(nv + 1); c2[-1] = 1.0
    rb = linprog(c2, A_ub=A2, b_ub=b2, bounds=list(zip(lb, ub)) + [(0, None)], method='highs')
    x = rb.x[:nv] if rb.status == 0 else xa
    return dict(status=0, pairs=pairs, x=x, G=Gv, lb=lb, ub=ub, xA=xa, wsum=wsum, stageB=rb.status == 0, nrow=A.shape[0])

def wstats(cfg, res, mems):
    """weight statistics of a solved design"""
    x = res['x']; G = res['G']; w = x / G; lb = res['lb']; ub = res['ub']; nv = len(x); tol = 1e-6
    at_lb = np.abs(x - lb) <= 1e-5; at_ub = np.abs(x - ub) <= 1e-5 * np.maximum(1, ub)
    cap_nS = np.abs(x - CAP) <= 1e-4; at_w1 = np.abs(w - 1.0) <= 1e-6
    des = set((c, n) for (C, N, M) in mems for n in N for c in C); pairs = res['pairs']; di = np.array([t for t, p in enumerate(pairs) if p in des], dtype=int)
    raised = ~at_lb
    out = dict(n_vars=nv, n_designed=len(di), frac_at_lb=float(at_lb.mean()), frac_raised=float(raised.mean()), frac_at_ub=float(at_ub.mean()),
               frac_w_ge_0p999=float(at_w1.mean()))
    if len(di):
        xd = x[di]; wd = w[di]
        out.update(des_x_min=float(xd.min()), des_x_med=float(np.median(xd)), des_x_max=float(xd.max()), des_w_min=float(wd.min()), des_w_med=float(np.median(wd)), des_w_max=float(wd.max()),
                   des_frac_at_cap686=float((np.abs(xd - CAP) <= 1e-4).mean()), des_frac_w1=float((wd >= 0.999).mean()), des_frac_at_margin=float((np.abs(xd - cfg.gap) <= 1e-4).mean()),
                   des_frac_w_ge_0p9=float((wd >= 0.9).mean()))
    rr = np.where(raised)[0]
    if len(rr) > 2:
        lx = np.log(x[rr]); out.update(raised_n=int(len(rr)), raised_x_med=float(np.median(x[rr])), raised_x_p90=float(np.percentile(x[rr], 90)),
                                       raised_logx_skew=float(((lx - lx.mean()) ** 3).mean() / (lx.std() ** 3 + 1e-12)), raised_w_med=float(np.median(w[rr])))
    inp = np.zeros(NP)
    for t, (i, j) in enumerate(pairs): inp[j] += x[t]
    nh = [j for j in range(NP) if j not in cfg.hubs]
    out.update(max_cell_input_nonhub=float(inp[nh].max()), frac_nonhub_within2pct_H=float((inp[nh] >= 0.98 * cfg.H).mean()), mean_cell_input=float(inp.mean()), n_hubs=len(cfg.hubs), hub_inputs=';'.join('%d:%.1f' % (j, inp[j]) for j in cfg.hubs))
    out['nonraised_at_lb_frac_of_nondesigned'] = float(at_lb.sum() / max(1, nv - len(di)))
    return out

def cascade(X, cue, thr=T, maxit=20):
    """threshold model on a dense programmed-conductance matrix X (pre, post). returns fired set (cue forced)."""
    fired = np.zeros(X.shape[1], dtype=bool); fired[list(cue)] = True
    for _ in range(maxit):
        inp = X[fired].sum(0); new = (inp >= thr - 1e-9) & ~fired
        if not new.any(): break
        fired |= new
    return fired
