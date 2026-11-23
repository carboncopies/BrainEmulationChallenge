# Per-receptor GABA/NMDA/AMPA strength in NES: patch, tests, usage (2026-11-23)

Implements section 3 of `FINDINGS.md`. Built and tested in the SEPARATE build only (NES 8011 / API 8010). Main NES 3156209 / API 1972355 were not touched. Local commits only: no push, no merge request, no emails. Randal can review the branches below.

## What it does
`Simulation/SetPrePostStrength`, `Simulation/BatchSetPrePostStrength` and `Simulation/SetAllStrength` accept an optional `Neurotransmitter`: `"AMPA" | "GABA" | "NMDA"` (Batch: one string for all entries, or a list with one entry per pair; `null` or `""` for an entry means legacy for that entry).
- **Given:** only the receptor group of that type between the pair is set: `weight = Conductance_nS / (summed peak conductance of that group)`. Groups of the other types, other pairs, other presynaptic cells are not touched. Works on GABA-only pairs (Int -> X) and for NMDA.
- **Absent:** exactly the old behaviour (first AMPA group set; every other group from that presynaptic cell onto that postsynaptic cell zeroed; `false` for a pair without AMPA, but the zeroing has already happened).
- **Failure with the argument changes nothing:** no group of that type for the pair, conductance negative or NaN, post-neuron ID out of range, unknown type string (`StatusCode` 2 = InvalidParametersPassed). BallAndStick/SC neurons reject the argument. No upper bound is enforced (as before): a weight above 1 is accepted, the simulator caps the conductance at the group's `g_peak_sum` (`Neuron.cpp:149-155`).
- Batch stays non-atomic, as before: it stops at the first failing entry and earlier entries stay applied.

## Branches (local, not pushed)
| repo | path | branch | commit | base |
|---|---|---|---|---|
| NES | `/home/johnjose/BrainGenix/wt/nes-receptor-strength-repo` (local clone of `BrainGenix-NES`, remote removed) | `nes-receptor-strength` | 0ce673cf3 | master dee7ee406 |
| Python client | `/home/johnjose/BrainGenix/wt/pythonclient-receptor-strength` (local clone of `BrainEmulationChallenge/PythonClient`, remote removed) | `nes-receptor-strength` | f25a201 | 5b723ce |

Why clones: `wt/nes-linefix` is a plain copy of the source (no `.git`), so a branch could not be created there; the main checkout was not to be touched. The patched sources were copied into `wt/nes-linefix` (7 files identical to the commit, `cmp` checked; `CMakeLists.txt` deliberately not copied) and built there, so the running instance has the patch AND the line-379 fix. NetMorph was not changed. The commit applies to upstream master with `git am`.
Diffs: `nes-receptor-strength.diff` (462 lines, `git format-patch`), `pythonclient-receptor-strength.diff`.

## Files changed (NES, +296 / -14)
| file | change |
|---|---|
| `Simulator/LIFCompartmental/LIFCNeuron.h/.cpp` | `UpdatePrePostStrength(pre, G, int NT = -1)`: with NT >= 0 sum `g_peak_sum_nS` of the groups (source = pre, type = NT) and set `weight = G / sum` on them (in abstracted mode there is exactly one group per (pre, post, type); otherwise all groups of that type get the same weight, i.e. the conductance is shared in proportion to peak). Returns false without side effects if none exists. Legacy loop untouched below it. |
| `Simulator/Structs/Simulation.h/.cpp` | `UpdatePrePostStrength(pre, post, G, NT = -1)`, `UpdateAllStrength(G, NT = -1)`, `UpdateBatchPrePostStrength(..., const std::vector<int>& NTs = {})` (empty = legacy; else one per entry, size checked); NT >= 0 on non-LIFC simulations returns false. |
| `Simulator/RPC/SimulationRPCInterface.cpp` | helper `ParseOptionalNT` (anonymous namespace) reads the optional JSON field; the three handlers pass NT through. Unknown string or wrong list length returns InvalidParametersPassed. |
| `Simulator/Structs/SimulationReceptorStrength.test.cpp` (new) + one line in `Source/Core/CMakeLists.txt` | 9 gtest cases, see Tests. |
| Python `BrainGenix/NES/Simulation/Simulation.py` | `SetPrePostStrength(..., Neurotransmitter=None)`, `SetAllStrength(..., Neurotransmitter=None)`, `BatchSetPrePostStrength(..., Neurotransmitter=None)` (string or list; key sent only when not `None`). |

## Tests
1. **Unit test (9 cases), PASS 9/9** (`unit_test.log`; run `./build_unit_test.sh`). Three LIFC neurons, groups AMPA (2 receptors x 0.98 nS), NMDA, GABA on 0->1 and GABA-only on 2->1: baseline; GABA alone / NMDA alone / AMPA alone leave the other types and pairs unchanged; legacy call unchanged (AMPA set, NMDA and GABA zero, other presynaptic cell untouched; legacy on a GABA-only pair returns false and zeroes GABA); GABA on a GABA-only pair; missing type, negative, invalid type, invalid post fail without side effects; Batch with a list of types, with a length mismatch, and without the argument; SetAllStrength per type and legacy. **Caveat:** the CMake unit-test target is commented out in this tree and the existing `Simulation.test.cpp` does not compile against the current API (`NeuralCircuits` is a vector now, etc.), so the new tests are a separate file and are built by `build_unit_test.sh` (same flags and link line as the NES binary, own `main`, gtest from the vcpkg tree). I added the file to `UNITTEST_SOURCES` for when the target is revived.
2. **Connectome test through the API, PASS 29/29** (`verify_api.py`, `verify_api.json`, `verify_api.log`). E4 model `V1n20_s33333` loaded on the patched instance, no simulation run. After every call the whole connectome (6,878 groups) was read back and compared with the previous state: GABA alone on an Int->Pyr pair (96->0, 1.2 nS): only that group changed. NMDA alone on Pyr->Pyr 0->4 (0.35 nS): only that group changed. AMPA alone with the argument (4.5 nS): NMDA still 0.35. Legacy call without the argument (3.0 nS): AMPA 3.0, NMDA zeroed, as before. Batch with one string (3 GABA pairs, 0.9 nS) and with a list (AMPA 2.5 + NMDA 0.4 on one pair): exactly those groups. Batch without the argument: legacy. Errors: unknown type `"GLUTAMATE"`, `"AMPA"` on a GABA-only pair (GABA stays 1.2 nS; the legacy call on the same pair zeroes it, which is also checked), negative conductance: status 2 and nothing changed. `SetAllStrength(0.5, 'GABA')`: all 1,174 GABA groups 0.5 nS, every AMPA/NMDA group unchanged; `SetAllStrength(0.0)` legacy: every NMDA and GABA weight 0.
3. **Old calls reproduce a stored run exactly (spikes):** `gaba_vm/run_vm.py V0p 1.5 1 none api` (the V0 recipe: client without the new argument, `BatchSetPrePostStrength` only) on the patched build against the stored V0 run (`raw_V0_api_x1_c1.5.json`, made before the patch): same model, same connectome readback, **512 / 512 spikes, max absolute spike-time difference 0 ms** (outputs `gaba_vm/raw_V0p.json`, `log_V0p.txt`, `vm_V0p.npz`).
4. **New route equals the file route for NMDA-on recall:** `run_nt_nmda.py` programs the same c = 1.5 recipe through the API with the new argument (AMPA by the old batch call, then NMDA = 0.56 x AMPA target by `BatchSetPrePostStrength(..., Neurotransmitter='NMDA')`, GABA left at the grown weight 0.2) and compares with the stored file-route run `gaba_vm/raw_K_nmda056_x1.json` (same programming written into a model-file copy): 3,299 pairs, NMDA set on 2,405 (pairs that have an NMDA group; 109 above the group's peak, capped by the simulator as in the file route), AMPA and NMDA readback mismatches 0, GABA weights unchanged (0.2); **628 / 628 spikes, same spiking cells, max spike-time difference 0.00012 ms** (`raw_nt_nmda056_x1.json`, `compare_nt_vs_file.json`, `run_nt_nmda.log`). So NMDA-on recall no longer needs the model-file hack. One simulation at a time; both deleted afterwards.

## How to use (patched client on `PYTHONPATH` first: `/home/johnjose/BrainGenix/wt/pythonclient-receptor-strength`; server 8010)
```python
sim.SetPrePostStrength(96, 0, 0.64, Neurotransmitter='GABA')            # one GABA pair to 0.64 nS (other groups untouched)
sim.SetPrePostStrength(3, 7, 0.40, Neurotransmitter='NMDA')             # NMDA of a Pyr->Pyr pair to 0.40 nS, AMPA kept
sim.BatchSetPrePostStrength(pre, post, g_ampa)                           # old call (AMPA; zeroes that pair's NMDA and GABA)
sim.BatchSetPrePostStrength(pre, post, [0.56*g for g in g_ampa], Neurotransmitter='NMDA')   # then NMDA as a ratio of AMPA
sim.BatchSetPrePostStrength([3,3], [7,7], [2.5, 0.4], Neurotransmitter=['AMPA','NMDA'])     # one list entry per pair
sim.SetAllStrength(0.5, Neurotransmitter='GABA')                         # every GABA group to 0.5 nS, AMPA/NMDA unchanged
sim.SetAllStrength(0.0)                                                  # legacy: AMPA = 0, EVERY NMDA and GABA zeroed
```
Raw JSON: `{"Simulation/SetPrePostStrength": {"SimulationID": 0, "PreSyn": 96, "PostSyn": 0, "Conductance_nS": 0.64, "Neurotransmitter": "GABA"}}`.
Order matters: the old (no-argument) call zeroes NMDA and GABA of the pairs it touches, so program AMPA first and the other types after. Conductance of a type = weight x (grown number of synapses x per-synapse peak): GABA per grown synapse 0.8 nS, NMDA 0.55 nS, AMPA 0.98 nS, so a pair with n GABA synapses cannot exceed n x 0.8 nS before the cap (`Neuron.cpp:152`). Readback: `GetConnectome` (types 1 AMPA, 2 GABA, 3 NMDA).

## Limits and not done
- Per-pair granularity only (as before); kinetics, peak conductance, recording of conductances by type are not exposed (items 3 to 6 of `gaba_vm/API_NEEDS.md`).
- Weights set through the API are still not written by `SaveModel` on this base (the `fix/modelsave-edited-weights` branch is separate and not merged here).
- Not compiled into CI: the project's unit-test target is disabled; the separate test file builds standalone.
- Not tested: non-abstracted mode (`SetLIFCAbstractedFunctional(False)`; the code shares the conductance over same-type groups, unit-tested only for the abstracted case), BallAndStick/SC rejection (by reading), `null`/`""` list entries.
- Instance: NES pid 803572 on 8011, API pid 804251 on 8010 (8009 internal); logs `wt/linefix-instance/nes.log`, `api.log`. Binary `wt/nes-linefix/Binaries/BrainGenix-NES` built 2026-11-23 07:28 (rc 0, incremental `make -j32`).
