"""math_run library: graph variants (ER / CM / VS / hub-capped / synapse-capped) and distributed-cue assemblies under the lp_weights constraints. Offline only."""
import sys, math, itertools, random
import numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/lp_weights_dummy')
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
import lpw_lib as L
NP = 96; T = L.T; CAP = L.CAP; SYN = 0.98
QFRAC = 0.75   # sub-cue silence rule: a cue lacking (1-QFRAC) of its cells must not complete (preregistered 0.75; post-hoc sensitivity changes it)

# ---------------- graph variants ----------------
def edges_of(G):
    ii, jj = np.nonzero(G); return list(zip(ii.tolist(), jj.tolist(), G[ii, jj].tolist()))

def g_er(G, seed):
    rs = np.random.RandomState(seed); E = edges_of(G); vals = np.array([e[2] for e in E])
    allp = [(i, j) for i in range(NP) for j in range(NP) if i != j]; sel = rs.choice(len(allp), size=len(E), replace=False)
    H = np.zeros_like(G)
    for s, v in zip(sel, vals): H[allp[s]] = v
    return H

def g_cm(G, seed, sweeps=10):
    rs = np.random.RandomState(seed); E = edges_of(G); n = len(E)
    src = [e[0] for e in E]; dst = [e[1] for e in E]; val = [e[2] for e in E]; present = set(zip(src, dst))
    for _ in range(sweeps * n):
        a, b = rs.randint(n), rs.randint(n)
        if a == b: continue
        i, j, k, l = src[a], dst[a], src[b], dst[b]
        if i == l or k == j or (i, l) in present or (k, j) in present: continue
        present.discard((i, j)); present.discard((k, l)); present.add((i, l)); present.add((k, j))
        dst[a], dst[b] = l, j
    H = np.zeros_like(G)
    for s, d, v in zip(src, dst, val): H[s, d] = v
    return H

def g_vs(G, seed):
    rs = np.random.RandomState(seed); ii, jj = np.nonzero(G); v = G[ii, jj].copy(); rs.shuffle(v); H = np.zeros_like(G); H[ii, jj] = v; return H

def dcap(G):
    A = G > 0; p = A.sum() / (NP * (NP - 1)); return int(math.ceil(A.sum(0).mean() + 3 * math.sqrt((NP - 1) * p * (1 - p))))

def g_cap(G, seed, keep='random'):
    rs = np.random.RandomState(seed); H = G.copy(); D = dcap(G)
    for j in range(NP):
        idx = np.nonzero(H[:, j])[0]
        if len(idx) > D:
            if keep == 'random': drop = rs.choice(idx, size=len(idx) - D, replace=False)
            else: drop = idx[np.argsort(H[idx, j], kind='stable')[:len(idx) - D]]
            H[drop, j] = 0.0
    return H

def g_syn(G, s):
    H = G.copy(); H[H > s * SYN] = s * SYN; return H

def gstats(G):
    A = G > 0; din = A.sum(0); dout = A.sum(1); nz = G[A]
    return dict(edges=int(A.sum()), p=float(A.sum() / (NP * (NP - 1))), in_mean=float(din.mean()), in_median=float(np.median(din)), in_max=int(din.max()), in_cv=float(din.std() / max(din.mean(), 1e-9)),
                out_cv=float(dout.std() / max(dout.mean(), 1e-9)), syn_mean=float(nz.mean() / SYN) if len(nz) else 0.0, share_single=float((nz < 1.5 * SYN).mean()) if len(nz) else 0.0,
                share_ge5=float((nz >= 4.9).mean()) if len(nz) else 0.0, share_strong=float((nz >= 4.125).mean()) if len(nz) else 0.0, syn_max=float(nz.max() / SYN) if len(nz) else 0.0)

# ---------------- distributed-cue assemblies ----------------
def waterfill_lb(lb, U):
    """minimal uniform x_c = clip(lam, lb_c, U_c) with sum >= T; None if sum(U) < T"""
    if U.sum() < T - 1e-9: return None
    if lb.sum() >= T: return lb.copy()
    lo, hi = 0.0, float(U.max())
    for _ in range(60):
        mid = (lo + hi) / 2
        if np.clip(mid, lb, U).sum() >= T: hi = mid
        else: lo = mid
    return np.clip(hi, lb, U)

def topq(x, q): return float(np.sort(x)[::-1][:q].sum())

def check_gen(F, cfg, M, C, q):
    M = list(M); C = list(C); s = F[M].sum(0); s[M] = 0.0
    if s.max() > cfg.theta + 1e-9: return False
    Cs = set(C)
    for n in M:
        if n in Cs:
            others = [c for c in C if c != n]
            if F[others, n].sum() > cfg.theta + 1e-9: return False
        elif topq(F[C, n], q) > cfg.theta + 1e-9: return False
    return True

def dist_candidates(cfg, c, nper=4, seed=0):
    rs = np.random.RandomState(seed); G = cfg.G; q = int(math.ceil(QFRAC * c))
    pre = [set(int(i) for i in np.nonzero(G[:, n])[0]) - {n} for n in range(NP)]
    tg = [n for n in range(NP) if n not in cfg.hub_excl]; out = []
    for a in range(len(tg)):
        for b in range(a + 1, len(tg)):
            n1, n2 = tg[a], tg[b]; com = sorted(pre[n1] & pre[n2] - {n1, n2})
            if len(com) < c: continue
            sc = np.array([min(cfg.U[i, n1], cfg.U[i, n2]) for i in com]); order = np.argsort(-sc, kind='stable')
            subsets = [tuple(sorted(com[i] for i in order[:c]))]
            if len(com) > c:
                w = sc + 1e-6; w = w / w.sum()
                for _ in range(nper):
                    pick = rs.choice(len(com), size=c, replace=False, p=w); subsets.append(tuple(sorted(com[i] for i in pick)))
            for C in set(subsets):
                xs = {}; ok = True
                for n in (n1, n2):
                    Cl = list(C); x = waterfill_lb(cfg.LB[Cl, n], cfg.U[Cl, n])
                    if x is None or topq(x, q) > cfg.theta + 1e-9: ok = False; break
                    xs[n] = x
                if ok: out.append((C, (n1, n2), xs))
    return out

def pack_dist(cfg, cands, c, k, seed, max_rej=1500, max_mem=60):
    q = int(math.ceil(QFRAC * c)); rs = np.random.RandomState(seed); idx = np.arange(len(cands)); rs.shuffle(idx)
    F = cfg.base.copy(); mem = []; Mem = np.zeros((0, NP), dtype=np.int8); rej = 0
    for i in idx:
        if rej >= max_rej or len(mem) >= max_mem: break
        C, N, xs = cands[i]; M = sorted(set(C) | set(N)); mv = np.zeros(NP, dtype=np.int8); mv[M] = 1
        if len(mem) and ((Mem @ mv) > k).any(): rej += 1; continue
        F2 = F.copy()
        for n in N:
            for cc, x in zip(C, xs[n]): F2[cc, n] = max(F2[cc, n], x)
        if (F2[:, list(N)].sum(0) > cfg.Hv[list(N)] + 1e-9).any(): rej += 1; continue
        aff = [a for a in range(len(mem)) if Mem[a][list(C)].any()]
        if not check_gen(F2, cfg, M, C, q) or not all(check_gen(F2, cfg, mem[a][2], mem[a][0], q) for a in aff): rej += 1; continue
        F = F2; mem.append((C, N, M)); Mem = np.vstack([Mem, mv]); rej = 0
    return mem, F

def verify_dist(cfg, mem, F, c, thr_list=(16.5, 15.0), nrand=30, seed=0):
    """independent check of a distributed design given its programmed matrix F (Pyr->Pyr conductances)."""
    rs = np.random.RandomState(seed); q = int(math.ceil(QFRAC * c)); G = cfg.G
    ok = dict(bounds=bool((F >= cfg.LB - 1e-7).all() and (F <= cfg.U + 1e-7).all()), no_new_pairs=bool(((F > 0) <= (G > 0)).all()), dale=bool((F >= 0).all()),
              H_ok=bool((F.sum(0) <= cfg.Hv + 1e-6).all()), w_range=bool((F[G > 0] / G[G > 0]).min() >= cfg.lbw - 1e-7 and (F[G > 0] / G[G > 0]).max() <= 1 + 1e-7))
    for thr in thr_list:
        full = 0; sub_bad = 0; nsub = 0
        for (C, N, M) in mem:
            fs = set(int(i) for i in np.where(L.cascade(F, C, thr=thr))[0]); full += int(fs == set(M))
            sets = []
            for n in N: sets.append(list(np.argsort(-F[list(C), n], kind='stable')[:q]))   # worst case per target: the q strongest contributors
            for _ in range(nrand): sets.append(list(rs.choice(len(C), size=q, replace=False)))
            for s in sets:
                S = [C[i] for i in s]; nsub += 1; fs2 = set(int(i) for i in np.where(L.cascade(F, S, thr=thr))[0]); sub_bad += int(fs2 != set(S))
        ok['cascade_%s' % thr] = dict(full_exact=full, n_mem=len(mem), subcue_clean=nsub - sub_bad, n_subcue=nsub)
    return ok

def design_stats(cfg, mem, F, c):
    des = [(cc, n) for (C, N, M) in mem for n in N for cc in C]
    if not des: return {}
    Gd = np.array([cfg.G[p] for p in des]); xd = np.array([F[p] for p in des]); w = xd / Gd
    inp = F.sum(0); nh = [j for j in range(NP) if j not in cfg.hubs]
    return dict(n_designed=len(des), syn_per_pair_median=float(np.median(Gd / SYN)), syn_per_pair_mean=float(np.mean(Gd / SYN)), frac_pairs_ge5syn=float((Gd >= 4.9).mean()), frac_single=float((Gd < 1.5 * SYN).mean()),
                x_min=float(xd.min()), x_med=float(np.median(xd)), x_max=float(xd.max()), w_min=float(w.min()), w_med=float(np.median(w)), w_max=float(w.max()), frac_w_ge_0p9=float((w >= 0.9).mean()),
                max_input_nonhub=float(inp[nh].max()), frac_active=float(np.mean([len(M) / NP for (C, N, M) in mem])), cells_used=int(len(set(x for (C, N, M) in mem for x in M))))
