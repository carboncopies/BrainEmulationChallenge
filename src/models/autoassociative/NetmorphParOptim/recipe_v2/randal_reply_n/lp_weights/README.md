# lp_weights: offline weight design on the 10 E4 networks (2026-11-22/23)

Candidate 1 of `math_scout/SCOUT.md`. Offline only: no simulation, no NES/API call, no git, no email. `PREREGISTRATION.md` was written before any solve and is unedited; `DEVIATIONS.md` has two entries (D1 written before any solve; D2 written when the first solver attempt stopped on an input-cap conflict). Every result below is **feasibility in the NES-like threshold model of `ripple_overlap_j/ovlib.py` (a cell fires when the summed programmed conductance of fired cells reaches T = 16.5 nS)**, not recall in NES.

## 0. Short answer
1. **The constraints were enforced inside the solver** (variable bounds and linear constraints; `lpw_lib.py`), and an independent re-check of all 386 stored designs found no violation (section 5). Existing pairs only, Dale (x >= 0), weight in [0.1, 1.0], per-pair cap 6.86 nS, homeostatic input cap, objective = smallest then most uniform weights.
2. **Per-pair weights are settable through the API** (read from code, section 1): `Simulation/BatchSetPrePostStrength` sets one conductance per (pre, post) AMPA pair; GABA pairs are not settable; the API itself does not enforce 0.1-1.0.
3. **The LP does not raise single-memory capacity** (it cannot: an algebraic identity, section 3). The preregistered claims "LP finds more memories than R3" MISSED.
4. **Biological constraints decide the outcome.** With my homeostatic cap (total input per cell <= 3 x 16.5 = 49.5 nS) and every grown pair kept at weight >= 0.1, the capacity collapses to a median of 1.5 disjoint and 2 overlapping (k <= 3) six-cell memories and zero eight-cell memories. The reason is structural: the cells that can host memories are the few high-input cells (4-13 candidate target cells per network, median as-grown input 186-335 nS against 10-33 nS for the median cell) plus 0-2 extreme hub cells (up to 1,021 nS) that cannot take any memory input under the cap (section 4). Without the cap the LP-feasible count is about the R3 "fit" count (median 71 at overlap <= 3), but those solutions put 112-291 nS on single cells, i.e. they are non-biological by the cap I chose.
5. **The weights are legal but not "biological-looking"**: 99.4-99.5% of all pairs (primary; 95.3-99.4% in the other variants) sit at the lower bound 0.1, the 0.5-1% raised pairs all sit at one value (4.125 nS, weight 0.2-0.84), so the distribution is a spike at the floor plus a narrow cluster, not lognormal. The memory pairs must be the 5% of grown pairs that have at least 5 synapses (55% of grown pairs have exactly one).
6. **Where the LP does help** (threshold model, to be confirmed by sims): removing the non-cue loops that R3 programmed (and respecting a margin) makes overlapping-memory sets that the sims showed cross-completing (F2/F3) come out clean in the model (section 6).

## 1. API: are per-pair weights settable? (code read, not run)
Files in `/home/johnjose/BrainGenix/BrainGenix-NES/Source/Core/Simulator/`:
- `RPC/SimulationRPCInterface.cpp:73-75, 595-660`: routes `Simulation/SetPrePostStrength` (PreSyn, PostSyn, Conductance_nS) and `Simulation/BatchSetPrePostStrength` (vectors), `SetAllStrength`.
- `Structs/Simulation.cpp:1358-1392`: forwards to the post-synaptic neuron; the batch version stops at the first pair that returns false.
- `LIFCompartmental/LIFCNeuron.cpp:543-559`: the FIRST AMPA receptor entry from that pre cell gets `weight = NewConductance_nS / g_peak_sum_nS`; all other entries from that pre cell (NMDA, further AMPA) are set to weight 0; returns false if no AMPA entry exists.
Consequences: yes, per PAIR (all synapses of a pair share one weight); only AMPA pairs (Pyr->Pyr, Pyr->Int) are settable, so inhibition stays as grown; programming a pair removes its NMDA; no clamp to 0.1-1.0 or to any maximum exists in this code, so the limits are ours to enforce; the weight formula can exceed 1 if a conductance above g_peak_sum is passed. The earlier recipe (`recipe/recipelib.py` docstring) uses exactly this call and reads the weights back.

## 2. Constraints, as enforced (see PREREGISTRATION.md for the text)
| # | constraint | how enforced | source of the number |
|---|---|---|---|
| 1 | only existing grown pairs | variables exist only where as-grown G_ij > 0 | the viz dump `g_peak_sum` |
| 2 | Dale's law | all variables are excitatory outputs with x >= 0; GABA pairs are not variables | API (GABA not settable) |
| 3 | w_ij in [0.1, 1.0] | variable bounds x in [0.1 G, min(G, 6.86)] | bio_ranges.json `dm.weight` 0.1-1.0 read as a per-pair weight range (it holds no per-synapse conductance limits) |
| 4 | per-pair cap | x <= 6.86 nS and x <= G (n synapses x 0.98 nS) | Randal's `autoassociative_connectome.py:75-79` (27.44 nS / 4) and `LIFtest.py:444` (7 supersynapses x 0.98 nS); literature check in nS UNVERIFIED (search found only 0.56 mV unitary CA3-CA3 EPSPs from 1-2 contacts, Guzman 2016, snippet) |
| 5 | input cap per cell | sum_i x_ij <= H_j = max(3T = 49.5 nS, 0.1 sum_i G_ij) | **my choice**, not sourced; sensitivity 2T, 5T and none; hub cells (D2) |
| 6 | smallest, most uniform | stage A min sum w, stage B min max w within 2% | task |
Threshold-model constraints per memory (4 cue cells C, m non-cue cells N, members M): (i) sum_C x >= 16.5 for each n in N; (ii) any 3 of the cue cells give <= theta to every other member (theta = 12.375 nS: the margin R3 itself has for a 3-cell cue); (iii) the whole memory gives <= theta to every cell outside M. Overlaps allowed up to k shared cells.
Variants: `primary` (above); `hubs_waived` (constraint 5 waived for hub cells; NON-COMPLIANT, shown because R3's counts used those cells); `H2T`, `H5T`, `Hinf` (cap 33, 82.5 nS, none; `Hinf` is a post-hoc variant); `theta14` (margin 14.0 nS); `Hinf_theta14` (post-hoc); `w0` (weights may go to 0, outside the stated limit); `r3equiv` (post-hoc: R3 pair rule each cue pair >= 4.125 nS, outsiders only need to stay below 16.5 nS, hubs waived = the closest thing to the R3 programming).

## 3. Algebraic identity (D1)
(i) sum of four cue pairs >= 16.5 and (ii) any three <= 12.375 force every cue pair >= 4.125 nS: exactly the R3 rule. So for one memory the candidate set equals the R3 candidate set and the smallest solution is x = 4.125 nS on each cue pair (weight 4.125 / G, interior of [0.1, 1], weights 0.20-0.84, median 0.70). I wrote predictions P1/P2/P5 without this and now score them as written.

## 4. Results
### 4.1 Capacity (largest packing found: lower bounds; greedy, 10 restarts for the main variants, 3 for the others)
Median over 10 networks (min-max). R3 = counts from `ripple_overlap_j/README.md` section 1 on the same graphs (k = 0 is the earlier disjoint count). Full per-model tables: `results_tables.md`.
| variant | 6-cell k=0 | k<=1 | k<=2 | k<=3 | 8-cell k=0 | 8-cell k<=3 |
|---|---|---|---|---|---|---|
| **R3 (fit counts; sims: only k<=1 clean)** | 3 (2-4) | 6 (4-8) | 16.5 (7-29) | 70.5 (16-201) | 1 (0-1) | 1 (0-5) |
| **primary (all constraints)** | **1.5 (1-3)** | **2 (1-3)** | **2 (1-4)** | **2 (1-5)** | **0 (0-0)** | **0 (0-0)** |
| H2T (cap 33 nS) | 0 | 0 | 0 | 0 | 0 | 0 |
| H5T (cap 82.5 nS) | 2 (1-3) | 4 (2-6) | 6.5 (3-10) | 7.5 (4-12) | 0.5 (0-1) | 0.5 (0-2) |
| Hinf (no cap, post-hoc) | 2 (2-3) | 7.5 (4-9) | 17.5 (7-24) | 71 (13-160) | 1 (0-1) | 1 (0-4) |
| hubs_waived | 2 (1-3) | 3.5 (1-6) | 4 (1-12) | 5.5 (1-105) | 0 (0-1) | 0 (0-1) |
| theta14 | 3 (1-4) | 4.5 (1-8) | 6.5 (1-11) | 6.5 (2-11) | 1.5 (1-2) | 2 (1-4) |
| Hinf_theta14 (post-hoc) | 3 (2-4) | 14 (10-18) | 39 (30-50) | 185 (89-231) | 1 (1-2) | 9 (4-13) |
| w0 (weights may reach 0) | 2 (1-3) | 5 (4-7) | 5 (3-9) | 7.5 (5-14) | 1 (0-1) | 1 (0-3) |
| r3equiv (post-hoc) | 2 (1-3) | 3.5 (1-6) | 4 (1-15) | 5.5 (1-113) | 0 (0-1) | 0 (0-1) |
No 4+6 memory exists in any network (0 candidates, `extra_*.json`). Eight-cell candidates are few (0-1,387 cue sets per network at margin 12.375; up to 6,736 at margin 14.0).
R3 memories filtered through the LP constraints (`filt_*.json`; kept / R3 size summed over models): primary 8/21 (k=0), 5/56, 6/173, 6/910; w0 21/21, 46/56, 44/173, 57/910. Why the primary variant rejects R3 memories (1,179 in total): 850 target a hub cell (72%), 304 break the input cap (26%), 25 kept, none fail the closure rule.
**What limits capacity.** In every network a handful of cells carry all the candidate memories: with no input cap the 39,275-565,000 candidate memories use only 4-13 distinct target cells (median 9), and those cells have median as-grown input 186-335 nS against 10-33 nS for the median cell. Memories are essentially built on the hub cells. The input cap (a cell may be driven by at most about three times its firing threshold) allows at most 2 memories (2 x 16.5 nS) per target cell once the baseline (0.1 x as-grown inputs) is paid, so capacity = (usable target cells) x about 2 / (cells per memory). With the cap removed capacity matches R3's fit count.

### 4.2 Weight distributions and fit to biology
- Primary / hubs_waived solutions (all variants in `results_tables.md`): 99.4-99.5% (primary), 98.2-99.4% (hubs_waived) and 95.3-99.3% (Hinf) of the variable pairs sit at the lower bound w = 0.1; 11-39 pairs per network are raised; all of them at x = 4.125 nS exactly (weights 0.2-0.84, median 0.70, none above 0.9, none on the 6.86 nS cap). So the distribution is a **point mass at the floor plus a narrow cluster**; skew of log x among raised pairs = 0. It is sparse, but **not** lognormal. Median x over all pairs is 0.098 nS against 0.98 nS as grown; the total recurrent conductance of a solved network is 456-663 nS against 4,075-5,863 nS as grown (11%); only 5-21% of the total conductance is in raised pairs.
- Per-synapse view: a designed pair has at least 5 synapses (4.125 / 0.98 = 4.2 -> 5) and weight 0.2-0.84, i.e. 0.2-0.8 nS per synapse, below the NES default 0.98 nS. The unusual part is the synapse count, not the strength: only 2.3-7.6% (mean 4.9%) of the grown pairs have at least 5 synapses; 54.7% have exactly one; the median is 1. Published unitary CA3-CA3 connections are 1-2 contacts (Guzman et al. 2016, snippet; UNVERIFIED in full), so the memory pairs are drawn from the top tail of the grown synapse-count distribution. FLAGGED.
- `theta14` solutions (margin 14.0): 66-68% of the designed pairs are at weight >= 0.9, i.e. ON THE UPPER BOUND (the four pairs must reach 16.5 nS with weaker grown pairs). FLAGGED. `r3equiv`: 7-14% of designed pairs on the 6.86 nS cap and 13-18% at w = 1. FLAGGED. Homeostatic cap active (cell within 2% of H): 0.2-2.6% of cells in the capped variants.
- Hub cells (constraint 3 against 5, D2): 7 of the 10 networks have 1-2 cells whose as-grown input is above 495 nS (in-degree up to 95 of 95; up to 1,021 nS), which a weight of 0.1 cannot bring below 49.5 nS. In the uncapped variants some cells receive 112-291 nS (7-18 times the firing threshold). The weight design cannot fix these; they come from the growth (pyramidal dendrite 27.9k um, 1.8-3x the Ishizuka CA3 values, `CA3_MORPH_COMPARE.md`, may be related; not tested).

## 5. Enforcement check (independent of the solver)
`verify.py` re-solved all 386 stored designs and checked: LP feasible 386/386; bounds 386; w in range 386; per-pair cap 386; homeostatic cap 386 (hub-adjusted); no pair added 386; Dale (x >= 0) 386. Cascade threshold model, threshold 16.5: the full cue completes exactly its memory in 4,246/4,246 and no 3-cell cue completes anything in 16,984/16,984. At threshold 15.0 (the effective NES threshold suggested by the validation below): all designs with margin theta <= 14 pass (primary 73/73 and 292/292; hubs_waived, theta14, w0, H5T, Hinf, Hinf_theta14 all pass), the post-hoc `r3equiv` (no margin) fails for 252 of its 1,148 3-cell cues and 8 of 287 full cues.

## 6. Threshold model versus the existing sims (step E) and a mechanism check
R3-programmed designs of `ripple_overlap_j` (c = 0, GABA on), cascade model, threshold 16.5 / 15.0:
| family | full-cue events | sim clean | model clean (16.5 / 15.0) | agreement (16.5 / 15.0) | model clean but sim not (16.5 / 15.0) | model not clean but sim clean |
|---|---|---|---|---|---|---|
| F1 | 56 | 56 | 56 / 56 | 56 / 56 | 0 / 0 | 0 / 0 |
| F2 | 167 | 102 | 121 / 96 | 148 / 161 | 19 / 0 | 0 / 6 |
| F3 | 232 | 132 | 158 / 120 | 206 / 218 | 26 / 1 | 0 / 13 |
| F8 | 10 | 10 | 10 / 10 | 10 / 10 | 0 / 0 | 0 / 0 |
The model never flags an event that was clean in the sims at 16.5, and agrees on 96.4% (F2) and 94.0% (F3) at 15.0 (post-hoc comparison; the preregistered threshold is 16.5). So the effective threshold in NES is about 15 nS, as the earlier note said (~15 nS), and the margin theta = 12.375 leaves about 2.6 nS.
Mechanism check (post-hoc, `noloops.py`): removing the R3 non-cue->non-cue loops from the same programming makes 146 of 167 (F2) and 196 of 232 (F3) full-cue events clean at 16.5 (sims: 102, 132; model with loops: 121, 158). So the loops explain much of the cross-completion; the rest comes from cue pairs of other memories on shared targets (the LP's closure constraint removes those by design).

## 7. Preregistration scoring (20 sub-claims: 11 HIT, 9 MISS)
| id | prediction | observed | score |
|---|---|---|---|
| P1a | LP single 4+2 count >= R3 disjoint in 10/10 models | primary k=0 count >= R3 in 2/10 (LP 1-3 vs R3 2-4); `Hinf` 4/10 | MISS |
| P1b | median ratio to R3 1.2-2.5 | about 0.5 (primary), 0.7 (Hinf) | MISS |
| P1c | no 4+6 memory | none (0 candidates) | HIT |
| P2a | disjoint LP count 3-8 per model (median 5) | 1-3 (median 1.5) | MISS |
| P2b | LP count larger than R3 in >= 8/10 | 0/10 | MISS |
| P3a | k<=1: 5-12 (median 8) | 1-3 (median 2); Hinf 4-9 (7.5) | MISS (primary) |
| P3b | k<=3 smaller than R3 in 10/10 | 10/10 (2 vs 16-201) | HIT |
| P3c | k<=3 below 40 in 9/10 | 10/10 | HIT |
| P4a | 8-cell count 0-3 per model | 0 in all | HIT |
| P4b | >= 1 model with >= 2 eight-cell at k<=3 | none | MISS |
| P5a | > 90% of variable pairs at the lower bound | 95.3-99.5% in every variant shown | HIT |
| P5b | >= 50% of raised pairs on the 6.86 nS cap | 0% (primary) | MISS |
| P5c | raised-pair distribution not lognormal (bimodal) | point mass at floor + single value | HIT |
| P6a | cap binds (within 2%) in < 5% of cells, k=0 | 0.2% | HIT |
| P6b | more cells at the cap for k<=3 | 0.3% vs 0.2% | HIT (weak) |
| P7a | model: no cross for >= 90% of F1 | 56/56 | HIT |
| P7b | model flags cross in >= 70% of sim cross events (F2, F3) | 46/65 = 70.8%, 74/100 = 74% | HIT |
| P8a | w = 0 raises capacity < 30% | +33% (k=0) to +275% (k<=3) | MISS |
| P8b | cap 2T lowers capacity > 30% | to 0 | HIT |
| P9 | > half of memories need the 6.86 nS cap | 0% | MISS |
(P5a, P6a/b are almost forced by the objective and the cap.) The preregistered expectation that a convex weight design would gain capacity was wrong; section 3 explains why.

## 8. Limits (read before using the numbers)
- Threshold model only: no timing, no GABA, no NMDA, no adaptation, no noise. A design that is feasible here has not been shown to recall in NES; the sims that would show it were not allowed. The model's own fit to the sims is imperfect (section 6).
- Capacity numbers are greedy lower bounds (the LP in the loop is the final feasibility check, but pair sharing between memories makes the packer conservative).
- The homeostatic cap H = 3T, the margin theta = 12.375, T = 16.5 and the 6.86 nS cap are my choices or Randal's example values, not measured biology; the cap decides the headline (1.5 vs 71 memories). The 0.1-1.0 limit is the dm.weight growth-parameter range reused as a per-pair weight range.
- Post-hoc additions (not preregistered, labelled): variants Hinf, Hinf_theta14, r3equiv, the 15.0 threshold comparison, `noloops.py`, `extra_stats.py`.
- Literature cross-check of the 6.86 nS pair cap in nS: not possible from the searches (no conductance values found).
- The grown networks are what they are: hub cells and heavy-tailed input are a feature of the growth, not of the weight design.

## Files
`PREREGISTRATION.md`, `DEVIATIONS.md`, `lpw_lib.py` (LP, packer, threshold model), `run_capacity.py`, `run_r3eq.py`, `run_hinf.py`, `filter_r3.py`, `verify.py`, `validate_r3.py`, `noloops.py`, `extra_stats.py`, `aggregate.py`; results `cap_*.json`, `capr3_*.json`, `caphinf_*.json`, `filt_*.json`, `verify_*.json`, `validate_r3.json`, `extra_*.json`, `results_tables.md` (all tables). Scratch: `t0.py`, `t1.py`, `t2.py`, `patch*.py`.
