# stdp_k: STDP on the E4 recipe (2026-11-19)
**Answer in one paragraph.** The simulator DOES support STDP (AMPA receptors only, enabled per simulation with `SetSTDP`), so the main experiment is simulated, not offline. Its rule is potentiation-only (depression essentially never fires; 13 weights out of 32,273 decreased, all Pyr->Int pairs sitting at the cap, by <= 0.007). Repeating recalls strengthens exactly the programmed cue->non-cue pairs (+0.0103 weight per recall, 100% at the cap after 100 recalls), leaves every pair involving a non-member and every between-memory pair exactly unchanged, and never causes runaway (0 of 11,000 training events with > 50 spurious spikes). But it breaks the R3 selectivity: full-cue recall stays perfect (28 of 28 memories), yet after only 10 recalls 15 of 28 memories already complete (at least partly) from a 3-cell cue, and after 100 recalls all 28 do (R3 requires the 3-cell cue to stay silent). "Weakening others" is not available in the simulator; an OFFLINE literature rule (Song et al. 2000; Bi & Poo time constants) applied to the same spike trains does weaken the non-cue->cue loops (-0.046 per 10 recalls) and non-cue loops, and strengthens cue->non-cue.
Files: PREREGISTRATION.md (written after the capability probe, before any experiment run, unedited), probe_stdp.py / probe_on.json / probe_off.json (capability probe), stdp_run.py (training sim with STDP on -> trained weights -> probe sim with STDP off), run_queue.sh, raw_*.json (100 runs: 10 models x {A1, A2} x R {10, 100} x c {0, 0.15} = 80, plus 20 controls R = 0), analyze.py, summary.json, summary.txt, log_*.txt. 180 simulations run (80 training sims with STDP on + 100 probe sims with STDP off, the 20 controls going through the same probe pipeline without training), every sim deleted, no Traceback / DELETE FAILED, `loaded_ok` true. Patched instance (NES 8011 / API 8010) only, max 3 concurrent; stopped. Main NES 3156209 / API 1972355 untouched; no git, no email, no NES code change.

## 1. What the simulator supports (source: BrainGenix-NES/Source/Core; probe on s33333)
- `Simulation/SetSTDP(DoSTDP)` sets `Sim.STDP`. With it on, every spike of a postsynaptic neuron (forced spikes included) updates all incoming AMPA connections (`LIFCReceptorData::STDP_Update`, Structs/Neuron.cpp:162): dt = t_post - t_pre(last spike of the presynaptic cell) - Shift; dt >= 0: dw = A_pos (dt/tau_pos) exp(-dt/tau_pos); dt < 0: dw = A_neg (dt/tau_neg) exp(dt/tau_neg); weight clamped to [0, 1]; conductance = min(g_peak_sum, weight x g_peak_sum x kernel).
- Parameters (fixed in NetmorphManagerThread.cpp, not settable through the API): AMPA Hebbian, A_pos 0.027, A_neg 0.02, tau_pos = tau_neg = 7 ms, Shift -4 ms. NMDA and GABA: no STDP. Because of Shift = -4 ms the effective dt is positive for every post spike at or after the last pre spike, so the depression branch is practically never taken; kernel peak is at t_post - t_pre = 3 ms (0.0099 per pairing); 100 ms apart it is ~3e-6.
- Probe (9 forced pairs, 20 pairings): pre-before-post +1/+3/+6 ms: +0.0094/+0.0099/+0.0092 per pairing, +20 ms +0.003, +50 ms +0.0001; post-before-pre (-3, -8, -20 ms): 0 change; NMDA / GABA connections: 0 of 3,579 changed; STDP off: 0 of 3,299 AMPA changed.
- Consequences: potentiation of any AMPA pair whose two cells both fire (also pruned c = 0 pairs, but never a new connection: g_peak_sum and the pair set are the grown ones); no depression.

## 2. Hard caps (bio_ranges.json has no synaptic-weight entry; used: weight in [0, 1], conductance <= grown g_peak_sum, STDP parameters untouched)
Checked on all 80 training sims: 0 weight violations, 0 conductance violations (weights in [0, 1.0000001], float32 rounding); no growth or bio_ranges parameter changed.

## 3. Simulated results (10 E4 models, 28 memories = disjoint 4+2 packings, GABA on, STDP on only while training; c = 0 and 0.15 give identical weight changes because only memory cells fire)
Arms: A1 = full-cue recall; A2 = 3-cell partial cue + second spike in each cue cell (100-250 Hz, f cycling), R repetitions per memory, interleaved, 500 ms apart.
**Weight change (mean over pairs; n pairs) per class after training, c = 0.15 (c = 0 same except cue->cue w0 = 0):**
| class | A1 R=10 | A1 R=100 | A2 R=10 | A2 R=100 | n pairs |
|---|---|---|---|---|---|
| (a) cue->non-cue | +0.103 | +0.333 (100% at cap) | +0.084 | +0.251 (75% at cap; the 3 forced cue cells; the unforced 4th cue cell: exactly 0.000) | 224 |
| (b) non-cue<->non-cue loops | +0.0002 | +0.004 | +0.001 | +0.004 | 51 (almost all already at weight 1) |
| (c) non-cue->cue loops | 0.000 | 0.000 | 0.000 | 0.000 | 53 |
| (d) cue->cue | +0.051 / +0.005 per recall (54 of 100 pairs, those where the earlier-firing cell is the pre) | +0.47 | +0.071 | +0.45 | 100 |
| (e) Pyr->Int from cue cells | +0.027 | +0.157 | +0.029 | +0.153 | 903 |
| (f) pairs between different memories | 0.000 | 0.000 | 0.000 | 0.000 | 990 |
| (g) pairs involving non-member cells | 0.000 | 0.000 | 0.000 | 0.000 | 29,572 |
| (h) other | 0.000 | -0.0000 | 0.000 | -0.0002 | 380 |
Per recall: cue->non-cue +0.0103 (A1); A2 +0.0084 averaged over all four cue cells, +0.0112 for the three forced cells (the unforced one is 0). Per model (A1, R = 10, c = 0.15) mean class-(a) change 0.099-0.110 in all 10 models. Decreases: 0 in A1 R=10 and A2 R=10; 1 (A1 R=100: s31415, Pyr->Int, 1.0000 -> 0.9986) and 12 (A2 R=100, all Pyr->Int pairs at the cap, down by 0.003-0.007) of 32,273 AMPA connections per arm; so the depression branch does fire very rarely (cause not identified; both ends of the decrease are forced/interneuron spikes).
**Training stability:** 0 of 280 (R=10) / 2,800 (R=100) events per arm and background had > 50 non-member Pyr spikes (maximum 0 non-member spikes per event); interneuron spikes per event rose only from 2.3 to 2.9 (A1) and from 2.8 to 3.4 (A2, R=100).
**R3 probe after training (STDP off, trained weights programmed into a fresh sim; 28 memories x full cue, 3-cell cue a, 3-cell cue b):**
| condition | full cue completes (10 ms) | memories with a 3-cell cue that makes >= 1 non-cue cell fire | 3-cell cue events with ALL non-cue cells firing (of 56) | non-member Pyr spikes / cross-memory firing |
|---|---|---|---|---|
| control R = 0 (c = 0, 0.15) | 28 / 28 | 0 | 0 | 0 / 0 |
| A1 R = 10 | 28 / 28 | 15 | 14 | 0 / 0 |
| A1 R = 100 | 28 / 28 | 28 | 51 | 0 / 0 |
| A2 R = 10 | 28 / 28 | 16 | 14 | 0 / 0 |
| A2 R = 100 | 28 / 28 | 28 | 45 | 0 / 0 |
(c = 0 and c = 0.15 give identical probe results.) From these probes (3-cell cue conductance sum onto a non-cue cell vs fired / not fired, 560 cell-events): firing occurs from 13.84 nS, and some cells stay silent up to 15.68 nS: the single-volley threshold lies between 13.8 and 15.7 nS depending on the cell, lower than the 16.5 nS design value that I used in the offline estimate (that estimate gave 24 of 28 memories able to complete from 3 cells at the cap; observed 28 of 28).

## 4. OFFLINE literature-rule analysis (NOT simulated; applied to the training spike trains, which were produced with the simulator's own STDP on)
Rules: all-to-all pair-based, additive, weights bounded to [0, 1], applied per event: L1 Song, Miller & Abbott 2000 (Nat Neurosci 3:919): A+ 0.005, A- 0.00525, tau+ = tau- = 20 ms; L2 Bi & Poo 1998 (J Neurosci 18:10464) time constants as used by van Rossum et al. 2000 (tau+ 16.8, tau- 33.7 ms; recalled, not re-verified), same A. Mean weight change per class (c = 0.15; c = 0 differs only for cue->cue because w0 = 0 cannot go down):
| class | L1 A1 R=10 | L1 A1 R=100 | L1 A2 R=10 | L1 A2 R=100 | L2 A1 R=10 |
|---|---|---|---|---|---|
| (a) cue->non-cue | +0.044 | +0.329 | +0.064 | +0.251 | +0.042 |
| (b) non-cue<->non-cue | -0.023 | -0.181 | -0.023 | -0.318 | -0.023 |
| (c) non-cue->cue | -0.046 | -0.559 | -0.069 | -0.667 | -0.049 |
| (d) cue->cue | +0.003 | +0.199 | +0.002 | +0.197 | +0.003 |
| (f), (g) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
Pairs that decrease: 135-224 of 32,273 per arm (non-cue->cue, non-cue loops, a few Pyr->Int). At R = 100 all non-cue->cue loops are at weight 0 (A1) or 16-33% (A2). So with depression the rule strengthens the memory pairs and weakens the return loops; pairs of non-members and between memories are still untouched, because they never fire. (This does not feed back into any simulation: if the loops were really weakened, recall of the full cue may fail differently; not tested.)

## 5. Prediction scoring (HIT inside range, PARTIAL within 25%, MISS otherwise)
| item | predicted | observed | score |
|---|---|---|---|
| S1 no weight decreases | 99% | 13 of 32,273 per arm-pair (Pyr->Int at cap, <= 0.007), 0 in R=10 arms | MISS (strictly), effect negligible |
| S2 cue->non-cue +0.009-0.022 per recall; R=10 +0.09 to +0.22; R=100 >= 90% at cap | 85% | +0.0103; +0.103; 100% (A1) | HIT |
| S3 loops +0.008-0.015 per recall | | non-cue loops +0.00002 per recall (already at cap); cue->cue +0.005 (0.007-0.010 predicted); non-cue->cue 0.000 | MISS (loops at cap), PARTIAL (cue->cue), HIT (non-cue->cue) |
| S4 classes (f), (g) unchanged < 0.001 after R = 100 | 90% | exactly 0.000 in 30,562 pairs | HIT |
| S5 A2: forced cells like A1 within 1.5x; unforced cell's pairs < 0.001 | 80% | forced cells 0.0112 vs 0.0103 per recall; unforced exactly 0.000 | HIT |
| S6 no event > 50 non-member spikes | 95% / 85% | 0 of 11,000 | HIT |
| S7 after R=10 3-cell cues silent in >= 90% of memories; no non-member spikes | 80% | silent in 13 (A1) / 12 (A2) of 28 (46% / 43%); 0 non-member spikes | MISS (selectivity), HIT (spikes) |
| S8 after R=100 full cue >= 95%, 3-cell completes >= 40% (A1) / 50% (A2), non-member spikes <= 20% | 70% | 100%; 100%; 0 | HIT |
| S9 controls: 100% | 97% | 28/28, 0 leak | HIT |
| L-predictions: cue->non-cue +0.003-0.006 per recall; non-cue->cue -0.003 to -0.006; cue->cue |dw| < 0.002 per recall; non-members 0 | | +0.0044; -0.0046; +0.0003; 0 | HIT x4 |
| L R=100: non-cue->cue >= 80% at 0; cue->non-cue about +0.4 | 70% | A1 100% at 0, A2 16-33%; +0.33 (A1), +0.25 (A2) | HIT (A1) / MISS (A2); PARTIAL |
Verdict rules: **Q1 (strengthens memory pairs): PASS** (10 of 10 models > 0.05 after R = 10; no class-(a) decrease). **Q2 (weakens others): simulated FAIL** (0.04% of pairs decreased, predicted); **offline PASS** (non-cue->cue -0.046 after R = 10 while cue->non-cue +0.044). **Q3 (no runaway): PASS.** **Q4 (R3 recall preserved): PARTIAL** at R = 10 and R = 100 (full cue 28/28 intact, no spurious spikes, but 3-cell selectivity lost in 54% / 100% of memories; predicted PASS at R = 10, so that is a miss). **Cap rule: PASS.**

## 6. Honest limits
- The simulator rule is potentiation-only with fixed parameters (A+ 0.027, tau 7 ms, Shift -4 ms, larger than the Song et al. steps of 0.005 at tau 20 ms) and a nearest-last-pre, post-spike-triggered update; results are about this rule, not hippocampal STDP. The depression branch fires rarely and its cause is not identified (not an intended behaviour I could verify without changing code).
- Recall is driven by forced spikes; R3 programming (cue->non-cue 4.125 nS per pair) is imposed, so the finding that potentiation of those pairs breaks 3-cell silence follows partly from the programmed starting weights (R3 sets them at the threshold edge). With grown weights (as-grown 0.2) the picture could differ; not tested.
- 28 memories in 10 models, one deterministic run per cell (Seed 0); events/memories within a model are not independent. Only 4+2 memories, GABA on, c <= 0.15; c = 1.5 and silenced GABA not run (no recall-related effect at c <= 0.15 expected from ripple_overlap_j, not tested with STDP).
- Probe uses trained weights programmed into a fresh sim (STDP off); readback from GetConnectome (float32); changes < 1e-4 are treated as zero.
- The offline literature analysis uses spike trains from simulations that had the simulator's STDP on, applies each rule independently of the network (no feedback), and takes the Bi & Poo time constants from memory. Not simulated.
- Weight cap is the simulator clamp [0, 1] and the grown conductance; bio_ranges.json defines no synaptic-weight limits, so "inside bio_ranges" means: no growth parameter touched and no connection stronger than grown.
