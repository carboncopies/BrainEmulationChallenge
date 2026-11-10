# Weight-space programming prototype (Phase 2 tune/prune) on a grown Netmorph reservoir

Date: 2026-11-09. Model: Claude Fable 5.1. Nothing committed; /home/johnjose/BrainGenix/BrainEmulationChallenge untouched;
no deletes, no new batches. One server-side modification: weights of OUR resident simulation 127 (validation
sample k=4) were programmed and it was run for 400 ms (section 6). Its g_peak_sum / morphology are unchanged.

## 1. What was built (all in this directory)
| file | purpose |
|---|---|
| `reservoir.py` | loads a viz dump (`batchB/vviz<k>/sample_0000.json`), builds Pyr->Pyr AMPA/NMDA, Pyr->Int AMPA, Int->Pyr GABA, Int->Int GABA matrices (summed g_peak_sum per ordered pair, nS, at weight 1), cell types, soma positions; `matrices_sim127.npz` |
| `engram.py` | assembly-sum engram search (doc B1): greedy growth from every seed + swap local search + exact best 4-cue; joint disjoint selection of K patterns maximizing the minimum margin |
| `program.py` | turns engram designs into `BatchSetPrePostStrength` ops `(pre, post, Conductance_nS)` with weights in [0,1]; validates (AMPA exists, pyramidal pre, Conductance <= g_peak_sum); `scaled_engram_weights` (per-post scaling to the 27.44 nS cue target); offline application incl. the API's NMDA-zeroing side effect |
| `surrogate.py` | explicit conductance-based LIF surrogate mirroring the Netmorph->LIFC converter defaults and the NES receptor rule `g = min(g_peak_sum, w*g_peak_sum*g_norm)`; fAHP/sAHP included; calibration of threshold conductance G* |
| `run_all.py` | driver -> `results.json`, `results.md`, `ops_K{2,3}_*.json` (8 programs) |
| `server_apply.py` | NES client (repo venv + PYTHONPATH): `verify` (read-only compare with dump) and `apply` (ops, cue APs, STDP off, run, spikes, weights-after); refuses sim IDs outside 123-132 |
| `score_server.py` | scores the real NES spikes with the same metrics -> `server_score_K2_scaled_prune.json` |
| outputs | `server_verify_127.json`, `server_apply_127_K2_scaled_prune.json`, `run_all.log` |

Reproduce offline: `$S/venv/bin/python run_all.py` (41 min, dominated by the engram swap search). Server:
`cd $R/src/models/autoassociative && PYTHONPATH=$R/PythonClient $R/venv/bin/python NetmorphParOptim/weight_space/server_apply.py -SimID 127 -dump <dump> -mode verify -out <json>`.

## 2. Reservoir analysis (sim 127 = validation sample k=4: days 25, pyr 67, int 27, minsep 15, radius 124, thickness 42, dm.weight 0.9)
| quantity | doc baseline (nesvbp-autoassociative, 20 d, 32 pyr / 16 int) | sim 127 |
|---|---|---|
| Pyr->Pyr AMPA ordered pairs present | 765/992 (77 %) | 2939/4422 (66 %) |
| mean g_peak_sum over existing pairs | 3.14 nS (3.2 synapses) | 7.55 nS (7.7 synapses) |
| max pair g_peak_sum | 16.66 nS | 124.5 nS (127 synapses) |
| pairs >= 6.86 nS (per-pair criterion) | 58 | 928 |
| pairs >= 27.44 nS | n/a | 121 |
| Pyr->Int AMPA pairs (total) | 5 | 70 (90.2 nS); only 14/27 interneurons receive any input; 3 receive >= 7.84 nS |
| Int->Pyr GABA pairs, max pair | 26, 1.6 nS | 173, 3.2 nS; 45/67 pyramidal receive any GABA; mean 2.6 nS, max 16.8 nS, 1 cell >= 16 nS |
| Int->Int GABA pairs | ? | 29 (26.4 nS) |
| per-receptor g_peak (from dump) | 0.98 AMPA / 0.80 GABA | 0.98 AMPA / 0.80 GABA / 0.55 NMDA (medians, exact) |
| as-built weights | 0.2 uniform | 0.2 uniform (all 6079 connections) |

Sample k=9 (sim 132, 54 pyr / 23 int) for comparison: 1614 pairs, mean 9.6 nS, 482 pairs >= 6.86, 147 >= 27.44, Int->Pyr 108 pairs. Both validation reservoirs are an order of magnitude denser in excitation than the doc's baseline; the inhibitory side improved far less (more Int->Pyr pairs by count, but per-pair strength still 1-3 nS and half of the interneurons disconnected on the input side).

## 3. Engram design (group 8, cue 4, assembly-sum >= 27.44 nS at weight 1)
Margin = max over 4-cues of the minimum conductance a non-cue member receives from the cue.

| K | feasible | margins (nS) | groups (NES neuron IDs) / cues |
|---|---|---|---|
| 1 | yes | 188.2 | [4,18,20,22,29,51,59,63] / [22,29,51,63] |
| 2 | yes | 188.2, 100.9 | + [8,27,33,39,41,42,44,60] / [8,27,33,44] |
| 3 | yes | 188.2, 100.9, 58.8 | + [0,12,17,19,21,37,49,50] / [12,17,19,50] |
| 4 | yes | 188.2, 100.9, 58.8, 38.2 | + [15,16,31,35,36,43,48,64] / [16,36,43,64] |

Doc baseline: P1 30.4 nS (feasible), disjoint P2 17.6 nS (64 %, infeasible). The doc's statement that a second
non-overlapping pattern needs a denser reservoir is confirmed from the other side: our denser validation reservoir
seats 4 disjoint 8-cell patterns with margins 1.4x-6.9x the target (K>=5 not searched). Capacity is no longer the bottleneck.

## 4. Weight programming
Semantics (proven from NES source, `Simulation.cpp:1358-1391`, `LIFCNeuron.cpp:543-559`): `BatchSetPrePostStrength(pre, post, Conductance_nS)`
sets on POST the first AMPA receptor-data from PRE to `weight = Conductance_nS / g_peak_sum` and zeroes every other
receptor-data from PRE (the pair's NMDA). No clamp: the caller must keep `Conductance_nS <= g_peak_sum`. Fails (and stops the
batch mid-way) if PRE has no AMPA onto POST, so GABA pairs are untouchable and missing synapses cannot be created.

Programs (K=2; K=3 analogues also written):
| program | ops | content | designated-cue margin at programmed weights |
|---|---|---|---|
| `w1_prune` | 2939 | 95 engram pairs at weight 1.0; 1206 off-pattern + 109 cross-pattern + 1529 background Pyr->Pyr pairs pruned to 0 | 188.2 / 100.9 nS |
| `scaled_prune` (PRIMARY) | 2939 | engram weights per post scaled so the 4-cue delivers ~27.44 nS and the full group ~48 nS (weights 0.13-1.0); same pruning | 32.3 / 29.8 nS |
| `scaled_bg02` | 1410 | as above but background (non-engram) pairs left at 0.2 | 32.3 / 29.8 |
| `scaled_prune_intdrive1` | 3009 | + all 70 existing Pyr->Int AMPA pairs to weight 1.0 (API-allowed) | 32.3 / 29.8 |
All weights in [0, 1]; every Conductance_nS <= g_peak_sum (asserted). Side effect: 2868 NMDA entries (1114 nS g_peak_sum) on
programmed pairs are zeroed (gap C2).

## 5. Offline surrogate
Assumptions: converter-default LIF (Vrest -70 / Vth -50 / Vreset -55 mV, Rm 100 MOhm, Cm 100 pF, refractory 2 ms), AMPA 0.5/3 ms, GABA 0.5/10 ms, NMDA 2/100 ms with Mg block, fAHP 3 nS (clip 5) 2.5/30 ms, sAHP 1 nS (clip 2) 30/300 ms; uniform 1 ms delay assumed; ADP, adaptive threshold and fatigue omitted; dt 0.1 ms.
Calibration: G* = 13.84 nS (smallest synchronous AMPA volley at weight 1 that fires a resting cell); doc target 27.44 nS = 1.98x G*;
four single synapses (3.92 nS) sub-threshold, consistent with the doc. Full table in `results.md`. Headlines:
- Completion from the 4-cue: 1.00 for every pattern and program (latency 1.4-2.4 ms). As-grown weights (no ops) also complete, but 77 % of non-member pyramidal cells (39/51) and 87.5 % of the other pattern fire too -> pruning is what makes recall specific. With pruning: 0 spurious, 0 cross-pattern (also with background left at 0.2).
- Selectivity is poor: a 2-cell cue still completes 0.67-1.0, because cue margins (even scaled) are ~2x G*. A tighter target (~1.2x G*) would improve it at the cost of robustness.
- Reverberation: in the surrogate every program keeps firing (40-45 spikes/member in 130 ms, members still active after 50 ms), identically with as-built GABA (0.2), no inhibition, or hypothetical GABA weight 1.0, because interneurons never fire (0; 1 with Pyr->Int at weight 1.0). The inhibition the reservoir provides is functionally absent; weights cannot fix it (doc B4 confirmed).

## 6. Real NES run on our sim 127 (`server_apply_127_K2_scaled_prune.json`, `server_score_K2_scaled_prune.json`)
Read-only verify first: 94 neurons, 6079 connections, 0 g_peak_sum mismatches vs the dump, all weights 0.2, InSimulationTime 0.
Then `scaled_prune` applied in 6 batches (all StatusCode 0), cues P0 at 20 ms and P1 at 220 ms via SetSpecificAPTimes, STDP off, RunAndWait 400 ms at dt 1 ms: 0.5 s wall.
| pattern | completion (non-cue 4) | latency | spurious non-members | cross-pattern | interneurons | spikes per member in its 200 ms | burst end |
|---|---|---|---|---|---|---|---|
| P0 | 4/4 = 1.00 | 2.06-2.16 ms | 0/51 | 0/8 | 0 | 11-14 (cue cells 1-2) | last spike ~63 ms (43 ms after cue), ISI growing 3 -> 4.7 ms |
| P1 | 4/4 = 1.00 | 1.84-2.25 ms | 0/51 | 0/8 | 0 | 7-11 | last spike ~246 ms (26 ms after cue) |
Weights read back: 2939/2939 AMPA weights equal the programmed values; 2868/2868 NMDA entries on programmed pairs are 0 (API side effect observed); GABA weights still 0.2. 140 spikes total, all pyramidal; 0 interneuron spikes in 400 ms.
On the real simulator the programmed engrams recall cleanly and the burst self-terminates (NES adaptive threshold/AHP/ADP, absent in the surrogate) without any inhibition.

## 7. Proven / inferred / assumed
PROVEN (observed): reservoir numbers in section 2 (dump == server state verified); engram margins (exact evaluation on the matrix); API semantics (source + observed weights-after); real-NES recall result in section 6 for K=2 `scaled_prune`; bio-limit checks in section 8.
INFERRED: that K=3/4 would also recall on the server (same mechanism, margins >= 38 nS > 27.44; not run); that burst termination comes from the NES adaptive threshold/AHP/ADP (consistent with converter defaults and with the surrogate lacking them; not isolated); that `scaled_bg02` is also clean on the server (surrogate only).
ASSUMED: surrogate parameters listed in section 5; the 27.44 nS target carried over from LIFtest (~2x the surrogate's G*, so conservative); scoring window 0.5-20 ms after the cue volley; that single-volley recall is the right behaviour metric (the doc's STDP protocol repeats cues at 70 ms; fatigue with the converter's 1000 ms recovery was not exercised in a 400 ms run).

## 8. Bio-limits
- Grown reservoir (sim 127): days 25 [20-25], pyramidal 67 [16-128], interneuron 27 [16-128], minneuronseparation 15 [10-15], radius 124 [100-200], thickness 42 [20-50], dm.weight 0.9 [0.1-1.0] -> `bio_check.assert_hard_limits` passed (re-asserted in `run_all.py`). growth_F / nu0 fixed by the team, not changed.
- Synaptic conductances were not modified: per-receptor g_peak remains 0.98 nS AMPA, 0.80 nS GABA, 0.55 nS NMDA (dump and server); only the dimensionless weight was set, within [0.0, 1.0] (asserted for all 8 programs; max programmed Conductance_nS equals the pair's own g_peak_sum, i.e. weight 1.0). No synapse was created; nothing exceeds what the grown morphology supports.

## 9. Blockers for the intended model (API gaps, confirmed)
- C2: no per-neurotransmitter weight endpoint. Programming AMPA zeroes the pair's NMDA (observed: 2868 entries), so the slow NMDA component LIFtest relies on is lost, and GABA weights cannot be raised from 0.2 at all.
- B4 inhibition bottleneck: even at the maximum weights the API allows (Pyr->Int 1.0), grown Int->Pyr conductance (mean 2.6 nS at weight 1, 0.5 nS at 0.2) is 6-30x below LIFtest's 16 nS, and 13/27 interneurons have no pyramidal input. Interneurons never fired on the server. Recall specificity currently rests entirely on pruning plus intrinsic adaptation.
- C1: EditLIFCNeuron cannot set fatigue (1000 ms converter default) -> any repeated-cue / STDP training protocol will hit the doc's B2 failure; not exercised here.
- C3: no compartment-ID query, so synapses cannot be topped up on a loaded model.
- Partial-batch hazard: `UpdateBatchPrePostStrength` applies elements until the first failure and then returns false (half-applied server state). Validate pairs offline first (done here).

## 10. Questions for the team
1. Should BatchSetPrePostStrength keep (or scale) NMDA instead of zeroing it, or should a (pre, post, neurotransmitter) weight endpoint be added (C2)? With it, GABA 0.5 and NMDA 0.5 as in LIFtest become possible.
2. Is the inhibitory bottleneck to be solved in Netmorph (interneuron axon/dendrite growth, placement) rather than in weight space? LIFtest targets: >= 7.84 nS onto every interneuron, >= 16 nS onto every pyramidal cell; sim 127 reaches 3 and 1 cells respectively.
3. Is single-volley cued recall with self-terminating bursts (section 6) an acceptable behaviour definition for the evaluation metrics, or must retrieval be sustained/sparse (needs inhibition)?
4. Should the 27.44 nS criterion be re-based on the converter-default neuron (G* ~ 14 nS), since the hand-built LIFtest neuron is not the one Netmorph builds?
5. May sim 127 stay in its programmed state (weights changed, simulated to 400 ms), or should it be reverted (SetAllStrength would zero NMDA on every pair, so reverting needs a reload from Netmorph)?
