# Ripple / recall on S1 (saved model `v2-arbor-S10000`: 96 pyr / 48 int, D_synmax 1.5/0.1, int axon B_inf 26, basal 6-10)
Own NES (8000). Fresh sim per case, ModelLoad then apply-then-run (no ModelSave), STDP off, every programmed pair read back (0 mismatches),
Dt 1 ms unless stated, 150 ms, cue protocol/analysis as in ripple_arborA (reused alib -> `slib.py`, `run_s1.py`, `analyze_s1.py`, `bio_audit_s1.py`, `design_sa.py`).
Data: `raw_*.json` (rasters, Vm for E1 best/worst), `summary.json`, `design_K4.json`, `bio_audit.json`, figures `fig_E1_*.png`, logs `run_*.log`.

## 1. Drivable criterion
Old criterion (`analyze_dend.py`): interneuron i is "drivable" if sum over ALL 96 pyramidal cells of AMPA g_peak_sum(pyr->i) >= 13.84 nS
(i.e. every pyramid firing at weight 1; 13 of 48 = 27%). That ignores that a memory has only 4-8 cells and weight <= 1 (conductance <= g_peak_sum).
Cap-aware (best possible 8 pyramidal cells, weight 1, synchronous): 7/48 interneurons reach >= 13.84 nS (7 at >= 15, 4 at >= 20);
best possible 4 cells: 2 (1 at >= 15). Selecting one fixed 8-cell memory: the annealed groups have only 1-2 interneurons at 11-22 nS each
(117 gets 11.8-21.8 nS from every memory; 134, 129, 142, 102 get 10-15 nS). Relaxation used in design: interneurons with total input >= 10 nS (17) counted, requiring >= 1 interneuron at >= 13.84 and >= 2 at >= 11 per memory (justified because members burst repeatedly, ISI 2-5 ms, so summation lets ~11 nS volleys fire: 10 interneurons fired in E1).

## 2. Design (`design_K4.json`, annealing on spike-weighted cross-inhibition, objective MAXIMISED unlike arbor A)
G0 [10,26,36,39,53,79,82,89] cue [10,26,36,53]; G1 [0,19,40,59,73,84,85,86] cue [0,59,73,86]; G2 [18,22,30,33,42,47,70,91] cue [18,22,42,70]; G3 [25,49,55,61,62,67,87,92] cue [61,62,67,87]. Cue->non-cue pairs >= 4.5 nS.
Even maximised, modelled cross-inhibition is 4.8-10.4 nS spike-weighted per memory pair (ripple_05 effective range 90-177 nS): Int->Pyr GABA g_peak is ~0.3-1 nS per pair, 2.2% inhibitory synapses. Inhibition cannot be made large by selection.

## 3. Results (success = all non-cue members spike within 10 ms, no cross-talk, 0 non-member pyr spikes, last spike <= 100 ms, no burst > 40 ms)
Single memory (4-cell completes / 3-cell does not): E1, NI, SG, ES: 4/4 groups complete (latency 4.03 ms), 0/8 false completions with 3 cells, clean. E1 bg0.03/0.05: complete, 3-cell clean, but 113/160 spurious non-member pyr spikes on full recall.
"burst end" = last member spike after own cue (ms, G order of cueing); int = interneuron spikes in each window.

| variant | case | complete | max lat ms | burst end ms | member spikes (total pyr) | int spikes | cross-talk / spurious | last spike after 1st cue | result |
|---|---|---|---|---|---|---|---|---|---|
| E1 | sep12 | 4,4,4,4 | 4.34 | 20.8/68.8/33.8/34.9 | 222 | 35 | 0/0 | 80.8 | FAIL (G1 burst 69 > 40) |
| E1 | sep16 | 4,4,4,4 | 4.32 | 20.8/48.9/33.8/33.8 | 195 | 33 | 0/0 | 81.8 | FAIL (G1 49 > 40) |
| E1 | sep20 | 4,4,4,4 | 4.26 | 20.8/47.6/33.8/33.8 | 195 | 30 | 0/0 | 93.8 | FAIL (G1 48) |
| E1 | shuffled 2,0,3,1 sep16 | 4,4,4,4 | 4.32 | 33.8/20.9/34.6/69.0 | 225 | 27 | 0/0 | 117.0 | FAIL (69 ms burst, ends > 100) |
| E1 | 3-mem subset 0,1,2 sep16 | 4,4,4 | 4.16 | 20.8/49.0/33.7 | 151 | 25 | 0/0 | 65.7 | FAIL (G1 burst 49) |
| E1 | sep12 / sep20, Dt 0.1 | 4,4,4,4 | 4.64 / 4.61 | 26.7/71.4/37.8/35.9 ; 26.3/63.3/37.5/35.0 | 263 / 253 | 38 / 36 | 0/0 | 83.4 / 95.0 | FAIL (burst > 40) |
| NI (Pyr->Int=0) | sep12/16/20, 3-subset | 4,4,4,4 (4,4,4) | 4.03 | 23.1/68.9/33.7/34.4 | 225 (181) | 0 | 0/0 | 80.9/84.9/94.4 (84.9) | FAIL (G1 69) |
| NI | shuffled | 4,4,4,4 | 4.03 | 33.7/23.1/34.4/68.9 | 225 | 0 | 0/0 | 116.9 | FAIL |
| SG (interneurons fire, all 1542 GABA pairs zeroed) | sep16 / sep20 / shuffled | 4,4,4,4 | 4.03 | 23.1/68.9/33.7/34.4 | 225 | 41 / 40 / 30 | 0/0 | 84.9 / 94.4 / 116.9 | FAIL; pyramidal spikes identical to NI |
| ES (no 10 nS cue cap on Pyr->Int, all weight 1) | sep16 / shuffled | 4,4,4,4 | 4.32 | identical to E1 | 195 / 225 | 33 / 27 | 0/0 | 81.8 / 117.0 | FAIL, identical to E1 (cap never binds) |
| E1 + background Pyr->Pyr 0.03 | sep16 | 4,4,4,4 | 4.03 | 61.1/52.6/33.8/16.1 | 378 pyr | 58 | 80 cross-talk / 59 spurious | 68.6 | FAIL (non-member and cross-memory firing; 48-55 int spikes/single recall) |
| E1 + background 0.05 | sep16 | 4,4,4,4 | 4.03 | 82.3/74.4/48.4/33.4 | 578 pyr | 77 | 96 / 144 | 90.4 | FAIL, runaway-like spread |

## 4. Did inhibition matter? Yes, but weakly and not as a ripple mechanism
* E1 vs SG/NI (GABA output zeroed): SG pyramidal spikes are identical to NI (to 0.001 ms), so the difference E1-vs-NI is caused by interneuron output, not by anything else. Effect: member latency +0.1-0.3 ms (4.03 -> 4.16-4.34), total pyramidal spikes -13% (195 vs 225), G0 burst 2.3 ms shorter, and in the ordered sep16/20 runs the G1 burst is cut from 68.9 to 47.6-48.9 ms (by inhibition from later-cued memories). It does not change completion (always 4/4), does not abolish cross-talk (none exists), and does not terminate the G1 burst below 40 ms.
* Strengthening: Pyr->Int already at weight 1 (cap 10 nS on cue cells never binds: ES = E1); Int->Pyr GABA cannot be programmed upward (API only zeroes it). So no stronger variant is possible within limits beyond a design with more shared interneurons.
* Failure stated plainly: every ripple case fails the pre-set success criteria because memory G1 (a 109-spike, 69 ms intrinsic burst; 3.2 ms interspike slowing, ends without inhibition in NI) does not terminate within 40 ms; the shuffled order (G1 last) also ends at 117 ms > 100 ms. Recall itself (4/4, <= 4.64 ms, no cross-talk, no spurious spikes) works in every pruned (bg 0) run, and the 3-cell cue never completes a memory. Cross-inhibition was never strong enough to veto another memory.
* Background connectivity: not tolerated. Even 0.03 (3% of grown weight, on ~97% of pairs) gives spurious non-member pyramidal firing (113 spikes in single recalls, 59 in the ripple), 80 cross-talk events, ~50 interneuron spikes per recall; at 0.05 worse (144 spurious). Completion still 4/4, but recall is no longer selective. Tolerance threshold lies below 0.03.

## 5. Vm / rasters
`raw_E1.json` runs `o0123s12_dt1` (best), `o0123s20_dt1` (worst: ends 93.8), `o0123s12_dt0.1`, `o0123s20_dt0.1` (window -5..110 ms; 32 memory pyr cells + interneurons that fired + 8 most driven). Figures: fig_E1_best_dt1.png, fig_E1_worst_dt1.png, fig_E1_best_zoom_dt0.1.png (8-28 ms), fig_E1_worst_zoom_dt0.1.png (54-74 ms). Best/worst chosen a priori by spacing (not post hoc), all runs equally "complete".

## 6. Bio limits (`bio_audit.json`)
Growth hard limits pass (bio_check; soft warnings: density, pyramidal fraction 0.667, separation vs soma); D_synmax 1.5/0.1 has no approved range. Programmed weights in [0,1] (max 1.0). Pyr->Pyr: 5533 pairs programmed, 5387 = 97.36% set to 0 (bg 0), 6 in 0.05-0.1, 140 in 0.1-1; Pyr->Int 569 all in [0.93,1] (NI: all 0). With bg 0.03: 0.47% zero, 5367 at 0.03 (below the 0.1 floor if read as a per-synapse limit). Strict reading breached by the pruning as before; Int->Pyr/Int->Int GABA unprogrammable (0.2), NMDA on programmed pairs zeroed. In SG GABA weights were zeroed through the API quirk (a control, not a bio configuration).

## 7. Bookkeeping
25 simulations (ids 139-163): E1 single 1 + ripple 7, NI 6, SG 4, ES 3, bg0.03 2, bg0.05 2. All deleted with DeleteResidentByID right after use (StatusCode 0); GetStatus on 139-163 afterwards returns StatusCode 2 (not found) for all. No saved model or earlier folder modified.
