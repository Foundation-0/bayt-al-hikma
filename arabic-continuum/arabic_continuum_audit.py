"""Dual-mode (live_corpus_recount + standalone_fixture_replay) audit runner (v2)
for Classical Arabic / Qur'anic layered cohesion, ring-vs-inclusio multi-shuffle
adjudication, and 2-translator remainder.

Modes:
- Default / --standalone: offline threshold & invariant replay on pinned counts
  (mode='standalone_fixture_replay', live_corpus_recounted=False; reads no text).
- --live or --corpus-dir <path>: SHA-256 verifies all 9 primary corpora on disk
  (downloadable via ../fetch_corpora.py --dest ./corpora) and recomputes every
  count and every B=250 multi-shuffle null directly from the raw primary texts
  (mode='live_corpus_recount', live_corpus_recounted=True).

Pure Python 3 stdlib. Zero floats on trust paths. Zero bare assert statements.
"""

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import os
import re
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from arabic_continuum_oracle import (
    ArabicOracleError,
    MIN_MULTISHUFFLE_B,
    audit_ring_vs_inclusio_multishuffle_exact,
    audit_root_pattern_lattice_and_cohesion_exact,
    audit_translation_remainder_exact,
    block_jaccard_cohesion_exact,
    canonical_json_bytes,
    certify_arabic_own_terms_5axis_gate,
    det_shuffle_exact,
    en_content_stems,
    light_stem_ar,
    stratified_shuffle_exact,
    to_rasm,
)


TARGET_ROOTS = ("ftq", "rtq", "sbH", "mdd", "wsE", "flk", "kwr", "qdr", "zwj")

AUDIT_FEATURES = (
    "non_concatenative_root_wazn_lattice",
    "per_layer_null_normalized_lift_w10_w20_w40",
    "multishuffle_b250_tier4a_and_tier4b_pos_nulls",
    "classical_arabic_prose_and_poetry_controls",
    "pointwise_mirror_falsification_vs_inconclusive_inclusio",
    "split_half_internal_consistency_odd_even",
    "two_instrument_translation_remainder_sahih_pickthall",
)

EXPECTED_CORPUS_SHA256 = {
    "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt": (
        "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46"
    ),
    "openiti_controls/antara_muallaqa.txt": (
        "e346bde4145972d7ef243777cf6a02ced4ec96e0ddf402d5ad7f21b6d029eb38"
    ),
    "openiti_controls/ibn_muqaffa_adab_kabir.txt": (
        "7b6aa0a311465a28ae5f52b04c919fd89118e8b29cb283ac96a71710c62381b1"
    ),
    "openiti_controls/ibn_muqaffa_kalila.txt": (
        "0b55371e4c69f44ffb5a1876b11e174398f3f84f400302c24007bdf1004afdc9"
    ),
    "openiti_controls/imru_al_qays_diwan.txt": (
        "7236a43a2309e92f556f6347d3b2279100eab606405563b2f07e9c54d1bd04d7"
    ),
    "openiti_controls/tarafa_diwan.txt": (
        "bde2655e74a09670c78decab34573e2913f2ba9e90b04438fc65410a49aedf38"
    ),
    "tanzil-en.pickthall.txt": (
        "4aabbfa9d96796f5a6b0217d2c39dce1a3084f772bf6f2650e37082a774e3cc7"
    ),
    "tanzil-en.sahih.txt": (
        "a1778a1a56695d9b59ae910809ec46d9f4a55f05961de51cd56e6ebcf9040883"
    ),
    "tanzil-quran-uthmani.txt": (
        "bf4f57b968d03f4131c070b1e285da9be0e0a108a21c910e872801ca273312c8"
    ),
}

VF_RE = re.compile(r"(?:^|\|)\((II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\)(?:\||$)")
ROOT_RE = re.compile(r"ROOT:([^|]+)")
LEM_RE = re.compile(r"LEM:([^|]+)")
OPENITI_NOISE_RE = re.compile(r"PageV\d+P\d+|ms\d+|%~~%|~%")

SEED_LAYER_RAW = 20261000
SEED_LAYER_RASM = 20262000
SEED_LAYER_STEM = 20263000
SEED_LAYER_ROOT = 20264000
SEED_ROOT_T4B = 20265000
SEED_ODD_T4B = 20266000
SEED_EVEN_T4B = 20267000
SEED_CTRL_KALILA = 20268000
SEED_CTRL_ADAB = 20268500
SEED_CTRL_POETRY = 20269000
SEED_RING_PERM = 20269500
SEED_BG_PAIRS = 2026097
BG_PAIR_COUNT = 1000
WINDOW_SIZES = (10, 20, 40)
ARB_CHUNK_LINES = 60

STANDALONE_FIXTURE = {
  "bg_pickthall_pair": [
    923,
    1000
  ],
  "bg_sahih_pair": [
    897,
    1000
  ],
  "control_w20_metrics": {
    "adab_prose": {
      "ge_count": 0,
      "null_pooled": [
        204317,
        4328092
      ],
      "obs": [
        1178,
        16040
      ]
    },
    "kalila_prose": {
      "ge_count": 0,
      "null_pooled": [
        789689,
        20323672
      ],
      "obs": [
        5398,
        76231
      ]
    },
    "poetry_pooled": {
      "ge_count": 0,
      "null_pooled": [
        81887,
        4938238
      ],
      "obs": [
        501,
        19177
      ]
    },
    "quran_stem": {
      "ge_count": 0,
      "null_pooled": [
        1443498,
        35731606
      ],
      "obs": [
        8954,
        134393
      ]
    }
  },
  "n_shuffles": 250,
  "pinned_sha256s": {
    "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt": "a1d12923815341face765083805d2148ed2d9f5cc3f7d6665219d887675d8c46",
    "openiti_controls/antara_muallaqa.txt": "e346bde4145972d7ef243777cf6a02ced4ec96e0ddf402d5ad7f21b6d029eb38",
    "openiti_controls/ibn_muqaffa_adab_kabir.txt": "7b6aa0a311465a28ae5f52b04c919fd89118e8b29cb283ac96a71710c62381b1",
    "openiti_controls/ibn_muqaffa_kalila.txt": "0b55371e4c69f44ffb5a1876b11e174398f3f84f400302c24007bdf1004afdc9",
    "openiti_controls/imru_al_qays_diwan.txt": "7236a43a2309e92f556f6347d3b2279100eab606405563b2f07e9c54d1bd04d7",
    "openiti_controls/tarafa_diwan.txt": "bde2655e74a09670c78decab34573e2913f2ba9e90b04438fc65410a49aedf38",
    "tanzil-en.pickthall.txt": "4aabbfa9d96796f5a6b0217d2c39dce1a3084f772bf6f2650e37082a774e3cc7",
    "tanzil-en.sahih.txt": "a1778a1a56695d9b59ae910809ec46d9f4a55f05961de51cd56e6ebcf9040883",
    "tanzil-quran-uthmani.txt": "bf4f57b968d03f4131c070b1e285da9be0e0a108a21c910e872801ca273312c8"
  },
  "ring_metrics": {
    "all_inclusio": [
      769,
      5204
    ],
    "all_middle": [
      698,
      5004
    ],
    "all_mirror": [
      1642,
      40725
    ],
    "all_shift": [
      1642,
      40689
    ],
    "all_strip10_inclusio": [
      559,
      4728
    ],
    "all_strip10_middle": [
      490,
      4564
    ],
    "delta_nulls": {
      "all": {
        "ge_count": 30,
        "q025": [
          -86421,
          7370741
        ],
        "q975": [
          3023,
          234270
        ]
      },
      "all_strip10": {
        "ge_count": 11,
        "q025": [
          -30371,
          3018863
        ],
        "q975": [
          138570,
          11982959
        ]
      },
      "even": {
        "ge_count": 48,
        "q025": [
          -66764,
          3873471
        ],
        "q975": [
          140725,
          8023014
        ]
      },
      "even_strip10": {
        "ge_count": 64,
        "q025": [
          -106267,
          6428704
        ],
        "q975": [
          125429,
          6887350
        ]
      },
      "kalila_arb": {
        "ge_count": 161,
        "q025": [
          -271,
          29151
        ],
        "q975": [
          63884,
          7175217
        ]
      },
      "kalila_nat": {
        "ge_count": 19,
        "q025": [
          -127163,
          12217556
        ],
        "q975": [
          158809,
          11978268
        ]
      },
      "odd": {
        "ge_count": 50,
        "q025": [
          -5639,
          364344
        ],
        "q975": [
          3803,
          185288
        ]
      },
      "odd_strip10": {
        "ge_count": 6,
        "q025": [
          -18517,
          917626
        ],
        "q975": [
          40684,
          2793045
        ]
      }
    },
    "even_inclusio": [
      397,
      2719
    ],
    "even_middle": [
      359,
      2586
    ],
    "even_strip10_inclusio": [
      281,
      2475
    ],
    "even_strip10_middle": [
      250,
      2356
    ],
    "kalila_arb_inclusio": [
      570,
      6419
    ],
    "kalila_arb_middle": [
      584,
      6425
    ],
    "kalila_nat_inclusio": [
      632,
      4599
    ],
    "kalila_nat_middle": [
      607,
      4754
    ],
    "mirror_ge_count": 246,
    "mirror_le_count": 4,
    "mirror_null_pooled": [
      428283,
      10166734
    ],
    "odd_inclusio": [
      372,
      2485
    ],
    "odd_middle": [
      339,
      2418
    ],
    "odd_strip10_inclusio": [
      278,
      2253
    ],
    "odd_strip10_middle": [
      240,
      2208
    ]
  },
  "root_records": [
    {
      "occurrences": 1,
      "pickthall_lost_pairs": 0,
      "pickthall_top_count": 1,
      "pickthall_total_pairs": 0,
      "root": "ftq",
      "sahih_lost_pairs": 0,
      "sahih_top_count": 1,
      "sahih_total_pairs": 0,
      "unique_lemmas": 1,
      "verse_count": 1
    },
    {
      "occurrences": 1,
      "pickthall_lost_pairs": 0,
      "pickthall_top_count": 1,
      "pickthall_total_pairs": 0,
      "root": "rtq",
      "sahih_lost_pairs": 0,
      "sahih_top_count": 1,
      "sahih_total_pairs": 0,
      "unique_lemmas": 1,
      "verse_count": 1
    },
    {
      "occurrences": 92,
      "pickthall_lost_pairs": 2498,
      "pickthall_top_count": 28,
      "pickthall_total_pairs": 3741,
      "root": "sbH",
      "sahih_lost_pairs": 357,
      "sahih_top_count": 82,
      "sahih_total_pairs": 3741,
      "unique_lemmas": 7,
      "verse_count": 87
    },
    {
      "occurrences": 32,
      "pickthall_lost_pairs": 336,
      "pickthall_top_count": 7,
      "pickthall_total_pairs": 406,
      "root": "mdd",
      "sahih_lost_pairs": 304,
      "sahih_top_count": 11,
      "sahih_total_pairs": 406,
      "unique_lemmas": 9,
      "verse_count": 29
    },
    {
      "occurrences": 32,
      "pickthall_lost_pairs": 258,
      "pickthall_top_count": 8,
      "pickthall_total_pairs": 406,
      "root": "wsE",
      "sahih_lost_pairs": 218,
      "sahih_top_count": 12,
      "sahih_total_pairs": 406,
      "unique_lemmas": 6,
      "verse_count": 29
    },
    {
      "occurrences": 25,
      "pickthall_lost_pairs": 42,
      "pickthall_top_count": 23,
      "pickthall_total_pairs": 300,
      "root": "flk",
      "sahih_lost_pairs": 39,
      "sahih_top_count": 23,
      "sahih_total_pairs": 300,
      "unique_lemmas": 2,
      "verse_count": 25
    },
    {
      "occurrences": 3,
      "pickthall_lost_pairs": 1,
      "pickthall_top_count": 1,
      "pickthall_total_pairs": 1,
      "root": "kwr",
      "sahih_lost_pairs": 0,
      "sahih_top_count": 2,
      "sahih_total_pairs": 1,
      "unique_lemmas": 1,
      "verse_count": 2
    },
    {
      "occurrences": 132,
      "pickthall_lost_pairs": 4939,
      "pickthall_top_count": 49,
      "pickthall_total_pairs": 7260,
      "root": "qdr",
      "sahih_lost_pairs": 4792,
      "sahih_top_count": 46,
      "sahih_total_pairs": 7260,
      "unique_lemmas": 11,
      "verse_count": 121
    },
    {
      "occurrences": 81,
      "pickthall_lost_pairs": 1591,
      "pickthall_top_count": 29,
      "pickthall_total_pairs": 2556,
      "root": "zwj",
      "sahih_lost_pairs": 1758,
      "sahih_top_count": 22,
      "sahih_total_pairs": 2556,
      "unique_lemmas": 2,
      "verse_count": 72
    }
  ],
  "total_root_tokens": 49968,
  "unique_lemmas": 4657,
  "unique_root_wazn_cells": 3923,
  "unique_roots": 1642,
  "verb_form_counts": {
    "I": 12347,
    "II": 1300,
    "III": 334,
    "IV": 3487,
    "IX": 5,
    "V": 414,
    "VI": 77,
    "VII": 51,
    "VIII": 963,
    "X": 369,
    "XII": 9
  },
  "window_metrics": {
    "10": {
      "even_split_root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          485191,
          12236181
        ],
        "obs": [
          3159,
          44852
        ]
      },
      "odd_split_root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          436221,
          10839541
        ],
        "obs": [
          2801,
          39772
        ]
      },
      "rasm": {
        "ge_count": 0,
        "null_pooled": [
          679579,
          37556903
        ],
        "obs": [
          4968,
          146340
        ]
      },
      "raw": {
        "ge_count": 0,
        "null_pooled": [
          313169,
          38327853
        ],
        "obs": [
          3075,
          149959
        ]
      },
      "root": {
        "ge_count": 0,
        "null_pooled": [
          869364,
          23169133
        ],
        "obs": [
          5961,
          84662
        ]
      },
      "root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          913277,
          23079338
        ],
        "obs": [
          5961,
          84662
        ]
      },
      "stem": {
        "ge_count": 0,
        "null_pooled": [
          866971,
          37181030
        ],
        "obs": [
          6342,
          143242
        ]
      }
    },
    "20": {
      "even_split_root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          724147,
          11508861
        ],
        "obs": [
          3892,
          40914
        ]
      },
      "odd_split_root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          654577,
          10179476
        ],
        "obs": [
          3354,
          36390
        ]
      },
      "rasm": {
        "ge_count": 0,
        "null_pooled": [
          1131561,
          36420990
        ],
        "obs": [
          7253,
          139141
        ]
      },
      "raw": {
        "ge_count": 0,
        "null_pooled": [
          582523,
          37740278
        ],
        "obs": [
          4723,
          145316
        ]
      },
      "root": {
        "ge_count": 0,
        "null_pooled": [
          1373771,
          21791348
        ],
        "obs": [
          7283,
          77384
        ]
      },
      "root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          1376797,
          21701539
        ],
        "obs": [
          7283,
          77384
        ]
      },
      "stem": {
        "ge_count": 0,
        "null_pooled": [
          1443498,
          35731606
        ],
        "obs": [
          8954,
          134393
        ]
      }
    },
    "40": {
      "even_split_root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          1000638,
          10500651
        ],
        "obs": [
          4319,
          36542
        ]
      },
      "odd_split_root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          905626,
          9265193
        ],
        "obs": [
          3792,
          32573
        ]
      },
      "rasm": {
        "ge_count": 0,
        "null_pooled": [
          1669728,
          34742910
        ],
        "obs": [
          9054,
          130114
        ]
      },
      "raw": {
        "ge_count": 0,
        "null_pooled": [
          1023812,
          36705935
        ],
        "obs": [
          6396,
          138905
        ]
      },
      "root": {
        "ge_count": 0,
        "null_pooled": [
          1940392,
          19842861
        ],
        "obs": [
          8300,
          69156
        ]
      },
      "root_t4b": {
        "ge_count": 0,
        "null_pooled": [
          1900871,
          19790805
        ],
        "obs": [
          8300,
          69156
        ]
      },
      "stem": {
        "ge_count": 0,
        "null_pooled": [
          2126089,
          33595990
        ],
        "obs": [
          10868,
          123506
        ]
      }
    }
  }
}
def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verify_corpus_hashes(corpus_dir, expected_hashes=None):
    pins = EXPECTED_CORPUS_SHA256 if expected_hashes is None else expected_hashes
    verified = {}
    for rel_path, expected in sorted(pins.items()):
        full_path = os.path.join(corpus_dir, rel_path)
        if not os.path.isfile(full_path):
            raise ArabicOracleError("CORPUS_MISSING", f"missing corpus file {rel_path}")
        actual = sha256_file(full_path)
        if actual != expected:
            raise ArabicOracleError("SHA256_MISMATCH", f"hash mismatch for {rel_path}")
        verified[rel_path] = actual
    return verified


def parse_tanzil_lines(lines):
    verses = {}
    for raw in lines:
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split("|", 2)
        if len(parts) != 3:
            raise ArabicOracleError("PARSE_ERROR", "malformed tanzil verse line")
        verses[(int(parts[0]), int(parts[1]))] = parts[2]
    return verses


def parse_openiti_lines(lines):
    in_body = False
    sections = []
    current = []
    all_lines = []
    for raw in lines:
        line = raw.strip()
        if not in_body:
            if line.startswith("#META#Header#End#"):
                in_body = True
            continue
        if not line:
            continue
        if line.startswith("###"):
            if current:
                sections.append(current)
                current = []
            continue
        cleaned = OPENITI_NOISE_RE.sub(" ", line)
        stems = [light_stem_ar(t) for t in cleaned.split() if to_rasm(t)]
        if stems:
            current.append(stems)
            all_lines.append(stems)
    if current:
        sections.append(current)
    return all_lines, sections


def parse_leeds_morphology_lines(lines):
    roots_set = set()
    root_lems = set()
    root_wazn_cells = set()
    vf_counts = Counter()
    root_freq = Counter()
    surah_verses = defaultdict(lambda: defaultdict(list))
    leeds_roots = []
    leeds_pos = []
    leeds_odd = []
    leeds_odd_pos = []
    leeds_even = []
    leeds_even_pos = []
    target_verses = {r: set() for r in TARGET_ROOTS}
    target_occs = Counter()
    target_lems = {r: set() for r in TARGET_ROOTS}

    for raw in lines:
        if not raw or raw.startswith("#") or raw.startswith("LOCATION"):
            continue
        parts = raw.rstrip("\r\n").split("\t")
        if len(parts) < 4:
            continue
        loc, _, tag, feat = parts[0], parts[1], parts[2], parts[3]
        rm = ROOT_RE.search(feat)
        if not rm:
            continue
        root = rm.group(1)
        lm = LEM_RE.search(feat)
        lem = lm.group(1) if lm else ""
        loc_parts = loc.strip("()").split(":")
        surah_num = int(loc_parts[0])
        verse_num = int(loc_parts[1])

        roots_set.add(root)
        if lem:
            root_lems.add((root, lem))
        root_freq[root] += 1

        vm = VF_RE.search(feat)
        vf = vm.group(1) if vm else ("I" if tag == "V" else "BASE")
        if tag == "V":
            vf_counts[vf] += 1

        toks = feat.split("|")
        if "ACT" in toks and "PCPL" in toks:
            dtag = "ACT_PCPL"
        elif "PASS" in toks and "PCPL" in toks:
            dtag = "PASS_PCPL"
        elif "VN" in toks:
            dtag = "VN"
        else:
            dtag = "BASE"
        root_wazn_cells.add((root, f"{tag}:{vf}:{dtag}"))

        leeds_roots.append(root)
        leeds_pos.append(tag)
        surah_verses[surah_num][verse_num].append(root)
        if surah_num % 2 == 1:
            leeds_odd.append(root)
            leeds_odd_pos.append(tag)
        else:
            leeds_even.append(root)
            leeds_even_pos.append(tag)

        if root in target_verses:
            target_verses[root].add((surah_num, verse_num))
            target_occs[root] += 1
            if lem:
                target_lems[root].add(lem)

    return {
        "unique_roots": len(roots_set),
        "unique_lemmas": len(root_lems),
        "unique_root_wazn_cells": len(root_wazn_cells),
        "total_root_tokens": len(leeds_roots),
        "verb_form_counts": dict(sorted(vf_counts.items())),
        "top10_roots": frozenset(r for r, _ in root_freq.most_common(10)),
        "surah_verses": surah_verses,
        "leeds_roots": leeds_roots,
        "leeds_pos": leeds_pos,
        "leeds_odd": leeds_odd,
        "leeds_odd_pos": leeds_odd_pos,
        "leeds_even": leeds_even,
        "leeds_even_pos": leeds_even_pos,
        "target_verses": target_verses,
        "target_occs": target_occs,
        "target_lems": target_lems,
    }


def _encode_ids(seq):
    mp = {}
    out = []
    for item in seq:
        idx = mp.get(item)
        if idx is None:
            idx = len(mp)
            mp[item] = idx
        out.append(idx)
    return out


def multishuffle_layer_cohesion(seq, window_sizes, n_shuffles, base_seed, classes=None):
    """Exact pure-integer B-shuffle cohesion summary across all requested window sizes."""
    ids = _encode_ids(seq)
    obs = {w: block_jaccard_cohesion_exact(ids, w)[:2] for w in window_sizes}
    null_i = {w: 0 for w in window_sizes}
    null_u = {w: 0 for w in window_sizes}
    ge = {w: 0 for w in window_sizes}
    for b in range(n_shuffles):
        if classes is None:
            sh = det_shuffle_exact(ids, base_seed + b)
        else:
            sh = stratified_shuffle_exact(ids, classes, base_seed + b)
        for w in window_sizes:
            ni, nu = block_jaccard_cohesion_exact(sh, w)[:2]
            null_i[w] += ni
            null_u[w] += nu
            oi, ou = obs[w]
            if ni * ou >= oi * nu:
                ge[w] += 1
    return {
        w: {
            "obs": [obs[w][0], obs[w][1]],
            "null_pooled": [null_i[w], null_u[w]],
            "ge_count": ge[w],
        }
        for w in window_sizes
    }


def evaluate_ring_and_inclusio_multishuffle(units, n_shuffles, exclude=frozenset(), base_seed=SEED_RING_PERM):
    """Exact pure-Q observed & B-shuffle verse-permutation null for mirror & inclusio."""
    prepared = []
    for unit in units:
        if len(unit) < 20:
            continue
        prepared.append([frozenset(x for x in verse if x not in exclude) for verse in unit])

    def _measure(unit_list):
        mi = mu = si = su = ii = iu = mdi = mdu = 0
        for sets in unit_list:
            length = len(sets)
            half = length // 2
            for i in range(half):
                a = sets[i]
                b = sets[length - 1 - i]
                mi += len(a & b)
                mu += len(a | b)
                c = sets[half + i]
                si += len(a & c)
                su += len(a | c)
            k = length // 10
            fs = set().union(*sets[:k])
            ls = set().union(*sets[length - k:])
            ms_start = (length - k) // 2
            ms = set().union(*sets[ms_start:ms_start + k])
            ii += len(fs & ls)
            iu += len(fs | ls)
            mdi += len(fs & ms)
            mdu += len(fs | ms)
        return (mi, mu), (si, su), (ii, iu), (mdi, mdu)

    mir_o, shf_o, inc_o, mid_o = _measure(prepared)
    mir_r = Fraction(mir_o[0], mir_o[1])
    delta_o = Fraction(inc_o[0], inc_o[1]) - Fraction(mid_o[0], mid_o[1])

    mir_null_i = mir_null_u = 0
    mir_ge = mir_le = 0
    delta_ge = 0
    delta_nulls = []
    for b in range(n_shuffles):
        perm_units = [
            det_shuffle_exact(sets, base_seed + b * 1009 + idx * 97)
            for idx, sets in enumerate(prepared)
        ]
        mn, _, in_p, md_p = _measure(perm_units)
        mir_null_i += mn[0]
        mir_null_u += mn[1]
        mn_r = Fraction(mn[0], mn[1])
        if mn_r >= mir_r:
            mir_ge += 1
        if mn_r <= mir_r:
            mir_le += 1
        dn = Fraction(in_p[0], in_p[1]) - Fraction(md_p[0], md_p[1])
        delta_nulls.append(dn)
        if dn >= delta_o:
            delta_ge += 1

    delta_sorted = sorted(delta_nulls)
    q025_idx = (n_shuffles * 25) // 1000
    q975_idx = min(n_shuffles - 1, (n_shuffles * 975) // 1000)
    q025 = delta_sorted[q025_idx]
    q975 = delta_sorted[q975_idx]

    return {
        "mirror": [mir_o[0], mir_o[1]],
        "shift": [shf_o[0], shf_o[1]],
        "mirror_null_pooled": [mir_null_i, mir_null_u],
        "mirror_ge_count": mir_ge,
        "mirror_le_count": mir_le,
        "inclusio": [inc_o[0], inc_o[1]],
        "middle": [mid_o[0], mid_o[1]],
        "delta_null": {
            "ge_count": delta_ge,
            "q025": [q025.numerator, q025.denominator],
            "q975": [q975.numerator, q975.denominator],
        },
    }


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def compute_live_measurements(
    corpus_dir,
    expected_hashes=None,
    window_sizes=WINDOW_SIZES,
    bg_pair_count=BG_PAIR_COUNT,
    arb_chunk_lines=ARB_CHUNK_LINES,
    n_shuffles=MIN_MULTISHUFFLE_B,
):
    verified_hashes = verify_corpus_hashes(corpus_dir, expected_hashes=expected_hashes)

    morph_data = parse_leeds_morphology_lines(
        _read_lines(os.path.join(corpus_dir, "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt"))
    )
    uthmani = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-quran-uthmani.txt")))
    sahih = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-en.sahih.txt")))
    pick = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-en.pickthall.txt")))

    uth_raw = []
    uth_rasm = []
    uth_stem = []
    for key in sorted(uthmani.keys()):
        for tok in uthmani[key].split():
            rasm = to_rasm(tok)
            if not rasm:
                continue
            uth_raw.append(tok)
            uth_rasm.append(rasm)
            uth_stem.append(light_stem_ar(tok))

    ms_raw = multishuffle_layer_cohesion(uth_raw, window_sizes, n_shuffles, SEED_LAYER_RAW)
    ms_rasm = multishuffle_layer_cohesion(uth_rasm, window_sizes, n_shuffles, SEED_LAYER_RASM)
    ms_stem = multishuffle_layer_cohesion(uth_stem, window_sizes, n_shuffles, SEED_LAYER_STEM)
    ms_root = multishuffle_layer_cohesion(morph_data["leeds_roots"], window_sizes, n_shuffles, SEED_LAYER_ROOT)
    ms_root_t4b = multishuffle_layer_cohesion(
        morph_data["leeds_roots"], window_sizes, n_shuffles, SEED_ROOT_T4B, classes=morph_data["leeds_pos"]
    )
    ms_odd_t4b = multishuffle_layer_cohesion(
        morph_data["leeds_odd"], window_sizes, n_shuffles, SEED_ODD_T4B, classes=morph_data["leeds_odd_pos"]
    )
    ms_even_t4b = multishuffle_layer_cohesion(
        morph_data["leeds_even"], window_sizes, n_shuffles, SEED_EVEN_T4B, classes=morph_data["leeds_even_pos"]
    )

    window_metrics = {}
    for w in window_sizes:
        window_metrics[w] = {
            "raw": ms_raw[w],
            "rasm": ms_rasm[w],
            "stem": ms_stem[w],
            "root": ms_root[w],
            "root_t4b": ms_root_t4b[w],
            "odd_split_root_t4b": ms_odd_t4b[w],
            "even_split_root_t4b": ms_even_t4b[w],
        }

    kalila_lines, kalila_secs = parse_openiti_lines(
        _read_lines(os.path.join(corpus_dir, "openiti_controls/ibn_muqaffa_kalila.txt"))
    )
    adab_lines, _ = parse_openiti_lines(
        _read_lines(os.path.join(corpus_dir, "openiti_controls/ibn_muqaffa_adab_kabir.txt"))
    )
    imru_lines, _ = parse_openiti_lines(
        _read_lines(os.path.join(corpus_dir, "openiti_controls/imru_al_qays_diwan.txt"))
    )
    tarafa_lines, _ = parse_openiti_lines(
        _read_lines(os.path.join(corpus_dir, "openiti_controls/tarafa_diwan.txt"))
    )
    antara_lines, _ = parse_openiti_lines(
        _read_lines(os.path.join(corpus_dir, "openiti_controls/antara_muallaqa.txt"))
    )

    kalila_flat = [t for ln in kalila_lines for t in ln]
    adab_flat = [t for ln in adab_lines for t in ln]
    poetry_flat = [t for ln in (imru_lines + tarafa_lines + antara_lines) for t in ln]

    ctrl_w = window_sizes[1] if len(window_sizes) > 1 else window_sizes[0]
    control_w20_metrics = {
        "quran_stem": ms_stem[ctrl_w],
        "kalila_prose": multishuffle_layer_cohesion(kalila_flat, (ctrl_w,), n_shuffles, SEED_CTRL_KALILA)[ctrl_w],
        "adab_prose": multishuffle_layer_cohesion(adab_flat, (ctrl_w,), n_shuffles, SEED_CTRL_ADAB)[ctrl_w],
        "poetry_pooled": multishuffle_layer_cohesion(poetry_flat, (ctrl_w,), n_shuffles, SEED_CTRL_POETRY)[ctrl_w],
    }

    all_units = []
    odd_units = []
    even_units = []
    for s_num in sorted(morph_data["surah_verses"].keys()):
        vs = [morph_data["surah_verses"][s_num][v] for v in sorted(morph_data["surah_verses"][s_num].keys())]
        if len(vs) >= 20:
            all_units.append(vs)
            if s_num % 2 == 1:
                odd_units.append(vs)
            else:
                even_units.append(vs)

    top10 = morph_data["top10_roots"]
    ri_all = evaluate_ring_and_inclusio_multishuffle(all_units, n_shuffles, base_seed=SEED_RING_PERM)
    ri_odd = evaluate_ring_and_inclusio_multishuffle(odd_units, n_shuffles, base_seed=SEED_RING_PERM + 100000)
    ri_even = evaluate_ring_and_inclusio_multishuffle(even_units, n_shuffles, base_seed=SEED_RING_PERM + 200000)
    ri_all_s10 = evaluate_ring_and_inclusio_multishuffle(all_units, n_shuffles, exclude=top10, base_seed=SEED_RING_PERM + 300000)
    ri_odd_s10 = evaluate_ring_and_inclusio_multishuffle(odd_units, n_shuffles, exclude=top10, base_seed=SEED_RING_PERM + 400000)
    ri_even_s10 = evaluate_ring_and_inclusio_multishuffle(even_units, n_shuffles, exclude=top10, base_seed=SEED_RING_PERM + 500000)

    kalila_arb = [
        kalila_lines[i:i + arb_chunk_lines]
        for i in range(0, len(kalila_lines) - arb_chunk_lines + 1, arb_chunk_lines)
    ]
    kalila_nat = [sec for sec in kalila_secs if len(sec) >= 20]
    ri_kalila_arb = evaluate_ring_and_inclusio_multishuffle(kalila_arb, n_shuffles, base_seed=SEED_RING_PERM + 600000)
    ri_kalila_nat = evaluate_ring_and_inclusio_multishuffle(kalila_nat, n_shuffles, base_seed=SEED_RING_PERM + 700000)

    ring_metrics = {
        "all_mirror": ri_all["mirror"],
        "all_shift": ri_all["shift"],
        "mirror_null_pooled": ri_all["mirror_null_pooled"],
        "mirror_ge_count": ri_all["mirror_ge_count"],
        "mirror_le_count": ri_all["mirror_le_count"],
        "all_inclusio": ri_all["inclusio"],
        "all_middle": ri_all["middle"],
        "odd_inclusio": ri_odd["inclusio"],
        "odd_middle": ri_odd["middle"],
        "even_inclusio": ri_even["inclusio"],
        "even_middle": ri_even["middle"],
        "all_strip10_inclusio": ri_all_s10["inclusio"],
        "all_strip10_middle": ri_all_s10["middle"],
        "odd_strip10_inclusio": ri_odd_s10["inclusio"],
        "odd_strip10_middle": ri_odd_s10["middle"],
        "even_strip10_inclusio": ri_even_s10["inclusio"],
        "even_strip10_middle": ri_even_s10["middle"],
        "kalila_arb_inclusio": ri_kalila_arb["inclusio"],
        "kalila_arb_middle": ri_kalila_arb["middle"],
        "kalila_nat_inclusio": ri_kalila_nat["inclusio"],
        "kalila_nat_middle": ri_kalila_nat["middle"],
        "delta_nulls": {
            "all": ri_all["delta_null"],
            "odd": ri_odd["delta_null"],
            "even": ri_even["delta_null"],
            "all_strip10": ri_all_s10["delta_null"],
            "odd_strip10": ri_odd_s10["delta_null"],
            "even_strip10": ri_even_s10["delta_null"],
            "kalila_arb": ri_kalila_arb["delta_null"],
            "kalila_nat": ri_kalila_nat["delta_null"],
        },
    }

    sahih_stems = {k: en_content_stems(v) for k, v in sahih.items()}
    pick_stems = {k: en_content_stems(v) for k, v in pick.items()}
    shuf_keys = det_shuffle_exact(sorted(sahih.keys()), SEED_BG_PAIRS)
    bg_s_lost = 0
    bg_p_lost = 0
    for i in range(bg_pair_count):
        k1 = shuf_keys[2 * i]
        k2 = shuf_keys[2 * i + 1]
        if not (sahih_stems[k1] & sahih_stems[k2]):
            bg_s_lost += 1
        if not (pick_stems[k1] & pick_stems[k2]):
            bg_p_lost += 1

    root_records = []
    for root in TARGET_ROOTS:
        vs = sorted(morph_data["target_verses"][root])
        n = len(vs)
        tot_p = n * (n - 1) // 2
        s_df = Counter()
        p_df = Counter()
        for k in vs:
            for st in sahih_stems[k]:
                s_df[st] += 1
            for st in pick_stems[k]:
                p_df[st] += 1
        s_top = s_df.most_common(1)[0][1] if s_df else 0
        p_top = p_df.most_common(1)[0][1] if p_df else 0
        s_lost = 0
        p_lost = 0
        for i in range(n):
            for j in range(i + 1, n):
                if not (sahih_stems[vs[i]] & sahih_stems[vs[j]]):
                    s_lost += 1
                if not (pick_stems[vs[i]] & pick_stems[vs[j]]):
                    p_lost += 1
        root_records.append({
            "root": root,
            "occurrences": morph_data["target_occs"][root],
            "verse_count": n,
            "unique_lemmas": len(morph_data["target_lems"][root]),
            "sahih_top_count": s_top,
            "pickthall_top_count": p_top,
            "sahih_lost_pairs": s_lost,
            "pickthall_lost_pairs": p_lost,
            "sahih_total_pairs": tot_p,
            "pickthall_total_pairs": tot_p,
        })

    return {
        "n_shuffles": n_shuffles,
        "pinned_sha256s": verified_hashes,
        "unique_roots": morph_data["unique_roots"],
        "unique_lemmas": morph_data["unique_lemmas"],
        "unique_root_wazn_cells": morph_data["unique_root_wazn_cells"],
        "total_root_tokens": morph_data["total_root_tokens"],
        "verb_form_counts": morph_data["verb_form_counts"],
        "window_metrics": window_metrics,
        "control_w20_metrics": control_w20_metrics,
        "ring_metrics": ring_metrics,
        "root_records": root_records,
        "bg_sahih_pair": [bg_s_lost, bg_pair_count],
        "bg_pickthall_pair": [bg_p_lost, bg_pair_count],
    }


def certify_from_measurements(mode, live_corpus_recounted, measurements):
    n_shuf = measurements["n_shuffles"]
    p1 = audit_root_pattern_lattice_and_cohesion_exact(
        unique_roots=measurements["unique_roots"],
        unique_lemmas=measurements["unique_lemmas"],
        unique_root_wazn_cells=measurements["unique_root_wazn_cells"],
        total_root_tokens=measurements["total_root_tokens"],
        verb_form_counts=measurements["verb_form_counts"],
        window_metrics=measurements["window_metrics"],
        control_w20_metrics=measurements["control_w20_metrics"],
        n_shuffles=n_shuf,
    )
    p2 = audit_ring_vs_inclusio_multishuffle_exact(
        measurements["ring_metrics"],
        n_shuffles=n_shuf,
    )
    p3 = audit_translation_remainder_exact(
        root_records=measurements["root_records"],
        bg_sahih_pair=measurements["bg_sahih_pair"],
        bg_pickthall_pair=measurements["bg_pickthall_pair"],
    )
    five_axes = {
        "per_layer_null_normalized_lift": p1["lift_reverses_absolute_ladder"] and p1["lattice_nontrivial"],
        "window_size_10_20_40_holm": p1["all_12_cells_beat_null_holm"] and p1["root_beats_t4b_all_w"],
        "split_half_internal_consistency": p1["split_halves_beat_t4b_all_w"],
        "honest_boundary_inclusio_adjudication": p2["passed"],
        "second_instrument_and_controls": (
            p1["shared_classical_prose_property"]
            and p1["prose_exceeds_poetry_baseline"]
            and p2["arbitrary_prose_reverses_to_decay"]
            and p3["passed"]
        ),
    }
    return certify_arabic_own_terms_5axis_gate(
        mode=mode,
        live_corpus_recounted=live_corpus_recounted,
        pinned_sha256s=measurements["pinned_sha256s"],
        feature_names=AUDIT_FEATURES,
        pillar1_result=p1,
        pillar2_result=p2,
        pillar3_result=p3,
        five_axis_checks=five_axes,
    )


def default_corpus_dir():
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "corpora"))


def run_audit(live=False, corpus_dir=None):
    if not live and corpus_dir is None:
        return certify_from_measurements("standalone_fixture_replay", False, STANDALONE_FIXTURE)
    target_dir = default_corpus_dir() if corpus_dir is None else corpus_dir
    measurements = compute_live_measurements(target_dir)
    return certify_from_measurements("live_corpus_recount", True, measurements)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Classical Arabic continuum audit (v2)")
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Offline pinned-fixture replay (default when --live/--corpus-dir not passed)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Recompute all counts & B=250 nulls from downloaded corpora (default: ../corpora)",
    )
    parser.add_argument(
        "--corpus-dir",
        default=None,
        help="Path to primary corpora directory (implies live recount)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write canonical JSON certificate",
    )
    args = parser.parse_args(argv)

    use_live = args.live or (args.corpus_dir is not None)
    cert = run_audit(live=use_live, corpus_dir=args.corpus_dir)
    raw_bytes = canonical_json_bytes(cert)
    if args.output:
        with open(args.output, "wb") as f:
            f.write(raw_bytes)
            f.write(b"\n")
    sys.stdout.write(raw_bytes.decode("utf-8") + "\n")
    return 0 if cert["all_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
