"""C1: random-draw feasibility vs P and margins. usage: c1_run.py SEED -> c1_s<seed>.json"""
import sys, json, time, numpy as np
import mtlib as M, c1lib as L
from scipy.stats import spearmanr
s = int(sys.argv[1]); G = M.G(s); rs = np.random.RandomState(s); t0 = time.time()
cands = M.O.candidates(G, 2); out = dict(seed=s, n_cands=len(cands)); indeg = (G >= 4.125).sum(0)
PS = [1, 2, 4, 8, 16, 32]; ND = 12
for cap in (True, False):
    key = 'cap' if cap else 'nocap'; out[key] = {}
    for Pn in PS:
        feas = []; cellfrac = []; smin = []; cs = {}
        for d in range(ND):
            idx = rs.choice(len(cands), size=min(Pn, len(cands)), replace=False)
            mems = [(c, tuple(rs.choice(t, 2, replace=False))) for c, t in (cands[i] for i in idx)]
            cells = range(96); ss = []
            for i in cells:
                sv, js, x = L.solve_cell(G, i, mems, cap=cap)
                ss.append(sv)
                if Pn == 8 and cap: cs.setdefault(i, []).append(sv)
            ss = np.array(ss); feas.append(bool((ss >= -1e-9).all())); cellfrac.append(float((ss >= -1e-9).mean())); smin.append(float(ss.min()))
        out[key][Pn] = dict(joint_feasible=float(np.mean(feas)), cell_feasible=float(np.mean(cellfrac)), s_min_mean=float(np.mean(smin)))
        if Pn == 8 and cap:
            ms = np.array([np.mean(cs[i]) if i in cs else np.nan for i in range(96)]); ok = ~np.isnan(ms)
            rho = spearmanr(ms[ok], indeg[ok]); out['spearman_s_vs_strong_indeg_P8'] = [float(rho.statistic), float(rho.pvalue)]
            lowest = np.argsort(np.where(ok, ms, 1e9))[:10]; out['lowest10_cells'] = [int(c) for c in lowest]; out['lowest10_strong_indeg'] = [int(indeg[c]) for c in lowest]
            out['median_strong_indeg'] = float(np.median(indeg)); out['mean_s_by_cell_P8_quartiles'] = [float(np.nanpercentile(ms, q)) for q in (10, 50, 90)]
    print(s, key, {k: v['joint_feasible'] for k, v in out[key].items()}, round(time.time() - t0), flush=True)
json.dump(out, open('c1_s%d.json' % s, 'w'))
