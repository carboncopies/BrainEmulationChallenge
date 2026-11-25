# neuron_reset_ahp PREREGISTRATION (2026-11-24; written before any simulation of this study; not edited afterwards, changes go to DEVIATIONS.md)

**Question.** Can two literature-grounded pyramidal-cell changes, idea 1 and idea 2 of `../idea_scout3/IDEAS.md`, approved by John, end the 200-440 ms reverberation of the dense learned assembly? The assembly must still complete from 50-75% cues and stay silent for 25% cues, and R3 recall must not break. The two changes are:
- a fixed reset to -55 mV instead of the pre-spike Vm
- a stronger, slower slow AHP

Context and offline estimate: PLAN.md.

**Rules.**
- Patched instance only (NES 8011 / API 8010, venv python, patched client). Main NES 3156209 / API 1972355 untouched.
- No emails, no git, no pushes. Nothing upstream; NES code is unchanged.
- Model-file changes only on copies (deleted after each run).
- At most 3 simulations at once across all workers. The separate build is restarted when its RSS exceeds 10 GB and no simulation is running.

**Limits (all kept, asserted in code).**
- per pair <= 6.86 nS
- AMPA weight in [0.1, 1.0] of grown G
- NMDA r <= 1.0 nominal
- GABA x1-x2
- Dale's law
- Input cap: reported honestly, not enforced beyond what arm LH already does.

## Neuron arms (pyramidal cells 0-95 only; interneurons unchanged; everything else as in the model file)
| arm | ResetMethod / Vreset | sAHP peak / gmax / rise / decay | source of the values |
|---|---|---|---|
| N0 (control, = model file) | TOVM (pre-spike Vm, about -50 mV) / (-55 unused) | 1 / 2 nS / 30 / 300 ms | NetMorph build defaults |
| R | AFTER / **-55 mV** | unchanged | AdEx/LIF fits reset 3-10 mV below threshold; V_r >= V_T gives bursting (Naud et al. 2008, Biol Cybern 99:335, PMC2798047). CA3b fAHP 10.2 ± 0.5 mV below threshold; only 16-17% of CA3b cells burst, and only under strong current (Hemond et al. 2008, Hippocampus 18:411, PMC4339291). |
| S2 | unchanged | **2 / 4 nS / 30 / 1000 ms** | sAHP decay tau about 1.5 s (1.3-1.6 s), lasting seconds (Sahu & Turner 2021, Front Physiol 12:759707, review, mostly CA1). Per-spike slow adaptation of the Hippocampome CA3c fit: d = 104 pA with recovery about 500 ms (Venkadesh et al. 2018, Front Neuroinform 12:8, PMC5859109), i.e. about 2.6 nS at a 40 mV driving force (my conversion). The CA3 sAHP conductance itself was not found (UNVERIFIED), so the conductance is a constrained free parameter. |
| RS2 | R + S2 | 2 / 4 / 30 / 1000 | as above |
| RS3 | R + **3 / 6 nS / 30 / 1500 ms** | | decay at the measured 1.5 s; peak 3 nS ≈ the CA3c d at the upper end (my conversion) |

## Simulations (14 planned; load failures rerun unchanged, at most 2, counted)
Base design for 1-12: partial_cue addendum B, arm **LH**.
- Same allocated A17 assemblies (`partial_cue/alloc_b.json`) on s77777 and s66666.
- Same programmed weights: learned pairs at min(G, 6.86), with per-cell scaling to the 3T = 49.5 nS cap.
- Same 27 events with the same cue subsets: 1 full, 6 × 75%, 6 × 50%, 6 × 25%, 4 single-cell, 4 unrelated, 3 s apart.
- Same programming order and read-back. Code: `partial_cue/run_pl.py`, called unchanged through a wrapper that only substitutes the model copy.

| # | arm | model | r | GABA |
|---|---|---|---|---|
| 1 | N0 route control (unmodified copy) | s77777 | 1.0 | x1 |
| 2, 3 | R | s77777, s66666 | 1.0 | x1 |
| 4, 5 | S2 | s77777, s66666 | 1.0 | x1 |
| 6, 7 | RS2 | s77777, s66666 | 1.0 | x1 |
| 8, 9 | RS2 | s77777, s66666 | 0.56 | x1 |
| 10, 11 | RS3 | s77777, s66666 | 1.0 | x1 |
| 12 | RS2 | s66666 | 1.0 | x2 |
| 13, 14 | RS2 safety: R3 design D0 (`partial_cue/run_pc.py`: R3 memories, 4 cue + 2 non-cue, cue→non-cue 4.125 nS, grown background; full, 3-of-4, 2-of-4, 1-cell and cross cues, 3 s apart) | s77777, s66666 | 0.56 | x1 |

LH references: the stored addendum B runs. Run 1 checks that the model-copy route reproduces them.

## Measures (windows from cue onset t; non-contaminated events, i.e. <= 60 Pyr spikes in [t-1500, t))
These follow partial_cue B, plus the definitions in `baseline_measures.py`:
- **complete**: every non-cue member fires in [t, t+30).
- **recruit**: any non-cue Pyr cell fires in [t, t+30).
- **last**: time of the last Pyr spike in [t, t+1000) minus t.
- **stops100**: no Pyr spike in [t+100, t+450).
- **spikes per member**: member spikes in [t, t+450) / 17.
- **non-member spikes**: Pyr spikes of cells that are neither members nor cue cells in [t, t+450).
- **Completing events**: full, 75% and 50% events that complete.
- **Carry-over check** (preregistered): within each run, compare completion and *last* between events that follow a reverberating event (> 50 Pyr spikes in the previous event's 450 ms) and events that follow a non-reverberating one.

## Criteria
**PASS_T (the target, per run):**
- 75% cues complete >= 5/6
- 50% cues complete >= 4/6
- 25% cues recruit 0/6
- single-cell cues recruit 0/4
- unrelated cues recruit 0/4
- every completing event stops100
- 0 non-member spikes in every event

**RELIEF (per run):** median *last* of the completing events <= 50% of the LH reference for the same model and r, while 75% completion stays >= 5/6.
LH references (from baseline.json):
- s77777: r1 378 ms; r0.56 209 ms
- s66666: r1 412 ms; r0.56 209 ms

**SAFE (runs 13-14), compared with the stored D0 r0.56 runs of the same model:**
- full cues complete in all events
- 3-of-4, 2-of-4, 1-cell and cross cues recruit and complete nothing
- every full-cue event stops100 with 0 non-member spikes

**Route control (run 1):** same spiking cells and spike counts per cell as `rawB_s77777_LH_r1_f1`, with max |Δt| <= 0.01 ms.

## Predictions (HIT/MISS; confidence in brackets)
- **P0:** run 1 reproduces the stored LH run within the route-control tolerance (90%).
- **P1:** R alone: 75% completion >= 5/6 in both models (80%); RELIEF in at least 1 of 2 models (25%).
- **P2:** S2 alone: RELIEF in at least 1 model (35%); median spikes per member lower than LH in both models (80%).
- **P3:** RS2 r1: median spikes per member at least 30% lower than LH in both models (45%); RELIEF in at least 1 model (35%).
- **P4:** RS3 r1: RELIEF in at least 1 model (45%); 50% completion < 4/6 in at least 1 model (45%).
- **P5:** PASS_T in at least one of the 11 LH-based runs (2-12) (20%).
- **P6:** RS2: median *last* lower at r 0.56 than at r 1.0 in both models (75%).
- **P7:** GABA x2 vs x1 (RS2, s66666, r1): median *last* differs by <= 20% (60%).
- **P8:** SAFE in both models (80%).
- **P9:** 25%-cue, single-cell and unrelated cues recruit nothing (0) in every LH-based run (85%).
- **P10:** carry-over: in arms with sAHP decay >= 1 s, events after a reverberating event have a shorter median *last* than events after a non-reverberating one, in at least 1 run (50%). This is reported as a history effect, not as termination.

## Bio status (stated before running)
- All neuron values are inside the measured ranges cited above, except the sAHP conductance, which has no CA3 measurement. It is anchored by the Hippocampome CA3c fit conversion and flagged.
- Weights, NMDA (r <= 1.0 nominal; achieved lower, logged) and GABA (x1, x2) are within the existing limits.
- Input cap: as in LH (one hub cell over 49.5 nS in s77777, cell 3, floor 57.2 nS; none in s66666); flags written per run.
- If a run violates a limit, it is reported, not hidden.

## Reporting
- Every prediction is scored with numbers. Deviations go to DEVIATIONS.md.
- README.md contains the results, the neuron parameter table (value/range + reference) for Randal, and the honest limits.
- A learnings entry goes to `/home/johnjose/agent-library/LEARNINGS.md`.
- Post-hoc analyses are labelled.
