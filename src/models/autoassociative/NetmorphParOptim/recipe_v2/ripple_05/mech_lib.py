"""Sensitivity study, D_synmax 0.5, not bio-realistic. Mechanism experiments E1-E4 (fix A/B) on fable-it1a-sim133 (seed 20240628)."""
import json, sys, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import numpy as np
import recipelib as L
D = '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05/'
def _guard():
    m = L.mem_available_gb(); assert m >= 100, 'available RAM %.1f GB < 100 GB: stopping' % m
    return m
L.guard_memory = _guard
S = L.SEEDS[20240628]; dump = L.Dump(S['dump'])
EXP = json.load(open(D + 'mech_experiments.json'))['experiments']
WREF = {(p[0], p[1]): (p[2], p[3]) for p in json.load(open(L.RECIPE + '/seed20240628/weights.json'))['pairs']}
CUE_OFFS = [0.0, 0.5, 1.0, 1.5]; T0 = 20.0

def groups_of(name):
    return [(sorted(g['members']), sorted(g['cue'])) for g in EXP[name]['groups']]

def build_set(name, kept=None):
    """returns groups, ref{(pre,post):g}, plist[(pre,post,cond,g)], info. kept: override keep-sets (E2b)."""
    e = EXP[name]; groups = groups_of(name)
    d = L.build_pairs(dump, groups)
    cond = {k: v[1] for k, v in d.items()}
    ref = {k: v[0] for k, v in d.items()}
    info = {}
    if kept is not None:   # rule: zero member(i)->k for k not in kept[i]
        n = 0
        for gi, (mem, cue) in enumerate(groups):
            for m in mem:
                for k in dump.its:
                    if (m, k) in cond and k not in kept[gi] and cond[(m, k)] != 0.0: cond[(m, k)] = 0.0; n += 1
        info['n_zeroed_by_rule'] = n
    elif e.get('pyr_int_scaling'):
        for ch in e['pyr_int_weight_changes_vs_weights_json']:
            k = (ch['pre'], ch['post']); cond[k] = min(ch['target_conductance_nS'], ref[k])  # JSON values are rounded; clip to weight <= 1 (max overshoot 3e-7 relative)
    plist = [(a, b, cond[(a, b)], ref[(a, b)]) for (a, b) in d]
    # consistency vs recipe weights.json (verified G0-G2 set): count differences
    diff_ii = [k for k in cond if k[1] in dump.its and k in WREF and abs(cond[k] - WREF[k][1]) > 1e-3]
    diff_new = [k for k in cond if k not in WREF]
    diff_pp = [k for k in cond if k[1] not in dump.its and k in WREF and abs(cond[k] - WREF[k][1]) > 1e-3]
    info.update(n_pairs=len(plist), n_pyr_int_diff_vs_weights_json=len(diff_ii), n_pyr_pyr_diff_vs_weights_json=len(diff_pp), n_pairs_not_in_weights_json=len(diff_new))
    return groups, ref, plist, info

def run_case(NES, client, name, groups, ref, plist, events, run_ms=150.0, dt=1.0, record=False, nes_name=''):
    print('mem GB %.1f' % L.guard_memory(), name, flush=True)
    sim, load = L.fresh_copy(NES, client, S['model'], 'mech05-' + nes_name + name, ref); assert load['loaded_ok'], load
    rec = None; rep = None
    try:
        rep = L.apply_pairs(sim, plist); assert rep['weight_min'] >= 0 and rep['weight_max'] <= 1 + 1e-9, rep
        sim.SetSTDP(_DoSTDP=False)
        cues = []
        for gi, on in events:
            for c, o in zip(groups[gi][1], CUE_OFFS): cues.append((float(T0 + on + o), int(c)))
        r = sim.SetSpecificAPTimes(cues); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=float(T0 + run_ms), Dt_ms=dt, timeout_s=900.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
        if record: rec = sim.GetRecording()['Recording']
    finally:
        try: print('deleted', sim.ID, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sim.ID, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    return dict(cues=[(t - T0, c) for t, c in cues], spikes=spikes, load=load, readback=dict(n_pairs=rep['n_pairs'], n_mismatch=rep['n_readback_mismatch'], mismatches=rep['mismatches'], wmin=rep['weight_min'], wmax=rep['weight_max'], nmda_nonzero_after=rep['nmda_nonzero_after'])), rec

def analyse(events, spikes, groups, run_ms=150.0):
    pyr = range(67); its = range(67, 94)
    first = min(on for _, on in events); evs = sorted(events, key=lambda e: e[1])
    allmem = set().union(*[set(groups[gi][0]) for gi, _ in events])
    out = dict(memories=[]); ct = []
    for k, (gi, on) in enumerate(evs):
        mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]
        wend = evs[k + 1][1] if k + 1 < len(evs) else run_ms
        lat = {}
        for m in nc:
            xs = [x for x in spikes.get(m, []) if on <= x < on + 10.0]
            lat[m] = (xs[0] - on) if xs else None
        comp = all(v is not None for v in lat.values())
        # cross-talk: non-cue member spike before its own cue onset
        for m in nc:
            for x in spikes.get(m, []):
                if x < on: ct.append((gi, m, x))
        memsp = [x for m in mem for x in spikes.get(m, []) if x >= on]
        pyr_win = [x for i in pyr for x in spikes.get(i, []) if on <= x < wend]
        nint = {i: len([x for x in spikes.get(i, []) if on <= x < wend]) for i in its}
        out['memories'].append(dict(group=gi, cue_onset_ms=on, complete=comp, n_noncue_fired_10ms=sum(v is not None for v in lat.values()),
            noncue_latency_ms={str(m): v for m, v in lat.items()},
            latency_last_noncue_ms=(max(lat.values()) if comp else None),
            last_member_spike_after_cue_ms=(max(memsp) - on if memsp else None),
            last_pyr_spike_in_window_after_cue_ms=(max(pyr_win) - on if pyr_win else None),
            member_spikes_total=len(memsp), int_spikes_in_window=sum(nint.values()), ints_fired_in_window=sum(1 for v in nint.values() if v),
            int_spikes_by_id={str(i): v for i, v in nint.items() if v}))
    out['crosstalk_events'] = ct
    outside = [(i, x) for i in pyr if i not in allmem for x in spikes.get(i, [])]
    out['spurious_nonmember_pyr_spikes'] = len(outside); out['spurious_nonmember_pyr_cells'] = sorted({i for i, _ in outside})
    allp = [x for i in pyr for x in spikes.get(i, [])]; allt = [x for i in range(94) for x in spikes.get(i, [])]
    out['last_pyr_spike_ms'] = max(allp) if allp else None; out['last_any_spike_ms'] = max(allt) if allt else None
    out['activity_end_after_first_cue_ms'] = (out['last_any_spike_ms'] - first) if allt else None
    out['activity_ends_within_100ms'] = bool(allt and out['last_any_spike_ms'] <= first + 100.0)
    out['active_in_last_10ms_of_run'] = bool(allt and out['last_any_spike_ms'] >= run_ms - 10.0)
    out['burst_not_terminated'] = bool(out['active_in_last_10ms_of_run'] or any((m['last_member_spike_after_cue_ms'] or 0) > 40 for m in out['memories']))
    out['burst_over_40ms_groups'] = [m['group'] for m in out['memories'] if (m['last_member_spike_after_cue_ms'] or 0) > 40]
    out['total_interneuron_spikes'] = sum(len(spikes.get(i, [])) for i in its); out['total_pyr_spikes'] = len(allp)
    out['all_complete'] = all(m['complete'] for m in out['memories'])
    out['min_int_spikes_per_recall'] = min(m['int_spikes_in_window'] for m in out['memories'])
    out['robust_ok_this_run'] = bool(out['all_complete'] and not ct and out['spurious_nonmember_pyr_spikes'] == 0 and out['activity_ends_within_100ms'] and out['min_int_spikes_per_recall'] >= 1)
    return out

def run_experiment(name, outfile, kept=None, tag=''):
    NES, client = L.connect()
    groups, ref, plist, info = build_set(name, kept)
    print(name, info, flush=True)
    K = len(groups); e = EXP[name]
    cases = [('single_G%d' % g, [(g, 0.0)], 1.0) for g in range(K)]
    for r in e['runs']:
        ev = [(g, i * r['spacing_ms']) for i, g in enumerate(r['order'])]
        cases.append((r['name'], ev, 1.0)); 
    for r in e['runs']:
        ev = [(g, i * r['spacing_ms']) for i, g in enumerate(r['order'])]
        cases.append((r['name'] + '_dt0.1', ev, 0.1))
    out = dict(label='sensitivity study, D_synmax 0.5, not bio-realistic', experiment=name + tag, groups=[dict(members=m, cue=c) for m, c in groups], set_info=info, runs={})
    first = True
    for cname, ev, dt in cases:
        if not first: time.sleep(30)
        first = False
        r, _ = run_case(NES, client, cname, groups, ref, plist, ev, dt=dt, nes_name=name + tag + '-')
        a = analyse(ev, r['spikes'], groups)
        out['runs'][cname] = dict(events=ev, dt_ms=dt, cues=r['cues'], spikes={str(k): v for k, v in r['spikes'].items() if v}, analysis=a, readback=r['readback'], load={k: v for k, v in r['load'].items() if k != 'modelload_response'})
        print(cname, 'dt', dt, [(m['group'], m['n_noncue_fired_10ms'], m['latency_last_noncue_ms'], m['int_spikes_in_window'], m['last_member_spike_after_cue_ms']) for m in a['memories']], 'robust_ok', a['robust_ok_this_run'], 'end', a['last_any_spike_ms'], 'mismatch', r['readback']['n_mismatch'], flush=True)
        json.dump(out, open(D + outfile, 'w'))
    return out
