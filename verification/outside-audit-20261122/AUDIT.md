# Audit: Foundation-0/bayt-al-hikma

Date: 2026-11-22. Target: `main` at `c08544ffc735c003c39bf2745eb2b27b0b226721`.

Site branch audited too: `site/github-pages` at `42dc8af` (open PR 6).

Method: Aletheia single-agent loop with one independent verifier subagent.

The subagent wrote its own checker. It shares no code with the repo.

All checks ran on Python 3.14.6, macOS. No other version was tested.

Provenance: independent automated audit of the commit above, run on 2026-11-22. This file is the repo copy of the audit.

## Finding to issue map

| Finding | Where it is tracked |
|---|---|
| F1, no CI runs the verifier | Issue 7 |
| F2, stemmer sensitivity range | Issue 8 |
| F5, W=10 lift order sentence | Issue 9 |
| F3, F4, F6, F7, F8, F9 | This report only, no issue |

Site copies of F2 and F5 were fixed on the site branch in commit `1015b8a`.

## Verdict

The computational claims hold inside their stated scope.

Offline replay passes. The live recount from the 9 upstream texts passes.

No headline number failed. One wording claim needs narrowing (F5).

The main risks are process risks, not wrong numbers. See F1, F2 and F3.

Novelty stays `N0` everywhere. That default is correct and honest.

## What was verified

### Offline verifier, three modes (exact)

`verify_all_standalone.py` passed under `-I -B`, `-I -O -B` and `-I -B -W error`.

All three stdout hashes match. SHA-256 of the 962-byte stdout: `1d1e22ad6a983e66b1a81f4679f56f1c0dc7593f982393d5dc6b4ec7ff208af1`.

Output says `arabic_live_corpora_recounted=false`. That limit is printed, not hidden.

The independent subagent got the same hashes in a clean clone.

### Live recount (reference replay of a sampled method)

`fetch_corpora.py` fetched all 9 texts. Every size and SHA-256 matched its pin.

`verify_all_standalone.py --live` then passed in 123.9 seconds.

Both Arabic certificates came back byte for byte. Live mode reported true.

So the certificates are not just stored numbers. The code rebuilds them today.

### Certificates (exact)

All 4 certificates parse as strict JSON. No floats. No duplicate keys.

Each inner `certificate_sha256` equals the hash of the body without that field.

The subagent reproduced all 4 inner digests and 14 rational checks.

Checks include the Pell solutions, Brahmagupta area and the amicable pairs.

### Code hygiene (exact)

Bare `assert` statements: 0 in all 12 Python files, by AST count.

Float literals in non-test code: 0. Test floats are must-fail inputs.

CRLF bytes: 0. Tracked `__pycache__` or `.pyc` files: none.

Secret patterns and home path leaks: none found.

Holm and rank-p code read correctly. The Holm rule uses the running max.

The shuffle is Fisher-Yates over a 64-bit LCG. Seeds are fixed in code.

Fresh-seed reruns in PR 2 back the same family verdicts.

## Claim ledger

Labels follow Aletheia: exact, sampled, reference replay, anchor.

| Claim | Class | Verdict |
|---|---|---|
| Polymath and veins certificates rebuild byte for byte | exact | Verified |
| Arabic live certificates rebuild from the 9 texts | reference replay | Verified |
| 12 cohesion cells beat per-layer shuffles, B=250, Holm | sampled | Verified, see F4 |
| Cohesion ladder reversed | sampled | Stands narrowed, F5 |
| Pointwise mirror falsified | sampled | Verified as falsified |
| Boundary inclusio inconclusive | sampled | Verified |
| Wazn concentration 0.926980 | sampled, one corpus | Verified in scope |
| Lemma gap +0.3349 and +0.2734 | sampled | Verified |
| Translation loss 50.91% and 65.88% | sampled, one stemmer | Stands narrowed, F2 |
| Lineage graphs consistent and cited | exact, encoding only | Verified in scope |
| History in the lineage tables is true | anchor | Not checked |
| External mutation counts 392/392, 83/83 | anchor, external tool | Not shown, F6 |

Mirror counts check out: 246 nulls at or above, 4 at or below, no ties.

The 19,356 and 19,347 verb totals also check out.

The gap is 9 Form XII tokens. The lexicon count covers Forms I to X only.

## Findings

Each narrowing finding got a second pass with a brief to overturn it.

Rulings use the Aletheia words: stands, stands narrowed, or falls.

### F1. No CI runs the verifier (medium)

The repo has no `.github` folder. Only CodeQL and Pages workflows run.

The org ruleset `protect-main` requires a PR and one approval.

It sets no required status checks. A broken certificate could merge on review alone.

Second pass: the rule works today by discipline. PRs 3 and 5 update pinned hashes.

Ruling: stands narrowed. Fix: add one workflow for the offline verifier.

The offline run takes about 2 seconds, so the cost is small.

### F2. Translation loss per cent depends on the stemmer (medium)

The 50.91% figure is exact for the pinned English word rules in the code.

PR 2 (`sens.py`) gives 24.3% to 64.0% under three other strict rules.

Two looser rules give 8.0% and 6.3%. The full span is 6.3% to 64.0%.

Reports and the site state the hand-picked roots. They give no such range.

Second pass: the pinned code is the instrument, so the figure is well defined.

The lemma gap is the robust result. It survives shuffles, distance bands and PR 2.

Ruling: stands narrowed. Read the per cent as one instrument reading.

Fix: quote the sensitivity range wherever the per cent appears.

### F3. Live fetch depends on mutable sources (medium-low)

Six texts use commit-pinned URLs. The three Tanzil URLs name no version.

Hash pins fail closed, so a changed upstream breaks loudly, not silently.

But there is no archived fallback if Tanzil changes a file.

First fetch here also failed: stock macOS Python lacks CA certificates.

The error was a raw `URLError` traceback, exit 1, no partial files written.

With `SSL_CERT_FILE=/etc/ssl/cert.pem` the fetch passed in 6.5 seconds.

Ruling: stands. Fix: wrap the error, document the macOS fix, mirror the texts.

Check each corpus licence before mirroring. The manifest lists them.

### F4. B=250 puts borderline labels at the resolution floor (low-medium)

The 12-cell Holm value is `12/251 = 0.0478`, just under 0.05 by design.

The protocol file states this choice openly. It is not a hidden trick.

PR 2 reran 2,000 fresh shuffles. All 12 cells still rejected after Holm.

All 9 context tests also held. Inclusio still did not reject any test.

One per-root label flipped: Pickthall `Erj` fails at B=250, passes at 2,000.

Ruling: stands narrowed. Family claims are robust. Borderline roots are not.

Fix: use a larger B for per-root claims in the next confirmatory run.

### F5. Lift order sentence overstates one cell (low)

At W=20 and W=40 the lift order is raw, rasm, stem, root. Full reversal holds.

At W=10 root lift is 1.876457 and rasm is 1.876153, from the certificate.

Root beats rasm there by 0.000304. Stem beats both. Raw still leads by far.

So "reverses at every window" fails as a strict total order at W=10.

The same sentence appears in the report, the README and the site index.

Ruling: stands narrowed. The retraction itself is right. One sentence is loose.

Fix: say raw leads and root drops from first to near last, with the W=10 near tie.

### F6. External mutation counts cannot be rerun from this repo (low)

README and reports cite `392/392` and `83/83` external mutation results.

The tool is Aletheia v2.0.0 on an open PR in another repo. It is not vendored.

The text labels these counts as external receipts. That label is honest.

From this repo alone the verdict is not shown. No command here reproduces them.

In-repo support exists: issue 4 swept 121 stemmer mutants, PR 2 killed 45 of 47.

Ruling: stands. Fix: pin the tool commit, or call the counts author-reported.

### F7. Duplicated oracle code needs twin fixes (low)

The two Arabic oracles share 399 non-empty lines of text.

The stemmer is identical apart from the exception class name.

Both stop-word sets match: 87 words each. Sample outputs match too.

Issue 4, PR 3 and PR 5 all had to edit both packages for one function.

Second pass: standalone packages are a stated design choice, and it has value.

Ruling: stands as a trade-off. Add a parity check instead of a refactor.

One verifier step could compare both stop-word sets and stemmer outputs.

### F8. The `dec6` suffix means two things (low)

Arabic certificates round half up to 6 places. Lineage certificates truncate.

Both use the same `_dec6` suffix. Only function docstrings say which rule applies.

Exact fractions sit beside every value, so no result changes.

The largest display gap is 0.000001. Still, cross-package reads can mislead.

Fix: rename the truncating fields, or state the rule inside each certificate.

### F9. Small metadata gaps (low)

No minimum Python version is stated. Only 3.14.6 was tested in this audit.

There is no `CITATION.cff` and no release tag for the certificate set.

At the audited commit `LICENSE` is a shortened paraphrase of Apache-2.0 (134 lines, 7,249 bytes, no appendix), not the verbatim text. GitHub reported the licence as "Other". Pull request 12 later replaced it with the verbatim text (202 lines, 11,358 bytes).

The wiki is enabled but unused. The verifier does not pin the README.

It cannot pin itself either. The git commit is the root of trust. Say so once.

## Open pull requests

### PR 5: stemmer mutant tests (closes issue 4)

Verifier passes on head `93eecae`. Both Arabic suites pass.

New tests cover each row of issue 4, including the full 87-word set.

The `119/119` count rests on the external mutator. See F6 for that limit.

Ready for review and merge on your call.

### PR 2: outside recount

This is the strongest outside evidence in the repo history.

It recounts 65 of 65 and 34 of 34 checks with no shared code.

Its base predates PR 3, so one expected-output line is now stale.

The `mutate2` survivor it reports was fixed by PR 3 and PR 5 work.

Ask for a rebase and refreshed outputs before merging it as a receipt.

### PR 6: Pages site (this session)

All 22 fresh site checks passed: 4 inner digests and 18 headline numbers.

The corpus byte total on the site, 10,084,822, matches the manifest sum.

Tags keep their limits: the lineage page says consistency, not discovery.

Two site fixes follow from F2 and F5. Both landed on the site branch in `1015b8a`.

Other site limits: Google Fonts is an external request on every page.

The social image is SVG, which some scrapers ignore.

No browser check ran here, as no Chromium is installed on this Mac.

Pages returns 404 until merge, because `docs/` is only on the PR branch.

## Not checked in this audit

Cited books were not opened. Historical inputs rest on the cited editions.

PR 2 states the same limit for its recount, so two audits share it.

The lineage checker accepts a well-formed edge with a nonsense citation.

That behaviour matches its label: encoding consistency only.

Prior art needs no verdict. Every package claims `N0` and nothing above it.

## Bottom line

Verified within stated scope. No falsified headline stands in the repo.

Fix order: F1 first, then F2 wording, then PR 2 refresh, then F5 wording.

`main` itself was not modified during this audit. Issues 7, 8 and 9 were filed, and the site copies of F2 and F5 were fixed on the site branch in commit `1015b8a`.

> Automated posting by agentic team with human oversight.
