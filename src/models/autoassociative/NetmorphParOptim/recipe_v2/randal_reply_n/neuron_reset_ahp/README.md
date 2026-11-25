# neuron_reset_ahp: literature reset and slow AHP on the dense learned assembly (2026-11-24)

**What was run.**
- 14 simulations as preregistered, with no failures and no reruns. Summed wall time 2.2 h, at most 3 sims at once, no other worker active. Every simulation was deleted.
- Changes were made only to model-file COPIES in the patched instance's model folder; all copies were removed. NES code was not changed; nothing was pushed or committed, and no emails were sent.
- Patched instance only (NES 8011 / API 8010). It was restarted once before the first run (residual sim, 12.7 GB; DEVIATIONS 2). Main NES 3156209 / API 1972355 were untouched.

**Files.**
- PLAN.md: offline plan and single-cell estimate (`cell_offline.py`)
- PREREGISTRATION.md: written before any sim, unedited
- DEVIATIONS.md: 4 items, including an analysis bug fixed before scoring
- `run_nr.py`: patched copy plus the unchanged `partial_cue/run_pl.py` / `run_pc.py`
- `run_queue.sh`, `check_route.py` → `route_check.json`
- `analyze_nr.py` → `results.md`, `summary.json`, `events.json`
- post hoc: `posthoc_residual_sahp.py` → `posthoc_residual_sahp.json`
- `raw_*.json`, `log_*.txt`, `runs/` (intermediate outputs)

## Short answer
1. **The fixed reset to -55 mV (idea 1) does nothing measurable to the reverberation.**
   - Median last Pyr spike after the cue: s77777 383 → 393 ms; s66666 413 → 393 ms.
   - Spikes per member: 29.4 → 29.0 and 33.4 → 32.1.
   - Completion is unchanged.
   - Why: the fAHP (up to 5 nS at -90 mV) and the adaptive threshold already hold a cell below threshold after a spike. The reset value only lengthens the first interspike interval (PLAN.md offline estimate, confirmed).
2. **The stronger, slower slow AHP (idea 2) shortens the reverberation, but at measured parameters it ends within 100 ms in only one of the two models, and it costs 50%-cue completion.**
   - At r 1.0, reset plus sAHP x2 (1 s) gives 243 / 271 ms.
   - Reset plus sAHP x3 (1.5 s) gives **96 ms on s77777** (RELIEF; 4 of 7 completing events stop within 100 ms) but 194 ms on s66666.
   - **The best case is s77777, RS2 at r 0.56.** Every completing event stops within 100 ms (9/9), with a median last spike at 25 ms and 4.9 spikes per member (LH: 209 ms, 21.1). 75% cues complete 6/6, and 25%, single-cell and unrelated cues stay silent. It still misses the target: 50% cues complete 2/6, the same as its LH reference at r 0.56, and 2 events have 2 non-member spikes. The same setting on s66666 runs 160 ms.
3. **No run meets the full preregistered target (PASS_T)** on either model.
4. **The 50%-cue loss is a history effect of the long sAHP (post hoc).**
   - At the cue onsets of failed 50% events, the reconstructed residual sAHP is 2.4-6 nS. It is left over from the previous reverberation, 3 s earlier.
   - At completed 50% events it is 0-0.1 nS. In s77777 RS2 r0.56 the split is weak (0.6 vs 0.9 nS).
   - So with the measured sAHP (decay 1-1.5 s, lasting seconds), an assembly that has just reverberated is refractory to weak cues for several seconds.
   - Whether 50% completion returns with longer spacing (e.g. 8-10 s) was not tested.
5. **Nothing else broke.**
   - 25%-cue, single-cell and unrelated cues recruited no cell in any run.
   - R3 recall (D0 design, r 0.56) with reset plus sAHP x2 is identical in outcome to the stored runs on both models: full cues 3/3 and 4/4; 3-of-4, 2-of-4, 1-cell and cross cues 0; full-cue events end in 4.6 ms; no non-member spikes.
   - GABA x2 (s66666 RS2 r1) changed the median duration by +9.5% (271 → 296 ms): GABA again does not end it.

## Results: dense assembly A17, LH weights (non-contaminated events; contamination 0 in every run)
"Completing" = full, 75% and 50% events that complete. "last" = last Pyr spike after the cue. "stops100" = no Pyr spike in [t+100, t+450).

| model | arm | r | GABA | 75% compl | 50% compl | 25% / 1-cell / unrel recruit | median last (ms) | max last | stops100 | spikes per member (median) | events with non-member spikes | PASS_T |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s77777 | LH (stored) | 1 | x1 | 6/6 | 6/6 | 0/6, 0/4, 0/4 | 383 | 442 | 0/13 | 29.4 | 13/27 | fail |
| s77777 | N0 (route control) | 1 | x1 | 6/6 | 6/6 | 0, 0, 0 | 383 | 442 | 0/13 | 29.4 | 13/27 | fail |
| s77777 | R | 1 | x1 | 6/6 | 6/6 | 0, 0, 0 | 393 | 447 | 0/13 | 29.0 | 12/27 | fail |
| s77777 | S2 | 1 | x1 | 5/6 | 1/6 | 0, 0, 0 | 234 | 240 | 0/7 | 20.6 | 8/27 | fail |
| s77777 | RS2 | 1 | x1 | 6/6 | 2/6 | 0, 0, 0 | 243 | 263 | 0/9 | 20.5 | 10/27 | fail |
| s77777 | RS3 | 1 | x1 | 5/6 | 1/6 | 0, 0, 0 | **96** | 130 | 4/7 | 9.6 | 2/27 | fail |
| s77777 | LH (stored) | 0.56 | x1 | 6/6 | 2/6 | 0, 0, 0 | 209 | 210 | 0/9 | 21.1 | 11/27 | fail |
| s77777 | **RS2** | 0.56 | x1 | 6/6 | 2/6 | 0, 0, 0 | **25** | 90 | **9/9** | 4.9 | 2/27 (2 spikes each) | fail (50%, non-member) |
| s66666 | LH (stored) | 1 | x1 | 6/6 | 5/6 | 0, 0, 0 | 413 | 515 | 0/12 | 33.4 | 12/27 | fail |
| s66666 | R | 1 | x1 | 6/6 | 6/6 | 0, 0, 0 | 393 | 490 | 0/13 | 32.1 | 13/27 | fail |
| s66666 | S2 | 1 | x1 | 6/6 | 2/6 | 0, 0, 0 | 305 | 311 | 0/9 | 26.2 | 9/27 | fail |
| s66666 | RS2 | 1 | x1 | 6/6 | 3/6 | 0, 0, 0 | 271 | 294 | 0/10 | 24.4 | 10/27 | fail |
| s66666 | RS2 | 1 | x2 | 6/6 | 3/6 | 0, 0, 0 | 296 | 336 | 0/10 | 24.1 | 10/27 | fail |
| s66666 | RS3 | 1 | x1 | 6/6 | 2/6 | 0, 0, 0 | 194 | 204 | 0/9 | 18.2 | 9/27 (22-28 spikes each) | fail |
| s66666 | LH (stored) | 0.56 | x1 | 6/6 | 5/6 | 0, 0, 0 | 209 | 233 | 0/12 | 26.4 | 12/27 | fail |
| s66666 | RS2 | 0.56 | x1 | 6/6 | 2/6 | 0, 0, 0 | 160 | 165 | 0/9 | 19.8 | 9/27 | fail |

Full table, including carry-over columns: `results.md`.

## Results: R3 safety (D0 design, r 0.56, x1)
| model | arm | full complete | 3-of-4 complete / recruit | 2-of-4 recruit | 1-cell recruit | cross recruit | full stops100 | full median last | non-member events | SAFE |
|---|---|---|---|---|---|---|---|---|---|---|
| s77777 | stored | 4/4 | 0/16 / 0/16 | 0/24 | 0/16 | 0/6 | 4/4 | 4.6 ms | 0/66 | SAFE |
| s77777 | RS2 | 4/4 | 0/16 / 0/16 | 0/24 | 0/16 | 0/6 | 4/4 | 4.6 ms | 0/66 | SAFE |
| s66666 | stored | 3/3 | 0/12 / 0/12 | 0/18 | 0/12 | 0/3 | 3/3 | 7.4 ms | 0/48 | SAFE |
| s66666 | RS2 | 3/3 | 0/12 / 0/12 | 0/18 | 0/12 | 0/3 | 3/3 | 4.6 ms | 0/48 | SAFE |

## Preregistered predictions scored
RELIEF references: 378/412/209/209 ms as preregistered, or 383/413/209/209 ms with the full-cue fix (DEVIATIONS 1). The verdicts are the same under both.

| | prediction (confidence) | observed | score |
|---|---|---|---|
| P0 | route control reproduces the stored LH run (90%) | 6,487 / 6,487 spikes, same cells, max \|Δt\| 0.0 ms | HIT |
| P1 | R: 75% completion >= 5/6 in both (80%); RELIEF in >= 1 model (25%) | 6/6, 6/6; last 393 vs 383, 393 vs 413 ms | HIT / MISS |
| P2 | S2: RELIEF in >= 1 model (35%); spikes per member lower than LH in both (80%) | 234/383 = 0.61, 305/413 = 0.74; 20.6 < 29.4, 26.2 < 33.4 | MISS / HIT |
| P3 | RS2 r1: spikes per member >= 30% lower in both (45%); RELIEF in >= 1 (35%) | -30.3% (s77777), -27% (s66666); 0.64, 0.66 | MISS (s66666 by 3 points) / MISS |
| P4 | RS3 r1: RELIEF in >= 1 model (45%); 50% completion < 4/6 in >= 1 (45%) | s77777 96/383 = 0.25 with 75% at 5/6; 1/6 and 2/6 | HIT / HIT |
| P5 | PASS_T in >= 1 of the 11 LH-based runs (20%) | none | MISS |
| P6 | RS2: *last* lower at r 0.56 than at r 1.0 in both (75%) | 25 < 243; 160 < 271 | HIT |
| P7 | GABA x2 vs x1 changes *last* by <= 20% (60%) | +9.5% | HIT |
| P8 | SAFE in both models (80%) | both identical to stored | HIT |
| P9 | 25%-cue, single-cell and unrelated cues recruit 0 everywhere (85%) | 0 in all 13 LH-based runs | HIT |
| P10 | carry-over: after-reverb events have a shorter median *last* than after-quiet events, in >= 1 sAHP >= 1 s run (50%) | yes in 3 runs (s66666 S2 293 vs 303, RS3 188 vs 196, RS2 r0.56 153 vs 160), but small and n = 2-3; the LH reference itself shows 346 vs 419 | HIT (weak, not specific to the new sAHP) |

Totals, counted by clause (P1-P4 have two clauses each): 15 clauses, 10 HIT, 5 MISS. The misses are P1b, P2a, P3a, P3b and P5. P10 is a weak HIT.

## Neuron parameters used, with literature values (for Randal)
Changes apply to pyramidal cells (0-95) only; interneurons keep the build values. Status: VERIFIED = an agent fetched the page and read the value (idea_scout3 method); UNVERIFIED = not found or second-hand.

| parameter | build value (model file) | used here | literature value / range | reference (status) |
|---|---|---|---|---|
| Reset after spike | TOVM: Vm before the spike, at most -50 mV (= threshold) | AFTER: **-55 mV** (the file's own `Vreset`) | AdEx fits: V_r about -53 mV against V_T -42 to -56 mV; V_r >= V_T gives bursting | Naud, Marcille, Clopath & Gerstner 2008, Biol Cybern 99:335, https://pmc.ncbi.nlm.nih.gov/articles/PMC2798047/ (VERIFIED) |
| | | | CA3b fAHP 10.2 ± 0.5 mV, threshold -40 to -45 mV, so a trough of about -50 to -55 mV (my inference); 16-17% of CA3b cells burst, only under strong current | Hemond et al. 2008, Hippocampus 18:411, https://pmc.ncbi.nlm.nih.gov/articles/PMC4339291/ (VERIFIED) |
| | | | CA3c Izhikevich fit: reset 2 mV below threshold plus a recovery jump d = 104 pA per spike (recovery about 500 ms) | Venkadesh et al. 2018, Front Neuroinform 12:8, https://pmc.ncbi.nlm.nih.gov/articles/PMC5859109/ (VERIFIED, Table 1) |
| sAHP decay | 300 ms | **1000 ms** (S2, RS2), **1500 ms** (RS3) | decay tau about 1.5 s (1.3-1.6 s); peak about 0.5 s after a train; lasts 3-5 s after 10 spikes and up to 20 s after 150 | Sahu & Turner 2021, Front Physiol 12:759707, https://www.frontiersin.org/articles/10.3389/fphys.2021.759707/full (VERIFIED review; mostly CA1) |
| sAHP conductance per spike / cap (AHPCLIP) | 1 / 2 nS | **2 / 4 nS** (x2), **3 / 6 nS** (x3) | no CA3 sAHP conductance found (UNVERIFIED). Anchor: CA3c fit d = 104 pA per spike, about 2.6 nS at a 40 mV driving force (my conversion). CA3 network model with strong adaptation: b = 207 pA per spike, tau_w 85 ms | Venkadesh 2018 (above); Ecker et al. 2022, eLife 11:e71850, https://doi.org/10.7554/eLife.71850 (VERIFIED) |
| sAHP rise | 30 ms | 30 ms (unchanged) | build value | - |
| fAHP, adaptive threshold, ADP, Rm, Cm, Vth | build values (fAHP 3/5 nS, 2.5/30 ms; threshold +10 mV x (1-h), h 0.2/spike, tau 50 ms; floor +1 mV/spike, tau 500 ms) | unchanged | not tested here | - |

## Limits
- Two models and one assembly each, with 6 cues per size. The simulator is deterministic, so 2/6 vs 4/6 is two cues.
- Learning is programmed (saturation plus the cap script), not run through SetSTDP. The input cap is as in LH: s77777 hub cell 3 at 57.2 nS (1 member above 49.5 nS); s66666 none.
- NMDA nominal r 1.0 achieves about 0.80-0.85 on the programmed pairs here; r 0.56 achieves about 0.54.
- The sAHP conductance has no CA3 measurement; the values are anchored by a model fit, not by data.
- Events are 3 s apart. With a sAHP lasting seconds this spacing is part of the result: it is what causes the 50%-cue loss (post hoc).
- The "non-member" criterion is strict. The best run fails it with 2 spikes in each of 2 events.

## What this means and possible next steps (not started)
- **The reset is not the reason for the reverberation.** It can be set to the literature value (-55 mV) for realism, at no cost to recall: R3 outcomes, completion and silence are unchanged.
- **A measured-scale slow AHP is a genuine terminator, but not a sufficient one.**
  - It ends the events within 100 ms only where the recurrent drive is lower: s77777 at r 0.56, or at sAHP x3.
  - Because it lasts seconds, it also makes a just-active assembly refractory to weak cues. That is a biological behaviour, but it fails the "50% cues complete" target at 3 s spacing.
- **Cheap follow-ups (each needs John's go):**
  - RS2/RS3 with 8-10 s spacing, to see whether 50% completion returns (4 sims).
  - RS2 at r 0.56 combined with the addendum C W70 weights on s66666 (2 sims).
  - The remaining idea_scout3 terminators: GABA_B-like slow inhibition (idea 3), and a mAHP/M-current-like faster adaptation if the build exposes it.

---
# Addendum B, step B1 (2026-11-24): 9 s cue spacing (PREREGISTRATION_B.md; 4 sims, all deleted, copies removed; `run_nr2.py`, `run_queue_b1.sh`, `analyze_b.py` -> `resultsB.md`)
Same A17 assemblies, LH weights and the same 27 cues, now 9,000 ms apart instead of 3,000 ms. Nothing else changed.

| model | arm | r | spacing | 75% | 50% | median last (ms) | stops100 | spikes/member | non-member events | residual sAHP at 50% cues (nS) | TERM | RECOVER |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s77777 | RS2 | 0.56 | 3 s | 6/6 | 2/6 | 25.5 | 9/9 | 4.9 | 2/27 | 0.62 | yes | yes (ref 2) |
| s77777 | RS2 | 0.56 | **9 s** | 6/6 | 2/6 | 25.2 | 9/9 | 4.8 | 1/27 | 0.00 | yes | yes (ref 2) |
| s66666 | RS2 | 0.56 | 3 s | 6/6 | 2/6 | 160 | 0/9 | 19.8 | 9/27 | 2.26 | no | no |
| s66666 | RS2 | 0.56 | **9 s** | 6/6 | **5/6** | 164 | 0/12 | 19.9 | 12/27 | 0.01 | no | yes (ref 5) |
| s77777 | RS3 | 1.0 | 3 s | 5/6 | 1/6 | 96 | 4/7 | 9.6 | 2/27 | 2.70 | no | no |
| s77777 | RS3 | 1.0 | **9 s** | 6/6 | **5/6** | 120 | 3/12 | 11.0 | 6/27 | 0.10 | no | yes (ref 6) |
| s66666 | RS3 | 1.0 | 3 s | 6/6 | 2/6 | 194 | 0/9 | 18.2 | 9/27 | 6.00 | no | no |
| s66666 | RS3 | 1.0 | **9 s** | 6/6 | **6/6** | 196 | 0/13 | 18.5 | 13/27 | 0.15 | no | yes (ref 5) |

25%-cue, single-cell and unrelated cues recruited no cell in any run. Contamination was 0.

**Answer to step 1.**
- **Yes, 50%-cue completion recovers once the leftover sAHP has decayed** (residual at most 0.15 nS; RECOVER in 4/4). This confirms the post hoc explanation.
- **But where it recovers, the events do not end within 100 ms** (median last 120-196 ms). The leftover sAHP at 3 s spacing had also been shortening the events: s77777 RS3 went 96 → 120 ms, stops100 4/7 → 3/12.
- The only run in which every event ends within 100 ms is s77777 RS2 r0.56. It does so at both spacings, with 50% completion 2/6, which is its LH baseline at r 0.56.
- So completing from 50% cues and ending within 100 ms never occur together, the same trade-off as the weaker-pair arms. This matches the knob-scout model (one threshold for both; no window).

**Predictions B1 scored.**
- B1a: residual <= 0.5 nS in all 4 runs: HIT (max 0.15).
- B1b: RECOVER in >= 3/4: HIT (4/4).
- B1c: median last longer at 9 s in >= 3/4: HIT (3/4; +2 ms, +2 ms and +24 ms; s77777 RS2 -0.3 ms). Only s77777 RS3 is a material change.
- B1d: TERM in >= 1 run: HIT; TERM on s77777 RS2 r0.56 again: HIT.
- B1e: PASS_T in any run (15%): MISS. None passes; s77777 RS2 r0.56 fails on 50% (2/6) and 1 event with non-member spikes.
- B1f: silence of 25%-cue, single-cell and unrelated cues: HIT.

**Best arm for B2** (preregistered rule: TERM models, then 50% completions, then non-member events): RS2 (1 TERM model vs 0) → **RS2**.

---
# Addendum B, step B2 (2026-11-24): pair strength set by the dominant eigenvalue (PREREGISTRATION_B.md; 6 sims, all deleted, copies removed)
**Design (knob-scout hypothesis, `../loopedwsp_scout/stability/README.md`, read only).**
- Member pairs of the LH matrix are rescaled above the 0.1·G floor, X = fl + k·(X_LH - fl), with k solved per model.
- The target is a dominant eigenvalue rho of the 17x17 member AMPA matrix of 16.0 or 16.5 nS.
- Resulting pair weights are 0.10-0.75 of G. The largest pair is 3.3-4.4 nS (cap 6.86).
- Input cap: s66666 has no member above 49.5 nS (max 47.7); s77777 has 1 (hub cell 3, 57.2 nS = its grown floor input, as in every arm).
- r 1.0, GABA x1, 9 s spacing.
- "Best arm from B1" = RS2 by the preregistered rule.

| model | design (rho, nS) | neuron | 75% | 50% | 25%, 1-cell, unrel recruit | median last (ms) | max last | stops100 | spikes/member | non-member events | 75%-design pass | PASS_T |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s77777 | E16 (16.0) | N0 | 3/6 | 0/6 | 0, 0, 0 | 6.2 | 8.1 | 4/4 | 1.0 | 0/27 | no (75% 3/6) | no |
| s77777 | E16.5 (16.5) | N0 | 4/6 | 0/6 | 0, 0, 0 | 7.7 | 9.0 | 5/5 | 1.0 | 0/27 | no (4/6) | no |
| s77777 | E16 | **RS2** | **6/6** | 0/6 | 0, 0, 0 | **13.8** | 16.6 | **7/7** | 2.7 | **0/27** | **PASS** | no (50% 0/6) |
| s66666 | E16 | N0 | 4/6 | 0/6 | 0, 0, 0 | 8.3 | 8.8 | 5/5 | 1.1 | 0/27 | no (4/6) | no |
| s66666 | E16.5 | N0 | 4/6 | 0/6 | 0, 0, 0 | 7.9 | 17.6 | 5/5 | 1.1 | 1/27 | no (4/6, 1 non-member event) | no |
| s66666 | E16 | RS2 | 6/6 | 0/6 | 0, 0, 0 | 190 | 202 | 0/7 | 17.6 | 7/27 | no (reverberates) | no |

References (stored, 3 s, N0, r1):
- W70 (rho 17.0 / 17.9): s77777 75% 5/6, ends; s66666 75% 5/6, reverberates.
- LH (rho 21.5 / 22.9): 75% 6/6, 50% 5-6/6, reverberates.

**Answer to step 2.**
- **The eigenvalue rule removes the reverberation on both models with the build's neurons.** At rho 16.0 and 16.5 every completing event ends within 6-18 ms, on s66666 too, where W70 reverberated. No non-member spikes appear (1 event at E16.5 s66666), and all silence criteria hold. So the per-model eigenvalue does remove the s77777/s66666 difference that the fixed 0.7 factor had.
- **But 75% completion is only 3-4 of 6 at rho 16-16.5,** below the preregistered >= 5/6. 50% cues never complete (0/6 everywhere). The completing level for 75% cues therefore sits slightly above 16.5 in these models, close to the ignition level: the window is narrow.
- **With the reset + sAHP x2 arm (RS2), s77777 meets the 75% design target:** 75% 6/6, events end within 14 ms, no non-member spikes, 25%/single/unrelated silent. This is the first run of the whole study to do so. **On s66666 the same arm ignites** (190 ms).
- **Mechanism (post hoc, `posthoc_cue_rebound.py`): the gain from RS2 comes from the reset acting on the forced cue cells, not from the sAHP.**
  - Under TOVM a cue cell forced to fire from rest resets to its pre-spike Vm (about -70 mV). Under AFTER it resets to -55 mV and fires again about 4 ms later.
  - Cue cells give 2.7 spikes per cell in 30 ms (s77777) and 7.0 (s66666), against exactly 1.0 with N0.
  - So RS2 turns a single-spike cue into a short burst. That is a stronger cue, which tips s77777 into completion and s66666 into ignition.
  - The same effect explains why R alone raised 50% completion on s66666 in the 3-s runs (5/6 → 6/6).
  - This is a property of the stimulation protocol (forced spikes from rest) interacting with the reset. It is not termination by adaptation. Whether a burst-like cue is the biological input (dentate gyrus/mossy-fibre bursts would be) is a question for Randal.

**Predictions B2 scored.**
- B2a: E16 N0 75% >= 4/6 in both: MISS (3/6 s77777, 4/6 s66666). TERM in both: HIT.
- B2b: E16 N0 50% <= 1/6 in both: HIT (0/6, 0/6).
- B2c: E16.5 N0 75% >= E16's in each model: HIT (4 >= 3, 4 >= 4). TERM in >= 1: HIT (both).
- B2d: RS2 lowers 75% completion: MISS (6/6 > 3/6 and 4/6). RS2 lowers median last: MISS (13.8 > 6.2; 190 > 8.3). Both are the opposite of what I predicted; see the mechanism above.
- B2e: a 75%-design pass in >= 1 run: HIT (s77777 E16 RS2).
- B2f: PASS_T in any run: MISS (50% 0/6 everywhere).
- B2g: the two models agree at E16 N0: HIT (both fail, both on 75% completion; both end).

B totals: B1 7 clauses, 6 HIT and 1 MISS. B2 10 clauses, 6 HIT and 4 MISS.

## Overall (steps 1-2), for John and Randal
1. **Reverberation is a loop-gain problem and can be removed by design.** Setting the member AMPA matrix to rho about 16 nS per model ends every event within about 10 ms on both models without any neuron change. The literature sAHP shortens the reverberation but does not end it, and the -55 mV reset does not affect it.
2. **The price is completion.** At gain levels that do not ignite, 75% cues complete 3-4 of 6 and 50% cues never complete. In every arm tested, 50% completion appears only together with ignition (the knob-scout prediction: one threshold, no window).
3. **One configuration meets the 75% design on one model:** s77777, rho 16.0, reset -55 + sAHP x2. It works because the reset makes the cue cells burst. It fails on s66666 (ignition), so it is not robust: the cue strength now matters as much as the weights.
4. Not tested and possible next steps (each needs John's go):
   - the reset alone (R) at rho 16.0, to separate the reset from the sAHP
   - rho 16.0 with a 2-spike cue protocol under N0, the clean version of the "burst cue" finding
   - a finer rho grid (16.7-17.2) for 75% completion at N0
   - a question to Randal: is a 50%-cue completion requirement compatible with a terminating assembly, or is ignition (a 100-200 ms burst) acceptable?

# Step C: 2-spike cue and finer rho grid (PREREGISTRATION_C.md, 8 sims, original neurons, r 1.0, GABA x1, 9 s spacing)
John approved options 2 and 3 together. Runner `run_nr3.py`, analysis `analyze_c.py`, table `resultsC.md`. All 8 runs completed and were deleted, and all model copies were removed. No rerun or restart was needed (max RSS 8.5 GB).

| model | rho | cue | 75% | 50% | 25%, 1-cell, unrel recruit | median / max last (ms) | stops100 | non-member events | TERM | PASS75 |
|---|---|---|---|---|---|---|---|---|---|---|
| s77777 | 16.0 (B2) | 1 spike | 3/6 | 0/6 | 0, 0, 0 | 6.2 / 8.1 | 4/4 | 0/27 | yes | no |
| s77777 | 16.5 (B2) | 1 | 4/6 | 0/6 | 0, 0, 0 | 7.7 / 9.0 | 5/5 | 0/27 | yes | no |
| s77777 | 16.7 | 1 | 4/6 | 0/6 | 0, 0, 0 | 7.4 / 9.8 | 5/5 | 0/27 | yes | no |
| s77777 | 16.9 | 1 | 5/6 | 0/6 | 0, 0, 0 | 7.7 / 11.0 | 6/6 | 0/27 | yes | **yes** |
| s77777 | 17.1 | 1 | 5/6 | 0/6 | 0, 0, 0 | 7.4 / 10.2 | 6/6 | 0/27 | yes | **yes** |
| s77777 | 16.0 | **2 spikes** | 6/6 | 4/6 | **2/6**, 0, 0 | 285 / 303 | 0/11 | 11/27 | no | no |
| s66666 | 16.0 (B2) | 1 | 4/6 | 0/6 | 0, 0, 0 | 8.3 / 8.8 | 5/5 | 0/27 | yes | no |
| s66666 | 16.5 (B2) | 1 | 4/6 | 0/6 | 0, 0, 0 | 7.9 / 17.6 | 5/5 | 1/27 | yes | no |
| s66666 | 16.7 | 1 | 4/6 | 0/6 | 0, 0, 0 | 10.9 / 315 | 4/5 | 1/27 | no | no |
| s66666 | 16.9 | 1 | 4/6 | 0/6 | 0, 0, 0 | 16.6 / 313 | 3/5 | 2/27 | no | no |
| s66666 | 17.1 | 1 | 4/6 | 0/6 | 0, 0, 0 | 301 / 314 | 1/5 | 4/27 | no | no |
| s66666 | 16.0 | **2 spikes** | 6/6 | 6/6 | **4/6**, 0, 0 | 298 / 314 | 0/13 | 13/27 | no | no |

The full cue completed 1/1 everywhere. There was no contamination. Input cap: s66666 has 0 members over 49.5 nS (max 47.9); s77777 has 1 (hub cell 3, 57.2 nS, from the grown graph, in every design). The largest pair is 3.3-4.6 nS, against the 6.86 cap.

## Answer to C1 (2-spike cue)
- The manipulation check passed: 100% of cue-cell instances fired 2 spikes in 8 ms.
- The second spike makes every completing cue ignite on both models: events last 270-310 ms, and every completing event has non-member spikes. s66666 recruits about 63 non-member spikes per event, so the whole network joins.
- 50% cues now complete (4/6, 6/6), but only by ignition, the same as every earlier 50% completion.
- **Silence breaks:** doubled 25% cues recruit a few cells in 2/6 (s77777) and 4/6 (s66666) events. These are small events (8-18 Pyr spikes, ending within 21 ms), not ignition. Single-cell and unrelated cues stay silent.
- So the burst explanation holds in the strong direction: cue strength matters as much as weights. But a uniform 2-spike cue overshoots both models. The B2 RS2 pass on s77777 (2.7 spikes per cue cell, with a -55 mV reset) sits between 1 and 2 forced spikes and is not reproduced by a clean doubled cue.

## Answer to C2 (rho grid)
- **s77777 has a passing range:** rho 16.9 and 17.1 give 75% 5/6, all events end within 11 ms, no non-member spikes, and silence holds (PASS75 at both). These are the first original-neuron passes in the study. 5/6 against 4/6 is one event, though, so the lower edge (16.7-16.9) is not sharp.
- **s66666 has none:** 75% completion stays at 4/6 from 16.0 to 17.1. Meanwhile ignition grows: 1 of 5 completing events ignite at 16.7, 2 at 16.9, 4 at 17.1. So s66666 reaches ignition before its 75% completion rises.
- **No window** (no rho with PASS75 on both models). The per-model eigenvalue does not equalise the two models near the threshold.
- Post hoc (labelled, not preregistered): the failing 75% events on s66666 are the same two cue subsets at every rho (rho 16.0-17.1). They miss members 28 (both events), 46 and 57. On s77777 the misses are members 65 and 70. So incompleteness comes from specific cells, not from the global gain. Uniform rescaling raises the gain of the cells that ignite as well as the cells that fail. A per-cell fix (raising input to cells 28/65 only) would be the next lever, but it is outside this preregistration.

**Predictions C scored** (16 clauses: 6 HIT, 10 MISS):
- C1a manipulation check passes: HIT.
- C1b 75% >= 5/6 both: HIT (6/6, 6/6).
- C1c 50% <= 1/6 both: MISS (4/6, 6/6).
- C1d TERM s77777: MISS. TERM s66666: MISS.
- C1e silence holds: MISS (25% recruit 2/6, 4/6).
- C1f PASS75 in >= 1 model: MISS. In both: MISS.
- C2a 75% non-decreasing in rho: HIT (s77777 3-4-4-5-5; s66666 flat 4).
- C2b >= 5/6 in both models: MISS (s66666 stays at 4/6).
- C2c TERM both at 16.7: MISS (s66666 4/5). TERM both at 17.1: MISS.
- C2d PASS75 in >= 1 grid run: HIT (s77777 16.9, 17.1). Window: MISS.
- C2e 50% <= 1/6 everywhere: HIT.
- C2f silence in the grid: HIT.

## Overall after step C
1. **Uniform gain (rho) gives a 75%-design pass on s77777 (rho 16.9-17.1, original neurons) but not on s66666.** On s66666 two cue subsets never complete before other events start to ignite.
2. **A stronger cue moves everything together:** completion (75% and 50%), ignition and 25% recruitment all rise. Within the cue and weight knobs tested, 50% completion has never come without ignition.
3. Possible next steps (not started; each needs John's go):
   - a per-cell input boost for the non-completing members (s66666 cells 28, 46, 57; s77777 cells 65, 70) at rho about 16.5
   - a cue between 1 and 2 spikes (e.g. a 2-spike cue on half the cue cells)
   - asking Randal whether model-specific completion failures of this kind are acceptable, or whether the design needs a per-cell rule

# Step D: per-cell input boost of the consistently failing members (PREREGISTRATION_D.md, 6 sims)
Original neurons, single-spike cue, 9 s spacing, r 1.0, GABA x1, base design E16.5. Boosted cells: s66666 28, 46, 57; s77777 65, 70. Runner `run_nr4.py`, analysis `analyze_d.py`, table `resultsD.md`. All 6 runs completed and were deleted, and all model copies were removed. No rerun or restart was needed (RSS at most 9.9 GB at a start).

| model | design | rho | 75% | 50% | 25%, 1-cell, unrel recruit | median / max last (ms) | stops100 | non-member events | boosted cells join 75% events (uncued) | TERM | PASS75 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| s66666 | base (B2) | 16.50 | 4/6 | 0/6 | 0, 0, 0 | 7.9 / 17.6 | 5/5 | 1/27 | 28: 0/2, 46: 1/2, 57: 1/2 | yes | no |
| s66666 | L1 hold | 16.50 | **6/6** | 0/6 | 0, 0, 0 | 7.4 / 8.8 | 7/7 | 0/27 | 2/2, 2/2, 2/2 | yes | **yes** |
| s66666 | L2 hold | 16.50 | **6/6** | 0/6 | 0, 0, 0 | 6.9 / 10.6 | 7/7 | 0/27 | 2/2, 2/2, 2/2 | yes | **yes** |
| s66666 | L1 free | 17.08 | 6/6 | 0/6 | 0, 0, 0 | 8.0 / 331 | 6/7 | 1/27 | 2/2, 2/2, 2/2 | no (1 ignition) | no |
| s77777 | base (B2) | 16.50 | 4/6 | 0/6 | 0, 0, 0 | 7.7 / 9.0 | 5/5 | 0/27 | 65: 0/1, 70: 1/2 | yes | no |
| s77777 | L1 hold | 16.50 | **6/6** | 1/6 | 0, 0, 0 | 6.2 / 9.9 | 8/8 | 0/27 | 1/1, 2/2 | yes | **yes** |
| s77777 | L2 hold | 16.50 | **6/6** | 1/6 | 0, 0, 0 | 6.1 / 10.2 | 8/8 | 0/27 | 1/1, 2/2 | yes | **yes** |
| s77777 | L1 free | 17.04 | 6/6 | 1/6 | 0, 0, 0 | 7.0 / 12.7 | 8/8 | 0/27 | 1/1, 2/2 | yes | yes |

The full cue completed 1/1 everywhere; there was no contamination.

The boosted cells joined 50% events (uncued) as follows. Every incomplete 50% event still misses other members as well.
- s66666 L1-hold: 28 0/4, 46 0/1, 57 2/4. L2-hold: 57 3/4.
- s77777: 65 1/3, 70 1/4 in every design.

**Input cap, stated plainly:**
- s66666: cell 28 is at 52.5 nS (L1) or 53.9 nS (L2), the only member over 49.5 nS.
- s77777: 3 members are over: hub cell 3 at 57.2 nS (unchanged), cell 65 at 51.5-54.0, cell 70 at 49.5-52.0.
- The largest pair is 4.4 nS (cap 6.86), and the largest weight is 0.87 of G. NMDA r 1.0, GABA x1.

## Answer to step D
- **The per-cell boost gives the first window: one design that meets the 75% target on both models.**
  - Both rho-held designs (L1 and L2, rho 16.5) give PASS75 on both models: 75% cues complete 6/6, every event ends within 11 ms, no non-member spikes, and all silence checks hold.
  - All previously failing cells now join every 75% event in which they are not cued. That is 2/2, 2/2, 2/2 on s66666 and 1/1, 2/2 on s77777, against 0-1 of 1-2 in the base run. The denominators are small (each cell is uncued in only 1-2 of the 6 events), but in the base run these same events were the incomplete ones.
- **L1 is enough:** L2 gave the same counts. Bringing the weakest members up to the mean in-assembly input was sufficient.
- **Holding rho matters on s66666:** with the boost alone (rho rising to 17.08), one 75% event ignited (331 ms, non-member spikes), so the pass was lost. s77777 passed at 17.04 too.
  - So the design rule that worked is "equalise the in-assembly input of the weak members, then rescale the whole member matrix to rho 16.5".
- **50% cues still do not complete** (0/6 on s66666, 1/6 on s77777), so PASS_T fails everywhere. The 50% clause remains unmet without ignition.
- **Caveats:**
  - Each run has one random ordering of 6 cues per kind, on 2 models.
  - The failing cells were chosen from the B2/C runs that used the same cue subsets, so this is not a held-out test. New cue subsets would be the next check.
  - The boosted cells go over the 49.5 nS total-input cap (s66666 one cell; s77777 two cells besides the hub), because their non-member input was left unchanged.

**Predictions D scored** (13 testable clauses, 13 HIT; D8 not testable):
- D1 boosted cells join more often than in the base, L1-hold both: HIT. L2-hold both: HIT.
- D2 75% >= 5/6 both, L1-hold: HIT. L2-hold: HIT.
- D3 TERM both, L1-hold: HIT. L2-hold: HIT.
- D4 window: HIT. PASS75 on s66666 in any run: HIT.
- D5 L1-free s66666 does not TERM: HIT (1 ignited event).
- D6 50% <= 1/6 everywhere: HIT.
- D7 silence everywhere: HIT.
- D8 new weakest link where 75% < 6/6: not testable (every run is 6/6).

My confidences ranged from 35% to 85%, so 13/13 is better than I expected. I flag that rather than read it as calibration.

## Possible next steps (not started; each needs John's go)
1. A held-out check: the same L1-hold design with a new set of 27 cue subsets (different seed), on both models, 2 sims. This tests whether the fix is general or tuned to the subsets that defined the failing cells.
2. Make the rule cap-compliant: lower the non-member input of the boosted cells so their total stays <= 49.5 nS, then re-run L1-hold (2 sims).
3. Make the rule a priori: boost every member below mean - 1 SD, chosen from the matrix alone and not from failures; this would include s77777 hub cell 3 and s66666 cell 65 (2 sims).
4. 50% cues: still ask Randal whether 75% completion with fast termination is the acceptable target, given that 50% completion has only ever appeared together with ignition.

# Step E: held-out cues and a pre-fixed boost rule (PREREGISTRATION_E.md, 4 sims)
New cue subsets (key `E1111-`, chosen by the preregistered coverage rule; 0 repeated subsets), shared by both arms. L1 boost, rho held at 16.5, original neurons, single-spike cue, 9 s spacing, r 1.0, GABA x1. Runner `run_nr5.py`, analysis `analyze_e.py`, table `resultsE.md`. All 4 runs completed and were deleted, and all model copies were removed. The separate build was restarted once before the first run (new NES 2768884 / API 2769516).

| model | arm | boosted cells | 75% | 50% | 25%, 1-cell, unrel recruit | median / max last (ms) | stops100 | non-member events | boosted cells join 75% events (uncued) | missing in failed 75% events | members > 49.5 nS (max) | PASS75 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| s66666 | D (step-D cells) | 28, 46, 57 | **6/6** | 0/6 | 0, 0, 0 | 7.8 / 9.8 | 7/7 | 0/27 | 2/2, 2/2, 2/2 | - | 1 (52.5) | **yes** |
| s66666 | P (mean - 1 SD) | 28, 57, 65 | **5/6** | 0/6 | 0, 0, 0 | 7.0 / 8.4 | 6/6 | 0/27 | 2/2, 2/2, 3/3 | 46, 77, 79 | 1 (52.6) | **yes** |
| s77777 | D (step-D cells) | 65, 70 | 4/6 | 1/6 | 0, 0, 0 | 7.0 / 10.6 | 6/6 | 0/27 | 2/2, 2/2 | 3; 3, 4, 46 | 3 (57.2) | no |
| s77777 | P (mean - 1 SD) | 3, 65, 70 | **5/6** | 0/6 | 0, 0, 0 | 5.9 / 9.1 | 6/6 | 0/27 | 2/2, 2/2, 2/2 | 4, 46 | 2 (64.2) | **yes** |

Every event in every run ends within 11 ms. The full cue completed 1/1 everywhere, and there was no contamination. The largest pair is 4.2 nS (cap 6.86); NMDA r 1.0, GABA x1.

## Answer to step E
- **Held-out check (1): partial.**
  - The step-D design generalises on s66666: 6/6 on new cues, with every boosted cell joining.
  - It fails on s77777 (4/6). Both incomplete events miss **hub cell 3**, which was never uncued in a failing step-D/C event on the old cues, so it was not on the failure list.
  - The boost itself held up: cells 65 and 70 joined 2/2 each. A weak member that the old cues happened not to expose became the weak link.
- **Pre-fixed rule (3): works on both models (PASS75), but only at the threshold (5/6 each).**
  - It boosts the members below mean - 1 SD of in-assembly input, selected from the matrix alone. That includes hub cell 3, which the failure-based list missed, and it fixes s77777.
  - On s66666 the rule leaves out cell 46. The single failed event misses 46 (with 77, 79), as preregistered (E4). So the 1 SD threshold is slightly too strict for s66666.
- **Reading:** completion of 75% cues is limited by the members with the least in-assembly input. Ranking the members by that input predicts the failing cells better than a list of observed failures, because the failure list depends on which cues happened to be drawn.
  - The natural next rule is "boost every member below the mean" (or below mean - 0.5 SD). It would cover cell 46, and is untested.
- **Unchanged:** 50% cues complete 0-1/6, so PASS_T fails everywhere. Silence held in all runs.
- **Input cap, stated plainly:** P puts the s77777 hub cell at 64.2 nS total input (30% over 49.5 nS) and s66666 cell 28 at 52.6 nS. D also puts 2 s77777 cells over (51.5, 49.54). None of the passes satisfies the input cap on s77777.
- **Caveat:** 5/6 vs 4/6 is one event out of 6, and there is no unboosted run on these cues (preregistered limitation).

**Predictions E scored** (11 clauses: 9 HIT, 2 MISS):
- E1 D PASS75 s77777: MISS. s66666: HIT. Both: MISS.
- E2 P PASS75 s77777: HIT. s66666: HIT. Both: HIT.
- E3 D boosted cells join >= 75% of uncued 75% events: HIT (6/6, 4/4).
- E4 P s66666 failure misses cell 46: HIT.
- E5 50% <= 1/6 in all runs: HIT.
- E6 silence in all runs: HIT.
- E7 a missing member was not boosted in that arm, wherever 75% < 6/6: HIT (3; 46; 4 and 46).

## Possible next steps (not started; each needs John's go)
1. Rule "boost every member below the mean in-assembly input", rho held at 16.5. Use the same E1111 cues plus one more new cue set, both models (4 sims). This tests whether a rule with no free threshold gives 6/6.
2. A cap-compliant version: lower the non-member input of the boosted cells so their total stays <= 49.5 nS. This matters most for s77777 hub cell 3, which is 64.2 nS under P.
3. An unboosted base run on the E1111 cues (2 sims), so the boost's effect on these cues can be measured, not only the absolute criteria.
