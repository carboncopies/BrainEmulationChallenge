#!/usr/bin/env python
# coding: utf-8

# In[98]:


#Importing necessary libraries
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from scipy.stats import wasserstein_distance
from IPython.display import display
import numpy as np
import os
import h5py
import glob

os.makedirs("output/plots", exist_ok=True)
_plot_counter = [0]

def save_and_close(fig=None, name=None):
    _plot_counter[0] += 1
    if name is None:
        name = f"plot_{_plot_counter[0]:03d}"
    if fig is None:
        plt.savefig(f"output/plots/{name}.png", bbox_inches='tight')
    else:
        fig.savefig(f"output/plots/{name}.png", bbox_inches='tight')
    plt.close('all')

current_dir = os.getcwd()

#Loading GT and SUB Data
try:
    #Output/GT_h5/groundtruth.h5
    folder_dir = "output/GT_h5"
    h5_file_path = os.path.join(current_dir, "output", "GT_h5", "groundtruth.h5")
    gt_data  = pd.read_hdf(h5_file_path, "/data")
    print("Voltage Data Loading done!")
    gt_spikes = pd.read_hdf(h5_file_path,"/spikes_raw")
    print("Spikes Data Loading done!")

    sub_data = gt_data.copy()
    sub_spikes = gt_spikes.copy()

    #Common to both GT and SUB
    cfg  = pd.read_hdf(h5_file_path, "/network_config")
    print("Network configuration Loading done!")
    tmap = pd.read_hdf(h5_file_path, "/trial_map")
    print("Trial Map Loading done!")

    import json

    acq_folders = sorted(glob.glob("output/*-acquisition"))
    if not acq_folders:
        raise FileNotFoundError("No acquisition folders found in output/")
    latest_folder = acq_folders[-1]

    with open(os.path.join(latest_folder, "network_config.json"), "r") as f:
        net_config = json.load(f)
    truth_table = net_config["truth_table"]

except Exception as e:
    print(f"Data laoding failed as {e}")


# In[99]:


try:
    # verify GT and SUB have same number of trials
    assert len(gt_data["trial_id"].unique()) == len(sub_data["trial_id"].unique())

    # verify pattern distribution is identical
    assert (gt_data.groupby("case").size() == sub_data.groupby("case").size()).all()

except Exception as e:
    print(e)


# In[ ]:


#Helper Functions
def get_neurons(cfg, role=None, input_channel=None):
    #     role="output"                 - ["E"]
    #     role="input"                  - ["PyrIn_A","PyrIn_B1","PyrIn_B2"]
    #     role=["input","interneuron",
    #           "intermediate","output"]- all 8 active neurons
    #     role="all"                    - all 35 labels
    #     input_channel=2               - ["PyrIn_B1","PyrIn_B2"]
    result = cfg
    if role!= None and role!= "all":
        if isinstance(role, list):
            result = result[result["role"].isin(role)]
        else:
            result = result[result["role"] == role]

    if input_channel!= None:
        result = result[result["input_channel"] == input_channel]

    return result["label"].tolist()

def get_spiking_neurons(cfg, data, label = None):
    #     checks _spike cols in data at runtime
    #     returns labels where spike col sum > 0
    spiking = []

    if label == None:
        for _ in cfg["label"]:
            if data[f"{_}_spike"].sum()>0:
                spiking.append(_)
    else:
        if data[label].sum() > 0:
            spiking.append(label)

    return spiking

def get_spike_cols(cfg, data, role =None):
   #     calls get_spiking_neurons()
   #     returns ["{label}_spike", ...] for spiking neurons
   columns = []

   if role == None:
        for label in get_spiking_neurons(cfg,data):
            columns.append(f"{label}_spike")

   else:
        for label in get_neurons(cfg, role=role):
            columns.append(f"{label}_spike")

   return columns

def get_vm_cols(cfg, scope="all"):
    #     scope="all"    - all 35 _vm column names
    #     scope="active" - 8 active neurons _vm column names
    roles = []
    if(scope == "active"):
        for _,row in cfg.iterrows():
            if row["role"] != "extended_network":
                roles.append(f"{row['label']}_vm")
    else:
        for _,row in cfg.iterrows():
            roles.append(f"{row['label']}_vm")
    return roles

def get_trial(data, trial_id):
    return data[data["trial_id"] == trial_id]

def get_trials_by_pattern(data, pattern):
    #     returns list of DataFrames where case == pattern
    #     10 DataFrames per pattern (one per rep)
    result = []
    unique = data["rep"].unique()
    for u in unique:
        filtered = data[(data["case"] == pattern) & (data["rep"] == u)]
        result.append(filtered)

    return result

def load_metadata(h5_path):
    #     reads /metadata attrs via h5py
    #     returns plain dict:
    #       {"fs_hz": 1000.0, "t_total_ms": 4000.0, "n_trials": 40,
    #        "trial_len_ms": 100.0, "n_neurons_total": 35, "n_neurons_spiking": 8}
    with h5py.File(h5_path,"r") as f:
        metadata = dict(f["/metadata"].attrs)

    return metadata


# In[ ]:


#Initializing common stuff that gets repeated

spike_cols = list(set(get_spike_cols(cfg, gt_data)) | set(get_spike_cols(cfg, sub_data)))

patterns = tmap["case"].unique().tolist()

for patt in patterns:
    common_ids = tmap[tmap["case"] == patt]["trial_id"].tolist()


# In[100]:


#Behavioural Metrics
#This metric needs the output neuron

# Get output neuron spike column and trial length from metadata
role_behavioural = "output"
label = get_spike_cols(cfg, gt_data, role=role_behavioural)[0]
meta = load_metadata(h5_file_path)
trial_len = int(meta["trial_len_ms"])

def compute_confusion_matrix(data,pattern):
    """
    For a given pattern, loops over all 10 repetitions and checks
    whether E fired within the trial window. Classifies each trial
    as TP, FN, TN or FP based on the truth table.
    """
    trials = get_trials_by_pattern(data,pattern)
    TP, FN, TN, FP = 0, 0, 0, 0
    for t in trials:
        #print(t["t_in_trial"])
        window = t[t["t_in_trial"] <= trial_len]
        fired = window[label].sum() > 0
        want = truth_table[f"XOR_{pattern}"]["expected_output"]
        have = 1 if fired else 0

        if want == 1 and have == 1:
            TP += 1
        elif want == 1 and have == 0:
            FN += 1
        elif want == 0 and have == 0:
            TN += 1
        else:
            FP += 1

    return TP,FN,TN,FP

def all_patterns(data,patterns):
    """
    Runs compute_confusion_matrix() for all 4 XOR patterns.
    patterns derived from tmap — not hardcoded.
    Returns a DataFrame with TP/FN/TN/FP and derived metrics per pattern.
    """     
    rows = []
    for p in patterns:
        tp,fn,tn,fp = compute_confusion_matrix(data,p)
        den = tp + fn + tn + fp
        rows.append({
            "Pattern": p,
            "TP": tp, "FN": fn, "TN": tn, "FP": fp,
            "Accuracy": (tp + tn) / den if den else 0.0,
            "Sensitivity": tp / (tp + fn) if (tp + fn) else 0.0,
            "Specificity": tn / (tn + fp) if (tn + fp) else 0.0,
        })

    return pd.DataFrame(rows)

print("Behavioural Metrics")
print(pd.DataFrame(truth_table))
gt_results = all_patterns(gt_data,patterns)
sub_results = all_patterns(sub_data,patterns)
print("Ground Truth:")
print(gt_results.to_string(index=False))
print("\nSubmission:")
print(sub_results.to_string(index=False))


# In[101]:


#Membrane Potential Visualization - Stitched Traces and Statistical Views

# Maximum trials to show in stitched view (None = all)
MAX_TRIALS_PER_PATTERN_STITCH = None

def _median_iqr_over_trials(trials, idxs, col):
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

def _stitch_series(trials, idxs, col, max_trials=None):
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


# Generate visualizations for each pattern and neuron
print("Membrane Potential Visualization - Stitched Traces and Statistical Views")
for patt in patterns:
    common_ids = tmap[tmap["case"] == patt]["trial_id"].tolist()
    gt_trials_p  = [get_trial(gt_data,  trial_id=i) for i in common_ids]
    sub_trials_p = [get_trial(sub_data, trial_id=i) for i in common_ids]
    print(common_ids)
    for col in get_vm_cols(cfg, scope="active"):
        neuron = _neuron_label(col)

        # Compute statistics
        med_gt, q25_gt, q75_gt = _median_iqr_over_trials(gt_trials_p, range(len(gt_trials_p)), col)
        med_sub, q25_sub, q75_sub = _median_iqr_over_trials(sub_trials_p, range(len(sub_trials_p)), col)

        # Figure 1: GT stitched with median overlay
        y_gt, t_gt = _stitch_series(gt_trials_p, range(len(gt_trials_p)), col, MAX_TRIALS_PER_PATTERN_STITCH)
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
        save_and_close()

        # Figure 2: SUB stitched with median overlay
        y_sub, t_sub = _stitch_series(sub_trials_p, range(len(gt_trials_p)), col, MAX_TRIALS_PER_PATTERN_STITCH)
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
        save_and_close()

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
        save_and_close()

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
        save_and_close()


# In[102]:


#Raster Plot Visualization - Compare GT vs SUB spike patterns
gt_spike_cols  = set(get_spike_cols(cfg, gt_data))
sub_spike_cols = set(get_spike_cols(cfg, sub_data))
spike_cols = list(gt_spike_cols | sub_spike_cols)
trial_len  = int(meta["trial_len_ms"])                   

gt  = gt_data.copy()
sub = sub_data.copy()

FILTER_PATTERN = None

# Align lengths
n_rows = min(len(gt), len(sub))
gt = gt.iloc[:n_rows].reset_index(drop=True)
sub = sub.iloc[:n_rows].reset_index(drop=True)

# Extract spike times
gt_times = [np.where(gt[c].to_numpy(dtype=int) == 1)[0] for c in spike_cols]
sb_times = [np.where(sub[c].to_numpy(dtype=int) == 1)[0] for c in spike_cols]
diff_times = [np.setxor1d(g, s) for g, s in zip(gt_times, sb_times)]

print("Raster Plot Visualization - Compare GT vs SUB spike patterns")

def add_pattern_bands(ax, df, trial_len=100, alpha=0.10):
    """Add colored background bands to indicate input patterns."""
    import matplotlib.cm as cm
    unique_patterns = tmap["case"].unique()
    color_list = cm.Set3.colors[:len(unique_patterns)]
    colors = dict(zip(unique_patterns, [f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}" for r,g,b in color_list]))
    last_tid = int(df["trial_id"].iloc[-1])
    for tid in range(last_tid + 1):
        block = df[df["trial_id"] == tid]
        if block.empty:
            continue
        start = int(block.index.min())
        pat = str(block["case"].iloc[0])
        rect = Rectangle((start, -0.5), trial_len, len(spike_cols),
                        color=colors.get(pat, "#dddddd"), alpha=alpha, lw=0)
        ax.add_patch(rect)

# Figure 1: Overlay raster (GT and SUB)
fig, ax = plt.subplots(figsize=(12, 7))

if FILTER_PATTERN is None:
    add_pattern_bands(ax, gt, trial_len=trial_len, alpha=0.10)

ax.eventplot(gt_times, orientation="horizontal", linelengths=0.8, linewidths=0.9, colors="black")
ax.eventplot(sb_times, orientation="horizontal", linelengths=0.6, linewidths=0.9, colors="red")

ax.set_yticks(np.arange(len(spike_cols)))
ax.set_yticklabels(spike_cols)
ax.set_xlabel("Sample index (concatenated)")
ax.set_ylabel("Neuron")
ttl = "Raster — GT vs SUB" + (f" (pattern {FILTER_PATTERN})" if FILTER_PATTERN else " (all patterns shaded)")
ax.set_title(ttl)

# Legend
handles = [Line2D([0],[0], color="black", lw=2, label="GT"),
           Line2D([0],[0], color="red", lw=2, label="SUB")]
ax.legend(handles=handles, loc="upper right")

# Trial separators
total_trials = int(np.ceil(n_rows / trial_len))
for k in range(1, total_trials):
    ax.axvline(k * trial_len, color="0.85", lw=0.5, zorder=0)

plt.tight_layout()
save_and_close()

# Figure 2: Differences-only raster
fig, ax = plt.subplots(figsize=(12, 7))

if FILTER_PATTERN is None:
    add_pattern_bands(ax, gt, trial_len=trial_len, alpha=0.10)

ax.eventplot(diff_times, orientation="horizontal", linelengths=0.8, linewidths=0.9, colors="purple")
ax.set_yticks(np.arange(len(spike_cols)))
ax.set_yticklabels(spike_cols)
ax.set_xlabel("Sample index (concatenated)")
ax.set_ylabel("Neuron")
ax.set_title("Raster: Differences Only (GT ⊕ SUB)" + (f" (pattern {FILTER_PATTERN})" if FILTER_PATTERN else ""))

for k in range(1, total_trials):
    ax.axvline(k * trial_len, color="0.85", lw=0.5, zorder=0)

plt.tight_layout()
save_and_close()

# Numeric insights
def jaccard(a_idx, b_idx):
    """Compute Jaccard similarity between two spike index arrays."""
    if len(a_idx) == 0 and len(b_idx) == 0:
        return 1.0
    if len(a_idx) == 0 or len(b_idx) == 0:
        return 0.0
    inter = len(np.intersect1d(a_idx, b_idx))
    uni = len(np.union1d(a_idx, b_idx))
    return inter / uni if uni > 0 else 0.0

# Per-neuron Jaccard similarity
J = np.array([jaccard(g, s) for g, s in zip(gt_times, sb_times)], float)
mismatch_counts = {name: int(len(d)) for name, d in zip(spike_cols, diff_times)}
meanJ = float(np.nanmean(J)) if np.isfinite(J).any() else float("nan")

print("\nJaccard similarity per neuron:")
for name, val in zip(spike_cols, J):
    print(f"  {name:<18} {('%.3f'%val) if np.isfinite(val) else 'NA'}")
print(f"Mean Jaccard: {meanJ:.3f}" if np.isfinite(meanJ) else "Mean Jaccard: NA")

print("\nDifference counts (GT⊕SUB) per neuron:")
for k, v in mismatch_counts.items():
    print(f"  {k:<18} {v}")

# Per-pattern Jaccard (when showing all patterns)
if FILTER_PATTERN is None:
    per_pat = {}
    for p in patterns:
        gtp = gt[gt["case"]==p]
        subp = sub[sub["case"]==p]
        n = min(len(gtp), len(subp))
        gtp = gtp.iloc[:n]
        subp = subp.iloc[:n]
        gts = [np.where(gtp[c].to_numpy(int)==1)[0] for c in spike_cols]
        sbs = [np.where(subp[c].to_numpy(int)==1)[0] for c in spike_cols]
        Jp = np.array([jaccard(a,b) for a,b in zip(gts,sbs)], float)
        per_pat[p] = float(np.nanmean(Jp))

    print("\nMean Jaccard by pattern:") 
    for p in patterns:
        print(f"  pattern {p}: {per_pat[p]:.3f}")    



# In[103]:


# PSTH Metric - Peristimulus Time Histogram Analysis

# Configuration
BIN_MS          = 5          # Bin size for PSTH
SMOOTH_FOR_PLOT = False      # Smooth for visualization only
SMOOTH_SIGMA    = 2.0        # Gaussian smoothing sigma (bins)

# Response-aligned window (ms relative to earliest input)
ALIGN_PRE_MS    = 10
ALIGN_POST_MS   = 80

# Thresholds for narrative
SMALL_RMSE      = 0.01
MODERATE_RMSE   = 0.03
HIGH_R_FLOOR    = 0.98
OK_R_FLOOR      = 0.90
LAT_MS_TOL      = 2.0

RESP_ALIGN_PATTERNS = [p for p in patterns
                       if truth_table[f"XOR_{p}"]["input_A"] > 0 
                       or truth_table[f"XOR_{p}"]["input_B"] > 0]
FOCUS_NEURONS = [n + "_spike" for n in get_neurons(cfg, role=["intermediate", "output"])]
SHOW_RATE     = False
RATE_SCALE    = 1000.0 / BIN_MS
LATENCY_METHOD = "com"
COM_FRAC      = 0.30

print("PSTH Metric - Peristimulus Time Histogram Analysis")

def _safe_pearson(a, b):
    """Compute Pearson correlation, handling edge cases."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.size != b.size or a.size == 0:
        return np.nan
    va = np.nanvar(a)
    vb = np.nanvar(b)
    if va <= 0 or vb <= 0:
        return np.nan
    am = np.nanmean(a)
    bm = np.nanmean(b)
    num = np.nansum((a - am) * (b - bm))
    den = np.sqrt(np.nansum((a - am)**2) * np.nansum((b - bm)**2))
    return float(num / den) if den > 0 else np.nan

def _rmse(a, b):
    """Compute RMSE between two arrays."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.size != b.size or a.size == 0:
        return np.nan
    d = a - b
    return float(np.sqrt(np.nanmean(d*d)))

def _gauss1d(sigma_bins, radius=3):
    """Create 1D Gaussian kernel for smoothing."""
    sig = float(max(1e-9, sigma_bins))
    rad = int(max(1, int(radius * sig)))
    x = np.arange(-rad, rad+1, 1.0)
    k = np.exp(-(x*x)/(2*sig*sig))
    k /= k.sum()
    return k

def _bin_counts(vec, bin_ms, fs):
    """Bin spike vector into counts."""
    x = np.asarray(vec, int)
    bin_size = int(max(1, round((bin_ms/1000.0) * fs)))
    nb = len(x) // bin_size
    if nb == 0:
        return np.zeros(0, float)
    xx = x[: nb*bin_size].reshape(nb, bin_size).sum(axis=1).astype(float)
    return xx


def _psth_per_pattern(data, patterns, col, bin_ms, fs):
    out = {}
    for p in patterns:
        use = tmap[tmap["case"] == p]["trial_id"].tolist()
        mats = []
        for i in use:
            v = get_trial(data, trial_id=i)[col].to_numpy(int)
            mats.append(_bin_counts(v, bin_ms, fs))
        if mats:
            L = min(map(len, mats))
            mats = [m[:L] for m in mats]
            out[p] = np.nanmean(np.stack(mats, axis=0), axis=0)
        else:
            out[p] = None
    return out

def _resp_aligned(trials_p, col, pre_ms, post_ms):
    pre  = int(pre_ms)
    post = int(post_ms)
    rows = []
    for trial_df in trials_p:
        vec = trial_df[col].to_numpy(int)
        s = max(0, 0 - pre)
        e = min(trial_len - 1, 0 + post)
        rows.append(vec[s:e+1].astype(float))
    if rows:
        mean_curve = np.nanmean(np.stack(rows, axis=0), axis=0)
        actual_len = e - s + 1
        t_axis = np.arange(s, s + actual_len, 1)
        return t_axis, mean_curve
    return None

def _latency_peak(t, y):
    """Peak latency (argmax)."""
    if y is None or t is None:
        return None
    y = np.asarray(y, float)
    t = np.asarray(t, float)
    if not np.isfinite(y).any():
        return None
    i = int(np.nanargmax(y))
    return float(t[i])

def _latency_com(t, y, frac=0.30):
    """Center-of-mass latency above fraction of peak."""
    if y is None or t is None:
        return None
    y = np.asarray(y, float)
    t = np.asarray(t, float)
    y = np.where(np.isfinite(y), y, 0.0)
    if y.size == 0 or not np.isfinite(y).any():
        return None
    peak = float(np.nanmax(y))
    thr = frac * peak
    y2 = np.where(y >= thr, y, 0.0)
    s = y2.sum()
    if s <= 0:
        return None
    return float((t * y2).sum() / s)

def _latency(t, y, method="com", frac=0.30):
    """Compute latency using specified method."""
    if method == "com":
        val = _latency_com(t, y, frac=frac)
        return val if val is not None else _latency_peak(t, y)
    else:
        return _latency_peak(t, y)

# Compute PSTHs (trial-paired)
GT_psths = {c: _psth_per_pattern(gt_data, patterns, c, BIN_MS, meta["fs_hz"]) for c in spike_cols}
SB_psths = {c: _psth_per_pattern(sub_data, patterns, c, BIN_MS, meta["fs_hz"]) for c in spike_cols}

# Setup smoothing for plots
if SMOOTH_FOR_PLOT:
    K = _gauss1d(SMOOTH_SIGMA)
    _smooth = lambda y: y if y is None or len(y) == 0 else np.convolve(y, K, mode="same")
else:
    _smooth = lambda y: y

_scale_for_plot = (lambda y: None if y is None else y * RATE_SCALE) if SHOW_RATE else (lambda y: y)
_ylabel = "spikes/s" if SHOW_RATE else "spikes/bin"

# Plot per-pattern PSTHs
for col in spike_cols:
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.2), sharey=True)
    fig.suptitle(f"PSTH per pattern — {col} (bin={BIN_MS} ms)")
    for j, p in enumerate(patterns):
        g = GT_psths[col][p]
        s = SB_psths[col][p]
        ax = axes[j]
        if g is not None:
            ax.plot(_scale_for_plot(_smooth(g)), label="GT", linewidth=1.8)
        if s is not None:
            ax.plot(_scale_for_plot(_smooth(s)), label="SUB", linewidth=1.8, linestyle="--")
        ax.set_title(f"pattern {p}")
        ax.set_xlabel("bin")
        if j == 0:
            ax.set_ylabel(_ylabel)
        ax.grid(alpha=0.25)
    axes[-1].legend(loc="upper right")
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    save_and_close()

# Plot response-aligned PSTHs
for col in FOCUS_NEURONS:
    fig, axes = plt.subplots(1, len(RESP_ALIGN_PATTERNS), figsize=(14, 3.2), sharey=True)
    fig.suptitle(f"Response-aligned PSTH — {col} (0 = earliest input)")
    for j, p in enumerate(RESP_ALIGN_PATTERNS):
        trial_ids    = tmap[tmap["case"] == p]["trial_id"].tolist()
        gt_trials_p  = [get_trial(gt_data,  trial_id=i) for i in trial_ids]
        sub_trials_p = [get_trial(sub_data, trial_id=i) for i in trial_ids]
        GT_resp = _resp_aligned(gt_trials_p, col, ALIGN_PRE_MS, ALIGN_POST_MS)
        SB_resp = _resp_aligned(sub_trials_p, col, ALIGN_PRE_MS, ALIGN_POST_MS)
        ax = axes[j]
        if GT_resp is not None:
            tg, yg = GT_resp
            ax.plot(tg, _scale_for_plot(_smooth(yg)), label="GT", linewidth=1.8)
        if SB_resp is not None:
            ts, ys = SB_resp
            ax.plot(ts, _scale_for_plot(_smooth(ys)), label="SUB", linewidth=1.8, linestyle="--")
        ax.set_title(f"pattern {p}")
        ax.set_xlabel("ms rel. to input")
        if j == 0:
            ax.set_ylabel(_ylabel.replace("/bin","/sample") if not SHOW_RATE else _ylabel)
        ax.axvline(0, color="k", lw=0.8, ls=":")
        ax.grid(alpha=0.25)
    axes[-1].legend(loc="upper right")
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    save_and_close()

# Compute numeric metrics
rows = []
perpat = {}
for col in spike_cols:
    # Overall metrics (concatenate all patterns)
    gt_vecs, sb_vecs = [], []
    for p in patterns:
        g = GT_psths[col][p]
        s = SB_psths[col][p]
        if g is None or s is None:
            continue
        L = min(len(g), len(s))
        gt_vecs.append(g[:L])
        sb_vecs.append(s[:L])

    if gt_vecs and sb_vecs:
        G_all = np.concatenate(gt_vecs)
        S_all = np.concatenate(sb_vecs)
        r_all = _safe_pearson(G_all, S_all)
        rmse_all = _rmse(G_all, S_all)
        bias_all = float(np.nanmean(G_all - S_all))
    else:
        r_all = rmse_all = bias_all = np.nan

    # Per-pattern metrics
    pp = {}
    for p in patterns:
        g = GT_psths[col][p]
        s = SB_psths[col][p]
        if (g is None) or (s is None) or (len(g)==0) or (len(s)==0):
            pp[p] = {"r": np.nan, "rmse": np.nan, "bias": np.nan}
        else:
            L = min(len(g), len(s))
            gg, ss = g[:L], s[:L]
            pp[p] = {
                "r": _safe_pearson(gg, ss),
                "rmse": _rmse(gg, ss),
                "bias": float(np.nanmean(gg - ss))
            }
    perpat[col] = pp

    rows.append({
        "Neuron": col,
        "Overall_r":            r_all,
        "Overall_RMSE":         rmse_all,
        "Overall_bias(GT-SUB)": bias_all,
        **{f"r_{p}":    pp[p]["r"]    for p in patterns},
        **{f"RMSE_{p}": pp[p]["rmse"] for p in patterns},
        **{f"bias_{p}": pp[p]["bias"] for p in patterns},
    })

psth_metrics = pd.DataFrame(rows)
with pd.option_context("display.max_columns", None):
    print("\n[PSTH metrics] (r, RMSE, bias) per neuron:")
    print(psth_metrics.round(4).to_string(index=False))

# Compute latencies for aligned curves
latency = {}
for col in FOCUS_NEURONS:
    lat = {}
    for p in RESP_ALIGN_PATTERNS:
        trial_ids    = tmap[tmap["case"] == p]["trial_id"].tolist()
        gt_trials_p  = [get_trial(gt_data,  trial_id=i) for i in trial_ids]
        sub_trials_p = [get_trial(sub_data, trial_id=i) for i in trial_ids]
        GTa = _resp_aligned(gt_trials_p, col, ALIGN_PRE_MS, ALIGN_POST_MS)
        SBa = _resp_aligned(sub_trials_p, col, ALIGN_PRE_MS, ALIGN_POST_MS)
        if GTa is None or SBa is None:
            lat[p] = np.nan
        else:
            tg, yg = GTa
            ts, ys = SBa
            lg = _latency(tg, yg, method=LATENCY_METHOD, frac=COM_FRAC)
            ls = _latency(ts, ys, method=LATENCY_METHOD, frac=COM_FRAC)
            lat[p] = np.nan if (lg is None or ls is None) else float(ls - lg)
    latency[col] = lat

# Generate narrative
def f3(x):
    """Format to 3 decimal places."""
    return "n/a" if not np.isfinite(x) else f"{x:.3f}"

def f3_signed(x):
    """Format with sign."""
    return "" if not np.isfinite(x) else f" ({x:+.3f})"

def bias_word(b):
    """Describe bias direction."""
    if not np.isfinite(b) or abs(b) < 1e-6:
        return "no bias"
    return "GT higher" if b > 0 else "SUB higher"

bullets = []

# Overall health per neuron
for _, row in psth_metrics.iterrows():
    n = row["Neuron"]
    r = row["Overall_r"]
    rm = row["Overall_RMSE"]
    b = row["Overall_bias(GT-SUB)"]
    grade = ("excellent" if (np.isfinite(r) and r >= HIGH_R_FLOOR)
             else "good" if (np.isfinite(r) and r >= OK_R_FLOOR)
             else "weak" if np.isfinite(r) else "n/a")
    bullets.append(
        f"{n}: shape {grade} (r={f3(r)}), "
        f"level mismatch RMSE={f3(rm)} spikes/bin, "
        f"bias={bias_word(b)}{f3_signed(b)}."
    )

# Worst pattern per neuron
for col in spike_cols:
    stats = perpat[col]
    rmse_vals = {p: (stats[p]['rmse'] if np.isfinite(stats[p]['rmse']) else -1) for p in patterns}
    worst = max(rmse_vals, key=rmse_vals.get)
    wv = stats[worst]
    if np.isfinite(wv["rmse"]) and wv["rmse"] > SMALL_RMSE:
        bias_txt = f3_signed(wv['bias']).strip() or '0.000'
        bullets.append(
            f"{col}: largest difference in pattern {worst} "
            f"(r={f3(wv['r'])}, RMSE={f3(wv['rmse'])}, bias={bias_txt})."
        )

# Latency differences
for col in FOCUS_NEURONS:
    for p in RESP_ALIGN_PATTERNS:
        dlat = latency[col][p]
        if np.isfinite(dlat) and abs(dlat) > LAT_MS_TOL:
            direction = "SUB earlier" if dlat < 0 else "SUB later"
            bullets.append(f"{col}@{p}: {direction} by ~{dlat:.1f} ms (latency).")

# Summary
output_neuron = get_neurons(cfg, role="output")[0] + "_spike"
worst_pattern = tmap[tmap["case"].isin(["00","11"])]["case"].unique()[0]
e11 = perpat[output_neuron][worst_pattern]

print("\n=== PSTH Auto-Narrative ===")
for b in bullets:
    print("•", b)

# Bundle results
PSTH_RESULTS = dict(
    bin_ms=BIN_MS,
    fs_hz=meta["fs_hz"],
    patterns=patterns,
    gt_psths=GT_psths,
    sub_psths=SB_psths,
    metrics=psth_metrics,
    latency=latency,
    config=dict(
        SMOOTH_FOR_PLOT=SMOOTH_FOR_PLOT, SMOOTH_SIGMA=SMOOTH_SIGMA,
        SHOW_RATE=SHOW_RATE, LATENCY_METHOD=LATENCY_METHOD, COM_FRAC=COM_FRAC
    )
)
AUTO_PSTH_REPORT = dict(
    psth_summary=psth_metrics,
    per_pattern=perpat,
    latency=latency,
    bullets=bullets,
    config=dict(BIN_MS=BIN_MS, ALIGN_PRE_MS=ALIGN_PRE_MS, ALIGN_POST_MS=ALIGN_POST_MS)
)
print("[PSTH] Results bundled: PSTH_RESULTS, AUTO_PSTH_REPORT")


# In[104]:


#ISI

try:
    from scipy.stats import wasserstein_distance
except Exception:
    wasserstein_distance = None

rows = []

print("ISI")

def compute_isi_metrics(data_spikes,data, cfg, patterns, tmap):
    rows = []
    for neuron in get_spiking_neurons(cfg, data):
        for p in patterns:
            spike_times = data_spikes[
                (data_spikes["label"] == neuron) & 
                (data_spikes["pattern"] == p)
            ]["spike_time_ms"].to_numpy()

            all_reps = tmap[tmap["case"] == p]["rep"].unique()
            counts = data_spikes[
                (data_spikes["label"] == neuron) & 
                (data_spikes["pattern"] == p)
            ].groupby("rep").size().reindex(all_reps, fill_value=0).to_numpy()

            isi = np.diff(spike_times)

            cv   = np.std(isi) / np.mean(isi) if len(isi) > 0 else None
            fano = np.var(counts) / np.mean(counts) if np.mean(counts) > 0 else None

            rows.append({
                "neuron":  neuron,
                "pattern": p,
                "cv":      cv,
                "fano":    fano,
                "isi":     isi  # keep raw ISI for wasserstein + plotting later
            })
    return pd.DataFrame(rows)

gt_isi_stats = compute_isi_metrics(gt_spikes,gt_data,cfg,patterns, tmap)
sub_isi_stats = compute_isi_metrics(gt_spikes,sub_data,cfg,patterns, tmap)
print("GT Model")
print()
print(gt_isi_stats.to_string())
print()
print("SUB Model")
print()
print(sub_isi_stats.to_string())


def plot_isi(gt_isi_df, sub_isi_df):
    for neuron in gt_isi_df["neuron"].unique():
        for p in patterns:
            gt_row = gt_isi_df[(gt_isi_df["neuron"] == neuron) & (gt_isi_df["pattern"] == p)]
            sub_row = sub_isi_df[(sub_isi_df["neuron"] == neuron) & (sub_isi_df["pattern"] == p)]

            gt_isi = gt_row["isi"].values[0]
            sub_isi = sub_row["isi"].values[0]

            if len(gt_isi) == 0 and len(sub_isi) == 0:
                continue  #Skip that dont give results

            if len(gt_isi) > 0 and len(sub_isi) > 0:
                w = wasserstein_distance(gt_isi, sub_isi)
            else:
                w = None

            # print the data
            print(f"\nNeuron: {neuron} | Pattern: {p}")
            print(f"  GT  - CV: {gt_row['cv'].values[0]:.4f} | Fano: {gt_row['fano'].values[0]}")
            print(f"  SUB - CV: {sub_row['cv'].values[0]:.4f} | Fano: {sub_row['fano'].values[0]}")
            print(f"  Wasserstein: {w:.4f}" if w is not None else "  Wasserstein: N/A")
            # plot
            fig, ax = plt.subplots(figsize=(6, 3))
            if len(gt_isi) > 0:
                ax.hist(gt_isi, bins=20, alpha=0.6, label="GT", color="tab:green")
            if len(sub_isi) > 0:
                ax.hist(sub_isi, bins=20, alpha=0.6, label="SUB", color="tab:pink")

            ax.set_title(f"{neuron} : ISI Distribution (Pattern {p})")
            ax.set_xlabel("ISI (ms)")
            ax.set_ylabel("Count")
            ax.legend()
            plt.tight_layout()
            save_and_close()


plot_isi(gt_isi_stats,sub_isi_stats)


# In[105]:


#Summary PLots for ISI and Fano Factor

print("Summary PLots for ISI and Fano Factor")

def plot_isi_cv_summary(gt_isi_df, sub_isi_df):
    neurons = gt_isi_df["neuron"].unique()

    gt_cv  = [gt_isi_df[gt_isi_df["neuron"] == n]["cv"].dropna().mean() for n in neurons]
    sub_cv = [sub_isi_df[sub_isi_df["neuron"] == n]["cv"].dropna().mean() for n in neurons]

    x = np.arange(len(neurons))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 4))
    bars_gt  = ax.bar(x - width/2, gt_cv,  width, label="GT",  color="tab:green")
    bars_sub = ax.bar(x + width/2, sub_cv, width, label="SUB", color="tab:pink")

    ax.bar_label(bars_gt,  fmt="%.3f", padding=3)
    ax.bar_label(bars_sub, fmt="%.3f", padding=3)
    ax.set_xticks(x)
    ax.set_xticklabels(neurons)
    ax.set_ylabel("ISI CV")
    ax.set_title("ISI Coefficient of Variation per Neuron")
    ax.legend()
    plt.tight_layout()
    save_and_close()

def plot_fano_summary(gt_isi_df, sub_isi_df):
    neurons = gt_isi_df["neuron"].unique()

    gt_fano  = [gt_isi_df[gt_isi_df["neuron"] == n]["fano"].dropna().mean() for n in neurons]
    sub_fano = [sub_isi_df[sub_isi_df["neuron"] == n]["fano"].dropna().mean() for n in neurons]

    x = np.arange(len(neurons))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 4))
    bars_gt  = ax.bar(x - width/2, gt_fano,  width, label="GT",  color="tab:green")
    bars_sub = ax.bar(x + width/2, sub_fano, width, label="SUB", color="tab:pink")

    ax.bar_label(bars_gt,  fmt="%.3f", padding=3)
    ax.bar_label(bars_sub, fmt="%.3f", padding=3)
    ax.set_xticks(x)
    ax.set_xticklabels(neurons)
    ax.set_ylabel("Fano Factor (Var/Mean)")
    ax.set_title("Fano Factor per Neuron: Pooled over patterns 00/01/10/11")
    ax.legend()
    plt.tight_layout()
    save_and_close()


plot_isi_cv_summary(gt_isi_stats,sub_isi_stats)
plot_fano_summary(gt_isi_stats,sub_isi_stats)


# In[106]:


# KS Metric - Kolmogorov-Smirnov Test for Spike Time Distributions
from scipy.stats import ks_2samp

print("KS Metric - Kolmogorov-Smirnov Test for Spike Time Distributions")

def plot_ecdf(gt_times, sub_times, neuron, pattern=None):
    # build ECDFs
    fig, ax = plt.subplots(figsize=(7, 4))

    if len(gt_times) > 0:
        gt_sorted  = np.sort(gt_times)
        gt_ecdf  = np.arange(1, len(gt_sorted)  + 1) / len(gt_sorted)
        ax.step(gt_sorted,  gt_ecdf,  label="GT",  color="green", lw=1.0, linestyle="--")

    if len(sub_times) > 0:
        sub_sorted = np.sort(sub_times)
        sub_ecdf = np.arange(1, len(sub_sorted) + 1) / len(sub_sorted)
        ax.step(sub_sorted, sub_ecdf, label="SUB", color="hotpink",   lw=2.0)

    ax.set_xlabel("t_in_trial (ms)")
    ax.set_ylabel("Cumulative fraction of spikes")
    title = f"{neuron} : ECDF"
    if pattern:
        title += f" (pattern {pattern})"
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    save_and_close()

gt_spike_times = []
sub_spike_times = []
rows_pattern = []
for neuron in spike_cols:
    label = neuron.replace("_spike", "")
    gt_spike_times  = gt_spikes[gt_spikes["label"] == label]["t_in_trial"].to_numpy()
    sub_spike_times = sub_spikes[sub_spikes["label"] == label]["t_in_trial"].to_numpy()

    if len(gt_spike_times) > 0 and len(sub_spike_times) > 0:
        ks_stat, p_val = ks_2samp(gt_spike_times, sub_spike_times)
        print(f"{neuron}: KS={ks_stat:.3f}, p={p_val:.3f}")
    else:
        print(f"{neuron}: not enough spikes")

    for p in patterns:
        gt_times  = gt_spikes[(gt_spikes["label"] == label) & (gt_spikes["pattern"] == p)]["t_in_trial"].to_numpy()
        sub_times = sub_spikes[(sub_spikes["label"] == label) & (sub_spikes["pattern"] == p)]["t_in_trial"].to_numpy()

        if len(gt_times) > 0 and len(sub_times) > 0:
            ks_stat, p_val = ks_2samp(gt_times, sub_times)
        else:
            ks_stat, p_val = None, None

        rows_pattern.append({
                "neuron":     neuron,
                "pattern":    p,
                "gt_spikes":  len(gt_times),
                "sub_spikes": len(sub_times),
                "ks_stat":    ks_stat,
                "p_value":    p_val
        })

        if len(gt_times) == 0 and len(sub_times) == 0:
            continue  # skip silent patterns

        plot_ecdf(gt_times, sub_times, neuron, pattern=p)


# In[107]:


# PSP Counts Metric - Peak detection in membrane potentials
from scipy.signal import find_peaks

# Detection parameters
PEAK_PROMINENCE = 0.5        # mV threshold for PSP detection
MIN_PEAK_DISTANCE_MS = 2     # Minimum distance between peaks
BASELINE_PRE_MS = 10         # Baseline window before input
CLIP_TO_RESP_WINDOW = True   # Count only within response window

print("PSP Counts Metric - Peak detection in membrane potentials")

def _earliest_anchor(m):
    """Get earliest input time."""
    a, b = m.get("a_time"), m.get("b_time")
    if a is None and b is None:
        return None
    return min([t for t in (a, b) if t is not None])

def _baseline_subtracted(vec, pre_ms=BASELINE_PRE_MS):
    v = np.asarray(vec, float)
    # anchor is always 0 — baseline is pre_ms before stimulus
    s, e = 0, min(int(trial_len) - 1, int(pre_ms))
    base = float(np.nanmedian(v[s:e+1]))
    return v - base

def _detect_psp_counts(v0, lo, hi):
    """Detect EPSP and IPSP peaks in window."""
    v = np.asarray(v0, float)
    use_lo = int(max(0, lo)) if CLIP_TO_RESP_WINDOW else 0
    use_hi = int(min(len(v)-1, hi)) if CLIP_TO_RESP_WINDOW else len(v)-1

    if use_hi < use_lo:
        return 0, 0

    seg = v[use_lo:use_hi+1]
    p_up, _ = find_peaks(seg, prominence=PEAK_PROMINENCE, distance=max(1, int(MIN_PEAK_DISTANCE_MS)))
    p_down, _ = find_peaks(-seg, prominence=PEAK_PROMINENCE, distance=max(1, int(MIN_PEAK_DISTANCE_MS)))

    return int(p_up.size), int(p_down.size)

# Build counts table
vm_cols = get_vm_cols(cfg, scope="all")
rows_counts = []
for patt in patterns:
    ids = tmap[tmap["case"] == patt]["trial_id"].tolist()
    if not ids:
        continue

    for col in vm_cols:  # ← also fix this — see point 3
        epsp_gt = ipsp_gt = epsp_sb = ipsp_sb = 0

        for i in ids:
            gt_df = get_trial(gt_data, trial_id=i)
            sb_df = get_trial(sub_data, trial_id=i)
            lo, hi = 0, int(trial_len)

            vbs  = _baseline_subtracted(gt_df[col].to_numpy(float))
            n_up, n_dn = _detect_psp_counts(vbs, lo, hi)
            epsp_gt += n_up
            ipsp_gt += n_dn

            vbs2 = _baseline_subtracted(sb_df[col].to_numpy(float))
            n_up2, n_dn2 = _detect_psp_counts(vbs2, lo, hi)
            epsp_sb += n_up2
            ipsp_sb += n_dn2

        rows_counts.append(dict(
            pattern=patt,
            neuron=col.replace("_vm", ""),
            n_trials=len(ids),
            EPSP_GT=epsp_gt, EPSP_SUB=epsp_sb,
            IPSP_GT=ipsp_gt, IPSP_SUB=ipsp_sb
        ))

PSP_COUNTS = pd.DataFrame(rows_counts).sort_values(["pattern", "neuron"]).reset_index(drop=True)

# Print formatted table
def print_psp_counts_by_pattern(df):
    """Display PSP counts with pattern separators."""
    df = df.sort_values(["pattern", "neuron", "n_trials"]).reset_index(drop=True)
    pat_groups = list(df.groupby("pattern", sort=False))

    header_cols = ["pattern", "neuron", "n_trials", "EPSP_GT", "EPSP_SUB", "IPSP_GT", "IPSP_SUB"]
    header = " ".join(f"{c:>12}" if c != "neuron" else f"{c:>8}" for c in header_cols)
    sep = "-" * max(88, len(header))

    print("\n=== PSP — Counts (GT vs SUB, per pattern × neuron) ===")
    print(header)
    print(sep)

    for idx, (patt, g) in enumerate(pat_groups):
        for _, r in g[header_cols].iterrows():
            print(f"{str(r['pattern']):>12} "
                  f"{str(r['neuron']):>8} "
                  f"{int(r['n_trials']):>12d} "
                  f"{int(r['EPSP_GT']):>12d} {int(r['EPSP_SUB']):>11d} "
                  f"{int(r['IPSP_GT']):>12d} {int(r['IPSP_SUB']):>11d}")
        if idx < len(pat_groups) - 1:
            print(sep)

print_psp_counts_by_pattern(PSP_COUNTS)


# In[108]:


# VM Mismatch Metric - Membrane potential comparison and visualization

print("VM Mismatch Metric - Membrane potential comparison and visualization")

def build_tables_then_plot(gt_data,sub_data, dpi=130, verbose=True):
    vm_cols  = get_vm_cols(cfg, scope="all")
    patterns = tmap["case"].unique().tolist()
    trial_len = int(meta["trial_len_ms"])
    ms_per_sample = 1000.0 / meta["fs_hz"]

    def _trial_full_stats(gt_df, sb_df, vm_cols):
        """Compute full-trial mismatch statistics."""
        n = min(len(gt_df), len(sb_df))
        if n == 0:
            return {"neuron_col": None, "rms": 0.0, "peak": 0.0, "win_str": ""}

        win_str = f"0.0–{(n-1)*ms_per_sample:.1f}"

        best_col, best_rms, best_peak = None, 0.0, 0.0
        for col in vm_cols:
            if (col not in gt_df.columns) or (col not in sb_df.columns):
                continue
            g = gt_df[col].to_numpy(dtype=float)[:n]
            s = sb_df[col].to_numpy(dtype=float)[:n]
            d = g - s
            if d.size == 0:
                continue
            rms = float(np.sqrt(np.nanmean(d * d)))
            peak = float(np.nanmax(np.abs(d)))
            if rms > best_rms:
                best_rms = rms
                best_peak = peak
                best_col = col

        return {"neuron_col": best_col, "rms": best_rms, "peak": best_peak, "win_str": win_str}


    # Table 1: Worst trial per pattern
    p_rows = []
    for patt in patterns:
        ids = tmap[tmap["case"] == patt]["trial_id"].tolist()
        if not ids:
            continue
        scored = []
        for i in ids:
            s = _trial_full_stats(get_trial(gt_data, trial_id=i), get_trial(sub_data, trial_id=i), vm_cols)
            if s["neuron_col"] is None:
                continue
            scored.append((i, s))
        if not scored:
            continue
        trial_id, stat = max(scored, key=lambda x: x[1]["rms"])
        p_rows.append({
            "pattern": patt,
            "trial_id": int(trial_id),
            "Neuron_VM (worst)": stat["neuron_col"],
            "Best RMS Δ (mV)": float(stat["rms"]),
            "Peak |Δ| (mV)": float(stat["peak"]),
            "Window (ms)": stat["win_str"],
        })

    pattern_worst_table = pd.DataFrame(p_rows, columns=[
        "pattern", "trial_id", "Neuron_VM (worst)", "Best RMS Δ (mV)", "Peak |Δ| (mV)", "Window (ms)"
    ])

    # Table 2: Worst trial per neuron across all trials
    n_rows = []
    for col in vm_cols:
        best = {"trial": None, "patt": None, "rms": 0.0, "peak": 0.0, "win": ""}
        for i in range(len(tmap)):
            gt_df, sb_df = get_trial(gt_data, trial_id=i),get_trial(sub_data, trial_id=i)
            if (col not in gt_df.columns) or (col not in sb_df.columns):
                continue
            stat = _trial_full_stats(gt_df, sb_df, [col])
            if stat["neuron_col"] is None:
                continue
            if stat["rms"] > best["rms"]:
                best.update({
                    "trial": i,
                    "patt": tmap[tmap["trial_id"] == i]["case"].values[0],
                    "rms": float(stat["rms"]),
                    "peak": float(stat["peak"]),
                    "win": stat["win_str"]
                })

        if best["trial"] is None:
            n_rows.append({
                "Neuron_VM": col, "Best RMS Δ (mV)": 0.0, "Peak |Δ| (mV)": 0.0,
                "pattern": None, "trial_id": np.nan, "Window (ms)": ""
            })
        else:
            n_rows.append({
                "Neuron_VM": col, "Best RMS Δ (mV)": best["rms"], "Peak |Δ| (mV)": best["peak"],
                "pattern": best["patt"], "trial_id": int(best["trial"]), "Window (ms)": best["win"]
            })

    neuron_best_table = pd.DataFrame(n_rows, columns=[
        "Neuron_VM", "Best RMS Δ (mV)", "Peak |Δ| (mV)", "pattern", "trial_id", "Window (ms)"
    ])

    # Format floats
    def _fmt_float(x, nd=6):
        try:
            return float(f"{float(x):.{nd}g}")
        except:
            return x

    if not pattern_worst_table.empty:
        pattern_worst_table["Best RMS Δ (mV)"] = pattern_worst_table["Best RMS Δ (mV)"].map(lambda v: _fmt_float(v, 6))
        pattern_worst_table["Peak |Δ| (mV)"] = pattern_worst_table["Peak |Δ| (mV)"].map(lambda v: _fmt_float(v, 6))
        pattern_worst_table = pattern_worst_table.sort_values(["pattern"]).reset_index(drop=True)

    if not neuron_best_table.empty:
        neuron_best_table["Best RMS Δ (mV)"] = neuron_best_table["Best RMS Δ (mV)"].map(lambda v: _fmt_float(v, 6))
        neuron_best_table["Peak |Δ| (mV)"] = neuron_best_table["Peak |Δ| (mV)"].map(lambda v: _fmt_float(v, 6))
        neuron_best_table = neuron_best_table.sort_values(["Neuron_VM"]).reset_index(drop=True)

    # Print tables
    print("=== Membrane Potential — Mismatch (Pattern Worst Trial) ===")
    if pattern_worst_table.empty:
        print("(none)")
    else:
        print(pattern_worst_table.to_string(index=False))

    print("\n=== Membrane Potential — Mismatch (Best Across Trials per Neuron) ===")
    if neuron_best_table.empty:
        print("(none)")
    else:
        print(neuron_best_table.to_string(index=False))

    # Plot referenced trials
    def _plot_trial_fullstack(gt_df, sb_df, patt, trial_id, title_note, vm_cols, dpi=130):
        """Plot all VM traces for a trial."""
        n = min(len(gt_df), len(sb_df))
        if n == 0:
            return

        tt = gt_df["t_in_trial"].to_numpy(dtype=float)[:n]
        xlab = "Time in trial (ms)"

        ms0 = 0.0
        ms1 = float(meta["trial_len_ms"]) - 1.0

        rows = len(vm_cols)
        fig_h = max(2.2 * rows, 3.2)
        fig, axs = plt.subplots(rows, 1, figsize=(8.6, fig_h), sharex=True, dpi=dpi)
        if rows == 1:
            axs = [axs]

        for ax, c in zip(axs, vm_cols):
            if (c not in gt_df.columns) or (c not in sb_df.columns):
                ax.axis("off")
                continue
            g = gt_df[c].to_numpy(dtype=float)[:n]
            s = sb_df[c].to_numpy(dtype=float)[:n]
            ax.plot(tt, g, lw=1.6, label="GT")
            ax.plot(tt, s, lw=1.6, ls="--", label="SUB")
            ax.fill_between(tt, g, s, alpha=0.12)
            ax.set_ylabel("mV")
            ax.set_title(c, fontsize=9)
            ax.grid(alpha=0.25)

        axs[-1].set_xlabel(xlab)
        fig.suptitle(
            f"Pattern {patt} — Trial {trial_id} • table-selected | window ms [{ms0:.1f}–{ms1:.1f}] • {title_note}",
            fontsize=11
        )
        axs[0].legend(loc="upper right", fontsize=9)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        save_and_close()

    # Collect unique trials to plot
    to_plot = set()
    for df in (pattern_worst_table, neuron_best_table):
        if not df.empty:
            for _, r in df.iterrows():
                patt = r.get("pattern", None)
                tid = r.get("trial_id", None)
                if pd.notna(patt) and pd.notna(tid):
                    to_plot.add((str(patt), int(tid)))

    def _ids_for_pattern(patt):
        return set(tmap[tmap["case"] == patt]["trial_id"].tolist())

    if not to_plot and verbose:
        print("\n[vm-plot] No valid trials in tables — nothing to plot.")
    else:
        grouped = {}
        for patt, tid in to_plot:
            grouped.setdefault(patt, set()).add(tid)

        for patt, tids in sorted(grouped.items()):
            common = _ids_for_pattern(patt)
            valid_ids = [tid for tid in sorted(tids) if tid in common]
            if not valid_ids:
                if verbose:
                    print(f"\n[vm-plot] pattern {patt}: no valid table-selected trials — skipped.")
                continue

            if verbose:
                print(f"\n[vm-plot] pattern {patt}: plotting {len(valid_ids)} table-selected trial(s)")
            for tid in valid_ids:
                gt_trial  = get_trial(gt_data,  trial_id=tid)
                sub_trial = get_trial(sub_data, trial_id=tid)

                stat = _trial_full_stats(gt_trial, sub_trial, vm_cols)
                note = f"worst-neuron={stat['neuron_col']} • peak|Δ|={stat['peak']:.3f} mV • rmsΔ={stat['rms']:.3f} mV"
                _plot_trial_fullstack(gt_trial, sub_trial, patt, tid, note, vm_cols, dpi=dpi)
    return {"pattern_worst_table": pattern_worst_table, "neuron_best_table": neuron_best_table}

# Execute
out = build_tables_then_plot(gt_data,sub_data, dpi=130, verbose=True)


# In[109]:


# Cross Correlogram Metric - Binary cross-correlation analysis
from IPython.display import display

MAX_LAG_MS = 15

print("Cross Correlogram Metric - Binary cross-correlation analysis")

def _seg_bin(df, col, lo_idx, hi_idx):
    """Extract binary segment from column."""
    if (col not in df.columns) or lo_idx >= hi_idx:
        return np.zeros(0, dtype=np.int8)
    arr = df[col].to_numpy(int, copy=False)
    hi_idx = min(hi_idx, len(arr))
    return arr[lo_idx:hi_idx].astype(np.int8, copy=False)

def _xcorr_norm(a, b, max_lag):
    """Normalized binary cross-correlation."""
    if a.size == 0 or b.size == 0:
        lags = np.arange(-max_lag, max_lag + 1, dtype=int)
        return lags, np.zeros(lags.size, dtype=float)

    W = int(min(a.size, b.size))
    if W <= 1:
        lags = np.arange(-max_lag, max_lag + 1, dtype=int)
        return lags, np.zeros_like(lags, dtype=float)

    L = int(min(max_lag, W - 1))
    full = np.correlate(a.astype(float), b.astype(float), mode="full")
    l_full = np.arange(-(W - 1), (W - 1) + 1, dtype=int)
    sel = (l_full >= -L) & (l_full <= L)
    lags = l_full[sel]
    counts = full[sel].astype(float)
    eff = (W - np.abs(lags)).astype(float)
    eff[eff <= 0] = np.nan
    cc = counts / eff
    cc = np.where(np.isfinite(cc), cc, 0.0)
    return lags, cc

def _avg_ccg_trials(trials_i, trials_j, meta, col_i, col_j, max_lag):
    """Average CCG across trials."""
    curves = []
    for df_i, df_j, m in zip(trials_i, trials_j, meta):
        lo, hi = 0, trial_len
        ai = _seg_bin(df_i, col_i, lo, hi)
        bj = _seg_bin(df_j, col_j, lo, hi)
        lags, cc = _xcorr_norm(ai, bj, max_lag)
        curves.append(cc)

    if not curves:
        lags = np.arange(-max_lag, max_lag + 1, dtype=int)
        mean_cc = np.zeros_like(lags, dtype=float)
    else:
        mean_cc = np.nanmean(np.vstack(curves), axis=0)
    return lags, mean_cc

def _ccg_matrix_for_pattern(trials_block, meta_block, spike_cols, title, max_lag=MAX_LAG_MS):
    """Create CCG matrix plot for pattern."""
    n = len(spike_cols)
    if n == 0 or not trials_block:
        return None, np.nan

    lags = np.arange(-max_lag, max_lag + 1, dtype=int)
    fig, axes = plt.subplots(n, n, figsize=(3 * n, 3 * n), sharex=True, sharey=True)
    if n == 1:
        axes = np.array([[axes]])

    zero_vals = []
    for i, ci in enumerate(spike_cols):
        for j, cj in enumerate(spike_cols):
            _, cc = _avg_ccg_trials(trials_block, trials_block, meta_block, ci, cj, max_lag)
            ax = axes[i, j]
            ax.bar(lags, cc, width=1)
            ax.axvline(0, color="red", ls="--", lw=1)
            if i == n - 1:
                ax.set_xlabel(f"Lag (ms)\n{cj}")
            if j == 0:
                ax.set_ylabel(f"{ci}\nCoincidence (norm)")
            if i != j:
                zero_vals.append(cc[max_lag])

    fig.suptitle(title, fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    mean_zero = float(np.nan) if not zero_vals else float(np.nanmean(zero_vals))
    return fig, mean_zero

def _intersect_spike_cols(spike_cols, trials_a, trials_b):
    """Filter spike columns to those present in both datasets."""
    if not trials_a or not trials_b or not spike_cols:
        return []
    cols_a = set(trials_a[0].columns)
    cols_b = set(trials_b[0].columns)
    return [c for c in spike_cols if (c in cols_a and c in cols_b)]

def render_ccg_grids_like_old():
    """Generate CCG matrices and summary statistics."""
    rows, figs = [], []

    for patt in patterns:
        ids = common_ids
        if not ids:
            continue

        fig_gt, mean0_gt = _ccg_matrix_for_pattern(
            gt_trials_p, col, spike_cols,
            title=f"Cross Correlogram — Ground Truth (Concatenated-style) — Pattern {patt}",
            max_lag=MAX_LAG_MS
        )
        fig_sb, mean0_sb = _ccg_matrix_for_pattern(
            sub_trials_p, col, spike_cols,
            title=f"Cross Correlogram — Submission (Concatenated-style) — Pattern {patt}",
            max_lag=MAX_LAG_MS
        )

        if fig_gt is not None:
            figs.append(fig_gt)
        if fig_sb is not None:
            figs.append(fig_sb)

        rows.append(dict(
            Pattern=patt,
            MeanZeroLag_GT=mean0_gt,
            MeanZeroLag_SUB=mean0_sb,
            Delta_SUB_minus_GT=(mean0_sb - mean0_gt) if (np.isfinite(mean0_gt) and np.isfinite(mean0_sb)) else np.nan
        ))

    return pd.DataFrame(rows, columns=["Pattern", "MeanZeroLag_GT", "MeanZeroLag_SUB", "Delta_SUB_minus_GT"]), figs

# Run and display results
ccg_summary_like_old, ccg_figs_like_old = render_ccg_grids_like_old()

# Print summary table
print("\n=== CCG (old-report style) — Mean zero-lag summary ===")
if not ccg_summary_like_old.empty:
    print(ccg_summary_like_old.to_string(index=False))
else:
    print("(no patterns)")

# Display figures
for f in ccg_figs_like_old:
    display(f)
    plt.close(f)





# In[110]:


# Van Rossum Distance Metric - Spike train comparison with exponential kernel

MS_PER_SAMPLE = 1000.0 / meta["fs_hz"] if meta["fs_hz"] > 0 else 1.0

print("Van Rossum Distance Metric - Spike train comparison with exponential kernel")

def _spike_times_in_window(df, col, lo_ms, hi_ms):
    if df is None or df.empty or (col not in df.columns):
        return np.empty(0, dtype=float)
    mask = (df["t_in_trial"] >= lo_ms) & (df["t_in_trial"] < hi_ms)
    spike_mask = df[col].to_numpy(dtype=int) == 1
    return df.loc[mask & spike_mask, "t_in_trial"].to_numpy(dtype=float)

def _vr_distance(spike_t_x, spike_t_y, tau_ms):
    """Compute Van Rossum distance with exponential kernel."""
    Nx = spike_t_x.size
    Ny = spike_t_y.size

    if Nx == 0 and Ny == 0:
        return 0.0
    if Nx == 0 or Ny == 0:
        return np.sqrt((Nx + Ny) / (2.0 * tau_ms))

    diffs = np.abs(spike_t_x[:, None] - spike_t_y[None, :])
    sxy = np.exp(-diffs / float(tau_ms)).sum()
    d2 = (Nx + Ny - 2.0 * sxy) / (2.0 * float(tau_ms))
    return float(np.sqrt(max(d2, 0.0)))

def run_vr_metric(tau_ms=20.0, min_trials_per_pattern=1):
    """Compute Van Rossum distance per trial and neuron."""
    if not gt_trials_p or not sub_trials_p:
        empty_cols = ["pattern", "trial_id", "neuron", "VR", "GT_spikes", "SUB_spikes", "tau_ms", "win_lo_ms", "win_hi_ms"]
        return (pd.DataFrame(columns=empty_cols),
                pd.DataFrame(columns=["pattern", "n_trials", "rows", "VR_mean", "VR_median"]),
                pd.DataFrame(columns=["neuron", "rows", "VR_mean", "VR_median"]))

    if not spike_cols:
        empty_cols = ["pattern", "trial_id", "neuron", "VR", "GT_spikes", "SUB_spikes", "tau_ms", "win_lo_ms", "win_hi_ms"]
        return (pd.DataFrame(columns=empty_cols),
                pd.DataFrame(columns=["pattern", "n_trials", "rows", "VR_mean", "VR_median"]),
                pd.DataFrame(columns=["neuron", "rows", "VR_mean", "VR_median"]))

    records = []
    for patt in patterns:
        ids = common_ids
        if not ids or len(ids) < min_trials_per_pattern:
            continue

        for i in ids:
            gt_df = get_trial(gt_data,  trial_id=i)
            sb_df = get_trial(sub_data, trial_id=i)
            lo_ms, hi_ms = 0, trial_len

            for neuron in spike_cols:
                tx = _spike_times_in_window(gt_df, neuron, lo_ms, hi_ms)
                ty = _spike_times_in_window(sb_df, neuron, lo_ms, hi_ms)
                vr = _vr_distance(tx, ty, tau_ms=float(tau_ms))
                records.append({
                    "pattern": patt,
                    "trial_id": i,
                    "neuron": neuron,
                    "VR": vr,
                    "GT_spikes": int(tx.size),
                    "SUB_spikes": int(ty.size),
                    "tau_ms": float(tau_ms),
                    "win_lo_ms": int(lo_ms),
                    "win_hi_ms": int(hi_ms),
                })

    trial_level_df = pd.DataFrame.from_records(records)

    if trial_level_df.empty:
        trial_level_df = pd.DataFrame(columns=["pattern", "trial_id", "neuron", "VR", "GT_spikes", "SUB_spikes", "tau_ms", "win_lo_ms", "win_hi_ms"])

    # Compute summaries
    if not trial_level_df.empty:
        pattern_summary = (
            trial_level_df
            .groupby("pattern", as_index=False)
            .agg(n_trials=("trial_id", lambda x: len(np.unique(x))),
                 rows=("VR", "size"),
                 VR_mean=("VR", "mean"),
                 VR_median=("VR", "median"))
            .sort_values("pattern")
            .reset_index(drop=True)
        )

        neuron_summary = (
            trial_level_df
            .groupby("neuron", as_index=False)
            .agg(rows=("VR", "size"),
                 VR_mean=("VR", "mean"),
                 VR_median=("VR", "median"))
            .sort_values("neuron")
            .reset_index(drop=True)
        )
    else:
        pattern_summary = pd.DataFrame(columns=["pattern", "n_trials", "rows", "VR_mean", "VR_median"])
        neuron_summary = pd.DataFrame(columns=["neuron", "rows", "VR_mean", "VR_median"])

    return trial_level_df, pattern_summary, neuron_summary

# Run metric
vr_trials, vr_by_pattern, vr_by_neuron = run_vr_metric(tau_ms=20.0)

# Print summaries
if not vr_by_pattern.empty:
    print("\n=== Van Rossum — Pattern Summary (τ=20 ms) ===")
    print(vr_by_pattern.to_string(index=False))

if not vr_by_neuron.empty:
    print("\n=== Van Rossum — Neuron Summary (τ=20 ms) ===")
    print(vr_by_neuron.to_string(index=False))

# trial-level table if want the worsts:
# vr_trials.sort_values('VR', ascending=False).head(10)


# In[111]:


# Multi-Scale Correlation Metric - Correlation across time scales
import math 
lo_ms = 0
hi_ms = trial_len

MS_PER_SAMPLE = 1000.0 / meta["fs_hz"]

print("Multi-Scale Correlation Metric - Correlation across time scales")

def _window_indices(df, lo_ms, hi_ms):
    n = len(df)
    if n == 0:
        return 0, 0
    lo = int(max(0, lo_ms))
    hi = int(min(n, hi_ms))
    return lo, hi

def _get_bin_window(df, col, lo_idx, hi_idx):
    """Extract binary vector for window."""
    if df is None or df.empty or (col not in df.columns):
        return np.zeros(0, dtype=float)
    arr = df[col].to_numpy(int)
    hi_idx = min(hi_idx, len(arr))
    if lo_idx >= hi_idx:
        return np.zeros(0, dtype=float)
    return arr[lo_idx:hi_idx].astype(float)

def _gauss_kernel_sigma_samp(sig_samp):
    """Create Gaussian kernel."""
    ksz = max(3, int(round(6.0 * sig_samp)))
    if ksz % 2 == 0:
        ksz += 1
    x = np.linspace(-3.0 * sig_samp, 3.0 * sig_samp, ksz)
    g = np.exp(-(x**2) / 2.0)
    g /= g.sum()
    return g

def _pearson_r_safe(a, b):
    """Compute correlation with degenerate case handling."""
    va = float(np.var(a))
    vb = float(np.var(b))
    if va == 0.0 and vb == 0.0:
        return 1.0  # Both constant
    if va == 0.0 or vb == 0.0:
        return 0.0  # One constant
    ca = a - float(np.mean(a))
    cb = b - float(np.mean(b))
    denom = math.sqrt(float(np.sum(ca*ca)) * float(np.sum(cb*cb)))
    if denom == 0.0:
        return 0.0
    return float(np.sum(ca*cb) / denom)

def _msc_curve_for_trial_neuron(gt_df, sb_df, neuron, lo_ms, hi_ms, sigma_vals_ms, dt_ms):
    """Compute correlation curve across scales for single trial/neuron."""
    lo_idx, hi_idx = _window_indices(gt_df, lo_ms, hi_ms)
    a = _get_bin_window(gt_df, neuron, lo_idx, hi_idx)
    b = _get_bin_window(sb_df, neuron, lo_idx, hi_idx)

    # Handle degenerate cases
    sa = int(a.sum())
    sb = int(b.sum())
    if sa == 0 and sb == 0:
        return np.ones_like(sigma_vals_ms, dtype=float), True, False
    if (sa == 0 and sb > 0) or (sa > 0 and sb == 0):
        return np.zeros_like(sigma_vals_ms, dtype=float), False, True

    # Compute correlations at each scale
    r = np.zeros_like(sigma_vals_ms, dtype=float)
    for k, sigma_ms in enumerate(sigma_vals_ms):
        sig_samp = max(1e-6, float(sigma_ms / dt_ms))
        g = _gauss_kernel_sigma_samp(sig_samp)
        ca = np.convolve(a, g, mode="same")
        cb = np.convolve(b, g, mode="same")
        r[k] = _pearson_r_safe(ca, cb)
    return r, False, False

def run_multi_scale_correlation(sigma_ms=(np.arange(1, 101)), per_pattern_plots=True, show=True):
    """Compute multi-scale correlation analysis."""
    if (not gt_trials_p) or (not sub_trials_p) or (not spike_cols):
        print("[msc] Missing trials or spike columns.")
        return (pd.DataFrame(columns=["pattern", "n_trials", "rows", "r_mean", "r_median", "both_silent_pct", "one_silent_pct"]),
                pd.DataFrame(columns=["neuron", "rows", "r_mean", "r_median", "both_silent_pct", "one_silent_pct"]),
                {})

    sigma_vals_ms = np.asarray(sigma_ms, dtype=float)
    dt_ms = MS_PER_SAMPLE

    # Storage structures
    per_pattern_per_neuron_curves = {p: {n: [] for n in spike_cols} for p in patterns}
    all_records_neu = {n: [] for n in spike_cols}
    silent_both = {p: {n: 0 for n in spike_cols} for p in patterns}
    silent_one = {p: {n: 0 for n in spike_cols} for p in patterns}
    counts_trials = {p: 0 for p in patterns}
    neuron_tot_trials = {n: 0 for n in spike_cols}
    neuron_both_silent = {n: 0 for n in spike_cols}
    neuron_one_silent = {n: 0 for n in spike_cols}

    # Process each pattern
    for patt in patterns:
        ids = common_ids
        if not ids:
            continue
        counts_trials[patt] = len(ids)

        for i in ids:
            gt_df = get_trial(gt_data,  trial_id=i)
            sb_df = get_trial(sub_data, trial_id=i)

            for neu in spike_cols:
                neuron_tot_trials[neu] += 1
                r_vec, is_both_silent, is_one_silent = _msc_curve_for_trial_neuron(
                    gt_df, sb_df, neu, lo_ms, hi_ms, sigma_vals_ms, dt_ms
                )

                per_pattern_per_neuron_curves[patt][neu].append(r_vec)
                all_records_neu[neu].extend(r_vec.tolist())

                if is_both_silent:
                    silent_both[patt][neu] += 1
                    neuron_both_silent[neu] += 1
                if is_one_silent:
                    silent_one[patt][neu] += 1
                    neuron_one_silent[neu] += 1

    # Generate summaries
    rows_patt = []
    for patt in patterns:
        vals = []
        bs = os_ = 0
        tot_trials_for_pattern = counts_trials[patt] * len(spike_cols) if counts_trials[patt] > 0 else 0
        if counts_trials[patt] > 0:
            for neu in spike_cols:
                curves = per_pattern_per_neuron_curves[patt][neu]
                if curves:
                    vals.extend(np.concatenate(curves).tolist())
                    bs += silent_both[patt][neu]
                    os_ += silent_one[patt][neu]

        if vals:
            arr = np.asarray(vals, dtype=float)
            rows_patt.append({
                "pattern": patt,
                "n_trials": counts_trials[patt],
                "rows": int(arr.size),
                "r_mean": float(np.mean(arr)),
                "r_median": float(np.median(arr)),
                "both_silent_pct": float(100.0 * (bs / tot_trials_for_pattern)) if tot_trials_for_pattern > 0 else np.nan,
                "one_silent_pct": float(100.0 * (os_ / tot_trials_for_pattern)) if tot_trials_for_pattern > 0 else np.nan
            })
    pattern_summary = pd.DataFrame(rows_patt, columns=["pattern", "n_trials", "rows", "r_mean", "r_median", "both_silent_pct", "one_silent_pct"])

    rows_neu = []
    for neu in spike_cols:
        vals = np.asarray(all_records_neu[neu], dtype=float)
        tot_trials = neuron_tot_trials[neu]
        if vals.size > 0 and tot_trials > 0:
            rows_neu.append({
                "neuron": neu,
                "rows": int(vals.size),
                "r_mean": float(np.mean(vals)),
                "r_median": float(np.median(vals)),
                "both_silent_pct": float(100.0 * neuron_both_silent[neu] / tot_trials),
                "one_silent_pct": float(100.0 * neuron_one_silent[neu] / tot_trials),
            })
    neuron_summary = pd.DataFrame(rows_neu, columns=["neuron", "rows", "r_mean", "r_median", "both_silent_pct", "one_silent_pct"])

    # Generate plots
    curves_by_pattern = {}
    for patt in patterns:
        ids = common_ids
        if not ids:
            continue

        plt.figure(figsize=(8.5, 4.8))
        for neu in spike_cols:
            curves = per_pattern_per_neuron_curves[patt][neu]
            if not curves:
                continue
            C = np.vstack(curves)
            mean_curve = np.mean(C, axis=0)
            plt.plot(sigma_vals_ms, mean_curve, lw=1.8, label=neu)
            curves_by_pattern.setdefault(patt, {})[neu] = mean_curve

        plt.title(f"Multi-Scale Correlation — Pattern {patt}")
        plt.xlabel("σ (ms)")
        plt.ylabel("Correlation r")
        plt.ylim(-0.05, 1.05)
        plt.legend(loc="best", ncol=2 if len(spike_cols) > 4 else 1, fontsize=8)
        plt.grid(alpha=0.25)
        plt.tight_layout()
        if show:
            save_and_close()

    # Print summaries
    if not pattern_summary.empty:
        print("\n=== Multi-Scale Correlation — Pattern Summary (across trials × neurons × σ) ===")
        print(pattern_summary.to_string(index=False))
    else:
        print("\n=== Multi-Scale Correlation — Pattern Summary (across trials × neurons × σ) ===")
        print("(no patterns)")

    if not neuron_summary.empty:
        print("\n=== Multi-Scale Correlation — Neuron Summary (pooled across patterns & σ) ===")
        print(neuron_summary.to_string(index=False))
    else:
        print("\n=== Multi-Scale Correlation — Neuron Summary (pooled across patterns & σ) ===")
        print("(no neurons)")

    return pattern_summary, neuron_summary, curves_by_pattern

# Run analysis
msc_pattern_summary, msc_neuron_summary, msc_curves = run_multi_scale_correlation(
    sigma_ms=np.arange(1, 101),
    per_pattern_plots=True,
    show=True
)


# In[112]:


# Schreiber Similarity Metric - Gaussian-smoothed spike trains

print("Schreiber Similarity Metric - Gaussian-smoothed spike trains")

def _binary_segment_in_window(df, col, lo_ms, hi_ms):
    """Extract binary spike segment for window."""
    if df is None or df.empty or (col not in df.columns):
        return np.zeros(0, dtype=np.float32)

    x = df[col].to_numpy(dtype=np.float32)
    n = x.size

    mask = (df["t_in_trial"] >= lo_ms) & (df["t_in_trial"] < hi_ms)
    return df.loc[mask, col].to_numpy(dtype=np.float32)

def _gaussian_kernel(sigma_ms, fs_hz):
    """Build Gaussian kernel for smoothing."""
    dt = 1000.0 / float(fs_hz)
    sigma = float(sigma_ms)
    if sigma <= 0:
        return np.array([1.0], dtype=np.float32)
    ksz = max(3, int(round(6.0 * sigma / dt)))
    if ksz % 2 == 0:
        ksz += 1
    half = ksz // 2
    t = (np.arange(ksz) - half) * dt
    g = np.exp(-0.5 * (t / sigma) ** 2).astype(np.float32)
    s = float(g.sum())
    if s > 0:
        g /= s
    return g

def _schreiber_similarity(a_bin, b_bin, kernel):
    """Compute Schreiber similarity between smoothed spike trains."""
    na = int(a_bin.sum() > 0)
    nb = int(b_bin.sum() > 0)
    both_silent = (na == 0 and nb == 0)
    one_silent = ((na == 0) ^ (nb == 0))

    if a_bin.size == 0 or b_bin.size == 0:
        return np.nan, both_silent, one_silent

    ca = np.convolve(a_bin, kernel, mode="same")
    cb = np.convolve(b_bin, kernel, mode="same")
    num = float(np.dot(ca, cb))
    den = float(np.sqrt(np.dot(ca, ca) * np.dot(cb, cb)))
    if den == 0.0:
        return np.nan, both_silent, one_silent
    r = num / den
    r = max(-1.0, min(1.0, r))  # Clamp numerical drift
    return r, both_silent, one_silent

def run_schreiber_metric(sigma_ms=10.0, min_trials_per_pattern=1):
    """Compute Schreiber similarity per trial and neuron."""
    if (not gt_trials_p) or (not sub_trials_p) or (not spike_cols):
        empty_trials = ["pattern", "trial_id", "neuron", "r", "both_silent", "one_silent",
                       "win_lo_ms", "win_hi_ms", "sigma_ms"]
        return (pd.DataFrame(columns=empty_trials),
                pd.DataFrame(columns=["pattern", "n_trials", "rows", "r_mean", "r_median", "masked_pct"]),
                pd.DataFrame(columns=["neuron", "rows", "r_mean", "r_median", "both_silent_pct", "one_silent_pct"]))

    kernel = _gaussian_kernel(sigma_ms=float(sigma_ms), fs_hz=meta["fs_hz"])

    rows = []
    for patt in patterns:
        ids = common_ids
        if not ids or len(ids) < int(min_trials_per_pattern):
            continue

        for i in ids:
            gt_df = get_trial(gt_data,  trial_id=i)
            sb_df = get_trial(sub_data, trial_id=i)

            lo_ms, hi_ms = 0, trial_len

            for neuron in spike_cols:
                a = _binary_segment_in_window(gt_df, neuron, lo_ms, hi_ms)
                b = _binary_segment_in_window(sb_df, neuron, lo_ms, hi_ms)
                r, both_silent, one_silent = _schreiber_similarity(a, b, kernel)
                rows.append({
                    "pattern": patt,
                    "trial_id": i,
                    "neuron": neuron,
                    "r": float(r) if (r == r) else np.nan,
                    "both_silent": bool(both_silent),
                    "one_silent": bool(one_silent),
                    "win_lo_ms": int(lo_ms),
                    "win_hi_ms": int(hi_ms),
                    "sigma_ms": float(sigma_ms),
                })

    trial_level = pd.DataFrame.from_records(rows)

    # Compute summaries
    if trial_level.empty:
        pattern_summary = pd.DataFrame(columns=["pattern", "n_trials", "rows", "r_mean", "r_median", "masked_pct"])
        neuron_summary = pd.DataFrame(columns=["neuron", "rows", "r_mean", "r_median", "both_silent_pct", "one_silent_pct"])
        return trial_level, pattern_summary, neuron_summary

    pattern_summary = (
        trial_level
        .groupby("pattern", as_index=False)
        .agg(
            n_trials=("trial_id", lambda x: len(np.unique(x))),
            rows=("r", "size"),
            r_mean=("r", "mean"),
            r_median=("r", "median"),
            masked_pct=("r", lambda x: float(np.mean(np.isnan(x))) * 100.0)
        )
        .sort_values("pattern")
        .reset_index(drop=True)
    )

    neuron_summary = (
        trial_level
        .groupby("neuron", as_index=False)
        .agg(
            rows=("r", "size"),
            r_mean=("r", "mean"),
            r_median=("r", "median"),
            both_silent_pct=("both_silent", lambda x: float(np.mean(x)) * 100.0),
            one_silent_pct=("one_silent", lambda x: float(np.mean(x)) * 100.0),
        )
        .sort_values("neuron")
        .reset_index(drop=True)
    )

    return trial_level, pattern_summary, neuron_summary

def plot_schreiber_per_pattern_lines_bars(trial_level_df, title_prefix="Schreiber (σ=10 ms) — Pattern"):
    """Plot similarity and usable fraction per pattern."""
    if trial_level_df.empty:
        return []
    figs = []

    for patt in patterns:
        dfp = trial_level_df.loc[trial_level_df["pattern"] == patt]
        if dfp.empty:
            continue

        g = (dfp.groupby("neuron", as_index=False)
                .agg(r_median=("r", "median"),
                     usable_frac=("both_silent", lambda x: 1.0 - float(np.mean(x)) if len(x) else np.nan)))

        g["neuron_label"] = g["neuron"].str.replace("_spike", "", regex=False)
        neuron_order = [n for n in spike_cols]
        g = g.set_index("neuron").reindex(neuron_order)
        no_data_mask = g["usable_frac"].isna() & g["r_median"].isna()
        g["usable_frac"] = g["usable_frac"].fillna(0.0)

        g = g.reset_index()
        x = np.arange(len(g))
        n_neurons = len(g)
        fig_width = max(8, 0.9 * n_neurons)  # scales with neuron count
        fig, ax1 = plt.subplots(figsize=(fig_width, 4.5))
        ax2 = ax1.twinx()

        # Bars for usable fraction
        bars = ax2.bar(g["neuron_label"], g["usable_frac"].to_numpy(float), alpha=0.28, width=0.8,
                      label="Usable frac (not both-silent)", zorder=1)

        # Mark no-data neurons
        if no_data_mask.any():
            for xi in x[no_data_mask.to_numpy()]:
                ax2.bar(g["neuron_label"].iloc[xi], 0.02,
                       fill=False, hatch="///", edgecolor="k", linewidth=1.0, alpha=0.9,
                       label="_no_data_outline", zorder=3)

        ax2.set_ylim(0.0, 1.0)
        ax2.set_ylabel("Usable fraction")

        # Line for median similarity
        ax1.plot(g["neuron_label"], g["r_median"].to_numpy(float), marker="o", linewidth=1.8,
                label="Median similarity", zorder=4)
        ax1.set_ylim(0.0, 1.0)
        ax1.set_ylabel("Median Schreiber r")
        ax1.set_xlabel("Neuron")
        ax1.set_title(f"{title_prefix} {patt}")
        ax1.grid(alpha=0.25, axis="y")
        plt.xticks(rotation=45, ha="right")

        # Annotate zero bars
        for rect, val in zip(bars, g["usable_frac"].to_numpy(float)):
            if val == 0.0:
                ax2.text(rect.get_x() + rect.get_width()/2, 0.02, "0", ha="center", va="bottom", fontsize=8)

        # Combined legend
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        if no_data_mask.any():
            from matplotlib.patches import Patch
            h2.append(Patch(fill=False, hatch="///", edgecolor="k", linewidth=1.0))
            l2.append("No data (all NaN)")
        ax1.legend(h1+h2, l1+l2, loc="lower right", fontsize=9)

        plt.tight_layout()
        figs.append(fig)
    return figs

# Run Schreiber analysis
sch_trials, sch_by_pattern, sch_by_neuron = run_schreiber_metric(sigma_ms=10.0)

if not sch_by_pattern.empty:
    print("\n=== Schreiber Similarity — Pattern Summary (σ=10 ms) ===")
    print(sch_by_pattern.to_string(index=False))
if not sch_by_neuron.empty:
    print("\n=== Schreiber Similarity — Neuron Summary (pooled across patterns) ===")
    print(sch_by_neuron.to_string(index=False))

figs = plot_schreiber_per_pattern_lines_bars(sch_trials, title_prefix="Schreiber (σ=10 ms) — Pattern")
for i, f in enumerate(figs):
    save_and_close(fig=f, name=f"fig_{i}")


# In[113]:


# Granger Causality Metric - Directional connectivity analysis

print("Granger Causality Metric - Directional connectivity analysis")

# Check for SciPy (needed for p-values)
try:
    from scipy.stats import f as _f_dist
    _HAS_SCIPY = True
except:
    _HAS_SCIPY = False

def _bin_spikes_block(trials, spike_cols, bin_ms=5):
    """Bin and concatenate spike counts across trials."""
    if not trials or not spike_cols:
        return np.zeros((0, 0)), np.array([])

    pieces = []
    for df in trials:
        lo_ms, hi_ms = 0, trial_len
        mask = (df["t_in_trial"] >= lo_ms) & (df["t_in_trial"] < hi_ms)
        if not mask.any():
            continue
        block = df.loc[mask, spike_cols].to_numpy(int)

        # Bin the data
        W = block.shape[0]

        step_ms = MS_PER_SAMPLE
        B = int(np.ceil(W * step_ms / bin_ms))
        binned = np.zeros((B, block.shape[1]), dtype=float)
        for b in range(B):
            lo = int(round((b * bin_ms) / step_ms))
            hi = int(round(((b+1) * bin_ms) / step_ms))
            hi = min(hi, W)
            if lo < hi:
                binned[b] = block[lo:hi].sum(axis=0)
        pieces.append(binned)

    if not pieces:
        return np.zeros((0, len(spike_cols))), np.array([])
    X = np.vstack(pieces)
    edges_ms = np.arange(X.shape[0] + 1) * bin_ms
    return X, edges_ms

def _lag_design(y, X_lags, lag):
    """Build regression design matrices for Granger test."""
    T = y.shape[0]
    if T <= lag:
        return np.zeros(0), np.zeros((0, lag + 1)), np.zeros((0, 2*lag + 1))
    rows = T - lag
    Y = y[lag:]

    def _lags(v):
        return np.column_stack([v[lag - k - 1:T - k - 1] for k in range(lag)])

    Ylags = _lags(y)
    Xlags = _lags(X_lags)
    R = np.column_stack([np.ones(rows), Ylags])
    F = np.column_stack([R, Xlags])
    return Y, R, F

def _ols_rss(design, target):
    """Compute residual sum of squares."""
    if design.shape[0] == 0 or design.shape[1] == 0:
        return np.nan
    beta, *_ = np.linalg.lstsq(design, target, rcond=None)
    resid = target - design @ beta
    return float(np.dot(resid, resid))

def _granger_pair(y, x, lag):
    """Compute Granger causality effect and p-value."""
    Y, R, F = _lag_design(y, x, lag)
    if Y.size == 0:
        return dict(effect=np.nan, p=np.nan)

    rss_r = _ols_rss(R, Y)
    rss_f = _ols_rss(F, Y)
    if not np.isfinite(rss_r) or not np.isfinite(rss_f) or rss_f <= 0:
        return dict(effect=np.nan, p=np.nan)

    effect = np.log(rss_r / rss_f)

    if _HAS_SCIPY:
        df1 = F.shape[1] - R.shape[1]
        df2 = F.shape[0] - F.shape[1]
        if df1 > 0 and df2 > 0:
            Fstat = ((rss_r - rss_f) / df1) / (rss_f / df2)
            p = _f_dist.sf(Fstat, df1, df2)
        else:
            p = np.nan
    else:
        p = np.nan

    return dict(effect=float(effect), p=float(p) if np.isfinite(p) else np.nan)

def _bh_fdr(pvals, alpha=0.05):
    """Benjamini-Hochberg FDR correction."""
    p = np.asarray(pvals, float)
    m = np.sum(np.isfinite(p))
    if m == 0:
        return np.full_like(p, np.nan)

    order = np.argsort(np.where(np.isfinite(p), p, np.inf))
    ranks = np.empty_like(order)
    ranks[order] = np.arange(1, len(p) + 1)
    q = np.full_like(p, np.nan)
    q_work = np.where(np.isfinite(p), p * m / ranks, np.nan)

    # Enforce monotonicity
    prev = np.inf
    for idx in order[::-1]:
        if np.isfinite(q_work[idx]):
            prev = min(prev, q_work[idx])
            q[idx] = prev
    return q

def _gc_for_dataset(trials, spike_cols, bin_ms=5, lag_bins=10, alpha=0.05, min_bins=50, min_spike_sum=10):
    """Compute Granger causality adjacency matrix."""
    X, _ = _bin_spikes_block(trials, spike_cols, bin_ms=bin_ms)
    N = len(spike_cols)
    if X.shape[0] < max(min_bins, lag_bins + 5):
        return (np.full((N, N), np.nan),) * 3 + (np.zeros((N, N), bool),)

    spike_sums = X.sum(axis=0)
    ok_neuron = spike_sums >= min_spike_sum

    # Z-score normalization
    Xz = X.copy().astype(float)
    for j in range(N):
        if ok_neuron[j]:
            mu = Xz[:, j].mean()
            sd = Xz[:, j].std(ddof=1)
            Xz[:, j] = (Xz[:, j] - mu) / (sd if sd > 0 else 1.0)
        else:
            Xz[:, j] = 0.0

    M_eff = np.full((N, N), np.nan)
    M_p = np.full((N, N), np.nan)

    for j in range(N):  # Target
        y = Xz[:, j]
        if not ok_neuron[j]:
            continue
        for i in range(N):  # Source
            if i == j or not ok_neuron[i]:
                continue
            res = _granger_pair(y, Xz[:, i], lag_bins)
            M_eff[j, i] = res["effect"]
            M_p[j, i] = res["p"]

    # FDR correction
    q = _bh_fdr(M_p.ravel(), alpha=alpha).reshape(M_p.shape)
    usable = np.isfinite(M_eff) & np.isfinite(q) & (q <= alpha)
    return M_eff, M_p, q, usable

def run_granger_per_pattern(bin_ms=5, lag_bins=10, alpha=0.05):
    """Run Granger causality analysis per pattern."""
    if not gt_trials_p or not sub_trials_p or not spike_cols:
        return pd.DataFrame(columns=["pattern", "edges_GT", "edges_SUB", "overlap", "jaccard"]), {}

    figs = {}
    rows = []

    for patt in patterns:
        ids = common_ids
        if not ids:
            continue

        gt_tr = [get_trial(gt_data,  trial_id=i) for i in ids]
        sb_tr = [get_trial(sub_data, trial_id=i) for i in ids]


        eff_gt, p_gt, q_gt, use_gt = _gc_for_dataset(gt_tr, spike_cols, bin_ms=bin_ms, lag_bins=lag_bins, alpha=alpha)
        eff_sb, p_sb, q_sb, use_sb = _gc_for_dataset(sb_tr, spike_cols, bin_ms=bin_ms, lag_bins=lag_bins, alpha=alpha)

        # Edge statistics
        A = use_gt
        B = use_sb
        e_gt = int(A.sum() - np.trace(A))
        e_sb = int(B.sum() - np.trace(B))
        inter = int((A & B).sum() - np.trace(A & B))
        union = int((A | B).sum() - np.trace(A | B))
        jacc = (inter / union) if union > 0 else np.nan
        rows.append(dict(pattern=patt, edges_GT=e_gt, edges_SUB=e_sb, overlap=inter, jaccard=jacc))

        # Create figure
        def _plot_heat(ax, M, mask, title):
            im = ax.imshow(np.where(mask, M, np.nan), cmap="magma", aspect="equal")
            ax.set_title(title, fontsize=11)
            ax.set_xticks(np.arange(len(spike_cols)))
            ax.set_xticklabels(spike_cols, rotation=60, ha="right")
            ax.set_yticks(np.arange(len(spike_cols)))
            ax.set_yticklabels(spike_cols)
            cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
            cb.set_label("GC effect (log RSSr/RSSf)")

        def _plot_degree(ax, mask, title):
            outdeg = mask.sum(axis=0)
            indeg = mask.sum(axis=1)
            x = np.arange(len(spike_cols))
            ax.bar(x - 0.2, outdeg, width=0.4, label="out-degree")
            ax.bar(x + 0.2, indeg, width=0.4, label="in-degree")
            ax.set_xticks(x)
            ax.set_xticklabels(spike_cols, rotation=60, ha="right")
            ax.set_title(title, fontsize=11)
            ax.legend()

        fig = plt.figure(figsize=(13, 5.5))
        gs = fig.add_gridspec(2, 3, height_ratios=[1, 1])
        ax1 = fig.add_subplot(gs[:, 0])
        ax2 = fig.add_subplot(gs[:, 1])
        ax3 = fig.add_subplot(gs[:, 2])

        _plot_heat(ax1, eff_gt, use_gt, f"GT — Pattern {patt}")
        _plot_heat(ax2, eff_sb, use_sb, f"SUB — Pattern {patt}")
        _plot_degree(ax3, use_sb, f"Degree (significant @ q≤{alpha}) — SUB")

        fig.suptitle(f"Granger Causality (bin={bin_ms} ms, lag={lag_bins} bins) — Pattern {patt}", fontsize=12)
        fig.tight_layout(rect=[0, 0, 1, 0.95])
        figs[patt] = fig

    summary = pd.DataFrame(rows, columns=["pattern", "edges_GT", "edges_SUB", "overlap", "jaccard"])
    return summary, figs

# Run Granger analysis
gc_summary, gc_figs = run_granger_per_pattern(bin_ms=5, lag_bins=10, alpha=0.05)

if not gc_summary.empty:
    print("\n=== Granger Causality — Pattern summary (q≤0.05) ===")
    print(gc_summary.to_string(index=False))
else:
    print("\n=== Granger Causality — Pattern summary (q≤0.05) ===\n(no patterns)")

for patt, fig in gc_figs.items():
    save_and_close(fig=fig, name=f"gc_{patt}")


# In[ ]:





# 

