"""apply / recall entry points shared by seed*/apply.py and seed*/recall_test.py"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recipelib as L

def seed_of(d): return int(os.path.basename(d.rstrip('/')).replace('seed', ''))

def load_recipe(d):
    wj = json.load(open(os.path.join(d, 'weights.json'))); ej = json.load(open(os.path.join(d, 'engrams.json')))
    groups = [(g['members'], g['cue']) for g in ej['groups']]
    return wj, ej, groups

def apply_main(d, pause=30):
    seed = seed_of(d); S = L.SEEDS[seed]; wj, ej, groups = load_recipe(d)
    print('available memory GB %.1f' % L.guard_memory())
    NES, client = L.connect()
    ref = {(p[0], p[1]): p[2] for p in wj['pairs']}
    sim, load = L.fresh_copy(NES, client, S['model'], 'recipe-seed%d-copy' % seed, ref)
    print('fresh copy:', load)
    assert load['loaded_ok'], 'loaded model does not match recipe reference (g_peak_sum / weights 0.2)'
    pairs = [(p[0], p[1], p[3], p[2]) for p in wj['pairs']]
    rep = L.apply_pairs(sim, pairs)
    print('apply:', {k: v for k, v in rep.items() if k != 'mismatches'}, rep['mismatches'][:5])
    out = dict(seed=seed, load=load, apply=rep, sim_id=sim.ID, ok=bool(rep['n_readback_mismatch'] == 0))
    json.dump(out, open(os.path.join(d, 'apply_report.json'), 'w'), indent=1)
    print('APPLY', 'OK: all %d pairs read back correctly' % rep['n_pairs'] if out['ok'] else 'FAILED: %d mismatches' % rep['n_readback_mismatch'])
    return out

def recall_main(d, control=True, pause=30):
    seed = seed_of(d); S = L.SEEDS[seed]; wj, ej, groups = load_recipe(d)
    ap = json.load(open(os.path.join(d, 'apply_report.json'))); assert ap['ok'], 'run apply.py first (and it must succeed)'
    print('available memory GB %.1f' % L.guard_memory())
    NES, client = L.connect()
    c = NES.Simulation.Configuration(); c.Name = 'attach'; c.Seed = 0
    sim = client.CreateSimulation(c, _Create=False); sim.ID = ap['sim_id']
    assert sim.ID >= 0
    sim.SetSTDP(_DoSTDP=False)
    events = L.standard_events(groups)
    t0 = time.time(); times, sp = L.run_events(sim, events, spacing=2000.0)
    res, outside = L.analyse(events, times, sp, groups)
    for e, r in zip(events, res): r['expect_complete'] = e['expect_complete']; r['clean'] = L.verdict(r, e['expect_complete'])
    summ = dict(n_events=len(res), n_clean=sum(r['clean'] for r in res),
                full_cue_complete=sum(1 for r in res if r['expect_complete'] and r['noncue_fired'] == r['noncue_total']),
                n_full_cues=sum(1 for r in res if r['expect_complete']),
                subthreshold_cues_that_completed=sum(1 for r in res if not r['expect_complete'] and r['noncue_fired'] > 0),
                n_subthreshold=sum(1 for r in res if not r['expect_complete'] and r['group'] is not None),
                cross_pattern_events_with_activity=sum(1 for r in res if r['other_group_members_fired'] or r['other_pyr_fired']),
                spikes_outside_event_windows=outside, wall_s=round(time.time() - t0, 1))
    print('RECALL', summ)
    for r in res: print(' ', r['label'], 'cue', r['cue'], 'fired %s/%s' % (r['noncue_fired'], r.get('noncue_total')), 'lat', r.get('latency_ms'), 'otherGrp', r['other_group_members_fired'], 'otherPyr', r['other_pyr_fired'], 'int', r['interneurons_fired'], 'CLEAN' if r['clean'] else 'NOT-CLEAN')
    out = dict(seed=seed, sim_id=sim.ID, spacing_ms=2000, summary=summ, events=res)
    # ---- control: fresh copy, NO programming (as-grown weights 0.2 everywhere), same 4-cell cues
    if control:
        time.sleep(pause)
        print('available memory GB %.1f' % L.guard_memory())
        ref = {(p[0], p[1]): p[2] for p in wj['pairs']}
        csim, load = L.fresh_copy(NES, client, S['model'], 'recipe-seed%d-control' % seed, ref)
        assert load['loaded_ok']
        cev = [dict(label='CONTROL G%d full cue (no pruning/programming)' % k, group=k, cue=list(cue), expect_complete=True) for k, (mem, cue) in enumerate(groups)]
        ctimes, csp = L.run_events(csim, cev, spacing=3000.0)
        cres, couts = L.analyse(cev, ctimes, csp, groups)
        for e, r in zip(cev, cres): r['clean'] = L.verdict(r, True)
        out['control'] = dict(sim_id=csim.ID, load=load, events=cres, spikes_outside_windows=couts)
        for r in cres: print('  CONTROL', r['label'], 'fired %s/%s' % (r['noncue_fired'], r['noncue_total']), 'otherGrp', r['other_group_members_fired'], 'otherPyr', r['other_pyr_fired'], 'total_spikes', r['total_spikes'], 'last_pyr_ms', r['last_pyr_spike_ms'])
        out['control_raster'] = {str(i): L.raster(csp, t, pre=5, post=300) for i, t in enumerate(ctimes)}
    json.dump(out, open(os.path.join(d, 'recall_results.json'), 'w'), indent=1)
    # ---- demo data
    dump = L.Dump(S['dump']); pairs = {(p[0], p[1]): p for p in wj['pairs']}
    gm = []
    for k, (mem, cue) in enumerate(groups):
        nc = [m for m in mem if m not in cue]
        gm.append(dict(group=k, cue=cue, noncue=nc,
                       cue_to_noncue_conductance_nS={'rows_cue': cue, 'cols_noncue': nc, 'matrix': [[pairs[(a, b)][3] if (a, b) in pairs else 0.0 for b in nc] for a in cue]},
                       noncue_to_noncue_conductance_nS={'ids': nc, 'matrix': [[pairs[(a, b)][3] if (a, b) in pairs else 0.0 for b in nc] for a in nc]},
                       noncue_to_cue_conductance_nS={'rows_noncue': nc, 'cols_cue': cue, 'matrix': [[pairs[(a, b)][3] if (a, b) in pairs else 0.0 for b in cue] for a in nc]},
                       cue_total_delivered_to_noncue_nS={str(b): round(sum(pairs[(a, b)][3] for a in cue if (a, b) in pairs), 3) for b in nc}))
    demo = dict(seed=seed, n_neurons=dump.N, neuron_type={str(n['id']): ('pyramidal' if n['soma_type'] == 1 else 'interneuron') for n in dump.neurons},
                soma_positions_um={str(n['id']): [n['x'], n['y'], n['z']] for n in dump.neurons},
                soma_radius_um={str(n['id']): n['soma_radius'] for n in dump.neurons},
                groups=[dict(group=k, members=m, cue=c) for k, (m, c) in enumerate(groups)], engram_weight_summary=gm,
                weight_counts={r: sum(1 for p in wj['pairs'] if p[5] == r) for r in sorted({p[5] for p in wj['pairs']})},
                notes='spike times in ms relative to the first cue spike (t=0); raster window -5..+150 ms; cue spikes are forced (SetSpecificAPTimes) and appear in the raster at their cue offsets',
                test_cases=[dict(label=r['label'], group=r['group'], cue_cells=r['cue'], cue_spike_times_ms=[o for o in (r['offsets'] or [0.0] * len(r['cue']))],
                                 expect_complete=r['expect_complete'], completed_noncue=r['noncue_fired'], noncue_total=r.get('noncue_total'),
                                 latency_ms=r.get('latency_ms'), clean=r['clean'], interneurons_fired=r['interneurons_fired'], interneuron_spikes=r['interneuron_spikes'],
                                 raster=L.raster(sp, t, pre=5, post=150),
                                 interneuron_raster=[x for x in L.raster(sp, t, pre=5, post=150) if x[0] >= 67]) for r, t in zip(res, times)])
    if control: demo['control_run_away'] = [dict(label=r['label'], cue_cells=r['cue'], raster=out['control_raster'][str(i)], total_spikes=r['total_spikes'], other_group_members_fired=r['other_group_members_fired'], other_pyr_fired=r['other_pyr_fired']) for i, r in enumerate(out['control']['events'])]
    json.dump(demo, open(os.path.join(d, 'demo_data.json'), 'w'))
    return out
