# PHASE 2 RESULTS (12 sims, new cue set M2025-, 9 s spacing, r 1.0, GABA x1, original neurons, scorer = neuron_reset_ahp analyze_d.summ; script p2_score.py -> p2_summary.json)
Gate opened 08:36 (fable-knobs batch ended); 4 waves of 3 sims on my instance j0; all 12 finished, 0 contaminated events, 0 failed runs, j0 RSS peaked 3.1 GB, every sim deleted in p2_run's finally.

| model | design | rho | 75% | 50% | 25% recruit | 1-cell / unrel recruit | median / max last (ms) | stops100 | events w/ non-member | max member input (nS) / members >49.5 | max pair | PASS75 | PASS_T (50% >=3/6) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s66666 | BASE | 16.50 | 6/6 | 0/6 | 0/6 | 0/4, 0/4 | 7.3 / 8.7 | 7/7 | 0/27 | 52.6 / 1 | 3.30 | **yes** | no |
| s77777 | BASE | 16.50 | 4/6 | 0/6 | 0/6 | 0/4, 0/4 | 8.6 / 9.1 | 5/5 | 0/27 | 64.2 / 2 | 4.06 | no | no |
| s66666 | W13 | 16.50 | 4/6 | 0/6 | 0/6 | 0/4, 0/4 | 8.1 / 10.2 | 5/5 | 0/27 | 49.9 / 1 | 3.85 | no | no |
| s77777 | W13 | 16.50 | 4/6 | 0/6 | 0/6 | 0/4, 0/4 | 8.5 / 9.9 | 5/5 | 0/27 | 62.5 / 1 | 5.85 | no | no |
| s66666 | LPS | 15.39 | 4/6 | 0/6 | 0/6 | 0/4, 0/4 | 7.9 / 10.7 | 5/5 | 0/27 | 54.4 / 1 | 4.90 | no | no |
| s77777 | LPS | 15.32 | 3/6 | 0/6 | 0/6 | 0/4, 0/4 | 8.5 / 9.9 | 4/4 | 0/27 | 62.0 / 2 | 4.90 | no | no |
| s66666 | CASC | 16.39 | 5/6 | 0/6 | 0/6 | 0/4, 0/4 | 7.8 / 11.6 | 6/6 | 0/27 | 55.1 / 1 | 4.41 | **yes** | no |
| s77777 | CASC | 16.50 | 5/6 | 0/6 | 0/6 | 0/4, 0/4 | 7.2 / 8.2 | 6/6 | 0/27 | 65.8 / 2 | 5.35 | **yes** | no |
| s66666 | RN | 16.15 | 5/6 | 0/6 | 0/6 | 0/4, 0/4 | 7.0 / 8.2 | 6/6 | 0/27 | **49.5 / 0** | 3.63 | **yes** | no |
| s77777 | RN | 16.88 | 3/6 | 0/6 | 0/6 | 0/4, 0/4 | 9.6 / 11.9 | 4/4 | 0/27 | 58.4 / 1 | 5.88 | no | no |
| s66666 | E20 | 20.45 | 6/6 | **6/6** | 1/6 | 0/4, 0/4 | 327 / 371 | 0/13 | 13/27 | 68.2 / 5 | 5.21 | no | no |
| s77777 | E20 | 20.62 | 6/6 | **5/6** | 2/6 | 0/4, 0/4 | 388 / 416 | 0/12 | 12/27 | 77.1 / 7 | 5.88 | no | no |

Limits: per-pair max 6.86 nS (largest used 5.88), NMDA r <= 1.0, GABA x1: respected. **Input cap 49.5 nS: met only by RN on s66666 (max 49.46)**; every other design has 1-7 members above it (hub cell s77777 #3 at 57-64 nS in all s77777 designs).

## Findings
1. **The 50% target is not met by anything.** The only designs that complete 50% cues (E20, 6/6 and 5/6) do it by igniting: every completing event runs 327-416 ms median, 0 of 25 events end within 100 ms, 25% cues recruit (1-2/6) and 12-13 of 27 events have non-member spikes. All 10 designs at rho 15.3-16.9 complete 0/6 50% cues. This is the Phase-1 C3 prediction (no 50% window for weights alone: 50% completion needs rho ~20.5, ignition starts at ~16.5-17.4), confirmed in simulation on both models.
2. **75% + <=100 ms + silence is reached by 4 of 10 non-E20 runs** (BASE s66666, CASC both, RN s66666), each at 5/6 or 6/6 with every event ending (max last spike 8-12 ms) and 0 non-member events. No method was reliably better than the stored recipe: BASE got 6/6 on s66666 but 4/6 on s77777 (stored held-out cues: 5/6 on both; one 75% event of difference = draw noise at n=6). CASC is the only math design that passes on both models (5/6, 5/6); it equals BASE's mean (5.0 vs 5.0 completions) and is not statistically distinguishable.
3. **W13 (C6 rule) did not improve on BASE** (4/6, 4/6 vs 6/6, 4/6). **LPS (max-slack LP at rho 15.3) under-delivers** (4/6, 3/6): the T_eff=13.6 calibration puts it just below the working window. **RN transfers on one model only** (5/6 and 3/6; reduced-model search overfit as predicted by its held-out result).
4. Misses were the known hubs/weak cells: s77777 cells 3, 58, 65 (hub 3 is over the input cap in every design), s66666 28, 46.
5. Reduced model rn.py: 75% counts within 1 event of the sim in 10/12 runs (largest errors: BASE s77777 pred 6 sim 4; RN s77777 pred 5 sim 3), 50% counts within 1 event in 12/12.

## Prediction scoring (PREREGISTRATION_P2.md)
- P1 (BASE passes PASS75 on both, 45%): MISS (s66666 yes, s77777 4/6).
- P2 (no design passes PASS_T, 93%): HIT.
- P3 (E20 50% >=3/6 on >=1 model 75%; does not end on both 85%; 25% recruits in >=1 event 50%): HIT, HIT, HIT.
- P4 (W13 75% >= BASE on s77777 40%): HIT (4 vs 4; but W13 passes PASS75 on both, 30%: did not happen).
- P5 (LPS <=3/6 on both 60%; never ignites 85%): half: s66666 got 4/6 so the first part failed; no ignition HIT.
- P6 (CASC passes PASS75 on >=1, 35%; RN on >=1, 25%): HIT, HIT.
- P7 (some math design beats BASE strictly on both, 12%): did not happen (consistent with P7's low odds).
- P8: HIT (10/12 and 12/12).
- P9 (non-member spike event in 25%/single/unrelated, 15%): occurred, in E20 only (25% cues recruit in 1 and 2 events; non-member events 13/27, 12/27); in the 10 non-E20 runs 0 events.
