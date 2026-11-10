# Netmorph timing ladder (Nov 9 2026, sequential, 1 sample at a time, cap 900 s each)

Samples are rows of batch100_samples.xlsx (all inside hard limits). Run: gen_autonm_labels.py -batchlimit 1, NO -deleteresident (nothing deleted on server).
Files: NetmorphParOptim/ladder/{s*.xlsx,out*.xlsx,out*-rawcounts.json,run*/run.log,ladder.log}; driver: scratchpad/ladder_run.sh.

| # | pyr | int | total | days | minsep | radius | thick | dm.w | wall | conns1 | conns2 | pyr_int | int_pyr | int_int | frac_int_driven | frac_pyr_inh (16 nS) | frac_pyr_inh_w05 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 18 | 31 | 49 | 20 | 11 | 169 | 24 | 0.5 | 95 s | 228 | 45 | 0 | 1 | 3 | 0 | 0 | 0 |
| 1 | 30 | 27 | 57 | 21 | 12 | 141 | 34 | 0.4 | 143 s | 621 | 119 | 0 | 3 | 0 | 0 | 0 | 0 |
| 2 | 67 | 28 | 95 | 24 | 13 | 172 | 48 | 0.8 | 470 s | 2356 | 537 | 7 | 16 | 4 | 0.036 | 0 | 0.030 |
| 3 | 96 | 26 | 122 | 24 | 10 | 155 | 44 | 0.1 | >900 s, HIT CAP (progress bar 99%, ~10 s from done, rate slowing to 9 s/it) | - | - | - | - | - | - | - | - |
| 4 | 125 | 36 | 161 | 20 | 12 | 200 | 26 | 0.6 | NOT RUN (ladder stopped per rule) | | | | | | | | |

Cap handling: timeout -s TERM 900 sent SIGTERM to my own python client at 900 s; verified with ps that no gen_autonm/ladder_run process remains. Sample 3 produced no labels. Sample 4 was not attempted.

## Simulation IDs on NES (needed for cleanup) - NOT RECORDED
My attempt to print the NES simulation ID patched the wrong code path (parallel_batch_test.py; gen_autonm_labels has its own launch code), and the later patch to gen_autonm_labels.py (print NES_SIM_ID in sample_launch_requests) came after sample 3 had started. The client has no list-simulations route, and -deleteresident was not used. So four of my simulations are left resident, IDs unknown, created (server local time, Nov 9, ~07:0x):
- 07:04:51 (18 pyr + 31 int, done)
- 07:06:26 (30 pyr + 27 int, done)
- 07:08:49 (67 pyr + 28 int, done)
- 07:16:39 (96 pyr + 26 int; client killed at 900 s; Netmorph may still be running or have finished server-side)
Plus the two from the aborted batch (~00:21 on Nov 9, 165 and 139 neurons) and the 4 smoke samples were deleted by -deleteresident earlier. Server-side sim names are "Netmorph-autoassociative000N" (modelname from the script). The NES_SIM_ID print is now in gen_autonm_labels.py (uncommitted) so future runs record IDs.

## Findings
- Runtime grows steeply with size: 49 -> 95 neurons took 95 s -> 470 s (about 5x for 2x neurons, also days 20->24); 122 neurons did not finish in 15 min (single run, no concurrency). Per-iteration step time keeps rising late in the run (1 s -> 9 s per progress step), so the cost is super-linear, consistent with the earlier two 139/165-neuron runs not finishing in 9.5 min.
- Aggregate labels: frac_int_driven became non-zero (0.036, 1 of 28 interneurons) and frac_pyr_inhibited_w05 non-zero (0.030) only at 95 neurons / 67 pyr / dm.weight 0.8 and larger/denser volume. At <=57 neurons all aggregates were 0. Strict frac_pyr_inhibited (16 nS) stayed 0 everywhere. Caveat: n=3 completed samples, and dm.weight, radius and thickness (density) are confounded with size.
- Label counts rise with size (conns2 45 -> 119 -> 537).

## Recommendation
- Feasible for ~100 samples: total <= ~100 neurons (pyr <= ~70, int <= ~30), ~2-8 min/sample sequential (avg ~4 min => roughly 6-7 h for 100). Under this range aggregate labels are mostly 0, so frac_int_driven/frac_pyr_inhibited will be sparse and weak as regression targets (consider frac_*_w05, or per-pair counts, or lower thresholds).
- 120+ neurons exceed 15 min each; 100 samples would be >25 h sequential. Only feasible overnight/multi-day with a longer cap, and shared-server load is a concern.
- Suggested next step: re-run sample 3 alone with a 40 min cap to get its true time, and test whether larger interneuron share or higher dm.weight at ~95 neurons pushes the strict aggregates above 0.
