# linefix_c: low pyramidal D on the line-379-fixed build (ranking B). Stage 1 scored 2026-11-15 (ledger tmwidgz0z)
Ranking B (John): Pyr->Pyr connection probability 0.1-0.3 first, synapses per connected pair 1.9-4.5 second. A (inhibitory fraction) is reported, not gated.
Files: DESIGN.md (analysis + Stage 1 design; old ranking-A design kept as section 4), PREREGISTRATION.md (written before launch, not edited), STAGE2_DESIGN.md and PREREGISTRATION_stage2.md (written while Stage 1 ran, before scoring; nothing launched), grow_pv.py (usage: V1 SEED DPP DI; API port 8010), run_stage1.sh, analyze_pv.py -> pv_results.json, stage1.py -> stage1_results.json, pairs.py / sweep.py / sweep_n30.py / sweep_s2aux.py (read-only threshold analyses), grow_V1_s16180_*/.
Patched build /home/johnjose/BrainGenix/wt/nes-linefix (line 379 `tx/PQ`), NES 8011 / API 8010 (PIDs 599987 / 600788, started by arbor-seeds). Main NES/API and main repo untouched. No commit, no push.

## Stage 1 runs (V1, 96 pyramidal + 48 interneurons, seed 16180, interneuron D 0.05)
Launched 21:38 after linefix_b's queue had ended and no growth run remained; all three verified running at 150 s. rc 0 in 3 of 3, "Deleted resident simulation" in 3 of 3, walls 2,231 / 2,232 / 2,182 s, bio_check pass, D_synmax read back from each .nibr.clp (0.021 / 0.01 / 0.05 and 0.05 x3). Output dirs: B1 4cded057-..., B2 de28ea38-..., B3 4453c83b-... under linefix-instance/out.
Arbors: interneuron axon 45,207.09 um, interneuron dendrite 6,733.74, pyramidal dendrite 24,165.88, pyramidal axon 19,042.74 in all three, equal to the linefix V1 run to 9 digits.

## Results against predictions (measured / predicted)
| quantity | B1 pyr D 0.021 | B2 pyr D 0.01 | B3 pyr D 0.05 |
|---|---|---|---|
| Pyr->Pyr synapses | 5,019 / 5,021 HIT | 2,468 / 2,425 HIT (+1.8%) | 11,878 / 11,942 HIT |
| Pyr->Pyr connection prob. | 0.288 / 0.289 HIT | 0.184 / 0.184 HIT | 0.439 / 0.441 HIT |
| Pyr->Pyr syn per connected pair | 1.91 / 1.91 HIT | 1.47 / 1.45 HIT | 2.96 / 2.97 HIT |
| pyramidal cells with no Pyr input | 8 / 11 MISS | 15 / 17 MISS | 5 / 4 HIT |
| A (reported only) | 74.1% / 74.1% HIT | 85.3% / 85.5% HIT | 54.7% / 54.6% HIT |
| Int->Pyr synapses (pred. 14,345) | 14,388 HIT | 14,280 HIT | 14,360 HIT |
| Int->Pyr prob. (0.60) / per pair (5.21) | 0.593 / 5.26 HIT | 0.594 / 5.22 HIT | 0.595 / 5.24 HIT |
| targets per interneuron (57.4) | 57.0 | 57.0 | 57.1 |
| Pyr->Int synapses (7,960) | 7,944 HIT | 8,130 MISS (+2.1%) | 8,065 HIT |
| Pyr->Int prob. (0.46) / per pair (3.77) | 0.452 / 3.82 HIT | 0.458 / 3.85 MISS (per pair +0.08) | 0.458 / 3.82 HIT |
| Int->Int synapses (9,121) / per pair (7.09) | 9,122 / 7.12 HIT | 9,089 / 7.13 HIT | 9,038 / 7.05 HIT |
| drivable 8-cell of 48 (26), simple (32) | 26 (32) HIT | 25 (33) HIT | 25 (33) HIT |
| interneurons with no pyramidal input (6) | 5 HIT | 3 MISS | 6 HIT |
| arbor length ratio 1.000 | HIT | HIT | HIT |
Tolerances as preregistered: counts +-2%, probabilities +-0.01, per pair +-0.05, drivable and zero-input +-1. Score: 37 HIT, 5 MISS of 42 scored items (targets per interneuron had no stated tolerance; it is 0.7% low).

## Success bar (ranking B)
| bar | B1 | B2 | B3 |
|---|---|---|---|
| 1. Pyr->Pyr prob. 0.1-0.3 | 0.288 pass | 0.184 pass | 0.439 FAIL |
| 2. Pyr->Pyr per pair 1.9-4.5 | 1.91 pass | 1.47 FAIL | 2.96 pass |
| 3. Int->Pyr per pair 4-9 | 5.26 pass | 5.22 pass | 5.24 pass |
| 4. Pyr->Int per pair 1.5-4.5 | 3.82 pass | 3.85 pass | 3.82 pass |
| 5. drivable 8-cell >= 16 | 26 pass | 25 pass | 25 pass |
| 6. inside bio_ranges.json | pass | pass | pass |
B1 (pyramidal D 0.021, interneuron D 0.05) passes all six, as predicted, bars 1 and 2 by 0.012 and 0.01. B2 and B3 each fail the one bar predicted. A is 74% for B1: far above any biological inhibitory fraction, reported not gated.

## What Stage 1 shows
- Thresholding the stored synapse distance predicts a rerun at lower D to within about 2% on counts, 0.01 on probability and 0.08 on synapses per pair (measured, 3 runs).
- It is not exact. The three runs have identical arbors and identical interneuron D, yet their interneuron-pair counts differ (Pyr->Int 7,944 / 8,130 / 8,065; Int->Pyr 14,388 / 14,280 / 14,360). So synapse selection has run-to-run noise of about 1-2% at fixed arbors. Cause not investigated (inference: a random draw in synapse placement that is not tied to the growth random stream).
- Counts of cells with zero input are the noisiest items (3 of the 5 misses); they depend on single synapses.
- The 0.021 result is a knife edge: 1.91 per pair against a 1.9 bar, with run-to-run noise of about 0.02.

## Stage 2 batch 1 (V1, 96 pyramidal + 30 interneurons, pyramidal D 0.0175, interneuron D 0.0495), scored 2026-11-15
Settings from the preregistered decision rule, applied literally: Stage 1 arbors identical but one count outside +-2% (B2 Pyr->Int +2.1%), so rule 2: f = 5,019 / 5,021 = 1.000, g = 5.26 / 5.21 = 1.010, pyramidal D 0.0175, interneuron D 0.0495, tolerance +-10% for seeds 16180 and 31415.
Launched 22:44 with no other growth run active (`./run_stage2a.sh 0.0175 0.0495`, driver grow_pv_s2.py = grow_pv.py plus 30-interneuron configs); all three verified running at 150 s. rc 0 in 3 of 3, "Deleted resident simulation" in 3 of 3, walls 1,589 / 1,838 / 1,657 s, bio_check pass, D_synmax read back from each .nibr.clp. Output dirs: s16180 e882c1f4-..., s31415 d2406438-..., s27182 4fe0548b-.... Data: pv_results_stage2.json, stage2_results.json, analyze_stage2.log (Stage 1 copies: pv_results_stage1.json, stage1_results.json).

Arbors: s16180 identical to its linefix_b run (interneuron axon 46,317.51, dendrite 6,586.84, pyramidal dendrite 23,918.18). **s31415 is a new realisation**: interneuron axon 47,349 against 46,235 in linefix_b (+2.4%), interneuron dendrite 6,535 against 6,682 (-2.2%), pyramidal dendrite 25,871 against 25,737 (+0.5%). So, as preregistered, s31415 is scored against the range column, not the exact column.

| quantity | s16180 measured / predicted | s31415 measured (range) | s27182 measured (range) |
|---|---|---|---|
| Pyr->Pyr synapses | 4,692 / 4,768 HIT (-1.6%) | 5,545 (4,500-6,500) HIT | 4,548 HIT |
| Pyr->Pyr connection prob. | 0.251 / 0.252 HIT | 0.308 (0.24-0.34) HIT | 0.241 HIT |
| Pyr->Pyr syn per connected pair | 2.05 / 2.08 HIT | 1.97 (1.9-2.2) HIT | 2.07 HIT |
| pyramidal cells with no Pyr input | 7 / 10 MISS | 9 (8-14) HIT | 17 MISS |
| Int->Pyr synapses | 10,387 / 10,621 HIT (-2.2%) | 11,034 | 8,404 |
| Int->Pyr prob. / per pair | 0.535 / 6.74 against 0.536 / 6.87 HIT | 0.622 / 6.16 (6.2-7.3) MISS by 0.04 | 0.498 / 5.86 MISS |
| pyramidal targets per interneuron | 51.4 / 51.5 HIT | 59.7 (50-62) HIT | 47.8 MISS |
| Pyr->Int synapses | 3,920 / 4,020 HIT (-2.5%) | 4,677 | 4,705 |
| Pyr->Int prob. / per pair | 0.393 / 3.46 against 0.397 / 3.51 HIT | 0.432 / 3.76 (3.3-4.4) HIT | 0.407 / 4.01 HIT |
| Int->Int synapses / per pair | 3,022 / 5.98 against 3,040 / 6.01 HIT | 2,988 / 6.29 (5.8-7.2) HIT | 2,897 / 6.45 HIT |
| drivable 8-cell of 30 (simple) | 16 (22) / 17 (22) HIT | 16 (20) (14-19) HIT | 17 (17) HIT |
| interneurons with no pyramidal input | 1 / 2 HIT | 1 (0-3) HIT | 2 HIT |
| A (reported only) | 68.9% / 69.0% HIT | 66.6% (65-71) HIT | 64.9% MISS by 0.1 |
| interneuron axon / dendrite length (um) | 46,317 / 6,587, ratio 1.000 HIT | 47,349 / 6,535 (ranges) HIT | 43,289 MISS / 6,709 HIT |
Score: s16180 13 HIT, 1 MISS; s31415 12 HIT, 1 MISS (on ranges); s27182 8 HIT, 5 MISS (ranges were built from two seeds and were too narrow for a third: its interneuron axons are 6.5% shorter). The interneuron counts of s16180 are 2.2-2.5% under the D 0.05 prediction; about 1 point of that is the D 0.0495 rescale, the rest run-to-run noise.

### Success bar (ranking B). Bar 5 is a proportional bar, 10 of 30 (the same one third as 16 of 48), chosen by John on 2026-11-15
| bar | s16180 | s31415 | s27182 |
|---|---|---|---|
| 1. Pyr->Pyr prob. 0.1-0.3 | 0.251 pass | 0.308 FAIL (by 0.008) | 0.241 pass |
| 2. Pyr->Pyr per pair 1.9-4.5 | 2.05 pass | 1.97 pass | 2.07 pass |
| 3. Int->Pyr per pair 4-9 | 6.74 pass | 6.16 pass | 5.86 pass |
| 4. Pyr->Int per pair 1.5-4.5 | 3.46 pass | 3.76 pass | 4.01 pass |
| 5. drivable 8-cell >= 10 of 30 (raw count) | 16 of 30 pass | 16 of 30 pass | 17 of 30 pass |
| 6. inside bio_ranges.json | pass | pass | pass |
Two of three seeds pass all six bars; s31415 misses only the probability bar, by 0.008 (predicted miss was 0.028). Raw drivable counts 16, 16, 17 of 30 would also meet an absolute bar of 16. A is 65-69% in all three: reported, not gated, and far above any biological inhibitory fraction.

### What Stage 2 shows
- With 30 interneurons, pyramidal D 0.0175 and interneuron D about 0.05 put all four per-pair/probability measures inside or within 0.01 of their bands on three seeds (measured).
- Same seed did not reproduce the arbors for s31415 (second such case; the first was V1 s27182 in pv_dsyn015). Cause not investigated. Exact predictions hold only when arbor lengths match; always compare them first.
- Remaining mismatches with biology, not addressed by these settings: A 65-69%; 7-17 of 96 pyramidal cells receive no Pyr input; the pyramidal D means about 1.2% filling of the 1.5 um reach, not a physical distance.

## Stage 2 batch 2 (S1 and V3 with 30 interneurons, pyramidal D 0.0175, interneuron D 0.04), scored 2026-11-16
John approved running it although the batch 1 condition was not cleanly met. Preregistered in PREREGISTRATION_stage2.md (seed 16180 ranges) and PREREGISTRATION_stage2b.md (seed 27182 ranges, run mechanics), both written before launch and not edited.
Launched 06:43 with `run_stage2b.sh` (gate: a run starts only when fewer than 3 growth processes are active machine-wide). Starts 06:43, 06:44, 06:44, 07:17; never more than 3 growth sims. Verified running at 200 s. rc 0 in 4 of 4, "Deleted resident simulation" in 4 of 4, walls 2,794 (S1n30 s16180) / 2,021 (V3n30 s16180) / 2,740 (S1n30 s27182) / 2,207 (V3n30 s27182) s, bio_check pass, D_synmax read back (0.0175 / 0.04 x3), 96 + 30 cells. Data: pv_results_stage2b.json, stage2b_results.json, analyze_stage2b.log. No growth or dynamics process of another worker was seen in ps at launch, at 200 s or at the end.

| quantity (measured; preregistered range) | S1n30 s16180 | V3n30 s16180 | S1n30 s27182 | V3n30 s27182 |
|---|---|---|---|---|
| Pyr->Pyr synapses | 5,752 | 4,366 | 4,202 | 5,329 |
| Pyr->Pyr connection prob. | 0.3003 (0.26-0.35) HIT | 0.240 (0.27-0.36) MISS | 0.266 (0.22-0.36) HIT | 0.272 (0.22-0.36) HIT |
| Pyr->Pyr syn per connected pair | 2.10 (1.8-2.1) HIT | 1.99 (2.0-2.3) MISS by 0.01 | 1.73 (1.75-2.2) MISS by 0.02 | 2.15 (1.85-2.35) HIT |
| Int->Pyr synapses / prob. | 16,701 / 0.655 | 10,139 / 0.535 | 11,004 / 0.604 | 11,088 / 0.537 |
| Int->Pyr per connected pair | 8.85 (7.1-8.7) MISS | 6.58 (6.6-8.0) MISS by 0.02 | 6.32 (6.0-9.0) HIT | 7.16 (5.8-8.4) HIT |
| Pyr->Int synapses / prob. | 3,047 / 0.382 | 6,114 / 0.543 | 2,992 / 0.354 | 4,016 / 0.424 |
| Pyr->Int per connected pair | 2.77 (2.3-2.8) HIT | 3.91 (3.0-3.6) MISS | 2.94 (2.2-4.8) HIT | 3.29 (2.8-3.9) HIT |
| Int->Int synapses / per pair | 3,775 / 7.07 | 5,692 / 9.15 | 3,133 / 6.75 | 3,669 / 6.86 |
| drivable 8-cell of 30 (simple) | 13 (18) (10-17) HIT | 20 (22) (13-20) HIT | 13 (16) (9-18) HIT | 14 (21) (12-20) HIT |
| A (reported only) | 74.4% (62-72) MISS | 69.9% (62-72) HIT | 72.4% (60-74) HIT | 67.5% (60-74) HIT |
| pyramidal cells with no Pyr input | 8 | 13 | 14 | 19 |
| interneurons with no pyramidal input | 2 | 1 | 3 | 1 |
| targets per interneuron (of 96) | 62.9 | 51.3 | 58.0 | 51.6 |
| interneuron axon / dendrite length (um) | 81,138 / 6,474 | 58,962 / 9,312 | 73,982 / 6,452 | 59,103 / 9,328 |
Score: 17 HIT, 7 MISS of 24 range items (I expected about one in four outside; it was 7 of 24, three of them by 0.01-0.02).

### Success bar (ranking B; bar 5 is the proportional 10 of 30 chosen by John on 2026-11-15)
| bar | S1n30 s16180 | V3n30 s16180 | S1n30 s27182 | V3n30 s27182 |
|---|---|---|---|---|
| 1. Pyr->Pyr prob. 0.1-0.3 | 0.3003 FAIL (3 pairs over: 2,739 of 9,120; limit 2,736) | 0.240 pass | 0.266 pass | 0.272 pass |
| 2. Pyr->Pyr per pair 1.9-4.5 | 2.10 pass | 1.99 pass | 1.73 FAIL | 2.15 pass |
| 3. Int->Pyr per pair 4-9 | 8.85 pass | 6.58 pass | 6.32 pass | 7.16 pass |
| 4. Pyr->Int per pair 1.5-4.5 | 2.77 pass | 3.91 pass | 2.94 pass | 3.29 pass |
| 5. drivable 8-cell >= 10 of 30 (raw count) | 13 of 30 pass | 20 of 30 pass | 13 of 30 pass | 14 of 30 pass |
| 6. inside bio_ranges.json | pass | pass | pass | pass |
V3n30 passes all six bars on both seeds. S1n30 fails one Pyr->Pyr bar on each seed (s16180 probability by 0.0003, inside run-to-run noise; s27182 per pair 1.73). Against an absolute drivable bar of 16 only V3n30 s16180 would pass.

## All Stage 2 runs together (pyramidal D 0.0175, 30 interneurons)
| variant (interneuron D) | seeds passing all six bars | the failures |
|---|---|---|
| V1n30 (0.0495) | 2 of 3 | s31415 probability 0.308 |
| V3n30 (0.04) | 2 of 2 | none |
| S1n30 (0.04) | 0 of 2 | s16180 probability 0.3003; s27182 per pair 1.73 |
- Over 7 runs: Pyr->Pyr probability 0.240-0.308, per pair 1.73-2.15, Int->Pyr per pair 5.86-8.85, Pyr->Int per pair 2.77-4.01, drivable 13-20 of 30, A 65-74% (measured).
- Bars 3-6 pass in 7 of 7. Every failure is a Pyr->Pyr bar missed by a small margin: the seed-to-seed spread of probability and per-pair values is about as wide as the window that satisfies both.
- S1 (longest interneuron axons, 74,000-81,000 um) runs closest to the Int->Pyr limit (8.85 at D 0.04) and has the lowest drivable counts; V3 is the most robust variant here.
- Not addressed by these settings: A 65-74% (reported, not gated); 7-19 of 96 pyramidal cells receive no Pyr input; pyramidal D 0.0175 is about 1.2% filling of the 1.5 um reach, not a physical distance.

The patched instance (PIDs 599987 / 600788) is still up, as John asked, until arbor-seeds' recall/dynamics check is also done. Stop commands are in ../linefix/README.md.
