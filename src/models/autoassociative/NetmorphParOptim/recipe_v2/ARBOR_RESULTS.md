# Interneuron arbor growth experiments: measured results vs pre-registered predictions

Run 2026-11-12 09:34-10:58 PST on our own NES (localhost:8000), after the predictions in `ARBOR_DESIGN.md` (timestamped 2026-11-12 09:31:18 PST). The prediction block below is copied verbatim from that file; `ARBOR_DESIGN.md` was not edited. No git repo touched, no commit.

## Summary

- Pyr->Pyr control: only A is within the 5% rule (+2.5%). B (-8.8%), C (-8.1%), D (+18.8%) moved more than 5% from 71924 and are **flagged as discarded** per the design rule. The echoes show the added lines were applied as written, so the movement is not a config-reading problem; the arbor change reshuffles the random sequence and the whole network is a new realisation (design 2.1 item 6), and here that realisation shifts Pyr->Pyr by more than the predicted range. The flagged runs are still reported below; they should not be used as clean tests of the lever.
- Decision rule: **STOP the arbor route.** D gives 10 of 48 drivable (<16) and an inhibitory fraction of 0.63% (<3%). Neither "go further" condition holds (needs >=20 drivable or Int->Pyr >2000; D has 10 and 542). D itself is a flagged run (Pyr->Pyr +18.8%), but the stop conclusion holds on its numbers and also on every other config (best drivable is 10 of 48 in both A and D).
- After-A check: Pyr->Int 539 (>=300), passed. After-B check: Int->Pyr 298 (<450) triggered the "stop and inspect echo" rule; the echo was inspected (all six lines applied with intended values), and the task instruction was to run all four, so D and C were run. B was also a flagged run.
- Direction of effects: dendrite lever (A) worked as predicted (Pyr->Int x2.4, Int->Int x2.4, Int->Pyr unchanged). Axon lever (B) did NOT raise Int->Pyr (298 vs 348 baseline) or Int->Int (102 vs 108); the predicted x1.9 axon length did not show up in synapses. Wall times did not increase (0.90-1.11 of 1260 s), far below the predicted 1.3-1.8.

## Observed vs predicted (central [10-90 range]); HIT = observed inside range, mechanical

Baseline a (measured, phase 1): Pyr->Pyr 71924, Pyr->Int 227, Int->Pyr 348, Int->Int 108, drivable 6, zero input 26, inhib fraction 0.5%, wall 1260 s.

| Quantity | Config | Predicted | Observed | Hit/Miss |
|---|---|---|---|---|
| Pyr->Int | A | 455 [300-650] | 539 | HIT |
| Pyr->Int | B | 227 [170-300] | 246 | HIT |
| Pyr->Int | C | 455 [300-650] | 407 | HIT |
| Pyr->Int | D | 700 [430-1050] | 688 | HIT |
| Int->Pyr | A | 348 [270-440] | 422 | HIT |
| Int->Pyr | B | 660 [450-950] | 298 | MISS |
| Int->Pyr | C | 660 [450-950] | 299 | MISS |
| Int->Pyr | D | 1010 [650-1500] | 542 | MISS |
| Int->Int | A | 216 [140-330] | 262 | HIT |
| Int->Int | B | 205 [130-320] | 102 | MISS |
| Int->Int | C | 410 [250-680] | 166 | MISS |
| Int->Int | D | 970 [500-1700] | 380 | MISS |
| Drivable (of 48) | A | 9 [5-13] | 10 | HIT |
| Drivable (of 48) | B | 6 [3-9] | 4 | HIT |
| Drivable (of 48) | C | 9 [5-13] | 8 | HIT |
| Drivable (of 48) | D | 12 [7-18] | 10 | HIT |
| Zero pyr input | A | 15 [9-21] | 17 | HIT |
| Zero pyr input | B | 26 [21-31] | 27 | HIT |
| Zero pyr input | C | 15 [9-21] | 16 | HIT |
| Zero pyr input | D | 11 [5-17] | 16 | HIT |
| Inhib frac onto pyr % | A | 0.5 [0.4-0.6] | 0.57 | HIT |
| Inhib frac onto pyr % | B | 0.9 [0.6-1.3] | 0.45 | MISS |
| Inhib frac onto pyr % | C | 0.9 [0.6-1.3] | 0.45 | MISS |
| Inhib frac onto pyr % | D | 1.4 [0.9-2.0] | 0.63 | MISS |
| Pyr->Pyr | A | 72000 [69000-75000] | 73735 | HIT |
| Pyr->Pyr | B | 72000 [69000-75000] | 65616 | MISS |
| Pyr->Pyr | C | 72000 [69000-75000] | 66103 | MISS |
| Pyr->Pyr | D | 72000 [69000-75000] | 85447 | MISS |
| Wall ratio | A | 1.05 [0.9-1.2] | 0.96 | HIT |
| Wall ratio | B | 1.3 [1.05-1.6] | 0.92 | MISS |
| Wall ratio | C | 1.35 [1.1-1.7] | 0.9 | MISS |
| Wall ratio | D | 1.8 [1.3-2.5] | 1.11 | MISS |

Hits: A 8 of 8, B 3 of 8, C 3 of 8, D 3 of 8. Inhibitory fraction is observed as 100 x Int->Pyr / (Int->Pyr + Pyr->Pyr). Wall ratio = wall / 1260 s.

### Raw measured values (analyze_arbor.py, same conventions as analyze_p1.py; `arbor_results.json`)

| cfg | Pyr->Pyr | vs 71924 | Pyr->Int | Int->Pyr | Int->Int | mean Pyr syn per Int | Int >=13.84 nS from pyr | Int zero pyr input | inhib frac | mean GABA onto a pyr cell (wt 1) | wall s | ratio to 1260 s | Pyr->Pyr rule |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 73735 | +2.5% | 539 | 422 | 262 | 11.2 | 10/48 | 17 | 0.57% | 3.5 nS | 1207 | 0.96 | ok |
| B | 65616 | -8.8% | 246 | 298 | 102 | 5.1 | 4/48 | 27 | 0.45% | 2.5 nS | 1156 | 0.92 | DISCARD (flag) |
| D | 85447 | +18.8% | 688 | 542 | 380 | 14.3 | 10/48 | 16 | 0.63% | 4.5 nS | 1396 | 1.11 | DISCARD (flag) |
| C | 66103 | -8.1% | 407 | 299 | 166 | 8.5 | 8/48 | 16 | 0.45% | 2.5 nS | 1140 | 0.90 | DISCARD (flag) |

## Decision rule outcome

- After A: Pyr->Int 539 >= 300: continue (passed).
- After B: Int->Pyr 298 < 450: rule says stop and inspect the echo. Echo inspected, directives applied as intended; continued as instructed (run all four). B flagged (Pyr->Pyr -8.8%).
- After D: 10/48 drivable (<16) and inhibitory fraction 0.63% (<3%): **stop the arbor route**. Not reached: >=20 drivable or Int->Pyr >2000. The "go further" and "16-19, run C and an extra D seed" branches do not apply. C was run anyway (run order A, B, D, C): 8/48 drivable, no improvement.
- Caveat: D, B, C are flagged by the 5% Pyr->Pyr rule. Per the design these do not test what they claim; if the team wants clean tests, the flagged configs would need repeating (not done: instruction was not to run extra configs).

## Config echo check (step 2)

The Netmorph parameter echo is the directive file `<sim-uuid>/<timestamp>_.nibr.clp` in `/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/`. (The sibling `*_report` directories were empty.) For every run all four D_synmax lines (1.5 pyr-pyr, 0.1 for the three interneuron pairs) and every added directive were present, verbatim, at the end of the file. No value was ignored or differed, and there was no duplicate key.

| cfg | echo file | added lines present |
|---|---|---|
| A | eb52a1ae-0b5b-472d-bfb1-da1c0edaded3/202611120934_.nibr.clp | interneuron.min_basal=4; max_basal=8: yes |
| B | 5bc0cf01-ef3d-407c-b93f-86b1eb06b997/202611120955_.nibr.clp | 6 axon lines (tau=864000): yes |
| D | 78bebc45-0c5a-4145-998e-af6bb28de2b4/202611121014_.nibr.clp | min_basal=6, max_basal=8, 6 dendrite lines (B_inf 3.5, tau 259680, E 0.73), 6 axon lines (tau 432000): yes |
| C | ce3b0324-418a-4113-b692-7e689363df30/202611121038_.nibr.clp | min_basal=4, max_basal=8, 6 axon lines (tau 864000): yes |

Limit of this check: the .nibr.clp is the directive text as sent, not Netmorph's internal post-parse parameter dump. It confirms that the lines reached Netmorph unaltered, not that Netmorph acted on them. The B result (no Int->Pyr gain, no wall-time rise) is consistent with the design's own unconfirmed point (section 1.1 item 2 and 3.3): the axon branching override may have had less effect than modelled, or axon length did not translate to synapses. This was not investigated (no morphology data was extracted).

## Growth-cone counts at day 25 (from the Netmorph run folders, `*_net.txt.growthcones`, counted by soma neuron type)

This is the only morphology evidence collected; it was read after the runs, from the same folders as the echoes. No baseline (config a) folder was available to me, so A (whose axon settings equal the baseline) is the nearest reference for axons, and B (default dendrites, mean 3 primary) for dendrites.

| cfg | interneuron dendrite cones (per cell) | predicted per cell (design 2.1) | interneuron axon cones (per cell) | predicted per cell | pyramidal dendrite cones | pyramidal axon cones |
|---|---|---|---|---|---|---|
| A | 1081 (22.5) | about 25 (6 x 4.2) | 3560 (74) | 80 (baseline) | 5459 | 6899 |
| B | 577 (12.0) | about 12.6 (3 x 4.2) | 3021 (63) | 143 | 5431 | 6874 |
| C | 1086 (22.6) | about 25 | 3084 (64) | 143 | 5350 | 7277 |
| D | 1423 (29.6) | about 40 (7 x 5.7) | 3487 (73) | 174 | 5508 | 7222 |

Reading: the dendrite lever acts as designed (interneuron dendrite tips scale with primary-dendrite count and B_inf, within about 25% of the estimate). The axon lever does not: shortening tau from 19.5 d to 10 d (B, C) or 5 d (D) did not increase interneuron axon growth cones (63-73 per cell against 74 in A, and the design predicted 143-174). So the echo shows the axon lines were sent, but the growth-cone data show no effect in the predicted direction; that explains the Int->Pyr and Int->Int misses. Either the inherited axon branching parameters differ from the design's assumption, or the lines are parsed but the van_Pelt model with these values does not give the predicted tip counts. Not resolved here. Pyramidal cone counts also differ by up to 5% across runs (new random realisation), consistent with the Pyr->Pyr movement.

Netmorph warnings files: A, C, D: only "2004 samples were empty" (statistics collection). B additionally had 5 warnings "Unable to place arbors at desired minimum angular separation" for interneurons (IDs 53, 36, 33, 30, 23; 3 arbors each, constraint [0.314, 3.142]); placement continues anyway (per design 3.2).

## Commands

- `cp grow_v2.py grow_v3.py` then edited: added EXTRA directive lists per config (A, B, C, D; text exactly as in ARBOR_DESIGN.md section 2.2), `CAP=3600` (was 1500), run folders `grow_arbor_<X>`, model names `v2-arbor-<X>`. Everything else as grow_v2.py: bio_check assertion, seed 20240628, base config a (96/48, 10, 120, 30, 0.9, days 25), D_synmax 1.5/0.1/0.1/0.1, memory guard 100 GB (MemAvailable was about 350-367 GB), SIGTERM only on our own client, `-savemodels -deleteresident`.
- Runs, one at a time with at least 25-30 s pause (python = BrainGenix/BrainEmulationChallenge/venv/bin/python):
  - `python grow_v3.py A` (09:34, 1207 s)
  - `python grow_v3.py B` (09:55, 1156 s)
  - `python grow_v3.py D` (10:15, 1396 s)
  - `python grow_v3.py C` (10:39, 1140 s)
- Measurement: `python analyze_arbor.py A B D C` (a copy of analyze_p1.py pointing at grow_arbor_<X>/ and writing `arbor_results.json`).
- Files: `grow_arbor_<X>/` (model_v2<X>, run.log, result.txt, viz/sample_0000.json), `grow_arbor_<X>.log`.

## Anomalies

- No timeouts (cap 3600 s, longest run 1396 s). No server/connection failures, no retries needed. Memory never close to the guard.
- Pyr->Pyr moved >5% in B, C and D (flags above). Pyr->Pyr is not independent of the interneuron arbor settings here, even though only interneuron lines were added.
- Wall time did not rise with larger arbors (B and C faster than the 1260 s baseline); prediction of 1.3-1.8x missed. Wall time spread across configs (0.90-1.11) is within the roughly 15% run-to-run spread noted in the design.
- Another agent may have used the server during these runs; nothing indicated interference.
- Saved models: v2-arbor-A, v2-arbor-B, v2-arbor-C, v2-arbor-D (names as passed to gen_autonm_labels, which may append an index suffix as in phase 1).

## Prediction block (copied verbatim from ARBOR_DESIGN.md, written 2026-11-12 09:31:18 PST)

### 2.3 Predictions (central value, 10-90% range in brackets)

| Quantity | baseline a (measured) | A | B | C | D |
|---|---|---|---|---|---|
| Interneuron dendrite length factor (estimate) | 1 | 2.0 | 1 | 2.0 | 3.1 |
| Interneuron axon length factor (estimate) | 1 | 1 | 1.9 | 1.9 | 2.9 |
| Pyr->Int synapses | 227 | 455 [300-650] | 227 [170-300] | 455 [300-650] | 700 [430-1050] |
| Int->Pyr synapses | 348 | 348 [270-440] | 660 [450-950] | 660 [450-950] | 1010 [650-1500] |
| Int->Int synapses | 108 | 216 [140-330] | 205 [130-320] | 410 [250-680] | 970 [500-1700] |
| Interneurons (of 48) with >= 13.84 nS from pyramidal | 6 | 9 [5-13] | 6 [3-9] | 9 [5-13] | 12 [7-18] |
| Interneurons with no pyramidal input | 26 | 15 [9-21] | 26 [21-31] | 15 [9-21] | 11 [5-17] |
| Inhibitory fraction onto pyramidal | 0.5% | 0.5% [0.4-0.6] | 0.9% [0.6-1.3] | 0.9% [0.6-1.3] | 1.4% [0.9-2.0] |
| Pyr->Pyr synapses (control, should not move) | 71924 | 72000 [69000-75000] | 72000 [69000-75000] | 72000 [69000-75000] | 72000 [69000-75000] |
| Wall time relative to 1260 s | 1.0 | 1.05 [0.9-1.2] | 1.3 [1.05-1.6] | 1.35 [1.1-1.7] | 1.8 [1.3-2.5] |
