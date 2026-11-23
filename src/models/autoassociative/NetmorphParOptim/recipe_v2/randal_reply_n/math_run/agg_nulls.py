import json, numpy as np, glob
KEYS = ['s16180','s27182','s31415','s11111','s22222','s33333','s44444','s55555','s66666','s77777']
TY = ['grown', 'ER', 'CM', 'VS', 'CAPr', 'CAPs', 'SYN8', 'SYN5', 'CAPr_SYN5']
FAM = ['m2_k0', 'm2_k1', 'm2_k3', 'm4_k0']
data = {k: json.load(open('nulls_%s.json' % k)) for k in KEYS}
def val(k, t, v, f, stat='res'):
    xs = [r['res'][v][f] for r in data[k] if r['type'] == t and v in r['res'] and f in r['res'][v]]
    return float(np.median(xs)) if xs else float('nan')
def gs(k, t, f):
    xs = [r['stats'][f] for r in data[k] if r['type'] == t]; return float(np.mean(xs))
out = []; P = out.append
P('## Parts 2 and 3: capacity on grown, null and pruned graphs (median over 3 rewires where random; best of 5 greedy restarts; median over 10 models; per-model ratio to grown in the last columns)')
for v in ('primary', 'Hinf'):
    P('\n### variant `%s`' % v)
    P('| graph | in-degree CV (mean) | share pairs >= 5 syn | memories k=0 | k<=1 | k<=3 | 8-cell k=0 | candidates m2 (median) | target cells (median) | k<=1 ratio to grown: median [models <= 25% / <= 50% / >= 80% of grown] |'); P('|---|---|---|---|---|---|---|---|---|---|')
    for t in TY:
        row = []
        for f in FAM: row.append('%g (%d-%d)' % (np.median([val(k, t, v, f) for k in KEYS]), min(val(k, t, v, f) for k in KEYS), max(val(k, t, v, f) for k in KEYS)))
        cand = np.median([val(k, t, v, 'cands_m2') for k in KEYS]); tc = np.median([val(k, t, v, 'target_cells_m2') for k in KEYS])
        rat = [val(k, t, v, 'm2_k1') / max(val(k, 'grown', v, 'm2_k1'), 1e-9) for k in KEYS]
        P('| %s | %.2f | %.3f | %s | %g | %g | %.1f / %d / %d / %d |' % (t, np.mean([gs(k, t, 'in_cv') for k in KEYS]), np.mean([gs(k, t, 'share_ge5') for k in KEYS]), ' | '.join(row), cand, tc, np.median(rat), sum(r <= 0.25 for r in rat), sum(r <= 0.5 for r in rat), sum(r >= 0.8 for r in rat)))
P('\n### graph statistics (mean over models)')
P('| graph | edges | p | in-degree mean | in-degree median | in-degree max | in-degree CV | out-degree CV | synapses/pair mean | share single | share >= 5 | max synapses/pair |'); P('|---|---|---|---|---|---|---|---|---|---|---|---|')
for t in TY: P('| %s | ' % t + ' | '.join('%.2f' % np.mean([gs(k, t, f) for k in KEYS]) for f in ('edges', 'p', 'in_mean', 'in_median', 'in_max', 'in_cv', 'out_cv', 'syn_mean', 'share_single', 'share_ge5', 'syn_max')) + ' |')
# prediction scoring helpers
er0 = sum(all(r['res']['Hinf']['cands_m2'] == 0 for r in data[k] if r['type'] == 'ER') for k in KEYS)
P('\nP2.1 ER: models with zero candidate cue sets in all 3 rewires: %d/10' % er0)
for t in ('CM', 'VS', 'CAPr', 'CAPs'):
    rat = [val(k, t, 'Hinf', 'm2_k1') / max(val(k, 'grown', 'Hinf', 'm2_k1'), 1e-9) for k in KEYS]
    P('%s: Hinf k<=1 count / grown: %s | <=25%%: %d/10, <=50%%: %d/10, >=50%%: %d/10' % (t, [round(x, 2) for x in rat], sum(x <= .25 for x in rat), sum(x <= .5 for x in rat), sum(x >= .5 for x in rat)))
for t in ('SYN8', 'SYN5', 'CAPr_SYN5'):
    rat = [val(k, t, 'Hinf', 'm2_k1') / max(val(k, 'grown', 'Hinf', 'm2_k1'), 1e-9) for k in KEYS]
    P('%s: Hinf k<=1 count / grown: %s | within 20%%: %d/10, <=50%%: %d/10' % (t, [round(x, 2) for x in rat], sum(abs(x - 1) <= .2 for x in rat), sum(x <= .5 for x in rat)))
# success rule on primary
base = {'m2_k0': 1.5, 'm2_k1': 2, 'm2_k3': 2}; thr = {'m2_k0': 5, 'm2_k1': 6, 'm2_k3': 6}
for t in TY:
    ok = [f for f in ('m2_k0', 'm2_k1', 'm2_k3') if np.median([val(k, t, 'primary', f) for k in KEYS]) >= thr[f] and sum(val(k, t, 'primary', f) >= base[f] for k in KEYS) >= 8]
    P('success rule (primary) for %s: %s' % (t, ok if ok else 'none'))
open('results_nulls.md', 'w').write('\n'.join(out)); print('\n'.join(out))
