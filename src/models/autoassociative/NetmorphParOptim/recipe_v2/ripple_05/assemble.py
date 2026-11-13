import json, sys
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05')
from ripple_lib import *
LABEL = 'sensitivity study, D_synmax 0.5, not bio-realistic'
m = json.load(open('raw_main.json')); x = json.load(open('raw_extra.json')); v = json.load(open('ripple_vm_full.json'))
pos = {str(n['id']): [n['x'], n['y'], n['z']] for n in dump.neurons}
typ = {str(n['id']): ('pyramidal' if n['soma_type'] == 1 else 'interneuron') for n in dump.neurons}
data = dict(label=LABEL, seed=20240628, model=S['model'], stdp=False, n_neurons=94, neuron_type=typ, soma_positions_um=pos,
            memory_groups=[dict(group=g, members=mm, cue=c, noncue=[a for a in mm if a not in c]) for g, (mm, c) in enumerate(GROUPS)],
            unused_fifth_group_not_programmed=dict(members=ALLG[4][0], cue=ALLG[4][1]),
            cue_spike_offsets_within_memory_ms=CUE_OFFS, time_zero='first cue spike; spikes in ms relative to it; run 150 ms at Dt 1 ms', cases={})
for src in (m, x):
    for k, c in src.items():
        d = dict(c); d['label'] = LABEL; d['spike_raster_time_ms_by_neuron'] = d.pop('spikes'); data['cases'][k] = d
# inhibition diagnostic: GABA from interneurons that fired in single-memory run of a onto memory b non-cue members
inhm = {}
for a in range(K):
    sp = m['single_G%d' % a]['spikes']; fired = [i for i in range(67, 94) if sp.get(str(i))]
    inhm['G%d_alone' % a] = dict(interneurons_fired=len(fired), spikes=sum(len(sp[str(i)]) for i in fired),
        mean_gaba_nS_onto_noncue_member_of={('G%d' % b): round(sum(float(dump.GA[i, n]) for i in fired for n in GROUPS[b][0] if n not in GROUPS[b][1]) / 4, 2) for b in range(K)})
data['inhibition_matrix'] = inhm
json.dump(data, open('ripple_data.json', 'w'), separators=(',', ':'))
vm = dict(label=LABEL, note='Vm in mV rounded to 0.1; spike samples are clamped at +30 mV; no subsampling; window -5..110 ms around first cue (cue at t=0)', **{k: v[k] for k in ('window_ms', 'cue_offsets_ms', 'neurons', 'interneuron_selection', 'bystander_selection', 'cases')})
json.dump(vm, open('ripple_vm.json', 'w'), separators=(',', ':'))
print(inhm)
# summaries
def burst(a, ev, sp):
    out = []
    for mm in a['memories']:
        gi = mm['group']; on = mm['cue_onset_ms']; later = sorted(o for _, o in ev if o > on); we = later[0] if later else 150
        xs = [t for n in GROUPS[gi][0] for t in sp.get(str(n), []) if on <= t < we]
        out.append(round(max(xs) - on, 1) if xs else None)
    return out
rows = {}
for src in (m, x):
    for k, c in src.items():
        a = c['analysis']; ev = c['events']
        print(k, '| complete', [(mm['group'], mm['n_noncue_fired_10ms'], round(mm['latency_last_noncue_ms'], 1) if mm['latency_last_noncue_ms'] else None) for mm in a['memories']], '| xtalk', len(a['crosstalk_events']), '| spurNonMem', a['spurious_nonmember_pyr_spikes'], a['spurious_nonmember_pyr_cells'], '| memspk>10ms', a['member_spikes_outside_own_10ms_window'], '| burstdur', burst(a, ev, c['spikes']), '| intspk', [i['int_spikes'] for i in a['interneuron_per_event']], '| last', a['last_any_spike_ms'], '| tot', a['total_pyr_spikes'], a['total_interneuron_spikes'], '| ok', a['ripple_success'])
# dt0.1 analysis
for case in v['cases']:
    c = v['cases'][case]
    for dt in ('dt0.1', 'dt1'):
        sp = {int(k): s for k, s in c[dt]['spikes_all_neurons'].items()}
        a = analyse(c['events'], sp)
        print(case, dt, [(mm['group'], mm['n_noncue_fired_10ms']) for mm in a['memories']], 'ints', [i['int_spikes'] for i in a['interneuron_per_event']], 'last', a['last_any_spike_ms'], a['ripple_success'])
