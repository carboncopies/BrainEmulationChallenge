#metrics/voltage_dependent/Vm_visualization

#Membrane Potential Visualization - Stitched Traces and Statistical Views

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

from metrics.helper_functions import get_trial, get_vm_cols
# Maximum trials to show in stitched view (None = all)
MAX_TRIALS_PER_PATTERN_STITCH = None

def _median_iqr_over_trials(trials, idxs, col, trial_len):
    """
    Compute per-sample median and IQR across trials.
    Returns: (median, q25, q75) arrays of length trial_len
    """
    if not idxs:
        return None, None, None

    mat = []
    for i in idxs:
        if i >= len(trials):
            continue
        vec = trials[i][col].to_numpy(float)
        if len(vec) >= trial_len:
            mat.append(vec[:int(trial_len)])

    if not mat:
        return None, None, None

    M = np.vstack(mat)
    med = np.nanmedian(M, axis=0)
    q25 = np.nanpercentile(M, 25, axis=0)
    q75 = np.nanpercentile(M, 75, axis=0)
    return med, q25, q75

def _stitch_series(trials, idxs, col,trial_len, max_trials=None):
    """
    Concatenate trials end-to-end.
    Returns: (stitched_y, time_axis)
    """
    if not idxs:
        return np.array([]), np.array([])

    use = idxs if (max_trials is None) else idxs[:max_trials]
    chunks = []
    for i in use:
        vec = trials[i][col].to_numpy(float)[:trial_len]
        chunks.append(vec)

    if not chunks:
        return np.array([]), np.array([])

    y = np.concatenate(chunks)
    t = np.arange(y.size, dtype=float)
    return y, t

def _neuron_label(col):
    """Extract neuron name from column."""
    return col.replace("_vm", "")


plt.close("all")
def run(gt_data, sub_data, cfg, tmap, meta, truth_table):
    # Generate visualizations for each pattern and neuron
    trial_len = int(meta["trial_len_ms"])
    print("Membrane Potential Visualization - Stitched Traces and Statistical Views")
    patterns = tmap["case"].unique().tolist()
    for patt in patterns:
        common_ids = tmap[tmap["case"] == patt]["trial_id"].tolist()
        gt_trials_p  = [get_trial(gt_data,  trial_id=i) for i in common_ids]
        sub_trials_p = [get_trial(sub_data, trial_id=i) for i in common_ids]
        print(common_ids)
        for col in get_vm_cols(cfg, scope="active"):
            neuron = _neuron_label(col)

            # Compute statistics
            med_gt, q25_gt, q75_gt = _median_iqr_over_trials(gt_trials_p, range(len(gt_trials_p)), col, trial_len)
            med_sub, q25_sub, q75_sub = _median_iqr_over_trials(sub_trials_p, range(len(sub_trials_p)), col, trial_len)

            # Figure 1: GT stitched with median overlay
            y_gt, t_gt = _stitch_series(gt_trials_p, range(len(gt_trials_p)), col, trial_len,  MAX_TRIALS_PER_PATTERN_STITCH)
            fig, ax = plt.subplots(figsize=(12, 3.2))

            if y_gt.size:
                ax.plot(t_gt, y_gt, lw=0.6, label="GT stitched", alpha=0.9)

            if med_gt is not None:
                reps = int(np.ceil(max(1, y_gt.size) / trial_len))
                med_tile = np.tile(med_gt, reps)[:max(1, y_gt.size)]
                ax.plot(np.arange(med_tile.size), med_tile, lw=1.6, linestyle="--",
                    label="GT median", alpha=0.9)

            ax.set_title(f"{neuron} — GT Stitched (pattern {patt}) with Median")
            ax.set_xlabel("Sample (ms)")
            ax.set_ylabel("Vm (mV)")
            ax.grid(alpha=0.25)
            ax.legend(loc="upper right")
            plt.tight_layout()
            plt.show()

            # Figure 2: SUB stitched with median overlay
            y_sub, t_sub = _stitch_series(sub_trials_p, range(len(gt_trials_p)), col, trial_len, MAX_TRIALS_PER_PATTERN_STITCH)
            fig, ax = plt.subplots(figsize=(12, 3.2))

            if y_sub.size:
                ax.plot(t_sub, y_sub, lw=0.6, color="tab:orange", label="SUB stitched", alpha=0.9)

            if med_sub is not None:
                reps = int(np.ceil(max(1, y_sub.size) / trial_len))
                med_tile = np.tile(med_sub, reps)[:max(1, y_sub.size)]
                ax.plot(np.arange(med_tile.size), med_tile, lw=1.6, linestyle="--",
                    color="tab:blue", label="SUB median", alpha=0.9)

            ax.set_title(f"{neuron} — SUB Stitched (pattern {patt}) with Median")
            ax.set_xlabel("Sample (ms)")
            ax.set_ylabel("Vm (mV)")
            ax.grid(alpha=0.25)
            ax.legend(loc="upper right")
            plt.tight_layout()
            plt.show()

            # Figure 3: GT Median ± IQR
            x = np.arange(trial_len)
            fig, ax = plt.subplots(figsize=(10, 3.0))

            if med_gt is not None:
                ax.plot(x, med_gt, lw=2.0, label="GT median")
                if (q25_gt is not None) and (q75_gt is not None):
                    ax.fill_between(x, q25_gt, q75_gt, alpha=0.25, label="GT IQR")

            ax.set_title(f"{neuron} — Median ± IQR (GT) — Pattern {patt}")
            ax.set_xlabel("Time within trial (ms)")
            ax.set_ylabel("Vm (mV)")
            ax.grid(alpha=0.25)
            ax.legend(loc="upper right")
            plt.tight_layout()
            plt.show()

            # Figure 4: SUB Median ± IQR
            fig, ax = plt.subplots(figsize=(10, 3.0))

            if med_sub is not None:
                ax.plot(x, med_sub, lw=2.0, color="tab:orange", label="SUB median")
                if (q25_sub is not None) and (q75_sub is not None):
                    ax.fill_between(x, q25_sub, q75_sub, alpha=0.25, color="tab:orange", label="SUB IQR")

            ax.set_title(f"{neuron} — Median ± IQR (SUB) — Pattern {patt}")
            ax.set_xlabel("Time within trial (ms)")
            ax.set_ylabel("Vm (mV)")
            ax.grid(alpha=0.25)
            ax.legend(loc="upper right")
            plt.tight_layout()
            plt.show()
            plt.close(fig)


    pass
