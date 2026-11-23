"""Independent after-the-fact check (second line of defence; the constraints are enforced inside the LP). usage: verify.py KEY -> verify_KEY.json
For every stored design (cap_KEY.json, capr3_KEY.json): re-solve the LP, then check bounds, per-pair cap, weight range, homeostatic cap, and run the cascade threshold model (thr 16.5 and 15.0):
the full cue must complete exactly its memory, every 3-cell cue must complete nothing."""
import sys, json, itertools, numpy as np, lpw_lib as L
key = sys.argv[1]; G = L.load(key); out = {}
srcs = []
for f in ('cap_%s.json' % key, 'capr3_%s.json' % key, 'caphinf_%s.json' % key):
    try: srcs.append(json.load(open(f)))
    except Exception: pass
VAR = dict(L.VARIANTS); VAR['r3equiv'] = L.R3EQ; VAR['Hinf'] = dict(L.PRIMARY, H=1e9); VAR['Hinf_theta14'] = dict(L.PRIMARY, H=1e9, theta=14.0)
for src in srcs:
    for vn, R in src.items():
        cfg = L.Cfg(G, **VAR[vn])
        for fn, fam in R['fams'].items():
            if not fam['mems']: continue
            mems = [(tuple(m['cue']), tuple(m['noncue']), sorted(set(m['cue']) | set(m['noncue']))) for m in fam['mems']]
            res = L.solve(cfg, mems)
            e = dict(n_mem=len(mems), lp_status=res['status'])
            if res['status'] == 0:
                x = res['x']; Gv = res['G']; w = x / Gv; pairs = res['pairs']
                X = np.zeros((96, 96))
                for (i, j), v in zip(pairs, x): X[i, j] = v
                inp = X.sum(0); nonhub = [j for j in range(96) if j not in cfg.hubs]
                e.update(bounds_ok=bool((x >= res['lb'] - 1e-7).all() and (x <= res['ub'] + 1e-7).all()), w_min=float(w.min()), w_max=float(w.max()), w_in_range=bool(w.min() >= cfg.lbw - 1e-7 and w.max() <= 1 + 1e-7),
                         x_max=float(x.max()), cap_ok=bool(x.max() <= L.CAP + 1e-7), H_ok=bool((inp <= cfg.Hv + 1e-6).all()), max_input_nonhub=float(inp[nonhub].max()),
                         no_new_pairs=bool(((X > 0) <= (G > 0)).all()), dale_ok=bool((X >= 0).all()))
                for thr in (16.5, 15.0):
                    full_ok = 0; part_bad = 0; npart = 0
                    for (C, N, M) in mems:
                        fs = set(int(i) for i in np.where(L.cascade(X, C, thr=thr))[0]); full_ok += int(fs == set(M))
                        for S in itertools.combinations(C, 3):
                            npart += 1; fs3 = set(int(i) for i in np.where(L.cascade(X, S, thr=thr))[0]); part_bad += int(fs3 != set(S))
                    e['cascade_%s' % thr] = dict(full_exact=full_ok, partial_clean=npart - part_bad, n_partial=npart)
            out['%s|%s|%s' % (vn, fn, str(srcs.index(src)))] = e
    print(key, 'done src', flush=True)
json.dump(out, open('verify_%s.json' % key, 'w'))
