#!/usr/bin/env python3
"""fresh_run recall runner. PATCHED instance only (API 8010 / NES 8011), patched client. One simulation per process, deleted in finally.
usage: fr_dyn.py TAG REAL EFF DESIGN C   REAL = real model key (B1_s33333 | B1_s55555 | C1_s33333 | base_s44444 ...), EFF = effective-graph dump path (pruned copy or the real dump),
DESIGN = json {'groups':[{'cue':[..],'noncue':[..],'members':[..]}]}, C = background nS (0.15 / 1.5).
Programming through the API only: AMPA = R3 recipe (ovlib.pair_list_ov on the EFFECTIVE graph, pairs absent there -> 0) via legacy batch call; then NMDA = 0.56 x AMPA (Neurotransmitter='NMDA'); GABA x1 (0.2 x peak). STDP off.
Events per memory: full 4-cell cue, four 3-cell sub-cues; 800 ms spacing. writes raw_TAG.json"""
import sys, os, json, time, itertools, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_run/'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp')
import run_exp as RE            # patched client import + program(), read_conn(), connect()
import ovlib as O, recipelib as L
NES = RE.NES; NP = 96; N = 116; T0 = 20.0; SP = 800.0; CUE_OFFS = RE.CUE_OFFS
def model_of(real):
    kind, sd = real.split('_s')
    if kind == 'base': return O.MODELS['s' + sd]['model'], O.MODELS['s' + sd]['dump']
    pre = 'v2-rrn-' if (kind == 'B1' and sd in ('33333', '44444')) else 'v2-fr-'
    return pre + real + '0000', HERE + 'grow_%s/viz/sample_0000.json' % real
def main():
    tag, real, eff, design, c = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]); r = 0.56; f = 1.0
    t_start = time.time(); model, rdump = model_of(real)
    groups = json.load(open(design))['groups']
    Dr = L.Dump(rdump); De = L.Dump(eff); assert Dr.N == De.N == N
    pe = O.pair_list_ov(De, [(g['members'], g['cue']) for g in groups], c); ce = {(a, b): cc for a, b, cc, g in pe}
    plist = []
    for a in range(NP):
        for b in range(N):
            g = float(Dr.G[a, b])
            if a == b or g <= 0: continue
            cond = ce.get((a, b), 0.0); assert cond <= g * (1 + 1e-6) + 1e-6, (a, b, cond, g)
            plist.append((a, b, round(min(cond, g), 6), round(g, 6)))
    ev = []; k = 0
    for gi, g in enumerate(groups):
        ev.append(dict(kind='full', group=gi, cue=g['cue'])); 
        for s in itertools.combinations(g['cue'], 3): ev.append(dict(kind='p3', group=gi, cue=list(s)))
    cues = []
    for k, e in enumerate(ev):
        e['t'] = T0 + k * SP; e['cues'] = [(e['t'] + o, cc) for cc, o in zip(sorted(e['cue']), CUE_OFFS)]; cues += e['cues']
    run_ms = T0 + len(ev) * SP; cues = sorted((float(t), int(cc)) for t, cc in cues)
    client = RE.connect(); cf = NES.Simulation.Configuration(); cf.Name = 'fr-' + tag; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0; print('sim', sid, tag, flush=True)
    out = dict(tag=tag, real=real, eff=eff, design=design, c=c, r=r, f=f, model=model, groups=groups, events=ev, run_ms=run_ms, sim_id=sid, dt_ms=0.1, n_pairs_programmed=len(plist))
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
        sim.ModelLoad(model)
        n = len(sim.GetSomaPositions().get('SomaCenters', [])); assert n == N, n
        c_load = RE.read_conn(sim)
        out['load'] = dict(n_neurons=n, weights_on_load={str(t): sorted(set(round(w, 3) for w, g in d.values())) for t, d in c_load.items()}, pairs_missing=sum(1 for a, b, cond, g in plist if (a, b) not in c_load[1]),
                           g_mismatch=sum(1 for a, b, cond, g in plist if (a, b) in c_load[1] and abs(c_load[1][(a, b)][1] - g) > 1e-3 * max(1.0, g)))
        assert out['load']['pairs_missing'] == 0 and out['load']['g_mismatch'] == 0, out['load']
        rep, _ = RE.program(sim, plist, r, f, groups); out['program'] = rep; print('program', json.dumps(rep)[:400], flush=True)
        sim.SetSTDP(_DoSTDP=False)
        rr = sim.SetSpecificAPTimes(cues); assert rr.get('StatusCode', 1) == 0, rr
        sim.RecordAll(1.0)
        sim.RunAndWait(Runtime_ms=float(run_ms), Dt_ms=0.1, timeout_s=7200.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
        out['spikes'] = {int(k_): [float(x) for x in v['tSpike_ms']] for k_, v in sp.items() if v['tSpike_ms']}
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    out['wall_s'] = time.time() - t_start
    json.dump(out, open(HERE + 'raw_%s.json' % tag, 'w'), separators=(',', ':'), default=float)
    print('done', tag, 'wall', round(out['wall_s']), 'spikes', sum(len(v) for v in out['spikes'].values()), flush=True)
if __name__ == '__main__': main()
