#!/usr/bin/env python3
"""STDP experiment: one process = training sim (STDP ON) -> trained weights -> probe sim (STDP OFF), PATCHED instance only (API 8010 / NES 8011).
usage: stdp_run.py KEY ARM R C      ARM = A1 (full-cue recall) | A2 (3-cell partial cue + 2nd spike, f cycling 100/150/200/250 Hz); R = repetitions per memory (0 = control, no training); C = background nS
Design = ripple_overlap_j/design_<KEY>_R42.json. writes raw_<KEY>_<ARM>_R<R>_c<C>.json."""
import sys, json
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0, '/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient')
import ovlib as O, recipelib as L, run_sim as R_
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/stdp_k/'; T0 = 20.0; CUE_OFFS = R_.CUE_OFFS; RIP_F = (100, 150, 200, 250); NP = 96; N = 116
def train_events(groups, arm, R):
    evs = []; cues = []; t = 0.0
    for r in range(R):
        for gi, g in enumerate(groups):
            cue = sorted(g['cue'])
            if arm == 'A1':
                evs.append(dict(rep=r, group=gi, t=t, kind='full')); cues += [(t + o, c) for c, o in zip(cue, CUE_OFFS)]
            else:
                f = RIP_F[r % 4]; per = 1000.0 / f; part = cue[1:]
                evs.append(dict(rep=r, group=gi, t=t, kind='rip', f=f)); cues += [(t + o + k * per, c) for c, o in zip(part, CUE_OFFS) for k in range(2)]
            t += 500.0
    return evs, cues, t
def weights_of(sim):
    conn = sim.GetConnectome(Pause_s=0.1); out = {}
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            ty = int(conn['ConnectionTypes'][pre][i])
            if ty == 1: out[(pre, int(post))] = float(conn['ConnectionWeights'][pre][i])
    return out
def load_check(sim, D, ref, model):
    n = len(sim.GetSomaPositions().get('SomaCenters', [])); conn = sim.GetConnectome(Pause_s=0.1); ampa = {}; wa = set(); wg = set()
    for pre in range(len(conn['ConnectionTargets'])):
        for i, post in enumerate(conn['ConnectionTargets'][pre]):
            t = int(conn['ConnectionTypes'][pre][i]); w = round(float(conn['ConnectionWeights'][pre][i]), 3)
            (wg if t == 2 else wa).add(w)
            if t == 1: ampa[(pre, int(post))] = float(conn['ConnectionGPeakSum'][pre][i])
    miss = [k for k in ref if k not in ampa]; gbad = [k for k in ref if k in ampa and abs(ampa[k] - ref[k]) > 1e-3 * max(1.0, ref[k])]
    return dict(model=model, n_neurons=n, pairs_missing=len(miss), g_mismatch=len(gbad), loaded_ok=bool(n == N and not miss and not gbad and wa == {0.2} and wg == {0.2}))
def run_sim(NES, client, name, D, plist, ref, model, stdp, cues, tend):
    cf = NES.Simulation.Configuration(); cf.Name = name; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0; w_after = None; rep = None; load = None
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=bool(stdp))
        sim.ModelLoad(model); load = load_check(sim, D, ref, model); assert load['loaded_ok'], load
        rep = L.apply_pairs(sim, plist); assert rep['n_readback_mismatch'] == 0, rep
        if cues:
            r = sim.SetSpecificAPTimes([(float(T0 + tt), int(cc)) for tt, cc in cues]); assert r.get('StatusCode', 1) == 0, r
            sim.RecordAll(-1); sim.RunAndWait(Runtime_ms=float(T0 + tend + 100), Dt_ms=1.0, timeout_s=3000.0)
            sp = sim.GetSpikeTimes()['SpikeTimes']
            if stdp: w_after = weights_of(sim)
        else: sp = {}
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    return spikes, w_after, load, rep
def main():
    key, arm, R, c = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4])
    tag = '%s_%s_R%d_c%s' % (key, arm, R, sys.argv[4])
    D, P = O.load(key); groups = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/design_%s_R42.json' % key))['groups']
    plist0 = O.pair_list_ov(D, [(g['members'], g['cue']) for g in groups], c); ref = {(a, b): g for a, b, cc, g in plist0}; model = O.MODELS[key]['model']
    NES, client = R_.connect(); out = dict(tag=tag, key=key, arm=arm, R=R, c=c, groups=groups)
    plist1 = plist0
    if R > 0:
        evs, cues, tend = train_events(groups, arm, R)
        sp, w1, load, rep = run_sim(NES, client, 'stdp-tr-' + tag, D, plist0, ref, model, True, cues, tend)
        viol = [(a, b, w1[(a, b)], cc / g) for a, b, cc, g in plist0 if (a, b) not in w1 or not (-1e-6 <= w1[(a, b)] <= 1 + 1e-6)]
        plist1 = [(a, b, round(min(w1[(a, b)], 1.0) * g, 6), g) for a, b, cc, g in plist0]
        gviol = [(a, b) for (a, b, cc, g), (a2, b2, c2, g2) in zip(plist0, plist1) if c2 > g + 1e-6]
        out.update(train_events=evs, train_spikes=sp, train_load=load, weights=[[a, b, cc / g, w1[(a, b)], g] for a, b, cc, g in plist0 if (a, b) in w1], cap_violations=dict(weight=len(viol), conductance=len(gviol), missing=sum(1 for a, b, cc, g in plist0 if (a, b) not in w1)))
        print('trained', tag, 'spikes', sum(len(v) for v in sp.values()), 'cap viol', out['cap_violations'], flush=True)
    else:
        out['weights'] = [[a, b, cc / g, cc / g, g] for a, b, cc, g in plist0]
    evs, cues, tend = R_.schedule(groups, 'ov')
    sp2, _, load2, rep2 = run_sim(NES, client, 'stdp-pr-' + tag, D, plist1, ref, model, False, cues, tend)
    out.update(probe_events=evs, probe_spikes=sp2, probe_load=load2)
    json.dump(out, open(HERE + 'raw_%s.json' % tag, 'w'), separators=(',', ':'), default=float)
    print('done', tag, flush=True)
if __name__ == '__main__': main()
