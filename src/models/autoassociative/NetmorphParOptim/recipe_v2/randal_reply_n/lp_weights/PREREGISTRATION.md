# lp_weights PREREGISTRATION (written 2026-11-22, before any solver run; not to be edited afterwards, deviations go in DEVIATIONS.md)

Task: offline weight design (candidate 1 of math_scout/SCOUT.md) on the 10 grown E4 networks. No sims, no emails, no pushes, no NES contact. Everything below is fixed before the first LP is solved. The solver enforces the constraints; checking afterwards is only a second line of defence.

## 0. What the API can do (read from code, not run): per-pair weights are settable
Code read in `/home/johnjose/BrainGenix/BrainGenix-NES/Source/Core/Simulator/`:
- `RPC/SimulationRPCInterface.cpp:73-75, 595-660`: routes `Simulation/SetPrePostStrength` (PreSyn, PostSyn, Conductance_nS) and `Simulation/BatchSetPrePostStrength` (vectors), plus `SetAllStrength`.
- `Structs/Simulation.cpp:1358-1392`: `UpdatePrePostStrength` forwards to the post-synaptic neuron; the batch version aborts at the first pair that fails (returns false -> `BGStatusInvalidParametersPassed`).
- `LIFCompartmental/LIFCNeuron.cpp:543-559`: for a pre-synaptic neuron ID, the FIRST AMPA receptor entry gets `weight = NewConductance_nS / g_peak_sum_nS`; every other receptor entry from that pre cell (NMDA, and any later AMPA) is set to weight 0; the function returns false if no AMPA entry exists for that pair.
Consequences for this design: (a) weights are per PAIR (all synapses of a pair share one weight, so a per-synapse weight is the pair weight); (b) only pairs that have an AMPA entry are settable (Pyr->Pyr and Pyr->Int; GABA pairs, Int->Pyr and Int->Int, are NOT settable through this call, so inhibition stays as grown and Dale's law holds trivially for it); (c) programming a pair removes its NMDA component; (d) the code does NOT clamp the weight to 0.1-1.0 or to any bound, so the bounds below are ours to enforce.

## 1. Hard constraints (in the solver as variable bounds or linear constraints)
Variables: for every EXISTING grown Pyr->Pyr pair (i, j) with as-grown peak-conductance sum G_ij (nS, from `g_peak_sum` of the E4 viz dump; per synapse 0.98 nS = 0.02 nS x 49 receptor units, the NES default), the programmed pair conductance x_ij, weight w_ij = x_ij / G_ij.
1. **Existing pairs only.** Variables exist only for pairs with G_ij > 0 in the dump. No pair is added, no synapse count or morphology changed. Pyr->Int and Int->* pairs are not variables (kept as grown, weight 1, except that the earlier R3 rule that caps the summed cue input to any interneuron at 10 nS is kept when quoting R3 numbers; it does not enter the threshold model below).
2. **Dale's law.** x_ij >= 0 for excitatory pre cells (all variables are pyramidal outputs); inhibitory pairs are not variables and keep their as-grown sign and size. No sign can flip because no variable has a negative range.
3. **Weight limits.** 0.1 <= w_ij <= 1.0 for every variable pair (PRIMARY; the 0.1-1.0 dm.weight hard limit of bio_ranges.json read as the allowed per-pair weight range). That means no pair may be silenced (w = 0 is outside the limit); every grown pair keeps at least 10% of its grown strength. A SENSITIVITY run lets w go to 0 ("silent synapses", Randal's suggestion), reported separately and marked as outside the stated limit. Note: bio_ranges.json itself only contains dm.weight 0.1-1.0 as a growth parameter; it has no per-synapse conductance limits, so the per-pair cap below is a separate choice.
4. **Per-pair conductance cap.** x_ij <= min(G_ij, 6.86 nS). Source of 6.86 nS: Randal Koene's autoassociative example, `BEC/src/models/autoassociative/autoassociative_connectome.py:75-79` (27.44 nS combined at maximum weight / cue size 4 = 6.86 nS per pre-post pair; 7 "supersynapses" x 0.98 nS, `LIFtest.py:444` `SUPERSYNAPSES=7`). The largest Pyr->Int value in his examples is 8 x 0.98 = 7.84 nS (`LIFtest.py:445`), not used here (Pyr->Int is not a variable). Literature cross-check: NOT possible in conductance units (the search found unitary CA3-CA3 EPSPs of about 0.56 mV from 1-2 synaptic contacts, Guzman et al. 2016, snippet only; no nS value), so I mark the cap "source = example code; literature UNVERIFIED". Because w <= 1 the cap also enforces "n synapses x per-synapse maximum": x_ij <= n_ij x 0.98 nS = G_ij (constraint 3 of the task).
5. **Homeostatic cap on total input.** For every pyramidal cell j: sum over i of x_ij <= H, with H = 3 x T = 49.5 nS (T = 16.5 nS is the firing threshold of the threshold model, `ovlib.py:T`). This H is MY CHOICE, not a sourced number (its meaning: all of a cell's pyramidal inputs together cannot drive it beyond 3 times its firing threshold). Sensitivity: H = 2T (33 nS) and 5T (82.5 nS). If a cell's lower bound sum_i 0.1 G_ij already exceeds H the model is declared infeasible for that H and reported.
6. **Objective.** Stage A: minimise sum_ij w_ij (L1 of the weights, so the smallest weights). Stage B: with the stage-A optimum fixed to within 2%, minimise the largest weight among the pairs that stage A raised above 0.1 (uniformity). A maximal-weight objective is never used.

## 2. The offline threshold model (the NES-like model of `ripple_overlap_j/ovlib.py`)
A cell fires if the summed programmed conductance x from the cells that have fired reaches T = 16.5 nS (ovlib.py: `T = 16.5`; the R3 rule gives each cue->non-cue pair T/4 = 4.125 nS, so 4 cue cells just reach T and 3 give 12.375 nS). Cue cells are forced to fire. Closure: iterate until no new cell fires. Timing, GABA, NMDA, adaptation and noise are NOT modelled; a design that is feasible here is not shown to recall in NES (that needs sims, not allowed here). In the earlier sims the effective firing threshold was somewhat below 16.5 (an observed cross-completion at 16.2 nS, `ripple_overlap_j/README.md` section 2), so I use a margin:
- intended firing: input >= T = 16.5 nS;
- unintended non-firing: input <= T - 4.125 = 12.375 nS (the same margin R3 has for a 3-cell cue). Sensitivity: unintended <= 14.0 nS.
A memory = 4 cue cells C + m non-cue cells N (m = 2 for "6-cell", m = 4 for "8-cell"); members M = C u N.
Linear constraints per memory (all in x, so LPs):
 (i) for every n in N: sum_{c in C} x_cn >= 16.5 (a cue completes the memory);
 (ii) for every n in M \ S and every 3-subset S of C: sum_{c in S} x_cn <= 12.375 (a 3-cell cue does not complete anything; includes the 4th cue cell);
 (iii) for every cell m' not in M: sum_{f in M} x_fm' <= 12.375 (the completed memory does not fire any outsider: no cross-completion, no spurious spikes; includes the cells of other memories not in M).
Overlaps: any number of memories in one LP; shared cells have the same role everywhere is NOT required (a cell may be cue in one memory and non-cue in another) unless stated; pairwise shared-cell count k <= 0, 1, 2 or 3.

## 3. What will be solved (on each of the 10 models: s16180, s27182, s31415, s11111, s22222, s33333, s44444, s55555, s66666, s77777)
A. **Single memory**: the largest m (non-cue cells) for which some 4-cue set is feasible (m = 2, 4, 6); the count of feasible 4+2 memories (each checked alone).
B. **Many memories, disjoint (k = 0)**: greedy sequential packing (candidates ordered by their capacity slack, 3 random orders; keep a memory only if the joint LP stays feasible), reporting the largest set found. Lower bounds.
C. **Overlapping**: same for k <= 1, 2, 3 (shared cells counted over all members), and 8-cell (4+4) memories at k = 0 and k <= 3.
D. **Capacity versus the fixed R3 rule**: compare with the R3 counts in `ripple_overlap_j/README.md` section 1 (6-cell: k=0, <=1, <=2, <=3; 8-cell k=0, <=3), the same graph and the same pair data. Because the R3 counts at k >= 2 were shown in sims to cross-complete, the table also reports the R3-programmed designs evaluated in my threshold model (step E).
E. **Validation of the threshold model against the existing sims (offline)**: program the 49 existing overlap designs (`design_*.json`) with the R3 rule at c = 0 (`ovlib.pair_list_ov`) and ask the cascade model whether each cued memory cross-completes; compare with the sim outcomes (`events_ov.json`, c = 0, GABA on).
F. **Weight statistics** for every solved design: fraction of variable pairs at the lower bound 0.1 (+- 0.001), at the per-pair cap (x within 1% of min(G, 6.86)), fraction of programmed cue->non-cue pairs at the cap, distribution of w among raised pairs, median and 90th percentile of x, per-cell total input relative to H; shape of the distribution of x for the raised pairs (log-scale histogram, skew of log x), compared with the biological expectation that synaptic strengths are roughly lognormal with many weak and few strong (Song et al. 2005 PLoS Biol, from memory, UNVERIFIED; Brunel 2004 for >50% silent in an optimal perceptron, VERIFIED in SCOUT.md).
G. **Flags**: any design that has more than 50% of its raised pairs on the cap, any cell with total input within 2% of H, any LP whose optimum has the margin active everywhere, and any solution that needs w = 0.1 on all non-memory pairs (a spike at the lower bound) is flagged as "on the bounds". The report says plainly whether the solutions look biological.

## 4. Predictions (probabilities are my belief that the statement holds)
P1. Single 4+2 memory count per model under the LP is at least the R3 disjoint count in 10 of 10 models (95%); the median across models is 1.2-2.5 times the R3 disjoint count (60%); the LP never finds a 4+6 memory (80%).
P2. Disjoint (k = 0) 6-cell packing: LP count is 3-8 per model (median 5) (60%), larger than R3 in at least 8 of 10 models (70%).
P3. Overlap <= 1: LP count 5-12 (median 8) (55%). Overlap <= 3: LP count under the closure constraints is much smaller than the R3 "fit" count (16-201) in 10 of 10 models (85%), and is below 40 in 9 of 10 (65%).
P4. 4+4 memories: 0-3 per model, at least one model with 2 or more at k <= 3 (60%).
P5. Weights: more than 90% of the variable pairs sit at the lower bound 0.1 in every solution (85%, trivial because of the L1 objective); among raised pairs, at least 50% are on the per-pair cap (70%, because 4 pairs must sum to 16.5 nS and the cap is 6.86 nS while grown pairs carry about 2 nS); the distribution of x for raised pairs is NOT lognormal-like (bimodal: lower bound plus cap) (75%).
P6. Homeostatic cap H = 49.5 nS binds (a cell within 2% of H) in fewer than 5% of cells for k = 0 designs (70%), and in more cells for k <= 3 (60%).
P7. Threshold-model validation (step E): the model predicts "no cross-completion" for at least 90% of F1 designs and "cross-completion" for at least 70% of the F2 and F3 designs in which the sims showed cross-completion (65%).
P8. Sensitivity: allowing w to 0 raises the capacity by less than 30% on average (65%); H = 2T lowers it by more than 30% on average (55%).
P9. Overall, I do NOT expect to be able to call the LP weights "biological": I expect the memory pairs to sit on the 6.86 nS cap (55% that more than half of memories need that).

## 5. Scoring
HIT = value inside the stated range or the statement true; PARTIAL = within 25% beyond a range; MISS otherwise. Every prediction is scored in README.md, with the miss list stated plainly.

## 6. Rules for the run
- Seeds: random orders use `numpy.random.RandomState(seed)`, seed = 0, 1, 2 (three greedy orders).
- Solver: scipy 1.10.1 `linprog` with HiGHS (no other solvers available here).
- Any change to the constraints, the numbers above, or the thresholds after the first solve is written to DEVIATIONS.md with the reason and the time.
- No NES, API, git or email contact. Reads only: the viz dumps in each model folder, `ripple_overlap_j` JSON files, and source code.
