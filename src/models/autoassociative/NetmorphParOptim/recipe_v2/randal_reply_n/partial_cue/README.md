# partial_cue: mechanism test of partial-cue completion in the patched build (2026-11-23)
33 simulations (32 complete + 1 load failure rerun; cap 50), 5.7 h summed wall, max 3 sims at once across workers (arbor-seeds' fr_dyn.py shares the patched instance), every simulation deleted. Patched instance only (NES 8011 / API 8010, venv python, patched client; restarted once at 22:19, own build only). Main NES 3156209 / API 1972355 untouched; no emails, no git, no pushes; `bio_ranges.json` untouched.
Files: PREREGISTRATION.md (written before any sim, unedited), DEVIATIONS.md (8 items), run_pc.py, run_queue.sh, analyze_pc.py -> results_tables.md, events.json, raw_*.json (spikes, programming read-back, input flags), log_*.txt, queue.log.

## Short answer
1. **3-of-4 partial cues complete at NMDA r 0.56 (not only r 1.0) once the cue->non-cue AMPA conductance per pair is 5.5 nS instead of 4.125 nS (D1): 40/40 events over 3 models, with zero recruitment from single cells (0/40) and from unrelated cells (0/12 mixed cues) and clean full cues (10/10).** All values are inside the stated limits (pair <= 6.86 nS, AMPA weight 0.09-1.0, NMDA r <= 1.0 nominal, GABA x1-x2). The R3 control (4.125 nS, D0) reproduces the old result on a grown-default background: r 0.56: 0/40, r 1.0: 40/40.
2. **2-of-4 cues complete only at the cap (D2, 6.86 nS, i.e. limited by grown G per pair): 6/60 (10%) at r 0.56 and 18/60 (30%) at r 1.0**, strongly different between memories (s33333 2/18, s66666 6/18, s77777 10/24 at r 1.0). It never reaches the 50% criterion. Another 11 events at r 1.0 get one of the two non-cue cells to fire without completing (recruitment 29/60). 1-cell cues recruit nothing anywhere (0/40 in every cell of the table), and no event anywhere produced a spurious (non-member) spike within 30 ms.
3. **GABA x1 vs x2 changes nothing**: s33333 outcomes are identical event by event for all 4 designs x 2 r (0 differences), and there was no reverberation, no runaway and no contamination in any of the 32 runs (so GABA had nothing to contain; contrast nmda_gaba_exp, which had a c = 1.5 nS background on every pair).
4. **The "learned assembly" question (Q2) is NOT answered.** DL (STDP-saturated member pairs) differs from D2 in only 4-7 pairs per model (the R3 memories have few, weak cue-cue pairs) and the spikes are identical. It cannot say whether a dense allocated assembly opens or closes the window. fresh_learn Stage 1's prediction (the window closes) therefore remains untested in the simulator. See DEVIATIONS 8.

## Results (f = 1, pooled over s33333, s66666, s77777; non-contaminated events; contaminated = 0; runaway = 0 in all runs; k/n)
| design (cue->non-cue AMPA per pair) | r | full complete | full clean | 3-of-4 complete | 2-of-4 complete | 1-cell recruits | unrelated x2 recruits |
|---|---|---|---|---|---|---|---|
| D0 R3 control (4.125 nS) | 0.56 | 10/10 | 10/10 | **0/40** | 0/60 | 0/40 | 0/12 |
| D0 | 1.0 | 10/10 | 10/10 | **40/40** | 0/60 | 0/40 | 0/12 |
| D1 (5.5 nS) | 0.56 | 10/10 | 10/10 | **40/40** | 0/60 | 0/40 | 0/12 |
| D1 | 1.0 | 10/10 | 10/10 | 40/40 | 0/60 | 0/40 | 0/12 |
| D2 (6.86 nS cap) | 0.56 | 10/10 | 10/10 | 40/40 | 6/60 | 0/40 | 0/12 |
| D2 | 1.0 | 10/10 | 10/10 | 40/40 | **18/60** | 0/40 | 0/12 |
| DL (STDP-saturated members; = D2 in effect) | 0.56 / 1.0 | 10/10 | 10/10 | 40/40 | 6/60 / 18/60 | 0/40 | 0/12 |
GABA x2 (s33333 only): identical outcomes to x1. Full table incl. recruitment: results_tables.md. Per memory set, 3-s spacing, 4-spike cue over 1.5 ms.
PASS_3 (window open for 3-of-4): D0 r 1.0, D1 r 0.56 and 1.0, D2, DL. PASS_2 (2-of-4 >= 50%): none.

## Preregistered predictions scored
| | prediction | observed | score |
|---|---|---|---|
| P0 | D0 f1: 3-of-4 r 0.56 <= 10%, r 1.0 >= 90%; 2-of-4 0% | 0/40, 40/40, 0/60 | HIT |
| P1 | D1: 3-of-4 >= 90% at both r; 2-of-4 <= 10% | 40/40 both; 0/60 | HIT |
| P2 | D2: 2-of-4 >= 30% at r 1.0; 3-of-4 >= 95%; full clean >= 95% at r 0.56 but < 95% at r 1.0 | 18/60 = 30.0% (boundary); 40/40; clean 10/10 at both | 2 of 3 clauses hit, third missed: **MISS** (conjunctive) |
| P3 | DL: 2-of-4 >= 50% and 1-cell recruitment >= 25%; full clean < 95% at r 1.0 | 30% / 0% / clean 10/10 | MISS (DL ~ D2, untested design, DEVIATIONS 8) |
| P4 | f2 vs f1 changes partial completion <= 10 points; f2 lowers non-clean full cues >= 30% at r 1.0 | 0 points; no non-clean full cues at either f | first part HIT, second uninformative |
| P5 | unrelated x2 recruit nothing in D0-D2; DL >= 90% silent | 0/12 recruit everywhere, DL 100% silent | HIT |
| P6 | some design passes PASS_3 at f1; none passes PASS_2 | D0 r1, D1, D2, DL pass; none passes PASS_2 | HIT / HIT |
| P7 | in DL where 2-of-4 >= 50%, 1-cell recruitment > 10% | 2-of-4 never >= 50% | uninformative |

## Flags and limits (read these before quoting any number)
- **Input cap NOT met** (DEVIATIONS 3): member cells in all designs, D0 included, have 100-136 nS Pyr->Pyr input (grown default 0.2 x G plus programmed), above the lp_weights 3T = 49.5 nS cap; 6-9 hub-like member cells per model exceed it (the grown graphs, not my programming). The completion numbers hold on that background and I do not claim input-cap compliance.
- D1/D2 raise cue->non-cue pairs above the R3 value 4.125 nS (made for the 25%-silence design rule of math_run). Capacity and cross-talk with more memories were not tested here: only the 3-4 disjoint memories of each model, no overlap designs, no second-cue tests. A bigger cue->non-cue weight also lowers the number of memories that fit under the per-cell input cap (math_run); not re-computed.
- NMDA r 1.0 is nominal; achieved ~0.60 on cue->non-cue (s77777 D2: 0.596), 0.51 on loops (simulator caps NMDA at the grown peak 0.55 nS/synapse). Unprogrammed pairs keep grown AMPA + NMDA (DEVIATIONS 4); background differs from nmda_gaba_exp (c = 1.5 on every pair there).
- One cue timing (4 spikes in 1.5 ms), 3-s spacing (history effect avoided, as asked), one event per cue combination per memory, deterministic simulator (Seed 0): rates are over memories x cue subsets, not independent trials. Three models.
- Model reach: s66666_D2 etc. results differ by memory (2-of-4 0.1-0.42), so the 30% pooled figure is memory-set dependent.
- Completion window 30 ms, abstracted LIFC, STDP off.

## What this means (for John / Randal)
- Randal's partial completion (25% missing) is reachable at r 0.56 with per-pair cue->non-cue AMPA of 5.5 nS (inside the per-pair cap) without breaking silence for single cells or unrelated cells. The nmda_gaba_exp "needs r 1.0" result was a consequence of the R3 value sitting at the threshold edge.
- 50% missing (2 of 4) needs per-pair AMPA at the cap and still completes only 10-30% of the time; with 4 cue cells and a 6.86 nS cap two cells deliver at most 13.7 nS, under the 16.5 nS threshold; completion happens only on pairs whose grown G gives the extra margin plus NMDA. More cue cells per memory (larger assemblies) or a lower relative threshold is a design question, not an API one.
- GABA is irrelevant to the partial-cue decision (arrives after it; again) and irrelevant to reverberation here because none occurs at this background.
- Open: learned dense assemblies (Q2). Needs allocated memories; ~17 sims of the cap remain.

---
# Addendum B (2026-11-24): dense, STDP-saturated assemblies in the simulator (Q2). PREREGISTRATION_B.md, DEVIATIONS B1-B3
11 more simulations (total 44 of 50), same instance/limits/gate (<= 2 mine, <= 3 total with arbor-seeds; main NES/API untouched; no emails/git/pushes). Files: PREREGISTRATION_B.md (before any addendum sim), alloc_b.py/json, run_pl.py, run_queue_b.sh, analyze_pl.py -> resultsB_tables.md, eventsB.json, rawB_*.json, logB_*.txt.

## Short answer
1. **The two-assembly design cannot be made dense in this graph, so I did not run it (B1).** My preregistered density gate (A17 + disjoint A12; >= 90% of members with >= 22 nS in-assembly ceiling input and >= 90% threshold-model 75%-cue completion) failed on all 10 models: the second assembly gets 0-17% of members with enough input and 0-5% completion. Same as fresh_learn Stage 1 (never 2 assemblies). I ran a **reduced best-case test instead: one assembly A17 (17 cells, 17.7% of Pyr cells, allocated as a dense subgraph, 79-84% of possible pairs present) on s77777 (passes the gate) and s66666 (near-gate: 88% of members >= 22 nS)**. Two models, one assembly each: a mechanism test, not a capacity test.
2. **Learned assembly without homeostasis (L0: all member pairs at min(G, 6.86) nS): the window is closed, as in fresh_learn Stage 1.** 25%-cues (4 of 17) recruit the assembly in 30/30 events (both models, r 0.56 and 1.0, GABA x1 and x2), 50% and 75% cues complete 29/30 and 30/30, single cells and unrelated cues recruit nothing (1/20 and 0/20). Every completion reverberates (full cue not clean in every run; Pyr spikes > 50 in 450 ms in 29-30 of 30 completing events; in L0 some events keep firing for 2-3 s, up to the 3-s window). GABA x2 changes nothing (25%-recruitment 6/6 vs 6/6; mean 450-ms Pyr spikes 115 vs 111).
3. **With the homeostasis script (LH: per-cell multiplicative scaling to 3T = 49.5 nS, as in fresh_learn) the window opens, which the threshold model did not predict: 25% cues stay silent (0/24 recruit over both models, both r), 75% cues complete 24/24, 50% cues complete 18/24 (s66666 5/6 at both r; s77777 6/6 at r 1.0 but 2/6 at r 0.56), single cells and unrelated cues recruit nothing (0/16, 0/16).** But the completed assembly then **reverberates**: 11-13 of 27 events per run exceed 50 Pyr spikes in 450 ms; median 360-650 spikes in 450 ms (17 cells, ~65 Hz average over the 450 ms, I computed this post hoc), activity lasts ~200-440 ms (median last Pyr spike after the cue) and GABA x1 does not stop it. In s66666 12 events also recruit non-member cells within 30 ms (spurious), in s77777 none. So by the preregistered PASS definition (75% completes, 25% silent, single/unrelated silent, **full cue clean**) **no arm passes**; the failing item is the reverberation, not the completion-silence window. Whether a 200-440 ms, ~65 Hz assembly burst is biological is not checked here (unverified; the preregistered "clean" criterion is stricter than CA3 may require).
4. **Strong inhibitory drive (LI: all Pyr->Int at weight 1.0, R3 strength) stops the full-cue reverberation (full cue clean in both models, 27-48 Pyr spikes) but not the partial-cue ones**: 25% cues recruit 12/12, 75% cues still run for 100-2,900 ms. So extra inhibition does not open the window either.
5. **Threshold-model fidelity:** for L0 the threshold model agrees with the simulator on completion (55/57) and recruitment (125/128), trivially (everything ignites). For LH it under-predicts completion: agreement 30/48 on completion; e.g. s77777 LH r 1.0 50% cues: simulator 6/6 complete, threshold model 1/6. So Stage 1's "window does not open" holds without homeostasis but is not the whole story with it: NMDA/timing/background in the simulator lets a cap-scaled assembly complete from 50% cues while staying silent for 25%.

## Results table (non-contaminated events, k/n; full table with the threshold reference: resultsB_tables.md)
| model | arm | r | GABA | full clean | 75% complete | 50% complete | 25% recruit | 1-cell recruit | unrelated recruit | spurious | members over 3T input |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s77777 | L0 | 0.56 / 1.0 | x1 | 0/1, 0/1 | 6/6, 5/5 | 6/6, 6/6 | 6/6, 6/6 | 0/4, 0/3 | 0/3, 0/4 | 0 | 13/17 |
| s77777 | L0 | 1.0 | x2 | 0/1 | 5/5 | 6/6 | 6/6 | 0/3 | 0/4 | 0 | 13/17 |
| s77777 | LH | 0.56 / 1.0 | x1 | 0/1, 0/1 | 6/6, 6/6 | 2/6, 6/6 | 0/6, 0/6 | 0/4, 0/4 | 0/4, 0/4 | 0 | 1/17 (hub cell 3, floor 57.2 nS) |
| s77777 | LI | 1.0 | x1 | 1/1 | 5/5 | 6/6 | 6/6 | 0/3 | 0/4 | 0 | 13/17 |
| s66666 | L0 | 0.56 / 1.0 | x1 | 0/1, - | 6/6, 6/6 | 6/6, 5/5 | 6/6, 6/6 | 0/4, 0/4 | 0/4, 0/4 | 19, 18 | 9/17 |
| s66666 | LH | 0.56 / 1.0 | x1 | 0/1, 0/1 | 6/6, 6/6 | 5/6, 5/6 | 0/6, 0/6 | 0/4, 0/4 | 0/4, 0/4 | 12, 12 | 0/17 |
| s66666 | LI | 1.0 | x1 | - | 6/6 | 5/5 | 6/6 | 0/4 | 0/4 | 17 | 9/17 |
"-" = the single full-cue event was contaminated by a preceding reverberation and excluded.

## Input-cap status (honest)
L0 and LI: **cap not met**: 13/17 (s77777) and 9/17 (s66666) members exceed 49.5 nS Pyr->Pyr input (max 176 and 136 nS) because saturated assembly pairs push members far above it. LH: met by construction except a hub cell (s77777 cell 3, grown floor input alone 57.2 nS; 1 member; 0 cells in s66666). So **the only arm that respects the input cap is the one with the homeostasis script, and it is the one where the window opens.** Per-pair <= 6.86 nS and AMPA weight within [0.1, 1.0] hold everywhere (asserted); NMDA r <= 1.0 nominal (achieved lower, see raw program read-back), GABA x1-x2.

## Preregistered predictions (A17 only, DEVIATIONS B1) scored
| | prediction | observed | score |
|---|---|---|---|
| Q1 | >= 2 of the first 3 models pass the density gate for both assemblies | 0 of 10 | MISS |
| Q2 | L0: A17 25% cues recruit >= 50%; no L0 assembly passes | 30/30; none passes | HIT (A12 part n/a) |
| Q3 | L0 A17 75% completion >= 80% | 30/30 (all events; non-contaminated 28/28) | HIT |
| Q4 | LH 75% completion <= 60%; no LH assembly passes | 24/24 complete; none passes (fails on clean/reverberation) | first part MISS, second HIT |
| Q5 | L0 full cues not clean in >= 50% at r 1.0 x1 | 0 clean (only 1 event per run) | HIT |
| Q6 | GABA x2 vs x1 and LI vs L0 change 25%-recruitment by <= 10 points | 0 points both (but LI stops full-cue reverberation, not predicted) | HIT |
| Q7 | threshold model agrees with the simulator on complete/not in >= 80% (L0) | 55/57 (L0); LH only 30/48 | HIT (L0) / see 5 |
| Q8 | (changed, B1) A17 passes in none of the arms | none passes | HIT |

## Limits (read before quoting)
Two models, one assembly each (s66666 below the preregistered gate by 2 points); 6 cues per size, deterministic simulator (rates over cue subsets, not independent trials); learning is programmed (saturation), not run through SetSTDP; the homeostasis script is a sketch (3T cap my choice, multiplicative scaling down only), outside NES; one cue timing (spread over 1.5 ms); 3-s spacing; Pyr->Int at the grown default except LI; no overlap, no second assembly (cannot be made dense), no capacity claim; the 3T cap is the lp_weights value, not a measured biological number.

## What this means
- A single dense 17-cell (17.7%) assembly CAN show partial-cue completion with silence for 25% cues, single cells and unrelated cues in the simulator, but only with the input-cap homeostasis (LH); without it any cue of 25% or more ignites it (L0, matches Stage 1).
- What goes wrong is no longer the window but the aftermath: the completed assembly reverberates for ~0.2-0.4 s (and in L0/LI sometimes seconds) at high rate; GABA x1-x2 does not end it. If Randal's requirement is "GABA silences the network after a pattern", this design fails it; strong feedback inhibition (LI) stops full-cue reverberation but not the partial-cue one.
- Capacity: a second dense assembly cannot be allocated in these graphs (gate failure on 10/10 models), so learned assemblies at 8-23% activity give about one memory per model, consistent with fresh_learn Stage 1. The mechanism result (homeostasis opens the window) does not change the capacity verdict.
- Next steps if John wants more (6 sims of the cap left): test whether reducing recurrent drive after the cap (e.g. cap 2T, or weaker assembly pairs below the ceiling) removes the reverberation while keeping completion; and ask Randal whether a 200-440 ms assembly burst is acceptable.

---
# Addendum C (2026-11-24): weaker assembly pairs with the 49.5 nS cap kept (PREREGISTRATION_C.md, DEVIATIONS C1-C2)
6 sims (the last of the 50-sim cap: 44 + 5 complete + 1 load failure that I did not rerun), same two models, same A17 assemblies, same 27 events/cue subsets as addendum B, r 1.0, GABA x1, Pyr->Int grown default. Arms: **W70** = member pairs at 0.7 of the ceiling (then the same 3T cap scaling as LH), **W50** = 0.5, **H2** = full-ceiling pairs with a 2T = 33 nS cap (s77777 only). Reference: LH from addendum B. Files: PREREGISTRATION_C.md, pwlib.py, run_pw.py, run_queue_c.sh, analyze_pw.py -> resultsC_tables.md, eventsC.json, rawC_*.json, logC_*.txt.

## Short answer
1. **There is a narrow sweet spot, and it is model dependent.** On s77777, W70 (pairs at 70% of the ceiling, cap 49.5 nS) gives **75% cues complete 5/6 with no reverberation** (median 20 Pyr spikes in 450 ms versus 465 for LH; 0/6 runaway), 25% cues silent (0/6), single-cell 0/4, unrelated 0/4, no spurious spikes, full cue clean. On s66666 the same W70 completes 5/6 too but **reverberates in 5/5 completed events for ~340-370 ms** (median 548 spikes vs LH 627) and recruits non-member cells in 6 events: no relief.
2. **50% cues no longer complete** in any weaker arm (W70 0/6 in both models; W50 0/6) while LH completed 5-6 of 6: the weakening trades the 50%-cue completion for the end of the reverberation. Completion from 75% cues (25% missing) survives only at 0.7, not at 0.5: **W50 completes nothing (0/6 in both models) and neither does H2 on s77777 (0/6, cap 2T)**; none of them reverberate (median 9-17 Pyr spikes in 450 ms, 0 runaway). So the window between "too weak to complete" and "completes and runs away" is narrow, between 0.5 and 0.7 of the ceiling at cap 3T, and does not coincide in the two models.
3. **Strict preregistered PASS_C (6/6 completion + no runaway in >= 5/6) is met by no arm**; s77777 W70 misses it by one cue (5/6). By the looser "reverberation relief" criterion (median pyr450 at least halved vs LH with completion >= 5/6) s77777 W70 qualifies, s66666 W70 does not. This is one model, one assembly, 6 cues per size, one weight factor: not a robust result.
4. **What the successful case is:** a 17-cell assembly (17.7% of Pyr cells) that completes from 13 of 17 cells, is silent for 4 of 17, 1 cell and unrelated cells, and fires once without reverberation, with weights below the ceiling (mean member-pair weight 0.55 of G, no pair above 0.9) and the input cap respected except one hub cell (s77777 cell 3, floor 57.2 nS). It does not complete from 50% cues, so "partial completion" holds to 25% missing only, like the R3 D1 result.

## Results table (non-contaminated events, k/n; contamination 0 in all runs; runaway = pyr450 > 50; full table incl. threshold reference: resultsC_tables.md)
| model | arm | 75% complete | 50% complete | 25% recruit | 1-cell | unrelated | spurious events | median pyr450 (75%) | runaway (75% events) | full clean | members > 49.5 nS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s77777 | LH (B) | 6/6 | 6/6 | 0/6 | 0/4 | 0/4 | 0 | 465 | 6/6 | 0/1 | 1 (hub) |
| s77777 | **W70** | **5/6** | 0/6 | 0/6 | 0/4 | 0/4 | 0 | **20** | **0/6** | 1/1 | 1 (hub) |
| s77777 | W50 | 0/6 | 0/6 | 0/6 | 0/4 | 0/4 | 0 | 15.5 | 0/6 | 1/1 | 1 (hub) |
| s77777 | H2 (2T) | 0/6 | 0/6 | 0/6 | 0/4 | 0/4 | 0 | 15 | 0/6 | 1/1 | 1 (hub) |
| s66666 | LH (B) | 6/6 | 5/6 | 0/6 | 0/4 | 0/4 | 12 | 627.5 | 6/6 | 0/1 | 0 |
| s66666 | W70 | 5/6 | 0/6 | 0/6 | 0/4 | 0/4 | 6 | 548.5 | 5/6 | 0/1 | 0 |
| s66666 | W50 | 0/6 | 0/6 | 0/6 | 0/4 | 0/4 | 0 | 14.5 | 0/6 | 1/1 | 0 |
| s66666 | H2 | not run (load failure, cap reached) | | | | | | | | | |
Threshold-model reference (same weights and cues): W70 completes 1/6 of 75% cues in both models, while the simulator completes 5/6; W50/H2 0/6 in both. The threshold model under-predicts completion again, now by a larger margin.

## Preregistered predictions scored
| | prediction | observed | score |
|---|---|---|---|
| C1 | W70 75% completion >= 5/6 in both models; W50 <= 3/6 in at least one | 5/6 and 5/6; 0/6 and 0/6 | HIT / HIT |
| C2 | W70: >= half of the completing 75% events runaway; W50: <= 50% runaway where it completes | pooled 5 of 10 completed events runaway (exactly half) but 0/5 on s77777 and 5/5 on s66666; W50 never completes | boundary HIT, split by model; W50 part n/a |
| C3 | no W arm passes PASS_C in both models; some (model, W arm) shows relief | none passes (strict: none at all); s77777 W70 shows relief | HIT / HIT (relief predicted at 35%) |
| C4 | 25% silent and single/unrelated 0 in every W and H2 run | 0/6, 0/4, 0/4 in all 5 runs | HIT |
| C5 | H2: completion <= LH's, 25% silent; median pyr450 lower than LH in both models | s77777: 0/6, silent, 15 vs 465; s66666 not run | HIT on s77777; second model untested |
| C6 | 50%-cue completion LH >= W70 >= W50 on each model | 6/0/0 and 5/0/0 | HIT |
| C7 | some arm completes >= 5/6 with >= 5/6 non-runaway events (30%) | s77777 W70 | HIT (existence, one model) |

## Limits
Two models, one assembly each, factors 0.7/0.5 and cap values (3T, 2T) are my choices; 6 cues per size and a deterministic simulator, so 5/6 vs 6/6 is one cue; learning is programmed, homeostasis a script outside NES; NMDA r 1.0 only (nominal; achieved lower); GABA x1 only; no second assembly (cannot be allocated dense, addendum B); no overlap or interference test, so no capacity claim; reverberation threshold (50 Pyr spikes in 450 ms) is a convention. s66666 H2 not run (load failure, cap reached).

## What this means
- Reverberation of dense assemblies is not unavoidable: below the ceiling (about 0.7) with the cap kept, a single assembly can complete from 75% cues, stay silent for 25% cues and fire without a 200-440 ms burst (s77777). But it is the narrow band between "does not complete" (W50, H2) and "reverberates" (LH, s66666 W70), and the band sits at different strengths in the two models, so a real learning rule would need a regulation mechanism (a set-point on total drive, inhibition tuned to the assembly) rather than a fixed pair strength, and this is not shown here.
- Combined with addendum B: the cap-respecting arms are the only ones with a window; the capacity verdict (one assembly per model) is unchanged.
- The sim cap of 50 is used up. Open: s66666 H2; a finer strength sweep (0.6, 0.8) and more models/cue draws to see if the band is robust; GABA x2 in the W70 arms; run the assembly through real SetSTDP. Each needs John's go and new sims.
