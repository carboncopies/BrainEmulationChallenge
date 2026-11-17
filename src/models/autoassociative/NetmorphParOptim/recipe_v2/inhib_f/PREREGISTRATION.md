# inhib_f PREREGISTRATION (2026-11-17, written before any launch; not edited after launch)
Task: replicate the three in-band configurations from inhib_e on seeds 27182 and 31415. Configurations (patched build, pyramidal D 0.0175, 96 pyramidal cells, all else as inhib_e): **E4** V1, 20 interneurons, interneuron D 0.03 on all three interneuron pairs; **E5** V3, 24 interneurons, D_int 0.02; **E6** V3, 20 interneurons, D_int 0.02. 6 growth runs. Seed 16180 comes from inhib_e (E4 passed all seven bars; E5 failed bars 2 and 3; E6 failed bar 3). Bars as in inhib_e/PREREGISTRATION.md: 1 Pyr->Pyr p 0.1-0.3; 2 Pyr->Pyr syn per connected pair 1.9-4.5; 3 Int->Pyr per connected pair 4-9; 4 Pyr->Int per connected pair 1.5-4.5; 5 drivable 8-cell >= one third of interneurons (7 of 20, 8 of 24); 6 inside bio_ranges.json; 7 A = Int->Pyr/(Int->Pyr + Pyr->Pyr) 25-50%.

## How the predictions were made
Central value = the seed-16180 result from inhib_e, multiplied by the seed-to-seed ratio seen for the V1n30 networks in linefix_c Stage 2 (seed 27182 / 16180: Pyr->Pyr synapses x0.97, p x0.96, per pair x1.01, Int->Pyr synapses x0.81, Int->Pyr per pair x0.87, Pyr->Int per pair x1.16, drivable x1.06; seed 31415 / 16180: x1.18, x1.23, x0.96, x1.06, x0.91, x1.09, x1.00). Ranges: A +-5 points, Int->Pyr per pair +-10%, Pyr->Int per pair +-12%, p +-0.04, Pyr->Pyr per pair +-0.15, drivable +-3 cells. Arbors may not reproduce (linefix_b/c: 2 of 5 seeds differed, 5-10% shifts) and these are new configurations, so the ranges are wide; the shifts are from 3 existing runs only.

## Predictions (central; range in brackets as above)
| run | p | Pyr->Pyr per pair | A (%) | Int->Pyr per pair | Pyr->Int per pair | drivable | bars predicted to FAIL at the central value | P(all 7 bars pass) |
|---|---|---|---|---|---|---|---|---|
| E4 s27182 | 0.227 | 1.95 | 42.3 | 3.59 | 4.67 | 11 of 20 | 3 (Int->Pyr), 4 (Pyr->Int) | 10% |
| E4 s31415 | 0.290 | 1.85 | 44.1 | 3.77 | 4.38 | 10 of 20 | 2, 3 (p 0.29 within 0.01 of the bar 1 limit) | 6% |
| E5 s27182 | 0.229 | 1.86 | 44.0 | 3.19 | 3.04 | 12 of 24 | 2, 3 | 3% |
| E5 s31415 | 0.292 | 1.77 | 45.8 | 3.35 | 2.85 | 11 of 24 | 2, 3 | 2% |
| E6 s27182 | 0.252 | 2.07 | 36.2 | 3.14 | 4.68 | 12 of 20 | 3, 4 | 2% |
| E6 s31415 | 0.321 | 1.97 | 37.9 | 3.30 | 4.39 | 11 of 20 | 1, 3 | 1% |
Across all six runs: bars 5, 6 and 7 pass in all six (A 36-46%, drivable above one third, 90% each); bar 3 (Int->Pyr per pair >= 4) fails in at least 5 of 6 (85%); zero-input interneurons 0-3 per run.
## Per-configuration probability of passing all seven bars on all three seeds (seed 16180 as measured in inhib_e)
- E5: 0% and E6: 0%. Each already fails a bar on seed 16180 (E5 bars 2 and 3; E6 bar 3), so neither can pass on 3 of 3.
- E4: 1% (it passed on 16180; chance of passing on both new seeds about 10% x 6%, with the seeds treated as independent).
- At least one configuration passes all seven on 3 of 3 seeds: 1%. Hence the dynamics check (dyn2.py on a seed-16180 E4 network) is expected NOT to be run (99%); it runs only if a configuration passes on all three.
## Scoring rule
HIT inside the stated range, PARTIAL up to 25% beyond its edge, MISS otherwise; bars predicted at the central value, scored pass/fail per run. Pooled table over 3 seeds uses inhib_e for seed 16180.
## Literal readings
Same as inhib_e: interneuron D applies to Pyr->Int, Int->Pyr and Int->Int; per-pair values per connected pair; drivable = the dump proxy (summed conductance, best 8 inputs with the 10 nS cue cap); same-seed arbors are compared to inhib_e only where the configuration is identical (seed 16180).
