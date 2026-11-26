# `S150Pilot1Theorems`: Pure-`Init` `Lean 4.36.0` Formalization of the 3 Unified *Bayt al-Ḥikma S³* Seminar Theorems

Zero-Mathlib, zero-`Classical.choice`, zero-`bv_decide`, zero-`native_decide`, zero-`sorryAx` constructive kernel formalization (`leanprover/lean4:v4.36.0`, `packages: []`) of the three unified Pilot-1 theorems from the trans-historical Socratic seminar, paired with a self-bound pure-$\mathbb{Q}/\mathbb{Z}$ verifier and negative-control suite.

## Formalized Theorem Inventory (`36` Public Theorems)

| Module | Theorems | Axiom Profile | Core Formalized Statements |
|---|---:|---|---|
| `S150Pilot1Theorems/IntPoly.lean` | `6` | `4` `[propext]`, `2` `[propext, Quot.sound]` | Sound sparse multivariate `Int` polynomial normalizer (`evalPoly_norm`, `poly_eq_of_norm_eq`) + constructive integer square nonnegativity & vanishing (`int_sq_nonneg`, `int_sq_eq_zero_iff`, `sum_two_sq_eq_zero_iff`, `nonneg_mul_nonneg`). |
| `S150Pilot1Theorems/Topic1FrickeCayley.lean` | `11` | `2` `[]`, `5` `[propext]`, `4` `[propext, Quot.sound]` | Universal Fricke–Cayley discriminant $\kappa(a,b,x,y,z) = 4ab - bx^2 - ay^2 - z^2 + xyz$; doubled-Hurwitz $\times 16$ homogeneity; definite quaternion commutator identity $\kappa = \|AB - BA\|^2 = 4\|A_{\mathrm{vec}}\times B_{\mathrm{vec}}\|^2$; multiplicative group-commutator scalar law $\operatorname{Re}(AB\bar{A}\bar{B}) = \|A\|^2\|B\|^2 - 2\|A_{\mathrm{vec}}\times B_{\mathrm{vec}}\|^2$; exact $SO(3)$ Frobenius commutator law $\|R_A R_B - R_B R_A\|_F^2 = 32 C (\|A\|^2\|B\|^2 - C)$ & mod-16 parity transfer $F_{\mathrm{cleared}} \equiv 8D \pmod{16}$; Spinor-Hippopede $(i, j)$ $SO(3)$-invisible kernel; split $GL_2(\mathbb{Z})$ transpose factorization $\kappa = -[(p-s')^2 + (q+r)^2](q-r)^2 \le 0$; palindromic vanishing iff $W = W^T$; naive-$SL_2(\mathbb{Z})$ overshoot $2(1-s)t^2$; exact CF witnesses (`5/3`, `8/3`, `13/8`, `355/113`). |
| `S150Pilot1Theorems/Topic2ValveKhipu.lean` | `9` | `1` `[]`, `8` `[propext, Quot.sound]` | Universal inclusive two-threshold hysteresis bounded-chatter total-variation theorem $(F - 1)(\mathrm{hi} - \mathrm{lo}) \le \mathrm{TV}$; sub-deadband zero-chatter guarantee ($\mathrm{TV} < \mathrm{hi} - \mathrm{lo} \implies F \le 1$); strict deadband interior zero-flip law; threshold-hit bound $F \le H + L$; Khipu hierarchical tree-sum conservation & single-cord tamper detection ($\Delta \ne 0$); chiral `left + 3 * right` single-cord ($3^d \Delta \ne 0$) & sibling-swap detection; non-coprime CRT pairwise necessity; certified seminar witnesses (`root = 15, 13, 123`). |
| `S150Pilot1Theorems/Topic3SchurWittFold.lean` | `10` | `1` `[]`, `3` `[propext]`, `6` `[propext, Quot.sound]` | Fraction-free $2\times 2$ & $3\times 3$ block Schur congruences over $\mathbb{Z}$; $GL(\mathbb{Z})$ canonical shear iff $a \mid b$ + converse counterexample `[[4,2],[2,1]]`; constructive irrationality of $\sqrt{2}$ ($m^2 \ne 2k^2$); bidirectional $1\times 1$ block-drop rational congruence iff $a(ad-b^2)d$ is a nonzero integer square + `[[3,3],[3,4]]` witness (`Q = [[1,-2],[0,2]]`) & universal $GL_2(\mathbb{Q})$ obstruction on `[[2,1],[1,1]]`; $GF(2)$ invertibility iff $\det A \equiv 1 \pmod 2$ + universal even-diagonal Schur preservation; $(2,3)$ doubled-coordinate mirror billiard 24-step cycle & unimodular Euclid refutation. |

## Verification Commands

```bash
# Offline static + pure-Q certificate check (fast, deterministic)
python3 -I -B verify_s150_lean_theorems.py --check

# Full cold Lean 4.36.0 sandbox build + leanchecker --fresh + AxiomAudit replay
python3 -I -B verify_s150_lean_theorems.py --check --live-lean

# Negative-control & tamper-rejection unit test suite
python3 -I -B test_verify_s150_lean_theorems_r5.py -v
```
