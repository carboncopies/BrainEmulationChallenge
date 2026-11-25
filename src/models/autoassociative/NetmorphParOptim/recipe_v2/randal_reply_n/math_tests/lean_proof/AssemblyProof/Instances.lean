/-
  Concrete instances, checked by `decide` (kernel evaluation) or `omega`.
  Same model-class caveat as Model.lean: threshold units, instantaneous, no inhibition inside
  the assembly, no adaptation, no short-term plasticity. Not a statement about NES.
  Units below: 0.1 nS (so 136 = 13.6 nS).
-/
import AssemblyProof.Model

namespace Assembly

/-! ## 1. A17, 50% vs 75% cues under ONE-STEP completion (Theorem B with k = 17) -/

/-- 50% cue (9 of 17), Tc = 13.6 nS: every member's in-sum must exceed 17.4 nS (the top of the
    observed ignition range 16.5-17.4). Exact bound: 16·13.6/9 = 24.18 nS. -/
theorem a17_half_cue_column_sum (W : Nat → Nat → Nat) (i : Nat) (hi : i < 17) (hdiag : W i i = 0)
    (h : ∀ C, C i = false → card 17 C = 9 → 136 ≤ inp 17 W C i) :
    241 < inp 17 W full i := by
  have : 16 * 136 ≤ 9 * inp 17 W full i := one_step_bound 16 9 136 i W (by decide) (by decide) hi hdiag h
  omega

/-- Same with the lower calibration Tc = 13.4 nS: in-sum > 23.8 nS. -/
theorem a17_half_cue_column_sum_134 (W : Nat → Nat → Nat) (i : Nat) (hi : i < 17)
    (hdiag : W i i = 0) (h : ∀ C, C i = false → card 17 C = 9 → 134 ≤ inp 17 W C i) :
    237 < inp 17 W full i := by
  have : 16 * 134 ≤ 9 * inp 17 W full i := one_step_bound 16 9 134 i W (by decide) (by decide) hi hdiag h
  omega

/-- 75% cue (13 of 17), Tc = 13.6 nS: the same bound only gives in-sum ≥ 16.74 nS, which is
    BELOW 17.4 nS, so the 75% case is not excluded by this bound (consistent with the
    observed 15.8-17.4 window, which needs hysteresis to exist at all: see Theorem A). -/
theorem a17_75_cue_column_sum (W : Nat → Nat → Nat) (i : Nat) (hi : i < 17) (hdiag : W i i = 0)
    (h : ∀ C, C i = false → card 17 C = 13 → 136 ≤ inp 17 W C i) :
    167 < inp 17 W full i := by
  have : 16 * 136 ≤ 13 * inp 17 W full i := one_step_bound 16 13 136 i W (by decide) (by decide) hi hdiag h
  omega

example : ¬ (13 * 174 < 16 * 136) := by decide   -- 75%: bound does not exceed 17.4 nS
example : 9 * 174 < 16 * 136 := by decide        -- 50%: bound exceeds 17.4 nS

/-- Hysteresis needed for a 50% window (one-step completion, k = 17): Ts/Tc > 16/9 ≈ 1.78. -/
theorem a17_half_cue_hysteresis (W : Nat → Nat → Nat) (Tc Ts i : Nat) (hi : i < 17)
    (hdiag : W i i = 0) (h : ∀ C, C i = false → card 17 C = 9 → Tc ≤ inp 17 W C i)
    (hdie : inp 17 W full i < Ts) : 16 * Tc < 9 * Ts :=
  hysteresis_needed 16 9 Tc Ts i W (by decide) (by decide) (by decide) hi hdiag h hdie

/-! ## 2. K42 ceiling arithmetic: 2 cue cells at ≤ 6.86 nS give at most 13.72 nS -/

theorem k42_two_cue_ceiling (W : Nat → Nat → Nat) (C : CellSet) (k Tc i : Nat)
    (hw : ∀ j, j < k → W j i ≤ 686) (hcard : card k C = 2) (hdrive : Tc ≤ inp k W C i) :
    Tc ≤ 1372 := ceiling_bound k 2 Tc 686 i W C hw hcard hdrive

example : ¬ (1650 ≤ 2 * 686) := by decide  -- infeasible at T = 16.5 nS
example : ¬ (1500 ≤ 2 * 686) := by decide  -- infeasible at T = 15.0 nS
example : 1370 ≤ 2 * 686 := by decide      -- feasible only if T_eff ≤ 13.72 nS

/-! ## 3. Counterexample: the worst-m-subset bound is ONE-STEP only.
    k = 4, m = 2, T = 2, edges 0→1 (1), 1→2 (2), 2→0 (2), 2→3 (2), 3→1 (1), no cap.
    Every 2-of-4 cue completes by a cascade, yet cue {0,2} gives cell 1 only 1 < T in one step.
    And, as Theorem A predicts, the all-on state is self-sustaining (no termination). -/

def W4 : Nat → Nat → Nat
  | 0, 1 => 1
  | 1, 2 => 2
  | 2, 0 => 2
  | 2, 3 => 2
  | 3, 1 => 1
  | _, _ => 0

/-- Cue given by the bits of `b`. -/
def mask (b : Nat) : CellSet := fun j => b.testBit j

theorem w4_every_2cue_completes :
    ∀ b, b < 16 → card 4 (mask b) = 2 → ∀ i, i < 4 → traj 4 W4 2 1000 (mask b) 4 i = true := by
  decide

theorem w4_one_step_fails : inp 4 W4 (mask 5) 1 < 2 := by decide   -- mask 5 = {0, 2}

theorem w4_full_self_sustains : ∀ i, i < 4 → fire 4 W4 2 1000 full i = true := by decide

/-- Theorem A applied to the instance: once all four fire and the cue is gone, they fire forever. -/
theorem w4_never_terminates : ∀ t i, i < 4 → iter (fire 4 W4 2 1000) t full i = true :=
  never_terminates w4_full_self_sustains full (fun _ _ => rfl)

end Assembly
