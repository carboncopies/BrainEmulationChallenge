# lean_proof: why "50% cue completion with fast termination by weights alone" fails in the threshold model (Lean 4, machine-checked)

**Scope, read first.** Everything here is proved for ONE idealised model class: k assembly cells,
nonnegative weights, a cell fires when the summed input from currently firing cells reaches a
threshold (optionally through an input cap), instantaneous synchronous updates, **no inhibition
inside the assembly, no adaptation, no short-term plasticity**, and (unless a separate sustain
threshold is named) one threshold for recruiting and for sustaining. It says **nothing** about
NES or conductance-based spiking networks in general; it shows what must be added (hysteresis
or a non-cooperative slow variable) for a window to exist at all.

Weights and thresholds are natural numbers (in the instances: units of 0.1 nS). Rational values
reduce to this by a common scale factor; real-valued weights are not formally covered.

## Model (AssemblyProof/Model.lean)
- `W j i` = weight from cell j to cell i, `inp k W S i` = Σ_{j<k, j∈S} W j i.
- `fire k W T cap S i` = (T ≤ min cap (inp k W S i)). Big `cap` = no cap.
- With cue C held: `stepC` = cue cells forced on, others by `fire`. `traj C n` = state at step n.
- `Completes C` = at some step all k cells fire. After cue removal the dynamics is `fire` alone.

## What is proved (all with `lake build`, no `sorry`, no `native_decide`)
| Theorem | Plain statement |
|---|---|
| `traj_mono_cue`, `traj_grows`, `completes_of_superset` | Monotonicity: a bigger cue gives a bigger firing set at every step; while the cue is held the firing set only grows; if C completes, every superset of C completes (so if C fails, every subset of C fails). |
| `completion_forces_ignition`, `anyM_completion_forces_ignition` (**Theorem A**) | If every cell can be recruited by some cue that does not contain it (true whenever every m-of-k cue completes, any m < k, cascades allowed), then once all cells fire they fire forever after the cue is removed. **With one threshold, no cue size gives completion plus termination**: 50% and 75% alike. Holds for any k, any cap, any weight bound. |
| `one_step_bound` (**Theorem B**) | If every m-subset of the other k-1 cells drives cell i over Tc in ONE step (zero self-weight), then (k-1)·Tc ≤ m·(in-sum of i). For k = 17: every column sum ≥ 16·Tc/m. |
| `hysteresis_needed`, `no_window_without_hysteresis` | Under the same one-step hypothesis, letting the all-on state die needs a sustain threshold Ts with (k-1)·Tc < m·Ts, i.e. Ts/Tc > (k-1)/m (> 1.78 for 9-of-17, > 1.23 for 13-of-17). With Ts = Tc it is impossible. |
| `ceiling_bound` | Weights ≤ wmax and some m-cue drives i to Tc ⇒ Tc ≤ m·wmax. |
| `a17_half_cue_column_sum` (Instances) | 9-of-17 one-step completion at Tc = 13.6 nS ⇒ every in-sum > 24.1 nS (> 23.7 at 13.4 nS), above the observed ignition range 16.5–17.4 nS. |
| `a17_75_cue_column_sum` | 13-of-17 at 13.6 nS ⇒ in-sum > 16.7 nS only: **not** excluded by this bound (consistent with the 75% window seen in simulation, which itself needs hysteresis by Theorem A). |
| `k42_two_cue_ceiling` + examples | 2 cue cells at ≤ 6.86 nS give ≤ 13.72 nS: infeasible at T = 16.5 and 15.0, feasible only if T_eff ≤ 13.72. |
| `w4_*` (counterexample) | k = 4, m = 2: every 2-cue completes by a cascade, yet one cell gets only 1 < T = 2 from a worst 2-cue in one step. So the "worst m-subset ≥ T" condition is **one-step only**. The same network ignites forever (Theorem A instance). |

## What is NOT proved (be careful when citing)
- **Not about NES.** NMDA nonlinearity, adaptation, delayed inhibition, short-term depression, noise and conductance dynamics are all outside the model; any of them can create the hysteresis that Theorem A says is required.
- **ρ is not formalised.** Theorem B bounds every column sum (hence the minimum column sum). ρ ≥ min column sum (Collatz–Wielandt / Perron for nonnegative matrices) is standard but is cited, not machine-checked here.
- **The cascade numbers ρ 20.4 (s66666) / 21.3 (s77777) from PHASE1_RESULTS C3 are NOT checked.** They come from a random local search, not a proof. Under cascades the only machine-checked bound is Theorem A (in-sum ≥ T for every cell, from the all-on state), which does not distinguish 50% from 75%.
- The ignition range 16.5–17.4 nS and T_eff 13.4–13.6 nS are empirical inputs from the stored simulations, used only as numbers in the arithmetic.
- "Silent for smaller cues": monotonicity allows it (sub-cues of a completing cue may fail); "silent for other cues" (non-nested, e.g. a different 9-of-17 cue) is not addressed by monotonicity at all. Theorem A shows the obstacle is not selectivity but termination.

## Part 2: existence side (AssemblyProof/Mechanisms.lean, AssemblyProof/Windows.lean)
Same toy model with uniform weights, cue held 2 steps, no noise or background input, plus ONE
non-cooperative variable. `net_eq_cls` proves that for ANY cue of size c the network reduces to
two classes (cue cells and non-cue cells). So every theorem below covers **all** C(17,9) and
C(17,4) cues, not one sample cue. `windowB_sound` turns a `decide`-checked class computation into:
every 9-cue completes, then all cells are silent forever from some step on; every 4-cue recruits
no non-cue cell, ever.

| Mechanism | Proved | Fails (proved) when |
|---|---|---|
| (a) sustain threshold Ts > Tc | **symbolic, any k, m, s, w**: window iff s·w < Tc ≤ m·w and Ts > (k−1)·w (`hyst_window_general`) | Ts ≤ (k−1)w: all on at step 2 (`hyst_cls2_burns`, `hyst_fail_net`) |
| (b) short-term depression | instance + sweeps d = 1..10, T = 41..90 (`depl_*`) | d = 0 ignites forever; T = 40 lets the 4-cue recruit; T = 91 never completes |
| (c) adaptation | instance + exact event length ⌊((k−1)w−T)/α⌋+1 for α = 1..100 | α = 0 ignites forever |
| (d) delayed global inhibition | instance + sweep γ = 1..4, L = 1..6, event length exactly L | γ = 0 ignites forever |

The parameter inequalities, and which ones are proved versus derived by hand, are in **DESIGN_CONDITIONS.md**.
Not covered: noise or background input, heterogeneous weights (existence part), continuous time,
NMDA/conductances, and the inter-cue recovery conditions (derived, not checked). Some proofs use
Lean's standard `Classical.choice` axiom through `simp` lemmas; there is still no `sorry` and no `native_decide`.

## Run
```
export PATH=$HOME/.elan/bin:$PATH     # elan installed user-level in ~/.elan, no system changes
cd lean_proof && lake build           # ~10 s; Lean core 4.36.0 only, no Mathlib
lake env lean CheckAxioms.lean        # standard axioms only (propext, Quot.sound, Classical.choice)
```
Files: `AssemblyProof/Sums.lean` (finite sums, rotation, index-skipping), `AssemblyProof/Model.lean`
(model, Theorems A and B), `AssemblyProof/Instances.lean` (k = 17 numbers, K42, 4-cell counterexample),
`AssemblyProof/Mechanisms.lean` (framework, reduction, checkers), `AssemblyProof/Windows.lean` (four mechanisms).
