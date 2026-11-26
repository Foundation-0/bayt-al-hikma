/-
  RawArabicHigherOrderMesh.lean
  Raw-Arabic Scientific Mesh: Pure-Init Lean 4.36.0 Companion for Live Raw-Arabic K_12
  Scientific Mesh, Higher-Order Translation Silo-Cut Collapse,
  Schur Conductance Monotonicity, and Dotless Rasm Homography Obstruction.

  Zero external imports (Init only). Zero axioms beyond Init core.
  Zero sorry, zero admit, zero Classical.choice, zero quotes or guillemets.
-/

namespace RawArabicHigherOrderMesh

/-- Exact edge count C(k+1, 2) of a k-simplex on k+1 vertices. -/
def simplexEdges (k : Nat) : Nat :=
  (k + 1) * k / 2

/-- Theorem 1: Exact closed form 2 * C(k+1, 2) = (k+1) * k for all k. -/
theorem simplex_edge_count_doubled :
    ∀ k : Nat, 2 * simplexEdges k = (k + 1) * k := by
  intro k
  unfold simplexEdges
  have heven : 2 ∣ (k + 1) * k := by
    induction k with
    | zero => exact ⟨0, by omega⟩
    | succ m ih =>
      rcases ih with ⟨t, ht⟩
      refine ⟨t + m + 1, ?_⟩
      have h1 : (m + 1 + 1) * (m + 1) = (m + 1) * m + 2 * (m + 1) := by
        rw [Nat.mul_succ, Nat.succ_mul]
        omega
      omega
  rcases heven with ⟨t, ht⟩
  rw [ht]
  omega

/-- Theorem 2: Exact edge counts for k = 1, 2, 3, 4 simplices (1, 3, 6, 10). -/
theorem simplex_edge_counts_k1_to_k4 :
    simplexEdges 1 = 1 ∧ simplexEdges 2 = 3 ∧
    simplexEdges 3 = 6 ∧ simplexEdges 4 = 10 := by
  decide

/-- Theorem 3: Exact K_12 simplicial face counts (66 edges, 220 triangles, 495 tetrahedra, 792 5-cells). -/
theorem k12_simplicial_face_counts :
    simplexEdges 11 = 66 ∧
    (12 * 11 * 10) / 6 = 220 ∧
    (12 * 11 * 10 * 9) / 24 = 495 ∧
    (12 * 11 * 10 * 9 * 8) / 120 = 792 ∧
    12 - 1 = 11 := by
  decide

/-- Theorem 4: Strict monotone increase of k-simplex edge count for all k >= 1. -/
theorem simplex_edge_strict_step :
    ∀ k : Nat, 1 ≤ k → simplexEdges k < simplexEdges (k + 1) := by
  intro k hk
  have h1 := simplex_edge_count_doubled k
  have h2 := simplex_edge_count_doubled (k + 1)
  have hdiff : (k + 1) * k < (k + 1 + 1) * (k + 1) := by
    have hexp : (k + 1 + 1) * (k + 1) = (k + 1) * k + 2 * (k + 1) := by
      rw [Nat.mul_succ, Nat.succ_mul]
      omega
    omega
  omega

/-- Helper: strict positivity of powers of positive natural numbers. -/
theorem nat_pow_pos : ∀ a n : Nat, 0 < a → 0 < a ^ n := by
  intro a n ha
  induction n with
  | zero => simp
  | succ m ih =>
    rw [Nat.pow_succ]
    exact Nat.mul_pos ih ha

/-- Helper: strict power monotonicity p^k < q^k for 0 < p < q and k >= 1. -/
theorem nat_pow_strict_lt :
    ∀ p q k : Nat, 0 < p → p < q → 1 ≤ k → p ^ k < q ^ k := by
  intro p q k hp hpq hk
  induction k with
  | zero => omega
  | succ m ih =>
    cases m with
    | zero =>
      simp
      exact hpq
    | succ r =>
      have hm : p ^ (r + 1) < q ^ (r + 1) := ih (by omega)
      have hqpos : 0 < q := by omega
      have hqpow : 0 < q ^ (r + 1) := nat_pow_pos q (r + 1) hqpos
      rw [Nat.pow_succ, Nat.pow_succ]
      have s1 : p ^ (r + 1) * p < q ^ (r + 1) * p :=
        Nat.mul_lt_mul_of_pos_right hm hp
      have s2 : q ^ (r + 1) * p < q ^ (r + 1) * q :=
        Nat.mul_lt_mul_of_pos_left hpq hqpow
      exact Nat.lt_trans s1 s2

/-- Theorem 5: Cleared-denominator strict exponential decay (p/q)^n < (p/q)^m for 0 < p < q and m < n. -/
theorem pow_strict_lt_of_lt :
    ∀ p q m n : Nat, 0 < p → p < q → m < n →
      p ^ n * q ^ m < p ^ m * q ^ n := by
  intro p q m n hp hpq hmn
  let d := n - m
  have hdiff : 1 ≤ d := by omega
  have hnm : n = m + d := by omega
  have hlt : p ^ d < q ^ d := nat_pow_strict_lt p q d hp hpq hdiff
  have hpm : 0 < p ^ m := nat_pow_pos p m hp
  have hqm : 0 < q ^ m := nat_pow_pos q m (by omega)
  have hprod : 0 < p ^ m * q ^ m := Nat.mul_pos hpm hqm
  have hmul : (p ^ m * q ^ m) * p ^ d < (p ^ m * q ^ m) * q ^ d :=
    Nat.mul_lt_mul_of_pos_left hlt hprod
  have hlhs : p ^ n * q ^ m = (p ^ m * q ^ m) * p ^ d := by
    rw [hnm, Nat.pow_add]
    calc
      p ^ m * p ^ d * q ^ m
          = p ^ m * (p ^ d * q ^ m) := Nat.mul_assoc _ _ _
      _ = p ^ m * (q ^ m * p ^ d) := by rw [Nat.mul_comm (p ^ d) (q ^ m)]
      _ = (p ^ m * q ^ m) * p ^ d := (Nat.mul_assoc _ _ _).symm
  have hrhs : p ^ m * q ^ n = (p ^ m * q ^ m) * q ^ d := by
    rw [hnm, Nat.pow_add]
    exact (Nat.mul_assoc _ _ _).symm
  rw [hlhs, hrhs]
  exact hmul

/-- Theorem 6: Universal super-exponential clique retention decay r^10 < r^6 < r^3 < r^1 < 1. -/
theorem super_exponential_simplex_collapse :
    ∀ p q : Nat, 0 < p → p < q →
      (p ^ 10 * q ^ 6 < p ^ 6 * q ^ 10) ∧
      (p ^ 6 * q ^ 3 < p ^ 3 * q ^ 6) ∧
      (p ^ 3 * q ^ 1 < p ^ 1 * q ^ 3) ∧
      (p < q) := by
  intro p q hp hpq
  refine ⟨?_, ?_, ?_, hpq⟩
  · exact pow_strict_lt_of_lt p q 6 10 hp hpq (by omega)
  · exact pow_strict_lt_of_lt p q 3 6 hp hpq (by omega)
  · exact pow_strict_lt_of_lt p q 1 3 hp hpq (by omega)

/-- Theorem 7: Universal step-amplification across arbitrary clique order k >= 1. -/
theorem simplex_decay_step_amplification :
    ∀ k p q : Nat, 1 ≤ k → 0 < p → p < q →
      p ^ simplexEdges (k + 1) * q ^ simplexEdges k <
      p ^ simplexEdges k * q ^ simplexEdges (k + 1) := by
  intro k p q hk hp hpq
  exact pow_strict_lt_of_lt p q (simplexEdges k) (simplexEdges (k + 1))
    hp hpq (simplex_edge_strict_step k hk)

/-- Helper: power monotonicity for weak inequality a <= b. -/
theorem nat_pow_le_of_le :
    ∀ a b n : Nat, a ≤ b → a ^ n ≤ b ^ n := by
  intro a b n hab
  induction n with
  | zero => simp
  | succ m ih =>
    rw [Nat.pow_succ, Nat.pow_succ]
    exact Nat.mul_le_mul ih hab

/-- Theorem 8: Universal >= 87.5% triangle loss whenever per-edge retention r <= 1/2. -/
theorem triangle_collapse_below_half_retention :
    ∀ p q : Nat, 2 * p ≤ q → 8 * p ^ 3 ≤ q ^ 3 := by
  intro p q h
  have h3 : (2 * p) ^ 3 ≤ q ^ 3 := nat_pow_le_of_le (2 * p) q 3 h
  have heq : (2 * p) ^ 3 = 8 * p ^ 3 := by
    rw [Nat.mul_pow]
  omega

/-- Theorem 9: Universal >= 98.4375% tetrahedron loss whenever per-edge retention r <= 1/2. -/
theorem tetrahedron_collapse_below_half_retention :
    ∀ p q : Nat, 2 * p ≤ q → 64 * p ^ 6 ≤ q ^ 6 := by
  intro p q h
  have h6 : (2 * p) ^ 6 ≤ q ^ 6 := nat_pow_le_of_le (2 * p) q 6 h
  have heq : (2 * p) ^ 6 = 64 * p ^ 6 := by
    rw [Nat.mul_pow]
  omega

/-- Theorem 10: Universal > 99.90% 5-cell loss whenever per-edge retention r <= 1/2. -/
theorem five_cell_collapse_below_half_retention :
    ∀ p q : Nat, 2 * p ≤ q → 1024 * p ^ 10 ≤ q ^ 10 := by
  intro p q h
  have h10 : (2 * p) ^ 10 ≤ q ^ 10 := nat_pow_le_of_le (2 * p) q 10 h
  have heq : (2 * p) ^ 10 = 1024 * p ^ 10 := by
    rw [Nat.mul_pow]
  omega

/-- Theorem 11: Exact Bayt al-Hikma Sahih retention r_S = 3601/7335 higher-order collapse thresholds. -/
theorem bayt_sahih_higher_order_thresholds :
    2 * 3601 < 7335 ∧
    1000 * 3601 ^ 3 < 119 * 7335 ^ 3 ∧
    10000 * 3601 ^ 6 < 141 * 7335 ^ 6 ∧
    10000 * 3601 ^ 10 < 9 * 7335 ^ 10 := by
  decide

/-- Theorem 12: Exact Bayt al-Hikma Pickthall retention r_P = 1001/2934 higher-order collapse thresholds. -/
theorem bayt_pickthall_higher_order_thresholds :
    2 * 1001 < 2934 ∧
    1000 * 1001 ^ 3 < 40 * 2934 ^ 3 ∧
    10000 * 1001 ^ 6 < 16 * 2934 ^ 6 ∧
    100000 * 1001 ^ 10 < 3 * 2934 ^ 10 := by
  decide

/-- Theorem 13: Scalar multiplicative strict thinning inequality (p/q) * g < g for 0 < p < q. -/
theorem schur_conductance_strict_thinning :
    ∀ g_num g_den p q : Nat, 0 < g_num → 0 < g_den → 0 < p → p < q →
      (p * g_num) * g_den < g_num * (q * g_den) := by
  intro g_num g_den p q hgn hgd _ hpq
  have hprod : 0 < g_num * g_den := Nat.mul_pos hgn hgd
  have hlt : p * (g_num * g_den) < q * (g_num * g_den) :=
    Nat.mul_lt_mul_of_pos_right hpq hprod
  have hlhs : (p * g_num) * g_den = p * (g_num * g_den) := Nat.mul_assoc p g_num g_den
  have hrhs : g_num * (q * g_den) = q * (g_num * g_den) := by
    calc
      g_num * (q * g_den) = (g_num * q) * g_den := (Nat.mul_assoc g_num q g_den).symm
      _ = (q * g_num) * g_den := by rw [Nat.mul_comm g_num q]
      _ = q * (g_num * g_den) := Nat.mul_assoc q g_num g_den
  rw [hlhs, hrhs]
  exact hlt

/-- Theorem 14: Scalar multiplicative strict inverse inflation inequality r < (q/p) * r for 0 < p < q. -/
theorem schur_effective_resistance_inflation :
    ∀ r_num r_den p q : Nat, 0 < r_num → 0 < r_den → 0 < p → p < q →
      r_num * (p * r_den) < (q * r_num) * r_den := by
  intro r_num r_den p q hrn hrd _ hpq
  have hprod : 0 < r_num * r_den := Nat.mul_pos hrn hrd
  have hlt : p * (r_num * r_den) < q * (r_num * r_den) :=
    Nat.mul_lt_mul_of_pos_right hpq hprod
  have hlhs : r_num * (p * r_den) = p * (r_num * r_den) := by
    calc
      r_num * (p * r_den) = (r_num * p) * r_den := (Nat.mul_assoc r_num p r_den).symm
      _ = (p * r_num) * r_den := by rw [Nat.mul_comm r_num p]
      _ = p * (r_num * r_den) := Nat.mul_assoc p r_num r_den
  have hrhs : (q * r_num) * r_den = q * (r_num * r_den) := Nat.mul_assoc q r_num r_den
  rw [hlhs, hrhs]
  exact hlt

/-- Theorem 15: Two-edge series-branch conductance strict monotonicity a*b/(a+b) < a*b2/(a+b2). -/
theorem schur_series_branch_strict_monotone :
    ∀ a b b2 : Nat, 0 < a → 0 < b → b < b2 →
      (a * b) * (a + b2) < (a * b2) * (a + b) := by
  intro a b b2 ha _ hbb2
  have haa : 0 < a * a := Nat.mul_pos ha ha
  have hlt : (a * a) * b < (a * a) * b2 := Nat.mul_lt_mul_of_pos_left hbb2 haa
  have hlhs : (a * b) * (a + b2) = (a * a) * b + a * b * b2 := by
    rw [Nat.mul_add]
    have t1 : a * b * a = a * a * b := by
      calc
        a * b * a = a * (b * a) := Nat.mul_assoc a b a
        _ = a * (a * b) := by rw [Nat.mul_comm b a]
        _ = a * a * b := (Nat.mul_assoc a a b).symm
    rw [t1]
  have hrhs : (a * b2) * (a + b) = (a * a) * b2 + a * b * b2 := by
    rw [Nat.mul_add]
    have t1 : a * b2 * a = a * a * b2 := by
      calc
        a * b2 * a = a * (b2 * a) := Nat.mul_assoc a b2 a
        _ = a * (a * b2) := by rw [Nat.mul_comm b2 a]
        _ = a * a * b2 := (Nat.mul_assoc a a b2).symm
    have t2 : a * b2 * b = a * b * b2 := by
      calc
        a * b2 * b = a * (b2 * b) := Nat.mul_assoc a b2 b
        _ = a * (b * b2) := by rw [Nat.mul_comm b2 b]
        _ = a * b * b2 := (Nat.mul_assoc a b b2).symm
    rw [t1, t2]
  rw [hlhs, hrhs]
  exact Nat.add_lt_add_right hlt (a * b * b2)

/-- Theorem 16: Exact two-layer cross-lemma fracture amplification sandwich. -/
theorem cross_lemma_fracture_amplification :
    ∀ l_s n_s l_c n_c : Nat, 0 < n_s → 0 < n_c →
      l_s * n_c < l_c * n_s →
      (l_s * (n_s + n_c) < (l_s + l_c) * n_s) ∧
      ((l_s + l_c) * n_c < l_c * (n_s + n_c)) := by
  intro l_s n_s l_c n_c _ _ hgap
  constructor
  · rw [Nat.mul_add, Nat.add_mul]
    exact Nat.add_lt_add_left hgap (l_s * n_s)
  · rw [Nat.add_mul, Nat.mul_add]
    exact Nat.add_lt_add_right hgap (l_c * n_c)

/-- Theorem 17: Law-5 Dotless Rasm Homography Collision Inflation (merging any two positive classes). -/
theorem rasm_homography_collision_inflation :
    ∀ rest a b : Nat, 0 < a → 0 < b →
      rest + a * a + b * b < rest + (a + b) * (a + b) := by
  intro rest a b ha hb
  have hab : 0 < 2 * (a * b) := Nat.mul_pos (by decide) (Nat.mul_pos ha hb)
  have hexp : (a + b) * (a + b) = a * a + b * b + 2 * (a * b) := by
    rw [Nat.add_mul, Nat.mul_add, Nat.mul_add]
    have hcomm : b * a = a * b := Nat.mul_comm b a
    rw [hcomm]
    omega
  rw [hexp]
  omega

/-- Theorem 18: Law-5 Necessary Null-Inflation Criterion implied by Observed-Overlap Rise and Lift Reversal. -/
theorem rasm_lift_reversal_criterion :
    ∀ obs_r null_r obs_m null_m : Nat,
      0 < obs_r → 0 < null_r → 0 < obs_m → 0 < null_m →
      obs_r < obs_m →
      obs_m * null_r < obs_r * null_m →
      null_r < null_m := by
  intro obs_r null_r obs_m null_m _ hnr _ _ hobs hrev
  match Nat.lt_or_ge null_r null_m with
  | Or.inl hlt => exact hlt
  | Or.inr hge =>
    have h1 : obs_r * null_m ≤ obs_r * null_r := Nat.mul_le_mul_left obs_r hge
    have h2 : obs_r * null_r < obs_m * null_r := Nat.mul_lt_mul_of_pos_right hobs hnr
    exact False.elim (Nat.not_lt_of_ge h1 (Nat.lt_trans h2 hrev))

end RawArabicHigherOrderMesh
