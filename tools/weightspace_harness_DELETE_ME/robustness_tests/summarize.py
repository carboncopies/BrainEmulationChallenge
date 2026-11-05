"""summarize.py: output/robust.json -> markdown table (mean over seeds; fall s per seed)."""
import json, sys
import numpy as np
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else 'output/robust.json'))
conds = []
for r in d['results']:
    if r['cond'] not in conds: conds.append(r['cond'])
print('| condition | ctrl | upr | th1 deg | th2 deg | rmsF N | peak F N | drift m | fall s (seeds 0/1/2) |')
print('|---|---|---|---|---|---|---|---|---|')
for c in conds:
    for k in ('spiking', 'lqr'):
        rs = sorted([r for r in d['results'] if r['cond'] == c and r['kind'] == k], key=lambda r: r['seed'])
        if not rs: continue
        g = lambda key: np.mean([r['m'][key] for r in rs])
        fall = '/'.join('-' if r['m']['fall_time_s'] is None else '%.2f' % r['m']['fall_time_s'] for r in rs)
        print('| %s | %s | %.3f | %.2f | %.2f | %.2f | %.1f | %.2f | %s |' % (c, k, g('upright_frac'),
              g('rms_th1_deg'), g('rms_th2_deg'), g('rms_force_N'), g('max_abs_force_N'), g('max_cart_drift_m'), fall))
