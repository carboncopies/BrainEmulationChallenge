# Verification of the realism-tester literature profiles (2026-11-24)

Offline literature work only: no sims, no NES calls, no emails, no git, no Drive. Originals `ca3.json`, `drosophila_mushroom_body.json`, `v1.json` are unchanged. New files (same schema plus extra keys `status`, `evidence_level`, `species`, `prep`, `quote`, `notes`, `old_index`, `doi/pmid` inside `reference`): `ca3_verified.json` (46 entries), `drosophila_mushroom_body_verified.json`, `v1_verified.json`. All three load with `rt.compare.load_profile` and run through `compare()`; `tests/test_core.py` passes (13 tests).

## Meaning of the flags
- `verified: true` = the number was read in the primary paper (text, table or abstract) and the stated tissue matches. It does NOT mean "anatomical": Ecker 2022 rows are verified as MODEL PARAMETERS (`status` says so), the Bezaire rows are CA1 model values used as fallback.
- `verified: false` = only seen through a secondary paper or search summary, not checked, or no source exists.
- Evidence levels: PRIMARY_TEXT (table/passage read), PRIMARY_ABSTRACT (abstract only; per-table detail not read), SECONDARY (quoted in another paper), DERIVED (my arithmetic on verified numbers), UNVERIFIED.
- How papers were read: PMC/eLife/J Neurosci pages blocked WebFetch (reCAPTCHA/JS), so texts came from NCBI E-utilities efetch (PubMed abstracts, PMC XML), Europe PMC XML, NCBI BioC, and two directly downloaded PDFs. Paywalled full texts (Ishizuka 1995, Wittner 2007, Sik 1993/1995, Gulyas 1999, Henze 1996, Jinno & Kosaka 2010) were NOT read beyond the abstract. Working extracts are in the session scratchpad (`.../scratchpad/ver/groupA|B|D|E.md`, with quotes and URLs); they are not part of the deliverable.

## CA3 (33 original entries): result
21 of the 33 original entries are now `verified: true` (after correction), 12 stay `false`. 13 new entries were added (11 verified).

### Wrong numbers or citations that were corrected
| old entry | problem | fix |
|---|---|---|
| conn_prob pyr-pyr "<1%, Guzman 2016, rat and human" | The paper is rat only; exact value 0.92% (146/15,930 pairs; 400 um slices, ~22 and ~34 C). Human CA3 is a separate paper (Watson et al. 2025 Cell 188:501, "sparse", no number read). | value 0.0092, rat only |
| conn_prob pyr-pyr "mouse slice ~9%" | Not in Ecker 2022. Source is Sammons et al. 2025 eLife 13:RP98653: 65/734 = 8.9% (mouse, 400 um slices, 32-34 C). | separate entry added |
| conn_prob 0.1 / 0.1 / 0.25 / 0.25 (Ecker 2022) | Values right but they are model parameters. 0.25 is "estimated ... (Schlingloff et al., 2014)" which I could not open; 10% PC-PC is "based on the classical viewpoint" of a highly interconnected CA3. | kept, flagged as model parameter |
| syn_per_pair 1-10 "Bezaire 2016 Tables 1/5" | Table 5 is theta phase. Table 1 only says "generally comprise 1-10 synapses". Authors are Bezaire, Raikov, Burk, Vyas, Soltesz. Real per-pair values (CA1 model, Appendix 1): pyr-pyr 1, pyr-PVBC 3, PVBC-pyr 11, PVBC-PVBC 1. CA3 data: PC-PC 1-2 contacts (Guzman, 12 pairs), PC-PV mostly single (Sik 1993 84.7%, Gulyas 1993 >80%). | CA3-specific ranges [1,2], [1,3]; CA1 model values 11 and 1 |
| length.dendrite.pyramidal 12,481 +/- 2,999 "PMC6792859 table T1" | PMC6792859 is Jiang et al. 1998 J Neurosci (epilepsy), not a review. A search summary places that value in Tecuatl et al. 2021 J Neurosci 41:1665 (PMC8115893) Table 1, citing Ishizuka. I could not open that table. | citation corrected, value stays UNVERIFIED |
| proportion.interneuron 7-15% | 15% has no verified source (Freund & Buzsaki 1996 was only recalled). 11% (Bezaire & Soltesz 2013) is an assumption inside their quoted 7-11%; 8.0% (Bezaire 2016) is my arithmetic on a modelled subset. GAD65 "13%" (Czeh et al. 2013, rat) is interneuron:principal ratio = 11.5% of all neurons. | verified range 0.07-0.125 (Aika 1994 7.0% rat CA1; Woodson 1989 ~11% rat hippocampus; Czeh 2013 11.5% rat CA3; Keller 2018 12.5% mouse hippocampus) |
| length.axon.pyramidal "150-500 mm, 200 mm CA3b" | 150-300 mm = Li et al. 1994 (in vivo, projected, authors Li/Somogyi/Ylinen/Buzsaki). >0.5 m = Wittner 2007, ONE CA3c cell. "200 mm (CA3b)" found nowhere. | split in two entries, "200 mm" dropped |
| syn_dendrite.pyramidal.from.interneuron >=140 | Numbers right (60 CA1, 140 CA3) but the source (Takacs et al. 2015 Brain Struct Funct 220:919) is MOUSE and counts somatic basket terminals only. | flagged |
| length.axon.interneuron NeuroMorpho 21,148-59,018 | #10716 is Tukker's cell B13a, which Tukker places in CA2 (axon partial, mostly CA1); #49377 comes from a CA1-focused paper; #10658 is only "fast-spiking" in a transgenic mouse; no length field in the NeuroMorpho API so sums could not be cross-checked. | kept, UNVERIFIED with the problems listed |
| reach_max.axon.interneuron "half of 780-1,740 um" | The review wording "from the cell body" is ambiguous; extents in Tukker/Bezaire look like full widths, so half-extents are about 460-660 um. | kept as derived/unverified; Ascoli and Tukker-derived entries added |
| cells_per_volume "not found" | Found for mouse: 165.2e3 (dorsal) and 172.4e3 (ventral) /mm^3 CA3 pyramidal (Jinno & Kosaka 2010, abstract). No verified RAT CA3 density. | filled (mouse) |

### Confirmed
Ishizuka 1995 9,300-15,800 um (abstract; rat CA3, in vitro slice, n=20); Ascoli 2009 axon 21,535 +/- 12,042 um (Table 5, juvenile rat slice, not PV-identified; Table 5 not "4-6"); Tukker 2013 dendrite 9,032 +/- 992 um (EMS63728 confirmed; n=4 includes one CA2 cell); Sik 1993 15,295 and Wittner 2007 ~40,000 boutons (abstracts, each ONE cell); Sik 1995 >1,500 pyramidal targets (CA1); Gulyas 1999 16,294 synapses (CA1 PV); Tukker ~34,810 input synapses (n=3).

### Not verified (and why)
- Hajos-lab mouse dendrite 5,021 +/- 1,306 um: cell list not available.
- Gulyas 4,347 +/- 1,125 um and Sik 1995 46,180 um: seen only as quoted in a review (Booker & Vida 2018; Bezaire & Soltesz 2013). The Gulyas abstract gives 4,300 um (added).
- reach_max (dendrite and axon) for CA3 pyramidal cells: no soma-to-tip number found (Henze 1996: transverse/septotemporal extents 311/269 um; Ishizuka full text unreadable).
- Recurrent CA3-CA3 inputs per cell: ~12,000 (Treves & Rolls 1992, citing Amaral, Ishizuka, Claiborne 1990 which I did not open). SECONDARY. The "4,000" lower end in earlier notes was not found.
- 15% interneuron upper bound, Jinno & Kosaka 2006 CA3 fraction, Boss 1987 numbers, Schlingloff 2014 (source of 0.25), Sammons 2024 PNAS 8.8% (only quoted second-hand), PVBC-to-pyramid synapses per connection in CA3 (Kohus 2016 full text unavailable).
- ball_index entries: no literature exists; the 0.5-2 tolerance is a design choice.

### Unresolved conflict worth knowing
CA3-CA3 connection probability: 0.92% (Guzman, rat slice) vs 8.9% (Sammons 2025, mouse slice) vs 10% (Ecker model assumption). Both slice studies use 400 um slices, which cut axons; the difference is species/age/method and I cannot resolve it from the papers read. Single-cell axon-length discrepancy in PV basket dendrites (Tukker 7,566 vs Gulyas 4,347 um in CA1, ~1.7x) is also real.

## Drosophila mushroom body (stub -> 11 filled rows, 9 verified)
All from full texts (Europe PMC XML): Kenyon cells 1,927 in the right hemibrain MB (Li et al. 2020 eLife 9:e62576) and ~2,000 per MB (Aso et al. 2014 eLife 3:e04577); 34 MBONs of 21 types (Aso 2014); ~130 DANs of 20 types (Aso 2014) and 158 DANs (Li 2020); 126 PNs innervating the main calyx at a 25-synapse threshold (Li 2020); KC claws 7 (range 2-11, n=200, male, light microscopy; Caron et al. 2013 Nature 497:113) and 5.2 +/- 1.6 (n=1,356, female FAFB EM; Zheng et al. 2022 Curr Biol 32:3334, author list not verified); APL gives 9.5% of KC calyx input synapses (Li 2020). Marked unverified: one APL neuron per hemisphere (Lin et al. 2014; quote came only from a WebFetch summary), proportion.kenyon_cell 0.91 (derived; denominator excludes APL/DPM/OAN; 1927/2600 = 0.74 under another denominator).
Not found, left TODO: KC cable length, synapses per KC, any reach, KC soma density/calyx volume, APL arbor, KC per PN bouton (would need a hemibrain neuPrint query, which I did not run). A "Wu 2013 Stereotypy and APL" paper mentioned in my brief could not be found and was not used.

## V1 (stub -> mouse V1, 18 filled rows, 15 verified)
Species chosen: mouse. V1 neuron density 155,426/mm^3 (Herculano-Houzel et al. 2013, isotropic fractionator) and neocortex mean 9.2e4/mm^3 (Schuz & Palm 1989, abstract); PV/SST/VIP densities 20,237/12,499/7,539 per mm^3 (Gonchar et al. 2008, immunolabel) with a 3-4x lower Cre-reporter spread (Kim 2017 via Keller 2018, SECONDARY, not entered as value); shares of GABAergic cells 36/30/17% (Pfeffer et al. 2013; Gonchar gives 39/23/11%); pyramidal 85% = model assumption (Billeh et al. 2020), 80-85% derived and unverified; pyramidal L2a/L2b synaptic inputs 4,758/2,649, dendrite 4,532/3,510 um (Schneider-Mizell et al. 2025, complete EM dendrites; the 1.475 mm EM median of Turner 2022 is truncated and NOT used); neocortex 8,200 synapses/neuron (Schuz & Palm); SST output synapses 1,499-9,621 per cell (Gamlin et al. 2025, first author not verified); L2/3 pyramid to Pvalb pmax 0.79, to Vip 0.38 (Campagnola et al. 2022; peak probabilities, `comparable=false`). PeriTC 581 and InhTC 16 synapses are marked unverified for the PV/VIP labels (the authors say the class mapping is "not a one-to-one match").
Not found: interneuron total axon/dendrite length, any reach, mouse V1 spines per cell. GABA density in Gonchar (51,785/mm^3) is about 1/3 of Herculano-Houzel's neuron density, a cross-study inconsistency: do not combine them to compute fractions.

## Caveats on this work
- Several of the checks were done by sub-agents; I read their extracts (quotes, URLs, evidence levels) and cross-checked them against each other, but I did not re-open the papers myself. The strongest claims (Ecker table values, Guzman 0.92%, Tukker/Ascoli tables, Takacs mouse) rest on a text the agent reported reading locally.
- Abstract-only entries confirm the headline number, not the per-condition detail.
- Billeh 2020 was read only to about the first third of the preprint; Lin 2014's APL quote came via WebFetch only.
