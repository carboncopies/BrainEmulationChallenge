# CA3 interneuron arbor references (web research)

Method note: WebFetch returns a summary produced by a small model over page text, not raw text. "Full text (via fetch)" below means the number came from fetched article text, which I did not read myself. "Snippet" means a search-result snippet only. Nothing is filled in from memory. Items marked "derived" are computed by the cited paper from its own assumptions.

## 1. Axon length and boutons per cell

| Value | Species / region / cell | Source | Read as |
|---|---|---|---|
| Axon ~21,535 +/- 12,042 um (R type, n=7), ~25,081 +/- 10,938 um (L-M type, n=6); axonal bifurcations 192 +/- 72 (R), 289 +/- 83 (L-M). Ascoli 2009 pooled summary: "~20 mm" axon | Rat, CA3b, intracellularly filled interneurons in slices (axon likely incomplete); NOT PV-identified | Quantitative morphometry of CA3b interneurons, https://pmc.ncbi.nlm.nih.gov/articles/PMC2827149/ ; ~20 mm figure from https://pmc.ncbi.nlm.nih.gov/articles/PMC3577356/ | Full text (via fetch), Tables 4-6. First 100k of 180k chars only. |
| Axon area 0.666 +/- 0.223 mm2 (n=3); no axon length, no bouton count | Rat (Sprague Dawley), CA2/3 PV basket cell, in vivo labelled | Distinct Dendritic Arborization... PV Basket Cells in CA3, https://pmc.ncbi.nlm.nih.gov/articles/mid/EMS63728 | Full text (via fetch), first ~200k chars read |
| Axon length 46,180 um (Sik et al. 1995); bouton density 22.6 per 100 um; 10,440 boutons per cell (derived: 46,180 x 0.226) | Rat, **CA1 (FALLBACK, not CA3)**, PV+ basket cell | Bezaire & Soltesz 2013, https://pmc.ncbi.nlm.nih.gov/articles/PMC3775914/ | Full text (via fetch) |
| CA3 PV basket cell axon length / bouton count | not found | | |
| NeuroMorpho.Org CA3 basket morphometrics | not found (search did not surface any neuron page; not queried directly) | | |
| Hippocampome.org CA3 Basket page | not found. The one page I fetched (id=1005) was DG MOLAX and has no numeric morphometrics; Hippocampome gives only qualitative layer lists | https://hippocampome.org/php/neuron_page.php?id=1005 | Full text (via fetch) |

## 2. Primary dendrites and total dendritic length

| Value | Species / region / cell | Source | Read as |
|---|---|---|---|
| 1-6 primary dendrites, mean 3.08 +/- 1.26 (all 13 cells pooled) | Rat, CA3b interneurons (R and L-M types), not PV-identified | PMC2827149 | Full text (via fetch) |
| Dendritic length 2,910 +/- 1,387 um (R), 3,217 +/- 2,900 um (L-M); HiDe 3,942 +/- 2,273 um, LoDe 1,627 +/- 559 um; dendritic bifurcations 9-83 | Same | PMC2827149 | Full text (via fetch) |
| Dendritic length ~3 mm (summary) | Same set, quoted in Ascoli 2009 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3577356/ | Full text (via fetch) |
| Total dendritic length 10,037 / 9,213 / 9,218 / 7,662 um, mean 9,032 +/- 992 um (n=4) | Rat, CA2/3 **PV basket cells**, in vivo labelled, much larger than the CA3b slice cells above | https://pmc.ncbi.nlm.nih.gov/articles/mid/EMS63728 (Table 2) | Full text (via fetch) |
| Primary dendrite count for PV basket cells | not found in the text I read (fetch covered about 200k of 188k chars, no count reported by summary) | | |

Note: the slice-based dendritic length (~3 mm) is about 3x lower than the in vivo PV basket value (~9 mm). Use the 9 mm value for PV basket cells.

## 3. Pyramidal cells contacted, synapses per connection

| Value | Species / region / cell | Source | Read as |
|---|---|---|---|
| 943 pyramidal cells + 71 interneurons = 1,014 cells contacted per PV basket cell (derived by the model authors) | **CA1 (FALLBACK)** | Bezaire & Soltesz 2013, PMC3775914 | Full text (via fetch) |
| ~11 synapses per PV basket -> pyramidal connection; 1 synapse per connection onto interneurons (assumption) | Mouse data (Foldy et al. 2010) used for CA1 model | PMC3775914 | Full text (via fetch) |
| 7,600 pyramidal cells converge on each CA2/3 basket cell (convergence, the reverse direction) | Rat CA2/3 PV basket cell | EMS63728 | Full text (via fetch) |
| Divergence (pyramidal cells contacted) from CA3 PV basket cell | not found | | |
| Gulyas 1999 | not found (not fetched/located) | | |
| Context only: CA3 pyramidal cell axon with ~15,300 boutons, 2.1% on PV+ neurons (Sik, Tamamaki, Freund 1993); >0.5 m axon, ~40,000 boutons (Wittner 2007). Pyramidal, not interneuron | Rat CA3 | search snippets | Snippet only |

## 4. Density and interneuron:pyramidal ratio

| Value | Source | Read as |
|---|---|---|
| CA3: 230,000 neurons (range 210,000-250,000, West et al. 1991, 30-day-old Wistar rat); with an assumed 11% interneurons: 204,700 pyramidal + 25,300 interneurons (ratio ~8.1:1 pyramidal:interneuron; this is an assumption transferred from whole hippocampus, not a CA3 measurement) | Bezaire & Soltesz 2013, PMC3775914 | Full text (via fetch) |
| CA1: 311,500 pyramidal + 38,500 interneurons (ratio ~8.1:1); GABAergic interneurons 7-11% of hippocampal neurons (Woodson 1989, Aika 1994) | PMC3775914 | Full text (via fetch) |
| CA3 cell density per mm3 | **not found**. Candidate sources not opened: bioRxiv 2025 "Updated neuronal numbers of the rat hippocampal formation" https://www.biorxiv.org/content/10.1101/2025.04.16.649153.full.pdf (snippet says only 4 studies report CA3 alone); van Dijk 2016 https://pmc.ncbi.nlm.nih.gov/articles/PMC4783399 | |

Densities per mm3 need layer volumes; none obtained.

## 5. Inhibitory vs excitatory synapse fraction (Megias et al. 2001)

Megias, Emri, Freund, Gulyas 2001, Neuroscience 102:527-540, doi 10.1016/S0306-4522(00)00496-6, PMID 11226691. I could NOT open the paper or its abstract (PubMed blocked by cookie wall). The values below are second-hand.

| Value | Species / region | Source | Read as |
|---|---|---|---|
| ~28,860 excitatory synapses per CA1 pyramidal cell (stratum radiatum + oriens), citing Megias 2001 | Rat CA1 pyramidal cell | Bezaire & Soltesz, PMC3775914 | Full text (via fetch), second-hand |
| ~1,830 GABAergic synapses per CA1 pyramidal cell (dendrites, somata, proximal axon), citing Megias 2001 | same | PMC3775914 | Full text (via fetch), second-hand |
| Table 19 of Bezaire lists 1,713 GABA+ of 32,351 total synapses on CA1 pyramidal dendrites (~5.3%, derived by the fetch summary, not stated in text). Caution: 28,860 + 1,713 = 30,573, not 32,351, so the table's total may include other categories. Recheck against the table | same | PMC3775914 | Full text (via fetch); unverified arithmetic |
| Inhibitory share ~3% on distal spiny radiatum/oriens dendrites; 70-100% on proximal dendrites | Rat CA1 | Megias 2001 abstract excerpt via search result, https://portalcientifico.uvigo.gal/documentos/5faf829229995246a6dd43fb | Snippet only |
| 94% type 1 (excitatory) / 6% type 2 (inhibitory) in a stratum radiatum EM volume | Adult rat CA1 s. radiatum (Harris lab-linked, one volume) | search snippet via https://synapseweb.clm.utexas.edu/ | Snippet only |
| Whole-cell inhibitory fraction for CA3 | not found | | |

Verdict on Megias: the ~6% overall inhibitory (1,830 of ~30,700) and ~3% distal figures are consistent with each other, but I did not verify them in the original paper.

## Other
- Bezaire & Soltesz: Schaffer collateral synapses 93% onto pyramidal cells, 7% onto interneurons (Takacs 2012); CA3c pyramidal cell ~39,200 boutons in ipsilateral dorsal hippocampus (full text via fetch). Bezaire text covered chars 0-200k of 256k.
- Not completed: Gulyas 1999, direct NeuroMorpho.Org queries, Hippocampome CA3 Basket page.
