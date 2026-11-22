"""Exact pure-Q oracle (v2) for Classical Arabic Lexical Semantic-Field Topology
& Multi-Translator Continuum Projection Defect.

Governance & statistical upgrades (closing review 6011346623):
- Pure Python 3 standard library only; zero floats anywhere on trust paths.
- Zero bare assert statements; fail closed with typed LexiconOracleError.
- B >= 200 deterministic multi-shuffle empirical rank p-values + exact pure-Q
  Holm-Bonferroni multiplicity correction across Pillars 1, 2, and 3.
- Pillar 1 within-root wazn concentration explicitly labelled as a single-corpus
  descriptive morphological measure (form_tagged_openiti_control_present: False).
- Pillar 2 odd/even splits explicitly labelled split_half_internal_consistency
  (never 'strictly unseen').
- Pillar 3 replaces post-hoc fitted thresholds (9/20, 3/10) with B >= 200
  within-root lemma-label shuffle nulls (pooled + per-root Holm-Bonferroni) AND
  exact 4-stratum verse-distance-matched controls with additive conservation.
- Explicit live_corpus_recounted boolean distinguishing live recount vs standalone
  pinned-fixture replay.
"""

from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
import math
import re
import unicodedata


SCHEMA_VERSION = "arabic-lexicon-topology-oracle/v2"
CANONICAL_DECIMALS = 6
MIN_MULTISHUFFLE_B = 250
DEFAULT_ALPHA = Fraction(1, 20)

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
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise LexiconOracleError("INVALID_PAIR", f"{field} must be a 2-tuple of ints")
    num = require_exact_int(pair[0], f"{field}[0]", min_value=0)
    den = require_exact_int(pair[1], f"{field}[1]", min_value=1)
    if num > den:
        raise LexiconOracleError("INVALID_PAIR", f"{field} num > den")
    return num, den, Fraction(num, den)


def require_signed_ratio_pair(pair, field):
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise LexiconOracleError("INVALID_PAIR", f"{field} must be a 2-tuple of ints")
    num = require_exact_int(pair[0], f"{field}[0]")
    den = require_exact_int(pair[1], f"{field}[1]", min_value=1)
    if abs(num) > den:
        raise LexiconOracleError("INVALID_PAIR", f"{field} |num| > den")
    return num, den, Fraction(num, den)


def frac_str(val):
    f = require_exact_fraction(val, "frac")
    return f"{f.numerator}/{f.denominator}"


def format_exact_decimal(val, places=CANONICAL_DECIMALS):
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


def empirical_rank_p_exact(extreme_count, n_shuffles):
    b = require_exact_int(n_shuffles, "n_shuffles", min_value=1)
    ext = require_exact_int(extreme_count, "extreme_count", min_value=0, max_value=b)
    return Fraction(1 + ext, b + 1)


def holm_bonferroni_exact(p_map, alpha=DEFAULT_ALPHA):
    verify_no_floats({"p_map": p_map, "alpha": alpha}, "holm")
    if not isinstance(p_map, dict) or len(p_map) == 0:
        raise LexiconOracleError("INVALID_PMAP", "p_map must be non-empty dict")
    a = require_exact_fraction(alpha, "alpha", Fraction(1, 1000), Fraction(1, 2))
    items = []
    for k, v in p_map.items():
        tk = require_non_empty_str(k, "test_id")
        pv = require_exact_fraction(v, f"p[{tk}]", Fraction(1, 1000000), Fraction(1, 1))
        items.append((pv, tk))
    items.sort(key=lambda pair: (pair[0], pair[1]))
    m = len(items)
    running_max = Fraction(0, 1)
    adj_exact = {}
    adj_dec6 = {}
    rejected = {}
    for rank_idx, (pv, tk) in enumerate(items):
        scaled = pv * (m - rank_idx)
        if scaled > running_max:
            running_max = scaled
        adj = Fraction(1, 1) if running_max > Fraction(1, 1) else running_max
        adj_exact[tk] = frac_str(adj)
        adj_dec6[tk] = format_exact_decimal(adj)
        rejected[tk] = adj <= a
    return {
        "test_count": m,
        "alpha_exact": frac_str(a),
        "adjusted_p_exact": adj_exact,
        "adjusted_p_dec6": adj_dec6,
        "rejected_at_alpha": rejected,
    }


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
    s = require_non_empty_str(text, "fnv1a_32.text")
    h = 2166136261
    for b in s.encode("utf-8"):
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return h


def det_shuffle_exact(items, seed):
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
    if not isinstance(seq, (list, tuple)):
        raise LexiconOracleError("INVALID_SEQ", "seq must be list or tuple")
    w = require_exact_int(window_size, "window_size", min_value=2)
    n_blocks = len(seq) // w
    if n_blocks < 2:
        raise LexiconOracleError("INSUFFICIENT_BLOCKS", "need at least 2 full windows")
    num = 0
    den = (n_blocks - 1) * w * w
    prev = Counter(seq[0:w])
    for i in range(1, n_blocks):
        cur = Counter(seq[i * w:(i + 1) * w])
        for tok in prev.keys() & cur.keys():
            num += prev[tok] * cur[tok]
        prev = cur
    return num, den, Fraction(num, den)


def enforce_zero_numerology_policy(feature_names):
    """Feature-naming label hygiene filter (NOT a statistical proof of method)."""
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
    return {
        "naming_filter_ok": True,
        "guard_scope": "feature_label_filter_only_not_statistical_proof",
        "feature_count": len(normalized),
        "features": normalized,
    }


def audit_wazn_agency_matrix_and_renyi2_exact(
    total_unique_roots,
    verb_roots,
    poly_wazn_roots,
    verb_tokens_i_x,
    form_xii_tokens,
    op_class_counts,
    transition_pair_counts,
    within_root_renyi2_pairs,
    within_root_ge_counts,
    control_renyi2_metrics,
    n_shuffles=MIN_MULTISHUFFLE_B,
    alpha=DEFAULT_ALPHA,
):
    """Pillar 1: 1,642-root x Wazn (I-X) descriptive morphological matrix (single
    corpus; no form-tagged OpenITI control) + B >= 200 OpenITI W=20 controls.
    """
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
            "within_root_ge_counts": within_root_ge_counts,
            "control_renyi2_metrics": control_renyi2_metrics,
            "n_shuffles": n_shuffles,
            "alpha": alpha,
        },
        "pillar1",
    )
    tot_roots = require_exact_int(total_unique_roots, "total_unique_roots", min_value=1)
    v_roots = require_exact_int(verb_roots, "verb_roots", min_value=1, max_value=tot_roots)
    poly_roots = require_exact_int(poly_wazn_roots, "poly_wazn_roots", min_value=1, max_value=v_roots)
    v_toks = require_exact_int(verb_tokens_i_x, "verb_tokens_i_x", min_value=v_roots + poly_roots)
    xii_toks = require_exact_int(form_xii_tokens, "form_xii_tokens", min_value=0)
    b_shuf = require_exact_int(n_shuffles, "n_shuffles", min_value=MIN_MULTISHUFFLE_B)
    a_val = require_exact_fraction(alpha, "alpha", Fraction(1, 1000), Fraction(1, 10))

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
        wr_raw["all_t4a"][1] != all_d * b_shuf
        or wr_raw["all_t4b"][1] != all_d * b_shuf
        or wr_raw["odd_t4b"][1] != odd_d * b_shuf
        or wr_raw["even_t4b"][1] != even_d * b_shuf
        or all_d * v_roots < v_toks * v_toks
        or all_d > v_toks * v_toks
        or all_d - all_u < 2 * poly_roots
        or all_d < odd_d + even_d
        or all_d > 2 * (odd_d + even_d)
        or all_u < odd_u + even_u
        or all_u > 2 * (odd_u + even_u)
    ):
        raise LexiconOracleError("CONSERVATION_ERROR", "within-root Renyi-2 conservation violated")

    req_ge = ("all_t4a", "all_t4b", "odd_t4b", "even_t4b")
    if not isinstance(within_root_ge_counts, dict) or set(within_root_ge_counts.keys()) != set(req_ge):
        raise LexiconOracleError("INVALID_GE_COUNTS", "within_root_ge_counts keys mismatch")
    wr_ge_clean = {}
    wr_p_map = {}
    for gk in req_ge:
        g = require_exact_int(within_root_ge_counts[gk], f"wr_ge.{gk}", min_value=0, max_value=b_shuf)
        wr_ge_clean[gk] = g
        wr_p_map[gk] = empirical_rank_p_exact(g, b_shuf)
    holm_wr = holm_bonferroni_exact(wr_p_map, alpha=a_val)
    wazn_beats_nulls = all(holm_wr["rejected_at_alpha"].values())

    ctrl_names = ("quran_stem", "kalila_prose", "adab_prose", "poetry_pooled")
    if not isinstance(control_renyi2_metrics, dict) or set(control_renyi2_metrics.keys()) != set(ctrl_names):
        raise LexiconOracleError("INVALID_CONTROLS", "control_renyi2_metrics keys mismatch")
    ctrl_report = {}
    ctrl_vals = {}
    for cn in ctrl_names:
        cd = control_renyi2_metrics[cn]
        if not isinstance(cd, dict) or set(cd.keys()) != {"global_c2", "w20_obs", "w20_t4a_pooled", "w20_ge_count"}:
            raise LexiconOracleError("INVALID_CONTROL_ENTRY", f"{cn} keys mismatch")
        gn, gd, g_c2 = require_pair_ratio(cd["global_c2"], f"{cn}.global_c2")
        on, od, o_r = require_pair_ratio(cd["w20_obs"], f"{cn}.w20_obs")
        nn, nd, n_r = require_pair_ratio(cd["w20_t4a_pooled"], f"{cn}.w20_t4a_pooled")
        c_ge = require_exact_int(cd["w20_ge_count"], f"{cn}.w20_ge_count", min_value=0, max_value=b_shuf)
        n_tok = math.isqrt(gd)
        if n_tok * n_tok != gd or gn < n_tok or (gn - n_tok) % 2 != 0:
            raise LexiconOracleError("CONSERVATION_ERROR", f"{cn}.global_c2 violates exact sum(c^2)/N^2 law")
        if nd != od * b_shuf:
            raise LexiconOracleError("CONSERVATION_ERROR", f"{cn} w20 pooled null denominator != obs_den * B")
        if n_r == 0:
            raise LexiconOracleError("ZERO_DENOM", f"{cn} w20_t4a_pooled is zero")
        d2 = Fraction(1, 1) / g_c2
        lift = o_r / n_r
        p_c = empirical_rank_p_exact(c_ge, b_shuf)
        ctrl_vals[cn] = (g_c2, d2, o_r, n_r, lift, p_c)
        ctrl_report[cn] = {
            "global_c2_pair": [gn, gd],
            "global_c2_dec6": format_exact_decimal(g_c2),
            "effective_d2_exact": frac_str(d2),
            "effective_d2_dec6": format_exact_decimal(d2),
            "w20_obs_pair": [on, od],
            "w20_obs_dec6": format_exact_decimal(o_r),
            "w20_t4a_pooled_pair": [nn, nd],
            "w20_t4a_pooled_dec6": format_exact_decimal(n_r),
            "w20_ge_count": c_ge,
            "w20_p_emp_exact": frac_str(p_c),
            "w20_p_emp_dec6": format_exact_decimal(p_c),
            "w20_lift_exact": frac_str(lift),
            "w20_lift_dec6": format_exact_decimal(lift),
        }

    poly_ratio = Fraction(poly_roots, v_roots)
    derived_share = Fraction(v_toks - clean_ops["GROUND_I"], v_toks)
    shared_prose_lift = (
        ctrl_vals["quran_stem"][5] <= a_val
        and ctrl_vals["kalila_prose"][5] <= a_val
        and ctrl_vals["adab_prose"][5] <= a_val
        and ctrl_vals["kalila_prose"][4] > ctrl_vals["quran_stem"][4]
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
        "n_shuffles": b_shuf,
        "alpha_exact": frac_str(a_val),
        "within_root_wazn_claim_scope": "single_corpus_descriptive_morphology",
        "form_tagged_openiti_control_present": False,
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
        "within_root_ge_counts": wr_ge_clean,
        "within_root_holm": holm_wr,
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
    n_shuffles=MIN_MULTISHUFFLE_B,
    alpha=DEFAULT_ALPHA,
):
    """Pillar 2: Native Arabic top-10-stripped co-occurrence neighborhood topology
    with B >= 200 multi-shuffle nulls, Holm-Bonferroni adjustment, and honest
    split-half internal consistency labelling.
    """
    verify_no_floats({"metrics": metrics, "n_shuffles": n_shuffles, "alpha": alpha}, "pillar2")
    b_shuf = require_exact_int(n_shuffles, "n_shuffles", min_value=MIN_MULTISHUFFLE_B)
    a_val = require_exact_fraction(alpha, "alpha", Fraction(1, 1000), Fraction(1, 10))

    req_pairs = (
        "ctx_r2_all", "ctx_r2_null_pooled",
        "ctx_r2_odd", "ctx_r2_odd_null_pooled",
        "ctx_r2_even", "ctx_r2_even_null_pooled",
        "ctx_jaccard_all", "ctx_jaccard_null_pooled",
        "ctx_jaccard_odd", "ctx_jaccard_odd_null_pooled",
        "ctx_jaccard_even", "ctx_jaccard_even_null_pooled",
        "cooccur_all", "cooccur_null_pooled",
        "cooccur_odd", "cooccur_odd_null_pooled",
        "cooccur_even", "cooccur_even_null_pooled",
    )
    req_ext = (
        "ctx_r2_all", "ctx_r2_odd", "ctx_r2_even",
        "ctx_jaccard_all", "ctx_jaccard_odd", "ctx_jaccard_even",
        "cooccur_all", "cooccur_odd", "cooccur_even",
    )
    if not isinstance(metrics, dict) or set(metrics.keys()) != (set(req_pairs) | {"extreme_counts"}):
        raise LexiconOracleError("INVALID_METRICS", "pillar2 metrics keys mismatch")

    ratios = {}
    raw_pairs = {}
    for k in req_pairs:
        n, d, r = require_pair_ratio(metrics[k], f"pillar2.{k}")
        ratios[k] = r
        raw_pairs[k] = [n, d]

    # Exact additive split conservation for direct co-occurrence (obs & B-pooled null)
    if (
        raw_pairs["cooccur_all"][0] != raw_pairs["cooccur_odd"][0] + raw_pairs["cooccur_even"][0]
        or raw_pairs["cooccur_all"][1] != raw_pairs["cooccur_odd"][1] + raw_pairs["cooccur_even"][1]
        or raw_pairs["cooccur_null_pooled"][0] != raw_pairs["cooccur_odd_null_pooled"][0] + raw_pairs["cooccur_even_null_pooled"][0]
        or raw_pairs["cooccur_null_pooled"][1] != raw_pairs["cooccur_odd_null_pooled"][1] + raw_pairs["cooccur_even_null_pooled"][1]
    ):
        raise LexiconOracleError("SPLIT_SUM_MISMATCH", "cooccur_all/null must equal odd + even")

    # Exact weighted Jaccard split conservation (obs & B-pooled null)
    for a_k, o_k, e_k in (
        ("ctx_jaccard_all", "ctx_jaccard_odd", "ctx_jaccard_even"),
        ("ctx_jaccard_null_pooled", "ctx_jaccard_odd_null_pooled", "ctx_jaccard_even_null_pooled"),
    ):
        ai, au = raw_pairs[a_k]
        oi, ou = raw_pairs[o_k]
        ei, eu = raw_pairs[e_k]
        if ai + au != (oi + ou) + (ei + eu) or ai < oi + ei or au > ou + eu:
            raise LexiconOracleError("SPLIT_SUM_MISMATCH", f"{a_k} violates weighted Jaccard split conservation")

    # Quadratic context Renyi-2 split conservation (obs & B-pooled null)
    for a_k, o_k, e_k in (
        ("ctx_r2_all", "ctx_r2_odd", "ctx_r2_even"),
        ("ctx_r2_null_pooled", "ctx_r2_odd_null_pooled", "ctx_r2_even_null_pooled"),
    ):
        au, ad = raw_pairs[a_k]
        ou, od = raw_pairs[o_k]
        eu, ed = raw_pairs[e_k]
        if au < ou + eu or au > 2 * (ou + eu) or ad < od + ed or ad > 2 * (od + ed):
            raise LexiconOracleError("SPLIT_SUM_MISMATCH", f"{a_k} violates quadratic Renyi-2 split conservation")

    for nk in ("ctx_r2_null_pooled", "ctx_r2_odd_null_pooled", "ctx_r2_even_null_pooled"):
        if ratios[nk] == 0:
            raise LexiconOracleError("ZERO_DENOM", f"{nk} ratio is zero")

    ext_in = metrics["extreme_counts"]
    if not isinstance(ext_in, dict) or set(ext_in.keys()) != set(req_ext):
        raise LexiconOracleError("INVALID_EXTREME_COUNTS", "extreme_counts keys mismatch")
    ext_clean = {}
    p_map = {}
    for ek in req_ext:
        g = require_exact_int(ext_in[ek], f"extreme_counts.{ek}", min_value=0, max_value=b_shuf)
        ext_clean[ek] = g
        p_map[ek] = empirical_rank_p_exact(g, b_shuf)

    holm_9 = holm_bonferroni_exact(p_map, alpha=a_val)

    lift_all = ratios["ctx_r2_all"] / ratios["ctx_r2_null_pooled"]
    lift_odd = ratios["ctx_r2_odd"] / ratios["ctx_r2_odd_null_pooled"]
    lift_even = ratios["ctx_r2_even"] / ratios["ctx_r2_even_null_pooled"]

    ctx_r2_specialized = (
        holm_9["rejected_at_alpha"]["ctx_r2_all"]
        and holm_9["rejected_at_alpha"]["ctx_r2_odd"]
        and holm_9["rejected_at_alpha"]["ctx_r2_even"]
        and lift_all > Fraction(1, 1)
        and lift_odd > Fraction(1, 1)
        and lift_even > Fraction(1, 1)
    )
    distinct_neighborhoods = (
        holm_9["rejected_at_alpha"]["ctx_jaccard_all"]
        and holm_9["rejected_at_alpha"]["ctx_jaccard_odd"]
        and holm_9["rejected_at_alpha"]["ctx_jaccard_even"]
        and ratios["ctx_jaccard_all"] < ratios["ctx_jaccard_null_pooled"]
        and ratios["ctx_jaccard_odd"] < ratios["ctx_jaccard_odd_null_pooled"]
        and ratios["ctx_jaccard_even"] < ratios["ctx_jaccard_even_null_pooled"]
    )
    direct_coupling_enriched = (
        holm_9["rejected_at_alpha"]["cooccur_all"]
        and holm_9["rejected_at_alpha"]["cooccur_odd"]
        and holm_9["rejected_at_alpha"]["cooccur_even"]
        and ratios["cooccur_all"] > ratios["cooccur_null_pooled"]
        and ratios["cooccur_odd"] > ratios["cooccur_odd_null_pooled"]
        and ratios["cooccur_even"] > ratios["cooccur_even_null_pooled"]
    )

    passed = ctx_r2_specialized and distinct_neighborhoods and direct_coupling_enriched

    return {
        "n_shuffles": b_shuf,
        "alpha_exact": frac_str(a_val),
        "split_half_label": "split_half_internal_consistency_not_unseen",
        "pairs": raw_pairs,
        "extreme_counts": ext_clean,
        "holm_9_tests": holm_9,
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
        "ctx_r2_specialized_split_half": ctx_r2_specialized,
        "distinct_neighborhoods_vs_background": distinct_neighborhoods,
        "direct_coupling_enriched_split_half": direct_coupling_enriched,
        "passed": passed,
    }


def audit_two_layer_projection_defect_exact(
    root_records,
    bg_sahih_pair,
    bg_pickthall_pair,
    lemma_shuffle_null,
    distance_strata,
    n_shuffles=MIN_MULTISHUFFLE_B,
    alpha=DEFAULT_ALPHA,
):
    """Pillar 3 (Closing Finding #5a & #7): Two-instrument continuum-vs-discrete
    projection defect validated against B >= 200 within-root lemma-label shuffle
    nulls AND 4-stratum verse-distance-matched controls (zero post-hoc thresholds).
    """
    verify_no_floats(
        {
            "root_records": root_records,
            "bg_sahih_pair": bg_sahih_pair,
            "bg_pickthall_pair": bg_pickthall_pair,
            "lemma_shuffle_null": lemma_shuffle_null,
            "distance_strata": distance_strata,
            "n_shuffles": n_shuffles,
            "alpha": alpha,
        },
        "pillar3",
    )
    b_shuf = require_exact_int(n_shuffles, "n_shuffles", min_value=MIN_MULTISHUFFLE_B)
    a_val = require_exact_fraction(alpha, "alpha", Fraction(1, 1000), Fraction(1, 10))
    bs_n, bs_d, bg_sahih = require_pair_ratio(bg_sahih_pair, "bg_sahih_pair")
    bp_n, bp_d, bg_pick = require_pair_ratio(bg_pickthall_pair, "bg_pickthall_pair")

    if not isinstance(root_records, (list, tuple)) or len(root_records) == 0:
        raise LexiconOracleError("INVALID_RECORDS", "root_records must be non-empty sequence")

    seen_roots = set()
    per_root = []
    tot_pairs = s_lost_tot = p_lost_tot = 0
    same_tot = s_same_tot = p_same_tot = 0
    cross_tot = s_cross_tot = p_cross_tot = 0
    ml_same_tot = ml_cross_tot = ml_s_same = ml_s_cross = ml_p_same = ml_p_cross = 0
    multi_lemma_roots = []
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
                multi_lemma_roots.append(root)
                ml_same_tot += same_p
                ml_cross_tot += cross_p
                ml_s_same += s_same_l
                ml_s_cross += s_cross_l
                ml_p_same += p_same_l
                ml_p_cross += p_cross_l
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

    multi_lemma_tested = len(multi_lemma_roots)
    if tot_pairs == 0 or same_tot == 0 or cross_tot == 0 or multi_lemma_tested < 2:
        raise LexiconOracleError("INSUFFICIENT_PARTITION", "need >= 2 multi-lemma roots with same & cross pairs")

    # Validate B >= 200 within-root lemma-label shuffle null (pooled + per-root Holm)
    req_lsn = {
        "sahih_ge_count", "pickthall_ge_count",
        "sahih_q025", "sahih_q975", "pickthall_q025", "pickthall_q975",
        "per_root_sahih_ge", "per_root_pickthall_ge",
    }
    if not isinstance(lemma_shuffle_null, dict) or set(lemma_shuffle_null.keys()) != req_lsn:
        raise LexiconOracleError("INVALID_LEMMA_NULL", "lemma_shuffle_null keys mismatch")
    ls_s_ge = require_exact_int(lemma_shuffle_null["sahih_ge_count"], "lsn.sahih_ge_count", 0, b_shuf)
    ls_p_ge = require_exact_int(lemma_shuffle_null["pickthall_ge_count"], "lsn.pickthall_ge_count", 0, b_shuf)
    sq025_n, sq025_d, sq025_f = require_signed_ratio_pair(lemma_shuffle_null["sahih_q025"], "lsn.sahih_q025")
    sq975_n, sq975_d, sq975_f = require_signed_ratio_pair(lemma_shuffle_null["sahih_q975"], "lsn.sahih_q975")
    pq025_n, pq025_d, pq025_f = require_signed_ratio_pair(lemma_shuffle_null["pickthall_q025"], "lsn.pickthall_q025")
    pq975_n, pq975_d, pq975_f = require_signed_ratio_pair(lemma_shuffle_null["pickthall_q975"], "lsn.pickthall_q975")
    if sq025_f > sq975_f or pq025_f > pq975_f:
        raise LexiconOracleError("CONSERVATION_ERROR", "lemma shuffle quantile q025 > q975")

    pr_s_ge = lemma_shuffle_null["per_root_sahih_ge"]
    pr_p_ge = lemma_shuffle_null["per_root_pickthall_ge"]
    if (
        not isinstance(pr_s_ge, dict)
        or not isinstance(pr_p_ge, dict)
        or set(pr_s_ge.keys()) != set(multi_lemma_roots)
        or set(pr_p_ge.keys()) != set(multi_lemma_roots)
    ):
        raise LexiconOracleError("INVALID_LEMMA_NULL", "per-root ge keys must match multi-lemma roots")
    pr_s_ge_clean = {}
    pr_p_ge_clean = {}
    pr_s_pmap = {}
    pr_p_pmap = {}
    for mr in multi_lemma_roots:
        gs = require_exact_int(pr_s_ge[mr], f"pr_s_ge.{mr}", 0, b_shuf)
        gp = require_exact_int(pr_p_ge[mr], f"pr_p_ge.{mr}", 0, b_shuf)
        pr_s_ge_clean[mr] = gs
        pr_p_ge_clean[mr] = gp
        pr_s_pmap[mr] = empirical_rank_p_exact(gs, b_shuf)
        pr_p_pmap[mr] = empirical_rank_p_exact(gp, b_shuf)
    holm_pr_s = holm_bonferroni_exact(pr_s_pmap, alpha=a_val)
    holm_pr_p = holm_bonferroni_exact(pr_p_pmap, alpha=a_val)

    # Validate 4-stratum verse-distance-matched control with exact additive conservation
    req_strata = ("same_surah_near", "same_surah_far", "diff_surah_near", "diff_surah_far")
    if not isinstance(distance_strata, dict) or set(distance_strata.keys()) != set(req_strata):
        raise LexiconOracleError("INVALID_STRATA", "distance_strata keys mismatch")
    strata_report = {}
    st_same_sum = st_cross_sum = st_s_same_sum = st_s_cross_sum = st_p_same_sum = st_p_cross_sum = 0
    all_strata_positive_both = True
    for sk in req_strata:
        sd = distance_strata[sk]
        req_sk = {"same_pairs", "cross_pairs", "sahih_same_lost", "sahih_cross_lost", "pickthall_same_lost", "pickthall_cross_lost"}
        if not isinstance(sd, dict) or set(sd.keys()) != req_sk:
            raise LexiconOracleError("INVALID_STRATUM_ENTRY", f"stratum {sk} keys mismatch")
        sp = require_exact_int(sd["same_pairs"], f"{sk}.same_pairs", min_value=1)
        cp = require_exact_int(sd["cross_pairs"], f"{sk}.cross_pairs", min_value=1)
        ssl = require_exact_int(sd["sahih_same_lost"], f"{sk}.sahih_same_lost", 0, sp)
        scl = require_exact_int(sd["sahih_cross_lost"], f"{sk}.sahih_cross_lost", 0, cp)
        psl = require_exact_int(sd["pickthall_same_lost"], f"{sk}.pickthall_same_lost", 0, sp)
        pcl = require_exact_int(sd["pickthall_cross_lost"], f"{sk}.pickthall_cross_lost", 0, cp)
        st_same_sum += sp
        st_cross_sum += cp
        st_s_same_sum += ssl
        st_s_cross_sum += scl
        st_p_same_sum += psl
        st_p_cross_sum += pcl
        s_gap = Fraction(scl, cp) - Fraction(ssl, sp)
        p_gap = Fraction(pcl, cp) - Fraction(psl, sp)
        if not (s_gap > 0 and p_gap > 0):
            all_strata_positive_both = False
        strata_report[sk] = {
            "same_pairs": sp,
            "cross_pairs": cp,
            "sahih_same_lost": ssl,
            "sahih_cross_lost": scl,
            "pickthall_same_lost": psl,
            "pickthall_cross_lost": pcl,
            "sahih_gap_exact": frac_str(s_gap),
            "sahih_gap_dec6": format_exact_decimal(s_gap),
            "pickthall_gap_exact": frac_str(p_gap),
            "pickthall_gap_dec6": format_exact_decimal(p_gap),
        }

    if (
        st_same_sum != ml_same_tot
        or st_cross_sum != ml_cross_tot
        or st_s_same_sum != ml_s_same
        or st_s_cross_sum != ml_s_cross
        or st_p_same_sum != ml_p_same
        or st_p_cross_sum != ml_p_cross
    ):
        raise LexiconOracleError("CONSERVATION_ERROR", "distance_strata sums != multi-lemma pooled totals")

    s_overall = Fraction(s_lost_tot, tot_pairs)
    p_overall = Fraction(p_lost_tot, tot_pairs)
    s_same_pool = Fraction(s_same_tot, same_tot)
    p_same_pool = Fraction(p_same_tot, same_tot)
    s_cross_pool = Fraction(s_cross_tot, cross_tot)
    p_cross_pool = Fraction(p_cross_tot, cross_tot)
    s_p_pooled = empirical_rank_p_exact(ls_s_ge, b_shuf)
    p_p_pooled = empirical_rank_p_exact(ls_p_ge, b_shuf)

    below_bg_both = s_overall < bg_sahih and p_overall < bg_pick
    intra_lemma_nonzero = s_same_pool > 0 and p_same_pool > 0
    lemma_shuffle_sig_both = s_p_pooled <= a_val and p_p_pooled <= a_val
    unanimous_cross_amp = (
        multi_lemma_s_strict == multi_lemma_tested
        and multi_lemma_p_strict == multi_lemma_tested
        and lemma_shuffle_sig_both
        and all_strata_positive_both
    )

    passed = below_bg_both and intra_lemma_nonzero and unanimous_cross_amp

    return {
        "n_shuffles": b_shuf,
        "alpha_exact": frac_str(a_val),
        "selection_rule": "author_selected_thematic_set_disclosed",
        "cross_lemma_gap_interpretation": "descriptive_lemma_effect_expected_in_derivational_languages_not_arabic_uniqueness",
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
        "lemma_shuffle_null": {
            "sahih_ge_count": ls_s_ge,
            "pickthall_ge_count": ls_p_ge,
            "sahih_p_emp_exact": frac_str(s_p_pooled),
            "sahih_p_emp_dec6": format_exact_decimal(s_p_pooled),
            "pickthall_p_emp_exact": frac_str(p_p_pooled),
            "pickthall_p_emp_dec6": format_exact_decimal(p_p_pooled),
            "sahih_q025": [sq025_n, sq025_d],
            "sahih_q975": [sq975_n, sq975_d],
            "sahih_q025_dec6": format_exact_decimal(sq025_f),
            "sahih_q975_dec6": format_exact_decimal(sq975_f),
            "pickthall_q025": [pq025_n, pq025_d],
            "pickthall_q975": [pq975_n, pq975_d],
            "pickthall_q025_dec6": format_exact_decimal(pq025_f),
            "pickthall_q975_dec6": format_exact_decimal(pq975_f),
            "per_root_sahih_ge": pr_s_ge_clean,
            "per_root_pickthall_ge": pr_p_ge_clean,
            "per_root_holm_sahih": holm_pr_s,
            "per_root_holm_pickthall": holm_pr_p,
        },
        "distance_strata": strata_report,
        "all_distance_strata_positive_both": all_strata_positive_both,
        "multi_lemma_roots_tested": multi_lemma_tested,
        "multi_lemma_sahih_strict_count": multi_lemma_s_strict,
        "multi_lemma_pickthall_strict_count": multi_lemma_p_strict,
        "below_background_both_translators": below_bg_both,
        "intra_lemma_polysemy_nonzero": intra_lemma_nonzero,
        "lemma_shuffle_significant_both": lemma_shuffle_sig_both,
        "unanimous_cross_lemma_amplification": unanimous_cross_amp,
        "per_root": per_root,
        "passed": passed,
    }


def certify_arabic_lexicon_own_terms_gate(
    mode,
    live_corpus_recounted,
    pinned_sha256s,
    feature_names,
    pillar1_result,
    pillar2_result,
    pillar3_result,
    five_axis_checks,
):
    """Pillar 4: Cryptographically bound OWN_TERMS_FIRST honest lexicon audit ledger."""
    verify_no_floats(
        {
            "mode": mode,
            "live_corpus_recounted": live_corpus_recounted,
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
    if clean_mode not in ("live_corpus_recount", "standalone_fixture_replay"):
        raise LexiconOracleError("INVALID_MODE", f"unsupported mode {clean_mode}")
    live_flag = require_exact_bool(live_corpus_recounted, "live_corpus_recounted")
    if live_flag != (clean_mode == "live_corpus_recount"):
        raise LexiconOracleError("MODE_MISMATCH", "live_corpus_recounted contradicts mode")

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
        "single_corpus_wazn_descriptive_renyi2",
        "openiti_negative_controls",
        "arabic_context_topology_split_half",
        "lemma_shuffle_and_distance_control",
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
            "w20_t4a_pooled": cd.get("w20_t4a_pooled_pair"),
            "w20_ge_count": cd.get("w20_ge_count"),
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
        within_root_ge_counts=pillar1_result.get("within_root_ge_counts"),
        control_renyi2_metrics=rebuilt_ctrls,
        n_shuffles=pillar1_result.get("n_shuffles"),
    )
    if re_p1 != pillar1_result:
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar1_result does not match re-derived evidence")

    raw_p2_pairs = pillar2_result.get("pairs")
    if not isinstance(raw_p2_pairs, dict):
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar2 missing pairs dict")
    rebuilt_p2 = dict(raw_p2_pairs)
    rebuilt_p2["extreme_counts"] = pillar2_result.get("extreme_counts")
    re_p2 = audit_context_neighborhood_topology_exact(
        rebuilt_p2,
        n_shuffles=pillar2_result.get("n_shuffles"),
    )
    if re_p2 != pillar2_result:
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar2_result does not match re-derived evidence")

    raw_lsn = pillar3_result.get("lemma_shuffle_null")
    raw_st = pillar3_result.get("distance_strata")
    if not isinstance(raw_lsn, dict) or not isinstance(raw_st, dict):
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar3 missing lemma_shuffle_null or distance_strata")
    rebuilt_lsn = {
        "sahih_ge_count": raw_lsn.get("sahih_ge_count"),
        "pickthall_ge_count": raw_lsn.get("pickthall_ge_count"),
        "sahih_q025": raw_lsn.get("sahih_q025"),
        "sahih_q975": raw_lsn.get("sahih_q975"),
        "pickthall_q025": raw_lsn.get("pickthall_q025"),
        "pickthall_q975": raw_lsn.get("pickthall_q975"),
        "per_root_sahih_ge": raw_lsn.get("per_root_sahih_ge"),
        "per_root_pickthall_ge": raw_lsn.get("per_root_pickthall_ge"),
    }
    rebuilt_st = {
        sk: {
            "same_pairs": sd.get("same_pairs"),
            "cross_pairs": sd.get("cross_pairs"),
            "sahih_same_lost": sd.get("sahih_same_lost"),
            "sahih_cross_lost": sd.get("sahih_cross_lost"),
            "pickthall_same_lost": sd.get("pickthall_same_lost"),
            "pickthall_cross_lost": sd.get("pickthall_cross_lost"),
        }
        if isinstance(sd, dict)
        else None
        for sk, sd in raw_st.items()
    }
    re_p3 = audit_two_layer_projection_defect_exact(
        root_records=pillar3_result.get("per_root"),
        bg_sahih_pair=pillar3_result.get("bg_unrelated_sahih_pair"),
        bg_pickthall_pair=pillar3_result.get("bg_unrelated_pickthall_pair"),
        lemma_shuffle_null=rebuilt_lsn,
        distance_strata=rebuilt_st,
        n_shuffles=pillar3_result.get("n_shuffles"),
    )
    if re_p3 != pillar3_result:
        raise LexiconOracleError("PILLAR_CONTRADICTION", "pillar3_result does not match re-derived evidence")

    expected_axes = {
        "single_corpus_wazn_descriptive_renyi2": re_p1["agency_matrix_nontrivial"] and re_p1["within_root_wazn_beats_nulls"],
        "openiti_negative_controls": re_p1["shared_prose_renyi2_lift"] and re_p1["poetry_higher_effective_diversity"],
        "arabic_context_topology_split_half": (
            re_p2["ctx_r2_specialized_split_half"]
            and re_p2["distinct_neighborhoods_vs_background"]
            and re_p2["direct_coupling_enriched_split_half"]
        ),
        "lemma_shuffle_and_distance_control": (
            re_p3["intra_lemma_polysemy_nonzero"]
            and re_p3["lemma_shuffle_significant_both"]
            and re_p3["all_distance_strata_positive_both"]
        ),
        "two_translator_agreement": (
            re_p3["below_background_both_translators"] and re_p3["unanimous_cross_lemma_amplification"]
        ),
    }
    if clean_axes != expected_axes:
        raise LexiconOracleError("AXIS_CONTRADICTION", "five_axis_checks contradicts pillar evidence")

    all_axes_ok = all(clean_axes.values())
    all_passed = all_axes_ok

    body = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "AUDIT-094-V2",
        "mode": clean_mode,
        "live_corpus_recounted": live_flag,
        "pinned_corpus_sha256": clean_pins,
        "pinned_corpus_count": len(clean_pins),
        "feature_naming_guard": num_guard,
        "five_axis_audit_checks": clean_axes,
        "all_five_axes_passed": all_axes_ok,
        "within_root_wazn_claim_scope": re_p1["within_root_wazn_claim_scope"],
        "form_tagged_openiti_control_present": re_p1["form_tagged_openiti_control_present"],
        "pillar1_wazn_agency_and_renyi2": re_p1,
        "pillar2_context_neighborhood_topology": re_p2,
        "pillar3_two_layer_projection_defect": re_p3,
        "verdict": "AUDITED_ARABIC_LEXICON_HONEST_LEDGER" if all_passed else "REJECTED_GATE_FAILED",
        "all_gates_passed": all_passed,
    }
    body["certificate_sha256"] = canonical_sha256(body)
    return body
