# Preregistration: D_synmax 0.1 -> 0.15 on the three interneuron pairs (written before launch; not edited afterwards)
Written 2026-11-15. Runs: S1, V1, V3 at seed 16180, only change vs the baselines in ../pv_arbor_seeds (S1_s16180, V1_s16180, V3_s16180) is D_synmax.pyramidal.interneuron / interneuron.pyramidal / interneuron.interneuron = 0.15 (pyramidal.pyramidal stays 1.5). Prediction source: ../knob_scout/FABLE_ANALYSIS.md sec. 1 (x1.94, plausible 1.8-2.1, same arbors).
Baselines (seed 16180, D 0.1): S1 Pyr->Pyr 73105, Pyr->Int 348, Int->Pyr 1616, Int->Int 685, syn/pair 1.60, targets/int 21.0, A 2.16%, B 3.04%, drivable 8-cell 2 (simple 8), zero-input 14. V1: 70921, 461, 876, 509, 1.38, 13.3, 1.22%, 1.90%, 4 (11), 17. V3: 86230, 573, 1364, 717, 1.56, 18.3, 1.56%, 2.34%, 2 (14), 12.

## Predictions
1. Arbors unchanged. Interneuron axon and dendrite length within +-10% of baseline (my expectation: within +-3%, since D_synmax acts only on synapse acceptance; if the synapse test consumes random numbers the realisation may differ slightly). Pyr->Pyr within +-15% of baseline (my expectation +-3%; the pyramidal pair is untouched). Reach unchanged (+-5%).
2. Synapse counts (Fable x1.94; my own range x1.7-2.2 per run, given Poisson-like noise of 3-5% at these counts plus any realisation change):
   - S1: Int->Pyr 3135 (2750-3550), Pyr->Int 675 (590-770), Int->Int 1330 (1160-1500)
   - V1: Int->Pyr 1700 (1490-1930), Pyr->Int 894 (780-1010), Int->Int 987 (860-1120)
   - V3: Int->Pyr 2646 (2320-3000), Pyr->Int 1112 (970-1260), Int->Int 1391 (1220-1580)
3. Syn/pair Int->Pyr: rises less than the synapse count because new synapses fall partly on already-connected pairs; connected pairs rise about x1.5 (x1.35-1.7), syn/pair by x1.1-1.3: S1 1.9 (1.75-2.1), V1 1.6 (1.5-1.8), V3 1.8 (1.65-2.0). Targets per interneuron: S1 31 (28-35), V1 20 (18-23), V3 27 (24-31).
4. Inhibitory fraction (computed from the predicted counts): A: S1 4.1% (3.7-4.5), V1 2.3% (2.1-2.6), V3 2.9% (2.6-3.2). B: S1 5.7%, V1 3.6%, V3 4.4% (each +-0.4).
5. Drivable 8-cell (baseline 2/4/2): S1 6 (3-10), V1 8 (5-12), V3 7 (4-11); simple count: S1 18 (14-24), V1 20 (15-26), V3 24 (19-30); zero-input interneurons: S1 7 (4-11), V1 9 (5-13), V3 6 (3-10). No run reaches 16 on the 8-cell criterion (probability about 90%).
6. Direction check (read-only, if computable): fraction of Int->Pyr synapse-carrying axon segments with cosine to +x > 0.9 falls from the baseline-style 57% to about 45% (38-52%), because the wider acceptance admits more oblique segments.

## Scoring rule (applied later)
- Main claim (Fable's stop rule): HIT if, for each of the three pathways, the ratio new/baseline summed over the three variants is within 1.8-2.1 AND arbor lengths and Pyr->Pyr stay within the +-10% / +-15% bounds. PARTIAL if the pooled ratio is within 1.6-2.3 (or in range but one run outside 1.6-2.3). MISS if the pooled ratio is outside 1.6-2.3 for any pathway, or the arbors change beyond the bounds.
- Items 2-5 numbers: hit = observed inside my stated range, partial = within 25% outside the range, miss otherwise. Item 6: hit if inside 38-52%, otherwise miss; skipped if not computable.
