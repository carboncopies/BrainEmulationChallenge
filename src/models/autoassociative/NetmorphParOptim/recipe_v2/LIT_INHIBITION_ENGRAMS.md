# Literature: inhibition in CA3 memory/ripple models, unitary synapses, engram size, pattern-completion cue fraction (2026-11-13)

Web search and fetch only. No simulation, no NES. Legend: READ = number appeared in a page or search snippet fetched this session (source named); RECALLED = from memory, not verified here; DERIVED = my arithmetic on READ numbers; INFERENCE = my reasoning, not a published claim. Many primary full texts could not be parsed (Guzman 2016, Nakazawa 2002, Treves and Rolls PDFs were compressed binaries; Schlingloff full text only partly read), so several requested numbers are "not found". The WebFetch tool summarises pages with a small model, so READ numbers are from that summary of the page, not my own eyes on raw text; spot-check anything critical.

Our network for reference (from FABLE_DESIGN_S1.md, M/C labels there): 96 pyramidal, 48 interneurons, Int->Pyr synapses 1314 on S1 (about 13.7 per pyramid), GABA 0.8 nS at weight 1, fixed weight 0.2 = 0.16 nS per synapse per spike, reversal -70 mV = rest (shunt), decay 10 ms, leak 10 nS, 24 of 96 pyramids with no inhibitory synapse, cue 4 cells delivers 18 nS to each non-cue cell, firing threshold for that volley about 14 nS.

## A. Role of inhibition in CA3 attractor models and sharp-wave ripples

| Finding | Value | Source | Status |
|---|---|---|---|
| Ecker CA3 SWR model: ripples need recurrent PVBC inhibition | "necessary and sufficient" for ripples; removing PVBC-PVBC synapses keeps network stable and replay still works (with PC-PC weights x1.3) but no ripples | Ecker et al. 2022 | READ |
| Same model: what terminates SWR | SWR (up to ~800 ms) ends when replayed sequence reaches end of track, not by inhibition; authors suggest a second interneuron class could give delayed feedback inhibition (not implemented) | Ecker 2022 | READ |
| Same model: cell counts and rates | 8000 PC, 150 PVBC; mean PVBC rate during SWR about 65 Hz; ripple optimisation target 180 Hz; analysis band 150-220 Hz | Ecker 2022 | READ |
| Same model: inhibition vs excitation | "approximately balanced" during SWR, no number | Ecker 2022 | READ |
| Implied PVBC inputs per PC in Ecker | about 37.5 (0.25 x 150) | DERIVED | DERIVED |
| Evangelista model: SWR termination | short-term depression at PV-BC -> "anti-SWR" interneuron synapses terminates SWR; eta_D 0.18, tau_D 250 ms; B->A conductance 8 nS before depression. SWR initiation by disinhibition of pyramids via competition of two interneuron classes | Evangelista et al. 2020 | READ |
| Evangelista: cells | 8200 PC, 135 PV BC, 50 anti-SWR cells; ripple peak 135 Hz (90-180 Hz filter); SWR duration 50-100 ms | same | READ |
| Schlingloff 2014 (slice, mouse): mechanism | excitatory envelope drives reciprocally connected PV BCs, which fire ripple-frequency spikes phase-locked via reciprocal inhibition; measured ripple 189 +/- 16.7 Hz (light evoked), 186 +/- 5.3 Hz (spontaneous) | Schlingloff 2014 | READ |
| Schlingloff: E/I ratio onto pyramids | gamma 0.23; SWR 0.47 (twice as big), i.e. I/E about 2.1 in SWR (DERIVED); gabazine puff reduced SWR envelope from 5.17 mV to 2.81 mV and raised PVBC spikes per SWR (3.09 -> 5.3) | same | READ (page text; one possible typo noted by the reader tool) |
| Schlingloff model: PVBC-PVBC | connection probability about 0.15; synaptic tau 1.5 ms; delay 1.5 ms; reversal -70 mV; max conductance 2 nS (citing Bartos 2002); about 150 PVBCs per 600 um slice | same | READ |
| Stark 2014 (in vivo CA1): causal role | depolarising a small cluster of nearby pyramids induces high-frequency oscillation; silencing pyramids or driving PV/SOM interneurons stops ripples; local GABA-A block abolishes ripples; PV activation sets ensemble spike timing. Pyramid precedes interneuron by about 90 deg per ripple cycle (via a review) | Stark et al. 2014 | READ (abstract/snippets) |
| Gan 2017 (CA1, awake head-fixed mice): conductance ratio | peak inhibitory/excitatory conductance ratio during ripples 4.1 +/- 0.5; IPSCs phase-locked to late ascending phase; IPSC size tracks ripple magnitude, EPSC size does not; PV+ cells supply major share | Gan et al. 2017 | READ |
| Hulse 2016 (CA1, awake mice) | inhibition scales with net excitation, keeping firing sparse; post-ripple hyperpolarisation proportional to excitation; no ratio number found | Hulse et al. 2016 | READ (abstract) |
| English 2014 (CA1, freely moving mice) | large depolarisations during SWRs often cross spike threshold, but spiking suppressed by concurrent shunting inhibition; post-ripple AHP and spike suppression | English et al. 2014 | READ (abstract) |
| Kim and Kim 2025 CA3 attractor model: global vs selective inhibition | CA3 2400 E, 120 I (5%); recall about 90% with selective inhibition vs about 60% global-only (equal cues); with 2-6 competing engrams, selective about 80% -> 60%, global about 60% up to 3 engrams then about 30% at 6; engram about 10 CA3 excitatory cells; non-plastic synapses 3 nS, qmax 3 nS, E->I 0.5 nS, GABA-A:GABA-B 9:1 | Kim and Kim, PLoS Comput Biol 2025 | READ |
| Classical CA3 theory (Treves and Rolls 1991/1994) | capacity scales as N/[a ln(1/a)] at sparsity a; conventional models use global (uniform) inhibition | Treves and Rolls (via 2026 arXiv and 2025 PLoS CB summaries); PDF unreadable | READ (secondary); inhibition acts as threshold/gain control to keep activity at sparsity a: RECALLED |
| Hasselmo | cholinergic modulation suppressing recurrent transmission during encoding; no numbers found | Hasselmo et al. | not found |
| Kali and Dayan 2000 | CA3 recurrent model, attractors selected by perforant path input; no inhibition numbers found | Kali and Dayan, J Neurosci 20:7463 | READ (abstract), numbers not found |
| Malerba and Bazhenov 2019 | paper not located by search | | not found |
| Taxidis 2012/2013 | not searched successfully | | not found |
| Bezaire 2016 CA1 model: inhibitory counts | 311,500 pyramids; 27,240 interneurons (8%) | Bezaire et al. 2016 (from CA3_NATURAL_RANGES.md) | READ (earlier) |
| Inhibitory synapses per pyramid in real CA3 | not found. Tukker 2013: PV BC receives about 35,000 synaptic inputs (READ via earlier file). Sik 1995: one basket cell contacts more than 1500 pyramids and 60 PV cells (READ earlier) | | partly found |

Answer to "how many inhibitory synapses and what strength": no source gives a minimum count for burst termination or memory competition. The only quantitative anchors are (a) Ecker 0.65 nS x about 37 PVBC inputs per PC with p=0.25, (b) Evangelista 0.7 nS with p=0.5 (about 67 inputs from 135 BCs), (c) I/E conductance of about 2 (Schlingloff SWR, from E/I 0.47) to 4.1 (Gan, CA1 peak). Burst termination in the Ecker and Evangelista models is not simple feedback inhibition from PVBCs: it is end-of-sequence (Ecker) or short-term depression of a second interneuron class (Evangelista).

## B. Unitary IPSC / EPSC in CA3

| Synapse | Value | Source | Status |
|---|---|---|---|
| PVBC -> PC conductance (model) | 0.65 nS; rise/decay 0.3 / 3.3 ms; p=0.25; delay 1.1 ms | Ecker 2022 Table 3 | READ (model parameters, fitted to data) |
| PC -> PVBC | 0.85 nS; rise/decay 1 / 4.1 ms; p=0.1; delay 0.9 ms | Ecker 2022 Table 3 | READ |
| PVBC -> PVBC | 5 nS; rise/decay 0.25 / 1.2 ms; p=0.25 | Ecker 2022 | READ |
| PVBC -> PC (Evangelista) | 0.7 nS; p=0.5; tau 1.5 ms | Evangelista 2020 | READ |
| PC -> PVBC (Evangelista) | 0.05 nS; p=0.2; tau 2 ms | same | READ |
| PVBC -> PVBC (Evangelista) | 5 nS; p=0.2; tau 1.5 ms | same | READ |
| PV-BC -> BC unitary IPSC decay (slice, mouse) | amplitude-weighted decay 1.2 ms CA3, 1.8 ms CA1, 2.5 ms DG at 33-34 C; BC-BC faster than BC-principal | Bartos et al. 2002 PNAS | READ (snippet); amplitudes in nS not found |
| CA3-CA3 unitary EPSC | connection probability 0.92%; 1-2 contacts, 1 contact in 58% of connected pairs; amplitude (pA) not found | Guzman et al. 2016 | READ (snippet); amplitude not found |
| Synapses per PVBC->PC connection | not found (Ecker models one conductance per connection); CA1 model 1-10 synapses per connection (earlier file) | | not found for CA3 |
| Release probability | not found; Ecker excludes short-term plasticity | | not found |
| Gabazine/GABA-A decay vs ours | ours: 10 ms decay, 0.16 nS; literature PVBC->PC 1.2-3.3 ms decay, 0.65-0.7 nS | DERIVED comparison | DERIVED |

## C. Engram size and structure

| Quantity | Value | Source | Status |
|---|---|---|---|
| Overlap of cells active at training and test (engram reactivation) | roughly 10-40% depending on study; chance in basal amygdala about 11% | Josselyn and Tonegawa 2020 | READ |
| Engram size vs memory strength | stable, invariant to memory strength; engrams "sparsely encoded", a "small" fraction of eligible cells | same | READ |
| Percent of neurons allocated (LA, CREB) | review gives no percent; commonly quoted LA 10-30% (Han 2007, Yiu 2014) | | RECALLED |
| DG engram size | commonly about 2-4% of granule cells in c-fos tagging | | RECALLED |
| CA3 engram fraction | not found | | not found |
| Connectivity among engram cells | DG engram cells have higher AMPA/NMDA ratio and more spines; CA3 engram cells more functionally connected to DG engram cells than non-engram CA3; CA1 engram cells with CA3 engram input have more/larger spines; "fire together, wire together" | Josselyn and Tonegawa 2020 | READ |
| Inhibition and engram size | inhibiting SOM interneurons enlarges DG fear engram (lateral-inhibition-like); inhibiting PV in BLA enlarges LA engram (disynaptic inhibition); DG engram cells have stronger connections to PV CA3 basket cells (feedforward inhibition supports precision) | same; Stefanelli et al. 2016 | READ |
| Stefanelli 2016 mechanism | GCs recruit SOM interneurons that inhibit dendrites of neighbouring GCs (lateral inhibition limits ensemble size); fraction not found | Neuron 89:1074 | READ (abstract) |
| Yiu 2014 | cells with higher excitability just before training are allocated to the trace; their activation can cue retrieval | Neuron 83:722 | READ (abstract) |
| Rao-Ruiz 2019 | not searched | | not found |
| Our 8-of-96 | 8.3% of the pyramidal pool | DERIVED | DERIVED |
| Model comparison | Kim and Kim 2025: about 10 of 2400 CA3 cells per engram (0.4%) | PLoS CB 2025 | READ |

Reading: 8.3% is within the range quoted for lateral amygdala (RECALLED) and well above DG/CA3 engram fractions (DG RECALLED, CA3 not found). It is a plausible engram size for a 96-cell network (8 cells is the smallest useful assembly given a 4-cell cue), but not a "natural CA3" fraction; with 96 cells a natural 1-5% would be 1-5 cells.

## D. Pattern completion thresholds

| Quantity | Value | Source | Status |
|---|---|---|---|
| Nakazawa 2002 (mice, CA3 NR1 KO, water maze, 4 cues) | KO impaired when part of the cues was presented; press accounts: with one cue (25% of cues) KO fail, with all four succeed; per-fraction percentages not found | Science 297:211 | READ (secondary press summaries); exact numbers not found |
| Gold and Kesner 2005 (rats, CA3 lesion, 4 extramaze cues) | 0,1,2,3 or 4 cues removed at choice; controls complete well regardless; CA3-lesioned error rises steadily as cues removed | Hippocampus 15:808 | READ (abstract); percent correct not found |
| Neunuebel and Knierim 2014 (rats) | CA3 population response more coherent than DG input under local/global cue conflict; proximal CA3 (weak recurrents) degraded, distal CA3 (strong recurrents) coherent (Lee 2015) | Neuron 81:416 | READ; no cue-fraction number |
| Guzman 2016 model | sparse (0.92%), motif-rich, single-contact connectivity supports robust completion; fraction of cue needed not found | Science 353:1117 | READ; number not found |
| Hebb / Josselyn | reactivating a fraction of an assembly can reactivate it; no required fraction given | Josselyn and Tonegawa 2020 | READ |
| Fraction of cue needed in theory | not found (Treves and Rolls: depends on loading and sparsity) | | not found |

Rodent behaviour: completion survives removal of 50-75% of cues (CA3-dependent), and fails in CA3-impaired animals at about 25% cue. Our 4-of-8 (50%) cue lies inside the normally-functional range.

## What to change in our network and recipe

All items are INFERENCE grounded in the numbers above; magnitudes are starting points to test, not published requirements.

1. Fix the GABA weight, do not leave it at 0.2. Literature PVBC->PC unitary conductance is 0.65-0.7 nS (Ecker, Evangelista; model values). Ours is 0.16 nS per spike. Set weight about 0.8-0.9 (0.65-0.7 nS) as the physiological baseline; to compensate for fewer synapses per cell, allow up to about 2-4 (1.6-3.2 nS per synapse, equivalent to 2-4 co-located contacts as in the CA1 model's 1-10 synapses per connection) as a test range.
2. Inhibitory drive per pyramid. Ecker implies about 37 PVBC inputs per PC (0.25 x 150) x 0.65 nS, up to about 24 nS if all fire; Evangelista about 67 inputs x 0.7 nS. Ours, 13.7 x 0.16 = 2.2 nS. Target coincident inhibition of about 10-20 nS on non-engram pyramids (comparable to the 14 nS excitatory firing threshold and 18 nS cue volley), reached by combination of items 1 and 3. Target I/E conductance ratio about 2 during an engram burst (Schlingloff SWR: E/I 0.47) up to about 4 (Gan CA1 peak) on non-member cells; use about 0.5-1 on member cells so recall still fires.
3. Synapse counts. Target at least 25-35 Int->Pyr synapses per pyramid (mean), zero cells with none (now 24 of 96 have none). With only 48 interneurons, p=0.25 gives 12 (our 14 is already near that); to reach 30 either raise p to about 0.6 (Evangelista used 0.5) or use 2-3 synapses per connection (CA1 model 1-10 per connection). Keep PC->Int small-number reliable: Ecker 0.85 nS at p=0.1 vs Evangelista 0.05 nS at p=0.2, so literature disagrees by 17x; pick about 0.85 nS only if interneurons must fire on 4-8 coincident pyramid spikes.
4. Interneuron-interneuron. Both models use 5 nS PVBC->PVBC at p=0.2-0.25 with 1.2-1.5 ms decay. Use about 5 nS weight (weight about 6 at 0.8 nS) with fast kinetics if ripple timing is a goal. Ripple generation needs this recurrent loop plus fast PC->PVBC drive; without PVBC-PVBC the Ecker model gives no ripples.
5. Kinetics. Literature decay 1.2-3.3 ms (PVBC) vs ours 10 ms. A 10 ms decay is too slow for 150-200 Hz ripples; use about 3 ms for PVBC-class synapses and keep a slower class (about 4-10 ms, Evangelista anti-SWR 4 ms) only for the second interneuron population that terminates bursts.
6. Burst termination. Do not expect simple PVBC feedback to end the burst. Either (a) keep end-of-sequence termination, (b) add a second interneuron class (about 50 of 8200 = 0.6% in Evangelista; about 6 of 96 PC equivalent) with a depressing B->A synapse (eta_D 0.18, tau_D 250 ms), or (c) rely on adaptation as now. For us, option (b) with about 4-6 slow interneurons is the cheapest test.
7. Interneuron fraction. 48/96 = 33% is far above anatomy (7-13%; Ecker PVBC 1.8%). With 96 PCs, 8-14 interneurons are natural; keep 48 only as a means to give each cell enough inhibitory inputs. Count synapses per pyramid, not cells, as the controlled variable.
8. Engram size. 8 of 96 (8.3%) is within the quoted amygdala range but above DG/CA3; natural CA3 fractions not found. For competition tests use 2-4 engrams of 4-8 cells with overlap at most 10% (Kim and Kim recall falls from about 70% to about 35% as overlap goes 0.1 -> 0.3 even with selective inhibition). Do not go below 4 cells per engram (the cue is 4).
9. Cue fraction. Rodent completion works with 25-50% of cues (Nakazawa, Gold and Kesner). Test cue fractions 25%, 38%, 50% (2, 3, 4 of 8) and require no-recall at about 0-12% (0-1 cell). Currently the 4-cell cue gives 18 nS and fires every non-cue member at threshold 14.5 nS, so completion is all-or-none; with inhibition fixed per items 1-3, the threshold on non-member cells should rise above 18 nS so that 1-cell or random 4-cell cues of other memories fail.
10. Selective inhibition. Kim and Kim: assembly-specific (selective) inhibition raised competing-memory recall from about 60% to about 80-90%. Engram-specific inhibition (an interneuron driven by engram members and projecting to non-members, lateral-inhibition style, as in Stefanelli SOM->GC) is the literature-supported role for inhibition in engram models; our 5 of 48 interneurons that can be driven by 8 cells to 15 nS is too few: aim for at least 10 interneurons driven past threshold by one engram, projecting preferentially to non-members.

## Key references

1. Ecker A, Bagi B, Vertes E, Steinbach-Nemeth O, Karlocai MR, Papp OI, Miklos I, Hajos N, Freund TF, Gulyas AI, Kali S. Hippocampal sharp wave-ripples and the associated sequence replay emerge from structured synaptic interactions in a network model of area CA3. eLife 2022;11:e71850. doi 10.7554/eLife.71850 (PMC8865846).
2. Evangelista R, Cano G, Cooper C, Schmitz D, Maier N, Kempter R. Generation of sharp wave-ripple events by disinhibition. J Neurosci 2020;40:7811-7836. doi 10.1523/JNEUROSCI.2174-19.2020 (PMC7548694).
3. Schlingloff D, Kali S, Freund TF, Hajos N, Gulyas AI. Mechanisms of sharp wave initiation and ripple generation. J Neurosci 2014;34:11385-11398. doi 10.1523/JNEUROSCI.0867-14.2014 (PMC6615505).
4. Stark E, Roux L, Eichler R, Senzai Y, Royer S, Buzsaki G. Pyramidal cell-interneuron interactions underlie hippocampal ripple oscillations. Neuron 2014;83:467-480. doi 10.1016/j.neuron.2014.06.023.
5. Gan J, Weng SM, Pernia-Andrade AJ, Csicsvari J, Jonas P. Phase-locked inhibition, but not excitation, underlies hippocampal ripple oscillations in awake mice in vivo. Neuron 2017;93:308-314 (PMC5263253).
6. Bartos M, Vida I, Frotscher M, Meyer A, Monyer H, Geiger JRP, Jonas P. Fast synaptic inhibition promotes synchronized gamma oscillations in hippocampal interneuron networks. PNAS 2002;99:13222-13227. doi 10.1073/pnas.192233099.
7. Guzman SJ, Schlogl A, Frotscher M, Jonas P. Synaptic mechanisms of pattern completion in the hippocampal CA3 network. Science 2016;353:1117-1123. doi 10.1126/science.aaf1836.
8. Josselyn SA, Tonegawa S. Memory engrams: recalling the past and imagining the future. Science 2020;367:eaaw4325. doi 10.1126/science.aaw4325 (PMC7577560).
9. Stefanelli T, Bertollini C, Luscher C, Muller D, Mendez P. Hippocampal somatostatin interneurons control the size of neuronal memory ensembles. Neuron 2016;89:1074-1085. doi 10.1016/j.neuron.2016.01.024.
10. Nakazawa K, Quirk MC, Chitwood RA, ... Tonegawa S. Requirement for hippocampal CA3 NMDA receptors in associative memory recall. Science 2002;297:211-218. doi 10.1126/science.1071795. (Author list beyond first, partly RECALLED.)
11. Gold AE, Kesner RP. The role of the CA3 subregion of the dorsal hippocampus in spatial pattern completion in the rat. Hippocampus 2005;15:808-814. doi 10.1002/hipo.20103.
12. Kim G, Kim P. Selective inhibition in CA3: a mechanism for stable pattern completion through heterosynaptic plasticity. PLoS Comput Biol 2025;21:e1013267. doi 10.1371/journal.pcbi.1013267.

Also seen: Neunuebel JP, Knierim JJ, Neuron 2014;81:416-427 (PMC3904133); Yiu AP et al., Neuron 2014;83:722-735, doi 10.1016/j.neuron.2014.07.017; Hulse BK et al., Neuron 2016; English DF et al., J Neurosci 2014;34:16509-16517 (PMC4252557); Kali S, Dayan P, J Neurosci 2000;20:7463-7477.

## Not found (be explicit)

Treves and Rolls inhibition numbers; Hasselmo numbers; Malerba and Bazhenov 2019; Taxidis 2012/2013; Rao-Ruiz 2019; Hajos/Buzsaki review numbers; Hulse and English ratios; CA3 unitary PVBC->PC and PC->PVBC amplitudes from paired recordings; synapses per connection and release probability in CA3; minimum inhibitory synapse count for burst termination; CA3 engram fraction; exact cue-fraction percent-correct from Nakazawa and Gold and Kesner.
