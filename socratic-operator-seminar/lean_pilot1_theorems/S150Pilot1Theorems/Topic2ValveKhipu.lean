/-
  S150Pilot1Theorems/Topic2ValveKhipu.lean

  Topic 2 (`aletheion`) — `CRTVALVESEAL` Bounded-Chatter Total-Variation
  Hysteresis Theorem, Khipu Hierarchical Tree-Sum Conservation & Single-Cord
  Tamper Detection, and Half-Split Chiral (`a + 3*b`) Tree Checksum Sensitivity.
-/

import S150Pilot1Theorems.IntPoly

namespace S150Pilot1Theorems

/-! ### Part 2A: Inclusive Hysteresis Automaton & Universal Bounded-Chatter TV Law -/

def intAbs (x : Int) : Int := if x ≥ 0 then x else -x

def intMax0 (x : Int) : Int := if x ≥ 0 then x else 0

/-- Inclusive two-threshold hysteresis step (`v ≥ hi -> true`, `v ≤ lo -> false`, else hold). -/
def valveStep (lo hi : Int) (cur : Bool) (v : Int) : Bool :=
  if v ≥ hi then true
  else if v ≤ lo then false
  else cur

/-- Count state transitions along stream `xs` starting from `cur`. -/
def valveFlips (lo hi : Int) (cur : Bool) : List Int → Nat
  | [] => 0
  | x :: xs =>
    let nxt := valveStep lo hi cur x
    (if nxt == cur then 0 else 1) + valveFlips lo hi nxt xs

def hiHits (lo hi : Int) : List Int → Nat
  | [] => 0
  | x :: xs => (if x ≥ hi then 1 else 0) + hiHits lo hi xs

def loHits (lo hi : Int) : List Int → Nat
  | [] => 0
  | x :: xs => (if ¬(x ≥ hi) ∧ x ≤ lo then 1 else 0) + loHits lo hi xs

/-- Total variation `∑ |x_{k+1} - x_k|` of an integer (or common-denominator rational) stream. -/
def totalVariation : List Int → Int
  | [] => 0
  | [_] => 0
  | x :: y :: rest => intAbs (y - x) + totalVariation (y :: rest)

/-- Anchored hysteresis potential `Φ(s, x)`: deficit from threshold `hi` (if `s = true`) or `lo` (if `s = false`). -/
private def valvePotential (lo hi : Int) (s : Bool) (x : Int) : Int :=
  if s then intMax0 (hi - x) else intMax0 (x - lo)

private theorem valvePotential_nonneg (lo hi : Int) (s : Bool) (x : Int) :
    0 ≤ valvePotential lo hi s x := by
  unfold valvePotential intMax0
  cases s <;> split <;> omega

private theorem step_anchored_potential_ineq {lo hi : Int} (_hband : lo < hi)
    (s : Bool) (x y : Int) :
    let s' := valveStep lo hi s y
    (if s' == s then (0 : Int) else hi - lo) + valvePotential lo hi s' y - valvePotential lo hi s x ≤
      intAbs (y - x) := by
  dsimp only
  unfold valveStep valvePotential intMax0 intAbs
  cases s
  · -- s = false
    rcases Decidable.em (y ≥ hi) with hy_hi | hy_hi
    · simp only [hy_hi, Bool.false_eq_true, ↓reduceIte]; dsimp [BEq.beq]
      repeat (first | split | omega)
    · simp only [hy_hi, Bool.false_eq_true, ↓reduceIte]
      rcases Decidable.em (y ≤ lo) with hy_lo | hy_lo
      · simp only [hy_lo, Bool.false_eq_true, ↓reduceIte]; dsimp [BEq.beq]
        repeat (first | split | omega)
      · simp only [hy_lo, Bool.false_eq_true, ↓reduceIte]; dsimp [BEq.beq]
        repeat (first | split | omega)
  · -- s = true
    rcases Decidable.em (y ≥ hi) with hy_hi | hy_hi
    · simp only [hy_hi, ↓reduceIte]; dsimp [BEq.beq]
      repeat (first | split | omega)
    · simp only [hy_hi, ↓reduceIte]
      rcases Decidable.em (y ≤ lo) with hy_lo | hy_lo
      · simp only [hy_lo, Bool.false_eq_true, ↓reduceIte]; dsimp [BEq.beq]
        repeat (first | split | omega)
      · simp only [hy_lo, ↓reduceIte]; dsimp [BEq.beq]
        repeat (first | split | omega)

/-- Telescoping bound once anchored at sample `x` in state `s`. -/
private theorem valveFlips_anchored_bound {lo hi : Int} (hband : lo < hi) :
    ∀ (ys : List Int) (s : Bool) (x : Int),
      Int.ofNat (valveFlips lo hi s ys) * (hi - lo) - valvePotential lo hi s x ≤
        totalVariation (x :: ys)
  | [], s, x => by
    have hp := valvePotential_nonneg lo hi s x
    have hz : Int.ofNat (valveFlips lo hi s []) * (hi - lo) = 0 := Int.zero_mul (hi - lo)
    rw [hz]
    simp only [totalVariation]
    omega
  | y :: rest, s, x => by
    let s' := valveStep lo hi s y
    have hstep : (if s' == s then (0 : Int) else hi - lo) + valvePotential lo hi s' y -
        valvePotential lo hi s x ≤ intAbs (y - x) := step_anchored_potential_ineq hband s x y
    have ih := valveFlips_anchored_bound hband rest s' y
    simp only [valveFlips, totalVariation]
    change Int.ofNat ((if s' == s then 0 else 1) + valveFlips lo hi s' rest) * (hi - lo) -
        valvePotential lo hi s x ≤ intAbs (y - x) + totalVariation (y :: rest)
    cases hbeq : (s' == s)
    · rw [hbeq] at hstep
      simp only [Bool.false_eq_true, ↓reduceIte] at hstep ⊢
      have hadd : Int.ofNat (1 + valveFlips lo hi s' rest) = 1 + Int.ofNat (valveFlips lo hi s' rest) := rfl
      rw [hadd, Int.add_mul, Int.one_mul]
      omega
    · rw [hbeq] at hstep
      simp only [↓reduceIte, Nat.zero_add] at hstep ⊢
      omega

private theorem first_flip_zero_potential {lo hi : Int} (_hband : lo < hi)
    (cur : Bool) (x : Int) (hflip : (valveStep lo hi cur x == cur) = false) :
    valvePotential lo hi (valveStep lo hi cur x) x = 0 := by
  unfold valveStep at hflip ⊢
  unfold valvePotential intMax0
  cases cur
  · rcases Decidable.em (x ≥ hi) with hx_hi | hx_hi
    · simp only [hx_hi, ↓reduceIte]
      split <;> omega
    · simp only [hx_hi, ↓reduceIte] at hflip
      rcases Decidable.em (x ≤ lo) with hx_lo | hx_lo <;> simp [hx_lo] at hflip
  · rcases Decidable.em (x ≥ hi) with hx_hi | hx_hi
    · simp [hx_hi] at hflip
    · simp only [hx_hi, ↓reduceIte] at hflip ⊢
      rcases Decidable.em (x ≤ lo) with hx_lo | hx_lo
      · simp only [hx_lo, Bool.false_eq_true, ↓reduceIte]
        split <;> omega
      · simp [hx_lo] at hflip

private theorem totalVariation_nonneg : ∀ xs : List Int, 0 ≤ totalVariation xs
  | [] => by simp [totalVariation]
  | [_] => by simp [totalVariation]
  | x :: y :: rest => by
    have habs : 0 ≤ intAbs (y - x) := by unfold intAbs; split <;> omega
    have ih := totalVariation_nonneg (y :: rest)
    simp only [totalVariation]
    omega

/-- **Universal Bounded-Chatter Total-Variation Theorem (`(F - 1) * (hi - lo) ≤ TV`)**:
    For every deadband `lo < hi`, initial state `init`, and stream `xs : List Int`,
    `(Int.ofNat (valveFlips lo hi init xs) - 1) * (hi - lo) ≤ totalVariation xs`. -/
theorem t2_valve_bounded_chatter_tv_universal {lo hi : Int} (hband : lo < hi)
    (init : Bool) (xs : List Int) :
    (Int.ofNat (valveFlips lo hi init xs) - 1) * (hi - lo) ≤ totalVariation xs := by
  induction xs generalizing init with
  | nil =>
    have hz : (Int.ofNat (valveFlips lo hi init []) - 1) * (hi - lo) = -(hi - lo) := by
      change ((0 : Int) - 1) * (hi - lo) = -(hi - lo)
      omega
    rw [hz]
    simp only [totalVariation]
    omega
  | cons x rest ih =>
    simp only [valveFlips]
    let nxt := valveStep lo hi init x
    change (Int.ofNat ((if nxt == init then 0 else 1) + valveFlips lo hi nxt rest) - 1) * (hi - lo) ≤
      totalVariation (x :: rest)
    cases hbeq : (nxt == init)
    · simp only [Bool.false_eq_true, ↓reduceIte]
      have hadd : Int.ofNat (1 + valveFlips lo hi nxt rest) = 1 + Int.ofNat (valveFlips lo hi nxt rest) := rfl
      rw [hadd]
      have hsub : (1 + Int.ofNat (valveFlips lo hi nxt rest)) - 1 = Int.ofNat (valveFlips lo hi nxt rest) := by omega
      rw [hsub]
      have hp0 : valvePotential lo hi nxt x = 0 := first_flip_zero_potential hband init x hbeq
      have hanch := valveFlips_anchored_bound hband rest nxt x
      rw [hp0] at hanch
      omega
    · simp only [↓reduceIte, Nat.zero_add]
      have ih_rest := ih nxt
      cases rest with
      | nil =>
        have htv0 : totalVariation [x] = totalVariation [] := rfl
        rw [htv0]
        exact ih_rest
      | cons y ys =>
        have habs : 0 ≤ intAbs (y - x) := by unfold intAbs; split <;> omega
        simp only [totalVariation]
        omega

/-- **Sub-Deadband Zero-Chatter Corollary**:
    Whenever `totalVariation xs < hi - lo`, the hysteresis valve transitions at most once
    (`valveFlips ≤ 1`, i.e., zero back-and-forth chatter). -/
theorem t2_valve_zero_chatter_when_tv_lt_band {lo hi : Int} (hband : lo < hi)
    (init : Bool) (xs : List Int) (htv : totalVariation xs < hi - lo) :
    valveFlips lo hi init xs ≤ 1 := by
  have hmain := t2_valve_bounded_chatter_tv_universal hband init xs
  rcases Decidable.em (valveFlips lo hi init xs ≤ 1) with hle | hle
  · exact hle
  · have hge2_nat : 2 ≤ valveFlips lo hi init xs := by omega
    have hge2 : (2 : Int) ≤ Int.ofNat (valveFlips lo hi init xs) := Int.ofNat_le.mpr hge2_nat
    have hmul : 1 * (hi - lo) ≤ (Int.ofNat (valveFlips lo hi init xs) - 1) * (hi - lo) :=
      Int.mul_le_mul_of_nonneg_right (by omega) (by omega)
    omega

/-- **Strict Deadband Interior Zero-Flip Law**:
    If every sample satisfies `lo < x ∧ x < hi`, `valveFlips lo hi init xs = 0`. -/
theorem t2_valve_strict_deadband_zero_flips (lo hi : Int) (init : Bool) (xs : List Int)
    (hin : ∀ x ∈ xs, lo < x ∧ x < hi) :
    valveFlips lo hi init xs = 0 := by
  induction xs generalizing init with
  | nil => rfl
  | cons x rest ih =>
    have hx := hin x (.head _)
    have hstep : valveStep lo hi init x = init := by
      unfold valveStep
      have h1 : ¬(x ≥ hi) := by omega
      have h2 : ¬(x ≤ lo) := by omega
      simp [h1, h2]
    simp only [valveFlips, hstep, beq_self_eq_true, ↓reduceIte, Nat.zero_add]
    exact ih init (fun y hy => hin y (.tail _ hy))

/-- **Upper/Lower Threshold Hit Bound (`F ≤ H + L`)**. -/
theorem t2_valve_flips_le_hi_plus_lo_hits (lo hi : Int) (init : Bool) (xs : List Int) :
    valveFlips lo hi init xs ≤ hiHits lo hi xs + loHits lo hi xs := by
  induction xs generalizing init with
  | nil => simp [valveFlips, hiHits, loHits]
  | cons x rest ih =>
    simp only [valveFlips, hiHits, loHits]
    unfold valveStep
    rcases Decidable.em (x ≥ hi) with h1 | h1
    · simp only [h1, ↓reduceIte, not_true_eq_false, false_and]
      have ih' := ih true
      cases init <;> dsimp [BEq.beq] <;> omega
    · simp only [h1, ↓reduceIte, not_false_eq_true, true_and]
      rcases Decidable.em (x ≤ lo) with h2 | h2
      · simp only [h2, ↓reduceIte]
        have ih' := ih false
        cases init <;> dsimp [BEq.beq] <;> omega
      · simp only [h2, ↓reduceIte, beq_self_eq_true]
        have ih' := ih init
        omega

/-! ### Part 2B: Khipu Hierarchical Tree-Sum Conservation & Chiral (`a + 3*b`) Checksum -/

inductive KhipuTree where
  | cord (val : Int)
  | branch (left right : KhipuTree)
  deriving Repr, DecidableEq

def khipuRootSum : KhipuTree → Int
  | .cord v => v
  | .branch l r => khipuRootSum l + khipuRootSum r

def khipuLeaves : KhipuTree → List Int
  | .cord v => [v]
  | .branch l r => khipuLeaves l ++ khipuLeaves r

def listSumInt : List Int → Int
  | [] => 0
  | x :: xs => x + listSumInt xs

private theorem listSumInt_append (xs ys : List Int) :
    listSumInt (xs ++ ys) = listSumInt xs + listSumInt ys := by
  induction xs with
  | nil => simp [listSumInt]
  | cons x rest ih => simp only [List.cons_append, listSumInt, ih]; omega

/-- **Khipu Hierarchical Tree-Sum Conservation**:
    Every hierarchical binary Khipu knot tree evaluates at its top cord to the exact sum of its pendant cords. -/
theorem t2_khipu_tree_sum_conservation (t : KhipuTree) :
    khipuRootSum t = listSumInt (khipuLeaves t) := by
  induction t with
  | cord v => simp [khipuRootSum, khipuLeaves, listSumInt]
  | branch l r ihl ihr =>
    simp only [khipuRootSum, khipuLeaves, listSumInt_append, ihl, ihr]

inductive CordPath where
  | here
  | goLeft  (p : CordPath)
  | goRight (p : CordPath)
  deriving Repr, DecidableEq

def tamperKhipuAt (delta : Int) : KhipuTree → CordPath → KhipuTree
  | .cord v, _ => .cord (v + delta)
  | .branch l r, .here => .branch (tamperKhipuAt delta l .here) r
  | .branch l r, .goLeft p => .branch (tamperKhipuAt delta l p) r
  | .branch l r, .goRight p => .branch l (tamperKhipuAt delta r p)

/-- **Khipu Single-Cord Tamper Detection**:
    Perturbing any single pendant cord along path `p` by `delta ≠ 0` shifts `khipuRootSum`
    by exactly `+ delta`, guaranteeing `khipuRootSum (tamperKhipuAt delta t p) ≠ khipuRootSum t`. -/
theorem t2_khipu_single_cord_tamper_detected (t : KhipuTree) (p : CordPath) (delta : Int)
    (hdelta : delta ≠ 0) :
    khipuRootSum (tamperKhipuAt delta t p) = khipuRootSum t + delta ∧
    khipuRootSum (tamperKhipuAt delta t p) ≠ khipuRootSum t := by
  have hshift : ∀ (tr : KhipuTree) (pt : CordPath),
      khipuRootSum (tamperKhipuAt delta tr pt) = khipuRootSum tr + delta := by
    intro tr
    induction tr with
    | cord v => intro _; simp [tamperKhipuAt, khipuRootSum]
    | branch l r ihl ihr =>
      intro pt
      cases pt with
      | here => simp only [tamperKhipuAt, khipuRootSum, ihl .here]; omega
      | goLeft pl => simp only [tamperKhipuAt, khipuRootSum, ihl pl]; omega
      | goRight pr => simp only [tamperKhipuAt, khipuRootSum, ihr pr]; omega
  have hs := hshift t p
  exact ⟨hs, by omega⟩

/-- Asymmetric chiral tree checksum (`left + 3 * right`) from the Topic-2 synthesis. -/
def chiralChecksum : KhipuTree → Int
  | .cord v => v
  | .branch l r => chiralChecksum l + 3 * chiralChecksum r

def chiralRightDepth : KhipuTree → CordPath → Nat
  | .cord _, _ => 0
  | .branch l _, .here => chiralRightDepth l .here
  | .branch l _, .goLeft p => chiralRightDepth l p
  | .branch _ r, .goRight p => chiralRightDepth r p + 1

def pow3 : Nat → Int
  | 0 => 1
  | k + 1 => 3 * pow3 k

private theorem pow3_pos : ∀ k : Nat, 0 < pow3 k
  | 0 => by decide
  | k + 1 => by have ih := pow3_pos k; simp only [pow3]; omega

/-- **Chiral (`a + 3*b`) Checksum Single-Cord & Adjacent-Transposition Detection**:
    1. Any single-cord edit `delta ≠ 0` shifts `chiralChecksum` by `3^d * delta ≠ 0`, and
    2. Swapping unequal sibling branches `l, r` (`chiralChecksum l ≠ chiralChecksum r`) changes
       `chiralChecksum` by `2 * (chiralChecksum l - chiralChecksum r) ≠ 0` (unlike unweighted addition). -/
theorem t2_chiral_checksum_detects_single_and_swap (t l r : KhipuTree) (p : CordPath)
    (delta : Int) (hdelta : delta ≠ 0) (hne : chiralChecksum l ≠ chiralChecksum r) :
    chiralChecksum (tamperKhipuAt delta t p) = chiralChecksum t + pow3 (chiralRightDepth t p) * delta ∧
    chiralChecksum (tamperKhipuAt delta t p) ≠ chiralChecksum t ∧
    chiralChecksum (.branch l r) ≠ chiralChecksum (.branch r l) := by
  have hshift : ∀ (tr : KhipuTree) (pt : CordPath),
      chiralChecksum (tamperKhipuAt delta tr pt) = chiralChecksum tr + pow3 (chiralRightDepth tr pt) * delta := by
    intro tr
    induction tr with
    | cord v => intro _; simp [tamperKhipuAt, chiralChecksum, chiralRightDepth, pow3]
    | branch bl br ihl ihr =>
      intro pt
      cases pt with
      | here => simp only [tamperKhipuAt, chiralChecksum, chiralRightDepth, ihl .here]; omega
      | goLeft pl => simp only [tamperKhipuAt, chiralChecksum, chiralRightDepth, ihl pl]; omega
      | goRight pr =>
        simp only [tamperKhipuAt, chiralChecksum, chiralRightDepth, ihr pr, pow3]
        rw [Int.mul_add, ← Int.mul_assoc 3 (pow3 (chiralRightDepth br pr)) delta]
        omega
  have hs := hshift t p
  have hp3 := pow3_pos (chiralRightDepth t p)
  have hprod_ne : pow3 (chiralRightDepth t p) * delta ≠ 0 := by
    intro hz
    rcases Int.mul_eq_zero.mp hz with h0 | h0 <;> omega
  refine ⟨hs, ?_, ?_⟩
  · omega
  · simp only [chiralChecksum]; omega

/-- **General Non-Coprime CRT Pairwise Compatibility Necessity**:
    Whenever `x = r1 + k1 * m1` and `x = r2 + k2 * m2` with `d ∣ m1` and `d ∣ m2`, `d ∣ (r1 - r2)`. -/
theorem t2_crt_two_moduli_necessity (x r1 r2 m1 m2 k1 k2 d : Int)
    (hx1 : x = r1 + k1 * m1) (hx2 : x = r2 + k2 * m2)
    (hd1 : d ∣ m1) (hd2 : d ∣ m2) :
    d ∣ (r1 - r2) := by
  rcases hd1 with ⟨u1, rfl⟩
  rcases hd2 with ⟨u2, rfl⟩
  refine ⟨k2 * u2 - k1 * u1, ?_⟩
  have hdiff : r1 - r2 = k2 * (d * u2) - k1 * (d * u1) := by omega
  rw [hdiff]
  exact poly_eq_of_norm_eq [d, k1, k2, u1, u2]
    (PExpr.var 2 * (PExpr.var 0 * PExpr.var 4) - PExpr.var 1 * (PExpr.var 0 * PExpr.var 3))
    (PExpr.var 0 * (PExpr.var 2 * PExpr.var 4 - PExpr.var 1 * PExpr.var 3)) rfl

/-- **Certified Topic-2 `CRTVALVESEAL` Witnesses (`[]` zero axioms)**:
    Verifies the 3 seminar streams (`c0`: `flips=2, tv=6, root=15`; `c2`: `flips=2, tv=10, root=13`;
    `c7` tight band scaled by `×6`: `flips=4, 6*tv=38, leaves=[3,2,5,2,3], root=123`). -/
theorem t2_seminar_crt_valve_seal_witnesses :
    let s0 := [3, -1, 1]
    let t0 : KhipuTree := .branch (.cord (2 * 1 + 1)) (.cord (2 * 2 + 0))
    let s2 := [4, 2, 5, 0]
    let t2 : KhipuTree := .branch (.cord (2 * 3 + 1)) (.cord (2 * 1 + 0))
    let s7_x6 := [6, 0, 12, 6, 2, 12]
    let t7 : KhipuTree :=
      .branch (.branch (.cord 3) (.cord 2)) (.branch (.cord 5) (.branch (.cord 2) (.cord 3)))
    valveFlips 0 2 false s0 = 2 ∧ totalVariation s0 = 6 ∧ chiralChecksum t0 = 15 ∧
    valveFlips 1 3 false s2 = 2 ∧ totalVariation s2 = 10 ∧ chiralChecksum t2 = 13 ∧
    valveFlips 3 9 true s7_x6 = 4 ∧ totalVariation s7_x6 = 38 ∧ chiralChecksum t7 = 123 := by
  decide

end S150Pilot1Theorems
