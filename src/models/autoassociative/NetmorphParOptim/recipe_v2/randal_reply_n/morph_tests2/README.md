# morph_tests2: larger tissue + more cells × low attraction weight

Date: 2026-11-25. Follow-up to `../morph_tests/`.
- Preregistration: `PREREGISTRATION_morph2.md`, written before growth and not edited since.
- Deviations: `DEVIATIONS.md` (N1–N3; none changes the design or the criteria).
- Full tables: `results_tables.md`; machine-readable results: `results.json`, `runs.json`, `capacity.json`.

## Bottom line
1. **No arm meets the preregistered success criteria** (predicted, 80%). Pyr→Pyr connection probability never enters the 0.9–10% band. The lowest is x3 at dm 0.1: 0.136 in all 3 seeds.
2. **Larger tissue lowers connection probability, but slowly.** At constant density, tripling cells and volume (116 → 348 cells) takes Pyr→Pyr p:
   - from 0.29 to 0.16 at dm 0.9 (about N^-0.53);
   - from 0.21 to 0.14 at dm 0.1 (about N^-0.38).

   Extrapolating to the largest disc the hard limits allow at this density (R200, T50: about 444 pyramidal + 93 interneuron cells; that would need the pyramidal max raised to about 450) gives p ≈ 0.12–0.13. That is still above 0.10. **Size alone cannot reach the literature band within the current hard limits.**
3. **The low-dm benefits hold at every size, and so does their cost.** At dm 0.1, ball index is 5–11 (against 1,700–3,600 at dm 0.9) and interneuron reach is 362–399 µm. At x3, reach passes the 390 µm bar in 3 of 3 seeds. But Int→Pyr synapses per pair stay at 1.6–1.8 (bar ≥ 4), and the capacity proxy is 0 at every size.
4. **dm 0.9 per-pair contacts also fall with size.** Int→Pyr goes from 4.3 at x1 to 3.0 at x3, so even the baseline loses C1 at x3.
5. **Volume vs cell count (control: 116 cells in the x2 disc, dm 0.1).**
   - Pyr→Pyr p (0.163) is about the x2 value (0.159). Connection probability is set by volume and geometry.
   - Recurrent inputs per pyramidal cell (15.5) are half of x2's (30.3). The absolute number of partners is set by cell count.
6. **Cost.**
   - Growth time scales as about **N^2.1** (x3: 7.7 h per growth with 27 growths running at once).
   - NES RSS stays low: peak 7.3 GB on an instance running three x3 growths.
   - No NES or NetMorph failure at any size (39/39 completed, 0 failed).
   - The practical breaking points are the parameter hard limits (radius ≤ 200) and wall time, not RAM or crashes.

## Design (as preregistered)
Constant cell density, disc shape, one slab. The interneuron fraction is held at 17.2%. All other parameters are E4 (`model_E4`, line-379-fixed build `wt/nes-linefix`, dendrite-node attraction).

| size | pyramidal + interneuron | R µm | T µm | pyramidal/mm³ |
|---|---|---|---|---|
| x1 (E4) | 96 + 20 | 120 | 30 | 70,736 |
| x1.5 | 144 + 30 | 147 | 30 | 70,706 |
| x2 | 192 + 40 | 170 | 30 | 70,491 |
| x3 | 288 + 60 | 200 | 32 | 71,620 |
| ctrl | 96 + 20 | 170 | 30 | 35,245 |

- **Arms:** 4 sizes × dm.weight {0.9, 0.1, 0.2} + ctrl at dm 0.1, seeds 66666/77777/88888. That is **39 growths**, and all completed.
- **Density check:** the tester's `cells_per_volume` matched the design: 85.2–86.5k cells/mm³, ctrl 42.6k.
- **Density scaling law:** N ∝ R²T, holding E4's density.
  - E4's pyramidal density is about 0.42× the verified CA3 density in `profiles/ca3_verified.json` (165–172k/mm³, Jinno & Kosaka 2010).
  - The 17% interneuron fraction is above the verified 7–12.5%.
  - Matching CA3 density is a separate axis, not tested here.

## Bio limits: what changed (copies only)
The shared files were not edited.
- **`bio/bio_ranges.json`:**
  - copy of `cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim/bio_ranges.json`;
  - one change: `parameters.pyramidal.max` 128 → **300**;
  - note appended: "morph_tests2 COPY: max 128 -> 300 (Randal allowed >128 pyramidal, relayed by John 2026-11-25; morph_tests2 only)".
- **`bio/bio_check.py`:** byte-identical copy. `run_instance.py` asserts that this copy is the one imported, and calls `assert_hard_limits` on every sub-batch.
- **`gen_autonm_labels_mt2.py`** (copy of `../morph_tests/gen_autonm_labels_mt.py`):
  - `HARD_LIMITS ('In.pyramidal', 16, 128)` → `(…, 16, 300)`;
  - timing prints `NETMORPH_OUT … t=`, `NETMORPH_DONE`, `CHECK_DONE`.

  The repo `gen_autonm_labels.py` was not touched.

## Results (median over 3 seeds; per-seed values in `results_tables.md`)

| arm | ball axon | Int reach max µm | p P→P | p I→P | syn/pair P→P | syn/pair I→P | rec. inputs/pyr mean (median) | strong pairs | disjoint 4+4 / 4+2 |
|---|---|---|---|---|---|---|---|---|---|
| x1 dm0.9 | 3209 | 131 | 0.293 | 0.534 | 1.93 | 4.27 | 27.8 (17) | 173 | 1 / 3 |
| x1.5 dm0.9 | 2691 | 161 | 0.225 | 0.435 | 1.80 | 3.48 | 32.2 (15.5) | 246 | 1 / 3 |
| x2 dm0.9 | 1742 | 174 | 0.186 | 0.334 | 1.93 | 3.59 | 35.5 (8) | 411 | 1 / 3 (LB) |
| x3 dm0.9 | 1721 | 196 | 0.163 | 0.346 | 1.63 | 3.00 | 46.8 (15.5) | 417 | 1 / 2 (LB) |
| x1 dm0.2 | 21 | 250 | 0.273 | 0.653 | 1.33 | 2.24 | 26.0 (24) | 6 | 0 / 0 |
| x1.5 dm0.2 | 32 | 272 | 0.223 | 0.591 | 1.26 | 1.95 | 31.8 (26.5) | 5 | 0 / 0 |
| x2 dm0.2 | 56 | 285 | 0.191 | 0.465 | 1.31 | 2.00 | 36.5 (31) | 72 | 0 / 0 |
| x3 dm0.2 | 95 | 297 | 0.158 | 0.435 | 1.22 | 1.81 | 45.4 (36.5) | 33 | 0 / 0 |
| x1 dm0.1 | 5.1 | 362 | 0.207 | 0.549 | 1.18 | 1.80 | 19.6 (20) | 1 | 0 / 0 |
| x1.5 dm0.1 | 6.3 | 376 | 0.182 | 0.513 | 1.15 | 1.67 | 26.1 (24.5) | 1 | 0 / 0 |
| x2 dm0.1 | 7.8 | 378 | 0.159 | 0.441 | 1.21 | 1.60 | 30.3 (28) | 35 | 0 / 0 |
| x3 dm0.1 | 10.8 | 399 | 0.136 | 0.400 | 1.15 | 1.56 | 39.1 (33.5) | 26 | 0 / 0 |
| ctrl dm0.1 | 7.0 | 381 | 0.163 | 0.466 | 1.14 | 1.62 | 15.5 (13.5) | 0 | 0 / 0 |

- **Tester:** `realism_tester --profile ca3_verified`, run per arm. The reports are in `reports/<arm>/`.
- **Capacity proxy:** `capacity.py`, which is feas2.py generalised to N pyramidal cells (pair threshold 4.125 nS; disjoint cue sets by 300 greedy restarts).
  - It reproduces headline feas2 on morph_tests A09.
  - "LB" means sampled (3e6 random cue sets), so the value is a lower bound.
- **Dominant eigenvalue:** the full pyramidal AMPA matrix grows with N at every dm (dm 0.9: 42–63 → 69–77 nS; dm 0.1: 21–26 → 44–45 nS). This is driven by more weak partners, not by strong pairs.
  - The eigenvalue of the strong-pair submatrix is 0 in most large or low-dm runs, because the strong graph has no cycles.

### Preregistered criteria (seeds passing, out of 3)
- **S1 (ball ≤ 10):** 3/3 at dm 0.1 for x1, x1.5, x2 and ctrl. 0/3 at x3 dm 0.1 (10.4–11.0, just over the bar). 0/3 at dm 0.2 and dm 0.9.
- **S2 (probability):** 0/3 everywhere.
- **S3 (reach ≥ 390):** 3/3 only at x3 dm 0.1; 1/3 at ctrl.
- **C1 (Int→Pyr per pair ≥ 4):** at most 2/3 (x1 dm 0.9); 0/3 at x3 dm 0.9 and at all low-dm arms.
- **Pyr→Pyr per pair in 1–2:** met almost everywhere.
- **Success:** none.

### Predictions, scored

| # | prediction | outcome |
|---|---|---|
| 1 | dm 0.9: ball > 100 at all sizes; reach ≈ 1.1 R, x3 180–260 | **right**. Ball 1,700–3,200. Reach/R = 1.09, 1.10, 1.02, 0.98; x3 196 |
| 2 | dm 0.9: P→P p falls (x3 < x1 every seed); stays > 0.10; I→P/pair ≥ 4 | right, right, **wrong** (x3 3.0) |
| 3 | dm 0.1: ball ≤ 10 all sizes; reach 330–400 ±15% of x1; I→P/pair 1.5–2.2 | **wrong** (x3 10.8, narrowly), right (362→399, +10%), right |
| 4 | dm 0.1: P→P p ∝ 1/N; x3 in band; I→P ≤ 0.375 at x3 | wrong (only N^-0.38), wrong (0.136), wrong (0.400) |
| 5 | recurrent inputs at dm 0.1 rise ≥ 20%; flat at dm 0.9 | right (+99%), **wrong** (+68%) |
| 6 | ctrl: per-pair below x1 dm 0.1; p below x1; p above x2 | right (1.62 vs 1.80), right (0.163 vs 0.207), right, marginally (0.163 vs 0.159) |
| 7 | dm 0.2 lies between dm 0.9 and dm 0.1 on ball, reach, per-pair | right at every size. Not predicted: dm 0.2 has the highest I→P p and the most inputs per cell |
| 8 | no arm succeeds | right. But the universal blocker is S2, which I had not named |
| 9 | capacity at dm 0.9 ×2 by x3; ≤ 1 at dm 0.1 | wrong (median 1 → 1), right (0 everywhere) |
| 10 | time x3/x1 3–9×; x3 instance ≤ 10 GB; no failure | wrong (10.2×), right (7.3 GB peak), right |
| 11 | x1 reproduces morph_tests exactly | **wrong as stated.** 6 of 9 runs had lengths identical to 4 significant figures; 3 runs (88888 dm 0.9/0.1, 77777 dm 0.2) differ by ≤ 3% in length and p. Nondeterminism in NetMorph runs; the conclusions are unaffected |

## Cost and scaling

| size | cells | growth time median (s) | per-instance NES RSS after batch (GB) |
|---|---|---|---|
| x1 | 116 | 2,718 | — (shares an instance with x1.5) |
| x1.5 | 174 | 5,922 | 2.3–2.6 |
| x2 | 232 | 13,763 | 3.2–3.3 |
| x3 | 348 | 27,710 | 4.9–5.1 (peak 7.3) |
| ctrl | 116 | 2,623 | — |

- **Growth time:** fit `growth_s = 0.106 · N^2.14` over all non-control runs (N = total cells). These are contended timings: up to 27 growths running at once, 3 per NES. Extrapolated to 537 cells (the R200/T50 maximum at this density), that is about 20 h per growth.
- **Control:** ctrl (116 cells in a double volume) grows as fast as x1. Time is driven by cell count, not volume.
- **RAM:**
  - NES RSS grows about linearly with cells and is not fully released between sub-batches (x1.5 then x1 on the same instance leaves 4.4 GB).
  - No instance came near the 10 GB restart threshold, so no restarts happened.
  - Machine used-RAM (all users) ranged 93–134 GB; STOP_NEW never fired.
- **CPU:** our NES processes averaged about 33 cores (peak 36) by ps.
- **Where it breaks:** nothing broke up to 348 cells (1 transient status-poll comms hiccup, recovered). The binding limits are:
  1. hard parameter limits: radius ≤ 200 forces thickness up for larger sizes, and the pyramidal max needs raising above 300 beyond x3;
  2. the roughly quadratic wall time.

## Generator / batch notes
- The run pattern is the same as `../morph_tests/` (README there): Randal's BatchRun via `gen_autonm_labels_mt2.py -deleteresident -batchlimit 3`, one samples.xlsx per sub-batch.
- **Sheet columns:** Randal's 7 columns, plus `arm`, `size` and `randomseed` (read only by the mt copy).
- **Records:** NES_SIM_IDs and output directories are in `runs.json`. All 39 residents were deleted (39 "Deleted resident" lines).
- **Cleanup:** the NetMorph output folders (`instances/i*/out/Admonishing`, about 8 GB) were deleted after scoring. The viz dumps in `batch_*/viz/` (a few MB) are kept for re-scoring and the capacity proxy.
- **Parser gotcha (N2):** tqdm shares lines with prints, so parse logs with `re.search`, not `re.match`.
- **Instances:** 9 instances (ports 8200+10k) were used and are now stopped. Main NES 3156209 / API 1972355 and the shared patched 2768884/2769516 were not used and are still running.

## Files

| file | purpose |
|---|---|
| `run_instance.py` | per-instance driver (plan, RSS restart, STOP_NEW, bio assert) |
| `inst.sh`, `setup_instances.sh` | instance start/stop and setup |
| `monitor.sh` | resource monitor |
| `analyze2.py` | scoring: tester, capacity, criteria, cost fit |
| `capacity.py` | capacity proxy |
| `batch_i<k>_b<b>/` | samples.xlsx, launch.json, run.log, result.txt, viz/ |
| `monitor.log`, `monitor_flags.log`, `instance_events.log` | resource and run logs |
| `reports/<arm>/` | tester reports |

## Suggested next steps (not done)
1. Probability needs more than size. Candidates:
   - lower D_synmax for P→P, which cuts p and per-pair together, so C1 needs separate care;
   - an intermediate dm (0.3–0.5), to look for a C1-preserving point;
   - more pyramidal density at a fixed disc, which is the CA3-density axis.
2. If size is pushed further, raise the pyramidal max to about 450 in the copy and budget about 20 h per growth.
