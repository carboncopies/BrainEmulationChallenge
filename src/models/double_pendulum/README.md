# double_pendulum: cart + inverted double pendulum, LQR baseline

Phase 1 of a new BEC model. Pure Python (numpy, scipy), no NES, no network.
Later phases will drive this env from a spiking network in NES stepped in
discrete control ticks (Pong used 20 ms), so the env has an explicit control
period, zero-order hold, actuation delay and force saturation.

## Files
- `dp_env.py`: dynamics (Lagrangian, derivation in the docstring), RK4, `DoublePendulumEnv`, `run(controller, T, seed, ...)` episode runner with metrics and optional trace.
- `dp_lqr.py`: analytic linearisation `linearize()` (A, B), finite-difference check `linearize_fd()`, controllability, continuous LQR `clqr()`, discrete ZOH LQR `dlqr(ctrl_dt, delay)`. Phase 2 can read the gain K (and A, B) from here.
- `test_dp_env.py`: pytest (determinism, energy, linearisation vs finite difference, LQR holds 180 s, delay/saturation).
- `dp_baseline.py`: CLI producing the table below and `output/baseline.json` (gitignored).

## Model
q = [x, th1, th2]; th1, th2 are absolute angles from upright (0 = upright). State
s = [x, th1, th2, xd, th1d, th2d], input = horizontal cart force F. Uniform rods
(centre of mass at l/2, inertia about the centre m l^2/12). With
a = m1 lc1 + m2 l1, b = m2 lc2, c = m2 l1 lc2: M(q) qdd = rhs, with M diagonal
terms (mc+m1+m2, m1 lc1^2+m2 l1^2+I1, m2 lc2^2+I2) and off-diagonals
a cos th1, b cos th2, c cos(th1-th2); rhs has the centripetal terms
(a sin th1 th1d^2 + b sin th2 th2d^2 in x; -c sin(th1-th2) th2d^2 in th1, +c sin(th1-th2) th1d^2 in th2),
gravity (a g sin th1, b g sin th2), F, and viscous friction.

Params (defaults): cart 1 kg, links 0.5 m / 0.2 kg each, g 9.81, cart friction
0.05 N s/m, joint friction 0.002 N m s/rad, |F| <= 20 N. RK4 dt = 5 ms.
Disturbance (seeded): Poisson kicks at 1 Hz, each 20 ms long, cart impulse
N(0, 0.02 N s) (about 1 N) and link torque impulses N(0, 0.001 N m s) (about
0.05 N m). Sensor noise optional (default off, not used in the baseline).
Fall = any |angle| > 45 deg (episode ends). Upright = both |angle| <= 10 deg.

## LQR
Open-loop poles: +-10.8, +-10.1, +-4.3, ~0 (controllable, rank 6). Weights
Q = diag(50, 100, 100, 5, 1, 1), R = 2. Continuous gain
K = [5.0, -158.18, 199.74, 7.62, -1.81, 25.18] (u = -K s). Discrete ZOH gains:
5 ms [4.615, -151.07, 188.56, 7.04, -2.02, 23.70]; 10 ms [4.26, -144.47,
178.19, 6.51, -2.21, 22.32]; 20 ms [3.63, -132.62, 159.62, 5.56, -2.55, 19.86].
Controllers: `StateFeedback(K)` (ignores delay), `DelayAwareLQR`
(gain designed on the state augmented with the pending commands).

## Run
    cd src/models/double_pendulum
    python3 -m pytest -q -s
    OMP_NUM_THREADS=1 python3 dp_baseline.py        # about 6 min with 2 processes

## Baseline (measured, 180 s, 3 seeds, mean over seeds)
Columns: upr = fraction of time both angles within 10 deg; th1/th2 = rms deg;
rmsF/maxF = N; drift = max |x| (m); rmsX (m); last column = fall time per seed
(- = no fall). A run "holds" if no seed fell and upr >= 0.99 for all seeds.
`plain` = gain for ctrl_dt that ignores delay; `aware` = delay-augmented gain.
cXX = control period ms, dN = delay in ticks. Disturbance on except row 1.

```
condition                             upr    th1    th2   rmsF   maxF  drift   rmsX  fall s (per seed)
lqr, no disturbance                 1.000   0.06   0.05   0.03   0.71   0.06  0.004  -/-/-
lqr, disturbance                    1.000   1.04   0.71   0.75   8.99   0.23  0.061  -/-/-
zero force, disturbance             0.002  12.58  15.57   0.00   0.00   0.04  0.015  0.51/0.63/0.63  [FAILS]
plain c5 d0                         1.000   1.04   0.71   0.75   8.99   0.23  0.061  -/-/-

-- plain gain, disturbance on, ctrl_dt (ms) x delay (ticks)
condition                             upr    th1    th2   rmsF   maxF  drift   rmsX  fall s (per seed)
plain c5 d0                         1.000   1.04   0.71   0.75   8.99   0.23  0.061  -/-/-
plain c5 d1                         1.000   1.03   0.71   0.80  10.23   0.23  0.061  -/-/-
plain c5 d2                         1.000   1.02   0.70   0.87  11.25   0.23  0.061  -/-/-
plain c5 d3                         1.000   1.02   0.69   0.97  12.03   0.23  0.060  -/-/-
plain c5 d4                         1.000   1.01   0.69   1.12  12.98   0.23  0.060  -/-/-
plain c10 d0                        1.000   1.06   0.73   0.77   9.05   0.24  0.062  -/-/-
plain c10 d1                        1.000   1.05   0.72   0.90  11.08   0.24  0.062  -/-/-
plain c10 d2                        1.000   1.04   0.70   1.18  12.87   0.24  0.062  -/-/-
plain c10 d3                        1.000   1.07   0.67   2.58  19.22   0.23  0.060  -/-/-
plain c10 d4                        0.005  10.90   4.32  13.52  20.00   0.44  0.116  0.87/1.27/1.29  [FAILS]
plain c20 d0                        1.000   1.12   0.77   0.81   9.51   0.25  0.065  -/-/-
plain c20 d1                        1.000   1.09   0.73   1.33  13.39   0.25  0.065  -/-/-
plain c20 d2                        0.004  13.09   6.98  13.48  20.00   0.29  0.108  0.73/1.17/1.16  [FAILS]
plain c20 d3                        0.002  13.94  12.23  13.44  20.00   0.19  0.075  0.59/0.76/0.76  [FAILS]
plain c20 d4                        0.002  13.47   9.42  12.88  20.00   0.41  0.128  0.48/0.73/0.73  [FAILS]
plain c30 d0                        1.000   1.18   0.82   0.86   9.34   0.26  0.069  -/-/-
plain c30 d1                        0.011   9.58   5.05  12.34  20.00   0.28  0.078  1.38/2.92/2.51  [FAILS]
plain c30 d2                        0.003  15.31   7.20  12.75  20.00   0.19  0.090  0.57/0.73/0.73  [FAILS]
plain c30 d3                        0.002  14.94   8.52  11.33  20.00   0.25  0.107  0.45/0.69/0.69  [FAILS]
plain c30 d4                        0.002  12.71   3.10   9.82  20.00   0.39  0.122  0.48/0.58/0.58  [FAILS]
plain c40 d0                        1.000   1.25   0.87   0.91   8.86   0.28  0.073  -/-/-
plain c40 d1                        0.004  13.06   6.99  12.80  20.00   0.34  0.102  0.73/0.99/0.99  [FAILS]
plain c40 d2                        0.002  11.97   8.92  11.48  20.00   0.21  0.094  0.48/0.71/0.71  [FAILS]
plain c40 d3                        0.003  12.30   3.74   9.61  17.94   0.40  0.122  0.48/0.59/0.59  [FAILS]
plain c40 d4                        0.002  10.93  10.32  11.36  20.00   0.47  0.134  0.55/0.64/0.64  [FAILS]

-- aware gain, disturbance on, ctrl_dt (ms) x delay (ticks)
condition                             upr    th1    th2   rmsF   maxF  drift   rmsX  fall s (per seed)
aware c5 d1                         1.000   1.09   0.75   0.79   9.45   0.24  0.063  -/-/-
aware c5 d2                         1.000   1.14   0.79   0.82   9.93   0.25  0.066  -/-/-
aware c5 d3                         1.000   1.19   0.83   0.87  10.43   0.27  0.069  -/-/-
aware c5 d4                         1.000   1.25   0.87   0.91  10.96   0.28  0.073  -/-/-
aware c10 d1                        1.000   1.17   0.81   0.85   9.99   0.26  0.068  -/-/-
aware c10 d2                        1.000   1.28   0.89   0.93  11.03   0.29  0.074  -/-/-
aware c10 d3                        1.000   1.41   0.98   1.03  12.17   0.31  0.081  -/-/-
aware c10 d4                        1.000   1.54   1.07   1.14  13.44   0.34  0.089  -/-/-
aware c20 d1                        1.000   1.35   0.94   0.99  11.52   0.30  0.078  -/-/-
aware c20 d2                        1.000   1.63   1.13   1.21  13.98   0.36  0.093  -/-/-
aware c20 d3                        0.999   1.98   1.37   1.49  15.78   0.42  0.111  -/-/-
aware c20 d4                        0.929   2.54   1.73   1.96  17.68   0.54  0.129  -/-/144.00  [FAILS]
aware c30 d1                        1.000   1.57   1.09   1.16  12.64   0.34  0.090  -/-/-
aware c30 d2                        0.998   2.11   1.45   1.59  15.94   0.44  0.116  -/-/-
aware c30 d3                        0.921   3.06   1.97   2.33  19.16   0.54  0.143  -/-/143.59  [FAILS]
aware c30 d4                        0.066   6.45   3.91   4.87  20.00   0.46  0.148  7.00/24.23/6.83  [FAILS]
aware c40 d1                        1.000   1.83   1.27   1.36  13.32   0.39  0.104  -/-/-
aware c40 d2                        0.924   2.93   1.89   2.24  18.82   0.58  0.140  -/-/143.91  [FAILS]
aware c40 d3                        0.065   6.55   3.98   4.84  20.00   0.47  0.158  6.88/23.66/6.77  [FAILS]
aware c40 d4                        0.026   6.86   7.76   7.43  20.00   0.47  0.123  0.68/11.69/3.59  [FAILS]

```

Timing budget (disturbance on, largest ctrl_dt in ms that holds, from the grid
above; ceiling is also in `output/baseline.json`):

```
delay (ticks)      0    1    2    3    4
plain gain        40   20   10   10    5
delay-aware gain  40   40   30   20   10
```


## Phase 2: hand-derived spiking controller (Python stand-in, no NES)

Files: `dp_codec.py` (encoder/decoder, swappable), `dp_spiking.py` (LIFC-like stand-in network + controller
class for `dp_env.run`), `dp_derive.py` (K and closed-loop statistics -> every weight, writes
`weights_recipe.json`; `weights_recipe_derived.json` is the pre-adjustment version), `dp_phase2.py` (CLI),
`weightspace_log.md` (each number: derived vs hand adjustment), `test_dp_spiking.py`.

Architecture: 6 states x (pos, neg) input populations of 256 spike sources (rates r0 +- g_i s_i, r0 = 150 Hz,
regular spikes on the 1 ms grid) -> AMPA only -> push and pull groups of 111 clean LIFC neurons (Pong step-1
parameters, 1 ms step); force = 0.0854 N x (push count - pull count) per 10 ms window. 3072 input neurons,
222 output neurons, 1998 receptors, weights 0.21 to 1.88 nS. K_i sigma_i spans 11.6x (|K| 80x); the encoder
gain g_i = r0/range_i takes the range and the weight carries only K_i range_i. Latency: encode and count
in the same 10 ms window, force applied one tick later, plus 0.28 tick of measured lag: 1.28 ticks, run at
delay 2. Weights are derived; one hand adjustment (decoder constant x 1/1.113).

Measured, 180 s, disturbance on, ctrl_dt 10 ms, mean of seeds 0,1,2 (all upright 1.000, none fell):

| delay (ticks) | controller | RMS th1 (deg) | RMS th2 (deg) | RMS force (N) | peak force (N) | max cart drift (m) |
|---|---|---|---|---|---|---|
| 2 | spiking | 1.16 | 0.84 | 1.49 | 15.1 | 0.26 |
| 2 | LQR 10 ms | 1.04 | 0.70 | 1.18 | 12.9 | 0.24 |
| 1 | spiking | 1.17 | 0.86 | 1.11 | 12.4 | 0.27 |
| 1 | LQR 10 ms | 1.05 | 0.72 | 0.90 | 11.1 | 0.24 |

Per-seed numbers are in `output/phase2.json` (delay 2; `dp_phase2.py --delay 2`) and `output/phase2_d1.json`
(`dp_phase2.py --delay 1 --out output/phase2_d1.json`), both gitignored. Seed 2 is the hardest: spiking peak
force 18.5 N at delay 2, and the encoder clipped on 59 (delay 2) and 96 (delay 1) of 18000 ticks.
Encoder clipping on the eval seeds: 3, 0 and 59 of 18000 ticks (the ranges come from seed 100).
Run: `python3 dp_phase2.py [--delay D]`, `python3 dp_phase2.py --latency`, `python3 dp_derive.py`.

Would not carry over to NES as is: single-exponential synapse (NES AMPA has a 0.5 ms rise), perfectly regular
input trains and exact count readout (NES needs `SetSpecificAPTimes` per window plus `GetSpikeTimes`
round trips, 27-35 ms per tick in Pong, which is over the 10 ms budget), arbitrary receptor values
(grown pairs cap at `g_peak_sum`; setters write only AMPA), designed connectivity of 1998 receptors
(Pong grew 526) and 3072 input neurons, and the clean LIFC parameters (R 100 MOhm, C 100 pF) must be
applied through `LIFC/Edit` (no adaptation) as in Pong step 1. Real run time per window is not modelled.


## Phase 3a: the phase-2 controller in NES (speed and first short run)

Files: `dp_nes.py` (builder + `NESController`, lockstep tick), `dp_nes_speed.py` (step 1 CLI),
`dp_nes_run.py` (latency, static calibration, closed-loop run and stand-in on the same settings). Private stack
only (API 127.0.0.1:8100; the PythonClient is imported from the Pong worktree because this worktree's submodule is
not checked out: `DP_PYTHONCLIENT` overrides). Results in `output/` (gitignored). Weight and parameter adjustments
are logged in `weightspace_log.md` (U1 unit conversion, A2 decoder constant).

Build (recipe as is, batched requests): 3294 LIFC neurons (3072 inputs + 2 x 111), 1998 AMPA receptors, **4.4 to 4.8 s**
wall (shapes 1 s, compartments 1 s, neurons 1.5 s, receptors 1 s). The client's own `BatchCreate` for LIFC neurons and
receptors references undefined classes (`SCNeuron`), so `dp_nes._batch` builds the request list itself.

Per control tick (10 ms simulated, `SetSpecificAPTimes` of about 4600 input spikes, `RunFor(10, 1)` plus 2 ms status
polling, `GetSpikeTimes`), 300 ticks, random observations 0.5 sigma (`dp_nes_speed.py`), ms:

| | schedule | run | read | total |
|---|---|---|---|---|
| mean over 300 | 41 | 955 | 1042 | 2039 |
| p95 | 53 | 1490 | 1896 | 3274 |
| ticks 1-50 | 42 | 285 | 233 | 561 |
| ticks 251-300 | 41 | 1264 | 1790 | 3096 |

It grows with tick count. Schedule is flat. Read grows linearly (about 6 ms per tick per tick): `GetSpikeTimes` returns the
full history of all 3294 neurons, 92% of it the input sources (1.38 M of 1.51 M spikes at tick 300; 10.1 MB response,
0.09 MB at tick 1). Run also grows, with the same slope when `GetSpikeTimes` is never called (`--noread`: 284, 708,
1008 ms for ticks 1-50, 51-100, 101-150, `output/nes_speed_noread.json`), then levels off near 1.2 to 1.3 s. So it is
inside NES. Candidate cause (read from source, not isolated): `g_norm` in `Structs/Receptor.cpp` walks the presynaptic
spike history backwards with `spike_dt_delta` = 1000 ms before it stops, per receptor per step. 720-tick run (below):
mean 3.34 s/tick, 0.96 s for ticks 1-100, 5.3 s for 701-720.

(a) The loop is lockstep. `dp_env.run` calls `controller(obs)` and blocks until it returns the force; the plant does not
advance during the NES tick, and the actuation delay is counted in simulated control ticks, not wall time. Slowness
costs wall-clock only, not balance. Simulated latency is the one 10 ms window plus the network lag.

(b) Projection, using the per-tick growth measured in the 720-tick run (about 5.3 ms per tick per tick after tick 400):
10 s simulated about 1.1 h (it took 40 min to reach 7.2 s); 30 s about 8 h (last tick about 17 s); 180 s about 245 h
(last tick about 97 s, history response about 600 MB). Not feasible as is.

Smallest fix, proposed only (not built, running NES untouched): `feature/windowed-getspiketimes` (`~/BrainGenix/wt/nes-spikewindow`)
adds `SinceTime_ms` and `NeuronIDs` to `Simulation/GetSpikeTimes`; asking for the 222 output IDs since t0 makes the read
constant (tens of ms) and removes the input sources from the response. Run would then stay near the 1.2 to 1.3 s plateau
(expected about 1.3 s per tick: 30 s about 1.1 h, 180 s about 6.6 h, projections, unmeasured). The plateau itself would need
the history cut in `g_norm` (`spike_dt_delta` 1000 ms to a few tens of ms, where the contribution is below `history_delta`);
untested.

Latency of the NES net (step response, 5 repetitions, `output/nes_latency.json`): first tick 0.47 of steady, then
0.92, 1.04, 0.96; extra lag 0.60 tick, total 1.60 ticks (stand-in 1.28), so the delay used is **2** (same as phase 2).
Static gain was 1.69x the stand-in's (see A2 in the log), zero-state force sd 0.18 N.

First short run (disturbance on, seed 0, ctrl_dt 10 ms, delay 2, A2 applied; NES budget 40 min, so **7.2 s of the 10 s
requested** was reached, 720 ticks, 2406 s wall, no fall). Stand-in on the identical settings for 7.2 s and for 10 s:

| controller | T (s) | upright | RMS th1 (deg) | RMS th2 (deg) | RMS force (N) | peak force (N) | drift (m) | fall |
|---|---|---|---|---|---|---|---|---|
| NES | 7.2 | 1.000 | 1.28 | 0.71 | 1.82 | 11.1 | 0.104 | none |
| stand-in | 7.2 | 1.000 | 1.26 | 0.78 | 2.17 | 14.2 | 0.087 | none |
| stand-in | 10 | 1.000 | 1.18 | 0.78 | 1.91 | 14.2 | 0.151 | none |

One seed, 7 s: this shows the NES net holds the pendulum under the same disturbance, not a statistical comparison.
Encoder clipped on 0 of 720 ticks; mean 417 output spikes per tick (stand-in about 372). The budget stop replays the
seeded episode with the recorded forces (observations checked identical) so the metrics cover exactly the time reached.
Run: `python3 dp_nes_speed.py`, `python3 dp_nes_run.py --latency | --calibrate | --run --T 10 --delay 2 | --standin`.

## Phase 3b: windowed spike read (per-tick cost stops growing), 10 s run

NES build: `~/BrainGenix/wt/nes-spikewindow` (`feature/windowed-getspiketimes`, `9a8bdfb92` + `5d91103a1`:
`Simulation/GetSpikeTimes` takes optional `SinceTime_ms` (spikes with t >= it) and `NeuronIDs`; both absent gives the old
response). The existing binary predated the source commits (built 23:27, sources 23:51 to 23:57), so it was **rebuilt**
(`cmake --build Build --target BrainGenix-NES -j8`; the old one kept as `Binaries/BrainGenix-NES.prev`). That NES reports
API version 1.0.1, and the local `BrainGenix-API` binary (1.0.0) answers 204 (version mismatch), so the API was rebuilt from
`origin/master` (`50b06777e`, only the 1.0.1 bump and a checksum-polling change vs the old binary) in a separate worktree
`~/BrainGenix/wt/api-v101`; no existing binary was touched.

Private stack `~/BrainGenix/wt/dp-stack` (`api/`, `nes/`, `Source/Core/Config/users.json` symlink, `nes-out/`, logs
`api.log`, `nes.log`), tmux session `dp-stack` (windows `api`, `nes`). API 127.0.0.1:8100; NES 8101 and callback 8099
bind 0.0.0.0 (#72; the config has no host option for them). The client needs requests_futures: run with
`~/BrainGenix/BrainEmulationChallenge/venv/bin/python`.

Client: `NESLoop(read='window')` posts the request itself (`_windowed_request`; the PythonClient has neither argument) with
`SinceTime_ms` = tick start and `NeuronIDs` = the 222 outputs. Output spikes of a tick are stamped t0 .. t0+9 ms, so the
tick-start offset is exact (an offset of 0.5 ms drops the ones stamped t0, about 10%).
`dp_nes_check_window.py`, 40 ticks, 16059 output spikes: per neuron, the windowed list equals the new part of the full
read's list exactly (times and counts) on every tick. Response: 7.4 to 7.7 kB per tick, against 0.92 MB at tick 30 for the
full read (grows to 10 MB by tick 300).

Speed, 300 ticks, same random observations as 3a, ms (`dp_nes_speed.py --read window`, `output/nes_speed_windowed.json`):

| | schedule | run | read | total |
|---|---|---|---|---|
| mean over 300 | 55 | 940 | 14 | 1011 |
| p95 | 104 | 1487 | 30 | 1566 |
| ticks 1-50 | 41 | 283 | 10 | 336 |
| ticks 251-300 | 65 | 1343 | 17 | 1428 |

(3a, full read: total 2039 mean, 561 at ticks 1-50, 3096 at 251-300.) The read is now 10 to 17 ms (still a slope of 0.024
ms per tick: the filter walks each output neuron's history). `RunFor` is unchanged and now the whole cost; in the closed
loop it flattens at about 1.1 to 1.2 s per tick from tick 150 on.

10 s run (seed 0, disturbance on, ctrl_dt 10 ms, delay 2, U1 + A2 as is, `--read window`, `output/nes_T10_windowed.log`
progress every 50 ticks, `output/nes_T10_windowed.json`): completed 10.00 s simulated, 1000 ticks, **1056 s wall** (0.56 s per
tick for ticks 1-100, 1.05 to 1.21 after; 40 ms schedule, 1002 ms run, 10.5 ms read, 8.0 kB response, mean).

| controller | T (s) | upright | RMS th1 (deg) | RMS th2 (deg) | RMS force (N) | peak force (N) | drift (m) | fall |
|---|---|---|---|---|---|---|---|---|
| NES, windowed | 10 | 1.000 | 1.21 | 0.72 | 1.66 | 11.1 | 0.157 | none |
| stand-in | 10 | 1.000 | 1.18 | 0.78 | 1.91 | 14.2 | 0.151 | none |

Same dynamics as 3a: the first 720 forces are identical to 3a's (max difference 0.0 N; metrics over 7.2 s equal 3a's to
three digits), as expected, since the read does not touch the network. No recalibration (U1, A2 unchanged). Encoder clipped on 0
ticks; 417 output spikes per tick (stand-in 371). One seed.

Projection from this run (about 0.56 s per tick for the first 100 ticks, then about 1.1 to 1.2 s; not measured beyond
1000 ticks): 30 s about 55 to 60 min, 180 s about 5.5 to 6 h. If `RunFor` keeps creeping up past 1000 ticks (the last
100 ticks were at 1.21 s) these rise; the `g_norm` history cut named in 3a is still untested.
Run: `python3 dp_nes_check_window.py`, `python3 dp_nes_speed.py --read window`,
`python3 dp_nes_run.py --run --T 10 --read window --progress output/nes_T10_windowed.log --out output/nes_T10_windowed.json`.

### 30 s runs, seeds 0, 1, 2 (windowed read)

Same settings as the 10 s run (disturbance on, ctrl_dt 10 ms, delay 2, U1 + A2, no recalibration; seeds 1 and 2 are eval
seeds, nothing was tuned on them). Files: `output/nes_T30_windowed[_s1|_s2].log/.json`, `output/standin_T30_d2_s{0,1,2}.json`.
All six runs completed 30.00 s with no fall (upright 1.000); encoder clipped on 0 ticks.

| seed | controller | RMS th1 (deg) | RMS th2 (deg) | RMS force (N) | peak force (N) | drift (m) |
|---|---|---|---|---|---|---|
| 0 | NES | 1.13 | 0.73 | 1.42 | 11.1 | 0.222 |
| 0 | stand-in | 1.23 | 0.91 | 1.54 | 14.2 | 0.234 |
| 1 | NES | 1.08 | 0.73 | 1.38 | 8.7 | 0.215 |
| 1 | stand-in | 1.21 | 0.90 | 1.44 | 9.5 | 0.243 |
| 2 | NES | 1.17 | 0.75 | 1.66 | 10.2 | 0.217 |
| 2 | stand-in | 1.35 | 0.99 | 1.70 | 12.0 | 0.272 |
| mean | NES | 1.13 | 0.74 | 1.49 | 10.0 | 0.218 |
| mean | stand-in | 1.26 | 0.94 | 1.56 | 11.9 | 0.249 |

Wall: 3795 s (seed 0), 3715 s (seed 1), 3701 s (seed 2), 1.23 to 1.26 s per tick mean (about 1.2 s run, 12 ms read, 44 ms
schedule, 8.3 kB response). `RunFor` did **not** keep creeping up past tick 1000: mean per tick for ticks 1000-2000 /
2000-3000 was 1.27 / 1.26 (seed 0), 1.28 / 1.26 (1), 1.28 / 1.25 (2); the first 100 ticks cost 0.5 s. The seed 0 run showed
1.75 to 1.91 s per tick over ticks 300-500, while another process on the box had load average above 100 (it fell back
by tick 900); this is box contention, not NES. Over 100 ticks of the first minute the cost rises from 0.5 to the 1.25 s
plateau reached by about tick 600 and stays flat, so wall-clock is linear: 180 s simulated is about 5.5 h at 1.1 to 1.25 s per tick
(projection beyond 3000 ticks, unmeasured). One 30 s episode per seed is a small sample; the NES net is at or slightly
better than the stand-in on every seed in these metrics.

## Speed-up: where the NES tick goes, and a g_norm lookback cap (not adopted as-is)

Profile of the unmodified NES (`nes-spikewindow`, v1.0.1, `Dt_ms` 1.0, i.e. 10 steps per tick) via a timing build of the same
source (`profiling/nes_gnorm_prof.patch`: chrono counters around the `g_norm` callers, one `PROF` line per `RunFor` on
stderr; `perf` is not permitted on this box, `perf_event_paranoid` 3). 700 ticks, `dp_nes_equiv.py --tag prof`, parsed with
`dp_nes_compare.py --prof LOG`. The timing build gives spikes identical to the plain binary (deterministic).

| per tick, ms | ticks 1-50 | ticks 601-700 |
|---|---|---|
| Python total (schedule + run + read) | 264 | 1116 |
| NES stepping inside RunFor | 213 | 1062 |
| synapse `g_norm` (Neuron.cpp:153,156, 1998 receptors) | 37 (17%) | 130 (12%) |
| fAHP + sAHP `g_norm` (LIFCNeuron.cpp:260-261) | 105 (49%) | 628 (59%) |
| ADP `g_norm` (LIFCNeuron.cpp:270) | 50 (23%) | 276 (26%) |
| other stepping | 13 (6%) | 19 (2%) |
| `g_norm` iterations per call (synapse / fAHP+sAHP / ADP) | 37 / 38 / 38 | 151 / 244 / 223 |

(The remaining Python-side cost is about 30 ms schedule and 7 to 8 ms read per tick.) So about 97% of a plateau tick is `g_norm`, but
only 12% of that is the synapse lookback the cap targets: 85% is the neuron's own fAHP/sAHP/ADP kernels, evaluated for all 3294 neurons
every step even though every `*PeakConductance_nS` in this network is 0 (so the result is `0 * g_norm`). The growth over the first
several hundred ticks is the spike history filling the lookback (1 s for synapses, 2 to 3 s for ADP/sAHP).

Change tried (`~/BrainGenix/wt/nes-lookback`, branch `perf/gnorm-lookback`, `54f0a65fb`): in `g_norm`,
`spike_dt_delta = min(spike_dt_delta, max(12 * max(tau_rise, tau_decay), 10 ms))`. It only affects kernels with 12 tau < 1000 ms
(AMPA 3 ms -> 36 ms, fAHP 30 ms -> 360 ms); sAHP and ADP are unchanged. Dropped tail below 6.1e-6 of one spike's peak per spike,
at most 3.7e-5 for a 1 spike per ms AMPA train. Same 700-tick fixed observation sequence for both binaries (ticks 1-300 random,
301-450 six static states of 25 ticks, calibrate()-style seed 7, 451-700 random), windowed read:

| | baseline | cap | speedup |
|---|---|---|---|
| ticks 1-50 total (sched / run / read) | 257.5 (36.3 / 210.4 / 9.0) | 222.9 (35.1 / 177.0 / 9.2) | 1.16x |
| ticks 601-700 total (sched / run / read) | 1039.8 (37.0 / 991.1 / 10.0) | 811.4 (34.5 / 766.3 / 9.2) | 1.28x |
| projected 30 s (3000 ticks) at plateau | 52 min | 41 min | |
| projected 180 s (18000 ticks) at plateau | 5.2 h | 4.1 h | |

**Behaviour is not identical.** The baseline is bit-reproducible (the timing build gives the same 290430 spikes), the cap run is not
the same: 5 of 290430 output spikes differ (290425), all 1 ms shifts at threshold, first at tick 5 neuron 213 (t=41 ms against 42 ms,
just after the first spike leaves the 36 ms window); 33 neuron-ticks differ (max 1 spike); force differs on 33 of 700 ticks, max
|dF| 0.051 N (one spike, = 1 decoder count), mean |dF| 0.0024 N (RMS force 1.75 N). That is a rounding-level change in one
neuron, not float noise, so the cap was stopped here and not tuned. A bit-identical alternative that would remove the 85%: skip the
`g_peak * g_norm` AHP/ADP evaluation when the peak conductance is 0 (not implemented or measured).
Scripts: `dp_nes_equiv.py --tag X` (records spikes and force per tick), `dp_nes_compare.py A B [--prof LOG]`.
