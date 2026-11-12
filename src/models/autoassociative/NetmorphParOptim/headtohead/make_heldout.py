"""12 held-out configs: scrambled Sobol seed 777 in (hard limits ∩ size cap); first 8 'general', next 4 'corner'."""
import numpy as np, pandas as pd
from scipy.stats import qmc
from h2h_common import *
lo, hi = box()
u = qmc.Sobol(7, scramble=True, seed=777).random(12)   # first 12 points of the seed-777 stream
raw = lo + u * (hi - lo)
df = pd.DataFrame(raw, columns=F)
df['kind'] = ['general'] * 8 + ['corner'] * 4
iDM, iD = F.index('dm.weight'), F.index('days')
for k in range(8, 12):
    df.loc[k, 'dm.weight'] = [0.8, 0.9, 1.0][min(int(u[k, iDM] * 3), 2)]
    df.loc[k, 'days'] = [24, 25][min(int(u[k, iD] * 2), 1)]
kind = df.pop('kind'); df = round_cfg(df)
for f in F:
    if f != 'dm.weight': df[f] = df[f].astype(int)
assert_limits(df)
df.insert(0, 'config_id', ['H%02d' % (i + 1) for i in range(12)]); df['kind'] = kind
df['soft_clean'] = soft_clean(df); df['density'] = density(df).round(0); df['pyr_frac'] = pyrfrac(df).round(3)
df['pred_wall_s'] = pred_wall(df).round(0)
df.to_csv(H2H + '/heldout_configs.csv', index=False)
print(df.to_string())
