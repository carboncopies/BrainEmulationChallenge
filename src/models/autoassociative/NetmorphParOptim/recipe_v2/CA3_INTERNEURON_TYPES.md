# CA3 interneuron types: morphometrics and role in lateral/feedback inhibition

Date 2026-11-13. Literature/database task, no NES runs.

Tags: READ = number seen in source text (fetched page text; WebFetch summarises with a small model, so "READ" means the fetch output stated it, I did not see the raw page). DERIVED = computed by me from raw SWC files downloaded from NeuroMorpho.Org. RECALLED = from memory, not verified here. Anything not found is marked NOT FOUND.

## 0. How "total dendritic length" is defined in each source

| Source | Definition | Tag |
|---|---|---|
| NeuroMorpho.Org `length` field (API `/api/morphometry/id/<id>`) | Its FAQ lists "Total arborization length" and says "each of these parameters is extracted from the whole neuron (axon plus dendrites)". The exact L-Measure definition is not on the FAQ page (it defers to L-Measure). So for any cell with a reconstructed axon, the `length` field is axon + dendrite, NOT dendrite alone. My own check on SWC files confirms the field equals the sum of all neurite segment lengths (soma excluded): e.g. Somogyi rat PV basket 10716 `length` 36,450 vs DERIVED dend 10,636 + axon 25,814 = 36,450. | READ (FAQ https://neuromorpho.org/myfaq.jsp) + DERIVED |
| NeuroMorpho dendrite-only length | Not served as a field; I computed it from SWC (type 3 + 4 = dendrite, type 2 = axon), Euclidean distance summed over parent-child points. | DERIVED |
| Hippocampome.org | Neuron-type pages give only layer (e.g. CA3:SL) labels for axon/dendrite/soma, no numeric length (checked CA3 Granule page id=2001 and morphology.php). A 2024 eLife preprint on v2.0 (https://elifesciences.org/reviewed-preprints/90597) describes computing dendritic and axonal path lengths from 2D reconstructions, per search snippet only. Hippocampome gives no usable CA3 interneuron length values. | READ (negative) |
| Ascoli lab CA3b interneuron paper (rat slice) | Neurolucida tracing, lengths of "dendrites" and "axon" reported separately, axon likely incomplete (slice). See existing notes. | READ (earlier notes, PMC2827149) |
| Szabadics-style AAC paper (Viney et al. 2013 Nat Neurosci) | "Total dendritic length per stratum" from Neurolucida Explorer on shrinkage-corrected reconstructions (x-y 1.06, z about 1.3-1.4 expansion). Only percentages per layer in text (sOri+alveus 46.7 +/- 6.7%, sRad 11.8 +/- 8.3%, sPyr 4.9 +/- 2.4%, sLuc 1.9 +/- 0.4%, n=3 CA3 AACs); no absolute length. | READ https://pmc.ncbi.nlm.nih.gov/articles/PMC4471148 |
| Review PMC6132631 (CA1 mostly) | "overall dendritic length", i.e. dendrite-only total. | READ |
| BBP portal | Not accessed (no tool route; the BBP/Hippocampus Hub model is CA1). Not a CA3 interneuron source. | NOT FOUND |

Main trap: NeuroMorpho "length" for a PV basket cell with axon (e.g. 36-65 mm) is mostly axon. Use the dendrite-only numbers below for dendritic length.

## 1. Table by cell type

Species caveat: NeuroMorpho CA3 interneurons are mostly mouse (Hajos, McBain, Peng, Anstoetz, Nacher) or rat slice cells (Jaffe, Ascoli, Somogyi). "Axon" lengths from slices are lower bounds (cut axons). All lengths in um. NeuroMorpho IDs are neuron_id.

| Type | Axon length / arbor extent | Dendritic length (dendrite-only, definition) | Pyr targets per cell | Synapses per pair | Role in lateral/feedback inhibition |
|---|---|---|---|---|---|
| PV basket (BC) | Rat CA3 Somogyi #10716: axon 25,814 (DERIVED, NeuroMorpho, shrinkage reported, axon "Moderate"). Mouse Peng #165014: 28,868; mouse McBain #49377 (inner CA3): 59,018; mouse FS Heistek #10658: 21,148 (all DERIVED, SWC type 2). Rat CA2/3 in vivo PV BC axon AREA 0.666 +/- 0.223 mm2, n=3, no length (READ, EMS63728). CA1 PV BC lateral axon extent 780-1740 from soma (READ, PMC6132631); CA1 axon length 46,180 (READ via Bezaire 2013, PMC3775914) as fallback. | Rat in vivo CA2/3 PV BC: 10,037/9,213/9,218/7,662, mean 9,032 +/- 992, n=4 (READ, EMS63728 Table 2; total dendritic length). Rat Somogyi #10716 dend 10,636, #10717 9,460, #10718 9,272 (DERIVED, dendrite-only). Mouse Hajos PV BC n=8: mean 5,021 +/- 1,306 (range 3,620-7,539; DERIVED, no axon, "Dendrites Moderate"). Mouse Peng 5,357. CA1 vertical PV BC 4,347 +/- 1,125 (READ). | NOT FOUND for CA3. CA1 model: 943 PC + 71 interneurons contacted (DERIVED by Bezaire, READ). CA1 >1000 to >1500 PCs (Sik 1995, second-hand search snippet). | ~11 synapses per BC->PC connection (READ, Foldy 2010 mouse via PMC3775914, CA1 model). PC->interneuron mostly 1 bouton (Sik 1993 CA3: 84.7% single contacts, 2.1% of 15,300 boutons on PV cells; READ via search snippet). | Strongest candidate. Kohus 2016 CA3 paired recordings: PV BC and AAC uIPSCs faster, shorter latency, larger than CCK BC; PV BC inhibition "may be responsible for the refractory mechanism between SWRs" and may contribute to SWR generation (READ, https://pmc.ncbi.nlm.nih.gov/articles/PMC4929320). Strong PV BC<->PV BC reciprocity: CP 66.6%, uIPSC 81 pA, latency 0.76 ms (READ). CA3 model: BC silencing reduced SWR occurrence; BCs act mainly via BC-BC mutual inhibition (READ, PMC12146282, model not data). |
| Axo-axonic / chandelier (AAC) | Rat Somogyi chandelier #49814: axon 2,339 (partial, DERIVED); axon not quantified in Viney 2013 (READ negative). Radial "cartridge" boutons around sPyr-sOri border (READ). | Rat Somogyi chandelier: 6,768 / 7,815 / 8,266 (DERIVED). Mouse Hajos chandelier n=15: mean 3,563 (range 2,599-6,811) and horizontal chandelier n=2 about 3,856 (DERIVED, no axon). CA1 AAC 3,325 (READ, PMC6132631). | NOT FOUND. Targets are the axon initial segment (EM synapse counts per AAC 7-14 on AISs of sampled cells, READ, PMC4471148). | One AAC axon cartridge per AIS, multiple synapses per cartridge (qualitative). RECALLED. | Kohus: AAC->PC uIPSC fast/large like PV BC (READ, n=9 pairs). Controls spike initiation at AIS; plausible part of shut-off, but SWR-termination role not established in sources I read. Viney 2013 states AACs fire during SWRs (RECALLED; not verified in read text). |
| CCK basket | Mouse McBain #36082 (CCK+/SOM+, stratum radiatum): axon 11,103; #36083 CGE-derived: 8,826; MFA-like #49381 (VIP+/CCK+, lucidum): 8,818 (all DERIVED, mouse, slice, subtype labels are McBain's and mixed). | Mouse #36082: 6,907; #36083: 7,329; #49381: 7,366 (DERIVED). CA1 CCK BC 6,338 +/- 986 (READ, PMC6132631). | NOT FOUND | NOT FOUND | Not the fast feedback shut-off. Kohus: CCK BC transmission slower, facilitating, asynchronous release, "more subtle, graded control" (READ). Reciprocal CCK-CCK CP 42.85% (READ). In the 2025 CA3 model CCK cells inhibit SWR generation mainly via direct CCK->PC synapses (READ, PMC12146282; paper contradicts itself on whether CCK->PC exists in the model; model not data). In vivo SWR snippet: CCK activity falls before ripple, PV BC rises after (search snippet, not verified). |
| Bistratified | CA1 total axon 78,800; extent 1,860 septo-temporal x 2,090 medio-lateral (READ, PMC6132631). CA3: NOT FOUND (no CA3 bistratified in NeuroMorpho subset I queried; labelled "interneuron" only). | CA1 not reported in that review. CA3: NOT FOUND. | NOT FOUND | NOT FOUND | Dendrite-targeting (oriens + radiatum); fires strongly in SWRs alongside PV BCs in CA1 and CA3 recordings (search snippet, unverified). Feedback onto apical/basal dendrites, secondary to perisomatic cells for fast shut-off. |
| OLM | CA1 axon over 63,000, spread 840 x 500 (READ, PMC6132631). CA3 OLM: transverse spread 223, dorsal-ventral 1,200-1,300 (READ via same review). NeuroMorpho CA3 OLM #168584 has no axon. | Mouse Anstoetz CA3 OLM #168584: 2,449 (DERIVED, dendrites only, no axon). SOM+ Nacher (mouse CA3 s. oriens, n=32, dendrites only, "Moderate" completeness): mean 1,359 (range 457-2,623; DERIVED), likely partial. | NOT FOUND | NOT FOUND | Targets distal apical dendrites in lacunosum-moleculare; feedback onto EC input, not onto somatic output. Not main driver of post-recall pyramidal shut-off (RECALLED/inference; the sources I read do not test it). |
| Ivy / neurogliaform | Mouse McBain #36057 and #36059 (MGE late-spiking ivy/NGF, radiatum): axon 15,610 and 22,477 (DERIVED). | 6,768 and 5,576 (DERIVED). | NOT FOUND | NOT FOUND | Slow, volume-transmitted GABA-A/B; tonic-like inhibition. Not a fast feedback source. RECALLED. |
| Unclassified CA3 interneurons, rat | Ascoli rat CA3b slice, n=12: axon mean 24,230 +/- 11,065 (range 11,815-44,197; DERIVED). Paper (R type, L-M type) gives 21,535 +/- 12,042 and 25,081 +/- 10,938 (READ, PMC2827149). | DERIVED mean 3,151 +/- 2,180 (range 1,265-8,909). Paper: 2,910 +/- 1,387 (R), 3,217 +/- 2,900 (L-M) (READ). Jaffe rat CA3 n=59 dendrite-only (axon not reconstructed): mean 2,901 (NeuroMorpho `length`, DERIVED stats, range 459-7,599). | n/a | n/a | Mixed population, none PV-identified. Slice dendrites about 3x shorter than in vivo PV BC (9,032). |

## 2. Which type does lateral/feedback inhibition after a recall burst

Ranked, with evidence level:
1. PV basket cells (perisomatic). Best-supported: fast, large, short-latency unitary IPSCs onto PCs; strong PV-PV reciprocity; paired-recording authors explicitly propose PV BC inhibition as the SWR refractory mechanism (READ, Kohus 2016). Model evidence that BCs control burst occurrence via BC-BC inhibition (READ, model).
2. Axo-axonic cells. Same fast kinetics (READ, Kohus), act at the AIS; second-order contributor.
3. Bistratified. Dendritic feedback, active during SWR (snippet only).
4. CCK basket. Slow, graded, asynchronous, modulatory; sets inhibitory tone before the burst, not the rapid cutoff.
5. OLM and ivy/NGF. Dendritic/slow, minimal role for rapid shut-off.

Caveat: none of the sources I read measured pyramidal-cell shut-off after a CA3 recall burst directly for each type; ranking rests on synaptic kinetics, connectivity and SWR studies.

## 3. Gaps (not found)
- CA3 PV BC axon length with complete axon in vivo; pyramidal targets per CA3 BC; synapses per pair in CA3 (only mouse/CA1 fallback ~11).
- Any CA3 bistratified morphometrics in NeuroMorpho (not tagged as such in the subset).
- BBP portal CA3 interneurons (BBP model is CA1).
- Numeric Hippocampome morphometrics (layer labels only).
- Viney 2013 text covered chars 0-100k of 120k; last 20k unread.

## 4. Ten-line summary for our interneuron arbor settings
1. Model the interneuron population as mostly PV basket cells (plus optionally a few AACs); give CCK/OLM/bistratified at most a minor share.
2. Dendritic length target for a PV basket cell: about 5,000-9,000 um (mouse Hajos mean 5,021; rat in vivo CA2/3 9,032; rat Somogyi 9,300-10,600). Use about 9,000 for a rat-scaled network; lower end only if the pyramidal cells are also shrunk.
3. Dendrite-only: do not use NeuroMorpho "length" as dendritic length when an axon is traced (it is axon + dendrite; PV BC 36-65 mm).
4. Axon length for a PV basket cell: roughly 25,000-60,000 um (DERIVED, slice, lower bounds); CA1 anchor 46,180 um. Use about 30,000-45,000 um as the working range.
5. Axon spatial extent: keep it at a few hundred to about 1,700 um lateral (CA1 780-1,740 um from soma); CA3 PV BC axon area about 0.67 mm2 (rat in vivo). For a small network scale to the tissue block so the axon covers essentially all pyramidal somata.
6. Dendrites of AACs are shorter, about 3,500-8,000 um; arbor concentrated at the pyramidal layer border with bouton cartridges; low priority.
7. Pyramidal targets per basket cell: NOT FOUND for CA3; with 96-128 pyramidal cells, target near full coverage (CA1 model fraction 943 of about 311,500 PCs is tiny, so full coverage is a deliberate deviation).
8. Synapses per BC->PC pair: use about 11 (mouse, CA1 model, READ via Bezaire); PC->interneuron 1 synapse per pair (READ, Sik 1993).
9. Interneuron:pyramidal ratio about 1:8 in the literature (assumed 11%, Bezaire); our 16-48 on 96-128 is 1:2.7 to 1:8, so keep the low end (16 per 128) if matching biology.
10. Reciprocal BC-BC wiring (CP about 0.67 in paired recordings, READ) should be included if the simulator allows interneuron-to-interneuron synapses; this is what makes the burst shut-off fast.
