# DELETE ME: weight-space programming tooling (temporary branch)

This branch only exists so Randal's AI can reuse the scripts we used while developing the
Pong and inverted-double-pendulum weight-space work, instead of reinventing them.
Nothing here is reviewed or meant to be merged. Delete the branch when it has been copied.

## Where the real code is (other branches, same repo)
- `feature/pong-netmorph` (draft MR !41): `src/models/pong_netmorph/`: Pong env, hand-wired LIFC controller,
  NES loop helper, Netmorph growth and transplant scripts, recipes, `output/weightspace_log.md`.
- `feature/double-pendulum` (work in progress): `src/models/double_pendulum/`: plant, LQR, derivation of
  spiking weights from the LQR gain, NES runner, speed measurement, `weightspace_log.md`.
- NES fixes we needed (repo BrainGenix-NES): `fix/modelsave-edited-weights`, `feature/windowed-getspiketimes`.
- NES notes (repo dev_frame): `docs/pong-netmorph-learnings`.

## What is in this folder
- `pendulum_nes_harness/`: encoder (state to signed population spike rates), decoder (two output
  groups to a clipped force), pluggable control loop, and a pure-Python LIF stand-in for smoke tests.
  Written by a Claude Haiku worker; checked with py_compile and its own self-test only.
- `lqr_crosscheck/`: an independent numpy/scipy derivation of the linearised cart + double pendulum,
  LQR gains and a 180 s nonlinear run. Uses 0.1 kg frictionless links, unlike the main plant (0.2 kg, friction).
- `robustness_tests/`: stress tests (sensor noise, jittered spikes, bigger kicks, start offsets) for the
  spiking controller and the results table. These scripts import `dp_env`, `dp_spiking`, `dp_codec` from
  `src/models/double_pendulum/` on `feature/double-pendulum`; copy them there to run.
- `agent_launch_examples/`: how we started OpenCode worker agents per worktree. They reference a session
  scratch folder that will not exist for you; treat them as examples.

## Caveats
- The widened-input-range experiment is still running and is not included.
- Numbers in `robustness_tests/RESULTS.md` come from the Python stand-in, not NES.
