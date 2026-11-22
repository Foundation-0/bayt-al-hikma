"""Dual-mode (live_readonly + --standalone) audit runner for Wave 3 Lane 5 (AUDIT-091):
Classical Arabic / Qur'anic layered continuum semantics & non-concatenative
root-pattern geometry.

Live read-only mode verifies all 9 pinned primary corpus SHA-256 hashes under
../repos/arabic/ and computes every exact rational count directly from the raw
texts. Standalone mode runs with zero external file dependencies against the
verbatim measured integer fixture and verifies identical oracle certification.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import os
import re
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from arabic_continuum_oracle import (
    ArabicOracleError,
    audit_ring_vs_inclusio_transform_exact,
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
    "window_jaccard_cohesion_w10_w20_w40",
    "tier4a_iid_and_tier4b_pos_nulls",
    "classical_arabic_prose_and_poetry_controls",
    "pointwise_ring_falsification_vs_boundary_inclusio",
    "top10_stripped_split_half_unseen_inclusio",
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

SEED_T4A = 2026091
SEED_T4B = 2026092
SEED_ODD_T4B = 2026093
SEED_EVEN_T4B = 2026094
SEED_RING_PERM = 2026095
SEED_CTRL_T4A = 2026096
SEED_BG_PAIRS = 2026097
BG_PAIR_COUNT = 1000
WINDOW_SIZES = (10, 20, 40)
ARB_CHUNK_LINES = 60

STANDALONE_FIXTURE = {
    "pinned_sha256s": dict(EXPECTED_CORPUS_SHA256),
    "unique_roots": 1642,
    "unique_lemmas": 4657,
    "unique_root_wazn_cells": 3923,
    "total_root_tokens": 49968,
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
        "XII": 9,
    },
    "window_metrics": {
        10: {
            "raw": [3075, 149959],
            "rasm": [4968, 146340],
            "stem": [6342, 143242],
            "root": [5961, 84662],
            "root_t4a": [3531, 92671],
            "root_t4b": [3722, 92353],
            "odd_root": [2801, 39772],
            "odd_t4b": [1771, 43306],
            "even_root": [3159, 44852],
            "even_t4b": [1946, 48890],
        },
        20: {
            "raw": [4723, 145316],
            "rasm": [7253, 139141],
            "stem": [8954, 134393],
            "root": [7283, 77384],
            "root_t4a": [5600, 86999],
            "root_t4b": [5468, 86833],
            "odd_root": [3354, 36390],
            "odd_t4b": [2617, 40639],
            "even_root": [3892, 40914],
            "even_t4b": [2948, 45952],
        },
        40: {
            "raw": [6396, 138905],
            "rasm": [9054, 130114],
            "stem": [10868, 123506],
            "root": [8300, 69156],
            "root_t4a": [7780, 79217],
            "root_t4b": [7472, 79327],
            "odd_root": [3792, 32573],
            "odd_t4b": [3625, 36992],
            "even_root": [4319, 36542],
            "even_t4b": [3995, 41903],
        },
    },
    "control_w20_pairs": {
        "quran_stem": {"obs": [8954, 134393], "t4a": [5829, 142800]},
        "kalila_prose": {"obs": [5398, 76231], "t4a": [3234, 81211]},
        "adab_prose": {"obs": [1178, 16040], "t4a": [846, 17285]},
        "poetry_pooled": {"obs": [501, 19177], "t4a": [322, 19763]},
    },
    "ring_metrics": {
        "all_mirror": [1642, 40725],
        "all_shift": [1642, 40689],
        "all_perm_null": [1707, 40708],
        "all_inclusio": [769, 5204],
        "all_middle": [698, 5004],
        "odd_inclusio": [372, 2485],
        "odd_middle": [339, 2418],
        "even_inclusio": [397, 2719],
        "even_middle": [359, 2586],
        "odd_strip10_inclusio": [278, 2253],
        "odd_strip10_middle": [240, 2208],
        "even_strip10_inclusio": [281, 2475],
        "even_strip10_middle": [250, 2356],
        "kalila_arb_inclusio": [570, 6419],
        "kalila_arb_middle": [584, 6425],
        "kalila_nat_inclusio": [632, 4599],
        "kalila_nat_middle": [607, 4754],
    },
    "root_records": [
        {
            "root": "ftq",
            "occurrences": 1,
            "verse_count": 1,
            "unique_lemmas": 1,
            "sahih_top_count": 1,
            "pickthall_top_count": 1,
            "sahih_lost_pairs": 0,
            "pickthall_lost_pairs": 0,
            "sahih_total_pairs": 0,
            "pickthall_total_pairs": 0,
        },
        {
            "root": "rtq",
            "occurrences": 1,
            "verse_count": 1,
            "unique_lemmas": 1,
            "sahih_top_count": 1,
            "pickthall_top_count": 1,
            "sahih_lost_pairs": 0,
            "pickthall_lost_pairs": 0,
            "sahih_total_pairs": 0,
            "pickthall_total_pairs": 0,
        },
        {
            "root": "sbH",
            "occurrences": 92,
            "verse_count": 87,
            "unique_lemmas": 7,
            "sahih_top_count": 82,
            "pickthall_top_count": 28,
            "sahih_lost_pairs": 357,
            "pickthall_lost_pairs": 2498,
            "sahih_total_pairs": 3741,
            "pickthall_total_pairs": 3741,
        },
        {
            "root": "mdd",
            "occurrences": 32,
            "verse_count": 29,
            "unique_lemmas": 9,
            "sahih_top_count": 11,
            "pickthall_top_count": 7,
            "sahih_lost_pairs": 304,
            "pickthall_lost_pairs": 336,
            "sahih_total_pairs": 406,
            "pickthall_total_pairs": 406,
        },
        {
            "root": "wsE",
            "occurrences": 32,
            "verse_count": 29,
            "unique_lemmas": 6,
            "sahih_top_count": 12,
            "pickthall_top_count": 8,
            "sahih_lost_pairs": 218,
            "pickthall_lost_pairs": 258,
            "sahih_total_pairs": 406,
            "pickthall_total_pairs": 406,
        },
        {
            "root": "flk",
            "occurrences": 25,
            "verse_count": 25,
            "unique_lemmas": 2,
            "sahih_top_count": 23,
            "pickthall_top_count": 23,
            "sahih_lost_pairs": 39,
            "pickthall_lost_pairs": 42,
            "sahih_total_pairs": 300,
            "pickthall_total_pairs": 300,
        },
        {
            "root": "kwr",
            "occurrences": 3,
            "verse_count": 2,
            "unique_lemmas": 1,
            "sahih_top_count": 2,
            "pickthall_top_count": 1,
            "sahih_lost_pairs": 0,
            "pickthall_lost_pairs": 1,
            "sahih_total_pairs": 1,
            "pickthall_total_pairs": 1,
        },
        {
            "root": "qdr",
            "occurrences": 132,
            "verse_count": 121,
            "unique_lemmas": 11,
            "sahih_top_count": 46,
            "pickthall_top_count": 49,
            "sahih_lost_pairs": 4792,
            "pickthall_lost_pairs": 4939,
            "sahih_total_pairs": 7260,
            "pickthall_total_pairs": 7260,
        },
        {
            "root": "zwj",
            "occurrences": 81,
            "verse_count": 72,
            "unique_lemmas": 2,
            "sahih_top_count": 22,
            "pickthall_top_count": 29,
            "sahih_lost_pairs": 1758,
            "pickthall_lost_pairs": 1591,
            "sahih_total_pairs": 2556,
            "pickthall_total_pairs": 2556,
        },
    ],
    "bg_sahih_pair": [897, 1000],
    "bg_pickthall_pair": [923, 1000],
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


def evaluate_ring_and_inclusio_units(units, exclude=frozenset(), seed=SEED_RING_PERM):
    m_i = m_u = sh_i = sh_u = pn_i = pn_u = 0
    inc_i = inc_u = mid_i = mid_u = 0
    for idx, unit in enumerate(units):
        length = len(unit)
        if length < 20:
            continue
        sets = [set(x for x in verse if x not in exclude) for verse in unit]
        half = length // 2
        for i in range(half):
            a = sets[i]
            b = sets[length - 1 - i]
            m_i += len(a & b)
            m_u += len(a | b)
            c = sets[half + i]
            sh_i += len(a & c)
            sh_u += len(a | c)
        perm = det_shuffle_exact(sets, seed + idx)
        for i in range(half):
            a = perm[i]
            b = perm[length - 1 - i]
            pn_i += len(a & b)
            pn_u += len(a | b)
        k = length // 10
        first_set = set().union(*sets[:k])
        last_set = set().union(*sets[length - k:])
        mid_start = (length - k) // 2
        mid_set = set().union(*sets[mid_start:mid_start + k])
        inc_i += len(first_set & last_set)
        inc_u += len(first_set | last_set)
        mid_i += len(first_set & mid_set)
        mid_u += len(first_set | mid_set)
    return {
        "mirror": [m_i, m_u],
        "shift": [sh_i, sh_u],
        "perm_null": [pn_i, pn_u],
        "inclusio": [inc_i, inc_u],
        "middle": [mid_i, mid_u],
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

    root_t4a_seq = det_shuffle_exact(morph_data["leeds_roots"], SEED_T4A)
    root_t4b_seq = stratified_shuffle_exact(morph_data["leeds_roots"], morph_data["leeds_pos"], SEED_T4B)
    odd_t4b_seq = stratified_shuffle_exact(morph_data["leeds_odd"], morph_data["leeds_odd_pos"], SEED_ODD_T4B)
    even_t4b_seq = stratified_shuffle_exact(morph_data["leeds_even"], morph_data["leeds_even_pos"], SEED_EVEN_T4B)

    window_metrics = {}
    for w in window_sizes:
        window_metrics[w] = {
            "raw": list(block_jaccard_cohesion_exact(uth_raw, w)[:2]),
            "rasm": list(block_jaccard_cohesion_exact(uth_rasm, w)[:2]),
            "stem": list(block_jaccard_cohesion_exact(uth_stem, w)[:2]),
            "root": list(block_jaccard_cohesion_exact(morph_data["leeds_roots"], w)[:2]),
            "root_t4a": list(block_jaccard_cohesion_exact(root_t4a_seq, w)[:2]),
            "root_t4b": list(block_jaccard_cohesion_exact(root_t4b_seq, w)[:2]),
            "odd_root": list(block_jaccard_cohesion_exact(morph_data["leeds_odd"], w)[:2]),
            "odd_t4b": list(block_jaccard_cohesion_exact(odd_t4b_seq, w)[:2]),
            "even_root": list(block_jaccard_cohesion_exact(morph_data["leeds_even"], w)[:2]),
            "even_t4b": list(block_jaccard_cohesion_exact(even_t4b_seq, w)[:2]),
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
    control_w20_pairs = {}
    for name, seq in (
        ("quran_stem", uth_stem),
        ("kalila_prose", kalila_flat),
        ("adab_prose", adab_flat),
        ("poetry_pooled", poetry_flat),
    ):
        obs_p = list(block_jaccard_cohesion_exact(seq, ctrl_w)[:2])
        null_p = list(block_jaccard_cohesion_exact(det_shuffle_exact(seq, SEED_CTRL_T4A), ctrl_w)[:2])
        control_w20_pairs[name] = {"obs": obs_p, "t4a": null_p}

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

    ri_all = evaluate_ring_and_inclusio_units(all_units)
    ri_odd = evaluate_ring_and_inclusio_units(odd_units)
    ri_even = evaluate_ring_and_inclusio_units(even_units)
    ri_odd_s10 = evaluate_ring_and_inclusio_units(odd_units, morph_data["top10_roots"])
    ri_even_s10 = evaluate_ring_and_inclusio_units(even_units, morph_data["top10_roots"])
    kalila_arb = [
        kalila_lines[i:i + arb_chunk_lines]
        for i in range(0, len(kalila_lines) - arb_chunk_lines + 1, arb_chunk_lines)
    ]
    kalila_nat = [sec for sec in kalila_secs if len(sec) >= 20]
    ri_kalila_arb = evaluate_ring_and_inclusio_units(kalila_arb)
    ri_kalila_nat = evaluate_ring_and_inclusio_units(kalila_nat)

    ring_metrics = {
        "all_mirror": ri_all["mirror"],
        "all_shift": ri_all["shift"],
        "all_perm_null": ri_all["perm_null"],
        "all_inclusio": ri_all["inclusio"],
        "all_middle": ri_all["middle"],
        "odd_inclusio": ri_odd["inclusio"],
        "odd_middle": ri_odd["middle"],
        "even_inclusio": ri_even["inclusio"],
        "even_middle": ri_even["middle"],
        "odd_strip10_inclusio": ri_odd_s10["inclusio"],
        "odd_strip10_middle": ri_odd_s10["middle"],
        "even_strip10_inclusio": ri_even_s10["inclusio"],
        "even_strip10_middle": ri_even_s10["middle"],
        "kalila_arb_inclusio": ri_kalila_arb["inclusio"],
        "kalila_arb_middle": ri_kalila_arb["middle"],
        "kalila_nat_inclusio": ri_kalila_nat["inclusio"],
        "kalila_nat_middle": ri_kalila_nat["middle"],
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
        "pinned_sha256s": verified_hashes,
        "unique_roots": morph_data["unique_roots"],
        "unique_lemmas": morph_data["unique_lemmas"],
        "unique_root_wazn_cells": morph_data["unique_root_wazn_cells"],
        "total_root_tokens": morph_data["total_root_tokens"],
        "verb_form_counts": morph_data["verb_form_counts"],
        "window_metrics": window_metrics,
        "control_w20_pairs": control_w20_pairs,
        "ring_metrics": ring_metrics,
        "root_records": root_records,
        "bg_sahih_pair": [bg_s_lost, bg_pair_count],
        "bg_pickthall_pair": [bg_p_lost, bg_pair_count],
    }


def certify_from_measurements(mode, measurements):
    p1 = audit_root_pattern_lattice_and_cohesion_exact(
        unique_roots=measurements["unique_roots"],
        unique_lemmas=measurements["unique_lemmas"],
        unique_root_wazn_cells=measurements["unique_root_wazn_cells"],
        total_root_tokens=measurements["total_root_tokens"],
        verb_form_counts=measurements["verb_form_counts"],
        window_metrics=measurements["window_metrics"],
        control_w20_pairs=measurements["control_w20_pairs"],
    )
    p2 = audit_ring_vs_inclusio_transform_exact(measurements["ring_metrics"])
    p3 = audit_translation_remainder_exact(
        root_records=measurements["root_records"],
        bg_sahih_pair=measurements["bg_sahih_pair"],
        bg_pickthall_pair=measurements["bg_pickthall_pair"],
    )
    five_axes = {
        "diacritics_vs_rasm": p1["monotonic_ladder_all_w"],
        "window_size_10_20_40": p1["root_beats_nulls_all_w"],
        "root_vs_stem": p1["monotonic_ladder_all_w"] and p1["lattice_nontrivial"],
        "odd_vs_even_unseen": (
            p1["split_halves_beat_t4b_all_w"]
            and p2["inclusio_holds_train_and_unseen"]
            and p2["strip10_inclusio_holds_train_and_unseen"]
        ),
        "second_instrument_and_controls": (
            p1["shared_classical_prose_property"]
            and p1["prose_exceeds_poetry_baseline"]
            and p2["arbitrary_prose_reverses_to_decay"]
            and p3["passed"]
        ),
    }
    return certify_arabic_own_terms_5axis_gate(
        mode=mode,
        pinned_sha256s=measurements["pinned_sha256s"],
        feature_names=AUDIT_FEATURES,
        pillar1_result=p1,
        pillar2_result=p2,
        pillar3_result=p3,
        five_axis_checks=five_axes,
    )


def default_corpus_dir():
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "repos", "arabic"))


def run_audit(standalone=False, corpus_dir=None):
    if standalone:
        return certify_from_measurements("standalone", STANDALONE_FIXTURE)
    target_dir = default_corpus_dir() if corpus_dir is None else corpus_dir
    measurements = compute_live_measurements(target_dir)
    return certify_from_measurements("live_readonly", measurements)


def main(argv=None):
    parser = argparse.ArgumentParser(description="AUDIT-091 Classical Arabic continuum audit")
    parser.add_argument("--standalone", action="store_true", help="Run using pinned standalone fixture")
    parser.add_argument("--corpus-dir", default=None, help="Path to read-only staged Arabic corpora")
    parser.add_argument("--output", default=None, help="Optional path to write canonical JSON certificate")
    args = parser.parse_args(argv)

    cert = run_audit(standalone=args.standalone, corpus_dir=args.corpus_dir)
    raw_bytes = canonical_json_bytes(cert)
    if args.output:
        with open(args.output, "wb") as f:
            f.write(raw_bytes)
            f.write(b"\n")
    sys.stdout.write(raw_bytes.decode("utf-8") + "\n")
    return 0 if cert["all_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
