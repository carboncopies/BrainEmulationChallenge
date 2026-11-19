# ripple_overlap_j: overlap between memories and a ripple-like event on the E4 recipe (2026-11-19)
E4 = V1 arbor, 20 interneurons, pyramidal D 0.0175, interneuron D 0.03, line-379-fixed build. All 10 grown E4 models reused (no regrowth): s16180 (inhib_e), s27182, s31415 (inhib_f), s11111, s22222 (headline_h), s33333, s44444, s55555, s66666, s77777 (headline_i). No STDP. Patched instance (NES 8011 / API 8010) only, max 3 concurrent, 294 sims, 294 of 294 completed, every sim deleted afterwards (no Traceback / DELETE FAILED), `loaded_ok` true in all. Patched instance stopped; main NES 3156209 / API 1972355 untouched; no git, no email, no NES code change.
Files: PREREGISTRATION.md (written before any packing count or sim, unedited), DEVIATIONS.md (3 items, written after the packing counts and before any sim), ovlib.py (candidates, overlap packing, R3 programming for overlapping memories), unit_check.py (programming identical to headline_i/dyn2.py for disjoint memories: 9 of 9 cases), capacity_ov.py + cap_*.json/log, design_*.json (49 designs), run_sim.py, run_queue.sh, raw_*.json (294), analyze.py (events_ov.json 8,370 events, events_rip.json 1,836 events), summarize.py, summary.txt, summary.json, stats.txt, test_runs/ (2 benchmark sims, not used).

## Headline results
1. **Overlapping memories fit in large numbers offline** (section 1), far more than I predicted. Sharing at most 1 cell: 4-8 six-cell memories per model; at most 2: 7-29; at most 3: 16-201 (disjoint: 2-4).
2. **Recall of overlapping memories is NOT clean in general.** Every full cue completes its own memory (100% of 2,790 full-cue trials) and every 3-cell cue stays silent (100%), but the cue also completes OTHER memories in many designs: full cross-completion (all exclusive non-cue members of another memory fire) in 5 of 168 full-cue trials for pairwise overlap <= 1 (F1; 0 of 56 at c = 0), but in 65 of 167 (39%) and 100 of 232 (43%) trials for overlap <= 2 (F2) and <= 3 (F3) at c = 0 already. The cause is summation of programmed pairs from different memories on a shared target (section 2), not runaway: non-member Pyr spikes are 0 at c <= 0.15.
3. **A ripple-like burst after a partial cue does replay the memory** (section 4): a 3-cell cue followed by a second spike in each cue cell 4-10 ms later (100-250 Hz) replays the full memory in 1,631 of 1,632 events (34 memories x 8 burst types x 6 conditions; 816 of 816 with GABA on) with no false completion at c <= 0.15; the plain 3-cell cue never does (0/204). But the event is not ripple-like: median duration 11 ms (max 21), the non-cue response has 1-2 volleys, the "frequency" is set by the input timing, and interneurons are driven feed-forward (median 20% participate, 1.3 spikes each), not pacing anything.

## 1. Offline capacity with overlap (6-cell = 4 cue + 2 non-cue; 8-cell = 4 + 4; role-consistent sharing; exact candidate lists, 150 random-restart greedy packings: lower bounds)
Max number of memories with pairwise overlap <= k. k = 0 is max(my packing, earlier feas2 count): my k = 0 packer found 2-3 where feas2 found 2-4 in 6 of 10 models (DEVIATIONS 2), so the k = 0 column is the earlier disjoint count; k >= 1 are my packer's (probably underestimates too).
| model | 6-cell k=0 | k<=1 | k<=2 | k<=3 | 8-cell k=0 | 8-cell k<=3 |
|---|---|---|---|---|---|---|
| s16180 | 2 | 4 | 13 | 64 | 0 | 0 |
| s27182 | 4 | 6 | 18 | 110 | 1 | 1 |
| s31415 | 3 | 7 | 29 | 201 | 1 | 3 |
| s11111 | 2 | 4 | 12 | 53 | 0 | 0 |
| s22222 | 3 | 6 | 25 | 197 | 1 | 5 |
| s33333 | 3 | 6 | 16 | 51 | 1 | 1 |
| s44444 | 2 | 4 | 17 | 108 | 0 | 0 |
| s55555 | 2 | 4 | 7 | 16 | 0 | 0 |
| s66666 | 3 | 7 | 16 | 33 | 1 | 1 |
| s77777 | 4 | 8 | 20 | 77 | 1 | 2 |
8-cell memories exist at all only in the 6 models with a cue set having >= 4 strong common targets; with overlap <= 3 two or more fit in 3 models (s31415, s22222, s77777), and only those have a pair that shares exactly 3 cells (F8 designs). Capacity here is limited by cells with >= 4 strong inputs (6-14 per model), not by cell number: allowing shared non-cue cells lets the same targets serve many memories. That is also why these huge counts are suspicious as "memories": see section 2.

## 2. Overlap recall (33 overlap designs x 6 conditions = 198 sims; 16 ripple designs x 6 = 96 sims; 294 in total)
Design families: F1/F2/F3 = maximal 6-cell packing with pairwise overlap <= 1/2/3 (all memories programmed simultaneously; cued memories: all if <= 24, else a seeded random 24, DEVIATIONS 1), F8 = 8-cell packing with overlap <= 3 (3 models). Trials = full-cue trials (cued memory) and 3-cell trials (2 per memory). Conditions c = 0, 0.15, 1.5 nS x GABA on / silenced (SG). clean = full cue: completes (all non-cue fire within 10 ms), no cell of any other memory outside the cued one fires, no non-member Pyr spike; 3-cell: nothing completes, no cross.
| family | c | GABA | full-cue trials | own completion | clean | any cross | full cross | 3-cell trials clean | non-member Pyr trials |
|---|---|---|---|---|---|---|---|---|---|
| F1 (<=1) | 0 | on / SG | 56 | 56 | 56 / 56 | 0 / 0 | 0 / 0 | 112 / 112 | 0 |
| F1 | 0.15 | on / SG | 56 | 56 | 55 / 55 | 1 / 1 | 1 / 1 | 112 / 112 | 0 |
| F1 | 1.5 | on / SG | 56 | 56 | 52 / 47 | 4 / 9 | 4 / 9 | 112 / 112 | 0 |
| F2 (<=2) | 0 | on / SG | 167 | 167 | 102 / 95 | 65 / 72 | 65 / 72 | 334 / 334 | 0 |
| F2 | 0.15 | on / SG | 167 | 167 | 96 / 93 | 71 / 74 | 71 / 74 | 334 / 334 | 0 |
| F2 | 1.5 | on / SG | 167 | 167 | 49 / 42 | 118 / 125 | 118 / 125 | 334 / 334 | 0 / 9 |
| F3 (<=3) | 0 | on / SG | 232 | 232 | 132 / 115 | 100 / 117 | 100 / 117 | 464 / 464 | 0 |
| F3 | 0.15 | on / SG | 232 | 232 | 120 / 109 | 112 / 123 | 112 / 123 | 464 / 464 | 0 |
| F3 | 1.5 | on / SG | 232 | 232 | 56 / 50 | 176 / 182 | 176 / 182 | 464 / 464 | 1 / 20 |
| F8 (8-cell, <=3) | 0 | on / SG | 10 | 10 | 10 / 10 | 0 / 0 | 0 / 0 | 20 / 20 | 0 |
| F8 | 0.15 | on / SG | 10 | 10 | 10 / 10 | 0 / 0 | 0 / 0 | 20 / 20 | 0 |
| F8 | 1.5 | on / SG | 10 | 10 | 8 / 3 | 2 / 7 | 2 / 6 | 20 / 20 | 0 |
Designs with ALL cued trials clean (10 models per family; stats.txt): F1 on: 10/10 (c 0), 9/10 (0.15), 7/10 (1.5); F2: 1/10, 1/10, 0/10; F3: 0/10 at every c; F8 (3 models): 3/3, 3/3, 2/3. Per-model F1 full-cue clean at c<=1.5 on: perfect in seven models (12/12, 12/12, 18/18, 18/18, 21/21, 12/12, 12/12), 17/18 (s33333), 18/21 (s66666), 23/24 (s77777).
GABA: on vs silenced give the same clean / not-clean outcome in 1,371 / 1,395 paired events at c = 0, 1,381 / 1,395 at c = 0.15 and 1,366 / 1,395 at c = 1.5 (98.4% overall). Where they differ (mostly c = 1.5) silencing is worse (F1 52 -> 47, F8 8 -> 3 clean; non-member Pyr spikes appear only in SG, 9 + 20 trials): inhibition starts to help only at c = 1.5.
**Mechanism of the cross-completion (checked on a failing case, s16180 F2, c = 0).** Cell 8 is a non-cue member of several memories. When memory 0 (cue 2, 42, 50, 95; non-cue 19, 84) is cued, cue cells 42 and 95 also belong to other memories whose non-cue cell is 8, so each already carries a programmed 4.12 nS pair onto cell 8; the fired non-cue cells 19 and 84 are non-cue partners of 8 in other memories (6.22 + 1.78 nS loops). Total programmed conductance from cells that fired onto cell 8 = 16.2 nS, i.e. at the R3 threshold (16.5), so 8 fires and the other memories' exclusive non-cue member(s) are completed. This is superposition of per-memory R3 programming (my union rule), not a dynamical instability. By shared-cell type of the cued/other pair (c = 0, GABA on, all families): one shared non-cue cell only: F1 0/200 full cross, F2 379/1,310 (29%), F3 4,304/8,758 (49%); one shared cue cell only: F1 0/32, F2 9/104, F3 173/343; one shared cue + one non-cue: F2 297/728, F3 2,134/3,399. Dense families make shared targets accumulate pairs from many memories, so the 16.5 nS threshold is reached by chance. (Pair-level rates in summary.txt count chains too, e.g. memories sharing 0 cells with the cued one show high rates because their members belong to other memories that completed; they are not independent evidence.)
**Verdict by the preregistered rule (per family, GABA on, c <= 1.5):** F1 PARTIAL (97.0% of full-cue trials clean = 163 / 168 but 5 full cross-completions, so not PASS under "no full cross-completion"; at c <= 0.15 only 1 of 112 trials); F2 FAIL (49.3%: 247 / 501); F3 FAIL (44.3%: 308 / 696); F8 PARTIAL (28 / 30 = 93.3%, 2 full cross at c = 1.5; 0 of 20 at c <= 0.15, 3 models, 6 memories at most). Capacity claim "overlapping memories fit" holds offline (section 1) but with the programming rule used here only overlap <= 1 (and 8-cell overlap 3 at c <= 0.15, tiny n) recalls essentially cleanly.

## 3. Scoring of overlap predictions (HIT inside range, PARTIAL within 25% beyond, MISS otherwise)
| item | predicted | observed | score |
|---|---|---|---|
| O1 6-cell k<=1 | 3-6 (median 4) | 4,6,7,4,6,6,4,4,7,8 (median 6) | 7 HIT, 2 PARTIAL (7), 1 MISS (8) |
| O1 6-cell k<=2 | 4-9 (median 6) | 13,18,29,12,25,16,17,7,16,20 (median 16.5) | 1 HIT, 9 MISS |
| O1 6-cell k<=3 | 5-14 (median 8) | 64,110,201,53,197,51,108,16,33,77 | 0 HIT, 1 PARTIAL (16), 9 MISS |
| O1 more at k=3 than k=0 in >= 8 of 10 | 90% | 10 of 10 | HIT |
| O1 8-cell k<=3: 0-2 per model; >= 2 memories in 3-5 models; max 3 | | 0,1,3,0,5,1,0,0,1,2; 3 models with >= 2; max 5 | per-model range 2 MISS (3, 5); count of models HIT; max MISS (5) |
| O2 own completion >= 97% | 90-100% | 100% (all families, c, GABA) | HIT |
| O2 3-cell silent >= 98% | | 100% | HIT |
| O2 full cross-completion in 0 trials | 80% | F1 5 of 168; F2 254 of 501; F3 388 of 696 (c<=1.5 on) | MISS |
| O2 any cross <= 2% of full-cue trials | 70% | F1 5/168 = 3.0%, F2, F3 > 50% | MISS |
| O2 non-member Pyr spikes 0 at c<=0.15 | 85% | 0 trials | HIT |
| O3 on vs SG identical in >= 90% of trials | 85% | 98.4% | HIT |
| O4 C-type k=3 still silent; first failures at k=3, c=1.5 | 80% | shared-cue-only pairs fail 3 of 4 (F3) and 173/343 (1 shared); the failures are not confined to c = 1.5 | MISS |
| O5 designs all-clean (c<=1.5, on): k=1 85%, k=2 80%, k=3 70% | | F1 26/30 = 87%, F2 2/30, F3 0/30 | HIT, MISS, MISS |
What I got wrong: I assumed R3 programming of overlapping memories could be superposed without interference because each target still needs 4 cue cells; shared non-cue targets in dense families receive pairs from several memories, so partial sums reach threshold. The offline "fit" counts are therefore not evidence of usable capacity.

## 4. Ripple-like event after a partial cue (28 four+two memories and 6 four+four memories from the earlier disjoint packings, all 10 models; 34 memories x 9 events x 6 conditions = 1,836 events)
**Definition (as preregistered).** Partial cue = 3 cue cells (cue[1:], spikes at 0 / 0.5 / 1.0 ms) followed, in the same 3 cells, by n total spikes at period 1000/f ms, f = 100, 150, 200, 250 Hz, n = 1 (control), 2, 3; interneurons are not driven; everything else is the standard R3 memory at c = 0, 0.15, 1.5 nS, GABA on / silenced. Biological reference: CA3/CA1 SWR ripple 90-250 Hz (Ecker 2022; Evangelista 2020; Schlingloff 2014; see CA3_NATURAL_RANGES.md, LIT_INHIBITION_ENGRAMS.md), SWR 50-100 ms, <= 3 spikes per cell at <= 250 Hz. No bio_ranges.json value changed (it has no rate limits); weights are the R3 ones (<= grown conductance). The simulator cannot generate a ripple (no current injection, no envelope, GABA decay ~10 ms), so "interneuron-paced" cannot be tested as stated; interneuron participation is measured.
| quantity | result (replaying events pooled; GABA on, c <= 0.15: 544 events) |
|---|---|
| control (3-cell, 1 spike) | 0 / 204 replay (34 memories x 6 conditions) |
| replay (all non-cue members fire within 100 ms) | 544 / 544 (n=2 and n=3, all four frequencies); c = 1.5 on 272 / 272; SG c <= 0.15 544 / 544; SG c = 1.5 271 / 272 |
| latency of the first non-cue spike (median, c = 0 on) | n=2 and n=3: 12.7 ms at 100 Hz, 8.5 ms at 150, 6.8 at 200, 6.0 at 250 (i.e. 2-3 ms after the SECOND forced volley) |
| duration (first to last Pyr member spike) | median 11.0 ms, max 21 (c <= 0.15 on); < 30 ms in 100% (99% at c = 1.5 on; SG c = 1.5: 78%, max 70.5 ms) |
| non-cue volleys (gap >= 2 ms) | 1 or 2 per event; >= 3 volleys in 10 / 544 events (1.8%), event frequency defined only there (all > 250 Hz or well off f); with GABA silenced 52 / 544 |
| interneuron participation | median 20% of the 20 interneurons (IQR 15-25%), 1.3 spikes per participating interneuron; all interneuron spikes 1-6 ms after some member spike (lock 1.00, trivially because forced cue spikes and member spikes cover most of the window) |
| false completion, c <= 0.15 | 0 events with another memory's cells firing, 0 non-member Pyr spikes |
| c = 1.5 on | 9 events cross, 20 non-member spikes, 4 runaway (> 50 spurious) of 272 (1.5%); silenced: 55 cross, 73 non-member, 59 runaway of 272 (22%; 20 of 34 at n=3, f = 150 and 250) |
Replay needs only the second spike: n = 3 adds nothing over n = 2, and 100 Hz replays as reliably as 250 Hz (only the latency changes). A 3-cell volley delivers about 12.4 nS (below the 16.5 nS single-volley threshold); two volleys 4-10 ms apart summate. So this is temporal summation of a doublet, not an oscillation; the plain partial cue (one volley) fails, a doublet succeeds.
GABA effect at c <= 0.15 (544 paired events): duration within 10% in 384 (71%), same number of non-cue volleys in 366 (67%), interneuron spikes higher when silenced in 334 (silencing lets non-cue cells fire a second volley: n = 3 events with 3 volleys 10 on vs 52 silenced). So the 10 ms GABA kinetics do shape the response (limit to one volley) but there is no inhibitory pacing at ripple frequencies.

## 5. Ripple predictions scored
| item | predicted | observed | score |
|---|---|---|---|
| R1 control silent | 97% | 0 / 204 | HIT |
| R2 n=3, f>=150 replay >= 80% at c<=0.15 on | 60% | 100% | HIT |
| R2 replay at 100 Hz lower than at 250 Hz in >= 6 of 10 models | 75% | equal in all models (latency differs 12.7 vs 6.0 ms) | MISS |
| R2 n=2 no more than n=3 | 90% | equal | HIT |
| R3 no false completion at c<=0.15 | 85% | 0 / 544 | HIT |
| R3 c=1.5 non-member > 50 spikes in <= 5% of events | 80% | on 1.5% (silenced 22%) | HIT (on) |
| R4 event frequency undefined (< 3 volleys) in >= 50% | 70% | 98% (on) | HIT |
| R4 frequency within +-20% of f in >= 70% of events with >= 3 volleys | | 0 of 10 (c <= 0.15 on) | MISS |
| R5 duration < 30 ms in >= 80% (does not reproduce 50-100 ms SWR) | 85% | 100% | HIT |
| R6 participation median 20-40%, 1-3 spikes | 70% | median 20%, 1.3 | HIT (lower edge) |
| R6 >= 70% of interneuron spikes 1-6 ms after a member volley | | 100% (trivial) | HIT, weak |
| R6 GABA silenced changes frequency/duration < 10% in >= 80% of paired events | 75% | duration 71%, volley count 67% | PARTIAL (duration), MISS (volleys) |
| R7 c=1.5 vs 0 replay within 10 points | 75% | 100% vs 100% (on) | HIT |
Verdicts (rules fixed in advance): (a) "partial-cue replay by a ripple-frequency burst" = **PASS** (control silent, n = 3 replays 100% of memories at c <= 0.15 on, no false completion); (b) "ripple-like event" = **FAIL**, as predicted (frequency with >= 3 volleys in 1.8% of events and none in 100-250 Hz; duration 11 ms vs 30 ms; participation 20% vs 25%).

## 6. Honest limits
- Forced spikes, not a network-generated ripple; replay here is summation of a doublet in the 3 cue cells onto the R3 non-cue threshold (16.5 nS), and R3 programming (cue->non-cue 4.125 nS per pair) is imposed, not grown. The ripple PASS means "the programmed memory completes when its partial cue fires twice within 10 ms", not that the network produces ripples.
- Overlap results depend on my programming rule for overlapping memories (union of pre cells for the 8 nS loop caps, same-role sharing, cue->interneuron cap per memory). A rule that keeps cross-memory pairs from adding up (e.g. lower per-pair values for hub targets) might remove the cross-completion; I did not tune it (no tuning allowed beyond the preregistered rule), so the F2/F3 failures are failures of this rule.
- Offline counts are lower bounds from a random-restart packer that was weaker than feas2 at k = 0; the big F3 designs (16-201 memories on 96 cells with 6-14 usable targets) are stress tests rather than memory systems, and only 24 memories per design were cued (DEVIATIONS 1). Events inside a design are not independent (same targets, same network), and one deterministic run per grid cell (seed 0): n counts are trials, not independent samples. Per-model variation is large (F2 full-cue clean 14/72 in s22222 against 51/54 in s27182).
- Overlap structure (cue-sharing vs non-cue-sharing) was not controlled by design; types appear only post hoc from the packing. 8-cell overlap rests on 3 models and 6 memories.
- Interneuron "locking" is computed against all member spikes (including forced cue spikes) and is trivially 1.0; participation counts spikes in a 100 ms window.
- 10 E4 models: 5 pass all 7 bars (headline_i); the overlap/ripple outcomes were not related to that; no regrowth, so grown-model noise (repro_g) is a between-model, not within-model, quantity here.
- c = 3.0 not run (runaway is known there). No STDP.
