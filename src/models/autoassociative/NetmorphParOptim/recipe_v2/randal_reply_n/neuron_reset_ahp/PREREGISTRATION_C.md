# neuron_reset_ahp PREREGISTRATION_C (2026-11-24; written before any simulation of step C; not edited afterwards, changes go to DEVIATIONS.md as C1, C2, ...)

John approved options 2 and 3 from the step-B report, run together (8 sims).
- **C1, a deliberate 2-spike cue:** each forced cue spike gets a second forced spike on the same cell 4.0 ms later. Original neurons (no reset or sAHP change). Run on s77777 and s66666 with the eigenvalue design. This is the clean test of the post hoc B2 finding that RS2 helped because the -55 mV reset made the forced cue cells fire again about 4 ms later.
- **C2, a finer rho grid:** rho 16.7, 16.9 and 17.1 nS, original neurons, single-spike cue, both models. The question is where 75% cues complete without ignition.

**Same rules as before:**
- Patched instance only (NES 2397163 / API 2397757 on 8011 / 8010). Main NES 3156209 / API 1972355 untouched. No emails, git or pushes.
- Model-file copies only, deleted after each run. For the original neurons the copy has no field changed (arm N0), the same route as B2.
- At most 3 simulations at once across all workers. Restart the separate build if RSS > 10 GB between runs.
- Delete every simulation after its run.

**Limits (asserted in code):**
- per pair <= 6.86 nS
- AMPA weight in [0.1, 1.0] of grown G
- NMDA r = 1.0 nominal
- GABA x1
- The input cap (3T = 49.5 nS per cell) is reported per run, not enforced beyond LH's cap script.

**Common to C1 and C2** (as B2):
- A17 assemblies (`../partial_cue/alloc_b.json`) on s77777 and s66666.
- The same 27 cue subsets in the same order (`run_pl.make_events`, same seeds). Event spacing 9,000 ms, first event at 20 ms.
- r 1.0, GABA x1, arm N0.
- Member pairs rescaled above the 0.1 G floor so the dominant eigenvalue of the 17x17 member AMPA matrix equals the target (`run_nr2.make_scaled`; every other pair as LH).
- Runner: `run_nr3.py WDESIGN SEED NCUE`. Analysis: `analyze_c.py`, using the `analyze_nr.py` measures and the `analyze_b.py` criteria (TERM, PASS75, PASS_T).
- The contamination rule is unchanged.

**Computed before running** (`run_nr3.py --design-only`; weights as fraction of G, nS):

| model | rho | k | member w min / mean / max | max pair | max member input | members > 49.5 nS |
|---|---|---|---|---|---|---|
| s77777 | 16.0 | 0.692 | 0.10 / 0.515 / 0.723 | 4.25 | 57.2 (hub cell 3) | 1 |
| s77777 | 16.7 | 0.732 | 0.10 / 0.539 / 0.758 | 4.46 | 57.2 | 1 |
| s77777 | 16.9 | 0.743 | 0.10 / 0.546 / 0.768 | 4.52 | 57.2 | 1 |
| s77777 | 17.1 | 0.754 | 0.10 / 0.552 / 0.779 | 4.58 | 57.2 | 1 |
| s66666 | 16.0 | 0.646 | 0.118 / 0.517 / 0.682 | 3.34 | 47.6 | 0 |
| s66666 | 16.7 | 0.682 | 0.119 / 0.540 / 0.714 | 3.50 | 47.8 | 0 |
| s66666 | 16.9 | 0.692 | 0.119 / 0.546 / 0.723 | 3.54 | 47.8 | 0 |
| s66666 | 17.1 | 0.703 | 0.119 / 0.553 / 0.732 | 3.59 | 47.9 | 0 |

The s77777 hub cell exceeds the input cap in every design, because of the grown graph and the per-cell LH scaling, which leaves the non-member input in place.

## C1: 2-spike cue (2 sims), rho 16.0
**Choice of rho, fixed now:** 16.0 is the best rho so far.
- It is the only rho with a 75%-design pass (E16 + RS2, s77777).
- It is the only rho whose N0 runs had no non-member spikes on both models (E16.5 s66666 had 1 event).
- It is the direct comparison for the burst explanation: E16 N0 and E16 RS2 were run at this rho.

**Cue.**
- Every cue kind gets the doubled cue: full, 75%, 50%, 25%, single cell and unrelated. The silence checks are therefore tested with the stronger cue.
- The first spikes keep their 1.5 ms spread, and each cell's second spike follows its own first spike by 4.0 ms. 4.0 ms is the rebound latency measured post hoc under RS2; NES refractory is 2 ms.
- *last* includes the forced spikes, so it is at least about 5.5 ms for every cued event. "Complete" counts only non-cue members, as before.

| # | design | cue | model | reference (B2, single-spike cue) |
|---|---|---|---|---|
| 1 | E16 | 2-spike | s77777 | N0: 75% 3/6, 50% 0/6, last 6.2 ms, TERM. RS2: 6/6, 0/6, 13.8 ms, TERM, PASS75 |
| 2 | E16 | 2-spike | s66666 | N0: 4/6, 0/6, 8.3 ms, TERM. RS2: 6/6, 0/6, 190 ms, ignition |

**Manipulation check:** count cue-cell spikes in [t, t+8) per cue cell and event. The check passes if >= 95% of cue-cell instances fire at least 2 spikes. If it fails, C1 is reported as not testing the hypothesis.

**Predictions (confidence):**
- **C1a:** the manipulation check passes in both runs (90%).
- **C1b:** 75% completion >= 5/6 in both models (65%).
- **C1c:** 50% completion <= 1/6 in both models (70%). A doubled 50% cue is 18 forced spikes against 26 for a single 75% cue at the same rho. Under RS2 the cue cells fired 2.7-7 spikes each and still gave 0/6.
- **C1d:** TERM on s77777 (70%); TERM on s66666 (50%). The RS2 ignition on s66666 came with about 7 spikes per cue cell and the depolarised reset, which a 2-spike cue does not reproduce.
- **C1e:** 25%, single-cell and unrelated cues recruit 0 in both runs, even with 2 spikes (80%).
- **C1f:** PASS75 (75% >= 5/6, silence, TERM, no non-member spikes) in >= 1 model (50%); in both models (30%).

## C2: rho grid (6 sims), single-spike cue
| # | design | models |
|---|---|---|
| 3, 4 | E16.7 | s77777, s66666 |
| 5, 6 | E16.9 | s77777, s66666 |
| 7, 8 | E17.1 | s77777, s66666 |

**Existing points** (N0, single cue):
- E16: 3/6 and 4/6, TERM both (9 s).
- E16.5: 4/6 and 4/6, TERM both, with one non-member event on s66666 (9 s).
- W70 at 3 s spacing: s77777 at rho 16.98 gave 5/6 and no runaway; s66666 at 17.88 gave 5/6 with runaway 5/5.

knob-scout puts the ignition threshold at 17.4 ± 1 nS.

**Definitions:**
- **Window:** a rho in the grid where both models have PASS75. Bracketing of this kind is a per-model, single-run measure. A count of 5/6 vs 4/6 is within the noise of 6 events, which the report will say.
- **Per-model passing range:** the grid rhos where that model has PASS75.

**Predictions (confidence):**
- **C2a:** 75% completion is non-decreasing in rho within each model (16.0, 16.5, 16.7, 16.9, 17.1), with one step down of 1 allowed (70%).
- **C2b:** 75% completion >= 5/6 at some grid rho <= 17.1 in both models (55%).
- **C2c:** TERM in both models at 16.7 (70%); TERM in both models at 17.1 (45%).
- **C2d:** PASS75 in >= 1 of the 6 grid runs (50%); a window (both models PASS75 at the same rho) (30%).
- **C2e:** 50% completion <= 1/6 in all 6 runs (75%).
- **C2f:** 25%, single-cell and unrelated cues recruit 0 in all 6 runs (85%).

## Budget, order, reporting
- 8 sims, all queued at once. No result changes another run. Order: C1 (2), then C2 by increasing rho. Up to 2 reruns for load failures, counted.
- Each run takes about 20 min, 3 at a time.
- Outputs: README section C, `resultsC.md`, LEARNINGS entry, deviations as C1, C2, ... in DEVIATIONS.md.
- The report gives completion counts, event durations (median and max *last*, stops100), non-member events, and the silence checks per run.
