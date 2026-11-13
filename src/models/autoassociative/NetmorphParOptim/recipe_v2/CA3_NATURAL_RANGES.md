# CA3 natural ranges for NetMorph growth parameters (literature pass, 2026-11-12)

Legend: READ = number appeared in text I fetched or in a search-result snippet this session; RECALLED = from memory, not verified here; DERIVED = my arithmetic on READ numbers. Several primary sources (PMC 2013 Bezaire & Soltesz, Tukker 2013, Sik 1995, bioRxiv full text) were blocked (403/429/captcha), so detailed morphometry is mostly NOT FOUND. No NES/API/simulation used.

## 1. Cell ratio and density

| Quantity | Value | Range | Source | Status |
|---|---|---|---|---|
| Ecker et al. CA3 SWR model: PCs / PV basket cells | 8000 PC, 150 PVBC (1.8% PVBC; ~1.9% of 8150) | fixed | Ecker, Bagi, Vertes ... Hajos, Freund, Kali, eLife 2022 (PMC8865846), doi 10.7554/eLife.71850 | READ. Note: only PVBCs modeled, not the whole GABAergic population, so it is a sub-class count, not an interneuron fraction. Sized to "CA3 of a 600 um-thick mouse slice"; justified by Schlingloff 2014, Bezaire & Soltesz 2013, Donoso 2018, Evangelista 2020 |
| Bezaire 2016 CA1 model, rat: pyramidal / interneuron | 311,500 / 27,240 (8.0% interneurons, DERIVED) | modeled 8 types = ~70% of CA1 interneurons | Bezaire, Raikov, Burk, Vyas, Soltesz, eLife 2016 5:e18566, doi 10.7554/eLife.18566 (PMC5313080) | READ |
| Per-type counts, same model (CA1) | PV basket 5,530; CCK basket 3,600; bistratified 2,210; axo-axonic 1,470; OLM 1,640; neurogliaform 3,580; ivy 8,810; SC-A ~400 (DERIVED by subtraction) | | same | READ |
| Bezaire & Soltesz 2013 assumption | interneurons = 11% of CA1 cells | | Hippocampus 23:751-785, doi 10.1002/hipo.22141 | READ only via search summary; full text blocked |
| CA1 GABAergic fraction (Kosaka/Aika disector) | ~7% of all neurons | | KAKEN grant report summary of rat disector counts | READ (secondary, grant summary) |
| CA3 GAD65 mRNA+ cells relative to principal cells | 13% in CA3 vs 8% in CA1-2 | | Acta Biol. Hung. 2013 (authors not captured) | READ in search snippet, unverified; denominator is principal cells |
| Rat CA3 total neuron number (male) | ~210,000 | strain differences in CA3/CA2 | bioRxiv 10.1101/2025.04.16.649153 (Arellano & Rakic, "Updated neuronal numbers of the rat hippocampal formation") | READ in abstract only |
| CA3 interneuron fraction, Freund & Buzsaki 1996 | commonly quoted ~10-15% of neurons; CA3 slightly higher than CA1 | | Freund & Buzsaki, Hippocampus 6:347-470, 1996 | RECALLED, not verified |
| Cell density per mm^3 in CA3 pyramidal layer | not found | | | NOT FOUND |
| Per-layer interneuron counts in CA3 | not found | | | NOT FOUND |

Key point: the Ecker model's "low interneuron fraction" is a modeling choice (PVBC only, 1.8%), while anatomical CA1 estimates are 7-11% and CA3 is believed a little higher (13% vs 8% by GAD65 relative to principal cells). Nothing I found supports 33%.

## 2. Interneuron morphology

| Quantity | Value | Source | Status |
|---|---|---|---|
| CA2/3 PV basket cell dendrite: share in stratum lacunosum-moleculare | 33% of length, 29% of surface, 24% of synaptic input; total synaptic input ~35,000 | Tukker, Lasztoczi, Katona, ... Klausberger, Somogyi, J Neurosci 33:6809, 2013, doi 10.1523/JNEUROSCI.5052-12.2013 (in vivo juxtacellular, rat) | READ (abstract). Absolute dendritic length: NOT FOUND |
| Basket cell axon reach (CA1, in vivo, rat) | one basket cell contacts >1500 pyramidal cells and 60 PV interneurons; axon confined to pyramidal layer | Sik, Penttonen, Ylinen, Buzsaki, J Neurosci 15:6651, 1995, doi 10.1523/JNEUROSCI.15-10-06651.1995 | READ (abstract). Axon length/boutons: NOT FOUND |
| Synapses onto PV interneurons (CA1) | 16,294 mean (PV) vs 3,839 (CB) vs 2,186 (CR) | Gulyas, Megias, Emri, Freund, J Neurosci 1999 | READ (snippet) |
| Total axon length, bouton number, primary dendrite number, arbor extents for PV BC, CCK BC, OLM, bistratified, axo-axonic in CA3 | NOT FOUND | | Candidates to fetch: Ascoli et al. 2009 (CA3b interneuron morphometry), Hippocampome.org, NeuroMorpho.org, Bezaire & Soltesz 2013 tables, Sik 1995 full text |
| Comparison: CA3 pyramidal cell axon (in vivo, rat) | ~15,000 boutons (Sik 1993); CA3c axon >0.5 m long, ~40,000 boutons (Wittner 2007) | | READ (snippet) |
| Bezaire model used dendritic lengths to set inhibitory connectivity | values not in readable text | eLife 2016 | READ, but numbers NOT FOUND |

## 3. Connectivity

| Connection | Value | Source | Status |
|---|---|---|---|
| PC->PC (CA3) | 10% assumed in Ecker; measured <1% (Guzman 2016, rat and human), ~9% reported in a mouse-slice study | Ecker 2022; Guzman et al. Science 2016; J Neurosci 2025 citation | READ (secondary) |
| PC->PVBC (CA3 model) | 0.10 | Ecker 2022 Table 3 | READ |
| PVBC->PC (CA3 model) | 0.25 | Ecker 2022 Table 3 | READ |
| PVBC->PVBC (CA3 model) | 0.25 | Ecker 2022 | READ |
| Interneuron -> pyramidal, interneuron->interneuron, PC->interneuron probabilities from slice paired recordings | not found | | NOT FOUND |
| Synapses per connection | CA1 model: 1-10 synapses per connection; CA3 input to CA1 PC = 2 synapses per connection (5,985 connections); Ecker: not reported | Bezaire 2016 Table 1/5 | READ |
| Somatic inhibitory terminals per pyramidal cell | ~60 (CA1) and ~140 (CA3); ~60% PV+, 35-40% CB1+ | 2015 ultrastructural study (Struct. Funct.; first author not captured) | READ (snippet) |
| CA1 pyramidal soma inhibitory synapses | 77-103 per cell; LM dendrites 14-17% inhibitory | Megias, Emri, Freund, Gulyas, Neuroscience 102:527, 2001, doi 10.1016/S0306-4522(00)00496-6 | READ (abstract) |
| Overall inhibitory fraction of CA1 pyramidal synapses | ~5-6% (total ~30,000, ~1,700 inhibitory) | Megias 2001 | RECALLED, not verified. CA3-specific value: NOT FOUND |
| Bezaire model total synapses | ~5.19e9; PC->PC 6.14e7, PVBC->PC 5.83e7 | eLife 2016 Table 1 | READ |

## 4. Sharp-wave ripple (pointer for Randal's third question)

| Feature | Value | Source | Status |
|---|---|---|---|
| Ripple generator | reciprocally connected PV basket cells, necessary and sufficient for ripple-frequency current/rhythm | Schlingloff et al., J Neurosci 2014 | READ (snippet) |
| Ripples generated in CA3, transmitted to CA1; most interneurons fire in SWR, few PCs; PVBC among most active, ivy cells silent | Hajos-group in vitro study (Hajos et al. 2013 J Neurosci, recalled attribution) | READ (snippet) |
| CA2/3 basket cells increase firing during CA1 sharp waves, phase-locked to gamma | Tukker 2013 | READ |
| Ecker model synapse kinetics: PVBC->PC peak 0.65 nS, rise 0.3 ms, decay 3.3 ms, delay 1.1 ms; PVBC->PVBC 5 nS, rise 0.25, decay 1.2, delay 0.6; PC->PVBC 0.85 nS, rise 1, decay 4.1; PC->PC rise 1.3, decay 9.5; Erev(GABA-A) -70 mV; single-compartment cells | Ecker 2022 Table 3 | READ (table garbled, some column assignment inferred) |
| Bezaire CA1 GABA-A onto PC (Gmax nS; rise/decay ms): PV+B 2.0e-4; 0.30/6.2. Axo 1.15e-3; 0.28/8.4. Bis 5.1e-4; 0.11/9.7. CCK 5.2e-4; 0.20/4.2. OLM 3.0e-4; 0.13/11. Ivy 4.1e-5; 1.1/11. NGF 6.5e-5; 9/39. Erev -60 mV | eLife 2016 Table 8 | READ (unit of Gmax as stated by extractor; check) |
| Ripple band 80-180 Hz; CA3 gamma 25-75 Hz | PMC4697528 (macaque reduced model) | READ |
| Needed features | fast (sub-ms rise, 1-4 ms decay) perisomatic GABA-A from PV BCs, recurrent BC-BC connectivity ~25%, BC->PC ~25%, mixed excitatory drive from PCs | synthesis of above | DERIVED |

## What this implies for our grown networks

Our 33% interneuron fraction (48/144) is 3-4x the anatomical estimate (7-11% of CA1 neurons; CA3 modestly higher, about 13% relative to principal cells by one GAD65 count) and far above Ecker's 1.8% PV basket cells. If the goal is natural, a 96-PC network would hold roughly 8-15 interneurons, mostly PV baskets; 48 is defensible only as a deliberate over-representation to get statistics, and should be labeled so. Our 0.5-1% inhibitory synapse fraction is below the ~5-6% recalled for CA1 pyramidal cells and the somatic count of ~60-140 inhibitory terminals per cell, so inhibition is under-grown by roughly 5-10x. Our growth cone counts (22.5 dendritic, 63-74 axonal per interneuron) cannot be checked: absolute CA3 interneuron axon length and bouton data were NOT FOUND. Single PV basket cells reach >1500 pyramidal cells, so with only 96 targets a natural basket axon would cover essentially the whole slab. Ecker's 25% BC->PC and BC->BC probabilities are a useful target for connection-level checks. Next step: pull Ascoli 2009, Hippocampome and NeuroMorpho for CA3 interneuron lengths.
