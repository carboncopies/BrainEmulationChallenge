# Netmorph configuration-space and weight-space programming: write-up

Status: prototype. Written 2026-11-10, updated 2026-11-11 with Phase E. All results are from the shared NES server, one seed unless stated, and have not been peer reviewed.

## 1. Problem

Instead of finding a network's weights and growth parameters by trial-and-error optimisation, study the underlying model and edit it directly (configuration-space and weight-space programming). Goal (John, 2026-11-08): grow networks with Netmorph, following the structures in the Challenges Atlas, that have enough synapses on the relevant pathways to implement a desired behaviour, without violating biological realism.

Concrete tasks:
1. Extend Marianna Gabrielyan's Pyr-Pyr prediction model (random forest plus DiCE counterfactuals) to Pyr-Int, Int-Pyr and Int-Int connections, and check its suggestions with real Netmorph growth.
2. Prototype weight-space programming (engram storage, tune/prune) on a grown reservoir.
3. Look beyond weights: find other Netmorph knobs that fix the weak spots, and test whether the relationships between parameters can be found by reasoning.

Constraint: parameters never leave the hard biological limits in `bio_ranges.json` (days 20-25, In.pyramidal 16-128, In.interneuron 16-128, minneuronseparation 10-15 um, shape.radius 100-200, shape.thickness 20-50, dm_weight 0.1-1.0; growth_F and growth_nu0 constant). `bio_check.py` asserts them before each run.

## 2. Inspiration and related work

- Takehi, Teoh, Zhang, Khattab (MIT CSAIL), "Sparks of Weight-Space Programming: LLMs can natively read & write neural network weights", blog post, 2026-11-02, https://rikiyat.github.io/blog/weight-space-programming/ . A very early, non-peer-reviewed blog post. Fetched through a summarising tool on 2026-11-05: re-open it and check wording before quoting. We use the idea (set weights from reasoning about the model, no gradient descent). We do not reproduce its numbers, and our networks are spiking NES neurons, not its tanh MLPs.
- Varun Sinha, xor_scnm optimization (Dec 2025): Bayesian optimisation and grid search over Netmorph growth parameters, `src/models/xor_scnm/optimization/README.md`. This is the optimisation route the present work contrasts with.
- Pong and double-pendulum weight-space work: branches `feature/pong-netmorph` (draft MR !41) and `feature/double-pendulum`. Not part of this branch.
- Internal documents: "Netmorph auto-configuration ML optimization", "Building Synthetic Ground-Truth Examples", "Tuning and Pruning", "Building an Autoassociative Memory Example", "Deriving the Connectivity Target Function" (Google Docs), and the Confluence PCD pages "Working large example" and "Optimization Guide".
- Not received or not read: the Challenges Atlas, the BrainGenix platform paper draft (interneuron values).

## 3. Experiments and results

### Phase A. Multi-target prediction model (sims 22-132)
- Labels added for Pyr-Int, Int-Pyr and Int-Int usable connections and aggregate interneuron-drive and inhibition fractions (`gen_autonm_labels.py`); hard limits asserted per run.
- Random forest per target plus conservative DiCE (`multi_target_optim.py`, 8 tests pass).
- 100 real samples (Sobol design inside the limits, size capped at 70 pyramidal and 30 interneurons by runtime): real skill for Int-Pyr (R2 0.46), weight-scaled pyramidal inhibition (0.46) and Pyr-Pyr conns2 (0.58); none for Pyr-Int, Int-Int, frac_int_driven and strict frac_pyr_inhibited. dm.weight is the top feature everywhere.
- Validation of the top 10 suggested configs: all ran; means predicted vs observed close for the skilled targets (e.g. int_pyr 22.9 vs 27.2). Ten runs cannot show the model ranks configs correctly.
- Bug found: the Excel header `'dm.weight '` had a trailing space, so every earlier Phase 0/1 sample ran at 0.5, not the intended value. Earlier dm.weight importance results should not be trusted. (Marianna had not been told when this was written.) 53 of 100 previously suggested samples were also outside the hard limits.

### Phase B. Weight-space prototype on sim 127 (`weight_space/`)
- 67 pyramidal, 27 interneurons, dm.weight 0.9. 928 Pyr-Pyr pairs at 6.86 nS or more. One to four disjoint engrams feasible.
- On the server, 2939 weights applied and verified; both patterns completed from a 4-cell cue in about 2 ms with no cross-pattern activation. Weights stayed in [0,1]; no synapses created.
- Interneurons never fired: Int-Pyr drive 2.6 nS per cell against 16 nS needed, and 13 of 27 interneurons had no pyramidal input.

### Phase C. Fable loop, round 1: configuration beyond weights (sims 133-140; `fable_loop/it1-it5`, `docs/FABLE_LOOP_LOG.md`)
- New knob: D_synmax for interneuron pairs. Pyr-Int synapses 92 -> 1208 -> 3627 and Int-Pyr 217 -> 3331 -> 10257 at 0.1 / 0.5 / 1.0, with Pyr-Pyr essentially unchanged (matrix correlation 0.97 with sim 127).
- Interneurons fire on NES; synchronous-volley threshold about 15 nS.
- K=3 disjoint 8-cell engrams with exact cue-size selectivity: 4 cue cells complete, 2 or 3 never, zero cross-pattern or bystander activity (needs the 18 nS design; 20 nS is not selective).
- Specificity still depends on pruning non-engram Pyr-Pyr weights: at the as-grown 0.2 every cue runs away; weak background of 0.05 already leaks.
- Inhibition raises the tolerated background weight from 0.01 to 0.03 at D_synmax 0.5.
- D_synmax 1.0 with uniform Pyr-Int weights is over-inhibited: the cue itself drives interneuron 89 (227 nS) and vetoes recall. Routing inhibition feedback-only (cue-cell to interneuron weights scaled to at most 10 nS) removes the veto and gives tolerance 0.05 at 1.0.

### Phase D. Fable loop, round 2: robustness as a test of prediction by reasoning (sims 141-153)
Every experiment had numeric predictions written and timestamped before the run, then scored.
- Scorecard: 51 predictions, 35 hit, 8 partial, 8 miss.
- Predicted well: single-volley conductance sums (which cues complete, 12 of 12 patterns over four seeds), first-spike latency to 0.2 ms, the jitter boundary (recall tolerates cue spread of 9 ms, fails at 12 ms), the D_synmax scaling law (synapse counts follow D_synmax to the power of about 1.6, 0.3 and 0.7 predicted within 1%), the leak threshold of the background weight.
- Predicted badly: burst size and duration, closed loops (STDP weight growth 2-5 times larger than computed), unmodelled mechanisms (fatigue), timing-dependent inhibition (predicted a self-veto at D_synmax 0.7 that did not occur), seed statistics extrapolated from one sample.
- Three new seeds at 0.5: all nine patterns recall from four cue cells and never from two or three; inhibition raises the tolerated background by one step in each seed. The original seed was the most favourable for interneuron drive (frac_int_driven ranges 0.19 to 0.44 over four seeds): quote the spread with any D_synmax claim.
- STDP as shipped can only potentiate: with it on, cue-size selectivity is gone after one recall. Keep it off for recall tests.
- Tolerated background with feedback-only inhibition: 0.02 / 0.03 / 0.03 / 0.05 at D_synmax 0.3 / 0.5 / 0.7 / 1.0; 0.01 everywhere without inhibition.
- Conclusion: reasoning predicts sums and scaling laws over the connectome well, and sustained recurrent dynamics and timing poorly. Reasoning proposes, measurement calibrates.

### Phase E. Head-to-head: mechanistic scaling law vs random forest + DiCE (sims 700-761; `headtohead/`, `docs/HEADTOHEAD_LOG.md`, `docs/SCOPE_headtohead.md`)
Track 1 only: the 7 approved parameters, D_synmax at default. Pre-registered 2026-11-10 before any run; 62 runs, one growth at a time, all rc=0, no hard-limit violation, no timeout.
- Arms: ML = random forest per target + DiCE (`multi_target_optim.py` style) trained on batch B; mechanistic = negative-binomial scaling law on pair count, volume, dm.weight and days, with analyst-chosen configs. Metric J = joint score over Pyr-Int, Int-Pyr, Int-Int and usable_conns2; targets T1 = 1.041, T2 (stretch) = 1.534.
- Search (10 training runs each): best J 1.76 (law) vs 1.49 (forest); runs reaching T1 7 vs 5; T2 4 vs 0.
- Nominations (3 configs per arm x 3 new seeds): mean J 1.19 (law) vs 0.71 (forest); T1 in 6/9 vs 1/9; T2 in 3/9 vs 0/9. Best config mean over 3 seeds: M1 1.42 (law) vs 0.96 (forest). No config reaches T2 on its mean.
- Held-out prediction (12 configs x 2 seeds): the arms rank about equally (J Spearman 0.81 vs 0.79; no bootstrap interval excludes zero). The law is better calibrated (R2 on Pyr-Int and Int-Pyr about 0.55 vs -0.12 and -0.34; J MAE 0.17 vs 0.25).
- Regression to the mean: the three best training configs lost 0.34-0.64 J on fresh seeds. Seed-to-seed noise is 50-70% on interneuron counts. Int-Int limited J in 13 of 18 nominated runs.
- The law's edge came mostly from going to the size cap (70/30) and dm.weight 1.0, which the forest did not do. One comparison, 9 runs per arm: suggestive (about 2 standard errors), not established.
- Analyst (Fable 5.2) pre-registered predictions: direction mostly right, sizes often wrong (e.g. predicted a 15-35% lead on mean J, observed 68%).
- Server: runs 1.35x slower than the timing model (max 1.99x), available memory 138 -> 108 GB.

### Phase F. Bio-consistent networks and ripple test (`recipe_v2/`, run on our own NES)
Source files: `recipe_v2/PHASE1.md`, `ARBOR_RESULTS.md`, `AXON_LEVER_FINDINGS.md`, `axon_rerun/`, `dendrite_rerun/`, `ripple_05/`, `ripple_arborA/`, `ripple_S1/`, `ripple_S1_R3/`, `FABLE_DESIGN_S1.md`, `CA3_NATURAL_RANGES.md`, `CA3_ARBOR_BOUNDS.md`, `roundtrip_test.py`. Raw growth outputs and saved models are not in the repo (size); copies are in `/home/johnjose/cos/netmorph_work/recipe_v2/`.

**(a) D_synmax change.** Team guidance (via John): maxima are pyramidal 1.5 um and interneuron pairs 0.1-0.15 um (maxima only, minimum 0); interneurons have no spines; spines are not in the EM output yet; where the natural arborization conflicts with a built-in specification, the natural arborization wins (Randal's rule). All Phase F growths use D_synmax pyramidal-pyramidal 1.5 and the three interneuron pairs 0.1 (config e: 0.15). The earlier 0.5 and 1.0 um runs (Phases C-E, `ripple_05/`) are therefore a **sensitivity study only**, not bio-realistic. `bio_ranges.json` and `bio_check.py` were not changed, because the maxima are not yet confirmed by Randal.

**(b) Phase 1 and arbor growth.** Five configurations at D_synmax 1.5/0.1 (e: 0.15) gave few drivable interneurons: 6/48, 2/30, 1/32, 2/46 and 8/48 (config e, 16.7%), against a 50% bar; inhibitory fraction onto pyramidal cells 0.5-1.0%. Pyr->Int counts scale with D_synmax, not with density (`PHASE1.md`). Arbor experiments on config a (dendrite lever A, axon levers B-D; `ARBOR_RESULTS.md`): the dendrite lever worked (Pyr->Int 227 -> 539, 10/48 drivable); the axon lever as first tried (shortening tau) did not raise Int->Pyr (298-542 vs 348 baseline). B, C and D were flagged because Pyr->Pyr moved more than the 5% rule.

**(c) Key finding: B_inf, not tau, sets the interneuron axon total** (`AXON_LEVER_FINDINGS.md`, `axon_rerun/README.md`). Interneuron axon tau only shifts the timing of branching (median bifurcation time 14.6, 11.2, 6.6 d for A, B, D) and not the total. Raising `all_interneuron_axons.B_inf` does change it:

| run | int axon cones per cell | Int->Pyr | inhibitory fraction | note |
|---|---|---|---|---|
| R0 (A, B_inf 13.22) | 74.2 | 453 | 0.61% | |
| R1 (B_inf 26) | 414 | 1378 | 2.13% | Pyr->Pyr -14.1% (flag) |
| R2 (B_inf 39) | 1283 | 4404 | 5.22% | about 6.8 h growth; passes the 3% bar, but probably too large |

Drivable interneurons stay at 10/48, because they depend on Pyr->Int (dendrites). Cone positions showed no spatial pile-up at the disc edge, so the earlier 63-74 "ceiling" was the default B_inf, not geometry. Pyr->Pyr moves about +-20% from a seed change alone (R3: +20.2%), so the 5% flag is too strict for that quantity.
Dendrites are at a natural ceiling: about 37 growth cones per interneuron (S1 36.9, S2 34.5, S3 35.4) against 10-39 dendritic bifurcations in the literature (Ascoli 2009, secondary extraction). Natural interneuron fraction is about 8-13% (CA1 7-11%; CA3 about 13% by one GAD65 count) against our 33% (48/144); with 16 interneurons (S3) Pyr->Int fell from 760 to 127 and 4/16 were drivable. (The brief mentioned 17%; no 17% interneuron configuration is in the source files, so S3 is reported as measured.)

**(d) S1: best bio-consistent net** (saved model `v2-arbor-S10000`, `dendrite_rerun/`): 96 pyramidal / 48 interneurons, D_synmax 1.5/0.1, axon B_inf 26, dendrite B_inf 3.5, basal 6-10. Pyr->Int 760, Int->Pyr 1314, Int->Int 1709, inhibitory fraction 2.2%, 13/48 drivable by the old criterion (summed input of all 96 pyramids at weight 1 reaching 13.84 nS). The cap-aware criterion (a memory has only 4-8 cells and weights are at most 1) gives 7/48 for an 8-cell volley and 2/48 for a 4-cell cue (`ripple_S1/README.md`).

**(e) Ripple results.**
- Arbor A (`ripple_arborA/`): 4 memories recall and the ripple works at all 16 simulations; zeroing all Pyr->Int changes nothing material, so inhibition is irrelevant there (recurrent excitation only, bursts end intrinsically).
- S1, standard recipe (`ripple_S1/`): recall 4/4 with no cross-talk, but every ripple case fails the pre-set 40 ms burst criterion (memory G1 bursts 47.6-69 ms; the shuffled order ends at 117 ms). GABA output zeroed (SG) gives identical pyramidal spikes to Pyr->Int zeroed (NI). A uniform background of 0.03 or 0.05 of grown weight gives spurious firing.
- S1, recipe R3, designed by Fable's offline emulator (`FABLE_DESIGN_S1.md`, `ripple_S1_R3/`; 6 hits and 1 miss against the pre-registered predictions as reported to us; not re-scored here). Cue to non-cue 4.125 nS per pair (16.5 nS for 4 cells), loop cap 8 nS, background Pyr->Pyr capped at c nS per connection. Results at c = 0.15: single recall 4/4 memories complete; a 3-cell cue never completes a memory; the ripple succeeds at 12, 16 and 20 ms spacing and in the shuffled order; bursts last 4-7.5 ms; 0 cross-talk and 0 non-member pyramidal spikes. Background cap 0.15 nS is tolerated; 0.25 gives false completion from a 3-cell cue (4/4); 0.5 runs away (297 spurious pyramidal spikes).
- GABA-silenced R3 runs behave identically (single recall and 12 ms ripple both succeed with the same completion): the memory is excitation-only and terminates intrinsically. Functional inhibition would need a settable GABA weight in NES plus roughly 50-60 Int->Pyr synapses per pyramidal cell from interneurons that an 8-cell memory can drive (S1 has 13.7 inhibitory synapses per pyramidal cell in total, median 3).

**(f) Bio-limit caveats.**
- The per-synapse reading of dm.weight 0.1-1.0 is breached by pruned zeros (97.4% of programmed Pyr->Pyr pairs in R3_c0) and by background weights below 0.1 (R3 c = 0.15: all but single-synapse pairs lie below 0.1). `dm_weight` is a growth parameter, so this is a breach only under the strict reading. **To ask Randal.**
- The 100-1000 interneuron axon-tip band is an inference (Ascoli's 10-39 dendritic bifurcations times about 10, plus one cat V1 basket cell study), not a measured CA3 value. In `CA3_NATURAL_RANGES.md` and `CA3_ARBOR_BOUNDS.md` each literature number is marked READ, RECALLED or DERIVED; RECALLED values (for example 5-6% inhibitory fraction of CA1 pyramidal synapses, 10-15% CA3 interneuron fraction) are not verified.
- The D_synmax maxima are not yet confirmed by Randal; spines are not in the EM output yet and interneurons have no spines.

**(g) NES limits found** (cross-reference `docs/NES_API_GAPS_AND_SPEC.md`). `roundtrip_test.py` / `roundtrip_result.json`: weights edited with `SetPrePostStrength` do not survive ModelSave/ModelLoad (`ampa_edit_survived_saveload` false), so all Phase F runs apply weights after ModelLoad in the same session. GABA cannot be programmed: the call returns StatusCode 2 and in effect only zeroes GABA, and inside a batch it aborts the batch. AMPA programming zeroes NMDA on programmed pairs. Fix branch for ModelSave: `fix/modelsave-edited-weights` (not yet in a tag).

**(h) Disclosure.** The R3 recipe was designed by Fable using an offline numpy emulator of the NES network written by Fable from the NES source constants (`recipe_v2/fable_design_S1/net.py`), validated only on arbor A (E1) before the S1 runs; the design memo states the emulator numbers are forecasts, not NES measurements. The emulator's validation on S1, with background, at a 16.5 nS cue or with GABA zeroed was not available when it was used (`FABLE_DESIGN_S1.md`, Not verified). All NES numbers above are from deterministic single runs, one seed.

## 4. Limits and open problems

- D_synmax: the 0.5 and 1.0 um values were modelling choices and are now a sensitivity study only; team guidance (maxima 1.5 pyramidal, 0.1-0.15 interneuron pairs) is used in Phase F but not yet confirmed by Randal, so `bio_ranges.json` is unchanged. `docs/DSYNMAX_RANGE_REQUEST.md` is superseded.
- Specificity relies on pruning non-engram Pyr-Pyr weights to 0.03 or below, and cue-size selectivity relies on a threshold window of about +/-10-20%.
- One reservoir geometry per D_synmax value except round 2's three extra seeds; one trial per condition (NES is deterministic here).
- API gaps: AMPA programming zeroes NMDA on every programmed pair (no per-neurotransmitter endpoint), so recall is AMPA-only; GABA weights cannot be programmed (fixed 0.2); fatigue not editable; no compartment-ID query.
- 5 to 7 of 27 interneurons still receive no pyramidal input. The D_synmax 1.0 reservoir is about 45% inhibitory synapses onto pyramidal cells, which is high.
- The offline surrogate in `weight_space/` is a surrogate, not NES. The 3D visualizer (`viz_app/`) and the Flask app were not run in a real browser.
- Jittered cues of 3 cells never complete; robustness beyond 9 ms spread untested.

## 5. Where things are

- Code and reports: `src/models/autoassociative/` (this branch). New under `NetmorphParOptim/`: `multi_target_optim.py`, `bio_ranges.json`, `bio_check.py`, `batchB_models.py`, `weight_space/`, `fable_loop/` (scripts, analyses and small data per iteration), `viz_app/`, `docs/` (work log, Fable loop log with the prediction blocks, range request), `REPORT_*.md`.
- Left out of the commit for size: per-sample raw output of the 100-sample batch (`NetmorphParOptim/batchB/`, 83 MB), `run_*`, `model_*` and `viz_*` raw dumps and `*.log` under `fable_loop/`, and any file above 1 MB there. Summaries (`batchB_labels_*.xlsx`, `analysis.txt`) are included. The full copy is in `/home/johnjose/cos/netmorph_work/`.
- Phase F material: `NetmorphParOptim/recipe_v2/` (READMEs, scripts, small JSON, figures; files above 2 MB, raw growth outputs, saved models and large logs left out).
- Base: branch `myg_autoassociative_20260325`, commit 57d23f2.
- Shared NES server simulations: 700-761 (Phase E), 22-132 (Phase A and B; sim 127 holds programmed weights) and 133-153 (Phases C and D). Pristine grown reservoirs saved on the server as `fable-it1a-sim133`, `fable-it1b-sim134`, `fable-r2-seed1001/1002/1003`, `fable-r2it4-d03`, `fable-r2it4-d07`. Nothing was deleted; simulations are shared with rkoene.

## 6. How it was made

Orchestration, scripts and simulation runs: Claude Sonnet 5.5 (and Haiku for trivial checks). Weight-space prototype (Phase B): Fable 5.1. Rounds in Phases C and D: Fable 5.2 used only for analysis and predictions, with scripts and runs delegated to cheaper subagents. Commit trailers follow the repository convention.

## 7. Next steps

1. D_synmax range request: emailed to Randal Koene on 2026-11-11 (Marianna not yet contacted); await the range, then run Track 2 (D_synmax added to the head-to-head).
2. Tell Marianna about the dm.weight bug and the out-of-limit samples; re-run the Phase 0/1 importance analysis.
3. Add samples aimed at Pyr-Int and Int-Int targets and retrain.
4. Predict burst length from the connectome (fatigue and adaptive-threshold terms).
5. Map Challenges Atlas structures to config targets once the Atlas is available.
6. Make STDP able to depress, or normalise weights, before using it in recall tests.
