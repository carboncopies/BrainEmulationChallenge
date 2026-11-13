import json, sys, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05')
import ripple_lib as R
from ripple_lib import *
NES, client = L.connect()
D = '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05/'
cases = [('diag_sep16_simultaneous_cues', [(g, g * 16) for g in range(K)], [0, 0, 0, 0]),
         ('diag_sep16_order_1_0_2_3', [(g, i * 16) for i, g in enumerate([1, 0, 2, 3])], CUE_OFFS),
         ('diag_two_memory_G0_then_G1_at_32', [(0, 0), (1, 32)], CUE_OFFS),
         ('diag_two_memory_G0_then_G1_at_48', [(0, 0), (1, 48)], CUE_OFFS),
         ('diag_two_memory_G0_then_G1_at_16', [(0, 0), (1, 16)], CUE_OFFS)]
out = {}
for n, (name, ev, offs) in enumerate(cases):
    if n: time.sleep(30)
    R.CUE_OFFS[:] = offs
    r, _ = run_case(NES, client, name, ev, program=True, run_ms=150.0, dt=1.0)
    a = analyse(ev, r['spikes'])
    out[name] = dict(events=ev, cue_offsets_ms=list(offs), cues=r['cues'], spikes={str(k): v for k, v in r['spikes'].items()}, analysis=a)
    print(name, [(m['group'], m['n_noncue_fired_10ms'], m['latency_last_noncue_ms']) for m in a['memories']], a['ripple_success'], a['last_any_spike_ms'], flush=True)
    json.dump(out, open(D + 'raw_extra.json', 'w'))
