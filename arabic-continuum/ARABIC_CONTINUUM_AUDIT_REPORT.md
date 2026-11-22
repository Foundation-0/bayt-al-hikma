# Classical Arabic Layered Cohesion, Ring-vs-Inclusio Multi-Shuffle Adjudication & Translation Remainder (v2)

- **Audit ID:** `AUDIT-091-V2` (updated directly in response to peer review `6011346623`)
- **Governance Standard:** Aletheia v2.0.0 (`OWN_TERMS_FIRST`, Law 2b, Law 4 honest `N0` novelty default, Law 5 feature-naming guard)
- **Execution Modes (Explicitly Distinguished):**
  - **Live Recount (`--live` / `--corpus-dir ./corpora`):** SHA-256-verifies all 9 primary corpora fetched via `../fetch_corpora.py` and recomputes EVERY count and EVERY $B = 250$ multi-shuffle null directly from the raw primary texts (`mode: "live_corpus_recount"`, `live_corpus_recounted: true`).
  - **Offline Standalone Replay (default / `--standalone`):** Reads NO corpus text; replays oracle invariants and exact rational calculations on the pinned verbatim fixture (`mode: "standalone_fixture_replay"`, `live_corpus_recounted: false`).
- **Exact Pinned Certificate Digests:**
  - `live_corpus_recount` (`arabic_continuum_certificate.json`): `99ec338fc7aec339c1ea5216afd2a0bcac4bff647d487a1a3f80c403b581b951`
  - `standalone_fixture_replay` (`--standalone`): `252e1dad44ab0d1c9653c41de28e0170f5a28dffc69ea1bea18f47bd9179b757`
- **Novelty Classification (Law 4 Honest Default):** **`N0`** (exact pure-$\mathbb{Q}$ computational quantification and honest falsification/retraction ledger on Classical Arabic primary texts; see `../PREREGISTERED_HYPOTHESES.md` for full retrospective disclosure and pre-registered protocol).

---

## 1. Methodological Disclosures, Retractions & Revisions Closing Review `6011346623`

1. **Full Live Reproducibility (`../fetch_corpora.py`):** All 9 primary corpora are fetched directly from their verified upstream URLs with pinned editions, licences, byte sizes, and SHA-256 digests (`python3 fetch_corpora.py --dest ./corpora`), then recounted live (`python3 arabic-continuum/arabic_continuum_audit.py --live`).
2. **Feature-Naming Guard Scope:** `enforce_zero_numerology_policy` is explicitly labelled as a **feature-label hygiene filter** (`guard_scope: "feature_label_filter_only_not_statistical_proof"`), NOT a statistical proof of methodology. Methodological validity rests on `../PREREGISTERED_HYPOTHESES.md`, $B = 250$ deterministic multi-shuffle nulls, exact Holm-Bonferroni correction, and matched OpenITI controls.
3. **Explicit Retraction of the Naive Absolute-Overlap Cohesion Ladder (Finding #4):**
   - Earlier reporting highlighted the raw monotonicity `raw < rasm < stem < root` in absolute adjacent-window Jaccard overlap (`0.0325 < 0.0521 < 0.0666 < 0.0941` at `W=20`).
   - Computing full per-layer $B = 250$ shuffle nulls across all `12` `(layer, W)` cells proves that **absolute monotonicity is a vocabulary-coarsening baseline artifact**: once normalized by each layer's own shuffle null (`obs / null`), **the ordering REVERSES** (`raw > rasm / stem > root` at every scale `W = 10, 20, 40`).
   - We therefore **explicitly retract** the absolute-overlap ladder claim and report the full 12-cell per-layer null-normalized lift matrix below (`cohesion_lift_reverses_absolute_ladder: true`).
4. **Honest Inconclusive Adjudication of Post-Hoc Boundary *Inclusio* (Findings #3 & #7):**
   - **Global pointwise mirror symmetry** (`i` vs `L - 1 - i`) is **FALSIFIED**: observed `1642/40725 = 0.040319` lies strictly below both the half-shifted baseline (`0.040355`) and the $B = 250$ verse-permutation null (`0.042126`; only `4/250` nulls $\le$ obs, lower-tail $p = 5/251 = 0.019920 \le 0.05$).
   - **Post-hoc boundary *inclusio*** (`first 10%` vs `last 10%` minus `first 10%` vs `middle 10%`) **FAILS Holm-Bonferroni at $B = 250$ across ALL `6/6` Qur'anic tests** (minimum adjusted $p = 42/251 = 0.167331 > 0.05$ on `odd_strip10`; pooled `all` adjusted $p = 124/251 = 0.494024$) AND **FAILS to separate from Ibn al-Muqaffa's natural framed prose chapters** in *Kalīla wa-Dimna* (`kalila_nat` $\Delta = +0.009739$, $p = 20/251 = 0.079681$ vs. Qur'an `all` $\Delta = +0.008283$, $p = 31/251 = 0.123506$).
   - Verdict is therefore reported honestly as **`boundary_inclusio_status: "EXPLORATORY_INCONCLUSIVE_NOT_SEPARATED"`**.
5. **No `"Unseen"` Claim:** Odd/even surah splits are strictly labelled **`split_half_internal_consistency`** (never `"strictly unseen"`), because the full text was inspected during design.
6. **Selection-Rule Disclosure (Pillar 3):** The 9 Pillar-3 roots (`ftq`, `rtq`, `sbH`, `mdd`, `wsE`, `flk`, `kwr`, `qdr`, `zwj`) are explicitly tagged `selection_rule: "author_selected_thematic_set_disclosed"` (see `../PREREGISTERED_HYPOTHESES.md`).

---

## 2. Pillar 1: Non-Concatenative Lattice & Full 12-Cell Per-Layer Null-Normalized Lift ($B = 250$, Holm-Bonferroni)

### 2.1 Root × *Wazn* Lattice Inventory (Leeds Quranic Arabic Corpus v0.4)
- **`1,642` unique roots**, **`4,657` unique `(root, lemma)` pairs** (`2.836175` lemmas/root), **`3,923` unique `(root, POS:Form:Deriv)` cells** (`2.389160` cells/root), across **`49,968` root-bearing tokens** and **`19,356` tagged verbs** across `11` verb forms (`I: 12,347`, `II: 1,300`, `III: 334`, `IV: 3,487`, `V: 414`, `VI: 77`, `VII: 51`, `VIII: 963`, `IX: 5`, `X: 369`, `XII: 9`).

### 2.2 Full 12-Cell Per-Layer Null-Normalized Lift Matrix (Retracting Naive Absolute Ladder)
Every one of the `12` `(layer, W)` cells beats all `250/250` per-layer random shuffles (`ge_count = 0`, raw $p = 1/251 = 0.003984$, Holm-Bonferroni adjusted $p = 12/251 = 0.047809 \le 0.05$), yet **per-layer null-normalized lift (`obs / null`) REVERSES the naive absolute ordering at every window scale**:

| Window $W$ | Layer | Observed Jaccard (`obs`) | $B=250$ Pooled Null (`null`) | Exact Lift (`obs / null`) | Null $\ge$ Obs | Holm $p_{\text{adj}}$ |
|---:|---|---:|---:|---:|---:|---:|
| `10` | **`raw`** | `0.020506` (`3075/149959`) | `0.008171` (`313169/38327853`) | **`2.509622×`** | `0/250` | `12/251 = 0.047809` |
| `10` | `rasm` | `0.033948` (`4968/146340`) | `0.018095` (`679579/37556903`) | `1.876153×` | `0/250` | `12/251 = 0.047809` |
| `10` | `stem` | `0.044275` (`6342/143242`) | `0.023318` (`866971/37181030`) | `1.898772×` | `0/250` | `12/251 = 0.047809` |
| `10` | `root` | `0.070409` (`5961/84662`) | `0.037523` (`869364/23169133`) | `1.876457×` | `0/250` | `12/251 = 0.047809` |
| `20` | **`raw`** | `0.032502` (`4723/145316`) | `0.015435` (`582523/37740278`) | **`2.105700×`** | `0/250` | `12/251 = 0.047809` |
| `20` | `rasm` | `0.052127` (`7253/139141`) | `0.031069` (`1131561/36420990`) | `1.677785×` | `0/250` | `12/251 = 0.047809` |
| `20` | `stem` | `0.066625` (`8954/134393`) | `0.040398` (`1443498/35731606`) | `1.649213×` | `0/250` | `12/251 = 0.047809` |
| `20` | `root` | `0.094115` (`7283/77384`) | `0.063042` (`1373771/21791348`) | `1.492894×` | `0/250` | `12/251 = 0.047809` |
| `40` | **`raw`** | `0.046046` (`6396/138905`) | `0.027892` (`1023812/36705935`) | **`1.650846×`** | `0/250` | `12/251 = 0.047809` |
| `40` | `rasm` | `0.069585` (`9054/130114`) | `0.048060` (`1669728/34742910`) | `1.447895×` | `0/250` | `12/251 = 0.047809` |
| `40` | `stem` | `0.087996` (`10868/123506`) | `0.063284` (`2126089/33595990`) | `1.390489×` | `0/250` | `12/251 = 0.047809` |
| `40` | `root` | `0.120019` (`8300/69156`) | `0.097788` (`1940392/19842861`) | `1.227335×` | `0/250` | `12/251 = 0.047809` |

- **Tier-4B POS-Preserving Root Null (`B = 250`):** Root cohesion still exceeds POS-stratified shuffles (`0/250`, $p = 1/251$) across all three scales (`W=10`: `1.779309×`; `W=20`: `1.483473×`; `W=40`: `1.249566×`) and across both `odd` and `even` split-half internal consistency slices (`0/250` on all 6 split-half cells).

### 2.3 Matched Classical Arabic OpenITI Negative Controls (`W = 20`, Light Stem, $B = 250$)
| Corpus (`light_stem`, `W=20`) | Observed Jaccard | $B=250$ Pooled Null | Exact Lift | Empirical $p$ |
|---|---:|---:|---:|---:|
| Qur'an Uthmani | `0.066625` (`8954/134393`) | `0.040398` | `1.649213×` | `1/251 = 0.003984` |
| *Kalīla wa-Dimna* (Prose) | `0.070811` (`5398/76231`) | `0.038856` | **`1.822415×`** | `1/251 = 0.003984` |
| *al-Adab al-Kabīr* (Prose) | `0.073441` (`1178/16040`) | `0.047207` | `1.555725×` | `1/251 = 0.003984` |
| Pre-Islamic Poetry (Pooled) | `0.026125` (`501/19177`) | `0.016582` | `1.575484×` | `1/251 = 0.003984` |

Honest Rule-5 interpretation: *Kalīla wa-Dimna* prose exhibits **higher** light-stem lift (`1.822415×`) than Qur'anic prose (`1.649213×`), confirming that local topical cohesion above shuffle null is a **shared Classical Arabic prose property** rather than a Qur'an-unique anomaly.

---

## 3. Pillar 2: Pointwise Mirror Falsification & Honest Boundary-*Inclusio* Multi-Shuffle Adjudication ($B = 250$)

- **Pointwise Mirror (`i` vs `L - 1 - i`) — FALSIFIED:**
  - Observed `1642/40725 = 0.040319` < half-shifted `1642/40689 = 0.040355` < $B=250$ permutation null `428283/10166734 = 0.042126` (`246/250` nulls $\ge$ obs; `4/250` nulls $\le$ obs -> lower-tail $p_{\le} = 5/251 = 0.019920 \le 0.05$).
- **Post-Hoc Boundary *Inclusio* ($\Delta = \text{first–last } 10\% - \text{first–middle } 10\%$) — `EXPLORATORY_INCONCLUSIVE_NOT_SEPARATED`:**

| Slice / Control | Inclusio | Middle | $\Delta$ (Obs) | $B=250$ Null 95% Interval | Null $\ge \Delta$ | Raw $p$ | Holm $p_{\text{adj}}$ (6 Qur'an Tests) | Reject at $\alpha = 0.05$? |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| Qur'an `all` | `0.147771` | `0.139488` | `+0.008283` | `[-0.011725, +0.012904]` | `30/250` | `31/251 = 0.123506` | `124/251 = 0.494024` | **No** |
| Qur'an `odd` | `0.149698` | `0.140199` | `+0.009500` | `[-0.015477, +0.020525]` | `50/250` | `51/251 = 0.203187` | `147/251 = 0.585657` | **No** |
| Qur'an `even` | `0.146010` | `0.138824` | `+0.007185` | `[-0.017236, +0.017540]` | `48/250` | `49/251 = 0.195219` | `147/251 = 0.585657` | **No** |
| Qur'an `all_strip10` | `0.118232` | `0.107362` | `+0.010870` | `[-0.010060, +0.011564]` | `11/250` | `12/251 = 0.047809` | `60/251 = 0.239044` | **No** |
| Qur'an `odd_strip10` | `0.123391` | `0.108696` | `+0.014695` | `[-0.020179, +0.014566]` | `6/250` | `7/251 = 0.027888` | `42/251 = 0.167331` | **No** |
| Qur'an `even_strip10` | `0.113535` | `0.106112` | `+0.007423` | `[-0.016530, +0.018212]` | `64/250` | `65/251 = 0.258964` | `147/251 = 0.585657` | **No** |
| *Kalīla* `natural` chapters | `0.137421` | `0.127682` | `+0.009739` | `[-0.010408, +0.013258]` | `19/250` | `20/251 = 0.079681` | — (control) | — |
| *Kalīla* `arbitrary` 60-line | `0.088799` | `0.090895` | `-0.002096` | `[-0.009296, +0.008903]` | `161/250` | `162/251 = 0.645418` | — (control) | — |

Not a single one of the `6` Qur'anic boundary-*inclusio* slices survives Holm-Bonferroni correction at $\alpha = 0.05$, and the unstripped Qur'an $\Delta$ (`+0.008283`, $p = 0.123506$) is actually **smaller** than *Kalīla wa-Dimna*'s natural framed chapters (`+0.009739`, $p = 0.079681$).

---

## 4. Pillar 3: Two-Instrument Translation Remainder (Disclosed Author-Selected 9-Root Set)

Across the `7` multi-verse roots (`365` verse occurrences, `14,670` root-linked verse pairs; plus `2` hapax roots `ftq`, `rtq`; unrelated background loss `897/1000 = 89.70%` Sahih, `923/1000 = 92.30%` Pickthall):
- **Pooled single-gloss miss rate:** `167/365 = 45.7534%` (Sahih) vs `44/73 = 60.2740%` (Pickthall).
- **Pooled pairwise lexical-edge loss:** `3734/7335 = 50.9066%` (Sahih) vs `1933/2934 = 65.8828%` (Pickthall) — both $\ge 50\%$ yet strictly below unrelated background (`89.70%` / `92.30%`), with `4` roots (`mdd`, `wsE`, `qdr`, `zwj`) losing $\ge 40\%$ of edges in BOTH translators (`max_translator_edge_divergence = 1.000000` on 2-verse `kwr`).
- **Scope note:** For the distance-controlled, within-root lemma-shuffle decomposition across `131,343` pairs, see `../arabic-lexicon/ARABIC_LEXICON_TOPOLOGY_REPORT.md` and `../PREREGISTERED_HYPOTHESES.md`.

---

## 5. Reproduction Commands

```bash
# 1. Fetch & SHA-256-verify all 9 primary corpora from upstream (once, from repo root)
python3 fetch_corpora.py --dest ./corpora

# 2. Full LIVE recount from the downloaded primary texts (B=250 multi-shuffle nulls)
python3 -I -B -W error arabic-continuum/arabic_continuum_audit.py --live --output arabic-continuum/arabic_continuum_certificate.json

# 3. Offline pinned-fixture invariant replay (reads no corpus; live_corpus_recounted=false)
python3 -I -B -W error arabic-continuum/arabic_continuum_audit.py --standalone

# 4. Assertion-free R5, threshold-pinning, known-answer mini-corpus, & fetch_corpora tests
python3 -I -O -B -W error arabic-continuum/test_arabic_continuum_r5.py
```
