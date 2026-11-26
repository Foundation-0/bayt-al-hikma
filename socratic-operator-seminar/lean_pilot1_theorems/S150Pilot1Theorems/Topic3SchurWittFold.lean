/-
  S150Pilot1Theorems/Topic3SchurWittFold.lean

  Topic 3 (`cave-expedition`) — Unified Schur–Witt–Fold Criterion:
    1. Exact fraction-free Z-lift & determinant factorization of 2x2 and 3x3 block Schur complements,
    2. Canonical shear in GL(Z) iff A^{-1}B is integral (+ explicit converse refutation at A=[[4]], B=[[2]], D=[[1]]),
    3. 1x1 block-drop M ~_Q A (+) D iff s * D is a rational square (refuting unconditional drop at [[3,3],[3,4]]
       and proving irrational-sqrt(2) obstruction on [[2,1],[1,1]] over all GL_2(Q)),
    4. GF(2) parity fold defined iff det A ≡ 1 (mod 2) with universal even-diagonal preservation,
    5. Doubled-coordinate mirror billiard on (2, 3) refuting naive single-shear divisibility.
-/

import S150Pilot1Theorems.Topic1FrickeCayley

namespace S150Pilot1Theorems

/-! ### Part 3A: Fraction-Free Schur Congruence & `GL(Z)` Canonical Shear -/

private def schur2x2Pairs : (PExpr × PExpr) × (PExpr × PExpr) × (PExpr × PExpr) × (PExpr × PExpr) :=
  let va := PExpr.var 0; let vb := PExpr.var 1; let vd := PExpr.var 2
  ((va * (va * va + vb * 0) + 0 * (vb * va + vd * 0), va * va * va),
   (va * (va * (-vb) + vb * va) + 0 * (vb * (-vb) + vd * va), 0),
   ((-vb) * (va * va + vb * 0) + va * (vb * va + vd * 0), 0),
   ((-vb) * (va * (-vb) + vb * va) + va * (vb * (-vb) + vd * va), va * (va * vd - vb * vb)))

/-- **2x2 Fraction-Free Schur Congruence**:
    For `M = [[a, b], [b, d]]`, `P_Z = [[a, -b], [0, a]]` satisfies
    `P_Z^T M P_Z = [[a^3, 0], [0, a*(a*d - b^2)]]` and `det M = a*d - b^2`. -/
theorem t3_schur_fraction_free_congruence_2x2 (a b d : Int) :
    let M : Mat2Z := ⟨a, b, b, d⟩
    let PZ : Mat2Z := ⟨a, -b, 0, a⟩
    mat2Mul (mat2Transpose PZ) (mat2Mul M PZ) = ⟨a * a * a, 0, 0, a * (a * d - b * b)⟩ ∧
    mat2Det M = a * d - b * b := by
  dsimp only
  let env := [a, b, d]
  have h00 : a * (a * a + b * 0) + 0 * (b * a + d * 0) = a * a * a :=
    poly_eq_of_norm_eq env schur2x2Pairs.1.1 schur2x2Pairs.1.2 rfl
  have h01 : a * (a * (-b) + b * a) + 0 * (b * (-b) + d * a) = 0 :=
    poly_eq_of_norm_eq env schur2x2Pairs.2.1.1 schur2x2Pairs.2.1.2 rfl
  have h10 : (-b) * (a * a + b * 0) + a * (b * a + d * 0) = 0 :=
    poly_eq_of_norm_eq env schur2x2Pairs.2.2.1.1 schur2x2Pairs.2.2.1.2 rfl
  have h11 : (-b) * (a * (-b) + b * a) + a * (b * (-b) + d * a) = a * (a * d - b * b) :=
    poly_eq_of_norm_eq env schur2x2Pairs.2.2.2.1 schur2x2Pairs.2.2.2.2 rfl
  refine ⟨?_, rfl⟩
  unfold mat2Mul mat2Transpose; dsimp only
  rw [h00, h01, h10, h11]

private abbrev Mat3EP :=
  (PExpr × PExpr × PExpr) × (PExpr × PExpr × PExpr) × (PExpr × PExpr × PExpr)

private def mmul3EP (A B : Mat3EP) : Mat3EP :=
  let ((a00, a01, a02), (a10, a11, a12), (a20, a21, a22)) := A
  let ((b00, b01, b02), (b10, b11, b12), (b20, b21, b22)) := B
  ((a00*b00 + a01*b10 + a02*b20, a00*b01 + a01*b11 + a02*b21, a00*b02 + a01*b12 + a02*b22),
   (a10*b00 + a11*b10 + a12*b20, a10*b01 + a11*b11 + a12*b21, a10*b02 + a11*b12 + a12*b22),
   (a20*b00 + a21*b10 + a22*b20, a20*b01 + a21*b11 + a22*b21, a20*b02 + a21*b12 + a22*b22))

-- Use `[a11, a12, a22, b1, b2, d, detA, u1, u2]` so every entry is degree ≤ 3!
private def schur3x3LinearPair : Mat3EP × Mat3EP :=
  let va11 := PExpr.var 0; let va12 := PExpr.var 1; let va22 := PExpr.var 2
  let vb1  := PExpr.var 3; let vb2  := PExpr.var 4; let vd   := PExpr.var 5
  let pdet := va11 * va22 - va12 * va12
  let pu1  := va22 * vb1 - va12 * vb2
  let pu2  := -va12 * vb1 + va11 * vb2
  let pdm  := pdet * vd - (vb1 * pu1 + vb2 * pu2)
  let M  : Mat3EP := ((va11, va12, vb1), (va12, va22, vb2), (vb1, vb2, vd))
  let PZ : Mat3EP := ((pdet, 0, -pu1), (0, pdet, -pu2), (0, 0, pdet))
  let PT : Mat3EP := ((pdet, 0, 0), (0, pdet, 0), (-pu1, -pu2, pdet))
  (mmul3EP PT (mmul3EP M PZ),
   ((pdet * pdet * va11, pdet * pdet * va12, 0),
    (pdet * pdet * va12, pdet * pdet * va22, 0),
    (0, 0, pdet * pdm)))

private def schur3x3CornerStep1 : PExpr × PExpr :=
  -- In `[a11, a12, a22, b1, b2, d, detA, u1, u2]`:
  -- MP col 2 = `(a11*(-u1)+a12*(-u2)+b1*detA, a12*(-u1)+a22*(-u2)+b2*detA, b1*(-u1)+b2*(-u2)+d*detA)`
  let va11 := PExpr.var 0; let va12 := PExpr.var 1; let va22 := PExpr.var 2
  let vb1  := PExpr.var 3; let vb2  := PExpr.var 4
  let pdet := va11 * va22 - va12 * va12
  let pu1  := va22 * vb1 - va12 * vb2
  let pu2  := -va12 * vb1 + va11 * vb2
  (va11 * (-pu1) + va12 * (-pu2) + vb1 * pdet, 0)

private def schur3x3CornerStep2 : PExpr × PExpr :=
  let va11 := PExpr.var 0; let va12 := PExpr.var 1; let va22 := PExpr.var 2
  let vb1  := PExpr.var 3; let vb2  := PExpr.var 4
  let pdet := va11 * va22 - va12 * va12
  let pu1  := va22 * vb1 - va12 * vb2
  let pu2  := -va12 * vb1 + va11 * vb2
  (va12 * (-pu1) + va22 * (-pu2) + vb2 * pdet, 0)

/-- **3x3 Block Fraction-Free Schur Congruence (`2x2` Pivot `A` + `1x1` Corner `d`)**:
    With `Δ = a11*a22 - a12^2`, adjugate column `adjB = (a22*b1 - a12*b2, -a12*b1 + a11*b2)`,
    and `P_Z = [[Δ, 0, -adjB_1], [0, Δ, -adjB_2], [0, 0, Δ]]`, `P_Z^T M P_Z = Δ^2 * A ⊕ diag(Δ * det M)`. -/
theorem t3_schur_fraction_free_congruence_3x3 (a11 a12 a22 b1 b2 d : Int) :
    let detA := a11 * a22 - a12 * a12
    let u1 := a22 * b1 - a12 * b2
    let u2 := -a12 * b1 + a11 * b2
    let detM := detA * d - (b1 * u1 + b2 * u2)
    let M : Mat3Z :=
      { m00 := a11, m01 := a12, m02 := b1
      , m10 := a12, m11 := a22, m12 := b2
      , m20 := b1,  m21 := b2,  m22 := d }
    let PZ : Mat3Z :=
      { m00 := detA, m01 := 0,    m02 := -u1
      , m10 := 0,    m11 := detA, m12 := -u2
      , m20 := 0,    m21 := 0,    m22 := detA }
    let PT : Mat3Z :=
      { m00 := detA, m01 := 0,    m02 := 0
      , m10 := 0,    m11 := detA, m12 := 0
      , m20 := -u1,  m21 := -u2,  m22 := detA }
    matMul3 PT (matMul3 M PZ) =
      { m00 := detA * detA * a11, m01 := detA * detA * a12, m02 := 0
      , m10 := detA * detA * a12, m11 := detA * detA * a22, m12 := 0
      , m20 := 0,                 m21 := 0,                 m22 := detA * detM } := by
  dsimp only
  let detA := a11 * a22 - a12 * a12
  let u1 := a22 * b1 - a12 * b2
  let u2 := -a12 * b1 + a11 * b2
  let detM := detA * d - (b1 * u1 + b2 * u2)
  -- First compute `M * PZ` explicitly! Its last column top two entries vanish by adjugate law `A * (-adjA B) + detA * B = 0`!
  have hcol0 : a11 * (-u1) + a12 * (-u2) + b1 * detA = 0 :=
    poly_eq_of_norm_eq [a11, a12, a22, b1, b2] schur3x3CornerStep1.1 schur3x3CornerStep1.2 rfl
  have hcol1 : a12 * (-u1) + a22 * (-u2) + b2 * detA = 0 :=
    poly_eq_of_norm_eq [a11, a12, a22, b1, b2] schur3x3CornerStep2.1 schur3x3CornerStep2.2 rfl
  let M : Mat3Z := { m00 := a11, m01 := a12, m02 := b1, m10 := a12, m11 := a22, m12 := b2, m20 := b1, m21 := b2, m22 := d }
  let PZ : Mat3Z := { m00 := detA, m01 := 0, m02 := -u1, m10 := 0, m11 := detA, m12 := -u2, m20 := 0, m21 := 0, m22 := detA }
  let PT : Mat3Z := { m00 := detA, m01 := 0, m02 := 0, m10 := 0, m11 := detA, m12 := 0, m20 := -u1, m21 := -u2, m22 := detA }
  have hMP : matMul3 M PZ =
      { m00 := a11 * detA, m01 := a12 * detA, m02 := 0
      , m10 := a12 * detA, m11 := a22 * detA, m12 := 0
      , m20 := b1 * detA,  m21 := b2 * detA,  m22 := detM } := by
    unfold M PZ matMul3; dsimp only
    rw [hcol0, hcol1]
    have h00 : a11 * detA + a12 * 0 + b1 * 0 = a11 * detA := by omega
    have h01 : a11 * 0 + a12 * detA + b1 * 0 = a12 * detA := by omega
    have h10 : a12 * detA + a22 * 0 + b2 * 0 = a12 * detA := by omega
    have h11 : a12 * 0 + a22 * detA + b2 * 0 = a22 * detA := by omega
    have h20 : b1 * detA + b2 * 0 + d * 0 = b1 * detA := by omega
    have h21 : b1 * 0 + b2 * detA + d * 0 = b2 * detA := by omega
    have h22 : b1 * (-u1) + b2 * (-u2) + d * detA = detM :=
      poly_eq_of_norm_eq [b1, b2, u1, u2, d, detA]
        (PExpr.var 0 * (-PExpr.var 2) + PExpr.var 1 * (-PExpr.var 3) + PExpr.var 4 * PExpr.var 5)
        (PExpr.var 5 * PExpr.var 4 - (PExpr.var 0 * PExpr.var 2 + PExpr.var 1 * PExpr.var 3)) rfl
    rw [h00, h01, h10, h11, h20, h21, h22]
  change matMul3 PT (matMul3 M PZ) = _
  rw [hMP]
  unfold PT matMul3; dsimp only
  have r00 : detA * (a11 * detA) + 0 * (a12 * detA) + 0 * (b1 * detA) = detA * detA * a11 :=
    poly_eq_of_norm_eq [detA, a11, a12, b1]
      (PExpr.var 0 * (PExpr.var 1 * PExpr.var 0) + 0 * (PExpr.var 2 * PExpr.var 0) + 0 * (PExpr.var 3 * PExpr.var 0))
      (PExpr.var 0 * PExpr.var 0 * PExpr.var 1) rfl
  have r01 : detA * (a12 * detA) + 0 * (a22 * detA) + 0 * (b2 * detA) = detA * detA * a12 :=
    poly_eq_of_norm_eq [detA, a12, a22, b2]
      (PExpr.var 0 * (PExpr.var 1 * PExpr.var 0) + 0 * (PExpr.var 2 * PExpr.var 0) + 0 * (PExpr.var 3 * PExpr.var 0))
      (PExpr.var 0 * PExpr.var 0 * PExpr.var 1) rfl
  have r02 : detA * 0 + 0 * 0 + 0 * detM = 0 := by omega
  have r10 : 0 * (a11 * detA) + detA * (a12 * detA) + 0 * (b1 * detA) = detA * detA * a12 :=
    poly_eq_of_norm_eq [detA, a11, a12, b1]
      (0 * (PExpr.var 1 * PExpr.var 0) + PExpr.var 0 * (PExpr.var 2 * PExpr.var 0) + 0 * (PExpr.var 3 * PExpr.var 0))
      (PExpr.var 0 * PExpr.var 0 * PExpr.var 2) rfl
  have r11 : 0 * (a12 * detA) + detA * (a22 * detA) + 0 * (b2 * detA) = detA * detA * a22 :=
    poly_eq_of_norm_eq [detA, a12, a22, b2]
      (0 * (PExpr.var 1 * PExpr.var 0) + PExpr.var 0 * (PExpr.var 2 * PExpr.var 0) + 0 * (PExpr.var 3 * PExpr.var 0))
      (PExpr.var 0 * PExpr.var 0 * PExpr.var 2) rfl
  have r12 : 0 * 0 + detA * 0 + 0 * detM = 0 := by omega
  have r20 : (-u1) * (a11 * detA) + (-u2) * (a12 * detA) + detA * (b1 * detA) = 0 := by
    have h : (a11 * (-u1) + a12 * (-u2) + b1 * detA) * detA = 0 * detA := congrArg (fun z => z * detA) hcol0
    have hl : ((-u1) * (a11 * detA) + (-u2) * (a12 * detA) + detA * (b1 * detA)) =
        (a11 * (-u1) + a12 * (-u2) + b1 * detA) * detA :=
      poly_eq_of_norm_eq [a11, a12, b1, u1, u2, detA]
        ((-PExpr.var 3) * (PExpr.var 0 * PExpr.var 5) + (-PExpr.var 4) * (PExpr.var 1 * PExpr.var 5) + PExpr.var 5 * (PExpr.var 2 * PExpr.var 5))
        ((PExpr.var 0 * (-PExpr.var 3) + PExpr.var 1 * (-PExpr.var 4) + PExpr.var 2 * PExpr.var 5) * PExpr.var 5) rfl
    rw [hl, h, Int.zero_mul]
  have r21 : (-u1) * (a12 * detA) + (-u2) * (a22 * detA) + detA * (b2 * detA) = 0 := by
    have h : (a12 * (-u1) + a22 * (-u2) + b2 * detA) * detA = 0 * detA := congrArg (fun z => z * detA) hcol1
    have hl : ((-u1) * (a12 * detA) + (-u2) * (a22 * detA) + detA * (b2 * detA)) =
        (a12 * (-u1) + a22 * (-u2) + b2 * detA) * detA :=
      poly_eq_of_norm_eq [a12, a22, b2, u1, u2, detA]
        ((-PExpr.var 3) * (PExpr.var 0 * PExpr.var 5) + (-PExpr.var 4) * (PExpr.var 1 * PExpr.var 5) + PExpr.var 5 * (PExpr.var 2 * PExpr.var 5))
        ((PExpr.var 0 * (-PExpr.var 3) + PExpr.var 1 * (-PExpr.var 4) + PExpr.var 2 * PExpr.var 5) * PExpr.var 5) rfl
    rw [hl, h, Int.zero_mul]
  have r22 : (-u1) * 0 + (-u2) * 0 + detA * detM = detA * detM := by omega
  rw [r00, r01, r02, r10, r11, r12, r20, r21, r22]

/-- **`GL(Z)` Canonical Shear Criterion**:
    An integer upper-unitriangular shear `P = [[1, -x], [0, 1]]` (`det P = 1`)
    eliminates the off-diagonal block (`P^T [[a, b], [b, d]] P` diagonal) iff `b = a * x` (`a ∣ b`). -/
theorem t3_glz_canonical_shear_iff_divides (a b d : Int) :
    (∃ x : Int, (mat2Mul (mat2Transpose ⟨1, -x, 0, 1⟩) (mat2Mul ⟨a, b, b, d⟩ ⟨1, -x, 0, 1⟩)).q = 0) ↔
      a ∣ b := by
  constructor
  · rintro ⟨x, hq⟩
    have hoff : (mat2Mul (mat2Transpose ⟨1, -x, 0, 1⟩) (mat2Mul ⟨a, b, b, d⟩ ⟨1, -x, 0, 1⟩)).q = b - a * x := by
      unfold mat2Mul mat2Transpose; dsimp only
      exact poly_eq_of_norm_eq [a, b, d, x]
        (1 * (PExpr.var 0 * (-PExpr.var 3) + PExpr.var 1 * 1) + 0 * (PExpr.var 1 * (-PExpr.var 3) + PExpr.var 2 * 1))
        (PExpr.var 1 - PExpr.var 0 * PExpr.var 3) rfl
    rw [hoff] at hq
    exact ⟨x, by omega⟩
  · rintro ⟨x, rfl⟩
    refine ⟨x, ?_⟩
    unfold mat2Mul mat2Transpose; dsimp only
    exact poly_eq_of_norm_eq [a, x, d]
      (1 * (PExpr.var 0 * (-PExpr.var 1) + (PExpr.var 0 * PExpr.var 1) * 1) +
       0 * ((PExpr.var 0 * PExpr.var 1) * (-PExpr.var 1) + PExpr.var 2 * 1))
      0 rfl

/-- **Refutation of Integral-Schur Converse (`A = [[4]], B = [[2]], D = [[1]]`, `[]` zero axioms)**:
    Here `S = d - b^2/a = 1 - 4/4 = 0 ∈ Z` is integral (`4 ∣ (4*1 - 2^2)`), yet `a ∤ b` (`2 % 4 ≠ 0`),
    so no integer canonical shear exists despite `S ∈ Z`. -/
theorem t3_glz_schur_integral_converse_counterexample :
    let a : Int := 4; let b : Int := 2; let d : Int := 1
    (a * d - b * b = 0) ∧ (b % a ≠ 0) := by
  decide

/-! ### Part 3B: `1x1` Diagonal Block-Drop Square-Class Criterion & `sqrt(2)` Obstruction -/

private def evenSqPair3 : PExpr × PExpr := ((2 * PExpr.var 0) * (2 * PExpr.var 0), 4 * (PExpr.var 0 * PExpr.var 0))
private def oddSqPair3  : PExpr × PExpr :=
  ((2 * PExpr.var 0 + 1) * (2 * PExpr.var 0 + 1), 4 * (PExpr.var 0 * PExpr.var 0 + PExpr.var 0) + 1)

private theorem nat_sq_ne_two_sq_fuel :
    ∀ (fuel d : Nat), d ≤ fuel → 0 < d → ∀ n : Nat, n * n ≠ 2 * (d * d)
  | 0, d, hle, hd, _, _ => by omega
  | fuel + 1, d, hle, hd, n, h => by
    let q := n / 2
    have hmod : n % 2 = 0 ∨ n % 2 = 1 := by omega
    rcases hmod with h0 | h1
    · have hn : n = 2 * q := by omega
      have h4 : (2 * q) * (2 * q) = 4 * (q * q) := by
        have hp : Int.ofNat ((2 * q) * (2 * q)) = Int.ofNat (4 * (q * q)) :=
          poly_eq_of_norm_eq [Int.ofNat q] evenSqPair3.1 evenSqPair3.2 rfl
        exact Int.ofNat.inj hp
      rw [hn, h4] at h
      have hd2 : d * d = 2 * (q * q) := by omega
      have hq_pos : 0 < q := by
        cases Nat.eq_zero_or_pos q with
        | inl hq0 =>
          rw [hq0] at hd2
          have hd_ge1 : 1 ≤ d * d := Nat.mul_le_mul hd hd
          omega
        | inr hp => exact hp
      have hq_lt_d : q < d := by
        rcases Decidable.em (q < d) with hlt | hlt
        · exact hlt
        · have hge : d ≤ q := by omega
          have hsq_ge : d * d ≤ q * q := Nat.mul_le_mul hge hge
          have hd_ge1 : 1 ≤ d * d := Nat.mul_le_mul hd hd
          omega
      exact nat_sq_ne_two_sq_fuel fuel q (by omega) hq_pos d hd2
    · have hn : n = 2 * q + 1 := by omega
      have hodd : (2 * q + 1) * (2 * q + 1) = 4 * (q * q + q) + 1 := by
        have hp : Int.ofNat ((2 * q + 1) * (2 * q + 1)) = Int.ofNat (4 * (q * q + q) + 1) :=
          poly_eq_of_norm_eq [Int.ofNat q] oddSqPair3.1 oddSqPair3.2 rfl
        exact Int.ofNat.inj hp
      rw [hn, hodd] at h
      omega

private theorem int_sq_eq_natAbs_sq (x : Int) : x * x = Int.ofNat (x.natAbs * x.natAbs) := by
  cases x with
  | ofNat _ => rfl
  | negSucc _ => rfl

/-- **Constructive Irrationality of `sqrt(2)` over `Int`**:
    For all `m, k ∈ Z` with `k ≠ 0`, `m * m ≠ 2 * (k * k)`. -/
theorem t3_two_mul_sq_ne_sq (m k : Int) (hk : k ≠ 0) : m * m ≠ 2 * (k * k) := by
  intro heq
  rw [int_sq_eq_natAbs_sq m, int_sq_eq_natAbs_sq k] at heq
  have hk_pos : 0 < k.natAbs := Int.natAbs_pos.mpr hk
  have h2 : (2 : Int) * Int.ofNat (k.natAbs * k.natAbs) = Int.ofNat (2 * (k.natAbs * k.natAbs)) := rfl
  rw [h2] at heq
  exact nat_sq_ne_two_sq_fuel k.natAbs k.natAbs (Nat.le_refl _) hk_pos m.natAbs (Int.ofNat.inj heq)

private def mat2DetMulPair : PExpr × PExpr :=
  ((PExpr.var 0 * PExpr.var 4 + PExpr.var 1 * PExpr.var 6) * (PExpr.var 2 * PExpr.var 5 + PExpr.var 3 * PExpr.var 7) -
   (PExpr.var 0 * PExpr.var 5 + PExpr.var 1 * PExpr.var 7) * (PExpr.var 2 * PExpr.var 4 + PExpr.var 3 * PExpr.var 6),
   (PExpr.var 0 * PExpr.var 3 - PExpr.var 1 * PExpr.var 2) * (PExpr.var 4 * PExpr.var 7 - PExpr.var 5 * PExpr.var 6))

/-- **Bidirectional `1x1` Block-Drop Square-Class Theorem (`M ~_Q diag(a, d)`)**:
    For nonsingular `a ≠ 0` and `d ≠ 0` with `a*d - b^2 ≠ 0`:
    `M = [[a, b], [b, d]]` is rationally congruent to `diag(a, d)`
    (`∃ Q : Mat2Z, ∃ k : Int, k ≠ 0 ∧ mat2Det Q ≠ 0 ∧ Q^T M Q = k^2 * diag(a, d)`)
    **if and only if** `a * (a * d - b^2) * d` is a nonzero rational square (`∃ u v : Int, v ≠ 0 ∧ u ≠ 0 ∧ v^2 * a * (a*d - b^2) * d = u^2`). -/
theorem t3_block_drop_1x1_iff_square_class (a b d : Int)
    (ha : a ≠ 0) (hd : d ≠ 0) (_hs : a * d - b * b ≠ 0) :
    (∃ (Q : Mat2Z) (k : Int), k ≠ 0 ∧ mat2Det Q ≠ 0 ∧
      mat2Mul (mat2Transpose Q) (mat2Mul ⟨a, b, b, d⟩ Q) = ⟨k * k * a, 0, 0, k * k * d⟩) ↔
    (∃ u v : Int, v ≠ 0 ∧ u ≠ 0 ∧ v * v * a * (a * d - b * b) * d = u * u) := by
  have det_mul : ∀ A B : Mat2Z, mat2Det (mat2Mul A B) = mat2Det A * mat2Det B :=
    fun A B => poly_eq_of_norm_eq [A.p, A.q, A.r, A.s, B.p, B.q, B.r, B.s] mat2DetMulPair.1 mat2DetMulPair.2 rfl
  constructor
  · rintro ⟨Q, k, hk, hdetQ, hcong⟩
    have hdet_lhs : mat2Det (mat2Mul (mat2Transpose Q) (mat2Mul ⟨a, b, b, d⟩ Q)) =
        mat2Det Q * mat2Det Q * (a * d - b * b) := by
      rw [det_mul, det_mul]
      have htr : mat2Det (mat2Transpose Q) = mat2Det Q :=
        poly_eq_of_norm_eq [Q.p, Q.q, Q.r, Q.s]
          (PExpr.var 0 * PExpr.var 3 - PExpr.var 2 * PExpr.var 1)
          (PExpr.var 0 * PExpr.var 3 - PExpr.var 1 * PExpr.var 2) rfl
      rw [htr]
      unfold mat2Det; dsimp only
      exact poly_eq_of_norm_eq [mat2Det Q, a, b, d]
        (PExpr.var 0 * ((PExpr.var 1 * PExpr.var 3 - PExpr.var 2 * PExpr.var 2) * PExpr.var 0))
        (PExpr.var 0 * PExpr.var 0 * (PExpr.var 1 * PExpr.var 3 - PExpr.var 2 * PExpr.var 2)) rfl
    have hdet_rhs : mat2Det ⟨k * k * a, 0, 0, k * k * d⟩ = (k * k) * (k * k) * (a * d) := by
      unfold mat2Det; dsimp only
      exact poly_eq_of_norm_eq [k, a, d]
        ((PExpr.var 0 * PExpr.var 0 * PExpr.var 1) * (PExpr.var 0 * PExpr.var 0 * PExpr.var 2) - 0 * 0)
        ((PExpr.var 0 * PExpr.var 0) * (PExpr.var 0 * PExpr.var 0) * (PExpr.var 1 * PExpr.var 2)) rfl
    rw [hcong, hdet_rhs] at hdet_lhs
    refine ⟨k * k * a * d, mat2Det Q, hdetQ, ?_, ?_⟩
    · intro hu0
      rcases Int.mul_eq_zero.mp hu0 with h1 | hd0
      · rcases Int.mul_eq_zero.mp h1 with h2 | ha0
        · rcases Int.mul_eq_zero.mp h2 with hk0 | hk0 <;> exact hk hk0
        · exact ha ha0
      · exact hd hd0
    · have hmul_ad : (mat2Det Q * mat2Det Q * (a * d - b * b)) * (a * d) =
          ((k * k) * (k * k) * (a * d)) * (a * d) := congrArg (fun z => z * (a * d)) hdet_lhs.symm
      have hl_simp : (mat2Det Q * mat2Det Q * (a * d - b * b)) * (a * d) =
          mat2Det Q * mat2Det Q * a * (a * d - b * b) * d :=
        poly_eq_of_norm_eq [mat2Det Q, a, b, d]
          ((PExpr.var 0 * PExpr.var 0 * (PExpr.var 1 * PExpr.var 3 - PExpr.var 2 * PExpr.var 2)) * (PExpr.var 1 * PExpr.var 3))
          (PExpr.var 0 * PExpr.var 0 * PExpr.var 1 * (PExpr.var 1 * PExpr.var 3 - PExpr.var 2 * PExpr.var 2) * PExpr.var 3) rfl
      have hr_simp : ((k * k) * (k * k) * (a * d)) * (a * d) = (k * k * a * d) * (k * k * a * d) :=
        poly_eq_of_norm_eq [k, a, d]
          (((PExpr.var 0 * PExpr.var 0) * (PExpr.var 0 * PExpr.var 0) * (PExpr.var 1 * PExpr.var 2)) * (PExpr.var 1 * PExpr.var 2))
          ((PExpr.var 0 * PExpr.var 0 * PExpr.var 1 * PExpr.var 2) * (PExpr.var 0 * PExpr.var 0 * PExpr.var 1 * PExpr.var 2)) rfl
      rw [hl_simp, hr_simp] at hmul_ad
      exact hmul_ad
  · rintro ⟨u, v, hv, hu, hsq⟩
    let Q : Mat2Z := ⟨u, -v * b * d, 0, v * a * d⟩
    refine ⟨Q, u, hu, ?_, ?_⟩
    · show u * (v * a * d) - (-v * b * d) * 0 ≠ 0
      rw [Int.mul_zero, Int.sub_zero]
      intro h0
      rcases Int.mul_eq_zero.mp h0 with hu0 | hvad
      · exact hu hu0
      · rcases Int.mul_eq_zero.mp hvad with hva | hd0
        · rcases Int.mul_eq_zero.mp hva with hv0 | ha0
          · exact hv hv0
          · exact ha ha0
        · exact hd hd0
    · unfold mat2Mul mat2Transpose; dsimp only
      have e00 : u * (a * u + b * 0) + 0 * (b * u + d * 0) = u * u * a :=
        poly_eq_of_norm_eq [u, a, b, d]
          (PExpr.var 0 * (PExpr.var 1 * PExpr.var 0 + PExpr.var 2 * 0) + 0 * (PExpr.var 2 * PExpr.var 0 + PExpr.var 3 * 0))
          (PExpr.var 0 * PExpr.var 0 * PExpr.var 1) rfl
      have e01 : u * (a * (-v * b * d) + b * (v * a * d)) + 0 * (b * (-v * b * d) + d * (v * a * d)) = 0 :=
        poly_eq_of_norm_eq [u, v, a, b, d]
          (PExpr.var 0 * (PExpr.var 2 * (-PExpr.var 1 * PExpr.var 3 * PExpr.var 4) + PExpr.var 3 * (PExpr.var 1 * PExpr.var 2 * PExpr.var 4)) +
           0 * (PExpr.var 3 * (-PExpr.var 1 * PExpr.var 3 * PExpr.var 4) + PExpr.var 4 * (PExpr.var 1 * PExpr.var 2 * PExpr.var 4)))
          0 rfl
      have e10 : (-v * b * d) * (a * u + b * 0) + (v * a * d) * (b * u + d * 0) = 0 :=
        poly_eq_of_norm_eq [u, v, a, b, d]
          ((-PExpr.var 1 * PExpr.var 3 * PExpr.var 4) * (PExpr.var 2 * PExpr.var 0 + PExpr.var 3 * 0) +
           (PExpr.var 1 * PExpr.var 2 * PExpr.var 4) * (PExpr.var 3 * PExpr.var 0 + PExpr.var 4 * 0))
          0 rfl
      have e11_raw : (-v * b * d) * (a * (-v * b * d) + b * (v * a * d)) +
          (v * a * d) * (b * (-v * b * d) + d * (v * a * d)) =
          (v * v * a * (a * d - b * b) * d) * d :=
        poly_eq_of_norm_eq [v, a, b, d]
          ((-PExpr.var 0 * PExpr.var 2 * PExpr.var 3) * (PExpr.var 1 * (-PExpr.var 0 * PExpr.var 2 * PExpr.var 3) + PExpr.var 2 * (PExpr.var 0 * PExpr.var 1 * PExpr.var 3)) +
           (PExpr.var 0 * PExpr.var 1 * PExpr.var 3) * (PExpr.var 2 * (-PExpr.var 0 * PExpr.var 2 * PExpr.var 3) + PExpr.var 3 * (PExpr.var 0 * PExpr.var 1 * PExpr.var 3)))
          ((PExpr.var 0 * PExpr.var 0 * PExpr.var 1 * (PExpr.var 1 * PExpr.var 3 - PExpr.var 2 * PExpr.var 2) * PExpr.var 3) * PExpr.var 3) rfl
      rw [hsq] at e11_raw
      rw [e00, e01, e10, e11_raw]

/-- **Seminar Witnesses & Universal `GL_2(Q)` Obstruction on `[[2,1],[1,1]]`**:
    1. `[[3,3],[3,4]]` (`b ≠ 0`, `B^T adj(A) B = 9 ≠ 0`) IS `Q`-congruent to `diag(3, 4)` via `Q = [[1,-2],[0,2]]` (`k = 1`, `det Q = 2`),
       refuting the naive claim that `1x1` block drop requires `B = 0`, AND
    2. `[[2,1],[1,1]]` is **provably non-congruent** to `diag(2, 1)` over **all** `Q ∈ GL_2(Q)`. -/
theorem t3_block_drop_obstruction_2111_and_witness_3334 :
    let Q34 : Mat2Z := ⟨1, -2, 0, 2⟩
    let M34 : Mat2Z := ⟨3, 3, 3, 4⟩
    mat2Det Q34 = 2 ∧
    mat2Mul (mat2Transpose Q34) (mat2Mul M34 Q34) = ⟨3, 0, 0, 4⟩ ∧
    (¬ ∃ (Q : Mat2Z) (k : Int), k ≠ 0 ∧ mat2Det Q ≠ 0 ∧
      mat2Mul (mat2Transpose Q) (mat2Mul ⟨2, 1, 1, 1⟩ Q) = ⟨k * k * 2, 0, 0, k * k * 1⟩) := by
  refine ⟨by decide, by decide, ?_⟩
  intro hex
  have hsq := (t3_block_drop_1x1_iff_square_class 2 1 1 (by decide) (by decide) (by decide)).mp hex
  rcases hsq with ⟨u, v, hv, _, heq⟩
  have hsimp : v * v * 2 * (2 * 1 - 1 * 1) * 1 = 2 * (v * v) := by omega
  rw [hsimp] at heq
  exact t3_two_mul_sq_ne_sq u v hv heq.symm

/-! ### Part 3C: `GF(2)` Parity Fold & Doubled-Coordinate Mirror Billiard -/

private def gf2DetOddPair : PExpr × PExpr :=
  ((2 * PExpr.var 0 + 1) * (2 * PExpr.var 1 + 1) - (2 * PExpr.var 2) * (2 * PExpr.var 3),
   2 * (2 * PExpr.var 0 * PExpr.var 1 + PExpr.var 0 + PExpr.var 1 - 2 * PExpr.var 2 * PExpr.var 3) + 1)

/-- **`GF(2)` Invertibility Criterion (`det A ≡ 1 mod 2`)**:
    A `2x2` integer matrix `A` admits an integer inverse modulo `2` iff `(mat2Det A) % 2 = 1`. -/
theorem t3_gf2_inv_2x2_iff_det_odd (A : Mat2Z) :
    (∃ B : Mat2Z,
      (mat2Mul A B).p % 2 = 1 ∧ (mat2Mul A B).q % 2 = 0 ∧
      (mat2Mul A B).r % 2 = 0 ∧ (mat2Mul A B).s % 2 = 1) ↔
      mat2Det A % 2 = 1 := by
  have det_mul : ∀ X Y : Mat2Z, mat2Det (mat2Mul X Y) = mat2Det X * mat2Det Y :=
    fun X Y => poly_eq_of_norm_eq [X.p, X.q, X.r, X.s, Y.p, Y.q, Y.r, Y.s] mat2DetMulPair.1 mat2DetMulPair.2 rfl
  constructor
  · rintro ⟨B, hp, hq, hr, hs⟩
    let C := mat2Mul A B
    have hpC : C.p % 2 = 1 := hp
    have hqC : C.q % 2 = 0 := hq
    have hrC : C.r % 2 = 0 := hr
    have hsC : C.s % 2 = 1 := hs
    have hc_det : mat2Det C % 2 = 1 := by
      unfold mat2Det
      let qp := C.p / 2; let qs := C.s / 2; let qq := C.q / 2; let qr := C.r / 2
      have hp1 : C.p = 2 * qp + 1 := by omega
      have hs1 : C.s = 2 * qs + 1 := by omega
      have hq0 : C.q = 2 * qq := by omega
      have hr0 : C.r = 2 * qr := by omega
      have hexp : (2 * qp + 1) * (2 * qs + 1) - (2 * qq) * (2 * qr) =
          2 * (2 * qp * qs + qp + qs - 2 * qq * qr) + 1 :=
        poly_eq_of_norm_eq [qp, qs, qq, qr] gf2DetOddPair.1 gf2DetOddPair.2 rfl
      change (C.p * C.s - C.q * C.r) % 2 = 1
      rw [hp1, hs1, hq0, hr0, hexp]
      omega
    have hmul := det_mul A B
    change mat2Det C = mat2Det A * mat2Det B at hmul
    rcases Decidable.em (mat2Det A % 2 = 1) with ha_odd | ha_odd
    · exact ha_odd
    · let qA := mat2Det A / 2
      have ha_ev : mat2Det A = 2 * qA := by omega
      have hprod_ev : mat2Det A * mat2Det B = 2 * (qA * mat2Det B) := by
        rw [ha_ev]; exact Int.mul_assoc 2 qA (mat2Det B)
      rw [hmul, hprod_ev] at hc_det
      omega
  · intro hodd
    refine ⟨mat2Adj A, ?_⟩
    have hadj : mat2Mul A (mat2Adj A) = ⟨mat2Det A, 0, 0, mat2Det A⟩ := by
      unfold mat2Mul mat2Adj mat2Det; dsimp only
      have e00 : A.p * A.s + A.q * (-A.r) = A.p * A.s - A.q * A.r :=
        poly_eq_of_norm_eq [A.p, A.q, A.r, A.s]
          (PExpr.var 0 * PExpr.var 3 + PExpr.var 1 * (-PExpr.var 2))
          (PExpr.var 0 * PExpr.var 3 - PExpr.var 1 * PExpr.var 2) rfl
      have e01 : A.p * (-A.q) + A.q * A.p = 0 :=
        poly_eq_of_norm_eq [A.p, A.q] (PExpr.var 0 * (-PExpr.var 1) + PExpr.var 1 * PExpr.var 0) 0 rfl
      have e10 : A.r * A.s + A.s * (-A.r) = 0 :=
        poly_eq_of_norm_eq [A.r, A.s] (PExpr.var 0 * PExpr.var 1 + PExpr.var 1 * (-PExpr.var 0)) 0 rfl
      have e11 : A.r * (-A.q) + A.s * A.p = A.p * A.s - A.q * A.r :=
        poly_eq_of_norm_eq [A.p, A.q, A.r, A.s]
          (PExpr.var 2 * (-PExpr.var 1) + PExpr.var 3 * PExpr.var 0)
          (PExpr.var 0 * PExpr.var 3 - PExpr.var 1 * PExpr.var 2) rfl
      rw [e00, e01, e10, e11]
    rw [hadj]
    dsimp only
    exact ⟨hodd, rfl, rfl, hodd⟩

private def gf2SchurEvenPair : PExpr × PExpr :=
  let vu1 := PExpr.var 0; let vu2 := PExpr.var 1; let vc := PExpr.var 2
  let vb1 := PExpr.var 3; let vb2 := PExpr.var 4; let vw := PExpr.var 5
  let pa11 := 2 * vu1; let pa22 := 2 * vu2; let pd := 2 * vw
  let pdet := pa11 * pa22 - vc * vc
  (pdet * pd - (vb1 * (pa22 * vb1 - vc * vb2) + vb2 * (-vc * vb1 + pa11 * vb2)),
   2 * ((4 * vu1 * vu2 - vc * vc) * vw - vu2 * vb1 * vb1 + vc * vb1 * vb2 - vu1 * vb2 * vb2))

/-- **`GF(2)` Schur Even-Diagonal Preservation Theorem**:
    For any symmetric `3x3` block matrix with `2x2` pivot `A = [[2*u1, c], [c, 2*u2]]`
    (`det A % 2 = 1`) and even corner `d = 2*w`, the cleared Schur numerator
    `det(A) * d - B^T adj(A) B` is always even (`% 2 = 0`) while `det(A) % 2 = 1`. -/
theorem t3_gf2_schur_preserves_even_diagonal (u1 u2 c b1 b2 w : Int) :
    let a11 := 2 * u1; let a22 := 2 * u2; let d := 2 * w
    let detA := a11 * a22 - c * c
    let schurNum := detA * d - (b1 * (a22 * b1 - c * b2) + b2 * (-c * b1 + a11 * b2))
    schurNum % 2 = 0 := by
  dsimp only
  have htwo :
      (2 * u1 * (2 * u2) - c * c) * (2 * w) -
        (b1 * (2 * u2 * b1 - c * b2) + b2 * (-c * b1 + 2 * u1 * b2)) =
      2 * ((4 * u1 * u2 - c * c) * w - u2 * b1 * b1 + c * b1 * b2 - u1 * b2 * b2) :=
    poly_eq_of_norm_eq [u1, u2, c, b1, b2, w] gf2SchurEvenPair.1 gf2SchurEvenPair.2 rfl
  rw [htwo]
  omega

structure BilliardState where
  x  : Int
  y  : Int
  dx : Int
  dy : Int
  deriving Repr, DecidableEq

/-- Single doubled-coordinate mirror-billiard step on `[0, 2p] × [0, 2q]`. -/
def billiardStep (w h : Int) (st : BilliardState) : BilliardState :=
  let nx := st.x + st.dx
  let ny := st.y + st.dy
  let ndx := if intIsZero nx || intIsZero (nx - w) then -st.dx else st.dx
  let ndy := if intIsZero ny || intIsZero (ny - h) then -st.dy else st.dy
  ⟨nx, ny, ndx, ndy⟩

def billiardIter (w h : Int) : Nat → BilliardState → BilliardState
  | 0, st => st
  | k + 1, st => billiardIter w h k (billiardStep w h st)

/-- **Mirror Billiard `(2, 3)` Eulerian Cycle & Unimodular Euclid Refutation (`[propext]` only)**:
    On `(p, q) = (2, 3)` (`W = 4, H = 6`, `24` directed boundary-and-interior half-edges = `1` closed
    24-step curve), the trajectory returns in period `24` (`1` Eulerian curve = `gcd(2, 3)`),
    `3 % 2 ≠ 0` refutes single-shear divisibility (`p ∣ q`), and `U = [[-1, 1], [3, -2]]` is unimodular (`det U = -1`). -/
theorem t3_mirror_billiard_2_3_refutes_single_shear :
    let st0 : BilliardState := ⟨1, 0, 1, 1⟩
    let U : Mat2Z := ⟨-1, 1, 3, -2⟩
    billiardIter 4 6 24 st0 = st0 ∧
    billiardIter 4 6 12 st0 ≠ st0 ∧
    billiardIter 4 6 8 st0 ≠ st0 ∧
    (3 : Nat) % 2 ≠ 0 ∧
    mat2Det U = -1 ∧
    U.p * 2 + U.q * 3 = 1 ∧
    U.r * 2 + U.s * 3 = 0 := by
  decide

end S150Pilot1Theorems
