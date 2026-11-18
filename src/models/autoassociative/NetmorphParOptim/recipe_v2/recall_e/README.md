# recall_e: capacity and recall on the E4 networks (V1, 20 interneurons, D_int 0.03, pyramidal D 0.0175), 2026-11-17
**Outside the original rule.** inhib_f/PREREGISTRATION.md said the recall protocol would run only if a configuration passed all seven bars on 3 of 3 seeds. E4 passed on 2 of 3 (seed 16180 in inhib_e and 27182 pass; seed 31415 misses Int->Pyr per pair by 0.003, 3.9967 vs 4). John asked on 2026-11-17 for the recall check anyway, so this is a requested exception: it does not show that E4 meets the preregistered condition. Files: PREREGISTRATION.md (written before the packing and any sim, not edited), feas2.py (identical to capacity_d/feas2.py, diff checked), feas_E4_*.json/log, groups_*.json, dyn2.py (capacity_d/dyn2.py with only paths, model names `v2-ihe-` (seed 16180) / `v2-ihf-` (27182, 31415), N 116 and sim name changed), run_dyn.sh, summarize.py, raw_*.json (24), log_*.txt.
Patched instance only (NES 8011 / API 8010); main NES/API untouched; 24 of 24 sims loaded_ok (116 neurons, all pairs programmed, 0 mismatches), every sim deleted (no Traceback / DELETE FAILED); no git, no email, no NES code change.

## 1. Capacity (offline packing, exact enumeration, same method and 300 tries as capacity_d)
| network | Pyr->Pyr synapses | p | pairs >= 4.125 nS | cells with >= 4 strong inputs | max 4+4 memories | max 4+2 memories |
|---|---|---|---|---|---|---|
| E4 s16180 | 4,158 | 0.236 | 148 | 6 | 0 | 2 |
| E4 s27182 | 5,443 | 0.254 | 238 | 12 | 1 | 4 |
| E4 s31415 | 5,350 | 0.282 | 223 | 9 | 1 | 3 |
| V1n30 D 0.0175 (3 seeds, capacity_d) | 4,548-5,545 | 0.24-0.31 | 194-195 | 8-9 | 1 | 3 |
So E4 holds the same as V1n30 on seeds 27182 and 31415 (1 big, 3-4 small; 4 small on 27182, one more than V1n30) and less on seed 16180 (no 4+4 memory, 2 small): capacity in this family still follows the strong-pair count (148 -> 0/2, 223-238 -> 1/3-4).

## 2. Recall (dynamics_c criterion; GABA on = x1 as grown; seeds 16180 and 27182; seed 31415 packed but not simulated)
Memories ok / memories (ok = full cue completes all non-cue cells, both 3-cell cues silent, nothing else fires); spurious = non-member Pyr spikes over the run; interneuron spikes over the run. 3-cell false completions: 0 in all 24 runs; last non-cue spike 4.52 ms in every clean run.
| net | design | c = 0, 0.15, 1.5 (on / silenced) | c = 3.0 on: ok; spurious; Int spikes | c = 3.0 silenced: ok; spurious; Int spikes |
|---|---|---|---|---|
| s16180 | 2 x (4+2) | 2/2 and 2/2 at every c (Int spikes 7 / 9) | 0/2; 0; 9 | 0/2; 2; 16 |
| s27182 | 4 x (4+2) | 4/4 and 4/4 (13 / 15) | 0/4; 231; 129 | 0/4; 671; 313 |
| s27182 | 1 x (4+4) | 1/1 and 1/1 (6 / 6) | 0/1; 150; 52 | 0/1; 213; 74 |
Runaway (> 50 spurious non-member Pyr spikes): none at c <= 1.5 in any run. At c = 3.0: s27182 runs away in all four (on: 231 and 150; silenced: 671 and 213). s16180 does not (0 and 2 spurious spikes) but fails the strict criterion through cross-talk (a member of the other memory fires, 1-2 cells, in both on and silenced runs); onset on s16180 is above 3.0.
**Verdict.** Recall works for every memory that fits (7 of 7: 2 + 4 + 1) at c 0, 0.15 and 1.5 with and without GABA, with perfect 3-cell selectivity. The runaway onset is between 1.5 and 3.0 where it can be resolved (s27182) and above 3.0 on the sparsest seed (16180). Inhibition at x1 does not stop runaway at c = 3.0 on s27182 (it lowers the spurious count by only 1.4-3x), unlike V1n30 D 0.0175, where GABA on stayed near clean (2-3 stray spikes).

## 3. Comparison with V1n30 D 0.0175 (dynamics_c)
| | V1n30 D 0.0175 (30 Int, 10,387 Int->Pyr synapses on s16180) | E4 (20 Int, 3,655-4,416 Int->Pyr synapses) |
|---|---|---|
| capacity | 1 big + 3 small per seed | s16180 0 + 2, s27182 1 + 4, s31415 1 + 3 |
| recall at c <= 1.5 | perfect, on and silenced | perfect, on and silenced |
| silenced runaway at c = 3.0 | 4 of 4 runs (198-533 spurious) | 2 of 3 silenced runs (s27182: 213 and 671 spurious; s16180: 2) |
| GABA on at c = 3.0 | near clean (0-3 stray spikes) | s27182: 231 and 150 spurious (no suppression to speak of); s16180: 0 |
Recall is as good as V1n30 where memories exist; E4 gains nothing in capacity and loses the inhibitory suppression at c = 3.0 (3x fewer Int->Pyr synapses). In exchange E4 meets the interneuron-fraction band (A 40.7-46.8%, V1n30 65-69%).

## 4. Prediction scoring (HIT inside range; PARTIAL one packing step or 25% beyond; MISS otherwise)
| item | s16180 | s27182 | s31415 |
|---|---|---|---|
| pairs >= 4.125 nS | 148 vs 150 (100-210) HIT | 238 vs 260 (190-340) HIT | 223 vs 250 (180-330) HIT |
| cells with >= 4 strong inputs | 6 vs 6 (4-9) HIT | 12 vs 11 (8-15) HIT | 9 vs 10 (8-14) HIT |
| max 4+4 | 0 vs 0 (0-1) HIT | 1 vs 1 (0-2) HIT | 1 vs 1 (0-2) HIT |
| max 4+2 | 2 vs 2 (1-3) HIT | 4 vs 3 (2-4) HIT | 3 vs 3 (2-4) HIT |
Capacity: 12 of 12 HIT (the pair counts followed the square-of-synapses scaling). R6 (E4 no more than V1n30 on s16180: 0-1 big, 2-3 small): HIT (0, 2).
R1 (all memories recall at c 0, 0.15, 1.5, on and silenced; 3-cell cues never complete): HIT. R2 (silenced runaway at 3.0 in every run, 85%): MISS (2 of 3 silenced runs); (GABA-on runaway at 3.0 in at least one run, 65%): HIT (s27182). R3 (silenced onset between 1.5 and 3.0, 70%): PARTIAL (true on s27182, above 3.0 on s16180). R4 (no inhibitory veto at c <= 1.5): HIT. R5 (overall recall works at c <= 1.5 for every memory that fits): HIT.

## 5. Honest limits
- Packings are single exact enumerations with 300 random restarts; the group designs are the first packing found; one network per seed. Seed 31415 was packed but not simulated (as asked: 16180 and 27182 only).
- Background c is an imposed per-pair cap; the grid (0, 0.15, 1.5, 3.0) only brackets onset (between 1.5 and 3.0, or above 3.0). Sparse seed 16180 never reached runaway.
- The weaker inhibition at c = 3.0 is attributed to the 3x lower Int->Pyr synapse count (inference, consistent with the numbers, not isolated by an experiment).
- This check does not retroactively make E4 satisfy the preregistered 3-of-3 bar rule; E4 misses bar 3 on seed 31415 by 0.003 and its seed 27182 pass has drivable exactly 7 of 20 with 4 zero-input interneurons.
- Memories are the small R3 designs only (no ripple/overlap tests; the largest design is a single 4+4 memory).
