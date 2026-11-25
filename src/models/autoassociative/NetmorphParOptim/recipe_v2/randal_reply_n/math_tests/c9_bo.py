"""C9: noise/power arithmetic and Wasserstein ordering of strong in-degree distributions vs K42 (uses c5_*.json, c2_*.json)"""
import json, glob, numpy as np
from scipy.stats import wasserstein_distance, spearmanr
import mtlib as M
FR = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run/'
base = json.load(open('c5_base.json')); arms = json.load(open('c5_arms.json'))
rows = {}
def din(P): S = (P >= 4.125).astype(float); np.fill_diagonal(S, 0); return np.sort(S.sum(0))
import recipelib as L
for s in M.SEEDS: rows['base_s%d' % s] = dict(K42=base[str(s)]['K42_greedy'], din=din(M.G(s)))
for tag, v in arms.items():
    D = L.Dump(FR + 'grow_%s/viz/sample_0000.json' % tag); P = D.G[:96, :96].copy(); np.fill_diagonal(P, 0); rows[tag] = dict(K42=v['K42_greedy'], din=din(P))
best = max(rows, key=lambda k: rows[k]['K42']); ref = rows[best]['din']
names = list(rows); k = np.array([rows[n]['K42'] for n in names]); w = np.array([wasserstein_distance(rows[n]['din'], ref) for n in names])
rho = spearmanr(k, -w); out = dict(n_graphs=len(names), best_graph=best, spearman_K42_vs_negW1=[float(rho.statistic), float(rho.pvalue)])
sd_base = float(np.std([base[str(s)]['K42_greedy'] for s in M.SEEDS], ddof=1)); out['K42_sd_baseline_10seeds'] = sd_base
B1P = [v['K42_greedy'] for t, v in arms.items() if t.startswith('B1P')]; out['K42_B1P'] = B1P; out['K42_sd_B1P'] = float(np.std(B1P, ddof=1)) if len(B1P) > 1 else None
sig = max(sd_base, out['K42_sd_B1P'] or 0)
for delta in (1, 2): out['n_per_arm_for_delta%d' % delta] = float(np.ceil(2 * (1.96 + 0.84) ** 2 * sig ** 2 / delta ** 2))
out['noise_over_effect_2'] = sig / 2; out['budget_6param_GP_growths'] = 'about 15 per dimension x 6 = 90 (rule of thumb, Eriksson-Poloczek: >= 100 evals); at 25 min per growth and 3 concurrent = 12.5 h'
json.dump(out, open('c9.json', 'w'), indent=1, default=float); print(json.dumps(out, default=float)); print({n: (rows[n]['K42'], round(float(x), 2)) for n, x in zip(names, w)})
