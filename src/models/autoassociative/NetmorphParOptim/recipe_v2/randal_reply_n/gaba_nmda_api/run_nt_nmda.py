#!/usr/bin/env python3
"""Check 2 of the patch: program the E4 recall (R3 recipe pair list, c = 1.5) through the API with the NEW argument:
AMPA by BatchSetPrePostStrength (old call), then NMDA = 0.56 x AMPA target by BatchSetPrePostStrength(..., Neurotransmitter='NMDA').
GABA stays at the grown weight 0.2 (x1). Compare spikes with the stored FILE-route run raw_K_nmda056_x1.json (gaba_vm) = same programming
written into a model-file copy. One simulation, PATCHED instance only (API 8010). Output: raw_nt_nmda056_x1.json here."""
import sys, os, json, time, numpy as np
GV = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_vm/'; HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_nmda_api/'
sys.path.insert(0, GV)
import run_vm as R, recipelib as L, dyn2 as H
sys.path.insert(0, '/home/johnjose/BrainGenix/wt/pythonclient-receptor-strength')   # patched client first
import BrainGenix.NES as NES, inspect
assert 'Neurotransmitter' in inspect.signature(NES.Simulation.Simulation.BatchSetPrePostStrength).parameters
NP, N = R.NP, R.N; r_nmda = 0.56; c = 1.5
t0 = time.time(); D = L.Dump(H.DUMPS[R.SEED]); plist = R.pair_list(D, c, ampa=1.0, capcue=H.CAPCUE)
ev = R.events(); cues = []
for e in ev:
    cues += [(e['t'] + o, cc) for cc, o in zip(R.GROUPS[e['first']][1], R.CUE_OFFS)]
    if e['second'] is not None: cues += [(e['t'] + e['delta'] + o, cc) for cc, o in zip(R.GROUPS[e['second']][1], R.CUE_OFFS)]
run_ms = R.T0 + len(ev) * R.SPACING
_, client = H.connect()
cf = NES.Simulation.Configuration(); cf.Name = 'nt-nmda056'; cf.Seed = 0
sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0; print('sim', sid, flush=True)
out = dict(model=R.SRC, c=c, nmda_ratio=r_nmda, sim_id=sid)
try:
    sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
    sim.ModelLoad(R.SRC)
    conn0 = sim.GetConnectome(Pause_s=0.1); nmda_g = {}; gaba0 = {}
    for p in range(len(conn0['ConnectionTargets'])):
        for i, q in enumerate(conn0['ConnectionTargets'][p]):
            t = int(conn0['ConnectionTypes'][p][i]); g = float(conn0['ConnectionGPeakSum'][p][i])
            if t == 3: nmda_g[(p, int(q))] = g
            if t == 2: gaba0[(p, int(q))] = float(conn0['ConnectionWeights'][p][i])
    # step 1: AMPA, old call (zeroes NMDA on the programmed pairs)
    ra = L.apply_pairs(sim, plist); assert ra['n_readback_mismatch'] == 0, ra
    # step 2: NMDA through the new argument, only on pairs that have an NMDA group
    sel = [(a, b, r_nmda * cond) for a, b, cond, g in plist if (a, b) in nmda_g]
    capped = sum(1 for a, b, w in sel if w > nmda_g[(a, b)])
    for s in range(0, len(sel), 500):
        ch = sel[s:s + 500]
        r = sim.BatchSetPrePostStrength([x[0] for x in ch], [x[1] for x in ch], [x[2] for x in ch], Neurotransmitter='NMDA'); assert r.get('StatusCode', 1) == 0, r
    conn = sim.GetConnectome(Pause_s=0.1); amp = {}; nm = {}; gw = {}
    for p in range(len(conn['ConnectionTargets'])):
        for i, q in enumerate(conn['ConnectionTargets'][p]):
            t = int(conn['ConnectionTypes'][p][i]); w = float(conn['ConnectionWeights'][p][i]); g = float(conn['ConnectionGPeakSum'][p][i])
            if t == 1: amp[(p, int(q))] = w * g
            elif t == 3: nm[(p, int(q))] = (w, g)
            elif t == 2: gw[(p, int(q))] = w
    badA = [(a, b) for a, b, cond, g in plist if abs(amp[(a, b)] - cond) > 1e-3 * max(1.0, cond)]
    badN = [(a, b) for a, b, w in sel if abs(min(1.0, nm[(a, b)][0]) * nm[(a, b)][1] - min(w, nmda_g[(a, b)])) > 1e-3 * max(1.0, w)]
    out['readback'] = dict(n_pairs=len(plist), n_nmda_set=len(sel), nmda_capped=capped, ampa_mismatch=len(badA), nmda_mismatch=len(badN), gaba_weight_unchanged=bool(gw == gaba0),
                           gaba_weights=sorted(set(round(v, 4) for v in gw.values())))
    print('readback', out['readback'], flush=True); assert not badA and not badN
    r = sim.SetSpecificAPTimes([(float(t), int(cc)) for t, cc in cues]); assert r.get('StatusCode', 1) == 0, r
    sim.RecordAll(float(os.environ.get('GVM_VM_MS', '1100')))
    sim.RunAndWait(Runtime_ms=float(run_ms), Dt_ms=0.1, timeout_s=5400.0)
    sp = sim.GetSpikeTimes()['SpikeTimes']
    out['spikes'] = {int(k): [float(x) for x in v['tSpike_ms']] for k, v in sp.items() if v['tSpike_ms']}
finally:
    try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
    except Exception as e: print('DELETE FAILED', sid, e, flush=True)
out['wall_s'] = time.time() - t0
json.dump(out, open(HERE + 'raw_nt_nmda056_x1.json', 'w'), separators=(',', ':'), default=float)
ref = json.load(open(GV + 'raw_K_nmda056_x1.json'))['spikes']; got = out['spikes']
same_cells = sorted(map(int, ref)) == sorted(got); n = 0; m = 0.0; lenok = True
for k in got:
    a = ref[str(k)] if str(k) in ref else ref.get(k, [])
    if len(a) != len(got[k]): lenok = False; continue
    for x, y in zip(a, got[k]): m = max(m, abs(x - y)); n += 1
print('COMPARE vs file-route K_nmda056_x1: same spiking cells', same_cells, 'same counts', lenok, 'spikes', n, 'total', sum(len(v) for v in got.values()), 'ref total', sum(len(v) for v in ref.values()), 'max diff ms', m)
json.dump(dict(same_cells=same_cells, same_counts=lenok, n_compared=n, max_diff_ms=m, total=sum(len(v) for v in got.values()), ref_total=sum(len(v) for v in ref.values())), open(HERE + 'compare_nt_vs_file.json', 'w'))
