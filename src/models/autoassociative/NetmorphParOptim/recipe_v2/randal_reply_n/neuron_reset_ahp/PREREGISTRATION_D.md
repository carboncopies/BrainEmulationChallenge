# neuron_reset_ahp PREREGISTRATION_D (2026-11-24; written before any simulation of step D; not edited afterwards, changes go to DEVIATIONS.md as D1, D2, ...)

John approved option (a) from the step-C report: boost only the inputs of the member cells that consistently failed to join 75% cues. Run at rho about 16.5, with original neurons, a single-spike cue and 9 s spacing.

**Same rules as before:**
- Patched instance only (NES 2397163 / API 2397757). Main NES 3156209 / API 1972355 untouched. No emails, git or pushes.
- Model-file copies only (arm N0, no field changed), deleted after each run.
- At most 3 simulations at once across all workers. Restart the separate build if RSS > 10 GB between runs. Delete every simulation.

**Limits (asserted in code):**
- per pair <= 6.86 nS
- AMPA weight in [0.1, 1.0] of grown G
- NMDA r = 1.0 nominal
- GABA x1
- The input cap (3T = 49.5 nS of total Pyr->Pyr input per cell) is NOT enforced. It is reported below and per run, and the boost puts boosted cells over it.

**Common to all runs** (as C):
- A17 assemblies on s77777 and s66666, with the same 27 cue subsets in the same order.
- Spacing 9,000 ms, r 1.0, GABA x1.
- Runner `run_nr4.py SEED LEVEL HOLD`; analysis `analyze_d.py`, with the analyze_nr / analyze_b measures and criteria (TERM, PASS75, PASS_T).

## Failing cells (fixed now, from B2 and C)
These are the non-cue members missing in every incomplete 75% event at rho 16.0-17.1:
- **s66666:** 28, 46, 57.
- **s77777:** 65, 70.

**Offline check** (before running; base design E16.5; in-assembly input = sum of member→cell AMPA conductance, nS):

| model | failing cell | in-assembly input | rank (0 = lowest of 17) | member mean ± SD |
|---|---|---|---|---|
| s66666 | 28 | 11.68 | 0 | 16.64 ± 1.99 |
| s66666 | 57 | 14.50 | 1 | |
| s66666 | 46 | 15.89 | 4 | |
| s77777 | 65 | 11.76 | 1 | 16.94 ± 2.95 |
| s77777 | 70 | 13.74 | 2 | |

The failing cells are the members with the least in-assembly input. Two members as low that do not fail (s77777 hub cell 3, 9.80; s66666 cell 65, 14.52) are not boosted. Cell 3 has a large non-member input (57 nS total). I report this rather than add them.

## Boost rule
- **Boost.** For each failing cell m, every incoming member AMPA pair (pre in A17, grown pair present) becomes min(s_m · X[a, m], min(G[a, m], 6.86)). s_m >= 1 is found by bisection so that the cell's in-assembly input equals the target. Nothing else is changed: non-member inputs, NMDA (r 1.0 of the programmed AMPA, as before), and GABA x1.
- **Levels:**
  - L1: target = mean member in-assembly input.
  - L2: target = mean + 1 SD.
- **HOLD = free:** boost the E16.5 design once. rho rises, so a gain increase is mixed in.
- **HOLD = hold:** alternate the boost with a rescale of all member pairs above the 0.1 G floor (X = fl + k(X - fl), k bisected to rho = 16.5) until a fixed point. At the fixed point, the failing cells sit at the target of the final matrix and rho = 16.5 exactly. This takes 6-10 iterations; the other members lose 3-6% of their in-assembly input.

**Computed before running** (`run_nr4.py --design-only`):

| # | model | level | hold | rho | failing cells' in-assembly input (nS) | other members' mean (nS) | max pair (nS) | total input of failing cells (nS) | members > 49.5 nS |
|---|---|---|---|---|---|---|---|---|---|
| base (B2) | s66666 | - | - | 16.50 | 11.7 / 15.9 / 14.5 | 17.20 | 3.45 | 47.7 / 28.4 / 26.1 | 0 |
| 1 | s66666 | L1 | hold | 16.50 | 16.50 each | 16.50 | 3.30 | 52.5 / 29.1 / 28.1 | 1 (cell 28) |
| 2 | s66666 | L2 | hold | 16.50 | 17.88 each | 16.11 | 3.41 | 53.9 / 30.4 / 29.4 | 1 (cell 28) |
| 3 | s66666 | L1 | free | 17.08 | 16.64 each | 17.20 | 3.45 | 52.7 / 29.2 / 28.2 | 1 (cell 28) |
| base (B2) | s77777 | - | - | 16.50 | 11.8 / 13.7 | 17.50 | 4.40 | 46.4 / 46.4 | 1 (hub 3) |
| 4 | s77777 | L1 | hold | 16.50 | 16.88 each | 16.88 | 4.23 | 51.5 / 49.54 | 3 (hub 3, 65, 70) |
| 5 | s77777 | L2 | hold | 16.50 | 19.33 each | 16.58 | 4.15 | 54.0 / 52.0 | 3 |
| 6 | s77777 | L1 | free | 17.04 | 16.94 each | 17.50 | 4.40 | 51.6 / 49.6 | 3 |

- No boosted pair reaches its ceiling. The largest boosted weight is 0.87 of G (s66666 cell 57, L2).
- **Input cap, stated plainly:** the boost puts every boosted s77777 cell and s66666 cell 28 above 49.5 nS. Cell 70 at L1 is 0.04 nS over. Cell 28 was already the top-input s66666 member (47.7 nS). So most of its input comes from non-members, and the boost makes it the only s66666 member over the cap.

## Measures added
- **JOIN (per boosted cell):** the fraction of non-contaminated 75% and 50% events, where the cell is not cued, in which it fires within 30 ms. It is compared with the same events in the B2 E16.5 base run.
- **New failures:** non-cue members missing in incomplete 75% events, listed per run.

## Predictions (confidence)
- **D1:** in the held runs (1, 2, 4, 5), each boosted cell joins 75% events more often than in the base run (JOIN 75% higher). This holds in L1-hold on both models (75%) and in L2-hold on both (80%).
- **D2:** 75% completion >= 5/6 on both models in L1-hold (45%); in L2-hold (55%).
- **D3:** TERM on both models in L1-hold (60%); in L2-hold (45%).
- **D4:** a window, i.e. PASS75 on both models in the same design (L1-hold, L2-hold or L1-free) (35%). PASS75 on s66666 in any run (50%).
- **D5:** L1-free on s66666 does not TERM (at least 1 completing event without stops100) (60%). The comparison is C rho 17.1 uniform, 4/5 ignited.
- **D6:** 50% completion <= 1/6 in all 6 runs (65%).
- **D7:** 25%, single-cell and unrelated cues recruit 0 in all 6 runs (85%).
- **D8:** where 75% is still < 6/6, at least one missing member in the failed events is a cell that was not boosted (a new weakest link) (55%).

## Budget, order, reporting
- 6 sims, queued at once (order 1, 4, 2, 5, 3, 6). No result changes another run. Up to 1 rerun for a load failure, counted.
- Outputs: README section D, `resultsD.md`, LEARNINGS entry, deviations D1, D2, ...
- The report gives 75%/50% completion, event durations, non-member events, silence checks, JOIN of the boosted cells, and the input-cap status.
