import json, numpy as np, mtlib as M
rows = []
for s in M.SEEDS:
    d = json.load(open('c1_s%d.json' % s)); r = dict(seed=s, n_cands=d['n_cands'])
    for key in ('nocap', 'cap'):
        j = {int(k): v['joint_feasible'] for k, v in d[key].items()}; ok = [p for p, v in j.items() if v >= 0.5]; r['Pc_' + key] = max(ok) if ok else 0
        r['cellfeas_P8_' + key] = d[key]['8']['cell_feasible']
    r['spearman_s_strongindeg_P8'] = d['spearman_s_vs_strong_indeg_P8'][0]; r['lowest10_strong_indeg_mean'] = float(np.mean(d['lowest10_strong_indeg'])); r['median_strong_indeg'] = d['median_strong_indeg']
    rows.append(r); print(r)
json.dump(rows, open('c1_summary.json', 'w'), indent=1)
print('Spearman>=0.5 in', sum(r['spearman_s_strongindeg_P8'] >= 0.5 for r in rows), 'of 10; lowest10 below median in', sum(r['lowest10_strong_indeg_mean'] < r['median_strong_indeg'] for r in rows))
print('Pc_cap<=3', sum(r['Pc_cap'] <= 3 for r in rows), 'Pc_nocap', [r['Pc_nocap'] for r in rows])
