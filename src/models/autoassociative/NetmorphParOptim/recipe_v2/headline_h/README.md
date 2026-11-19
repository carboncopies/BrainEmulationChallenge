# headline_h: a headline recipe under "grow once, reuse" (2026-11-19)
Candidates (patched build, pyramidal D 0.0175, 96 pyramidal cells): **V1n30** (V1, 30 interneurons, interneuron D 0.0495) and **E4** (V1, 20 interneurons, interneuron D 0.03). Five grown models each: three existing (not regrown; folders/uuids in models.md) plus seeds 11111 and 22222 (4 new growths; the first three launched within seconds of each other, the fourth when a slot freed; patched instance freshly restarted, NES pid 2246396). Files: PREREGISTRATION.md (written before the new growths, not edited), bars.py -> bars_table.json (bars 1-7, unrounded), analyze_pv.py/pv_results.json (new models), feas2.py + feas_*.json/log (packing), groups_*.json, dyn2.py + run_dyn.sh + summarize.py (recall; raw_*.json, 40 sims), grow_pv.py (copy of inhib_f/grow_pv.py, paths and model prefix `v2-hdh-` only; diff checked), models.md.
All 4 growths rc 0 (walls 1,260-1,800 s), bio_check pass, 40 of 40 recall sims loaded_ok and deleted (no Traceback / DELETE FAILED). Patched instance only; main NES/API untouched; no NES code change; no git, no email.

## 1. Bars 1-7 per model (1 p 0.1-0.3; 2 Pyr->Pyr per pair 1.9-4.5; 3 Int->Pyr per pair 4-9; 4 Pyr->Int per pair 1.5-4.5; 5 drivable 8-cell >= one third (10 of 30, 7 of 20); 6 bio ranges; 7 A inside the derived 25-50% band, inhib_e/TARGET.md)
**V1n30**
| seed | p | per pair | A % | Int->Pyr | Pyr->Int | drivable | zero-input | failed bars | all 7 | max 4+4 / 4+2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 11111 (new) | 0.281 | 1.79 | 65.0 | 5.051 | 3.24 | 18 of 30 | 4 | 2, 7 | no | 0 / 2 |
| 16180 | 0.251 | 2.05 | 68.9 | 6.736 | 3.46 | 16 of 30 | 1 | 7 | no | 1 / 3 |
| 22222 (new) | 0.279 | 1.99 | 68.5 | 6.488 | 3.76 | 12 of 30 | 5 | 7 | no | 0 / 2 |
| 27182 | 0.241 | 2.07 | 64.9 | 5.861 | 4.01 | 17 of 30 | 2 | 7 | no | 1 / 3 |
| 31415 | 0.308 | 1.97 | 66.5 | 6.164 | 3.76 | 16 of 30 | 1 | 1, 7 | no | 1 / 3 |
| mean +- SD | 0.272 +- 0.027 | 1.98 +- 0.11 | 66.8 +- 1.9 | 6.06 +- 0.65 | 3.65 +- 0.30 | 15.8 +- 2.3 | 2.6 +- 1.8 | | **0 of 5** | 0.6 / 2.6 |
**E4**
| seed | p | per pair | A % | Int->Pyr | Pyr->Int | drivable | zero-input | failed bars | all 7 | max 4+4 / 4+2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 11111 (new) | 0.321 | 1.94 | 41.9 | 3.794 | 1.77 | 7 of 20 | 5 | 1, 3 | no | 0 / 2 |
| 16180 | 0.236 | 1.93 | 46.8 | 4.130 | 4.03 | 10 of 20 | 3 | none | yes | 0 / 2 |
| 22222 (new) | 0.258 | 2.33 | 41.0 | 4.399 | 2.15 | 9 of 20 | 2 | none | yes | 1 / 3 |
| 27182 | 0.254 | 2.35 | 44.8 | 5.147 | 3.90 | 7 of 20 | 4 | none | yes | 1 / 4 |
| 31415 | 0.282 | 2.08 | 40.7 | 3.997 | 3.72 | 10 of 20 | 1 | 3 (by 0.003) | no | 1 / 3 |
| mean +- SD | 0.270 +- 0.033 | 2.13 +- 0.20 | 43.0 +- 2.6 | 4.29 +- 0.53 | 3.12 +- 1.07 | 8.6 +- 1.5 | 3.0 +- 1.6 | | **3 of 5** | 0.6 / 2.8 |
Pass counts: V1n30 passes bars 1-6 in 3 of 5 models and bar 7 in none (A 64.9-68.9%); E4 passes all seven in 3 of 5 (failures: bar 1 and 3 on 11111, bar 3 on 31415). Capacity (offline packing of memories needing every cue->noncue pair >= 4.125 nS, 300 tries; existing values from capacity_d/feas_n30_D0.0175_* and recall_e/feas_E4_*): both recipes hold at most 1 memory of 8 cells (mean 0.6 of 5 models) and 2-4 memories of 6 cells (mean 2.6 / 2.8); the earlier option_B/S1 design (4 memories of 8 cells) is not reachable with either.

## 2. Recall (dynamics_c protocol and criterion; single runs; c 0 / 0.15 / 1.5 / 3.0 nS; GABA on x1 and silenced)
New models (this folder, designs = packed memories: 4+2 on all four, plus 4+4 on E4 s22222). Memories ok / memories; spurious non-member Pyr spikes at c = 3.0 (runaway if > 50):
| model | designs | c 0, 0.15, 1.5 (on and silenced) | c = 3.0, GABA on | c = 3.0, silenced |
|---|---|---|---|---|
| V1n30 s11111 | 2 x (4+2) | 2/2 | 0/2 ok, 0 spurious (no runaway; cross-talk) | 0/2, 0 spurious (no runaway) |
| V1n30 s22222 | 2 x (4+2) | 2/2 | 0/2, 0 spurious | 0/2, 358 spurious (runaway) |
| E4 s11111 | 2 x (4+2) | 2/2 | 0/2, 346 (runaway) | 0/2, 485 |
| E4 s22222 | 3 x (4+2), 1 x (4+4) | 3/3 and 1/1 | 0/3, 418; 0/1, 164 (runaway) | 0/3, 686; 0/1, 245 |
Every memory built recalls at c <= 1.5 in all four models, GABA on and silenced, 0 false 3-cell completions, last non-cue spike 4.52 ms; no inhibitory veto. Cited results for the existing models: V1n30 s16180 and s27182 in dynamics_c (and capacity_d for D 0.0175): perfect at c <= 1.5, silenced runaway at 3.0 in 4 of 4 runs, GABA on near-clean (0-3 stray spikes); E4 s16180 and s27182 in recall_e: perfect at c <= 1.5 (7 of 7 memories), runaway at 3.0 on s27182 with and without GABA (231 and 150 spurious on), none on s16180. V1n30 s31415 and E4 s31415 have no recall run.
So the pattern holds across seeds: at c <= 1.5 recall works for both recipes; at c = 3.0 V1n30 mostly keeps inhibition effective (no runaway with GABA on in 4 of 4 models tested), E4 does not (runaway on in 3 of 4 models tested: s27182, s11111, s22222; none on s16180).

## 3. Scoring against PREREGISTRATION.md (HIT inside the range, PARTIAL up to 25% beyond the edge or one packing step, MISS otherwise)
| item | outcome |
|---|---|
| pass count V1n30 all seven: 0 of 5 | HIT (0) |
| pass count V1n30 bars 1-6: 3 of 5 (2-4) | HIT (3) |
| pass count E4 all seven: 3 of 5 (2-4); P(>= 4) 20%, P(<= 2) 30% | HIT (3) |
| E4 metrics new seeds (p .20-.32, per pair 1.75-2.6, A 36-52, Int->Pyr 3.3-5.8, drivable 5-12, zero 1-4) | HIT 10 of 14 cells; PARTIAL 2 (p 0.321 and zero-input 5, both s11111); MISS 2 (Pyr->Int, next row) |
| E4 Pyr->Int per pair 3.1-4.5 | MISS both new seeds (1.77, 2.15; well below) |
| V1n30 metrics new seeds (p .21-.34, A 61-72, Int->Pyr 5.0-7.5, Pyr->Int 3.0-4.4) | HIT 8 of 8 |
| V1n30 per pair 1.8-2.3 and drivable 13-20 | HIT 2 of 4; PARTIAL 2 (s11111 per pair 1.79; s22222 drivable 12) |
| V1n30 zero-input 1-3 | MISS both new seeds (4, 5) |
| capacity, new seeds: V1n30 4+4 1 (0-2), 4+2 3 (2-4); E4 4+4 1 (0-1), 4+2 3 (2-4) | HIT 8 of 8 (6 of the 8 values sit at the lower edge of their range: 4+4 = 0 in three models, 4+2 = 2 in three) |
| R1 every memory built recalls at c <= 1.5, no false completions | HIT |
| R2 V1n30 c = 3.0 GABA on no runaway in either new seed (55%) | HIT; silenced runaway in both (80%): MISS (1 of 2: s11111 does not run away silenced) |
| R2 E4 c = 3.0 GABA on runaway in at least one new seed (60%) | HIT (both) |
| recommendation rule: E4 if it passes all 7 on >= 3 of 5 and recall clean at c <= 1.5 | applies: E4 (prior 55%) |

## 4. Recommendation
**Recommend E4 (V1, 20 interneurons, pyramidal D 0.0175, interneuron D 0.03) as the headline recipe, with stated limits; do not recommend V1n30 against the current target set.** Reasons: E4 passes all seven bars in 3 of 5 independently grown models (V1n30 in 0 of 5, because A = 65-69% is outside the sourced 25-50% band in every model; V1n30 passes bars 1-6 in 3 of 5), and recall works for every memory that fits. V1n30 is the better choice only if bar 7 is dropped or the inhibitory-fraction band is changed (then 3 of 5 models pass), and it keeps inhibition effective at c = 3.0.
Limits of the recommendation: (a) 3 of 5 is a noisy estimate (exact binomial 95% interval about 15-95%), and E4's passes are marginal (Int->Pyr per pair 3.79-5.15 against the bar at 4, per pair 1.93 against 1.9, drivable 7 of 20 at the bar in two models), so a further regrowth could fail; (b) E4 has 1-5 interneurons with no pyramidal input per model and Pyr->Int per pair varies 1.8-4.0; (c) capacity is small for both recipes (at most one 8-cell memory, 2-4 six-cell memories); (d) inhibition at x1 does not stop runaway at c = 3.0 in E4; (e) the A band is derived (inhib_e/TARGET.md), not measured; 20 interneurons are 17% of cells against about 11.5% in CA3.
**Regrowth-noise caveat.** A recipe is a distribution of networks, not a network: repro_g showed that regrowing the same seed and parameters gives about 30% different node positions and 1-3% different synapse counts, with per-cell and per-pair structure different (so the pass/fail of a bar near its edge can flip on regrowth). The five seeds here are independent realisations, which is why the pass count (3 of 5) and the spread (SD column) are the result, not any single model. Under "grow once, reuse" a given grown model (uuids in models.md for the existing three; the four new ones are in this folder's NetmorphOutput dirs and as `v2-hdh-*` models in the patched instance) is fixed and every analysis here refers to that specific model.
