# repro_g PREREGISTRATION (2026-11-18; written after Step 1 (STEP1.md, no sims) and before any simulation; not edited after launch)
Question: why does the same seed with the same parameters sometimes give a different arbor? Test config: **V1n30, seed 31415, pyramidal D 0.0175, interneuron D 0.0495** (96 pyramidal + 30 interneurons, V1 recipe). It already has two arbor classes in the history: A = linefix_b run (finished 11-15 21:37; interneuron axon mean 46,234.6079, interneuron dendrite 6,681.5584, pyramidal dendrite 25,736.7841, pyramidal axon 21,022.7151; note that run used D 1.5/0.1, which does not change arbors) and B = linefix_c run (11-15 23:15; 47,349.0650 / 6,534.5135 / 25,871.1473 / 21,132.5274). Two arbor means "agree" if all four equal to 1e-6 relative.
## Hypotheses (ranked by my probability that it is the main cause of the V1 deviations)
- **H1 (about 35%): a data race on shared static state between concurrently growing NetMorph threads**, most visibly `static float x, y` in normal_pdf::nfix (global.cc:413). Needs >= 2 concurrent growths in one NES process. Predicts: sequential single-growth repeats are all identical; concurrent runs sometimes deviate; deviating concurrent runs usually differ from each other (each race event is a unique perturbation).
- **H2 (about 25%): state in the long-lived NES process that is not reset between runs** (for example the one-time normal_pdf tables or allocator-dependent behaviour, anything that varies with process history). Predicts: sequential repeats can differ from each other or drift with the number of earlier runs; a freshly restarted NES reproduces its own first-run class; deviation does not need concurrency.
- **H3 (about 15%): a rare discrete numerical event** (for example a floating-point comparison on a knife edge, specific to the V1 axon B_inf 20 recipe) that is itself nondeterministic across hardware threads or CPU state; predicts rare deviations at similar rates whether sequential or concurrent, and a small number of alternative classes (A/B recurring).
- **H4 (about 10%): something external to the model text that varies run to run (output directory uuid, wall-clock timestamp, memory addresses)**. Pointer-order of neurons is already excluded as sufficient (STEP1.md section 2, identical order with different arbors). Predicts: deviations unrelated to concurrency and to process age.
- **H5 (about 15%): other / not found by this experiment.**
H5 and H4 are the residual; D_synmax / build / model name are excluded by the data (V1 48 s16180 reproduced over five D settings and two builds).
## Experiment (V1n30 seed 31415, D 0.0175 / 0.0495; only the run label differs: output folder and model name get a suffix; the model file text is verified identical by md5; same driver and flags as linefix_c grow_pv_s2.py; patched NES 8011 / API 8010, freshly started for the experiment)
1. **SEQ**: 3 growths one after the other (a growth starts only after the previous finished and its resident simulation was deleted; nothing else running), same NES process: SEQ1, SEQ2, SEQ3.
2. **CON**: 3 growths launched at once in the same NES process (the same process as SEQ, 60 s apart is NOT used; all three within 5 s): CON1, CON2, CON3.
3. If all 6 agree to 1e-6 and equal the same class: restart NES/API and run **RST1** alone, then RST2 and RST3 concurrently; compare. Otherwise the restart step is run only if needed to separate H1 from H2 (decided by the table below).
Comparison: arbor means to 9 digits against each other and against A and B; for any deviating run also cell-by-cell by soma position.
## Predictions
| item | prediction | probability |
|---|---|---|
| P1 SEQ1, SEQ2, SEQ3 agree to 1e-6 | yes | 60% (H1, H3 lower, H2 and H4 imply disagreement or drift) |
| P2 SEQ class | = A 30%, = B 30%, a third arbor 40% | |
| P3 at least one of CON1-3 differs from the SEQ class | yes | 55% (H1 about 80%, H3 40%, H2 50%, H4 50%) |
| P4 if two CON runs deviate, they agree with each other | no (unique perturbations) under H1; yes under H3/H2 | 35% they agree |
| P5 all 6 runs identical (and then restart) | | 25% |
| P6 after a restart, RST1 equals SEQ class (given SEQ1-3 agree) | yes | 65% |
Decision rules for the verdict: **H1 supported** if SEQ1-3 agree and at least one CON run deviates (race, concurrency dependent); **H1 rejected** if a SEQ run deviates from another SEQ run (then H2/H3/H4: concurrency is not needed); **narrowed, not found** if all six agree (deviation rate under a single config is then below about 1 in 6 per run and cannot be provoked on demand). Cause "found" only if a deviation is provoked in the predicted condition and not in the control condition (3 SEQ vs 3 CON is a weak test: a single clean result moves a hypothesis by a factor of about 2, not more, and I will say so).
## Practice to recommend (provisional, to be updated by the result)
Compare the four arbor means to 9 digits before comparing any counts; grow a model once and reuse the grown model for every analysis that needs a fixed network; run growths needing reproducibility one at a time; keep the grown model and its viz dump with each result.
