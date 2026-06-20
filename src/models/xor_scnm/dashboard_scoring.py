"""
Weighted overall GT vs SUB score (/100) for the XOR metrics dashboard.
Category scores (0–10) × category weights → overall /100.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from scipy.stats import ks_2samp
except ImportError:
    ks_2samp = None

from pdf_report import (
    TRUTH,
    _granger_jaccard,
    _isi_fano_summary,
    _normalize_pattern,
    _psth_summary,
    _spike_times,
)

# Category weights (sum = 27); overall /100 = weighted avg category score × 10.
CATEGORY_WEIGHTS: Dict[str, float] = {
    "behavior": 20.0,
    "spiking": 2.0,
    "membrane": 1.0,
    "structure": 4.0,
}

CATEGORY_METRICS: Dict[str, List[str]] = {
    "behavior": ["behavior"],
    "spiking": [
        "fano_delta",
        "isi_cv_delta",
        "ks",
        "multi_scale_corr",
        "psth_corr",
        "psth_rmse",
        "raster_jaccard",
        "schreiber",
        "vr_distance",
    ],
    "membrane": ["vm_median_corr"],
    "structure": ["granger_jaccard", "xcorr_matrix_corr"],
}

IO_NEURONS = ("PyrIn_A", "PyrIn_B1", "PyrIn_B2", "E")


def _score_high(x: Optional[float], lo: float, hi: float) -> float:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 0.0
    if hi <= lo:
        return 0.0
    return float(np.clip((float(x) - lo) / (hi - lo) * 10.0, 0.0, 10.0))


def _score_low(x: Optional[float], lo: float, hi: float) -> float:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 0.0
    if hi <= lo:
        return 0.0
    return float(np.clip((hi - float(x)) / (hi - lo) * 10.0, 0.0, 10.0))


def _load_metadata(h5_path: str) -> dict:
    import h5py

    with h5py.File(h5_path, "r") as f:
        if "/metadata" in f:
            return dict(f["/metadata"].attrs)
        return dict(f.attrs)


def _load_truth_table(h5_path: str) -> dict:
    base = os.path.dirname(os.path.abspath(h5_path))
    candidates = [
        os.path.join(base, "network_config.json"),
        os.path.join(os.path.dirname(base), "network_config.json"),
        os.path.join(base, "GT", "network_config.json"),
        os.path.join(base, "output", "GT", "network_config.json"),
    ]
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            tt = raw.get("truth_table") or raw.get("truthTable")
            if isinstance(tt, dict):
                out = {}
                for k, v in tt.items():
                    pk = _normalize_pattern(k)
                    if isinstance(v, dict):
                        out[pk] = {
                            "input_A": int(v.get("input_A", v.get("A", 0))),
                            "input_B": int(v.get("input_B", v.get("B", 0))),
                            "expected_output": int(
                                v.get("expected_output", v.get("output", v.get("E", 0)))
                            ),
                        }
                if out:
                    return out
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return dict(TRUTH)


def _get_trial(data: pd.DataFrame, tid) -> pd.DataFrame:
    return data[data["trial_id"] == tid].reset_index(drop=True)


def _out_spike_col(cfg: pd.DataFrame, data: pd.DataFrame) -> str:
    outs = [f"{n}_spike" for n in cfg.loc[cfg["role"] == "output", "label"].astype(str)]
    for c in outs:
        if c in data.columns:
            return c
    for c in data.columns:
        if c.endswith("_spike"):
            return c
    return "E_spike"


def _io_spike_cols(spike_cols: List[str]) -> List[str]:
    names = {c.replace("_spike", "") for c in spike_cols}
    return [f"{n}_spike" for n in IO_NEURONS if n in names]


def _pooled_behavior_accuracy(
    data: pd.DataFrame,
    out_col: str,
    tmap: pd.DataFrame,
    patterns: List[str],
    trial_len: int,
    truth: dict,
) -> float:
    tp = fn = tn = fp = 0
    for p in patterns:
        row = truth.get(p) or TRUTH.get(p, {"expected_output": 0})
        want = int(row["expected_output"])
        ids = tmap[tmap["case"].astype(str) == str(p)]["trial_id"].tolist()
        for tid in ids:
            t = _get_trial(data, tid)
            fired = t[t["t_in_trial"] <= trial_len][out_col].sum() > 0 if out_col in t.columns else False
            have = 1 if fired else 0
            if want == 1 and have == 1:
                tp += 1
            elif want == 1 and have == 0:
                fn += 1
            elif want == 0 and have == 0:
                tn += 1
            else:
                fp += 1
    den = tp + fn + tn + fp
    return (tp + tn) / den if den else 0.0


def _raster_jaccard(
    gt_data: pd.DataFrame,
    sub_data: pd.DataFrame,
    spike_cols: List[str],
    trial_len: int,
) -> float:
    inter = union = 0
    tids = sorted(set(gt_data["trial_id"].unique()) & set(sub_data["trial_id"].unique()))
    for tid in tids:
        gt_t = _get_trial(gt_data, tid)
        sub_t = _get_trial(sub_data, tid)
        for col in spike_cols:
            if col not in gt_t.columns or col not in sub_t.columns:
                continue
            g = np.where(
                (gt_t["t_in_trial"] >= 0)
                & (gt_t["t_in_trial"] < trial_len)
                & (gt_t[col].to_numpy(int) == 1)
            )[0]
            s = np.where(
                (sub_t["t_in_trial"] >= 0)
                & (sub_t["t_in_trial"] < trial_len)
                & (sub_t[col].to_numpy(int) == 1)
            )[0]
            inter += len(np.intersect1d(g, s))
            union += len(np.union1d(g, s))
    return float(inter / union) if union > 0 else 1.0


def _bin_counts(vec, bin_ms: float, fs_hz: float) -> np.ndarray:
    x = np.asarray(vec, int)
    bs = max(1, int(round(bin_ms * fs_hz / 1000.0)))
    nb = len(x) // bs
    if nb == 0:
        return np.zeros(0, dtype=float)
    return x[: nb * bs].reshape(nb, bs).sum(1).astype(float)


def _safe_pearson(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.size != b.size or a.size == 0 or np.nanvar(a) <= 0 or np.nanvar(b) <= 0:
        return float("nan")
    am, bm = np.nanmean(a), np.nanmean(b)
    d = np.sqrt(np.nansum((a - am) ** 2) * np.nansum((b - bm) ** 2))
    return float(np.nansum((a - am) * (b - bm)) / d) if d > 0 else float("nan")


def _psth_io_means(
    gt_data,
    sub_data,
    io_cols: List[str],
    patterns: List[str],
    common_ids: dict,
    trial_len: int,
    fs_hz: float,
    bin_ms: float = 5.0,
) -> Tuple[float, float]:
    rs, rmses = [], []
    for col in io_cols:
        df = _psth_summary(gt_data, sub_data, col, patterns, common_ids, trial_len, fs_hz, bin_ms)
        if df.empty:
            continue
        rs.extend(df["Pearson_r"].dropna().tolist())
        rmses.extend(df["PSTH_RMSE"].dropna().tolist())
    mean_r = float(np.mean(rs)) if rs else float("nan")
    mean_rmse = float(np.mean(rmses)) if rmses else float("nan")
    return mean_r, mean_rmse


def _ks_max(spike_cols, gt_spikes, sub_spikes, patterns) -> float:
    if ks_2samp is None:
        return float("nan")
    stats = []
    for col in spike_cols:
        lbl = col.replace("_spike", "")
        for p in patterns:
            gt_t = _spike_times(gt_spikes, lbl, p)
            sub_t = _spike_times(sub_spikes, lbl, p)
            if len(gt_t) and len(sub_t):
                stats.append(float(ks_2samp(gt_t, sub_t).statistic))
    return float(np.max(stats)) if stats else 0.0


def _isi_fano_deltas(gt_spikes, sub_spikes, cfg, gt_data, patterns) -> Tuple[float, float]:
    gt_df = _isi_fano_summary(gt_spikes, cfg, gt_data, patterns)
    sub_df = _isi_fano_summary(sub_spikes, cfg, gt_data, patterns)
    if gt_df.empty or sub_df.empty:
        return float("nan"), float("nan")
    merged = gt_df.merge(sub_df, on=["neuron", "pattern"], suffixes=("_gt", "_sub"))
    if merged.empty:
        return float("nan"), float("nan")
    cv_delta = merged[["ISI_CV_gt", "ISI_CV_sub"]].dropna()
    fano_delta = merged[["Fano_gt", "Fano_sub"]].dropna()
    cv_d = float(np.mean(np.abs(cv_delta["ISI_CV_gt"] - cv_delta["ISI_CV_sub"]))) if len(cv_delta) else float("nan")
    f_d = float(np.mean(np.abs(fano_delta["Fano_gt"] - fano_delta["Fano_sub"]))) if len(fano_delta) else float("nan")
    return cv_d, f_d


def _gaussian_kernel(sigma_ms: float, fs_hz: float) -> np.ndarray:
    dt = 1000.0 / fs_hz
    ksz = max(3, int(round(6.0 * sigma_ms / dt)))
    if ksz % 2 == 0:
        ksz += 1
    half = ksz // 2
    t = (np.arange(ksz) - half) * dt
    g = np.exp(-0.5 * (t / sigma_ms) ** 2).astype(np.float64)
    g /= g.sum() if g.sum() else 1.0
    return g


def _schreiber_mean(
    gt_data,
    sub_data,
    neuron_cols: List[str],
    patterns: List[str],
    common_ids: dict,
    trial_len: int,
    fs_hz: float,
    sigma_ms: float = 10.0,
) -> float:
    kernel = _gaussian_kernel(sigma_ms, fs_hz)
    rs = []
    for p in patterns:
        for tid in common_ids[p]:
            gt_df = _get_trial(gt_data, tid)
            sb_df = _get_trial(sub_data, tid)
            for neuron in neuron_cols:
                if neuron not in gt_df.columns or neuron not in sb_df.columns:
                    continue
                mg = (gt_df["t_in_trial"] >= 0) & (gt_df["t_in_trial"] < trial_len)
                ms = (sb_df["t_in_trial"] >= 0) & (sb_df["t_in_trial"] < trial_len)
                a = gt_df.loc[mg, neuron].to_numpy(np.float32)
                b = sb_df.loc[ms, neuron].to_numpy(np.float32)
                if a.size == 0 or b.size == 0:
                    continue
                ca = np.convolve(a, kernel, mode="same")
                cb = np.convolve(b, kernel, mode="same")
                num = float(np.dot(ca, cb))
                den = float(np.sqrt(np.dot(ca, ca) * np.dot(cb, cb)))
                if den > 0:
                    rs.append(max(-1.0, min(1.0, num / den)))
    return float(np.mean(rs)) if rs else float("nan")


def _msc_mean_io(
    gt_data,
    sub_data,
    io_cols: List[str],
    patterns: List[str],
    common_ids: dict,
    trial_len: int,
    dt_ms: float,
) -> float:
    sigma_vals = np.array([1.0, 5.0, 10.0, 20.0, 50.0], dtype=float)
    rs = []

    def _gauss_kernel_sigma_samp(sig_samp: float) -> np.ndarray:
        ksz = max(3, int(round(6.0 * sig_samp)))
        if ksz % 2 == 0:
            ksz += 1
        x = np.linspace(-3.0 * sig_samp, 3.0 * sig_samp, ksz)
        g = np.exp(-(x**2) / 2.0)
        g /= g.sum()
        return g

    for p in patterns:
        for tid in common_ids[p]:
            gt_df = _get_trial(gt_data, tid)
            sb_df = _get_trial(sub_data, tid)
            for neuron in io_cols:
                if neuron not in gt_df.columns or neuron not in sb_df.columns:
                    continue
                a = gt_df[neuron].to_numpy(float)[:trial_len]
                b = sb_df[neuron].to_numpy(float)[:trial_len]
                sa, sb_ = int(a.sum()), int(b.sum())
                if sa == 0 and sb_ == 0:
                    rs.append(1.0)
                    continue
                if (sa == 0) != (sb_ == 0):
                    rs.append(0.0)
                    continue
                for sigma_ms in sigma_vals:
                    sig_samp = max(1e-6, float(sigma_ms / dt_ms))
                    g = _gauss_kernel_sigma_samp(sig_samp)
                    ca = np.convolve(a, g, mode="same")
                    cb = np.convolve(b, g, mode="same")
                    rs.append(_safe_pearson(ca, cb))
    clean = [r for r in rs if np.isfinite(r)]
    return float(np.mean(clean)) if clean else float("nan")


def _vr_mean_output(
    gt_data,
    sub_data,
    out_col: str,
    patterns: List[str],
    common_ids: dict,
    trial_len: int,
    tau_ms: float = 20.0,
) -> float:
    def vr_dist(tx, ty, tau):
        nx, ny = tx.size, ty.size
        if nx == 0 and ny == 0:
            return 0.0
        if nx == 0 or ny == 0:
            return float(np.sqrt((nx + ny) / (2.0 * tau)))
        diffs = np.abs(tx[:, None] - ty[None, :])
        sxy = np.exp(-diffs / float(tau)).sum()
        return float(np.sqrt(max((nx + ny - 2.0 * sxy) / (2.0 * tau), 0.0)))

    dists = []
    for p in patterns:
        for tid in common_ids[p]:
            gt_df = _get_trial(gt_data, tid)
            sb_df = _get_trial(sub_data, tid)
            if out_col not in gt_df.columns or out_col not in sb_df.columns:
                continue
            mg = (gt_df["t_in_trial"] >= 0) & (gt_df["t_in_trial"] < trial_len) & (gt_df[out_col] == 1)
            ms = (sb_df["t_in_trial"] >= 0) & (sb_df["t_in_trial"] < trial_len) & (sb_df[out_col] == 1)
            tx = gt_df.loc[mg, "t_in_trial"].to_numpy(float)
            ty = sb_df.loc[ms, "t_in_trial"].to_numpy(float)
            dists.append(vr_dist(tx, ty, tau_ms))
    return float(np.mean(dists)) if dists else float("nan")


def _vm_median_corr(
    gt_data: pd.DataFrame,
    sub_data: pd.DataFrame,
    patterns: List[str],
    common_ids: dict,
    trial_len: int,
) -> float:
    """Mean Pearson r between GT and SUB median Vm traces (I/O neurons)."""
    vm_cols = [f"{n}_vm" for n in IO_NEURONS if f"{n}_vm" in gt_data.columns and f"{n}_vm" in sub_data.columns]
    rs = []
    for col in vm_cols:
        for p in patterns:
            gt_mats, sub_mats = [], []
            for tid in common_ids[p]:
                gt_df = _get_trial(gt_data, tid)
                sb_df = _get_trial(sub_data, tid)
                if col not in gt_df.columns or col not in sb_df.columns:
                    continue
                gt_mats.append(gt_df[col].to_numpy(float)[:trial_len])
                sub_mats.append(sb_df[col].to_numpy(float)[:trial_len])
            if not gt_mats or not sub_mats:
                continue
            L = min(min(len(m) for m in gt_mats), min(len(m) for m in sub_mats))
            gt_med = np.nanmedian(np.stack([m[:L] for m in gt_mats]), 0)
            sub_med = np.nanmedian(np.stack([m[:L] for m in sub_mats]), 0)
            r = _safe_pearson(gt_med, sub_med)
            if np.isfinite(r):
                rs.append(r)
    return float(np.mean(rs)) if rs else float("nan")


def _xcorr_matrix_corr(
    gt_data: pd.DataFrame,
    sub_data: pd.DataFrame,
    spike_cols: List[str],
    patterns: List[str],
    common_ids: dict,
    trial_len: int,
    max_lag: int = 15,
) -> float:
    """Pearson r between flattened mean cross-correlogram matrices (GT vs SUB)."""

    def xcorr_norm(a, b, lag_max):
        if a.size == 0 or b.size == 0:
            return np.zeros(2 * lag_max + 1, dtype=float)
        w = int(min(a.size, b.size))
        if w <= 1:
            return np.zeros(2 * lag_max + 1, dtype=float)
        L = int(min(lag_max, w - 1))
        full = np.correlate(a.astype(float), b.astype(float), mode="full")
        l_full = np.arange(-(w - 1), w, dtype=int)
        sel = (l_full >= -L) & (l_full <= L)
        lags = l_full[sel]
        counts = full[sel].astype(float)
        eff = (w - np.abs(lags)).astype(float)
        eff[eff <= 0] = np.nan
        return np.where(np.isfinite(eff), counts / eff, 0.0)

    def mean_flat_ccg(data, ids):
        acc = None
        n = 0
        for tid in ids:
            df = _get_trial(data, tid)
            vecs = []
            for ci in spike_cols:
                for cj in spike_cols:
                    ai = (
                        df[ci].to_numpy(int)[:trial_len].astype(np.int8)
                        if ci in df.columns
                        else np.zeros(trial_len, np.int8)
                    )
                    bj = (
                        df[cj].to_numpy(int)[:trial_len].astype(np.int8)
                        if cj in df.columns
                        else np.zeros(trial_len, np.int8)
                    )
                    vecs.append(xcorr_norm(ai, bj, max_lag))
            if not vecs:
                continue
            mat = np.concatenate(vecs)
            acc = mat if acc is None else acc + mat
            n += 1
        return acc / n if acc is not None and n else None

    rs = []
    for p in patterns:
        ids = common_ids[p]
        gt_vec = mean_flat_ccg(gt_data, ids)
        sub_vec = mean_flat_ccg(sub_data, ids)
        if gt_vec is None or sub_vec is None:
            continue
        r = _safe_pearson(gt_vec, sub_vec)
        if np.isfinite(r):
            rs.append(r)
    return float(np.mean(rs)) if rs else float("nan")


def _build_category_tables(
    subscores: Dict[str, float],
) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    metric_rows = []
    category_rows = []
    weighted_sum = 0.0
    weight_sum = sum(CATEGORY_WEIGHTS.values())

    for cat, weight in CATEGORY_WEIGHTS.items():
        metrics = CATEGORY_METRICS[cat]
        subs = [subscores[m] for m in metrics if m in subscores]
        cat_score = float(np.mean(subs)) if subs else 0.0
        weighted = cat_score * weight
        weighted_sum += weighted
        category_rows.append(
            {
                "Category": cat,
                "CategoryScore (0-10)": round(cat_score, 3),
                "Weight": weight,
                "Weighted Points": round(weighted, 3),
            }
        )
        for m in metrics:
            metric_rows.append(
                {
                    "Category": cat,
                    "Metric": m,
                    "Subscore (0-10)": round(subscores.get(m, 0.0), 3),
                }
            )

    # Weighted average of category scores on 0–10 scale → ×10 for /100 display.
    overall = (weighted_sum / weight_sum * 10.0) if weight_sum > 0 else 0.0
    return pd.DataFrame(category_rows), pd.DataFrame(metric_rows), round(overall, 1)


def compute_overall_score(gt_path: str, sub_path: str) -> Dict[str, Any]:
    """Return overall /100, category + metric tables, and raw metric values."""
    gt_path = os.path.abspath(gt_path)
    sub_path = os.path.abspath(sub_path)

    gt_data = pd.read_hdf(gt_path, "/data")
    gt_spikes = pd.read_hdf(gt_path, "/spikes_raw")
    sub_data = pd.read_hdf(sub_path, "/data")
    sub_spikes = pd.read_hdf(sub_path, "/spikes_raw")
    cfg = pd.read_hdf(gt_path, "/network_config")
    tmap = pd.read_hdf(gt_path, "/trial_map")
    meta = _load_metadata(gt_path)
    trial_len = int(meta.get("trial_len_ms", meta.get("trial_length_ms", 100)))
    fs_hz = float(meta.get("fs_hz", meta.get("sampling_rate_hz", 1000.0)))
    dt_ms = 1000.0 / fs_hz
    patterns = [_normalize_pattern(p) for p in tmap["case"].unique()]
    common_ids = {p: tmap[tmap["case"].astype(str) == str(p)]["trial_id"].tolist() for p in patterns}
    spike_cols = sorted(
        {c for c in gt_data.columns if c.endswith("_spike")}
        | {c for c in sub_data.columns if c.endswith("_spike")}
    )
    truth = _load_truth_table(gt_path)
    out_col = _out_spike_col(cfg, gt_data)
    io_cols = _io_spike_cols(spike_cols) or [out_col]

    raw: Dict[str, float] = {}
    raw["behavior"] = _pooled_behavior_accuracy(sub_data, out_col, tmap, patterns, trial_len, truth)
    raw["raster_jaccard"] = _raster_jaccard(gt_data, sub_data, spike_cols, trial_len)
    psth_r, psth_rmse = _psth_io_means(
        gt_data, sub_data, io_cols, patterns, common_ids, trial_len, fs_hz
    )
    raw["psth_corr"] = psth_r
    raw["psth_rmse"] = psth_rmse
    raw["ks"] = _ks_max(spike_cols, gt_spikes, sub_spikes, patterns)
    cv_d, fano_d = _isi_fano_deltas(gt_spikes, sub_spikes, cfg, gt_data, patterns)
    raw["isi_cv_delta"] = cv_d
    raw["fano_delta"] = fano_d
    raw["multi_scale_corr"] = _msc_mean_io(
        gt_data, sub_data, io_cols, patterns, common_ids, trial_len, dt_ms
    )
    raw["schreiber"] = _schreiber_mean(
        gt_data, sub_data, io_cols, patterns, common_ids, trial_len, fs_hz
    )
    gt_trials = [_get_trial(gt_data, tid) for tid in sorted(gt_data["trial_id"].unique())]
    sub_trials = [_get_trial(sub_data, tid) for tid in sorted(sub_data["trial_id"].unique())]
    gc = _granger_jaccard(gt_trials, sub_trials, spike_cols, fs_hz)
    raw["granger_jaccard"] = float(gc.get("jaccard", float("nan")))
    raw["vr_distance"] = _vr_mean_output(
        gt_data, sub_data, out_col, patterns, common_ids, trial_len
    )
    raw["vm_median_corr"] = _vm_median_corr(
        gt_data, sub_data, patterns, common_ids, trial_len
    )
    raw["xcorr_matrix_corr"] = _xcorr_matrix_corr(
        gt_data, sub_data, spike_cols, patterns, common_ids, trial_len
    )

    subscores: Dict[str, float] = {
        "behavior": _score_high(raw["behavior"], 0.5, 1.0),
        "raster_jaccard": _score_high(raw["raster_jaccard"], 0.3, 1.0),
        "psth_corr": _score_high(raw["psth_corr"], 0.5, 1.0),
        "psth_rmse": _score_low(raw["psth_rmse"], 0.0, 2.0),
        "ks": _score_low(raw["ks"], 0.0, 0.5),
        "isi_cv_delta": _score_low(raw["isi_cv_delta"], 0.0, 1.0),
        "fano_delta": _score_low(raw["fano_delta"], 0.0, 2.0),
        "multi_scale_corr": _score_high(raw["multi_scale_corr"], 0.5, 1.0),
        "schreiber": _score_high(raw["schreiber"], 0.5, 1.0),
        "granger_jaccard": _score_high(raw["granger_jaccard"], 0.3, 1.0),
        "vr_distance": _score_low(raw["vr_distance"], 0.0, 0.5),
        "vm_median_corr": _score_high(raw["vm_median_corr"], 0.5, 1.0),
        "xcorr_matrix_corr": _score_high(raw["xcorr_matrix_corr"], 0.5, 1.0),
    }

    categories, metric_subscores, overall = _build_category_tables(subscores)
    return {
        "overall": overall,
        "categories": categories,
        "metric_subscores": metric_subscores,
        "raw": raw,
        "subscores": subscores,
    }

