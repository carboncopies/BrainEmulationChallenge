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

Per-seed numbers are in `output/phase2.json` (delay 2) and `output/phase2_d1.json` (gitignored).
Encoder clipping on the eval seeds: 3, 0 and 59 of 18000 ticks (the ranges come from seed 100).
Run: `python3 dp_phase2.py [--delay D]`, `python3 dp_phase2.py --latency`, `python3 dp_derive.py`.

Would not carry over to NES as is: single-exponential synapse (NES AMPA has a 0.5 ms rise), perfectly regular
input trains and exact count readout (NES needs `SetSpecificAPTimes` per window plus `GetSpikeTimes`
round trips, 27-35 ms per tick in Pong, which is over the 10 ms budget), arbitrary receptor values
(grown pairs cap at `g_peak_sum`; setters write only AMPA), designed connectivity of 1998 receptors
(Pong grew 526) and 3072 input neurons, and the clean LIFC parameters (R 100 MOhm, C 100 pF) must be
applied through `LIFC/Edit` (no adaptation) as in Pong step 1. Real run time per window is not modelled.
