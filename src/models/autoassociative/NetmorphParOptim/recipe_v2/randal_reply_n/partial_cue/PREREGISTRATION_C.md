# partial_cue PREREGISTRATION_C (addendum 2, 2026-11-24; written before any simulation of this addendum; not edited afterwards, changes go to DEVIATIONS.md)

John approved the last ~6 sims (cap 50; 44 used, so **exactly 6 left**) for: **do weaker assembly pairs (strength below the ceiling, input cap 49.5 nS kept) keep completion from 50-75% cues without the 200-440 ms reverberation seen in LH (addendum B)?** Optional lower-cap arm (2T) only if sims remain.
Rules unchanged: patched instance NES 8011 / API 8010 only, venv python, patched client; main NES 3156209 / API 1972355 untouched; no emails/git/pushes; `bio_ranges.json` untouched; total concurrent sims across all workers <= 3 (I run <= 2; gate counts python processes `run_exp|fr_dyn|dyn*|run_pc|run_pl|run_pw`); per-pair <= 6.86 nS, AMPA weight in [0.1, 1.0], NMDA r <= 1.0 nominal, GABA x1-x2.

## Setup (same as addendum B except the arms)
Same two models and the same A17 assemblies (alloc_b.json; s77777 passes the density gate, s66666 near-gate), same events (27 per sim, same fixed cue subsets, 3 s apart), programming order, read-back, measures and contamination rule as PREREGISTRATION_B. Pyr->Int at the grown default, GABA x1. **NMDA r = 1.0 only** (the harder case for reverberation; r had little effect on LH completion in s66666). Learning is programmed, not run through SetSTDP; the homeostasis scaling is a script (outside NES), as in LH.
## Arms (5 shown below = 6 sims; every rerun after a failure takes a slot from the last arm)
- **W70**: every existing member pair set to x = max(grown default, 0.7 x min(G, 6.86)), then the LH homeostatic scaling to 3T (per-cell multiplicative scaling of the above-floor input, hubs keep the floor). (2 sims: s77777, s66666)
- **W50**: same with 0.5. (2 sims)
- **H2**: pairs at the full ceiling (as LH) but cap 2T = 33 nS (hub rule as before). (2 sims, only if all 4 W sims ran without loss; if a W sim must be rerun it uses one of these slots and H2 runs on s77777 only or not at all; any such change is stated in DEVIATIONS.)
Weights stay within [0.1, 1.0] of G and <= 6.86 nS by construction (asserted). Pair strength factors 0.7/0.5 are my choices (no biological measurement behind them: a "weaker learned pair" knob; a 0.5 pair is still a potentiated pair relative to the grown 0.2 G for G > ~ 2 nS).
Reference for every arm: LH (full-strength pairs, cap 3T, r 1.0, x1) from addendum B on the same models and cues (rawB_s*_LH_r1_f1.json), threshold-model reference on the same weights and cues.

## Measures and criteria (windows from cue onset t; as PREREGISTRATION_B)
Completion (all members spike in [t, t+30)), recruitment (any non-cue Pyr spike in [t, t+30)), spurious (non-member Pyr in 30 ms), Pyr spikes in 450 ms (pyr450), runaway = pyr450 > 50, duration = last Pyr spike within 2.9 s after the cue (reported when pyr450 > 50), late member spikes [t+15, t+450).
**PASS_C (window open without reverberation)** per (model, arm): 75% cues complete in 6/6 with no spurious spike; 25% cues recruit 0/6; single-cell 0/4; unrelated 0/4; **and in at least 5 of the 6 completed 75% events pyr450 <= 50** (no runaway), median pyr450 of the 75% events reported.
**"Reverberation relief"** = median pyr450 of 75%-cue events at least halved versus LH on the same model (LH medians: s77777 465, s66666 627.5 from addendum B), with 75% completion >= 5/6.
Input-cap status reported per arm (members above 49.5 nS, hubs).

## Predictions (scored HIT / MISS; confidence)
- C1: W70: 75% cues complete >= 5/6 in both models (60%). W50: 75% cues complete <= 3/6 in at least one model (55%).
- C2: Where W70 completes >= 5/6, at least half of those 75% events are runaway (pyr450 > 50), i.e. reverberation persists (60%). W50: where it completes >= 5/6, runaway in <= 50% of events (40%).
- C3: no W arm passes PASS_C in both models (65%); at least one (model, W arm) shows reverberation relief (35%).
- C4: 25% cues stay silent (0/6) and single/unrelated 0 in every W and H2 run (80%).
- C5: H2: 75% completion <= LH's (6/6 each) in both models and 25% silent (85%); median pyr450 lower than LH's in both models (55%).
- C6: The fraction of 50%-cue completions falls monotonically LH >= W70 >= W50 on each model (65%).
- C7: Any arm with 75% completion >= 5/6 and pyr450 <= 50 in >= 5/6 events exists (= a PASS_C-like result on either model) (30%).

## Reporting
Every prediction HIT/MISS with numbers; deviations to DEVIATIONS.md; post hoc items labelled; append to README.md and LEARNINGS.md; honest report including failure.
