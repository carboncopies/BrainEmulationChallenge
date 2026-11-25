#!/usr/bin/env python3
"""POST HOC (not preregistered): spikes of the CUE cells in [t, t+30) per 75% cue event (forced spike = 1), N0 vs reset AFTER arms.
Tests the explanation that reset AFTER (-55 mV) lifts a cell that was forced to fire from rest (TOVM would reset it to its pre-spike Vm ~ -70 mV)."""
import json, glob, numpy as np
for fn in sorted(glob.glob('rawB2_B2_E16*_r1_f1.json')) + ['raw_LH_s77777_N0_r1_f1.json', 'raw_LH_s77777_R_r1_f1.json', 'raw_LH_s66666_R_r1_f1.json']:
    d = json.load(open(fn)); sp = {int(k): np.array(v) for k, v in d['spikes'].items()}; per = []; lat = []
    for e in d['events']:
        if e['kind'] != 'p75': continue
        t = e['t']; per.append(np.mean([((sp.get(c, np.array([])) >= t) & (sp.get(c, np.array([])) < t + 30)).sum() for c in e['cue']]))
        sec = [x for c in e['cue'] for x in (sp.get(c, np.array([]))[(sp.get(c, np.array([])) >= t + 2.5) & (sp.get(c, np.array([])) < t + 30)] - t)]
        lat.append(min(sec) if sec else np.nan)
    print('%-38s cue-cell spikes in 30 ms per cell (median over 75%% events) %.2f; first non-forced cue-cell spike %s ms' % (fn.replace('rawB2_B2_', '').replace('.json', ''), np.median(per), '%.1f' % np.nanmedian(lat) if not np.all(np.isnan(lat)) else 'none'))
