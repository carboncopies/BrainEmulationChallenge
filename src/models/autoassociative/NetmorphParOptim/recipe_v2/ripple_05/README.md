# Ripple-style multi-memory recall -- SENSITIVITY STUDY, D_synmax 0.5, NOT BIO-REALISTIC

Network: existing saved model `fable-it1a-sim133` (seed 20240628, 94 neurons: 67 pyramidal, 27 interneurons; interneuron
D_synmax 0.5 um, above the team's smooth-dendrite maximum of 0.1-0.15 um). Run only to see whether feedback inhibition
can terminate successive recalls. Pristine model never modified (fresh_copy of a new simulation each case, then
`DeleteResidentByID` right after reading; 18 sims created, 18 deleted, one at a time, 30 s pauses). STDP off. All programmed
weights in [0,1] (asserted). RAM stayed >= 349 GB (guard 100 GB).

## Design
* K=4 disjoint 8-cell memories = first four groups of `recipe/sweep_designs.json` `K_groups` (G0..G3; G0-G2 identical to the
  verified recipe groups; G3 = members 16,24,25,35,45,48,56,64, cue 16,45,56,64). Programmed with `recipelib.build_pairs`
  (same rule as `recipe/`: cue->non-cue 18 nS/4, non-cue->non-cue, non-cue->cue as grown, all other Pyr->Pyr 0, Pyr->Int on with
  cue cells capped at 10 nS). The 5th group is not programmed. Programming read back and verified for all 3,000+ pairs.
* Cue: 4 cue cells at +0, +0.5, +1.0, +1.5 ms (SetSpecificAPTimes) at onsets 0, S, 2S, 3S (S = 12, 16, 20 ms), run 150 ms (Dt 1 ms).
  Shuffled order: G2, G0, G3, G1 at 0/16/32/48 ms.
* Success per memory: all 4 non-cue members spike within 10 ms of their cue. Cross-talk: member of a memory spikes before its cue.
  Ripple success: all complete, no cross-talk, all activity ends <= 100 ms after first cue.
* Only changes vs recall_test.py defaults: the 1.5 ms cue spread (recall_test uses simultaneous cues); the diagnostic cases
  below (simultaneous cues; other orders; 2-memory runs) are labelled `diag_`. No weights were tuned.

## Commands
`ripple_05/run.sh run_main.py` (main cases + baselines + control), `run.sh run_extra.py` (diagnostics), `run.sh run_vm.py`
(Vm), `python3 assemble.py` (builds ripple_data.json, ripple_vm.json). `run.sh` = NES venv python with PYTHONPATH set.
Library: `ripple_lib.py`. Raw: `raw_main.json`, `raw_extra.json`, `ripple_vm_full.json` (identical to ripple_vm.json content).

## Results (Dt 1 ms raster; latency = last non-cue member's first spike after its cue)
| case | memories completed (non-cue fired /4) | latencies ms | cross-talk | spurious non-member pyr spikes | interneuron spikes per event window | last spike (ms) | ripple |
|---|---|---|---|---|---|---|---|
| sep 12, order G0-G1-G2-G3 | 4,3,4,4 | 4.0, fail, 4.6, 4.3 | 0 | 0 | 11,13,3,8 | 43.9 | FAIL (G1 3/4) |
| sep 16 | 4,1,4,4 | 4.0, fail, 4.3, 4.3 | 0 | 0 | 14,9,6,6 | 55.9 | FAIL (G1 1/4) |
| sep 20 | 4,2,4,4 | 4.0, fail, 4.2, 4.2 | 0 | 0 | 17,8,7,4 | 73.3 | FAIL (G1 2/4) |
| sep 16, order G2-G0-G3-G1 | 4,4,4,4 | 4.0, 4.3, 4.5, 4.7 | 0 | 0 | 4,13,9,9 | 66.9 | success at Dt 1 ms, but NOT at Dt 0.1 (see below) |
| single G0 / G1 / G2 / G3 | 4/4 each | 4.0 | 0 | 0 | 19 / 13 / 4 / 7 | 21.1 / 18.3 / 8.5 / 15.3 | ok |
| control, no programming, sep 16 | 4 x 4 (runaway) | 1.6-2.8 | 117 early member spikes | 840 (25 cells) | 18,24,17,70 | 148.9 (still active at run end) | FAIL (runaway) |
Diagnostics (all failures with G1 at +16 ms after G0): simultaneous cues sep16 -> G1 1/4; order G1,G0,G2,G3 sep16 -> G1 fine, G0 0/4;
2 memories G0->G1 at +16: G1 1/4, at +32: 4/4, at +48: 4/4 (success).

## Findings
* Pyramidal-side spurious activity is nil in programmed runs: 0 spikes from non-member pyramidal cells in every programmed case;
  no memory fired before its cue (no cross-talk). Members do re-fire: each recalled memory bursts 3-6 spikes per cell over 8-20 ms
  (median burst length 8-16 ms; G0 alone 20 ms) before it dies; 12-31 member spikes fall after the 10 ms recall window per case.
  Bursts are therefore longer than a clean single-spike recall.
* Inhibition does terminate each burst. Interneurons (up to 6 fire per memory, 4-19 spikes per event; ids 89 and 93 carry most)
  start firing ~6 ms after the cue, fire at 2-3 ms intervals, and the pyramidal burst stops 8-20 ms after the cue. Total activity ends 21-67 ms
  after the first cue for the programmed runs (limit 100 ms met in all). Control without programming: runaway (2026 pyramidal spikes,
  still active at 149 ms, all memories overlap).
* But inhibition is the failure mechanism for ripples: it is too slow/strong in the wrong place. A recall's interneuron volley lasts
  ~20-25 ms and G0's interneurons deliver 32 nS mean GABA to G1's non-cue members (vs 16 / 13 nS to G2 / G3; G1 is
  the most inhibition-exposed memory; `inhibition_matrix` in ripple_data.json). With S = 12-20 ms the next memory's cue lands inside this window: G1 members rise to only
  -51 mV, never spike (Vm peaks about -50.7 / -51.6 mV for members 39/41 in the fail case; threshold not reached) -> recall is suppressed.
  At S = 32 or 48 the 2-memory G0->G1 works. Moving G1 first (G1,G0,...) makes G0 fail, so the suppression is memory/order dependent
  (not a G1 defect). G2 and G3 recall fully at all separations after G0/G1/G2. Result: 3 of 4 memories work at any separation tested; a clean 4-memory
  ripple at 12-20 ms spacing in order G0..G3 does NOT work.
* K=3 was not run separately; the K=4 failure is only at G1 after G0, so K=3 with G0,G2,G3-like orderings would likely work, untested.
* No lingering depolarisation outside members/interneurons: bystander pyramidal cells stay at -70.0 mV; uncued members sit at -70 to -74 mV.
  Interneurons 89/93 stay active/depolarised (mean Vm about -41 to -57 mV after 40 ms) and keep spiking at 39-60 ms in some cases;
  these late interneuron spikes are the only spurious activity beyond the bursts.
* Anomaly / caveat (important): results are not Dt-invariant. At Dt 0.1 ms the shuffled-order "best" case loses G0 (0/4 non-cue; G2,G3,G1
  4/4) and the failing sep-16 case still fails at G1 (1/4) with 121 vs 101 spikes (Dt 0.1 produces extra spikes
  in 15 neurons). The shuffled success is thus marginal (G0 at +16 after G2 barely above threshold) and the Dt 1 ms raster is the
  specified one. Spike counts at Dt 1 ms in the Vm run match the raster run exactly (101 and 113 spikes, deterministic).
* Why the ripple does not work (hypotheses supported by data): (1) feedback inhibition is strong and slow enough
  (interneurons fire for ~20 ms) to veto a second memory within 12-20 ms; (2) the margin of cue->non-cue drive (18 nS vs about 15 nS threshold) is small, so
  GABA of ~30 nS onto G1 prevents firing; (3) each memory's own burst (3-6 spikes per cell) is longer than the target single-spike recall.
  STDP is off (not tested whether it matters) and NMDA is zeroed on programmed pairs by the API (not tested whether NMDA would help).

## Membrane potentials (`ripple_vm.json`)
Window -5..+110 ms around first cue, cases `fail_sep16_order0123` (G1 fails) and `best_sep16_shuffled_2_0_3_1`, each at Dt 0.1 ms
(1151 samples) and Dt 1 ms (116 samples; spikes identical to raster). 23 neurons: per memory the first cue cell + 2 non-cue members
(roles in `neurons`), 8 interneurons with highest programmed drive from members (ids 89, 93, 82, 80, 79, 77, 76, 90; drive nS and GABA conductance to members in
`interneuron_selection`), 3 bystanders (31, 15, 13). Vm rounded to 0.1 mV, no subsampling; spike samples are clamped at +30 mV by the simulator.
File size ~0.37 MB. `spikes_all_neurons` gives precise spike times (relative to first cue) for cross-checking with the raster.
