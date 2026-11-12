# NES API gaps and proposed spec for weight-space programming

Date: 2026-11-11. Read-only study; nothing was run against the NES server and no repo was modified.
Code read: BrainGenix-NES checked out at tag 1.7.1 (detached HEAD), Python client in BrainEmulationChallenge/PythonClient.
Path shorthand: `NES/` = `/home/johnjose/BrainGenix/BrainGenix-NES/Source/Core/`, `Sim/` = `NES/Simulator/`,
`PY/` = `/home/johnjose/BrainGenix/BrainEmulationChallenge/PythonClient/BrainGenix/NES/`.
"(inferred)" marks anything not directly visible in code. Line numbers are for 1.7.1.

## 0. What our experiments actually call
`wt/bec-netmorph/.../NetmorphParOptim/weight_space/server_apply.py` (header lines 12-13 and 87-96) and the fable_loop scripts use:
GetStatus, GetSomaPositions, GetConnectome, GetAbstractConnectome, BatchSetPrePostStrength, SetSpecificAPTimes, SetSTDP(False),
RecordAll, RunAndWait, GetSpikeTimes, ModelSave/ModelLoad, SetLIFCAbstractedFunctional, SetLIFCPreciseSpikeTimes.
Neuron class is LIFC (LIFCNeuron), built by Netmorph inside NES.

## 1. Inventory of existing routes (server) and client methods

All routes registered with `_RPCManager->AddRoute(...)`: simulation routes `Sim/RPC/SimulationRPCInterface.cpp:59-98`,
model routes `Sim/RPC/ModelRPCInterface.cpp:41-67`, Netmorph routes `NES/Netmorph/NetmorphRPCInterface.cpp:31-34`.
Default handler behaviour: a route is rejected with `BGStatusSimulationBusy` while the sim is running unless it opts in
(`NES/RPC/RPCHandlerHelper.cpp:99-103`). Numeric params are only type-checked (`is_number`), never range-checked
(`RPCHandlerHelper.cpp:264-276`); no NaN/inf/negative check anywhere in the handlers below.

### 1.1 Weights / conductances / synapses
| Route (client method) | Args | What the C++ does | Limitations |
|---|---|---|---|
| `Simulation/SetPrePostStrength` (`SetPrePostStrength`, PY Simulation.py:412) | SimulationID, PreSyn int, PostSyn int, Conductance_nS float | RPC `SimulationRPCInterface.cpp:595-615` -> `Simulation::UpdatePrePostStrength` (`Sim/Structs/Simulation.cpp:1358-1370`) -> `LIFCNeuron::UpdatePrePostStrength` (`Sim/LIFCompartmental/LIFCNeuron.cpp:543-560`) | See 1.4. One scalar per pair; AMPA only; zeroes everything else from that pre neuron; no range check; fails (false) only if post ID >= N or no AMPA found. |
| `Simulation/SetAllStrength` (`SetAllStrength`, :426) | Conductance_nS | RPC `:617-632` -> `Simulation::UpdateAllStrength` (`Simulation.cpp:1376-1382`): loops over ALL N x N pairs calling UpdatePrePostStrength; return values ignored | Sets first-AMPA weight of every connected pair to value/g_peak_sum and zeroes all NMDA and GABA everywhere. Value 0 = "silence the whole network incl. inhibition". Not undoable except ModelLoad (Reset behaviour on weights not determined). O(N^2) loop. |
| `Simulation/BatchSetPrePostStrength` (`BatchSetPrePostStrength`, :448) | PreSyn[], PostSyn[], Conductance_nS[] | RPC `:634-653` -> `UpdateBatchPrePostStrength` (`Simulation.cpp:1383-1391`): size check, then applies entries in order, returns false at first failing entry | NOT atomic: entries before the failure stay applied, and the failing entry itself has already zeroed that pre neuron's other receptors (see 1.4). Client says it "returns an error if connections do not exist" (PY :441-447) but gives no index of the failing entry. |
| `Simulation/GetConnectome` (`GetConnectome`, :557; managed task) | none | `Simulation::GetConnectomeJSON` (`Simulation.cpp:1579-1622`); LIFC branch uses `LIFCNeuron::GetConnectomeTargetsJSON` (`LIFCNeuron.cpp:~525-541`) | READ path for per-neurotransmitter weights already exists: per pre neuron, arrays ConnectionTargets, ConnectionTypes (1=AMPA, 2=GABA, 3=NMDA, `LIFCNeuron.cpp:~510-523`), ConnectionWeights (= abstracted `weight`, dimensionless, includes STDP drift), ConnectionGPeakSum (nS), NumReceptors. One row per (pre, post, NT) in abstracted mode. Whole-network dump, no filter. |
| `Simulation/GetAbstractConnectome` (:569) | Sparse, NonZero | `Simulation.cpp:1648-1700`, `LIFCNeuron::GetAbstractConnection` (`LIFCNeuron.cpp:563-583`) | Counts receptors per pair, AMPA+GABA only (NMDA skipped to avoid double count), NonZero counts those with weight != 0. |
| `Simulation/LIFCAbstractedFunctional` (`SetLIFCAbstractedFunctional`, :210) | UseAbstractedFunctional | sets `Simulation::use_abstracted_LIF_receptors` (`SimulationRPCInterface.cpp:485-500`, default true `Simulation.h:118`) | Only affects receptors created AFTER the call (`Simulation.cpp:279-296`). Netmorph builds happen inside NES, so you must call it before `Netmorph_Start` (inferred from build order). |
| `Simulation/LIFCReceptor/Create`, `NetmorphLIFCReceptor/Create` (`AddLIFCReceptor`, `AddNetmorphLIFCReceptor`, :259-262) | full receptor params: Source/DestinationCompartmentID, ReversalPotential_mV, PSPRise_ms, PSPDecay_ms, PeakConductance_nS, Weight, OnsetDelay_ms, Neurotransmitter, voltage_gated, STDP_* (6), ReceptorMorphology (shape ID) | `ModelRPCInterface.cpp:179-232` and `:234+`; `Simulation::AddLIFCReceptor` `Simulation.cpp:261-299` | Only way to set per-receptor NT parameters, but only at creation and only for hand-built models. Netmorph-built models never pass here. No delete. |
| `Simulation/Receptor/Create` (BS/SC neurons) | Conductance_nS, TimeConstantRise/Decay_ms, Neurotransmitter... | `ModelRPCInterface.cpp` ~`:100-177`; `Simulation::AddReceptor` `Simulation.cpp:233-259` | Different neuron classes (BS/SC) use a different receptor model; `BSNeuron::UpdatePrePostStrength` (`Sim/BallAndStick/BSNeuron.cpp:396-408`) zeroes all receptors from that pre neuron and sets the LAST one. |
| `Simulation/Staple/Create` | Source/DestinationCompartmentID | `ModelRPCInterface.cpp:75-95` | Pure compartment-to-compartment copy; irrelevant here. |
| `Simulation/SetSTDP` (`SetSTDP`, :235) | DoSTDP bool | `SimulationRPCInterface.cpp:527-545` sets `Simulation::STDP` | Global on/off only. STDP rule parameters live per receptor (STDP_A_pos etc., `Sim/Structs/Receptor.h:~105-110`) and cannot be edited after build. |
| Synapse creation/deletion | none | Synapses are created only by Netmorph build (`NES/Netmorph/NetmorphManagerThread.cpp:389-460`) or the Create routes above | No synapse/receptor deletion or post-hoc addition for Netmorph nets (other than zeroing weight). |
| `Simulation/SaveModel` / `LoadModel` (`ModelSave`, `ModelLoad`) | name | `Simulation.cpp:~660-1000` writes `LIFCReceptorBase` structs (`:675`, `:717-718`) | On 1.7.1 master, weights changed by SetPrePostStrength are stored in `LIFCReceptorData::weight`, not in `LIFCReceptor::Weight`, so edits are lost on save. Fixed on branch `fix/modelsave-edited-weights` (commits 1f2f2b3cf, b42e137cf; worktree `wt/nes-modelsave`), 3 commits after 1.7.1, not yet in a tag. |

### 1.2 Neuron / compartment parameters
| Route | What it does | Limitations |
|---|---|---|
| `Simulation/Neuron/LIFC/Create` (`AddLIFCNeuron`, :313) `ModelRPCInterface.cpp:584-681` | Takes ALL LIFC parameters incl. every AHP/ADP/fatigue/adaptive-threshold field (lines 599-651) | Not used for Netmorph nets; no range checks (only enum strings checked, `:653-673`). |
| `Simulation/Neuron/LIFC/Edit` (`EditLIFCNeuron`, PY :328) `ModelRPCInterface.cpp:683-720`, `LIFCNeuron::Edit` `LIFCNeuron.cpp:75-114`, flags struct `LIFCEdit` `Sim/Structs/Neuron.h:398-406` | Edits ONLY 7 fields: RestingPotential, ResetPotential, SpikeThreshold, MembraneResistance, MembraneCapacitance, RefractoryPeriod, SpikeDepolarization. Empty NeuronIDs = all neurons. | No AHP/ADP/fatigue/adaptive-threshold fields. Per-neuron ID range checked up front, but per-neuron result ignored (`:708-719`, comment "could add test for false return"). Side effect: always sets `Vm_mV = VRest_mV` (`LIFCNeuron.cpp:~108`) i.e. wipes membrane state. No range validation. |
| `Simulation/Neuron/SC/Edit` | SC neurons: MembranePotential, Resting, SpikeThreshold, DecayTime_ms (= AHP tau), AfterHyperpolarizationAmplitude_mV (`SCNeuron.cpp:49-55`) | SC/BS class only; irrelevant to LIFC. |
| `Simulation/SetSpecificAPTimes` (`SetSpecificAPTimes`, :358) `ModelRPCInterface.cpp:888-918` | Appends forced spike times to `TDirectStim_ms` (`BSNeuron.cpp:61-68`) | Append only; no clear/replace. Validation of neuron ID happens mid-loop: earlier pairs of a bad list stay applied. Used for cues. |
| `Simulation/SetSpontaneousActivity` `ModelRPCInterface.cpp:938-` | mean/stdev inter-spike interval for chosen neurons | Not a threshold/AHP parameter. |
| `Simulation/Compartments/LIFC/Create` `ModelRPCInterface.cpp:~540` | creates compartment with shape | LIFC compartment params (`Sim/Structs/LIFC.h:28-37`) include AfterHyperpolarizationAmplitude_mV but this is unused by `LIFCNeuron` dynamics (grep: only printed in `LIFC.cpp:17`) (inferred: dead field). |
| Netmorph build defaults | `LIFCNeuronPars` (`NetmorphManagerThread.cpp:590-650`), `LIFCReceptorPars` (`:328-377`) are local structs in `BuildLIFCFromNetmorphNetwork` (`:837-838`) | Hard-coded; none of the Netmorph routes (`Netmorph/SetModelfile`, `StartSimulation`, `GetStatus`, `GetFile`) pass them. |

### 1.3 Compartment / morphology queries
- `Simulation/GetSomaPositions` (`SimulationRPCInterface.cpp:1324-1336`): soma centres only.
- `Simulation/GetBoundingBox`, `GetGeoCenter`: whole-sim extents.
- NO route returns compartment IDs, neurite geometry, receptor compartment IDs, or receptor shape. The data exists server-side:
  `LIFCNeuronStruct::{Soma,Dendrite,Axon}CompartmentIDs` (`Neuron.h:~384-392`, kept in `LIFCNeuron::build_data`, `LIFCNeuron.h:50`),
  `Simulation::NeuronByCompartment` map (`Simulation.h:148`) and `FindNeuronByCompartment` (`Simulation.h:234`),
  `Simulation::LIFCCompartments[id].ShapeID` (`Simulation.h:~146`), each receptor's Source/DestinationCompartmentID and ShapeID
  (`Receptor.h:~92-96`), `Simulation::GetReceptorByIdx` (`Simulation.cpp:1259-1267`).
- VSDA/Visualizer routes render geometry but do not return IDs (not read in detail).

### 1.4 WHY NMDA is zeroed and GABA cannot be set (determined from code)
`LIFCNeuron::UpdatePrePostStrength` (`LIFCNeuron.cpp:543-560`):
```
for each LIFCReceptorData r on this (post) neuron with r->SrcNeuronID == PreSyn:
    if (!AMPA_found && r->Type()==AMPA) { r->weight = G / r->g_peak_sum_nS; AMPA_found = true; }
    else                                { r->weight = 0.0; }
return AMPA_found;
```
- The comment on the C++ side (`Simulation.cpp:1349-1357`) and client (PY :436-440) describe it as a "short-hand: all receptors between the pair are collected, for all but one the conductance is set to 0". It was written for BS neurons (one scalar per pair, `BSNeuron.cpp:396-408`) and was carried over to LIFC without an NT argument (inferred from history: commit 042e6e777 "Added connection strength updating functions and API", before LIFC existed).
- In abstracted mode (default) each (pre, post, NT) triple is one `LIFCReceptorData` (`Simulation.cpp:279-289`, `LIFCNeuron.cpp:~FindLIFCReceptorPairing`). So a pair with AMPA+NMDA has two entries: the AMPA one gets the value, the NMDA one is hit by the `else` branch -> weight 0. That is the NMDA zeroing.
- GABA: only `Type()==AMPA` can receive a value, so GABA is never settable. Worse, a GABA-only pair (interneuron -> neuron) goes through the loop, GABA weight is zeroed, and the call returns false (no AMPA). The failed call has already deleted the inhibition, and in a Batch it also aborts the rest of the list.
- "GABA fixed 0.2": every Netmorph receptor starts at `C.Weight = 0.2` regardless of NT (`NetmorphManagerThread.cpp:457`). AMPA/NMDA/GABA all start at 0.2; GABA keeps it because nothing can change it.
- Effective conductance of a pair-NT is `g_k = min(g_peak_sum_nS, weight * g_peak_sum_nS * kernel)` (NMDA additionally multiplied by Mg block `B_NMDA(Vm)`) (`Sim/Structs/Neuron.cpp:149-160`). Two consequences: requested Conductance above `g_peak_sum_nS` is silently saturated (no validation), and `weight` is clamped to [0,1] by STDP (`Neuron.cpp:~186-187`) so with STDP on, any weight > 1 is cut at the first pre/post event. Our scripts turn STDP off (`server_apply.py:96`).
- Non-abstracted mode: every receptor is its own `LIFCReceptorData`; the same function then keeps only the first AMPA receptor of the pair and zeroes all other receptors including other AMPA ones (inferred from the loop above).

## 2. AHP / ADP / fatigue / refractory in the simulator
All of it is in ONE class: `LIFCNeuron` (`Sim/LIFCompartmental/LIFCNeuron.h:44-135`, `.cpp`), a single-compartment (point) LIF
neuron; per-NEURON, not per-compartment. BS/SC neurons have only one exponential AHP (`BSNeuron.cpp:151-160`, `VAHP_mV`, `TauAHP_ms`).
Build-time values are copied from `LIFCNeuronStruct` (`LIFCNeuron.cpp:14-62`) and kept in `build_data`. Defaults below are the Netmorph
principal-cell values (`NetmorphManagerThread.cpp:590-650`); interneurons are identical except sAHP g_peak 0 and ADP g_peak 0 (`:~648-652`).

| Mechanism | Parameters (field in LIFCNeuron.h; units; Netmorph default; code comment range) | Where used |
|---|---|---|
| Refractory | `tau_absref_ms` (ms; 2) | `update_with_*` `LIFCNeuron.cpp:347-400`. Editable now via Edit. |
| fAHP | `tau_rise_fAHP_ms` 2.5 (1-5), `tau_decay_fAHP_ms` 30 (20-50), `g_peak_fAHP_nS` 3 (1-5), `g_peak_fAHP_max_nS` 5 (3-6), `Kd_fAHP_nS` 1.5 (1.5-3), shared `E_AHP_mV` -90 | `update_conductances` `:253-275`; current in `update_currents` `:279-` |
| sAHP | `tau_rise_sAHP_ms` 30 (20-50), `tau_decay_sAHP_ms` 300 (150-1000), `g_peak_sAHP_nS` 1 (0.5-3), `g_peak_sAHP_max_nS` 2 (0.5-2.5), `Kd_sAHP_nS` 0.3 (0.3-1) | same |
| AHP saturation model | enum CLIP (default) / SIGMOID (`build_data.AfterHyperpolarizationSaturationModel`) | `:264-271` |
| ADP | `E_ADP_mV` -20, `tau_rise_ADP_ms` 20, `tau_decay_ADP_ms` 200, `g_peak_ADP_nS` 0.3 (principal; 0 interneuron), `ADP_saturation_multiplier` 2 (2-3), `tau_recovery_ADP_ms` 300 (200-600), `ADP_depletion` 0.3 (0.2-0.4); model enum CLIP / RESOURCE | `:273-284`, `spike()` `:175-216` |
| Fatigue (hard cap) | `fatigue_threshold` 300 spikes (0 = off), `tau_fatigue_recovery_ms` 1000 | `spike()` +1; decay in `Update` `:477-481`; blocks spiking in `check_spiking` `:227-229` |
| Adaptive threshold (Na inactivation) | `dh_spike` 0.2, `tau_h_ms` 50 (50-200), `dVth_mV` 10 | `update_adaptive_threshold` `:335-345`, `spike()` |
| Dynamic threshold floor | `Vth_floor_mV` -50, `delta_floor_per_spike_mV` 1 (0 = off), `tau_floor_decay_ms` 500 | same. NOTE `Vth_floor_mV` is also run-time state (incremented per spike, `:~199`), so reading/setting the "parameter" is ambiguous; the original value is in `build_data.AdaptiveThresholdFloor_mV`. |
| Derived (computed once in ctor) | `tau_m_ms = Rm*Cm`, `g_L_nS`, `g_peak_ADP_max_nS = g_peak_ADP*multiplier`, `norm_fAHP/sAHP/ADP = compute_normalization(rise, decay)` (`:56-62`) | `compute_normalization` THROWS `std::invalid_argument` if rise == decay (`Sim/Structs/Receptor.cpp:9-12`). |
| Run state | `g_fAHP_nS, g_sAHP_nS, g_ADP_nS, a_ADP, h_spike, fatigue, Vth_floor_mV, t_last_spike` | not readable through any route (spike times via GetSpikeTimes, Vm via RecordAll/GetRecording). |

Conductance kernels are double exponentials of the neuron's own spike history, `g_norm` (`Receptor.cpp:19-37`); lookback is truncated per
kernel (see branch commit 54f0a65fb "cap the spike lookback per kernel at 12 time constants", worktree `wt/nes-lookback`, not in 1.7.1),
which matters if we program long taus.

API exposure today: create-time only (`LIFC/Create`, all fields) and Edit for the 7 basic fields. AHP/ADP/fatigue/adaptive-threshold of a Netmorph-grown
network are NOT reachable by any route (and Netmorph builds use compiled-in defaults). Nothing is readable (no Get).

What is needed to expose them (all in `LIFCNeuron`, local, low-risk):
1. Extend `LIFCEdit` (`Neuron.h:398`) with one bool per field (about 30), extend `LIFCNeuronEdit` RPC (`ModelRPCInterface.cpp:683`) to fill them.
2. `LIFCNeuron::Edit` must also update `build_data` for each field (so ModelSave round-trips, as it does for the first 7) and recompute derived values: `g_peak_ADP_max_nS`, `norm_fAHP/sAHP/ADP`, `tau_m_ms`, `g_L_nS`.
3. Validate before mutating (rise != decay, rise < decay, positivity, g_peak <= g_peak_max, Kd > 0, depletion in [0,1], multiplier >= 1, floor >= SpikeThreshold), for ALL listed neurons first, then apply (atomic).
4. Stop resetting `Vm_mV` in Edit unless explicitly asked (`ResetState` flag).
5. Add a read route for the parameters and, optionally, the state variables.

## 3. Spine / synapse geometry

What NES models today (1.7.1):
- Each Netmorph synapse becomes a `Geometries::Box` ("synbox") spanning the synapse segment's P0..P1 (axis-wise absolute differences as dims, centre = midpoint, no rotation) (`NetmorphManagerThread.cpp:396-409`) plus one `LIFCReceptor` per NT with Source/DestinationCompartmentID = axon/dendrite segment compartments (`:424-436`) and `ShapeID` = that box. The code itself says "needs better detailing ... with spines, terminals and receptors" (`:394-395`).
- Synapse location on a neurite: encoded implicitly (DestinationCompartmentID = the dendrite segment cylinder, box position). Not exposed by any route; not used by dynamics.
- Receptor count and size: no spine count, head area or neck. A per-synapse receptor "quantity" is a compiled constant (`ampa_raw` 49 x 0.02 nS, `nmda_raw` 11 x 0.05 nS, `gaba_raw` 10 x 0.08 nS, `:366-376`) turned into `PeakConductance_nS = quantity * unit` (`Simulation.cpp:302-308`). The TODO at `NetmorphManagerThread.cpp:~448-452` says: `ReceptorQuantity = int(AMPAChannelsProportion*Synapse_Area_um2/0.0086)`, plus hillock-distance tracing and weight; i.e. the intended structure-to-strength link is not implemented.
- Interactions between synapses on one neurite: not possible. `LIFCNeuron` sums ALL receptors of the neuron into a single membrane equation (`update_membrane_potential_exponential_Euler_Cm`, `LIFCNeuron.cpp:~315-333`). Neurite compartments exist only as geometry plus ID mapping (`NetmorphManagerThread.cpp:153-208`), they carry no state. In abstracted mode the per-receptor compartment identity is even discarded: receptors are merged per (pre neuron, post neuron, NT) (`Simulation.cpp:279-289`, `Neuron.cpp:74-81`), with PSP timing medians (`Neuron.cpp:84-147`).
- Netmorph side: vendored NetmorphCMake at 1189112 has a global switch `include_spines` (`ThirdParty/NetmorphCMake/Source/synapse_formation_model.hh:278`, parsed `synapse_formation_model.cc:51`) and distance rules for who can bridge 1.0 vs 0.1 um (`.hh:~246-262`), but no spine geometry output. Branch `origin/rkoene-20260422-spines` of NetmorphCMake adds `synapse_morphology {presyn_terminal_pos, postsyn_pos, requires_dendritic_spine}`; `requires_dendritic_spine = distance > 0.15 um` (`synapse_structure.cc:55-60`, `.hh:40,51-55`). NES branch `origin/rkoene-20260629-add-spines` (author Randal Koene) calls `get_morphology()` in `LIFCSynapseBuild` only inside a `SPINES_TEST` logging block and groups co-located receptors on one `synapse_structure` via `cache.i`; it stores nothing. Neither branch is in 1.7.1.

What exists vs what would need NES changes:
- Exists: synapse endpoints (box), compartment IDs, receptor quantity constants, Netmorph distance data.
- Trivial/small: expose per-receptor info (IDs, compartments, shape centre/dims, NT, g_peak, weight) read-only; per-receptor weight/quantity edit that recomputes the aggregate.
- Medium: NES stores per-synapse morphology (spine yes/no, head size proxy, neck length from P0-P1 distance), `ReceptorQuantity` rule from area, route to set it (changes `PeakConductance_nS` -> needs `LIFCReceptorData::g_peak_sum_nS` recomputation).
- Large (NES upgrade): same-neurite interactions. Options (inferred): (i) group receptors by DestinationCompartmentID and apply cluster nonlinearity/sublinear summation or shunting in `update_conductances`; (ii) true multi-compartment cable/passive-dendrite model using the existing cylinder geometry. Both require abandoning pair-level aggregation or keeping per-compartment sub-aggregates.

## 4. Proposed API spec

Conventions follow existing routes: POST via `Simulation/<Route>` JSON, `StatusCode` in response (0 = ok), `SimulationID` required, sim must not be busy.
New status code needed for per-entry errors: add `BGStatusInvalidParametersPassed` with an `Errors` array (existing code `API::BGStatusCode`). Adding routes changes `NES_API_VERSION` (see `RPC/StaticRoutes.cpp:10`, `SafeClient.cpp:56`); bump client+server together (cf. the 1.0.1 bump in worktree `wt/api-v101`).
Legend: [EXISTS] reachable today under some name; [TRIVIAL] <= ~1-2 days local C++/Python; [UPGRADE] needs real NES model work.

### 4(a) Per-neurotransmitter weights [route: TRIVIAL; reads: EXISTS]
READ [EXISTS]: `GetConnectome` already gives weight, type, g_peak_sum, num receptors per (pre, post, NT) (see 1.1). Optional convenience route
`Simulation/GetReceptorWeights` [TRIVIAL]: request `{SimulationID, PreSyn?:[int], PostSyn?:[int], Neurotransmitters?:["AMPA","NMDA","GABA"]}`, response
`{StatusCode, Entries:[{PreSyn, PostSyn, Neurotransmitter, Weight, Conductance_nS (= Weight*GPeakSum_nS), GPeakSum_nS, NumReceptors}]}` (filtered, sparse, synchronous).

WRITE new route `Simulation/SetReceptorWeights` [TRIVIAL; replaces misuse of SetPrePostStrength]:
```
Request:  {"SimulationID": 7,
           "Mode": "Conductance_nS" | "Weight",          // default Conductance_nS
           "Entries": [{"PreSyn": 3, "PostSyn": 12, "Neurotransmitter": "AMPA", "Value": 0.45},
                       {"PreSyn": 3, "PostSyn": 12, "Neurotransmitter": "NMDA", "Value": 0.10},
                       {"PreSyn": 9, "PostSyn": 12, "Neurotransmitter": "GABA", "Value": 0.30}],
           "DryRun": false}                               // true = validate only
Response ok:   {"StatusCode": 0, "Applied": 3, "Entries": [{"Index":0,"Weight":0.4592,"Conductance_nS":0.45}, ...]}
Response fail: {"StatusCode": <InvalidParametersPassed>, "Applied": 0,
                "Errors": [{"Index": 2, "Code": "NO_SUCH_RECEPTOR", "Message": "..."}]}
```
Semantics: two-phase. Phase 1 resolves every entry to its `LIFCReceptorData*` (match SrcNeuronID, Neurotransmitter via `Type()`) and validates; if ANY error, nothing is modified (all errors reported, with index). Phase 2 assigns weights (cannot fail; plain float writes, optionally under the sim's busy flag). Entries touch ONLY the named (pre, post, NT); other receptors are left alone.
Validation (hard): sim class is LIFC (else error `NOT_LIFC`); IDs in [0,N); NT in {AMPA,NMDA,GABA}; (pre,post,NT) triple exists (else `NO_SUCH_RECEPTOR`; never silently create); duplicates of the same triple in one request rejected (`DUPLICATE`); value finite; Mode Weight: 0 <= w <= 1 (STDP clamp range, `Neuron.cpp:~186`); Mode Conductance_nS: 0 <= G <= GPeakSum_nS of that triple (above it the sim saturates at `g_peak_sum_nS`, `Neuron.cpp:149-160`, so we reject rather than silently clip). Sign: all three NTs take non-negative magnitudes; the sign comes from the reversal potential (GABA -70 mV, `NetmorphManagerThread.cpp:362`).
Bio range guidance (inferred, to be checked with Randal): unitary AMPA 0.05-0.5 nS/synapse (Netmorph per-synapse default 49*0.02 = 0.98 nS aggregated peak); NMDA about 0.2-1x AMPA, GABA about 0.5-2x AMPA; reject only physical impossibilities, put plausible ranges in a `Warnings` array.
Client: `Simulation.SetReceptorWeights(self, Entries:list, Mode:str='Conductance_nS', DryRun:bool=False) -> dict` and helper `SetReceptorWeightsArrays(self, Pre:list, Post:list, NT:list, Value:list, Mode=..., DryRun=False)`; `GetReceptorWeights(self, PreSyn=None, PostSyn=None, Neurotransmitters=None) -> dict`. Keep chunking (our server_apply chunks calls) but atomicity is then per request.
Also fix, as part of the same change (trivial): make legacy `UpdatePrePostStrength` not zero other receptors when new optional arg `PreserveOthers=true` is passed (default false for back-compat), and make `UpdateBatchPrePostStrength` validate first.
Effort: SMALL (about 1-2 days incl. tests). Files: `Sim/RPC/SimulationRPCInterface.{h,cpp}` (route+handler, near `:595-653`), `Sim/Structs/Simulation.{h,cpp}` (new `SetReceptorWeights`, near `:1358`), `Sim/LIFCompartmental/LIFCNeuron.{h,cpp}` (lookup helper by (src,NT)), `PY/Simulation/Simulation.py`, tests next to `Simulation.test.cpp`.
STDP companion `Simulation/SetSTDPParameters` [SMALL]: per NT `{Method, A_pos, A_neg, Tau_pos, Tau_neg, Shift}` applied to all or to listed (pre,post,NT); must write both `LIFCReceptor` entries and the abstracted `LIFCReceptorData` copies (`Neuron.cpp:~117-147` computes medians once at first update, so edits must precede the first `Update` or recompute). Files: same plus `Neuron.cpp`.

### 4(b) AHP/ADP/fatigue/adaptive-threshold per neuron [EXISTS only at create time; route extension SMALL-MEDIUM]
Extend `Simulation/Neuron/LIFC/Edit` rather than invent a new route (keeps client method `EditLIFCNeuron`); add read route `Simulation/Neuron/LIFC/Get`.
```
Edit request: {"SimulationID": 7, "NeuronIDs": [4,5,9] | [] (= all), "ResetState": false, "DryRun": false,
               "FastAfterHyperpolarizationRise_ms": 2.0, "FastAfterHyperpolarizationDecay_ms": 35.0,
               "SlowAfterHyperpolarizationDecay_ms": 400.0, "AfterDepolarizationPeakConductance_nS": 0.4, ... any subset}
Edit response ok:   {"StatusCode":0,"Edited":3}
Edit response fail: {"StatusCode":<Invalid>, "Errors":[{"NeuronID":5,"Field":"AfterDepolarizationRise_ms","Code":"OUT_OF_RANGE","Min":1,"Max":100}]}
Get request:  {"SimulationID":7,"NeuronIDs":[4,5],"Fields":["AHP","ADP","Fatigue","AdaptiveThreshold","Basic"] (optional)}
Get response: {"StatusCode":0,"Neurons":[{"NeuronID":4,"Type":"GenericPrincipalNeuron",  "<all LIFCNeuronBase fields from build_data>": ...}]}
```
Fields = every `LIFCNeuronBase` member (`Neuron.h:~326-362`); enums as strings (same strings as Create, `ModelRPCInterface.cpp:~540-583`).
Validation: all neurons x all fields checked before any change (atomic); neuron must be LIFC. Hard limits (reject) and soft "bio" ranges (Warnings array, or reject with `Strict:true`). Soft ranges below come first from the code comments in `LIFCNeuron.h:55-87` (authors' intended pyramidal ranges); items marked (lit.) are my reading of the literature and need confirmation:

| Field | Hard | Soft bio range |
|---|---|---|
| tau_rise/decay fAHP ms | rise>0, decay>rise, differ by >1e-3 (compute_normalization throws if equal) | rise 1-5, decay 20-50 |
| g_peak fAHP nS / max | 0 <= g_peak <= g_peak_max <= 50 | 1-5 / 3-6 |
| Kd fAHP | > 0 | 1.5-3 |
| tau_rise/decay sAHP ms | same rules | rise 20-50, decay 150-1000 |
| g_peak sAHP / max | same | 0.5-3 / 0.5-2.5 |
| Kd sAHP | > 0 | 0.3-1 |
| E_AHP mV | -120..-60 | -95..-80 (lit.) |
| ADP rise/decay ms | same rules | defaults 20 / 200; no comment range; (lit.) decay 50-500 |
| g_peak_ADP nS (0 = off) | 0..10 | 0-0.5 ("0.3 pyramidal") |
| ADP_saturation_multiplier | >= 1 | 2-3 |
| tau_recovery_ADP ms, ADP_depletion | >0; depletion in [0,1] | 200-600; 0.2-0.4 |
| E_ADP mV | -60..+10 | -20 (default) |
| FatigueThreshold (0 = off), FatigueRecoveryTime_ms | >= 0; >0 | model-specific (default 300 spikes/1000 ms) |
| AdaptiveThreshold: dh_spike (0..1), tau_h ms (>0), dVth mV (>=0), floor mV (>= SpikeThreshold), floor delta/spike (>=0), floor recovery ms (>0) | as given | tau_h 50-200 |
| RefractoryPeriod_ms | 0 < x <= 50 | 1-5 (lit.) |
Apply step must (i) write field and `build_data`, (ii) recompute `g_peak_ADP_max_nS`, `norm_fAHP/sAHP/ADP`, `tau_m_ms`, `g_L_nS`, (iii) leave Vm/run state alone unless `ResetState` (current `Edit` always resets Vm, `LIFCNeuron.cpp:~108`).
Not editable at runtime while busy (default handler rule); ModelSave then carries them because `build_data` is saved (`Simulation.cpp:~679`, flat header `Neuron.h:365-382`).
Client: `Simulation.EditLIFCNeuron(NeuronIDs, EditPars)` (exists, `PY :328`; just accepts the new keys, add `DryRun`), new `Simulation.GetLIFCNeuronParameters(NeuronIDs=None, Fields=None) -> dict`, helper `Simulation.EditLIFCNeuronTimingBatch(Params:dict[int, dict])` that sends one request per distinct parameter set. A per-neuron-different-values call (e.g. different tau for each of N neurons) should be a separate route `Simulation/Neuron/LIFC/BatchEdit` with `Edits:[{NeuronID, <fields...>}]` [SMALL], validated atomically, because experiments will program per-neuron values.
Effort: SMALL-MEDIUM (about 3-4 days with tests; mostly boilerplate and validation). Files: `Sim/Structs/Neuron.h` (`LIFCEdit` + struct), `Sim/LIFCompartmental/LIFCNeuron.{h,cpp}` (`Edit`, getters), `Sim/RPC/ModelRPCInterface.{h,cpp}` (Edit/Get/BatchEdit; Create's string-to-enum helpers at `:~540-583` reusable), `PY/Simulation/Simulation.py`, `PY/Models/Neurons/LIFC.py`, tests.
Related need: Netmorph-grown networks always start from the compiled defaults. A `Netmorph/SetLIFCDefaults` route [SMALL-MEDIUM] that fills `LIFCNeuronPars` and `LIFCReceptorPars` before `StartSimulation` (stored in `NetmorphParameters`, `NES/Netmorph/NetmorphParameters.h`) would let per-type defaults (principal vs interneuron) be set at build; per-neuron values still need the Edit route.

### 4(c) Compartment ID query [data EXISTS; route TRIVIAL]
Route `Simulation/GetCompartments` (synchronous for moderate N; use the managed-task pattern of `GetConnectome` `SimulationRPCInterface.cpp:1353-1373` if the net is large):
```
Request:  {"SimulationID":7,"NeuronIDs":[4,5] | [] (=all),"IncludeGeometry":false}
Response: {"StatusCode":0,"Neurons":[{"NeuronID":4,"Soma":[11],"Dendrites":[12,13,...],"Axon":[40,41,...],
            "Compartments":[{"ID":12,"Kind":"Dendrite","ShapeID":88,"ShapeType":"Cylinder",
                             "End0":[x,y,z],"End1":[x,y,z],"End0Radius_um":..,"End1Radius_um":..}]}]}   // Compartments only if IncludeGeometry
Inverse:  "Simulation/GetNeuronByCompartment": {"CompartmentIDs":[..]} -> {"NeuronIDs":[..]}  (uses Simulation::NeuronByCompartment)
Errors:   bad neuron ID -> InvalidParametersPassed (whole call rejected); non-LIFC/BS/SC sim -> NOT_SUPPORTED.
```
Data source: `LIFCNeuron::build_data.{Soma,Dendrite,Axon}CompartmentIDs`, `Simulation::LIFCCompartments[i].ShapeID`, `Collection` shapes (as used by `LIFCNeuron::GetSomaBoundingBox`, `LIFCNeuron.cpp:~130-160`). Python: `Simulation.GetCompartments(NeuronIDs=None, IncludeGeometry=False)`, `Simulation.GetNeuronByCompartment(CompartmentIDs)`.
Companion `Simulation/GetReceptors` [TRIVIAL-SMALL], needed for (d): request `{ReceptorIDs?|PreSyn?|PostSyn?, Neurotransmitters?}`, response per receptor `{ReceptorID, Neurotransmitter, SourceCompartmentID, DestinationCompartmentID, ShapeID, ShapeCenter_um, ShapeDims_um, PeakConductance_nS, Weight, OnsetDelay_ms, PreNeuronID, PostNeuronID}` using `LIFCReceptors` (`Simulation.h:~157`, `GetReceptorByIdx` `Simulation.cpp:1259`).
Effort: SMALL (1-2 days). Files: `Sim/RPC/SimulationRPCInterface.{h,cpp}`, `Sim/Structs/Simulation.{h,cpp}`, `PY/Simulation/Simulation.py`.

### 4(d) Synapse/spine strength linked to spine count/size
Three levels, increasing cost:

D1 [TRIVIAL-SMALL, available from NES-only work]: per-receptor (per-synapse) weight/quantity set/get.
`Simulation/SetReceptorStrength`: `{"SimulationID","Entries":[{"ReceptorID":1234,"Weight":0.3} | {"ReceptorID":1234,"ReceptorQuantity":37}], "DryRun"}`. Atomic two-phase like (a).
Implementation: write `LIFCReceptor::Weight` / `PeakConductance_nS` (= quantity * unit conductance) then recompute the owning `LIFCReceptorData` aggregate: `g_peak_sum_nS` and `weight = sum(w_i*g_i)/sum(g_i)` (same formulas as `Neuron.cpp:74-81`; needs a new `RecomputeAggregate()` and a receptor-to-RData lookup, map by (dst neuron, src neuron, NT) via `FindLIFCReceptorPairing`). Caveat: in abstracted mode the dynamics only see the aggregate, so per-receptor values matter only through the sums; this is exactly the right place to implement "strength = number of receptors" (sum of `PeakConductance_nS`). Validation: receptor exists, quantity in [0, 500] (spine head AMPA counts are typically tens to ~200; lit.), weight in [0,1].
Effort: SMALL-MEDIUM (2-4 days). Files: `Sim/Structs/Neuron.{h,cpp}` (`LIFCReceptorData`), `Sim/Structs/Simulation.{h,cpp}`, `Sim/RPC/SimulationRPCInterface.cpp`, ModelSave (`Simulation.cpp` saver already stores `LIFCReceptorBase` incl. Weight/PeakConductance; relies on the modelsave fix branch).

D2 [MEDIUM; NES + Netmorph integration]: synapse morphology object.
Land the work already in flight: Netmorph `rkoene-20260422-spines` (`synapse_morphology`) and NES `rkoene-20260629-add-spines`. Persist per synapse `{SpineHeadArea_um2 (proxy), NeckLength_um (= |P0-P1|), RequiresSpine}` in a new struct next to the box (store on `LIFCReceptorBase`, which would change the ModelSave binary layout (`Simulation.cpp:717`) -> versioned format), implement the TODO rule `ReceptorQuantity = int(AMPAChannelsProportion * Area_um2 / 0.0086)` (`NetmorphManagerThread.cpp:~448`), and routes `Simulation/GetSynapses` (list per synapse: pre/post compartment, NT receptors, morphology, quantity) and `Simulation/SetSynapseMorphology` `{SynapseID, SpineHeadArea_um2, NeckLength_um}` that recomputes quantity -> `PeakConductance_nS` -> aggregate (D1 path). Validation: head area 0.01-1.0 um^2 (lit.), neck length 0-3 um (lit.), area 0 only for non-spine synapses.
Effort: MEDIUM-LARGE (1-2 weeks; needs Randal's decision on the area-to-conductance rule and a save-format change). Files: `NES/Netmorph/NetmorphManagerThread.cpp`, `Sim/Structs/Receptor.h`, `Simulation.cpp` (save/load), `ModelRPCInterface.cpp`, ThirdParty NetmorphCMake submodule pointer.

D3 [UPGRADE, LARGE]: same-neurite synapse interactions (shunting, saturation, NMDA cluster supralinearity, spine neck attenuation).
Needs per-dendritic-compartment aggregation in `LIFCNeuron::update_conductances` / `update_membrane_potential_*` instead of one pooled sum; at minimum (i) key `LIFCReceptorData` also by DestinationCompartmentID, (ii) per-compartment effective-conductance nonlinearity, or (iii) real multi-compartment cable using the existing cylinder compartments. This changes the model class and runtime cost; propose as a separate project. Route surface afterwards: `GetCompartmentState`, per-compartment passive parameters (Ra, Cm, Rm) via a `Compartments/LIFC/Edit` route (does not exist; `Compartments/LIFC/Create` only). Files: `LIFCNeuron.{h,cpp}`, `Neuron.{h,cpp}`, `Simulation.cpp`, geometry helpers.

### 4(e) Other gaps found while reading
1. Silent side effects and partial application in existing routes (1.1, 1.4): SetPrePostStrength zeroes then fails; Batch non-atomic; SetSpecificAPTimes non-atomic; LIFC/Edit ignores per-neuron failure and resets Vm. [TRIVIAL fixes, include in (a)/(b)]
2. Conductance saturates silently at `g_peak_sum_nS` (`Neuron.cpp:149-160`). Programming a larger value looks successful and is clipped. Solve through validation in (a). Related: maximum programmable strength per pair/NT is therefore set by Netmorph synapse counts, not by us; a route to scale `g_peak_sum` (or receptor quantity, D1) is needed to program beyond it. [TRIVIAL once D1 exists]
3. No per-NT receptor kinetics edit (PSP rise/decay, reversal potential, onset delay, voltage_gated) after build; only at `LIFCReceptor/Create`. NMDA decay and GABA reversal are natural programmable parameters. `Simulation/SetReceptorKinetics` [SMALL-MEDIUM]: must recompute `norm` and re-run the median step (`Neuron.cpp:84-147`; norm computed in ctor `:52-54` when non-abstracted, once at first Update when abstracted, `LIFCNeuron.cpp:473`). Same rise != decay constraint.
4. No state readback (fatigue, adaptive-threshold h, a_ADP, current AHP/ADP conductances) and no way to clear/replace cue spikes. Add `Simulation/Neuron/LIFC/GetState` and `SetSpecificAPTimes` with `Replace:true`/`ClearSpecificAPTimes` [TRIVIAL]. (`BSNeuron.cpp:61-68`, `TDirectStim_ms` has no clear; sorted at first update.)
5. ModelSave drops edited weights on master (fix exists on `fix/modelsave-edited-weights`); neuron edits only persist if `build_data` is updated (see 4b). Recommend landing the branch and adding a save/load round-trip test for every new route.
6. Reset semantics for weights/neuron params: not determined from the code I read (`SIMULATION_RESET` handling not located). Needs a test before we rely on Reset between trials.
7. Netmorph defaults fixed in code (1.2). `Netmorph/SetLIFCDefaults` (4b) or ability to edit per type.
8. Python client issues seen: `OptoModifyInjection`/`OptoActivation` omit SimulationID (client comments, PY :370-400); `SetAllStrength` loop O(N^2) server side.
9. Compiled `STDP` weight clamp [0,1] coupled with conductance saturation: with STDP on, programmed weights drift; fine for us (STDP off) but document.
10. Netmorph receptors of the same synapse structure share compartments; branch `rkoene-20260629-add-spines` adds `cache.i` sharing so one box per synapse instead of one per receptor (not in 1.7.1). Our "synapse count" numbers depend on whether that is merged.

## 5. Summary table
| Need | Status | Effort | Main files |
|---|---|---|---|
| Per-NT weight read | EXISTS (`GetConnectome`) | none (filter route SMALL) | n/a |
| Per-NT weight set, atomic | missing (route) | SMALL | SimulationRPCInterface.cpp, Simulation.cpp, LIFCNeuron.cpp |
| GABA weights | missing, solved by the above | SMALL | same |
| AHP/ADP/fatigue/adaptive-threshold edit | create-time only; Edit lacks fields | SMALL-MEDIUM | Neuron.h, LIFCNeuron.cpp, ModelRPCInterface.cpp |
| Parameter read (Get) | missing | SMALL | same |
| Compartment ID query | data exists, no route | SMALL | SimulationRPCInterface.cpp, Simulation.cpp |
| Per-receptor strength/quantity | missing | SMALL-MEDIUM | Neuron.cpp, Simulation.cpp |
| Spine/synapse morphology to strength | partial in flight (branches) | MEDIUM-LARGE | NetmorphManagerThread.cpp, Receptor.h, save format |
| Same-neurite synapse interactions | not modelled | LARGE (NES upgrade) | LIFCNeuron.cpp, Neuron.cpp |
| Receptor kinetics edit, STDP params, Netmorph defaults | missing | SMALL-MEDIUM each | see 4(e) |

## 6. Prioritised list
1. (a) `SetReceptorWeights` + fix partial-failure behaviour. Unblocks per-NT programming and GABA now, trivial, high value. Also land `fix/modelsave-edited-weights`.
2. (b) Extend `LIFC/Edit` + `LIFC/Get` (+ `BatchEdit`) with AHP/ADP/fatigue/adaptive threshold, atomic and validated. Unblocks Randal's AHP/ADP timing extension, all code lives in `LIFCNeuron`.
3. (c) `GetCompartments`/`GetReceptors`: small, and a prerequisite for any morphology claim.
4. D1 per-receptor strength/quantity and the saturation fix; gives "strength = number of receptors" without morphology changes.
5. 4(e).3 receptor kinetics and STDP parameters.
6. D2 spine morphology (needs Randal's rule and format change; builds on his two in-flight branches).
7. D3 same-neurite interactions (separate research/engineering project; Randal already flagged it needs NES upgrade).
A demonstrable "morphology matters" experiment that needs only items 1-4: make strengths proportional to Netmorph synapse receptor counts/box size and show a rewiring-by-spine-count effect that connectivity-and-count cannot reproduce; the same-neurite part needs D3.

## 7. Draft message to the NES owners (not sent)
Subject: NES API requests for weight-space programming on Netmorph-grown LIFC networks

Hi all,
we program weights and neuron parameters on Netmorph-grown LIFC networks through the NES API and hit these limits (details and code references in NES_API_GAPS_AND_SPEC.md):
1. `SetPrePostStrength`/`BatchSetPrePostStrength` write one scalar per pre/post pair: `LIFCNeuron::UpdatePrePostStrength` (LIFCNeuron.cpp:543-560) sets the first AMPA entry and zeroes every other receptor from that pre neuron, so NMDA is zeroed and GABA can never be set; a GABA-only pair is zeroed and the call returns false; batches are not atomic. Could we add `Simulation/SetReceptorWeights` with (pre, post, NT, value) entries, validate-then-apply, per-entry error indexes, reject values above `g_peak_sum_nS`?
2. `Simulation/Neuron/LIFC/Edit` only edits 7 fields; AHP/ADP/fatigue/adaptive-threshold parameters exist in `LIFCNeuron` but cannot be edited or read for Netmorph-built nets. Could `LIFCEdit` be extended (recomputing norm_* and g_peak_ADP_max, updating build_data, no Vm reset) plus a Get route?
3. A compartment-ID/receptor query (data is in `build_data`, `NeuronByCompartment`, `LIFCReceptors`).
4. Per-receptor strength/quantity, and spine morphology for synapse strength: is the `rkoene-20260629-add-spines` / NetmorphCMake `rkoene-20260422-spines` work heading toward the receptor-quantity-from-area rule (NetmorphManagerThread.cpp TODO)? Same-neurite synapse interaction would need per-compartment integration in LIFCNeuron; is that on the roadmap?
5. Please merge `fix/modelsave-edited-weights` so edited weights survive ModelSave.
Which of these would you accept as MRs from us, and what API versioning/test conventions should we follow?
Thanks.
