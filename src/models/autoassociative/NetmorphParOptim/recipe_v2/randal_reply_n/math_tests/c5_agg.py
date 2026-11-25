import json, numpy as np
from scipy.stats import spearmanr
b = json.load(open('c5_base.json')); a = json.load(open('c5_arms.json'))
w = 0
for s, r in b.items():
    m = float(np.mean(r['surrogate_K42'])); ok = abs(m - r['K42_greedy']) <= 1; w += ok; print(s, r['K42_greedy'], round(m, 2), ok)
print('surrogate within +-1:', w, 'of', len(b))
rows = [(k, v['K42_greedy'], v['proxies']) for k, v in b.items()] + [(k, v['K42_greedy'], v['proxies']) for k, v in a.items()]
def sp(rows_, name):
    k = [r[1] for r in rows_]; return {p: round(float(spearmanr(k, [r[2][p] for r in rows_]).statistic), 2) for p in rows_[0][2]}
print('all', len(rows), sp(rows, 'all')); base_rows = [(k, v['K42_greedy'], v['proxies']) for k, v in b.items()]; print('base only', sp(base_rows, 'b'))
# leave-one-out linear prediction using n_strong
x = np.array([r[2]['n_strong'] for r in rows], float); y = np.array([r[1] for r in rows], float); err = []
for i in range(len(x)):
    m = np.ones(len(x), bool); m[i] = False; c = np.polyfit(x[m], y[m], 1); err.append(abs(np.polyval(c, x[i]) - y[i]))
print('LOO MAE n_strong all-arms', round(float(np.mean(err)), 2), 'mean K42', y.mean())
