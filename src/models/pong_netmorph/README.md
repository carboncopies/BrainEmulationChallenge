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

Evidence (verifier): fact 1 `LIFCNeuron.cpp:543-558` (also zeroes the pair's NMDA receptor; the batch
call stops at the first failing pair, `Simulation.cpp:1385-1388`); fact 2 `Neuron.cpp:152-155`; fact 3
`LIFCSaver`, `Simulation.cpp:716-718`, saves `LIFCReceptorBase`, not the edited `LIFCReceptorData` weight;
fact 4 `Structs/Neuron.h:398-406`; fact 5 PythonClient `Client.py:344-347`. `effective_strength_nS` in
recipes now reports min(weight*g_peak, g_peak_sum) (recipes written before this commit store the uncapped value).

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

## Caveats on the numbers
- `calibrate()` picks k from probes that cover all 64 truth-table combinations, so the tuned 42/64 is
  IN-SAMPLE. The play results are the out-of-sample measure and are near chance (0.47 seed 1 vs random
  0.23, 0.52 seed 2 vs random 0.36).
- The headline G2 uses a different design from step 1 (excitatory-coincidence paddle cells, 88-edge
  spec) instead of step 1's GABA inhibition, because of NES fact 1.

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

# Step 3: weight-space programming of the grown model (`johnjose-pong-g2`)

Protocol (https://rikiyat.github.io/blog/weight-space-programming/): read the grown connectome (pairs and
`g_peak_sum` caps), write weights directly from a spec, no optimiser, measure on held-out runs. Files:
`pong_weightspace.py` (solver, recipe writer, evaluation: `solve | truthtable | play | handwired-play | probe | outchar | stats`) and
`weightspace_recipe.json` (the frozen recipe: every grown AMPA pair with its written nS, neuron edits, input encoding).
Replay: `python pong_weightspace.py truthtable -SpacingMs 100` and `play -Seed 101 -Ticks 1000` (loads g2, applies the recipe).
The graded readout `sign(nUP - nDOWN)` is used for the truth table too (the step-1 truth table counts "both fired" as an error).

## Design
Linear comparator through relays: hidden cells U_k/D_k relay the inputs; U relays drive only UP, D relays only DOWN
(that is what exists in g2). Required drive: UP = c*(i + 7-j), DOWN = c*(7-i + j), so UP - DOWN = 2c(i-j) and the tie gives equal counts.
A MILP (scipy `milp`, deterministic, existing pairs only, input->relay cap >= 2.9 nS) picks, per side, relay output weights
w_r <= 0.6*cap, and which inputs drive which relay. Ball and paddle inputs never share a relay (class variable), so both bursts can be
coincident and conductances add at UP/DOWN. An input with no usable pair (UP side: P5 and P6, all caps < 2.9 nS) gets a common-mode
deficit applied to BOTH sides, which keeps UP - DOWN for that input. Everything else (470 of 526 grown AMPA pairs, including all 125 recurrent
hidden->hidden, U0->DOWN, D4->UP) is set to 0; 56 pairs are written non-zero (all differ from the grown value); 18 of 34 neurons get a LIFC/Edit.
Final: c = 1.1 nS/level, input->relay min(cap, 10 nS), burst of 3 input spikes 3 ms apart, ball and paddle at +1 ms (declared in the recipe, same in
every evaluation). Assignment table: `design.relays` in the recipe (relay, output nS, inputs), e.g. UP: U7 4.4 nS <- B6,B7 ... see file.
Neuron edits: used relays R 3000 MOhm, C 0.5 pF, Vrest -53 mV; UP and DOWN identical: R 200 MOhm, C 10 pF.

## Things learned from the diagnostics (NES facts, from source and probes)
- `LIFC/Edit` cannot lower the threshold: Netmorph neurons start with an adaptive-threshold floor at -50 mV that only decays toward Vth. Gaps are set with Vrest.
- The conductance of a pair is `min(g_peak_sum, w*g_peak_sum*g_norm)`, so summed pulses of one pair saturate at the cap.
- Input->relay latency is pair specific (2-8 ms, grown onset delays); weak pairs (<~2 nS) fire a relay late or once for three spikes, strong ones fire at once.
  Hence (a) designs that need relay counts or pulse timing from weak pairs fail, (b) only pairs >= 2.9 nS were used.
- ToVm output cells fire about one spike per relay pulse above a threshold amplitude (forced-relay probe: 2.9 nS 0-1 spike, 5.8 nS 2, >= 8 nS 3, 23 nS 4),
  not a charge-proportional count. The tie drive 7c is therefore placed mid-slope (c = 0.8 -> 51/64, c = 1.1 -> 56/64).
- Floor +1 mV per spike (500 ms recovery) silences UP/DOWN when ticks come every 20 ms.

## Results
Blind (one evaluation, recipe written from the connectome alone, first design: MILP with shared relays, weights up to caps): truth table 40/64, play seed 1 x 500: 11/30 = 0.37 (random 0.23).
Diagnostic: 20 stack runs (play only seed 2): 11 truth tables (10 at 100 ms, 1 at 20 ms), 7 single-input probes, 1 forced-relay output probe, 1 play run;
every edit a hand edit (list above and `output/weightspace_log.md`, gitignored). Key edits: gap via Vrest instead of Vth; relay equalisation attempt (all inputs 0.95 nS, abandoned: relays then fire once at scattered latencies);
output stage R/C; disjoint ball/paddle relays + coincident bursts; strong pairs only (gmin 2.9) with L1-error MILP; common-mode deficit shift; c = 0.8 -> 1.1.
Forward-pass budget before the final: 2 blind evaluations (truth table + 500-tick play) + 20 diagnostic runs = 11 x 64 truth-table presentations + 7 x 16 single-input probes + 1 forced-relay probe + 500 closed-loop ticks, i.e. about 1.5k simulated ticks of 20-100 ms; no gradient or search loop.

Final (recipe frozen, held-out seeds 101-103 x 1000 ticks, private stack :8100):
| Model | truth table 100 ms | truth table 20 ms | play 101 | play 102 | play 103 | mean |
|---|---|---|---|---|---|---|
| hand-wired (step 1) | 64/64 | 64/64 | 0.983 | 0.933 | 0.950 | 0.955 |
| step 2 tuned (g2-cal-rm600) | 42/64 (in-sample) | not run | 0.466 | 0.450 | 0.583 | 0.500 |
| step 3 weight-space (g2) | 56/64 | 35/64 | 0.362 | 0.400 | 0.467 | 0.410 |
| random | | | 0.310 | 0.283 | 0.333 | 0.309 |

Edited: of 526 grown AMPA pairs, 56 (10.6%) written non-zero (all changed from grown), 470 (89.4%) zeroed (100% of pairs touched, 34-neuron net, 18 neurons edited).

## Conclusions
- Target not met: mean held-out play 0.41 (target 0.85), truth table 56/64 at 100 ms (target 60/64). Step 3 is slightly above random and below the step-2 tuned model in closed loop.
- The linear-comparator spec is sound (the 100 ms truth table went 40 -> 56/64 with reasoned edits, errors only at |i-j| = 1), but g2's default neuron dynamics defeat it:
  at 20 ms spacing the adaptive-threshold floor silences UP/DOWN (35/64, mostly 0/0), which is also why play (661/1000 ticks differ from the bin rule) is poor.
  The same weights on step-1 neurons (no adaptation) are the hand-wired net.
- What would likely fix it: NES edit of ResetMethod/adaptive floor/fAHP (limit C4), GABA strength setters (C1) for real inhibition instead of a conductance-sum, and
  persisted edits in ModelSave (C3). With those, the MILP spec above should transfer; without them the 20 ms regime is not reachable by weights alone.
- Honest caveat: 20 diagnostic runs used the 64-combination truth table (100 ms) as the main signal, so 56/64 is in-sample; the play numbers are the held-out measure.

## Step 3b: tick length

Hypothesis: grown neurons keep a Netmorph adaptive-threshold floor (+1 mV per spike, ~500 ms recovery) that NES cannot edit, so decisions
every 20 ms of sim time accumulate it. If each game tick simulates more time (`-TickMs`, default 20; one `env.step` per tick, input bursts at the
start of each tick, readout = new UP/DOWN spikes over the whole tick), neurons recover between decisions. This is an encoding/timing change only.
**The weights did not change: `weightspace_recipe.json` is the frozen step-3 recipe in every run below.**

Dev runs (seed 1, 500 ticks unless noted; action_mismatches counts ticks differing from the sign(ball bin - paddle bin) rule):
| TickMs | hit rate | action_mismatches /500 | wall ms/tick |
|---|---|---|---|
| 20 (seed 1) | 0.367 | 327 | 64 |
| 20 (seed 2) | 0.452 | 304 | 61 |
| 100 | 0.433 | 357 | 88 |
| 200 | 0.400 | 336 | 105 |
| 300 | 0.367 | 324 | 131 |

(Hit rates are over only ~30 episodes per run, so differences of 0.05 to 0.1 are noise.) Longer ticks did not reduce mismatches at all, so no tick length
was better than another. 100 ms was kept for the final as the smallest value that matches the 100 ms truth-table regime (56/64). Wall clock per tick
grows with tick length (about 0.35 ms per simulated ms on top of ~55 ms fixed), so it is not free.

Final (seeds 201-203 x 1000 ticks, same stack, held out from the dev seeds):
| Model | play 201 | play 202 | play 203 | mean | mismatches (of 1000) | ms/tick |
|---|---|---|---|---|---|---|
| hand-wired, 100 ms ticks | 0.966 | 0.949 | 0.932 | 0.949 | 0, 0, 0 | 43 |
| step 3, 20 ms ticks | 0.492 | 0.475 | 0.339 | 0.435 | 656, 635, 637 | 66 |
| step 3, 100 ms ticks | 0.305 | 0.407 | 0.356 | 0.356 | 700, 731, 725 | 89 |
| random | 0.322 | 0.153 | 0.271 | 0.249 | | |

Truth table at SpacingMs 100: 56/64 (unchanged from step 3).

Conclusion: the hypothesis is not supported. Tick length 20 to 300 ms did not improve closed-loop play of the step-3 weights; 100 ms was
no better than 20 ms (0.356 vs 0.435 mean, within noise and, if anything, worse). The truth table is 56/64 at 100 ms, yet play mismatches
the bin rule on about 70% of ticks, so the adaptive-threshold floor accumulating across 20 ms ticks is not the main cause of the poor play.
Not diagnosed here. Candidates to check next: errors at |ball - paddle| = 1 and ties, which dominate real game states (truth-table errors sit exactly there),
and state carried over between ticks (relay recovery, residual UP/DOWN charge) that the isolated-row truth table does not exercise.

## Step 3c: diagnosing play

Recipe unchanged (frozen). Added only diagnostics: `play` writes a per-tick trace (`output/ws_play_trace_s<seed>.json`: b, p, nUP, nDOWN, action, expected, t0, spike times
relative to t0, sim time after the tick), plus modes `shuffled` (64 combos in a fixed random order, `-Seed`) and `replay` (the play trace's (b,p) sequence run open-loop as a truth-table-style schedule).
All on the private stack :8100. Play seed 3, 300 ticks, TickMs 100: hit rate 0.556 (10/18), 163/300 ticks differ from the bin rule (random 0.333).

- H4 (bug in the play path): not supported. Every UP/DOWN spike falls 5-14 ms after its tick start (inside the tick); `t0` steps exactly 100 ms and sim time after each tick equals t0 + 100;
  no scheduled time is below the current sim time; a second play run gave an identical trace; and the open-loop replay of the same (b,p) sequence with the truth-table code path
  reproduced all 300 per-tick (nUP, nDOWN) pairs exactly (137/300 correct = 163 mismatches). Play and truth table read out identically, so the difference is in the inputs' sequence, not the code.
- H1 (distribution): partly. |i-j| histogram in play: 0: 84, 1: 122, 2: 37, 3: 18, 4: 16, 5: 13, 6: 10 (69% of ticks at |i-j| <= 1; the truth table has 22/64 = 34% there). Mismatch rate by i-j:
  -1: 0.53, 0: 0.65, +1: 0.28, |i-j| = 2: 0.15 (down) / 0.62 (up), i-j >= 3: 0.73-0.89 (n = 49). If every play tick took the action the truth table gave for its own (b,p) cell, 113/300 would mismatch (38%), so the distribution accounts for about 113 of the 163.
- H2 (history/order): supported, and it is the larger remaining effect. Truth table, same weights: smooth ball-major order 56/64, fixed shuffled order (seed 7) 52/64. The play sequence replayed open-loop: 137/300 at 100 ms spacing and 110/300 at 500 ms
  (131 of the 190 mismatches at |i-j| <= 1 but 59 of 94 ticks at |i-j| >= 2 wrong, where the truth table is 26/26 right). The truth table at 500 ms is still 56/64, so spacing alone is not the cause and a 500 ms recovery time does not remove it.
  In play 27 of 37 repeated cells gave different (nUP, nDOWN) on different visits. Largest cell shifts: (b, p=1) is UP-driven 2 to 3 net spikes in the truth table but 0 to 0.6 in play (n = 9-13 each);
  mismatch is 0.69 when the paddle bin is unchanged from the previous tick vs 0.39 when it changed. The slow state is probably the repeated-input adaptive floor of the same relays (not isolated here).
- H3 (UP/DOWN bias): mostly not. Play actions: UP 84, DOWN 91, 0 125 against expected 120, 96, 84; 54 ticks are 0/0. The error is a surplus of 0 (net too weak), not a sign bias, but it makes the paddle stick: paddle bin 1 holds 105 of 300 ticks (82% mismatch there, 61 zero actions),
  because (b,1) cells go quiet after repeated visits. P5/P6 UP-drive deficit is not visible as a separate effect (mismatch 0.42 and 0.27 there).

Conclusion: the 56/64 truth table is a smooth-order, once-per-cell measurement; play dwells at |i-j| <= 1 and repeats the same cells, and carried state (time scale longer than 500 ms) weakens the output, so the programmed weights do not transfer. Future calibration should use shuffled/repeated schedules (and play-order) rather than the ordered 64-cell table.

# Step 4: connectome transplant (`pong_transplant.py`, `transplant_recipe.json`)

Why: step 3 wrote a linear comparator onto the grown g2 network and play stayed near random (held-out 0.36-0.44), while the same
weights on step-1 neurons are the hand-wired net. Step 3c located the failure in slow state carried across ticks. The cause is in NES, not in
growth: `struct LIFCNeuronPars` in `BrainGenix-NES/Source/Core/Netmorph/NetmorphManagerThread.cpp` (~lines 588-640 at NES master) gives every grown LIFC neuron hardcoded defaults (ToVm reset,
fAHP 3 nS, sAHP 300 ms decay, ADP with 300 ms recovery and depletion, fatigue 1000 ms recovery, adaptive threshold with a floor that rises 1 mV per spike
and recovers over 500 ms). They do not come from the Netmorph config and `LIFC/Edit` cannot change them. Step 4 therefore keeps everything Netmorph grew
about connectivity and replaces only the neuron dynamics model.

## Transplant rule
Built from `output/johnjose-pong-g2_connectome.json` (index = presynaptic id, `ConnectionTargets[pre]` = posts, types 1 AMPA, 2 GABA, 3 NMDA as in
`pong_netmorph_analyze.py`; g2 has 526 AMPA pairs and 505 NMDA receptor entries on the same pairs, no GABA):
1. A fresh simulation with the same 34 roles (`Regions` map), somata as spheres at the grown `SomaPositions`, step-1 clean LIFC neurons
   (Onset reset, no fAHP/sAHP/ADP/fatigue/adaptive threshold).
2. A receptor is built ONLY for a (pre, post) pair that exists in the grown connectome, ONLY of a type that grew for that pair, with conductance <= the
   grown cap of that pair and type (sum of `ConnectionGPeakSum` over the pair's receptors of that type). `build()` asserts this for every receptor.
3. Pairs not used are not built (== zeroed). NMDA is not used.
Topology and strength limits are grown; weights, neuron dynamics, receptor kinetics (rise 0.5 / decay 3 ms) and onset delay (1 ms; grown delays are
not in the connectome JSON) are written. Stated limit: this is not the grown neuron, it is the grown wiring diagram with step-1-class neurons.

## Design (written blind, from the connectome only)
Same linear comparator as step 3: relays U_k/D_k (the only pairs into UP/DOWN are U->UP and D->DOWN), UP drive = c(i + 7 - j), DOWN drive = c(7 - i + j),
ball and paddle relays disjoint. The step-3 MILP is adapted (`solve_side`): relay output weight w_r <= cap(r, out), input->relay pairs need cap >= 0.97 nS,
c is a MILP variable, then the max drive error is minimised at a fixed c. c = 2 nS/level was chosen (exact solution, zero drive error on both sides;
the largest c with <= 12% error was 5.4, not used). What clean neurons change:
- Relays are one neuron parameter set for all 16 hidden cells: R 1000 MOhm, C 3 pF (g_L 1 nS, tau 3 ms), Vrest/Vreset/Vth -70/-55/-50. High R makes the
  weakest grown synapses (0.98 nS, one synapse) fire a relay per input spike; every input pair is written at 0.97 nS (identical for all inputs, so relays respond
  identically). The old 2.9 nS cut is gone, which is what makes the UP-side paddle inputs P5, P6 deliverable without step 3's common-mode shift.
- With weight 1 a receptor clamps at its peak (`Update_Conductance`, `min(g_peak_sum, ...)`), so a relay firing every 2 ms gives a plateau conductance = w_r at the output. The output
  is a threshold element: UP and DOWN are one identical parameter set, g_L = 7.4c/0.4 (R 27 MOhm, C 74 pF, tau 2 ms), so V_ss crosses Vth at G = 7.4c. Tie drive 7c < 7.4c < 8c: at a tie nothing
  fires on either side (UP = DOWN = 0 exactly), a win fires one side only. The readout stays sign(new UP spikes - new DOWN spikes).
- Encoding: 3-spike bursts 3 ms apart, ball and paddle both at +1 ms.
- Before the stack: an offline model of the NES update rule (ExpEulerCm, g_norm, clamp; written from the source, not fitted to any stack data) predicted 64/64 at 100 and 20 ms,
  including a shuffled order.
Assignment (relay: output nS <- inputs; full table with caps in `design.relays`): UP: U0 2 <- B1; U1 2 <- P1,P4,P6; U2 6 <- B3,B5,B7; U3 10 <- P0,P1,P2; U4 4 <- P0,P4,P5;
U5 8 <- B4,B6,B7; U6 4 <- B2,B5,B6; U7 8 <- P3. DOWN: D0 10 <- B0,B1,B2; D1 6 <- P3,P5,P7; D2 8 <- P4,P6,P7; D3 4 <- B0,B5; D4 4 <- P2,P5,P6; D5 6 <- B3,B4;
D6 2 <- B1,B3,B6; D7 2 <- P1. 56 receptors: 10 B->U, 10 B->D, 10 P->U, 10 P->D, 8 U->UP, 8 D->DOWN (mean written/cap 0.34).

## Blind result (one evaluation, private stack :8100)
Truth table 64/64 at 100 ms and 64/64 at 20 ms; play seed 1 x 500 at 20 ms tick: 30/30 = 1.00 (0 mismatches against the bin rule; random 0.233).
It matched the offline prediction cell for cell.

## Diagnostics
4 stack runs (limit 12), seeds 2 and 5 only for play, no recipe edits (none were needed): shuffled truth table at 20 ms, orders seed 7 and 9: 64/64 and 64/64;
play seed 2 x 1000: 56/60 = 0.933 (random 0.283); play seed 5 x 1000: 59/61 = 0.967 (random 0.164); 0 mismatches against the bin rule in both. Log: `output/transplant_log.md` (gitignored).

## Final (recipe frozen, unchanged since the blind run; seeds 301-303 x 1000 ticks at 20 ms tick)
Truth table: 64/64 at 100 ms, 64/64 at 20 ms, 64/64 shuffled at 20 ms (order seed 11).

| Model | play 301 | play 302 | play 303 | mean | mismatches vs bin rule | ms/tick (mean) |
|---|---|---|---|---|---|---|
| hand-wired (step 1) | 0.967 | 0.984 | 0.983 | 0.978 | 0, 0, 0 | 39.5 |
| step 3 weight-space on grown neurons | 0.450 | 0.475 | 0.407 | 0.444 | 628, 617, 632 | 67.4 |
| step 4 transplant | 0.967 | 0.984 | 0.983 | 0.978 | 0, 0, 0 | 67.4 |
| random | 0.200 | 0.180 | 0.237 | 0.206 | | |

Independent verifier (seeds 401/402 x 1000): 0.935 / 0.966; shuffled truth table seed 23: 64/64; 0 transplant-rule violations over all 56 receptors.
Hand-wired truth table re-run at the end: 64/64 at 100 ms and 20 ms (step 1 unchanged). Pairs used: 56 of 526 grown AMPA pairs (10.6%); 470 (89.4%) not built.
All 34 neurons are replaced. Hand-wired and transplant hit rates are identical because both follow the bin rule on every tick (the misses are 8-bin quantisation, as in step 1).
The transplant costs 67 ms/tick against 39 ms for the hand-wired net, the same as step 3 on grown neurons (cause not investigated; likely the larger spike history returned by GetSpikeTimes).

## Conclusions
- Target met: mean held-out play 0.978 (>= 0.85), truth table 64/64 at 20 ms (>= 60/64). The step-3 specification and solver were not at fault; the hardcoded neuron defaults were.
  Same grown topology and caps, same kind of MILP assignment: 0.444 -> 0.978.
- What Netmorph contributed: which pairs exist and their strength limits (enough for a full comparator through relays, using 10.6% of the grown pairs) and the soma layout.
  What was written: every weight, the neuron model, kinetics, delays. Index specificity still did not come from growth (step 2).
- Caveats: AMPA-only comparator (g2), no inhibition, a threshold-at-7.4c output instead of step 1's GABA veto; relay and output cells use non-default R/C (one set per class, listed in the recipe);
  the offline model and the blind run agreed exactly, so the diagnostic budget was barely used and the weight-space margins (0.4c at ties) were not stressed beyond shuffled orders at 20 ms.
  g1 (GABA paddle) was not run.
- NES follow-up: make the grown LIFC defaults (`struct LIFCNeuronPars`, `NetmorphManagerThread.cpp`) configurable from the Netmorph/NES config and let `LIFC/Edit` change
  ResetMethod, fAHP/sAHP/ADP, fatigue and adaptive-threshold fields. Then this transplant is a plain "edit the grown model" (no rebuild), and persisting edited weights in `ModelSave` would make it storable.

# Neuroglancer views (`pong_neuroglancer.py`)

    python pong_neuroglancer.py -Model handwired|g2|transplant [-Resolution_um 0.5] [-SubdivideSize 1]
    python pong_neuroglancer.py -Model g2 -BBoxOnly       # print bounding box + voxel estimate, no render

Builds/loads the model (handwired: `pong_handwired.build`; g2: `ModelLoad('johnjose-pong-g2')`;
transplant: `pong_transplant.build` from `transplant_recipe.json` + g2 connectome), then runs the xor_scnm
acquisition calls: EM render (segmentation and meshes on), `PrepareNeuroglancerDataset`, `WaitForConversion`,
`GetNeuroglancerDatasetURL(_ForceURLBase='http://localhost:8100')`. It prints `Dataset Handle:` and `URL:`
and writes `output/ng_<model>.json`. Port 8100 (private stack) only. No sim is run; geometry exists after build.

Viewing: the URLs use the API base `http://localhost:8100`. In VS Code Remote-SSH port 8100 is normally
forwarded automatically when you open the link (otherwise add it in the Ports panel); from a plain shell use
`ssh -L 8100:localhost:8100 ccfbgworkserver01`.

Bounding boxes (um) and voxel counts at the chosen resolution:

| Model | Extent (um) | Resolution | Voxels |
|---|---|---|---|
| handwired | 148 x 180 x 218 | 0.5 | 4.7e7 |
| g2 | 1630 x 1274 x 1377 | 1.0 (2.3e10 voxels at 0.5, too many) | 2.9e9 |
| transplant | 640 x 376 x 461 | 0.5 | 8.9e8 |

## Status: not yet rendered (NES crash)
First attempt (handwired, 0.5 um, sim 193) crashed the private NES during the render, at "Voxel Array Does Not
Exist Yet Or Is Wrong Size, (Re)Creating":
`terminate called after throwing an instance of 'std::out_of_range'  what(): vector::_M_range_check: __n (which is 40097548) >= this->size() (which is 172)`
(`pong-stack/nes.log`). The client sees `MakePostQuery request returned error: 204` afterwards. The NES on 8100
has to be restarted before any further attempt, so no dataset UUIDs or URLs exist yet.

| Model | UUID | URL | Resolution | Render time |
|---|---|---|---|---|
| handwired | - | - | 0.5 | crashed NES after 10 s |
| g2 | - | - | - | not run |
| transplant | - | - | - | not run |
