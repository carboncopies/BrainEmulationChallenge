# Head-to-head log (Track 1)

## Pre-registration (written 2026-11-10 23:31:47 PST, before any NES run)

### Protocol summary
- Problem: choose Netmorph growth configs (7 parameters, `D_synmax` at defaults, base model `nesvbp-autoassociative` untouched) that maximise the joint score J on the grown network. Two arms: ML arm (random forest per component + DiCE) and mechanistic arm (negative-binomial scaling law, analyst-fixed round-1 configs).
- Budget: 10 training runs per arm in two rounds of 5, 12 held-out configs x 2 seeds (24 runs), 3 nominations per arm x 3 seeds (18 runs): 20 + 24 + 18 = 62 runs. Training runs both arms: Netmorph seed 20240628, interleaved ML, mech, ML, mech... Held-out seeds 2001, 2002. Nomination seeds 3001, 3002, 3003 (shared by arms).
- Hard limits (asserted with `bio_check.assert_hard_limits`): days 20-25 (int), pyramidal 16-128, interneuron 16-128, minneuronseparation 10-15, shape.radius 100-200, shape.thickness 20-50, dm.weight 0.1-1.0. Size cap: pyramidal 16-70, interneuron 16-30. Asserted at generation and again immediately before each launch.
- soft-clean: 10000 <= (pyr+int)/(pi r^2 t 1e-9) <= 50000 and 0.70 <= pyr/(pyr+int) <= 0.80.
- Components per grown network: raw_pyr_int_n, raw_int_pyr_n, raw_int_int_n (rawcounts `classes` census: pyr->int:1, int->pyr:2, int->int:2 connections), usable_conns2. J = min(raw_pyr_int_n/42.0, raw_int_pyr_n/97.25, raw_int_int_n/18.25, usable_conns2/460). Also recorded: raw_pyr_pyr_n, usable_pyr_int/int_pyr/int_int, frac_int_driven, wall_s, NES_SIM_ID, frac of interneurons with incoming pyramidal AMPA >= 13.84 nS, mean incoming GABA g per pyramidal cell.
- Targets: T1 = soft-clean and J >= 1.041 (best soft-clean batch B row). T2 (stretch) = soft-clean and J >= 1.534 (best batch B row overall).
- Metrics (score.py): held-out per arm, per component and J, per run (24) and on config means (12): Spearman, R2, Poisson D2 vs the batch-B mean, MAE, 80% interval coverage. Training: index of first run (in arm order) reaching T1 and T2; best J and best soft-clean J after 5 and 10 runs. Nominations: hit rate at T1 and T2 over 9 (config, seed) runs, mean J, per-config seed CV of each component.
- Pacing and abort: one growth at a time (`run_queue.py`), timeout 1500 s (SIGTERM own client only), 30 s sleep between runs, `headtohead/STOP` checked before each run. Queue is ABORTED (`<queue>.status`) on non-zero rc, timeout, server/connection error pattern, or wall_s > 2 x predicted (predicted = exp(-4.4642 + 1.7582 ln(pyr+int) + 0.1119 days)); DONE on completion. Runs with rc=0 already in runs.csv are skipped. No `-deleteresident`; only own sims are created; nothing is deleted.
- Netmorph seed: passed as `-randomseed <seed>` to `gen_autonm_labels.py` (appends `randomseed=<seed>;` to the base model content, same mechanism as fable_loop r2_seeds). Batch B used the default 20240628, so training runs are identical in setup to batch B. `D_synmax` stays at defaults: the base model file `nesvbp-autoassociative` (the one batch B used) contains no `D_synmax` line (grep: none), and no model with such lines is referenced.
- Sanity: `run_queue.py --dry-run` selftest recomputes batch B sample 1 from its rawcounts json and matches `load_batchB()` (31 / 74 / 5 / 240).

### Predicted wall time (fitted model)
Queue 1 total: 5467 s = 1.52 h. Held-out (12 configs x 2 seeds): 6056 s = 1.68 h (from heldout_configs.csv).

| run_id | arm | config_id | pred_wall_s |
|---|---|---|---|
| T-ML-R1-1 | ML | ML-R1-1 | 505.0 |
| T-MECH-R1-M1 | MECH | M1 | 620.0 |
| T-ML-R1-2 | ML | ML-R1-2 | 470.0 |
| T-MECH-R1-M2 | MECH | M2 | 620.0 |
| T-ML-R1-3 | ML | ML-R1-3 | 507.0 |
| T-MECH-R1-M3 | MECH | M3 | 620.0 |
| T-ML-R1-4 | ML | ML-R1-4 | 505.0 |
| T-MECH-R1-M4 | MECH | M4 | 620.0 |
| T-ML-R1-5 | ML | ML-R1-5 | 505.0 |
| T-MECH-R1-M5 | MECH | M5 | 495.0 |

### Files and sha256
- `env.sh`  fe843b14cff3c000982edab399d3fe8ee24fa60ced3da7800981a38a65ac3781
- `h2h_common.py`  3968160bcbb3bcf463004f35526665f93ce0617c775f7c595d1100e0d4e97ac1
- `make_heldout.py`  e92ac8bc2b373750049d9a4773f28cfef3b5ce387cc3872a43ae7db744c03dac
- `ml_arm.py`  0c2defc3643206eb60b0e6adfa403b20ef721ffab8284da00a17d3e8664c6539
- `mech_arm.py`  a5acbbda1ed61d2453c5e9fb46b4d217909ca948fe44d640e57250552b1ab72b
- `make_queue1.py`  eac1bf4dd11be45c0ac7f2510996ec27c7bc40eed0003b09b7fe842a3cad1f14
- `run_queue.py`  fb866cc9bb38a27de99ad9639fc05b76e1868022f191eabb570d6d3ded721d7d
- `score.py`  02ad47099ec0871489c3b08792e28880ccbe35affd50a43a496cbc46b6ef0e23
- `heldout_configs.csv`  10153068075f02de613029c0dd482e599444dcfe9ecfc2e9d577153644757ab1
- `ml_round1.csv`  9465e6253060d9de664a3ceca0a0439e28b7dfb44e87435055b5ea9854d0cbe4
- `mech_round1.csv`  9d05fafecce15ea8bb87a1295c3300ce1f2895e71def815a27ee40e608e1caeb
- `queue1.csv`  1e65c5d45768de79a5c68a15170c1ecfab5f7f84b65813b7df0fa7c124dd91cd
- `preds_heldout_ml.csv`  566655d188c609e2207be96890b17e78917172bb003855972e52b930e083490e
- `preds_heldout_mech.csv`  8d97f76ca0ae4b1aafe288f04c1c10aff7ec539e4362b45dbd048a5d92d37887
- `preds_queue1_ml.csv`  49992308b5a6ca3105a96b0897e736cffc26d3b2a471d4cb6513c338c13f1c5c
- `preds_queue1_mech.csv`  39949d5a447048c9d6ca826e387a672b85d322161254e71d95726416485612eb

### Held-out configs (scrambled Sobol seed 777, first 12 points; 1-8 general, 9-12 corner; no soft-clean filter)
| config_id | days | pyramidal | interneuron | minneuronseparation | shape.radius | shape.thickness | dm.weight | kind | soft_clean | density | pyr_frac | pred_wall_s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H01 | 25 | 51 | 23 | 15 | 184 | 28 | 0.2 | general | False | 24848.0 | 0.689 | 365.0 |
| H02 | 21 | 28 | 20 | 11 | 142 | 47 | 0.7 | general | False | 16122.0 | 0.583 | 109.0 |
| H03 | 20 | 63 | 27 | 13 | 116 | 42 | 0.4 | general | False | 50691.0 | 0.7 | 295.0 |
| H04 | 24 | 33 | 16 | 10 | 161 | 23 | 0.8 | general | False | 26162.0 | 0.673 | 158.0 |
| H05 | 23 | 66 | 22 | 11 | 173 | 33 | 0.5 | general | True | 28361.0 | 0.75 | 396.0 |
| H06 | 21 | 42 | 26 | 13 | 100 | 44 | 0.9 | general | False | 49193.0 | 0.618 | 201.0 |
| H07 | 22 | 48 | 19 | 12 | 129 | 37 | 0.2 | general | True | 34637.0 | 0.716 | 219.0 |
| H08 | 24 | 17 | 29 | 14 | 194 | 26 | 0.7 | general | False | 14963.0 | 0.37 | 142.0 |
| H09 | 25 | 59 | 18 | 13 | 147 | 21 | 0.9 | corner | False | 54012.0 | 0.766 | 392.0 |
| H10 | 24 | 35 | 29 | 11 | 180 | 39 | 1.0 | corner | False | 16122.0 | 0.547 | 253.0 |
| H11 | 24 | 53 | 21 | 14 | 153 | 50 | 0.8 | corner | True | 20125.0 | 0.716 | 327.0 |
| H12 | 25 | 23 | 25 | 12 | 124 | 31 | 1.0 | corner | False | 32054.0 | 0.479 | 171.0 |

### ML arm
Method actually used: **DiCE** (dice_ml 0.x installed to `headtohead/pylib_dice`, `method='random'`), following `multi_target_optim.generate_joint_cfs`: one scalar handed to DiCE = min over components of (RF mean / (1.041 x reference)), set to -1 when the (rounded) config is not soft-clean or outside the hard-limit/size-cap box; desired_range [1, inf); permitted range = hard limits intersect size cap. It was NOT the unmodified function: the stored `TargetModel` uses a train/test split, 2000 trees and 2.5th-percentile scoring, and its pool supplement ignores the size cap, so DiCE was driven directly with the pre-registered RF (500 trees, random_state 0, trained on all 100 batch B rows). 25 calls x 5000 samples gave 94 unique soft-clean candidates with predicted score >= 1.041; the 5 below are the top-5 by score, greedy-diverse (min distance 0.15 in hard-limit-span units), excluding configs already run. Pool fallback was not needed (it is still the code path for `--method pool`; `nominate` always uses the pool).
Training data for round 1: batch B only (100 rows).
| config_id | days | pyramidal | interneuron | minneuronseparation | shape.radius | shape.thickness | dm.weight | soft_clean | pred_wall_s |
|---|---|---|---|---|---|---|---|---|---|
| ML-R1-1 | 25 | 64 | 25 | 11 | 136 | 44 | 0.9 | True | 505.0 |
| ML-R1-2 | 23 | 69 | 28 | 12 | 141 | 32 | 0.9 | True | 470.0 |
| ML-R1-3 | 24 | 67 | 28 | 13 | 140 | 41 | 0.9 | True | 507.0 |
| ML-R1-4 | 25 | 64 | 25 | 14 | 136 | 44 | 0.8 | True | 505.0 |
| ML-R1-5 | 25 | 64 | 25 | 11 | 136 | 48 | 0.8 | True | 505.0 |

### Mechanistic arm (fixed by the analyst: days 25, minsep 12, seed 20240628)
All five pass hard limits, size cap and soft-clean.
| config_id | days | pyramidal | interneuron | minneuronseparation | shape.radius | shape.thickness | dm.weight | soft_clean | density | pyr_frac |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 25 | 70 | 30 | 12 | 113 | 50 | 1.0 | True | 49857.0 | 0.7 |
| M2 | 25 | 70 | 30 | 12 | 179 | 20 | 1.0 | True | 49672.0 | 0.7 |
| M3 | 25 | 70 | 30 | 12 | 142 | 32 | 1.0 | True | 49331.0 | 0.7 |
| M4 | 25 | 70 | 30 | 12 | 113 | 50 | 0.8 | True | 49857.0 | 0.7 |
| M5 | 25 | 70 | 18 | 12 | 106 | 50 | 1.0 | True | 49860.0 | 0.795 |

### Held-out predictions (mean [10th-90th pct]); both arms predict all 12 configs
ML arm (RF; interval = per-tree 10th-90th percentile):
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| H01 | 21.0 [10-32] | 66.8 [33-96] | 9.2 [3-16] | 147.9 [31-281] | 0.32 |
| H02 | 29.1 [13-61] | 76.7 [41-125] | 12.1 [5-22] | 234.0 [96-403] | 0.51 |
| H03 | 34.9 [18-49] | 80.3 [57-102] | 12.2 [5-20] | 313.6 [198-525] | 0.67 |
| H04 | 32.6 [13-63] | 82.2 [54-107] | 12.2 [4-32] | 250.8 [138-413] | 0.55 |
| H05 | 24.5 [9-53] | 65.8 [48-90] | 9.9 [3-22] | 377.9 [226-499] | 0.54 |
| H06 | 37.9 [14-74] | 105.4 [75-149] | 17.9 [7-33] | 529.0 [322-872] | 0.90 |
| H07 | 21.5 [10-37] | 50.9 [37-75] | 7.2 [4-10] | 196.3 [63-334] | 0.40 |
| H08 | 28.7 [13-50] | 76.0 [57-104] | 20.3 [10-28] | 218.6 [96-413] | 0.48 |
| H09 | 56.8 [18-129] | 93.5 [69-111] | 15.8 [4-38] | 502.2 [364-641] | 0.87 |
| H10 | 26.8 [11-64] | 78.9 [68-105] | 19.1 [6-34] | 239.8 [138-415] | 0.52 |
| H11 | 37.2 [14-66] | 89.4 [61-125] | 13.2 [4-24] | 412.7 [311-538] | 0.72 |
| H12 | 31.7 [15-64] | 92.1 [69-113] | 18.5 [6-38] | 368.0 [96-709] | 0.76 |

Mechanistic arm (NB2 law, alpha_total = alpha + 0.03):
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| H01 | 15.8 [8-25] | 57.1 [39-77] | 8.3 [3-14] | 145.9 [82-219] | 0.32 |
| H02 | 9.8 [4-16] | 36.0 [24-49] | 7.5 [3-13] | 129.8 [72-195] | 0.23 |
| H03 | 29.8 [15-46] | 74.1 [51-99] | 10.7 [4-18] | 246.9 [139-369] | 0.54 |
| H04 | 17.3 [8-27] | 51.8 [35-70] | 9.2 [3-16] | 332.3 [188-496] | 0.41 |
| H05 | 30.1 [16-46] | 77.2 [53-103] | 9.7 [4-17] | 386.5 [219-576] | 0.53 |
| H06 | 33.4 [18-51] | 82.1 [57-110] | 18.4 [8-30] | 382.0 [216-569] | 0.79 |
| H07 | 12.2 [6-20] | 40.6 [27-55] | 4.9 [1-9] | 113.2 [63-170] | 0.25 |
| H08 | 9.9 [4-16] | 42.1 [28-57] | 21.3 [10-35] | 91.4 [51-138] | 0.20 |
| H09 | 46.9 [25-72] | 110.4 [77-146] | 14.6 [6-24] | 998.5 [568-1485] | 0.80 |
| H10 | 27.3 [14-42] | 76.7 [53-102] | 24.2 [11-40] | 319.5 [181-477] | 0.65 |
| H11 | 25.2 [13-39] | 78.9 [54-105] | 11.2 [4-19] | 454.0 [258-676] | 0.60 |
| H12 | 24.4 [12-38] | 70.1 [48-94] | 29.5 [14-48] | 302.9 [171-452] | 0.58 |

### Queue-1 predictions (each arm predicts all 10 configs)
ML arm:
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| T-ML-R1-1 | 69.6 [21-129] | 118.5 [90-143] | 24.1 [8-40] | 671.9 [467-798] | 1.22 |
| T-MECH-R1-M1 | 64.1 [18-129] | 142.4 [125-172] | 18.5 [6-34] | 785.7 [622-925] | 1.01 |
| T-ML-R1-2 | 53.5 [18-82] | 125.3 [88-143] | 22.1 [8-33] | 590.9 [459-709] | 1.21 |
| T-MECH-R1-M2 | 70.2 [18-129] | 108.2 [74-143] | 25.8 [6-40] | 527.2 [364-622] | 1.11 |
| T-ML-R1-3 | 50.2 [18-82] | 119.8 [88-143] | 23.3 [8-34] | 591.0 [442-757] | 1.20 |
| T-MECH-R1-M3 | 65.8 [18-129] | 128.2 [96-143] | 20.6 [6-34] | 599.2 [439-757] | 1.13 |
| T-ML-R1-4 | 65.4 [28-129] | 115.9 [90-146] | 23.9 [9-40] | 664.3 [376-909] | 1.19 |
| T-MECH-R1-M4 | 66.7 [29-129] | 138.8 [125-172] | 20.5 [8-34] | 784.3 [622-909] | 1.13 |
| T-ML-R1-5 | 69.2 [27-129] | 115.7 [90-146] | 22.4 [8-40] | 676.7 [459-779] | 1.19 |
| T-MECH-R1-M5 | 61.5 [18-129] | 131.9 [78-172] | 14.8 [4-28] | 853.5 [679-1200] | 0.81 |

Mechanistic arm:
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| T-ML-R1-1 | 60.9 [33-92] | 127.9 [90-169] | 23.2 [10-38] | 896.7 [510-1334] | 1.27 |
| T-MECH-R1-M1 | 96.2 [53-145] | 176.1 [124-232] | 37.7 [18-61] | 1218.7 [694-1813] | 1.81 |
| T-ML-R1-2 | 68.2 [37-103] | 135.2 [95-179] | 24.3 [11-40] | 839.9 [478-1250] | 1.33 |
| T-MECH-R1-M2 | 96.0 [53-144] | 175.9 [124-232] | 37.6 [18-61] | 1216.8 [693-1810] | 1.81 |
| T-ML-R1-3 | 62.0 [34-94] | 135.5 [95-179] | 24.7 [11-40] | 822.6 [468-1224] | 1.35 |
| T-MECH-R1-M3 | 95.7 [53-144] | 175.6 [124-231] | 37.5 [18-61] | 1213.3 [691-1805] | 1.81 |
| T-ML-R1-4 | 51.3 [28-78] | 124.8 [87-165] | 20.7 [9-34] | 774.9 [441-1153] | 1.14 |
| T-MECH-R1-M4 | 86.0 [47-129] | 162.3 [114-214] | 33.8 [16-55] | 990.4 [564-1474] | 1.67 |
| T-ML-R1-5 | 54.9 [30-83] | 119.7 [84-158] | 21.2 [9-35] | 775.2 [441-1154] | 1.16 |
| T-MECH-R1-M5 | 56.3 [31-85] | 122.9 [86-163] | 14.4 [6-24] | 1285.3 [732-1912] | 0.79 |

### Go-criterion result (offline, scope_offline/A/GO_CRITERION.md)
Spearman lead of the NB law over the forest (pooled OOF, 5-fold x 10 repeats): raw Pyr-Int +0.241 (min over repeats +0.182); raw Int-Int +0.208 (min +0.145). Criterion >= 0.15 met on the mean for both.

### Fable cost estimate
Fable session cost estimate at pre-registration: $28.35, calibrated on the $24 figure; subagent costs not included.

---
### Analyst (Fable 5.2) predictions, mechanistic arm, written before any run
1. Held-out set (24 runs): the law has higher Spearman than the forest on raw Pyr-Int and raw Int-Int counts (expected about 0.65-0.75 vs 0.45-0.55) and on J; the gap is smaller (< 0.1) on raw Int-Pyr and usable_conns2. Both arms' 80% intervals under-cover on the new seeds (coverage 0.6-0.75 rather than 0.8), the forest's more than the law's, because all training data are from one seed.
2. Shape at fixed volume (not in the law, which only sees volume): compact beats thin. Relative to M1 (radius 113, thickness 50): M3 (142, 32) gives about 0.8 of M1's raw Pyr-Int count and about 0.85 of its usable_conns2; M2 (179, 20) gives 0.5-0.65 of M1's raw Pyr-Int and 0.6-0.75 of its usable_conns2. Reason: the measured connection kernel has a length scale (140-190 um) comparable to the disc radius, so a wide thin disc puts many pairs out of reach. The law predicts no difference (96 / 176 / 38 / 1219 for all three).
3. M1 absolute values: raw Pyr-Int 110 (80% range 65-160), raw Int-Pyr 190 (150-235), raw Int-Int 40 (20-62), usable_conns2 1250 (800-1800); J about 1.9; M1 reaches T1 (probability 0.85) and T2 (probability 0.6).
4. M4 (dm.weight 0.8) gives 0.85-0.92 of M1's raw interneuron-pathway counts and about 0.8 of its usable_conns2.
5. M5 (18 interneurons) has J below 1.041, limited by raw Int-Int (predicted about 14, reference 18.25): interneuron count, not density, limits J at that corner.
6. Runs needed: the mechanistic arm reaches T1 on its first run. The forest arm also reaches T1 within its first 5 runs, because the optimum is a corner both methods find; I expect the mechanistic arm's best soft-clean J after 10 runs to be higher than the forest's by 10-30%, not more.
7. Nominations: seed coefficient of variation of the components 0.12-0.25; with that spread, hit rate at T1 is >= 7 of 9 for the mechanistic arm and >= 5 of 9 for the forest arm; at T2 it is below 5 of 9 for both.
8. Wall time: runs with 100 neurons at days 25 take 550-700 s (fitted model: 620 s); no run hits the 1500 s timeout.
---

Queue 1 launched 2026-11-10 23:32:50 PST


## Round 1 results (2026-11-11 01:56:55 PST)
Queue 1 finished DONE: 10 runs, sims 700-709, seed 20240628, all rc=0.
| run_id | sim | config d/pyr/int/ms/R/t/dm | wall_s (pred) | PI | IP | II | conns2 | raw PP | J | soft-clean | T1 | T2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-ML-R1-1 | 700 | 25/64/25/11/136/44/0.9 | 841 (505) | 57 | 125 | 20 | 700 | 4637 | 1.096 | True | True | False |
| T-MECH-R1-M1 | 701 | 25/70/30/12/113/50/1.0 | 943 (620) | 74 | 185 | 35 | 915 | 6201 | 1.762 | True | True | True |
| T-ML-R1-2 | 702 | 23/69/28/12/141/32/0.9 | 809 (470) | 53 | 116 | 23 | 777 | 4617 | 1.193 | True | True | False |
| T-MECH-R1-M2 | 703 | 25/70/30/12/179/20/1.0 | 775 (620) | 52 | 158 | 17 | 1069 | 5249 | 0.932 | True | False | False |
| T-ML-R1-3 | 704 | 24/67/28/13/140/41/0.9 | 818 (507) | 63 | 155 | 26 | 715 | 4474 | 1.425 | True | True | False |
| T-MECH-R1-M3 | 705 | 25/70/30/12/142/32/1.0 | 888 (620) | 98 | 155 | 44 | 730 | 5687 | 1.587 | True | True | True |
| T-ML-R1-4 | 706 | 25/64/25/14/136/44/0.8 | 674 (505) | 67 | 103 | 12 | 665 | 4885 | 0.658 | True | False | False |
| T-MECH-R1-M4 | 707 | 25/70/30/12/113/50/0.8 | 790 (620) | 61 | 195 | 23 | 850 | 6793 | 1.26 | True | True | False |
| T-ML-R1-5 | 708 | 25/64/25/11/136/48/0.8 | 642 (505) | 74 | 89 | 24 | 537 | 4802 | 0.915 | True | False | False |
| T-MECH-R1-M5 | 709 | 25/70/18/12/106/50/1.0 | 841 (495) | 84 | 104 | 12 | 1091 | 6731 | 0.658 | True | False | False |

Each arm's predicted vs observed on its own 5 configs (preds_queue1 files; interval = 10th-90th pct).
ML arm (RF trained on batch B only):
| run_id | PI pred [10-90] / obs | IP pred [10-90] / obs | II pred [10-90] / obs | conns2 pred [10-90] / obs | J pred / obs |
|---|---|---|---|---|---|
| T-ML-R1-1 | 70 [21-129] / 57 | 119 [90-143] / 125 | 24 [8-40] / 20 | 672 [467-798] / 700 | 1.22 / 1.10 |
| T-ML-R1-2 | 54 [18-82] / 53 | 125 [88-143] / 116 | 22 [8-33] / 23 | 591 [459-709] / 777 | 1.21 / 1.19 |
| T-ML-R1-3 | 50 [18-82] / 63 | 120 [88-143] / 155 | 23 [8-34] / 26 | 591 [442-757] / 715 | 1.20 / 1.42 |
| T-ML-R1-4 | 65 [28-129] / 67 | 116 [90-146] / 103 | 24 [9-40] / 12 | 664 [376-909] / 665 | 1.19 / 0.66 |
| T-ML-R1-5 | 69 [27-129] / 74 | 116 [90-146] / 89 | 22 [8-40] / 24 | 677 [459-779] / 537 | 1.19 / 0.92 |

Mechanistic arm (NB2 law trained on batch B only):
| run_id | PI pred [10-90] / obs | IP pred [10-90] / obs | II pred [10-90] / obs | conns2 pred [10-90] / obs | J pred / obs |
|---|---|---|---|---|---|
| T-MECH-R1-M1 | 96 [53-145] / 74 | 176 [124-232] / 185 | 38 [18-61] / 35 | 1219 [694-1813] / 915 | 1.81 / 1.76 |
| T-MECH-R1-M2 | 96 [53-144] / 52 | 176 [124-232] / 158 | 38 [18-61] / 17 | 1217 [693-1810] / 1069 | 1.81 / 0.93 |
| T-MECH-R1-M3 | 96 [53-144] / 98 | 176 [124-231] / 155 | 37 [18-61] / 44 | 1213 [691-1805] / 730 | 1.81 / 1.59 |
| T-MECH-R1-M4 | 86 [47-129] / 61 | 162 [114-214] / 195 | 34 [16-55] / 23 | 990 [564-1474] / 850 | 1.67 / 1.26 |
| T-MECH-R1-M5 | 56 [31-85] / 84 | 123 [86-163] / 104 | 14 [6-24] / 12 | 1285 [732-1912] / 1091 | 0.79 / 0.66 |

Memory (headtohead/mem_watch.log): available memory 138 -> 131 GB over the 10 runs; NES RSS 221 -> 227 GB.
Fable session cost estimate after round 1: $31.79 (cost_estimate.py "estimated cost now"; calibrated on the $24 figure; subagent costs not included).

---
### Analyst scoring of round-1 predictions (Fable 5.2)
- Prediction 2 (shape at fixed volume): mostly MISS. M3/M1 raw Pyr-Int 1.32 (predicted about 0.8): miss. M3/M1 usable_conns2 0.80 (predicted 0.85): hit. M2/M1 raw Pyr-Int 0.70 (predicted 0.5-0.65): partial. M2/M1 usable_conns2 1.17 (predicted 0.6-0.75): miss. Raw Pyr-Pyr synapses do fall with thinness (6201, 5687, 5249), as the kernel argument says, but the thresholded label does not follow. Failed step: I treated one run per config as a measurement; neighbouring configs on the same seed differ by about +/-30% on the interneuron counts, which is larger than the effect predicted.
- Prediction 3 (M1 absolute values): HIT. 74 / 185 / 35 / 915 all inside the stated ranges; J 1.76 (predicted about 1.9); T1 and T2 reached.
- Prediction 4 (dm.weight 0.8 vs 1.0): MISS. Ratios M4/M1: Pyr-Int 0.82, Int-Pyr 1.05, Int-Int 0.66, usable_conns2 0.93 (predicted 0.85-0.92 and 0.8). Same failed step as prediction 2.
- Prediction 5 (M5 limited by Int-Int): HIT. J 0.657, Int-Int 12.
- Prediction 6 (runs needed), interim: both arms reached T1 on their first run, as predicted. Best soft-clean J after 5 runs: mechanistic 1.76, forest 1.42 (+24%, inside the predicted 10-30%). The mechanistic arm reached T2 on run 1; the forest arm has not.
- Prediction 8 (wall time): MISS on duration (775-943 s for 100-neuron runs against 550-700 predicted; the server is 1.25-1.7 times slower than during batch B), HIT on no timeout.

### Analyst round-2 design and predictions, mechanistic arm (written before queue 2)
The law puts the optimum at the corner (pyr 70, int 30, dm.weight 1.0, days 25, density at the 50k limit); round 1 agrees (M1 best). What is left free there is shape and minimum separation, and single runs are noisy, so round 2 samples five neighbours of M1 to average over that noise before nominating:
 M6: pyr 70, int 30, days 25, minsep 10, radius 113, thickness 50, dm.weight 1.0
 M7: pyr 70, int 30, days 25, minsep 15, radius 113, thickness 50, dm.weight 1.0
 M8: pyr 70, int 30, days 25, minsep 12, radius 127, thickness 40, dm.weight 1.0
 M9: pyr 70, int 30, days 25, minsep 12, radius 120, thickness 45, dm.weight 1.0
 M10: pyr 70, int 30, days 25, minsep 12, radius 113, thickness 50, dm.weight 0.9
Predictions: (a) at least 4 of the 5 reach T1 and 2 or 3 of the 5 reach T2; (b) every component of every run lies within +/-35% of the mean of M1 and M3 (Pyr-Int 86, Int-Pyr 170, Int-Int 39.5, usable_conns2 822); (c) no detectable effect of minimum separation (M6 vs M7 J differ by less than the M1-M3 difference of 0.18 in either direction is NOT claimed; I claim only that neither is outside 1.0-2.2); (d) the forest arm's round 2 stays near its round-1 region and its best round-2 J is below 1.6; after 10 runs the mechanistic arm's best soft-clean J is 10-30% above the forest's.
---

## Round 2 pre-registration (2026-11-11 01:56:55 PST, before any queue-2 run)
- ML arm: `ml_arm.py round2 --runs runs.csv`: RF (500 trees, random_state 0) refit on batch B + its 5 round-1 rows (105 rows); method **DiCE** again (same procedure as round 1; 98 unique soft-clean candidates with predicted score >= 1.041; top-5 greedy-diverse at 0.15, excluding all configs already run). Pool fallback not needed.
- Mechanistic arm: M6-M10 fixed by the analyst; all five pass hard limits, size cap and soft-clean (densities 49,122-49,857; pyr fraction 0.700). Law refit on batch B + its 5 round-1 rows (105 rows).
- Queue: queue2.csv interleaved ML/mech, seed 20240628, run_ids T-ML-R2-<k>, T-MECH-R2-M<k>. Pacing/abort rules unchanged (abort at wall > 2 x predicted; observed round-1 walls were 1.3-1.7x predicted).
- Queue-2 predicted wall total (fitted model, which underestimated round 1): 5424 s.
- sha256 queue2.csv: bd0d74b95542fc98525922dbbeafbe175f29a55fba4c2218e89b8a52da0c7ee3
- sha256 ml_round2.csv: 295c7d4a02ab46dddb0c37dc49658e2f4ddbc54d8eca027ad6f90a30c078d47e; mech_round2.csv: a9a9e8c4151d386b35ccdaad37b678a456670d9cb1e20e15df7e99a5e8fd0801; preds_queue2_ml.csv: 552ab32bf69f43b329c2d1fb868f3a75e55677619564992a587d95480b60857a; preds_queue2_mech.csv: 4867f70b4341c4a39076f56cf050c992d9a7dfc508eb41cf4c83abeae7256fca; make_queue2.py: 584c35f16789a75ec32d9a9fd2f63b95bdce819a1926fef847c15ab3395d8889
Mechanistic refit coefficients on batch B + 5 round-1 rows (raw scale; `mech_arm.py refit --runs runs.csv`):
```
training rows 105 (batch B 100 + own MECH runs 5)
== variant M1
  raw_pyr_int_n alpha=0.1029 const=2.071 log(npre*npost)=1.117 logV=-0.506 log dm.weight=0.498 days=0.094 log minsep=-0.443
  raw_int_pyr_n alpha=0.0211 const=0.890 log(npre*npost)=0.775 logV=-0.266 log dm.weight=0.362 days=0.080 log minsep=0.080
  raw_int_int_n alpha=0.1493 const=0.198 log(npre*npost)=0.941 logV=-0.379 log dm.weight=0.466 days=0.120 log minsep=-0.197
  usable_conns2 alpha=0.0997 const=4.759 log(npre*npost)=0.653 logV=-0.407 log dm.weight=0.905 days=0.120 log minsep=-0.137
== variant M1rt
  raw_pyr_int_n alpha=0.0995 const=1.631 log(npre*npost)=1.109 log radius=-1.161 log thickness=-0.318 log dm.weight=0.496 days=0.093 log minsep=-0.435
  raw_int_pyr_n alpha=0.0128 const=0.820 log(npre*npost)=0.750 log radius=-0.755 log thickness=0.017 log dm.weight=0.361 days=0.078 log minsep=0.122
  raw_int_int_n alpha=0.1479 const=-0.193 log(npre*npost)=0.939 log radius=-0.854 log thickness=-0.249 log dm.weight=0.467 days=0.119 log minsep=-0.194
  usable_conns2 alpha=0.0816 const=4.531 log(npre*npost)=0.643 log radius=-1.127 log thickness=-0.008 log dm.weight=0.907 days=0.115 log minsep=-0.100
```
ML round-2 configs:
| config_id | days | pyramidal | interneuron | minneuronseparation | shape.radius | shape.thickness | dm.weight | soft_clean | pred_wall_s |
|---|---|---|---|---|---|---|---|---|---|
| ML-R2-1 | 23 | 69 | 28 | 14 | 141 | 32 | 0.9 | True | 470.0 |
| ML-R2-2 | 24 | 64 | 26 | 10 | 121 | 41 | 0.8 | True | 461.0 |
| ML-R2-3 | 23 | 67 | 28 | 12 | 141 | 32 | 0.9 | True | 453.0 |
| ML-R2-4 | 23 | 69 | 28 | 13 | 141 | 32 | 0.9 | True | 470.0 |
| ML-R2-5 | 23 | 69 | 28 | 15 | 141 | 32 | 0.9 | True | 470.0 |

Queue 2 predictions (each arm predicts all 10), ML arm refit forest:
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| T-ML-R2-1 | 57.9 [40-82] | 130.3 [116-155] | 23.2 [20-30] | 720.2 [611-868] | 1.27 |
| T-MECH-R2-M6 | 54.5 [29-79] | 140.2 [108-172] | 19.4 [8-34] | 785.1 [505-1200] | 1.07 |
| T-ML-R2-2 | 60.9 [43-74] | 123.4 [89-148] | 24.5 [12-34] | 767.9 [665-909] | 1.27 |
| T-MECH-R2-M7 | 54.4 [29-80] | 142.2 [105-172] | 17.9 [8-33] | 788.2 [505-925] | 0.98 |
| T-ML-R2-3 | 55.8 [52-63] | 123.4 [102-155] | 23.6 [22-26] | 704.5 [611-777] | 1.27 |
| T-MECH-R2-M8 | 52.7 [29-74] | 131.2 [105-155] | 19.3 [6-28] | 731.4 [459-829] | 1.06 |
| T-ML-R2-4 | 55.3 [45-80] | 129.5 [116-155] | 23.2 [20-30] | 724.6 [611-777] | 1.27 |
| T-MECH-R2-M9 | 51.8 [29-74] | 133.3 [111-155] | 17.7 [8-30] | 732.7 [459-829] | 0.97 |
| T-ML-R2-5 | 57.0 [34-82] | 129.2 [105-155] | 22.9 [18-30] | 722.4 [611-909] | 1.26 |
| T-MECH-R2-M10 | 55.4 [29-79] | 139.7 [108-172] | 19.7 [8-33] | 759.6 [505-925] | 1.08 |

Mechanistic arm refit NB law:
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| T-ML-R2-1 | 61.7 [34-93] | 136.4 [96-180] | 22.8 [10-37] | 792.5 [454-1175] | 1.25 |
| T-MECH-R2-M6 | 99.7 [55-150] | 172.7 [122-227] | 37.0 [18-59] | 1181.3 [678-1751] | 1.78 |
| T-ML-R2-2 | 64.6 [35-98] | 124.8 [88-165] | 23.0 [10-38] | 780.1 [447-1157] | 1.26 |
| T-MECH-R2-M7 | 83.3 [46-126] | 178.4 [126-234] | 34.2 [16-55] | 1117.4 [641-1656] | 1.83 |
| T-ML-R2-3 | 63.9 [35-97] | 131.7 [93-174] | 23.5 [11-38] | 778.6 [446-1155] | 1.29 |
| T-MECH-R2-M8 | 91.5 [51-138] | 174.8 [124-230] | 35.6 [17-57] | 1147.2 [658-1700] | 1.80 |
| T-ML-R2-4 | 63.7 [35-97] | 135.6 [96-179] | 23.1 [11-38] | 800.6 [459-1187] | 1.27 |
| T-MECH-R2-M9 | 91.3 [51-138] | 174.6 [124-229] | 35.5 [17-57] | 1145.2 [657-1697] | 1.79 |
| T-ML-R2-5 | 59.8 [33-91] | 137.2 [97-181] | 22.5 [10-37] | 785.0 [450-1164] | 1.23 |
| T-MECH-R2-M10 | 87.3 [48-132] | 168.7 [119-222] | 34.0 [16-55] | 1047.3 [601-1552] | 1.73 |


Queue 2 launched 2026-11-11 01:57:04 PST


## Round 2 results (2026-11-11 04:03:46 PST)
Queue 2 finished DONE: 10 runs, sims 710-719, seed 20240628, all rc=0.
| run_id | sim | config d/pyr/int/ms/R/t/dm | wall_s (pred) | PI | IP | II | conns2 | raw PP | J | soft-clean | T1 | T2 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T-ML-R2-1 | 710 | 23/69/28/14/141/32/0.9 | 650 (470) | 29 | 162 | 16 | 671 | 6100 | 0.69 | True | False | False |
| T-MECH-R2-M6 | 711 | 25/70/30/10/113/50/1.0 | 836 (620) | 43 | 188 | 14 | 1078 | 7022 | 0.767 | True | False | False |
| T-ML-R2-2 | 712 | 24/64/26/10/121/41/0.8 | 520 (461) | 93 | 145 | 38 | 882 | 4970 | 1.491 | True | True | False |
| T-MECH-R2-M7 | 713 | 25/70/30/15/113/50/1.0 | 833 (620) | 188 | 167 | 87 | 820 | 5335 | 1.717 | True | True | True |
| T-ML-R2-3 | 714 | 23/67/28/12/141/32/0.9 | 601 (453) | 86 | 104 | 38 | 498 | 4206 | 1.069 | True | True | False |
| T-MECH-R2-M8 | 715 | 25/70/30/12/127/40/1.0 | 759 (620) | 46 | 148 | 20 | 808 | 5773 | 1.095 | True | True | False |
| T-ML-R2-4 | 716 | 23/69/28/13/141/32/0.9 | 739 (470) | 46 | 120 | 13 | 754 | 4582 | 0.712 | True | False | False |
| T-MECH-R2-M9 | 717 | 25/70/30/12/120/45/1.0 | 779 (620) | 106 | 147 | 36 | 889 | 5598 | 1.512 | True | True | False |
| T-ML-R2-5 | 718 | 23/69/28/15/141/32/0.9 | 556 (470) | 42 | 133 | 18 | 897 | 5697 | 0.986 | True | False | False |
| T-MECH-R2-M10 | 719 | 25/70/30/12/113/50/0.9 | 863 (620) | 65 | 189 | 36 | 874 | 6449 | 1.548 | True | True | True |

Predicted vs observed, own configs (pred = pre-registered round-2 prediction from the refit model; interval 10th-90th pct).
ML arm:
| run_id | PI pred [10-90] / obs | IP pred [10-90] / obs | II pred [10-90] / obs | conns2 pred [10-90] / obs | J pred / obs |
|---|---|---|---|---|---|
| T-ML-R2-1 | 58 [40-82] / 29 | 130 [116-155] / 162 | 23 [20-30] / 16 | 720 [611-868] / 671 | 1.27 / 0.69 |
| T-ML-R2-2 | 61 [43-74] / 93 | 123 [89-148] / 145 | 25 [12-34] / 38 | 768 [665-909] / 882 | 1.27 / 1.49 |
| T-ML-R2-3 | 56 [52-63] / 86 | 123 [102-155] / 104 | 24 [22-26] / 38 | 705 [611-777] / 498 | 1.27 / 1.07 |
| T-ML-R2-4 | 55 [45-80] / 46 | 129 [116-155] / 120 | 23 [20-30] / 13 | 725 [611-777] / 754 | 1.27 / 0.71 |
| T-ML-R2-5 | 57 [34-82] / 42 | 129 [105-155] / 133 | 23 [18-30] / 18 | 722 [611-909] / 897 | 1.26 / 0.99 |

Mechanistic arm:
| run_id | PI pred [10-90] / obs | IP pred [10-90] / obs | II pred [10-90] / obs | conns2 pred [10-90] / obs | J pred / obs |
|---|---|---|---|---|---|
| T-MECH-R2-M6 | 100 [55-150] / 43 | 173 [122-227] / 188 | 37 [18-59] / 14 | 1181 [678-1751] / 1078 | 1.78 / 0.77 |
| T-MECH-R2-M7 | 83 [46-126] / 188 | 178 [126-234] / 167 | 34 [16-55] / 87 | 1117 [641-1656] / 820 | 1.83 / 1.72 |
| T-MECH-R2-M8 | 92 [51-138] / 46 | 175 [124-230] / 148 | 36 [17-57] / 20 | 1147 [658-1700] / 808 | 1.80 / 1.10 |
| T-MECH-R2-M9 | 91 [51-138] / 106 | 175 [124-229] / 147 | 36 [17-57] / 36 | 1145 [657-1697] / 889 | 1.79 / 1.51 |
| T-MECH-R2-M10 | 87 [48-132] / 65 | 169 [119-222] / 189 | 34 [16-55] / 36 | 1047 [601-1552] / 874 | 1.73 / 1.55 |

Running summary after 10 training runs per arm (arm order = run order in runs.csv):
| arm | n_runs | best soft-clean J | mean J | runs reaching T1 | runs reaching T2 | first run reaching T1 | first run reaching T2 |
|---|---|---|---|---|---|---|---|
| ML | 10 | 1.491 | 1.024 | 5 | 0 | 1 | nan |
| MECH | 10 | 1.762 | 1.284 | 7 | 4 | 1 | 1.0 |

Memory (mem_watch.log): available memory 138 GB (2026-11-10 23:47) -> 125 GB (2026-11-11 04:00, after 20 runs); NES RSS 221 -> 233 GB.
Fable session cost estimate after round 2: $34.41 (cost_estimate.py; calibrated on the $24 figure; subagent costs not included).

---
### Analyst scoring of round-2 predictions (Fable 5.2)
- (a) HIT. 4 of 5 mechanistic runs reach T1 (M7 1.72, M10 1.55, M9 1.51, M8 1.10; M6 0.77 does not) and 2 of 5 reach T2 (M7, M10).
- (b) MISS. Interneuron-pathway counts are far outside +/-35%: raw Pyr-Int 43 (M6), 46 (M8) and 188 (M7) against a centre of 86; raw Int-Int 14, 20 and 87 against 39.5. Int-Pyr and usable_conns2 stay inside the band except M6's usable_conns2 (1078, +31%, inside) . Failed step: I sized the band from two runs (M1, M3). The Pyr-Int and Int-Int totals on one seed change by a factor of 2-4 between configs that differ only in minimum separation (M6 vs M7), consistent with the offline finding that a few interneurons collect most of the input.
- (c) MISS. M6 has J 0.77, outside 1.0-2.2.
- (d) HIT. Forest best round-2 J is 1.49 (< 1.6). After 10 runs the best soft-clean J is 1.76 (mechanistic) vs 1.49 (forest), +18%, inside 10-30%. Mean J over the 10 training runs: mechanistic 1.29, forest 1.02.

### Analyst nominations and predictions, mechanistic arm (written before queue 3)
Nominations: M1 (minsep 12, radius 113, thickness 50), M7 (minsep 15, radius 113, thickness 50), M9 (minsep 12, radius 120, thickness 45); all pyr 70, int 30, days 25, dm.weight 1.0. Reason: the law's optimum is this corner; within the corner family single runs do not separate shapes or separations reliably, so I take the law's optimum and the two neighbours with the highest observed J that keep dm.weight at 1.0 and a compact shape (the refit with radius and thickness separate gives radius exponent -1.16 for raw Pyr-Int).
Predictions for the 9 mechanistic and 9 forest nomination runs (seeds 3001-3003):
1. Selection will not survive new seeds: mean J of the mechanistic nominations is about 1.3 (range 1.1-1.5), equal to the mean of its corner-family training runs, not to the best of them (1.76).
2. Hit rate at T1: mechanistic 6 of 9 (5-8); forest 4 of 9 (2-6). This revises my pre-registered ">= 7 of 9" downward for the mechanistic arm after seeing the run-to-run scatter. At T2: mechanistic 3 of 9 (1-5); forest at most 1 of 9.
3. Mean J: mechanistic higher than forest by 15-35%.
4. Seed coefficient of variation within a config: raw Pyr-Int and raw Int-Int 0.4-0.6 (revised up from the pre-registered 0.12-0.25); raw Int-Pyr and usable_conns2 0.1-0.2.
5. In every nomination run of both arms, J is limited by raw Pyr-Int or raw Int-Int, not by Int-Pyr or usable_conns2 (at most 2 exceptions in 18).

---

## Nomination pre-registration (2026-11-11 04:03:46 PST, before any queue-3 run)
- ML nominations: `ml_arm.py nominate --runs runs.csv` (RF 500 trees refit on batch B + its 10 rows = 110 rows). Method: **pool** (60000 scrambled Sobol points, seed 123, soft-clean, score = min component mean/reference, top-3 greedy-diverse at 0.15), as pre-registered for nominations; DiCE is not used here.
- Mechanistic nominations: M1, M7, M9 (analyst). Law refit on batch B + its 10 rows.
- All 6 nominated configs asserted: hard limits, size cap, soft-clean (pass).
- queue3.csv: 18 nomination runs (seeds 3001, 3002, 3003; arms interleaved) then 24 held-out runs (12 configs at seed 2001, then at 2002; arm HELD). Held-out predictions scored are the ORIGINAL pre-registration files (preds_heldout_ml.csv / preds_heldout_mech.csv), not regenerated.
- Predicted wall (fitted model): queue 3 total 15581 s = 4.33 h (nominations 9527 s, held-out 6055 s). At the observed 1.3-1.7x slowdown, expected real duration 5.6-7.4 h. Abort rule unchanged (wall > 2 x predicted).
- sha256 queue3.csv: 0441a6e4e6f4913e25f28d7e32f4a435949668aae61661b94f5a575601c4dfe0
- sha256 nominations.csv: f998b88eda42224640806c7ac7f974c5945161d59e7bcdde51557ee53afe1f9d; ml_nominate.csv: 826dfd6b423e6f1b8c92f4f28edb80758349b6e9c3f038757103b177ce4edec8; preds_nom_ml.csv: 5ed47e2e30c680d024b05b2e36e2afec2819087330a4fcbbb193ba50037ec5b2; preds_nom_mech.csv: 9d5a9bf51a2bcaff949b54315a64bf7c50ad6595582ccc8fa1d849316d4a5497; make_queue3.py: 77c887d9deb12d315a6ae47b0e5d2e0754606f859824970ff50d85b0efd5cc47; preds_heldout_ml.csv: 566655d188c609e2207be96890b17e78917172bb003855972e52b930e083490e; preds_heldout_mech.csv: 8d97f76ca0ae4b1aafe288f04c1c10aff7ec539e4362b45dbd048a5d92d37887
Nominated configs:
| run_id | arm | config_id | days | pyramidal | interneuron | minneuronseparation | shape.radius | shape.thickness | dm.weight |
|---|---|---|---|---|---|---|---|---|---|
| nom-ML-NOM-1 | ML | ML-NOM-1 | 24 | 65 | 24 | 10 | 122 | 39 | 0.9 |
| nom-ML-NOM-2 | ML | ML-NOM-2 | 24 | 62 | 26 | 12 | 107 | 49 | 0.9 |
| nom-ML-NOM-3 | ML | ML-NOM-3 | 23 | 66 | 25 | 10 | 133 | 43 | 0.9 |
| nom-M1 | MECH | M1 | 25 | 70 | 30 | 12 | 113 | 50 | 1.0 |
| nom-M7 | MECH | M7 | 25 | 70 | 30 | 15 | 113 | 50 | 1.0 |
| nom-M9 | MECH | M9 | 25 | 70 | 30 | 12 | 120 | 45 | 1.0 |

ML arm predictions for the 6 nominated configs (refit forest):
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| ML-NOM-1 | 75.6 [54-93] | 138.9 [104-172] | 27.5 [10-38] | 851.2 [680-925] | 1.43 |
| ML-NOM-2 | 66.6 [36-93] | 130.5 [89-172] | 24.8 [8-34] | 796.1 [537-925] | 1.34 |
| ML-NOM-3 | 61.2 [48-87] | 130.2 [103-145] | 25.5 [8-38] | 721.6 [498-829] | 1.34 |
| M1 | 56.4 [29-86] | 133.6 [103-172] | 18.8 [8-33] | 766.4 [505-884] | 1.03 |
| M7 | 54.2 [29-82] | 137.6 [103-172] | 18.3 [8-33] | 809.0 [505-925] | 1.01 |
| M9 | 57.3 [29-93] | 132.6 [111-155] | 19.3 [8-33] | 755.3 [498-882] | 1.06 |

Mechanistic arm predictions for the 6 nominated configs (refit NB law):
| id | PyrInt mean [10-90%] | IntPyr mean [10-90%] | IntInt mean [10-90%] | conns2 mean [10-90%] | J |
|---|---|---|---|---|---|
| ML-NOM-1 | 61.9 [33-95] | 124.7 [88-164] | 20.2 [9-34] | 869.9 [503-1284] | 1.11 |
| ML-NOM-2 | 62.8 [33-97] | 130.5 [92-172] | 24.2 [11-40] | 807.5 [466-1192] | 1.33 |
| ML-NOM-3 | 52.3 [27-81] | 111.9 [79-148] | 17.4 [7-29] | 710.3 [410-1049] | 0.95 |
| M1 | 91.3 [49-140] | 173.8 [123-228] | 36.0 [16-59] | 1102.3 [637-1627] | 1.79 |
| M7 | 87.0 [46-133] | 176.3 [125-231] | 36.8 [17-60] | 1066.2 [616-1574] | 1.81 |
| M9 | 90.6 [48-139] | 173.2 [123-227] | 35.8 [16-59] | 1095.8 [634-1617] | 1.78 |


Queue 3 launched 2026-11-11 04:03:56 PST

## Final results (queue 3 done; written 2026-11-11 10:27:44 PST)
Queue 3 status DONE, 42 runs, sims 720-761, all rc 0, no STOP, no run over 2x predicted wall (max ratio 1.99, max wall 1234 s). Memory available at end 108 GB (start of track: 138 GB), NES RSS 251 GB. Fable cost estimate so far: $35.93 (subagents not included). Hard stop $45.

### Scoring tables (score_final.py)
# SCORE_FINAL

## A. Sanity
| item | value |
|---|---|
| rows_per_queue | {"queue1": 10, "queue2": 10, "queue3": 42} |
| all_rc0 | True |
| sim_id_min | 700 |
| sim_id_max | 761 |
| sim_id_unique | True |
| wall_s | {"min": 153.7, "median": 632.45, "max": 1233.6} |
| q3_ratio | {"median": 1.3471196844865916, "max": 1.9890357949048691} |
| runs_over_2x_all | [] |
| q3_over_2x | [] |
| J_recompute_maxabsdiff | 0 |
| nan_cells_in_key_cols | 0 |

## B. Held-out prediction error
### vs config_mean (12 config means over 2 seeds)
| arm | target | n | Spearman | R2 | PoissonD2 | MAE | MedAbsRelErr | cov80 |
|---|---|---|---|---|---|---|---|---|
| ml | raw_pyr_int_n | 12 | 0.741 | -0.118 | -0.0316 | 13.2 | 0.67 | 0.75 |
| ml | raw_int_pyr_n | 12 | 0.545 | -0.343 | -0.207 | 17.6 | 0.22 | 0.75 |
| ml | raw_int_int_n | 12 | 0.809 | 0.445 | 0.48 | 4.43 | 0.428 | 1 |
| ml | usable_conns2 | 12 | 0.818 | 0.441 | 0.459 | 100 | 0.343 | 0.75 |
| ml | J | 12 | 0.79 | -1.09 | nan | 0.246 | 0.847 | nan |
| mech | raw_pyr_int_n | 12 | 0.846 | 0.545 | 0.64 | 7.23 | 0.328 | 0.833 |
| mech | raw_int_pyr_n | 12 | 0.79 | 0.549 | 0.665 | 8.33 | 0.0989 | 1 |
| mech | raw_int_int_n | 12 | 0.785 | 0.34 | 0.488 | 4.77 | 0.368 | 0.917 |
| mech | usable_conns2 | 12 | 0.902 | 0.363 | 0.606 | 96.5 | 0.29 | 0.833 |
| mech | J | 12 | 0.811 | -0.0866 | nan | 0.172 | 0.464 | nan |

### vs per_run (24 runs)
| arm | target | n | Spearman | R2 | PoissonD2 | MAE | MedAbsRelErr | cov80 |
|---|---|---|---|---|---|---|---|---|
| ml | raw_pyr_int_n | 24 | 0.656 | -0.102 | -0.0259 | 13.8 | 0.43 | 0.708 |
| ml | raw_int_pyr_n | 24 | 0.574 | -0.273 | -0.17 | 19.1 | 0.298 | 0.583 |
| ml | raw_int_int_n | 24 | 0.593 | 0.29 | 0.325 | 6.06 | 0.483 | 0.917 |
| ml | usable_conns2 | 24 | 0.814 | 0.421 | 0.445 | 103 | 0.294 | 0.708 |
| ml | J | 24 | 0.685 | -0.923 | nan | 0.257 | 0.921 | nan |
| mech | raw_pyr_int_n | 24 | 0.755 | 0.469 | 0.525 | 8.92 | 0.335 | 0.708 |
| mech | raw_int_pyr_n | 24 | 0.782 | 0.436 | 0.547 | 12.4 | 0.169 | 0.958 |
| mech | raw_int_int_n | 24 | 0.608 | 0.221 | 0.33 | 5.95 | 0.338 | 0.833 |
| mech | usable_conns2 | 24 | 0.887 | 0.346 | 0.587 | 96.5 | 0.295 | 0.792 |
| mech | J | 24 | 0.716 | -0.0736 | nan | 0.176 | 0.504 | nan |

### vs general_H01-H08 (config means)
| arm | target | n | Spearman | R2 | PoissonD2 | MAE | MedAbsRelErr | cov80 |
|---|---|---|---|---|---|---|---|---|
| ml | raw_pyr_int_n | 8 | 0.619 | 0.0208 | -0.0119 | 14.5 | 1 | 0.625 |
| ml | raw_int_pyr_n | 8 | 0.31 | -0.746 | -0.561 | 20.7 | 0.3 | 0.625 |
| ml | raw_int_int_n | 8 | 0.826 | 0.34 | 0.385 | 5.52 | 0.746 | 1 |
| ml | usable_conns2 | 8 | 0.738 | 0.0479 | 0.22 | 93.8 | 0.343 | 0.75 |
| ml | J | 8 | 0.881 | -0.874 | nan | 0.232 | 0.956 | nan |
| mech | raw_pyr_int_n | 8 | 0.905 | 0.61 | 0.682 | 6.8 | 0.394 | 0.75 |
| mech | raw_int_pyr_n | 8 | 0.905 | 0.757 | 0.786 | 6.68 | 0.111 | 1 |
| mech | raw_int_int_n | 8 | 0.599 | 0.434 | 0.518 | 4.64 | 0.41 | 0.875 |
| mech | usable_conns2 | 8 | 0.857 | 0.647 | 0.72 | 60.3 | 0.208 | 1 |
| mech | J | 8 | 0.881 | 0.386 | nan | 0.123 | 0.38 | nan |

### vs corner_H09-H12 (config means)
| arm | target | n | Spearman | R2 | PoissonD2 | MAE | MedAbsRelErr | cov80 |
|---|---|---|---|---|---|---|---|---|
| ml | raw_pyr_int_n | 4 | 0.6 | -2.75 | -1.52 | 10.6 | 0.431 | 1 |
| ml | raw_int_pyr_n | 4 | -0.4 | -26.1 | -23.9 | 11.5 | 0.172 | 1 |
| ml | raw_int_int_n | 4 | 0.8 | 0.531 | 0.505 | 2.25 | 0.095 | 1 |
| ml | usable_conns2 | 4 | 0.8 | 0.556 | 0.518 | 112 | 0.298 | 0.75 |
| ml | J | 4 | 0 | -2.23 | nan | 0.274 | 0.712 | nan |
| mech | raw_pyr_int_n | 4 | 0.4 | -0.62 | -0.314 | 8.09 | 0.276 | 1 |
| mech | raw_int_pyr_n | 4 | 0.4 | -48.2 | -39.6 | 11.6 | 0.0828 | 1 |
| mech | raw_int_int_n | 4 | 0.6 | -1.29 | -0.653 | 5.03 | 0.264 | 1 |
| mech | usable_conns2 | 4 | 1 | -0.0464 | 0.315 | 169 | 0.695 | 0.5 |
| mech | J | 4 | 0.4 | -1.45 | nan | 0.269 | 0.864 | nan |

### Bootstrap (2000 resamples of 12 config means, seed 0; Spearman mech - ml; NaN resamples dropped)
| target | point diff | CI90 lo | CI90 hi | frac mech>ml | frac tie | frac ml>mech | n valid | n NaN |
|---|---|---|---|---|---|---|---|---|
| raw_pyr_int_n | 0.105 | -0.256 | 0.495 | 0.704 | 0.0135 | 0.282 | 2000 | 0 |
| raw_int_pyr_n | 0.245 | -0.109 | 0.642 | 0.875 | 0.0085 | 0.117 | 2000 | 0 |
| raw_int_int_n | -0.0245 | -0.241 | 0.152 | 0.337 | 0.064 | 0.6 | 2000 | 0 |
| usable_conns2 | 0.0839 | -0.107 | 0.288 | 0.795 | 0.038 | 0.167 | 2000 | 0 |
| J | 0.021 | -0.178 | 0.25 | 0.565 | 0.0285 | 0.407 | 2000 | 0 |

## C. Held-out seed spread
| target | median |a-b|/mean | max | Spearman s2001 vs s2002 | Pearson |
|---|---|---|---|---|
| raw_pyr_int_n | 0.532 | 1.43 | 0.644 | 0.742 |
| raw_int_pyr_n | 0.242 | 0.426 | 0.722 | 0.593 |
| raw_int_int_n | 0.667 | 1.48 | 0.32 | 0.389 |
| usable_conns2 | 0.226 | 0.285 | 0.963 | 0.956 |
| J | 0.32 | 1.38 | 0.552 | 0.717 |

## D. Nominations
| arm | config | seed | raw_pyr_int_n | raw_int_pyr_n | raw_int_int_n | usable_conns2 | J | soft_clean | limiting |
|---|---|---|---|---|---|---|---|---|---|
| ML | ML-NOM-1 | 3001 | 56 | 140 | 12 | 913 | 0.658 | True | raw_int_int_n |
| MECH | M1 | 3001 | 44 | 182 | 19 | 853 | 1.04 | True | raw_int_int_n |
| ML | ML-NOM-2 | 3001 | 29 | 144 | 11 | 810 | 0.603 | True | raw_int_int_n |
| MECH | M7 | 3001 | 31 | 210 | 15 | 824 | 0.738 | True | raw_pyr_int_n |
| ML | ML-NOM-3 | 3001 | 11 | 113 | 3 | 747 | 0.164 | True | raw_int_int_n |
| MECH | M9 | 3001 | 29 | 205 | 9 | 900 | 0.493 | True | raw_int_int_n |
| ML | ML-NOM-1 | 3002 | 37 | 130 | 10 | 741 | 0.548 | True | raw_int_int_n |
| MECH | M1 | 3002 | 86 | 155 | 29 | 771 | 1.59 | True | raw_int_int_n |
| ML | ML-NOM-2 | 3002 | 65 | 157 | 34 | 668 | 1.45 | True | usable_conns2 |
| MECH | M7 | 3002 | 82 | 184 | 37 | 1054 | 1.89 | True | raw_int_pyr_n |
| ML | ML-NOM-3 | 3002 | 56 | 91 | 14 | 637 | 0.767 | True | raw_int_int_n |
| MECH | M9 | 3002 | 38 | 210 | 13 | 1016 | 0.712 | True | raw_int_int_n |
| ML | ML-NOM-1 | 3003 | 44 | 135 | 12 | 838 | 0.658 | True | raw_int_int_n |
| MECH | M1 | 3003 | 69 | 178 | 31 | 766 | 1.64 | True | raw_pyr_int_n |
| ML | ML-NOM-2 | 3003 | 39 | 141 | 15 | 707 | 0.822 | True | raw_int_int_n |
| MECH | M7 | 3003 | 49 | 176 | 22 | 1275 | 1.17 | True | raw_pyr_int_n |
| ML | ML-NOM-3 | 3003 | 42 | 112 | 13 | 675 | 0.712 | True | raw_int_int_n |
| MECH | M9 | 3003 | 71 | 173 | 26 | 953 | 1.42 | True | raw_int_int_n |

Per config mean / SD (ddof=1) / CV
| arm | config | raw_pyr_int_n mean | raw_pyr_int_n sd | raw_pyr_int_n cv | raw_int_pyr_n mean | raw_int_pyr_n sd | raw_int_pyr_n cv | raw_int_int_n mean | raw_int_int_n sd | raw_int_int_n cv | usable_conns2 mean | usable_conns2 sd | usable_conns2 cv | J mean | J sd | J cv |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ML | ML-NOM-1 | 45.7 | 9.61 | 0.21 | 135 | 5 | 0.037 | 11.3 | 1.15 | 0.102 | 831 | 86.2 | 0.104 | 0.621 | 0.0633 | 0.102 |
| MECH | M1 | 66.3 | 21.1 | 0.318 | 172 | 14.6 | 0.0849 | 26.3 | 6.43 | 0.244 | 797 | 48.9 | 0.0613 | 1.42 | 0.333 | 0.234 |
| ML | ML-NOM-2 | 44.3 | 18.6 | 0.419 | 147 | 8.5 | 0.0577 | 20 | 12.3 | 0.614 | 728 | 73.4 | 0.101 | 0.959 | 0.441 | 0.46 |
| MECH | M7 | 54 | 25.9 | 0.479 | 190 | 17.8 | 0.0936 | 24.7 | 11.2 | 0.456 | 1.05e+03 | 226 | 0.215 | 1.27 | 0.583 | 0.461 |
| ML | ML-NOM-3 | 36.3 | 23 | 0.634 | 105 | 12.4 | 0.118 | 10 | 6.08 | 0.608 | 686 | 55.9 | 0.0814 | 0.548 | 0.333 | 0.608 |
| MECH | M9 | 46 | 22.1 | 0.481 | 196 | 20.1 | 0.102 | 16 | 8.89 | 0.556 | 956 | 58.1 | 0.0607 | 0.877 | 0.487 | 0.556 |

| arm | n | mean J | median J | T1 hits | T2 hits | best J |
|---|---|---|---|---|---|---|
| MECH | 9 | 1.19 | 1.17 | 6 | 3 | 1.89 |
| ML | 9 | 0.709 | 0.658 | 1 | 0 | 1.45 |

Limiting component counts over 18 runs: {"raw_int_int_n": 13, "raw_pyr_int_n": 3, "usable_conns2": 1, "raw_int_pyr_n": 1}; by arm: {"MECH": {"raw_int_int_n": 5, "raw_pyr_int_n": 3, "raw_int_pyr_n": 1}, "ML": {"raw_int_int_n": 8, "usable_conns2": 1}}

| config | obs mean J | ml pred J | mech pred J |
|---|---|---|---|
| ML-NOM-1 | 0.621 | 1.43 | 1.11 |
| ML-NOM-2 | 0.959 | 1.34 | 1.33 |
| ML-NOM-3 | 0.548 | 1.34 | 0.955 |
| M1 | 1.42 | 1.03 | 1.79 |
| M7 | 1.27 | 1.01 | 1.81 |
| M9 | 0.877 | 1.06 | 1.78 |

ml: MAE=0.469, bias(pred-obs)=0.252, Spearman(6)=-0.657, obs rank (order ['ML-NOM-1', 'ML-NOM-2', 'ML-NOM-3', 'M1', 'M7', 'M9'])=[5.0, 3.0, 6.0, 1.0, 2.0, 4.0], pred rank=[1.0, 2.0, 3.0, 5.0, 6.0, 4.0]
mech: MAE=0.513, bias(pred-obs)=0.513, Spearman(6)=0.886, obs rank (order ['ML-NOM-1', 'ML-NOM-2', 'ML-NOM-3', 'M1', 'M7', 'M9'])=[5.0, 3.0, 6.0, 1.0, 2.0, 4.0], pred rank=[5.0, 4.0, 6.0, 2.0, 1.0, 3.0]

## E. Training recap (queues 1-2, run order in file)
| arm | n | n soft_clean | best soft-clean J | best J any | mean J | n T1 | n T2 | first T1 idx | first T2 idx |
|---|---|---|---|---|---|---|---|---|---|
| ML | 10 | 10 | 1.49 | 1.49 | 1.02 | 5 | 0 | 1 | nan |
| MECH | 10 | 10 | 1.76 | 1.76 | 1.28 | 7 | 4 | 1 | 1 |

ML J sequence: [1.096, 1.193, 1.425, 0.658, 0.915, 0.69, 1.491, 1.069, 0.712, 0.986]; soft_clean: [True, True, True, True, True, True, True, True, True, True]
MECH J sequence: [1.762, 0.932, 1.587, 1.26, 0.658, 0.767, 1.717, 1.095, 1.512, 1.548]; soft_clean: [True, True, True, True, True, True, True, True, True, True]

## F. Training vs nomination re-runs
| arm | config | train J (seed 20240628) | nom J s3001 | s3002 | s3003 | nom mean | train - nom mean |
|---|---|---|---|---|---|---|---|
| MECH | M1 | 1.76 | 1.04 | 1.59 | 1.64 | 1.42 | 0.338 |
| MECH | M7 | 1.72 | 0.738 | 1.89 | 1.17 | 1.27 | 0.452 |
| MECH | M9 | 1.51 | 0.493 | 0.712 | 1.42 | 0.877 | 0.635 |

ML nominations matching an ML training config_id: []

## Anomalies / notes
- soft_clean False rows by kind: {"H": 18}
- soft_clean False run_ids: H-H01-s2001, H-H02-s2001, H-H03-s2001, H-H04-s2001, H-H06-s2001, H-H08-s2001, H-H09-s2001, H-H10-s2001, H-H12-s2001, H-H01-s2002, H-H02-s2002, H-H03-s2002, H-H04-s2002, H-H06-s2002, H-H08-s2002, H-H09-s2002, H-H10-s2002, H-H12-s2002
- heldout_configs.csv soft_clean flag vs observed runs agree: True
- N- and H- run params match nominations.csv and heldout_configs.csv on all 7 params (checked separately: 0 mismatches)
- soft_clean reasons are not stored in runs.csv beyond the boolean; frac_* columns exist but the criterion is not re-derived here.

### Analyst scoring of logged predictions (Fable)
Pre-registration item 1 (held-out ranking): PARTIAL. Predicted law clearly ahead on raw Pyr-Int and Int-Int Spearman (0.65-0.75 vs 0.45-0.55) and on J. Observed on 12 config means: Pyr-Int 0.85 vs 0.74 (law ahead, smaller gap, both higher than predicted); Int-Int 0.79 vs 0.81 (no lead: MISS); J 0.81 vs 0.79 (tie: MISS). Int-Pyr gap predicted <0.1, observed 0.25 in the law's favour (MISS, wrong in the conservative direction); conns2 gap 0.08 (HIT). No bootstrap 90% interval for the Spearman difference excludes zero with 12 configs. The law's solid advantage is calibration, not ranking: R2 0.55/0.55 vs -0.12/-0.34 on Pyr-Int/Int-Pyr, J mean abs error 0.17 vs 0.25. Coverage predicted 0.6-0.75 for both: law 0.83-1.0 (MISS, intervals not too narrow), forest 0.75-1.0 (edge). Failed reasoning step: I carried the offline cross-validation gap (same seed for every sample) over to new seeds; with a seed-to-seed rank correlation of only 0.32 for Int-Int and 0.64 for Pyr-Int, no predictor can separate there with 12 configs.
Pre-registration item 7 (nominations): seed CV 0.12-0.25 MISS (observed 0.2-0.6 on Pyr-Int and Int-Int; corrected before queue 3). T1 hit rate law >=7/9: 6/9 (narrow MISS); forest >=5/9: 1/9 (MISS); T2 <5/9 both: 3/9 and 0/9 (HIT).
Pre-registration item 8: no timeout (HIT); duration 550-700 s (MISS, server 1.35x slower than the timing model, max 1.99x).
Nomination predictions logged before queue 3: (1) mean J of law nominations 1.3 (1.1-1.5): 1.19 HIT. (2) T1 law 6/9 (5-8): 6/9 HIT; forest 4/9 (2-6): 1/9 MISS; T2 law 3/9 (1-5): 3/9 HIT; forest <=1/9: 0/9 HIT. (3) law mean J higher by 15-35%: observed 68% (1.19 vs 0.71), direction HIT, size MISS. (4) seed CV Pyr-Int and Int-Int 0.4-0.6: observed 0.21-0.63 and 0.10-0.61, PARTIAL; Int-Pyr and conns2 0.1-0.2: observed 0.04-0.12 and 0.06-0.22, PARTIAL. (5) J limited by Pyr-Int or Int-Int in all but <=2 runs: 16/18 HIT.
Arm self-assessment: each arm predicted J for all six nominated configs. Forest: rank correlation with observed -0.66 (it ranked its own three above the law's; observed is the reverse), mean abs error 0.47. Law: rank correlation +0.89, mean abs error 0.51, all six over-predicted (bias +0.51). Both arms over-predict J: J is a minimum of four noisy components, and the nominated configs were picked for high single-seed scores (regression to the mean: M1 1.76 -> 1.42, M7 1.72 -> 1.27, M9 1.51 -> 0.88 on three new seeds).
Caveats: one comparison, 9 runs per arm on 3 shared seeds and 3 configs per arm, so the 1.19 vs 0.71 difference is suggestive (roughly 2 standard errors), not established. No config reaches T2 on its three-seed mean; M1 (1.42) and M7 (1.27) reach T1 on the mean, no forest nomination does (best 0.96). The law arm's edge in the search came mostly from one decision the forest did not make: go to the size cap (70/30) and dm.weight 1.0. 18 of 24 held-out runs are not soft-clean by design (held-out configs were drawn over the full hard limits).
