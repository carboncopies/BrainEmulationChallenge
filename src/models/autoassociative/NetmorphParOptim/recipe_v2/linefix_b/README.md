# Line-379-fixed build: repeat seeds (Part A) and V1 with 30 interneurons (Part B), 2026-11-15 (ledger tmwidgz1a)
Scripts: grow_pv.py (copy of ../linefix/grow_pv.py; only the path, the added `V1n30` config = V1 with 30 interneurons, and the usage line differ; API port 8010), analyze_pv.py (path and V1n30), measure.py, xdir.py (unchanged), run_queue.sh (8 jobs, xargs -P 3, 40 s start gate), PREREGISTRATION.md (written before any launch, not edited). Data: pv_results.json (8 runs here; seed 16180 Part A runs are in ../linefix/pv_results.json), xdir.log, xdir2.log, analyze.log, analyze2.log, grow_*_fix/.
Patched build: /home/johnjose/BrainGenix/wt/nes-linefix (line 379 `tx/PQ`), separate NES 8011 / API 8010, restarted by me (NES pid 599987, API pid 600788). Main NES/API untouched. D_synmax 1.5 / 0.1 / 0.1 / 0.1 (read back in pv_results.json for all 8 runs), bio_check pass for all 8, rc 0 for all 8, "Deleted resident simulation" in 8 of 8 run.logs, max 3 concurrent. Walls (s): S1 5571 (s31415) / 5583 (s27182); V1 3501 / 3470; V3 4328 / 4131; V1n30 2873 (s16180) / 3387 (s31415).

## 1. All runs (seed 16180 Part A rows are the ../linefix runs; baseline for Part B is linefix V1 s16180)
| variant | seed | n_int | dend len | axon len | reach | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | syn/pair I->P | targets/int | A / B (%) | drivable 8-cell (simple) | zero-in |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | 16180 | 48 | 6629 | 74624 | 143 | 365853 | 11326 | 50982 | 22328 | 14.21 | 74.8 | 12.23 / 16.27 | 33 (38) | 2 |
| S1 | 31415 | 48 | 7114 | 76482 | 135 | 358106 | 16924 | 46365 | 31460 | 15.80 | 61.1 | 11.46 / 17.19 | 24 (30) | 3 |
| S1 | 27182 | 48 | 6864 | 81506 | 138 | 348280 | 16580 | 49908 | 33018 | 14.96 | 69.5 | 12.53 / 18.52 | 29 (36) | 0 |
| V1 | 16180 | 48 | 6733 | 45207 | 145 | 348125 | 15974 | 28484 | 18329 | 8.95 | 66.3 | 7.56 / 11.39 | 31 (35) | 4 |
| V1 | 31415 | 48 | 7045 | 45151 | 136 | 389171 | 12429 | 31409 | 13952 | 10.41 | 62.9 | 7.47 / 10.15 | 28 (32) | 3 |
| V1 | 27182 | 48 | 7119 | 46619 | 136 | 429208 | 17457 | 33652 | 19552 | 10.26 | 68.3 | 7.27 / 10.64 | 33 (37) | 1 |
| V3 | 16180 | 48 | 9405 | 55380 | 141 | 421278 | 17692 | 40440 | 24137 | 12.69 | 66.4 | 8.76 / 12.82 | 39 (41) | 0 |
| V3 | 31415 | 48 | 9281 | 64079 | 137 | 384593 | 15212 | 44110 | 24367 | 14.16 | 64.9 | 10.29 / 14.62 | 30 (37) | 0 |
| V3 | 27182 | 48 | 10100 | 59286 | 137 | 384839 | 29253 | 39513 | 41838 | 12.13 | 67.9 | 9.31 / 16.42 | 34 (41) | 0 |
| V1n30 | 16180 | 30 | 6586 | 46317 | 134 | 391012 | 8058 | 21210 | 5991 | 11.83 | 59.8 | 5.15 / 6.38 | 21 (24) | 1 |
| V1n30 | 31415 | 30 | 6681 | 46234 | 137 | 496464 | 9403 | 23910 | 6233 | 11.56 | 69.0 | 4.59 / 5.62 | 19 (21) | 0 |

## 2. Part A pooled over 3 seeds (16180 linefix + 31415 + 27182), 48 interneurons; SD is sample SD (n=3)
| variant | metric | mean of 3 seeds | SD | range |
|---|---|---|---|---|
| S1 | syn/pair I->P | 14.99 | 0.80 | 14.21-15.80 |
| S1 | targets/int | 68.5 | 6.9 | 61.1-74.8 |
| S1 | A % | 12.07 | 0.55 | 11.46-12.53 |
| S1 | B % | 17.33 | 1.13 | 16.27-18.52 |
| S1 | drivable 8-cell | 28.7 | 4.5 | 24.0-33.0 |
| S1 | drivable simple | 34.7 | 4.2 | 30.0-38.0 |
| S1 | zero-input | 1.7 | 1.5 | 0.0-3.0 |
| S1 | Pyr->Pyr | 357413 | 8807 | 348280-365853 |
| S1 | Int->Pyr | 49085 | 2416 | 46365-50982 |
| V1 | syn/pair I->P | 9.87 | 0.80 | 8.95-10.41 |
| V1 | targets/int | 65.8 | 2.7 | 62.9-68.3 |
| V1 | A % | 7.43 | 0.15 | 7.27-7.56 |
| V1 | B % | 10.73 | 0.62 | 10.15-11.39 |
| V1 | drivable 8-cell | 30.7 | 2.5 | 28.0-33.0 |
| V1 | drivable simple | 34.7 | 2.5 | 32.0-37.0 |
| V1 | zero-input | 2.7 | 1.5 | 1.0-4.0 |
| V1 | Pyr->Pyr | 388835 | 40543 | 348125-429208 |
| V1 | Int->Pyr | 31182 | 2591 | 28484-33652 |
| V3 | syn/pair I->P | 12.99 | 1.05 | 12.13-14.16 |
| V3 | targets/int | 66.4 | 1.5 | 64.9-67.9 |
| V3 | A % | 9.45 | 0.78 | 8.76-10.29 |
| V3 | B % | 14.62 | 1.80 | 12.82-16.42 |
| V3 | drivable 8-cell | 34.3 | 4.5 | 30.0-39.0 |
| V3 | drivable simple | 39.7 | 2.3 | 37.0-41.0 |
| V3 | zero-input | 0.0 | 0.0 | 0.0-0.0 |
| V3 | Pyr->Pyr | 396903 | 21109 | 384593-421278 |
| V3 | Int->Pyr | 41354 | 2431 | 39513-44110 |

Ratios of the new seeds vs their unpatched baselines: Int->Pyr x30.7-33.5, Pyr->Int x26.6-33.5, Int->Int x28.4-32.9, Pyr->Pyr x4.8-5.0 (x5.43 for V1 s27182). Interneuron axon and dendrite lengths ratio 1.0000 in 5 of 6 runs; V1 s27182 differs (axon x0.995, dendrite x1.001) from its baseline. That is the same realisation difference found in ../pv_dsyn015 (V1 s27182 D 0.15 run): the D 0.15 run and this patched run have identical arbors to 8 digits (axon 46,619.5; pyramidal dendrite 23,906.2), so it is the unpatched baseline run of V1 s27182 that is the odd realisation (inference: not reproducible between that run and the later ones; cause not investigated). The x5.43 Pyr->Pyr ratio for that run is partly this effect; its Pyr->Pyr 429k against 389k and 349k for the other V1 seeds is within the seed scatter.

## 3. Direction check (xdir.py; synapse-carrying Int->Pyr axon segments with cos(+x) > 0.9)
New (patched) runs: S1 s31415 4.49% (n 46,365), V1 s31415 4.80% (31,409), V3 s31415 4.97% (44,110), S1 s27182 4.94% (49,908), V1 s27182 4.68% (33,652), V3 s27182 4.89% (39,513), V1n30 s16180 4.83% (21,210), V1n30 s31415 4.56% (23,910). Share among all interneuron axon segments 4.6-5.0%; median cosine -0.02 to 0.03. Unpatched baselines of the same seeds 55.9-60.3% with median cosine 0.92-0.94. So the synapse geometry is isotropic in all 8 runs (measured).

## 4. Part B (V1, 30 interneurons = 24% of cells) against linefix V1 s16180 (48 interneurons) and Part A V1 s31415 (48)
| quantity | V1 s16180, 48 int | V1n30 s16180 | ratio | V1 s31415, 48 int | V1n30 s31415 | ratio |
|---|---|---|---|---|---|---|
| Pyr->Pyr | 348,125 | 391,012 | 1.12 | 389,171 | 496,464 | 1.28 |
| Pyr->Int | 15,974 | 8,058 | 0.50 | 12,429 | 9,403 | 0.76 |
| Int->Pyr | 28,484 | 21,210 | 0.745 | 31,409 | 23,910 | 0.76 |
| Int->Int | 18,329 | 5,991 | 0.33 | 13,952 | 6,233 | 0.45 |
| syn/pair Int->Pyr | 8.95 | 11.83 | | 10.41 | 11.56 | |
| targets/int (of 96) | 66.3 | 59.8 | | 62.9 | 69.0 | |
| inhibitory A / B (%) | 7.56 / 11.39 | 5.15 / 6.38 | | 7.47 / 10.15 | 4.59 / 5.62 | |
| drivable 8-cell (simple) | 31 of 48 (35) | 21 of 30 (24) | | 28 of 48 (32) | 19 of 30 (21) | |
| zero-input interneurons | 4 | 1 | | 3 | 0 | |
Pyr->Pyr per pyramidal cell: 4,073 (s16180), 5,172 (s31415) synapses (bio_ranges info line: 5,000-10,000 per neuron). Measured. In both Part B runs the pyramidal network differs from the 48-interneuron run of the same seed (more Pyr->Pyr synapses by 12% and 28%): the cell count changes the random stream and cell placement. Inference.

## 5. Scored preregistration
Part A, 6 runs x 10 items (Pyr->Pyr, Pyr->Int, Int->Pyr, Int->Int, A, B, syn/pair, targets, drivable, zero-input): 56 HIT, 4 PARTIAL, 0 MISS. Partials: targets per interneuron S1 s31415 61.1 and S1 s27182 69.5 (range 70-81), drivable 8-cell S1 s31415 24 (27-40), V3 s31415 30 (31-44). Count ranges (+-30%) all met; Pyr->Pyr within +-12% in all 6 (V1 s27182 429k vs predicted 388k, +10.6%). Arbors unchanged (ratio 0.99-1.01, reach 0.996-1.009): HIT. +x share 4.4-5.2%: HIT (4.49-4.97%).
Pooled statements: A above the 3-6% band for every variant (S1 12.1, V1 7.4, V3 9.5; predicted about 11.7, 7.7, 9.2): HIT; no V1 run with A <= 6%: HIT (7.3-7.6). Syn/pair pooled: V1 9.9 (predicted about 9) HIT; V3 13.0 (predicted 12.5 and near-11 band 9-13) HIT at the upper edge; S1 15.0 against the stated "near 11 (9-13)" MISS (my pooled sentence contradicted my own per-run S1 value of 14; per-run S1 values 15.8 and 15.0 were inside 12-16.5, HIT).
Part B: s16180: Int->Pyr 21,210 (17,800; 15,500-20,500) PARTIAL; Pyr->Int 8,058 (9,980; 8,700-11,500) PARTIAL; Int->Int 5,991 (7,150; 5,800-8,800) HIT; Pyr->Pyr 391,012 (295-410k) HIT; syn/pair 11.83 (7.5-10.5) PARTIAL (about 13% above); targets 59.8 (58-74) HIT; A 5.15 (4.0-6.0) HIT; B 6.38 (5.3-7.8) HIT; drivable 21 of 30 (15-25) HIT; zero-input 1 HIT; +x 4.83% HIT. s31415: Int->Pyr x0.76 (0.55-0.72) PARTIAL; Pyr->Int x0.76 (0.55-0.72) PARTIAL; Int->Int x0.45 (0.30-0.50) HIT; Pyr->Pyr x1.28 (0.85-1.15) PARTIAL; A 4.59 (3.8-6.2) HIT; drivable 19 of 30 (14-25) HIT; +x 4.56% HIT. The scaling argument (x0.625 for interneuron axon and dendrite counts) over-predicted the drop for Int->Pyr (measured x0.75-0.76): the 30-interneuron networks have denser per-pair contact (syn/pair 11.6-11.8 vs 9.0-10.4), i.e. the pair overlap is not independent of the count.

## 6. Answers
- Inhibitory fraction in the 3-6% band? Part A (48 interneurons): NO in all 9 runs, A = 7.3-12.5% (V1 7.3-7.6, V3 8.8-10.3, S1 11.5-12.5), B = 10.2-18.5%. Part B (30 interneurons): YES for A in both runs (5.15% and 4.59%); B is 6.38% and 5.62% (just above 6% in one run, inside in the other). Measured.
- Synapses per Int->Pyr pair near 11? Part A: V1 8.95-10.41 (slightly below), V3 12.1-14.2 and S1 14.2-15.8 (above). Part B: 11.83 and 11.56, closest to 11 of all configurations. Measured.
- Drivable >= 16 for Part B at 30 interneurons? YES: 21 of 30 (s16180) and 19 of 30 (s31415) on the 8-cell criterion (63-70%; simple count 24 and 21). Part A: 24-39 of 48 (50-81%), also >= 16 everywhere. 8-cell is a summed-conductance proxy, not a dynamic simulation.
- Verdict: of the configurations tried with the fixed build and unchanged biological ranges, V1 with 30 interneurons (24% of cells) is the only one with inhibitory fraction A in 3-6%, synapses per pair about 11, drivable >= 16 and a Pyr->Pyr count of 4,100-5,200 per cell, in two seeds. This is a two-seed result with one cell count and unchanged D_synmax; it does not test dynamics, and the Pyr->Pyr count is 5x the unpatched network (decision for John / Randal, as in ../linefix).
Inference (not tested): fewer interneurons (e.g. 25-35) would move A and B proportionally within the band; the Part B Pyr->Pyr realisation shift (12%, 28%) means comparisons between cell counts carry realisation noise of that size. Limits: 2 seeds for Part B, 3 for Part A; the V1 s27182 unpatched baseline is an odd realisation.

## 7. Housekeeping
No git, no email, nothing outside this folder (plus the LEARNINGS.md entry) written; main NES 3156209 and API 1972355 untouched; max 3 concurrent sims; no background jobs of mine remain. The patched NES (pid 599987) and API (pid 600788) were NOT stopped: at 21:38 another worker (folder ../linefix_c, `run_stage1.sh`) started three runs on that instance (port 8010), so stopping it would have killed their simulations. Whoever owns linefix_c should stop the instance when they finish (restart/stop commands in ../linefix/README.md).
