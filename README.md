# Bayt al-Ḥikma — Classical Arabic Corpus Analyses & Polymath Pure-$\mathbb{Q}$ Verification

**Website:** <https://foundation-0.github.io/bayt-al-hikma/> (source in [`docs/`](docs/), plain HTML/CSS/JS, no build step; preview with `cd docs && python3 -m http.server 8000`). GitHub Pages serves `main` branch, `/docs` folder.

> **Scope, Execution Honesty & Law-4 `N0` Default**
>
> This repository contains **4 pure-$\mathbb{Q}$ Python 3 stdlib research packages** (`0` IEEE-754 floats on trust paths, `0` bare `assert`s) across two tracks:
> 1. **Classical Arabic Corpus Studies (`arabic-continuum/`, `AUDIT-091-V2` · `arabic-lexicon/`, `AUDIT-094-V2`):** Exact rational root-pattern cohesion, ring-vs-*inclusio* adjudication, *wazn* agency/reciprocity tables, native context topology, and two-translator (`en.sahih`, `en.pickthall`) lexical-edge loss across `9` SHA-256-pinned primary texts (Leeds Quranic Arabic Corpus v0.4, Tanzil Uthmani + 2 translations, and 5 OpenITI prose/poetry controls).
>    - **Full live recount from the 9 primary texts** is reproduced via [`fetch_corpora.py`](fetch_corpora.py) + `verify_all_standalone.py --live` (`mode: "live_corpus_recount"`, `live_corpus_recounted: true`, $B = 250$ deterministic multi-shuffle nulls + exact Holm-Bonferroni correction).
>    - **Offline default (`--standalone`)** reads **no corpus file**; it replays oracle invariants and exact rational calculations on pinned fixtures (`mode: "standalone_fixture_replay"`, `live_corpus_recounted: false`).
>    - **Retrospective vs. Pre-Registered Disclosure:** See [`PREREGISTERED_HYPOTHESES.md`](PREREGISTERED_HYPOTHESES.md) for the complete ledger of all `9` retrospective exploratory patterns inspected (including explicit falsifications and retractions), root-list selection rules, the scope of the feature-label naming filter (`enforce_zero_numerology_policy`), and the locked future confirmatory protocol.
> 2. **Bayt al-Ḥikma Polymath Lineage, Tributary Veins & Downstream Branches (`polymath-lineage/`, `AUDIT-092R2` · `veins-and-branches/`, `AUDIT-095R`):** Self-contained offline pure-$\mathbb{Q}$ arithmetic verifications of classical mathematical constructions across **`23` cited scholars** (`c. 287 BCE – 1543 CE`) and fail-closed **encoding-consistency checks** (`encoding_consistency_only = True`) over active-voice cited lineage tables. Both certifiers recompute every theorem from scratch offline with Python 3 stdlib only and reproduce their committed JSON certificates byte-for-byte.
>
> **Novelty Default (`N0`):** All `4/4` packages carry honest novelty tier **`N0`**. All classical Semitic philology, historical mathematical theorems, treatises, and published editions are prior art; no `N1` novelty is claimed without an explicit full-text prior-art audit.

---

## 1. Repository Layout

```text
bayt-al-hikma/
├── README.md                                        # Scope, live vs. offline reproduction, honest receipts & provenance
├── LICENSE                                          # Apache License 2.0
├── .gitignore                                       # Excludes __pycache__/, *.py[cod], and downloaded ./corpora/
├── PREREGISTERED_HYPOTHESES.md                      # Retrospective 9-pattern ledger, root-selection disclosure & locked protocol
├── fetch_corpora.py                                 # Pure-stdlib fetcher & SHA-256 verifier for all 9 primary texts (URLs, editions, licences)
├── verify_all_standalone.py                         # Zero-dependency verifier: offline fixture/standalone check OR --live corpus recount
├── docs/                                            # GitHub Pages site (index, continuum, lexicon, lineage, method, reproduce; no build step)
├── arabic-continuum/                                # AUDIT-091-V2 (N0, B=250 multi-shuffle nulls + Holm-Bonferroni)
│   ├── ARABIC_CONTINUUM_AUDIT_REPORT.md             # Full report, 12-cell lift reversal retraction & honest inclusio adjudication
│   ├── arabic_continuum_oracle.py                   # Pure-Q lattice, B=250 null, Holm-Bonferroni & feature-naming filter
│   ├── arabic_continuum_audit.py                    # Dual-mode --live / --corpus-dir recount + --standalone fixture replay
│   ├── test_arabic_continuum_r5.py                  # Assertion-free R5, threshold-pinning, known-answer mini-corpus & fetch tests
│   └── arabic_continuum_certificate.json            # Canonical live_corpus_recount JSON (file 7081c463..., inner 99ec338f...)
├── arabic-lexicon/                                  # AUDIT-094-V2 (N0, B=250 lemma-shuffle null + 4-stratum distance control)
│   ├── ARABIC_LEXICON_TOPOLOGY_REPORT.md            # Full report, single-corpus wazn disclosure & distance-controlled tables
│   ├── arabic_lexicon_oracle.py                     # Pure-Q Renyi-2, context topology, lemma-shuffle & feature-naming filter
│   ├── arabic_lexicon_audit.py                      # Dual-mode --live / --corpus-dir recount + --standalone fixture replay
│   ├── test_arabic_lexicon_r5.py                    # Assertion-free R5, threshold-pinning & hand-computed known-answer tests
│   └── arabic_lexicon_certificate.json              # Canonical live_corpus_recount JSON (file 96d855fa..., inner 230441ac...)
├── polymath-lineage/                                # AUDIT-092R2 (N0, self-contained offline pure-Q)
│   ├── BAYT_AL_HIKMA_POLYMATH_REPORT.md             # 13 cited scholars, published editions, Biruni 2..5-place sensitivity table
│   ├── bayt_al_hikma_polymath_certifier.py          # Pure-Q math verifier & active-voice encoding-consistency checker
│   ├── test_bayt_al_hikma_polymaths_r5.py           # Assertion-free -I -O -B -W error R5 & chronology/citation tests
│   └── bayt_al_hikma_polymath_certificate.json      # Canonical standalone_pure_q JSON (file 76fac890..., inner 4834f376...)
└── veins-and-branches/                              # AUDIT-095R (N0, self-contained offline pure-Q)
    ├── BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md   # 23 cited scholars, conservative pi/96-gon brackets & 13-step Chakravala
    ├── bayt_al_hikma_veins_certifier.py             # Pure-Q math verifier & active-voice encoding-consistency checker
    ├── test_bayt_al_hikma_veins_r5.py               # Assertion-free -I -O -B -W error R5 & chronology/citation tests
    └── bayt_al_hikma_veins_certificate.json         # Canonical standalone_pure_q JSON (file 236c165d..., inner d9e2af09...)
```

---

## 2. Exact Reproduction — Live Corpus Recount vs. Offline Replay

### Path A — Full Live Recount From the 9 Primary Corpora (Recommended)

Downloads all `9` upstream primary texts directly from their documented URLs (`cltk` Leeds v0.4 mirror, `tanzil.net`, `OpenITI/0150AH`, `OpenITI/0025AH`), verifies every byte size and SHA-256 digest atomically into `./corpora/` (gitignored), and recounts every metric and every $B = 250$ multi-shuffle null directly from the texts:

```bash
git clone https://github.com/Foundation-0/bayt-al-hikma.git
cd bayt-al-hikma

# 1. Inspect upstream URLs, editions, licences, byte sizes & SHA-256 pins (zero network):
python3 -I -B -W error fetch_corpora.py --manifest-json

# 2. Download & SHA-256-verify all 9 primary texts into ./corpora (once):
python3 -I -B -W error fetch_corpora.py --dest ./corpora

# 3. Full live verification across all 4 studies (recounts Arabic texts live + recomputes polymath/veins):
python3 -I -B -W error verify_all_standalone.py --live --corpus-dir ./corpora
```

**What `PASS` means in `--live` mode (`arabic_live_corpora_recounted: true`):**
- `fetch_corpora.py --verify-only` confirmed all `9/9` primary texts on disk match their pinned upstream byte sizes and SHA-256 digests.
- Both `arabic-continuum/arabic_continuum_audit.py` and `arabic-lexicon/arabic_lexicon_audit.py` read the `9` texts from disk, recomputed every count, every $B = 250$ multi-shuffle null, Holm-Bonferroni adjustment, and 4-stratum distance control from scratch, and matched their committed JSON certificates **byte-for-byte**.
- Both `polymath-lineage/` and `veins-and-branches/` recomputed every mathematical theorem from scratch and matched their committed JSON certificates **byte-for-byte**.
- All `4/4` R5 + known-answer test suites exited `0` under `-I -O -B -W error`, and all `20/20` pinned files matched their SHA-256 digests.

### Path B — Offline Zero-Network Check (Python 3 Stdlib Only)

```bash
# 3-mode isolated determinism check (bit-identical stdout across all 3 modes):
python3 -I -B verify_all_standalone.py
python3 -I -O -B verify_all_standalone.py
python3 -I -B -W error verify_all_standalone.py

# Machine-readable canonical zero-float JSON receipt:
python3 -I -B -W error verify_all_standalone.py --json
```

**What `PASS` means in offline mode (`arabic_live_corpora_recounted: false`):**
- `polymath-lineage/` and `veins-and-branches/` recomputed every mathematical verification from scratch and matched their committed JSON certificates **byte-for-byte**.
- `arabic-continuum/` and `arabic-lexicon/` ran `--standalone` (**reading NO corpus file**), replaying oracle invariants and exact rational calculations on their pinned verbatim fixtures (`mode: "standalone_fixture_replay"`).
- All `4/4` R5 / threshold-pinning / known-answer test suites exited `0`, and all `20/20` pinned files matched their SHA-256 digests.
- **Offline `PASS` MUST NOT be interpreted as a live recount from the 9 primary Arabic texts.** Use Path A (`--live`) for a live recount.

### Individual Package Commands

```bash
# Arabic Continuum (live recount vs. offline fixture replay + R5/known-answer tests):
python3 -I -B -W error arabic-continuum/arabic_continuum_audit.py --live --corpus-dir ./corpora
python3 -I -B -W error arabic-continuum/arabic_continuum_audit.py --standalone
python3 -I -O -B -W error arabic-continuum/test_arabic_continuum_r5.py

# Arabic Lexicon (live recount vs. offline fixture replay + R5/known-answer tests):
python3 -I -B -W error arabic-lexicon/arabic_lexicon_audit.py --live --corpus-dir ./corpora
python3 -I -B -W error arabic-lexicon/arabic_lexicon_audit.py --standalone
python3 -I -O -B -W error arabic-lexicon/test_arabic_lexicon_r5.py

# Polymath Lineage (self-contained offline pure-Q + R5 tests):
(cd polymath-lineage && python3 -I -B -W error bayt_al_hikma_polymath_certifier.py --json)
(cd polymath-lineage && python3 -I -O -B -W error test_bayt_al_hikma_polymaths_r5.py)

# Tributary Veins & Downstream Branches (self-contained offline pure-Q + R5 tests):
(cd veins-and-branches && python3 -I -B -W error bayt_al_hikma_veins_certifier.py --json)
(cd veins-and-branches && python3 -I -O -B -W error test_bayt_al_hikma_veins_r5.py)
```

---

## 3. Study Summary, Honest Retractions & Exact Digests

| Study Directory | Audit ID · Novelty | Offline vs. Live Recompute | Committed Cert SHA-256 (File / Inner) | Headline Findings, Retractions & Honest Scope |
|---|---|---|---|---|
| [`arabic-continuum/`](arabic-continuum/ARABIC_CONTINUUM_AUDIT_REPORT.md) | `AUDIT-091-V2` · **`N0`** | Offline: fixture replay (`817738b4...`); Live (`--live`): recounts 9 texts byte-identical to cert | `7081c463...` / `99ec338f...` | `1,642` roots × `11` verb forms (`49,968` tokens). **Retracts** naive absolute cohesion ladder (`raw < rasm < stem < root`): across all 12 `(layer, W)` cells with $B=250$ per-layer shuffles, **lift reverses** (`raw > rasm/stem > root`; at `W=20`, `2.11× > 1.68× > 1.65× > 1.49×`, all 12 cells Holm `p_adj = 12/251 = 0.0478`). *Kalīla* stem lift (`1.82×`) > Qur'an (`1.65×`), confirming shared Classical Arabic prose cohesion. Pointwise mirror **FALSIFIED** (`0.040319 < 0.042126`, lower-tail `p = 5/251 = 0.0199`). Post-hoc boundary *inclusio* adjudicated **`EXPLORATORY_INCONCLUSIVE_NOT_SEPARATED`** (`6/6` Qur'an slices fail Holm-Bonferroni at $B=250$, min `p_adj = 42/251 = 0.1673 > 0.05`; *Kalīla* natural chapters `+0.009739` > Qur'an `all` `+0.008283`). Odd/even splits strictly labelled `split_half_internal_consistency`. Descriptive 2-translator edge loss (`50.91%` Sahih / `65.88%` Pickthall) on disclosed 9-root set. |
| [`arabic-lexicon/`](arabic-lexicon/ARABIC_LEXICON_TOPOLOGY_REPORT.md) | `AUDIT-094-V2` · **`N0`** | Offline: fixture replay (`4c562cf1...`); Live (`--live`): recounts 9 texts byte-identical to cert | `96d855fa...` / `230441ac...` | `1,642`-root × *Wazn* (`19,347` verbs, Forms `I–X`) within-root Rényi-2 concentration (`0.926980`, $B=250$ T4A/T4B Holm `p_adj = 4/251`) explicitly scoped as **`single_corpus_descriptive_morphology`** (`form_tagged_openiti_control_present: false`). Matched OpenITI `W=20` light-stem Rényi-2 lift confirms shared prose lift (*Kalīla* `1.81×` > Qur'an `1.69×`; poetry $D_2 = 477.68$). Disclosed 15-root / 14-field context topology survives `9/9` Holm-Bonferroni (`p_adj = 9/251 = 0.0359`) on `split_half_internal_consistency` slices. Two-translator projection defect (`131,343` pairs; same-lemma floor `34.41%` / `45.96%`, cross-lemma gap `+0.3349` / `+0.2734`) survives $B=250$ within-root lemma-label shuffle (`p = 1/251` pooled; per-root Holm passes `11/12` Sahih with `wzn` failing, `10/12` Pickthall with `wzn` & `Erj` failing) and 4-stratum verse-distance-matched controls (`+25` to `+36` pp across all `4/4` strata on both translators), noting a positive cross-lemma gap is expected in any derivational language. |
| [`polymath-lineage/`](polymath-lineage/BAYT_AL_HIKMA_POLYMATH_REPORT.md) | `AUDIT-092R2` · **`N0`** | Self-contained offline pure-$\mathbb{Q}$ recompute (byte-identical to cert) | `76fac890...` / `4834f376...` | `13`-scholar, `14`-edge active-voice **encoding-consistency check** (`encoding_consistency_only = True`) with mandatory structured citations (`work`, `edition`, `location`) on every node and edge. Exact pure-$\mathbb{Q}$ verifications: al-Bīrūnī ↔ Ibn Sīnā 2-adic parity & `1/2`-atom wheel-slippage; Thābit amicable precondition & unequal-grid quadrature (`width = 1/N`); Ibn al-Haytham reflection quartic & primitive Ferrari cubic resolvent (`531441` × monic standard resolvent, `0` rational roots); Haytham–Khayyām curvature trichotomy; Ibn Rushd toy overparameterization witness; al-Khwārizmī 6-form reducer & Karajī/Samawʾal Laurent ring; al-Kindī scaling & permutation invariance; al-Bīrūnī *Taḥdīd* `12,803,337`-cubit `2/3/4/5`-place base-60 truncation sensitivity table (Ali 1967 & Kennedy 1973 cited, explicitly labelled **`ARITHMETIC_FIT_HYPOTHESIS_SINGLE_NUMBER`**); zero-residual Ṭūsī couple; al-Jazarī float-valve stability. |
| [`veins-and-branches/`](veins-and-branches/BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md) | `AUDIT-095R` · **`N0`** | Self-contained offline pure-$\mathbb{Q}$ recompute (byte-identical to cert) | `236c165d...` / `d9e2af09...` | `23`-scholar, `28`-edge 3-tier active-voice **encoding-consistency check** (`encoding_consistency_only = True`) with mandatory structured citations on every node and edge. Exact pure-$\mathbb{Q}$ verifications: Brahmagupta cyclic quad (`K = 1764`, `R = 65/2`, Ptolemy `3528`), *bhāvanā* (`D = 92`), exact **`13`-step** (`14`-row) integer Chakravala (`D = 61`); Heron `d = 0` limit & $\sqrt{720}$; Archimedes `96`-gon strictly conservative outer bracket `223/71 < 3.141031 < pi < 3.142715 < 22/7`; Apollonius focal reflection; Ibn al-Shāṭir ↔ Copernicus `0/1` lunar/Mercury equivalence (`L1 = 1/9000`; transmission route noted historiographically open); al-Ghazālī ↔ Ibn Rushd `2×2` binary causal witness (`obs_l1 = 0/1`, `ATE = 9/25 vs 0/1`); al-Kāshī Banach `L = 1/625` $\sin(1^\circ)$ (`9/9` leading base-60 match) and certified pure-integer $3\cdot 2^{28}$-gon $\pi$ bracket (conservative 10-place outer width `2.481e-17` for $\pi$, unrounded rational width `<= 2.416352e-17`, floored 10-place display width `2.398e-17`, confirming `16` decimal digits and bracketing 1424 CE $2\pi$); al-Fārābī 11-limit acoustic cent brackets (`12/11 >= 49`c, `27/22 >= 45`c). |

---

## 4. Verification Provenance, External Tooling & Seat Separation

1. **Directly Reproducible From This Repository (Python 3 Stdlib Only):**
   - Everything in §2 (`fetch_corpora.py`, `verify_all_standalone.py`, all `4` certifier scripts, and all `4` R5 + threshold-pinning + known-answer test suites) runs with Python 3 stdlib only.
2. **External `aletheia v2.0.0` Tooling Receipts (Not Bundled Here):**
   - `audit-check` and AST mutation harnesses come from the external repository [`Foundation-0/aletheia`](https://github.com/Foundation-0/aletheia) (`v2.0.0`, currently on open PR [`Foundation-0/aletheia#1`](https://github.com/Foundation-0/aletheia/pull/1), not merged to `main` and not vendored in this repository).
   - External mutation receipts reported across the `4` studies + `fetch_corpora.py` (`392/392` R5 AST mutants killed + `83/83` AST `BoolOp(And)` conjunct deletions killed on the Arabic modules) require running that external tool against this tree; they are reported as external verification receipts rather than stdlib-reproducible claims.
3. **Explicit Author vs. Independent Verifier Seats:**

| Component | Author Seat | Independent Clean-Room Verifier Seat |
|---|---|---|
| `fetch_corpora.py`, `arabic-continuum/`, `arabic-lexicon/` | `continuum-bridge` | `verifier` |
| `PREREGISTERED_HYPOTHESES.md` | `continuum-bridge` (initial protocol) · `session-cartographer` (`B=250` table sync) | `verifier` |
| `polymath-lineage/`, `veins-and-branches/` | `fractals-probe` | `verifier` |
| `verify_all_standalone.py`, `README.md`, `.gitignore` | `session-cartographer` | `verifier` |

---

## 5. Conceptual Parallels & Related Repositories

No machine-verified cross-repository bridge is claimed in this repository, and no external non-repository vault files are hashed or required by any script. The links below document **external tooling provenance** and **conceptual parallels / research motivation** only:

| Related Repository | Relationship (Tooling Provenance or Conceptual Parallel Only) |
|---|---|
| [`Foundation-0/aletheia`](https://github.com/Foundation-0/aletheia) (open PR `#1`, `v2.0.0`) | External static-hygiene (`audit-check --strict-ancestors --safety-scan`) and AST mutation (`mutate`) toolchain used during development and review. |
| [`Foundation-0/cave-expedition`](https://github.com/Foundation-0/cave-expedition) | Parent research ledger indexing the audit IDs (`AUDIT-091-V2`, `AUDIT-092R2`, `AUDIT-094-V2`, `AUDIT-095R`). |
| [`Foundation-0/continuum`](https://github.com/Foundation-0/continuum) | Conceptual motivation for comparing continuous/multi-layer representations against discrete projections (al-Bīrūnī/Ibn Sīnā discrete obstructions, al-Fārābī 11-limit ratios vs. 12-TET, Arabic root/lemma translation loss). |
| [`Moissanite-Labs/warp-drive`](https://github.com/Moissanite-Labs/warp-drive) | Conceptual parallel to discrete-time bounded feedback (al-Jazarī float-valve dynamics) and contraction mappings (al-Kāshī Banach fixed-point solver). |
| [`Foundation-0/incentre-lattices`](https://github.com/Foundation-0/incentre-lattices) | Conceptual parallel to rational-parametrized kinematics (Ṭūsī couple, Ibn al-Shāṭir / Copernicus double-epicycle models). |

---

## 6. Pre-Registration & Contribution Standard

Any future confirmatory corpus study added to `Foundation-0/bayt-al-hikma` must follow the locked protocol in [`PREREGISTERED_HYPOTHESES.md`](PREREGISTERED_HYPOTHESES.md) §2:
- Fix hypotheses, units, window sizes, and **algorithmic** (non-hand-picked) root-selection criteria BEFORE inspecting target data;
- Use $B \ge 250$ deterministic multi-shuffle nulls with exact pure-$\mathbb{Q}$ empirical rank $p$-values and Holm-Bonferroni correction across the full family of inspected tests;
- Label odd/even splits strictly as `split_half_internal_consistency` (never `"unseen"`), require morphologically form-tagged control corpora before cross-corpus morphological uniqueness claims, and default all novelty classifications to **`N0`** unless backed by a full-text prior-art audit.

---

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
