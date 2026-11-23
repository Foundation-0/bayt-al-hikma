# Bayt al-Ḥikma

Classical Arabic corpus analyses and polymath lineage verification under Aletheia v2.0.0: pure-ℚ (exact rational) Python 3 stdlib research packages, zero IEEE-754 floats on trust paths.

## Tracks

- **Classical Arabic Corpus Studies** — `arabic-continuum/` (AUDIT-091-V2) and `arabic-lexicon/` (AUDIT-094-V2): root-pattern cohesion, *wazn* agency/reciprocity, lexical-edge loss across 9 SHA-256-pinned primary texts.
- **Polymath Lineage** — `polymath-lineage/` (AUDIT-092R2) and `veins-and-branches/` (AUDIT-095R): offline pure-ℚ verifications across 23 cited scholars (c. 287 BCE – 1543 CE).

## Reproduce

- Offline: `python3 verify_all_standalone.py` replays oracle invariants on pinned fixtures.
- Live recount: `fetch_corpora.py` + `verify_all_standalone.py --live` recomputes from the 9 primary texts with B = 250 multi-shuffle nulls and Holm-Bonferroni correction.

Full scope, layout, reports, and the pre-registered hypotheses ledger are in the [repository README](https://github.com/Foundation-0/bayt-al-hikma#readme).
