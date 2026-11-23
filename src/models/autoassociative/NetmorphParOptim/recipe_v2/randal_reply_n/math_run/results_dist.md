## Part 1: distributed-cue assemblies (c cue + 2 targets), best of 5 greedy restarts; median (min-max) over 10 models
| variant | c | k | candidates (median) | memories median (min-max) | models >= 1 | models >= 5 (k=0) / >= 6 (k=2) | cell budget bound 96/(c+2) |
|---|---|---|---|---|---|---|---|
| primary | 8 | 0 | 70 | 2 (1-3) | 10 | 0 | 9 |
| primary | 8 | 2 | 70 | 6 (3-8) | 10 | 6 | 9 |
| primary | 12 | 0 | 187.5 | 2 (0-2) | 9 | 0 | 6 |
| primary | 12 | 2 | 187.5 | 5 (0-6) | 9 | 4 | 6 |
| primary | 17 | 0 | 0 | 0 (0-0) | 0 | 0 | 5 |
| primary | 17 | 2 | 0 | 0 (0-0) | 0 | 0 | 5 |
| primary | 20 | 0 | 2384 | 1 (0-2) | 8 | 0 | 4 |
| primary | 20 | 2 | 2384 | 2 (0-3) | 8 | 0 | 4 |
| Hinf | 8 | 0 | 85.5 | 3 (2-3) | 10 | 0 | 9 |
| Hinf | 8 | 2 | 85.5 | 9 (5-10) | 10 | 9 | 9 |
| Hinf | 12 | 0 | 194 | 2 (1-2) | 10 | 0 | 6 |
| Hinf | 12 | 2 | 194 | 5 (1-7) | 10 | 3 | 6 |
| Hinf | 17 | 0 | 0 | 0 (0-0) | 0 | 0 | 5 |
| Hinf | 17 | 2 | 0 | 0 (0-0) | 0 | 0 | 5 |
| Hinf | 20 | 0 | 2383 | 1 (0-2) | 8 | 0 | 4 |
| Hinf | 20 | 2 | 2383 | 2 (0-3) | 8 | 0 | 4 |

### Biological statistics of the primary designs (pooled over models with >= 1 memory)
| c | k | models with design | designed pairs (mean) | synapses per designed pair median [mean over models] | share of designed pairs with >=5 synapses | share single-synapse | weight median [min-max] | share w>=0.9 | x max (nS) | max non-hub input (nS) | active fraction | independent check (bounds, w-range, H, no-new-pair, Dale) | cascade 16.5: full exact / sub-cue clean | cascade 15.0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 | 0 | 10 | 35.2 | 4.0 [4.4] | 0.19 | 0.00 | 0.53 [0.18-0.70] | 0.00 | 2.06 | 47.6 | 0.104 | ALL OK | 22/22, 704/704 | 22/22, 704/704 |
| 8 | 2 | 10 | 92.8 | 4.0 [4.3] | 0.18 | 0.00 | 0.53 [0.18-0.70] | 0.00 | 2.06 | 49.0 | 0.104 | ALL OK | 58/58, 1856/1856 | 58/58, 1856/1856 |
| 12 | 0 | 9 | 45.3 | 3.5 [3.5] | 0.10 | 0.00 | 0.41 [0.14-0.70] | 0.00 | 1.38 | 46.7 | 0.146 | ALL OK | 17/17, 544/544 | 17/17, 544/544 |
| 12 | 2 | 9 | 114.7 | 3.0 [3.3] | 0.09 | 0.00 | 0.47 [0.11-0.70] | 0.00 | 1.38 | 46.7 | 0.146 | ALL OK | 43/43, 1376/1376 | 43/43, 1376/1376 |
| 17 | 0 | 0 | | | | | | | | | | | | |
| 17 | 2 | 0 | | | | | | | | | | | | |
| 20 | 0 | 8 | 55.0 | 1.2 [2.0] | 0.03 | 0.48 | 0.74 [0.11-0.84] | 0.00 | 0.83 | 46.4 | 0.229 | ALL OK | 11/11, 352/352 | 11/11, 352/352 |
| 20 | 2 | 8 | 95.0 | 2.0 [2.0] | 0.03 | 0.45 | 0.42 [0.11-0.84] | 0.00 | 0.83 | 46.4 | 0.229 | ALL OK | 19/19, 608/608 | 19/19, 608/608 |