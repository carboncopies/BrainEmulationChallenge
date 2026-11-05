# pend_nes_harness: spiking controller harness for cart + double pendulum

`pend_nes_harness.py` is a pure-stdlib harness for driving a cart + double-pendulum plant with a spiking
network. It follows how `bec-pong/src/models/pong_netmorph` drives NES with LIFC neurons. The harness does
not start or stop NES, and it does not import `crosscheck.py`.

Run the self-test and smoke test (no NES needed):

    python3 -m py_compile pend_nes_harness.py
    python3 pend_nes_harness.py

## Pieces and where they come from in Pong

| Harness piece | What it does | Pong counterpart (`bec-pong/src/models/pong_netmorph/`) |
|---|---|---|
| `Encoder` | State -> input spike trains per control window. Signed population code: 6 variables x 2 signs x 8 neurons. | `pong_env.py` `_bin` / `ball_bin` / `paddle_bin` turn the state into one bin index. `pong_handwired.py` / `pong_transplant.py` fire one place cell (B_i, P_j) per bin. The encoder replaces one-hot bins with a rate code. |
| Burst timing (not yet in the harness) | Input spikes are emitted as integer-ms times within the window. | `pong_transplant.py` `ENCODING` (3 spikes, 3 ms ISI, 1 ms offsets) and `SetSpecificAPTimes` in `pong_handwired.py`. Pong AP times must be integer ms (README "NES gotchas"). |
| `Decoder` | Net count (right minus left) per window -> force in N, clipped to +/-20 N. | `pong_handwired.py` / `nes_loop.py` read new UP/DOWN spikes per tick. Pong's action is `sign(nUP - nDOWN)` (README, Architecture). The harness keeps the difference and scales it to newtons. |
| Output groups | Push-left (L) and push-right (R) groups. | UP and DOWN cells (`pong_transplant.py` `out_neuron`, `RELAY_NEURON`, `INPUT_NEURON` parameter sets). |
| `synapse_routes` / `ControlLoop.set_weights` | Maps the 6-input weight vector W to input -> output routes. | `weightspace_recipe.json` `pairs` (`[pre, post, g_nS]`) and `design.relays`. The transplant rule in `pong_transplant.py` `build()` builds a receptor only for a pair that exists in the grown connectome. |
| `LIFStandIn` | Pure-Python LIF pair, for smoke tests without NES. | Stands in for the NES LIFC neurons built by `pong_transplant.py` `neuron()` / `compartment()`. |
| `ControlLoop` | Encoder -> network -> decoder, once per 10 ms window. | `nes_loop.py` `ClosedLoop`: `RunFor`, status poll, new-spike slicing. |
| `StubPlant` | Kinematic plant for smoke tests only. | No counterpart. The real plant is the simulated cart-pendulum. |

## Encoder

- For variable i, `z_i = clip(state_i / scale_i, -1, 1)`.
- Positive group (sign 0) carries `max(z, 0)`, negative group (sign 1) carries `max(-z, 0)`.
- Each group has 8 neurons with hat-shaped tuning centred at `(k+1)/8`. Their rates are `R_MAX * hat_k(z)`.
- The hats interpolate the identity, so `sum_k c_k * rate_k / R_MAX == z` exactly. The self-test checks this.
- Input index is `(i*2 + sign)*8 + k`. 96 input neurons in total.
- Fractional spikes carry over between windows. Spike times are integer ms.

## Decoder

- `F = (N_per_count) * (n_right - n_left)`, with `N_per_count = 20 N / 100` by default.
- Clipped to +/-20 N. Positive force pushes the cart to +x, the same sign as `F = -K s` in `crosscheck.py`.
- Force resolution is `0.2 N` per net spike at the default `N_FULL_COUNTS = 100`.

## Weight vector W (the pluggable 6-input weight)

- `W` has 6 entries, one per state variable. Each entry is in counts per unit encoder value.
- `weights_from_gain(K, scales, gain, N_per_count)` returns `W_i = -gain * K_i * scale_i / N_per_count`.
  For an unclipped state this gives `F = -gain * K.s`, the LQR law.
- Routing: for `W_i >= 0`, the positive group goes to R and the negative group goes to L. For `W_i < 0` the
  groups swap. Each input neuron's weight per spike is `|W_i| * c_k / (R_MAX * T)`.
- Using only excitatory routes to the two groups gives `R - L = W.z`. No inhibition is needed. This matters
  because Pong's weight-space recipe only grew AMPA pairs for the used relays.
- To plug in a different controller, call `ControlLoop.set_weights(W)`. It rebuilds the routes.

## Stand-in LIF (`LIFStandIn`)

- Two groups of 32 LIF neurons with heterogeneous thresholds (-50 to -48 mV, 2 mV spread).
- Each input spike adds `weight * 1 mV` to every neuron on its target side. `tau_m` = 20 ms, refractory 2 ms.
- The jump constant is uncalibrated. The stand-in checks routing and decoding, not force scale. The smoke
  run shows the gap: mean force error is 2.4 N at gain 1 and 5.3 N at gain 5.

## Gain range and scale

- `gain_table` prints, for gains 5 and 200, the force a single variable produces at its encoder scale and the
  state excursion that alone reaches the 20 N cap.
- With `K_LQR_DEMO` (the LQR row from `crosscheck.py`) and the demo scales, the 20 N cap is reached at:
  - gain 5: theta2 = 0.017 rad, theta1 = 0.023 rad
  - gain 200: theta2 = 0.00042 rad, theta1 = 0.00057 rad
- So the per-variable scale cannot keep gains 5 to 200 unsaturated under the 20 N cap. This is an
  arithmetic fact about `K` and the cap, not a bug.
- In the smoke run at gain 5, one side fired 96 spikes in a window (the stand-in allows up to 160 per side).
  The decoder cap was never reached (max |F| 12.8 N).

## Open issues before NES

1. **Connectivity budget.** 96 input neurons, each routed to one output side, is 96 receptors if each side is one
   neuron. A 32-neuron output group would need 3072 receptors. The Pong connectome has 526 grown AMPA pairs,
   so the pairs must be checked against the connectome, as `pong_transplant.py` does.
2. **Output readout.** Pong's UP and DOWN are single neurons. A single LIFC neuron with 2 ms refractory fires
   at most 5 spikes per 10 ms, which caps the count. Either use more output neurons (more pairs) or
   accept the cap.
3. **Adaptive threshold floor.** Pong's README (Step 3 and 3b) found that the grown Netmorph adaptive-threshold
   floor (+1 mV per spike, about 500 ms recovery) silences UP/DOWN at 20 ms ticks. Use the clean LIFC set from
   `pong_transplant.py` (`AdaptiveThresholdDiffPerSpike = 0`), not the grown one. README step 3b found 20 ms
   ticks (0.435 mean play) slightly better than 100 ms (0.356), and both poor. A 10 ms window is untested.
4. **Shunting.** Pong's inhibition is GABA with E = -70 mV, which is shunting, not subtractive. The harness avoids
   inhibition by design, so no GABA is needed.
5. **Burst timing.** Pong's grown onset delays (2 to 8 ms, README) affect relay latency. A 10 ms window leaves
   little room for them.
6. **Force resolution.** At 0.2 N per spike, the LQR force in the nominal run (about 0.04 N RMS in `crosscheck.py`)
   is below one spike. The network must average over windows or the cap/scale must change.

## Files

- `pend_nes_harness.py`: the harness and smoke test.
- `README.md`: this file.
