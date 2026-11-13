# Interneuron arbor design: which Netmorph parameters, and what they should deliver

Analyst note, written 2026-11-12 from source reading and arithmetic only. Nothing was grown, nothing was run on the NES server, no repo was edited.
Source tree read: `/home/johnjose/BrainGenix/wt/nes-nt-24-verify/ThirdParty/NetmorphCMake/Source` (called `S/` below). Manual: `S/doc/NETMORPH_version_2011-06-24_manual_2014-04-03.pdf`.
Base growth config: `/home/johnjose/cos/netmorph_work/bec/src/models/autoassociative/nesvbp-autoassociative` (called "base file").

## 0. Bottom line

- Interneuron arbor parameters exist, are settable from the config text, and should raise all three weak pathways. But inside biologically plausible arbor sizes they give about x2 on Pyr->Int, x2 on Int->Pyr and x4 on Int->Int. The inhibitory fraction onto pyramidal cells needs about x25 (0.5% to 13%). **I predict arbor size alone will not reach the 50% drivable-interneuron bar** (best case config D: 12 of 48, range 7-18).
- Three source findings change how the config must be written (section 1.1). The most important: selecting a model for an interneuron set creates a fresh model with compile-time defaults; it does not inherit the `all_axons` / `all_dendrites` numbers, so every parameter has to be restated.
- One finding for Randal outside the arbor question (section 3.4): the synapse distance test is between fibre centre lines, and fibre radius is not subtracted. With D_synmax 0.1 two fibres whose membranes touch do not connect unless their axes are within 0.1 um. I did not change any D_synmax value; this is a point for the team to decide.

Everything about lengths and counts below is a mean-field estimate from the model equations. No morphology data exists locally to check it (the viz dump holds somata and connections only). Each such number is marked "estimate".

## 1. Parameters

### 1.1 How the sets resolve (read this before the table)

1. **Most specific set only.** An interneuron axon takes all its models from the schema `[region][all_interneuron_axons]`; an interneuron dendrite from `[region][all_interneuron_dendrites]` (`S/prepost_structure.cc:38-54`, `:79-89`, `:133`).
2. **Inheritance path.** In the universal network, `all_interneuron_axons` inherits from `all_axons`, which inherits from the universal set; same for dendrites (`S/global.cc:40-51`). For a region, `In.all_interneuron_axons` inherits from the universal `all_interneuron_axons`, **not** from `In.all_axons` (`S/neuron.cc:158-161`, `:253-264`).
   - Consequence (by source reading, not confirmed by a run): the base file's `In.all_axons.B_inf=10.0; In.all_axons.tau=319680; In.all_axons.E=0.5` block has no effect on pyramidal or interneuron axons. They use `all_axons.B_inf=13.21658; tau=1681541; E=0.319251`.
   - So interneuron settings should be written with the universal prefixes `all_interneuron_axons.` and `all_interneuron_dendrites.` (no `In.`).
3. **Parameters are read only when the model is selected for that set.** `all_interneuron_axons.B_inf=...` alone is ignored. It needs `all_interneuron_axons.branching_model=van_Pelt;` on the same set (`S/branching_models.cc:689-716`). Selecting it builds a new model with compile-time defaults, B_inf 4.75, tau 319680, E 0.5, competition `whole_neuron`, min_node_interval 0 (`S/branching_models.cc:55-66`, `:111`). All five must be restated.
4. **Each model family is a separate schema.** Branching model, terminal-segment branching model (S), arbor elongation (growth_nu0, growth_F), terminal-segment elongation, elongation-rate initialisation, direction, turning and L0 are selected independently (`S/neuron.cc:255-263`). Restating the branching model leaves elongation untouched, so growth_F and growth_nu0 stay exactly as they are.
5. **Do not select `arbor_elongation_model` on an interneuron set.** That would create a new elongation model with defaults nu0 15.5 um/day and F 0.74 (`S/fibre_elongation_model.cc:152`), which breaks the "growth_F / growth_nu0 constant" rule.
6. **Dendrites do not use growth_nu0 / growth_F at all.** `all_dendrites.terminal_segment_elongation_model=nonnorm_BESTL` makes every dendritic growth cone elongate at its own absolute rate drawn from `all_dendrites.eri.PDF` (mean 0.0000914464 um/s = 7.9 um/day), with no sharing inside the arbor (`S/fibre_elongation_model.cc:764-808`, `:1246-1249`). Dendrite length is therefore (number of growth cones) x (rate) x (time).
7. **Axons do use the arbor budget.** Axons keep the universal `BESTL` terminal model, so total arbor elongation per unit time is nu0 x n^(1-F) with the `all_axons` values nu0 0.0005208333 um/s (45 um/day) and F 0.16, n = number of growth cones (`S/fibre_elongation_model.cc:199-203`). More growth cones means more total length, with no change to nu0 or F.

### 1.2 Table

"Proposed range" is what I would allow in this study. Biological ranges are my recall and are **unverified**; none was looked up.

| # | Parameter (exact config syntax) | Defined at | Default / current value | Code-enforced validity | Proposed range | Biological justification | Confidence in justification |
|---|---|---|---|---|---|---|---|
| 1 | `interneuron.min_basal=<int>;` | `S/neuron.cc:957`, default `S/neuron.hh:442`, used `S/neuron.cc:1353` | 2 | none (atoi, no check; min > max is not guarded) | 4-6 | Number of primary dendrites per interneuron. Recall: cortical and hippocampal basket / multipolar interneurons have about 3-8 primary dendrites | medium (unverified recall) |
| 2 | `interneuron.max_basal=<int>;` | `S/neuron.cc:958`, default `S/neuron.hh:443` | 4 | none | 8 | same; count is drawn uniformly from min..max inclusive (`S/mtprng.hh:279-282`) | medium (unverified recall) |
| 3 | `interneuron.basal.minangle=<rad>; interneuron.basal.maxangle=<rad>;` | `S/neuron.cc:959-960`, defaults `S/neuron.hh:447-448` | 0.1 pi, 1.0 pi (dendrites leave in almost any direction) | none | leave | Multipolar interneurons are roughly isotropic | medium |
| 4 | `all_interneuron_dendrites.branching_model=van_Pelt;` with `.B_inf=`, `.tau=`, `.E=`, `.E_competes_with=same_arbor;`, `.min_node_interval=2.0;` | `S/branching_models.cc:111-139`, `:62`, formula `:207-220` | inherited from `all_dendrites`: B_inf 2.52, tau 259680 s (3.0 d), E 0.73, same_arbor, 2.0 | B_inf < 0 ignored with warning; tau = 0 ignored (negative tau is accepted, do not use); E unchecked; min_node_interval < 0 set to 0 | B_inf 2.52-3.5; tau and E unchanged | Interneuron dendrites are long and sparsely branched. Estimate: B_inf 2.52 gives 4.2 tips per primary dendrite, 3.5 gives 5.7 | low-medium (unverified recall; tip counts are estimates) |
| 5 | `all_interneuron_dendrites.elongation_rate_initialization_model=nonnorm_BESTL_length_distribution;` with `.eri.PDF=normal; .eri.PDF.mean=; .eri.PDF.std=;` | `S/fibre_elongation_model.cc:1220`, `:1246`, selection `:1546-1568` | inherited: mean 0.0000914464 um/s, std 0.0000365786 | none found | **not used here** | This is the dendritic elongation rate. It is not named growth_nu0, but it plays the same role for dendrites. I treat it as covered by the "elongation rate constant" rule until Randal says otherwise | n/a |
| 6 | `all_interneuron_dendrites.L0=<min>,<max>;` | `S/fibre_structure.cc:1111-1124`, default `S/fibre_structure.hh:445` | 9-11 um (inherited default) | negative or max < min is a fatal error (`S/fibre_structure.cc:1095`) | leave | Adds about 10 um per dendrite; negligible lever | high that it is negligible |
| 7 | `all_interneuron_axons.branching_model=van_Pelt;` with `.B_inf=`, `.tau=`, `.E=`, `.E_competes_with=same_arbor;`, `.min_node_interval=2.0;` | same as row 4 | inherited from `all_axons`: B_inf 13.21658, tau 1681541 s (19.5 d), E 0.319251, same_arbor, 2.0 | same as row 4 | tau 432000-1681541 s (5-19.5 d); B_inf and E unchanged | Local-circuit axons arborise densely near the soma. A shorter tau moves branching earlier (more growth cones for more of the 25 days) without raising the final branching propensity B_inf | low-medium (qualitative; unverified) |
| 8 | `all_interneuron_axons.TSBM=van_Pelt; all_interneuron_axons.S=<x>;` | `S/branching_models.cc:314-317`, selection `:744-770` | inherited: S -0.20538 | none | leave | Centrifugal-order bias of branching; no clear biological reason to change | n/a |
| 9 | `all_interneuron_axons.L0=<min>,<max>;` | as row 6 | inherited `all_axons.L0=15,25` | as row 6 | leave | negligible | high |
| 10 | `all_interneuron_axons.arbor_elongation_model`, `.growth_nu0`, `.growth_F`, `.F_competes_with` | `S/fibre_elongation_model.cc:152-166` | inherited from `all_axons`: van_Pelt, 0.0005208333, 0.16, same_arbor | none | **must not be set** (rule) | The manual's own examples slow interneuron axons to nu0 0.0001 (manual p. 6-7; those lines are commented out in the base file), which would cut Int->Pyr further | n/a |
| 11 | `all_interneuron_axons.direction_model=...; .dm_label=...; .<label>.dm_weight=...` | `S/axon_direction_model.cc` (selection near `:841`) | inherited from `all_axons`: segment_history_tension chained with cell_attraction, weight = the hard-limited dm_weight | **not read in detail** | not used | Guidance of interneuron axons towards pyramidal somata would be the biologically right lever (basket cells target somata) but I could not establish from the time available how cell_attraction picks its target | not determined |
| 12 | `interneuron.max_axons` | `S/neuron.cc:1212` | 1 | none | no effect | `interneuron::initialize_output_structure` hard-codes one axon (`S/neuron.cc:1341`) | high |
| 13 | Termination | - | - | - | - | There is no termination parameter. Growth stops at `days`. Branching decays as exp(-t/tau); elongation continues to the end | high |

Rows 1, 2, 4 and 7 are the usable levers. Rows 5, 10 and 11 are deliberately left alone.

## 2. Pre-registered predictions

**Written 2026-11-12 09:31:18 PST, before any of these configs has been grown.**

Geometry for all four: 96 pyramidal, 48 interneuron, minneuronseparation 10, radius 120, thickness 30, dm_weight 0.9, days 25, seed 20240628, D_synmax 1.5 (pyramidal.pyramidal) and 0.1 (the three interneuron pairs). All seven hard-limited parameters, growth_F, growth_nu0 and every D_synmax are identical to config a. Only the lines listed are appended. None of the parameter names occurs in the base file, so there is no duplicate-key question.

Baseline (config a, measured, `phase1_results.json`): Pyr->Int 227, Int->Pyr 348, Int->Int 108, Pyr->Pyr 71924, 6 of 48 interneurons at or above 13.84 nS, 26 with no pyramidal input, inhibitory fraction onto pyramidal 0.5%, wall 1260 s. Config e (same geometry, different D_synmax) took 1067 s, so wall time has about 15% run-to-run spread.

### 2.1 Scaling arguments

1. **Contact count.** A synapse candidate is one (axon segment, dendrite segment) pair whose centre lines pass within D_synmax (`S/synapse_formation_model.cc:390-411`). For fibres crossing at random, pairs within distance d number about (pi/2) x d x L_axon x L_dendrite / V, with L the total lengths sharing volume V. So, at fixed D_synmax:
   - Pyr->Int is proportional to total interneuron dendrite length.
   - Int->Pyr is proportional to total interneuron axon length.
   - Int->Int is proportional to the product of the two.
2. **Dendrite length (estimate).** Growth cones per primary dendrite follow n^E = 1 + E x B_inf x (1 - exp(-t/tau)). With B_inf 2.52, E 0.73, tau 3.0 d: 4.2 tips, nearly all by day 8. Each tip grows 7.9 um/day. That gives about 790 um per primary dendrite at day 25, so about 2.4 mm per baseline interneuron (mean 3 dendrites). Length is linear in the number of primary dendrites, because dendrites do not share a budget (section 1.1 item 6). B_inf 3.5 gives 5.7 tips and about 1040 um per primary dendrite.
3. **Axon length (estimate).** Same branching law with B_inf 13.2, E 0.319: growth cones at day 25 are 80 (tau 19.5 d), 143 (tau 10 d), 174 (tau 5 d). Total elongation rate is 45 um/day x n^0.84. Integrated over 25 days: 21 mm (baseline), 40 mm (tau 10 d, x1.9), 61 mm (tau 5 d, x2.9).
4. **Consistency check on the estimates.** The measured Pyr->Pyr / Pyr->Int ratio (317) and the crossing formula are consistent with these lengths to within a factor of about 3. That is the accuracy to expect.
5. **Drivable interneurons.** From earlier runs (mean pyramidal synapses per interneuron m against fraction at or above 13.84 nS: 4.7 -> 12.5%, 10.5 -> 17%, 44.7 -> 19-44% across seeds, 134 -> 59%), the fraction is roughly 0.13 x ln(m/2). It rises slowly because input is very uneven (26 of 48 have none). More primary dendrites should even it out a little, since each dendrite is an independent sample of the pyramidal axon field; I add a small bonus for that in A, C and D.
6. **Why ranges are wide.** Changing the interneuron arbor changes the random-number sequence, so the whole network is a new realisation. Earlier seed-to-seed spread at fixed parameters was about a factor of 2 in drivable count.

### 2.2 Configs

**Config A: dendrites only (within plausible range)**

```
interneuron.min_basal=4;
interneuron.max_basal=8;
```

Mean 6 primary dendrites instead of 3: interneuron dendrite length x2.0 (estimate 4.7 mm per cell).

**Config B: axons only (moderate)**

```
all_interneuron_axons.branching_model=van_Pelt;
all_interneuron_axons.B_inf=13.21658;
all_interneuron_axons.tau=864000;
all_interneuron_axons.E=0.319251;
all_interneuron_axons.E_competes_with=same_arbor;
all_interneuron_axons.min_node_interval=2.0;
```

Only tau differs from what interneuron axons use now (1681541 -> 864000 s, 10 days). Axon length x1.9 (estimate 40 mm per cell, 143 growth cones).

**Config C: both moderate** = the two lines of A plus the six lines of B.

**Config D: both strong (ceiling probe, at or beyond the plausible edge)**

```
interneuron.min_basal=6;
interneuron.max_basal=8;
all_interneuron_dendrites.branching_model=van_Pelt;
all_interneuron_dendrites.B_inf=3.5;
all_interneuron_dendrites.tau=259680;
all_interneuron_dendrites.E=0.73;
all_interneuron_dendrites.E_competes_with=same_arbor;
all_interneuron_dendrites.min_node_interval=2.0;
all_interneuron_axons.branching_model=van_Pelt;
all_interneuron_axons.B_inf=13.21658;
all_interneuron_axons.tau=432000;
all_interneuron_axons.E=0.319251;
all_interneuron_axons.E_competes_with=same_arbor;
all_interneuron_axons.min_node_interval=2.0;
```

Mean 7 primary dendrites with 5.7 tips each: dendrite length x3.1 (estimate 7.3 mm per cell). Axon tau 5 days: axon length x2.9 (estimate 61 mm per cell). Both exceed the adult values I recall (section 3.1); D is there to show the ceiling, not as a candidate recipe.

### 2.3 Predictions (central value, 10-90% range in brackets)

| Quantity | baseline a (measured) | A | B | C | D |
|---|---|---|---|---|---|
| Interneuron dendrite length factor (estimate) | 1 | 2.0 | 1 | 2.0 | 3.1 |
| Interneuron axon length factor (estimate) | 1 | 1 | 1.9 | 1.9 | 2.9 |
| Pyr->Int synapses | 227 | 455 [300-650] | 227 [170-300] | 455 [300-650] | 700 [430-1050] |
| Int->Pyr synapses | 348 | 348 [270-440] | 660 [450-950] | 660 [450-950] | 1010 [650-1500] |
| Int->Int synapses | 108 | 216 [140-330] | 205 [130-320] | 410 [250-680] | 970 [500-1700] |
| Interneurons (of 48) with >= 13.84 nS from pyramidal | 6 | 9 [5-13] | 6 [3-9] | 9 [5-13] | 12 [7-18] |
| Interneurons with no pyramidal input | 26 | 15 [9-21] | 26 [21-31] | 15 [9-21] | 11 [5-17] |
| Inhibitory fraction onto pyramidal | 0.5% | 0.5% [0.4-0.6] | 0.9% [0.6-1.3] | 0.9% [0.6-1.3] | 1.4% [0.9-2.0] |
| Pyr->Pyr synapses (control, should not move) | 71924 | 72000 [69000-75000] | 72000 [69000-75000] | 72000 [69000-75000] | 72000 [69000-75000] |
| Wall time relative to 1260 s | 1.0 | 1.05 [0.9-1.2] | 1.3 [1.05-1.6] | 1.35 [1.1-1.7] | 1.8 [1.3-2.5] |

Probability that any config reaches 24 of 48 drivable: A, B, C under 3% each; D about 5%.

Wall-time reasoning: interneuron axons are about a quarter of all fibre length in the baseline (estimate: 1.0 m of 4.0 m). B adds about 0.9 m, D about 2.2 m. I do not know what share of the 1260 s is Netmorph growth and what share is NES conversion, hence the wide ranges.

Checks to make on each run before scoring: (a) the appended lines appear in the Netmorph parameter echo; (b) Pyr->Pyr stays near 72000. If Pyr->Pyr moves by more than 5%, the change leaked into pyramidal cells and the run does not test what it claims.

## 3. Risks and unknowns

### 3.1 Realism

- Biological reference values, all **unverified recall**: basket-type interneurons have about 3-8 primary dendrites, total dendritic length about 3-6 mm, total axon length about 20-50 mm; inhibitory synapses are about 10-20% of synapses onto a pyramidal cell. These are adult values; the simulation covers 25 days of development.
- A and B stay inside those values on my estimates (4.7 mm dendrite, 40 mm axon). D does not (7.3 mm, 61 mm).
- My length estimates are mean-field and unchecked. If true baseline arbors are much shorter than estimated, there is more plausible headroom than stated; if longer, less. Netmorph's statistics output (`statsattr_collect_statistics=true`) may hold arbor lengths, but I did not find per-type lengths in the files available locally.
- Real interneuron axons place boutons on targets; Netmorph only counts chance crossings within D_synmax. That is the structural reason the grown inhibitory fraction is 25 times too low, and arbor size does not address it.

### 3.2 Things that could break a run

- **Timeout.** `grow_v2.py` kills the growth at 1500 s. B, C and D are predicted to exceed it. The cap needs to be about 3600 s for these runs. `grow_v2.py` also has no hook for extra directives yet (it only appends D_synmax lines).
- **Memory and NES conversion.** D roughly doubles the interneuron segment count. I do not know the conversion's limits on compartments per neuron.
- **Dendrite placement warnings.** The base file sets the surface-division placement model globally. With n dendrites it demands 1.8 pi / n radians between roots (`S/neuron.cc`, surface_division_basal_force_model); 8 dendrites need 40 degrees, which fits. If placement fails after 500 tries it warns and continues, it does not abort.
- **Silent no-op.** If `branching_model=van_Pelt` is omitted, or the `In.` prefix is used with a universal setting expected to carry over, the lines are accepted and ignored. Check the parameter echo.
- **Silent default.** If any of the five restated branching values is omitted, the compile-time default is used instead of the inherited value (for example E_competes_with falls back to whole_neuron, min_node_interval to 0).
- **No validation of min_basal / max_basal.** min > max, zero or negative values are not checked by the code.

### 3.3 Not determined from the source

- How `cell_attraction` chooses its target and how it shapes interneuron axons (row 11). Not read.
- Turning model and veer-angle effects on contact counts. Not read.
- Whether the measured contact count scales linearly with fibre length in practice. The D_synmax dependence was measured at power 1.6, not the 1.0 of the simple crossing formula, so the formula is incomplete.
- Actual arbor lengths, growth-cone counts and spatial overlap of interneuron and pyramidal arbors in the baseline. No local data.
- Whether the `In.all_axons.*` block is really inert for pyramidal axons. This follows from the code path but was not confirmed against a run.
- Share of wall time spent in growth versus conversion.
- The manual's parameter tables were only searched, not read end to end.

### 3.4 Finding for Randal: what D_synmax measures

`S/synapse_formation_model.cc:142` and `:390-411` compare D_synmax with the distance between the two segment centre lines. Fibre diameter is computed in this config (`fibrediameter=true`) but, as far as I read, is not subtracted. Two fibres whose surfaces touch have centre lines separated by the sum of their radii, which for a dendrite and an axon is likely several tenths of a micron. So "touching always connects" holds only if the axes come within D_synmax. At 0.1 um this is stricter than membrane contact. If the team wants "smooth dendrite, contact only", the matching centre-line value would be about (axon radius + dendrite radius), not 0.1. This is a question for Randal; I have not proposed or changed any D_synmax value.

## 4. Run order and decision rule

Run order:

1. **A** (dendrites only). Cheapest, inside the timeout, fully inside plausible range. Tests that `interneuron.min_basal/max_basal` take effect and that Pyr->Int is linear in dendrite count.
2. **B** (axons only). Tests the set-inheritance reading and the axon-length law. Needs the longer timeout.
3. **D** (ceiling). Shows the most that arbor size can give.
4. **C** (both moderate). Only informative if A and B behaved as predicted; its result is then the product of the two and can be skipped if time is short.

Decision rule:

- **After A.** If Pyr->Int is below 300 (less than x1.3), the dendrite lever or my reading of it is wrong: stop and inspect the parameter echo before spending more runs. If it is in range, continue.
- **After B.** If Int->Pyr is below 450, same action for the axon lever. If the run times out, raise the cap before D.
- **After D.** 
  - Stop the arbor route if D gives fewer than 16 of 48 drivable interneurons (33%) or an inhibitory fraction below 3%. That is my expected outcome. Arbor size cannot then close the gap within plausible morphology, and the decision goes back to Randal with section 3.4 and the guidance option (row 11) as the alternatives.
  - Go further if D reaches 20 or more drivable (above 40%) or Int->Pyr above 2000. Then run C, and try intermediate settings between C and D to find the smallest arbors that hold the result, and repeat on two more seeds before believing it.
  - Between those (16-19 drivable): run C and one extra seed of D before deciding.
- **Any run** where Pyr->Pyr moves by more than 5% from 71924 is discarded as a leak into pyramidal parameters.
