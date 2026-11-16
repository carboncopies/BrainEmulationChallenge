# Line 379 of synapse_formation_model.cc: verdict, fix, first validation (2026-11-15, ledger task tmwidgz0z)

## Summary
1. Verdict: `frac_T_PQ = tx/qx` is a real bug (high confidence). It should be `tx/PQ`.
2. The same line is in upstream NetMorph (Randal Koene's GitHub repo and the diyhpl mirror), so it is old, not a BrainGenix port error.
3. Toy test: the current code accepts 2-19% of true crossings, almost only for axons pointing along +x. With `tx/PQ` it matches an independent ground truth exactly and has no direction bias.
4. Patched build made in a separate copy and run on separate ports. The running NES/API was not touched. No git, no commit.
5. Validation (S1, V1, V3, seed 16180, D_synmax unchanged at 1.5 / 0.1): arbors identical to baseline to the um.
6. Interneuron-pair synapses rise x30-36, Pyr->Pyr x4.9-5.0. I predicted x13 and x2.9: right direction, too small.
7. Synapses per Int->Pyr pair: 14.2 (S1), 9.0 (V1), 12.7 (V3). PV target is about 11. Baseline was 1.4-1.6.
8. Drivable interneurons (8-cell): 33, 31, 39 of 48 (bar is 16; baseline 2, 4, 2).
9. Inhibitory fraction A: 12.2%, 7.6%, 8.8%. This is above the 3-6% band. V1 (PV axon length) is closest.
10. +x share of synapse-carrying segments: 4.7-4.9% (baseline 57%), equal to the all-segment share. No parameter leaves bio_ranges.json.

Files: `line379_fix.diff` (the patch), `toy_test.py` / `toy_test.log`, `PREREGISTRATION.md` (written before launch, not edited), `grow_pv.py`, `run_all.sh`, `analyze_pv.py`, `measure.py`, `xdir.py`, `pv_results.json`, `analyze.log`, `xdir.log`, `grow_*_fix/`.

## 1. Research verdict
- Read in code (lines 200-415): the axon piece PQ is translated to the origin and rotated onto the x-axis, so it runs from 0 to `PQ`. `ux` (= `tx`) is the x-coordinate, in that rotated frame, where the dendrite piece crosses. The crossing point on the axon is then `P + (tx/PQ)(Q-P)`. The code divides by `qx = Qx-Px` (line 207), the axon's x-component in world coordinates. The two agree only when the axon points along +x.
- `double qx3 = PQ;` is defined at line 345 and used in condition B1. The most likely history is a typo of `qx` for `qx3`. (Guess about history; the geometry does not depend on it.)
- Upstream: `https://raw.githubusercontent.com/randalkoene/netmorph/master/synapse_formation_model.cc` line 549 and `https://secure.diyhpl.us/cgit/netmorph/plain/synapse_formation_model.cc` line 540 both have `tx/qx`, with the same `qx = Qx - Px`. I did not find the SECO Year 2 report the code cites, so I could not compare with the written derivation.
- Toy test (`toy_test.py`, 4 million random 5 um segment pairs, numpy port of the C++ arithmetic, ground truth = closest points of the two carrier lines inside both pieces and distance <= D):

| D | current: accepted / true | current: share of accepted with cos(axon,+x) > 0.9 | tx/PQ: accepted / true | tx/PQ: share |
|---|---|---|---|---|
| 0.1 | 0.021 | 86% | 1.000 | 4.8% |
| 0.15 | 0.029 | 83% | 1.000 | 4.8% |
| 1.5 | 0.190 | 26% | 1.000 | 5.0% |

  With `tx/PQ`: zero false accepts, zero misses, |TU - true distance| <= 1.4e-15, conditions A, B1, B2 equal "closest points lie inside both pieces" in every case. Fixed axon directions at D 0.1: +x 1.000, -x 0.001, +y 0.000, +z 0.000, diagonals 0.006-0.007 (current) versus 1.000 everywhere (fixed).
- The rest of the test (rotations, conditions A/B1/B2, `frac_U_RS`) is correct; only this line is wrong. The current code never accepts a false crossing; it only rejects true ones.
- Confidence: about 97% that this is an unintended error. The remaining doubt is only whether the D_synmax values in use were tuned to compensate for it (see section 4).

## 2. Patch and build
- Patch: one line, `double frac_T_PQ = tx/PQ;` (`line379_fix.diff`, paths relative to the NetmorphCMake submodule).
- Build: plain copy (rsync, no .git, no Build) of `/home/johnjose/BrainGenix/BrainGenix-NES` to `/home/johnjose/BrainGenix/wt/nes-linefix`; `vcpkg_installed` copied from the main Build; `cmake .. -DCMAKE_BUILD_TYPE=Release -DVCPKG_MANIFEST_INSTALL=OFF`; build rc 0. No source file in the main tree is newer than the running binary (built 2026-10-04), so the patched build differs from the baseline binary by this line only (same tree, same build type; compiler not re-verified).
- NetMorph is linked statically into the NES binary, so a patched NetMorph needs its own NES process.
- Instance: `/home/johnjose/BrainGenix/wt/linefix-instance` (API copy with `API.cfg` ports 8010 / 8009 / NES 8011; copy of the API's `users.json`, mode 600; output under `out/`). Patched `NES.yaml`: port 8011, `Output_BasePath` = that `out/` folder.
- Restart (both were stopped after the runs; an idle NES uses about 2 cores):
  `cd /home/johnjose/BrainGenix/wt/nes-linefix/Binaries && source /home/johnjose/BrainGenix/BrainGenix-NES/venv/bin/activate && setsid nohup ./BrainGenix-NES > ../../linefix-instance/nes.log 2>&1 &` then `cd /home/johnjose/BrainGenix/wt/linefix-instance/api && setsid nohup ./BrainGenix-API > ../api.log 2>&1 &`. Clients use `-Port 8010`.
- Incident: the first launch failed in 2 s ("Service unavailable") because the second API looks for `../Source/Core/Config/users.json` relative to its working directory. Fixed by copying that file; nothing had run.

## 3. Validation, seed 16180, D_synmax 1.5 (pyr-pyr) / 0.1 (three interneuron pairs)
Baseline = existing unpatched runs in `../pv_arbor_seeds`. `.nibr.clp` read back as 1.5 / 0.1 / 0.1 / 0.1 and bio_check pass in all three. rc 0; walls 5223 / 3476 / 4201 s (baseline 3309 / 1994 / 2318). Each run deleted its resident simulation.

| run | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | syn/pair I->P | targets/int (of 96) | inhib A / B (%) | drivable 8-cell (simple) | zero-input | int axon len | int dend len |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 baseline | 73,105 | 348 | 1,616 | 685 | 1.60 | 21.0 | 2.16 / 3.04 | 2 (8) | 14 | 74,624 | 6,629 |
| S1 fixed | 365,853 | 11,326 | 50,982 | 22,328 | 14.21 | 74.8 | 12.23 / 16.27 | 33 (38) | 2 | 74,624 | 6,629 |
| V1 baseline | 70,921 | 461 | 876 | 509 | 1.38 | 13.3 | 1.22 / 1.90 | 4 (11) | 17 | 45,207 | 6,734 |
| V1 fixed | 348,125 | 15,974 | 28,484 | 18,329 | 8.95 | 66.3 | 7.56 / 11.39 | 31 (35) | 4 | 45,207 | 6,734 |
| V3 baseline | 86,230 | 573 | 1,364 | 717 | 1.56 | 18.3 | 1.56 / 2.34 | 2 (14) | 12 | 55,380 | 9,406 |
| V3 fixed | 421,278 | 17,692 | 40,440 | 24,137 | 12.69 | 66.4 | 8.76 / 12.82 | 39 (41) | 0 | 55,380 | 9,406 |

Ratio fixed / baseline: Pyr->Pyr 5.00 / 4.91 / 4.89; Pyr->Int 32.5 / 34.7 / 30.9; Int->Pyr 31.5 / 32.5 / 29.6; Int->Int 32.6 / 36.0 / 33.7. Arbor lengths ratio 1.0000 (all four fibre classes), reach within 0.6%.
Other pairs: synapses per Pyr->Int pair 4.4 / 6.4 / 6.1, per Int->Int pair 13.2 / 12.6 / 13.7.

Direction (xdir.py, Int->Pyr synapse-carrying axon segments with cos(+x) > 0.9): S1 4.66% (n 50,982), V1 4.68% (28,484), V3 4.93% (40,440); all interneuron axon segments 4.71 / 4.79 / 4.85%. Median cosine -0.01 / -0.02 / 0.01 (baseline 0.93). The synapses are isotropic.

Independent check: the plain line-crossing formula in FABLE_ANALYSIS section 1.2 gave, for S1 at D 0.1, Int->Pyr 47,195, Int->Int 20,546, Pyr->Int 10,375. The patched run gives 50,982, 22,328, 11,326: 8-9% above the formula in all three. The patched code now does what the crossing model says.

## 4. Movement toward PV targets
- Synapses per Int->Pyr pair: 14.2 / 9.0 / 12.7 against about 11. The target is bracketed; V1 (the variant with PV-range axon length, 45k um) is slightly below, S1 and V3 slightly above.
- Targets per interneuron: 66-75 of 96 (69-78%), up from 13-21.
- Drivable 8-cell >= 16: met in all three (31-39 of 48). Summed-conductance proxy, not a dynamic simulation.
- Inhibitory fraction 3-6%: NOT met; it overshoots (A 7.6-12.2%, B 11.4-16.3%). Interneuron pairs rise x32 while Pyr->Pyr rises x5.
- Pyr->Pyr is now 348-421k synapses, about 3,600-4,400 per pyramidal cell (bio_ranges.json info line: 5,000-10,000 per neuron), about 40 per ordered pyramidal pair. The old "Pyr->Pyr within 5%" rule cannot be applied across this change.
- Biological ranges: no parameter was changed; all seven hard-limited parameters and the four D_synmax values are inside bio_ranges.json.
- Levers that stay inside the ranges if the overshoot must come down (not tested): D_synmax for interneuron pairs has a maximum only, so values below 0.1 are allowed; with the fix the count is linear in D, so about 0.05-0.07 should put V1 near 4-5% (A) but would also cut synapses per pair in the same proportion (V1 to about 5-6). The 11 per pair and the 3-6% targets pull in opposite directions at this arbor size; fewer interneurons (48 is 33% of cells, docs say 20-30%) lowers the fraction without lowering synapses per pair. This is a decision for John / Randal, not something I tuned.

## 5. Scored preregistration
- 1 arbors unchanged: HIT (ratio 1.0000, reach within 0.6%).
- 2 interneuron-pair ratio x13 (9-18): MISS, measured x30-36. Cause: my 7.7% acceptance figure for the unpatched test was about 2.4 times too high; the true figure is about 3%. The geometric formula count (section 3) was right.
- 3 Pyr->Pyr x2.9 (2.0-4.0): MISS, measured x4.9-5.0 (unpatched acceptance at D 1.5 is about 20%, not 35%).
- 4 synapses per pair 5.1 / 3.2 / 4.5: MISS (measured 14.2 / 9.0 / 12.7); "below 11 in all three" was wrong for S1 and V3.
- 5 targets 85 / 75 / 82: S1 74.8 PARTIAL (range 75-93), V1 66.3 HIT (62-86), V3 66.4 MISS (72-91).
- 6 inhibitory A 9.0 / 5.3 / 6.6: all three inside the stated ranges, HIT; B 16.3 / 11.4 / 12.8 against 12 / 8 / 9.5 +-4: S1 PARTIAL, V1 and V3 HIT. "S1 overshoots, V1 nearest" HIT.
- 7 drivable 44 (36-48): S1 33 and V1 31 below range (MISS), V3 39 HIT; ">= 16 in all three" HIT; zero-input 0-2: S1 2, V3 0 HIT, V1 4 MISS.
- 8 +x share 4-7%: HIT (4.7-4.9%).
- 9 bio_check pass HIT; wall 1.0-1.6x: 1.58 HIT, 1.74 and 1.81 MISS.
- Falsifiers (ratio below x5, +x above 15%, arbor change above 1%): none occurred.
The direction and the mechanism held; my size estimates were too low by a factor of about 2.4 for interneuron pairs and 1.7 for Pyr->Pyr.

## 6. Limits
- One seed, one realisation per variant. The count ratios are within-realisation (identical arbors), so they are not seed-sensitive; drivable and targets are.
- The fix has not been reviewed by Randal Koene or the NES team; the D_synmax limits (1.5 / 0.15) were agreed while the test passed about 20% / 3% of contacts, so they may need to be revisited together with the fix.
- Nothing downstream was run on the fixed networks (no dynamics, no ripple or recall tests). A fivefold Pyr->Pyr count will change the functional model.
- Models `v2-lfx-*` were saved by the patched instance under its own output folder, not in the main NES store.

## Housekeeping
Running NES (PID 3156209) and API (PID 1972355) untouched and still up. Main repo tree not edited. No git operation, no commit, no push, no email. Max 3 concurrent sims; no other sims were running. Patched NES and API stopped after the runs. Disk: 1.5 GB build copy, 2.1 GB output under `/home/johnjose/BrainGenix/wt/`.
