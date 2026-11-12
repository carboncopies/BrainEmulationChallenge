#!/usr/bin/env python3
"""Task C: scalability on the seed-20240628 network. One fresh copy per condition (30 s pause between), results in sweeps_results.json.
usage: run_sweeps.py [cond ...]   conditions: K1 K2 K3 K4.. S6 S8 S10"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipelib as L
seed = 20240628; S = L.SEEDS[seed]; dump = L.Dump(S['dump']); des = json.load(open(L.RECIPE + '/sweep_designs.json'))
resf = L.RECIPE + '/sweeps_results.json'
res = json.load(open(resf)) if os.path.exists(resf) else {}
ref = {(a, b): float(dump.G[a, b]) for a in range(dump.N) for b in range(dump.N) if dump.G[a, b] > 0}
def conds():
    Kg = [(g['members'], g['cue']) for g in des['K_groups']]
    c = {}
    for K in range(1, len(Kg) + 1): c['K%d' % K] = Kg[:K]
    for size in (6, 8, 10): c['S%d' % size] = [(g['members'], g['cue']) for g in des['size'][str(size)]]
    return c
C = conds(); todo = sys.argv[1:] or list(C)
NES, client = L.connect(); first = True
for name in todo:
    groups = C[name]
    if not first: time.sleep(30)
    first = False
    print('available memory GB %.1f' % L.guard_memory(), flush=True)
    sim, load = L.fresh_copy(NES, client, S['model'], 'recipe-sweep-%s' % name, ref)
    assert load['loaded_ok'], load
    pairs = L.build_pairs(dump, groups, bg=0.0, inh=True)
    rep = L.apply_pairs(sim, [(a, b, v, g) for (a, b), (g, v, r) in pairs.items()])
    ev = L.standard_events(groups, extra_cross=(len(groups) >= 2))
    if len(groups[0][1]) != 4:     # size sweep: full cue, (n-1)-cell cues (two subsets), 2-cell cue
        ev = []
        for gi, (mem, cue) in enumerate(groups):
            n = len(cue)
            ev += [dict(label='G%d full %d-cell cue' % (gi, n), group=gi, cue=list(cue), expect_complete=True),
                   dict(label='G%d %d-cell cue (a)' % (gi, n - 1), group=gi, cue=list(cue[:n - 1]), expect_complete=False),
                   dict(label='G%d %d-cell cue (b)' % (gi, n - 1), group=gi, cue=list(cue[1:]), expect_complete=False),
                   dict(label='G%d 2-cell cue' % gi, group=gi, cue=list(cue[:2]), expect_complete=False)]
    times, sp = L.run_events(sim, ev, spacing=2000.0)
    r, outside = L.analyse(ev, times, sp, groups)
    for e, x in zip(ev, r): x['expect_complete'] = e['expect_complete']; x['clean'] = L.verdict(x, e['expect_complete'])
    full = [x for x in r if x['expect_complete']]; sub = [x for x in r if not x['expect_complete'] and x['group'] is not None]
    summ = dict(condition=name, K=len(groups), group_size=len(groups[0][0]), cue_size=len(groups[0][1]), sim_id=sim.ID, apply_mismatches=rep['n_readback_mismatch'],
                completion=sum(1 for x in full if x['noncue_fired'] == x['noncue_total']), n_full=len(full),
                subthreshold_false_completions=sum(1 for x in sub if x['noncue_fired'] > 0), n_sub=len(sub),
                n_leak_events=sum(1 for x in r if x['other_group_members_fired'] or x['other_pyr_fired']), n_clean=sum(x['clean'] for x in r), n_events=len(r),
                min_pair_nS=[g['score'] for g in (des['size'][name[1:]] if name.startswith('S') else des['K_extra_scores'])] if False else None,
                groups=[dict(members=m, cue=c) for m, c in groups])
    summ['all_hold'] = bool(summ['completion'] == summ['n_full'] and summ['subthreshold_false_completions'] == 0 and summ['n_leak_events'] == 0)
    print(name, {k: v for k, v in summ.items() if k != 'groups'}, flush=True)
    for x in r: print('   ', x['label'], 'fired %s/%s' % (x['noncue_fired'], x.get('noncue_total')), 'otherGrp', x['other_group_members_fired'], 'otherPyr', x['other_pyr_fired'], 'int', x['interneurons_fired'], 'CLEAN' if x['clean'] else 'NOT-CLEAN', flush=True)
    res[name] = dict(summary=summ, events=r, spikes_outside_windows=outside)
    json.dump(res, open(resf, 'w'), indent=1)
