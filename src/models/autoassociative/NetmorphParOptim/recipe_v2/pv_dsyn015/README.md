# D_synmax 0.1 -> 0.15 on the three interneuron pairs, seed 16180 (own NES 8000/7999/8001), 2026-11-15
Scripts: grow_pv.py (diff vs ../pv_arbor_seeds/grow_pv.py: only paths, run tag `_d015`, model name `v2-pvd-`, and the three interneuron D_synmax values 0.1 -> 0.15), run_all.sh, measure.py (unchanged), analyze_pv.py (paths, tag-parsing and a 0.15 check in the run lookup), xdir.py (read-only +x direction check). Data: pv_results.json (3 runs), xdir.log, analyze.log, dirs.txt, grow_*_d015/. PREREGISTRATION.md was written before launch and not edited.
Setup: S1 (axon B_inf 26, dend 3.5), V1 (20, 3.5), V3 (23, 5); 96 pyramidal, 48 interneurons, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9, seed 16180, D_synmax 1.5 pyr-pyr and 0.15 for Pyr->Int, Int->Pyr, Int->Int. Baselines: the existing seed-16180 runs at D 0.1 in ../pv_arbor_seeds (not re-run). Pre-flight per run: .nibr.clp read back shows D_synmax 1.5 / 0.15 / 0.15 / 0.15 (all 3), bio_check pass (all 3). Each run deleted its resident simulation (run.log, 3 of 3). rc 0, walls S1 3487 s, V1 2005 s, V3 2747 s, 3 concurrent, no NES restart.

## 1. Per-run table (new vs baseline, same seed)
| run | D_synmax int | dend len | axon len | axon reach | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | syn/pair I->P | targets/int | inhib A / B (%) | drivable 8-cell (simple) | zero-input |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 baseline | 0.1 | 6629 | 74624 | 143 | 73105 | 348 | 1616 | 685 | 1.60 | 21.0 | 2.16 / 3.04 | 2 (8) | 14 |
| S1 new | 0.15 | 6629 | 74624 | 143 | 73200 | 743 | 3237 | 1437 | 2.10 | 32.1 | 4.23 / 5.95 | 6 (15) | 9 |
| V1 baseline | 0.1 | 6733 | 45207 | 146 | 70921 | 461 | 876 | 509 | 1.38 | 13.3 | 1.22 / 1.90 | 4 (11) | 17 |
| V1 new | 0.15 | 6733 | 45207 | 145 | 70911 | 971 | 1845 | 1105 | 1.69 | 22.8 | 2.54 / 3.94 | 9 (17) | 13 |
| V3 baseline | 0.1 | 9405 | 55380 | 141 | 86230 | 573 | 1364 | 717 | 1.56 | 18.3 | 1.56 / 2.34 | 2 (14) | 12 |
| V3 new | 0.15 | 9405 | 55380 | 141 | 85887 | 1142 | 2691 | 1584 | 2.03 | 27.6 | 3.04 / 4.68 | 10 (22) | 7 |

Ratio new / baseline:
| variant | dend len | axon len | reach | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | syn/pair | targets/int |
|---|---|---|---|---|---|---|---|---|---|
| S1 | 1.000 | 1.000 | 0.996 | 1.001 | 2.14 | 2.00 | 2.10 | 1.31 | 1.53 |
| V1 | 1.000 | 1.000 | 0.997 | 1.000 | 2.11 | 2.11 | 2.17 | 1.22 | 1.71 |
| V3 | 1.000 | 1.000 | 0.998 | 0.996 | 1.99 | 1.97 | 2.21 | 1.30 | 1.51 |

Pooled over the three variants (sum new / sum baseline): Pyr->Int 2.07, Int->Pyr 2.02, Int->Int 2.16.
Inhibitory fraction A / B rises from 2.16 / 3.04 to 4.23 / 5.95 (S1), 1.22 / 1.90 to 2.54 / 3.94 (V1), 1.56 / 2.34 to 3.04 / 4.68 (V3).

## 2. Direction check (read-only, xdir.py)
Method: for each Int->Pyr AMPA/GABA synapse in the synapse file, the presynaptic axon fiber piece ID (column 9) is matched to the node with that fiber piece label in the node files; the segment is node minus parent node; cosine of that vector to +x. Baseline S1 reproduces the FABLE_ANALYSIS figures (57.0% of synapse-carrying segments with cosine > 0.9; 4.69% of all interneuron axon segments), so the method matches section 1.3 there.
| run | n Int->Pyr synapses | segments cos(+x)>0.9, synapse-carrying | median cos | all interneuron axon segments cos>0.9 |
|---|---|---|---|---|
| S1 baseline D 0.1 | 1616 | 57.0% | 0.925 | 4.69% |
| S1 D 0.15 | 3237 | 53.6% | 0.912 | 4.69% |
| V1 baseline | 876 | 56.5% | 0.925 | 4.83% |
| V1 D 0.15 | 1845 | 54.0% | 0.915 | 4.84% |
| V3 baseline | 1364 | 58.4% | 0.934 | 4.82% |
| V3 D 0.15 | 2691 | 52.1% | 0.911 | 4.84% |
Measured: the +x preference stays strong (52-54% of the segments carrying synapses vs 4.7-4.8% of all), falling only 2.5-6 points when D rises to 0.15.

## 3. Scored preregistration
- Item 1, arbors unchanged: HIT. Axon and dendrite length identical to the um in all 3 runs (ratio 1.000), reach ratio 0.996-0.998, Pyr->Pyr ratios 1.001 / 1.000 / 0.996 (predicted +-3% / +-10% / +-15% bounds).
- Item 2, synapse counts: Int->Pyr S1 3237 (pred 3135, 2750-3550) HIT, V1 1845 (1700, 1490-1930) HIT, V3 2691 (2646, 2320-3000) HIT. Pyr->Int S1 743 (675, 590-770) HIT, V1 971 (894, 780-1010) HIT, V3 1142 (1112, 970-1260) HIT. Int->Int S1 1437 (1330, 1160-1500) HIT, V1 1105 (987, 860-1120) HIT, V3 1584 (1391, 1220-1580) PARTIAL (4 above the range).
- Item 3, syn/pair and targets: syn/pair S1 2.10 (1.9, 1.75-2.1) HIT, V1 1.69 (1.6, 1.5-1.8) HIT, V3 2.03 (1.8, 1.65-2.0) PARTIAL (just above). Targets per interneuron S1 32.1 (31, 28-35) HIT, V1 22.8 (20, 18-23) HIT, V3 27.6 (27, 24-31) HIT.
- Item 4, inhibitory fractions A and B: all six HIT (A 4.23 / 2.54 / 3.04 vs 4.1 / 2.3 / 2.9; B 5.95 / 3.94 / 4.68 vs 5.7 / 3.6 / 4.4, all within the stated ranges).
- Item 5, drivable 8-cell S1 6, V1 9, V3 10 (predicted 6, 8, 7; ranges 3-10, 5-12, 4-11) HIT; none at 16 HIT (max 10); simple count 15 / 17 / 22 (ranges 14-24, 15-26, 19-30) HIT; zero-input 9 / 13 / 7 (ranges 4-11, 5-13, 3-10) HIT.
- Item 6, +x fraction falls to about 45% (38-52%): MISS (53.6 / 54.0 / 52.1%; the fall was real but smaller).
- Main claim (Fable's x1.8-2.1 with unchanged arbors): PARTIAL under my pre-set rule. Arbors unchanged exactly; Int->Pyr (2.02) and Pyr->Int (2.07) pooled ratios are inside 1.8-2.1, but pooled Int->Int (2.16) is just above 2.1 and several single runs are 2.10-2.21 (all inside the 1.6-2.3 partial band). Per run Int->Pyr 2.00 / 2.11 / 1.97.
Overall: 20 of 24 itemised numbers hit, 2 partial, 1 miss (+x fraction), main claim partial.

## 4. Verdict
Measured: raising D_synmax on the three interneuron pairs from 0.1 to 0.15 leaves every arbor property unchanged (lengths identical, reach, Pyr->Pyr within 0.4%) and multiplies Int->Pyr by 1.97-2.11, Pyr->Int by 1.99-2.14 and Int->Int by 2.10-2.21 (pooled 2.02 / 2.07 / 2.16). Fable's prediction (x1.94, plausible 1.8-2.1) holds for Int->Pyr and Pyr->Int and is exceeded slightly for Int->Int (about 10% above the stated upper end, 2.16 vs 2.1). Synapses per pair rise by 1.2-1.3 and targets per interneuron by 1.5-1.7, so the counts rise by both more connected pairs and more synapses per pair.
Stop rule: as written ("x1.8-2.1 with unchanged arbors") it fires for the two pathways that matter for drivability and inhibition (Int->Pyr, Pyr->Int) and is marginally over for Int->Int; I read it as fired. This supports, but does not itself prove, the line 379 (tx/qx) explanation: any mechanism with count proportional to D^1.6 would give the same ratio. The unchanged arbors also show that the synapse test does not feed back into growth in this binary (INFERENCE from identical lengths; not checked in source).
Consequences measured: V1 (PV axon length) goes from 1.9% to 3.9% inhibitory (B) and 1.2% to 2.5% (A), drivable 8-cell 4 -> 9 (simple 11 -> 17, simple count passes 16, the 8-cell does not); V3 reaches A 3.04% and drivable 10 (8-cell) / 22 (simple) at this seed; S1 reaches A 4.2%. These are single-seed results: from the earlier seed repeat, drivable 8-cell has a between-seed SD of 1.5-3.5 for S1/V1/V3, so the drivable numbers here (single seed 16180, which was a low seed for the baselines: 2 / 4 / 2) should not be read as a seed-independent effect. The counts (the x2 ratios) are not seed-sensitive in this comparison because the arbors are identical between baseline and new run.
Inference (not tested): the D 0.15 maximum alone does not reach the PV targets (11 synapses per pair; here 1.7-2.1, 23-32 targets of 96); this matches FABLE_ANALYSIS section 1.5.
Limits: one seed; baselines are the earlier runs (not re-run, but arbor identity confirms the same realisation); the +x method matches the earlier analysis only as far as the S1 baseline figure (57.0%) shows; the 8-cell criterion is a summed-conductance proxy not validated dynamically.
Housekeeping: no NES/API restart, no git, no email, nothing outside this folder edited, bio_ranges.json untouched, no background jobs left.

---
# Addendum: repeat on seeds 31415 and 27182 (pooled with 16180 = 9 runs), 2026-11-15
Preregistration: PREREGISTRATION_seeds2.md (written before launch, not edited). Same grow_pv.py (unchanged), 6 more runs, 3 concurrent, all rc 0 (walls: s31415 S1 3311 s, V1 2300, V3 2696; s27182 S1 3468, V1 2300, V3 2424), "Deleted resident simulation" in every run.log, .nibr.clp read back as D_synmax 1.5 / 0.15 / 0.15 / 0.15 and bio_check pass for all 9 d015 runs (pv_results.json), NES not touched. Baselines: D 0.1 runs of the same seed in ../pv_arbor_seeds.

## A1. All 9 runs, baseline (0.1) then new (0.15)
| seed | variant | D | dend len | axon len | reach | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | syn/pair | targets/int | A / B (%) | drivable 8-cell (simple) | zero-in |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16180 | S1 | 0.1 | 6629 | 74624 | 143 | 73105 | 348 | 1616 | 685 | 1.60 | 21.0 | 2.16 / 3.04 | 2 (8) | 14 |
| 16180 | S1 | 0.15 | 6629 | 74624 | 143 | 73200 | 743 | 3237 | 1437 | 2.10 | 32.1 | 4.23 / 5.95 | 6 (15) | 9 |
| 16180 | V1 | 0.1 | 6733 | 45207 | 146 | 70921 | 461 | 876 | 509 | 1.38 | 13.3 | 1.22 / 1.90 | 4 (11) | 17 |
| 16180 | V1 | 0.15 | 6733 | 45207 | 145 | 70911 | 971 | 1845 | 1105 | 1.69 | 22.8 | 2.54 / 3.94 | 9 (17) | 13 |
| 16180 | V3 | 0.1 | 9405 | 55380 | 141 | 86230 | 573 | 1364 | 717 | 1.56 | 18.3 | 1.56 / 2.34 | 2 (14) | 12 |
| 16180 | V3 | 0.15 | 9405 | 55380 | 141 | 85887 | 1142 | 2691 | 1584 | 2.03 | 27.6 | 3.04 / 4.68 | 10 (22) | 7 |
| 31415 | S1 | 0.1 | 7114 | 76482 | 135 | 72104 | 533 | 1384 | 957 | 1.67 | 17.3 | 1.88 / 3.12 | 5 (12) | 24 |
| 31415 | S1 | 0.15 | 7114 | 76482 | 136 | 71893 | 1097 | 2917 | 1976 | 2.30 | 26.4 | 3.90 / 6.28 | 8 (14) | 20 |
| 31415 | V1 | 0.1 | 7045 | 45151 | 136 | 78446 | 371 | 969 | 474 | 1.41 | 14.3 | 1.22 / 1.80 | 3 (7) | 12 |
| 31415 | V1 | 0.15 | 7045 | 45151 | 136 | 78454 | 797 | 2091 | 936 | 1.82 | 23.9 | 2.60 / 3.68 | 7 (14) | 10 |
| 31415 | V3 | 0.1 | 9281 | 64079 | 138 | 79826 | 467 | 1435 | 764 | 1.64 | 18.2 | 1.77 / 2.67 | 5 (8) | 11 |
| 31415 | V3 | 0.15 | 9281 | 64079 | 138 | 79665 | 973 | 2981 | 1475 | 2.25 | 27.6 | 3.61 / 5.24 | 7 (17) | 9 |
| 27182 | S1 | 0.1 | 6864 | 81506 | 138 | 70237 | 533 | 1534 | 1074 | 1.54 | 20.7 | 2.14 / 3.55 | 5 (10) | 11 |
| 27182 | S1 | 0.15 | 6864 | 81506 | 139 | 70881 | 1103 | 3175 | 2169 | 2.09 | 31.6 | 4.29 / 6.91 | 11 (17) | 9 |
| 27182 | V1 | 0.1 | 7109 | 46851 | 135 | 79085 | 626 | 1026 | 645 | 1.46 | 14.6 | 1.28 / 2.05 | 6 (12) | 16 |
| 27182 | V1 | 0.15 | 7119 | 46619 | 135 | 84950 | 1135 | 2109 | 1291 | 1.81 | 24.3 | 2.42 / 3.80 | 9 (20) | 12 |
| 27182 | V3 | 0.1 | 10100 | 59286 | 136 | 77402 | 1098 | 1275 | 1475 | 1.47 | 18.1 | 1.62 / 3.38 | 8 (16) | 9 |
| 27182 | V3 | 0.15 | 10100 | 59286 | 137 | 77708 | 2136 | 2511 | 2925 | 1.88 | 27.8 | 3.13 / 6.37 | 15 (23) | 6 |

## A2. Ratio new / baseline per run
| seed | variant | dend | axon | reach | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | syn/pair | targets/int |
|---|---|---|---|---|---|---|---|---|---|---|
| 16180 | S1 | 1.000 | 1.000 | 0.996 | 1.001 | 2.14 | 2.00 | 2.10 | 1.31 | 1.53 |
| 16180 | V1 | 1.000 | 1.000 | 0.997 | 1.000 | 2.11 | 2.11 | 2.17 | 1.22 | 1.71 |
| 16180 | V3 | 1.000 | 1.000 | 0.998 | 0.996 | 1.99 | 1.97 | 2.21 | 1.30 | 1.51 |
| 31415 | S1 | 1.000 | 1.000 | 1.003 | 0.997 | 2.06 | 2.11 | 2.06 | 1.38 | 1.53 |
| 31415 | V1 | 1.000 | 1.000 | 1.002 | 1.000 | 2.15 | 2.16 | 1.97 | 1.29 | 1.67 |
| 31415 | V3 | 1.000 | 1.000 | 0.999 | 0.998 | 2.08 | 2.08 | 1.93 | 1.37 | 1.52 |
| 27182 | S1 | 1.000 | 1.000 | 1.013 | 1.009 | 2.07 | 2.07 | 2.02 | 1.36 | 1.53 |
| 27182 | V1 | 1.001 | 0.995 | 0.998 | 1.074 | 1.81 | 2.06 | 2.00 | 1.24 | 1.66 |
| 27182 | V3 | 1.000 | 1.000 | 1.001 | 1.004 | 1.95 | 1.97 | 1.98 | 1.28 | 1.54 |

Pooled ratios (sum new / sum baseline over the three variants of a seed):
| seed | Pyr->Int | Int->Pyr | Int->Int |
|---|---|---|---|
| 16180 | 2.07 | 2.02 | 2.16 |
| 31415 | 2.09 | 2.11 | 2.00 |
| 27182 | 1.94 | 2.03 | 2.00 |
| all 9 | 2.02 | 2.05 | 2.04 |

Per-run ratios over all 9: Int->Pyr 1.97-2.16 (mean 2.06, SD 0.07), Pyr->Int 1.81-2.15 (2.04, SD 0.11), Int->Int 1.93-2.21 (2.05, SD 0.09); syn/pair Int->Pyr x1.23-1.38 (mean 1.31), targets per interneuron x1.51-1.71 (mean 1.58).
Arbors: interneuron dendrite and axon length ratio is 1.000 in 8 of 9 runs. EXCEPTION: V1 seed 27182 is not the same realisation: axon length x0.995, dendrite x1.001, pyramidal dendrite x0.998, pyramidal axon x1.003 and Pyr->Pyr x1.074 (the pyramidal pair was not changed). Its Pyr->Int ratio is the lowest (1.81). Reach ratio is 0.996-1.013 in all 9 (varying by up to 1.3% even where lengths are identical; cause not investigated). Pyr->Pyr ratio 0.996-1.009 in the other 8 runs. Inference (not checked in source): NetMorph growth is not perfectly reproducible between runs with the same seed in that run (e.g. thread timing), so a baseline-vs-new comparison can carry a small realisation difference; it is 1 of 9 here.

## A3. +x direction check (xdir.py, same method as the 16180 section; synapse-carrying Int->Pyr axon segments with cos(+x) > 0.9)
| run | baseline | D 0.15 | change | all-segment share (baseline / new) |
|---|---|---|---|---|
| s31415 S1 | 55.9% (n 1384) | 50.7% (n 2917) | -5.2 | 4.67 / 4.66% |
| s31415 V1 | 57.8% (969) | 52.9% (2091) | -4.9 | 4.90 / 4.89% |
| s31415 V3 | 60.0% (1435) | 54.6% (2981) | -5.4 | 4.86 / 4.87% |
| s27182 S1 | 59.8% (1534) | 54.7% (3175) | -5.1 | 4.75 / 4.76% |
| s27182 V1 | 57.8% (1026) | 54.2% (2109) | -3.6 | 4.71 / 4.68% |
| s27182 V3 | 60.3% (1275) | 54.9% (2511) | -5.4 | 5.05 / 5.03% |
Together with seed 16180 (57.0 -> 53.6, 56.5 -> 54.0, 58.4 -> 52.1): in all 9 runs the share falls by 2.5-6 points to 50.7-54.9% and stays about 11x the all-segment share. Measured.

## A4. Scored addendum preregistration
- Item 1 (arbors: lengths 1.000, reach 0.99-1.01, Pyr->Pyr 1.00): PARTIAL. 5 of 6 new runs match (lengths exactly 1.000, Pyr->Pyr 0.997-1.009); reach 1.013 in s27182 S1 is just outside; V1 s27182 diverged (axon x0.995, Pyr->Pyr x1.074): MISS for that run.
- Item 2 (per-run ratios Int->Pyr 1.85-2.30, Pyr->Int 1.85-2.35, Int->Int 1.90-2.40): 17 of 18 HIT; Pyr->Int V1 s27182 = 1.81 just below 1.85: PARTIAL. Pooled over the 6 new runs: Int->Pyr 2.07, Pyr->Int 2.00, Int->Int 2.00 (predicted 2.0-2.2 each): HIT (two at the lower edge). Pooled over all 9: Int->Pyr 2.05 (pred 2.0-2.1) HIT, Pyr->Int 2.02 (2.0-2.15) HIT, Int->Int 2.04 (2.1-2.2) PARTIAL (below the range). Per-seed pooled ratios 1.94-2.16, all inside 1.9-2.3: HIT.
- Item 3 (counts and fractions): counts 17 of 18 inside the ratio bands (the exception is the Pyr->Int count of V1 s27182: 1135 vs predicted band 1155-1459); inhibitory fractions A and B 12 of 12 within +-0.4 points of prediction (A 2.42-4.29%, B 3.68-6.91%). HIT.
- Item 4 (drivable 8-cell): s31415 S1 8 (6-11), V1 7 (4-10), V3 7 (6-12), s27182 S1 11 (5-11), V1 9 (7-13), V3 15 (9-15): 6 of 6 inside, V3 s27182 at the upper edge; but the stated maximum of about 12-13 was exceeded by 15. Any run at 16: none (predicted 10% chance): HIT. Simple counts 14, 14, 17, 17, 20, 23: 5 of 6 within 1.7x baseline +-30% (S1 s31415, 14 vs baseline 12, x1.17, just below). Overall HIT with the maximum partial.
- Item 5 (+x share 51-55% for S1/V1, 49-54% for V3, 2-6 points below baseline): all 6 drops are 3.6-5.4 points (HIT); levels: 4 of 6 inside, S1 s31415 50.7% (just below) PARTIAL, V3 54.6 / 54.9 (just above 54) PARTIAL x2. All-segment share 4.7-5.0%, unchanged vs baseline.
- Main claim "x2 holds on all seeds with unchanged arbors": the ratio part HIT (every per-seed pooled ratio 1.94-2.16); strict reading of the rule (no arbor property changes) PARTIAL because V1 s27182 diverged.

## A5. Verdict
Measured: over 9 runs (3 seeds x S1/V1/V3), raising D_synmax on the three interneuron pairs from 0.1 to 0.15 multiplies Int->Pyr by 2.05, Pyr->Int by 2.02 and Int->Int by 2.04 (pooled), per run 1.81-2.21, per seed pooled 1.94-2.16. Fable's x1.8-2.1 (point x1.94) holds on all three seeds for all three pathways within seed noise (pooled Int->Int 2.04 and per-seed Int->Int 2.00-2.16; the single x2.16 on seed 16180 was not repeated). Arbors do not change in 8 of 9 runs, and the +x share of synapse-carrying segments falls about 5 points but stays at 51-55%. Stop rule (x1.8-2.1 with unchanged arbors) fires on this evidence.
Drivable 8-cell at D 0.15 (9 runs): S1 6, 8, 11; V1 9, 7, 9; V3 10, 7, 15 (mean 8.3 / 8.3 / 10.7, SD 2.5 / 1.2 / 4.0); versus 16 required by the bar: no run reaches it (max 15, V3 s27182); 3 of 9 runs reach 10 or more, 1 reaches 15. On the simple count, 6 of 9 runs reach 16 or more (15, 17, 22 / 14, 14, 17 / 17, 20, 23: S1 never above 17, V3 up to 23). The 3-6% inhibitory-fraction condition (A): met by S1 in 3 of 3 seeds (3.9-4.3%) and V3 in 3 of 3 (3.0-3.6%), not by V1 (2.4-2.6%); the Pyr->Pyr 5% condition compares like with like (ratio 1.00) in 8 of 9 runs. So the combined bar is still not met: it fails on drivable 8-cell (max 15 vs 16) for every run.
Inference (not tested): D 0.15 is the largest allowed lever, lifts the drivable count about 2x, and brings the bar within a few cells of reach in the best seed-realisation, but it does not by itself deliver 16 drivable at the 8-cell criterion; seed variation of drivable (SD 1-4) means the V3 value of 15 versus V1 and S1 is not a demonstrated variant difference. The count ratio of x2 is not seed sensitive (SD 0.07-0.11 per run); the drivable and +x levels are.
Limits: 3 seeds; baselines are earlier runs; one run (V1 s27182) is a slightly different realisation; 8-cell is a summed-conductance proxy not validated dynamically.
Housekeeping: no NES/API restart, max 3 concurrent sims, no git, no email, only this folder (plus the requested LEARNINGS.md entry) written; no background jobs left.
