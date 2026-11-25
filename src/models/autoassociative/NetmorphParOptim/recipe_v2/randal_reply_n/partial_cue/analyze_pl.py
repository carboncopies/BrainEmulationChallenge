#!/usr/bin/env python3
"""rawB_*.json -> resultsB_tables.md, eventsB.json. Definitions: PREREGISTRATION_B.md. Includes threshold-model reference (fllib, same weights, same cues)."""
import json, glob, sys, collections
import numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_learn'); sys.path.insert(0, HERE)
import fllib as FL
NP = 96; WC = 30.0
def rows_of(d):
    sp = {int(k): np.array(sorted(v)) for k, v in d['spikes'].items()}; A = set(d['A']); key = 's%d' % d['seed']
    net = FL.Net(key); Fm, _ = FL.build_F(net, [sorted(A)], 3.0 if d['arm'] == 'LH' else None)
    def w(i, a, b): x = sp.get(i); return x[(x >= a) & (x < b)] if x is not None else np.array([])
    pyr = np.sort(np.concatenate([sp[i] for i in sp if i < NP])) if any(i < NP for i in sp) else np.array([])
    npyr = lambda a, b: int(((pyr >= a) & (pyr < b)).sum()); rows = []
    for e in d['events']:
        t = e['t']; cue = set(e['cue']); r = dict(seed=d['seed'], arm=d['arm'], r=d['r'], f=d['f'], kind=e['kind'], ncue=len(cue), label=e['label'])
        r['cont'] = npyr(t - 1500, t) > 60
        nonc = [m for m in A if m not in cue]
        r['complete'] = all(len(w(m, t, t + WC)) > 0 for m in nonc) if e['kind'] != 'unrel' else False
        r['recruit'] = any(len(w(i, t, t + WC)) > 0 for i in range(NP) if i not in cue)
        r['spurious'] = any(len(w(i, t, t + WC)) > 0 for i in range(NP) if i not in A and i not in cue)
        r['n_recruited'] = int(sum(len(w(i, t, t + WC)) > 0 for i in range(NP) if i not in cue))
        r['late_member'] = int(sum(len(w(m, t + 15, t + 450)) for m in A)); r['nonmember_pyr'] = int(sum(len(w(i, t, t + 450)) for i in range(NP) if i not in A))
        r['pyr450'] = npyr(t, t + 450); r['runaway'] = r['pyr450'] > 50; r['clean'] = r['late_member'] == 0 and r['nonmember_pyr'] <= 2
        cm = np.zeros((1, NP), bool); cm[0, list(cue)] = True; fm = FL.cascade_batch(Fm, cm)[0]
        r['th_complete'] = bool(all(fm[m] for m in nonc)) if e['kind'] != 'unrel' else False; r['th_recruit'] = bool(fm.sum() > len(cue)); r['th_n_recruited'] = int(fm.sum() - len(cue))
        rows.append(r)
    return rows
def rate(rs, key, excl=True):
    rs = [x for x in rs if not (excl and x['cont'])]; return (sum(bool(x[key]) for x in rs), len(rs))
def fmt(p): return '%d/%d' % p if p[1] else '-'
if __name__ == '__main__':
    allr = []; flags = {}
    for fn in sorted(glob.glob(HERE + 'rawB_*.json')):
        d = json.load(open(fn)); allr += rows_of(d); flags[d['tag']] = d['flags']
    json.dump(allr, open(HERE + 'eventsB.json', 'w'))
    out = ['# addendum B results (A17 alone; k/n over non-contaminated events; th = threshold-model reference on the same cues and weights)\n',
           '| seed | arm | r | GABA | full complete | full clean | p75 complete | p50 complete | p25 recruit | p1 recruit | unrel recruit | spurious (any) | contaminated | runaway | th p75 | th p50 | th p25 recruit | members >3T |', '|' + '---|' * 18]
    for (s, a, r, f) in sorted(set((x['seed'], x['arm'], x['r'], x['f']) for x in allr)):
        rs = [x for x in allr if (x['seed'], x['arm'], x['r'], x['f']) == (s, a, r, f)]; k = lambda kind: [x for x in rs if x['kind'] == kind]
        fl = flags['s%d_%s_r%g_f%g' % (s, a, r, f)]
        out.append('| %d | %s | %g | x%g | %s | %s | %s | %s | %s | %s | %s | %d | %d | %d | %s | %s | %s | %d/17 |' % (s, a, r, f, fmt(rate(k('full'), 'complete')), fmt(rate(k('full'), 'clean')), fmt(rate(k('p75'), 'complete')), fmt(rate(k('p50'), 'complete')),
              fmt(rate(k('p25'), 'recruit')), fmt(rate(k('p1'), 'recruit')), fmt(rate(k('unrel'), 'recruit')), sum(x['spurious'] for x in rs), sum(x['cont'] for x in rs), sum(x['runaway'] for x in rs),
              fmt(rate(k('p75'), 'th_complete', False)), fmt(rate(k('p50'), 'th_complete', False)), fmt(rate(k('p25'), 'th_recruit', False)), fl['members_over_3T']))
    open(HERE + 'resultsB_tables.md', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
