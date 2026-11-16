# dynamics_c PREREGISTRATION (written 2026-11-16 before any simulation; not edited after launch)
Predictions (probabilities in brackets are my confidence). "Memory" = DA (1 per seed) or DB (3 per seed); 8 memories in total across both seeds; SG = GABA silenced.
P1. c = 0 and 0.15, GABA on: all 8 memories succeed (full cue completes all non-cue cells, both 3-cell cues 0 false completions, no spurious Pyr spikes). [85% for DA; 70% for all 8 together]. SG identical to GABA on at these c. [85%]
P2. Latency of last non-cue spike after cue within 3.5-5.5 ms; interneurons fire few spikes (< 10 per memory trial) at c <= 0.15. [65%]
P3. Runaway (sustained spurious non-member Pyr activity, > 50 non-member spikes) does not occur at c <= 0.6 in any SG run [80%], does occur in at least one SG run at c = 3.0 [65%]. Reasoning: S1 had ~9k pairs and onset at c ~0.6; here ~2.3k pairs (x0.25) so onset should move to ~2.4 nS, uncertain by 2x.
P4. GABA on shifts the runaway onset by at most one grid step relative to SG (x1 GABA did not suppress in S1). [75%]
P5. Veto by inhibition (full cue fails to complete in GABA-on but completes in SG) occurs in at most 1 of the 8 memories at c <= 0.6. [75%]
P6. Overall verdict: PASS as defined in PLAN.md. [75%]
Scoring: each P marked HIT / MISS / PARTIAL against the table in README.md.
