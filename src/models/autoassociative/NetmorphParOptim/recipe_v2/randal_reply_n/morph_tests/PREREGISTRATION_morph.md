# PREREGISTRATION: morphology tests 1(a) and 1(b)

Written 2026-11-24, before any growth. It will not be edited after launch; deviations go in DEVIATIONS.md.

## Question
The axons of the current best recipe (E4) collapse into a ball at the disc centre:
- the axon ball index is 2,500–5,400;
- connection probabilities are 0.29–0.64;
- maximum interneuron axon reach is 122–144 µm.

Does changing the axon steering fix this without losing synapses per pair?
- **(a)** the balance between straight outgrowth and cell attraction;
- **(b)** which points attract the axons.

## Parameters (read in NetMorph source, `nes-linefix/ThirdParty/NetmorphCMake/Source`)
- **Axon direction:** `all_axons.direction_model=segment_history_tension` (weight 1, fixed as the first model in the chain), chained with `all_axons.axondm.direction_model=cell_attraction`, whose weight is `all_axons.axondm.dm_weight`.
  - `cell_attraction_direction_model::predict` (axon_direction_model.cc:741-751) sums 1/d² vectors to all attractor points, normalises the sum to unit length and multiplies it by `dm_weight`.
  - The pull therefore does not weaken with distance and has no cutoff.
  - The tension (history) term is the "straight / radial outgrowth" side of the balance.
  - Turns happen every 5 µm on average (`turn_separation=5.0`).
- **`dm_weight`** comes from the samples-sheet column `dm.weight` (gen_autonm_labels.py, sent with `%.1f`). The current value is 0.9. The hard limit is 0.1–1.0 (`assert_within_hard_limits`, bio_ranges.json).
- **Attractor points** (axon_direction_model.cc:714-728; network.cc:220-222, 697-708):
  - `In.attractors=NGF_A; In.attractedto=NGF_A`: every neuron is both an attractor and attracted.
  - `soma_attraction_weight` (global, default 1.0): with a value above 0, each attractor soma is a point with this weight.
  - `detailed_chemical_factors=true`: every dendrite branch point (P1 of a new branching dendrite segment) of an attractor neuron becomes an attractor point with weight 1.
- **The current E4 file sets `detailed_chemical_factors=true; soma_attraction_weight=0.0`, so the CURRENT setting is dendrite-node-only attraction.** Somata do not attract at all. (The task text assumed somata were included; this is corrected here.)
- When a parameter is repeated, the last value wins (Command_Line_Parameters.cc:159-160 "new value takes precedence"). Directives appended after the model file therefore override it.

## Build and baseline
- **Build:** patched NES `wt/nes-linefix/Binaries/BrainGenix-NES` (built 2026-11-23 07:28), with embedded NetMorph containing the line-379 fix: synapse_formation_model.cc `frac_T_PQ = tx/PQ` (file dated 2026-11-15). Every arm uses this build.
- **Baseline = E4:** `model_E4` is a byte-identical copy of the headline_i model file used for s66666/s77777. It is the base file plus:
  - D_synmax 0.0175 / 0.03 / 0.03 / 0.03;
  - interneuron basal 6–10;
  - interneuron dendrite B_inf 3.5;
  - interneuron axon B_inf 20.

  Sheet values: days 25, pyramidal 96, interneuron 20, minneuronseparation 10, radius 120, thickness 30, dm.weight 0.9.

## Arms (6) × seeds (4) = 24 growths
| arm | change from E4 (appended directives / sheet value) |
|---|---|
| A09 (baseline) | none (dm.weight 0.9; dendrite nodes only) |
| A05 | dm.weight 0.5 |
| A02 | dm.weight 0.2 |
| A01 | dm.weight 0.1 (lowest value the hard limit allows) |
| Bs (soma only) | `detailed_chemical_factors=false; soma_attraction_weight=1.0;` dm.weight 0.9 |
| Bsd (soma + dendrite nodes) | `soma_attraction_weight=1.0;` (detailed stays true), dm.weight 0.9 |

- **Seeds:** 66666 and 77777 (comparable with the existing E4 models), plus 88888 and 99999 (new).
- Test (a) is A09/A05/A02/A01, four levels.
- Test (b) is Bs and Bsd against the A09 baseline (dendrite nodes only).

## Machinery (John's addendum)
- Randal's batch generator is `gen_autonm_labels.py` with BatchRun. I use a copy, `morph_tests/gen_autonm_labels_mt.py`; the repo file is untouched.
- The copy adds two optional per-row sheet columns, because the original has a single `-randomseed` for the whole batch and no way to vary other directives per row:
  - `randomseed`;
  - `nm.<directive>`, appended as `<directive>=<value>;`.
- Each arm × seed is one row of a samples sheet.
- Hard limits are asserted as before (`assert_within_hard_limits` in the copy, plus `bio_check.assert_hard_limits` on the sheet).
- Runs use `-deleteresident` and `-batchlimit 3`, and the copy prints `NES_SIM_ID` per run.

## Scoreboard (realism tester, `--profile ca3`, NetMorph output folder)
For each model:
- ball_index.axon.{all, interneuron, pyramidal};
- ball_index.dendrite.all;
- length.axon/dendrite per type;
- reach_max/reach_mean axon per type;
- conn_prob for the four pairs;
- targets/sources per type;
- syn_per_pair for the four pairs.

The tester uses means and medians over cells or pairs. An arm's value is the median over its 4 seeds. Comparisons are paired by seed against A09 grown in this run, not against the stored older models.

## Success criteria (per arm)
- **S1 (ball):** ball_index.axon.all ≤ A09/10, paired by seed, in ≥ 3 of 4 seeds. The literature-plausible tier, ≤ 2 (the profile's derived 0.5–2), is reported separately.
- **S2 (connection probability):** conn_prob interneuron→pyramidal AND pyramidal→pyramidal are closer to the band [0.10, 0.25] than in A09 (a distance of 0 counts as closer or equal), paired, in ≥ 3 of 4 seeds.
- **S3 (reach):** reach_max.axon.interneuron (mean over cells) ≥ 1.5 × A09, paired, in ≥ 3 of 4 seeds. The literature tier is the derived 390–870 µm.
- **C1 (constraint):** syn_per_pair.interneuron→pyramidal (mean over connected pairs) ≥ 4.0 in ≥ 3 of 4 seeds. This is bar 3 used earlier. I also report pyramidal→pyramidal per pair against the earlier bar 2 (1.9–4.5).
- **Arm success** = S1 and S2 and S3 and C1.

## Predictions (written before any growth; probabilities are mine)
1. **A05:** ball index lower than A09 but still > 100 (70%). Reach × 1.1–1.5. C1 holds (55%).
2. **A02:** ball index 10–300 (55%). Reach × 1.5–2.5. Int→Pyr conn_prob 0.3–0.5. C1 fails (65%).
3. **A01:** ball index 2–50 (55%). Reach × 2–3.5 (about 250–450 µm). Int→Pyr conn_prob 0.2–0.45. C1 fails, with per-pair Int→Pyr < 4 (75%). Ball index ≤ 2 (literature tier): no (80%).
4. Lowering dm_weight lowers per-pair synapses monotonically (Int→Pyr per pair A09 > A05 > A02 > A01 in median) (65%).
5. **No arm meets full success (70%).** The most likely partial pattern is that S1/S3 improve while C1 fails.
6. **Bs (soma only):**
   - ball index lower than A09 (75%) but > 20 (60%);
   - axons cluster around individual somata;
   - reach within ±30% of A09 (60%);
   - Int→Pyr per pair ≥ A09 (55%).
7. **Bsd (soma + dendrite nodes):** about 116 somata against thousands of dendrite points, so every scoreboard metric changes by less than the seed-to-seed spread of A09 (80%).
8. **Total length:** direction knobs do not change total axon length per type by more than ±10% at the same seed (75%), nor dendrite length by more than ±5% (70%).
9. **Reproducibility:** A09 s66666/s77777 reproduce the stored headline_i models' per-type arbor lengths within 0.1% (60%). The grow here is concurrent in one NES process and RNGs are per-run objects (global.cc:176-185), but earlier same-seed mismatches were seen.
10. **Wall time per growth** is within 2× of the earlier ~1,540 s when 24 run concurrently (60%).

## Resource plan
- Limits: about 48 cores and under 250 GB RAM in total (the machine is 64 vCPU / 368 GB; about 91 GB is used now, mostly by the main NES, which is untouched).
- **8 new patched NES + API instance pairs.** Each has its own ports (8100+10k … 8104+10k), its own config folder and its own Output_BasePath under `morph_tests/instances/i<k>/out` (local disk). They share the read-only binary.
  - The main NES 3156209 / API 1972355 and the existing patched 2768884/2769516 are not used.
- Each instance runs one batch of 3 rows (one seed × 3 arms), with `-batchlimit 3` (3 concurrent per NES process: the known-safe level; 6 crashed a NES before).
- All 24 growths run at once. Expected about 16 cores of idle NES burn plus 24 growth threads, about 40 cores. RAM about 2–4 GB per growth.
- A monitor logs every 60 s: load, CPU, iowait (vmstat), disk utilisation (iostat), RSS per instance, and total used RAM.
  - If total used RAM exceeds 240 GB, no further work is started.
  - An instance above 10 GB RSS is restarted before any further batch (each instance runs one batch, then stops).
- Outputs:
  - NetMorph folders are kept until the tester has run.
  - `-savemodels` is not used (growth only), so there are no NES saved models.
  - Finished NetMorph output folders and any residents are deleted after the tester reports and summaries are written. Results JSON and grids stay.

## Not done
No recall or simulation. No change to the repo script or to the main or shared instances. No emails, git, pushes or Drive.
