"""Shared definitions for the Track-1 head-to-head. Only pandas/numpy at import time (run_queue imports this too)."""
import glob, json, math, os, re, sys
import numpy as np, pandas as pd
H2H = os.path.dirname(os.path.abspath(__file__))
D = '/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim/'
sys.path.insert(0, D)
import bio_check
F = ['days', 'pyramidal', 'interneuron', 'minneuronseparation', 'shape.radius', 'shape.thickness', 'dm.weight']
SIZE_CAP = {'pyramidal': (16, 70), 'interneuron': (16, 30)}
COMP = ['raw_pyr_int_n', 'raw_int_pyr_n', 'raw_int_int_n', 'usable_conns2']
REF = {'raw_pyr_int_n': 42.0, 'raw_int_pyr_n': 97.25, 'raw_int_int_n': 18.25, 'usable_conns2': 460.0}
T1, T2 = 1.041, 1.534
SEED_TRAIN, SEEDS_HELD, SEEDS_NOM = 20240628, (2001, 2002), (3001, 3002, 3003)

def box():
    P = bio_check.load_ranges()['parameters']
    lo = np.array([P[f]['min'] for f in F], float); hi = np.array([P[f]['max'] for f in F], float)
    for f, (a, b) in SIZE_CAP.items():
        i = F.index(f); lo[i], hi[i] = max(lo[i], a), min(hi[i], b)
    return lo, hi
HARD_SPAN = np.array([(lambda P: P[f]['max'] - P[f]['min'])(bio_check.load_ranges()['parameters']) for f in F], float)

def round_cfg(df):
    df = df.copy()
    for f in F:
        df[f] = df[f].astype(float).round(1) if f == 'dm.weight' else df[f].astype(float).round(0)
    return df

def assert_limits(df):
    """hard limits (bio_check) AND size cap; raises on violation."""
    df = pd.DataFrame(df)[F].astype(float)
    bio_check.assert_hard_limits(df)
    for f, (a, b) in SIZE_CAP.items():
        if not df[f].between(a, b).all(): raise ValueError('size cap violated: %s' % f)
    return True

def density(df): return (df['pyramidal'] + df['interneuron']) / (math.pi * df['shape.radius'] ** 2 * df['shape.thickness'] * 1e-9)
def pyrfrac(df): return df['pyramidal'] / (df['pyramidal'] + df['interneuron'])
def soft_clean(df):
    d, p = density(df), pyrfrac(df)
    return ((d >= 10000) & (d <= 50000) & (p >= 0.70) & (p <= 0.80)).values

def pred_wall(df): return np.exp(-4.4642 + 1.7582 * np.log(df['pyramidal'] + df['interneuron']) + 0.1119 * df['days'])

def J_of(df):
    return np.minimum.reduce([df[c].values.astype(float) / REF[c] for c in COMP])

def comps_from_rawcounts(j):
    """j = one run's dict (rawcounts json entry). Returns dict of components/labels."""
    rc = j['rawcounts']; c = rc['classes']
    def s(keys, fld): return float(sum(c[k][fld] for k in keys if k in c))
    out = {'raw_pyr_int_n': s(['pyr->int:1'], 'connections'), 'raw_pyr_int_g': s(['pyr->int:1'], 'g_peak_sum_nS'),
           'raw_int_pyr_n': s(['int->pyr:2'], 'connections'), 'raw_int_pyr_g': s(['int->pyr:2'], 'g_peak_sum_nS'),
           'raw_int_int_n': s(['int->int:2'], 'connections'), 'raw_int_int_g': s(['int->int:2'], 'g_peak_sum_nS'),
           'raw_pyr_pyr_n': s(['pyr->pyr:1', 'pyr->pyr:3'], 'connections'), 'raw_pyr_pyr_g': s(['pyr->pyr:1', 'pyr->pyr:3'], 'g_peak_sum_nS')}
    for k, v in j['labels'].items(): out[k] = v
    pn = rc.get('agg_int_incoming_AMPA_from_pyr_nS', {}).get('per_neuron')
    out['frac_int_ampa_ge13_84'] = float(np.mean(np.array(pn) >= 13.84)) if pn else float('nan')
    out['n_int_pn'] = len(pn) if pn else 0
    out['mean_gaba_per_pyr_nS'] = rc.get('agg_pyr_incoming_GABA_from_int_nS', {}).get('mean', float('nan'))
    return out

def load_batchB():
    df = pd.read_excel(D + 'batchB_labels_all.xlsx')
    rows = []
    for f in glob.glob(D + 'batchB/out*-rawcounts.json'):
        n = int(re.search(r'out(\d+)-', f).group(1)); j = json.load(open(f))['0']
        r = comps_from_rawcounts(j); r['sample'] = n + 1; r['_pars'] = j['pars']; rows.append(r)
    R = pd.DataFrame(rows).set_index('sample').sort_index(); df = df.set_index('sample').loc[R.index]
    for s, r in R.iterrows():
        assert np.abs(np.array(r['_pars'], float) - df.loc[s, F].values.astype(float)).max() < 1e-9
        assert abs(r['usable_conns2'] - df.loc[s, 'usable_conns2']) < 1e-9
    out = df[F].copy()
    for c in R.columns:
        if c not in ('_pars',): out[c] = R[c].values
    out = out.reset_index(drop=True); out['run_id'] = ['B%03d' % s for s in R.index]
    assert len(out) == 100
    out['J'] = J_of(out); out['soft_clean'] = soft_clean(out)
    return out

def load_arm_runs(path, arm, prefix='T-'):
    """Completed training runs of one arm from runs.csv (rc==0)."""
    if not path or not os.path.exists(path): return pd.DataFrame(columns=F + COMP)
    r = pd.read_csv(path)
    r = r[(r['arm'] == arm) & (r['rc'] == 0) & r['run_id'].astype(str).str.startswith(prefix)]
    return r.reset_index(drop=True)

def sobol_pool(n=60000, seed=123):
    from scipy.stats import qmc
    lo, hi = box()
    u = qmc.Sobol(7, scramble=True, seed=seed).random(n)
    c = round_cfg(pd.DataFrame(lo + u * (hi - lo), columns=F)).drop_duplicates().reset_index(drop=True)
    assert_limits(c)
    return c
