# What the NES API must expose for GABA (and the other knobs) — from building this test (2026-11-22)
Source read: /home/johnjose/BrainGenix/wt/nes-linefix (the line-379 build; the API code is the same as main NES as far as these routes go, not re-checked line by line). CONFIRMED = read in source and/or observed in this task.

## What exists today and why it is not enough
| need | today | evidence |
|---|---|---|
| set GABA strength per pair | **not possible**. `Simulation/SetPrePostStrength` and `BatchSetPrePostStrength` set the first AMPA receptor-group of the pair and set every other receptor group of that pair (NMDA, GABA) to weight 0. For an Int->X pair (GABA only) the call returns false but still zeroes the GABA. So the API can silence GABA, not set it | LIFCNeuron.cpp:543-559 (`UpdatePrePostStrength`); CONFIRMED (gaba_check_l used it to silence; roundtrip_result.json StatusCode 2 for a GABA set) |
| set GABA strength globally | **not possible**. `SetAllStrength` loops the same per-pair call over all pairs (Simulation.cpp:1375-1381), so it sets every AMPA pair to one conductance and zeroes all NMDA and GABA | CONFIRMED by source |
| keep NMDA when programming AMPA | **not possible**. Any AMPA programming through the API zeroes that pair's NMDA. Every recall run in this repo so far (dyn2.py, R3 recipe) therefore had NMDA = 0 on every Pyr->Pyr and Pyr->Int pair | LIFCNeuron.cpp:549-553; CONFIRMED here (connectome NMDA nonzero 0 after apply_pairs, V0 run) |
| raise a pair above its grown conductance | weight is capped: g_k <= g_peak_sum (Neuron.cpp:149-158, `Update_Conductance`), so weight > 1 adds nothing. Going above the grown peak needs PeakConductance, which no route edits | CONFIRMED by source |
| edit AHP / ADP / adaptive threshold | `Simulation/Neuron/LIFC/Edit` exists but only edits RestingPotential, ResetPotential, SpikeThreshold, MembraneResistance, MembraneCapacitance, RefractoryPeriod, SpikeDepolarization (ModelRPCInterface.cpp:682-725). AHP (fast, slow), ADP, fatigue and adaptive-threshold fields are settable only at `Neuron/LIFC/Create` (ModelRPCInterface.cpp:584-660), not for a loaded Netmorph model | CONFIRMED by source |
| receptor kinetics (GABA decay, E_GABA) | fixed per receptor in the model file (Netmorph defaults: GABA rise 0.5, decay 10 ms, E -70, onset delay 1.0 ms; NetmorphManagerThread.cpp:360-376). `LIFCReceptor/Create` can add receptors, nothing edits or deletes them | CONFIRMED (read from the s33333 model file: all GABA records 0.5/10/-70/1.0001) |
| see GABA in the recording | `GetRecording` returns Vm only (and spike times). Conductances (g_GABA, g_AMPA, g_NMDA, g_AHP, g_ADP) are not recorded; in this task g_GABA was reconstructed offline from interneuron spikes and connectome weights | LIFCNeuron.cpp:500 `Record(t_ms)`; CONFIRMED |
| read GABA strength | `GetConnectome` returns weight and GPeakSum per (pre, post, type) including GABA (type 2) and NMDA (type 3): reading works | CONFIRMED |

## How this task worked around it (not a fix)
I edited copies of the saved model file before loading: receptor Weight per record (AMPA programming, NMDA ratio, GABA x factor), receptor PeakConductance (Pyr->Int x2 for the lateral-inhibition knob), and neuron fields (AHP, ADP) in each LIFCNeuronStruct record (layout from Neuron.h, verified on the file: 116 neurons, IDs 0-115, principal/interneuron defaults as in NetmorphManagerThread.cpp:593-643). Validation V0: file programming and API programming gave identical spikes (512 spikes, max difference 0.0005 ms). This works for us but it is a binary hack: it depends on struct layout and compiler, so it is not a user route.

## Minimal API additions (proposal)
1. `SetPrePostStrength` / `BatchSetPrePostStrength` with an optional `Neurotransmitter` field ("AMPA" | "NMDA" | "GABA"). It sets only that receptor group and leaves the others unchanged. Without the field: current behaviour (back-compatible).
2. `SetAllStrength` / a scale variant with `Neurotransmitter` and `Scale` (multiply existing weights), so "GABA x2 everywhere" is one call.
3. Allow conductance above g_peak_sum (or a `PeakConductance` edit) for a pair, so strengthening is not capped at the grown synapse count.
4. Extend `Neuron/LIFC/Edit` to the AHP, ADP, fatigue and adaptive-threshold fields that `Create` already accepts.
5. A receptor-group kinetics edit by type (rise, decay, reversal, onset delay), for "GABA decay 10 -> 3.3 ms" or "E_GABA -70 -> -75" tests.
6. Optional recording of per-neuron summed conductance by type (g_AMPA, g_NMDA, g_GABA, g_AHP, g_ADP), so Vm traces can be read with their causes.
Items 1 and 6 matter most for Randal's question: without 1, GABA strength can only be changed by editing files; without 6, a Vm trace does not show whether GABA was there.
