# G1/G2/G3 (offline; statsmodels 0.15.0 installed to A/pylib; scripts g1.py g23.py; raw: g1_results.json g23_results.json)
NB2 = statsmodels discrete NegativeBinomial(loglike_method='nb2'), alpha by ML per training fold, standardised features (no ridge), Poisson start values; chain newton->bfgs->nm; fallback = alpha from full-data fit. Fallback count: 2 folds of 50 for raw_pyr_pyr_n, 0 for all other targets. Note: pip --target also placed numpy 2.4.6/scipy 1.17.1 in pylib (they shadow the venv ones when pylib is on PYTHONPATH). Same folds RepeatedKFold(5,10,rs=0). Pooled OOF per repeat, mean±sd over 10 repeats. M1 = earlier Poisson ridge(0.01) numbers.
## G1 pooled OOF (NB | M1 Poisson | RF7)
| target | Spearman NB | M1 | RF7 | R2 NB | M1 | RF7 | D2 NB | M1 | RF7 | MAE NB | M1 | RF7 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| raw_pyr_int_n | 0.731±0.005 | 0.729±0.006 | 0.489±0.038 | 0.541±0.010 | 0.524±0.015 | 0.224±0.053 | 0.594±0.010 | 0.584±0.010 | 0.292±0.040 | 9.700±0.053 | 9.788±0.067 | 13.324±0.415 |
| raw_int_int_n | 0.651±0.013 | 0.650±0.013 | 0.443±0.027 | 0.400±0.018 | 0.395±0.019 | 0.192±0.040 | 0.447±0.023 | 0.447±0.020 | 0.234±0.039 | 5.360±0.068 | 5.376±0.068 | 6.336±0.133 |
| raw_int_pyr_n | 0.850±0.008 | 0.850±0.008 | 0.725±0.034 | 0.703±0.016 | 0.701±0.016 | 0.501±0.033 | 0.736±0.014 | 0.735±0.014 | 0.525±0.029 | 12.632±0.309 | 12.668±0.298 | 17.212±0.624 |
| raw_pyr_pyr_n | 0.939±0.002 | 0.940±0.002 | 0.912±0.008 | 0.905±0.004 | 0.906±0.003 | 0.860±0.008 | 0.919±0.003 | 0.920±0.003 | 0.868±0.009 | 350.0±8.2 | 347.8±7.2 | 447.5±17.0 |
| usable_conns2 | 0.886±0.003 | 0.891±0.004 | 0.803±0.019 | 0.667±0.020 | 0.725±0.020 | 0.647±0.030 | 0.751±0.012 | 0.777±0.014 | 0.640±0.030 | 90.9±1.8 | 82.9±2.4 | 101.9±3.6 |
| usable_pyr_int | 0.483±0.014 | 0.478±0.016 | 0.334±0.035 | 0.334±0.029 | 0.285±0.036 | -0.067±0.073 | 0.415±0.019 | 0.386±0.025 | 0.157±0.055 | 2.416±0.036 | 2.471±0.056 | 3.043±0.114 |
| usable_int_int | 0.491±0.019 | 0.491±0.022 | 0.334±0.033 | 0.187±0.056 | 0.162±0.065 | 0.008±0.114 | 0.303±0.034 | 0.293±0.039 | 0.167±0.056 | 1.026±0.027 | 1.038±0.029 | 1.221±0.064 |
| usable_int_pyr | 0.818±0.009 | 0.818±0.010 | 0.765±0.012 | 0.643±0.019 | 0.639±0.022 | 0.512±0.038 | 0.679±0.019 | 0.676±0.021 | 0.582±0.025 | 3.408±0.078 | 3.434±0.088 | 3.956±0.177 |
## Per-repeat Spearman(M1NB) - Spearman(RF7), 10 repeats
| target | mean | min | max | median fold alpha |
|---|---|---|---|---|
| raw_pyr_int_n | +0.241 | +0.182 | +0.301 | 0.101 |
| raw_int_int_n | +0.208 | +0.145 | +0.253 | 0.150 |
| raw_int_pyr_n | +0.125 | +0.089 | +0.173 | 0.022 |
| raw_pyr_pyr_n | +0.028 | +0.019 | +0.044 | 0.011 |
| usable_conns2 | +0.084 | +0.066 | +0.120 | 0.104 |
| usable_pyr_int | +0.149 | +0.067 | +0.203 | 0.598 |
| usable_int_int | +0.157 | +0.085 | +0.221 | 0.333 |
| usable_int_pyr | +0.053 | +0.014 | +0.074 | 0.077 |
**Diff >= 0.15: raw_pyr_int_n YES (mean +0.241, min +0.182 - every repeat). raw_int_int_n YES on the mean (+0.208) but NOT in every repeat (min +0.145, i.e. 1+ repeat below 0.15).**
## Full-data NB2 fit (raw feature scale). alpha = ML estimate. SEs: GLM-NB with alpha fixed at the ML value (statsmodels discrete Hessian SEs were NaN on the 100-row fit for several targets, so alpha has no SE here; alpha SE from discrete fit available only for usable_pyr_int 0.623±0.158, usable_int_int 0.344±0.170). Coefs equal the discrete-ML coefs to <3e-5.
Order: const, log(n_pre*n_post), logV, log dm.weight, days, log minsep
- raw_pyr_int_n alpha=0.1025: 1.741±1.559, 1.176±0.131, -0.513±0.082, 0.506±0.065, 0.0974±0.0219, -0.470±0.274
- raw_int_int_n alpha=0.1539: 0.128±1.936, 0.965±0.132, -0.389±0.108, 0.485±0.087, 0.1273±0.0287, -0.227±0.368
- raw_int_pyr_n alpha=0.0218: 0.914±0.786, 0.771±0.065, -0.267±0.041, 0.366±0.033, 0.0814±0.0110, 0.079±0.138
- raw_pyr_pyr_n alpha=0.0112: 3.300±0.439, 0.923±0.023, -0.229±0.023, -0.115±0.018, 0.0364±0.0062, -0.017±0.077
- usable_conns2 alpha=0.1027: 4.619±1.338, 0.671±0.071, -0.416±0.070, 0.929±0.056, 0.1282±0.0190, -0.151±0.236
- usable_pyr_int alpha=0.6233: -0.841±4.464, 1.013±0.380, -0.701±0.236, 1.451±0.227, 0.2279±0.0632, 0.167±0.794
- usable_int_int alpha=0.3441: -4.747±4.797, 0.527±0.329, -0.296±0.268, 1.437±0.284, 0.3105±0.0729, -0.190±0.912
- usable_int_pyr alpha=0.0769: 3.044±1.875, 0.405±0.156, -0.423±0.098, 1.243±0.098, 0.1403±0.0263, -0.006±0.333
## G2
P75 over 100 rows: raw_pyr_int_n=42.0, raw_int_pyr_n=97.25, raw_int_int_n=18.25. J = min(c1/42, c2/97.25, c3/18.25, usable_conns2/460).
| set | n | min | q25 | median | q75 | P90 | max |
|---|---|---|---|---|---|---|---|
| all | 100 | 0.011 | 0.237 | 0.438 | 0.667 | 0.953 | 1.534 |
| soft-clean | 34 | 0.013 | 0.219 | 0.329 | 0.578 | 0.813 | 1.041 |
Top 5 overall (pyr,int,days,minsep,radius,thick,dm | raw_pyr_int_n, raw_int_pyr_n, raw_int_int_n, conns2 | J, density/mm3, wall_s):
1. 64,23,24,14,111,24,0.9 | 80,172,28,925 | 1.534, 93651 (not clean), 491
2. 65,28,21,14,104,48,0.8 | 79,149,33,868 | 1.532, 57020 (not clean), 349
3. 69,30,23,14,148,30,0.9 | 82,143,30,622 | 1.352, 47956 (pyr frac 0.697, not clean), 423
4. 58,26,24,10,108,45,0.8 | 64,128,34,680 | 1.316, 50941 (not clean), 409
5. 64,25,25,11,136,23,0.8 | 129,111,40,757 | 1.141, 66594 (not clean), 474
Top 5 soft-clean:
1. 68,29,25,12,119,50,0.5 | 44,146,19,798 | 1.041, 43607, 514
2. 70,19,25,15,126,39,0.6 | 64,129,18,909 | 0.986, 45755, 558
3. 63,20,25,10,183,25,0.9 | 63,90,32,481 | 0.925, 31556, 473
4. 70,26,21,11,177,49,0.9 | 46,108,15,459 | 0.822, 19906, 371
5. 59,24,24,13,137,35,0.5 | 41,96,22,364 | 0.791, 40218, 423
(density for #3 overall: pyr fraction 0.697 -> fails the 0.70 bound.)
## G3 (M1NB all 100 rows; mean [80% NB predictive interval p10-p90]; days 25, minsep 12)
| cfg | raw_pyr_int_n | raw_int_pyr_n | raw_int_int_n | usable_conns2 | J (from means) | density /mm3 | pyr frac | soft-clean | wall_s (T6 A) |
|---|---|---|---|---|---|---|---|---|---|
| a pyr70 int30 r113 t50 dm1.0 | 96.2 [58,139] | 176.1 [140,214] | 37.7 [19,59] | 1218.7 [751,1740] | 1.81 | 49857 | 0.700 | YES (barely) | 620 |
| b r178 t20 dm1.0 | 96.6 [58,140] | 176.5 [140,215] | 37.8 [19,59] | 1222.5 [753,1746] | 1.81 | 50232 | 0.700 | NO (density just above 50000) | 620 |
| c r141 t32 dm1.0 | 96.4 [58,140] | 176.3 [140,215] | 37.7 [19,59] | 1220.5 [752,1743] | 1.81 | 50034 | 0.700 | NO (just above 50000) | 620 |
| d r113 t50 dm0.8 | 86.0 [51,125] | 162.3 [128,198] | 33.8 [17,53] | 990.4 [610,1415] | 1.67 | 49857 | 0.700 | YES | 620 |
| e pyr70 int18 r106 t50 dm1.0 | 56.3 [33,82] | 122.9 [96,151] | 14.4 [6,24] | 1285.3 [792,1835] | 0.79 | 49860 | 0.795 | YES | 495 |
Caveats: a-d are at the edge/outside of the sampled box (dm.weight=1.0 and pyr70/int30 corners, radius 178 with t=20 untested jointly) so predictions are extrapolative; predicted wall_s for a-d (620 s) exceeds the observed max 584 s. Predictions barely vary across a/b/c because the fitted V exponent (~-0.2 to -0.5) times a near-constant V (113^2*50 ~ 178^2*20 ~ 141^2*32 ~ 2.0e6) gives equal V. In e, J is limited by raw_int_int_n (14.4/18.25).
