#!/usr/bin/env python3
"""nmda_gaba_exp runner (PREREGISTRATION.md). PATCHED instance only (API 8010 / NES 8011), patched client. One simulation per process, deleted in finally.
usage: run_exp.py PART SEED C R F        PART = A | B | C | F ; SEED = 33333 | 66666 | 77777 ; C nS ; R = NMDA/AMPA ratio ; F = GABA factor (0,1,2,5)
Programming (API only): AMPA = R3 recipe via legacy batch call; NMDA = R x AMPA via Neurotransmitter='NMDA'; GABA = F x 0.2 x peak via Neurotransmitter='GABA'.
writes raw_TAG.json (and vm_TAG.npz for PART F)."""
import sys, os, json, time, itertools, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp/'
RV2 = '/home/johnjose/cos/netmorph_work/recipe_v2/'
sys.path.insert(0, RV2 + 'ripple_overlap_j'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe')
import ovlib as O, recipelib as L
sys.path.insert(0, '/home/johnjose/BrainGenix/wt/pythonclient-receptor-strength')   # patched client first
import BrainGenix.NES as NES, inspect
assert 'Neurotransmitter' in inspect.signature(NES.Simulation.Simulation.BatchSetPrePostStrength).parameters
assert NES.__file__.startswith('/home/johnjose/BrainGenix/wt/pythonclient-receptor-strength'), NES.__file__
PORT = 8010; NP = 96; N = 116
CUE_OFFS = [0.0, 0.5, 1.0, 1.5]; T0 = 20.0
SPACING = dict(A=800.0, B=800.0, C=1000.0, F=800.0, X=3000.0)   # X = post hoc history check (DEVIATIONS 6)
DELTAS = [5.0, 10.0, 20.0, 50.0, 100.0]; TRAIN_I = [10.0, 20.0, 50.0, 100.0]; TRAIN_N = 5

def connect():
    cfg = NES.Client.Configuration(); cfg.Mode = NES.Client.Modes.Remote; cfg.Host = 'localhost'; cfg.Port = PORT; cfg.UseHTTPS = False
    cfg.AuthenticationMethod = NES.Client.Authentication.Password; cfg.Username = 'Admonishing'; cfg.Password = 'Instruction'
    client = NES.Client.Client(cfg); assert client.IsReady(), 'NES not ready'; return client

def groups_for(part, seed):
    if part == 'B': d = json.load(open(RV2 + 'ripple_overlap_j/design_s%d_F2.json' % seed))
    else: d = json.load(open(RV2 + 'headline_i/groups_D42_V1n20_s%d.json' % seed))
    return [dict(members=sorted(g['members']), cue=sorted(g['cue']), noncue=sorted(g['noncue'])) for g in d['groups']]

def cue_times(t, cells): return [(t + o, c) for c, o in zip(sorted(cells), CUE_OFFS)]

def schedule(part, groups):
    """returns events (dict with kind, label, t, cues=[(t,cell)], plus fields) in time order"""
    ev = []
    def add(**e): ev.append(e)
    if part == 'A':
        for gi, g in enumerate(groups):
            add(kind='full', group=gi, cue=g['cue'], label='G%d full' % gi)
            for s in itertools.combinations(g['cue'], 3): add(kind='p3', group=gi, cue=list(s), label='G%d 3cell %s' % (gi, s))
            for s in itertools.combinations(g['cue'], 2): add(kind='p2', group=gi, cue=list(s), label='G%d 2cell %s' % (gi, s))
    elif part == 'X':
        for gi, g in enumerate(groups):
            for s in itertools.combinations(g['cue'], 3): add(kind='p3', group=gi, cue=list(s), label='G%d 3cell %s' % (gi, s))
    elif part == 'B':
        for gi, g in enumerate(groups):
            for lab, cc in (('full', g['cue']), ('3a', g['cue'][:3]), ('3b', g['cue'][1:])): add(kind='full' if lab == 'full' else 'p3', group=gi, cue=list(cc), label='G%d %s' % (gi, lab))
    elif part == 'C':
        for gi, g in enumerate(groups): add(kind='solo', group=gi, cue=g['cue'], label='G%d alone' % gi)
        for a in range(len(groups)):
            for b in range(len(groups)):
                if a != b:
                    for d in DELTAS: add(kind='pair', group=a, second=b, delta=d, cue=groups[a]['cue'], label='G%d>G%d d%g' % (a, b, d))
        for gi, g in enumerate(groups):
            for I in TRAIN_I: add(kind='train', group=gi, interval=I, cue=g['cue'], label='G%d train I%g' % (gi, I))
    elif part == 'F':
        g0, g1 = groups[0], groups[1]
        add(kind='full', group=0, cue=g0['cue'], label='G0 full')
        add(kind='p3', group=0, cue=g0['cue'][:3], label='G0 3cell')
        add(kind='p2', group=0, cue=g0['cue'][:2], label='G0 2cell')
        add(kind='pair', group=0, second=1, delta=10.0, cue=g0['cue'], label='G0>G1 d10')
        add(kind='train', group=0, interval=20.0, cue=g0['cue'], label='G0 train I20')
    sp = SPACING[part]
    for k, e in enumerate(ev):
        t = T0 + k * sp; e['t'] = t; cues = cue_times(t, e['cue'])
        if e['kind'] == 'pair': cues += cue_times(t + e['delta'], groups[e['second']]['cue'])
        if e['kind'] == 'train': cues = [(tt + j * e['interval'], c) for j in range(TRAIN_N) for tt, c in cue_times(t, e['cue'])]
        e['cues'] = cues
    return ev, T0 + len(ev) * sp

def read_conn(sim):
    conn = sim.GetConnectome(Pause_s=0.1); out = {1: {}, 2: {}, 3: {}}
    for p in range(len(conn['ConnectionTargets'])):
        for i, q in enumerate(conn['ConnectionTargets'][p]):
            t = int(conn['ConnectionTypes'][p][i]); out.setdefault(t, {})[(p, int(q))] = (float(conn['ConnectionWeights'][p][i]), float(conn['ConnectionGPeakSum'][p][i]))
    return out

def batch(sim, sel, nt):
    for s in range(0, len(sel), 500):
        ch = sel[s:s + 500]
        r = sim.BatchSetPrePostStrength([x[0] for x in ch], [x[1] for x in ch], [float(x[2]) for x in ch], Neurotransmitter=nt)
        assert r.get('StatusCode', 1) == 0, (nt, r)

def pair_class(a, b, groups):
    if b >= NP: return 'pyr_int'
    for g in groups:
        if a in g['cue'] and b in g['noncue']: return 'cue_noncue'
        if a in g['noncue'] and b in g['members']: return 'loop'
    return 'background'

def program(sim, plist, r, f, groups):
    rep = {}
    ra = L.apply_pairs(sim, plist); assert ra['n_readback_mismatch'] == 0, ra
    rep['ampa'] = {k: v for k, v in ra.items() if k != 'mismatches'}
    c0 = read_conn(sim)
    sel = [(a, b, r * cond) for a, b, cond, g in plist if (a, b) in c0[3] and cond > 0] if r > 0 else []
    if sel: batch(sim, sel, 'NMDA')
    gsel = [(p, q, f * 0.2 * g) for (p, q), (w, g) in c0[2].items()]
    batch(sim, gsel, 'GABA')
    c1 = read_conn(sim)
    pl = {(a, b): cond for a, b, cond, g in plist}
    badA = [k for k, cond in pl.items() if abs(min(1.0, c1[1][k][0]) * c1[1][k][1] - cond) > 1e-3 * max(1.0, cond)]
    want = {(a, b): w for a, b, w in sel}
    badN = []; capped = 0; nmda_other = 0; cls = {}
    for k, (w, g) in c1[3].items():
        eff = min(1.0, w) * g
        if k in pl:
            exp = min(want.get(k, 0.0), g)
            if want.get(k, 0.0) > g * (1 + 1e-6): capped += 1
            if abs(eff - exp) > 1e-3 * max(1.0, exp): badN.append(k)
            cl = pair_class(k[0], k[1], groups); s = cls.setdefault(cl, [0.0, 0.0, 0]); s[0] += pl[k]; s[1] += eff; s[2] += 1
        elif eff > 0: nmda_other += 1
    badG = [k for k, (w, g) in c1[2].items() if abs(w * g - f * 0.2 * g) > 1e-4 * max(1.0, g)]
    rep.update(nmda_set=len(sel), nmda_capped=capped, nmda_nonzero_unprogrammed=nmda_other, ampa_mismatch=len(badA), nmda_mismatch=len(badN), gaba_pairs=len(gsel), gaba_mismatch=len(badG),
               achieved_r={cl: dict(ampa_nS=round(s[0], 3), nmda_nS=round(s[1], 3), r=round(s[1] / s[0], 4) if s[0] > 0 else None, n_pairs=s[2]) for cl, s in cls.items()},
               gaba_weights=sorted(set(round(w, 4) for w, g in c1[2].values())))
    assert not badA and not badN and not badG, (badA[:3], badN[:3], badG[:3])
    eff = {}
    for t_, d in c1.items():
        for (p, q), (w, g) in d.items():
            e_ = min(1.0, w) * g
            if e_ > 0: eff['%d,%d,%d' % (p, q, t_)] = [round(w, 6), round(g, 5)]   # [weight, g_peak_sum]
    return rep, eff

def main():
    part, seed, c, r, f = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    tag = '%s_s%d_c%g_r%g_f%g' % (part, seed, c, r, f)
    assert part in SPACING and f in (0, 1, 2, 5) and r in (0, 0.56, 1.0)
    t_start = time.time()
    key = 's%d' % seed; D, _ = O.load(key); assert D.N == N
    groups = groups_for(part, seed)
    plist = O.pair_list_ov(D, [(g['members'], g['cue']) for g in groups], c)
    ev, run_ms = schedule(part, groups)
    cues = sorted((float(t), int(cc)) for e in ev for t, cc in e['cues'])
    client = connect()
    cf = NES.Simulation.Configuration(); cf.Name = 'nge-' + tag; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0; print('sim', sid, tag, flush=True)
    out = dict(tag=tag, part=part, seed=seed, c=c, r=r, f=f, model=O.MODELS[key]['model'], groups=groups, events=ev, run_ms=run_ms, sim_id=sid, dt_ms=0.1)
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
        sim.ModelLoad(O.MODELS[key]['model'])
        n = len(sim.GetSomaPositions().get('SomaCenters', [])); assert n == N, n
        c_load = read_conn(sim)
        out['load'] = dict(n_neurons=n, weights_on_load={str(t): sorted(set(round(w, 3) for w, g in d.values())) for t, d in c_load.items()},
                           pairs_missing=sum(1 for a, b, cond, g in plist if (a, b) not in c_load[1]))
        assert out['load']['pairs_missing'] == 0
        rep, eff = program(sim, plist, r, f, groups); out['program'] = rep
        print('program', json.dumps(rep), flush=True)
        if part == 'F': out['eff_cond'] = eff
        sim.SetSTDP(_DoSTDP=False)
        rr = sim.SetSpecificAPTimes(cues); assert rr.get('StatusCode', 1) == 0, rr
        sim.RecordAll(-1 if part == 'F' else 1.0)
        sim.RunAndWait(Runtime_ms=float(run_ms), Dt_ms=0.1, timeout_s=7200.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
        out['spikes'] = {int(k): [float(x) for x in v['tSpike_ms']] for k, v in sp.items() if v['tSpike_ms']}
        if part == 'F':
            rec = sim.GetRecording()['Recording']
            tt = np.array(rec['t_ms'], np.float32); vm = np.array([rec['neurons'][str(i)]['Vm_mV'] if str(i) in rec['neurons'] else rec['neurons'][i]['Vm_mV'] for i in range(N)], np.float32)
            np.savez_compressed(HERE + 'vm_%s.npz' % tag, t=tt, vm=vm)
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    out['wall_s'] = time.time() - t_start
    json.dump(out, open(HERE + 'raw_%s.json' % tag, 'w'), separators=(',', ':'), default=float)
    print('done', tag, 'wall', round(out['wall_s']), 'spikes', sum(len(v) for v in out['spikes'].values()), flush=True)

if __name__ == '__main__': main()
