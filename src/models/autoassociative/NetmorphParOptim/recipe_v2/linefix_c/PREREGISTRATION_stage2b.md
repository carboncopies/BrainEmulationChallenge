# Preregistration addendum, linefix_c Stage 2 batch 2 (S1 and V3 with 30 interneurons). Written 2026-11-16 before launch; not to be edited after launch.
Ledger task tmwidgz0z. John approved running batch 2 although the batch 1 condition was not cleanly met (s31415 was a new realisation). PREREGISTRATION_stage2.md is unchanged; its batch 2 table stands for seed 16180. This file adds seed 27182 and the run mechanics.

## Runs (patched build, API port 8010; 96 pyramidal + 30 interneurons; pyramidal D 0.0175; interneuron D 0.04 on all three interneuron pairs)
1. S1n30 seed 16180. 2. V3n30 seed 16180. 3. S1n30 seed 27182. 4. V3n30 seed 27182.
Runs 1 and 2 start first. Runs 3 and 4 start only when fewer than 3 growth processes (any grow_pv*.py on the machine, including other workers') are active. All else as batch 1 (days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9; S1 / V3 arbor settings). Inside bio_ranges.json.

## Predictions
Seed 16180: the batch 2 table of PREREGISTRATION_stage2.md (S1n30: probability 0.26-0.35, Pyr->Pyr per pair 1.8-2.1, Int->Pyr 7.1-8.7, Pyr->Int 2.3-2.8, drivable 10-17 of 30, A 62-72%; V3n30: 0.27-0.36, 2.0-2.3, 6.6-8.0, 3.0-3.6, 13-20, 62-72%).
Seed 27182 (no node files for any 30-interneuron S1/V3; wider ranges because batch 1 showed my two-seed ranges were too narrow for a third seed):
| quantity | S1n30 s27182 | V3n30 s27182 |
|---|---|---|
| Pyr->Pyr connection prob. | 0.22-0.36 | 0.22-0.36 |
| Pyr->Pyr syn per connected pair | 1.75-2.2 | 1.85-2.35 |
| Int->Pyr per connected pair | 6.0-9.0 | 5.8-8.4 |
| Pyr->Int per connected pair | 2.2-4.8 | 2.8-3.9 |
| drivable 8-cell of 30 | 9-18 | 12-20 |
| A (reported only) | 60-74% | 60-74% |
Expectation: these are scaled from 48-interneuron runs with V1's 48->30 ratios, and a 30-interneuron network is a different realisation of the pyramidal network too, so I expect about one item in four to fall outside its range.

## Success bar (ranking B; A reported, not gated)
1. Pyr->Pyr connection probability 0.1-0.3. 2. Pyr->Pyr synapses per connected pair 1.9-4.5. 3. Int->Pyr per pair 4-9. 4. Pyr->Int per pair 1.5-4.5. 5. Drivable 8-cell >= 10 of 30 (proportional bar chosen by John on 2026-11-15; raw counts reported). 6. Nothing outside bio_ranges.json.
Expected: about 40% per run to pass bar 1; S1n30 about 50% to pass bar 2 (S1 has the fewest synapses per connected pair); bars 3-6 expected to pass, with S1n30 Int->Pyr the closest to its limit (9).
