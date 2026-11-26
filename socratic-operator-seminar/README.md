# *Bayt al-Ḥikma S³*: Trans-Historical Socratic Operator Seminar, 5-Arm Variation Ablation & Pure-`Init` Lean 4 Formalization

A self-contained, 100%-executable pure-$\mathbb{Z}/\mathbb{Q}$ and pure-`Init` `Lean 4.36.0` study demonstrating how trans-historical exact mathematical operators compose, refute, and repair one another across multi-round refereed Socratic seminars — culminating in **36 constructive Lean 4 kernel-verified theorems** and a **105-turn matched-budget 5-arm variation ablation**.

---

## 1. Architecture & Four Verified Pillars

All artifacts live strictly additively under `socratic-operator-seminar/` with zero external Python dependencies and zero external Lean dependencies (`packages: []`):

1. **Executable Socratic Seminar Harness (`socratic_operator_seminar.py`):**
   - Enforces a strict 4-field structured turn schema (`corpus_anchor`, `composition_or_challenge`, `executable_conjecture`, `target_frontier`) plus mandatory `epistemic_web_interpositions` for Chair `SEAT-0`.
   - Rejects prose-only turns, empty specifications, trivial constant oracles, float literals, bare asserts, and unsafe AST constructs before running every conjecture in an isolated `python3 -I -B` pure-`int`/`Fraction` subprocess referee.
   - Tracks causal DAG depth, counterexample repairs, cross-seat compositions, and bidirectional chair-peer pollination (`historical -> SEAT-0` and `SEAT-0 -> historical`), sealing every transcript with canonical `transcript_sha256`.
   - Ships deterministic offline dossiers (`dossiers/*.json`) across all 4 variations (`scholars`, `civilizations`, `operators`, `single`) and both chair settings (`aletheia`, `none`), including strict label-stripping enforcement (`assert_variation_c_label_stripped`) on Variation C.
2. **Pilot-1 Three-Topic Certified Syntheses (`verify_pilot1_theorems.py`, `pilot1_transcripts/`):**
   - Cryptographically binds all `6` sanitized Pilot-1 transcript files (`3` topics × `21` turns = `63` refereed turns: `51` `PASS_WITNESS`, `12` `MINIMAL_COUNTEREXAMPLE`, `20` counterexample repairs, `30` cross-seat compositions, depth `3`, bidirectional pollination `PASS` on `3 / 3` topics) and independently re-certifies all three emergent Round-3 Chair theorems in exact $\mathbb{Z}/\mathbb{Q}$:
     - **Theorem 1 (`Foundation-0/continuum`):** Unified Fricke–Cayley discriminant $\kappa(a,b,x,y,z) = 4ab - bx^2 - ay^2 - z^2 + xyz$ spanning definite Hurwitz/Lipschitz quaternion orders ($\kappa = 2D \ge 0$, odd Hurwitz $D=1$ gap halving, $SO(3)$ Frobenius defect $F_{\mathrm{cleared}} = 8D(2ab-D) \equiv 8D \pmod{16}$, spinor-invisible kernel $D \in \{0, 2ab\}$) and split $GL_2(\mathbb{Z})$ continued-fraction transpose pairs ($\kappa = -[(p-s')^2+(q+r)^2](q-r)^2 \le 0$, palindromic vanishing iff $W = W^T$, naive-$SL_2(\mathbb{Z})$ overshoot $2(1-s)t^2$).
     - **Theorem 2 (`Foundation-0/aletheion`):** Joint non-coprime Chinese Remainder Theorem (triple-decider agreement), coprime single-cycle stride, inclusive two-threshold hysteresis bounded-chatter total-variation law $(F-1)(\mathrm{hi}-\mathrm{lo}) \le \mathrm{TV}$, and chiral half-split tree checksum (`left + 3 * right`) tamper detection.
     - **Theorem 3 (`Foundation-0/cave-expedition`):** Unified Schur–Witt–Fold criterion — exact $\mathbb{Q}$ and fraction-free $\mathbb{Z}$ Schur congruences, $GL(\mathbb{Z})$ canonical shear iff $A^{-1}B$ is integral (with converse counterexample `[[4,2],[2,1]]`), bidirectional $1\times 1$ block-drop rational congruence iff $sD$ is a nonzero rational square (witness `[[3,3],[3,4]]` with $Q = [[1,-2],[0,2]]$ and universal $\sqrt{2}$ obstruction on `[[2,1],[1,1]]`), $GF(2)$ invertibility iff $\det A$ is odd with even-diagonal preservation, and $(2,3)$ doubled-coordinate mirror billiard (`curves == gcd(p, q)`).
3. **5-Arm Matched-Budget Variation Ablation (`verify_ablation_scorecard.py`, `ablation_transcripts/`):**
   - Re-evaluates all **`5` matched-budget `21`-turn arms (`105` live refereed turns)** on `TOPIC-1-CONTINUUM` live through `socratic_operator_seminar.evaluate_seminar_session` with **`5 / 5` exact dictionary equality (`0` transcript drift)** and raw-byte SHA-256 on-disk binding to all `7` input JSON files (including fully anonymized neutral-ID `provenance_map.json`).
4. **Pure-`Init` `Lean 4.36.0` Formalization (`lean_pilot1_theorems/`):**
   - Zero-Mathlib, zero-`Classical.choice`, zero-`bv_decide`, zero-`native_decide`, zero-`sorryAx` constructive kernel formalization of **`36` public theorems** across `4` modules (`IntPoly` `6`, `Topic1FrickeCayley` `11`, `Topic2ValveKhipu` `9`, `Topic3SchurWittFold` `10`), verified by cold `lake build`, `leanchecker --fresh` (`EC=0`), and `AxiomAudit.lean` (`#print axioms` strictly within `[]`, `[propext]`, `[propext, Quot.sound]`).

---

## 2. Exact Pure-$\mathbb{Q}$ 5-Arm Variation Ablation Scorecard (`105` Refereed Turns)

| Arm | Variation / Chair (Seats) | `PASS` (`pass_rate_q`) | `CEX` (`cex_rate_q`) | Depth / Edges | Repairs (`rep/cex`) | Cross-Seat (`xs/edge`) | Live Interps (`int/turn`) | `h2m` / `m2h` | R3 PASS (`r3_rate_q`) | Compounding / Bidirectional | Label Strip |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Arm_A_plus`** | `scholars` / `aletheia` (`7`) | `16` (`16/21`) | `5` (`5/21`) | `3` / `14` | `5` (`1/1`) | `9` (`9/14`) | **`15`** (`5/7`) | **`2` / `3`** | `6/7` (`6/7`) | **PASS / PASS** | `n/a` |
| **`Arm_A_minus`** | `scholars` / `none` (`6`) | `18` (`6/7`) | `3` (`1/7`) | `3` / `15` | `7` (`7/3`) | `9` (`3/5`) | `0` (`0/1`) | `0` / `0` | `8/9` (`8/9`) | PASS / FAIL | `n/a` |
| **`Arm_B_plus`** | `civilizations` / `aletheia` (`7`) | `18` (`6/7`) | `3` (`1/7`) | `3` / `14` | `4` (`4/3`) | `9` (`9/14`) | `12` (`4/7`) | `1` / `0` | `5/7` (`5/7`) | PASS / FAIL | `n/a` |
| **`Arm_C_plus`** | `operators` / `aletheia` (`7`) | `18` (`6/7`) | `3` (`1/7`) | `3` / `14` | `3` (`1/1`) | `9` (`9/14`) | `12` (`4/7`) | `2` / `0` | `5/7` (`5/7`) | PASS / FAIL | **PASS (`21/21`)** |
| **`Arm_D_single`** | `single` / `none` (`1`) | **`19`** (`19/21`) | `2` (`2/21`) | `3` / `14` | `7` (`7/2`) | **`0`** (`0/1`) | **`0`** (`0/1`) | `0` / `0` | `7/7` (`1/1`) | PASS / FAIL | `n/a` |

### Key Findings & Scope Disclosure

- **Overall Structural Winner (`Arm_A_plus`):** `Arm_A_plus` is the sole arm (`1 / 5`) simultaneously passing dynamic compounding, bidirectional pollination (`h2m = 2`, `m2h = 3`), cross-seat composition (`9/14`), and live interposition grounding (`15`).
- **Single-Seat Control (`Arm_D_single`):** Achieved the highest raw pass rate (`19/21`) via `7` self-repairs, yet produced **`0` cross-seat compositions** and **`0` interpositions** — showing that raw pass rate alone cannot distinguish homogeneous monologue from cross-tradition synthesis.
- **Label-Stripped Operator Parity (`Arm_C_plus`):** Passed strict `assert_variation_c_label_stripped` across all `21 / 21` turns while matching multi-seat cross-composition (`9/14`), reaching `18/21` (`6/7`) PASS, `12` interpositions, and `2` `h2m` edges — refuting persona theater.
- **Root Cause of `m2h = 0` in `Arm_B_plus` and `Arm_C_plus`:** Neither arm had a Round-2 or Round-3 peer seat target `R1-SEAT-0` or `R2-SEAT-0`. Adding a Round-2 scheduling rule requiring at least one peer seat to target `R1-SEAT-0` guarantees bidirectional pollination structurally across chaired variations.
- **Routing-Fallback Covariate Sensitivity Disclosure:** Across the three multi-seat ablation arms (`Arm_A_minus`, `Arm_B_plus`, `Arm_C_plus`), `22 / 63` turns (`7/21`, `6/21`, `9/21` — all cross-route fallbacks across `7`–`9` anonymized routes) experienced routing failover, versus `2 / 21` same-route retries (`0` cross-route fallbacks, `1` route) in `Arm_D_single` (`fallback_rate_gap_q = 16/63`; `Arm_A_plus` was recorded prior to the ablation provenance logger). Accordingly, small raw pass-rate differences (`16/21` vs `18/21` vs `19/21`) on a single benchmark topic (`n = 1`) are confounded by routing reliability and single-topic variance and are not overclaimed; the topological separations (`9` vs `0` cross-seat compositions, `12–15` vs `0` interpositions, bidirectional pollination) are architectural invariants.
- **Energy / Power Scope:** `UNCONTROLLED_LAPTOP_NOT_CLAIMED` — all verification runs strictly CPU-only in exact $\mathbb{Z}/\mathbb{Q}$ and Lean 4 with zero energy/power claims.

---

## 3. Reproducible Verification Commands

```bash
cd socratic-operator-seminar

# 1. Unified 4-pillar offline verifier across 3 isolated Python modes (bit-identical output)
python3 -I -B verify_all_seminar.py --json
python3 -I -O -B verify_all_seminar.py --json
python3 -I -B -W error verify_all_seminar.py --json

# 2. Full verification including cold Lean 4.36.0 build + leanchecker --fresh + AxiomAudit
python3 -I -B verify_all_seminar.py --live-lean --json

# 3. All 5 adversarial negative-control & tamper-rejection unit test suites
python3 -I -B tests/test_socratic_operator_seminar_r5.py -v
python3 -I -B tests/test_pilot1_theorems_r5.py -v
python3 -I -B tests/test_ablation_scorecard_r5.py -v
python3 -I -B tests/test_verify_all_seminar_r5.py -v
(cd lean_pilot1_theorems && python3 -I -B test_verify_s150_lean_theorems_r5.py -v)

# 4. Root repository unified offline verifier (includes SOCRATIC-SEMINAR as study 8/8)
(cd .. && python3 -I -B verify_all_standalone.py --json && python3 -I -B test_verify_all_standalone.py -v)
```

### Verification Summary

- **Pure-$\mathbb{Z}/\mathbb{Q}$ AST Self-Guard (`verify_pure_q_ast`) & Isolated Referee Hardening:** Enforced live inside all 4 verifiers (`0` `ast.Div`, `0` `ast.FloorDiv`, `0` `ast.Pow`, `0` `ast.Mod`, `0` float/complex literals, `0` f-string format specifiers, `0` bare asserts, `0` forbidden imports, `0` `getattr`/`eval`/`exec`/`vars`/`format`/`format_map`/`memoryview`/`literal_eval`/`compile`/dunder escapes outside `__init__`/`__name__`, `0` indirect calls or container-wrapped `Fraction` aliases, `0` unsafe `Fraction(str)` or `=`/`:`/` :=` aliased rebinds, fail-closed `SyntaxError` wrapping). The isolated referee AST gate and subprocess runner additionally reject `ast.Yield`/`ast.YieldFrom`/unbound `GeneratorExp`/`AsyncFor`/`AsyncWith`/`Await`, block frame/generator/coroutine/traceback/code attributes (`gi_*`/`f_*`/`cr_*`/`ag_*`/`tb_*`/`co_*`/`func_*`/`im_*`), clear runner module globals and `__builtins__` prior to `exec`, expose only locked-down pure-`int`/`Fraction` namespaces (`math.gcd`, `math.isqrt`, exact-int/rational `Fraction`), and AST-rewrite `/` and `**` at runtime to refuse float-producing `int / int` and negative integer powers.
- **Strict Byte-Level I/O, JSON, Symlink, Manifest, & Lean Hardening:** Every verifier enforces ancestor-symlink refusal + `O_NOFOLLOW | O_NONBLOCK` + `S_ISREG` + streaming `16 MiB` file cap + sanitized `OSError` wrapping, rejects UTF-8 BOM (plus CR/CRLF in `socratic_operator_seminar.py` and canonical cert byte checks in `verify_s150_lean_theorems.py`), duplicate object keys (`object_pairs_hook`), float literals, `NaN`/`Infinity`, pre-parse nested JSON depth `>32` (+ `RecursionError` catch), and `>1024`-digit integer literals (wrapped cleanly to `RC=2` structured JSON errors with zero tracebacks, including `sos.SeminarError` across Pilot-1/Ablation, `BAD_UTF8` self-source decoding and pre-sort turn/`round_num` validation in `socratic_operator_seminar.py`, `OSError`/`UnicodeDecodeError` in `--live-lean`, and non-symlink-following `Path(__file__)` refusal + `(OSError, UnicodeDecodeError, RecursionError) -> RC=2` in root `verify_all_standalone.py`), bans `#eval`/`#reduce`/`IO.`/`System.` Lean escapes and unpinned `lakefile.toml` keys (`moreLeanArgs`/`plugins`), wraps Lean subprocess timeouts (`LEAN_TIMEOUT` -> `RC=2`), compares offline static & pure-$\mathbb{Q}$ fields directly without synthetic `live_lean_verified` fabrication, and binds all `5/5` ablation arms (including honest pre-logger baseline `Arm_A_plus`) inside `provenance_map.json`.
- **Acyclic External SHA-256 Pinning & 3-Mode Isolated `-I` Parity:** `SEMINAR_MANIFEST.json` cryptographically pins all `42` Layer-1 seminar files (including this `README.md`), `verify_all_seminar.py` pins `SEMINAR_MANIFEST.json` plus all 4 pillar verifiers & certificates before executing any sub-verifier (forwarding active `-O`/`-OO`/`-W` flags), and root `verify_all_standalone.py` pins `SEMINAR_MANIFEST.json`, `verify_all_seminar.py`, and `certificates/seminar_unified_certificate.json` as study `8/8`. `verify_all_seminar.py --json` (`4/4` pillars `PASS`, byte-identical to `certificates/seminar_unified_certificate.json`), root `verify_all_standalone.py --json`, and all `5` seminar R5 test suites (`24/24` tests `OK`) + `test_verify_all_standalone.py` match identically across `-I -B`, `-I -O -B`, and `-I -B -W error`.
- **External Mutation Runner Results (`aletheia mutate --max-mutants 0`, both default and `--guards require_ok`, plus whole-file AST `BoolOp` sweep):**
  - `socratic_operator_seminar.py`: `127 / 127` (`100.0%`) dual mutate, `46 / 46` (`100.0%`) `BoolOp`
  - `verify_pilot1_theorems.py`: `55 / 55` (`100.0%`) dual mutate, `28 / 28` (`100.0%`) `BoolOp`
  - `verify_ablation_scorecard.py`: `83 / 83` (`100.0%`) dual mutate, `18 / 18` (`100.0%`) `BoolOp`
  - `lean_pilot1_theorems/verify_s150_lean_theorems.py`: `155 / 155` (`100.0%`) dual mutate, `45 / 45` (`100.0%`) `BoolOp`
  - `verify_all_seminar.py`: `33 / 33` (`100.0%`) dual mutate, `4 / 4` (`100.0%`) `BoolOp`
  - **Combined (`5` seminar verifiers):** `453 / 453` (`100.0%`) guard/boundary mutants killed, `141 / 141` (`100.0%`) AST `BoolOp` mutants killed, `0` survivors (plus root `verify_all_standalone.py`: `66 / 66 = 100.0%` dual mutate, `12 / 12 = 100.0%` `BoolOp`; grand total `519 / 519` dual mutate & `153 / 153` `BoolOp`).

---

## 4. Core Layer-1 Deliverable SHA-256 Manifest

*(Downstream digests for `SEMINAR_MANIFEST.json`, `verify_all_seminar.py`, and `certificates/seminar_unified_certificate.json` depend on this `README.md` via the acyclic manifest chain and are pinned in `../verify_all_standalone.py`.)*

| Relative Path (`socratic-operator-seminar/...`) | Lines | Bytes | Raw-Byte SHA-256 |
| :--- | :---: | :---: | :--- |
| `socratic_operator_seminar.py` | `1,857` | `85,044` | `e4f39de6d9fbb1a16265e8622e2ccf988f96654973a9c0930ab29437185eb196` |
| `verify_pilot1_theorems.py` | `1,035` | `40,910` | `d927eff59ce74b8f4b31b994354b3cb40807caec226e5b2a349a7667bc77fc85` |
| `verify_ablation_scorecard.py` | `695` | `34,425` | `688106cdc2476e3f937eb34ff5c0995053692a3aebbd7012d14ab84cc242b237` |
| `tests/test_socratic_operator_seminar_r5.py` | `645` | `40,399` | `016d5ebc4c4aa750590eedb29bee976a1d03ae60bc792caec2754fb2fd73d9db` |
| `tests/test_pilot1_theorems_r5.py` | `367` | `20,626` | `beb2a31810f71c9c9db94c1bb95862f60599cfa7fda18c95913a8fa365606051` |
| `tests/test_ablation_scorecard_r5.py` | `494` | `29,656` | `e26f6e803b51c343be7443ee5b48e45b20355ca4253e06f9733b552d24df35ee` |
| `tests/test_verify_all_seminar_r5.py` | `263` | `14,261` | `d285b3455f01bc6228ad12624fde3669af31c573b1be04eecd203d6547e92f11` |
| `certificates/seminar_harness_certificate.json` | `304` | `9,305` | `552467381026f06c74ebb804c3fdeeee0d97cb12e615734841e454326412fa27` |
| `certificates/pilot1_theorems_certificate.json` | `379` | `9,330` | `bf1a1b7f18fdc57ea58ad1a95eae80a2e10a6035447fd38ebed7ad31a544e8d2` |
| `certificates/ablation_scorecard_certificate.json` | `370` | `13,790` | `436ec03628a6f7ba00286c1297f4a39f36037735ca0fca0f81f16164a5f8f288` |
| `lean_pilot1_theorems/verify_s150_lean_theorems.py` | `1,139` | `50,614` | `633c063f82e72a83bf3703219c427886401cd68b9b68f2c762f19797d91faf4e` |
| `lean_pilot1_theorems/test_verify_s150_lean_theorems_r5.py` | `699` | `42,740` | `0417c592c8b567e32830c7206231c93fd163370312b8b061b4e9999142b66029` |
| `lean_pilot1_theorems/s150_lean_theorems_certificate.json` | `48` | `1,893` | `72f6d6733a454879dbb83507a0b7571992d8e227721b77dc9acd9fe11ee92fcf` |
| `lean_pilot1_theorems/S150Pilot1Theorems/IntPoly.lean` | `277` | `10,388` | `1c7288f534a6f5ca1ba1f239ea4069874abdc7bb6bc226e03db048dd04b70990` |
| `lean_pilot1_theorems/S150Pilot1Theorems/Topic1FrickeCayley.lean` | `641` | `32,034` | `85e17836d193de5433e3c19c947f835c9eff4e42bc2130c7598031fbde0369f2` |
| `lean_pilot1_theorems/S150Pilot1Theorems/Topic2ValveKhipu.lean` | `384` | `17,125` | `7d2564ce4818a1fa5bc6cd8e541765de58ebac73b9590abbe9bd68aa437e0e9f` |
| `lean_pilot1_theorems/S150Pilot1Theorems/Topic3SchurWittFold.lean` | `516` | `28,833` | `cf75141c91bfe3441be42ee75c760d0d4e9cbaaabb231cce6f4e18d3fea4fd4b` |
| `lean_pilot1_theorems/AxiomAudit.lean` | `45` | `2,572` | `69571c3419f5ac5142275d6bf95a711aa83f5f3bdfaa9be7afe6b811ab057679` |
| `ablation_transcripts/provenance_map.json` | `1,675` | `42,747` | `aab295d3e0c07f6144ec3a2f95ed46740f68f1bf0b599ba4c575e861c083b3f0` |
