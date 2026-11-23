# E4 arbors versus published CA3 pyramidal and PV basket cell morphology (2026-11-22)

No simulation. Our numbers are measured offline from the NetMorph text output of the 10 grown E4 networks (`morph_e4.py` -> `morph_e4.json`, in this folder; models listed in `models.json`). Literature numbers come from the earlier literature notes in recipe_v2 plus four searches today; every row carries its source and how I got it. Status tags: **READ** = number seen in fetched text or a search snippet, **DERIVED** = I computed it from SWC files or from quoted numbers, **RECALLED** = from memory, not checked, **NOT FOUND**. Most sources were seen through a summarising fetch tool or a search snippet, not the original PDF, so treat every literature number as "checked at snippet level" until someone opens the paper.

## 1. What was measured on our side
E4 = recipe V1 arbor: interneuron axons van Pelt branching with B_inf 20 (tau 1,681,541, E 0.319251), interneuron dendrites B_inf 3.5 (tau 259,680, E 0.73), 20 interneurons and 96 pyramidal cells in a slab with soma centres spread over about 222 x 234 x 29 um (seed 33333 as an example), line-379-fixed build, grown 25 simulated days. Pyramidal arbors are not customised by the recipe (they use the base configuration of the earlier phases, which was not tuned to CA3). Ten networks (seeds 16180, 27182, 31415, 11111, 22222, 33333, 44444, 55555, 66666, 77777).

Definitions (so the numbers are comparable):
- Length = sum of Euclidean distances from every node to its parent node, per cell and fibre class (soma-to-root stub not counted). Units are um as written in the NetMorph coordinate files (I assumed um; the soma radius of 7-8 um is consistent with that).
- Branch points = number of `bifurcationnodes`; tips = number of `growthcones`.
- Extent = Euclidean distance from the soma centre to the farthest node ("max") and the 90th percentile of node distances ("p90"), as per-cell means.
- Values below are the mean over the 10 networks of the per-cell mean, with the SD across the 10 networks. Per-cell spread within a network was not summarised here (the earlier logs give, e.g., interneuron axon length 22,222-71,884 um across the 20 cells of one network).

| our E4 cells (10 networks) | total length (um) | branch points | tips | max distance from soma (um) | p90 distance (um) |
|---|---|---|---|---|---|
| interneuron axon (20 per network) | 43,600 (SD 2,200; network range 40,210-45,755) | 204 (range 187-215) | 205 | 136 (122-147) | 101 |
| interneuron dendrite | 6,699 (SD 444; range 5,923-7,163) | 27 (24-29) | 35 (31-37) | 309 (300-317) | 206 |
| pyramidal axon (96 per network) | 19,825 (SD 1,022; range 18,397-21,348) | 73 (68-79) | 74 | 132 (125-140) | 101 |
| pyramidal dendrite | 27,922 (SD 2,898; range 23,640-33,174) | 60 (53-70) | 67 (60-77) | 702 (693-713) | 459 |

Consistency check with earlier measurements: the interneuron axon and dendrite means agree with the per-network values in the earlier analyze logs (e.g. seed 33333: 44,763 and 6,917 um).

## 2. Published values and comparison

### 2a. PV basket / interneuron
| Quantity | Published value | Source | Status | Our E4 | Verdict |
|---|---|---|---|---|---|
| Axon total length, rat CA3b interneurons (not PV-identified, slice, axon partly cut) | 21,535 +/- 12,042 um (R type, n=7); 25,081 +/- 10,938 (L-M type, n=6) | Ascoli GA, Brown KM, Calixto E, Card JP, Galvan EJ, Perez-Rosello T, Barrionuevo G (2009) J Comp Neurol 515:677-695 (title from memory: "Quantitative morphometry of electrophysiologically identified CA3b interneurons reveals robust local geometry and distinct cell classes"); data via https://pmc.ncbi.nlm.nih.gov/articles/PMC2827149/ Tables 4-6 | READ (fetch of first 100k of 180k characters; earlier note CA3_INTERNEURON_ARBOR_REFS.md) | 43,600 | about 1.7-2.0x the slice means; the slice axons are lower bounds, so not evidence of too long |
| Axon bifurcations, same cells | 192 +/- 72 (R), 289 +/- 83 (L-M) | same | READ | 204 | inside |
| Axon total length, CA3 PV basket cells from NeuroMorpho SWC files (slice, partial axons) | rat Somogyi #10716: 25,814; mouse Peng #165014: 28,868; mouse McBain #49377: 59,018; mouse Heistek #10658: 21,148 um | NeuroMorpho.Org (neuron IDs as listed); I summed type-2 SWC segments (CA3_INTERNEURON_TYPES.md) | DERIVED (SWC downloaded earlier; not re-run today) | 43,600 | inside the 21k-59k spread |
| Axon total length, CA1 PV basket cell (fallback, not CA3) | 46,180 um; bouton density 22.6 per 100 um; 10,440 boutons (derived by the authors) | Sik et al. 1995 as quoted in Bezaire & Soltesz (2013) Hippocampus 23:751-785, https://pmc.ncbi.nlm.nih.gov/articles/PMC3775914/ | READ (second-hand) | 43,600 | close |
| Axon extent / lateral spread from soma, CA1 PV BC | 780-1,740 um lateral extent | review PMC6132631 (earlier note; authors not captured) | READ (snippet) | 136 max, 101 p90 | **about 6-13x smaller than the published lateral extent** |
| CA2/3 PV BC axon area (in vivo, n=3) | 0.666 +/- 0.223 mm^2, no length given | https://pmc.ncbi.nlm.nih.gov/articles/mid/EMS63728 (manuscript version; I take it to be Tukker et al. 2013, J Neurosci 33:6809, doi 10.1523/JNEUROSCI.5052-12.2013 because a search for the title returned both; not confirmed) | READ (earlier note) | not computed | not comparable |
| Dendrite total length, rat CA2/3 PV BC in vivo (n=4) | 10,037 / 9,213 / 9,218 / 7,662 (mean 9,032 +/- 992) um | same EMS63728 Table 2 | READ (fetch; earlier note) | 6,699 | 26% below the mean; our value is about 2.4 of their SD below (n=4, so a weak statement) |
| Dendrite total length, mouse CA3 PV BC | mean 5,021 +/- 1,306 (n=8; range 3,620-7,539) | NeuroMorpho.Org Hajos-lab cells, dendrite-only SWC sums | DERIVED (no axons in those files) | 6,699 | inside |
| Dendrite length, CA1 vertical PV BC | 4,347 +/- 1,125 um | Gulyas et al., quoted in a 2018 Cell Tissue Res review (snippet) | READ (snippet, second-hand) | 6,699 | within about 2 SD |
| Dendrite length, rat CA3b interneurons (slice) | 2,910 +/- 1,387 um (R); 3,217 +/- 2,900 (L-M) | Ascoli 2009 (PMC2827149) | READ | 6,699 | about 2x slice means (slice dendrites are about 3x shorter than in vivo PV BC by the same notes) |
| Dendritic bifurcations, same cells | 30.3 +/- 25.7 (R), 24.5 +/- 19.6 (L-M) | Ascoli 2009 via neuroelectro table extraction | READ (secondary) | 27 | inside |
| Primary dendrites per cell | 3.08 +/- 1.26 (all 13 cells pooled; 1-6) | Ascoli 2009 | READ | not counted today (tips 35, branch points 27 imply about 8 stems or tips beyond bifurcations; not a stem count) | not compared |
| CA3 PV BC axon bouton count, CA3 PV BC divergence | NOT FOUND | | NOT FOUND | | |
| Allen Cell Types Database, Human Brain Project / Blue Brain portal | not used: I did not find CA3 PV basket morphologies in either (Allen's database is neocortex-focused; the Blue Brain hippocampus model is CA1) | | RECALLED (not checked this session) | | |

### 2b. CA3 pyramidal cell
| Quantity | Published value | Source | Status | Our E4 | Verdict |
|---|---|---|---|---|---|
| Dendrite total length, rat CA3 pyramidal (slice, HRP fills, position dependent) | 9,300 um (cells nearest dentate gyrus) to 15,800 um (cells nearest CA2) | Ishizuka N, Cowan WM, Amaral DG (1995) J Comp Neurol 362:17-45, doi 10.1002/cne.903620103, "A quantitative analysis of the dendritic organization of pyramidal cells in the rat hippocampus" (abstract values via search snippet today) | READ (abstract snippet) | 27,922 (range 23,640-33,174) | **our pyramidal dendrite is about 1.8-3.0x longer than these values** |
| Same, as listed in a later review table | 12,481 +/- 2,999 um | https://pmc.ncbi.nlm.nih.gov/articles/PMC6792859/table/T1 (title and authors not captured; attributed to Ishizuka 1995 in the snippet) | READ (snippet, second-hand; not checked against the paper) | 27,922 | about 2.2x |
| Dendritic branch points per CA3 pyramidal cell | the paper reports branch numbers, but I did not retrieve them | | NOT FOUND | 60 | not compared |
| Dendrite extent from soma | NOT FOUND (not retrieved) | | NOT FOUND | 702 max, 459 p90 | not compared; note that 702 um exceeds the slab width of about 222 x 234 um |
| Axon total length, CA3 pyramidal | "150-300 mm typical"; "200 mm (CA3b) to 500 mm (CA3c)"; >0.5 m and about 40,000 boutons for a CA3c cell; 15,295 boutons (Sik 1993) | search snippets summarised in CA3_ARBOR_BOUNDS.md; Sik, Tamamaki, Freund (1993) Eur J Neurosci for the bouton count; Wittner et al. 2007 (Brain Struct Funct, from memory) for the long axon | READ (snippets; primary papers not opened); author/journal for Wittner RECALLED | 19,825 (range 18,397-21,348) | **about 8-25x shorter than 150-500 mm** |
| Axon branch points / tips, CA3 pyramidal | not found; boutons about 15,000-40,000 | as above | NOT FOUND (boutons only) | 73 / 74 | our axon has orders of magnitude fewer branches than boutons in the real cell; not comparable like for like |
| Axon extent | millimetres (spans much of CA3 and goes to CA1; Wittner 2007, snippet) | | READ (snippet) | 132 max | about 1/10-1/100 or less; a truncated local axon |

## 3. What the comparison shows (and does not)
1. **Interneuron arbors are not obviously wrong in total size or branching.** Interneuron axon length (43,600 um) sits between slice-based CA3 values (21-59k um, cut axons) and the CA1 PV value (46k um); axon bifurcations (204) are inside Ascoli's 192 +/- 72 / 289 +/- 83; dendrite bifurcations (27) are inside 24-30 +/- 20-26; dendrite length (6.7k um) is between CA1/mouse PV values (4.3-5.0k) and the in vivo CA2/3 PV value (9.0k). This is the part that bears on the earlier assumption that interneuron outgrowth was too small; on these measures it is not, but I only compared totals and branch counts.
2. **Reach is the exception.** Our interneuron axon reaches 136 um at most (p90 101 um) from the soma, while published CA1 PV axons spread 780-1,740 um laterally. So we have about the right amount of axon packed into a region 6-13x smaller in radius. That means a locally very dense axon, which would raise contacts per nearby pair. This is an inference from two numbers (our reach, one CA1 review value); I did not check whether the region or the simulated time limits the reach.
3. **Pyramidal dendrites are too long compared with the Ishizuka values** (27.9k um vs 9.3-15.8k um), and pyramidal axons are far too short and unbranched compared with a real CA3 axon. I did not test whether the long dendrites are the reason the recipe needs a very small pyramidal D_synmax (0.0175 versus the 1.5 limit), but it is a candidate cause worth checking: the dendrite default statistics come from cultured cells (2008), as Randal pointed out, and I did not change them.
4. **Pyramidal axon length is not a like-for-like comparison.** Most of a real CA3 axon lies outside a 220 um patch; our axon is the part grown inside the simulation. The amount of a real axon that would fall inside a 220 x 234 x 29 um patch was not computed.
5. **Not done:** branch counts and extent for CA3 pyramidal dendrites, PV primary-dendrite counts, bouton counts for the PV axon, Sholl profiles, any spatial inspection of the grown morphology (Randal's suggestion), and the Allen / HBP numbers. If those data are used, the references must go into the build docs, as Randal asked.

## 4. Data provenance
- Ours: NetMorph output folders (`*_net.txt.neurons`, `.rootnodes`, `.continuationnodes`, `.bifurcationnodes`, `.growthcones`) under `/home/johnjose/BrainGenix/wt/linefix-instance/out/Admonishing/NetmorphOutput/<uuid>/`; the uuids are in `models.json`. Script: `morph_e4.py`; output `morph_e4.json` (per network, per cell type and fibre). The SD in section 1 is across networks, not across cells.
- Literature: recipe_v2/CA3_INTERNEURON_ARBOR_REFS.md, CA3_INTERNEURON_TYPES.md, CA3_ARBOR_BOUNDS.md, CA3_NATURAL_RANGES.md (earlier sessions); two searches today (Ishizuka 1995 abstract; Tukker 2013 / EMS63728 title).
- Allen / HBP: no numbers used.
