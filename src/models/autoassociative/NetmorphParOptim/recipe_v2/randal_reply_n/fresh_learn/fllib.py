"""fresh_learn Stage 1 library (offline, threshold model). See PREREGISTRATION.md. No NES/API call."""
import sys, math, zlib
import numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/lp_weights')
import lpw_lib as L
NP = 96; T = 16.5; CAP = 6.86; TCAP = T / 0.75

class Net:
    """one grown model: ceilings U, floors, grown state x0 (w0 = 0.2)."""
    def __init__(self, key):
        self.key = key; G = L.load(key); self.G = G; self.U = np.minimum(G, CAP)
        self.fl = np.minimum(0.1 * G, self.U); self.x0 = np.clip(0.2 * G, self.fl, self.U); self.pos = G > 0
        self.floorsum = (0.1 * G).sum(0)

def caps(net, Hmode):
    """per-cell input cap H_j. Hmode: multiple of T (float) or None = no homeostasis."""
    if Hmode is None: return None
    return np.maximum(Hmode * T, net.floorsum)

def build_F(net, assemblies, Hmode=3.0):
    """learning (saturate co-active pairs of every assembly) then homeostatic scaling of the above-floor part. returns F, info."""
    X = net.x0.copy()
    for A in assemblies:
        A = list(A); ix = np.ix_(A, A); X[ix] = np.where(net.pos[ix], net.U[ix], X[ix])
    info = dict(n_scaled=0, hubs=[])
    if isinstance(Hmode, tuple):   # POST-HOC variant ('sp', Xstar_in_T): set-point normalisation of the LEARNED input per cell (down only), then the 3T cap
        xs = Hmode[1] * T; Hmode = 3.0; Lmask = np.zeros_like(net.pos)
        for A in assemblies:
            A = list(A); ix = np.ix_(A, A); Lmask[ix] |= net.pos[ix]
        Ls = (net.U * Lmask).sum(0); fac = np.where(Ls > xs, xs / np.maximum(Ls, 1e-12), 1.0)
        X = np.where(Lmask, np.maximum(net.x0, np.maximum(net.fl, net.U * fac[None, :])), net.x0)
    Hv = caps(net, Hmode)
    if Hv is not None:
        tot = X.sum(0); over = np.where(tot > Hv + 1e-9)[0]
        for j in over:
            e = X[:, j] - net.fl[:, j]; room = Hv[j] - net.fl[:, j].sum()
            if room <= 0 or e.sum() <= 0: X[:, j] = net.fl[:, j]; info['hubs'].append(int(j)); continue
            s = min(1.0, room / e.sum()); X[:, j] = net.fl[:, j] + s * e
        info['n_scaled'] = int(len(over))
        info['hub_cells'] = [int(j) for j in np.where(net.floorsum > Hmode * T + 1e-9)[0]]
    return X, info

def cascade_batch(F, cues):
    """cues: (m, NP) bool. returns fired (m, NP) bool."""
    fired = cues.copy()
    for _ in range(20):
        inp = fired.astype(np.float64) @ F
        new = (inp >= T - 1e-9) & ~fired
        if not new.any(): break
        fired |= new
    return fired

def _rs(A, tag): return np.random.RandomState(zlib.crc32(('%s-%s' % (tag, ','.join(map(str, sorted(A))))).encode()) & 0x7fffffff)

def cues_for(A, system, n75, n50, n25, nu):
    """deterministic cue sets for assembly A in a system. returns dict of boolean matrices."""
    A = np.array(sorted(A)); k = len(A); rs = _rs(A, 'cue'); out = {}
    def subs(n, size):
        m = np.zeros((n, NP), bool)
        for t in range(n): m[t, rs.choice(A, size=size, replace=False)] = True
        return m
    out['c75'] = subs(n75, int(math.ceil(0.75 * k))); out['c50'] = subs(n50, int(math.ceil(0.5 * k))); out['s25'] = subs(n25, max(1, int(math.floor(0.25 * k))))
    outside = np.array([c for c in range(NP) if c not in set(A.tolist())]); size = int(math.ceil(0.5 * k)); su = []
    sets = [set(B) for B in system]; lim = [max(1, int(math.floor(0.25 * len(B)))) for B in system]
    for t in range(nu * 8):
        if len(su) >= nu: break
        cue = rs.choice(outside, size=size, replace=False); cs = set(cue.tolist())
        if all(len(cs & b) <= l for b, l in zip(sets, lim)): su.append(cue)
    m = np.zeros((len(su), NP), bool)
    for t, cue in enumerate(su): m[t, cue] = True
    out['su'] = m; return out

def evaluate(net, assemblies, Hmode=3.0, n75=20, n50=20, n25=15, nu=15, thr75=0.95, F=None, early=False, req=None):
    req = req or {}
    """whole-system evaluation. returns (all_held, per-assembly list of dict)."""
    if F is None: F, _ = build_F(net, assemblies, Hmode)
    res = []; ok_all = True
    for a, A in enumerate(assemblies):
        mask = np.zeros(NP, bool); mask[list(A)] = True; cs = cues_for(A, assemblies, n75, n50, n25, nu); r = {}
        f75 = cascade_batch(F, cs['c75']); r['c75'] = float((f75 == mask).all(1).mean())
        ok = r['c75'] >= thr75 - 1e-9
        if early and not ok: res.append(r); return False, res
        f25 = cascade_batch(F, cs['s25']); r['s25'] = float((f25.sum(1) == cs['s25'].sum(1)).mean())
        fu = cascade_batch(F, cs['su']) if len(cs['su']) else np.zeros((0, NP), bool); r['su'] = float((fu.sum(1) == cs['su'].sum(1)).mean()) if len(cs['su']) else 1.0
        r['n_su'] = int(len(cs['su']))
        ok = ok and (r['s25'] >= 1.0 - 1e-9 or req.get('no_s25')) and r['su'] >= 1.0 - 1e-9
        if req.get('c50'):
            f50_ = cascade_batch(F, cs['c50']); r['c50'] = float((f50_ == mask).all(1).mean()); ok = ok and r['c50'] >= thr75 - 1e-9
        r['spurious'] = float(((f75 & ~mask).any(1)).mean())
        if ok and r['spurious'] > 0: ok = False
        r['held'] = bool(ok)
        if not early:
            f50 = cascade_batch(F, cs['c50']); r['c50'] = float((f50 == mask).all(1).mean())
        res.append(r); ok_all = ok_all and ok
        if early and not ok: return False, res
    return ok_all, res

def alloc(net, k, system, o, rs, noise=0.3):
    """greedy dense-subgraph allocation of k cells, overlap <= o with every assembly of `system`; returns (cells, objective)."""
    U = net.U; sets = [set(B) for B in system]; sysmask = np.zeros((len(system), NP), bool)
    for i, B in enumerate(system): sysmask[i, list(B)] = True
    def eligible(A, cnt):
        el = np.ones(NP, bool); el[list(A)] = False
        for i in range(len(system)):
            if cnt[i] >= o + 1: el[:] = False
            elif cnt[i] == o: el &= ~sysmask[i]       # adding a cell of B would exceed the overlap limit
        return el
    out_s = U.sum(1)
    for tries in range(20):
        s = int(rs.choice(NP, p=(out_s + 1e-3) / (out_s + 1e-3).sum())); A = [s]
        cnt = [int(s in b) for b in sets]
        if any(c > o for c in cnt): continue
        while len(A) < k:
            el = eligible(A, cnt)
            if not el.any(): break
            S = U[A].sum(0); base = np.minimum(S[A], TCAP)
            gain = (np.minimum(S[A][None, :] + U[:, A], TCAP) - base[None, :]).sum(1) + np.minimum(S, TCAP)
            gain = gain + noise * rs.rand(NP); gain[~el] = -1e9; c = int(np.argmax(gain)); A.append(c)
            for i, b in enumerate(sets): cnt[i] += int(c in b)
        if len(A) < k: continue
        # swap passes
        def obj(B): S = U[B].sum(0); return float(np.minimum(S[B] - U[B, B] * 0, TCAP).sum())
        cur = obj(A)
        for _ in range(10):
            S = U[A].sum(0); worst = A[int(np.argmin(np.minimum(S[A], TCAP)))]; rest = [c for c in A if c != worst]
            cnt2 = [len(b & set(rest)) for b in sets]; el = eligible(rest, cnt2)
            if not el.any(): break
            S2 = U[rest].sum(0); base = np.minimum(S2[rest], TCAP)
            gain = (np.minimum(S2[rest][None, :] + U[:, rest], TCAP) - base[None, :]).sum(1) + np.minimum(S2, TCAP); gain[~el] = -1e9
            c = int(np.argmax(gain)); new = rest + [c]
            if obj(new) > cur + 1e-9: A = new; cur = obj(A)
            else: break
        return sorted(A), cur
    return None, -1

def pack(net, k, o, Hmode, seed, R=40, max_stop=1, req=None):
    """sequential allocation: R candidates per placement, accept the best one for which the whole system is held. returns list of assemblies."""
    rs = np.random.RandomState(seed); system = []
    while True:
        cands = []
        for _ in range(R):
            A, ob = alloc(net, k, system, o, rs)
            if A is not None and A not in cands and A not in [list(s) for s in system]: cands.append((ob, A))
        cands.sort(key=lambda t: -t[0]); got = False
        for ob, A in cands:
            ok, _ = evaluate(net, system + [A], Hmode, early=True, req=req)
            if ok: system.append(A); got = True; break
        if not got or len(system) >= 40: break
    return system

def random_control(net, k, Hmode, n=5000, seed=5):
    """fraction of uniform random k-sets that are held standalone."""
    rs = np.random.RandomState(seed); held = 0
    for _ in range(n):
        A = sorted(rs.choice(NP, size=k, replace=False).tolist())
        ok, _ = evaluate(net, [A], Hmode, early=True)
        held += int(ok)
    return held / n
