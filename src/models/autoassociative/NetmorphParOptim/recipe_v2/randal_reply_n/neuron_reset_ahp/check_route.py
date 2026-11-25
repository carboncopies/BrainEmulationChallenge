#!/usr/bin/env python3
"""Route control (PREREGISTRATION run 1, P0): raw_LH_s77777_N0_r1_f1.json vs stored partial_cue/rawB_s77777_LH_r1_f1.json.
Pass = same spiking cells, same spike count per cell, max |dt| <= 0.01 ms. Exit 1 on fail. Writes route_check.json."""
import json, sys, numpy as np
HERE = '/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/neuron_reset_ahp/'
a = json.load(open(HERE + 'raw_LH_s77777_N0_r1_f1.json'))['spikes']
b = json.load(open('/home/johnjose/cos/netmorph_work/recipe_v2/randal_reply_n/partial_cue/rawB_s77777_LH_r1_f1.json'))['spikes']
same_cells = set(a) == set(b); same_counts = same_cells and all(len(a[k]) == len(b[k]) for k in a)
dt = max((float(np.max(np.abs(np.array(a[k]) - np.array(b[k])))) for k in a if len(a[k])), default=0.0) if same_counts else None
res = dict(same_cells=same_cells, same_counts=same_counts, max_abs_dt_ms=dt, n_spikes_new=sum(map(len, a.values())), n_spikes_stored=sum(map(len, b.values())),
           passed=bool(same_counts and dt <= 0.01))
json.dump(res, open(HERE + 'route_check.json', 'w'), indent=1); print('route check', res); sys.exit(0 if res['passed'] else 1)
