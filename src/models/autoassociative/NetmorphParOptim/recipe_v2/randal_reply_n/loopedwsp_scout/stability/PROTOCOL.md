# stability: protocol (written 2026-11-24 before the reduced model was run on any stored event; not edited afterwards, changes go to DEVIATIONS in README)

Task (John, idea 1 of the LoopedWSP scout): offline analysis of whether the completed 17-cell state is self-sustaining once adaptation and inhibition are included; predict which arms terminate and why W70 works on s77777 but not s66666; give parameter ranges for fable-knobs' reset/AHP tests; check against stored data. 0 sims, no NES call, nothing under neuron_reset_ahp/ touched or written (read-only reading of its PREREGISTRATION.md, PLAN.md, results.md, cell_offline.py).

## What I already knew (so this is NOT a blind test)
- The outcome-level results of addenda B and C (summary in partial_cue/README.md) were known to me before this analysis; so was fable-knobs' stored result for N0 and S2 on s77777 (results.md: S2 75% 5/6, 50% 1/6, median last 232 ms, spikes/member 20.6). I had NOT opened rawB/rawC event-level spikes with the reduced model.
- So "check against stored data" is a retrodiction for B/C and for S2-s77777. The only genuinely forward predictions are for arms of neuron_reset_ahp that were not in its results.md when I read it (R, RS2, RS3, S2 on s66666, r 0.56 runs); I will write them to PREDICTIONS_FORWARD.md before reading any of their raw files for those arms, and will not read them until the check is asked for.

## Model (rn.py): exact cell equations (cell_offline.py / LIFCNeuron.cpp), exact programmed member matrices (fllib Net + pwlib.arm_matrix), Netmorph synapse kernels, NMDA = min(r AMPA, 0.5612 G), members only; interneuron feedback = ONE free scalar kappa (nS per member spike per member, delay 1 + 2.5 ms)
## Fitting policy (fixed now)
- Free quantities: kappa (inhibition), and nothing else. kappa is calibrated on ONE run only: s77777 LH r1 GABA x1 (match of mean member spikes in the 450 ms of non-contaminated 75% events to within 10%). Every other arm, model, and r is then out-of-sample for the parameters (not for my knowledge of outcomes).
- Inhibition tests: GABA x2 = 2 kappa (stored s77777_L0_r1_f2), LI arm (stored) = larger kappa; sensitivity of every arm to kappa in {0, 0.5, 1, 2, 4} x kappa_cal.
- No parameter is changed after seeing a mismatch; mismatches are reported as MISS and listed with candidate causes (clearly labelled post hoc).

## Scoring (fixed now)
Per stored run (s77777/s66666 x LH, W70, W50, H2 where it exists, L0, LI) and per event class: complete, recruit, reverb (member spikes in 450 ms > 50), median mem450, median last member spike. Agreement counted per class as: boolean rates within 1 event of 6 (or 4); mem450 within a factor 2; last within 100 ms. "Predicts" = >= 75% of the compared cells agree AND the ordering of arms by median mem450 within each model matches (Spearman). Termination prediction, per arm and model, is decided by the model only: terminates if the median last member spike of the completing 75% events is < 100 ms.
