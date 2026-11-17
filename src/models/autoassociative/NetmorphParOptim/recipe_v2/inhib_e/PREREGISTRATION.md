# Preregistration, inhib_e: fewer interneurons and lower interneuron D (2026-11-17). Written before any launch; not to be edited after launch.
Ledger task tmwidgz0z (post-experiment-1 list, item 2). Reasoning and sources: TARGET.md. Offline predictions: offline.py -> offline_results.json, offline.log.

## Question
Can the within-patch inhibitory fraction A = Int->Pyr / (Int->Pyr + Pyr->Pyr) be brought into a sourced band, while the per-pair bars still hold, by using 20 or 24 interneurons and interneuron D 0.02 or 0.03?

## Target replacing the 3-6% band
Within-patch A 25-50%. This is a derived band (TARGET.md section 3): whole-cell census values (5-13% inhibitory) are not comparable with A, because most excitatory input to a pyramidal cell comes from outside a 240 um patch. The band rests on one snippet-only figure and one unsourced assumption, and is a working band.

## Runs (patched build, API port 8010; 96 pyramidal cells; pyramidal D 0.0175; seed 16180; all else as linefix_c Stage 2)
| run | variant | interneurons | interneuron D (all three interneuron pairs) |
|---|---|---|---|
| E1 | V3 | 24 | 0.03 |
| E2 | V3 | 20 | 0.03 |
| E3 | V1 | 24 | 0.03 |
| E4 | V1 | 20 | 0.03 |
| E5 | V3 | 24 | 0.02 |
| E6 | V3 | 20 | 0.02 |
Batch 1 = E1-E3, batch 2 = E4-E6. V1 at interneuron D 0.02 is not grown: it is obtained by thresholding E3 and E4 at 0.02 (method good to about 2%, linefix_c Stage 1), and it is predicted to fail the Int->Pyr bar. E5 and E6 are direct runs and double as a check of thresholding E1 and E2. Seeds 27182 and 31415 only after seed 16180 is scored. Max 3 concurrent growth sims on the machine; launch only when arbor-seeds' growth step is done or slots are free and the patched instance is up (arbor-seeds owns the instance; I do not start or stop it). All values inside bio_ranges.json (D_synmax has a maximum only).

## How the predictions were made
Existing patched 30-interneuron networks at pyramidal D 0.0175 (V3n30 seeds 16180, 27182; V1n30 seeds 16180, 27182, 31415), synapses thresholded at interneuron D 0.03 / 0.02, and 24 or 20 of the 30 interneurons kept at random (1,000 draws). A regrown network with a different cell count is a new realisation (linefix_b: Pyr->Pyr moved +12% and +28% when 48 became 30), so predictions are ranges: the spread over the available seeds of that variant, widened by about 10%.

## Predictions
| run | A | Int->Pyr per connected pair | Pyr->Int per connected pair | drivable 8-cell | central values from the seed-16180 network (A / Int->Pyr / Pyr->Int / drivable) |
|---|---|---|---|---|---|
| E1 V3, 24, D 0.03 | 50-63% | 4.8-6.4 | 2.4-3.6 | 8-18 of 24 | 58.1% / 5.37 / 3.24 / 16.0 |
| E2 V3, 20, D 0.03 | 46-59% | 4.8-6.4 | 2.4-3.6 | 7-15 of 20 | 53.6% / 5.37 / 3.21 / 13.4 |
| E3 V1, 24, D 0.03 | 43-57% | 3.8-5.1 | 2.4-3.2 | 7-14 of 24 | 51.8% / 4.65 / 2.64 / 9.5 |
| E4 V1, 20, D 0.03 | 38-52% | 3.8-5.1 | 2.4-3.2 | 6-12 of 20 | 47.2% / 4.65 / 2.63 / 8.0 |
| E5 V3, 24, D 0.02 | 41-52% | 3.6-4.8 | 1.9-2.8 | 7-15 of 24 | 47.6% / 4.03 / 2.55 / 13.6 |
| E6 V3, 20, D 0.02 | 37-47% | 3.6-4.8 | 1.9-2.8 | 6-13 of 20 | 43.1% / 4.03 / 2.53 / 11.3 |
All runs: Pyr->Pyr connection probability 0.22-0.33, Pyr->Pyr synapses per connected pair 1.8-2.3, Pyr->Pyr synapses 4,000-6,200. Int->Pyr connection probability 0.40-0.56 (D 0.03) or 0.35-0.50 (D 0.02).
Thresholding checks: E1 thresholded at 0.02 against E5, and E2 against E6, agree only as two realisations would if the arbors differ; if a pair has identical pyramidal arbors, counts agree within 3%.
V1 at D 0.02 by thresholding E3 / E4: A 33-46% (24) / 30-42% (20), Int->Pyr per pair 3.0-3.9 (below the bar), drivable 4-10 / 4-9.

## Success bar (priority order)
1. Pyr->Pyr connection probability 0.1-0.3. 2. Pyr->Pyr synapses per connected pair 1.9-4.5. 3. Int->Pyr per connected pair 4-9. 4. Pyr->Int per connected pair 1.5-4.5. 5. Drivable 8-cell at least one third of interneurons: 8 of 24, 7 of 20 (the proportional rule John chose on 2026-11-15, extended to these counts; raw counts reported). 6. Nothing outside bio_ranges.json. 7. New: within-patch A 25-50%.
Expected: bar 7 met by E6 (about 75%), E5 (about 55%), E4 (about 55%), E3 (about 30%), E2 (about 25%), E1 (under 10%). At D 0.02 the Int->Pyr bar is at risk (about 50% to pass in E5 and E6). I put about 35% on at least one run passing all seven bars, most likely E6 or E4. Bars 1 and 2 carry their usual seed risk (4 of 7 Stage 2 runs passed both).

## What would count against the approach
A above 50% in all six runs: 20-24 interneurons with D 0.02-0.03 is not enough, and the next lever is the interneuron count (about 12, the CA3 fraction) rather than D. Int->Pyr per pair below 4 in E5 and E6: D 0.02 is too low for interneuron pairs and D 0.03 is the floor.
