/-
  S150Pilot1Theorems/Topic1FrickeCayley.lean

  Topic 1 (`continuum`) — Unified Fricke–Cayley Discriminant Theorem Across
  Definite Hurwitz/Lipschitz Quaternion Orders & Split GL_2(Z) Continued-Fraction
  Transpose Pairs:
    kappa(a, b, x, y, z) = 4*a*b - b*x^2 - a*y^2 - z^2 + x*y*z.
-/

import S150Pilot1Theorems.IntPoly

namespace S150Pilot1Theorems

/-- Universal Fricke–Cayley discriminant polynomial over `Int`. -/
def frickeDisc (a b x y z : Int) : Int :=
  4 * a * b - b * x * x - a * y * y - z * z + x * y * z

private def frickeDiscE (pa pb px py pz : PExpr) : PExpr :=
  4 * pa * pb - pb * px * px - pa * py * py - pz * pz + px * py * pz

private def hom16Pair : PExpr × PExpr :=
  let va := PExpr.var 0; let vb := PExpr.var 1
  let vx := PExpr.var 2; let vy := PExpr.var 3; let vz := PExpr.var 4
  (frickeDiscE (4 * va) (4 * vb) (2 * vx) (2 * vy) (4 * vz),
   16 * frickeDiscE va vb vx vy vz)

/-- Exact homogeneity under doubled Hurwitz coordinates:
    `kappa(4a, 4b, 2x, 2y, 4z) = 16 * kappa(a, b, x, y, z)`. -/
theorem t1_fricke_homogeneity_16 (a b x y z : Int) :
    frickeDisc (4 * a) (4 * b) (2 * x) (2 * y) (4 * z) = 16 * frickeDisc a b x y z :=
  poly_eq_of_norm_eq [a, b, x, y, z] hom16Pair.1 hom16Pair.2 rfl

/-! ### Part 1A: Definite Hurwitz / `SU(2)` Quaternion Order Side -/

structure Quat4Z where
  w : Int
  x : Int
  y : Int
  z : Int
  deriving Repr, DecidableEq

def quatConj4 (q : Quat4Z) : Quat4Z := ⟨q.w, -q.x, -q.y, -q.z⟩

def quatSub4 (p q : Quat4Z) : Quat4Z := ⟨p.w - q.w, p.x - q.x, p.y - q.y, p.z - q.z⟩

def quatMul4 (p q : Quat4Z) : Quat4Z :=
  ⟨ p.w * q.w - p.x * q.x - p.y * q.y - p.z * q.z
  , p.w * q.x + p.x * q.w + p.y * q.z - p.z * q.y
  , p.w * q.y - p.x * q.z + p.y * q.w + p.z * q.x
  , p.w * q.z + p.x * q.y - p.y * q.x + p.z * q.w ⟩

def quatNormSq4 (q : Quat4Z) : Int :=
  q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z

def quatDot4 (p q : Quat4Z) : Int :=
  p.w * q.w + p.x * q.x + p.y * q.y + p.z * q.z

def crossSq3 (p q : Quat4Z) : Int :=
  let cx := p.y * q.z - p.z * q.y
  let cy := p.z * q.x - p.x * q.z
  let cz := p.x * q.y - p.y * q.x
  cx * cx + cy * cy + cz * cz

private abbrev QuatE := PExpr × PExpr × PExpr × PExpr

private def qmulE (p q : QuatE) : QuatE :=
  (p.1 * q.1     - p.2.1 * q.2.1   - p.2.2.1 * q.2.2.1 - p.2.2.2 * q.2.2.2,
   p.1 * q.2.1   + p.2.1 * q.1     + p.2.2.1 * q.2.2.2 - p.2.2.2 * q.2.2.1,
   p.1 * q.2.2.1 - p.2.1 * q.2.2.2 + p.2.2.1 * q.1     + p.2.2.2 * q.2.1,
   p.1 * q.2.2.2 + p.2.1 * q.2.2.1 - p.2.2.1 * q.2.1   + p.2.2.2 * q.1)

private def qconjE (q : QuatE) : QuatE := (q.1, -q.2.1, -q.2.2.1, -q.2.2.2)

private def qnormE (q : QuatE) : PExpr :=
  q.1 * q.1 + q.2.1 * q.2.1 + q.2.2.1 * q.2.2.1 + q.2.2.2 * q.2.2.2

private def qdotE (p q : QuatE) : PExpr :=
  p.1 * q.1 + p.2.1 * q.2.1 + p.2.2.1 * q.2.2.1 + p.2.2.2 * q.2.2.2

private def qsubE (p q : QuatE) : QuatE :=
  (p.1 - q.1, p.2.1 - q.2.1, p.2.2.1 - q.2.2.1, p.2.2.2 - q.2.2.2)

private def crossSq3E (p q : QuatE) : PExpr :=
  let cx := p.2.2.1 * q.2.2.2 - p.2.2.2 * q.2.2.1
  let cy := p.2.2.2 * q.2.1   - p.2.1   * q.2.2.2
  let cz := p.2.1   * q.2.2.1 - p.2.2.1 * q.2.1
  cx * cx + cy * cy + cz * cz

private def lagrange3Pair : PExpr × PExpr :=
  let ax := PExpr.var 0; let ay := PExpr.var 1; let az := PExpr.var 2
  let bx := PExpr.var 3; let by_ := PExpr.var 4; let bz := PExpr.var 5
  let na3 := ax*ax + ay*ay + az*az
  let nb3 := bx*bx + by_*by_ + bz*bz
  let dt3 := ax*bx + ay*by_ + az*bz
  let cx := ay*bz - az*by_; let cy := az*bx - ax*bz; let cz := ax*by_ - ay*bx
  (na3 * nb3 - dt3 * dt3, cx*cx + cy*cy + cz*cz)

private def frickeToLagrangePair : PExpr × PExpr :=
  let aw := PExpr.var 0; let bw := PExpr.var 1
  let na3 := PExpr.var 2; let nb3 := PExpr.var 3; let dt3 := PExpr.var 4
  (frickeDiscE (aw*aw + na3) (bw*bw + nb3) (2*aw) (2*bw) (2*(aw*bw - dt3)),
   4 * (na3 * nb3 - dt3 * dt3))

private def commNormToCrossPair : PExpr × PExpr :=
  let a : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let b : QuatE := (.var 4, .var 5, .var 6, .var 7)
  (qnormE (qsubE (qmulE a b) (qmulE b a)), 4 * crossSq3E a b)

/-- **Definite Fricke–Quaternion Commutator Identity**:
    For all doubled-coordinate quaternions `A, B ∈ Z^4`,
    `frickeDisc ||A||^2 ||B||^2 (2*A.w) (2*B.w) (2*(AB).w) = ||AB - BA||^2 = 4 * ||A_vec × B_vec||^2`. -/
theorem t1_fricke_definite_commutator_exact (A B : Quat4Z) :
    let nA := quatNormSq4 A
    let nB := quatNormSq4 B
    let z2 := (quatMul4 A B).w
    frickeDisc nA nB (2 * A.w) (2 * B.w) (2 * z2) = quatNormSq4 (quatSub4 (quatMul4 A B) (quatMul4 B A)) ∧
    quatNormSq4 (quatSub4 (quatMul4 A B) (quatMul4 B A)) = 4 * crossSq3 A B := by
  dsimp only
  let na3 := A.x*A.x + A.y*A.y + A.z*A.z
  let nb3 := B.x*B.x + B.y*B.y + B.z*B.z
  let dt3 := A.x*B.x + A.y*B.y + A.z*B.z
  have hnA : quatNormSq4 A = A.w * A.w + na3 := by
    unfold quatNormSq4; omega
  have hnB : quatNormSq4 B = B.w * B.w + nb3 := by
    unfold quatNormSq4; omega
  have hz2 : (quatMul4 A B).w = A.w * B.w - dt3 := by
    unfold quatMul4; dsimp only; omega
  have hlag : na3 * nb3 - dt3 * dt3 = crossSq3 A B :=
    poly_eq_of_norm_eq [A.x, A.y, A.z, B.x, B.y, B.z] lagrange3Pair.1 lagrange3Pair.2 rfl
  have hfr : frickeDisc (A.w * A.w + na3) (B.w * B.w + nb3) (2 * A.w) (2 * B.w) (2 * (A.w * B.w - dt3)) =
      4 * (na3 * nb3 - dt3 * dt3) :=
    poly_eq_of_norm_eq [A.w, B.w, na3, nb3, dt3] frickeToLagrangePair.1 frickeToLagrangePair.2 rfl
  have hcomm : quatNormSq4 (quatSub4 (quatMul4 A B) (quatMul4 B A)) = 4 * crossSq3 A B :=
    poly_eq_of_norm_eq [A.w, A.x, A.y, A.z, B.w, B.x, B.y, B.z] commNormToCrossPair.1 commNormToCrossPair.2 rfl
  rw [hnA, hnB, hz2, hfr, hlag, hcomm]
  exact ⟨rfl, rfl⟩

private def groupCommW_eq_dot_Pair : PExpr × PExpr :=
  let a : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let b : QuatE := (.var 4, .var 5, .var 6, .var 7)
  ((qmulE (qmulE a b) (qmulE (qconjE a) (qconjE b))).1, qdotE (qmulE a b) (qmulE b a))

private def dotAB_BA_Pair : PExpr × PExpr :=
  let a : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let b : QuatE := (.var 4, .var 5, .var 6, .var 7)
  (qdotE (qmulE a b) (qmulE b a), qnormE a * qnormE b - 2 * crossSq3E a b)

/-- **Multiplicative Group-Commutator Scalar Part & Norm Law**:
    `Re(A B conj(A) conj(B)) = ||A||^2 ||B||^2 - 2 * ||A_vec × B_vec||^2`, so in Hurwitz
    units (`||A||^2 = 4a, ||B||^2 = 4b, crossSq3 = 8D`), `Re(g h g_bar h_bar) = ab - D`
    and `trd[g, h] = 2 - kappa / (ab)`. -/
theorem t1_hurwitz_group_commutator_trace (A B : Quat4Z) :
    (quatMul4 (quatMul4 A B) (quatMul4 (quatConj4 A) (quatConj4 B))).w =
      quatNormSq4 A * quatNormSq4 B - 2 * crossSq3 A B ∧
    quatDot4 (quatMul4 A B) (quatMul4 B A) =
      quatNormSq4 A * quatNormSq4 B - 2 * crossSq3 A B := by
  let env := [A.w, A.x, A.y, A.z, B.w, B.x, B.y, B.z]
  have h1 : (quatMul4 (quatMul4 A B) (quatMul4 (quatConj4 A) (quatConj4 B))).w =
      quatDot4 (quatMul4 A B) (quatMul4 B A) :=
    poly_eq_of_norm_eq env groupCommW_eq_dot_Pair.1 groupCommW_eq_dot_Pair.2 rfl
  have h2 : quatDot4 (quatMul4 A B) (quatMul4 B A) =
      quatNormSq4 A * quatNormSq4 B - 2 * crossSq3 A B :=
    poly_eq_of_norm_eq env dotAB_BA_Pair.1 dotAB_BA_Pair.2 rfl
  rw [h1, h2]
  exact ⟨rfl, rfl⟩

structure Mat3Z where
  m00 : Int
  m01 : Int
  m02 : Int
  m10 : Int
  m11 : Int
  m12 : Int
  m20 : Int
  m21 : Int
  m22 : Int
  deriving Repr, DecidableEq

/-- Unnormalized integer `SO(3)` rotation numerator matrix (`||q||^2 * R_q`). -/
def so3Unnorm (q : Quat4Z) : Mat3Z :=
  let w := q.w; let x := q.x; let y := q.y; let z := q.z
  { m00 := w*w + x*x - y*y - z*z, m01 := 2*(x*y - w*z),         m02 := 2*(x*z + w*y)
  , m10 := 2*(x*y + w*z),         m11 := w*w - x*x + y*y - z*z, m12 := 2*(y*z - w*x)
  , m20 := 2*(x*z - w*y),         m21 := 2*(y*z + w*x),         m22 := w*w - x*x - y*y + z*z }

def matMul3 (A B : Mat3Z) : Mat3Z :=
  { m00 := A.m00*B.m00 + A.m01*B.m10 + A.m02*B.m20
  , m01 := A.m00*B.m01 + A.m01*B.m11 + A.m02*B.m21
  , m02 := A.m00*B.m02 + A.m01*B.m12 + A.m02*B.m22
  , m10 := A.m10*B.m00 + A.m11*B.m10 + A.m12*B.m20
  , m11 := A.m10*B.m01 + A.m11*B.m11 + A.m12*B.m21
  , m12 := A.m10*B.m02 + A.m11*B.m12 + A.m12*B.m22
  , m20 := A.m20*B.m00 + A.m21*B.m10 + A.m22*B.m20
  , m21 := A.m20*B.m01 + A.m21*B.m11 + A.m22*B.m21
  , m22 := A.m20*B.m02 + A.m21*B.m12 + A.m22*B.m22 }

def matSub3 (A B : Mat3Z) : Mat3Z :=
  { m00 := A.m00 - B.m00, m01 := A.m01 - B.m01, m02 := A.m02 - B.m02
  , m10 := A.m10 - B.m10, m11 := A.m11 - B.m11, m12 := A.m12 - B.m12
  , m20 := A.m20 - B.m20, m21 := A.m21 - B.m21, m22 := A.m22 - B.m22 }

def frobSq3 (A : Mat3Z) : Int :=
  A.m00*A.m00 + A.m01*A.m01 + A.m02*A.m02 +
  A.m10*A.m10 + A.m11*A.m11 + A.m12*A.m12 +
  A.m20*A.m20 + A.m21*A.m21 + A.m22*A.m22

private def mat3Transpose (A : Mat3Z) : Mat3Z :=
  { m00 := A.m00, m01 := A.m10, m02 := A.m20
  , m10 := A.m01, m11 := A.m11, m12 := A.m21
  , m20 := A.m02, m21 := A.m12, m22 := A.m22 }

private def mat3Tr (A : Mat3Z) : Int := A.m00 + A.m11 + A.m22

private abbrev Mat3E :=
  (PExpr × PExpr × PExpr) × (PExpr × PExpr × PExpr) × (PExpr × PExpr × PExpr)

private def so3E (q : QuatE) : Mat3E :=
  let w := q.1; let x := q.2.1; let y := q.2.2.1; let z := q.2.2.2
  ((w*w + x*x - y*y - z*z, 2*(x*y - w*z),         2*(x*z + w*y)),
   (2*(x*y + w*z),         w*w - x*x + y*y - z*z, 2*(y*z - w*x)),
   (2*(x*z - w*y),         2*(y*z + w*x),         w*w - x*x - y*y + z*z))

private def mmul3E (A B : Mat3E) : Mat3E :=
  let ((a00, a01, a02), (a10, a11, a12), (a20, a21, a22)) := A
  let ((b00, b01, b02), (b10, b11, b12), (b20, b21, b22)) := B
  ((a00*b00 + a01*b10 + a02*b20, a00*b01 + a01*b11 + a02*b21, a00*b02 + a01*b12 + a02*b22),
   (a10*b00 + a11*b10 + a12*b20, a10*b01 + a11*b11 + a12*b21, a10*b02 + a11*b12 + a12*b22),
   (a20*b00 + a21*b10 + a22*b20, a20*b01 + a21*b11 + a22*b21, a20*b02 + a21*b12 + a22*b22))

private def so3HomPair : Mat3E × Mat3E :=
  let a : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let b : QuatE := (.var 4, .var 5, .var 6, .var 7)
  (so3E (qmulE a b), mmul3E (so3E a) (so3E b))

private theorem so3Unnorm_hom (A B : Quat4Z) :
    so3Unnorm (quatMul4 A B) = matMul3 (so3Unnorm A) (so3Unnorm B) := by
  let env := [A.w, A.x, A.y, A.z, B.w, B.x, B.y, B.z]
  have e00 : (so3Unnorm (quatMul4 A B)).m00 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m00 :=
    poly_eq_of_norm_eq env so3HomPair.1.1.1 so3HomPair.2.1.1 rfl
  have e01 : (so3Unnorm (quatMul4 A B)).m01 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m01 :=
    poly_eq_of_norm_eq env so3HomPair.1.1.2.1 so3HomPair.2.1.2.1 rfl
  have e02 : (so3Unnorm (quatMul4 A B)).m02 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m02 :=
    poly_eq_of_norm_eq env so3HomPair.1.1.2.2 so3HomPair.2.1.2.2 rfl
  have e10 : (so3Unnorm (quatMul4 A B)).m10 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m10 :=
    poly_eq_of_norm_eq env so3HomPair.1.2.1.1 so3HomPair.2.2.1.1 rfl
  have e11 : (so3Unnorm (quatMul4 A B)).m11 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m11 :=
    poly_eq_of_norm_eq env so3HomPair.1.2.1.2.1 so3HomPair.2.2.1.2.1 rfl
  have e12 : (so3Unnorm (quatMul4 A B)).m12 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m12 :=
    poly_eq_of_norm_eq env so3HomPair.1.2.1.2.2 so3HomPair.2.2.1.2.2 rfl
  have e20 : (so3Unnorm (quatMul4 A B)).m20 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m20 :=
    poly_eq_of_norm_eq env so3HomPair.1.2.2.1 so3HomPair.2.2.2.1 rfl
  have e21 : (so3Unnorm (quatMul4 A B)).m21 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m21 :=
    poly_eq_of_norm_eq env so3HomPair.1.2.2.2.1 so3HomPair.2.2.2.2.1 rfl
  have e22 : (so3Unnorm (quatMul4 A B)).m22 = (matMul3 (so3Unnorm A) (so3Unnorm B)).m22 :=
    poly_eq_of_norm_eq env so3HomPair.1.2.2.2.2 so3HomPair.2.2.2.2.2 rfl
  cases hs1 : so3Unnorm (quatMul4 A B)
  cases hs2 : matMul3 (so3Unnorm A) (so3Unnorm B)
  rw [hs1, hs2] at e00 e01 e02 e10 e11 e12 e20 e21 e22
  dsimp only at e00 e01 e02 e10 e11 e12 e20 e21 e22
  subst e00 e01 e02 e10 e11 e12 e20 e21 e22
  rfl

private def so3FrobSinglePair : PExpr × PExpr :=
  let q : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let ((r00, r01, r02), (r10, r11, r12), (r20, r21, r22)) := so3E q
  (r00*r00 + r01*r01 + r02*r02 + r10*r10 + r11*r11 + r12*r12 + r20*r20 + r21*r21 + r22*r22,
   3 * qnormE q * qnormE q)

private def so3ConjTransposePair : Mat3E × Mat3E :=
  let q : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let ((r00, r01, r02), (r10, r11, r12), (r20, r21, r22)) := so3E q
  (so3E (qconjE q), ((r00, r10, r20), (r01, r11, r21), (r02, r12, r22)))

private def so3TracePair : PExpr × PExpr :=
  let q : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let ((r00, _, _), (_, r11, _), (_, _, r22)) := so3E q
  (r00 + r11 + r22, 4 * q.1 * q.1 - qnormE q)

private def frobSubExpandPair : PExpr × PExpr :=
  let a0 := PExpr.var 0; let a1 := PExpr.var 1; let a2 := PExpr.var 2
  let a3 := PExpr.var 3; let a4 := PExpr.var 4; let a5 := PExpr.var 5
  let a6 := PExpr.var 6; let a7 := PExpr.var 7; let a8 := PExpr.var 8
  let b0 := PExpr.var 9; let b1 := PExpr.var 10; let b2 := PExpr.var 11
  let b3 := PExpr.var 12; let b4 := PExpr.var 13; let b5 := PExpr.var 14
  let b6 := PExpr.var 15; let b7 := PExpr.var 16; let b8 := PExpr.var 17
  ((a0-b0)*(a0-b0) + (a1-b1)*(a1-b1) + (a2-b2)*(a2-b2) +
   (a3-b3)*(a3-b3) + (a4-b4)*(a4-b4) + (a5-b5)*(a5-b5) +
   (a6-b6)*(a6-b6) + (a7-b7)*(a7-b7) + (a8-b8)*(a8-b8),
   (a0*a0 + a1*a1 + a2*a2 + a3*a3 + a4*a4 + a5*a5 + a6*a6 + a7*a7 + a8*a8) +
   (b0*b0 + b1*b1 + b2*b2 + b3*b3 + b4*b4 + b5*b5 + b6*b6 + b7*b7 + b8*b8) -
   2 * ((a0*b0 + a3*b3 + a6*b6) + (a1*b1 + a4*b4 + a7*b7) + (a2*b2 + a5*b5 + a8*b8)))

private def qNormMulPair : PExpr × PExpr :=
  let p : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let q : QuatE := (.var 4, .var 5, .var 6, .var 7)
  (qnormE (qmulE p q), qnormE p * qnormE q)

private theorem quatNormSq4_mul (A B : Quat4Z) :
    quatNormSq4 (quatMul4 A B) = quatNormSq4 A * quatNormSq4 B :=
  poly_eq_of_norm_eq [A.w, A.x, A.y, A.z, B.w, B.x, B.y, B.z] qNormMulPair.1 qNormMulPair.2 rfl

private theorem quatNormSq4_conj (A : Quat4Z) : quatNormSq4 (quatConj4 A) = quatNormSq4 A :=
  poly_eq_of_norm_eq [A.w, A.x, A.y, A.z] (qnormE (qconjE (.var 0, .var 1, .var 2, .var 3)))
    (qnormE (.var 0, .var 1, .var 2, .var 3)) rfl

private def conjMulW_Pair : PExpr × PExpr :=
  let p : QuatE := (.var 0, .var 1, .var 2, .var 3)
  let q : QuatE := (.var 4, .var 5, .var 6, .var 7)
  ((qmulE (qconjE p) q).1, qdotE p q)

private theorem so3Unnorm_conj (q : Quat4Z) : so3Unnorm (quatConj4 q) = mat3Transpose (so3Unnorm q) := by
  let env := [q.w, q.x, q.y, q.z]
  have e00 : (so3Unnorm (quatConj4 q)).m00 = (mat3Transpose (so3Unnorm q)).m00 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.1.1 so3ConjTransposePair.2.1.1 rfl
  have e01 : (so3Unnorm (quatConj4 q)).m01 = (mat3Transpose (so3Unnorm q)).m01 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.1.2.1 so3ConjTransposePair.2.1.2.1 rfl
  have e02 : (so3Unnorm (quatConj4 q)).m02 = (mat3Transpose (so3Unnorm q)).m02 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.1.2.2 so3ConjTransposePair.2.1.2.2 rfl
  have e10 : (so3Unnorm (quatConj4 q)).m10 = (mat3Transpose (so3Unnorm q)).m10 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.2.1.1 so3ConjTransposePair.2.2.1.1 rfl
  have e11 : (so3Unnorm (quatConj4 q)).m11 = (mat3Transpose (so3Unnorm q)).m11 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.2.1.2.1 so3ConjTransposePair.2.2.1.2.1 rfl
  have e12 : (so3Unnorm (quatConj4 q)).m12 = (mat3Transpose (so3Unnorm q)).m12 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.2.1.2.2 so3ConjTransposePair.2.2.1.2.2 rfl
  have e20 : (so3Unnorm (quatConj4 q)).m20 = (mat3Transpose (so3Unnorm q)).m20 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.2.2.1 so3ConjTransposePair.2.2.2.1 rfl
  have e21 : (so3Unnorm (quatConj4 q)).m21 = (mat3Transpose (so3Unnorm q)).m21 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.2.2.2.1 so3ConjTransposePair.2.2.2.2.1 rfl
  have e22 : (so3Unnorm (quatConj4 q)).m22 = (mat3Transpose (so3Unnorm q)).m22 :=
    poly_eq_of_norm_eq env so3ConjTransposePair.1.2.2.2.2 so3ConjTransposePair.2.2.2.2.2 rfl
  cases hs1 : so3Unnorm (quatConj4 q)
  cases hs2 : mat3Transpose (so3Unnorm q)
  rw [hs1, hs2] at e00 e01 e02 e10 e11 e12 e20 e21 e22
  dsimp only at e00 e01 e02 e10 e11 e12 e20 e21 e22
  subst e00 e01 e02 e10 e11 e12 e20 e21 e22
  rfl

private def frobBridgePair : PExpr × PExpr :=
  let nP := PExpr.var 0; let nQ := PExpr.var 1; let dt := PExpr.var 2
  (3 * nP * nP + 3 * nQ * nQ - 2 * (4 * dt * dt - nP * nQ),
   3 * (nP - nQ) * (nP - nQ) + 8 * (nP * nQ - dt * dt))

private theorem frobSq3_so3Unnorm_diff (P Q : Quat4Z) :
    let nP := quatNormSq4 P
    let nQ := quatNormSq4 Q
    let dPQ := quatDot4 P Q
    frobSq3 (matSub3 (so3Unnorm P) (so3Unnorm Q)) =
      3 * (nP - nQ) * (nP - nQ) + 8 * (nP * nQ - dPQ * dPQ) := by
  dsimp only
  let RP := so3Unnorm P
  let RQ := so3Unnorm Q
  have hexp : frobSq3 (matSub3 RP RQ) =
      frobSq3 RP + frobSq3 RQ - 2 * mat3Tr (matMul3 (mat3Transpose RP) RQ) :=
    poly_eq_of_norm_eq
      [RP.m00, RP.m01, RP.m02, RP.m10, RP.m11, RP.m12, RP.m20, RP.m21, RP.m22,
       RQ.m00, RQ.m01, RQ.m02, RQ.m10, RQ.m11, RQ.m12, RQ.m20, RQ.m21, RQ.m22]
      frobSubExpandPair.1 frobSubExpandPair.2 rfl
  have hfP : frobSq3 RP = 3 * quatNormSq4 P * quatNormSq4 P :=
    poly_eq_of_norm_eq [P.w, P.x, P.y, P.z] so3FrobSinglePair.1 so3FrobSinglePair.2 rfl
  have hfQ : frobSq3 RQ = 3 * quatNormSq4 Q * quatNormSq4 Q :=
    poly_eq_of_norm_eq [Q.w, Q.x, Q.y, Q.z] so3FrobSinglePair.1 so3FrobSinglePair.2 rfl
  have htr1 : matMul3 (mat3Transpose RP) RQ = so3Unnorm (quatMul4 (quatConj4 P) Q) := by
    change matMul3 (mat3Transpose (so3Unnorm P)) (so3Unnorm Q) = so3Unnorm (quatMul4 (quatConj4 P) Q)
    rw [← so3Unnorm_conj P, ← so3Unnorm_hom (quatConj4 P) Q]
  let C := quatMul4 (quatConj4 P) Q
  have htr2 : mat3Tr (so3Unnorm C) = 4 * C.w * C.w - quatNormSq4 C :=
    poly_eq_of_norm_eq [C.w, C.x, C.y, C.z] so3TracePair.1 so3TracePair.2 rfl
  have hcw : C.w = quatDot4 P Q :=
    poly_eq_of_norm_eq [P.w, P.x, P.y, P.z, Q.w, Q.x, Q.y, Q.z] conjMulW_Pair.1 conjMulW_Pair.2 rfl
  have hcn : quatNormSq4 C = quatNormSq4 P * quatNormSq4 Q := by
    change quatNormSq4 (quatMul4 (quatConj4 P) Q) = quatNormSq4 P * quatNormSq4 Q
    rw [quatNormSq4_mul, quatNormSq4_conj]
  rw [hexp, hfP, hfQ, htr1]
  change 3 * quatNormSq4 P * quatNormSq4 P + 3 * quatNormSq4 Q * quatNormSq4 Q -
      2 * mat3Tr (so3Unnorm C) = _
  rw [htr2, hcw, hcn]
  exact poly_eq_of_norm_eq [quatNormSq4 P, quatNormSq4 Q, quatDot4 P Q] frobBridgePair.1 frobBridgePair.2 rfl

private def frobFinalPair : PExpr × PExpr :=
  let vN := PExpr.var 0; let vC := PExpr.var 1
  (3 * (vN - vN) * (vN - vN) + 8 * (vN * vN - (vN - 2 * vC) * (vN - 2 * vC)),
   32 * vC * (vN - vC))

/-- **Exact `SO(3)` Frobenius Commutator Law**:
    `||R_A R_B - R_B R_A||_F^2 = 32 * crossSq3(A, B) * (||A||^2 ||B||^2 - crossSq3(A, B))`,
    giving `F_cleared = 8 * D * (2 * a * b - D)` for Hurwitz units (`||A||^2 = 4a, ||B||^2 = 4b, crossSq3 = 8D`). -/
theorem t1_so3_frobenius_commutator_exact (A B : Quat4Z) :
    frobSq3 (matSub3 (matMul3 (so3Unnorm A) (so3Unnorm B)) (matMul3 (so3Unnorm B) (so3Unnorm A))) =
      32 * crossSq3 A B * (quatNormSq4 A * quatNormSq4 B - crossSq3 A B) := by
  rw [← so3Unnorm_hom A B, ← so3Unnorm_hom B A]
  rw [frobSq3_so3Unnorm_diff (quatMul4 A B) (quatMul4 B A)]
  rw [quatNormSq4_mul A B, quatNormSq4_mul B A, Int.mul_comm (quatNormSq4 B) (quatNormSq4 A)]
  rw [(t1_hurwitz_group_commutator_trace A B).2]
  exact poly_eq_of_norm_eq [quatNormSq4 A * quatNormSq4 B, crossSq3 A B] frobFinalPair.1 frobFinalPair.2 rfl

private def parityMod16Pair : PExpr × PExpr :=
  (8 * PExpr.var 1 * (2 * PExpr.var 0 - PExpr.var 1),
   16 * (PExpr.var 1 * PExpr.var 0) - 8 * (PExpr.var 1 * PExpr.var 1))

private def evenSqPair : PExpr × PExpr := ((2 * PExpr.var 0) * (2 * PExpr.var 0), 4 * (PExpr.var 0 * PExpr.var 0))
private def oddSqPair  : PExpr × PExpr :=
  ((2 * PExpr.var 0 + 1) * (2 * PExpr.var 0 + 1), 4 * (PExpr.var 0 * PExpr.var 0 + PExpr.var 0) + 1)

/-- **`SO(3)` Parity-Transfer Law**:
    `F_cleared = 8 * D * (2 * ab - D)` satisfies `F_cleared % 16 = (8 * D) % 16` for all `ab, D ∈ Z`. -/
theorem t1_so3_parity_transfer_mod16 (ab D : Int) :
    (8 * D * (2 * ab - D)) % 16 = (8 * D) % 16 := by
  have hexp : 8 * D * (2 * ab - D) = 16 * (D * ab) - 8 * (D * D) :=
    poly_eq_of_norm_eq [ab, D] parityMod16Pair.1 parityMod16Pair.2 rfl
  rw [hexp]
  let q := D / 2
  have hd_par : D % 2 = 0 ∨ D % 2 = 1 := by omega
  rcases hd_par with h0 | h1
  · have h2 : D = 2 * q := by omega
    have hsq : (2 * q) * (2 * q) = 4 * (q * q) :=
      poly_eq_of_norm_eq [q] evenSqPair.1 evenSqPair.2 rfl
    rw [h2, hsq]
    omega
  · have h2 : D = 2 * q + 1 := by omega
    have hsq : (2 * q + 1) * (2 * q + 1) = 4 * (q * q + q) + 1 :=
      poly_eq_of_norm_eq [q] oddSqPair.1 oddSqPair.2 rfl
    rw [h2, hsq]
    omega

/-- **Certified Definite Witnesses (`[]` zero axioms)**:
    1. Odd Hurwitz `(5,3,1,1), (13,5,1,1)`: `D = 1` (`crossSq3 = 8`), `F_cleared = 7048` (`256 * 7048 = 1804288`),
    2. Lipschitz `(4,4,2,0), (12,6,4,0)`: `D = 2` (`crossSq3 = 16`), `F_cleared = 14080`,
    3. Spinor-Hippopede `(i, j)` (`(0,2,0,0), (0,0,2,0)`): `SO(3)`-invisible spin holonomy (`frobSq3 = 0`, `Re C = -16 = 16 * (-1)`). -/
theorem t1_hurwitz_witnesses_and_spin_kernel :
    let hA : Quat4Z := ⟨5, 3, 1, 1⟩
    let hB : Quat4Z := ⟨13, 5, 1, 1⟩
    let lA : Quat4Z := ⟨4, 4, 2, 0⟩
    let lB : Quat4Z := ⟨12, 6, 4, 0⟩
    let iQ : Quat4Z := ⟨0, 2, 0, 0⟩
    let jQ : Quat4Z := ⟨0, 0, 2, 0⟩
    crossSq3 hA hB = 8 ∧
    frobSq3 (matSub3 (matMul3 (so3Unnorm hA) (so3Unnorm hB)) (matMul3 (so3Unnorm hB) (so3Unnorm hA))) = 256 * 7048 ∧
    crossSq3 lA lB = 16 ∧
    frobSq3 (matSub3 (matMul3 (so3Unnorm lA) (so3Unnorm lB)) (matMul3 (so3Unnorm lB) (so3Unnorm lA))) = 256 * 14080 ∧
    (quatMul4 (quatMul4 iQ jQ) (quatMul4 (quatConj4 iQ) (quatConj4 jQ))).w = -16 ∧
    frobSq3 (matSub3 (matMul3 (so3Unnorm iQ) (so3Unnorm jQ)) (matMul3 (so3Unnorm jQ) (so3Unnorm iQ))) = 0 := by
  decide

/-! ### Part 1B: Split `GL_2(Z)` Continued-Fraction Transpose-Pair Side -/

structure Mat2Z where
  p : Int
  q : Int
  r : Int
  s : Int
  deriving Repr, DecidableEq

def mat2Det (M : Mat2Z) : Int := M.p * M.s - M.q * M.r
def mat2Tr  (M : Mat2Z) : Int := M.p + M.s
def mat2Transpose (M : Mat2Z) : Mat2Z := ⟨M.p, M.r, M.q, M.s⟩
def mat2Adj (M : Mat2Z) : Mat2Z := ⟨M.s, -M.q, -M.r, M.p⟩
def mat2Scale (c : Int) (M : Mat2Z) : Mat2Z := ⟨c * M.p, c * M.q, c * M.r, c * M.s⟩

def mat2Mul (A B : Mat2Z) : Mat2Z :=
  ⟨ A.p * B.p + A.q * B.r, A.p * B.q + A.q * B.s
  , A.r * B.p + A.s * B.r, A.r * B.q + A.s * B.s ⟩

def mat2Sub (A B : Mat2Z) : Mat2Z :=
  ⟨A.p - B.p, A.q - B.q, A.r - B.r, A.s - B.s⟩

private def splitFactorPair1 : PExpr × PExpr :=
  let vp := PExpr.var 0; let vq := PExpr.var 1; let vr := PExpr.var 2; let vs := PExpr.var 3
  let dW := vp * vs - vq * vr
  let vt := vp + vs
  let vz := (vp * vp + vq * vq) + (vr * vr + vs * vs)
  let wv00 := vp*vp + vq*vq; let wv01 := vp*vr + vq*vs; let wv10 := vr*vp + vs*vq; let wv11 := vr*vr + vs*vs
  let vw00 := vp*vp + vr*vr; let vw01 := vp*vq + vr*vs; let vw10 := vq*vp + vs*vr; let vw11 := vq*vq + vs*vs
  (frickeDiscE dW dW vt vt vz, (wv00 - vw00) * (wv11 - vw11) - (wv01 - vw01) * (wv10 - vw10))

private def splitFactorPair2 : PExpr × PExpr :=
  let vp := PExpr.var 0; let vq := PExpr.var 1; let vr := PExpr.var 2; let vs := PExpr.var 3
  let wv00 := vp*vp + vq*vq; let wv01 := vp*vr + vq*vs; let wv10 := vr*vp + vs*vq; let wv11 := vr*vr + vs*vs
  let vw00 := vp*vp + vr*vr; let vw01 := vp*vq + vr*vs; let vw10 := vq*vp + vs*vr; let vw11 := vq*vq + vs*vs
  ((wv00 - vw00) * (wv11 - vw11) - (wv01 - vw01) * (wv10 - vw10),
   - (((vp - vs) * (vp - vs) + (vq + vr) * (vq + vr)) * ((vq - vr) * (vq - vr))))

/-- **Split Fricke Transpose Factorization**:
    For every `W = [[p, q], [r, s']] ∈ M_2(Z)` and `V = W^T`, with `detW = p*s' - q*r`,
    `t = tr W`, and `z = tr(W V)`,
    `frickeDisc detW detW t t z = det(W V - V W) = -((p - s')^2 + (q + r)^2) * (q - r)^2`. -/
theorem t1_fricke_split_transpose_factorization (W : Mat2Z) :
    let V := mat2Transpose W
    let detW := mat2Det W
    let t := mat2Tr W
    let z := mat2Tr (mat2Mul W V)
    frickeDisc detW detW t t z = mat2Det (mat2Sub (mat2Mul W V) (mat2Mul V W)) ∧
    mat2Det (mat2Sub (mat2Mul W V) (mat2Mul V W)) =
      - (((W.p - W.s) * (W.p - W.s) + (W.q + W.r) * (W.q + W.r)) * ((W.q - W.r) * (W.q - W.r))) :=
  let env := [W.p, W.q, W.r, W.s]
  ⟨poly_eq_of_norm_eq env splitFactorPair1.1 splitFactorPair1.2 rfl,
   poly_eq_of_norm_eq env splitFactorPair2.1 splitFactorPair2.2 rfl⟩

/-- **Universal Nonpositivity of Split Transpose Fricke Discriminant**:
    `frickeDisc (det W) (det W) (tr W) (tr W) (tr (W W^T)) ≤ 0` for all `W ∈ M_2(Z)`. -/
theorem t1_fricke_split_nonpos (W : Mat2Z) :
    let V := mat2Transpose W
    frickeDisc (mat2Det W) (mat2Det W) (mat2Tr W) (mat2Tr W) (mat2Tr (mat2Mul W V)) ≤ 0 := by
  dsimp only
  have hfac := t1_fricke_split_transpose_factorization W
  dsimp only at hfac
  rw [hfac.1, hfac.2]
  have h1 : 0 ≤ (W.p - W.s) * (W.p - W.s) + (W.q + W.r) * (W.q + W.r) := by
    have hp := int_sq_nonneg (W.p - W.s)
    have hq := int_sq_nonneg (W.q + W.r)
    omega
  have h2 : 0 ≤ (W.q - W.r) * (W.q - W.r) := int_sq_nonneg (W.q - W.r)
  have hprod : 0 ≤ ((W.p - W.s) * (W.p - W.s) + (W.q + W.r) * (W.q + W.r)) * ((W.q - W.r) * (W.q - W.r)) :=
    nonneg_mul_nonneg h1 h2
  omega

/-- **Palindromic Symmetry Vanishing Criterion**:
    Whenever `q + r ≠ 0` (which holds for every non-empty positive CF matrix `W`),
    `frickeDisc (det W) (det W) (tr W) (tr W) (tr (W W^T)) = 0 ↔ W = W^T`. -/
theorem t1_fricke_split_vanishes_iff_symmetric (W : Mat2Z) (hqr : W.q + W.r ≠ 0) :
    frickeDisc (mat2Det W) (mat2Det W) (mat2Tr W) (mat2Tr W) (mat2Tr (mat2Mul W (mat2Transpose W))) = 0 ↔
      W = mat2Transpose W := by
  have hfac := t1_fricke_split_transpose_factorization W
  dsimp only at hfac
  rw [hfac.1, hfac.2]
  constructor
  · intro h0
    have hprod0 : ((W.p - W.s) * (W.p - W.s) + (W.q + W.r) * (W.q + W.r)) * ((W.q - W.r) * (W.q - W.r)) = 0 := by omega
    have hsum_pos : 0 < (W.p - W.s) * (W.p - W.s) + (W.q + W.r) * (W.q + W.r) := by
      have hp := int_sq_nonneg (W.p - W.s)
      have hq := int_sq_nonneg (W.q + W.r)
      have hq_ne : (W.q + W.r) * (W.q + W.r) ≠ 0 := fun hz => hqr ((int_sq_eq_zero_iff _).mp hz)
      omega
    rcases Int.mul_eq_zero.mp hprod0 with hleft | hright
    · omega
    · have hqr_eq : W.q - W.r = 0 := (int_sq_eq_zero_iff (W.q - W.r)).mp hright
      have heq : W.q = W.r := by omega
      cases W; dsimp only at heq; subst heq; rfl
  · intro hsym
    have heq : W.q = W.r := by cases W; injection hsym
    rw [heq]; simp

private def adjProdTrPair : PExpr × PExpr :=
  let vp := PExpr.var 0; let vq := PExpr.var 1; let vr := PExpr.var 2; let vs := PExpr.var 3
  let ps := vp * vs - vq * vr
  let pt := vp + vs
  let pz := (vp*vp + vq*vq) + (vr*vr + vs*vs)
  let wv00 := vp*vp + vq*vq; let wv01 := vp*vr + vq*vs; let wv10 := vr*vp + vs*vq; let wv11 := vr*vr + vs*vs
  let u00 := vs*vs + (-vq)*(-vq); let u01 := vs*(-vr) + (-vq)*vp
  let u10 := (-vr)*vs + vp*(-vq); let u11 := (-vr)*(-vr) + vp*vp
  ((wv00*u00 + wv01*u10) + (wv10*u01 + wv11*u11),
   2 * (ps * ps) - frickeDiscE ps ps pt pt pz)

private def scaleMulTrPair : PExpr × PExpr :=
  let s := PExpr.var 0
  let a00 := PExpr.var 1; let a01 := PExpr.var 2; let a10 := PExpr.var 3; let a11 := PExpr.var 4
  let b00 := PExpr.var 5; let b01 := PExpr.var 6; let b10 := PExpr.var 7; let b11 := PExpr.var 8
  let c00 := PExpr.var 9; let c01 := PExpr.var 10; let c10 := PExpr.var 11; let c11 := PExpr.var 12
  let sb00 := s*b00; let sb01 := s*b01; let sb10 := s*b10; let sb11 := s*b11
  let sc00 := s*c00; let sc01 := s*c01; let sc10 := s*c10; let sc11 := s*c11
  let m1_00 := sb00*sc00 + sb01*sc10; let m1_01 := sb00*sc01 + sb01*sc11
  let m1_10 := sb10*sc00 + sb11*sc10; let m1_11 := sb10*sc01 + sb11*sc11
  let bc00 := b00*c00 + b01*c10; let bc01 := b00*c01 + b01*c11
  let bc10 := b10*c00 + b11*c10; let bc11 := b10*c01 + b11*c11
  ((a00*m1_00 + a01*m1_10) + (a10*m1_01 + a11*m1_11),
   (s * s) * ((a00*bc00 + a01*bc10) + (a10*bc01 + a11*bc11)))

private def overshootPair : PExpr × PExpr :=
  let vs := PExpr.var 0; let vt := PExpr.var 1; let vz := PExpr.var 2
  ((2 * vt * vt + vz * vz - vt * vt * vz - 2) - (2 - frickeDiscE vs vs vt vt vz),
   2 * (1 - vs) * vt * vt + 4 * (vs * vs - 1))

/-- **`GL_2(Z)` Group-Commutator Trace & Naive-`SL_2(Z)` Overshoot Theorem**:
    For any `W ∈ GL_2(Z)` (`(det W)^2 = 1`, `W^{-1} = det(W) * adj(W)`), the group commutator
    `C = W W^T W^{-1} (W^T)^{-1}` satisfies `tr C = 2 - kappa`, and the naive `SL_2(Z)` polynomial
    `2*t^2 + z^2 - t^2*z - 2` overshoots `tr C` by the exact formula `2 * (1 - det W) * t^2`. -/
theorem t1_fricke_split_group_commutator_and_overshoot (W : Mat2Z) (hgl : mat2Det W * mat2Det W = 1) :
    let V := mat2Transpose W
    let s := mat2Det W
    let t := mat2Tr W
    let z := mat2Tr (mat2Mul W V)
    let wInv := mat2Scale s (mat2Adj W)
    let vInv := mat2Scale s (mat2Adj V)
    let C := mat2Mul (mat2Mul W V) (mat2Mul wInv vInv)
    let kappa := frickeDisc s s t t z
    let naiveSL2 := 2 * t * t + z * z - t * t * z - 2
    mat2Tr C = 2 - kappa ∧
    naiveSL2 - mat2Tr C = 2 * (1 - s) * t * t := by
  dsimp only
  let V := mat2Transpose W
  let s := mat2Det W
  let WV := mat2Mul W V
  let AW := mat2Adj W
  let AV := mat2Adj V
  have hsc : mat2Tr (mat2Mul WV (mat2Mul (mat2Scale s AW) (mat2Scale s AV))) =
      (s * s) * mat2Tr (mat2Mul WV (mat2Mul AW AV)) :=
    poly_eq_of_norm_eq
      [s, WV.p, WV.q, WV.r, WV.s, AW.p, AW.q, AW.r, AW.s, AV.p, AV.q, AV.r, AV.s]
      scaleMulTrPair.1 scaleMulTrPair.2 rfl
  have hadj : mat2Tr (mat2Mul WV (mat2Mul AW AV)) =
      2 * (s * s) - frickeDisc s s (mat2Tr W) (mat2Tr W) (mat2Tr WV) :=
    poly_eq_of_norm_eq [W.p, W.q, W.r, W.s] adjProdTrPair.1 adjProdTrPair.2 rfl
  have htr : mat2Tr (mat2Mul WV (mat2Mul (mat2Scale s AW) (mat2Scale s AV))) =
      2 - frickeDisc s s (mat2Tr W) (mat2Tr W) (mat2Tr WV) := by
    rw [hsc, hadj]
    change (mat2Det W * mat2Det W) * (2 * (mat2Det W * mat2Det W) - _) = _
    rw [hgl, Int.one_mul, Int.mul_one]
  refine ⟨htr, ?_⟩
  change (2 * mat2Tr W * mat2Tr W + mat2Tr WV * mat2Tr WV - mat2Tr W * mat2Tr W * mat2Tr WV - 2) -
      mat2Tr (mat2Mul WV (mat2Mul (mat2Scale s AW) (mat2Scale s AV))) = _
  rw [htr]
  have hov : (2 * mat2Tr W * mat2Tr W + mat2Tr WV * mat2Tr WV - mat2Tr W * mat2Tr W * mat2Tr WV - 2) -
      (2 - frickeDisc s s (mat2Tr W) (mat2Tr W) (mat2Tr WV)) =
      2 * (1 - s) * mat2Tr W * mat2Tr W + 4 * (s * s - 1) :=
    poly_eq_of_norm_eq [s, mat2Tr W, mat2Tr WV] overshootPair.1 overshootPair.2 rfl
  rw [hov]
  dsimp only [s]
  rw [hgl]
  omega

/-- Continued-fraction matrix product `∏ Q(a_i)` with `Q(a) = [[a, 1], [1, 0]]`. -/
def cfMatrix : List Int → Mat2Z
  | [] => ⟨1, 0, 0, 1⟩
  | a :: as => mat2Mul ⟨a, 1, 1, 0⟩ (cfMatrix as)

/-- **Certified Split CF Witnesses (`5/3`, `8/3`, `13/8`, and Zu Chongzhi `355/113`, `[]` zero axioms)**. -/
theorem t1_split_cf_witnesses_exact :
    let w53 := cfMatrix [1, 1, 2]
    let w83 := cfMatrix [2, 1, 2]
    let w138 := cfMatrix [1, 1, 1, 1, 2]
    let w355 := cfMatrix [3, 7, 16]
    let kap (W : Mat2Z) := frickeDisc (mat2Det W) (mat2Det W) (mat2Tr W) (mat2Tr W) (mat2Tr (mat2Mul W (mat2Transpose W)))
    let naive (W : Mat2Z) :=
      let t := mat2Tr W; let z := mat2Tr (mat2Mul W (mat2Transpose W))
      2 * t * t + z * z - t * t * z - 2
    kap w53 = -41 ∧ (2 - kap w53) = 43 ∧ naive w53 = 187 ∧ naive w53 - (2 - kap w53) = 144 ∧
    kap w83 = 0 ∧ w83 = mat2Transpose w83 ∧
    kap w138 < 0 ∧
    w355.p = 355 ∧ w355.r = 113 ∧ naive w355 = 1154307627 ∧ (2 - kap w355) ≠ 1154307627 := by
  decide

end S150Pilot1Theorems
