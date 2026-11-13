# Phase 1: growth with bio-consistent D_synmax (2026-11-12)

Directives (confirmed in the Netmorph parameter echo `*_.nibr.clp` of run a): `D_synmax.pyramidal.pyramidal=1.5`; `D_synmax.pyramidal.interneuron`,
`D_synmax.interneuron.pyramidal`, `D_synmax.interneuron.interneuron` = 0.1 (configs a-d) or 0.15 (config e). Seed 20240628, days 25. Hard limits asserted with bio_check before each growth.
Each growth ran alone with 30 s pauses, memory guard 100 GB, 1500 s cap (none hit it), model saved as `v2-<x>0000`, sim deleted after.
Command: `python grow_v2.py a b c d e` (grow_v2.py); table from `analyze_p1.py` (phase1_results.json). Conductance convention as in earlier analyses (g_peak_sum, 0.98 nS per AMPA synapse).

| cfg | geometry (pyr/int, minsep, radius, thick, dm) | D_synmax int pairs | Pyr->Pyr syn | Pyr->Int syn | Int->Pyr syn | Int->Int syn | mean Pyr syn per int | int with >=13.84 nS from pyr | inhib. fraction onto pyr | wall s |
|---|---|---|---|---|---|---|---|---|---|---|
| a | 96/48, 10, 120, 30, 0.9 (Randal) | 0.1 | 71924 | 227 | 348 | 108 | 4.7 | 6/48 (12.5%) | 0.5% | 1260 |
| b | 70/30, 12, 113, 50, 1.0 (h2h corner) | 0.1 | 46205 | 107 | 253 | 51 | 3.6 | 2/30 (6.7%) | 0.5% | 802 |
| c | 64/32, 10, 100, 40, 1.0 (denser) | 0.1 | 54840 | 80 | 308 | 35 | 2.5 | 1/32 (3.1%) | 0.6% | 701 |
| d | 70/46, 10, 100, 50, 1.0 (40% interneurons) | 0.1 | 53021 | 133 | 376 | 87 | 2.9 | 2/46 (4.3%) | 0.7% | 905 |
| e | 96/48, 10, 120, 30, 0.9 (Randal) | 0.15 | 71439 | 505 | 727 | 211 | 10.5 | 8/48 (16.7%) | 1.0% | 1067 |

Interneurons with zero pyramidal input: a 26/48, b 20/30, c 19/32, d 23/46, e 19/48. Mean GABA onto a pyramidal cell (weight 1): 2.9, 2.9, 3.8, 4.3, 6.1 nS (the earlier D_synmax 0.5 network had about 40 nS).

Result: NO config gives a usable interneuron reservoir. Best is e (D_synmax 0.15, 16.7% of interneurons drivable), far below the 50% bar; denser or interneuron-rich geometry (c, d) did not help
(the Pyr->Int count scales with D_synmax, not with density, as found earlier: about D_synmax^1.6). Pyr->Pyr is huge (46-72k synapses) because of D_synmax 1.5. Phase 2/3 NOT run (per instruction).
Saved models: v2-a0000 ... v2-e0000 (reloadable); viz dumps in grow_<x>/viz/sample_0000.json.
Options for the decision: (1) accept a larger interneuron D_synmax (earlier 0.5 gave 10/27 drivable, 1.0 gave 16/27; 0.3 gave 6/27) but that conflicts with the smooth-dendrite design note;
(2) keep 0.1-0.15 and obtain interneuron drive another way, e.g. interneuron count 128 with high dm_weight, or change which parameters set interneuron dendrite size (min_basal/max_basal, interneuron axon growth), which is outside the seven approved parameters;
(3) treat interneurons as a fixed pool and programme inhibition only through weights, which cannot create synapses.
