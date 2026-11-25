# Design conditions for a "complete from 50%, die fast, ignore 25%" window (toy threshold model)

**Scope.** These are conditions in a toy model (`AssemblyProof/Mechanisms.lean`, `Windows.lean`):
k cells, uniform excitatory weight w between all pairs, synchronous discrete steps,
cue held for 2 steps, **no noise and no background input**, one added slow variable per
mechanism. They are NOT NES results. Use them as hypotheses to test in the simulator, not as
predictions of its numbers. Toy "steps" are not milliseconds; units are abstract (0.1 nS in (a)).

Notation: k = 17 assembly cells, m = 9 (completing cue), s = 4 (cue that must stay silent),
w = pair weight, D = all-on event length in steps.

Baseline (already proved, `Model.lean`): with ONE threshold and no slow variable, any completion
means the all-on state never stops. So each mechanism must do two jobs: allow recruitment
from m cells, and make the all-on state unstable.

## Shared condition (every mechanism; recruitment and silence at rest)
**s · w_rest < T_recruit ≤ m · w_rest**, i.e. 4·w < T ≤ 9·w. Here w_rest is the pair drive with
the slow variable at rest. This is the one-step recruitment window. It is proved exactly for (a)
and checked by a sweep for (b): every T from 41 to 90 works at w·X = 10, and T = 40 and T = 91 fail.

## (a) Separate sustain threshold (hysteresis): PROVED symbolically, any k, m, s, w
- Window exists **iff** s·w < Tc ≤ m·w **and** Ts > (k−1)·w (`hyst_window_general`, with converses
  `hyst_cls2_burns`, `hyst_s_recruits`).
- Equivalent ratio: **Ts / Tc > (k−1)/m = 16/9 ≈ 1.78** for 9-of-17 (1.23 for 13-of-17).
- Event: all on for 1 step, silent from step 2. Instance: w 1.5, Tc 13.5, Ts 24.1 (nS); Ts = 24.0 ignites forever.

## (b) Short-term depression (output w·x, x drops d per firing step, recovers r per silent step, max X)
Proved: an instance window for all 9-of-17 and 4-of-17 cues; the sweep d = 1..10; the sweep T = 41..90.
Proved failures: d = 0 ignites forever; T = 40 lets the 4-cue recruit; T = 91 never completes.
- Recruit / silence: **s·w·X < T ≤ m·w·X** (sweep-checked).
- Termination: **(k−1)·w·x_floor < T** (derived). In the toy x_floor = 0, so any d ≥ 1 terminates (sweep-checked).
  If the real depression saturates at a nonzero steady state x_ss, you need (k−1)·w·x_ss < T.
- Event length ≈ (X − T/((k−1)w))/d + 1 steps (derived, ±1 step). Checked values at X 10, T 80:
  d 1 gives 6, d 2 gives 3, d 4 gives 2 (python mirror; d 2 is `depl_timing`: on at steps 1–3, silent from 5).
- Re-use (derived, NOT machine-checked): the next cue completes only after the cue cells' resources
  recover to x ≥ T/(m·w). The inter-cue interval must be ≥ (T/(m·w) − x_end)/r steps.

## (c) Adaptation (fire iff T + a ≤ input; a += α per firing step, a −= β per silent step)
Proved: an instance window; the sweep of exact event length; the failure at α = 0 (ignites forever).
- Recruit / silence: s·w < T ≤ m·w.
- Event length is exactly **D = ⌊((k−1)·w − T)/α⌋ + 1** steps, proved for every α = 1..100 at w 10, T 85
  (`adapt_duration`). For a target D_max: **α > ((k−1)·w − T)/D_max**.
- Termination: needs α > 0. With a saturating adaptation of maximum a_max, you need
  **T + a_max > (k−1)·w** (derived).
- Re-use (derived, NOT checked): the residual adaptation must have decayed so that T + a_residual ≤ m·w.
  That requires an interval ≥ (a_end − (m·w − T))/β steps.

## (d) Delayed global inhibition (fire iff T + γ·(total output L steps ago) ≤ input)
Proved: an instance window; the sweep γ = 1..4 × L = 1..6 (all windows, event length exactly L);
the failure at γ = 0 (ignites forever).
- Recruit before inhibition arrives: **L ≥ recruitment time** (1 step here). Recruitment uses
  inhibition from L steps earlier, which is still zero.
- Termination: **γ · (cue-phase total output) > (k−1)·w − T**, i.e. inhibition driven by the cue alone already
  overcomes the excess drive (derived; in the instances γ·m·w = 9 > 16 − 9 = 7).
- Event length = **L** steps (sweep-checked). So the delay sets the event duration directly.
- Re-use: the interval must be ≥ L, so the buffer clears (derived).

## What is not covered
Noise or background input, which could re-ignite a recovering network (in the toy a silent
network has zero input). Also not covered: heterogeneous weights (only uniform weights here; the
heterogeneous necessity bounds are in `Model.lean`), conductance/NMDA dynamics, continuous time,
and combinations of mechanisms. The inter-cue (re-use) conditions are derived by hand, not checked.
