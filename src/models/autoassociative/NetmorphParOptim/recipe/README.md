# Netmorph autoassociative-memory recipe (BrainGenix-NES)

## STATUS: all tasks run on a fresh, own NES (2026-11-12); task A REPRODUCES the earlier results

The original shared NES was gone, so a fresh own API/NES was started by the chief of staff (sim ids restart from 0; the pristine
saved models on disk were only loaded, never modified). Each condition ran on a new simulation, one at a time, 30 s apart, memory guard
60 GB (about 360 GB available throughout), STDP off. One run per condition; NES was deterministic in the earlier repeats (not re-verified here).
- Task A (seed 20240628, D_synmax 0.5): 3344 pairs applied, all read back correctly (0 mismatches, weights 0.0-1.0, NMDA 0). 4-cell cue 4/4 for G0/G1/G2
  at latency 3.55 ms, 28/27/20 member spikes (identical to the earlier sim 139 run: 28/27/20, 3.55 ms), 2- and 3-cell cues 0/4, cross-pattern mixes 0, no other pyramidal spikes, 14/14 events clean. Reproduces.
- Control with no pruning/programming (as-grown weights 0.2): G0 and G2 cues run away (4/4 plus 14 other-pattern members, 33 other pyramidal cells, 1758-2902 spikes, still firing at 300 ms). The G1 control cue only fired 1 of 4 non-cue cells with 5 spikes (no run-away for that cue; I did not investigate why).
- Task C and D numbers: see the table below and RESULTS.json. Raw data: recall_results.json per seed, sweeps_results.json, logs sweeps.log.
- demo_data.json is in every seed folder (spike rasters for all 94 neurons per test case, types, 3D soma positions, engram weight matrices, control raster).

## What the recipe is
Take a grown Netmorph reservoir (94 neurons: 67 pyramidal, 27 interneurons; D_synmax 0.5 for interneuron pairs), then by
programming synaptic conductances only (no synapses created, STDP off, all weights in [0,1]) store K = 3 disjoint 8-cell
engrams, each with a 4-cell cue:
1. cue -> non-cue pairs: 4.5 nS each (4 cue cells deliver 18 nS to a non-cue cell: ~20% above the ~15 nS NES firing threshold; 3 cells deliver 13.5 nS, below it).
2. cue -> cue pairs: 0. non-cue -> non-cue: w_post * g with w_post = min(1, 27.44 / sum of cue input). non-cue -> cue: full as-grown.
3. Pruning: every other Pyr->Pyr pair is set to 0 (a background of even 0.03-0.05 leaks into other patterns).
4. Feedback-only inhibition routing: all Pyr->Int pairs weight 1, except presynaptic cue cells, scaled by min(1, 10 / C_gi) so a cue alone
   delivers <= 10 nS to any interneuron (interneurons then fire only after completion). Int->Pyr / Int->Int GABA stay at 0.2 (not programmable).
Programmed values are sent through `BatchSetPrePostStrength(pre, post, conductance_nS)`; weight = conductance / g_peak_sum, always in [0,1].

## How to reproduce (when NES is up at localhost:8000)
```
export PYTHONPATH=/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient
PY=/home/johnjose/BrainGenix/BrainEmulationChallenge/venv/bin/python
cd /home/johnjose/cos/netmorph_work/recipe
$PY seed20240628/apply.py          # NEW sim, ModelLoad('fable-it1a-sim133') copy, apply weights.json, read back every pair
$PY seed20240628/recall_test.py    # 14 test events + no-programming control; writes recall_results.json and demo_data.json
# other seeds: seed1001, seed1002, seed1003 (same two commands)
$PY run_sweeps.py                  # task C (K=1..5, group sizes 6/8/10), one fresh sim per condition, 30 s pauses
./RUN_ALL.sh                       # all of the above in order
```
Rules built in: only new simulation IDs (the guard was relaxed to any id because the server is a fresh own instance), pristine saved models are only loaded (never modified), memory check before
each run (< 60 GB available aborts), STDP off. Rebuild the json inputs offline with `python3 build_recipe.py <seed>`.

## Caveats (known, from the earlier experiments)
- AMPA only: the weight API zeroes NMDA on every programmed Pyr->Pyr pair.
- GABA weights fixed at 0.2 (not programmable); STDP off (with STDP on the earlier test did not hold up as a clean result - see FABLE_LOOP_LOG round 2 iteration 2).
- D_synmax 0.5 for interneuron pairs is a working value with no team-approved range in bio_ranges.json (not approved).
- Pruning of non-engram Pyr->Pyr is required (background >= 0.03-0.05 leaks; as-grown 0.2 runs away).
- Narrow cue window: T4 = 18 nS works, T4 = 20 nS was not selective, i.e. about +/-10-20% around threshold.
- Jitter tolerance: cue spikes spread up to 9 ms complete, 12 ms fails.
- One geometry per seed; engrams are chosen per seed (the 20240628 groups do not transfer). One run per condition; NES was deterministic in earlier repeats.

## Results table (measured 2026-11-12)
Clean = full cue completes 4/4 non-cue cells, sub-threshold cues complete 0, no other-pattern or other-pyramidal spikes.

| condition | events | clean | full-cue completion | sub-threshold false completions | leaks | notes |
|---|---|---|---|---|---|---|
| A seed 20240628 (K=3, 8 cells, cue 4) | 14 | 14 | 3/3, 3.55 ms | 0/9 | 0 | reproduces earlier sim 139 (28/27/20 spikes) |
| D seed 1001 | 14 | 14 | 3/3, 3.55 ms | 0/9 | 0 | member spikes 21/14/13 (earlier 21/14/13) |
| D seed 1002 | 14 | 14 | 3/3, 3.55 ms | 0/9 | 0 | 27/27/12 |
| D seed 1003 | 14 | 14 | 3/3, 3.55 ms | 0/9 | 0 | 22/32/34 (earlier 22/32/33) |
| C K=1 | 4 | 4 | 1/1 | 0/3 | 0 | |
| C K=2 | 10 | 10 | 2/2 | 0/6 | 0 | |
| C K=3 | 14 | 14 | 3/3 | 0/9 | 0 | |
| C K=4 (extra group min pair 7.84 nS) | 18 | 18 | 4/4 | 0/12 | 0 | |
| C K=5 (extra group min pair 4.90 nS) | 22 | 22 | 5/5 | 0/15 | 0 | 5 is the maximum by the design rule (6th group only 2.94 nS < 4.5 nS needed); K=6 not attempted |
| C size 6 (cue 3) | 12 | 12 | 3/3 | 0/9 | 0 | 2-cell cues also 0 |
| C size 8 (cue 4) | 14 | 14 | 3/3 | 0/9 | 0 | |
| C size 10 (cue 5) | 12 | 12 | 3/3 | 0/9 | 0 | 4-of-5 cue delivers 14.4 nS, which still did not fire here; this is close to the ~15 nS threshold, so it is fragile |

Nothing broke inside the tested range. K above 5 is not possible with this rule on this 67-pyramidal-cell network; group size above 10 and
size 10 robustness (margin of only ~0.6 nS below threshold) were not tested. Jitter, STDP and background-weight tolerance were not re-run here (see FABLE_LOOP_LOG).
Controls (no programming), seeds 1001/1002/1003: two of three cues run away in each seed except seed 1002 where all three run away; the other cue stays near silent (0-1 non-cue cells, 5 spikes) in seeds 20240628/1001/1003.

## Membrane-potential (Vm) traces (added 2026-11-12)
Recording method: `Simulation.RecordAll(-1)`, `RunAndWait(Runtime_ms, Dt_ms)`, then `GetRecording()` returns `{t_ms, neurons{id:{Vm_mV}}}` (soma Vm of
every neuron, one sample per step; LIFC cells are single-compartment so soma is the only Vm available; there is no read-back API for neuron
parameters, so rest/threshold are taken from the NES source defaults and confirmed in the traces: rest -70.0 mV, base threshold -50 mV, spike peak 30 mV,
absolute refractory 2 ms, post-spike undershoot about -74.5 mV; the threshold is adaptive in the simulator).
```
PYTHONPATH=<PythonClient> <venv>/bin/python seed20240628/vm_traces.py            # Dt 1 ms (same as the rasters) -> vm_traces.json
PYTHONPATH=<PythonClient> <venv>/bin/python seed20240628/vm_traces.py --dt 0.1   # finest step tried -> vm_traces_dt0.1.json
```
Each case runs in a NEW simulation (fresh copy of fable-it1a-sim133, weights.json applied with read-back check, cue at sim t=20 ms, 70 ms run), the data is read, and the
sim is deleted with `DeleteResidentByID` (own sims only). The 16 sims from the earlier recipe runs (ids 0-15) were also deleted. Cases: (a) G0 4-cell cue, (b) G0 3-cell cue
[22,29,51], (c) G0 4-cell cue on the unpruned/unprogrammed model, (d) G1 4-cell cue. Recorded per case: the 8 members, the 6 interneurons with the strongest Pyr->Int drive from the
members that also project back to them (selection and GABA conductances are in `interneuron_selection`; G0: 89, 93, 77, 82, 80, 90; G1: 89, 93, 82, 79, 80, 77), and 2 bystander pyramidal cells
(G0: 48 and 31, the ungrouped cells with the largest as-grown input from G0; G1: 48 and 35). Times are ms relative to the first cue spike; Vm rounded to 0.1 mV, no subsampling (file sizes 52 KB / 327 KB).
Findings: the Dt 1 ms spike times match demo_data.json exactly (max difference 0.002 ms; non-cue members first spike at 3.55 ms). Peak Vm of the G0 non-cue members before their first spike: 4-cell case
-52.0 mV at the last 1 ms sample before the spike (spike at 3.55 ms; at Dt 0.1 the pre-spike peak is -50.3 mV), 3-cell case -51.1 mV at Dt 1 and -50.4 mV at Dt 0.1, i.e. the 3-cell cue ends only about 0.4-1.1 mV below threshold. At Dt 0.1 the first non-cue
spike is at 3.57 ms (consistent), but later burst spikes differ from the Dt 1 rasters by up to 2.5 ms, so burst timing depends on the integration step; use the Dt 1 file for comparison with demo_data.json.
Artifacts of the recording: a spike sample reads 30 mV and decays (30, 19.1, then reset to -70), and a sample clamped at exactly -50.0 can follow a spike (precise-spike-time triangulation); bystanders stay at -70.0 mV in cases a, b, d and fire in the unpruned control (c) along with the members (13 spikes in 40 ms).
