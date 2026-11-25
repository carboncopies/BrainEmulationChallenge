# neuron_reset_ahp PREREGISTRATION_E (2026-11-24; written before any simulation of step E; not edited afterwards, changes go to DEVIATIONS.md as E1, E2, ...)

John approved two follow-ups to step D, run together (4 sims):
- **(1) Held-out check:** the step-D L1 rho-held design on both models, with a new set of cue subsets not used in any earlier run.
- **(3) Pre-fixed rule:** boost every member whose in-assembly input is below mean - 1 SD. The cells are chosen from the matrix only, not from observed failures. rho is held at 16.5, tested with the same new cues.

**Same rules as before:**
- Patched instance only. Main NES 3156209 / API 1972355 untouched. No emails, git or pushes.
- Model-file copies only (arm N0, no field changed), deleted after each run.
- At most 3 simulations at once across all workers. Restart the separate build if RSS > 10 GB between runs. Delete every simulation.
- The build is at 9.36 GB now and three starts add about 2 GB, so I restart it once before the first run, as John expected. Its PIDs will then differ from 2397163 / 2397757; the restart is logged.

**Limits (asserted in code):**
- per pair <= 6.86 nS
- AMPA weight in [0.1, 1.0] of grown G
- NMDA r = 1.0 nominal
- GABA x1
- The input cap (3T = 49.5 nS total Pyr->Pyr input per cell) is NOT enforced. It is reported below and per run.

**Common:**
- A17 assemblies on s77777 and s66666.
- Spacing 9,000 ms, r 1.0, GABA x1, original neurons, single-spike cue.
- Base matrix E16.5 (run_nr2.make_scaled, rho 16.5).
- Runner `run_nr5.py SEED ARM`; analysis `analyze_e.py` (step-D measures).

## New cue subsets (fixed now)
- **Generator:** the same as every earlier run (`run_pl.make_events`: 1 full, 6 x 75% = 13 cells, 6 x 50% = 9, 6 x 25% = 4, 4 single cells, 4 unrelated 8-cell cues, shuffled). The key is `'E<n>-s<seed>'` instead of `'s<seed>'`.
- **Draw rule.** The first draw (`E-`, which I looked at) cued s66666 cells 28 and 57 in all six 75% events, which would leave the boosted cells untested. Before preregistering I therefore fixed a coverage rule that uses no outcome:
  - take the first n = 1, 2, ... such that, on both models, no 75%/50%/25% subset repeats any subset in any earlier raw file (this folder and `../partial_cue`);
  - and every cell boosted by either arm (s66666: 28, 46, 57, 65; s77777: 3, 65, 70) is uncued in >= 2 of the six 75% events and >= 2 of the six 50% events.
  - The first such n is **1111**: key `E1111-`. 0 subsets repeat.
- The same cues are shared by both arms. They are recorded in `cues_E_s66666.json` (md5 9e18b110...) and `cues_E_s77777.json` (md5 775a231e...).

**75% and 50% subsets** (cue cells):

s66666:
- 75%: {8,14,19,29,34,39,43,46,64,66,77,79,91}; {8,14,29,34,39,43,46,57,64,66,77,87,91}; {8,14,19,28,34,39,46,57,65,77,79,87,91}; {8,19,28,29,34,39,43,57,64,65,66,87,91}; {14,19,28,29,34,39,43,46,57,66,77,79,91}; {8,14,28,29,34,39,64,65,66,77,79,87,91}
- 50%: {8,14,43,57,65,66,77,87,91}; {8,14,28,29,64,65,66,77,87}; {19,29,34,39,46,64,65,79,87}; {8,14,28,29,34,43,57,66,87}; {8,28,39,43,57,64,77,79,91}; {8,28,34,39,46,57,66,77,79}

s77777:
- 75%: {3,4,11,40,42,46,58,65,67,70,81,87,94}; {3,11,19,40,41,42,46,58,61,65,70,81,87}; {4,11,19,40,41,42,46,58,61,65,67,87,94}; {11,19,40,41,42,58,61,65,67,74,81,87,94}; {3,4,11,19,40,46,58,67,70,74,81,87,94}; {3,11,19,40,41,42,46,58,67,70,74,81,94}
- 50%: {3,4,42,46,58,61,65,67,94}; {4,11,42,46,65,67,70,74,87}; {3,19,40,42,58,61,67,81,87}; {11,41,42,58,61,65,70,74,81}; {11,19,40,41,46,65,70,74,81}; {11,19,40,42,46,58,74,87,94}

The 25%, single-cell and unrelated subsets and the event order are in the JSON files.

## Arms (boost to the mean member in-assembly input, L1; rho held at 16.5 by the step-D fixed point)
- **D (held-out check):** the boosted cells are the step-D failing cells (s66666 28, 46, 57; s77777 65, 70), exactly as step D L1-hold.
- **P (pre-fixed):** the boosted cells are every member with in-assembly input < mean - 1 SD on the base E16.5 matrix, selected once before the boost.

**Computed before running** (`run_nr5.py --design-only`; nS):

| model | arm | boosted cells (base in-assembly input) | selection threshold | boosted to | other members' mean after | max pair | total input of boosted cells | members > 49.5 nS |
|---|---|---|---|---|---|---|---|---|
| s66666 | D | 28 (11.68), 46 (15.89), 57 (14.50) | - | 16.50 | 16.50 | 3.30 | 52.5 / 29.1 / 28.1 | 1 (28) |
| s66666 | P | 28 (11.68), 57 (14.50), 65 (14.52) | 14.65 | 16.58 | 16.58 | 3.30 | 52.6 / 28.2 / 47.3 | 1 (28) |
| s77777 | D | 65 (11.76), 70 (13.74) | - | 16.88 | 16.88 | 4.23 | 51.5 / 49.54 | 3 (hub 3, 65, 70) |
| s77777 | P | 3 (9.80), 65 (11.76), 70 (13.74) | 13.99 | 16.72 | 16.72 | 4.06 | 64.2 / 51.4 / 49.4 | 2 (3, 65) |

- P differs from D by adding s66666 cell 65 and s77777 hub cell 3, and by leaving out s66666 cell 46 (15.89, above the threshold), which failed in step D.
- So P is a real test of the matrix-only rule: if 46 is again the weak link, P fails on s66666 where D does not.
- **Input cap, stated plainly:** P raises the s77777 hub cell to 64.2 nS of total input, 30% over the cap. That is the largest cap violation of the study.

## Success criteria (per run)
**PASS75**, all of:
- 75% completion >= 5/6;
- every completing (full/75%/50%) event ends within 100 ms (stops100: no Pyr spike in [t+100, t+450));
- 25%, single-cell and unrelated cues recruit no cell in 30 ms;
- no event has non-member Pyr spikes in 450 ms.

Reported but not part of the pass: 50% completion (and PASS_T, which adds 50% >= 4/6), median and max *last*, spikes per member, JOIN of each boosted cell (75% and 50% events where it is uncued), the missing members in incomplete 75% events, and the input cap.

**Step verdicts:**
- **Held-out check (1):** generalises if D gives PASS75 on both models; partial if on one; fails if on none.
- **Pre-fixed rule (3):** works if P gives PASS75 on both models.

**Limitation:** no unboosted (base) run with the new cues is included (budget about 4). So an improvement over base cannot be shown on these cues; only the absolute criteria are tested. The JOIN of the boosted cells is compared with their JOIN in the step-D base run, which used different cues and is a weak comparison.

## Predictions (confidence)
- **E1:** D gives PASS75 on s77777 (70%) and on s66666 (60%); on both (50%).
- **E2:** P gives PASS75 on s77777 (65%) and on s66666 (45%); on both (35%).
- **E3:** in D, every boosted cell joins >= 75% of the 75% events where it is uncued (pooled per model) (70%).
- **E4:** in P on s66666, at least one incomplete 75% or 50% event misses cell 46 (45%).
- **E5:** 50% completion <= 1/6 in all 4 runs (65%).
- **E6:** silence (25%, single-cell, unrelated recruit 0) in all 4 runs (85%).
- **E7:** where 75% < 6/6, at least one missing member was not boosted in that arm (60%; not testable if every run is 6/6).

## Budget, order, reporting
- 4 sims: D s66666, D s77777, P s66666, then P s77777 when a slot frees. Up to 1 rerun for a load failure, counted.
- Outputs: README section E, `resultsE.md`, LEARNINGS entry, deviations E1, E2, ...
