# randal_reply_n: own interneuron dm.weight + group steering (A), weight-0 thinning (B), morphology check (C) on E4 (2026-11-22/23)
E4 = V1 arbor, 20 interneurons, pyramidal D 0.0175, interneuron D 0.03, line-379-fixed build, patched instance only (NES 8011 / API 8010; started for this task, stopped at the end; main NES 3156209 / API 1972355 untouched; no git, no emails, no merges). PREREGISTRATION.md was written before the first growth and not edited. Seeds 33333 (baseline passes all 7 bars) and 44444 (baseline fails bar 5, drivable 3). 15 growths (about 25 min each, 2 at a time), 32 recall sims. n = 2 seeds per arm: **descriptive, not a pass-rate estimate**; the existing 10-model E4 noise (SD: Int->Pyr/pair 0.49, p 0.033, drivable 2.4, A 2.4 points) applies.
Other files in this folder (`bio_scout/`, `gaba_vm/`, `lp_weights/`, `math_*`, `*.md` notes, `morph_e4.py/json`, `models.json`) were put there by another worker; not mine, not used except `morph_e4.py` (its `load`/`measure` node parser, imported by `analyze_arm.py`/`morph_check.py`) and `models.json` (uuid map of the baseline models).

## Headline
1. **The syntax works and the lever is real, but it moves geometry, not length.** `all_interneuron_axons.axondm.dm_weight` (own set) is accepted. Interneuron axon total length, node count and branch counts are identical to the last digit in every arm (44,763 um / 8,997 nodes per cell on 33333) because length is set by the growth/branching parameters, not by direction. What changes is **where** the axon goes: mean extent (max node distance from soma) 204 / 157 / 138 um for W 0.3 / 0.6 / 1.0 (seed 33333; baseline at 0.9: 140) and 195 / 151 / 129 on 44444 (baseline 132).
2. **Lowering the interneuron weight hurts the E4 bars.** Int->Pyr synapses per pair fall to 2.55 (W 0.3) and 3.42 (W 0.6) on 33333, 2.69 / 3.60 on 44444 (bar 3 needs >= 4), and the inhibitory fraction drops to 37-42% (inside the 25-50 band). W 1.0 gives 4.69 / 5.16 (in range). Interneuron axons spread out (less overlap with pyramidal dendrites) so fewer synapses per pair, more targets per interneuron (59-62 vs 48-49).
3. **Group steering works as a targeting tool**: with W 1.0 the share of Int->Pyr synapses landing on the interneuron's own pyramidal group is 0.51 / 0.46 (chance 0.24-0.26; the A0 control gives 0.24), with W 0.6 0.43 / 0.37. Side effects: Int->Int synapses fall by 60% (1091 -> 425), because interneurons are no longer attractors for each other's axons; Pyr->Pyr, Pyr->Int and all other bars are unchanged within noise.
4. **No arm rescues seed 44444** (drivable 4-6, needs >= 7; baseline 3). Seed 33333: A3 (W 1.0) and A5 (steering, W 1.0) keep all 7 bars; A1, A2, A4 lose bar 3.
5. **Weight-0 thinning is statistically indistinguishable from the baseline connectome on these metrics.** Higher pyramidal D (0.035, 0.05) raises Pyr->Pyr p to 0.39 / 0.45 and synapses/pair to 2.9 / 3.6-3.7, failing bar 1 (p <= 0.3; B2 also bar 7, A 22%). Randomly zeroing synapses to the baseline total gives p 0.276-0.283 and spc 1.99-2.05, equal to the baseline (p 0.28, spc 1.98-2.07), all 7 bars pass wherever the baseline does. Recall with thinned weights is clean everywhere. The un-thinned high-D models also recall cleanly (up to c = 1.5) and fit more memories (7-9 4+2 vs 2-3).
6. **Visual check (C): the arbors do collapse, not wrap around.** All axons, from every soma, end in a dense ball (median radius 36 um from disc centre, p99 66 um) near the disc centre regardless of where the soma sits, with 1000-5000x higher node density in the centre than at the rim of the disc; tip straightness 0.12-0.13 (very tortuous); 67-80% of an axon's nodes lie within 2 um of a non-relative node of the same cell. Dendrites do the opposite (pyramidal dendrite median radius 192 um, 73% outside the 120 um disc, up to 600 um). Lower W spreads the interneuron axon ball (p99 radius 113 um at W 0.3) and removes the entanglement (self-contact 0.78 -> 0.24).

## A. Arms (bars 1-7 as in headline_i `bars.py`; `bars_table.json`, `pv_results.json`)
| arm | seed | p | Pyr->Pyr/pair | Int->Pyr/pair | Pyr->Int/pair | A % | drivable (>=7) | zero-in | int axon extent um | own-group share (syn) | Int->Int syn | failed bars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline (0.9) | 33333 | .280 | 1.98 | 4.35 | 3.40 | 45.7 | 10 | 3 | 140 | - | 1091 | none |
| A0 own set 0.9 | 33333 | .280 | 2.01 | 4.31 | 3.37 | 45.2 | 11 | 3 | 140 | .24 | 1081 | none |
| A1 W 0.3 | 33333 | .279 | 2.03 | 2.55 | 3.36 | 37.0 | 10 | 1 | 204 | .26 | 629 | 3 |
| A2 W 0.6 | 33333 | .279 | 2.00 | 3.42 | 3.40 | 41.7 | 10 | 2 | 157 | .24 | 864 | 3 |
| A3 W 1.0 | 33333 | .279 | 2.04 | 4.69 | 3.42 | 45.7 | 10 | 1 | 138 | .24 | 1129 | none |
| A4 steer W 0.6 | 33333 | .279 | 2.05 | 3.00 | 3.30 | 38.0 | 9 | 1 | 172 | .43 | 415 | 3 |
| A5 steer W 1.0 | 33333 | .278 | 2.00 | 4.47 | 3.41 | 44.5 | 10 | 2 | 149 | .51 | 425 | none |
| baseline (0.9) | 44444 | .278 | 2.07 | 4.51 | 4.39 | 45.3 | 3 | 2 | 132 | - | 771 | 5 |
| A1 W 0.3 | 44444 | .283 | 2.03 | 2.69 | 4.39 | 38.8 | 4 | 2 | 195 | .25 | 435 | 3, 5 |
| A2 W 0.6 | 44444 | .279 | 2.05 | 3.60 | 4.49 | 42.4 | 6 | 2 | 151 | .25 | 576 | 3, 5 |
| A3 W 1.0 | 44444 | .281 | 2.05 | 5.16 | 4.39 | 46.4 | 5 | 2 | 129 | .26 | 802 | 5 |
| A4 steer W 0.6 | 44444 | .291 | 2.01 | 3.03 | 3.97 | 38.1 | 5 | 3 | 179 | .37 | 423 | 3, 5 |
| A5 steer W 1.0 | 44444 | .278 | 2.03 | 4.14 | 4.48 | 44.0 | 4 | 2 | 155 | .46 | 456 | 5 |
Notes. (i) A0 is **not** identical to the baseline: dendrites are identical (100% of nodes), axons only 44% (pyramidal) / 52% (interneuron) identical to 1e-3 um, so any parameter line reshuffles the random stream for axons; same-seed differences between arms therefore mix the lever with a new realisation (the interneuron axon length and branching are identical anyway). Seed-to-seed noise applies when judging drivable changes (44444: 3 -> 4-6 is inside the noise, the interneuron count that can be driven stays below 7 in all five arms). (ii) Pyramidal axon geometry also differs between arms (random-stream effect; extent of pyramidal axons unchanged within 1%).

## B. Weight-0 thinning (`thin.py`, `dyn3.py`, `feas_B*.json`, `raw_*.json`)
Rule R = each Pyr->Pyr synapse kept with probability (baseline total / higher-D total) (r = 0.48 / 0.34 on 33333, 0.51 / 0.35 on 44444), pair weight = n_kept/n, zero if none; Pyr->Int and interneuron pairs untouched. Rule W = pairs with fewest synapses zeroed first.
| model (seed) | p | Pyr->Pyr/pair | A % | failed bars | max disjoint 4+4 / 4+2 | recall clean (D42+D44, c 0.15 and 1.5, GABA on) |
|---|---|---|---|---|---|---|
| baseline 33333 / 44444 | .280 / .278 | 1.98 / 2.07 | 45.7 / 45.3 | none / 5 | 1 / 3 and 0 / 2 | (headline_i: clean) |
| B1 D 0.035 | .391 / .384 | 2.93 / 2.94 | 28.9 / 29.9 | 1 / 1, 5 | >= 3 / >= 7 (lower bounds) | 100% (all memories, 90 + 54 events) |
| B2 D 0.05 | .446 / .439 | 3.63 / 3.71 | 22.4 / 22.5 | 1, 7 / 1, 5, 7 | >= 4 / >= 9 (lower bounds) | 100% |
| B1 rule R | .276 / .283 | 1.99 / 2.02 | 46.0 / 45.8 | none / 5 | 1 / 3 and 1 / 2 | 100% |
| B2 rule R | .281 / .277 | 1.98 / 2.05 | 45.6 / 45.4 | none / 5 | 1 / 3 and 1 / 2 | 100% |
| B1 / B2 rule W | .072 / .043 (33333), .078 / .042 (44444) | 7.7-13.6 | ~45.7 | 1, 2 (+5) | not run | not run |
Recall: every full-cue event completed, every 3-cell event stayed silent, 0 spurious non-member Pyr spikes, 0 other-group members fired, in all 32 sims (c 0.15 and 1.5, GABA on only; GABA-silenced and c 3.0 were not run here). Equivalence rule from the preregistration (thinned bars pass wherever the baseline passes and recall within one memory-trial): **met for rule R**; rule W (kill weakest pairs) is not equivalent (p 0.04-0.08, bars 1 and 2 fail).

## C. Morphology (`morph_check.py`, `morph_check.json`, `png/*_network.png` top and side views, `png/*_cells.png` 3 interneurons + 3 pyramidal cells; 12 models: baseline, A1-A5, both seeds)
| model | int axon nodes outside slab (|z-zc|>15) | axon node density centre/rim | tip straightness (int) | self-contact (int axon) | int axon p99 radius um | outside disc |
|---|---|---|---|---|---|---|
| base 33333 | 11% | 1150x | 0.126 | 0.78 | 66 | 0.01% |
| A1 W 0.3 | 44% | 35x | 0.144 | 0.24 | 113 | 0.67% |
| A3 W 1.0 | 8% | 1528x | 0.133 | 0.80 | 63 | 0.01% |
| A5 steer 1.0 | 35% | 19x | 0.108 | 0.77 | 98 | 0.03% |
(all 12 rows in `morph_check.json`). Max parent-child segment 64 um (33333) / 92 um (44444), 0.6% of segments above 25 um, p99 22.9 um; these are identical in every arm, so they come from pyramidal arbors and the unchanged part of the pipeline, I did not trace the cause (no evidence of teleports: only 0.6%; a true wrap-around check against the region boundary was not possible because the code has no periodic boundary I could identify). Judgement from the images: the interneuron axon ball sits inside the 120 um disc and is roughly round (about +-30 um in z, i.e. mostly inside the 30 um slab at W 1.0, 11% of nodes outside); pyramidal and interneuron dendrites extend hundreds of um, far outside the disc.

## Preregistration scoring (HIT inside range, PARTIAL up to 25% beyond, MISS otherwise)
| | prediction | observed | |
|---|---|---|---|
| P1 | A0 reproduces baseline arbors (>=99% nodes identical) | 44-52% axon nodes, 100% dendrite | MISS |
| P2 | int axon length within ±15% | identical (0.0%) | HIT |
| P3 | extent non-increasing in W, A1 >= 1.10 x A3 | monotone both seeds; 1.48x / 1.51x | HIT |
| P4 | Int->Pyr/pair in range for all A1-A3 runs | 4 of 6 in range (A1, A2 fail both seeds: 2.55-3.60) | MISS |
| P5 | A rescues 44444 (25%); loses a bar on 33333 (40%) | no rescue; A1, A2 lose bar 3 | HIT, HIT |
| P6 | own-group share > 40% in all four S runs / > 30% in all four | 0.37-0.51 / yes | PARTIAL / HIT |
| P7 | steering leaves p, spc within ±0.05/±0.3; drivable change <= 3 | yes; yes | HIT |
| P8 | B2 spc > 4.5; B1 in range | B2 3.63-3.71 (bar 2 passes; bar 1 and 7 fail instead); B1 in range | MISS / HIT |
| P9 | R: p >= baseline + 0.03; spc <= baseline - 0.2; >= 2 of 4 pass all 7 | p equal to baseline (0.276-0.283); spc equal; 2 of 4 pass (the two 33333 models; 44444 fails bar 5 like its baseline) | MISS, MISS, HIT |
| P10 | thinned recall clean >= 80%; unthinned more spurious than thinned | 100%; zero spurious everywhere | HIT / MISS |
| P11 | max segment <= 25 um; >50% int axon nodes outside slab; straightness 0.3-0.8; centre density >= 1.5x | 64/92 um; 11%; 0.126; 1150x | MISS, MISS, MISS, HIT |
Overall: the direction of the effects (extent, steering share, group size) was predicted; the magnitude of the cost to bar 3, the equality of the thinned connectome to the baseline, and the geometry of the collapsed arbors were not.

## Honest limits
- Two seeds, one realisation per arm, no repeats. A realisation change reshuffles axons (A0), so small differences (drivable 3 vs 4-6, spc 1.98 vs 2.05) are noise; only effects well beyond the existing E4 spread (Int->Pyr/pair 2.5-3.6 vs 4.3 +- 0.5, extent 1.5x, own-group share 0.5 vs 0.24) are claimed.
- The own-set parameter is outside what bio_check validates (it checks the 7 global hard limits, which passed in all runs); W 0.3-1.0 is inside the 0.1-1.0 sample range of Randal's study, which is not itself a documented limit of the code (randal_examples_m).
- Steering uses 4 arbitrary groups (index mod 4), no functional meaning; XOR examples use named cell groups; the stated "natural arborization" notion was not defined by Randal's materials, so I tested only what the lever does.
- (B): the dump has no per-synapse distances, so random per-synapse thinning is an approximation; real D reduction removes the longest-distance synapses. Equal p and spc after rule R is largely built in (the same total is imposed), the informative part is that bars and recall behave identically. Rule W was only scored on bars.
- Recall used forced cue spikes, the R3 weights and `BatchSetPrePostStrength`, which (per the 2026-11-22 LEARNINGS entry from the gaba_vm worker) zeroes NMDA on the programmed pairs; so this recall is the same AMPA-only recall as all earlier recall results here, not a full AMPA+NMDA test. GABA silenced and c 3.0 were not run.
- (C) is a visual and quantitative check, not a comparison with real tissue; the self-contact measure uses a 2 um threshold with 10-step ancestors excluded, my own choice.
