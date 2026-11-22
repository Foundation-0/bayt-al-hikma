# AUDIT-095: Bayt al-Hikma Tributary Veins & Downstream Branches — Pure-$\mathbb{Q}$ Cartography

**Track:** Wave 3b Track 2 / Lane C (`bayt-al-hikma-veins-and-branches/`)  
**Certifier:** [bayt_al_hikma_veins_certifier.py](bayt_al_hikma_veins_certifier.py) (pure Python 3 stdlib, ZERO floats)  
**R5 Test Suite:** [test_bayt_al_hikma_veins_r5.py](test_bayt_al_hikma_veins_r5.py)  
**Certificate:** [bayt_al_hikma_veins_certificate.json](bayt_al_hikma_veins_certificate.json)  
**Honest Novelty Classification:** **`N1`** (engineering verification engine, pure-integer interval arithmetic, and fail-closed certifiers; ALL historical theorems credited strictly as **`N0`** prior art to their original authors).

---

## 1. Executive Summary & Architectural Bridge

Where `AUDIT-092R` mapped the `13`-scholar Baghdad–Cairo–Khwarazm–Cordoba core of the **Bayt al-Hikma** lineage, **`AUDIT-095`** widens the verified mathematical river basin across **`23` scholars and `28` directed/correspondence edges (`c. 287 BCE – 1543 CE`)**, proving in zero-float pure $\mathbb{Q}$ how pre-Abbasid **tributary veins** (Indian *Brāhmasphuṭasiddhānta* + Greek/Syriac Alexandria/Syracuse via Gundishapur, Ḥunayn ibn Isḥāq, Banū Mūsā, and Thābit ibn Qurra) fused inside Bayt al-Hikma and branched into **Damascus, Marāgha, Samarkand, Cordoba, and Renaissance Europe**.

Three live read-only SHA-256 vault cross-links anchor this study directly into the expedition fabric:
1. [bayt_al_hikma_polymath_certificate.json](../polymath-lineage/bayt_al_hikma_polymath_certificate.json) (`AUDIT-092R`, `c052a62a...`) — `13`-scholar Bayt al-Hikma core certificate.
2. [arabic_continuum_certificate.json](../arabic-continuum/arabic_continuum_certificate.json) (`AUDIT-091R`, `aa860805...`) — Classical Arabic `OWN_TERMS_FIRST` continuum certificate.
3. [continuum.md](https://github.com/Foundation-0/continuum/pull/1) (`516f6080...`) — `Foundation-0/continuum` primary portal (directly bridged by Pillar 4's Al-Fārābī acoustic continuum vs. 12-TET bucketization defect).

---

## 2. Pillar 1 — Tributary Veins Feeding Bayt al-Hikma

### 2A. Indian Vein: Brahmagupta (*Brāhmasphuṭasiddhānta*, `628` CE) & Chakravala
Transmitted to Abbasid Baghdad via the `771/773` CE *Zīj al-Sindhind* embassy and directly absorbed by al-Khwārizmī:
- **Brahmagupta's Cyclic Quadrilateral (*BSS* XII.38):** On integer-vertex cyclic quadrilateral `(15,0), (0,36), (-48,0), (0,-20)` (intersecting chords `15 * 48 == 36 * 20 == 720`), sides `(39, 60, 52, 25)` and semiperimeter `s = 88`:
  - Exact area formula $K^2 = (s-a)(s-b)(s-c)(s-d) = 49 \cdot 28 \cdot 36 \cdot 63 = \mathbf{1764^2}$, matching perpendicular diagonals `e = 63, f = 56` (`ef/2 = 1764`).
  - Exact **Brahmagupta diagonal formulas** $e^2 = \frac{(ac+bd)(ad+bc)}{ab+cd} = 63^2$, $f^2 = \frac{(ac+bd)(ab+cd)}{ad+bc} = 56^2$, and exact **Ptolemy identity** `ef = ac + bd = 3528`.
  - Exact **circumdiameter** $a^2 + c^2 = b^2 + d^2 = 65^2 \implies R = \mathbf{65/2}$ and **Brahmagupta's perpendicular-bisector theorem**: the line through the diagonal intersection perpendicular to side `AD` `(15, 20)` has zero inner product (`0/1`) with the midpoint `(-24, 18)` of opposite side `BC`.
- **Brahmagupta–Fibonacci *Bhāvanā* Composition & Exact Pell / Chakravala Solver:**
  - Verifies exact norm multiplicativity $(x_1^2 - D y_1^2)(x_2^2 - D y_2^2) = (x_1 x_2 + D y_1 y_2)^2 - D(x_1 y_2 + x_2 y_1)^2$ on Brahmagupta's classic challenge **`D = 92`** (*BSS* XVIII.67), deriving the exact fundamental solution **`(1151, 120)`** (`1151^2 - 92 * 120^2 == 1`) from `(10, 1, k=8)`.
  - Runs the pure exact-integer **Jayadeva / Bhāskara II Chakravala algorithm** on **`D = 61`**, certifying the exact `14`-step convergence to **`x = 1,766,319,049`, `y = 226,153,980`** (`x^2 - 61 y^2 == 1`).

### 2B. Greek / Syriac Vein: Alexandria & Syracuse → Gundishapur, Ḥunayn, Banū Mūsā, Thābit
- **Heron of Alexandria (*Metrica*, c. `60` CE → Banū Mūsā Theorem 7):** Unifies Heron's triangle area formula as the exact `d = 0` degenerate limit of Brahmagupta's cyclic-quadrilateral formula on `(13, 14, 15, 0) -> K^2 = 7056 = 84^2`, and certifies Heron's *Metrica* I.8 pure-$\mathbb{Q}$ Babylonian bracket for $\sqrt{720} \in [26.832815729..., 26.832815729...]$.
- **Archimedes (*Measurement of a Circle*, c. `250` BCE → Banū Mūsā Theorems 4–6):** Executes the pure-integer half-angle polygon recurrence for `k = 4` doublings (`96`-gon), strictly certifying:
  $$\frac{223}{71} < 3.141031 < \pi < 3.142714 < \frac{22}{7}$$
  — establishing the exact geometric bridge to Pillar 3's Samarkand `3 * 2^28`-gon!
- **Apollonius (*Conics*, Books V–VII preserved ONLY via Banū Mūsā & Thābit ibn Qurra):** Certifies Banū Mūsā's string ("gardener's") ellipse construction & optical focal-reflection property on the exact rational Pythagorean ellipse $(x/5)^2 + (y/4)^2 = 1$ at `P = (3, 16/5)` with foci `(±3, 0)`: `d1 = 16/5`, `d2 = 34/5`, `d1 + d2 = 10 = 2a`, and equal inward-normal unit-ray inner products `dot1 == dot2 == 5/1`.

---

## 3. Pillar 2 — Downstream Astronomical & Causal Branches

### 3A. Ibn al-Shāṭir (Damascus, `1304–1375`) ↔ Nicolaus Copernicus (`1543`)
- **Removal of Ptolemy's Catastrophic Lunar Distance Defect:**
  - **Ptolemy (*Almagest* V):** Eccentric + crank mechanism forces $d_{\max}/d_{\min} = \mathbf{3915/2047 \approx 1.912554}$ (predicting an unphysical nearly `2×` lunar apparent-diameter variation).
  - **Ibn al-Shāṭir (*Nihāyat al-Sūl*):** Concentric deferent `R = 60` + zero-equant double epicycle `r1 = 6;35 = 79/12`, `r2 = 1;25 = 17/12` yields syzygy radius `r1 - r2 = 31/6 (5;10)`, quadrature radius `r1 + r2 = 8 (8;00)`, and realistic distance ratio **`17/13 ≈ 1.307692`**.
  - **Copernicus (*De Revolutionibus* IV.3):** Uses `R = 10000, r1 = 1097, r2 = 237` (`d_max/d_min = 5667/4333 ≈ 1.307869`), with total normalized $L_1$ parameter discrepancy across both epicycles of just **`1/9000 ≈ 0.000111`** (`< 0.012%`!).
- **Exact Zero-Residual Kinematic Equivalence:** Across rational Weierstrass anomaly/elongation pairs `(tan(a/2), tan(e/2))`, Ibn al-Shāṭir's and Copernicus's normalized lunar double-epicycle vectors agree with **`0/1` residual identically**, and their shared Mercury Ṭūsī-couple radial oscillation `r_eff = r0 + a cos(2e)` exhibits **`0/1` transverse residual identically**.

### 3B. Al-Ghazālī (*Tahāfut al-Falāsifa*, `1095`) ↔ Ibn Rushd (*Tahāfut al-Tahāfut*, `1180`)
- **Pure-$\mathbb{Q}$ Structural-Causal & Counterfactual Intervention Witness (Fire & Cotton, 17th Discussion):**
  - Constructs two exact binary structural models `(U, F, C)`:
    1. **Ibn Rushd direct structural mechanism (`F -> C`):** $P(F=1)=1/2$, $P(C=1 \mid F=1) = 17/25$, $P(C=1 \mid F=0) = 8/25$.
    2. **Al-Ghazālī common-cause / *iqtirān* model (`F <- U -> C`, NO edge `F -> C`):** $P(U=1)=1/2$, $P(F=1 \mid U=1)=P(C=1 \mid U=1)=4/5$, $P(F=1 \mid U=0)=P(C=1 \mid U=0)=1/5$.
  - **Exact Non-Identifiability (`Al-Ghazālī`):** Both models induce the **EXACT SAME observational joint distribution** `p11 = 17/50, p10 = 4/25, p01 = 4/25, p00 = 17/50` (**`obs_l1 == 0/1`**), certifying rigorously that observational conjunction alone CANNOT logically distinguish necessary causation from hidden common cause!
  - **Exact Interventional Separation (`Ibn Rushd`):** Under `do(F=1)` vs. `do(F=0)`, $\mathrm{ATE}_{\text{Rushd}} = \mathbf{9/25}$ whereas $\mathrm{ATE}_{\text{Ghazali}} = \mathbf{0/1}$ — proving **`9/25` interventional separation** and formalizing the medieval debate directly in Pearl's `do`-calculus hierarchy.

---

## 4. Pillar 3 — Samarkand Precision Analysis: Jamshīd al-Kāshī (`1380–1429`)

### 4A. Exact Banach Contraction Fixed-Point Cubic Solver for $\sin(1^\circ)$ (*Risālat al-Watar wa-l-Jayb*, `1427`)
- Rewrites $\sin(3^\circ) = 3x - 4x^3$ as $T(x) = (\sin 3^\circ + 4x^3)/3$ on `[0, 1/50]`:
  - **Certified Lipschitz Constant:** $\sup_{[0, 1/50]} |T'(x)| = 4 (1/50)^2 = \mathbf{1/625 < 1}$.
  - Computing $\sin(3^\circ) = \sin(75^\circ - 72^\circ)$ purely via certified `10^35`-scale integer `isqrt` interval arithmetic, `7` monotone iterations pin $\sin(1^\circ) \in [0.017452406437283512, 0.017452406437283512]$ with cubic residual **`< 10^-18`**.
  - **Exact Historical Verification:** Matches al-Kāshī's `1427` CE 10-place sexagesimal value `0; 1, 2, 49, 43, 11, 14, 44, 16, 26, 17` across **all first 9 sexagesimal places (`0; 1, 2, 49, 43, 11, 14, 44, 16, 26`)** with max difference **`< 10^-17`** (`1` unit in the 10th base-60 place!).

### 4B. Certified Pure-Integer $3 \cdot 2^{28} = 805,306,368$-gon $\pi$ Bracket (*al-Risāla al-Muḥīṭiyya*, `1424`)
- Executing the exact same pure-integer half-angle polygon recurrence as Archimedes (Pillar 1B) for `27` doublings from the hexagon (`6 * 2^27 = 805,306,368` sides) at scale `10^35` with strictly conservative integer rounding proves with ZERO floats:
  - $2\pi \in [\mathbf{6; 16, 59, 28, 01, 34, 51, 46, 14, 49, 45},\ \mathbf{6; 16, 59, 28, 01, 34, 51, 46, 14, 50, 14}]$ — **strictly bracketing al-Kāshī's 1424 CE 9-place sexagesimal value `6; 16, 59, 28, 01, 34, 51, 46, 14, 50`!**
  - Base-10 agreement to **`16` exact decimal digits (`3.1415926535897932`)**, tightening Archimedes's `96`-gon width (`~2.0 × 10^-3`) by **`> 10^{13}×`** (`width < 10^-16`).

---

## 5. Pillar 4 — Al-Fārābī's Acoustic Continuum vs. Discrete 12-TET Bucketization

In *Kitāb al-Mūsīqā al-Kabīr* (`c. 940` CE), **Abū Naṣr al-Fārābī** formalized the Arabic *ʿūd* fret continuum via exact 11-limit rational ratios:
- **Exact Tetrachord Identities:** `(9/8) * (12/11) == 27/22` (Zalzal's neutral third), `(9/8) * (12/11) * (88/81) == 4/3`, and superparticular `(12/11) * (11/10) * (10/9) == 4/3`; exact **Pythagorean comma** `(3/2)^12 / 2^7 == 531441/524288 > 1`.
- **Pure-Integer Incommensurability & 12-TET Quantization Defect (`0` floats, `0` logs):**
  By unique prime factorization, no ratio with odd prime factors (`3, 11`) equals any 12-TET semitone $2^{k/12}$. Comparing $r^{1200}$ directly against integer powers $2^c$ yields exact integer cent brackets:

| Al-Fārābī / Zalzal Ratio | Exact Fraction | Exact Cent Bracket | Nearest 12-TET Bucket | Min Rounding Defect |
| :--- | :---: | :---: | :---: | :---: |
| Three-quarter tone | `12/11` | `(150, 151)` | `200` (semitone 2) | **`>= 49` cents (`98%` of 50c worst case!)** |
| Zalzal neutral third | `27/22` | `(354, 355)` | `400` (semitone 4) | **`>= 45` cents** |
| Tetrachord complement | `88/81` | `(143, 144)` | `100` (semitone 1) | **`>= 43` cents** |
| Whole tone | `9/8` | `(203, 204)` | `200` (semitone 2) | `>= 3` cents |
| Perfect fourth | `4/3` | `(498, 499)` | `500` (semitone 5) | `>= 1` cent |
| Perfect fifth | `3/2` | `(701, 702)` | `700` (semitone 7) | `>= 1` cent |

- **`OWN_TERMS_FIRST` / `continuum` Bridge:** Discrete 12-TET bucketization appears deceptively benign on Western 3-limit fifths/fourths (`~2` cents error), yet inflicts **`45–49` cents of catastrophic rounding distortion** on al-Fārābī's 11-limit *maqām* continuum — directly paralleling the discrete semantic-projection defect of Classical Arabic (`AUDIT-091R`) and the grid-metric defect of `Foundation-0/continuum` (`AUDIT-088R`).

---

## 6. Pillar 5 — Two Fail-Closed Pure-$\mathbb{Q}$ Certifiers & Law-4 Attribution

1. **`certify_extended_polymath_dag(nodes, edges)`:** Certifies the `23`-scholar (`4` tributaries, `15` core, `4` downstream branches), `28`-edge lineage graph across `3` tiers (`tributary -> core -> branch`), enforcing strict ASCII/no-dup/no-self-loop refusals, tier epoch bounds (`tributary: death <= 750`, `core: 750 <= birth <= 1150`, `branch: birth >= 1200`), forward tier monotonicity (and same-tier correspondence), full scholarly-maturity chronology (`teacher_of`, `corresponded_with`, `extended`/`commented_on`/`critiqued` for BOTH source and target), exact 3-color DFS DAG acyclicity, AND directed `tributary ->+ core ->+ branch` bridge reachability (blocking vacuous empty-edge certificates).
2. **`certify_contraction_and_causal_identifiability(spec)`:** Unified fail-closed certifier combining al-Kāshī's Banach fixed-point criteria (strict contraction `0 <= L < 1`, self-map invariance ball `x0 ± step0_gap/(1-L) ⊆ [domain_lo, domain_hi]`, and a-priori tolerance `L^k * step0_gap / (1-L) <= target_tol`) with al-Ghazālī / Ibn Rushd causal identifiability (recomputing the exact `U -> F, U -> C` confounded joint distribution from primitives to defeat joint spoofing, enforcing non-degenerate marginals, `obs_l1 == 0`, and `|ATE_direct - ATE_confounded| >= min_ate_separation`).

- **`N0` Historical Prior Art:** Archimedes, Apollonius, Heron, Brahmagupta, Bhāskara II/Jayadeva, al-Khwārizmī, al-Kindī, Banū Mūsā, Ḥunayn ibn Isḥāq, Thābit ibn Qurra, al-Fārābī, al-Karajī, Ibn al-Haytham, al-Bīrūnī, Ibn Sīnā, ʿUmar al-Khayyām, al-Ghazālī, al-Samawʾal, Ibn Rushd, Ismāʿīl al-Jazarī, Naṣīr al-Dīn al-Ṭūsī, Ibn al-Shāṭir, Jamshīd al-Kāshī, and Nicolaus Copernicus.
- **`N1` Engineering & Verification Contribution:** Pure-$\mathbb{Q}$ zero-float verification engine, certified pure-integer `3 * 2^28`-gon $\pi$ and Banach $\sin(1^\circ)$ solvers, pure-integer cent-resolution 12-TET acoustic defect proof, structural-causal witness, and two `100.0%`-R5-killed fail-closed certifiers.

---

## 7. Reproducibility & Verification Receipts (Aletheia v2.0.0)

- **Live-anchored certificate:** [bayt_al_hikma_veins_certificate.json](bayt_al_hikma_veins_certificate.json) (`certificate_sha256: e495d9bcfdf15a77147cc82d5f4c8f96eb68812d7c08cbad3ef0d470640c282d`, `3/3` vault cross-links verified, `0` floats).
- **Standalone pure-$\mathbb{Q}$ certificate:** `certificate_sha256: 0d1bdb3b13edddbf0b1842931fe2fb93db0ebc03ff5b2f6bbe88f8cedd46d910`.
- **Aletheia v2.0.0 Audit & Safety Gate:** `aletheia audit-check . --strict-ancestors --safety-scan --scripts bayt_al_hikma_veins_certifier.py test_bayt_al_hikma_veins_r5.py` `PASS` (`4` files, `0` defects, `0` safety findings, `8/8` ancestor dirs clean, `0` bare `assert`s, `0` floats, `0` `/home/` or `file:///` leaks, `0` CRLF, `0` `__pycache__`).
- **R4 Determinism:** `4/4` isolated `python3 -I -O -B -W error` runs bit-identical (`live --json`, `standalone --json`, human summary, `test_bayt_al_hikma_veins_r5.py` `10/10` OK, `0` skipped).
- **R5 Mutation Gate:** `aletheia v2.0.0 mutate bayt_al_hikma_veins_certifier.py --work-root . --add-cwd --max-mutants 0 --test-cmd "python3 -I -O -B -W error test_bayt_al_hikma_veins_r5.py"` **`110/110` (`100.0%`) KILLED, `0` survivors**.
