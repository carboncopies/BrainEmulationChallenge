# Weight-space prototype: numeric results (sim 127 = validation sample k=4)

## Reservoir vs doc baseline

| quantity | doc baseline (20 d, 32 pyr/16 int) | sim 127 (25 d, 67 pyr/27 int, dm.w 0.9) |
|---|---|---|
| Pyr->Pyr AMPA pairs present | 765/992 (77%) | 2939/4422 (66%) |
| mean g_peak_sum over existing pairs (nS) | 3.14 | 7.55 |
| max pair g_peak_sum (nS) | 16.66 | 124.46 |
| pairs >= 6.86 nS (per-pair criterion) | 58 | 928 |
| pairs >= 27.44 nS | n/a | 121 |
| Pyr->Int AMPA pairs (total nS) | 5 | 70 (90.2) |
| Int->Pyr GABA pairs, max pair nS | 26, 1.6 | 173, 3.2 |
| pyramidal cells receiving any GABA | ? | 45 of 67 (mean total 2.6 nS, max 16.8) |
| interneurons receiving any Pyr AMPA | ? | 14 of 27 (max total 40.2 nS) |

## Engram design (assembly-sum criterion, group 8, cue 4, target 27.44 nS at weight 1)

| K | feasible | min margin (nS) | per-pattern margins | groups (neuron IDs) | cues |
|---|---|---|---|---|---|
| 1 | True | 188.2 | [188.16] | [4, 18, 20, 22, 29, 51, 59, 63] | [22, 29, 51, 63] |
| 2 | True | 100.9 | [188.16, 100.94] | [4, 18, 20, 22, 29, 51, 59, 63]; [8, 27, 33, 39, 41, 42, 44, 60] | [22, 29, 51, 63]; [8, 27, 33, 44] |
| 3 | True | 58.8 | [188.16, 100.94, 58.8] | [4, 18, 20, 22, 29, 51, 59, 63]; [8, 27, 33, 39, 41, 42, 44, 60]; [0, 12, 17, 19, 21, 37, 49, 50] | [22, 29, 51, 63]; [8, 27, 33, 44]; [12, 17, 19, 50] |
| 4 | True | 38.2 | [188.16, 100.94, 58.8, 38.22] | [4, 18, 20, 22, 29, 51, 59, 63]; [8, 27, 33, 39, 41, 42, 44, 60]; [0, 12, 17, 19, 21, 37, 49, 50]; [15, 16, 31, 35, 36, 43, 48, 64] | [22, 29, 51, 63]; [8, 27, 33, 44]; [12, 17, 19, 50]; [16, 36, 43, 64] |

Doc baseline: P1 margin 30.4 nS (feasible), P2 disjoint 17.6 nS (64%, infeasible).

## Surrogate calibration

G* (one synchronous AMPA volley, weight 1, resting converter-default LIF with AHP) = 13.84 nS; doc target 27.44 nS = 1.98x G*; four single synapses = 3.92 nS (sub-threshold, consistent with the doc).

## Weight programs

| program | ops | by role | weight range | cue margin at programmed weights (nS, per pattern) | NMDA zeroed on engram pairs (nS) |
|---|---|---|---|---|---|
| K2_w1_prune | 2939 | {'prune_background': 1529, 'prune_offpattern': 1206, 'engram_P0': 48, 'prune_cross': 109, 'engram_P1': 47} | [0.00, 1.00] | [188.16, 100.94] | 1114 |
| K2_scaled_prune | 2939 | {'prune_background': 1529, 'prune_offpattern': 1206, 'engram_P0': 48, 'prune_cross': 109, 'engram_P1': 47} | [0.00, 1.00] | [32.27, 29.8] | 1114 |
| K2_scaled_bg02 | 1410 | {'prune_offpattern': 1206, 'engram_P0': 48, 'prune_cross': 109, 'engram_P1': 47} | [0.00, 1.00] | [32.27, 29.8] | 1114 |
| K2_scaled_prune_intdrive1 | 3009 | {'prune_background': 1529, 'prune_offpattern': 1206, 'engram_P0': 48, 'prune_cross': 109, 'engram_P1': 47, 'pyr_int_drive': 70} | [0.00, 1.00] | [32.27, 29.8] | 1114 |
| K3_w1_prune | 2939 | {'prune_offpattern': 1452, 'prune_cross': 310, 'engram_P2': 39, 'prune_background': 1043, 'engram_P0': 48, 'engram_P1': 47} | [0.00, 1.00] | [188.16, 100.94, 58.8] | 1304 |
| K3_scaled_prune | 2939 | {'prune_offpattern': 1452, 'prune_cross': 310, 'engram_P2': 39, 'prune_background': 1043, 'engram_P0': 48, 'engram_P1': 47} | [0.00, 1.00] | [32.27, 29.8, 32.67] | 1304 |
| K3_scaled_bg02 | 1896 | {'prune_offpattern': 1452, 'prune_cross': 310, 'engram_P2': 39, 'engram_P0': 48, 'engram_P1': 47} | [0.00, 1.00] | [32.27, 29.8, 32.67] | 1304 |
| K3_scaled_prune_intdrive1 | 3009 | {'prune_offpattern': 1452, 'prune_cross': 310, 'engram_P2': 39, 'prune_background': 1043, 'engram_P0': 48, 'engram_P1': 47, 'pyr_int_drive': 70} | [0.00, 1.00] | [32.27, 29.8, 32.67] | 1304 |

## Surrogate recall (cue volley at 20 ms, window 20.5-40 ms)

| program | inhibition | cue | pattern | completion | latency ms | spurious non-member frac (n) | cross-pattern frac | ints firing | spikes/member after cue | members firing >50 ms later |
|---|---|---|---|---|---|---|---|---|---|---|
| K2_w1_prune | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 1.4 | 0.00 (0) | 0.0 | 0 | 44.5 | 7 |
| K2_w1_prune | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 1.94 | 0.00 (0) | 0.0 | 0 | 44.5 | 7 |
| K2_w1_prune | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 1.55 | 0.00 (0) | 0.0 | 0 | 43.2 | 7 |
| K2_w1_prune | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 2.42 | 0.00 (0) | 0.0 | 0 | 43.0 | 7 |
| K2_w1_prune | no_inhibition | cue4 | P0 | 1.00 | 1.4 | 0.00 (0) | 0.0 | 0 | 44.5 | 7 |
| K2_w1_prune | no_inhibition | cue4 | P1 | 1.00 | 1.55 | 0.00 (0) | 0.0 | 0 | 43.2 | 7 |
| K2_w1_prune | gaba_w1_hypothetical | cue4 | P0 | 1.00 | 1.4 | 0.00 (0) | 0.0 | 0 | 44.5 | 7 |
| K2_w1_prune | gaba_w1_hypothetical | cue4 | P1 | 1.00 | 1.55 | 0.00 (0) | 0.0 | 0 | 43.2 | 7 |
| K2_scaled_prune | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K2_scaled_prune | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 4.3 | 0.00 (0) | 0.0 | 0 | 41.6 | 7 |
| K2_scaled_prune | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K2_scaled_prune | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 3.6 | 0.00 (0) | 0.0 | 0 | 40.5 | 7 |
| K2_scaled_prune | no_inhibition | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K2_scaled_prune | no_inhibition | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K2_scaled_prune | gaba_w1_hypothetical | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K2_scaled_prune | gaba_w1_hypothetical | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K2_scaled_bg02 | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K2_scaled_bg02 | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 4.3 | 0.00 (0) | 0.0 | 0 | 41.6 | 7 |
| K2_scaled_bg02 | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K2_scaled_bg02 | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 3.6 | 0.00 (0) | 0.0 | 0 | 40.5 | 7 |
| K2_scaled_bg02 | no_inhibition | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K2_scaled_bg02 | no_inhibition | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K2_scaled_bg02 | gaba_w1_hypothetical | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K2_scaled_bg02 | gaba_w1_hypothetical | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K2_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 1 | 42.5 | 7 |
| K2_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 4.3 | 0.00 (0) | 0.0 | 1 | 41.6 | 7 |
| K2_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 1 | 40.8 | 7 |
| K2_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 3.6 | 0.00 (0) | 0.0 | 1 | 40.5 | 7 |
| K2_scaled_prune_intdrive1 | no_inhibition | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 1 | 42.5 | 7 |
| K2_scaled_prune_intdrive1 | no_inhibition | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 1 | 40.8 | 7 |
| K2_scaled_prune_intdrive1 | gaba_w1_hypothetical | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 1 | 42.5 | 7 |
| K2_scaled_prune_intdrive1 | gaba_w1_hypothetical | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 1 | 40.8 | 7 |
| K2_as_grown_no_ops | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 2.1 | 0.77 (39) | 0.875 | 1 | 50.9 | 7 |
| K2_as_grown_no_ops | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 2.85 | 0.77 (39) | 0.875 | 1 | 51.5 | 7 |
| K3_w1_prune | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 1.4 | 0.00 (0) | 0.0 | 0 | 44.5 | 7 |
| K3_w1_prune | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 1.94 | 0.00 (0) | 0.0 | 0 | 44.5 | 7 |
| K3_w1_prune | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 1.55 | 0.00 (0) | 0.0 | 0 | 43.2 | 7 |
| K3_w1_prune | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 2.42 | 0.00 (0) | 0.0 | 0 | 43.0 | 7 |
| K3_w1_prune | gaba_as_built_0.2 | cue4 | P2 | 1.00 | 1.85 | 0.00 (0) | 0.0 | 0 | 32.8 | 5 |
| K3_w1_prune | gaba_as_built_0.2 | cue2 | P2 | 0.67 | 2.35 | 0.00 (0) | 0.0 | 0 | 32.6 | 5 |
| K3_scaled_prune | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K3_scaled_prune | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 4.3 | 0.00 (0) | 0.0 | 0 | 41.6 | 7 |
| K3_scaled_prune | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K3_scaled_prune | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 3.6 | 0.00 (0) | 0.0 | 0 | 40.5 | 7 |
| K3_scaled_prune | gaba_as_built_0.2 | cue4 | P2 | 1.00 | 2.33 | 0.00 (0) | 0.0 | 0 | 32.2 | 5 |
| K3_scaled_prune | gaba_as_built_0.2 | cue2 | P2 | 0.67 | 3.35 | 0.00 (0) | 0.0 | 0 | 31.6 | 5 |
| K3_scaled_bg02 | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 0 | 42.5 | 7 |
| K3_scaled_bg02 | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 4.3 | 0.00 (0) | 0.0 | 0 | 41.6 | 7 |
| K3_scaled_bg02 | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 0 | 40.8 | 7 |
| K3_scaled_bg02 | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 3.6 | 0.00 (0) | 0.0 | 0 | 40.5 | 7 |
| K3_scaled_bg02 | gaba_as_built_0.2 | cue4 | P2 | 1.00 | 2.33 | 0.00 (0) | 0.0 | 0 | 32.2 | 5 |
| K3_scaled_bg02 | gaba_as_built_0.2 | cue2 | P2 | 0.67 | 3.35 | 0.00 (0) | 0.0 | 0 | 31.6 | 5 |
| K3_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue4 | P0 | 1.00 | 2.35 | 0.00 (0) | 0.0 | 1 | 42.5 | 7 |
| K3_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue2 | P0 | 0.83 | 4.3 | 0.00 (0) | 0.0 | 1 | 41.6 | 7 |
| K3_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue4 | P1 | 1.00 | 2.3 | 0.00 (0) | 0.0 | 1 | 40.8 | 7 |
| K3_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue2 | P1 | 1.00 | 3.6 | 0.00 (0) | 0.0 | 1 | 40.5 | 7 |
| K3_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue4 | P2 | 1.00 | 2.33 | 0.00 (0) | 0.0 | 0 | 32.2 | 5 |
| K3_scaled_prune_intdrive1 | gaba_as_built_0.2 | cue2 | P2 | 0.67 | 3.35 | 0.00 (0) | 0.0 | 0 | 31.6 | 5 |

## Bio limits

sim 127 parameters: {'days': 25, 'pyramidal': 67, 'interneuron': 27, 'minneuronseparation': 15, 'shape.radius': 124, 'shape.thickness': 42, 'dm.weight': 0.9} -> hard limits passed (bio_check.assert_hard_limits). Per-receptor g_peak (median, nS): {'AMPA': 0.9799999509538923, 'GABA': 0.7999999523162842, 'NMDA': 0.550000011920929}. Programmed weights in [0.00, 1.00]; every Conductance_nS <= pair g_peak_sum.
