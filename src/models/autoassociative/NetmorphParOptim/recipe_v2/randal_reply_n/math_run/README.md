# math_run: SCOUT2 items 4, 2, 1 and the offline part of 3 (2026-11-23, autonomous run)

Offline only: no NES sims, no emails, no pushes, main NES/API untouched, nothing in the sim slots. `PREREGISTRATION.md` (written before any run, unedited) holds the numbers, thresholds and predictions; `DEVIATIONS.md` has one entry (D1, before any run). All capacity numbers are **feasibility in the NES-like threshold model** (`lp_weights/lpw_lib.py`, `ripple_overlap_j/ovlib.py`), under the same constraints as `lp_weights` (grown pairs only; Dale; weight 0.1-1.0; per-pair cap 6.86 nS; per-cell input cap 49.5 nS with the hub rule; T = 16.5 nS, unintended input <= 12.375 nS). Counts are greedy lower bounds (5 restarts here against 10 in `lp_weights`, so the "grown" row here is slightly lower than the `lp_weights` baseline; ratios inside one table use the same settings).

## 0. Short answer
1. **No robust, biologically plausible 3x capacity gain.** One cell of the design space reaches the preregistered letter of the rule: **distributed cues with 8 cue cells + 2 targets, overlap <= 2, primary variant: median 6 memories (3-8) against a baseline of 2 (3.0x; 10 of 10 models at or above 2; 6 of 10 models at 6 or more; no hard flag).** I do not count it as the clear gain John asked for because: (a) it does not hold at k = 0 (median 2 against the 5 needed; the cell budget alone limits disjoint 10-cell memories to 9); (b) it needs a cue that completes from 75% of its cells; with the silence rule tightened to "a cue lacking one of 8 cells must not complete" nothing fits at all (post-hoc table in section 3); (c) its designed pairs have a median of 4.0 synapses (mean 4.3; 18% have 5 or more), above the 1-2 contacts reported for CA3-CA3 connections (Guzman 2016, snippet), though inside the 1.85-4.5 per-pair range of L2/3 data; (d) memories are 10 cells instead of 6, so the counts are not like for like; (e) it is the threshold model only. Per the instruction I then **started the biology round** (`bio_scout/BIO_SCOUT.md`).
2. **Capacity-vs-in-degree baseline (part 4):** the grown E4 graphs hold 10^7-10^9 times more strong K(4,2) cue sets than an Erdos-Renyi graph with the same strong-pair density would (expected count 0.00003-0.006 against 1,182-284,463 observed). All capacity comes from structure that a random graph lacks.
3. **Degree-controlled nulls (part 2):** capacity needs the heterogeneity. ER and value-shuffled graphs have zero candidate cue sets in 10 of 10 models; the degree-preserving configuration model keeps 50-100% of the grown count (Hinf, k <= 1); hub-capping at an in-degree of about 40 removes 50-86% of it. **Hubs help; removing them hurts.** Only 11-22 of the 96 cells receive any strong pair (85-99% of all strong pairs land on the 10 most-driven cells), and in-degree falls with distance from the slab centre (Spearman about -0.5), which suggests a finite-slab edge effect (post-hoc, section 2).
4. **Pruning recount (part 3):** capping synapses per pair at 8 or 5 does nothing to capacity (pairs needed are 4.125-4.9 nS); capping in-degree cuts it to 14-50% (Hinf, k <= 1) and the primary-variant counts stay at 1-2. **NES/API cannot delete or zero an individual synapse** (code read, section 4); a whole pair can be set to any conductance including 0.

## 1. Part 4: capacity versus in-degree baseline (`part4.json`)
| quantity (10 models) | range |
|---|---|
| connection probability p / mean in-degree C | 0.236-0.350 / 22.4-33.2 |
| median in-degree | 10-27 (bimodal; many cells with about 10 inputs) |
| in-degree CV (grown; binomial of the same density would be 0.14-0.18) | 0.81-1.20 |
| strong pairs (G >= 4.125 nS) / share of all 9,120 ordered pairs r | 130-260 / 0.0143-0.0285 |
| expected strong K(4,2) cue sets under ER, E = C(96,4) C(92,2) r^8 (my arithmetic) | 0.00003-0.0061 |
| observed candidate cue sets (hubs allowed) | 1,182-284,463 |
| ratio observed / expected | 9.0e6 - 5.9e8 |
| N cells at the same r for E >= 10 | 324-813 |
| reference 2C/pi (Derrida-Gardner-Zippelius, lecture-note snippet, UNVERIFIED) | 14.3-21.1 |
| packer counts, six-cell k <= 3: primary / Hinf | 1-5 / 13-160 |
Reading: the primary packer counts are below 2C/pi in 10 of 10 models; the Hinf counts exceed it in 9 of 10, so the reference is not an upper bound for this rule (a different capacity definition: the reference counts random dense patterns, our candidates are structured bicliques on hub cells). Under a random graph the rule needs about 300-800 cells to give even 10 candidate memories; the pyramidal count is hard-limited to 16-128 by `bio_ranges.json`, so scale cannot be bought inside the stated limits.

## 2. Part 2: degree-controlled null graphs and hub capping (`results_nulls.md`, `nulls_*.json`)
Median over 10 models (min-max) of the number of six-cell memories, best of 5 restarts (random types: median over 3 rewires).
| graph | in-degree CV | k = 0 (primary) | k <= 1 (primary) | k <= 3 (primary) | k <= 1 (Hinf) | k <= 3 (Hinf) | candidates (Hinf, median) | Hinf k <= 1 as fraction of grown |
|---|---|---|---|---|---|---|---|---|
| grown | 1.02 | 1 (1-3) | 1 (1-3) | 1 (1-5) | 7 (4-9) | 66 (13-140) | 30,876 | 1 |
| ER | 0.16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CM (degree-preserving) | 1.02 | 1 (0-2) | 1 (0-2) | 1 (0-3) | 4.5 (2-6) | 36.5 (2-125) | 7,840 | 0.50-1.0 (median 0.70) |
| VS (values shuffled) | 1.02 | 0 (0-1) | 0 (0-2) | 0 (0-2) | 0 (0-2) | 0 (0-2) | 0 | 0-0.25 |
| CAPr (in-degree cap about 40, random removal) | 0.83 | 1 (1-2) | 2 (1-2) | 2 (1-4) | 2 (1-3) | 4.5 (2-7) | 52 | 0.14-0.50 |
| CAPs (cap, weakest removed) | 0.83 | 2 (1-3) | 2 (2-5) | 3.5 (2-6) | 7 (4-9) | 46.5 (14-72) | 7,222 | 0.67-1.25 |
- **ER and VS have (almost) no candidates**: ER has zero candidate cue sets in 10 of 10 models and 3 of 3 rewires; VS has a median of 0 candidates and 0-2 memories: random placement of the strong pairs cannot produce a K(4,2).
- **CM keeps most of the capacity**: preserving in- and out-degree, with each edge keeping its conductance, retains 50-100% (median 70%). The structure that supports memories is therefore the degree heterogeneity and the link between a source cell and its strong outputs, not the exact pair wiring.
- **CAPr removes most of it** (14-50%); **CAPs, which keeps the strongest in-edges, loses little** (67-125%). The strong pairs are what matter, and they sit on the high-in-degree cells.
- Post-hoc concentration check (`strong_concentration.json`): strong pairs (>= 4.125 nS) come from many sources (54-92 of 96 cells) but go to only 11-22 target cells; 85-99% of them land on the 10 most-driven cells. Post-hoc position check (`indeg_vs_position.json`): in-degree decreases with the distance from the centre of the slab (Spearman -0.46 to -0.61; strong in-degree -0.25 to -0.54; slab 222-235 x 221-235 x 29-30 um), i.e. the hubs are mostly the central cells of a small slab. That is an inference from a correlation in 10 networks; it was not tested by growing a larger slab.
- Question answered: **hubs help.** They are where the strong pairs sit; a capped or randomised graph supports fewer or no memories under this rule. That does not make them biological (section 7).

## 3. Part 1: distributed-cue assemblies (`results_dist.md`, `dist_*.json`, `results_posthoc.md`)
Memory = c cue cells + 2 targets; recall conditions in the threshold model: the full cue gives every target >= 16.5 nS; any sub-cue lacking 25% of the cue cells gives every other member <= 12.375 nS; the whole memory gives every outside cell <= 12.375 nS; overlap <= k shared members; constraints as in lp_weights (weights are the minimal waterfill solution, D1). Median (min-max) over 10 models:
| c | variant | k = 0 | k <= 2 | cell budget bound (96/(c+2)) | models reaching the success rule |
|---|---|---|---|---|---|
| 8 | primary | 2 (1-3) | **6 (3-8)** | 9 | k=2: 6/10 at >= 6 (median 6) |
| 8 | Hinf | 3 (2-3) | 9 (5-10) | 9 | |
| 12 | primary | 2 (0-2) | 5 (0-6) | 6 | k=2: 4/10 |
| 17 | primary | 0 | 0 | 5 | no candidates: the 75% rule needs the 4 weakest of 17 pairs to sum to >= 4.125 nS (more than a single synapse each can give) |
| 20 | primary | 1 (0-2) | 2 (0-3) | 4 | 0/10 (cell budget 4 at k=0) |
Biological statistics of the primary designs (all 10 models pooled, pairs counted over designed cue->target pairs):
| c | synapses per designed pair (median [mean]) | share of designed pairs with >= 5 synapses | share single-synapse | weight median [min-max] | share w >= 0.9 | max pair conductance | max non-hub cell input | active fraction |
|---|---|---|---|---|---|---|---|---|
| 8 | 4.0 [4.3] | 0.18-0.19 | 0.00 | 0.53 [0.18-0.70] | 0 | 2.06 nS | 47.6-49.0 nS (cap 49.5) | 10.4% |
| 12 | 3.0-3.5 [3.3-3.5] | 0.09-0.10 | 0.00 | 0.41-0.47 [0.11-0.70] | 0 | 1.38 nS | 46.7 nS | 14.6% |
| 20 | 1.2-2.0 [2.0] | 0.03 | 0.45-0.48 | 0.42-0.74 [0.11-0.84] | 0 | 0.83 nS | 46.4 nS | 22.9% |
Independent check (`verify_dist`): bounds, weight range, no added pair, Dale, per-cell cap all OK for every stored design; cascade model at 16.5 and at 15.0 nS: every full cue completes exactly its memory (100% in every (c, k) group of `results_dist.md`) and every sub-cue (the q strongest contributors per target plus 30 random q-subsets) stays silent.
Bio comparison and flags: no hard flag. Soft notes: c = 8 uses pairs with a median of 4 synapses (the baseline uses pairs with 5 or more for every cue pair, so this is less extreme but still above the 1-2 contacts of CA3-CA3 pairs in Guzman 2016 and in Watson 2025 as far as the snippets go); c = 20 needs 23% of the cells active. **Correction of my own soft flag (made in the preregistration as an assumption):** the biology round found Arc-based estimates of 18% (context) and 8-23% (dorsal/ventral) of CA3 cells active in an environment (secondary snippets; `bio_scout/BIO_SCOUT.md`), so 10-23% is not out of range; I leave the flag count unchanged in the scoring.
**Post-hoc sensitivity (not preregistered; `results_posthoc.md`, 10 restarts, primary):** the result depends strongly on how selective a cue must be. Rule "a cue lacking 50% of its cells must not complete": c = 8, k <= 2: 17.5 memories (12-21), k = 0: 4 (4-5). The preregistered 25%: 6 (3-8) and 2.5 (2-3). Rule "a cue lacking 12.5% (one of 8) must not complete": **0 memories in all 10 models for c = 8, 12 and 20.** So the gain is bought with cue selectivity, the classical capacity/robustness trade-off, and the preregistered 25% rule is the same fraction as the baseline's "3 of 4 must not fire".

## 4. Part 3: touch-pruning recount and the API question
Graph types (same packer, `results_nulls.md`): CAPr / CAPs (in-degree cap about 40: removed edges become w = 0, flagged), SYN8 / SYN5 (pair conductance capped at 7.84 / 4.9 nS = 8 / 5 synapses), CAPr+SYN5.
- SYN8 and SYN5 change nothing in the Hinf counts (1.0 of grown in 10/10 models) because the pairs the rule needs are 4.125-4.9 nS; in the primary variant the counts stay at 1-1.5. Synapses per pair after capping: mean 2.04 -> 2.00 (SYN8), 1.89 (SYN5); maximum 17.9 -> 8 / 5.
- CAPr and CAPr+SYN5: 14-50% of grown (Hinf k <= 1, 10/10 models at or below 50%); primary counts 2 (k <= 1) and 2 (k <= 3), no gain. CAPs: 67-125% of grown.
- Biology of the pruned graphs: in-degree CV 0.83 (against 0.14-0.18 for a binomial graph of the same density, still heavy-tailed), synapses per pair 1.7-2.2 (inside the published 1.85-4.5), single-synapse share 50-62%.
**API (code read, not run):** `Simulation/SetPrePostStrength` and `BatchSetPrePostStrength` (`SimulationRPCInterface.cpp:73-75, 595-660`) set a conductance for a PAIR: `LIFCNeuron.cpp:543-559` sets `weight = conductance / g_peak_sum_nS` on the first AMPA receptor-data entry from that pre cell and zeros the rest. In the abstracted LIFC mode the individual receptors of one pre/post pair are merged into a single receptor-data object (`Neuron.cpp:77-79`: `AddToAbstractedFunctional` adds the peak conductances and averages the weights), so **there is no handle for an individual synapse, and the route list contains no route that removes or zeroes a synapse or a connection.** Whole pairs can be removed only by setting their conductance to 0 (a pruned pair = w 0, outside the 0.1-1.0 reading, allowed in Randal's 22 Nov email); within a pair the number of effective synapses can be reduced by setting the pair conductance to k x 0.98 nS (w = k / n, which must stay >= 0.1 to respect the stated limit).

## 5. Decision against the preregistered rule
Rule (PREREGISTRATION section 2): in the primary variant, median over models >= 3x baseline (k = 0: >= 5; overlap: >= 6), at least 8 of 10 models at or above the baseline, no hard flag; Hinf never counts.
| method | result | rule met? |
|---|---|---|
| ER / CM / VS / CAPr / CAPs / SYN8 / SYN5 / CAPr+SYN5 (parts 2, 3) | primary medians 0-3.5 for all families | no |
| distributed cue c = 8, k = 0 | 2 | no |
| distributed cue c = 8, k <= 2 | 6 (3-8); 10/10 models >= 2; no hard flag | **yes, by the letter (median exactly 6; 6 of 10 models reach 6)** |
| distributed cue c = 12, 17, 20 | 5 (k=2), 0, 2 | no |
Caveats that keep this from being a clear win are in section 0. Because the rule's second half asks for a gain "at comparable bio statistics", I treat the result as **borderline / not established** and ran the biology round (done next, `bio_scout/BIO_SCOUT.md`). I did not relax any constraint to obtain it.

## 6. Preregistration scoring (18 sub-claims: 14 HIT, 4 MISS)
| id | prediction | observed | score |
|---|---|---|---|
| P4.1 | observed candidates >= 1,000x ER expectation in >= 8/10 | 10/10 (min 9.0e6) | HIT |
| P4.2 | N for E_ER >= 10 in 300-1,500 in >= 8/10 | 324-813 in 10/10 | HIT |
| P4.3 | packer counts below 2C/pi in 10/10 (primary and Hinf) | primary 10/10; Hinf k <= 3 exceeds it in 9/10 | MISS |
| P2.1 | ER has zero candidates in >= 9/10 | 10/10 | HIT |
| P2.2 | CM Hinf k <= 1 <= 25% of grown in >= 8/10 | 0/10 (50-100% of grown) | MISS |
| P2.3 | VS <= 25% in >= 8/10 | 10/10 | HIT |
| P2.4a | CAPr <= 50% in >= 8/10 | 10/10 | HIT |
| P2.4b | CAPs >= 50% in >= 6/10 | 10/10 | HIT |
| P2.5 | no null or capped graph meets the rule | none | HIT |
| P1.1 | primary c = 8, 12 k = 0 median <= 3 | 2, 2 | HIT |
| P1.2 | c = 17, 20 k = 0 median <= 4 | 0, 1 | HIT |
| P1.3 | Hinf >= 3x primary for some c | at most 1.5x (c = 8, k = 2: 9 vs 6) | MISS |
| P1.4 | independent check finds no violation | none | HIT |
| P1.5 | no c meets the rule | c = 8, k <= 2 meets the letter | MISS |
| P3.1 | CAPr and CAPr+SYN5 <= 50% in >= 8/10 | 10/10 both | HIT |
| P3.2a | SYN8 within 20% of grown in >= 8/10 | 10/10 | HIT |
| P3.2b | SYN5 within 20% in >= 6/10 | 10/10 | HIT |
| P3.3 | no pruned variant meets the rule | none | HIT |
My expectation that CM would lose most of the capacity was wrong (the link between sources, strong pairs and high-in-degree targets survives degree-preserving swaps); my expectation that no distributed design would reach the rule was wrong by one cell of the grid.

## 7. Flags: what looks non-biological, and what does not
- **Hub cells and heavy-tailed in-degree** (CV 0.8-1.2; median in-degree 10-27 against mean 22-33; 12-26 cells above in-degree 54) are the substrate of every memory found here. A finite-slab edge effect is the likeliest cause (central cells have more neighbours; correlation about -0.5). Real CA3 has about 12,000 recurrent inputs per cell (Treves & Rolls 1992, snippet) and no slab edges. Nothing in this run makes the hub structure more biological; capping it removes the capacity.
- **Strong pairs** (>= 5 synapses) are 5% of grown pairs and concentrated on 11-22 target cells; published CA3-CA3 connections have 1-2 contacts (Guzman 2016).
- **Weights**: the distributed designs keep weights in [0.11, 0.84], none at the upper bound, 98-99% of the other pairs at the lower bound 0.1 as in `lp_weights` (point mass at the floor, not lognormal).
- **Pruned graphs** with CAPr/CAPs need w = 0 on 25% of the pairs (flagged; Randal's email allows it).
- Constraints never relaxed to obtain a result; the Hinf variant is shown for comparison only and is flagged non-biological wherever a cell exceeds the cap.

## 8. Limits
- Threshold model only (no timing, GABA, NMDA, adaptation, noise); the model matched the earlier overlap sims at 94-96% (`lp_weights/README.md` section 6).
- Counts are greedy lower bounds with 5 restarts; ratios use identical settings; absolute grown counts differ slightly from `lp_weights` (10 restarts).
- The 75% silence rule, the cap H = 3T, T = 16.5, theta = 12.375 and the 6.86 nS cap are my choices or Randal's example values; the post-hoc table shows how much the first one matters.
- The edge-effect explanation is a correlation, not a test. The null graphs reuse the grown G values; they do not represent how a differently grown network would look.
- The in-degree cap of about 40 is a statistic of a random graph of the same density, not a measured CA3 value.

## Files
`PREREGISTRATION.md`, `DEVIATIONS.md`, `mrlib.py`, `run_part4.py` -> `part4.json`, `run_nulls.py` -> `nulls_*.json`/`.log`, `agg_nulls.py` -> `results_nulls.md`, `run_dist.py` -> `dist_*.json`, `agg_dist.py` -> `results_dist.md`, `posthoc_dist.py` -> `posthoc_*.json`, `results_posthoc.md`, `strong_concentration.json`, `indeg_vs_position.json`. The biology round is in `../bio_scout/BIO_SCOUT.md`.
