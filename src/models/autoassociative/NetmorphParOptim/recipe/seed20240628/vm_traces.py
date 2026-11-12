#!/usr/bin/env python3
"""Record soma Vm (NES RecordAll + GetRecording) for G0/G1 recall cases on seed 20240628; writes vm_traces.json.
Each case runs in a NEW simulation (fresh copy of the pristine model + weights.json), Vm is read, then the sim is deleted
with DeleteResidentByID. usage: vm_traces.py [--dt 1.0]"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE + '/..')
import numpy as np
import recipelib as L
DT = float(sys.argv[sys.argv.index('--dt') + 1]) if '--dt' in sys.argv else 1.0
OUTNAME = 'vm_traces.json' if DT == 1.0 else 'vm_traces_dt%g.json' % DT
S = L.SEEDS[20240628]; dump = L.Dump(S['dump'])
wj = json.load(open(HERE + '/weights.json')); ej = json.load(open(HERE + '/engrams.json'))
groups = [(g['members'], g['cue']) for g in ej['groups']]
cond = {(p[0], p[1]): p[3] for p in wj['pairs']}          # programmed conductance nS
ref = {(p[0], p[1]): p[2] for p in wj['pairs']}
ingrp = set(ej['pyramidal_ids']) - set(ej['ungrouped_pyramidal'])
def chosen_interneurons(gi, n=6):
    mem = groups[gi][0]; rows = []
    for i in dump.its:
        drive = sum(cond.get((m, i), 0.0) for m in mem)
        back = [m for m in mem if dump.GA[i, m] > 0]
        if drive > 0 and back: rows.append((drive, i, back))
    rows.sort(reverse=True)
    return [dict(id=i, drive_from_members_nS=round(d, 2), projects_back_to=b, gaba_g_to_members_nS={str(m): round(float(dump.GA[i, m]), 2) for m in b}) for d, i, b in rows[:n]]
def bystanders(gi, n=2):
    mem = groups[gi][0]; ung = ej['ungrouped_pyramidal']
    sc = sorted(((sum(float(dump.G[m, u]) for m in mem), u) for u in ung), reverse=True)
    return [dict(id=u, asgrown_input_from_members_nS=round(s, 2)) for s, u in sc[:n]]
INT = {g: chosen_interneurons(g) for g in range(2)}; BY = {g: bystanders(g) for g in range(2)}
print('G0 interneurons', INT[0]); print('G0 bystanders', BY[0]); print('G1 interneurons', INT[1]); print('G1 bystanders', BY[1])
cases = [dict(name='a_G0_full_4cell_recall', g=0, cue=groups[0][1], program=True),
         dict(name='b_G0_3cell_no_recall', g=0, cue=groups[0][1][:3], program=True),
         dict(name='c_G0_control_no_pruning_runaway', g=0, cue=groups[0][1], program=False),
         dict(name='d_G1_full_4cell_recall', g=1, cue=groups[1][1], program=True)]
NES, client = L.connect(); out = dict(seed=20240628, model=S['model'], dt_ms=DT, window_ms=[-5, 40], cue_time_in_sim_ms=20.0, cases={}, interneuron_selection={}, bystander_selection={})
out['interneuron_selection'] = {'G%d' % g: INT[g] for g in INT}; out['bystander_selection'] = {'G%d' % g: BY[g] for g in BY}
T0 = 20.0; RUN = 70.0; first = True; params = None
for c in cases:
    if not first: time.sleep(30)
    first = False
    print('mem GB %.1f' % L.guard_memory(), c['name'], flush=True)
    sim, load = L.fresh_copy(NES, client, S['model'], 'recipe-vm-' + c['name'], ref); assert load['loaded_ok']
    try:
        if c['program']:
            rep = L.apply_pairs(sim, [(p[0], p[1], p[3], p[2]) for p in wj['pairs']]); assert rep['n_readback_mismatch'] == 0
        sim.SetSTDP(_DoSTDP=False)
        r = sim.SetSpecificAPTimes([(T0, int(x)) for x in c['cue']]); assert r.get('StatusCode', 1) == 0
        sim.RecordAll(-1)
        sim.RunAndWait(Runtime_ms=RUN, Dt_ms=DT, timeout_s=300.0)
        rec = sim.GetRecording(); sp = sim.GetSpikeTimes()['SpikeTimes']
    finally:
        try: d = sim.DeleteResidentByID(); print('deleted sim', sim.ID, d)
        except Exception as e: print('DELETE FAILED', sim.ID, e)
    R = rec['Recording']
    if params is None:
        e0 = R['neurons']['0']; print('recording format: neuron entry', type(e0), (list(e0.keys()) if isinstance(e0, dict) else len(e0)), 't_ms n=%d first=%s last=%s' % (len(R['t_ms']), R['t_ms'][:3], R['t_ms'][-2:]), flush=True)
    g = c['g']; mem, cue = groups[g]; nc = [m for m in mem if m not in cue]
    roles = [(m, 'pyramidal', 'cue' if m in cue else 'non-cue member') for m in mem] + [(i['id'], 'interneuron', 'interneuron') for i in INT[g]] + [(b['id'], 'pyramidal', 'bystander') for b in BY[g]]
    neurons = []
    for nid, typ, role in roles:
        e = R['neurons'][str(nid)]
        vm = e['Vm_mV'] if isinstance(e, dict) else e; tt = R['t_ms']
        assert len(vm) == len(tt), (len(vm), len(tt))
        t = np.array(tt, float) - T0; v = np.array(vm, float); m = (t >= -5) & (t <= 40)
        spk = [round(x - T0, 3) for x in sp.get(str(nid), {}).get('tSpike_ms', []) if -5 <= x - T0 <= 40]
        neurons.append(dict(id=nid, type=typ, role=role, times_ms=[round(float(x), 3) for x in t[m]], vm_mV=[round(float(x), 1) for x in v[m]], spike_times_ms=spk,
                            peak_vm_mV_excluding_spike_samples=None))
    out['cases'][c['name']] = dict(group=g, cue_cells=c['cue'], programmed=c['program'], neurons=neurons,
                                   all_spikes_first40ms={str(k): [round(x - T0, 3) for x in v['tSpike_ms'] if -5 <= x - T0 <= 40] for k, v in sp.items() if any(-5 <= x - T0 <= 40 for x in v['tSpike_ms'])})
    print(c['name'], 'recorded neurons', len(R['neurons']), 'samples', len(neurons[0]['times_ms']), flush=True)
json.dump(out, open(HERE + '/' + OUTNAME, 'w'), separators=(',', ':'))
print('wrote', OUTNAME, os.path.getsize(HERE + '/' + OUTNAME))
