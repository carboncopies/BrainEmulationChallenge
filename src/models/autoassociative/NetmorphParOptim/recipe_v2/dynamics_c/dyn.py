#!/usr/bin/env python3
"""Dynamics check on the patched-build V1n30 networks (96 Pyr + 30 Int), PATCHED instance only (API 8010 / NES 8011).
Own code (no edits to NES/API or earlier scripts); recipe logic copied from recipe_v2/fable_design_S1/design.py + ripple_S1_R3/r3lib.py (R3 recipe, single-run protocol and `clean` criterion).
usage: dyn.py TAG SEED DESIGN BGC SG(0|1)   DESIGN = name of groups_<DESIGN>_s<SEED>.json ; BGC = uniform Pyr->Pyr background per-pair conductance cap (nS), 0 = pruned
writes raw_TAG.json. One simulation per process, deleted in a finally block."""
import sys, json, os, numpy as np
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0, '/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient')
import recipelib as L
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/dynamics_c/'
PORT = 8010
MODELS = {16180: 'v2-lfc-V1n30_s16180_p0d0175_i0d04950000', 27182: 'v2-lfc-V1n30_s27182_p0d0175_i0d04950000'}
DUMPS = {s: '/home/johnjose/cos/netmorph_work/recipe_v2/linefix_c/grow_V1n30_s%d_p0d0175_i0d0495/viz/sample_0000.json' % s for s in MODELS}
CUE_OFFS = [0.0, 0.5, 1.0, 1.5]; T0 = 20.0
T = 16.5; LNN = 8.0; LNC = 8.0; CAPCUE = 10.0
def connect():
    import BrainGenix.NES as NES
    cfg = NES.Client.Configuration()
    cfg.Mode = NES.Client.Modes.Remote; cfg.Host = 'localhost'; cfg.Port = PORT; cfg.UseHTTPS = False
    cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username = 'Admonishing'; cfg.Password = 'Instruction'
    client = NES.Client.Client(cfg); assert client.IsReady(), 'NES not ready'
    return NES, client
def load_groups(fn):
    return [(sorted(g['members']), sorted(g['cue'])) for g in json.load(open(fn))['groups']]
def pair_list(D, groups, c):
    """R3 recipe weights: returns [(pre,post,conductance,g,role)] for every Pyr->Pyr and Pyr->Int pair with g>0.
    cue->noncue = T/4 per pair (needs g>=T/4), noncue->noncue and noncue->cue loops capped at 8 nS total per post cell, cue->cue = background,
    Pyr->Int weight 1 except cue->interneuron summed to at most 10 nS, all other Pyr->Pyr = min(g, c) (uniform background, c=0 pruned)."""
    G = D.G; nP = 96; N = D.N
    W = np.zeros((N, N))
    if c > 0: W[:nP, :nP] = np.minimum(1.0, c / np.maximum(G[:nP, :nP], 1e-9))
    for mem, cue in groups:
        nc = [m for m in mem if m not in cue]
        for a in mem:
            for b in mem:
                if a != b and not (a in cue and b in cue and c > 0): W[a, b] = 0.0
        for n in nc:
            for cc in cue:
                assert G[cc, n] >= T / 4 - 1e-9, (cc, n, G[cc, n]); W[cc, n] = (T / 4) / G[cc, n]
            s = sum(G[m, n] for m in nc if m != n); sc = min(1.0, LNN / s) if s > 0 else 0.0
            for m in nc:
                if m != n and G[m, n] > 0: W[m, n] = sc
        for cc in cue:
            s = sum(G[m, cc] for m in nc); sc = min(1.0, LNC / s) if s > 0 else 0.0
            for m in nc:
                if G[m, cc] > 0: W[m, cc] = sc
    W[:nP, nP:] = 1.0
    for mem, cue in groups:
        for k in range(nP, N):
            Cs = sum(G[cc, k] for cc in cue)
            if Cs > CAPCUE:
                for cc in cue: W[cc, k] = CAPCUE / Cs
    out = []
    for a in range(nP):
        for b in range(N):
            g = float(G[a, b])
            if a == b or g <= 0: continue
            out.append((a, b, round(min(float(W[a, b]), 1.0) * g, 6), round(g, 6)))
    return out
def main():
    tag, seed, design, c, sg = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), sys.argv[5] == '1'
    D = L.Dump(DUMPS[seed]); N = D.N; NP = 96; assert N == 126
    groups = load_groups(HERE + 'groups_%s_s%d.json' % (design, seed))
    plist = pair_list(D, groups, c); ref = {(a, b): g for a, b, cc, g in plist}
    NES, client = connect()
    cf = NES.Simulation.Configuration(); cf.Name = 'dynC-' + tag; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0
    print('sim', sid, flush=True)
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
        sim.ModelLoad(MODELS[seed])
        n = len(sim.GetSomaPositions().get('SomaCenters', []))
        conn = sim.GetConnectome(Pause_s=0.1); ampa = {}; wa = set(); wg = set()
        for pre in range(len(conn['ConnectionTargets'])):
            for i, post in enumerate(conn['ConnectionTargets'][pre]):
                t = int(conn['ConnectionTypes'][pre][i]); w = round(float(conn['ConnectionWeights'][pre][i]), 3)
                (wg if t == 2 else wa).add(w)
                if t == 1: ampa[(pre, int(post))] = float(conn['ConnectionGPeakSum'][pre][i])
        miss = [k for k in ref if k not in ampa]; gbad = [k for k in ref if k in ampa and abs(ampa[k] - ref[k]) > 1e-3 * max(1.0, ref[k])]
        load = dict(sim_id=sid, model=MODELS[seed], n_neurons=n, ampa_nmda_weights_on_load=sorted(wa), gaba_weights_on_load=sorted(wg), pairs_missing=len(miss), g_mismatch=len(gbad),
                    n_ampa_pairs=len(ampa), n_programmed=len(plist), loaded_ok=bool(n == N and not miss and not gbad and wa == {0.2} and wg == {0.2}))
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
        else:
            conn = sim.GetConnectome(Pause_s=0.1)
            gw = [float(w) for pre in D.its for w, t in zip(conn['ConnectionWeights'][pre], conn['ConnectionTypes'][pre]) if int(t) == 2]
            rep['gaba_pairs'] = len(gw); rep['gaba_weights'] = sorted({round(w, 3) for w in gw})
        sim.SetSTDP(_DoSTDP=False)
        evs = []; t = 0.0
        for gi, (mem, cue) in enumerate(groups):
            evs.append(dict(label='G%d full 4-cell' % gi, group=gi, cue=list(cue), t=t, expect=True)); t += 500
            evs.append(dict(label='G%d 3-cell a' % gi, group=gi, cue=list(cue[:3]), t=t, expect=False)); t += 500
            evs.append(dict(label='G%d 3-cell b' % gi, group=gi, cue=list(cue[1:]), t=t, expect=False)); t += 500
        cues = [(e['t'] + o, cc) for e in evs for cc, o in zip(e['cue'], CUE_OFFS)]
        r = sim.SetSpecificAPTimes([(float(T0 + tt), int(cc)) for tt, cc in cues]); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=float(T0 + t + 100), Dt_ms=1.0, timeout_s=3000.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    spikes = {int(k): sorted(round(float(x) - T0, 3) for x in v['tSpike_ms']) for k, v in sp.items()}
    allmem = {m for mm, _ in groups for m in mm}; res = []
    for e in evs:
        gi = e['group']; mem, cue = groups[gi]; nc = [m for m in mem if m not in cue]; t0 = e['t']
        w = lambda i: [x - t0 for x in spikes.get(i, []) if t0 <= x < t0 + 450]
        fired = [m for m in nc if w(m)]; otherg = [m for g2, (mm, _) in enumerate(groups) if g2 != gi for m in mm if w(m)]
        op = [i for i in range(NP) if i not in allmem and w(i)]
        lat = min((x for m in fired for x in w(m)), default=None); memsp = [x for m in mem for x in w(m)]
        res.append(dict(label=e['label'], cue=e['cue'], expect_complete=e['expect'], noncue_fired=len(fired), noncue_total=len(nc), latency_ms=lat, member_spikes=len(memsp),
            burst_end_ms=max(memsp, default=None), other_group_members_fired=len(otherg), other_pyr_fired=len(op), n_other_pyr_spikes=sum(len(w(i)) for i in op),
            interneuron_spikes=sum(len(w(i)) for i in range(NP, N)), ints_fired=[i for i in range(NP, N) if w(i)],
            last_pyr_spike_ms=max((x for i in range(NP) for x in w(i)), default=None),
            clean=bool((len(fired) == len(nc) if e['expect'] else len(fired) == 0) and not otherg and not op)))
        r_ = res[-1]; print(tag, r_['label'], r_['noncue_fired'], r_['noncue_total'], r_['latency_ms'], r_['member_spikes'], r_['interneuron_spikes'], r_['other_pyr_fired'], r_['clean'], flush=True)
    json.dump(dict(tag=tag, seed=seed, design=design, c=c, sg=sg, groups=groups, events=res, load=load, readback={k: v for k, v in rep.items() if k != 'mismatches'}, sim_id=sid), open(HERE + 'raw_%s.json' % tag, 'w'), separators=(',', ':'))
if __name__ == '__main__': main()
