"""Sensitivity study, D_synmax 0.5, not bio-realistic. Ripple-style multi-memory recall on fable-it1a-sim133 (seed 20240628)."""
import json, sys, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import numpy as np
import recipelib as L
def _guard():
    m = L.mem_available_gb(); assert m >= 100, 'available RAM %.1f GB < 100 GB: stopping' % m
    return m
L.guard_memory = _guard
S = L.SEEDS[20240628]; dump = L.Dump(S['dump'])
SD = json.load(open(L.RECIPE + '/sweep_designs.json'))['K_groups']
ALLG = [(sorted(g['members']), sorted(g['cue'])) for g in SD]
K = 4; GROUPS = ALLG[:K]
CUE_OFFS = [0.0, 0.5, 1.0, 1.5]   # 4 cue cells spike within 1.5 ms
T0 = 20.0
def pairs_for(groups, program=True):
    d = L.build_pairs(dump, groups)
    ref = {k: v[0] for k, v in d.items()}
    plist = [(a, b, v[1], v[0]) for (a, b), v in d.items()]
    return ref, plist
REF, PAIRS = pairs_for(GROUPS)
def run_case(NES, client, name, events, program=True, run_ms=150.0, dt=1.0, record=False, tag=''):
    """events: list of (group_index, onset_ms). returns spikes (relative to first cue), recording."""
    print('mem GB %.1f' % L.guard_memory(), name, flush=True)
    sim, load = L.fresh_copy(NES, client, S['model'], 'ripple05-' + name, REF); assert load['loaded_ok'], load
    rec = None
    try:
        if program:
            rep = L.apply_pairs(sim, PAIRS); assert rep['n_readback_mismatch'] == 0 and rep['weight_min'] >= 0 and rep['weight_max'] <= 1 + 1e-9, rep
        sim.SetSTDP(_DoSTDP=False)
        cues = []
        for gi, on in events:
            for c, o in zip(GROUPS[gi][1], CUE_OFFS): cues.append((float(T0 + on + o), int(c)))
        r = sim.SetSpecificAPTimes(cues); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=float(T0 + run_ms), Dt_ms=dt, timeout_s=600.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
        if record: rec = sim.GetRecording()['Recording']
    finally:
        try: print('deleted', sim.ID, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sim.ID, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    return dict(cues=[(t - T0, c) for t, c in cues], spikes=spikes, load=load), rec

def analyse(events, spikes, groups=GROUPS, end_win=150.0):
    """per-memory verdicts. events [(gi, onset)]."""
    ingrp = {m for mem, _ in groups for m in mem}
    cued_time = {gi: on for gi, on in events}
    out = dict(memories=[]); pyr = range(67); its = range(67, 94)
    first_cue = min(on for _, on in events)
    for gi, on in events:
        mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]
        # window: from this cue until next cue onset (or end)
        later = sorted(o for _, o in events if o > on)
        wend = later[0] if later else end_win
        lat = {}
        for m in nc:
            xs = [x for x in spikes.get(m, []) if on <= x < on + 10.0]
            lat[m] = xs[0] - on if xs else None
        # cross-talk: members of memory fire before own cue
        early = {m: [x for x in spikes.get(m, []) if x < on + CUE_OFFS[0] - 0.0 and x >= first_cue - 5.0] for m in mem if m not in cue}
        early = {m: v for m, v in early.items() if v}
        # spikes in own window after ripple completion (non-cue) beyond first 10 ms (repeat bursts)
        extra = sum(len([x for x in spikes.get(m, []) if on + 10.0 <= x < wend]) for m in mem)
        spk_in = {m: len([x for x in spikes.get(m, []) if on <= x < on + 10.0]) for m in mem}
        out['memories'].append(dict(group=gi, cue_onset_ms=on, complete=all(v is not None for v in lat.values()),
            n_noncue_fired_10ms=sum(v is not None for v in lat.values()), noncue_latency_ms={str(m): v for m, v in lat.items()},
            latency_last_noncue_ms=(max(v for v in lat.values() if v is not None) if all(v is not None for v in lat.values()) else None),
            member_spikes_in_first_10ms=sum(spk_in.values()), member_spikes_after_10ms_until_next_cue=extra,
            crosstalk_early_members=early))
    # cross-talk: member of not-yet-cued memory fires before its cue
    ct = []
    for gi, on in events:
        for m in groups[gi][0]:
            if m in groups[gi][1]: continue
            for x in spikes.get(m, []):
                if x < on: ct.append((gi, m, x))
    out['crosstalk_events'] = ct
    # spurious pyramidal spikes: pyramidal cell outside the memory currently being cued ... define: not a member of any cued memory OR member of memory outside its own 10ms window... keep simple & explicit
    memset = {gi: set(groups[gi][0]) for gi, _ in events}
    allmem = set().union(*memset.values())
    outside = [(i, x) for i in pyr if i not in allmem for x in spikes.get(i, [])]
    mem_off = []  # member spikes outside own memory's [on, on+10) window and not cue-forced
    for gi, on in events:
        for m in groups[gi][0]:
            for x in spikes.get(m, []):
                if not (on <= x < on + 10.0): mem_off.append((gi, m, x))
    out['spurious_nonmember_pyr_spikes'] = len(outside); out['spurious_nonmember_pyr_cells'] = sorted({i for i, _ in outside})
    out['member_spikes_outside_own_10ms_window'] = len(mem_off)
    allpyr_t = [x for i in pyr for x in spikes.get(i, [])]
    out['last_pyr_spike_ms'] = max(allpyr_t) if allpyr_t else None
    allt = [x for i in range(94) for x in spikes.get(i, [])]
    out['last_any_spike_ms'] = max(allt) if allt else None
    out['activity_ends_within_100ms'] = bool(out['last_any_spike_ms'] is not None and out['last_any_spike_ms'] <= first_cue + 100.0)
    # per-event (cue onset to next onset) interneuron spikes, burst
    bins = sorted(o for _, o in events) + [end_win + 1]
    iev = []
    for k, (gi, on) in enumerate(sorted(events, key=lambda e: e[1])):
        wend = bins[k + 1]
        n = {i: len([x for x in spikes.get(i, []) if on <= x < wend]) for i in its}
        iev.append(dict(group=gi, window_ms=[on, wend], int_spikes=sum(n.values()), ints_fired=sum(1 for v in n.values() if v)))
    out['interneuron_per_event'] = iev
    out['total_interneuron_spikes'] = sum(len(spikes.get(i, [])) for i in its)
    out['total_pyr_spikes'] = len(allpyr_t)
    out['pyr_spikes_after_last_event_window_end10'] = len([x for x in allpyr_t if x >= max(o for _, o in events) + 20.0])
    out['all_complete'] = all(m['complete'] for m in out['memories'])
    out['ripple_success'] = bool(out['all_complete'] and not ct and out['activity_ends_within_100ms'])
    return out
