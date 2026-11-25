/-
  Existence of a "complete from 9-of-17, die fast, stay silent for 4-of-17" window once ONE
  non-cooperative variable is added. Toy model only (see Mechanisms.lean header); not NES.
  Conventions: k = 17 cells, uniform weight w between all pairs (zero self-weight), cue held
  on for 2 steps (tc = 2), no noise, no background input. Every statement "for every cue C
  with card 17 C = m" is about ALL C(17,m) cues, via `net_eq_cls` + `windowB_sound`.
-/
import AssemblyProof.Mechanisms

namespace Assembly

/-! ## The four mechanisms -/

/-- (a) Hysteresis: a silent cell starts at input ≥ Tc; a firing cell keeps firing only at
    input ≥ Ts. -/
def hyst (w Tc Ts : Nat) : Mech where
  out s := if s.1 then w else 0
  upd cl s I _ := (cl || (if s.1 then decide (Ts ≤ I) else decide (Tc ≤ I)), 0)
  gupd g _ := g
  rest := (false, 0)
  cueInit := (true, 0)
  g0 := []

/-- (b) Short-term depression: output w·x while firing; x drops by d per firing step,
    recovers by r per silent step up to X. Threshold T (single threshold). -/
def depl (w T X d r : Nat) : Mech where
  out s := if s.1 then w * s.2 else 0
  upd cl s I _ := (cl || decide (T ≤ I), if s.1 then s.2 - d else min X (s.2 + r))
  gupd g _ := g
  rest := (false, X)
  cueInit := (true, X)
  g0 := []

/-- (c) Adaptation: fire iff T + a ≤ input; a grows by α per firing step, decays by β per
    silent step. -/
def adapt (w T α β : Nat) : Mech where
  out s := if s.1 then w else 0
  upd cl s I _ := (cl || decide (T + s.2 ≤ I), if s.1 then s.2 + α else s.2 - β)
  gupd g _ := g
  rest := (false, 0)
  cueInit := (true, 0)
  g0 := []

/-- (d) Delayed global inhibition: fire iff T + γ·(total output L steps ago) ≤ input.
    The buffer holds the last L totals (oldest first). -/
def inhib (w T γ L : Nat) : Mech where
  out s := if s.1 then w else 0
  upd cl _ I g := (cl || decide (T + γ * g.headD 0 ≤ I), 0)
  gupd g tot := g.tail ++ [tot]
  rest := (false, 0)
  cueInit := (true, 0)
  g0 := List.replicate L 0

/-! ## Main existence theorems (one instance per mechanism, all cues of the given sizes) -/

-- (a) w = 1.5 nS, Tc = 13.5 nS, Ts = 24.1 nS (units 0.1 nS). Ts/Tc = 1.785 > 16/9.
theorem hyst_window : windowB (hyst 15 135 241) 17 9 4 2 10 = true := by decide
-- (b) w = 1, X = 10 (output up to 10 per cell), T = 80, depletion 2/step, recovery 1/step.
theorem depl_window : windowB (depl 1 80 10 2 1) 17 9 4 2 30 = true := by decide
-- (c) w = 10, T = 85, adaptation +30 per firing step, decay 10 per silent step.
theorem adapt_window : windowB (adapt 10 85 30 10) 17 9 4 2 30 = true := by decide
-- (d) w = 1, T = 9, inhibition gain 1 per unit of total output, delay 2 steps.
theorem inhib_window : windowB (inhib 1 9 1 2) 17 9 4 2 30 = true := by decide

/-- Unpacked statement for (b); the others unpack identically through `windowB_sound`. -/
theorem depl_window_unpacked :
    (∀ C, card 17 C = 9 → ∃ t, t ≤ 30 ∧ ∀ i, i < 17 → ((net (depl 1 80 10 2 1) 17 2 C t).1 i).1 = true) ∧
    (∀ C, card 17 C = 9 → ∃ t0, t0 ≤ 30 ∧ ∀ t, t0 ≤ t → ∀ i, i < 17 →
        ((net (depl 1 80 10 2 1) 17 2 C t).1 i).1 = false) ∧
    (∀ C, card 17 C = 4 → (∀ t i, i < 17 → C i = false → ((net (depl 1 80 10 2 1) 17 2 C t).1 i).1 = false) ∧
        ∃ t0, t0 ≤ 30 ∧ ∀ t, t0 ≤ t → ∀ i, i < 17 → ((net (depl 1 80 10 2 1) 17 2 C t).1 i).1 = false) :=
  windowB_sound _ 17 9 4 2 30 depl_window

/-! ## Exact timing of the instances (completion step 1; last all-on step D; silent from t1) -/

/-- Silent on [t1, t0] and dead fixed point at t0 ⇒ silent forever from t1. -/
theorem silent_from (M : Mech) (k tc t1 t0 : Nat) (C : CellSet)
    (hq : allUpTo (fun u => decide (u < t1) ||
          (!(cls M k (card k C) tc u).1.1 && !(cls M k (card k C) tc u).2.1.1)) t0 = true)
    (hd : deadFixB M k (card k C) tc t0 = true) :
    ∀ t, t1 ≤ t → ∀ i, i < k → ((net M k tc C t).1 i).1 = false := by
  intro t ht i hi
  by_cases h : t0 ≤ t
  · exact dead_net M k tc t0 C hd t h i hi
  · have := allUpTo_sound _ t0 hq t (by omega)
    simp only [Bool.or_eq_true, decide_eq_true_eq, Bool.and_eq_true, Bool.not_eq_true'] at this
    rcases this with h' | ⟨ha, hb⟩
    · omega
    · rw [(net_eq_cls M k tc C t).1 i hi]; cases C i <;> simp [ha, hb]

/-- Event timing checker: all cells on at every step 1..D, not all on at D+1, silent from t1. -/
def timingB (M : Mech) (k m tc D t1 t0 : Nat) : Bool :=
  allUpTo (fun u => u == 0 || allOnB M k m tc u) D && !allOnB M k m tc (D+1) &&
  allUpTo (fun u => decide (u < t1) || (!(cls M k m tc u).1.1 && !(cls M k m tc u).2.1.1)) t0 &&
  deadFixB M k m tc t0

theorem timingB_sound (M : Mech) (k m tc D t1 t0 : Nat) (h : timingB M k m tc D t1 t0 = true) :
    ∀ C, card k C = m →
      (∀ t, 1 ≤ t → t ≤ D → ∀ i, i < k → ((net M k tc C t).1 i).1 = true) ∧
      (∀ t, t1 ≤ t → ∀ i, i < k → ((net M k tc C t).1 i).1 = false) := by
  intro C hC
  subst hC
  simp only [timingB, Bool.and_eq_true] at h
  obtain ⟨⟨⟨hon, _⟩, hq⟩, hd⟩ := h
  refine ⟨fun t h1 hD i hi => ?_, silent_from M k tc t1 t0 C hq hd⟩
  have := allUpTo_sound _ D hon t hD
  simp only [Bool.or_eq_true, beq_iff_eq] at this
  rcases this with h0 | h'
  · omega
  · exact allOn_net M k tc t C h' i hi

-- (a): all on at step 1 only, silent from step 2.
theorem hyst_timing : timingB (hyst 15 135 241) 17 9 2 1 2 2 = true := by decide
-- (b): all on at steps 1-3, silent from step 5 (resources back to full by step 15).
theorem depl_timing : timingB (depl 1 80 10 2 1) 17 9 2 3 5 15 = true := by decide
-- (c): all on at steps 1-3, silent from step 5 (adaptation back to 0 by step 17).
theorem adapt_timing : timingB (adapt 10 85 30 10) 17 9 2 3 5 17 = true := by decide
-- (d): all on at steps 1-2 (= delay L), silent from step 3 (buffer clear by step 5).
theorem inhib_timing : timingB (inhib 1 9 1 2) 17 9 2 2 3 5 = true := by decide

/-! ## Parameter sweeps (each value checked, all cues) -/

/-- (b) Any depletion rate d = 1..10 gives a window (with T = 80, X = 10). -/
theorem depl_sweep_d : ∀ d, d < 11 → 1 ≤ d → windowB (depl 1 80 10 d 1) 17 9 4 2 30 = true := by
  decide
/-- (b) Every threshold with 4·w·X < T ≤ 9·w·X, i.e. T = 41..90, gives a window (d = 2). -/
theorem depl_sweep_T : ∀ T, T < 91 → 41 ≤ T → windowB (depl 1 T 10 2 1) 17 9 4 2 30 = true := by
  decide
set_option maxRecDepth 20000 in
/-- (c) Event length is exactly ⌊((k-1)w - T)/α⌋ + 1 steps for α = 1..100 (w = 10, T = 85). -/
theorem adapt_duration : ∀ α, α < 101 → 1 ≤ α →
    (allOnB (adapt 10 85 α 10) 17 9 2 ((160 - 85) / α + 1) &&
      !allOnB (adapt 10 85 α 10) 17 9 2 ((160 - 85) / α + 2)) = true := by decide
/-- (d) For gains γ = 1..4 and delays L = 1..6: a window, with the all-on event lasting
    exactly L steps (steps 1..L). -/
theorem inhib_sweep : ∀ γ, γ < 5 → 1 ≤ γ → ∀ L, L < 7 → 1 ≤ L →
    (windowB (inhib 1 9 γ L) 17 9 4 2 20 &&
      allOnB (inhib 1 9 γ L) 17 9 2 L && !allOnB (inhib 1 9 γ L) 17 9 2 (L+1)) = true := by decide

/-! ## Boundaries: when the mechanism is too weak, the window disappears (all cues) -/

/-- (a) Ts = 24.0 nS = (k-1)·w: no hysteresis margin; all cells fire forever from step 1. -/
theorem hyst_fail : burnFixB (hyst 15 135 240) 17 9 2 1 = true := by decide
/-- (b) d = 0 (no depletion): ignition forever. -/
theorem depl_fail : burnFixB (depl 1 80 10 0 1) 17 9 2 1 = true := by decide
/-- (b) T = 40 = 4·w·X: a 4-of-17 cue recruits non-cue cells (silence fails). -/
theorem depl_fail_silence : (cls (depl 1 40 10 2 1) 17 4 2 1).2.1.1 = true := by decide
/-- (b) T = 91 > 9·w·X: a 9-of-17 cue never completes (quiet fixed point, never all on). -/
theorem depl_fail_recruit : deadFixB (depl 1 91 10 2 1) 17 9 2 6 = true ∧
    allUpTo (fun t => !allOnB (depl 1 91 10 2 1) 17 9 2 t) 6 = true := by decide
/-- (c) α = 0 (no adaptation): ignition forever. -/
theorem adapt_fail : burnFixB (adapt 10 85 0 10) 17 9 2 1 = true := by decide
/-- (d) γ = 0 (no inhibition): ignition forever. -/
theorem inhib_fail : burnFixB (inhib 1 9 0 2) 17 9 2 3 = true := by decide

/-- Transfer of a failure to the full network, e.g. (a) with Ts = (k-1)·w: for every 9-cue,
    all 17 cells fire at every step ≥ 1. -/
theorem hyst_fail_net : ∀ C, card 17 C = 9 → ∀ t, 1 ≤ t → ∀ i, i < 17 →
    ((net (hyst 15 135 240) 17 2 C t).1 i).1 = true := by
  intro C hC
  exact burn_net _ 17 2 1 C (by rw [hC]; exact hyst_fail)

/-! ## (a) exactly: symbolic conditions for the hysteresis mechanism (any k, m, w, Tc, Ts) -/

theorem hyst_cls1 (k m w Tc Ts : Nat) (_hm : m ≤ k) (hrec : Tc ≤ m * w) :
    cls (hyst w Tc Ts) k m 2 1 = ((true, 0), (true, 0), []) := by
  simp [cls, clsStep, hyst, hrec]

theorem hyst_insum (k m w : Nat) (hm : m ≤ k) (_hk : 1 ≤ k) :
    m * w + (k - m) * w - w = (k - 1) * w := by
  rw [← Nat.add_mul, Nat.add_sub_cancel' hm, Nat.sub_mul, Nat.one_mul]

/-- With one-step recruitment (Tc ≤ m·w), the all-on state at step 1 dies at step 2 iff
    (k-1)·w < Ts, and otherwise persists. -/
theorem hyst_cls2_dies (k m w Tc Ts : Nat) (hm : m ≤ k) (hk : 1 ≤ k) (hrec : Tc ≤ m * w)
    (hdie : (k - 1) * w < Ts) : cls (hyst w Tc Ts) k m 2 2 = ((false, 0), (false, 0), []) := by
  show clsStep (hyst w Tc Ts) k m 2 1 (cls (hyst w Tc Ts) k m 2 1) = _
  rw [hyst_cls1 k m w Tc Ts hm hrec]
  simp only [clsStep, hyst, ↓reduceIte, hyst_insum k m w hm hk]
  simp [Nat.not_le.mpr hdie]

theorem hyst_cls2_burns (k m w Tc Ts : Nat) (hm : m ≤ k) (hk : 1 ≤ k) (hrec : Tc ≤ m * w)
    (hburn : Ts ≤ (k - 1) * w) : cls (hyst w Tc Ts) k m 2 2 = ((true, 0), (true, 0), []) := by
  show clsStep (hyst w Tc Ts) k m 2 1 (cls (hyst w Tc Ts) k m 2 1) = _
  rw [hyst_cls1 k m w Tc Ts hm hrec]
  simp only [clsStep, hyst, ↓reduceIte, hyst_insum k m w hm hk]
  simp [hburn]

theorem hyst_dead_fix (k c w Tc Ts : Nat) (hTc : 0 < Tc) :
    clsStep (hyst w Tc Ts) k c 0 0 ((false, 0), (false, 0), []) = ((false, 0), (false, 0), []) := by
  simp [clsStep, hyst]; omega

theorem hyst_s_cls1 (k s w Tc Ts : Nat) (hsil : s * w < Tc) :
    cls (hyst w Tc Ts) k s 2 1 = ((true, 0), (false, 0), []) := by
  simp [cls, clsStep, hyst, Nat.not_le.mpr hsil]

/-- Silence fails exactly when a small cue reaches Tc: non-cue cells fire at step 1. -/
theorem hyst_s_recruits (k s w Tc Ts : Nat) (hrec : Tc ≤ s * w) :
    (cls (hyst w Tc Ts) k s 2 1).2.1.1 = true := by
  simp [cls, clsStep, hyst, hrec]

theorem hyst_s_cls2 (k s w Tc Ts : Nat) (hs : s ≤ k) (hsil : s * w < Tc)
    (hdie : (k - 1) * w < Ts) : cls (hyst w Tc Ts) k s 2 2 = ((false, 0), (false, 0), []) := by
  show clsStep (hyst w Tc Ts) k s 2 1 (cls (hyst w Tc Ts) k s 2 1) = _
  rw [hyst_s_cls1 k s w Tc Ts hsil]
  have h1 : s * w ≤ k * w := Nat.mul_le_mul_right w hs
  have h2 : (k - 1) * w = k * w - w := by rw [Nat.sub_mul, Nat.one_mul]
  have h3 : s * w - w < Ts := by
    have := Nat.sub_le_sub_right h1 w
    rw [← h2] at this; omega
  simp only [clsStep, hyst, ↓reduceIte]
  simp only [Bool.false_eq_true, ↓reduceIte, Bool.false_or, decide_eq_false_iff_not,
    Nat.not_le, Prod.mk.injEq, and_true]
  simp only [Nat.mul_zero, Nat.add_zero, Nat.sub_zero, show decide (1 + 1 < 2) = false from rfl,
    Bool.false_or, decide_eq_false_iff_not, Nat.not_le]
  exact ⟨h3, hsil⟩

theorem deadFix_of (M : Mech) (k c tc t : Nat) (x : CState × CState × GState)
    (h : cls M k c tc t = x) (hfix : clsStep M k c 0 0 x = x) (ht : tc ≤ t + 1)
    (hx1 : x.1.1 = false) (hx2 : x.2.1.1 = false) : deadFixB M k c tc t = true := by
  simp [deadFixB, h, hfix, hx1, hx2, ht]

/-- **(a) exact design condition, symbolic.** For ANY k, cue sizes m and s ≤ k, weight w and
    thresholds with  s·w < Tc ≤ m·w  and  (k-1)·w < Ts :
    every m-cue completes at step 1 and everything is silent from step 2 on, forever;
    every s-cue recruits no non-cue cell, ever, and everything is silent from step 2 on.
    Conversely (`hyst_cls2_burns`, `hyst_s_recruits`) Ts ≤ (k-1)·w keeps all cells on at
    step 2, and Tc ≤ s·w recruits from the small cue. -/
theorem hyst_window_general (k m s w Tc Ts : Nat) (hk : 1 ≤ k) (hm : m ≤ k) (hs : s ≤ k)
    (hrec : Tc ≤ m * w) (hsil : s * w < Tc) (hdie : (k - 1) * w < Ts) :
    (∀ C, card k C = m → (∀ i, i < k → ((net (hyst w Tc Ts) k 2 C 1).1 i).1 = true) ∧
        ∀ t, 2 ≤ t → ∀ i, i < k → ((net (hyst w Tc Ts) k 2 C t).1 i).1 = false) ∧
    (∀ C, card k C = s → (∀ t i, i < k → C i = false → ((net (hyst w Tc Ts) k 2 C t).1 i).1 = false) ∧
        ∀ t, 2 ≤ t → ∀ i, i < k → ((net (hyst w Tc Ts) k 2 C t).1 i).1 = false) := by
  have hTc : 0 < Tc := by omega
  refine ⟨fun C hC => ⟨?_, ?_⟩, fun C hC => ?_⟩
  · apply allOn_net
    simp [allOnB, hC, hyst_cls1 k m w Tc Ts hm hrec]
  · apply dead_net
    rw [hC]
    exact deadFix_of _ k m 2 2 _ (hyst_cls2_dies k m w Tc Ts hm hk hrec hdie)
      (hyst_dead_fix k m w Tc Ts hTc) (by omega) rfl rfl
  · have hd : ∀ t, 2 ≤ t → ∀ i, i < k → ((net (hyst w Tc Ts) k 2 C t).1 i).1 = false := by
      apply dead_net
      rw [hC]
      exact deadFix_of _ k s 2 2 _ (hyst_s_cls2 k s w Tc Ts hs hsil hdie)
        (hyst_dead_fix k s w Tc Ts hTc) (by omega) rfl rfl
    refine ⟨fun t i hi hCi => ?_, hd⟩
    match t with
    | 0 => rw [(net_eq_cls _ k 2 C 0).1 i hi, hCi]; rfl
    | 1 => rw [(net_eq_cls _ k 2 C 1).1 i hi, hCi, hC, hyst_s_cls1 k s w Tc Ts hsil]; rfl
    | t+2 => exact hd (t+2) (by omega) i hi

/-- (a) at k = 17, 9-cue vs 4-cue: the window exists iff 4w < Tc ≤ 9w and Ts > 16w. -/
example : (4 * 15 < 135 ∧ 135 ≤ 9 * 15) ∧ 16 * 15 < 241 := by decide

end Assembly
