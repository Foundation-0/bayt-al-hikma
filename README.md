# Bayt al-Ḥikma — Raw Classical Arabic Continuum Semantics & Polymath Mathematical Lineage

> **Aletheia v2.0.0 Charter (`OWN_TERMS_FIRST` + Law 2b Transformational Steelman + Strict Law-5 Zero Numerology)**
>
> This repository applies the [`Foundation-0/aletheia`](https://github.com/Foundation-0/aletheia) v2.0.0 adversarial verification standard to two coupled research tracks spanning **4 independently verified pure-$\mathbb{Q}$ studies** (`334/334` R5 AST mutants killed, `0` IEEE-754 floats on trust paths, `0` bare `assert`s):
> 1. **Raw Classical Arabic / Qur'anic Layered Continuum Semantics (`arabic-continuum/`, `AUDIT-091R` · `arabic-lexicon/`, `AUDIT-094R`):** Probing non-concatenative triliteral root-pattern geometry ($C_1 C_2 C_3 \times \text{wazn}$), the `1,642`-root × *Wazn* (Forms I–X) derivational agency/reciprocity matrix, macro-textual boundary *inclusio*, native semantic-field context topology, and two-instrument (`en.sahih` vs. `en.pickthall`) continuum-to-discrete translation loss directly on `9` SHA-256-pinned primary Arabic corpora against matched Classical Arabic negative controls (*Kalīla wa-Dimna*, *al-Adab al-Kabīr*, pre-Islamic *Muʿallaqāt* / *dīwāns*) and stratified Tier-4A / Tier-4B nulls. **STRICTLY ZERO numerology, abjad, gematria, or base-10 digit-count claims** (enforced fail-closed in code via `NUMEROLOGY_FORBIDDEN` + NFKC/homoglyph/control-char guards).
> 2. **Bayt al-Ḥikma Polymath Lineage, Tributary Veins & Downstream Branches (`polymath-lineage/`, `AUDIT-092R` · `veins-and-branches/`, `AUDIT-095`):** Pure-$\mathbb{Q}$ zero-float mathematical verification and structural bridges across **`23` interconnected scholars** (`c. 287 BCE – 1543 CE`) linking pre-Abbasid **tributary veins** (Archimedes, Apollonius, Heron, **Brahmagupta**, Gundishapur / Ḥunayn ibn Isḥāq), the **Bayt al-Ḥikma core** (**al-Khwārizmī**, **al-Kindī**, **Banū Mūsā**, **Thābit ibn Qurra**, **al-Fārābī**, **al-Karajī**, **Ibn al-Haytham**, **al-Bīrūnī**, **Ibn Sīnā**, **ʿUmar al-Khayyām**, **al-Ghazālī**, **al-Samawʾal**, **Ibn Rushd**, **Ismāʿīl al-Jazarī**, **Naṣīr al-Dīn al-Ṭūsī**), and **downstream branches** (**Ibn al-Shāṭir**, **Jamshīd al-Kāshī**, **Nicolaus Copernicus**).
>
> **Law-4 Epistemic Honesty:** All classical Semitic philology, literary *inclusio* scholarship, and original ancient/medieval/Renaissance theorems and treatises are strictly attributed as **`N0` prior art**. Our contributions here are honestly scoped as **`N1`**: pure-$\mathbb{Q}$ zero-float executable verification engines, matched negative-control falsifications, forensic sexagesimal cancellation reconstruction, pure-integer $3\cdot 2^{28}$-gon $\pi$ and Banach $\sin(1^\circ)$ solvers, exact cent-resolution 12-TET acoustic defect proofs, structural-causal witnesses, fail-closed lineage/feedback certifiers, and `100.0%` R5 mutation-hardened test suites.

---

## 1. Repository Layout

```text
bayt-al-hikma/
├── README.md                                        # Charter, 4-study verified receipts & cross-repo bridges
├── LICENSE                                          # Apache License 2.0
├── verify_all_standalone.py                         # Zero-dependency 3-mode R4 verifier for all 4 committed studies
├── arabic-continuum/                                # AUDIT-091R VERIFIED (68/68 R5 killed, N1)
│   ├── ARABIC_CONTINUUM_AUDIT_REPORT.md             # Full Law-1..5 report, 9 SHA-256 corpus pins & falsification criteria
│   ├── arabic_continuum_oracle.py                   # Pure-Q root-pattern, inclusio, remainder & zero-numerology oracle (63/63 R5)
│   ├── arabic_continuum_audit.py                    # Dual-mode live_readonly + --standalone audit runner (5/5 R5)
│   ├── test_arabic_continuum_r5.py                  # Assertion-free -I -O -B -W error R5 & red-team test suite
│   └── arabic_continuum_certificate.json            # Canonical zero-float live-corpus certificate (28c3f9da...)
├── arabic-lexicon/                                  # AUDIT-094R VERIFIED (81/81 R5 killed, N1)
│   ├── ARABIC_LEXICON_TOPOLOGY_REPORT.md            # Full Law-1..5 report, 1,642-root x Wazn matrix & 14-root projection tables
│   ├── arabic_lexicon_oracle.py                     # Pure-Q agency/reciprocity, Renyi-2, Jaccard & NFKC guard oracle (76/76 R5)
│   ├── arabic_lexicon_audit.py                      # Dual-mode live_readonly + --standalone audit runner (5/5 R5)
│   ├── test_arabic_lexicon_r5.py                    # Assertion-free -I -O -B -W error R5 & red-team test suite
│   └── arabic_lexicon_certificate.json              # Canonical zero-float live-corpus certificate (54801bff...)
├── polymath-lineage/                                # AUDIT-092R VERIFIED (75/75 R5 killed, N1)
│   ├── BAYT_AL_HIKMA_POLYMATH_REPORT.md             # Full Law-1..5 report across 13 scholars & 4 mathematical pillars
│   ├── bayt_al_hikma_polymath_certifier.py          # Pure-Q zero-float math engine & fail-closed DAG/valve certifiers (75/75 R5)
│   ├── test_bayt_al_hikma_polymaths_r5.py           # Assertion-free -I -O -B -W error R5 & red-team test suite
│   └── bayt_al_hikma_polymath_certificate.json      # Canonical zero-float live-anchored certificate (746e331e...)
└── veins-and-branches/                              # AUDIT-095 VERIFIED (110/110 R5 killed, N1)
    ├── BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md   # Full Law-1..5 report across 23-scholar 3-tier DAG & 5 mathematical pillars
    ├── bayt_al_hikma_veins_certifier.py             # Pure-Q veins/branches math engine & Banach/causal/DAG certifiers (110/110 R5)
    ├── test_bayt_al_hikma_veins_r5.py               # Assertion-free -I -O -B -W error R5 & red-team test suite
    └── bayt_al_hikma_veins_certificate.json         # Canonical zero-float live-anchored certificate (e495d9bc...)
```

---

## 2. Verified Study Summary & Exact Receipts

Every artifact below passed independent zero-shared-code clean-room verification under [`Foundation-0/aletheia`](https://github.com/Foundation-0/aletheia) `v2.0.0` (zero IEEE-754 floats on trust paths, zero bare `assert`s, `4/4` isolated `-I` R4 bit-identical determinism, **`334/334` (`100.0%`)** R5 AST mutation kill, `0` bypasses across adversarial red-team probes):

| Study Directory | Audit & Clean-Room Check | Oracle / Novelty | R5 Mutants Killed | Standalone Stdout SHA-256 | Headline Verified Findings |
|---|---|---|---:|---|---|
| [`arabic-continuum/`](arabic-continuum/ARABIC_CONTINUUM_AUDIT_REPORT.md) | **`AUDIT-091R`** (`check_082`, `0` defects, `16/16` extra probes PASS) | `exact+anchor` · `N1` | **`68/68`** (`100.0%`) | `d723eab3b2009795...` | `1,642` roots × `11` verb forms (`49,968` morphemes) obey strict cohesion ladder `raw < rasm < stem < root` across `W ∈ {10,20,40}` on odd & unseen even surahs; matched OpenITI *Kalīla* (`1.778×`) refutes false uniqueness; Law 2b falsifies global pointwise mirror ring (`0.040319 < 0.041933`) while verifying top-10-stripped boundary *inclusio* (`+0.007423` unseen even vs `-0.002096` arbitrary *Kalīla* slices); two-instrument translation remainder loses `50.91%` (Sahih) / `65.88%` (Pickthall) of Arabic root-linked verse pairs. |
| [`arabic-lexicon/`](arabic-lexicon/ARABIC_LEXICON_TOPOLOGY_REPORT.md) | **`AUDIT-094R`** (`check_085`, `0` defects, `10/10` extra probes PASS) | `exact+anchor` · `N1` | **`81/81`** (`100.0%`) | `c81d5a6d4e5173b4...` | Exact `1,642`-root × *Wazn* (Forms I–X) agency/reciprocity matrix (`942` verbal roots, `19,347` verbs, `349/942 = 37.0488%` multi-*wazn* roots; within-root Rényi-2 `6190677/6678331 = 0.926980` vs Tier-4B `0.507537`, unseen even `0.923794` vs `0.549852`); honest OpenITI Rule-5 control (*Kalīla* `W=20` lift `1.811516×` > Qur'an `1.689581×`; pre-Islamic poetry $D_2 = 477.682941$); `14` root fields (`15` roots) specialized context neighborhoods (`1.634358×` Rényi-2 lift, lower inter-root Jaccard `0.182547 < 0.225574`, higher same-verse coupling `173/1161` vs `137/1172`); Law-2b Two-Layer continuum projection defect across `131,343` pairs (`77,081` same-lemma floor `34.4054%` Sahih / `45.9556%` Pickthall; `54,262` cross-lemma surge `67.8965%` / `73.2981%`, **unanimous `12/12` multi-lemma roots in BOTH translators**). |
| [`polymath-lineage/`](polymath-lineage/BAYT_AL_HIKMA_POLYMATH_REPORT.md) | **`AUDIT-092R`** (`check_080`, `0` defects, `15/15` extra probes PASS) | `exact+anchor` · `N1` | **`75/75`** (`100.0%`) | `898ee17e3f1ebee4...` | Exact `13`-scholar chronological DAG (`14` edges); 2-adic valuation parity & `1/2`-atom wheel-slippage continuum obstruction (al-Bīrūnī ↔ Ibn Sīnā) + Thābit unequal-grid parabola quadrature (`width = 1/N`); complete pure-$\mathbb{Q}$ Ferrari cubic resolvent (`0` rational roots) proving Alhazen spherical-mirror quartic non-constructibility + Haytham–Khayyām curvature trichotomy + Ibn Rushd anti-epicycle; Khwārizmī 6-form reducer + Karajī/Samawʾal $\mathbb{Q}[x, x^{-1}]$ Laurent ring; exact 3-place sexagesimal reconstruction of al-Bīrūnī's 1025 CE `12,803,337`-cubit *Taḥdīd* value (`28167341479/2200 = 12,803,337.036`) via `cos(34') = 0;59,59,49`; zero-residual Ṭūsī couple; al-Jazarī float-valve stability + saturation headroom certifier. |
| [`veins-and-branches/`](veins-and-branches/BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md) | **`AUDIT-095`** (`check_086`, `0` defects, `22/22` extra probes PASS) | `exact+anchor` · `N1` | **`110/110`** (`100.0%`) | `df16a48ee68027ea...` | Exact `23`-scholar, `28`-edge 3-tier DAG (`tributary -> core -> branch`, `c. 287 BCE – 1543 CE`); Indian/Greek/Syriac veins (Brahmagupta cyclic quad `(39,60,52,25)` `K=1764`/`R=65/2`/Ptolemy `3528`/perp-bisector `0`, *bhāvanā* `D=92 -> (1151,120)`, `14`-step exact integer Chakravala `D=61 -> (1766319049, 226153980)`, Heron `d=0` limit & $\sqrt{720}$, Archimedes `96`-gon inside `[223/71, 22/7]`, Apollonius/Banū Mūsā focal reflection); downstream branches (Ibn al-Shāṭir ↔ Copernicus `0/1` lunar double-epicycle & Mercury Ṭūsī-couple equivalence with `L1 = 1/9000` eliminating Ptolemy's `3915/2047` lunar artifact; al-Ghazālī ↔ Ibn Rushd exact `2×2` causal witness `obs_l1 = 0/1` vs `ATE = 9/25 vs 0/1`; Jamshīd al-Kāshī Banach `L = 1/625` $\sin(1^\circ)$ `9/9` leading base-60 match & certified pure-integer $3\cdot 2^{28} = 805,306,368$-gon $\pi$ bracket agreeing to `16` decimal digits and bracketing 1424 CE $2\pi = 6;16,59,28,01,34,51,46,14,50$; al-Fārābī 11-limit acoustic continuum `12/11` `>= 49`c & `27/22` `>= 45`c 12-TET rounding defect) + unified fail-closed Banach/causal certifier. |

---

## 3. Exact Zero-Dependency Reproduction

Run the entire standalone verification suite (`4` certifiers + `4` R5 test suites, strict zero-float JSON parsing on both committed certificates and standalone outputs, and byte-exact SHA-256 verification across all `18/18` study files) from a fresh clone with **Python 3 stdlib only**:

```bash
git clone https://github.com/Foundation-0/bayt-al-hikma.git
cd bayt-al-hikma

# 3-mode isolated Gate-7 (R4) parity verification (bit-identical across all 3 modes):
python3 -I -B verify_all_standalone.py
python3 -I -O -B verify_all_standalone.py
python3 -I -B -W error verify_all_standalone.py

# Machine-readable canonical zero-float JSON receipt:
python3 -I -B -W error verify_all_standalone.py --json
```

Individual package runs:

```bash
# Track 1A — Classical Arabic Continuum Semantics (AUDIT-091R):
(cd arabic-continuum && python3 -I -B -W error arabic_continuum_audit.py --standalone)
(cd arabic-continuum && python3 -I -O -B -W error test_arabic_continuum_r5.py)

# Track 1B — Classical Arabic Lexical Semantic-Field Topology (AUDIT-094R):
(cd arabic-lexicon && python3 -I -B -W error arabic_lexicon_audit.py --standalone)
(cd arabic-lexicon && python3 -I -O -B -W error test_arabic_lexicon_r5.py)

# Track 2A — Bayt al-Hikma 13-Polymath Lineage (AUDIT-092R):
(cd polymath-lineage && python3 -I -B -W error bayt_al_hikma_polymath_certifier.py --json)
(cd polymath-lineage && python3 -I -O -B -W error test_bayt_al_hikma_polymaths_r5.py)

# Track 2B — Bayt al-Hikma Tributary Veins & Downstream Branches (AUDIT-095):
(cd veins-and-branches && python3 -I -B -W error bayt_al_hikma_veins_certifier.py --json)
(cd veins-and-branches && python3 -I -O -B -W error test_bayt_al_hikma_veins_r5.py)
```

*(Full live-corpus replay of `arabic-continuum/` and `arabic-lexicon/` uses the `9` open SHA-256-pinned primary texts listed in [`arabic-continuum/ARABIC_CONTINUUM_AUDIT_REPORT.md`](arabic-continuum/ARABIC_CONTINUUM_AUDIT_REPORT.md) §2 and [`arabic-lexicon/ARABIC_LEXICON_TOPOLOGY_REPORT.md`](arabic-lexicon/ARABIC_LEXICON_TOPOLOGY_REPORT.md) §2 via `--corpus-dir <path>`.)*

---

## 4. Cross-Repository Epistemic Bridges

| Upstream / Sibling Repository | Structural Bridge Verified Here |
|---|---|
| [`Foundation-0/aletheia`](https://github.com/Foundation-0/aletheia) (`v2.0.0`, PR `#1`) | Governs all `4` packages (`OWN_TERMS_FIRST`, Law 2b Transformational Steelman, `R6`/`R7`, `--strict-ancestors`, `--safety-scan`); grounded historically by **Ibn Rushd's Anti-Epicycle Principle** (`G2`), **al-Ghazālī ↔ Ibn Rushd** observational-vs-interventional identifiability, **al-Khwārizmī's *al-jabr wa-l-muqābala*** ($\mathcal{T}_2$), and **al-Kindī's permutation-invariant frequency null** ($\mathcal{T}_1$). |
| [`Foundation-0/continuum`](https://github.com/Foundation-0/continuum) (`PR #1`) | **al-Bīrūnī ↔ Ibn Sīnā** 2-adic diagonal & `1/2`-atom concentric-wheel obstructions, **Thābit ibn Qurra** non-uniform quadrature, **al-Fārābī's** 11-limit *maqām* acoustic continuum (`45–49`c 12-TET bucketization defect), and **`arabic-continuum/` + `arabic-lexicon/`** two-layer semantic projection loss (`12/12` unanimous cross-lemma amplification) directly formalize the continuum-vs-discrete thesis of `continuum.md:3`. |
| [`Foundation-0/cave-expedition`](https://github.com/Foundation-0/cave-expedition) (`PR #1`) | Umbrella verification ledger (`AUDIT-001`–`095`), Round-10 `AUDIT-085R` $\mathbb{Q}[q]$ Laurent-ring bridge to **al-Karajī & al-Samawʾal**, and `AUDIT-088R` Law 2b vault. |
| [`Moissanite-Labs/warp-drive`](https://github.com/Moissanite-Labs/warp-drive) | **Banū Mūsā** & **Ismāʿīl al-Jazarī** bounded float-valve contraction ($0 < \mu < 2$) and proportional saturation headroom (`linear_head_margin * 10 >= setpoint`), plus **Jamshīd al-Kāshī's** certified Banach fixed-point contraction ($L = 1/625 < 1$), connect directly to bounded discrete-time controllers. |
| [`Foundation-0/incentre-lattices`](https://github.com/Foundation-0/incentre-lattices) | **Ibn al-Haytham–Khayyām–Ṭūsī** curvature trichotomy and zero-residual **Ṭūsī-couple** / **Ibn al-Shāṭir ↔ Copernicus** double-epicycle kinematic involutions connect directly to exact zero-trig bar/kinematic geometry. |

---

## 5. Provenance & Contribution Standard

- **Verbatim Package Parity:** All `18` study files across `arabic-continuum/`, `arabic-lexicon/`, `polymath-lineage/`, and `veins-and-branches/` are SHA-256-pinned inside [`verify_all_standalone.py`](verify_all_standalone.py). All `100%` of executable certifiers, R5 test suites, canonical certificates, and `3/4` reports match the original clean-room vault artifacts byte-for-byte; only the 3 cross-study anchor links on lines 16–18 of [`veins-and-branches/BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md`](veins-and-branches/BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md) were retargeted from internal vault directory names to this repository's live in-tree / GitHub paths so zero dead relative links exist.
- **Bar for Future Studies:** Any additional classical linguistic, historical-scientific, or polymath verification study added to `Foundation-0/bayt-al-hikma` must pass `aletheia v2.0.0 audit-check --strict-ancestors --safety-scan`, `100.0%` R5 AST mutation kill (`--max-mutants 0`), strict zero-float pure-$\mathbb{Q}$ trust-path execution, `4/4` isolated `-I` R4 determinism, honest Law-4 `N0`/`N1` attribution, and strict Law-5 zero-numerology enforcement.

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
