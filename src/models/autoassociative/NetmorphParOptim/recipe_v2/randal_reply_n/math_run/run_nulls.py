"""usage: run_nulls.py KEY [quick] -> nulls_KEY.json. Graph variants x {primary, Hinf} x families; same packer as lp_weights (greedy restarts). Offline."""
import sys, json, time, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/math_run')
import mrlib as M, lpw_lib as L
key = sys.argv[1]; quick = len(sys.argv) > 2; G0 = L.load(key); t0 = time.time()
FAMS = [(2, 0), (2, 1), (2, 3), (4, 0)]; NREST = 2 if quick else 5; REJ = 600 if quick else 1500
types = [('grown', 0, lambda G, s: G)]
for s in (1, 2, 3):
    types += [('ER', s, M.g_er), ('CM', s, M.g_cm), ('VS', s, M.g_vs), ('CAPr', s, lambda G, s_: M.g_cap(G, s_, 'random')), ('CAPr_SYN5', s, lambda G, s_: M.g_syn(M.g_cap(G, s_, 'random'), 5))]
types += [('CAPs', 0, lambda G, s: M.g_cap(G, s, 'strong')), ('SYN8', 0, lambda G, s: M.g_syn(G, 8)), ('SYN5', 0, lambda G, s: M.g_syn(G, 5))]
out = []
for name, seed, fn in types:
    G = fn(G0, seed); st = M.gstats(G); rec = dict(type=name, seed=seed, stats=st, res={})
    for vn, kw in (('primary', L.PRIMARY), ('Hinf', dict(L.PRIMARY, H=1e9))):
        try: cfg = L.Cfg(G, **kw)
        except Exception as e: rec['res'][vn] = dict(error=str(e)); continue
        cache = {}; R = {}
        for m, k in FAMS:
            if m not in cache: cache[m] = L.candidates(cfg, m)
            cands = cache[m]; best = 0
            for s in range(NREST if cands else 0):
                mem, F = L.pack(cfg, cands, m, k, s, max_rej=REJ, max_mem=150); best = max(best, len(mem))
            R['m%d_k%d' % (m, k)] = best; R['cands_m%d' % m] = len(cands)
        R['target_cells_m2'] = len(set(n for C, tl in cache[2] for n in tl)); R['hubs'] = cfg.hubs
        rec['res'][vn] = R
    out.append(rec); print(key, name, seed, 'in_cv %.2f' % st['in_cv'], {v: (r.get('m2_k0'), r.get('m2_k1'), r.get('m2_k3'), r.get('m4_k0'), r.get('cands_m2')) for v, r in rec['res'].items()}, round(time.time() - t0), flush=True)
    json.dump(out, open('nulls_%s%s.json' % (key, '_quick' if quick else ''), 'w'))
print(key, 'DONE', round(time.time() - t0), flush=True)
