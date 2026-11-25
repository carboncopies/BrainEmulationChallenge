# fresh_learn Stage 1: capacity of learned assemblies on the 10 grown E4 models (offline, 2026-11-23)

Offline only (threshold model); no NES/API call, no sim; main NES 3156209 / API 1972355 untouched; no emails, no pushes. `PREREGISTRATION.md` was written before any computation and is not edited; deviations and post-hoc items are in `DEVIATIONS.md` and labelled below. Files: `fllib.py` (model, learning + homeostasis, cue tests, allocation, packing), `run_stage1.py` -> `stage1_runs.json`, `stage1_random.json`, `results_stage1.md` (full table), post-hoc `diag_post.py`, `run_posthoc_sp.py`, `run_posthoc_crit.py`, `stats_final.py` (+ json/log).

## Verdict: NO-GO for Stage 2 as preregistered
Go criterion G1 (median over the 10 models of M(k) >= 3 and >= 7 models with M >= 2, for some k in 12, 17, 20) fails by a wide margin: **the median number of held assemblies is 0 for every k and every homeostasis variant; no model ever holds 2 assemblies; the best any model reaches is 1.** Stage 2 (simulations) was not started (also no slots: at the time, fable-knobs had `run_exp.py` sims running and a B1 growth was running).

## What was computed
10 grown graphs, grown state w0 = 0.2 on every pair, per-pair ceiling min(G, 6.86), w in [0.1, 1.0], learning = every co-active pair of an assembly saturates to its ceiling (random presentation order, both directions), homeostasis = per-cell multiplicative scaling of the above-floor input to a cap H (3T primary; 1.5T, 2T, 5T, none as variants), threshold model T = 16.5 nS. Assembly sizes k = 6, 8, 12, 17, 20, 25 (6-26% of the 96 pyramidal cells), overlap <= 0 or floor(k/8), allocation by greedy dense-subgraph search (300 restarts per placement, swap passes) so that assemblies sit on cells that already have strong pairs, greedy sequential packing, best of 3 orderings. An assembly is "held" if, in the whole system: >= 95% of 20 random 75% cues complete it exactly (no spurious extra cell), 25% cues recruit nothing (15/15), unrelated cues recruit nothing (15/15).

## Results (median over 10 models of M; full table in `results_stage1.md`)
| k (active %) | no homeostasis | H 5T | **H 3T (primary)** | H 2T | H 1.5T | models with M >= 1 (primary) |
|---|---|---|---|---|---|---|
| 6 (6.2) | 0 | 0 | **0** | 0 | 0 | 0 |
| 8 (8.3) | 0 | 0 | **0** | 0 | 0 | 0 |
| 12 (12.5) | 0 | 0 | **0** | 0 | 0 | 0 |
| 17 (17.7) | 0 | 1 (6 models) | **0** | 0 | 0 | 1 |
| 20 (20.8) | 0 | 0 | **0** | 0 | 0 | 2 |
| 25 (26.0, flagged > 25% active) | 0 | 0 | **0** | 0 | 0 | 2 |
Overlap-allowed and disjoint give identical counts. **Random allocation control: 0 of 5,000 uniform random k-sets is held, for every k and model** (so any held assembly rests on allocation).
For the held systems found (16 single-assembly systems in the k >= 12, H 3T/5T runs) the 200-cue re-verification passes for **1** (s55555, k 17, H 3T). Typical failure: completion from 75% cues 0.74-1.0 but 25% cues recruit in 0.5-13% of trials.

## Why (post-hoc diagnostics, labelled; they do not change the verdict)
1. **Window problem.** Best allocated candidate without homeostasis (`diag_post`): k = 17 completes from 75% cues in 97% of trials (median) and from 50% in 70%, but a 25% cue already recruits in 77% of trials (silence 0.23); k = 20: 100% / 95% / silence 0.07. Saturated learned weights make dense clusters ignite from small cues: the completion-silence window the preregistered criteria need does not open. Randal says partial cues should complete in CA3, so the 25% silence rule is itself debatable (question A3 in FRESH.md); dropping it was tested next.
2. **The homeostatic cap works against completion as built.** With H = 3T the same candidates complete from 75% cues only 5% (k 8), 28% (k 12), 47% (k 17), 60% (k 20): cells with strong learned input also have strong background input (0.2 x G from all grown inputs) and are scaled down hard. Cap 5T is the only variant that gives M = 1 in 6 of 10 models at k = 17, i.e. a looser cap helps. Set-point normalisation of the learned input only (X* = 1.5-3T, post-hoc) does not change this: M <= 1 everywhere (`posthoc_sp.json`).
3. **Dropping the 25%-cue silence requirement (post-hoc, NO25):** without homeostasis M = 1 in 7 of 10 models at k = 17 and 6 of 10 at k = 20, **never 2**; with H = 3T 1-3 models. Also requiring 50%-cue completion: <= 1 per model (`posthoc_crit.json`).
4. **Never two assemblies.** Cells with enough ceiling input at all are few: sum of ceilings of incoming pairs >= 22 nS on 38-58 of 96 cells, >= 33 nS on 29-48, >= 49.5 nS on 22-37 (`stats_final` log), and the strong pairs among them form one dense cluster per graph (consistent with math_run: strong pairs land on 11-22 target cells). A second assembly cannot find enough such cells within the overlap limit.

## Preregistered predictions scored
| | prediction | observed | score |
|---|---|---|---|
| P1 | random k = 17 held <= 1%; k <= 12 <= 5% | 0 of 5,000 for every k | HIT |
| P2 | allocated candidate held in >= 50% of restarts for k <= 12 (60%), k = 17 (45%); M medians k 6: 1-2, 8: 1-3, 12: 2-5, 17: 2-6, 20: 1-4, 25: <= 2 | no model has a held candidate at k <= 12 at H 3T (post-hoc best-of-10); all medians 0 | MISS x5, HIT (k 25) |
| P3 | H 3T lowers M vs none by >= 20% at k 17 in >= 5 models; 1.5T <= 50% of none | none has M = 0, so nothing to lower; 5T/3T raise M from 0 to 1 in 6 / 1 models (opposite direction); the second part is true trivially (0 <= 0) | MISS; second part uninformative |
| P4 | M(overlap) >= M(disjoint) everywhere | equal in all cells | HIT (uninformative) |
| P5 | among held assemblies 50%-cue completion <= 30% at k 12 and 17 | k 17: 0.38 (H 3T, 1 set), 0.47-1.0 (H 5T, 6 sets) | MISS |
| P6 | > 50% of learned pairs at w >= 0.9 at H 3T for k <= 17 in all models; strict rule fails | 38-45% at H 3T (homeostasis pulls weights below the bound), 70-91% at H 5T | MISS |
| P7 | best k among 8, 12, 17, 20 is 12 or 17 | all medians 0 (undefined); by models with M >= 1 at H 5T: k 17 (6 models) | uninformative |
| P8 | Stage 1 is a GO | NO-GO | MISS |

## Flags and limits
- Threshold model: no timing, no inhibition, no NMDA, no STDP dynamics; learning is an idealised saturation of co-active pairs, homeostasis a script (NES has neither depression nor homeostasis). Inhibition (GABA, feedback) is the obvious mechanism that could open the completion-silence window and is not in this model; Stage 1 cannot say it would not help.
- Greedy allocation and packing give lower bounds on M; the diagnostics show candidates that are close (e.g. k 17, 100% of members with enough input in one model), so a stronger search might find a few more, but two assemblies per model never occurred even with the silence requirement dropped.
- Random cues (20 per type), not adversarial; held assemblies were re-verified with 200 cues and mostly fail, so M = 1 is itself optimistic.
- The earlier FRESH.md number (3.5% of random 17 + 2 patterns storable) does **not** transfer: it only required two targets to be reached from the cue cells; here every member must be completed from a partial cue (random control: 0 / 5,000). This corrects an optimistic reading of FRESH.md section 2B for the "assembly" case.
- Comparison with hand-set R3 memories (1.5-4 per model) is loose: those need only the 2 target cells to be driven by 4 designed cue cells, not a mutually completing assembly.

## What this means for Stage 2 (decision for John, nothing started)
As a capacity method, learned assemblies in the grown state are not supported by Stage 1 (<= 1 assembly per model at 6-26% activity, with or without a homeostatic cap). Two things remain open and could justify a **narrower** Stage 2 that is a mechanism test, not a capacity claim: (a) does STDP + script homeostasis form the one feasible assembly of an allocated cell set and does it complete from partial cues (n = 1-2 models, ~50 sims, needs free slots); (b) does GABA open the completion-silence window that the threshold model cannot (a 25% cue recruiting without inhibition may be stopped by feedback GABA; Stage 1 has no inhibition). I recommend asking Randal whether partial cues of 25% may complete (then the NO25 variant, which still holds only 1 assembly per model, is the relevant criterion) before spending sims.
