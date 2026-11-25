# stability: is the completed 17-cell state self-sustaining? (offline, 2026-11-24)

Offline only: 0 sims, no NES/API call. Inputs: stored partial_cue addendum B/C runs (read only), the model-file neuron constants, Netmorph synapse constants. Nothing under `neuron_reset_ahp/` was touched (I read its PREREGISTRATION.md, PLAN.md, results.md, cell_offline.py). No emails, git, pushes. `PROTOCOL.md` (written before the model met any stored event) and `PREDICTIONS_FORWARD.md` (written before I read any of fable-knobs' other arms) are unedited.

## Method (rn.py)
- 17 member cells with the exact LIFC equations of `cell_offline.py` (adaptive threshold h + floor +1 mV/spike tau 500 ms, fAHP, sAHP with AHPCLIP, reset TOVM/AFTER), the **exact programmed member matrices** (rebuilt with fllib + pwlib.arm_matrix; column sums match the stored `member_input_nS` to 0.004 nS), AMPA 0.5/3 ms, NMDA 2/100 ms with Mg block, GABA 0.5/10 ms, 1 ms delay, NMDA = min(r AMPA, 0.5612 G), the stored cue schedules (27 events per run, all events of a run batched).
- **No fitted parameter.** My protocol planned to calibrate one inhibition scalar on s77777 LH r1; the calibration failed (Deviation 1) so the main analysis has **no inhibition term and nothing tuned**: every comparison with a stored run is out of sample for parameters (not for my knowledge of the outcomes, see PROTOCOL.md).
- Inhibition is analysed separately with 7 explicit interneurons (strengths free, not stored): `inh_scan.py`.
- Not modelled: non-member Pyr, carry-over between events (fresh cell state per event), real Pyr->Int/Int->Pyr conductances.

## Answers
**1. Is the completed state self-sustaining with adaptation included? Yes, as a metastable ignited state with a finite lifetime.**
Scaling all recurrent member conductances by c, every event is all-or-none: either it ends within ~10-20 ms of completion, or all 17 members run at ~170-340 Hz and stop only after about 280-440 ms (`t4.py`). The ignition threshold is a sharp bistability, and the lifetime (370-385 ms for LH r1; 284-300 ms at r 0.56) is set by adaptation, not by the weights: it hardly moves when c is varied above threshold. So "silence after completion" is not a stable fixed point of this circuit; it is a transient that ends when threshold floor + AHP have removed enough gain.
- AMPA alone (NMDA x0) ends after about 50 ms; the NMDA tail (tau 100 ms) holds the ignited state. Removing half of NMDA shortens it to ~200 ms (`t3.py`). In the model, NMDA at its capped value is what makes the 200-440 ms event.

**2. One number predicts ignition: the dominant eigenvalue of the member AMPA matrix.** (`scan_c.py`, `scan_table.md`)
rho(AMPA) x (first scale that ignites) is 16.4-18.3 nS in all 9 arm/model cases (mean 17.4), whatever the arm or model. Completion of 75% cues needs rho ~14.4-17.2 nS (mean 15.8); completion of 50% cues needs 17-20 nS, i.e. at or above ignition. So:
| cue | window between "completes" and "ignites" | width |
|---|---|---|
| 75% | rho in about 15.8 - 17.4 nS | about 10% of rho |
| 50% | none (|c_comp - c_ign| <= 0.025 in 35 of 37 events that complete or ignite; 17 more never do up to c = 1.35) | 0 |
| 25%, 1 cell, unrelated | never complete (silent) | - |
Table (at the programmed c = 1; `scan_table.md`):
| run | rho(AMPA) | median c_ign (75%) | ignites in n/6 | completes without igniting |
|---|---|---|---|---|
| s77777 LH | 21.5 | 0.850 | 6 | 0 |
| s66666 LH | 22.9 | 0.800 | 6 | 0 |
| s77777 W70 | 17.0 | 1.012 | 3 | 3 |
| s66666 W70 | 17.9 | 0.975 | 5 | 0 |
| s77777 W50 | 13.2 | 1.275 | 0 | 2 (stored 0) |
| s66666 W50 | 13.7 | 1.225 | 0 | 0 |
| s77777 2T | 12.6 | 1.300 | 0 | 0 |
| s77777 L0 (no homeostasis) | 34.3 | 0.525 | 6 | 0 |
| s66666 L0 (no homeostasis) | 32.7 | 0.538 | 6 | 0 |

**3. Why W70 works on s77777 and not on s66666 (analysis).** At the same pair factor 0.7, s77777 has rho = 17.0 nS and s66666 17.9 nS (5% higher; same 3T cap rule, different graph and hubs). The ignition threshold is rho ~17.4 +- 1. s77777 sits about 2% below it (window open for 3 of 6 cues at c = 1, 4-5 of 6 at c = 0.975), s66666 about 3% above (ignites in 5 of 6). **The difference is a 5% difference in dominant eigenvalue against a window about 10% wide, with a calibration uncertainty of the threshold itself of about +-6%**: the model gives the right direction and the right size of the effect, but cannot resolve a knife edge; it predicts s77777 W70 igniting in 3/6 events where the stored run shows 0/6 (miss, below).

**4. Inhibition.** (`inh_scan.py`, 7 interneurons all-to-all, free strengths) The model has a threshold in Int->Pyr strength: below it inhibition does nothing (reverberation 365-417 ms, GABA at 0.25-1 nS per pair no effect), above it events end within 10-25 ms. That matches the stored invariance to GABA x1/x2 (L0 f1 vs f2; LH) if the real strength is below threshold. Where it kills the ignition, it also removes completion from 50% cues (s77777 LH, Pyr->Int 1 nS: 50% completion 5/6, 4/6 at gIP 1.5, 2/6 at gIP >= 2; Pyr->Int 3 nS: 0/6) and, at stronger inhibition, 75% cues (6/6 -> 3/6). A usable window (75% complete, ends in 18 ms) exists in the model at gPI 1, gIP 1.5 for s77777 LH (6/6, 50% 4/6); on s66666 LH it needs gIP 2 (6/6 75%, 5/6 50%). The stored LI arm (all Pyr->Int at weight 1.0) still reverberated for partial cues, so real feedback inhibition has not reached that threshold. These strengths are unmeasured; this is a sensitivity scan, not a prediction of the real value.

## Check against stored data (score.py, all 14 B/C runs except LI, 83 class cells; definitions fixed in PROTOCOL.md)
| measure | agreement |
|---|---|
| complete / recruit / reverb counts within 1 event | **78/83 = 94%** |
| median member spikes in 450 ms within x2 | 53/83 = 64% (model overshoots reverberating events 2-10x; low for strongly driven L0) |
| median last member spike within 100 ms | 65/83 = 78% (LH/W70/W50/2T only: 98%) |
| termination call (median last of 75% events < 100 ms) | **12/14** runs; misses: s77777 W70 (model ignites 3/6, stored 0/6), s66666 L0 r1 (stored ends, model ignites) |
| ordering of arms by median member spikes | Spearman 0.52 (s77777) and 0.09 (s66666) with L0 included; 0.90 and 1.00 without L0 |
Verdict by the protocol rule (>= 75% agreement AND ordering): **partly**. The categorical outcomes (which arms ignite, which complete, which end) are predicted (94% counts, 12/14 terminations, W50 and 2T exactly: same spike counts to within 1-3), the quantitative spike counts and the ordering of arms with L0 are not. The sign of the W70 s77777-vs-s66666 difference is right, the s77777 W70 magnitude is a miss (3/6 vs 0/6 igniting). The model does not capture r: at r 0.56 it ends ~80 ms later than the stored runs (284-300 vs 207-209 ms).
Retrodiction check on fable-knobs' stored S2 s77777 row (seen before, so not blind): model median last 323 vs stored 232, 75% completion 6/6 vs 5/6 (hit), 50% completion 5/6 vs 1/6 (**miss**: S2 raises thresholds at the cue and kills 50% completion; the model does not).

## Predicted parameter ranges for fable-knobs (neuron_reset_ahp; `sweep_neuron.py`, `PREDICTIONS_FORWARD.md`)
LH weights, r 1, median last member spike (ms) in the model (stored LH 378 / 412): reset -55 **398 / 381**; reset -60 397 / 394; reset -52 364 / 381; S2 (2/4 nS, 1000 ms) 323 / 326; RS2 342 / 346; RS3 298 / 299; sAHP 4/8 nS 285 / 253; 6/12 251 / 227; 8/16 nS decay 1500 ms **189 / 229**.
- **Reset: no relief** (changes last by -5% to +10%). It does not change the loop gain.
- **sAHP alone cannot end the ignition**, only shorten it: the ignition occurs in the first ~50 ms, before slow adaptation builds. Within the anchored range (peak <= 3 nS, gmax <= 6, decay <= 1500 ms) the model predicts x0.87 (S2) to x0.80 (RS3) of LH; the one stored S2 point is x0.61, so the model underestimates the sAHP effect by about half (bias-adjusted guess for RS3: x0.55-0.6, borderline for RELIEF).
- Reaching RELIEF (<= 50% of LH) needs sAHP peak/gmax about 8/16 nS (6x the anchored 2.6 nS conversion; outside the literature range) at r 1; at r 0.56 the model terminates the event within 25-44 ms at 8/16 nS (decay 1500 ms) while keeping 75% completion 6/6 (50% completion 3/6 on s77777, 5/6 on s66666); 6/12 nS does not terminate at r 0.56 (last 180-190 ms).
- Expect no PASS_T from any neuron arm: 50% completion is lost together with the reverberation (no window), the same trade-off as the weaker-pair arms.
- Strength of the claim: forward predictions written before reading their other arms (`PREDICTIONS_FORWARD.md`); scoring is left until their runs are available to me.

## Design rule suggested by the analysis (hypothesis, needs sims; no sims were run)
Choose assembly pair strengths so that rho(AMPA member matrix) is about 15.5-16.5 nS (above the completion level of 75% cues, about 15.8, below the ignition level 17.4 +- 1), ideally computed per model, instead of a fixed factor of the ceiling (0.7 gave 17.0 and 17.9, on opposite sides of the threshold). Expected: 75% completion without reverberation in most models, no 50% completion. Cost to test: 3 models x 1-2 factors = about 6 sims, needs John's approval.

## Deviations from PROTOCOL.md
1. The planned one-parameter inhibition calibration (kappa, then explicit interneurons with 2 free strengths: `calib.py`, `calib2.py`) could not match the stored time course or spike counts: every setting either left the reverberation untouched or removed it entirely, and the model's member spike count stays 2x too high (949-1235 vs 499 median; stored time course has a dip at 100-150 ms the model lacks). I dropped the calibration, kept the model with **no fitted parameter and no inhibition**, and analysed inhibition as a sensitivity scan. The overshoot of spike counts and the missing dip are unexplained (candidates, not tested: missing non-member and interneuron dynamics, differences between `cell_offline.py` and LIFCNeuron.cpp, depolarisation effects at high drive; L0 stored runs fire fewer spikes than LH although input is larger).
2. Scoring protocol used as written; I added the LH/W70/W50/2T-only subset as an extra line (labelled).

## Limits
Two models, one allocated assembly each, six cues per size, the model is a 17-cell reduction (no non-members, no Int dynamics, no carry-over); c_ign and rho_ign have a resolution of 0.025 in c; the rho criterion was found on these 9 arm/model cases and is untested out of sample (also not tested at r 0.56 or on other models); absolute reverberation durations and all spike counts are not predicted well; the sAHP prediction was bias-corrected with a single stored data point.

## Files
rn.py (reduced model), calib*.py (failed calibration, kept), t0.py (matrix check), t2-t5.py (diagnostics), scan_c.py -> scan_c.json, scan_table.md; sweep_neuron.py -> sweep_neuron.json; inh_scan.py -> inh_scan.json; score.py -> score_table.md; PROTOCOL.md, PREDICTIONS_FORWARD.md.
