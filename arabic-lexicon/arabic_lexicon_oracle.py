"""Exact pure-Q oracle for Wave 3b Lane B (AUDIT-094):
Classical Arabic Lexical Semantic-Field Topology & Multi-Translator Continuum
Projection Defect under OWN_TERMS_FIRST, Law 2b Transformational Steelman,
and Law 5 Anti-Numerology Guard.

Governance invariants:
- Pure Python 3 standard library only; zero floats anywhere on trust paths.
- Zero bare assert statements; fail closed with typed LexiconOracleError.
- Strict raw ASCII control & Unicode Cf format-char rejection + compact
  separator-stripped anti-numerology guard + exact conservation laws.
"""

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import math
import re
import unicodedata


SCHEMA_VERSION = "arabic-lexicon-topology-oracle/v1"
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


class LexiconOracleError(ValueError):
    """Typed fail-closed error carrying a stable machine-readable code."""

    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code


def verify_no_floats(obj, path="root"):
    """Recursively reject float and complex values anywhere in a structure."""
    if isinstance(obj, (float, complex)):
        raise LexiconOracleError("FLOAT_FORBIDDEN", f"float/complex at {path}")
    if isinstance(obj, dict):
        for k, v in obj.items():
            verify_no_floats(k, f"{path}.<key>")
            verify_no_floats(v, f"{path}.{k}")
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for idx, item in enumerate(obj):
            verify_no_floats(item, f"{path}[{idx}]")


def require_non_empty_str(val, field):
    if not isinstance(val, str):
        raise LexiconOracleError("INVALID_TYPE", f"{field} must be str")
    for ch in val:
        code = ord(ch)
        if code < 32 or code == 127 or unicodedata.category(ch) == "Cf":
            raise LexiconOracleError("CONTROL_CHAR", f"{field} contains control or format char")
    stripped = val.strip()
    if not stripped:
        raise LexiconOracleError("EMPTY_STRING", f"{field} must be non-empty")
    return stripped


def require_exact_bool(val, field):
    if not isinstance(val, bool):
        raise LexiconOracleError("INVALID_BOOL", f"{field} must be bool")
    return val


def require_exact_int(val, field, min_value=None, max_value=None):
    if isinstance(val, bool) or not isinstance(val, int):
        raise LexiconOracleError("INVALID_INT", f"{field} must be int")
    if min_value is not None and val < min_value:
        raise LexiconOracleError("RANGE_ERROR", f"{field} < {min_value}")
    if max_value is not None and val > max_value:
        raise LexiconOracleError("RANGE_ERROR", f"{field} > {max_value}")
    return val


def require_exact_fraction(val, field, min_value=None, max_value=None):
    if isinstance(val, bool):
        raise LexiconOracleError("INVALID_FRACTION", f"{field} must not be bool")
    if isinstance(val, int):
        out = Fraction(val, 1)
    elif isinstance(val, Fraction):
        out = val
    else:
        raise LexiconOracleError("INVALID_FRACTION", f"{field} must be Fraction or int")
    if min_value is not None and out < min_value:
        raise LexiconOracleError("RANGE_ERROR", f"{field} < {min_value}")
    if max_value is not None and out > max_value:
        raise LexiconOracleError("RANGE_ERROR", f"{field} > {max_value}")
    return out


def require_pair_ratio(pair, field):
    """Validate an exact (num, den) integer pair with 0 <= num <= den and den > 0."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise LexiconOracleError("INVALID_PAIR", f"{field} must be a 2-tuple of ints")
    num = require_exact_int(pair[0], f"{field}[0]", min_value=0)
    den = require_exact_int(pair[1], f"{field}[1]", min_value=1)
    if num > den:
        raise LexiconOracleError("INVALID_PAIR", f"{field} num > den")
    return num, den, Fraction(num, den)


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
    quot, rem = divmod(mag.numerator * scale, mag.denominator)
    if rem * 2 >= mag.denominator:
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
        raise LexiconOracleError("INVALID_SEQ", "items must be list or tuple")
    x = require_exact_int(seed, "seed", min_value=0) & 0xFFFFFFFFFFFFFFFF
    arr = list(items)
    for i in range(len(arr) - 1, 0, -1):
        x = (6364136223846793005 * x + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        j = (x >> 33) % (i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def stratified_shuffle_exact(items, classes, seed):
    """Tier-4B class-preserving deterministic shuffle."""
    if not isinstance(items, (list, tuple)) or not isinstance(classes, (list, tuple)):
        raise LexiconOracleError("INVALID_SEQ", "items and classes must be list or tuple")
    if len(items) != len(classes):
        raise LexiconOracleError("LENGTH_MISMATCH", "items and classes lengths differ")
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
    if not isinstance(token, str):
        raise LexiconOracleError("INVALID_TYPE", "token must be str")
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
    if not isinstance(text, str):
        raise LexiconOracleError("INVALID_TYPE", "text must be str")
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


def renyi2_concentration_pair(counts_dict):
    """Exact pure-Q Renyi-2 collision concentration (sum c_i^2, N^2)."""
    if not isinstance(counts_dict, dict) or len(counts_dict) == 0:
        raise LexiconOracleError("INVALID_COUNTS", "counts_dict must be non-empty dict")
    total = 0
    sq_sum = 0
    for k, v in counts_dict.items():
        c = require_exact_int(v, f"counts[{k}]", min_value=1)
        total += c
        sq_sum += c * c
    return sq_sum, total * total, Fraction(sq_sum, total * total)


def block_renyi2_cross_pair(seq, window_size):
    """Exact pure-Q adjacent-window Renyi-2 cross-collision probability."""
    if not isinstance(seq, (list, tuple)):
        raise LexiconOracleError("INVALID_SEQ", "seq must be list or tuple")
    w = require_exact_int(window_size, "window_size", min_value=2)
    n_blocks = len(seq) // w
    if n_blocks < 2:
        raise LexiconOracleError("INSUFFICIENT_BLOCKS", "need at least 2 full windows")
    num = 0
    den = (n_blocks - 1) * w * w
    for i in range(n_blocks - 1):
        ca = Counter(seq[i * w:(i + 1) * w])
        cb = Counter(seq[(i + 1) * w:(i + 2) * w])
        for tok in ca.keys() & cb.keys():
            num += ca[tok] * cb[tok]
    return num, den, Fraction(num, den)


def enforce_zero_numerology_policy(feature_names):
    """Strict Law 5 guard: reject any abjad/gematria/digit-count/miracle feature."""
    verify_no_floats(feature_names, "feature_names")
    if not isinstance(feature_names, (list, tuple)) or len(feature_names) == 0:
        raise LexiconOracleError("INVALID_FEATURES", "feature_names must be non-empty sequence")
    seen_compact = set()
    normalized = []
    for idx, raw in enumerate(feature_names):
        name = unicodedata.normalize("NFKC", require_non_empty_str(raw, f"feature_names[{idx}]")).lower()
        compact = NON_ALNUM_RE.sub("", name)
        if not compact:
            raise LexiconOracleError("EMPTY_STRING", f"feature_names[{idx}] has no alnum chars")
        if compact in seen_compact:
            raise LexiconOracleError("DUPLICATE_FEATURE", f"duplicate feature {name}")
        for bad in FORBIDDEN_NUMEROLOGY_TOKENS:
            if bad in compact:
                raise LexiconOracleError("NUMEROLOGY_FORBIDDEN", f"forbidden feature {name}")
        seen_compact.add(compact)
        normalized.append(name)
    return {"zero_numerology_ok": True, "feature_count": len(normalized), "features": normalized}


def audit_wazn_agency_matrix_and_renyi2_exact(
    total_unique_roots,
    verb_roots,
    poly_wazn_roots,
    verb_tokens_i_x,
    form_xii_tokens,
    op_class_counts,
    transition_pair_counts,
    within_root_renyi2_pairs,
    control_renyi2_metrics,
    min_wazn_margin=Fraction(1, 5),
):
    """Pillar 1: 1,642-root x Wazn (I-X) agency/reciprocity matrix & Renyi-2 concentration."""
    verify_no_floats(
        {
            "total_unique_roots": total_unique_roots,
            "verb_roots": verb_roots,
            "poly_wazn_roots": poly_wazn_roots,
            "verb_tokens_i_x": verb_tokens_i_x,
            "form_xii_tokens": form_xii_tokens,
            "op_class_counts": op_class_counts,
            "transition_pair_counts": transition_pair_counts,
            "within_root_renyi2_pairs": within_root_renyi2_pairs,
            "control_renyi2_metrics": control_renyi2_metrics,
            "min_wazn_margin": min_wazn_margin,
        },
        "pillar1",
    )
    tot_roots = require_exact_int(total_unique_roots, "total_unique_roots", min_value=1)
    v_roots = require_exact_int(verb_roots, "verb_roots", min_value=1, max_value=tot_roots)
    poly_roots = require_exact_int(poly_wazn_roots, "poly_wazn_roots", min_value=1, max_value=v_roots)
    v_toks = require_exact_int(verb_tokens_i_x, "verb_tokens_i_x", min_value=v_roots + poly_roots)
    xii_toks = require_exact_int(form_xii_tokens, "form_xii_tokens", min_value=0)
    margin = require_exact_fraction(min_wazn_margin, "min_wazn_margin", min_value=Fraction(0, 1))

    req_ops = (
        "GROUND_I",
        "CAUS_INTENS_II_III_IV",
        "REFL_RECIP_V_VI_VII_VIII",
        "STAT_ESTIM_IX_X",
    )
    if not isinstance(op_class_counts, dict) or set(op_class_counts.keys()) != set(req_ops):
        raise LexiconOracleError("INVALID_OP_CLASSES", "op_class_counts must match exact 4 classes")
    clean_ops = {}
    op_sum = 0
    for op in req_ops:
        cnt = require_exact_int(op_class_counts[op], f"op_class_counts.{op}", min_value=1)
        clean_ops[op] = cnt
        op_sum += cnt
    if op_sum != v_toks:
        raise LexiconOracleError("CONSERVATION_ERROR", "op_class_counts sum != verb_tokens_i_x")

    req_pairs = ("I+IV", "I+II", "II+V", "III+VI", "I+VIII", "I+X", "IV+X")
    if not isinstance(transition_pair_counts, dict) or set(transition_pair_counts.keys()) != set(req_pairs):
        raise LexiconOracleError("INVALID_TRANSITIONS", "transition_pair_counts keys mismatch")
    clean_trans = {}
    for pk in req_pairs:
        clean_trans[pk] = require_exact_int(
            transition_pair_counts[pk],
            f"transition_pair_counts.{pk}",
            min_value=1,
            max_value=poly_roots,
        )

    # LEX-BUG-02: disjoint form-class lower bounds on op_class_counts
    if (
        max(clean_trans["I+IV"], clean_trans["I+II"], clean_trans["I+VIII"], clean_trans["I+X"])
        > clean_ops["GROUND_I"]
        or max(clean_trans["I+II"], clean_trans["II+V"])
        + clean_trans["III+VI"]
        + max(clean_trans["I+IV"], clean_trans["IV+X"])
        > clean_ops["CAUS_INTENS_II_III_IV"]
        or clean_trans["II+V"] + clean_trans["III+VI"] + clean_trans["I+VIII"]
        > clean_ops["REFL_RECIP_V_VI_VII_VIII"]
        or max(clean_trans["I+X"], clean_trans["IV+X"]) > clean_ops["STAT_ESTIM_IX_X"]
    ):
        raise LexiconOracleError("CONSERVATION_ERROR", "transition counts exceed disjoint op-class totals")

    req_wr = ("all_obs", "all_t4a", "all_t4b", "odd_obs", "odd_t4b", "even_obs", "even_t4b")
    if not isinstance(within_root_renyi2_pairs, dict) or set(within_root_renyi2_pairs.keys()) != set(req_wr):
        raise LexiconOracleError("INVALID_WR_PAIRS", "within_root_renyi2_pairs keys mismatch")
    wr_ratios = {}
    wr_raw = {}
    for wk in req_wr:
        n, d, r = require_pair_ratio(within_root_renyi2_pairs[wk], f"wr.{wk}")
        if 10 * n < d:
            raise LexiconOracleError("CONSERVATION_ERROR", f"wr.{wk} violates 10-form Cauchy-Schwarz floor")
        wr_ratios[wk] = r
        wr_raw[wk] = [n, d]

    all_u, all_d = wr_raw["all_obs"]
    odd_u, odd_d = wr_raw["odd_obs"]
    even_u, even_d = wr_raw["even_obs"]
    if (
        all_d != wr_raw["all_t4a"][1]
        or all_d != wr_raw["all_t4b"][1]
        or odd_d != wr_raw["odd_t4b"][1]
        or even_d != wr_raw["even_t4b"][1]
        or all_d * v_roots < v_toks * v_toks
        or all_d > v_toks * v_toks
        or all_d - all_u < 2 * poly_roots
        or all_d < odd_d + even_d
        or all_d > 2 * (odd_d + even_d)
        or all_u < odd_u + even_u
        or all_u > 2 * (odd_u + even_u)
    ):
        raise LexiconOracleError("CONSERVATION_ERROR", "within-root Renyi-2 conservation violated")

    wazn_beats_nulls = (
        wr_ratios["all_obs"] - abs(wr_ratios["all_t4a"]) >= margin
        and wr_ratios["all_obs"] - abs(wr_ratios["all_t4b"]) >= margin
        and wr_ratios["odd_obs"] - abs(wr_ratios["odd_t4b"]) >= margin
        and wr_ratios["even_obs"] - abs(wr_ratios["even_t4b"]) >= margin
    )

    ctrl_names = ("quran_stem", "kalila_prose", "adab_prose", "poetry_pooled")
    if not isinstance(control_renyi2_metrics, dict) or set(control_renyi2_metrics.keys()) != set(ctrl_names):
        raise LexiconOracleError("INVALID_CONTROLS", "control_renyi2_metrics keys mismatch")
    ctrl_report = {}
    ctrl_vals = {}
    for cn in ctrl_names:
        cd = control_renyi2_metrics[cn]
        if not isinstance(cd, dict) or set(cd.keys()) != {"global_c2", "w20_obs", "w20_t4a"}:
            raise LexiconOracleError("INVALID_CONTROL_ENTRY", f"{cn} must have global_c2, w20_obs, w20_t4a")
        gn, gd, g_c2 = require_pair_ratio(cd["global_c2"], f"{cn}.global_c2")
        on, od, o_r = require_pair_ratio(cd["w20_obs"], f"{cn}.w20_obs")
        nn, nd, n_r = require_pair_ratio(cd["w20_t4a"], f"{cn}.w20_t4a")
        n_tok = math.isqrt(gd)
        if n_tok * n_tok != gd or gn < n_tok or (gn - n_tok) % 2 != 0:
            raise LexiconOracleError("CONSERVATION_ERROR", f"{cn}.global_c2 violates exact sum(c^2)/N^2 law")
        if od != nd:
            raise LexiconOracleError("CONSERVATION_ERROR", f"{cn} w20 obs/t4a denominator mismatch")
        if n_r == 0:
            raise LexiconOracleError("ZERO_DENOM", f"{cn} w20_t4a is zero")
        d2 = Fraction(1, 1) / g_c2
        lift = o_r / n_r
        ctrl_vals[cn] = (g_c2, d2, o_r, n_r, lift)
        ctrl_report[cn] = {
            "global_c2_pair": [gn, gd],
            "global_c2_dec6": format_exact_decimal(g_c2),
            "effective_d2_exact": frac_str(d2),
            "effective_d2_dec6": format_exact_decimal(d2),
            "w20_obs_pair": [on, od],
            "w20_obs_dec6": format_exact_decimal(o_r),
            "w20_t4a_pair": [nn, nd],
            "w20_t4a_dec6": format_exact_decimal(n_r),
            "w20_lift_exact": frac_str(lift),
            "w20_lift_dec6": format_exact_decimal(lift),
        }

    poly_ratio = Fraction(poly_roots, v_roots)
    derived_share = Fraction(v_toks - clean_ops["GROUND_I"], v_toks)
    shared_prose_lift = (
        ctrl_vals["quran_stem"][2] > ctrl_vals["quran_stem"][3]
        and ctrl_vals["kalila_prose"][2] > ctrl_vals["kalila_prose"][3]
        and ctrl_vals["adab_prose"][2] > ctrl_vals["adab_prose"][3]
    )
    poetry_higher_d2 = (
        ctrl_vals["poetry_pooled"][1] > ctrl_vals["quran_stem"][1]
        and ctrl_vals["poetry_pooled"][1] > ctrl_vals["kalila_prose"][1]
        and ctrl_vals["poetry_pooled"][1] > ctrl_vals["adab_prose"][1]
    )
    agency_matrix_nontrivial = (
        poly_ratio >= Fraction(1, 3)
        and derived_share >= Fraction(1, 3)
        and clean_trans["I+IV"] >= 100
        and clean_trans["II+V"] >= 20
        and clean_trans["III+VI"] >= 10
    )

    passed = agency_matrix_nontrivial and wazn_beats_nulls and shared_prose_lift and poetry_higher_d2

    return {
        "total_unique_roots": tot_roots,
        "verb_roots": v_roots,
        "poly_wazn_roots": poly_roots,
        "poly_wazn_ratio_exact": frac_str(poly_ratio),
        "poly_wazn_ratio_dec6": format_exact_decimal(poly_ratio),
        "verb_tokens_i_x": v_toks,
        "form_xii_tokens": xii_toks,
        "derived_verb_share_exact": frac_str(derived_share),
        "derived_verb_share_dec6": format_exact_decimal(derived_share),
        "op_class_counts": clean_ops,
        "transition_pair_counts": clean_trans,
        "within_root_renyi2_pairs": wr_raw,
        "within_root_renyi2_exact": {k: frac_str(v) for k, v in wr_ratios.items()},
        "within_root_renyi2_dec6": {k: format_exact_decimal(v) for k, v in wr_ratios.items()},
        "controls_renyi2": ctrl_report,
        "agency_matrix_nontrivial": agency_matrix_nontrivial,
        "within_root_wazn_beats_nulls": wazn_beats_nulls,
        "shared_prose_renyi2_lift": shared_prose_lift,
        "poetry_higher_effective_diversity": poetry_higher_d2,
        "passed": passed,
    }


def audit_context_neighborhood_topology_exact(
    metrics,
    min_r2_lift=Fraction(6, 5),
    min_cooccur_margin=Fraction(1, 50),
):
    """Pillar 2: Native Arabic top-10-stripped co-occurrence neighborhood topology."""
    verify_no_floats(
        {
            "metrics": metrics,
            "min_r2_lift": min_r2_lift,
            "min_cooccur_margin": min_cooccur_margin,
        },
        "pillar2",
    )
    r2_lift_min = require_exact_fraction(min_r2_lift, "min_r2_lift", min_value=Fraction(1, 1))
    co_margin = require_exact_fraction(min_cooccur_margin, "min_cooccur_margin", min_value=Fraction(0, 1))

    req_keys = (
        "ctx_r2_all", "ctx_r2_null",
        "ctx_r2_odd", "ctx_r2_odd_null",
        "ctx_r2_even", "ctx_r2_even_null",
        "ctx_jaccard_all", "ctx_jaccard_null",
        "ctx_jaccard_odd", "ctx_jaccard_odd_null",
        "ctx_jaccard_even", "ctx_jaccard_even_null",
        "cooccur_all", "cooccur_null",
        "cooccur_odd", "cooccur_odd_null",
        "cooccur_even", "cooccur_even_null",
    )
    if not isinstance(metrics, dict) or set(metrics.keys()) != set(req_keys):
        raise LexiconOracleError("INVALID_METRICS", "pillar2 metrics keys mismatch")

    ratios = {}
    raw_pairs = {}
    for k in req_keys:
        n, d, r = require_pair_ratio(metrics[k], f"pillar2.{k}")
        ratios[k] = r
        raw_pairs[k] = [n, d]

    # Exact additive split conservation for direct co-occurrence verse counts
    if (
        raw_pairs["cooccur_all"][0] != raw_pairs["cooccur_odd"][0] + raw_pairs["cooccur_even"][0]
        or raw_pairs["cooccur_all"][1] != raw_pairs["cooccur_odd"][1] + raw_pairs["cooccur_even"][1]
        or raw_pairs["cooccur_null"][0] != raw_pairs["cooccur_odd_null"][0] + raw_pairs["cooccur_even_null"][0]
        or raw_pairs["cooccur_null"][1] != raw_pairs["cooccur_odd_null"][1] + raw_pairs["cooccur_even_null"][1]
    ):
        raise LexiconOracleError("SPLIT_SUM_MISMATCH", "cooccur_all/null must equal odd + even")

    # LEX-BUG-03: exact weighted Jaccard & quadratic context Renyi-2 split-half conservation
    for a_k, o_k, e_k in (
        ("ctx_jaccard_all", "ctx_jaccard_odd", "ctx_jaccard_even"),
        ("ctx_jaccard_null", "ctx_jaccard_odd_null", "ctx_jaccard_even_null"),
    ):
        ai, au = raw_pairs[a_k]
        oi, ou = raw_pairs[o_k]
        ei, eu = raw_pairs[e_k]
        if ai + au != (oi + ou) + (ei + eu) or ai < oi + ei or au > ou + eu:
            raise LexiconOracleError("SPLIT_SUM_MISMATCH", f"{a_k} violates weighted Jaccard split conservation")

    for a_k, o_k, e_k in (
        ("ctx_r2_all", "ctx_r2_odd", "ctx_r2_even"),
        ("ctx_r2_null", "ctx_r2_odd_null", "ctx_r2_even_null"),
    ):
        au, ad = raw_pairs[a_k]
        ou, od = raw_pairs[o_k]
        eu, ed = raw_pairs[e_k]
        if au < ou + eu or au > 2 * (ou + eu) or ad < od + ed or ad > 2 * (od + ed):
            raise LexiconOracleError("SPLIT_SUM_MISMATCH", f"{a_k} violates quadratic Renyi-2 split conservation")

    for nk in ("ctx_r2_null", "ctx_r2_odd_null", "ctx_r2_even_null"):
        if ratios[nk] == 0:
            raise LexiconOracleError("ZERO_DENOM", f"{nk} ratio is zero")

    lift_all = ratios["ctx_r2_all"] / ratios["ctx_r2_null"]
    lift_odd = ratios["ctx_r2_odd"] / ratios["ctx_r2_odd_null"]
    lift_even = ratios["ctx_r2_even"] / ratios["ctx_r2_even_null"]

    ctx_r2_specialized = (
        lift_all >= r2_lift_min
        and lift_odd >= r2_lift_min
        and lift_even >= r2_lift_min
    )
    distinct_neighborhoods = (
        ratios["ctx_jaccard_all"] < ratios["ctx_jaccard_null"]
        and ratios["ctx_jaccard_odd"] < ratios["ctx_jaccard_odd_null"]
        and ratios["ctx_jaccard_even"] < ratios["ctx_jaccard_even_null"]
    )
    direct_coupling_enriched = (
        ratios["cooccur_all"] - abs(ratios["cooccur_null"]) >= co_margin
        and ratios["cooccur_odd"] - abs(ratios["cooccur_odd_null"]) >= co_margin
        and ratios["cooccur_even"] - abs(ratios["cooccur_even_null"]) >= co_margin
    )

    passed = ctx_r2_specialized and distinct_neighborhoods and direct_coupling_enriched

    return {
        "pairs": raw_pairs,
        "ratios_exact": {k: frac_str(v) for k, v in ratios.items()},
        "ratios_dec6": {k: format_exact_decimal(v) for k, v in ratios.items()},
        "ctx_r2_lifts_exact": {
            "all": frac_str(lift_all),
            "odd": frac_str(lift_odd),
            "even": frac_str(lift_even),
        },
        "ctx_r2_lifts_dec6": {
            "all": format_exact_decimal(lift_all),
            "odd": format_exact_decimal(lift_odd),
            "even": format_exact_decimal(lift_even),
        },
        "ctx_r2_specialized_train_and_unseen": ctx_r2_specialized,
        "distinct_neighborhoods_vs_background": distinct_neighborhoods,
        "direct_coupling_enriched_train_and_unseen": direct_coupling_enriched,
        "passed": passed,
    }


def audit_two_layer_projection_defect_exact(
    root_records,
    bg_sahih_pair,
    bg_pickthall_pair,
    min_overall_loss=Fraction(9, 20),
    min_same_lemma_loss=Fraction(3, 10),
    min_cross_minus_same=Fraction(1, 5),
):
    """Pillar 3 (Law 2b): Two-instrument continuum-vs-discrete projection defect
    with exact Same-Lemma vs Cross-Lemma (wazn-induced) partition conservation.
    """
    verify_no_floats(
        {
            "root_records": root_records,
            "bg_sahih_pair": bg_sahih_pair,
            "bg_pickthall_pair": bg_pickthall_pair,
            "min_overall_loss": min_overall_loss,
            "min_same_lemma_loss": min_same_lemma_loss,
            "min_cross_minus_same": min_cross_minus_same,
        },
        "pillar3",
    )
    m_overall = require_exact_fraction(min_overall_loss, "min_overall_loss", Fraction(0, 1), Fraction(1, 1))
    m_same = require_exact_fraction(min_same_lemma_loss, "min_same_lemma_loss", Fraction(0, 1), Fraction(1, 1))
    m_amp = require_exact_fraction(min_cross_minus_same, "min_cross_minus_same", Fraction(0, 1), Fraction(1, 1))
    bs_n, bs_d, bg_sahih = require_pair_ratio(bg_sahih_pair, "bg_sahih_pair")
    bp_n, bp_d, bg_pick = require_pair_ratio(bg_pickthall_pair, "bg_pickthall_pair")

    if not isinstance(root_records, (list, tuple)) or len(root_records) == 0:
        raise LexiconOracleError("INVALID_RECORDS", "root_records must be non-empty sequence")

    seen_roots = set()
    per_root = []
    tot_pairs = 0
    s_lost_tot = 0
    p_lost_tot = 0
    same_tot = 0
    s_same_tot = 0
    p_same_tot = 0
    cross_tot = 0
    s_cross_tot = 0
    p_cross_tot = 0
    multi_lemma_tested = 0
    multi_lemma_s_strict = 0
    multi_lemma_p_strict = 0

    for idx, rec in enumerate(root_records):
        if not isinstance(rec, dict):
            raise LexiconOracleError("INVALID_RECORD", f"record[{idx}] must be dict")
        root = require_non_empty_str(rec.get("root"), f"record[{idx}].root")
        norm = root.lower()
        if norm in seen_roots:
            raise LexiconOracleError("DUPLICATE_ROOT", f"duplicate root {root}")
        seen_roots.add(norm)

        occ = require_exact_int(rec.get("occurrences"), f"{root}.occurrences", min_value=1)
        vcnt = require_exact_int(rec.get("verse_count"), f"{root}.verse_count", min_value=1, max_value=occ)
        lems = require_exact_int(rec.get("unique_lemmas"), f"{root}.unique_lemmas", min_value=1, max_value=occ)
        s_top = require_exact_int(rec.get("sahih_top_count"), f"{root}.sahih_top_count", min_value=0, max_value=vcnt)
        p_top = require_exact_int(rec.get("pickthall_top_count"), f"{root}.pickthall_top_count", min_value=0, max_value=vcnt)

        exp_pairs = vcnt * (vcnt - 1) // 2
        same_p = require_exact_int(rec.get("same_lemma_pairs"), f"{root}.same_lemma_pairs", min_value=0, max_value=exp_pairs)
        cross_p = require_exact_int(rec.get("cross_lemma_pairs"), f"{root}.cross_lemma_pairs", min_value=0, max_value=exp_pairs)
        if same_p + cross_p != exp_pairs:
            raise LexiconOracleError("PARTITION_MISMATCH", f"{root} same+cross != expected_pairs")
        q_lem, r_lem = divmod(vcnt, lems)
        turan_min = r_lem * (q_lem + 1) * q_lem // 2 + (lems - r_lem) * q_lem * (q_lem - 1) // 2
        if same_p < turan_min:
            raise LexiconOracleError("LEMMA_MISMATCH", f"{root} same_lemma_pairs < Turan lower bound {turan_min}")

        s_same_l = require_exact_int(rec.get("sahih_same_lost"), f"{root}.sahih_same_lost", min_value=0, max_value=same_p)
        s_cross_l = require_exact_int(rec.get("sahih_cross_lost"), f"{root}.sahih_cross_lost", min_value=0, max_value=cross_p)
        p_same_l = require_exact_int(rec.get("pickthall_same_lost"), f"{root}.pickthall_same_lost", min_value=0, max_value=same_p)
        p_cross_l = require_exact_int(rec.get("pickthall_cross_lost"), f"{root}.pickthall_cross_lost", min_value=0, max_value=cross_p)

        s_min_l = exp_pairs if (vcnt >= 2 and s_top <= 1) else 0
        p_min_l = exp_pairs if (vcnt >= 2 and p_top <= 1) else 0
        s_max_l = exp_pairs - s_top * (s_top - 1) // 2
        p_max_l = exp_pairs - p_top * (p_top - 1) // 2
        s_lost = require_exact_int(rec.get("sahih_lost_pairs"), f"{root}.sahih_lost_pairs", min_value=s_min_l, max_value=s_max_l)
        p_lost = require_exact_int(rec.get("pickthall_lost_pairs"), f"{root}.pickthall_lost_pairs", min_value=p_min_l, max_value=p_max_l)

        if s_same_l + s_cross_l != s_lost or p_same_l + p_cross_l != p_lost:
            raise LexiconOracleError("PARTITION_MISMATCH", f"{root} same_lost+cross_lost != total_lost")

        entry = {
            "root": root,
            "occurrences": occ,
            "verse_count": vcnt,
            "unique_lemmas": lems,
            "sahih_top_count": s_top,
            "pickthall_top_count": p_top,
            "total_pairs": exp_pairs,
            "same_lemma_pairs": same_p,
            "cross_lemma_pairs": cross_p,
            "sahih_lost_pairs": s_lost,
            "pickthall_lost_pairs": p_lost,
            "sahih_same_lost": s_same_l,
            "sahih_cross_lost": s_cross_l,
            "pickthall_same_lost": p_same_l,
            "pickthall_cross_lost": p_cross_l,
        }
        if exp_pairs > 0:
            tot_pairs += exp_pairs
            s_lost_tot += s_lost
            p_lost_tot += p_lost
            same_tot += same_p
            s_same_tot += s_same_l
            p_same_tot += p_same_l
            cross_tot += cross_p
            s_cross_tot += s_cross_l
            p_cross_tot += p_cross_l
            s_edge = Fraction(s_lost, exp_pairs)
            p_edge = Fraction(p_lost, exp_pairs)
            entry["sahih_edge_loss_dec6"] = format_exact_decimal(s_edge)
            entry["pickthall_edge_loss_dec6"] = format_exact_decimal(p_edge)
            entry["translator_divergence_dec6"] = format_exact_decimal(abs(s_edge - p_edge))
            if same_p > 0 and cross_p > 0:
                multi_lemma_tested += 1
                s_sr = Fraction(s_same_l, same_p)
                s_cr = Fraction(s_cross_l, cross_p)
                p_sr = Fraction(p_same_l, same_p)
                p_cr = Fraction(p_cross_l, cross_p)
                if s_cr > s_sr:
                    multi_lemma_s_strict += 1
                if p_cr > p_sr:
                    multi_lemma_p_strict += 1
                entry["sahih_same_loss_dec6"] = format_exact_decimal(s_sr)
                entry["sahih_cross_loss_dec6"] = format_exact_decimal(s_cr)
                entry["pickthall_same_loss_dec6"] = format_exact_decimal(p_sr)
                entry["pickthall_cross_loss_dec6"] = format_exact_decimal(p_cr)
        per_root.append(entry)

    if tot_pairs == 0 or same_tot == 0 or cross_tot == 0 or multi_lemma_tested < 2:
        raise LexiconOracleError("INSUFFICIENT_PARTITION", "need >= 2 multi-lemma roots with same & cross pairs")

    s_overall = Fraction(s_lost_tot, tot_pairs)
    p_overall = Fraction(p_lost_tot, tot_pairs)
    s_same_pool = Fraction(s_same_tot, same_tot)
    p_same_pool = Fraction(p_same_tot, same_tot)
    s_cross_pool = Fraction(s_cross_tot, cross_tot)
    p_cross_pool = Fraction(p_cross_tot, cross_tot)

    discrete_bucket_falsified = (
        s_overall >= m_overall
        and p_overall >= m_overall
        and s_overall < bg_sahih
        and p_overall < bg_pick
    )
    intra_lemma_nonzero = s_same_pool >= m_same and p_same_pool >= m_same
    unanimous_cross_amp = (
        multi_lemma_s_strict == multi_lemma_tested
        and multi_lemma_p_strict == multi_lemma_tested
        and s_cross_pool - abs(s_same_pool) >= m_amp
        and p_cross_pool - abs(p_same_pool) >= m_amp
    )

    passed = discrete_bucket_falsified and intra_lemma_nonzero and unanimous_cross_amp

    return {
        "root_count": len(per_root),
        "bg_unrelated_sahih_pair": [bs_n, bs_d],
        "bg_unrelated_sahih_dec6": format_exact_decimal(bg_sahih),
        "bg_unrelated_pickthall_pair": [bp_n, bp_d],
        "bg_unrelated_pickthall_dec6": format_exact_decimal(bg_pick),
        "pooled_total_pairs": tot_pairs,
        "pooled_same_lemma_pairs": same_tot,
        "pooled_cross_lemma_pairs": cross_tot,
        "sahih_overall_loss_exact": frac_str(s_overall),
        "sahih_overall_loss_dec6": format_exact_decimal(s_overall),
        "pickthall_overall_loss_exact": frac_str(p_overall),
        "pickthall_overall_loss_dec6": format_exact_decimal(p_overall),
        "sahih_same_lemma_loss_exact": frac_str(s_same_pool),
        "sahih_same_lemma_loss_dec6": format_exact_decimal(s_same_pool),
        "pickthall_same_lemma_loss_exact": frac_str(p_same_pool),
        "pickthall_same_lemma_loss_dec6": format_exact_decimal(p_same_pool),
        "sahih_cross_lemma_loss_exact": frac_str(s_cross_pool),
        "sahih_cross_lemma_loss_dec6": format_exact_decimal(s_cross_pool),
        "pickthall_cross_lemma_loss_exact": frac_str(p_cross_pool),
        "pickthall_cross_lemma_loss_dec6": format_exact_decimal(p_cross_pool),
        "multi_lemma_roots_tested": multi_lemma_tested,
        "multi_lemma_sahih_strict_count": multi_lemma_s_strict,
        "multi_lemma_pickthall_strict_count": multi_lemma_p_strict,
        "discrete_bucket_falsified": discrete_bucket_falsified,
        "intra_lemma_polysemy_nonzero": intra_lemma_nonzero,
        "unanimous_cross_lemma_amplification": unanimous_cross_amp,
        "per_root": per_root,
        "passed": passed,
    }


def certify_arabic_lexicon_own_terms_gate(
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
        raise LexiconOracleError("INVALID_MODE", f"unsupported mode {clean_mode}")

    if not isinstance(pinned_sha256s, dict) or len(pinned_sha256s) == 0:
        raise LexiconOracleError("MISSING_PROVENANCE", "pinned_sha256s must be non-empty dict")
    clean_pins = {}
    for k, v in sorted(pinned_sha256s.items()):
        pk = require_non_empty_str(k, "pin_path")
        if pk.startswith("/") or "\\" in pk or ".." in pk or "://" in pk:
            raise LexiconOracleError("UNSAFE_PIN_PATH", f"unsafe pin path {pk}")
        if pk in clean_pins:
            raise LexiconOracleError("DUPLICATE_PIN_PATH", f"duplicate pin path {pk}")
        if not isinstance(v, str) or not HEX64_RE.fullmatch(v) or v == "0" * 64:
            raise LexiconOracleError("INVALID_SHA256", f"invalid sha256 for {pk}")
        clean_pins[pk] = v

    num_guard = enforce_zero_numerology_policy(feature_names)

    req_axes = (
        "wazn_agency_and_renyi2",
        "openiti_negative_controls",
        "arabic_context_topology_split_half",
        "two_layer_same_vs_cross_lemma",
        "two_translator_agreement",
    )
    if not isinstance(five_axis_checks, dict) or set(five_axis_checks.keys()) != set(req_axes):
        raise LexiconOracleError("INVALID_AXES", "five_axis_checks keys must match exact 5 axes")
    clean_axes = {}
    for ax in req_axes:
        clean_axes[ax] = require_exact_bool(five_axis_checks[ax], f"five_axis_checks.{ax}")

    if (
        not isinstance(pillar1_result, dict)
        or not isinstance(pillar2_result, dict)
        or not isinstance(pillar3_result, dict)
    ):
        raise LexiconOracleError("INVALID_PILLAR", "pillar results must be dicts")

    # LEX-BUG-05: cryptographically bind Pillar 4 to exact re-derivation of Pillars 1-3 from embedded integer payloads
    raw_ctrls = pillar1_result.get("controls_renyi2")
    if not isinstance(raw_ctrls, dict):
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar1 missing controls_renyi2 dict")
    rebuilt_ctrls = {}
    for cn, cd in raw_ctrls.items():
        if not isinstance(cd, dict):
            raise LexiconOracleError("PILLAR_CONTRADICTION", f"pillar1 control {cn} must be dict")
        rebuilt_ctrls[cn] = {
            "global_c2": cd.get("global_c2_pair"),
            "w20_obs": cd.get("w20_obs_pair"),
            "w20_t4a": cd.get("w20_t4a_pair"),
        }
    re_p1 = audit_wazn_agency_matrix_and_renyi2_exact(
        total_unique_roots=pillar1_result.get("total_unique_roots"),
        verb_roots=pillar1_result.get("verb_roots"),
        poly_wazn_roots=pillar1_result.get("poly_wazn_roots"),
        verb_tokens_i_x=pillar1_result.get("verb_tokens_i_x"),
        form_xii_tokens=pillar1_result.get("form_xii_tokens"),
        op_class_counts=pillar1_result.get("op_class_counts"),
        transition_pair_counts=pillar1_result.get("transition_pair_counts"),
        within_root_renyi2_pairs=pillar1_result.get("within_root_renyi2_pairs"),
        control_renyi2_metrics=rebuilt_ctrls,
    )
    if re_p1 != pillar1_result:
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar1_result does not match re-derived evidence")

    re_p2 = audit_context_neighborhood_topology_exact(pillar2_result.get("pairs"))
    if re_p2 != pillar2_result:
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar2_result does not match re-derived evidence")

    re_p3 = audit_two_layer_projection_defect_exact(
        root_records=pillar3_result.get("per_root"),
        bg_sahih_pair=pillar3_result.get("bg_unrelated_sahih_pair"),
        bg_pickthall_pair=pillar3_result.get("bg_unrelated_pickthall_pair"),
    )
    if re_p3 != pillar3_result:
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar3_result does not match re-derived evidence")

    expected_axes = {
        "wazn_agency_and_renyi2": re_p1["agency_matrix_nontrivial"] and re_p1["within_root_wazn_beats_nulls"],
        "openiti_negative_controls": re_p1["shared_prose_renyi2_lift"] and re_p1["poetry_higher_effective_diversity"],
        "arabic_context_topology_split_half": (
            re_p2["ctx_r2_specialized_train_and_unseen"]
            and re_p2["distinct_neighborhoods_vs_background"]
            and re_p2["direct_coupling_enriched_train_and_unseen"]
        ),
        "two_layer_same_vs_cross_lemma": (
            re_p3["intra_lemma_polysemy_nonzero"] and re_p3["unanimous_cross_lemma_amplification"]
        ),
        "two_translator_agreement": (
            re_p3["discrete_bucket_falsified"] and re_p3["unanimous_cross_lemma_amplification"]
        ),
    }
    if clean_axes != expected_axes:
        raise LexiconOracleError("AXIS_CONTRADICTION", "five_axis_checks contradicts pillar evidence")

    p1_ok = re_p1["passed"]
    p2_ok = re_p2["passed"]
    p3_ok = re_p3["passed"]
    all_axes_ok = all(clean_axes.values())
    all_passed = p1_ok and p2_ok and p3_ok and all_axes_ok and num_guard["zero_numerology_ok"]

    body = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "AUDIT-094",
        "mode": clean_mode,
        "pinned_corpus_sha256": clean_pins,
        "pinned_corpus_count": len(clean_pins),
        "zero_numerology_guard": num_guard,
        "five_axis_net_invariance": clean_axes,
        "all_five_axes_passed": all_axes_ok,
        "pillar1_wazn_agency_and_renyi2": pillar1_result,
        "pillar2_context_neighborhood_topology": pillar2_result,
        "pillar3_two_layer_projection_defect": pillar3_result,
        "verdict": "CERTIFIED_ARABIC_LEXICON_TOPOLOGY" if all_passed else "REJECTED_GATE_FAILED",
        "all_gates_passed": all_passed,
    }
    body["certificate_sha256"] = canonical_sha256(body)
    return body
