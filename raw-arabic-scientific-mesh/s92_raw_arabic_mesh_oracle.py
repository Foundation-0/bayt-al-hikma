"""Exact pure-Z/Q oracle for Live Raw-Arabic K_12 Scientific Mesh,
Higher-Order Translation Silo-Cut Collapse, Schur Conductance Monotonicity,
and Law-5 Dotless Rasm Homography Obstruction.

Pure Python 3 standard library only:
- Zero floats anywhere on trust paths (zero AST float literals, zero float()).
- Zero bare assert statements (fail closed with typed S92OracleError).
- Zero random module calls (100% deterministic pure-Z/Q replay).
- Explicitly credits Foundation-0/bayt-al-hikma (AUDIT-091-V2, AUDIT-094-V2,
  AUDIT-092R2, AUDIT-095R) as N0 prior art; max novelty is N1.
"""

from fractions import Fraction
import hashlib
import json
import pathlib

SCHEMA_VERSION = "bayt-al-hikma-raw-arabic-scientific-mesh/v1"
TRACK_ID = "BAYT-AL-HIKMA-RAW-ARABIC-SCIENTIFIC-MESH"
CANONICAL_DECIMALS = 6
REQUIRED_B = 250
DEFAULT_ALPHA = Fraction(1, 20)
CONDUCTANCE_SCALE = 100000
MAX_ORACLE_INT_BITS = 512

LAYERS = ("raw", "dotless_rasm", "stem_v1", "stem_v2")
EXPECTED_TREATISE_COUNT = 12
EXPECTED_DISCIPLINE_COUNT = 6
EXPECTED_EDGE_COUNT = 66
EXPECTED_TRIANGLE_COUNT = 220
EXPECTED_TETRAHEDRON_COUNT = 495
EXPECTED_FIVECELL_COUNT = 792

ALLOWED_LEAN_AXIOMS = frozenset({"propext", "Quot.sound"})
EXPECTED_LEAN_THEOREMS = (
    "RawArabicHigherOrderMesh.simplex_edge_count_doubled",
    "RawArabicHigherOrderMesh.simplex_edge_counts_k1_to_k4",
    "RawArabicHigherOrderMesh.k12_simplicial_face_counts",
    "RawArabicHigherOrderMesh.simplex_edge_strict_step",
    "RawArabicHigherOrderMesh.pow_strict_lt_of_lt",
    "RawArabicHigherOrderMesh.super_exponential_simplex_collapse",
    "RawArabicHigherOrderMesh.simplex_decay_step_amplification",
    "RawArabicHigherOrderMesh.triangle_collapse_below_half_retention",
    "RawArabicHigherOrderMesh.tetrahedron_collapse_below_half_retention",
    "RawArabicHigherOrderMesh.five_cell_collapse_below_half_retention",
    "RawArabicHigherOrderMesh.bayt_sahih_higher_order_thresholds",
    "RawArabicHigherOrderMesh.bayt_pickthall_higher_order_thresholds",
    "RawArabicHigherOrderMesh.schur_conductance_strict_thinning",
    "RawArabicHigherOrderMesh.schur_effective_resistance_inflation",
    "RawArabicHigherOrderMesh.schur_series_branch_strict_monotone",
    "RawArabicHigherOrderMesh.cross_lemma_fracture_amplification",
    "RawArabicHigherOrderMesh.rasm_homography_collision_inflation",
    "RawArabicHigherOrderMesh.rasm_lift_reversal_criterion",
)

# Pinned SHA-256 of frozen live primary-source anchor (s92_raw_arabic_anchor.json)
EXPECTED_ANCHOR_FILE_SHA256 = "eeffe3c912d8f4037b5e04cfc06abbe6fd9145802ca9009ac0a2ae184621db89"


class S92OracleError(ValueError):
    """Typed fail-closed error carrying a stable machine-readable code."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def require_ok(cond, code, message):
    if not cond:
        raise S92OracleError(code, message)


def require_exact_int(val, label, min_val=None, max_val=None):
    require_ok(type(val) is int, "INVALID_INT", f"{label} must be strict int")
    require_ok(
        val.bit_length() <= MAX_ORACLE_INT_BITS,
        "INT_BIT_LIMIT",
        f"{label} exceeds {MAX_ORACLE_INT_BITS} bits",
    )
    if min_val is not None:
        require_ok(val >= min_val, "INT_TOO_SMALL", f"{label} < {min_val}")
    if max_val is not None:
        require_ok(val <= max_val, "INT_TOO_LARGE", f"{label} > {max_val}")
    return val


def require_exact_bool(val, label):
    require_ok(type(val) is bool, "INVALID_BOOL", f"{label} must be strict bool")
    return val


def require_non_empty_str(val, label):
    require_ok(type(val) is str and len(val.strip()) > 0, "INVALID_STR", f"{label} must be non-empty str")
    return val


def require_pair_ratio(pair, label):
    require_ok(type(pair) is list and len(pair) == 2, "INVALID_PAIR", f"{label} must be 2-element list")
    num = require_exact_int(pair[0], f"{label}[0]", min_val=0)
    den = require_exact_int(pair[1], f"{label}[1]", min_val=1)
    require_ok(num <= den, "PAIR_EXCEEDS_ONE", f"{label} num > den")
    return num, den, Fraction(num, den)


def frac_str(val):
    require_ok(isinstance(val, Fraction), "INVALID_FRACTION", "expected Fraction")
    return f"{val.numerator}/{val.denominator}"


def format_exact_decimal(val, places=CANONICAL_DECIMALS):
    require_ok(isinstance(val, Fraction), "INVALID_FRACTION", "expected Fraction")
    p = require_exact_int(places, "places", min_val=0, max_val=12)
    neg = val < 0
    mag = -val if neg else val
    scale = 10 ** p
    quot, rem = divmod(mag.numerator * scale, mag.denominator)
    if rem * 2 >= mag.denominator:
        quot += 1
    prefix = "-" if (neg and quot > 0) else ""
    if p == 0:
        return f"{prefix}{quot}"
    whole, frac_part = divmod(quot, scale)
    return f"{prefix}{whole}.{frac_part:0{p}d}"


def verify_no_floats_iterative(root_obj):
    stack = [root_obj]
    while stack:
        cur = stack.pop()
        t = type(cur)
        if t is dict:
            for k, v in cur.items():
                require_ok(type(k) is str, "NON_STR_KEY", "dict key must be str")
                stack.append(v)
        elif t is list:
            for item in cur:
                stack.append(item)
        elif t is int or t is str or t is bool or cur is None:
            continue
        else:
            raise S92OracleError("FORBIDDEN_TYPE", f"forbidden type {t.__name__}")


def canonical_json_bytes(obj):
    verify_no_floats_iterative(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def canonical_sha256(obj):
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def empirical_rank_p_exact(extreme_count, n_shuffles):
    b = require_exact_int(n_shuffles, "n_shuffles", min_val=1)
    ext = require_exact_int(extreme_count, "extreme_count", min_val=0, max_val=b)
    return Fraction(1 + ext, b + 1)


def holm_bonferroni_exact(p_map, alpha=DEFAULT_ALPHA):
    require_ok(type(p_map) is dict and len(p_map) > 0, "INVALID_PMAP", "p_map must be non-empty dict")
    items = []
    for k, pv in p_map.items():
        require_non_empty_str(k, "test_id")
        require_ok(isinstance(pv, Fraction) and pv > 0 and pv <= 1, "INVALID_PVAL", f"bad p for {k}")
        items.append((pv, k))
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
        rejected[tk] = adj <= alpha
    return {
        "test_count": m,
        "alpha_exact": frac_str(alpha),
        "adjusted_p_exact": adj_exact,
        "adjusted_p_dec6": adj_dec6,
        "rejected_at_alpha": rejected,
        "rejected_count": sum(1 for v in rejected.values() if v),
    }


def _round_div_half_up(num, den):
    require_ok(den > 0 and num >= 0, "INVALID_DIV", "invalid integer division inputs")
    return (num + den // 2) // den


def exact_ldlt_inertia(matrix):
    """Exact pure-Q Sylvester LDL^T inertia [n_pos, n_neg, n_zero] for symmetric matrix."""
    n = len(matrix)
    a = [[Fraction(matrix[i][j]) for j in range(n)] for i in range(n)]
    pos = neg = zero = 0
    for k in range(n):
        piv = a[k][k]
        if piv == 0:
            # Verify rest of row/col is zero for positive semidefinite Laplacian kernel
            for j in range(k + 1, n):
                require_ok(a[k][j] == 0, "INDEFINITE_ZERO_PIVOT", f"non-zero off-diagonal at zero pivot {k}")
            zero += 1
            continue
        if piv > 0:
            pos += 1
        else:
            neg += 1
        for i in range(k + 1, n):
            factor = a[i][k] / piv
            for j in range(i, n):
                val = a[i][j] - factor * a[k][j]
                a[i][j] = val
                a[j][i] = val
            a[i][k] = Fraction(0, 1)
            a[k][i] = Fraction(0, 1)
    return [pos, neg, zero]


def exact_invert_matrix(mat):
    """Exact pure-Q Gauss-Jordan inversion of a non-singular square matrix."""
    n = len(mat)
    aug = [
        [Fraction(mat[i][j]) for j in range(n)]
        + [Fraction(1, 1) if i == j else Fraction(0, 1) for j in range(n)]
        for i in range(n)
    ]
    for col in range(n):
        piv_row = -1
        for r in range(col, n):
            if aug[r][col] != 0:
                piv_row = r
                break
        require_ok(piv_row >= 0, "SINGULAR_MATRIX", f"singular matrix at col {col}")
        if piv_row != col:
            aug[col], aug[piv_row] = aug[piv_row], aug[col]
        piv = aug[col][col]
        aug[col] = [v / piv for v in aug[col]]
        for r in range(n):
            if r != col:
                fac = aug[r][col]
                aug[r] = [aug[r][c] - fac * aug[col][c] for c in range(2 * n)]
    return [row[n:] for row in aug]


def compute_schur_mesh_exact(n_nodes, weighted_edges):
    """Exact pure-Q Laplacian inertia, grounded inverse, Foster identity, and 66/66 Schur conductance."""
    require_ok(n_nodes == EXPECTED_TREATISE_COUNT, "INVALID_NODE_COUNT", "expected K_12")
    require_ok(len(weighted_edges) == EXPECTED_EDGE_COUNT, "INVALID_EDGE_COUNT", "expected 66 edges")

    lap = [[Fraction(0, 1) for _ in range(n_nodes)] for _ in range(n_nodes)]
    for i, j, w, _ in weighted_edges:
        require_ok(w > 0, "NONPOSITIVE_WEIGHT", f"edge ({i},{j}) must have positive weight")
        wf = Fraction(w)
        lap[i][i] += wf
        lap[j][j] += wf
        lap[i][j] -= wf
        lap[j][i] -= wf

    inertia = exact_ldlt_inertia(lap)
    require_ok(inertia == [n_nodes - 1, 0, 1], "BAD_INERTIA", f"unexpected Laplacian inertia {inertia}")

    # Ground node (n_nodes - 1) and invert top-left (n-1)x(n-1) minor
    red = [[lap[i][j] for j in range(n_nodes - 1)] for i in range(n_nodes - 1)]
    inv_red = exact_invert_matrix(red)

    # Embed into n x n grounded Green's matrix G with row/col (n-1) = 0
    green = [[Fraction(0, 1) for _ in range(n_nodes)] for _ in range(n_nodes)]
    for i in range(n_nodes - 1):
        for j in range(n_nodes - 1):
            green[i][j] = inv_red[i][j]

    foster_sum = Fraction(0, 1)
    comp_ratios = []
    ceff_vals = []
    within_ceff_sum = Fraction(0, 1)
    cross_ceff_sum = Fraction(0, 1)
    within_count = 0
    cross_count = 0
    strict_compounded = 0
    edge_ceff = {}

    for i, j, w, same_disc in weighted_edges:
        r_eff = green[i][i] + green[j][j] - 2 * green[i][j]
        wf = Fraction(w)
        c_eff = Fraction(1, 1) / r_eff
        foster_sum += wf * r_eff
        ratio = c_eff / wf
        if ratio > 1:
            strict_compounded += 1
        comp_ratios.append(ratio)
        ceff_vals.append(c_eff)
        edge_ceff[(i, j)] = c_eff
        if same_disc:
            within_ceff_sum += c_eff
            within_count += 1
        else:
            cross_ceff_sum += c_eff
            cross_count += 1

    min_ceff = min(ceff_vals)
    max_ceff = max(ceff_vals)
    min_ratio = min(comp_ratios)
    max_ratio = max(comp_ratios)
    mean_ceff = (within_ceff_sum + cross_ceff_sum) / EXPECTED_EDGE_COUNT
    mean_within_ceff = within_ceff_sum / within_count
    mean_cross_ceff = cross_ceff_sum / cross_count

    return {
        "laplacian_inertia": inertia,
        "foster_sum_exact": frac_str(foster_sum),
        "strictly_compounded_edges": strict_compounded,
        "min_compounding_ratio_dec6": format_exact_decimal(min_ratio),
        "max_compounding_ratio_dec6": format_exact_decimal(max_ratio),
        "min_ceff_dec6": format_exact_decimal(min_ceff),
        "max_ceff_dec6": format_exact_decimal(max_ceff),
        "mean_ceff_dec6": format_exact_decimal(mean_ceff),
        "mean_within_discipline_ceff_dec6": format_exact_decimal(mean_within_ceff),
        "mean_cross_discipline_ceff_dec6": format_exact_decimal(mean_cross_ceff),
        "mean_ceff_frac": mean_ceff,
        "mean_within_ceff_frac": mean_within_ceff,
        "mean_cross_ceff_frac": mean_cross_ceff,
        "edge_ceff_map": edge_ceff,
    }


def compute_higher_order_simplices_k12(disciplines, edge_weight_map):
    """Exact enumeration of all 66 edges, 220 triangles, 495 tetrahedra, 792 5-cells on K_12."""
    n = len(disciplines)
    require_ok(n == EXPECTED_TREATISE_COUNT, "INVALID_K12", "expected 12 treatises")

    def summarize_order(k_verts):
        total = 0
        cross_disc = 0
        bots = []
        if k_verts == 2:
            for a in range(n):
                for b in range(a + 1, n):
                    total += 1
                    if disciplines[a] != disciplines[b]:
                        cross_disc += 1
                    bots.append(edge_weight_map[(a, b)])
        elif k_verts == 3:
            for a in range(n):
                for b in range(a + 1, n):
                    wab = edge_weight_map[(a, b)]
                    for c in range(b + 1, n):
                        total += 1
                        if len({disciplines[a], disciplines[b], disciplines[c]}) >= 2:
                            cross_disc += 1
                        bots.append(min(wab, edge_weight_map[(a, c)], edge_weight_map[(b, c)]))
        elif k_verts == 4:
            for a in range(n):
                for b in range(a + 1, n):
                    wab = edge_weight_map[(a, b)]
                    for c in range(b + 1, n):
                        wabc = min(wab, edge_weight_map[(a, c)], edge_weight_map[(b, c)])
                        for d in range(c + 1, n):
                            total += 1
                            if len({disciplines[a], disciplines[b], disciplines[c], disciplines[d]}) >= 2:
                                cross_disc += 1
                            bots.append(min(wabc, edge_weight_map[(a, d)], edge_weight_map[(b, d)], edge_weight_map[(c, d)]))
        else:
            for a in range(n):
                for b in range(a + 1, n):
                    wab = edge_weight_map[(a, b)]
                    for c in range(b + 1, n):
                        wabc = min(wab, edge_weight_map[(a, c)], edge_weight_map[(b, c)])
                        for d in range(c + 1, n):
                            wabcd = min(wabc, edge_weight_map[(a, d)], edge_weight_map[(b, d)], edge_weight_map[(c, d)])
                            for e in range(d + 1, n):
                                total += 1
                                if len({disciplines[a], disciplines[b], disciplines[c], disciplines[d], disciplines[e]}) >= 2:
                                    cross_disc += 1
                                bots.append(min(
                                    wabcd,
                                    edge_weight_map[(a, e)],
                                    edge_weight_map[(b, e)],
                                    edge_weight_map[(c, e)],
                                    edge_weight_map[(d, e)],
                                ))
        return {
            "total_simplices": total,
            "cross_discipline_simplices": cross_disc,
            "cross_discipline_share_exact": frac_str(Fraction(cross_disc, total)),
            "cross_discipline_share_dec6": format_exact_decimal(Fraction(cross_disc, total)),
            "min_bottleneck_weight": min(bots),
            "max_bottleneck_weight": max(bots),
            "mean_bottleneck_weight_dec6": format_exact_decimal(Fraction(sum(bots), total)),
        }

    k1 = summarize_order(2)
    k2 = summarize_order(3)
    k3 = summarize_order(4)
    k4 = summarize_order(5)
    return {"k1_edges": k1, "k2_triangles": k2, "k3_tetrahedra": k3, "k4_five_cells": k4}


def higher_order_retention_ladder(loss_pair, label):
    """Exact pure-Q super-exponential clique retention r^1, r^3, r^6, r^10 and loss 1 - r^C(k+1,2)."""
    lost, total, loss_frac = require_pair_ratio(loss_pair, label)
    ret = Fraction(1, 1) - loss_frac
    require_ok(ret > 0 and ret < 1, "RETENTION_OUT_OF_RANGE", f"{label} retention must lie in (0, 1)")
    out = {
        "edge_loss_pair": [lost, total],
        "edge_loss_exact": frac_str(loss_frac),
        "edge_loss_dec6": format_exact_decimal(loss_frac),
        "edge_retention_exact": frac_str(ret),
        "edge_retention_dec6": format_exact_decimal(ret),
    }
    for k, exp in ((1, 1), (2, 3), (3, 6), (4, 10)):
        surv = ret ** exp
        coll = Fraction(1, 1) - surv
        out[f"k{k}_exp{exp}_survival_dec6"] = format_exact_decimal(surv)
        out[f"k{k}_exp{exp}_collapse_dec6"] = format_exact_decimal(coll)
    return out


def build_payload_from_anchor(anchor):
    """Compute complete pure-Z/Q Raw-Arabic Scientific Mesh payload deterministically from frozen primary anchor."""
    verify_no_floats_iterative(anchor)
    require_ok(type(anchor) is dict, "INVALID_ANCHOR", "anchor must be dict")
    require_ok(anchor.get("schema_version") == "s92-raw-arabic-anchor/v1", "BAD_ANCHOR_SCHEMA", "bad anchor schema")
    b_shuf = require_exact_int(anchor.get("multishuffle_b"), "multishuffle_b", min_val=REQUIRED_B, max_val=REQUIRED_B)

    # Verify anchor internal SHA-256
    anchor_no_sha = {k: v for k, v in anchor.items() if k != "anchor_sha256"}
    calc_anchor_sha = canonical_sha256(anchor_no_sha)
    require_ok(
        anchor.get("anchor_sha256") == calc_anchor_sha,
        "ANCHOR_SHA_MISMATCH",
        "anchor internal sha256 mismatch",
    )

    # ------------------------------------------------------------------
    # Pillar 1: Live Raw-Arabic K_12 Corpus, Per-Layer Lifts, & Schur Mesh
    # ------------------------------------------------------------------
    treatises = anchor["treatises"]
    require_ok(type(treatises) is list and len(treatises) == EXPECTED_TREATISE_COUNT, "BAD_TREATISES", "need 12 treatises")
    disciplines = [require_non_empty_str(t["discipline"], "discipline") for t in treatises]
    require_ok(len(set(disciplines)) == EXPECTED_DISCIPLINE_COUNT, "BAD_DISCIPLINES", "need 6 distinct disciplines")

    total_raw_tokens = 0
    rasm_inflation_count = 0
    treatise_summaries = []
    for idx, t in enumerate(treatises):
        require_exact_int(t["index"], f"t[{idx}].index", min_val=idx, max_val=idx)
        n_tok = require_exact_int(t["token_count"], f"t[{idx}].token_count", min_val=1000)
        total_raw_tokens += n_tok
        _, _, c2_raw = require_pair_ratio(t["global_c2_pairs"]["raw"], f"t[{idx}].c2_raw")
        _, _, c2_rasm = require_pair_ratio(t["global_c2_pairs"]["dotless_rasm"], f"t[{idx}].c2_rasm")
        require_ok(c2_raw > 0, "ZERO_C2", f"t[{idx}].c2_raw == 0")
        infl = c2_rasm / c2_raw
        if c2_rasm > c2_raw:
            rasm_inflation_count += 1
        treatise_summaries.append({
            "id": require_non_empty_str(t["id"], f"t[{idx}].id"),
            "discipline": t["discipline"],
            "author": require_non_empty_str(t["author"], f"t[{idx}].author"),
            "title_en": require_non_empty_str(t["title_en"], f"t[{idx}].title_en"),
            "rel_path": require_non_empty_str(t["rel_path"], f"t[{idx}].rel_path"),
            "bytes": require_exact_int(t["bytes"], f"t[{idx}].bytes", min_val=1),
            "sha256": require_non_empty_str(t["sha256"], f"t[{idx}].sha256"),
            "token_count": n_tok,
            "vocab_raw": require_exact_int(t["vocab_sizes"]["raw"], f"t[{idx}].v_raw", min_val=1),
            "vocab_dotless_rasm": require_exact_int(t["vocab_sizes"]["dotless_rasm"], f"t[{idx}].v_rasm", min_val=1),
            "vocab_stem_v1": require_exact_int(t["vocab_sizes"]["stem_v1"], f"t[{idx}].v_s1", min_val=1),
            "vocab_stem_v2": require_exact_int(t["vocab_sizes"]["stem_v2"], f"t[{idx}].v_s2", min_val=1),
            "rasm_c2_inflation_dec6": format_exact_decimal(infl),
        })

    require_ok(rasm_inflation_count == EXPECTED_TREATISE_COUNT, "RASM_INFLATION_FAIL", "expected 12/12 rasm C2 inflation")

    # Within-treatise W=20 B=250 lifts & Holm-Bonferroni per layer
    within_w20 = anchor["within_treatise_w20_b250"]
    within_layer_summary = {}
    w20_j_lifts = {}
    w20_r2_lifts = {}
    w20_j_obs = {}
    for lyr in LAYERS:
        cells = within_w20[lyr]
        require_ok(type(cells) is dict and len(cells) == EXPECTED_TREATISE_COUNT, "BAD_W20_LAYER", f"layer {lyr}")
        oi_s = ou_s = ni_s = nu_s = r2o_s = r2od_s = r2n_s = r2nd_s = 0
        p_map_j = {}
        p_map_r2 = {}
        for t in treatises:
            tid = t["id"]
            c = cells[tid]
            oi, ou, _ = require_pair_ratio(c["jaccard_obs"], f"w20.{lyr}.{tid}.j_obs")
            ni, nu, _ = require_pair_ratio(c["jaccard_null_pooled"], f"w20.{lyr}.{tid}.j_null")
            ro, rod, _ = require_pair_ratio(c["r2_obs"], f"w20.{lyr}.{tid}.r2_obs")
            rn, rnd, _ = require_pair_ratio(c["r2_null_pooled"], f"w20.{lyr}.{tid}.r2_null")
            j_ge = require_exact_int(c["jaccard_ge_count"], f"w20.{lyr}.{tid}.j_ge", min_val=0, max_val=b_shuf)
            r_ge = require_exact_int(c["r2_ge_count"], f"w20.{lyr}.{tid}.r2_ge", min_val=0, max_val=b_shuf)
            oi_s += oi
            ou_s += ou
            ni_s += ni
            nu_s += nu
            r2o_s += ro
            r2od_s += rod
            r2n_s += rn
            r2nd_s += rnd
            p_map_j[tid] = empirical_rank_p_exact(j_ge, b_shuf)
            p_map_r2[tid] = empirical_rank_p_exact(r_ge, b_shuf)
        j_obs = Fraction(oi_s, ou_s)
        j_null = Fraction(ni_s, nu_s)
        r_obs = Fraction(r2o_s, r2od_s)
        r_null = Fraction(r2n_s, r2nd_s)
        j_lift = j_obs / j_null
        r_lift = r_obs / r_null
        w20_j_obs[lyr] = j_obs
        w20_j_lifts[lyr] = j_lift
        w20_r2_lifts[lyr] = r_lift
        holm_j = holm_bonferroni_exact(p_map_j, alpha=DEFAULT_ALPHA)
        holm_r2 = holm_bonferroni_exact(p_map_r2, alpha=DEFAULT_ALPHA)
        within_layer_summary[lyr] = {
            "pooled_jaccard_obs_dec6": format_exact_decimal(j_obs),
            "pooled_jaccard_null_dec6": format_exact_decimal(j_null),
            "pooled_jaccard_lift_dec6": format_exact_decimal(j_lift),
            "pooled_r2_obs_dec6": format_exact_decimal(r_obs),
            "pooled_r2_null_dec6": format_exact_decimal(r_null),
            "pooled_r2_lift_dec6": format_exact_decimal(r_lift),
            "holm_jaccard_rejected_count": holm_j["rejected_count"],
            "holm_r2_rejected_count": holm_r2["rejected_count"],
            "holm_jaccard_battani_p_adj_dec6": holm_j["adjusted_p_dec6"]["battani_zij"],
        }

    # Law-5 local dotless_rasm lift reversal below raw despite higher absolute overlap
    local_rasm_lift_reversed_vs_raw = (
        w20_j_obs["dotless_rasm"] > w20_j_obs["raw"]
        and w20_j_lifts["dotless_rasm"] < w20_j_lifts["raw"]
        and w20_r2_lifts["dotless_rasm"] < w20_r2_lifts["raw"]
    )
    require_ok(local_rasm_lift_reversed_vs_raw, "LOCAL_RASM_REVERSAL_FAIL", "expected local rasm lift reversal vs raw")

    # Cross-treatise K_12 4-layer mesh & B=250 vocab-label / discipline-label nulls
    k12_in = anchor["k12_cross_treatise_layers"]
    k12_layer_summary = {}
    vocab_p_map = {}
    disc_p_map = {}
    cross_abs_by_layer = {}
    cross_lift_by_layer = {}
    for lyr in LAYERS:
        kl = k12_in[lyr]
        _, _, w_r = require_pair_ratio(kl["within_discipline_pooled"], f"k12.{lyr}.within")
        _, _, c_r = require_pair_ratio(kl["cross_discipline_pooled"], f"k12.{lyr}.cross")
        _, _, top_obs = require_pair_ratio(kl["top500_obs_pooled"], f"k12.{lyr}.top_obs")
        _, _, top_null = require_pair_ratio(kl["top500_vocab_null_pooled"], f"k12.{lyr}.top_null")
        require_ok(c_r > 0 and top_null > 0, "ZERO_K12_RATE", f"k12.{lyr} zero denominator")
        v_ge = require_exact_int(kl["top500_vocab_ge_count"], f"k12.{lyr}.v_ge", min_val=0, max_val=b_shuf)
        d_ge = require_exact_int(kl["discipline_perm_ge_count"], f"k12.{lyr}.d_ge", min_val=0, max_val=b_shuf)
        v_lift = top_obs / top_null
        within_cross_ratio = w_r / c_r
        vocab_p_map[lyr] = empirical_rank_p_exact(v_ge, b_shuf)
        disc_p_map[lyr] = empirical_rank_p_exact(d_ge, b_shuf)
        cross_abs_by_layer[lyr] = c_r
        cross_lift_by_layer[lyr] = v_lift
        k12_layer_summary[lyr] = {
            "shared_vocab_size": require_exact_int(kl["shared_vocab_size"], f"k12.{lyr}.v_shared", min_val=1),
            "within_discipline_r2_dec6": format_exact_decimal(w_r),
            "cross_discipline_r2_dec6": format_exact_decimal(c_r),
            "within_to_cross_ratio_dec6": format_exact_decimal(within_cross_ratio),
            "discipline_perm_ge_count": d_ge,
            "discipline_perm_raw_p_exact": frac_str(disc_p_map[lyr]),
            "top500_obs_r2_dec6": format_exact_decimal(top_obs),
            "top500_null_r2_dec6": format_exact_decimal(top_null),
            "top500_vocab_lift_dec6": format_exact_decimal(v_lift),
            "top500_vocab_ge_count": v_ge,
        }

    holm_k12_vocab = holm_bonferroni_exact(vocab_p_map, alpha=DEFAULT_ALPHA)
    holm_k12_disc = holm_bonferroni_exact(disc_p_map, alpha=DEFAULT_ALPHA)
    require_ok(holm_k12_vocab["rejected_count"] == 4, "K12_VOCAB_HOLM_FAIL", "all 4 layers must beat B=250 vocab null")

    # Exact bayt-al-hikma#9 full 4-layer cross-treatise lift reversal vs naive absolute ordering
    cross_treatise_full_lift_reversal = (
        cross_abs_by_layer["raw"] < cross_abs_by_layer["dotless_rasm"]
        and cross_abs_by_layer["dotless_rasm"] < cross_abs_by_layer["stem_v1"]
        and cross_abs_by_layer["stem_v1"] < cross_abs_by_layer["stem_v2"]
        and cross_lift_by_layer["raw"] > cross_lift_by_layer["dotless_rasm"]
        and cross_lift_by_layer["dotless_rasm"] > cross_lift_by_layer["stem_v1"]
        and cross_lift_by_layer["stem_v1"] > cross_lift_by_layer["stem_v2"]
    )
    require_ok(
        cross_treatise_full_lift_reversal,
        "CROSS_LIFT_REVERSAL_FAIL",
        "expected full 4-layer cross-treatise lift reversal",
    )

    # Exact K_12 weighted Laplacian & Schur compounding on empirical raw-Arabic stem_v1 mesh
    s1_edges = k12_in["stem_v1"]["edges"]
    require_ok(len(s1_edges) == EXPECTED_EDGE_COUNT, "BAD_S1_EDGES", "need 66 stem_v1 edges")
    weighted_edges_raw = []
    edge_weight_map = {}
    within_edge_count = 0
    cross_edge_count = 0
    for e in s1_edges:
        i = require_exact_int(e["i"], "edge.i", min_val=0, max_val=11)
        j = require_exact_int(e["j"], "edge.j", min_val=0, max_val=11)
        require_ok(i < j, "EDGE_ORDER", "edge i must be < j")
        dot = require_exact_int(e["content_dot"], "edge.dot", min_val=1)
        den = require_exact_int(e["content_den"], "edge.den", min_val=1)
        sd = require_exact_bool(e["same_discipline"], "edge.same_discipline")
        w_int = max(1, _round_div_half_up(dot * CONDUCTANCE_SCALE, den))
        weighted_edges_raw.append((i, j, w_int, sd))
        edge_weight_map[(i, j)] = w_int
        if sd:
            within_edge_count += 1
    require_ok(within_edge_count == 10, "BAD_DISC_SPLIT", "expected 10 within-discipline edges")

    schur_raw_arabic = compute_schur_mesh_exact(EXPECTED_TREATISE_COUNT, weighted_edges_raw)
    simplices_k12 = compute_higher_order_simplices_k12(disciplines, edge_weight_map)

    # ------------------------------------------------------------------
    # Pillar 2: Algorithmic Bridges, Disclosed 8 Thematic Roots, Law-5 Rasm
    # ------------------------------------------------------------------
    alg = anchor["algorithmic_cross_discipline_bridges"]
    qual_stems = require_exact_int(alg["qualifying_stem_v1_count"], "qualifying_stem_v1_count", min_val=100)

    thematic_in = anchor["thematic_root_probes"]["roots"]
    require_ok(type(thematic_in) is list and len(thematic_in) == 8, "BAD_THEMATIC_ROOTS", "need 8 thematic roots")
    thematic_summary = []
    universal_12_count = 0
    honest_partial_count = 0
    for r in thematic_in:
        s1_tot = require_exact_int(r["stem_v1_total"], "root.s1_tot", min_val=1)
        s1_docs = require_exact_int(r["stem_v1_docs"], "root.s1_docs", min_val=1, max_val=12)
        s1_discs = require_exact_int(r["stem_v1_disciplines"], "root.s1_discs", min_val=1, max_val=6)
        s2_tot = require_exact_int(r["stem_v2_total"], "root.s2_tot", min_val=1)
        s2_docs = require_exact_int(r["stem_v2_docs"], "root.s2_docs", min_val=1, max_val=12)
        vec_s1 = r["stem_v1_counts"]
        require_ok(type(vec_s1) is list, "ROOT_VEC_TYPE", "s1 vec must be list")
        require_ok(len(vec_s1) == 12, "ROOT_VEC_LEN", "s1 vec len != 12")
        require_ok(sum(vec_s1) == s1_tot, "ROOT_CONSERVATION", "s1 sum mismatch")
        if s1_docs == 12:
            universal_12_count += 1
        else:
            honest_partial_count += 1
        thematic_summary.append({
            "root_key": require_non_empty_str(r["root_key"], "root_key"),
            "stem_v1_total": s1_tot,
            "stem_v1_docs": s1_docs,
            "stem_v1_disciplines": s1_discs,
            "stem_v2_total": s2_tot,
            "stem_v2_docs": s2_docs,
            "zero_treatises_s1_count": 12 - s1_docs,
            "universal_all_12_s1": s1_docs == 12,
        })
    require_ok(honest_partial_count >= 1, "NO_HONEST_PARTIAL_ROOT", "expected honest non-universal root falsification")

    rasm_in = anchor["rasm_homography_witnesses"]
    require_ok(type(rasm_in) is list and len(rasm_in) == 10, "BAD_RASM_WITNESSES", "need 10 rasm witnesses")
    rasm_verified = 0
    total_top10_delta_s2 = 0
    for w in rasm_in:
        ms = require_exact_int(w["merged_sum"], "rasm.merged_sum", min_val=2)
        ssq = require_exact_int(w["sum_of_squares"], "rasm.sum_of_squares", min_val=2)
        exc = require_exact_int(w["collision_excess_delta_s2"], "rasm.excess", min_val=1)
        require_ok(ms * ms - ssq == exc, "RASM_ALGEBRA_MISMATCH", "ms^2 - ssq != excess")
        rasm_verified += 1
        total_top10_delta_s2 += exc

    # ------------------------------------------------------------------
    # Pillar 3: Higher-Order Translation Silo-Cut Theorem & Bilingual Catalogs
    # ------------------------------------------------------------------
    bp = anchor["bayt_prior_art"]
    bayt_ladders = {
        "sahih_7root": higher_order_retention_ladder(bp["sahih_7root_edge_loss_pair"], "sahih_7root"),
        "pickthall_7root": higher_order_retention_ladder(bp["pickthall_7root_edge_loss_pair"], "pickthall_7root"),
        "sahih_15root_same_lemma": higher_order_retention_ladder(bp["sahih_15root_same_loss_pair"], "sahih_same"),
        "sahih_15root_cross_lemma": higher_order_retention_ladder(bp["sahih_15root_cross_loss_pair"], "sahih_cross"),
        "pickthall_15root_same_lemma": higher_order_retention_ladder(bp["pickthall_15root_same_loss_pair"], "pick_same"),
        "pickthall_15root_cross_lemma": higher_order_retention_ladder(bp["pickthall_15root_cross_loss_pair"], "pick_cross"),
    }

    # Live bilingual parallel scientific catalogs (148 entries, 6 sensitivity variants)
    bi = anchor["bilingual_scientific_catalogs"]
    require_exact_int(bi["catalog_count"], "bi.catalog_count", min_val=12, max_val=12)
    require_exact_int(bi["entry_count"], "bi.entry_count", min_val=148, max_val=148)
    sweep_in = bi["sensitivity_sweep"]
    require_ok(type(sweep_in) is dict and len(sweep_in) == 6, "BAD_BI_SWEEP", "expected 6 sensitivity variants")

    bi_reports = {}
    bi_p_map = {}
    overall_losses = []
    cross_losses = []
    for vkey in sorted(sweep_in.keys()):
        v = sweep_in[vkey]
        ar_l = require_exact_int(v["ar_linked_pairs"], f"bi.{vkey}.ar", min_val=1)
        en_lost = require_exact_int(v["en_lost_pairs"], f"bi.{vkey}.en_lost", min_val=1, max_val=ar_l - 1)
        cr_ar = require_exact_int(v["cross_disc_ar_pairs"], f"bi.{vkey}.cr_ar", min_val=1)
        cr_lost = require_exact_int(v["cross_disc_en_lost"], f"bi.{vkey}.cr_lost", min_val=1, max_val=cr_ar - 1)
        _, _, bg_r = require_pair_ratio(v["all_pairs_bg_en_lost"], f"bi.{vkey}.bg")
        ple = require_exact_int(v["en_perm_le_obs_count"], f"bi.{vkey}.ple", min_val=0, max_val=b_shuf)
        ov_f = Fraction(en_lost, ar_l)
        cr_f = Fraction(cr_lost, cr_ar)
        require_ok(ov_f < bg_r, "BI_ABOVE_BG", f"{vkey} loss >= background")
        require_ok(cr_f > ov_f, "BI_CROSS_NOT_WORSE", f"{vkey} cross-discipline loss <= overall")
        overall_losses.append(ov_f)
        cross_losses.append(cr_f)
        bi_p_map[vkey] = empirical_rank_p_exact(ple, b_shuf)
        bi_reports[vkey] = {
            "overall_ladder": higher_order_retention_ladder([en_lost, ar_l], f"bi.{vkey}.overall"),
            "cross_disc_ladder": higher_order_retention_ladder([cr_lost, cr_ar], f"bi.{vkey}.cross"),
            "bg_en_loss_dec6": format_exact_decimal(bg_r),
            "en_perm_le_obs_count": ple,
        }

    holm_bilingual = holm_bonferroni_exact(bi_p_map, alpha=DEFAULT_ALPHA)
    require_ok(holm_bilingual["rejected_count"] == 6, "BI_HOLM_FAIL", "all 6 bilingual variants must beat null")

    # Exact Schur Conductance Collapse on live K_12 empirical Arabic scientific mesh:
    # 1. Uniform English thinning at Sahih, Pickthall, and primary bilingual catalog rate
    r_sahih = Fraction(1, 1) - Fraction(*bp["sahih_7root_edge_loss_pair"])
    r_pick = Fraction(1, 1) - Fraction(*bp["pickthall_7root_edge_loss_pair"])
    v_primary = sweep_in["stem_v1__en_pr_min4"]
    r_cat_overall = Fraction(v_primary["ar_linked_pairs"] - v_primary["en_lost_pairs"], v_primary["ar_linked_pairs"])
    # Within-discipline vs cross-discipline empirical retention on primary bilingual catalog
    within_ar_bi = v_primary["ar_linked_pairs"] - v_primary["cross_disc_ar_pairs"]
    within_lost_bi = v_primary["en_lost_pairs"] - v_primary["cross_disc_en_lost"]
    r_cat_within = Fraction(within_ar_bi - within_lost_bi, within_ar_bi)
    r_cat_cross = Fraction(v_primary["cross_disc_ar_pairs"] - v_primary["cross_disc_en_lost"], v_primary["cross_disc_ar_pairs"])

    # 2. Exact heterogeneous silo-cut Schur recomputation on empirical K_12 mesh:
    #    Scale within-discipline edge weights by r_cat_within and cross-discipline weights by r_cat_cross!
    weighted_edges_silo = [
        (i, j, Fraction(w) * (r_cat_within if sd else r_cat_cross), sd)
        for i, j, w, sd in weighted_edges_raw
    ]
    schur_silo_thinned = compute_schur_mesh_exact(EXPECTED_TREATISE_COUNT, weighted_edges_silo)

    silo_strictly_collapsed_edges = sum(
        1
        for i, j, _, _ in weighted_edges_raw
        if schur_silo_thinned["edge_ceff_map"][(i, j)] < schur_raw_arabic["edge_ceff_map"][(i, j)]
    )

    cross_ceff_retention = (
        schur_silo_thinned["mean_cross_ceff_frac"] / schur_raw_arabic["mean_cross_ceff_frac"]
    )
    within_ceff_retention = (
        schur_silo_thinned["mean_within_ceff_frac"] / schur_raw_arabic["mean_within_ceff_frac"]
    )
    overall_ceff_retention = (
        schur_silo_thinned["mean_ceff_frac"] / schur_raw_arabic["mean_ceff_frac"]
    )

    schur_collapse_summary = {
        "raw_arabic_k12": {k: v for k, v in schur_raw_arabic.items() if not k.endswith("_frac") and k != "edge_ceff_map"},
        "uniform_sahih_thinning": {
            "retention_exact": frac_str(r_sahih),
            "retention_dec6": format_exact_decimal(r_sahih),
            "mean_ceff_dec6": format_exact_decimal(schur_raw_arabic["mean_ceff_frac"] * r_sahih),
            "effective_resistance_inflation_dec6": format_exact_decimal(Fraction(1, 1) / r_sahih),
        },
        "uniform_pickthall_thinning": {
            "retention_exact": frac_str(r_pick),
            "retention_dec6": format_exact_decimal(r_pick),
            "mean_ceff_dec6": format_exact_decimal(schur_raw_arabic["mean_ceff_frac"] * r_pick),
            "effective_resistance_inflation_dec6": format_exact_decimal(Fraction(1, 1) / r_pick),
        },
        "uniform_bilingual_catalog_thinning": {
            "retention_exact": frac_str(r_cat_overall),
            "retention_dec6": format_exact_decimal(r_cat_overall),
            "mean_ceff_dec6": format_exact_decimal(schur_raw_arabic["mean_ceff_frac"] * r_cat_overall),
            "effective_resistance_inflation_dec6": format_exact_decimal(Fraction(1, 1) / r_cat_overall),
        },
        "heterogeneous_english_silo_cut_k12": {
            "within_edge_retention_exact": frac_str(r_cat_within),
            "within_edge_retention_dec6": format_exact_decimal(r_cat_within),
            "cross_edge_retention_exact": frac_str(r_cat_cross),
            "cross_edge_retention_dec6": format_exact_decimal(r_cat_cross),
            "laplacian_inertia": schur_silo_thinned["laplacian_inertia"],
            "foster_sum_exact": schur_silo_thinned["foster_sum_exact"],
            "strictly_collapsed_edges": silo_strictly_collapsed_edges,
            "mean_ceff_dec6": schur_silo_thinned["mean_ceff_dec6"],
            "mean_within_ceff_dec6": schur_silo_thinned["mean_within_discipline_ceff_dec6"],
            "mean_cross_ceff_dec6": schur_silo_thinned["mean_cross_discipline_ceff_dec6"],
            "overall_ceff_collapse_dec6": format_exact_decimal(Fraction(1, 1) - overall_ceff_retention),
            "within_ceff_collapse_dec6": format_exact_decimal(Fraction(1, 1) - within_ceff_retention),
            "cross_ceff_collapse_dec6": format_exact_decimal(Fraction(1, 1) - cross_ceff_retention),
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "track_id": TRACK_ID,
        "novelty_classification": {
            "prior_art_n0": "Foundation-0/bayt-al-hikma (AUDIT-091-V2, AUDIT-094-V2, AUDIT-092R2, AUDIT-095R)",
            "max_novelty": "N1",
            "n2_claims_count": 0,
            "methodology": "OWN_TERMS_FIRST_PURE_ARABIC_PRIMARY_TEXTS",
        },
        "anchor_pin": {
            "anchor_schema_version": anchor["schema_version"],
            "anchor_internal_sha256": calc_anchor_sha,
            "multishuffle_b": b_shuf,
            "local_window_w": anchor["local_window_w"],
            "matched_local_tokens": anchor["matched_local_tokens"],
            "top_func_stripped_count": anchor["top_func_stripped_count"],
        },
        "n0_bayt_al_hikma_prior_art": {
            "continuum_audit_id": bp["continuum_audit_id"],
            "continuum_cert_file_sha256": bp["continuum_cert_file_sha256"],
            "continuum_cert_internal_sha256": bp["continuum_cert_internal_sha256"],
            "lexicon_audit_id": bp["lexicon_audit_id"],
            "lexicon_cert_file_sha256": bp["lexicon_cert_file_sha256"],
            "lexicon_cert_internal_sha256": bp["lexicon_cert_internal_sha256"],
            "higher_order_collapse_ladders": bayt_ladders,
        },
        "pillar1_raw_arabic_k12_mesh": {
            "treatise_count": EXPECTED_TREATISE_COUNT,
            "discipline_count": EXPECTED_DISCIPLINE_COUNT,
            "total_raw_arabic_tokens": total_raw_tokens,
            "rasm_c2_inflation_treatises": rasm_inflation_count,
            "treatises": treatise_summaries,
            "within_treatise_w20_b250": within_layer_summary,
            "local_dotless_rasm_lift_reversed_vs_raw": local_rasm_lift_reversed_vs_raw,
            "k12_cross_treatise_layers": k12_layer_summary,
            "holm_k12_vocab_null_4layers": holm_k12_vocab,
            "holm_k12_discipline_perm_4layers": holm_k12_disc,
            "cross_treatise_full_4layer_lift_reversal": cross_treatise_full_lift_reversal,
            "k12_simplicial_complex": simplices_k12,
            "schur_conductance_and_silo_collapse": schur_collapse_summary,
        },
        "pillar2_bridges_and_law5_obstruction": {
            "algorithmic_qualifying_stem_v1_count": qual_stems,
            "thematic_selection_rule": anchor["thematic_root_probes"]["selection_rule"],
            "thematic_root_count": len(thematic_summary),
            "thematic_universal_12_of_12_count": universal_12_count,
            "thematic_honest_partial_count": honest_partial_count,
            "thematic_roots": thematic_summary,
            "rasm_homography_witnesses_verified": rasm_verified,
            "rasm_top10_total_delta_s2": total_top10_delta_s2,
        },
        "pillar3_bilingual_scientific_catalogs": {
            "catalog_count": bi["catalog_count"],
            "entry_count": bi["entry_count"],
            "overall_loss_min_dec6": format_exact_decimal(min(overall_losses)),
            "overall_loss_max_dec6": format_exact_decimal(max(overall_losses)),
            "cross_disc_loss_min_dec6": format_exact_decimal(min(cross_losses)),
            "cross_disc_loss_max_dec6": format_exact_decimal(max(cross_losses)),
            "holm_6_variants": holm_bilingual,
            "sensitivity_variants": bi_reports,
        },
        "lean_companion_spec": {
            "lean_file": "RawArabicHigherOrderMesh.lean",
            "theorem_count": len(EXPECTED_LEAN_THEOREMS),
            "allowed_axioms": sorted(ALLOWED_LEAN_AXIOMS),
            "theorems": list(EXPECTED_LEAN_THEOREMS),
        },
        "all_gates_passed": True,
        "verdict": "S92_RAW_ARABIC_K12_MESH_AND_SILO_COLLAPSE_CERTIFIED",
    }


def load_anchor_from_path(anchor_path):
    p = pathlib.Path(anchor_path)
    raw = p.read_bytes()
    return json.loads(raw.decode("utf-8"))


def build_certificate(anchor=None, anchor_path=None):
    if anchor is None:
        if anchor_path is None:
            anchor_path = pathlib.Path(__file__).resolve().parent / "s92_raw_arabic_anchor.json"
        anchor = load_anchor_from_path(anchor_path)
    payload = build_payload_from_anchor(anchor)
    payload_sha = canonical_sha256(payload)
    cert_body = {
        "schema": SCHEMA_VERSION,
        "track_id": TRACK_ID,
        "payload_sha256": payload_sha,
        "payload": payload,
    }
    cert_sha = canonical_sha256(cert_body)
    cert = dict(cert_body)
    cert["certificate_sha256"] = cert_sha
    return cert
