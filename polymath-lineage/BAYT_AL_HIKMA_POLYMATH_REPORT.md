# AUDIT-092R2: Bayt al-Hikma Polymath Lineage — Pure-$\mathbb{Q}$ Verification of Classical Mathematics & Encoding-Consistency Checks

> **Audit ID:** `AUDIT-092R2`  
> **Artifacts:** [bayt_al_hikma_polymath_certifier.py](bayt_al_hikma_polymath_certifier.py) · [test_bayt_al_hikma_polymaths_r5.py](test_bayt_al_hikma_polymaths_r5.py) · [bayt_al_hikma_polymath_certificate.json](bayt_al_hikma_polymath_certificate.json)  
> **Novelty Classification (Law 4):** **`N0`** (all mathematical theorems, historical figures, and published editions are classical prior art; this package provides a self-contained pure-$\mathbb{Q}$ stdlib verification script and encoding-consistency checker without claiming `N1` mathematical novelty).  
> **Scope & Conceptual Motivation:** Pure-$\mathbb{Q}$ zero-float transcriptions of mathematical constructions across `13` scholars (`c. 780–1274` CE): **al-Khwārizmī**, **al-Kindī**, **Banū Mūsā**, **Thābit ibn Qurra**, **al-Karajī**, **Ibn al-Haytham**, **al-Bīrūnī**, **Ibn Sīnā**, **ʿUmar al-Khayyām**, **Ibn Rushd**, **al-Samawʾal**, **Ismāʿīl al-Jazarī**, and **Naṣīr al-Dīn al-Ṭūsī**. Any parallels noted to modern continuum, algebraic, or feedback-control themes are **conceptual analogies / motivating parallels** only, not machine-verified cross-repository maps.

---

## 1. The 13-Scholar Lineage Dataset (Active-Voice Encoding-Consistency Check)

**Edge Direction Convention (Active Voice):** Every edge `{source, target, relation, citation}` is read as *`source` `<relation>` `target`* — for `teacher_of`, `source` taught `target`; for `corresponded_with`, `source` and `target` exchanged letters as contemporaries; for `extended`, `commented_on`, and `critiqued`, the later actor (`source`) engaged the prior subject (`target`)'s work.

`certify_polymath_lineage_graph()` in [bayt_al_hikma_polymath_certifier.py](bayt_al_hikma_polymath_certifier.py) runs **encoding-consistency checks** (`encoding_consistency_only = True`) on the `13`-node, `14`-edge curated dataset: verifying that every node and edge carries a structured secondary-edition `source` / `citation` (`work`, `edition`, `location`), that lifespans and active-voice chronology bounds hold (rejecting immature actors/subjects, reversed actor/subject birth order, and edges where an actor died before the subject reached age 15), and that the forward-time influence order is acyclic (`directed_dag_acyclic = True`). Acyclicity and chronology passage confirm internal consistency of the encoded table against its stated conventions, not independent empirical discovery about history.

| Scholar | Dates (CE) | Centers | Primary Treatise(s) | Published Edition Cited | Conceptual Parallel |
|---|---:|---|---|---|---|
| **Muḥammad ibn Mūsā al-Khwārizmī** | c. `780–850` | Baghdad | *al-Kitāb al-Mukhtaṣar fī Ḥisāb al-Jabr wa-l-Muqābala* | Rashed (2009), pp. 8–22, 94–110 | Canonical normal-form reduction |
| **Abū Yūsuf Yaʿqūb al-Kindī** | c. `801–873` | Baghdad | *Risāla fī Istikhrāj al-Muʿammā*; *De Gradibus* | Mrayati et al. (2003), pp. 121–158; McVaugh (1975), pp. 269–280 | Permutation-invariant frequency profile |
| **Banū Mūsā (Muḥammad ibn Mūsā ibn Shākir)** | c. `803–873` | Baghdad | *Kitāb al-Ḥiyal* | Hill (1979), pp. 3–15, Models 1–100 | Early hydraulic float-valve regulation |
| **Thābit ibn Qurra** | c. `836–901` | Harran / Baghdad | *Amicable Numbers*; *Parabola Quadrature* | Rashed (2009), pp. 3–14, 155–209, 259–290 | Non-uniform rational quadrature |
| **Abū Bakr al-Karajī** | c. `953–1029` | Baghdad | *al-Fakhrī fī al-Jabr wa-l-Muqābala* | Rashed (1994), ch. 1, pp. 22–45 | Polynomial-ring arithmetization |
| **Ibn al-Haytham (Alhazen)** | c. `965–1040` | Basra / Cairo | *Kitāb al-Manāẓir*; *al-Shukūk*; *Sharḥ Muṣādarāt* | Sabra (1989), vol. 2 pp. xix–xxxii; Sabra & Shehaby (1971), pp. 3–42 | Non-constructible optics, parallel-postulate defect |
| **Abū Rayḥān al-Bīrūnī** | `973–1048` | Khwarazm / Ghazna | *Taḥdīd Nihāyāt al-Amākin*; *al-Asʾilah wa-l-Ajwibah* | Ali (1967), pp. 187–190; Kennedy (1973), pp. 139–144 | Continuum vs. atomism; base-60 rounding sensitivity |
| **Ibn Sīnā (Avicenna)** | `980–1037` | Bukhara / Isfahan | *al-Shifāʾ*; *al-Asʾilah wa-l-Ajwibah* | Nasr & Mohaghegh (1995), pp. 1–62 | Continuous magnitude vs. discrete atomism |
| **ʿUmar al-Khayyām** | `1048–1131` | Nishapur / Isfahan | *Sharḥ mā Ashkala min Muṣādarāt Uqlīdis*; *Algebra* | Rashed & Vahabzadeh (2000), pp. 113–162, 217–244 | Quadrilateral curvature trichotomy |
| **Ibn Rushd (Averroes)** | `1126–1198` | Cordoba / Marrakesh | *Tafsīr mā baʿd al-ṭabīʿa* Book $\Lambda$ | Genequand (1984), pp. 176–181; Sabra (1984), pp. 133–153 | Anti-epicycle overparameterization critique |
| **al-Samawʾal al-Maghribī** | c. `1130–1180` | Baghdad / Maragheh | *al-Bāhir fī al-Jabr* | Ahmad & Rashed (1972), pp. 20–58 | Sparse Laurent ring $\mathbb{Q}[x, x^{-1}]$ |
| **Ismāʿīl al-Jazarī** | `1136–1206` | Diyarbakır | *Kitāb fī Maʿrifat al-Ḥiyal al-Handasiyya* | Hill (1974), pp. 17–34, Cat. I ch. 1 | Discrete-time proportional float-valve stability |
| **Naṣīr al-Dīn al-Ṭūsī** | `1201–1274` | Maragheh | *al-Tadhkira fī ʿIlm al-Hayʾa*; *al-Risāla al-Shāfiya* | Ragep (1993), vol. 1 pp. 194–223 (II.11) | Zero-residual Ṭūsī couple |

---

## 2. Pillar 1 — Al-Bīrūnī ↔ Ibn Sīnā Discrete Obstruction & Thābit ibn Qurra's Quadrature

1. **Discrete-Atomism Geometric Obstruction (*al-Asʾilah wa-l-Ajwibah*, Nasr & Mohaghegh 1995, pp. 1–62):**
   - **2-Adic Valuation Parity:** On an $N \times N$ square lattice, equating diagonal and side atom counts requires $M^2 = 2 N^2$. Since $v_2(2 N^2) = 2 v_2(N) + 1$ is odd while $v_2(M^2) = 2 v_2(M)$ is even, no rational solution exists (`all_v2_odd = True`), and identifying the diagonal with the $L_\infty$ lattice induces a `2/1` squared-metric distortion.
   - **Concentric Wheel Slippage:** On rigidly coupled concentric rings of radii `2:1`, stepping the outer ring by `1` indivisible atom forces the inner ring to advance by `1/2` atom (`denominator = 2 != 1`).
2. **Thābit ibn Qurra (`c. 836–901` CE; Rashed 2009, pp. 155–209, 259–290):**
   - **Amicable-Number Precondition:** Exact proper-divisor sums confirm $n = 2 \implies (p, q, r) = (5, 11, 71)$ prime $\implies (220, 284)$ (`is_amicable = True`) and $n = 4 \implies (23, 47, 1151)$ prime $\implies (17{,}296, 18{,}416)$ (`is_amicable = True`), while $n = 3$ gives composite $r = 287 = 7 \times 41$ (`is_amicable = False`).
   - **Non-Uniform Parabola Quadrature:** Partitioning $[0, 1]$ at $x_k = (k/N)^2$ produces exact rational Darboux bounds around `2/3` of width `1/N` (`N = 100`: `13233/20000 < 2/3 < 13433/20000`, width `1/100`).

---

## 3. Pillar 2 — Ibn al-Haytham, ʿUmar al-Khayyām & Ibn Rushd

1. **Ibn al-Haytham's Spherical Mirror Quartic (*Kitāb al-Manāẓir* Book V; Neumann 1998):**
   - Under stereographic Weierstrass parametrization $M(t) = ((1-t^2)/(1+t^2), 2t/(1+t^2))$, the reflection law $(A \times M)(B \cdot M - 1) + (B \times M)(A \cdot M - 1) = 0$ yields:
     - Symmetric `A=(2,1), B=(2,-1)`: $t = 0$ residual **`0/1`**.
     - Asymmetric `A=(2,0), B=(0,3)`: **`P(t) = 9 t^4 + 4 t^3 - 36 t^2 + 4 t + 3 = 0`** (`0` rational roots, `4` real roots isolated via rational sign changes on `(-3, -1, -1/5, 1/2, 3)`).
     - Depressed quartic $y^4 - \frac{110}{27} y^2 + \frac{980}{729} y + \frac{512}{2187} = 0$ has primitive integer Ferrari cubic resolvent **`531441 w^3 - 4330260 w^2 + 8323236 w - 960400 = 0`** (`531441` times the monic standard resolvent) with **`0` rational roots**, certifying $3 \mid |\operatorname{Gal}(P)|$ and straightedge-and-compass non-constructibility purely in $\mathbb{Q}$.
2. **Haytham–Khayyām–Ṭūsī Quadrilateral Curvature Trichotomy (Rashed & Vahabzadeh 2000, pp. 217–244):**
   - Exact Pythagorean-triple summit cosines on a trirectangular quadrilateral: hyperbolic `5/16 > 0` (acute), Euclidean `0/1` (right), spherical `-3/13 < 0` (obtuse).
3. **Ibn Rushd's Anti-Epicycle Toy Witness (Sabra 1984, pp. 133–153):**
   - Interpolating `n_train = 3` points with `dof = 3` parameters gives `0/1` in-sample $L_1$ error and `45/1` held-out error at `x = 10` — a simple algebraic illustration of overparameterization motivating the `dof < held_out_constraints` guard in `certify_bounded_feedback_and_anti_epicycle()`.

---

## 4. Pillar 3 — Al-Khwārizmī, Al-Karajī & Al-Samawʾal

1. **Al-Khwārizmī's 6-Form *al-Jabr wa-l-Muqābala* Canonical Reducer (Rashed 2009, pp. 94–110):**
   - `reduce_khwarizmi_quadratic()` reduces signed rational quadratics into all `6` positive-coefficient canonical forms, verifying Ch. 1's flagship `(2x^2 + 7x - 9) = (x^2 - 3x + 30)` $\to$ `x^2 + 10x = 39` (discriminant `64/1`, positive root `x = 3`).
2. **Al-Karajī & Al-Samawʾal Sparse Laurent Ring $\mathbb{Q}[x, x^{-1}]$ (Ahmad & Rashed 1972, pp. 20–58):**
   - Exact sparse Laurent arithmetic verifies `(3 x^-2) * ((1/3) x^2) = 1`, `(1 - x^-1) * sum_{k=0}^5 x^-k = 1 - x^-6`, and the exact polynomial Schur-complement numerator identity `K_00 K_11 - K_01^2 = q^2(1 - q) - q^2 = -q^3` on `K = [[q^2, q], [q, 1 - q]]`.

---

## 5. Pillar 4 — Al-Kindī, Al-Bīrūnī Geodesy Sensitivity, Al-Ṭūsī Couple & Al-Jazarī Feedback

1. **Al-Kindī (*De Gradibus*, McVaugh 1975; Cryptanalysis, Mrayati et al. 2003):**
   - Verifies exact $2^n$ geometric scaling (`1, 2, 4, 8, 16`) and exact permutation invariance of $L_1$ distance from uniform (`plain_l1 == cipher_l1 == 1/2 > 0`).
2. **Al-Bīrūnī's Nandana Geodesy (*Taḥdīd*, c. `1025` CE) — Historical Inputs & Sexagesimal Truncation Hypothesis:**
   - **Published Inputs:** Jamil Ali (trans.), *The Determination of the Coordinates of Positions* (Beirut: AUB, 1967), pp. 187–190; E. S. Kennedy, *A Commentary upon Bīrūnī's Kitāb Taḥdīd al-Amākin* (Beirut: AUB, 1973), pp. 139–144: mountain height `h = 652;03,18 = 652.055` cubits, horizon dip `theta = 34'`, reported radius `12,803,337;02,09` cubits.
   - **Exact Pure-$\mathbb{Q}$ Taylor Bracket (Conservative):** `R(34') in [13,331,619.621397, 13,331,728.382993]` cubits (lower floored, upper ceiled).
   - **Base-60 Truncation Sensitivity Table (`cos(34') = 0; 59, 59, 49, 26, 09, ...`):**

| Sexagesimal Places Kept | Truncated $\cos(34')$ | Exact Fraction | Computed Radius $R$ (cubits) |
| :---: | :--- | :---: | :---: |
| `2` places | `0; 59, 59` | `3599 / 3600` | `2,346,745.945000` |
| **`3` places** | **`0; 59, 59, 49`** | **`215989 / 216000`** | **`12,803,337.035909` (`28167341479 / 2200`)** |
| `4` places | `0; 59, 59, 49, 26` | `6479683 / 6480000` | `13,328,421.762034` |
| `5` places | `0; 59, 59, 49, 26, 09` | `259187323 / 259200000` | `13,331,576.074683` |

   - **Epistemic Status (`ARITHMETIC_FIT_HYPOTHESIS_SINGLE_NUMBER`):** While the `3`-place arithmetic reproduces `12,803,337` to within `0.036` cubits (specifically `12,803,337;02,09` in base 60), the match is specific to cutting at `3` places and is fitted to a single reported number. It is therefore labelled strictly as an **arithmetic fit / hypothesis**, not archival proof of al-Bīrūnī's exact intermediate table lookup (see Kennedy 1973, pp. 139–144, for historical analysis of al-Bīrūnī's intermediate sine/cosine steps). Astrolabe dip sensitivity (`33'` $\to$ `14,151,987.5`; `35'` $\to$ `12,580,767.8`) and terrestrial refraction bias `1/(1 - 1/7) = 7/6` are also computed in exact $\mathbb{Q}$.
3. **Naṣīr al-Dīn al-Ṭūsī's Ṭūsī Couple (*al-Tadhkira* II.11; Ragep 1993, vol. 1 pp. 194–223):**
   - Across `7` rational Weierstrass points $t = \tan(\theta/2)$, exact transverse residual `P_y(t) == 0/1` identically.
4. **Ismāʿīl al-Jazarī's Float-Valve Dynamics (*Kitāb al-Ḥiyal*; Hill 1974, pp. 17–34):**
   - Discrete-time pure-$\mathbb{Q}$ trajectories $e_{k+1} = (1 - \mu) e_k$ ($\mu = \kappa \Delta t / A$) illustrate monotone convergence (`mu=1/2`), damped oscillation (`mu=3/2`), period-2 hunting (`mu=2`), and divergence (`mu=5/2`). `certify_bounded_feedback_and_anti_epicycle()` checks the DOF/null/in-sample constraints, `0 < mu < 2`, and proportional operating-band headroom `linear_head_margin * 10 >= setpoint`.

---

## 6. Law-4 Historical `N0` Attribution

- **`N0` Classification:** All mathematical theorems, constructions, historical treatises, and published scholarly editions cited above are classical prior art (`N0`). No `N1` mathematical novelty is claimed here; this package provides a self-contained pure-$\mathbb{Q}$ Python 3 stdlib transcription, arithmetic verification suite, and fail-closed encoding-consistency checker.

---

## 7. Reproducibility & Verification Receipts

- **Self-Contained Offline Reproduction (Python 3 stdlib only, zero external files required):**
  - `python3 -I -O -B -W error bayt_al_hikma_polymath_certifier.py --json` reproduces [bayt_al_hikma_polymath_certificate.json](bayt_al_hikma_polymath_certificate.json) **byte-for-byte** (`certificate_sha256: 4834f376d7668430c3838e46bb4dd34440a7363fb4d48dc8c4191afc1b07ee2d`, `execution_mode: standalone_pure_q`, `honest_tier: N0`, `0` floats).
  - `python3 -I -O -B -W error test_bayt_al_hikma_polymaths_r5.py` runs `10/10` tests OK (`0` skipped) across all isolated modes (`-I -B`, `-I -O -B`, `-I -B -W error`).
- **External Aletheia v2.0.0 Verification (`Foundation-0/aletheia#1`, external tool not bundled in this repo):**
  - Author seat: `fractals-probe`; independent clean-room verifier seat: `verifier`.
  - `aletheia v2.0.0 audit-check . --strict-ancestors --safety-scan --scripts bayt_al_hikma_polymath_certifier.py test_bayt_al_hikma_polymaths_r5.py`: **`PASS`** (`4` files, `2/2` R4, `0` safety findings, `0` bare `assert`s, `0` floats, `0` `/home/` or `file:///` leaks, `0` CRLF, `0` `__pycache__`).
  - `aletheia v2.0.0 mutate bayt_al_hikma_polymath_certifier.py --work-root . --add-cwd --max-mutants 0 --test-cmd "python3 -I -O -B -W error test_bayt_al_hikma_polymaths_r5.py"`: **`83/83` (`100.0%`, `truncated: false`) KILLED, `0` survivors**.
