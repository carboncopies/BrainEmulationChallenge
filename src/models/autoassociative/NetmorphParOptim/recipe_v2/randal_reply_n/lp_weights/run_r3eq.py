"""usage: run_capacity.py KEY  -> cap_KEY.json. Offline; no NES. For each variant: single-memory counts, greedy packings (restarts) for families, then the real LP on the best set."""
import sys, json, time, numpy as np, lpw_lib as L
key = sys.argv[1]; G = L.load(key); out = {}
FULL = ('r3equiv',); FAMS = [(2, 0), (2, 1), (2, 2), (2, 3), (4, 0), (4, 3)]
t00 = time.time()
for vn, kw in [('r3equiv', L.R3EQ)]:
    cfg = L.Cfg(G, **kw); R = dict(hubs=cfg.hubs, n_strong_pairs=int(cfg.strong.sum()), fams={})
    nrest, rej = (10, 4000) if vn in FULL else (3, 1500)
    cache = {}
    for m, k in FAMS:
        if m not in cache: cache[m] = L.candidates(cfg, m)
        cands = cache[m]; best = []; nc = len(cands)
        for s in range(nrest if cands else 0):
            mem, F = L.pack(cfg, cands, m, k, s, max_rej=rej)
            if len(mem) > len(best): best = mem
        res = L.solve(cfg, best) if best else dict(status='empty')
        fam = dict(m=m, k=k, n_cands=nc, n_mem=len(best), mems=[dict(cue=list(C), noncue=list(N)) for C, N, M in best], lp_status=res['status'])
        if res['status'] == 0:
            fam['stageB'] = bool(res['stageB']); fam['wstats'] = L.wstats(cfg, res, best); fam['wsum'] = res['wsum']
            if vn in FULL and m == 2 and k in (0, 3):
                fam['x'] = [float(v) for v in res['x']]; fam['pairs'] = [list(p) for p in res['pairs']]
        R['fams']['m%d_k%d' % (m, k)] = fam
        print(key, vn, 'm', m, 'k', k, 'cands', nc, 'best', len(best), 'LP', res['status'], 'elapsed', round(time.time() - t00), flush=True)
    out[vn] = R
    json.dump(out, open('capr3_%s.json' % key, 'w'))
print(key, 'DONE', round(time.time() - t00), flush=True)
