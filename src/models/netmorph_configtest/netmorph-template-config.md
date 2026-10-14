# Netmorph template configuration: line-by-line annotation

This annotates every statement in [`netmorph-template-config`](./netmorph-template-config), which
is a copy of `../autoassociative/nesvbp-autoassociative`. It is meant for walking through the
template line by line to decide what the browser configurator should cover next, aiming
eventually at everything Netmorph offers.

Line numbers refer to `netmorph-template-config`. If that file is edited, update the numbers here.

## Documentation sources

| Key | Source | Notes |
|---|---|---|
| **M §x p.N** | `NetmorphCMake/Source/doc/NETMORPH_version_2011-06-24_manual_2014-04-03.pdf` | `N` is the page number printed on the page. In a PDF viewer, go to page N+1. Chapter 8 lists USER parameters, chapter 10 lists ADVANCED parameters, and chapter 5 explains the prefix (schema) system. |
| **M7 Part n** | Same manual, chapter 7 ("A fully described sample simulation script", p.12–26) | Most of this template comes from that sample script, including many of its comments. Each Part explains a block of the script in prose. |
| **EXT** | `NetmorphCMake/Source/doc/extensions.md` | Features added since 2024 that aren't in the manual yet: chemical tagging, completion checks, soma detailing. |
| **HELP** | `NetmorphCMake/Source/common_entry.cc`, `helpstr` (starting at line 913) | Netmorph's built-in parameter list. It is the most complete list of accepted parameter names, but has one line per parameter. |
| **SRC** | `NetmorphCMake/Source/<file>:<line>` | Used only where no document covers a parameter. |

The older `NETMORPH-manual_5Mar09.pdf` in the same folder is superseded by the 2014 manual.

## Background needed to read the table

**Statement syntax.** Each command is `name=value;`, and `#` starts a comment. A later
assignment overrides an earlier one (M §3 p.3–4). That is how `autoassociative_reservoir.py`
overrides `In.pyramidal`, `In.interneuron` and `days`: it appends new values to the end of the
file.

**Prefixes (schemas).** Most model parameters can be preceded by
`[region.][natural set.][contributing label.]` (M §5.1 p.5, Table 2):

- **Natural sets:** none (the universal set), `all_axons.`, `all_dendrites.`,
  `all_pyramidal_axons.`, `all_pyramidal_dendrites.`, `all_interneuron_axons.`,
  `all_interneuron_dendrites.` and `all_apical_pyramidal_dendrites.`.
- **Region prefixes**, such as `In.`, restrict a setting to the neurons in that region (M §5.5 p.8).
- **Contributing labels**, such as `axondm.`, address a model chained after another one (M §5.3 p.7).

The manual and HELP mark parameters that accept a prefix with `*` or `<schema.>`.
**Beware (M §5.2 p.6):** if a set specifies a model choice, parameters that set leaves out get
compiled defaults. They are *not* inherited from a broader set. The configurator should
probably warn about this.

**PDFs.** Many parameters take a probability density function: `<label>.PDF=<pdf>` plus
parameters that depend on which PDF is chosen. `delta` uses `.PDF.value`. `normal` uses `.PDF.mean`,
`.PDF.std` and `.PDF.trunc`. `linear` uses `.PDF.max_x` and `.PDF.height_b`. `spline_normal[_with_min]` uses
`.PDF.max_x`, `.PDF.significance_threshold`, `.PDF.proportion_significant` and `[.PDF.min_x]`.
`uniform` and `exponential` take no parameters. (M §8.5 p.32, §10.5 p.42.) A configurator
component for picking a PDF would be reused in many places.

**Units.** Lengths are in µm, times in seconds, angles in radians, and elongation rates in µm/s
(for example, 0.0005208333 µm/s ≈ 45 µm/day).

## Configurator column

Swastik's configurator currently covers populations, their 3D placement and shape, and pathways
grown with chemical attractors. The **Cfg** column is a first guess at which statements that
covers, to be confirmed in the review:

- ✅ = probably covered already
- ⬜ = not yet covered
- — = comment or no-op line

---

## Lines 1–16: header and global simulation context

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 1–7 | comments | Description, author and run instructions. These still name `nesvbp-autoassociative`. | M7 Part 1 p.13 | — |
| 12 | `days=20;` | How many days of growth to simulate. `seconds=` overrides it if both are given. Default 21. `autoassociative_reservoir.py -growdays` appends its own `days=`. | M §8.1 p.26; M7 Part 2 p.14 | ⬜ |
| 13 | `dt=100;` | Fixed simulation time step in seconds. Default 100. | M §8.1 p.26; M7 Part 2 p.14 | ⬜ |
| 14 | `randomseed=20240628;` | Master random seed. `0` takes the seed from the clock, so runs are not reproducible. Default 0. | M §8.1 p.26; M7 Part 2 p.14 | ⬜ |
| 15 | `enable_completion_requirements=false;` | When true, growth can stop before `days` once every intended neuron pair (from chemical tags) is connected. Related parameter: `inputs=<regions>`. | EXT "Input neurons and completion checks"; HELP l.927 | ⬜ |
| 16 | `use_soma_detailing=true;` | Turns on neuron-type-specific soma radii (default ranges: interneuron 4–6 µm, others 7–10 µm). Ranges can be set with `soma_min_radius_<type>` and `soma_max_radius_<type>`. Default false. | EXT "Somatic detailing"; HELP l.952 | ⬜ |

## Lines 18–48: soma initialization (orientation and dendrite roots)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 22 | `pia_attraction_repulsion_hypothesis=true;` | The apical dendrite grows toward the pia, and the axon emerges from the opposite side of the soma. Default true. | M §10.3 p.37–38; M7 Part 3 p.14 | ⬜ |
| 26 | `use_specified_basal_direction=true;` | Orients each neuron so that the basal dendrite roots' center of mass points along a given vector, instead of a random direction. Default false. | M §10.2 p.37; M7 Part 3 p.14 | ⬜ |
| 27–29 | `specified_basal_direction_relx/rely/relz` = `0.001`, `0`, `-1` | The relative direction vector for line 26: basal dendrites point down (−z) and apical dendrites up. The vector can also be given as `_theta`/`_phi` angles. Default (0,1,0). Related: `apical_specified_overrides_centroid` and `random_orientation`. | M §10.2 p.37 | ⬜ |
| 33–34 | `pyramidal.min_basal=4;` `pyramidal.max_basal=8;` | Each pyramidal neuron gets a uniformly random number of basal dendrites in this range. The prefix is a neuron type (`principal`, `interneuron`, `multipolar`, `bipolar`, `pyramidal`, `untyped`), not a region. | M §10.3 p.38; M7 Part 3 p.14 | ⬜ |
| 38–39 | `pyramidal.basal.minangle=0;` `pyramidal.basal.maxangle=1.5;` | Angular range (radians) around the center-of-mass vector where basal roots may emerge. The example in M §10.3 spells it `basal_minangle`, but the source accepts `.basal.minangle` (SRC `neuron.cc:985`). | M §10.3 p.38; M7 Part 3 p.14–15 | ⬜ |
| 43 | `pyramidal.basal.force_model=surface_division;` | Spreads basal roots evenly over that area, as if they repel each other. The other option is `unrestricted` (the default). | M §10.3 p.38; M7 Part 3 p.15 | ⬜ |
| 48 | `all_axons.L0=15,25;` | Range (µm) for the initial length of axon root segments, chosen uniformly at random. Dendrites keep the default 9–11 µm. Accepts a schema prefix. The M7 prose says "22 µm", but the script value is 15. | M §8.2 p.27; M7 Part 3 p.15 | ⬜ |

## Lines 50–68: populations and soma placement (regions)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 51–55 | comments | Out of date. They describe two layers with one neuron each, but the file defines a single region `In` with 16+16 neurons. | — | — |
| 57 | `shape=regions;` | Somas are placed within named regions. Other shapes (`box`, `circle`, `rectangle`, `hexagon`) are deprecated in 3D. | M §8.2 p.27; M §10.3 p.38–39; M7 Part 5 p.15 | ✅ |
| 58 | `regions=In;` | List of region labels. **Separated by spaces, not commas** (SRC `network.cc:1276`). | M §8.2 p.27; M7 Part 5 p.15 | ✅ |
| 61 | `In.shape=disc;` | Region shape: `disc`, `box` or `sphere`. | M §8.2 p.27 | ✅ |
| 62 | `In.neurons=0;` | Number of neurons drawn from the general pool into this region, with types set by the global `approxproportion<type>` / `populationsize<type>`. `0` means the per-type counts below define the whole region. | M §8.2 p.27; M §5.4 p.7–8; M7 Part 6 p.16 | ✅ |
| 63 | `In.pyramidal=16;` | Number of pyramidal neurons added to the region. Other types: `interneuron`, `bipolar`, `multipolar`, `principal`, `untyped`. `autoassociative_reservoir.py` overrides this value. | M §10.3 p.39; M §5.4 p.7–8 | ✅ |
| 64 | `In.interneuron=16;` | Number of interneurons added to the region. Also overridden by `autoassociative_reservoir.py`. | M §10.3 p.39; M §5.4 p.7–8 | ✅ |
| 65 | `In.minneuronseparation=10;` | Minimum distance (µm) between neighboring soma centers. Default 75. | M §8.2 p.27 | ✅ |
| 66 | `In.centerZ=-300;` | Region center coordinate. `centerX`/`centerY` are left at the default 0. | M §8.2 p.27 | ✅ |
| 67 | `In.shape.radius=100;` | Radius (µm) of a disc or sphere. Default 700. | M §8.2 p.27 | ✅ |
| 68 | `In.shape.thickness=20;` | Thickness (µm) of a disc. Default 500. A box uses `shape.width`, `shape.height` and `shape.depth` instead. | M §8.2 p.27 | ✅ |

Not used here but in the same family: `neurons=`, `populationsize<type>=` and
`approxproportion<type>=` for the global pool (M §8.2 p.27–28, §10.2 p.36–37), and
`electrodes=` (M §10.3 p.37).

## Lines 70–76: region- and type-specific overrides (commented out)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 74–76 | `#Mid.all_interneuron_axons.…` | Disabled example of setting a model only for interneuron axons in region `Mid` (no such region exists here). It shows the `region.naturalset.parameter` pattern. | M §5.5 p.8; M7 Part 7 p.17 | ⬜ |

## Lines 78–88: environment physics (tissue boundary)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 83 | `environment_physics=pia;` | Declares labeled physical constraints, as a space-separated list. | M §10.3 p.38; M7 Part 8 p.17–18 | ⬜ |
| 84 | `pia.physical_boundary=spherical;` | Boundary type: `spherical` or `point_attractor`. | M §10.3 p.38 | ⬜ |
| 85 | `pia.spherical_center=0,0,-50000;` | Center of the sphere (µm). It can also be given per axis with `spherical_centerX/Y/Z`. | M §10.3 p.38 | ⬜ |
| 86 | `pia.spherical_radius=50000;` | Sphere radius (5 cm), so the boundary sits at z = 0, above the region at z = −300. | M §10.3 p.38 | ⬜ |
| 87 | `pia.spherical_maxrange=100;` | Distance (µm) inside the boundary within which repulsion acts. | M §10.3 p.38 | ⬜ |
| 88 | `pia.spherical_c_repulse=0.2;` | Strength of the repulsion (as a proportion of approach speed). | M §10.3 p.38 | ⬜ |

A `point_attractor` uses `attractor_point[X/Y/Z]`, `attractor_maxrange` and `attractor_c_attract`
instead (M §10.3 p.38).

## Lines 90–105: elongation, universal set (all neurites without a more specific setting)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 99 | `arbor_elongation_model=van_Pelt;` | Model for the total elongation resources of each arbor. Others: `polynomial_O1`, `polynomial_O3`. Ignored by growth cones that use `nonnorm_BESTL`/`pyrAD_BESTLNN`. | M §8.5 p.30; M §10.5 p.40; M7 Part 9 p.18 | ⬜ |
| 100 | `growth_F=0.39;` | Competition factor: how much the number of branches slows each terminal segment. | M §8.5 p.30 | ⬜ |
| 101 | `growth_nu0=0.00013889;` | Base elongation rate in µm/s (≈12 µm/day). | M §8.5 p.30 | ⬜ |
| 102 | `F_competes_with=same_arbor;` | Which terminal segments compete: `whole_neuron`, `all_axons`, `all_dendrites` or `same_arbor`. | M §8.5 p.30 | ⬜ |
| 103 | `terminal_segment_elongation_model=BESTL;` | How an arbor's resources are split among its growth cones. Others: `nonnorm_BESTL`, `pyrAD_BESTLNN`, `simple`, `inertia`, `second_order`, and more. | M §8.5 p.30–31; M §10.5 p.41 | ⬜ |
| 104 | `tsem.PDF=delta;` | Perturbation of each growth cone's share. `delta` (value 0) means no perturbation. Warning: a delta value > 0 can make the speed grow without limit. | M §8.5 p.31 | ⬜ |
| 105 | `elongation_rate_initialization_model=length_distribution;` | How elongation rates are assigned to the two branches after a bifurcation: the longer branch gets the larger rate. Others: `pure_stochastic`, `zero`, `unitary`, `continue_defaults`, `nonnorm_BESTL_length_distribution`. | M §8.5 p.31–32; M §10.5 p.42; M7 Part 9 p.18 | ⬜ |

## Lines 107–114: branching, universal set

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 112 | `branching_model=van_Pelt;` | Arbor-level branching probability model. It uses `B_inf`, `tau`, `E` and `E_competes_with`; the compiled defaults apply here. | M §8.4 p.28; M §10.6 p.43; M7 Part 10 p.18 | ⬜ |
| 113 | `min_node_interval=2.0;` | Minimum fiber length (µm) between turn or branch points. Default 0. | M §10.6 p.43 | ⬜ |
| 114 | `branch_angle_model=Balanced_Forces;` | Branch angles are set by the elongation rates of the two daughter branches. Parameters: `bam.bfbam.PDF` and `bam.PDF`. | M §8.4 p.29; M §10.6 p.44 | ⬜ |

## Lines 116–119: turning

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 118 | `TSTM=linear_rate;` | Model deciding when a growth cone turns. Others: `none`, `each_dt`, `branch_coupled`. | M §8.6 p.33; M §10.7 p.44; M7 Part 11 p.19 | ⬜ |
| 119 | `turn_separation=5.0;` | Mean fiber length (µm) between turns. Default 10. Alternatively `turn_rate` (turns per µm). | M §8.6 p.33–34 | ⬜ |

## Lines 121–127: direction of growth, universal set

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 124 | `direction_model=segment_history_tension;` | The new direction after a turn follows the fiber's own recent path, like tension along the fiber. Others: `cell_attraction`, `radial`, `vector`. Related: `history_power`. | M §8.6 p.34; M §10.7 p.45; M7 Part 12 p.19 | ⬜ |
| 125–126 | `veeranglemin=0.0;` `veeranglemax=0.75;` | Range (radians) of the random angle added to the expected direction. Defaults π/16 and π/4. | M §8.6 p.34 | ⬜ |
| 127 | `dirhistory_selection=none;` | The whole fiber history counts. The alternative, `random_truncation`, uses the `general_rtdhs_*` parameters. | M §10.7 p.46 | ⬜ |

## Lines 129–151: axon direction with chemical attraction (pathways)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 129–137 | comments | Out of date. They say the weight is 0.05 (it's 0.2) and describe the old default of attraction to the next region (In→Mid→Out). Chemical tags replace that default. | — | — |
| 138 | `all_axons.direction_model=segment_history_tension;` | Head of the axon direction-model chain (implicit weight 1.0). | M §5.3 p.7; M7 Part 14 p.19–20; EXT "Enabling attraction during axon growth" | ✅ |
| 139 | `all_axons.dm_label=axondm;` | Chains a second direction model, addressed with the label `axondm`. | M §5.3 p.7; M §10.7 p.45 | ✅ |
| 140 | `all_axons.axondm.dm_weight=0.2;` | Weight of the chained model relative to the head model. EXT recommends 0.2–0.5 for natural-looking fibers that still reach their targets. | EXT "Enabling attraction during axon growth"; M §10.7 p.45 | ✅ |
| 141 | `all_axons.axondm.direction_model=cell_attraction;` | The chained model steers growth cones toward neurons that emit factors this neuron is attracted to. Optional refinements: `neuron_specific_attraction_switch`, `single_attractor_per_growthcone`, `attraction_moderation_base`. | EXT "Refinements of the cell_attraction model" | ✅ |
| 143 | `detailed_chemical_factors=true;` | Dendrite branch points of emitting neurons also attract, not only somas. This favors neurons with large arbors. Default false. | EXT "Attraction to somas and dendrites"; HELP l.1148 | ✅ |
| 144 | `soma_attraction_weight=0.0;` | Weight of the somas as attraction points. `0` means only dendrites attract. Default 1.0. | EXT "Attraction to somas and dendrites" | ✅ |
| 146 | `In.attractedto=NGF_A;` | Axons of `In` neurons are attracted to factor `NGF_A`. Multiple IDs are separated by spaces. | EXT "Emitting and receiving chemical factors" | ✅ |
| 147 | `In.attractors=NGF_A;` | `In` neurons emit `NGF_A`. Together with line 146, this grows recurrent In→In connections. Every factor that some neuron is attracted to must be emitted by at least one neuron. | EXT "Emitting and receiving chemical factors" | ✅ |
| 149, 151 | `#idx.In.pyramidal.0.attractedto=…` | Disabled examples of tagging a single neuron as `idx.<region>.<type>.<i>.` (or `idx.<n>.`). | EXT "Emitting and receiving chemical factors" | ⬜ |

Not used here: `inputs=<regions>` (EXT "Input neurons and completion checks").

## Lines 153–176: axon elongation and branching

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 154–155 | comments | They refer to `Mid` interneurons, which don't exist in this template. | — | — |
| 158 | `all_axons.arbor_elongation_model=van_Pelt;` | Arbor elongation model for axons. Lines 159–165 are its parameters. | M §8.5 p.30; M7 Part 13 p.19 | ⬜ |
| 159 | `all_axons.growth_nu0=0.0005208333;` | Base axon elongation rate (≈45 µm/day). | M §8.5 p.30 | ⬜ |
| 160 | `all_axons.growth_F=0.16;` | Competition factor for axons. | M §8.5 p.30 | ⬜ |
| 161 | `all_axons.F_competes_with=same_arbor;` | See line 102. | M §8.5 p.30 | ⬜ |
| 162 | `all_axons.elongation_rate_initialization_model=nonnorm_BESTL_length_distribution;` | Rates after a bifurcation are drawn as absolute values from `eri.PDF`. | M §10.5 p.42; M7 Part 15 p.20 (described for dendrites) | ⬜ |
| 163–165 | `all_axons.eri.PDF=normal;` `.mean=0.000213…` `.std=0.0003978` | The PDF for line 162 (µm/s). | M §8.5 p.32 | ⬜ |
| 170 | `all_axons.branching_model=van_Pelt;` | Branching model for axons. M7 Part 13 sets the same parameters but doesn't name the model. | M §8.4 p.28 | ⬜ |
| 171 | `all_axons.B_inf=13.21658;` | Expected number of branching events in the long run. Default 4.75. | M §8.4 p.28 | ⬜ |
| 172 | `all_axons.E_competes_with=same_arbor;` | Which growth cones compete for branching. Default `whole_neuron`. | M §8.4 p.28 | ⬜ |
| 173 | `all_axons.E=0.319251;` | Strength of branching competition. Default 0.5. | M §8.4 p.28 | ⬜ |
| 174 | `all_axons.tau=1681541;` | Time constant (s) of branching. A larger value means branching happens later. Default 319680. | M §8.4 p.28 | ⬜ |
| 175 | `all_axons.TSBM=van_Pelt;` | Branching probability for each growth cone, depending on its centrifugal order (how many branch points from the soma). | M §8.4 p.29 | ⬜ |
| 176 | `all_axons.S=-0.20538;` | How strongly branching depends on centrifugal order. Default 0. | M §8.4 p.29 | ⬜ |

## Lines 178–184: axon branching for region `In` only

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 179–184 | `In.all_axons.branching_model/B_inf/tau/E_competes_with/E/TSBM` | Branching settings for `In` axons that override lines 170–175. Because this re-specifies the model, `S` is **not** inherited from line 176 and falls back to the default 0 (M §5.2 p.6). Check whether that is intended. | M §5.5 p.8; M §8.4 p.28–29 | ⬜ |

## Lines 186–211: dendrites (basal; apical defaults also come from here)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 192 | `all_dendrites.terminal_segment_elongation_model=nonnorm_BESTL;` | Each growth cone elongates at its own rate, ignoring arbor-level resources (`arbor_elongation_model` doesn't apply). | M §8.5 p.30–31; M7 Part 15 p.20 | ⬜ |
| 193–194 | `all_dendrites.tsem.PDF=delta;` `.value=0` | No change in rate between bifurcations. | M §8.5 p.31 | ⬜ |
| 195–197 | `all_dendrites.tsem.branch.PDF=normal;` `.mean=6` `.std=5` | Initial length (µm) of new branches. Default normal(2, 1). | M §8.5 p.31 | ⬜ |
| 198 | `all_dendrites.elongation_rate_initialization_model=nonnorm_BESTL_length_distribution;` | See line 162. | M §10.5 p.42; M7 Part 15 p.20 | ⬜ |
| 199–201 | `all_dendrites.eri.PDF=normal;` `.mean=0.0000914464` `.std=0.0000365786` | Dendrite elongation rate (≈7.9 µm/day). | M §8.5 p.32; M7 Part 15 p.20 | ⬜ |
| 206 | `all_dendrites.branching_model=van_Pelt;` | Branching model for dendrites. | M §8.4 p.28; M7 Part 16 p.20–21 | ⬜ |
| 207 | `all_dendrites.B_inf=2.52;` | Few branching events. | M §8.4 p.28 | ⬜ |
| 208 | `all_dendrites.tau=259680;` | Branching happens early. | M §8.4 p.28 | ⬜ |
| 209–210 | `all_dendrites.E_competes_with=same_arbor;` `all_dendrites.E=0.73;` | Branching competition within the dendrite. | M §8.4 p.28 | ⬜ |
| 211 | `all_dendrites.TSBM=van_Pelt;` | M7 Part 16 also sets `all_dendrites.S=0.5`. **The template leaves it out**, so S = 0. Check whether that is intended. | M §8.4 p.29; M7 Part 16 p.20 | ⬜ |

## Lines 213–256: apical dendrite trunk of pyramidal neurons

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 214 | `substitute=APD:all_apical_pyramidal_dendrites;` | Shorthand: every later `APD` becomes `all_apical_pyramidal_dendrites` (a regex substitution applied to commands). | M7 Part 17 p.21; HELP l.1359 | ⬜ |
| 218–222 | `APD.branching_model=van_Pelt;` `B_inf=0.1` `tau=400000` `E=0` `E_competes_with=same_arbor` | The trunk almost never branches. | M7 Part 18 p.21; M §8.4 p.28 | ⬜ |
| 228 | `APD.terminal_segment_elongation_model=pyrAD_BESTLNN;` | Special elongation model for pyramidal apical dendrites: a straight trunk, oblique branches along it, and a tuft at its end. | M §5.6 p.9; M §8.5 p.30–31; M7 Part 19 p.21–22 | ⬜ |
| 229–231 | `APD.tsem.trunklength.PDF=normal;` `.mean=80` `.std=2` | Trunk length (µm from the soma center) at which the tuft starts. Default normal(700, 100). | M §8.5 p.31 | ⬜ |
| 232 | `APD.tsem.prefix=pyr1;` | Label under which the tuft and oblique models are given (`pyr1.tuft.…`, `pyr1.oblique.…`). Default `pyrAP`. | M §8.5 p.31; M7 Part 19 p.21 | ⬜ |
| 233–234 | `APD.tsem.PDF=delta;` `.value=0` | No change in rate between bifurcations. | M §8.5 p.31 | ⬜ |
| 235–237 | `APD.tsem.branch.PDF=normal;` `.mean=6` `.std=1` | Initial branch length (µm) for obliques and tuft branches. | M §8.5 p.31; M7 Part 19 p.22 | ⬜ |
| 238–241 | `APD.elongation_rate_initialization_model=nonnorm_BESTL_length_distribution;` `APD.eri.PDF=normal;` `.mean=0.0010208333` `.std=0.000256` | Fast trunk growth (≈88 µm/day). | M7 Part 19 p.22; M §8.5 p.32 | ⬜ |
| 244 | `APD.direction_model=segment_history_tension;` | Trunk direction model. | M7 Part 20 p.22 | ⬜ |
| 245–246 | `APD.veeranglemin=0.0;` `APD.veeranglemax=0.1;` | Very little random deviation, so the trunk stays straight. | M7 Part 20 p.22; M §8.6 p.34 | ⬜ |
| 251–253 | `APD.tsem.obliques.PDF=normal;` `.mean=5` `.std=1` | Number of oblique branches on the trunk. Default normal(7, 3). | M §8.5 p.31; M7 Part 21 p.22 | ⬜ |
| 254–256 | `APD.tsem.obliqueangle.PDF=normal;` `.mean=0` `.std=1` | Angle of oblique branches; mean 0 means at right angles to the trunk. **Not listed in the chapter 8/10 tables**, only in M7. | M7 Part 21 p.22 | ⬜ |

## Lines 258–278: apical tuft (`pyr1.tuft.`)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 260 | `pyr1.tuft.terminal_segment_elongation_model=nonnorm_BESTL;` | Elongation model for tuft fibers. Under `<prefix>.tuft.` you can set the elongation, elongation-rate-initialization, branching (TSBM), branch-angle and direction models. | M §8.5 p.31 (`<prefix>.tuft.`); M7 Part 22 p.22–23 | ⬜ |
| 261–263 | `pyr1.tuft.tsem.branch.PDF=normal;` `.mean=6` `.std=1` | Initial branch length in the tuft. | M §8.5 p.31 | ⬜ |
| 264–265 | `pyr1.tuft.tsem.PDF=delta;` `.value=0` | No perturbation. | M §8.5 p.31 | ⬜ |
| 266–269 | `pyr1.tuft.elongation_rate_initialization_model=…;` `pyr1.tuft.eri.PDF=normal;` `.mean=0.0003889` `.std=0.000004` | Tuft elongation rate (≈33.6 µm/day). | M7 Part 22 p.23 | ⬜ |
| 272 | `pyr1.tuft.TSBM=van_Pelt_specBM;` | Like the `van_Pelt` TSBM, but it reads its branching model from the `pyr1.tuft.` prefix (lines 274–278) instead of the arbor's model. | M §8.4 p.29; M7 Part 23 p.23 | ⬜ |
| 273 | `pyr1.tuft.S=1;` | Dependence of branching on centrifugal order. | M §8.4 p.29 | ⬜ |
| 274–278 | `pyr1.tuft.branching_model=van_Pelt;` `B_inf=25` `tau=400000` `E=0.3` `E_competes_with=same_arbor` | Heavy branching in the tuft. | M7 Part 23 p.23; M §8.4 p.28 | ⬜ |

## Lines 280–300: apical obliques (`pyr1.oblique.`)

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 282 | `pyr1.oblique.terminal_segment_elongation_model=nonnorm_BESTL;` | Same structure as the tuft section (lines 260–278). | M §8.5 p.31 (`<prefix>.oblique.`); M7 Part 24 p.23 | ⬜ |
| 283–285 | `pyr1.oblique.tsem.branch.PDF=normal;` `.mean=6` `.std=1` | Initial branch length. | M §8.5 p.31 | ⬜ |
| 286–287 | `pyr1.oblique.tsem.PDF=delta;` `.value=0` | No perturbation. | M §8.5 p.31 | ⬜ |
| 288–291 | `pyr1.oblique.elongation_rate_initialization_model=…;` `pyr1.oblique.eri.PDF=normal;` `.mean=0.0002` `.std=0.000001` | Oblique elongation rate (≈17.3 µm/day). | M7 Part 24 p.23 | ⬜ |
| 294–295 | `pyr1.oblique.TSBM=van_Pelt_specBM;` `pyr1.oblique.S=1;` | See lines 272–273. | M §8.4 p.29; M7 Part 25 p.24 | ⬜ |
| 296–300 | `pyr1.oblique.branching_model=van_Pelt;` `B_inf=1.5` `tau=500000` `E=0.3` `E_competes_with=same_arbor` | Little branching on obliques, spread over a long time. | M7 Part 25 p.24 | ⬜ |

## Lines 302–321: general growth flags, synapses, fiber diameter

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 311–312 | comments | Out of date. They say candidate synapses are not sought, but line 318 is `true`. | — | — |
| 313 | `fibreswithturns=true;` | Applies turning models (lines 118–119). Costly to compute. Default true. | M §8.3 p.28; M7 Part 26 p.24 | ⬜ |
| 314 | `branchatinitlength=false;` | Doesn't force the first branching at the `L0` root length. | M §10.4 p.39; M7 Part 26 p.24 | ⬜ |
| 315 | `branchinsegment=true;` | A branch point can be anywhere in the most recently grown piece of fiber. | M §10.4 p.40 | ⬜ |
| 316–317 | `Abranchesatturns=false;` `Dbranchesatturns=false;` | Turn points on axons and dendrites can't later become branch points. | M §10.4 p.39–40 | ⬜ |
| 318 | `candidate_synapses=true;` | Looks for possible synapse sites and simulates synapse formation. **Required for any connectome.** Related: `synapse_formation.PDF`, `D_synmax.<pre>.<post>` (maximum fiber distance at a synapse), `P_receptor.<pre>.<post>.<AMPAR/NMDAR/GABAR>`, `no_autapses`. | M §10.9 p.47–48; M §8.8 p.34–35 | ⬜ |
| 320 | `fibrediameter=true;` | Draws fiber thickness in XFig output only (SRC `fibre_structure.cc:393`). HELP says "use specific diameters". | M §10.14 p.53 | ⬜ |
| 321 | `neurite_diameter_model=rall;` | Fiber diameters follow Rall's power law. Parameters: `ndm.e_power.PDF` and `ndm.d_term.PDF`. Others: `none`, `asymptotic`. Default `none`. | M §8.7 p.34; M §10.8 p.46–47 | ⬜ |

## Lines 323–344: sampling and output

When Netmorph runs inside NES, NES reads the generated network directly, so most of these only
matter for standalone runs or for inspecting Netmorph's output files.

| Line | Statement | What it does | Docs | Cfg |
|---|---|---|---|---|
| 327 | `sample_dt=4320;` | Sampling interval in seconds (72 min) for statistics and for sequence or figure output. Default 86400. | M §10.12 p.49; M7 Part 27 p.24–25 | ⬜ |
| 328 | `statsattr_collect_statistics=true;` | Writes the `_stats.m` Octave file. Individual statistics can be switched with the `statsattr_D/A…` flags. | M §10.12 p.49–50; M §11.1 p.55 | ⬜ |
| 331 | `outattr_show_progress=true;` | Prints verbose progress. | M §10.13 p.51 | ⬜ |
| 332 | `outattr_make_full_Txt=true;` | Writes the network structure as text (format described in M §11.2). | M §8.9 p.35; M §11.2 p.56–59 | ⬜ |
| 333 | `outattr_Txt_sequence=false;` | No text snapshot at each sample time. | M §8.9 p.35 | ⬜ |
| 334 | `outattr_Txt_separate_files=true;` | One file per data type: `.neurons`, `.synapses`, `.rootnodes`, and so on. | M §8.9 p.35 | ⬜ |
| 335 | `outattr_track_synaptogenesis=true;` | Records when each synapse was created. | M §10.10 p.48 | ⬜ |
| 336 | `outattr_track_nodegenesis=true;` | Records when each branch or turn node was created. | M §10.10 p.48 | ⬜ |
| 337 | `outattr_show_stats=true;` | Writes the statistics to `stats.m`. | M §10.12 p.50–51 | ⬜ |
| 339 | `NES_output=true;` | Adds output for NES. For example, the neuron text output gains a soma radius column (SRC `network.cc:2139`). Not in the manual. | HELP l.1355 | ⬜ |
| 342 | `outattr_show_figure=false;` | HTML-form figure display. Not relevant here. | M §10.14 p.52 | ⬜ |
| 343 | `figattr_make_full_Fig=false;` | No XFig drawing of the network. | M §10.14 p.52 | ⬜ |
| 344 | `figuresequence=false;` | No figure per sample time. | M §10.15 p.54 | ⬜ |

NES-specific output options that `autoassociative_reservoir.py` appends when asked:
`outattr_make_full_OBJ`, `outattr_OBJ_bevdepth_axon`/`_dendrite`, `outattr_make_full_blend` and
`blender_exec_path`. These aren't in the manual. See `NetmorphCMake/Source/README-Blender.md`.

---

## Issues in the template worth fixing

1. **Out-of-date comments** at lines 51–55, 129–137, 154–155 and 311–312, described in the tables above.
2. **`all_dendrites.S` is missing.** The M7 source sets 0.5 (line 211).
3. **`In.all_axons.*` doesn't set `S`**, so `In` axons fall back to S = 0 instead of −0.20538 (lines 179–184).
4. **The `L0` comment** (line 47) and the M7 prose disagree about the minimum axon root length (15 vs. 22 µm).

## Parameter families for planning the configurator

Grouped by the configurator section each would most likely belong to.

| Family | Template lines | Doc sections | Status |
|---|---|---|---|
| Global run (days, dt, seed, completion) | 12–16 | M §8.1, EXT | ⬜ |
| Soma orientation and dendrite roots | 22–48 | M §10.2–10.3, M §8.2 (`L0`) | ⬜ |
| Populations and placement | 57–68 | M §8.2, §5.4, §10.3 | ✅ |
| Region/type overrides (prefix system) | 74–76, 179–184 | M §5 | ⬜ |
| Environment physics | 83–88 | M §10.3 | ⬜ |
| Elongation models | 99–105, 158–165, 192–201 | M §8.5, §10.5 | ⬜ |
| Branching models | 112–114, 170–184, 206–211 | M §8.4, §10.6 | ⬜ |
| Turning and direction | 118–127 | M §8.6, §10.7 | ⬜ |
| Chemical attraction pathways | 138–151 | EXT, M §5.3 | ✅ |
| Pyramidal apical dendrite (trunk, tuft, obliques) | 214–300 | M §5.6, §8.5, M7 Parts 17–25 | ⬜ |
| Growth flags | 313–317 | M §8.3, §10.4 | ⬜ |
| Synapse formation | 318 | M §8.8, §10.9 | ⬜ |
| Fiber diameter | 320–321 | M §8.7, §10.8 | ⬜ |
| Output and statistics | 327–344 | M §8.9, §10.10–10.15 | ⬜ |
