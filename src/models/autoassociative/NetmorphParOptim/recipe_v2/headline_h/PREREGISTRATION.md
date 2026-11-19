# headline_h PREREGISTRATION (2026-11-19; written before the four new growths; not edited after launch)
Task: pick a headline recipe under "grow once, reuse". Candidates: **V1n30** (V1, 30 interneurons, pyramidal D 0.0175, interneuron D 0.0495 on all three interneuron pairs) and **E4** (V1, 20 interneurons, pyramidal D 0.0175, interneuron D 0.03). Five grown models per recipe: the three existing (not regrown; folders and uuids in models.md) plus new seeds 11111 and 22222 (4 growths, patched build, patched instance restarted fresh; the first three launched within seconds of each other, the fourth when a slot frees). Battery per model: (1) bars 1-7 (1 p 0.1-0.3; 2 Pyr->Pyr per connected pair 1.9-4.5; 3 Int->Pyr per connected pair 4-9; 4 Pyr->Int per connected pair 1.5-4.5; 5 drivable 8-cell >= one third of the interneurons (10 of 30, 7 of 20); 6 bio_ranges; 7 A = Int->Pyr/(Int->Pyr + Pyr->Pyr) inside the derived 25-50% band, inhib_e/TARGET.md), unrounded values; (2) capacity by offline packing (capacity_d/feas2.py method, 300 tries; D 0.0175 values from capacity_d/feas_n30_* and recall_e/feas_E4_*); (3) recall (dynamics_c protocol via dyn2.py: c 0/0.15/1.5/3.0, GABA on and silenced, designs from the packing) on the two new seeds per recipe; the old models' recall is cited: V1n30 s16180, s27182 in dynamics_c (and capacity_d for D 0.0175), E4 s16180, s27182 in recall_e; V1n30 s31415 and E4 s31415 have no recall run.
## Observed seed spread (3 existing models per recipe; bars.py -> bars_table.json)
| | V1n30 (s16180, s27182, s31415) | E4 (same seeds) |
|---|---|---|
| p | 0.251, 0.241, 0.308 | 0.236, 0.254, 0.282 |
| Pyr->Pyr per pair | 2.05, 2.07, 1.97 | 1.93, 2.35, 2.08 |
| A (%) | 68.9, 64.9, 66.5 | 46.8, 44.8, 40.7 |
| Int->Pyr per pair | 6.74, 5.86, 6.16 | 4.130, 5.147, 3.997 |
| Pyr->Int per pair | 3.46, 4.01, 3.76 | 4.03, 3.90, 3.72 |
| drivable | 16, 17, 16 of 30 | 10, 7, 10 of 20 |
| bars failed | 7 / 7 / 1 and 7 | none / none / 3 |
## Predictions for the four new models (central; range = observed spread widened by about 10-15%)
| quantity | V1n30 s11111, s22222 | E4 s11111, s22222 |
|---|---|---|
| p | 0.27 (0.21-0.34) | 0.26 (0.20-0.32) |
| Pyr->Pyr per pair | 2.05 (1.8-2.3) | 2.1 (1.75-2.6) |
| A (%) | 66.5 (61-72) | 44 (36-52) |
| Int->Pyr per pair | 6.2 (5.0-7.5) | 4.5 (3.3-5.8) |
| Pyr->Int per pair | 3.7 (3.0-4.4) | 3.9 (3.1-4.5) |
| drivable | 16 (13-20) of 30 | 9 (5-12) of 20 |
| zero-input interneurons | 1-3 | 1-4 |
| capacity (max disjoint 4+4 / 4+2) | 1 (0-2) / 3 (2-4) | 1 (0-1) / 3 (2-4) |
Per-model probability that each bar passes: V1n30: bar 1 70%, bar 2 85%, bar 3 98%, bar 4 80%, bar 5 95%, bar 6 100%, **bar 7 1%** (A 65-69% in all three existing models). E4: bar 1 80%, bar 2 75%, bar 3 60%, bar 4 90%, bar 5 75%, bar 6 100%, bar 7 90%.
## Pass-count predictions (models passing all 7 bars, out of 5; the existing three are counted as measured)
- **V1n30: 0 of 5 pass all seven (95%)**, because bar 7 fails in every model. Passing bars 1-6: 3 of 5 (range 2-4; existing: 2 of 3).
- **E4: 3 of 5 pass all seven** (range 2-4; existing 2 of 3; new seeds each about 30% to pass all seven, 0-2 of the two). P(E4 passes on at least 4 of 5) = 20%; P(on at most 2 of 5) = 30%.
- Mean +- SD over the 5 models (reported as measured): predicted E4 p 0.26 +- 0.03, Int->Pyr per pair 4.5 +- 0.6; V1n30 A 66.5 +- 2.5.
## Recall predictions (new seeds, designs from the packing)
- R1: every memory built recalls at c 0, 0.15 and 1.5, GABA on and silenced, 0 false 3-cell completions: 85% per recipe.
- R2: V1n30, c = 3.0 GABA on: no runaway (> 50 spurious non-member Pyr spikes) in either new seed: 55%; silenced runaway in both: 80%. E4, c = 3.0 GABA on: runaway in at least one new seed: 60%.
## Recommendation rule (decided before the data)
Recommend E4 as the headline recipe if it passes all 7 bars on at least 3 of 5 models and recall is clean at c <= 1.5; recommend V1n30 only if bar 7 is dropped or redefined (it fails bar 7 by construction); recommend neither as a "robust recipe" if E4 passes on fewer than 3 of 5. Prior: E4 recommended 55%; neither 40%; V1n30 5%. Regrowth noise: a pass count over 5 growths is itself a noisy estimate (binomial; with p = 0.5 the count has SD about 1.1), so conclusions are stated as ranges.
## Scoring
HIT inside the stated range, PARTIAL up to 25% beyond the edge (or one packing step), MISS otherwise; pass counts scored as exact or within +-1.
