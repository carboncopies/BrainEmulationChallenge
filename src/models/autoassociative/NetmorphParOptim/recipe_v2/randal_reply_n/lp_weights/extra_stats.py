import json, numpy as np, lpw_lib as L
import sys
KEYS = [sys.argv[1]]
rows = []
for k in KEYS:
    G = L.load(k); r = dict(model=k)
    for vn, kw in (('Hinf', dict(L.PRIMARY, H=1e9)), ('primary', L.PRIMARY)):
        cfg = L.Cfg(G, **kw)
        for m in (2, 4, 6):
            c = L.candidates(cfg, m); tg = sorted(set(n for C, tl in c for n in tl)); r['%s_m%d_cands' % (vn, m)] = len(c); r['%s_m%d_target_cells' % (vn, m)] = len(tg)
    base = 0.1 * G.sum(0); r['cells_baseline_ge_33'] = int((base >= 33).sum()); r['cells_in_sum_gt_330'] = int((G.sum(0) > 330).sum())
    cfg = L.Cfg(G, **dict(L.PRIMARY, H=1e9)); c = L.candidates(cfg, 2); tg = sorted(set(n for C, tl in c for n in tl))
    r['Hinf_target_cells'] = len(tg); r['Hinf_targets_with_inputsum_gt_300'] = int(sum(G.sum(0)[n] > 300 for n in tg)); r['Hinf_targets_median_inputsum'] = float(np.median([G.sum(0)[n] for n in tg]))
    r['all_cells_median_inputsum'] = float(np.median(G.sum(0)))
    # weight distribution of the final primary / hubs_waived solution, m2_k3
    cj = json.load(open('cap_%s.json' % k))
    for vn in ('primary', 'hubs_waived'):
        fam = cj[vn]['fams']['m2_k3']
        if 'x' in fam:
            x = np.array(fam['x']); pr = fam['pairs']; Gv = np.array([G[i, j] for i, j in pr]); w = x / Gv
            r['%s_k3_w_quantiles' % vn] = [float(np.percentile(w, q)) for q in (1, 25, 50, 75, 99, 99.9)]
            r['%s_k3_x_median_vs_grownG_median' % vn] = [float(np.median(x)), float(np.median(Gv))]
            r['%s_k3_total_x_vs_grown' % vn] = [float(x.sum()), float(Gv.sum())]
            r['%s_k3_frac_total_x_in_raised' % vn] = float(x[w > 0.1001].sum() / x.sum())
    rows.append(r); print(r, flush=True)
json.dump(rows, open('extra_%s.json' % KEYS[0], 'w'), indent=1)
