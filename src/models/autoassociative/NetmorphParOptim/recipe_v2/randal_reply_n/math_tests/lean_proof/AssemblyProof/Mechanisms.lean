/-
  EXISTENCE SIDE. Same toy model as Model.lean (instantaneous synchronous threshold units,
  uniform excitatory weights inside a k-cell assembly, no noise, no background input), now with
  ONE added non-cooperative variable per mechanism:
    (a) hysteresis: separate sustain threshold Ts for a cell that is already firing;
    (b) short-term depression: per-cell resource x scales the cell's output, drops while firing;
    (c) adaptation: per-cell threshold increment a, grows while firing, decays otherwise;
    (d) delayed global inhibition: inhibition proportional to total output L steps ago.
  NOT a model of NES. Results are existence proofs in this toy class plus parameter conditions.

  Framework: every cell carries a state `Bool × Nat` (firing flag, slow variable); an optional
  global state `List Nat` (delay buffer). The cue C is clamped on for steps 0..tc-1.
  `net_eq_cls` proves that for ANY cue C of size c the whole network is described by two
  class states (cue cells, non-cue cells), so statements "for every 9-of-17 cue" reduce to a
  finite computation checked by `decide`.
-/
import AssemblyProof.Model

namespace Assembly

abbrev CState := Bool × Nat
abbrev GState := List Nat

/-- A uniform-assembly mechanism. `out s` = output of a cell in state s to EACH other cell;
    `upd clamp s I g` = next state given clamp flag, own state, summed input from the other
    cells, global state; `gupd g tot` = next global state given total output. -/
structure Mech where
  out : CState → Nat
  upd : Bool → CState → Nat → GState → CState
  gupd : GState → Nat → GState
  rest : CState
  cueInit : CState
  g0 : GState

/-- Full network: k cells, cue C held for steps 0..tc-1. -/
def netStep (M : Mech) (k tc : Nat) (C : CellSet) (t : Nat) (st : (Nat → CState) × GState) :
    (Nat → CState) × GState :=
  (fun i => M.upd (C i && decide (t+1 < tc)) (st.1 i)
      (sumTo k (fun j => M.out (st.1 j)) - M.out (st.1 i)) st.2,
   M.gupd st.2 (sumTo k (fun j => M.out (st.1 j))))

def net (M : Mech) (k tc : Nat) (C : CellSet) : Nat → (Nat → CState) × GState
  | 0 => (fun j => if C j then M.cueInit else M.rest, M.g0)
  | t+1 => netStep M k tc C t (net M k tc C t)

/-- Two-class (cue / non-cue) dynamics for a cue of size c. -/
def clsStep (M : Mech) (k c tc t : Nat) (x : CState × CState × GState) : CState × CState × GState :=
  (M.upd (decide (t+1 < tc)) x.1 (c * M.out x.1 + (k - c) * M.out x.2.1 - M.out x.1) x.2.2,
   M.upd false x.2.1 (c * M.out x.1 + (k - c) * M.out x.2.1 - M.out x.2.1) x.2.2,
   M.gupd x.2.2 (c * M.out x.1 + (k - c) * M.out x.2.1))

def cls (M : Mech) (k c tc : Nat) : Nat → CState × CState × GState
  | 0 => (M.cueInit, M.rest, M.g0)
  | t+1 => clsStep M k c tc t (cls M k c tc t)

theorem card_le (n : Nat) (C : CellSet) : card n C ≤ n := by
  induction n with
  | zero => exact Nat.le_refl _
  | succ n ih =>
    have hc : card (n+1) C = card n C + (if C n then 1 else 0) := rfl
    rw [hc]; split <;> omega

theorem sum_two_class (k : Nat) (C : CellSet) (p q : Nat) :
    sumTo k (fun j => if C j then p else q) = card k C * p + (k - card k C) * q := by
  induction k with
  | zero => simp [sumTo, card]
  | succ n ih =>
    have hle := card_le n C
    have hc : card (n+1) C = card n C + (if C n then 1 else 0) := rfl
    rw [sumTo_succ, ih, hc]
    cases C n
    · simp only [Bool.false_eq_true, ↓reduceIte, Nat.add_zero]
      rw [show n + 1 - card n C = (n - card n C) + 1 by omega, Nat.add_mul, Nat.one_mul]; omega
    · simp only [↓reduceIte]
      rw [show n + 1 - (card n C + 1) = n - card n C by omega, Nat.add_mul, Nat.one_mul]; omega

/-- **Reduction theorem.** For every cue C, at every step, each cell's state equals the class
    state of its class, and the global state equals the class-level global state. -/
theorem net_eq_cls (M : Mech) (k tc : Nat) (C : CellSet) (t : Nat) :
    (∀ j, j < k → (net M k tc C t).1 j =
        if C j then (cls M k (card k C) tc t).1 else (cls M k (card k C) tc t).2.1) ∧
    (net M k tc C t).2 = (cls M k (card k C) tc t).2.2 := by
  induction t with
  | zero => exact ⟨fun j _ => rfl, rfl⟩
  | succ t ih =>
    obtain ⟨h1, h2⟩ := ih
    have htot : sumTo k (fun j => M.out ((net M k tc C t).1 j)) =
        card k C * M.out (cls M k (card k C) tc t).1
          + (k - card k C) * M.out (cls M k (card k C) tc t).2.1 := by
      rw [sumTo_congr (g := fun j => if C j then M.out (cls M k (card k C) tc t).1
            else M.out (cls M k (card k C) tc t).2.1) (fun j hj => by
          rw [h1 j hj]; split <;> rfl)]
      exact sum_two_class k C _ _
    refine ⟨fun j hj => ?_, ?_⟩
    · show M.upd (C j && decide (t+1 < tc)) ((net M k tc C t).1 j)
          (sumTo k (fun j => M.out ((net M k tc C t).1 j)) - M.out ((net M k tc C t).1 j))
          (net M k tc C t).2 = _
      rw [htot, h1 j hj, h2]
      cases C j
      · simp only [Bool.false_and, Bool.false_eq_true, ↓reduceIte]; rfl
      · simp only [Bool.true_and, ↓reduceIte]; rfl
    · show M.gupd (net M k tc C t).2 (sumTo k (fun j => M.out ((net M k tc C t).1 j))) = _
      rw [htot, h2]; rfl

/-- After the cue is off the class step does not depend on t. -/
theorem clsStep_free (M : Mech) (k c tc t : Nat) (x : CState × CState × GState)
    (h : tc ≤ t + 1) : clsStep M k c tc t x = clsStep M k c 0 0 x := by
  have : decide (t+1 < tc) = false := decide_eq_false (by omega)
  simp only [clsStep, this]; rfl

/-- A cue-free fixed point reached after the cue is off is kept forever. -/
theorem cls_stays (M : Mech) (k c tc t0 : Nat) (x : CState × CState × GState)
    (ht0 : tc ≤ t0 + 1) (hx : cls M k c tc t0 = x) (hfix : clsStep M k c 0 0 x = x) :
    ∀ n, cls M k c tc (t0 + n) = x := by
  intro n
  induction n with
  | zero => exact hx
  | succ n ih =>
    show clsStep M k c tc (t0 + n) (cls M k c tc (t0 + n)) = x
    rw [ih, clsStep_free M k c tc (t0+n) x (by omega), hfix]

/-! ## Bounded search helpers with soundness -/

def allUpTo (f : Nat → Bool) : Nat → Bool
  | 0 => f 0
  | n+1 => allUpTo f n && f (n+1)

def anyUpTo (f : Nat → Bool) : Nat → Bool
  | 0 => f 0
  | n+1 => anyUpTo f n || f (n+1)

theorem allUpTo_sound (f : Nat → Bool) (n : Nat) (h : allUpTo f n = true) :
    ∀ t, t ≤ n → f t = true := by
  induction n with
  | zero => intro t ht; have : t = 0 := by omega
            subst this; exact h
  | succ n ih =>
    intro t ht
    simp only [allUpTo, Bool.and_eq_true] at h
    by_cases htn : t ≤ n
    · exact ih h.1 t htn
    · have : t = n + 1 := by omega
      subst this; exact h.2

theorem anyUpTo_sound (f : Nat → Bool) (n : Nat) (h : anyUpTo f n = true) :
    ∃ t, t ≤ n ∧ f t = true := by
  induction n with
  | zero => exact ⟨0, Nat.le_refl _, h⟩
  | succ n ih =>
    simp only [anyUpTo, Bool.or_eq_true] at h
    rcases h with h | h
    · obtain ⟨t, ht, hf⟩ := ih h; exact ⟨t, by omega, hf⟩
    · exact ⟨n+1, Nat.le_refl _, h⟩

/-! ## Outcome checkers (class level) -/

/-- Both classes fire at step t: every one of the k cells fires. -/
def allOnB (M : Mech) (k c tc t : Nat) : Bool := (cls M k c tc t).1.1 && (cls M k c tc t).2.1.1

/-- At step t the cue is off, nobody fires, and the class state is a cue-free fixed point. -/
def deadFixB (M : Mech) (k c tc t : Nat) : Bool :=
  decide (tc ≤ t + 1) && !(cls M k c tc t).1.1 && !(cls M k c tc t).2.1.1 &&
    (clsStep M k c 0 0 (cls M k c tc t) == cls M k c tc t)

/-- At step t the cue is off, everybody fires, and the state is a cue-free fixed point. -/
def burnFixB (M : Mech) (k c tc t : Nat) : Bool :=
  decide (tc ≤ t + 1) && (cls M k c tc t).1.1 && (cls M k c tc t).2.1.1 &&
    (clsStep M k c 0 0 (cls M k c tc t) == cls M k c tc t)

/-- The window property for cue size m (complete, then die) and smaller cue size s (non-cue
    cells never recruited, then all quiet), searched up to horizon H. -/
def windowB (M : Mech) (k m s tc H : Nat) : Bool :=
  anyUpTo (fun t => allOnB M k m tc t) H &&
  anyUpTo (fun t => deadFixB M k m tc t) H &&
  anyUpTo (fun t => deadFixB M k s tc t && allUpTo (fun u => !(cls M k s tc u).2.1.1) t) H

/-! ## Transfer from class level to the full network, for every cue of the given size -/

theorem allOn_net (M : Mech) (k tc t : Nat) (C : CellSet) (h : allOnB M k (card k C) tc t = true) :
    ∀ i, i < k → ((net M k tc C t).1 i).1 = true := by
  intro i hi
  simp only [allOnB, Bool.and_eq_true] at h
  rw [(net_eq_cls M k tc C t).1 i hi]
  cases C i <;> simp [h.1, h.2]

theorem stays_net (M : Mech) (k tc t0 : Nat) (C : CellSet) (x : CState × CState × GState)
    (ht0 : tc ≤ t0 + 1) (hx : cls M k (card k C) tc t0 = x)
    (hfix : clsStep M k (card k C) 0 0 x = x) :
    ∀ t, t0 ≤ t → ∀ i, i < k → (net M k tc C t).1 i = if C i then x.1 else x.2.1 := by
  intro t ht i hi
  obtain ⟨n, rfl⟩ : ∃ n, t = t0 + n := ⟨t - t0, by omega⟩
  rw [(net_eq_cls M k tc C (t0+n)).1 i hi, cls_stays M k _ tc t0 x ht0 hx hfix n]

theorem dead_net (M : Mech) (k tc t0 : Nat) (C : CellSet) (h : deadFixB M k (card k C) tc t0 = true) :
    ∀ t, t0 ≤ t → ∀ i, i < k → ((net M k tc C t).1 i).1 = false := by
  simp only [deadFixB, Bool.and_eq_true, decide_eq_true_eq, Bool.not_eq_true',
    beq_iff_eq] at h
  obtain ⟨⟨⟨ht0, ha⟩, hb⟩, hfix⟩ := h
  intro t ht i hi
  rw [stays_net M k tc t0 C _ ht0 rfl hfix t ht i hi]
  cases C i <;> simp [ha, hb]

theorem burn_net (M : Mech) (k tc t0 : Nat) (C : CellSet) (h : burnFixB M k (card k C) tc t0 = true) :
    ∀ t, t0 ≤ t → ∀ i, i < k → ((net M k tc C t).1 i).1 = true := by
  simp only [burnFixB, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq] at h
  obtain ⟨⟨⟨ht0, ha⟩, hb⟩, hfix⟩ := h
  intro t ht i hi
  rw [stays_net M k tc t0 C _ ht0 rfl hfix t ht i hi]
  cases C i <;> simp [ha, hb]

/-- What `windowB = true` means for the full network:
    (1) every m-cue completes (all k cells fire at a common step),
    (2) every m-cue's activity dies and stays dead from some step ≤ H on,
    (3) under every s-cue no non-cue cell ever fires, and all activity stops by step H. -/
theorem windowB_sound (M : Mech) (k m s tc H : Nat) (h : windowB M k m s tc H = true) :
    (∀ C, card k C = m → ∃ t, t ≤ H ∧ ∀ i, i < k → ((net M k tc C t).1 i).1 = true) ∧
    (∀ C, card k C = m → ∃ t0, t0 ≤ H ∧ ∀ t, t0 ≤ t → ∀ i, i < k → ((net M k tc C t).1 i).1 = false) ∧
    (∀ C, card k C = s → (∀ t i, i < k → C i = false → ((net M k tc C t).1 i).1 = false) ∧
        ∃ t0, t0 ≤ H ∧ ∀ t, t0 ≤ t → ∀ i, i < k → ((net M k tc C t).1 i).1 = false) := by
  simp only [windowB, Bool.and_eq_true] at h
  obtain ⟨⟨h1, h2⟩, h3⟩ := h
  refine ⟨fun C hC => ?_, fun C hC => ?_, fun C hC => ?_⟩
  · obtain ⟨t, ht, hf⟩ := anyUpTo_sound _ H h1
    subst hC; exact ⟨t, ht, allOn_net M k tc t C hf⟩
  · obtain ⟨t, ht, hf⟩ := anyUpTo_sound _ H h2
    subst hC; exact ⟨t, ht, dead_net M k tc t C hf⟩
  · obtain ⟨t0, ht0, hf⟩ := anyUpTo_sound _ H h3
    simp only [Bool.and_eq_true] at hf
    obtain ⟨hdead, hsil⟩ := hf
    subst hC
    have hd := dead_net M k tc t0 C hdead
    refine ⟨fun t i hi hCi => ?_, ⟨t0, ht0, hd⟩⟩
    by_cases htt : t0 ≤ t
    · exact hd t htt i hi
    · have := allUpTo_sound _ t0 hsil t (by omega)
      rw [(net_eq_cls M k tc C t).1 i hi, hCi]
      simpa using this

end Assembly
