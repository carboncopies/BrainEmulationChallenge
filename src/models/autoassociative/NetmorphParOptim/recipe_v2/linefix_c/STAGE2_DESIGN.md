# Stage 2 design: 30 interneurons + low pyramidal D (ranking B). Written 2026-11-15 while Stage 1 runs; analysis only
Ledger task tmwidgz0z. Nothing here was launched. Launch only after Stage 1 is scored and John says go.
Scripts and data: sweep_n30.py -> sweep_n30_results.json, sweep_n30.log (the two patched V1n30 runs of ../linefix_b, thresholded); sweep_s2aux.py -> sweep_s2aux_results.json (48-interneuron patched runs at the same thresholds, for scaling S1/V3); grow_pv_s2.py (grow_pv.py plus V1n30/S1n30/V3n30 configs, one-line diff); run_stage2a.sh.

## 1. Method
Same crossing model as Stage 1: in a patched run every accepted synapse stores its pre-post distance, and the arbors do not depend on D_synmax, so keeping only synapses with distance <= D' reproduces a run at D_synmax = D'. Applied to the V1n30 node/synapse files of linefix_b (seed 16180 dir 7c0fa4af..., seed 31415 dir a7758e1f...; D 1.5/0.1). Check: thresholding at 0.1 returns the measured drivable 8-cell values 21 and 19. Stage 1 is the test of whether this is exact; the decision rule in section 5 depends on it.

## 2. What 30 interneurons changes (measured by thresholding)
Pyr->Pyr at the same D is denser than in V1 with 48 interneurons (the +12% / +28% total count John noted), and differently so per seed:

| pyramidal D | V1n30 s16180: prob. / syn per pair / zero-input cells | V1n30 s31415 | V1 48-int s16180 (Stage 1 network) |
|---|---|---|---|
| 0.05 | 0.402 / 3.68 / 4 | 0.510 / 3.67 / 7 | 0.441 / 2.97 / 4 |
| 0.03 | 0.328 / 2.70 / 7 | 0.422 / 2.67 / 9 | |
| 0.025 | 0.302 / 2.44 / 7 | 0.391 / 2.39 / 11 | |
| 0.021 | 0.276 / 2.26 / 9 | 0.358 / 2.17 / 12 | 0.289 / 1.91 / 11 |
| 0.0175 | 0.252 / 2.08 / 10 | 0.328 / 1.97 / 12 | 0.261 / 1.77 |
| 0.015 | 0.231 / 1.94 / 10 | 0.301 / 1.84 / 15 | 0.239 / 1.66 |
| 0.0125 | 0.207 / 1.79 / 13 | 0.271 / 1.69 / 16 | |
| 0.01 | 0.182 / 1.63 / 15 | 0.232 / 1.57 / 16 | 0.184 / 1.45 / 17 |

- Seed 16180 meets both Pyr->Pyr bars (prob. 0.1-0.3, 1.9-4.5 per pair) for pyramidal D about 0.014-0.0245: a much wider window than the 0.021-0.0225 of the 48-interneuron V1.
- Seed 31415 has no D that meets both: probability <= 0.30 needs D <= 0.015, 1.9 per pair needs D >= 0.016. The gap is small (at 0.015: 0.301 and 1.84; at 0.0175: 0.328 and 1.97).
- Cause of the seed difference (inference): the cell count changes the random stream, so each V1n30 seed is a different pyramidal network; s31415 has 27% more Pyr->Pyr contacts.

Interneuron pairs (same D for all three):

| interneuron D | s16180: Int->Pyr per pair / Pyr->Int per pair / drivable 8-cell of 30 (simple) | s31415 |
|---|---|---|
| 0.1 (linefix_b) | 11.83 / 5.47 / 21 (24) | 11.56 / 6.23 / 19 (21) |
| 0.075 | 9.46 / 4.54 / 19 (24) | 9.06 / 5.08 / 17 (21) |
| 0.06 | 7.96 / 3.96 / 18 (23) | 7.62 / 4.38 / 15 (21) |
| 0.05 | 6.87 / 3.51 / 17 (22) | 6.60 / 3.82 / 15 (20) |
| 0.04 | 5.82 / 3.09 / 16 (22) | 5.52 / 3.32 / 13 (19) |
| 0.03 | 4.72 / 2.60 / 13 (18) | 4.45 / 2.81 / 13 (18) |

Int->Pyr 4-9 and Pyr->Int 1.5-4.5 both hold for interneuron D 0.03-0.06 in both seeds; 0.075 breaks both bands.

## 3. Chosen settings (if Stage 1 validates the method; see section 5)
- **Pyramidal D 0.0175.** It is the value where probability and per-pair are closest to both bars across the two seeds: s16180 passes both (0.252, 2.08), s31415 passes per-pair (1.97) and misses probability by 0.028 (0.328). 0.021, the Stage 1 primary, would put s31415 at 0.358; 0.015 would put s31415 at 0.301 and 1.84 (two narrow misses instead of one). Under ranking B (probability first) 0.0175 is preferred to 0.021; it is lower than the Stage 1 primary because the 30-interneuron networks give more synapses per connected pair, which leaves room to go down.
- **Interneuron D 0.05** (all three pairs), as in Stage 1: mid-band for Int->Pyr (6.6-6.9) and Pyr->Int (3.5-3.8), so only the cell count differs from Stage 1.
- All else as linefix_b V1n30: 96 pyramidal + 30 interneurons, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9, V1 arbor settings. Inside bio_ranges.json (D_synmax has a maximum only). Pyramidal D 0.0175 is about 1.2% filling of the 1.5 um reach, not a physical distance; interneuron 0.05 is a third of the 0.15 limit.

## 4. Predictions at pyramidal D 0.0175, interneuron D 0.05
| quantity | V1n30 s16180 | V1n30 s31415 | V1n30 s27182 (no existing run; range) |
|---|---|---|---|
| Pyr->Pyr synapses | 4,768 | 5,893 | 4,500-6,500 |
| Pyr->Pyr connection prob. | 0.252 | 0.328 | 0.24-0.34 |
| Pyr->Pyr syn per connected pair | 2.08 | 1.97 | 1.9-2.2 |
| pyramidal cells with no Pyr input | 10 | 12 | 8-14 |
| Int->Pyr synapses / prob. / per pair | 10,621 / 0.536 / 6.87 | 11,975 / 0.630 / 6.60 | per pair 6.2-7.3 |
| pyramidal targets per interneuron | 51.5 | 60.5 | 50-62 |
| Pyr->Int synapses / prob. / per pair | 4,020 / 0.397 / 3.51 | 4,677 / 0.425 / 3.82 | per pair 3.3-4.4 |
| Int->Int synapses / per pair | 3,040 / 6.01 | 3,145 / 6.90 | per pair 5.8-7.2 |
| drivable 8-cell of 30 (simple) | 17 (22) | 15 (20) | 14-19 |
| interneurons with no pyramidal input | 2 | 1 | 0-3 |
| A, inhibitory fraction (reported, not gated) | 69.0% | 67.0% | 65-71% |
| interneuron axon / dendrite length (um) | 46,317 / 6,586 | 46,234 / 6,681 | 45,000-47,500 / 6,500-7,200 |

A stays near 67-69% because A depends on the D ratio (0.05 / 0.0175), not on cell count: going from 48 to 30 interneurons lowered A at D 1.5/0.1 from 7.5% to about 5%, but ranking B moves the D ratio by a factor of about 40.

Drivable bar. The bar so far was 16 of 48 (one third). With 30 interneurons I propose the same fraction, **10 of 30**, as the gate, and I report against 16 as well. Against an absolute 16, s31415 is predicted to miss by 1 (15), and no interneuron D inside the per-pair bands fixes that (0.06 also gives 15). John to confirm which bar applies.

S1 and V3 with 30 interneurons (no node files exist; scaled from their 48-interneuron patched runs with the V1 48->30 ratios, so ranges only). The 48->30 change raised Int->Pyr per pair by x1.08-1.32 in V1, which at interneuron D 0.05 would push S1 (7.86 at 48) to 8.5-10.4 and V3 (7.24) to 7.8-9.6, at or over the 9 limit. So for S1n30 and V3n30 the interneuron D is **0.04**:

| quantity (pyr D 0.0175, int D 0.04) | S1n30 s16180 | V3n30 s16180 |
|---|---|---|
| Pyr->Pyr connection prob. | 0.26-0.35 | 0.27-0.36 |
| Pyr->Pyr syn per connected pair | 1.8-2.1 | 2.0-2.3 |
| Int->Pyr per connected pair | 7.1-8.7 | 6.6-8.0 |
| Pyr->Int per connected pair | 2.3-2.8 | 3.0-3.6 |
| drivable 8-cell of 30 | 10-17 | 13-20 |
| A | 62-72% | 62-72% |

## 5. Decision rule (written before Stage 1 is scored)
Let f = measured / predicted Pyr->Pyr synapse count in Stage 1 run B1, and g = measured / predicted Int->Pyr synapses per connected pair in B1.
1. **Method holds** (B1, B2, B3 arbors identical to the linefix V1 run and all counts within +-2%): Stage 2 uses the settings of section 3 (pyramidal 0.0175, interneuron 0.05) whether or not B1 itself lands inside both Pyr->Pyr bars. Reason: B1's pass/fail is a knife edge specific to the 48-interneuron network; the 30-interneuron sweep is then exact and is the better guide.
2. **Arbors identical but counts off by more than 2%** (thresholding is not a rerun): rescale. Pyramidal D = 0.0175 / f, interneuron D = 0.05 / g, each rounded to 3 significant digits and kept inside 0.010-0.030 and 0.030-0.060. The section 4 predictions then carry over unchanged as targets, with tolerance widened to +-10%. If f or g is outside 0.7-1.4, do not launch; find the cause first.
3. **Arbors not identical in any Stage 1 run** (new realisation): no rescaling is possible from one run. Launch only V1n30 s16180 at 0.0175 / 0.05 as a single probe and treat the section 4 numbers as ranges (probability 0.22-0.36, per pair 1.8-2.4).
4. **A Stage 1 run failed** (rc non-zero, missing output): rerun that run once before anything else.

## 6. Run plan (max 3 concurrent, patched instance on 8010/8011 must be up)
- Batch 1: V1n30 seeds 16180, 31415, 27182 at the rule's D values (run_stage2a.sh DPP DI). About 50-60 min wall each (linefix_b V1n30 walls 2,873 and 3,387 s).
- Batch 2, only if batch 1 s16180 and s31415 match their predictions: S1n30 and V3n30 seed 16180 at pyramidal 0.0175, interneuron 0.04. They cost about as much as a V1n30 run, so they are cheap; the third slot stays empty unless John wants a repeat.
- Not planned: reruns of seed 16180/31415 at other D values. If the method holds, thresholding gives those for free (section 2 tables).

## 7. Success bar (ranking B, priority order; A reported, not gated)
1. Pyr->Pyr connection probability 0.1-0.3. 2. Pyr->Pyr synapses per connected pair 1.9-4.5. 3. Int->Pyr per pair 4-9. 4. Pyr->Int per pair 1.5-4.5. 5. Drivable 8-cell >= 10 of 30 (proposed; 16 also reported). 6. Nothing outside bio_ranges.json.
Expected: s16180 passes all six. s31415 passes all but bar 1 (0.328). s27182 unknown, about 50% to pass bar 1. A network that passes bars 1 and 2 on all seeds is not available at one pyramidal D: the per-seed window is narrower than the seed-to-seed spread.
