# PV-arbor repeat on new seeds: is the one-seed result real or seed noise? (own NES 8000/7999/8001), 2026-11-14/15
Scripts: grow_pv.py (driver, copy of pv_arbor/grow_pv.py; usage `grow_pv.py S1|V1|V3 SEED`), run_all.sh (one batch per seed, S1+V1+V3 3 concurrent), measure.py (unchanged copy), analyze_pv.py (copy adapted to seed-tagged runs) -> pv_results.json (9 new runs). PREREGISTRATION.md was written before any run and not edited. Original seed numbers come from ../pv_arbor/pv_results.json (not modified).
Setup identical to pv_arbor/README.md: 96 pyramidal, 48 interneurons, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9, D_synmax 1.5 pyr-pyr / 0.1 for the three interneuron pairs, bio_check.assert_hard_limits passed in every run (bio_check "pass" in pv_results.json), interneuron basal 6-10. S1: axon B_inf 26, dend B_inf 3.5; V1: 20 / 3.5; V3: 23 / 5. New seeds: 31415, 27182, 16180 (chosen arbitrarily, all different from 20240628). Definitions of lengths, drivable (8-cell and simple) and inhibitory fractions A and B: as in pv_arbor/README.md (A = Int->Pyr/(Int->Pyr+Pyr->Pyr); B = (Int->Pyr+Int->Int)/all synapses).
Walls (s): S1 3825/3915/3309, V1 1912/1842/1994, V3 3255/2343/2318 (seeds 31415/27182/16180). All 9 runs rc 0, each deleted its resident simulation (run.log "Deleted resident simulation" present 9 of 9).

## 1. Per-run table (original seed 20240628 from pv_arbor, then the three new seeds)
| seed | variant | dend len (um) | axon len (um) | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | syn/pair I->P | pyr targets/int | inhib A / B (%) | drivable 8-cell (simple) | zero-input ints |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20240628 (orig) | S1 | 7134 | 77554 | 57702 | 760 | 1314 | 1709 | 1.60 | 17.1 | 2.23 / 4.92 | 7 (13) | 7 |
| 20240628 (orig) | V1 | 7146 | 44870 | 58959 | 667 | 832 | 837 | 1.58 | 11.0 | 1.39 / 2.72 | 6 (14) | 12 |
| 20240628 (orig) | V3 | 9640 | 60580 | 60000 | 952 | 940 | 1523 | 1.38 | 14.2 | 1.54 / 3.88 | 10 (14) | 11 |
| 16180 | S1 | 6629 | 74624 | 73105 | 348 | 1616 | 685 | 1.60 | 21.0 | 2.16 / 3.04 | 2 (8) | 14 |
| 16180 | V1 | 6733 | 45207 | 70921 | 461 | 876 | 509 | 1.38 | 13.3 | 1.22 / 1.90 | 4 (11) | 17 |
| 16180 | V3 | 9405 | 55380 | 86230 | 573 | 1364 | 717 | 1.56 | 18.3 | 1.56 / 2.34 | 2 (14) | 12 |
| 27182 | S1 | 6864 | 81506 | 70237 | 533 | 1534 | 1074 | 1.54 | 20.7 | 2.14 / 3.55 | 5 (10) | 11 |
| 27182 | V1 | 7109 | 46851 | 79085 | 626 | 1026 | 645 | 1.46 | 14.6 | 1.28 / 2.05 | 6 (12) | 16 |
| 27182 | V3 | 10100 | 59286 | 77402 | 1098 | 1275 | 1475 | 1.47 | 18.1 | 1.62 / 3.38 | 8 (16) | 9 |
| 31415 | S1 | 7114 | 76482 | 72104 | 533 | 1384 | 957 | 1.67 | 17.3 | 1.88 / 3.12 | 5 (12) | 24 |
| 31415 | V1 | 7045 | 45151 | 78446 | 371 | 969 | 474 | 1.41 | 14.3 | 1.22 / 1.80 | 3 (7) | 12 |
| 31415 | V3 | 9281 | 64079 | 79826 | 467 | 1435 | 764 | 1.64 | 18.2 | 1.77 / 2.67 | 5 (8) | 11 |

## 2. Per-variant statistics across the 4 seeds (3 new + original); SD is the sample SD (n=4); last column is the mean of the 3 new seeds only
| variant | metric | mean (4 seeds) | SD | min-max | mean of 3 new seeds |
|---|---|---|---|---|---|
| S1 | drivable 8-cell | 5 | 2 | 2-7 | 4 |
| S1 | drivable simple | 11 | 2 | 8-13 | 10 |
| S1 | Pyr->Pyr | 68287 | 7156 | 57702-73105 | 71815 |
| S1 | Pyr->Int | 544 | 169 | 348-760 | 471 |
| S1 | Int->Pyr | 1462 | 138 | 1314-1616 | 1511 |
| S1 | Int->Int | 1106 | 434 | 685-1709 | 905 |
| S1 | syn/pair I->P | 1.60 | 0.05 | 1.54-1.67 | 1.60 |
| S1 | targets/int | 19.0 | 2.1 | 17.1-21.0 | 19.7 |
| S1 | inhib A % | 2.10 | 0.15 | 1.88-2.23 | 2.06 |
| S1 | inhib B % | 3.66 | 0.87 | 3.04-4.92 | 3.24 |
| S1 | zero-input ints | 14 | 7 | 7-24 | 16 |
| S1 | axon len | 77542 | 2907 | 74624-81507 | 77538 |
| S1 | dend len | 6936 | 238 | 6629-7134 | 6869 |
| V1 | drivable 8-cell | 5 | 2 | 3-6 | 4 |
| V1 | drivable simple | 11 | 3 | 7-14 | 10 |
| V1 | Pyr->Pyr | 71853 | 9361 | 58959-79085 | 76151 |
| V1 | Pyr->Int | 531 | 139 | 371-667 | 486 |
| V1 | Int->Pyr | 926 | 88 | 832-1026 | 957 |
| V1 | Int->Int | 616 | 165 | 474-837 | 543 |
| V1 | syn/pair I->P | 1.46 | 0.09 | 1.38-1.58 | 1.42 |
| V1 | targets/int | 13.3 | 1.6 | 11.0-14.6 | 14.1 |
| V1 | inhib A % | 1.28 | 0.08 | 1.22-1.39 | 1.24 |
| V1 | inhib B % | 2.12 | 0.41 | 1.80-2.72 | 1.92 |
| V1 | zero-input ints | 14 | 3 | 12-17 | 15 |
| V1 | axon len | 45520 | 900 | 44870-46852 | 45737 |
| V1 | dend len | 7009 | 188 | 6734-7147 | 6963 |
| V3 | drivable 8-cell | 6 | 4 | 2-10 | 5 |
| V3 | drivable simple | 13 | 3 | 8-16 | 13 |
| V3 | Pyr->Pyr | 75864 | 11213 | 60000-86230 | 81153 |
| V3 | Pyr->Int | 772 | 301 | 467-1098 | 713 |
| V3 | Int->Pyr | 1254 | 219 | 940-1435 | 1358 |
| V3 | Int->Int | 1120 | 439 | 717-1523 | 985 |
| V3 | syn/pair I->P | 1.51 | 0.11 | 1.38-1.64 | 1.56 |
| V3 | targets/int | 17.2 | 2.0 | 14.2-18.3 | 18.2 |
| V3 | inhib A % | 1.62 | 0.10 | 1.54-1.77 | 1.65 |
| V3 | inhib B % | 3.07 | 0.69 | 2.34-3.88 | 2.80 |
| V3 | zero-input ints | 11 | 1 | 9-12 | 11 |
| V3 | axon len | 59832 | 3592 | 55380-64079 | 59582 |
| V3 | dend len | 9607 | 361 | 9281-10101 | 9596 |

Paired V3 - V1 per seed, drivable 8-cell: original +4, 31415 +2, 27182 +2, 16180 -2 (mean +1.5, SD 2.65, SE about 1.3). Simple: +0, +1, +4, +3 (mean +2.0). Pyr->Pyr V3 - V1: +1.0k, +1.4k, -1.7k, +15.3k.
Pyr->Pyr relative to the S1 of the same seed (the 5% rule of the bar): V1 +2.2% (orig), +8.8%, +12.6%, -3.0%; V3 +4.0% (orig), +10.7%, +10.2%, +18.0%.

## 3. Pre-set bar (>=16 drivable AND 3-6% inhibitory AND Pyr->Pyr within 5%), new seeds
No run meets it. Drivable 8-cell maximum over the 9 new runs is 8 (V3, seed 27182); none reaches 16. With the looser "simple" count one run reaches 16 (V3 seed 27182, which has only 9 zero-input interneurons) but that run has inhibitory fraction A 1.62% and Pyr->Pyr +10.2% vs its S1. Inhibitory fraction A is 1.2-2.2% in all 12 runs (never 3%); fraction B is in 3-6% in 6 of 12 runs (S1 4 of 4 seeds, V3 2 of 4, V1 0 of 4).

## 4. Scored preregistration (PREREGISTRATION.md)
- (a) mean/spread of drivable 8-cell per variant. Predicted means S1 7 (range 4-10), V1 6 (3-9), V3 7.5 (4-11), SD about 2-2.5. Observed 3 new seeds: S1 4.0 (2-5, SD 1.7), V1 4.3 (3-6, SD 1.5), V3 5.0 (2-8, SD 3.0). Spreads were about right (hit) but all three means were too high by 1.7-3 and S1 fell outside its predicted range. The statement "no variant mean above 9" held. Score: PARTIAL (spread hit, level miss; S1 itself a miss).
- (b) V3 > V1 on repeats: predicted V3 mean > V1 mean with probability about 60%, not in all 3 seeds, gap shrinking toward about +1.5 and indistinguishable from noise. Observed V3 5.0 vs V1 4.3 (+0.7) on new seeds, V3 higher in 2 of 3 seeds (not all), +1.5 over 4 seeds, within noise. Score: HIT.
- (c) seed spread of Pyr->Pyr: predicted mean about 58,000, SD about 10% (6,000), max/min about 1.25. Observed SD 10.5% (S1), 13.0% (V1), 14.8% (V3), max/min 1.27 / 1.34 / 1.44, but means 68k / 72k / 76k: the original seed 20240628 gave the lowest Pyr->Pyr in all three variants (57.7-60.0k) and the three new seeds are all 70-86k. Score: PARTIAL (spread about right, upper end of the range larger for V3; the level of 58k was an artefact of the one original seed, a miss).
- (d) any run at 16 drivable: predicted no (3% chance). Observed none at 16 on the primary 8-cell criterion (max 8). One run reaches 16 on the looser simple count. Score: HIT on the stated primary criterion (note the simple-count exception).

## 5. Verdict
Measured:
- The original seed was the best of the four seeds for all three variants' drivable counts (S1 7 vs new 2-5; V3 10 vs 2-8; V1 6 vs 3-6). 'Best drivable 10/48' did not reproduce: across 12 runs the next-best is 8, and the 4-seed mean of V3 is 6 (SD about 4, range 2-10). 'Best drivable 10/48' was the top of a noisy distribution, not a stable value.
- V3 > V1 held on average (+1.5, 4 seeds) and in 3 of 4 seeds, but the paired SE is about 1.3 (t about 1.1) so it is not distinguishable from zero; at the 3 new seeds alone it is +0.7 with one reversal. Simple count favours V3 by +2.0 (4 seeds).
- Variant means of drivable (8-cell) are S1 4.8, V1 4.8, V3 6.3 with SDs 1.5-3.5: the three variants are not separated.
- Deterministic-looking lever effects did reproduce: lengths (axon V1 about 45.5k vs V3 about 59.8k vs S1 about 77.5k; dend 7.0k vs 9.6k), V1 has the lowest Int->Pyr (mean 926, range 832-1026, no overlap with S1 1314-1616; V3 940-1435 overlaps only at the V1 top) and fewest targets per interneuron (13.3 vs 17-19), syn/pair stays 1.4-1.7, inhibitory fraction A stays 1.2-2.2%. These effects are larger than the seed spread.
- Pyr->Pyr varies seed to seed by 10-15% SD and the original seed was low, so the 5% rule compares seeds as much as variants.
Inference (not tested): the drivable count of 8-cell is dominated by realisation noise at n=48 interneurons (SD 1.5-3.5 on a mean of 5-6), so differences of 1-2 between variants need many more seeds than 4; the best bet for improving drivable counts is something other than B_inf (e.g. connectivity parameters held fixed here), unchanged from the earlier conclusion. The original single-seed result overstated V3; I do not claim V3 is worse or better than V1.
Limits: n=3 new seeds per variant (4 with the original); seeds chosen once and not screened; drivable 8-cell criterion is a summed-conductance proxy not validated dynamically; every run used one NetMorph realisation per seed; S1 runs were slowest (about 55-65 min) when three ran concurrently.
Housekeeping: no NES/API restart, at most 3 concurrent sims, no git, no email, nothing outside this folder modified; no background jobs left (verified with ps). A first launch attempt produced no runs because my edit of the copied grow_pv.py had truncated its tail; the script exited rc 0 without contacting NES (no sims created), fixed and relaunched.
