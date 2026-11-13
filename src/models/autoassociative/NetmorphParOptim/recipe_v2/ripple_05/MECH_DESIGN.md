# Cross-inhibition mechanism: analysis and experiment design (E1-E4)

MECHANISM STUDY, D_synmax 0.5, NOT BIO-REALISTIC. Offline analysis only: nothing was grown, simulated or sent to NES.
Inputs: connectome dump `fable_loop/it1/viz_a/sample_0000.json`, `recipe/recipelib.py` (`build_pairs`),
`recipe/seed20240628/weights.json`, `ripple_05/raw_main.json` (observed spikes). Machine-readable companion:
`mech_experiments.json` (groups, every Pyr->Int weight change, runs, predictions, all matrices).

## 1. Conventions and the spike model

* AMPA 0.98 nS and GABA 0.80 nS per synapse; pair conductance = `g_peak_sum`; weight = conductance / g_peak_sum in [0,1].
* GABA values below are weight-1 `g_peak_sum` nS, the same convention as `inhibition_matrix` in `ripple_data.json`.
  GABA weight is fixed at 0.2, so the effective conductance is presumably 0.2 x these numbers (not verified).
* Drive of memory i onto interneuron k: `d_ik = min(sum cue->k, 10) + sum noncue->k` (the `build_pairs` rule).
* Spike model (fitted by eye to the four single-memory runs, nominal thresholds):
  `n_ik = cyc` if d >= 20 nS; `(cyc+1)//2` if 15 <= d < 20; `1` if 10 <= d < 15; else 0.
  `cyc = 5` if at least 2 non-cue members have loop gain >= 15 nS, else 2.
  Loop gain of a non-cue member = programmed noncue->noncue input + 4.5 nS per cue cell that itself receives >= 15 nS noncue->cue.
  A conservative variant (thresholds 16/12/8, loop 12) was used for the group search.
* Fit quality: predicted interneuron spikes per recall 17 / 13 / 7 / 10 for G0..G3, observed 19 / 13 / 4 / 7.
  The model over-predicts G2 and G3. It is a ranking tool, not a simulator.
* Metrics per target non-cue member n: spike-weighted `sum_k n_ik * GA[k,n]`; binary `sum_k [d_ik >= 10] * GA[k,n]` (README convention);
  drive-weighted `sum_k (d_ik/15) * GA[k,n]`.

## 2. What the connectome says

* Excitation of interneurons is concentrated on a few cells. Total as-grown Pyr->Int AMPA: id 89 = 500 nS, 93 = 175, 79 = 134,
  82 = 94, 80 = 83, 77 = 69; every other interneuron <= 24 nS. Any 8-cell memory therefore fires 89 (drive 37-56 nS) and usually 93.
* Interneuron 89 is a weak, diffuse inhibitor (56 nS total GABA onto pyramidal cells); 93 is a strong one (138 nS).
* Because the same interneurons fire for every memory, cross-inhibition onto a memory is roughly equal to that memory's own
  feedback inhibition. It is a property of the target cells, not of the source memory. G0 and G1 non-cue members are the most
  inhibited cells; G1 members 41 and 42 receive 48.0 and 48.8 nS (binary) from G0's recall, members 39 and 60 only 17.6 and 12.8.
* Arithmetic for the failing link, G0 -> member 42, observed spikes x g_peak_sum:
  93: 6 x 14.4 = 86.4; 89: 6 x 9.6 = 57.6; 82: 2 x 6.4 = 12.8; 80: 8.8; 90: 8.8; 77: 3 x 0.8 = 2.4; total 176.8 nS.
  Member 41: 91.2 + 33.6 + 22.4 + 7.2 + 7.2 + 4.8 = 166.4 nS. Half of it comes from interneuron 93.
* Burst length is set by recurrence, not by inhibition strength. G0 and G1 have loop gains of 21-24 and 11-27 nS and burst for
  17-21 ms despite a spike-weighted self-inhibition of 137 and 79 nS (mean per non-cue member). G2 has loop gain 13-17 nS and stops
  after 1-2 volleys with only 10 nS. The cue cells that re-fire in G0 (29, 63) receive almost no GABA (16 and 14 nS spike-weighted).
* Margin arithmetic (assumption: E_GABA about -70 mV, weight 0.2 applied to g_peak_sum): the cue gives 18 nS against a 15 nS
  threshold, a 3 nS AMPA surplus x about 50 mV = 150 nS mV. At -51 mV GABA has about 20 mV driving force, so about 7.5 nS effective,
  i.e. about 38 nS g_peak_sum active at cue time, cancels the surplus. Observed: binary mean 31.8 / max 48.8 fails, <= 20 passes.

### Matrix (1): candidate memories = G0..G3 plus the unused fifth group G4

Rows = recalled memory i, columns = target memory j (non-cue members), nominal model, nS g_peak_sum.

Spike-weighted, maximum over the target's non-cue members:

| i \ j | G0 | G1 | G2 | G3 | G4 |
|---|---|---|---|---|---|
| G0 | 136.8 | 150.4 | 59.2 | 37.6 | 26.4 |
| G1 | 120.8 | 140.8 | 52.0 | 27.2 | 14.4 |
| G2 | 63.2 | 68.8 | 28.0 | 20.0 | 9.6 |
| G3 | 76.8 | 103.2 | 32.0 | 18.4 | 12.8 |
| G4 | 65.6 | 88.0 | 28.8 | 23.2 | 21.6 |

Spike-weighted mean: G0 row 122.4 / 92.8 / 41.4 / 26.0 / 13.2; G1 row 101.8 / 82.2 / 35.4 / 18.2 / 10.8;
G2 row 55.0 / 45.0 / 21.0 / 13.4 / 7.8; G3 row 69.6 / 58.6 / 24.4 / 12.4 / 9.2; G4 row 55.0 / 60.4 / 27.2 / 15.0 / 16.8.
Drive-weighted mean: G0 row 71.1 / 57.8 / 25.9 / 16.7 / 10.0; G1 row 69.3 / 57.0 / 25.4 / 18.2 / 10.9 (rest in the JSON).

Calibration against what was observed (spike-weighted max from the real single-memory spikes, target cued 16 ms later):

| link | observed value | outcome |
|---|---|---|
| G0 -> G1 | 176.8 (mean 104.8) | fail, 1-3 of 4 |
| G1 -> G0 | 122.4 (mean 105.8) | fail, 0 of 4 |
| G3 -> G1 | 64.8 (mean 37.8) | pass at Dt 1 and Dt 0.1 |
| G1 -> G2 | 52.0 | pass |
| G0 -> G3 | 38.4 | pass |
| G2 -> G0 | 34.4 (mean 26.8) | pass at Dt 1, fail at Dt 0.1 |
| G2 -> G3 | 9.6 | pass |

Working threshold: <= 65 passed, >= 120 failed, 65-120 unknown. The G2 -> G0 row breaks monotonicity at Dt 0.1, so the
metric is not sufficient on its own.

## 3. Fix A: re-selected groups (E1)

Search: simulated annealing from the original groups (20,000 moves x 5 restarts), moves = replace a cell by an unused cell or
swap two cells. Hard constraint: every cue->non-cue pair has g_peak_sum >= 4.5 nS, so the 18 nS cue design is programmable with
weights <= 1. Objective (conservative model): minimise the maximum spike-weighted cross-inhibition into any non-cue member of any
other memory; require one interneuron with drive >= 25 nS (so interneurons still fire); penalise groups with a sustained loop.

| group | cue | non-cue | min cue->non-cue pair (nS) | loop gain (nS) |
|---|---|---|---|---|
| R0 | 1, 19, 23, 34 | 25, 33, 48, 54 | 4.90 | 8.6, 7.8, 24.4, 7.8 |
| R1 | 9, 52, 56, 62 | 13, 37, 60, 65 | 4.90 | 8.6, 9.0, 4.7, 4.9 |
| R2 | 2, 17, 29, 43 | 24, 31, 32, 47 | 4.90 | 6.9, 8.5, 5.9, 11.8 |
| R3 | 45, 51, 61, 63 | 15, 21, 35, 38 | 4.90 | 11.0, 11.9, 9.8, 2.6 |

Achieved matrix, spike-weighted max (nominal; conservative in brackets where different):

| i \ j | R0 | R1 | R2 | R3 |
|---|---|---|---|---|
| R0 | 7.2 | 13.6 (16.0) | 7.2 (11.2) | 11.2 (13.6) |
| R1 | 8.0 | 13.6 | 9.6 | 12.0 |
| R2 | 15.2 (16.8) | 10.4 (12.8) | 10.4 | 13.6 (14.4) |
| R3 | 6.4 | 11.2 | 5.6 | 9.6 |

Maximum off-diagonal 15.2 nS (conservative 16.8), against 150.4 predicted / 176.8 observed for the original groups.
Binary mean at most 9.6 nS (original 31.8). Predicted interneuron spikes per recall 5, 5, 5, 4; drive onto 89 is 27-40 nS.
The price: these cells receive little inhibition from anyone, so their own feedback inhibition is also small (2.5-5.6 nS mean
over all 8 members). Burst termination relies on the weak recurrence (all loop gains but one below 12 nS), as in original G2.

K=3 re-selected set (separately optimised): cue 1, 9, 43, 56 / non-cue 24, 25, 35, 48; cue 30, 46, 51, 63 / non-cue 21, 58, 60, 65;
cue 2, 16, 19, 27 / non-cue 13, 15, 33, 54. Max off-diagonal 13.6 nS; matrix rows 12.0 / 13.6 / 9.6, 4.0 / 4.0 / 4.0, 8.8 / 12.8 / 8.8.

## 4. Fix B: Pyr->Int weight scaling (E2)

Scale per (memory, interneuron): all member->interneuron pairs of memory i onto interneuron k are either left as programmed
(non-cue weight 1, cue cells capped at 10 nS) or set to weight 0. Weights stay in [0,1]. Non-member pyramidal cells are silent
after pruning, so their Pyr->Int weights are left alone. Rule:

1. Late-spike removal: zero the drive onto every interneuron with d_ik < 15 nS. Those fire 0-2 late spikes by temporal summation
   (observed: 80 at 11.0 ms, 90 at 17.8 ms, 79 at 12.4 ms, 82 at 10.8 ms). That is after the first volleys of the own burst and
   inside the next memory's cue window.
2. Cross cap: among the remaining interneurons choose the keep-set that maximises self-inhibition (spike-weighted mean onto the
   own non-cue members) subject to predicted spike-weighted cross max <= 70 nS onto any other memory's non-cue member.
   At least one kept interneuron must have d >= 25 nS so it fires on every volley.

Result for the original groups:

| memory | kept (drive nS) | removed | cross max before -> after | self mean (non-cue) before -> after |
|---|---|---|---|---|
| G0 | 89 (51.2), 82 (15.7), 77 (18.6) | 93, 80, 90, 79 and weaker | 150.4 -> 69.6 | 122.4 -> 53.6 |
| G1 | 89 (56.1) | 93, 82, 80, 79, 77, 83 | 120.8 -> 28.0 | 82.2 -> 20.0 |
| G2 | 89 (42.3), 93 (23.5), 80 (17.6) | 82, 79, 77 | 68.8 -> 56.8 | 21.0 -> 13.8 |
| G3 | 89 (37.4) | 93, 82, 79, 80 | 103.2 -> 48.0 | 12.4 -> 4.0 |

Arithmetic for G0 -> member 42 after scaling: 89: 5 x 9.6 = 48.0; 82: 3 x 6.4 = 19.2; 77: 3 x 0.8 = 2.4; total 69.6 nS
(observed baseline 176.8). Member 41: 28.0 + 33.6 + 4.8 = 66.4 nS (baseline 166.4). Binary mean G0 -> G1: 31.8 -> 12.0.
Interneurons still fire: 89 gets 37-56 nS from every memory, 2.5x the 15 nS threshold at the lowest.

The trade-off is explicit. 93 is both the main source of cross-inhibition onto G1 and the main terminator of G0's own burst.
Removing it cuts G0's self-inhibition to 44 % and G1's to 24 %. Both have sustained loops, so their bursts may run longer, which
adds 89 spikes (9.6 nS onto member 42 each) and may break the 100 ms activity limit. E2 is predicted to be a partial fix.
Pre-declared fallback E2b, only if E2 shows non-terminating bursts: same rule with cap 100 nS, kept sets G0 {77, 93},
G1 {89, 93}, G2 {80, 89, 93}, G3 {89, 93} (G0 -> G1 max 80.8).

## 5. Experiments

Common protocol: cue cells at +0, +0.5, +1.0, +1.5 ms; run 150 ms; STDP off; fresh copy of `fable-it1a-sim133` per case.
Runs per experiment: order 0,1,2,3 at 12, 16 and 20 ms; shuffled order 2,0,3,1 at 16 ms (K=3: order 0,1,2 and shuffled 2,0,1).
Each run at Dt 1 ms (primary) and Dt 0.1 ms (robustness), plus single-memory baselines.

| exp | groups | Pyr->Int | pairs changed vs `weights.json` |
|---|---|---|---|
| E1 | R0..R3 | standard rule | 46 Pyr->Int (cue caps), 236 Pyr->Pyr via `build_pairs` |
| E2 | original G0..G3 | scaling rule of section 4 | 155 Pyr->Int (151 zeroed, 4 cue caps of G3 onto 89), 33 Pyr->Pyr (G3) |
| E3 | R0..R3 | scaling rule applied to R0..R3 | 152 Pyr->Int (114 zeroed), 236 Pyr->Pyr |
| E4 | original G0, G1, G2 | scaling rule (K=3) | 113 Pyr->Int, all zeroed; 0 Pyr->Pyr |
| E4b | K=3 re-selected set | standard rule | 38 Pyr->Int, 201 Pyr->Pyr |

E3 kept sets: R0 {79, 89, 93}, R1 {89, 93}, R2 {80, 89, 93}, R3 {89, 93}; predicted max off-diagonal 11.2 nS.
E4: re-selection cannot be applied to fixed original groups, so E4 uses the scaling rule. E4b is the pre-declared alternative
"K=3 with the better fix" if E1 beats E2, which is the expected outcome.

## 6. Pre-registered predictions

Timestamp: 2026-11-12 09:54:59 PST. Written before any E1-E4 run. Dt 1 ms unless stated. P = probability.

| quantity | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| P(4/4) first memory in order | 0.95 | 0.97 | 0.95 | 0.97 |
| P(4/4) second memory at 12 / 16 / 20 ms | 0.85 / 0.85 / 0.87 | 0.35 / 0.35 / 0.40 (G1; 2-4 non-cue fire) | 0.86 / 0.86 / 0.88 | 0.35 / 0.35 / 0.40 |
| P(4/4) third memory | 0.85-0.87 | 0.80 | 0.86-0.88 | 0.80 |
| P(4/4) fourth memory | 0.85-0.87 | 0.85 | 0.86-0.88 | n/a |
| shuffled order, P(4/4) per memory | 0.95, 0.85, 0.85, 0.85 | G2 0.97, G0 0.70, G3 0.85, G1 0.80 | 0.95, 0.86, 0.86, 0.86 | G2 0.97, G0 0.70, G1 0.45 |
| P(all memories complete in all 4 runs) | 0.60 | 0.15 | 0.60 | 0.18 |
| latency of last non-cue (ms) | 4.0-4.8 | 4.0-6.5 | 4.0-4.8 | 4.0-6.5 |
| burst end after cue (ms) | 4-12 (P 0.70); > 20 (P 0.10) | G0 18-40 (P 0.55), G1 15-40 (P 0.45), G2 5-12, G3 8-25 | 4-14 (P 0.68); > 20 (P 0.13) | as E2 |
| interneuron spikes per recall | nominal 5, 5, 5, 4; range 3-9 (P 0.75) | nominal 11, 5, 5, 5; ranges 9-16, 5-12, 3-6, 4-8 (P 0.60) | nominal 4, 4, 4, 3; range 2-7 (P 0.75) | nominal 11, 5, 5 |
| peak GABA onto another memory's non-cue member, spike-weighted max (nS g_peak_sum) | nominal 15.2; range 8-30 (P 0.80) | G0 -> G1 nominal 69.6; range 55-110 (P 0.70); baseline 176.8 | nominal 11.2; range 5-25 (P 0.80) | G0 -> G1 69.6; range 55-110 |
| same, binary mean | <= 9.6 | G0 -> G1 12.0 (baseline 31.8) | <= 7.0 | 12.0 |
| P(a burst is not terminated within 40 ms in some group) | 0.10 | 0.50 (G0 0.35, G1 0.45, G3 0.20) | 0.13 | 0.45 |
| P(interneurons silent in some recall) | 0.05 | 0.02 | 0.05 | 0.02 |
| P(a single memory fails on its own) | 0.10 | about 0 (verified groups) | 0.10 | about 0 |
| P(cross-talk or non-member pyramidal spikes) | 0.03 | 0.03 | 0.03 | 0.03 |
| P(all complete at Dt 0.1 ms) | 0.50 | 0.10 | 0.50 | 0.12 |
| P(robust success, section 7) | 0.45 | 0.08 | 0.45 | 0.10 |

Other predictions: P(E1 completes more memories than E2) = 0.80. P(E3 gives the same completion counts as E1) = 0.75.
P(G1 after G0 in E2 is no worse than the baseline 3, 1, 2 of 4 at every spacing) = 0.60.
P(total activity exceeds 100 ms in some E2 run) = 0.40. E4b: P(all complete) 0.70, robust 0.55.

## 7. Risks and what counts as success

* Dt sensitivity. The shuffled baseline passed at Dt 1 ms and lost G0 completely at Dt 0.1 ms, with a predicted cross value of
  only 34 nS. Dt 0.1 produced extra spikes in 15 neurons. A Dt-1-only pass is marginal and must be reported as such.
* Thin cue margin. 18 nS against about 15 nS leaves 3 nS, which about 38 nS g_peak_sum of active GABA cancels (section 2,
  unverified assumptions on E_GABA and on how the 0.2 weight scales conductance). No fix here widens that margin.
* Re-selected groups are unverified. Their cue pairs are 4.90 nS (5 synapses) programmed to 4.5 nS, which is fine, but they have
  never been recalled even singly. Run the single-memory baselines first.
* Low inhibition cuts both ways. E1 and E3 rely on weak recurrence to end bursts. One non-cue member (48 in R0) has loop gain
  24.4 nS; if several re-fire, the burst has little inhibition to stop it.
* The spike model is crude: thresholds fitted to 4 runs, over-predicts G2 and G3, ignores Int->Int inhibition, GABA decay
  (20-25 ms), residual interneuron depolarisation (89 and 93 stay at -41 to -57 mV) and burst lengthening when inhibition is removed.
* E2 can make things worse: less self-inhibition gives longer bursts and more 89 spikes.
* The search minimised a model quantity; the annealing optimum is not guaranteed global, and the groups sit at model thresholds.

Robust success: every memory 4/4 non-cue within 10 ms of its cue; no cross-talk; no non-member pyramidal spikes; all activity
ends <= 100 ms after the first cue; at least one interneuron spike per recall; in all 4 runs; at both Dt 1 ms and Dt 0.1 ms.
Partial success: the same at Dt 1 ms only. A fix that completes all memories but leaves a burst running is a failure.
