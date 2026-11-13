"""Bio-limit audit: (1) growth parameters of v2-arbor-A via bio_check.assert_hard_limits; (2) every programmed weight per variant."""
import sys, json
sys.path.insert(0, '/home/johnjose/cos/netmorph_work/recipe_v2/ripple_arborA'); sys.path.insert(0, '/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim')
import pandas as pd, bio_check
from alib import *
F = ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']
df = pd.DataFrame([dict(zip(F, map(float, [25, 96, 48, 10, 120, 30, 0.9])))])  # arbor A row of grow_v3.py CFG (s.xlsx cannot be read here: no openpyxl)
out = dict(growth_row=df.iloc[0].to_dict())
try: bio_check.assert_hard_limits(df); out['growth_hard_limits'] = 'pass'
except Exception as e: out['growth_hard_limits'] = 'FAIL: %s' % e
res = bio_check.check_frame(df); out['growth_warnings'] = {c: bool(res[c].iloc[0]) for c in res.columns if c.startswith('warn') or c.startswith('bio_')}
groups = groups_from(OUT + 'design_K4.json')
out['weights'] = {}
for v in ['E1', 'NI']:
    ref, plist = build(groups, v)
    w = np.array([c / g for a, b, c, g in plist]); pre = np.array([a for a, b, c, g in plist]); post = np.array([b for a, b, c, g in plist])
    kinds = {'Pyr->Pyr': (post < NP), 'Pyr->Int': (post >= NP)}
    d = {}
    for k, m in kinds.items():
        x = w[m]
        d[k] = dict(n_programmed=int(m.sum()), n_zero=int((x == 0).sum()), n_in_0_to_0p1=int(((x > 0) & (x < 0.1 - 1e-9)).sum()), n_in_0p1_to_1=int(((x >= 0.1 - 1e-9) & (x <= 1 + 1e-9)).sum()),
                    n_above_1=int((x > 1 + 1e-9).sum()), min_nonzero=float(x[x > 0].min()) if (x > 0).any() else None, max=float(x.max()))
    d['all_in_0_1'] = bool(w.min() >= 0 and w.max() <= 1 + 1e-9)
    out['weights'][v] = d
    unprog = dict(note='not programmable via API: Int->Pyr / Int->Int GABA stay at as-grown weight 0.2; NMDA on programmed Pyr->Pyr zeroed by the API; unprogrammed pairs (Int->*, not listed) keep as-grown 0.2')
    out['weights'][v]['unprogrammed'] = unprog
json.dump(out, open(OUT + 'bio_audit.json', 'w'), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
