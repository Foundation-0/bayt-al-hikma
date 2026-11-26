/-
Classical Heritage Atlas: Cryptographically Pinned Islamic Scientific Heritage Corpus Atlas & K_10 Mesh
Pure-Init Lean 4.36.0 Formal Companion (zero external imports, zero Mathlib).

Certifies 17 public theorems (15 universally quantified ∀ theorems + 2 closed ground
propositions; 18 kernel-checked theorems incl. 1 private helper, plus 1 private Bool helper def) spanning:
  1. K_N balanced silo-cut simplex identities, K_10 5|5 destruction ladder,
     tetrahedral Z_2 Bianchi conservation, 3x3 grounded-Laplacian Kirchhoff Schur-complement
     compounding, and uniform-K_N Kirchhoff dipole effective-resistance & Foster sum law
  2. Classical exact-operator identities and obstructions for anchor nodes h00..h09:
     Al-Khwarizmi (completing the square), Thabit ibn Qurra (amicable product identity &
     n=3 composite obstruction), Al-Biruni (cleared dip-horizon radius), Ibn al-Haytham
     (2D Householder specular reflection law, Pythagorean circle & ray-norm invariance),
     Umar al-Khayyam (depressed-cubic positive negated discriminant), Nasir al-Din al-Tusi
     (2x2 counter-rotating orthogonal matrix curl annihilation & explicit 4-matrix 3x3 SO(3)
     spherical hippopede/commutator obstruction), Jamshid al-Kashi (cubic difference
     factorization), Kamal al-Din al-Farisi (stationary-deviation Snell caustic elimination
     & Alexander dark-band separation), Al-Khazini (hydrostatic alloy inverse), and
     Ibn al-Nafis (2x2 grounded-Laplacian Kirchhoff Schur-complement pulmonary rerouting
     & septal-leak conductance jump).
-/

namespace ClassicalHeritageAtlas

private theorem mul_pos_of_pos {a b : Int} (ha : 0 < a) (hb : 0 < b) : 0 < a * b :=
  Int.mul_pos ha hb

private def triParity (a b c : Bool) : Bool :=
  xor a (xor b c)

/-- Theorem 1: Universal complete-graph bipartition cut edge count in doubled integer form.
Splitting K_(a+b) into silos of sizes a and b destroys exactly a * b cross-silo edges. -/
theorem kn_silo_cut_edges_exact (a b : Int) :
    (a + b) * (a + b - 1) - a * (a - 1) - b * (b - 1) = 2 * a * b := by
  have h1 : (a + b) * (a + b - 1) = a * (a + b - 1) + b * (a + b - 1) :=
    Int.add_mul a b (a + b - 1)
  have h2 : a * (a + b - 1) = a * (a - 1) + a * b := by
    have hsplit : a + b - 1 = (a - 1) + b := by omega
    rw [hsplit]
    exact Int.mul_add a (a - 1) b
  have h3 : b * (a + b - 1) = b * (b - 1) + b * a := by
    have hsplit : a + b - 1 = (b - 1) + a := by omega
    rw [hsplit]
    exact Int.mul_add b (b - 1) a
  have hcomm : b * a = a * b := Int.mul_comm b a
  have h2ab : 2 * a * b = 2 * (a * b) := Int.mul_assoc 2 a b
  omega

/-- Theorem 2: Exact K_10 5|5 silo-cut destruction ladder across orders 1, 2, and 3.
Cutting K_10 into two 5-node silos severs 25/45 = 5/9 of edges, 100/120 = 5/6 of
triangles, and 200/210 = 20/21 of tetrahedra, with strict higher-order amplification
5/9 < 5/6 < 20/21 in cleared integer cross-products. -/
theorem k10_silo_cut_five_five_ladder :
    25 * 9 = 5 * 45 ∧
    100 * 6 = 5 * 120 ∧
    200 * 21 = 20 * 210 ∧
    5 * 6 < 5 * 9 ∧
    5 * 21 < 20 * 6 := by
  decide

/-- Theorem 3: Universal Z_2 tetrahedral Bianchi boundary conservation (d^2 = 0 mod 2).
For every 6-tuple of Boolean edge obstruction signs on K_4, the XOR of the 4 face
triangle parities vanishes identically (so frustrated faces always occur in even count). -/
theorem tetrahedral_z2_bianchi_universal (a b c d e f : Bool) :
    xor (triParity a b d)
      (xor (triParity a c e)
        (xor (triParity b c f) (triParity d e f))) = false := by
  cases a <;> cases b <;> cases c <;> cases d <;> cases e <;> cases f <;> rfl

/-- Theorem 4: Universal 3-node grounded-Laplacian Kirchhoff Schur-complement elimination
and strict conductance compounding on any triangle with positive indirect legs a, b > 0.
For direct conductance w on (1, 2) and series legs a on (1, 3), b on (2, 3), grounding node 2
gives the 2x2 Laplacian minor L_red = [[w + a, -a], [-a, a + b]] with determinant
det_red = (w + a)*(a + b) - a^2 = w*(a + b) + a*b; under Kirchhoff internal balance
(a + b)*v3 = a*v1 + b*v2, total terminal current i1 = w*(v1 - v2) + a*(v1 - v3) equals
i2 = w*(v1 - v2) + b*(v3 - v2), satisfies cleared Schur Ohm's law (a + b)*i1 = det_red*(v1 - v2),
and strictly exceeds the direct conductance w: w*(a + b) < det_red. -/
theorem schur_3node_compounding_strict (w a b v1 v2 v3 : Int)
    (ha : 0 < a) (hb : 0 < b)
    (hkirch : (a + b) * v3 = a * v1 + b * v2) :
    let det_red := (w + a) * (a + b) - a * a
    let i1 := w * (v1 - v2) + a * (v1 - v3)
    let i2 := w * (v1 - v2) + b * (v3 - v2)
    (det_red = w * (a + b) + a * b) ∧
    (i1 = i2) ∧
    ((a + b) * i1 = det_red * (v1 - v2)) ∧
    (w * (a + b) < det_red) := by
  intro det_red i1 i2
  have hdet : det_red = w * (a + b) + a * b := by
    change (w + a) * (a + b) - a * a = _
    rw [Int.add_mul, Int.mul_add a a b]
    omega
  have hbal : a * (v1 - v3) = b * (v3 - v2) := by
    have h1 : (a + b) * v3 = a * v3 + b * v3 := Int.add_mul a b v3
    have h2 : a * (v1 - v3) = a * v1 - a * v3 := Int.mul_sub a v1 v3
    have h3 : b * (v3 - v2) = b * v3 - b * v2 := Int.mul_sub b v3 v2
    omega
  have hi_eq : i1 = i2 := by
    change w * (v1 - v2) + a * (v1 - v3) = w * (v1 - v2) + b * (v3 - v2)
    rw [hbal]
  have hohm : (a + b) * i1 = det_red * (v1 - v2) := by
    change (a + b) * (w * (v1 - v2) + a * (v1 - v3)) = det_red * (v1 - v2)
    rw [Int.mul_add (a + b) (w * (v1 - v2)) (a * (v1 - v3))]
    have hw_term : (a + b) * (w * (v1 - v2)) = (w * (a + b)) * (v1 - v2) := by
      rw [← Int.mul_assoc (a + b) w (v1 - v2), Int.mul_comm (a + b) w]
    have ha_diff : (a + b) * (v1 - v3) = b * (v1 - v2) := by
      rw [Int.mul_sub (a + b) v1 v3, hkirch, Int.add_mul a b v1, Int.mul_sub b v1 v2]
      omega
    have ha_term : (a + b) * (a * (v1 - v3)) = (a * b) * (v1 - v2) := by
      calc (a + b) * (a * (v1 - v3))
          = ((a + b) * a) * (v1 - v3) := (Int.mul_assoc (a + b) a (v1 - v3)).symm
        _ = (a * (a + b)) * (v1 - v3) := by rw [Int.mul_comm (a + b) a]
        _ = a * ((a + b) * (v1 - v3)) := Int.mul_assoc a (a + b) (v1 - v3)
        _ = a * (b * (v1 - v2)) := by rw [ha_diff]
        _ = (a * b) * (v1 - v2) := (Int.mul_assoc a b (v1 - v2)).symm
    rw [hw_term, ha_term, hdet, Int.add_mul (w * (a + b)) (a * b) (v1 - v2)]
  have hab : 0 < a * b := mul_pos_of_pos ha hb
  exact ⟨hdet, hi_eq, hohm, by omega⟩

/-- Theorem 5: Universal uniform-K_N Kirchhoff dipole effective-resistance & Foster sum law.
On complete graph K_n (n >= 2) with uniform edge conductance w > 0, for any dipole potential
profile (vs at source s, vt < vs at sink t, vm at all n - 2 internal vertices) satisfying
internal Kirchhoff balance 2*vm = vs + vt:
  (1) every internal vertex has zero net Laplacian current (i_m = 0);
  (2) total Laplacian current across all n vertices sums to zero: i_s + i_t + (n - 2)*i_m = 0;
  (3) exact two-terminal Ohm's law 2*i_s = (n*w)*(vs - vt) (so R_eff = (vs - vt)/i_s = 2/(n*w))
      with strictly positive dipole current 0 < i_s;
  (4) summing w*R_eff across all C(n, 2) edges gives the cleared Foster identity
      (n*(n - 1))*(w*(vs - vt)) = (n - 1)*(2*i_s) (i.e. C(n, 2)*w*R_eff = n - 1). -/
theorem foster_uniform_kn_cleared (n w vs vt vm : Int)
    (hn : 2 ≤ n) (hw : 0 < w) (hdrop : vt < vs)
    (hkirch_int : 2 * vm = vs + vt) :
    let i_s := w * (vs - vt) + (n - 2) * (w * (vs - vm))
    let i_t := w * (vt - vs) + (n - 2) * (w * (vt - vm))
    let i_m := w * (vm - vs) + w * (vm - vt) + (n - 3) * (w * (vm - vm))
    (i_m = 0) ∧
    (i_s + i_t + (n - 2) * i_m = 0) ∧
    (2 * i_s = (n * w) * (vs - vt)) ∧
    (0 < i_s) ∧
    ((n * (n - 1)) * (w * (vs - vt)) = (n - 1) * (2 * i_s)) := by
  intro i_s i_t i_m
  have him : i_m = 0 := by
    change w * (vm - vs) + w * (vm - vt) + (n - 3) * (w * (vm - vm)) = 0
    have hself : vm - vm = 0 := by omega
    rw [hself, Int.mul_zero, Int.mul_zero, Int.add_zero, ← Int.mul_add]
    have hsum : (vm - vs) + (vm - vt) = 0 := by omega
    rw [hsum, Int.mul_zero]
  have hcons : i_s + i_t + (n - 2) * i_m = 0 := by
    rw [him, Int.mul_zero, Int.add_zero]
    change (w * (vs - vt) + (n - 2) * (w * (vs - vm))) +
      (w * (vt - vs) + (n - 2) * (w * (vt - vm))) = 0
    have hst : w * (vs - vt) + w * (vt - vs) = 0 := by
      rw [← Int.mul_add]
      have hz : (vs - vt) + (vt - vs) = 0 := by omega
      rw [hz, Int.mul_zero]
    have hsm : (n - 2) * (w * (vs - vm)) + (n - 2) * (w * (vt - vm)) = 0 := by
      rw [← Int.mul_add, ← Int.mul_add]
      have hz : (vs - vm) + (vt - vm) = 0 := by omega
      rw [hz, Int.mul_zero, Int.mul_zero]
    omega
  have h2is : 2 * i_s = (n * w) * (vs - vt) := by
    change 2 * (w * (vs - vt) + (n - 2) * (w * (vs - vm))) = (n * w) * (vs - vt)
    have hmid : 2 * (vs - vm) = vs - vt := by omega
    have h1 : 2 * ((n - 2) * (w * (vs - vm))) = (n - 2) * (w * (vs - vt)) := by
      calc 2 * ((n - 2) * (w * (vs - vm)))
          = ((n - 2) * 2) * (w * (vs - vm)) := by
              rw [← Int.mul_assoc 2 (n - 2) (w * (vs - vm)), Int.mul_comm 2 (n - 2)]
        _ = (n - 2) * (2 * (w * (vs - vm))) := Int.mul_assoc (n - 2) 2 (w * (vs - vm))
        _ = (n - 2) * (w * (2 * (vs - vm))) := by
              rw [← Int.mul_assoc 2 w (vs - vm), Int.mul_comm 2 w, Int.mul_assoc w 2 (vs - vm)]
        _ = (n - 2) * (w * (vs - vt)) := by rw [hmid]
    rw [Int.mul_add 2 (w * (vs - vt)) ((n - 2) * (w * (vs - vm))), h1]
    have hsum_n : 2 * (w * (vs - vt)) + (n - 2) * (w * (vs - vt)) = n * (w * (vs - vt)) := by
      rw [← Int.add_mul 2 (n - 2) (w * (vs - vt))]
      have hn2 : 2 + (n - 2) = n := by omega
      rw [hn2]
    rw [hsum_n, ← Int.mul_assoc n w (vs - vt)]
  have his_pos : 0 < i_s := by
    have hnw : 0 < n * w := mul_pos_of_pos (by omega) hw
    have hdv : 0 < vs - vt := by omega
    have hprod : 0 < (n * w) * (vs - vt) := mul_pos_of_pos hnw hdv
    omega
  have hfoster : (n * (n - 1)) * (w * (vs - vt)) = (n - 1) * (2 * i_s) := by
    rw [h2is]
    calc (n * (n - 1)) * (w * (vs - vt))
        = ((n - 1) * n) * (w * (vs - vt)) := by rw [Int.mul_comm n (n - 1)]
      _ = (n - 1) * (n * (w * (vs - vt))) := Int.mul_assoc (n - 1) n (w * (vs - vt))
      _ = (n - 1) * ((n * w) * (vs - vt)) := by rw [Int.mul_assoc n w (vs - vt)]
  exact ⟨him, hcons, h2is, his_pos, hfoster⟩

/-- Theorem 6 (h00 Al-Khwarizmi): Universal algebraic completing-the-square identity.
For all integers x and b, 4 * (x^2 + b * x) + b^2 = (2 * x + b)^2 identically. -/
theorem khwarizmi_completing_square_exact (x b : Int) :
    4 * (x * x + b * x) + b * b = (2 * x + b) * (2 * x + b) := by
  have h1 : (2 * x + b) * (2 * x + b) = 2 * x * (2 * x + b) + b * (2 * x + b) :=
    Int.add_mul (2 * x) b (2 * x + b)
  have h2 : 2 * x * (2 * x + b) = 2 * x * (2 * x) + 2 * x * b :=
    Int.mul_add (2 * x) (2 * x) b
  have h3 : b * (2 * x + b) = b * (2 * x) + b * b :=
    Int.mul_add b (2 * x) b
  have h4 : 2 * x * (2 * x) = 4 * (x * x) := by
    calc
      2 * x * (2 * x) = 2 * (x * (2 * x)) := Int.mul_assoc 2 x (2 * x)
      _ = 2 * (2 * x * x) := by rw [Int.mul_comm x (2 * x)]
      _ = 2 * (2 * (x * x)) := by rw [Int.mul_assoc 2 x x]
      _ = (2 * 2) * (x * x) := (Int.mul_assoc 2 2 (x * x)).symm
      _ = 4 * (x * x) := rfl
  have h5 : 2 * x * b = 2 * (b * x) := by
    calc
      2 * x * b = 2 * (x * b) := Int.mul_assoc 2 x b
      _ = 2 * (b * x) := by rw [Int.mul_comm x b]
  have h6 : b * (2 * x) = 2 * (b * x) := by
    calc
      b * (2 * x) = 2 * x * b := Int.mul_comm b (2 * x)
      _ = 2 * (b * x) := h5
  have h7 : 4 * (x * x + b * x) = 4 * (x * x) + 4 * (b * x) :=
    Int.mul_add 4 (x * x) (b * x)
  omega

/-- Theorem 7 (h01 Thabit ibn Qurra): Universal amicable-sum algebraic balance identity.
For t = 2^(n-1), p = 3t - 1, q = 6t - 1, r = 18t^2 - 1, the divisor-sum bridge
(p + 1) * (q + 1) = r + 1 holds identically for every integer t. -/
theorem thabit_amicable_product_identity (t p q r : Int)
    (hp : p = 3 * t - 1) (hq : q = 6 * t - 1) (hr : r = 18 * t * t - 1) :
    (p + 1) * (q + 1) = r + 1 := by
  have hp1 : p + 1 = 3 * t := by omega
  have hq1 : q + 1 = 6 * t := by omega
  have hr1 : r + 1 = 18 * t * t := by omega
  rw [hp1, hq1, hr1]
  calc
    3 * t * (6 * t) = 3 * (t * (6 * t)) := Int.mul_assoc 3 t (6 * t)
    _ = 3 * (6 * t * t) := by rw [Int.mul_comm t (6 * t)]
    _ = (3 * 6) * (t * t) := by
      rw [Int.mul_assoc 6 t t]
      exact (Int.mul_assoc 3 6 (t * t)).symm
    _ = 18 * (t * t) := rfl
    _ = 18 * t * t := (Int.mul_assoc 18 t t).symm

/-- Theorem 8 (h01 Thabit ibn Qurra): Exact n = 3 composite primality obstruction.
At n = 3 (t = 4), Thabit's r_3 = 18 * 4^2 - 1 = 287 = 7 * 41 is strictly composite,
blocking the primality precondition required for an amicable pair at n = 3. -/
theorem thabit_n3_composite_obstruction :
    18 * 4 * 4 - 1 = 7 * 41 ∧ 1 < (7 : Int) ∧ (7 : Int) < 287 := by
  decide

/-- Theorem 9 (h02 Al-Biruni): Exact mountain-dip horizon radius equation in cleared form.
From R * (den - num) = h * num (where cos(theta) = num / den), the total distance from
Earth center satisfies R * den = (R + h) * num identically. -/
theorem biruni_dip_radius_cleared_identity (R h num den : Int)
    (hEq : R * (den - num) = h * num) :
    R * den = (R + h) * num := by
  have h1 : R * (den - num) = R * den - R * num := Int.mul_sub R den num
  have h2 : (R + h) * num = R * num + h * num := Int.add_mul R h num
  omega

/-- Theorem 10 (h03 Ibn al-Haytham): Exact 2D Householder specular reflection law,
Pythagorean rational-circle parameterization, and squared ray-norm invariance.
For any mirror normal (a, b) with D = a^2 + b^2, c = a^2 - b^2, s = 2*a*b, the cleared
2D Householder reflection H_{a,b}(vx, vy) = (-c*vx - s*vy, -s*vx + c*vy) satisfies:
  (1) Pythagorean rational-circle identity (a^2 - b^2)^2 + (2*a*b)^2 = (a^2 + b^2)^2;
  (2) exact squared ray-norm preservation rx^2 + ry^2 = D^2 * (vx^2 + vy^2);
  (3) normal component sign reversal a*rx + b*ry = -D*(a*vx + b*vy);
  (4) tangent component preservation (-b)*rx + a*ry = D*((-b)*vx + a*vy). -/
theorem haytham_reflection_norm_invariance (a b vx vy : Int) :
    let c := a * a - b * b
    let s := 2 * (a * b)
    let D := a * a + b * b
    let rx := (-c) * vx - s * vy
    let ry := (-s) * vx + c * vy
    (c * c + s * s = D * D) ∧
    (rx * rx + ry * ry = (D * D) * (vx * vx + vy * vy)) ∧
    (a * rx + b * ry = -(D * (a * vx + b * vy))) ∧
    ((-b) * rx + a * ry = D * ((-b) * vx + a * vy)) := by
  intro c s D rx ry
  have hcircle : c * c + s * s = D * D := by
    change (a * a - b * b) * (a * a - b * b) + (2 * (a * b)) * (2 * (a * b)) =
      (a * a + b * b) * (a * a + b * b)
    have h1 : (a * a - b * b) * (a * a - b * b) =
        (a * a) * (a * a) - 2 * ((a * a) * (b * b)) + (b * b) * (b * b) := by
      rw [Int.sub_mul, Int.mul_sub, Int.mul_sub, Int.mul_comm (b * b) (a * a)]
      omega
    have h2 : (a * a + b * b) * (a * a + b * b) =
        (a * a) * (a * a) + 2 * ((a * a) * (b * b)) + (b * b) * (b * b) := by
      rw [Int.add_mul, Int.mul_add, Int.mul_add, Int.mul_comm (b * b) (a * a)]
      omega
    have h3 : (2 * (a * b)) * (2 * (a * b)) = 4 * ((a * a) * (b * b)) := by
      have hab : (a * b) * (a * b) = (a * a) * (b * b) := by
        calc (a * b) * (a * b) = a * (b * (a * b)) := Int.mul_assoc a b (a * b)
          _ = a * (a * (b * b)) := by
              rw [← Int.mul_assoc b a b, Int.mul_comm b a, Int.mul_assoc a b b]
          _ = (a * a) * (b * b) := (Int.mul_assoc a a (b * b)).symm
      calc (2 * (a * b)) * (2 * (a * b)) = 2 * ((a * b) * (2 * (a * b))) := Int.mul_assoc _ _ _
        _ = 2 * (2 * ((a * b) * (a * b))) := by
            rw [← Int.mul_assoc (a * b) 2 (a * b), Int.mul_comm (a * b) 2, Int.mul_assoc 2 (a * b) (a * b)]
        _ = 4 * ((a * b) * (a * b)) := by rw [← Int.mul_assoc 2 2 _]; rfl
        _ = 4 * ((a * a) * (b * b)) := by rw [hab]
    omega
  have hnorm : rx * rx + ry * ry = (D * D) * (vx * vx + vy * vy) := by
    have hrx : rx = -(c * vx + s * vy) := by
      change (-c) * vx - s * vy = -(c * vx + s * vy)
      rw [Int.neg_mul]
      omega
    have hry : ry = c * vy - s * vx := by
      change (-s) * vx + c * vy = c * vy - s * vx
      rw [Int.neg_mul]
      omega
    rw [hrx, hry, Int.neg_mul_neg]
    have e1 : (c * vx + s * vy) * (c * vx + s * vy) =
        (c * c) * (vx * vx) + 2 * ((c * s) * (vx * vy)) + (s * s) * (vy * vy) := by
      rw [Int.add_mul, Int.mul_add, Int.mul_add]
      have p1 : c * vx * (c * vx) = (c * c) * (vx * vx) := by
        calc c * vx * (c * vx) = c * (vx * (c * vx)) := Int.mul_assoc _ _ _
          _ = c * (c * (vx * vx)) := by rw [← Int.mul_assoc vx c vx, Int.mul_comm vx c, Int.mul_assoc c vx vx]
          _ = (c * c) * (vx * vx) := (Int.mul_assoc c c (vx * vx)).symm
      have p2 : s * vy * (s * vy) = (s * s) * (vy * vy) := by
        calc s * vy * (s * vy) = s * (vy * (s * vy)) := Int.mul_assoc _ _ _
          _ = s * (s * (vy * vy)) := by rw [← Int.mul_assoc vy s vy, Int.mul_comm vy s, Int.mul_assoc s vy vy]
          _ = (s * s) * (vy * vy) := (Int.mul_assoc s s (vy * vy)).symm
      have p3 : c * vx * (s * vy) = (c * s) * (vx * vy) := by
        calc c * vx * (s * vy) = c * (vx * (s * vy)) := Int.mul_assoc _ _ _
          _ = c * (s * (vx * vy)) := by rw [← Int.mul_assoc vx s vy, Int.mul_comm vx s, Int.mul_assoc s vx vy]
          _ = (c * s) * (vx * vy) := (Int.mul_assoc c s (vx * vy)).symm
      have p4 : s * vy * (c * vx) = (c * s) * (vx * vy) := by rw [Int.mul_comm (s * vy) (c * vx), p3]
      omega
    have e2 : (c * vy - s * vx) * (c * vy - s * vx) =
        (c * c) * (vy * vy) - 2 * ((c * s) * (vx * vy)) + (s * s) * (vx * vx) := by
      rw [Int.sub_mul, Int.mul_sub, Int.mul_sub]
      have p1 : c * vy * (c * vy) = (c * c) * (vy * vy) := by
        calc c * vy * (c * vy) = c * (vy * (c * vy)) := Int.mul_assoc _ _ _
          _ = c * (c * (vy * vy)) := by rw [← Int.mul_assoc vy c vy, Int.mul_comm vy c, Int.mul_assoc c vy vy]
          _ = (c * c) * (vy * vy) := (Int.mul_assoc c c (vy * vy)).symm
      have p2 : s * vx * (s * vx) = (s * s) * (vx * vx) := by
        calc s * vx * (s * vx) = s * (vx * (s * vx)) := Int.mul_assoc _ _ _
          _ = s * (s * (vx * vx)) := by rw [← Int.mul_assoc vx s vx, Int.mul_comm vx s, Int.mul_assoc s vx vx]
          _ = (s * s) * (vx * vx) := (Int.mul_assoc s s (vx * vx)).symm
      have p3 : c * vy * (s * vx) = (c * s) * (vx * vy) := by
        calc c * vy * (s * vx) = c * (vy * (s * vx)) := Int.mul_assoc _ _ _
          _ = c * (s * (vy * vx)) := by rw [← Int.mul_assoc vy s vx, Int.mul_comm vy s, Int.mul_assoc s vy vx]
          _ = (c * s) * (vy * vx) := (Int.mul_assoc c s (vy * vx)).symm
          _ = (c * s) * (vx * vy) := by rw [Int.mul_comm vy vx]
      have p4 : s * vx * (c * vy) = (c * s) * (vx * vy) := by rw [Int.mul_comm (s * vx) (c * vy), p3]
      omega
    have fx : (c * c) * (vx * vx) + (s * s) * (vx * vx) = (D * D) * (vx * vx) := by
      rw [← Int.add_mul, hcircle]
    have fy : (s * s) * (vy * vy) + (c * c) * (vy * vy) = (D * D) * (vy * vy) := by
      rw [← Int.add_mul, Int.add_comm (s * s) (c * c), hcircle]
    have hrhs : (D * D) * (vx * vx + vy * vy) = (D * D) * (vx * vx) + (D * D) * (vy * vy) :=
      Int.mul_add (D * D) (vx * vx) (vy * vy)
    omega
  have hdot_n : a * rx + b * ry = -(D * (a * vx + b * vy)) := by
    have h1 : a * rx = (-(a * c)) * vx - (a * s) * vy := by
      change a * ((-c) * vx - s * vy) = _
      rw [Int.mul_sub, Int.neg_mul, Int.mul_neg, ← Int.mul_assoc a c vx, ← Int.mul_assoc a s vy, Int.neg_mul]
    have h2 : b * ry = (-(b * s)) * vx + (b * c) * vy := by
      change b * ((-s) * vx + c * vy) = _
      rw [Int.mul_add, Int.neg_mul, Int.mul_neg, ← Int.mul_assoc b s vx, ← Int.mul_assoc b c vy, Int.neg_mul]
    have hax : -(a * c) + -(b * s) = -(D * a) := by
      change -(a * (a * a - b * b)) + -(b * (2 * (a * b))) = -((a * a + b * b) * a)
      rw [Int.mul_sub, Int.add_mul]
      have p1 : b * (2 * (a * b)) = 2 * (a * (b * b)) := by
        calc b * (2 * (a * b)) = 2 * (b * (a * b)) := by rw [← Int.mul_assoc b 2 (a * b), Int.mul_comm b 2, Int.mul_assoc 2 b (a * b)]
          _ = 2 * (a * (b * b)) := by rw [← Int.mul_assoc b a b, Int.mul_comm b a, Int.mul_assoc a b b]
      have p2 : a * (a * a) = (a * a) * a := (Int.mul_assoc a a a).symm
      have p3 : (b * b) * a = a * (b * b) := Int.mul_comm (b * b) a
      omega
    have hby : b * c - a * s = -(D * b) := by
      change b * (a * a - b * b) - a * (2 * (a * b)) = -((a * a + b * b) * b)
      rw [Int.mul_sub, Int.add_mul]
      have p1 : a * (2 * (a * b)) = 2 * ((a * a) * b) := by
        calc a * (2 * (a * b)) = 2 * (a * (a * b)) := by rw [← Int.mul_assoc a 2 (a * b), Int.mul_comm a 2, Int.mul_assoc 2 a (a * b)]
          _ = 2 * ((a * a) * b) := by rw [← Int.mul_assoc a a b]
      have p2 : b * (a * a) = (a * a) * b := Int.mul_comm b (a * a)
      have p3 : b * (b * b) = (b * b) * b := (Int.mul_assoc b b b).symm
      omega
    have hrhs : -(D * (a * vx + b * vy)) = (-(D * a)) * vx + (-(D * b)) * vy := by
      rw [Int.mul_add, ← Int.mul_assoc D a vx, ← Int.mul_assoc D b vy, Int.neg_mul, Int.neg_mul]
      omega
    have hlhs : a * rx + b * ry = (-(a * c) + -(b * s)) * vx + (b * c - a * s) * vy := by
      rw [h1, h2, Int.add_mul, Int.sub_mul]
      omega
    rw [hlhs, hax, hby, hrhs]
  have hdot_t : (-b) * rx + a * ry = D * ((-b) * vx + a * vy) := by
    have h1 : (-b) * rx = (b * c) * vx + (b * s) * vy := by
      change (-b) * ((-c) * vx - s * vy) = _
      rw [Int.mul_sub, Int.neg_mul, Int.neg_mul, Int.mul_neg, Int.neg_neg,
          ← Int.mul_assoc b c vx, Int.neg_mul, ← Int.mul_assoc b s vy]
      omega
    have h2 : a * ry = (-(a * s)) * vx + (a * c) * vy := by
      change a * ((-s) * vx + c * vy) = _
      rw [Int.mul_add, Int.neg_mul, Int.mul_neg, ← Int.mul_assoc a s vx, ← Int.mul_assoc a c vy, Int.neg_mul]
    have htx : b * c + -(a * s) = -(D * b) := by
      change b * (a * a - b * b) + -(a * (2 * (a * b))) = -((a * a + b * b) * b)
      rw [Int.mul_sub, Int.add_mul]
      have p1 : a * (2 * (a * b)) = 2 * ((a * a) * b) := by
        calc a * (2 * (a * b)) = 2 * (a * (a * b)) := by rw [← Int.mul_assoc a 2 (a * b), Int.mul_comm a 2, Int.mul_assoc 2 a (a * b)]
          _ = 2 * ((a * a) * b) := by rw [← Int.mul_assoc a a b]
      have p2 : b * (a * a) = (a * a) * b := Int.mul_comm b (a * a)
      have p3 : b * (b * b) = (b * b) * b := (Int.mul_assoc b b b).symm
      omega
    have hty : b * s + a * c = D * a := by
      change b * (2 * (a * b)) + a * (a * a - b * b) = (a * a + b * b) * a
      rw [Int.mul_sub, Int.add_mul]
      have p1 : b * (2 * (a * b)) = 2 * (a * (b * b)) := by
        calc b * (2 * (a * b)) = 2 * (b * (a * b)) := by rw [← Int.mul_assoc b 2 (a * b), Int.mul_comm b 2, Int.mul_assoc 2 b (a * b)]
          _ = 2 * (a * (b * b)) := by rw [← Int.mul_assoc b a b, Int.mul_comm b a, Int.mul_assoc a b b]
      have p2 : a * (a * a) = (a * a) * a := (Int.mul_assoc a a a).symm
      have p3 : (b * b) * a = a * (b * b) := Int.mul_comm (b * b) a
      omega
    have hrhs : D * ((-b) * vx + a * vy) = (-(D * b)) * vx + (D * a) * vy := by
      rw [Int.mul_add, Int.neg_mul, Int.mul_neg, ← Int.mul_assoc D b vx, Int.neg_mul, ← Int.mul_assoc D a vy]
    have hlhs : (-b) * rx + a * ry = (b * c + -(a * s)) * vx + (b * s + a * c) * vy := by
      rw [h1, h2, Int.add_mul, Int.add_mul]
      omega
    rw [hlhs, htx, hty, hrhs]
  exact ⟨hcircle, hnorm, hdot_n, hdot_t⟩

/-- Theorem 11 (h04 Umar al-Khayyam): Strict positivity of negated depressed-cubic discriminant.
For x^3 + a * x = b with a > 0, the negated discriminant 4 * a^3 + 27 * b^2 is strictly
positive for all b, certifying the unique-real-root conic intersection regime. -/
theorem khayyam_cubic_positive_neg_discriminant (a b : Int) (ha : 0 < a) :
    0 < 4 * a * a * a + 27 * b * b := by
  have ha2 : 0 < a * a := mul_pos_of_pos ha ha
  have ha3 : 0 < a * a * a := mul_pos_of_pos ha2 ha
  have h4a3 : 4 * a * a * a = 4 * (a * a * a) := by
    calc
      4 * a * a * a = 4 * (a * a) * a := by rw [Int.mul_assoc 4 a a]
      _ = 4 * (a * a * a) := Int.mul_assoc 4 (a * a) a
  have hb2 : 0 ≤ b * b := by
    cases Int.le_total 0 b with
    | inl hge => exact Int.mul_nonneg hge hge
    | inr hle =>
      have hneg : 0 ≤ -b := by omega
      have hsq : 0 ≤ (-b) * (-b) := Int.mul_nonneg hneg hneg
      rw [Int.neg_mul_neg] at hsq
      exact hsq
  have h27b2 : 27 * b * b = 27 * (b * b) := Int.mul_assoc 27 b b
  have h27nonneg : 0 ≤ 27 * (b * b) := Int.mul_nonneg (by omega) hb2
  omega

/-- Theorem 12 (h05 Nasir al-Din al-Tusi): Exact 2x2 counter-rotating planar matrix
superposition and perpendicular-curl annihilation on the rational Pythagorean circle.
For c = p^2 - q^2, s = 2*p*q, D = p^2 + q^2, the counter-rotating 2x2 orthogonal matrices
R+ = [[c, -s], [s, c]] and R- = [[c, s], [-s, c]] acting on any vector (x, y) satisfy:
  (1) rational circle membership c^2 + s^2 = D^2;
  (2) R+ squared Euclidean norm preservation (c*x - s*y)^2 + (s*x + c*y)^2 = D^2*(x^2 + y^2);
  (3) R- squared Euclidean norm preservation (c*x + s*y)^2 + (-s*x + c*y)^2 = D^2*(x^2 + y^2);
  (4) exact matrix-vector curl annihilation (R+ + R-)(x, y) = (2*c*x, 2*c*y). -/
theorem tusi_planar_curl_annihilation (p q x y : Int) :
    let c := p * p - q * q
    let s := 2 * (p * q)
    let D := p * p + q * q
    (c * c + s * s = D * D) ∧
    ((c * x - s * y) * (c * x - s * y) + (s * x + c * y) * (s * x + c * y) =
      (D * D) * (x * x + y * y)) ∧
    ((c * x + s * y) * (c * x + s * y) + (-(s * x) + c * y) * (-(s * x) + c * y) =
      (D * D) * (x * x + y * y)) ∧
    ((c * x - s * y) + (c * x + s * y) = (2 * c) * x ∧
     (s * x + c * y) + (-(s * x) + c * y) = (2 * c) * y) := by
  intro c s D
  have hcircle : c * c + s * s = D * D := by
    change (p * p - q * q) * (p * p - q * q) + (2 * (p * q)) * (2 * (p * q)) =
      (p * p + q * q) * (p * p + q * q)
    have h1 : (p * p - q * q) * (p * p - q * q) =
        (p * p) * (p * p) - 2 * ((p * p) * (q * q)) + (q * q) * (q * q) := by
      rw [Int.sub_mul, Int.mul_sub, Int.mul_sub, Int.mul_comm (q * q) (p * p)]
      omega
    have h2 : (p * p + q * q) * (p * p + q * q) =
        (p * p) * (p * p) + 2 * ((p * p) * (q * q)) + (q * q) * (q * q) := by
      rw [Int.add_mul, Int.mul_add, Int.mul_add, Int.mul_comm (q * q) (p * p)]
      omega
    have h3 : (2 * (p * q)) * (2 * (p * q)) = 4 * ((p * p) * (q * q)) := by
      have hpq : (p * q) * (p * q) = (p * p) * (q * q) := by
        calc (p * q) * (p * q) = p * (q * (p * q)) := Int.mul_assoc p q (p * q)
          _ = p * (p * (q * q)) := by
              rw [← Int.mul_assoc q p q, Int.mul_comm q p, Int.mul_assoc p q q]
          _ = (p * p) * (q * q) := (Int.mul_assoc p p (q * q)).symm
      calc (2 * (p * q)) * (2 * (p * q)) = 2 * ((p * q) * (2 * (p * q))) := Int.mul_assoc _ _ _
        _ = 2 * (2 * ((p * q) * (p * q))) := by
            rw [← Int.mul_assoc (p * q) 2 (p * q), Int.mul_comm (p * q) 2, Int.mul_assoc 2 (p * q) (p * q)]
        _ = 4 * ((p * q) * (p * q)) := by rw [← Int.mul_assoc 2 2 _]; rfl
        _ = 4 * ((p * p) * (q * q)) := by rw [hpq]
    omega
  have pcxx : c * x * (c * x) = (c * c) * (x * x) := by
    calc c * x * (c * x) = c * (x * (c * x)) := Int.mul_assoc _ _ _
      _ = c * (c * (x * x)) := by rw [← Int.mul_assoc x c x, Int.mul_comm x c, Int.mul_assoc c x x]
      _ = (c * c) * (x * x) := (Int.mul_assoc c c (x * x)).symm
  have psyy : s * y * (s * y) = (s * s) * (y * y) := by
    calc s * y * (s * y) = s * (y * (s * y)) := Int.mul_assoc _ _ _
      _ = s * (s * (y * y)) := by rw [← Int.mul_assoc y s y, Int.mul_comm y s, Int.mul_assoc s y y]
      _ = (s * s) * (y * y) := (Int.mul_assoc s s (y * y)).symm
  have pcxsy : c * x * (s * y) = (c * s) * (x * y) := by
    calc c * x * (s * y) = c * (x * (s * y)) := Int.mul_assoc _ _ _
      _ = c * (s * (x * y)) := by rw [← Int.mul_assoc x s y, Int.mul_comm x s, Int.mul_assoc s x y]
      _ = (c * s) * (x * y) := (Int.mul_assoc c s (x * y)).symm
  have psxx : s * x * (s * x) = (s * s) * (x * x) := by
    calc s * x * (s * x) = s * (x * (s * x)) := Int.mul_assoc _ _ _
      _ = s * (s * (x * x)) := by rw [← Int.mul_assoc x s x, Int.mul_comm x s, Int.mul_assoc s x x]
      _ = (s * s) * (x * x) := (Int.mul_assoc s s (x * x)).symm
  have pcyy : c * y * (c * y) = (c * c) * (y * y) := by
    calc c * y * (c * y) = c * (y * (c * y)) := Int.mul_assoc _ _ _
      _ = c * (c * (y * y)) := by rw [← Int.mul_assoc y c y, Int.mul_comm y c, Int.mul_assoc c y y]
      _ = (c * c) * (y * y) := (Int.mul_assoc c c (y * y)).symm
  have psxcy : s * x * (c * y) = (c * s) * (x * y) := by
    calc s * x * (c * y) = s * (x * (c * y)) := Int.mul_assoc _ _ _
      _ = s * (c * (x * y)) := by rw [← Int.mul_assoc x c y, Int.mul_comm x c, Int.mul_assoc c x y]
      _ = (s * c) * (x * y) := (Int.mul_assoc s c (x * y)).symm
      _ = (c * s) * (x * y) := by rw [Int.mul_comm s c]
  have fx : (c * c) * (x * x) + (s * s) * (x * x) = (D * D) * (x * x) := by
    rw [← Int.add_mul, hcircle]
  have fy : (s * s) * (y * y) + (c * c) * (y * y) = (D * D) * (y * y) := by
    rw [← Int.add_mul, Int.add_comm (s * s) (c * c), hcircle]
  have hrhs : (D * D) * (x * x + y * y) = (D * D) * (x * x) + (D * D) * (y * y) :=
    Int.mul_add (D * D) (x * x) (y * y)
  have hnorm_pos : (c * x - s * y) * (c * x - s * y) + (s * x + c * y) * (s * x + c * y) =
      (D * D) * (x * x + y * y) := by
    have e1 : (c * x - s * y) * (c * x - s * y) =
        (c * c) * (x * x) - 2 * ((c * s) * (x * y)) + (s * s) * (y * y) := by
      rw [Int.sub_mul, Int.mul_sub, Int.mul_sub, pcxx, psyy, pcxsy, Int.mul_comm (s * y) (c * x), pcxsy]
      omega
    have e2 : (s * x + c * y) * (s * x + c * y) =
        (s * s) * (x * x) + 2 * ((c * s) * (x * y)) + (c * c) * (y * y) := by
      rw [Int.add_mul, Int.mul_add, Int.mul_add, psxx, pcyy, psxcy, Int.mul_comm (c * y) (s * x), psxcy]
      omega
    omega
  have hnorm_neg : (c * x + s * y) * (c * x + s * y) + (-(s * x) + c * y) * (-(s * x) + c * y) =
      (D * D) * (x * x + y * y) := by
    have hrew : -(s * x) + c * y = c * y - s * x := by omega
    rw [hrew]
    have e1 : (c * x + s * y) * (c * x + s * y) =
        (c * c) * (x * x) + 2 * ((c * s) * (x * y)) + (s * s) * (y * y) := by
      rw [Int.add_mul, Int.mul_add, Int.mul_add, pcxx, psyy, pcxsy, Int.mul_comm (s * y) (c * x), pcxsy]
      omega
    have e2 : (c * y - s * x) * (c * y - s * x) =
        (c * c) * (y * y) - 2 * ((c * s) * (x * y)) + (s * s) * (x * x) := by
      rw [Int.sub_mul, Int.mul_sub, Int.mul_sub, pcyy, psxx, Int.mul_comm (c * y) (s * x), psxcy]
      omega
    omega
  have h2cx : (2 * c) * x = c * x + c * x := by
    have t : 2 * c = c + c := by omega
    rw [t, Int.add_mul]
  have h2cy : (2 * c) * y = c * y + c * y := by
    have t : 2 * c = c + c := by omega
    rw [t, Int.add_mul]
  exact ⟨hcircle, hnorm_pos, hnorm_neg, ⟨by omega, by omega⟩⟩

/-- Theorem 13 (h05 Nasir al-Din al-Tusi): Algebraic polynomial identity and strict positivity
for the expanded scalar coordinates of the spherical Tusi-couple hippopede and commutator.
Evaluating the expanded scalar polynomial coordinates corresponding to the four cleared rotation
stages R_z(theta) * R_y(alpha) * R_z(-2*theta) * R_y(alpha) on (0, 0, 1) (with double-angle
polynomials c2 = ct^2 - st^2, s2 = 2*st*ct, D2 = ct^2 + st^2; explicit 3x3 matrix multiplication
is verified in the Python pure-Q oracle rather than via matrix types or ca^2 + sa^2 = Da^2 here):
  (1) the expanded lateral coordinate v4y equals -2 * sa * (Da - ca) * st * ct^2;
  (2) for any non-flat tilt parameters (0 < sa, ca < Da) and generic phase (st != 0, ct != 0),
      the squared lateral coordinate v4y * v4y is strictly positive (> 0);
  (3) the expanded commutator y-coordinate st * sa - 0 has strictly positive square (> 0). -/
theorem tusi_spherical_obstruction_pos (Da ca sa ct st : Int)
    (hsa : 0 < sa) (hca : ca < Da) (hst : st ≠ 0) (hct : ct ≠ 0) :
    let c2 := ct * ct - st * st
    let s2 := 2 * (st * ct)
    let D2 := ct * ct + st * st
    let v2x := c2 * sa
    let v2y := (-s2) * sa
    let v2z := D2 * ca
    let v3x := ca * v2x + sa * v2z
    let v3y := Da * v2y
    let v4y := st * v3x + ct * v3y
    let comm_y := st * sa - 0
    (v4y = -(2 * sa * (Da - ca) * st * (ct * ct))) ∧
    (0 < v4y * v4y) ∧
    (0 < comm_y * comm_y) := by
  intro c2 s2 D2 v2x v2y v2z v3x v3y v4y comm_y
  have hv3x : v3x = 2 * sa * ca * (ct * ct) := by
    change ca * ((ct * ct - st * st) * sa) + sa * ((ct * ct + st * st) * ca) = _
    have a1 : ca * ((ct * ct - st * st) * sa) = (sa * ca) * (ct * ct - st * st) := by
      calc ca * ((ct * ct - st * st) * sa)
          = (ca * sa) * (ct * ct - st * st) := by
              rw [Int.mul_comm (ct * ct - st * st) sa, ← Int.mul_assoc ca sa (ct * ct - st * st)]
        _ = (sa * ca) * (ct * ct - st * st) := by rw [Int.mul_comm ca sa]
    have a2 : sa * ((ct * ct + st * st) * ca) = (sa * ca) * (ct * ct + st * st) := by
      rw [Int.mul_comm (ct * ct + st * st) ca, ← Int.mul_assoc sa ca (ct * ct + st * st)]
    rw [a1, a2, ← Int.mul_add]
    have hsum : (ct * ct - st * st) + (ct * ct + st * st) = 2 * (ct * ct) := by omega
    rw [hsum]
    calc (sa * ca) * (2 * (ct * ct))
        = 2 * ((sa * ca) * (ct * ct)) := by
            rw [← Int.mul_assoc (sa * ca) 2 (ct * ct), Int.mul_comm (sa * ca) 2, Int.mul_assoc 2 (sa * ca) (ct * ct)]
      _ = 2 * sa * ca * (ct * ct) := by
          rw [← Int.mul_assoc 2 (sa * ca) (ct * ct), ← Int.mul_assoc 2 sa ca]
  have hv3y : v3y = -(2 * sa * Da * (st * ct)) := by
    change Da * (-(2 * (st * ct)) * sa) = _
    rw [Int.neg_mul, Int.mul_neg]
    have hpos : Da * (2 * (st * ct) * sa) = 2 * sa * Da * (st * ct) := by
      calc Da * (2 * (st * ct) * sa)
          = Da * (2 * (sa * (st * ct))) := by
              rw [Int.mul_assoc 2 (st * ct) sa, Int.mul_comm (st * ct) sa]
        _ = 2 * (Da * (sa * (st * ct))) := by
              rw [← Int.mul_assoc Da 2 (sa * (st * ct)), Int.mul_comm Da 2, Int.mul_assoc 2 Da (sa * (st * ct))]
        _ = 2 * ((sa * Da) * (st * ct)) := by
              rw [← Int.mul_assoc Da sa (st * ct), Int.mul_comm Da sa]
        _ = (2 * (sa * Da)) * (st * ct) := (Int.mul_assoc 2 (sa * Da) (st * ct)).symm
        _ = 2 * sa * Da * (st * ct) := by rw [← Int.mul_assoc 2 sa Da]
    rw [hpos]
  have hv4y : v4y = -(2 * sa * (Da - ca) * st * (ct * ct)) := by
    change st * v3x + ct * v3y = _
    rw [hv3x, hv3y, Int.mul_neg]
    have p1 : st * (2 * sa * ca * (ct * ct)) = 2 * sa * ca * st * (ct * ct) := by
      calc st * (2 * sa * ca * (ct * ct))
          = (st * (2 * sa * ca)) * (ct * ct) := (Int.mul_assoc st (2 * sa * ca) (ct * ct)).symm
        _ = (2 * sa * ca * st) * (ct * ct) := by rw [Int.mul_comm st (2 * sa * ca)]
    have p2 : ct * (2 * sa * Da * (st * ct)) = 2 * sa * Da * st * (ct * ct) := by
      calc ct * (2 * sa * Da * (st * ct))
          = (2 * sa * Da) * (ct * (st * ct)) := by
              rw [← Int.mul_assoc ct (2 * sa * Da) (st * ct), Int.mul_comm ct (2 * sa * Da),
                  Int.mul_assoc (2 * sa * Da) ct (st * ct)]
        _ = (2 * sa * Da) * (st * (ct * ct)) := by
              rw [← Int.mul_assoc ct st ct, Int.mul_comm ct st, Int.mul_assoc st ct ct]
        _ = 2 * sa * Da * st * (ct * ct) := (Int.mul_assoc (2 * sa * Da) st (ct * ct)).symm
    have p3 : 2 * sa * (Da - ca) * st * (ct * ct) =
        2 * sa * Da * st * (ct * ct) - 2 * sa * ca * st * (ct * ct) := by
      rw [Int.mul_sub (2 * sa) Da ca, Int.sub_mul, Int.sub_mul]
    rw [p1, p2, p3]
    omega
  have hst2 : 0 < st * st := by
    cases Int.lt_or_gt_of_ne hst with
    | inl hlt =>
      have hn : 0 < -st := by omega
      have hs : 0 < (-st) * (-st) := mul_pos_of_pos hn hn
      rw [Int.neg_mul_neg] at hs
      exact hs
    | inr hgt => exact mul_pos_of_pos hgt hgt
  have hct2 : 0 < ct * ct := by
    cases Int.lt_or_gt_of_ne hct with
    | inl hlt =>
      have hn : 0 < -ct := by omega
      have hs : 0 < (-ct) * (-ct) := mul_pos_of_pos hn hn
      rw [Int.neg_mul_neg] at hs
      exact hs
    | inr hgt => exact mul_pos_of_pos hgt hgt
  have hmag_ne : 2 * sa * (Da - ca) * st * (ct * ct) ≠ 0 := by
    have h1 : 0 < 2 * sa * (Da - ca) := mul_pos_of_pos (by omega) (by omega)
    have h2 : 0 < (2 * sa * (Da - ca)) * (ct * ct) := mul_pos_of_pos h1 hct2
    cases Int.lt_or_gt_of_ne hst with
    | inl hlt =>
      have hneg : 0 < -st := by omega
      have hp : 0 < (2 * sa * (Da - ca)) * (-st) := mul_pos_of_pos h1 hneg
      have hp2 : 0 < (2 * sa * (Da - ca)) * (-st) * (ct * ct) := mul_pos_of_pos hp hct2
      rw [Int.mul_neg, Int.neg_mul] at hp2
      omega
    | inr hgt =>
      have hp : 0 < 2 * sa * (Da - ca) * st := mul_pos_of_pos h1 hgt
      have hp2 : 0 < 2 * sa * (Da - ca) * st * (ct * ct) := mul_pos_of_pos hp hct2
      omega
  have hv4_sq_pos : 0 < v4y * v4y := by
    rw [hv4y, Int.neg_mul_neg]
    cases Int.lt_or_gt_of_ne hmag_ne with
    | inl hlt =>
      have hn : 0 < -(2 * sa * (Da - ca) * st * (ct * ct)) := by omega
      have hs : 0 < (-(2 * sa * (Da - ca) * st * (ct * ct))) * (-(2 * sa * (Da - ca) * st * (ct * ct))) :=
        mul_pos_of_pos hn hn
      rw [Int.neg_mul_neg] at hs
      exact hs
    | inr hgt => exact mul_pos_of_pos hgt hgt
  have hcomm_pos : 0 < comm_y * comm_y := by
    have hc_eq : comm_y = st * sa := by change st * sa - 0 = st * sa; omega
    rw [hc_eq]
    have hsa2 : 0 < sa * sa := mul_pos_of_pos hsa hsa
    have hmul : (st * sa) * (st * sa) = (st * st) * (sa * sa) := by
      calc (st * sa) * (st * sa) = st * (sa * (st * sa)) := Int.mul_assoc _ _ _
        _ = st * (st * (sa * sa)) := by rw [← Int.mul_assoc sa st sa, Int.mul_comm sa st, Int.mul_assoc st sa sa]
        _ = (st * st) * (sa * sa) := (Int.mul_assoc st st (sa * sa)).symm
    rw [hmul]
    exact mul_pos_of_pos hst2 hsa2
  exact ⟨hv4y, hv4_sq_pos, hcomm_pos⟩

/-- Theorem 14 (h06 Jamshid al-Kashi): Exact cubic difference factorization for contraction.
For g(x) = (q + x^3) / p, the difference x^3 - y^3 factors identically as
(x - y) * (x^2 + x * y + y^2), yielding exact Lipschitz factor (x^2 + x * y + y^2) / p. -/
theorem kashi_cubic_difference_factorization (x y : Int) :
    x * x * x - y * y * y = (x - y) * (x * x + x * y + y * y) := by
  have h1 : (x - y) * (x * x + x * y + y * y) =
      x * (x * x + x * y + y * y) - y * (x * x + x * y + y * y) :=
    Int.sub_mul x y (x * x + x * y + y * y)
  have h2 : x * (x * x + x * y + y * y) = x * (x * x + x * y) + x * (y * y) :=
    Int.mul_add x (x * x + x * y) (y * y)
  have h3 : x * (x * x + x * y) = x * (x * x) + x * (x * y) :=
    Int.mul_add x (x * x) (x * y)
  have h4 : y * (x * x + x * y + y * y) = y * (x * x + x * y) + y * (y * y) :=
    Int.mul_add y (x * x + x * y) (y * y)
  have h5 : y * (x * x + x * y) = y * (x * x) + y * (x * y) :=
    Int.mul_add y (x * x) (x * y)
  have ha : x * (x * x) = x * x * x := (Int.mul_assoc x x x).symm
  have hb : y * (y * y) = y * y * y := (Int.mul_assoc y y y).symm
  have hc : y * (x * x) = x * (x * y) := by
    calc
      y * (x * x) = x * x * y := Int.mul_comm y (x * x)
      _ = x * (x * y) := Int.mul_assoc x x y
  have hd : y * (x * y) = x * (y * y) := by
    calc
      y * (x * y) = x * y * y := Int.mul_comm y (x * y)
      _ = x * (y * y) := Int.mul_assoc x y y
  omega

/-- Theorem 15 (h07 Kamal al-Din al-Farisi): Stationary-deviation k-reflection rainbow caustic
derivation (dD_k/di = 0 + Snell's law) and Alexander dark-band separation.
For a spherical drop of refractive index n = n_num / n_den > 1 (0 < n_den < n_num):
  (1) tangent stationary deviation 2*di - 2*(k + 1)*dr = 0 (from D_k = 2*i - 2*(k + 1)*r + k*pi)
      combined with differentiated Snell's law (n_den*ci)*di = (n_num*cr)*dr (dr != 0) forces
      (k + 1)*(n_den*ci) = n_num*cr;
  (2) eliminating cr2 between cleared Snell's law n_den^2*(c_den - ci2) = n_num^2*(c_den - cr2)
      and squared stationary condition (k + 1)^2*(n_den^2*ci2) = n_num^2*cr2 proves the universal
      k-reflection caustic law (k*(k + 2))*(n_den^2*ci2) = (n_num^2 - n_den^2)*c_den;
  (3) at primary (k = 1, divisor 1*3 = 3) and secondary (k = 2, divisor 2*4 = 8) caustics over
      common denominator c_den > 0, 0 < ci2_2 < ci2_1 (cos^2(i_2) < cos^2(i_1), i_1 < i_2). -/
theorem farisi_rainbow_caustic_separation (n_num n_den : Int)
    (hd : 0 < n_den) (hgt : n_den < n_num) :
    (∀ k ci cr di dr : Int,
      dr ≠ 0 →
      2 * di - 2 * (k + 1) * dr = 0 →
      (n_den * ci) * di = (n_num * cr) * dr →
      (k + 1) * (n_den * ci) = n_num * cr) ∧
    (∀ k ci2 cr2 c_den : Int,
      (n_den * n_den) * (c_den - ci2) = (n_num * n_num) * (c_den - cr2) →
      ((k + 1) * (k + 1)) * ((n_den * n_den) * ci2) = (n_num * n_num) * cr2 →
      (k * (k + 2)) * ((n_den * n_den) * ci2) = (n_num * n_num - n_den * n_den) * c_den) ∧
    (∀ ci2_1 ci2_2 c_den : Int,
      0 < c_den →
      3 * ((n_den * n_den) * ci2_1) = (n_num * n_num - n_den * n_den) * c_den →
      8 * ((n_den * n_den) * ci2_2) = (n_num * n_num - n_den * n_den) * c_den →
      0 < ci2_2 ∧ ci2_2 < ci2_1) := by
  have hdiff_pos : 0 < n_num - n_den := by omega
  have hsum_pos : 0 < n_num + n_den := by omega
  have hfac : n_num * n_num - n_den * n_den = (n_num - n_den) * (n_num + n_den) := by
    have h1 : (n_num - n_den) * (n_num + n_den) =
        n_num * (n_num + n_den) - n_den * (n_num + n_den) :=
      Int.sub_mul n_num n_den (n_num + n_den)
    have h2 : n_num * (n_num + n_den) = n_num * n_num + n_num * n_den :=
      Int.mul_add n_num n_num n_den
    have h3 : n_den * (n_num + n_den) = n_den * n_num + n_den * n_den :=
      Int.mul_add n_den n_num n_den
    have hcomm : n_den * n_num = n_num * n_den := Int.mul_comm n_den n_num
    omega
  have hpos : 0 < n_num * n_num - n_den * n_den := by
    rw [hfac]
    exact mul_pos_of_pos hdiff_pos hsum_pos
  have hd2_pos : 0 < n_den * n_den := mul_pos_of_pos hd hd
  refine ⟨?_, ?_, ?_⟩
  · intro k ci cr di dr hdr hdD hdSnell
    have hdi : di = (k + 1) * dr := by
      have hm : 2 * ((k + 1) * dr) = 2 * (k + 1) * dr := (Int.mul_assoc 2 (k + 1) dr).symm
      omega
    rw [hdi] at hdSnell
    have hassoc : (n_den * ci) * ((k + 1) * dr) = ((k + 1) * (n_den * ci)) * dr := by
      rw [← Int.mul_assoc (n_den * ci) (k + 1) dr, Int.mul_comm (n_den * ci) (k + 1)]
    rw [hassoc] at hdSnell
    have hzero : ((k + 1) * (n_den * ci) - n_num * cr) * dr = 0 := by
      rw [Int.sub_mul, hdSnell]
      omega
    let diff := (k + 1) * (n_den * ci) - n_num * cr
    have hdiff_zero : diff = 0 := by
      cases Int.lt_trichotomy diff 0 with
      | inl hlt =>
        have hnd : 0 < -diff := by omega
        cases Int.lt_or_gt_of_ne hdr with
        | inl hdr_neg =>
          have hndr : 0 < -dr := by omega
          have hp : 0 < (-diff) * (-dr) := mul_pos_of_pos hnd hndr
          rw [Int.neg_mul_neg] at hp
          change diff * dr = 0 at hzero
          omega
        | inr hdr_pos =>
          have hp : 0 < (-diff) * dr := mul_pos_of_pos hnd hdr_pos
          rw [Int.neg_mul] at hp
          change diff * dr = 0 at hzero
          omega
      | inr hrest =>
        cases hrest with
        | inl heq => exact heq
        | inr hgt_d =>
          cases Int.lt_or_gt_of_ne hdr with
          | inl hdr_neg =>
            have hndr : 0 < -dr := by omega
            have hp : 0 < diff * (-dr) := mul_pos_of_pos hgt_d hndr
            rw [Int.mul_neg] at hp
            change diff * dr = 0 at hzero
            omega
          | inr hdr_pos =>
            have hp : 0 < diff * dr := mul_pos_of_pos hgt_d hdr_pos
            change diff * dr = 0 at hzero
            omega
    change (k + 1) * (n_den * ci) - n_num * cr = 0 at hdiff_zero
    omega
  · intro k ci2 cr2 c_den hsnell hstat
    have hs1 : (n_den * n_den) * (c_den - ci2) =
        (n_den * n_den) * c_den - (n_den * n_den) * ci2 :=
      Int.mul_sub (n_den * n_den) c_den ci2
    have hs2 : (n_num * n_num) * (c_den - cr2) =
        (n_num * n_num) * c_den - (n_num * n_num) * cr2 :=
      Int.mul_sub (n_num * n_num) c_den cr2
    have hk_id : (k + 1) * (k + 1) - 1 = k * (k + 2) := by
      have e1 : (k + 1) * (k + 1) = k * k + 2 * k + 1 := by
        rw [Int.add_mul, Int.mul_add, Int.mul_add]
        omega
      have e2 : k * (k + 2) = k * k + 2 * k := by
        rw [Int.mul_add, Int.mul_comm k 2]
      omega
    have hlhs : (k * (k + 2)) * ((n_den * n_den) * ci2) =
        ((k + 1) * (k + 1)) * ((n_den * n_den) * ci2) - 1 * ((n_den * n_den) * ci2) := by
      rw [← hk_id, Int.sub_mul]
    have hrhs : (n_num * n_num - n_den * n_den) * c_den =
        (n_num * n_num) * c_den - (n_den * n_den) * c_den :=
      Int.sub_mul (n_num * n_num) (n_den * n_den) c_den
    have hone : 1 * ((n_den * n_den) * ci2) = (n_den * n_den) * ci2 :=
      Int.one_mul ((n_den * n_den) * ci2)
    omega
  · intro ci2_1 ci2_2 c_den hc_pos hprim hsec
    have hrhs_pos : 0 < (n_num * n_num - n_den * n_den) * c_den :=
      mul_pos_of_pos hpos hc_pos
    have hd2_ci2_pos : 0 < (n_den * n_den) * ci2_2 := by omega
    have hci2_pos : 0 < ci2_2 := by
      cases Int.le_total ci2_2 0 with
      | inl hle =>
        have hn : 0 ≤ -ci2_2 := by omega
        have hm : 0 ≤ (n_den * n_den) * (-ci2_2) :=
          Int.mul_nonneg (Int.le_of_lt hd2_pos) hn
        rw [Int.mul_neg] at hm
        omega
      | inr hge =>
        cases Int.lt_or_gt_of_ne (by
          intro hz
          rw [hz, Int.mul_zero] at hd2_ci2_pos
          omega : ci2_2 ≠ 0) with
        | inl hlt => omega
        | inr hgt_c => exact hgt_c
    have hgap_scaled : 0 < (n_den * n_den) * (ci2_1 - ci2_2) := by
      rw [Int.mul_sub]
      omega
    have hlt_12 : ci2_2 < ci2_1 := by
      cases Int.le_total (ci2_1 - ci2_2) 0 with
      | inl hle =>
        have hn : 0 ≤ -(ci2_1 - ci2_2) := by omega
        have hm : 0 ≤ (n_den * n_den) * (-(ci2_1 - ci2_2)) :=
          Int.mul_nonneg (Int.le_of_lt hd2_pos) hn
        rw [Int.mul_neg] at hm
        omega
      | inr hge =>
        cases Int.lt_or_gt_of_ne (by
          intro hz
          rw [hz, Int.mul_zero] at hgap_scaled
          omega : ci2_1 - ci2_2 ≠ 0) with
        | inl hlt => omega
        | inr hgt_d => omega
    exact ⟨hci2_pos, hlt_12⟩

/-- Theorem 16 (h08 Al-Khazini): Exact 2-metal hydrostatic alloy inverse identity.
Given component masses m1, m2 and specific gravities r1, r2, eliminating m2 yields
(m1 + m2) * r2 - (m1 * r1 + m2 * r2) = m1 * (r2 - r1), invertible iff r1 != r2. -/
theorem khazini_hydrostatic_alloy_inverse (m1 m2 r1 r2 : Int) :
    (m1 + m2) * r2 - (m1 * r1 + m2 * r2) = m1 * (r2 - r1) := by
  have h1 : (m1 + m2) * r2 = m1 * r2 + m2 * r2 := Int.add_mul m1 m2 r2
  have h2 : m1 * (r2 - r1) = m1 * r2 - m1 * r1 := Int.mul_sub m1 r2 r1
  omega

/-- Theorem 17 (h09 Ibn al-Nafis): Exact 2x2 grounded-Laplacian Kirchhoff Schur-complement
elimination and septal-wall pulmonary rerouting identity.
For the 3-node cardiopulmonary conductance network (RV, Lungs, LV) grounded at LV (v_LV = 0)
with pulmonary conductances w1, w2 > 0 and septal conductance ws > 0 (vs imperforate ws = 0),
the grounded 2x2 Laplacian minor L_red = [[w1 + ws, -w1], [-w1, w1 + w2]] satisfies:
  (1) exact Schur determinant det(L_red) = (w1 + ws)*(w1 + w2) - w1^2 = ws*(w1 + w2) + w1*w2;
  (2) under Kirchhoff lung balance (w1 + w2)*vL = w1*vR, eliminating vL gives the exact
      cleared total outflow (w1 + w2)*(w1*(vR - vL) + ws*vR) = det(L_red)*vR;
  (3) at zero septal permeability ws = 0 (imperforate septum), det(L_red) = w1*w2 and
      cleared pulmonary flow (w1 + w2)*(w1*(vR - vL)) equals total outflow (w1*w2)*vR;
  (4) any positive septal leak ws > 0 strictly raises effective conductance above the
      imperforate pulmonary value: w1*w2 < det(L_red). -/
theorem nafis_septal_wall_rerouting_exact (w1 w2 ws vR vL : Int)
    (hw1 : 0 < w1) (hw2 : 0 < w2) (hws : 0 < ws)
    (hkirch : (w1 + w2) * vL = w1 * vR) :
    let det_s := (w1 + ws) * (w1 + w2) - w1 * w1
    let det_0 := (w1 + 0) * (w1 + w2) - w1 * w1
    let i_pulm := w1 * (vR - vL)
    let i_tot := i_pulm + ws * vR
    (det_s = ws * (w1 + w2) + w1 * w2) ∧
    ((w1 + w2) * i_tot = det_s * vR) ∧
    (det_0 = w1 * w2 ∧ (w1 + w2) * i_pulm = det_0 * vR) ∧
    (det_0 < det_s) := by
  intro det_s det_0 i_pulm i_tot
  have hdet_s : det_s = ws * (w1 + w2) + w1 * w2 := by
    change (w1 + ws) * (w1 + w2) - w1 * w1 = _
    rw [Int.add_mul, Int.mul_add]
    omega
  have hdet_0 : det_0 = w1 * w2 := by
    change (w1 + 0) * (w1 + w2) - w1 * w1 = _
    rw [Int.add_zero, Int.mul_add]
    omega
  have hpulm : (w1 + w2) * i_pulm = (w1 * w2) * vR := by
    change (w1 + w2) * (w1 * (vR - vL)) = (w1 * w2) * vR
    rw [Int.mul_sub, Int.mul_sub]
    have t1 : (w1 + w2) * (w1 * vR) = (w1 * w1) * vR + (w1 * w2) * vR := by
      rw [← Int.mul_assoc (w1 + w2) w1 vR, Int.add_mul, Int.add_mul, Int.mul_comm w2 w1]
    have t2 : (w1 + w2) * (w1 * vL) = (w1 * w1) * vR := by
      calc (w1 + w2) * (w1 * vL)
          = w1 * ((w1 + w2) * vL) := by
              rw [← Int.mul_assoc (w1 + w2) w1 vL, Int.mul_comm (w1 + w2) w1, Int.mul_assoc w1 (w1 + w2) vL]
        _ = w1 * (w1 * vR) := by rw [hkirch]
        _ = (w1 * w1) * vR := (Int.mul_assoc w1 w1 vR).symm
    omega
  have htot : (w1 + w2) * i_tot = det_s * vR := by
    change (w1 + w2) * (i_pulm + ws * vR) = det_s * vR
    rw [Int.mul_add, hpulm, hdet_s, Int.add_mul (ws * (w1 + w2)) (w1 * w2) vR]
    have t3 : (w1 + w2) * (ws * vR) = ws * (w1 + w2) * vR := by
      calc (w1 + w2) * (ws * vR)
          = ((w1 + w2) * ws) * vR := (Int.mul_assoc (w1 + w2) ws vR).symm
        _ = (ws * (w1 + w2)) * vR := by rw [Int.mul_comm (w1 + w2) ws]
    omega
  have hlt : det_0 < det_s := by
    have hsum : 0 < w1 + w2 := by omega
    have hjump : 0 < ws * (w1 + w2) := mul_pos_of_pos hws hsum
    omega
  exact ⟨hdet_s, htot, ⟨hdet_0, by rw [hdet_0]; exact hpulm⟩, hlt⟩

#print axioms kn_silo_cut_edges_exact
#print axioms k10_silo_cut_five_five_ladder
#print axioms tetrahedral_z2_bianchi_universal
#print axioms schur_3node_compounding_strict
#print axioms foster_uniform_kn_cleared
#print axioms khwarizmi_completing_square_exact
#print axioms thabit_amicable_product_identity
#print axioms thabit_n3_composite_obstruction
#print axioms biruni_dip_radius_cleared_identity
#print axioms haytham_reflection_norm_invariance
#print axioms khayyam_cubic_positive_neg_discriminant
#print axioms tusi_planar_curl_annihilation
#print axioms tusi_spherical_obstruction_pos
#print axioms kashi_cubic_difference_factorization
#print axioms farisi_rainbow_caustic_separation
#print axioms khazini_hydrostatic_alloy_inverse
#print axioms nafis_septal_wall_rerouting_exact

end ClassicalHeritageAtlas
