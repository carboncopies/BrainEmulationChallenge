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
- Resolved 2026-11-13 (Randal Koene, Phase H): `dm.weight` applies only to the growth parameter, so the 0.1-1.0 limit is not a per-synapse weight limit. Pruned zeros and the 0.15 nS background weights are therefore not a limit breach. (Earlier wording of this item treated it as an open question under a strict per-synapse reading; that reading is withdrawn.)
- The 100-1000 interneuron axon-tip band is an inference (Ascoli's 10-39 dendritic bifurcations times about 10, plus one cat V1 basket cell study), not a measured CA3 value. In `CA3_NATURAL_RANGES.md` and `CA3_ARBOR_BOUNDS.md` each literature number is marked READ, RECALLED or DERIVED; RECALLED values (for example 5-6% inhibitory fraction of CA1 pyramidal synapses, 10-15% CA3 interneuron fraction) are not verified.
- The D_synmax maxima were confirmed by Randal on 2026-11-13 (Phase H); spines are not in the EM output yet and interneurons have no spines.

**(g) NES limits found** (cross-reference `docs/NES_API_GAPS_AND_SPEC.md`). `roundtrip_test.py` / `roundtrip_result.json`: weights edited with `SetPrePostStrength` do not survive ModelSave/ModelLoad (`ampa_edit_survived_saveload` false), so all Phase F runs apply weights after ModelLoad in the same session. GABA cannot be programmed: the call returns StatusCode 2 and in effect only zeroes GABA, and inside a batch it aborts the batch. AMPA programming zeroes NMDA on programmed pairs. Fix branch for ModelSave: `fix/modelsave-edited-weights` (not yet in a tag).

**(h) Disclosure.** The R3 recipe was designed by Fable using an offline numpy emulator of the NES network written by Fable from the NES source constants (`recipe_v2/fable_design_S1/net.py`), validated only on arbor A (E1) before the S1 runs; the design memo states the emulator numbers are forecasts, not NES measurements. The emulator's validation on S1, with background, at a 16.5 nS cue or with GABA zeroed was not available when it was used (`FABLE_DESIGN_S1.md`, Not verified). All NES numbers above are from deterministic single runs, one seed.

### Phase G. Robustness, GABA patch route and inhibition timing (`recipe_v2/robustness_S1/`, `gaba_patch/`, `inhibition_timing/`, run on our own NES)
Source files: `recipe_v2/robustness_S1/README.md`, `GABA_LEVERS.md`, `gaba_patch/README.md`, `inhibition_timing/README.md`, `LIT_INHIBITION_ENGRAMS.md`, `CA3_NATURAL_RANGES.md`, `CA3_ARBOR_BOUNDS.md`, `FABLE_DESIGN_S1.md`, `fable_design_S1/`. All numbers below are copied from those files. Growth outputs for the two new seeds (`grow_S1-seed629/630`, saved models, `viz/`) and `probe_traces.npz` are left out of the repo (size); copies are in `/home/johnjose/cos/netmorph_work/recipe_v2/`.

**(a) Robustness of recipe R3 on S1** (`robustness_S1/`). R3 was used unchanged (cue 16.5 nS = 4.125 nS per pair, loop cap 8 nS, Pyr->Int weight 1, background min(0.2 g, c) with c = 0 or 0.15 nS, GABA untouched); no recipe value needed adjusting. Every run is scored "complete" when the non-cue cells fired 4/4 for every cued memory. Designs: annealing, 4 cue + 4 non-cue cells per memory, every cue->non-cue pair at least 4.5 nS, no relaxation.

| network | K | drivable interneurons (cap-aware; network / used by memories) | single recall, 3-cell cue never completes (c0, c0.15) | ripple 12/16/20 ms + shuffled 16 ms (c0.15) | GABA-silenced (12 ms) |
|---|---|---|---|---|---|
| seed 20240629 (new) | 4 | 3 (109, 126, 142) / 0 | pass, pass | all pass; last spike 40.1/52.3/64.4/52.2 ms | identical to GABA on |
| seed 20240630 (new) | 4 | 4 (100, 127, 130, 138) / 1 (138) | pass, pass | all pass; 40.1/52.2/64.3/52.2 ms | identical |
| S1 seed 628, new groups | 4 | 7 | single pass | 12 ms pass, last 40.2 ms | - |
| S1 seed 628 | 5 | 7 | pass (c0.15) | 12 ms pass, last 52.6 ms | - |
| S1 seed 628 | 6 | 7 | pass (c0.15) | 12 ms pass, last 64.1 ms | - |

Per memory: 8 member spikes (one volley); burst end 4.1-4.5 ms after the cue in all cases. Pyramidal spikes 32, 40, 48 for K = 4, 5, 6 (8 per memory, members only, once each). Cross-talk 0 and spurious non-member pyramidal spikes 0 in every run; 3-cell cues gave 0 false completions in every single run (K = 4 per seed: 8 cues; K = 5: 10; K = 6: 12). In a ripple (K = 5, 6) with a 3-cell cue for memory 2: that memory 0/4 with 3 member spikes, other memories unaffected. Interneurons: on seed 629 none fired; on seed 630 int 138 fired once per event in 2 memories; S1 K = 5 had 0-2 per memory. GABA-silenced runs (all GABA pairs zeroed, readback `gaba_nonzero_after` = 0) are spike-for-spike identical. Readback: 0 weight mismatches, 0 NMDA left in all 24 sims. Seeds 629/630 grew in 66/63 min.
Not tested: Dt 0.1 on the new seeds; a 3-cell cue inside a ripple on seeds 629/630 (single-run 3-cell tests pass); K > 6; background above 0.15; each design is one annealing result, not an optimum. Deterministic single runs.

**(b) GABA strength and count levers: source reading** (`GABA_LEVERS.md`; read-only, CONFIRMED = read in source, INFERENCE = reasoned, not run).
- The "GABA 0.2" is the dimensionless receptor `Weight` (`NetmorphManagerThread.cpp:457`, `C.Weight = 0.2`, hard-coded for AMPA, NMDA and GABA alike), not 0.2 nS. Peak conductance per GABA synapse is 0.8 nS (`gaba_raw.ReceptorPeakConductance_nS = 80e-3`, quantity 10), so the effective GABA is 0.16 nS per synapse; a pair's conductance scales linearly with synapse count and with weight.
- `dm.weight` is an axon direction-model weight (steers growth) and not a synaptic parameter. No growth parameter scales GABA strength, and no multi-synapse-per-contact, density or bouton-spacing parameter was found. Remaining count levers: D_synmax, arbor size (B_inf, tau, etc.).
- API: `SetPrePostStrength`/`SetAllStrength`/batch are AMPA only. `LIFCReceptor/Create` exists and can add receptors (feasibility of adding GABA receptors by this route: INFERENCE, not run).
- Model-file route: the saved model is a flat binary, with `LIFCReceptorBase` records (Weight, PeakConductance_nS, PSPRise/Decay_ms, reversal, neurotransmitter) that ModelLoad uses to rebuild the receptors. Source reading said an edit of GABA records before ModelLoad would be honoured; Section (c) below tested it.

**(c) GABA patch via the model file** (`gaba_patch/`, S1 = `v2-arbor-S10000`). The original model was never modified; patched copies (`v2-arbor-S1-gabax{2,2p5,5}`) were made by `patch_model.py`, used and deleted (regenerate in seconds).
- The file has 113,267 receptor records: 58,462 AMPA (W 0.2, 0.98 nS), 3,023 GABA (W 0.2, 0.8 nS, reversal -70 mV, rise 0.5, decay 10 ms) and 51,782 NMDA (W 0.2, 0.55 nS); this matches the growth dump (3,023 GABA synapses; 1,314 in 823 Int->Pyr pairs, 1,709 in 719 Int->Int pairs).
- ModelLoad honours the GABA weight edit: x2 gives all GABA pair weights 0.4 with AMPA/NMDA unchanged at 0.2, GPeakSum identical for 7,644 pairs, and total GABA pair conductance ratio 2.0000. x2.5 (0.5) and x5 (1.0) loaded the same way.
- Natural-range comparison (S1, `natural_range.json`): Int->Pyr unitary conductance (weight x 0.8 nS x synapses) mean 0.255 nS (median 0.16, p90 0.48, max 1.6) against Ecker PV->PC 0.65 nS; the mean reaches 0.65 at x2.54 and the median at x4.06; max <= 3 nS at x1.875; x5 puts all pairs at >= 0.8 nS with 5% above 3 nS. Connection probabilities: Int->Pyr 0.179 (Ecker 0.25), Pyr->Int 0.123 (0.10), Int->Int 0.319 (0.25). 13.7 GABA synapses per pyramidal cell (natural somatic terminals about 60-140, as quoted in the source file) and GABA decay 10 ms against 3.3 ms.
- Effect on recall and ripple (R3 recipe, c = 0 and 0.15, single recall, 4-memory ripple at 12/16/20 ms and shuffled 16 ms) at x1, x2, x2.5, x5: every metric identical or within 0.5 ms; all complete, 0 spurious, 0 cross-talk, 3-cell cues never complete, activity end 40.2/53.7/66.3 ms, 1-2 interneuron spikes per memory. Inhibition did not veto the cue either. Burst end differed by up to +0.6 ms against GABA-silenced (x5, 12 ms: 4.64 vs 4.09 ms).

**(d) Inhibition timing and drive** (`inhibition_timing/`). Edits were tested on copies of the S1 model (35 sims, all deleted). A ModelLoad -> ModelSave round trip left all 113,267 records identical.
- Honoured by the loader: Pyr->Int AMPA Weight 1.0 (4.97x PSP), PeakConductance x3 (2.99x, exact), both (14.7x), rise/decay edits (waveform changes), GABA weight x2.5/x5 and kinetics 0.3/3.3 ms. Int->Int weight/decay edits were only round-trip verified, not used.
- Weight above 1 is loaded and reported by the connectome but the conductance is clipped at PeakConductance (W 2: 1.14x of W 1 at 3 ms; W 5: 1.17x, only a faster rise). It is not a drive lever; raise PeakConductance instead.
- Natural bound on Pyr->Int: per-connection unitary conductance at weight 1 (R3) is already 1.31 nS mean (median 0.98, max 4.9) against a natural 0.85 nS, i.e. 1.54x natural; 7.6% of pairs (43/569) lie above 3x natural. Scaling to the natural mean (x0.649) reduces drive. Drivable interneurons (at least 13.84 nS from the best 8 cells): 4 of 48 at x0.65, 7 at x1.0, 21 at x1.95 (3x natural mean; non-natural). The source file attributes the weakness to the number of Pyr inputs per interneuron (11.9 pairs, 15.8 synapses), not to per-connection strength.
- Variants: P1 (Pyr->Int x0.649, GABA x2.5, kinetics 0.3/3.3), P2 (P1 with GABA x5), P3 (Pyr->Int x1.948, GABA x2.5 kinetics, non-natural), P1u (Pyr->Int x1.0). Results (`summary.json`): all P1, P1u and P3 single recalls and ripples (12/16/20 ms, shuffled 16 ms) complete 4/4 with 0 spurious and 0 cross-talk; burst ends 4.1-4.6 ms; ripple last spike 42.0/54.8/67.5 ms (P1) and 42.8/55.2/67.2 ms (P3). With P3, 6-7 interneurons fire 3-5 spikes per memory; zeroing GABA (SG) or interneuron spikes (IS) changes burst end by at most 0.1 ms in 12 ms ripples (P3_rip12 4.52/4.26/4.16/4.17 vs SG 4.52/4.19/4.09/4.06). The 3-cell-cue-in-ripple runs for P3 are recorded in `summary.json` (`P3_c025_cue3`, success False, memory 3 0/4 complete); they were not analysed further here. Interneurons fire after the 8-spike pyramidal burst has ended, so inhibition shapes nothing even at 1.95x drive.

**(e) Literature notes** (`LIT_INHIBITION_ENGRAMS.md`, `CA3_NATURAL_RANGES.md`, `CA3_ARBOR_BOUNDS.md`, `CA3_INTERNEURON_ARBOR_REFS.md`). These are web-search summaries. Each number is marked READ (seen in a fetched page or snippet), RECALLED (from memory, not verified), DERIVED or INFERENCE. Full texts were often unreadable (for example Guzman 2016, Nakazawa 2002 and Treves and Rolls PDFs were compressed binaries; Schlingloff only partly read) and the fetch tool summarises pages with a small model. **Spot-check any number against the primary source before quoting it.**

**(f) Conclusions.**
- Excitation-only memory is reproducible: R3 works on three seeds (628, 629, 630) and with up to 6 memories (K = 4, 5, 6), without changing any recipe value, and recall and ripple are identical with GABA silenced.
- Functional inhibition was not achieved at the hard limits (weight at most 1 per synapse, Pyr->Pyr and interneuron limits, natural-range bounds) with current methods: raising GABA weight x2-x5, speeding GABA kinetics, and raising Pyr->Int drive up to 1.95x changed no recall or ripple metric beyond 0.6 ms in burst end.
- Inference (not tested): the hypothesis that network size and convergence (about 12 Pyr inputs per interneuron, 13.7 GABA synapses per pyramidal cell in a 96/48 network) rather than strength or timing limits inhibition. A larger network or more inputs per interneuron would test it.
- Workaround: patch-via-model-file route for GABA settings (weight, kinetics; Pyr->Int AMPA peak conductance). Caveats: source-confirmed and round-trip verified for weight and kinetics (113,267 records identical); weight above 1 is clipped at PeakConductance; the reader locates the receptor array by an ID-sequence pattern and uses a 72-byte record layout from this NES build; edits must be made offline on a copy before ModelLoad; new growths still get the hard-coded 0.2 unless the source line at `NetmorphManagerThread.cpp:457` is changed (not done). This is a workaround, not a supported API.
- Disclosure: all NES results are deterministic single runs; designs for seeds 629/630 and K = 5, 6 are one annealing result each.

### Phase H: team replies 2026-11-13
Randal Koene replied to the open questions. Source for the interneuron literature part: `recipe_v2/CA3_INTERNEURON_TYPES.md` (tags READ / DERIVED / RECALLED kept; partly RECALLED or from summarised fetches, spot-check before quoting). No NES runs in this phase.

1. **D_synmax limits.** The proposed hard limits make sense: maximum only, minimum 0; pyramidal-pyramidal 1.5 um, interneuron pairs 0.15 um (0.1 used in our runs).
2. **Interneuron morphometrics dataset.** Randal knows of no dataset source for CA3 interneuron morphometrics. He asked us to check the definition of total dendritic length and suggested the HBP / BlueBrain reconstructions. Result in `CA3_INTERNEURON_TYPES.md`: NeuroMorpho's `length` field is axon plus dendrite for cells with a traced axon, so it is not dendritic length; the BBP portal was not accessed (no tool route; its model is CA1); Hippocampome gives layer labels only.
3. **Reference for CA3 interneuron types.** No preferred reference. He asked us to check the CA3 interneuron types and which does lateral inhibition. Literature headline (`CA3_INTERNEURON_TYPES.md`): PV basket cells are the most likely source (fast, large, short-latency IPSCs onto pyramidal cells, PV-PV reciprocity; READ, Kohus 2016); axo-axonic cells second; CCK basket, OLM and ivy/neurogliaform cells slow or dendritic. No source directly measured shut-off after a CA3 recall burst per type.
4. **Gap from natural.** The gap is interneuron arbor extent and the high proportion of pyramidal cells contacted. NetMorph's default interneuron outgrowth may be wrong for PV basket cells (its statistics come from cultures). Reference values in the literature note: PV basket dendrite about 5,000-9,000 um, axon about 30,000-45,000 um working range (DERIVED from slice reconstructions, lower bounds).
5. **dm.weight.** It applies only to the growth parameter, so the 0.1-1.0 limit is not a per-synapse weight limit. The 0.15 nS background weights and pruned zeros are not a limit breach. The earlier open-question wording (section 3, Phase F item on the per-synapse reading, the "Limits and open problems" section and the share page) is updated accordingly.
6. **GABA and NMDA settings.** He would consider exposing GABA and NMDA settings in the interface: GABA with a maximum conductance and a weight 0-1; NMDA mostly relevant only for learning. This would remove the need for the model-file patch route of Phase G.

**Housekeeping.** `bio_ranges.json` is gitignored (`*.json`), and the new D_synmax limits were added to local copies only. They are recorded in `docs/BIO_RANGES_DSYNMAX_ADDITION.md` so they are reproducible. `docs/DSYNMAX_RANGE_REQUEST.md` is marked answered.

## 4. Limits and open problems

- D_synmax: the 0.5 and 1.0 um values were modelling choices and are now a sensitivity study only; team guidance (maxima 1.5 pyramidal, 0.1-0.15 interneuron pairs) was confirmed by Randal on 2026-11-13 (Phase H). `bio_ranges.json` is gitignored, so the entries are recorded in `docs/BIO_RANGES_DSYNMAX_ADDITION.md`. `docs/DSYNMAX_RANGE_REQUEST.md` is answered.
- Specificity relies on pruning non-engram Pyr-Pyr weights to 0.03 or below, and cue-size selectivity relies on a threshold window of about +/-10-20%.
- One reservoir geometry per D_synmax value except round 2's three extra seeds; one trial per condition (NES is deterministic here).
- API gaps: AMPA programming zeroes NMDA on every programmed pair (no per-neurotransmitter endpoint), so recall is AMPA-only; GABA weights cannot be programmed through the API (fixed 0.2; a model-file patch route exists, Phase G); fatigue not editable; no compartment-ID query.
- Phase G: functional inhibition was not achieved at the hard limits with current methods (GABA x2-x5, faster kinetics, Pyr->Int drive up to 1.95x: no effect on recall or ripple). Network size/convergence as the cause is an inference, untested. The excitation-only result is tested on 3 seeds and K = 4-6 only (deterministic single runs; Dt 0.1, K > 6 and background above 0.15 untested). Literature numbers in `recipe_v2/LIT_*.md` and `CA3_*.md` are partly RECALLED or from unreadable full texts and must be spot-checked.
- 5 to 7 of 27 interneurons still receive no pyramidal input. The D_synmax 1.0 reservoir is about 45% inhibitory synapses onto pyramidal cells, which is high.
- The offline surrogate in `weight_space/` is a surrogate, not NES. The 3D visualizer (`viz_app/`) and the Flask app were not run in a real browser.
- Jittered cues of 3 cells never complete; robustness beyond 9 ms spread untested.

## 5. Where things are

- Code and reports: `src/models/autoassociative/` (this branch). New under `NetmorphParOptim/`: `multi_target_optim.py`, `bio_ranges.json`, `bio_check.py`, `batchB_models.py`, `weight_space/`, `fable_loop/` (scripts, analyses and small data per iteration), `viz_app/`, `docs/` (work log, Fable loop log with the prediction blocks, range request), `REPORT_*.md`.
- Left out of the commit for size: per-sample raw output of the 100-sample batch (`NetmorphParOptim/batchB/`, 83 MB), `run_*`, `model_*` and `viz_*` raw dumps and `*.log` under `fable_loop/`, and any file above 1 MB there. Summaries (`batchB_labels_*.xlsx`, `analysis.txt`) are included. The full copy is in `/home/johnjose/cos/netmorph_work/`.
- Phase F and G material: `NetmorphParOptim/recipe_v2/` (READMEs, scripts, small JSON, figures; files above 2 MB, raw growth outputs, saved models and large logs left out). Phase G: `robustness_S1/`, `gaba_patch/` (patcher `patch_model.py`, reader `gabafile.py`), `inhibition_timing/`, `fable_design_S1/`, and the notes `GABA_LEVERS.md`, `LIT_INHIBITION_ENGRAMS.md`, `CA3_NATURAL_RANGES.md`, `CA3_ARBOR_BOUNDS.md`, `CA3_INTERNEURON_ARBOR_REFS.md`, `AXON_LEVER_FINDINGS.md`, `FABLE_DESIGN_S1.md`. Phase H: `recipe_v2/CA3_INTERNEURON_TYPES.md`, `docs/BIO_RANGES_DSYNMAX_ADDITION.md`.
- Base: branch `myg_autoassociative_20260325`, commit 57d23f2.
- Shared NES server simulations: 700-761 (Phase E), 22-132 (Phase A and B; sim 127 holds programmed weights) and 133-153 (Phases C and D). Pristine grown reservoirs saved on the server as `fable-it1a-sim133`, `fable-it1b-sim134`, `fable-r2-seed1001/1002/1003`, `fable-r2it4-d03`, `fable-r2it4-d07`. Nothing was deleted; simulations are shared with rkoene.

## 6. How it was made

Orchestration, scripts and simulation runs: Claude Sonnet 5.5 (and Haiku for trivial checks). Weight-space prototype (Phase B): Fable 5.1. Rounds in Phases C and D: Fable 5.2 used only for analysis and predictions, with scripts and runs delegated to cheaper subagents. Commit trailers follow the repository convention.

## 7. Next steps

1. D_synmax range request: answered by Randal Koene on 2026-11-13 (Phase H; hard maxima, minimum 0). Track 2 (D_synmax added to the head-to-head) can now run if wanted.
2. Tell Marianna about the dm.weight bug and the out-of-limit samples; re-run the Phase 0/1 importance analysis.
3. Add samples aimed at Pyr-Int and Int-Int targets and retrain.
4. Predict burst length from the connectome (fatigue and adaptive-threshold terms).
5. Map Challenges Atlas structures to config targets once the Atlas is available.
6. Make STDP able to depress, or normalise weights, before using it in recall tests.
