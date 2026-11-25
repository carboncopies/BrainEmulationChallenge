#!/usr/bin/env python3
"""Offline: new measures (duration, spikes per member, non-member spikes, termination) on STORED partial_cue runs (addendum B LH, C W70, main D0).
No simulation. Output baseline.json / printed table. Same definitions are used in analyze_nr.py."""
import json, glob, numpy as np
PC = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
NP = 96
def measures(d, A, ev_kind_key='kind'):
    sp = {int(k): np.array(sorted(v)) for k, v in d['spikes'].items()}
    pyr = {i: sp[i] for i in sp if i < NP}
    rows = []
    for e in d['events']:
        t = e['t']; cue = set(e['cue']); mem = set(A) if A is not None else set(e.get('members', []))
        def cnt(cells, a, b): return int(sum(((pyr[i] >= a) & (pyr[i] < b)).sum() for i in cells if i in pyr))
        allp = np.sort(np.concatenate([x[(x >= t) & (x < t + 1000)] for x in pyr.values()])) if pyr else np.array([])
        last = float(allp[-1] - t) if len(allp) else 0.0
        nonc = [m for m in mem if m not in cue]
        rows.append(dict(kind=e[ev_kind_key], ncue=len(cue),
            complete=bool(nonc) and all(i in pyr and (((pyr[i] >= t) & (pyr[i] < t + 30)).any()) for i in nonc),
            last_ms=round(last, 1), pyr450=cnt(range(NP), t, t + 450), late100=cnt(range(NP), t + 100, t + 450),
            nonmember450=cnt([i for i in range(NP) if i not in mem and i not in cue], t, t + 450),
            per_member=round(cnt(mem, t, t + 450) / max(1, len(mem)), 2),
            cont=cnt(range(NP), t - 1500, t) > 60))
    return rows
def summ(rows, kinds=('full', 'p75', 'p50')):
    c = [r for r in rows if r['kind'] in kinds and r['complete'] and not r['cont']]
    if not c: return dict(n=0)
    L = [r['last_ms'] for r in c]
    return dict(n=len(c), median_last_ms=float(np.median(L)), max_last_ms=max(L), frac_stop100=sum(r['late100'] == 0 for r in c) / len(c),
                median_pyr450=float(np.median([r['pyr450'] for r in c])), median_spk_per_member=float(np.median([r['per_member'] for r in c])),
                events_with_nonmember=sum(r['nonmember450'] > 0 for r in rows if not r['cont']), n_all=sum(not r['cont'] for r in rows))
if __name__ == '__main__':
    out = {}
    for fn in sorted(glob.glob(PC + 'rawB_*_LH_*.json')) + sorted(glob.glob(PC + 'rawC_*_W70_*.json')):
        d = json.load(open(fn)); rows = measures(d, d['A']); out[d['tag'] + ('' if 'rawB' in fn else '_C')] = summ(rows)
    for fn in sorted(glob.glob(PC + 'raw_s*_D0_r0.56_f1.json')):
        d = json.load(open(fn)); rows = []
        for e in d['events']: e['members'] = d['groups'][e['group']]['members']
        rows = measures(d, None)
        k = lambda kind: [r for r in rows if r['kind'] == kind and not r['cont']]
        out[d['tag']] = dict(full_complete='%d/%d' % (sum(r['complete'] for r in k('full')), len(k('full'))), p3_complete='%d/%d' % (sum(r['complete'] for r in k('p3')), len(k('p3'))),
                             full_median_last_ms=float(np.median([r['last_ms'] for r in k('full')])), nonmember_events=sum(r['nonmember450'] > 0 for r in rows if not r['cont']), n=len(rows))
    json.dump(out, open('baseline.json', 'w'), indent=1)
    for k, v in out.items(): print(k, v)
