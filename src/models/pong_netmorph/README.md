# pong_netmorph (step 1: hand-wired controller, step 2: Netmorph growth)

A spiking LIFC network, simulated in BrainGenix NES, that plays Pong in a closed
loop. Weights are written directly from a spec ("weight-space programming"); there
is no training. Step 2 will grow this topology with Netmorph (BallY -> Hidden ->
Up/Down regions) and tune weights afterwards.

## Files
- `pong_env.py`: pure-Python deterministic Pong, `random_policy`, `oracle_policy`.
- `test_pong_env.py`: pytest for the env (no NES).
- `nes_loop.py`: `ClosedLoop` helper: fast `RunFor` + 2 ms status polling,
  new-spike slicing (GetSpikeTimes returns the whole history), latency stats.
- `pong_handwired.py`: builds the network, `-Mode truthtable|play`.
- `Run.sh`: wrapper (`-H host -P port`, default localhost:8000).

## Architecture (N = 8 bins, y up, bin = floor(y*N))

    B_i (ball place cell) --AMPA--> U_i, D_i
    P_j (paddle place cell) --GABA--> U_i for all j >= i
                            --GABA--> D_i for all j <= i
    U_i --AMPA--> UP        D_i --AMPA--> DOWN
    action per tick = sign(new UP spikes - new DOWN spikes)

U_i fires iff ball in bin i and paddle strictly below (j < i). D_i fires iff ball
in bin i and paddle strictly above. Equal bins silence both. B/P are driven only by
`SetSpecificAPTimes`: a 3-spike burst (2 ms apart); paddle burst at tick+1 ms, ball
burst at tick+3 ms, so inhibition arrives first. 34 neurons, 104 receptors.

## Final parameters
| Connection | Receptor | g_peak (nS) | weight | rise/decay (ms) |
|---|---|---|---|---|
| B_i -> U_i, D_i | AMPA (E=0) | 10 | 1.0 | 0.5 / 3 |
| P_j -> U_i, D_i | GABA (E=-70) | 60 | 1.0 | 0.5 / 6 |
| U_i -> UP, D_i -> DOWN | AMPA | 20 | 1.0 | 0.5 / 3 |

Neurons: Vrest -70, Vreset -55, Vth -50 mV, R 100 MOhm, C 100 pF, 2 ms refractory,
ExpEulerCm, no sAHP/ADP/fAHP/adaptive threshold. See comments in `pong_handwired.py`.

## NES gotchas found while calibrating
- `AdaptiveThresholdFloor_mV = 0` is a 0 mV floor in practice (the comment in the
  reference scripts says "0 means not applied" but the cell never spikes). Set it to Vth.
- `ResetMethod='ToVm'` resets Vm to exactly the threshold, so a driven cell refires every
  refractory period and keeps firing after the input ends. `'Onset'` fixes it.
- fAHP (30 ms decay) carried over between 20 ms ticks and made the second consecutive
  response in the same bin fail; fAHP is zeroed. Inhibition needs to be strong (shunting 60 nS).
- GetSpikeTimes format: `{"SpikeTimes": {id: {"tSpike_ms": [...]}}}` or `None` when empty.
- Ticks run as `RunFor(20 ms, dt 1 ms)`; AP times must be integer-ms to land on the grid.

## Run
    # 8000 is the repo-wide default port (Run.sh default, as in the other models).
    # On ccfbgworkserver01 the dev stack for this work is on 8100, hence -P 8100.
    # The worktree has no venv: point PYTHON at the shared one.
    export PYTHON=~/BrainGenix/BrainEmulationChallenge/venv/bin/python
    ./Run.sh -P 8100 -m truthtable            # add -S 20 for 20 ms combo spacing
    ./Run.sh -P 8100 -m play -t 1000 -s 1 -O output
    python3 -m pytest test_pong_env.py
Results JSON goes to `output/` (gitignored).

## Results (private stack, localhost:8100)
- Truth table: 64/64 correct at 100 ms and at 20 ms combo spacing (UP iff ball>paddle,
  DOWN iff ball<paddle, silent iff equal).
- Play, 1000 ticks, tick 20 ms:

| Seed | Network hit rate | Random | Oracle | Net-vs-bin-rule action mismatches | ms/tick mean / p95 |
|---|---|---|---|---|---|
| 1 | 60/60 = 1.00 | 0.233 | 1.00 | 0 | 35.3 / 45.7 |
| 2 | 56/60 = 0.93 | 0.283 | 1.00 | 0 | 35.3 / 45.7 |

## Known limits
- Network matches the bin rule on every tick; the seed-2 misses come from 8-bin
  quantisation (deadband at equal bins, paddle speed 0.08 vs bin width 0.125), not from
  the network. The oracle uses continuous positions.
- ms/tick grows with history (about 27 ms at 100 ticks, 35 ms at 1000): GetSpikeTimes
  returns the whole spike history each call. Time is dominated by HTTP round trips.
- Only 60 hit/miss events per 1000 ticks, so hit rates have wide error bars.

# Step 2: Netmorph growth

Question: how much of a working controller comes from Netmorph's spatial layout plus chemical
attraction alone, and how much from writing weights afterwards? Short answer on this stack:
growth reproduces the stage structure and almost every intended edge, but also ~5x as many
unintended pairs, and the controller only appears after post-hoc weight writing, and then only
partly (42/64 truth table vs 64/64 hand-wired).

## Files (step 2)
- `pong_spec.py`: step-1 wiring as data (`edges()`), role names, soma layout.
- `pong_netmorph_config.py`: generates `nesvbp-pong` (physics/growth/synapse blocks copied from
  `xor_scnm/nesvbp-xor-res-sep-targets`; regions and attraction block generated).
  `nesvbp-pong` in git = the final config (variant edge, pyramidal paddle cells, D_synmax 4).
- `pong_netmorph_grow.py`: grow + `ModelSave` + `output/<model>_connectome.json`.
- `pong_netmorph_analyze.py`: wiring fidelity table (`-Effective` = ignore pairs tuned to zero).
- `pong_netmorph_tune.py`: tuning recipe on the existing pairs (+ optional per-cell calibration).
- `pong_handwired.py -Model <name>`: loads a grown/tuned model, maps roles, same truthtable/play
  (`Run.sh -M <name>`). Step-1 behaviour unchanged (truth table re-run: 64/64).

## Config design
- Every role is its own one-neuron region named after the role (34 regions). Netmorph has no
  per-neuron coordinates, so this is the way to place a specific neuron at a chosen spot and to
  read its identity back from `GetAbstractConnectome()['Regions']` (no ID guessing).
- Layout: x = stage (B/P 0, U/D 300, UP/DOWN 600 um), y = 50 um * bin, z = -250 / -450. All z < 0:
  the `pia` boundary is a 50 mm sphere whose top is at z = 0.
- Steering: `detailed_chemical_factors`, `neuron_specific_attraction_switch`,
  `single_attractor_per_growthcone`. Variant `edge`: one chemical per intended edge (post neuron
  emits it, pre neuron is attracted to it). Variant `class`: one chemical per postsynaptic class
  (NGF_U, NGF_D, NGF_UP, NGF_DOWN), no per-edge information. Note `edge` is the wiring spec encoded
  as chemistry, so it is the generous case for "configuration alone".
- Cell types: P cells as interneurons => GABA synapses (the step-1 spec); as pyramidal => AMPA.
  Netmorph defaults: pyramidal->pyramidal AMPA + 0.4 NMDA, interneuron->any GABA only.
- Growth: 20 days, dt 100, seed 20241104. 90-111 s per growth on the private stack.

## NES facts that shaped step 2 (verified in NES source and by experiment)
1. `BatchSetPrePostStrength`/`SetPrePostStrength` only write the first AMPA receptor of a pair
   (`LIFCNeuron::UpdatePrePostStrength`). A GABA-only pair cannot be set (it can be zeroed: the call
   returns an error but clears the weight). Grown GABA stays at ~0.5 nS effective (Netmorph gives
   0.2 weight, ~0.8 nS/receptor) against the 60 nS shunting inhibition step 1 needs.
2. The conductance of a pair is `min(g_peak_sum, weight*g_peak_sum*g_norm)`: strength can never
   exceed the grown `g_peak_sum` (about 1 nS per synapse). Synapse count caps strength. With
   D_synmax 2 many B->U pairs had 1-8 nS; with 4 they have 8-26 nS (still 1-2 nS for some P->U/D).
3. `ModelSave` stores the receptor structs as Netmorph built them, NOT edited strengths: reloading a
   "-tuned" model gives back the grown weights (checked). Here a tuned model = grown model + a recipe
   file (`output/<tuned>_recipe.json`) that `pong_handwired -Model` re-applies after `ModelLoad`.
   (xor_scnm's `-tuned` save has the same issue.)
4. Grown neurons use the Netmorph default LIFC parameters (ToVm reset, fAHP 3 nS, adaptive threshold
   with floor +1 mV/spike, 500 ms recovery); `LIFC/Edit` can only change Vrest/Vreset/Vth/R/C/
   refractory/spike depol. History dependence therefore cannot be removed as in step 1: the same
   tuned model scores 42/64 at 100 ms spacing and 54/64 at 600 ms.
5. `Client.LoadSimulation` has a bug (`Response` undefined), not used.

## Wiring fidelity (neuron-pair level, intended = 88 edges for the AMPA variant, 104 for GABA)
| Growth | Config | pairs present | intended present | unintended | precision | recall |
|---|---|---|---|---|---|---|
| G1 | edge, P=interneuron, D_synmax 2 | 350 | 101/104 | 249 | 0.29 | 0.97 |
| G2 | edge, P=pyramidal, D_synmax 4 | 526 | 85/88 | 441 | 0.16 | 0.97 |
| G3 | class, P=pyramidal, D_synmax 4 | 572 | 85/88 | 487 | 0.15 | 0.97 |
| G4 | edge, P=pyramidal, D_synmax 3, y step 120 | 295 | 65/88 | 230 | 0.22 | 0.74 |

G2 per class (intended/present/missing): B->U 8/8/0, B->D 8/8/0, P->U 28/25/3 (P2->U6, P5->U7,
P6->U7), P->D 28/28/0, U->UP 8/8/0, D->DOWN 8/8/0. No wrong-sign intended pairs. Unintended pairs are
mostly forward wrong-index (B_i->U_m, B_i->D_m: 96 of 112 possible) plus recurrent U->U, D->D, U->D,
P->P, B->B, B->P (axons of neighbouring cells overlap dendrites at 50 um pitch).
Reading: at 50 um pitch the graph between adjacent stages is nearly complete, so recall comes from
density, not chemistry: `edge` (G2) and `class` (G3, no per-edge information) have identical recall.
Stretching the layout (G4) removes some unintended pairs but loses the long intended edges first
(P->U/D 0.61/0.68). Index specificity did not emerge at any setting tried. An all-to-all-ish feed
forward graph with the right stages is what spatial layout alone gives.

## Results (500 ticks play, seeds 1 and 2; truth table at 100 ms spacing; private stack :8100)
| Model | truth table | play seed 1 (hit rate) | play seed 2 | random seed 1 / 2 |
|---|---|---|---|---|
| hand-wired (step 1) | 64/64 | 30/30 = 1.00 | 28/31 = 0.90 | 0.23 / 0.36 |
| grown, untuned (G2) | 10/64 | 12/30 = 0.40 | 10/31 = 0.32 | |
| grown + tuned (G2, calibrated, `johnjose-pong-tuned`) | 42/64 | 14/30 = 0.47 | 16/31 = 0.52 | |
| G3 (class chemistry) tuned the same way | 40/64 | not run | not run | |
| G4 (sparser) tuned the same way | 20/64 | not run | not run | |
| G1 (GABA paddle), tuned, intended GABA left at grown strength | 10/64 | not run | not run | |
Untuned truth table 10/64 is the 8 diagonal (silent) cells plus 2; the untuned play rate is at chance.

What "tuned" is for G2 (`pong_netmorph_tune.py -Calibrate -Rm 600`): all 441 unintended pairs set
to 0 (post-hoc pruning); each comparator cell U_i/D_i gets one input scale k_i (B_i and the P_j
pairs set to min(k_i, g_peak_sum)), chosen from 8 B-alone, 8 P-alone and 64 B+P probe runs per k
(score: silent on B alone and P alone, spikes on B+P for each existing intended P_j); U->UP and
D->DOWN set to 20 nS (capped by g_peak_sum); UP/DOWN membrane resistance raised to 600 MOhm via
`LIFC/Edit` (their inputs are 2-20 nS, a single comparator spike did not fire them). The excitatory
coincidence design replaces step 1's inhibition because of fact 1. The Rm edit is a neuron edit, not
a weight edit; without it the same calibration reaches 28/64.

## Conclusions
- Growth alone (no weight writing): 10/64, chance-level play. Netmorph delivered the topology's
  stages and nearly all intended edges, but with ~5x unintended pairs and Netmorph-default weights.
- Weight writing carries the result: pruning the unintended pairs and calibrating strengths took it
  to 42/64 and play 0.47-0.52 (random 0.23-0.36), still far from 64/64 and 0.9-1.0.
- Chemical specificity bought nothing measurable at 50 um pitch (G2 vs G3). Density of overlap
  decided connectivity.
- Remaining failure modes: (a) history dependence of default LIFC neurons (adaptive threshold, fAHP)
  at 20-100 ms spacing, since 54/64 at 600 ms; (b) per-cell calibration cannot separate B-alone from
  B+P where grown g_peak_sum is 1-2 nS; (c) 3 missing P->U edges, which tuning cannot restore;
  (d) the paddle inhibition of step 1 is not reproducible (fact 1).

## Open problems and next ideas
- NES: let strength setters reach GABA receptors and honour weights above `g_peak_sum`; persist
  edited weights in `ModelSave`; allow LIFC Edit of ResetMethod/fAHP/adaptive threshold. Each removes
  one limitation above. Question for whoever owns Netmorph: can a region be told to attract a
  single specific neuron index so index specificity would not depend on spacing?
- Growth: widen D_synmax only for selected type pairs, shorten dendrites, or use a 3D layout where
  index specificity comes from distance (bins on a line, 150+ um apart, with a stage gap < 600 um).
- Tuning: calibrate with the same spacing and ordering as play; add per-pair (not per-cell) scales;
  search over Rm for U/D cells too.
- Only 30 hit/miss events per 500 ticks: hit rates have wide error bars.
