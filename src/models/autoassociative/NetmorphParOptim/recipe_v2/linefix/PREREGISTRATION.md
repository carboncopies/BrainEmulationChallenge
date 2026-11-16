# Preregistration: line-379 fix (frac_T_PQ = tx/PQ), patched NES build, D_synmax unchanged
Written 2026-11-15 before any run of the patched build. Not to be edited after launch. Ledger task tmwidgz0z.

## What is run
- Patched build: copy of the NES main tree at /home/johnjose/BrainGenix/wt/nes-linefix, one line changed (line379_fix.diff), separate NES on port 8011 with its own API on 8010 (callback 8009) and its own output folder. The running NES/API (8001/8000/7999) is not touched.
- Runs: S1, V1, V3 at seed 16180, 3 concurrent. Parameters identical to ../pv_arbor_seeds (D_synmax 1.5 pyr-pyr, 0.1 for the three interneuron pairs, radius 120, thickness 30, 96 pyr, 48 int, dm.weight 0.9, days 25). Baselines: the existing seed-16180 runs in ../pv_arbor_seeds (unpatched binary, not re-run).
- Metrics: same analyze/measure/xdir code as pv_dsyn015 (only paths changed).

## Basis of the predictions
FABLE_ANALYSIS 1.3: the unpatched test passes about 7.7% of true crossings at D 0.1 and about 35% at D 1.5 (derived from measured segment lengths; the D 0.15 check of the same model predicted x1.94 and x2.05 was measured). With the fix every true crossing within D passes. So interneuron-pair counts should rise about x13 and Pyr->Pyr about x2.9. The synapse test does not feed back into growth (arbors were identical in the D 0.15 runs).

## Predictions (point; range)
Baseline seed 16180: S1 PP 73105, PI 348, IP 1616, II 685 | V1 70921, 461, 876, 509 | V3 86230, 573, 1364, 717.
1. Arbors unchanged: interneuron axon and dendrite length ratio 1.000 (allow 0.99-1.01 because 1 of 9 earlier same-seed runs diverged slightly); reach ratio 0.98-1.02.
2. Interneuron-pair synapse counts, ratio to baseline x13 (9-18) for each of Int->Pyr, Pyr->Int, Int->Int:
   - S1: Int->Pyr 21,000 (14,500-29,000); Pyr->Int 4,500 (3,100-6,300); Int->Int 8,900 (6,200-12,300)
   - V1: Int->Pyr 11,400 (7,900-15,800); Pyr->Int 6,000 (4,100-8,300); Int->Int 6,600 (4,600-9,200)
   - V3: Int->Pyr 17,700 (12,300-24,600); Pyr->Int 7,450 (5,200-10,300); Int->Int 9,300 (6,500-12,900)
3. Pyr->Pyr ratio x2.9 (2.0-4.0): S1 212,000, V1 206,000, V3 250,000. This is a large change to the excitatory network and is NOT within the old "Pyr->Pyr within 5%" rule; that rule compared growth variants and cannot hold across a change of the synapse test.
4. Synapses per connected Int->Pyr pair: S1 5.1 (4.0-6.5), V1 3.2 (2.5-4.2), V3 4.5 (3.5-5.8). Below the PV target of about 11 in all three.
5. Pyramidal targets per interneuron (of 96): S1 85 (75-93), V1 75 (62-86), V3 82 (72-91).
6. Inhibitory fraction A = Int->Pyr/(Int->Pyr+Pyr->Pyr): S1 9.0% (5-15), V1 5.3% (3-9), V3 6.6% (3.8-11). B = (Int->Pyr+Int->Int)/all: S1 12%, V1 8%, V3 9.5% (each +-4 points). So I expect S1 to overshoot the 3-6% band, V1 to be nearest to it.
7. Drivable interneurons, 8-cell criterion: 44 of 48 (36-48) in each variant; at least 16 in all three runs with 95% confidence. Zero-input interneurons 0-2.
8. +x share of Int->Pyr synapse-carrying axon segments (cos > 0.9): 4-7% (baseline 57%; all-segment share 4.7-4.8%).
9. bio_check passes (no parameter changes); wall time 1.0-1.6x baseline.

## What would count against the bug explanation
Interneuron-pair ratio below x5, or +x share above 15%, or arbor lengths changing by more than 1%.

## Reading rule for "biologically faithful"
No parameter leaves bio_ranges.json (none is changed). Movement toward PV targets is judged on: synapses per pair toward 11, A within 3-6%, drivable 8-cell >= 16. An overshoot of the inhibitory fraction, or a Pyr->Pyr count that is too high for the functional model, is reported as such, not tuned away in this step.
