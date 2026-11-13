# Request for an approved range for Netmorph D_synmax (interneuron pairs)

**SUPERSEDED (2026-11-13) by the team guidance: D_synmax maxima are 1.5 um pyramidal-pyramidal and 0.1-0.15 um for interneuron pairs (maxima only, minimum 0), not the 0.5 um proposed below. Where natural arborization conflicts with a built-in specification, natural arborization wins (Randal's rule). Caveat: interneurons have no spines, and spines are not in the EM output yet. The 0.5/1.0 um runs below are a sensitivity study only. `bio_ranges.json` is not changed until Randal confirms the maxima. Kept for the record.**

**SENT to Randal Koene by email 2026-11-11 (Marianna not yet contacted)** | 2026-11-09
For: Randal Koene, Marianna Gabrielyan (NetMorph / BrainGenix). From: John.

## The ask

We need an approved biological range for the Netmorph parameter `D_synmax` for the three pair types that involve an interneuron (`D_synmax.pyramidal.interneuron`, `D_synmax.interneuron.pyramidal`, `D_synmax.interneuron.interneuron`), so that it can be added to `bio_ranges.json`. If the team judges that these parameters must stay at their default of 0.1 um, we need that ruling instead. We propose 0.5 um as our working value. It matters because the default leaves interneurons almost disconnected from pyramidal cells in our grown networks, and we do not want to keep using a value that has no team-approved range.

## What the parameter is

`D_synmax` is the maximum axon-dendrite distance at which Netmorph forms a synapse. The defaults are 1.0 um for pyramidal-to-pyramidal (Pyr->Pyr) and 0.1 um for every pair involving an interneuron (set in `synapse_formation_model.cc` line 50, defaults in `synapse_formation_model.hh`, `maxfibredistance`). Netmorph's own source comment says that spiny combinations bridge up to 1.0 um and aspiny combinations 0.1 um. `D_synmax` is not one of the seven hard-limited parameters and has no entry in `bio_ranges.json`. Those seven parameters stayed within their limits in every run described here.

## Evidence from growth

We grew the same network three times (same geometry, same random seed 20240628), changing only the three interneuron `D_synmax` values. "Sim" is our NES simulation ID. Sim 127 is the default (0.1 um), sim 133 is 0.5 um, sim 134 is 1.0 um. Pyr->Pyr is essentially unchanged (matrix correlation with sim 127: 0.9749 at 0.5, 0.9724 at 1.0).

| quantity | sim 127 (0.1 um) | sim 133 (0.5 um) | sim 134 (1.0 um) |
|---|---|---|---|
| Pyr->Pyr AMPA synapses | 22651 | 22899 | 22787 |
| Pyr->Int AMPA synapses | 92 | 1208 | 3627 |
| Int->Pyr GABA synapses | 217 | 3331 | 10257 |
| Int->Int GABA synapses | 33 | 543 | 1504 |
| Pyr->Int pairs | 70 | 397 | 640 |
| interneurons (of 27) with zero pyramidal input | 13 | 7 | 5 |
| mean / median AMPA input per interneuron (nS) | 3.339 / 0.980 | 43.846 / 6.860 | 131.647 / 26.460 |

## Functional evidence

These tests ran on the NES simulator, using copies of sims 133 and 134 with programmed weights.

- Interneurons fire on NES at 0.5 um; this is the first time they have fired in this project. The firing threshold for a synchronous volley is about 15 nS for both cell classes.
- On the 0.5 um network we programmed K=3 disjoint engrams (8 cells each) with cue-size selectivity: a 4-cell cue completes the pattern (4/4), while 2- and 3-cell cues do not (0/4), with no cross-pattern or spurious activity.
- With feedback-only inhibition routing, the largest tolerated weight on non-engram Pyr->Pyr connections ("background weight") was 0.01 without inhibition, 0.03 at 0.5 um and 0.05 at 1.0 um.
- At 1.0 um, with uniform Pyr->Int weights, the interneurons fire on the cue alone and veto recall (0/4 for two of three patterns). Scaling down only the cue-cell-to-interneuron weights removed the veto.
- Inhibitory synapses are about 13% of input synapses onto pyramidal cells at 0.5 um (3331 vs 22899) and about 45% at 1.0 um (10257 vs 22787); we regard 45% as high.

## Why 0.5 um, and caveats

0.5 um gives a usable interneuron reservoir (1208 Pyr->Int and 3331 Int->Pyr synapses, against 92 and 217 at the default) with an inhibitory share of about 13% of input synapses onto pyramidal cells, which we have not yet checked against a reference value. At 1.0 um that share is about 45%, which we think is too high. This is a working value, not a validated one. The evidence comes from one geometry, one random seed and one trial per condition (the simulator was deterministic in repeats, to within one or two spikes). Recall is AMPA-only because the weight API zeroes NMDA on programmed Pyr->Pyr pairs; GABA weight is fixed at 0.2; STDP was off. Cue-size selectivity needs a narrow window (cue strength about 20% above threshold) and was not tested with jittered cues. Robustness tests have since been run; see 'Additional evidence (robustness round)' below.

## Additional evidence (robustness round)

After the first draft we ran four more experiments on fresh copies; each simulation ID below is one of our own NES simulations.

**Synapse counts versus D_synmax (same random seed and soma positions)**

| D_synmax (um) | Pyr->Int AMPA synapses | Int->Pyr GABA synapses | Int->Int GABA synapses | Pyr->Pyr AMPA synapses | simulation |
|---|---|---|---|---|---|
| 0.1 | 92 | 217 | 33 | 22651 | 127 |
| 0.3 | 537 | 1441 | 201 | 22761 | 147 |
| 0.5 | 1208 | 3331 | 543 | 22899 | 133 |
| 0.7 | 2080 | 5775 | 868 | 22821 | 151 |
| 1.0 | 3627 | 10257 | 1504 | 22787 | 134 |

- The counts follow a power law in D_synmax with an exponent of about 1.6. The 0.3 and 0.7 values were predicted in advance from the other three points (predicted 533 and 2070 Pyr->Int synapses, measured 537 and 2080; predicted 1427 and 5823 Int->Pyr, measured 1441 and 5775). Pyramidal-to-pyramidal wiring is unaffected at every value.
- Three further random seeds at D_synmax 0.5 (simulations 141, 145, 146): Pyr->Int synapses 955, 1399, 927; Int->Pyr 2951, 2585, 3575; interneurons receiving enough pyramidal input to fire (at least 13.84 nS): 6, 8, 5 of 27 (10 of 27 in simulation 133). The original seed was the most favourable of the four for interneuron drive.
- On all four seeds at 0.5, three 8-cell patterns each recalled from a 4-cell cue and never from a 2- or 3-cell cue (12 of 12 patterns), with no activity outside the cued pattern when the remaining pyramidal weights were pruned.
- Inhibition raised the largest non-pattern ("background") weight that still gives clean recall from 0.01-0.02 to 0.02-0.03 on every seed at 0.5. For the original seed the tolerated background weight with feedback-only inhibition was 0.02 at D_synmax 0.3, 0.03 at 0.5 and 0.7, and 0.05 at 1.0; without inhibition it was 0.01 at every value.
- With uniform pyramidal-to-interneuron weights, the cue blocks its own recall at D_synmax 1.0 but not at 0.7 or below.
- Recall tolerates cue spikes spread over up to 9 ms and fails at 12 ms (simulation 142).
- The built-in STDP rule only potentiates (its depression branch cannot be reached with the current shift of -4 ms). With STDP on, cue-size selectivity was lost after a single recall (simulation 144); with STDP off, behaviour was unchanged over repeated recalls (simulation 143). All other results here were obtained with STDP off.

## Questions for the team

1. Is a bridging distance of 0.5 um from bouton to dendritic shaft defensible for interneuron contacts?
2. Should the three pair types (Pyr->Int, Int->Pyr, Int->Int) share one value, or have separate ranges?
3. What lower and upper limits should `bio_ranges.json` carry for `D_synmax`?
4. Is there a preferred biological check, for example the inhibitory synapse fraction per pyramidal cell, that you want us to report alongside?
5. Should `D_synmax` become a sampled parameter in the auto-configuration batches?
6. The built-in AMPA STDP rule cannot depress with the current parameters (shift -4 ms, evaluated only on postsynaptic spikes). Is that intended, and should recall tests be run with STDP off until it is changed?
