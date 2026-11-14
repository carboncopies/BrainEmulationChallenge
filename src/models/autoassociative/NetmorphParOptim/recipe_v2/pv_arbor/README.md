# PV-basket-size interneuron arbors with NetMorph knobs only (own NES 8000/7999/8001), 2026-11-13/14
Scripts: grow_pv.py (driver, copy of dendrite_rerun/grow_dend.py; one run per process), run_all.sh (two groups of 3 concurrent runs), measure.py (arbor length/extent from NetMorph txt output), analyze_pv.py (all metrics -> pv_results.json). Data: pv_results.json, S1_arbor_measure.json, grow_V*/ (model files, run.log, viz dump). crashed_attempt/ = logs of the first launch (see Incidents).
Common to all: seed 20240628, days 25, 96 pyramidal, minsep 10, radius 120, thickness 30, dm.weight 0.9, D_synmax 1.5 (pyr-pyr) / 0.1 (the three interneuron pairs) as in S1 (read back from each run's .nibr.clp), bio_check.assert_hard_limits passed for every variant (the 7 hard-limited params only; D_synmax kept at 1.5/0.1), interneuron min_basal 6 / max_basal 10, interneuron axon block restated (van_Pelt, tau 1681541, E 0.319251, same_arbor, min_node_interval 0), dendrite block restated (van_Pelt, tau 259680, E 0.73, min_node_interval 2). growth_F, growth_nu0 and the interneuron axon nu0/F were NOT touched (design rule, ARBOR_DESIGN.md items 5, 10). Only knobs varied: axon B_inf, dendrite B_inf, interneuron count. Reference S1 = dendrite_rerun/grow_S1 (48 int, basal 6-10, dend B_inf 3.5, axon B_inf 26; model v2-arbor-S10000).

## Definitions (units)
- Length (um, NetMorph coordinates): for every node (continuation, bifurcation, growth cone) the Euclidean distance to its parent node, summed per neuron and fibre type (dendrite/axon) from `*_net.txt.{rootnodes,continuationnodes,bifurcationnodes,growthcones}`. This IS extractable (the earlier cone-count-only approach was unnecessary). The soma-to-root stub is not counted. Straight-line between nodes; nodes are about 5 um apart (turn_separation 5), so tortuosity below that scale is not captured.
- Extent: max Euclidean distance of any node from the soma centre, averaged over cells ("reach"). Literature extent figures (CA1 780-1740 um lateral) are not directly comparable (different tissue size).
- Pairs / synapses per pair: from the NES viz dump (num_receptors per pre,post), Pyr->Int AMPA, Int->Pyr and Int->Int GABA.
- Inhibitory fraction, two conventions (the bar is ambiguous): A = Int->Pyr/(Int->Pyr + Pyr->Pyr) (convention used in earlier reports); B = (Int->Pyr + Int->Int)/(all synapses).
- Drivable by 8-cell volley (primary): same criterion as robustness_S1/rdesign.py `best8`: best 8 pyramidal presynaptic cells at weight 1 (4 cue cells capped at 10 nS summed + 4 non-cue), summed g_peak >= 13.84 nS. Also "simple" = sum over all pyramidal inputs >= 13.84 (the earlier dendrite_rerun convention, an upper bound).

## 1. S1 versus literature targets (per interneuron, n=48)
| quantity | S1 measured (mean; range) | target | verdict |
|---|---|---|---|
| dendrite total length | 7,134 um (4,174-11,667) | 5,000-9,000 | already in range |
| axon total length | 77,554 um (38,395-131,697); 15,620 nodes/cell | 30,000-45,000 | ABOVE target (1.7x the top); cone count 416/cell |
| axon reach from soma | mean 133, max 185 um | CA1 780-1740 um; CA3 area 0.67 mm2 | tiny: whole arbor is inside the 120 um-radius disc |
| pyramidal targets per interneuron | 17.1 of 96 (median 17, max 30) | "many"; ~full coverage is the design intent | low (18%) |
| synapses per Int->Pyr pair | 1.60 | ~11 | 7x too low |
| Int->Pyr / Pyr->Int / Int->Int synapses | 1314 / 760 / 1709 | | |
So in S1 the length targets for dendrite are met and axon length is over target; the shortfall is in synapses per pair (1.6 vs 11) and targets per cell, not in length.

## 2. Variants (all 96 pyramidal, seed 20240628, bio_check pass)
Pyr->Pyr change is vs S1 (57,702). INFERENCE/caveat: Pyr->Pyr is a realisation-level random effect (earlier reruns: seed-only change moved it +20%, B_inf changes -14%/+8.5%), so the 5% rule mostly tests luck, not the lever.
| run | n_int | ax B_inf | dend B_inf | dend len (um) | axon len (um) | axon reach | Pyr->Pyr (vs S1) | Pyr->Int | Int->Pyr | Int->Int | pairs P->I / I->P / I->I | syn/pair I->P | pyr targets/int | inhib frac A / B | drivable 8-cell (simple) | zero-input ints | bio_check |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 (ref) | 48 | 26 | 3.5 | 7,134 | 77,554 | 133 | 57,702 | 760 | 1314 | 1709 | 569/823/719 | 1.60 | 17.1 | 2.23% / 4.92% | 7 (13) | 7 | pass |
| V1 | 48 | 20 | 3.5 | 7,146 | 44,870 | 127 | 58,959 (+2.2% ok) | 667 | 832 | 837 | 532/527/522 | 1.58 | 11.0 | 1.39% / 2.72% | 6 (14) | 12 | pass |
| V2 | 48 | 20 | 5 | 9,512 | 44,889 | 123 | 84,525 (+46.5% REJECT) | 803 | 1057 | 942 | 628/714/563 | 1.48 | 14.9 | 1.24% / 2.29% | 10 (17) | 13 | pass |
| V3 | 48 | 23 | 5 | 9,640 | 60,580 | 128 | 60,000 (+4.0% ok) | 952 | 940 | 1523 | 619/682/617 | 1.38 | 14.2 | 1.54% / 3.88% | 10 (14) | 11 | pass |
| V4 | 48 | 26 | 5 | 9,962 | 75,196 | 129 | 76,111 (+31.9% REJECT) | 885 | 1588 | 1614 | 670/916/799 | 1.73 | 19.1 | 2.04% / 3.99% | 8 (19) | 9 | pass |
| V5 | 20 | 20 | 5 | 9,682 | 44,857 | 125 | 68,438 (+18.6% REJECT) | 293 | 349 | 113 | 223/228/69 | 1.53 | 11.4 | 0.51% / 0.67% | 4 (6) | 6 | pass |
| V6 | 20 | 26 | 5 | 9,968 | 80,339 | 125 | 63,780 (+10.5% REJECT) | 560 | 553 | 409 | 384/387/151 | 1.43 | 19.4 | 0.86% / 1.47% | 6 (10) | 4 | pass |
Walls: V1 2133 s, V2 2154, V3 2787, V4 3381, V5 1499, V6 2083 (3 concurrent). Per-cell ranges are in pv_results.json (axon length range across cells is wide, e.g. V3 28,014-100,943).

## 3. Findings
1. Lengths are controllable with B_inf alone: axon B_inf 20 gives 44.9k um (inside 30-45k), 23 gives 60.6k, 26 gives 75-78k; dendrite B_inf 3.5 -> 7.1k, 5 -> 9.5-10k (top of / just above the 5-9k range). Both total-length targets can be met simultaneously (V1: dend 7.1k + axon 44.9k; V2: dend 9.5k + axon 44.9k).
2. Hitting the length targets does NOT raise synaptic output; shortening the axon to the PV target (V1) lowers Int->Pyr from 1314 to 832 and the drivable count (8-cell) from 7 to 6. More axon length gives more Int->Pyr only modestly (V4 1588 vs S1 1314 with dendrites +40%).
3. Synapses per Int->Pyr pair stay at 1.4-1.7 in every variant (target ~11), and pyramidal targets per interneuron stay at 11-19 of 96. INFERENCE (not tested): the per-pair cap D_synmax=0.1 for interneuron pairs (held by instruction) and the 120 um disc geometry (axon reach ~125-133 um, all arbors overlapping within the same small volume) limit this; bumping D_synmax is outside the allowed range here.
4. Axon reach stays about 125-133 um in all variants: more length means more branching inside the disc, not a wider arbor. Real PV axons extend 0.8-1.7 mm; with radius at most 200 um (hard limit) this cannot be matched.
5. 20 interneurons (V5, V6) are worse on every count: Int->Pyr 349/553 (0.5-0.9% inhibitory, A), drivable 4-6 (8-cell). More interneurons (48) is better here because input and output synapses scale with cell count.
6. Pyr->Pyr: V1 (+2.2%) and V3 (+4.0%) pass the 5% rule; V2, V4, V5, V6 do not.

## 4. Pre-set bar (>=16 drivable interneurons AND 3-6% inhibitory synapses AND Pyr->Pyr within 5%)
No variant meets it.
- Drivable (8-cell, primary criterion): maximum 10 (V2, V3) of 48; none reaches 16. With the looser "simple" count V2 (17) and V4 (19) reach >=16, but both fail the Pyr->Pyr 5% rule (+46.5%, +31.9%).
- Inhibitory fraction: under convention A the maximum is 2.23% (S1) / 2.04% (V4), never 3%. Under convention B V3 (3.88%) and V4 (3.99%), and S1 itself (4.92%), are inside 3-6%; V3 passes Pyr->Pyr (+4.0%) but only 10 drivable (8-cell) / 14 (simple).
- Best compromise: V3 (dendrite 9.6k um slightly above 9k, axon 60.6k above 45k) passes Pyr->Pyr and convention B but not drivable>=16. V1 is the only variant with both lengths and Pyr->Pyr in range but fails drivable and inhibitory bars.
Conclusion: the NetMorph knobs tested (B_inf of axon and dendrite, interneuron count) can hit the PV total-length targets but do not bring the synaptic connectivity (synapses per pair, targets per cell, drivable interneurons) to PV values within the hard limits and D_synmax 1.5/0.1.

## 5. Honest limits
- One seed (20240628), one realisation per variant; Pyr->Pyr and every count carry realisation noise of order +-20% (earlier reruns), so differences like V1 vs V3 on drivable (6 vs 10) are not demonstrated effects. No repeat seeds were run.
- Lengths are node-chain lengths at NetMorph resolution, compared with literature lengths from different species/preparations (slice axons are lower bounds, per the notes file); the comparison is order-of-magnitude.
- Not varied: E, tau, interneuron axon growth_nu0/growth_F (excluded by the fixed-config rule), turn/direction parameters, D_synmax.
- 8-cell drivable criterion at weight 1 uses summed conductance as in rdesign.py best8; it was not validated by a dynamic simulation here.
## Incidents and housekeeping
- First launch (6 concurrent NES sims, ids 265-270) crashed the NES server (`terminate called ... std::system_error: Resource temporarily unavailable`, nes log tail) after about 18 min; the clients reported "batch did NOT complete". The sims were lost with the process (INFERENCE: not verified via API; the NES process was restarted, so none are resident). I restarted NES with Tools/Run.sh (log recipe/server_logs/nes_1113_pv.log) and reran the 6 runs 3 at a time. Other users' simulations on that NES (if any) were lost with the crash.
- Rerun sims (ids 0-5 on the restarted NES) were each deleted by gen_autonm_labels -deleteresident (run.log "Deleted resident simulation" for all six). No sims were created otherwise; no email, no git. Saved models v2-pv-V1..V6 (name suffix 0000 appended by the generator).
