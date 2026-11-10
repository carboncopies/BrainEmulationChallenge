#!/usr/bin/env python3
"""Score the real NES run (server_apply output) with the same metrics as the surrogate."""
import json, sys, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reservoir import Reservoir, AMPA, NMDA
d = json.load(open(sys.argv[1])); res = json.load(open(os.path.join(HERE, 'results.json')))
ops = json.load(open(sys.argv[2]))['ops']
K = sys.argv[3] if len(sys.argv) > 3 else '2'
r = Reservoir(res['dump'])
st = d['spike_times']['SpikeTimes']
# SpikeTimes: list per neuron (index = neuron ID) or dict
if isinstance(st, dict):
    sp = {int(k): list(v['tSpike_ms'] if isinstance(v, dict) else v) for k, v in st.items()}
else:
    sp = {i: list(v) for i, v in enumerate(st)}
des = res['engram_design']['K'][K]['patterns']
cue_steps = [s for s in d['steps'] if s['step'] == 'SetSpecificAPTimes'][0]['pairs']
cue_t = sorted(set(p[0] for p in cue_steps))
allmem = set(c for p in des for c in p['group_ids'])
out = {'per_pattern': [], 'total_spikes_all': int(sum(len(v) for v in sp.values()))}
for k, p in enumerate(des):
    t0 = cue_t[k]; win = (t0 + 0.5, t0 + 20.0); G = p['group_ids']; C = p['cue_ids']
    hit = lambda ids, w: [i for i in ids if any(w[0] <= t <= w[1] for t in sp.get(i, []))]
    noncue = [i for i in G if i not in C]
    nonmem = [int(i) for i in r.pyr if int(i) not in allmem]
    others = [i for kk, q in enumerate(des) if kk != k for i in q['group_ids']]
    comp = hit(noncue, win)
    seg = (t0, t0 + (cue_t[1] - cue_t[0] if len(cue_t) > 1 else 200.0))
    per_member = {int(i): len([t for t in sp.get(i, []) if seg[0] <= t < seg[1]]) for i in G}
    out['per_pattern'].append({'pattern': k, 'cue_t_ms': t0, 'group': G, 'cue': C,
        'completion': round(len(comp) / len(noncue), 3), 'completed_members': comp,
        'latency_ms': [round(min(t for t in sp[i] if t >= win[0]) - t0, 2) for i in comp],
        'spurious_frac': round(len(hit(nonmem, win)) / len(nonmem), 3), 'n_spurious': len(hit(nonmem, win)),
        'cross_pattern_frac': round(len(hit(others, win)) / len(others), 3),
        'interneurons_firing_in_window': len(hit([int(i) for i in r.int], win)),
        'spikes_per_member_in_200ms_segment': per_member,
        'members_firing_after_50ms': len(hit(G, (t0 + 50, seg[1]))),
        'member_spike_times_first_member': sp.get(noncue[0], [])[:12]})
# weights verification
wa = d['weights_after']; bad = 0; nmda_zero = 0; nmda_total = 0
for o in ops:
    w = wa.get('%d,%d,1' % (o['pre'], o['post']))
    if w is None or abs(w - o['weight']) > 2e-3: bad += 1
    wn = wa.get('%d,%d,3' % (o['pre'], o['post']))
    if wn is not None:
        nmda_total += 1; nmda_zero += (wn == 0.0)
untouched = [v for k, v in wa.items() if k.endswith(',2')]
out['weights_check'] = {'ops': len(ops), 'ampa_weight_mismatches': bad, 'nmda_entries_on_programmed_pairs': nmda_total,
                        'nmda_zeroed': nmda_zero, 'gaba_weights_unique': sorted(set(round(v, 3) for v in untouched))}
out['interneuron_spikes_total'] = int(sum(len(sp.get(int(i), [])) for i in r.int))
out['pyr_spikes_total'] = int(sum(len(sp.get(int(i), [])) for i in r.pyr))
json.dump(out, open(os.path.join(HERE, 'server_score_%s.json' % os.path.basename(sys.argv[1])[13:-5]), 'w'), indent=1)
print(json.dumps(out, indent=1)[:6000])
