"""Multi-target RF models trained on REAL batch B labels (batchB_labels_all.xlsx) + bounded optimizer.
Run: python batchB_models.py cv | optimize   (writes batchB_cv_results.json / suggested_configs_batchB.xlsx)"""
import json, os, sys, warnings
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import RepeatedKFold
from sklearn.inspection import permutation_importance
from scipy.stats import spearmanr
import bio_check
import multi_target_optim as mto

HERE = os.path.dirname(os.path.abspath(__file__))
FEATS = mto.BASE_FEATURES
TARGETS = ["usable_pyr_int", "usable_int_pyr", "usable_int_int", "frac_int_driven",
           "frac_pyr_inhibited_w05", "usable_conns2", "frac_pyr_inhibited"]
WEAK_FLAG = {"frac_pyr_inhibited": "weak: non-zero in only 13/100 rows"}
SIZE_CAP = {"pyramidal": (16, 70), "interneuron": (16, 30)}   # sampled range -> no extrapolation
N_TREES_CV, N_TREES_FINAL = 500, 2000

def load():
    import merge_batchB
    return merge_batchB.merge()

def rf(n, seed=0):
    return RandomForestRegressor(n_estimators=n, min_samples_leaf=1, random_state=seed, n_jobs=1)

def tree_pred(m, X):
    return mto.tree_predictions(m, X)

def _fold(X, y, tr, te, k):
    m = rf(N_TREES_CV).fit(X.iloc[tr], y[tr])
    tp = tree_pred(m, X.iloc[te]); p = tp.mean(axis=1)
    lo, hi = np.percentile(tp, 2.5, axis=1), np.percentile(tp, 97.5, axis=1)
    imp = None
    if k < 10:
        imp = permutation_importance(m, X.iloc[te], y[te], n_repeats=5, random_state=0, scoring="r2").importances_mean
    return (r2_score(y[te], p), mean_absolute_error(y[te], p), mean_absolute_error(y[te], np.full(len(te), y[tr].mean())),
            np.mean((y[te] >= lo) & (y[te] <= hi)), np.mean(hi - lo), imp)

def poisson_model():
    from sklearn.linear_model import PoissonRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return make_pipeline(StandardScaler(), PoissonRegressor(alpha=1e-2, max_iter=1000))

def _alt_fold(kind, X, y, tr, te):
    m = (poisson_model() if kind == "poisson_lin" else
         RandomForestRegressor(300, min_samples_leaf=5, random_state=0, n_jobs=1)).fit(X.iloc[tr], y[tr])
    return r2_score(y[te], m.predict(X.iloc[te]))

def cv(df, repeats=10):
    out = {}
    X = df[FEATS].reset_index(drop=True)
    rkf = RepeatedKFold(n_splits=5, n_repeats=repeats, random_state=1)
    for t in TARGETS:
        y = df[t].values.astype(float)
        from joblib import Parallel, delayed
        R = Parallel(n_jobs=32)(delayed(_fold)(X, y, tr, te, k) for k, (tr, te) in enumerate(rkf.split(X)))
        r2s, maes, base_mae, cov, widths = [[r[i] for r in R] for i in range(5)]
        fold_imp = [r[5] for r in R if r[5] is not None]
        imp = np.mean(fold_imp, axis=0)
        alt = {k: float(np.mean(Parallel(n_jobs=32)(delayed(_alt_fold)(k, X, y, tr, te) for tr, te in rkf.split(X))))
               for k in ("poisson_lin", "rf_leaf5")}
        full = rf(N_TREES_CV).fit(X, y)
        rho = {f: float(spearmanr(df[f], y)[0]) if y.std() > 0 else float("nan") for f in FEATS}
        out[t] = dict(n=len(y), n_nonzero=int((y > 0).sum()), mean=float(y.mean()), r2_mean=float(np.mean(r2s)),
                      r2_sd=float(np.std(r2s)), mae=float(np.mean(maes)), mae_baseline_mean=float(np.mean(base_mae)),
                      pi95_coverage=float(np.mean(cov)), pi95_width=float(np.mean(widths)),
                      perm_importance_heldout=dict(zip(FEATS, map(float, imp))),
                      impurity_importance=dict(zip(FEATS, map(float, full.feature_importances_))),
                      spearman=rho, alt_model_r2=alt, flag=WEAK_FLAG.get(t, ""))
        print(t, {k: round(v, 3) for k, v in out[t].items() if isinstance(v, float)}, flush=True)
    return out

if __name__ == "__main__":
    cmd = sys.argv[1]
    df = load()
    if cmd == "cv":
        res = cv(df)
        json.dump(res, open(os.path.join(HERE, "batchB_cv_results.json"), "w"), indent=1)

# ------------------------------------------------------------------ optimizer
# joint score uses ONLY targets whose CV R2 beats the mean baseline clearly (see report); the others are reported but NOT optimized
JOINT_TARGETS = ["usable_int_pyr", "frac_pyr_inhibited_w05", "usable_conns2"]
POISSON_XCHECK = JOINT_TARGETS
PYRPYR_BAND = (200, 2500)  # Marianna's usable range for Pyr-Pyr; used as a soft sanity target, reported only

def candidates(n=60000, seed=0):
    from scipy.stats import qmc
    cfg = bio_check.load_ranges()["parameters"]
    lo = np.array([cfg[f]["min"] for f in FEATS], float); hi = np.array([cfg[f]["max"] for f in FEATS], float)
    for f, (a, b) in SIZE_CAP.items():
        i = FEATS.index(f); lo[i], hi[i] = max(lo[i], a), min(hi[i], b)
    u = qmc.Sobol(len(FEATS), scramble=True, seed=seed).random(n)
    c = pd.DataFrame(lo + u * (hi - lo), columns=FEATS)
    c = mto._round_candidates(c, bio_check.load_ranges())
    c = c.drop_duplicates().reset_index(drop=True)
    bio_check.assert_hard_limits(c)
    assert c.pyramidal.between(*SIZE_CAP["pyramidal"]).all() and c.interneuron.between(*SIZE_CAP["interneuron"]).all()
    return c

def optimize(df, cvres, n_sel=20, seed=0):
    X = df[FEATS]
    models = {t: rf(N_TREES_FINAL, seed).fit(X, df[t].values.astype(float)) for t in TARGETS}
    c = candidates(seed=seed)
    P = {}
    for t, m in models.items():
        tp = tree_pred(m, c)
        P[t] = dict(lo=np.percentile(tp, 2.5, axis=1), med=np.percentile(tp, 50, axis=1), hi=np.percentile(tp, 97.5, axis=1), mean=tp.mean(axis=1))
    # scale: 75th percentile of observed non-zero label, so that margin 1 = "a good observed value"
    scale = {t: float(np.percentile(df[t][df[t] > 0], 75)) for t in JOINT_TARGETS}
    # joint score on the MEAN prediction (point estimate), min over targets of mean/scale; the 'lo' band
    # is reported but the RF's lower PI is ~0 for many targets (zero-inflated), so is too harsh for ranking
    M = np.column_stack([P[t]["mean"] / scale[t] for t in JOINT_TARGETS])
    c["joint_score"] = M.min(axis=1)
    c["mean_score"] = M.mean(axis=1)
    for t in TARGETS:
        for k in ("mean", "lo", "hi"):
            c[f"{t}__{k}"] = P[t][k]
    for t in POISSON_XCHECK:
        pm = poisson_model().fit(X, df[t].values.astype(float)); c[f"{t}__poisson_xcheck"] = pm.predict(c[FEATS])
    # in-sample density / fraction warnings
    b = bio_check.check_frame(c[FEATS])
    c["density_per_mm3"] = b["density_per_mm3"].values; c["pyramidal_fraction"] = b["pyramidal_fraction"].values
    c["bio_soft_violations"] = b["bio_soft_violations"].values
    # distance to training data (standardized nearest neighbour) as extrapolation check
    sd = X.std().values; Xt = (X.values / sd)
    def nn(v): return np.min(np.linalg.norm(Xt - v / sd, axis=1))
    # per-pathway top picks
    per = {}
    for t in TARGETS:
        per[t] = c.sort_values(f"{t}__mean", ascending=False).head(5).assign(objective=t)
    # joint: greedy diverse selection by joint_score then mean_score
    span = np.array([bio_check.load_ranges()["parameters"][f]["max"] - bio_check.load_ranges()["parameters"][f]["min"] for f in FEATS], float)
    clean = c[c.bio_soft_violations == 0]
    print("candidates:", len(c), "soft-clean:", len(clean))
    base = clean if len(clean) >= 100 else c
    pool = base.sort_values(["joint_score", "mean_score"], ascending=False).head(3000)
    chosen, idx = [], []
    for i, r in pool.iterrows():
        v = r[FEATS].values.astype(float) / span
        if all(np.linalg.norm(v - w) > 0.15 for w in chosen):
            chosen.append(v); idx.append(i)
            if len(idx) == n_sel: break
    sel = c.loc[idx].copy().reset_index(drop=True)
    sel.insert(0, "config_id", [f"B{i+1:02d}" for i in range(len(sel))])
    sel["nn_dist_std"] = [nn(r[FEATS].values.astype(float)) for _, r in sel.iterrows()]
    bio_check.assert_hard_limits(sel[FEATS])   # every suggestion
    for f, (a, b2) in SIZE_CAP.items():
        assert sel[f].between(a, b2).all()
    # grid optimum summary: best predicted value for each target and the params
    best = {t: c.loc[c[f"{t}__mean"].idxmax(), FEATS + [f"{t}__mean", f"{t}__lo", f"{t}__hi"]].to_dict() for t in TARGETS}
    return sel, per, best, scale, c, models

if __name__ == "__main__" and sys.argv[1] == "optimize":
    cvres = json.load(open(os.path.join(HERE, "batchB_cv_results.json")))
    sel, per, best, scale, c, models = optimize(df, cvres)
    out = sel.copy()
    cols = ["config_id"] + FEATS + ["joint_score", "mean_score"]
    for t in TARGETS:
        cols += [f"{t}__mean", f"{t}__lo", f"{t}__hi"]
    cols += [f"{t}__poisson_xcheck" for t in POISSON_XCHECK]
    cols += ["density_per_mm3", "pyramidal_fraction", "bio_soft_violations", "nn_dist_std"]
    xl = os.path.join(HERE, "suggested_configs_batchB.xlsx")
    with pd.ExcelWriter(xl) as w:
        out[cols].round(4).to_excel(w, sheet_name="suggestions", index=False)
        pd.concat(per.values())[["objective"] + FEATS + [f"{t}__mean" for t in TARGETS]].round(3).to_excel(w, sheet_name="per_pathway_top5", index=False)
        pd.DataFrame(best).T.round(3).to_excel(w, sheet_name="best_single_target")
        pd.DataFrame({"target": list(scale), "scale_75pct_nonzero": list(scale.values())}).to_excel(w, sheet_name="joint_scale", index=False)
        pd.DataFrame({"note": [
            "Predictions: RF mean over trees; lo/hi = 2.5/97.5 percentile of per-tree predictions (ensemble spread, NOT a noise-aware predictive interval).",
            "Trained on 100 real batch B rows; search box = hard bio limits intersected with sampled size range (pyr 16-70, int 16-30).",
            "joint_score = min over 3 skilled targets (int_pyr, frac_pyr_inhibited_w05, conns2) of (mean prediction / 75th pct of observed non-zero label). Not validated by simulation.",
            "usable_pyr_int, usable_int_int, frac_int_driven and strict frac_pyr_inhibited have NO cross-validated skill; their columns are shown for completeness but were NOT used to choose configs.",
            "*__poisson_xcheck = independent log-linear Poisson GLM prediction (CV R2 higher than RF for the 3 skilled targets); large disagreement with RF = distrust."]}).to_excel(w, sheet_name="notes", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50)
    print(out[["config_id"] + FEATS + ["joint_score"] + [f"{t}__mean" for t in JOINT_TARGETS] + ["nn_dist_std"]].round(2).to_string())
    print(pd.DataFrame(best).T.round(2).to_string())
    print(scale)
    print("sel mean-vs-observed joint score: observed max joint", )
    Xo = df[JOINT_TARGETS] / pd.Series(scale); print("observed rows joint (min ratio) top5:", Xo.min(axis=1).sort_values().tail(5).round(2).tolist())
    json.dump({"scale": scale}, open(os.path.join(HERE, "batchB_opt_meta.json"), "w"))
