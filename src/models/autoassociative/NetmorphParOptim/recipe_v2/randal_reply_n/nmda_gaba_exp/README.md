# nmda_gaba_exp: recall with NMDA on (set through the patched API), GABA off / x1 / x2 / x5 (2026-11-23)
E4 models s33333, s66666, s77777 (3, 3 and 4 disjoint 6-cell memories, 4 cue + 2 non-cue). Patched separate build only (NES 8011 / API 8010, per-type `Neurotransmitter` argument; AMPA programmed first with the legacy call, then NMDA, then GABA). Main NES 3156209 / API 1972355 untouched; no model-file edits, no emails, no git. 263 preregistered simulations + 12 post hoc checks, max 3 at a time, Dt 0.1 ms; every simulation deleted (one delete failed after a load error, see Deviations 7; it went with the next NES restart).
Files: PREREGISTRATION.md (written before any run, unedited), DEVIATIONS.md (7 items), run_exp.py, run_queue.sh, run_queue_x.sh, analyze.py -> events.json, programs.json, score.py -> tables.txt, scoring.json, figs.py + summary_figs.py -> fig_*.png, raw_*.json, vm_*.npz, xcheck/ (post hoc X runs).

## Short answer
1. **NMDA can now be switched on through the API, and it reproduces the old runs exactly when off.** P0: r = 0 through the new route gives the same spikes as the stored gaba_vm runs (0.0 ms difference). But **NMDA is capped at the grown NMDA peak of each pair** (0.55 nS per synapse vs 0.98 AMPA): nominal r 0.56 gives achieved 0.55-0.56 on cue->non-cue pairs and 0.43-0.53 on the loops; **nominal r 1.0 gives only 0.73-0.78 on cue->non-cue and 0.43-0.61 on loops**. So "r 1.0" as run is not above the biological range; the API cannot go higher (needs a peak-conductance edit, API_NEEDS item 3). **Pyr->Int pairs have no NMDA receptors in these models**, so interneurons never get NMDA.
2. **A single full-cue recall is untouched by NMDA at c <= 1.5 nS:** 100% completion, no reverberation, for every r and every GABA level (also with GABA off). NMDA shortens the non-cue latency slightly (median 4.80 -> 4.64 -> 4.54 ms for r 0 / 0.56 / 1.0 at c 0).
3. **With NMDA on, the build's GABA (x1) no longer stops reverberation when the drive is strong.** Full-cue events that reverberate at c = 3.0 (late member spikes > 0, 10 memories):

   | | GABA off | x1 | x2 | x5 (non-bio) |
   |---|---|---|---|---|
   | r 0 (old) | 8/10 | 2/10 | 1/10 | 0/10 |
   | r 0.56 | 10/10 | **10/10** | 5/10 | 1/10 |
   | r 1.0 (achieved ~0.75) | 10/10 | **10/10** | 9/10 | 3/10 |

   The same holds for two memories cued 5 ms apart at c 1.5: runaway in 24/24 pairs with GABA off at every r, x1 contains it at r 0 (2/24) but not fully at r 0.56 (6/24) or r 1.0 (13/24); x2 brings it to 0-3/24, x5 to 0. Figure: fig_full_c3_r0.56.png (x1 trace keeps firing for >150 ms despite 40-110 nS of GABA on the non-cue cells; NMDA reaches ~120 nS).
4. **Partial cues (Randal's partial completion):**
   - 2 of 4 cue cells (50% missing): never complete (0 of 2,880 events over all c, r, GABA).
   - 3 of 4 (25% missing): never complete at r 0 or r 0.56 at c <= 1.5 (0 of 960); at c 3.0, 13 of 320 complete, all in conditions with runaway background activity. **At r 1.0 they complete, but on a knife edge:** in the preregistered runs exactly half (240/480) completed, always the 2nd and 4th 3-cell event of a memory. The cause is history, not which cell is missing: the adaptive threshold floor (+1 mV per spike, 500 ms recovery) is still ~0.2 mV up 800 ms after the non-cue cells last fired, and the partial-cue depolarisation peaks at about -50.1 mV (fig_3cell_c1.5_r1.png shows Vm 0.3 mV under the reconstructed threshold). Post hoc check with 3 s between cues (xcheck/): r 1.0 completes 40/40, r 0.56 0/40, at c 0 and 1.5.
   - **GABA does not gate partial completion at all:** identical counts for off/x1/x2/x5 at every c <= 1.5. Interneurons fire only after the non-cue cells: in a completed 3-cell event the non-cue cells fire at ~7.0 ms and the first interneuron at ~9.0-9.7 ms, and in a failed one no interneuron fires at all. GABA therefore arrives after the decision. Only at c 3.0 does GABA change the counts, and there x5 increases them (less runaway carry-over).
5. **Overlap / cross-trigger (F2 designs, overlap <= 2): NMDA increases cross-completion; GABA does not change it.** Full cues that also fully complete another memory, c = 0: r 0 18/52 (35%), r 0.56 26/52 (50%), r 1.0 29/52 (56%); GABA off 19/27/30 of 52. c = 1.5: 44/52 -> 47/52 -> 48/48 (x1). With NMDA at r 1.0, half of the 3-cell cues also complete in the overlap designs (52/104 silent). Own completion stays 100% except where runaway carry-over contaminates (c 1.5, GABA off, r >= 0.56).
6. **Second-cue discard (fig_summary_discard.png):** the GABA window is 5-10 ms, never theta-scale.
   - c 0, x1: discards 71% / 54% (r 0), 54% / 46% (r 0.56), 50% / 21% (r 1.0) of valid pairs at 5 / 10 ms; 0% at 20, 50, 100 ms. NMDA shortens the window slightly. x2: 83-100% / 63-79% at 5 / 10 ms, 0-4% at 20. x5: 100% at 5 and 10 ms, 0-33% at 20 ms. GABA off: 0%.
   - c 1.5: x1 and x2 discard almost nothing (0-21%) at any r; x5 discards 42-75% at 10 ms only. Background excitation outweighs GABA, as in gaba_vm.
   - Discard window W (largest delay with >= 50% discard) is 0-10 ms in all 24 conditions.
7. **Pacing (fig_summary_trains.png): GABA does not impose a regular recall interval; the adaptive threshold does, and NMDA removes it.** Same memory cued 5 times:
   - NMDA off (r 0), c 0: only 3.0 of 5 recalls complete even at 100 ms intervals, 2.0 at 50 ms, identical for every GABA level. Completions alternate (yes/no/yes...) because each recall raises the non-cue threshold floor for hundreds of ms. This is a refractoriness of the memory cells, not of the network, and it is set by the neuron's adaptive threshold, not GABA.
   - NMDA on, c 0: 4.9-5.0 of 5 at 50-100 ms for every GABA level; at 10-20 ms GABA removes some recalls (r 0.56: off 5.0 / 4.2, x1 4.0 / 3.9, x5 2.8 / 3.2).
   - The intervals between completed recalls equal the cue interval: the rhythm comes from the input; nothing in the network produces a theta-like period (GABA decays in 10 ms; the slowest network variable here is the 500 ms threshold floor).

## Preregistered predictions
| | result | numbers |
|---|---|---|
| P0 new route = old runs at r 0 | **PASS** | 0.0 ms difference, same cells, c 0 and 1.5 |
| P1 full cues complete (c <= 1.5) | **PASS** | 100% for every r and GABA level (incl. x5) |
| P2 no reverberation with x1 at c <= 1.5; some with GABA off at r 1.0, c 1.5 | **FAIL** | first half holds (0 reverberating events); second half fails: no single full cue reverberates even with GABA off at r 1.0, c 1.5 |
| P3 c 3.0: runaway with GABA off; x1 cuts >= 90% | **FAIL** | runaway in all 3 seeds, but x1 cuts late spikes by only 9% (r 0.56) and -4% (r 1.0) |
| P4 3-cell silence (r 0: 100%; r 0.56 >= 90%; r 1.0 some but < 50%) | **FAIL** (boundary) | r 0 and r 0.56: 100% silent; r 1.0: completion in all 3 seeds but exactly 50% (240/480), not < 50%, and history-driven (see 4) |
| P5 2-cell cues never complete | **PASS** | 0 completions anywhere |
| P6 GABA reduces partial completion | **FAIL** | no effect at c <= 1.5 (20/20/20 completions off/x1/x5 per c); at c 3.0 x5 gives more (16 vs 6) |
| P7 NMDA raises cross-completion by >= 5 points at c 0 | **PASS** | 35% -> 50% -> 56%; GABA off vs on at r 0 differ by 2 points |
| P8 discard at c 0 (x1 >= 25% at 5 and 10 ms, <= 10% later; x2/x5 >= 75% at 5 and 10 ms; off 0%) | **FAIL** | 3 of 12 conditions miss: r 1.0 x1 at 10 ms 21%; x2 at 10 ms 67% (r 0.56) and 63% (r 1.0). Others hold, and nothing is discarded at >= 20 ms except x5 (non-bio) |
| P9 c 1.5: x1 discards < 25%; r 1.0 x1 runaway at 5 ms >= 25%, x5 none | **PASS** | x1 0% discards; runaway 13/24 (x1) vs 0/24 (x5) |
| P10 W <= 20 ms everywhere; trains at 100 ms >= 90% complete (r <= 0.56) | **FAIL** | W <= 10 ms everywhere (holds), but at r 0 only 60% of 100-ms train cues complete, for every GABA level (adaptive threshold, see 7) |
| P11 c 0, r 0.56, 10 ms trains: x1 <= 3 of 5, off >= 4 | **FAIL** | x1 4.0, off 5.0 |
5 PASS, 7 FAIL (P0-P11). The failures that matter: GABA x1 does not contain NMDA-driven reverberation (P3), GABA does not gate partial completion (P6), and recall rate is limited by the threshold floor rather than GABA (P10).

## Flags (non-biological or capped)
- GABA x5 = weight 1.0 = the grown GABA peak, outside the natural range: diagnostic only. x2 is above the literature mean; x1 about the mean (gaba_vm README).
- r 1.0 is nominal; achieved 0.73-0.78 on cue->non-cue, 0.43-0.61 on loops (simulator cap), so the r 1.0 runs are within a plausible NMDA/AMPA range as run. Nothing above r 1 was run.
- Pyr->Int has no NMDA in these models (the NMDA on interneurons in real CA3 is absent here).
- Contamination: events preceded by > 60 Pyr spikes in 1.5 s are excluded from rates (counted in tables.txt, column "cont"); this affects only GABA-off/low-GABA conditions with runaway (c 1.5 or 3.0, r >= 0.56).

## Figures for Randal (Vm recorded by NES; g_NMDA and g_GABA reconstructed offline from spike times and read-back weights, NMDA with NES's Mg block at the recorded Vm; dotted line in the non-cue panel = reconstructed adaptive threshold)
| file | what |
|---|---|
| fig_full_c1.5_r{0,0.56,1}.png | G0 full cue, GABA off vs x1 (NMDA adds an occasional second non-cue spike: 6.3 / 6.5 / 6.8 Pyr spikes per full-cue event at r 0 / 0.56 / 1.0) |
| fig_3cell_c1.5_r{0,0.56,1}.png | 3-of-4 cue: Vm of non-cue cells peaks just under threshold (r 1.0: 0.3 mV under the history-raised threshold) |
| fig_2cell_c1.5_r*.png | 2-of-4 cue: far below threshold |
| fig_pair_d10_c1.5_r*.png, fig_pair_d10_c0_r0.56.png | G0 then G1 at 10 ms: Vm of both memories' non-cue cells, interneurons, g_GABA |
| fig_train20_c1.5_r*.png, fig_train20_c0_r0.56.png | G0 cued 5 x every 20 ms |
| fig_full_c3_r0.56.png, fig_raster_c3_r0.56.png | c 3.0: GABA off / x1 / x5; x1 does not stop the NMDA-driven reverberation, x5 does |
| fig_raster_pair_c1.5_r1.png | double cue at c 1.5, r 1.0: runaway with off and x1 |
| fig_summary_discard.png, fig_summary_trains.png | discard vs delay and train completions, all conditions |

## Operational notes
- **The patched NES died once (10:26), cause unknown** (log ends mid-line, no core dump tool, dmesg not readable). I restarted the separate build only (logs preserved as wt/linefix-instance/nes_died_20261123_1026.log, api_before_restart_20261123_1030.log; output appended since). 8 runs were repeated from scratch.
- **NES memory grows ~0.2-0.3 GB per simulation even though every simulation is deleted** (RSS 0.23 GB -> 9 GB over ~35 runs), which looks like a leak in delete / model load and is a candidate cause of the crash. The queue restarted the separate NES + API whenever RSS passed 10 GB, between runs only (5 restarts). Separate instance now: NES pid 1600447 on 8011, API pid 1601098 on 8010; left running.
- One load failure (GetSomaPositions returned 0 neurons) on B_s77777_c1.5_r1_f1; rerun unchanged.
- Wall time: 09:37-16:34 (about 7 h) for 275 simulations (18.4 h of summed per-run wall time at 3 in parallel).

## Limits
Three models, disjoint 6-cell memories (B uses the overlap designs of ripple_overlap_j); one cue timing (4 spikes over 1.5 ms); NMDA kinetics and Mg block are NES defaults; the history effect means every rate in A/C depends on the 800/1000 ms spacing used; post hoc X check covers only 3-cell cues at GABA x1. The NMDA cap and the missing Pyr->Int NMDA mean "NMDA on" here is weaker than a free NMDA/AMPA ratio would be.
