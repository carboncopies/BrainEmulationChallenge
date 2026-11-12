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
