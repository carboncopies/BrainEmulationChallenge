# Preregistration, linefix_c Stage 1 (ranking B). Written 2026-11-15 before launch; not to be edited after launch.
Ledger task tmwidgz0z. Full reasoning: DESIGN.md sections 2 and 3 (revision 2). Predictions come from thresholding the stored synapse distances of the existing patched V1 seed-16180 run (linefix), so they are exact if arbors reproduce.

## Runs (patched build, API port 8010, V1, seed 16180, one batch of 3)
| run | D_synmax pyr-pyr | D_synmax pyr-int, int-pyr, int-int |
|---|---|---|
| B1 (primary) | 0.021 | 0.05 |
| B2 | 0.01 | 0.05 |
| B3 (contrast) | 0.05 | 0.05 |
All else as linefix: 96 pyramidal, 48 interneurons, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9, V1 arbor settings. All values inside bio_ranges.json (D_synmax has a maximum only). A pyramidal D of 0.01-0.05 um means about 1-3% filling of the 1.5 um reach, not a physical distance.

## Predictions
| run | Pyr->Pyr synapses | Pyr->Pyr connection prob. | Pyr->Pyr syn per connected pair | pyramidal cells with no Pyr input | A (reported only) |
|---|---|---|---|---|---|
| B1 | 5,021 | 0.289 | 1.91 | 11 | 74.1% |
| B2 | 2,425 | 0.184 | 1.45 | 17 | 85.5% |
| B3 | 11,942 | 0.441 | 2.97 | 4 | 54.6% |
All three runs: Int->Pyr 14,345 synapses, probability 0.60, 5.21 per connected pair, 57.4 targets per interneuron; Pyr->Int 7,960, probability 0.46, 3.77 per pair; Int->Int 9,121, 7.09 per pair; drivable 8-cell 26 of 48 (simple 32); interneurons with no pyramidal input 6. Interneuron axon length 45,207 um and dendrite 6,734 um (ratio 1.000 to the linefix V1 run). bio_check pass.
Tolerances: counts +-2%, probabilities +-0.01, synapses per pair +-0.05, drivable +-1, zero-input counts +-1.

## Success bar (ranking B, in priority order; A is reported, not gated)
1. Pyr->Pyr connection probability 0.1-0.3. 2. Pyr->Pyr synapses per connected pair 1.9-4.5. 3. Int->Pyr per connected pair 4-9. 4. Pyr->Int per connected pair 1.5-4.5. 5. Drivable 8-cell >= 16. 6. Nothing outside bio_ranges.json.
Expected: B1 passes all, bars 1 and 2 by about 0.01 each (a knife edge: I give it 75% that both hold, the risk being arbor drift or rounding at the edge). B2 passes all but bar 2. B3 passes all but bar 1.

## What would count against the method
Arbors identical but any count outside +-2%: thresholding is not equivalent to a rerun, and Stage 2 predictions are void. Arbors not identical: the run is a new realisation (seen in 1 of 9 earlier same-seed runs); then expect probability 0.25-0.34 and 1.7-2.4 per pair for B1.
