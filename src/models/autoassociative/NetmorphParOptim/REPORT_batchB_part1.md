# Batch B part 1 (samples 1-10 of 100), Nov 9 2026

Sheet: batchB_samples.xlsx (100 rows, Sobol 5-D over days/minsep/radius/thickness/dm.weight, scrambled, best of 300 seeds (seed 54) by lowest max |corr| of size/dm.weight/density; dm.weight rounded to 0.1; size drawn independently then assigned). 70 rows total 80-100, 30 rows total 50-79; pyr 16-70, int 16-30, total <=100. All hard limits asserted. Rows 1-10 = 6 large + 4 small. Column row_source present.
Run: sequential, one at a time, gen_autonm_labels.py -batchlimit 1, 900 s cap, no -deleteresident, nothing deleted. No cap hits; no process left (ps verified). Per-sample files: batchB/ (s*.xlsx, out*.xlsx, run*/run.log, batch.log). Labels: batchB_labels_part1.xlsx (label columns + wall_s, NES_SIM_ID, row_source).

| # | pyr | int | total | days | dm.w | wall s | NES_SIM_ID | conns1 | conns2 | pyr_int | int_pyr | int_int | frac_int_driven | frac_pyr_inh (16nS) | frac_pyr_inh_w05 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 69 | 30 | 99 | 22 | 0.2 | 493 | 22 | 3364 | 240 | 0 | 4 | 1 | 0 | 0 | 0 |
| 2 | 27 | 30 | 57 | 25 | 0.6 | 233 | 23 | 628 | 138 | 3 | 11 | 7 | 0.033 | 0 | 0.074 |
| 3 | 66 | 27 | 93 | 25 | 0.2 | 584 | 24 | 3469 | 330 | 2 | 3 | 1 | 0 | 0 | 0 |
| 4 | 62 | 24 | 86 | 25 | 0.4 | 476 | 25 | 2778 | 459 | 3 | 6 | 1 | 0 | 0 | 0 |
| 5 | 39 | 18 | 57 | 23 | 0.6 | 195 | 26 | 1208 | 350 | 7 | 11 | 2 | 0.056 | 0 | 0.026 |
| 6 | 68 | 27 | 95 | 22 | 0.3 | 448 | 27 | 2606 | 204 | 0 | 4 | 1 | 0 | 0 | 0 |
| 7 | 58 | 19 | 77 | 24 | 0.3 | 314 | 28 | 2748 | 281 | 2 | 2 | 0 | 0 | 0 | 0 |
| 8 | 57 | 29 | 86 | 20 | 0.2 | 262 | 29 | 1940 | 41 | 0 | 5 | 0 | 0 | 0 | 0 |
| 9 | 70 | 27 | 97 | 24 | 0.7 | 476 | 30 | 3358 | 777 | 0 | 12 | 0 | 0 | 0 | 0.043 |
| 10 | 43 | 19 | 62 | 20 | 0.8 | 180 | 31 | 1194 | 403 | 1 | 13 | 1 | 0.053 | 0 | 0.047 |

(conns1/conns2 = usable_conns1/usable_conns2.) Other params per sample are in the labels file.

## Correlation matrix (all 100 rows)
|  | total | dm.weight | density (N/mm3 from radius, thickness) |
|---|---|---|---|
| total | 1 | -0.022 | 0.094 |
| dm.weight | -0.022 | 1 | 0.031 |
| density | 0.094 | 0.031 | 1 |

Also: dm.weight vs pyr -0.002, vs int -0.053; density vs pyr 0.145, vs int -0.103; pyr vs int 0.004. Design is effectively orthogonal. Density ranges widely (about 10k to 77k+/mm3, many rows outside the 10-50k bio warning band, only a warning).

## Non-zero aggregate labels (10 samples)
- frac_int_driven > 0: 3/10 (samples 2, 5, 10). frac_pyr_inhibited_w05 > 0: 4/10 (2, 5, 9, 10). Strict frac_pyr_inhibited (16 nS): 0/10. Any aggregate non-zero: 4/10.
- Non-zero ones are mostly at higher dm.weight (>=0.6) and smaller networks, not the largest (dm.weight 0.2-0.3 large nets give 0). Strict aggregate remains uninformative.

## Timing and projection
Large (80-100, n=6): mean 457 s (range 262-584). Small (50-80, n=4): mean 230 s (180-314). Total for 10 = 3661 s (61 min). Remaining 90 rows (64 large, 26 small): projected 8.9 h (log-linear fit on total) to 9.8 h (class means), about 9-10 h sequential. No cap hits, so a 15 min cap has headroom (max 584 s) at <=100 neurons.

## Recommendation
Continue as is; the cap of 100 total is feasible (max 10 min). No need to trim size. Caveats: the strict 16 nS aggregate is 0 everywhere so use the w05 / frac_int_driven or per-pair counts as targets; expect those aggregates to be non-zero in roughly 30-40% of samples. SIM IDs 22-31 are left resident on the server (sim ids 22-31, none deleted).
