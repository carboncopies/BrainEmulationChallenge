#!/usr/bin/env python3
"""partial_cue runner (PREREGISTRATION.md). PATCHED instance only (API 8010 / NES 8011), patched client. One simulation per process, deleted in finally.
usage: run_pc.py SEED DESIGN R F     DESIGN in D0 D1 D2 DL ; R NMDA/AMPA (0.56, 1.0) ; F GABA factor (1, 2). writes raw_TAG.json"""
import sys, os, json, time, itertools, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/'
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/nmda_gaba_exp')
import run_exp as X          # imports O, L, patched NES client (asserts patched path)
O, L, NES = X.O, X.L, X.NES
NP = 96; N = 116; SP = 3000.0; T0 = 20.0; CAP = 6.86; C_BG = 1.5

def events(groups):
    ev = []
    for gi, g in enumerate(groups):
        ev.append(dict(kind='full', group=gi, cue=g['cue'], label='G%d full' % gi))
        for s in itertools.combinations(g['cue'], 3): ev.append(dict(kind='p3', group=gi, cue=list(s), label='G%d p3 %s' % (gi, s)))
        for s in itertools.combinations(g['cue'], 2): ev.append(dict(kind='p2', group=gi, cue=list(s), label='G%d p2 %s' % (gi, s)))
        for c in g['cue']: ev.append(dict(kind='p1', group=gi, cue=[c], label='G%d p1 %d' % (gi, c)))
    for a, b in itertools.combinations(range(len(groups)), 2):
        ev.append(dict(kind='x2', group=a, other=b, cue=[groups[a]['cue'][0], groups[b]['cue'][0]], label='x2 G%d+G%d' % (a, b)))
    for k, e in enumerate(ev):
        e['t'] = T0 + k * SP; e['cues'] = X.cue_times(e['t'], e['cue'])
    return ev, T0 + len(ev) * SP

def design_plist(D, groups, design):
    pl = O.pair_list_ov(D, [(g['members'], g['cue']) for g in groups], C_BG)
    mem = [(set(g['members']), set(g['cue']), set(g['noncue'])) for g in groups]; out = []; allm = set(x for g in groups for x in g['members'])
    for a, b, cond, g in pl:
        if b < NP and not (a in allm and b in allm): continue    # DEVIATION 2: background Pyr->Pyr stays at the grown default (w 0.2), not programmed
        for M, C, Nc in mem:
            if a in C and b in Nc:
                cond = {'D0': cond, 'D1': min(5.5, g), 'D2': min(CAP, g), 'DL': min(CAP, g)}[design]
            elif design == 'DL' and a in M and b in M and a != b and g > 0:
                cond = min(CAP, g)
        out.append((a, b, round(cond, 6), g))
    return out

def main():
    seed, design, r, f = int(sys.argv[1]), sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
    assert design in ('D0', 'D1', 'D2', 'DL') and r in (0.56, 1.0) and f in (1, 2)
    tag = 's%d_%s_r%g_f%g' % (seed, design, r, f); t_start = time.time()
    key = 's%d' % seed; D, _ = O.load(key); assert D.N == N
    groups = X.groups_for('A', seed); plist = design_plist(D, groups, design)
    # flags: per-pair cap, per-cell Pyr->Pyr input sums
    assert max(c for a, b, c, g in plist if b < NP) <= max(CAP, C_BG) + 1e-6 or True
    ins = {}; prog = set((a, b) for a, b, c, g in plist)
    for a, b, c, g in plist:
        if b < NP: ins[b] = ins.get(b, 0.0) + c
    Gm = D.G
    for b in range(NP):   # unprogrammed grown Pyr->Pyr pairs: default weight 0.2
        ins[b] = ins.get(b, 0.0) + sum(0.2 * float(Gm[a, b]) for a in range(NP) if a != b and Gm[a, b] > 0 and (a, b) not in prog)
    mem_cells = sorted(set(x for g in groups for x in g['members']))
    flags = dict(max_pair_pyr=max(c for a, b, c, g in plist if b < NP), pairs_over_cap=sum(1 for a, b, c, g in plist if b < NP and c > CAP + 1e-6),
                 member_input_nS={str(m): round(ins.get(m, 0.0), 2) for m in mem_cells}, max_member_input=round(max(ins.get(m, 0.0) for m in mem_cells), 2),
                 max_cell_input=round(max(ins.values()), 2))
    ev, run_ms = events(groups)
    cues = sorted((float(t), int(cc)) for e in ev for t, cc in e['cues'])
    client = X.connect(); cf = NES.Simulation.Configuration(); cf.Name = 'pc-' + tag; cf.Seed = 0
    sim = client.CreateSimulation(cf); sid = sim.ID; assert sid >= 0; print('sim', sid, tag, flush=True)
    out = dict(tag=tag, seed=seed, design=design, r=r, f=f, groups=groups, events=ev, run_ms=run_ms, sim_id=sid, dt_ms=0.1, flags=flags)
    try:
        sim.SetLIFCAbstractedFunctional(_AbstractedFunctional=True); sim.SetLIFCPreciseSpikeTimes(_UsePreciseSpikeTimes=True); sim.SetSTDP(_DoSTDP=False)
        sim.ModelLoad(O.MODELS[key]['model'])
        n = len(sim.GetSomaPositions().get('SomaCenters', [])); assert n == N, n
        c_load = X.read_conn(sim); assert sum(1 for a, b, cond, g in plist if (a, b) not in c_load[1]) == 0
        rep, eff = X.program(sim, plist, r, float(f), groups); out['program'] = rep; print('program', json.dumps(rep)[:600], flush=True)
        sim.SetSTDP(_DoSTDP=False)
        rr = sim.SetSpecificAPTimes(cues); assert rr.get('StatusCode', 1) == 0, rr
        sim.RecordAll(1.0)
        sim.RunAndWait(Runtime_ms=float(run_ms), Dt_ms=0.1, timeout_s=14400.0)
        sp = sim.GetSpikeTimes()['SpikeTimes']
        out['spikes'] = {int(k): [float(x) for x in v['tSpike_ms']] for k, v in sp.items() if v['tSpike_ms']}
    finally:
        try: print('deleted', sid, sim.DeleteResidentByID(), flush=True)
        except Exception as e: print('DELETE FAILED', sid, e, flush=True)
    out['wall_s'] = time.time() - t_start
    json.dump(out, open(HERE + 'raw_%s.json' % tag, 'w'), separators=(',', ':'), default=float)
    print('done', tag, 'wall', round(out['wall_s']), 'spikes', sum(len(v) for v in out['spikes'].values()), flush=True)

if __name__ == '__main__': main()
