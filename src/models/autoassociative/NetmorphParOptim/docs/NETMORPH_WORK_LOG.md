# Netmorph configuration-space and weight-space programming: work log

Written 2026-11-09. Status: prototype stage. Nothing is committed or pushed.

## 1. Problem and goal

Goal (stated by John, 2026-11-08): use Netmorph configuration-space programming to grow networks, following the structures in the Challenges Atlas, that have enough synapses on the relevant pathways between neural populations to implement a desired behavior, without violating biological realism.

Concrete task: Marianna Gabrielyan's prediction model (random forest plus DiCE counterfactuals) covered only Pyr-Pyr connections. This work extends it to Pyr-Int, Int-Pyr and Int-Int, runs the suggestions through real Netmorph growth in BrainGenix-NES, visualizes the result, and prototypes weight-space programming (Phase 2 tune/prune) on a grown reservoir.

Constraint (John): parameters must never leave the biological limits.

HARD parameter limits (from "Netmorph auto-configuration ML optimization" and "Building Synthetic Ground-Truth Examples"):

| parameter | range |
|---|---|
| days | 20-25 |
| In.pyramidal | 16-128 |
| In.interneuron | 16-128 |
| In.minneuronseparation | 10-15 um |
| In.shape.radius | 100-200 |
| In.shape.thickness | 20-50 |
| all_axons.axondm.dm_weight | 0.1-1.0 |

growth_F = 0.39 and growth_nu0 = 0.00013889 stay constant. Density (10k-50k per mm3) and pyramidal fraction (70-80%) are warnings only.

## 2. Sources used

- Google Docs: Netmorph investigation; Tuning and Pruning; Building an Autoassociative Memory Example; Netmorph auto-configuration ML optimization (1Sl8E9GBP__XJFlYmtbT4oGWaZTo7eJMUCxUbHnxohZY); Building Synthetic Ground-Truth Examples (1HH56qwt_UeDCJT9Gy2a41tQD23CZ4npK); Deriving the Connectivity Target Function (1noTo6Mzj2j74N_S-OAOtaHf9_u0EUncD).
- GitLab: BrainEmulationChallenge, branch myg_autoassociative_20260325, src/models/autoassociative/NetmorphParOptim.
- Confluence (carboncopiespythondev.atlassian.net, space PCD): "Working large example" and subpages; Phase 1 - Spring; Optimization Guide; Autoassociative Optimization Guide.
- Not received: the Challenges Atlas.
- Not yet read: BrainGenix platform paper draft (interneuron GABA and threshold values), Fall 2025 Phase 1-3 pages, Summer 2026 children.

## 3. What was built

All work lives in a detached git worktree of origin/myg_autoassociative_20260325, in the session scratchpad: `/tmp/claude-1002/-home-johnjose-cos/9b844e52-8758-4704-8f2c-1e93562a405d/scratchpad/bec`. The scratchpad is temporary, so copy what you want to keep. John's own clone (BrainEmulationChallenge, branch Drosophilla_example) was not modified.

In `src/models/autoassociative/`:
- `gen_autonm_labels.py` (modified): per-pair labels `usable_pyr_int`, `usable_int_pyr`, `usable_int_int` (default 1 synapse per pair, 0.98 nS AMPA and 0.80 nS GABA per synapse); aggregate labels `frac_int_driven` (>=7.84 nS incoming AMPA), `frac_pyr_inhibited` (>=16 nS incoming GABA) and `frac_pyr_inhibited_w05` (8 nS, weight-scaled); hard limits asserted before each run; NES_SIM_ID printed. `usable_conns1/2` unchanged.
- `NetmorphParOptim/multi_target_optim.py`: random forest per target, conservative DiCE wrapper, joint counterfactuals drawn from a bio-feasible pool, needs-more-samples, CLI (train, optimize, needs-more, synthetic-demo, bio-report).
- `NetmorphParOptim/bio_ranges.json` and `bio_check.py`: hard limits, with every number tagged docs, prior_work or assumption.
- `NetmorphParOptim/test_pipeline.py`: 8 tests pass.
- Flask app extended with targets, interneuron input and a synthetic-data banner. Checked only with the Flask test client and `node --check`.
- `NetmorphParOptim/weight_space/`: `reservoir.py`, `engram.py`, `program.py`, `surrogate.py`, `run_all.py`, `server_apply.py`, `score_server.py` and `REPORT_weight_space.md`.
- Visualizer in `scratchpad/viz`: Express 4.21.2 plus three 0.170.0, `npm start` on port 3100, `npm test` passes. The 3D rendering has not been checked in a real browser.

## 4. Findings

1. **dm.weight bug.** The Excel header was `'dm.weight '` with a trailing space, so the setting was never found and every earlier Phase 0 and Phase 1 sample ran at 0.5 (the base model has 0.2). Total Pyr-Pyr g_peak now scales with dm.weight: 1733, 1220 and 472 at 1.0, 0.9 and 0.2. Old dm.weight importance results should not be trusted. Marianna has not been told yet.
2. **Suggested sample file.** 53 of 100 suggested samples were outside the hard limits (15 with pyramidal above 128, 48 with thickness above 50). They were replaced with in-limit rows.
3. **Runtime grows steeply with size.** 49 neurons took 95 s, 57 took 143 s, 95 took 470 s, and 122 hit the 15 minute cap. This set the size cap of pyramidal 70 or fewer and interneurons 30 or fewer for the batch.
4. **Batch B (100 real samples).** Sobol design inside the hard limits; correlations between size, dm.weight and density are near zero (-0.02 to 0.09). All 100 runs completed with rc=0 and no cap hits; the longest took 584 s. Simulations 22-122 on the shared NES server.
5. **Models (5-fold, 10 repeats, random forest).**

| target | R2 | verdict |
|---|---|---|
| int_pyr | 0.46 | real skill |
| frac_pyr_inhibited_w05 | 0.46 | real skill |
| Pyr-Pyr conns2 | 0.58 | real skill |
| pyr_int | -0.64 | no better than the mean |
| int_int | -0.46 | no better than the mean |
| frac_int_driven | 0.08 | no better than the mean |
| strict frac_pyr_inhibited | -0.56 | no better than the mean |

   A Poisson model beats the random forest on the three skilled targets (R2 0.60-0.69). dm.weight is the top feature on every target (Spearman 0.6-0.77); optima sit at 0.8-1.0.
6. **Validation of the top 10 suggested configs (simulations 123-132).** All completed. Means predicted vs observed: int_pyr 22.9 vs 27.2; conns2 653 vs 660; frac_pyr_inhibited_w05 0.080 vs 0.059; frac_int_driven 0.076 vs 0.085. Every config gave non-zero `frac_int_driven` and `w05`, against about half of the random samples. Ten runs are too few to say the model ranks configs correctly.
7. **Weight-space prototype (simulation 127: 67 pyramidal, 27 interneurons, dm.weight 0.9).** The reservoir has 928 Pyr-Pyr pairs at 6.86 nS or more, against 58 in the doc baseline. One to four disjoint engrams are feasible. On the server, 2939 weights were applied and verified; both patterns completed from a 4-cell cue in about 2 ms with no spurious or cross-pattern activation. Weights stayed in [0,1] and no synapses were created.

## 5. Limits and open problems

- Inhibition is untested: interneurons never fired. Int-Pyr drive is 2.6 nS per cell against 16 nS needed, and 13 of 27 interneurons get no pyramidal input. Weights cannot fix this; it needs a denser interneuron reservoir.
- The offline surrogate completes a pattern even from 2 cue cells, so selectivity is weak. It is a surrogate, not NES.
- API gaps: AMPA programming zeroed 2868 NMDA entries (no per-neurotransmitter weight endpoint, C2); GABA cannot be programmed; fatigue not editable (C1); no compartment-ID query (C3). A partly failed batch is a hazard.
- Weak targets (pyr_int, int_int, frac_int_driven, strict frac_pyr_inhibited) need more samples aimed at them.
- Assumptions in `bio_ranges.json` still to review: 25% interneuron imputation, um units, soma separation rule, per-neuron synapse comparison.
- The 3D visualizer and the Flask app have not been run in a real browser.

## 6. Server state (shared NES server, shared with rkoene)

- Simulations from this work: IDs 22-132 named Netmorph-autoassociative000N, including 62 (orphan from a restarted launch). Earlier stray runs from the ladder (4) and the aborted overnight batch (2) have unrecorded IDs. Nothing was deleted.
- Simulation 127 holds programmed weights and was simulated to 400 ms; morphology unchanged. Keep or revert is awaiting John's answer.
- John texted Randal about cleanup; no reply recorded here.

## 7. Models used

Claude Sonnet 5.5 for orchestration and routine runs. The weight-space prototype ran on the "fable" alias, which resolved to Fable 5.1 (claude-fable-5-1). Fable 5.2 was released 2026-11-09 (Anthropic announcement); John plans to update Claude Code and retry.

## 8. Commits

None yet. When committing, end messages with: Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>

## 9. Next steps

1. Decide keep or revert for simulation 127.
2. Tell Marianna about the dm.weight bug.
3. Collect the Randal reply and clean up our simulations (only our own IDs).
4. Add samples aimed at Pyr-Int and Int-Int, then retrain.
5. Weight-space: test with a denser interneuron reservoir; compare to the doc's inhibition bottleneck; try K=2-3 engrams on the server with STDP.
6. Review the assumption-tagged bio ranges; read the platform paper for interneuron values.
7. Open the visualizer in a real browser (the VNC setup from worker-1 can do this).
8. Get the Challenges Atlas and map its structures to config targets.
9. Copy the worktree out of the scratchpad and commit.

## 10. Key files

- Worktree root: `/tmp/claude-1002/-home-johnjose-cos/9b844e52-8758-4704-8f2c-1e93562a405d/scratchpad/bec/src/models/autoassociative/NetmorphParOptim/`
- Reports there: `REPORT_run1.md`, `REPORT_timing_ladder.md`, `REPORT_batchB_part1.md` to `part3.md`, `REPORT_models_batchB.md`, `weight_space/REPORT_weight_space.md`.
- Data there: `batchB_samples.xlsx`, `batchB_labels_part1-4.xlsx`, `validation_configs.xlsx`, `validation_predictions.xlsx`, `validation_labels.xlsx`, `suggested_configs_batchB.xlsx`.
