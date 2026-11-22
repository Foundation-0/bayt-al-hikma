"""Assertion-free R5 mutation-hardened & red-team test suite for AUDIT-094.

Runs cleanly under:
  python3 -I -O -B -W error test_arabic_lexicon_r5.py
  aletheia v2.0.0 mutate arabic_lexicon_oracle.py --max-mutants 0 --add-cwd
  aletheia v2.0.0 mutate arabic_lexicon_audit.py --max-mutants 0 --add-cwd

Zero bare assert statements. Zero floats on trust paths. Zero external writes.
"""

import copy
from fractions import Fraction
import io
import json
import os
import subprocess
import sys
import tempfile

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import arabic_lexicon_audit as audit
import arabic_lexicon_oracle as oracle


EXPECTED_STANDALONE_SHA = (
    "a96fda1ccfa0a41ae6ed07d7767cff61c754b3853ae1df49977ca1cda1c14712"
)


def check(cond, msg):
    if not cond:
        raise RuntimeError(f"CHECK_FAILED: {msg}")


def expect_error(fn, expected_code):
    try:
        fn()
    except oracle.LexiconOracleError as err:
        if err.code != expected_code:
            raise RuntimeError(f"Expected {expected_code}, got {err.code}: {err}")
        return
    raise RuntimeError(f"Expected LexiconOracleError({expected_code}), but succeeded")


def test_primitives_and_text_nets():
    check(oracle.SCHEMA_VERSION == "arabic-lexicon-topology-oracle/v1", "schema")
    check(oracle.CANONICAL_DECIMALS == 6, "decimals")

    # verify_no_floats
    oracle.verify_no_floats({"a": [1, (Fraction(1, 2), {3}, frozenset({4}))]})
    expect_error(lambda: oracle.verify_no_floats(0.5), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats(1 + 2j), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats({1.5: "x"}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats({"x": [2.0]}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats(frozenset({3.14})), "FLOAT_FORBIDDEN")

    # require_non_empty_str
    check(oracle.require_non_empty_str("  hello ~ ", "f") == "hello ~", "strip")
    expect_error(lambda: oracle.require_non_empty_str(123, "f"), "INVALID_TYPE")
    expect_error(lambda: oracle.require_non_empty_str("   ", "f"), "EMPTY_STRING")
    expect_error(lambda: oracle.require_non_empty_str("a\x1fb", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("a\x7fb", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("abc\n", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("ab\u200bjad", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("\ufeffabc", "f"), "CONTROL_CHAR")

    # require_exact_bool / int / fraction / pair
    check(oracle.require_exact_bool(True, "b") is True, "bool true")
    expect_error(lambda: oracle.require_exact_bool(1, "b"), "INVALID_BOOL")
    check(oracle.require_exact_int(5, "i", 5, 5) == 5, "int exact")
    expect_error(lambda: oracle.require_exact_int(True, "i"), "INVALID_INT")
    expect_error(lambda: oracle.require_exact_int(4, "i", min_value=5), "RANGE_ERROR")
    expect_error(lambda: oracle.require_exact_int(6, "i", max_value=5), "RANGE_ERROR")
    check(oracle.require_exact_fraction(3, "q") == Fraction(3, 1), "int frac")
    check(oracle.require_exact_fraction(Fraction(1, 2), "q", Fraction(1, 2), Fraction(1, 2)) == Fraction(1, 2), "frac exact")
    expect_error(lambda: oracle.require_exact_fraction(False, "q"), "INVALID_FRACTION")
    expect_error(lambda: oracle.require_exact_fraction("1/2", "q"), "INVALID_FRACTION")
    expect_error(lambda: oracle.require_exact_fraction(Fraction(1, 3), "q", min_value=Fraction(1, 2)), "RANGE_ERROR")
    expect_error(lambda: oracle.require_exact_fraction(Fraction(2, 3), "q", max_value=Fraction(1, 2)), "RANGE_ERROR")
    check(oracle.require_pair_ratio([0, 1], "p") == (0, 1, Fraction(0, 1)), "pair zero")
    check(oracle.require_pair_ratio((3, 3), "p") == (3, 3, Fraction(1, 1)), "pair unit")
    expect_error(lambda: oracle.require_pair_ratio("ab", "p"), "INVALID_PAIR")
    expect_error(lambda: oracle.require_pair_ratio([1], "p"), "INVALID_PAIR")
    expect_error(lambda: oracle.require_pair_ratio([-1, 2], "p"), "RANGE_ERROR")
    expect_error(lambda: oracle.require_pair_ratio([0, 0], "p"), "RANGE_ERROR")
    expect_error(lambda: oracle.require_pair_ratio([3, 2], "p"), "INVALID_PAIR")

    # frac_str / format_exact_decimal / canonical_json / sha
    check(oracle.frac_str(Fraction(4, 6)) == "2/3", "frac_str")
    check(oracle.format_exact_decimal(Fraction(1, 2), 0) == "1", "half up")
    check(oracle.format_exact_decimal(Fraction(49, 100), 0) == "0", "below half")
    check(oracle.format_exact_decimal(Fraction(-3, 2), 0) == "-2", "neg half up")
    check(oracle.format_exact_decimal(Fraction(-1, 10000000), 6) == "0.000000", "no neg zero")
    check(oracle.format_exact_decimal(Fraction(-1, 4), 2) == "-0.25", "neg dec")
    expect_error(lambda: oracle.format_exact_decimal(Fraction(1, 2), -1), "RANGE_ERROR")
    expect_error(lambda: oracle.format_exact_decimal(Fraction(1, 2), 13), "RANGE_ERROR")
    check(oracle.canonical_json_bytes({"b": 1, "a": "\u0633"}) == b'{"a":"\\u0633","b":1}', "canon json")
    check(len(oracle.canonical_sha256({"x": 1})) == 64, "canon sha")
    expect_error(lambda: oracle.canonical_json_bytes({"x": 0.1}), "FLOAT_FORBIDDEN")

    # fnv1a_32 / det_shuffle / stratified_shuffle
    check(oracle.fnv1a_32("N") == 3406561745, "fnv N")
    check(oracle.det_shuffle_exact([0, 1, 2, 3, 4, 5, 6, 7], 42) == [0, 5, 1, 7, 3, 4, 2, 6], "shuffle golden")
    expect_error(lambda: oracle.det_shuffle_exact("abc", 1), "INVALID_SEQ")
    expect_error(lambda: oracle.det_shuffle_exact([1, 2], -1), "RANGE_ERROR")
    st = oracle.stratified_shuffle_exact(["a1", "b1", "a2", "b2", "a3", "b3", "a4", "b4"], ["N", "V", "N", "V", "N", "V", "N", "V"], 99)
    check(st == ["a2", "b3", "a4", "b4", "a1", "b2", "a3", "b1"], "strat golden")
    expect_error(lambda: oracle.stratified_shuffle_exact("ab", ["N", "V"], 1), "INVALID_SEQ")
    expect_error(lambda: oracle.stratified_shuffle_exact(["a"], "N", 1), "INVALID_SEQ")
    expect_error(lambda: oracle.stratified_shuffle_exact(["a"], ["N", "V"], 1), "LENGTH_MISMATCH")

    # Arabic & English text nets
    expect_error(lambda: oracle.to_rasm(123), "INVALID_TYPE")
    check(oracle.to_rasm("\u0671\u0623\u0625\u0622\u0649\u0629\u064e\u0640!") == "\u0627\u0627\u0627\u0627\u064a\u0647", "rasm")
    check(oracle.light_stem_ar("\u0643\u062a\u0628") == "\u0643\u062a\u0628", "stem 3")
    check(oracle.light_stem_ar("\u0648\u0627\u0644\u0643\u062a\u0628\u0647\u0645") == "\u0643\u062a\u0628", "stem affixes")
    expect_error(lambda: oracle.en_content_stems(None), "INVALID_TYPE")
    stems = oracle.en_content_stems("The wrapped wraps spinning walking bring walked bred fishes goes ships laws lorded that")
    check(stems == {"wrap", "spin", "walk", "bring", "bred", "fish", "goes", "ship", "laws"}, f"en stems: {stems}")

    # Renyi-2 helpers
    check(oracle.renyi2_concentration_pair({"a": 2, "b": 2}) == (8, 16, Fraction(1, 2)), "renyi2 exact")
    expect_error(lambda: oracle.renyi2_concentration_pair({}), "INVALID_COUNTS")
    expect_error(lambda: oracle.renyi2_concentration_pair("bad"), "INVALID_COUNTS")
    expect_error(lambda: oracle.renyi2_concentration_pair({"a": 0}), "RANGE_ERROR")
    check(oracle.block_renyi2_cross_pair(["a", "a", "a", "b"], 2) == (2, 4, Fraction(1, 2)), "block r2 exact")
    expect_error(lambda: oracle.block_renyi2_cross_pair("abcd", 2), "INVALID_SEQ")
    expect_error(lambda: oracle.block_renyi2_cross_pair(["a", "b", "c"], 1), "RANGE_ERROR")
    expect_error(lambda: oracle.block_renyi2_cross_pair(["a", "b", "c"], 2), "INSUFFICIENT_BLOCKS")

    # Anti-numerology guard
    res = oracle.enforce_zero_numerology_policy([" Root_Matrix ", "Renyi_2"])
    check(res["zero_numerology_ok"] is True and res["features"] == ["root_matrix", "renyi_2"], "num ok")
    expect_error(lambda: oracle.enforce_zero_numerology_policy([1.0]), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.enforce_zero_numerology_policy([]), "INVALID_FEATURES")
    expect_error(lambda: oracle.enforce_zero_numerology_policy("root"), "INVALID_FEATURES")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["___"]), "EMPTY_STRING")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["root_a", "root-a"]), "DUPLICATE_FEATURE")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["ab\u200bjad_score"]), "CONTROL_CHAR")
    # LEX-BUG-05 regression: NFKC fullwidth obfuscation blocked!
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["root_\uff41\uff42\uff4a\uff41\uff44"]), "NUMEROLOGY_FORBIDDEN")
    for obf in ("base_10_count", "code_19_filter", "digit-sum", "a b j a d", "gematria_x", "miracle1", "numerology"):
        expect_error(lambda tok=obf: oracle.enforce_zero_numerology_policy([tok]), "NUMEROLOGY_FORBIDDEN")


def test_pillar1_wazn_and_renyi2():
    fx = copy.deepcopy(audit.STANDALONE_FIXTURE)
    p1 = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
        fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
        fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
        fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], fx["control_renyi2_metrics"],
    )
    check(p1["passed"] is True, "p1 passes fixture")

    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(1.0, 1, 1, 2, 0, {}, {}, {}, {}),
        "FLOAT_FORBIDDEN",
    )
    # verb_tokens_i_x < verb_roots + poly_wazn_roots
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            100, 50, 30, 79, 0, fx["op_class_counts"], fx["transition_pair_counts"],
            fx["within_root_renyi2_pairs"], fx["control_renyi2_metrics"],
        ),
        "RANGE_ERROR",
    )
    # op_class_counts bad keys & sum conservation
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], {"GROUND_I": 1},
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], fx["control_renyi2_metrics"],
        ),
        "INVALID_OP_CLASSES",
    )
    bad_ops = dict(fx["op_class_counts"])
    bad_ops["GROUND_I"] += 1
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], bad_ops,
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    # transition_pair_counts bad keys
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            {"I+IV": 100}, fx["within_root_renyi2_pairs"], fx["control_renyi2_metrics"],
        ),
        "INVALID_TRANSITIONS",
    )
    # LEX-BUG-02 regression: disjoint op-class lower bounds vs transition counts
    bad_stat = dict(fx["op_class_counts"])
    bad_stat["GROUND_I"] += bad_stat["STAT_ESTIM_IX_X"] - 1
    bad_stat["STAT_ESTIM_IX_X"] = 1
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], bad_stat,
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    # within_root_renyi2_pairs bad keys, 10-form floor, Cauchy-Schwarz, poly gap & split conservation (LEX-BUG-01)
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], {"all_obs": [1, 2]}, fx["control_renyi2_metrics"],
        ),
        "INVALID_WR_PAIRS",
    )
    # 10-form Cauchy-Schwarz floor breach
    bw_10 = copy.deepcopy(fx["within_root_renyi2_pairs"])
    bw_10["all_t4a"] = [1, bw_10["all_t4a"][1]]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], bw_10, fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    # Zero poly-wazn gap breach (all_obs=[D, D])
    bw_gap = copy.deepcopy(fx["within_root_renyi2_pairs"])
    bw_gap["all_obs"] = [bw_gap["all_obs"][1], bw_gap["all_obs"][1]]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], bw_gap, fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    # Tiny [1, 1] violates all_d * v_roots >= v_toks^2
    bw_tiny = {k: [1, 1] for k in fx["within_root_renyi2_pairs"]}
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], bw_tiny, fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    for bad_k in ("all_t4a", "all_t4b", "odd_t4b", "even_t4b"):
        bw = copy.deepcopy(fx["within_root_renyi2_pairs"])
        bw[bad_k] = [bw[bad_k][0], bw[bad_k][1] + 1]
        expect_error(
            lambda m=bw: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
                fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
                fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
                fx["transition_pair_counts"], m, fx["control_renyi2_metrics"],
            ),
            "CONSERVATION_ERROR",
        )
    # control_renyi2_metrics errors & LEX-BUG-02 global_c2 exact sum(c^2)/N^2 law
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], {"quran_stem": {}},
        ),
        "INVALID_CONTROLS",
    )
    bc1 = copy.deepcopy(fx["control_renyi2_metrics"])
    bc1["quran_stem"] = {"global_c2": [1, 10]}
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], bc1,
        ),
        "INVALID_CONTROL_ENTRY",
    )
    bc2 = copy.deepcopy(fx["control_renyi2_metrics"])
    bc2["kalila_prose"]["w20_t4a"] = [100, 881201]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], bc2,
        ),
        "CONSERVATION_ERROR",
    )
    for bad_gc2 in ([1, 1000000], [100, 101], [1001, 1000000]):
        bc3 = copy.deepcopy(fx["control_renyi2_metrics"])
        bc3["poetry_pooled"]["global_c2"] = bad_gc2
        expect_error(
            lambda m=bc3: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
                fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
                fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
                fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], m,
            ),
            "CONSERVATION_ERROR",
        )
    bc4 = copy.deepcopy(fx["control_renyi2_metrics"])
    bc4["poetry_pooled"]["w20_t4a"] = [0, 204400]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"], bc4,
        ),
        "ZERO_DENOM",
    )

    # Exact gate pass/fail boundaries
    bt = dict(fx["transition_pair_counts"])
    bt["I+IV"] = 99
    r_bt = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
        fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
        fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
        bt, fx["within_root_renyi2_pairs"], fx["control_renyi2_metrics"],
    )
    check(r_bt["agency_matrix_nontrivial"] is False and r_bt["passed"] is False, "I+IV=99 fails")

    # 2) within-root margin breach & exact 10*n == d Cauchy-Schwarz boundary
    wr_10eq = {
        "all_obs": [4200000, 6000000], "all_t4a": [600000, 6000000], "all_t4b": [3000000, 6000000],
        "odd_obs": [2100000, 3000000], "odd_t4b": [1500000, 3000000],
        "even_obs": [2100000, 3000000], "even_t4b": [1500000, 3000000],
    }
    check(
        oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], wr_10eq, fx["control_renyi2_metrics"],
            min_wazn_margin=Fraction(1, 5),
        )["passed"] is True,
        "wr exact 10*n == d boundary passes",
    )
    wr_eq = {
        "all_obs": [4200000, 6000000], "all_t4a": [3000000, 6000000], "all_t4b": [3000000, 6000000],
        "odd_obs": [2100000, 3000000], "odd_t4b": [1500000, 3000000],
        "even_obs": [2100000, 3000000], "even_t4b": [1500000, 3000000],
    }
    check(
        oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], wr_eq, fx["control_renyi2_metrics"],
            min_wazn_margin=Fraction(1, 5),
        )["passed"] is True,
        "wr exact margin passes",
    )
    wr_fail = copy.deepcopy(wr_eq)
    wr_fail["even_t4b"] = [1500001, 3000000]
    check(
        oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], wr_fail, fx["control_renyi2_metrics"],
            min_wazn_margin=Fraction(1, 5),
        )["within_root_wazn_beats_nulls"] is False,
        "wr margin breach fails",
    )
    # 3) negative-control shared lift & poetry D2 breach (valid sum(c^2)/N^2 pair: 100/10000 -> D2=100)
    bc_nolift = copy.deepcopy(fx["control_renyi2_metrics"])
    bc_nolift["kalila_prose"]["w20_obs"] = bc_nolift["kalila_prose"]["w20_t4a"]
    check(
        oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], wr_eq, bc_nolift,
        )["shared_prose_renyi2_lift"] is False,
        "kalila no-lift fails",
    )
    bc_poet = copy.deepcopy(fx["control_renyi2_metrics"])
    bc_poet["poetry_pooled"]["global_c2"] = [100, 10000]
    check(
        oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], wr_eq, bc_poet,
        )["poetry_higher_effective_diversity"] is False,
        "poetry low D2 fails",
    )


def test_pillar2_context_topology():
    cm = copy.deepcopy(audit.STANDALONE_FIXTURE["context_metrics"])
    p2 = oracle.audit_context_neighborhood_topology_exact(cm)
    check(p2["passed"] is True, "p2 passes fixture")

    expect_error(lambda: oracle.audit_context_neighborhood_topology_exact({"ctx_r2_all": 0.1}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.audit_context_neighborhood_topology_exact({"ctx_r2_all": [1, 2]}), "INVALID_METRICS")

    # Split-sum mismatch (cooccur, LEX-BUG-03 weighted Jaccard & quadratic Renyi-2)
    for key, bad_val in (
        ("cooccur_all", [cm["cooccur_all"][0] + 1, cm["cooccur_all"][1]]),
        ("cooccur_null", [cm["cooccur_null"][0] + 1, cm["cooccur_null"][1]]),
        ("ctx_jaccard_all", [1, 100]),
        ("ctx_jaccard_null", [1, 100]),
        ("ctx_r2_all", [6, 1000]),
        ("ctx_r2_null", [6, 1000]),
    ):
        m_bad = copy.deepcopy(cm)
        m_bad[key] = bad_val
        expect_error(lambda m=m_bad: oracle.audit_context_neighborhood_topology_exact(m), "SPLIT_SUM_MISMATCH")

    # Zero null denom (while preserving quadratic split conservation!)
    m_z_all = copy.deepcopy(cm)
    m_z_all["ctx_r2_null"] = [0, m_z_all["ctx_r2_null"][1]]
    m_z_all["ctx_r2_odd_null"] = [0, m_z_all["ctx_r2_odd_null"][1]]
    m_z_all["ctx_r2_even_null"] = [0, m_z_all["ctx_r2_even_null"][1]]
    expect_error(lambda: oracle.audit_context_neighborhood_topology_exact(m_z_all), "ZERO_DENOM")

    # Exact boundaries (satisfying all LEX-BUG-03 conservation identities)
    base = {
        "ctx_r2_all": [120, 20000], "ctx_r2_null": [100, 20000],
        "ctx_r2_odd": [60, 10000], "ctx_r2_odd_null": [50, 10000],
        "ctx_r2_even": [60, 10000], "ctx_r2_even_null": [50, 10000],
        "ctx_jaccard_all": [36, 200], "ctx_jaccard_null": [38, 200],
        "ctx_jaccard_odd": [18, 100], "ctx_jaccard_odd_null": [19, 100],
        "ctx_jaccard_even": [18, 100], "ctx_jaccard_even_null": [19, 100],
        "cooccur_all": [24, 200], "cooccur_null": [20, 200],
        "cooccur_odd": [12, 100], "cooccur_odd_null": [10, 100],
        "cooccur_even": [12, 100], "cooccur_even_null": [10, 100],
    }
    check(oracle.audit_context_neighborhood_topology_exact(base)["passed"] is True, "p2 exact boundary passes")
    for k, val, aux in (
        ("ctx_r2_even", [59, 10000], ("ctx_r2_all", [119, 20000])),
        ("ctx_jaccard_even", [19, 100], ("ctx_jaccard_all", [37, 200])),
        ("cooccur_even", [11, 100], ("cooccur_all", [23, 200])),
    ):
        m = copy.deepcopy(base)
        m[k] = val
        m[aux[0]] = aux[1]
        check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, f"p2 breach {k}")


def test_pillar3_two_layer_projection():
    fx = copy.deepcopy(audit.STANDALONE_FIXTURE)
    p3 = oracle.audit_two_layer_projection_defect_exact(
        fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"]
    )
    check(p3["passed"] is True, "p3 passes fixture")
    check(p3["multi_lemma_roots_tested"] == 12, "12 multi-lemma roots")
    check(p3["multi_lemma_sahih_strict_count"] == 12, "12/12 sahih strict")
    check(p3["multi_lemma_pickthall_strict_count"] == 12, "12/12 pick strict")

    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([{"x": 0.1}], [9, 10], [9, 10]),
        "FLOAT_FORBIDDEN",
    )
    expect_error(lambda: oracle.audit_two_layer_projection_defect_exact([], [9, 10], [9, 10]), "INVALID_RECORDS")
    expect_error(lambda: oracle.audit_two_layer_projection_defect_exact(["bad"], [9, 10], [9, 10]), "INVALID_RECORD")

    def mk(name, lems=2, s_top=2, p_top=2, sp=5, cp=5, ssl=2, scl=4, psl=2, pcl=4):
        return {
            "root": name, "occurrences": 5, "verse_count": 5, "unique_lemmas": lems,
            "sahih_top_count": s_top, "pickthall_top_count": p_top,
            "same_lemma_pairs": sp, "cross_lemma_pairs": cp,
            "sahih_same_lost": ssl, "sahih_cross_lost": scl,
            "pickthall_same_lost": psl, "pickthall_cross_lost": pcl,
            "sahih_lost_pairs": ssl + scl, "pickthall_lost_pairs": psl + pcl,
        }

    # Duplicate root (case-insensitive)
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([mk("sbH"), mk("sbh")], [9, 10], [9, 10]),
        "DUPLICATE_ROOT",
    )
    # Partition mismatch (same+cross != 10)
    bad_part = mk("r1")
    bad_part["cross_lemma_pairs"] = 4
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([bad_part, mk("r2")], [9, 10], [9, 10]),
        "PARTITION_MISMATCH",
    )
    # Single lemma with cross pairs > 0 & LEX-BUG-04 Turan pigeonhole lower bound (V=10, L=2 -> turan_min=20)
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([mk("r1", lems=1), mk("r2")], [9, 10], [9, 10]),
        "LEMMA_MISMATCH",
    )
    turan_bad = {
        "root": "t1", "occurrences": 10, "verse_count": 10, "unique_lemmas": 2,
        "sahih_top_count": 2, "pickthall_top_count": 2,
        "same_lemma_pairs": 19, "cross_lemma_pairs": 26,
        "sahih_same_lost": 5, "sahih_cross_lost": 20,
        "pickthall_same_lost": 5, "pickthall_cross_lost": 20,
        "sahih_lost_pairs": 25, "pickthall_lost_pairs": 25,
    }
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([turan_bad, mk("r2")], [9, 10], [9, 10]),
        "LEMMA_MISMATCH",
    )
    turan_ok = dict(turan_bad)
    turan_ok["same_lemma_pairs"] = 20
    turan_ok["cross_lemma_pairs"] = 25
    check(
        oracle.audit_two_layer_projection_defect_exact([turan_ok, mk("r2")], [9, 10], [9, 10])["multi_lemma_roots_tested"] == 2,
        "turan exact boundary 20 passes",
    )
    # Lost partition mismatch
    bad_lp = mk("r1")
    bad_lp["sahih_lost_pairs"] = 5
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([bad_lp, mk("r2")], [9, 10], [9, 10]),
        "PARTITION_MISMATCH",
    )
    # Pigeonhole upper & converse lower bounds
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([mk("r1", s_top=4, ssl=2, scl=3), mk("r2")], [9, 10], [9, 10]),
        "RANGE_ERROR",
    )
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([mk("r1", s_top=1, ssl=2, scl=4), mk("r2")], [9, 10], [9, 10]),
        "RANGE_ERROR",
    )
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([mk("r1", p_top=0, psl=2, pcl=4), mk("r2")], [9, 10], [9, 10]),
        "RANGE_ERROR",
    )
    # Insufficient multi-lemma roots (< 2)
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([mk("r1")], [9, 10], [9, 10]),
        "INSUFFICIENT_PARTITION",
    )

    # Exact pass & breach checks on 2 multi-lemma roots
    # Each has sp=5, cp=5, ssl=2 (0.40), scl=4 (0.80) -> overall=6/10 (0.60), same=0.40, cross-same=0.40
    ok2 = [mk("r1"), mk("r2")]
    check(oracle.audit_two_layer_projection_defect_exact(ok2, [9, 10], [9, 10])["passed"] is True, "2-root ok")
    # Breach bg ceiling
    check(oracle.audit_two_layer_projection_defect_exact(ok2, [6, 10], [9, 10])["passed"] is False, "bg ceiling breach")
    # Breach intra-lemma floor (same=1/5=0.20 < 0.30)
    low_same = [mk("r1", ssl=1, scl=4), mk("r2", ssl=1, scl=4)]
    check(oracle.audit_two_layer_projection_defect_exact(low_same, [9, 10], [9, 10])["passed"] is False, "low same fails")
    # Breach unanimous strict cross > same (r2 has scl=2 == ssl=2)
    non_strict = [mk("r1", ssl=2, scl=5), mk("r2", ssl=2, scl=2)]
    check(oracle.audit_two_layer_projection_defect_exact(non_strict, [9, 10], [9, 10])["passed"] is False, "non-strict fails")
    non_strict_p = [mk("r1", psl=2, pcl=5), mk("r2", psl=2, pcl=2)]
    check(oracle.audit_two_layer_projection_defect_exact(non_strict_p, [9, 10], [9, 10])["passed"] is False, "pick non-strict fails")


def test_pillar4_gate_and_contradictions():
    cert = audit.run_audit(standalone=True)
    check(cert["verdict"] == "CERTIFIED_ARABIC_LEXICON_TOPOLOGY", "standalone verdict")
    check(cert["all_gates_passed"] is True, "all gates passed")
    check(cert["certificate_sha256"] == EXPECTED_STANDALONE_SHA, f"standalone sha: {cert['certificate_sha256']}")

    p1 = cert["pillar1_wazn_agency_and_renyi2"]
    p2 = cert["pillar2_context_neighborhood_topology"]
    p3 = cert["pillar3_two_layer_projection_defect"]
    axes = dict(cert["five_axis_net_invariance"])
    pins = dict(audit.EXPECTED_CORPUS_SHA256)

    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", {"a": 1.0}, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "FLOAT_FORBIDDEN",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("bad", pins, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "INVALID_MODE",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", {}, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "MISSING_PROVENANCE",
    )
    for bad_path in ("/abs/p", "../escape", "file:///etc/passwd", "FILE:///etc/passwd", "sub\\dir\\x"):
        expect_error(
            lambda bp=bad_path: oracle.certify_arabic_lexicon_own_terms_gate(
                "standalone", {bp: "a" * 64}, audit.AUDIT_FEATURES, p1, p2, p3, axes
            ),
            "UNSAFE_PIN_PATH",
        )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate(
            "standalone", {"a": "a" * 64, " a ": "a" * 64}, audit.AUDIT_FEATURES, p1, p2, p3, axes
        ),
        "DUPLICATE_PIN_PATH",
    )
    for bad_sha in ("A" * 64, "a" * 64 + "\n", " " + "a" * 64, "0" * 64, 123):
        expect_error(
            lambda bs=bad_sha: oracle.certify_arabic_lexicon_own_terms_gate(
                "standalone", {"x": bs}, audit.AUDIT_FEATURES, p1, p2, p3, axes
            ),
            "INVALID_SHA256",
        )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, p1, p2, p3, "bad"),
        "INVALID_AXES",
    )
    extra_ax = dict(axes)
    extra_ax["extra"] = True
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, p1, p2, p3, extra_ax),
        "INVALID_AXES",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, "bad", p2, p3, axes),
        "INVALID_PILLAR",
    )
    # LEX-BUG-05 regression: hollow shells & forged numeric/bool pillar evidence rejected via full re-derivation!
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate(
            "standalone", pins, audit.AUDIT_FEATURES, {"passed": True}, p2, p3, axes
        ),
        "PILLAR_CONTRADICTION",
    )
    bp1_ctrl = copy.deepcopy(p1); bp1_ctrl["controls_renyi2"]["quran_stem"] = "bad"
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, bp1_ctrl, p2, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    bp1 = copy.deepcopy(p1); bp1["agency_matrix_nontrivial"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, bp1, p2, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    bp2 = copy.deepcopy(p2); bp2["distinct_neighborhoods_vs_background"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, p1, bp2, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    bp3 = copy.deepcopy(p3); bp3["discrete_bucket_falsified"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, p1, p2, bp3, axes),
        "PILLAR_CONTRADICTION",
    )
    bax = dict(axes); bax["two_translator_agreement"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone", pins, audit.AUDIT_FEATURES, p1, p2, p3, bax),
        "AXIS_CONTRADICTION",
    )

    # Consistent rejection using genuinely re-derived failing Pillar 2
    bad_cm = copy.deepcopy(audit.STANDALONE_FIXTURE["context_metrics"])
    bad_cm["ctx_jaccard_odd"] = list(bad_cm["ctx_jaccard_odd_null"])
    bad_cm["ctx_jaccard_even"] = list(bad_cm["ctx_jaccard_even_null"])
    bad_cm["ctx_jaccard_all"] = list(bad_cm["ctx_jaccard_null"])
    q2 = oracle.audit_context_neighborhood_topology_exact(bad_cm)
    qax = dict(axes)
    qax["arabic_context_topology_split_half"] = False
    rej = oracle.certify_arabic_lexicon_own_terms_gate("live_readonly", pins, audit.AUDIT_FEATURES, p1, q2, p3, qax)
    check(rej["verdict"] == "REJECTED_GATE_FAILED" and rej["all_gates_passed"] is False, "consistent rejection")


def test_audit_parsers_and_synthetic_live():
    check(len(audit.TARGET_ROOTS) == 15, "15 target roots")
    check(audit.default_corpus_dir().endswith(os.path.join("repos", "arabic")), "default corpus dir")

    # parse_tanzil_lines
    tz = audit.parse_tanzil_lines(["# c\n", "\n", "1|1|alpha | beta\n"])
    check(tz == {(1, 1): "alpha | beta"}, "tanzil")
    expect_error(lambda: audit.parse_tanzil_lines(["bad_line\n"]), "PARSE_ERROR")

    # parse_openiti_stems
    stems = audit.parse_openiti_stems([
        "### preheader \u0643\u062a\u0628\n",
        "#META#Header#End#\n",
        "\n",
        "### section\n",
        "PageV01P01 ms01 %~~% ~% \u0648\u0627\u0644\u0643\u062a\u0628 !!!\n",
    ])
    check(stems == ["\u0643\u062a\u0628"], f"openiti stems: {stems}")

    # parse_leeds_lexicon_lines (including Form XII, missing LEM, no ROOT, <4 cols)
    leeds = [
        "", "# c\n", "LOCATION\tFORM\tTAG\tFEATURES\n", "a\tb\tc\n",
        "(1:1:1:1)\tbi\tP\tPREFIX|bi+\n",
        "(1:1:2:1)\tf\tV\tSTEM|POS:V|PERF|(II)|LEM:L1|ROOT:sbH\n",
        "(1:1:3:1)\tf\tV\tSTEM|POS:V|PERF|ROOT:ktb\n",
        "(2:1:1:1)\tf\tV\tSTEM|POS:V|PERF|(XII)|LEM:L2|ROOT:Tmn\n",
        "(2:1:2:1)\tf\tV\tSTEM|POS:V|PERF|(IV)|LEM:L3|ROOT:sbH\n",
    ]
    md = audit.parse_leeds_lexicon_lines(leeds)
    check(md["total_unique_roots"] == 3 and md["form_xii_tokens"] == 1, "leeds counts")
    check(len(md["verb_pairs_odd"]) == 2 and len(md["verb_pairs_even"]) == 1, "odd/even verbs")

    # freq_stratified_wazn_shuffle exercises all 4 bins (B1..B4)
    big_pairs = [("r1", "I")] * 2 + [("r2", "II")] * 5 + [("r3", "IV")] * 15 + [("r4", "I")] * 55
    shuf = audit.freq_stratified_wazn_shuffle(big_pairs, 12345)
    check(len(shuf) == len(big_pairs), "freq strat len")

    # Synthetic 9-file corpus live pipeline + CLI tests
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "arabic_morphology_quranic-corpus"))
        os.makedirs(os.path.join(tmpdir, "openiti_controls"))
        morph_lines = ["LOCATION\tFORM\tTAG\tFEATURES\n"]
        uth_lines, sahih_lines, pick_lines = [], [], []
        forms = ("I", "II", "IV", "V", "VI", "VIII", "X")
        for s_num in (1, 2):
            for v_num in range(1, 16):
                r1 = audit.TARGET_ROOTS[(v_num - 1) % len(audit.TARGET_ROOTS)]
                r2 = audit.TARGET_ROOTS[v_num % len(audit.TARGET_ROOTS)]
                vf = forms[(v_num - 1) % len(forms)]
                tag_vf = "" if vf == "I" else f"|({vf})"
                morph_lines.append(f"({s_num}:{v_num}:1:1)\tf\tV\tSTEM|POS:V{tag_vf}|LEM:{r1}A|ROOT:{r1}\n")
                morph_lines.append(f"({s_num}:{v_num}:2:1)\tf\tN\tSTEM|POS:N|LEM:{r2}B|ROOT:{r2}\n")
                uth_lines.append(f"{s_num}|{v_num}|\u0643\u062a\u0628 \u0633\u0628\u062d !!!\n")
                if s_num == 1 and v_num == 1:
                    sahih_lines.append(f"{s_num}|{v_num}|the of and\n")
                    pick_lines.append(f"{s_num}|{v_num}|the of and\n")
                elif v_num % 2 == 0:
                    sahih_lines.append(f"{s_num}|{v_num}|exalt ship create truth\n")
                    pick_lines.append(f"{s_num}|{v_num}|glorify ship create truth\n")
                else:
                    sahih_lines.append(f"{s_num}|{v_num}|extend measure descend order\n")
                    pick_lines.append(f"{s_num}|{v_num}|spread measure reveal command\n")

        openiti = "#META#Header#End#\n" + "\u0643\u062a\u0628 \u0633\u0628\u062d \u0641\u0644\u0643 \u0642\u062f\u0631\n" * 10
        fmap = {
            "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt": "".join(morph_lines),
            "tanzil-quran-uthmani.txt": "".join(uth_lines),
            "tanzil-en.sahih.txt": "".join(sahih_lines),
            "tanzil-en.pickthall.txt": "".join(pick_lines),
            "openiti_controls/ibn_muqaffa_kalila.txt": openiti,
            "openiti_controls/ibn_muqaffa_adab_kabir.txt": openiti,
            "openiti_controls/imru_al_qays_diwan.txt": openiti,
            "openiti_controls/tarafa_diwan.txt": openiti,
            "openiti_controls/antara_muallaqa.txt": openiti,
        }
        pins = {}
        for rel, content in fmap.items():
            fp = os.path.join(tmpdir, rel)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            pins[rel] = audit.sha256_file(fp)

        expect_error(lambda: audit.verify_corpus_hashes(tmpdir), "SHA256_MISMATCH")
        bad_pins = dict(pins); bad_pins["missing.txt"] = "0" * 64
        expect_error(lambda: audit.verify_corpus_hashes(tmpdir, expected_hashes=bad_pins), "CORPUS_MISSING")

        m = audit.compute_live_measurements(tmpdir, expected_hashes=pins, ctrl_window=4, bg_pair_count=5, min_multi_verses=2)
        check(m["total_unique_roots"] == 15 and len(m["root_records"]) == 15, "synth live ok")
        expect_error(lambda: audit.run_audit(standalone=False, corpus_dir=tmpdir), "SHA256_MISMATCH")

        out_path = os.path.join(tmpdir, "cert.json")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            rc = audit.main(["--standalone", "--output", out_path])
        finally:
            sys.stdout = old_stdout
        check(rc == 0, "main rc=0")
        with open(out_path, "rb") as f:
            written = f.read()
        check(json.loads(written.decode("utf-8"))["certificate_sha256"] == EXPECTED_STANDALONE_SHA, "cli sha")

        orig_fx = audit.STANDALONE_FIXTURE
        bad_fx = copy.deepcopy(orig_fx)
        bad_fx["transition_pair_counts"]["I+IV"] = 99
        buf2 = io.StringIO()
        try:
            audit.STANDALONE_FIXTURE = bad_fx
            sys.stdout = buf2
            rc_fail = audit.main(["--standalone"])
        finally:
            audit.STANDALONE_FIXTURE = orig_fx
            sys.stdout = old_stdout
        check(rc_fail == 1, "main rc=1")

    proc = subprocess.run(
        [sys.executable, "-I", "-B", "-W", "error", os.path.join(_SCRIPT_DIR, "arabic_lexicon_audit.py"), "--standalone"],
        capture_output=True, text=True, check=False,
    )
    check(proc.returncode == 0 and json.loads(proc.stdout)["certificate_sha256"] == EXPECTED_STANDALONE_SHA, "subproc -I")


def run_all_tests():
    test_primitives_and_text_nets()
    test_pillar1_wazn_and_renyi2()
    test_pillar2_context_topology()
    test_pillar3_two_layer_projection()
    test_pillar4_gate_and_contradictions()
    test_audit_parsers_and_synthetic_live()
    return "ALL_AUDIT094_TESTS_PASSED"


if __name__ == "__main__":
    print(run_all_tests())
