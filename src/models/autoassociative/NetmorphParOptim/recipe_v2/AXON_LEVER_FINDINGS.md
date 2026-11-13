# Axon lever findings (read-only; nothing run)

Source: /home/johnjose/BrainGenix/wt/nes-nt-24-verify/ThirdParty/NetmorphCMake/Source (S/). Evidence dirs: /var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/<uuid>/.

## 1. Cause
- CONFIRMED-BY-RUN-OUTPUT: the directives were matched to the interneuron type and applied. The `<ts>_report` file (B: 5bc0cf01.../202611120955_report:220, :369) shows `Subset 'all_interneuron_axons.' ... van_Pelt (B_inf=13.22, tau=864000.00, E=0.32)`, both at universal level and region In. Pyramidal axons stay at tau=1681541 (:218). The earlier "directives not parsed/overridden" hypothesis is therefore ruled out. Earlier finding confirmed: `In.all_axons.*` (B_inf=10, tau=319680) only affects the unused In.all_axons set (:361); no neuron type uses it (S/prepost_structure.cc:33-45 maps interneuron->all_interneuron_axons; S/neuron.cc:158-161, :257).
- CONFIRMED-BY-DATA: tau did act, in time. Interneuron axon bifurcation-time median: A 14.6 d, B 11.2 d, D 6.6 d (from *.bifurcationnodes). Total count did not follow: bifurcations/cell 73, 62, 72.
- INFERENCE (not verified): the arbor-size ceiling is set by something other than tau. The mean-field n^E = 1+E*B_inf*(1-exp(-t/tau)) (S/branching_models.cc:201-220) predicts 143 at tau=10 d, but observed 62. The formula matches only the baseline (80 vs 74), so it is not validated as a count predictor. Candidates: branching only happens during elongation (S/dendritic_growth_model.cc:392), so cones stalled at the 240 um x 30 um disc/pia boundary cannot branch; TSBM centrifugal-order factor (S=-0.205, branching_models.cc:322); I did not trace either.
- Side effect I found: our restated block set `min_node_interval=2.0` for interneuron axons only. Every other set reports 0.000 (report :212-221). Segment must be >= 2 um to branch (dendritic_growth_model.cc:392). Small, but a confound B/C/D introduced.

## 2. Syntax that changes size
Tau only moves timing. Final count is set by `E*B_inf` (and E). The directive form is already right: `all_interneuron_axons.branching_model=van_Pelt; .B_inf; .tau; .E; .E_competes_with=same_arbor;` (all five must be restated; omit min_node_interval or set 0.0 to match others). Raise `all_interneuron_axons.B_inf` (e.g. 26), keep tau. Length levers (`all_interneuron_axons.arbor_elongation_model=van_Pelt; .growth_nu0; .growth_F`) also parse (report :133) but were excluded by the design rule. Whether B_inf raises counts above the ceiling is untested.

## 3. Pyr->Pyr drift
NOT explained by this cause. Pyramidal axon and dendrite sets are unchanged in the reports. Pyramidal cone counts moved only about 1-5%. Most likely a new random realisation (inference; not tested). A control rerun with the same config and a different seed would give the spread.

## 4. Proposed minimal rerun (not executed)
Config B2 = baseline a plus: `all_interneuron_axons.branching_model=van_Pelt; B_inf=26; tau=1681541; E=0.319251; E_competes_with=same_arbor; min_node_interval=0.0;`. Compare with A (axon-equal baseline). Success check first: interneuron axon growth cones/cell (target >>74) and the report line. Add a baseline-a rerun with a second seed to measure Pyr->Pyr noise. If cones stay near 70, the ceiling is spatial (inspect axon cone positions near the disc edge) rather than a parameter.

Not verified: that the running NES binary is built from this S/ tree (report output matches its format, so likely); the real cause of the ceiling.
