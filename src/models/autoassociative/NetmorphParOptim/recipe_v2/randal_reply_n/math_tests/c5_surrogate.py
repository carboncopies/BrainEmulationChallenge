"""C5: proxies vs K42, and degree-preserving surrogate K42 (strong-pair digraph). usage: c5_surrogate.py GROUP (base|arms)  -> c5_<group>.json"""
import sys, json, glob, os, numpy as np
import mtlib as M
grp = sys.argv[1]; FR = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run/'
def K42(P, restarts=10):
    c = M.O.candidates(P, 2); best = 0
    if not c: return 0
    for r in range(restarts):
        best = max(best, len(M.O.pack(c, 2, 0, seed=r, restarts=10)))
    return best
def proxies(P):
    S = (P >= 4.125).astype(float); np.fill_diagonal(S, 0); din = S.sum(0); dout = S.sum(1)
    srt = np.sort(din)[::-1]; x = np.sort(din); n = len(x); gini = float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum())) if x.sum() > 0 else 0
    rho = float(np.max(np.abs(np.linalg.eigvals(S)))); recip = float((S * S.T).sum() / max(S.sum(), 1))
    return dict(n_strong=int(S.sum()), top10_in=float(srt[:10].sum()), in_cv=float(din.std() / max(din.mean(), 1e-9)), rho_strong=rho, reciprocity=recip, in_gini=gini)
def swap_surrogate(S, rs, nswap=None):
    S = S.copy().astype(bool); E = np.argwhere(S); m = len(E); nswap = nswap or 10 * m
    for _ in range(nswap):
        a, b = rs.randint(m, size=2); (i, j), (k, l) = E[a], E[b]
        if i == k or j == l or i == l or k == j: continue
        if S[i, l] or S[k, j]: continue
        S[i, j] = S[k, l] = False; S[i, l] = S[k, j] = True; E[a] = (i, l); E[b] = (k, j)
    return S
out = {}
if grp == 'base':
    for s in M.SEEDS:
        P = M.G(s); r = dict(proxies=proxies(P), K42_greedy=K42(P))
        S = P >= 4.125; np.fill_diagonal(S, False); rs = np.random.RandomState(s); ks = []
        for t in range(8):
            Z = swap_surrogate(S, rs); ks.append(K42(np.where(Z, 5.0, 0.0), restarts=4))
        r['surrogate_K42'] = ks; out[s] = r; print(s, r['K42_greedy'], ks, flush=True)
else:
    import recipelib as L
    for f in sorted(glob.glob(FR + 'grow_*_s*/viz/sample_0000.json')):
        tag = f.split('/')[-3][5:]
        try:
            D = L.Dump(f); P = D.G[:96, :96].copy(); np.fill_diagonal(P, 0)
            out[tag] = dict(proxies=proxies(P), K42_greedy=K42(P, 5)); print(tag, out[tag]['K42_greedy'], flush=True)
        except Exception as e: print(tag, 'ERR', e, flush=True)
json.dump(out, open('c5_%s.json' % grp, 'w'), default=float)
