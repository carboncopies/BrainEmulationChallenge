# R3 robustness on S1: seeds and K (own NES 8000/7999/8001)

Recipe R3 used unchanged everywhere (cue T=16.5 nS = 4.125/pair, loop cap 8 nS, Pyr->Int weight 1, background min(0.2 g, c) with c = 0 or 0.15 nS, Int->* untouched, all Pyr->Pyr/Pyr->Int pairs programmed, Dt 1 ms, apply-then-run in one session).
No recipe value needed adjusting. Scripts: grow_seed.py (same as dendrite_rerun/grow_dend.py S1, only seed differs), rdesign.py (design + pair export, any network), rrun.py (runner), run_part1.sh, run_part2.sh, analyze.py, status.py. Data: raw/, summary.json, designs/, pairs/, logs/.
Design: rdesign.py annealing, 4 cue + 4 non-cue per memory, every cue->non-cue pair >= 4.5 nS (held for every design; no relaxation used), objective = own closed-loop inhibition. Its network drivable-interneuron count reproduces the memo's 7 for seed 628 (102,117,129,134,135,138,142).
Growth: seeds 20240629 / 20240630 completed (66 / 63 min), models v2-arbor-S1-seed6290000 / v2-arbor-S1-seed6300000 (the generator appends 0000).

## Results (all runs: complete = non-cue fired 4/4 for every cued memory)
| network | design | drivable ints (cap-aware, network / used by memories) | single 4/4 + 3-cell never completes (c0, c0.15) | ripple 12/16/20 + shuffled 16 (c0.15), c0 at 12 | SG control (12 ms) |
|---|---|---|---|---|---|
| seed 629 | K=4 | 3 (109,126,142) / 0 | pass, pass | all pass; last spike 40.1/52.3/64.4/52.2 ms; c0 40.5 | identical to GABA on |
| seed 630 | K=4 | 4 (100,127,130,138) / 1 (138) | pass, pass | all pass; 40.1/52.2/64.3/52.2; c0 40.5 | identical |
| seed 628 (S10000), new K=4 groups | K=4 | 7 | single pass | 12 ms pass, last 40.2 ms | - |
| seed 628 | K=5 | 7 | pass (c0.15) | 12 ms pass, last 52.6 ms | - |
| seed 628 | K=6 | 7 | pass (c0.15) | 12 ms pass, last 64.1 ms | - |

Per memory: 8 member spikes (one volley), burst end 4.1-4.5 ms after its cue (c0 and c0.15, all cases), so all bursts end far inside 40 ms. Pyramidal spikes: 32 (K=4), 40 (K=5), 48 (K=6) = 8 per memory, i.e. only members, once each. Cross-talk 0, spurious non-member pyramidal spikes 0, every run. 3-cell cues: 0 false completions in every single run (K=4 per seed: 8 cues; K=5: 10; K=6: 12). Inside a ripple (K=5, K=6, memory 2 given a 3-cell cue): that memory 0/4, 3 member spikes, the other memories unaffected (K=6 last spike 64.1 ms).
Interneurons: seed 629 none fired at all (no memory drives a drivable interneuron); seed 630 one spike per event from int 138 in 2 memories; S10000 K=5 0-2 per memory. Inhibition is not functional, as the memo stated. SG control (all GABA pairs zeroed, readback gaba_nonzero_after = 0) gives spike-for-spike identical output.
Readback: 0 weight mismatches, 0 NMDA left, in all 24 sims.
## Failures
None. Not tested: Dt 0.1 on the new seeds; 3-cell cue inside a ripple on seeds 629/630 (single-run 3-cell tests pass); K>6; background above 0.15; designs are one annealing result per case, not an optimum.
## Housekeeping
24 sims created (ids 185,187,188,191,192,194,197,198 and 249-264), each deleted by DeleteResidentByID in the script; GetStatus on all 24 returns StatusCode 2 (not found). Growth sims deleted by the generator. Shared server not used; other sims untouched.
