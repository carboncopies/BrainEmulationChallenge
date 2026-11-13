import json, sys, time
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05')
from ripple_lib import *
NES, client = L.connect()
cases = []
for sep in (12, 16, 20): cases.append(('ripple_sep%d' % sep, [(g, g * sep) for g in range(K)], True))
cases.append(('ripple_sep16_shuffled_2_0_3_1', [(g, i * 16) for i, g in enumerate([2, 0, 3, 1])], True))
for g in range(K): cases.append(('single_G%d' % g, [(g, 0.0)], True))
cases.append(('control_no_programming_sep16', [(g, g * 16) for g in range(K)], False))
out = {}; first = True
for name, ev, prog in cases:
    if not first: time.sleep(30)
    first = False
    r, _ = run_case(NES, client, name, ev, program=prog, run_ms=150.0, dt=1.0)
    a = analyse(ev, r['spikes'])
    out[name] = dict(events=ev, programmed=prog, cues=r['cues'], spikes={str(k): v for k, v in r['spikes'].items()}, analysis=a, load=r['load'])
    print(name, {k: a[k] for k in ('ripple_success', 'all_complete', 'crosstalk_events', 'last_any_spike_ms', 'spurious_nonmember_pyr_spikes', 'member_spikes_outside_own_10ms_window')}, [(m['group'], m['n_noncue_fired_10ms'], m['latency_last_noncue_ms']) for m in a['memories']], [i['int_spikes'] for i in a['interneuron_per_event']], flush=True)
    json.dump(out, open('/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05/raw_main.json', 'w'))
