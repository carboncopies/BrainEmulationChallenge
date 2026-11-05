# pong_netmorph (step 1: hand-wired controller)

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
    ./Run.sh -P 8100 -m truthtable
    ./Run.sh -P 8100 -m play -t 1000 -s 1
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
