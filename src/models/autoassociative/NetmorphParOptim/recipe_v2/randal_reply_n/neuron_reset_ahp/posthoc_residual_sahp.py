#!/usr/bin/env python3
"""POST HOC (not preregistered): reconstructed residual sAHP conductance at cue onset, per member cell, from recorded spikes and the arm's sAHP
parameters (NES AHPCLIP: g = min(peak * sum of normalised rise/decay kernels, gmax)); relation to 50%/75% completion. Output posthoc_residual_sahp.json."""
import json, glob, numpy as np
P = {'N0': (1., 2., 30., 300.), 'R': (1., 2., 30., 300.), 'S2': (2., 4., 30., 1000.), 'RS2': (2., 4., 30., 1000.), 'RS3': (3., 6., 30., 1500.)}
def gs(sp, t, g, gm, tr, td):
    s = sp[sp < t]; s = s[s > t - 10 * td]
    if not len(s): return 0.0
    tp = tr * td / (td - tr) * np.log(td / tr); nrm = np.exp(-tp / td) - np.exp(-tp / tr)
    return float(min(g * ((np.exp(-(t - s) / td) - np.exp(-(t - s) / tr)) / nrm).sum(), gm))
out = {}
for fn in sorted(glob.glob('raw_LH_*.json')):
    d = json.load(open(fn)); arm = d['neuron_arm']; A = d['A']; sp = {int(k): np.array(v) for k, v in d['spikes'].items()}
    rows = []
    for e in d['events']:
        if e['kind'] not in ('p50', 'p75'): continue
        t = e['t']; nonc = [m for m in A if m not in e['cue']]
        res = [gs(sp.get(m, np.array([])), t, *P[arm]) for m in nonc]
        comp = all(m in sp and ((sp[m] >= t) & (sp[m] < t + 30)).any() for m in nonc)
        rows.append(dict(kind=e['kind'], complete=comp, mean_residual_nS=round(float(np.mean(res)), 3)))
    out[d['nr_tag']] = rows
    for kind in ('p50', 'p75'):
        c = [r['mean_residual_nS'] for r in rows if r['kind'] == kind and r['complete']]; f = [r['mean_residual_nS'] for r in rows if r['kind'] == kind and not r['complete']]
        print('%-24s %s complete %d (resid median %s) / fail %d (resid median %s)' % (d['nr_tag'], kind, len(c), '%.2f' % np.median(c) if c else '-', len(f), '%.2f' % np.median(f) if f else '-'))
json.dump(out, open('posthoc_residual_sahp.json', 'w'), indent=1)
