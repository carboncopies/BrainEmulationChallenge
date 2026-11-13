# Ripple / multi-memory recall on bio-consistent arbor config A (saved NES model `v2-arbor-A0000`)

Network: 96 pyramidal + 48 interneurons, D_synmax pyramidal 1.5 um, interneuron pairs 0.1 um, interneuron basal dendrites 4-8
(10/48 interneurons drivable, 0.57% inhibitory synapses). Own NES (localhost:8000). Fresh simulation per case,
ModelLoad then apply-then-run in the same session (no ModelSave), STDP off, 1 deterministic run per case, read back every
programmed pair (5855 Pyr->Pyr + 385 Pyr->Int, 0 mismatches), RAM >= 335 GB throughout. Reused from ripple_05: build_pairs
(18 nS cue, noncue->noncue, pruning), Pyr->Int rule, group selection by modelled cross-inhibition (E1), cue protocol
(4 cue cells at +0/0.5/1.0/1.5 ms), cases (12/16/20 ms spacing order G0-G3, shuffled G2,G0,G3,G1 at 16 ms), success criteria.

## What was done
* Groups (`design_K4.json`, `design_sa.py`): 4 disjoint 8-cell memories (4 cue + 4 non-cue), simulated annealing, hard constraint
  every cue->non-cue pair >= 4.5 nS (so the 18 nS cue works with weight <= 1), interneurons restricted to the 10 drivable ones
  (total pyramidal input >= 13.84 nS: ids 129,117,128,134,131,99,113,105,141,98). In arbor A only interneuron 129 gets
  >= 16 nS from a memory (16.7-17.8 nS), so the model predicts one interneuron spike per recall and near-zero cross-inhibition.
  The ripple_05 requirement of an interneuron with >= 25 nS drive could not be met (relaxed to 16 nS).
* E1 = these groups + standard Pyr->Int rule (feedback inhibition on). NI = same groups, all Pyr->Int zero (no dependence on
  inhibition; Int->Pyr GABA 0.2 is not programmable but nothing excites the interneurons).
* 16 simulations: E1 single-memory (1), E1 ripple Dt 1 ms (4), E1 ripple Dt 0.1 ms (4), NI single (1), NI ripple Dt 1 (4), NI Dt 0.1 (2).

## Results (all cases, success = every non-cue member spikes within 10 ms of its cue, 0 cross-talk, 0 non-member pyramidal spikes, last spike <= 100 ms after first cue, no burst > 40 ms, nothing in last 10 ms of 150 ms run)
| variant | case | dt | memories complete (4/4 each) | max latency ms | burst end after own cue (G0..G3 order of cueing) ms | int spikes per event | last spike after 1st cue ms | result |
|---|---|---|---|---|---|---|---|---|
| E1 | single memory, 4-cell cue | 1 | G0-G3 all 4/4 | 4.03 | 8.4 / 32.9 / 26.7 / 34.8 (11/40/40/53 member spikes) | 1/3/4/4 | - | OK |
| E1 | single memory, 3-cell cues (a,b per group) | 1 | 0/4 in all 8 events | - | - | 0 | - | OK (no false completion) |
| E1 | 4 memories sep 12 | 1 | 4,4,4,4 | 4.04 | 8.4/32.9/26.7/34.8 | 1,1,4,11 | 70.8 | success |
| E1 | sep 16 | 1 | 4,4,4,4 | 4.04 | same | 1,1,6,6 | 82.9 | success |
| E1 | sep 20 | 1 | 4,4,4,4 | 4.04 | same | 1,3,6,2 | 94.9 | success (only 5 ms inside the 100 ms limit; the last cue is at 60 ms) |
| E1 | shuffled G2,G0,G3,G1 sep 16 | 1 | 4,4,4,4 | 4.05 | 26.7/8.4/34.9/32.8 | 3,4,1,8 | 80.8 | success |
| E1 | same 4 cases | 0.1 | all 4/4 | 4.41-4.43 | 15.6-36.1 | 1-12 | 67.8 / 79.8 / 91.7 / 83.6 | success |
| NI (Pyr->Int = 0) | single memory 4-cell / 3-cell | 1 | 4/4 each; 3-cell 0/4 | 4.03 | identical to E1 (11/40/40/53 member spikes) | 0 | - | OK |
| NI | sep 12 / 16 / 20 / shuffled | 1 | all 4/4 | 4.03 | 8.4/32.8/26.7/34.9 | 0 | 70.9 / 82.9 / 94.9 / 80.8 | success |
| NI | sep 12 / sep 20 | 0.1 | all 4/4 | 4.41 | 15.6-32.9 | 0 | 67.7 / 91.7 | success |

Every one of the 16 simulations succeeded by the criteria. Full per-case numbers: `summary.json`; rasters, per-neuron
spike times, analysis: `raw_E1.json`, `raw_NI.json`.

Best case (E1 sep 12, ends at 70.8 ms) and worst case (E1 sep 20, ends 94.9 ms, closest to the limit): spike rasters and Vm of all 32
memory pyramidal cells plus the 8 most-driven interneurons and every interneuron that fired are stored in `raw_E1.json`
(`runs.o0123s12_dt1`, `runs.o0123s20_dt1` at Dt 1 ms; `runs.*_dt0.1.vm` at Dt 0.1 ms; window -5..+110 ms; Vm samples clamped
at +30 mV on spikes). Figures: `fig_E1_best_dt1.png`, `fig_E1_worst_dt1.png`, `fig_E1_best_zoom_dt0.1.png` (8-28 ms),
`fig_E1_worst_zoom_dt0.1.png` (54-74 ms).

## Honest reading (what the result does and does not mean)
1. Recall and ripple work here, but NOT because of inhibition. E1 and NI give nearly the same pyramidal spike times (single-memory
   member spike counts are identical, 11/40/40/53, with 0 interneuron spikes in NI; burst ends differ by < 0.2 ms at Dt 1). Removing
   all excitatory drive to interneurons changes nothing material. The arbor-A inhibition is too weak to matter either way.
   The ripple_05 mechanism (cross-inhibition from the previous memory vetoing the next one) cannot occur: the cross-inhibition
   model gives 0.8 nS spike-weighted max and no recall was suppressed. The earlier E1-E4b "robust ripple" result is reproduced
   in outcome but not in mechanism; this is a recurrent-excitation-only memory with no meaningful inhibitory control.
2. Burst termination is intrinsic. Each recalled memory fires a train of 1-10 spikes per cell with slowing interspike intervals
   (about 2.3 ms to 5 ms) lasting 8-35 ms (G1 33 ms, G3 35 ms) and then stops with no inhibition (NI). All runs ended within 95 ms of
   the first cue and nothing fires in the last 10 ms of the 150 ms run. Bursts are much longer than a clean single-spike recall
   (G3: 53 spikes from 8 cells in one recall); a burst of 35 ms is not a ripple-like 5 ms event. This is a weakness, not a success of the design.
3. Spurious activity: none in pyramidal cells (0 non-member pyramidal spikes, 0 cross-talk in all 16 sims). Interneuron 129 fires
   repetitively (up to 11 spikes, ISI 4-5 ms, until 72 ms) and 5-8 other drivable interneurons fire 1-2 spikes; this is the only
   non-memory activity and it is driven by the memories (E1 only; 0 in NI).
4. Dt dependence: Dt 0.1 ms gives longer bursts (up to 36 ms vs 35 ms; G0 15.6 vs 8.4 ms) and 30 more spikes but the same completion.
5. Not tested: >4 memories, other seeds/geometries, K=3 sub-tests, NMDA, STDP, jitter tolerance, an unprogrammed (as-grown) control
   on arbor A, whether the groups chosen for low cross-inhibition matter (they probably do not, given point 1). One run per case
   (NES is deterministic). Spacing 12-20 ms is the only range tried; the 100 ms limit is only 5 ms away at sep 20.

## Bio-limit check (`bio_audit.py` -> `bio_audit.json`)
* Growth parameters of arbor A (days 25, 96/48 neurons, minneuronseparation 10, radius 120, thickness 30, dm.weight 0.9) pass
  `bio_check.assert_hard_limits`. Soft warnings: density, pyramidal fraction (96/144 = 0.667 < 0.7) and separation vs soma size.
  D_synmax 1.5/0.1 has no team-approved range in bio_ranges.json (as stated in earlier notes).
* Programmed weights (conductance / g_peak_sum): all within [0, 1] (max 1.0, none above 1). E1: Pyr->Pyr 5855 pairs: 5715 set to 0
  (pruning), 8 between 0.052 and 0.1, 132 in [0.1, 1]; Pyr->Int 385 pairs all in [0.93, 1]. NI: Pyr->Int all 0.
* LIMIT BREACH, stated plainly: if dm_weight 0.1-1.0 is read as a limit on each synaptic weight, 5715 (97.6%) of programmed
  Pyr->Pyr weights are 0 and 8 are in 0.05-0.1, so the pruned memory-specific wiring violates it (and in NI all 385 Pyr->Int
  are 0). dm.weight is a growth parameter (axon guidance), not a per-synapse weight, and it was within limits at growth, so this is
  a breach only under the strict reading. The 97.6% pruning of Pyr->Pyr itself is the biologically unrealistic part of the recipe.
* Not programmable and left at as-grown 0.2: Int->Pyr and Int->Int GABA. NMDA on programmed Pyr->Pyr zeroed by the API.

## Files
`alib.py` (library), `design_sa.py` (+ `design_sa.log`, `design_K4.json`), `run_arbor.py` (usage: `run.sh run_arbor.py E1 single rip:NAME:ORDER:SPACING:DT[:r]`),
`analyze.py` (-> `summary.json`, figures), `bio_audit.py`, logs `run_E1.log run_E1b.log run_NI.log run_NIb.log`.
Run with the NES venv via `../ripple_05/run.sh`. Pristine saved models and ripple_05 files untouched.

## Simulation bookkeeping
16 simulations created (ids 116-131), 16 deleted with DeleteResidentByID right after reading (all StatusCode 0, 0 delete failures).
