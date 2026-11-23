"""Keep, in order, those memories of the existing R3 packings (ripple_overlap_j/cap_*.json) that satisfy the LP constraints (forced-value test), then solve the real LP on the kept set.
usage: filter_r3.py KEY -> filt_KEY.json"""
import sys, json, numpy as np, lpw_lib as L
key = sys.argv[1]; G = L.load(key); capj = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/cap_%s.json' % key)); out = {}
def keep(cfg, groups):
    F = cfg.base.copy(); mem = []; rej = dict(pair_weak=0, hub_target=0, cap_H=0, closure=0)
    for g in groups:
        C = tuple(sorted(g['cue'])); N = tuple(sorted(g['noncue'])); M = sorted(set(C) | set(N))
        if any(n in cfg.hub_excl for n in N): rej['hub_target'] += 1; continue
        if any((cfg.U[c, n] < cfg.gap - 1e-9) for c in C for n in N) or any(cfg.U[list(C), n].sum() < L.T - 1e-9 for n in N): rej['pair_weak'] += 1; continue
        F2 = F.copy()
        for n in N:
            for c, x in zip(C, L.xvals(cfg, C, n)): F2[c, n] = max(F2[c, n], x)
        if (F2[:, list(N)].sum(0) > cfg.Hv[list(N)] + 1e-9).any(): rej['cap_H'] += 1; continue
        aff = [a for a in range(len(mem)) if set(mem[a][0]) & set(C)]
        if not L.check_mem(F2, cfg, M, C) or not all(L.check_mem(F2, cfg, mem[a][2], mem[a][0]) for a in aff): rej['closure'] += 1; continue
        F = F2; mem.append((C, N, M))
    return mem, rej
VAR = dict(L.VARIANTS); VAR['r3equiv'] = L.R3EQ
for vn, kw in VAR.items():
    cfg = L.Cfg(G, **kw); R = {}
    for m, k in [(2, 0), (2, 1), (2, 2), (2, 3), (4, 0), (4, 3)]:
        gj = capj.get('m%d_k%d' % (m, k)); groups = gj['groups'] if gj else []
        mem, rej = keep(cfg, groups); res = L.solve(cfg, mem) if mem else dict(status='empty')
        e = dict(r3_n=len(groups), kept=len(mem), rejected=rej, lp_status=res['status'])
        if res['status'] == 0: e['wstats'] = L.wstats(cfg, res, mem)
        R['m%d_k%d' % (m, k)] = e
    out[vn] = R; print(key, vn, {f: (v['r3_n'], v['kept']) for f, v in R.items()}, flush=True)
json.dump(out, open('filt_%s.json' % key, 'w'))
