p='lpw_lib.py'; s=open(p).read()
old=s[s.index("def candidates(cfg, m, limit=None):"):s.index("def check_mem")]
new='''def candidates(cfg, m, limit=None):
    """4-cue sets with >= m common targets n (hub cells excluded as targets, DEVIATIONS D2) such that the cue pairs are all >= gap and sum(U) >= T.
    returns list of (C tuple, [targets]); the minimal x values are computed lazily by xvals()."""
    byC = {}; U = cfg.U
    for n in range(NP):
        if n in cfg.hubs: continue
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

'''
s=s.replace(old,new)
s=s.replace("        C, tl, xs = cands[i]\n","        C, tl = cands[i]\n")
s=s.replace("for c, x in zip(C, xs[n]): F2[c, n] = max(F2[c, n], x)","for c, x in zip(C, xvals(cfg, C, n)): F2[c, n] = max(F2[c, n], x)")
open(p,'w').write(s)
