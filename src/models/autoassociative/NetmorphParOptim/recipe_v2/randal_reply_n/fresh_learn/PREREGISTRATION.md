# fresh_learn PREREGISTRATION, Stage 1 (written 2026-11-23, before any Stage 1 computation; not edited afterwards, changes go to DEVIATIONS.md)

Task: shortlist item 2 of `fresh_scout/FRESH.md` (John approved): learned assemblies at biological sparsity. Stage 1 = OFFLINE capacity curve on the 10 grown E4 models. Stage 2 (simulations, patched build) only if Stage 1 is a GO and only when sim slots are free (max 3 concurrent sims across all workers; at the time of writing `fable-knobs` runs 3 sims of nmda_gaba_exp on its own instance, so Stage 2 cannot start now). No NES/API call in Stage 1; main NES 3156209 / API 1972355 untouched; no emails, no pushes.

## 0. What I had already seen before writing this (so it is not a prediction)
- `fresh_scout` (2026-11-23): fraction of RANDOM patterns storable with saturated weights (threshold model, 10 models): 4 cue + 2 targets 2.2e-4, 17 + 2 targets 3.5e-2 (full cue), any-9-of-17 4.8e-4; strongest-pair pruning keeps strong pairs.
- `math_run`: distributed cues (c = 8 cue cells + 2 targets, overlap <= 2) median 6 memories under the 75% silence rule, 0 if one missing cell must stay silent, 17.5 if 50% missing may complete; hand-set weights, 4 cue x 4.125 nS.
- `stdp_k`: STDP saturates co-active programmed pairs; 3-cell silence breaks. `nmda_gaba_exp`: NMDA at c <= 1.5 changes nothing.
- lp_weights baseline (hand-set R3-like weights, 4+2, silence for 3 of 4 cue cells): primary medians 1.5 (k = 0), 2 (k <= 1).
- I had not computed any allocation search or capacity curve of assemblies.

## 1. Model (identical constraints to lp_weights / math_run, enforced in the code, not checked afterwards)
- Graph: grown Pyr->Pyr conductance ceilings G (g_peak_sum, nS) of the 10 E4 models (`lpw_lib.load`; seeds 16180, 27182, 31415, 11111, 22222, 33333, 44444, 55555, 66666, 77777). Only existing pairs carry weight. Dale: excitatory outputs x >= 0, GABA untouched. Pair ceiling U = min(G, 6.86 nS) (Randal `autoassociative_connectome.py:75-79`).
- Weight w = x / G in [0.1, 1.0] on every existing pair (floor x >= 0.1 G, ceiling x <= U). **Initial (grown) state: w0 = 0.2 on every pair (the NetMorph build default), x0 = min(0.2 G, U).** (Stage 2 starts from the same state.)
- Threshold model: T = 16.5 nS; cell fires if the summed x of fired cells >= T; cascade to fixpoint (`lpw_lib.cascade`, 20 iterations). Cue cells fire by force. No timing, no inhibition, no NMDA, no STDP dynamics in Stage 1.
- **Learning rule (stands in for STDP with random presentation order):** for an assembly A (a set of k Pyr cells that are presented together many times in random order), every ordered pair (i, j), i != j in A with G_ij > 0, is potentiated to the ceiling x_ij = U_ij (NES STDP saturates co-active pairs, stdp_k: 100% at cap after ~100 recalls). Assumption stated plainly: random presentation order makes both directions of a pair potentiate. NES has **no depression and no homeostasis**; the rule below is a script on top.
- **Homeostatic rule (script, not NES):** after learning, per-cell multiplicative scaling of the above-floor part of the incoming conductance: x_ij <- 0.1 G_ij + s_j (x_ij - 0.1 G_ij), with s_j in [0, 1] the largest value such that sum_i x_ij <= H_j. Cap H_j = max(3T = 49.5 nS, 0.1 sum_i G_ij) (the same per-cell input cap as lp_weights "primary", hub rule D2: a cell whose unavoidable floor input already exceeds the cap keeps the floor and is flagged as a hub). Sensitivity variants H = 1.5 T, 2 T, 5 T, infinity (no homeostasis). Source of the idea: multiplicative synaptic scaling preserves relative strengths (Turrigiano et al. 1998 Nature 391:892-896, VERIFIED via search result; Turrigiano 2008 Cell 135:422-435, VERIFIED), heterosynaptic competition as a complement (Chistiakova et al. 2015 Front Comput Neurosci 9:89, VERIFIED). **This is a sketch of the rule family, not a calibrated model**: the cap value (3T) and the "scale only the part above the floor" form are my choices; scaling is one-directional here (down only, because learned weights sit at the ceiling).
- Activity fractions: assembly size k in {6, 8, 12, 17, 20, 25} of 96 Pyr cells = 6.3, 8.3, 12.5, 17.7, 20.8, 26.0%. The CA3-like band 8-23% = k = 8..22 (k = 8, 12, 17, 20). k = 6 is the old memory size; k = 25 (26%) exceeds my hard flag of 25% active and is reported only as a flagged stress case.
- Overlap: two assemblies may share at most o cells; o = 0 (disjoint) or o = floor(k / 8) (k: 6 -> 0, 8 -> 1, 12 -> 1, 17 -> 2, 20 -> 2, 25 -> 3). **Primary variant: H = 3T, o = floor(k/8).**

## 2. Allocation (choosing which cells form an assembly)
Allocation to cells that already have strong pairs is part of the idea (excitability-based allocation; FRESH D5/D2) and is stated as an assumption, not hidden. Greedy dense-subgraph search per candidate: start from a random seed cell; repeatedly add the cell (not violating the overlap limit with already placed assemblies) that maximises sum over members of min(S_A(j), T / 0.75) where S_A(j) = sum_{i in A, i != j} U_ij; then 10 swap passes (replace the weakest member by the best outsider if the objective rises). 300 random restarts per (model, k). Control: **random allocation** (uniform random k-sets, 5,000 per (model, k), early exit on first failure) shows what the search adds.

## 3. Held-assembly criteria (all evaluated with the cascade on the post-homeostasis matrix of the WHOLE system of assemblies)
For every assembly A of the system, with random cue subsets (seeded by assembly index, so deterministic):
- **C75 (completion, required):** 20 random cues of ceil(0.75 k) members: at least 19 of 20 complete, completion = the cascade fires exactly all members of A and no other cell (no spurious extra cells; an extra cell counts as failure).
- **C50 (partial completion, reported, not required):** 20 random cues of ceil(0.5 k) members, same definition; reported as the fraction of assemblies with >= 50% of cues completing.
- **S25 (silence, required):** 15 random cues of floor(0.25 k) (at least 1) members of A: the cascade must fire no cell beyond the cue (no recruitment at all), 15 of 15.
- **SU (unrelated cue, required):** 15 random cues of ceil(0.5 k) cells drawn from the cells outside A, resampled until the cue contains at most floor(0.25 k) cells of any single assembly; the cascade must fire no cell beyond the cue, 15 of 15.
Limitation stated now: random cues, not adversarial; held assemblies are re-verified with 200 cues per type for the final counts.
M(k) = maximum number of assemblies in a system for which all are held (greedy packing: candidates in random order, accepted only if the whole system still satisfies the criteria and the overlap rule; stop after 150 consecutive rejections; best of 3 orderings).

## 4. Flags
Hard (disqualify a count): any weight outside [0.1, 1.0]; any pair above 6.86 nS; any cell above its input cap (by construction none, hub cells flagged); active fraction k/96 > 25% (k = 25 excluded from GO); a hub cell (floor input above the cap) inside an assembly.
**Deviation from math_run stated here:** the math_run hard flag "more than 50% of designed pairs on the upper weight bound (w >= 0.9)" cannot be applied unchanged: the learning rule under test (potentiation-only STDP) saturates co-active pairs by construction. I report the share of learned pairs with w >= 0.9 for every variant. **Go/no-go is decided on the saturation-allowed rule (B); the strict rule (A, including the w >= 0.9 hard flag) is reported next to it**, so the reader sees what is being allowed.
Soft: number of synapses per learned pair (G / 0.98): share >= 5 synapses above 20%; fraction of cells with scaling s_j < 1.

## 5. Predictions (scored HIT inside the range / PARTIAL within 25% beyond / MISS)
- P1 (random allocation): median over models of the standalone-held probability of a random k = 17 set <= 1% (85%); for k = 6, 8, 12 also <= 5% (70%).
- P2 (allocated, standalone): a standalone allocated candidate is held for >= 50% of restarts for k <= 12 (60%) and for k = 17 (45%); M(k) primary medians: k = 6: 1-2 (70%); k = 8: 1-3 (60%); k = 12: 2-5 (55%); k = 17: 2-6 (50%); k = 20: 1-4 (50%); k = 25: <= 2 (65%).
- P3 (homeostasis effect): H = 3T lowers M versus H = infinity by >= 20% at k = 17 in at least 5 of 10 models (55%); H = 1.5T lowers M at k = 17 to <= 50% of H = infinity in at least 5 of 10 models (60%).
- P4 (overlap): M with o = floor(k/8) >= M with o = 0 in every (model, k) (95%).
- P5 (partial cues): among held assemblies at primary, the fraction completing from 50% cues (C50) is <= 30% at k = 12 and 17 (70%).
- P6 (saturation): share of learned pairs at w >= 0.9 is > 50% at H = 3T for k <= 17 in all 10 models (90%); therefore the strict rule (A) fails for all models (90%).
- P7 (best size): the k with the highest median M among {8, 12, 17, 20} is 12 or 17 (60%).
- P8 (verdict): Stage 1 is a GO under rule B (50%).

## 6. Go/no-go for Stage 2 (fixed now)
GO (rule B) if ALL hold, at the primary variant:
- G1: for at least one k in {12, 17, 20}: median over the 10 models of M(k) >= 3 AND at least 7 of 10 models have M(k) >= 2;
- G2: for that k, the held assemblies pass the re-verification with 200 cues per type (>= 95% C75, 100% S25 and SU, 0 spurious extra cells);
- G3: no hard flag for that k;
- G4: the random-allocation control is at least 10 times lower than the allocated rate for that k (i.e. the result needs allocation, and this is said in the report; if it holds for random sets too, allocation is not what the result rests on).
Otherwise NO-GO; the report says which criterion failed. Reference points (not criteria): hand-set R3-like six-cell memories, 1.5-2; m = 8 distributed-cue memories in math_run, median 6 under its own rule.
Stage 2 plan (only after GO and free slots): patched instance 8011/8010, patched client, grown E4 model (s33333 first), STDP on while assemblies are presented in random order with staggered spikes, homeostasis by script between epochs (`BatchSetPrePostStrength` AMPA), stated plainly as outside NES; test recall (full, 75%, 50%, 25% and unrelated cues), runaway, with STDP off; NMDA r = 0 and 0.56, GABA x1.

## 7. Reporting
Every prediction scored in README.md; deviations in DEVIATIONS.md; post-hoc analyses labelled. Random seeds numpy RandomState. Greedy counts are lower bounds on capacity.
