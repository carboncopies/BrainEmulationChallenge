#!/usr/bin/env python3
"""
GT vs black-box SUB metrics (input/output neurons and XOR behavior only).

Reads two HDF5 files produced by ``build_h5.py`` (same schema). Uses
``/network_config`` and ``/trial_map`` from the GT file. Compares:

  - XOR behavioral confusion / accuracy / sensitivity / specificity (output neuron)
  - Membrane potential RMSE per I/O neuron, pooled and per pattern
  - Output spike train: Van Rossum distance and Schreiber correlation (trial-wise summaries)

Does not depend on the full ``in_domain_metrics.py`` notebook stack.

Example::

  python in_domain_gt_sub_metrics.py \\
    --gt output/GT/groundtruth.h5 \\
    --sub output/SUB/substitute.h5 \\
    --network-config output/GT/network_config.json \\
    --output output/METRICS
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Tuple

import h5py
import numpy as np
import pandas as pd


def load_metadata(h5_path: str) -> Dict[str, Any]:
    with h5py.File(h5_path, "r") as f:
        return dict(f["/metadata"].attrs)


def get_trial(data: pd.DataFrame, trial_id: int) -> pd.DataFrame:
    return data[data["trial_id"] == trial_id]


def get_trials_by_pattern(data: pd.DataFrame, pattern: str) -> List[pd.DataFrame]:
    out: List[pd.DataFrame] = []
    for r in sorted(data["rep"].unique()):
        sub = data[(data["case"] == pattern) & (data["rep"] == r)]
        if not sub.empty:
            out.append(sub)
    return out


def all_patterns_behaviour(
    data: pd.DataFrame,
    patterns: List[str],
    truth_table: Dict[str, Any],
    out_spike_col: str,
    trial_len: int,
) -> pd.DataFrame:
    rows = []
    for p in patterns:
        want_key = f"XOR_{p}"
        want = int(truth_table[want_key]["expected_output"])
        trials = get_trials_by_pattern(data, p)
        tp = fn = tn = fp = 0
        for tdf in trials:
            window = tdf[tdf["t_in_trial"] < trial_len]
            fired = int(window[out_spike_col].sum()) > 0
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
        rows.append(
            {
                "Pattern": p,
                "TP": tp,
                "FN": fn,
                "TN": tn,
                "FP": fp,
                "Accuracy": (tp + tn) / den if den else 0.0,
                "Sensitivity": tp / (tp + fn) if (tp + fn) else 0.0,
                "Specificity": tn / (tn + fp) if (tn + fp) else 0.0,
            }
        )
    return pd.DataFrame(rows)


def vm_rmse_io(
    gt: pd.DataFrame,
    sub: pd.DataFrame,
    vm_cols: List[str],
    tmap: pd.DataFrame,
    patterns: List[str],
    trial_len: int,
) -> pd.DataFrame:
    rows = []
    for patt in patterns:
        ids = tmap[tmap["case"] == patt]["trial_id"].tolist()
        for col in vm_cols:
            sq = []
            for tid in ids:
                g = get_trial(gt, tid)
                s = get_trial(sub, tid)
                n = min(len(g), len(s), trial_len)
                if n == 0:
                    continue
                d = g[col].to_numpy(float)[:n] - s[col].to_numpy(float)[:n]
                sq.append(float(np.mean(d * d)))
            rmse = float(np.sqrt(np.mean(sq))) if sq else float("nan")
            rows.append({"pattern": patt, "neuron_vm": col, "rmse_mV": rmse})
    return pd.DataFrame(rows)


def _spike_times_in_window(df: pd.DataFrame, col: str, lo_ms: float, hi_ms: float) -> np.ndarray:
    if col not in df.columns:
        return np.empty(0, dtype=float)
    mask = (df["t_in_trial"] >= lo_ms) & (df["t_in_trial"] < hi_ms)
    sp = df[col].to_numpy(dtype=int) == 1
    return df.loc[mask & sp, "t_in_trial"].to_numpy(dtype=float)


def van_rossum_distance(tx: np.ndarray, ty: np.ndarray, tau_ms: float) -> float:
    nx, ny = int(tx.size), int(ty.size)
    if nx == 0 and ny == 0:
        return 0.0
    if nx == 0 or ny == 0:
        return float(np.sqrt((nx + ny) / (2.0 * tau_ms)))
    diffs = np.abs(tx[:, None] - ty[None, :])
    sxy = float(np.exp(-diffs / float(tau_ms)).sum())
    d2 = (nx + ny - 2.0 * sxy) / (2.0 * float(tau_ms))
    return float(np.sqrt(max(d2, 0.0)))


def collect_vr_e(
    gt: pd.DataFrame,
    sub: pd.DataFrame,
    col: str,
    tmap: pd.DataFrame,
    patterns: List[str],
    trial_len: int,
    tau_ms: float,
) -> pd.DataFrame:
    recs = []
    for patt in patterns:
        for tid in tmap[tmap["case"] == patt]["trial_id"].tolist():
            g = get_trial(gt, tid)
            s = get_trial(sub, tid)
            tx = _spike_times_in_window(g, col, 0, trial_len)
            ty = _spike_times_in_window(s, col, 0, trial_len)
            recs.append(
                {
                    "pattern": patt,
                    "trial_id": tid,
                    "VR": van_rossum_distance(tx, ty, tau_ms),
                    "GT_spikes": int(tx.size),
                    "SUB_spikes": int(ty.size),
                }
            )
    return pd.DataFrame(recs)


def _gaussian_kernel(sigma_ms: float, fs_hz: float) -> np.ndarray:
    dt = 1000.0 / float(fs_hz)
    sig = float(sigma_ms)
    if sig <= 0:
        return np.array([1.0], dtype=np.float64)
    ksz = max(3, int(round(6.0 * sig / dt)))
    if ksz % 2 == 0:
        ksz += 1
    half = ksz // 2
    t = (np.arange(ksz) - half) * dt
    g = np.exp(-0.5 * (t / sig) ** 2).astype(np.float64)
    g /= float(g.sum()) if g.sum() else 1.0
    return g


def schreiber_r(a: np.ndarray, b: np.ndarray, kernel: np.ndarray) -> float:
    na, nb = int(a.sum() > 0), int(b.sum() > 0)
    if na == 0 and nb == 0:
        return 1.0
    if (na == 0) ^ (nb == 0):
        return 0.0
    if a.size == 0 or b.size == 0:
        return float("nan")
    ca = np.convolve(a.astype(float), kernel, mode="same")
    cb = np.convolve(b.astype(float), kernel, mode="same")
    num = float(np.dot(ca, cb))
    den = float(np.sqrt(np.dot(ca, ca) * np.dot(cb, cb)))
    if den == 0.0:
        return float("nan")
    return float(max(-1.0, min(1.0, num / den)))


def collect_schreiber_e(
    gt: pd.DataFrame,
    sub: pd.DataFrame,
    col: str,
    tmap: pd.DataFrame,
    patterns: List[str],
    trial_len: int,
    fs_hz: float,
    sigma_ms: float,
) -> pd.DataFrame:
    k = _gaussian_kernel(sigma_ms, fs_hz)
    recs = []
    for patt in patterns:
        for tid in tmap[tmap["case"] == patt]["trial_id"].tolist():
            g = get_trial(gt, tid)
            s = get_trial(sub, tid)
            mask = (g["t_in_trial"] >= 0) & (g["t_in_trial"] < trial_len)
            a = g.loc[mask, col].to_numpy(dtype=np.float32)
            b = s.loc[mask, col].to_numpy(dtype=np.float32)
            n = min(len(a), len(b))
            a, b = a[:n], b[:n]
            recs.append(
                {
                    "pattern": patt,
                    "trial_id": tid,
                    "r": schreiber_r(a, b, k),
                }
            )
    return pd.DataFrame(recs)


def main() -> None:
    p = argparse.ArgumentParser(description="GT vs SUB I/O + behaviour metrics")
    p.add_argument("--gt", required=True, help="Ground-truth HDF5 from build_h5")
    p.add_argument("--sub", required=True, help="Substitute HDF5 from build_h5")
    p.add_argument("--output", required=True, help="Directory for CSV/JSON summaries")
    p.add_argument(
        "--network-config",
        required=True,
        help="network_config.json (truth_table + roles)",
    )
    p.add_argument("--tau-vr-ms", type=float, default=20.0)
    p.add_argument("--schreiber-sigma-ms", type=float, default=10.0)
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "plots_gt_sub"), exist_ok=True)

    gt_path, sub_path = args.gt, args.sub
    gt_data = pd.read_hdf(gt_path, "/data")
    sub_data = pd.read_hdf(sub_path, "/data")
    cfg = pd.read_hdf(gt_path, "/network_config")
    tmap = pd.read_hdf(gt_path, "/trial_map")
    meta = load_metadata(gt_path)
    trial_len = int(meta["trial_len_ms"])

    with open(args.network_config, "r") as f:
        net = json.load(f)
    truth_table = net["truth_table"]

    inputs = cfg[cfg["role"] == "input"]["label"].tolist()
    outputs = cfg[cfg["role"] == "output"]["label"].tolist()
    if len(outputs) != 1:
        raise ValueError("Expected exactly one output neuron label in network_config")
    out_label = outputs[0]
    out_spike_col = f"{out_label}_spike"
    io_vm_cols = [f"{lbl}_vm" for lbl in inputs + outputs]

    patterns = sorted(tmap["case"].astype(str).unique().tolist())

    gt_beh = all_patterns_behaviour(gt_data, patterns, truth_table, out_spike_col, trial_len)
    sub_beh = all_patterns_behaviour(sub_data, patterns, truth_table, out_spike_col, trial_len)
    gt_beh.insert(0, "model", "GT")
    sub_beh.insert(0, "model", "SUB")
    beh = pd.concat([gt_beh, sub_beh], ignore_index=True)
    beh_path = os.path.join(args.output, "gt_sub_behavior_by_pattern.csv")
    beh.to_csv(beh_path, index=False)

    vm_df = vm_rmse_io(gt_data, sub_data, io_vm_cols, tmap, patterns, trial_len)
    vm_path = os.path.join(args.output, "gt_sub_io_vm_rmse.csv")
    vm_df.to_csv(vm_path, index=False)

    vr_df = collect_vr_e(
        gt_data, sub_data, out_spike_col, tmap, patterns, trial_len, args.tau_vr_ms
    )
    vr_path = os.path.join(args.output, "gt_sub_output_van_rossum_trials.csv")
    vr_df.to_csv(vr_path, index=False)

    sch_df = collect_schreiber_e(
        gt_data,
        sub_data,
        out_spike_col,
        tmap,
        patterns,
        trial_len,
        float(meta["fs_hz"]),
        args.schreiber_sigma_ms,
    )
    sch_path = os.path.join(args.output, "gt_sub_output_schreiber_trials.csv")
    sch_df.to_csv(sch_path, index=False)

    summary = {
        "gt_h5": os.path.abspath(gt_path),
        "sub_h5": os.path.abspath(sub_path),
        "io_neurons_vm": io_vm_cols,
        "output_spike_col": out_spike_col,
        "mean_io_vm_rmse_mV": float(vm_df["rmse_mV"].mean()) if not vm_df.empty else None,
        "mean_vr_output": float(vr_df["VR"].mean()) if not vr_df.empty else None,
        "mean_schreiber_r_output": float(sch_df["r"].mean()) if not sch_df.empty else None,
        "trial_len_ms": trial_len,
        "tau_vr_ms": args.tau_vr_ms,
        "schreiber_sigma_ms": args.schreiber_sigma_ms,
    }
    summ_path = os.path.join(args.output, "gt_sub_io_summary.json")
    with open(summ_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("GT vs SUB (I/O + behaviour)")
    print(beh.to_string(index=False))
    print("\nI/O Vm RMSE (mV)")
    print(vm_df.to_string(index=False))
    print("\nVan Rossum (output), mean:", summary["mean_vr_output"])
    print("Schreiber r (output), mean:", summary["mean_schreiber_r_output"])
    print(f"\nWrote: {beh_path}\n       {vm_path}\n       {vr_path}\n       {sch_path}\n       {summ_path}")


if __name__ == "__main__":
    main()
