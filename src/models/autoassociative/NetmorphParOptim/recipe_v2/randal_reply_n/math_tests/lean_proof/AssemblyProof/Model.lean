/-
  SCOPE (read first). Everything here is about ONE idealised model class:
    * k assembly cells, indices 0..k-1; nonnegative weights W j i (from j to i), natural numbers
      (any rational weights/thresholds reduce to this by a common scale factor; reals are not covered);
    * a cell fires at step t+1 iff its summed input from cells firing at step t is >= threshold,
      optionally passed through an input cap (min cap input);
    * instantaneous, deterministic, synchronous update; NO inhibition inside the assembly,
      NO adaptation, NO short-term plasticity, NO hysteresis unless stated as a separate threshold.
  It proves nothing about NES / conductance-based spiking networks in general.
-/
import AssemblyProof.Sums

namespace Assembly

/-- A set of cells as a Boolean predicate (only indices < k matter). -/
abbrev CellSet := Nat → Bool

/-- `S ⊆ S'` on the k cells. -/
def Sub (k : Nat) (S S' : CellSet) : Prop := ∀ j, j < k → S j = true → S' j = true

/-- Number of cells of `C` among 0..n-1. -/
def card (n : Nat) (C : CellSet) : Nat := sumTo n (fun j => if C j then 1 else 0)

/-- Σ_{j<n, j ∈ C} a j. -/
def sumOn (n : Nat) (C : CellSet) (a : Nat → Nat) : Nat := sumTo n (fun j => if C j then a j else 0)

/-- Summed input to cell `i` from the firing set `S`; `W j i` = weight j → i. -/
def inp (k : Nat) (W : Nat → Nat → Nat) (S : CellSet) (i : Nat) : Nat := sumOn k S (fun j => W j i)

/-- Everybody fires. -/
def full : CellSet := fun _ => true

/-- One threshold update: fire iff `T ≤ min cap (input)`. Use a huge `cap` for "no cap". -/
def fire (k : Nat) (W : Nat → Nat → Nat) (T cap : Nat) (S : CellSet) : CellSet :=
  fun i => decide (T ≤ min cap (inp k W S i))

/-- Update while the cue `C` is clamped on (cue cells forced, others by threshold). -/
def stepC (k : Nat) (W : Nat → Nat → Nat) (T cap : Nat) (C S : CellSet) : CellSet :=
  fun i => C i || fire k W T cap S i

/-- n-fold iteration of a set map. -/
def iter (f : CellSet → CellSet) : Nat → CellSet → CellSet
  | 0, S => S
  | n+1, S => f (iter f n S)

/-- State at step n when cue `C` is presented (held) from step 0. -/
def traj (k : Nat) (W : Nat → Nat → Nat) (T cap : Nat) (C : CellSet) (n : Nat) : CellSet :=
  iter (stepC k W T cap C) n C

/-- Completion: at some step every member fires. -/
def Completes (k : Nat) (W : Nat → Nat → Nat) (T cap : Nat) (C : CellSet) : Prop :=
  ∃ n, ∀ i, i < k → traj k W T cap C n i = true

/-! ## Part 2: monotonicity -/

theorem sumOn_mono {n : Nat} {C C' : CellSet} (a : Nat → Nat) (h : Sub n C C') :
    sumOn n C a ≤ sumOn n C' a := by
  apply sumTo_mono
  intro j hj
  cases hC : C j
  · simp only [Bool.false_eq_true, ↓reduceIte]; exact Nat.zero_le _
  · simp [h j hj hC]

theorem inp_mono {k : Nat} {W : Nat → Nat → Nat} {S S' : CellSet} (i : Nat) (h : Sub k S S') :
    inp k W S i ≤ inp k W S' i := sumOn_mono _ h

theorem fire_mono {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat} {S S' : CellSet} (h : Sub k S S') :
    ∀ i, fire k W T cap S i = true → fire k W T cap S' i = true := by
  intro i hi
  simp only [fire, decide_eq_true_eq] at hi ⊢
  have := inp_mono (W := W) i h
  omega

theorem stepC_mono {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat} {C C' S S' : CellSet}
    (hC : Sub k C C') (hS : Sub k S S') : Sub k (stepC k W T cap C S) (stepC k W T cap C' S') := by
  intro j hj h
  simp only [stepC, Bool.or_eq_true] at h ⊢
  rcases h with h | h
  · exact Or.inl (hC j hj h)
  · exact Or.inr (fire_mono hS j h)

/-- (2a) Bigger cue ⇒ bigger firing set at every step. -/
theorem traj_mono_cue {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat} {C C' : CellSet}
    (hC : Sub k C C') (n : Nat) : Sub k (traj k W T cap C n) (traj k W T cap C' n) := by
  induction n with
  | zero => exact hC
  | succ n ih => exact stepC_mono hC ih

/-- (2b) While the cue is held, the firing set only grows in time. -/
theorem traj_grows {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat} (C : CellSet) (n : Nat) :
    Sub k (traj k W T cap C n) (traj k W T cap C (n+1)) := by
  induction n with
  | zero =>
    intro j _ h
    show (C j || fire k W T cap C j) = true
    rw [Bool.or_eq_true]
    exact Or.inl h
  | succ n ih => exact stepC_mono (fun _ _ h => h) ih

/-- (2c) A cue that contains a completing cue also completes. Equivalently (contrapositive):
    if a cue fails to complete, every sub-cue fails too. Monotonicity says NOTHING about
    cues that are not nested (e.g. two different 50% cues). -/
theorem completes_of_superset {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat} {C C' : CellSet}
    (hC : Sub k C C') (h : Completes k W T cap C) : Completes k W T cap C' := by
  obtain ⟨n, hn⟩ := h
  exact ⟨n, fun i hi => traj_mono_cue hC n i hi (hn i hi)⟩

/-! ## Part 2 core: completion ⇒ the all-on state is self-sustaining (no termination) -/

/-- If cell `i` ever fires without being a cue cell, then the all-on state alone drives `i`
    over threshold. -/
theorem recruited_full {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat} {C : CellSet} {n i : Nat}
    (hCi : C i = false) (hfire : traj k W T cap C n i = true) : fire k W T cap full i = true := by
  cases n with
  | zero => simp [traj, iter, hCi] at hfire
  | succ p =>
    have h : (C i || fire k W T cap (traj k W T cap C p) i) = true := hfire
    rw [hCi, Bool.false_or] at h
    exact fire_mono (fun _ _ _ => rfl) i h

/-- Autonomous dynamics (cue removed): if all k cells fire, they fire at every later step,
    provided the all-on state drives every cell. -/
theorem never_terminates {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat}
    (hfull : ∀ i, i < k → fire k W T cap full i = true)
    (S : CellSet) (hS : ∀ i, i < k → S i = true) :
    ∀ n i, i < k → iter (fire k W T cap) n S i = true := by
  intro n
  induction n with
  | zero => exact hS
  | succ n ih =>
    intro i hi
    have hsub : Sub k full (iter (fire k W T cap) n S) := fun j hj _ => ih j hj
    exact fire_mono hsub i (hfull i hi)

/-- **Theorem A (equal recruit/sustain threshold, cascades allowed).**
    Suppose every cell can be recruited by SOME cue that does not contain it (true whenever
    every m-of-k cue completes with m < k, see `anyM_recruits`). Then once all k cells fire
    and the cue is removed, all k cells fire forever: fast termination is impossible.
    No assumption on k, m, cue fraction, weight bounds, cap, or diagonal. -/
theorem completion_forces_ignition {k : Nat} {W : Nat → Nat → Nat} {T cap : Nat}
    (hrec : ∀ i, i < k → ∃ C n, C i = false ∧ traj k W T cap C n i = true)
    (S : CellSet) (hS : ∀ i, i < k → S i = true) :
    ∀ n i, i < k → iter (fire k W T cap) n S i = true := by
  apply never_terminates _ S hS
  intro i hi
  obtain ⟨C, n, hCi, hf⟩ := hrec i hi
  exact recruited_full hCi hf

/-! ## Relabelling: cues on the k-1 cells other than `i` -/

/-- Lift a set on 0..k-2 to a set on 0..k-1 that avoids `i`. -/
def lift (i : Nat) (C' : CellSet) : CellSet :=
  fun x => if x = i then false else C' (if x < i then x else x - 1)

theorem lift_self (i : Nat) (C' : CellSet) : lift i C' i = false := by simp [lift]

theorem lift_skip (i j : Nat) (C' : CellSet) : lift i C' (skip i j) = C' j := by
  unfold lift skip
  by_cases h : j < i
  · simp only [h, ↓reduceIte]; simp only [Nat.ne_of_lt h, ↓reduceIte]
  · simp only [h, ↓reduceIte]
    have h1 : j + 1 ≠ i := by omega
    have h2 : ¬ (j + 1 < i) := by omega
    simp only [h1, h2, ↓reduceIte, Nat.add_sub_cancel]

theorem sumOn_lift (n i : Nat) (hi : i < n + 1) (C' : CellSet) (a : Nat → Nat) :
    sumOn (n+1) (lift i C') a = sumOn n C' (fun j => a (skip i j)) := by
  unfold sumOn
  rw [sumTo_skip n _ i hi, lift_self]
  simp only [Bool.false_eq_true, ↓reduceIte, Nat.zero_add]
  exact sumTo_congr (fun j _ => by rw [lift_skip])

theorem card_lift (n i : Nat) (hi : i < n + 1) (C' : CellSet) :
    card (n+1) (lift i C') = card n C' := sumOn_lift n i hi C' (fun _ => 1)

/-- An explicit m-of-k cue avoiding `i` exists when m ≤ k - 1. -/
theorem exists_cue_avoiding (n m i : Nat) (hi : i < n + 1) (hm : m ≤ n) :
    ∃ C : CellSet, C i = false ∧ card (n+1) C = m := by
  refine ⟨lift i (fun j => decide (j < m)), lift_self i _, ?_⟩
  rw [card_lift n i hi]
  unfold card
  have := sumTo_ite_lt n m 1
  simp only [decide_eq_true_eq] at *
  rw [this, Nat.min_eq_right hm, Nat.mul_one]

/-- Completion from every m-of-k cue with m < k means every cell is recruitable by a cue
    that avoids it. -/
theorem anyM_recruits {n m : Nat} {W : Nat → Nat → Nat} {T cap : Nat} (hm : m ≤ n)
    (hall : ∀ C, card (n+1) C = m → Completes (n+1) W T cap C) :
    ∀ i, i < n + 1 → ∃ C k, C i = false ∧ traj (n+1) W T cap C k i = true := by
  intro i hi
  obtain ⟨C, hCi, hcard⟩ := exists_cue_avoiding n m i hi hm
  obtain ⟨t, ht⟩ := hall C hcard
  exact ⟨C, t, hCi, ht i hi⟩

/-- **Corollary A'.** If every m-of-k cue (m < k) completes, the all-on state never terminates
    once reached (same threshold for recruiting and sustaining). In particular this holds for
    m = 9, k = 17 (the 50% cue) and for m = 13, k = 17 (the 75% cue) alike. -/
theorem anyM_completion_forces_ignition {n m : Nat} {W : Nat → Nat → Nat} {T cap : Nat}
    (hm : m ≤ n) (hall : ∀ C, card (n+1) C = m → Completes (n+1) W T cap C)
    (S : CellSet) (hS : ∀ i, i < n + 1 → S i = true) :
    ∀ t i, i < n + 1 → iter (fire (n+1) W T cap) t S i = true :=
  completion_forces_ignition (anyM_recruits hm hall) S hS

/-! ## Part 1: one-step completion from the worst m-subset; counting bound -/

/-- Cyclic window {j : (j + s) mod n < m}. -/
def window (n m s : Nat) : CellSet := fun j => decide ((j + s) % n < m)

theorem card_window (n m s : Nat) (hn : 0 < n) (hm : m ≤ n) : card n (window n m s) = m := by
  unfold card window
  have h := sumTo_rot n hn (fun x => if decide (x < m) = true then 1 else 0) s
  rw [h]
  have := sumTo_ite_lt n m 1
  simp only [decide_eq_true_eq] at *
  rw [this, Nat.min_eq_right hm, Nat.mul_one]

/-- **Counting lemma.** If every m-subset of n nonnegative numbers sums to ≥ Tc, then
    n * Tc ≤ m * (total). (Average over the n cyclic windows of length m.) -/
theorem window_count (n m Tc : Nat) (hn : 0 < n) (hm : m ≤ n) (a : Nat → Nat)
    (h : ∀ C, card n C = m → Tc ≤ sumOn n C a) : n * Tc ≤ m * sumTo n a := by
  have step1 : n * Tc ≤ sumTo n (fun s => sumOn n (window n m s) a) := by
    rw [← sumTo_const]
    exact sumTo_mono (fun s _ => h _ (card_window n m s hn hm))
  have step2 : sumTo n (fun s => sumOn n (window n m s) a) = sumTo n (fun j => m * a j) := by
    unfold sumOn
    rw [sumTo_comm]
    apply sumTo_congr
    intro j _
    have h := sumTo_rot n hn (fun x => if decide (x < m) = true then a j else 0) j
    have hcomm : sumTo n (fun s => if window n m s j = true then a j else 0)
        = sumTo n (fun s => if decide ((s + j) % n < m) = true then a j else 0) :=
      sumTo_congr (fun s _ => by simp only [window, Nat.add_comm j s])
    rw [hcomm, h]
    have := sumTo_ite_lt n m (a j)
    simp only [decide_eq_true_eq] at *
    rw [this, Nat.min_eq_right hm]
  rw [step2, sumTo_mul_left] at step1
  exact step1

/-- **Theorem B (Part 1).** k = n+1 cells, zero self-weight at `i`. If EVERY m-subset of the
    other cells drives `i` to ≥ Tc in ONE step (simultaneous completion), then
      n * Tc ≤ m * (total in-sum of i),
    i.e. in-sum(i) ≥ (k-1)/m · Tc. For k = 17 this is the 16·Tc/m bound on every column sum,
    hence on the minimum column sum. (ρ ≥ min column sum is the Collatz–Wielandt / Perron
    bound for nonnegative matrices; it is NOT proved in this file.) -/
theorem one_step_bound (n m Tc i : Nat) (W : Nat → Nat → Nat) (hn : 0 < n) (hm : m ≤ n)
    (hi : i < n + 1) (hdiag : W i i = 0)
    (h : ∀ C, C i = false → card (n+1) C = m → Tc ≤ inp (n+1) W C i) :
    n * Tc ≤ m * inp (n+1) W full i := by
  have hfull : inp (n+1) W full i = sumTo n (fun j => W (skip i j) i) := by
    unfold inp sumOn full
    rw [sumTo_skip n _ i hi]
    simp [hdiag]
  rw [hfull]
  apply window_count n m Tc hn hm
  intro C' hC'
  have h1 := h (lift i C') (lift_self i C') (by rw [card_lift n i hi]; exact hC')
  unfold inp at h1
  rw [sumOn_lift n i hi] at h1
  exact h1

/-- **Corollary B' (hysteresis needed).** Under one-step completion from every m-subset
    (0 < m ≤ k-1), if after completion the all-on state is to die out under a SUSTAIN
    threshold Ts (some cell's full in-sum < Ts), then n * Tc < m * Ts, i.e.
    Ts / Tc > (k-1)/m. With Ts = Tc (no hysteresis) this is impossible for every m ≤ k-1. -/
theorem hysteresis_needed (n m Tc Ts i : Nat) (W : Nat → Nat → Nat) (hn : 0 < n) (hm0 : 0 < m)
    (hm : m ≤ n) (hi : i < n + 1) (hdiag : W i i = 0)
    (h : ∀ C, C i = false → card (n+1) C = m → Tc ≤ inp (n+1) W C i)
    (hdie : inp (n+1) W full i < Ts) : n * Tc < m * Ts := by
  have hb := one_step_bound n m Tc i W hn hm hi hdiag h
  have : m * inp (n+1) W full i < m * Ts := Nat.mul_lt_mul_of_pos_left hdie hm0
  omega

theorem no_window_without_hysteresis (n m T i : Nat) (W : Nat → Nat → Nat) (hn : 0 < n)
    (hm0 : 0 < m) (hm : m ≤ n) (hi : i < n + 1) (hdiag : W i i = 0)
    (h : ∀ C, C i = false → card (n+1) C = m → T ≤ inp (n+1) W C i) :
    ¬ inp (n+1) W full i < T := by
  intro hdie
  have := hysteresis_needed n m T T i W hn hm0 hm hi hdiag h hdie
  have : m * T ≤ n * T := Nat.mul_le_mul_right T hm
  omega

/-- **Weight ceiling.** If every weight into `i` is ≤ wmax and some m-cue drives `i` to ≥ Tc,
    then Tc ≤ m * wmax. -/
theorem sumOn_le_card_mul (n : Nat) (C : CellSet) (a : Nat → Nat) (wmax : Nat)
    (h : ∀ j, j < n → a j ≤ wmax) : sumOn n C a ≤ card n C * wmax := by
  unfold sumOn card
  rw [Nat.mul_comm, ← sumTo_mul_left]
  apply sumTo_mono
  intro j hj
  cases C j
  · simp
  · simp only [↓reduceIte, Nat.mul_one]; exact h j hj

theorem ceiling_bound (k m Tc wmax i : Nat) (W : Nat → Nat → Nat) (C : CellSet)
    (hw : ∀ j, j < k → W j i ≤ wmax) (hcard : card k C = m) (hdrive : Tc ≤ inp k W C i) :
    Tc ≤ m * wmax := by
  have := sumOn_le_card_mul k C (fun j => W j i) wmax hw
  unfold inp at hdrive
  rw [hcard] at this
  omega

end Assembly
