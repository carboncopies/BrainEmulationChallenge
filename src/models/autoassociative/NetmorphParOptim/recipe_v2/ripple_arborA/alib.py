"""Shared lib for arbor-A ripple work (bio-consistent v2-arbor-A: 96 pyr, 48 int)."""
import sys, json, itertools, random
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import numpy as np
import recipelib as L
OUT = '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_arborA/'
DUMP = '/home/johnjose/cos/netmorph_work/recipe_v2/grow_arbor_A/viz/sample_0000.json'
MODEL = 'v2-arbor-A0000'
dump = L.Dump(DUMP)
NP, NI, N = len(dump.pyr), len(dump.its), dump.N
G, GA = dump.G, dump.GA
DRIVE_THR = 13.84
tot_in = {i: float(G[dump.pyr, i].sum()) for i in dump.its}
DRIVABLE = [i for i in dump.its if tot_in[i] >= DRIVE_THR]
CUE_OFFS = [0.0, 0.5, 1.0, 1.5]; T0 = 20.0

def mem_available_gb():
    return L.mem_available_gb()

def drive(groups, dr=None):
    """d[gi][k] = min(sum cue->k,10)+sum noncue->k (standard rule), restricted to ints in dr (default drivable)."""
    dr = DRIVABLE if dr is None else dr
    out = []
    for mem, cue in groups:
        nc = [m for m in mem if m not in cue]; d = {}
        for k in dr:
            v = min(sum(G[c, k] for c in cue), 10.0) + sum(G[m, k] for m in nc)
            d[k] = float(v)
        out.append(d)
    return out

def nspk(d, cyc=2):
    return cyc if d >= 20 else ((cyc + 1) // 2 if d >= 15 else (1 if d >= 10 else 0))

def cross_matrix(groups, dr=None, cyc=2):
    dd = drive(groups, dr); K = len(groups)
    M = np.zeros((K, K)); 
    for i in range(K):
        for j in range(K):
            nc = [m for m in groups[j][0] if m not in groups[j][1]]
            M[i, j] = max(sum(nspk(dd[i][k], cyc) * GA[k, n] for k in dd[i]) for n in nc)
    return M, dd

def loop_gain_ok(groups):
    return True

def groups_from(path):
    d = json.load(open(path)); return [(sorted(g['members']), sorted(g['cue'])) for g in d['groups']]

def build(groups, variant):
    """variant: 'E1' standard rule; 'NI' all Pyr->Int zero (no inhibition dependence); 'E1d' standard but Pyr->Int onto non-drivable ints zeroed."""
    d = L.build_pairs(dump, groups, inh=(variant != 'NI'))
    cond = {k: v[1] for k, v in d.items()}; ref = {k: v[0] for k, v in d.items()}
    if variant == 'E1d':
        for (a, b) in list(cond):
            if b in dump.its and b not in DRIVABLE: cond[(a, b)] = 0.0
    plist = [(a, b, cond[(a, b)], ref[(a, b)]) for (a, b) in d]
    return ref, plist

def fresh_copy(NES, client, name, ref_pairs):
    c = NES.Simulation.Configuration(); c.Name = name; c.Seed = 0
    sim = client.CreateSimulation(c); assert sim.ID >= 0
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True)
    sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True)
    sim.SetSTDP(_DoSTDP=False)
    r = sim.ModelLoad(MODEL)
    n = len(sim.GetSomaPositions().get('SomaCenters', []))
    conn = sim.GetConnectome(Pause_s=0.1)
    ampa = {}; w = set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            w.add(round(float(conn['ConnectionWeights'][pre][i]), 3))
            if int(conn['ConnectionTypes'][pre][i]) == 1: ampa[(pre, int(post))] = float(conn['ConnectionGPeakSum'][pre][i])
    miss = [k for k in ref_pairs if k not in ampa]
    gbad = [k for k in ref_pairs if k in ampa and abs(ampa[k] - ref_pairs[k]) > 1e-3 * max(1.0, ref_pairs[k])]
    ok = (n == N and not miss and not gbad and w == {0.2})
    return sim, dict(sim_id=sim.ID, n_neurons=n, weights_on_load=sorted(w), pairs_missing=len(miss), g_mismatch=len(gbad), loaded_ok=bool(ok))

def run_sim(NES, client, tag, groups, variant, cues, run_ms, dt, record=False, tail_note=''):
    """cues: list of (time_ms_relative_to_T0, neuron). returns dict(spikes rel T0, rec, readback, weights stats)."""
    m = mem_available_gb(); assert m >= 100, 'RAM %.1f' % m
    ref, plist = build(groups, variant)
    sim, load = fresh_copy(NES, client, 'arborA-' + tag, ref); assert load['loaded_ok'], load
    rec = None; rep = None
    try:
        rep = L.apply_pairs(sim, plist)
        assert rep['n_readback_mismatch'] == 0 and rep['weight_min'] >= 0 and rep['weight_max'] <= 1 + 1e-9, rep
        sim.SetSTDP(_DoSTDP=False)
        r = sim.SetSpecificAPTimes([(float(T0 + t), int(c)) for t, c in cues]); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=float(T0 + run_ms), Dt_ms=dt, timeout_s=1800.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
        if record: rec = sim.GetRecording()['Recording']
    finally:
        try: print('deleted', sim.ID, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sim.ID, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    rb = dict(n_pairs=rep['n_pairs'], n_mismatch=rep['n_readback_mismatch'], wmin=rep['weight_min'], wmax=rep['weight_max'], nmda_nonzero_after=rep['nmda_nonzero_after'])
    return spikes, rec, rb, load

def analyse_ripple(events, spikes, groups, run_ms=150.0):
    pyr = range(NP); its = range(NP, N)
    evs = sorted(events, key=lambda e: e[1]); first = evs[0][1]
    allmem = set().union(*[set(groups[gi][0]) for gi, _ in events])
    out = dict(memories=[]); ct = []
    for k, (gi, on) in enumerate(evs):
        mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]
        wend = evs[k + 1][1] if k + 1 < len(evs) else run_ms
        lat = {}
        for m in nc:
            xs = [x for x in spikes.get(m, []) if on <= x < on + 10.0]; lat[m] = (xs[0] - on) if xs else None
        comp = all(v is not None for v in lat.values())
        for m in nc:
            for x in spikes.get(m, []):
                if x < on: ct.append((gi, m, x))
        memsp = [x for m in mem for x in spikes.get(m, []) if x >= on]
        nint = {i: len([x for x in spikes.get(i, []) if on <= x < wend]) for i in its}
        out['memories'].append(dict(group=gi, cue_onset_ms=on, complete=comp, n_noncue_fired_10ms=sum(v is not None for v in lat.values()),
            noncue_latency_ms={str(m): v for m, v in lat.items()}, latency_last_noncue_ms=(max(lat.values()) if comp else None),
            last_member_spike_after_cue_ms=(max(memsp) - on if memsp else None), member_spikes_total=len(memsp),
            int_spikes_in_window=sum(nint.values()), ints_fired=[i for i, v in nint.items() if v]))
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
    out['ints_that_fired'] = sorted(i for i in its if spikes.get(i))
    out['all_complete'] = all(m['complete'] for m in out['memories'])
    out['terminates'] = bool(not out['active_in_last_10ms_of_run'] and not out['burst_over_40ms_groups'])
    out['ripple_success'] = bool(out['all_complete'] and not ct and out['spurious_nonmember_pyr_spikes'] == 0 and out['activity_ends_within_100ms'] and out['terminates'])
    return out

def ripple_cues(groups, events):
    return [(on + o, c) for gi, on in events for c, o in zip(groups[gi][1], CUE_OFFS)]
