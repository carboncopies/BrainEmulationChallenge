# Run 1 report (labels fix, bio limits, smoke rerun, 100-sample batch ABORTED)

## Outcome in one line
Labels + dm.weight fix + hard limits done and verified on 4 smoke samples. The 100-sample batch was started and ABORTED after ~9.5 min because
runs were far slower than the 3x-of-41 s/sample threshold. No batch labels exist, so step 5 (model rerun, needs >=20 rows) was NOT done.

## Changes (all in the scratch worktree; nothing committed)
- gen_autonm_labels.py
  - get_sample_data strips whitespace from column names (bug fix, see below).
  - Per-pair thresholds: -MINSYNAPSES default 1 (assumption; was 7 and gave all-zero labels). Per-pair targets = 1 x 0.98 nS (AMPA), 1 x 0.80 nS (GABA); still CLI args.
  - New aggregate labels (CLI: -PYRINT_AGG_TARGET_nS def 7.84, -INTPYR_AGG_TARGET_nS def 16.0, -INTPYR_AGG_WEIGHT def 0.5):
    - frac_int_driven = fraction of interneurons whose total incoming AMPA g_peak_sum from pyramidal cells >= 7.84 nS.
      Origin: LIFtest.py SUPERSYNAPSESONINT=8 x 0.98 nS (weight 1.0). Team/LIFtest-derived.
    - frac_pyr_inhibited = fraction of pyramidal cells whose total incoming GABA g_peak_sum from interneurons >= 16.0 nS.
      Origin: LIFtest.py SUPERSYNAPSESFROMINT=20 x 0.80 nS, but LIFtest applies it at weight 0.5. NES g_peak_sum is the UNWEIGHTED peak conductance, so this compares raw g_peak_sum with the full 16 nS (strict).
    - frac_pyr_inhibited_w05 (extra) = same but threshold 16 x 0.5 = 8 nS (weight-scaled equivalent). Assumption on how to compare; both recorded.
    - Per-neuron incoming AMPA/GABA sums, per-class counts/sums still stored in *-rawcounts.json.
    - The per-pair threshold (1 synapse-equivalent) is MY ASSUMPTION, not from LIFtest/docs.
  - assert_within_hard_limits() in extra_prep: refuses to run any sample outside the hard limits (dm.weight checked after rounding to the %.1f that is sent). dm.weight is rounded to 1 decimal.
  - Prints the directives actually appended per run.
- bio_ranges.json / bio_check.py: hard limits = days 20-25, pyramidal 16-128, interneuron 16-128, minsep 10-15, radius 100-200, thickness 20-50, dm.weight 0.1-1.0
  (all tagged docs). growth_F=0.39 and growth_nu0=0.00013889 recorded as fixed. Density (10k-50k/mm3) and pyramidal fraction (70-80 %) are now warnings (warn_* columns, still reported).
  New bio_check.assert_hard_limits(). Old limits were wrong vs the team's (pyramidal/interneuron upper 136, thickness upper 60).
- multi_target_optim.py: candidate/suggestion generator now samples the 7-parameter hard box (LHS), rounds dm.weight to 0.1, asserts hard limits on candidates and on suggested samples. test_pipeline.py bio test updated accordingly (passes; the full earlier tests passed with the exception of that one which was expected to change).

## dm.weight bug: was it ignored? YES
The sample sheets have header 'dm.weight ' (trailing space); extra_prep tested 'dm.weight' in cols, never matched, printed "Missing dm.weight column. Using default: 0.5" and sent 0.5 for every sample (old smoke log confirms). The base nesvbp-autoassociative file has dm_weight=0.2, so the appended directive (0.5) always overrode it.
interneuron was NOT affected (its header has no space), so interneuron counts were used correctly.
Verified after the fix from the run log: appended directives contain all_axons.axondm.dm_weight=0.5/1.0/0.2/0.9 for the 4 smoke samples (matching the sheet), and In.interneuron=16/16/24/24.
Effect (same sample params, smoke): Pyr->Pyr AMPA total g_peak_sum 847 (w=0.5) vs 1733 (w=1.0, previously 952 with w forced to 0.5); sample w=0.2: 472 (previously 832); w=0.9: 1220 (prev 634). So dm.weight scales synaptic strength roughly linearly, and ALL earlier labeled data (Phase0/Phase1 files, 'usable_conns2' etc.) were generated at dm.weight=0.5 regardless of the column; any model that used dm.weight as a feature learned nothing about it.
Also: pyramidal count is applied (base ARCHITECTURE_MODIFY writes In.pyramidal=32 first, later override wins; connectome shows 16 pyr + 16/24 int = 32/40 neurons, as expected).
Minor: connection counts for dm.weight=0.5 sample differ by 1-2 vs the earlier smoke (177 vs 178); not investigated (likely seed/run nondeterminism).

## Smoke rerun (4 samples, new file newlabels_smoke2.xlsx, rawcounts newlabels_smoke2-rawcounts.json, viz in viz_data_smoke2/; old newlabels_smoke.* untouched)
All 4 completed. pyr=16 each, int 16/16/24/24.
| run | dm.w | conns2 | pyr_int | int_pyr | int_int | frac_int_driven | frac_pyr_inhib(16nS) | frac_pyr_inhib_w05(8nS) |
|---|---|---|---|---|---|---|---|---|
| 0 | 0.5 | 33 | 0 | 0 | 0 | 0 | 0 | 0 |
| 1 | 1.0 | 71 | 5 | 9 | 2 | 0 | 0 | 0.125 |
| 2 | 0.2 | 12 | 0 | 1 | 0 | 0 | 0 | 0 |
| 3 | 0.9 | 41 | 0 | 6 | 0 | 0 | 0 | 0.0625 |
Gate: per-pair labels and frac_pyr_inhibited_w05 vary (not all identical/zero) -> gate passed on the stated criterion. Caveat: frac_int_driven and strict frac_pyr_inhibited are 0 for all 4 (max incoming AMPA onto an interneuron 0.98-4.9 nS vs 7.84; max GABA onto a pyramidal 2.4-11.2 nS vs 16). These smoke samples have the minimum pyramidal count (16), so aggregate inputs per cell are small; larger networks should raise them but this is untested.

## 100-sample batch: ABORTED (0 completed)
Samples: batch100_samples.xlsx. suggested_netmorph_samples.xlsx had 53/100 rows outside the hard limits (15 with pyramidal >128 [max 136], 48 with thickness >50 [max 59]). I dropped those 53 (not clipped, to avoid piling rows on the boundary), kept 47, and replaced 53 with LHS rows inside the hard box (column row_source says which). dm.weight rounded to 1 decimal (changed 79 rows' value, e.g. 0.15 -> 0.1/0.2, because Netmorph is sent %.1f). All 100 rows asserted within hard limits. Columns: 'dm.weight' (stripped) and 'interneuron' present. Neuron counts range 33-255.
Run: -batchlimit 2 -deleteresident, started 00:21. First two samples (165 and 139 neurons, days 24 and 21) had not completed after ~9.5 min (progress bar projected >8 h total), vs ~41 s/sample earlier (those were 32-40 neuron nets). That is far over the 3x (~123 s/sample) abort threshold, so my first SIGINT attempt silently did not stop it (pkill pattern miss); it was killed with SIGTERM at ~00:35 (about 14 min of runtime, still 0 completed). Server stayed responsive (HTTP 200). No failures were logged.
ANOMALY / CLEANUP: the two in-flight simulations (batch runs 0 and 1) were launched by me and may still be resident/running on the NES server; the aborted script did not record their IDs, so I did NOT try to delete anything (to avoid touching others' sims). Whoever owns the server may want to check for two simulations created around 00:21-00:22 on Nov 9.

## Not done / could not verify
- Step 5 (model R^2 per target, counterfactuals, sampling-need update): not run; only 4 labeled rows exist (<20) and no synthetic fallback was allowed.
- Per-class label distributions for the batch: n/a. Distributions on the 4 smoke samples are in the table above.
- Whether Netmorph really honours later-wins for repeated directives is inferred from outputs (neuron counts and dm.weight-dependent conductances match the later values), not from Netmorph docs.
- I could not confirm the runtime scaling model; 165-neuron samples take >9.5 min each with 2 concurrent (likely scales super-linearly with neuron count and days).

## Viz (step 6)
Three REAL new runs (smoke2 runs 1, 2, 3) converted to the viewer schema in viz/data/netmorph-smoke2-000{1,2,3}.json (NMDA connections omitted; notes field has params and labels). `npm test` in viz: ALL OK.

## Suggested next step (needs your decision)
Run the batch on smaller networks (e.g. pyramidal+interneuron <= ~60, which are within the hard limits) or accept hours of runtime (e.g. an overnight run for ~100 mid-size samples), or run a handful of mid-size samples (pyr ~64-128) first to see if frac_int_driven / frac_pyr_inhibited become non-zero and measure time per size.
