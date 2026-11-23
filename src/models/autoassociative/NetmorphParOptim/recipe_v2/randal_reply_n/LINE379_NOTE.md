# Line 379 of synapse_formation_model.cc: what it does, and what it hid (note for Randal, 2026-11-22)

Status: written for Randal Koene's review. Nothing here was pushed or sent to upstream; the fix exists only as a one-line diff and in a separate local build. Everything below comes from our own files (paths at the end); nothing new was simulated for this note.

## 1. The line, in one paragraph
NetMorph tests whether an axon line piece PQ and a dendrite line piece RS cross within D_synmax. It translates P to the origin and rotates the frame so PQ lies on the x-axis, running from 0 to PQ (length `PQ`). In that rotated frame, `tx` is the x-position (along the axon piece, in um) where the closest point sits, and `ux` the same for the dendrite piece. To place the contact on the real axon piece the code then needs the fraction of the way along PQ:

- current, line 379: `double frac_T_PQ = tx/qx;`
- proposed: `double frac_T_PQ = tx/PQ;`

`qx` is defined at line 207 as `qx = Qx - Px`: the x-component of the axon piece in WORLD coordinates (before rotation). `tx` is a distance along the rotated axon axis, which has length `PQ`. The two are the same number only when the axon piece happens to point along +x in world coordinates (then `qx = PQ`). `PQ` is already in the file (`double qx3 = PQ;` at line 345, used in condition B1), so I think this is a typo of `qx` for `qx3`; that is a guess about history, and the geometry below does not depend on it.

Where the fraction is used: `Tx = Px + frac_T_PQ*(Qx - Px)` and the same for y, z, then the distance TU between the two contact points, which is compared with D_synmax. With the wrong fraction, T lands somewhere other than the closest point (or off the segment), TU is too large, and a true crossing is rejected. The wrong fraction cannot create a false accept; it only rejects true contacts (see the toy test).

Conditions A, B1, B2 and `frac_U_RS` are correct; only this fraction is wrong.

## 2. Toy test (4 million segment pairs; `linefix/toy_test.py`, log `linefix/toy_test.log`)
- Numpy port of the C++ arithmetic, so it tests the formulas, not the compiled program. Random 5 um segment pairs, 4,000,000 per D value, isotropic directions.
- Ground truth, independent of the NetMorph code: closest points of the two carrier lines, both inside their pieces, distance <= D.
- Result ("accepted / true" = share of true crossings that the code accepts):

| D_synmax (um) | current `tx/qx` accepted / true | share of accepted segments with axon cos(+x) > 0.9 | `tx/PQ` accepted / true | same share |
|---|---|---|---|---|
| 0.1 | 0.021 | 86% | 1.000 | 4.8% |
| 0.15 | 0.029 | 83% | 1.000 | 4.8% |
| 1.5 | 0.190 | 26% | 1.000 | 5.0% |

- Isotropic expectation for the "cos(+x) > 0.9" share is 5.0%. With `tx/PQ`: zero false accepts, zero misses, |TU - true distance| <= 1.4e-15, and conditions A, B1, B2 equal "closest points lie inside both pieces" in every case.
- Fixed axon directions at D 0.1 (acceptance relative to truth, current vs fixed): +x 1.000 / 1.000; -x 0.001 / 1.000; +y 0.000; +z 0.000; xy diagonal 0.007; xyz diagonal 0.006 (the fixed code gives 1.000 everywhere).

## 3. How much was hidden
Share of true contacts that the current line hides = 1 - accepted/true: 98% at D 0.1, 97% at D 0.15, 81% at D 1.5 (toy test). So "about 90%" is roughly right as a summary, but it depends on D: the smaller D_synmax, the more is hidden. The contacts that survive almost all belong to axon pieces pointing along +x.

## 4. Effect on counts in grown networks (patched build, same seed and same arbors)
(`linefix/README.md`, seed 16180; the patched build differs from the baseline binary by this line only; arbors identical to the um, arbor length ratio 1.0000, reach within 0.6%.) D_synmax unchanged at 1.5 (Pyr->Pyr) / 0.1 (interneuron pairs).

| | baseline (current code) | fixed | ratio |
|---|---|---|---|
| Pyr->Pyr synapses (S1 / V1 / V3) | 73,105 / 70,921 / 86,230 | 365,853 / 348,125 / 421,278 | x4.9-5.0 |
| Pyr->Int | 348 / 461 / 573 | 11,326 / 15,974 / 17,692 | x31-35 |
| Int->Pyr | 1,616 / 876 / 1,364 | 50,982 / 28,484 / 40,440 | x30-32 |
| Int->Int | 685 / 509 / 717 | 22,328 / 18,329 / 24,137 | x33-36 |
| Int->Pyr synapses per connected pair | 1.60 / 1.38 / 1.56 | 14.2 / 9.0 / 12.7 | |
| pyramidal targets per interneuron (of 96) | 21 / 13 / 18 | 75 / 66 / 66 | |
| share of synapse-carrying segments with cos(+x) > 0.9 | 57% | 4.7-4.9% | all segments: 4.7-4.9% |

The synapses are no longer biased along +x (median cosine about 0 instead of 0.93). An independent plain line-crossing count (FABLE_ANALYSIS section 1.2) for S1 at D 0.1 gives 47,195 Int->Pyr; the patched run gives 50,982 (8-9% above the formula, same for the other pairs). In other words the patched code now agrees with the crossing model, while the unpatched code agrees with it only for +x axons.

Later work (all on the patched build): with the fix, pyramidal D_synmax had to be lowered to 0.0175 and interneuron D_synmax set to 0.03 to bring Pyr->Pyr per-pair counts into a sourced band; those are the "E4" recipe networks (recipe_v2/headline_h and headline_i). That later tuning is only valid with the fix in place.

## 5. How this relates to the assumption that small interneuron outgrowth was the cause
What I can say, and what I cannot.

Can say:
- With arbors held fixed (identical to the um), changing this one line raised Int->Pyr synapses about x30 and moved synapses per pair from about 1.5 to 9-14, i.e. into the biological range (PV basket to pyramidal about 4-9 per pair; Lee 2014 CA1 mouse 8.7 and 4.0 boutons per pair, Foldy 2010 about 11, see lit_review/LIT_REVIEW.md). So the line alone is enough to explain the shortfall in the interneuron connection counts of our grown networks; no change in outgrowth is needed to reach the biological per-pair counts.
- The arbors we grew are not obviously small: V1 interneuron axon about 45,000 um and dendrite about 6,900 um per cell (E4, 10 networks), against measured values of roughly 20,000-46,000 um axon and 3,000-9,000 um dendrite in the literature (see CA3_MORPH_COMPARE.md; mostly slice cells with cut axons, so axon values are lower bounds).
- Before the fix we also tried longer or more branched interneuron axons and dendrites (ARBOR_RESULTS.md). The dendrite lever raised Pyr->Int and Int->Int by x2.4 as designed. The axon lever did not change the growth-cone count (63-73 per cell against 74 baseline), so that experiment did NOT test bigger axons and I do not claim it showed axon outgrowth was irrelevant. Int->Pyr stayed at 298-542 (about 1.4-1.6 per pair) in all four configurations.

Cannot say:
- That the real interneuron outgrowth in NetMorph is correct. We compared total length, node count and reach for a few cell types only against published slice and in vivo cells (CA3_MORPH_COMPARE.md); branch counts and per-type shapes are not validated, and we did not look at the morphologies spatially.
- That your hypothesis is wrong. If outgrowth is also short in some configuration, that would add to the shortfall; the bug hides contacts independently of arbor size. The two effects multiply, and our experiments held outgrowth fixed, so they cannot separate the two in general.
- How much of the published NetMorph literature is affected. van Ooyen et al. 2014 used 4-10 um criteria for L2/3 pyramidal cells and got 2.53-5.57 synapses per connection, in line with experiment. The acceptance at larger D is higher (19% at D 1.5 in the toy test); I did not run D 4-10, so I do not know how much of those counts the line hid. I would not call those results wrong; whether they used this branch of the code the same way is for you to say.

## 6. How to reproduce on a branch (no sim needed for the first step)
1. Toy test, no NetMorph needed: `python3 recipe_v2/linefix/toy_test.py` (numpy; RNG seed 12345; run time not measured). It prints the table above.
2. Patch (`recipe_v2/linefix/line379_fix.diff`, paths relative to the NetmorphCMake submodule):
```
--- a/Source/synapse_formation_model.cc
+++ b/Source/synapse_formation_model.cc
@@ -376,7 +376,7 @@
-    double frac_T_PQ = tx/qx;
+    double frac_T_PQ = tx/PQ;
```
   In the checkout I have (NetmorphCMake `main`, merge `1189112`) the line is 379; upstream randalkoene/netmorph master has it at line 549 and the diyhpl mirror at line 540, with the same `qx = Qx - Px` definition, so the bug is old and not a BrainGenix port issue.
3. On your own branch: apply the one-line change in `ThirdParty/NetmorphCMake/Source/synapse_formation_model.cc`, rebuild NES (NetMorph is statically linked, so a patched NetMorph needs its own NES process). Our setup: plain copy of the NES tree, `cmake .. -DCMAKE_BUILD_TYPE=Release -DVCPKG_MANIFEST_INSTALL=OFF`, own ports (NES 8011, API 8010), separate output folder (details in `linefix/README.md` section 2).
4. Compare with a baseline: grow the same model with the same seed and the same D_synmax on both builds; the arbors should be identical (lengths ratio 1.0000) and synapse counts should differ as in section 4. Also count the share of synapse-carrying segments with cos(+x) > 0.9: about 57% before, about 5% after. `linefix/xdir.py` does this.
5. Caveat for determinism: the same seed does not give an identical network on regrowth (about 70% of nodes match, `repro_g`); compare over several seeds, or compare synapse counts on a single grown network before and after thresholding.

## 7. Honest limits
- The toy test is a port of the arithmetic, not the compiled code. The patched build validates against the crossing model on three arbors (seed 16180) only.
- The patched build has not been reviewed by you or the NES team; we do not know whether the D_synmax limits in bio_ranges.json (1.5 / 0.15) were tuned with the old behaviour in mind. I rate "unintended error" at about 97%.
- Upstream issue tracker: no issue, fork or paper found about this line (search was limited, not exhaustive; lit_review/LIT_REVIEW.md).
- Nothing was pushed or sent. You asked to see our branch; I have not created a merge request.

## Files (all under /home/johnjose/cos/netmorph_work/recipe_v2/)
linefix/line379_fix.diff, linefix/README.md, linefix/toy_test.py, linefix/toy_test.log, linefix/xdir.py, linefix/xdir.log, linefix/PREREGISTRATION.md, lit_review/LIT_REVIEW.md, ARBOR_RESULTS.md, headline_h/, headline_i/.
