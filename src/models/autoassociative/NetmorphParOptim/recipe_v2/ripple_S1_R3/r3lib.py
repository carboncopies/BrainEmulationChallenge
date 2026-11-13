"""R3 runner on S1: programs pairs_*.json from fable_design_S1 (apply then run in same session), GABA zeroing for SG. Reuses ripple_S1/slib."""
import sys, json, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1')
from slib import *
FD = '/home/johnjose/cos/netmorph_work/recipe_v2/fable_design_S1/'
OUT = '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_S1_R3/'
def load_pairs(name):
    d = json.load(open(FD + 'pairs_%s.json' % name))
    groups = [(sorted(g['members']), sorted(g['cue'])) for g in d['groups']]
    return groups, [(int(a), int(b), float(c), float(g)) for a, b, c, g, r in d['pairs']], d['pairs']

def run_pairs(NES, client, tag, pname, sg, cues, run_ms, dt, record=False):
    assert mem_available_gb() >= 100
    groups, plist, raw = load_pairs(pname)
    ref = {(a, b): g for a, b, c, g in plist}
    sim, load = fresh_copy(NES, client, 'R3-' + tag, ref)
    print('sim', sim.ID, load, flush=True)
    rec = None; rep = None; sid = sim.ID
    try:
        assert load['loaded_ok'], load
        rep = L.apply_pairs(sim, plist)
        assert rep['n_readback_mismatch'] == 0, rep
        if sg:
            conn = sim.GetConnectome(Pause_s=0.1); gp = []
            for pre in dump.its:
                for post, t in zip(conn['ConnectionTargets'][pre], conn['ConnectionTypes'][pre]):
                    if int(t) == 2: gp.append((pre, int(post)))
            fails = 0
            for a, b in gp:
                r = sim.SetPrePostStrength(a, b, 0.0)
            conn = sim.GetConnectome(Pause_s=0.1)
            gw = [float(w) for pre in dump.its for w, t in zip(conn['ConnectionWeights'][pre], conn['ConnectionTypes'][pre]) if int(t) == 2]
            rep['gaba_pairs_zeroed'] = len(gp); rep['gaba_nonzero_after'] = sum(1 for w in gw if w != 0); print('SG gaba', len(gp), rep['gaba_nonzero_after'], flush=True)
        sim.SetSTDP(_DoSTDP=False)
        r = sim.SetSpecificAPTimes([(float(T0 + t), int(c)) for t, c in cues]); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=float(T0 + run_ms), Dt_ms=dt, timeout_s=3000.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
        if record: rec = sim.GetRecording()['Recording']
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    rb = dict(sim_id=sid, n_pairs=rep['n_pairs'], n_mismatch=rep['n_readback_mismatch'], wmin=rep['weight_min'], wmax=rep['weight_max'],
              nmda_nonzero_after=rep['nmda_nonzero_after'], gaba_nonzero_after=rep.get('gaba_nonzero_after'), gaba_pairs_zeroed=rep.get('gaba_pairs_zeroed'))
    return groups, plist, spikes, rec, rb, load

def single_run(NES, client, tag, pname, sg):
    groups, _, _ = load_pairs(pname)
    evs = []; t = 0.0
    for gi, (mem, cue) in enumerate(groups):
        evs.append(dict(label='G%d full 4-cell' % gi, group=gi, cue=list(cue), t=t, expect=True)); t += 500
        evs.append(dict(label='G%d 3-cell a' % gi, group=gi, cue=list(cue[:3]), t=t, expect=False)); t += 500
        evs.append(dict(label='G%d 3-cell b' % gi, group=gi, cue=list(cue[1:]), t=t, expect=False)); t += 500
    cues = [(e['t'] + o, c) for e in evs for c, o in zip(e['cue'], CUE_OFFS)]
    groups, plist, spikes, rec, rb, load = run_pairs(NES, client, tag, pname, sg, cues, t + 100, 1.0)
    res = []; allmem = {m for mm, _ in groups for m in mm}
    for e in evs:
        gi = e['group']; mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]; t0 = e['t']
        w = lambda i: [x - t0 for x in spikes.get(i, []) if t0 <= x < t0 + 450]
        fired = [m for m in nc if w(m)]
        otherg = [m for g2, (mm, _) in enumerate(groups) if g2 != gi for m in mm if w(m)]
        op = [i for i in range(NP) if i not in allmem and w(i)]
        lat = min((x for m in fired for x in w(m)), default=None)
        memsp = [x for m in mem for x in w(m)]
        res.append(dict(label=e['label'], cue=e['cue'], expect_complete=e['expect'], noncue_fired=len(fired), noncue_total=len(nc), latency_ms=lat,
            member_spikes=len(memsp), burst_end_ms=max(memsp, default=None), other_group_members_fired=len(otherg), other_pyr_fired=len(op),
            interneuron_spikes=sum(len(w(i)) for i in range(NP, N)), ints_fired=[i for i in range(NP, N) if w(i)],
            last_pyr_spike_ms=max((x for i in range(NP) for x in w(i)), default=None),
            clean=bool((len(fired) == len(nc) if e['expect'] else len(fired) == 0) and not otherg and not op)))
        r = res[-1]; print(tag, r['label'], r['noncue_fired'], r['latency_ms'], r['member_spikes'], r['burst_end_ms'], r['interneuron_spikes'], r['clean'], flush=True)
    return dict(kind='single', events=res, readback=rb, load=load, spikes={str(k): v for k, v in spikes.items() if v})

def ripple_run(NES, client, tag, pname, sg, order, sp, dt, cue3=None, record=False):
    """cue3: group index whose cue is cut to first 3 cells (selectivity test)."""
    groups, _, _ = load_pairs(pname)
    ev = [(g, i * sp) for i, g in enumerate(order)]
    cues = []
    for gi, on in ev:
        cl = groups[gi][1]; offs = CUE_OFFS
        if cue3 == gi: cl = cl[:3]; offs = offs[:3]
        cues += [(on + o, c) for c, o in zip(cl, offs)]
    groups, plist, spikes, rec, rb, load = run_pairs(NES, client, tag, pname, sg, cues, 150.0, dt, record)
    a = analyse_ripple(ev, spikes, groups)
    a['cue3_group'] = cue3
    entry = dict(kind='ripple', events=ev, dt_ms=dt, analysis=a, readback=rb, load=load, spikes={str(k): v for k, v in spikes.items() if v})
    if record:
        t = np.array(rec['t_ms'], float) - T0; lo, hi = (-5, 110); msk = (t >= lo) & (t <= hi)
        allm = [m for mm, _ in groups for m in mm]
        cond = {(x, y): c for x, y, c, g in plist}
        dr = sorted(dump.its, key=lambda i: -sum(cond.get((m, i), 0.0) for m in allm))[:8]
        ints = sorted(set(dr) | set(a['ints_that_fired'])); tr = {}
        for nid in allm + ints:
            e = rec['neurons'][str(nid)]; vm = np.array(e['Vm_mV'] if isinstance(e, dict) else e, float)
            tr[str(nid)] = [round(float(x), 1) for x in vm[msk]]
        entry['vm'] = dict(window_ms=[lo, hi], times_ms=[round(float(x), 2) for x in t[msk]], vm_mV=tr, pyramidal_memory_cells=allm, interneurons=ints, top_driven_ints=dr)
    print(tag, [(m['group'], m['n_noncue_fired_10ms'], m['latency_last_noncue_ms'], m['last_member_spike_after_cue_ms'], m['member_spikes_total'], m['int_spikes_in_window']) for m in a['memories']],
          'spur', a['spurious_nonmember_pyr_spikes'], 'ct', len(a['crosstalk_events']), 'end', a['last_any_spike_ms'], 'succ', a['ripple_success'], flush=True)
    return entry
