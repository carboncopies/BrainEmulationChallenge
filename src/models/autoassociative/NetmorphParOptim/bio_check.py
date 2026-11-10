"""Biological-realism checker for Netmorph parameter sets.

Reads bio_ranges.json (each number tagged docs / prior_work / assumption).
Usable as a library (check_row, check_frame, bio_ok_mask) or CLI:
    python bio_check.py candidates.xlsx
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_JSON = os.path.join(HERE, "bio_ranges.json")


def load_ranges(path=DEFAULT_JSON):
    with open(path) as f:
        return json.load(f)


def clean_columns(df):
    """Strip whitespace from column names ('dm.weight ' in Phase0 files)."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def derived_quantities(df, cfg=None):
    """Return DataFrame with volume_mm3, interneuron_used, density, pyr_fraction."""
    cfg = cfg or load_ranges()
    df = clean_columns(df)
    out = pd.DataFrame(index=df.index)
    vol_um3 = math.pi * df["shape.radius"].astype(float) ** 2 * df["shape.thickness"].astype(float)
    out["volume_mm3"] = vol_um3 * 1e-9
    if "interneuron" in df.columns:
        inter = df["interneuron"].astype(float)
        out["interneuron_imputed"] = False
    else:
        f = cfg["derived_checks"]["assumed_interneuron_fraction_if_column_missing"]["value"]
        inter = df["pyramidal"].astype(float) * f / (1 - f)
        out["interneuron_imputed"] = True
    out["interneuron_used"] = inter
    tot = df["pyramidal"].astype(float) + inter
    out["density_per_mm3"] = tot / out["volume_mm3"]
    out["pyramidal_fraction"] = df["pyramidal"].astype(float) / tot
    return out


def check_frame(df, cfg=None, tol=1e-9):
    """Per-row checks. Returns DataFrame of booleans (True = violation) plus
    columns bio_hard_violations, bio_soft_violations, bio_ok (no hard violation),
    and the derived quantities. Columns missing from df are skipped."""
    cfg = cfg or load_ranges()
    df = clean_columns(df)
    d = derived_quantities(df, cfg)
    res = pd.DataFrame(index=df.index)
    hard, soft = [], []
    # 1. parameter permitted ranges (hard)
    for p, r in cfg["parameters"].items():
        if p in df.columns:
            v = df[p].astype(float)
            res["viol_range_" + p] = (v < r["min"] - tol) | (v > r["max"] + tol)
            hard.append("viol_range_" + p)
    # 2. density (WARNING only: team hard limits are the parameter ranges above)
    dc = cfg["derived_checks"]["neuron_density_per_mm3"]
    res["warn_density"] = (d.density_per_mm3 < dc["min"]) | (d.density_per_mm3 > dc["max"])
    soft.append("warn_density")
    # 3. pyramidal fraction (WARNING only)
    pc = cfg["derived_checks"]["pyramidal_fraction"]
    res["warn_pyr_fraction"] = (d.pyramidal_fraction < pc["min"] - 0.005) | (d.pyramidal_fraction > pc["max"] + 0.005)
    soft.append("warn_pyr_fraction")
    # 4. min separation vs soma size (soft, assumption)
    if "minneuronseparation" in df.columns:
        sr = cfg["derived_checks"]["soma_radius_um"]
        pr, ir = np.mean(sr["pyramidal"]), np.mean(sr["interneuron"])
        pf = d.pyramidal_fraction
        mean_r = pf * pr + (1 - pf) * ir
        res["warn_separation_vs_soma"] = df["minneuronseparation"].astype(float) < 2 * mean_r
        soft.append("warn_separation_vs_soma")
    res["bio_hard_violations"] = res[hard].sum(axis=1).astype(int)
    res["bio_soft_violations"] = res[soft].sum(axis=1).astype(int)
    res["bio_ok"] = res["bio_hard_violations"] == 0
    return pd.concat([res, d], axis=1)


def bio_ok_mask(df, cfg=None):
    return check_frame(df, cfg)["bio_ok"].values


def explain(row, include_warnings=False):
    """Human-readable list of hard violations (and optionally warnings) for one row of check_frame output."""
    pre = ("viol_", "warn_") if include_warnings else ("viol_",)
    return [c for c in row.index if c.startswith(pre) and bool(row[c])]


def assert_hard_limits(df, cfg=None, tol=1e-9):
    """Raise ValueError if any row of df leaves the HARD parameter limits (columns present are checked)."""
    cfg = cfg or load_ranges()
    df = clean_columns(df)
    bad = []
    for p, r in cfg["parameters"].items():
        if p in df.columns:
            v = df[p].astype(float)
            m = (v < r["min"] - tol) | (v > r["max"] + tol)
            bad += [(int(i), p, float(df.loc[i, p])) for i in df.index[m]]
    if bad:
        raise ValueError("hard limit violations (row, param, value): %s" % bad[:20])
    return True


def synapses_per_neuron_info(pred_count, n_source, kind, cfg=None):
    cfg = cfg or load_ranges()
    rng = cfg["derived_checks"]["synapses_per_neuron"].get(kind)
    per = pred_count / max(n_source, 1)
    return {"per_neuron": float(per), "docs_range": rng,
            "within": (rng is not None and rng[0] <= per <= rng[1])}


if __name__ == "__main__":
    f = sys.argv[1]
    df = pd.read_excel(f) if f.endswith("xlsx") else pd.read_csv(f)
    r = check_frame(df)
    print(r[["bio_ok", "bio_hard_violations", "bio_soft_violations", "density_per_mm3", "pyramidal_fraction"]].describe())
    print("fraction within HARD limits:", r["bio_ok"].mean())
    for w in [c for c in r.columns if c.startswith("warn_")]:
        print("warning %s: %d rows" % (w, int(r[w].sum())))
