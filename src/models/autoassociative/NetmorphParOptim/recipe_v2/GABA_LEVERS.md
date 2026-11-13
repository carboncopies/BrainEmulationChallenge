# GABA strength/count levers (read-only source investigation, 2026-11-13)
Tags: CONFIRMED = read in source/data; INFERENCE = reasoned, not run.
NES = /home/johnjose/BrainGenix/BrainGenix-NES (HEAD detached at 1.7.1 + 2 commits; Netmorph at ThirdParty/NetmorphCMake/Source).

## (1) Where "GABA 0.2" is set
CONFIRMED. The 0.2 is the dimensionless receptor `Weight`, not 0.2 nS.
- Source/Core/Netmorph/NetmorphManagerThread.cpp:457 `C.Weight = 0.2;` for EVERY Netmorph receptor (AMPA/NMDA/GABA alike), hard-coded, per synapse (per LIFCReceptor).
- Per-synapse peak conductance: :375-376 `gaba_raw.ReceptorPeakConductance_nS = 80e-3; ReceptorQuantity = 10;` -> Simulation.cpp:304 `PeakConductance_nS = Quantity*Unit` = 0.8 nS per GABA synapse (AMPA :366-367 49*0.02 = 0.98 nS; NMDA 11*0.05 = 0.55 nS).
- So effective GABA = 0.2*0.8 = 0.16 nS per synapse (before kernel). roundtrip_result.json agrees: GABA pairs have GPeakSum 4.8/6.4/13.6 = 6/8/17 synapses x 0.8, weight 0.2.
- Per pair: abstracted mode merges all same-(pre,post,NT) receptors into one LIFCReceptorData: Simulation.cpp:279-288, Neuron.cpp:70-80: g_peak_sum = SUM of synapse peaks; weight = sum(w_i*g_i)/sum(g_i). Pair GABA conductance = weight * g_peak_sum, so it scales linearly with synapse COUNT (n*0.16 nS) and with weight.
- Reversal -70 mV, rise 0.5, decay 10 ms: :360-363. GABA copies nmda then overrides, so STDP_Method = STDPNONE (:352) -> no STDP clamp of weight to [0,1].
- Not read from any config/yaml; compiled constants. Our growth files (grow_v3.py, nesvbp-autoassociative) contain no receptor/P_receptor lines (grep).

## (2) dm.weight
CONFIRMED NOT a synaptic parameter. Excel `dm.weight` -> `all_axons.axondm.dm_weight` (gen_autonm_labels.py:488-490, :734); Netmorph parses it as axon direction-model contributor weight (axon_direction_model.cc:193,238). It steers axon growth only. No growth parameter scales GABA strength.

## (3) More Int->Pyr synapses without raising B_inf
CONFIRMED: no multi-synapse-per-contact, density or bouton spacing parameter exists. synapse_formation_model.cc:114 comment: "If multiple synapses between the same pair of segments are a possibility..." (unimplemented). One candidate per axon/dendrite segment pair (likelihood is only -1/0/1, :128-ish); P_receptor.<pre>.<post>.GABAR (synapse_formation_model.cc:45, :495) is a probability <=1 (default Int->Pyr 1.0, hh:150ff) so it cannot raise counts above 1 per candidate. Only count levers: D_synmax (already used), arbor size/density (B_inf, tau, min_node_interval, soma separation), and `synapse_formation.PDF` (acceptance already saturated with delta PDF - INFERENCE). `include_spines` (cc:51) tags spines but does not add synapses (INFERENCE; not traced).

## (4) API / model-file routes to GABA conductance
- API: SetPrePostStrength / SetAllStrength / Batch: AMPA only (LIFCNeuron.cpp:543-559; zeroes GABA; returns false for GABA-only pair; roundtrip_result.json set_gaba StatusCode 2). CONFIRMED.
- LIFCReceptor/Create (ModelRPCInterface.cpp:179-232) takes Neurotransmitter, PeakConductance, Weight, PSPRise/Decay, reversal: full control, but ADDS a receptor on an existing/new compartment pair (hand-built); no delete/edit. Creating extra GABA receptors between Int and Pyr somas' existing compartments is possible in principle (needs compartment IDs from the loaded model) -> would raise count and conductance. INFERENCE for feasibility (not run); Create path CONFIRMED to exist (NES_API_GAPS_AND_SPEC.md:32).
- **Model file edit (strongest route)**: saved model is a flat binary, not JSON: SaverInfo, geometries, compartments, then `LIFCReceptorBase[]` (Simulation.cpp:675 ordering, :717-718 write, :883-884 read), each with Weight, PeakConductance_nS, PSPRise/Decay_ms, ReversalPotential_mV, Neurotransmitter (Receptor.h:88-112). Load path (Simulation.cpp:1006-1009) builds LIFCReceptor from those fields and calls AddLIFCReceptor, which rebuilds the aggregate from file Weight*PeakConductance (Neuron.cpp:46-47,77-79). So editing Weight/PeakConductance of Neurotransmitter==GABA(1) records in the file and ModelLoad-ing is honored. CONFIRMED by source; not executed. The modelsave bug (1f2f2b3cf) is irrelevant for this route (it concerns saving weights edited live via the API; file edit bypasses it). Edit offline on a COPY; needs header sizeof(SaveLoadPrior)+sizeof(SaverInfo) and struct sizes from a build of this source (a small C++/ctypes reader).
- Also possible: after ModelLoad, no API can change it, so edit must precede load.

## (5) Is 0.2 baked into the compiled binary only?
Yes for freshly grown nets (constants above), but they are then persisted per receptor in the model file (see 4), so already-grown models are editable without recompiling.

## Natural bounds (INFERENCE, check CA3_NATURAL_RANGES.md)
Weight 0.2 -> 1.0 gives 0.8 nS/synapse, 5x; within the 0.8 nS "unit" peak. Going higher needs PeakConductance_nS edit; keep unitary IPSC within literature (~0.5-3 nS perisomatic, verify). g_k capped at g_peak_sum (Neuron.cpp:152-155) so weight>1 gives no extra peak anyway.

## Minimal source change (if file-edit is not enough)
Option A, 1 line, NetmorphManagerThread.cpp:457: `C.Weight = (C.Neurotransmitter == Connections::GABA) ? 1.0f : 0.2f;` (or scale gaba_raw.ReceptorQuantity at :376, e.g. 10 -> 30).
Option B: read an env var/NES.yaml value instead of the literal.
Build: CONFIRMED a configured Release tree exists at /home/johnjose/BrainGenix/BrainGenix-NES/Build (Makefile, CMakeCache home = that dir); current binary Binaries/BrainGenix-NES (Oct 4). We run our own NES, so rebuild + run on our own instance is possible; this affects only newly grown nets (re-growth needed, ~1 h each per grow_v3 CAP). Build time/deps not tested. Using the modelsave worktree (/home/johnjose/BrainGenix/wt/nes-modelsave) as base would also fix ModelSave of edited weights.
