# inhib_f: seed replication of the three in-band configurations (seeds 27182 and 31415 new, 16180 from inhib_e), scored 2026-11-17
Configs: **E4** V1, 20 interneurons, D_int 0.03; **E5** V3, 24 interneurons, D_int 0.02; **E6** V3, 20 interneurons, D_int 0.02; pyramidal D 0.0175, 96 pyramidal cells, patched build. Files: PREREGISTRATION.md (written before launch, not edited), grow_pv.py/analyze_pv.py (copies of inhib_e, paths and model prefix `v2-ihf-` only; diffs checked), run_grow.sh, stats.py, score.py/score.log (scoring from the numbers below), pv_results.json (6 new runs), analyze_*.log, grow_*/. Seed 16180 values come from ../inhib_e/pv_results.json.
All 6 growths rc 0 (walls 1,688-6,065 s; seed 31415 runs were slow, up to 1.7 h, for an unknown reason under unchanged machine load of about 4), bio_check pass, D_synmax read back, resident simulations deleted. Patched instance only (NES 8011 / API 8010); main NES/API untouched; no git, no email, no code changes.

## 1. All runs and bars (bars: 1 p 0.1-0.3; 2 Pyr->Pyr per pair 1.9-4.5; 3 Int->Pyr per pair 4-9; 4 Pyr->Int per pair 1.5-4.5; 5 drivable 8-cell >= 7 of 20 / 8 of 24; 6 bio_ranges; 7 A 25-50%)
| config | seed | p | Pyr->Pyr /pair | A % | Int->Pyr /pair | Pyr->Int /pair | drivable | zero-input Ints | failed bars |
|---|---|---|---|---|---|---|---|---|---|
| E4 | 16180 (inhib_e) | 0.236 | 1.93 | 46.8 | 4.130 | 4.03 | 10 of 20 | 3 | none |
| E4 | 27182 | 0.254 | 2.35 | 44.8 | 5.147 | 3.90 | 7 of 20 | 4 | none |
| E4 | 31415 | 0.282 | 2.08 | 40.7 | **3.997** | 3.72 | 10 of 20 | 1 | 3 (by 0.003) |
| E5 | 16180 (inhib_e) | 0.237 | 1.84 | 48.5 | 3.667 | 2.62 | 11 of 24 | 3 | 2, 3 |
| E5 | 27182 | 0.286 | 1.76 | 43.0 | 3.031 | 3.13 | 15 of 24 | 1 | 2, 3 |
| E5 | 31415 | 0.290 | 1.88 | 45.2 | 3.655 | 2.44 | 10 of 24 | 2 | 2, 3 |
| E6 | 16180 (inhib_e) | 0.262 | 2.05 | 40.5 | 3.609 | 4.04 | 11 of 20 | 1 | 3 |
| E6 | 27182 | 0.256 | 1.94 | 42.6 | 3.633 | 2.47 | 5 of 20 | 4 | 3, 5 |
| E6 | 31415 | 0.258 | 2.76 | 40.9 | 5.573 | 2.87 | 10 of 20 | 1 | none |
Literal reading: Int->Pyr per pair is synapses / connected pairs, not rounded: E4 s31415 = 3,677 / 920 = 3.9967, which fails the bar of 4 by 0.003 (it would pass if rounded to 4.0; I report the fail).
## 2. Pooled over the 3 seeds (mean, min-max)
| config | p | Pyr->Pyr /pair | A % | Int->Pyr /pair | Pyr->Int /pair | drivable | Pyr->Pyr synapses | seeds passing all 7 bars |
|---|---|---|---|---|---|---|---|---|
| E4 V1, 20, 0.03 | 0.257 (0.236-0.282) | 2.12 (1.93-2.35) | 44.1 (40.7-46.8) | 4.42 (4.00-5.15) | 3.88 (3.72-4.03) | 9 (7-10) of 20 | 4,984 (4,158-5,443) | **2 of 3** |
| E5 V3, 24, 0.02 | 0.271 (0.237-0.290) | 1.83 (1.76-1.88) | 45.6 (43.0-48.5) | 3.45 (3.03-3.67) | 2.73 (2.44-3.13) | 12 (10-15) of 24 | 4,524 (3,991-4,990) | 0 of 3 |
| E6 V3, 20, 0.02 | 0.259 (0.256-0.262) | 2.25 (1.94-2.76) | 41.3 (40.5-42.6) | 4.27 (3.61-5.57) | 3.13 (2.47-4.04) | 8.7 (5-11) of 20 | 5,314 (4,538-6,494) | 1 of 3 |
**Result.** A is inside the sourced band in all nine runs (40.5-48.5%) and bars 1, 6, 7 hold everywhere; the failures are in the per-pair bars, mostly Int->Pyr per pair, which sits on the boundary (3.0-5.6, mean 3.5-4.4). **No configuration passes all seven bars on all three seeds**: E4 passes on 2 of 3 (misses by 0.003 on 31415), E6 on 1 of 3, E5 on none (it fails bars 2 and 3 on every seed). Per the task, the capacity_d recall protocol (dyn2.py) was therefore NOT run. If a seed-count rule of 2 of 3 were wanted, E4 would be the candidate; that would be a different rule from the one preregistered.

## 3. Prediction scoring (PREREGISTRATION.md; scoring rule: HIT inside the stated range, PARTIAL up to 25% beyond its edge, MISS otherwise; detail in score.log)
| run | p | per pair | A | Int->Pyr /pair | Pyr->Int /pair | drivable |
|---|---|---|---|---|---|---|
| E4 s27182 | 0.254 vs 0.227 HIT | 2.35 vs 1.95 PARTIAL | 44.8 vs 42.3 HIT | 5.15 vs 3.59 MISS | 3.90 vs 4.67 PARTIAL | 7 vs 11 PARTIAL |
| E4 s31415 | 0.282 vs 0.290 HIT | 2.08 vs 1.85 PARTIAL | 40.7 vs 44.1 HIT | 4.00 vs 3.77 HIT | 3.72 vs 4.38 PARTIAL | 10 vs 10 HIT |
| E5 s27182 | 0.286 vs 0.229 PARTIAL | 1.76 vs 1.86 HIT | 43.0 vs 44.0 HIT | 3.03 vs 3.19 HIT | 3.13 vs 3.04 HIT | 15 vs 12 HIT |
| E5 s31415 | 0.290 vs 0.292 HIT | 1.88 vs 1.77 HIT | 45.2 vs 45.8 HIT | 3.66 vs 3.35 HIT | 2.44 vs 2.85 PARTIAL | 10 vs 11 HIT |
| E6 s27182 | 0.256 vs 0.252 HIT | 1.94 vs 2.07 HIT | 42.6 vs 36.2 PARTIAL | 3.63 vs 3.14 PARTIAL | 2.47 vs 4.68 MISS | 5 vs 12 MISS |
| E6 s31415 | 0.258 vs 0.321 PARTIAL | 2.76 vs 1.97 MISS | 40.9 vs 37.9 HIT | 5.57 vs 3.30 MISS | 2.87 vs 4.39 MISS | 10 vs 11 HIT |
Totals: 20 HIT, 10 PARTIAL, 6 MISS of 36 cells. The misses are the three quantities the seed-shift model (V1n30 ratios from linefix_c) handles worst: Int->Pyr per pair (E4 s27182, E6 s31415: much higher than predicted), Pyr->Int per pair (E6 both seeds: lower), per pair Pyr->Pyr (E6 s31415), drivable (E6 s27182, 5 vs 12). The seed ratios came from three V1n30 runs and did not transfer to V3 20-24-interneuron networks.
Bar predictions: "bars 5, 6, 7 pass in all six runs": bar 7 and 6 held in 6 of 6; bar 5 failed once (E6 s27182, 5 of 20) (5 of 6). "Bar 3 fails in at least 5 of 6": it failed in 4 of 6 (E4 s31415, E5 x2, E6 s27182 failed; E4 s27182 and E6 s31415 passed) MISS. Per-run P(all 7 passing): predicted 10%, 6%, 3%, 2%, 2%, 1%; observed pass: E4 s27182 (10%) yes, E6 s31415 (1%) yes, the other four no. Per-configuration probability of passing on all three seeds: E4 1%, E5 0%, E6 0%; observed none (E4 2 of 3). "At least one configuration passes on 3 of 3: 1%; dynamics check expected not to run (99%)": HIT.

## 4. Honest limits
- The conclusion rests on one pass criterion that sits on a knife edge: Int->Pyr per pair 3.997 (E4 s31415) vs 4, 4.13 (s16180), and 3.6-3.7 for E5 and E6 on most seeds. The 4-9 bar is the binding one in 5 of 9 failing runs.
- E4 s27182 passes drivable at exactly 7 of 20 with 4 zero-input interneurons; E6 s27182 has 4 zero-input interneurons and only 5 drivable. Interneuron-pair counts move 5-30% between seeds for a fixed configuration (e.g. Int->Pyr 3,655 / 4,416 / 3,677 for E4).
- Each config/seed is a new arbor realisation; arbor reproduction was not checked across seeds (no earlier run of these configs on seeds 27182/31415 exists), and the inhib_e result for 16180 is a single seed.
- 20-24 interneurons are 17-20% of the cells (CA3 about 11.5%) and all are one perisomatic PV-like class; the 25-50% A band is derived (inhib_e/TARGET.md), and the drivable bar is the dump proxy. No recall dynamics were run on these networks; E4 on 2 of 3 seeds does not meet the preregistered condition for them.
