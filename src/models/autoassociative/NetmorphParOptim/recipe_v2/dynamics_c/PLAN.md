# dynamics_c PLAN (written 2026-11-16, before any simulation)
Question: does autoassociative recall (R3 recipe, option_B_scaled criterion) still work when Pyr->Pyr has ~5k synapses (connection prob ~0.25, ~2 syn/pair) with biological-range interneuron connectivity?

## Networks
linefix_c Stage 2 V1n30 (96 Pyr + 30 Int, line-379-fixed build, pyr D 0.0175, int D 0.0495), seeds 16180 and 27182 (models v2-lfc-V1n30_s<seed>_p0d0175_i0d04950000 in the patched instance, API 8010 / NES 8011). Own scripts only, no code changes, main NES/API untouched. Interneuron connectivity as grown (unscaled): Int->Pyr 5.9-6.7 syn/pair, Pyr->Int ~3.5-4, GABA weight 0.2 (x1, model default), 10 ms decay.

## Can the weight-space programming be applied? Partly (offline check, feas.py / feas.log)
The R3 recipe sets every cue->non-cue pair to T/4 = 4.125 nS, which needs a grown g_peak_sum >= 4.125 nS on each of the 16 cue->noncue pairs of an 8-cell memory (weights can only be lowered, max 1.0). In the sparse network only 194 of 9,120 pyramidal pairs reach 4.125 nS (median pair 0.98 nS), and only 8-9 cells have >= 4 such inputs. Random-restart packing (300 tries, not exhaustive) finds at most **1 disjoint 4-cue + 4-noncue memory per seed** (the earlier S1 work used K=4), and 3 disjoint 4+2 memories per seed. Relaxing to 3.5 nS does not give more 4+4 memories on seed 16180 (1) and only 2 on 27182, and would break the 3-cell selectivity margin, so it is not used. So the literal 4-memory R3 design cannot be built; smallest feasible test:
- DA: 1 memory, 4 cue + 4 noncue (exact R3 memory, per seed).
- DB: 3 disjoint memories, 4 cue + 2 noncue each (exact R3 weights, smaller completion target), per seed.
Groups: groups_DA_s*.json, groups_DB_s*.json (first packing found; fixed now, not re-drawn).

## Protocol (identical to option_B_scaled single-run criterion, copied in dyn.py)
Per memory: full 4-cell cue (cue spikes 0/0.5/1/1.5 ms), 3-cell cue a, 3-cell cue b, 500 ms apart, STDP off, dt 1 ms. An event is `clean` if: full cue -> all non-cue cells fire, 3-cell cue -> no non-cue cell fires, and no member of another memory and no non-member pyramidal cell fires in the 450 ms window. A memory "succeeds" if its 3 events are all clean. Recall success rate = successful memories / memories.
Conditions per (seed, design): background Pyr->Pyr per-pair conductance cap c = min(g, c) nS with c in {0 (pruned), 0.15 (R3 natural cap), 0.6, 1.5, 3.0}; GABA on (x1) vs silenced (SG: every Int->* pair zeroed, readback checked, interneurons still fire). Pyr->Int at weight 1 with the 10 nS cue cap (R3). 2 designs x 2 seeds x 5 c x 2 GABA = 40 short sims, one at a time or as slots allow.
Not run: scaled GABA / Pyr->Int (option_B s3-s5 g5): those exceed natural bounds; ripple multi-memory protocol; STDP.

## Baseline
Unpatched S1 (96 Pyr, ~72-86k Pyr->Pyr synapses, K=4 8-cell memories), option_B_scaled README: at c 0.15 x1 and SG all 4 memories complete 4/4, 0 false completions; runaway onset c ~0.6 (SG and x1; 0.5 an edge), no suppression by x1 GABA; seed629 onset 0.55.

## Pass/fail (see PREREGISTRATION.md for predictions)
PASS ("recall works on the sparse network"): at c 0 and 0.15 with GABA on, >= 7 of the 8 memories (DA 2 + DB 6) succeed, both seeds, with 0 false completions from 3-cell cues.
FAIL: >= 2 memories fail full-cue completion (veto) at c <= 0.15 with GABA on, or any false completion from a 3-cell cue.
Inhibition role: reported as GABA-on minus SG differences only.
Concurrency: the patched instance is shared with fable-knobs (batch 2 growth). Launch only when (growth sims + mine) <= 3; sims deleted at the end of every run.
