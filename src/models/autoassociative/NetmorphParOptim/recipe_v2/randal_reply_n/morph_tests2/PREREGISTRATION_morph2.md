# PREREGISTRATION: morph_tests2, larger tissue + more cells × low attraction weight

Written 2026-11-25, before any growth. It will not be edited after launch; deviations go in DEVIATIONS.md.

## Why
In morph_tests:
- dm_weight 0.1 removed the axon ball (ball index 3,000 → 5) and raised interneuron reach (133 → 351 µm).
- Connection probability stayed high (Int→Pyr about 0.6), because the 120 µm disc is small compared with the arbors.
- Per-pair contacts fell below the Int→Pyr ≥ 4 bar.

Question: does a larger patch with more cells at the same cell density bring connection probability down to literature values? And does cell count or volume matter?

## Size ladder (constant cell density, disc shape, one slab)
Cells scale with volume, so N ∝ R² T. The interneuron fraction is held at E4's 20/116 = 17.2%.

| size | pyramidal | interneuron | radius µm | thickness µm | volume × | total cells/mm³ | pyramidal cells/mm³ |
|---|---|---|---|---|---|---|---|
| x1 (E4) | 96 | 20 | 120 | 30 | 1.000 | 85,472 | 70,736 |
| x1.5 | 144 | 30 | 147 | 30 | 1.501 | 85,437 | 70,706 |
| x2 | 192 | 40 | 170 | 30 | 2.007 | 85,176 | 70,491 |
| x3 | 288 | 60 | 200 | 32 | 2.963 | 86,541 | 71,620 |
| ctrl (fixed cells, larger disc) | 96 | 20 | 170 | 30 | 2.007 | 42,588 | 35,245 |

- **x3:** radius 200 is the hard maximum, so thickness goes 30 → 32 (within 20–50) to reach about ×3 volume. Density is +1.2%.
- **Against CA3 (`realism_tester/profiles/ca3_verified.json`):**
  - verified pyramidal density is 165,200–172,400 /mm³ (Jinno & Kosaka 2010, mouse CA3, stereology);
  - the unverified review value is 140,000 (Keller et al. 2018).

  Our ladder holds E4's density, about 0.42× the verified CA3 pyramidal density. Matching CA3 density would need about 2.4× more cells in the same volume, which is a different axis and is not tested here. The interneuron fraction of 17% is above the verified 7–12.5%.
- **Constant-density law:** N_pyr = 96 · (R² T)/(120² · 30) and N_int = 20 · (same factor). Check: 70.5–71.6k pyramidal/mm³ at every size.

## Bio limits: a copy, never the shared files
- `morph_tests2/bio/bio_check.py` and `morph_tests2/bio/bio_ranges.json` are copies of `cos/netmorph_work/bec/src/models/autoassociative/NetmorphParOptim/{bio_check.py, bio_ranges.json}`.
- The only change is `parameters.pyramidal.max` 128 → 300, with the note "Randal allowed >128 pyramidal (2026-11-25), morph_tests2 only".
- `gen_autonm_labels_mt2.py` (copied from `morph_tests/gen_autonm_labels_mt.py`) has the same single change in its internal `HARD_LIMITS` (`('In.pyramidal', 16, 128)` → `('In.pyramidal', 16, 300)`).
- All other limits stay: interneuron ≤ 128, radius 100–200, thickness 20–50, dm.weight 0.1–1.0, days 20–25, D_synmax as E4.
- The shared files are not edited.

## Arms
- **Sizes:** x1, x1.5, x2, x3 × dm.weight 0.9 (E4), 0.1 and 0.2.
- **Control:** ctrl at dm 0.1.
- **Seeds:** 66666, 77777, 88888 (x1 is expected to reproduce the morph_tests arbors exactly).
- **Total:** (4 × 3 + 1) × 3 = **39 growths**.
- Everything else is E4: `model_E4` from morph_tests, dendrite-node attraction, line-379-fixed build `wt/nes-linefix` (binary 2026-11-23).

## Scoreboard (realism tester, `--profile ca3_verified`)
- ball_index.axon.all;
- reach_max.axon.interneuron;
- conn_prob for the 4 pairs;
- syn_per_pair for the 4 pairs;
- recurrent inputs per pyramidal cell (`sources.pyramidal.from.pyramidal`, mean and median);
- targets and sources per cell;
- lengths.

**Capacity proxy (cheap, offline):** `capacity.py` is feas2.py generalised to N pyramidal cells, using the AMPA conductance matrix from each run's viz dump. It reports:
- strong pairs (≥ 4.125 nS);
- the maximum number of disjoint 4+4 and 4+2 memories (300 greedy restarts; sampled lower bound when the full enumeration is too large);
- the dominant eigenvalue of the pyramidal AMPA matrix.

## Success criteria (per size × dm arm, ≥ 2 of 3 seeds)
- **S1 (ball):** ball_index.axon.all ≤ 10. Literature tier ≤ 2 reported separately.
- **S2 (probability):** conn_prob Pyr→Pyr in [0.009, 0.10] (verified rat slice 0.92%, mouse slice 8.9%, Ecker model 0.10) AND Int→Pyr ≤ 0.375 (the Ecker model value 0.25, +50%).
- **S3 (reach):** reach_max.axon.interneuron ≥ 390 µm (the derived lower bound).
- **C1 (constraint):** syn_per_pair Int→Pyr ≥ 4.0. Pyr→Pyr per pair is also reported against the verified 1–2.
- **Arm success** = S1 & S2 & S3 & C1.

## Predictions (my probabilities)
1. **dm 0.9:** the ball persists at every size (ball index > 100 at all sizes; 80%). Interneuron reach grows with radius, roughly ~1.1 R (x3 reach 180–260 µm; 60%), because axons from the periphery travel to the centre.
2. **dm 0.9:** Pyr→Pyr p falls with size (x3 below x1 in every seed; 75%), but stays > 0.10 at x3 (60%). Int→Pyr per pair stays ≥ 4 (60%).
3. **dm 0.1:**
   - ball index ≤ 10 at every size (75%);
   - reach about 330–400 µm, independent of size (±15% of x1; 65%);
   - Int→Pyr per pair 1.5–2.2 at every size, so C1 fails (80%).
4. **dm 0.1:** Pyr→Pyr p falls with size, roughly ∝ 1/N once R exceeds the reach. x3 Pyr→Pyr in [0.009, 0.10] in ≥ 2 of 3 seeds (50%). Int→Pyr ≤ 0.375 at x3 (55%).
5. **Recurrent inputs per pyramidal cell at dm 0.1** rise with size while the reach exceeds the disc (x3 > x1 by ≥ 20%; 60%). At dm 0.9 they are roughly flat (within ±25%; 50%).
6. **Control (fixed 116 cells, double volume, dm 0.1):**
   - per-pair contacts below x1 dm 0.1 (lower dendrite density along the axon) (70%);
   - Pyr→Pyr p lower than x1 dm 0.1 (65%);
   - higher than x2 dm 0.1 (55%).

   Cell count, not volume, drives the absolute number of partners.
7. **dm 0.2:** values lie between dm 0.9 and dm 0.1 on ball, reach and per-pair contacts at every size (70%).
8. **No arm meets full success (80%).** The most likely blocker is C1 at dm 0.1 and S1 at dm 0.9.
9. **Capacity proxy (disjoint 4+4 memories):** at dm 0.9 it grows with N (x3 ≥ 2× x1 in median; 55%). At dm 0.1 it is ≤ 1 at every size (60%), because pairs ≥ 4.125 nS need several contacts.
10. **Growth cost:**
    - wall time per growth rises superlinearly with cell count, x3/x1 = 3–9× (60%);
    - peak NES RSS per instance rises about ∝ N (x3 instance ≤ 10 GB; 70%);
    - no NES or NetMorph failure at x3 (70%).
11. **Reproducibility:** x1 dm 0.9 and dm 0.1 reproduce the morph_tests A09 and A01 arbor lengths exactly for the 3 seeds (80%).

## Resource plan
- **Instances:** 9 new patched NES+API instances (`morph_tests2/instances/i0..i8`, ports 8200+10k … +4, own Output_BasePath on local disk), sharing the binary. Main NES 3156209 / API 1972355 and the shared patched 2768884/2769516 are not used.
- **Concurrency:** ≤ 3 growths per NES (`-batchlimit 3`), at most 27 concurrent growths. Expected about 18 cores of idle NES burn plus about 27 growth cores, ≤ 48.
- **Per seed (j = 0..2):**
  - instance 3j: one batch, x3 × {0.9, 0.1, 0.2};
  - instance 3j+1: one batch, x2 × {0.9, 0.1, 0.2};
  - instance 3j+2: batch 1, x1.5 × {0.9, 0.1, 0.2}; then batch 2, x1 × {0.9, 0.1, 0.2} + ctrl 0.1 (4 rows, at most 3 at once).
- **Between batches on one instance:** if NES RSS > 10 GB, the instance is restarted.
- **RAM guard:** `monitor.sh` logs every 60 s and writes STOP_NEW if used RAM > 240 GB. The driver starts no new batch while STOP_NEW exists; a running batch is not killed unless RAM > 250 GB.
- **Records:** NES_SIM_IDs and output folders go in batch logs and `runs.json`. Residents are deleted by `-deleteresident`. NetMorph output folders are deleted after scoring and the capacity proxy.

## Not done
No recall or simulation. No shared-file edits. No emails, git, pushes or Drive.
