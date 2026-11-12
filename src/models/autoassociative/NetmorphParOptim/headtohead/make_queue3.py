"""queue3.csv: 18 nomination runs (ML-NOM-1..3 from ml_nominate.csv; mech M1,M7,M9 fixed by the analyst) x seeds 3001-3003, interleaved,
then 24 held-out runs (12 configs at seed 2001, then at 2002; arm HELD). Also nominations.csv (6 configs)."""
import pandas as pd
from h2h_common import *
L = pd.read_csv(H2H + '/ml_nominate.csv')[['config_id'] + F]
R = pd.concat([pd.read_csv(H2H + '/mech_round1.csv'), pd.read_csv(H2H + '/mech_round2.csv')])
Mn = R[R.config_id.isin(['M1', 'M7', 'M9'])].drop_duplicates('config_id').set_index('config_id').loc[['M1', 'M7', 'M9']].reset_index()[['config_id'] + F]
for d in (L, Mn):
    assert_limits(d); assert soft_clean(d).all(), 'nominee not soft-clean'
noms = pd.concat([L.assign(arm='ML'), Mn.assign(arm='MECH')], ignore_index=True)
noms['run_id'] = ['nom-%s' % c for c in noms.config_id]
noms.to_csv(H2H + '/nominations.csv', index=False)
rows = []
for s in SEEDS_NOM:
    for k in range(3):
        for arm, src in [('ML', L), ('MECH', Mn)]:
            r = src.iloc[k]; d = {'run_id': 'N-%s-%s-s%d' % (arm, r['config_id'], s), 'arm': arm, 'config_id': r['config_id']}
            d.update({f: r[f] for f in F}); d['netmorph_seed'] = s; rows.append(d)
H = pd.read_csv(H2H + '/heldout_configs.csv')
for s in SEEDS_HELD:
    for _, r in H.iterrows():
        d = {'run_id': 'H-%s-s%d' % (r['config_id'], s), 'arm': 'HELD', 'config_id': r['config_id']}
        d.update({f: r[f] for f in F}); d['netmorph_seed'] = s; rows.append(d)
Q = pd.DataFrame(rows)
for f in F:
    if f != 'dm.weight': Q[f] = Q[f].astype(int)
assert_limits(Q); assert Q.run_id.is_unique and len(Q) == 42
Q.to_csv(H2H + '/queue3.csv', index=False)
pw = pred_wall(Q); print(Q.head(8).to_string()); print('n=%d total predicted wall %.0f s = %.2f h' % (len(Q), pw.sum(), pw.sum() / 3600))
print('noms %.0f s, heldout %.0f s' % (pw[:18].sum(), pw[18:].sum()))
