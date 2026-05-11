# XOR Black-Box Substitute, GT Comparison, and Pipeline Outputs

**Document type:** System description / standard operating procedure (SOP)  
**Scope:** `xor_scnm` in-domain evaluation — black-box IF substitute, metrics, and `run_pipeline.sh` artifacts  
**Audience:** Engineers and reviewers who need to understand provenance, alignment with ground truth, and where to look when a step fails.

*For a formal PDF with Times New Roman: import this file into Microsoft Word or Google Docs and set the body font to Times New Roman, 11–12 pt, or print from a browser after applying the same font in the stylesheet.*

---

## 1. Purpose

This workflow supports **functional comparison** between:

1. **Ground truth (GT)** — membrane potential and spike data from the **NES-connected** XOR circuit, produced by the acquisition flow (`acquisition_template.py` via `Run_flat.sh`), and  
2. **Substitute (SUB)** — a **separate** dynamical model that implements XOR-like behaviour **without** using the NES simulation internals as its source of truth.

The substitute is intentionally a **black box**: same **inputs and trial schedule** as GT, same **output reporting format** as GT, but a **different** neuron implementation and network structure so that metrics measure **functional alignment** (I/O and task behaviour), not structural identity.

---

## 2. Origin of the Black-Box Model (Jainil’s IF XOR)

The substitute dynamics come from a **small integrate-and-fire (IF) XOR circuit** developed for in-domain XOR experiments (historically maintained in the separate **IFneuron-model** repository under `In_Domain/In_Domain_Data_Generation`). That stack includes:

- **`run_single_in_domain_trial`** — builds a five-neuron network (inputs A and B, AND gate C, OR gate D, XOR output E) and runs a single trial for a given bit pattern and stimulus times.  
- **`NeuronNetwork`** / **`IFneuron`** — synchronous 1 ms updates, double-exponential PSPs, direct stimulation for forced input spikes.

For **self-contained** use inside **BrainEmulationChallenge**, that logic was **vendored** (copied and namespaced) into:

`src/models/xor_scnm/vendor_if_xor/`

— so the challenge repo does **not** depend on cloning IFneuron-model. The behaviour of `run_single_in_domain_trial` is preserved; only import paths were adapted for a Python package layout.

**`blackbox_if_xor_sub.py`** does **not** reimplement the maths; it **calls** `run_single_in_domain_trial` once per row of `trial_map.json`, then **maps** IF neuron traces onto the **xor_scnm neuron IDs and labels** expected by `network_config.json` and `build_h5.py`.

---

## 3. Design Rationale

### 3.1 Why a black-box substitute?

The goal is to exercise **metrics and dashboards** against a model that:

- Solves the **same logical task** (XOR over two binary inputs) on the **same trial timeline**, but  
- Is **not** derived from the NES ground-truth simulator (different equations, different graph, different cell count).

If SUB were always a copy of GT, metrics would only check **self-consistency**. A distinct IF model tests whether the **evaluation pipeline** (HDF5 layout, trial alignment, behavioural definitions) is meaningful when GT and SUB **differ**.

### 3.2 Alignment with NES acquisition (trial schedule)

NES acquisition (`acquisition_template.py`) defines **100 ms trials** in a repeating **400 ms** cycle, with **direct input spikes at the start** of each pattern window (`t_in_trial = 0` for active channels). The black-box script reads **`trial_map.json`** (same file GT uses), and for each trial:

- Derives pattern `00`, `01`, `10`, or `11` from the `case` field.  
- Sets IF input bits **A** and **B** accordingly.  
- Applies stimulation at **0 ms within the trial** when a bit is 1 (no random jitter), matching the **effective** timing of the scripted NES input spikes for this experiment.

Thus GT and SUB see the **same** sequence of logical conditions and trial boundaries.

### 3.3 Input / output channel mapping (xor_scnm vs two-input IF)

The NES xor_scnm model uses **one** labelled input for channel A (`PyrIn_A`) and **two** neurons for channel B (`PyrIn_B1`, `PyrIn_B2`) that are driven **together** in acquisition. The IF model has **one** neuron **A** and **one** neuron **B**.

**Mapping chosen:**

- **A (IF) → `PyrIn_A` (NES id from `network_config.json`).**  
- **B (IF) → both `PyrIn_B1` and `PyrIn_B2`** — same membrane trace and same spike events **duplicated** onto both IDs so the HDF5 schema and downstream code that expect two B-line neurons remain valid.  
- **E (IF) → `E`** (output neuron label in `network_config.json`).

All **other** neuron IDs in the 35-neuron config remain at **resting membrane potential** with **no spikes**, so `build_h5.py` still receives a full-width Vm and spike table consistent with the connectome layout.

### 3.4 Same HDF5 path as GT

`build_h5.py` is **unchanged** in contract: it consumes **Vm CSV** (long format: `t_ms`, `neuron_id`, `field`, `value`), **spike CSV**, **`network_config.json`**, and **`trial_map.json`**. The black-box script writes **SUB-specific** CSV filenames but **compatible** columns so the **same** `build_h5` class produces **`substitute.h5`** with the same internal keys as **`groundtruth.h5`** (`/data`, `/spikes_raw`, `/network_config`, `/trial_map`, `/metadata`).

---

## 4. Comparison With GT (Acquisition)

| Aspect | Ground truth (GT) | Substitute (SUB) |
|--------|-------------------|------------------|
| **Source** | NES simulation + `acquisition_template.py` recordings | Vendored IF `run_single_in_domain_trial` per trial |
| **Trial definition** | `trial_map.json` from acquisition | **Same** `trial_map.json` (copied into SUB folder) |
| **Neuron layout** | Full xor_scnm connectome (35 neurons in config) | Only I/O-related labels filled from IF; others silent / rest |
| **HDF5** | `build_h5` on staged GT CSVs | `build_h5` on SUB CSVs |

**`in_domain_gt_sub_metrics.py`** reads **two HDF5 files** and compares aligned trials and columns. It uses **`truth_table`** from `network_config.json` for expected XOR output per pattern when scoring **behaviour**.

---

## 5. Metrics in `in_domain_gt_sub_metrics.py` — What and Why

This script is intentionally **narrow**: it complements the large **`in_domain_metrics.py`** notebook-style bundle by answering: *“On the **inputs and output** and **task behaviour**, how close is SUB to GT?”*  
It avoids interneuron / full-circuit shape metrics here so that **black-box** comparison stays interpretable and fast to run in CI or after a pipeline failure.

### 5.1 Behavioural table (per pattern)

**Outputs:** `gt_sub_behavior_by_pattern.csv` (GT and SUB rows).

**Content:** For each XOR pattern, counts **TP / FN / TN / FP** treating **output neuron firing within the trial window** vs **`truth_table`** `expected_output`. Also **accuracy**, **sensitivity**, **specificity**.

**Why:** The primary scientific question for XOR is whether the **readout** implements the truth table. Comparing GT vs SUB on the **same** metric definition makes misclassification visible without comparing internal wiring.

### 5.2 Membrane potential RMSE on I/O neurons

**Outputs:** `gt_sub_io_vm_rmse.csv`.

**Content:** Root-mean-square error of **Vm** between GT and SUB for every neuron labelled **`input` or `output`** in `network_config`, aggregated per pattern (and pooled in the table).

**Why:** Inputs and output are the **declared boundary** of the task. RMSE quantifies how similar the **observable** voltages are at the pins of the problem, without requiring SUB to match hidden interneurons (which the IF model does not populate meaningfully).

### 5.3 Van Rossum distance (output spike train)

**Outputs:** `gt_sub_output_van_rossum_trials.csv`, summary fields in `gt_sub_io_summary.json`.

**Content:** Per trial, per pattern, distance between GT and SUB **binary spike trains** on the **output** neuron column, with configurable **τ** (default 20 ms).

**Why:** Van Rossum is a standard **spike-train distance** that is sensitive to timing differences, not only spike counts. It summarizes **when** the readout fires relative to GT on each trial.

### 5.4 Schreiber similarity (output spike train)

**Outputs:** `gt_sub_output_schreiber_trials.csv`, summary in `gt_sub_io_summary.json`.

**Content:** Gaussian-smoothed spike trains on the output channel; **correlation** between GT and SUB per trial (default σ = 10 ms, scaled with sampling rate from HDF5 metadata).

**Why:** Schreiber similarity measures **co-modulation** of smoothed firing at a chosen temporal scale; it is complementary to Van Rossum (correlation vs distance) and is widely used for spike train comparison.

### 5.5 Summary JSON

**Output:** `gt_sub_io_summary.json`.

**Content:** Paths to both HDF5s, list of I/O Vm columns used, mean RMSE / mean Van Rossum / mean Schreiber **r**, trial length and hyperparameters.

**Why:** Single machine-readable artifact for dashboards, regression checks, or archival alongside CSVs.

### 5.6 Plots directory

**Folder:** `output/METRICS/plots_gt_sub/` (created empty by the script; reserved for future plot outputs if added).

---

## 6. `run_pipeline.sh` — End-to-End Flow (Typical Run)

All paths below are relative to **`src/models/xor_scnm`** (the working directory for `./run_pipeline.sh`).

1. **Acquisition (unless `--skip-acquisition`)** — `Run_flat.sh` runs reservoir/connectome as selected (`-x r|c|a`) and **`acquisition_template.py`** against NES. Writes a timestamped folder under **`output/*-acquisition/`** with `groundtruth-Vm.csv`, `groundtruth-spikes.csv`, `trial_map.json`, and usually `network_config.json` (or it is copied in step 2).  
2. **Stage GT bundle** — Copies acquisition outputs into **`output/GT/`** with stable names for debugging.  
3. **Build GT HDF5** — `build_h5` → **`output/GT/groundtruth.h5`**.  
4. **Black-box SUB (unless `--skip-blackbox-sub`)** — `blackbox_if_xor_sub.py` → **`output/SUB/`** CSVs + JSON copies; `build_h5` → **`output/SUB/substitute.h5`**; **`in_domain_gt_sub_metrics.py`** → **`output/METRICS/`** CSV/JSON.  
5. **Full metrics** — **`in_domain_metrics.py`** (matplotlib, large plot set); log to **`output/METRICS/metrics_log.txt`**; plots under **`output/plots/`** (repo convention for that script). Environment variables **`XOR_GT_H5_PATH`** and **`XOR_SUB_H5_PATH`** point the script at the built HDF5s when SUB is present.  
6. **Dashboard (unless `--no-dashboard`)** — Copies **`dashboard.py`** and both HDF5s into **`output/METRICS/`**, then runs **Streamlit** from that directory (optional **`--pinggy`** for tunnel).

---

## 7. Output Folders and Files After a Successful Pipeline

### 7.1 `output/<timestamp>-acquisition/` (example name)

| File | Role |
|------|------|
| `groundtruth-Vm.csv` | Long-format Vm from NES recording |
| `groundtruth-spikes.csv` | Spike list from NES |
| `trial_map.json` | Trial boundaries, pattern labels, repetition index |
| `network_config.json` | Neuron ids, labels, roles, `truth_table` |

**Shows:** Raw acquisition as produced by the experiment script; first place to inspect if acquisition fails.

---

### 7.2 `output/GT/`

| File | Role |
|------|------|
| `gt-Vm.csv` | Staged copy of GT Vm (same content as acquisition `groundtruth-Vm.csv`) |
| `gt-spikes.csv` | Staged copy of GT spikes |
| `network_config.json` | Staged copy for `build_h5` and metrics |
| `trial_map.json` | Staged copy |
| `groundtruth.h5` | **GT HDF5** from `build_h5` |

**Shows:** The **canonical GT bundle** used for all downstream steps; if HDF5 build fails, check these four inputs first.

---

### 7.3 `output/SUB/` (skipped if `--skip-blackbox-sub`)

| File | Role |
|------|------|
| `blackbox_sub-Vm.csv` | IF-mapped Vm in NES-compatible long CSV |
| `blackbox_sub-spikes.csv` | IF-mapped spikes |
| `network_config.json` | Copy (same as GT) |
| `trial_map.json` | Copy (same as GT) |
| `substitute.h5` | **SUB HDF5** from `build_h5` |

**Shows:** The **black-box** run aligned to GT trials; if SUB HDF5 fails, inspect IF trial loop or CSV size vs GT.

---

### 7.4 `output/METRICS/`

| File / folder | Role |
|---------------|------|
| `gt_sub_behavior_by_pattern.csv` | GT vs SUB behavioural scores by pattern |
| `gt_sub_io_vm_rmse.csv` | I/O Vm RMSE between GT and SUB |
| `gt_sub_output_van_rossum_trials.csv` | Trial-level Van Rossum on output |
| `gt_sub_output_schreiber_trials.csv` | Trial-level Schreiber **r** on output |
| `gt_sub_io_summary.json` | Machine-readable summary |
| `plots_gt_sub/` | Reserved for future GT–SUB plots from this script |
| `metrics_log.txt` | Captured stdout/stderr from `in_domain_metrics.py` |
| `dashboard.py` | Copy of Streamlit app |
| `groundtruth.h5` | Copy for Streamlit default path |
| `substitute.h5` | Copy when black-box step ran |

**Shows:** **Published** comparison artefacts and the **UI launch** directory; open `metrics_log.txt` if step 5 errors.

---

### 7.5 `output/plots/`

| Content | Role |
|---------|------|
| PNG figures | Written by **`in_domain_metrics.py`** (matplotlib) |

**Shows:** Full-circuit style metric plots from the large metrics script (not the same as Streamlit, which recomputes from HDF5 in Plotly).

---

## 8. Related Scripts (Quick Reference)

| Script | Role |
|--------|------|
| `acquisition_template.py` | NES functional acquisition → CSV + `trial_map.json` |
| `Run_flat.sh` | Orchestrates reservoir / connectome / acquisition entry points |
| `run_pipeline.sh` | End-to-end automation from acquisition through metrics and dashboard |
| `build_h5.py` | Normalizes CSV + JSON → HDF5 for GT or SUB |
| `blackbox_if_xor_sub.py` | IF SUB → SUB CSVs + JSON copies |
| `vendor_if_xor/` | Vendored IF XOR implementation |
| `in_domain_gt_sub_metrics.py` | Focused GT vs SUB I/O + behaviour metrics |
| `in_domain_metrics.py` | Broad offline metrics + plots |
| `dashboard.py` | Streamlit GT vs SUB UI (reads HDF5 paths in sidebar) |
| `sync_xor_scnm_to_pve.sh` | Optional **scp** helper to copy `xor_scnm` tree to a remote host |

---

## 9. Revision History

Document generated for the BrainEmulationChallenge **xor_scnm** pipeline. Update this SOP when acquisition timing, HDF5 schema, metric sets, or default output paths change.
