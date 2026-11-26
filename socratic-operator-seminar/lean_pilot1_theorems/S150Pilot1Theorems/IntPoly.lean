/-
  S150Pilot1Theorems/IntPoly.lean

  Pure-Init (`Lean 4.36.0`) zero-`Classical.choice` constructive multivariate `Int`
  polynomial normalizer (`PExpr`, `norm`, `poly_eq_of_norm_eq`) and integer square
  positivity lemmas used across Topics 1, 2, and 3.
-/

namespace S150Pilot1Theorems

/-- Reified multivariate polynomial expression over `Int`. -/
inductive PExpr where
  | const (c : Int)
  | var   (i : Nat)
  | neg   (a : PExpr)
  | add   (a b : PExpr)
  | sub   (a b : PExpr)
  | mul   (a b : PExpr)
  deriving Repr, DecidableEq

instance : Add PExpr := ⟨PExpr.add⟩
instance : Sub PExpr := ⟨PExpr.sub⟩
instance : Mul PExpr := ⟨PExpr.mul⟩
instance : Neg PExpr := ⟨PExpr.neg⟩
instance (n : Nat) : OfNat PExpr n := ⟨PExpr.const (Int.ofNat n)⟩

def lookupVar : List Int → Nat → Int
  | [], _ => 0
  | x :: _, 0 => x
  | _ :: xs, k + 1 => lookupVar xs k

def PExpr.eval (env : List Int) : PExpr → Int
  | .const c => c
  | .var i   => lookupVar env i
  | .neg a   => - (a.eval env)
  | .add a b => a.eval env + b.eval env
  | .sub a b => a.eval env - b.eval env
  | .mul a b => a.eval env * b.eval env

abbrev Monom := List Nat
abbrev Poly  := List (Monom × Int)

def evalMonom (env : List Int) : Monom → Int
  | [] => 1
  | i :: is => lookupVar env i * evalMonom env is

def evalPoly (env : List Int) : Poly → Int
  | [] => 0
  | (m, c) :: rest => c * evalMonom env m + evalPoly env rest

def insertVar (i : Nat) : Monom → Monom
  | [] => [i]
  | j :: js => if Nat.ble i j then i :: j :: js else j :: insertVar i js

def mulMonom : Monom → Monom → Monom
  | [], m2 => m2
  | i :: is, m2 => insertVar i (mulMonom is m2)

def cmpMonom : Monom → Monom → Ordering
  | [], [] => .eq
  | [], _ :: _ => .lt
  | _ :: _, [] => .gt
  | x :: xs, y :: ys =>
    if Nat.blt x y then .lt
    else if Nat.beq x y then cmpMonom xs ys
    else .gt

def intIsZero : Int → Bool
  | .ofNat 0 => true
  | _ => false

def insertTerm (m : Monom) (c : Int) : Poly → Poly
  | [] => if intIsZero c then [] else [(m, c)]
  | (m', c') :: rest =>
    match cmpMonom m m' with
    | .lt => if intIsZero c then (m', c') :: rest else (m, c) :: (m', c') :: rest
    | .eq =>
      let s := c + c'
      if intIsZero s then rest else (m', s) :: rest
    | .gt => (m', c') :: insertTerm m c rest

def addPoly : Poly → Poly → Poly
  | [], q => q
  | (m, c) :: ps, q => insertTerm m c (addPoly ps q)

def negPoly : Poly → Poly
  | [] => []
  | (m, c) :: ps => if intIsZero (-c) then negPoly ps else (m, -c) :: negPoly ps

def mulTermPoly (m : Monom) (c : Int) : Poly → Poly
  | [] => []
  | (m', c') :: qs => insertTerm (mulMonom m m') (c * c') (mulTermPoly m c qs)

def mulPoly : Poly → Poly → Poly
  | [], _ => []
  | (m, c) :: ps, q => addPoly (mulTermPoly m c q) (mulPoly ps q)

def norm : PExpr → Poly
  | .const c => if intIsZero c then [] else [([], c)]
  | .var i   => [([i], 1)]
  | .neg a   => negPoly (norm a)
  | .add a b => addPoly (norm a) (norm b)
  | .sub a b => addPoly (norm a) (negPoly (norm b))
  | .mul a b => mulPoly (norm a) (norm b)

private theorem intIsZero_spec : ∀ c : Int, intIsZero c = true → c = 0
  | .ofNat 0, _ => rfl
  | .ofNat (_ + 1), h => Bool.noConfusion h
  | .negSucc _, h => Bool.noConfusion h

private theorem evalMonom_insertVar (env : List Int) (i : Nat) (m : Monom) :
    evalMonom env (insertVar i m) = lookupVar env i * evalMonom env m := by
  induction m with
  | nil => simp [insertVar, evalMonom]
  | cons j js ih =>
    unfold insertVar
    cases Nat.ble i j
    · simp only [Bool.false_eq_true, ↓reduceIte, evalMonom, ih]
      rw [← Int.mul_assoc, Int.mul_comm (lookupVar env j) (lookupVar env i), Int.mul_assoc]
    · simp only [↓reduceIte, evalMonom]

private theorem evalMonom_mulMonom (env : List Int) (m1 m2 : Monom) :
    evalMonom env (mulMonom m1 m2) = evalMonom env m1 * evalMonom env m2 := by
  induction m1 with
  | nil => simp [mulMonom, evalMonom]
  | cons i is ih =>
    simp only [mulMonom, evalMonom, evalMonom_insertVar, ih, Int.mul_assoc]

private theorem cmpMonom_eq_iff : ∀ m1 m2 : Monom, cmpMonom m1 m2 = .eq → m1 = m2
  | [], [], _ => rfl
  | [], _ :: _, h => by cases h
  | _ :: _, [], h => by cases h
  | x :: xs, y :: ys, h => by
    unfold cmpMonom at h
    cases hlt : Nat.blt x y <;> rw [hlt] at h
    · simp only [Bool.false_eq_true, ↓reduceIte] at h
      cases hbeq : Nat.beq x y <;> rw [hbeq] at h
      · cases h
      · simp only [↓reduceIte] at h
        have hxy : x = y := Nat.eq_of_beq_eq_true hbeq
        rw [hxy, cmpMonom_eq_iff xs ys h]
    · cases h

private theorem evalPoly_insertTerm (env : List Int) (m : Monom) (c : Int) (p : Poly) :
    evalPoly env (insertTerm m c p) = c * evalMonom env m + evalPoly env p := by
  induction p with
  | nil =>
    unfold insertTerm
    cases hz : intIsZero c
    · simp [evalPoly]
    · rw [intIsZero_spec c hz]; simp [evalPoly]
  | cons hd rest ih =>
    rcases hd with ⟨m', c'⟩
    unfold insertTerm
    cases hcmp : cmpMonom m m'
    · cases hz : intIsZero c
      · simp [evalPoly]
      · rw [intIsZero_spec c hz]; simp [evalPoly]
    · dsimp only
      have hm_eq : m = m' := cmpMonom_eq_iff m m' hcmp
      cases hz : intIsZero (c + c')
      · simp only [Bool.false_eq_true, ↓reduceIte, evalPoly, hm_eq]
        rw [Int.add_mul, Int.add_assoc]
      · simp only [↓reduceIte, evalPoly, hm_eq]
        have hs0 : c + c' = 0 := intIsZero_spec (c + c') hz
        rw [← Int.add_assoc, ← Int.add_mul, hs0, Int.zero_mul, Int.zero_add]
    · simp only [evalPoly, ih]
      rw [← Int.add_assoc, Int.add_comm (c' * evalMonom env m') (c * evalMonom env m), Int.add_assoc]

private theorem evalPoly_addPoly (env : List Int) (p q : Poly) :
    evalPoly env (addPoly p q) = evalPoly env p + evalPoly env q := by
  induction p with
  | nil => simp [addPoly, evalPoly]
  | cons hd ps ih =>
    rcases hd with ⟨m, c⟩
    simp only [addPoly, evalPoly_insertTerm, ih, evalPoly, Int.add_assoc]

private theorem evalPoly_negPoly (env : List Int) (p : Poly) :
    evalPoly env (negPoly p) = - evalPoly env p := by
  induction p with
  | nil => simp [negPoly, evalPoly]
  | cons hd ps ih =>
    rcases hd with ⟨m, c⟩
    unfold negPoly
    cases hz : intIsZero (-c)
    · simp only [Bool.false_eq_true, ↓reduceIte, evalPoly, ih, Int.neg_mul, Int.neg_add]
    · simp only [↓reduceIte, evalPoly, ih]
      have hc0 : -c = 0 := intIsZero_spec (-c) hz
      rw [Int.neg_add, ← Int.neg_mul, hc0, Int.zero_mul, Int.zero_add]

private theorem evalPoly_mulTermPoly (env : List Int) (m : Monom) (c : Int) (q : Poly) :
    evalPoly env (mulTermPoly m c q) = (c * evalMonom env m) * evalPoly env q := by
  induction q with
  | nil => simp [mulTermPoly, evalPoly]
  | cons hd qs ih =>
    rcases hd with ⟨m', c'⟩
    simp only [mulTermPoly, evalPoly_insertTerm, evalMonom_mulMonom, ih, evalPoly, Int.mul_add]
    have hmul : c * c' * (evalMonom env m * evalMonom env m') = c * evalMonom env m * (c' * evalMonom env m') := by
      rw [Int.mul_assoc c c', ← Int.mul_assoc c' (evalMonom env m), Int.mul_comm c' (evalMonom env m),
          Int.mul_assoc (evalMonom env m), ← Int.mul_assoc]
    rw [hmul]

private theorem evalPoly_mulPoly (env : List Int) (p q : Poly) :
    evalPoly env (mulPoly p q) = evalPoly env p * evalPoly env q := by
  induction p with
  | nil => simp [mulPoly, evalPoly]
  | cons hd ps ih =>
    rcases hd with ⟨m, c⟩
    simp only [mulPoly, evalPoly_addPoly, evalPoly_mulTermPoly, ih, evalPoly, Int.add_mul]

/-- Sound sparse normalizer (`[propext]` only). -/
theorem evalPoly_norm (env : List Int) (e : PExpr) :
    evalPoly env (norm e) = e.eval env := by
  induction e with
  | const c =>
    unfold norm
    cases hz : intIsZero c
    · simp [evalPoly, evalMonom, PExpr.eval]
    · rw [intIsZero_spec c hz]; simp [evalPoly, PExpr.eval]
  | var i => simp [norm, evalPoly, evalMonom, PExpr.eval]
  | neg a ih => simp [norm, evalPoly_negPoly, ih, PExpr.eval]
  | add a b iha ihb => simp [norm, evalPoly_addPoly, iha, ihb, PExpr.eval]
  | sub a b iha ihb => simp [norm, evalPoly_addPoly, evalPoly_negPoly, iha, ihb, PExpr.eval, Int.sub_eq_add_neg]
  | mul a b iha ihb => simp [norm, evalPoly_mulPoly, iha, ihb, PExpr.eval]

/-- Reflective multivariate `Int` ring solver (`[propext]` only). -/
theorem poly_eq_of_norm_eq (env : List Int) (lhs rhs : PExpr) (h : norm lhs = norm rhs) :
    lhs.eval env = rhs.eval env := by
  rw [← evalPoly_norm env lhs, h, evalPoly_norm env rhs]

/-- Constructive square nonnegativity over `Int`. -/
theorem int_sq_nonneg (x : Int) : 0 ≤ x * x := by
  cases x with
  | ofNat n => exact Int.ofNat_le.mpr (Nat.zero_le (n * n))
  | negSucc n =>
    have h : Int.negSucc n * Int.negSucc n = Int.ofNat ((n + 1) * (n + 1)) := rfl
    rw [h]
    exact Int.ofNat_le.mpr (Nat.zero_le _)

/-- Constructive `x * x = 0 ↔ x = 0` over `Int`. -/
theorem int_sq_eq_zero_iff (x : Int) : x * x = 0 ↔ x = 0 := by
  constructor
  · intro h
    cases x with
    | ofNat n =>
      cases n with
      | zero => rfl
      | succ k =>
        have hpos : 0 < (k + 1) * (k + 1) := Nat.mul_pos (Nat.succ_pos k) (Nat.succ_pos k)
        have heq : Int.ofNat (k + 1) * Int.ofNat (k + 1) = Int.ofNat ((k + 1) * (k + 1)) := rfl
        rw [heq] at h
        have hposZ : (0 : Int) < Int.ofNat ((k + 1) * (k + 1)) := Int.ofNat_lt.mpr hpos
        omega
    | negSucc k =>
      have hpos : 0 < (k + 1) * (k + 1) := Nat.mul_pos (Nat.succ_pos k) (Nat.succ_pos k)
      have heq : Int.negSucc k * Int.negSucc k = Int.ofNat ((k + 1) * (k + 1)) := rfl
      rw [heq] at h
      have hposZ : (0 : Int) < Int.ofNat ((k + 1) * (k + 1)) := Int.ofNat_lt.mpr hpos
      omega
  · intro h; rw [h]; rfl

/-- Sum of two integer squares vanishes iff both terms vanish. -/
theorem sum_two_sq_eq_zero_iff (a b : Int) : a * a + b * b = 0 ↔ a = 0 ∧ b = 0 := by
  constructor
  · intro h
    have ha : 0 ≤ a * a := int_sq_nonneg a
    have hb : 0 ≤ b * b := int_sq_nonneg b
    have ha0 : a * a = 0 := by omega
    have hb0 : b * b = 0 := by omega
    exact ⟨(int_sq_eq_zero_iff a).mp ha0, (int_sq_eq_zero_iff b).mp hb0⟩
  · rintro ⟨rfl, rfl⟩; rfl

/-- Product of two nonnegative integers is nonnegative. -/
theorem nonneg_mul_nonneg {a b : Int} (ha : 0 ≤ a) (hb : 0 ≤ b) : 0 ≤ a * b :=
  Int.mul_nonneg ha hb

end S150Pilot1Theorems
