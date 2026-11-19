#!/usr/bin/env python3
"""One simulation per process on the PATCHED instance (API 8010 / NES 8011). Own code; recipe logic (model load check, pair programming read-back, SG zeroing, cue offsets) copied from headline_i/dyn2.py.
usage: run_sim.py TAG KEY MODE DESIGN.json C SG     MODE = ov (per memory: full cue, 3-cell a, 3-cell b; 500 ms apart) | rip (per memory: control + ripple events; 600 ms apart)
DESIGN.json = {"groups":[{"cue":[..],"noncue":[..],"members":[..]}, ...]}.  writes raw_TAG.json (all spike times, relative to T0), deletes the sim in a finally block."""
import sys, json, os
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0, '/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient')
import ovlib as O, recipelib as L
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_overlap_j/'; PORT = 8010
CUE_OFFS = [0.0, 0.5, 1.0, 1.5]; T0 = 20.0
RIP_F = (100, 150, 200, 250); RIP_N = (2, 3)
def connect():
    import BrainGenix.NES as NES
    cfg = NES.Client.Configuration(); cfg.Mode = NES.Client.Modes.Remote; cfg.Host = 'localhost'; cfg.Port = PORT; cfg.UseHTTPS = False
    cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username = 'Admonishing'; cfg.Password = 'Instruction'
    client = NES.Client.Client(cfg); assert client.IsReady(), 'NES not ready'; return NES, client
def schedule(groups, mode, cued=None):
    evs = []; cues = []; t = 0.0
    for gi, g in enumerate(groups):
        if cued is not None and gi not in cued: continue
        cue = sorted(g['cue'])
        if mode == 'ov':
            for lab, cc, exp in (('full', cue, True), ('3a', cue[:3], False), ('3b', cue[1:], False)):
                evs.append(dict(group=gi, label=lab, cue=list(cc), t=t, expect=exp, f=None, n=None)); cues += [(t + o, c) for c, o in zip(cc, CUE_OFFS)]; t += 500.0
        else:
            part = cue[1:]
            evs.append(dict(group=gi, label='control', cue=list(part), t=t, expect=False, f=None, n=1)); cues += [(t + o, c) for c, o in zip(part, CUE_OFFS)]; t += 600.0
            for n in RIP_N:
                for f in RIP_F:
                    per = 1000.0 / f
                    evs.append(dict(group=gi, label='rip n%d f%d' % (n, f), cue=list(part), t=t, expect=False, f=f, n=n))
                    cues += [(t + o + k * per, c) for c, o in zip(part, CUE_OFFS) for k in range(n)]; t += 600.0
    return evs, cues, t
def main():
    tag, key, mode, dfile, c, sg = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), sys.argv[6] == '1'
    D, P = O.load(key); N = D.N; NP = 96; assert N == 116
    dd = json.load(open(dfile)); groups = dd['groups']; cued = set(dd['cued']) if 'cued' in dd else None
    plist = O.pair_list_ov(D, [(g['members'], g['cue']) for g in groups], c); ref = {(a, b): g for a, b, cc, g in plist}
    NES, client = connect()
    cf = NES.Simulation.Configuration(); cf.Name = 'rov-' + tag; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0
    print('sim', sid, flush=True)
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
        sim.ModelLoad(O.MODELS[key]['model'])
        n = len(sim.GetSomaPositions().get('SomaCenters', []))
        conn = sim.GetConnectome(Pause_s=0.1); ampa = {}; wa = set(); wg = set()
        for pre in range(len(conn['ConnectionTargets'])):
            for i, post in enumerate(conn['ConnectionTargets'][pre]):
                t = int(conn['ConnectionTypes'][pre][i]); w = round(float(conn['ConnectionWeights'][pre][i]), 3)
                (wg if t == 2 else wa).add(w)
                if t == 1: ampa[(pre, int(post))] = float(conn['ConnectionGPeakSum'][pre][i])
        miss = [k for k in ref if k not in ampa]; gbad = [k for k in ref if k in ampa and abs(ampa[k] - ref[k]) > 1e-3 * max(1.0, ref[k])]
        load = dict(sim_id=sid, model=O.MODELS[key]['model'], n_neurons=n, pairs_missing=len(miss), g_mismatch=len(gbad), n_ampa_pairs=len(ampa), n_programmed=len(plist),
                    loaded_ok=bool(n == N and not miss and not gbad and wa == {0.2} and wg == {0.2}))
        print(load, flush=True); assert load['loaded_ok'], load
        rep = L.apply_pairs(sim, plist); assert rep['n_readback_mismatch'] == 0, rep
        if sg:
            conn = sim.GetConnectome(Pause_s=0.1); gp = []
            for pre in D.its:
                for post, t in zip(conn['ConnectionTargets'][pre], conn['ConnectionTypes'][pre]):
                    if int(t) == 2: gp.append((pre, int(post)))
            for a, b in gp: sim.SetPrePostStrength(a, b, 0.0)
            conn = sim.GetConnectome(Pause_s=0.1)
            gw = [float(w) for pre in D.its for w, t in zip(conn['ConnectionWeights'][pre], conn['ConnectionTypes'][pre]) if int(t) == 2]
            rep['gaba_pairs_zeroed'] = len(gp); rep['gaba_nonzero_after'] = sum(1 for w in gw if w != 0); print('SG', len(gp), rep['gaba_nonzero_after'], flush=True)
            assert rep['gaba_nonzero_after'] == 0
        sim.SetSTDP(_DoSTDP=False)
        evs, cues, tend = schedule(groups, mode, cued)
        r = sim.SetSpecificAPTimes([(float(T0 + tt), int(cc)) for tt, cc in cues]); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=float(T0 + tend + 100), Dt_ms=1.0, timeout_s=3000.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    json.dump(dict(tag=tag, key=key, mode=mode, c=c, sg=sg, groups=groups, events=evs, spikes=spikes, load=load, readback={k: v for k, v in rep.items() if k != 'mismatches'}, sim_id=sid), open(HERE + 'raw_%s.json' % tag, 'w'), separators=(',', ':'), default=float)
    print('done', tag, sum(len(v) for v in spikes.values()), 'spikes', flush=True)
if __name__ == '__main__': main()
