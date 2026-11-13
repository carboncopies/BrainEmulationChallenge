# CA3 interneuron arbor bounds (literature pass, 2026-11-12)

Follow-up to CA3_NATURAL_RANGES.md. Legend: READ = seen in fetched page or search snippet this session (secondary extractions flagged); RECALLED = memory, unverified; DERIVED = my arithmetic; not found = absent. Hippocampome neuron pages, NeuroMorpho API, and Ascoli 2009 full text gave no usable CA3 interneuron axon/dendrite numbers directly.

## Addendum: interneuron arbor bounds

### (a) Axon total length, branch points, tips
| Quantity | Value | Source | Status |
|---|---|---|---|
| CA3 interneuron axon total length (PV BC, CCK BC, AAC, bistratified, OLM) | not found | | not found |
| CA3 interneuron axon bifurcations / terminal tips | not found | | not found |
| Ascoli 2009 qualitative: axons branch about an order of magnitude more than dendrites (CA3b interneurons) | ~10x dendrite branching | Ascoli et al. 2009 (J Comp Neurol 515, via search snippet) | READ (snippet, secondary) |
| Cat V1 large basket cell axon (neocortex, NOT hippocampus) | 632 +/- 348 axon nodes per arbor; ~44,064 boutons over 9 cells (about 4,900 per cell, DERIVED); max Strahler order mostly 7; spiny cell axons 130 +/- 73 nodes | PMC2837396 (Binzegger/Kisvarday-type reconstruction study; exact authors not captured) | READ (page text) |
| CA3 pyramidal axon, for comparison | 15,295 boutons (Sik 1993); >0.5 m and ~40,000 boutons (CA3c, Wittner 2007); 150-300 mm typical; 200 mm (CA3b) to 500 mm (CA3c) | search snippets | READ |
| Hippocampome CA3 basket / basket CCK+ pages | morphometrics absent on type pages (checked DG granule page: layer-wise qualitative axon/dendrite data only) | hippocampome.org | READ (one page checked; CA3 basket page not directly fetched) |
| NeuroMorpho: CA3 pyramidal-layer PV+ basket cells exist (e.g. IDs 10407-10410); API records return surface/volume only, no stems/bifurcations/length | surface 11,250-16,896; volume 4,043-7,274 (units unstated) | neuromorpho.org API | READ (axon/dendrite split not available) |

Derived rough tip estimate (speculative): Ascoli dendrite bifurcations 10-39 (below) x ~10 gives axon bifurcations on the order of 100-400; the cat V1 basket axon gives ~630 +/- 350 nodes (tips ~ nodes+1). Together: roughly 100-1000 tips, central ~300-600. This is inference, not a measured CA3 value.

### (b) Primary dendrites and dendritic tips
| Quantity | Value | Source | Status |
|---|---|---|---|
| CA3b interneurons, soma in radiatum: dendritic bifurcations / total dendritic length | 30.29 +/- 25.69 / 2910 +/- 1387 um | Ascoli 2009 via neuroelectro table extraction | READ (secondary) |
| Same, soma in lacunosum-moleculare | 24.50 +/- 19.56 / 3217 +/- 2900 um | same | READ (secondary) |
| High- vs low-branching groups | 38.88 +/- 21.85 bif, ~3900 um vs 9.60 +/- 0.55 bif, ~1600 um | same | READ (secondary) |
| Dendritic tips | ~bifurcations + number of primary dendrites (DERIVED): about 12-45 tips | | DERIVED |
| PV BC (vertical) dendritic length | 4347 +/- 1125 um | Gulyas et al., quoted in a 2018 Cell Tissue Res review | READ (snippet) |
| Neocortical basket cell, for scale | 6 stems, 18,070 um | NeuroMorpho C260897C-I1 | READ (not hippocampus) |
| Number of primary dendrites for CA3 types | not found (typical 3-6 for hippocampal interneurons is RECALLED only) | | not found |
| CA2/3 PV BC dendrite in LM | 33% of length, 24% of synaptic input; total input ~35,000 synapses | Tukker 2013 | READ (prior note) |

Our 22.5 dendritic growth cones per interneuron sits inside the derived 12-45 tip range.

### (c) Inhibitory synapses per pyramidal cell
| Quantity | Value | Source | Status |
|---|---|---|---|
| Somatic inhibitory terminals per PC | ~60 CA1, ~140 CA3; ~60% PV+, 35-40% CB1+ | ultrastructural study (Springer, abstract) | READ |
| CA1 PC soma inhibitory synapses | 77-103; LM dendrites 14-17% inhibitory; 92% of GABAergic synapses on PCs are dendritic | Megias 2001 | READ (abstract/review snippets) |
| Total synapses per CA1 PC and inhibitory fraction | ~30,000 total, ~5-6% inhibitory | Megias 2001 | RECALLED; the search could not confirm 30,000 or 5.5% |
| CA3 inhibitory fraction or count per PC | not found | | not found |
| Guzman 2016 CA3 synapse counts | supplement (Tables S1-S4) exists at caltech.edu mirror; not read | | not found |

### (d) Interneuron -> PC and interneuron -> interneuron synapses per connection
| Quantity | Value | Source | Status |
|---|---|---|---|
| Axo-axonic bouton | one synapse per bouton; PV boutons "small macular synapses" | ultrastructural abstract | READ |
| BC->PC synapses per connection (Tamas/Buhl/Somogyi) | not found (RECALLED: ~2-6 for BC->PC, ~1-3 for AAC; unverified) | | not found |
| One CA1 basket cell targets | >1500 PCs and ~60 PV interneurons | Sik 1995 | READ (abstract) |
| Bezaire CA1 model | 1-10 synapses per connection | eLife 2016 | READ (prior) |
| CA3 model PVBC->PC / PVBC->PVBC probabilities | 0.25 / 0.25 | Ecker 2022 | READ (prior) |
| Network-graph degrees (CA2 basket, potential connectivity) | out 5, in 9 | PMC5114701 | READ (not synapse count) |

### (e) PC -> interneuron synapses
| Quantity | Value | Source | Status |
|---|---|---|---|
| CA3 PC axon boutons contacting PV cells | 2.1% of 15,295 boutons (~320) | Sik 1993 | READ (snippet) |
| Synapses onto CA1 PV interneurons | 16,294 mean (PV), 3,839 (CB), 2,186 (CR) | Gulyas 1999 | READ (prior) |
| PC->interneuron synapses per connection | not found | | not found |
| PC->PVBC probability | 0.10 | Ecker 2022 | READ (prior) |

## Conclusion (120 words)

No measured CA3 interneuron axon tip count was found, so no value is verifiably natural. Indirect bounds: Ascoli's dendrites carry 10-39 bifurcations and axons branch roughly ten times more, while a neocortical basket axon has about 630 +/- 350 nodes. Treat roughly 100-1000 axon tips, centered near 300-600, as plausible. B_inf 26 is therefore plausible if its count falls in that band (the 74 end, at B_inf 13, looks sparse; 1283 at B_inf 39 exceeds the single measured analogue by about two standard deviations and is likely too high). Prefer 26, but confirm by counting tips per cell and comparing with Ascoli 2009 Table values or NeuroMorpho CA3 reconstructions before committing.
