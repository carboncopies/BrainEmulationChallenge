# Scope: head-to-head on the Netmorph configuration problem

Written 2026-11-10. Scoping only: no NES simulation was run for this document, nothing was committed or deleted. All numbers below come from existing data (100 batch B samples, sims 22-122; 8 connectome dumps from sims 127, 133, 134, 141, 145, 146, 147, 151). Offline test outputs: `scope_offline/A/RESULTS.md` (models on batch B) and `scope_offline/B/RESULTS.md` (per-pair kernel).

Arms:
- **ML arm** (Marianna Gabrielyan's method as we extended it): random forest per target on the raw config parameters plus DiCE counterfactuals, `NetmorphParOptim/multi_target_optim.py`.
- **Mechanistic arm**: a small scaling law proposed by reasoning, calibrated on few runs, inverted directly.

## 1. Problem definition and targets

**Problem.** Choose the growth configuration, inside the hard limits, so that the grown network has enough synapses and drive on the interneuron pathways and the Pyr-Pyr pathway to support engram recall with working inhibition.

**Hard limits (both arms, asserted with `bio_check.py`).** days 20-25; pyramidal 16-128; interneuron 16-128; minneuronseparation 10-15; shape.radius 100-200; shape.thickness 20-50; dm.weight 0.1-1.0; growth_F and growth_nu0 constant. Runtime cap: pyramidal <= 70, interneuron <= 30.

**Two tracks, because the decisive knob is outside the approved set.**
- Track 1: the seven parameters only, `D_synmax` at defaults (0.1 for interneuron pairs).
- Track 2: the seven parameters plus `D_synmax` for the three interneuron pathways. It runs only if the team approves a range (`DSYNMAX_RANGE_REQUEST.md`, not sent). Both arms get the same range.

**Targets and success criteria.** Use continuous per-pathway totals as the primary quantities, with functional thresholds taken from the NES measurements in the Fable loop (interneuron fires at about 15 nS synchronous AMPA, i.e. 15 synapses at 0.98 nS).

| id | quantity (per grown network) | success threshold | basis |
|---|---|---|---|
| T-PI | fraction of interneurons with >= 13.84 nS incoming AMPA from pyramidal cells | >= 0.30 | sim 133 has 0.37 and inhibition worked; seeds 1001-1003 have 0.19-0.30 |
| T-IP | mean incoming GABA g_peak per pyramidal cell | >= 30 nS | sim 133: 3331 x 0.8 / 67 = 39.8 nS; sim 147 (D 0.3): 17.2 nS, tolerance only 0.02 |
| T-II | Int->Int synapses | >= 200 | sim 147 level; no functional test yet, so this is a reporting target, not a pass/fail one |
| T-PP | Pyr->Pyr pairs usable for a 4-cell cue (`usable_conns2`) | >= 460 | 75th percentile of batch B; sim 127 class supports K=3 engrams |
| T-soft | density 10k-50k per mm3, pyramidal fraction 0.70-0.80 | no warning | soft bio checks |

A config "hits" when T-PI, T-IP and T-PP pass and T-soft has no warning, on at least 2 of 3 seeds. T-PI and T-IP are not reachable in Track 1 on current evidence (best batch B `frac_int_driven` is 0.24 at the lower 7.84 nS threshold; sim 127 has 1 of 27 interneurons at 13.84 nS). Track 1 is therefore scored on prediction error and on the best value reached, not on hit rate.

The existing labels `usable_pyr_int`, `usable_int_int`, `frac_int_driven` (7.84 nS) and strict `frac_pyr_inhibited` are kept as secondary metrics so results stay comparable with the batch B report.

## 2. Fair protocol

1. **Same information at the start.** Both arms get all existing data: the 100 batch B rows and their raw counts, and the 21 Fable sims (133-153; 7 of them are distinct grown reservoirs).
2. **Same simulation budget.** Each arm gets the same number of new growth runs (section 3), in two rounds, so both can adapt once.
3. **Held-out test set neither arm tunes on.** 12 configs drawn by a fixed script (scrambled Sobol, seed written in the pre-registration) inside the hard limits and the size cap, stratified so 4 sit in the high-value corner (dm.weight >= 0.8, days >= 24), each grown on 2 seeds that neither arm has used. Both arms submit predictions for all targets with 80% intervals before these are run.
4. **Final nominations.** Each arm nominates 5 configs per track. Each is grown on 3 fresh seeds (shared between arms).
5. **Pre-registration.** A dated block in the log before every round: predictions with numbers, the metric definitions below, and the analysis script hash. Scored hit, partial or miss as in round 2.
6. **Metrics.**
   - Target hit rate of the nominated configs (per seed and 2-of-3 rule).
   - Simulations needed to reach the first hit and to reach hit rate >= 0.6.
   - Prediction error on the held-out set: Spearman, Poisson deviance explained, MAE, interval coverage.
   - Seed spread: coefficient of variation across seeds for every reported quantity.
7. **Seeds.** All 100 batch B runs used the same Netmorph seed (20240628; verified in all run logs). So the ML arm has never seen seed variation, and there are no replicates to measure a noise floor there. The only seed evidence is four seeds at one config: totals vary by 12-20% (CV: Pyr-Pyr 0.12, Pyr-Int 0.20, Int-Pyr 0.14, Int-Int 0.16). Any held-out error below about that level is noise, not skill.
8. **Same executor.** All runs are launched by the same script and cheaper subagents for both arms; Fable is used only to propose the mechanistic arm's model and configs.
9. **ML arm is run faithfully.** RF with 500 trees and DiCE as in `multi_target_optim.py`; it may add `D_synmax` as a feature in Track 2 and may use continuous labels if that helps it. A Poisson GLM on the seven raw parameters is reported as a second baseline, because it already beats the RF (section 5).

## 3. Budget and runtime

Runtime model fitted on the 100 batch B runs (in-sample, R2 0.92): log(wall_s) = -4.46 + 1.76 log(pyr+int) + 0.112 days. Volume adds nothing.

| config | predicted wall time |
|---|---|
| 24 pyr + 16 int, days 20 | 71 s |
| 48 + 20, days 22 | 225 s |
| 67 + 27, days 25 | 556 s |
| batch B mean (measured) | 340 s, range 106-584 s |
| 96 + 26, days 24 (ladder, measured) | > 900 s, hit the cap |

| item | runs | est. wall time (sequential) |
|---|---|---|
| ML arm, 2 rounds of 10 | 20 | ~2.3 h at ~420 s (it will sample large, dense configs) |
| Mechanistic arm, 2 rounds of 10 | 20 | ~1.5-2.3 h (may use small calibration nets) |
| Held-out set, 12 configs x 2 seeds | 24 | ~2.3 h at the batch mean |
| Final nominations, 2 arms x 5 configs x 3 seeds | 30 | ~4.6 h at 556 s |
| Total (one track) | 94 | ~11-12 h |

Track 2 adds about the same again if run in full; a reduced Track 2 (10 runs per arm, 6 held-out x 2 seeds, 3 nominations x 3 seeds: 50 runs, ~6 h) is the recommended size.

**Parallelism.** Not measured. All our batches ran one growth at a time. Before the live phase, run one probe: two identical 48+20 growths concurrently against one alone. If two concurrent runs take less than 1.5 times one run each, use two streams. The server is shared with rkoene, so no more than two streams, only our own sim IDs, nothing deleted, and a new sim per run. Recall tests on NES are out of this head-to-head (growth labels only); they come after, on the winning configs.

## 4. What each arm does, and predictions

**ML arm.** Round 1: fit RF on existing data, generate DiCE counterfactuals toward the thresholds, run 10. Round 2: refit, run 10 more. Nominate the top 5 by predicted joint score.

**Mechanistic arm.** Fit the law of section 5 (idea 1) to existing data. Round 1: 10 runs chosen to pin down the least certain exponents (and, in Track 2, the interaction of `D_synmax` with dm.weight and density, on small cheap networks). Round 2: 10 runs at the predicted optimum and its neighbours on new seeds. Nominate 5 configs with a seed margin (predicted mean >= threshold x 1.3).

**Predictions (to be copied into the pre-registration).**
- Track 1, held-out prediction: the mechanistic arm has higher Spearman than the RF on every pathway total; the gap is large for Pyr-Int and Int-Int (about 0.7 vs 0.5 on raw counts) and small for Int-Pyr and Pyr-Pyr. Reason: the offline cross-validation below.
- Track 1, optimisation: both arms end in the same corner (dm.weight 1.0, days 25, highest density the soft check allows, large pyramidal count). Hit rate on T-PI and T-IP is 0 for both. Reason: the law is monotone, and the best observed row in 100 samples reaches 33 usable Pyr-Int pairs. This track will not separate the arms on optimisation, only on prediction and on runs needed.
- Track 2: the mechanistic arm reaches a first hit within its first 5 runs; the ML arm needs at least 10, because it has no training data in which `D_synmax` varies with the other parameters. Reason: synapse counts on the interneuron pathways follow `D_synmax`^1.6 (fitted on 3 points, predicted 2 more within 1%). Risk to this prediction: the exponent is known at one config and one seed only.
- Both tracks: held-out error on thresholded fractions (T-PI) stays poor for both arms unless the per-neuron model of idea 2 works. Reason: section 5, idea 2.

## 5. Breakthrough ideas, with offline tests run now

### Why the random forest fails on the weak targets

1. **The labels are thresholded small counts.** `usable_pyr_int` has median 1 and maximum 33; 30 of 100 rows are zero. The underlying raw Pyr-Int synapse count has mean 31. Thresholding throws away most of the signal.
2. **The structure is multiplicative.** Counts scale as (number of pre cells x number of post cells) x a density term x dm.weight^a x exp(b x days). A forest on seven raw inputs has to learn products from 100 rows.
3. **Input is concentrated on a few cells.** Incoming synapses per cell vary far more than distance explains (coefficient of variation of actual over kernel-predicted incoming input: 2.1-2.6 for Pyr-Int, against 0.15 expected from Poisson noise). A fraction-above-threshold label depends on that tail, which no aggregate model captures.
4. **The knob that moves these targets is not among the features.** `D_synmax` changes Pyr-Int synapses 13-fold (0.1 to 0.5); the whole seven-parameter box changes them much less.
5. **One seed.** The forest has seen no seed variation, which is 12-20% on totals.

### Idea 1. Low-dimensional scaling law on continuous labels (tested, positive)

Model M1: Poisson regression with log link on log(n_pre x n_post), log(volume), log(dm.weight), days, log(minsep). M2: the same with the first two exponents fixed at +1 and -1, leaving 3 free parameters. POIS7: Poisson regression on the seven raw parameters. RF7: the incumbent. Same folds for all (5-fold x 10 repeats); pooled out-of-fold R2 / Spearman:

| target | RF7 | POIS7 | M1 | M2 |
|---|---|---|---|---|
| usable_pyr_int | -0.07 / 0.33 | 0.20 / 0.43 | 0.29 / 0.48 | 0.43 / 0.50 |
| usable_int_int | 0.01 / 0.33 | 0.07 / 0.42 | 0.16 / 0.49 | 0.30 / 0.50 |
| frac_int_driven | 0.12 / 0.52 | 0.13 / 0.61 | 0.28 / 0.65 | - |
| strict frac_pyr_inhibited | 0.04 / 0.37 | 0.13 / 0.41 | 0.07 / 0.39 | - |
| usable_int_pyr | 0.51 / 0.77 | 0.71 / 0.85 | 0.64 / 0.82 | 0.53 / 0.77 |
| usable_conns2 | 0.65 / 0.80 | 0.74 / 0.87 | 0.73 / 0.89 | 0.27 / 0.82 |
| raw Pyr-Int synapses | 0.22 / 0.49 | 0.45 / 0.68 | 0.52 / 0.73 | 0.38 / 0.67 |
| raw Int-Int synapses | 0.19 / 0.44 | 0.32 / 0.60 | 0.40 / 0.65 | 0.18 / 0.61 |
| raw Int-Pyr synapses | 0.50 / 0.73 | 0.77 / 0.88 | 0.70 / 0.85 | -0.13 / 0.70 |
| raw Pyr-Pyr synapses | 0.86 / 0.91 | 0.94 / 0.96 | 0.91 / 0.94 | -0.34 / 0.76 |

Reading:
- The answer to "does a mechanistic fit beat the random forest on the weak targets" is yes, on every weak target except strict `frac_pyr_inhibited` (13 non-zero rows, nothing works). The size of the win is moderate: Spearman about 0.5 instead of 0.33.
- Switching to continuous labels helps every model (Pyr-Int: RF -0.07 to 0.22, M1 0.29 to 0.52).
- The fixed exponents of M2 are wrong for the well-measured pathways (fitted: 0.4-1.2 on the pair count, -0.2 to -0.9 on volume), and M2 loses there. It wins only where data are too noisy to fit exponents. So the right form is M1 with informative priors, not hard constraints.
- On the strong targets a plain Poisson model on raw parameters is as good as or better than M1. The gain over the forest comes mostly from "log-linear and smooth", less from the specific physics.
- Fold-level R2 on the two weak usable labels is negative for every model including the mean (label is heavy-tailed); pooled values and Spearman are the stable numbers.
- Achieved R2 is far below the Poisson ceiling (0.68-0.99), and the counts are overdispersed (dispersion 1.5-4 on interneuron pathways, 27-43 on Pyr-Pyr). Much variance is still unexplained.

Risk: 0.01 ridge was used; no negative-binomial fit (statsmodels missing); all on one seed.

### Idea 2. Per-neuron heterogeneity model for the thresholded targets (tested: the simple version fails; the fix is untested)

Test: fit a distance kernel (mean synapses per pair vs soma distance) on sim 133 and predict, on the soma positions of the other three seeds, how many interneurons get >= 13.84 nS.

| predictor | seed 1001 | seed 1002 | seed 1003 |
|---|---|---|---|
| actual | 6 | 8 | 5 |
| "same as sim 133" | 10 | 10 | 10 |
| kernel, independent pairs (Poisson or negative binomial) | 27 | 27 | 26.5 |

The independent-pair model is badly wrong: mean input is 45 synapses per interneuron against a threshold of 15, so it predicts all 27 fire, while in the real network a few interneurons collect most of the input. The missing structure is a per-cell gain (arbor size or orientation). A back-of-envelope gamma gain with the measured CV (2.2) and the measured mean gives about 10 of 27 for sim 133 (actual 10) and about 7.6 for seed 1003 (actual 5); this was computed by hand, not by script, and is not a validated result.

Expected gain: makes T-PI and seed spread predictable from two numbers per pathway (mean and per-cell CV). Cheap offline test still to do: fit the gain distribution on 3 seeds, predict the 4th, on all four fraction labels. Risk: the CV may depend on config (we have dumps at one config only).

### Idea 3. `D_synmax` as a calibrated analytic knob (tested within one seed, positive)

Kernel amplitude relative to D = 0.5, against (D/0.5)^1.6:

| D | law | Pyr-Int | Int-Pyr | Int-Int | Pyr-Pyr |
|---|---|---|---|---|---|
| 0.1 | 0.076 | 0.061 | 0.069 | 0.088 | 0.99 |
| 0.3 | 0.442 | 0.464 | 0.442 | 0.402 | 0.98 |
| 0.7 | 1.713 | 1.678 | 1.808 | 1.437 | 0.98 |
| 1.0 | 3.031 | 2.958 | 3.146 | 2.582 | 0.99 |

The distance shape is unchanged and only the amplitude moves, so `D_synmax` enters the law as one multiplicative term and can be inverted in closed form: D = 0.5 x (target / value at 0.5)^(1/1.6). Int-Int falls 15% below the law at 0.7 and 1.0. Expected gain: this is where the mechanistic arm should win clearly (Track 2). Not shown: the exponent at any other config, dm.weight or seed. Risk: no approved range.

### Idea 4. Few-run calibration and sequential design (tested, positive)

Learning curves: train on n random batch B rows, test on the rest (median Spearman over 100 draws).

| target | model | n=5 | n=10 | n=20 | n=40 | n=80 |
|---|---|---|---|---|---|---|
| usable_int_pyr | RF7 | 0.36 | 0.61 | 0.68 | 0.73 | 0.76 |
| | M1 | 0.56 | 0.73 | 0.79 | 0.82 | 0.81 |
| | M2 | 0.73 | 0.76 | 0.78 | 0.78 | 0.78 |
| usable_pyr_int | RF7 | 0.08 | 0.12 | 0.18 | 0.23 | 0.36 |
| | M1 | 0.18 | 0.36 | 0.44 | 0.47 | 0.52 |
| | M2 | 0.44 | 0.47 | 0.50 | 0.50 | 0.53 |
| usable_conns2 | RF7 | 0.35 | 0.56 | 0.65 | 0.75 | 0.83 |
| | M1 | 0.61 | 0.82 | 0.87 | 0.88 | 0.88 |
| | M2 | 0.84 | 0.84 | 0.83 | 0.82 | 0.81 |

The constrained law with 10 runs ranks configs as well as the forest with 80, on all three targets. This is the strongest evidence for the "reasoning proposes, a few runs calibrate" hybrid. Practical form: start with M2 priors, relax toward M1 as runs accumulate (at about 20). Risk: with 5 runs the free-exponent models are unstable (R2 strongly negative), so priors are needed, and ranking quality saturates at Spearman about 0.5 on the weak labels whatever n.

### Idea 5. Calibrate on small, cheap networks and extrapolate (tested, positive)

Train on the 53 rows with at most 84 neurons, test on the 47 larger ones:

| target | RF7 R2 | POIS7 R2 | M1 R2 |
|---|---|---|---|
| usable_conns2 | 0.55 | 0.66 | 0.79 |
| usable_int_pyr | 0.27 | 0.69 | 0.63 |
| usable_pyr_int | 0.16 | 0.18 | 0.18 (M2: 0.40) |
| raw Pyr-Pyr synapses | -0.23 | 0.73 | 0.78 |

The log-linear models extrapolate in size; the forest does not. A 40-neuron run costs about 71 s against 556 s for the 94-neuron working config, so calibration runs can be about 8 times cheaper. Risk: tested only within 40-100 neurons; beyond the cap is unknown.

### Idea 6. Per-pair connectome statistics in place of aggregate labels (tested, mostly negative)

- A geometry term computed from the sim 127 distance kernel plus dm.weight and days (3 parameters) beats the forest (usable_int_pyr R2 0.58 vs 0.44; usable_conns2 0.76 vs 0.61) but is no better than M1. The kernel adds nothing beyond n_pre x n_post and volume.
- Soma geometry explains almost none of the seed-to-seed spread: predicted totals vary 2-5% across placements, actual totals 12-20%; the kernel is no better than "same as sim 133" at predicting another seed.
- The useful part of the per-pair data is the per-cell heterogeneity it revealed (idea 2).

### Idea 7. Seed transfer as a random effect, and design with a margin (partly tested)

Seed spread cannot be predicted from soma positions (idea 6), and the kernel length scale itself varies between seeds (CV 0.19-0.32). Treat the seed as a multiplicative random effect with CV about 0.15-0.20 on totals and nominate configs with a margin of about 1.3 times the threshold. Not shown: whether the spread is the same at other configs; whether the law's exponents hold on other seeds (all batch B is one seed).

### Idea 8. Analytic inversion (tested: trivial inside the box)

The fitted law is monotone, so the unconstrained optimum is the corner: dm.weight 1.0, days 25, smallest volume (radius ~100, thickness ~20), large cell counts. M1 predicts 48 usable Int-Pyr and 36 usable Pyr-Int pairs there, against best observed 44 and 33. With the soft density and pyramidal-fraction checks, the optimum moves to about pyr 67, int 26, radius 137, thickness 36, dm.weight 1.0, days 25, predicted 31 and 14. M1 underpredicts the best observed rows (31 predicted for the row that gave 44). Consequence: in Track 1 no search method can do much better than "go to the corner"; the configuration problem only becomes interesting with `D_synmax` and with a functional target.

### What is not shown

- No live head-to-head: every comparison above is retrospective cross-validation on one seed.
- DiCE itself was not part of the offline comparison, only the forest it relies on.
- No model reaches the noise ceiling; the weak usable labels stay at Spearman about 0.5.
- The per-cell gain model (idea 2) and any `D_synmax` interaction with the other parameters are untested.
- No link from growth labels to recall behaviour is modelled; round 2 showed dynamics are the part reasoning predicts badly.
- Concurrency on the server is unmeasured.

## 6. Recommended plan, cost, go/no-go

| phase | content | NES runs | est. wall time | est. model cost |
|---|---|---|---|---|
| 0 | Finish offline work: per-cell gain test (idea 2), negative-binomial fit, pre-registration text, held-out config script | 0 | 1 h | ~$1-2 (cheap models), ~$1 Fable |
| 1 | Concurrency probe; send the `D_synmax` range request | 3 | 20 min | < $1 |
| 2 | Track 1 head-to-head, reduced: 10 runs per arm, 12 held-out x 2 seeds, top 3 per arm x 3 seeds | 62 | ~7 h | ~$3-5 cheap models, ~$2-3 Fable |
| 3 | Track 2 head-to-head (only with an approved range), reduced size as in section 3 | 50 | ~6 h | ~$3-4 cheap models, ~$2-3 Fable |
| 4 | Recall tests on the winning configs (existing engram design, STDP off) | ~6 | 1 h | ~$2 |

Cost figures are rough estimates from this session's pattern (monitoring a growth batch with a cheaper model, Fable only for the pre-registration, the model form and scoring); they are not measured. Total for phases 0-3 is on the order of $12-18, which fits the remaining November budget only if Fable use stays at the analysis steps.

**Go / no-go.**
- Go for phase 2 if phase 0 confirms that the mechanistic arm's held-out Spearman on raw Pyr-Int and Int-Int counts stays >= 0.15 above the forest under a negative-binomial fit (now: 0.73 vs 0.49 and 0.65 vs 0.44).
- Go for phase 3 only with a team-approved `D_synmax` range. Without it, report Track 1 and stop.
- Stop early in any phase if, after the first round of 10, the mechanistic arm's pre-registered held-out predictions are not better than the forest's on at least 3 of 4 pathway totals.
- The mechanistic arm "wins" if it has lower held-out error on at least 3 of 4 pathway totals with non-overlapping bootstrap intervals, or reaches hit rate >= 0.6 with at most half the runs the ML arm needs. Anything less is reported as a draw.
- Honest prior: a clear win on data efficiency and on Track 2; a modest win on Track 1 prediction; no win on Track 1 optimisation, because the optimum is a corner both arms find.
