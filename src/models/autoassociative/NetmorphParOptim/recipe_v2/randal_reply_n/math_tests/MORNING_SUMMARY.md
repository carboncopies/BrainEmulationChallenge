# MORNING SUMMARY (final; phase 1 written 07:30, phase 2 added 2026-11-25 after the sims)

## Status
- Phase 1 (10 candidates, offline) and Phase 2 (12 sims) are both finished. Files: PREREGISTRATION_P1/P2.md, PHASE1_RESULTS.md, PHASE2_RESULTS.md, DEVIATIONS.md (D1-D12).
- Phase 2 started only after fable-knobs' batch ended (gate opened 08:36); an early start on my own judgement was refused by the permission system and I did not work around it.
- Nothing touched: main NES 3156209 / API 1972355, fable-knobs' instances, no git, no emails, no uploads.

## Ranking of the 10 candidates by what they delivered (phase 1; details in PHASE1_RESULTS.md)
1. **C3 spectral design**: for any weights, completion from m of 17 cues needs rho >= 16 T_eff / m; T_eff (completion threshold in rho units) is 12.8-13.7 nS, not 16.5. A cascade-minimal search gives rho 16.3-16.6 for 75% cues (the window that works in simulation) but 20.4-21.3 for 50% cues, against ignition at rho 16.5-17.4. **A 50%-cue window does not exist for weights alone, by 20-25% of rho.** rho separates stored termination (AUC 0.92 pooled, 1.0 per model) but the ceiling differs by model (16.5 vs 17.1).
2. **C7 per-member polytope under 50% cues**: with the grown pair ceilings, 2-6 of 17 members cannot complete from a worst-case 75% cue even without the input cap; only 3-5 members can complete from 50% cues. Supports C3 independently.
3. **C6 worst-case slack ranking**: ranking members by the sum of their 13 smallest in-weights puts 5 of the 6 known failing members in its lowest five, including the hub cell the failure list missed. It is an a-priori boost rule (design W13).
4. **C2 exact packing**: proved the repo's packer exact on s55555 and s66666 (K42 = 2, 3). The exact formulation did not scale to the other 8 graphs in the time box (machine load 250-570), so the "exact = greedy on >= 8 of 10" rule is undecided.
5. **C10 reduced-model search**: reproduces the stored 75% results; the search found no 50%-completing design that ends and overfit its training cues (held-out worse than start). Free validator.
6. C1 per-cell LP and volume (hubs and the cap decide; binding cells are high-in-degree cells, opposite to the prediction; 4 zero-volume cells per graph coincide with known failing members). 7. C5 surrogate (proxies predict arm-level K42, Spearman 0.89; not within an arm). 8. C9 BO budget (noise is not the blocker; ~90 growths is). 9. C8 LP packing bound (weak). 10. C4 percolation (no spread at as-grown weights; nothing to predict).
- Exploratory C11 (not preregistered): in the reduced model, no E20-type design with any literature neuron lever (reset, sAHP up to 3/6 nS) combines 75% completion with ending within 100 ms and 50% completion with ending: same trade-off as the simulator arms.

## Phase 2 (simulations, finished 10:11): what the top methods gave
12 sims (6 designs x s66666/s77777, new cues, patched NES, j0), 0 failures. Full table in PHASE2_RESULTS.md.
- **No design completes 50% cues and ends within 100 ms.** The 10 non-E20 designs complete 0/6 50% cues. E20 (rho 20.5, C3 50%-cue design) completes 6/6 and 5/6 but ignites: 0 of 25 events end within 100 ms (median last spike 327-388 ms), 25% cues recruit, 12-13/27 events have non-member spikes. The Phase-1 prediction (no weights-only window) holds in simulation.
- **75% + ends <=100 ms + silence** (PASS75): BASE s66666 6/6, CASC 5/6 on both models, RN s66666 5/6; failing: BASE s77777 4/6, W13 4/6 both, LPS 4/6 and 3/6, RN s77777 3/6. Math designs did not beat the stored E16.5 + boost recipe; CASC (C3) matches it and is the only one passing on both models.
- Input cap 49.5 nS: met only by RN s66666 (49.46). Others have 1-7 members above it (s77777 hub cell 3 at 57-64 nS). Per-pair <= 5.88 nS (cap 6.86), NMDA r 1.0, GABA x1.
- Reduced model rn.py agreed within 1 event in 10/12 (75%) and 12/12 (50%) runs.
- Prediction scoring: P2, P3, P6, P8 hit; P1 and P5 missed (see PHASE2_RESULTS.md).

## Honest answer
**75% cues: yes, partly.** The 75% + ending <=100 ms + silence behaviour is reproducible (4 of 10 runs pass the 5/6 bar, all with 0 non-member events), but not reliably, not better than the stored recipe, and the input cap is not met except in one run. **50% cues: no.** None of the 12 designs gave 50% completion with termination; the only designs that complete 50% cues ignite. Combined with Phase 1 (C3: needs rho ~20.5 vs ignition ~16.5-17.4; C7: 3-5 of 17 members can complete from 50% cues even in the polytope), the weights-only route to the 50% target looks closed for this model class; something beyond weights (a neuron-level or network-level terminator, or a different assembly structure) is needed. Caveats: 6 events per class, one cue draw, two models; differences of 1 event between designs are noise.

## Phase 2 plan (preregistered)
Designs on A17 of s66666 / s77777: BASE (stored recipe), W13 (C6 rule), LPS (C1/C7 max-slack LP), CASC (C3 cascade-minimal rho), RN (C10 search), E20 (C3 50%-target design, expected to ignite). New cue set M2025-, 9 s spacing, r 1.0, GABA x1, original neurons. Predictions P1-P9 are in PREREGISTRATION_P2.md (P2: no design passes the 50% target, 93%).
