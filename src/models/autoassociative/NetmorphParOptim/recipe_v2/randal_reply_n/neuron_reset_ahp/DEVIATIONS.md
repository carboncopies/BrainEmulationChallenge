# Deviations and notes after launch (PREREGISTRATION.md is unedited)
1. **(after all runs, analysis bug fixed before scoring) Full-cue events were not counted as "completing".** The preregistration lists full, 75% and 50% events as completing events. My code required at least one non-cue member (`bool(nonc)`), which is impossible for a full cue (all 17 members are cued). So the full-cue event was left out of *last*, stops100 and the spikes-per-member medians, in the new runs and in the LH references alike.
   - Fixed in `analyze_nr.py`: a full cue counts as complete. The same bug sits in `baseline_measures.py` (PLAN.md numbers), which I left as written.
   - Effect on the preregistered RELIEF references (median *last*, LH): s77777 r1 378 → 383 ms; s66666 r1 412 → 413 ms; r0.56 unchanged (209 / 209).
   - Every RELIEF verdict is the same under either reference; the README states both.
2. **(10:33, queue start) The separate build was restarted before the first run.** It held 12.7 GB RSS, ran at about 250% CPU with no client attached (the residual load-failed simulation from partial_cue C2) and was logging RPC timeouts. The queue's rule (RSS > 10 GB and no simulation running, checked across all workers) restarted it: NES 1955266 / API 1955879 became NES 2397163 / API 2397757. Main NES 3156209 / API 1972355 were untouched. No other restart was needed (RSS at most 4.2 GB).
3. **(after all runs, post hoc, labelled)** `posthoc_residual_sahp.py` reconstructs the residual sAHP conductance at cue onset from the recorded spikes and the arm's parameters (NES AHPCLIP rule). It was added after seeing the loss of 50%-cue completion. It is not preregistered and is reported as an explanation, not as a test.
4. Counting: 14 simulations were run as planned and none failed, so no rerun was used. Every simulation was deleted (14 "deleted" lines), and every model copy was removed (14 "removed copy" lines; 0 `nr-*` files left in the model folder).

# PREREGISTRATION_B deviations and notes
B1. (before any B sim) `run_queue_b1.sh` was generated from `run_queue.sh`. My first edit did not add `run_nr2` to the concurrency gate; I fixed it before launch and checked it (the queue log shows "sims running" 1-2 during the runs). No effect on any simulation.
B2. Counting: B1 4 sims and B2 6 sims, 10 in total as planned. None failed, so no rerun was used. All deleted (10 "deleted"), all model copies removed (0 `nr*` files left). No NES restart was needed (RSS at most 6.6 GB).
B3. (after B2, post hoc, labelled) `posthoc_cue_rebound.py` was added after seeing that RS2 *raised* 75% completion in E16. It counts cue-cell spikes in the 30 ms window. It is not preregistered and is reported as an explanation.
B4. B2 uses the 9 s spacing, so the stored W70/LH references (3 s) differ in spacing as well. For N0 (sAHP 300 ms) the leftover sAHP at 3 s is about 0 anyway (residual 0.00 in the 3-s N0 run).

# PREREGISTRATION_C deviations and notes
C1. Counting: 8 sims as planned (C1 2, C2 6). None failed, so no rerun was used. All deleted (8 "deleted" lines), all model copies removed (0 `nr*` files left). No NES restart was needed (RSS at most 8.5 GB before a start, 7.9 GB after the queue). Main NES 3156209 / API 1972355 untouched.
C2. (after C, post hoc, labelled) The list of non-completing members per failed 75% event (README "Answer to C2") was added after seeing that s66666 stays at 4/6. It is not a preregistered measure.
C3. `analyze_c.py` reads the B2 E16/E16.5 runs as references. Its manipulation-check column is also printed for B2 rows, where it shows the RS2 rebound (0.42), not a manipulation.

# PREREGISTRATION_D deviations and notes
D1. (before launch) After writing PREREGISTRATION_D.md and before any D sim, I corrected two base-row values in its design table: max pair 3.5 → 3.45 (s66666) and 4.5 → 4.40 (s77777), read from the stored B2 E16.5 runs. No other edit.
D2. Counting: 6 sims as planned, none failed, no rerun. All deleted (6 "deleted"), all model copies removed (0 `nr*` files left). No NES restart was needed: RSS at the last start was 9.93 GB, under the 10 GB rule, and 9.36 GB after the queue. Main NES 3156209 / API 1972355 untouched.
D3. Prediction D8 is not testable (no run has 75% < 6/6). It is scored n/a, not HIT.

# PREREGISTRATION_E deviations and notes
E1. (before preregistration) The first cue draw (key `E-`) was generated and inspected before the cue rule was written. It cued s66666 cells 28 and 57 in all six 75% events. PREREGISTRATION_E records this and the coverage rule that replaced it (first n with coverage >= 2 and no repeated subsets; n = 1111). The draw was chosen on coverage only, not on any outcome.
E2. The separate build was restarted once before the first run, as preregistered (RSS 9.36 GB, below the 10 GB rule, restarted at John's expectation). NES 2397163 / API 2397757 became NES 2768884 / API 2769516. No other restart (RSS at most 1.8 GB at a start). Main NES 3156209 / API 1972355 untouched.
E3. Counting: 4 sims as planned, none failed, no rerun. All deleted (4 "deleted"), all model copies removed (0 `nr*` files left).
