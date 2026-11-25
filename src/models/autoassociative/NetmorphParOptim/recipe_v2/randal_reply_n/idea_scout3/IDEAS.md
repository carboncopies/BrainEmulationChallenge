# idea_scout3: new, biologically legitimate ideas for our two failures (2026-11-24)

This is a literature scout only. I ran no simulations, sent no emails, made no git commits and did not touch NES or the API. Earlier scouts (math_scout, math_scout2, bio_scout) are not repeated here except where noted.

**The two failures**
- **(R) Reverberation.** A dense learned assembly of 17 cells completes from 50-75% cues only with input scaling (the LH arm). It then fires for 200-440 ms at about 65 Hz, and GABA x1/x2 does not stop it (partial_cue Addendum B).
- **(C) Capacity.** The networks hold about 2 hand-designed memories, or 1 dense assembly (fresh_learn, partial_cue B).

## How sources were checked (read this first)
- **How verification was done.** Three research subagents ran web searches and fetched each source. Most PubMed, PMC and publisher pages refused automated fetching, so the agents fell back to Europe PMC REST records, arXiv, author pages or PDFs. I did not re-fetch every source myself.
- **VERIFIED** means an agent fetched a page and read the abstract, or the full text where it says "full text/PDF". A number counts as VERIFIED only if it was read on the fetched page.
- **VERIFIED (metadata)** means the title, authors and venue were seen but the abstract was not read.
- **UNVERIFIED** means the claim came from a search snippet, a secondary citation or memory. It is marked inline wherever it appears.
- Two agents disagree on some details. Where they do, I give both versions (see Guzman 2016 and Hajos 2013 below).
- **Model values were read by me.** The simulator values below come from the E4 model file `v2-hdi-V1n20_s33333` (read-only, with `gaba_vm/modelfile.py` and `gaba_patch/gabafile.py`) and from the NES source in `wt/nes-linefix`.

## 0. What our model does now, compared with measured biology

| item | our E4 model (read from the model file / source) | biology (source, status) |
|---|---|---|
| Spike reset | `ResetMethod` = TOVM, which resets to the pre-spike Vm, i.e. about the threshold of -50 mV. The file also holds `Vreset` -55 mV, but TOVM ignores it. NES offers ONSET and AFTER, which reset to `ResetPotential_mV`. | AdEx fits: V_r about -53 mV against V_T -42 to -56 mV, and "regular bursting is made possible with a V_r higher than the effective threshold" (Naud 2008, VERIFIED full text). The Hippocampome CA3c Izhikevich fit resets about 2 mV below threshold, but adds a large slow recovery jump per spike (d = 104, recovery tau about 500 ms) (Venkadesh 2018, VERIFIED Table 1). CA3b fAHP is 10.2 ± 0.5 mV and only 16-17% of cells burst, and only under strong current (Hemond 2008, VERIFIED). |
| Slow AHP | g 1 nS, gmax 2 nS (saturating, Kd 0.3), rise 30 ms, decay 300 ms. Interneurons have sAHP 0. | The sAHP peaks about 500 ms after a train, decays with tau about 1.5 s (1.3-1.6 s) and lasts 3-20 s. The mAHP (M-current/SK) acts over 50-100 ms (Sahu & Turner 2021 review, mostly CA1, VERIFIED). No CA3 sAHP conductance was found (UNVERIFIED). |
| Threshold adaptation | +10 mV x (1 - h), with h dropping 0.2 per spike and recovering with tau 50 ms. The floor rises +1 mV per spike and recovers with tau 500 ms. | Roughly covers the mAHP time scale (my inference). |
| Fatigue | Hard cap of 300 spikes, recovery over 1000 ms. This is effectively off. | No biological analogue as a hard cap. See idea 8. |
| GABA_A | Erev -70 mV (= Vrest -70), rise 0.5 ms, decay 10 ms, 0.8 nS per synapse. One interneuron type. | Basket→pyramidal decay is biexponential, 1.2 ms (60%) + 7.3 ms (40%) (Bartos 2002, VERIFIED). OLM→pyramidal decay is 20.8 ± 1.7 ms and axo-axonic 11.2 ms (Maccaferri 2000, VERIFIED abstract). GABA_A,slow decays in 30-70 ms (Pearce 1993, VERIFIED abstract). |
| GABA_B | none | Activation tau 45 ms, inactivation 110 ms (84%) and 516 ms, Erev -97.9 mV (Otis 1993, granule cells, VERIFIED abstract). Normally needs several interneurons firing together; one interneuron at 100 Hz x 30 spikes gave none (Scanziani 2000, VERIFIED PDF). |
| Short-term plasticity | none. NES has no depression or facilitation. `SynTrQuantalRelease` exists but is not used by LIFC. | CA3→CA3 depresses little at near-physiological temperature, see the Guzman 2016 row below. Pyr→basket synapses depress (EPSP2 at 34-94% of EPSP1) (Ali et al. 1998, VERIFIED abstract). Pyr→OLM synapses facilitate (EPSP2 = 253%) (Ali & Thomson 1998, VERIFIED abstract). PV output depresses at high rates (Kohus 2016, VERIFIED abstract). |
| Guzman 2016, CA3→CA3 short-term plasticity (the two agents' versions) | — | Agent C read Table S1 (VERIFIED PDF): EPSC10/EPSC1 is 0.52 at about 22 °C but 1.25 at about 34 °C. Agent A read pp. 1-3: depression is minimal in 5-10 spike trains at 20-100 Hz. Both agree that fast recurrent depression is weak at physiological temperature. |
| Interneuron timing | Interneurons fire about 2-3 ms after the non-cue members. | In CA3 SWRs in vitro, pyramidal cells fire 4.25 ms before the ripple trough and PV basket cells 0.5 ms after it, so PV cells lag by about 3-5 ms. PV cells fire 1.8 spikes per event, in 91% of events. Pyramidal cells fire 0.07 spikes per event. The pyramidal inhibitory conductance is 63.8 nS against 23.5 nS excitatory (Hajos 2013). Agent C read these in PMC full text (VERIFIED). Agent A only got the abstract. Bistratified cells fire 1-2 ms after pyramidal cells during ripples (Klausberger 2004, VERIFIED abstract). |

**Main point for Randal.** Our 2-3 ms interneuron lag is biological. Real CA3 also does not end events with fast feedback GABA_A alone.

What the sources name as the terminators instead:
- adaptation (Traub 1993; Ecker 2022; Levenstein 2019)
- depletion of recurrent release (Staley 1998)
- slow inhibition (Scanziani 2000)
- depression of inhibitory synapses onto a second interneuron class (Evangelista 2020)

The scale of our reverberation is far outside biology:
- Our cells fire about 13-29 spikes each in 200-440 ms. In vitro, pyramidal cells fire 0.07 spikes per SWR (Hajos 2013), and SWRs last about 60 ms on average (Levenstein 2019, VERIFIED).
- Our near-threshold reset is the one model feature the sources tie directly to bursting (Naud 2008). The link to our 65 Hz reverberation is my inference.

## 1. Ranked top 5
"Cost" counts sims in the partial_cue B design: one sim = one model x one arm x one r, with about 27 events. Every idea needs a re-check that completion survives, because each terminator also weakens completion. All neuron and receptor knobs below are model-file patches on COPIES of the model, the method already used in gaba_vm. Weights go through the patched API.

### 1. Reset to a fixed potential below threshold instead of the pre-spike Vm
- **Sources:**
  - Naud, Marcille, Clopath & Gerstner 2008, "Firing patterns in the adaptive exponential integrate-and-fire model", Biol Cybern 99:335. https://pmc.ncbi.nlm.nih.gov/articles/PMC2798047/ (VERIFIED full text).
  - Hemond et al. 2008, "Distinct classes of pyramidal cells exhibit mutually exclusive firing patterns in hippocampal area CA3b", Hippocampus 18:411. https://pmc.ncbi.nlm.nih.gov/articles/PMC4339291/ (VERIFIED).
  - Venkadesh et al. 2018, Front Neuroinform 12:8. https://pmc.ncbi.nlm.nih.gov/articles/PMC5859109/ (VERIFIED).
- **Mechanism.** If the reset is at or above threshold, a cell fires again as soon as the refractory period ends, which gives bursting. A reset 5-10 mV below threshold, as the fAHP trough sets it, gives regular firing.
- **What NES does now.** Our TOVM reset puts a recruited cell back at about -50 mV. Only the 2 ms refractory period, the AHP and the adaptive threshold hold it off (gaba_vm README item 5).
- **NES knob.** Neuron field `ResetMethod` = AFTER (2), using the `Vreset` -55 mV that is already in the file, on Pyr cells only, or on Pyr and Int as a second arm. An extra arm could use -60 mV.
- **Expected effect.**
  - (R): fewer spikes per cell per event and a lower rate. This could break the 65 Hz loop, because the assembly reloads itself every 15 ms and a cell 5 mV lower needs more input to fire again (my inference).
  - (C): indirect. Less ignition from small cues, which may let input scaling go up again.
  - Risk to completion: the first spike is unchanged (reset acts only after a spike). NMDA/AMPA summation for recruited cells is unchanged.
- **Biological risk: low.** -55 mV is within the trough implied by Hemond 2008 (threshold -40 to -45 mV minus 10 mV; my inference). The data-fit CA3c model resets near threshold only together with a large adaptation current, which we do not have.
- **Cost.**
  - Main test: the LH arm on s77777 and s66666 at r 0.56 and 1.0, GABA x1, giving 4 sims, plus 2 sims with reset AFTER on interneurons too.
  - One unit sanity run (f-I curve, 1 sim, or offline with `gaba_check_l/unit_ref.py`).
  - About 6-7 sims in total.

### 2. Adaptation on biological time scales: stronger sAHP with a slower decay
- **Sources:**
  - Traub, Miles & Jefferys 1993, J Physiol 461:525, PMID 8350274 (VERIFIED abstract). A 100-cell CA3 model with 20 inputs per cell, AMPA and NMDA, almost our network. After-discharges of 200 ms or more end in a prolonged AHP. Full-text details are UNVERIFIED.
  - Ecker et al. 2022, "Hippocampal sharp wave-ripples and the associated sequence replay emerge from structured synaptic interactions in a network model of area CA3", eLife 11:e71850. https://doi.org/10.7554/eLife.71850 (VERIFIED full text). Without adaptation, activity becomes a stationary bump. Their AdEx b is 206.8 pA per spike with tau_w 84.9 ms. Their Vreset is -29.7 mV as read by the agent; it is unusual, so check it before quoting.
  - Levenstein, Buzsaki & Rinzel 2019, Nat Commun 10:2478. https://doi.org/10.1038/s41467-019-10327-5 (VERIFIED). Hippocampal events are excitable transients ended by adaptation; sharp waves last about 60 ms.
  - Sahu & Turner 2021, Front Physiol 12:759707. https://www.frontiersin.org/articles/10.3389/fphys.2021.759707/full (VERIFIED review). The sAHP decays with tau about 1.5 s; the mAHP acts over 50-100 ms.
- **Mechanism.** A spike-triggered K+ conductance builds over tens of spikes and ends the event. Our sAHP saturates at gmax 2 nS. At -50 mV, 2 nS x (-90 + 50) mV gives about 80 pA, against Ecker's 207 pA per spike that accumulates over spikes (my arithmetic).
- **NES knob.** Pyr neuron fields:
  - `SlowAfterHyperpolarizationPeakConductance_nS` 1 → 2-3 and `...MaxPeakConductance_nS` 2 → 4-5 (both must rise, because of saturation).
  - `SlowAfterHyperpolarizationDecay_ms` 300 → 1000-1500.
  - Arms: sAHP x2 at tau 1 s; sAHP x3 at tau 1.5 s.
- **Already done.** gaba_vm tried AHP x2 (fast and slow) on the R3 design with GABA silenced: late spikes fell from 331-350 to 2-222 per double cue. It was never tried on a dense assembly, and never with a biological tau.
- **Expected effect.**
  - (R): shorter events, a likely candidate to bring 200-440 ms down toward 50-100 ms.
  - (C): neutral to slightly positive. A slower sAHP also adds history effects: more refractoriness between recalls, like the threshold-floor alternation seen in nmda_gaba_exp. Keep 3 s or more between events.
- **Biological risk: low to medium.** The time constants are measured (CA1-heavy). The CA3 sAHP conductance is UNVERIFIED, so report g as a free parameter.
- **Cost.** LH arm on 2 models x 2 arms x r 0.56 at GABA x1, giving 4 sims, plus 2 at r 1.0. About 6 sims. Combining with idea 1 adds 2.

### 3. A slow GABA_B-like inhibitory component on Int→Pyr synapses
- **Sources:**
  - Scanziani 2000, "GABA spillover activates postsynaptic GABA_B receptors to control rhythmic hippocampal activity", Neuron 25:673. https://doi.org/10.1016/S0896-6273(00)81069-7 (VERIFIED PDF). GABA_B needs about 2-20 interneurons firing together.
  - Otis, De Koninck & Mody 1993, J Physiol 463:391. https://doi.org/10.1113/jphysiol.1993.sp019600 (VERIFIED abstract), for the kinetics.
  - Price et al. 2008, J Neurosci 28:6974. https://pmc.ncbi.nlm.nih.gov/articles/PMC2685170/ (VERIFIED). A unitary neurogliaform GABA_B response is tiny: 1.9 pA peaking at 187 ms.
- **Mechanism.** Synchronous, repetitive interneuron firing, which is exactly what our reverberation produces, recruits a slow K+ inhibition. It peaks at about 150-200 ms and decays over 100-500 ms, the time scale of our events. That matches Randal's "GABA silences the network after a pattern".
- **NES knob.**
  - Model-file receptor records (`gabafile.RDT`: Erev, Rise, Decay, G) for Int→Pyr.
  - **Constraint I checked in the source (`Structs/Neuron.cpp:29-58, 98-106`).** In abstracted mode, the receptors of one (pre, post, type) group share ONE set of kinetics: the median rise, decay and onset of the group's records. Erev is taken from the group's first record. So converting a fraction of a pair's GABA records does NOT add a slow component; it only shifts the median.
  - Workable form: convert whole Int→Pyr pairs, i.e. all outgoing GABA records of 2-4 chosen interneurons (a neurogliaform-like subgroup), to GABA_B-like values. Use Erev -90 to -95 mV, rise about 40-50 ms, decay 150-200 ms and small G (about 0.05-0.1 nS per receptor); these values are my choice, inside the Otis/Price range. The other interneurons keep GABA_A.
  - Which interneurons to pick: the ones that fire most during the reverberation (from the stored partial_cue B spikes).
- **Caveats.**
  - NES has no pooling nonlinearity, so a single interneuron spike will activate it. That is UNLIKE biology. Keep G small so that only dozens of spikes matter, and report the single-spike IPSP size.
  - The patched receptor records still carry NT = GABA, so a later `Neurotransmitter='GABA'` API call would overwrite them. Program GABA through the file only, or reprogram those records afterwards.
  - Kinetics are per (pre, post, type) group, not per record (checked, see above). Idea 6, slow GABA_A on chosen interneurons, has the same constraint and the same whole-pair solution.
- **Expected effect.**
  - (R): ends reverberation after 50-150 ms (the event will still last that long, which is roughly what SWRs do).
  - Single recalls are unaffected: only 2-3 interneurons fire, once each.
  - (C): enforces spacing between successive recalls, which suits Randal's theta-pacing rationale.
- **Biological risk: medium.** The kinetics are measured, but the activation rule (pooling) is not reproduced and conductances per pair are uncertain.
- **Cost.** 1 unit check (1 sim) plus 2 models x 2 G levels x r 0.56 (4 sims) plus 2 at r 1.0. About 7 sims.

### 4. Inhibition co-clustered with each memory (E/I assemblies)
- **Sources:**
  - Rost, Deger & Nawrot 2018, "Winnerless competition in clustered balanced networks: inhibitory assemblies do the trick", Biol Cybern 112:81. https://doi.org/10.1007/s00422-017-0737-7 (VERIFIED abstract).
  - Sadeh & Clopath 2021, Sci Adv 7:eabg8411. https://doi.org/10.1126/sciadv.abg8411 (VERIFIED full text). With E↔I weights x4, learning is slower but the assemblies are specific, versus recruitment of non-stimulated cells at x1. Their network is 500E/500I with assemblies of about 20 cells.
  - Vogels et al. 2011, Science 334:1569. https://doi.org/10.1126/science.1211095 (VERIFIED abstract).
  - Litwin-Kumar & Doiron 2014, Nat Commun 5:5319. https://doi.org/10.1038/ncomms6319 (VERIFIED abstract).
- **Mechanism.** Purely excitatory clusters saturate at maximum rate, which is our 65 Hz. Pairing each excitatory cluster with its own inhibitory cluster gives multistable states at moderate rates. Specific inhibition also stops one assembly from recruiting another's cells.
- **NES knob.**
  - Patched API: Pyr→Int AMPA and Int→Pyr `Neurotransmitter='GABA'` per pair.
  - For each memory, pick the 3-5 interneurons with the most grown pairs from and to its members.
  - Raise within-memory Pyr→Int and Int→Pyr to the GABA x2 level, and keep across-memory pairs at x1 or lower.
  - **Offline first:** count, on the 10 E4 graphs, how many interneurons have grown pairs in both directions with each memory. If interneuron axons are not memory-specific, this idea is weak.
- **Expected effect.**
  - (R): moderate. Rates may fall rather than events end, because GABA_A is still fast.
  - (C): the best structural route past 2 memories in the sources. In our 20-interneuron network it allows at most 4-6 memories with 3-5 interneurons each (my arithmetic).
  - Partial_cue LI (all Pyr→Int at 1.0, global) stopped full-cue reverberation but not partial-cue reverberation. Here the inhibition is memory-specific instead.
- **Biological risk: medium.** Specific E-I wiring is a modelling result. Hippocampal biological evidence for it was not searched (UNVERIFIED). The x2 GABA level is above the literature mean but inside the earlier gaba_patch range. Grown pairs limit what is possible.
- **Cost.** Offline feasibility check, no sims. Then 2 models x 2 memories designed (partial_cue C-type designs) x r 0.56, plus controls: about 8 sims.

### 5. Capacity: steer allocation away from hubs and run near the attractor onset
- **Sources:**
  - McGraw & Menzinger 2003, Phys Rev E 68:047102, arXiv cond-mat/0304021 (VERIFIED). In scale-free networks, the hub-carried part of a pattern is retrieved robustly ("strong partial recognition"), while random topology is best for whole patterns.
  - Leibold & Kempter 2006, Neural Comput 18:904. https://doi.org/10.1162/089976606775774714 (VERIFIED author abstract page). With sparse connectivity, the optimal pattern size scales as 1/c, and at fixed synapses per neuron capacity does not depend on N.
  - Amit & Brunel 1997, Cereb Cortex 7:237. https://doi.org/10.1093/cercor/7.3.237 (VERIFIED). Selective delay attractors appear abruptly at a critical potentiation.
  - Gastaldi et al. 2021, PLoS Comput Biol 17:e1009691. https://doi.org/10.1371/journal.pcbi.1009691 (VERIFIED). Memories merge above about 22% pairwise overlap.
  - Kopsick et al. 2024, J Comput Neurosci 52:303. https://doi.org/10.1007/s10827-024-00881-3 (VERIFIED). A full-scale mouse CA3 model with symmetric STDP and sleep-like downscaling. Its best assembly size is about 0.33% of pyramidal cells, and 5% overlap is harmless.
  - Rolls 2012, "Advantages of dilution in the connectivity of attractor networks", doi 10.1016/j.bica.2012.03.003 (UNVERIFIED: the PDF could not be read).
- **Mechanism.** Our in-degree hubs (11-22 cells receiving 85-99% of the strong pairs, math_run) pull every memory into one hub-centred attractor. Capacity is set by in-degree (about 25), not by 96 cells.
- **NES knob / test.**
  - Offline in `fresh_learn/fllib.py`: rerun the dense-subgraph allocation, which fresh_learn already did, but with hub cells excluded from all assemblies, or each hub allowed in at most one.
  - Rerun it with learned weights scaled down to the smallest gain that still completes from 75% cues (Amit-Brunel critical gain; a uniform x0.8 downscale after learning as in Kopsick).
  - Then simulate only what passes, using API AMPA/NMDA per pair.
- **What is already done.** fresh_learn already did wiring-aware allocation and homeostatic caps and got at most 1 assembly per model. The new parts are hub exclusion and the near-critical gain, so expectations are modest.
- **Expected effect.**
  - (C): maybe 1 → 2 assemblies in some models, or none at all. Leibold-Kempter suggests that at in-degree about 25 the ceiling is low whatever we do.
  - (R): a near-critical gain should shorten reverberation. LH, which is cap-scaled, still reverberated.
- **Biological risk: low.** Allocation and weight level are design choices inside the existing limits.
- **Cost.** Offline (about a day). Then about 4-6 sims if something passes.

## 2. Further ideas (not in the top 5)

| # | idea (source, status) | NES knob | expected effect R / C | bio risk | cost |
|---|---|---|---|---|---|
| 6 | Late dendrite-targeting OLM-like inhibition with slow GABA_A. Sources: Pangalos et al. 2013, PNAS 110:4398, https://doi.org/10.1073/pnas.1215496110, VERIFIED abstract (OLM fire about 6.5 ms after the ripple peak). Maccaferri 2000 (OLM IPSC decay 20.8 ms). Pearce 1993 (GABA_A,slow 30-70 ms). | Model file: Int→Pyr receptor decay 20-50 ms on the 5-8 interneurons recruited latest. Erev unchanged. | R: some shortening. C: neutral. Needs facilitation at Pyr→OLM (Ali & Thomson 1998) to be truly late, which NES lacks. | low (kinetics measured, CA1) | 4 sims |
| 7 | Disinhibition model of SWR: an event ends when PV→"anti-SWR" interneuron synapses depress (η_D 0.18, τ_D 250 ms, events 50-100 ms). Source: Evangelista et al. 2020, J Neurosci 40:7811, https://doi.org/10.1523/JNEUROSCI.2174-19.2020, VERIFIED PDF. | Needs inhibitory short-term depression in NES (code change). | R: strong in their model. | — | outside configuration |
| 8 | Recurrent release depletion ends CA3 population bursts; GABA shortens them but is not needed. Source: Staley et al. 1998, Nat Neurosci 1:201, https://doi.org/10.1038/651, VERIFIED abstract, no taus. | Proper version: depression in NES (code change). Diagnostic stand-in: lower `FatigueThreshold` to 10-20 spikes with recovery 1-5 s. **The hard cap is NOT biological**; use only to ask "would a per-cell spike budget end the events?". | R: certain by construction. C: none. | non-biological as a hard cap | 2 sims (diagnostic) |
| 9 | ISN check: if extra drive to interneurons lowers their rate, the network is inhibition-stabilized, and strong assembly weights are safe only in that regime. Sources: Tsodyks et al. 1997, J Neurosci 17:4382, https://doi.org/10.1523/JNEUROSCI.17-11-04382.1997; Ozeki et al. 2009, Neuron 62:578, https://doi.org/10.1016/j.neuron.2009.03.028; Sanzeni et al. 2020, eLife 9:e54875, https://doi.org/10.7554/eLife.54875. All VERIFIED abstracts. | Forced extra spikes or added drive to interneurons during the reverberation. Look at Int rates, not Pyr rates. | Diagnostic for ideas 4 and 5. | none | 2 sims |
| 10 | Symmetric STDP window for learned assemblies (A+ = A−, tau about 60 ms, hard w_max). Sources: Ecker 2022 (A± 80 pA, tau 62.5 ms, VERIFIED); Hiratani & Fukai 2014, PLoS ONE 9:e101535, https://doi.org/10.1371/journal.pone.0101535, VERIFIED (12 of 32 assemblies survived 30 min; a symmetric window was crucial; they also needed STD, u 0.1-0.2). | `SetSTDP` with receptor STDP fields (STDP_Method Hebbian, A_pos = A_neg, Tau_pos = Tau_neg about 60 ms). The weight cap is via `Weight` ≤ 1. | C: makes "learned" assemblies real rather than programmed. R: none by itself. | low | about 10 sims (training + test) |
| 11 | Sparser, smaller assemblies at the coding level where capacity peaks (Tsodyks & Feigel'man 1988, Europhys Lett 6:101, https://doi.org/10.1209/0295-5075/6/2/002, VERIFIED (metadata); the 1/(a ln(1/a)) formula UNVERIFIED). Includes a covariance rule: small uniform weakening of member→non-member pairs. | API AMPA per pair (lower bound 0.1 weight). | C: more memories only if each member keeps enough within-assembly input. fresh_learn found k ≤ 12 never held. R: smaller assemblies give less recurrent drive. | low | offline first |
| 12 | Theta-phase inhibition limits activity to under about 100 ms per cycle. Source: Lisman & Jensen 2013, Neuron 77:1002, https://doi.org/10.1016/j.neuron.2013.03.007, VERIFIED abstract. The termination effect is UNVERIFIED. | Forced periodic spikes (8 Hz) into a few interneurons, which can be done with direct stimulation. | R: may cut events at the next theta trough. C: pacing. | medium (no septum in the model) | 4 sims |
| 13 | Spatially organised or small-world connectivity costs little capacity (Roudi & Treves 2004/2006, arXiv cond-mat/0407128, cond-mat/0505349, VERIFIED). Near-ordered IF networks give spatial "bumps" instead of retrieval (Anishchenko & Treves 2006, J Physiol Paris 100:225, https://doi.org/10.1016/j.jphysparis.2007.01.004, VERIFIED). Ordered networks get stuck in mixture states; a few long links rescue them (Morelli et al. 2004, arXiv nlin/0310033, VERIFIED; Bohland & Minai 2001, https://doi.org/10.1016/S0925-2312(01)00378-2, VERIFIED metadata). | Offline: check whether our reverberation is a spatial bump (are the late-firing cells spatially clustered, not the stored members?). If yes, a higher D_synmax or a larger slab, within bio_ranges, reduces locality. | Diagnostic. C: modest per the theory. | low | offline; growths only if positive |

Not recommended on its own: raising fast GABA_A further. Perisomatic inhibition in CA3 fires 1-2 ms after pyramidal cells and depresses at high rates (Klausberger 2004; Kohus 2016, https://doi.org/10.1113/JP272231, VERIFIED abstract; Mori et al. 2004, Nature 431:453, https://doi.org/10.1038/nature02854, VERIFIED PDF). So x5 is both non-biological and unlike how CA3 works.

Also checked, less directly useful:
- Torborg et al. 2010, J Neurosci 30:15628, https://doi.org/10.1523/JNEUROSCI.3099-10.2010 (VERIFIED abstract). Without GABA_A, mossy-fibre input gives a long plateau with repetitive firing.
- Saviane et al. 2002, J Physiol 544:469, https://doi.org/10.1113/jphysiol.2002.026609 (VERIFIED abstract). Slow, low-frequency CA3-CA3 depression with taus of 36-98 s, not within-burst.
- Mi, Katkov & Tsodyks 2017, Neuron 93:323, https://doi.org/10.1016/j.neuron.2016.12.004 (VERIFIED abstract). STD gives brief population spikes, and capacity scales with the depression tau. Needs NES STD.
- Mongillo et al. 2008, Science 319:1543 (VERIFIED). Facilitation-based working memory; needs NES STF.
- Fiebig & Lansner 2017, J Neurosci 37:83 (VERIFIED).
- Battaglia & Treves 1998, Neural Comput 10:431, https://doi.org/10.1162/089976698300017827 (VERIFIED). "Sufficiently multiplicative" (shunting) inhibition reconciles stability and capacity. Our GABA Erev (-70) already equals Vrest (-70), so this is mostly in place already (my reading).
- Schlingloff et al. 2014, J Neurosci 34:11385, https://doi.org/10.1523/JNEUROSCI.0867-14.2014; Ellender et al. 2010, J Neurosci 30:5979, https://doi.org/10.1523/JNEUROSCI.3962-09.2010; Klausberger et al. 2003, Nature 421:844, https://doi.org/10.1038/nature01374. All VERIFIED abstracts: SWR initiation and interneuron roles.

## 3. Things that need a simulator change (outside configuration)
1. Short-term depression and facilitation per synapse type: Pyr→PV depressing, Pyr→OLM facilitating, PV output depressing, recurrent depletion. The Tsodyks-Markram u/τ_D/τ_F is the standard form (UNVERIFIED as a citation here). This is the biologically central mechanism for both termination (Staley 1998; Evangelista 2020) and inhibition routing (Pouille & Scanziani 2004, Nature 429:717, https://doi.org/10.1038/nature02615, VERIFIED abstract).
2. A GABA_B activation that is nonlinear in GABA (pooling), for idea 3 to be fully biological.
3. Multiple interneuron types in the growth recipe (PV/OLM/neurogliaform) with type-specific kinetics. At present this is emulated by patching receptor records of chosen interneurons.

## 4. Suggested order (if John approves sims; none started)
1. **Offline, no sims.**
   - Interneuron co-cluster feasibility (idea 4).
   - Hub-excluded allocation and critical-gain scan (idea 5).
   - Spatial-bump check on the stored partial_cue B spikes (idea 13).
   - Pick the interneurons for ideas 3 and 6 from the stored spikes. The kinetics question is settled: the median per group, so whole pairs must be converted.
2. **One preregistered batch of about 16-20 sims on the LH arm (s77777, s66666), each arm with a completion re-check:**
   - reset AFTER -55 (1)
   - sAHP x2 at tau 1 s (2)
   - 1 + 2 combined
   - GABA_B-like (3)
   - fatigue diagnostic (8)
   - ISN probe (9)
3. **Only then capacity sims** (4, 5).
4. **Questions to ask Randal:**
   - Is an assembly event of about 50-100 ms (SWR-like) the acceptable target?
   - Is TOVM reset intentional? It is the one model choice that is outside the measured CA3 regime.

## 5. Unverified or uncertain items (collected)
- CA3 sAHP conductance.
- The CA3→CA3 (associational/commissural) NMDA/AMPA ratio. Only the mossy-fibre ratio, 0.37-0.53, was verified (Carta et al. 2018, J Physiol 596:703, https://pmc.ncbi.nlm.nih.gov/articles/PMC5813612/).
- The GABA_B textbook kinetics used by one agent. Superseded here by Otis 1993, which is verified.
- The Ecker 2022 Vreset value of -29.7 mV (as read; unusual).
- The Tsodyks-Feigel'man capacity formula.
- Rolls 2012.
- Li et al. 1994.
- Brette & Gerstner 2005 reset values.
- Miles 1990 single-pyramid recruitment (fetch failed).
- Klausberger 2003 per-type ripple firing details (from memory).
- Hajos 2013 numbers: read by one agent in full text; the other agent saw only the abstract.
- Most kinetic data are from CA1 or dentate gyrus, not CA3.
- All mapping to our network and all expected effects are my inference, not from the sources.
