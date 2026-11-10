# NetMorph Fable loop log (configuration + weight-space programming)

- Started 2026-11-09.
- Model: Claude Fable 5.2 for analysis and decisions; sonnet/haiku subagents for all execution.
- No git commits.
- Nothing deleted on the NES server.
- Worktree copy: /home/johnjose/cos/netmorph_work/bec (copied from the old scratchpad without its .git pointer; the git worktree itself remains in the old scratchpad).
- Working files: /home/johnjose/cos/netmorph_work/fable_loop/.

## Knob survey (ranked by expected effect on the weak spots)

| rank | knob | where | default | expected effect | bio-limit status |
|---|---|---|---|---|---|
| 1 | D_synmax.pyramidal.interneuron, D_synmax.interneuron.pyramidal, D_synmax.interneuron.interneuron | Netmorph config text (synapse_formation_model.cc:50, defaults in synapse_formation_model.hh maxfibredistance) | 0.1 um for every pair involving an interneuron vs 1.0 um for Pyr->Pyr | Directly gates all three weak pathways; this is the cause of 92 Pyr->Int synapses vs 22651 Pyr->Pyr in sim 127 | NOT in bio_ranges.json (no team range). Netmorph's own comment: spiny combinations bridge up to 1.0 um, aspiny 0.1 um. Flagged as an unranged modelling choice. |
| 2 | interneuron.min_basal / interneuron.max_basal | Netmorph config (neuron.cc:957-958) | 2-4 dendrites (pyramidal: 4-8 basal + apical) | More interneuron dendrite to receive pyramidal input (Pyr->Int only) | not in bio_ranges.json |
| 3 | all_interneuron_axons.* and all_interneuron_dendrites.* (B_inf, tau, E, growth_nu0, growth_F, L0, direction model) | Netmorph config; interneuron sets inherit from all_axons / all_dendrites | inherited | Denser interneuron arbors: Int->Pyr, Int->Int | not in bio_ranges.json; global growth_F=0.39 and growth_nu0=0.00013889 must stay constant |
| 4 | In.interneuron count, In.shape.radius, In.shape.thickness, minneuronseparation, days, dm_weight | hard-limited parameters | - | Already explored in batch B (100 samples): weak/unpredictable effect on Pyr->Int, Int->Int | HARD limits, asserted before each run |
| 5 | Engram membership chosen from the connectome + Pyr->Int AMPA weights | weight space (BatchSetPrePostStrength) | weights 0.2 | Choose engram cells converging on the same interneurons; Pyr->Int weight up to 1.0 | weights within [0,1] |
| 6 | Cue-margin scaling of engram weights | weight space | - | Cue-size selectivity: 4-cell cue just above firing threshold, 3 cells below | weights within [0,1] |
| 7 | EditLIFCNeuron on interneurons (Vth, Rm, Cm, refractory, Vrest, Vreset, spike depolarization) | NES API | converter gives interneurons the same LIF parameters as pyramidal cells (only sAHP and ADP are off) | Could make interneurons more excitable | no documented bio range; not used so far |

Also surveyed, not usable:

- P_receptor.<pre>.<post>.<type> (receptor probabilities; Pyr->Int has AMPA only, no NMDA).
- soma_min/max_radius_interneuron.
- idx.<region>.<type>.<k>.attractedto/attractors (per-neuron chemoattraction).
- NES-side per-synapse conductances (AMPA 0.98, NMDA 0.55, GABA 0.80 nS) and initial weight 0.2 are hard-coded.
- GABA weights cannot be programmed through the API.
- AHP/ADP/fatigue/adaptive-threshold parameters cannot be edited.

## Iteration 1: D_synmax dose-response (growth)

### Observations before

- Sim 127 (days 25, pyr 67, int 27, minsep 15, radius 124, thickness 42, dm.weight 0.9): synapses Pyr->Pyr AMPA 22651, Pyr->Int AMPA 92, Int->Pyr GABA 217, Int->Int GABA 33.
- Per-interneuron AMPA input mean 3.339 nS, 13 of 27 with zero, 1 of 27 >= 13.84 nS.
- Per-pyramidal GABA mean 2.591 nS, 1 cell >= 16 nS.

### Reasoning

- Per target cell, pyramidal cells receive about 338 synapses but interneurons 3.4.
- Netmorph source shows the capture distance for any pair involving an interneuron is 0.1 um vs 1.0 um for Pyr->Pyr.
- Changing only this isolates the cause.
- Two doses to get a dose-response.

### Edit (before -> after)

- D_synmax.pyramidal.interneuron, D_synmax.interneuron.pyramidal, D_synmax.interneuron.interneuron: 0.1 (default) -> 0.5 (arm a) and -> 1.0 (arm b).
- All seven hard-limited parameters unchanged and identical to sim 127.
- bio_check.assert_hard_limits returned True.
- Directives sent confirmed in run logs.
- Same random seed 20240628.

### Result

| quantity | sim 127 (0.1) | sim 133 (arm a, 0.5) | sim 134 (arm b, 1.0) |
|---|---|---|---|
| wall time s | - | 616 | 568 |
| Pyr->Pyr AMPA synapses | 22651 | 22899 | 22787 |
| Pyr->Int AMPA synapses | 92 | 1208 | 3627 |
| Int->Pyr GABA synapses | 217 | 3331 | 10257 |
| Int->Int GABA synapses | 33 | 543 | 1504 |
| Pyr->Int pairs | 70 | 397 | 640 |
| interneurons with zero pyramidal input | 13 | 7 | 5 |
| interneurons with >= 7.84 nS input | 3 | 12 | 17 |
| interneurons with >= 13.84 nS input | 1 | 10 | 16 |
| mean / median AMPA input per interneuron (nS) | 3.339 / 0.980 | 43.846 / 6.860 | 131.647 / 26.460 |
| max AMPA input onto one interneuron (nS) | 40.2 | 499.8 | 1442.6 |
| mean / median GABA onto a pyramidal cell (nS, weight 1) | 2.591 / 1.600 | 39.773 / 23.200 | 122.472 / 68.000 |
| pyramidal cells with >= 16 nS GABA | 1 | 39 | 52 |
| frac_int_driven | - | 0.444 | 0.630 |
| frac_pyr_inhibited (16 nS) | - | 0.582 | 0.776 |
| frac_pyr_inhibited_w05 (8 nS) | - | 0.687 | 0.821 |
| usable_pyr_int / usable_int_pyr / usable_int_int | - | 211 / 616 / 97 | 418 / 1065 / 182 |
| usable_conns2 (Pyr->Pyr) | - | 968 | 1066 |

- Soma positions identical to sim 127 in both arms.
- Pyr->Pyr AMPA matrix correlation with sim 127: 0.9749 (a), 0.9724 (b).

### Learned

- The knob works and leaves Pyr->Pyr essentially unchanged.
- Growth is superlinear in D_synmax.
- Sim 133 (0.5) is taken forward: inhibitory synapses onto pyramidal cells are about 13% of their input synapses (3331 vs 22899) and mean GABA at the fixed 0.2 weight is about 8 nS, the documented target.
- Sim 134 (1.0) would be about 45% inhibitory synapses.
- Input onto interneurons remains very uneven (7 with none, one with 499.8 nS).
- Caveat: D_synmax has no team-approved range.

## Iteration 2: weights on a copy of sim 133 (done, sim 135)

### Observations

- Design table, fable_loop/it2/design_table.txt: the four engram groups designed on sim 127 remain feasible on sim 133 (minimum 4-cue margins 175.4, 94.1, 55.9, 32.3 nS).
- At Pyr->Int weight 1, G0's eight cells deliver 122.5 nS to interneuron 89, 40.2 to 93, 18.6 to 77, 15.7 to 82.
- G1 delivers 83.3 to 89, 35.3 to 79, 26.5 to 93, 14.7 to 82.
- Interneurons 89 and 93 are driven by every group (global, not pattern-specific inhibition).
- Those interneurons return 22.4-30.4 nS GABA (weight 1) onto G0's non-cue members but a mean of 1.9 nS onto pyramidal cells outside any group.

### Reasoning

- Prediction is that interneurons will now fire and shorten bursts, but will not suppress bystander cells, so pruning is still needed for specificity.
- Unknown NES firing thresholds are calibrated first.

### Edit

Five phases on a ModelSave/ModelLoad copy of sim 133:

- A: pyramidal threshold calibration (4-cue totals 12, 14, 16, 18 nS onto G0 non-cue cells and 20, 22, 24, 28 nS onto G1 non-cue cells, everything else 0).
- B: all Pyr->Int at weight 1, Pyr->Pyr 0, cue 4 or 8 cells.
- C: K=2 scaled engrams (4-cue delivers 27.44 nS), other Pyr->Pyr pruned to 0, Pyr->Int weight 1.
- D: same with Pyr->Int 0 (inhibition off).
- E: repeat of C.

### Result

Result (new sim 135 = ModelLoad copy of sim 133, model saved on the server as 'fable-it1a-sim133'; copy verified: 94 neurons, 7370 connections, 0 g_peak_sum mismatches, all weights 0.2; sim 133 itself only received read-only calls plus one ModelSave). All ops StatusCode 0; 3344 ops per phase; simulation clock 1000, 2000, 3500, 5000, 6500 ms; 426 spikes total, none outside the cue windows. Raw data: fable_loop/it2/it2_out.json, it2_summary.txt.

- Phase A (pyramidal threshold, synchronous 4-cell volley): totals 12 nS (cell 4) and 14 nS (cell 18) did not fire; 16 nS (cell 20, latency 4.21 ms) and 18 nS (cell 59, 3.55 ms) fired; 20, 22, 24, 28 nS all fired (3.09, 2.85, 2.67, 2.39 ms). Threshold is in (14, 16] nS. No interneuron spikes.
- Phase B (interneuron drive, Pyr->Int weight 1, Pyr->Pyr 0): G0 4-cue fired interneurons 89 (81.3 nS, 2 spikes) and 93 (15.7 nS, 1 spike); 82 (9.8 nS) and 77 (7.8 nS) silent. G0 8 cells: 77 (18.6), 82 (15.7), 89 (3 spikes), 93 (2 spikes) fired. G1 8 cells: 79 (35.3), 89, 93 fired; 82 (14.7 nS) silent. G2 8 cells: 79 (16.7), 80 (17.6), 89, 93 fired; 82 (13.7) silent. Interneuron threshold is in (14.7, 15.7] nS.
- Phases C/D/E (K=2 recall, scaled engram weights 0.109-0.292 onto non-cue cells, everything else pruned):

| pattern | condition | member spikes | last pyramidal spike after cue (ms) | interneuron spikes | interneurons firing | spurious / cross-pattern |
|---|---|---|---|---|---|---|
| G0 | C inhibition on | 49 | 26.76 | 28 | 6 | 0 / 0 |
| G0 | D inhibition off | 73 | 43.17 | 0 | 0 | 0 / 0 |
| G0 | E inhibition on (repeat) | 42 | 22.85 | 26 | 6 | 0 / 0 |
| G1 | C inhibition on | 33 | 18.15 | 20 | 7 | 0 / 0 |
| G1 | D inhibition off | 40 | 21.94 | 0 | 0 | 0 / 0 |
| G1 | E inhibition on (repeat) | 33 | 18.17 | 20 | 7 | 0 / 0 |

- Completion 4/4 non-cue members in every recall event (latency 2.4-2.5 ms).
- Final weights read back: Pyr->Pyr AMPA {0, 0.1089, 0.1176, 0.1346, 0.1564, 0.2435, 0.2642, 0.2917, 1.0}; Pyr->Pyr NMDA all 0 (known API side effect); Pyr->Int AMPA 1.0; Int->Pyr and Int->Int GABA 0.2 (not programmable).

Learned:

- (1) Interneurons now fire on the real simulator, for the first time in this project.
- (2) Feedback inhibition cuts member spikes by 33-42% (G0) and 17.5% (G1) and shortens the G0 burst from 43 ms to 23-27 ms; phase E reproduces phase C, so this is not a run-order or fatigue artefact.
- (3) The firing threshold on NES is about 15 nS for both cell classes, so the earlier 27.44 nS cue target is about 1.8x threshold, which explains the weak cue-size selectivity.

Not tested here: cue-size selectivity, K=3, unpruned background.

## Iteration 3: K=3 engrams with cue-size selectivity (done, sim 136)

### Observations

- NES firing threshold for a synchronous volley is in (14, 16] nS (iteration 2).
- The earlier engram target of 27.44 nS from a 4-cell cue is about 1.8x threshold, so 2- and 3-cell cues also complete.
- G0/G1/G2 all have cue->non-cue pair conductances >= 6.86 nS (minimum per group: 33.32, 8.82, 6.86 nS).

### Reasoning

- If every cue cell gives every non-cue member the same conductance T4/4, then k cue cells deliver exactly k*T4/4.
- T4 = 18 nS puts 4 cells at 18 (fired in calibration) and 3 cells at 13.5 (below the 14 nS that failed).
- Cue->cue links are set to 0 because three cue cells would otherwise deliver up to 19.7 nS to the fourth and recruit it.
- Also tested:
  - T4 = 20 (3 cells = 15 nS, inside the uncertain band).
  - Weak background weights instead of full pruning (0.05, chosen from a single-volley estimate: largest cross-pattern input 219 nS x 0.05 = 11 nS).
  - The as-grown background 0.2.

### Edit (before -> after)

On new sim 136 (ModelLoad copy of sim 133, verified 94 neurons / 7370 connections / 0 mismatches / weights 0.2):

- cue->non-cue pairs: per-post scaled weights (4-cue total 27.44 nS) -> equal 4.5 nS per pair (T4 = 18) or 5.0 nS (T4 = 20)
- cue->cue pairs: weight 1 -> 0
- non-cue->non-cue: w_post x G with w_post = min(1, 27.44/S_post) (0.109-0.491)
- non-cue->cue: weight 1
- all other Pyr->Pyr: 0, or 0.05, or 0.2
- Pyr->Int: weight 1 (inhibition on) or 0 (off)
- 3344 ops per phase, all StatusCode 0. Events 500 ms apart.
- Raw data: fable_loop/it3/it3_out.json, it3_summary.txt.

### Result

Result 1 (T4 = 18, other weights pruned; identical with inhibition on (phase 1) and off (phase 2)):

| cue | G0 | G1 | G2 | cross-pattern / other pyramidal cells firing |
|---|---|---|---|---|
| 2 cells | 0/4 | 0/4 | 0/4 | 0 / 0 |
| 3 cells, subset 1 | 0/4 | 0/4 | 0/4 | 0 / 0 |
| 3 cells, subset 2 | 0/4 | 0/4 | 0/4 | 0 / 0 |
| 4 cells | 4/4 (latency 3.56 ms) | 4/4 (3.60 ms) | 4/4 (3.55 ms) | 0 / 0 |

- Member spikes for the 4-cell cue, inhibition on vs off: G0 33 vs 46, G1 28 vs 36, G2 21 vs 25.
- Last pyramidal spike: G0 19.87 vs 29.68 ms, G1 17.79 vs 22.35 ms, G2 15.78 vs 18.78 ms.
- Interneurons firing with inhibition on: 6, 5, 5 (21, 18, 13 spikes).
- Interneuron 89 also fires on 2- and 3-cell G0 cues (2 spikes) without any pyramidal completion.

Result 2 (T4 = 20, pruned, phases 3-4): not selective.

- The 3-cell cues [22,29,51], [12,17,19] (inhibition on and off), [27,33,44] (on) and [8,27,33] (off) completed 4/4 at latency 4.91-4.95 ms; the other 3-cell subsets did not.
- 15 nS is at threshold and the outcome depends on recent activity (events were only 500 ms apart, so this phase has an order confound).

Result 3 (T4 = 18, background 0.05, phases 5-6):

- 2- and 3-cell cues still give 0/4.
- The 4-cell cue completes its pattern but also fires 11-13 members of the other two patterns and 12-13 other pyramidal cells (19-20 spikes) with inhibition on.
- With inhibition off: 11-13 members and 18 other pyramidal cells (45-47 spikes).
- Target-pattern member spikes on vs off: G0 56 vs 77, G1 42 vs 65, G2 36 vs 50.
- 9-10 interneurons fire (54-58 spikes).

Result 4 (T4 = 18, background 0.2 as grown, phases 7-8): runaway.

- Inhibition on:
  - G0 cue: 14 other-pattern members and 32 other pyramidal cells fire (380 spikes), 13 interneurons (145 spikes), activity lasts 75.88 ms.
  - G1 cue 500 ms later does not complete (0/4).
  - G2 cue again runs away (72.44 ms).
- Inhibition off:
  - G0 cue: 0/4 (it follows the previous runaway by 500 ms).
  - G1 cue runs away (435 other-pyramidal spikes, 87.79 ms).
  - G2 cue: 0/4.

### Learned

- (1) K=3 disjoint engrams with exact cue-size selectivity (4 cells complete, 2 or 3 never) and zero cross-pattern or spurious activity were measured on NES, with interneurons active. This needs T4 = 18 nS, a window of only about +/-10-20% around threshold.
- (2) Pattern specificity still depends on pruning non-engram Pyr->Pyr weights to 0. A background of 0.05 already leaks into the other patterns; the single-volley estimate was wrong because it ignored summation over a multi-spike burst.
- (3) Inhibition at the fixed GABA weight 0.2 reduces spread (other-pyramidal spikes 19-20 vs 45-47 at background 0.05) but cannot contain it, and cannot stop the runaway at the as-grown 0.2.
- (4) 500 ms between events is too short after a burst; later iterations use 1000-1500 ms.

## Iteration 4: background tolerance vs inhibition strength (done, sims 137 and 138)

### Observations

Going in: on sim 136 a background (non-engram Pyr->Pyr) weight of 0.05 leaked into other patterns with and without inhibition; pruned (0) was clean. Sim 134 (D_synmax 1.0) has about three times the GABA conductance of sim 133 (mean 122.5 vs 39.8 nS per pyramidal cell at weight 1) and 16 instead of 10 interneurons above threshold input.

### Reasoning

Measure the largest background weight that keeps recall specific, with inhibition on and off, on both reservoirs. If stronger grown inhibition helps, sim 134 should tolerate more background than sim 133. Events 1000-1500 ms apart to avoid the adaptation confound seen in iteration 3.

### Edit (before -> after)

Same engram rule as iteration 3 with T4 = 18 nS, recomputed from each reservoir's own dump (arm b: 2951 Pyr->Pyr and 640 Pyr->Int pairs; minimum cue->non-cue pair conductance G0 33.32, G1 5.88, G2 6.86 nS). Background weight 0 -> 0.01, 0.02, 0.03, 0.05. Pyr->Int weight 1 (on) or 0 (off).

New sims: 137 = ModelLoad copy of sim 133 (model 'fable-it1a-sim133'); 138 = ModelLoad copy of sim 134 (one ModelSave on sim 134 as 'fable-it1b-sim134' after read-only verification: 94 neurons, 8030 connections, 0 mismatches, weights 0.2). Both copies verified against their dumps. All ops StatusCode 0. Raw data: fable_loop/it4/arm_a and arm_b (it4_out.json, it4_summary.txt, build.log).

### Result

Sim 137 (D_synmax 0.5). Cue-size selectivity at background 0 reproduced: 2- and 3-cell cues 0/4, 4-cell cue 4/4 for G0, G1, G2, with inhibition on and off, no cross-pattern or other spikes. Member spikes on vs off: G0 28 vs 50, G1 28 vs 37, G2 21 vs 25; last pyramidal spike 15.97 vs 32.94 ms, 17.92 vs 23.96 ms, 15.91 vs 18.72 ms.

Table "4-cell cue, sim 137":

| background weight | inhibition on | inhibition off |
|---|---|---|
| 0.01 | clean (4/4, 0 cross, 0 other) for G0, G1, G2 | clean for G0, G1, G2 |
| 0.02 | clean for G0, G1, G2 | G0 and G2 clean; G1 cue also fires 7 G0 members (1-8 spikes each), activity lasts 46.40 ms |
| 0.03 | clean for G0, G1, G2 (member spikes 28, 28, 21, identical to background 0) | 11-13 other-pattern members and 5-7 other pyramidal cells fire on every cue |
| 0.05 | G0 and G1 cues fire 11-12 other-pattern members and 13 other pyramidal cells (20 spikes); G2 cue (third in the phase) clean | 11-13 other-pattern members and 18 other pyramidal cells (45-48 spikes) on every cue |

Sim 138 (D_synmax 1.0). Inhibition off: same pattern as sim 137 (clean at 0 and 0.01; G1 cue recruits 7 G0 members at 0.02; widespread at 0.03 and 0.05). Inhibition on, at every background weight including 0: the 4-cell cue fails for G0 (0/4) and G1 (0/4); G2 completes 4/4 but with only 9 member spikes ending at 6.86 ms. Interneurons fire on the cue alone: for the G0 4-cell cue, interneuron 89 at 1.34 ms, 93 at 1.74 ms, 82 at 1.93 ms, 80 at 2.59 ms, before the non-cue members could reach threshold (3.55 ms without inhibition). Cue cells alone deliver 227.36 nS to interneuron 89 in this reservoir (81.34 nS in sim 133). 2- and 3-cell cues give 0/4 as before.

### Learned

(1) On the D_synmax 0.5 reservoir, feedback inhibition raises the tolerated background weight from 0.01 to 0.03 with recall unchanged; inhibition therefore buys robustness to incomplete pruning, a result weights alone could not give on sim 127.

(2) The D_synmax 1.0 reservoir with all Pyr->Int weights at 1 is over-inhibited: feed-forward inhibition driven by the cue itself vetoes recall. More grown inhibition is not automatically better.

(3) The veto is feed-forward, and Pyr->Int weights are programmable per pair, so the next step is to scale down cue-cell->interneuron weights and keep the rest (feedback-only inhibition).

## Iteration 5: feedback-only inhibition routing (done, sims 139 and 140)

### Observations

On sim 138 (D_synmax 1.0) the 4 cue cells alone deliver 227.36 nS to interneuron 89, which fires at 1.34 ms and vetoes recall. On sim 137 (0.5) interneuron 89 also fires on 2- and 3-cell cues. Pyr->Int AMPA weights are programmable per pair.

### Reasoning

Scale down only the cue-cell->interneuron weights so that a cue alone stays below the interneuron threshold (14.7-15.7 nS); leave non-cue members and ungrouped pyramidal cells at weight 1. Interneurons should then fire only after the pattern has completed or when activity spreads to bystanders, which is exactly when inhibition is wanted.

### Edit (before -> after)

Pyr->Int weight for pairs whose presynaptic cell is a designated cue cell of group g: 1.0 -> min(1, 10 / C_gi), where C_gi is the summed conductance from group g's four cue cells onto interneuron i (cue-only drive capped at 10 nS). All other Pyr->Int pairs stay at 1.0. Sim 139 (copy of 133): 23 pairs below weight 1, minimum 0.1229. Sim 140 (copy of 134): 79 pairs below weight 1, minimum 0.0440. Engram rule unchanged (T4 = 18 nS). Background weights 0, 0.03, 0.05, 0.1, 0.2; controls with all Pyr->Int at 0 for background 0.05 and 0.2. Events 1000 ms (12-event set) or 3000 ms apart. Both copies verified against their dumps (7370 and 8030 connections, 0 mismatches, weights 0.2); all ops StatusCode 0. Raw data: fable_loop/it5/arm_a and arm_b.

### Result

Cue-size selectivity at background 0 (both sims): 2-cell and both 3-cell cues give 0/4 with zero interneuron spikes; the 4-cell cue gives 4/4 for G0, G1 and G2 with no cross-pattern or other spikes. First interneuron spike now comes after completion (sim 139: 4.44 ms; sim 140: 4.23 ms; non-cue members fire at 3.55 ms). Member spikes for the 4-cell cue: sim 139: 28, 27, 20 (last spike 16.21, 16.09, 15.58 ms); sim 140: 9, 10, 9 (last spike 6.43, 7.79, 6.65 ms).

Table "4-cell cue with background weights":

| background weight | sim 139 (D_synmax 0.5), feedback inhibition | sim 140 (D_synmax 1.0), feedback inhibition | inhibition off (both sims) |
|---|---|---|---|
| 0.03 | clean for G0, G1, G2 | clean for G0, G1, G2 | not rerun here (iteration 4: 11-13 other-pattern members fire) |
| 0.05 | 11-13 other-pattern members, 13 other pyramidal cells (20 spikes), last spike 29.93-32.82 ms | clean for G0, G1, G2 (member spikes 9, 10, 9) | 11-13 other-pattern members, 18-19 other pyramidal cells (45-48 spikes), last spike 39.87-47.83 ms |
| 0.1 | 11-13 other-pattern members, 23 other pyramidal cells (105-111 spikes), 36.60-40.34 ms | 11-13 other-pattern members (1-5 spikes each), 16-18 other pyramidal cells (24-27 spikes), 16.92-17.93 ms | not run |
| 0.2 (as grown) | 14 other-pattern members, 32 other pyramidal cells (406-409 spikes), 84.25-86.04 ms | 13-14 other-pattern members, 28 other pyramidal cells (130-135 spikes), 25.99-27.86 ms | 14 other-pattern members, 32 other pyramidal cells (472-492 spikes), 96.88-101.93 ms |

"Clean" means 4/4 completion with zero cross-pattern and zero other pyramidal spikes. With 3000 ms between events every cue completed 4/4 even after a runaway.

### Learned

(1) Routing inhibition as feedback only removes the cue veto: the D_synmax 1.0 reservoir now recalls all three patterns, sparsely (about one to two spikes per member, over within 8 ms). (2) Tolerated background weight: 0.01 without inhibition, 0.03 on the 0.5 reservoir, 0.05 on the 1.0 reservoir with feedback routing. (3) At the as-grown background 0.2 nothing is specific, but on the 1.0 reservoir inhibition ends the spread after 26-28 ms instead of 97-101 ms and cuts other-pyramidal spikes from 472-492 to 130-135. (4) Feedback routing does not improve the 0.5 reservoir's tolerance (still 0.03); the gain there is only that sub-threshold cues no longer fire interneuron 89.

## Summary after 5 iterations

Table "Simulations created in this loop":

| sim ID | what it is | state |
|---|---|---|
| 133 | grown, D_synmax 0.5 (it1 arm a) | pristine (as-built weights 0.2); saved on server as 'fable-it1a-sim133' |
| 134 | grown, D_synmax 1.0 (it1 arm b) | pristine; saved on server as 'fable-it1b-sim134' |
| 135 | copy of 133, iteration 2 | programmed, simulated to 6500 ms |
| 136 | copy of 133, iteration 3 | programmed, simulated to 39000 ms |
| 137 | copy of 133, iteration 4 arm a | programmed, simulated to 60000 ms |
| 138 | copy of 134, iteration 4 arm b | programmed, simulated to 60000 ms |
| 139 | copy of 133, iteration 5 arm a | programmed, simulated to 66000 ms |
| 140 | copy of 134, iteration 5 arm b | programmed, simulated to 66000 ms |

Nothing was deleted. Sim 127 and all earlier simulations were not touched.

### What holds

- D_synmax for interneuron pairs is the knob that fixes the interneuron reservoir: Pyr->Int synapses 92 -> 1208 -> 3627 and Int->Pyr 217 -> 3331 -> 10257 at 0.1 / 0.5 / 1.0, with Pyr->Pyr unchanged.
- Interneurons fire on NES; firing threshold for a synchronous volley is about 15 nS for both cell classes.
- K=3 disjoint 8-cell engrams with exact cue-size selectivity (4 cue cells complete, 2 or 3 do not) and no cross-pattern or spurious activity, measured on sims 136, 137, 139 and 140.
- Inhibition shortens recall bursts and raises the tolerated background weight from 0.01 to 0.03 (0.5 reservoir) or 0.05 (1.0 reservoir, feedback-only routing).

### What does not hold / caveats

- D_synmax is not in bio_ranges.json; there is no team-approved range. 0.5 and 1.0 are modelling choices (Netmorph's own comment gives 1.0 um for spiny and 0.1 um for aspiny contacts). The seven hard-limited parameters never left their ranges.
- Specificity still needs non-engram Pyr->Pyr weights at or below 0.03-0.05; at the as-grown 0.2 every cue spreads through the network.
- Cue-size selectivity relies on T4 = 18 nS, about 20% above threshold; T4 = 20 was not selective. Robustness to jittered (non-synchronous) cues was not tested.
- All results are for one reservoir geometry and one random seed, one trial per condition (the simulator is deterministic here: repeated conditions reproduced to within one or two spikes).
- BatchSetPrePostStrength zeroes NMDA on every programmed Pyr->Pyr pair, so all recall here is AMPA-only. GABA weights stayed at 0.2 (not programmable). STDP was off throughout.
- 7 of 27 (sim 133) and 5 of 27 (sim 134) interneurons still receive no pyramidal input.
- The sim 134 reservoir has about 45% inhibitory synapses onto pyramidal cells (10257 GABA vs 22787 AMPA), which is high.

# Round 2: robustness tests as a test of prediction by reasoning
Rules for this round: before each experiment a dated prediction block (numbers plus reasoning) is written here; after the run each prediction is scored hit or miss with the reasoning step that failed. Working config: D_synmax 0.5 (sim 133 lineage). Max 4 iterations.

## Working model used for the predictions (written 2026-11-09 22:43 PST)
- Neuron: leak 10 nS (Rm 100 MOhm), Cm 100 pF, rest -70 mV, threshold -50 mV (20 mV to climb). AMPA: reversal 0 mV, rise 0.5 ms, decay 3 ms.
- Single-volley kernel: a synaptic volley of peak conductance g (nS) arriving at time 0 produces depolarisation V(t) = 0.927 x g x K(t) mV, with K(t) = 4.286 (e^(-t/10) - e^(-t/3)) - 0.526 (e^(-t/10) - e^(-2t)), t in ms. K peaks at 1.485 near t = 5.7 ms; K(2) = 0.89, K(3) = 1.21, K(4) = 1.39, K(5) = 1.47, K(6) = 1.48, K(7) = 1.45, K(8) = 1.39, K(10) = 1.23, K(12) = 1.05, K(14) = 0.89. The factor 0.927 is calibrated so that the synchronous threshold is 14.5 nS (measured: 14 nS fails, 15 nS fires). Fitted synaptic delay about 0.5 ms (measured latencies 3.55 ms at 18 nS, 4.21 ms at 16 nS, 2.39 ms at 28 nS).
- Sustained-burst rule (correction for the earlier miss that ignored burst summation): members of a recalled pattern fire about every 3.1 ms. A train of volleys of peak g every 3.1 ms gives a mean conductance of 1.38 x g. A cell fires when mean conductance x 55 mV / (10 nS + mean conductance + inhibitory shunt) reaches 20 mV, i.e. mean conductance >= 0.571 x (10 + shunt). Without inhibition that is a single-volley-equivalent peak of only 4.1 nS, 3.5 times lower than the 14.5 nS single-volley threshold. Check against existing data (not a prediction): background 0.02 without inhibition, G1 burst onto cell 59: sustained G1 members deliver 214.7 nS at weight 1, x 0.02 = 4.3 nS >= 4.1, and it fired; G0 burst onto cell 41: 152.8 x 0.02 = 3.1 nS < 4.1, and it stayed silent.

## Prediction block P1: jittered (non-synchronous) cues (written 2026-11-09 22:43 PST, before the run)
Experiment: fresh copy of sim 133, engram rule T4 = 18 nS (4.5 nS per cue->non-cue pair), background 0, feedback-only inhibition. The four cue spikes are spread evenly over a window J (offsets 0, J/3, 2J/3, J). Events 2000 ms apart.
Reasoning: each cue spike adds 0.927 x 4.5 x K(t - t_i) = 4.17 x K mV; firing needs the sum of the four K values to reach 4.80 (synchronous maximum 5.94). Because the membrane time constant (10 ms) is longer than the AMPA decay (3 ms), K stays above 1.2 from 3 to 10 ms, so a few ms of jitter costs little. Computed best sums: J = 3: 5.70; J = 6: 5.44; J = 9: 5.06; J = 12: 4.62.
Predictions:
- P1.1: J = 0, 3 and 6 ms: 4/4 completion for G0, G1 and G2 (high confidence).
- P1.2: J = 9 ms: 4/4 for all three patterns (low confidence, 5% margin).
- P1.3: J = 12 and 15 ms: 0/4 for all three patterns (J = 12 low confidence, 4% margin; J = 15 high confidence).
- P1.4: latency of the first non-cue spike measured from the FIRST cue spike: 3.55 ms (J = 0), 5.3 ms (J = 3), 7.9 ms (J = 6), 11.8 ms (J = 9), each +/- 0.5 ms.
- P1.5: three-cell cues with jitter (offsets 0, 2, 4 ms): 0/4 for all patterns (high confidence; jitter can only lower the 13.5 nS peak).
- P1.6: reversing which cue cell is early or late changes nothing (same completion; latency within 0.2 ms), because all cue->non-cue pairs are equal at 4.5 nS.
- P1.7: when a jittered cue completes, member spike counts are within 20% of the synchronous values (28, 27, 20 for G0, G1, G2), with 0 cross-pattern and 0 other pyramidal spikes; interneurons fire only on events that complete.

## Prediction block P3a: growth with three new random seeds at D_synmax 0.5 (written 2026-11-09 22:43 PST, before the runs)
Experiment: same seven hard-limited parameters as sim 133 (days 25, pyramidal 67, interneuron 27, minneuronseparation 15, radius 124, thickness 42, dm.weight 0.9), D_synmax 0.5 for the three interneuron pairs, random seeds 1001, 1002, 1003 (sim 133 used 20240628).
Reasoning: Pyr->Pyr synapse count is a sum over about 2900 connected pairs, so it should vary little with seed. Pyr->Int input was dominated by one interneuron in sim 133 (499.8 of 1183.8 nS), so totals for interneuron pathways should vary by about a factor of two. The ratio of Int->Pyr to Pyr->Int synapses was 2.76 at 0.5 and 2.83 at 1.0, so it looks like a property of the growth rules, not of the seed.
Predictions (each for all three seeds unless stated):
- P3a.1: Pyr->Pyr AMPA synapses between 20500 and 25000 (sim 133: 22899).
- P3a.2: Pyr->Int AMPA synapses between 500 and 2500 (sim 133: 1208).
- P3a.3: Int->Pyr GABA synapses between 2000 and 5000 (sim 133: 3331).
- P3a.4: ratio Int->Pyr / Pyr->Int synapses between 2.3 and 3.3.
- P3a.5: Int->Int GABA synapses between 200 and 1100 (sim 133: 543).
- P3a.6: interneurons with >= 13.84 nS pyramidal input: 7 to 13 of 27 (sim 133: 10); interneurons with zero input: 4 to 10 (sim 133: 7).
- P3a.7: frac_int_driven between 0.33 and 0.56 (sim 133: 0.444).
- P3a.8: wall time 520 to 680 s per run, exit code 0.
- P3a.9: for every seed, three disjoint 8-cell engram groups exist in which every cue->non-cue pair has at least 4.5 nS; with a max-min search the weakest pair is >= 30 nS in the first group and >= 12 nS in the third.

## Prediction block P2: STDP on vs off (written 2026-11-09 22:46 PST, before the run)

- Experiment: two fresh copies of sim 133 with identical weights (engram rule T4 = 18 nS, background 0, feedback-only inhibition), one with STDP off, one with STDP on.
- Protocol: per pattern, a 3-cell cue before any recall, then 4-cell recalls interleaved with 3-cell and 2-cell probe cues; events 2000 ms apart. Weights are read back after the first G0 recall and at the end.
- Source facts (NES: Neuron.cpp STDP_Update, LIFCNeuron.cpp spike()):
  - STDP acts on AMPA only; evaluated on each postsynaptic spike against the most recent spike of each presynaptic cell.
  - dw = 0.027 x X x e^(-X), with X = (t_post - t_pre + 4 ms) / 7 ms; weight clipped to [0, 1]; additive, so a weight of 0 can grow.
  - Because t_pre <= t_post always, X >= 0.57 and the depression branch is never reached: this STDP only potentiates.
  - dw per post spike: 0.0087 at 0 ms lag, 0.0099 at 3 ms, 0.0090 at 6.6 ms, 0.0074 at 10 ms, 0.0030 at 20 ms, about 0 beyond 50 ms.
- Reasoning:
  - In a recall each non-cue member fires about 5 times within 16 ms, each time potentiating its four cue inputs.
  - Summed over the burst: about +0.037 for a cue cell that fired once, +0.047 for one that keeps firing.
  - The conductance added is dw x the pair's g_peak_sum. G0 pairs are large (33-75 nS), so one recall adds 5-10 nS to the 18 nS a full cue delivers and 3-7 nS to the 13.5 nS of a 3-cell cue.
  - G0 non-cue cells would receive 18-21 nS from three cue cells. G1: 16-20 nS.
  - G2 pairs are small (7-22 nS): 14.7-15.4 nS, right at the 14.5 nS threshold.
  - Events are 2000 ms apart, so cells of different patterns are never co-active within the STDP window.
- Predictions:
  - P2.1 (STDP off copy): unchanged behaviour on every repetition. 3-cell and 2-cell cues 0/4; 4-cell cues 4/4 with member spikes 28, 27, 20 (+/- 2) for G0, G1, G2; all weights read back unchanged.
  - P2.2 (STDP on): the 3-cell cue given before any recall gives 0/4 for all patterns.
  - P2.3: after the first G0 recall, every G0 cue->non-cue weight has increased by 0.030 to 0.050 (e.g. pair 22->4 from 0.078 to between 0.108 and 0.128); no weight anywhere has decreased; all weights between different patterns and to or from ungrouped pyramidal cells are still exactly 0.
  - P2.4: a 3-cell cue completes 4/4 immediately after one 4-cell recall for G0 and G1 (high confidence). For G2 borderline: completes after one recall (low confidence), and certainly after two.
  - P2.5: 2-cell cue after one recall: G0 at most 1 of 4 non-cue cells (cell 59 predicted at 14.8 nS, borderline); G1 and G2 0/4 (low confidence for G0). After at least three full recalls: G0 2-cell cue completes 4/4 (medium confidence); G1 at least cell 39 fires (medium); G2 0/4 (low confidence).
  - P2.6: member spikes per 4-cell recall grow with repetition; the fifth G0 recall has at least 1.3 times the member spikes of the first (medium confidence).
  - P2.7: no cross-pattern and no other pyramidal spikes in any event, with STDP on or off (high confidence).
  - P2.8: at the end, all G0 cue->non-cue weights are >= 0.25 (they start at 0.06-0.14).
- Overall claim under test: with this STDP rule (potentiation only, no normalisation), cue-size selectivity is lost after a single recall and erodes further with use.

## Round 2, iteration 1 result: jittered cues (sim 142, scored 2026-11-09 22:46 PST)

- New sim 142 = ModelLoad copy of sim 133 (verified: 94 neurons, 7370 connections, 0 mismatches, weights 0.2). Weights: T4 = 18 nS, background 0, feedback-only inhibition; STDP off.
- 30 events 2000 ms apart; all 90 forced spikes at the expected times; 669 spikes, none outside the event windows.
- Raw data: fable_loop/r2_it1/r2it1_out.json, r2it1_summary.txt.
- Results (cue | G0 | G1 | G2):

| cue | G0 | G1 | G2 |
|---|---|---|---|
| 4 cells, spread 0 ms | 4/4, latency 3.55 ms, 28 member spikes | 4/4, 3.55 ms, 27 | 4/4, 3.55 ms, 20 |
| 4 cells, spread 3 ms | 4/4, 5.43 ms, 28 | 4/4, 5.43 ms, 27 | 4/4, 5.43 ms, 20 |
| 4 cells, spread 6 ms | 4/4, 7.97 ms, 34 | 4/4, 7.96 ms, 27 | 4/4, 7.96 ms, 19 |
| 4 cells, spread 9 ms | 4/4, 11.67 ms, 34 | 4/4, 11.62 ms, 28 | 4/4, 11.62 ms, 21 |
| 4 cells, spread 12 ms | 0/4 | 0/4 | 0/4 |
| 4 cells, spread 15 ms | 0/4 | 0/4 | 0/4 |
| 3 cells, offsets 0/2/4 ms (two subsets) | 0/4, 0/4 | 0/4, 0/4 | 0/4, 0/4 |
| 4 cells, spread 9 ms, order reversed | 4/4, 11.56 ms, 34 | 4/4, 11.56 ms, 28 | 4/4, 11.56 ms, 20 |
| 4 cells, spread 12 ms, order reversed | 0/4 | 0/4 | 0/4 |

- No cross-pattern and no other pyramidal spikes in any event. Interneurons fired only on completed events (first interneuron spike about 0.9-1.4 ms after the first non-cue spike).
- Scorecard P1 (prediction | predicted | measured | score):
- P1.1 | spread 0, 3, 6 ms: 4/4 for all patterns | 4/4 for all patterns | hit
- P1.2 | spread 9 ms: 4/4 (low confidence) | 4/4 for all patterns | hit
- P1.3 | spread 12 and 15 ms: 0/4 | 0/4 for all patterns | hit
- P1.4 | latency 3.55 / 5.3 / 7.9 / 11.8 ms (+/- 0.5) | 3.55 / 5.43 / 7.96-7.97 / 11.62-11.67 ms | hit
- P1.5 | jittered 3-cell cues 0/4 | 0/4 for all six | hit
- P1.6 | reversed order: same completion, latency within 0.2 ms | same completion; 11.56 vs 11.62-11.67 ms | hit
- P1.7 | member spikes within 20% of 28, 27, 20; no cross or other spikes; interneurons only on completed events | G1 27-28, G2 19-21 (within); G0 34 at 6 and 9 ms spread (+21%); no cross or other spikes; interneurons only on completed events | partial miss (G0 spike count)
- What the reasoning got right: the linear membrane kernel with one calibrated constant placed the jitter boundary between 9 and 12 ms although both calls were within 5% of threshold, and gave the latencies to within 0.2 ms.
- What failed: P1.7 assumed the burst after completion is independent of cue timing. Late cue spikes arrive while the non-cue members are already firing and add drive during the burst, which lengthened the G0 burst (last spike 25-29 ms instead of 16 ms). This is the same class of error as the earlier burst-summation miss: quantities that depend on sustained recurrent dynamics.
- Practical result: recall tolerates cue spikes spread over up to 9 ms and fails at 12 ms; cue-size selectivity is unaffected by jitter.

## Round 2, iteration 2 result: STDP on vs off (sims 143 and 144, scored 2026-11-09 22:53 PST)

New sims: 143 (STDP off) and 144 (STDP on), both ModelLoad copies of sim 133, verified (94 neurons, 7370 connections, 0 mismatches, weights 0.2). Identical weights applied once (T4 = 18 nS, background 0, feedback-only inhibition), 39 events 2000 ms apart, weight snapshots between segments. Raw data: `fable_loop/r2_it2/stdp_off` and `stdp_on` (out.json, snaps.json, summary.txt).

- **STDP off (sim 143):** every 2- and 3-cell cue 0/4; every 4-cell cue 4/4 with 28-29 (G0), 27 (G1), 20 (G2) member spikes, latency 3.55-3.57 ms; no weight changed in any snapshot; 749 spikes total.
- **STDP on (sim 144), event by event:**
  - **G0:** 3-cell cue before any recall 0/4. First 4-cell recall: 4/4 but 119 member spikes lasting 83.44 ms (STDP-off value: 28 spikes, 16.22 ms). After it: 3-cell cues 4/4 (171 and 202 spikes, latency 2.02 and 1.53 ms), 2-cell cue 4/4 (193 spikes). Later 4-cell recalls 200, 196, 166 spikes, then 24 and (2-cell) 14 spikes; final 4-cell recall after a 50 s gap: 211 spikes, 129.86 ms.
  - **G1:** 3-cell before recall 0/4; first recall 33 spikes (20.47 ms); then 3-cell 4/4 (44, 50 spikes), 2-cell 4/4 (55 spikes); recalls grow to 70, 123, 131, 130; final 134 spikes, 78.37 ms.
  - **G2:** 3-cell before recall 0/4; first recall 19 spikes; then 3-cell 4/4 (26 and 31 spikes, latency 4.96 and 4.31 ms); first 2-cell probe 0/4; later 2-cell probes 4/4 (37 and 52 spikes); recalls 33, 53, 53, 48; final 48 spikes.
  - No cross-pattern and no other pyramidal spikes in any event. 4556 spikes total; 1 spike outside the 300 ms event windows.
- **Weights, STDP on:**
  - G0 cue->non-cue weights after the first recall (start 0.060-0.135): from cell 22: 0.158-0.202; from 29: 0.261-0.337; from 51: 0.132-0.164; from 63: 0.268-0.286.
  - After the G0 block: 1.0 from cells 22, 29, 63 and 0.49-0.54 from cell 51.
  - End of run: G1 cue->non-cue 0.60-1.0, G2 0.53-1.0; all non-cue->non-cue weights 1.0 in all three patterns; cue->cue weights (programmed 0) up to 1.0 in G0 and G1 and up to 0.31 in G2.
  - Pyr->Pyr pairs changed: 36 after the first recall, 105 at the end, all increases, none outside a pattern (0 changed, max change 0.0000).
  - Pyr->Int pairs increased: 8 after the first recall, 19 at the end (largest +0.8771); cue-cell->interneuron 89 weights rose from 0.12-0.46 to 0.56-1.0.
  - GABA weights 0.2 throughout.

### Scorecard P2

| Prediction | Predicted | Measured | Score |
|---|---|---|---|
| P2.1 | STDP off: unchanged on repetition, 28/27/20 +/- 2, weights fixed | 28-29 / 27 / 20; no weight changed | hit |
| P2.2 | 3-cell cue before any recall 0/4 | 0/4 for all patterns | hit |
| P2.3a | G0 cue->non-cue weights +0.030 to +0.050 after one recall (22->4 to 0.108-0.128) | +0.046 to +0.21 (22->4 to 0.1645; 29->4 to 0.2787) | miss (2-5 times too small) |
| P2.3b | no weight decreases anywhere | 0 decreased in every snapshot | hit |
| P2.3c | weights between patterns and to/from ungrouped cells stay exactly 0 | 0 pairs changed outside patterns | hit |
| P2.4 | 3-cell cue completes after one recall: G0 and G1 (high confidence), G2 (low confidence) | 4/4 for G0, G1 and G2 | hit |
| P2.5a | 2-cell cue after one recall: G0 at most 1/4, G1 0/4, G2 0/4 | G0 4/4, G1 4/4, G2 0/4 | miss for G0 and G1, hit for G2 |
| P2.5b | 2-cell cue after three or more recalls: G0 4/4, G1 at least cell 39, G2 0/4 | G0 4/4, G1 4/4, G2 4/4 | hit for G0 and G1, miss for G2 |
| P2.6 | fifth G0 recall at least 1.3 times the first | first 119, then 200, 196, 166, fifth 24 | miss |
| P2.7 | no cross-pattern or other pyramidal spikes, STDP on or off | 0 in every event | hit |
| P2.8 | G0 cue->non-cue weights >= 0.25 at the end | 0.5467-1.0 | hit |

- **Overall claim** (selectivity lost after a single recall and eroding with use): confirmed.
- **What the reasoning got right:** the per-spike update read from the source (cell 51, which fired once, gained +0.040 to +0.047 against a computed +0.037 to +0.046), the absence of depression, the strict locality to co-active cells, and the qualitative loss of selectivity.
- **What failed and why:**
  1. P2.3a, P2.5a: I counted about 5 postsynaptic spikes per recall, taken from STDP-off bursts. With STDP on, the recurrent non-cue->non-cue and cue->non-cue weights grow during the burst itself, the burst feeds on that and ran to 21 spikes per cell over 83 ms, so cells that kept firing gained about 0.2 instead of 0.047. I treated plasticity and dynamics as separable; they are a closed loop.
  2. P2.6: after several long bursts 2000 ms apart the G0 cells almost stopped (24 and 14 spikes) and recovered after a 50 s rest. The fatigue mechanism in the neuron model (fatigue threshold, 1000 ms recovery) was not in my working model at all.
  3. P2.5b for G2: same underestimate of weight growth as (1).
- **Practical result:** with the built-in STDP (potentiation only, no depression reachable, no normalisation), programmed cue-size selectivity does not survive use. Recall-time STDP has to stay off, or the rule needs a depression branch or weight normalisation, before a learning protocol can be combined with programmed engrams.

## Prediction block P4a: D_synmax interpolation, growth at 0.3 and 0.7 (written 2026-11-09 22:53 PST, before the runs)

**Experiment:** same seven hard-limited parameters and seed 20240628 as sims 127/133/134, D_synmax for the three interneuron pairs set to 0.3 and to 0.7.

**Reasoning:** the three existing points lie on a power law in D_synmax. Pyr->Int synapses 92, 1208, 3627 at 0.1, 0.5, 1.0 give exponents 1.60 (0.1 to 0.5) and 1.59 (0.5 to 1.0). Int->Pyr 217, 3331, 10257 give 1.70 and 1.62. Int->Int 33, 543, 1504 give 1.74 and 1.47. An exponent between 1 and 2 is what a capture cross-section between crossing fibres would give. Interpolating from the 0.5 point with exponent 1.6 (1.66 for Int->Pyr).

### Predictions

| Quantity | D_synmax 0.3 | D_synmax 0.7 |
|---|---|---|
| P4a.1 Pyr->Int AMPA synapses | 533 (accept 450-620) | 2070 (accept 1750-2400) |
| P4a.2 Int->Pyr GABA synapses | 1427 (accept 1200-1650) | 5823 (accept 4950-6700) |
| P4a.3 Int->Int GABA synapses | 240 (accept 180-300) | 930 (accept 750-1110) |
| P4a.4 Pyr->Pyr AMPA synapses | 22300-23300 | 22300-23300 |
| P4a.5 soma positions identical to sim 133 | yes | yes |
| P4a.6 mean GABA onto a pyramidal cell at weight 1 (nS) | 17.0 (accept 14-20) | 69.5 (accept 59-80) |
| P4a.7 interneurons with >= 13.84 nS pyramidal input (0.1: 1, 0.5: 10, 1.0: 16) | 5-8 | 11-14 |
| P4a.8 wall time | 520-680 s | 520-680 s |

## Round 2, iteration 3a result: growth with three new seeds (sims 141, 145, 146, scored 2026-11-09 23:18 PST)

- Seeds 1001, 1002, 1003 -> sims 141, 145, 146.
- Hard limits asserted (True); directives confirmed in each run log; all exit 0; wall 630, 538, 653 s.
- Each verified against its dump (94 neurons; 6852, 6130, 7070 connections; 0 mismatches; weights 0.2) and saved on the server as 'fable-r2-seed1001', 'fable-r2-seed1002', 'fable-r2-seed1003'.
- Raw data: fable_loop/r2_seeds (analysis.txt, design_<seed>.txt).

| quantity | sim 133 (seed 20240628) | seed 1001 | seed 1002 | seed 1003 |
|---|---|---|---|---|
| Pyr->Pyr AMPA synapses | 22899 | 21450 | 19674 | 26205 |
| Pyr->Int AMPA synapses | 1208 | 955 | 1399 | 927 |
| Int->Pyr GABA synapses | 3331 | 2951 | 2585 | 3575 |
| ratio Int->Pyr / Pyr->Int | 2.76 | 3.09 | 1.85 | 3.86 |
| Int->Int GABA synapses | 543 | 414 | 497 | 384 |
| interneurons >= 13.84 nS pyramidal input | 10 | 6 | 8 | 5 |
| interneurons with zero pyramidal input | 7 | 11 | 7 | 10 |
| frac_int_driven | 0.444 | 0.296 | 0.444 | 0.185 |
| frac_pyr_inhibited (16 nS) | 0.582 | 0.493 | 0.373 | 0.537 |
| mean GABA onto a pyramidal cell (nS, weight 1) | 39.773 | 35.236 | 30.866 | 42.687 |

### Engram design by max-min search

Weakest cue->non-cue pair (nS) for groups 1 / 2 / 3:

- Seed 1001: 30.38 / 19.60 / 10.78
  - G0 cue [17,19,59,62], non-cue [3,32,55,61]
  - G1 cue [11,13,38,65], non-cue [4,20,54,63]
  - G2 cue [21,44,45,53], non-cue [6,12,16,18]
- Seed 1002: 32.34 / 11.76 / 6.86
  - G0 cue [12,15,24,38], non-cue [0,7,9,25]
  - G1 cue [18,42,43,58], non-cue [30,31,33,60]
  - G2 cue [17,36,53,55], non-cue [34,44,50,65]
- Seed 1003: 44.10 / 18.62 / 13.72
  - G0 cue [14,25,31,63], non-cue [7,9,26,58]
  - G1 cue [5,33,53,59], non-cue [4,8,56,57]
  - G2 cue [15,29,40,66], non-cue [1,3,44,51]

### Scorecard P3a

| prediction | predicted | measured (1001 / 1002 / 1003) | score |
|---|---|---|---|
| P3a.1 Pyr->Pyr | 20500-25000 | 21450 / 19674 / 26205 | miss (two of three outside) |
| P3a.2 Pyr->Int | 500-2500 | 955 / 1399 / 927 | hit |
| P3a.3 Int->Pyr | 2000-5000 | 2951 / 2585 / 3575 | hit |
| P3a.4 ratio | 2.3-3.3 | 3.09 / 1.85 / 3.86 | miss |
| P3a.5 Int->Int | 200-1100 | 414 / 497 / 384 | hit |
| P3a.6 | interneurons >= 13.84 nS: 7-13; zero input: 4-10 | 6 / 8 / 5; 11 / 7 / 10 | miss |
| P3a.7 frac_int_driven | 0.33-0.56 | 0.296 / 0.444 / 0.185 | miss |
| P3a.8 wall 520-680 s, exit 0 | 630 / 538 / 653 s, exit 0 | hit |
| P3a.9 three feasible groups per seed; weakest pair >= 30 nS (first group), >= 12 nS (third) | all nine groups feasible; first 30.38 / 32.34 / 44.10; third 10.78 / 6.86 / 13.72 | hit on feasibility and first group, miss on third group |

### What failed and why

These are not dynamics errors.

- P3a.4: I took the Int->Pyr / Pyr->Int ratio as a constant of the growth rules because it was 2.76 and 2.83 at two D_synmax values. Those two runs share one seed and one set of soma positions, so the agreement said nothing about seeds.
- P3a.6, P3a.7: ranges were centred on sim 133, a single sample from a heavy-tailed distribution. Sim 133 is the most favourable of the four seeds for interneuron drive.
- P3a.1: I estimated +/-10% from the number of pairs, but the count is dominated by a few multi-synapse pairs and by soma placement, so +/-15% was needed.
- Practical result: D_synmax 0.5 gives 5-10 interneurons above firing threshold depending on seed; frac_int_driven 0.19-0.44.

## Prediction block P3b: recall on the three new-seed reservoirs (written 2026-11-09 23:18 PST, before the runs)

Experiment: one fresh copy per seed (ModelLoad of the saved models), engram groups from the max-min design above, engram rule T4 = 18 nS, feedback-only inhibition. Phase 1: background 0 with the 12-event cue set (2, 3, 3, 4 cells per pattern). Then background 0.01, 0.02, 0.03, 0.05, each with feedback inhibition and with inhibition off, 4-cell cues 3000 ms apart.

Leak threshold reasoning without inhibition (sustained-burst rule): a bystander fires when background weight x S_sus >= 4.1 nS, where S_sus is the weight-1 conductance it receives from the members that keep firing during the burst: the four non-cue cells plus any cue cell that the non-cue cells drive with >= 14.5 nS. From the design tables (largest non-cue-only sum SNC / all-eight sum S8, nS):

- Seed 1001: G1->G0 157.78 / 343.00, G2->G0 116.62 / 345.94, G0->G1 83.30 / 212.66. No G1 or G2 cue cell is driven above 14.5 nS (max 5.88 and 9.80); one G0 cue cell is (15.68).
- Seed 1002: G1->G0 230.30 / 583.10, G2->G0 214.62 / 541.94. G1 has a re-firing cue cell (22.54); G2 does not (11.76).
- Seed 1003: G0->G1 125.44 / 307.72, G1->G0 134.26 / 344.96, G2->G0 117.60 / 309.68, G2->G1 114.66 / 280.28. G0 cue cells re-fire (40.18); G1 and G2 marginal (16.66).

Predictions:

- P3b.1: background 0, all nine patterns: 4-cell cue 4/4 with first non-cue latency 3.55 ms (+/- 0.05); every 2- and 3-cell cue 0/4; no cross-pattern or other spikes (high confidence: these are fixed by the equalised 4.5 nS pairs).
- P3b.2: member spikes per 4-cell recall at background 0 with feedback inhibition: between 14 and 40 for each of the nine patterns (medium confidence).
- P3b.3: at least two interneurons fire in every 4-cell recall at background 0, none on 2- or 3-cell cues (medium confidence).
- P3b.4: leak threshold without inhibition (first background weight in {0.01, 0.02, 0.03, 0.05} at which any cell outside the cued pattern fires):
  - Seed 1001: S_sus 157.78 -> 4.1/157.78 = 0.026, so clean at 0.01 and 0.02, leak at 0.03.
  - Seed 1002: S_sus 230-320 -> 0.013-0.018, so clean at 0.01, leak at 0.02.
  - Seed 1003: S_sus 171-216 -> 0.019-0.024, so clean at 0.01, leak at 0.02 (low confidence, borderline), certainly at 0.03.
- P3b.5: which cue leaks first and into what:
  - Seed 1001: the G1 cue, recruiting G0 cells, while the G0 cue is still clean at that weight.
  - Seed 1002: the G1 and G2 cues, recruiting G0 cells, G0 cue clean.
  - Seed 1003: the G0 cue recruiting G1 cells and/or the G1 cue recruiting G0 cells.
- P3b.6: at the first leaking weight the extra spikes come only from members of the other patterns, with 0 ungrouped pyramidal cells firing (no ungrouped cell receives >= 140 nS from any pattern in any seed).
- P3b.7, with feedback inhibition: in every seed the first leaking weight is strictly higher than without inhibition (medium confidence). Specific calls (low confidence): seed 1001 clean at 0.03, leaking at 0.05; seed 1002 clean at 0.02; seed 1003 clean at 0.02.
- P3b.8: at background 0.05 without inhibition every seed leaks on at least two of the three cues (high confidence).

## Prediction block P4b: recall at D_synmax 0.3 and 0.7, predicted from scaling alone (written 2026-11-09 23:18 PST, before those reservoirs exist)

Experiment: after growing D_synmax 0.3 and 0.7 (seed 20240628), copies are programmed with the sim 133 engram groups (G0, G1, G2), T4 = 18 nS. Phases:

1. background 0, all Pyr->Int weights 1 ("uniform"), 12-event cue set;
2. background 0, inhibition off;
3. background 0, feedback-only inhibition;
4-6. background 0.02, 0.03, 0.05 with feedback-only inhibition;
7. background 0.03, inhibition off.

Reasoning: interneuron pathways scale as D_synmax^1.6, so relative to sim 133 all interneuron conductances are x 0.44 at 0.3 and x 1.71 to 1.75 at 0.7. In sim 133 the four G0 cue cells drive interneurons 89 / 93 / 82 / 77 with 81.3 / 15.7 / 9.8 / 7.8 nS; at 0.7 that becomes about 139 / 27 / 17 / 13 nS, so three interneurons fire on the cue alone, and the GABA they return to the G0 non-cue cells (22-30 nS at weight 1 in sim 133) becomes about 33-45 nS x 0.2 = 6.5-9 nS of shunt. An 18 nS cue is only 24% above threshold, so a shunt above about 2.4 nS arriving before 3.5 ms should veto it. At 0.3 the same numbers are 36 / 7 / 4 / 3 nS and about 2 nS of shunt: no veto, little inhibition.

Predictions:

- P4b.1: all cue->non-cue pairs are >= 4.5 nS in both new reservoirs, so the design applies unchanged (high confidence).
- P4b.2 (0.3, uniform weights): 4-cell cue 4/4 for G0, G1, G2; 2- and 3-cell cues 0/4 (high confidence).
- P4b.3 (0.3): inhibition is weak: G0 member spikes with uniform inhibition 36-46, against 50 (+/- 3) with inhibition off (sim 133: 28 vs 50); 1 to 3 interneurons fire per recall.
- P4b.4 (0.7, uniform weights): the cue vetoes itself for G0 (0/4, medium confidence) and for G1 (0/4, low to medium confidence); G2 completes 4/4 with at most 15 member spikes.
- P4b.5 (0.7, feedback-only inhibition): all three patterns complete 4/4; member spikes between the sim 133 values (28, 27, 20) and the D_synmax 1.0 values (9, 10, 9): 12-22 each (medium confidence).
- P4b.6 (0.7, inhibition off, background 0): same as sim 133 without inhibition: 4/4, member spikes 50 / 37 / 25 (+/- 4).
- P4b.7, tolerated background with feedback-only inhibition:
  - At 0.3: clean at 0.02, leaking at 0.03 (medium-low confidence).
  - At 0.7: clean at 0.03 (high confidence), leaking at 0.05 (low confidence; D_synmax 0.5 leaked at 0.05 and 1.0 did not).
- P4b.8: background 0.03 with inhibition off leaks in both reservoirs, with 11-13 other-pattern members firing (high confidence).

## Round 2, iteration 3b result: recall on three new-seed reservoirs (sims 148, 149, 150, scored 2026-11-09 23:24 PST)

New sims 148, 149, 150 = ModelLoad copies of the seed 1001, 1002, 1003 reservoirs (verified: 6852, 6130, 7070 connections, 0 mismatches, weights 0.2). Engram groups from the max-min design; T4 = 18 nS; feedback-only inhibition or inhibition off; STDP off. All ops StatusCode 0; 36/36 forced spikes at the expected times in each. Raw data: `fable_loop/r2_it3/seed<seed>/out.json`, `summary.txt`.

- **Background 0 (all three seeds, nine patterns):** every 2-cell and 3-cell cue 0/4 with no interneuron spikes; every 4-cell cue 4/4 at latency 3.55 ms; no cross-pattern or other spikes.
- **Member spikes per 4-cell recall (G0, G1, G2):** seed 1001: 21, 14, 13; seed 1002: 27, 27, 12; seed 1003: 22, 32, 33.
- **Interneurons firing:** 4, 3, 4 / 5, 4, 4 / 4, 3, 3.

### 4-cell cues with background weights

| background weight | seed 1001, feedback inhibition | seed 1001, inhibition off | seed 1002, feedback inhibition | seed 1002, inhibition off | seed 1003, feedback inhibition | seed 1003, inhibition off |
|---|---|---|---|---|---|---|
| 0.01 | clean | clean | clean | clean | clean | clean |
| 0.02 | clean | clean | clean | G1 cue fires 6 G0 members (7-10 spikes each) | clean | every cue fires 13-14 other-pattern members; 1 ungrouped cell (1 spike) on two cues |
| 0.03 | clean | G0 cue fires 4 G1 members (2-3 spikes each); G1 and G2 cues clean | G1 cue fires 6 G0 members (3-5 spikes each); G0 and G2 cues clean | every cue fires 5-11 other-pattern members | G2 cue fires 1 G0 member (1 spike); G0 and G1 cues clean | every cue fires 13-14 other-pattern members and 10 ungrouped cells |
| 0.05 | G1 cue fires 1 G0 member (1 spike), G2 cue fires 2 G0 members (1 spike each); G0 cue clean | every cue fires 10-13 other-pattern members and 13 ungrouped cells | every cue fires 5-11 other-pattern members, 0 ungrouped | every cue fires 11-12 other-pattern members, 1 ungrouped cell | every cue fires 13-14 other-pattern members and 11-13 ungrouped cells | every cue fires 13-15 other-pattern members and 16-17 ungrouped cells |

- "Clean" = 4/4 completion with zero spikes outside the cued pattern.
- First leaking weight without / with feedback inhibition: seed 1001: 0.03 / 0.05; seed 1002: 0.02 / 0.03; seed 1003: 0.02 / 0.03 (sim 133: 0.02 / 0.05).

### Scorecard P3b

| prediction | predicted | measured | score |
|---|---|---|---|
| P3b.1 | all nine patterns: 4-cell 4/4 at 3.55 ms, 2- and 3-cell 0/4, no other spikes | exactly that | hit |
| P3b.2 | member spikes 14-40 per recall | 21, 14, 13 / 27, 27, 12 / 22, 32, 33 | partial miss (two of nine at 12-13) |
| P3b.3 | at least 2 interneurons per 4-cell recall, none on 2- or 3-cell cues | 3-5 per recall; none on smaller cues | hit |
| P3b.4 | first leaking weight without inhibition: 0.03 (seed 1001), 0.02 (1002), 0.02 (1003, low confidence) | 0.03, 0.02, 0.02 | hit |
| P3b.5 | first leak: seed 1001 G1 cue into G0 cells with G0 cue clean; seed 1002 G1 and G2 cues into G0 cells with G0 cue clean; seed 1003 G0 and/or G1 cue | seed 1001: G0 cue into G1 cells, G1 cue clean; seed 1002: G1 cue into G0 cells, G2 and G0 cues clean; seed 1003: all three cues | miss (1001), partial (1002), hit (1003) |
| P3b.6 | at the first leaking weight only other-pattern members fire, 0 ungrouped cells | 0 / 0 / 1 ungrouped cell with 1 spike | hit, hit, near miss |
| P3b.7 | feedback inhibition raises the first leaking weight in every seed; seed 1001 clean at 0.03 and leaking at 0.05, seed 1002 clean at 0.02, seed 1003 clean at 0.02 | 0.03 -> 0.05, 0.02 -> 0.03, 0.02 -> 0.03; all specific calls correct | hit |
| P3b.8 | background 0.05 without inhibition leaks on at least two of three cues in every seed | all three cues in every seed | hit |

### Reasoning review

- **What the reasoning got right:** everything fixed by conductance sums at a single volley (selectivity, latency), and the leak thresholds from the sustained-burst rule (4.1 nS divided by the sustained drive) in all three unseen reservoirs.
- **What failed and why:** P3b.5 for seed 1001 (and half of seed 1002), and P3b.2 for the same patterns. The rule assumes the cued pattern's burst is sustained. I assumed that for every pattern whose non-cue cells receive more than about 10 nS of recurrent drive, but G1 in seed 1001 and G2 in seeds 1001 and 1002 stop after two cycles (12-14 member spikes, last spike 7-11 ms) and so never reach the summed drive the rule assumes. The 0.03 threshold for seed 1001 was right, but it came from the G0 burst (30 spikes, 18.8 ms), not from the pair I named.
- **Open question:** whether a burst sustains or dies after two cycles is not yet predictable from my working model; it depends on after-hyperpolarisation, the adaptive threshold and the timing of re-firing cue cells.

### Practical result

- The weight design transfers to new seeds with groups chosen by a mechanical search.
- Cue-size selectivity is exact in 12 of 12 patterns tested so far (4 seeds).
- Feedback inhibition raises the tolerated background by one grid step in every seed.
- Tolerated background with inhibition is 0.02-0.03.

## Round 2, iteration 4 result: D_synmax 0.3 and 0.7 (sims 147, 151, 152, 153, scored 2026-11-09 23:45 PST)

Growth: sims 147 (D_synmax 0.3) and 151 (0.7), seed 20240628, hard limits asserted (True), directives confirmed, exit 0, wall 623 and 591 s. Verified against their dumps (6891 and 7745 connections, 0 mismatches, weights 0.2) and saved as 'fable-r2it4-d03' and 'fable-r2it4-d07'. Recall protocol on ModelLoad copies: sims 152 (0.3) and 153 (0.7), both verified. All ops StatusCode 0. Raw data: fable_loop/r2_it4 (analysis.txt, d03/summary.txt, d07/summary.txt).

Scorecard P4a (growth), columns: prediction | predicted 0.3 | measured 0.3 | predicted 0.7 | measured 0.7 | score.

| prediction | predicted 0.3 | measured 0.3 | predicted 0.7 | measured 0.7 | score |
|---|---|---|---|---|---|
| P4a.1 Pyr->Int synapses | 533 (450-620) | 537 | 2070 (1750-2400) | 2080 | hit |
| P4a.2 Int->Pyr synapses | 1427 (1200-1650) | 1441 | 5823 (4950-6700) | 5775 | hit |
| P4a.3 Int->Int synapses | 240 (180-300) | 201 | 930 (750-1110) | 868 | hit |
| P4a.4 Pyr->Pyr synapses | 22300-23300 | 22761 | 22300-23300 | 22821 | hit |
| P4a.5 soma positions identical to sim 133 | yes | yes | yes | yes | hit |
| P4a.6 mean GABA onto a pyramidal cell (nS) | 17.0 (14-20) | 17.206 | 69.5 (59-80) | 68.955 | hit |
| P4a.7 interneurons >= 13.84 nS input | 5-8 | 6 | 11-14 | 11 | hit |
| P4a.8 wall time (s) | 520-680 | 623 | 520-680 | 591 | hit |

- Other growth numbers: frac_int_driven 0.259 (0.3) and 0.593 (0.7); frac_pyr_inhibited 0.388 and 0.672; interneurons with zero input 9 and 6; Pyr->Pyr matrix correlation with sim 133: 0.9745 and 0.9749.
- Full dose-response for seed 20240628 at D_synmax 0.1 / 0.3 / 0.5 / 0.7 / 1.0:
  - Pyr->Int: 92 / 537 / 1208 / 2080 / 3627
  - Int->Pyr: 217 / 1441 / 3331 / 5775 / 10257
  - Int->Int: 33 / 201 / 543 / 868 / 1504

Recall results.

- D_synmax 0.3 (sim 152): uniform Pyr->Int weights, background 0:
  - 2- and 3-cell cues 0/4; 4-cell cues 4/4 with 37, 30, 27 member spikes (G0, G1, G2) and 4, 5, 2 interneurons firing.
  - Inhibition off: 40, 32, 27. Feedback-only: 37, 31, 27.
  - Feedback-only with background 0.02: clean. 0.03: every cue fires 11-13 other-pattern members and 4 ungrouped cells. 0.05: 11-13 members and 17 ungrouped cells.
  - Inhibition off at 0.03: 11-13 members and 7 ungrouped cells.
- D_synmax 0.7 (sim 153): uniform weights, background 0:
  - 2- and 3-cell cues 0/4 but 1-3 interneurons fire on them (first spike 1.45-2.33 ms).
  - 4-cell cues 4/4 with latency 3.72, 3.73, 3.56 ms and 9, 13, 16 member spikes, 5-6 interneurons (first spike 1.41-1.77 ms).
  - Inhibition off: 32, 38, 27. Feedback-only: 11, 20, 16 (first interneuron spike 4.28-4.34 ms).
  - Feedback-only with background 0.02 and 0.03: clean. 0.05: G1 cue fires 7 other-pattern members and 1 ungrouped cell, G0 and G2 cues clean.
  - Inhibition off at 0.03: 11-13 other-pattern members and 5-6 ungrouped cells on every cue.

Scorecard P4b (recall), columns: prediction | predicted | measured | score.

| prediction | predicted | measured | score |
|---|---|---|---|
| P4b.1 all cue->non-cue pairs >= 4.5 nS in both reservoirs | minimum per group | 30.38 / 9.80 / 6.86 (0.3) and 34.30 / 7.84 / 6.86 (0.7) | hit |
| P4b.2 0.3 uniform: 4-cell 4/4, 2- and 3-cell 0/4 | exactly that | exactly that | hit |
| P4b.3 0.3: G0 member spikes 36-46 with uniform inhibition vs 50 (+/- 3) off; 1-3 interneurons per recall | 37 vs 40; 4, 5, 2 interneurons | partial (uniform value hit; inhibition-off value and interneuron count missed) |
| P4b.4 0.7 uniform: cue vetoes itself for G0 and G1 (0/4); G2 4/4 with at most 15 spikes | G0 4/4 (9 spikes), G1 4/4 (13 spikes), G2 4/4 (16 spikes) | miss |
| P4b.5 0.7 feedback-only: all 4/4, member spikes 12-22 each | all 4/4; 11, 20, 16 | partial (G0 one spike below the range) |
| P4b.6 0.7 inhibition off, background 0: 50 / 37 / 25 (+/- 4) | 32 / 38 / 27 | partial (G0 missed) |
| P4b.7 tolerated background with feedback-only inhibition: 0.3 clean at 0.02 and leaking at 0.03; 0.7 clean at 0.03 and leaking at 0.05 | 0.3: clean at 0.02, leaking at 0.03; 0.7: clean at 0.03, leaking at 0.05 (G1 cue only) | hit |
| P4b.8 background 0.03 without inhibition leaks in both, 11-13 other-pattern members | 11-13 members in both | hit |

What failed and why:

1. P4b.4. I estimated that about 2.4 nS of shunt would veto an 18 nS cue and that D_synmax 0.7 would deliver 6.5-9 nS. The interneurons did fire early (1.41-1.77 ms), but recall only slowed by 0.17 ms and then stopped early. The estimate used a steady-state shunt; inhibition arriving after most of the cue's charge is already on the membrane does far less. The veto boundary for uniform Pyr->Int weights lies between 0.7 and 1.0.
2. P4b.3 and P4b.6. I assumed the inhibition-off burst of G0 (50 spikes in sims 137 and 139) is a fixed property of the pattern. In the 0.3 and 0.7 reservoirs it is 40 and 32 although the Pyr->Pyr matrices correlate 0.975 with sim 133: burst length is sensitive to small differences in recurrent weights.

Tolerated background with feedback-only inhibition as a function of D_synmax (seed 20240628): 0.3: 0.02; 0.5: 0.03; 0.7: 0.03 (0.05 leaks on one cue of three); 1.0: 0.05. Without inhibition: 0.01 at every value.

## Round 2 prediction scorecard (written 2026-11-09 23:45 PST)

Table, columns: block | experiment | predictions | hit | partial | miss.

| block | experiment | predictions | hit | partial | miss |
|---|---|---|---|---|---|
| P1 | jittered cues (sim 142) | 7 | 6 | 1 | 0 |
| P2 | STDP on vs off (sims 143, 144) | 11 | 7 | 1 | 3 |
| P3a | growth with three new seeds (sims 141, 145, 146) | 9 | 4 | 1 | 4 |
| P3b | recall on the new seeds (sims 148, 149, 150) | 8 | 6 | 2 | 0 |
| P4a | D_synmax 0.3 and 0.7 growth (sims 147, 151) | 8 | 8 | 0 | 0 |
| P4b | D_synmax 0.3 and 0.7 recall (sims 152, 153) | 8 | 4 | 3 | 1 |
| Total | | 51 | 35 | 8 | 8 |

Predicted well:

- Single-volley conductance arithmetic: which cues complete, cue-size selectivity in all 12 patterns over 4 seeds and 3 further D_synmax values, first-spike latency to within 0.2 ms.
- The jitter boundary (complete at 9 ms spread, fail at 12 ms) from a linear membrane kernel with one calibrated constant, although both calls were within 5% of threshold.
- The D_synmax scaling law: synapse counts at 0.3 and 0.7 to within 1% (Pyr->Int, Int->Pyr) and 7-16% (Int->Int) from a power law with exponent about 1.6.
- The per-spike STDP update and its locality, read from the source code.
- The background weight at which recall starts to leak, from the sustained-burst rule (4.1 nS divided by the sustained drive): correct in all three unseen seeds and at D_synmax 0.3 and 0.7.

Predicted badly:

- Burst size and duration (member spike counts): missed or only partly right in P1.7, P3b.2, P4b.3, P4b.5, P4b.6.
- Closed loops between plasticity and activity: STDP weight growth was 2-5 times larger than computed because the burst lengthened while weights grew (P2.3a, P2.5).
- Mechanisms missing from the working model: fatigue after repeated long bursts (P2.6); whether a given pattern's burst sustains or dies after two cycles (P3b.5).
- Timing-dependent inhibition: the predicted self-veto at D_synmax 0.7 did not happen (P4b.4).
- Statistics across seeds extrapolated from one sample: interneuron-drive ranges and the Int->Pyr / Pyr->Int ratio (P3a.4, P3a.6, P3a.7).

Earlier misses from round 1 and whether the corrected reasoning held:

- Burst summation (corrected rule held in 5 of 5 new reservoirs).
- "More grown inhibition is better" (veto boundary now bracketed between 0.7 and 1.0, but my estimate of where it lies was wrong).
- Event spacing (2000-3000 ms spacing gave reproducible events, except under STDP where fatigue appeared).
- Superlinear D_synmax growth (now a quantitative law that predicted two new points).

Simulations created in round 2 (all ours; nothing deleted; no earlier simulation modified):

- 141, 145, 146 (grown, seeds 1001-1003, pristine, saved as 'fable-r2-seed1001/1002/1003').
- 147, 151 (grown, D_synmax 0.3 and 0.7, pristine, saved as 'fable-r2it4-d03' and 'fable-r2it4-d07').
- 142 (jitter).
- 143, 144 (STDP off, on).
- 148, 149, 150 (seed recall).
- 152, 153 (D_synmax recall).
