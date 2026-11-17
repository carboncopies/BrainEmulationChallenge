# capacity_d PREREGISTRATION (written 2026-11-17 after Step 1 on EXISTING networks, before any D 0.035 / 0.05 V1n30 network was grown; not edited after launch)
Basis (existing data only): (a) linefix_c Stage 1 B3 (V1, 48 Int, seed 16180, pyr D 0.05) thresholded by stored synapse distance (thresh.py, thresh_results.json). Validation: thresholding B3 at 0.021 gives 4,967 synapses vs 5,019 measured in B1 (-1%), but only 153 vs 170 pairs >= 4.125 nS (-10%, the tail is noisier). Thresholded B3 values (V1, 48 Int): D 0.0175: 4,133 syn, p 0.260, 1.75 syn/pair, 98 pairs >= 4.125 nS; D 0.035: 8,394 syn, p 0.376, 2.45/pair, 430 pairs; D 0.05: 11,878 syn, p 0.439, 2.96/pair, 711 pairs. (b) Actual V1n30 at D 0.0175 (3 seeds): p 0.24-0.31, ~2.0/pair, 194-195 pairs >= 4.125 nS (about 1.9x the thresholded 48-Int network at the same D: cell count changes the pyramidal realisation), packing 1 memory 4+4 and 3 memories 4+2 per seed. Thresholded V1 packing (same method, feas2.py) gives 0 / 2 at 0.0175 (so under-predicts V1n30 by about 1), 2 / 5 at 0.035, 3 / 6 at 0.05 (lower bound: candidate list capped).
Pair counts below assume pair >= 4.125 nS means >= 5 synapses (0.98 nS each).

## Predictions for the new V1n30 networks (interneuron D 0.0495, seeds 16180 and 27182; central value, range in brackets)
| quantity | D 0.035 | D 0.05 |
|---|---|---|
| Pyr->Pyr connection probability | 0.36 (0.32-0.42) | 0.43 (0.38-0.48) |
| syn per connected pair | 2.45 (2.2-2.8) | 2.95 (2.6-3.3) |
| Pyr->Pyr synapses | 8,400 (7,000-10,000) | 11,500 (9,500-14,000) |
| pairs >= 4.125 nS | 650 (450-850) | 1,100 (700-1,400) |
| cells with >= 4 strong inputs | 20 (14-26) | 30 (22-40) |
| max disjoint 4+4 memories (packing, 300 tries) | 3 (2-3) | 4 (3-5) |
| max disjoint 4+2 memories | 5 (4-6) | 7 (5-8) |
| arbor lengths equal to the D 0.0175 run of the same seed (<0.1%) | 3 of 4 seeds-D combinations (60% each) | same |
| ranking-B bars: probability 0.1-0.3 | FAIL | FAIL |
| ranking-B bars: per pair 1.9-4.5 | pass | pass |
| Int->Pyr, Pyr->Int, Int->Int counts | unchanged vs D 0.0175 within 3% (interneuron D is the same) | same |
## Dynamics predictions (dynamics_c protocol, c 0/0.15/1.5/3.0, GABA on vs silenced), on the best new network per D
- D1. Every memory that is built recalls at c 0 and 0.15 with GABA on and silenced (all clean, 0 false 3-cell completions): 80%.
- D2. Runaway with GABA silenced starts at a lower c than at D 0.0175 (between 1.5 and 3.0 there): at D 0.035 onset between 1.5 and 3.0 (60%), at D 0.05 onset <= 1.5 (55%). GABA on suppresses runaway at c = 3.0 at D 0.035 (65%), not at D 0.05 (55%).
- D3. 4-memory ripple/overlap protocol: only attempted if a network has >= 4 disjoint 4+4 memories; I expect that applies only at D 0.05 (50%).
Scoring: HIT within the stated range, PARTIAL just outside (up to 25% beyond the range edge, or one packing step), MISS otherwise.
