# NetMorph synapse test: literature and biology review (2026-11-15)

## Summary (10 lines)
1. No paper found that noticed low or direction-dependent NetMorph synapse counts, or reimplemented the synapse test (NOT FOUND; search was limited, not exhaustive).
2. GitHub randalkoene/netmorph: 1 open issue (#1, cygwin install, 2021), no closed issues, no visible PRs, no forks listed in the page's default filter (VERIFIED on page; the forks page filter was 2y/Active, so older forks could be hidden). No erratum found.
3. Raw source fetch shows `double frac_T_PQ = tx/qx;` still on master (fetched through a summarizing tool, so exact text is VERIFIED-via-summary only; line number not confirmed).
4. van Ooyen et al. 2014 (PLoS ONE, L2/3 pyramidal only): 2.53 +/- 2.14 synapses per connection at 4 um criterion, rising to 3.28/4.43/5.57 at 6/8/10 um; connection probability 0.301 (VERIFIED). Their parameter is a 4 um default, much larger than your D 0.15-1.5, so their counts are not directly comparable.
5. Possible QUALIFIER: the 2014 paper's pyramidal-pyramidal values are in line with experiment (Feldmeyer 4.5, Hellwig 1.85), i.e. the bug, if it affects that code path in the same way, did not produce obviously deficient counts there. Not tested by us; do not claim the published results were wrong.
6. A Master's thesis (NetMorph vs CX3D) reportedly found NetMorph gave "excessive" synapses per neuron (SEEN IN SNIPPET ONLY; PDF returned 403). This points the opposite way from the bug and should be checked.
7. Biology, PV basket to pyramidal: CA1 mouse 8.7 +/- 0.9 (deep) and 4.0 +/- 0.6 (superficial) boutons per pair (Lee 2014, VERIFIED). Cat V1: a basket cell to pyramidal pair via 15 release sites (Tamas 1997, SNIPPET ONLY). Your "4-12, target ~11" is plausible but 11 is at the high end.
8. Pyramidal to FS interneuron, human/rat L2/3: 3.3 +/- 1.5 / 2.9 +/- 1.5 contacts (Molnar 2016, SEEN IN SNIPPET/abstract). Pyr to pyr (L4 to L2/3 rat): 4.5 +/- 0.5 (Feldmeyer 2002, via van Ooyen 2014 text, VERIFIED as quoted there).
9. Interneuron share of cortical neurons: about 15-30% (Tepper 2018 via BioNumbers, VERIFIED page text; striatum paper, so a secondary source for cortex); ~20% mouse, ~25% monkey (SNIPPET ONLY). Inhibitory synapse fraction 10-20%: NOT CONFIRMED; only 11% GABA-immunoreactive targets in cat V1 (Beaulieu & Somogyi 1990, snippet).
10. Not found: Maki-Marttunen / Hjorth / Acimovic using NetMorph (no hits); interneuron-to-interneuron and human PV to pyramidal counts; synapse-per-pair data for D_synmax sensitivity beyond van Ooyen 2014.

## 1. Papers using NetMorph synapse formation

- Koene RA, Tijms B, van Hees P, Postma F, de Ridder A, Ramakers GJA, van Pelt J, van Ooyen A (2009) NETMORPH: a framework for the stochastic generation of large scale neuronal networks with realistic neuron morphologies. Neuroinformatics 7(3):195-210. https://pubmed.ncbi.nlm.nih.gov/19672726/ . SEEN IN SNIPPET ONLY (abstract-level; not read for synapse numbers).
- van Ooyen A, Carnell A, de Ridder S, Tarigan B, Mansvelder HD, Bijma F, de Gunst M, van Pelt J (2014) Independently outgrowing neurons and geometry-based synapse formation produce networks with realistic synaptic connectivity. PLoS ONE 9(1):e85858. https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0085858 . VERIFIED (read first 100k of ~119k characters, via fetch tool summary). Reports:
  - 250 L2/3 pyramidal neurons, one layer; 48,743 synapses used in comparisons; 12,267 basal and 5,302 apical connections; mean connection probability 0.301.
  - Synapses per connection: 2.53 (sd 2.14) at 4 um; 3.28 (3.1) at 6 um; 4.43 (4.6) at 8 um; 5.57 (5.7) at 10 um. Quote: "The larger the distance criterion, the more synapses will be created, and the larger the number of synapses per connection."
  - Comparison data: Feldmeyer et al. 4.5 (sd 0.5, n=13); Hellwig semi-experimental 1.85 (model gave 1.8 at an assumed 2 um criterion).
  - Test described as: axonal and dendritic line pieces must "cross" and orthogonal distance be below threshold. Does not mention any direction dependence or anomaly.
  - Interneurons were not modelled (pyramidal only), so no interneuron synapse counts.
- van Pelt J, van Ooyen A (2013) Estimating neuronal connectivity from axonal and dendritic density fields. Front Comput Neurosci 7:160. https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2013.00160/full . VERIFIED (first 100k of 119k chars). Uses NetMorph (50 L2/3 neurons); criteria delta = 1-4 um; connection probability about 0.7 at very short distances falling to about 0.04 at 500 um (delta = 1 um example); Holmgren data 0.09 down to 0.01. Contacts per connection only in figures (not read). Notes about 4 um "seems plausible" but "still has to be validated".
- Carnell A, de Ridder S, van Pelt J, van Ooyen A (2011) BMC Neurosci 12(Suppl 1):P356. https://pmc.ncbi.nlm.nih.gov/articles/PMC3240474/ . VERIFIED (abstract). NetMorph networks, "crossing criterion", small-world; no synapse counts.
- ModelDB entry (code): https://modeldb.science/182135 . SEEN IN SNIPPET ONLY.
- Master's thesis comparing NetMorph with CX3D, reported to find realistic results but "excessive numbers of synapses per neuron": https://core.ac.uk/download/250120217.pdf . SEEN IN SNIPPET ONLY (fetch returned HTTP 403; author/title not obtained). Worth retrieving manually; if true it conflicts with the "too few synapses" finding, though it may reflect a different D or a different setup.
- Mäki-Marttunen, Hjorth, Acimovic, Kleinfeld using NetMorph: NOT FOUND in the searches run.
- Papers that noticed direction-dependent or anomalously low counts, or reimplemented the test: NOT FOUND.

## 2. GitHub and mirrors

- https://github.com/randalkoene/netmorph/issues : one open issue #1 "Installation with cygwin" (opened 2021-05-04, 2 comments); no closed issues; no PR count visible. Nothing about synapse formation. VERIFIED (page via fetch tool).
- https://github.com/randalkoene/netmorph/forks : "No forked repositories found" under default filters (2 years, Active). Inactive/older forks not checked. Qualified.
- raw master synapse_formation_model.cc contains `double frac_T_PQ = tx/qx;` (excerpt returned by fetch tool summary; treat as confirming the bug persists upstream, but line number 379 NOT verified).
- Other mirrors, erratum: NOT FOUND (not exhaustively searched; no search for gitlab/ModelDB code diffs).

## 3. Biology reference values

PV basket to pyramidal
- Lee S-H et al. (2014) Neuron 82(5):1129-1144, mouse hippocampal CA1. https://pmc.ncbi.nlm.nih.gov/articles/PMC4076442 . VERIFIED (via fetch summary): putative boutons of single PVBC on single pyramidal cell: deep PC 8.7 +/- 0.9 (n=10), superficial PC 4.0 +/- 0.6 (n=10); amygdala-projecting 6.0 +/- 0.4, mPFC-projecting 3.0 +/- 0.4. These are hippocampus, not neocortex, and boutons not confirmed synapses.
- Tamas G, Buhl EH, Somogyi P (1997) J Physiol 500(3):715-738, cat visual cortex. https://pmc.ncbi.nlm.nih.gov/articles/PMC1159419/ (url appeared in results; not read). SEEN IN SNIPPET ONLY: a basket cell innervated a pyramidal cell via 15 release sites in one pair; interneuron total 5240 +/- 1600 synaptic junctions; ~0.66% of GABAergic synapses in axonal field.
- Micheva et al. mouse neocortex: synapses from a PV1 interneuron onto a partner reduced roughly threefold in postnatal week 4. SEEN IN SNIPPET ONLY (paper not identified; do not cite without checking). Implication: age matters for the target number.
- Neocortical (barrel) FS interneuron: 3.7 +/- 1.3 putative inhibitory contacts; L4-to-L2/3 interneuron 2.3 +/- 0.8 (SNIPPET ONLY, sources unidentified; do not cite).

Pyramidal to pyramidal
- Feldmeyer, Lubke, Silver, Sakmann (2002) J Physiol, rat barrel cortex L4 to L2/3: 4.5 +/- 0.5 putative contacts, n=13. Value quoted in van Ooyen 2014 (VERIFIED there) and in a search snippet; primary paper not opened.
- L4 spiny to L4 spiny (Feldmeyer 1999): 3.4 +/- 0.2 (range 2-5). SNIPPET ONLY via a review.

Pyramidal to interneuron
- Molnar G et al. (2016) eLife 5:e18167, human and rat L2/3 PC to FS interneuron. https://elifesciences.org/articles/18167 . SEEN IN SNIPPET/abstract: 3.3 +/- 1.5 (range 1-6) human, 2.9 +/- 1.5 rat light-microscopy contacts; about 3 contacts on average. Buhl et al. 1997 (cat): unitary EPSPs in basket cells via 1-2 junctions (snippet only).

Interneuron to interneuron: NOT FOUND.

Connection probability: only the model values above (0.301, van Ooyen 2014) and Holmgren 0.09 to 0.01 as quoted by van Pelt 2013 (VERIFIED as quoted). Biological PV to pyramidal probabilities: NOT FOUND in this pass.

Interneuron fraction
- "about 15%-30% of the neuronal populations in structures such as the cortex and hippocampus", Tepper et al. 2018 Front Neuroanat 12:91 (doi 10.3389/fnana.2018.00091), via https://bionumbers.hms.harvard.edu/bionumber.aspx?id=117208 . VERIFIED text; secondary source (striatal review).
- About 20% (mouse), about 25% in 8 of 10 monkey areas, under 20% in V1: SEEN IN SNIPPET ONLY, sources not opened (a mouse developmental paper, "Fraction of Cortical GABAergic Neurons is Constant..."; a monkey GABA-immunoreactivity study).
- PV about 40%, SST about 30%, 5HT3aR about 30% of GABAergic neurons in mouse S1: SNIPPET ONLY (likely Rudy/Kepecs-type papers; unidentified).

Inhibitory synapse fraction
- 10-20%: NOT CONFIRMED. Beaulieu & Somogyi (1990) Eur J Neurosci, cat V1: 11% of postsynaptic targets GABA-immunoreactive; GABA synapse density about 48 million/mm^3 (SNIPPET ONLY). Motta et al. 2019 Science (mouse L4 connectomics; https://www.biorxiv.org/content/10.1101/460618) does not give the fraction in the results retrieved; check the paper directly.

## 4. Findings that contradict or qualify the working claims

- The published parameter regime (4-10 um criteria) differs from yours (0.15-1.5): the published counts do not validate your D values. Their trend (more synapses per connection with larger criterion) matches your bug-fixed behaviour.
- Published L2/3 pyr-pyr counts (2.5 at 4 um, matching experiment 1.85-4.5) mean the upstream code is not known to have visibly under-produced; either the buggy branch was not hit the same way or the effect was masked. Untested by us; do not assert the published results are invalid.
- A thesis snippet suggests NetMorph over-produced synapses; this runs against the bug explanation and needs reading.
- Your target of ~11 for PV basket to pyramidal is at the upper end; verified experimental values are 4.0-8.7 (mouse CA1) and about 3-4 for other interneuron contacts. A range of 4-9 is better supported by what was verified. Cat basket cell 15 release sites is a single pair (snippet).
- Pyramidal to interneuron is about 3 contacts (human/rat L2/3), lower than a PV to pyramidal value, so model outputs for the two directions should not be equal.
- Inhibitory synapse fraction of 10-20% is unconfirmed (only 11% in cat V1 snippet).
- Method caveat: web pages were read through a summarizing fetch tool, not as raw text; "VERIFIED" means the summarizer returned the stated numbers from the fetched page, not that I read the full PDF. Several fetches covered only the first 100k characters.
