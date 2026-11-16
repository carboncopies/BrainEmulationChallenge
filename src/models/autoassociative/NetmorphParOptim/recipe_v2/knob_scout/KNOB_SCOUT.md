# NetMorph knob scout for interneuron connectivity (read-only, nothing run), 2026-11-15

Tags: **[CODE]** = read in NetMorph source (path relative to `BrainGenix-NES/ThirdParty/NetmorphCMake/Source/`, called `S/`). **[REPORT]** = read in a `<ts>_report` file of one of our own grown networks. **[DATA]** = I computed it read-only from the node/synapse text files of one existing grown network. **[INF]** = my inference, not tested. Nothing was simulated, no NES/API call, no existing file edited, `bio_ranges.json` untouched.

## 0. Headline findings (read this first)

1. **[DATA] Axons do not stop short. They collapse to the centre of the disc.** In the one network I audited (seed 16180, interneuron axon B_inf 26; its 1616 Int->Pyr synapses match S1 s16180 in `pv_arbor_seeds/README.md`):
   - Interneuron axon tips have a path length from the soma of median 616 um (p90 838, max 1935), but their straight-line distance from the soma averages only 88 um. Straight-line/path ratio is 0.13-0.15. Pyramidal axons are the same (path 746, straight 85).
   - Median axon node distance from the **disc centre** is 19 um for interneurons whose somata are at 0-40, 40-80 and 80-120 um from the centre alike. Their median distance from **their own soma** is 45, 64 and 108 um. Correlation of soma radius with axon-node radius is -0.20. 99% of axon nodes lie within 55 um of the centre although somata reach r = 117 um.
   - So "axon reach 125-133 um" is mostly the soma-to-centre distance, and it is not a growth-time or length limit.
2. **[CODE]+[REPORT] The cause is almost certainly the `cell_attraction` direction contributor.** Every neuron is both attractor and attracted (`In.attractedto=NGF_A; In.attractors=NGF_A`, 144 of 144 neurons in the report). Every dendritic bifurcation point becomes an attractor point. Each turn, a growth cone's direction is `unit(history) + 0.9 * unit(sum of 1/d^2 vectors to ALL attractor points)`. The attraction vector is normalised to unit length, so its strength does not fall with distance, and there is no range cutoff (S/axon_direction_model.cc:639-651, 737-748). Points are spread over a disc, so the net pull always points to the centre.
3. **[DATA] Attractor mix is already about 81% pyramidal** (5289 pyramidal vs 1272 interneuron dendritic bifurcation points). Per-cell-type chemical labels would therefore change target preference by at most 19 points. This is a weak lever.
4. **[DATA]+[INF] Synapses per pair (1.6) is the low-crossing regime, not a cap.** 1007 Int->Pyr pairs with 1616 synapses: 660 pairs (66%) have 1 synapse, 21% have 2, 7% have 3, max 11. Zero-truncated Poisson with lambda 1.03 reproduces the mean but not the shape (predicts 57/30/10% for 1/2/3). Synapses form only where a pre and post segment centre-line pass within D_synmax (S/synapse_formation_model.cc:134-200), so the count per pair is the number of crossings. **[CODE]** The source says multiple synapses per segment pair are not implemented (:114-116), and `P_receptor` is a probability <= 1, so no knob raises per-pair count above the crossing count. Direction knobs cannot give 11 per pair. They can only move targets per interneuron and, indirectly, crossing density.
5. **[CODE] D_synmax is the one direct count lever, and part of its allowed range is unused.** Hard limit for the three interneuron pairs is max 0.15 (bio_ranges.json), our runs use 0.1 (grow_pv.py). `pv_arbor/README.md` says raising D_synmax "is outside the allowed range", which contradicts bio_ranges.json (max 0.15). Please check; I did not change anything.
6. **[CODE]+[REPORT] Veer angle is 0.20-0.79 rad (11-45 deg) per turn, turn every 5 um** for all axons (`all_axons` restates the direction model, so it does not inherit the universal 0.0-0.75; report lines 160-168, 199-205). **[INF]** Taken alone this gives a persistence length of about 35 um, i.e. a rms displacement of about 200 um for a 630 um path. The observed 88 um is about 2.3x lower, consistent with the centroid pull on top.
7. **No lateral tissue boundary found [CODE, not exhaustive].** The only physical boundary is the spherical pia (centre z -50000, radius 50000, maxrange 100, S/environment_physics.cc:130-190). The slab is at z about -300, so the boundary field (within 100 um of z=0) never reaches it. Earlier notes (AXON_LEVER_FINDINGS section 1) guessed cones "stall at the disc boundary"; I found no code for that and the data show no axon node beyond r = 140.

## 1. Catalogue

"Hard limits" = `bio_ranges.json`: days 20-25, pyramidal 16-128, interneuron 16-128, minsep 10-15, radius 100-200, thickness 20-50, dm.weight 0.1-1.0, D_synmax pyr-pyr 0-1.5, other three pairs 0-0.15; growth_F 0.39 and growth_nu0 0.00013889 fixed (universal set). "Randal" column = does the guidance relayed in the task (extent of interneuron arbor, high proportion of pyramidal contacted, natural arborization overrides built-in specs, default interneuron outgrowth may be wrong) cover it? Y = directly, P = partly, N = no.

Common syntax rule **[CODE]** (S/axon_direction_model.cc:787-830, same pattern as ARBOR_DESIGN 1.1): a per-type directive is read only when the model is selected on that set. To change anything about interneuron-axon direction you must restate the whole chain under `all_interneuron_axons.`: `direction_model=segment_history_tension; dm_label=axondm; axondm.dm_weight=..; axondm.direction_model=cell_attraction;` plus `veeranglemin/max` and `history_power`. A fresh model takes veer defaults from `global turnanglemin/max` (pi/16..pi/4, S/axon_direction_model.cc:201, S/global.hh:652-653), not from the universal 0..0.75. A lone `all_interneuron_axons.veeranglemax=..` is silently ignored **[CODE]**. Report check: `Subset 'all_interneuron_axons.' direction model` block must show the new numbers.

### (a) Axon reach / spatial extent
| # | Knob (config key) | Where | Default | What it does | Our value | Hard limit | Randal |
|---|---|---|---|---|---|---|---|
| a1 | `<set>.axondm.dm_weight` (our file: `all_axons.axondm.dm_weight`) | S/axon_direction_model.cc:238; set from Excel `dm.weight` in `gen_autonm_labels.py:734` | none (Randal's base file 0.2) | Weight of the attraction contributor relative to the tension model (weight 1.0). Attraction is unit-normalised then multiplied by this, so it sets how hard axons are pulled to the dendrite-point centroid [CODE] | 0.9 for all axons [REPORT contrib.w=0.90] | Param `dm.weight` 0.1-1.0. A per-type override inside 0.1-1.0 is inside the number but whether it counts as the limited parameter is a question | Y (extent, natural arborization) |
| a2 | `<set>.veeranglemin / veeranglemax` | :215-232, default :201 | pi/16, pi/4 | Random angular perturbation applied to the predicted direction at every turn; sets axon curliness | 0.20 / 0.79 for all axons [REPORT] | none | P |
| a3 | `<set>.history_power` | :313, used :370 | 2 | Tension model weight of past segments = mass / distance^p. p=2 means the previous 5-um segment carries about 80% of the history weight, so direction memory is short. p=0 means the whole history since the last branch point counts equally (much straighter) [CODE] | 2.0 [REPORT] | none | P |
| a4 | `<set>.turn_separation` / `turn_rate`, `<set>.TSTM=linear_rate` | S/turning_models.cc:228-231 | 10 um (rate 0.1/um; a restated TSTM falls back to 0.1) | Mean length between turns | 5 um (0.2/um) [REPORT] | none | P |
| a5 | `turnanglemin/max` (global) | S/global.cc:115-123 | pi/16, pi/4 | Default for all veer angles | unset | none | N |
| a6 | `dirhistory_selection`, `general_rtdhs_*` | :64-75 | none | Random truncation of the history | none | none | N |
| a7 | `<set>.axondm.direction_model=radial` + `.Samsonovich_hypothesis=true` | :427, :470-500 | n/a | Expected direction = outward from the soma centre, contributes with its own weight. A way to give interneuron axons an explicit outward bias instead of (or beside) centroid attraction | not used | none | P |
| a8 | `<set>.axondm.direction_model=vector` + `.direction=<vec>` | :502 | n/a | One fixed direction for all cones. Not natural | not used | none | N |
| a9 | `all_interneuron_axons.arbor_elongation_model`, `.growth_nu0`, `.growth_F`, `.F_competes_with` | S/fibre_elongation_model.cc:152-166 | interneuron axons inherit pyramidal-axon nu0 45 um/day, F 0.16 [REPORT line 133] | Total arbor elongation. Manual examples slow interneuron axons to nu0 0.0001. Randal's remark "default interneuron outgrowth may be wrong" points here | inherited | universal growth_F/nu0 are team-fixed; whether that fixes the interneuron-axon override is unclear | Y, but ARBOR_DESIGN row 10 excluded it as a rule |
| a10 | `all_interneuron_axons.B_inf, tau, E, min_node_interval` | S/branching_models.cc:55-66, 207-220 | restated, see grow_pv.py | Branch count / timing | B_inf 20/23/26 | none | exhausted |
| a11 | `pia.*` boundary | S/environment_physics.cc:52-190 | | Spherical repulsion near z=0 only | maxrange 100, c_repulse 0.2; not reached by slab at z -300 [INF from geometry] | none | N |
| a12 | `all_interneuron_axons.L0`, initial axon direction | S/fibre_structure.cc:1111; initial direction random S/neuron.cc:530 | 9-11 um [REPORT line 121] | Negligible; initial direction is random, not settable | | none | N |

### (b) Synapses per pre-post pair
| # | Knob | Where | Default | What it does | Our value | Hard limit | Randal |
|---|---|---|---|---|---|---|---|
| b1 | `D_synmax.<pre>.<post>` | S/synapse_formation_model.cc:50, :134, default table S/synapse_formation_model.hh:251-270 | pyr rows 1.0 / 0.1 vs interneuron; interneuron row 0.1 | Centre-line distance within which a crossing becomes a candidate synapse. Fibre radius is not subtracted [CODE, per ARBOR_DESIGN 3.4]. Earlier measurement: count scales about as D^1.6 [ARBOR_DESIGN 3.3; not re-measured] | pyr-pyr 1.5; the three interneuron pairs 0.1 | max 1.5 / 0.15 / 0.15 / 0.15 | N (team limit) |
| b2 | `P_receptor.<pre>.<post>.GABAR` etc. | :45, :495 | Int->Pyr GABA 1.0 | Probability per candidate; already 1 | default | none | N |
| b3 | `synapse_formation.PDF` | :46, :493 | uniform | Acceptance test; likelihood is 1 so already saturated [INF] | default | none | N |
| b4 | `include_spines` | :51 | false | Tags spines; no extra synapses traced [INF] | default | spine_length 0.5-2.0 | N |
| b5 | Multiple synapses per segment pair | S/synapse_formation_model.cc:114-116 (comment) | not implemented | **No knob exists** [CODE] | | | N |
| b6 | Soma or proximal targeting (basket boutons on somata) | synapse code is fibre-to-fibre only [CODE for :97-200, not exhaustive]; the synapse file has only BASAL / APICAL location tags [DATA] | | **No knob found.** Needs code change or NES-side post-processing | | | P |
| b7 | Crossing density itself | emerges from axon length, tortuosity, overlap | | Per-pair count is about lambda = crossings. With d fixed, lambda ~ axon length in the target's dendritic field x dendrite length [INF] | lambda about 1 | | Y (extent) |

### (c) Which targets an axon contacts
| # | Knob | Where | Default | What it does | Our value | Hard limit | Randal |
|---|---|---|---|---|---|---|---|
| c1 | `<region>.attractors`, `<region>.attractedto` | S/network.cc:1160-1195 | none | Chemical labels. Applies to all neurons of the region, both types | `In.attractedto=NGF_A; In.attractors=NGF_A` (Randal's base file) | none | Y (target selection) |
| c2 | `idx.<region>.<type>.<n>.attractors / attractedto` | S/network.cc:232-272, 290-305, 363; S/neuron.cc:435-460 | none | Per-neuron labels; additive (cannot remove a region-level label) [CODE]. Would allow pyramidal-only labels for interneuron axons, 144 lines of config. Not tested whether NES passes `idx.` lines through [unverified] | unused | none | Y |
| c3 | `soma_attraction_weight` (global) | S/network.cc:222, S/network.hh:195 (default 1.0) | 1.0 | Scales attraction to somata; only dendrite points count when 0.0 | 0.0 (base file) | none | Y |
| c4 | `detailed_chemical_factors` | S/network.cc:220 | false | Enables dendrite-bifurcation attractor points | true | none | N |
| c5 | `<set>.axondm.neuron_specific_attraction_switch` | S/axon_direction_model.cc:573, used :664-668, 687-692 | false | When true, a neuron's dendrite points stop attracting an axon that already has a connection to it. Connections are created at candidate time during growth [CODE: S/Spatial_Segment_Subset.cc:273,280; S/synapse_formation_model.cc:~185; S/neuron.cc:503-509], so the test is live during growth | false | none | Y |
| c6 | `<set>.axondm.attraction_moderation_base` | :572, :602-612 | 1.0 (off) | Attraction toward a target is divided by base^(number of input connections the target has). Needs base > 1 | off | none | Y |
| c7 | `<set>.axondm.single_attractor_per_growthcone` | :574, :718-725 | false | Each cone follows one chemical only; useless with a single label | false | none | N |
| c8 | `<set>.branch_angle_model` (Balanced_Forces, fork_main_daughter) and `.bam.bfbam.*` PDF | S/branching_models.cc:576-579, :795 | normal mean pi/2, std 0.5 | Branch divergence angle | default [REPORT line 256] | none | P |

### (d) Interneuron vs pyramidal growth rules
| # | Knob | Where | Default | Notes | Our value | Hard limit |
|---|---|---|---|---|---|---|
| d1 | Set resolution: interneuron axons use `all_interneuron_axons.*`, not `In.all_axons.*` | S/prepost_structure.cc:33-45; S/neuron.cc:158-161 (per ARBOR_DESIGN/AXON_LEVER, not re-read by me) | | `In.all_axons.*` is inert for our cells | `In.all_axons.*` present, inert | n/a |
| d2 | `interneuron.min_basal / max_basal / basal.minangle/maxangle` | S/neuron.cc:957-960 (per ARBOR_DESIGN) | 2 / 4 | Interneuron dendrite roots | 6-10 | none |
| d3 | `interneuron.max_axons` | S/neuron.cc:1190, 1212 | 1 | Hard-coded one axon | 1 | none |
| d4 | `all_interneuron_dendrites.*` | as in ARBOR_DESIGN | | Affects Pyr->Int / Int->Int, not Int->Pyr | B_inf 3.5/5 | none |
| d5 | Interneuron-specific direction chain | see a1-a7 | cloned from `all_axons` | **Not used so far**; interneuron axons are steered exactly like pyramidal axons | cloned | dm.weight range |

## 2. Ranked shortlist

Read vs inferred is marked per claim.

**1. Interneuron-axon attraction weight (a1), restated chain, other values unchanged.**
- Mechanism. Read: centroid pull, unit-normalised, no range limit, weight 0.9 (code and report). Read in data: axon nodes sit at the disc centre regardless of soma position. Inferred: lowering the weight (0.1 is the hard-limit minimum) spreads interneuron axons around their own somata, to about the veer-random-walk scale of 200 um or more (inferred above), roughly doubling reach.
- Direction and size of the effect on what we care about is **uncertain and may be negative**. Inferred: with fixed axon length, spreading dilutes axon density and the crossing count falls. The earlier Phase0 regression (`scope_offline/A/RESULTS_tables.md:173-177`) found `log dm.weight` coefficients of +1.3 for usable Int->Pyr (global weight, different networks), i.e. weaker attraction tended to give fewer connections. Targets per interneuron could rise (more cells in reach) while synapses per pair stay about 1.5 and Int->Pyr totals fall.
- Value even if connectivity does not rise: it tests Randal's extent claim directly and tells us whether the centre collapse is the whole story.
- Risk. Low for pyramidal arbors (set-specific; **read**: report shows separate `all_interneuron_axons.` block). Random-number stream shifts, so Pyr->Pyr moves by seed-like noise (10-15% SD). Axon length outside the slab finds no dendrites. Randal-covered: yes.

**2. Target diversification in cell attraction (c5, optionally c6), at weight 0.9.**
- Mechanism. Read: with the switch on, an axon that already has a connection to a neuron is no longer pulled toward that neuron's dendrite points, so the pull goes to neurons not yet contacted (`!n->is_connected_to(target)`). c6 divides the pull toward heavily-innervated targets.
- Expected effect (inference): targets per interneuron up by about 20-50% (V1 baseline 13.3), synapses per pair slightly down (floor is 1.0), Int->Pyr total about flat. It acts at fixed axon length, so it is the cleanest test of "proportion of pyramidal cells contacted". Risk: the pull is still toward the centre cluster, so the effect may be small. Randal-covered: yes (target selection).

**3. D_synmax.interneuron.pyramidal (and the other two interneuron pairs) 0.1 -> 0.15 (b1).**
- Read: max allowed 0.15, unspent. Inferred effect from the old D^1.6 scaling: crossing count x1.5 to x1.9, so synapses per pair about 1.6 -> 2.0-2.3 and more pairs contacted. Small but near-certain. Not a new knob and not Randal's lever, but it is inside the hard limit. Flagged because the README says the range is closed.

**4. Straightness family (a2 veer, a3 history_power, a4 turn_separation), only together with 1.**
- Read: veer 0.20-0.79 every 5 um. Inferred: with attraction at 0.9, reducing veer may make axons converge to the centre even more tightly (veer is the only noise spreading them), so alone it may lower reach. With a lowered weight (1) it should lengthen straight runs and push reach beyond the disc (axon leaves the dendrite cloud, so density falls). A 2x2 design (weight x veer) is the follow-up if 1 shows reach moves.

**5. Outward radial bias or soma-targeting chemical labels (a7, c2, c3).** Largest design freedom, least understood. a7 could give PV-like radial fans but would be a non-NetMorph-default shape; c2/c3 need 144 idx lines and a global `soma_attraction_weight` that also affects pyramidal axons. Per finding 3, label-based selectivity can move at most 19% of the attractor points. Treat as a question for Randal first.

Not recommended: a9 (outgrowth rate; the data show path length 600-750 um per tip, so reach is not rate-limited), b6/b5 (no knob).

## 3. Minimal test designs for the top 2 (not run)

Common to both: `grow_pv.py` copy (new folder, not editing the existing one) with CFG entry based on **V1** (axon B_inf 20, dend B_inf 3.5, 48 interneurons, basal 6-10), because V1 is the length-matched config (axon 45k, dend 7k um) we would actually adopt. Seeds 20240628, 31415, 27182, 16180. Same hard-limited values (96/48, days 25, minsep 10, radius 120, thickness 30, dm.weight 0.9 in the Excel), D_synmax 1.5 / 0.1 / 0.1 / 0.1, `bio_check.assert_hard_limits` as now. Baselines: the four existing V1 runs (`pv_arbor_seeds/pv_results.json` and `pv_arbor`). 3 concurrent NES sims maximum, detached launch, check `ps` and growing logs after one minute (LEARNINGS 2026-11-14). V1 wall about 1900-2100 s each.

**Metrics** (pv_arbor README definitions): dendrite/axon total length, axon reach (max distance from soma, mean over cells), Pyr->Pyr / Pyr->Int / Int->Pyr / Int->Int synapses, syn/pair Int->Pyr, pyramidal targets per interneuron, inhibitory fraction A and B, drivable 8-cell (and simple), zero-input interneurons, Pyr->Pyr change vs the same-seed baseline. Added by this scout (read-only scripts on the node files, as I used above): median axon-node distance from own soma and from disc centre by soma-radius band, fraction of axon nodes beyond r = 120 um from centre, straight-line/path ratio of growth cones.

**Pre-flight checks per run** (abort the interpretation if any fails): the `.nibr.clp` contains the appended lines; the report block `Subset 'all_interneuron_axons.' direction model` shows the intended numbers; `Subset 'all_axons.'` still shows contrib.w 0.90 and veer 0.20/0.79; the pyramidal axon and dendrite length are within +-10% of the same-seed V1 baseline; interneuron axon length within +-15% (B_inf unchanged).

**Control C0** (2 runs, V1 seeds 20240628 and 31415): the restated chain with unchanged values (`dm_weight=0.9`, `veeranglemin=0.19635`, `veeranglemax=0.78540`, `history_power=2.0`, no switch). Purpose: show that restating alone reproduces the clone-from-`all_axons` behaviour (same report numbers, metrics within seed noise). If C0 differs from baseline, tests 1 and 2 are not comparable and must be compared with C0.

### Test 1: interneuron-axon attraction weight
Appended lines (V1 plus):
```
all_interneuron_axons.direction_model=segment_history_tension;
all_interneuron_axons.dm_label=axondm;
all_interneuron_axons.axondm.dm_weight=0.1;      # arm T1a; arm T1b uses 0.45
all_interneuron_axons.axondm.direction_model=cell_attraction;
all_interneuron_axons.veeranglemin=0.19635;
all_interneuron_axons.veeranglemax=0.78540;
all_interneuron_axons.history_power=2.0;
```
Runs: T1a (0.1) x 4 seeds, T1b (0.45) x 2 seeds (20240628, 31415) = 6 runs; 0.1 is the hard-limit minimum, and 0.45 gives a dose point. Both values lie inside 0.1-1.0. Universal and pyramidal weights stay 0.9.

Pre-registered predictions (V1 baselines from the 4-seed README: targets/int 13.3 SD 1.6, Int->Pyr 926 SD 88, syn/pair 1.46, A 1.28%):
| metric | baseline | T1a (w=0.1), mean [range] | T1b (w=0.45) |
|---|---|---|---|
| axon-node median dist. from own soma, soma r 80-120 | 108 um | 150 [110-220] | 125 |
| fraction of axon nodes beyond r = 120 from centre | 0.000 | 0.15 [0.05-0.35] | 0.03 |
| axon reach (max dist from soma) | 127 | 230 [170-320] | 170 |
| straight/path ratio | 0.14 | 0.30 [0.2-0.45] | 0.2 |
| axon length | 45.5k | 45k +-15% | same |
| Int->Pyr synapses | 926 | 650 [350-1000] | 800 |
| targets per interneuron | 13.3 | 14 [9-22] | 14 |
| syn/pair Int->Pyr | 1.46 | 1.35 [1.15-1.6] | 1.4 |
| inhibitory fraction A | 1.28% | 0.9% [0.5-1.4] | 1.1% |
| Pyr->Pyr vs same-seed baseline | | within +-15% (noise) | |
Probability that T1a raises mean targets/int to >= 20: about 20%.

Success: reach >= 1.5x baseline (>= 190 um) in 4 of 4 seeds (this confirms the mechanism) **and** mean targets/int >= 20 with Int->Pyr >= 800. Partial (mechanism confirmed, connectivity not): reach success but targets < 17 or Int->Pyr < 700; this would mean extent and density trade off at fixed length, and the next step is a 2x2 with veer or D_synmax 0.15. Failure: reach < 1.2x baseline, which means the centroid pull is not the cause and my reading is wrong.

### Test 2: target diversification
Appended lines (V1 plus):
```
all_interneuron_axons.direction_model=segment_history_tension;
all_interneuron_axons.dm_label=axondm;
all_interneuron_axons.axondm.dm_weight=0.9;
all_interneuron_axons.axondm.direction_model=cell_attraction;
all_interneuron_axons.axondm.neuron_specific_attraction_switch=true;
all_interneuron_axons.veeranglemin=0.19635;
all_interneuron_axons.veeranglemax=0.78540;
all_interneuron_axons.history_power=2.0;
```
Runs: 4 seeds (T2) = 4 runs. If T2 shows an effect, a second arm adds `attraction_moderation_base=1.02` (about 0.55x pull toward a target with 30 inputs, 0.17x at 90; the dose is my guess).

Pre-registered predictions: targets per interneuron 13.3 -> 17 [13-23]; syn/pair 1.46 -> 1.30 [1.15-1.45]; Int->Pyr 926 -> 900 [700-1150]; reach 127 -> 140 [120-190]; Pyr->Pyr within noise. Probability that targets/int rises by >= 3 in at least 3 of 4 seeds: about 35%.

Success: mean targets/int >= 17 and >= +3 over baseline in >= 3 of 4 seeds, Int->Pyr not below 800, pyramidal arbors unchanged (+-10%). Failure: mean gain < +2, or Int->Pyr below 700. Statistical note: baseline seed SD of targets/int is 1.6 (n=4), so +3 is about 2 SD; with n=4 vs n=4 this has low power, so a "success" is suggestive, not proof, and should be repeated on V3 before use.

Run count and time: 2 + 6 + 4 = 12 runs, 4 batches of 3, about 2.5 h wall. Optional follow-up (not part of this design): D_synmax 0.15 on the interneuron pairs at the best arm.

## 4. Questions

For Randal / NES team:
1. Is the `dm.weight` limit 0.1-1.0 a single global value, or may interneuron axons carry their own weight inside that range? (Our Excel value is applied to `all_axons` only, `gen_autonm_labels.py:734`.)
2. May `D_synmax` interneuron pairs be used up to their hard max 0.15? Our runs and `pv_arbor/README.md` treated 0.1 as the ceiling.
3. In your base file every neuron is both attractor and attracted (`In.attractedto=NGF_A; In.attractors=NGF_A`). Was the resulting collapse of all axons to the region centre intended? Is that your "natural arborization", or should interneuron axons be steered locally (own soma, or toward pyramidal somata, as basket cells do)?
4. What did "natural arborization overrides built-in specs" mean operationally: per-type directives in the model file, a different NES generator, or imported reconstructed morphologies? If the last, growth-knob tuning may be the wrong path.
5. Does the NES API/model path pass `all_interneuron_axons.*` and `idx.<region>.<type>.<n>.*` lines to Netmorph unchanged? (The first is proven by our reports; the second is untested.)
6. Is there an intended mechanism for multiple synapses per axon-dendrite contact (bouton clusters; the source comment at synapse_formation_model.cc:114 says not implemented) or for perisomatic targeting? Neither exists in the code I read, and the synapse files only tag BASAL/APICAL.
7. How does NES treat fibre nodes outside the disc radius (radius <= 200 hard limit) if axons are allowed to extend beyond it? Is the interneuron axon reach target meant relative to the region size?
8. Does the running NES binary come from this source tree (`BrainGenix-NES/ThirdParty/NetmorphCMake`) or from the `wt/nes-nt-24-verify` worktree that earlier notes read? Report output matched key lines, but differences were not diffed.

Hard sub-questions that deserve a stronger model (Fable):
1. Analytic or semi-analytic equilibrium of axon-node density under unit-normalised 1/d^2 attraction plus persistence-limited veer in a disc (with the z thickness), to pick the weight at which reach matches PV extent and to predict the density penalty. My persistence estimate (35 um) and the 2.3x gap to the data are rough.
2. Upper bound on targets per interneuron and synapses per pair achievable at PV total axon length (30-45 mm), D_synmax <= 0.15 and the crossing-only synapse model: is a PV-like 11 per pair reachable at all, or is the model structurally limited? (Includes reconciling the measured D^1.6 scaling with the crossing formula.)
3. How to build territory-limited, soma-centred interneuron arbors out of global attractors, per-neuron `idx.` labels and weights, without touching pyramidal arbors; read-through of network.cc and neuron.cc order of configuration.
4. Statistical design: how many seeds and which paired comparison to detect a +3 targets/int shift given 10-15% realisation noise and changing RNG streams.
5. Whether `history_power=0` plus smaller turn rate plus low attraction yields natural-looking (Sholl-profile-matched) basket axons rather than just longer reach.

## 5. What I read and did not read; limits

Read in full: pv_arbor_seeds/README.md, pv_arbor/README.md, ARBOR_DESIGN.md, AXON_LEVER_FINDINGS.md, GABA_LEVERS.md, agent-library/LEARNINGS.md, pv_arbor_seeds/grow_pv.py, `NetmorphParOptim/bio_ranges.json`, the base config `nesvbp-autoassociative` (first 230 non-empty lines). Skimmed only the first 3.5-4 KB of CA3_ARBOR_BOUNDS.md, CA3_NATURAL_RANGES.md, CA3_INTERNEURON_TYPES.md. Not read: CA3_INTERNEURON_ARBOR_REFS.md, PREREGISTRATION.md, the other recipe folders. A grep of the Phase-0 regression tables only.
Source (S/): axon_direction_model.cc lines 20-80, 180-470, 560-846 (not 80-180, 470-560); network.cc, neuron.cc, fibre_structure.cc, synapse_formation_model.cc (97-200, 380-506), turning_models.cc (205-262), branching_models.cc (selected parts), environment_physics.cc (grep only), common_entry.cc help text (1096-1152), CMakeLists defines, the manual by `pdftotext` and grep (not read end to end). Not read: the growth loop in dendritic_growth_model.cc, fibre_elongation_model.cc, the spatial partitioning code except the two call sites, the NES wrapper (NetmorphManagerThread.cpp), gen_autonm_labels.py beyond grep. The statement that no lateral boundary exists is "not found", not "proved absent".
Data: findings 0.1, 0.3 and 0.4 come from **one** grown network (NES output `00657198-0d99-4f4c-83f3-92bda8015f7a`, report 202611142317, randomseed 16180, interneuron axon B_inf 26, i.e. S1 s16180). I did not check that the centre collapse is the same in the other 11 runs. That check (read-only, same scripts, on whichever NES output folders still exist) is step 0 before any run. Pyramidal bifurcation counts come from the same network. The V1/V3 reach values in the README (127-133) are consistent with the collapse but I have not measured them per band.
Temporary analysis scripts and a pdftotext copy of the manual were written to the session scratchpad (`/tmp/claude-1002/-home-johnjose-cos-netmorph-work-recipe-v2/a5c72076-8345-4748-be8f-0b002d4555b2/scratchpad/`), not to the project; this file and its folder are the only project additions.

## Step 0 result (2026-11-15)
Read in data: I audited all 17 requested runs (pv_arbor V1-V6 seed 20240628, S1 seed 20240628, S1/V1/V3 x seeds 31415, 27182, 16180; none missing) and the centre collapse holds in every one, for interneuron and pyramidal axons alike: median axon-node distance from the disc centre is 14-34 um (15-24 um in 15 of 17) in all soma-radius bands, at most 0.02% of axon nodes lie beyond r = 120 um, and the straight/path ratio of growth cones is 0.13-0.15. It does not differ systematically between S1, V1 and V3 or by seed; the only outlier is V3 seed 27182 (about 33 um). Attractor points are 69-87% pyramidal in all runs. Inference: the cause is shared by all axons, which fits the centroid-attraction reading, but no run varied the weight, so that remains untested until Test 1. Details and scripts: `step0_audit/README.md`.
