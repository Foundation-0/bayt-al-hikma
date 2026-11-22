"""Dual-mode (live_readonly + --standalone) audit runner for Wave 3b Lane B (AUDIT-094):
Classical Arabic Lexical Semantic-Field Topology & Multi-Translator Continuum
Projection Defect across 9 SHA-256-pinned primary corpora.

Pure Python 3 stdlib. Zero floats on trust paths. Zero bare assert statements.
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

from arabic_lexicon_oracle import (
    LexiconOracleError,
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
    "root_wazn_forms_i_to_x_agency_reciprocity_matrix",
    "pure_q_renyi2_collision_concentration_tier4a_tier4b",
    "openiti_classical_prose_and_poetry_renyi2_controls",
    "arabic_top10_stripped_context_neighborhood_topology",
    "split_half_odd_train_even_unseen_context_invariance",
    "two_instrument_sahih_pickthall_same_vs_cross_lemma_defect",
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

SEED_WAZN_T4A = 20260941
SEED_WAZN_T4B = 20260942
SEED_CTRL_R2_T4A = 20260943
SEED_CTX_NULL = 20260944
SEED_WAZN_ODD_T4B = 20260945
SEED_WAZN_EVEN_T4B = 20260946
SEED_BG_PAIRS = 2026097
BG_PAIR_COUNT = 1000
CTRL_WINDOW = 20


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


def freq_stratified_wazn_shuffle(verb_pairs, seed):
    r_col = [p[0] for p in verb_pairs]
    vf_col = [p[1] for p in verb_pairs]
    r_freq = Counter(r_col)
    bins = [
        "B1" if r_freq[r] <= 2 else ("B2" if r_freq[r] <= 10 else ("B3" if r_freq[r] <= 50 else "B4"))
        for r in r_col
    ]
    shuf_vf = stratified_shuffle_exact(vf_col, bins, seed)
    return list(zip(r_col, shuf_vf))


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
):
    verified_hashes = verify_corpus_hashes(corpus_dir, expected_hashes=expected_hashes)

    md = parse_leeds_lexicon_lines(
        _read_lines(os.path.join(corpus_dir, "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt"))
    )
    uthmani = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-quran-uthmani.txt")))
    sahih = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-en.sahih.txt")))
    pick = parse_tanzil_lines(_read_lines(os.path.join(corpus_dir, "tanzil-en.pickthall.txt")))

    # Pillar 1: 1,642-root x Wazn (I..X) matrix & within-root Renyi-2
    verb_roots_sorted = sorted(md["root_vf"].keys())
    poly_wazn_roots = sum(1 for r in verb_roots_sorted if len(md["root_vf"][r]) >= 2)
    op_class_counts = Counter()
    for _, vf in md["verb_pairs_all"]:
        op_class_counts[OP_CLASS_MAP[vf]] += 1
    transition_pair_counts = {
        f"{a}+{b}": sum(1 for r in verb_roots_sorted if a in md["root_vf"][r] and b in md["root_vf"][r])
        for a, b in TRANSITION_PAIRS
    }

    r_col = [p[0] for p in md["verb_pairs_all"]]
    vf_t4a = det_shuffle_exact([p[1] for p in md["verb_pairs_all"]], SEED_WAZN_T4A)
    within_root_renyi2_pairs = {
        "all_obs": within_root_renyi2_pair(md["verb_pairs_all"]),
        "all_t4a": within_root_renyi2_pair(list(zip(r_col, vf_t4a))),
        "all_t4b": within_root_renyi2_pair(freq_stratified_wazn_shuffle(md["verb_pairs_all"], SEED_WAZN_T4B)),
        "odd_obs": within_root_renyi2_pair(md["verb_pairs_odd"]),
        "odd_t4b": within_root_renyi2_pair(freq_stratified_wazn_shuffle(md["verb_pairs_odd"], SEED_WAZN_ODD_T4B)),
        "even_obs": within_root_renyi2_pair(md["verb_pairs_even"]),
        "even_t4b": within_root_renyi2_pair(freq_stratified_wazn_shuffle(md["verb_pairs_even"], SEED_WAZN_EVEN_T4B)),
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
    for name, seq in (
        ("quran_stem", q_stems),
        ("kalila_prose", kalila_stems),
        ("adab_prose", adab_stems),
        ("poetry_pooled", poetry_stems),
    ):
        g_pair = list(renyi2_concentration_pair(dict(Counter(seq)))[:2])
        o_pair = list(block_renyi2_cross_pair(seq, ctrl_window)[:2])
        n_pair = list(block_renyi2_cross_pair(det_shuffle_exact(seq, SEED_CTRL_R2_T4A), ctrl_window)[:2])
        control_renyi2_metrics[name] = {
            "global_c2": g_pair,
            "w20_obs": o_pair,
            "w20_t4a": n_pair,
        }

    # Pillar 2: Top-10-stripped Arabic co-occurrence context topology
    target_set = frozenset(TARGET_ROOTS)
    all_vkeys = sorted(md["verse_roots"].keys())
    flat_roots = []
    v_lens = []
    for k in all_vkeys:
        rs = sorted(md["verse_roots"][k])
        v_lens.append(len(rs))
        flat_roots.extend(rs)
    shuf_roots = det_shuffle_exact(flat_roots, SEED_CTX_NULL)
    null_verses = {}
    pos = 0
    for k, ln in zip(all_vkeys, v_lens):
        null_verses[k] = set(shuf_roots[pos:pos + ln])
        pos += ln

    top10 = md["top10_roots"]
    ctx_all = build_context_counters(md["verse_roots"], target_set, top10)
    ctx_null = build_context_counters(null_verses, target_set, top10)
    ctx_odd = build_context_counters(md["verse_roots"], target_set, top10, "odd")
    ctx_odd_null = build_context_counters(null_verses, target_set, top10, "odd")
    ctx_even = build_context_counters(md["verse_roots"], target_set, top10, "even")
    ctx_even_null = build_context_counters(null_verses, target_set, top10, "even")

    multi_targets = frozenset(r for r in TARGET_ROOTS if len(md["root_verses"][r]) >= min_multi_verses)
    context_metrics = {
        "ctx_r2_all": pooled_context_renyi2_pair(ctx_all),
        "ctx_r2_null": pooled_context_renyi2_pair(ctx_null),
        "ctx_r2_odd": pooled_context_renyi2_pair(ctx_odd),
        "ctx_r2_odd_null": pooled_context_renyi2_pair(ctx_odd_null),
        "ctx_r2_even": pooled_context_renyi2_pair(ctx_even),
        "ctx_r2_even_null": pooled_context_renyi2_pair(ctx_even_null),
        "ctx_jaccard_all": pooled_weighted_context_jaccard_pair(ctx_all, multi_targets),
        "ctx_jaccard_null": pooled_weighted_context_jaccard_pair(ctx_null, multi_targets),
        "ctx_jaccard_odd": pooled_weighted_context_jaccard_pair(ctx_odd, multi_targets),
        "ctx_jaccard_odd_null": pooled_weighted_context_jaccard_pair(ctx_odd_null, multi_targets),
        "ctx_jaccard_even": pooled_weighted_context_jaccard_pair(ctx_even, multi_targets),
        "ctx_jaccard_even_null": pooled_weighted_context_jaccard_pair(ctx_even_null, multi_targets),
        "cooccur_all": target_cooccur_pair(md["verse_roots"], target_set),
        "cooccur_null": target_cooccur_pair(null_verses, target_set),
        "cooccur_odd": target_cooccur_pair(md["verse_roots"], target_set, "odd"),
        "cooccur_odd_null": target_cooccur_pair(null_verses, target_set, "odd"),
        "cooccur_even": target_cooccur_pair(md["verse_roots"], target_set, "even"),
        "cooccur_even_null": target_cooccur_pair(null_verses, target_set, "even"),
    }

    # Pillar 3: 2-instrument Sahih vs Pickthall Same-Lemma vs Cross-Lemma projection defect
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
        same_p = cross_p = 0
        s_same_l = s_cross_l = p_same_l = p_cross_l = 0
        for i in range(n):
            k1 = vs[i]
            for j in range(i + 1, n):
                k2 = vs[j]
                s_zero = not (sahih_stems[k1] & sahih_stems[k2])
                p_zero = not (pick_stems[k1] & pick_stems[k2])
                if md["verse_root_lems"][k1][root] & md["verse_root_lems"][k2][root]:
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

    return {
        "pinned_sha256s": verified_hashes,
        "total_unique_roots": md["total_unique_roots"],
        "verb_roots": len(verb_roots_sorted),
        "poly_wazn_roots": poly_wazn_roots,
        "verb_tokens_i_x": len(md["verb_pairs_all"]),
        "form_xii_tokens": md["form_xii_tokens"],
        "op_class_counts": dict(op_class_counts),
        "transition_pair_counts": transition_pair_counts,
        "within_root_renyi2_pairs": within_root_renyi2_pairs,
        "control_renyi2_metrics": control_renyi2_metrics,
        "context_metrics": context_metrics,
        "root_records": root_records,
        "bg_sahih_pair": [bg_s_lost, bg_pair_count],
        "bg_pickthall_pair": [bg_p_lost, bg_pair_count],
    }


STANDALONE_FIXTURE = {
    "pinned_sha256s": dict(EXPECTED_CORPUS_SHA256),
    "total_unique_roots": 1642,
    "verb_roots": 942,
    "poly_wazn_roots": 349,
    "verb_tokens_i_x": 19347,
    "form_xii_tokens": 9,
    "op_class_counts": {
        "GROUND_I": 12347,
        "STAT_ESTIM_IX_X": 374,
        "CAUS_INTENS_II_III_IV": 5121,
        "REFL_RECIP_V_VI_VII_VIII": 1505,
    },
    "transition_pair_counts": {
        "I+IV": 146,
        "I+II": 87,
        "II+V": 40,
        "III+VI": 12,
        "I+VIII": 67,
        "I+X": 42,
        "IV+X": 41,
    },
    "within_root_renyi2_pairs": {
        "all_obs": [6190677, 6678331],
        "all_t4a": [3053107, 6678331],
        "all_t4b": [3389501, 6678331],
        "odd_obs": [1373154, 1474950],
        "odd_t4b": [798528, 1474950],
        "even_obs": [1747029, 1891145],
        "even_t4b": [1039849, 1891145],
    },
    "control_renyi2_metrics": {
        "quran_stem": {
            "global_c2": [32595109, 6065450161],
            "w20_obs": [14108, 1557200],
            "w20_t4a": [8350, 1557200],
        },
        "kalila_prose": {
            "global_c2": [9431822, 1943928100],
            "w20_obs": [7708, 881200],
            "w20_t4a": [4255, 881200],
        },
        "adab_prose": {
            "global_c2": [577088, 91891396],
            "w20_obs": [1888, 191200],
            "w20_t4a": [1189, 191200],
        },
        "poetry_pooled": {
            "global_c2": [219899, 105042001],
            "w20_obs": [658, 204400],
            "w20_t4a": [432, 204400],
        },
    },
    "context_metrics": {
        "ctx_r2_all": [101506, 14920444],
        "ctx_r2_null": [56862, 13660274],
        "ctx_r2_odd": [25931, 3454687],
        "ctx_r2_odd_null": [15173, 3088243],
        "ctx_r2_even": [29831, 4085025],
        "ctx_r2_even_null": [18215, 3836317],
        "ctx_jaccard_all": [17298, 94759],
        "ctx_jaccard_null": [19908, 88255],
        "ctx_jaccard_odd": [7251, 46429],
        "ctx_jaccard_odd_null": [7834, 43041],
        "ctx_jaccard_even": [8124, 50253],
        "ctx_jaccard_even_null": [9327, 47961],
        "cooccur_all": [173, 1161],
        "cooccur_null": [137, 1172],
        "cooccur_odd": [85, 562],
        "cooccur_odd_null": [71, 574],
        "cooccur_even": [88, 599],
        "cooccur_even_null": [66, 598],
    },
    "root_records": [
        {
            "root": "ftq", "occurrences": 1, "verse_count": 1, "unique_lemmas": 1,
            "sahih_top_count": 1, "pickthall_top_count": 1,
            "same_lemma_pairs": 0, "cross_lemma_pairs": 0,
            "sahih_same_lost": 0, "sahih_cross_lost": 0,
            "pickthall_same_lost": 0, "pickthall_cross_lost": 0,
            "sahih_lost_pairs": 0, "pickthall_lost_pairs": 0,
        },
        {
            "root": "rtq", "occurrences": 1, "verse_count": 1, "unique_lemmas": 1,
            "sahih_top_count": 1, "pickthall_top_count": 1,
            "same_lemma_pairs": 0, "cross_lemma_pairs": 0,
            "sahih_same_lost": 0, "sahih_cross_lost": 0,
            "pickthall_same_lost": 0, "pickthall_cross_lost": 0,
            "sahih_lost_pairs": 0, "pickthall_lost_pairs": 0,
        },
        {
            "root": "sbH", "occurrences": 92, "verse_count": 87, "unique_lemmas": 7,
            "sahih_top_count": 82, "pickthall_top_count": 28,
            "same_lemma_pairs": 1603, "cross_lemma_pairs": 2138,
            "sahih_same_lost": 17, "sahih_cross_lost": 340,
            "pickthall_same_lost": 682, "pickthall_cross_lost": 1816,
            "sahih_lost_pairs": 357, "pickthall_lost_pairs": 2498,
        },
        {
            "root": "flk", "occurrences": 25, "verse_count": 25, "unique_lemmas": 2,
            "sahih_top_count": 23, "pickthall_top_count": 23,
            "same_lemma_pairs": 254, "cross_lemma_pairs": 46,
            "sahih_same_lost": 0, "sahih_cross_lost": 39,
            "pickthall_same_lost": 0, "pickthall_cross_lost": 42,
            "sahih_lost_pairs": 39, "pickthall_lost_pairs": 42,
        },
        {
            "root": "kwr", "occurrences": 3, "verse_count": 2, "unique_lemmas": 1,
            "sahih_top_count": 2, "pickthall_top_count": 1,
            "same_lemma_pairs": 1, "cross_lemma_pairs": 0,
            "sahih_same_lost": 0, "sahih_cross_lost": 0,
            "pickthall_same_lost": 1, "pickthall_cross_lost": 0,
            "sahih_lost_pairs": 0, "pickthall_lost_pairs": 1,
        },
        {
            "root": "wsE", "occurrences": 32, "verse_count": 29, "unique_lemmas": 6,
            "sahih_top_count": 12, "pickthall_top_count": 8,
            "same_lemma_pairs": 77, "cross_lemma_pairs": 329,
            "sahih_same_lost": 13, "sahih_cross_lost": 205,
            "pickthall_same_lost": 19, "pickthall_cross_lost": 239,
            "sahih_lost_pairs": 218, "pickthall_lost_pairs": 258,
        },
        {
            "root": "mdd", "occurrences": 32, "verse_count": 29, "unique_lemmas": 9,
            "sahih_top_count": 11, "pickthall_top_count": 7,
            "same_lemma_pairs": 124, "cross_lemma_pairs": 282,
            "sahih_same_lost": 78, "sahih_cross_lost": 226,
            "pickthall_same_lost": 85, "pickthall_cross_lost": 251,
            "sahih_lost_pairs": 304, "pickthall_lost_pairs": 336,
        },
        {
            "root": "qdr", "occurrences": 132, "verse_count": 121, "unique_lemmas": 11,
            "sahih_top_count": 46, "pickthall_top_count": 49,
            "same_lemma_pairs": 1582, "cross_lemma_pairs": 5678,
            "sahih_same_lost": 338, "sahih_cross_lost": 4454,
            "pickthall_same_lost": 619, "pickthall_cross_lost": 4320,
            "sahih_lost_pairs": 4792, "pickthall_lost_pairs": 4939,
        },
        {
            "root": "zwj", "occurrences": 81, "verse_count": 72, "unique_lemmas": 2,
            "sahih_top_count": 22, "pickthall_top_count": 29,
            "same_lemma_pairs": 2288, "cross_lemma_pairs": 268,
            "sahih_same_lost": 1526, "sahih_cross_lost": 232,
            "pickthall_same_lost": 1351, "pickthall_cross_lost": 240,
            "sahih_lost_pairs": 1758, "pickthall_lost_pairs": 1591,
        },
        {
            "root": "Erj", "occurrences": 9, "verse_count": 9, "unique_lemmas": 3,
            "sahih_top_count": 5, "pickthall_top_count": 4,
            "same_lemma_pairs": 12, "cross_lemma_pairs": 24,
            "sahih_same_lost": 1, "sahih_cross_lost": 21,
            "pickthall_same_lost": 4, "pickthall_cross_lost": 18,
            "sahih_lost_pairs": 22, "pickthall_lost_pairs": 22,
        },
        {
            "root": "nzl", "occurrences": 293, "verse_count": 257, "unique_lemmas": 12,
            "sahih_top_count": 152, "pickthall_top_count": 124,
            "same_lemma_pairs": 15036, "cross_lemma_pairs": 17860,
            "sahih_same_lost": 4636, "sahih_cross_lost": 10240,
            "pickthall_same_lost": 6314, "pickthall_cross_lost": 11086,
            "sahih_lost_pairs": 14876, "pickthall_lost_pairs": 17400,
        },
        {
            "root": "xlq", "occurrences": 261, "verse_count": 218, "unique_lemmas": 8,
            "sahih_top_count": 150, "pickthall_top_count": 140,
            "same_lemma_pairs": 15065, "cross_lemma_pairs": 8588,
            "sahih_same_lost": 2288, "sahih_cross_lost": 6913,
            "pickthall_same_lost": 4393, "pickthall_cross_lost": 6685,
            "sahih_lost_pairs": 9201, "pickthall_lost_pairs": 11078,
        },
        {
            "root": "Amr", "occurrences": 248, "verse_count": 226, "unique_lemmas": 6,
            "sahih_top_count": 83, "pickthall_top_count": 62,
            "same_lemma_pairs": 14111, "cross_lemma_pairs": 11314,
            "sahih_same_lost": 8394, "sahih_cross_lost": 7848,
            "pickthall_same_lost": 10342, "pickthall_cross_lost": 8741,
            "sahih_lost_pairs": 16242, "pickthall_lost_pairs": 19083,
        },
        {
            "root": "Hqq", "occurrences": 287, "verse_count": 263, "unique_lemmas": 7,
            "sahih_top_count": 175, "pickthall_top_count": 157,
            "same_lemma_pairs": 26803, "cross_lemma_pairs": 7650,
            "sahih_same_lost": 9162, "sahih_cross_lost": 6271,
            "pickthall_same_lost": 11544, "pickthall_cross_lost": 6285,
            "sahih_lost_pairs": 15433, "pickthall_lost_pairs": 17829,
        },
        {
            "root": "wzn", "occurrences": 23, "verse_count": 21, "unique_lemmas": 4,
            "sahih_top_count": 7, "pickthall_top_count": 10,
            "same_lemma_pairs": 125, "cross_lemma_pairs": 85,
            "sahih_same_lost": 67, "sahih_cross_lost": 53,
            "pickthall_same_lost": 69, "pickthall_cross_lost": 50,
            "sahih_lost_pairs": 120, "pickthall_lost_pairs": 119,
        },
    ],
    "bg_sahih_pair": [897, 1000],
    "bg_pickthall_pair": [923, 1000],
}


def certify_from_measurements(mode, measurements):
    p1 = audit_wazn_agency_matrix_and_renyi2_exact(
        total_unique_roots=measurements["total_unique_roots"],
        verb_roots=measurements["verb_roots"],
        poly_wazn_roots=measurements["poly_wazn_roots"],
        verb_tokens_i_x=measurements["verb_tokens_i_x"],
        form_xii_tokens=measurements["form_xii_tokens"],
        op_class_counts=measurements["op_class_counts"],
        transition_pair_counts=measurements["transition_pair_counts"],
        within_root_renyi2_pairs=measurements["within_root_renyi2_pairs"],
        control_renyi2_metrics=measurements["control_renyi2_metrics"],
    )
    p2 = audit_context_neighborhood_topology_exact(measurements["context_metrics"])
    p3 = audit_two_layer_projection_defect_exact(
        root_records=measurements["root_records"],
        bg_sahih_pair=measurements["bg_sahih_pair"],
        bg_pickthall_pair=measurements["bg_pickthall_pair"],
    )
    five_axes = {
        "wazn_agency_and_renyi2": p1["agency_matrix_nontrivial"] and p1["within_root_wazn_beats_nulls"],
        "openiti_negative_controls": p1["shared_prose_renyi2_lift"] and p1["poetry_higher_effective_diversity"],
        "arabic_context_topology_split_half": (
            p2["ctx_r2_specialized_train_and_unseen"]
            and p2["distinct_neighborhoods_vs_background"]
            and p2["direct_coupling_enriched_train_and_unseen"]
        ),
        "two_layer_same_vs_cross_lemma": (
            p3["intra_lemma_polysemy_nonzero"] and p3["unanimous_cross_lemma_amplification"]
        ),
        "two_translator_agreement": (
            p3["discrete_bucket_falsified"] and p3["unanimous_cross_lemma_amplification"]
        ),
    }
    return certify_arabic_lexicon_own_terms_gate(
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
    parser = argparse.ArgumentParser(description="AUDIT-094 Classical Arabic lexical topology audit")
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
