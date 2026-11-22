# Outside recount of the Arabic corpus results

This folder holds the scripts and saved outputs behind an outside review of pull request 1. The scripts recount every number in the two Arabic packages from the nine source texts, run fresh shuffle tests, probe the lineage checkers, and remove guards from the code to see whether the tests notice.

The scripts share no code with the repository. They read the repository's audit files only as data (the fixture numbers and the English stop-word list, through `ast`). The recount, test and sensitivity scripts import nothing from the repository. `lineage_probes.py` loads the two lineage checkers in order to probe them. `mutate2.py` runs the repository's own tests on altered copies.

No source text is stored here. Saved outputs hold counts, root names and short tokens only.

## Get the texts

Run this from the repository root. It needs a network. Any folder works.

```
python3 fetch_corpora.py --dest ./corpora
```

Every script that reads texts takes that folder as its first argument. The folder must have the layout `fetch_corpora.py` writes. The scripts need Python 3.12 and the standard library only.

## What each script checks

| Script | What it checks | Needs texts |
|---|---|---|
| `recount2.py` | Recounts the continuum package: root counts, per-layer cohesion, the 250 shuffle nulls with the authors' seeds, ring and inclusio, translation loss | yes |
| `recount2b.py` | Recounts the lexicon package: wazn concentration, controls, context topology, lemma shuffle, distance strata, per-root signs | yes |
| `nulls2.py` | Fresh shuffle tests with 2,000 draws and new seeds for every family, plus a stem-count-matched lemma control | yes |
| `holm_tables.py` | For each test family at 250 and 2,000 draws: smallest adjusted p, and how many exceedances would flip each result | no |
| `sens.py` | Recomputes the translation-loss numbers under other English word rules | yes |
| `variant_basmala.py` | Recomputes the Qur'an layers with the repeated basmala removed | yes |
| `lineage_probes.py` | Feeds extra and altered edges to both lineage checkers | no |
| `mutate2.py` | Removes one guard or one convention at a time in a scratch copy and runs the package tests under `-I -O -B -W error` | no |
| `retract_search.py` | Searches reports, README, scripts and certificates for sentences that assert retracted claims | no |
| `ast_scan.py` | Counts `assert` statements and float literals in every Python file | no |

`rc_common.py` and `rc2_common.py` hold the shared readers and helpers.

## Rerun each result

Run from the repository root. Use the same commands with `-I -O -B` and `-I -B -W error` in place of `-I -B`. The output is identical in all three. `<dir>` is the folder from the step above.

```
python3 -I -B verification/outside-recount/recount2.py <dir>
python3 -I -B verification/outside-recount/recount2b.py <dir>
python3 -I -B verification/outside-recount/nulls2.py <dir> 2000
python3 -I -B verification/outside-recount/holm_tables.py
python3 -I -B verification/outside-recount/sens.py <dir>
python3 -I -B verification/outside-recount/variant_basmala.py <dir> 500
python3 -I -B verification/outside-recount/lineage_probes.py
python3 -I -B verification/outside-recount/mutate2.py <new empty scratch folder>
python3 -I -B verification/outside-recount/retract_search.py
python3 -I -B verification/outside-recount/ast_scan.py
```

`mutate2.py` never deletes anything. It needs a scratch folder that does not exist yet and refuses to reuse one. `nulls2.py` takes about 15 minutes of processor time and `variant_basmala.py` about 5.

## Expected results

The saved output of each command is in `outputs/`, one file per mode (`Ib` is `-I -B`, `IOb` is `-I -O -B`, `IbWerror` is `-I -B -W error`).

| Script | Last line or key result |
|---|---|
| `recount2.py` | `checks=65 match=65 diff=0` |
| `recount2b.py` | `checks=34 match=34 diff=0` |
| `nulls2.py` | `nulls2 done`. All 12 layer cells and all 9 context tests rejected at 0.05 after Holm. None of the 6 inclusio tests rejected (smallest adjusted p 0.2939). Pickthall `Erj` is rejected (0.0430) and `wzn` is not |
| `holm_tables.py` | At 250 draws the 12-cell family has smallest adjusted p 12/251 = 0.04781 |
| `sens.py` | The 7-root Sahih loss is 50.9% under the repository's rule and 24.3% to 64.0% under three other rules |
| `variant_basmala.py` | Removing the basmala changes the raw, rasm and stem lifts by at most 0.09 |
| `lineage_probes.py` | Both checkers reject the order, overlap, teacher, self-loop and missing-citation probes, and accept the legal edge with a nonsense citation |
| `mutate2.py` | `summary: 47 tried, 45 caught, 2 survived` (the English minimum word length, in both packages) |
| `retract_search.py` | No hit asserts a retracted claim. The hits state the retraction |
| `ast_scan.py` | `total bare assert statements: 0` |

## Not run

- The external `aletheia` tool is not in the repository, so its mutation counts were not reproduced.
- `fetch_corpora.py` was not run against the network by the reviewer. The nine files were fetched from the same upstream commits and matched the nine pins.
- The cited editions behind the historical inputs were not checked against the books.
- `nulls2.py` and `variant_basmala.py` use more draws and different seeds than the repository, so their p values differ from the repository's 250-draw values.
