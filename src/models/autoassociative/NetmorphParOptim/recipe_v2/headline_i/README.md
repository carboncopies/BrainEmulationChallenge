# headline_i: tightening the E4 pass-rate estimate (2026-11-19)
E4 = V1 arbor (axon B_inf 20, dendrite 3.5), 20 interneurons, pyramidal D 0.0175, interneuron D 0.03, line-379-fixed build (patched NES 8011 / API 8010). Five NEW seeds 33333, 44444, 55555, 66666, 77777, each grown once (3 launched together, 66666 and 77777 when slots freed); bars, packing and recall all offline/read-back on those models. Scripts are headline_h copies (bars.py, analyze_pv.py, measure.py, feas2.py, dyn2.py; model prefix v2-hdi-). PREREGISTRATION.md was written before the first growth and not edited. Main NES/API untouched; no git, no emails.

## 1. Result: combined pass rate over 10 E4 models = 5 of 10 (50%), exact (Clopper-Pearson) 95% interval 18.7%-81.3%
| set | models passing all 7 bars | exact 95% interval |
|---|---|---|
| headline_h (s16180, 22222, 27182, 31415, 11111) | 3 of 5 | 14.7-94.7% |
| headline_i (new, s33333, 44444, 55555, 66666, 77777) | 2 of 5 | 5.3-85.3% |
| **combined** | **5 of 10** | **18.7-81.3%** |
The point estimate went from 60% to 50%; the interval narrowed from 80 points to 63 points. It does NOT tighten much: five more models cannot pin a pass rate down.

## 2. Per-model bars (unrounded; `bars_table.json`; threshold bar 5: >= 7 of 20)
| seed | p (0.1-0.3) | Pyr->Pyr/pair (1.9-4.5) | Int->Pyr/pair (4-9) | Pyr->Int/pair (1.5-4.5) | drivable (>=7) | A % (25-50) | zero-input | fails |
|---|---|---|---|---|---|---|---|---|
| 16180 | 0.236 | 1.93 | 4.130 | 4.03 | 10 | 46.8 | 3 | none |
| 27182 | 0.254 | 2.35 | 5.147 | 3.90 | 7 | 44.8 | 4 | none |
| 31415 | 0.282 | 2.08 | 3.997 | 3.72 | 10 | 40.7 | 1 | bar 3 |
| 11111 | 0.321 | 1.94 | 3.794 | 1.77 | 7 | 41.9 | 5 | bars 1, 3 |
| 22222 | 0.258 | 2.33 | 4.399 | 2.15 | 9 | 41.0 | 2 | none |
| **33333** | 0.280 | 1.98 | 4.349 | 3.40 | 10 | 45.7 | 3 | none |
| **44444** | 0.278 | 2.07 | 4.508 | 4.39 | **3** | 45.3 | 2 | bar 5 |
| **55555** | 0.289 | **1.80** | **3.559** | 2.42 | 9 | 43.1 | 1 | bars 2, 3 |
| **66666** | **0.350** | **1.88** | 4.214 | 2.60 | 7 | 45.0 | 2 | bars 1, 2 |
| **77777** | 0.291 | 2.09 | 4.947 | 2.86 | 11 | 47.6 | 2 | none |
Mean +- SD, new 5: p 0.297 +- 0.030, Pyr->Pyr/pair 1.96 +- 0.13, Int->Pyr/pair 4.32 +- 0.51, Pyr->Int/pair 3.14 +- 0.79, A 45.3 +- 1.6, drivable 8.0 +- 3.2, zero-input 2.0 +- 0.7.
Mean +- SD, all 10: p 0.284 +- 0.033, Pyr->Pyr/pair 2.05 +- 0.18, Int->Pyr/pair 4.30 +- 0.49, Pyr->Int/pair 3.13 +- 0.89, A 44.2 +- 2.4, drivable 8.3 +- 2.4, zero-input 2.5 +- 1.3.
Failures over the 10 models: bar 3 x3, bar 1 x2, bar 2 x2, bar 5 x1, bar 4 / 6 / 7 never. Bar 6 passes everywhere and bar 7 (A) passes everywhere (A 40.7-47.6%; the E4 recipe is reliably inside the derived band).

## 3. Capacity (offline packing, feas2.py, 300 tries; no sampling, exact candidates)
| seed | max disjoint 4+4 | max disjoint 4+2 |
|---|---|---|
| 33333 | 1 | 3 |
| 44444 | 0 | 2 |
| 55555 | 0 | 2 |
| 66666 | 1 | 3 |
| 77777 | 1 | 4 |
Same pattern as the older E4 models (0-1 eight-cell memories, 2-4 six-cell memories). Capacity is unrelated to passing: the two models with the weakest packing (44444, 55555) fail bars 5 and 2/3, but 33333 and 66666 pack equally and only one passes.

## 4. Recall check (dyn2.py, all 5 new models have memories; 64 sims, designs D42 = disjoint 4+2 memories, D44 = disjoint 4+4; c 0/0.15/1.5/3.0; GABA on and silenced; `summary.json`, `raw_*.json`)
- c = 0, 0.15, 1.5, GABA on and silenced: **every memory recalls cleanly in every model** (cue fires the non-cue members, 0 false 3-cell completions, 0 spurious non-member Pyr spikes), 17 memories in total (4+2: 14, 4+4: 3) x 3 background levels x 2 GABA conditions = 102 memory-trials, all clean.
- c = 3.0, GABA on: spurious non-member Pyr spikes (>50 = runaway) in 33333 D44 (220; its D42 design only 14), 55555 (543), 66666 (737/412), 77777 (149/207); 44444 has 0 spurious spikes (one of its two memories fails to recall cleanly, no runaway). So 4 of 5 models run away; GABA silenced: 4 of 5 clearly (323-1336 spikes), 44444 minimal (3). Same verdict as headline_h: E4's inhibition does not contain recurrent drive at c = 3.0; usable range is c <= 1.5.
- Passing the 7 bars does not matter for recall here: the two failing-bar models fit and recall memories too.

## 5. Preregistration scoring (HIT inside range, PARTIAL up to 25% beyond, MISS otherwise)
| prediction | observed | |
|---|---|---|
| per-model pass probability 50% | 5 of 10 (50%) | HIT |
| new 5: 2-3 pass (80% 1-4) | 2 | HIT |
| combined 10: 5.5 (4-7) | 5 | HIT |
| combined interval still ~55-65 points wide | 62.6 points | HIT |
| metric means, new 5: p 0.23-0.31 / Pyr->Pyr 1.9-2.4 / A 39-47 / Int->Pyr 3.9-4.9 / Pyr->Int 2.0-4.2 / drivable 7-10 / zero-input 2-3 | 0.297 / 1.96 / 45.3 / 4.32 / 3.14 / 8.0 / 2.0 | 7 of 7 HIT; SD of Int->Pyr 0.5 predicted, 0.51 observed |
| capacity: >=1 4+2 memory everywhere; 4+4 in 2-3 of 5; mean 4+4 0.6 | 4+2 in 5 of 5; 4+4 in 3 of 5; mean 0.6 | HIT x3 |
| recall at c <= 1.5 clean | clean everywhere | HIT |
| c = 3.0 GABA on: runaway in >= half the models | 4 of 5 | HIT |
| failing bars: bar 3 45%, bar 1 25%, bar 5 20%, bar 7 5%, other 5% | bar 2 x2, bars 1, 3, 5 once each, bar 7 never | PARTIAL: bar 2 (Pyr->Pyr/pair, 1.80 and 1.88 vs bound 1.9) was budgeted under "other 5%" and failed twice |
Overall: predictions held; the one miss is that the lower bound of bar 2 matters (both failures are within 0.1 of the bound).

## 6. Honest limits
- n = 10 models. The 95% interval 18.7-81.3% is the honest statement; "about 50%" is the estimate. Resolving a +-10 point interval would need roughly 100 models. The 3/5 of headline_h was an upward fluctuation (3 of 5 vs 2 of 5 are well inside binomial noise: Fisher exact p = 1.0).
- A "pass" is a conjunction of six bars on continuous quantities whose means sit close to the bounds (p 0.284 vs 0.3, Pyr->Pyr/pair 2.05 vs 1.9, Int->Pyr/pair 4.30 vs 4); a single model fails whenever any one wanders across. This is why ~50% emerges despite every bar mean being "inside". The bars themselves (e.g. 1/3 drivable, 25-50% A band derived in inhib_e, not measured) are thresholds I did not choose independently.
- Seeds and regrowth noise (repro_g) are not separable: each seed was grown once, and launch timing differed (three simultaneous, then two later at higher load). A recipe is a distribution of networks, not a single network; passing models are specific networks, recorded by folder (headline_i/grow_*, inhib_e, inhib_f, headline_h).
- The headline_h five and these five were grown in different batches; I assume exchangeable, no batch effect tested.
- Recall tested at fixed protocol (cue 4 cells, 3 events per memory, background c uniform per pair, STDP off) on packed memories; fits are by pairwise conductance threshold (4.125 nS), capacity a lower-bound heuristic of 300 greedy packings (exact candidate lists, no sampling here). Only 4+2 and 4+4 sizes. Runaway criterion > 50 spurious spikes is a convention.
- Not tested: other D_int values, more interneurons, any regrowth of a model with the same seed.

## Files
PREREGISTRATION.md, README.md, run_grow.sh/run_dyn.sh, grow_V1n20_s*/ (models v2-hdi-V1n20_s<seed>_p0d0175_i0d030000, viz dumps), pv_results.json, bars_table.json (10 E4 models), feas_*.json/log, groups_D42/D44_*.json, raw_*.json (64 sims), summary.json, analyze_*.log.
