# weightspace_log.md: phase 2 spiking controller, every parameter and where it came from

No search, no tuning loop. "derived" = a formula in `dp_derive.py` (numbers below are its
output, stored in `weights_recipe_derived.json`). "hand adjustment" = a reasoned single change.
There is one numerical hand adjustment (A1, a calibration of the decoder constant). Several structural
and sizing choices were also made by measurement or by judgement, not by formula; they are listed under
"Choices not derived" below. The weights themselves never changed after derivation. Everything was
measured on the Python stand-in only, with sensor noise off (the controller sees the exact state, as
the LQR baseline does).

## Derived (formula and numbers)
| Parameter | Value | Source |
|---|---|---|
| K (plain 10 ms DLQR, 1x6) | 4.26, -144.5, 178.2, 6.51, -2.21, 22.3 | `dlqr(ctrl_dt=0.01)`; |K| spans 80x |
| state peak (LQR 10 ms, delay 1, disturbance, 180 s, stats seed 100) | 0.213, 0.111, 0.068, 0.661, 1.070, 0.496 | closed-loop run; peak/sigma 3.3 to 8.7 (kicks give heavy tails) |
| sigma_i | 0.0639, 0.0218, 0.0147, 0.1223, 0.1231, 0.0591 | same run |
| K_i sigma_i (N) | 0.27, 3.15, 2.62, 0.80, 0.27, 1.32 | spread 11.6x, not 80x |
| range_i = 1.25 x peak_i | 0.266, 0.139, 0.085, 0.826, 1.337, 0.619 | encoder never leaves [0, 2 r0] on the stats seed |
| K_i range_i (N) | 1.13, 20.0, 15.1, 5.38, 2.96, 13.8 | spread 17.7x |
| r0 | 150 Hz | input rates 0..300 Hz (integer-ms grid, regular) |
| g_i = r0/range_i (Hz per unit) | 563, 1082, 1771, 182, 112, 242 | encoder gain; this absorbs the 40x+ of K into the per-variable ranges |
| neuron | Vrest -70, Vreset -55, Vth -50 mV, R 100 MOhm, C 100 pF, 2 ms refr., AMPA E 0, decay 3 ms | Pong step-1 clean LIFC |
| operating point Ge0 | 5.793 nS, nu0 = 166.7 Hz | nu(Ge0) = half the refractory-limited max 1/(t_ref+dt) = 333 Hz, closed-form mean-field rate |
| S = d nu/dG at Ge0 | 47.76 Hz/nS | central difference of the closed form |
| tau_e (discrete integral of one unit synaptic conductance) | 3.528 ms | dt/(1-exp(-dt/tau_s)) |
| C = sum K_i range_i / (2 S Ge0) | 0.1056 N/Hz | force per Hz of push-minus-pull rate per neuron; follows from "baseline conductance of the signal populations = Ge0", no bias population |
| w_i k_i = share_i Ge0/(r0 tau_e) (nS) | 0.213, 3.75, 2.83, 1.01, 0.55, 2.59 | share_i = K_i range_i / sum |
| k_i = ceil(w_i k_i / 2 nS) | 1, 2, 2, 1, 1, 2 | synapses per output neuron per state |
| w_i (nS) | 0.213, 1.88, 1.41, 1.01, 0.554, 1.30 | all <= 2 nS |
| routing | K>0: pos -> pull, neg -> push; K<0 swapped | s>0 with K>0 must give negative force; AMPA only, one side per population |
| n_out per side = 2 v (C/(T sigma))^2 | 111 | v = 0.031 spikes^2 per neuron, MEASURED once on a first oversized build (n_out 595, zero-state force sd 0.108 N); sigma target 0.25 N |
| c = C/(n_out T) before A1 | 0.0951 N/spike | decoder |
| n_in | 256 per population | sized by experience from the zero-state noise (not a formula), see "failures" |

### How the gain range is handled
|K_i| spans 80x (2.2 to 178) but K_i sigma_i only 11.6x and K_i range_i 17.7x. The per-variable
encoder gain g_i = r0/range_i puts every input population over the same 0..2 r0 range at its own
peak; the weight then carries only K_i range_i, so w_i k_i is proportional to K_i range_i (0.2 to
3.8 nS) instead of K_i (80x). The rest is population size: no weight is scaled up, synapse counts
k_i are 1 or 2, and the largest weight is 1.88 nS against a 2 nS self-imposed cap (see cap below).

### Cap
Per-synapse conductance <= 2 nS. Reference limits from Pong: step-1 clean LIFC used 10 nS (B->U,D) and
20 nS (U->UP); grown pairs are capped by `min(g_peak_sum, ...)` (about 1 nS per synapse, 8-26 nS per pair at
D_synmax 4). A pair here is one receptor of weight w_i, so 1.9 nS is within the D_synmax-4 range but above a
typical 1 nS grown synapse. Wanting to stay near 1 nS needs about twice the receptors (about 4000).

## Derived net: where it failed, before any adjustment (honest)
1. First build (n_in 32, random fan-out): zero-state force sd 0.8 N, static-state force errors 20-30%. Causes
   (found by measuring, not by search): (a) input population count quantisation (random phases
   gave sqrt(n_in) spike noise on a baseline of r0 per population; fixed by stratified phases,
   which is a codec change, not a weight change); (b) random fan-out made some input neurons drive
   several more output cells than others, a fixed ripple; fixed by balanced fan-out
   (consecutive entries of a seeded permutation); (c) n_in 32 -> 64 -> 256 for the residual quantisation
   (1 spike out of n_in r0 T on every population's baseline). These are encoder/connectivity structure,
   all before the weights were calibrated; the weights themselves never changed.
2. With those in place the derived weights give static-state force with regression slope 1.113
   (measured/derived, n 40 random states ~ N(0, (0.5 sigma)^2), 40 ticks each), RMSE 0.35 N. So the
   derived gain is 11% high. Cause: S comes from a continuous closed form; the stand-in steps at 1 ms
   with a 1-step synaptic delay and regular input, which is slightly steeper.
3. Latency (measured, step response): the net answers within the first window; the 2-tick
   ripple of the output counts (neurons phase-lock to the regular input, +-20% of the step) gives an
   extra lag of 0.28 tick over the 1 tick window. Total 1.28 ticks, so the matching delay is 2 ticks.

## Hand adjustment
| id | change | before | after | why | measured effect |
|---|---|---|---|---|---|
| A1 | decoder constant c (N/spike), weights untouched | 0.09510 | 0.08542 (= before / 1.1132) | failure 2: derived slope 11% high | static gain ratio 1.113 -> 1.010 (fresh seed), RMSE 0.35 -> 0.14 N |

A1 is a one-parameter calibration against the target law (regression slope on the built net, seeds 7 and 8),
not a formula. The stated cause (continuous-time S vs the 1 ms stand-in) is plausible but untested.

## Choices not derived (added after independent review)
| item | value | how it was set |
|---|---|---|
| n_in | 32 -> 64 -> 256 per population | raised by measuring zero-state noise (failure 1c); the seeds used for that were not recorded |
| encoder phases | random -> stratified | structural change after measuring noise (failure 1a) |
| fan-out | random -> balanced | structural change after measuring ripple (failure 1b) |
| v | 0.031 spikes^2 per neuron | measured once on an oversized build (n_out 595); consistent: 0.0177 sqrt(1190 v) = 0.108 N |
| design constants | RANGE_MARGIN 1.25, r0 150 Hz, W_MAX 2 nS, noise target 0.25 N, Ge0 at half the refractory cap | judgement, not derived |

The 0.25 N noise target is missed: zero-state force sd is 0.28-0.52 N depending on seed. No eval seed
(0, 1, 2) was used for any calibration: stats seed 100, A1 seeds 7 and 8, connect_seed 12345.

## Force resolution, saturation and size (the add-on constraints)
1. Force quantisation per tick: one net spike = c = 0.0854 N (was 0.2 N in the harness defaults; population of
   111 neurons per side). RMS force is 1.1 N (spiking, delay 1) to 1.5 N (delay 2): 13 to 17 spikes. Count
   noise at zero state (6 states at 0): sd 0.28 to 0.52 N (seed dependent), mean offset about -0.3 N for seed 1
   (fixed random connectivity, 4 spikes).
2. Output capacity: one neuron fires at most 5 spikes per 10 ms (2 ms refractory); with the 1 ms step the
   closed form caps at 333 Hz (3 per window). Operating point 1.67 per neuron per window (mean 186 spikes
   per side per tick, 372 total). Peak force of 13.5 N is a push-pull difference of 158 spikes, which moves
   each side by about 0.7 spikes per neuron, to 2.4 per neuron, under the 3 per neuron cap. The decoder
   clip +-20 N is never the limit; at the alignment extreme the pull side would reach 0 rate and the
   response compresses (the 1 sigma mix measured 1.075 gain against 1.27 at small signal in the pre-A1 build).
3. Size: 3072 input neurons (12 populations x 256, spike sources only), 222 output neurons (2 x 111),
   9 receptors per output neuron, 1998 receptors in total. Pong had 526 grown AMPA pairs; the harness
   quotes 3072 for a 32-neuron group. 1998 is the same order as the harness figure and about 4x Pong's grown
   set; it assumes designed (not grown) connectivity, so see the NES list in README.
4. Routing: excitatory AMPA only, every population feeds exactly one side, force = push - pull.

## Encoder and decoder choice vs the harness (`pend_nes_harness.py`)
The harness encoder is rectified with 8 hat neurons per sign and its decoder takes (n_left, n_right);
`dp_codec.py` keeps that interface shape (`spike_trains(state, steps)`, `decode(n_push, n_pull)`) but
uses a DIFFERENTIAL code (r0 +- g s) because the linearisation about the operating point needs a common
bias for push and pull; the rectified code adds a second-order error whenever two states disagree. Its
scales and demo K were not used (placeholders for the 0.1 kg frictionless plant).

## Phase 3a (NES) hand adjustments

Measured on the NES build of the same network (`dp_nes.py`, private stack 8100). Weights in `weights_recipe.json`
and the encoder are unchanged; only the translation to NES units and the decoder constant differ.

| id | change | before | after | why | measured effect |
|---|---|---|---|---|---|
| U1 (unit conversion, not tuning) | NES receptor `PeakConductance_nS` = 20 (cap, never reached), `Weight` = w_nS x 0.8218 / 20 | w_eff = w_nS | w_eff = 0.8218 w_nS | NES AMPA (rise 0.5, decay 3 ms, peak-normalised) carries 4.29 ms nS per nS of peak; the stand-in's single exponential carries 3.528 ms nS (tau_e). Same charge per input spike. NES clips a pair at `min(PeakConductance, Weight x PeakConductance x gnorm)`, so with Weight 1 (Pong) the pair would saturate at one spike's peak; the large cap avoids that. | w_eff 0.175 to 1.542 nS; no clipping possible (max gnorm x w_eff about 3 nS < 20) |
| A2 | decoder constant c (N/spike), weights untouched | 0.08542 | 0.05052 (= before / 1.6906) | NES net is 1.69x steeper than the derived law, with the stand-in at 1.01 after A1. Cause not isolated (candidates: NES refractory/reset handling, ExpEulerCm update, double-exponential synapse smoothing, 2 ms refractory on a 1 ms grid). Same mechanism as A1: one-parameter regression of measured on target force | seed 7 (24 random states ~ N(0,(0.5 sigma)^2), 2-tick means): slope 1.6906, rmse after slope 0.34 N. Verification with A2 applied, seed 8: slope 0.953, rmse 0.21 N. Zero-state force sd 0.18 N (20 clean ticks), mean -0.18 N |

A2 is a calibration against the target law on the built net, as A1 was; eval seeds 0, 1, 2 were not used. Raw file:
`output/nes_calib_raw_seed7.json`, `output/nes_calib_A2_seed8.json` (gitignored). `DP_NES_C_ADJUST=1` runs the raw net.

NES timing facts that mattered (no design change needed for them): inputs are plain LIFC neurons driven by
`SetSpecificAPTimes` (appends to the neuron's list, absolute times, one spike per update step per neuron);
spikes scheduled at t0+10 ms are recorded in the next window with their own time (effect unchanged, onset delay
1 ms). `GetSpikeTimes` also returns the input sources.
