"""Exact pure-Q oracle (v2) for Classical Arabic / Qur'anic layered cohesion,
ring-vs-inclusio multi-shuffle adjudication, and 2-translator remainder.

Governance & statistical upgrades (closing review 6011346623):
- Pure Python 3 standard library only; zero floats anywhere on trust paths.
- Zero bare assert statements; fail closed with typed ArabicOracleError.
- B >= 200 deterministic multi-shuffle empirical rank p-values + exact pure-Q
  Holm-Bonferroni multiplicity correction.
- Full 12-cell per-layer null-normalized lift (retracting naive absolute-overlap
  ladder ordering).
- Honest adjudication of post-hoc boundary inclusio (never forces PASS when
  multi-shuffle null or framed-prose separation fails; drops 'strictly unseen'
  in favour of split-half internal consistency).
- Feature-naming guard explicitly labelled as a label filter, not a statistical proof.
- Explicit live_corpus_recounted boolean distinguishing live recount vs standalone
  pinned-fixture replay.
"""

from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import re
import unicodedata


SCHEMA_VERSION = "arabic-continuum-oracle/v2"
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


def require_signed_ratio_pair(pair, field):
    """Validate a signed [num, den] integer pair with den > 0 and |num| <= den."""
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        raise ArabicOracleError("INVALID_PAIR", f"{field} must be a 2-tuple of ints")
    num = require_exact_int(pair[0], f"{field}[0]")
    den = require_exact_int(pair[1], f"{field}[1]", min_value=1)
    if abs(num) > den:
        raise ArabicOracleError("INVALID_PAIR", f"{field} |num| > den")
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


def empirical_rank_p_exact(extreme_count, n_shuffles):
    """Exact pure-Q Phipson-Smyth empirical rank p = (1 + extreme) / (B + 1)."""
    b = require_exact_int(n_shuffles, "n_shuffles", min_value=1)
    ext = require_exact_int(extreme_count, "extreme_count", min_value=0, max_value=b)
    return Fraction(1 + ext, b + 1)


def holm_bonferroni_exact(p_map, alpha=DEFAULT_ALPHA):
    """Exact pure-Q step-down Holm-Bonferroni multiplicity adjustment."""
    verify_no_floats({"p_map": p_map, "alpha": alpha}, "holm")
    if not isinstance(p_map, dict) or len(p_map) == 0:
        raise ArabicOracleError("INVALID_PMAP", "p_map must be non-empty dict")
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
    prev = set(seq[0:w])
    for i in range(1, n_blocks):
        cur = set(seq[i * w:(i + 1) * w])
        inter_sum += len(prev & cur)
        union_sum += len(prev | cur)
        prev = cur
    return inter_sum, union_sum, Fraction(inter_sum, union_sum)


def enforce_zero_numerology_policy(feature_names):
    """Feature-naming label hygiene filter (NOT a statistical proof of method).

    Normalizes via NFKC, strips non-alphanumeric separators, rejects duplicates
    and any feature label containing forbidden numerology substrings.
    """
    verify_no_floats(feature_names, "feature_names")
    if not isinstance(feature_names, (list, tuple)) or len(feature_names) == 0:
        raise ArabicOracleError("INVALID_FEATURES", "feature_names must be non-empty sequence")
    seen_compact = set()
    normalized = []
    for idx, raw in enumerate(feature_names):
        name = unicodedata.normalize("NFKC", require_non_empty_str(raw, f"feature_names[{idx}]")).lower()
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
    return {
        "naming_filter_ok": True,
        "guard_scope": "feature_label_filter_only_not_statistical_proof",
        "feature_count": len(normalized),
        "features": normalized,
    }


def _validate_layer_cell(cell, field, n_shuffles):
    if not isinstance(cell, dict) or set(cell.keys()) != {"obs", "null_pooled", "ge_count"}:
        raise ArabicOracleError("INVALID_CELL", f"{field} must have obs, null_pooled, ge_count")
    oi, ou, obs_r = require_pair_ratio(cell["obs"], f"{field}.obs")
    ni, nu, null_r = require_pair_ratio(cell["null_pooled"], f"{field}.null_pooled")
    if null_r == 0:
        raise ArabicOracleError("ZERO_NULL", f"{field}.null_pooled is zero")
    ge = require_exact_int(cell["ge_count"], f"{field}.ge_count", min_value=0, max_value=n_shuffles)
    lift = obs_r / null_r
    p_emp = empirical_rank_p_exact(ge, n_shuffles)
    return {
        "obs": [oi, ou],
        "null_pooled": [ni, nu],
        "ge_count": ge,
        "obs_exact": frac_str(obs_r),
        "obs_dec6": format_exact_decimal(obs_r),
        "null_pooled_exact": frac_str(null_r),
        "null_pooled_dec6": format_exact_decimal(null_r),
        "lift_exact": frac_str(lift),
        "lift_dec6": format_exact_decimal(lift),
        "p_emp_exact": frac_str(p_emp),
        "p_emp_dec6": format_exact_decimal(p_emp),
    }, obs_r, null_r, lift, p_emp


def audit_root_pattern_lattice_and_cohesion_exact(
    unique_roots,
    unique_lemmas,
    unique_root_wazn_cells,
    total_root_tokens,
    verb_form_counts,
    window_metrics,
    control_w20_metrics,
    n_shuffles=MIN_MULTISHUFFLE_B,
    alpha=DEFAULT_ALPHA,
):
    """Pillar 1: Root-pattern lattice + full 12-cell per-layer null-normalized lift
    (B >= 200 multi-shuffle nulls + Holm-Bonferroni) & OpenITI negative controls.
    """
    verify_no_floats(
        {
            "unique_roots": unique_roots,
            "unique_lemmas": unique_lemmas,
            "unique_root_wazn_cells": unique_root_wazn_cells,
            "total_root_tokens": total_root_tokens,
            "verb_form_counts": verb_form_counts,
            "window_metrics": window_metrics,
            "control_w20_metrics": control_w20_metrics,
            "n_shuffles": n_shuffles,
            "alpha": alpha,
        },
        "pillar1",
    )
    u_roots = require_exact_int(unique_roots, "unique_roots", min_value=1)
    u_lems = require_exact_int(unique_lemmas, "unique_lemmas", min_value=1)
    u_cells = require_exact_int(unique_root_wazn_cells, "unique_root_wazn_cells", min_value=1)
    tot_tok = require_exact_int(total_root_tokens, "total_root_tokens", min_value=1)
    b_shuf = require_exact_int(n_shuffles, "n_shuffles", min_value=MIN_MULTISHUFFLE_B)
    a_val = require_exact_fraction(alpha, "alpha", Fraction(1, 1000), Fraction(1, 10))

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

    layers = ("raw", "rasm", "stem", "root")
    req_win_keys = set(layers) | {"root_t4b", "odd_split_root_t4b", "even_split_root_t4b"}

    win_report = {}
    p_map_12 = {}
    lifts_by_w = {}
    split_halves_beat_t4b_all = True
    root_beats_t4b_all = True
    for w_key in sorted(window_metrics.keys(), key=lambda x: int(x) if isinstance(x, str) and x.isdigit() else x):
        w_int = require_exact_int(int(w_key) if isinstance(w_key, str) and w_key.isdigit() else w_key, "window_key", min_value=2)
        entry = window_metrics[w_key]
        if not isinstance(entry, dict) or set(entry.keys()) != req_win_keys:
            raise ArabicOracleError("INVALID_WINDOW_ENTRY", f"window {w_int} keys mismatch")
        w_out = {}
        lifts_by_w[w_int] = {}
        for lyr in layers:
            cell_rep, _, _, lft, p_e = _validate_layer_cell(entry[lyr], f"W{w_int}.{lyr}", b_shuf)
            w_out[lyr] = cell_rep
            lifts_by_w[w_int][lyr] = lft
            p_map_12[f"W{w_int}_{lyr}"] = p_e
        # root_t4b, odd_split_root_t4b, even_split_root_t4b
        for tk in ("root_t4b", "odd_split_root_t4b", "even_split_root_t4b"):
            t_rep, _, _, _, p_t = _validate_layer_cell(entry[tk], f"W{w_int}.{tk}", b_shuf)
            w_out[tk] = t_rep
            if tk == "root_t4b":
                if entry[tk]["obs"] != entry["root"]["obs"]:
                    raise ArabicOracleError("CONSERVATION_ERROR", f"W{w_int}.root_t4b obs != root obs")
                if p_t > a_val:
                    root_beats_t4b_all = False
            elif p_t > a_val:
                split_halves_beat_t4b_all = False
        win_report[str(w_int)] = w_out

    holm_12 = holm_bonferroni_exact(p_map_12, alpha=a_val)
    all_12_beat_null_holm = all(holm_12["rejected_at_alpha"].values())
    # Finding #4 honest lift comparison: lift reverses naive absolute-overlap ladder!
    lift_reverses_absolute = all(
        lifts_by_w[w]["raw"] > lifts_by_w[w]["root"] for w in lifts_by_w
    ) and (20 not in lifts_by_w or lifts_by_w[20]["stem"] > lifts_by_w[20]["root"])

    ctrl_names = ("quran_stem", "kalila_prose", "adab_prose", "poetry_pooled")
    if not isinstance(control_w20_metrics, dict) or set(control_w20_metrics.keys()) != set(ctrl_names):
        raise ArabicOracleError("INVALID_CONTROLS", "control_w20_metrics keys mismatch")
    ctrl_report = {}
    ctrl_stats = {}
    for cn in ctrl_names:
        c_rep, obs_r, null_r, lft, p_c = _validate_layer_cell(control_w20_metrics[cn], f"ctrl.{cn}", b_shuf)
        ctrl_report[cn] = c_rep
        ctrl_stats[cn] = (obs_r, null_r, lft, p_c)

    if "20" in win_report and (
        ctrl_report["quran_stem"]["obs"] != win_report["20"]["stem"]["obs"]
        or ctrl_report["quran_stem"]["null_pooled"] != win_report["20"]["stem"]["null_pooled"]
    ):
        raise ArabicOracleError("CONTROL_MISMATCH", "quran_stem W=20 must match window_metrics[20].stem")

    shared_classical_prose = (
        ctrl_stats["quran_stem"][3] <= a_val
        and ctrl_stats["kalila_prose"][3] <= a_val
        and ctrl_stats["adab_prose"][3] <= a_val
        and ctrl_stats["kalila_prose"][2] > ctrl_stats["quran_stem"][2]
    )
    prose_exceeds_poetry = (
        ctrl_stats["quran_stem"][0] > ctrl_stats["poetry_pooled"][0]
        and ctrl_stats["kalila_prose"][0] > ctrl_stats["poetry_pooled"][0]
        and ctrl_stats["adab_prose"][0] > ctrl_stats["poetry_pooled"][0]
    )

    passed = (
        lattice_nontrivial
        and all_12_beat_null_holm
        and root_beats_t4b_all
        and split_halves_beat_t4b_all
        and lift_reverses_absolute
        and shared_classical_prose
        and prose_exceeds_poetry
    )

    return {
        "n_shuffles": b_shuf,
        "alpha_exact": frac_str(a_val),
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
        "holm_12_cells": holm_12,
        "all_12_cells_beat_null_holm": all_12_beat_null_holm,
        "root_beats_t4b_all_w": root_beats_t4b_all,
        "split_halves_beat_t4b_all_w": split_halves_beat_t4b_all,
        "lift_reverses_absolute_ladder": lift_reverses_absolute,
        "negative_controls_w20": ctrl_report,
        "shared_classical_prose_property": shared_classical_prose,
        "prose_exceeds_poetry_baseline": prose_exceeds_poetry,
        "passed": passed,
    }


def audit_ring_vs_inclusio_multishuffle_exact(
    metrics,
    n_shuffles=MIN_MULTISHUFFLE_B,
    alpha=DEFAULT_ALPHA,
):
    """Pillar 2 (Honest Multi-Shuffle Adjudication — Closing Findings #3 & #7):
    Evaluates global pointwise mirror symmetry AND post-hoc boundary inclusio
    against B >= 200 verse-permutation shuffles + Holm-Bonferroni correction.
    Never forces a PASS when boundary inclusio fails the multi-shuffle null or
    fails to separate from the framed-prose negative control.
    """
    verify_no_floats({"metrics": metrics, "n_shuffles": n_shuffles, "alpha": alpha}, "pillar2")
    b_shuf = require_exact_int(n_shuffles, "n_shuffles", min_value=MIN_MULTISHUFFLE_B)
    a_val = require_exact_fraction(alpha, "alpha", Fraction(1, 1000), Fraction(1, 10))
    if not isinstance(metrics, dict):
        raise ArabicOracleError("INVALID_METRICS", "metrics must be dict")

    req_pairs = (
        "all_mirror", "all_shift", "mirror_null_pooled",
        "all_inclusio", "all_middle",
        "odd_inclusio", "odd_middle",
        "even_inclusio", "even_middle",
        "all_strip10_inclusio", "all_strip10_middle",
        "odd_strip10_inclusio", "odd_strip10_middle",
        "even_strip10_inclusio", "even_strip10_middle",
        "kalila_arb_inclusio", "kalila_arb_middle",
        "kalila_nat_inclusio", "kalila_nat_middle",
    )
    req_delta_tests = (
        "all", "odd", "even",
        "all_strip10", "odd_strip10", "even_strip10",
        "kalila_arb", "kalila_nat",
    )
    expected_keys = set(req_pairs) | {"mirror_ge_count", "mirror_le_count", "delta_nulls"}
    if set(metrics.keys()) != expected_keys:
        raise ArabicOracleError("INVALID_METRICS", "pillar2 metrics keys mismatch")

    ratios = {}
    raw_pairs = {}
    for k in req_pairs:
        inter, union, frac = require_pair_ratio(metrics[k], f"pillar2.{k}")
        ratios[k] = frac
        raw_pairs[k] = [inter, union]

    # Exact additive split conservation (all == odd + even) for raw & strip10
    for pref in ("", "strip10_"):
        a_inc = raw_pairs[f"all_{pref}inclusio"]
        o_inc = raw_pairs[f"odd_{pref}inclusio"]
        e_inc = raw_pairs[f"even_{pref}inclusio"]
        a_mid = raw_pairs[f"all_{pref}middle"]
        o_mid = raw_pairs[f"odd_{pref}middle"]
        e_mid = raw_pairs[f"even_{pref}middle"]
        if (
            a_inc[0] != o_inc[0] + e_inc[0]
            or a_inc[1] != o_inc[1] + e_inc[1]
            or a_mid[0] != o_mid[0] + e_mid[0]
            or a_mid[1] != o_mid[1] + e_mid[1]
        ):
            raise ArabicOracleError("SPLIT_SUM_MISMATCH", f"all_{pref}inclusio/middle != odd + even")

    m_ge = require_exact_int(metrics["mirror_ge_count"], "mirror_ge_count", min_value=0, max_value=b_shuf)
    m_le = require_exact_int(metrics["mirror_le_count"], "mirror_le_count", min_value=0, max_value=b_shuf)
    if m_ge + m_le < b_shuf:
        raise ArabicOracleError("CONSERVATION_ERROR", "mirror_ge_count + mirror_le_count < n_shuffles")
    m_p_ge = empirical_rank_p_exact(m_ge, b_shuf)
    m_p_le = empirical_rank_p_exact(m_le, b_shuf)

    delta_nulls = metrics["delta_nulls"]
    if not isinstance(delta_nulls, dict) or set(delta_nulls.keys()) != set(req_delta_tests):
        raise ArabicOracleError("INVALID_DELTA_NULLS", "delta_nulls keys mismatch")

    deltas = {}
    delta_reports = {}
    quran_p_map = {}
    for dt in req_delta_tests:
        d_entry = delta_nulls[dt]
        if not isinstance(d_entry, dict) or set(d_entry.keys()) != {"ge_count", "q025", "q975"}:
            raise ArabicOracleError("INVALID_DELTA_ENTRY", f"delta_nulls.{dt} keys mismatch")
        d_val = ratios[f"{dt}_inclusio"] - ratios[f"{dt}_middle"]
        deltas[dt] = d_val
        ge = require_exact_int(d_entry["ge_count"], f"delta_nulls.{dt}.ge_count", min_value=0, max_value=b_shuf)
        q025_n, q025_d, q025_f = require_signed_ratio_pair(d_entry["q025"], f"delta_nulls.{dt}.q025")
        q975_n, q975_d, q975_f = require_signed_ratio_pair(d_entry["q975"], f"delta_nulls.{dt}.q975")
        if q025_f > q975_f:
            raise ArabicOracleError("CONSERVATION_ERROR", f"delta_nulls.{dt} q025 > q975")
        p_d = empirical_rank_p_exact(ge, b_shuf)
        delta_reports[dt] = {
            "delta_exact": frac_str(d_val),
            "delta_dec6": format_exact_decimal(d_val),
            "ge_count": ge,
            "q025": [q025_n, q025_d],
            "q975": [q975_n, q975_d],
            "q025_dec6": format_exact_decimal(q025_f),
            "q975_dec6": format_exact_decimal(q975_f),
            "p_emp_exact": frac_str(p_d),
            "p_emp_dec6": format_exact_decimal(p_d),
        }
        if not dt.startswith("kalila_"):
            quran_p_map[dt] = p_d

    holm_quran = holm_bonferroni_exact(quran_p_map, alpha=a_val)

    pointwise_mirror_falsified = (
        ratios["all_mirror"] < ratios["all_shift"]
        and ratios["all_mirror"] < ratios["mirror_null_pooled"]
        and m_p_le <= a_val
    )
    boundary_inclusio_holm_confirmed = any(holm_quran["rejected_at_alpha"].values())
    kalila_nat_p = empirical_rank_p_exact(delta_nulls["kalila_nat"]["ge_count"], b_shuf)
    all_inc_p = quran_p_map["all"]
    boundary_inclusio_separated = (
        deltas["all"] > deltas["kalila_nat"] and all_inc_p < kalila_nat_p
    )
    boundary_inclusio_status = (
        "CONFIRMED_AND_SEPARATED"
        if (boundary_inclusio_holm_confirmed and boundary_inclusio_separated)
        else "EXPLORATORY_INCONCLUSIVE_NOT_SEPARATED"
    )
    arbitrary_prose_decays = ratios["kalila_arb_inclusio"] < ratios["kalila_arb_middle"]

    honest_adjudication_passed = (
        pointwise_mirror_falsified
        and (not boundary_inclusio_holm_confirmed)
        and (not boundary_inclusio_separated)
        and arbitrary_prose_decays
    )

    return {
        "n_shuffles": b_shuf,
        "alpha_exact": frac_str(a_val),
        "pairs": raw_pairs,
        "ratios_exact": {k: frac_str(v) for k, v in ratios.items()},
        "ratios_dec6": {k: format_exact_decimal(v) for k, v in ratios.items()},
        "mirror_ge_count": m_ge,
        "mirror_le_count": m_le,
        "mirror_p_ge_exact": frac_str(m_p_ge),
        "mirror_p_ge_dec6": format_exact_decimal(m_p_ge),
        "mirror_p_le_exact": frac_str(m_p_le),
        "mirror_p_le_dec6": format_exact_decimal(m_p_le),
        "delta_null_reports": delta_reports,
        "holm_quran_inclusio": holm_quran,
        "pointwise_mirror_falsified": pointwise_mirror_falsified,
        "boundary_inclusio_holm_confirmed": boundary_inclusio_holm_confirmed,
        "boundary_inclusio_separated_from_framed_prose": boundary_inclusio_separated,
        "boundary_inclusio_status": boundary_inclusio_status,
        "arbitrary_prose_reverses_to_decay": arbitrary_prose_decays,
        "passed": honest_adjudication_passed,
    }


def audit_translation_remainder_exact(
    root_records,
    bg_sahih_pair,
    bg_pickthall_pair,
    min_pooled_edge_loss=Fraction(1, 2),
):
    """Pillar 3: Two-instrument translation remainder across author-selected thematic roots."""
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
        lems = require_exact_int(rec.get("unique_lemmas"), f"{root}.unique_lemmas", min_value=1, max_value=occ)
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
            "sahih_total_pairs": s_tot,
            "pickthall_total_pairs": p_tot,
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
        "selection_rule": "author_selected_thematic_set_disclosed",
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
    live_corpus_recounted,
    pinned_sha256s,
    feature_names,
    pillar1_result,
    pillar2_result,
    pillar3_result,
    five_axis_checks,
):
    """Pillar 4: Cryptographically bound OWN_TERMS_FIRST honest audit ledger."""
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
        raise ArabicOracleError("INVALID_MODE", f"unsupported mode {clean_mode}")
    live_flag = require_exact_bool(live_corpus_recounted, "live_corpus_recounted")
    if live_flag != (clean_mode == "live_corpus_recount"):
        raise ArabicOracleError("MODE_MISMATCH", "live_corpus_recounted contradicts mode")

    if not isinstance(pinned_sha256s, dict) or len(pinned_sha256s) == 0:
        raise ArabicOracleError("MISSING_PROVENANCE", "pinned_sha256s must be non-empty dict")
    clean_pins = {}
    for k, v in sorted(pinned_sha256s.items()):
        pk = require_non_empty_str(k, "pin_path")
        if pk.startswith("/") or "\\" in pk or ".." in pk or "://" in pk:
            raise ArabicOracleError("UNSAFE_PIN_PATH", f"unsafe pin path {pk}")
        if pk in clean_pins:
            raise ArabicOracleError("DUPLICATE_PIN_PATH", f"duplicate pin path {pk}")
        if not isinstance(v, str) or not HEX64_RE.fullmatch(v) or v == "0" * 64:
            raise ArabicOracleError("INVALID_SHA256", f"invalid sha256 for {pk}")
        clean_pins[pk] = v

    num_guard = enforce_zero_numerology_policy(feature_names)

    req_axes = (
        "per_layer_null_normalized_lift",
        "window_size_10_20_40_holm",
        "split_half_internal_consistency",
        "honest_boundary_inclusio_adjudication",
        "second_instrument_and_controls",
    )
    if not isinstance(five_axis_checks, dict) or set(five_axis_checks.keys()) != set(req_axes):
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

    # Full cryptographic re-derivation of Pillars 1-3 from embedded raw integer payloads
    raw_wm = pillar1_result.get("window_metrics")
    raw_ctrl = pillar1_result.get("negative_controls_w20")
    if not isinstance(raw_wm, dict) or not isinstance(raw_ctrl, dict):
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar1 missing window_metrics or controls")
    rebuilt_wm = {}
    for wk, wd in raw_wm.items():
        if not isinstance(wd, dict):
            raise ArabicOracleError("PILLAR_CONTRADICTION", f"pillar1 window {wk} must be dict")
        rebuilt_wm[wk] = {
            ck: {
                "obs": cd.get("obs"),
                "null_pooled": cd.get("null_pooled"),
                "ge_count": cd.get("ge_count"),
            }
            if isinstance(cd, dict)
            else None
            for ck, cd in wd.items()
        }
    rebuilt_ctrl = {
        cn: {
            "obs": cd.get("obs"),
            "null_pooled": cd.get("null_pooled"),
            "ge_count": cd.get("ge_count"),
        }
        if isinstance(cd, dict)
        else None
        for cn, cd in raw_ctrl.items()
    }
    re_p1 = audit_root_pattern_lattice_and_cohesion_exact(
        unique_roots=pillar1_result.get("unique_roots"),
        unique_lemmas=pillar1_result.get("unique_lemmas"),
        unique_root_wazn_cells=pillar1_result.get("unique_root_wazn_cells"),
        total_root_tokens=pillar1_result.get("total_root_tokens"),
        verb_form_counts=pillar1_result.get("verb_form_counts"),
        window_metrics=rebuilt_wm,
        control_w20_metrics=rebuilt_ctrl,
        n_shuffles=pillar1_result.get("n_shuffles"),
    )
    if re_p1 != pillar1_result:
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar1_result does not match re-derived evidence")

    raw_p2_pairs = pillar2_result.get("pairs")
    raw_p2_dn = pillar2_result.get("delta_null_reports")
    if not isinstance(raw_p2_pairs, dict) or not isinstance(raw_p2_dn, dict):
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar2 missing pairs or delta_null_reports")
    rebuilt_p2_in = dict(raw_p2_pairs)
    rebuilt_p2_in["mirror_ge_count"] = pillar2_result.get("mirror_ge_count")
    rebuilt_p2_in["mirror_le_count"] = pillar2_result.get("mirror_le_count")
    rebuilt_p2_in["delta_nulls"] = {
        dt: {"ge_count": dd.get("ge_count"), "q025": dd.get("q025"), "q975": dd.get("q975")}
        if isinstance(dd, dict)
        else None
        for dt, dd in raw_p2_dn.items()
    }
    re_p2 = audit_ring_vs_inclusio_multishuffle_exact(
        rebuilt_p2_in,
        n_shuffles=pillar2_result.get("n_shuffles"),
    )
    if re_p2 != pillar2_result:
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar2_result does not match re-derived evidence")

    re_p3 = audit_translation_remainder_exact(
        root_records=pillar3_result.get("per_root"),
        bg_sahih_pair=pillar3_result.get("bg_unrelated_sahih_pair"),
        bg_pickthall_pair=pillar3_result.get("bg_unrelated_pickthall_pair"),
    )
    if re_p3 != pillar3_result:
        raise ArabicOracleError("PILLAR_CONTRADICTION", "pillar3_result does not match re-derived evidence")

    expected_axes = {
        "per_layer_null_normalized_lift": re_p1["lift_reverses_absolute_ladder"] and re_p1["lattice_nontrivial"],
        "window_size_10_20_40_holm": re_p1["all_12_cells_beat_null_holm"] and re_p1["root_beats_t4b_all_w"],
        "split_half_internal_consistency": re_p1["split_halves_beat_t4b_all_w"],
        "honest_boundary_inclusio_adjudication": re_p2["passed"],
        "second_instrument_and_controls": (
            re_p1["shared_classical_prose_property"]
            and re_p1["prose_exceeds_poetry_baseline"]
            and re_p2["arbitrary_prose_reverses_to_decay"]
            and re_p3["passed"]
        ),
    }
    if clean_axes != expected_axes:
        raise ArabicOracleError("AXIS_CONTRADICTION", "five_axis_checks contradicts pillar evidence")

    all_axes_ok = all(clean_axes.values())
    all_passed = all_axes_ok

    body = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": "AUDIT-091-V2",
        "mode": clean_mode,
        "live_corpus_recounted": live_flag,
        "pinned_corpus_sha256": clean_pins,
        "pinned_corpus_count": len(clean_pins),
        "feature_naming_guard": num_guard,
        "five_axis_audit_checks": clean_axes,
        "all_five_axes_passed": all_axes_ok,
        "boundary_inclusio_status": re_p2["boundary_inclusio_status"],
        "cohesion_lift_reverses_absolute_ladder": re_p1["lift_reverses_absolute_ladder"],
        "pillar1_root_pattern_lattice": re_p1,
        "pillar2_ring_vs_inclusio_multishuffle": re_p2,
        "pillar3_translation_remainder": re_p3,
        "verdict": "AUDITED_ARABIC_CONTINUUM_HONEST_LEDGER" if all_passed else "REJECTED_GATE_FAILED",
        "all_gates_passed": all_passed,
    }
    body["certificate_sha256"] = canonical_sha256(body)
    return body
