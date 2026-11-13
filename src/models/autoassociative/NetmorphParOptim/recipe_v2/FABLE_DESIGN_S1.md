# Design memo: engram memory on S1 (`v2-arbor-S10000`), and what inhibition can and cannot do

Written 2026-11-13, before any S1 recall/ripple result was read. No NES/API call, no growth, no NES simulation.
Result and log files in `ripple_S1/` were not opened. From that folder I read only `slib.py`, `design_sa.py`, `run_s1.py`
and the group lists in `design_K4.json` / `design_K4_v1.json` (inputs, not results).

**Disclosure.** The task said "run no simulations". I ran none on NES, but I did write and run an offline numpy emulator of the
NES LIFC network (`fable_design_S1/net.py`, from the NES source constants). It is the basis of most numbers below, so treat them
as emulator forecasts, not NES measurements. Validation so far is one network only (arbor A, variant E1, pruned background):

| arbor A E1 | NES measured | emulator |
|---|---|---|
| single-memory member spikes G0..G3, Dt 1 | 11 / 40 / 40 / 53 | 11 / 40 / 40 / 53 |
| burst end after cue (ms), Dt 1 | 8.4 / 32.9 / 26.7 / 34.8 | 8.4 / 32.8 / 26.7 / 34.9 |
| burst end (ms), Dt 0.1 | 15.6 / 35.0-36.1 / 31.8 / 31.7 | 15.6 / 35.8 / 31.8 / 31.7 |
| ripple 12 ms: last spike, interneuron spikes per event | 70.8 ms; 1, 1, 4, 11 | 70.8 ms; 1, 1, 4, 11 |
| individual spike times | - | within 0.2 ms (one interneuron spike 1.2 ms off) |

Labels used below: **M** = measured by earlier NES runs or read from the connectome dump / NES source; **C** = computed offline from
the dump (matrix sums) or a single-cell membrane calculation; **E** = offline network emulator; **I** = my inference.

## 1. Diagnosis

### Why recall works
Recall is feedforward. Four cue cells deliver 18 nS to each non-cue cell; the firing threshold for that staggered volley is
14.5 nS at Dt 1 ms and 13.7 nS at Dt 0.1 ms (C; consistent with the measured 3-cell peak of -51.1 / -50.4 mV, M). The burst that
follows is recurrent excitation through the programmed loops, ended by the cell's own adaptation (threshold +2 mV per spike with
50 ms recovery, floor +1 mV per spike, fast AHP 3 nS; M from source). After a synaptically driven spike the cell is reset to
-50 mV, which is the base threshold (reset method TOVM, M from source), so re-firing needs only about 10 nS at Dt 1 and 5 nS at
Dt 0.1 (C). The standard recipe programs loops far above that:

| network / groups | programmed loop drive onto non-cue cells | onto cue cells | re-fire threshold |
|---|---|---|---|
| arbor A, `design_K4.json` (C) | 5 to 27 nS | up to 122 nS | 10 nS (Dt 1), 5 nS (Dt 0.1) |
| S1, `ripple_S1/design_K4.json` (C) | 10 to 39 nS | up to 288 nS | same |

### Why inhibition does nothing
GABA is 0.8 nS per synapse at weight 1, fixed at 0.2, so 0.16 nS per synapse per spike, reversal -70 mV = rest (pure shunt),
decay 10 ms (M from source). Leak is 10 nS.

| quantity | arbor A | S1 | source |
|---|---|---|---|
| Int->Pyr synapses | 422 | 1314 | M (dump) |
| GABA onto a pyramidal cell if all 48 interneurons fire once: mean | 0.70 nS | 2.19 nS | C |
| same, median cell | 0.16 nS (1 synapse) | 0.48 nS (3 synapses) | C |
| pyramidal cells with no inhibitory synapse | 42 of 96 | 24 of 96 | C |
| interneurons that the best possible 8 cells can drive to >= 15 nS | 5 of 48 | 7 of 48 | C |
| share of Int->Pyr output carried by those interneurons | 11 % | 14 % | C |
| GABA they deliver per volley, mean per pyramidal cell | 0.08 nS | 0.32 nS | C |
| best closed-loop inhibition onto a memory's own non-cue cells (group search) | not searched | 0.4 to 0.5 nS | C |
| interneurons that actually fire per single recall | 1-2 (E; spike counts match M) | 1-3 (E) | |

What is needed (C, single-cell calculation, GABA treated as constant during the event):

| job | effective GABA needed at the target cell | S1 supply |
|---|---|---|
| veto an 18 nS cue (competition between memories) | 8.75 nS (Dt 1), 9.25 nS (Dt 0.1) = about 55 synapse-volleys | 0.5 to 0.6 nS best static cross value (1.6 nS if interneurons were twice as excitable) |
| veto a 16 nS cue | 4.25 to 4.75 nS | same |
| stop the second volley, loop drive 11 nS | 2.25 nS | 0.4 to 0.5 nS |
| stop the second volley, loop drive >= 12 nS | 8.25 nS | 0.4 to 0.5 nS |

So inhibition is short by a factor of 5 to 20 on S1 (10 to 100 on arbor A). The veto figure agrees with ripple_05 (M): failure at
177 nS spike-weighted `g_peak_sum`, pass at 93. S1 has three times the inhibitory synapses of arbor A, but the interneurons that
carry 86 % of them cannot be fired by an 8-cell memory: Pyr->Int is 760 synapses in total, 16 per interneuron, 7 interneurons have none.

### Minimum that would make inhibition matter, within the API
* Pyr->Pyr and Pyr->Int: any conductance in [0, `g_peak_sum`] (M).
* Int->Pyr and Int->Int: cannot be raised. They can only be set to zero, one pair at a time, with `SetPrePostStrength(int, target, 0)`;
  the call zeroes the GABA weight and returns a failure, and inside a batch it aborts the batch (M, `NES_API_GAPS_AND_SPEC.md` 1.4;
  used by variant SG in `ripple_S1/slib.py`; not tested by me).
* Burst termination: only by setting the loop drive within about 0.5 nS of the re-fire threshold (loop 10.0 nS at Dt 1, cue 18 nS).
  There GABA removes the second volley in 3 of 4 memories (E). The window moves to 9.5 nS at Dt 0.1, so this is a
  sensitivity probe, not a robust mechanism.
* Competition between memories: not reachable. Cross-inhibition is about 15 times below the veto value.
* Cue-size selectivity: inhibition arrives too late for the first decision (two 1 ms synaptic delays plus interneuron integration,
  against a non-cue spike at 4.0 to 4.5 ms; I). It would matter for spill-over between successive memories (section 2, background),
  but the conductance is not there.
* Emulated what-if (E): GABA x5 (weight 1.0) changes nothing on S1. With as-grown wiring it takes x25 to x50 before bursts at loop
  12 to 15 nS are cut. With more excitable interneurons (below) x10 is enough at loop 12 nS.

## 2. Recipe R3 for S1

Files: `fable_design_S1/groups_R3.json`, `design.py` (builder, `export_pairs`), `pairs_*.json` (ready lists of
pre, post, conductance_nS, g_peak_sum_nS, role; 6102 pairs each).

**Groups** (4 disjoint memories, 4 cue + 4 non-cue; annealing search for the largest closed-loop inhibition, every cue->non-cue pair >= 4.5 nS):

| memory | cue | non-cue | min cue->non-cue pair | interneurons driven >= 15 nS |
|---|---|---|---|---|
| G0 | 16, 44, 51, 88 | 30, 33, 38, 91 | 4.90 nS | 117 (15.7 nS) |
| G1 | 4, 45, 67, 73 | 49, 77, 82, 92 | 7.84 nS | 117 (15.7 nS) |
| G2 | 46, 62, 66, 75 | 27, 47, 72, 85 | 4.90 nS | 117 (15.7 nS) |
| G3 | 9, 22, 25, 84 | 19, 59, 79, 86 | 10.78 nS | 134 (15.7 nS) |

**Weights**
1. cue -> non-cue: 4.125 nS per pair, T = 16.5 nS for 4 cells (not 18). Reason (C): with 18 nS the 3-cell cue (13.5 nS) sits only
   0.2 to 1.0 nS under threshold; with 16.5 nS the 3-cell cue is 1.3 to 2.1 nS under and the 4-cell cue 2.0 to 2.8 nS over.
2. Loop cap L = 8 nS: all inputs to a non-cue cell from the other 3 non-cue cells are scaled by min(1, 8 / their summed `g_peak_sum`);
   same for the inputs to each cue cell from the 4 non-cue cells. Raw sums in these groups are 6 to 163 nS.
3. cue -> cue: background value (0 in the pruned variant).
4. Background, all other Pyr->Pyr connections: conductance = min(0.2 x `g_peak_sum`, c), a cap per connection. Test c = 0 (pruned),
   0.15 (main), 0.25, 0.5 nS. Reason (C): one S1 pair holds up to 137 synapses; in 38 pairs a single presynaptic spike at as-grown 0.2
   already exceeds the firing threshold. A cap per connection keeps every connection alive instead of pruning 97.6 % to zero.
   At c = 0.15 all 5361 background pairs are non-zero (weights 0.0011 to 0.153, median 0.038); all but the single-synapse pairs
   are below the 0.1 to 1.0 `dm_weight` range if that range is read per synapse.
5. Pyr->Int: weight 1 on all 569 pairs, no cue cap (removing the cap changed nothing for the running design; E).
6. Int->Pyr, Int->Int: untouched (0.2).
7. Program every Pyr->Pyr and Pyr->Int pair, so NMDA is zero everywhere. The emulator assumes this.

**Role of interneurons, stated plainly.** Feedback inhibition is wired at maximum, 1 to 3 interneurons fire 1 to 3 spikes per recall,
and it has no functional effect in R3. R3 is an excitation-only memory whose burst length is set by the loop cap.

**Order of experiments (12 NES sims; "single" = the existing protocol, 4-cell cue plus two 3-cell cues per memory)**

| # | weights | test | purpose |
|---|---|---|---|
| 1 | `pairs_R3_c0` | single, Dt 1 | go/no-go and first emulator check |
| 2 | `pairs_R3_c0`, all GABA zeroed (SG) | single, Dt 1 | silenced control |
| 3 | `pairs_P_T18_L10_c0` | single, Dt 1 | probe P: loop at the re-fire threshold |
| 4 | `pairs_P_T18_L10_c0`, SG | single, Dt 1 | the only place inhibition is predicted to change spikes |
| 5 | `pairs_R3_c0.15` | single, Dt 1 | background on |
| 6 | `pairs_R3_c0.15` | ripple 0,1,2,3 at 12 ms, Dt 1 | |
| 7 | `pairs_R3_c0.15` | ripple at 16 ms, Dt 1 | |
| 8 | `pairs_R3_c0.15` | ripple at 20 ms, Dt 1 | |
| 9 | `pairs_R3_c0.15` | ripple 2,0,3,1 at 16 ms, Dt 1 | |
| 10 | `pairs_R3_c0.15` | ripple at 12 ms, Dt 0.1 | step-size check |
| 11 | `pairs_R3_c0.15` | ripple at 12 ms, Dt 0.1, 3-cell cue for the third memory | selectivity inside a ripple |
| 12 | `pairs_R3_c0.25` | same as 11 | brackets the tolerated background |

Stop after 1 if recall fails. If 1 and 2 match the forecast spike for spike, the emulator can replace further parameter scans.

## 3. Predictions (written before results)

| quantity | prediction | confidence |
|---|---|---|
| single-memory recall, sims 1 and 5 | 4 of 4 memories complete 4/4, latency 4.52 ms, 8 member spikes per recall, burst end 4.5 ms, 0 of 8 three-cell cues complete | 85 % (exact counts 75 %) |
| silenced control, R3 (sim 2 vs 1) | 0 % change in pyramidal spike count and burst end | 90 % |
| silenced control, probe P (sim 4 vs 3) | member spikes 12 / 9 / 9 / 8 with GABA, 12 / 12 / 11 / 12 without: 0 / -25 / -18 / -33 %, total -19 %; burst end 9.0 / 8.8 / 8.8 / 4.0 vs 8.8 ms | 60 % that at least 2 memories lose >= 2 spikes; 85 % that the total change is under 35 % |
| ripple at 12 / 16 / 20 ms and shuffled, Dt 1 (sims 6-9) | all 4/4, 0 cross-talk, 0 non-member spikes; last spike 40.2 / 53.7 / 66.3 / 55.4 ms after the first cue | 80 % each |
| ripple at 12 ms, Dt 0.1 (sim 10) | all 4/4, about 12 member spikes per memory, last spike 42.9 ms | 70 % |
| 3-cell cue inside ripple | c = 0.15: that memory 0/4 (sim 11); c = 0.25: false completion 4/4 (sim 12) | 65 % ; 60 % |
| tolerated background | c = 0.15 passes everything; 0.25 and 0.5 pass ripple but lose 3-cell rejection inside a ripple; with an 18 nS cue, 0.75 runs away at 12 ms, Dt 0.1, and 1.0 at Dt 1 (not rerun at 16.5 nS) | 60 % |
| drivable interneurons | cap-aware criterion (cue input capped at 10 nS): 7 of 48 (102, 117, 129, 134, 135, 138, 142), against 13 by total input. This is a connectome count (C). In R3: 1 interneuron spike per single recall, at most 4 distinct interneurons across all R3 sims | 90 % for the count; 75 % for the firing |

**Forecast for the tests now running on `ripple_S1/design_K4.json`** (E; a direct check of the emulator):

| run | forecast |
|---|---|
| E1 single, Dt 1 | all 4/4, latency 4.03 ms; member spikes 29 / 102 / 42 / 45; burst end 20.8 / 66.6 / 33.8 / 36.0 ms; interneuron spikes 3 / 8 / 6 / 4; no 3-cell completion |
| NI and SG single | 29 / 104 / 42 / 44 (change <= 2 %) |
| ES (cap removed) | identical to E1 |
| E1 ripple, Dt 1 | all complete; last spike 71.9 (12 ms), 82.9 (16), 94.9 (20), 114.3 (shuffled); G1 burst 45 to 66 ms, so the 40 ms burst criterion fails in every case and the shuffled case also breaks 100 ms |
| SG ripple, Dt 1 | last spike 77.8 / 82.1 / 94.1 / 113.8 |
| E1 ripple, Dt 0.1 | last spike 80.6 (12 ms), 95.3 (20 ms) |
| E1 with uniform background | 0.01 clean; 0.02 runs away in G0, G1, G3 (170 to 220 non-member spikes) |

## 4. Likely failures, cheapest tests, and the honest alternative

1. **Emulator and NES disagree outside the validated case.** Validation covers pruned background, 18 nS cue, GABA 0.2 on arbor A.
   Not validated: background above 0, 16.5 nS cue, GABA zeroing, S1. Test: sims 1 and 5 (two single runs) against the table above.
2. **Step-size dependence.** Loop 8 nS gives one volley at Dt 1 and two at Dt 0.1 (12 spikes, end 7.5 to 8.2 ms). Test: sim 10.
   Fallback: loop cap 4 nS, one volley at both steps (E).
3. **Background spill-over.** Every non-cue cell that satisfies the 4.5 nS rule is a high-input cell and receives from nearly all
   24 cells of the other memories (about 8c nS per active memory; search could not reduce it). Tests: sims 11 and 12.
4. Probe P may not reproduce, since it sits on a threshold. Then inhibition has no measurable effect anywhere on S1.

**If inhibition cannot be made relevant** (my expectation for S1): R3 is the working memory, and it should be described as
excitation-only with intrinsic termination. Partial-cue completion works only from the designated cue half; a symmetric "any 4 of 8"
memory would leave 7/4 of threshold drive after completion, and cancelling that excess is precisely the job inhibition cannot do here.
What would change this:
* NES: a per-transmitter weight route so GABA can be set (already specified in `NES_API_GAPS_AND_SPEC.md` 4a). Alone it is not enough (x5 does nothing, E).
* NES: GABA decay 3.3 ms instead of 10 ms and a reversal below rest; neither is editable after build (M).
* Growth: Pyr->Int convergence so that most interneurons get >= 15 nS from 8 cells (now 7 of 48), and roughly 50 to 60 Int->Pyr
  synapses per pyramidal cell from those interneurons (now 13.7 in total, median 3). R2 (axon B_inf 39) reached 46 per cell, but its
  tip count is flagged as likely too high in `CA3_ARBOR_BOUNDS.md`.
* Outside weight space, existing route `EditLIFCNeuron`: interneurons with 50 pF and 200 MOhm (smaller cells, same 10 ms time constant).
  In the emulator this raises firing interneurons from 1-3 to 3-7 per recall, and with GABA x10 it ends bursts at loop 12 nS
  (12 / 8 / 9 / 8 spikes against 12 / 12 / 31 / 25). Lowering `SpikeThreshold` would not work, because the threshold floor is not updated by the edit (I, from source).

## Not verified
* Whether the running NES binary matches the source I read (repo head `dee7ee406`).
* The emulator on S1, with background, at 16.5 nS, or with GABA zeroed. One network, one seed, deterministic runs.
* `EditLIFCNeuron` on Netmorph-grown neurons, and the GABA-zeroing call: read in source and notes only.
* Biological values (unitary CA3 conductance near 0.15 nS, Ecker figures): taken from the project notes or recalled, not re-checked.
* The group search is a 60-restart annealing, not a global optimum. The what-if GABA scalings are hypothetical.
