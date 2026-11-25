# fresh_run: #1 strongest-pair pruning (5 models) and #3 steered assemblies (2 growths), 2026-11-23/24
Patched instance only (NES 8011 / API 8010); main NES 3156209 / API 1972355 untouched. No commits, pushes or emails. Preregistration: PREREGISTRATION.md (not edited). Slot rule (<=3 concurrent sims/growths, pgrep gate) kept.

## #1 Pruning to p = 0.29 (B1 = Pyr D 0.035, keep the 2,644 pairs with most synapses)
| seed | baseline K42 | B1P K42 | ratio | unpruned B1 K42 | random-prune Q K42 | bars failed (pruned) | soft flag (pairs>=5 syn) | D42 memories clean (c 0.15 / 1.5) |
|---|---|---|---|---|---|---|---|---|
| 33333 | 3 | 7 | 2.3 | 7 | 6 | none | 25.6% (>20) | 7/7, 7/7 |
| 44444 | 2 | 7 | 3.5 | 7 | 7 | bar 5 (drivable 4) | 23.3% | 7/7, 7/7 |
| 55555 | 2 | 6 | 3.0 | 6 | 5 | bar 3 (Int->Pyr 3.59/pair) | 17.9% | 6/6, 6/6 |
| 66666 | 3 | 7 | 2.3 | 7 | 5 | none | 26.6% | 7/7, 7/7 |
| 77777 | 4 | 8 | 2.0 | 8 | 7 | none | 28.2% | 8/8, 8/8 |
Baseline D42 recall: 3, 2, 2, 3, 4 memories, all clean. 3-cell sub-cues silent and 0 non-member spikes everywhere in D42.
**Preregistered #1 verdict: FAIL (0 of 5 successes; needs 3).** K42 >= 3x baseline on 2 of 5 (44444, 55555), and both of those fail a bar (bar 5 / bar 3, growth-only bars that pruning cannot fix). K42 >= 2x on 5 of 5 (report-only line).
Key facts:
- Pruning does not create capacity. B1P K42 equals unpruned B1 K42 on all 5 seeds because strongest-first pruning keeps every strong pair. The 2-3.5x gain comes from the higher D (0.035). Pruning only fixes bar 1 (unpruned p 0.39-0.49).
- Selection matters: random pruning to the same p gives K42 lower on 5/5 seeds (5-7 vs 6-8) and a lower share of strong pairs (ge5 12-20%).
- Pruning concentrates synapses: soft flag (>= 5-synapse pairs) exceeds 20% on 4 of 5 pruned models. This is a flag, not relaxed.
- Overlapping memories (O1 designs, 17-24 memories vs 4-8 baseline): at c = 0.15 clean 22/24, 18/19, 13/17, 20/21, 21/24 (baseline 6/6, 4/4, 4/4, 6/7, 8/8). At c = 1.5 only 10/24, 14/19, 6/17, 6/21, 11/24 are clean; cross-completion 5-14 per model (baseline 1-6 of 4-8), non-member events 3-10 on 4 models, and 4 three-cell cues not silent on 55555, 4 on 66666. More stored memories means more cross-completion at high background. So the extra capacity is real only for disjoint designs.
- Bars 3-6 are properties of the growth: pruned bars 1-7 all pass on 3 of 5 (33333, 66666, 77777).

## #3 Steering of pyramidal axons to own-group dendrites (arm C1, Pyr D 0.0175)
Per-cell attractors for 48 pyramidal cells in 8 groups of 6 (`NGF_A NGF_G<g>` emitted; attractedto `NGF_G<g>` only), 48 ungrouped cells and all interneurons on `NGF_A`.
| seed | p | spc | A | bars | own-group share (chance .053) | within-group pairs >= 5 syn | strong pairs within groups / all | usable 4+2 groups | K42 whole graph |
|---|---|---|---|---|---|---|---|---|---|
| 33333 | .253 | 2.03 | 47.6% | all 7 pass | 0.306 | 21% | 51 / 182 | 0 of 8 (best 4-5 of 8 cue->target pairs strong) | 2 |
| 44444 | .269 | 1.96 | 47.8% | all 7 pass | 0.273 | 21% | 50 / 167 | 0 of 8 (best 3-4 of 8) | 2 |
**Preregistered #3 verdict: FAIL** (own-group share < 0.35, within-group >= 5-synapse pairs 21% vs 50% needed). Steering works (about 5-6x chance, and about 8x the strong pairs inside groups vs baseline pseudo-groups' 2-6) but is far from enough to make a 4+2 memory (needs all 8 cue->target pairs strong). No recall run because no designed group is usable, K42 is 2 (below baseline 3/2). The C1 graphs are in no worse bar shape than baseline (steering side effect: the extra parameter lines reshuffle the axon stream, so these are not paired with baseline realisations; C1 passes bar 5 on 44444 where baseline failed, that is realisation noise).
Implementation finding (post hoc, c1_metrics_mapped.py): the steered cells (steering indices 0-47) show up as viz ids 48-95 (enrichment is only in viz blocks 8-15 on both seeds; blocks 0-7 are at chance). c1_metrics.py as originally written looked at blocks 0-47 and reported chance values (own share .056/.042) plus a "control" of .306/.273 which is actually the steered set. The mapping is inferred from the data (consistent on both seeds, block-aligned), not verified from NES id tables. The verdict does not depend on it (both readings fail).

## Prediction scoring (HIT = event as predicted)
P1 HIT. P2 HIT. P3 HIT (3 of 5 pass all bars). P4 HIT (5/5 equal). P5: K42 >= 3x on >= 3 of 5 MISS (2 of 5; predicted 15%); median ratio 2.3 within 1.5-3 HIT; >= 2x on >= 3 of 5 HIT. P6: soft flag on all 5 MISS (4 of 5); zeroed fraction 22-28% PARTIAL (it is 26-41% depending on seed; 66666 started at p 0.49). P7 HIT 5/5. P8: D42 clean at both c HIT; O1 cross-completion <= 10% of full cues: c 0.15 PARTIAL (8, 5, 24, 5, 12%), c 1.5 MISS. P9 MISS (0 successes, as the 8% implied). P10: own share >= 0.35 MISS; >= 0.20 HIT; within-group >= 5 syn 50% MISS; bars 1-7 pass on both HIT (predicted 35%); #3 success MISS. P11: p within +-0.05 HIT; usable groups median >= 1 MISS; K42 C1 >= 3x MISS.

## Incidents
- NES/API outage on the patched instance (twice) killed B1 66666 and C1 growths, plus one recall sim; rc=0 from gen_autonm_labels does NOT prove a growth succeeded (check viz/ exists; out-rawcounts.json status failed). Failed dirs in failed_nes_outage/ and failed_nes_outage2/, stale logs in stale/. Reran all to completion. A sim whose soma count was 0 (assertion) was rerun.
- Growths took 24 min each unless the server was down.

## Honest limits
5 models, one realisation each; K42 from sampled packings (lower bounds); recall is 1-seed per cell; O1 results use my overlap <= 1 design; pruned weights are R3 recipe weights mapped to the real pairs (pairs absent from the effective graph = 0); no limits relaxed. Data: fr_results.json, bars_fr.json, dyn_scores.json, c1_metrics*.json, feas_*.json, design_*.json, raw_*.json.
