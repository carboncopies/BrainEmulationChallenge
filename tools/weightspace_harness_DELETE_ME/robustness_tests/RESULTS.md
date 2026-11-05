# Robustness results: hand-derived spiking controller (Python stand-in) vs LQR

All numbers measured, from `output/robust.json` (written by `dp_robust.py`), table made by `summarize.py`.
Source folder was copied unchanged; weights, recipe, `dp_env.py`, `dp_spiking.py`, `dp_codec.py` are untouched.
New files: `dp_robust.py`, `summarize.py`, `diag.py`, `diag_clip.py`. No NES.

Setup: 180 s, ctrl_dt 10 ms, actuation delay 2 ticks (the recipe's assumed latency), baseline disturbance on
(1 Hz kicks) unless scaled, seeds 0,1,2. LQR = plain 10 ms DLQR gain at the same delay.
Columns: mean over the 3 seeds; fall s is per seed (- = none). For a run that fell, RMS/peak/drift cover the time before the fall
and `upr` is time upright / 180 s (so a fall lowers it). `base` reproduces the phase-2 table (1.16/0.84/1.49/15.1/0.26).

Conditions:
- noise_L: Gaussian noise on all 6 readings, std = L x sigma_i (sigma_i = closed-loop std per state from `weights_recipe.json`:
  0.0639, 0.0218, 0.0147, 0.1223, 0.1231, 0.0591). Own rng, so the kicks are identical to `base` for each seed. Applied to both controllers.
- jit_Nms: each input spike moved by round(N(0,N)) ms within its 10 ms window (counts per window unchanged); poisson: Bernoulli per 1 ms step at the same rate. Spiking only (LQR has no spikes).
- kick_Kx: cart and torque kick impulse std multiplied by K.
- off_V: start with th1 = th2 = V rad (baseline start is 1 deg = 0.0175 rad), everything else 0.
The levels are my choices (the request gave none for noise/jitter).

## Results

| condition | ctrl | upr | th1 deg | th2 deg | rmsF N | peak F N | drift m | fall s (seeds 0/1/2) |
|---|---|---|---|---|---|---|---|---|
| base | spiking | 1.000 | 1.16 | 0.84 | 1.49 | 15.1 | 0.26 | -/-/- |
| base | lqr | 1.000 | 1.04 | 0.70 | 1.18 | 12.9 | 0.24 | -/-/- |
| noise_0.1 | spiking | 1.000 | 1.16 | 0.84 | 1.63 | 14.9 | 0.26 | -/-/- |
| noise_0.1 | lqr | 1.000 | 1.05 | 0.71 | 1.33 | 13.0 | 0.24 | -/-/- |
| noise_0.25 | spiking | 1.000 | 1.23 | 0.88 | 2.14 | 15.6 | 0.26 | -/-/- |
| noise_0.25 | lqr | 1.000 | 1.11 | 0.75 | 1.94 | 13.4 | 0.25 | -/-/- |
| noise_0.5 | spiking | 1.000 | 1.43 | 1.01 | 3.37 | 18.9 | 0.28 | -/-/- |
| noise_0.5 | lqr | 1.000 | 1.32 | 0.87 | 3.30 | 16.6 | 0.26 | -/-/- |
| jit_1ms | spiking | 1.000 | 1.08 | 0.77 | 1.52 | 15.1 | 0.24 | -/-/- |
| jit_3ms | spiking | 1.000 | 1.04 | 0.69 | 1.52 | 14.2 | 0.23 | -/-/- |
| poisson | spiking | 1.000 | 1.10 | 0.72 | 2.11 | 14.0 | 0.24 | -/-/- |
| kick_2x | spiking | 0.129 | 3.72 | 1.72 | 4.01 | 20.0 | 0.38 | 6.83/27.09/37.17 |
| kick_2x | lqr | 0.998 | 2.03 | 1.36 | 2.37 | 20.0 | 0.46 | -/-/- |
| kick_4x | spiking | 0.030 | 8.27 | 4.05 | 9.03 | 20.0 | 0.30 | 1.25/13.08/3.19 |
| kick_4x | lqr | 0.156 | 6.62 | 3.73 | 5.99 | 20.0 | 0.53 | 6.74/75.23/6.45 |
| off_0.05 | spiking | 1.000 | 1.17 | 0.85 | 1.49 | 15.0 | 0.26 | -/-/- |
| off_0.05 | lqr | 1.000 | 1.05 | 0.71 | 1.18 | 12.9 | 0.24 | -/-/- |
| off_0.1 | spiking | 1.000 | 1.21 | 0.89 | 1.50 | 14.9 | 0.35 | -/-/- |
| off_0.1 | lqr | 1.000 | 1.09 | 0.75 | 1.19 | 13.6 | 0.29 | -/-/- |

## What failed, where and why

Everything passes (upr 1.000, no falls) for sensor noise up to 0.5 sigma, all three input-timing conditions and both start offsets. Spiking tracks LQR
closely there (noise 0.5: spiking rms th1 1.43 vs LQR 1.32, peak force 18.9 vs 16.6 N; force RMS rises mostly from the noise itself, 3.37 vs 3.30 N).
Irregular timing did not hurt (jit_3ms and poisson are no worse than the regular baseline on angle RMS). Start offset 0.1 rad raised drift (0.35 vs 0.26 m).

**kick_2x: spiking fails on all 3 seeds (falls 6.83, 27.09, 37.17 s), LQR holds (upr 0.998, no fall).
kick_4x: both fail** (spiking 1.25/13.08/3.19 s; LQR 6.74/75.23/6.45 s, so LQR also loses at 4x).

Why (kick_2x), from `diag.py` (seed 0) and `diag_clip.py`:
- The encoder input ranges (1.25 x the peak of the unkicked stats run) are exceeded under bigger kicks. In the seed-0 trace before the fall, th1 reaches 1.87 x its range
  (range 0.139 rad); over the run state/range peaks at 5.6 for th1 and 4.2 for th1d. Past 1 x range the input rate pins at 0 or 2 r0, so the
  controller reads a saturated angle and its effective gain falls exactly when the angle is large. Encoder clipped on 58, 97, 291 ticks for seeds 0,1,2 up to their falls (baseline: 3, 0, 59 of 18000).
- Test of that cause: the LQR with each reading clipped to the same +/- range_i fails at kick_2x as well (seed 0 at 6.805 s vs spiking 6.83 s; seed 2 37.185 vs 37.17 s; seed 1 75.48 vs spiking 27.09 s; upr 0.04/0.42/0.20). So the range clip reproduces the failure for two of three seeds almost to the tick and fails the third later; it is a main cause, not proven the only one.
- Force saturation at 20 N also contributes (peak force hits 20.0 for both controllers) and is the plant limit at 4x, where unclipped LQR fails too. It is not the cause at 2x for the
  spiking net, since unclipped LQR at 2x holds with the same 20 N limit.

## Proposed fixes (not applied)
1. Widen the encoder ranges (e.g. 2.5-3x the unkicked peak, or from a stats run with 2x kicks) and rescale the weights per `dp_derive.py` so K_i range_i is unchanged in the linear region. Cost: coarser resolution near zero (spike-count quantisation noise grows by the same factor, and zero-state force sd was already 0.28-0.52 N vs the 0.25 N target), possibly needing more input neurons per population. Larger ranges would lift the clip, but would not help at 4x where the 20 N limit also binds.
2. Instead of widening, soft-compress the input (e.g. a nonlinear encoder gain) so the large-angle reading keeps growing; this changes the linear law and would need re-derivation.
3. At 4x the actuator limit decides; no controller fix without a larger F_max or a different plant limit.
I did not run either fix.

## Commands used (from this folder, `OMP_NUM_THREADS=1`)
```
cp -r ~/BrainGenix/wt/bec-dpend/src/models/double_pendulum/. /home/johnjose/pendulum_work/robustness/   # then removed .pytest_cache, __pycache__
OMP_NUM_THREADS=1 python3 dp_robust.py --jobs 32        # 57 runs, 69 s wall; writes output/robust.json
python3 summarize.py                                    # table above
python3 diag.py                                         # seed-0 kick_2x trace
OMP_NUM_THREADS=1 python3 diag_clip.py                  # range-clipped LQR at kick 2x/4x
```
(`dp_robust.py` smoke test before that: `--T 10 --seeds 1 --only base,noise_0.5,jit_3ms,poisson`, output not kept.)
