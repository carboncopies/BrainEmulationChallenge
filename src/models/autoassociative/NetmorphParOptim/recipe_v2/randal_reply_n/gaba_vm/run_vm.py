#!/usr/bin/env python3
"""gaba_vm runner (PREREGISTRATION.md). PATCHED instance only (API 8010). One simulation per process, deleted in finally; model copy deleted in finally.
usage: run_vm.py TAG C GABA KNOB PROG
  C     background Pyr->Pyr cap (nS), 0 = pruned
  GABA  sg | 1 | 2 | 5   (GABA receptor weight 0.2 x factor; sg = 0)
  KNOB  none | ahp0 | ahp2 | adp0 | adp3 | nmda056 | nmda100 | ampa125 | lat
  PROG  file (program into a model-file copy) | api (dyn2 path: SetPrePostStrength; only with GABA 1, KNOB none)"""
import sys, os, json, shutil, time, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/gaba_vm/'
sys.path.insert(0, HERE); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/headline_i')
sys.path.insert(0, '/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient')
import recipelib as L, dyn2 as H
from modelfile import RDT, neurons, comp2neuron
MDIR = '/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/Models/'
SEED = 'V1n20_s33333'; SRC = H.MODELS[SEED]; NP = 96; N = 116
GROUPS = H.load_groups(H.HERE + 'groups_D42_%s.json' % SEED)
CUE_OFFS = [0.0, 0.5, 1.0, 1.5]; T0 = 20.0; SPACING = 500.0; DELTAS = [5.0, 10.0, 20.0, 50.0]
VM_MS = float(os.environ.get('GVM_VM_MS', '1100'))   # figure-only reruns (added after the first results) record longer

def events():
    ev = [dict(label='e0 G0 alone', first=0, second=None, delta=None), dict(label='e1 G0>G1 d10', first=0, second=1, delta=10.0),
          dict(label='e2 G1 alone', first=1, second=None, delta=None), dict(label='e3 G2 alone', first=2, second=None, delta=None)]
    for a in range(3):
        for b in range(3):
            if a != b:
                for d in DELTAS: ev.append(dict(label='G%d>G%d d%g' % (a, b, d), first=a, second=b, delta=d))
    for k, e in enumerate(ev): e['t'] = T0 + k * SPACING
    return ev

def pair_list(D, c, ampa=1.0, capcue=H.CAPCUE):
    """copy of dyn2.pair_list with the cue->interneuron cap and a programmed-AMPA scale as parameters. returns [(pre,post,cond,g,programmed_flag)]"""
    G = D.G; T, LNN, LNC = H.T, H.LNN, H.LNC
    W = np.zeros((N, N)); prog = np.zeros((N, N), bool)
    if c > 0: W[:NP, :NP] = np.minimum(1.0, c / np.maximum(G[:NP, :NP], 1e-9))
    for mem, cue in GROUPS:
        nc = [m for m in mem if m not in cue]
        for a in mem:
            for b in mem:
                if a != b and not (a in cue and b in cue and c > 0): W[a, b] = 0.0
        for n in nc:
            for cc in cue:
                assert G[cc, n] >= T / 4 - 1e-9; W[cc, n] = (T / 4) / G[cc, n]; prog[cc, n] = True
            s = sum(G[m, n] for m in nc if m != n); sc = min(1.0, LNN / s) if s > 0 else 0.0
            for m in nc:
                if m != n and G[m, n] > 0: W[m, n] = sc; prog[m, n] = True
        for cc in cue:
            s = sum(G[m, cc] for m in nc); sc = min(1.0, LNC / s) if s > 0 else 0.0
            for m in nc:
                if G[m, cc] > 0: W[m, cc] = sc; prog[m, cc] = True
    W[:NP, NP:] = 1.0
    for mem, cue in GROUPS:
        for k in range(NP, N):
            Cs = sum(G[cc, k] for cc in cue)
            if Cs > capcue:
                for cc in cue: W[cc, k] = capcue / Cs
    out = []
    for a in range(NP):
        for b in range(N):
            g = float(G[a, b])
            if a == b or g <= 0: continue
            w = min(float(W[a, b]), 1.0) * (ampa if prog[a, b] else 1.0)
            out.append((a, b, round(w * g, 6), round(g, 6)))
    return out

def patch_copy(dst, plist, gaba, knob):
    """copy SRC -> dst and write programming + knobs. returns a report of what was written (read back from the file)."""
    shutil.copyfile(MDIR + SRC, dst)
    h, roff, nl = neurons(dst, N); c2n = comp2neuron(nl)
    rec = np.memmap(dst, dtype=RDT, mode='r+', offset=roff, shape=(h['Rec'],))
    pre = np.array([c2n[int(x)] for x in rec['Src']]); post = np.array([c2n[int(x)] for x in rec['Dst']]); nt = rec['NT'].copy()
    rep = dict(n_receptors=int(h['Rec']))
    # lateral inhibition: Pyr->Int AMPA peak conductance x2 (changes g_peak_sum, so do it before computing weights)
    gscale = np.ones(len(rec), np.float32)
    if knob == 'lat':
        m = (nt == 0) & (pre < NP) & (post >= NP); gscale[m] = 2.0; rec['G'][m] = (rec['G'][m] * np.float32(2.0)).astype('<f4'); rep['lat_receptors_x2'] = int(m.sum())
    key = pre.astype(np.int64) * 1000 + post
    target = {(a * 1000 + b): cond for a, b, cond, g in plist}
    gsum = {}
    for t_ in (0, 2):
        m = nt == t_; ks = key[m]; gs = rec['G'][m].astype(np.float64)
        u, inv = np.unique(ks, return_inverse=True); s = np.bincount(inv, weights=gs); gsum[t_] = dict(zip(u.tolist(), s.tolist()))
    r = {'nmda056': 0.56, 'nmda100': 1.0}.get(knob, 0.0)
    W = rec['W'].astype(np.float64)
    nmda_capped = 0; nprog = 0
    for i in np.where((nt == 0) | (nt == 2))[0]:
        k = int(key[i])
        if pre[i] >= NP: continue
        cond = target.get(k)
        if cond is None: cond = 0.0
        if knob == 'lat' and post[i] >= NP: cond = cond * 2.0   # same weight as the API recipe, on the doubled peak conductance
        if nt[i] == 0: W[i] = cond / gsum[0][k]
        else:
            if k not in gsum[0]: W[i] = 0.0; continue
            want = r * cond; W[i] = want / gsum[2][k]
            if W[i] > 1.0: nmda_capped += 1
    rec['W'][:] = W.astype('<f4')
    mg = nt == 1; rec['W'][mg] = np.float32(0.0 if gaba == 'sg' else 0.2 * float(gaba)); rep['gaba_receptors'] = int(mg.sum())
    rec.flush(); rep['nmda_receptors_weight_gt1_capped'] = nmda_capped
    # neuron parameters (principal cells only, IDs < 96)
    f = dict(ahp0=0.0, ahp2=2.0).get(knob); fa = dict(adp0=0.0, adp3=3.0).get(knob)
    mm = np.memmap(dst, dtype='u1', mode='r+')
    from modelfile import NDT
    for k_, n_ in enumerate(nl[:NP]):
        v = np.ndarray(shape=(1,), dtype=NDT, buffer=mm, offset=n_['off'])
        if f is not None:
            for fld in ('fAHP_g', 'fAHP_gmax', 'sAHP_g', 'sAHP_gmax'): v[fld] = v[fld] * np.float32(f)
        if fa is not None: v['ADP_g'] = v['ADP_g'] * np.float32(fa)
    mm.flush()
    h2, _, nl2 = neurons(dst, N)
    rep['principal_params'] = {fld: float(nl2[0]['rec'][fld]) for fld in ('fAHP_g', 'fAHP_gmax', 'sAHP_g', 'sAHP_gmax', 'ADP_g')}
    rep['interneuron_params'] = {fld: float(nl2[100]['rec'][fld]) for fld in ('fAHP_g', 'fAHP_gmax', 'sAHP_g', 'sAHP_gmax', 'ADP_g')}
    rep['size_equal'] = os.path.getsize(dst) == os.path.getsize(MDIR + SRC)
    return rep, r

def main():
    tag, c, gaba, knob, prog = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
    assert gaba in ('sg', '1', '2', '5') and prog in ('file', 'api')
    if prog == 'api': assert gaba == '1' and knob == 'none'
    t_start = time.time()
    D = L.Dump(H.DUMPS[SEED]); assert D.N == N
    plist = pair_list(D, c, ampa=1.25 if knob == 'ampa125' else 1.0, capcue=1e9 if knob == 'lat' else H.CAPCUE)
    copy = None; rep = {}; r_nmda = 0.0
    if prog == 'file':
        name = 'gvm-%s' % tag; copy = MDIR + name; assert not os.path.exists(copy)
        rep, r_nmda = patch_copy(copy, plist, gaba, knob)
    else: name = SRC
    print('patched', rep, flush=True)
    ev = events(); cues = []
    for e in ev:
        cues += [(e['t'] + o, cc) for cc, o in zip(GROUPS[e['first']][1], CUE_OFFS)]
        if e['second'] is not None: cues += [(e['t'] + e['delta'] + o, cc) for cc, o in zip(GROUPS[e['second']][1], CUE_OFFS)]
    run_ms = T0 + len(ev) * SPACING
    NES, client = H.connect()
    cf = NES.Simulation.Configuration(); cf.Name = 'gvm-' + tag; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0; print('sim', sid, flush=True)
    out = dict(tag=tag, c=c, gaba=gaba, knob=knob, prog=prog, model=name, patch=rep, nmda_ratio=r_nmda, events=ev, sim_id=sid)
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
        sim.ModelLoad(name)
        n = len(sim.GetSomaPositions().get('SomaCenters', [])); assert n == N, n
        if prog == 'api':
            ra = L.apply_pairs(sim, plist); assert ra['n_readback_mismatch'] == 0, ra; out['api_readback'] = {k: v for k, v in ra.items() if k != 'mismatches'}
        conn = sim.GetConnectome(Pause_s=0.1)
        amp = {}; nm = {}; gw = []
        for p_ in range(len(conn['ConnectionTargets'])):
            for i, q in enumerate(conn['ConnectionTargets'][p_]):
                t_ = int(conn['ConnectionTypes'][p_][i]); w_ = float(conn['ConnectionWeights'][p_][i]); g_ = float(conn['ConnectionGPeakSum'][p_][i])
                if t_ == 1: amp[(p_, int(q))] = (w_, g_)
                elif t_ == 3: nm[(p_, int(q))] = (w_, g_)
                elif t_ == 2: gw.append(round(w_, 4))
        bad = [(a, b) for a, b, cond, g in plist if abs(amp[(a, b)][0] * amp[(a, b)][1] - cond * (2.0 if (knob == 'lat' and b >= NP) else 1.0)) > 1e-3 * max(1.0, cond)]
        nm_eff = [min(1.0, w_) * g_ for w_, g_ in nm.values()]
        out['load'] = dict(n_neurons=n, ampa_pairs=len(amp), ampa_cond_mismatch=len(bad), gaba_weight_set=sorted(set(gw)), gaba_pairs=len(gw),
                           nmda_pairs=len(nm), nmda_nonzero=sum(1 for x in nm_eff if x > 0), nmda_eff_sum_nS=float(sum(nm_eff)),
                           pyr_int_ampa_g_mean=float(np.mean([g_ for (a, b), (w_, g_) in amp.items() if b >= NP])))
        print('load', out['load'], flush=True); assert not bad, bad[:5]
        sim.SetSTDP(_DoSTDP=False)
        r = sim.SetSpecificAPTimes([(float(t), int(cc)) for t, cc in cues]); assert r.get('StatusCode', 1) == 0, r
        sim.RecordAll(VM_MS)
        sim.RunAndWait(Runtime_ms=float(run_ms), Dt_ms=0.1, timeout_s=5400.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']; rec = sim.GetRecording()['Recording']
        out['spikes'] = {int(k): [float(x) for x in v['tSpike_ms']] for k, v in sp.items() if v['tSpike_ms']}
        tt = np.array(rec['t_ms'], np.float32); vm = np.array([rec['neurons'][str(i)]['Vm_mV'] if str(i) in rec['neurons'] else rec['neurons'][i]['Vm_mV'] for i in range(N)], np.float32)
        np.savez_compressed(HERE + 'vm_%s.npz' % tag, t=tt, vm=vm)
        gpairs = {}
        for p_ in range(NP, N):
            for i, q in enumerate(conn['ConnectionTargets'][p_]):
                if int(conn['ConnectionTypes'][p_][i]) == 2: gpairs['%d,%d' % (p_, int(q))] = float(conn['ConnectionWeights'][p_][i]) * float(conn['ConnectionGPeakSum'][p_][i])
        out['gaba_pair_cond'] = gpairs
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
        if copy and os.path.exists(copy): os.remove(copy); print('removed copy', copy, flush=True)
    out['wall_s'] = time.time() - t_start
    json.dump(out, open(HERE + 'raw_%s.json' % tag, 'w'), separators=(',', ':'), default=float)
    print('done', tag, 'wall', round(out['wall_s']), 'spiking cells', len(out['spikes']), flush=True)

if __name__ == '__main__': main()
