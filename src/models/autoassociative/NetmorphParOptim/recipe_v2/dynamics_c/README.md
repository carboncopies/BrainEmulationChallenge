# dynamics_c: autoassociative recall on the sparse line-379-fixed network (2026-11-16)
Question: does R3-recipe recall still work with ~5k Pyr->Pyr synapses (V1n30 from linefix_c Stage 2, seeds 16180 and 27182, 96 Pyr + 30 Int, interneuron connectivity as grown, GABA x1)? Files: PLAN.md, PREREGISTRATION.md (written before any sim, unedited), dyn.py (own driver, patched instance API 8010 only), queue.sh, feas.py/feas.log, groups_*.json, raw_*.json (40 runs), summary.json (summarize.py), log_*.txt.
Verified per run: ModelLoad `loaded_ok` (126 neurons, 3,421 AMPA pairs programmed, 0 missing, 0 g mismatch, 0 readback mismatch), SG runs zero all 2,047 GABA pairs (readback 0 nonzero), sim deleted (log "deleted", StatusCode 0). 40 of 40 completed, no failures. Main NES/API untouched; no code changes, no git, no email.

## 1. The recipe cannot be applied literally (offline, feas.log)
R3 needs every cue->noncue pair >= 4.125 nS grown g_peak_sum (16 pairs per 8-cell memory; weights can only be lowered). Only 194 of 9,120 pyramidal pairs reach it (median pair 0.98 nS). Random-restart packing (300 tries, not exhaustive) finds 1 disjoint 4+4 memory per seed (earlier S1 work: K=4) and 3 disjoint 4+2 memories. Tested designs: DA = 1 memory 4 cue + 4 noncue; DB = 3 memories 4 cue + 2 noncue. The 4-memory ripple and overlap protocols were not run.

## 2. Results (single-run protocol; criterion identical to option_B_scaled; "ok" = memories whose full cue completes and both 3-cell cues stay silent with no other member or non-member Pyr firing)
Columns: memories ok / K; spurious non-member Pyr spikes in whole run; interneuron spikes in whole run (GABA on / SG). 3-cell false completions were 0 in every run.
| seed | design | c (nS) | ok on | ok SG | spurious on / SG | Int spikes on / SG |
|---|---|---|---|---|---|---|
| 16180 | DA | 0, 0.15, 0.6, 1.5 | 1/1 | 1/1 | 0 / 0 | 6 / 8 |
| 16180 | DA | 3.0 | 0/1 | 0/1 | 2 / 230 | 7 / 155 |
| 16180 | DB | 0, 0.15, 0.6, 1.5 | 3/3 | 3/3 | 0 / 0 | 12 / 15 |
| 16180 | DB | 3.0 | 2/3 | 0/3 | 0 / 198 | 12 / 170 |
| 27182 | DA | 0, 0.15, 0.6, 1.5 | 1/1 | 1/1 | 0 / 0 | 10 / 12 |
| 27182 | DA | 3.0 | 0/1 | 0/1 | 2 / 223 | 12 / 184 |
| 27182 | DB | 0, 0.15, 0.6, 1.5 | 3/3 | 3/3 | 0 / 0 | 18 / 24 |
| 27182 | DB | 3.0 | 0/3 | 0/3 | 3 / 533 | 46 / 537 |
Latency of the last non-cue spike after the cue: 4.52 ms in every clean run (SG at 3.0: up to 4.84). Full cue completed all non-cue cells in every run (GABA on and SG, all c). Sustained runaway (200-533 spurious Pyr spikes, 150-540 interneuron spikes) only at c = 3.0 with GABA silenced, 4 of 4; with GABA on at c = 3.0 there were 0-3 stray spikes and cross-talk into other memories (e.g. 3 other-memory members fired in s27182 DB) but no runaway.

## 3. Prediction scoring
- P1 (c 0 and 0.15 on: all 8 memories ok; SG identical): HIT (8/8 at both c, SG identical).
- P2 (last non-cue latency 3.5-5.5 ms; < 10 interneuron spikes per memory trial at c <= 0.15): PARTIAL. Latency HIT (4.52 ms). Interneuron spikes: 6-8 for s16180 DA, but 10 (on) and 12 (SG) for s27182 DA, so one design reached the limit.
- P3 (no SG runaway at c <= 0.6; runaway in >= 1 SG run at c = 3.0): HIT (none up to 1.5; 4 of 4 at 3.0). Onset lies between 1.5 and 3.0, inside my 2.4 estimate.
- P4 (GABA on moves the runaway onset by at most one grid step): MISS in the direction of more suppression: with GABA on no run at c = 3.0 ran away (0-3 spurious spikes vs 198-533), so the onset moved beyond the top of the grid (>= 1 step, not resolved because c > 3.0 was not run).
- P5 (veto at c <= 0.6 in at most 1 of 8 memories): HIT (0 of 8; GABA on never failed to complete a full cue).
- P6 (verdict PASS): HIT, see below.

## 4. Verdict
PASS by the preregistered rule: at c 0 and 0.15 with GABA on, 8 of 8 memories succeed on both seeds with 0 false completions from 3-cell cues. Recall in a network with ~5k Pyr->Pyr synapses (instead of 72-86k) works for the memories that can be built, and it works with no GABA at all up to c = 1.5.
Inhibition has a role only near runaway: at c = 3.0 (about 5x the S1 onset in nS but the sparse network has ~4x fewer pairs) silenced GABA runs away in all 4 runs while GABA on at unscaled x1 strength stays near clean (stray spikes). This differs from S1, where x1 GABA gave no suppression and scaling (x3-x5) was needed; the as-grown interneuron connectivity here (5.9-6.7 syn per Int->Pyr pair, 30 Int) is stronger. At c = 3.0 GABA on does not give clean recall by the strict criterion (2 of 8 memories ok: DB s16180 2/3; DA 0/1 twice; DB s27182 0/3), because of cross-talk and 2-3 stray spikes.

## 5. Caveats
- Memories are smaller and fewer than in the baseline (K=1 at 4+4, K=3 at 4+2); the 4-memory capacity test and the overlap/ripple tests are not done. Capacity on this connectivity is the real open limit (feasibility count), not dynamics.
- Groups are the first packing found, fixed before running; one random design per seed and design. NES is deterministic (Seed 0), so no repeats over sim seeds.
- Background c is an imposed uniform cap on per-pair conductance (min(g, c)), as in option_B; at c <= 1.5 it changes nothing here because 3-cell and full cues behave identically, so this network is not near runaway until c ~ 2-3 (grid is coarse: onset between 1.5 and 3.0; GABA-on onset > 3.0).
- Programmed cue->noncue strengths are the R3 values (T = 16.5 nS), which is the same 'unnatural' programming as before for the Pyr->Pyr pairs; Pyr->Int weight 1 with the 10 nS cue cap as in R3.
- Only 2 seeds of one growth recipe; interneuron count 30 (24%). STDP off.
