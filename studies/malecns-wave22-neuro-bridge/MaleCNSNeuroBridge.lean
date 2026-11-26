/-
Track S162 (EXP-Q43a & EXP-Q43b): Pure-Init Lean 4.36.0 Formalization of
MaleCNS v1.0 Frustrated Cycles x PFC Loopy Belief Propagation, Ibn al-Nafis
Septal Cavity Exclusion (SOP-16), and Wave-22 Carved/Looped Routing Operators.

Zero external imports, zero sorry/admit/axiom/unsafe/native_decide/Classical.choice.
All 16 public theorems are universally quantified operator laws depending only on
Lean kernel primitives (`propext`, `Quot.sound`, or zero axioms).
-/

namespace MaleCNSNeuroBridge

private theorem sq_nonneg (x : Int) : 0 ≤ x * x := by
  by_cases h : 0 ≤ x
  · exact Int.mul_nonneg h h
  · have hneg : 0 ≤ -x := by omega
    have hmul : 0 ≤ (-x) * (-x) := Int.mul_nonneg hneg hneg
    have heq : (-x) * (-x) = x * x := by
      rw [Int.neg_mul, Int.mul_neg, Int.neg_neg]
    rw [heq] at hmul
    exact hmul

private theorem sq_pos_of_ne_zero (x : Int) (hx : x ≠ 0) : 0 < x * x := by
  by_cases h : 0 < x
  · exact Int.mul_pos h h
  · have hneg : 0 < -x := by omega
    have hmul : 0 < (-x) * (-x) := Int.mul_pos hneg hneg
    have heq : (-x) * (-x) = x * x := by
      rw [Int.neg_mul, Int.mul_neg, Int.neg_neg]
    rw [heq] at hmul
    exact hmul

private theorem diff_sq_identity (u v : Int) :
    (u - v) * (u - v) = u * u - 2 * (u * v) + v * v := by
  rw [Int.sub_mul, Int.mul_sub, Int.mul_sub]
  have hc : v * u = u * v := Int.mul_comm v u
  omega

private theorem sq_diff_factor (u v : Int) :
    u * u - v * v = (u - v) * (u + v) := by
  rw [Int.sub_mul, Int.mul_add, Int.mul_add, Int.mul_comm v u]
  omega

private theorem add_sq_identity (u v : Int) :
    (u + v) * (u + v) = u * u + 2 * (u * v) + v * v := by
  rw [Int.add_mul, Int.mul_add, Int.mul_add]
  have hc : v * u = u * v := Int.mul_comm v u
  omega

private theorem prod_sq_split (x y : Int) :
    (x * y) * (x * y) = (x * x) * (y * y) := by
  calc
    (x * y) * (x * y) = x * (y * (x * y)) := Int.mul_assoc x y (x * y)
    _ = x * (x * (y * y)) := by
      rw [← Int.mul_assoc y x y, Int.mul_comm y x, Int.mul_assoc x y y]
    _ = (x * x) * (y * y) := (Int.mul_assoc x x (y * y)).symm

/- =========================================================================
   GROUP A (EXP-Q43a): Damped Loopy BP, Complex Al-Tusi Oscillators,
   Signed Bethe-Hessian Frustration, and Cayley-Routh Schur Stability
   ========================================================================= -/

/-- Theorem 1 (Damped Loopy BP Real-Eigenvalue Stability Window):
    For any real eigenvalue `a / d < 1` (`d > 0, a < d`) and rational damping
    `p / q > 0` (`p > 0, q > 0`), the damped operator eigenvalue
    `mu = (1 - p/q) + (p/q)*(a/d)` strictly contracts (`|mu| < 1` in cleared form)
    if and only if `p * (d - a) < 2 * q * d` (i.e. `gamma < 2 / (1 - lambda)`). -/
theorem damped_bp_real_eigenvalue_stability_window
    (a d p q : Int)
    (hd : 0 < d) (ha : a < d) (hp : 0 < p) (hq : 0 < q) :
    let num := (q - p) * d + p * a
    let den := q * d
    (num * num < den * den) ↔ (p * (d - a) < 2 * q * d) := by
  intro num den
  have hden_pos : 0 < den := Int.mul_pos hq hd
  have hshift : num = den - p * (d - a) := by
    change (q - p) * d + p * a = q * d - p * (d - a)
    rw [Int.sub_mul, Int.mul_sub]
    omega
  have hpa_pos : 0 < p * (d - a) := Int.mul_pos hp (by omega)
  have hdiff : den * den - num * num = (p * (d - a)) * (2 * den - p * (d - a)) := by
    rw [hshift]
    have hsq := diff_sq_identity den (p * (d - a))
    have hmul : (p * (d - a)) * (2 * den - p * (d - a)) =
        2 * (den * (p * (d - a))) - (p * (d - a)) * (p * (d - a)) := by
      rw [Int.mul_sub]
      have h1 : (p * (d - a)) * (2 * den) = 2 * (den * (p * (d - a))) := by
        calc
          (p * (d - a)) * (2 * den) = (2 * den) * (p * (d - a)) := Int.mul_comm _ _
          _ = 2 * (den * (p * (d - a))) := Int.mul_assoc 2 den _
      omega
    omega
  have h2den : 2 * den = 2 * q * d := by
    change 2 * (q * d) = 2 * q * d
    exact (Int.mul_assoc 2 q d).symm
  constructor
  · intro hlt
    have hprod_pos : 0 < (p * (d - a)) * (2 * den - p * (d - a)) := by omega
    by_cases hgt : p * (d - a) < 2 * q * d
    · exact hgt
    · have hle : 2 * den - p * (d - a) ≤ 0 := by omega
      have hnonpos : (p * (d - a)) * (2 * den - p * (d - a)) ≤ 0 := by
        have hnn : 0 ≤ (p * (d - a)) * (-(2 * den - p * (d - a))) :=
          Int.mul_nonneg (by omega) (by omega)
        rw [Int.mul_neg] at hnn
        omega
      omega
  · intro hlt
    have hfac_pos : 0 < 2 * den - p * (d - a) := by omega
    have hprod_pos : 0 < (p * (d - a)) * (2 * den - p * (d - a)) :=
      Int.mul_pos hpa_pos hfac_pos
    omega

/-- Theorem 2 (Unsigned Positive-Loop Perron Runaway Obstruction):
    When an unsigned / positive-feedback loop carries a real eigenvalue `a / d >= 1`
    (`0 < d <= a`), NO positive damping `p / q > 0` (`p > 0, q > 0`) can contract
    the mode inside the unit disk: cleared `den <= num`, hence `den^2 <= num^2`. -/
theorem damped_bp_positive_runaway_obstruction
    (a d p q : Int)
    (hd : 0 < d) (ha : d ≤ a) (hp : 0 < p) (hq : 0 < q) :
    let num := (q - p) * d + p * a
    let den := q * d
    den ≤ num ∧ den * den ≤ num * num := by
  intro num den
  have hden_pos : 0 < den := Int.mul_pos hq hd
  have hshift : num - den = p * (a - d) := by
    change (q - p) * d + p * a - q * d = p * (a - d)
    rw [Int.sub_mul, Int.mul_sub]
    omega
  have hge : 0 ≤ p * (a - d) := Int.mul_nonneg (by omega) (by omega)
  have hle : den ≤ num := by omega
  have hsq : den * den ≤ num * num := by
    have hdiff := sq_diff_factor num den
    have hprod : 0 ≤ (num - den) * (num + den) := Int.mul_nonneg (by omega) (by omega)
    omega
  exact ⟨hle, hsq⟩

/-- Theorem 3 (Complex Al-Tusi E/I Oscillator Exact Critical Damping Threshold):
    For a complex eigenvalue `(a + i*b) / d` with `d > 0` and `a < d` under rational
    damping `p / q > 0`, cleared contraction `|mu|^2 < 1` holds if and only if
    `p * ((d - a)^2 + b^2) < 2 * q * d * (d - a)` (exact pure-Z formula for `gamma*`). -/
theorem damped_bp_complex_oscillator_stability_threshold
    (a b d p q : Int)
    (hd : 0 < d) (ha : a < d) (hp : 0 < p) (hq : 0 < q) :
    let reNum := (q - p) * d + p * a
    let imNum := p * b
    let den := q * d
    (reNum * reNum + imNum * imNum < den * den) ↔
      (p * ((d - a) * (d - a) + b * b) < 2 * q * d * (d - a)) := by
  intro reNum imNum den
  have hshift : reNum = den - p * (d - a) := by
    change (q - p) * d + p * a = q * d - p * (d - a)
    rw [Int.sub_mul, Int.mul_sub]
    omega
  have hdiff : den * den - (reNum * reNum + imNum * imNum) =
      p * (2 * q * d * (d - a) - p * ((d - a) * (d - a) + b * b)) := by
    rw [hshift]
    have hsq := diff_sq_identity den (p * (d - a))
    have hre2 : (p * (d - a)) * (p * (d - a)) = (p * p) * ((d - a) * (d - a)) :=
      prod_sq_split p (d - a)
    have him2 : imNum * imNum = (p * p) * (b * b) := prod_sq_split p b
    have hcross : 2 * (den * (p * (d - a))) = p * (2 * q * d * (d - a)) := by
      have hden_eq : den = q * d := rfl
      rw [hden_eq]
      calc
        2 * ((q * d) * (p * (d - a))) = 2 * (((q * d) * p) * (d - a)) := by
          rw [Int.mul_assoc (q * d) p (d - a)]
        _ = 2 * ((p * (q * d)) * (d - a)) := by rw [Int.mul_comm (q * d) p]
        _ = 2 * (p * ((q * d) * (d - a))) := by rw [Int.mul_assoc p (q * d) (d - a)]
        _ = p * (2 * ((q * d) * (d - a))) := by rw [Int.mul_left_comm 2 p _]
        _ = p * (2 * q * d * (d - a)) := by
          have ha1 : 2 * ((q * d) * (d - a)) = 2 * q * d * (d - a) := by
            rw [← Int.mul_assoc 2 (q * d) (d - a), ← Int.mul_assoc 2 q d]
          rw [ha1]
    have hrhs : p * (2 * q * d * (d - a) - p * ((d - a) * (d - a) + b * b)) =
        p * (2 * q * d * (d - a)) - (p * p) * ((d - a) * (d - a)) - (p * p) * (b * b) := by
      rw [Int.mul_sub, ← Int.mul_assoc p p _, Int.mul_add]
      omega
    omega
  have _ := hd
  have _ := ha
  have _ := hq
  constructor
  · intro hlt
    have hprod_pos : 0 < p * (2 * q * d * (d - a) - p * ((d - a) * (d - a) + b * b)) := by omega
    by_cases hcond : p * ((d - a) * (d - a) + b * b) < 2 * q * d * (d - a)
    · exact hcond
    · have hle : 2 * q * d * (d - a) - p * ((d - a) * (d - a) + b * b) ≤ 0 := by omega
      have hnn : 0 ≤ p * (-(2 * q * d * (d - a) - p * ((d - a) * (d - a) + b * b))) :=
        Int.mul_nonneg (by omega) (by omega)
      rw [Int.mul_neg] at hnn
      omega
  · intro hlt
    have hpos : 0 < p * (2 * q * d * (d - a) - p * ((d - a) * (d - a) + b * b)) :=
      Int.mul_pos hp (by omega)
    omega

/-- Theorem 4 (Undamped Divergence vs Damped Stabilization on Oscillatory E/I Rings):
    If an E/I ring oscillator has `a < d` and `a^2 + b^2 > d^2`, then undamped BP
    (`p = q`) strictly diverges, while any damping `p / q` strictly below `gamma*`
    strictly contracts inside the unit disk. -/
theorem damped_bp_oscillatory_undamped_divergence_damped_stabilization
    (a b d p q : Int)
    (hd : 0 < d) (ha : a < d) (hosc : d * d < a * a + b * b)
    (hp : 0 < p) (hq : 0 < q)
    (hdamp : p * ((d - a) * (d - a) + b * b) < 2 * q * d * (d - a)) :
    let undampedSq := a * a + b * b
    let reNum := (q - p) * d + p * a
    let imNum := p * b
    let den := q * d
    (d * d < undampedSq) ∧ (reNum * reNum + imNum * imNum < den * den) := by
  intro undampedSq reNum imNum den
  have hstab := (damped_bp_complex_oscillator_stability_threshold a b d p q hd ha hp hq).mpr hdamp
  exact ⟨hosc, hstab⟩

/-- Theorem 5 (Signed Bethe-Hessian 2x2 Determinant & Frustration Separation):
    For `H_BH(r) = [[r^2 - 1 + d, -r*s], [-r*s, r^2 - 1 + d]]`, its determinant
    factors as `((r^2 - 1 + d) - r*s) * ((r^2 - 1 + d) + r*s)`. At `r = 1`, an
    unfrustrated edge (`s = d`) has determinant `0` (zero harmonic mode), whereas
    frustrated degree excess (`d > |s|`, i.e. `-d < s ∧ s < d`) yields strictly
    positive determinant `(d - s) * (d + s) > 0`. -/
theorem signed_bethe_hessian_2x2_frustration_gap
    (r s d : Int)
    (hlo : -d < s) (hhi : s < d) :
    ((r * r - 1 + d) * (r * r - 1 + d) - (r * s) * (r * s) =
      ((r * r - 1 + d) - r * s) * ((r * r - 1 + d) + r * s)) ∧
    ((1 * 1 - 1 + d) * (1 * 1 - 1 + d) - (1 * d) * (1 * d) = 0) ∧
    (0 < (1 * 1 - 1 + d) * (1 * 1 - 1 + d) - (1 * s) * (1 * s)) := by
  have hfac : ∀ u v : Int, u * u - v * v = (u - v) * (u + v) := by
    intro u v
    rw [Int.sub_mul, Int.mul_add, Int.mul_add, Int.mul_comm v u]
    omega
  refine ⟨hfac (r * r - 1 + d) (r * s), ?_, ?_⟩
  · have h1 : (1 : Int) * 1 - 1 + d = d := by omega
    have h2 : (1 : Int) * d = d := by omega
    rw [h1, h2]
    omega
  · have h1 : (1 : Int) * 1 - 1 + d = d := by omega
    have h2 : (1 : Int) * s = s := by omega
    rw [h1, h2, hfac d s]
    exact Int.mul_pos (by omega) (by omega)

/-- Theorem 6 (Positive-Definite Bethe-Hessian / Signed Laplacian Zero-Nullspace):
    For any symmetric 2x2 operator `[[a, b], [b, d]]` with `a > 0` and Schur
    determinant `a * d - b^2 > 0`, the quadratic form `a*x^2 + 2*b*x*y + d*y^2`
    is strictly positive for every nonzero `(x, y)`. -/
theorem bethe_hessian_pd_implies_strict_frustration
    (a b d x y : Int)
    (ha : 0 < a) (hdet : 0 < a * d - b * b)
    (hxy : x ≠ 0 ∨ y ≠ 0) :
    0 < a * (x * x) + 2 * b * x * y + d * (y * y) := by
  have hcomp : a * (a * (x * x) + 2 * b * x * y + d * (y * y)) =
      (a * x + b * y) * (a * x + b * y) + (a * d - b * b) * (y * y) := by
    have h1 := add_sq_identity (a * x) (b * y)
    have h2 : (a * x) * (a * x) = a * (a * (x * x)) := by
      rw [prod_sq_split, Int.mul_assoc]
    have h3 : (b * y) * (b * y) = (b * b) * (y * y) := prod_sq_split b y
    have h4 : (a * x) * (b * y) = a * (b * x * y) := by
      rw [Int.mul_assoc a x (b * y), ← Int.mul_assoc x b y, Int.mul_comm x b]
    have h5 : (a * d - b * b) * (y * y) = a * (d * (y * y)) - (b * b) * (y * y) := by
      rw [Int.sub_mul, Int.mul_assoc]
    have h6 : a * (a * (x * x) + 2 * b * x * y + d * (y * y)) =
        a * (a * (x * x)) + a * (2 * b * x * y) + a * (d * (y * y)) := by
      rw [Int.mul_add, Int.mul_add]
    have h7 : a * (2 * b * x * y) = 2 * (a * (b * x * y)) := by
      have ht : 2 * b * x * y = 2 * (b * x * y) := by
        rw [Int.mul_assoc 2 b x, Int.mul_assoc 2 (b * x) y]
      rw [ht, Int.mul_left_comm]
    omega
  have hrhs_pos : 0 < (a * x + b * y) * (a * x + b * y) + (a * d - b * b) * (y * y) := by
    by_cases hy : y = 0
    · subst hy
      have hx : x ≠ 0 := by
        cases hxy with
        | inl h => exact h
        | inr h => exact False.elim (h rfl)
      have hax : a * x ≠ 0 := by
        intro hz
        have hpos : 0 < (a * x) * (a * x) := by
          rw [prod_sq_split]
          exact Int.mul_pos (Int.mul_pos ha ha) (sq_pos_of_ne_zero x hx)
        rw [hz] at hpos
        omega
      have hsq := sq_pos_of_ne_zero (a * x) hax
      simp [Int.mul_zero] at *
      exact hsq
    · have h1 : 0 ≤ (a * x + b * y) * (a * x + b * y) := sq_nonneg (a * x + b * y)
      have h2 : 0 < (a * d - b * b) * (y * y) := Int.mul_pos hdet (sq_pos_of_ne_zero y hy)
      omega
  by_cases hq : 0 < a * (x * x) + 2 * b * x * y + d * (y * y)
  · exact hq
  · have hnonpos : a * (a * (x * x) + 2 * b * x * y + d * (y * y)) ≤ 0 := by
      have hnn : 0 ≤ a * (-(a * (x * x) + 2 * b * x * y + d * (y * y))) :=
        Int.mul_nonneg (by omega) (by omega)
      rw [Int.mul_neg] at hnn
      omega
    omega

/-- Theorem 7 (Exact Cayley-Mobius Schur-Cohn / Routh-Hurwitz Equivalence for Degree 2):
    For a monic quadratic characteristic polynomial `p(z) = z^2 + c1*z + c0` with
    Cayley-transformed Routh coefficients `a2 = 1 - c1 + c0`, `a1 = 2*(1 - c0)`,
    `a0 = 1 + c1 + c0`, strict positivity of the Routh column (`a2 > 0 ∧ a1 > 0 ∧ a0 > 0`)
    is algebraically equivalent to the Schur-Cohn Jury disk conditions
    `p(1) > 0 ∧ p(-1) > 0 ∧ -1 < c0 < 1` and satisfies `a2 * a0 = (1 + c0)^2 - c1^2`. -/
theorem cayley_mobius_disk_to_lhp_degree2
    (c1 c0 : Int) :
    let a2 := 1 - c1 + c0
    let a1 := 2 * (1 - c0)
    let a0 := 1 + c1 + c0
    (a2 * a0 = (1 + c0) * (1 + c0) - c1 * c1) ∧
    (a2 + a0 = 2 * (1 + c0)) ∧
    ((0 < a2 ∧ 0 < a1 ∧ 0 < a0) ↔ (0 < 1 + c1 + c0 ∧ 0 < 1 - c1 + c0 ∧ -1 < c0 ∧ c0 < 1)) := by
  intro a2 a1 a0
  have hprod : a2 * a0 = (1 + c0) * (1 + c0) - c1 * c1 := by
    have h1 : a2 = (1 + c0) - c1 := by change 1 - c1 + c0 = (1 + c0) - c1; omega
    have h2 : a0 = (1 + c0) + c1 := by change 1 + c1 + c0 = (1 + c0) + c1; omega
    rw [h1, h2]
    exact (sq_diff_factor (1 + c0) c1).symm
  refine ⟨hprod, by omega, ?_⟩
  constructor
  · intro ⟨h2, h1, h0⟩
    refine ⟨h0, h2, by omega, by omega⟩
  · intro ⟨hp1, hpm1, hlo, hhi⟩
    exact ⟨hpm1, by omega, hp1⟩

/- =========================================================================
   GROUP B (SOP-16): Ibn al-Nafis Septal Firewall <-> BP Cavity Exclusion
   vs. STA Self-Echo Double-Counting & Non-Backtracking Trace Zeroing
   ========================================================================= -/

/-- Theorem 8 (Ibn al-Nafis Septal Firewall <-> BP Cavity Exclusion Isomorphism):
    In the 3-node grounded Laplacian `L_red = [[w1 + w_sep, -w1], [-w1, w1 + w2]]`
    with `w1, w2 > 0` and septal/cavity-leak conductance `w_sep >= 0`:
    `det(L_red) = w_sep*(w1 + w2) + w1*w2`; exact cavity exclusion (`w_sep = 0`)
    achieves 100% forward conductance (`det = w1 * w2`), while any positive leak
    `w_sep > 0` strictly inflates `det` above `w1 * w2` (diluting forward throughput). -/
theorem nafis_cavity_firewall_zero_leak_isomorphism
    (w1 w2 w_sep : Int)
    (hw1 : 0 < w1) (hw2 : 0 < w2) (hws : 0 ≤ w_sep) :
    let det := (w1 + w_sep) * (w1 + w2) - w1 * w1
    (det = w_sep * (w1 + w2) + w1 * w2) ∧
    (det = w1 * w2 ↔ w_sep = 0) ∧
    (0 < w_sep → w1 * w2 < det) := by
  intro det
  have hdet : det = w_sep * (w1 + w2) + w1 * w2 := by
    change (w1 + w_sep) * (w1 + w2) - w1 * w1 = w_sep * (w1 + w2) + w1 * w2
    rw [Int.add_mul, Int.mul_add]
    omega
  have hsum_pos : 0 < w1 + w2 := by omega
  refine ⟨hdet, ?_, ?_⟩
  · constructor
    · intro heq
      have hz : w_sep * (w1 + w2) = 0 := by omega
      by_cases hw0 : w_sep = 0
      · exact hw0
      · have hpos : 0 < w_sep * (w1 + w2) := Int.mul_pos (by omega) hsum_pos
        omega
    · intro hw0
      rw [hdet, hw0, Int.zero_mul]
      omega
  · intro hwpos
    have hpos : 0 < w_sep * (w1 + w2) := Int.mul_pos hwpos hsum_pos
    omega

/-- Theorem 9 (STA Self-Echo Double-Counting Monotone Blowup vs Stationary BP):
    On a 2-slot link with external evidence `a > 0` and coupling `b >= 1`, exact
    cavity-excluded BP stays stationary at `a`, whereas STA self-echo recurrence
    `z (t + 1) = a + b * z t` starting at `z 0 = a` strictly increases at every
    step `t` (`z t < z (t + 1)`) and strictly exceeds `a` for every `t >= 1`. -/
theorem sta_self_echo_double_counting_blowup
    (a b : Int) (z : Nat → Int)
    (ha : 0 < a) (hb : 1 ≤ b)
    (hz0 : z 0 = a)
    (hstep : ∀ t, z (t + 1) = a + b * z t) :
    (∀ t : Nat, 0 < z t ∧ z t < z (t + 1)) ∧ (∀ t : Nat, a < z (t + 1)) := by
  have hmain : ∀ t : Nat, 0 < z t ∧ a ≤ z t ∧ z t < z (t + 1) := by
    intro t
    induction t with
    | zero =>
      have h1 : z (0 + 1) = a + b * a := by
        have hs := hstep 0
        rw [hz0] at hs
        exact hs
      have hba : a ≤ b * a := by
        have hdiff : b * a - a = (b - 1) * a := by
          rw [Int.sub_mul, Int.one_mul]
        have hnn : 0 ≤ (b - 1) * a := Int.mul_nonneg (by omega) (by omega)
        omega
      refine ⟨by omega, by omega, by omega⟩
    | succ k ih =>
      have ⟨hpos, ha_le, hlt⟩ := ih
      have hs2 : z (k + 1 + 1) = a + b * z (k + 1) := hstep (k + 1)
      have hpos1 : 0 < z (k + 1) := by omega
      have hba1 : z (k + 1) ≤ b * z (k + 1) := by
        have hdiff : b * z (k + 1) - z (k + 1) = (b - 1) * z (k + 1) := by
          rw [Int.sub_mul, Int.one_mul]
        have hnn : 0 ≤ (b - 1) * z (k + 1) := Int.mul_nonneg (by omega) (by omega)
        omega
      refine ⟨hpos1, by omega, by omega⟩
  constructor
  · intro t
    have ⟨h1, _, h3⟩ := hmain t
    exact ⟨h1, h3⟩
  · intro t
    have ⟨_, h2, h3⟩ := hmain t
    omega

/-- Theorem 10 (Hashimoto Non-Backtracking 2-Cycle Trace Annihilation vs Opposing E/I Echo):
    Excluding backtracking 2-cycles zeroes the `2 * w12 * w21` 2-cycle trace
    contribution identically, whereas including backtracking produces strictly
    negative 2-cycle trace for Dale-opposing E/I pairs (`w12 > 0, w21 < 0`) and
    strictly positive 2-cycle trace for unsigned positive pairs (`w12 > 0, w21 > 0`). -/
theorem hashimoto_nonbacktracking_zero_2cycle_trace
    (w12 w21 : Int) :
    (0 * (w12 * w21) = 0) ∧
    (0 < w12 → w21 < 0 → 2 * (w12 * w21) < 0) ∧
    (0 < w12 → 0 < w21 → 0 < 2 * (w12 * w21)) := by
  refine ⟨Int.zero_mul _, ?_, ?_⟩
  · intro h1 h2
    have hpos : 0 < w12 * (-w21) := Int.mul_pos h1 (by omega)
    rw [Int.mul_neg] at hpos
    omega
  · intro h1 h2
    have hpos : 0 < w12 * w21 := Int.mul_pos h1 h2
    omega

/-- Theorem 11 (Acyclic Chain Exact Finite-Horizon Convergence):
    On an acyclic chain / DAG of horizon `d`, if residual error drops to `0` at
    step `d` and zero error is a fixed point (`e t = 0 → e (t + 1) = 0`), then
    error remains identically `0` for every sweep `k >= d`. -/
theorem chain_bp_exact_finite_horizon_convergence
    (e : Nat → Int) (d : Nat)
    (hreach : e d = 0)
    (hfix : ∀ t, e t = 0 → e (t + 1) = 0) :
    ∀ m : Nat, e (d + m) = 0 := by
  intro m
  induction m with
  | zero => exact hreach
  | succ k ih =>
    have hnext : d + (k + 1) = (d + k) + 1 := by omega
    rw [hnext]
    exact hfix (d + k) ih

/- =========================================================================
   GROUP C (EXP-Q43b): MaleCNS 5-Operator Tomography x Wave-22 Routing Models
   (Model Carving, MoLT Prop 1, MUX Cor 14-15, Floodgates, Schur Dark Shadow)
   ========================================================================= -/

/-- Theorem 12 (Unsigned Network Zero-Frustration & Zero-Incoherent-Triad Law):
    For any unsigned non-negative weights `w12, w23, w31 >= 0` (`MoLT`, `MUX`,
    `Floodgates`, unsigned `Model Carving`), every triad weight product is
    non-negative (`0` incoherent FFLs, `0` negative 3-cycles), and the Laplacian
    energy vanishes on every uniform mode `x = y = z = c` (zero frustration). -/
theorem unsigned_network_zero_frustration_theorem
    (w12 w23 w31 c : Int)
    (h12 : 0 ≤ w12) (h23 : 0 ≤ w23) (h31 : 0 ≤ w31) :
    (0 ≤ w12 * w23 * w31) ∧
    (w12 * ((c - c) * (c - c)) + w23 * ((c - c) * (c - c)) + w31 * ((c - c) * (c - c)) = 0) := by
  have hp : 0 ≤ w12 * w23 * w31 := Int.mul_nonneg (Int.mul_nonneg h12 h23) h31
  refine ⟨hp, ?_⟩
  have hcc : c - c = 0 := by omega
  rw [hcc]
  simp [Int.mul_zero]

/-- Theorem 13 (Anti-Symmetric Skip vs Dale-Inhibitory Symmetrization Obstruction):
    When a forward residual skip `w_fwd > 0` dominates a backward inhibitory skip
    `-w_bwd` (`0 <= w_bwd < w_fwd`, as in folded `Model Carving`), the symmetrized
    interaction `w_fwd + (-w_bwd)` stays strictly positive (cannot frustrate `L_sigma`).
    Conversely, Dale-inhibitory dominance (`w_bwd > w_fwd`, as in MaleCNS `ER -> EPG`)
    flips the symmetrized interaction strictly negative (`w_fwd + (-w_bwd) < 0`). -/
theorem antisymmetric_skip_positive_symmetrization_obstruction
    (w_fwd w_bwd : Int) :
    (w_bwd < w_fwd → 0 < w_fwd + (-w_bwd)) ∧
    (w_fwd < w_bwd → w_fwd + (-w_bwd) < 0) := by
  constructor
  · intro h; omega
  · intro h; omega

/-- Theorem 14 (MoLT Proposition 1 — Strictly Triangular Prefix Finite-Horizon Lock):
    For any recurrent loop operator `z : Nat → Nat → Int` (`z r t` = state of token
    `t` at loop `r`) whose token `0` restarts identically for all `r >= 1` and whose
    update at `(r+1, t+1)` depends strictly on prefix `j <= t` at loop `r`, induction
    on token index `t` proves exact stabilization `z r t = z (t + 1) t` for ALL
    `r >= t + 1` with ZERO Lipschitz contraction assumption. -/
theorem molt_triangular_prefix_nilpotent_lock
    (z : Nat → Nat → Int)
    (h0 : ∀ r1 r2 : Nat, 1 ≤ r1 → 1 ≤ r2 → z r1 0 = z r2 0)
    (hstep : ∀ t r1 r2 : Nat,
      (∀ j : Nat, j ≤ t → z r1 j = z r2 j) → z (r1 + 1) (t + 1) = z (r2 + 1) (t + 1)) :
    ∀ t r : Nat, t + 1 ≤ r → z r t = z (t + 1) t := by
  have hstrong : ∀ m : Nat, ∀ j : Nat, j ≤ m → ∀ r : Nat, j + 1 ≤ r → z r j = z (j + 1) j := by
    intro m
    induction m with
    | zero =>
      intro j hj r hr
      have hj0 : j = 0 := by omega
      subst hj0
      exact h0 r 1 hr (by omega)
    | succ k ih =>
      intro j hj r hr
      by_cases hjk : j ≤ k
      · exact ih j hjk r hr
      · have hj_eq : j = k + 1 := by omega
        subst hj_eq
        have hr_eq : r = (r - 1) + 1 := by omega
        rw [hr_eq]
        apply hstep k (r - 1) (k + 1)
        intro u hu
        have h1 := ih u hu (r - 1) (by omega)
        have h2 := ih u hu (k + 1) (by omega)
        rw [h1, h2]
  intro t r hr
  exact hstrong t t (Nat.le_refl t) r hr

/-- Theorem 15 (MUX Corollary 14-15 — Rational Geometric Separation Margin):
    For rational geometric ratio `rho = p / q` satisfying `0 < p` and `2 * p < q`
    (e.g. Al-Kashi ternary `p = 1, q = 3`), every nonzero ternary combination
    `c0 * q + c1 * p` with `c0, c1 ∈ {-1, 0, 1}` and `(c0, c1) ≠ (0, 0)` is strictly
    nonzero and has squared separation at least `p * p` (collision-free demultiplexing). -/
theorem mux_rational_geometric_separation_margin
    (p q c0 c1 : Int)
    (hp : 0 < p) (hq : 2 * p < q)
    (hc0 : c0 = -1 ∨ c0 = 0 ∨ c0 = 1)
    (hc1 : c1 = -1 ∨ c1 = 0 ∨ c1 = 1)
    (hnz : c0 ≠ 0 ∨ c1 ≠ 0) :
    let delta := c0 * q + c1 * p
    delta ≠ 0 ∧ p * p ≤ delta * delta := by
  intro delta
  have hge_abs : p ≤ delta ∨ delta ≤ -p := by
    rcases hc0 with h0 | h0 | h0 <;> rcases hc1 with h1 | h1 | h1
    all_goals subst h0; subst h1
    · right; change (-1) * q + (-1) * p ≤ -p; omega
    · right; change (-1) * q + 0 * p ≤ -p; omega
    · right; change (-1) * q + 1 * p ≤ -p; omega
    · right; change 0 * q + (-1) * p ≤ -p; omega
    · exfalso; cases hnz with | inl h => exact h rfl | inr h => exact h rfl
    · left; change p ≤ 0 * q + 1 * p; omega
    · left; change p ≤ 1 * q + (-1) * p; omega
    · left; change p ≤ 1 * q + 0 * p; omega
    · left; change p ≤ 1 * q + 1 * p; omega
  cases hge_abs with
  | inl hpos =>
    have hdiff := sq_diff_factor delta p
    have hnn : 0 ≤ (delta - p) * (delta + p) := Int.mul_nonneg (by omega) (by omega)
    exact ⟨by omega, by omega⟩
  | inr hneg =>
    have hsq : (-delta) * (-delta) = delta * delta := by
      rw [Int.neg_mul, Int.mul_neg, Int.neg_neg]
    have hdiff : delta * delta - p * p = ((-delta) - p) * ((-delta) + p) := by
      rw [← hsq]
      exact sq_diff_factor (-delta) p
    have hnn : 0 ≤ ((-delta) - p) * ((-delta) + p) := Int.mul_nonneg (by omega) (by omega)
    exact ⟨by omega, by omega⟩

/-- Theorem 16 (Schur Complement Dark-Shadow Conservation & Strict Positivity):
    For any 2x2 block Laplacian `[[L_bb, L_bi], [L_bi, L_ii]]` with `L_bb > 0`,
    `L_ii > 0`, and strictly positive Schur complement numerator
    `S_num = L_bb * L_ii - L_bi^2 > 0`, the cleared dark shadow `L_bi^2` satisfies
    exact trace conservation `S_num + L_bi^2 = L_bb * L_ii`, strict upper bound
    `L_bi^2 < L_bb * L_ii`, and strict positivity `0 < L_bi^2` iff `L_bi ≠ 0`. -/
theorem schur_dark_shadow_conservation_and_bounds
    (L_bb L_bi L_ii : Int)
    (hbb : 0 < L_bb) (hii : 0 < L_ii)
    (hschur : 0 < L_bb * L_ii - L_bi * L_bi) :
    let S_num := L_bb * L_ii - L_bi * L_bi
    let shadow_num := L_bi * L_bi
    (S_num + shadow_num = L_bb * L_ii) ∧
    (0 ≤ shadow_num ∧ shadow_num < L_bb * L_ii) ∧
    (L_bi ≠ 0 → 0 < shadow_num) := by
  intro S_num shadow_num
  have _ := hbb
  have _ := hii
  refine ⟨by omega, ⟨sq_nonneg L_bi, by omega⟩, ?_⟩
  intro hne
  exact sq_pos_of_ne_zero L_bi hne

#print axioms MaleCNSNeuroBridge.damped_bp_real_eigenvalue_stability_window
#print axioms MaleCNSNeuroBridge.damped_bp_positive_runaway_obstruction
#print axioms MaleCNSNeuroBridge.damped_bp_complex_oscillator_stability_threshold
#print axioms MaleCNSNeuroBridge.damped_bp_oscillatory_undamped_divergence_damped_stabilization
#print axioms MaleCNSNeuroBridge.signed_bethe_hessian_2x2_frustration_gap
#print axioms MaleCNSNeuroBridge.bethe_hessian_pd_implies_strict_frustration
#print axioms MaleCNSNeuroBridge.cayley_mobius_disk_to_lhp_degree2
#print axioms MaleCNSNeuroBridge.nafis_cavity_firewall_zero_leak_isomorphism
#print axioms MaleCNSNeuroBridge.sta_self_echo_double_counting_blowup
#print axioms MaleCNSNeuroBridge.hashimoto_nonbacktracking_zero_2cycle_trace
#print axioms MaleCNSNeuroBridge.chain_bp_exact_finite_horizon_convergence
#print axioms MaleCNSNeuroBridge.unsigned_network_zero_frustration_theorem
#print axioms MaleCNSNeuroBridge.antisymmetric_skip_positive_symmetrization_obstruction
#print axioms MaleCNSNeuroBridge.molt_triangular_prefix_nilpotent_lock
#print axioms MaleCNSNeuroBridge.mux_rational_geometric_separation_margin
#print axioms MaleCNSNeuroBridge.schur_dark_shadow_conservation_and_bounds

end MaleCNSNeuroBridge
