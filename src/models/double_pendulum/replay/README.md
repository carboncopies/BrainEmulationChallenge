# Replay page and ball-on-a-string experiment

Scripts behind the animated replay artifact (generated 2026-11-06). Run from this folder after
`cd ..` so `dp_*` modules import (scripts add the path themselves; some paths are absolute to the
author's machine and need editing).

- `gen.py`: 10 s runs of no control, LQR, the Python stand-in network and the recorded NES run (ticks 6000-7000 of the 180 s seed 0 run, circuit recomputed by the stand-in), per-neuron spike counts -> `replay.json`.
- `ball.py`: 4-DOF dynamics with a ball (0.1 kg) on a 0.3 m string hanging from the tip of link 2 (sympy Lagrangian; matches dp_env.dynamics to 1e-10 at ball mass 0).
- `ballrun.py`: old 6-state controllers with the ball (fall).
- `lqr8.py`, `net8.py`: 8-state LQR (adds ball angle and speed) and hand-derived 16-population network by the same formulas as dp_derive.py; `recipe8.json` is the result (decoder constant scaled by the measured gain ratio, as A1).
- `ballgen.py`: ball runs -> `ball.json`; `replay_template.html`: page template (`__DATA__`, `__BALL__` filled from the two JSON files; not committed, large).
Python stand-in only; nothing here was run in NES.
