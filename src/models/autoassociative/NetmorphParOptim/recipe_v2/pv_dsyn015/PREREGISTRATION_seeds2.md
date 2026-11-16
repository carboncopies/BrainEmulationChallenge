# Addendum preregistration: D_synmax 0.15 repeat on seeds 31415 and 27182 (written before launch; not edited afterwards)
Written 2026-11-15, after the seed-16180 result (README.md: ratios Int->Pyr 2.02, Pyr->Int 2.07, Int->Int 2.16 pooled; per run 1.97-2.21; lengths and Pyr->Pyr identical; +x share 52-54%). Same scripts (grow_pv.py unchanged), 6 runs S1/V1/V3 at seeds 31415 and 27182, baselines D 0.1 from ../pv_arbor_seeds/pv_results.json.

## Predictions (per seed and run)
1. Arbors: interneuron dendrite and axon length ratio new/baseline 1.000 (within 0.002), reach ratio 0.99-1.01, Pyr->Pyr ratio 1.00 (0.99-1.01).
2. Ratios new/baseline per run: Int->Pyr 2.05 (1.85-2.30), Pyr->Int 2.10 (1.85-2.35), Int->Int 2.15 (1.90-2.40). Wider per-run bands than seed 16180 because low baselines (V1 s31415 Pyr->Int 371, Int->Int 474) carry Poisson noise of about 5%. Pooled over the 6 runs: each pathway 2.0-2.2; pooled over all 9 runs (with seed 16180): Int->Pyr 2.0-2.1, Pyr->Int 2.0-2.15, Int->Int 2.1-2.2. Prediction: x2 holds on every seed (all per-seed pooled ratios 1.9-2.3).
3. Expected counts (baseline x2.05 Int->Pyr, x2.10 Pyr->Int and Int->Int) and the inhibitory fractions derived from them:
| run | baseline pp / pi / ip / ii | baseline A / B, drivable 8-cell (simple) | predicted ip / pi / ii (x2.05, x2.10, x2.10) | pred A / B (%) |
|---|---|---|---|---|
| S1 s31415 | 72104 / 533 / 1384 / 957 | 1.88 / 3.12, 5 (12) | 2837 / 1119 / 2009 | 3.8 / 6.2 |
| V1 s31415 | 78446 / 371 / 969 / 474 | 1.22 / 1.80, 3 (7) | 1986 / 779 / 995 | 2.5 / 3.6 |
| V3 s31415 | 79826 / 467 / 1435 / 764 | 1.77 / 2.67, 5 (8) | 2941 / 980 / 1604 | 3.6 / 5.3 |
| S1 s27182 | 70237 / 533 / 1534 / 1074 | 2.14 / 3.55, 5 (10) | 3144 / 1119 / 2255 | 4.3 / 7.0 |
| V1 s27182 | 79085 / 626 / 1026 / 645 | 1.28 / 2.05, 6 (12) | 2103 / 1314 / 1354 | 2.6 / 4.1 |
| V3 s27182 | 77402 / 1098 / 1275 / 1475 | 1.62 / 3.38, 8 (16) | 2613 / 2305 / 3097 | 3.3 / 6.7 |
   Fractions A and B accepted within +-0.4 points of those values.
4. Drivable 8-cell (baselines S1/V1/V3 = 5/3/5 at s31415 and 5/6/8 at s27182): s31415 S1 8 (6-11), V1 7 (4-10), V3 9 (6-12); s27182 S1 8 (5-11), V1 10 (7-13), V3 12 (9-15). Simple count about 1.7x baseline +-30%. Maximum 8-cell over the 6 runs about 12-13; probability that any run reaches 16 (8-cell): 10%; no run expected to meet the bar (16 drivable AND A in 3-6% AND 5% Pyr->Pyr).
5. +x share of Int->Pyr synapse-carrying segments (cos > 0.9): 51-55% for S1 and V1, 49-54% for V3, i.e. 2-6 points below each baseline (seed 16180: 57.0 -> 53.6, 56.5 -> 54.0, 58.4 -> 52.1); fraction among all interneuron axon segments 4.6-4.9% unchanged.

## Scoring rule
Hit = inside the stated range; partial = within 25% of the range edge; miss = otherwise. Main claim "x2 holds on all seeds" is HIT if every per-seed pooled ratio (3 pathways x 2 seeds) lies in 1.9-2.3 and no arbor property changes; PARTIAL if any is in 1.7-2.5; MISS otherwise.
