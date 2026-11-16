# Preregistration, linefix_c Stage 2 (30 interneurons, ranking B). Written 2026-11-15 before Stage 1 finished and before any Stage 2 launch; not to be edited after launch.
Ledger task tmwidgz0z. Reasoning and tables: STAGE2_DESIGN.md. Predictions come from thresholding the stored synapse distances of the two patched V1n30 runs in ../linefix_b (sweep_n30_results.json), so for seeds 16180 and 31415 they are exact if arbors reproduce and the method holds.

## Settings and decision rule (fixed before Stage 1 is scored)
f = measured / predicted Pyr->Pyr synapse count in Stage 1 run B1; g = measured / predicted Int->Pyr synapses per connected pair in B1.
1. Stage 1 arbors identical to the linefix V1 run and all counts within +-2%: pyramidal D 0.0175, interneuron D 0.05 (all three interneuron pairs), regardless of whether B1 lands inside both Pyr->Pyr bars.
2. Arbors identical, counts off by more than 2%: pyramidal D = 0.0175 / f, interneuron D = 0.05 / g, 3 significant digits, kept inside 0.010-0.030 and 0.030-0.060; predictions below stand as targets with tolerance +-10%. f or g outside 0.7-1.4: no launch.
3. Arbors not identical in any Stage 1 run: only V1n30 s16180 at 0.0175 / 0.05 as a probe; predictions become ranges (probability 0.22-0.36, per pair 1.8-2.4).
4. A Stage 1 run failed: rerun it once first.
All else: patched build (API port 8010), V1 arbor settings, 96 pyramidal + 30 interneurons, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9. Inside bio_ranges.json. Pyramidal D 0.0175 means about 1.2% filling of the 1.5 um reach, not a physical distance.

## Runs
Batch 1: V1n30 seeds 16180, 31415, 27182. Batch 2 (only if batch 1 seeds 16180 and 31415 match): S1n30 and V3n30 seed 16180 with pyramidal D as batch 1 and interneuron D 0.04. Max 3 concurrent sims.

## Predictions, batch 1 (pyramidal 0.0175, interneuron 0.05)
| quantity | s16180 | s31415 | s27182 (range; no existing run) |
|---|---|---|---|
| Pyr->Pyr synapses | 4,768 | 5,893 | 4,500-6,500 |
| Pyr->Pyr connection prob. | 0.252 | 0.328 | 0.24-0.34 |
| Pyr->Pyr syn per connected pair | 2.08 | 1.97 | 1.9-2.2 |
| pyramidal cells with no Pyr input | 10 | 12 | 8-14 |
| Int->Pyr synapses | 10,621 | 11,975 | |
| Int->Pyr prob. / per pair | 0.536 / 6.87 | 0.630 / 6.60 | per pair 6.2-7.3 |
| pyramidal targets per interneuron | 51.5 | 60.5 | 50-62 |
| Pyr->Int synapses | 4,020 | 4,677 | |
| Pyr->Int prob. / per pair | 0.397 / 3.51 | 0.425 / 3.82 | per pair 3.3-4.4 |
| Int->Int synapses / per pair | 3,040 / 6.01 | 3,145 / 6.90 | per pair 5.8-7.2 |
| drivable 8-cell of 30 (simple) | 17 (22) | 15 (20) | 14-19 |
| interneurons with no pyramidal input | 2 | 1 | 0-3 |
| A (reported, not gated) | 69.0% | 67.0% | 65-71% |
| interneuron axon / dendrite length (um) | 46,317 / 6,586 | 46,234 / 6,681 | 45,000-47,500 / 6,500-7,200 |
Tolerances for seeds 16180 and 31415: counts +-2%, probabilities +-0.01, synapses per pair +-0.05, drivable +-1, zero-input counts +-1, arbor lengths ratio 1.000.

## Predictions, batch 2 (pyramidal 0.0175, interneuron 0.04; scaled from 48-interneuron runs, ranges only)
| quantity | S1n30 s16180 | V3n30 s16180 |
|---|---|---|
| Pyr->Pyr connection prob. | 0.26-0.35 | 0.27-0.36 |
| Pyr->Pyr syn per connected pair | 1.8-2.1 | 2.0-2.3 |
| Int->Pyr per connected pair | 7.1-8.7 | 6.6-8.0 |
| Pyr->Int per connected pair | 2.3-2.8 | 3.0-3.6 |
| drivable 8-cell of 30 | 10-17 | 13-20 |
| A | 62-72% | 62-72% |

## Success bar (ranking B, priority order; A reported, not gated)
1. Pyr->Pyr connection probability 0.1-0.3. 2. Pyr->Pyr synapses per connected pair 1.9-4.5. 3. Int->Pyr per connected pair 4-9. 4. Pyr->Int per connected pair 1.5-4.5. 5. Drivable 8-cell >= 10 of 30 (same fraction as 16 of 48; the result against 16 is reported too, and John decides which applies). 6. Nothing outside bio_ranges.json.
Expected: s16180 passes all. s31415 passes all but bar 1 (0.328). s27182: about 50% to pass bar 1. Batch 2: about 40% each to pass bar 1.

## What would count against the method
Seeds 16180 or 31415 with arbors identical to their linefix_b runs but counts outside +-2%. Arbors not identical: new realisation (seen in 1 of 9 earlier same-seed runs); score that run against the s27182 ranges instead.
