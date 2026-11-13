"""Generic R3 runner. usage: rrun.py NAME MODEL DUMP PAIRSFILE SG(0|1) KIND
KIND: single | rip:order:spacing:dt[:cue3grp][:rec]   -> raw/raw_NAME.json   (apply-then-run in one session, sim deleted in finally)
Same protocol as ripple_S1_R3/r3lib.py (single = 4-cell cue + two 3-cell cues per memory, 500 ms apart; ripple cue offsets 0/0.5/1/1.5 ms)."""
import sys, json, os
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import numpy as np, recipelib as L
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/robustness_S1/'
name, MODEL, DUMP, pfile, sg, kind = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] == '1', sys.argv[6]
dump = L.Dump(DUMP); NP = len(dump.pyr); N = dump.N; CUE_OFFS = [0.0, 0.5, 1.0, 1.5]; T0 = 20.0

def fresh_copy(NES, client, nm, ref):
    c = NES.Simulation.Configuration(); c.Name = nm; c.Seed = 0
    sim = client.CreateSimulation(c); assert sim.ID >= 0
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(MODEL)
    n = len(sim.GetSomaPositions().get('SomaCenters', []))
    conn = sim.GetConnectome(Pause_s=0.1); ampa = {}; w = set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            w.add(round(float(conn['ConnectionWeights'][pre][i]), 3))
            if int(conn['ConnectionTypes'][pre][i]) == 1: ampa[(pre, int(post))] = float(conn['ConnectionGPeakSum'][pre][i])
    miss = [k for k in ref if k not in ampa]; gbad = [k for k in ref if k in ampa and abs(ampa[k] - ref[k]) > 1e-3 * max(1.0, ref[k])]
    ok = (n == N and not miss and not gbad and w == {0.2})
    return sim, dict(sim_id=sim.ID, n_neurons=n, weights_on_load=sorted(w), pairs_missing=len(miss), g_mismatch=len(gbad), loaded_ok=bool(ok))

d = json.load(open(pfile)); groups = [(sorted(g['members']), sorted(g['cue'])) for g in d['groups']]
plist = [(int(a), int(b), float(c), float(g)) for a, b, c, g, r in d['pairs']]; ref = {(a, b): g for a, b, c, g in plist}

def run_pairs(cues, run_ms, dt):
    assert L.mem_available_gb() >= 100
    NES, client = L.connect()
    sim, load = fresh_copy(NES, client, 'ROB-' + name, ref); sid = sim.ID
    print('sim', sid, load, flush=True); rep = None
    try:
        assert load['loaded_ok'], load
        rep = L.apply_pairs(sim, plist); assert rep['n_readback_mismatch'] == 0, rep
        if sg:
            conn = sim.GetConnectome(Pause_s=0.1); gp = []
            for pre in dump.its:
                for post, t in zip(conn['ConnectionTargets'][pre], conn['ConnectionTypes'][pre]):
                    if int(t) == 2: gp.append((pre, int(post)))
            for a, b in gp: sim.SetPrePostStrength(a, b, 0.0)
            conn = sim.GetConnectome(Pause_s=0.1)
            gw = [float(w) for pre in dump.its for w, t in zip(conn['ConnectionWeights'][pre], conn['ConnectionTypes'][pre]) if int(t) == 2]
            rep['gaba_pairs_zeroed'] = len(gp); rep['gaba_nonzero_after'] = sum(1 for w in gw if w != 0); print('SG gaba', len(gp), rep['gaba_nonzero_after'], flush=True)
        sim.SetSTDP(_DoSTDP=False)
        r = sim.SetSpecificAPTimes([(float(T0 + t), int(c)) for t, c in cues]); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=float(T0 + run_ms), Dt_ms=dt, timeout_s=3000.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    rb = dict(sim_id=sid, n_pairs=rep['n_pairs'], n_mismatch=rep['n_readback_mismatch'], wmin=rep['weight_min'], wmax=rep['weight_max'],
              nmda_nonzero_after=rep['nmda_nonzero_after'], gaba_nonzero_after=rep.get('gaba_nonzero_after'), gaba_pairs_zeroed=rep.get('gaba_pairs_zeroed'))
    return spikes, rb, load

def analyse_ripple(events, spikes, run_ms=150.0):
    pyr = range(NP); its = range(NP, N); evs = sorted(events, key=lambda e: e[1]); first = evs[0][1]
    allmem = set().union(*[set(groups[gi][0]) for gi, _ in events]); out = dict(memories=[]); ct = []
    for k, (gi, on) in enumerate(evs):
        mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]; wend = evs[k + 1][1] if k + 1 < len(evs) else run_ms; lat = {}
        for m in nc:
            xs = [x for x in spikes.get(m, []) if on <= x < on + 10.0]; lat[m] = (xs[0] - on) if xs else None
        comp = all(v is not None for v in lat.values())
        for m in nc:
            for x in spikes.get(m, []):
                if x < on: ct.append((gi, m, x))
        memsp = [x for m in mem for x in spikes.get(m, []) if x >= on]
        nint = {i: len([x for x in spikes.get(i, []) if on <= x < wend]) for i in its}
        out['memories'].append(dict(group=gi, cue_onset_ms=on, complete=comp, n_noncue_fired_10ms=sum(v is not None for v in lat.values()),
            latency_last_noncue_ms=(max(lat.values()) if comp else None), last_member_spike_after_cue_ms=(max(memsp) - on if memsp else None),
            member_spikes_total=len(memsp), int_spikes_in_window=sum(nint.values()), ints_fired=[i for i, v in nint.items() if v]))
    out['crosstalk_events'] = ct
    outside = [(i, x) for i in pyr if i not in allmem for x in spikes.get(i, [])]
    out['spurious_nonmember_pyr_spikes'] = len(outside); out['spurious_nonmember_pyr_cells'] = sorted({i for i, _ in outside})
    allp = [x for i in pyr for x in spikes.get(i, [])]; allt = [x for i in range(N) for x in spikes.get(i, [])]
    out['last_pyr_spike_ms'] = max(allp) if allp else None; out['last_any_spike_ms'] = max(allt) if allt else None
    out['activity_end_after_first_cue_ms'] = (out['last_any_spike_ms'] - first) if allt else None
    out['activity_ends_within_100ms'] = bool(allt and out['last_any_spike_ms'] <= first + 100.0)
    out['active_in_last_10ms_of_run'] = bool(allt and out['last_any_spike_ms'] >= run_ms - 10.0)
    out['burst_over_40ms_groups'] = [m['group'] for m in out['memories'] if (m['last_member_spike_after_cue_ms'] or 0) > 40]
    out['total_pyr_spikes'] = len(allp); out['total_interneuron_spikes'] = sum(len(spikes.get(i, [])) for i in its)
    out['ints_that_fired'] = sorted(i for i in its if spikes.get(i)); out['all_complete'] = all(m['complete'] for m in out['memories'])
    out['terminates'] = bool(not out['active_in_last_10ms_of_run'] and not out['burst_over_40ms_groups'])
    out['ripple_success'] = bool(out['all_complete'] and not ct and out['spurious_nonmember_pyr_spikes'] == 0 and out['activity_ends_within_100ms'] and out['terminates'])
    return out

if kind == 'single':
    evs = []; t = 0.0
    for gi, (mem, cue) in enumerate(groups):
        evs.append(dict(label='G%d full 4-cell' % gi, group=gi, cue=list(cue), t=t, expect=True)); t += 500
        evs.append(dict(label='G%d 3-cell a' % gi, group=gi, cue=list(cue[:3]), t=t, expect=False)); t += 500
        evs.append(dict(label='G%d 3-cell b' % gi, group=gi, cue=list(cue[1:]), t=t, expect=False)); t += 500
    cues = [(e['t'] + o, c) for e in evs for c, o in zip(e['cue'], CUE_OFFS)]
    spikes, rb, load = run_pairs(cues, t + 100, 1.0)
    res = []; allmem = {m for mm, _ in groups for m in mm}
    for e in evs:
        gi = e['group']; mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]; t0 = e['t']
        w = lambda i: [x - t0 for x in spikes.get(i, []) if t0 <= x < t0 + 450]
        fired = [m for m in nc if w(m)]; otherg = [m for g2, (mm, _) in enumerate(groups) if g2 != gi for m in mm if w(m)]
        op = [i for i in range(NP) if i not in allmem and w(i)]
        lat = min((x for m in fired for x in w(m)), default=None); memsp = [x for m in mem for x in w(m)]
        res.append(dict(label=e['label'], expect_complete=e['expect'], noncue_fired=len(fired), noncue_total=len(nc), latency_ms=lat, member_spikes=len(memsp),
            burst_end_ms=max(memsp, default=None), other_group_members_fired=len(otherg), other_pyr_fired=len(op),
            interneuron_spikes=sum(len(w(i)) for i in range(NP, N)), ints_fired=[i for i in range(NP, N) if w(i)],
            clean=bool((len(fired) == len(nc) if e['expect'] else len(fired) == 0) and not otherg and not op)))
        r = res[-1]; print(name, r['label'], r['noncue_fired'], r['latency_ms'], r['member_spikes'], r['burst_end_ms'], r['interneuron_spikes'], r['clean'], flush=True)
    entry = dict(kind='single', events=res, readback=rb, load=load, pyr_spikes_total=sum(len(v) for k, v in spikes.items() if k < NP))
else:
    p = kind.split(':'); q = [x for x in p if x != 'rec']
    order = [int(c) for c in q[1]]; sp_ = float(q[2]); dt = float(q[3]); cue3 = int(q[4]) if len(q) > 4 else None
    ev = [(g, i * sp_) for i, g in enumerate(order)]; cues = []
    for gi, on in ev:
        cl = groups[gi][1]; offs = CUE_OFFS
        if cue3 == gi: cl = cl[:3]; offs = offs[:3]
        cues += [(on + o, c) for c, o in zip(cl, offs)]
    spikes, rb, load = run_pairs(cues, 150.0, dt)
    a = analyse_ripple(ev, spikes); a['cue3_group'] = cue3
    entry = dict(kind='ripple', events=ev, dt_ms=dt, analysis=a, readback=rb, load=load, pyr_spikes_in_engram=sum(len(spikes.get(m, [])) for mm, _ in groups for m in mm))
    print(name, [(m['group'], m['n_noncue_fired_10ms'], m['latency_last_noncue_ms'], m['last_member_spike_after_cue_ms'], m['member_spikes_total'], m['int_spikes_in_window']) for m in a['memories']],
          'spur', a['spurious_nonmember_pyr_spikes'], 'ct', len(a['crosstalk_events']), 'end', a['last_any_spike_ms'], 'succ', a['ripple_success'], flush=True)
entry.update(name=name, pairs=os.path.basename(pfile), sg=sg, kind_arg=kind)
json.dump(entry, open(HERE + 'raw/raw_%s.json' % name, 'w'), separators=(',', ':'))
