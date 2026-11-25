#!/usr/bin/env python3
"""partial_cue addendum B runner (PREREGISTRATION_B.md + DEVIATIONS B1). usage: run_pl.py SEED ARM R F ; ARM in L0 LH LI. PATCHED instance only."""
import sys, json, time, zlib, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/fresh_learn')
import run_exp as X, fllib as FL
O, NES = X.O, X.NES
NP = 96; N = 116; SP = 3000.0; T0 = 20.0; CAP = 6.86

def cue_times_lin(t, cells):
    cells = sorted(cells); m = len(cells)
    return [(t + (1.5 * i / (m - 1) if m > 1 else 0.0), c) for i, c in enumerate(cells)]

def make_events(A, key):
    rs = np.random.RandomState(zlib.crc32(('pl-' + key).encode()) & 0x7fffffff); A = list(A); k = len(A)
    outside = [c for c in range(NP) if c not in set(A)]; ev = [dict(kind='full', cue=sorted(A))]
    for kind, size, n in (('p75', int(np.ceil(0.75 * k)), 6), ('p50', int(np.ceil(0.5 * k)), 6), ('p25', int(np.floor(0.25 * k)), 6), ('p1', 1, 4)):
        for _ in range(n): ev.append(dict(kind=kind, cue=sorted(int(x) for x in rs.choice(A, size=size, replace=False))))
    for _ in range(4): ev.append(dict(kind='unrel', cue=sorted(int(x) for x in rs.choice(outside, size=8, replace=False))))
    order = list(range(len(ev))); rs.shuffle(order)       # shuffled order so no cue size systematically follows the same predecessor
    ev = [ev[i] for i in order]
    for i, e in enumerate(ev): e['t'] = T0 + i * SP; e['cues'] = cue_times_lin(e['t'], e['cue']); e['label'] = '%s %d' % (e['kind'], i)
    return ev, T0 + len(ev) * SP

def arm_matrix(net, A, arm):
    Hm = 3.0 if arm == 'LH' else None
    Xm, info = FL.build_F(net, [A], Hm); return Xm, info

def plist_for(D, net, A, arm):
    Xm, info = arm_matrix(net, A, arm); G = net.G; out = []
    for a in range(NP):
        for b in range(NP):
            if a != b and G[a, b] > 0 and abs(Xm[a, b] - 0.2 * G[a, b]) > 1e-9: out.append((a, b, round(float(Xm[a, b]), 6), float(G[a, b])))
    if arm == 'LI':
        for a in range(NP):
            for b in range(NP, N):
                g = float(D.G[a, b])
                if g > 0: out.append((a, b, round(g, 6), g))
    return out, Xm, info

def main():
    seed, arm, r, f = int(sys.argv[1]), sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    assert arm in ('L0', 'LH', 'LI') and r in (0.56, 1.0) and f in (1, 2)
    tag = 's%d_%s_r%g_f%g' % (seed, arm, r, f); t_start = time.time(); key = 's%d' % seed
    D, _ = O.load(key); assert D.N == N; net = FL.Net(key); al = json.load(open(HERE + 'alloc_b.json'))[key]; A = al['A17']
    plist, Xm, info = plist_for(D, net, A, arm)
    assert max(c for a, b, c, g in plist if b < NP) <= CAP + 1e-6 and all(c <= g * (1 + 1e-5) + 1e-6 for a, b, c, g in plist)
    ins = (Xm).sum(0)    # total Pyr->Pyr input per cell in the arm (programmed + 0.2G unprogrammed, as built)
    flags = dict(n_programmed=len(plist), max_pair=max(c for a, b, c, g in plist if b < NP), pairs_over_cap=0, member_input_nS={str(m): round(float(ins[m]), 2) for m in A},
                 members_over_3T=int(sum(ins[m] > 49.5 + 1e-6 for m in A)), max_member_input=round(float(max(ins[m] for m in A)), 2),
                 cells_over_3T_all=int(sum(ins[c] > 49.5 + 1e-6 for c in range(NP))), hubs=[int(h) for h in info.get('hubs', [])])
    ev, run_ms = make_events(A, key); cues = sorted((float(t), int(cc)) for e in ev for t, cc in e['cues'])
    groups = [dict(members=sorted(A), cue=[], noncue=[])]
    client = X.connect(); cf = NES.Simulation.Configuration(); cf.Name = 'pl-' + tag; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0; print('sim', sid, tag, flush=True)
    out = dict(tag=tag, seed=seed, arm=arm, r=r, f=f, A=A, events=ev, run_ms=run_ms, sim_id=sid, flags=flags)
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
        sim.ModelLoad(O.MODELS[key]['model'])
        n = len(sim.GetSomaPositions().get('SomaCenters', [])); assert n == N, n
        c_load = X.read_conn(sim); assert sum(1 for a, b, cond, g in plist if (a, b) not in c_load[1]) == 0
        rep, eff = X.program(sim, plist, r, float(f), groups); out['program'] = rep; print('program', json.dumps(rep)[:500], flush=True)
        sim.SetSTDP(_DoSTDP=False)
        rr = sim.SetSpecificAPTimes(cues); assert rr.get('StatusCode', 1) == 0, rr
        sim.RecordAll(1.0); sim.RunAndWait(Runtime_ms=float(run_ms), Dt_ms=0.1, timeout_s=14400.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']; out['spikes'] = {int(k): [float(x) for x in v['tSpike_ms']] for k, v in sp.items() if v['tSpike_ms']}
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    out['wall_s'] = time.time() - t_start
    json.dump(out, open(HERE + 'rawB_%s.json' % tag, 'w'), separators=(',', ':'), default=float)
    print('done', tag, 'wall', round(out['wall_s']), 'spikes', sum(len(v) for v in out['spikes'].values()), flush=True)

if __name__ == '__main__': main()
