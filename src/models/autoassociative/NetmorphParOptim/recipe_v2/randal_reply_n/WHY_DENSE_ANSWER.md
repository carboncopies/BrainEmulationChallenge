# Answer to Randal: why is "too dense" a problem if weak synapses can be set to weight 0? (2026-11-22)

Draft text for John; not sent. Numbers from `linefix/README.md`, `headline_h/README.md`, `headline_i/README.md`, `lit_review/LIT_REVIEW.md`.

**Short answer.** Because the number of synapses per connected pair was far above what is measured, and because zeroing weights can reduce the effective count but cannot tell us which synapses are real; the sparse structure we need (who connects to whom, and how strongly) was lost. We reduced the density with D_synmax because it removes the contacts before they exist; zeroing weights afterwards would need a rule for which ones to zero, and that rule is then the model.

**Our numbers (patched build, line 379 fixed, same arbors as before the fix)**
- With the fix and the old limits (Pyr->Pyr D_synmax 1.5), Pyr->Pyr synapses rose x4.9-5.0 to 348,000-421,000 on 96 pyramidal cells (about 3,600-4,400 per pyramidal cell), i.e. about 40 synapses per ordered pyramidal pair averaged over all 9,120 pairs. In published pyramidal pairs the number per *connected* pair is 1.85 (Hellwig, semi-experimental), 2.5-5.6 (van Ooyen 2014 NetMorph results at 4-10 um criteria) and 4.5 +/- 0.5 (Feldmeyer, L4 to L2/3 rat), with connection probability about 0.1-0.3 (van Ooyen 0.301). Note: 40 is an average over all pairs, not over connected pairs, so it is not directly the same quantity as the published numbers; it still implies that nearly every pair was connected.
- With pyramidal D_synmax 0.0175 (E4, 10 grown networks): connection probability 0.236-0.350 (mean 0.284 +/- 0.033) and 1.80-2.35 synapses per connected pair (mean 2.05 +/- 0.18), about 4,000-5,000 Pyr->Pyr synapses per network. That is inside the sourced bands (probability 0.1-0.3, 1.9-4.5 per pair).
- Interneuron pairs went the other way: before the fix Int->Pyr was 1.4-1.6 synapses per pair (biology about 4-9, up to 15; Lee 2014 CA1 mouse 8.7 and 4.0 boutons per pair); after the fix at D 0.1 it was 9.0-14.2, and in E4 (D 0.03) 3.6-5.1 per pair. So "dense" applies to Pyr->Pyr at D 1.5, not to the interneuron pairs.
- Whole-cell totals are not the problem in themselves: 3,600-4,400 Pyr->Pyr synapses per cell is below the 5,000-10,000 per neuron quoted in bio_ranges.json, which counts all inputs. The problem is how they are distributed: about 40 per pair means a nearly fully connected network, not a sparse 10-30% one.

**Why weight 0 does not remove the issue**
1. The quantities we compare with biology are counts and probabilities (how many synapses per pair, what fraction of pairs connect). Zero-weight synapses still count as anatomical synapses; the pair would still look 100% connected in the connectivity matrix that we read back.
2. The weight range allowed is 0.1-1.0 (bio_ranges.json; per Randal, each cell type may use its own dm.weight inside it), so weights cannot be scaled down far enough to turn 40 synapses into 2 without exceeding the range. Setting individual weights to exactly 0 would be a different mechanism (per-synapse pruning). I did not check whether the current API allows it; Randal's reply says it can be done, and we would need to know how.
3. Pruning needs a rule for which synapses to keep. Lowering D_synmax is that rule in the simplest form: keep only contacts closer than D. It is built into NetMorph and is deterministic given the arbors.
4. Recall and capacity depend on the pairwise structure. With near-complete connectivity every cue would drive every memory; memories need the sparse pattern, and our recall tests (headline_h, headline_i) only make sense on sparse networks.
5. Cost: more synapses means more simulation time (the earlier fixed runs took 1.6-1.8x longer than the baseline).

**What I am not claiming**
- I did not run a zero-weight experiment, so I cannot say how a pruned dense network would behave compared with a low-D network.
- The "bio" numbers above come from the literature notes (lit_review) at snippet level; see CA3_MORPH_COMPARE.md for how each was obtained. Hellwig 1.85 and Feldmeyer 4.5 are quoted through van Ooyen et al. 2014.
- Randal's second point (growth direction making axons and dendrites wrap around each other) is a fair possibility. What we checked: the direction of synapse-carrying segments is isotropic after the fix (4.7-4.9% with cos(+x) > 0.9, equal to all segments). What we did not do: look at the morphologies spatially. We have the viz dumps and the NetMorph coordinate files, so a visual check is possible whenever he wants it.
