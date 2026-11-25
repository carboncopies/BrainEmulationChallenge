# neuron_reset_ahp: offline plan (2026-11-24, written before PREREGISTRATION.md and before any simulation)

John approved ideas 1 and 2 of `../idea_scout3/IDEAS.md`. Randal agreed that literature neuron parameters may be used if they are documented with references.

**The two ideas:**
1. Reset pyramidal cells to a fixed -55 mV instead of the pre-spike Vm.
2. A stronger and slower slow AHP: peak x2-3 with the cap raised, and decay 1-1.5 s.

## What is changed and how (read from the NES source and the E4 model file)
**Reset.**
- In the model file now: `ResetMethod` = TOVM (0). After the 2 ms refractory period, Vm is set to min(pre-spike Vm, -50 mV). In practice this is just under the -50 mV threshold (`LIFCNeuron.cpp:185-187, 383-387`).
- `Vreset` = -55 mV is already in the file, but TOVM ignores it.
- The arm sets `ResetMethod` = AFTER (2): Vm = -55 mV + dV once the refractory period ends.

**Slow AHP.**
- In the model file now: rise 30 ms, decay 300 ms, peak 1 nS per spike, `AHPsat` = 0 = AHPCLIP. The conductance is min(sum of per-spike kernels x peak, gmax) with gmax = 2 nS (`LIFCNeuron.cpp:261-264`).
- So after 2 spikes the cap binds. Raising only the peak changes almost nothing; the peak and gmax must be raised together.
- Arms:
  - S2: peak 2, gmax 4, decay 1000 ms.
  - S3: peak 3, gmax 6, decay 1500 ms.
  - Rise stays 30 ms.

**Scope.** The changes apply to pyramidal cells only (IDs 0-95). Interneurons keep their values (sAHP 0, TOVM), because the literature here is about pyramidal cells. Synaptic weights are not changed: they are programmed through the API exactly as in partial_cue addendum B, arm LH.

**Route.**
- For each run, copy the original model into the patched instance's model folder under a new name. Patch only the neuron fields of cells 0-95 in the copy, read the patch back, load the copy with `ModelLoad`, then program the weights through the API.
- The copy is deleted after the run. The originals are opened read-only.
- This is the same approach gaba_vm used for its file route. Nothing in NES itself is changed, and nothing goes upstream.

## Offline estimate (cell_offline.py, an approximate one-cell copy of the NES update; planning aid only)
Under constant excitatory drive of 12-30 nS (a stand-in for the recurrent drive during a reverberation):

| drive | LH | R (reset AFTER -55) | S2 | S3 (reset + S3, "RS3") |
|---|---|---|---|---|
| 12 nS | 16 spikes in 400 ms | 16 (first ISI 2.7 → 4.1 ms) | 12 | 9 |
| 30 nS | 39 | 39 | 36 | 32 |

- The reset alone hardly changes the steady rate. The fAHP (up to 5 nS at -90 mV) and threshold adaptation already set that rate.
- The stronger sAHP lowers the rate by about 10-45%.
- So any network effect would have to come from the recurrent loop losing gain, not from single cells stopping on their own.
- My prior is therefore modest: shorter and weaker reverberation is likely, and an end within 100 ms is unlikely.

## Baseline measures (baseline_measures.py on STORED partial_cue runs, no sims)
| run | median last Pyr spike after cue (completing events) | spikes per member in 450 ms | events with non-member spikes |
|---|---|---|---|
| s77777 LH r1 | 378 ms | 29.3 | 13/27 |
| s66666 LH r1 | 412 ms | 33.4 | 12/27 |
| s77777 LH r0.56 | 209 ms | 21.1 | 11/27 |
| s66666 LH r0.56 | 209 ms | 26.3 | 12/27 |

R3 D0 at r 0.56, the safety reference (grown background, cue→non-cue 4.125 nS):
- full cues complete 3/3, 3/3 and 4/4
- 3-of-4 cues complete 0/12, 0/12 and 0/16
- full-cue events end within 5-7 ms
- no non-member spikes

## Budget
14 sims, plus up to 2 reruns for load failures (counted and reported):
- 1 route control
- 11 LH-based runs
- 2 R3 safety runs

Detailed in PREREGISTRATION.md. Concurrency: at most 3 simulations at once across all workers. Gate on python simulation processes and on NES being alive. Restart the separate build (not the main one) when its RSS exceeds 10 GB and no simulation is running.
