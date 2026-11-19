# repro_g: why does the same seed with the same parameters sometimes give a different arbor? (2026-11-18)
**Verdict: narrowed, cause not found.** Arbors are not reproducible at node level in any case tested; what reproduces is only the length means, because lengths do not depend on direction. The run-to-run difference starts as a floating-point-sized perturbation (1e-6 um, the last printed digit) and is amplified chaotically by growth. Whether two runs agree depends on something tied to when they are launched (runs started in the same minute agree in 98.9-99.9% of nodes, runs started at other times agree in only about 70%); it does not depend on concurrency, on a NES restart, on D_synmax, on the build, or on neuron pointer order. The mechanism (which clock-dependent quantity) was not identified; reading the code gives candidates, not a proof.
Files: STEP1.md (Step 1, no sims: tables, source reading), PREREGISTRATION.md and PREREGISTRATION_addendum.md (written before the SEQ/CON stage and before the RST results were looked at, not edited), collect.py/runs.json, ptrorder.py, perneuron.py, grow_rep.py (copy of linefix_c/grow_pv_s2.py: REP env var adds a suffix to the output folder and model name only; diff checked, model text identical), run_exp.sh, run_rst.sh, analyze_rep.py -> rep_results.json, pairmat.py/agree.py/cellcmp.py (node-level comparison), grow_*_{SEQ,CON,RST}*/.
Patched instance only (NES 8011 / API 8010; main NES/API untouched, no NES code change, no git, no email). All 9 growths rc 0, walls 1,741-1,953 s, resident simulations deleted. No other growth ran on the instance during SEQ1-3 and RST1.

## 1. Step 1 (history, 57 runs; STEP1.md)
10 of 14 repeated groups reproduce on length means; the 4 that deviate are all V1 (axon B_inf 20; S1/V3: 0 of 8 groups). Class A/B pairs differ by 0.3-2.4% in the interneuron axon mean but in every cell (median per-cell difference 5-17%). No pattern with process, D_synmax, build, time of day, queue position, wall time or concurrency (no historic run grew alone); pointer order of neurons is neither necessary nor sufficient.

## 2. Experiment: V1n30 seed 31415, pyramidal D 0.0175, interneuron D 0.0495 (the config with two historical classes A = linefix_b and B = linefix_c)
| run | stage | launched | alone? | arbor means (class) | Pyr->Pyr@0.0175 | Pyr->Int | Int->Pyr | Int->Int |
|---|---|---|---|---|---|---|---|---|
| SEQ1 | sequential, first after NES start (pid 2102266) | 17:04:16 | yes | A | 5,793 | 4,589 | 11,916 | 3,120 |
| SEQ2 | sequential | 17:35:39 | yes | A | 5,824 | 4,666 | 11,994 | 3,139 |
| SEQ3 | sequential | 18:04:46 | yes | A | 5,911 | 4,591 | 11,893 | 3,152 |
| CON1 | concurrent (3 at once) | 18:33:49 | no | A | 5,959 | 4,620 | 11,898 | 3,110 |
| CON2 | concurrent | 18:33:52 | no | A | 5,952 | 4,617 | 11,890 | 3,105 |
| CON3 | concurrent | 18:33:55 | no | A | 5,959 | 4,616 | 11,894 | 3,109 |
| RST1 | first after NES restart (pid 2164826), alone | 19:06:44 | yes | A | 5,976 | 4,622 | 11,956 | 3,135 |
| RST2 | concurrent with RST3 | 19:39:19 | no | A | 5,829 | 4,660 | 11,995 | 3,138 |
| RST3 | concurrent with RST2 | 19:39:22 | no | A | 5,823 | 4,666 | 11,994 | 3,139 |
(arbor means = interneuron axon / interneuron dendrite / pyramidal dendrite / pyramidal axon: 46,234.6079 / 6,681.5584 / 25,736.7841 / 21,022.7151 in all nine, equal to the historical A run; class B (47,349.0650 ...) did not appear.)
Node-level agreement (fraction of the 1,198,886 nodes with identical position to 1e-3 um; node ids, soma positions and node counts identical in all nine):
| pair | agreement |
|---|---|
| SEQ1 vs SEQ2, SEQ1 vs SEQ3, SEQ2 vs SEQ3 | 0.700, 0.705, 0.711 |
| old linefix_b (A) vs each of the 9 | 0.702-0.710 |
| CON1 vs CON2 / CON2 vs CON3 / CON1 vs CON3 | 0.989 / 0.994 / 0.989 |
| RST2 vs RST3 | 0.999 |
| RST1 vs SEQ1 (both first run in a fresh process, alone) | 0.701 |
| SEQ, CON, RST1 vs RST2, RST3 (any pair across launch times) | 0.700-0.711 |
Every run launched in a different minute from every other agrees with it in about 70% of nodes. The two groups that agree (CON1-3, launched 18:33:49-55; RST2-3, launched 19:39:19-22) share the same minute stamp in their output file names (202611181833, 202611181939). Neuron pointer order (report tables) is identical in 8 of the 9 runs, including pairs that agree in only 70% of nodes, so it is not the determinant. First differing node of each pair differs by 1e-6 um (the print resolution), growing to 60-125 um downstream; synapse counts therefore differ by 1-3% between runs with identical length means (Pyr->Pyr 5,793-5,976, Int->Pyr 11,890-11,995).

## 3. Scoring
Preregistered predictions P1-P6 (scored on length means, the observable then used):
| item | prediction | outcome |
|---|---|---|
| P1 SEQ1-3 agree to 1e-6 | yes 60% | HIT (all class A) |
| P2 SEQ class = A 30% / B 30% / new 40% | | = A (the 30% option) |
| P3 at least one of CON1-3 differs from the SEQ class | yes 55% | MISS (all class A) |
| P4 deviating CON runs agree with each other | n/a | not testable (none deviated) |
| P5 all six runs identical on length means | 25% | HIT, so the restart stage was run as the rules say |
| P6 RST1 equals the SEQ class | yes 65% | HIT (class A), but see node level |
Hypothesis scoring by the addendum rules (RST1 vs SEQ1 = 0.701 < 0.9, RST2 vs RST3 = 0.999 > 0.95): **HB (launch-time dependence) supported**; HA (heap/pointer-order dependent summation, predicted RST1 vs SEQ1 > 0.99) rejected in the tested form; HC (thread race, predicted no mutual agreement of concurrent runs) disfavoured by CON1-3 and RST2-3; HD (other) remains. H1 of the first preregistration (data race on static state in nfix, concurrency needed) is not supported: sequential runs differ from each other (70%) and concurrent runs launched together agree (99%), the opposite of a race. Evidence strength: one fresh-process comparison and two time-adjacent groups; agreement tracks the launch minute in both, but minute versus second resolution, or another quantity that is merely correlated with launch time, cannot be separated by these data.
What this explains in the history: the V1 class A/B differences are the length-visible tip of an effect present in every pair of runs; V1 is more sensitive in lengths (4 of 6 groups deviate, S1/V3 0 of 8; not tested why). The 1-2% "run-to-run noise at fixed arbors" in synapse counts (linefix_c Stage 1) has the same origin.
## 4. Can exact thresholding predictions be trusted?
Yes for what they are: thresholding the stored pre-post distances of ONE grown model is exact for that model (same synapse list). No across regrowths: even with identical length means, a regrown model has about 30% different node positions, synapse counts 1-3% different (Pyr->Pyr spread 3% over these nine runs), and a different pair structure (which cells receive no input, which pairs carry >= 5 synapses, which memories fit). So "arbors identical to 9 digits, counts within 2%" holds only as a statement about totals, and tolerances tighter than +-3% on counts, or any claim about specific cells or pairs after a regrowth, are not supportable. Capacity packings, memory groups and recall results (capacity_d, recall_e) apply to the specific grown model they were computed on.
## 5. Recommended practice
1. Compare node-level positions (or at least synapse counts), not only length means, before treating two growths as the same network; length means can agree to 9 digits while 30% of the geometry differs.
2. Grow each network once and reuse the grown model and its viz dump for every analysis (thresholding, packing, recall); keep the model name, output uuid and NES process with the result. Never regrow and expect the same pairs.
3. Running growths one at a time, restarting NES, or holding D_synmax/build fixed does not give reproducibility (SEQ, RST and CON all differ in geometry); starting several growths within a few seconds of each other gave near-identical geometry here (98.9-99.9%), a convenience for same-network replicates (for instance different D_synmax applied to one growth set), but not a guarantee.
4. For comparisons of configurations use several seeds and quote the seed spread, since a regrown seed is a new realisation at the 1-3% level in counts and more for per-cell quantities.
5. Suggestions for Randal (not tested, no code changes made): (a) check what is drawn from the time(NULL)-seeded streams (global.hh:702 constructor) before set_random_seed at common_entry.cc:450, and whether anything keeps its value; (b) the pointer-keyed std::set<neuron*> / std::set<fibre_segment*> summation (axon_direction_model.cc:660/682); (c) the function-static `x, y` in normal_pdf::nfix (global.cc:413). These are candidates from reading only; the RST/CON results do not support (b) for neurons or (c) as the dominant cause.
## 6. Honest limits
- One configuration (V1n30 seed 31415), nine growths, one launch day. The "same minute agrees" observation rests on two groups; a clean test would launch pairs 1 s, 30 s, 70 s, 10 min apart in a fresh process (about 8 growths, 4 h at 3 concurrent) and, ideally, pin the clock-dependent quantity by a code change, which was out of scope.
- Class B never reappeared, so the original linefix_c result (47,349) could not be re-provoked; length-visible deviations are rare (0 of 9 here).
- Node ids are compared as given; the agreement fraction assumes node ids are stable between runs (they are: counts, parent indices (99.9%) and soma positions agree).
- The addendum hypotheses were written after the SEQ/CON data showed the node-level effect; the RST stage is the only genuinely prospective test of them (one fresh-process pair).
