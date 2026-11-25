# Forward predictions for neuron_reset_ahp (fable-knobs) arms (written 2026-11-24 before I read any raw/log file of theirs for these arms; model = rn.py, sweep_neuron.json, no inhibition term)

What I had already seen of their work: PREREGISTRATION.md, PLAN.md, cell_offline.py, and results.md rows for **N0 (s77777 r1)** and **S2 (s77777 r1)** only (S2: 75% 5/6, 50% 1/6, median last 232 ms, 20.6 spikes/member). Those two rows are retrodictions, everything below is forward. I did not open raw_*.json / log_*.txt / summary.json of any other arm.

Model numbers (median last member spike of completing full/75%/50% events, ms; stored LH reference in brackets; model overshoots absolute times, see README):
| arm | s77777 r1 (LH ref 378) | s66666 r1 (LH ref 412) | s77777 r0.56 (ref 209) | s66666 r0.56 (ref 209) |
|---|---|---|---|---|
| N0 / LH | 370 | 385 | 300 | 284 |
| R (-55) | 398 | 381 | 320 | 332 |
| S2 | 323 | 326 | 254 | 250 |
| RS2 | 342 | 346 | 282 | 258 |
| RS3 | 298 | 299 | 209 | 256 |
The model's S2 effect is about half of the one stored (S2 s77777: model 323 vs LH-model 370 = x0.87; stored 232 vs 378 = x0.61). Applying that one-point bias (a post-hoc scale, flagged) to the other sAHP arms gives roughly x0.6-0.75 of LH.

Predictions (HIT/MISS later; confidence in brackets), same wording as their P-list where they exist:
- F1 (their P1): R alone does not give RELIEF (median last <= 50% of LH) in either model (90%); its median last is within +/-15% of LH in both (80%). Reason: the reset changes the first ISI by a few ms, not the loop gain; the ignited state's lifetime is set by threshold-floor/sAHP accumulation.
- F2 (their P2/P3): S2 and RS2 shorten the median last by 15-45% in both models (65%) but RELIEF (<= 50%) is met in 0 of 2 models for S2 (80%), 0 of 2 for RS2 (75%).
- F3 (their P4): RS3 r1 RELIEF in at least 1 model: 25% (my model says x0.80, the bias-adjusted guess x0.55-0.6, i.e. borderline for s77777).
- F4: no neuron arm reaches PASS_T in any LH-based run (their P5 says 20%; mine: 90% that none does). Reason: 75% completion, 50% completion and termination all hinge on the same loop gain; the model has no window for 50% cues (c_comp ~ c_ign).
- F5: 50% completion falls below 4/6 in the stronger sAHP arms (S2 already 1/6 on s77777): in RS2 and RS3 on at least one model (80%).
- F6 (their P6): median last lower at r 0.56 than at r 1.0 in both models for RS2 (85%).
- F7 (their P7): GABA x2 vs x1 changes median last by <= 20% (75%): the model terminates or not independent of Int->Pyr strength in the range that still lets cues complete.
- F8: parameter regime in which the model terminates the 75% events within 100 ms while completing them: sAHP peak/gmax >= 8/16 nS with decay >= 1500 ms at r 0.56 (S8: last 25-42 ms, 75% 6/6 in both models, 50% 3/6 on s77777); not at r 1.0 within sAHP <= 8/16. That is 8x the model-file peak and 6x the conductance anchored by the Hippocampome fit conversion (2.6 nS): outside the anchored range, so it is an upper bound on what the literature can justify, not a recommended value.
