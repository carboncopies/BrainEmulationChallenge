# Interneuron axon B_inf rerun (own NES, 8000/8001), 2026-11-12
Scripts: grow_rerun.py (driver, copy of grow_v3.py conventions, seed arg), analyze_rerun.py. Data: rerun_results.json, cones_int_axon_*.npy. Run folders grow_R0..R3 (model files, run.log).
Common: 96 pyr / 48 int, days 25, D_synmax pyr.pyr 1.5, int pairs 0.1, bio_check asserted, interneuron min_basal=4 max_basal=8. R1/R2 add the restated all_interneuron_axons block (van_Pelt, tau=1681541, E=0.319251, same_arbor, min_node_interval=0.0), B_inf 26 / 39.
Report check (each run's _report): `all_interneuron_axons.` van_Pelt B_inf=13.22 (R0,R3), 26.00 (R1), 39.00 (R2); tau=1681541, E=0.32, min_node_interval=0.000 in all.

| run | seed | int axon cones/cell | int axon bifurc/cell | Pyr->Pyr (vs R0) | Pyr->Int | Int->Pyr | Int->Int | drivable /48 | inhib frac |
|---|---|---|---|---|---|---|---|---|---|
| R0 (A) | 20240628 | 74.2 | 73.2 | 73697 | 550 | 453 | 273 | 10 | 0.61% |
| R1 B_inf 26 | 20240628 | 414 | 413 | 63342 (-14.1%, FLAG) | 450 | 1378 | 877 | 10 | 2.13% |
| R2 B_inf 39 | 20240628 | 1283 | 1282 | 79955 (+8.5%, FLAG) | 476 | 4404 | 2439 | 10 | 5.22% |
| R3 (A, seed ...629) | 20240629 | 80.4 | 79.4 | 88580 (+20.2%, FLAG) | 362 | 540 | 172 | 10 | 0.61% |

Determinism: R0 cones (3560 = 74.2/cell) are identical to arbor A; synapse counts differ slightly from arbor_results A (Pyr->Pyr 73697 vs 73735, Pyr->Int 550 vs 539, Int->Pyr 453 vs 422, Int->Int 273 vs 262), so growth is deterministic but synapse counts are not exactly reproducible. Interneuron/pyramidal dendrite and pyramidal axon cone counts: R0 1081/6899/5459 (int dend / pyr axon / pyr dend), R1 1096/7015/5364, R2 1108/7156/5388, R3 1175/7129/6054.

Answer: yes. B_inf is the lever; the 63-74 "ceiling" was the B_inf=13.2 default, not spatial. Cones scale 5.6x (B_inf x2) and 17x (x3); Int->Pyr 453 -> 1378 -> 4404, inhibitory fraction 0.6% -> 2.1% -> 5.2% (R2 passes the 3% bar). Drivable interneurons stay 10/48 because they depend on Pyr->Int (dendrites), which the axon lever does not touch.
Spatial check (interneuron axon cone positions, R0/R3/R1/R2): radial distance from disc centre p99 about 47-49 um, 0% beyond 110 um (disc radius 120); |z-offset| >15 um for ~9% of cones. No pile-up at the boundary, so no spatial ceiling at these counts (caveat: positions are as written in *.growthcones, assumed absolute).
Pyr->Pyr noise: seed-only change (R3) moves it +20%; R1 -14%, R2 +8.5%. Pyr->Pyr is a realisation-level random effect (>5% flag applies to all three), so compare Pyr->Pyr with that spread (about +-20%), not 5%. Int->Pyr gains (x3, x10) are far outside that noise.
Wall time: R0 1242 s, R3 1460 s, R1 3195 s, R2 ~6.8 h (4 concurrent at start; R2 per-step time grew with cone count). grow_rerun.py had a 3600 s cap; R2's wrapper was killed by me at ~55 min (the gen_autonm_labels client kept running and completed rc 0, no failures). Saved models: v2-arbor-R00000, R10000, R20000, R30000. All four sims (NES IDs 132-135) deleted by gen_autonm_labels -deleteresident ("Deleted resident simulation" in each run.log).
