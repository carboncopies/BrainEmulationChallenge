"""Mechanistic arm: NB2 law (as scope_offline/A/g1.py). usage:
  mech_arm.py predict <csv> [--runs runs.csv] [--variant M1|M1rt] [--out f.csv]
  mech_arm.py refit [--runs runs.csv]     (fit on batch B + own T-MECH runs; print coefs for M1 and M1rt)
Features: log(n_pre*n_post'), log V, log dm.weight, days, log minsep  (M1rt: log radius, log thickness instead of log V). alpha by ML.
Predictive interval: NB2 with alpha_total = alpha + 0.03 (seed-variation term), 10th-90th percentile."""
import argparse, warnings
import numpy as np, pandas as pd, statsmodels.api as sm
from statsmodels.discrete.discrete_model import NegativeBinomial
from scipy.stats import nbinom
from h2h_common import *
warnings.filterwarnings('ignore')
PATH = {'raw_pyr_int_n': ('pyramidal', 'interneuron'), 'raw_int_pyr_n': ('interneuron', 'pyramidal'),
        'raw_int_int_n': ('interneuron', 'interneuron'), 'usable_conns2': ('pyramidal', 'pyramidal')}
SEED_ALPHA = 0.03
lg = lambda x: np.log(np.maximum(np.asarray(x, float), 1e-12))

def X_of(df, t, variant='M1'):
    a, b = PATH[t]; npre = df[a].values.astype(float); npo = df[b].values.astype(float)
    pair = npre * (npo - 1) if a == b else npre * npo
    cols = [lg(pair)]
    if variant == 'M1': cols.append(lg(np.pi * df['shape.radius'].values.astype(float) ** 2 * df['shape.thickness'].values.astype(float)))
    else: cols += [lg(df['shape.radius']), lg(df['shape.thickness'])]
    cols += [lg(df['dm.weight']), df['days'].values.astype(float), lg(df['minneuronseparation'])]
    return np.column_stack(cols)
NAMES = {'M1': ['const', 'log(npre*npost)', 'logV', 'log dm.weight', 'days', 'log minsep'],
         'M1rt': ['const', 'log(npre*npost)', 'log radius', 'log thickness', 'log dm.weight', 'days', 'log minsep']}

def nbfit(X, y):
    mu = X.mean(0); sd = X.std(0); Z = sm.add_constant((X - mu) / sd)
    p0 = sm.GLM(y, Z, family=sm.families.Poisson()).fit().params
    for meth in ['newton', 'bfgs', 'nm']:
        try:
            r = NegativeBinomial(y, Z, loglike_method='nb2').fit(start_params=np.append(p0, 0.5), method=meth, maxiter=500, disp=0)
            a = r.params[-1]
            if r.mle_retvals.get('converged', True) and np.isfinite(r.params).all() and 1e-6 < a < 1e3:
                beta = r.params[:-1]; break
        except Exception: pass
    else: raise RuntimeError('NB fit failed')
    # raw-scale coefficients
    b = beta[1:] / sd; c0 = beta[0] - (b * mu).sum()
    return dict(beta=beta, alpha=float(a), mu=mu, sd=sd, raw=np.append(c0, b))

def fit_all(tr, variant):
    return {t: nbfit(X_of(tr, t, variant), tr[t].values.astype(float)) for t in COMP}

def predict(fits, cfg, variant):
    out = {}
    for t in COMP:
        f = fits[t]; Z = sm.add_constant((X_of(cfg, t, variant) - f['mu']) / f['sd'], has_constant='add')
        m = np.exp(Z @ f['beta']); al = f['alpha'] + SEED_ALPHA
        n = 1.0 / al; p = n / (n + m)
        out[t + '_mean'] = m; out[t + '_lo80'] = nbinom.ppf(0.10, n, p); out[t + '_hi80'] = nbinom.ppf(0.90, n, p)
    o = pd.DataFrame(out, index=cfg.index)
    o['J_pred'] = np.minimum.reduce([o[t + '_mean'] / REF[t] for t in COMP])
    return o

def training(runs):
    b = load_batchB()[F + COMP]; r = load_arm_runs(runs, 'MECH')
    return pd.concat([b, r[F + COMP]], ignore_index=True), len(r)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('csv', nargs='?')
    ap.add_argument('--runs', default=None); ap.add_argument('--variant', default='M1'); ap.add_argument('--out', default=None)
    a = ap.parse_args(); tr, n = training(a.runs)
    print('training rows %d (batch B 100 + own MECH runs %d)' % (len(tr), n)); pd.set_option('display.width', 250); pd.set_option('display.max_columns', 50)
    if a.cmd == 'predict':
        cfg = pd.read_csv(a.csv); fits = fit_all(tr, a.variant); o = predict(fits, cfg, a.variant)
        res = pd.concat([cfg[[c for c in cfg.columns if c in ('config_id', 'run_id') or c in F]], o], axis=1)
        print(res.round(2).to_string())
        if a.out: res.to_csv(a.out, index=False)
    elif a.cmd == 'refit':
        for v in ['M1', 'M1rt']:
            fits = fit_all(tr, v); print('== variant', v)
            for t in COMP:
                print(' ', t, 'alpha=%.4f' % fits[t]['alpha'], ' '.join('%s=%.3f' % (nm, c) for nm, c in zip(NAMES[v], fits[t]['raw'])))
