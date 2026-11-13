# Ripple-tuning mechanism experiments E1-E4(b): observed results versus pre-registered predictions

**Sensitivity study, D_synmax 0.5, not bio-realistic.** Network: saved model `fable-it1a-sim133` (seed 20240628, 94 neurons, 67 pyramidal + 27 interneurons), run on our own NES (localhost:8000, not restarted). Predictions: `MECH_DESIGN.md` section 6 (timestamp 2026-11-12 09:54:59 PST, before any run; that file was not edited). Machine-readable: `mech_summary.json` (all numbers), `mech_data.json` (rasters, groups, neuron types and soma positions), `ripple_vm_mech.json` (Vm), `raw_mech_*.json` (raw per-run output).

## 1. Bottom line

All four pre-registered experiments (and E4b) gave a clean multi-memory ripple in every run, at both Dt 1 ms and Dt 0.1 ms: every memory had 4/4 non-cue members within 10 ms of its cue, no cross-talk, no spikes from non-member pyramidal cells, activity ended <= 77.1 ms after the first cue (<= 100 ms), at least one interneuron spike per recall, no burst running past 40 ms. By the pre-registered section-7 definition each is a ROBUST SUCCESS. The existing baseline (original groups, no scaling) failed at G1; the same framework reproduced that failure (control below), so the success is not a framework artifact.

| exp | memories 4/4, Dt 1 (4 runs) | memories 4/4, Dt 0.1 (4 runs) | worst Dt 0.1 latency of last non-cue (ms) | latest activity end after first cue (ms) | verdict (section 7) | pre-registered P(robust) | predictions HIT of scored |
|---|---|---|---|---|---|---|---|
| E1 | 16/16 | 16/16 | 4.64 | 70.9 | ROBUST SUCCESS | 0.45 | 25 of 26 |
| E2 | 16/16 | 16/16 | 6.32 | 77.1 | ROBUST SUCCESS | 0.08 | 21 of 28 |
| E3 | 16/16 | 16/16 | 4.60 | 70.8 | ROBUST SUCCESS | 0.45 | 25 of 26 |
| E4 | 12/12 | 12/12 | 6.32 | 56.6 | ROBUST SUCCESS | 0.10 | 13 of 19 |
| E4b | 12/12 | 12/12 | 4.55 | 53.9 | ROBUST SUCCESS | 0.55 | 6 of 6 |

Caveats on the verdict, stated plainly:
* Single deterministic simulation per case (NES is deterministic: E2 and E4 give identical spike times for the shared memories, E1 and E3 near-identical). The runs are NOT independent replicates; a hit on a probability says little about its calibration. All 5 experiments share one network and one seed.
* The E2/E4 margin is thinner than E1/E3: at Dt 0.1 ms the G0 memory cued second in the shuffled order completes with last non-cue latency 6.32 ms (limit 10 ms), vs <= 4.64 ms in E1/E3. The G0 -> G1 spike-weighted GABA observed in E2/E4 is 92.8 nS (baseline 176.8, fail), in the 65-120 "unknown" band of the pre-registered working threshold; it passes.
* "Robust" is only claimed for the tested protocol: 4 runs x 2 Dt, 150 ms, 12/16/20 ms spacing plus one shuffled order, one seed. Single-memory baselines were run at Dt 1 only.
* Fix A and fix B each work alone, and E1 = E3 in completion counts. Nothing was found that distinguishes them on the success criteria; they differ in interneuron-spike counts and burst length (E2/E4 keep G0/G1 bursts at 18-33 ms, E1/E3 at 4-13 ms).

Best experiment for the Vm file: E1 (tied with E3 on every success criterion; chosen as the simplest, no Pyr->Int zeroing). Best run = lowest max latency of the last non-cue member (shuffled order 2,0,3,1 at 16 ms, Dt 0.1: 4.502 ms); worst run = highest (order 0,1,2,3 at 12 ms, Dt 0.1: 4.641 ms). Both completed. Selection is by latency margin, not by success, since all runs succeeded.

## 2. Which experiments were run, and why

* E1, E2, E3, E4: all four, in that order, as instructed.
* E4b (K=3 re-selected set, standard rule): RUN, because E1 and E3 each completed all memories in all 4 runs at Dt 1 (MECH_DESIGN.md section 5: "if E1 beats E2"; the task's condition of "E1 or E3 reaches all complete in all 4 runs at Dt 1" is met).
* E2b (100 nS cap fallback): NOT RUN. MECH_DESIGN.md section 4 says "only if E2 shows non-terminating bursts"; E2 had none (longest G0/G1 burst 25.0 ms at Dt 1 and 32.7 ms at Dt 0.1, no activity past 77.1 ms after the first cue) and E2 also did not fail on completion. Not run, as the pre-declared condition was false.
* Extra check (not in the design): control run of the ORIGINAL groups with the unscaled standard rule, order 0,1,2,3 at 16 ms, Dt 1 ms, in this same framework (`run_control_mech.py`): G1 1/4 complete (0:4, 1:1, 2:4, 3:4), last activity 55.909 ms, 0 read-back mismatches, which matches the earlier `raw_main.json` result (G1 1/4, 55.909 ms). This confirms the framework reproduces the previous failure.

## 3. Other pre-registered predictions

| prediction | observed | mark |
|---|---|---|
| P(E1 completes more memories than E2) = 0.80 | equal: E1 16/16 and E2 16/16 at Dt 1 | MISS |
| P(E3 same completion counts as E1) = 0.75 | identical (all 4/4) | HIT |
| P(G1 after G0 in E2 is no worse than baseline 3,1,2 of 4 at every spacing) = 0.60 | 4,4,4 of 4 | HIT |
| P(total activity > 100 ms in some E2 run) = 0.40 | max 77.1 ms | HIT (not occurred) |
| E4b P(all complete) = 0.70, robust 0.55 | all complete, robust | HIT, HIT |

Largest misses: E2 and E4 G1 completion (predicted P 0.35-0.40, observed 4/4 in every run and Dt) and E2/E4 robust success (P 0.08 / 0.10, observed robust). The design assumed that removing interneuron 93 would lengthen the G0/G1 bursts enough to stop completion; bursts lengthened only moderately (G0 25.0 ms at Dt 1, within the predicted 18-40 ms) and did not stop terminating.

## 4. Peak GABA calculation versus predictions

Observed GABA = observed single-memory interneuron spike counts x dump `g_peak_sum` of interneuron->target non-cue member (weight-1 nS, same convention as the design; actual GABA weight is fixed 0.2). Maximum off-diagonal spike-weighted entry: E1 9.6 (predicted nominal 15.2, range 8-30, HIT), E3 9.6 (11.2, range 5-25, HIT), E4b 14.4 (13.6, range 4-28, HIT). E2 and E4 G0 -> G1: 92.8 (nominal 69.6, range 55-110, HIT; baseline 176.8). Observed binary mean G0 -> G1 12.0 equals the predicted 12.0 exactly in E2/E4. E2/E4 maximum any pair 92.8 is above the 69.6 nominal, caused by G0 firing 14 interneuron spikes in the single run (predicted nominal 11, within 9-16) vs the model's 11. Full matrices are in each section below and in `mech_summary.json` (`gaba_observed_from_singles`). These are weight-1 sums, not membrane conductances: no Vm-level GABA conductance was extracted, so the 38 nS cancel-the-margin estimate in MECH_DESIGN.md section 2 is not tested here.

## 5. Anomalies and notes

* E3 first attempt aborted on my own weights assertion before any spike was recorded: the rounded `target_conductance_nS` values in `mech_experiments.json` exceed `g_peak_sum` by up to 2.7e-7 relative for 15 Pyr->Int pairs (weight 1.0000003). I clipped targets to `min(target, g)` (weight exactly 1.0) in `mech_lib.build_set` and reran E3 from scratch. The aborted simulation was deleted (log `run_mech_E1-E3crash.log`, ends with the AssertionError). E1/E2/E4 sets are unaffected (no overshoot).
* Interneuron counts: E1/E3 interneurons fire only 3-4 spikes per single recall (predicted 5, range 3-9 / 2-7): lower edge, still HIT. At Dt 0.1 some later memories' windows contain only 1 interneuron spike (G3 in 3 of 4 E1 runs and in all 4 E3 runs), which just satisfies the >=1 criterion.
* Dt dependence: bursts are longer at Dt 0.1 (E1 G0 burst end 12.7 ms vs 7.3 ms at Dt 1), the latency 4.0 -> 4.4-4.6 ms; completion is unaffected. The earlier shuffled-order Dt 0.1 loss of G0 (baseline) does not occur in any of the 5 experiments.
* Not tested: larger K, other seeds, other spacings, NMDA, STDP (off).
* Activity end: "time activity ends overall" is last spike of any cell; it is dominated by the last cue time (36-60 ms) plus one burst of 4-13 ms (E1/E3) or 8-33 ms (E2/E4) plus late interneuron spikes of 1-4 ms. No spike in any run falls in the last 10 ms of the 150 ms run.
* Vm file: `ripple_vm_mech.json` (0.33 MB): E1, the two cases above, window -5..+110 ms, Dt 0.1 ms (1151 samples), 23 neurons: per memory 1 cue cell + 2 non-cue members (G0 1; 25, 33; G1 9; 13, 37; G2 2; 24, 31; G3 45; 15, 21), the 8 interneurons with most programmed member drive (89, 93, 79, 82, 80, 77, 90, 76; drives in `interneuron_selection`) and 3 bystander pyramidal cells (4, 59, 18, which are non-members of E1's groups; all stay at -70.0 mV). Vm spikes are clamped at +30 mV by the simulator. Spikes in the Vm runs match the raster runs of the same case within 112 ms (checked, `spikes_match_raster_run_within_112ms` true). E1 interneurons 89 and 93 fire 8 and 4 spikes in the best-run; 90 and 76 never fire.
* Bookkeeping: 62 simulations created (12 E1, 12 E2, 1 aborted + 12 E3, 11 E4, 11 E4b, 1 control, 2 Vm), every one deleted with `DeleteResidentByID` right after its data was read (0 delete failures), run one at a time with 30 s pauses; available RAM stayed >= 339 GB (guard 100 GB); STDP off; weights in [0,1]; every applied pair read back (3344 pairs per sim, 0 mismatches in all sims; the aborted E3 sim also had 0). No saved model modified, no git actions. Another agent's growths on the server were not touched.

## 6. Commands

```
cd /home/johnjose/cos/netmorph_work/recipe_v2/ripple_05
./run.sh run_mech.py E1 E2 E3 E4          # first launch: E1, E2 done, E3 aborted (clip bug), log run_mech_E1-E3crash.log
./run.sh run_mech.py E3 E4                # after the clip fix, log run_mech_E3-E4.log
./run.sh run_mech.py E4b_alternative      # log run_mech_E4b.log
./run.sh run_control_mech.py              # framework control (original groups, unscaled)
./run.sh run_vm_mech.py E1 "shuffled_2031_sep16_dt0.1:best ..." "order_0123_sep12_dt0.1:worst ..."   # log run_vm_mech.log
./run.sh assemble_mech.py                 # -> mech_summary.json
python3 write_results.py                  # -> mech_tables.md (tables below)
```
Library `mech_lib.py` (build_set builds weights = recipelib.build_pairs for the experiment's groups, then the listed Pyr->Int target conductances of `mech_experiments.json`; the resulting differences against `recipe/seed20240628/weights.json` were checked to equal the listed counts: E1 46+236, E2 155+33, E3 152+236, E4 113+0, E4b 38+201 Pyr->Int + Pyr->Pyr; the E2b rule (zeroing member->interneuron not in the kept set) reproduces E2's 151 zeroed pairs and E3's 114, so the keep-set rule was read correctly). Cue protocol as in `ripple_lib.py` (cells at +0/0.5/1.0/1.5 ms, 20 ms offset, 150 ms, spacings 12/16/20 ms plus shuffled 2,0,3,1 at 16 ms, K=3: 0,1,2 and shuffled 2,0,1).

## 7. Per-experiment tables (generated by write_results.py from mech_summary.json)

### E1: re-selected groups R0..R3, standard Pyr->Int rule

Label: sensitivity study, D_synmax 0.5, not bio-realistic. Groups (members; cue first 4 of each listed in JSON `groups`): G0 cue [1, 19, 23, 34] non-cue [25, 33, 48, 54]; G1 cue [9, 52, 56, 62] non-cue [13, 37, 60, 65]; G2 cue [2, 17, 29, 43] non-cue [24, 31, 32, 47]; G3 cue [45, 51, 61, 63] non-cue [15, 21, 35, 38].

Weight set: 3344 pairs programmed; vs weights.json: 46 Pyr->Int and 236 Pyr->Pyr pairs differ (matches mech_experiments.json); read-back mismatches in all 12 sims: 0.

**Verdict: ROBUST SUCCESS** (Dt 1 ms all memories complete in all 4 runs: True; Dt 0.1 ms: True; singles all complete: True).

Single-memory baselines (Dt 1): G0 4/4, latency 4.0 ms, 3 interneuron spikes (3 cells), last member spike 7.3 ms, last activity 7.6 ms; G1 4/4, latency 4.0 ms, 3 interneuron spikes (2 cells), last member spike 4.0 ms, last activity 8.5 ms; G2 4/4, latency 4.0 ms, 4 interneuron spikes (3 cells), last member spike 7.8 ms, last activity 8.5 ms; G3 4/4, latency 4.0 ms, 3 interneuron spikes (2 cells), last member spike 8.4 ms, last activity 9.1 ms.

Per-run observations (columns follow the cue order; "x" = no value). Burst end = last member pyramidal spike after its own cue; interneuron spikes counted from a memory's cue to the next cue (last: to run end); last activity = last spike of any cell, relative to first cue.

| run | order | non-cue fired /4 | latency last non-cue (ms) | burst end after cue (ms) | int spikes per window | cross-talk | non-member pyr spikes | last pyr spike (ms) | last activity (ms) | burst not terminated | robust ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| order_0123_sep12 | 0123 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.2 | 7.3, 4.1, 7.8, 8.7 | 3,2,4,2 | 0 | 0 | 44.7 | 47.6 | False | True |
| order_0123_sep16 | 0123 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.1 | 7.3, 4.1, 7.8, 8.5 | 3,2,4,2 | 0 | 0 | 56.5 | 59.6 | False | True |
| order_0123_sep20 | 0123 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.1 | 7.3, 4.1, 7.8, 8.4 | 3,3,3,2 | 0 | 0 | 68.4 | 70.9 | False | True |
| shuffled_2031_sep16 | 2031 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.1 | 7.8, 7.3, 8.4, 4.1 | 4,3,2,2 | 0 | 0 | 52.1 | 53.8 | False | True |
| order_0123_sep12_dt0.1 | 0123 | 4,4,4,4 | 4.4, 4.6, 4.5, 4.5 | 12.7, 7.2, 10.5, 10.3 | 7,4,5,2 | 0 | 0 | 46.3 | 46.3 | False | True |
| order_0123_sep16_dt0.1 | 0123 | 4,4,4,4 | 4.4, 4.6, 4.5, 4.5 | 12.7, 8.5, 10.5, 10.0 | 7,5,5,1 | 0 | 0 | 58.0 | 58.0 | False | True |
| order_0123_sep20_dt0.1 | 0123 | 4,4,4,4 | 4.4, 4.5, 4.4, 4.5 | 12.7, 8.4, 10.5, 10.0 | 7,4,4,1 | 0 | 0 | 70.0 | 70.0 | False | True |
| shuffled_2031_sep16_dt0.1 | 2031 | 4,4,4,4 | 4.4, 4.5, 4.5, 4.4 | 10.5, 9.1, 10.0, 8.0 | 7,5,1,4 | 0 | 0 | 56.0 | 57.5 | False | True |

Predicted (copied from MECH_DESIGN.md section 6 / mech_experiments.json) versus observed. Mark rule: ranges are HIT when inside; for probability predictions P, HIT when the outcome agrees with the side P>=0.5 favours, MISS otherwise (a coarse mechanical rule, not calibration).

| quantity | predicted | observed | mark |
|---|---|---|---|
| P(4/4) first memory 4/4 (all spacings) | 0.95 | [4, 4, 4] | HIT |
| P(4/4) second memory (G1) at 12 ms | 0.85 | 4/4 | HIT |
| P(4/4) third memory (G2) at 12 ms | 0.85 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 12 ms | 0.85 | 4/4 | HIT |
| P(4/4) second memory (G1) at 16 ms | 0.85 | 4/4 | HIT |
| P(4/4) third memory (G2) at 16 ms | 0.85 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 16 ms | 0.85 | 4/4 | HIT |
| P(4/4) second memory (G1) at 20 ms | 0.87 | 4/4 | HIT |
| P(4/4) third memory (G2) at 20 ms | 0.87 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 20 ms | 0.87 | 4/4 | HIT |
| P(4/4) shuffled, G2 (position 1) | 0.95 | 4/4 | HIT |
| P(4/4) shuffled, G0 (position 2) | 0.85 | 4/4 | HIT |
| P(4/4) shuffled, G3 (position 3) | 0.85 | 4/4 | HIT |
| P(4/4) shuffled, G1 (position 4) | 0.85 | 4/4 | HIT |
| P(all memories complete in all 4 runs), Dt 1 | 0.6 | True | HIT |
| latency of last non-cue (ms), Dt 1 all complete memories | [4.0, 4.8] | [4.03, 4.16] | HIT |
| burst end after cue (ms), last member spike, all memories, Dt 1 | range [4, 12] (P in range 0.70); >20 ms P 0.10 | min 4.1 max 8.7; 16/16 inside range; 0 > 20 ms | HIT |
| interneuron spikes per recall, single-memory runs, Dt 1 (G0..) | nominal [5, 5, 5, 4], range [3, 9] | [3, 3, 4, 3] | HIT |
| interneuron spikes per cue window in 4 ordered runs (G in order), Dt 1 | same ranges (windows include tails of earlier recalls) | [[3, 2, 4, 2], [3, 2, 4, 2], [3, 3, 3, 2], [4, 3, 2, 2]] | n/a |
| peak GABA onto another memory non-cue member: spike-weighted max, max off-diag (nS g_peak_sum, observed spikes from singles) | nominal 15.2, range [8, 30] | 9.6 | HIT |
| same, binary mean (max off-diag) | <= 9.6 | 7.0 | HIT |
| P(a burst not terminated within 40 ms in some group) | 0.1 | occurred: False [] | HIT |
| P(interneurons silent in some recall) | 0.05 | occurred: False | HIT |
| P(a single memory fails on its own) | 0.1 | occurred: False | HIT |
| P(cross-talk or non-member pyramidal spikes), all runs | 0.03 | occurred: False | HIT |
| P(all complete at Dt 0.1 ms) | 0.5 | True | HIT |
| P(robust success) | 0.45 | True | MISS |

Observed GABA matrix from the single-memory runs (rows = recalled memory, columns = target memory non-cue members; nS g_peak_sum at weight 1, observed interneuron spike counts x dump GABA conductance; same convention as predictions). Spike-weighted max: [[5.6, 9.6, 5.6, 8.8], [4.0, 7.2, 5.6, 4.8], [9.6, 9.6, 7.2, 8.8], [4.0, 7.2, 5.6, 4.8]]. Binary mean (cells that fired at least once): [[3.6, 7.0, 3.2, 6.4], [2.2, 2.2, 2.4, 2.6], [4.6, 5.2, 4.2, 5.8], [2.2, 2.2, 2.4, 2.6]].

Score: 25 HIT of 26 scored.

### E2: original G0..G3, Pyr->Int scaling (fix B)

Label: sensitivity study, D_synmax 0.5, not bio-realistic. Groups (members; cue first 4 of each listed in JSON `groups`): G0 cue [22, 29, 51, 63] non-cue [4, 18, 20, 59]; G1 cue [8, 27, 33, 44] non-cue [39, 41, 42, 60]; G2 cue [12, 17, 19, 50] non-cue [0, 21, 37, 49]; G3 cue [16, 45, 56, 64] non-cue [24, 25, 35, 48].

Weight set: 3344 pairs programmed; vs weights.json: 155 Pyr->Int and 33 Pyr->Pyr pairs differ (matches mech_experiments.json); read-back mismatches in all 12 sims: 0.

**Verdict: ROBUST SUCCESS** (Dt 1 ms all memories complete in all 4 runs: True; Dt 0.1 ms: True; singles all complete: True).

Single-memory baselines (Dt 1): G0 4/4, latency 4.0 ms, 14 interneuron spikes (3 cells), last member spike 25.0 ms, last activity 27.1 ms; G1 4/4, latency 4.0 ms, 7 interneuron spikes (1 cells), last member spike 21.4 ms, last activity 23.9 ms; G2 4/4, latency 4.0 ms, 4 interneuron spikes (3 cells), last member spike 7.8 ms, last activity 8.5 ms; G3 4/4, latency 4.0 ms, 4 interneuron spikes (1 cells), last member spike 12.4 ms, last activity 14.9 ms.

Per-run observations (columns follow the cue order; "x" = no value). Burst end = last member pyramidal spike after its own cue; interneuron spikes counted from a memory's cue to the next cue (last: to run end); last activity = last spike of any cell, relative to first cue.

| run | order | non-cue fired /4 | latency last non-cue (ms) | burst end after cue (ms) | int spikes per window | cross-talk | non-member pyr spikes | last pyr spike (ms) | last activity (ms) | burst not terminated | robust ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| order_0123_sep12 | 0123 | 4,4,4,4 | 4.0, 4.8, 4.2, 4.2 | 25.0, 18.5, 7.8, 12.5 | 7,6,5,2 | 0 | 0 | 48.5 | 48.5 | False | True |
| order_0123_sep16 | 0123 | 4,4,4,4 | 4.0, 4.8, 4.2, 4.1 | 25.0, 22.7, 7.8, 12.4 | 9,6,5,2 | 0 | 0 | 60.4 | 60.4 | False | True |
| order_0123_sep20 | 0123 | 4,4,4,4 | 4.0, 4.9, 4.2, 4.1 | 25.0, 22.9, 7.8, 12.1 | 11,7,4,1 | 0 | 0 | 72.1 | 72.1 | False | True |
| shuffled_2031_sep16 | 2031 | 4,4,4,4 | 4.0, 4.3, 4.3, 4.6 | 7.8, 25.0, 13.1, 22.9 | 4,9,6,6 | 0 | 0 | 70.9 | 71.4 | False | True |
| order_0123_sep12_dt0.1 | 0123 | 4,4,4,4 | 4.4, 5.4, 4.6, 4.6 | 27.7, 22.8, 16.3, 15.1 | 7,7,9,6 | 0 | 0 | 51.1 | 51.6 | False | True |
| order_0123_sep16_dt0.1 | 0123 | 4,4,4,4 | 4.4, 5.4, 4.6, 4.6 | 27.7, 24.4, 16.2, 17.5 | 10,7,11,3 | 0 | 0 | 65.5 | 65.5 | False | True |
| order_0123_sep20_dt0.1 | 0123 | 4,4,4,4 | 4.4, 5.5, 4.5, 4.5 | 27.7, 23.9, 16.1, 17.1 | 12,7,11,2 | 0 | 0 | 77.1 | 77.1 | False | True |
| shuffled_2031_sep16_dt0.1 | 2031 | 4,4,4,4 | 4.4, 6.3, 4.6, 5.7 | 16.1, 32.7, 15.0, 24.4 | 11,9,9,7 | 0 | 0 | 72.4 | 73.2 | False | True |

Predicted (copied from MECH_DESIGN.md section 6 / mech_experiments.json) versus observed. Mark rule: ranges are HIT when inside; for probability predictions P, HIT when the outcome agrees with the side P>=0.5 favours, MISS otherwise (a coarse mechanical rule, not calibration).

| quantity | predicted | observed | mark |
|---|---|---|---|
| P(4/4) first memory 4/4 (all spacings) | 0.97 | [4, 4, 4] | HIT |
| P(4/4) second memory (G1) at 12 ms | 0.35 | 4/4 | MISS |
| P(4/4) third memory (G2) at 12 ms | 0.8 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 12 ms | 0.85 | 4/4 | HIT |
| P(4/4) second memory (G1) at 16 ms | 0.35 | 4/4 | MISS |
| P(4/4) third memory (G2) at 16 ms | 0.8 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 16 ms | 0.85 | 4/4 | HIT |
| P(4/4) second memory (G1) at 20 ms | 0.4 | 4/4 | MISS |
| P(4/4) third memory (G2) at 20 ms | 0.8 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 20 ms | 0.85 | 4/4 | HIT |
| P(4/4) shuffled, G2 (position 1) | 0.97 | 4/4 | HIT |
| P(4/4) shuffled, G0 (position 2) | 0.7 | 4/4 | HIT |
| P(4/4) shuffled, G3 (position 3) | 0.85 | 4/4 | HIT |
| P(4/4) shuffled, G1 (position 4) | 0.8 | 4/4 | HIT |
| P(all memories complete in all 4 runs), Dt 1 | 0.15 | True | MISS |
| latency of last non-cue (ms), Dt 1 all complete memories | [4.0, 6.5] | [4.03, 4.88] | HIT |
| burst end G0 (ms) | range [18, 40] (P 0.55) | min 25.0 max 25.0; 4/4 inside | HIT |
| burst end G1 (ms) | range [15, 40] (P 0.45) | min 18.5 max 22.9; 4/4 inside | HIT |
| burst end G2 (ms) | range [5, 12] (P 0.80) | min 7.8 max 7.8; 4/4 inside | HIT |
| burst end G3 (ms) | range [8, 25] (P 0.65) | min 12.1 max 13.1; 4/4 inside | HIT |
| interneuron spikes per recall, single-memory runs, Dt 1 (G0..) | nominal [11, 5, 5, 5], range {'G0': [9, 16], 'G1': [5, 12], 'G2': [3, 6], 'G3': [4, 8]} | [14, 7, 4, 4] | HIT |
| interneuron spikes per cue window in 4 ordered runs (G in order), Dt 1 | same ranges (windows include tails of earlier recalls) | [[7, 6, 5, 2], [9, 6, 5, 2], [11, 7, 4, 1], [4, 9, 6, 6]] | n/a |
| peak GABA G0 -> G1 spike-weighted max (nS) | nominal 69.6, range [55, 110], baseline 176.8 | 92.8 | HIT |
| G0 -> G1 binary mean (nS) | 12.0 | 12.0 | n/a |
| max any pair spike-weighted (nS) | 69.6 | 92.8 | n/a |
| P(a burst not terminated within 40 ms in some group) | 0.5 | occurred: False [] | MISS |
| P(interneurons silent in some recall) | 0.02 | occurred: False | HIT |
| P(cross-talk or non-member pyramidal spikes), all runs | 0.03 | occurred: False | HIT |
| P(total activity > 100 ms in some run) | 0.4 | occurred: False | HIT |
| P(all complete at Dt 0.1 ms) | 0.1 | True | MISS |
| P(robust success) | 0.08 | True | MISS |

Observed GABA matrix from the single-memory runs (rows = recalled memory, columns = target memory non-cue members; nS g_peak_sum at weight 1, observed interneuron spike counts x dump GABA conductance; same convention as predictions). Spike-weighted max: [[72.0, 92.8, 30.4, 28.8], [39.2, 67.2, 16.8, 11.2], [34.4, 42.4, 16.8, 9.6], [22.4, 38.4, 9.6, 6.4]]. Binary mean (cells that fired at least once): [[15.6, 12.0, 5.8, 5.4], [3.4, 4.0, 1.4, 0.8], [23.4, 19.2, 9.0, 5.8], [3.4, 4.0, 1.4, 0.8]].

Score: 21 HIT of 28 scored.

### E3: re-selected R0..R3 + Pyr->Int scaling

Label: sensitivity study, D_synmax 0.5, not bio-realistic. Groups (members; cue first 4 of each listed in JSON `groups`): G0 cue [1, 19, 23, 34] non-cue [25, 33, 48, 54]; G1 cue [9, 52, 56, 62] non-cue [13, 37, 60, 65]; G2 cue [2, 17, 29, 43] non-cue [24, 31, 32, 47]; G3 cue [45, 51, 61, 63] non-cue [15, 21, 35, 38].

Weight set: 3344 pairs programmed; vs weights.json: 152 Pyr->Int and 236 Pyr->Pyr pairs differ (matches mech_experiments.json); read-back mismatches in all 12 sims: 0.

**Verdict: ROBUST SUCCESS** (Dt 1 ms all memories complete in all 4 runs: True; Dt 0.1 ms: True; singles all complete: True).

Single-memory baselines (Dt 1): G0 4/4, latency 4.0 ms, 3 interneuron spikes (3 cells), last member spike 7.3 ms, last activity 7.6 ms; G1 4/4, latency 4.0 ms, 3 interneuron spikes (2 cells), last member spike 4.0 ms, last activity 8.5 ms; G2 4/4, latency 4.0 ms, 4 interneuron spikes (3 cells), last member spike 7.8 ms, last activity 8.5 ms; G3 4/4, latency 4.0 ms, 3 interneuron spikes (2 cells), last member spike 8.4 ms, last activity 9.1 ms.

Per-run observations (columns follow the cue order; "x" = no value). Burst end = last member pyramidal spike after its own cue; interneuron spikes counted from a memory's cue to the next cue (last: to run end); last activity = last spike of any cell, relative to first cue.

| run | order | non-cue fired /4 | latency last non-cue (ms) | burst end after cue (ms) | int spikes per window | cross-talk | non-member pyr spikes | last pyr spike (ms) | last activity (ms) | burst not terminated | robust ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| order_0123_sep12 | 0123 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.1 | 7.3, 4.1, 7.8, 8.6 | 3,2,3,2 | 0 | 0 | 44.6 | 47.3 | False | True |
| order_0123_sep16 | 0123 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.1 | 7.3, 4.1, 7.8, 8.4 | 3,2,3,2 | 0 | 0 | 56.4 | 59.5 | False | True |
| order_0123_sep20 | 0123 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.1 | 7.3, 4.1, 7.8, 8.3 | 3,3,2,2 | 0 | 0 | 68.3 | 70.8 | False | True |
| shuffled_2031_sep16 | 2031 | 4,4,4,4 | 4.0, 4.1, 4.1, 4.1 | 7.8, 7.3, 8.4, 4.1 | 4,3,2,2 | 0 | 0 | 52.1 | 53.8 | False | True |
| order_0123_sep12_dt0.1 | 0123 | 4,4,4,4 | 4.4, 4.6, 4.5, 4.5 | 12.7, 8.6, 10.5, 10.0 | 6,5,3,1 | 0 | 0 | 46.0 | 46.0 | False | True |
| order_0123_sep16_dt0.1 | 0123 | 4,4,4,4 | 4.4, 4.5, 4.5, 4.5 | 12.7, 8.5, 10.5, 10.0 | 6,5,3,1 | 0 | 0 | 58.0 | 58.0 | False | True |
| order_0123_sep20_dt0.1 | 0123 | 4,4,4,4 | 4.4, 4.5, 4.4, 4.4 | 12.7, 8.2, 10.5, 10.0 | 6,4,3,1 | 0 | 0 | 70.0 | 70.0 | False | True |
| shuffled_2031_sep16_dt0.1 | 2031 | 4,4,4,4 | 4.4, 4.5, 4.5, 4.4 | 10.5, 12.6, 10.0, 8.0 | 6,4,1,4 | 0 | 0 | 56.0 | 57.5 | False | True |

Predicted (copied from MECH_DESIGN.md section 6 / mech_experiments.json) versus observed. Mark rule: ranges are HIT when inside; for probability predictions P, HIT when the outcome agrees with the side P>=0.5 favours, MISS otherwise (a coarse mechanical rule, not calibration).

| quantity | predicted | observed | mark |
|---|---|---|---|
| P(4/4) first memory 4/4 (all spacings) | 0.95 | [4, 4, 4] | HIT |
| P(4/4) second memory (G1) at 12 ms | 0.86 | 4/4 | HIT |
| P(4/4) third memory (G2) at 12 ms | 0.86 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 12 ms | 0.86 | 4/4 | HIT |
| P(4/4) second memory (G1) at 16 ms | 0.86 | 4/4 | HIT |
| P(4/4) third memory (G2) at 16 ms | 0.86 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 16 ms | 0.86 | 4/4 | HIT |
| P(4/4) second memory (G1) at 20 ms | 0.88 | 4/4 | HIT |
| P(4/4) third memory (G2) at 20 ms | 0.88 | 4/4 | HIT |
| P(4/4) fourth memory (G3) at 20 ms | 0.88 | 4/4 | HIT |
| P(4/4) shuffled, G2 (position 1) | 0.95 | 4/4 | HIT |
| P(4/4) shuffled, G0 (position 2) | 0.86 | 4/4 | HIT |
| P(4/4) shuffled, G3 (position 3) | 0.86 | 4/4 | HIT |
| P(4/4) shuffled, G1 (position 4) | 0.86 | 4/4 | HIT |
| P(all memories complete in all 4 runs), Dt 1 | 0.6 | True | HIT |
| latency of last non-cue (ms), Dt 1 all complete memories | [4.0, 4.8] | [4.03, 4.13] | HIT |
| burst end after cue (ms), last member spike, all memories, Dt 1 | range [4, 14] (P in range 0.68); >20 ms P 0.13 | min 4.1 max 8.6; 16/16 inside range; 0 > 20 ms | HIT |
| interneuron spikes per recall, single-memory runs, Dt 1 (G0..) | nominal [4, 4, 4, 3], range [2, 7] | [3, 3, 4, 3] | HIT |
| interneuron spikes per cue window in 4 ordered runs (G in order), Dt 1 | same ranges (windows include tails of earlier recalls) | [[3, 2, 3, 2], [3, 2, 3, 2], [3, 3, 2, 2], [4, 3, 2, 2]] | n/a |
| peak GABA onto another memory non-cue member: spike-weighted max, max off-diag (nS g_peak_sum, observed spikes from singles) | nominal 11.2, range [5, 25] | 9.6 | HIT |
| same, binary mean (max off-diag) | <= 7.0 | 7.0 | HIT |
| P(a burst not terminated within 40 ms in some group) | 0.13 | occurred: False [] | HIT |
| P(interneurons silent in some recall) | 0.05 | occurred: False | HIT |
| P(a single memory fails on its own) | 0.1 | occurred: False | HIT |
| P(cross-talk or non-member pyramidal spikes), all runs | 0.03 | occurred: False | HIT |
| P(all complete at Dt 0.1 ms) | 0.5 | True | HIT |
| P(robust success) | 0.45 | True | MISS |

Observed GABA matrix from the single-memory runs (rows = recalled memory, columns = target memory non-cue members; nS g_peak_sum at weight 1, observed interneuron spike counts x dump GABA conductance; same convention as predictions). Spike-weighted max: [[5.6, 9.6, 5.6, 8.8], [4.0, 7.2, 5.6, 4.8], [9.6, 9.6, 7.2, 8.8], [4.0, 7.2, 5.6, 4.8]]. Binary mean (cells that fired at least once): [[3.6, 7.0, 3.2, 6.4], [2.2, 2.2, 2.4, 2.6], [4.6, 5.2, 4.2, 5.8], [2.2, 2.2, 2.4, 2.6]].

Score: 25 HIT of 26 scored.

### E4: K=3 original G0,G1,G2 + Pyr->Int scaling

Label: sensitivity study, D_synmax 0.5, not bio-realistic. Groups (members; cue first 4 of each listed in JSON `groups`): G0 cue [22, 29, 51, 63] non-cue [4, 18, 20, 59]; G1 cue [8, 27, 33, 44] non-cue [39, 41, 42, 60]; G2 cue [12, 17, 19, 50] non-cue [0, 21, 37, 49].

Weight set: 3344 pairs programmed; vs weights.json: 113 Pyr->Int and 0 Pyr->Pyr pairs differ (matches mech_experiments.json); read-back mismatches in all 11 sims: 0.

**Verdict: ROBUST SUCCESS** (Dt 1 ms all memories complete in all 4 runs: True; Dt 0.1 ms: True; singles all complete: True).

Single-memory baselines (Dt 1): G0 4/4, latency 4.0 ms, 14 interneuron spikes (3 cells), last member spike 25.0 ms, last activity 27.1 ms; G1 4/4, latency 4.0 ms, 7 interneuron spikes (1 cells), last member spike 21.4 ms, last activity 23.9 ms; G2 4/4, latency 4.0 ms, 4 interneuron spikes (3 cells), last member spike 7.8 ms, last activity 8.5 ms.

Per-run observations (columns follow the cue order; "x" = no value). Burst end = last member pyramidal spike after its own cue; interneuron spikes counted from a memory's cue to the next cue (last: to run end); last activity = last spike of any cell, relative to first cue.

| run | order | non-cue fired /4 | latency last non-cue (ms) | burst end after cue (ms) | int spikes per window | cross-talk | non-member pyr spikes | last pyr spike (ms) | last activity (ms) | burst not terminated | robust ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| order_012_sep12 | 012 | 4,4,4 | 4.0, 4.8, 4.2 | 25.0, 18.5, 7.8 | 7,6,5 | 0 | 0 | 31.8 | 32.8 | False | True |
| order_012_sep16 | 012 | 4,4,4 | 4.0, 4.8, 4.2 | 25.0, 22.7, 7.8 | 9,6,5 | 0 | 0 | 39.8 | 39.8 | False | True |
| order_012_sep20 | 012 | 4,4,4 | 4.0, 4.9, 4.2 | 25.0, 22.9, 7.8 | 11,7,4 | 0 | 0 | 47.8 | 47.8 | False | True |
| shuffled_201_sep16 | 201 | 4,4,4 | 4.0, 4.3, 4.9 | 7.8, 25.0, 21.5 | 4,9,8 | 0 | 0 | 53.5 | 53.5 | False | True |
| order_012_sep12_dt0.1 | 012 | 4,4,4 | 4.4, 5.4, 4.6 | 27.7, 22.8, 16.3 | 7,7,13 | 0 | 0 | 40.3 | 41.9 | False | True |
| order_012_sep16_dt0.1 | 012 | 4,4,4 | 4.4, 5.4, 4.6 | 27.7, 24.4, 16.2 | 10,7,12 | 0 | 0 | 48.2 | 49.8 | False | True |
| order_012_sep20_dt0.1 | 012 | 4,4,4 | 4.4, 5.5, 4.5 | 27.7, 23.9, 16.1 | 12,7,11 | 0 | 0 | 56.1 | 56.2 | False | True |
| shuffled_201_sep16_dt0.1 | 201 | 4,4,4 | 4.4, 6.3, 5.9 | 16.1, 32.7, 24.6 | 11,9,12 | 0 | 0 | 56.6 | 56.6 | False | True |

Predicted (copied from MECH_DESIGN.md section 6 / mech_experiments.json) versus observed. Mark rule: ranges are HIT when inside; for probability predictions P, HIT when the outcome agrees with the side P>=0.5 favours, MISS otherwise (a coarse mechanical rule, not calibration).

| quantity | predicted | observed | mark |
|---|---|---|---|
| P(4/4) first memory 4/4 (all spacings) | 0.97 | [4, 4, 4] | HIT |
| P(4/4) second memory (G1) at 12 ms | 0.35 | 4/4 | MISS |
| P(4/4) third memory (G2) at 12 ms | 0.8 | 4/4 | HIT |
| P(4/4) second memory (G1) at 16 ms | 0.35 | 4/4 | MISS |
| P(4/4) third memory (G2) at 16 ms | 0.8 | 4/4 | HIT |
| P(4/4) second memory (G1) at 20 ms | 0.4 | 4/4 | MISS |
| P(4/4) third memory (G2) at 20 ms | 0.8 | 4/4 | HIT |
| P(4/4) shuffled, G2 (position 1) | 0.97 | 4/4 | HIT |
| P(4/4) shuffled, G0 (position 2) | 0.7 | 4/4 | HIT |
| P(4/4) shuffled, G1 (position 3) | 0.45 | 4/4 | MISS |
| P(all memories complete in all 4 runs), Dt 1 | 0.18 | True | MISS |
| burst end G0 (ms) | range [18, 40] (P 0.55) | min 25.0 max 25.0; 4/4 inside | HIT |
| burst end G1 (ms) | range [15, 40] (P 0.45) | min 18.5 max 22.9; 4/4 inside | HIT |
| burst end G2 (ms) | range [5, 12] (P 0.80) | min 7.8 max 7.8; 4/4 inside | HIT |
| interneuron spikes per recall, single-memory runs, Dt 1 (G0..) | nominal [11, 5, 5], range {'G0': [9, 16], 'G1': [5, 12], 'G2': [3, 6]} | [14, 7, 4] | HIT |
| interneuron spikes per cue window in 4 ordered runs (G in order), Dt 1 | same ranges (windows include tails of earlier recalls) | [[7, 6, 5], [9, 6, 5], [11, 7, 4], [4, 9, 8]] | n/a |
| peak GABA G0 -> G1 spike-weighted max (nS) | nominal 69.6, range [55, 110], baseline 176.8 | 92.8 | HIT |
| G0 -> G1 binary mean (nS) | 12.0 | 12.0 | n/a |
| max any pair spike-weighted (nS) | 69.6 | 92.8 | n/a |
| P(a burst not terminated within 40 ms in some group) | 0.45 | occurred: False [] | HIT |
| P(cross-talk or non-member pyramidal spikes), all runs | 0.03 | occurred: False | HIT |
| P(robust success) | 0.1 | True | MISS |

Observed GABA matrix from the single-memory runs (rows = recalled memory, columns = target memory non-cue members; nS g_peak_sum at weight 1, observed interneuron spike counts x dump GABA conductance; same convention as predictions). Spike-weighted max: [[72.0, 92.8, 30.4], [39.2, 67.2, 16.8], [34.4, 42.4, 16.8]]. Binary mean (cells that fired at least once): [[15.6, 12.0, 5.8], [3.4, 4.0, 1.4], [23.4, 19.2, 9.0]].

Score: 13 HIT of 19 scored.

### E4b: K=3 re-selected set, standard rule (run because E1 and E3 both completed all memories in all 4 runs at Dt 1)

Label: sensitivity study, D_synmax 0.5, not bio-realistic. Groups (members; cue first 4 of each listed in JSON `groups`): G0 cue [1, 9, 43, 56] non-cue [24, 25, 35, 48]; G1 cue [30, 46, 51, 63] non-cue [21, 58, 60, 65]; G2 cue [2, 16, 19, 27] non-cue [13, 15, 33, 54].

Weight set: 3344 pairs programmed; vs weights.json: 38 Pyr->Int and 201 Pyr->Pyr pairs differ (matches mech_experiments.json); read-back mismatches in all 11 sims: 0.

**Verdict: ROBUST SUCCESS** (Dt 1 ms all memories complete in all 4 runs: True; Dt 0.1 ms: True; singles all complete: True).

Single-memory baselines (Dt 1): G0 4/4, latency 4.0 ms, 6 interneuron spikes (4 cells), last member spike 10.6 ms, last activity 11.7 ms; G1 4/4, latency 4.0 ms, 3 interneuron spikes (2 cells), last member spike 7.9 ms, last activity 8.6 ms; G2 4/4, latency 4.0 ms, 4 interneuron spikes (3 cells), last member spike 7.9 ms, last activity 8.7 ms.

Per-run observations (columns follow the cue order; "x" = no value). Burst end = last member pyramidal spike after its own cue; interneuron spikes counted from a memory's cue to the next cue (last: to run end); last activity = last spike of any cell, relative to first cue.

| run | order | non-cue fired /4 | latency last non-cue (ms) | burst end after cue (ms) | int spikes per window | cross-talk | non-member pyr spikes | last pyr spike (ms) | last activity (ms) | burst not terminated | robust ok |
|---|---|---|---|---|---|---|---|---|---|---|---|
| order_012_sep12 | 012 | 4,4,4 | 4.0, 4.2, 4.1 | 10.6, 8.0, 7.8 | 6,2,2 | 0 | 0 | 31.8 | 31.8 | False | True |
| order_012_sep16 | 012 | 4,4,4 | 4.0, 4.2, 4.1 | 10.6, 8.0, 7.8 | 6,2,2 | 0 | 0 | 39.8 | 40.4 | False | True |
| order_012_sep20 | 012 | 4,4,4 | 4.0, 4.1, 4.1 | 10.6, 7.9, 7.8 | 6,2,3 | 0 | 0 | 47.8 | 49.8 | False | True |
| shuffled_201_sep16 | 201 | 4,4,4 | 4.0, 4.1, 4.1 | 7.9, 10.6, 8.0 | 4,4,2 | 0 | 0 | 40.0 | 40.0 | False | True |
| order_012_sep12_dt0.1 | 012 | 4,4,4 | 4.4, 4.6, 4.5 | 11.9, 7.0, 14.2 | 6,4,5 | 0 | 0 | 38.2 | 38.2 | False | True |
| order_012_sep16_dt0.1 | 012 | 4,4,4 | 4.4, 4.5, 4.4 | 11.9, 8.9, 14.0 | 7,3,4 | 0 | 0 | 46.0 | 46.0 | False | True |
| order_012_sep20_dt0.1 | 012 | 4,4,4 | 4.4, 4.5, 4.4 | 11.9, 8.7, 13.9 | 7,3,4 | 0 | 0 | 53.9 | 53.9 | False | True |
| shuffled_201_sep16_dt0.1 | 201 | 4,4,4 | 4.4, 4.5, 4.5 | 14.0, 12.0, 8.6 | 8,4,3 | 0 | 0 | 40.6 | 42.4 | False | True |

Predicted (copied from MECH_DESIGN.md section 6 / mech_experiments.json) versus observed. Mark rule: ranges are HIT when inside; for probability predictions P, HIT when the outcome agrees with the side P>=0.5 favours, MISS otherwise (a coarse mechanical rule, not calibration).

| quantity | predicted | observed | mark |
|---|---|---|---|
| P(all memories complete in all 4 runs), Dt 1 | 0.7 | True | HIT |
| burst end after cue (ms), last member spike, all memories, Dt 1 | range [4, 12] (P in range 0.70); >20 ms P nan | min 7.8 max 10.6; 12/12 inside range; 0 > 20 ms | HIT |
| interneuron spikes per recall, single-memory runs, Dt 1 (G0..) | nominal [5, 3, 5], range [2, 9] | [6, 3, 4] | HIT |
| interneuron spikes per cue window in 4 ordered runs (G in order), Dt 1 | same ranges (windows include tails of earlier recalls) | [[6, 2, 2], [6, 2, 2], [6, 2, 3], [4, 4, 2]] | n/a |
| peak GABA onto another memory non-cue member: spike-weighted max, max off-diag (nS g_peak_sum, observed spikes from singles) | nominal 13.6, range [4, 28] | 14.4 | HIT |
| P(cross-talk or non-member pyramidal spikes), all runs | 0.03 | occurred: False | HIT |
| P(robust success) | 0.55 | True | HIT |

Observed GABA matrix from the single-memory runs (rows = recalled memory, columns = target memory non-cue members; nS g_peak_sum at weight 1, observed interneuron spike counts x dump GABA conductance; same convention as predictions). Spike-weighted max: [[13.6, 14.4, 9.6], [4.0, 4.0, 4.0], [7.2, 9.6, 7.2]]. Binary mean (cells that fired at least once): [[7.6, 8.0, 7.0], [1.6, 1.6, 2.2], [3.6, 6.6, 4.4]].

Score: 6 HIT of 6 scored.
