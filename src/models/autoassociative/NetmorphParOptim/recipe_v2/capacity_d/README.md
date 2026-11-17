# capacity_d: memory capacity vs Pyr->Pyr connection probability (pyramidal D_synmax) , 2026-11-17
Question: how many R3 memories (every cue->noncue pair >= 4.125 nS, i.e. >= 5 synapses) fit as pyramidal D rises 0.0175 -> 0.035 -> 0.05, and what does it cost? Files: PREREGISTRATION.md (written before the D 0.035/0.05 networks were grown, unedited), feas2.py (packing, same method as dynamics_c/feas.py: 300 random-restart greedy packings; capped/sampled where noted), feas_*.json/log (all networks), thresh.py/thresh_results.json (thresholding model), grow_pv.py (copy of linefix_c/grow_pv_s2.py, only HERE and model prefix changed; diff checked), analyze_pv.py + pv_results.json (4 new networks), dyn2.py + queue (recall protocol of dynamics_c + ripple mode), raw_*.json (38 sims), summary.json.
Patched instance (NES 8011 / API 8010, line-379 fix); main NES/API untouched. All 4 growths rc 0, bio_check pass, D_synmax read back; all 38 recall sims deleted (no Traceback / DELETE FAILED in any log). No git, no email, no code changes in NES.

## 1. Capacity curve (offline packing). "4+4" = max disjoint 8-cell memories, "4+2" = max disjoint 6-cell memories
`LB` = candidate list built by random cue-set sampling (cap 240,000 candidates), so a lower bound. Unmarked = full enumeration (same as dynamics_c). Pairs >= 4.125 nS counted from the dumps' g_peak_sum (0.98 nS per synapse).
| network | Int | pyr D | Pyr->Pyr p | syn/pair | pairs >= 4.125 nS | cells with >= 4 strong inputs | max 4+4 | max 4+2 |
|---|---|---|---|---|---|---|---|---|
| V1 s16180 (linefix_c B2) | 48 | 0.01 | 0.184 | 1.47 | 30 | 2 | 0 | 0 |
| V1n30 (linefix_c, 3 seeds) | 30 | 0.0175 | 0.24-0.31 | 1.97-2.07 | 194-195 | 8-9 | 1 (all 3 seeds) | 3 (all 3) |
| V1 s16180 (linefix_c B1) | 48 | 0.021 | 0.288 | 1.91 | 170 | 8 | 0 | 3 |
| **V1n30 s16180 (new)** | 30 | 0.035 | 0.346 | 2.95 | 577 | 21 | 3 LB | 6 LB |
| **V1n30 s27182 (new)** | 30 | 0.035 | 0.356 | 2.99 | 647 | 18 | 3 LB | 6 LB |
| V1 s16180 (linefix_c B3) | 48 | 0.05 | 0.439 | 2.96 | 711 | 26 | 3 LB | 6 LB |
| **V1n30 s16180 (new)** | 30 | 0.05 | 0.442 | 3.61 | 975 | 29 | 4 LB | 9 LB |
| **V1n30 s27182 (new)** | 30 | 0.05 | 0.415 | 3.67 | 956 | 25 | 4 LB | 8 LB |
| D 1.5 (linefix, linefix_b; 9 networks S1/V1/V3, 3 seeds, 2 V1n30) | 30-48 | 1.5 | 0.76-0.88 | ~9-11 | 5,100-6,600 | 71-86 | 11 LB (of 12 possible) | 15-16 LB (of 16) |
Thresholded-model check (thresh.py, V1 B3 at lower D): 0.035 gives 2 / 5 memories, 0.05 gives 3 / 6; the real V1n30 networks hold 1 more memory of each kind than the 48-Int thresholded ones (V1n30 pyramids have about 2x the strong pairs at D 0.0175, 194 vs 98).
Capacity roughly follows the number of strong pairs: 1 -> 3 -> 4 memories of 4+4 for 194 -> ~600 -> ~960 strong pairs. D 1.5 saturates the 96 cells.

## 2. Recall (dynamics_c protocol and criterion; groups from the packing; one network per D, seed 16180: D 0.035 and D 0.05; D 0.0175 reference from dynamics_c)
Memories ok / memories (ok = full cue completes, both 3-cell cues silent, nothing else fires). 3-cell false completions: 0 in all 32 single runs.
| network | design | c 0 / 0.15 / 1.5 GABA on | same, GABA silenced | c = 3.0 GABA on (ok; spurious Pyr spikes) | c = 3.0 silenced (ok; spurious) |
|---|---|---|---|---|---|
| D 0.0175 (dynamics_c, s16180) | 1x(4+4) / 3x(4+2) | 1/1, 3/3 | 1/1, 3/3 | 0/1 (2), 2/3 (0) | 0/1 (230), 0/3 (198) |
| D 0.035 | 3x(4+4) | 3/3 | 3/3 | 0/3 (444) | 0/3 (1,379) |
| D 0.035 | 6x(4+2) | 6/6 | 6/6 | 0/6 (777) | 0/6 (2,446) |
| D 0.05 | 4x(4+4) | 4/4 | 4/4 | 0/4 (1,238) | 0/4 (2,692; 3 of 4 full cues complete) |
| D 0.05 | 9x(4+2) | 9/9 | 9/9 | 0/9 (1,893) | 1/9 (3,102; 6 of 9 complete) |
Last non-cue spike 4.52 ms in all clean runs; interneuron spikes in the whole run 17-32 (on) vs 23-44 (silenced).
Runaway onset (spurious Pyr spikes > 50): between c = 1.5 and 3.0 in all four D 0.035/0.05 designs, for GABA on and silenced (c = 1.5 clean everywhere). At D 0.0175, GABA on did not run away at 3.0 (2-3 stray spikes). So the extra synapses remove the inhibition benefit seen at D 0.0175 at c = 3.0, but inhibition still halves-to-thirds the spurious spike count (444 vs 1,379, 1,893 vs 3,102) at that point.
4-memory ripple on D 0.05 (4+4 x4, c 0.15; cues 12 or 16 ms apart, 150 ms run; success = all four complete, no cross-talk, no spurious spikes, activity ends before 100 ms): order 0123 at 16 ms: GABA on and silenced both succeed; shuffled 2031 at 16 ms: both succeed; order 0123 at 12 ms: GABA silenced succeeds, **GABA on fails (memory 1 completes only 1 of 4 non-cue cells: inhibition vetoes it)**. This ripple ran on a single 4-memory design, so it tests the same 12 ms veto as option_B_scaled s7 (S1), not overlap. The overlap protocol (shared cells, 37.5%) was not run: the 4 memories are disjoint packings, building overlapped designs would need a separate search.

## 3. Prediction scoring (PREREGISTRATION.md; both seeds scored; HIT inside range, PARTIAL up to 25% beyond the edge)
| item | D 0.035 | D 0.05 |
|---|---|---|
| connection probability | 0.346 / 0.356 vs 0.36 (0.32-0.42) HIT | 0.442 / 0.415 vs 0.43 (0.38-0.48) HIT |
| syn per connected pair | 2.95 / 2.99 vs 2.45 (2.2-2.8) PARTIAL (5-7% above range) | 3.61 / 3.67 vs 2.95 (2.6-3.3) PARTIAL (9-11% above) |
| Pyr->Pyr synapses | 9,305 / 9,704 vs 8,400 (7,000-10,000) HIT | 14,536 / 13,890 vs 11,500 (9,500-14,000) PARTIAL / HIT |
| pairs >= 4.125 nS | 577 / 647 vs 650 (450-850) HIT | 975 / 956 vs 1,100 (700-1,400) HIT |
| cells with >= 4 strong inputs | 21 / 18 vs 20 (14-26) HIT | 29 / 25 vs 30 (22-40) HIT |
| max disjoint 4+4 | 3 / 3 vs 3 (2-3) HIT | 4 / 4 vs 4 (3-5) HIT |
| max disjoint 4+2 | 6 / 6 vs 5 (4-6) HIT | 9 / 8 vs 7 (5-8) PARTIAL / HIT |
| arbors equal to the D 0.0175 run of the same seed | s16180 equal (HIT); s27182 differs (-0.45% interneuron axon) MISS | s16180 differs (+0.3%) MISS; s27182 differs (same as its D 0.035 run) MISS |
| Int->Pyr, Pyr->Int, Int->Int unchanged within 3% | s16180: +0.9 / +2.9 / -1.4% HIT; s27182 +8 / +7 / ... MISS (arbor differs) | s16180 +6.6 / +6.8% MISS; s27182 MISS |
| bar probability 0.1-0.3 FAIL, per pair 1.9-4.5 pass | HIT, HIT | HIT, HIT |
| D1 all built memories recall at c 0, 0.15 (on and silenced) | HIT (3+6 memories at D 0.035, 4+9 at D 0.05, all ok) | HIT |
| D2 runaway onset (silenced) 1.5-3.0 at D 0.035; <= 1.5 at D 0.05; GABA on suppresses at 3.0 at D 0.035 but not at D 0.05 | silenced onset HIT; GABA-on suppression MISS (444-777 spurious) | silenced onset <= 1.5 MISS (clean at 1.5); GABA-on not suppressing HIT |
| D3 4-memory ripple applicable at D 0.05 | - | HIT (4 disjoint 4+4 memories; ripple run; overlap not) |
Arbor reproduction: same seed and parameters except pyramidal D reproduced the arbor exactly in 1 of 4 cases against the D 0.0175 runs (s16180 D 0.035); s27182 D 0.035 and D 0.05 agree with each other to 8 digits but not with the D 0.0175 run (so the D 0.0175 s27182 run was the odd realisation, as for linefix_b V1 s27182). Count comparisons against D 0.0175 for s27182 are therefore not clean; the clean comparison is s16180 D 0.035.

## 4. Trade-off
- Capacity gained: 4+4 memories 1 -> 3 (D 0.035) -> 4 (D 0.05); 4+2 memories 3 -> 6 -> 8-9. All of them recall perfectly at c <= 1.5 with and without GABA; the 3-cell selectivity holds.
- Bars from linefix_c that fail: probability band 0.1-0.3 fails at D 0.035 (0.35) and D 0.05 (0.42-0.44); the per-pair band 1.9-4.5 still passes (2.95-3.67). Passing: Int->Pyr per pair 5.95-6.76 (bar 4-9), Pyr->Int 3.5-4.0 (bar 1.5-4.5), drivable 8-cell 15-17 of 30 (bar >= 10), bio ranges. Inhibitory fraction A falls from 65-69% to 40-53% (still far above the biological range; reported only).
- Dynamics cost: runaway no longer suppressed by GABA at c = 3.0, and at D 0.05 the 12 ms ripple is vetoed by inhibition for one memory (GABA on only).
- Net: even 4 memories of 8 cells needs p ~ 0.42, outside the band; D 0.035 (p 0.35) gives 3 and fails the band by 0.05. No pyramidal D inside the band (p <= 0.3) has been shown to hold more than 1 memory of 4+4 (D 0.0175 and 0.021: 1 and 0). A memory count in the earlier option_B/S1 sense (K = 4 with overlap) needs about D 0.05.
## 5. Caveats
- Packings of the new networks are sampled lower bounds (random restarts, capped candidates), 300 tries, one fixed seed; counts near the cap may be higher. D 0.0175 values are exact enumeration.
- Recall run on seed 16180 only (D 0.035 same arbor as D 0.0175; D 0.05 arbor 0.3% different); seed 27182 networks have packings but no recall runs. One group design per condition, NES deterministic.
- Background c is an imposed per-pair cap (as in option_B); runaway onset is resolved only between 1.5 and 3.0. Ripple: one design, 6 sims; overlap/crosstalk with shared cells not tested.
- Drivable/inhibition numbers from the dump proxy as in linefix_c, no dynamic simulation of the full network.
