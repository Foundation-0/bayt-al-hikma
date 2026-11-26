# `EXP-Q43a` & `EXP-Q43b` — FlyEM *Drosophila* MaleCNS v1.0 Connectome x Neuro-Model Cross-Pollination

- **Upstream Connectome Anchor:** Pinned MaleCNS v1.0 pure-integer anchor (`s102_malecns_anchor.json` SHA-256 `067638e0f8529df79e68e9869abcb26d4cde61f9648488310c1436432540e41c`, payload `f72c14e984f0c247fb44f9d5049a7575d8962eef6f16cacd243231f2a6a553ad`; upstream certificate envelope `25148049f59bef777a9ded709e0b8fc0ae758766d2a91513feda001072aaa472`). External FlyEM MaleCNS v1.0 `.feather` tables are read-only external data (`0` raw `.feather` copies or model weights in this bundle); all 3 external `.feather` SHA-256 hashes can be live-verified via `--verify-data`.
- **Certificate Schema:** `s162-malecns-neuro-bridge-cert-v1`
- **Certificate File (`s162_malecns_neuro_bridge_certificate.json`, `33,177` B):**
  - File SHA-256: `bf5ff7c97c8c766a4f88dea18774561f116970c20cf9a9aabf1ffe661f1852f8`
  - Envelope `certificate_sha256`: `aa495f9996a69f8180554336120363a45ce7db7c4cb1ff71ea39c57f1a1625d5`
  - `payload_sha256`: `95dff591af888903e9ec2d972049b19d50126489a5b7d7420b3ed403cb6a31a4`
- **Oracle Class & Governance:** `EXACT_INTEGER_RATIONAL_AND_LEAN4` (pure stdlib `int`/`Fraction`, `0` IEEE-754 production floats, `0` unseeded RNG calls, `0` bare `assert`s, `0` uncontrolled laptop energy/power claims, coordinate-free exact operators).
- **Honest Novelty Classification:** `N0_N1_CONNECTOME_NEURO_BRIDGE_EXACT_OPERATORS` (`N0` exact rational replay of real FlyEM MaleCNS v1.0 `6x6` CX / `8x8` supergraph + `w >= 10` CX triad counts and published routing equations; `N1` pure-`Q` Cayley-Routh BP damping tomography, 5-operator structural separation, and `16/16` universal pure-`Init` Lean 4.36.0 operator laws; `0` unverified `N2` claims).

---

## 1. `EXP-Q43a` — MaleCNS Frustrated Cycles x PFC Loopy BP & Ibn al-Nafis Septal Cavity Exclusion

### 1.1 Exact Pure-`Q` Bethe-Hessian & Cayley-Routh Damped BP Stability Tomography

Evaluated strictly in pure `Fraction` arithmetic (exact Faddeev-LeVerrier characteristic polynomial + exact Cayley-Mobius transform + minimal non-redundant Routh-Hurwitz decision procedure, plus exact LDL^T / congruence inertia) on the real MaleCNS v1.0 `6x6` Central Complex (`EPG, PEN, Delta7, PEG, ER, PFL`, Dale signs `[+1, +1, -1, +1, -1, +1]`, `11.197x` `w >= 10` reciprocity, `6.851x` negative-feedback 3-cycles, `6.853x` incoherent FFLs) and `8x8` functional supergraph at BP loop gain `alpha = 3/2` and `arXiv:2406.17863` log-damping `gamma = 1/2`:

| System / Control | Signed Laplacian `L_sigma` Inertia | Bethe-Hessian `H_BH(1)` PD | Critical `r_hi` (`1 - r_hi` Gap) | Undamped `gamma = 1` Stable | Log-Damped `gamma = 1/2` Stable | Exact Critical Damping `gamma*` (`gamma_mid_q`) |
|---|---|:---:|---|:---:|:---:|---|
| **Real MaleCNS `6x6` CX (cavity-excluded)** | `[6, 0, 0]` | `True` | `471/512` (`0.9199`, gap `41/512 = 0.0801`) | **`False`** | **`True`** | `1830019/2097152` (**`0.8726`**, bracket `[456993/524288, 916033/1048576]`) |
| **Real MaleCNS `6x6` CX (STA self-loop polluted)** | `[6, 0, 0]` | `True` | `471/512` | `False` | **`False`** | **`0`** (unstabilizable by any `gamma > 0`, bracket `[0, 1/1024]`) |
| **Real MaleCNS `8x8` Supergraph** | `[8, 0, 0]` | `True` | `993/1024` (`0.9697`, gap `31/1024 = 0.0303`) | `True` | `True` | `2362239/2097152` (`1.1264`) |
| **Unsigned CX `6x6` (`W6_u`, positive-only)** | `[5, 0, 1]` | `False` | `2049/2048` (`> 1`, gap `<= 0`) | `False` | **`False`** | **`0`** (Perron runaway `lambda >= 3/2`, Theorem 2) |
| **Unsigned Supergraph `8x8` (`W8_u`)** | `[7, 0, 1]` | `False` | `2049/2048` (`> 1`, gap `<= 0`) | `False` | **`False`** | **`0`** (Perron runaway) |
| **Acyclic DAG Control (`W6_dag`, upper-tri)** | `[6, 0, 0]` | `True` | `225/256` (`0.8789`) | `True` | `True` | `4192257/2097152` (`~2.0000`, nilpotent exact BP) |
| **Exhaustive `W9-OBS-1` Dale-Sign Shuffles (`14` other `[4+, 2-]` pairs)** | mixed | — | Real CX beats **`14/14`** (`1.6638x` mean gap lift `574/345`) | `8/14` stable (`2/14` unstabilizable) | `12/14` stable | Mean of `12` stabilizable = `1657559/1572864` (`1.0538`; **real CX `-17.20%` tighter**, `1140179/6630236`) |
| **Maslov-Sneppen Weighted Degree-Matched Null (`20` logged seeds `16201..16220`)** | `[6, 0, 0]` | `True` | Mean `945/1024` (`0.9229`) | **`20/20`** stable | `20/20` stable | Mean `6778643/5242880` (`1.2929`), range `[1.1371, 1.4729]`; **real CX strictly below `20/20` seeds (`-32.51%` tighter**, `4407191/13557286`) |

**Key Findings & Kill-Gate Verdicts (`EXP-Q43a`):**
1. **Kill Gate 1 (`bethe_bp_stability_bound_pass = True`):** On real MaleCNS `6x6` CX, undamped loopy BP (`gamma = 1`) **diverges/oscillates** along the frustrated Al-Tusi E/I ring attractor (`EPG <-> ER` / `EPG <-> Delta7`), while `arXiv:2406.17863` log-damping (`gamma = 1/2 < gamma* = 0.8726`) **stabilizes convergence** (Lean Theorems 3 & 4). Removing Dale signs (`W6_u`, `W8_u`) collapses `gamma* -> 0` (unstabilizable positive runaway, Lean Theorem 2).
2. **Kill Gate 2 (`separation_gt_5pct_vs_shuf_and_ms_pass = True`):** Real MaleCNS CX has critical damping `gamma*` **`-32.51%` tighter** than `20/20` degree- and Dale-preserving Maslov-Sneppen nulls (zero overlap: `0.8726 < 1.1371`) and **`-17.20%` tighter** than the mean of all stabilizable `[4+, 2-]` Dale-sign shuffles (plus rank `1/15` deepest Bethe-Hessian frustration gap `41/512`, `1.6638x` the shuffle mean) — exceeding the preregistered `5%` kill gate by `3.4x` to `6.5x`.
3. **Exact Hashimoto Non-Backtracking vs. STA Backtracking Traces (`W6_s`):**
   - Cavity-excluded Hashimoto operator `B_NB` zeroes 2-cycle self-echo identically (`tr(B_NB^2) = 0`, Lean Theorem 10), while `tr(B_NB^3) = -75,941,555,757,750` out of `78,130,263,203,598` absolute weighted 3-cycle mass — proving **`98.60%`** (`12839318246779/13021710533933`) of weighted directed 3-cycle mass in MaleCNS `6x6` CX is negative-feedback (vs. `0%` in `W6_u`).
   - STA backtracking (`B_STA`) injects massive self-echo `tr(B_STA^2) / ||W_off||_F^2 = -2360148764/8708730223` (`-0.2710`) on `W6_s` (and `+2968387082/8708730223 = +0.3409` on `W6_u`), and polluting `W6_s` with self-loops collapses `gamma*` from `0.8726` straight to `0`.

### 1.2 Exact Cavity-Exclusion Isomorphism (`STA` vs. `Max-Sum` BP vs. Ibn al-Nafis Septal Firewall)

- **Algebraic Isomorphism (Lean Theorem 8):** On the 3-node grounded Laplacian `L_red = [[w1 + w_sep, -w1], [-w1, w1 + w2]]` (`w1 = 3, w2 = 5`), `det(L_red) = w_sep*(w1 + w2) + w1*w2`. At `w_sep = 0` (Ibn al-Nafis non-porous septum / exact BP cavity exclusion), forward cavity throughput is `15/15 = 1` (`0` septal echo leak). Raising `w_sep` through `{1, 2, 5}` monotonically degrades forward throughput (`15/23`, `15/31`, `3/11`) and raises echo leak (`8/23`, `16/31`, `8/11`), conserving `fwd + leak = 1` identically.
- **Discrete Self-Echo Blowup (Lean Theorem 9):** On a 2-slot link (`a = 1, b = 2`), cavity-excluded BP stays stationary `[1, 1, 1, 1, 1, 1]`, while STA total-marginal echo `z_{t+1} = 1 + 2*z_t` diverges exponentially `[1, 3, 7, 15, 31, 63]`.
- **Pinned Empirical Confound Disclosure (`dileeplearning/sta-planning-benchmark`, `DOI: 10.82153/9dp2-6t31`, `eLife 109757`):** On 20 `15x15` DFS mazes (`3,000` queries across `d = 1..30`), `STA(400)` solves `700/3000` (`100%` at `d <= 7`, `0%` at `d >= 8`), `STA(1500)` solves `800/3000` (`100%` at `d <= 8`, `0%` at `d >= 9`), and `Max-Sum BP(30)` solves `3000/3000` (`100%` at `d = 1..30`). As disclosed in `METHODS.md`, this benchmark bundles cavity exclusion with start-clamping, reward scaling, `exp(-100)` flooring, and joint backtracing; our pure-`Q` operators isolate the cavity-exclusion mechanism algebraically.

---

## 2. `EXP-Q43b` — 5-Operator Tomography x Carved & Looped Neural Routing Topologies

> **Honest Epistemic Scope:** All neural routing topologies below are exact architectural routing operator graphs derived from published equations and configs (`arXiv:2611.27962v1` `Model Carving`, `configs/umolt_s.json` `U-MoLT`, `arXiv:2607.18264` `MUX` Cor. 14–15 `rho = 9/10`, `hf_fg_args_all.json` `Floodgates` `k = 8`), with zero model weights committed.

### 2.1 Exact 5-Operator Comparison Table (Biological Anchors vs. Wave-22 Topologies)

| Topology | `E` | Op 1: Top-20% Lift | Op 2: Recip (`FFL / 3-Cyc`) | Op 3: Inc-FFL / Neg-3C | Op 3: `L_sigma` Inertia (`Frust`) | Op 4: I/O Schur Dark Shadow | Op 5: Norm Commutator |
|---|---:|---:|---|---:|---|---:|---:|
| **`MaleCNS_6x6_CX`** (bio anchor) | `28` | **`4.2057`** | `1.0000` (`96 / 32`) | `0.2500 / 0.7500` | `[6, 0, 0]` (**`True`**) | `0.7541` | **`0.4737`** |
| **`MaleCNS_8x8_Super`** (bio anchor) | `50` | **`3.9591`** | `0.9600` (`240 / 80`) | `0.4167 / 0.4250` | `[8, 0, 0]` (**`True`**) | **`0.1355`** (`13.5524%`) | `0.0660` |
| `ModelCarving_Unroll_Signed_9` (`9/12` kept) | `27` | `1.7250` | `0.0000` (`39 / 0`) | `0.4103 / 0.0000` | `[9, 0, 0]` (`True`, DAG only) | `0.2351` | `0.2055` |
| `ModelCarving_Fold_Signed_AntiSym_6` | `30` | `2.0266` | `1.0000` (`120 / 40`) | `0.5000 / 0.5000` | `[5, 0, 1]` (**`False`**) | `0.4962` | `0.0425` |
| `ModelCarving_Fold_Unsigned_6` (`c >= 0`) | `30` | `2.0266` | `1.0000` (`120 / 40`) | `0.0000 / 0.0000` | `[5, 0, 1]` (**`False`**) | `0.4962` | `0.0425` |
| **`ModelCarving_Fold_MaleCNS_DalePrior_6`** | `30` | `2.0266` | `1.0000` (`120 / 40`) | `0.3333 / 0.6000` | `[6, 0, 0]` (**`True`**) | `0.3115` | **`0.4794`** |
| `MoLT_UMoLT_12` (`umolt_s.json`) | `23` | `1.5633` | `0.0870` (`13 / 2`) | `0.0000 / 0.0000` | `[11, 0, 1]` (**`False`**) | `0.6588` | `0.2009` |
| `MUX_Jacobi_8` (`rho = 9/10`, `S = 6`) | `42` | `1.6973` | `0.7143` (`180 / 40`) | `0.0000 / 0.0000` | `[7, 0, 1]` (**`False`**) | `0.5000` (`1/2`) | `0.4473` |
| `Floodgates_k8_10` (`k = 8`, `c_R` cache) | `81` | `2.1309` | `0.8889` (`576 / 168`) | `0.0000 / 0.0000` | `[9, 0, 1]` (**`False`**) | `0.5554` | `0.6863` |
| `Dense_Uniform_6` (null baseline) | `30` | `1.0000` | `1.0000` (`120 / 40`) | `0.0000 / 0.0000` | `[5, 0, 1]` (`False`) | `0.4000` (`2/5`) | `0.0000` |

**Honest Structural Separation Ruling (`EXP-Q43b` Kill Gate 1):**
1. **`0/4` unsigned Wave-22 architectures (`MoLT`, `MUX`, `Floodgates`, unsigned `Model Carving`) exhibit signed frustration:** All have `0%` incoherent FFLs, `0%` negative 3-cycles, and a zero Laplacian nullspace `[n-1, 0, 1]` (Lean Theorem 12). Every Wave-22 model also has roughly half the heavy-tail concentration lift (`1.56x..2.13x`) of real MaleCNS (`3.96x..4.21x`).
2. **Anti-Symmetric Skip Erasure Obstruction (Lean Theorem 13):** `Model Carving` (`carving/residual.py` Eq. 2) is the sole Wave-22 architecture permitting inhibitory weights (`c < 0`). Unrolled (`9` active kept nodes), its one-way negative cross-loop skips frustrate `L_sigma` (`[9, 0, 0]`) while carrying `0` reciprocity and `0` directed 3-cycles (separated cleanly from 20-seed Maslov-Sneppen `rec = 13/54`, `3-cyc = 4.1` and Erdos-Renyi `rec = 56/135`, `3-cyc = 8.1`). When loop-folded onto shared `K = 6` layers, stronger forward residual skips (`+w_fwd`) overpower weaker backward inhibitory skips (`-w_bwd`) inside `W + W^T`, **erasing signed frustration (`[5, 0, 1]`) and collapsing non-normality to `0.0425`**.
3. **MaleCNS Dale-Prior Restoration:** Injecting MaleCNS Dale row-homogeneous signs (`[+1, +1, -1, +1, -1, +1]`) into folded `Model Carving` simultaneously **restores `[6, 0, 0]` signed frustration**, lifts normalized commutator non-normality **`11.28x`** (`0.0425 -> 0.4794`, matching MaleCNS CX's `0.4737`), and increases negative 3-cycle share to `60.0%`.

### 2.2 `EXP-Q43b` Kill Gate 2 — Pure-`Q` Dynamical Tail-Stability Transfer (`20` Unseen Seeds `16251..16270`)

At matched off-diagonal row-L1 gain `alpha = 3/2`, damping `gamma = 1/2`, `T = 10` recurrent loop steps across `20` unseen logged disturbance seeds:

| Looped Controller Arm | Exact Mean Energy `E_10 / E_0` | Worst-Case Tail (`max E_10 / E_0`) | Worst-Case Ratio vs. Dale-Carving |
|---|---:|---:|---:|
| **`ModelCarving_Fold_MaleCNS_DalePrior`** | **`0.001079`** | **`0.002840`** | `1.00x` (best) |
| `ModelCarving_Fold_Signed_AntiSym` | `0.003180` | `0.006575` | `2.32x` worse |
| `Maslov_Sneppen_5seed_Avg` | `0.003176` | `0.014013` | `4.93x` worse |
| `MaleCNS_6x6_CX` (real biological core) | `0.011624` | `0.027898` | `9.82x` (ring-attractor oscillator) |
| `Dale_Sign_Shuffled_(0,4)` (`W9-OBS-1`) | `0.240633` | `0.857008` | `301.8x` worse |
| `Dale_Sign_Shuffled_(2,5)` (`W9-OBS-1`) | `2.536858` | `11.066500` | `3,897x` worse |
| `ModelCarving_Fold_Unsigned` (`c >= 0`) | `16.502930` | `60.514532` | **`21,308x` worse** |
| `Unsigned_W6_u` (unsigned CX) | `19.453293` | `93.218650` | **`32,823x` worse** |

Variance collapses by **`5.49e8x`** (`ModelCarving_Fold_Unsigned` / `ModelCarving_Fold_DalePrior`) and **`1.11e7x`** (`Unsigned_W6_u` / `MaleCNS_6x6_CX`), identifying **Dale row-homogeneous inhibitory dominance coupled with log-damping** as the primary algebraic mechanism stabilizing recurrent worst-case tails (`dale_prior_beats_all_controls_on_worst_case_tail = True`).

---

## 3. Pure-`Init` `Lean 4.36.0` Formalization (`MaleCNSNeuroBridge.lean`)

Zero external imports, zero Mathlib, zero `sorry`/`admit`/`axiom`/`unsafe`/`native_decide`/`Classical.choice`, `lake-manifest.json` `"packages": []`. All **`16` universal (`forall`) theorems** compile cleanly under `lake build` & `lean MaleCNSNeuroBridge.lean` (`0` warnings) and depend strictly on `[propext, Quot.sound]`:

1. `damped_bp_real_eigenvalue_stability_window` — exact cleared iff window `p*(d-a) < 2*q*d` for `lambda = a/d < 1`.
2. `damped_bp_positive_runaway_obstruction` — no positive damping `p/q > 0` can stabilize `lambda = a/d >= 1`.
3. `damped_bp_complex_oscillator_stability_threshold` — exact cleared iff formula for complex E/I oscillator critical damping `gamma*`.
4. `damped_bp_oscillatory_undamped_divergence_damped_stabilization` — oscillatory modes (`a < d, a^2+b^2 > d^2`) diverge undamped yet contract for `gamma < gamma*`.
5. `signed_bethe_hessian_2x2_frustration_gap` — `2x2` `H_BH(r)` determinant factorization, `0` mode at `r=1` when unfrustrated, strict positivity under frustration.
6. `bethe_hessian_pd_implies_strict_frustration` — positive-definite `2x2` Schur form implies zero harmonic nullspace.
7. `cayley_mobius_disk_to_lhp_degree2` — exact Cayley-Mobius Routh-Hurwitz <-> Schur-Cohn equivalence for degree 2.
8. `nafis_cavity_firewall_zero_leak_isomorphism` — Ibn al-Nafis `2x2` grounded-Laplacian Schur firewall (`w_sep = 0` iff zero echo leak).
9. `sta_self_echo_double_counting_blowup` — STA recurrence `z_{t+1} = a + b*z_t` (`b >= 1`) strictly diverges at every step vs. stationary cavity-excluded BP.
10. `hashimoto_nonbacktracking_zero_2cycle_trace` — cavity exclusion zeroes `2*w12*w21` 2-cycle trace vs. opposing E/I negative / unsigned positive echo.
11. `chain_bp_exact_finite_horizon_convergence` — exact zero-error lock on acyclic chains for all sweeps `k >= d`.
12. `unsigned_network_zero_frustration_theorem` — unsigned non-negative weights yield `0` negative triads and zero uniform-mode energy.
13. `antisymmetric_skip_positive_symmetrization_obstruction` — forward-dominant anti-symmetric skips keep `w_fwd - w_bwd > 0`, whereas Dale inhibitory dominance flips `W + W^T < 0`.
14. `molt_triangular_prefix_nilpotent_lock` — `MoLT` Proposition 1 (`arXiv:2611.34923`): strictly lower-triangular prefix recurrence stabilizes identically for all `r >= t + 1` with zero contraction assumption.
15. `mux_rational_geometric_separation_margin` — `MUX` Corollary 14–15 (`arXiv:2607.18264`): rational `rho = p/q` (`2p < q`) guarantees collision-free ternary margin `>= p^2`.
16. `schur_dark_shadow_conservation_and_bounds` — exact `2x2` Schur dark-shadow conservation `S_num + L_bi^2 = L_bb * L_ii` and strict `(0, 1)` bounds.

---

## 4. Artifact Manifest & End-to-End Verification Receipts

| File | Bytes | SHA-256 |
|---|---:|---|
| `MaleCNSNeuroBridge.lean` | `27,474` | `24f27295acdf9a1bcb27d2d8430523f9c3ee4729c79c1ed30314d0ed6e4a56ab` |
| `lakefile.toml` | `130` | `9333586dffaf46ae193f037255b0927ba46099797b79aa9380488259c61e58cc` |
| `lean-toolchain` | `25` | `582a63f8f9c5128067b688778c1051cf1464c3ca9d57b9325025c051c29b774a` |
| `lake-manifest.json` | `90` | `79ff7de19171b1eade041516df1cd0ac49262d36237a09376beca08243e8e449` |
| `s102_malecns_anchor.json` | `7,949` | `067638e0f8529df79e68e9869abcb26d4cde61f9648488310c1436432540e41c` |
| `s162_malecns_neuro_bridge_certificate.json` | `33,177` | `bf5ff7c97c8c766a4f88dea18774561f116970c20cf9a9aabf1ffe661f1852f8` |
| `s162_malecns_neuro_bridge_oracle.py` | `71,951` | `675b651abf78ef8df1efbde50336c4289159cf34321d4a8490dd7da3bd5afac7` |
| `verify_s162_malecns_neuro_bridge.py` | `29,739` | `e3427c229a771dc4e7f296465a24502682558acd55f19141dfb9311cb81ced8e` |
| `test_s162_malecns_neuro_bridge_r5.py` | `47,442` | `55bcebab6ddd9dd118a327156270a686b44b648ea14e7ab420dc1b673f5809fa` |

### Verified Deterministic, Mutation, Lean, & Safety Gates
- **`3x -I` Isolated Parity (`-I -B`, `-I -O -B`, `-I -B -W error`):**
  - `verify_s162_malecns_neuro_bridge.py --check --json`: bit-identical stdout SHA-256 `6a9f13c5f0d0a0ba1046474e20014288a513d750c7b835f6a8c03959f01fd99e`.
  - `verify_s162_malecns_neuro_bridge.py` (default text): bit-identical stdout SHA-256 `9f172331d0bb76629d181554b6b264ec6e3f63e06556b6e01c4942b607e93711`.
  - `test_s162_malecns_neuro_bridge_r5.py`: **`9/9 OK` x3** (`0` skips, `0` bare asserts, `0` floats; includes `chmod -R a-w` read-only `--live-lean` leaving `0` `.lake/` artifacts).
- **Live Lean 4.36.0 & External MaleCNS Pin Replay:** `verify_s162_malecns_neuro_bridge.py --check --json --live-lean --verify-data` -> `PASS` (`16/16` live axioms `[propext, Quot.sound]` in isolated `tempfile.TemporaryDirectory()` staging, `0` `.lake/` artifacts in the study directory, `3/3` external `.feather` SHA-256 verified, `0` dataset copies in this repository).
- **Dual `aletheia 2.1.0 mutate` (`--max-mutants 0`, `null_mutant = passed`, `truncated = false`):**
  - `verify_s162_malecns_neuro_bridge.py`: **`117/117 = 100.0%`** (`default`) & **`117/117 = 100.0%`** (`--guards require_ok`), `0` survived.
  - `s162_malecns_neuro_bridge_oracle.py`: **`54/54 = 100.0%`** (`default`) & **`54/54 = 100.0%`** (`--guards require_ok`), `0` survived.
  - Combined: **`171/171 = 100.0%` x2** (`342/342`, `0` survived).
- **Whole-File AST `BoolOp` Mutation Sweep:** `verify_s162_malecns_neuro_bridge.py` **`3/3 = 100.0%`** + `s162_malecns_neuro_bridge_oracle.py` **`4/4 = 100.0%`** = **`7/7 = 100.0%`** killed (`0` survived).
- **`aletheia 2.1.0 audit-check --scripts verify_s162_malecns_neuro_bridge.py --lean-audit --strict-ancestors --safety-scan --strict-unseeded`:** **`PASS`** (both before and after `--live-lean`; `0` findings, `0` leaks, `0` pycache, `0` bare asserts, `0` unseeded RNG, `1/1` R4 bit-identical, `1/1` Lean clean).
- **Uncontrolled Laptop Energy Claims:** `0` (`UNCONTROLLED_LAPTOP_NOT_CLAIMED`).
