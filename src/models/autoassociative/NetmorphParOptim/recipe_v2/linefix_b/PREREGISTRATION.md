# Preregistration: line-379-fixed build, repeat seeds (Part A) and V1 with 30 interneurons (Part B)
Written 2026-11-15, before any launch in this folder; not edited afterwards. Ledger tmwidgz1a. Patched build / separate instance as in ../linefix/README.md (API 8010, NES 8011); main NES/API untouched. D_synmax 1.5 / 0.1 (three interneuron pairs), everything else as ../linefix.
Basis: ../linefix seed 16180 (fixed/baseline ratios: Pyr->Pyr 5.00 / 4.91 / 4.89, Pyr->Int 32.6 / 34.7 / 30.9, Int->Pyr 31.6 / 32.5 / 29.7, Int->Int 32.6 / 36.0 / 33.7 for S1 / V1 / V3; Int->Pyr syn/pair 14.2 / 9.0 / 12.7; targets 74.8 / 66.3 / 66.4; A 12.2 / 7.6 / 8.8%; B 16.3 / 11.4 / 12.8%; drivable 8-cell 33 / 31 / 39; zero-input 2 / 4 / 0; +x share 4.7-4.9%) and the unpatched baselines of the new seeds in ../pv_arbor_seeds/pv_results.json.
Runs: Part A = S1, V1, V3 at seeds 31415 and 27182 (6 runs, 48 interneurons). Part B = V1 with 30 interneurons (30 / (96+30) = 24%) at seed 16180, and 31415 if time allows (V1n30). Max 3 concurrent.

## Part A predictions (per run: baseline x the seed-16180 ratio; count ranges +-30% because baseline counts at these low values are noisy)
| run | Pyr->Pyr | Pyr->Int | Int->Pyr | Int->Int | A (%) | B (%) |
|---|---|---|---|---|---|---|
| S1 s31415 | 360843 | 17347 | 43662 | 31194 | 10.8 | 16.5 |
| V1 s31415 | 385062 | 12855 | 31507 | 17068 | 7.6 | 10.9 |
| V3 s31415 | 389991 | 14419 | 42545 | 25719 | 9.8 | 14.4 |
| S1 s27182 | 351500 | 17347 | 48395 | 35007 | 12.1 | 18.4 |
| V1 s27182 | 388199 | 21691 | 33361 | 23226 | 7.9 | 12.1 |
| V3 s27182 | 378148 | 33901 | 37801 | 49654 | 9.1 | 17.5 |
Ranges: Pyr->Pyr +-12%; Pyr->Int, Int->Pyr, Int->Int +-30%; A +-25% relative; B +-3 points.
- Arbors unchanged vs the unpatched baseline of the same seed: interneuron axon/dendrite length ratio 1.00 (0.99-1.01), reach 0.98-1.02 (a divergent realisation, as in 1 of 9 earlier same-seed runs, is possible and would be reported).
- Syn/pair Int->Pyr: S1 14 (12-16.5), V1 9 (7.5-10.5), V3 12.5 (10.5-14.5) in each seed. Targets per interneuron (of 96): S1 75 (70-81), V1 66 (60-73), V3 66 (60-74).
- Drivable 8-cell of 48: S1 33 (27-40), V1 31 (24-38), V3 38 (31-44); all >= 16 (95%). Zero-input interneurons: S1 2 (0-4), V1 4 (1-8), V3 1 (0-3).
- +x share of Int->Pyr synapse-carrying segments 4.4-5.2%.
- Pooled over the 3 seeds (with the 16180 linefix runs): syn/pair near 11 (9-13) for S1 and V3, V1 about 9 (just below the band); inhibitory fraction A above the 3-6% band for all three variants (S1 about 11.7%, V1 7.7%, V3 9.2%); V1 is the closest and within 3-6% in no seed (probability that any V1 run has A <= 6%: 10%).

## Part B predictions (V1, 30 interneurons instead of 48; baseline = ../linefix V1 s16180: Pyr->Pyr 348,125, Pyr->Int 15,974, Int->Pyr 28,484, Int->Int 18,329, syn/pair 8.95, targets 66.3, A 7.56%, B 11.39%, drivable 31 of 48 (35 simple))
Scaling argument: Int->Pyr scales with the number of interneuron axons (x0.625), Pyr->Int with the number of interneuron dendrites (x0.625), Int->Int with the square (x0.39); per-pair properties (syn/pair, targets) unchanged because the pair overlap does not depend on the count; the pyramidal network is unchanged in principle, but a different cell count changes the random stream and cell placement, so Pyr->Pyr may move (earlier 20-interneuron runs moved by +10..+19%).
- s16180: Int->Pyr 17,800 (15,500-20,500); Pyr->Int 9,980 (8,700-11,500); Int->Int 7,150 (5,800-8,800); Pyr->Pyr 348,000 (295,000-410,000).
- Syn/pair Int->Pyr 8.9 (7.5-10.5); targets per interneuron 66 (58-74) of 96.
- Inhibitory fraction A 4.9% (4.0-6.0), so inside the 3-6% band with probability 80%; B 6.5% (5.3-7.8).
- Drivable 8-cell of 30: 20 (15-25) (the 31 of 48 fraction, 65%, is kept); at least 16 of 30 with 80% confidence. Zero-input 2 (0-5).
- +x share 4.4-5.2%.
- s31415 (if run), relative to Part A V1 s31415 (48 interneurons): Int->Pyr x0.63 (0.55-0.72), Pyr->Int x0.63 (0.55-0.72), Int->Int x0.39 (0.30-0.50), Pyr->Pyr x1.00 (0.85-1.15), A about 4.9% (3.8-6.2), drivable of 30 about 20 (14-25).

## Scoring rule
Hit = inside the stated range; partial = within 25% of the nearest range edge (A and B: within 1 point); miss otherwise. Verdict questions answered from measurements: A in 3-6%; syn/pair near 11 (9-13); drivable >= 16 of 30 in Part B.
