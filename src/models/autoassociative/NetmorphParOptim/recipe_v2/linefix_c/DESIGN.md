# linefix_c: Pyr->Pyr density under the line-379 fix, D_synmax sweep, and preregistered run design
Written 2026-11-15, before any linefix_c run. Analysis only: existing finished runs, no sims, no NES/API touched. Ledger task tmwidgz0z.
Scripts and data here: `pairs.py` -> `pairs_results.json`, `pairs.log`; `sweep.py` -> `sweep_results.json`, `sweep.log`.
Tags: MEASURED (from run files), EXACT-BY-THRESHOLD (see 2.1), MODEL (fitted extrapolation), MEMORY (my recollection of literature, not verified here), LIT (lit_review/LIT_REVIEW.md).

## Summary
1. John's averages are right: Pyr->Pyr is 7.8-9.5 synapses per ordered pair unpatched and 38-46 patched.
2. Connection probability is 0.68-0.72 unpatched and 0.84-0.88 patched. Synapses per connected pair: mean 11-14 (median 6-7) unpatched, mean 44-55 (median 21-23) patched.
3. This is a real mismatch with biology (0.1-0.3 and 1.9-4.5), and its cause is geometric: connection probability does not fall with soma distance, and 5 of 96 cells receive 30% of all Pyr->Pyr synapses.
4. Lowering pyramidal D_synmax stays inside bio_ranges.json and scales the count linearly.
5. Pyramidal D 0.03-0.075 gives 2-4 synapses per connected pair, but connection probability is then 0.35-0.54.
6. Connection probability 0.1-0.3 needs D 0.005-0.02, where pairs have 1.2-2.1 synapses. Only D about 0.02 touches both bands, at their edges.
7. Any such D sends the inhibitory fraction A far above 3-6% (to 40-80%). A is set by the ratio of the two D values and by the axon lengths, not by anything biological in this patch.
8. The 3-6% band is not sourced in LIT_REVIEW, and it cannot hold together with biological per-pair numbers in a closed 96+48 patch. I propose to drop it as a bar and report A only.
9. One value, D 0.05 for all four pair types, gives biological synapses per connected pair in all pathways at once (Pyr->Pyr 3.0-3.5, Int->Pyr 5.2-7.9, Pyr->Int 2.8-3.8) and 25-30 drivable interneurons.
10. Design (revision 2, John chose connection probability first): V1 seed 16180 at pyramidal D 0.021, 0.01 and 0.05, interneuron D 0.05; then S1/V3 and two more seeds. See section 3; the earlier design is section 4.

## 1. Pyr->Pyr as it is now (seed 16180; AMPA rows of the .synapses files; 96 cells, 9120 ordered pairs)
MEASURED.

| run | synapses | per ordered pair (all) | connected pairs | connection prob. | syn per connected pair mean / median / 90th pct | pairs with 1 synapse | reciprocal share |
|---|---|---|---|---|---|---|---|
| S1 unpatched | 73,105 | 8.0 | 6,526 | 0.716 | 11.2 / 6 / 27 | 16% | 0.71 |
| V1 unpatched | 70,921 | 7.8 | 6,384 | 0.700 | 11.1 / 6 / 28 | 17% | 0.70 |
| V3 unpatched | 86,230 | 9.5 | 6,207 | 0.681 | 13.9 / 7 / 36 | 16% | 0.67 |
| S1 patched | 365,853 | 40.1 | 7,990 | 0.876 | 45.8 / 23 / 115 | 7% | 0.88 |
| V1 patched | 348,125 | 38.2 | 7,868 | 0.863 | 44.3 / 21 / 109 | 7% | 0.86 |
| V3 patched | 421,278 | 46.2 | 7,671 | 0.841 | 54.9 / 22 / 148 | 8% | 0.84 |

Per cell (patched; unpatched in brackets): out mean 3,626-4,388 (739-898), out range 756-8,022; in mean equal to out mean, in median 1,513-1,905, in range 1 to 38,215. The five most-innervated cells receive 29-31% of all Pyr->Pyr synapses, in both builds and at every D.

Connection probability by soma distance (patched S1; V1 and V3 alike): 0-50 um 0.92, 50-100 um 0.91, 100-150 um 0.88, 150-250 um 0.81. Unpatched S1: 0.76, 0.76, 0.72, 0.63.

So: the averages in the task (about 8 and about 40 per pair) are correct. Against biology (LIT: 2.5-4.5 synapses per connected pair, probability 0.3 in the published NetMorph network and 0.01-0.09 in Holmgren as quoted there) the unpatched network was already too dense by about 3x in synapses per connected pair and 2.5-7x in connection probability; the fix makes it about 12x and 3-9x.

Artefact or real? Both, in this sense:
- It is a property of this geometry, not of the synapse test. Every pyramidal cell keeps its whole 19-20k um axon and 24-25k um dendrite inside one small volume, and the axons collapse to the disc centre (step0 audit). So every pair overlaps wherever the somata are: probability is flat with distance, where tissue shows a clear fall-off. The huge in-degree skew (a few cells near the collapse point take a third of the input) has the same cause.
- It is also a real mismatch for the functional model: the network that is simulated has these synapses. Fixing the test does not create the problem; it removes a direction filter that was hiding 80% of it.
- The patched count is the honest geometric one (within 8-9% of the plain crossing formula, linefix/README section 3). At D 1.5 it says that a pyramidal pair has on average 40 places where axon and dendrite pass within 1.5 um. In tissue only a fraction of such appositions are synapses (filling fraction; about 0.1-0.3, MEMORY: Stepanyants et al. 2002). NetMorph's D_synmax is the only knob we have for that fraction.

## 2. D_synmax sweep under the fix
### 2.1 Method
The .synapses file stores the two contact points of each synapse. In the patched runs their distance is uniform from 0 to D (Pyr->Pyr counts per 0.1 um bin, V1: 23,945, 23,938, 23,948 ... 22,056; maximum 1.5000; interneuron pairs maximum 0.1000). Arbors do not depend on the synapse test (lengths identical across all D and patch changes so far). So keeping only the synapses with distance <= D' gives exactly the network the patched build would grow at D_synmax = D'. This is not a model; the only risks are the occasional same-seed realisation drift (1 of 9 earlier runs) and any rule I have not seen that acts after the distance test. The 8-cell drivable count computed from thresholded counts x 0.98 nS reproduces the viz-dump value at D 0.1 in all three runs (33, 31, 39).
For D above the run value (interneuron pairs at 0.15) counts scale linearly (x1.5; checked: 0.05 -> 0.1 gives x1.99-2.01). Pair statistics there are MODEL: a negative-binomial fit; fitted at 0.05 it predicts the 0.1 values within 0.02 in probability and 0.2 in synapses per pair.

### 2.2 Pyr->Pyr versus pyramidal D (EXACT-BY-THRESHOLD; S1 / V1 / V3)
| D pyr-pyr | synapses | connection prob. | syn per connected pair, mean | median | in-degree median | cells with zero Pyr input |
|---|---|---|---|---|---|---|
| 1.5 | 366k / 348k / 421k | 0.88 / 0.86 / 0.84 | 45.8 / 44.3 / 54.9 | 23 / 21 / 22 | 1,905 / 1,513 / 1,622 | 0 / 0 / 0 |
| 0.5 | 125k / 119k / 144k | 0.79 / 0.77 / 0.75 | 17.4 / 17.0 / 21.2 | 9 / 9 / 10 | 627 / 481 / 555 | 1 / 1 / 0 |
| 0.3 | 75.6k / 71.8k / 86.9k | 0.74 / 0.71 / 0.69 | 11.3 / 11.0 / 13.8 | 6 / 6 / 7 | 364 / 285 / 340 | 1 / 1 / 2 |
| 0.15 | 38.1k / 35.8k / 43.7k | 0.65 / 0.62 / 0.61 | 6.4 / 6.3 / 7.9 | 4 / 4 / 4 | 187 / 139 / 164 | 2 / 3 / 3 |
| 0.1 | 25.4k / 23.9k / 29.2k | 0.59 / 0.56 / 0.55 | 4.8 / 4.7 / 5.8 | 3 / 3 / 3 | 125 / 92 / 112 | 2 / 3 / 4 |
| 0.075 | 19.0k / 17.9k / 21.9k | 0.54 / 0.51 / 0.51 | 3.9 / 3.9 / 4.7 | 2 / 2 / 3 | 90 / 70 / 87 | 2 / 3 / 4 |
| 0.05 | 12.6k / 11.9k / 14.5k | 0.46 / 0.44 / 0.45 | 3.0 / 3.0 / 3.5 | 2 / 2 / 2 | 62 / 48 / 53 | 3 / 4 / 5 |
| 0.03 | 7.6k / 7.1k / 8.7k | 0.37 / 0.35 / 0.37 | 2.3 / 2.3 / 2.6 | 2 / 2 / 2 | 38 / 27 / 32 | 4 / 9 / 6 |
| 0.02 | 5.1k / 4.8k / 5.8k | 0.30 / 0.28 / 0.30 | 1.9 / 1.9 / 2.1 | 1 / 1 / 1 | 23 / 19 / 21 | 5 / 12 / 10 |
| 0.01 | 2.5k / 2.4k / 2.9k | 0.19 / 0.18 / 0.20 | 1.5 / 1.5 / 1.6 | 1 / 1 / 1 | 12 / 10 / 10 | 9 / 17 / 18 |
| 0.005 | 1.3k / 1.2k / 1.5k | 0.11 / 0.11 / 0.13 | 1.2 / 1.2 / 1.3 | 1 / 1 / 1 | 6 / 5 / 6 | 19 / 25 / 26 |

Answers:
- 2-4 synapses per connected pair: D 0.03 to 0.075. Connection probability there is 0.35-0.54, above 0.1-0.3.
- Connection probability 0.1-0.3: D 0.005 to 0.02. Synapses per connected pair there are 1.2-2.1.
- Both at once: only at D about 0.02 (probability 0.28-0.30, 1.9-2.1 per pair), at the edge of each band.
- Why no D gives both comfortably: pairs differ enormously in overlap (mean far above median), so thinning removes the weak pairs slowly while the strong pairs keep many synapses. That spread is the collapse geometry again. It is not something D can repair.
- A D of 0.02-0.05 um is not a physical reach for spiny pairs (the limit note says spines bridge up to 1.5 um). It should be read as "1.5 um reach times a filling fraction of 1.3-3.3%". Biological filling fractions are higher (MEMORY: 0.1-0.3), which corresponds to D 0.15-0.45 and 6-15 synapses per pair here. The difference is the excess overlap from the geometry, about 3-5x.

### 2.3 Interneuron pairs under the fix
EXACT-BY-THRESHOLD for 0.1 and below; MODEL for 0.15. Cells: S1 / V1 / V3. "p" is connection probability, "spc" synapses per connected pair.

| D int pairs | Int->Pyr synapses | Int->Pyr p | Int->Pyr spc | Pyr->Int spc | Pyr->Int p | Int->Int spc | targets per interneuron (of 96) | drivable 8-cell (of 48) |
|---|---|---|---|---|---|---|---|---|
| 0.15 (model) | 76.5k / 42.7k / 60.7k | 0.82 / 0.74 / 0.73 | 20.3 / 12.6 / 18.0 | 6.0 / 8.8 / 8.4 | 0.62 / 0.59 / 0.69 | 18.8 / 17.7 / 19.6 | 78 / 71 / 70 | not computed (at least the 0.1 value) |
| 0.1 | 51.0k / 28.5k / 40.4k | 0.78 / 0.69 / 0.69 | 14.2 / 9.0 / 12.7 | 4.4 / 6.4 / 6.1 | 0.55 / 0.54 / 0.63 | 13.2 / 12.6 / 13.7 | 75 / 66 / 66 | 33 / 31 / 39 |
| 0.075 | 38.1k / 21.5k / 30.4k | 0.74 / 0.65 / 0.66 | 11.1 / 7.2 / 10.1 | 3.7 / 5.1 / 4.9 | 0.51 / 0.51 / 0.58 | 10.2 / 9.9 / 10.6 | 71 / 63 / 63 | 30 / 28 / 35 |
| 0.05 | 25.4k / 14.3k / 20.2k | 0.70 / 0.60 / 0.61 | 7.9 / 5.2 / 7.2 | 2.8 / 3.8 / 3.7 | 0.44 / 0.46 / 0.51 | 7.3 / 7.1 / 7.6 | 67 / 57 / 58 | 25 / 26 / 30 |
| 0.03 | 15.3k / 8.5k / 12.1k | 0.63 / 0.51 / 0.54 | 5.3 / 3.6 / 4.9 | 2.1 / 2.7 / 2.7 | 0.35 / 0.39 / 0.43 | 5.0 / 4.8 / 5.2 | 60 / 49 / 51 | 23 / 23 / 25 |

Against LIT: PV to pyramidal 4.0-8.7 boutons per pair verified (the earlier "about 11" is at the high end); pyramidal to fast-spiking interneuron about 3. With the fix, 0.15 is too much for every variant, 0.1 fits only V1 for Int->Pyr and is high for Pyr->Int, and 0.05 puts all three variants inside both ranges. Drivable stays above 16 down to D 0.03.

### 2.4 Inhibitory fraction A = Int->Pyr / (Int->Pyr + Pyr->Pyr)
EXACT-BY-THRESHOLD. Rows: interneuron D. Columns: pyramidal D. Cells: S1 / V1 / V3, in %.

| int D \ pyr D | 1.5 | 0.5 | 0.3 | 0.15 | 0.1 | 0.05 |
|---|---|---|---|---|---|---|
| 0.1 | 12 / 7.6 / 8.8 | 29 / 19 / 22 | 40 / 28 / 32 | 57 / 44 / 48 | 67 / 54 / 58 | 80 / 71 / 74 |
| 0.075 | 9.4 / 5.8 / 6.7 | 23 / 15 / 17 | 34 / 23 / 26 | 50 / 38 / 41 | 60 / 47 / 51 | 75 / 64 / 68 |
| 0.05 | 6.5 / 4.0 / 4.6 | 17 / 11 / 12 | 25 / 17 / 19 | 40 / 29 / 32 | 50 / 38 / 41 | 67 / 55 / 58 |
| 0.03 | 4.0 / 2.4 / 2.8 | 11 / 6.7 / 7.8 | 17 / 11 / 12 | 29 / 19 / 22 | 38 / 26 / 29 | 55 / 42 / 46 |

- Under the fix A is a function of the ratio r = D_int / D_pyr only: A = K r / (1 + K r), with K = 2.09 (S1), 1.23 (V1), 1.44 (V3). K is the ratio of geometric overlaps; it is above 1 because the 48 interneurons carry more axon in total (2.2-3.6 million um) than the 96 pyramidal cells (1.8-1.9 million um).
- A in 3-6% needs r of 0.015-0.03 (S1), 0.025-0.05 (V1), 0.02-0.045 (V3). With pyramidal D at 1.5 that is interneuron D 0.03-0.075. With pyramidal D at 0.05 it would need interneuron D near 0.002, which leaves about 0.1 Int->Pyr synapse per pair. So "biological Pyr->Pyr per pair" and "A in 3-6%" exclude each other here.
- Is the band well sourced? No. LIT_REVIEW does not source 3-6% at all, and marks 10-20% as not confirmed (one snippet: 11% GABA-positive targets, cat V1). MEMORY (unverified): whole-cell counts for a CA1 pyramidal cell are about 1,700 inhibitory of about 32,000 synapses, roughly 5%, which may be where 3-6% came from. Such figures count every input to the cell, most of them excitatory afferents from outside any 96-cell neighbourhood. A closed patch has only the local recurrent excitation.
- Check with biology's own per-pair numbers in a 96+48 patch: excitatory input per pyramidal cell = 95 x 0.2 x 3 = about 57 synapses; inhibitory = 48 x 0.6 x 5 = about 145 (0.6 is the model's value; LIT found no biological PV-to-pyramidal probability). That is A of about 70%. So the per-pair targets themselves imply a high A in this patch; 3-6% is a whole-brain census number and is the wrong yardstick for a closed local circuit.
- Proposal: drop A as a pass/fail bar. Keep reporting it. Judge inhibition by per-pair statistics and by the drivable count, and settle the excitation/inhibition balance in the functional model (weights), where it belongs.

## 3. Preregistered run design, revision 2 (2026-11-15): John chose ranking B
Ranking B: Pyr->Pyr connection probability (0.1-0.3) comes first, synapses per connected pair (1.9-4.5) second. So low-pyramidal-D settings are the candidates. The earlier design (ranking A, synapses per pair first, C1 as favourite) is kept unchanged at the end of this file as section 4.
Reminder: a pyramidal D of 0.01-0.05 um is not a physical reach. Read it as the 1.5 um spine reach times a filling fraction of about 1-3% (0.021 / 1.5 = 1.4%, 0.01 / 1.5 = 0.7%, 0.05 / 1.5 = 3.3%).

### 3.1 Setup common to all runs
Patched build (`/home/johnjose/BrainGenix/wt/nes-linefix`), API port 8010, own output folder. Driver `grow_pv.py` here: copy of `linefix/grow_pv.py` with pyramidal D and interneuron D as arguments, run tag `_p<pyrD>_i<intD>`, model name `v2-lfc-`. Everything else as before: 96 pyramidal, 48 interneurons, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9. Max 3 concurrent sims in total across all workers; launch only after the linefix_b queue has finished. Analysis: `analyze_pv.py` (viz dump; copy of the linefix one, run lookup also matches pyramidal D) and `stage1.py` (pair statistics from the .synapses file, same code as `pairs.py`). Pre-flight per run: `.nibr.clp` read-back of the four D values, bio_check pass.

### 3.2 Why these three settings (V1, seed 16180; exact by thresholding, finer steps in this revision)
| pyramidal D | V1 prob. / per pair | S1 prob. / per pair | V3 prob. / per pair |
|---|---|---|---|
| 0.01 | 0.184 / 1.45 | 0.191 / 1.46 | 0.204 / 1.56 |
| 0.015 | 0.239 / 1.67 | 0.250 / 1.68 | 0.261 / 1.84 |
| 0.0175 | 0.261 / 1.77 | 0.275 / 1.78 | 0.284 / 1.96 |
| 0.02 | 0.281 / 1.87 | 0.297 / 1.88 | 0.304 / 2.09 |
| 0.021 | 0.289 / 1.91 | 0.306 / 1.92 | 0.311 / 2.15 |
| 0.0225 | 0.299 / 1.96 | 0.318 / 1.97 | 0.322 / 2.23 |
| 0.025 | 0.317 / 2.05 | 0.335 / 2.08 | 0.339 / 2.35 |
| 0.05 | 0.441 / 2.97 | 0.460 / 3.01 | 0.452 / 3.51 |

- V1 meets both bands only for D 0.021-0.0225. V3 meets both for about 0.0165-0.0195. S1 misses by a hair at every D (probability reaches 0.30 at D 0.0205, where pairs have 1.90).
- These windows are narrower than the difference between variants, and certainly narrower than seed-to-seed spread. So "both bands" is a knife edge here, not a robust operating point; under ranking B the robust statement is "probability inside 0.1-0.3, synapses per pair at or just below the lower edge".
- Primary D 0.021 (not 0.02): it is the smallest value at which V1 is predicted to meet both bars (0.289 and 1.91); at 0.02 V1 would miss the second bar by 0.03.
- Interneuron D 0.05 for all three runs: Int->Pyr 5.21 and Pyr->Int 3.77 per connected pair in V1 (bands 4-9 and 1.5-4.5); it also keeps S1 and V3 inside both bands (7.9 / 2.8 and 7.2 / 3.7). Using one value in all three runs keeps the comparison to a single changed parameter.

### 3.3 Stage 1: V1, seed 16180, one batch of 3
| run | pyramidal D | interneuron D | role |
|---|---|---|---|
| B1 | 0.021 | 0.05 | primary: probability in band, per pair at the lower edge |
| B2 | 0.01 | 0.05 | well inside the probability band; per pair expected below 1.9 |
| B3 (= old C1) | 0.05 | 0.05 | contrast: per pair in band, probability above band |

Predictions (exact by thresholding of the existing patched V1 run):
| run | Pyr->Pyr syn | Pyr->Pyr prob. | Pyr->Pyr per connected pair | pyramidal cells with no Pyr input | inhibitory fraction A (reported, not a bar) |
|---|---|---|---|---|---|
| B1 | 5,021 | 0.289 | 1.91 | 11 | 74.1% |
| B2 | 2,425 | 0.184 | 1.45 | 17 | 85.5% |
| B3 | 11,942 | 0.441 | 2.97 | 4 | 54.6% |

Same in all three runs (interneuron D 0.05): Int->Pyr 14,345 synapses, probability 0.60, 5.21 per connected pair, 57.4 targets per interneuron; Pyr->Int 7,960, probability 0.46, 3.77 per pair; Int->Int 9,121, 7.09 per pair; drivable 8-cell 26 of 48 (simple 32); interneurons with no pyramidal input 6.
Arbors: identical to the existing patched V1 seed-16180 run (interneuron axon 45,207 um, dendrite 6,734 um; ratio 1.000).
Tolerances: counts +-2%, probabilities +-0.01, synapses per pair +-0.05, drivable +-1, zero-input counts +-1. If the arbor lengths differ (same-seed drift, seen in 1 of 9 earlier runs) the run is a new realisation and only the wide ranges of 3.4 apply to it. A miss with identical arbors means the thresholding method is wrong somewhere, and Stage 2 predictions are void until that is understood.

### 3.4 Stage 2 (after Stage 1 is scored)
- Setting: B1 unless Stage 1 says otherwise. Runs: S1 and V3 at seed 16180, then V1, S1, V3 at seeds 31415 and 27182 (8 runs, 3 at a time).
- Seed 16180 predictions at pyramidal 0.021 / interneuron 0.05: S1 Pyr->Pyr 5,350, probability 0.306, 1.92 per pair, Int->Pyr 25,414 (7.86 per pair), Pyr->Int 5,721 (2.82), drivable 25, A 82.6%. V3 Pyr->Pyr 6,114, probability 0.311, 2.15 per pair, Int->Pyr 20,202 (7.24), Pyr->Int 8,672 (3.69), drivable 30, A 76.8%. So S1 and V3 are predicted to sit just above 0.30; if John wants all three variants inside the band, 0.0175 is the value (0.26-0.28; per pair 1.77-1.96).
- Other seeds are new realisations (my judgement, about +-15% on counts): probability 0.25-0.34, per pair 1.7-2.4, Int->Pyr per pair 4.5-9.0, Pyr->Int per pair 2.4-4.4, drivable 20-34 with every run at least 16.

### 3.5 Success bar under ranking B (per run)
In order of priority:
1. Pyr->Pyr connection probability 0.1-0.3.
2. Pyr->Pyr synapses per connected pair, mean, 1.9-4.5.
3. Int->Pyr synapses per connected pair, mean, 4-9.
4. Pyr->Int synapses per connected pair, mean, 1.5-4.5.
5. Drivable interneurons, 8-cell criterion, at least 16 of 48.
6. No parameter outside bio_ranges.json.
Reported, not gated: inhibitory fraction A (section 2.4), pyramidal cells with no pyramidal input, in-degree skew.
Expected: B1 passes 1-6, bars 1 and 2 each by about 0.01; B2 passes 1 and 3-6, fails 2 (1.45); B3 fails 1 (0.44), passes 2-6.

### 3.6 What these runs cannot settle
- Whether the functional model (recall, ripples) works with about 5k Pyr->Pyr synapses (unpatched: 71k) and 11 of 96 pyramidal cells without any pyramidal input. That needs dynamics and probably new weights.
- The geometry: flat connection probability with distance and the in-degree skew stay at every D. Only a change to arbor growth can address them.
- The fix has not yet been reviewed by Randal Koene; a D this small is an effective filling fraction and should be agreed with him.

## 4. SUPERSEDED: earlier design under ranking A (synapses per pair first), kept for the record
### 4.1 Setup common to all runs
Patched build (`/home/johnjose/BrainGenix/wt/nes-linefix`, restart commands in linefix/README section 2), API port 8010, own output folder. Driver: copy of `linefix/grow_pv.py` with the four D_synmax values as arguments, run tag `_c<setting>`, model name `v2-lfc-`. Everything else as before: 96 pyramidal, 48 interneurons, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9. Max 3 concurrent sims in total across all workers. Analysis: `linefix/analyze_pv.py` plus `pairs.py` (paths changed only). Pre-flight per run: `.nibr.clp` read-back of the four D values, bio_check pass.

### 4.2 Stage 1: V1, seed 16180, three settings (one batch of 3)
| run | D pyr-pyr | D int pairs | purpose |
|---|---|---|---|
| C1 | 0.05 | 0.05 | one D for all pairs; per-pair biology in every pathway |
| C2 | 0.02 | 0.05 | the only pyramidal D that also reaches connection probability 0.3 |
| C3 | 0.3 | 0.1 | "20% filling fraction" reading; keeps strong recurrent excitation for the functional model |

Predictions, V1 seed 16180 (EXACT-BY-THRESHOLD, so tolerance +-2% on counts, +-0.02 on probabilities, +-0.1 on synapses per pair, +-1 on drivable; arbors identical to the existing patched V1 run: lengths ratio 1.000):

| run | Pyr->Pyr syn | Pyr->Pyr p | Pyr->Pyr spc | Int->Pyr syn | Int->Pyr spc | Pyr->Int syn | Pyr->Int spc | Int->Int syn | drivable 8-cell | A |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 | 11,942 | 0.44 | 2.97 | 14,345 | 5.21 | 7,960 | 3.77 | 9,121 | 26 | 54.6% |
| C2 | 4,785 | 0.28 | 1.87 | 14,345 | 5.21 | 7,960 | 3.77 | 9,121 | 26 | 75.0% |
| C3 | 71,831 | 0.71 | 11.04 | 28,484 | 8.95 | 15,974 | 6.41 | 18,329 | 31 | 28.4% |

If a run misses these tolerances, the thresholding method is wrong somewhere (a rule after the distance test, or realisation drift: check arbor lengths first) and the Stage 2 predictions are void until understood.

### 4.3 Stage 2
- Take the Stage 1 setting that passes the most bars in 3.4 (my expectation: C1; C2 only if connection probability is ranked above synapses per pair) and run S1 and V3 at seed 16180, then V1, S1, V3 at seeds 31415 and 27182 (8 runs, 3 at a time).
- Predictions at seed 16180 for setting C1: S1 Pyr->Pyr 12,632 (p 0.46, spc 3.01), Int->Pyr 25,414 (spc 7.86), Pyr->Int 5,721 (spc 2.82), Int->Int 11,149, drivable 25, A 66.8%. V3 Pyr->Pyr 14,455 (p 0.45, spc 3.51), Int->Pyr 20,202 (spc 7.24), Pyr->Int 8,672 (spc 3.69), Int->Int 12,037, drivable 30, A 58.3%. Same tolerances.
- Other seeds are new realisations, so only ranges (my judgement from the seed spread seen so far, about +-15% on counts): Pyr->Pyr spc 2.6-4.0, Pyr->Pyr p 0.40-0.50, Int->Pyr spc 4.5-9.0, Pyr->Int spc 2.4-4.4, drivable 20-34 with every run at least 16.

### 4.4 Success bar, rewritten from biology
Primary (all must hold, per run):
1. Pyr->Pyr synapses per connected pair, mean: 1.9-4.5 (LIT, verified values 2.5-4.5; lower edge from the task).
2. Int->Pyr synapses per connected pair, mean: 4-9 (LIT, verified 4.0-8.7).
3. Pyr->Int synapses per connected pair, mean: 1.5-4.5 (LIT, about 3; abstract-level source).
4. Drivable interneurons, 8-cell criterion: at least 16 of 48.
5. No parameter outside bio_ranges.json; arbor lengths unchanged from the 16180 baselines for the 16180 runs.

Secondary (reported, with the expected outcome stated now):
6. Pyr->Pyr connection probability 0.1-0.3. Expected: missed by C1 (0.44) and C3 (0.71), met at the edge by C2 (0.28). A miss here is attributed to arbor geometry, not to D.
7. Inhibitory fraction A: no bar (section 2.4). Reported for every run.
8. Pyramidal cells with no pyramidal input: reported (expected 4 for C1, 12 for C2, 1 for C3 in V1).

Expected result against the primary bar: C1 passes 1-5 in V1 and, by thresholding, in S1 and V3 at seed 16180. C2 fails bar 1 narrowly in V1 (1.87). C3 fails bar 1 (11.0) and passes 2 only at the top (8.95).

### 4.5 What these runs cannot settle
- Whether the functional model (recall, ripples) works with 12k instead of 71k (unpatched) Pyr->Pyr synapses. That needs dynamics and probably new weights; it is the next step after a setting passes.
- The geometry itself: flat connection probability with distance and the in-degree skew stay at every D. Only a change to arbor growth (the attraction model) can address them.
- The fix has not yet been reviewed by Randal Koene; D values this small are an "effective filling fraction" and should be agreed with him.
