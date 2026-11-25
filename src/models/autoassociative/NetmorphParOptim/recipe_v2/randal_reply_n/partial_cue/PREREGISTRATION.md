# partial_cue PREREGISTRATION (2026-11-23, written before any simulation of this task; not edited afterwards, changes go to DEVIATIONS.md)

Task (John approved Stage 2 of fresh_learn, narrowed): mechanism test of PARTIAL-CUE COMPLETION in the patched build, <= ~50 simulations. Not a capacity claim.
Starting facts (from nmda_gaba_exp/README.md and fresh_learn/README.md, read before writing this): R3 programming (cue->non-cue pair = 4.125 nS, 4 cue cells = threshold 16.5 nS): 2-of-4 cues never complete; 3-of-4 complete only at NMDA r 1.0 and depend on threshold-recovery history (post hoc with 3 s spacing: r 1.0 40/40, r 0.56 0/40); GABA does not gate partial completion (interneurons fire after the decision). fresh_learn Stage 1 (threshold model, no inhibition): with learned/saturated weights dense assemblies ignite from small cues (completion-silence window does not open).
Questions: (Q1) can partial cues (3-of-4, 2-of-4) complete with all parameters inside biological limits, when the cue->non-cue AMPA conductance is raised toward the per-pair cap, without making 1-cell cues or unrelated cues recruit? (Q2) does the STDP-saturated "learned assembly" design (all existing member pairs at the ceiling, the thing fresh_learn assumed) open the window in real dynamics, or does it ignite from small cues / reverberate? (Q3) does GABA x1 vs x2 change either?

## Setup (fixed)
- Patched instance only: NES 8011 / API 8010, venv python, patched client first on path (asserted in code). Main NES 3156209 / API 1972355 untouched. No emails, no git, no pushes, no model-file edits, `bio_ranges.json` untouched.
- Concurrency: max 3 simulations in total across all workers. I run at most 2 at a time and check `pgrep` for other workers (`run_exp|dyn|recall|run_pc`) before every launch; arbor-seeds' NetMorph growth processes (`grow_fr.py`, `gen_autonm_labels.py`) are not NES simulations. Every simulation is deleted in a `finally`.
- Models and memories: E4 models s33333 (3 memories), s66666 (3), s77777 (4) = the same disjoint 6-cell memories (4 cue + 2 non-cue) as nmda_gaba_exp (`headline_i/groups_D42_V1n20_s*.json`). Abstracted LIFC, precise spike times, STDP off, Dt 0.1 ms, cue cells driven by `SetSpecificAPTimes` at offsets 0, 0.5, 1.0, 1.5 ms (partial cues use the first offsets in cell-ID order). **Spacing between events 3.0 s** (threshold recovery, nmda_gaba_exp).
- Programming (API only, order as nmda_gaba_exp): AMPA via the legacy batch call, then NMDA = r x programmed AMPA on every programmed Pyr->Pyr/Pyr->Int pair with an NMDA group (`Neurotransmitter='NMDA'`, capped at the grown NMDA peak by the simulator), then GABA = f x 0.2 x grown GABA peak. Whole connectome read back; any mismatch aborts.
- **Designs** (cue-cue pairs keep c = 1.5 nS in D0-D2; loops, Pyr->Int programming and all caps as `ovlib.pair_list_ov`):
  - **D0 (R3 control)**: cue->non-cue pair = 4.125 nS (= T/4).
  - **D1**: cue->non-cue pair = min(5.5 nS, grown G).
  - **D2**: cue->non-cue pair = min(6.86 nS, grown G), i.e. at the per-pair cap (Randal `autoassociative_connectome.py:75-79`); AMPA weight <= 1.0 always; programmed pairs with G > 6.86 are held at 6.86 nS.
  - **DL (learned-assembly, STDP-saturated)**: every existing Pyr->Pyr pair among the 6 members (cue-cue, cue->non-cue, non-cue->cue, non-cue loops) at min(G, 6.86) nS; Pyr->Int as D0. This is what potentiation-only STDP would give co-active members; no homeostasis script is applied (cell input stays below the 3T = 49.5 nS cap by construction: <= 5 x 6.86 = 34.3 nS; I check and flag).
  - Biological limits kept: per-pair <= 6.86 nS, AMPA weight in [0.1, 1.0] of grown G for programmed pairs, Dale (only Pyr outputs touched for AMPA/NMDA; GABA only scaled by f), NMDA r <= 1.0 nominal (achieved ~0.75 on cue->non-cue, 0.43-0.61 on loops), GABA x1-x2. Nothing relaxed; D2/DL are the upper edge, not beyond it.
- **Events per memory** (3.0 s apart): full cue (4), each 3-of-4 (4), each 2-of-4 (6), each single cue cell (4) = 15; plus per pair of memories one **mixed unrelated cue** x2 = one cue cell from each of the two memories (silence expected), 3 / 3 / 6 events. s33333, s66666: 48 events (144 s), s77777: 66 events (198 s).

## Plan: 32 simulations (+ <= 8 reserve for reruns)
- A (s33333): 4 designs x r in {0.56, 1.0} x GABA f in {1, 2} = **16**.
- B (s66666 and s77777): 4 designs x r in {0.56, 1.0} x f = 1 = **8 + 8 = 16**.
- First sim of A is the smoke test and counts if it runs clean. Reserve (<= 8): reruns after load failures / NES restarts, or a targeted follow-up (declared in DEVIATIONS.md). Hard cap 50.

## Measures (windows from cue onset t; first cue spike at t)
- **Completion** of memory m: every non-cue member of m spikes in [t, t + 30). **Recruitment** (for 1-cell, x2, 2- and 3-cell events): any spike in [t, t + 30) of a Pyr cell that is not a cue cell of the event. **Spurious** completion: a non-member Pyr cell fires in [t, t + 30).
- **Full-cue clean**: late member spikes in [t + 15, t + 450) = 0 and <= 2 non-member Pyr spikes in [t, t + 450). **Runaway**: > 50 Pyr spikes in [t, t + 450).
- **Contamination**: > 60 Pyr spikes in the 1,500 ms before the event; excluded from rates, counted separately (raw counts also reported).
- **Window open (PASS_3)** for a (design, r, f) cell pooled over the seeds run: full cues complete 100% and clean >= 95%; 3-of-4 complete >= 90%; single-cell recruitment <= 10%; x2 unrelated recruitment 0%. **PASS_2**: same with 2-of-4 complete >= 50%.

## Predictions (scored HIT / MISS on non-contaminated events; confidence in brackets)
- P0 (control D0, f = 1): 3-of-4 completion r 0.56 <= 10%, r 1.0 >= 90% (3 s spacing); 2-of-4 0% at both (80%).
- P1 (D1): 3-of-4 completion >= 90% at r 0.56 and r 1.0; 2-of-4 <= 10% (65%).
- P2 (D2): 2-of-4 completion >= 30% at r 1.0, f = 1 (45%); 3-of-4 >= 95% at both r (75%); full cue clean >= 95% at r 0.56 but < 95% at r 1.0 (45%).
- P3 (DL): 2-of-4 completion >= 50% AND single-cell recruitment >= 25% at r 0.56, f = 1, i.e. the window is closed; full-cue clean < 95% at r 1.0 f = 1 (70% / 60%).
- P4 (GABA): f = 2 vs f = 1 changes partial completion by <= 10 points in every design (80%); f = 2 lowers the non-clean full-cue fraction of D2/DL at r 1.0 by >= 30% (65%).
- P5 (unrelated): x2 mixed cue recruits nothing in D0-D2 for every r, f (100% silent); DL >= 90% silent (75%).
- P6 (overall): at least one design passes PASS_3 at f = 1 (D0 r 1.0 expected) (75%); no design passes PASS_2 (60%).
- P7 (Stage-1 link): in DL, wherever 2-of-4 completion is >= 50%, 1-cell recruitment is > 10%, i.e. the Stage-1 "window problem" shows up in the simulator (65%).

## Reporting
Every prediction HIT/MISS with numbers; deviations in DEVIATIONS.md; post-hoc analyses labelled; flags for any non-bio setting; honest report incl. failure. Learnings logged to /home/johnjose/agent-library/LEARNINGS.md.
