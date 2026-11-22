"""Exact pure-Q oracle for Wave 3 Lane 5 (AUDIT-091):
Classical Arabic / Qur'anic layered continuum semantics, non-concatenative
root-pattern (C1-C2-C3 x wazn) geometry, Law 2b ring-vs-inclusio
transformational steelman, 2-instrument continuum-to-discrete translation
remainder, and OWN_TERMS_FIRST 5-axis net-invariance.

Governance invariants:
- Pure Python 3 standard library only; zero floats anywhere on trust paths.
- Zero bare assert statements; fail closed with typed ArabicOracleError.
- Strict Law 5 Anti-Numerology Guard (zero abjad/gematria/digit-count features).
"""

from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import re
import unicodedata


SCHEMA_VERSION = "arabic-continuum-oracle/v1"
CANONICAL_DECIMALS = 6

FORBIDDEN_NUMEROLOGY_TOKENS = (
    "abjad",
    "gematria",
    "digitsum",
    "base10",
    "miracle",
    "code19",
    "numerology",
)

HEX64_RE = re.compile(r"[0-9a-f]{64}")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]")
AR_LETTER_RE = re.compile(r"[\u0621-\u063a\u0641-\u064a]")
DIAC_STRIP_RE = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
EN_WORD_RE = re.compile(r"[a-z]+")

AR_PREFIXES = (
    "\u0648\u0627\u0644",
    "\u0641\u0627\u0644",
    "\u0628\u0627\u0644",
    "\u0643\u0627\u0644",
    "\u0644\u0644",
    "\u0627\u0644",
    "\u0648\u0628",
    "\u0641\u0628",
    "\u0648\u0644",
    "\u0641\u0644",
    "\u0648",
    "\u0641",
    "\u0628",
    "\u0643",
    "\u0644",
)
AR_SUFFIXES = (
    "\u0647\u0645\u0627",
    "\u0647\u0645",
    "\u0647\u0646",
    "\u0643\u0645",
    "\u0643\u0646",
    "\u0646\u0627",
    "\u0647\u0627",
    "\u0648\u0646",
    "\u064a\u0646",
    "\u0627\u0646",
    "\u0627\u062a",
    "\u0648\u0627",
    "\u062a\u0645",
    "\u062a\u0646",
    "\u0646\u064a",
    "\u0647",
    "\u0643",
    "\u064a",
    "\u062a",
)

EN_STOPWORDS = frozenset({
    "that", "this", "with", "from", "have", "were", "they", "them", "their",
    "then", "than", "when", "what", "which", "will", "would", "there", "been",
    "into", "upon", "unto", "over", "only", "also", "more", "most", "some",
    "such", "your", "ours", "shall", "should", "could", "those", "these",
    "being", "about", "after", "before", "against", "between", "through",
    "during", "without", "because", "while", "where", "whom", "whose",
    "indeed", "verily", "surely", "said", "says", "does", "done", "made",
    "make", "come", "came", "give", "gave", "take", "took", "know", "knew",
    "himself", "themselves", "ourselves", "yourselves", "thee", "thou",
    "hath", "doth", "shalt", "hast", "wilt", "therein", "thereof", "thereto",
    "thereon", "whereas", "wherein", "whereof", "allah", "lord", "except",
})


class ArabicOracleError(ValueError):
    """Typed fail-closed error carrying a stable machine-readable code."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


def verify_no_floats(obj, path="root"):
    """Recursively reject float and complex values anywhere in a structure."""
    if isinstance(obj, (float, complex)):
        raise ArabicOracleError("FLOAT_FORBIDDEN", f"float/complex at {path}")
    if isinstance(obj, dict):
        for k, v in obj.items():
            verify_no_floats(k, f"{path}.<key>")
            verify_no_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for idx, item in enumerate(obj):
            verify_no_floats(item, f"{path}[{idx}]")


def require_non_empty_str(val, field):
    if not isinstance(val, str):
        raise ArabicOracleError("INVALID_TYPE", f"{field} must be str")
    for ch in val:
        code = ord(ch)
        if code < 32 or code == 127 or unicodedata.category(ch) == "Cf":
            raise ArabicOracleError("CONTROL_CHAR", f"{field} contains control or format char")
    stripped = val.strip()
    if not stripped:
        raise ArabicOracleError("EMPTY_STRING", f"{field} must be non-empty")
    return stripped


def require_exact_bool(val, field):
    if not isinstance(val, bool):
        raise ArabicOracleError("INVALID_BOOL", f"{field} must be bool")
    return val


def require_exact_int(val, field, min_value=None, max_value=None):
    if isinstance(val, bool) or not isinstance(val, int):
        raise ArabicOracleError("INVALID_INT", f"{field} must be int")
    if min_value is not None and val < min_value:
        raise ArabicOracleError("RANGE_ERROR", f"{field} < {min_value}")
    if max_value is not None and val > max_value:
        raise ArabicOracleError("RANGE_ERROR", f"{field} > {max_value}")
    return val


def require_exact_fraction(val, field, min_value=None, max_value=None):
    if isinstance(val, bool):
        raise ArabicOracleError("INVALID_FRACTION", f"{field} must not be bool")
    if isinstance(val, int):
        out = Fraction(val, 1)
    elif isinstance(val, Fraction):
        out = val
    else:
        raise ArabicOracleError("INVALID_FRACTION", f"{field} must be Fraction or int")
    if min_value is not None and out < min_value:
        raise ArabicOracleError("RANGE_ERROR", f"{field} < {min_value}")
    if max_value is not None and out > max_value:
        raise ArabicOracleError("RANGE_ERROR", f"{field} > {max_value}")
    return out


def require_pair_ratio(pair, field):
    """Validate an exact (inter, union) integer pair with 0 <= inter <= union and union > 0."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise ArabicOracleError("INVALID_PAIR", f"{field} must be a 2-tuple of ints")
    inter = require_exact_int(pair[0], f"{field}[0]", min_value=0)
    union = require_exact_int(pair[1], f"{field}[1]", min_value=1)
    if inter > union:
        raise ArabicOracleError("INVALID_PAIR", f"{field} inter > union")
    return inter, union, Fraction(inter, union)


def frac_str(val):
    f = require_exact_fraction(val, "frac")
    return f"{f.numerator}/{f.denominator}"


def format_exact_decimal(val, places=CANONICAL_DECIMALS):
    """Pure-integer half-up decimal formatting of a Fraction."""
    f = require_exact_fraction(val, "decimal_val")
    p = require_exact_int(places, "places", min_value=0, max_value=12)
    neg = f < 0
    mag = -f if neg else f
    scale = 10 ** p
    scaled_num = mag.numerator * scale
    den = mag.denominator
    quot, rem = divmod(scaled_num, den)
    if rem * 2 >= den:
        quot += 1
    prefix = "-" if (neg and quot > 0) else ""
    if p == 0:
        return f"{prefix}{quot}"
    whole, frac_part = divmod(quot, scale)
    return f"{prefix}{whole}.{frac_part:0{p}d}"


def canonical_json_bytes(payload):
    verify_no_floats(payload, "canonical_json")
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def canonical_sha256(payload):
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def fnv1a_32(text):
    """Deterministic 32-bit FNV-1a hash over UTF-8 bytes."""
    s = require_non_empty_str(text, "fnv1a_32.text")
    h = 2166136261
    for b in s.encode("utf-8"):
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return h


def det_shuffle_exact(items, seed):
    """Pure-integer deterministic Fisher-Yates shuffle via 64-bit LCG."""
    if not isinstance(items, (list, tuple)):
        raise ArabicOracleError("INVALID_SEQ", "items must be list or tuple")
    x = require_exact_int(seed, "seed", min_value=0) & 0xFFFFFFFFFFFFFFFF
    arr = list(items)
    for i in range(len(arr) - 1, 0, -1):
        x = (6364136223846793005 * x + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        j = (x >> 33) % (i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def stratified_shuffle_exact(items, classes, seed):
    """Tier-4B class-preserving deterministic shuffle (exact POS or length strata)."""
    if not isinstance(items, (list, tuple)) or not isinstance(classes, (list, tuple)):
        raise ArabicOracleError("INVALID_SEQ", "items and classes must be list or tuple")
    if len(items) != len(classes):
        raise ArabicOracleError("LENGTH_MISMATCH", "items and classes lengths differ")
    s_int = require_exact_int(seed, "seed", min_value=0)
    buckets = defaultdict(list)
    for idx, cls in enumerate(classes):
        buckets[require_non_empty_str(cls, f"classes[{idx}]")].append(idx)
    out = list(items)
    for cls in sorted(buckets.keys()):
        idxs = buckets[cls]
        vals = [items[i] for i in idxs]
        shuffled = det_shuffle_exact(vals, s_int ^ fnv1a_32(cls))
        for i, v in zip(idxs, shuffled):
            out[i] = v
    return out


def to_rasm(token):
    """Strip Arabic diacritics/tatweel and normalize hamza/alif/ta-marbuta."""
    if not isinstance(token, str):
        raise ArabicOracleError("INVALID_TYPE", "token must be str")
    w = DIAC_STRIP_RE.sub("", token)
    w = (
        w.replace("\u0671", "\u0627")
        .replace("\u0623", "\u0627")
        .replace("\u0625", "\u0627")
        .replace("\u0622", "\u0627")
        .replace("\u0649", "\u064a")
        .replace("\u0629", "\u0647")
    )
    return "".join(AR_LETTER_RE.findall(w))


def light_stem_ar(token):
    """Deterministic concatenative Arabic light stemmer preserving >= 3-letter core."""
    r = to_rasm(token)
    if len(r) <= 3:
        return r
    for pref in AR_PREFIXES:
        if r.startswith(pref) and len(r) - len(pref) >= 3:
            r = r[len(pref):]
            break
    for suff in AR_SUFFIXES:
        if r.endswith(suff) and len(r) - len(suff) >= 3:
            r = r[:-len(suff)]
            break
    return r


def en_content_stems(text):
    """Deterministic English content-word stem set for translation-remainder audit."""
    if not isinstance(text, str):
        raise ArabicOracleError("INVALID_TYPE", "text must be str")
    out = set()
    for w in EN_WORD_RE.findall(text.lower()):
        if len(w) < 4 or w in EN_STOPWORDS:
            continue
        if len(w) >= 7 and w.endswith("ing"):
            w = w[:-3]
            if w[-1] == w[-2]:
                w = w[:-1]
        elif len(w) >= 6 and w.endswith("ed"):
            w = w[:-2]
            if w[-1] == w[-2]:
                w = w[:-1]
        elif len(w) >= 6 and w.endswith("es"):
            w = w[:-2]
        elif len(w) >= 5 and w.endswith("s"):
            w = w[:-1]
        if len(w) >= 4 and w not in EN_STOPWORDS:
            out.add(w)
    return out


def block_jaccard_cohesion_exact(seq, window_size):
    """Exact pooled Jaccard overlap between adjacent non-overlapping windows."""
    if not isinstance(seq, (list, tuple)):
        raise ArabicOracleError("INVALID_SEQ", "seq must be list or tuple")
    w = require_exact_int(window_size, "window_size", min_value=2)
    n_blocks = len(seq) // w
    if n_blocks < 2:
        raise ArabicOracleError("INSUFFICIENT_BLOCKS", "need at least 2 full windows")
    inter_sum = 0
    union_sum = 0
    for i in range(n_blocks - 1):
        a = set(seq[i * w:(i + 1) * w])
        b = set(seq[(i + 1) * w:(i + 2) * w])
        inter_sum += len(a & b)
        union_sum += len(a | b)
    return inter_sum, union_sum, Fraction(inter_sum, union_sum)


def enforce_zero_numerology_policy(feature_names):
    """Strict Law 5 guard: reject any abjad/gematria/digit-count/miracle feature."""
    verify_no_floats(feature_names, "feature_names")
    if not isinstance(feature_names, (list, tuple)) or len(feature_names) == 0:
        raise ArabicOracleError("INVALID_FEATURES", "feature_names must be non-empty sequence")
    seen_compact = set()
    normalized = []
    for idx, raw in enumerate(feature_names):
        name = require_non_empty_str(raw, f"feature_names[{idx}]").lower()
        compact = NON_ALNUM_RE.sub("", name)
        if not compact:
            raise ArabicOracleError("EMPTY_STRING", f"feature_names[{idx}] has no alnum chars")
        if compact in seen_compact:
            raise ArabicOracleError("DUPLICATE_FEATURE", f"duplicate feature {name}")
        for bad in FORBIDDEN_NUMEROLOGY_TOKENS:
            if bad in compact:
                raise ArabicOracleError("NUMEROLOGY_FORBIDDEN", f"forbidden feature {name}")
        seen_compact.add(compact)
        normalized.append(name)
    return {"zero_numerology_ok": True, "feature_count": len(normalized), "features": normalized}


def audit_root_pattern_lattice_and_cohesion_exact(
    unique_roots,
    unique_lemmas,
    unique_root_wazn_cells,
    total_root_tokens,
    verb_form_counts,
    window_metrics,
    control_w20_pairs,
    min_null_margin=Fraction(1, 100),
):
    """Pillar 1: Non-concatenative root-pattern lattice + multi-window cohesion & controls."""
    verify_no_floats(
        {
            "unique_roots": unique_roots,
            "unique_lemmas": unique_lemmas,
            "unique_root_wazn_cells": unique_root_wazn_cells,
            "total_root_tokens": total_root_tokens,
            "verb_form_counts": verb_form_counts,
            "window_metrics": window_metrics,
            "control_w20_pairs": control_w20_pairs,
            "min_null_margin": min_null_margin,
        },
        "pillar1",
    )
    u_roots = require_exact_int(unique_roots, "unique_roots", min_value=1)
    u_lems = require_exact_int(unique_lemmas, "unique_lemmas", min_value=1)
    u_cells = require_exact_int(unique_root_wazn_cells, "unique_root_wazn_cells", min_value=1)
    tot_tok = require_exact_int(total_root_tokens, "total_root_tokens", min_value=1)
    margin = require_exact_fraction(min_null_margin, "min_null_margin", min_value=Fraction(0, 1))

    if not isinstance(verb_form_counts, dict) or len(verb_form_counts) == 0:
        raise ArabicOracleError("INVALID_VERB_FORMS", "verb_form_counts must be non-empty dict")
    clean_vf = {}
    vf_total = 0
    for k, v in verb_form_counts.items():
        fk = require_non_empty_str(k, "verb_form_key").upper()
        if fk in clean_vf:
            raise ArabicOracleError("DUPLICATE_VERB_FORM", f"duplicate verb form {fk}")
        fv = require_exact_int(v, f"verb_form_counts[{fk}]", min_value=1)
        clean_vf[fk] = fv
        vf_total += fv

    if (
        u_roots > tot_tok
        or u_lems > tot_tok
        or u_cells > tot_tok
        or vf_total > tot_tok
        or u_cells < u_roots
    ):
        raise ArabicOracleError("CONSERVATION_ERROR", "lattice counts violate token/root conservation")

    lemmas_per_root = Fraction(u_lems, u_roots)
    cells_per_root = Fraction(u_cells, u_roots)
    lattice_nontrivial = (
        lemmas_per_root > Fraction(2, 1)
        and cells_per_root > Fraction(2, 1)
        and len(clean_vf) >= 8
    )

    if not isinstance(window_metrics, dict) or len(window_metrics) < 3:
        raise ArabicOracleError("INVALID_WINDOWS", "window_metrics must have >= 3 scales")

    req_keys = (
        "raw",
        "rasm",
        "stem",
        "root",
        "root_t4a",
        "root_t4b",
        "odd_root",
        "odd_t4b",
        "even_root",
        "even_t4b",
    )
    win_report = {}
    monotonic_all = True
    root_beats_nulls_all = True
    split_halves_beat_t4b_all = True
    for w_key in sorted(window_metrics.keys()):
        w_int = require_exact_int(w_key, "window_key", min_value=2)
        entry = window_metrics[w_key]
        if not isinstance(entry, dict):
            raise ArabicOracleError("INVALID_WINDOW_ENTRY", f"window {w_int} must be dict")
        ratios = {}
        raw_pairs = {}
        for rk in req_keys:
            if rk not in entry:
                raise ArabicOracleError("MISSING_KEY", f"window {w_int} missing {rk}")
            inter, union, frac = require_pair_ratio(entry[rk], f"W{w_int}.{rk}")
            ratios[rk] = frac
            raw_pairs[rk] = [inter, union]
        mono = ratios["raw"] < ratios["rasm"] < ratios["stem"] < ratios["root"]
        beats_nulls = (
            ratios["root"] - abs(ratios["root_t4a"]) >= margin
            and ratios["root"] - abs(ratios["root_t4b"]) >= margin
        )
        split_ok = (
            ratios["odd_root"] - abs(ratios["odd_t4b"]) >= margin
            and ratios["even_root"] - abs(ratios["even_t4b"]) >= margin
        )
        if not mono:
            monotonic_all = False
        if not beats_nulls:
            root_beats_nulls_all = False
        if not split_ok:
            split_halves_beat_t4b_all = False
        win_report[str(w_int)] = {
            "pairs": raw_pairs,
            "ratios_exact": {k: frac_str(v) for k, v in ratios.items()},
            "ratios_dec6": {k: format_exact_decimal(v) for k, v in ratios.items()},
            "monotonic_ladder": mono,
            "root_beats_t4a_and_t4b": beats_nulls,
            "odd_and_even_beat_t4b": split_ok,
        }

    if not isinstance(control_w20_pairs, dict):
        raise ArabicOracleError("INVALID_CONTROLS", "control_w20_pairs must be dict")
    ctrl_names = ("quran_stem", "kalila_prose", "adab_prose", "poetry_pooled")
    ctrl_ratios = {}
    ctrl_report = {}
    for cn in ctrl_names:
        if cn not in control_w20_pairs or not isinstance(control_w20_pairs[cn], dict):
            raise ArabicOracleError("MISSING_CONTROL", f"missing control {cn}")
        cd = control_w20_pairs[cn]
        if "obs" not in cd or "t4a" not in cd:
            raise ArabicOracleError("MISSING_CONTROL_FIELD", f"{cn} needs obs and t4a")
        oi, ou, obs_r = require_pair_ratio(cd["obs"], f"{cn}.obs")
        ni, nu, null_r = require_pair_ratio(cd["t4a"], f"{cn}.t4a")
        if null_r == 0:
            raise ArabicOracleError("ZERO_NULL", f"{cn} null ratio is zero")
        lift = obs_r / null_r
        ctrl_ratios[cn] = (obs_r, null_r, lift)
        ctrl_report[cn] = {
            "obs_pair": [oi, ou],
            "t4a_pair": [ni, nu],
            "obs_exact": frac_str(obs_r),
            "obs_dec6": format_exact_decimal(obs_r),
            "t4a_exact": frac_str(null_r),
            "t4a_dec6": format_exact_decimal(null_r),
            "lift_exact": frac_str(lift),
            "lift_dec6": format_exact_decimal(lift),
        }

    if "20" in win_report and ctrl_report["quran_stem"]["obs_pair"] != win_report["20"]["pairs"]["stem"]:
        raise ArabicOracleError(
            "CONTROL_MISMATCH",
            "control_w20_pairs.quran_stem.obs must equal window_metrics[20].stem",
        )

    shared_classical_prose = (
        ctrl_ratios["kalila_prose"][0] - abs(ctrl_ratios["kalila_prose"][1]) >= margin
        and ctrl_ratios["adab_prose"][0] - abs(ctrl_ratios["adab_prose"][1]) >= margin
    )
    prose_exceeds_poetry = (
        ctrl_ratios["quran_stem"][0] > ctrl_ratios["poetry_pooled"][0]
        and ctrl_ratios["kalila_prose"][0] > ctrl_ratios["poetry_pooled"][0]
    )

    pillar1_passed = (
        lattice_nontrivial
        and monotonic_all
        and root_beats_nulls_all
        and split_halves_beat_t4b_all
        and shared_classical_prose
        and prose_exceeds_poetry
    )

    return {
        "unique_roots": u_roots,
        "unique_lemmas": u_lems,
        "unique_root_wazn_cells": u_cells,
        "total_root_tokens": tot_tok,
        "verb_form_counts": clean_vf,
        "verb_form_total": vf_total,
        "lemmas_per_root_exact": frac_str(lemmas_per_root),
        "lemmas_per_root_dec6": format_exact_decimal(lemmas_per_root),
        "cells_per_root_exact": frac_str(cells_per_root),
        "cells_per_root_dec6": format_exact_decimal(cells_per_root),
        "lattice_nontrivial": lattice_nontrivial,
        "window_metrics": win_report,
        "monotonic_ladder_all_w": monotonic_all,
        "root_beats_nulls_all_w": root_beats_nulls_all,
        "split_halves_beat_t4b_all_w": split_halves_beat_t4b_all,
        "negative_controls_w20": ctrl_report,
        "shared_classical_prose_property": shared_classical_prose,
        "prose_exceeds_poetry_baseline": prose_exceeds_poetry,
        "passed": pillar1_passed,
    }


def audit_ring_vs_inclusio_transform_exact(
    metrics,
    min_inclusio_margin=Fraction(1, 200),
):
    """Pillar 2 (Law 2b Transformational Steelman):
    Honest falsification of literal global pointwise ring symmetry paired with
    verified top-10-stripped boundary inclusio across train (odd) and unseen (even)
    surahs, contrasted against arbitrary vs framed prose negative controls.
    """
    verify_no_floats({"metrics": metrics, "min_inclusio_margin": min_inclusio_margin}, "pillar2")
    margin = require_exact_fraction(min_inclusio_margin, "min_inclusio_margin", min_value=Fraction(0, 1))
    if not isinstance(metrics, dict):
        raise ArabicOracleError("INVALID_METRICS", "metrics must be dict")

    req_pairs = (
        "all_mirror",
        "all_shift",
        "all_perm_null",
        "all_inclusio",
        "all_middle",
        "odd_inclusio",
        "odd_middle",
        "even_inclusio",
        "even_middle",
        "odd_strip10_inclusio",
        "odd_strip10_middle",
        "even_strip10_inclusio",
        "even_strip10_middle",
        "kalila_arb_inclusio",
        "kalila_arb_middle",
        "kalila_nat_inclusio",
        "kalila_nat_middle",
    )
    ratios = {}
    raw_pairs = {}
    for k in req_pairs:
        if k not in metrics:
            raise ArabicOracleError("MISSING_KEY", f"pillar2 missing {k}")
        inter, union, frac = require_pair_ratio(metrics[k], f"pillar2.{k}")
        ratios[k] = frac
        raw_pairs[k] = [inter, union]

    if (
        raw_pairs["all_inclusio"][0] != raw_pairs["odd_inclusio"][0] + raw_pairs["even_inclusio"][0]
        or raw_pairs["all_inclusio"][1] != raw_pairs["odd_inclusio"][1] + raw_pairs["even_inclusio"][1]
        or raw_pairs["all_middle"][0] != raw_pairs["odd_middle"][0] + raw_pairs["even_middle"][0]
        or raw_pairs["all_middle"][1] != raw_pairs["odd_middle"][1] + raw_pairs["even_middle"][1]
    ):
        raise ArabicOracleError("SPLIT_SUM_MISMATCH", "all_inclusio/all_middle must equal odd+even")

    pointwise_ring_falsified = (
        ratios["all_mirror"] < ratios["all_shift"]
        and ratios["all_mirror"] < ratios["all_perm_null"]
    )
    inclusio_train_and_unseen = (
        ratios["odd_inclusio"] - abs(ratios["odd_middle"]) >= margin
        and ratios["even_inclusio"] - abs(ratios["even_middle"]) >= margin
    )
    strip10_train_and_unseen = (
        ratios["odd_strip10_inclusio"] - abs(ratios["odd_strip10_middle"]) >= margin
        and ratios["even_strip10_inclusio"] - abs(ratios["even_strip10_middle"]) >= margin
    )
    arbitrary_prose_decays = ratios["kalila_arb_inclusio"] < ratios["kalila_arb_middle"]
    framed_prose_shows_inclusio = (
        ratios["kalila_nat_inclusio"] - abs(ratios["kalila_nat_middle"]) >= margin
    )

    deltas = {
        "all_inclusio_minus_middle": ratios["all_inclusio"] - ratios["all_middle"],
        "odd_inclusio_minus_middle": ratios["odd_inclusio"] - ratios["odd_middle"],
        "even_inclusio_minus_middle": ratios["even_inclusio"] - ratios["even_middle"],
        "odd_strip10_delta": ratios["odd_strip10_inclusio"] - ratios["odd_strip10_middle"],
        "even_strip10_delta": ratios["even_strip10_inclusio"] - ratios["even_strip10_middle"],
        "kalila_arb_delta": ratios["kalila_arb_inclusio"] - ratios["kalila_arb_middle"],
        "kalila_nat_delta": ratios["kalila_nat_inclusio"] - ratios["kalila_nat_middle"],
    }

    passed = (
        pointwise_ring_falsified
        and inclusio_train_and_unseen
        and strip10_train_and_unseen
        and arbitrary_prose_decays
        and framed_prose_shows_inclusio
    )

    return {
        "pairs": raw_pairs,
        "ratios_exact": {k: frac_str(v) for k, v in ratios.items()},
        "ratios_dec6": {k: format_exact_decimal(v) for k, v in ratios.items()},
        "deltas_exact": {k: frac_str(v) for k, v in deltas.items()},
        "deltas_dec6": {k: format_exact_decimal(v) for k, v in deltas.items()},
        "pointwise_ring_falsified": pointwise_ring_falsified,
        "inclusio_holds_train_and_unseen": inclusio_train_and_unseen,
        "strip10_inclusio_holds_train_and_unseen": strip10_train_and_unseen,
        "arbitrary_prose_reverses_to_decay": arbitrary_prose_decays,
        "framed_prose_control_shows_inclusio": framed_prose_shows_inclusio,
        "passed": passed,
    }


def audit_translation_remainder_exact(
    root_records,
    bg_sahih_pair,
    bg_pickthall_pair,
    min_pooled_edge_loss=Fraction(1, 2),
):
    """Pillar 3: Two-instrument Continuum-to-Discrete Translation Remainder oracle."""
    verify_no_floats(
        {
            "root_records": root_records,
            "bg_sahih_pair": bg_sahih_pair,
            "bg_pickthall_pair": bg_pickthall_pair,
            "min_pooled_edge_loss": min_pooled_edge_loss,
        },
        "pillar3",
    )
    min_loss = require_exact_fraction(
        min_pooled_edge_loss,
        "min_pooled_edge_loss",
        min_value=Fraction(0, 1),
        max_value=Fraction(1, 1),
    )
    bs_i, bs_u, bg_sahih = require_pair_ratio(bg_sahih_pair, "bg_sahih_pair")
    bp_i, bp_u, bg_pick = require_pair_ratio(bg_pickthall_pair, "bg_pickthall_pair")

    if not isinstance(root_records, (list, tuple)) or len(root_records) == 0:
        raise ArabicOracleError("INVALID_RECORDS", "root_records must be non-empty sequence")

    seen_roots = set()
    per_root = []
    tot_multi_verses = 0
    sahih_miss_num = 0
    pick_miss_num = 0
    tot_pairs_all = 0
    sahih_lost_all = 0
    pick_lost_all = 0
    severe_both_count = 0
    max_trans_edge_div = Fraction(0, 1)

    for idx, rec in enumerate(root_records):
        if not isinstance(rec, dict):
            raise ArabicOracleError("INVALID_RECORD", f"record[{idx}] must be dict")
        root = require_non_empty_str(rec.get("root"), f"record[{idx}].root")
        norm_key = root.lower()
        if norm_key in seen_roots:
            raise ArabicOracleError("DUPLICATE_ROOT", f"duplicate root {root}")
        seen_roots.add(norm_key)

        occ = require_exact_int(rec.get("occurrences"), f"{root}.occurrences", min_value=1)
        vcnt = require_exact_int(rec.get("verse_count"), f"{root}.verse_count", min_value=1, max_value=occ)
        lems = require_exact_int(rec.get("unique_lemmas"), f"{root}.unique_lemmas", min_value=1)
        s_top = require_exact_int(rec.get("sahih_top_count"), f"{root}.sahih_top_count", min_value=0, max_value=vcnt)
        p_top = require_exact_int(rec.get("pickthall_top_count"), f"{root}.pickthall_top_count", min_value=0, max_value=vcnt)
        expected_pairs = vcnt * (vcnt - 1) // 2
        s_min_lost = expected_pairs if (vcnt >= 2 and s_top <= 1) else 0
        p_min_lost = expected_pairs if (vcnt >= 2 and p_top <= 1) else 0
        s_max_lost = expected_pairs - s_top * (s_top - 1) // 2
        p_max_lost = expected_pairs - p_top * (p_top - 1) // 2
        s_lost = require_exact_int(rec.get("sahih_lost_pairs"), f"{root}.sahih_lost_pairs", min_value=s_min_lost, max_value=s_max_lost)
        p_lost = require_exact_int(rec.get("pickthall_lost_pairs"), f"{root}.pickthall_lost_pairs", min_value=p_min_lost, max_value=p_max_lost)
        s_tot = require_exact_int(rec.get("sahih_total_pairs"), f"{root}.sahih_total_pairs", min_value=expected_pairs, max_value=expected_pairs)
        p_tot = require_exact_int(rec.get("pickthall_total_pairs"), f"{root}.pickthall_total_pairs", min_value=expected_pairs, max_value=expected_pairs)

        entry = {
            "root": root,
            "occurrences": occ,
            "verse_count": vcnt,
            "unique_lemmas": lems,
            "total_pairs": expected_pairs,
            "sahih_top_count": s_top,
            "pickthall_top_count": p_top,
            "sahih_lost_pairs": s_lost,
            "pickthall_lost_pairs": p_lost,
        }
        if vcnt >= 2:
            s_miss = Fraction(vcnt - s_top, vcnt)
            p_miss = Fraction(vcnt - p_top, vcnt)
            s_edge = Fraction(s_lost, s_tot)
            p_edge = Fraction(p_lost, p_tot)
            edge_div = abs(s_edge - p_edge)
            if edge_div > max_trans_edge_div:
                max_trans_edge_div = edge_div
            if s_edge >= Fraction(2, 5) and p_edge >= Fraction(2, 5):
                severe_both_count += 1
            tot_multi_verses += vcnt
            sahih_miss_num += vcnt - s_top
            pick_miss_num += vcnt - p_top
            tot_pairs_all += expected_pairs
            sahih_lost_all += s_lost
            pick_lost_all += p_lost
            entry.update({
                "multi_verse": True,
                "sahih_miss_exact": frac_str(s_miss),
                "sahih_miss_dec6": format_exact_decimal(s_miss),
                "pickthall_miss_exact": frac_str(p_miss),
                "pickthall_miss_dec6": format_exact_decimal(p_miss),
                "sahih_edge_loss_exact": frac_str(s_edge),
                "sahih_edge_loss_dec6": format_exact_decimal(s_edge),
                "pickthall_edge_loss_exact": frac_str(p_edge),
                "pickthall_edge_loss_dec6": format_exact_decimal(p_edge),
                "translator_edge_divergence_exact": frac_str(edge_div),
                "translator_edge_divergence_dec6": format_exact_decimal(edge_div),
            })
        else:
            entry["multi_verse"] = False
        per_root.append(entry)

    if tot_pairs_all == 0:
        raise ArabicOracleError("NO_MULTI_VERSE_ROOTS", "need at least one multi-verse root")

    s_pool_miss = Fraction(sahih_miss_num, tot_multi_verses)
    p_pool_miss = Fraction(pick_miss_num, tot_multi_verses)
    s_pool_edge = Fraction(sahih_lost_all, tot_pairs_all)
    p_pool_edge = Fraction(pick_lost_all, tot_pairs_all)

    two_instrument_confirmed = (
        s_pool_edge >= min_loss
        and p_pool_edge >= min_loss
        and s_pool_edge < bg_sahih
        and p_pool_edge < bg_pick
        and severe_both_count >= 4
    )

    return {
        "root_count": len(per_root),
        "bg_unrelated_sahih_pair": [bs_i, bs_u],
        "bg_unrelated_sahih_dec6": format_exact_decimal(bg_sahih),
        "bg_unrelated_pickthall_pair": [bp_i, bp_u],
        "bg_unrelated_pickthall_dec6": format_exact_decimal(bg_pick),
        "pooled_multi_verses": tot_multi_verses,
        "pooled_pairs": tot_pairs_all,
        "sahih_pooled_miss_exact": frac_str(s_pool_miss),
        "sahih_pooled_miss_dec6": format_exact_decimal(s_pool_miss),
        "pickthall_pooled_miss_exact": frac_str(p_pool_miss),
        "pickthall_pooled_miss_dec6": format_exact_decimal(p_pool_miss),
        "sahih_pooled_edge_loss_exact": frac_str(s_pool_edge),
        "sahih_pooled_edge_loss_dec6": format_exact_decimal(s_pool_edge),
        "pickthall_pooled_edge_loss_exact": frac_str(p_pool_edge),
        "pickthall_pooled_edge_loss_dec6": format_exact_decimal(p_pool_edge),
        "severe_remainder_both_translators": severe_both_count,
        "max_translator_edge_divergence_exact": frac_str(max_trans_edge_div),
        "max_translator_edge_divergence_dec6": format_exact_decimal(max_trans_edge_div),
        "per_root": per_root,
        "passed": two_instrument_confirmed,
    }


def certify_arabic_own_terms_5axis_gate(
    mode,
    pinned_sha256s,
    feature_names,
    pillar1_result,
    pillar2_result,
    pillar3_result,
    five_axis_checks,
):
    """Pillar 4: Integrated OWN_TERMS_FIRST 5-axis + Law-5 anti-numerology certificate."""
    verify_no_floats(
        {
            "mode": mode,
            "pinned_sha256s": pinned_sha256s,
            "feature_names": feature_names,
            "pillar1_result": pillar1_result,
            "pillar2_result": pillar2_result,
            "pillar3_result": pillar3_result,
            "five_axis_checks": five_axis_checks,
        },
        "pillar4",
    )
    clean_mode = require_non_empty_str(mode, "mode")
    if clean_mode not in ("live_readonly", "standalone"):
        raise ArabicOracleError("INVALID_MODE", f"unsupported mode {clean_mode}")

    if not isinstance(pinned_sha256s, dict) or len(pinned_sha256s) == 0:
        raise ArabicOracleError("MISSING_PROVENANCE", "pinned_sha256s must be non-empty dict")
    clean_pins = {}
    for k, v in sorted(pinned_sha256s.items()):
        pk = require_non_empty_str(k, "pin_path")
        if pk.startswith("/") or ".." in pk or "file://" in pk:
            raise ArabicOracleError("UNSAFE_PIN_PATH", f"unsafe pin path {pk}")
        if pk in clean_pins:
            raise ArabicOracleError("DUPLICATE_PIN_PATH", f"duplicate pin path {pk}")
        if not isinstance(v, str) or not HEX64_RE.fullmatch(v) or v == "0" * 64:
            raise ArabicOracleError("INVALID_SHA256", f"invalid sha256 for {pk}")
        clean_pins[pk] = v

    num_guard = enforce_zero_numerology_policy(feature_names)

    req_axes = (
        "diacritics_vs_rasm",
        "window_size_10_20_40",
        "root_vs_stem",
        "odd_vs_even_unseen",
        "second_instrument_and_controls",
    )
    if not isinstance(five_axis_checks, dict):
        raise ArabicOracleError("INVALID_AXES", "five_axis_checks must be dict")
    if set(five_axis_checks.keys()) != set(req_axes):
        raise ArabicOracleError("INVALID_AXES", "five_axis_checks keys must match exact 5 axes")
    clean_axes = {}
    for ax in req_axes:
        clean_axes[ax] = require_exact_bool(five_axis_checks[ax], f"five_axis_checks.{ax}")

    if (
        not isinstance(pillar1_result, dict)
        or not isinstance(pillar2_result, dict)
        or not isinstance(pillar3_result, dict)
    ):
        raise ArabicOracleError("INVALID_PILLAR", "pillar results must be dicts")

    p1_ok = require_exact_bool(pillar1_result.get("passed"), "pillar1.passed")
    p1_lat = require_exact_bool(pillar1_result.get("lattice_nontrivial"), "pillar1.lattice_nontrivial")
    p1_mono = require_exact_bool(pillar1_result.get("monotonic_ladder_all_w"), "pillar1.monotonic_ladder_all_w")
    p1_nulls = require_exact_bool(pillar1_result.get("root_beats_nulls_all_w"), "pillar1.root_beats_nulls_all_w")
    p1_split = require_exact_bool(pillar1_result.get("split_halves_beat_t4b_all_w"), "pillar1.split_halves_beat_t4b_all_w")
    p1_shared = require_exact_bool(pillar1_result.get("shared_classical_prose_property"), "pillar1.shared_classical_prose_property")
    p1_poetry = require_exact_bool(pillar1_result.get("prose_exceeds_poetry_baseline"), "pillar1.prose_exceeds_poetry_baseline")
    if p1_ok != (p1_lat and p1_mono and p1_nulls and p1_split and p1_shared and p1_poetry):
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar1.passed contradicts subchecks")

    p2_ok = require_exact_bool(pillar2_result.get("passed"), "pillar2.passed")
    p2_ring = require_exact_bool(pillar2_result.get("pointwise_ring_falsified"), "pillar2.pointwise_ring_falsified")
    p2_inc = require_exact_bool(pillar2_result.get("inclusio_holds_train_and_unseen"), "pillar2.inclusio_holds_train_and_unseen")
    p2_s10 = require_exact_bool(pillar2_result.get("strip10_inclusio_holds_train_and_unseen"), "pillar2.strip10_inclusio_holds_train_and_unseen")
    p2_arb = require_exact_bool(pillar2_result.get("arbitrary_prose_reverses_to_decay"), "pillar2.arbitrary_prose_reverses_to_decay")
    p2_nat = require_exact_bool(pillar2_result.get("framed_prose_control_shows_inclusio"), "pillar2.framed_prose_control_shows_inclusio")
    if p2_ok != (p2_ring and p2_inc and p2_s10 and p2_arb and p2_nat):
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar2.passed contradicts subchecks")

    p3_ok = require_exact_bool(pillar3_result.get("passed"), "pillar3.passed")
    p3_sev = require_exact_int(
        pillar3_result.get("severe_remainder_both_translators"),
        "pillar3.severe_remainder_both_translators",
        min_value=0,
    )
    require_exact_int(pillar3_result.get("pooled_pairs"), "pillar3.pooled_pairs", min_value=1)
    if p3_ok and p3_sev < 4:
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar3.passed contradicts severe count")

    expected_axes = {
        "diacritics_vs_rasm": p1_mono,
        "window_size_10_20_40": p1_nulls,
        "root_vs_stem": p1_mono and p1_lat,
        "odd_vs_even_unseen": p1_split and p2_inc and p2_s10,
        "second_instrument_and_controls": p1_shared and p1_poetry and p2_arb and p3_ok,
    }
    if clean_axes != expected_axes:
        raise ArabicOracleError("AXIS_CONTRADICTION", "five_axis_checks contradicts pillar evidence")

    all_axes_ok = all(clean_axes.values())
    all_passed = p1_ok and p2_ok and p3_ok and all_axes_ok and num_guard["zero_numerology_ok"]

    body = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "AUDIT-091",
        "mode": clean_mode,
        "pinned_corpus_sha256": clean_pins,
        "pinned_corpus_count": len(clean_pins),
        "zero_numerology_guard": num_guard,
        "five_axis_net_invariance": clean_axes,
        "all_five_axes_passed": all_axes_ok,
        "pillar1_root_pattern_lattice": pillar1_result,
        "pillar2_ring_vs_inclusio": pillar2_result,
        "pillar3_translation_remainder": pillar3_result,
        "verdict": "CERTIFIED_ARABIC_CONTINUUM_STRUCTURE" if all_passed else "REJECTED_GATE_FAILED",
        "all_gates_passed": all_passed,
    }
    body["certificate_sha256"] = canonical_sha256(body)
    return body
