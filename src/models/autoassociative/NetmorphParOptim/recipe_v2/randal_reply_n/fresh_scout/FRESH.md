# FRESH: review of all prior work and new ways to attack the problem (2026-11-23, offline scout)

Offline only: no simulations, no emails, no pushes. Read: both memory files, `LEARNINGS.md`, the READMEs of headline_h/i, ripple_overlap_j, stdp_k, gaba_check_l, randal_examples_m, lp_weights, math_run, bio_scout, math_scout/2, randal_reply_n (incl. `nmda_gaba_exp` **partial** results: 192 of 263 runs present, A complete, B not run, C partial, F not run), gaba_nmda_api, and the full Randal thread (26 messages; his replies are paraphrased in section 1.4). I ran five small offline computations for this scout (`tsweep.py`, `feas_random.py`, `prune_p29.py`, `prune_r3.py`, `lognorm.py`, `chains.py`, all in this folder, threshold model, greedy packers = lower bounds, 3-5 restarts). They are exploratory and **not preregistered**; treat their numbers as sizing, not as results. Where I am speculating the text says SPECULATION. Tags: VERIFIED = seen in a search result this session (title/venue/year at least); UNVERIFIED = not seen or only a number quoted by a snippet.

## 0. Short answer
- Nothing found so far beats the structural bottleneck by itself: **the grown graph has too few strong pairs (>= 5 synapses) between the right cells**, and everything so far (weights, overlap, distributed cues, pruning rules) re-expresses that.
- The cheapest real lever on the table is **keeping the strongest pairs and zeroing the weakest (weight 0, which Randal allows) in a higher-D growth** until the connection-probability bar is met: strong pairs x3.1-3.7 at p = 0.29 and 3.6 synapses per connected pair (both inside the bars), but disjoint 4+2 memory counts only x1-3 on two seeds (section 2, C). Modest, nearly free, uses existing grown models.
- Two assumptions we never questioned look wrong or at least unexamined: (a) **arbitrary patterns cannot be stored at all** in these graphs (2e-4 of random 4+2 patterns are storable even with saturated weights), so "learn by STDP from presented patterns" only works for patterns that fit the structure, unless assemblies are large (c = 17 + 2 targets: 3.5% of random assemblies, close to the ~18% CA3 activity fraction, secondary) or are *allocated* to pre-wired assemblies; (b) the neuron parameters that set the 16.5 nS threshold (Cm 100 pF, Vth - Vrest 20 mV) were never calibrated to CA3, and the literature direction (larger Cm) would make capacity **worse**, not better.
- Three experiments are proposed in section 4: strongest-pair pruning with recall check; learned assemblies at biological sparsity with script-level homeostasis; growth-programmed assemblies by per-cell steering.

## 1. Map

### 1.1 Settled (with where)
| claim | evidence |
|---|---|
| NetMorph line 379 `tx/qx` was a bug; fixed build gives PV-like Int->Pyr (9-16 synapses/pair), Pyr->Pyr x5 | linefix/README.md, toy test + 3 seeds; not yet reviewed by Randal |
| E4 recipe (V1 arbor, 20 interneurons, Pyr D 0.0175, Int D 0.03) passes all 7 bars on 5 of 10 grown models (95% CI 19-81%); same seed does not reproduce the arbor (~70% node agreement) | headline_h/i, repro_g |
| Capacity follows the number of strong pairs (G >= 4.125 nS = 4.2 synapses at 0.98 nS): 4+4 <= 1, 4+2 2-4 per model; higher Pyr D buys more but breaks the p band 0.1-0.3 | capacity_d, recall_e |
| Recall in the threshold regime is clean: full cue completes, 3-cell cue silent, no runaway at background c <= 1.5 nS (NMDA r 0 and 0.56, any GABA level); runaway at c = 3.0 | headline_i, nmda_gaba_exp A (partial) |
| Overlap is clean only up to 1 shared cell (k <= 2 gives 39-43% full cross-completion) | ripple_overlap_j |
| Weight design cannot create capacity: primary lp_weights medians 1.5/2/2 six-cell memories vs R3 counts; bottleneck is grown connectivity (hubs) | lp_weights |
| 10^7-10^9 x more strong K(4,2) sets than an ER graph of the same density; ER and value-shuffled graphs: ~0 candidates; degree-preserving rewiring keeps 50-100%; hub caps cost 50-86% | math_run Part 4/2 |
| No clear biologically plausible >= 3x gain from distributed cues; c = 8 meets the preregistered letter (median 6 vs 2) but depends on the silence rule (0 if one missing cue cell must stay silent, 17.5 if 50% missing may complete) | math_run Part 1 + post hoc |
| NES STDP: AMPA only, potentiation-only (Shift -4 ms), fixed parameters, weights in [0,1]; repeated recall strengthens exactly the programmed cue->non-cue pairs and breaks 3-cell silence (after 10 recalls 15/28 complete from 3 cells) | stdp_k |
| GABA acts but late (interneurons fire ~5-9 ms after the cue vs memory at ~4.5 ms); late GABA discards a second cue only at 5-10 ms and only for some pairs (r = 0, c = 0, x1: 5/12 and 2/12), x2 and x5 more; no theta-scale spacing (W <= 10 ms) | gaba_check_l, gaba_vm, nmda_gaba_exp C (partial) |
| NMDA on (r = 0.56, build ratio) changes nothing at c <= 1.5 (full complete 10/10, 3-cell silent 40/40, 2-cell 0/60); at c = 3.0 it makes runaway in every full-cue event unless GABA >= x2; r = 1.0 (achieved ratio only 0.5-0.75, capped by grown NMDA peak) completes exactly 2 of 4 three-cell cues of every memory, probably a history artifact (adaptive-threshold floor, check pending) | nmda_gaba_exp tables.txt + DEVIATIONS 2, 6 |
| API can now set GABA/NMDA/AMPA per pair (patched build, branch `nes-receptor-strength`, 29/29 connectome checks; 628/628 identical spikes vs file route) | gaba_nmda_api/PATCH.md |
| Growth levers: per-type dm.weight works but moves geometry not length; per-cell steering works (own-group share 0.51 vs 0.24 chance); any extra parameter line reshuffles the axon stream; weight-0 random thinning reproduces baseline bars and recall | randal_reply_n README |

### 1.2 Stuck
1. **Strong-pair supply.** 2% of all pairs (5-11% of existing pairs) have >= 4.125 nS; K(4,2)/K(4,4) sets are concentrated on 11-22 target cells (85-99% on the top 10).
2. **The 7 bars are a noisy conjunction** (50% pass; failures are near-bound wanders), interneuron side (Int->Pyr per pair 4-9, A fraction) still needs luck; seed-to-seed spread equals the pass window.
3. **Inhibition's role**: GABA arrives after the memory has fired; Randal says that is acceptable (pacing/anti-reverberation), but nothing yet gives theta-scale pacing.
4. **Reproducibility**: arbors not regenerable (Randal is investigating the RNG).
5. **Memory design is hand-programmed** (R3 rule); STDP destroys its selectivity (stdp_k); the project goal says "structures ... to implement the desired behavior".

### 1.3 Assumptions never questioned (each with how cheaply it can be questioned)
| # | assumption | status | cheapest question |
|---|---|---|---|
| A1 | One CA3 patch of 96 pyramidal + 20 interneurons, no dentate/mossy/perforant input, one region | never varied (pyramidal 16-128 limit; radius 100-200 um, thickness 20-50) | section 3, D8, D9; needs a 2-region NetMorph config (cost: growth) |
| A2 | **The design rule is the memory**: hand-programmed pair conductances (R3: 4 cue cells x 4.125 nS; 3-cell silence) rather than a learned or grown state | only tested as "STDP strengthens what was programmed" (stdp_k); never "learn from the grown state" | D2 (offline first) |
| A3 | Recall must be from a 4-cell cue and a 3-cell cue must stay **silent** (25% missing). Randal and the biology (Guzman, Neunuebel & Knierim) say partial cues should **complete** | opposite of the rule used for every count; math_run post hoc: 17.5 vs 0 memories depending on it | ask Randal; D2 |
| A4 | The 16.5 nS firing requirement is a property of the model neuron (INFERRED from the build defaults: Cm 100 pF, Vrest -70, Vth -50, Rm 100 MOhm, tau_m 10 ms; `NetmorphManagerThread.cpp:594-600`), never calibrated to CA3 | not in bio_ranges.json; editable per neuron through `Neuron/LIFC/Edit` | D5/D6 |
| A5 | 0.98 nS per synapse, identical for all synapses (build constant: 49 receptors x 20 pS) | never varied; Randal's own LIFtest uses 7 "supersynapses" per pair (6.86 nS cap); the code has an unimplemented TODO to derive receptor count from PSD area (`NetmorphManagerThread.cpp` ~448-452) | D7 |
| A6 | Hubs/low in-degree at the edge come from the **small slab**. The data says otherwise: in-degree falls with distance from the slab centre (rho ~ -0.5, correlation only) **and** every axon collapses into a ball at the disc centre (median radius 36 um) regardless of soma position, dendrites reach 600 um. Likely cause (code reading, untested): `cell_attraction` with every cell as attractor, 1/d^2, unit-normalised. So hubs are probably a steering artifact, not (only) a finite-size edge effect. And math_run found hubs **help** capacity | untested; larger radius (<= 200 um) is allowed but would not obviously change the collapse | D10 |
| A7 | One pass of growth with fixed parameters for all cells of a type; no cell-to-cell parameter variability | bio data show strong cell-to-cell variation in CA3 passive/firing properties (Hemond et al., snippet, UNVERIFIED details) and skewed firing rates (Mizuseki & Buzsaki 2013, VERIFIED in bio_scout) | D5, D11 |
| A8 | Cue cells are driven by forced spikes with 0.5 ms spacing (equivalent to an unnamed strong external input) | a DG/EC-like input was never modelled | D8 |
| A9 | The soft flag "<= 10% active" (mine) and the 4-8-cell memory sizes; CA3 activity is ~18% (8-23%) in Arc studies (secondary) => 17 +/- 8 active cells out of 96 | assembly size c was only varied in math_run | D2 |
| A10 | NMDA and GABA are minor (Randal: "NMDA not very relevant except during learning") | tested at c <= 1.5: yes for recall; **not tested during learning** | D2 |
| A11 | Pair-level weights are the right design variable | can zero a whole pair, cannot move synapses between pairs | D1 (uses weight 0 on purpose) |
| A12 | Pyramidal/interneuron counts, 70-80% pyramidal fraction, density 10-50k/mm^3 as warnings only | E4 has 83% pyramidal | not a capacity lever |

### 1.4 What Randal said that we have not used (paraphrased from the thread; not re-sent)
- (12 Nov) Natural arborization overrides Netmorph's built-in 2008 culture statistics; more room within what is natural than coded; consider more interneurons; if growth does not give the result, look for **other naturalistic reasons** (synapses, conductances, ion channels forgotten).
- (13 Nov) NMDA matters mostly during learning; GABA should have max conductance + weight 0-1 (now done in the patched build).
- (22 Nov) "Dense" is not a problem per se because weak synapses can be **weight 0**; each cell type can have its own growth parameters (not only dm.weight) if within measured in-vivo statistics (cite sources); feel free to branch NetMorphCMake and share; STDP often omitted for interneurons but "some STDP occurs", feel free to experiment; ripples without pacing occur in CA3 recall; **lateral GABA enforces regular spacing in theta**; need **homeostasis for learned memories**; recent work on retrieval and re-encoding; (reply 2) **heteroassociative connections** between successive patterns formed by repeated presentation could drive ripple retrieval.
- Not on his list but implied: mossy fibre / other circuit structure (A1/A8).

## 2. New offline numbers produced for this scout
All on the 10 grown E4 Pyr->Pyr graphs unless stated; threshold model; `lp_weights` packers; medians over models or per-seed values.

**A. Threshold requirement T (`tsweep.py`).** T scaled with pair rule T/4, theta = 0.75 T, hub cap 49.5 nS fixed, w >= 0.1. Six-cell memories, 3 restarts.
| T (nS) | strong-pair share of all pairs | cue sets (median) | disjoint (k=0) median [range] | overlap <= 2 median [range] |
|---|---|---|---|---|
| 16.5 (current) | 2.1% | 1.1e3 | 1 [0-2] | 1 [0-4] |
| 13 (-21%) | 3.7% | 2.4e4 | 2 [1-3] | 4.5 [2-7] |
| 10 (-39%) | 6.8% | 3.3e5 | 3.5 [2-5] | 12.5 [5-20] |
| 8 (-52%) | 6.8% (quantized) | 3.3e5 | 4 [2-5] | 15 [6-24] |
Reading: capacity is steeply sensitive to T, so any intrinsic-parameter change matters. **But direction matters (INFERRED, back-of-envelope): for a brief volley T scales ~ Cm x (Vth - Vrest) / (kernel area x driving force).** Literature snippets this session: CA1 cell capacitance 147/171 pF (dorsal/ventral, Sci Rep srep38242, snippet), ventral CA3 has greater capacitance than dorsal (PMC7717164), CA3 input resistance 135 +/- 8 MOhm and tau_0 66 +/- 4 ms in one study (source paper not identified; UNVERIFIED attribution). Our model has Cm 100 pF and tau_m 10 ms. So calibration to real cells would **raise** T for a synchronous volley (Cm up) and **help** dispersed, asynchronous input (tau_m up). Net effect unknown; do not tune T downward as a trick.

**B. Random-pattern feasibility with saturated weights (`feas_random.py`).** Pattern = c random cue cells + n random target cells; feasible if every target gets sum of U = min(G, 6.86) from the c cue cells >= T ("full"); "anyk" = the k weakest cue contributions already sum >= T (partial-cue completion). 400k random patterns per model, mean over 10 models.
| pattern | T 16.5: full | T 16.5: anyk | T 10: full |
|---|---|---|---|
| 4 cue + 2 targets (k=4) | 2.2e-4 | 2.2e-4 | 2.0e-3 |
| 4 + 4 | 0 | 0 | 4.8e-6 |
| 8 + 2 (any 4 of 8) | 4.4e-3 | 1.1e-5 | 1.8e-2 |
| 12 + 2 (any 6 of 12) | 1.6e-2 | 8.6e-5 | 4.3e-2 |
| 17 + 2 (any 9 of 17) | 3.5e-2 | 4.8e-4 | 7.6e-2 |
Reading: if weights saturate with presentation (what NES STDP does), **only about 1 in 4,500 random 4+2 patterns could be stored**; large assemblies (17 + 2, i.e. ~20% of cells) are storable 1 time in 30. Partial-cue completion (any 9 of 17) is still rare (5e-4). This is a property of the graph, independent of how the weights are set.

**C. Strongest-pair pruning (`prune_p29.py`, `prune_r3.py`).** Higher-D growths already in randal_reply_n (B1 = Pyr D 0.035, B2 = 0.05; seeds 33333, 44444); weakest pairs set to weight 0 until p = 0.29 (ties random), then counted. R3 convention = `R3EQ` (cue pairs >= 4.125, outsiders < 16.4, no input cap), 5 restarts, six-cell (4+2) and eight-cell (4+4) memories, disjoint.
| graph | p | synapses per connected pair | pairs >= 5 syn | strong pairs (>= 4.125 nS) | disjoint 4+2 | disjoint 4+4 | in-degree CV |
|---|---|---|---|---|---|---|---|
| s33333 baseline E4 | 0.28 | 1.98 | 7% | 181 | 1 | 0 | 1.04 |
| s33333 B1 unpruned | 0.391 | 2.93 | 19% | 678 | 3 | 1 | 0.89 |
| **s33333 B1 pruned to p 0.29** | 0.29 | **3.61** | 26% | 678 | 3 | 1 | 1.10 |
| s33333 B2 pruned to p 0.29 | 0.29 | 5.05 (fails bar 2, <= 4.5) | 39% | 1043 | 5 | 2 | 1.19 |
| s44444 baseline E4 | 0.278 | 2.07 | 8% | 198 | 2 | 0 | 1.08 |
| s44444 B1 unpruned | 0.384 | 2.94 | 18% | 617 | 2 | 1 | 0.95 |
| **s44444 B1 pruned to p 0.29** | 0.29 | **3.57** | 23% | 617 | 2 | 1 | 1.13 |
Reading: pruning keeps all strong pairs (x3.1-3.7 vs baseline), meets the p and per-pair bars at B1, and the disjoint counts rise x3 (s33333) and x1 (s44444) for 4+2 and 0 -> 1 for 4+4. Under the stricter primary packer (input cap, silence rule) counts are 1-3 vs 0-1 (noisy). The B2 variant fails bar 2. Flags I would raise: the share of pairs with >= 5 synapses is 23-26% (my own soft flag is 20%; published CA3 contacts 1-2 per connection, 1.85-4.5 for pairs elsewhere), and 26% of grown pairs become weight 0 ("silent"). Overlap k <= 2 counts (42-74) are not usable because of cross-completion (ripple_overlap_j). Bars 4-7 after pruning were **not** re-checked (Pyr->Pyr synapse total falls by ~9% (s33333); A fraction rises).

**D. Heavy-tailed per-synapse strengths (`lognorm.py`).** n = round(G/0.98) synapses per pair, each lognormal with mean 0.98 nS; primary packer; one draw per (model, sigma).
| sigma_ln | strong pairs (median) | disjoint (median [range]) | overlap <= 2 (median) | largest single synapse (median / max, nS) |
|---|---|---|---|---|
| 0 (now) | 190 | 1 [0-2] | 1 | 0.98 |
| 0.5 | 267 | 2 [1-3] | 3 | 6.2 / 9.4 |
| 0.9 | 335 | 2 [1-4] | 4.5 | 19.5 / 35.7 |
| 1.3 | 354 | 2.5 [1-3] | 3.5 | 46 / 105 |
Reading: x1.4-1.8 strong pairs, disjoint counts x2, but the tails produce single synapses of 6-100 nS, far above the pair cap (6.86 nS) and any single-synapse value I know (none sourced); with a sourced per-synapse cap the gain would be smaller. The lognormal sigma is **not** sourced (Song et al. 2005 is in my earlier notes for EPSP amplitudes; not re-verified here).

**E. Chains (`chains.py`; inconclusive).** Cue sets with >= 4 common targets: 2 (baseline s33333), 294k (B1 s33333), 0 (baseline s44444), 177k (B1 s44444). A chain needs a target 4-set that is itself a cue set: 1 edge (B1 s33333), 16 edges (B1 s44444). The search is incomplete (targets truncated to 24, DFS from 300 start sets), so: no chain of two or more 4-cell groups found; **no evidence for or against** longer chains with other group sizes.

## 3. New directions (11)
Each: idea | why it could work | bio plausibility and limits | cheapest first experiment | cost | risk | references.

**D1. Keep the strongest pairs, zero the weakest, in a higher-D growth ("weight-0 sparsification to the bar").**
- Idea: grow at Pyr D 0.035 (B1), then set the weakest Pyr->Pyr pairs to weight 0 until p = 0.29; keep Pyr->Int and interneuron pairs as grown.
- Why: strong pairs are kept (x3.1-3.7), bars 1-2 pass (section 2C); Randal explicitly allows weight 0 for weak synapses (22 Nov); `randal_reply_n` already showed that un-thinned high D recalls cleanly and random thinning (rule R) reproduces baseline stats, i.e. the missing piece was only "which pairs to drop".
- Bio / limits: D 0.035 < 1.5 hard limit; p inside 0.1-0.3; per-pair mean inside 1.9-4.5 (3.6); flags: 23-26% of pairs >= 5 synapses (soft flag), selecting by synapse count is "selection for capacity", silent pairs 26%. No bio_ranges violation. Plausibility of "silent" connections: Randal's statement; also the CA3 estimate of 5-15% recurrent connectivity (a 2010 PLoS Comput Biol snippet, authors not seen, UNVERIFIED) is close to p = 0.29 only after pruning.
- First experiment: offline on the two existing B1 dumps: recompute bars 1-7 after pruning (bars 4-7 pending), then pack and run the standard recall (c 0, 0.15, 1.5; GABA x1; NMDA r 0 and 0.56) against random-pair pruning at the same p as the control (to show the selection, not the pruning, matters).
- Cost: offline 1 h; recall sims ~30 s each, ~100 sims; regrow B1 on 3 more seeds if wanted (25 min each, 2 at a time).
- Risk: gain only x1-3 in disjoint memories (4+2: 1 -> 3 and 2 -> 2; 4+4: 0 -> 1), so it may not reach the "x3 at comparable bio statistics" bar; reviewers may read the pruning as tuning.
- References: none new; Randal email 22 Nov.

**D2. Learned assemblies at biological sparsity, with script-level homeostasis (replace hand programming).**
- Idea: stop programming R3 pairs; start from the grown (uniform 0.2) state, present assemblies of c = 10-17 cells (+ targets) with staggered cue spikes while STDP is on, between epochs renormalise each cell's summed AMPA input (homeostasis done by script through the patched API), then test recall by partial cues with STDP off.
- Why: (i) section 2B says saturated weights can store random assemblies only when large (c = 17: 3.5%), matching the ~18% CA3 activity (secondary); (ii) stdp_k showed repeated recall strengthens exactly co-active pairs; (iii) Randal asked for homeostasis, partial-cue completion, and notes NMDA matters in learning; (iv) completion from partial cues then comes for free (stdp_k: 3-cell silence breaks), matching biology instead of fighting it (A3).
- Bio / limits: weights within [0,1] of the grown peak (no new pairs), no growth/bio_ranges changes; STDP parameters are fixed (potentiation-only), so depression/homeostasis exist only as my script, which must be labelled non-NES. Active fraction 10-20%.
- First experiment (offline, one day): saturating-Hebbian storage of M random assemblies (c = 10-17, n = 2-4) on the 10 grown graphs; recall from k-of-c cues and cross-talk with the threshold model; capacity curve vs c and vs T. Then 1 sim stage: learn 3 assemblies on s33333 from the grown state, STDP off, test.
- Cost: offline cheap; sims ~28 s each, ~600 sims = ~5 h at one sim at a time.
- Risk: potentiation-only STDP saturates everything that co-fires (hubs, runaway); no inhibitory plasticity (Vogels-style) to rebalance; section 2B says most random assemblies are not storable at all, so "learning" may reduce to selecting those that fit.
- References: Zenke, Agnes, Gerstner 2015, Nat Commun 6:6922 (VERIFIED; abstract: Hebbian + heterosynaptic + homeostasis + consolidation needed to form/retrieve assemblies; any one missing breaks it); Litwin-Kumar & Doiron 2014, Nat Commun 5:5319 (VERIFIED; symmetric Hebbian STDP + homeostasis, spontaneous reactivation); Vogels et al. 2011, Science 334:1569-1573 (VERIFIED; inhibitory plasticity balances E/I, memories reactivatable); Stdp_k and Guzman 2016 (earlier).

**D3. Heteroassociative sequences / synfire-like chains (Randal's second reply).**
- Idea: successive groups A -> B -> C linked by strong pairs; recall of a sequence from the first group.
- Why: Randal says heteroassociative connections form between successively presented patterns; chain links need no silence rule.
- Bio: Lisman 1999 (recall of memory sequences by reciprocal dentate-CA3 interactions) puts the heteroassociation in the dentate synapses, not CA3 itself (secondary description). Synfire propagation needs pools large enough (Diesmann et al. 1999).
- First experiment: complete the offline chain search (section 2E was incomplete) with groups of 4-6 and a relaxed link rule (>= T from a fired group, no silence rule), on B1 graphs; if no chain of length >= 3 exists, drop.
- Cost: offline hours. Risk: high, likely few chains because each link needs the same scarce strong pairs; SPECULATION that a relaxed rule helps.
- References: Lisman 1999, Neuron 22:233-242 (VERIFIED, PubMed id 10069330, from a secondary description); Diesmann, Gewaltig, Aertsen 1999, Nature 402:529-533 (VERIFIED).

**D4. Growth-programmed assemblies: per-cell steering of pyramidal axons toward group dendrites ("memory by morphology").**
- Idea: use the per-cell attractor/attractedto syntax that already worked for interneurons (own-group share 0.51 vs chance 0.24) for pyramidal groups of 6 cells, so a group's axons target its own members' dendrites.
- Why: E4 has ~53 outgoing Pyr->Pyr synapses per cell (0.28 x 95 x 1.98, derived). If half go to 5 group partners that is ~5 per pair, i.e. strong pairs without changing p or the total synapse count (arithmetic, SPECULATION about how steering distributes them). Directly "config-space programming" of the memory, which is the project goal; Randal: per-group steering is part of the answer; bio support for preconfigured assemblies (Mizuseki & Buzsaki 2013, VERIFIED in bio_scout).
- Bio / limits: dm.weight inside 0.1-1.0; D_synmax unchanged; all bars to be rechecked; side effect seen before: Int->Int -60% (not relevant for pyramidal groups, unknown for Pyr).
- First experiment: two growths (s33333, s44444), 8 groups of 6 cells, steering on Pyr only, W 1.0; measure own-group synapse share, strong pairs inside groups, bars 1-7, then programme nothing extra and test recall with the group's own pairs (weights = grown, saturated).
- Cost: 2-4 growths x 25 min (2 at a time) + offline analysis + ~50 sims.
- Risk: any parameter line reshuffles the axon stream, so n = 2 is descriptive; unit-normalised attraction may not concentrate synapses (only direction is steered); programmed groups reduce between-group connectivity (does not fix pair strength outside the groups); "growth-coded memory" is not what a learned memory is (A2).
- References: Randal's thread; randal_reply_n A3/A5; Mizuseki & Buzsaki 2013 Cell Rep 4:1010-1021 (VERIFIED, bio_scout).

**D5. Excitability heterogeneity and allocation (per-neuron SpikeThreshold, memory cells slightly more excitable).**
- Idea: lower the spike threshold of the cells of a chosen assembly by a few mV (API `Neuron/LIFC/Edit`, per neuron), as in allocation experiments where more excitable cells are recruited to the engram.
- Why: section 2A: T -21% gives x2 disjoint and x4.5 overlap-2; a 3 mV lower threshold is ~15% lower T (INFERRED from 20 mV Vth - Vrest). Skewed, heterogeneous excitability is a measured feature.
- Bio / limits: threshold is not in bio_ranges.json (no limit stated); need a sourced range for CA3 threshold spread; stay within a few mV of the mean; excitability is transient in vivo (hours) and learning-dependent.
- First experiment: offline: T per target cell (0.85 T for allocated cells), recount; then 10-sim check of recall with the edit through the API.
- Cost: low. Risk: moderate gain, partly an assumption that allocated cells are in the right place (the pairs still have to exist: D2/D4); non-allocated cells' silence rule becomes harder.
- References: Yiu et al. 2014, Neuron 83(3):722-735, doi 10.1016/j.neuron.2014.07.017 (VERIFIED; relative excitability immediately before training biases recruitment); Rashid et al. 2016, "Competition between engrams influences fear memory formation and recall" (VERIFIED title/topic; venue not in the results, Science is my recollection: UNVERIFIED); Mizuseki & Buzsaki 2013 (VERIFIED).

**D6. Calibrate the neuron to CA3 before concluding anything (A4).**
- Idea: replace Cm, Rm, Vth, Vrest, refractory, AHP/ADP defaults by CA3 pyramidal values, with citations, and recompute T and the strong-pair threshold.
- Why: capacity is steeply sensitive to T (2A); the defaults are generic. Honest expectation: Cm up (CA1 147-171 pF vs our 100 pF) raises T and **lowers** capacity; tau_m up (CA3 135 MOhm, 66 ms in one study vs 10 ms) helps asynchronous inputs and distributed cues, which the 0.5 ms-spaced cue test does not exercise.
- Bio / limits: this is the point of the exercise; but nothing in bio_ranges.json.
- First experiment: literature table (needs VERIFIED CA3 numbers for Cm, Rm, tau_m, Vth: my searches this session did not give a citable Cm for CA3), then offline T estimate with a leaky-integrator calculation of the volley (not yet written), then the 4-memory recall check.
- Cost: literature + 1 day. Risk: negative result (capacity down); worth knowing because it changes which direction D5/D2 should push.
- References: Spruston & Johnston 1992 (perforated-patch CA3 estimates, named in a result, JNP; UNVERIFIED details); Hemond et al. (CA3b passive properties vary cell to cell, snippet; year/venue UNVERIFIED); PMC7717164 (dorsal/ventral CA3, snippet; authors not seen).

**D7. Heavy-tailed per-synapse strengths from morphology (structure -> function).**
- Idea: instead of 0.98 nS everywhere, assign receptor counts per synapse from a lognormal (PSD area), preserving the mean; implement through per-record `PeakConductance_nS` edits (file route) or the unimplemented receptor-quantity TODO.
- Why: section 2D: x1.4-1.8 strong pairs and x2 disjoint counts for sigma 0.5-0.9, because a few strong synapses make strong pairs.
- Bio / limits: lognormal weight distributions are a general finding, but the tails here give 6-100 nS single synapses, above the pair cap; needs a sourced per-synapse cap; hard/soft flags to state.
- First experiment: offline with a capped lognormal (cap = 3 x mean, sourced), recount; no sim.
- Cost: low. Risk: gain disappears with a sourced cap; model-file hack (not API).
- References: Song et al. 2005 (earlier notes; not re-verified here); `NetmorphManagerThread.cpp` TODO.

**D8. DG-like / mossy-fibre detonator region and an EC-like direct input (circuit structure we never used).**
- Idea: a second NetMorph region of sparse "granule-like" cells whose few strong synapses detonate CA3 cells, and a separate direct (perforant-like) cue pathway; pattern separation upstream chooses *which* CA3 assembly a stimulus activates (picking assemblies that fit, cf. 2B).
- Why: Treves & Rolls 1992 argue for two distinct input systems (strong non-modifiable synapses to drive the pattern, mossy fibres carrying the information to be stored); detonators drive CA3 cells singly (Henze et al. 2002; Vyleta et al. 2016, bio_scout); reduces the need for cue cells to carry all the conductance.
- Bio / limits: the 128-cell pyramidal limit might or might not count a second region (ask Randal); per-synapse conductance is a build constant (0.98 nS), a detonator needs a large one (file route/patch); adds a growth-config dimension.
- First experiment: none cheap. Smallest step: ask Randal whether a second region is allowed; offline, replace the 4 forced cue cells by "detonator" cells with fixed 1-synapse strong inputs and count the effect on T per cell (the cue then needs fewer recurrent pairs).
- Cost: high (new growth config, new receptor strengths). Risk: high; SPECULATION on mapping.
- References: Treves & Rolls 1992, Hippocampus 2(2):189-199 (VERIFIED); Henze, Wittner, Buzsaki 2002; Vyleta, Borges-Merjane, Jonas 2016; Marr 1971; McNaughton & Morris 1987 (all in bio_scout, VERIFIED there).

**D9. Theta-paced inhibition and time multiplexing (Randal: lateral GABA enforces spacing).**
- Idea: add a theta-rate (4-8 Hz) rhythmic drive to the interneurons (forced spikes through `SetSpecificAPTimes`, a stand-in for septal drive) so that memories are retrieved in windows, and GABA decay (10 ms; PV 1-3 ms in the literature) sets within-cycle spacing.
- Why: nmda_gaba_exp shows lateral GABA alone gives only a 5-10 ms discard window and no ~100 ms spacing; Randal expects the spacing from theta mode; time multiplexing is the biological way to hold several assemblies in one network.
- Bio / limits: adds an external input not in the grown model; not a capacity lever for stored memories, a **functional requirement** from Randal.
- First experiment: with the patched build, periodic interneuron spike trains at 8 Hz on one E4 model (c = 0.15, GABA x1/x2), two memories cued at random phases; measure the fraction of cues that complete vs phase. 20-30 sims.
- Cost: low. Risk: it is an input I choose, so it proves little about the grown network; SPECULATION on how it should be labelled.
- References: bio_scout (Lawrence & McBain 2003 feed-forward inhibition, VERIFIED there); a theta/gamma reference is still missing from my list (UNVERIFIED need).

**D10. Treat hubs as a feature and test the steering-collapse hypothesis (instead of "larger slab").**
- Idea: (a) test whether the collapse to the centre comes from attractor settings by growing with a lower pyramidal-axon dm.weight (0.3-0.6; per-type syntax works) and measuring in-degree CV and strong pairs; (b) if hubs help (math_run Part 2), grow them deliberately via cell-to-cell variation (D11) rather than removing them.
- Why: A6; math_run shows ER and value-shuffled graphs have ~0 candidates, hub caps cost 50-86%, so removing hubs would cost capacity; interneuron W 0.3 already spreads the axon ball (p99 radius 113 vs 66 um) but lowered Int->Pyr per pair to 2.5-3.6.
- Bio / limits: dm.weight 0.1-1.0; slab radius 100-200 um allows up to 24-39k cells/mm^3 at 148 cells (inside the warning band).
- First experiment: two growths with pyramidal-axon W 0.6 (s33333, s44444), in-degree CV, strong pairs, bars.
- Cost: 2 growths. Risk: predicted to **lower** capacity (hub loss) and Pyr->Pyr per pair; this is a realism check, not a gain. Boundary-effect literature (spatial random graphs have lower degree near boundaries; surrogate-network corrections exist; Coon, Dettmann, Georgiou, arXiv 1110.4929, VERIFIED as a result; EPL 100:28002 (2012), VERIFIED snippet) supports testing for an edge effect with a periodic-boundary or surrogate comparison, but NetMorph has no periodic boundary I could find (randal_reply_n C).

**D11. Cell-to-cell parameter variability and growth-parameter optimisation against statistics.**
- Idea: draw dendrite/axon growth parameters per cell from a measured spread (instead of one value per type), and optimise the growth/D/interneuron-count/dm.weight parameters against the 7 bars plus the strong-pair count, using the cheap surrogates we already validated (threshold at stored distance reproduces a D re-run within ~2%; weight-0 thinning).
- Why: the bars are a noisy conjunction (50% pass), per-seed failures are near-bound wanders (headline_i), so an optimiser that targets *margins* (not just pass) could raise the pass rate; variability creates hubs and strong pairs naturally; real CA3 cells vary (Hemond et al., UNVERIFIED).
- Bio / limits: all parameters stay inside bio_ranges and Randal's "natural" statistics (cite in-vivo sources, as he asks).
- First experiment: offline Bayesian/CMA search over (Pyr D <= 1.5, Int D <= 0.15, #interneurons 16-128, dm.weight 0.1-1.0) with the thresholding surrogate (free) and a pair-level pruning rule from D1 as a decision variable; only the final candidate is grown (3 seeds).
- Cost: moderate (a week of offline work, ~3 growths). Risk: seed noise is as wide as the pass window; same seed is not the same arbor, so one growth cannot confirm a margin.
- References: linefix_c/headline_h notes (surrogate within ~2%), Randal thread.

## 4. Ranked shortlist with experiment plans

**Rank 1: D1 strongest-pair sparsification (finish and verify).** Why first: nearly free, evidence is already on disk, and it follows directly from Randal's "set weak synapses to weight 0".
- Plan: (1) offline: bars 1-7 on B1 pruned for s33333/s44444 and on three new B1 growths (grow B1 on s55555, s66666, s77777 as 3 jobs, 25 min each); (2) controls: random pair pruning to the same p, and the unpruned B1; (3) pack 4+2 and 4+4 disjoint memories with R3EQ and primary; (4) recall sims on the patched instance (c 0, 0.15, 1.5; GABA x1; NMDA r 0 and 0.56; full / 3-cell / 2-cell cues, one second-cue test), about 150 sims at one at a time (~1.5 h); (5) report share of pairs >= 5 synapses and silent-pair fraction against the soft flags.
- Success: bars 1-7 pass on >= 3 of 5 B1 models after pruning; disjoint 4+2 count >= 3 x same-seed baseline in >= 3 of 5 models (currently 3x and 1x on two); recall clean; no hard flag. Failure: counts <= 2 x baseline; then stop and report.
- Cost ~4 h elapsed. Risk: low gain (x1-3); interpretation risk (selection).

**Rank 2: D2 learned assemblies at biological sparsity with script-level homeostasis.** Why: addresses assumption A2 and Randal's partial-cue/homeostasis points; stdp_k already showed the machinery acts on exactly the right pairs.
- Plan: (1) offline Willshaw-style capacity curve of saturated storage for assembly size c = 4, 8, 12, 17 (+ targets) on the 10 graphs: completion from any k-of-c cues and cross-talk; (2) simulate one stage on s33333: learn 3 feasible assemblies from the grown uniform state with STDP on (staggered presentation, 20 repetitions), homeostatic renormalisation between epochs by `BatchSetPrePostStrength(..., 'AMPA')`, test with STDP off (full, k-of-c, outsiders, two-assembly cross-talk, NMDA r 0/0.56, GABA x1); (3) only if completion and selectivity hold, scale to 5 models.
- Success: >= 3 assemblies learned without programming, partial cues (>= k of c) complete, outsider spikes 0, weights inside [0,1] and conductance <= grown peak, homeostasis keeps Sum input <= the same cap as before. Failure: everything saturates (runaway) or only the pre-selected feasible assemblies work (then it is allocation, report as such).
- Cost: offline 1 day + ~100-600 sims. Risk: moderate-high.

**Rank 3: D4 growth-programmed assemblies by per-cell pyramidal steering.** Why: the project's own definition of success is config-space programming; the lever already works for interneurons; one cheap growth pair tests it.
- Plan: (1) 2 growths (s33333, s44444), 8 groups x 6 cells with per-cell attractors/attractedto on pyramidal axons (W 1.0), region-level `In.*` lines removed as in randal_reply_n; (2) measure own-group share, synapses per within-group pair, strong pairs, bars 1-7; (3) if within-group pairs reach >= 5 synapses, set the grown (saturated) weights only and test recall of the groups as memories (cue 4 of 6), c 0 and 0.15, GABA x1.
- Success: within-group pairs >= 5 synapses for >= 50% of group pairs with bars 1-7 passing; failure: share < 0.35 or bars fail. Cost: 4 growths worth of time (~1 h with 2 at a time) + ~50 sims. Risk: moderate; n = 2 is descriptive only.

Not recommended now: D5/D6 before the literature table (direction unknown), D7 until a per-synapse cap is sourced, D8 until Randal answers about a second region, D3 (no chains found), D10 as a capacity lever (predicted negative), D9 (functional requirement, do after the capacity question).

## 5. Questions that would change the plan (not sent)
1. Should a partial cue (3 of 4, or 4 of 8) **complete** or stay silent? (A3; changes every capacity number.)
2. Is a weight-0 "silent" pair counted as "no connection" for the p band, and is selecting the strongest 29% of pairs acceptable? (D1)
3. May we calibrate Cm, Rm, Vth to CA3 and does he have a source? (D6)
4. Does a second region (DG-like) count toward the 128-cell pyramidal limit? (D8)
5. Can STDP parameters/homeostasis be exposed, and may interneuron STDP be enabled? (D2)

## 6. Honest limits
- All new numbers are threshold-model feasibility with greedy packers (lower bounds), 3-5 restarts, n = 10 models (A, B, D) or n = 2 (C); nothing was simulated; nothing preregistered.
- The T-sweep keeps the hub cap fixed at 49.5 nS and the silence rule at 75% of T; other choices move the counts (math_run post hoc showed the silence rule can swing results from 0 to 17).
- The relation "T proportional to Cm x (Vth - Vrest)" is back-of-envelope and untested.
- The 2% / 5-11% strong-pair numbers are of all pairs vs existing pairs respectively (not the same denominator).
- `nmda_gaba_exp` is only partly finished (192 of 263 runs): B (overlap) not run, C partial, F not run; its P0, P1, P5, P9 pass and P2, P3, P4, P6, P8, P10, P11 fail as preregistered (tables.txt); r = 1.0 is capped and history-affected (DEVIATIONS 2, 6).
- The Gmail thread was read from a saved JSON (all 26 messages scanned; Randal's replies read, mine only by length).
- Searches: 14 queries, snippets only (no full papers read). CA3 capacitance in pF was **not** found.

## 7. References
VERIFIED (title/venue/year in a search result this session; content = abstract/snippet only):
- Zenke F, Agnes EJ, Gerstner W (2015) Diverse synaptic plasticity mechanisms orchestrated to form and retrieve memories in spiking neural networks. Nat Commun 6:6922.
- Litwin-Kumar A, Doiron B (2014) Formation and maintenance of neuronal assemblies through synaptic plasticity. Nat Commun 5:5319, doi 10.1038/ncomms6319.
- Vogels TP, Sprekeler H, Zenke F, Clopath C, Gerstner W (2011) Inhibitory plasticity balances excitation and inhibition in sensory pathways and memory networks. Science 334:1569-1573, doi 10.1126/science.1211095.
- Treves A, Rolls ET (1992) Computational constraints suggest the need for two distinct input systems to the hippocampal CA3 network. Hippocampus 2(2):189-199, doi 10.1002/hipo.450020209.
- Lisman JE (1999) Relating hippocampal circuitry to function: recall of memory sequences by reciprocal dentate-CA3 interactions. Neuron 22:233-242 (secondary description only).
- Yiu AP et al. (2014) Neurons are recruited to a memory trace based on relative neuronal excitability immediately before training. Neuron 83(3):722-735, doi 10.1016/j.neuron.2014.07.017 (author list beyond the first not seen, Josselyn listed late).
- Brunel N (2016) Is cortical connectivity optimized for storing information? Nat Neurosci 19(5):749-755, doi 10.1038/nn.4286 (abstract only; not used for numbers).
- Diesmann M, Gewaltig M-O, Aertsen A (1999) Stable propagation of synchronous spiking in cortical neural networks. Nature 402:529-533.
- Coon J, Dettmann CP, Georgiou O: connectivity of random geometric graphs dominated by local geometry, corners (arXiv 1110.4929; Phys Rev E per the snippet; year not seen).
- Heitzig-type surrogate networks for boundary effects in spatially embedded networks, EPL 100:28002 (2012) (title/authors not seen).
- Earlier-session references re-used (VERIFIED then, see bio_scout/math_scout): Mizuseki & Buzsaki 2013; Henze, Wittner, Buzsaki 2002; Vyleta, Borges-Merjane, Jonas 2016; Guzman et al. 2016; Neunuebel & Knierim 2014; Marr 1971; McNaughton & Morris 1987; Song et al. 2005; Lawrence & McBain 2003.
UNVERIFIED: Rashid et al. 2016 "Competition between engrams ..." (journal not in the results); Hemond et al. (CA3b passive properties and firing classes; year/venue not seen); Spruston & Johnston 1992 (JNP, perforated-patch CA3; named in a result); CA3 input resistance 135 +/- 8 MOhm, tau_0 66 +/- 4 ms (a snippet quoting "one study"); CA1 capacitance 147/171 pF (Sci Rep srep38242, snippet) and ventral > dorsal CA3 capacitance (PMC7717164, snippet); a 2010 PLoS Comput Biol paper quoting 5-15% CA3 recurrent connectivity (authors not seen); "~18% CA3 active" (bio_scout, secondary).
