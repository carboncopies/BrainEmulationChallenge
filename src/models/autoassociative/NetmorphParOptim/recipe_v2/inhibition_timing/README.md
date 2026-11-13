# Inhibition timing test (2026-11-13), own NES, base model v2-arbor-S10000 (never modified)
35 sims created (ids 214-248: 5 probe/roundtrip, 28 batch, 2 ripple cue3), all deleted (GetStatus code 2 for every id). Patched model copies v2-arbor-S1-inh{P1,P2,P3,P1u} deleted from the models dir (regenerate with patch_inh.py; spec in run_inh.py VAR).
Files: comp2neuron.py/recmap.py (compartment->neuron map, receptor -> pre/post exact: file pair table == growth dump, 13050 pairs), patch_inh.py (patcher), probe_run.py/probe_result.json (edit honoured?), rt_test.py/rt_result.json (ModelLoad->ModelSave roundtrip, all 113,267 records identical), natural_check.py/.json, design_inh.py/groups_P1,P3.json, gen_pairs.py, run_inh.py, batch_*.sh, raw_*.json, summary.json (summarize.py).
## Edits
- Pyr->Int AMPA Weight=1.0 -> 4.97x PSP (honoured). PeakConductance x3 -> 2.99x (honoured, exact). Both -> 14.7x. Rise/Decay edits honoured (waveform changes).
- Weight >1 (2.0, 5.0): loaded and reported by the connectome, but conductance is clipped at PeakConductance (W=2: 1.14x of W=1 at 3 ms, W=5: 1.17x; only a faster rise). Weight>1 is not a drive lever; raise PeakConductance instead.
- GABA Weight x2.5/x5, Rise 0.3, Decay 3.3: loaded unchanged (roundtrip), faster IPSP onset seen in Vm. Int->Int weight/decay edits only roundtrip-verified, not used in any variant.
## Natural bound
Pyr->Int per-connection unitary conductance at weight 1 (R3) is ALREADY 1.31 nS mean (median 0.98, p90 1.96, max 4.9) vs natural 0.85: 1.54x natural; 7.6% of pairs (43/569) above 3x natural. Scale to natural mean = 0.649 (REDUCES drive; 0.4% above 3x). Drivable (>=13.84 nS from best 8 cells): 4 of 48 at 0.65x, 7 at 1.0x, 21 at 1.95x (=3x natural mean; 24% of pairs above 2.55 nS). The weakness is the number of Pyr inputs per interneuron (11.9 pairs, 15.8 synapses), not per-connection strength.
## Variants (R3 weights, recall protocol of ripple_S1_R3)
P1 = Pyr->Int x0.649 (natural), GABA x2.5, 0.3/3.3, groups_P1 (redesigned). P2 = P1 with GABA x5. P3 = Pyr->Int x1.948 (3x natural mean, NON-natural), GABA x2.5 kin, groups_P3. P1u = Pyr->Int x1.0 (R3 as is), GABA x2.5 kin, original R3 groups.
See summary.json and the final report for results.
