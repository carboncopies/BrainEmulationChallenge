# Morphology tests 1(a) and 1(b): axon steering vs the axon ball (2026-11-24/25)

The preregistration is `PREREGISTRATION_morph.md`, written before any growth and not edited after; deviations are in `DEVIATIONS.md`. Full tables are in `results_tables.md`; numbers are in `results.json`, run records in `runs.json`, the soma-clustering check in `soma_clustering.json`, and realism-tester reports per arm in `reports/<arm>/report.html` (4 seeds each, with a model selector).

## What was tested
The axon direction of every growth cone is `unit(history) + w · unit(Σ 1/d² vectors to all attractor points)`, recomputed at each turn (every ~5 µm):
- the history (tension) term has weight 1;
- `w = all_axons.axondm.dm_weight` (sheet column `dm.weight`, E4 = 0.9, hard limit 0.1–1.0).

The pull is normalised, so it does not weaken with distance (axon_direction_model.cc:741-751).

Attractor points:
- every soma, weighted `soma_attraction_weight`;
- every dendrite branch point, if `detailed_chemical_factors=true`.

**The E4 recipe uses dendrite branch points only (`soma_attraction_weight=0.0`)**, not somata.

| arm | setting | tests |
|---|---|---|
| A09 | E4 baseline (dm_weight 0.9, dendrite nodes) | — |
| A05 / A02 / A01 | dm_weight 0.5 / 0.2 / 0.1 | (a) outgrowth vs attraction |
| Bs | somata only (`detailed_chemical_factors=false; soma_attraction_weight=1.0`) | (b) |
| Bsd | somata + dendrite nodes (`soma_attraction_weight=1.0`) | (b) |

- Seeds: 66666, 77777, 88888, 99999, giving 24 growths.
- Build: patched NES `wt/nes-linefix` (binary 2026-11-23) with the line-379 fix (`frac_T_PQ = tx/PQ`) in every arm. The baseline model file `model_E4` is byte-identical to the headline_i E4 file.

## Results (median over 4 seeds; realism-tester means over cells or pairs)
| arm | axon ball index | Int axon max reach µm | p Int→Pyr | p Pyr→Pyr | contacts/pair Int→Pyr | contacts/pair Pyr→Pyr | total contacts (s66666) |
|---|---|---|---|---|---|---|---|
| A09 | 3,032 | 133 | 0.55 | 0.31 | 4.29 | 1.96 | 13,253 |
| A05 | 772 | 162 | 0.62 | 0.30 | 3.10 | 1.56 | – |
| A02 | 21 | 249 | 0.67 | 0.28 | 2.25 | 1.30 | – |
| A01 | 5.1 | 351 | 0.59 | 0.22 | 1.79 | 1.19 | 5,780 |
| Bs | 172 | 159 | 0.60 | 0.29 | 2.75 | 1.48 | 8,915 |
| Bsd | 2,985 | 137 | 0.55 | 0.30 | 4.06 | 1.96 | 12,813 |
| literature / bar | 0.5–2 (derived) | 390–870 (derived) | 0.10–0.25 band | 0.10–0.25 band | ≥ 4 (bar 3) | 1.9–4.5 (bar 2) | |

Preregistered criteria, as seeds out of 4, paired with A09 of the same seed:

| arm | S1 ball ≤ A09/10 | S2 p toward band | S3 reach ≥ 1.5× | C1 Int→Pyr/pair ≥ 4 | success |
|---|---|---|---|---|---|
| A05 | 0 | 0 | 0 | 0 | no |
| A02 | 4 | 0 | 4 | 0 | no |
| A01 | 4 | 1 | 4 | 0 | no |
| Bs | 4 | 0 | 0 | 0 | no |
| Bsd | 0 | 1 | 0 | 2 | no |

(A09 itself meets C1 in 3/4 seeds: s88888 has 3.77.)

**No arm succeeds.**

**dm_weight is a strong, monotonic dial on the ball:**
- Lowering it from 0.9 to 0.1 lowers the axon ball index from about 3,000 to about 5 (a 600-fold drop, consistent in all 4 seeds) and raises interneuron axon reach from 133 to 351 µm.
- A01 is the first setting near the literature tier on either metric, though still outside it: ball 4.6–5.3 against ≤ 2, and reach 341–362 µm against 390–870.

**But spreading the axons does not lower connection probability, and it costs synapses per pair:**
- Int→Pyr stays at 0.5–0.68 in every arm.
- Pyr→Pyr falls only at A01, to 0.20–0.24, inside the band.
- Contacts per connected pair fall steadily: Int→Pyr 4.29 → 3.10 → 2.25 → 1.79.
- Total contacts drop by about 60% (13.3k → 5.8k on s66666).

The reason: the disc is small (radius 120 µm, 116 cells) compared with the arbors, so each axon already passes through most cells' dendritic fields. The ball only piles extra contacts onto pairs that are already connected. Removing the ball therefore removes contacts per pair, not partners. Under this patch geometry, the probability band (0.10–0.25) and the per-pair bar (≥ 4) cannot both be met by axon steering. That would need a larger tissue volume or more cells per arbor volume, which is a different test.

**Soma-only attraction (Bs):**
- The ball index falls to 68–257 (median 172) and reach rises slightly (×1.2).
- Axons wrap the somata instead: 67–69% of axon length lies within 10 µm of a soma centre, against 19–34% in A09 (s66666, s88888; `soma_clustering.json`). That is a new, unrealistic clustering.
- Per-pair contacts fall to 2.75.

**Somata + dendrite nodes (Bsd)** is indistinguishable from A09 within seed spread (116 somata against thousands of dendrite points).

Total axon length per type is unchanged within ±8%, and dendrites are unchanged: the knobs only steer, they do not change how much axon grows.

## Prediction scoring (10 predictions)
1. **A05:**
   - ball > 100 (772): hit.
   - reach × 1.1–1.5 (× 1.22): hit.
   - C1 holds: **miss** (3.10).
2. **A02:**
   - ball 10–300 (21): hit.
   - reach × 1.5–2.5 (× 1.87): hit.
   - p Int→Pyr 0.3–0.5: **miss** (0.67; it rose).
   - C1 fails: hit.
3. **A01:**
   - ball 2–50 (5.1): hit.
   - reach × 2–3.5 (× 2.64, 351 µm): hit.
   - p Int→Pyr 0.2–0.45: **miss** (0.59).
   - C1 fails: hit.
   - not ≤ 2: hit.
4. Per-pair Int→Pyr falls monotonically with dm_weight: hit.
5. No arm succeeds, and the pattern is S1/S3 improving while C1 fails: hit.
6. **Bs:**
   - ball lower but > 20: hit.
   - clustering at somata: hit.
   - reach within ±30%: hit.
   - Int→Pyr/pair ≥ A09: **miss** (2.75).
7. Bsd within seed spread: hit.
8. Lengths unchanged (axon ±10%, dendrite ±5%): hit.
9. A09 reproduces the stored s66666/s77777 arbors within 0.1%: hit. All arbor lengths are identical to the digit; connection metrics differ by 0.3–7.6% at identical arbors, the known synapse-count noise.
10. Growth wall time within 2× of the earlier ~1,540 s: hit. Each batch of 3 took 1,848–2,661 s.

The systematic error: I expected spreading to lower connection probability, and it did not, because of the patch geometry above.

## Resources and scaling
- **Wall-clock:** all 24 growths in **44 min** (23:26:34 → 00:10:56) on 8 separate patched NES+API instances, with 3 concurrent growths per NES (`-batchlimit 3`). Earlier E4 work ran 3 growths at a time on one instance (about 3.7 h for 8 runs), so throughput rose about 15-fold.
- **Cores:** our 8 NES processes used a mean of 29 and a peak of 32 cores (sampled every 60 s). The whole machine peaked at 63% (about 40 of 64 vCPU), including the untouched main NES at about 2.2 cores.
- **RAM:** our NES processes peaked at 15.9 GB in total (about 2 GB each). The machine's used RAM went from 91 to at most 108 GB. No instance came near 10 GB, so no restart was needed; each instance ran one batch and was stopped.
- **I/O:** iowait ≤ 2% and disk utilisation ≤ 8% (iostat sda). I/O was not a bottleneck. Outputs were written to local disk under `instances/i<k>/out` (about 350 MB per 3 models).
- **What scaled well:**
  - separate NES processes: no failures, and per-growth time only 1.2–1.7× a lightly loaded run;
  - 3 growths per NES;
  - per-row seeds in one sheet.
- **What cost:**
  - each idle NES burns about 2 cores;
  - a second or later row in the same NES is not slower, but batches with many rows per NES risk the crash seen earlier at 6.
- **Headroom:** RAM was nowhere near the limit. CPU at about 30 of 48 cores suggests 10–12 instances × 3, i.e. 30–36 growths at once, would still fit.

Cleanup:
- All 24 NES residents were deleted by `-deleteresident` (24 "Deleted resident" lines). NES_SIM_IDs and output folders are recorded in `runs.json` and `batch_i*/run.log`.
- `-savemodels` was not used, so there are no NES saved models.
- The NetMorph output folders were deleted after the tester reports were written. The reports keep the full-precision grids (`reports/<arm>/grids/`).
- All 8 instances are stopped. The main NES 3156209 / API 1972355 and the shared patched 2768884/2769516 were not used.

## How the batch / samples sheet was built (for reuse)
- **Generator:** `gen_autonm_labels_mt.py` is a copy of `bec-netmorph/src/models/autoassociative/gen_autonm_labels.py` (`gen_autonm_labels.orig.py` is the unmodified copy for diffing). It uses Randal's BatchRun as is. The changes are about 10 lines:
  - **optional columns `randomseed`** (per row, overriding `-randomseed`) and **`nm.<directive>`**, appended as `<directive>=<value>;` after the sheet values so they win. Empty cells are skipped.
  - **an optional `arm` label column;**
  - **printing `NES_SIM_ID=… runID=… arm=… seed=…` and `NETMORPH_OUT runID=… dir=…`** per run.
  The original generator ignores the extra columns, so the same sheet still runs on it, with a single seed and no extra directives.
- **Sheet:** `batch_i<k>/samples.xlsx`, one row per arm × seed, columns `days, pyramidal, interneuron, minneuronseparation, shape.radius, shape.thickness, dm.weight, arm, randomseed, nm.detailed_chemical_factors, nm.soma_attraction_weight`. `run_batch.py` builds it from the `ARMS` / `SEEDS` tables, asserts `bio_check.assert_hard_limits` on the 7 limited columns, and the generator asserts `assert_within_hard_limits` again per row.
- **Command per instance:**

  ```
  gen_autonm_labels_mt.py -excel samples.xlsx -out out.xlsx -modelfile model_E4 -modelname mt-i<k>- -deleteresident -batchlimit 3 -vizdir viz -Port <8100+10k>
  ```

  with `n` fed to the final "compare?" prompt.
- **Instances:**
  - `setup_instances.sh N` makes N folders. Each shares the read-only binaries by symlink and has its own `NES.yaml` (port 8102+10k, its own Output_BasePath), its own `API.cfg` (8100+10k service, +1 callback, +3 EVM, +4 Neuroglancer) and its own `Source/Core/Config/users.json`.
  - `inst.sh start|stop|status k` controls one instance; `stop` checks the process cwd first.
  - `monitor.sh` logs resources (`monitor.log`).
- **Scoring:** `analyze.py` runs the realism tester per arm and evaluates the preregistered criteria.

## Notes on gen_autonm_labels.py / BatchRun (not edited in the repo)
1. **One random seed per batch.** `-randomseed` is appended to every row, so a sheet cannot hold several seeds. This is fixed in the copy with the `randomseed` column.
2. **No per-row directives beyond the 7 sheet parameters** (for example `soma_attraction_weight`). Fixed in the copy with the `nm.*` columns.
3. **`-fitcpus` sets the batch size to `os.cpu_count()` of the client machine** (64 here), regardless of NES memory or the number of NES processes. All rows would then grow as concurrent threads in one NES process, and 6 concurrent growths crashed a NES before (LEARNINGS 2026-11-14). I used `-batchlimit 3` per NES and several NES processes instead.
4. **The RAM guard is machine-wide:**
   - `lauch_resources_low` checks NES `RAMfree` < 2 GB;
   - `resources_low` also checks psutil used/total > 0.9.

   So it would allow about 330 GB on this machine, not 250. Our own monitor enforced the limit (it never triggered). Batch workers are threads inside one NES, about 2 GB each here; they do not each load the full RAM.
5. **The "Peak memory usage" print is always 0.00 GB** unless RAM was low: `peak_RAM` is updated only inside `get_OS_RAM_used_total_GB()`, which is called only on the low-RAM path.
6. `dm.weight` is sent with `%.1f`, so values like 0.05 or 0.25 are silently rounded (the hard-limit check rounds first). Sheet values must be multiples of 0.1.
7. `ARCHITECTURE_MODIFY` appends `In.pyramidal=32; In.interneuron=16;` (from the -EMBEDMULTIPLE/-PATTERNSIZE defaults) before the sheet values. It is harmless because the later sheet values win, but it is confusing in logs.
8. The script ends with an interactive `input()` ("compare the two label methods?"), so unattended runs must feed stdin.
9. pandas returns sheet text `false` as `False`. That is harmless for NetMorph booleans, which are lowercased, but other string-valued directives should be checked in the "Directives appended" log line.
10. `bec-netmorph` has `NetmorphParOptim/bio_check.py` but no `bio_ranges.json`, so `bio_check.assert_hard_limits` fails there. I used the `cos/netmorph_work/bec` checkout.

## Limits
- One patch geometry: disc radius 120 µm, thickness 30, 96 + 20 cells. The connection-probability conclusion is specific to a patch that is small compared with the arbors.
- 4 seeds per arm.
- Literature numbers in the tester profile are unverified, and the ball-index ≤ 2 and reach 390–870 µm tiers are derived.
- Only global switches were tested. `dm_weight` applies to all axons (pyramidal and interneuron alike). Interneuron-only steering (restating the chain under `all_interneuron_axons.`) and the `neuron_specific_attraction_switch` / `attraction_moderation_base` knobs are untested.
- No recall or dynamics were run.

## Files
- `PREREGISTRATION_morph.md`, `DEVIATIONS.md`
- `run_batch.py`, `gen_autonm_labels_mt.py`, `gen_autonm_labels.orig.py`, `model_E4`
- `setup_instances.sh`, `inst.sh`, `monitor.sh`, `analyze.py`
- `results_tables.md`, `results.json`, `runs.json`, `soma_clustering.json`, `monitor.log`, `batch_i*/`
- `reports/{A09,A05,A02,A01,Bs,Bsd}/report.html`
