# AUDIT-095R: Bayt al-Hikma Tributary Veins & Downstream Branches — Pure-$\mathbb{Q}$ Verification & Encoding-Consistency Checks

> **Audit ID:** `AUDIT-095R`  
> **Certifier:** [bayt_al_hikma_veins_certifier.py](bayt_al_hikma_veins_certifier.py) (pure Python 3 stdlib, ZERO floats)  
> **R5 Test Suite:** [test_bayt_al_hikma_veins_r5.py](test_bayt_al_hikma_veins_r5.py)  
> **Certificate:** [bayt_al_hikma_veins_certificate.json](bayt_al_hikma_veins_certificate.json)  
> **Novelty Classification (Law 4):** **`N0`** (all mathematical theorems, historical figures, and published editions are classical prior art; this package provides a self-contained pure-$\mathbb{Q}$ stdlib transcription, strictly conservative interval arithmetic, and encoding-consistency checks without claiming `N1` novelty).

---

## 1. Scope & Conceptual Motivation

Expanding on the `13`-scholar core transcription in [BAYT_AL_HIKMA_POLYMATH_REPORT.md](../polymath-lineage/BAYT_AL_HIKMA_POLYMATH_REPORT.md), **`AUDIT-095R`** encodes **`23` scholars and `28` cited relations (`c. 287 BCE – 1543 CE`)** spanning pre-Abbasid **tributary veins** (India and Hellenistic Alexandria/Syracuse), the **Baghdad–Cairo–Cordoba classical lineage**, and **downstream Marāgha, Damascus, Samarkand, and European branches**, verifying classical mathematical constructions purely in exact $\mathbb{Q}$ with zero floating-point arithmetic.

Any parallels drawn to modern continuum-vs-discrete modeling, causal inference, or fixed-point analysis are **conceptual parallels / motivating analogies** only, not machine-verified cross-repository maps. No external non-repository vault files are required to reproduce the committed certificate.

---

## 2. Pillar 1 — Tributary Veins Feeding Bayt al-Hikma

### 2A. Indian Vein: Brahmagupta (*Brāhmasphuṭasiddhānta*, `628` CE) & Chakravala
Published editions: H. T. Colebrooke (1817); K. Plofker, *Mathematics in India* (Princeton UP, 2009), pp. 142–157, 255–259; O. Neugebauer (1962), pp. 1–14:
- **Brahmagupta's Cyclic Quadrilateral (*BSS* XII.38):** Integer-vertex cyclic quadrilateral `(15,0), (0,36), (-48,0), (0,-20)` (intersecting chords `15 * 48 == 36 * 20 == 720`), sides `(39, 60, 52, 25)`, semiperimeter `s = 88`:
  - Exact area formula $K^2 = (s-a)(s-b)(s-c)(s-d) = 49 \cdot 28 \cdot 36 \cdot 63 = \mathbf{1764^2}$, matching perpendicular diagonals `e = 63, f = 56` (`ef/2 = 1764`).
  - Exact Brahmagupta diagonal formulas $e^2 = \frac{(ac+bd)(ad+bc)}{ab+cd} = 63^2$, $f^2 = \frac{(ac+bd)(ab+cd)}{ad+bc} = 56^2$, and Ptolemy identity `ef = ac + bd = 3528`.
  - Exact circumdiameter $a^2 + c^2 = b^2 + d^2 = 65^2 \implies R = \mathbf{65/2}$ and perpendicular-bisector orthogonality dot product `0/1` through the midpoint `(-24, 18)` of `BC`.
- **Brahmagupta–Fibonacci *Bhāvanā* Composition & Exact Pell / Chakravala Solver:**
  - Verifies exact norm multiplicativity $(x_1^2 - D y_1^2)(x_2^2 - D y_2^2) = (x_1 x_2 + D y_1 y_2)^2 - D(x_1 y_2 + x_2 y_1)^2$ on Brahmagupta's challenge **`D = 92`** (*BSS* XVIII.67), deriving **`(1151, 120)`** (`1151^2 - 92 * 120^2 == 1`).
  - Runs the pure exact-integer **Jayadeva / Bhāskara II Chakravala algorithm** on **`D = 61`**, reaching **`x = 1,766,319,049`, `y = 226,153,980`** (`x^2 - 61 y^2 == 1`) in **`13` iteration steps** (`14` table rows including the starting state `(8, 1, 3)`).

### 2B. Greek / Syriac Vein: Alexandria & Syracuse → Banū Mūsā, Ḥunayn & Thābit
Published editions: T. L. Heath (1897), pp. 91–98; M. Clagett, *Archimedes in the Middle Ages*, Vol. 1 (*Verba Filiorum*, Univ. of Wisconsin Press, 1964), pp. 223–367; G. J. Toomer, *Apollonius: Conics Books V to VII* (Springer, 1990), vol. 1 pp. xi–xxv; R. Rashed (2009), pp. 155–209:
- **Heron of Alexandria (*Metrica* I.8 → Banū Mūsā Prop. 7):** Verifies Heron's triangle area formula as the `d = 0` limit of Brahmagupta's formula on `(13, 14, 15, 0) -> K^2 = 7056 = 84^2`, and certifies Heron's pure-$\mathbb{Q}$ conservative bracket for $\sqrt{720} \in [26.832815729, 26.832815730]$ (lower floored, upper ceiled).
- **Archimedes (*Measurement of a Circle*, Prop. 3 → Banū Mūsā Props. 4–6):** Pure-integer half-angle polygon recurrence for `k = 4` doublings (`96`-gon), strictly certifying the conservative outer decimal bracket (lower floored below `3.141031950...`, upper ceiled strictly above `3.142714599...`):
  $$\frac{223}{71} < 3.141031 < \pi < \mathbf{3.142715} < \frac{22}{7}$$
- **Apollonius (*Conics* V–VII, preserved in Arabic via Banū Mūsā & Thābit ibn Qurra):** Verifies the rational Pythagorean ellipse $(x/5)^2 + (y/4)^2 = 1$ at `P = (3, 16/5)` with foci `(±3, 0)`: `d1 = 16/5`, `d2 = 34/5`, `d1 + d2 = 10 = 2a`, and equal inward-normal unit-ray inner products `dot1 == dot2 == 5/1`.

---

## 3. Pillar 2 — Downstream Astronomical & Causal Studies

### 3A. Ibn al-Shāṭir (Damascus, `1304–1375`) ↔ Nicolaus Copernicus (`1543`)
Published editions: V. Roberts, *Isis* 48 (1957), pp. 428–432; E. S. Kennedy & V. Roberts, *Isis* 50 (1959), pp. 227–235; E. Rosen (tr.), *On the Revolutions* (1978), III.4, IV.3, V.25; F. J. Ragep (1993), vol. 2 pp. 429–431; G. Saliba (2007), pp. 193–209. *(Historiographic note: the mathematical kinematic equivalence of the models below is exact; whether and by what manuscript route Copernicus had access to Marāgha/Damascus texts remains an open topic in the history of astronomy.)*
- **Lunar Distance Ratios:**
  - **Ptolemy (*Almagest* V):** $d_{\max}/d_{\min} = \mathbf{3915/2047 \approx 1.912554}$.
  - **Ibn al-Shāṭir (*Nihāyat al-Sūl*):** Concentric deferent `R = 60`, double epicycle `r1 = 6;35 = 79/12`, `r2 = 1;25 = 17/12` $\implies$ syzygy `31/6 (5;10)`, quadrature `8 (8;00)`, distance ratio **`17/13 ≈ 1.307692`**.
  - **Copernicus (*De Revolutionibus* IV.3):** `R = 10000, r1 = 1097, r2 = 237` $\implies$ distance ratio **`5667/4333 ≈ 1.307869`**, with total normalized $L_1$ parameter discrepancy across both epicycles of **`1/9000 ≈ 0.000111`**.
- **Exact Structural Vector Equivalence:** Across rational Weierstrass anomaly/elongation pairs, normalized double-epicycle vectors agree with **`0/1` residual identically**, and the Mercury Ṭūsī-couple radial oscillation exhibits **`0/1` transverse residual identically**.

### 3B. Al-Ghazālī (*Tahāfut al-Falāsifa*, `1095`) ↔ Ibn Rushd (*Tahāfut al-Tahāfut*, `1180`)
Published editions: M. E. Marmura (2000), Discussion 17, pp. 166–177; S. van den Bergh (1954), vol. 1 pp. 316–333.
- **Pure-$\mathbb{Q}$ Binary Structural-Causal Witness (Conceptual Parallel to Discussion 17):**
  - **Direct mechanism (`F -> C`):** $P(F=1)=1/2$, $P(C=1 \mid F=1)=17/25$, $P(C=1 \mid F=0)=8/25$.
  - **Confounded common-cause model (`F <- U -> C`, no `F -> C` edge):** $P(U=1)=1/2$, $P(F=1 \mid U=1)=P(C=1 \mid U=1)=4/5$, $P(F=1 \mid U=0)=P(C=1 \mid U=0)=1/5$.
  - Both induce the **identical observational joint distribution** `(p11=17/50, p10=4/25, p01=4/25, p00=17/50)` (`obs_l1 == 0/1`), while under `do(F=1)` vs. `do(F=0)`, $\mathrm{ATE}_{\text{direct}} = \mathbf{9/25}$ vs. $\mathrm{ATE}_{\text{confounded}} = \mathbf{0/1}$.

---

## 4. Pillar 3 — Samarkand Precision Analysis: Jamshīd al-Kāshī (`1380–1429`)

Published editions: P. Luckey, *Der Lehrbrief über den Kreisumfang* (Berlin, 1953), pp. 1–42; J. L. Berggren, *Episodes in the Mathematics of Medieval Islam* (Springer, 1986), pp. 50–55, 134–141.

### 4A. Banach Contraction Fixed-Point Cubic Solver for $\sin(1^\circ)$ (*Risālat al-Watar wa-l-Jayb*, `1427`)
- Rewrites $\sin(3^\circ) = 3x - 4x^3$ as $T(x) = (\sin 3^\circ + 4x^3)/3$ on `[0, 1/50]` with exact Lipschitz bound $\sup_{[0, 1/50]} |T'(x)| = \mathbf{1/625 < 1}$.
- Pure-integer `10^35`-scale conservative interval arithmetic for $\sin(3^\circ) = \sin(75^\circ - 72^\circ)$ followed by `7` monotone iterations brackets $\sin(1^\circ) \in [0.017452406437283512, 0.017452406437283513]$ (cubic residual `< 10^-18`), matching al-Kāshī's `1427` CE 10-place base-60 value `0; 1, 2, 49, 43, 11, 14, 44, 16, 26, 17` across all first `9` sexagesimal places (`max diff < 10^-17`).

### 4B. Certified Pure-Integer $3 \cdot 2^{28} = 805,306,368$-gon $\pi$ Bracket (*al-Risāla al-Muḥīṭiyya*, `1424`)
- Executing `27` pure-integer half-angle doublings from the hexagon (`6 * 2^27 = 805,306,368` sides) at scale `10^35` with strictly conservative rounding certifies:
  - **Conservative 10-place base-60 outer bracket for $2\pi$:** $[6; 16, 59, 28, 01, 34, 51, 46, 14, 49, 45,\ 6; 16, 59, 28, 01, 34, 51, 46, 14, 50, 15]$ (lower floored, upper ceiled; width `30 / 60^10` for $2\pi$, i.e. `2.481 × 10^-17` for $\pi$; note that the 10-place floored-upper display difference `29 / 60^10` has width **`4.796 × 10^-17`** for $2\pi$ and **`2.398 × 10^-17`** for $\pi$).
  - **Exact unrounded rational polygon bracket width:** `pi_hi - pi_lo <= 2.416352 × 10^-17` (`twopi_hi - twopi_lo <= 4.832703 × 10^-17`).
  - **Conservative decimal outer bracket:** `3.14159265358979323 < pi < 3.14159265358979326` (confirming `16` exact decimal digits `3.1415926535897932`) and strictly containing al-Kāshī's `1424` CE 9-place sexagesimal $2\pi = 6; 16, 59, 28, 01, 34, 51, 46, 14, 50$.

---

## 5. Pillar 4 — Al-Fārābī's 11-Limit Ratios vs. 12-TET Discrete Rounding

Published edition: R. d'Erlanger, *La Musique Arabe*, Vols. 1–2 (Geuthner, 1930–1935), vol. 1 pp. 163–218 (*Kitāb al-Mūsīqā al-Kabīr*, c. `940` CE):
- Exact identities: `(9/8) * (12/11) == 27/22`, `(9/8) * (12/11) * (88/81) == 4/3`, `(12/11) * (11/10) * (10/9) == 4/3`, and Pythagorean comma `(3/2)^12 / 2^7 == 531441/524288 > 1`.
- Comparing exact integer powers $r^{1200}$ against $2^c$ (`0` floats, `0` logs) establishes exact cent brackets and guaranteed lower bounds on 12-TET nearest-semitone rounding error:

| Al-Fārābī / Zalzal Ratio | Exact Fraction | Exact Cent Bracket | Nearest 12-TET Bucket | Min Rounding Defect |
| :--- | :---: | :---: | :---: | :---: |
| Three-quarter tone | `12/11` | `(150, 151)` | `200` (semitone 2) | **`>= 49` cents** |
| Zalzal neutral third | `27/22` | `(354, 355)` | `400` (semitone 4) | **`>= 45` cents** |
| Tetrachord complement | `88/81` | `(143, 144)` | `100` (semitone 1) | **`>= 43` cents** |
| Whole tone | `9/8` | `(203, 204)` | `200` (semitone 2) | `>= 3` cents |
| Perfect fourth | `4/3` | `(498, 499)` | `500` (semitone 5) | `>= 1` cent |
| Perfect fifth | `3/2` | `(701, 702)` | `700` (semitone 7) | `>= 1` cent |

---

## 6. Pillar 5 — Fail-Closed Encoding-Consistency & Mathematical Certifiers

**Edge Direction Convention (Active Voice):** Every edge `{source, target, relation, citation}` is read as *`source` `<relation>` `target`* — for `teacher_of`, `source` taught `target`; for `corresponded_with`, `source` and `target` corresponded as contemporaries; for `extended`, `commented_on`, and `critiqued`, the later actor (`source`) engaged the prior subject (`target`).

1. **`certify_extended_polymath_dag(nodes, edges)`:** Runs **encoding-consistency checks** (`encoding_consistency_only = True`) over the `23`-scholar (`4` tributary, `15` core, `4` branch), `28`-edge dataset: enforcing mandatory structured `source` / `citation` (`work`, `edition`, `location`) on EVERY node and edge, epoch bounds, active-voice chronology (rejecting immature actors/subjects, reversed birth order, and edges where an actor died before the subject reached age 15), tier monotonicity, forward-time influence DAG acyclicity, and a `tributary ->+ core ->+ branch` path. These verify internal consistency of the encoded dataset against its stated conventions, not independent empirical discovery.
2. **`certify_contraction_and_causal_identifiability(spec)`:** Checks Banach fixed-point criteria (`0 <= L < 1`, self-map invariance ball `x0 ± step0_gap/(1-L) ⊆ [domain_lo, domain_hi]`, a-priori tolerance `L^k * step0_gap / (1-L) <= target_tol`) alongside binary causal-identifiability criteria (recomputing the confounded joint distribution directly from `(p_u1, pf_u1, pf_u0, pc_u1, pc_u0)` to block joint spoofing, enforcing non-degenerate marginals, `obs_l1 == 0`, and `|ATE_direct - ATE_confounded| >= min_ate_separation`).

---

## 7. Reproducibility & Verification Receipts

- **Self-Contained Offline Reproduction (Python 3 stdlib only, zero external files required):**
  - `python3 -I -O -B -W error bayt_al_hikma_veins_certifier.py --json` reproduces [bayt_al_hikma_veins_certificate.json](bayt_al_hikma_veins_certificate.json) **byte-for-byte** (`certificate_sha256: d9e2af09c6b2d83dae1e31cae56717b309476e52c7d0261f6781180b21cffbd0`, `execution_mode: standalone_pure_q`, `honest_tier: N0`, `0` floats).
  - `python3 -I -O -B -W error test_bayt_al_hikma_veins_r5.py` runs `10/10` tests OK (`0` skipped) across all isolated modes (`-I -B`, `-I -O -B`, `-I -B -W error`).
- **External Aletheia v2.0.0 Verification (`Foundation-0/aletheia#1`, external tool not bundled in this repo):**
  - Author seat: `fractals-probe`; independent clean-room verifier seat: `verifier`.
  - `aletheia v2.0.0 audit-check . --strict-ancestors --safety-scan --scripts bayt_al_hikma_veins_certifier.py test_bayt_al_hikma_veins_r5.py`: **`PASS`** (`4` files, `2/2` R4, `0` safety findings, `0` bare `assert`s, `0` floats, `0` `/home/` or `file:///` leaks, `0` CRLF, `0` `__pycache__`).
  - `aletheia v2.0.0 mutate bayt_al_hikma_veins_certifier.py --work-root . --add-cwd --max-mutants 0 --test-cmd "python3 -I -O -B -W error test_bayt_al_hikma_veins_r5.py"`: **`116/116` (`100.0%`, `truncated: false`) KILLED, `0` survivors**.
