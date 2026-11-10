# Multi-target models on REAL batch B labels (100 samples), Nov 9 2026

Files (all in this directory): `merge_batchB.py` -> `batchB_labels_all.xlsx`; `batchB_models.py` (CV + optimizer; `python batchB_models.py cv|optimize`);
`batchB_cv_results.json`; `suggested_configs_batchB.xlsx`; new tests in `test_pipeline.py` (class TestBatchBRealLabels). Nothing committed, nothing deleted, no simulations or server calls.

## 1. Data merge
- 4 parts -> 100 rows, `sample` 1-100 (part 1 numbered 1-10 by order). No duplicate samples, no duplicate NES_SIM_ID (22-122; id 62 is unused, gap between part 2 and 3, not explained here).
- rc: parts 3-4 (60 rows) all rc=0. Parts 1-2 (40 rows) have no `rc` column; their reports state all completed with no cap hits, so rc is NaN for them (not verified from the file).
- Missing labels: none. All 100 rows pass `assert_hard_limits`; sampled sizes pyr 16-70, int 16-30.
- Label non-zero counts: pyr_int 70, int_pyr 96, int_int 53, frac_int_driven 53, frac_pyr_inhibited_w05 49, strict frac_pyr_inhibited 13 (weak), conns2 100.

## 2. Cross-validation (5-fold x 10 repeats, RF 500 trees, all 7 sample parameters as features, all 100 rows incl. zeros)
Baseline = predicting the training-fold mean. PI = 2.5/97.5 percentile of per-tree predictions, coverage measured on held-out rows.

| target | non-zero | RF R2 (mean ± sd over folds) | RF MAE | baseline MAE | 95% PI coverage | mean PI width | Poisson-GLM R2 (cross-check) |
|---|---|---|---|---|---|---|---|
| usable_pyr_int | 70 | -0.64 ± 1.81 | 2.99 | 2.96 | 0.96 | 14.7 | -0.17 |
| usable_int_pyr | 96 | 0.46 ± 0.21 | 3.98 | 6.30 | 0.94 | 20.1 | 0.67 |
| usable_int_int | 53 | -0.46 ± 0.79 | 1.23 | 1.16 | 0.95 | 5.35 | -0.32 |
| frac_int_driven | 53 | 0.08 ± 0.38 | 0.033 | 0.040 | 0.95 | 0.135 | 0.15 |
| frac_pyr_inhibited_w05 | 49 | 0.46 ± 0.25 | 0.015 | 0.026 | 0.95 | 0.066 | 0.60 |
| usable_conns2 (Pyr-Pyr) | 100 | 0.58 ± 0.23 | 101 | 170 | 0.91 | 533 | 0.69 |
| frac_pyr_inhibited (strict) - WEAK | 13 | -0.56 ± 1.13 | 0.0049 | 0.0056 | 0.96 | 0.020 | -0.01 |

Honest reading:
- Three targets have real but moderate skill: usable_int_pyr, frac_pyr_inhibited_w05, usable_conns2 (R2 0.46-0.58, MAE 30-40 % below baseline). Fold-to-fold sd is 0.2, so with n=100 the true R2 is uncertain.
- usable_pyr_int, usable_int_int, frac_int_driven and strict frac_pyr_inhibited have NO usable skill: RF R2 <= 0.1, MAE about equal to the mean baseline. They are zero-inflated small counts (pyr_int median 1, max 33). Trying RF min_samples_leaf=5 and a Poisson GLM did not rescue them (best R2 about 0.15 for frac_int_driven). Do not use their predictions to rank configurations.
- The 95 % PIs reach ~95 % coverage mostly because they are very wide (comparable to the label's own range); for conns2 coverage is 0.91, i.e. slightly under-covering. These are ensemble-spread intervals, not noise-aware predictive intervals.
- A simple log-linear Poisson GLM on the 7 parameters beats the RF for the three skilled targets (R2 0.60-0.69), i.e. the relationships are close to smooth/monotone and the RF mostly adds variance at n=100. RF is kept as the primary model (existing tooling, gives the PIs); the Poisson prediction is included as a cross-check column in the suggestions.

## 3. Is dm.weight informative now? YES, strongly.
| target | Spearman rho with dm.weight | RF impurity importance of dm.weight | next most important |
|---|---|---|---|
| usable_int_pyr | +0.77 | 0.56 | radius 0.15 |
| frac_pyr_inhibited_w05 | +0.75 | 0.59 | days 0.13 |
| usable_conns2 | +0.68 | 0.41 | radius 0.25, pyramidal 0.20 |
| frac_int_driven | +0.60 | 0.36 | radius 0.15 |
| usable_pyr_int | +0.44 | 0.19 | radius 0.22 |
| usable_int_int | +0.41 | 0.21 | thickness 0.19 |
Held-out permutation importance (drop in R2) is also largest for dm.weight on every target (noisy for the weak ones). Secondary effects: days positive (rho 0.2-0.3), radius negative (denser net, rho -0.15 to -0.29), pyramidal positive for conns2 (0.32). interneuron count, minneuronseparation and thickness are near-uninformative in this data. Consistent with the Run 1 finding that dm.weight scales synaptic strength roughly linearly (and that earlier Phase0/1 data could not show this because dm.weight was forced to 0.5). Consequence: optima sit at the dm.weight upper limit (0.8-1.0).

## 4. Optimizer
- Search space: 60 000 scrambled-Sobol points in the 7-D box = HARD limits intersected with the sampled size range (pyr 16-70, int 16-30); integers rounded, dm.weight to 0.1. `assert_hard_limits` run on the whole candidate set and on the 20 suggestions; sizes asserted inside the sampled range.
- Models: RF 2000 trees, fit on all 100 rows.
- Best single-target predictions (sheet `best_single_target`, RF mean, 95 % tree-PI): pyr_int 24.7 [1, 33] (params pyr 70, int 22, days 25, dm 0.9); int_pyr 34.7 [8, 44] (dm 1.0); int_int 8.6 [0, 12]; frac_int_driven 0.18 [0.03, 0.24] (dm 0.7); frac_pyr_inh_w05 0.12 [0.03, 0.14]; conns2 1021 [473, 1200]; strict frac_pyr_inh 0.05 [0, 0.07]. The pyr_int / int_int / frac_int_driven / strict optima are NOT reliable (no CV skill; they lie on the extremes of the observed range) and are listed only for completeness.
- 20 joint suggestions (sheet `suggestions`, ids B01-B20): chosen to maximize the joint score = min over the 3 skilled targets of (RF mean / 75th percentile of observed non-zero label: int_pyr 13, frac_pyr_inh_w05 0.062, conns2 460), greedy-diverse (min standardized distance 0.15). Restricted to the pool with no soft-bio warnings (density 10-50k/mm3 and pyramidal fraction 70-80 %; only 424 of 60 000 candidates qualify, so pyramidal fraction is ~0.70 in all). Typical suggestion: dm.weight 0.8-1.0 (mostly 0.9-1.0), minneuronseparation 15 (upper limit; the soft-clean pool forces it), pyr 46-68, int 20-29, days 21-25, radius 105-190, thickness 24-50. Predictions (RF mean, 20 configs): int_pyr 17-25 connections, frac_pyr_inh_w05 0.07-0.10, conns2 477-833; PIs per config in the sheet (e.g. B01: int_pyr 25 [7, 44], w05 0.08 [0.00, 0.14], conns2 721 [364, 925]). Poisson cross-check agrees within roughly 0-50 % (generally Poisson is higher).
- The suggestions' joint scores (1.04-1.36) are below the best OBSERVED rows (joint 1.3-2.0), because the model-mean is smoothed and the soft-clean filter excludes dense corners. Predicted values are therefore not higher than what the batch already contains; the suggestions mainly identify a region (high dm.weight, dense but in-range, large-ish pyramidal count) rather than a new record. Each config's `nn_dist_std` (distance to the nearest training point in standardized units, typically 0.8-2.5) is in the sheet.
- The unskilled targets for these configs (pyr_int 2.8-8.4, int_int, frac_int_driven, strict frac_pyr_inh 0.005-0.03) are listed with PIs but are not guaranteed and were not optimized.

## 5. Proven vs inferred
PROVEN (directly observed in the 100 real Netmorph runs / by code check):
- The 100 labels, their ranges and zero-inflation; all parameters of the 100 runs and of the 20 suggestions are inside the hard limits (asserted).
- dm.weight is strongly and monotonically associated with Int-Pyr, Pyr-Pyr, frac_pyr_inhibited_w05 and frac_int_driven in this design (Spearman 0.6-0.77; design near-orthogonal, dm.weight uncorrelated with size and density, |r|<0.1).
- Held-out (CV) performance numbers in the table.
INFERRED (not verified by any simulation):
- That the suggested configs would produce the predicted labels; none was simulated. Predictions are RF/Poisson extrapolations/interpolations from n=100, R2 about 0.5-0.6 at best, intervals wide.
- Causal/mechanistic statements (e.g. that radius reduces connectivity through density) are correlational.
- Pyr-Int, Int-Int and strict-inhibition optima: unsupported.
- Interactions (e.g. high dm.weight AND large size) are only weakly constrained: few rows at dm.weight >= 0.9 and large networks.
- The aggregate thresholds (7.84 nS, 16 nS, w05 = 8 nS) and the per-pair threshold (1 synapse equivalent) are the Run 1 assumptions; frac_pyr_inhibited_w05 depends on the weight-scaling assumption.
- Rows 1-40 rc inferred as 0 from the part reports.

## 6. Suggested next step
Simulate ~5-10 of the 20 suggestions (cheap, ~5-8 min each) and compare to the predicted values/PIs: that is the real test. For pyr_int / int_int, collect more samples with high dm.weight and larger networks or define a less zero-inflated label (e.g. total conductance instead of usable counts).

## Tests
`python -m unittest test_pipeline` -> 8 tests OK (6 earlier + 2 new: real batch label merge/limits; candidate generator inside hard limits and size range).
