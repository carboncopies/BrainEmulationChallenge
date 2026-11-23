# gaba_vm: does late GABA silence reverberation and discard a too-early second pattern in an E4 model? (2026-11-22)
Context: Randal's reply (thread 1a1ce43946326354) says late GABA is fine; in his view it should silence the network AFTER a pattern fires, to stop reverberation and to space successive patterns (theta later). He offered to inspect Vm traces and named the knobs AHP, ADP, max AMPA, NMDA and lateral inhibition.
Model: E4, V1n20 seed 33333 (headline_i; passes all 7 bars). Three disjoint 6-cell memories (design D42; 4 cue + 2 non-cue cells each). R3 recipe programming, Dt 0.1 ms, precise spike times, STDP off. PREREGISTRATION.md was written before any simulation and has not been edited. Scripts: run_vm.py (one simulation), modelfile.py (model-file reader/patcher), run_queue.sh, analyze.py -> summary.json / analyze.log, figs.py -> fig_*.png. Raw data: raw_*.json, vm_*.npz, log_*.txt. The API section is in API_NEEDS.md.

## Short answer for Randal
1. **Yes, the build's own GABA (x1) silences reverberation, but only where there is reverberation to silence.** A single recall at background c 0 or 1.5 nS does not reverberate even with GABA silenced: each member fires once and the last pyramidal spike comes at 4.8-5.1 ms. Reverberation appears when the drive is larger:
   - **Two memories cued 5 ms apart, c 1.5:** with GABA silenced there are 331-350 late pyramidal spikes per event (about 140 interneuron spikes), and the network is then unresponsive for the next 0.5-1 s. With GABA x1 there are 0-4 per event; with x2 and x5, 0.
   - **Single recall at c 3.0:** with GABA silenced, 51 late member + 328 non-member spikes, last spike at 51 ms. With x1: 2 non-member spikes, last at 10.9 ms; x2: 9.6 ms; x5: 7.7 ms.
   - **With NMDA kept (NMDA/AMPA 0.56, the build's own per-synapse ratio):** double cues with GABA silenced give 1,124-1,422 late spikes per event; x1 gives 3-15. At NMDA/AMPA 1.0, x1 no longer contains it (about 1,450 late spikes in 3 of 6 double-cue events); x5 does (0).
   - Figures: fig_runaway_d5.png, fig_late_c3.0.png, fig_late_nmda*.png.
2. **Discarding a second cue: yes at c 0, within a short window. With background excitation (c 1.5), mostly no.**
   - **c 0, 6 memory pairs per delay:** discards at delays 5 / 10 / 20 / 50 ms are
     - x1: 3 / 4 / 0 / 0
     - x2: 6 / 6 / 0 / 0
     - x5: 6 / 6 / 0 / 0
     - silenced: 0 / 0 / 0 / 0

     So the window closes between 10 and 20 ms after the first cue. That matches GABA decay (10 ms) plus the time the first memory's interneurons take to fire (6.5-7 ms).
   - **c 1.5:** x1 and x2 discard nothing at any delay; x5 discards 3 of 6 at 10 ms only. Here the first pattern's background excitation primes the second memory, which then fires earlier, not later (non-cue latency about 3.0 ms instead of 5.1 ms at 5-20 ms delays). Excitation outweighs the GABA.
   - Figures: fig_discard_G1toG0_d5_c0.png (Vm of a discard: the second memory's non-cue cells reach -51 mV and 8-17 nS of GABA holds them under threshold), fig_twocue_d10_c*.png.
3. **Early GABA kills recall; late GABA does not.** The lateral-inhibition knob (no cap on cue-to-interneuron drive, Pyr->Int AMPA x2) makes interneurons fire at 2.0-2.3 ms, before the non-cue members at about 4.8 ms. With GABA on, the memory itself is then vetoed: at x1, G0 fails when cued alone; at x5, all three fail. With GABA silenced, all three recall. This is gaba_check_l's veto window (GABA must arrive within about 3 ms) seen from the other side. Late, feedback GABA, as the build produces it, leaves recall intact and acts afterwards, as Randal describes. Figure: fig_recall_lateral.png.
4. **What contains reverberation when GABA is silenced:** AHP matters, ADP does not.
   - Double cues at c 1.5 with GABA silenced: AHP x0 gives 860-916 late spikes per event; the default AHP gives 331-350; AHP x2 gives 213-222 in two pairs and 2-12 in the other four. With GABA x1, every AHP setting gives 0-14 in total.
   - ADP x0 or x3 changes nothing measurable (2,039 / 2,237 against 2,050 total).
   - Max AMPA x1.25 (all programmed Pyr->Pyr): no reverberation in single recalls; double-cue numbers as at x1 (2,037 with silenced, 10 with x1).
5. **A model detail Randal may want to check in the traces:** after a spike, a recruited cell resets to its pre-spike Vm (ResetMethod TOVM), which is the -50 mV threshold. It is held off only by the 2 ms refractory period, the adaptive threshold and the AHP. In a runaway, a cell with GABA silenced therefore fires at about 300 Hz (fig_late_c3.0.png, cell 83). Cue cells forced from rest reset to -70 mV. Also, E_GABA = Vrest = -70 mV, so the GABA current is exactly zero at rest; it only acts on a depolarised cell (bottom panel of each recall figure).

## Figures (PNG, 120-130 dpi, made for Randal)
| file | what it shows |
|---|---|
| fig_recall_c0.png, fig_recall_c1.5.png, fig_recall_c3.0.png | one recall of G0. Raster; Vm of 2 cue cells, the 2 non-cue members and the interneurons that fired; reconstructed g_GABA and I_GABA on the non-cue cells. Overlays: GABA silenced (grey), x1 (blue), x5 (red) |
| fig_twocue_d10_c*.png | G0 cue, then G1 cue 10 ms later (the first such event in the run, at 520 ms; at c 0 x1 G1 is delayed by 0.35 ms but not discarded) |
| fig_discard_G1toG0_d5_c0.png | a discard with x1 at c 0: G1 at 0 ms, G0 at 5 ms; G0's non-cue cells fire with GABA silenced (grey) and not with x1 (blue). From a figure-only rerun that recorded Vm over the whole run (see Provenance) |
| fig_runaway_d5.png | rasters, two memories cued 5 ms apart, 0-150 ms: c 1.5 silenced / x1 / x5, NMDA 0.56, NMDA 1.0 |
| fig_late_c3.0.png, fig_late_nmda056.png, fig_late_nmda100.png | single recall rasters (silenced / x1 / x5) and Vm of the most active non-member cell |
| fig_recall_lateral.png | lateral-inhibition knob: interneurons at about 2 ms veto the non-cue members |
g_GABA is reconstructed offline: interneuron spike times x loaded connectome pair conductance (weight x GPeakSum), with the simulator's kernel (rise 0.5, decay 10 ms, peak-normalised, onset delay 1.0 ms; Receptor.cpp `g_norm`). NES records Vm only. I_GABA = g_GABA x (Vm + 70).

## Results table (c in nS; late = spikes 15-450 ms after onset; "2-cue late" = non-member + late member spikes summed over the six 5 ms double-cue events)
| run | single recalls complete | single-recall late / non-member spikes | last pyr spike, G0 (ms) | discards d5/10/20/50 (preregistered definition) | same, events where the first memory completed | 2-cue late spikes at d5 |
|---|---|---|---|---|---|---|
| c0 silenced | 3/3 | 0 / 0 | 4.8 | 0/0/0/0 | 0/0/0/0 of 6/6/6/6 | 0 |
| c0 x1 | 3/3 | 0 / 0 | 4.8 | 3/4/0/0 | same | 0 |
| c0 x2 | 3/3 | 0 / 0 | 4.8 | 6/6/0/0 | same | 0 |
| c0 x5 | 3/3 | 0 / 0 | 4.8 | 6/6/0/0 | same | 0 |
| c1.5 silenced | 3/3 | 0 / 0 | 4.8 | 0/6/0/0 | 0/0/0/0 of 6/0/0/6 | 2,050 |
| c1.5 x1 | 3/3 | 0 / 0 | 4.8 | 0/0/0/0 | same | 5 |
| c1.5 x2 | 3/3 | 0 / 0 | 4.8 | 0/0/0/0 | same | 0 |
| c1.5 x5 | 3/3 | 0 / 0 | 4.8 | 0/3/0/0 | same | 0 |
| c3.0 silenced | 2/3 | 51 / 328 | 51.0 | 0/4/0/2 | 0/0/0/2 of 6/0/0/6 | 2,214 |
| c3.0 x1 | 2/3 | 0 / 2 | 10.9 | 0/0/0/2 | 0/0/0/2 of 6/0/5/6 | 1,184 |
| c3.0 x2 | 3/3 | 0 / 2 | 9.6 | 0/0/0/1 | of 6/0/6/6 | 515 |
| c3.0 x5 | 3/3 | 0 / 1 | 7.7 | 0/1/4/1 | same | 96 |
| NMDA 0.56, silenced / x1 / x5 | 1/3, 3/3, 3/3 | 0 / 0 all | 8.1 / 7.6 / 4.6 | 0/2/2/0, 0/0/0/0, 0/2/0/0 | silenced: of 6/1/1/2 | 6,655 / 42 / 0 |
| NMDA 1.0, silenced / x1 / x5 | 2/3, 3/3, 3/3 | silenced 2 / 27 (G1, last 75.6 ms); others 0 | 7.4 / 7.4 / 7.5 | 1/2/1/3, 0/3/3/0, 0/1/0/0 | silenced 4/4/4/0, x1 6/6/3/3 | 743 (6,300 at d10) / 4,381 / 0 |
| AHP x0, silenced / x1 / x5 | 1/3, 3/3, 3/3 | 0 | 8.0 / 8.0 / 4.8 | 0/2/0/0, 0, 0/3/0/0 | silenced 6/0/0/6 | 5,316 / 14 / 0 |
| AHP x2, silenced / x1 / x5 | 3/3 all | 0 | 4.8 | 0/2/0/0, 0, 1/4/1/0 | | 462 / 4 / 0 |
| ADP x0, silenced / x1 / x5 | 3/3 all | 0 | 4.8 | 0/6/0/0, 0, 0/3/0/0 | silenced 6/0/0/6 | 2,039 / 4 / 0 |
| ADP x3, silenced / x1 / x5 | 3/3 all | 0 | 4.8 | 0/6/0/0, 0, 0/3/0/0 | silenced 6/0/0/6 | 2,237 / 6 / 0 |
| AMPA x1.25, silenced / x1 / x5 | 2/3, 3/3, 3/3 | 0 | 6.7 | 0, 0, 0/1/0/0 | | 2,037 / 10 / 0 |
| lateral, silenced / x1 / x5 | 3/3, 2/3, 0/3 | 0 | 4.8 / 5.0 / 1.5 (cue only) | 0/6/0/0, 0/4/3/0, 0 | x1 5/0/3/1, x5 0/0/0/0 | 2,050 / 0 / 0 |
All knob runs at c 1.5. Interneurons: 2-3 fire per single recall with the defaults, first at 6.5-7.1 ms; with the lateral knob, 4-6 fire, first at 2.0-2.3 ms.

## Important caveat: carry-over between events (found after the first results)
- **What happened:** events were 500 ms apart. Whenever an event ran away (GABA silenced, or NMDA 1.0), the network was unresponsive in the next 1-2 events: even the first memory's non-cue cells did not fire. The likely cause is adaptive-threshold-floor build-up (+1 mV per spike, 500 ms recovery) plus the slow AHP; this was not isolated.
- **How it affects the counts:** the preregistered "discard" counts those dead events as discards (e.g. c 1.5 silenced: 6 at 10 ms). So the table also gives a count restricted to events in which the first memory completed. That second count was added after seeing the data and is not preregistered.
- **Other consequences:**
  - Some "single recall fails" entries (c 3.0 silenced/x1 G1; NMDA 0.56 silenced; AHP x0 silenced; AMPA x1.25 silenced) follow a runaway in the e1 double cue at 520 ms.
  - NMDA 1.0 x1 alternates between runaway and quiet events for the same reason.
  - At c 0 x1, the same pair and delay (G0>G1, 10 ms) was not discarded at 520 ms but was discarded later in the run. The outcome is on a knife edge and depends on recent history.

## Preregistration scoring (HIT / PARTIAL / MISS)
| # | prediction | observed | score |
|---|---|---|---|
| 1 | V0: file = API programming (95%) | 512 spikes, max difference 0.0005 ms, Vm 0.00002 mV | HIT |
| 2 | c 0 / 1.5 single recalls: no reverberation, every GABA condition equal (85% / 80%) | each member fires once, last spike 4.8-5.1 ms, 0 late spikes; latencies within 0.27 ms across conditions | HIT |
| 3 | c 3.0: silenced > 10 late spikes (75%); falls with GABA (70%); x5 not 0 (60%) | 379 / x1 2 / x5 1 | HIT, HIT, HIT only technically (1 spike) |
| 4 | x1 discards: none at 20/50 (90%); at 5 ms only pairs ending on G0; at most 1 of 6 at 10 ms (75%) | c 0: 3/4/0/0, and the 5 ms discards include G0>G1; c 1.5: 0; c 3.0: 2 at 50 ms (also with GABA silenced, carry-over) | 20/50: HIT at c 0 and 1.5, MISS at c 3.0; 5 and 10 ms: MISS (x1 is stronger at c 0 than I predicted) |
| 5 | x2: 2-4 at 5 ms, 0-2 at 10, none at 20/50 (60%) | c 0: 6/6/0/0; c 1.5: 0/0/0/0 | MISS (depends on c: all at c 0, none at c 1.5) |
| 6 | x5: at least 5 at 5 ms (70%), 2-5 at 10 (60%), 0-2 at 20 (70%), none at 50 (90%) | c 0: 6/6/0/0; c 1.5: 0/3/0/0; c 3.0: 0/1/4/1 | mixed: 5 ms HIT only at c 0; 10 ms HIT at c 1.5; 20 ms HIT at c 0/1.5; 50 ms HIT at c 0/1.5 |
| 7 | silenced: no discards (90%) | c 0: 0; c 1.5 and c 3.0: 6 and 6 by the preregistered definition, all in unresponsive events after a runaway | MISS by definition (0 in the events where the first memory completed) |
| 8a | AHP/ADP change no single-recall outcome (70%) | with GABA on: none changed; AHP x0 silenced: 2 recalls fail (carry-over) | PARTIAL |
| 8b | AHP/ADP change discards by at most 1 per delay (65%) | at most 1 per delay (AHP x2 x5: 1/4/1/0 vs 0/3/0/0) | HIT |
| 8c | NMDA adds reverberation in at least 1 of 3 single recalls (0.56: 45%, 1.0: 60%); x5 reduces it | 0.56: no; 1.0: yes with GABA silenced (G1, 29 spikes), x5 0. In double cues NMDA multiplies the runaway (6,655) | 0.56 MISS, 1.0 HIT, x5 HIT |
| 8d | AMPA x1.25: no reverberation (65%) | none | HIT |
| 8e | lateral: more than 3 interneurons (70%), more discards (60%) | 4-6 HIT; discards not measurable because the recall itself is vetoed (G0 at x1, all at x5) | HIT / MISS (other mechanism) |
| 9 | late GABA works only within about 10 ms and for some pairs; reverberation-silencing untestable at c 1.5 without NMDA (70%) | window 10-20 ms at c 0 (most pairs at x1, all at x2/x5), none at c 1.5; reverberation does occur at c 1.5 with two overlapping cues and is stopped by x1 | MISS (I underrated both how much x1 GABA does and how much c and double cues matter) |
What I got wrong: I expected x1 GABA to be too weak to discard and nothing to reverberate at c 1.5. In fact x1 discards at c 0 within 10 ms, and its main visible role is stopping the runaway that overlapping patterns start. Background excitation (c) decides whether a too-early second pattern is suppressed or facilitated.

## Bio status of the settings
- **GABA strength:** Int->Pyr pairs in this model at x1 have mean 0.70 nS, median 0.48, p90 1.60, max 5.12 (1.9% above 3 nS), close to the mean unitary PV->PC conductance used in gaba_patch (Ecker, 0.65 nS). x2 (mean 1.39) is above that mean; **x5 (mean 3.48, 41% of pairs above 3 nS) is outside the natural range and is diagnostic only.**
- **Other knobs:** bio_ranges.json has no entry for receptor strength, AHP, ADP or NMDA, so for those only the factor is stated.
  - NMDA/AMPA 0.56 is the build's own per-synapse ratio (0.55/0.98 nS). 120 NMDA receptors in pairs where the requested NMDA exceeded the pair's NMDA peak were capped by the simulator (g <= g_peak_sum).
  - Lateral knob: Pyr->Int AMPA mean 3.33 nS per pair (recipe weight 1) doubled to about 6.7 nS. That is not checked against the literature, so treat it as a diagnostic.

## Provenance and run facts
- **Instance:** separate build only (NES 8011 / API 8010); main NES 3156209 / API 1972355 untouched; no NES code change, no git, no email.
- **Shared instance:** it had just been started (21:23) by the other worker in ../ (growth arms, their run_grow.sh, max 2 growth processes). I did not restart, pin or stop it.
  - My own start attempt failed on the busy ports. Because it redirected output, it truncated `linefix-instance/nes.log` and `api.log`; their processes keep writing to those files, but the first lines of their logs are lost. Sorry.
  - I could not pin NES to 4 cores (their NES was already running unpinned). Instead I ran strictly 1 simulation at a time; a LIFC simulation runs in one engine thread.
  - The instance is still up and in use by their growth queue, so I have **not** stopped it.
- **Simulations:** 39 in total, one at a time, 21:28-23:05, about 86 min of wall time; every simulation was deleted and every model copy (gvm-*) was removed (0 left).
  - 37 preregistered.
  - 2 figure-only reruns, added after the first results: F_sg_c0 (Vm to 10.7 s) and F2_x1_c0 (Vm to 6.1 s). Both are identical to A_sg_c0 / A_x1_c0 (max spike difference 0.0 ms).
  - F_x1_c0 failed twice at `GetRecording` with HTTP 204 when 10.7 s of Vm (116 cells, 0.1 ms) was requested; the same request for the silenced run worked. At 6.1 s it worked. Cause not investigated (probably response size); logs kept as log_F_x1_c0_attempt*_failed.txt.
- **File route:** the model files were programmed by editing copies (modelfile.py). V0 shows it equals the API route.

## Honest limits
One model (s33333), one design (3 disjoint 6-cell memories), forced cue spikes, one deterministic simulation per condition, events 500 ms apart (carry-over, above). "Discard" is judged on 2 non-cue cells. g_GABA in the figures is reconstructed, not recorded. The windows (10-20 ms) depend on this build's GABA kinetics (decay 10 ms; Ecker's PV->PC is 3.3 ms) and on interneuron latency. I did not test delays between 10 and 20 ms, theta-like spacing, other seeds, or STDP.
