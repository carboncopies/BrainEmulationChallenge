# Preregistration (written before any run; not edited afterwards)
Written 2026-11-14. New seeds: 31415, 27182, 16180 (original seed 20240628 gives S1=7, V1=6, V3=10 drivable 8-cell). Variants S1 (axon 26, dend 3.5), V1 (20, 3.5), V3 (23, 5); 48 interneurons, everything else as pv_arbor/README.md.
Basis: single-seed numbers in pv_arbor/README.md and its remark that realisation noise is about +-20%. Predictions are for the 3 new seeds, with the original seed given for the 4-seed statistics.

(a) Drivable 8-cell count per variant (mean over the 3 new seeds; SD = between-seed SD of single runs; range over the 3 new runs):
- S1: mean 7, SD 2, range 4-10
- V1: mean 6, SD 2, range 3-9
- V3: mean 7.5 (regression toward the mean from the original 10), SD 2.5, range 4-11
Predicted 4-seed best variant mean: V3 or S1, with no variant mean above 9.

(b) V3 > V1 on drivable repeats: V3 mean > V1 mean over the 3 new seeds, probability about 60%. V3 > V1 in all 3 seeds individually: about 20%. The original +4 gap shrinks to about +1.5, not distinguishable from noise (difference within 1 SD of the between-seed spread).

(c) Seed-to-seed spread of Pyr->Pyr (identical pyramidal config except seed): SD about 10% of the mean (mean about 58,000 synapses, SD about 6,000), max/min ratio across the 4 seeds of one variant about 1.25 (range of +-15%). Spread within each variant similar; no systematic variant effect on Pyr->Pyr.

(d) Any run reaching 16 drivable (8-cell) of 48: no. Probability that at least one of the 9 new runs reaches 16: 3%. Maximum over the 9 new runs predicted 10-11.

Scoring rule (to be applied later): hit = prediction within stated numbers / correct direction; partial = right direction but numbers outside, or about half of the sub-claims right; miss = otherwise.
