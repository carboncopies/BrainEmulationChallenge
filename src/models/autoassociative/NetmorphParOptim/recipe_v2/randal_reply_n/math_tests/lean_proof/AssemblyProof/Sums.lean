/-
  Finite sums over {0, ..., n-1} on Nat, built from Lean core only (no Mathlib).
  Helper lemmas for the assembly theorems in `Model.lean`.
-/
namespace Assembly

/-- `sumTo n f = f 0 + f 1 + ... + f (n-1)`. -/
def sumTo : Nat → (Nat → Nat) → Nat
  | 0, _ => 0
  | n+1, f => sumTo n f + f n

theorem sumTo_zero (f : Nat → Nat) : sumTo 0 f = 0 := rfl
theorem sumTo_succ (n : Nat) (f : Nat → Nat) : sumTo (n+1) f = sumTo n f + f n := rfl

theorem sumTo_congr {n : Nat} {f g : Nat → Nat} (h : ∀ j, j < n → f j = g j) :
    sumTo n f = sumTo n g := by
  induction n with
  | zero => rfl
  | succ n ih =>
    rw [sumTo_succ, sumTo_succ, ih (fun j hj => h j (Nat.lt_succ_of_lt hj)),
      h n (Nat.lt_succ_self n)]

theorem sumTo_mono {n : Nat} {f g : Nat → Nat} (h : ∀ j, j < n → f j ≤ g j) :
    sumTo n f ≤ sumTo n g := by
  induction n with
  | zero => exact Nat.le_refl _
  | succ n ih =>
    rw [sumTo_succ, sumTo_succ]
    exact Nat.add_le_add (ih (fun j hj => h j (Nat.lt_succ_of_lt hj))) (h n (Nat.lt_succ_self n))

theorem sumTo_add (n : Nat) (f g : Nat → Nat) :
    sumTo n (fun j => f j + g j) = sumTo n f + sumTo n g := by
  induction n with
  | zero => rfl
  | succ n ih => rw [sumTo_succ, sumTo_succ, sumTo_succ, ih]; omega

theorem sumTo_mul_left (n c : Nat) (f : Nat → Nat) :
    sumTo n (fun j => c * f j) = c * sumTo n f := by
  induction n with
  | zero => simp [sumTo]
  | succ n ih => rw [sumTo_succ, sumTo_succ, ih, Nat.mul_add]

theorem sumTo_zero_fn (n : Nat) : sumTo n (fun _ => 0) = 0 := by
  induction n with
  | zero => rfl
  | succ n ih => rw [sumTo_succ, ih]

theorem sumTo_const (n c : Nat) : sumTo n (fun _ => c) = n * c := by
  induction n with
  | zero => simp [sumTo]
  | succ n ih => rw [sumTo_succ, ih, Nat.succ_mul]

/-- Exchange of a double finite sum. -/
theorem sumTo_comm (n m : Nat) (F : Nat → Nat → Nat) :
    sumTo n (fun s => sumTo m (fun j => F s j)) = sumTo m (fun j => sumTo n (fun s => F s j)) := by
  induction n with
  | zero => rw [sumTo_zero]; exact (sumTo_zero_fn m).symm
  | succ n ih =>
    rw [sumTo_succ, ih]
    exact (sumTo_add m (fun j => sumTo n (fun s => F s j)) (fun j => F n j)).symm

/-- Peel off the first term. -/
theorem sumTo_succ_shift (n : Nat) (f : Nat → Nat) :
    sumTo (n+1) f = f 0 + sumTo n (fun j => f (j+1)) := by
  induction n with
  | zero => simp [sumTo]
  | succ n ih => rw [sumTo_succ, ih, sumTo_succ]; omega

/-- Cyclic rotation by one does not change a sum over `Z/n`. -/
theorem sumTo_rot1 (n : Nat) (hn : 0 < n) (f : Nat → Nat) :
    sumTo n (fun j => f ((j+1) % n)) = sumTo n f := by
  obtain ⟨p, rfl⟩ : ∃ p, n = p + 1 := ⟨n - 1, by omega⟩
  rw [sumTo_succ, Nat.mod_self, sumTo_succ_shift]
  rw [sumTo_congr (g := fun j => f (j+1)) (fun j hj => by
    rw [Nat.mod_eq_of_lt (by omega)])]
  omega

/-- Cyclic rotation by any `r` does not change a sum over `Z/n`. -/
theorem sumTo_rot (n : Nat) (hn : 0 < n) (f : Nat → Nat) (r : Nat) :
    sumTo n (fun j => f ((j + r) % n)) = sumTo n f := by
  induction r with
  | zero => exact sumTo_congr (fun j hj => by rw [Nat.add_zero, Nat.mod_eq_of_lt hj])
  | succ r ih =>
    have h := sumTo_rot1 n hn (fun x => f ((x + r) % n))
    rw [← ih, ← h]
    apply sumTo_congr
    intro j _
    show f ((j + (r+1)) % n) = f (((j+1) % n + r) % n)
    rw [Nat.mod_add_mod]
    congr 2
    omega

/-- Number of `s < n` with `s < m`, weighted by `c`. -/
theorem sumTo_ite_lt (n m c : Nat) :
    sumTo n (fun s => if s < m then c else 0) = min n m * c := by
  induction n with
  | zero => simp [sumTo]
  | succ n ih =>
    rw [sumTo_succ, ih]
    by_cases h : n < m
    · simp only [h, ↓reduceIte]
      rw [Nat.min_eq_left (by omega), Nat.min_eq_left (by omega), Nat.succ_mul]
    · simp only [h, ↓reduceIte]
      rw [Nat.min_eq_right (by omega), Nat.min_eq_right (by omega), Nat.add_zero]

/-- `skip i` enumerates `{0,1,...} \ {i}` in order. -/
def skip (i j : Nat) : Nat := if j < i then j else j + 1

theorem skip_ne (i j : Nat) : skip i j ≠ i := by
  unfold skip; split <;> omega

/-- Splitting one index `i` out of a sum over `0..k`. -/
theorem sumTo_skip (k : Nat) (f : Nat → Nat) (i : Nat) (hi : i < k + 1) :
    sumTo (k+1) f = f i + sumTo k (fun j => f (skip i j)) := by
  induction k with
  | zero =>
    have : i = 0 := by omega
    subst this; simp [sumTo]
  | succ k ih =>
    rw [sumTo_succ (k+1)]
    by_cases hik : i = k + 1
    · subst hik
      have hs : sumTo (k+1) (fun j => f (skip (k+1) j)) = sumTo (k+1) f :=
        sumTo_congr (fun j hj => by simp [skip, hj])
      rw [hs]; omega
    · rw [ih (by omega), sumTo_succ k]
      have : skip i k = k + 1 := by simp only [skip]; split <;> omega
      rw [this]; omega

end Assembly
