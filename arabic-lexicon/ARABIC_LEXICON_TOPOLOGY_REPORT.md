# Classical Arabic Lexical Semantic-Field Topology & Multi-Translator Projection Defect (v2)

- **Audit ID:** `AUDIT-094-V2` (updated directly in response to peer review `6011346623`)
- **Governance Standard:** Aletheia v2.0.0 (`OWN_TERMS_FIRST`, Law 2b, Law 4 honest `N0` novelty default, Law 5 feature-naming guard)
- **Execution Modes (Explicitly Distinguished):**
  - **Live Recount (`--live` / `--corpus-dir ./corpora`):** Verifies all 9 SHA-256-pinned primary corpora fetched via `../fetch_corpora.py` and recomputes EVERY count, $B = 250$ multi-shuffle null, and 4-stratum distance control directly from the raw primary texts (`mode: "live_corpus_recount"`, `live_corpus_recounted: true`).
  - **Offline Standalone Replay (default / `--standalone`):** Reads NO corpus text; replays oracle invariants and exact rational calculations on the pinned verbatim fixture (`mode: "standalone_fixture_replay"`, `live_corpus_recounted: false`).
- **Exact Pinned Certificate Digests:**
  - `live_corpus_recount` (`arabic_lexicon_certificate.json`): `230441ac38e9f84719f3acf7c491f9b1e14f1360d892bd36802bca046ad4ff77`
  - `standalone_fixture_replay` (`--standalone`): `8ec87277a9b5ae4ac529f3962bbf3fa9e89fa3c7727e08205c6805a7a4f62a4a`
- **Novelty Classification (Law 4 Honest Default):** **`N0`** (exact pure-$\mathbb{Q}$ computational quantification of established Classical Arabic morphological and lexical-semantic phenomena; see `../PREREGISTERED_HYPOTHESES.md` for full retrospective disclosure and pre-registered future protocol).

---

## 1. Methodological Disclosures & Revisions Closing Review `6011346623`

1. **Full Live Reproducibility (`../fetch_corpora.py`):** All 9 primary corpora can be fetched directly from their verified upstream URLs with exact editions, licences, byte sizes, and SHA-256 digests (`python3 fetch_corpora.py --dest ./corpora`), then recounted live (`python3 arabic-lexicon/arabic_lexicon_audit.py --live`).
2. **Feature-Naming Guard Scope:** `enforce_zero_numerology_policy` is explicitly labelled as a **feature-label hygiene filter** (`guard_scope: "feature_label_filter_only_not_statistical_proof"`), NOT a statistical proof of methodology. Methodological discipline rests on `../PREREGISTERED_HYPOTHESES.md`, $B = 250$ multi-shuffle nulls, Holm-Bonferroni adjustment, and matched controls.
3. **No `"Unseen"` Claim:** Odd/even surah splits are strictly labelled **`split_half_internal_consistency_not_unseen`** because the full text was inspected while designing the pipeline.
4. **Single-Corpus Descriptive Scope for Within-Root *Wazn* Concentration:** Within-root verb-form Rényi-2 concentration (`0.926980`) is explicitly labelled **`single_corpus_descriptive_morphology`** with **`form_tagged_openiti_control_present: false`**. Any natural language in which roots prefer specific derived stems beats a cross-root form shuffle; OpenITI controls currently enter ONLY the `W=20` light-stem Rényi-2 cross-collision and global $D_2$ comparison.
5. **Removal of Post-Hoc Fitted Thresholds + Addition of Lemma-Shuffle Null & Distance Control:** Dropped post-hoc fitted thresholds (`9/20`, `3/10`) in Pillar 3 and replaced them with (a) **$B = 250$ within-root lemma-label shuffle nulls** (pooled + per-root Holm-Bonferroni across all 12 multi-lemma roots) and (b) **4-stratum verse-distance-matched controls**. Explicitly notes that a positive cross-lemma vs. same-lemma gap is expected in any derivational language where distinct lemmas map to distinct glosses — the measurement quantifies both the intra-lemma polysemy floor (`34.41%` / `45.96%`) and the distance-controlled lemma-branching effect (`+25` to `+36` pp) across two independent translators.

---

## 2. Pillar 1: `1,642`-Root × *Wazn* (Forms `I–X`) Descriptive Matrix & OpenITI Controls ($B = 250$)

### 2.1 Single-Corpus Descriptive *Wazn* Agency/Reciprocity Matrix (`19,347` Verbs `I–X` + `9` Form `XII`)
- **`942` verb-bearing roots** out of `1,642` total roots; **`349 / 942 = 37.0488%`** carry `>= 2` distinct verb forms (`I+IV: 146`, `I+II: 87`, `I+VIII: 67`, `I+X: 42`, `IV+X: 41`, `II+V: 40`, `III+VI: 12`).
- Operator classes: `GROUND_I: 12,347` (`63.82%`), `CAUS_INTENS_II_III_IV: 5,121` (`26.47%`), `REFL_RECIP_V_VI_VII_VIII: 1,505` (`7.78%`), `STAT_ESTIM_IX_X: 374` (`1.93%`).
- Within-root *wazn* Rényi-2 concentration (`single_corpus_descriptive_morphology`, `form_tagged_openiti_control_present: false`): `6190677/6678331 = 0.926980` (`B=250` T4A & T4B `0/250`, Holm `p_adj = 4/251 = 0.015936`).

### 2.2 Matched OpenITI Controls (`W=20` Light-Stem Rényi-2 Cross-Collision, $B = 250$ Shuffles)
| Corpus (`light_stem`) | Global $C_2$ | Effective Diversity $D_2 = 1/C_2$ | $W=20$ Obs | $B=250$ Pooled Null | Exact Lift | Empirical $p$ |
|---|---:|---:|---:|---:|---:|---:|
| Qur'an Uthmani | `0.005374` | `186.084672` | `0.009060` | `0.005365` | `1.688852×` | `1/251 = 0.003984` |
| *Kalīla wa-Dimna* (Prose) | `0.004852` | `206.103137` | `0.008747` | `0.004824` | **`1.813219×`** | `1/251 = 0.003984` |
| *al-Adab al-Kabīr* (Prose) | `0.006280` | `159.232900` | `0.009874` | `0.006180` | `1.597779×` | `1/251 = 0.003984` |
| Pre-Islamic Poetry (Pooled) | `0.002093` | **`477.682941`** | `0.003219` | `0.001996` | `1.612555×` | `1/251 = 0.003984` |

Honest Rule-5 reading: *Kalīla* prose exceeds Qur'an light-stem lift (`1.813219× > 1.688852×`), confirming local Rényi-2 collision lift is a shared Classical Arabic prose feature, while pre-Islamic poetry displays `>2.3×` higher global lexical dispersion $D_2$.

---

## 3. Pillar 2: Top-10-Stripped Arabic Context Neighborhood Topology ($B = 250$, Holm-Bonferroni)

Across the `15` author-selected roots (`14` thematic fields; see `../PREREGISTERED_HYPOTHESES.md`), ALL **`9 / 9`** context topology tests survive $B = 250$ verse-slot permutation + Holm-Bonferroni at $\alpha = 1/20$ (`p_adj = 9/251 = 0.035857` on every test, reproducible across both `odd` and `even` split-half internal consistency slices):
- **Specialized context Rényi-2 (`ctx_r2 > null`):** `ALL 0.006803` vs null `0.004292` (lift `1.584918×`), `ODD 0.007506` vs null `0.005117` (lift `1.466772×`), `EVEN 0.007303` vs null `0.004856` (lift `1.503764×`; all `p_adj = 0.035857`).
- **Distinct semantic neighborhoods (`ctx_jaccard < null`):** `ALL 0.182547 < 0.221820`, `ODD 0.156174 < 0.178221`, `EVEN 0.161662 < 0.188628` (all `p_adj = 0.035857`).
- **Enriched direct same-verse coupling (`cooccur > null`):** `ALL 173/1161 = 0.149009` vs null `0.113958`, `ODD 85/562 = 0.151246` vs null `0.109467`, `EVEN 88/599 = 0.146912` vs null `0.118022` (all `p_adj = 0.035857`).

---

## 4. Pillar 3: Two-Translator Projection Defect — $B = 250$ Lemma-Shuffle Null & 4-Stratum Distance Control

Across `131,343` root-linked verse pairs (`77,081` same-lemma + `54,262` cross-lemma; unrelated background `89.70%` Sahih / `92.30%` Pickthall):
- **Intra-Lemma Polysemy Floor:** Same-lemma pairs lose **`26,520/77,081 = 34.4054%`** (Sahih) and **`35,423/77,081 = 45.9556%`** (Pickthall).
- **Cross-Lemma Gap vs. $B = 250$ Within-Root Lemma-Label Shuffle Null:**
  - **Sahih International:** observed gap **`+0.334911`** (`67.8965% - 34.4054%`), `0/250` shuffles reach observed (null 95% interval `[-0.007821, +0.039565]`) -> **`p = 1/251 = 0.003984`** (`11/12` roots pass individual Holm-Bonferroni at `12/251 = 0.047809`; **`wzn` fails individually** at `44/251 = 0.175299`).
  - **M. M. Pickthall:** observed gap **`+0.273425`** (`73.2981% - 45.9556%`), `0/250` shuffles reach observed (null 95% interval `[+0.002051, +0.051353]`) -> **`p = 1/251 = 0.003984`** (`10/12` roots pass individual Holm-Bonferroni at `12/251 = 0.047809`; **`Erj` fails at `14/251 = 0.055777` and `wzn` fails at `98/251 = 0.390438`**).
- **4-Stratum Verse-Distance-Matched Control (Ruling Out Proximity Confounding):**

| Distance Stratum | Same Pairs | Cross Pairs | Sahih Gap (Cross − Same) | Pickthall Gap (Cross − Same) |
|---|---:|---:|---:|---:|
| `same_surah_near` ($\le 10$ verses) | `426` | `222` | **`+0.363723`** | **`+0.332889`** |
| `same_surah_far` ($> 10$ verses) | `1,620` | `897` | **`+0.253904`** | **`+0.247890`** |
| `diff_surah_near` ($\le 1000$ verses) | `24,728` | `16,259` | **`+0.327448`** | **`+0.273341`** |
| `diff_surah_far` ($> 1000$ verses) | `50,306` | `36,884` | **`+0.338899`** | **`+0.271827`** |

---

## 5. Reproduction Commands

```bash
# 1. Fetch & SHA-256-verify all 9 primary corpora from upstream (once, from repo root)
python3 fetch_corpora.py --dest ./corpora

# 2. Full LIVE recount from the downloaded primary texts (B=250 multi-shuffle nulls)
python3 -I -B -W error arabic-lexicon/arabic_lexicon_audit.py --live --output arabic-lexicon/arabic_lexicon_certificate.json

# 3. Offline pinned-fixture invariant replay (reads no corpus; live_corpus_recounted=false)
python3 -I -B -W error arabic-lexicon/arabic_lexicon_audit.py --standalone

# 4. Assertion-free R5, threshold-pinning, & hand-computed known-answer live-path tests
python3 -I -O -B -W error arabic-lexicon/test_arabic_lexicon_r5.py
```
