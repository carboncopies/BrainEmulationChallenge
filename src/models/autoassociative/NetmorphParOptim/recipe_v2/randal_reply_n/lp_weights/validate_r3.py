"""Step E: R3-programmed existing overlap designs (c = 0) evaluated in the cascade threshold model vs the sim outcomes. Offline."""
import sys, json, glob, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j')
import ovlib as O, lpw_lib as L
ev = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/events_ov.json'))
sim = {}
for e in ev:
    if e['c'] == 0 and e['sg'] == 0 and e['label'] == 'full': sim[(e['tag'].rsplit('_c0', 1)[0], e['group'])] = e   # tag like s16180_F2_c0_sg0
rows = []; D = {}
for f in sorted(glob.glob('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/design_*.json')):
    nm = f.split('design_')[1][:-5]; key, fam = nm.split('_'); d = json.load(open(f))
    if fam not in ('F1', 'F2', 'F3', 'F8'): continue
    Dm, P = O.load(key)
    groups = [(g['members'], g['cue']) for g in d['groups']]
    pl = O.pair_list_ov(Dm, groups, 0.0)
    X = np.zeros((116, 116))
    for a, b, cond, g in pl: X[a, b] = cond
    Xp = X[:96, :96]
    for gi in d['cued']:
        g = d['groups'][gi]; M = set(g['members'])
        row = dict(design=nm, fam=fam, group=gi, sim_clean=None)
        e = sim.get((nm, gi))
        if e is None: continue
        row['sim_clean'] = bool(e['clean']); row['sim_full_cross'] = int(e['full_cross']); row['sim_cross_cells'] = int(e['cross_cells'])
        for thr in (16.5, 15.0):
            fired = L.cascade(Xp, g['cue'], thr=thr); fs = set(int(i) for i in np.where(fired)[0])
            comp = set(g['noncue']) <= fs; extra = fs - M
            row['model_clean_%s' % thr] = bool(comp and not extra); row['model_complete_%s' % thr] = bool(comp); row['model_extra_%s' % thr] = len(extra)
        # also: min margin of cue->noncue input
        rows.append(row)
json.dump(rows, open('validate_r3.json', 'w'), indent=0)
import collections
for thr in (16.5, 15.0):
    print('threshold', thr)
    for fam in ('F1', 'F2', 'F3', 'F8'):
        r = [x for x in rows if x['fam'] == fam]
        if not r: continue
        tp = sum(1 for x in r if x['sim_clean'] and x['model_clean_%s' % thr]); tn = sum(1 for x in r if (not x['sim_clean']) and (not x['model_clean_%s' % thr]))
        fp = sum(1 for x in r if (not x['sim_clean']) and x['model_clean_%s' % thr]); fn = sum(1 for x in r if x['sim_clean'] and not x['model_clean_%s' % thr])
        print(' ', fam, 'n', len(r), 'sim clean', sum(x['sim_clean'] for x in r), 'model clean', sum(x['model_clean_%s' % thr] for x in r), 'agree', tp + tn, 'model-clean/sim-notclean', fp, 'model-notclean/sim-clean', fn)
