"""queue2.csv: ML round 2 (ml_round2.csv) interleaved with M6..M10 (fixed by the analyst), seed 20240628. Also mech_round2.csv."""
import pandas as pd
from h2h_common import *
mech = [('M6', 70, 30, 113, 50, 1.0, 10), ('M7', 70, 30, 113, 50, 1.0, 15), ('M8', 70, 30, 127, 40, 1.0, 12), ('M9', 70, 30, 120, 45, 1.0, 12), ('M10', 70, 30, 113, 50, 0.9, 12)]
M = pd.DataFrame([dict(config_id=n, days=25, pyramidal=p, interneuron=i, minneuronseparation=ms, **{'shape.radius': r, 'shape.thickness': t, 'dm.weight': w}) for n, p, i, r, t, w, ms in mech])
assert_limits(M); M['soft_clean'] = soft_clean(M); M['density'] = density(M).round(0); M['pyr_frac'] = pyrfrac(M).round(3)
print(M.to_string()); M.to_csv(H2H + '/mech_round2.csv', index=False)
assert M['soft_clean'].all(), 'a mechanistic config is not soft-clean'
L = pd.read_csv(H2H + '/ml_round2.csv')
rows = []
for k in range(5):
    for arm, src, pre in [('ML', L, 'T-ML-R2-'), ('MECH', M, 'T-MECH-R2-')]:
        r = src.iloc[k]; d = {'run_id': pre + (str(k + 1) if arm == 'ML' else r['config_id']), 'arm': arm, 'config_id': r['config_id']}
        for f in F: d[f] = r[f]
        d['netmorph_seed'] = SEED_TRAIN; rows.append(d)
Q = pd.DataFrame(rows); 
for f in F:
    if f != 'dm.weight': Q[f] = Q[f].astype(int)
assert_limits(Q); Q['pred_wall_s'] = pred_wall(Q).round(0)
Q.drop(columns='pred_wall_s').to_csv(H2H + '/queue2.csv', index=False); print(Q.to_string()); print('total predicted wall (s): %.0f = %.2f h' % (Q.pred_wall_s.sum(), Q.pred_wall_s.sum() / 3600))
