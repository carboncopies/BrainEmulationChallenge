# inhib_e Part 1: a sourced target for the inhibitory fraction (2026-11-17, research only, no sims)
Marks as in ../lit_review: VERIFIED = number read in the paper's own text or abstract this session; SNIPPET ONLY = seen in a search-result summary, source not opened; RECALLED = from memory, not checked; DERIVED = my arithmetic. Three full-text fetches (Stepanyants 2009, Iascone 2020 on PMC) were blocked by a bot check, so several key numbers are SNIPPET ONLY.

## 1. Census values: inhibitory share of ALL synapses onto a pyramidal cell
| quantity | value | source | mark |
|---|---|---|---|
| CA1 pyramidal cell, rat: excitatory / inhibitory inputs | about 30,000 / 1,700 -> 5.4% inhibitory (DERIVED) | Megias, Emri, Freund, Gulyas 2001, Neuroscience 102:527 | VERIFIED (abstract as returned by search; paper not opened) |
| same cell, by compartment | proximal dendrites 70-100% inhibitory; distal spiny dendrites about 3%; soma inhibitory only (77-103 per cell) | same | VERIFIED (abstract) |
| L2/3 pyramidal neuron, mouse: one fully mapped cell | 8,115 spines, 1,045 inhibitory synapses -> 11.4% (DERIVED) | Iascone et al. 2020, Neuron 106:566 (preprint text) | SNIPPET ONLY |
| cortical neuropil, juvenile rat S1 (FIB/SEM, 6,184 synapses) | symmetric 6-13%, asymmetric 87-94% | Merchan-Perez / DeFelipe group | SNIPPET ONLY |
| cortical neuropil, review figure | about 95:5 asymmetric:symmetric | Frontiers Neuroanat 2024 review (DeFelipe group) | SNIPPET ONLY |
| "excitatory synapses 80-90% of cortical synapses" | implies 10-20% inhibitory | Brain Struct Funct 2017 paper, general statement | SNIPPET ONLY |
| CA3 pyramidal cell whole-cell E and I counts | not found (only: about 140 somatic terminals in CA3 vs about 60 in CA1) | | NOT FOUND / SNIPPET ONLY |
So the census value is about 5% (CA1) to 11-13% (neocortex). The old 3-6% band matches the CA1 census by coincidence; "10-20%" is the loose neocortical statement. Neither was ever sourced for our use.

## 2. Is A comparable to a census ratio? No
A = Int->Pyr / (Int->Pyr + Pyr->Pyr), counted inside a closed patch of 96 pyramidal cells in a disc of radius 120 um.
- A census counts every synapse on the cell. Most excitatory synapses come from cells outside any small patch: 92% of excitatory synapses near the axis of a 200 um column come from outside it, still 76% for an 800 um column (Stepanyants et al. 2009 PNAS 106:3555, cat V1; SNIPPET ONLY). In CA3 the local recurrent connection probability is 0.92% (146 connections in 15,930 pairs, not falling with distance up to 400 um; Guzman et al. 2016 Science; VERIFIED in the PDF text), and CA3 cells also receive mossy-fibre and perforant-path input from outside CA3.
- Inhibitory synapses come mainly from nearby interneurons (basket cell axons are local; RECALLED, the Stepanyants inhibitory figure could not be read).
- Scale check (DERIVED): our pyramidal cells receive about 50 Pyr->Pyr and about 70-115 Int->Pyr synapses from the patch, against about 31,700 inputs on a real CA1 cell. The patch supplies well under 1% of a cell's excitatory input, so a within-patch ratio cannot be read against a whole-cell census.
Conclusion: a census value (5-13%) is the wrong yardstick for A. A within-patch target has to be derived.

## 3. Derived within-patch target (DERIVED from the sourced numbers above plus stated assumptions)
Route 1, from census counts: local A = I_local / (I_local + E_local), with E_local = 8% of excitatory inputs (200 um column figure; our disc is 240 um across) and I_local = 50-100% of inhibitory inputs (assumption, unsourced).
- CA1 counts (30,000 / 1,700): E_local 2,400, I_local 850-1,700 -> A 26-41%.
- L2/3 counts (8,115 / 1,045): E_local 650, I_local 520-1,045 -> A 44-62%.
Route 2, from the per-pair bars we already use: A = N_int x P x s (Int->Pyr) / (that + 9,120 x P x s (Pyr->Pyr)). With Pyr->Pyr probability 0.2 and 3 synapses per pair (mid-band), Int->Pyr probability 0.5 (as grown) and 6 per pair (mid-band): 12 interneurons (11% of cells) -> 39%; 20 -> 52%; 24 -> 57%; 30 -> 62%.
Both routes say a closed local patch with biological per-pair values has A of roughly 25-50%, not 5%. Proposed target replacing the 3-6% band: **within-patch A 25-50%, a derived band, not a measured one.** It rests on one snippet-only figure (92% of excitation from outside a 200 um column) and one unsourced assumption (how local inhibition is), so it should be treated as a working band until Stepanyants 2009 is read in full.
For CA3 specifically the local excitatory share is probably lower still (0.92% connection probability), which would push the comparable A higher, not lower.

## 4. Interneuron fraction, and what 96 + 30 in this disc implies
| quantity | value | source | mark |
|---|---|---|---|
| CA3 interneurons relative to principal cells | 13% (CA1-2 8%; Ammon's horn 9.5%) -> 11.5% of all neurons (DERIVED) | GAD65 mRNA count, rat, Acta Biol Hung 2013 | SNIPPET ONLY |
| GABA-immunoreactive cells within the pyramidal layer, CA1-CA3 | 5-8% | older rat study (J Comp Neurol) | SNIPPET ONLY |
| CA1 interneurons | 8.0% (27,240 / 311,500, DERIVED) to 11% | Bezaire et al. 2016; Bezaire & Soltesz 2013 | READ earlier (../CA3_NATURAL_RANGES.md) |
| cortex and hippocampus generally | 15-30% | Tepper et al. 2018 via BioNumbers | VERIFIED text (secondary) |
- 96 pyramidal + 30 interneurons = 23.8% interneurons: inside the general 15-30% statement, about twice the CA3 figure (11.5%). At 11.5% the patch would hold 12-13 interneurons. 24 interneurons = 20.0%, 20 = 17.2%.
- Disc volume pi x 120^2 x 30 um^3 = 0.00136 mm^3; 126 cells -> about 93,000 neurons per mm^3 (DERIVED). CA3 pyramidal-layer density: NOT FOUND.
- All 30 interneurons are grown as one PV-basket-like type. In tissue PV cells are a minority of interneurons (about 40% in mouse S1, SNIPPET ONLY in ../lit_review), so 30 perisomatic-type cells per 96 pyramidal cells over-represents this class several-fold.

## 5. What this means for the experiment
A falls with fewer interneurons and with lower interneuron D, but per-pair Int->Pyr (bar 4-9) falls with D too. Offline predictions (offline.py, offline_results.json) say 20-24 interneurons at interneuron D 0.02-0.03 give A of about 37-58%, i.e. at or just above the top of the derived band, with Int->Pyr per pair at the bottom of its band at D 0.02. Reaching the middle of the band would need about 12 interneurons, which is outside this design.
