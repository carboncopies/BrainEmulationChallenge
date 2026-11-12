"""Scoring (run later). usage: score.py [--runs runs.csv] [--out score_results.json]
Needs: runs.csv, heldout_configs.csv, preds_heldout_ml.csv, preds_heldout_mech.csv.
run_id conventions: held-out H-<cfg>-s<seed> (arm column = ML or MECH is NOT used; held-out runs are shared, arm column 'HELD'),
training T-<ML|MECH>-..., nominations N-<ML|MECH>-<k>-s<seed> (arm column = ML|MECH)."""
import argparse, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import r2_score, mean_absolute_error, mean_poisson_deviance
from h2h_common import *
TG = COMP + ['J']

def metrics(y, p, base, lo=None, hi=None):
    y = np.asarray(y, float); p = np.asarray(p, float)
    r = {'spearman': spearmanr(y, p)[0] if len(y) > 2 and np.std(p) > 0 and np.std(y) > 0 else np.nan,
         'R2': r2_score(y, p) if len(y) > 1 else np.nan, 'MAE': mean_absolute_error(y, p)}
    pp = np.maximum(p, 1e-6); db = mean_poisson_deviance(y, np.full(len(y), max(base, 1e-6)))
    r['poisson_D2'] = 1 - mean_poisson_deviance(y, pp) / db if db > 0 else np.nan
    r['cov80'] = float(np.mean((y >= lo) & (y <= hi))) if lo is not None else np.nan
    r['n'] = len(y); return r

def heldout(runs, bB):
    cfgs = pd.read_csv(H2H + '/heldout_configs.csv'); out = {}
    h = runs[runs['run_id'].str.startswith('H-') & (runs['rc'] == 0)].copy()
    h['config_id'] = h['config_id'].astype(str)
    cm = h.groupby('config_id')[COMP + ['J']].mean().reset_index()
    for arm, fn in [('ML', 'preds_heldout_ml.csv'), ('MECH', 'preds_heldout_mech.csv')]:
        P = pd.read_csv(H2H + '/' + fn); out[arm] = {}
        for level, A in [('per_run', h), ('config_mean', cm)]:
            M = A.merge(P, on='config_id', suffixes=('', '_p'))
            out[arm][level] = {}
            for t in TG:
                if t == 'J': pm, lo, hi = M['J_pred'], None, None; base = bB['J'].mean()
                else: pm, lo, hi = M[t + '_mean'], M[t + '_lo80'].values, M[t + '_hi80'].values; base = bB[t].mean()
                out[arm][level][t] = metrics(M[t], pm, base, lo, hi)
    return out

def training(runs):
    out = {}
    for arm in ['ML', 'MECH']:
        r = runs[(runs['arm'] == arm) & runs['run_id'].str.startswith('T-') & (runs['rc'] == 0)].sort_values('timestamp').reset_index(drop=True)
        d = {'n_runs': len(r)}
        for nm, th in [('T1', T1), ('T2', T2)]:
            hit = np.where((r['J'] >= th) & r['soft_clean'].astype(bool))[0]
            d['first_run_reaching_' + nm] = int(hit[0]) + 1 if len(hit) else None
        for k in (5, 10):
            s = r.iloc[:k]
            d['best_J_after_%d' % k] = float(s['J'].max()) if len(s) else None
            sc = s[s['soft_clean'].astype(bool)]; d['best_softclean_J_after_%d' % k] = float(sc['J'].max()) if len(sc) else None
        out[arm] = d
    return out

def nominations(runs):
    out = {}
    for arm in ['ML', 'MECH']:
        r = runs[(runs['arm'] == arm) & runs['run_id'].str.startswith('N-') & (runs['rc'] == 0)]
        d = {'n_runs': len(r), 'mean_J': float(r['J'].mean()) if len(r) else None}
        for nm, th in [('T1', T1), ('T2', T2)]:
            d['hits_' + nm] = int(((r['J'] >= th) & r['soft_clean'].astype(bool)).sum()); d['hit_rate_' + nm] = d['hits_' + nm] / 9.0
        g = r.groupby('config_id'); d['seed_CV'] = {}
        for c, gg in g:
            d['seed_CV'][c] = {t: float(gg[t].std(ddof=1) / gg[t].mean()) if len(gg) > 1 and gg[t].mean() > 0 else None for t in COMP + ['J']}
        out[arm] = d
    return out

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--runs', default=H2H + '/runs.csv'); ap.add_argument('--out', default=H2H + '/score_results.json'); a = ap.parse_args()
    runs = pd.read_csv(a.runs); bB = load_batchB()
    res = {'heldout': heldout(runs, bB), 'training': training(runs), 'nominations': nominations(runs)}
    json.dump(res, open(a.out, 'w'), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float))
