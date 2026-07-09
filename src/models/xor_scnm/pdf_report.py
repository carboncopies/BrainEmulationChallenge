"""
Generate a detailed PDF report for the XOR GT vs SUB Streamlit dashboard.
"""

from __future__ import annotations

import io
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    _HAS_REPORTLAB = True
except ImportError:
    _HAS_REPORTLAB = False

TRUTH = {
    "00": {"input_A": 0, "input_B": 0, "expected_output": 0},
    "01": {"input_A": 0, "input_B": 1, "expected_output": 1},
    "10": {"input_A": 1, "input_B": 0, "expected_output": 1},
    "11": {"input_A": 1, "input_B": 1, "expected_output": 0},
}

IO_NEURONS = ("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E")
BLACKBOX_NOTE = (
    "Black-box SUB maps IF neurons to GT I/O only (PyrIn_A, PyrIn_B1/B2, E). "
    "Deep GT interneurons are often silent (~−60 mV) in SUB by design."
)


def _normalize_pattern(p) -> str:
    s = str(p).strip()
    if s.upper().startswith("XOR_"):
        s = s[4:]
    if s.isdigit():
        return s.zfill(2)
    return s


def _fmt_val(v, prec: int = 4) -> str:
    if v is None:
        return "—"
    try:
        if pd.isna(v):
            return "—"
    except (TypeError, ValueError):
        pass
    if isinstance(v, float):
        return f"{v:.{prec}f}"
    return str(v)


def _load_pair(gt_path: str, sub_path: str):
    import h5py

    gt_data = pd.read_hdf(gt_path, "/data")
    gt_spikes = pd.read_hdf(gt_path, "/spikes_raw")
    sub_data = pd.read_hdf(sub_path, "/data")
    sub_spikes = pd.read_hdf(sub_path, "/spikes_raw")
    cfg = pd.read_hdf(gt_path, "/network_config")
    tmap = pd.read_hdf(gt_path, "/trial_map")
    with h5py.File(gt_path, "r") as f:
        meta = dict(f["/metadata"].attrs)
    return gt_data, gt_spikes, sub_data, sub_spikes, cfg, tmap, meta


def _get_trial(data: pd.DataFrame, tid: int) -> pd.DataFrame:
    return data[data["trial_id"] == tid]


def _get_trials_by_pattern(data: pd.DataFrame, pattern: str, trial_len: int):
    if "case" not in data.columns or "rep" not in data.columns:
        return None
    pattern = str(pattern)
    out = []
    for u in data["rep"].unique():
        sub = data[(data["case"].astype(str) == pattern) & (data["rep"] == u)]
        if len(sub):
            out.append(sub)
    return out


def _get_spiking_neurons(cfg, data) -> List[str]:
    out = []
    for lbl in cfg["label"]:
        col = f"{lbl}_spike"
        if col in data.columns and data[col].sum() > 0:
            out.append(lbl)
    return out


def _spike_cols(cfg, data):
    return [f"{l}_spike" for l in _get_spiking_neurons(cfg, data)]


def _out_spike_col(cfg, data):
    outs = [f"{r['label']}_spike" for _, r in cfg.iterrows() if r["role"] == "output"]
    cols = _spike_cols(cfg, data)
    for c in outs:
        if c in cols:
            return c
    return outs[0] if outs else "E_spike"


def _behavioral_rows(data, cfg, tmap, patterns, trial_len, truth_effective, model: str):
    out_col = _out_spike_col(cfg, data)
    rows = []
    for p in patterns:
        ps = _normalize_pattern(p)
        tr = truth_effective.get(ps) or TRUTH.get(ps, TRUTH["00"])
        want = tr["expected_output"]
        TP = FN = TN = FP = 0
        trials = _get_trials_by_pattern(data, ps, trial_len)
        if trials is not None:
            for t in trials:
                window = t[t["t_in_trial"] <= trial_len]
                fired = window[out_col].sum() > 0
                have = 1 if fired else 0
                if want == 1 and have == 1:
                    TP += 1
                elif want == 1 and have == 0:
                    FN += 1
                elif want == 0 and have == 0:
                    TN += 1
                else:
                    FP += 1
        else:
            for _, row in tmap[tmap["case"].astype(str) == ps].iterrows():
                t = _get_trial(data, row["trial_id"])
                fired = t[t["t_in_trial"] <= trial_len][out_col].sum() > 0
                have = 1 if fired else 0
                if want == 1 and have == 1:
                    TP += 1
                elif want == 1 and have == 0:
                    FN += 1
                elif want == 0 and have == 0:
                    TN += 1
                else:
                    FP += 1
        den = TP + FN + TN + FP
        acc = (TP + TN) / den if den else 0.0
        sens = TP / (TP + FN) if (TP + FN) else 0.0
        spec = TN / (TN + FP) if (TN + FP) else 0.0
        rows.append({
            "model": model,
            "Pattern": ps,
            "TP": TP,
            "FN": FN,
            "TN": TN,
            "FP": FP,
            "Accuracy": round(acc, 4),
            "Sensitivity": round(sens, 4),
            "Specificity": round(spec, 4),
        })
    return pd.DataFrame(rows), out_col


def _spike_times(spk_df, label, pattern):
    pat = _normalize_pattern(pattern)
    mask = (spk_df["label"] == label) & (
        spk_df["pattern"].astype(str).map(_normalize_pattern) == pat
    )
    return spk_df.loc[mask, "t_in_trial"].to_numpy()


def _vr_dist(tx, ty, tau):
    nx, ny = tx.size, ty.size
    if nx == 0 and ny == 0:
        return 0.0
    if nx == 0 or ny == 0:
        return float(np.sqrt((nx + ny) / (2.0 * tau)))
    diffs = np.abs(tx[:, None] - ty[None, :])
    sxy = np.exp(-diffs / float(tau)).sum()
    return float(np.sqrt(max((nx + ny - 2.0 * sxy) / (2.0 * tau), 0.0)))


def _schreiber(a, b, kernel):
    ca = np.convolve(a.astype(float), kernel, mode="same")
    cb = np.convolve(b.astype(float), kernel, mode="same")
    num = float(np.dot(ca, cb))
    den = float(np.sqrt(np.dot(ca, ca) * np.dot(cb, cb)))
    if den == 0:
        return float("nan")
    return float(max(-1.0, min(1.0, num / den)))


def _gaussian_kernel(sigma_ms, fs_hz):
    dt = 1000.0 / fs_hz
    ksz = max(3, int(round(6.0 * sigma_ms / dt)))
    if ksz % 2 == 0:
        ksz += 1
    half = ksz // 2
    t = (np.arange(ksz) - half) * dt
    g = np.exp(-0.5 * (t / sigma_ms) ** 2).astype(np.float64)
    g /= g.sum() if g.sum() else 1.0
    return g


def _vm_rmse_io(gt, sub, vm_cols, common_ids, patterns, trial_len):
    rows = []
    for patt in patterns:
        for col in vm_cols:
            sq = []
            for tid in common_ids[patt]:
                g = _get_trial(gt, tid)
                s = _get_trial(sub, tid)
                n = min(len(g), len(s), trial_len)
                if n == 0:
                    continue
                d = g[col].to_numpy(float)[:n] - s[col].to_numpy(float)[:n]
                sq.append(float(np.mean(d * d)))
            rmse = float(np.sqrt(np.mean(sq))) if sq else float("nan")
            rows.append({
                "neuron": col.replace("_vm", ""),
                "pattern": patt,
                "rmse_mV": rmse,
            })
    return pd.DataFrame(rows)


def _bin_counts(v, bin_ms, fs_hz):
    bs = max(1, int(round(bin_ms * fs_hz / 1000.0)))
    nb = len(v) // bs
    if nb == 0:
        return np.zeros(0, dtype=float)
    return v[: nb * bs].reshape(nb, bs).sum(1).astype(float)


def _safe_pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.size != b.size or a.size == 0 or np.nanvar(a) <= 0 or np.nanvar(b) <= 0:
        return np.nan
    am, bm = np.nanmean(a), np.nanmean(b)
    d = np.sqrt(np.nansum((a - am) ** 2) * np.nansum((b - bm) ** 2))
    return float(np.nansum((a - am) * (b - bm)) / d) if d > 0 else np.nan


def _psth_summary(gt_data, sub_data, neuron_col, patterns, common_ids, trial_len, fs_hz, bin_ms=5):
    rows = []
    for p in patterns:
        mats_gt, mats_sub = [], []
        for tid in common_ids[p]:
            g = _get_trial(gt_data, tid)
            s = _get_trial(sub_data, tid)
            if neuron_col not in g.columns or neuron_col not in s.columns:
                continue
            mats_gt.append(_bin_counts(g[neuron_col].to_numpy(int), bin_ms, fs_hz))
            mats_sub.append(_bin_counts(s[neuron_col].to_numpy(int), bin_ms, fs_hz))
        if not mats_gt:
            continue
        L = min(min(len(m) for m in mats_gt), min(len(m) for m in mats_sub))
        gt_h = np.nanmean(np.stack([m[:L] for m in mats_gt]), 0)
        sub_h = np.nanmean(np.stack([m[:L] for m in mats_sub]), 0)
        r = _safe_pearson(gt_h, sub_h)
        rmse = float(np.sqrt(np.nanmean((gt_h - sub_h) ** 2)))
        rows.append({
            "neuron": neuron_col.replace("_spike", ""),
            "pattern": p,
            "Pearson_r": r,
            "PSTH_RMSE": rmse,
        })
    return pd.DataFrame(rows)


def _spike_count_table(data, spike_cols, patterns, common_ids, trial_len, model):
    rows = []
    for col in spike_cols:
        lbl = col.replace("_spike", "")
        for p in patterns:
            total = 0
            for tid in common_ids[p]:
                t = _get_trial(data, tid)
                if col not in t.columns:
                    continue
                mask = (t["t_in_trial"] >= 0) & (t["t_in_trial"] < trial_len)
                total += int(t.loc[mask, col].sum())
            rows.append({"model": model, "neuron": lbl, "pattern": p, "spike_count": total})
    return pd.DataFrame(rows)


def _isi_fano_summary(spk_df, cfg, data, patterns):
    rows = []
    time_col = "spike_time_ms" if "spike_time_ms" in spk_df.columns else "t_in_trial"
    for neuron in _get_spiking_neurons(cfg, data):
        for p in patterns:
            pat = _normalize_pattern(p)
            if "pattern" not in spk_df.columns:
                continue
            mask = (spk_df["label"] == neuron) & (
                spk_df["pattern"].astype(str).map(_normalize_pattern) == pat
            )
            sub = spk_df.loc[mask]
            if sub.empty:
                rows.append({"neuron": neuron, "pattern": pat, "ISI_CV": np.nan, "Fano": np.nan})
                continue
            st_arr = sub[time_col].to_numpy(dtype=float)
            isi = np.diff(np.sort(st_arr))
            if "rep" in sub.columns:
                counts = sub.groupby("rep").size().to_numpy(dtype=float)
            else:
                counts = np.array([float(len(st_arr))])
            cv = float(np.std(isi) / np.mean(isi)) if len(isi) and np.mean(isi) > 0 else np.nan
            fano = float(np.var(counts) / np.mean(counts)) if len(counts) and np.mean(counts) > 0 else np.nan
            rows.append({"neuron": neuron, "pattern": pat, "ISI_CV": cv, "Fano": fano})
    return pd.DataFrame(rows)


def _cfg_io_table(cfg: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ("label", "role", "type", "input_channel") if c in cfg.columns]
    if not cols:
        return cfg.head(0)
    mask = cfg["role"].isin(["input", "output"]) if "role" in cfg.columns else pd.Series(True, index=cfg.index)
    return cfg.loc[mask, cols].copy()


def _granger_jaccard(gt_trials, sub_trials, spike_cols, fs_hz, bin_ms=5, lag=10, alpha=0.05):
    try:
        from scipy.stats import f as f_dist
    except ImportError:
        return dict(gt_edges=0, sub_edges=0, overlap=0, jaccard=np.nan)

    ms_per_sample = 1000.0 / fs_hz

    def lag_design(y, x_lags, lag_n):
        T = y.shape[0]
        if T <= lag_n:
            return np.zeros(0), np.zeros((0, lag_n + 1)), np.zeros((0, 2 * lag_n + 1))
        Y = y[lag_n:]

        def _lags(v):
            return np.column_stack([v[lag_n - k - 1 : T - k - 1] for k in range(lag_n)])

        ylags = _lags(y)
        xlags = _lags(x_lags)
        R = np.column_stack([np.ones(T - lag_n), ylags])
        F = np.column_stack([R, xlags])
        return Y, R, F

    def ols_rss(design, target):
        if design.shape[0] == 0:
            return np.nan
        beta, *_ = np.linalg.lstsq(design, target, rcond=None)
        resid = target - design @ beta
        return float(np.dot(resid, resid))

    def granger_pair(y, x, lag_n):
        Y, R, F = lag_design(y, x, lag_n)
        if Y.size == 0:
            return np.nan, np.nan
        rr, rf = ols_rss(R, Y), ols_rss(F, Y)
        if not (np.isfinite(rr) and np.isfinite(rf) and rf > 0):
            return np.nan, np.nan
        d1, d2 = F.shape[1] - R.shape[1], F.shape[0] - F.shape[1]
        p = np.nan
        if d1 > 0 and d2 > 0:
            p = float(f_dist.sf(((rr - rf) / d1) / (rf / d2), d1, d2))
        return float(np.log(rr / rf)), p

    def bh_fdr(pvals, alpha_n):
        p = np.asarray(pvals, float)
        m = np.sum(np.isfinite(p))
        if m == 0:
            return np.full_like(p, np.nan)
        order = np.argsort(np.where(np.isfinite(p), p, np.inf))
        ranks = np.empty_like(order)
        ranks[order] = np.arange(1, len(p) + 1)
        q = np.full_like(p, np.nan)
        q_work = np.where(np.isfinite(p), p * m / ranks, np.nan)
        prev = np.inf
        for idx in order[::-1]:
            if np.isfinite(q_work[idx]):
                prev = min(prev, q_work[idx])
                q[idx] = prev
        return q

    def bin_block(trials, sc):
        pieces = []
        for df in trials:
            block = df[sc].to_numpy(int)
            W = block.shape[0]
            B = int(np.ceil(W * ms_per_sample / bin_ms))
            binned = np.zeros((B, len(sc)), float)
            for b in range(B):
                lo = int(round((b * bin_ms) / ms_per_sample))
                hi = min(int(round(((b + 1) * bin_ms) / ms_per_sample)), W)
                if lo < hi:
                    binned[b] = block[lo:hi].sum(0)
            pieces.append(binned)
        return np.vstack(pieces) if pieces else np.zeros((0, len(sc)))

    def gc_map(trials, sc):
        X = bin_block(trials, sc)
        N = len(sc)
        if X.shape[0] < lag + 5:
            return np.zeros((N, N), bool)
        ok = X.sum(0) >= 10
        Xz = X.copy().astype(float)
        for j in range(N):
            if ok[j]:
                mu, sd = Xz[:, j].mean(), Xz[:, j].std(ddof=1)
                Xz[:, j] = (Xz[:, j] - mu) / (sd if sd > 0 else 1.0)
            else:
                Xz[:, j] = 0.0
        M_p = np.full((N, N), np.nan)
        for j in range(N):
            if not ok[j]:
                continue
            for i in range(N):
                if i == j or not ok[i]:
                    continue
                _, p = granger_pair(Xz[:, j], Xz[:, i], lag)
                M_p[j, i] = p
        q = bh_fdr(M_p.ravel(), alpha).reshape(M_p.shape)
        return np.isfinite(q) & (q <= alpha)

    sc = [c for c in spike_cols if c in gt_trials[0].columns]
    use_gt = gc_map(gt_trials, sc)
    use_sb = gc_map(sub_trials, sc)
    e_gt = int(use_gt.sum() - np.trace(use_gt))
    e_sb = int(use_sb.sum() - np.trace(use_sb))
    inter = int((use_gt & use_sb).sum() - np.trace(use_gt & use_sb))
    union = int((use_gt | use_sb).sum() - np.trace(use_gt & use_sb))
    jacc = inter / union if union > 0 else 1.0
    return dict(gt_edges=e_gt, sub_edges=e_sb, overlap=inter, jaccard=float(jacc))


def _load_pipeline_artifacts(metrics_dir: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    files = {
        "summary_json": "gt_sub_io_summary.json",
        "beh_csv": "gt_sub_behavior_by_pattern.csv",
        "vm_csv": "gt_sub_io_vm_rmse.csv",
        "vr_csv": "gt_sub_output_van_rossum_trials.csv",
        "sch_csv": "gt_sub_output_schreiber_trials.csv",
    }
    for key, fname in files.items():
        path = os.path.join(metrics_dir, fname)
        if not os.path.isfile(path):
            continue
        try:
            if fname.endswith(".json"):
                with open(path, "r", encoding="utf-8") as f:
                    out[key] = json.load(f)
            else:
                out[key] = pd.read_csv(path)
        except (OSError, json.JSONDecodeError, pd.errors.EmptyDataError):
            pass
    return out


def _metric_pivot(df, value_col, patterns, index_col="neuron", aggfunc="max"):
    if df is None or df.empty or value_col not in df.columns:
        return pd.DataFrame()
    if index_col not in df.columns and "neuron_vm" in df.columns:
        df = df.copy()
        df[index_col] = df["neuron_vm"].astype(str).str.replace("_vm", "", regex=False)
    if index_col not in df.columns or "pattern" not in df.columns:
        return pd.DataFrame()
    g = df.groupby([index_col, "pattern"])[value_col].agg(aggfunc).unstack("pattern")
    for p in patterns:
        if p not in g.columns:
            g[p] = np.nan
    return g.reindex(columns=patterns).reset_index()


def collect_report_context(gt_path: str, sub_path: str) -> Dict[str, Any]:
    """Gather metrics from current GT/SUB files for PDF export."""
    gt_path = os.path.abspath(gt_path)
    sub_path = os.path.abspath(sub_path)
    metrics_dir = os.path.dirname(gt_path)
    gt_data, gt_spikes, sub_data, sub_spikes, cfg, tmap, meta = _load_pair(gt_path, sub_path)
    artifacts = _load_pipeline_artifacts(metrics_dir)

    same = os.path.normpath(gt_path) == os.path.normpath(sub_path)
    trial_len = int(meta["trial_len_ms"])
    fs_hz = float(meta["fs_hz"])
    patterns = [_normalize_pattern(p) for p in tmap["case"].unique()]
    common_ids = {
        p: tmap[tmap["case"].astype(str) == str(p)]["trial_id"].tolist() for p in patterns
    }
    spike_cols = sorted(set(_spike_cols(cfg, gt_data)) | set(_spike_cols(cfg, sub_data)))
    spiking = _get_spiking_neurons(cfg, gt_data)
    truth_effective = dict(TRUTH)
    tau_ms = float((artifacts.get("summary_json") or {}).get("tau_vr_ms", 20.0))
    sigma_ms = float((artifacts.get("summary_json") or {}).get("schreiber_sigma_ms", 10.0))

    gt_beh, out_col = _behavioral_rows(
        gt_data, cfg, tmap, patterns, trial_len, truth_effective, "GT"
    )
    sub_beh, _ = _behavioral_rows(
        sub_data, cfg, tmap, patterns, trial_len, truth_effective, "SUB"
    )
    beh_full = pd.concat([gt_beh, sub_beh], ignore_index=True)
    if "beh_csv" in artifacts:
        beh_full = artifacts["beh_csv"].copy()
        if "Pattern" in beh_full.columns:
            beh_full["Pattern"] = beh_full["Pattern"].map(_normalize_pattern)

    sub_acc = float(sub_beh["Accuracy"].mean()) if len(sub_beh) else 0.0
    sub_tp = int(sub_beh["TP"].sum())
    sub_tn = int(sub_beh["TN"].sum())
    sub_den = int(sub_beh[["TP", "FN", "TN", "FP"]].sum().sum())

    summary_json = artifacts.get("summary_json") or {}

    ks_rows = []
    try:
        from scipy.stats import ks_2samp
        for col in spike_cols:
            lbl = col.replace("_spike", "")
            for p in patterns:
                gt_t = _spike_times(gt_spikes, lbl, p)
                sub_t = _spike_times(sub_spikes, lbl, p)
                if len(gt_t) and len(sub_t):
                    ks, pval = ks_2samp(gt_t, sub_t)
                else:
                    ks, pval = (np.nan, np.nan)
                ks_rows.append({"neuron": col, "pattern": p, "ks_stat": ks, "p_value": pval})
    except ImportError:
        pass
    ks_df = pd.DataFrame(ks_rows)
    ks_max = float(ks_df["ks_stat"].dropna().max()) if len(ks_df) else None

    vr_recs = []
    for p in patterns:
        for tid in common_ids[p]:
            gdf = _get_trial(gt_data, tid)
            sdf = _get_trial(sub_data, tid)
            for neuron in spike_cols:
                mg = (gdf["t_in_trial"] >= 0) & (gdf["t_in_trial"] < trial_len) & (gdf[neuron] == 1)
                ms = (sdf["t_in_trial"] >= 0) & (sdf["t_in_trial"] < trial_len) & (sdf[neuron] == 1)
                tx = gdf.loc[mg, "t_in_trial"].to_numpy(float)
                ty = sdf.loc[ms, "t_in_trial"].to_numpy(float)
                vr_recs.append({"neuron": neuron, "pattern": p, "VR": _vr_dist(tx, ty, tau_ms)})
    vr_df = pd.DataFrame(vr_recs)
    vr_e = float(vr_df.loc[vr_df["neuron"] == out_col, "VR"].max()) if len(vr_df) else None

    kernel = _gaussian_kernel(sigma_ms, fs_hz)
    sch_recs = []
    for p in patterns:
        for tid in common_ids[p]:
            gdf = _get_trial(gt_data, tid)
            sdf = _get_trial(sub_data, tid)
            for neuron in spike_cols:
                mg = (gdf["t_in_trial"] >= 0) & (gdf["t_in_trial"] < trial_len)
                ms = (sdf["t_in_trial"] >= 0) & (sdf["t_in_trial"] < trial_len)
                if neuron not in gdf.columns or neuron not in sdf.columns:
                    continue
                a = gdf.loc[mg, neuron].to_numpy(np.float32)
                b = sdf.loc[ms, neuron].to_numpy(np.float32)
                if a.size == 0 or b.size == 0:
                    continue
                sch_recs.append({"neuron": neuron, "pattern": p, "r": _schreiber(a, b, kernel)})
    sch_df = pd.DataFrame(sch_recs)
    sch_e = float(sch_df.loc[sch_df["neuron"] == out_col, "r"].min()) if len(sch_df) else None

    vm_cols = [f"{n}_vm" for n in IO_NEURONS if f"{n}_vm" in gt_data.columns]
    vm_rmse_df = artifacts.get("vm_csv")
    if vm_rmse_df is None or vm_rmse_df.empty:
        vm_rmse_df = _vm_rmse_io(gt_data, sub_data, vm_cols, common_ids, patterns, trial_len)
    else:
        vm_rmse_df = vm_rmse_df.copy()
        if "pattern" in vm_rmse_df.columns:
            vm_rmse_df["pattern"] = vm_rmse_df["pattern"].map(_normalize_pattern)
        if "neuron_vm" in vm_rmse_df.columns:
            vm_rmse_df["neuron"] = vm_rmse_df["neuron_vm"].str.replace("_vm", "", regex=False)

    mm_rows = []
    for col in vm_cols:
        rms_vals = []
        for p in patterns:
            for tid in common_ids[p]:
                g = _get_trial(gt_data, tid)[col].to_numpy(float)
                s = _get_trial(sub_data, tid)[col].to_numpy(float)
                n = min(len(g), len(s))
                if n == 0:
                    continue
                d = g[:n] - s[:n]
                rms_vals.append(float(np.sqrt(np.nanmean(d * d))))
        mm_rows.append({
            "neuron": col.replace("_vm", ""),
            "RMS_mean": float(np.mean(rms_vals)) if rms_vals else 0.0,
            "RMS_max": float(np.max(rms_vals)) if rms_vals else 0.0,
        })
    mm_df = pd.DataFrame(mm_rows)

    io_spike_cols = [f"{n}_spike" for n in IO_NEURONS if f"{n}_spike" in spike_cols]
    try:
        psth_rows = []
        for col in io_spike_cols or [out_col]:
            psth_rows.append(
                _psth_summary(gt_data, sub_data, col, patterns, common_ids, trial_len, fs_hz, bin_ms=5)
            )
        psth_df = pd.concat(psth_rows, ignore_index=True) if psth_rows else pd.DataFrame()
    except Exception:
        psth_df = pd.DataFrame()

    try:
        spike_gt = _spike_count_table(gt_data, spike_cols, patterns, common_ids, trial_len, "GT")
        spike_sub = _spike_count_table(sub_data, spike_cols, patterns, common_ids, trial_len, "SUB")
        spike_counts = pd.concat([spike_gt, spike_sub], ignore_index=True)
    except Exception:
        spike_counts = pd.DataFrame()

    try:
        isi_gt = _isi_fano_summary(gt_spikes, cfg, gt_data, patterns)
        isi_sub = _isi_fano_summary(sub_spikes, cfg, sub_data, patterns)
        isi_gt["model"] = "GT"
        isi_sub["model"] = "SUB"
        isi_df = pd.concat([isi_gt, isi_sub], ignore_index=True)
    except Exception:
        isi_df = pd.DataFrame()

    granger_rows = []
    sc_gc = [c for c in spike_cols if c in gt_data.columns]
    for p in patterns:
        try:
            gt_trials = [_get_trial(gt_data, tid) for tid in common_ids[p]]
            sub_trials = [_get_trial(sub_data, tid) for tid in common_ids[p]]
            gc = _granger_jaccard(gt_trials, sub_trials, sc_gc, fs_hz)
            granger_rows.append({"pattern": p, **gc})
        except Exception:
            granger_rows.append({
                "pattern": p, "gt_edges": np.nan, "sub_edges": np.nan,
                "overlap": np.nan, "jaccard": np.nan,
            })
    granger_df = pd.DataFrame(granger_rows)

    cfg_io = _cfg_io_table(cfg)

    conclusions = []
    if sub_acc >= 0.999:
        conclusions.append("SUB passes XOR behavioral test (100% accuracy).")
    elif sub_acc >= 0.9:
        conclusions.append(f"SUB behavioral accuracy {sub_acc:.1%} — review failing patterns.")
    else:
        conclusions.append(f"SUB behavioral accuracy {sub_acc:.1%} — XOR failure.")
    if summary_json.get("mean_io_vm_rmse_mV") is not None:
        rmse = float(summary_json["mean_io_vm_rmse_mV"])
        conclusions.append(
            f"Mean I/O Vm RMSE = {rmse:.4f} mV."
            + (" Good voltage match." if rmse < 2.0 else " Voltage mismatch on I/O.")
        )
    if vr_e is not None:
        conclusions.append(
            f"Output E Van Rossum max = {vr_e:.6f} (τ={tau_ms} ms)."
            + (" Timing match." if vr_e < 0.05 else " Timing differs from GT.")
        )
    if sch_e is not None:
        conclusions.append(
            f"Output E Schreiber min r = {sch_e:.4f} (σ={sigma_ms} ms)."
            + (" Shape match." if sch_e > 0.95 else " Shape differs.")
        )
    if ks_max is not None:
        conclusions.append(
            f"Max KS statistic = {ks_max:.4f}."
            + (" Spike times align." if ks_max < 0.2 else " Spike-time mismatch detected.")
        )
    if len(granger_df):
        j_mean = float(granger_df["jaccard"].mean())
        conclusions.append(
            f"Mean Granger Jaccard across patterns = {j_mean:.3f} "
            "(low overlap expected for black-box SUB)."
        )

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "gt_path": gt_path,
        "sub_path": sub_path,
        "same_h5": same,
        "meta": meta,
        "patterns": patterns,
        "out_col": out_col,
        "spiking_neurons": spiking,
        "spike_cols": spike_cols,
        "cfg_io": cfg_io,
        "beh_full": beh_full,
        "sub_beh": sub_beh,
        "sub_accuracy": sub_acc,
        "sub_trials_correct": sub_tp + sub_tn,
        "sub_trials_total": sub_den,
        "summary_json": summary_json,
        "ks_df": ks_df,
        "ks_max": ks_max,
        "vr_df": vr_df,
        "vr_e": vr_e,
        "tau_ms": tau_ms,
        "sch_df": sch_df,
        "sch_e": sch_e,
        "sigma_ms": sigma_ms,
        "mm_df": mm_df,
        "vm_rmse_df": vm_rmse_df,
        "psth_df": psth_df,
        "spike_counts": spike_counts,
        "isi_df": isi_df,
        "granger_df": granger_df,
        "pipeline_vr_trials": artifacts.get("vr_csv"),
        "pipeline_sch_trials": artifacts.get("sch_csv"),
        "conclusions": conclusions,
    }


def _df_to_table_data(
    df: pd.DataFrame, max_rows: int = 80, float_prec: int = 4
) -> Tuple[List[List[str]], List[str]]:
    if df is None or df.empty:
        return [], []
    show = df.head(max_rows).copy()
    for c in show.columns:
        if show[c].dtype in (float, np.floating):
            show[c] = show[c].map(lambda v: _fmt_val(v, float_prec))
    headers = [str(c) for c in show.columns]
    rows = [[str(v) for v in row] for row in show.itertuples(index=False, name=None)]
    return [headers] + rows, headers


def _table_style(font_size: int = 7) -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])


def _add_table(story, df: pd.DataFrame, font_size: int = 7, max_rows: int = 80) -> None:
    data, headers = _df_to_table_data(df, max_rows=max_rows)
    if not data:
        return
    ncols = len(headers)
    page_w = letter[0] - 1.1 * inch
    if ncols > 8:
        font_size = max(5, font_size - 2)
    col_widths = [page_w / max(ncols, 1)] * ncols
    t = Table(data, repeatRows=1, colWidths=col_widths)
    t.setStyle(_table_style(font_size))
    story.append(t)


def _xml_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _add_section(story, title: str, h2, body, lines: Optional[List[str]] = None) -> None:
    story.append(Paragraph(title, h2))
    if lines:
        for line in lines:
            story.append(Paragraph(line, body))
    story.append(Spacer(1, 4))


def _matplotlib_png(fig) -> bytes:
    import matplotlib.pyplot as plt

    out = io.BytesIO()
    fig.savefig(out, format="png", dpi=120, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    out.seek(0)
    return out.getvalue()


def _pdf_chart_image(png_bytes: bytes, width_in: float = 6.3, height_in: float = 2.7):
    from reportlab.platypus import Image

    return Image(io.BytesIO(png_bytes), width=width_in * inch, height=height_in * inch)


def _chart_sub_accuracy(beh_full: pd.DataFrame, patterns: List[str]) -> Optional[bytes]:
    import matplotlib.pyplot as plt

    if beh_full is None or beh_full.empty:
        return None
    df = beh_full.copy()
    model_col = next((c for c in df.columns if str(c).lower() == "model"), None)
    if model_col is None:
        return None
    sub = df[df[model_col].astype(str).str.upper() == "SUB"]
    if sub.empty:
        return None
    pat_col = "Pattern" if "Pattern" in sub.columns else "pattern"
    if "Accuracy" not in sub.columns:
        return None
    fig, ax = plt.subplots(figsize=(6.5, 2.6))
    xs = [str(p) for p in sub[pat_col]]
    ax.bar(xs, sub["Accuracy"].astype(float), color="#58a6ff", edgecolor="#1f6feb")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Accuracy")
    ax.set_title("SUB behavioral accuracy by XOR pattern")
    ax.axhline(1.0, color="#3fb950", linestyle="--", linewidth=0.9, label="100% target")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    return _matplotlib_png(fig)


def _chart_vm_mismatch(mm_df: pd.DataFrame) -> Optional[bytes]:
    import matplotlib.pyplot as plt

    if mm_df is None or mm_df.empty:
        return None
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    x = mm_df["neuron"].astype(str)
    w = 0.38
    idx = np.arange(len(x))
    ax.bar(idx - w / 2, mm_df["RMS_mean"], width=w, label="Mean RMS Δ", color="#58a6ff")
    ax.bar(idx + w / 2, mm_df["RMS_max"], width=w, label="Max RMS Δ", color="#d29922")
    ax.set_xticks(idx)
    ax.set_xticklabels(x, rotation=45, ha="right")
    ax.set_ylabel("mV")
    ax.set_title("Vm mismatch per neuron (GT − SUB)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    return _matplotlib_png(fig)


def _chart_metric_heatmap(
    pivot: pd.DataFrame,
    title: str,
    cmap: str = "YlOrRd",
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    index_col: str = "neuron",
) -> Optional[bytes]:
    import matplotlib.pyplot as plt

    if pivot is None or pivot.empty:
        return None
    if index_col in pivot.columns:
        plot_df = pivot.set_index(index_col)
    else:
        plot_df = pivot.copy()
    data = plot_df.select_dtypes(include=[np.number]).to_numpy(dtype=float)
    if data.size == 0:
        return None
    fig_h = max(2.4, 0.38 * data.shape[0] + 1.2)
    fig, ax = plt.subplots(figsize=(6.5, fig_h))
    im = ax.imshow(data, aspect="auto", cmap=cmap, vmin=vmin, vmax=vmax)
    cols = [str(c) for c in plot_df.columns]
    rows = [str(i) for i in plot_df.index]
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    return _matplotlib_png(fig)


def _append_chart(story, png_bytes: Optional[bytes], caption: str = "", height_in: float = 2.7) -> None:
    if not png_bytes:
        return
    story.append(_pdf_chart_image(png_bytes, height_in=height_in))
    if caption:
        story.append(Paragraph(f"<i>{caption}</i>", ParagraphStyle(
            "ChartCap", fontSize=7, textColor=colors.grey, spaceAfter=6,
        )))


def build_pdf_bytes(ctx: Dict[str, Any]) -> bytes:
    if not _HAS_REPORTLAB:
        raise ImportError(
            "reportlab is required for PDF export. Install with: pip install reportlab"
        )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=10,
        textColor=colors.HexColor("#0d1117"),
    )
    h2 = ParagraphStyle(
        "H2Custom",
        parent=styles["Heading2"],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#1f2937"),
    )
    h3 = ParagraphStyle(
        "H3Custom",
        parent=styles["Heading3"],
        fontSize=9,
        spaceBefore=6,
        spaceAfter=3,
        textColor=colors.HexColor("#374151"),
    )
    body = ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )
    small = ParagraphStyle(
        "SmallCustom",
        parent=body,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#6b7280"),
    )

    story: List[Any] = []
    meta = ctx["meta"]
    patterns = ctx["patterns"]

    # ── Cover / overview ──
    story.append(Paragraph("XOR GT vs SUB — Detailed Metrics Report", title_style))
    story.append(Paragraph(f"Generated: {ctx['generated_at']}", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Ground truth:</b> {_xml_escape(ctx['gt_path'])}", small))
    story.append(Paragraph(f"<b>Submission:</b> {_xml_escape(ctx['sub_path'])}", small))
    story.append(Paragraph(
        f"<b>Mode:</b> {'Self-check (same H5)' if ctx['same_h5'] else 'GT vs SUB comparison'}",
        body,
    ))
    story.append(Paragraph(
        f"<b>Network:</b> {int(meta.get('n_neurons_total', 35))} neurons · "
        f"{len(ctx['spiking_neurons'])} spiking (runtime) · "
        f"{int(meta.get('n_trials', 40))} trials · "
        f"{int(meta.get('trial_len_ms', 100))} ms trial · "
        f"{int(meta.get('fs_hz', 1000))} Hz · "
        f"Patterns: {', '.join(patterns)}",
        body,
    ))
    story.append(Spacer(1, 8))

    _add_section(story, "Executive summary", h2, body, [
        f"• {line}" for line in ctx["conclusions"]
    ])
    sj = ctx.get("summary_json") or {}
    if sj:
        kpi_lines = []
        for key, label in (
            ("mean_io_vm_rmse_mV", "Pipeline mean I/O Vm RMSE (mV)"),
            ("mean_vr_output", "Pipeline mean Van Rossum (E)"),
            ("mean_schreiber_r_output", "Pipeline mean Schreiber r (E)"),
            ("tau_vr_ms", "Van Rossum τ (ms)"),
            ("schreiber_sigma_ms", "Schreiber σ (ms)"),
        ):
            if sj.get(key) is not None:
                kpi_lines.append(f"• {label}: {float(sj[key]):.4f}" if isinstance(sj[key], (int, float)) else f"• {label}: {sj[key]}")
        if kpi_lines:
            story.append(Paragraph("Pipeline summary (gt_sub_io_summary.json)", h3))
            for line in kpi_lines:
                story.append(Paragraph(line, body))

    story.append(Paragraph(BLACKBOX_NOTE, small))
    story.append(PageBreak())

    # ── I/O neuron roles ──
    _add_section(story, "1. I/O neurons compared", h2, body, [
        "Input/output neurons used for black-box evaluation:",
    ])
    _add_table(story, ctx["cfg_io"])
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Spiking neurons in GT runtime: {', '.join(ctx['spiking_neurons']) or '—'}",
        body,
    ))
    story.append(PageBreak())

    # ── Behavioral ──
    _add_section(story, "2. Behavioral accuracy (XOR truth table)", h2, body, [
        f"Output neuron: <b>{ctx['out_col'].replace('_spike', '')}</b>. "
        f"SUB pooled accuracy: <b>{ctx['sub_accuracy']:.1%}</b> "
        f"({ctx['sub_trials_correct']}/{ctx['sub_trials_total']} trials). "
        "Pass criterion: SUB accuracy = 100% on all four patterns.",
    ])
    _add_table(story, ctx["beh_full"])
    _append_chart(
        story,
        _chart_sub_accuracy(ctx["beh_full"], ctx["patterns"]),
        "Figure: SUB accuracy per pattern (from behavioral table).",
        height_in=2.5,
    )
    story.append(PageBreak())

    # ── Vm mismatch ──
    _add_section(story, "3. Membrane potential mismatch", h2, body, [
        "RMS ΔVm (mV) pooled across trials — summary per I/O neuron:",
    ])
    _add_table(story, ctx["mm_df"])
    _append_chart(
        story,
        _chart_vm_mismatch(ctx["mm_df"]),
        "Figure: mean and max RMS voltage error per neuron.",
        height_in=2.8,
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("RMSE per neuron × pattern (mV)", h3))
    vm_show = ctx["vm_rmse_df"].copy()
    if "neuron_vm" in vm_show.columns and "neuron" not in vm_show.columns:
        vm_show["neuron"] = vm_show["neuron_vm"].str.replace("_vm", "", regex=False)
    _add_table(story, _metric_pivot(vm_show, "rmse_mV", patterns, index_col="neuron", aggfunc="mean"))
    story.append(PageBreak())

    # ── Van Rossum ──
    _add_section(story, f"4. Van Rossum distance (τ = {ctx['tau_ms']:.0f} ms)", h2, body, [
        "Spike-timing distance. 0 = identical times. Lower is better.",
    ])
    if ctx["vr_e"] is not None:
        story.append(Paragraph(f"Output E max VR: <b>{ctx['vr_e']:.6f}</b>", body))
    story.append(Paragraph("Max VR per neuron × pattern", h3))
    vr_pivot = _metric_pivot(ctx["vr_df"], "VR", patterns, index_col="neuron", aggfunc="max")
    _append_chart(
        story,
        _chart_metric_heatmap(vr_pivot, f"Van Rossum max (τ={ctx['tau_ms']:.0f} ms)", "YlOrRd", 0, None),
        "Figure: darker = larger timing distance (0 = identical).",
        height_in=max(2.8, 0.35 * len(vr_pivot) + 1.5) if len(vr_pivot) else 2.8,
    )
    _add_table(story, vr_pivot)
    if ctx.get("pipeline_vr_trials") is not None and not ctx["pipeline_vr_trials"].empty:
        story.append(Spacer(1, 4))
        story.append(Paragraph("Output E — trial-level Van Rossum (pipeline CSV)", h3))
        vr_trials = ctx["pipeline_vr_trials"].copy()
        if "pattern" in vr_trials.columns:
            vr_trials["pattern"] = vr_trials["pattern"].map(_normalize_pattern)
        _add_table(story, vr_trials, max_rows=40)
    story.append(PageBreak())

    # ── Schreiber ──
    _add_section(story, f"5. Schreiber similarity (σ = {ctx['sigma_ms']:.0f} ms)", h2, body, [
        "Gaussian-smoothed spike-train correlation. 1 = identical shape.",
    ])
    if ctx["sch_e"] is not None:
        story.append(Paragraph(f"Output E min r: <b>{ctx['sch_e']:.4f}</b>", body))
    story.append(Paragraph("Min r per neuron × pattern", h3))
    sch_pivot = _metric_pivot(ctx["sch_df"], "r", patterns, index_col="neuron", aggfunc="min")
    _append_chart(
        story,
        _chart_metric_heatmap(sch_pivot, f"Schreiber min r (σ={ctx['sigma_ms']:.0f} ms)", "RdYlGn", 0, 1),
        "Figure: greener = more similar smoothed spike shape.",
        height_in=max(2.8, 0.35 * len(sch_pivot) + 1.5) if len(sch_pivot) else 2.8,
    )
    _add_table(story, sch_pivot)
    if ctx.get("pipeline_sch_trials") is not None and not ctx["pipeline_sch_trials"].empty:
        story.append(Spacer(1, 4))
        story.append(Paragraph("Output E — trial-level Schreiber r (pipeline CSV)", h3))
        sch_trials = ctx["pipeline_sch_trials"].copy()
        if "pattern" in sch_trials.columns:
            sch_trials["pattern"] = sch_trials["pattern"].map(_normalize_pattern)
        _add_table(story, sch_trials, max_rows=40)
    story.append(PageBreak())

    # ── KS ──
    _add_section(story, "6. Kolmogorov–Smirnov test (spike times)", h2, body, [
        "KS = 0 identical distributions; KS = 1 completely different.",
    ])
    if ctx["ks_max"] is not None:
        story.append(Paragraph(f"Global max KS: <b>{ctx['ks_max']:.4f}</b>", body))
    story.append(Paragraph("KS statistic per neuron × pattern", h3))
    ks_pivot = _metric_pivot(ctx["ks_df"], "ks_stat", patterns, index_col="neuron", aggfunc="max")
    _append_chart(
        story,
        _chart_metric_heatmap(ks_pivot, "KS statistic (max)", "YlOrRd", 0, 1),
        "Figure: 0 = identical spike-time distributions.",
        height_in=max(2.8, 0.35 * len(ks_pivot) + 1.5) if len(ks_pivot) else 2.8,
    )
    _add_table(story, ks_pivot)
    io_cols = {f"{n}_spike" for n in IO_NEURONS}
    ks_io = ctx["ks_df"][ctx["ks_df"]["neuron"].isin(io_cols)] if len(ctx["ks_df"]) else pd.DataFrame()
    if not ks_io.empty:
        story.append(Spacer(1, 4))
        story.append(Paragraph("I/O neurons — KS detail", h3))
        _add_table(story, ks_io)
    story.append(PageBreak())

    # ── PSTH ──
    _add_section(story, "7. PSTH correlation (bin = 5 ms)", h2, body, [
        "Pearson r between GT and SUB peri-stimulus time histograms (I/O neurons).",
    ])
    _add_table(story, ctx["psth_df"])
    if not ctx["psth_df"].empty:
        psth_pivot = _metric_pivot(ctx["psth_df"], "Pearson_r", patterns, index_col="neuron", aggfunc="mean")
        story.append(Spacer(1, 4))
        story.append(Paragraph("Mean Pearson r per neuron × pattern", h3))
        _append_chart(
            story,
            _chart_metric_heatmap(psth_pivot, "PSTH Pearson r (I/O neurons)", "RdYlGn", 0, 1),
            "Figure: PSTH curve similarity GT vs SUB.",
            height_in=max(2.6, 0.35 * len(psth_pivot) + 1.5) if len(psth_pivot) else 2.6,
        )
        _add_table(story, psth_pivot)
    story.append(PageBreak())

    # ── Spike counts ──
    _add_section(story, "8. Spike counts (trial window)", h2, body, [
        "Total spikes per neuron × pattern — GT vs SUB.",
    ])
    for model in ("GT", "SUB"):
        sub = ctx["spike_counts"][ctx["spike_counts"]["model"] == model]
        if sub.empty:
            continue
        story.append(Paragraph(f"{model}", h3))
        _add_table(story, _metric_pivot(sub, "spike_count", patterns, index_col="neuron", aggfunc="sum"))
        story.append(Spacer(1, 4))
    story.append(PageBreak())

    # ── ISI / Fano ──
    _add_section(story, "9. ISI variability & Fano factor", h2, body, [
        "ISI CV and Fano factor per neuron × pattern (spiking neurons only).",
    ])
    for model in ("GT", "SUB"):
        sub = ctx["isi_df"][ctx["isi_df"]["model"] == model]
        if sub.empty:
            continue
        story.append(Paragraph(f"{model} — mean CV / Fano", h3))
        isi_mean = sub.groupby("neuron")[["ISI_CV", "Fano"]].mean().reset_index()
        _add_table(story, isi_mean)
        story.append(Spacer(1, 4))
    story.append(PageBreak())

    # ── Granger ──
    _add_section(story, "10. Granger causality summary", h2, body, [
        "Binned Granger maps (bin=5 ms, lag=10, FDR α=0.05). "
        "Low Jaccard overlap is expected for black-box SUB.",
    ])
    _add_table(story, ctx["granger_df"])

    # ── Interpretation guide ──
    story.append(PageBreak())
    _add_section(story, "Appendix — How to read this report", h2, body)
    guide = [
        ("Tier 1 — Must pass", "SUB behavioral accuracy = 100% on patterns 00, 01, 10, 11."),
        ("Tier 2 — I/O fidelity", "I/O Vm RMSE, Van Rossum on E, Schreiber r on E, PSTH correlation."),
        ("Tier 3 — Diagnostics", "KS, ISI/Fano, spike counts, Granger (informative but not pass/fail for black-box)."),
        ("Evaluation order", "1) Behavioral → 2) Vm RMSE → 3) Van Rossum/Schreiber on E → 4) PSTH → 5) KS/Granger."),
    ]
    for title, text in guide:
        story.append(Paragraph(f"<b>{title}:</b> {text}", body))
        story.append(Spacer(1, 3))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "<i>Summary charts above use fixed report views (I/O-focused heatmaps, default τ/σ). "
        "Interactive combinations (Vm traces, rasters, CCG, per-pattern Granger heatmaps) "
        "remain in the Streamlit dashboard.</i>",
        small,
    ))

    doc.build(story)
    return buf.getvalue()


def generate_pdf_report(gt_path: str, sub_path: str) -> bytes:
    try:
        ctx = collect_report_context(gt_path, sub_path)
        return build_pdf_bytes(ctx)
    except Exception as exc:
        raise RuntimeError(f"PDF build failed: {exc}") from exc

