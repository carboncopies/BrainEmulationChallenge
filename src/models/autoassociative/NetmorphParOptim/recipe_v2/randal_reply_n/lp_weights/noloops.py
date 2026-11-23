"""Mechanism check (offline, threshold model): take the R3-programmed designs of ripple_overlap_j (c = 0), remove the non-cue->non-cue loops, re-evaluate cross-completion."""
import sys, json, glob, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j')
import ovlib as O, lpw_lib as L
ev = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/events_ov.json'))
sim = {(e['tag'].rsplit('_c0', 1)[0], e['group']): e for e in ev if e['c'] == 0 and e['sg'] == 0 and e['label'] == 'full'}
res = {}
for f in sorted(glob.glob('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/design_*.json')):
    nm = f.split('design_')[1][:-5]; key, fam = nm.split('_'); d = json.load(open(f))
    if fam not in ('F1', 'F2', 'F3', 'F8'): continue
    Dm, P = O.load(key); groups = [(g['members'], g['cue']) for g in d['groups']]
    X = np.zeros((116, 116))
    for a, b, cond, g in O.pair_list_ov(Dm, groups, 0.0): X[a, b] = cond
    Xp = X[:96, :96].copy(); X2 = Xp.copy()
    for g in d['groups']:
        for a in g['noncue']:
            for b in g['noncue']:
                if a != b: X2[a, b] = 0.0
    for gi in d['cued']:
        g = d['groups'][gi]; M = set(g['members']); e = sim.get((nm, gi))
        if e is None: continue
        for thr in (16.5, 15.0):
            r = res.setdefault((fam, thr), dict(n=0, sim_clean=0, loops_clean=0, noloops_clean=0, noloops_complete=0))
            for nm2, XX in (('loops', Xp), ('noloops', X2)):
                fs = set(int(i) for i in np.where(L.cascade(XX, g['cue'], thr=thr))[0]); clean = (set(g['noncue']) <= fs) and not (fs - M)
                r[nm2 + '_clean'] += int(clean)
                if nm2 == 'noloops': r['noloops_complete'] += int(set(g['noncue']) <= fs)
            r['n'] += 1; r['sim_clean'] += int(e['clean'])
for (fam, thr), r in sorted(res.items()): print(fam, 'thr', thr, r)
