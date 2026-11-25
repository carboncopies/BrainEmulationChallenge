#!/usr/bin/env python3
"""raw_*.json -> tables (results_tables.md) + events.json. Definitions: PREREGISTRATION.md."""
import json, glob, collections
import numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
NP = 96; WC = 30.0
def rows_of(d):
    sp = {int(k): np.array(sorted(v)) for k, v in d['spikes'].items()}; G = d['groups']; allmem = set(x for g in G for x in g['members'])
    def w(i, a, b): x = sp.get(i); return x[(x >= a) & (x < b)] if x is not None else np.array([])
    pyr = np.sort(np.concatenate([sp[i] for i in sp if i < NP])) if any(i < NP for i in sp) else np.array([])
    npyr = lambda a, b: int(((pyr >= a) & (pyr < b)).sum()); rows = []
    for e in d['events']:
        t = e['t']; g = G[e['group']]; nc = g['noncue']; mem = set(g['members']); cue = set(e['cue'])
        r = dict(seed=d['seed'], design=d['design'], r=d['r'], f=d['f'], kind=e['kind'], label=e['label'], group=e['group'])
        r['cont'] = npyr(t - 1500, t) > 60
        r['complete'] = all(len(w(m, t, t + WC)) > 0 for m in nc)
        # recruitment: any Pyr cell outside the cue cells fires in [t, t+30)
        r['recruit'] = any(len(w(i, t, t + WC)) > 0 for i in range(NP) if i not in set(c for _, c in e['cues']))
        r['spurious'] = any(len(w(i, t, t + WC)) > 0 for i in range(NP) if i not in allmem and i not in set(c for _, c in e['cues']))
        r['late_member'] = int(sum(len(w(m, t + 15, t + 450)) for m in mem)); r['nonmember_pyr'] = int(sum(len(w(i, t, t + 450)) for i in range(NP) if i not in allmem))
        r['pyr450'] = npyr(t, t + 450); r['runaway'] = r['pyr450'] > 50
        r['clean'] = r['late_member'] == 0 and r['nonmember_pyr'] <= 2
        r['n_noncue_fired'] = sum(len(w(m, t, t + WC)) > 0 for m in nc)
        if e['kind'] == 'x2':
            oth = G[e['other']]['noncue']; r['complete_other'] = all(len(w(m, t, t + WC)) > 0 for m in oth)
        rows.append(r)
    return rows
def rate(rs, key, excl=True):
    rs = [x for x in rs if not (excl and x['cont'])]; return (sum(x[key] for x in rs), len(rs))
def fmt(p): return '%d/%d' % p if p[1] else '-'
if __name__ == '__main__':
    allrows = []
    for fn in sorted(glob.glob(HERE + 'raw_*.json')): allrows += rows_of(json.load(open(fn)))
    json.dump(allrows, open(HERE + 'events.json', 'w'))
    out = ['# partial_cue results tables (non-contaminated events; cont = excluded count; k/n)\n']
    conds = sorted(set((x['design'], x['r'], x['f']) for x in allrows))
    out.append('| design | r | GABA | seeds | full complete | full clean | p3 complete | p2 complete | p1 recruit | x2 recruit | p3 recruit | p2 recruit | contaminated | runaway (all) |\n|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
    for dsg, r, f in conds:
        rs = [x for x in allrows if (x['design'], x['r'], x['f']) == (dsg, r, f)]; k = lambda kind: [x for x in rs if x['kind'] == kind]
        seeds = sorted(set(x['seed'] for x in rs))
        out.append('| %s | %g | x%g | %s | %s | %s | %s | %s | %s | %s | %s | %s | %d | %d |' % (dsg, r, f, ','.join(str(s)[-5:] for s in seeds), fmt(rate(k('full'), 'complete')), fmt(rate(k('full'), 'clean')),
                   fmt(rate(k('p3'), 'complete')), fmt(rate(k('p2'), 'complete')), fmt(rate(k('p1'), 'recruit')), fmt(rate(k('x2'), 'recruit')), fmt(rate(k('p3'), 'recruit')), fmt(rate(k('p2'), 'recruit')),
                   sum(x['cont'] for x in rs), sum(x['runaway'] for x in rs)))
    open(HERE + 'results_tables.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
