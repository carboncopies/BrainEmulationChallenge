# recall_e PREREGISTRATION (2026-11-17; written before the offline packing of the E4 dumps and before any simulation; not edited after launch)
Outside the original rule: the inhib_f preregistration said the recall protocol would run only if a configuration passed all seven bars on 3 of 3 seeds. E4 (V1, 20 interneurons, D_int 0.03, pyramidal D 0.0175) passed on 2 of 3 (seed 31415 missed Int->Pyr per pair by 0.003: 3.9967 vs 4). John asked on 2026-11-17 to run it anyway, so this is a requested exception, not a result of the preregistered rule.
Networks: E4 seeds 16180 (inhib_e), 27182 and 31415 (inhib_f), patched build. Method: capacity by offline packing exactly as capacity_d/feas2.py (pair threshold 4.125 nS = >= 5 synapses, 300 random-restart packings; sampled candidates if the 4-subset count exceeds 3e6) for 3 seeds; dynamics (dyn2.py copy with paths/models changed only, single-run protocol and `clean` criterion of dynamics_c/capacity_d) on seeds 16180 and 27182: designs = the packed 4+4 memories (if any) and the packed 4+2 memories; background per-pair cap c in {0, 0.15, 1.5, 3.0} nS; GABA on (x1) vs silenced.
## Baseline for comparison
V1n30 D 0.0175 (dynamics_c, linefix_c, 3 seeds): 194-195 pairs >= 4.125 nS, 1 memory 4+4 and 3 memories 4+2 per seed; recall perfect (all clean, 0 false 3-cell completions) at c <= 1.5 on and silenced; runaway silenced at c = 3.0 in 4 of 4, GABA on near-clean at 3.0 (0-3 stray spikes).
## Predictions (central; range)
Strong pairs scale about with the square of the Pyr->Pyr synapse count (capacity_d: 98 -> 430 -> 711 pairs for 4,133 -> 8,394 -> 11,878 synapses). E4 Pyr->Pyr synapses: 4,158 (s16180), 5,443 (s27182), 5,350 (s31415) vs 4,692 for V1n30 s16180 (194 pairs).
| seed | pairs >= 4.125 nS | cells with >= 4 strong inputs | max 4+4 memories | max 4+2 memories |
|---|---|---|---|---|
| 16180 | 150 (100-210) | 6 (4-9) | 0 (0-1) | 2 (1-3) |
| 27182 | 260 (190-340) | 11 (8-15) | 1 (0-2) | 3 (2-4) |
| 31415 | 250 (180-330) | 10 (8-14) | 1 (0-2) | 3 (2-4) |
Dynamics (each built memory):
- R1. All memories recall at c 0, 0.15 and 1.5, GABA on and silenced; 3-cell cues never complete a memory: 85%.
- R2. At c = 3.0 silenced: runaway (> 50 spurious non-member Pyr spikes) in every run: 85%. At c = 3.0 GABA on: runaway in at least one run: 65% (E4 has 20 interneurons and 3,655 Int->Pyr synapses against 10,387 at V1n30, so inhibition is weaker than in dynamics_c where it held).
- R3. Silenced runaway onset between 1.5 and 3.0: 70%; lower onset (<= 1.5): 15%.
- R4. No veto by inhibition (full cue fails with GABA on but completes silenced) at c <= 1.5: 90%.
- R5. Overall recall verdict "recall works at c <= 1.5 for every memory that fits": 80%.
- R6. Capacity ordering: E4 holds no more memories than V1n30 D 0.0175 on seed 16180 (0 or 1 big, 2-3 small): 75%.
Scoring: HIT inside range; PARTIAL one packing step or 25% beyond; MISS otherwise (packing is stochastic, one 300-try run).
