"""Framework check: original G0..G3 with the standard (unscaled) rule, order 0,1,2,3 at 16 ms, Dt 1 ms (previous result: G1 1/4). Sensitivity study, D_synmax 0.5, not bio-realistic."""
import sys, json
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_05')
from mech_lib import *
groups = groups_of('E2'); d = L.build_pairs(dump, groups)
ref = {k: v[0] for k, v in d.items()}; plist = [(a, b, v[1], v[0]) for (a, b), v in d.items()]
NES, client = L.connect()
ev = [(g, g * 16.0) for g in range(4)]
r, _ = run_case(NES, client, 'control_original_standard_sep16', groups, ref, plist, ev, dt=1.0, nes_name='ctl-')
a = analyse(ev, r['spikes'], groups)
print([(m['group'], m['n_noncue_fired_10ms']) for m in a['memories']], 'mismatch', r['readback']['n_mismatch'], 'end', a['last_any_spike_ms'])
json.dump(dict(events=ev, spikes={str(k): v for k, v in r['spikes'].items() if v}, analysis=a, readback=r['readback']), open(D + 'raw_mech_control.json', 'w'))
