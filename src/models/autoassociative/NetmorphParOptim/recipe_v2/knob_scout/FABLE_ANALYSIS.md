# Fable analysis of the knob scout: is PV-like interneuron connectivity reachable? (2026-11-15)

## Summary (10 lines)
1. The main limit is not arbor shape. The synapse test in NetMorph misplaces one point (`synapse_formation_model.cc:379`, `tx/qx` where `tx/PQ` is needed) and so rejects about 92% of true axon-dendrite crossings at D_synmax 0.1 (65% at 1.5).
2. This is confirmed in our own output: 57% of the axon segments carrying Int->Pyr synapses point along +x (4.7% of all axon segments do), and the code's faulty distance tops out at exactly 0.100.
3. It explains the old D^1.6 scaling exactly (predicted exponent 1.63) and why interneuron pathways are 7.5x sparser than Pyr->Pyr per crossing opportunity.
4. With the present binary and the hard limits, PV-like 11 synapses per pair on most of 96 targets is out of reach: best allowed combination gives about 0.5 synapses per ordered pair (need 11), i.e. 5% of the PV total.
5. The largest allowed lever is D_synmax 0.1 -> 0.15 on the three interneuron pairs: predicted x1.94 on Int->Pyr, Pyr->Int and Int->Int, with unchanged morphology.
6. With the one-line fix, V1 (45k um axon) at D 0.1 would give about 12,000 Int->Pyr synapses (2.6 per ordered pair, most pyramidal cells contacted). That is a code change and a decision for Randal.
7. Lowering the interneuron attraction weight is predicted to LOWER Int->Pyr (x0.56 at weight 0.1, targets 13 -> 10). No weight in 0.1-1.0 gives soma-centred arbors.
8. "Few targets per interneuron" is sparse sampling, not limited reach: a plain overlap model with no target selection predicts 22.7 targets, observed 21.0.
9. Recommended test: D_synmax 0.15 on unchanged V1, V3, S1 at one existing seed (3 runs, one batch). Skip T2. Run T1a only if Randal wants the extent shown (2 seeds).
10. Stop rule: if D 0.15 gives x1.8-2.1 with unchanged arbors, stop tuning growth knobs for connectivity and take line 379 to Randal.

Tags: **[CODE]** read in source (`S/` = `BrainGenix-NES/ThirdParty/NetmorphCMake/Source/`). **[DATA]** measured by me, read-only, on the existing output of one grown network (S1 seed 16180, folder `00657198`, the scout's audited network). **[DERIVED]** arithmetic or a small numeric evaluation from CODE and DATA. **[GUESS]** not checked. Nothing was grown, no NES/API call, no existing file edited. The toy walk in section 2 is a 60-line numpy evaluation of the direction rule, not a NetMorph run.

The Step 0 audit has landed (`step0_audit/README.md`): the centre collapse holds in all 17 runs (median axon-node distance from centre 14-24 um). I treat it as established.

---

## 1. Is PV-like connectivity reachable at all?

### 1.1 What the code tests [CODE]
- A candidate synapse needs: the common perpendicular between the axon segment line and the dendrite segment line has its feet inside both segments (conditions A, B1, B2), and its length TU <= D_synmax (`S/synapse_formation_model.cc:200-415`).
- Segments are registered when they stop being terminal (at a turn or branch), at full length, in every spatial partition they intersect, and tested against all segments in the same and neighbouring partitions (`S/dendritic_growth_model.cc:392-409`, `S/Spatial_Segment_Subset.cc:269-455`). So no crossings are missed by the search.
- For such a test the expected count is the standard line-crossing result: **N = (pi/2) x D x integral of (axon length density x dendrite length density) dV**, linear in D [DERIVED; same formula as ARBOR_DESIGN 2.1].

### 1.2 The formula against our network [DATA]
Length densities on a 5 um grid, per cell, S1 seed 16180:

| pathway | formula | observed | observed / formula |
|---|---|---|---|
| Int->Pyr (D 0.1) | 47,195 | 1,616 | 0.034 |
| Int->Int (D 0.1) | 20,546 | 685 | 0.033 |
| Pyr->Int (D 0.1) | 10,375 | 348 | 0.034 |
| Pyr->Pyr, only synapses with distance <= 0.1 | 23,353 | 6,049 | 0.26 |
| Pyr->Pyr, distance <= 0.5 | 116,767 | 29,259 | 0.25 |

Pyramidal and interneuron axons occupy the same volume (both: 90% of length within r 33 um, z within +-13 um), and the dendrites are the same. So geometry cannot explain a 7.5x gap between pathways at the same distance. The only difference is the D_synmax of the pathway (0.1 vs 1.5).

### 1.3 The cause [CODE + DATA]
- [CODE] Line 379: `frac_T_PQ = tx/qx`. `tx` is the crossing position along the axon segment (0..PQ, the segment length). `qx` is the x-component of the axon segment in network coordinates (line 207), not its length. The correct divisor is `PQ`. The point T on the axon is therefore misplaced along the axon by `err = u x |1/c - 1|`, where u is the distance of the crossing from the segment's proximal end and c is the cosine between the segment and the +x axis. The dendrite point U is computed correctly.
- [DERIVED] The tested quantity is sqrt(d^2 + err^2) <= D_synmax, with d the true distance. A true crossing passes only if the axon segment points close to +x, or the crossing is within a fraction of a micron of the segment's start.
- [DATA] The axon segments that carry the 1,616 Int->Pyr synapses: cosine to +x has median 0.93, and 57% exceed 0.9 (all axon segments: 4.7%, mean cosine -0.006). Cosines to y and z average 0. Median u is 0.36 um on segments of median 4.5 um. The maximum of sqrt(d^2 + err^2) over all 1,616 is 0.100. Pyr->Int gives the same picture (max 0.100); Pyr->Pyr gives max 1.500.
- [DERIVED] Acceptance of true crossings (isotropic segment directions, our measured segment lengths, mean 5 um): **7.7% at D 0.1, 10.0% at 0.15, 35% at 1.5**. Count is proportional to D x acceptance(D): from 0.1 to 0.15 this is x1.94, an exponent of 1.63. **This is the D^1.6 of ARBOR_DESIGN 3.3.** Inside one network the true distances are uniform (Pyr->Pyr counts 6049, 6044, 5762 in the first three 0.1 um bins), so the geometry is linear and the extra 0.6 comes from the acceptance.
- [DERIVED] After dividing by the acceptance, observed/formula is 0.44 (Int->Pyr) and 0.65 (Pyr->Pyr). The isotropic grid formula therefore over-predicts true crossings by 1.5-2.3x. [GUESS] Cause: fibre anisotropy and 5 um smoothing.
- Both source trees (`BrainGenix-NES` and `wt/nes-nt-24-verify`) have the same line [CODE]. The data show the running binary has it.

### 1.4 Reconciling the observed 1.5 per pair [DATA + DERIVED]
- Mean synapses per ordered Int->Pyr pair (all 48 x 96 pairs): 0.20 in V1, 0.32 in S1. A pair is "connected" when it draws at least one, so the mean per connected pair sits near 1.5 and targets near 13-21. This is a low-count regime, as the scout said.
- Per-pair rates from the grid overlap, scaled to the observed total, give 22.7 targets per interneuron and 1.48 synapses per connected pair. Observed: 21.0 and 1.60. No target-selection term is needed. The excess of 2- and 3-synapse pairs over a single Poisson is pair-to-pair variation in overlap.
- True crossings within 0.1 um (observed / 0.077): about 21,000 in S1 (4.6 per ordered pair), about 12,000 in V1 (2.6 per pair) [DERIVED].

### 1.5 Upper bound with the present binary and the hard limits [DERIVED unless marked]
PV-like target: 96 targets x 11 = 1,056 synapses per interneuron = 50,700 Int->Pyr. V1 has 926 (55x short), S1 1,462 (35x short).

| lever (allowed) | factor on Int->Pyr | basis |
|---|---|---|
| D_synmax interneuron pairs 0.1 -> 0.15 | x1.94 | section 1.3 |
| radius 120 -> 100 (soma density x1.44) | x1.2-1.4 | [GUESS] dendrite density at the centre rises less than soma density |
| thickness 30 -> 20 | about x1.0 | [DATA] fibres ignore the slab: pyramidal dendrite length spans z -178..+391 um (5-95%), median r 187 um |
| axon length 45k -> 77k (S1) | x1.58 | measured, but outside the PV length target |
| attraction weight, target switch | <= x1.0 | sections 2, 3 |

Best combination at PV axon length: 926 x 1.94 x 1.3 = about 2,300 Int->Pyr = 0.5 per ordered pair, roughly 30 targets per interneuron at 1.6 per connected pair. That is 5% of the PV total. **11 per pair across most targets is structurally out of reach with this binary.**

One more knob exists but I do not recommend using it without Randal: because acceptance depends on the distance from the segment start, shorter interneuron-axon segments raise it (mean segment 2 um: x1.77; 1 um: x2.6 at D 0.1) [DERIVED]. That is tuning to a defect, it multiplies node count, and it changes arbor shape unless veer is rescaled.

### 1.6 With line 379 corrected [DERIVED; a code change, not something we can do under current rules]
- Int->Pyr at D 0.1: V1 about 12,000 (2.6 per ordered pair; with even overlap 93% of pairs connected, with the measured unevenness about 75-90%). At D 0.15: about 18,000 (3.9 per pair). S1 length at 0.15: about 6.8 per pair.
- Pyr->Int would rise by the same x13, so almost every interneuron becomes drivable.
- Pyr->Pyr at D 1.5 would rise x2.9 (to about 210,000). To hold 72,000 the pyr-pyr D_synmax would drop to about 0.5. With that, inhibitory fraction A for V1 at D 0.1 would be about 14% (biological 10-20%).
- So 11 per pair is within a factor 3-4 at PV axon length, and "most pyramidal cells contacted" is met. The centre collapse helps here: every interneuron axon sits where every pyramidal cell has dendrite.

### 1.7 What this means for the project
- Ask Randal (in this order):
  1. Is `frac_T_PQ = tx/qx` at `synapse_formation_model.cc:379` intended? Evidence: section 1.3. All D_synmax limits (1.5 / 0.15) were set on a test that passes 35% / 10% of contacts, and passes them by axon direction.
  2. If it is corrected, D_synmax for every pair must be re-chosen. May we propose values that keep Pyr->Pyr near 72,000 and put interneuron pairs at 0.1?
  3. If it stays, may we use 0.15 now, and describe the rest as reduced-model scaling?
- Reduced-model wording, if the binary stays: "The grown network realises about 8-10% of geometric axon-dendrite contacts for interneuron pairs and 35% for pyramidal pairs. Int->Pyr is 1.4-1.7 synapses per connected pair against about 11 in PV cells, and 14-22% of pyramidal cells are contacted per interneuron. One model inhibitory synapse stands for about 7 biological contacts; inhibitory strength must be scaled in the functional model, not grown."
- Side effect to mention: synapse-forming axon segments are aligned with +x. Arbors are isotropic, so I expect no topological bias [GUESS].

---

## 2. Axon density under unit-normalised 1/d^2 attraction, and the weight question

### 2.1 Rule [CODE]
Each turn (mean every 5 um): predicted direction = unit(history) + w x unit(sum over all other neurons' dendritic branch points of (vector to point)/d^3). Then a veer of angle uniform in [0.196, 0.785] rad with random roll (`S/axon_direction_model.cc:255-275, 639-651, 737-763`). History is cleared at each branch.

### 2.2 Semi-analytic picture [DERIVED]
- Veer alone: mean cosine per turn 0.869, so persistence length 5 / -ln(0.869) = 36 um (the scout's 35).
- [DATA] The scout missed branching: a root-to-tip path of 632 um passes 19.5 bifurcations, one per 32 um, each a large direction change. Effective persistence is about 27 um.
- Strong weight (0.9): a misalignment psi to the field shrinks to psi/(1+w) per turn. Stationary rms misalignment = 0.52 / sqrt(1 - 1/(1+w)^2) = 0.61 rad. The cone tracks the field and moves along it at about 0.6-0.8 of path speed. From 100 um out it reaches the centre in about 150 um of path; tips have 616 um.
- The field direction [DATA, evaluated on the 6,561 real attractor points]: mean cosine to the centre direction is 0.96 at r 120, 0.90 at 80, 0.69 at 30, 0.50 at 20, 0.13 at 5. Inside r about 20 um nearby points dominate and the direction is random. That core radius is the observed median axon-node radius (19 um; 14-24 across the 17 audited runs).
- Weak weight: drift fraction is about (2/3) x w x c/(1-c), with c about 0.83 including branching, i.e. about 3.3 w. That is 0.33 at w 0.1. The toy gives about 0.17 above the free-walk value. Confinement length beyond the core = (persistence/3) / drift = 9 / 0.17-0.33 = 27-53 um.

### 2.3 Toy evaluation of the same rule in the measured attractor field [DERIVED]
288 walkers from the real interneuron soma positions, 5 um steps, branch reset every 32 um, nodes sampled at the measured path-length distribution. No parameter was fitted.

| weight | node r from centre, median / 90% | z 5-95% | median from own soma (outer somata) | nodes beyond r 120 | Int->Pyr relative | targets per int (V1) |
|---|---|---|---|---|---|---|
| data, 0.9 | 19 / 33 | -13..14 | 107 | 0.000 | 1 | 13.3 |
| toy 0.9 | 17 / 27 | -10..12 | 107 | 0.000 | 1.00 | (14.2) |
| 0.45 | 23 / 43 | -19..19 | 109 | 0.000 | 0.87 | 14.2 |
| 0.2 | 42 / 84 | -41..49 | 109 | 0.016 | 0.75 | 12.9 |
| 0.1 | 68 / 142 | -89..87 | 119 | 0.18 | 0.56 | 10.0 |
| 0.05 (not allowed) | 97 / 185 | -113..136 | 125 | 0.35 | 0.42 | 7.6 |
| 0 (not allowed) | 142 / 255 | -166..168 | 150 | 0.61 | 0.25 | 4.7 |

The toy at 0.9 also reproduces the tip straight/path ratio (0.14 vs 0.14) and the soma-distance medians of all three bands (46/62/107 vs 46/64/107). "Int->Pyr relative" is the overlap of the toy node cloud with the measured per-cell pyramidal dendrite density.

### 2.4 Answers
- **No weight in 0.1-1.0 restores soma-centred arbors.** At 0.45 the collapse is nearly unchanged. At 0.1 the cloud is centred between soma and disc centre, is 68 um (median) from the centre, and leaves the slab in z (+-88 um). Soma-centred needs w <= about 0.02, and then the arbor is a free random walk about 150 um wide, larger than the disc.
- If "PV-like extent" means the arbor fills the disc, the weight is 0.1-0.2 (90% radius 84-142 um), but the arbor is centred on the disc, not on the soma.
- **Lowering the weight LOWERS Int->Pyr at fixed axon length**: x0.87 at 0.45, x0.75 at 0.2, x0.56 at 0.1 (my uncertainty +-0.15). Targets per interneuron fall with it (13 -> 10 at 0.1) and synapses per pair approach 1.1.
- Reason [DATA]: pyramidal dendrite density is 0.066-0.076 um/um^3 at r < 60 um inside the slab, 0.045 at r 100-120, 0.015 at r 160-220, and the low-weight arbor also spreads in z. The sign agrees with the Phase 0 regression the scout quotes.
- Not modelled: the weak homing onto single branch points (axon-weighted dendrite density is 0.084 against about 0.07 ambient, so at most 20% of crossings). Losing it makes low weights slightly worse.

---

## 3. The scout's tests

### 3.1 Verdict on each
- **T1 (weight 0.1 / 0.45).** Mechanism is right, and my toy agrees with the scout's reach numbers (nodes beyond r 120: scout 0.15, toy 0.18). Connectivity outcome is predictable: down. Not worth 6 runs. If Randal wants the extent effect shown, run T1a on 2 seeds, no T1b. My pre-registered numbers for T1a: median node r from centre 68 [45-90]; z 5-95% +-88 [50-110]; Int->Pyr 926 -> 520 [400-700]; targets 13.3 -> 10 [8-13]; synapses per pair 1.15-1.3. Probability targets >= 20: under 3% (scout: 20%).
- **T2 (target switch).** Skip. Targets are set by sparse sampling (section 1.4), and the switch only acts through the homing part (at most 20% of crossings) and through removing about 15 of 143 cells' points from a unit-normalised pull. My prediction: +0.5 to +1.5 targets. Probability of +3 or more: about 7% (scout: 35%).
- **C0 control.** Sound, needed only if T1a is run.

### 3.2 Seeds needed for a +3 targets shift (if any direction knob is tested later) [DERIVED, approximate]
- Baseline SD 1.6 from n = 4 (so the SD itself is uncertain, roughly 1.0-4.7). Restating a model reshuffles the random streams, so compare arms unpaired; same-seed pairing keeps at most soma positions [GUESS].
- Standard error of the difference = SD x sqrt(2/n). Power for +3 at one-sided 5%:

| seeds per arm | SD 1.6 | SD 2.1 (S1, V3 value) |
|---|---|---|
| 4 | about 0.75 | about 0.5 |
| 6 | about 0.9 | about 0.7 |
| 8 | about 0.96 | about 0.85 |

- Use 8 per arm (4 existing baselines + 4 new) and report Int->Pyr total as co-primary (SD 9.5%).

### 3.3 Better single test
**D_synmax 0.15 on the three interneuron pairs, everything else unchanged, V1 + V3 + S1 at seed 16180. Three runs, one batch, about 1 hour.**
- It is paired exactly [GUESS until seen]: synapse draws use their own random stream (`S/global.hh:704-706`) and growth does not read synapses while the switch is off, so arbors should be identical to the existing runs. Check: axon lengths and Pyr->Pyr equal to the existing run.
- Predictions: Int->Pyr, Pyr->Int and Int->Int each x1.94 [1.8-2.1]. V1: 876 -> 1,700, targets 13 -> 21-23, synapses per pair about 1.7, fraction A 1.2 -> 2.3%. V3: 1,364 -> 2,650, A 3.0%. S1: 1,616 -> 3,135, A 4.1%. Pyr->Pyr unchanged.
- If Pyr->Pyr is not identical, the streams are coupled and 3 more seeds are needed.
- A 2x2 of weight x D is not needed. The D effect is a multiplier that depends only on segment directions and lengths; the weight effect is predicted negative.

### 3.4 When to stop growth knobs
- Stop if the D 0.15 runs give x1.8-2.1 with unchanged arbors. That confirms the acceptance picture; the remaining gap (20x or more) sits in line 379, not in any arbor.
- Also stop if T1a (if run) lowers Int->Pyr by 25% or more while reach rises.
- Continue with growth knobs only if D 0.15 gives x1.6 or less. That would mean my reading is wrong.

---

## 4. Scout report: wrong or unsupported

1. **Finding 4 and rows b1, b7: "count per pair is the number of crossings".** Wrong. It is about 8% of crossings (section 1.3). "D^1.6, not re-measured" is the signature of that.
2. **Shortlist 3: D 0.15 "small but near-certain", x1.5-1.9.** It is x1.94 and the largest allowed lever. The scout's point that `pv_arbor/README.md` wrongly calls it closed is correct (`bio_ranges.json` max 0.15, checked).
3. **Finding 6: persistence 35 um, "2.3x gap consistent with centroid pull".** Ignores a branch every 32 um. Free-walk straight/path is 0.28 in the toy, not the implied 0.32; conclusion unaffected.
4. **Shortlist 1: "spread around their own somata, roughly doubling reach".** Reach roughly right; "around their own somata" is not (section 2.4).
5. **T1a targets 14 [9-22], 20% chance of >= 20; T2 +3.7 targets.** Unsupported; both assume reach or target choice limits targets. Section 1.4 shows sampling does.
6. **Finding 3 (attractor mix 81% pyramidal, weak lever).** Correct, but for a further reason: target choice is not the limit.
7. **Finding 7 (no lateral boundary).** Supported and stronger than stated: pyramidal dendrite length reaches r 579 um (99%) and z +391; 61% of all dendrite length lies outside a box of +-300 um in x, y and +-80 um in z. Radius and thickness place somata only.
8. **Row b3 "likelihood saturated", b2 P_receptor 1.0.** Correct (report table read).
9. Confirmed on re-reading: finding 2 (unit-normalised 1/d^2, weight 0.9, no cutoff), row c5 (connection made at candidate time, line 430), the restated-chain rule (`:787-837`), and all of the scout's data numbers that I recomputed (6,561 points; 19/33/55 um; 46/64/107).

## 5. Limits of this analysis
- All DATA comes from one network (S1 seed 16180). The code line is identical in both trees and the D^1.6 from earlier runs fits, so I expect it to hold everywhere; the three D 0.15 runs test it.
- Acceptance numbers assume isotropic axon directions (measured mean cosine -0.006) and the measured segment lengths.
- The toy has no elongation budget, no dendrite growth in time, and fixed attractors.
- The radius factor (x1.2-1.4) is a guess.
- `bio_ranges.json`, the turning-model code and the NES wrapper were not re-read beyond the lines cited.
- Scratch scripts (not in the project, lost on cleanup): `/tmp/claude-1002/-home-johnjose-cos-netmorph-work-recipe-v2/ddb9d791-9fa9-4a28-9aa8-0a2955417a51/scratchpad/` (`cross.py`, `dens.py`, `bug.py`, `prep.py`, `toy.py`, `pen.py`).
