"""ML arm (fully mechanical). usage: ml_arm.py round1|round2|nominate [--runs runs.csv] [--out f.csv] [--method dice|pool]
                                    ml_arm.py predict <csv> [--runs runs.csv] [--out f.csv]
RF: RandomForestRegressor(500, random_state=0) per component on the 7 raw features. Training = batch B (100 rows) + own completed T-ML* runs."""
import argparse, sys, json, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from h2h_common import *
warnings.filterwarnings('ignore')

def training(runs):
    b = load_batchB()[F + COMP]
    r = load_arm_runs(runs, 'ML')
    return pd.concat([b, r[F + COMP]], ignore_index=True), len(r)

def fit(tr):
    return {c: RandomForestRegressor(n_estimators=500, random_state=0, n_jobs=1).fit(tr[F].values.astype(float), tr[c].values.astype(float)) for c in COMP}

def tree_preds(m, X):
    X = np.asarray(X, dtype=np.float32)
    return np.stack([t.predict(X) for t in m.estimators_], axis=1)

def predict_table(models, cfg):
    X = cfg[F].values.astype(float); out = {}
    for c in COMP:
        tp = tree_preds(models[c], X)
        out[c + '_mean'] = tp.mean(1); out[c + '_lo80'] = np.percentile(tp, 10, axis=1); out[c + '_hi80'] = np.percentile(tp, 90, axis=1)
    o = pd.DataFrame(out, index=cfg.index)
    o['J_pred'] = np.minimum.reduce([o[c + '_mean'] / REF[c] for c in COMP])
    return o

def score_mean(models, cfg):
    X = cfg[F].values.astype(float)
    return np.minimum.reduce([models[c].predict(X) / REF[c] for c in COMP])

def key(df): return set(map(tuple, df[F].astype(float).round(3).values))

def greedy(cands, score, n, excl, dmin=0.15):
    order = np.argsort(-score, kind='stable'); chosen = []; vecs = []
    for i in order:
        r = cands.iloc[i]
        if tuple(np.round(r[F].values.astype(float), 3)) in excl: continue
        v = r[F].values.astype(float) / HARD_SPAN
        if all(np.linalg.norm(v - w) >= dmin for w in vecs):
            vecs.append(v); chosen.append(i)
            if len(chosen) == n: break
    return chosen

def dice_candidates(models, tr, n_target=150, max_calls=25):
    import dice_ml
    lo, hi = box()
    class Scorer:   # scalar handed to DiCE: min over components of RF mean / (1.041*ref); <=0 if not soft-clean / out of box (as in multi_target_optim.JointScoreModel)
        def predict(self, inst):
            X = pd.DataFrame(inst, columns=F) if not isinstance(inst, pd.DataFrame) else inst[F]
            X = round_cfg(X.reset_index(drop=True))
            s = score_mean(models, X) / T1
            ok = soft_clean(X) & np.all((X.values >= lo - 1e-9) & (X.values <= hi + 1e-9), axis=1)
            return np.where(ok, s, -1.0)
    sc = Scorer(); data_df = tr[F].copy().astype(float); data_df['joint_score'] = sc.predict(data_df)
    d = dice_ml.Data(dataframe=data_df, continuous_features=F, outcome_name='joint_score')
    m = dice_ml.Model(model=sc, backend='sklearn', model_type='regressor')
    exp = dice_ml.Dice(d, m, method='random')
    pr = {f: [float(lo[i]), float(hi[i])] for i, f in enumerate(F)}
    out = []; log = []
    rng = np.random.default_rng(0)
    for k in range(max_calls):
        q = tr[F].astype(float).iloc[[int(rng.integers(len(tr)))]].reset_index(drop=True)
        try:
            res = exp.generate_counterfactuals(q, total_CFs=15, desired_range=[1.0, 1e9], permitted_range=pr, random_seed=1000 + k, sample_size=5000)
            cf = res.cf_examples_list[0].final_cfs_df
            n = 0 if cf is None else len(cf)
            if n: out.append(cf[F])
            log.append((k, n))
        except Exception as e:
            log.append((k, 'ERR ' + type(e).__name__ + ': ' + str(e)[:80]))
        if sum(len(o) for o in out) >= n_target: break
    if not out: return None, log
    c = round_cfg(pd.concat(out, ignore_index=True)).drop_duplicates().reset_index(drop=True)
    return c, log

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('csv', nargs='?')
    ap.add_argument('--runs', default=None); ap.add_argument('--out', default=None); ap.add_argument('--method', default='dice')
    a = ap.parse_args()
    tr, nown = training(a.runs); models = fit(tr)
    print('training rows: %d (batch B 100 + own ML runs %d)' % (len(tr), nown))
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 50)
    if a.cmd == 'predict':
        cfg = pd.read_csv(a.csv); o = predict_table(models, cfg)
        res = pd.concat([cfg[[c for c in cfg.columns if c in ('config_id', 'run_id') or c in F]], o], axis=1)
    else:
        excl = key(tr)
        if a.cmd == 'nominate':
            pool = sobol_pool(); pool = pool[soft_clean(pool)].reset_index(drop=True)
            idx = greedy(pool, score_mean(models, pool), 3, set()); sel = pool.iloc[idx]; method = 'pool (nominate always uses the pool top-3, greedy-diverse)'
            tag = 'ML-NOM'
        else:
            tag = {'round1': 'ML-R1', 'round2': 'ML-R2'}[a.cmd]; method = None
            sel = None
            if a.method == 'dice':
                c, log = dice_candidates(models, tr)
                print('DiCE calls (k, n_cfs):', log[:12], '...' if len(log) > 12 else '')
                if c is not None:
                    c = c[soft_clean(c)].reset_index(drop=True)
                    s = score_mean(models, c); c = c[s >= T1].reset_index(drop=True); s = s[s >= T1]
                    print('DiCE: %d unique soft-clean candidates with predicted score >= %.3f' % (len(c), T1))
                    if len(c) >= 5:
                        idx = greedy(c, s, 5, excl)
                        if len(idx) == 5: sel = c.iloc[idx]; method = 'DiCE (dice_ml method=random, joint min-margin scalar score)'
            if sel is None:
                pool = sobol_pool(); pool = pool[soft_clean(pool)].reset_index(drop=True)
                idx = greedy(pool, score_mean(models, pool), 5, excl); sel = pool.iloc[idx]
                method = 'POOL FALLBACK (Sobol 60000 seed 123, soft-clean, top-5 by score, greedy-diverse 0.15)'
            # ensure DiCE path result is labelled; sort by score
        sel = sel.reset_index(drop=True); assert_limits(sel)
        sel.insert(0, 'config_id', ['%s-%d' % (tag, i + 1) for i in range(len(sel))])
        for f in F:
            if f != 'dm.weight': sel[f] = sel[f].astype(int)
        o = predict_table(models, sel); res = pd.concat([sel, o], axis=1)
        res['soft_clean'] = soft_clean(sel); res['pred_wall_s'] = pred_wall(sel).round(0).values
        print('METHOD:', method)
    print(res.round(3).to_string())
    if a.out: res.to_csv(a.out, index=False)

if __name__ == '__main__': main()
