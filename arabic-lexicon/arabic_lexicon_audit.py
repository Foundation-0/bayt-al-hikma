"""Dual-mode (live_corpus_recount + standalone_fixture_replay) audit runner (v2)
for Classical Arabic Lexical Semantic-Field Topology & Multi-Translator Continuum
Projection Defect.

Modes:
- Default / --standalone: offline threshold & invariant replay on pinned counts
  (mode='standalone_fixture_replay', live_corpus_recounted=False; reads no text).
- --live or --corpus-dir <path>: SHA-256 verifies all 9 primary corpora on disk
  (downloadable via ../fetch_corpora.py --dest ./corpora) and recomputes every
  count, every B=250 multi-shuffle null, and every 4-stratum distance control
  directly from the raw primary texts (mode='live_corpus_recount',
  live_corpus_recounted=True).

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

from arabic_lexicon_oracle import (
    LexiconOracleError,
    MIN_MULTISHUFFLE_B,
    audit_context_neighborhood_topology_exact,
    audit_two_layer_projection_defect_exact,
    audit_wazn_agency_matrix_and_renyi2_exact,
    block_renyi2_cross_pair,
    canonical_json_bytes,
    certify_arabic_lexicon_own_terms_gate,
    det_shuffle_exact,
    en_content_stems,
    light_stem_ar,
    renyi2_concentration_pair,
    stratified_shuffle_exact,
    to_rasm,
)


TARGET_ROOTS = (
    "ftq", "rtq", "sbH", "flk", "kwr", "wsE", "mdd", "qdr",
    "zwj", "Erj", "nzl", "xlq", "Amr", "Hqq", "wzn",
)

OP_CLASS_MAP = {
    "I": "GROUND_I",
    "II": "CAUS_INTENS_II_III_IV",
    "III": "CAUS_INTENS_II_III_IV",
    "IV": "CAUS_INTENS_II_III_IV",
    "V": "REFL_RECIP_V_VI_VII_VIII",
    "VI": "REFL_RECIP_V_VI_VII_VIII",
    "VII": "REFL_RECIP_V_VI_VII_VIII",
    "VIII": "REFL_RECIP_V_VI_VII_VIII",
    "IX": "STAT_ESTIM_IX_X",
    "X": "STAT_ESTIM_IX_X",
}

TRANSITION_PAIRS = (
    ("I", "IV"),
    ("I", "II"),
    ("II", "V"),
    ("III", "VI"),
    ("I", "VIII"),
    ("I", "X"),
    ("IV", "X"),
)

AUDIT_FEATURES = (
    "single_corpus_root_wazn_forms_i_to_x_descriptive_matrix",
    "multishuffle_b250_renyi2_collision_tier4a_tier4b",
    "openiti_classical_prose_and_poetry_renyi2_controls",
    "arabic_top10_stripped_context_topology_b250_holm",
    "split_half_internal_consistency_odd_even",
    "two_instrument_lemma_shuffle_and_distance_strata_control",
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

SEED_WAZN_T4A = 20261100
SEED_WAZN_T4B = 20261500
SEED_WAZN_ODD_T4B = 20262000
SEED_WAZN_EVEN_T4B = 20262500
SEED_CTRL_R2_T4A = 20263000
SEED_CTX_NULL = 20264000
SEED_LEMMA_SHUFFLE = 20265000
SEED_BG_PAIRS = 2026097
BG_PAIR_COUNT = 1000
CTRL_WINDOW = 20

STANDALONE_FIXTURE = {
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
    "total_unique_roots": 1642,
    "verb_roots": 942,
    "poly_wazn_roots": 349,
    "verb_tokens_i_x": 19347,
    "form_xii_tokens": 9,
    "op_class_counts": {
        "GROUND_I": 12347,
        "STAT_ESTIM_IX_X": 374,
        "CAUS_INTENS_II_III_IV": 5121,
        "REFL_RECIP_V_VI_VII_VIII": 1505
    },
    "transition_pair_counts": {
        "I+IV": 146,
        "I+II": 87,
        "II+V": 40,
        "III+VI": 12,
        "I+VIII": 67,
        "I+X": 42,
        "IV+X": 41
    },
    "within_root_renyi2_pairs": {
        "all_obs": [
            6190677,
            6678331
        ],
        "all_t4a": [
            749702990,
            1669582750
        ],
        "all_t4b": [
            850295678,
            1669582750
        ],
        "odd_obs": [
            1373154,
            1474950
        ],
        "odd_t4b": [
            201805070,
            368737500
        ],
        "even_obs": [
            1747029,
            1891145
        ],
        "even_t4b": [
            255249980,
            472786250
        ]
    },
    "within_root_ge_counts": {
        "all_t4a": 0,
        "all_t4b": 0,
        "odd_t4b": 0,
        "even_t4b": 0
    },
    "control_renyi2_metrics": {
        "quran_stem": {
            "global_c2": [
                32595109,
                6065450161
            ],
            "w20_obs": [
                14108,
                1557200
            ],
            "w20_t4a_pooled": [
                2088401,
                389300000
            ],
            "w20_ge_count": 0
        },
        "kalila_prose": {
            "global_c2": [
                9431822,
                1943928100
            ],
            "w20_obs": [
                7708,
                881200
            ],
            "w20_t4a_pooled": [
                1062751,
                220300000
            ],
            "w20_ge_count": 0
        },
        "adab_prose": {
            "global_c2": [
                577088,
                91891396
            ],
            "w20_obs": [
                1888,
                191200
            ],
            "w20_t4a_pooled": [
                295410,
                47800000
            ],
            "w20_ge_count": 0
        },
        "poetry_pooled": {
            "global_c2": [
                219899,
                105042001
            ],
            "w20_obs": [
                658,
                204400
            ],
            "w20_t4a_pooled": [
                102012,
                51100000
            ],
            "w20_ge_count": 0
        }
    },
    "context_metrics": {
        "ctx_r2_all": [
            101506,
            14920444
        ],
        "ctx_r2_null_pooled": [
            14775289,
            3442174339
        ],
        "ctx_r2_odd": [
            25931,
            3454687
        ],
        "ctx_r2_odd_null_pooled": [
            3659861,
            715181957
        ],
        "ctx_r2_even": [
            29831,
            4085025
        ],
        "ctx_r2_even_null_pooled": [
            5014148,
            1032532578
        ],
        "ctx_jaccard_all": [
            17298,
            94759
        ],
        "ctx_jaccard_null_pooled": [
            4914194,
            22154001
        ],
        "ctx_jaccard_odd": [
            7251,
            46429
        ],
        "ctx_jaccard_odd_null_pooled": [
            1859967,
            10436306
        ],
        "ctx_jaccard_even": [
            8124,
            50253
        ],
        "ctx_jaccard_even_null_pooled": [
            2344216,
            12427706
        ],
        "cooccur_all": [
            173,
            1161
        ],
        "cooccur_null_pooled": [
            33791,
            296522
        ],
        "cooccur_odd": [
            85,
            562
        ],
        "cooccur_odd_null_pooled": [
            15422,
            140882
        ],
        "cooccur_even": [
            88,
            599
        ],
        "cooccur_even_null_pooled": [
            18369,
            155640
        ],
        "extreme_counts": {
            "ctx_r2_all": 0,
            "ctx_r2_odd": 0,
            "ctx_r2_even": 0,
            "ctx_jaccard_all": 0,
            "ctx_jaccard_odd": 1,
            "ctx_jaccard_even": 0,
            "cooccur_all": 0,
            "cooccur_odd": 1,
            "cooccur_even": 1
        }
    },
    "root_records": [
        {
            "root": "ftq",
            "occurrences": 1,
            "verse_count": 1,
            "unique_lemmas": 1,
            "sahih_top_count": 1,
            "pickthall_top_count": 1,
            "same_lemma_pairs": 0,
            "cross_lemma_pairs": 0,
            "sahih_same_lost": 0,
            "sahih_cross_lost": 0,
            "pickthall_same_lost": 0,
            "pickthall_cross_lost": 0,
            "sahih_lost_pairs": 0,
            "pickthall_lost_pairs": 0
        },
        {
            "root": "rtq",
            "occurrences": 1,
            "verse_count": 1,
            "unique_lemmas": 1,
            "sahih_top_count": 1,
            "pickthall_top_count": 1,
            "same_lemma_pairs": 0,
            "cross_lemma_pairs": 0,
            "sahih_same_lost": 0,
            "sahih_cross_lost": 0,
            "pickthall_same_lost": 0,
            "pickthall_cross_lost": 0,
            "sahih_lost_pairs": 0,
            "pickthall_lost_pairs": 0
        },
        {
            "root": "sbH",
            "occurrences": 92,
            "verse_count": 87,
            "unique_lemmas": 7,
            "sahih_top_count": 82,
            "pickthall_top_count": 28,
            "same_lemma_pairs": 1603,
            "cross_lemma_pairs": 2138,
            "sahih_same_lost": 17,
            "sahih_cross_lost": 340,
            "pickthall_same_lost": 682,
            "pickthall_cross_lost": 1816,
            "sahih_lost_pairs": 357,
            "pickthall_lost_pairs": 2498
        },
        {
            "root": "flk",
            "occurrences": 25,
            "verse_count": 25,
            "unique_lemmas": 2,
            "sahih_top_count": 23,
            "pickthall_top_count": 23,
            "same_lemma_pairs": 254,
            "cross_lemma_pairs": 46,
            "sahih_same_lost": 0,
            "sahih_cross_lost": 39,
            "pickthall_same_lost": 0,
            "pickthall_cross_lost": 42,
            "sahih_lost_pairs": 39,
            "pickthall_lost_pairs": 42
        },
        {
            "root": "kwr",
            "occurrences": 3,
            "verse_count": 2,
            "unique_lemmas": 1,
            "sahih_top_count": 2,
            "pickthall_top_count": 1,
            "same_lemma_pairs": 1,
            "cross_lemma_pairs": 0,
            "sahih_same_lost": 0,
            "sahih_cross_lost": 0,
            "pickthall_same_lost": 1,
            "pickthall_cross_lost": 0,
            "sahih_lost_pairs": 0,
            "pickthall_lost_pairs": 1
        },
        {
            "root": "wsE",
            "occurrences": 32,
            "verse_count": 29,
            "unique_lemmas": 6,
            "sahih_top_count": 12,
            "pickthall_top_count": 8,
            "same_lemma_pairs": 77,
            "cross_lemma_pairs": 329,
            "sahih_same_lost": 13,
            "sahih_cross_lost": 205,
            "pickthall_same_lost": 19,
            "pickthall_cross_lost": 239,
            "sahih_lost_pairs": 218,
            "pickthall_lost_pairs": 258
        },
        {
            "root": "mdd",
            "occurrences": 32,
            "verse_count": 29,
            "unique_lemmas": 9,
            "sahih_top_count": 11,
            "pickthall_top_count": 7,
            "same_lemma_pairs": 124,
            "cross_lemma_pairs": 282,
            "sahih_same_lost": 78,
            "sahih_cross_lost": 226,
            "pickthall_same_lost": 85,
            "pickthall_cross_lost": 251,
            "sahih_lost_pairs": 304,
            "pickthall_lost_pairs": 336
        },
        {
            "root": "qdr",
            "occurrences": 132,
            "verse_count": 121,
            "unique_lemmas": 11,
            "sahih_top_count": 46,
            "pickthall_top_count": 49,
            "same_lemma_pairs": 1582,
            "cross_lemma_pairs": 5678,
            "sahih_same_lost": 338,
            "sahih_cross_lost": 4454,
            "pickthall_same_lost": 619,
            "pickthall_cross_lost": 4320,
            "sahih_lost_pairs": 4792,
            "pickthall_lost_pairs": 4939
        },
        {
            "root": "zwj",
            "occurrences": 81,
            "verse_count": 72,
            "unique_lemmas": 2,
            "sahih_top_count": 22,
            "pickthall_top_count": 29,
            "same_lemma_pairs": 2288,
            "cross_lemma_pairs": 268,
            "sahih_same_lost": 1526,
            "sahih_cross_lost": 232,
            "pickthall_same_lost": 1351,
            "pickthall_cross_lost": 240,
            "sahih_lost_pairs": 1758,
            "pickthall_lost_pairs": 1591
        },
        {
            "root": "Erj",
            "occurrences": 9,
            "verse_count": 9,
            "unique_lemmas": 3,
            "sahih_top_count": 5,
            "pickthall_top_count": 4,
            "same_lemma_pairs": 12,
            "cross_lemma_pairs": 24,
            "sahih_same_lost": 1,
            "sahih_cross_lost": 21,
            "pickthall_same_lost": 4,
            "pickthall_cross_lost": 18,
            "sahih_lost_pairs": 22,
            "pickthall_lost_pairs": 22
        },
        {
            "root": "nzl",
            "occurrences": 293,
            "verse_count": 257,
            "unique_lemmas": 12,
            "sahih_top_count": 152,
            "pickthall_top_count": 124,
            "same_lemma_pairs": 15036,
            "cross_lemma_pairs": 17860,
            "sahih_same_lost": 4636,
            "sahih_cross_lost": 10240,
            "pickthall_same_lost": 6314,
            "pickthall_cross_lost": 11086,
            "sahih_lost_pairs": 14876,
            "pickthall_lost_pairs": 17400
        },
        {
            "root": "xlq",
            "occurrences": 261,
            "verse_count": 218,
            "unique_lemmas": 8,
            "sahih_top_count": 150,
            "pickthall_top_count": 140,
            "same_lemma_pairs": 15065,
            "cross_lemma_pairs": 8588,
            "sahih_same_lost": 2288,
            "sahih_cross_lost": 6913,
            "pickthall_same_lost": 4393,
            "pickthall_cross_lost": 6685,
            "sahih_lost_pairs": 9201,
            "pickthall_lost_pairs": 11078
        },
        {
            "root": "Amr",
            "occurrences": 248,
            "verse_count": 226,
            "unique_lemmas": 6,
            "sahih_top_count": 83,
            "pickthall_top_count": 62,
            "same_lemma_pairs": 14111,
            "cross_lemma_pairs": 11314,
            "sahih_same_lost": 8394,
            "sahih_cross_lost": 7848,
            "pickthall_same_lost": 10342,
            "pickthall_cross_lost": 8741,
            "sahih_lost_pairs": 16242,
            "pickthall_lost_pairs": 19083
        },
        {
            "root": "Hqq",
            "occurrences": 287,
            "verse_count": 263,
            "unique_lemmas": 7,
            "sahih_top_count": 175,
            "pickthall_top_count": 157,
            "same_lemma_pairs": 26803,
            "cross_lemma_pairs": 7650,
            "sahih_same_lost": 9162,
            "sahih_cross_lost": 6271,
            "pickthall_same_lost": 11544,
            "pickthall_cross_lost": 6285,
            "sahih_lost_pairs": 15433,
            "pickthall_lost_pairs": 17829
        },
        {
            "root": "wzn",
            "occurrences": 23,
            "verse_count": 21,
            "unique_lemmas": 4,
            "sahih_top_count": 7,
            "pickthall_top_count": 10,
            "same_lemma_pairs": 125,
            "cross_lemma_pairs": 85,
            "sahih_same_lost": 67,
            "sahih_cross_lost": 53,
            "pickthall_same_lost": 69,
            "pickthall_cross_lost": 50,
            "sahih_lost_pairs": 120,
            "pickthall_lost_pairs": 119
        }
    ],
    "lemma_shuffle_null": {
        "sahih_ge_count": 0,
        "pickthall_ge_count": 0,
        "sahih_q025": [
            -8178367,
            1045628740
        ],
        "sahih_q975": [
            16548161,
            418251496
        ],
        "pickthall_q025": [
            1072089,
            522814370
        ],
        "pickthall_q975": [
            53695913,
            1045628740
        ],
        "per_root_sahih_ge": {
            "sbH": 0,
            "flk": 3,
            "wsE": 0,
            "mdd": 1,
            "qdr": 0,
            "zwj": 0,
            "Erj": 3,
            "nzl": 0,
            "xlq": 0,
            "Amr": 0,
            "Hqq": 0,
            "wzn": 43
        },
        "per_root_pickthall_ge": {
            "sbH": 0,
            "flk": 3,
            "wsE": 0,
            "mdd": 0,
            "qdr": 0,
            "zwj": 0,
            "Erj": 6,
            "nzl": 0,
            "xlq": 0,
            "Amr": 1,
            "Hqq": 0,
            "wzn": 97
        }
    },
    "distance_strata": {
        "same_surah_near": {
            "same_pairs": 426,
            "cross_pairs": 222,
            "sahih_same_lost": 83,
            "sahih_cross_lost": 124,
            "pickthall_same_lost": 123,
            "pickthall_cross_lost": 138
        },
        "same_surah_far": {
            "same_pairs": 1620,
            "cross_pairs": 897,
            "sahih_same_lost": 526,
            "sahih_cross_lost": 519,
            "pickthall_same_lost": 673,
            "pickthall_cross_lost": 595
        },
        "diff_surah_near": {
            "same_pairs": 24728,
            "cross_pairs": 16259,
            "sahih_same_lost": 8228,
            "sahih_cross_lost": 10734,
            "pickthall_same_lost": 10807,
            "pickthall_cross_lost": 11550
        },
        "diff_surah_far": {
            "same_pairs": 50306,
            "cross_pairs": 36884,
            "sahih_same_lost": 17683,
            "sahih_cross_lost": 25465,
            "pickthall_same_lost": 23819,
            "pickthall_cross_lost": 27490
        }
    },
    "bg_sahih_pair": [
        897,
        1000
    ],
    "bg_pickthall_pair": [
        923,
        1000
    ]
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
            raise LexiconOracleError("CORPUS_MISSING", f"missing corpus file {rel_path}")
        actual = sha256_file(full_path)
        if actual != expected:
            raise LexiconOracleError("SHA256_MISMATCH", f"hash mismatch for {rel_path}")
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
            raise LexiconOracleError("PARSE_ERROR", "malformed tanzil verse line")
        verses[(int(parts[0]), int(parts[1]))] = parts[2]
    return verses


def parse_openiti_stems(lines):
    in_body = False
    stems = []
    for raw in lines:
        line = raw.strip()
        if not in_body:
            if line.startswith("#META#Header#End#"):
                in_body = True
            continue
        if not line or line.startswith("###"):
            continue
        cleaned = OPENITI_NOISE_RE.sub(" ", line)
        for tok in cleaned.split():
            if to_rasm(tok):
                stems.append(light_stem_ar(tok))
    return stems


def parse_leeds_lexicon_lines(lines):
    all_roots = set()
    root_vf = defaultdict(Counter)
    verb_pairs_all = []
    verb_pairs_odd = []
    verb_pairs_even = []
    form_xii_tokens = 0
    verse_roots = defaultdict(set)
    verse_root_lems = defaultdict(lambda: defaultdict(set))
    root_verses = defaultdict(set)
    root_occs = Counter()
    root_lems = defaultdict(set)

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
        s_num = int(loc_parts[0])
        v_num = int(loc_parts[1])

        all_roots.add(root)
        verse_roots[(s_num, v_num)].add(root)
        if lem:
            verse_root_lems[(s_num, v_num)][root].add(lem)
            root_lems[root].add(lem)
        root_verses[root].add((s_num, v_num))
        root_occs[root] += 1

        if tag == "V":
            vm = VF_RE.search(feat)
            vf = vm.group(1) if vm else "I"
            if vf == "XII":
                form_xii_tokens += 1
            elif vf in OP_CLASS_MAP:
                root_vf[root][vf] += 1
                verb_pairs_all.append((root, vf))
                if s_num % 2 == 1:
                    verb_pairs_odd.append((root, vf))
                else:
                    verb_pairs_even.append((root, vf))

    return {
        "total_unique_roots": len(all_roots),
        "root_vf": root_vf,
        "verb_pairs_all": verb_pairs_all,
        "verb_pairs_odd": verb_pairs_odd,
        "verb_pairs_even": verb_pairs_even,
        "form_xii_tokens": form_xii_tokens,
        "verse_roots": verse_roots,
        "verse_root_lems": verse_root_lems,
        "root_verses": root_verses,
        "root_occs": root_occs,
        "root_lems": root_lems,
        "top10_roots": frozenset(r for r, _ in root_occs.most_common(10)),
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


def within_root_renyi2_pair(verb_pairs):
    by_root = defaultdict(Counter)
    for root, vf in verb_pairs:
        by_root[root][vf] += 1
    num = 0
    den = 0
    for cnt in by_root.values():
        tot = sum(cnt.values())
        den += tot * tot
        num += sum(c * c for c in cnt.values())
    return [num, den]


def multishuffle_within_root_renyi2(verb_pairs, n_shuffles, base_seed, stratified=False):
    obs_u, obs_d = within_root_renyi2_pair(verb_pairs)
    r_col = [p[0] for p in verb_pairs]
    vf_col = [p[1] for p in verb_pairs]
    bins = None
    if stratified:
        r_freq = Counter(r_col)
        bins = [
            "B1" if r_freq[r] <= 2 else ("B2" if r_freq[r] <= 10 else ("B3" if r_freq[r] <= 50 else "B4"))
            for r in r_col
        ]
    sum_u = 0
    sum_d = 0
    ge = 0
    for b in range(n_shuffles):
        if bins is None:
            sh_vf = det_shuffle_exact(vf_col, base_seed + b)
        else:
            sh_vf = stratified_shuffle_exact(vf_col, bins, base_seed + b)
        nu, nd = within_root_renyi2_pair(list(zip(r_col, sh_vf)))
        sum_u += nu
        sum_d += nd
        if nu * obs_d >= obs_u * nd:
            ge += 1
    return [sum_u, sum_d], ge


def build_context_counters(verse_roots, target_set, exclude, split=None):
    ctx = {r: Counter() for r in target_set}
    for (s_num, _), rset in verse_roots.items():
        if split == "odd" and s_num % 2 != 1:
            continue
        if split == "even" and s_num % 2 != 0:
            continue
        present = rset & target_set
        if not present:
            continue
        for r in present:
            for nb in rset:
                if nb != r and nb not in exclude:
                    ctx[r][nb] += 1
    return ctx


def pooled_context_renyi2_pair(ctx_dict):
    num = 0
    den = 0
    for cnt in ctx_dict.values():
        tot = sum(cnt.values())
        if tot == 0:
            continue
        num += sum(c * c for c in cnt.values())
        den += tot * tot
    return [num, den]


def pooled_weighted_context_jaccard_pair(ctx_dict, keys):
    inter = 0
    union = 0
    klist = sorted(keys)
    for i in range(len(klist)):
        c1 = ctx_dict[klist[i]]
        for j in range(i + 1, len(klist)):
            c2 = ctx_dict[klist[j]]
            for w in c1.keys() | c2.keys():
                v1 = c1[w]
                v2 = c2[w]
                inter += v1 if v1 < v2 else v2
                union += v1 if v1 > v2 else v2
    return [inter, union]


def target_cooccur_pair(verse_roots, target_set, split=None):
    co_verses = 0
    tot_verses = 0
    for (s_num, _), rset in verse_roots.items():
        if split == "odd" and s_num % 2 != 1:
            continue
        if split == "even" and s_num % 2 != 0:
            continue
        hits = len(rset & target_set)
        if hits >= 1:
            tot_verses += 1
            if hits >= 2:
                co_verses += 1
    return [co_verses, tot_verses]


def _read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def compute_live_measurements(
    corpus_dir,
    expected_hashes=None,
    ctrl_window=CTRL_WINDOW,
    bg_pair_count=BG_PAIR_COUNT,
    min_multi_verses=9,
    n_shuffles=MIN_MULTISHUFFLE_B,
):
    verified_hashes = verify_corpus_hashes(corpus_dir, expected_hashes=expected_hashes)

    md = parse_leeds_lexicon_lines(
        _read_lines(os.path.join(corpus_dir, "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt"))
    )
    uthmani = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-quran-uthmani.txt")))
    sahih = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-en.sahih.txt")))
    pick = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-en.pickthall.txt")))

    # Pillar 1: 1,642-root x Wazn (I..X) descriptive matrix & B-shuffle within-root Renyi-2
    verb_roots_sorted = sorted(md["root_vf"].keys())
    poly_wazn_roots = sum(1 for r in verb_roots_sorted if len(md["root_vf"][r]) >= 2)
    op_class_counts = Counter()
    for _, vf in md["verb_pairs_all"]:
        op_class_counts[OP_CLASS_MAP[vf]] += 1
    transition_pair_counts = {
        f"{a}+{b}": sum(1 for r in verb_roots_sorted if a in md["root_vf"][r] and b in md["root_vf"][r])
        for a, b in TRANSITION_PAIRS
    }

    t4a_pool, ge_t4a = multishuffle_within_root_renyi2(md["verb_pairs_all"], n_shuffles, SEED_WAZN_T4A, stratified=False)
    t4b_pool, ge_t4b = multishuffle_within_root_renyi2(md["verb_pairs_all"], n_shuffles, SEED_WAZN_T4B, stratified=True)
    odd_t4b_pool, ge_odd = multishuffle_within_root_renyi2(md["verb_pairs_odd"], n_shuffles, SEED_WAZN_ODD_T4B, stratified=True)
    even_t4b_pool, ge_even = multishuffle_within_root_renyi2(md["verb_pairs_even"], n_shuffles, SEED_WAZN_EVEN_T4B, stratified=True)

    within_root_renyi2_pairs = {
        "all_obs": within_root_renyi2_pair(md["verb_pairs_all"]),
        "all_t4a": t4a_pool,
        "all_t4b": t4b_pool,
        "odd_obs": within_root_renyi2_pair(md["verb_pairs_odd"]),
        "odd_t4b": odd_t4b_pool,
        "even_obs": within_root_renyi2_pair(md["verb_pairs_even"]),
        "even_t4b": even_t4b_pool,
    }
    within_root_ge_counts = {
        "all_t4a": ge_t4a,
        "all_t4b": ge_t4b,
        "odd_t4b": ge_odd,
        "even_t4b": ge_even,
    }

    q_stems = [
        light_stem_ar(t)
        for k in sorted(uthmani.keys())
        for t in uthmani[k].split()
        if to_rasm(t)
    ]
    kalila_stems = parse_openiti_stems(_read_lines(os.path.join(corpus_dir, "openiti_controls/ibn_muqaffa_kalila.txt")))
    adab_stems = parse_openiti_stems(_read_lines(os.path.join(corpus_dir, "openiti_controls/ibn_muqaffa_adab_kabir.txt")))
    poetry_stems = (
        parse_openiti_stems(_read_lines(os.path.join(corpus_dir, "openiti_controls/imru_al_qays_diwan.txt")))
        + parse_openiti_stems(_read_lines(os.path.join(corpus_dir, "openiti_controls/tarafa_diwan.txt")))
        + parse_openiti_stems(_read_lines(os.path.join(corpus_dir, "openiti_controls/antara_muallaqa.txt")))
    )

    control_renyi2_metrics = {}
    for c_idx, (name, seq) in enumerate((
        ("quran_stem", q_stems),
        ("kalila_prose", kalila_stems),
        ("adab_prose", adab_stems),
        ("poetry_pooled", poetry_stems),
    )):
        ids = _encode_ids(seq)
        g_pair = list(renyi2_concentration_pair(dict(Counter(ids)))[:2])
        on, od = block_renyi2_cross_pair(ids, ctrl_window)[:2]
        sn = sd = ge_c = 0
        for b in range(n_shuffles):
            sh = det_shuffle_exact(ids, SEED_CTRL_R2_T4A + c_idx * 1000 + b)
            nn, nd = block_renyi2_cross_pair(sh, ctrl_window)[:2]
            sn += nn
            sd += nd
            if nn * od >= on * nd:
                ge_c += 1
        control_renyi2_metrics[name] = {
            "global_c2": g_pair,
            "w20_obs": [on, od],
            "w20_t4a_pooled": [sn, sd],
            "w20_ge_count": ge_c,
        }

    # Pillar 2: Top-10-stripped Arabic co-occurrence context topology (B-shuffle nulls)
    target_set = frozenset(TARGET_ROOTS)
    multi_targets = frozenset(r for r in TARGET_ROOTS if len(md["root_verses"][r]) >= min_multi_verses)
    top10 = md["top10_roots"]

    def _eval_ctx_bundle(vr):
        ca = build_context_counters(vr, target_set, top10)
        co = build_context_counters(vr, target_set, top10, "odd")
        ce = build_context_counters(vr, target_set, top10, "even")
        return {
            "ctx_r2_all": pooled_context_renyi2_pair(ca),
            "ctx_r2_odd": pooled_context_renyi2_pair(co),
            "ctx_r2_even": pooled_context_renyi2_pair(ce),
            "ctx_jaccard_all": pooled_weighted_context_jaccard_pair(ca, multi_targets),
            "ctx_jaccard_odd": pooled_weighted_context_jaccard_pair(co, multi_targets),
            "ctx_jaccard_even": pooled_weighted_context_jaccard_pair(ce, multi_targets),
            "cooccur_all": target_cooccur_pair(vr, target_set),
            "cooccur_odd": target_cooccur_pair(vr, target_set, "odd"),
            "cooccur_even": target_cooccur_pair(vr, target_set, "even"),
        }

    obs_ctx = _eval_ctx_bundle(md["verse_roots"])
    all_vkeys = sorted(md["verse_roots"].keys())
    flat_roots = []
    v_lens = []
    for k in all_vkeys:
        rs = sorted(md["verse_roots"][k])
        v_lens.append(len(rs))
        flat_roots.extend(rs)

    null_sum = {k: [0, 0] for k in obs_ctx}
    extreme_counts = {k: 0 for k in obs_ctx}
    for b in range(n_shuffles):
        sh_roots = det_shuffle_exact(flat_roots, SEED_CTX_NULL + b * 251)
        nvr = {}
        pos = 0
        for k, ln in zip(all_vkeys, v_lens):
            nvr[k] = set(sh_roots[pos:pos + ln])
            pos += ln
        nc = _eval_ctx_bundle(nvr)
        for k, pair in nc.items():
            null_sum[k][0] += pair[0]
            null_sum[k][1] += pair[1]
            on, od = obs_ctx[k]
            nn, nd = pair
            if k.startswith("ctx_jaccard_"):
                if nn * od <= on * nd:
                    extreme_counts[k] += 1
            elif nn * od >= on * nd:
                extreme_counts[k] += 1

    context_metrics = {
        "ctx_r2_all": obs_ctx["ctx_r2_all"],
        "ctx_r2_null_pooled": null_sum["ctx_r2_all"],
        "ctx_r2_odd": obs_ctx["ctx_r2_odd"],
        "ctx_r2_odd_null_pooled": null_sum["ctx_r2_odd"],
        "ctx_r2_even": obs_ctx["ctx_r2_even"],
        "ctx_r2_even_null_pooled": null_sum["ctx_r2_even"],
        "ctx_jaccard_all": obs_ctx["ctx_jaccard_all"],
        "ctx_jaccard_null_pooled": null_sum["ctx_jaccard_all"],
        "ctx_jaccard_odd": obs_ctx["ctx_jaccard_odd"],
        "ctx_jaccard_odd_null_pooled": null_sum["ctx_jaccard_odd"],
        "ctx_jaccard_even": obs_ctx["ctx_jaccard_even"],
        "ctx_jaccard_even_null_pooled": null_sum["ctx_jaccard_even"],
        "cooccur_all": obs_ctx["cooccur_all"],
        "cooccur_null_pooled": null_sum["cooccur_all"],
        "cooccur_odd": obs_ctx["cooccur_odd"],
        "cooccur_odd_null_pooled": null_sum["cooccur_odd"],
        "cooccur_even": obs_ctx["cooccur_even"],
        "cooccur_even_null_pooled": null_sum["cooccur_even"],
        "extreme_counts": extreme_counts,
    }

    # Pillar 3: 2-instrument projection defect + B-shuffle lemma null + 4 distance strata
    sahih_stems = {k: en_content_stems(v) for k, v in sahih.items()}
    pick_stems = {k: en_content_stems(v) for k, v in pick.items()}
    all_v_sorted = sorted(sahih.keys())
    v_global_idx = {k: idx for idx, k in enumerate(all_v_sorted)}

    shuf_keys = det_shuffle_exact(all_v_sorted, SEED_BG_PAIRS)
    bg_s_lost = 0
    bg_p_lost = 0
    for i in range(bg_pair_count):
        k1 = shuf_keys[2 * i]
        k2 = shuf_keys[2 * i + 1]
        if not (sahih_stems[k1] & sahih_stems[k2]):
            bg_s_lost += 1
        if not (pick_stems[k1] & pick_stems[k2]):
            bg_p_lost += 1

    strata_names = ("same_surah_near", "same_surah_far", "diff_surah_near", "diff_surah_far")
    distance_strata = {
        sk: {
            "same_pairs": 0, "cross_pairs": 0,
            "sahih_same_lost": 0, "sahih_cross_lost": 0,
            "pickthall_same_lost": 0, "pickthall_cross_lost": 0,
        }
        for sk in strata_names
    }

    root_records = []
    multi_precomp = {}
    multi_roots = []
    for root in TARGET_ROOTS:
        vs = sorted(md["root_verses"][root])
        n = len(vs)
        s_df = Counter()
        p_df = Counter()
        for k in vs:
            for st in sahih_stems[k]:
                s_df[st] += 1
            for st in pick_stems[k]:
                p_df[st] += 1
        s_top = s_df.most_common(1)[0][1] if s_df else 0
        p_top = p_df.most_common(1)[0][1] if p_df else 0
        lems_v = [frozenset(md["verse_root_lems"][k][root]) for k in vs]
        same_p = cross_p = 0
        s_same_l = s_cross_l = p_same_l = p_cross_l = 0
        sz_mat = [[False] * n for _ in range(n)]
        pz_mat = [[False] * n for _ in range(n)]
        for i in range(n):
            k1 = vs[i]
            for j in range(i + 1, n):
                k2 = vs[j]
                s_zero = not (sahih_stems[k1] & sahih_stems[k2])
                p_zero = not (pick_stems[k1] & pick_stems[k2])
                sz_mat[i][j] = s_zero
                pz_mat[i][j] = p_zero
                if lems_v[i] & lems_v[j]:
                    same_p += 1
                    if s_zero:
                        s_same_l += 1
                    if p_zero:
                        p_same_l += 1
                else:
                    cross_p += 1
                    if s_zero:
                        s_cross_l += 1
                    if p_zero:
                        p_cross_l += 1
        if same_p > 0 and cross_p > 0:
            multi_roots.append(root)
            multi_precomp[root] = (n, lems_v, sz_mat, pz_mat)
            for i in range(n):
                k1 = vs[i]
                g1 = v_global_idx[k1]
                for j in range(i + 1, n):
                    k2 = vs[j]
                    d = abs(v_global_idx[k2] - g1)
                    if k1[0] == k2[0]:
                        sk = "same_surah_near" if d <= 10 else "same_surah_far"
                    else:
                        sk = "diff_surah_near" if d <= 1000 else "diff_surah_far"
                    sd = distance_strata[sk]
                    if lems_v[i] & lems_v[j]:
                        sd["same_pairs"] += 1
                        if sz_mat[i][j]:
                            sd["sahih_same_lost"] += 1
                        if pz_mat[i][j]:
                            sd["pickthall_same_lost"] += 1
                    else:
                        sd["cross_pairs"] += 1
                        if sz_mat[i][j]:
                            sd["sahih_cross_lost"] += 1
                        if pz_mat[i][j]:
                            sd["pickthall_cross_lost"] += 1

        root_records.append({
            "root": root,
            "occurrences": md["root_occs"][root],
            "verse_count": n,
            "unique_lemmas": len(md["root_lems"][root]),
            "sahih_top_count": s_top,
            "pickthall_top_count": p_top,
            "same_lemma_pairs": same_p,
            "cross_lemma_pairs": cross_p,
            "sahih_same_lost": s_same_l,
            "sahih_cross_lost": s_cross_l,
            "pickthall_same_lost": p_same_l,
            "pickthall_cross_lost": p_cross_l,
            "sahih_lost_pairs": s_same_l + s_cross_l,
            "pickthall_lost_pairs": p_same_l + p_cross_l,
        })

    # B-shuffle within-root lemma-label shuffle null
    def _eval_lemma_gaps(lems_map):
        st = sl = ct = cl = psl = pcl = 0
        pr_gaps = {}
        for mr in multi_roots:
            n_r, _, sz_m, pz_m = multi_precomp[mr]
            lv = lems_map[mr]
            r_st = r_sl = r_ct = r_cl = r_psl = r_pcl = 0
            for i in range(n_r):
                li = lv[i]
                srow = sz_m[i]
                prow = pz_m[i]
                for j in range(i + 1, n_r):
                    if li & lv[j]:
                        r_st += 1
                        if srow[j]:
                            r_sl += 1
                        if prow[j]:
                            r_psl += 1
                    else:
                        r_ct += 1
                        if srow[j]:
                            r_cl += 1
                        if prow[j]:
                            r_pcl += 1
            st += r_st
            sl += r_sl
            ct += r_ct
            cl += r_cl
            psl += r_psl
            pcl += r_pcl
            pr_gaps[mr] = (
                Fraction(r_cl, r_ct) - Fraction(r_sl, r_st),
                Fraction(r_pcl, r_ct) - Fraction(r_psl, r_st),
            )
        return Fraction(cl, ct) - Fraction(sl, st), Fraction(pcl, ct) - Fraction(psl, st), pr_gaps

    obs_lems_map = {mr: multi_precomp[mr][1] for mr in multi_roots}
    obs_s_gap, obs_p_gap, obs_pr_gaps = _eval_lemma_gaps(obs_lems_map)
    s_null_gaps = []
    p_null_gaps = []
    s_ge = p_ge = 0
    pr_s_ge = {mr: 0 for mr in multi_roots}
    pr_p_ge = {mr: 0 for mr in multi_roots}
    for b in range(n_shuffles):
        sh_map = {
            mr: det_shuffle_exact(obs_lems_map[mr], SEED_LEMMA_SHUFFLE + b * 131 + idx)
            for idx, mr in enumerate(multi_roots)
        }
        sg, pg, prg = _eval_lemma_gaps(sh_map)
        s_null_gaps.append(sg)
        p_null_gaps.append(pg)
        if sg >= obs_s_gap:
            s_ge += 1
        if pg >= obs_p_gap:
            p_ge += 1
        for mr in multi_roots:
            if prg[mr][0] >= obs_pr_gaps[mr][0]:
                pr_s_ge[mr] += 1
            if prg[mr][1] >= obs_pr_gaps[mr][1]:
                pr_p_ge[mr] += 1

    s_sorted = sorted(s_null_gaps)
    p_sorted = sorted(p_null_gaps)
    q025_i = (n_shuffles * 25) // 1000
    q975_i = min(n_shuffles - 1, (n_shuffles * 975) // 1000)

    lemma_shuffle_null = {
        "sahih_ge_count": s_ge,
        "pickthall_ge_count": p_ge,
        "sahih_q025": [s_sorted[q025_i].numerator, s_sorted[q025_i].denominator],
        "sahih_q975": [s_sorted[q975_i].numerator, s_sorted[q975_i].denominator],
        "pickthall_q025": [p_sorted[q025_i].numerator, p_sorted[q025_i].denominator],
        "pickthall_q975": [p_sorted[q975_i].numerator, p_sorted[q975_i].denominator],
        "per_root_sahih_ge": pr_s_ge,
        "per_root_pickthall_ge": pr_p_ge,
    }

    return {
        "n_shuffles": n_shuffles,
        "pinned_sha256s": verified_hashes,
        "total_unique_roots": md["total_unique_roots"],
        "verb_roots": len(verb_roots_sorted),
        "poly_wazn_roots": poly_wazn_roots,
        "verb_tokens_i_x": len(md["verb_pairs_all"]),
        "form_xii_tokens": md["form_xii_tokens"],
        "op_class_counts": dict(op_class_counts),
        "transition_pair_counts": transition_pair_counts,
        "within_root_renyi2_pairs": within_root_renyi2_pairs,
        "within_root_ge_counts": within_root_ge_counts,
        "control_renyi2_metrics": control_renyi2_metrics,
        "context_metrics": context_metrics,
        "root_records": root_records,
        "lemma_shuffle_null": lemma_shuffle_null,
        "distance_strata": distance_strata,
        "bg_sahih_pair": [bg_s_lost, bg_pair_count],
        "bg_pickthall_pair": [bg_p_lost, bg_pair_count],
    }


def certify_from_measurements(mode, live_corpus_recounted, measurements):
    n_shuf = measurements["n_shuffles"]
    p1 = audit_wazn_agency_matrix_and_renyi2_exact(
        total_unique_roots=measurements["total_unique_roots"],
        verb_roots=measurements["verb_roots"],
        poly_wazn_roots=measurements["poly_wazn_roots"],
        verb_tokens_i_x=measurements["verb_tokens_i_x"],
        form_xii_tokens=measurements["form_xii_tokens"],
        op_class_counts=measurements["op_class_counts"],
        transition_pair_counts=measurements["transition_pair_counts"],
        within_root_renyi2_pairs=measurements["within_root_renyi2_pairs"],
        within_root_ge_counts=measurements["within_root_ge_counts"],
        control_renyi2_metrics=measurements["control_renyi2_metrics"],
        n_shuffles=n_shuf,
    )
    p2 = audit_context_neighborhood_topology_exact(
        measurements["context_metrics"],
        n_shuffles=n_shuf,
    )
    p3 = audit_two_layer_projection_defect_exact(
        root_records=measurements["root_records"],
        bg_sahih_pair=measurements["bg_sahih_pair"],
        bg_pickthall_pair=measurements["bg_pickthall_pair"],
        lemma_shuffle_null=measurements["lemma_shuffle_null"],
        distance_strata=measurements["distance_strata"],
        n_shuffles=n_shuf,
    )
    five_axes = {
        "single_corpus_wazn_descriptive_renyi2": p1["agency_matrix_nontrivial"] and p1["within_root_wazn_beats_nulls"],
        "openiti_negative_controls": p1["shared_prose_renyi2_lift"] and p1["poetry_higher_effective_diversity"],
        "arabic_context_topology_split_half": (
            p2["ctx_r2_specialized_split_half"]
            and p2["distinct_neighborhoods_vs_background"]
            and p2["direct_coupling_enriched_split_half"]
        ),
        "lemma_shuffle_and_distance_control": (
            p3["intra_lemma_polysemy_nonzero"]
            and p3["lemma_shuffle_significant_both"]
            and p3["all_distance_strata_positive_both"]
        ),
        "two_translator_agreement": (
            p3["below_background_both_translators"] and p3["unanimous_cross_lemma_amplification"]
        ),
    }
    return certify_arabic_lexicon_own_terms_gate(
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
    parser = argparse.ArgumentParser(description="Classical Arabic lexicon topology audit (v2)")
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
