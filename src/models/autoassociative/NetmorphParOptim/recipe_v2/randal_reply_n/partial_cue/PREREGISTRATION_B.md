# partial_cue PREREGISTRATION_B (addendum, 2026-11-23; written before any simulation of this addendum and before any allocation was computed; not edited afterwards, changes go to DEVIATIONS.md)

John approved spending the remaining sims (cap 50 total; 33 used, so <= 17) on Q2 of PREREGISTRATION.md: **does a dense, STDP-saturated assembly (allocated as a dense subgraph, as in fresh_learn) open the completion-silence window in the real simulator, or does it ignite from small cues / reverberate?** The first DL arm was not a test (DEVIATIONS 8: R3 memories have few cue-cue pairs).
Same rules: patched instance NES 8011 / API 8010 only, venv python, patched client; main NES 3156209 / API 1972355 untouched; no emails, no git, no pushes; `bio_ranges.json` untouched. **Total concurrent sims across all workers <= 3** (arbor-seeds' recall queue and growths use the same instance; gate counts python processes `run_exp|fr_dyn|dyn*|run_pc|run_pl`; I run at most 2). Limits: per-pair <= 6.86 nS, AMPA weight in [0.1, 1.0] of grown G, NMDA r <= 1.0 nominal (simulator caps ~0.5-0.8 achieved), GABA x1-x2, Dale (only Pyr AMPA/NMDA touched), nothing relaxed.

## Memories (offline allocation, fixed before running)
- Library: `fresh_learn/fllib.py` (`Net`, `alloc` = greedy dense-subgraph search with swaps, 300 restarts, numpy seed 7, best objective; `build_F`). Per model: **A17** (k = 17, 17.7% of 96 Pyr cells) allocated first, then **A12** (k = 12, 12.5%) allocated disjoint (overlap 0) from A17. Both in the same simulation (2 assemblies per sim, activity per assembly in the CA3-like 8-23% band, 30% of cells in assemblies together - flagged).
- **Density gate (fixed now):** a model is used only if, in the threshold model (T = 16.5 nS, `cascade_batch`, learned weights w/o homeostasis), (a) >= 90% of the members of each assembly have in-assembly ceiling input (sum of min(G, 6.86) from the other members) >= 22 nS (= T/0.75) and (b) >= 90% of 20 random 75% cues complete the assembly exactly. Models are tried in the order 33333, 66666, 77777, 44444, 55555, 11111, 22222, 16180, 27182, 31415 until 3 models pass. **If fewer than 3 pass the gate for both assemblies, I run only on those that pass (>= 1) and report that the design cannot be made dense enough on the others; if none pass, I run nothing and say so.**
- Learning = every existing ordered member pair set to its ceiling min(G, 6.86) nS (potentiation-only STDP saturates co-active pairs, stdp_k). **Programmed directly through the API, not run through SetSTDP** (stated plainly; NES has no depression/homeostasis; the homeostasis arm is a script, outside NES). Source of the homeostasis idea: multiplicative synaptic scaling (Turrigiano et al. 1998 Nature 391:892-896; Turrigiano 2008 Cell 135:422-435; heterosynaptic competition Chistiakova et al. 2015 Front Comput Neurosci 9:89; all VERIFIED earlier in fresh_learn).

## Arms (per model; 5 sims) and total
- **L0**: learned assemblies, no homeostasis, Pyr->Int at the grown default. r in {0.56, 1.0}, GABA x1. (2 sims)
- **LH**: L0 + homeostatic scaling (fresh_learn `build_F` Hmode 3.0: per-cell multiplicative scaling of the above-floor input to H = max(3T = 49.5 nS, floor sum); all scaled pairs programmed). r in {0.56, 1.0}, x1. (2 sims)
- **LI**: L0 + Pyr->Int at R3 strength (w = 1.0, all Pyr->Int pairs: strongest feedback inhibition, the best case for GABA to open the window), r 1.0, x1. (1 sim)
- **GABA x2 contrast**: L0, r 1.0, x2, first model only. (1 sim)
3 models x 5 + 1 = **16 sims**; 1 reserve for a load-failure rerun (cap 17; every rerun counted).
Programming order as before: AMPA (legacy batch call), then NMDA = r x programmed AMPA on programmed Pyr->Pyr/Pyr->Int pairs with an NMDA group, then GABA = f x 0.2 x grown peak; full read-back, abort on mismatch. Unprogrammed pairs stay at the grown state (AMPA w 0.2 and grown NMDA).

## Events (3.0 s apart, first at 20 ms; cue spikes spread linearly over 0-1.5 ms across the cue cells)
Per assembly: 1 full cue; 6 cues of 75% of the members (ceil), 6 of 50%, 6 of 25% (floor), 4 single-cell cues (random members) = 23; plus 4 unrelated cues of 8 cells drawn outside both assemblies. 50 events (150 s). Cue subsets drawn with fixed RandomState seeds (stored). The threshold-model outcome for the same cues (same weights) is computed offline as a reference and compared.

## Measures (windows from cue onset t)
Completion: all members spike in [t, t + 30). Recruitment: any Pyr cell that is not a cue cell fires in [t, t + 30). Spurious: a Pyr cell outside both assemblies fires in [t, t + 30). Late: member spikes in [t + 15, t + 450); non-member Pyr spikes in [t, t + 450); full cue clean = no late member spike and <= 2 non-member spikes; runaway = > 50 Pyr spikes in [t, t + 450). Contaminated = > 60 Pyr spikes in the 1,500 ms before (excluded from rates and counted; raw counts also reported).
**Assembly PASS (window open)**: 75% cues complete 6/6 with no spurious spike; 25% cues recruit 0/6; single-cell cues recruit 0/4; unrelated cues recruit 0/4; full cue clean.
**Input-cap status (reported for every arm)**: per member cell, total Pyr->Pyr input = programmed + 0.2 x G of unprogrammed pairs, versus 3T = 49.5 nS: number of member cells above, max; LH is within the cap by construction except hub cells whose floor input already exceeds it (counted); L0 and LI are expected to exceed it (DEVIATIONS 3 of the main README: even the grown default does for hubs).

## Predictions (scored HIT / MISS per statement; confidence in brackets)
- Q1 (density gate): on the first 3 models in order, >= 2 pass the gate for both A17 and A12 (55%).
- Q2 (L0, window closed by ignition): in L0 (any r, x1), for A17: 25% cues recruit in >= 50% of events pooled over models (65%); for A12: >= 25% (55%); no assembly passes PASS in L0 (75%).
- Q3 (75% completion in sim): L0 A17 75% cues complete >= 80% (60%).
- Q4 (homeostasis): LH 75% completion for A17 is <= 60% (threshold-model reference 47%) (55%); no assembly passes PASS in LH (75%).
- Q5 (reverberation): L0 full cues are not clean in >= 50% of events at r 1.0 x1 (60%).
- Q6 (GABA): x2 vs x1 (L0, r 1.0, first model) changes the 25%-recruitment fraction by <= 10 points (70%); LI vs L0 changes it by <= 10 points (60%).
- Q7 (model fidelity): the threshold model reference agrees with the simulator on complete/not complete in >= 80% of cue events in L0 (50%); disagreement is reported with its sign.
- Q8 (overall): **no arm has more than 1 PASS assembly in total (both assemblies, 3 models, 16 sims)** (70%); i.e. the window problem of fresh_learn Stage 1 reproduces in the simulator.

## Reporting
Every prediction HIT/MISS with numbers; deviations to DEVIATIONS.md; post-hoc analyses labelled; honest report including failure; append results to README.md and a learnings entry to /home/johnjose/agent-library/LEARNINGS.md.
