# Step 0 audit: does the "axons collapse to the disc centre" finding hold in the other runs? (read-only, 2026-11-15)

Files: `audit.py` (the audit, run with `python3 -I`), `table.py` (builds the table), `results.json` (all numbers), `results_table.md` (same table as below), `audit.log`. Only existing NES output folders under `/var/lib/BrainGenix/NES/Admonishing/NetmorphOutput/` were read (node text files and `.nibr.clp`). No NES/API call, no simulation, no existing file edited.

## How runs were found (read in data)
Folders were matched to runs by the parameters echoed in each folder's `.nibr.clp`: `randomseed`, `In.interneuron`, `all_interneuron_axons.B_inf`, `all_interneuron_dendrites.B_inf`, 96 pyramidal, radius 120. Folder names are NES uuids, so the link to the `grow_*` directories is by parameter match plus creation time, not by a stored path. Result: **17 of 17 requested runs found, none missing**: pv_arbor V1-V6 (seed 20240628), S1 seed 20240628, and S1/V1/V3 x seeds 31415, 27182, 16180. One extra folder matched (axon 26 / dendrite 5, seed 20240628, created 11-12 23:56, from an earlier dendrite_rerun variant, not pv_arbor V4); it is listed separately. Not available: none. Not audited: all other folders in the directory (other configs).

## Definitions
Axon nodes = continuation + bifurcation + growth-cone nodes of axons (roots excluded). Per cell, the median over its axon nodes of the distance (a) from the disc centre in xy, (b) from the cell's own soma (3D). Table cells are the mean of those per-cell medians within a soma-radius band (soma distance from the centre in xy: 0-40, 40-80, 80-120 um), shown as `centre / own soma (n cells)`. "frac r>120" = fraction of all axon nodes of that cell type more than 120 um from the centre in xy. Straight/path = mean over growth cones with path length >100 um of (straight distance from soma) / (path length along parent chain). Attractor mix = dendritic bifurcation nodes by neuron type (these are the attractor points, S/network.cc:696-706).

## Results (read in data)
| label | seed | folder (first 8) | created | ints | attractor pyr/int dend. bif (pyr %) | IN axon: dist from centre / own soma, bands 0-40, 40-80, 80-120 | IN frac nodes r>120 | IN straight/path | PYR axon: dist from centre / own soma, bands | PYR frac r>120 | PYR straight/path |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 (dendrite_rerun grow_S1 / pv_arbor ref) | 20240628 | 80dd3ce5 | 11-12 23:56 | 48 | 4676/1379 (77%) | 24/33 (n=7); 24/67 (n=22); 24/105 (n=19) | 0.0000 | 0.14 | 24/37 (n=11); 24/66 (n=28); 24/105 (n=57) | 0.0000 | 0.14 |
| pv_arbor V1 | 20240628 | 8cb66495 | 11-13 23:37 | 48 | 4764/1405 (77%) | 17/28 (n=7); 16/65 (n=22); 17/105 (n=19) | 0.0000 | 0.13 | 17/35 (n=11); 17/64 (n=28); 16/104 (n=57) | 0.0000 | 0.13 |
| pv_arbor V2 | 20240628 | 909b878c | 11-13 23:37 | 48 | 4628/1985 (70%) | 17/28 (n=7); 17/65 (n=22); 17/105 (n=19) | 0.0000 | 0.13 | 17/34 (n=11); 16/64 (n=28); 17/104 (n=57) | 0.0001 | 0.13 |
| pv_arbor V3 | 20240628 | 9a8c1832 | 11-13 23:38 | 48 | 4841/2020 (71%) | 16/28 (n=7); 16/66 (n=22); 16/104 (n=19) | 0.0001 | 0.13 | 16/34 (n=11); 16/64 (n=28); 16/103 (n=57) | 0.0002 | 0.13 |
| dendrite_rerun variant axon 26 / dend 5 (not pv_arbor V4) | 20240628 | f11dd9db | 11-12 23:56 | 48 | 4613/1388 (77%) | 19/30 (n=7); 17/66 (n=22); 18/107 (n=19) | 0.0000 | 0.14 | 18/38 (n=11); 18/66 (n=28); 18/104 (n=57) | 0.0000 | 0.13 |
| pv_arbor V4 | 20240628 | fe8d4c81 | 11-14 00:24 | 48 | 4631/2122 (69%) | 21/29 (n=7); 21/66 (n=22); 21/106 (n=19) | 0.0000 | 0.13 | 21/36 (n=11); 21/65 (n=28); 21/105 (n=57) | 0.0000 | 0.13 |
| pv_arbor V5 | 20240628 | 962a812f | 11-14 00:25 | 20 | 5418/843 (87%) | 18/34 (n=5); 17/72 (n=6); 17/105 (n=9) | 0.0000 | 0.13 | 17/33 (n=10); 17/66 (n=27); 17/104 (n=59) | 0.0001 | 0.13 |
| pv_arbor V6 | 20240628 | 7c07098c | 11-14 00:26 | 20 | 5137/882 (85%) | 15/33 (n=5); 14/71 (n=6); 14/105 (n=9) | 0.0000 | 0.15 | 14/34 (n=10); 13/66 (n=27); 14/104 (n=59) | 0.0001 | 0.13 |
| seeds S1 | 16180 | 00657198 | 11-14 23:17 | 48 | 5289/1272 (81%) | 20/47 (n=6); 19/65 (n=15); 19/108 (n=27) | 0.0001 | 0.15 | 19/34 (n=10); 19/68 (n=30); 19/103 (n=56) | 0.0001 | 0.13 |
| seeds S1 | 27182 | 57bc1c51 | 11-14 22:12 | 48 | 5418/1315 (80%) | 17/36 (n=6); 16/65 (n=17); 16/106 (n=25) | 0.0001 | 0.14 | 16/33 (n=8); 16/65 (n=33); 16/106 (n=55) | 0.0000 | 0.13 |
| seeds S1 | 31415 | 5911f275 | 11-14 21:08 | 48 | 5408/1395 (79%) | 15/36 (n=5); 15/67 (n=16); 15/100 (n=27) | 0.0001 | 0.14 | 15/31 (n=10); 15/67 (n=29); 15/108 (n=57) | 0.0000 | 0.13 |
| seeds V1 | 16180 | 76800c7f | 11-14 23:18 | 48 | 5114/1308 (80%) | 24/47 (n=6); 22/70 (n=15); 22/108 (n=27) | 0.0001 | 0.15 | 23/41 (n=10); 23/69 (n=30); 22/104 (n=56) | 0.0001 | 0.13 |
| seeds V1 | 27182 | 0ce88bc3 | 11-14 22:13 | 48 | 5106/1387 (79%) | 17/37 (n=6); 16/66 (n=17); 16/107 (n=25) | 0.0001 | 0.14 | 16/34 (n=8); 16/65 (n=33); 16/106 (n=55) | 0.0000 | 0.14 |
| seeds V1 | 31415 | 5be815b3 | 11-14 21:09 | 48 | 5651/1370 (80%) | 18/40 (n=5); 17/68 (n=16); 17/101 (n=27) | 0.0001 | 0.14 | 18/34 (n=10); 18/68 (n=29); 18/108 (n=57) | 0.0001 | 0.13 |
| seeds V3 | 16180 | 73629008 | 11-14 23:19 | 48 | 5222/1967 (73%) | 17/41 (n=6); 16/67 (n=15); 16/106 (n=27) | 0.0001 | 0.14 | 17/35 (n=10); 16/66 (n=30); 16/104 (n=56) | 0.0001 | 0.14 |
| seeds V3 | 27182 | a9b22b82 | 11-14 22:13 | 48 | 5016/2132 (70%) | 34/51 (n=6); 31/63 (n=17); 33/104 (n=25) | 0.0002 | 0.14 | 34/40 (n=8); 33/69 (n=33); 32/108 (n=55) | 0.0000 | 0.14 |
| seeds V3 | 31415 | 893decd3 | 11-14 21:09 | 48 | 5432/1986 (73%) | 19/40 (n=5); 18/68 (n=16); 18/100 (n=27) | 0.0001 | 0.15 | 19/34 (n=10); 18/68 (n=29); 19/109 (n=57) | 0.0001 | 0.14 |

## Verdict
**Read in data:**
- The collapse holds in all 17 runs, for interneuron and pyramidal axons alike. Median axon-node distance from the centre is 14-34 um (15-24 um in 15 of 17 runs) in every soma-radius band, while distance from the own soma rises with the band (about 30-50, 63-72, 100-109 um). Axon nodes beyond r = 120 um: at most 0.02% of nodes in any run. Straight/path ratio is 0.13-0.15 in every run and cell type.
- Interneuron and pyramidal axons give the same numbers in each run (differences of 1-2 um from the centre), so the collapse is not interneuron-specific.
- Differences by variant: none systematic. Centre distance (pooled over bands) by variant, seed 20240628 then 31415, 27182, 16180: S1 24, 15, 16, 19; V1 17, 18, 16, 22-24; V3 16, 18-19, 31-34, 16-17. V1-V6 of pv_arbor are 14-21. One outlier: V3 seed 27182 (about 33 um, 31-34 in all bands; same in pyramidal axons), so the whole network's axon cloud sits further from the centre in that realisation. The 20-interneuron runs (V5, V6) are 14-18, the lowest.
- By seed: the spread between seeds (15-24 um for S1 and V1) is similar to the spread between variants. Nothing separates S1 from V1 or V3 except the V3 s27182 outlier.
- Attractor mix is 69-87% pyramidal. S1 and V1: 77-81%. V3 and V2 (dendrite B_inf 5): 70-73%. The 20-interneuron runs: 85-87%. So interneuron dendritic points are at most 31% of attractor points in any run.

**Inference (not tested):**
- Because the same numbers appear for pyramidal and interneuron axons and for every B_inf, the cause is shared by all axons, which fits the centroid-attraction reading in KNOB_SCOUT.md section 0. This audit does not prove the cause: no run varied the attraction weight, so the dependence on `dm_weight` is untested (that is Test 1).
- The V3 s27182 outlier may reflect a shifted attractor centroid in that realisation (not checked).
- Per-type chemical labels would change at most about 13-31% of attractor points, so label-based target selection remains a weak lever.

Limits: the median-of-medians hides cells with wide axons (I did not report per-cell outliers); bands have 5-27 interneurons each; folder-to-run mapping is by parameters; all runs share dm.weight 0.9 and one attraction setup, so nothing here shows how the collapse changes with the weight.
