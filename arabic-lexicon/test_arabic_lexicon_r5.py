"""Assertion-free R5 mutation-hardened, threshold-pinning, & known-answer test suite
for arabic-lexicon (v2 — closing review 6011346623 Findings #1, #2, #3, #5, #7).

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
    "8ec87277a9b5ae4ac529f3962bbf3fa9e89fa3c7727e08205c6805a7a4f62a4a"
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


def test_primitives_holm_and_naming_guard():
    check(oracle.SCHEMA_VERSION == "arabic-lexicon-topology-oracle/v2", "schema v2")
    check(oracle.MIN_MULTISHUFFLE_B == 250, "min B=250")
    check(oracle.DEFAULT_ALPHA == Fraction(1, 20), "alpha=1/20")

    oracle.verify_no_floats({"a": [1, (Fraction(1, 2), {3}, frozenset({4}))]})
    expect_error(lambda: oracle.verify_no_floats(0.5), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats(1 + 2j), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats({1.5: "x"}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats({"x": [2.0]}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats(frozenset({3.14})), "FLOAT_FORBIDDEN")

    check(oracle.require_non_empty_str("  hello ~ ", "f") == "hello ~", "strip")
    expect_error(lambda: oracle.require_non_empty_str(123, "f"), "INVALID_TYPE")
    expect_error(lambda: oracle.require_non_empty_str("   ", "f"), "EMPTY_STRING")
    expect_error(lambda: oracle.require_non_empty_str("a\x1fb", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("a\x7fb", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("abc\n", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("ab\u200bjad", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("\ufeffabc", "f"), "CONTROL_CHAR")

    check(oracle.require_exact_bool(True, "b") is True, "bool")
    expect_error(lambda: oracle.require_exact_bool(1, "b"), "INVALID_BOOL")
    check(oracle.require_exact_int(5, "i", 5, 5) == 5, "int")
    expect_error(lambda: oracle.require_exact_int(True, "i"), "INVALID_INT")
    expect_error(lambda: oracle.require_exact_int(4, "i", min_value=5), "RANGE_ERROR")
    expect_error(lambda: oracle.require_exact_int(6, "i", max_value=5), "RANGE_ERROR")
    check(oracle.require_exact_fraction(3, "q") == Fraction(3, 1), "int frac")
    check(oracle.require_exact_fraction(Fraction(1, 2), "q", Fraction(1, 2), Fraction(1, 2)) == Fraction(1, 2), "frac")
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

    check(oracle.require_signed_ratio_pair([-3, 3], "sp") == (-3, 3, Fraction(-1, 1)), "signed neg")
    check(oracle.require_signed_ratio_pair([3, 3], "sp") == (3, 3, Fraction(1, 1)), "signed pos")
    expect_error(lambda: oracle.require_signed_ratio_pair("ab", "sp"), "INVALID_PAIR")
    expect_error(lambda: oracle.require_signed_ratio_pair([-4, 3], "sp"), "INVALID_PAIR")

    # empirical_rank_p_exact & holm_bonferroni_exact
    check(oracle.empirical_rank_p_exact(0, 250) == Fraction(1, 251), "rank p min")
    check(oracle.empirical_rank_p_exact(250, 250) == Fraction(1, 1), "rank p max")
    expect_error(lambda: oracle.empirical_rank_p_exact(251, 250), "RANGE_ERROR")
    expect_error(lambda: oracle.holm_bonferroni_exact({}), "INVALID_PMAP")
    expect_error(lambda: oracle.holm_bonferroni_exact("bad"), "INVALID_PMAP")
    hb = oracle.holm_bonferroni_exact({"t1": Fraction(1, 100), "t2": Fraction(4, 100), "t3": Fraction(4, 5)})
    check(hb["adjusted_p_exact"] == {"t1": "3/100", "t2": "2/25", "t3": "4/5"}, f"holm adj: {hb}")
    check(hb["rejected_at_alpha"] == {"t1": True, "t2": False, "t3": False}, "holm rej")
    hb_cap = oracle.holm_bonferroni_exact({"a": Fraction(2, 3), "b": Fraction(2, 3)})
    check(hb_cap["adjusted_p_exact"]["a"] == "1/1", "holm capped at 1")

    # formatting, canonical json, shuffles, text nets, Renyi-2
    check(oracle.format_exact_decimal(Fraction(1, 2), 0) == "1", "half up")
    check(oracle.format_exact_decimal(Fraction(-1, 10000000), 6) == "0.000000", "no neg zero")
    check(oracle.format_exact_decimal(Fraction(-1, 4), 2) == "-0.25", "neg 2 dec")
    check(oracle.canonical_json_bytes({"b": 1, "a": "\u0633"}) == b'{"a":"\\u0633","b":1}', "canon json")
    check(oracle.fnv1a_32("N") == 3406561745, "fnv")
    check(oracle.det_shuffle_exact([0, 1, 2, 3, 4, 5, 6, 7], 42) == [0, 5, 1, 7, 3, 4, 2, 6], "shuf")
    expect_error(lambda: oracle.det_shuffle_exact("abc", 1), "INVALID_SEQ")
    st = oracle.stratified_shuffle_exact(["a1", "b1", "a2", "b2", "a3", "b3", "a4", "b4"], ["N", "V", "N", "V", "N", "V", "N", "V"], 99)
    check(st == ["a2", "b3", "a4", "b4", "a1", "b2", "a3", "b1"], "strat")
    expect_error(lambda: oracle.stratified_shuffle_exact("ab", ["N", "V"], 1), "INVALID_SEQ")
    expect_error(lambda: oracle.stratified_shuffle_exact(["a"], ["N", "V"], 1), "LENGTH_MISMATCH")
    expect_error(lambda: oracle.to_rasm(123), "INVALID_TYPE")
    check(oracle.to_rasm("\u0671\u0623\u0625\u0622\u0649\u0629\u064e\u0640!") == "\u0627\u0627\u0627\u0627\u064a\u0647", "rasm")
    check(oracle.light_stem_ar("\u0648\u0627\u0644\u0643\u062a\u0628\u0647\u0645") == "\u0643\u062a\u0628", "stem")
    expect_error(lambda: oracle.en_content_stems(None), "INVALID_TYPE")
    check(oracle.en_content_stems("wrapped wraps spinning walking fishes ships lorded") == {"wrap", "spin", "walk", "fish", "ship"}, "en stems")
    check(oracle.renyi2_concentration_pair({"a": 2, "b": 2}) == (8, 16, Fraction(1, 2)), "r2")
    expect_error(lambda: oracle.renyi2_concentration_pair({}), "INVALID_COUNTS")
    check(oracle.block_renyi2_cross_pair(["a", "a", "a", "b"], 2) == (2, 4, Fraction(1, 2)), "block r2")
    expect_error(lambda: oracle.block_renyi2_cross_pair("abcd", 2), "INVALID_SEQ")
    expect_error(lambda: oracle.block_renyi2_cross_pair(["a", "b", "c"], 2), "INSUFFICIENT_BLOCKS")

    # Feature-naming guard (explicitly labelled filter-only!)
    ng = oracle.enforce_zero_numerology_policy([" Root_Matrix ", "Renyi_2"])
    check(ng["naming_filter_ok"] is True, "naming ok")
    check(ng["guard_scope"] == "feature_label_filter_only_not_statistical_proof", "honest scope")
    expect_error(lambda: oracle.enforce_zero_numerology_policy([1.0]), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.enforce_zero_numerology_policy([]), "INVALID_FEATURES")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["___"]), "EMPTY_STRING")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["root_a", "root-a"]), "DUPLICATE_FEATURE")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["ab\u200bjad_score"]), "CONTROL_CHAR")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["root_\uff41\uff42\uff4a\uff41\uff44"]), "NUMEROLOGY_FORBIDDEN")
    for obf in ("base_10_count", "code_19_filter", "digit-sum", "a b j a d", "gematria_x", "miracle1", "numerology"):
        expect_error(lambda tok=obf: oracle.enforce_zero_numerology_policy([tok]), "NUMEROLOGY_FORBIDDEN")


def test_pillar1_pinning_every_conjunct_and_conservation():
    fx = copy.deepcopy(audit.STANDALONE_FIXTURE)
    p1 = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
        fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
        fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
        fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
        fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        n_shuffles=fx["n_shuffles"],
    )
    check(p1["passed"] is True, "p1 passes")
    check(p1["within_root_wazn_claim_scope"] == "single_corpus_descriptive_morphology", "descriptive scope")
    check(p1["form_tagged_openiti_control_present"] is False, "no form-tagged openiti")

    # Guards & conservation checks
    expect_error(lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(1.0, 1, 1, 2, 0, {}, {}, {}, {}, {}), "FLOAT_FORBIDDEN")
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], {"GROUND_I": 1},
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        ),
        "INVALID_OP_CLASSES",
    )
    bad_ops = dict(fx["op_class_counts"]); bad_ops["GROUND_I"] += 1
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], bad_ops,
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            {"I+IV": 100}, fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        ),
        "INVALID_TRANSITIONS",
    )
    bad_stat = dict(fx["op_class_counts"])
    bad_stat["GROUND_I"] += bad_stat["STAT_ESTIM_IX_X"] - 1
    bad_stat["STAT_ESTIM_IX_X"] = 1
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], bad_stat,
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], {"all_obs": [1, 2]},
            fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        ),
        "INVALID_WR_PAIRS",
    )
    bw_10 = copy.deepcopy(fx["within_root_renyi2_pairs"])
    bw_10["all_t4a"] = [1, bw_10["all_t4a"][1]]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], bw_10, fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    # Exact 10*n == d boundary passes (kills 10*n < d -> 10*n <= d)
    bw_10eq = copy.deepcopy(fx["within_root_renyi2_pairs"])
    d_all = bw_10eq["all_t4a"][1]
    bw_10eq["all_t4a"] = [d_all // 10, d_all] if d_all % 10 == 0 else [bw_10eq["all_t4a"][0], d_all]
    wr_10eq = {
        "all_obs": [4200000, 6000000],
        "all_t4a": [150000000, 1500000000],
        "all_t4b": [750000000, 1500000000],
        "odd_obs": [2100000, 3000000],
        "odd_t4b": [375000000, 750000000],
        "even_obs": [2100000, 3000000],
        "even_t4b": [375000000, 750000000],
    }
    check(
        oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], wr_10eq, fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        )["passed"] is True,
        "exact 10*n == d passes",
    )
    bw_gap = copy.deepcopy(fx["within_root_renyi2_pairs"])
    bw_gap["all_obs"] = [bw_gap["all_obs"][1], bw_gap["all_obs"][1]]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], bw_gap, fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        ),
        "CONSERVATION_ERROR",
    )
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            {"all_t4a": 0}, fx["control_renyi2_metrics"],
        ),
        "INVALID_GE_COUNTS",
    )
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], {"quran_stem": {}},
        ),
        "INVALID_CONTROLS",
    )
    bc1 = copy.deepcopy(fx["control_renyi2_metrics"]); bc1["quran_stem"] = {"global_c2": [1, 10]}
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], bc1,
        ),
        "INVALID_CONTROL_ENTRY",
    )
    bc2 = copy.deepcopy(fx["control_renyi2_metrics"]); bc2["kalila_prose"]["w20_t4a_pooled"] = [100, 1000]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], bc2,
        ),
        "CONSERVATION_ERROR",
    )
    for bad_gc2 in ([1, 1000000], [100, 101], [1001, 1000000]):
        bc3 = copy.deepcopy(fx["control_renyi2_metrics"]); bc3["poetry_pooled"]["global_c2"] = bad_gc2
        expect_error(
            lambda m=bc3: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
                fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
                fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
                fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
                fx["within_root_ge_counts"], m,
            ),
            "CONSERVATION_ERROR",
        )
    bc4 = copy.deepcopy(fx["control_renyi2_metrics"])
    bc4["poetry_pooled"]["w20_t4a_pooled"] = [0, bc4["poetry_pooled"]["w20_obs"][1] * fx["n_shuffles"]]
    expect_error(
        lambda: oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], bc4,
        ),
        "ZERO_DENOM",
    )

    # Finding #7: Pin EVERY SINGLE prose & poetry comparison conjunct independently (kills L516 survivor!)
    for ctrl_k in ("quran_stem", "kalila_prose", "adab_prose"):
        c_hi_p = copy.deepcopy(fx["control_renyi2_metrics"])
        c_hi_p[ctrl_k]["w20_ge_count"] = 20  # p = 21/251 > 1/20
        r = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], c_hi_p,
        )
        check(r["shared_prose_renyi2_lift"] is False and r["passed"] is False, f"{ctrl_k} p>alpha fails")

    # Pin kalila_lift > quran_lift
    c_kl = copy.deepcopy(fx["control_renyi2_metrics"])
    c_kl["kalila_prose"]["w20_obs"] = [4300, c_kl["kalila_prose"]["w20_obs"][1]]
    check(
        oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], c_kl,
        )["shared_prose_renyi2_lift"] is False,
        "kalila_lift <= quran_lift fails",
    )
    # Pin poetry_d2 > each of quran_d2, kalila_d2, adab_d2 independently!
    for cmp_k in ("quran_stem", "kalila_prose", "adab_prose"):
        c_pd = copy.deepcopy(fx["control_renyi2_metrics"])
        # Give cmp_k a super-high D2 (1000/1000000 -> D2=1000 > poetry 477.68) while keeping the other 2 < poetry!
        c_pd[cmp_k]["global_c2"] = [1000, 1000000]
        r_pd = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], c_pd,
        )
        check(r_pd["poetry_higher_effective_diversity"] is False and r_pd["passed"] is False, f"poetry_d2 <= {cmp_k}_d2 fails")

    # Pin EVERY SINGLE agency_matrix_nontrivial & passed conjunct independently!
    # 1. poly_ratio < 1/3 (313/942 < 1/3)
    r_poly = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
        fx["total_unique_roots"], fx["verb_roots"], 313,
        fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
        fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
        fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
    )
    check(r_poly["agency_matrix_nontrivial"] is False and r_poly["passed"] is False, "poly_ratio < 1/3 fails")
    # 2. derived_share < 1/3 (raise GROUND_I & verb_tokens_i_x so derived/total < 1/3)
    ops_lo = dict(fx["op_class_counts"]); ops_lo["GROUND_I"] += 5000
    r_der = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
        fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
        fx["verb_tokens_i_x"] + 5000, fx["form_xii_tokens"], ops_lo,
        fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
        fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
    )
    check(r_der["agency_matrix_nontrivial"] is False and r_der["passed"] is False, "derived_share < 1/3 fails")
    # 3. transition thresholds I+IV < 50, II+V < 20, III+VI < 10
    for tk, bad_v in (("I+IV", 49), ("II+V", 19), ("III+VI", 9)):
        tr_lo = dict(fx["transition_pair_counts"]); tr_lo[tk] = bad_v
        r_tr = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
            fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
            fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
            tr_lo, fx["within_root_renyi2_pairs"],
            fx["within_root_ge_counts"], fx["control_renyi2_metrics"],
        )
        check(r_tr["agency_matrix_nontrivial"] is False and r_tr["passed"] is False, f"{tk} < thresh fails")
    # 4. wazn_beats_nulls False alone
    ge_bad = dict(fx["within_root_ge_counts"]); ge_bad["all_t4b"] = 20
    r_wb = oracle.audit_wazn_agency_matrix_and_renyi2_exact(
        fx["total_unique_roots"], fx["verb_roots"], fx["poly_wazn_roots"],
        fx["verb_tokens_i_x"], fx["form_xii_tokens"], fx["op_class_counts"],
        fx["transition_pair_counts"], fx["within_root_renyi2_pairs"],
        ge_bad, fx["control_renyi2_metrics"],
    )
    check(r_wb["within_root_wazn_beats_nulls"] is False and r_wb["passed"] is False, "wazn_beats_nulls fails")


def test_pillar2_context_topology_b250_and_conservation():
    cm = copy.deepcopy(audit.STANDALONE_FIXTURE["context_metrics"])
    p2 = oracle.audit_context_neighborhood_topology_exact(cm, n_shuffles=250)
    check(p2["passed"] is True, "p2 passes fixture")
    check(p2["split_half_label"] == "split_half_internal_consistency_not_unseen", "honest split label")

    expect_error(lambda: oracle.audit_context_neighborhood_topology_exact({"ctx_r2_all": 0.1}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.audit_context_neighborhood_topology_exact({"ctx_r2_all": [1, 2]}), "INVALID_METRICS")

    for key, bad_val in (
        ("cooccur_all", [cm["cooccur_all"][0] + 1, cm["cooccur_all"][1]]),
        ("cooccur_null_pooled", [cm["cooccur_null_pooled"][0] + 1, cm["cooccur_null_pooled"][1]]),
        ("ctx_jaccard_all", [1, 100]),
        ("ctx_jaccard_null_pooled", [1, 100]),
        ("ctx_r2_all", [6, 1000]),
        ("ctx_r2_null_pooled", [6, 1000]),
    ):
        mb = copy.deepcopy(cm); mb[key] = bad_val
        expect_error(lambda m=mb: oracle.audit_context_neighborhood_topology_exact(m), "SPLIT_SUM_MISMATCH")

    mz = copy.deepcopy(cm)
    for k in ("ctx_r2_null_pooled", "ctx_r2_odd_null_pooled", "ctx_r2_even_null_pooled"):
        mz[k] = [0, mz[k][1]]
    expect_error(lambda: oracle.audit_context_neighborhood_topology_exact(mz), "ZERO_DENOM")

    mb_ext = copy.deepcopy(cm); mb_ext["extreme_counts"] = {"ctx_r2_all": 0}
    expect_error(lambda: oracle.audit_context_neighborhood_topology_exact(mb_ext), "INVALID_EXTREME_COUNTS")

    # Pin ALL 9 Holm rejections individually
    for ek in (
        "ctx_r2_all", "ctx_r2_odd", "ctx_r2_even",
        "ctx_jaccard_all", "ctx_jaccard_odd", "ctx_jaccard_even",
        "cooccur_all", "cooccur_odd", "cooccur_even",
    ):
        m_hi = copy.deepcopy(cm)
        m_hi["extreme_counts"][ek] = 20
        check(oracle.audit_context_neighborhood_topology_exact(m_hi)["passed"] is False, f"{ek} holm breach fails")

    # Pin ALL 9 directional inequality conjuncts individually while preserving exact split conservation!
    def _clean_p2():
        return {
            "ctx_r2_all": [20, 200], "ctx_r2_odd": [10, 100], "ctx_r2_even": [10, 100],
            "ctx_r2_null_pooled": [10, 200], "ctx_r2_odd_null_pooled": [5, 100], "ctx_r2_even_null_pooled": [5, 100],
            "ctx_jaccard_all": [20, 180], "ctx_jaccard_odd": [10, 90], "ctx_jaccard_even": [10, 90],
            "ctx_jaccard_null_pooled": [40, 160], "ctx_jaccard_odd_null_pooled": [20, 80], "ctx_jaccard_even_null_pooled": [20, 80],
            "cooccur_all": [50, 200], "cooccur_odd": [25, 100], "cooccur_even": [25, 100],
            "cooccur_null_pooled": [20, 200], "cooccur_odd_null_pooled": [10, 100], "cooccur_even_null_pooled": [10, 100],
            "extreme_counts": {k: 0 for k in cm["extreme_counts"]},
        }
    check(oracle.audit_context_neighborhood_topology_exact(_clean_p2())["passed"] is True, "clean p2 base passes")
    # lift_all <= 1 alone
    m = _clean_p2(); m["ctx_r2_null_pooled"] = [20, 200]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "lift_all <= 1 fails")
    # lift_odd <= 1 alone
    m = _clean_p2(); m["ctx_r2_odd"] = [5, 100]; m["ctx_r2_even"] = [15, 100]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "lift_odd <= 1 fails")
    # lift_even <= 1 alone
    m = _clean_p2(); m["ctx_r2_odd"] = [15, 100]; m["ctx_r2_even"] = [5, 100]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "lift_even <= 1 fails")
    # ctx_jaccard_all >= null alone
    m = _clean_p2(); m["ctx_jaccard_all"] = [40, 160]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "jaccard_all >= null fails")
    # ctx_jaccard_odd >= null alone
    m = _clean_p2(); m["ctx_jaccard_odd"] = [20, 80]; m["ctx_jaccard_all"] = [30, 170]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "jaccard_odd >= null fails")
    # ctx_jaccard_even >= null alone
    m = _clean_p2(); m["ctx_jaccard_even"] = [20, 80]; m["ctx_jaccard_all"] = [30, 170]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "jaccard_even >= null fails")
    # cooccur_all <= null alone (Simpson's paradox: odd 2/100 > 1/100, even 6/10 > 500/1000, yet all 8/110 < 501/1100!)
    m = _clean_p2()
    m["cooccur_odd"] = [2, 100]; m["cooccur_even"] = [6, 10]; m["cooccur_all"] = [8, 110]
    m["cooccur_odd_null_pooled"] = [1, 100]; m["cooccur_even_null_pooled"] = [500, 1000]; m["cooccur_null_pooled"] = [501, 1100]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "cooccur_all <= null fails")
    # cooccur_odd <= null alone
    m = _clean_p2(); m["cooccur_odd"] = [10, 100]; m["cooccur_even"] = [40, 100]; m["cooccur_all"] = [50, 200]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "cooccur_odd <= null fails")
    # cooccur_even <= null alone
    m = _clean_p2(); m["cooccur_odd"] = [40, 100]; m["cooccur_even"] = [10, 100]; m["cooccur_all"] = [50, 200]
    check(oracle.audit_context_neighborhood_topology_exact(m)["passed"] is False, "cooccur_even <= null fails")


def test_pillar3_lemma_shuffle_distance_strata_and_both_translators():
    fx = copy.deepcopy(audit.STANDALONE_FIXTURE)
    p3 = oracle.audit_two_layer_projection_defect_exact(
        fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"],
        fx["lemma_shuffle_null"], fx["distance_strata"], n_shuffles=fx["n_shuffles"],
    )
    check(p3["passed"] is True, "p3 passes fixture")
    check(p3["all_distance_strata_positive_both"] is True, "4/4 strata positive")
    check(p3["lemma_shuffle_null"]["per_root_holm_sahih"]["rejected_at_alpha"]["wzn"] is False, "wzn honest non-sig")
    check(p3["lemma_shuffle_null"]["per_root_holm_pickthall"]["rejected_at_alpha"]["Erj"] is False, "Erj pick non-sig")

    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact([{"x": 0.1}], [9, 10], [9, 10], {}, {}),
        "FLOAT_FORBIDDEN",
    )
    expect_error(lambda: oracle.audit_two_layer_projection_defect_exact([], [9, 10], [9, 10], {}, {}), "INVALID_RECORDS")
    expect_error(lambda: oracle.audit_two_layer_projection_defect_exact(["bad"], [9, 10], [9, 10], {}, {}), "INVALID_RECORD")

    # Duplicate root, partition mismatch, Turan bound, pigeonhole upper & converse
    recs_dup = copy.deepcopy(fx["root_records"][:2])
    recs_dup[1]["root"] = recs_dup[0]["root"].upper()
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            recs_dup, fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], fx["distance_strata"]
        ),
        "DUPLICATE_ROOT",
    )
    recs_pm = copy.deepcopy(fx["root_records"])
    recs_pm[2]["cross_lemma_pairs"] -= 1
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            recs_pm, fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], fx["distance_strata"]
        ),
        "PARTITION_MISMATCH",
    )
    recs_turan = copy.deepcopy(fx["root_records"])
    recs_turan[3]["same_lemma_pairs"] = 10  # flk: V=25, L=2 -> turan_min=144
    recs_turan[3]["cross_lemma_pairs"] = 290
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            recs_turan, fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], fx["distance_strata"]
        ),
        "LEMMA_MISMATCH",
    )
    recs_lp = copy.deepcopy(fx["root_records"])
    recs_lp[2]["sahih_lost_pairs"] -= 1
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            recs_lp, fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], fx["distance_strata"]
        ),
        "PARTITION_MISMATCH",
    )
    # Insufficient multi-lemma roots (<2)
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"][:3], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], fx["distance_strata"]
        ),
        "INSUFFICIENT_PARTITION",
    )
    # Invalid lemma_shuffle_null & quantile inversion & per-root mismatch
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], {}, fx["distance_strata"]
        ),
        "INVALID_LEMMA_NULL",
    )
    lsn_q = copy.deepcopy(fx["lemma_shuffle_null"])
    lsn_q["sahih_q025"] = [1, 2]; lsn_q["sahih_q975"] = [0, 1]
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], lsn_q, fx["distance_strata"]
        ),
        "CONSERVATION_ERROR",
    )
    lsn_pr = copy.deepcopy(fx["lemma_shuffle_null"])
    lsn_pr["per_root_sahih_ge"] = {"sbH": 0}
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], lsn_pr, fx["distance_strata"]
        ),
        "INVALID_LEMMA_NULL",
    )
    # Invalid distance_strata & conservation mismatch
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], {}
        ),
        "INVALID_STRATA",
    )
    st_bad = copy.deepcopy(fx["distance_strata"]); st_bad["same_surah_near"] = {"same_pairs": 1}
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], st_bad
        ),
        "INVALID_STRATUM_ENTRY",
    )
    st_sum = copy.deepcopy(fx["distance_strata"]); st_sum["same_surah_near"]["same_pairs"] += 1
    expect_error(
        lambda: oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], st_sum
        ),
        "CONSERVATION_ERROR",
    )

    # Finding #7: Pin BOTH translators independently (kills @orda-aska L816 survivor!)
    # 1) Sahih bg breach while Pickthall passes
    check(
        oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], [400, 1000], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], fx["distance_strata"]
        )["passed"] is False,
        "sahih >= bg_sahih fails",
    )
    # 2) Pickthall bg breach while Sahih passes (EXACTLY kills dropping p_overall < bg_pick!)
    check(
        oracle.audit_two_layer_projection_defect_exact(
            fx["root_records"], fx["bg_sahih_pair"], [500, 1000], fx["lemma_shuffle_null"], fx["distance_strata"]
        )["passed"] is False,
        "pickthall >= bg_pick fails",
    )
    # 3) Sahih vs Pickthall lemma-shuffle p > alpha independently
    for tr_k in ("sahih_ge_count", "pickthall_ge_count"):
        lsn_f = copy.deepcopy(fx["lemma_shuffle_null"]); lsn_f[tr_k] = 20
        check(
            oracle.audit_two_layer_projection_defect_exact(
                fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], lsn_f, fx["distance_strata"]
            )["passed"] is False,
            f"lsn {tr_k} breach fails",
        )
    # 4) Negative distance-stratum gap on Pickthall while Sahih positive (shifting lost counts between strata to keep exact sum!)
    st_neg = copy.deepcopy(fx["distance_strata"])
    # Move 150 pickthall_same_lost from diff_surah_far into same_surah_near (426 same -> 123+150=273/426=0.6408 > 138/222=0.6216!)
    st_neg["same_surah_near"]["pickthall_same_lost"] += 150
    st_neg["diff_surah_far"]["pickthall_same_lost"] -= 150
    r_st_neg = oracle.audit_two_layer_projection_defect_exact(
        fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"], fx["lemma_shuffle_null"], st_neg
    )
    check(
        r_st_neg["all_distance_strata_positive_both"] is False
        and r_st_neg["unanimous_cross_lemma_amplification"] is False
        and r_st_neg["passed"] is False,
        "stratum gap <= 0 fails",
    )

    # 5) Pin s_same_pool > 0, p_same_pool > 0, multi_lemma_s_strict, multi_lemma_p_strict individually!
    def _tiny_p3(s_same_l=1, p_same_l=1, r1_s_cross=10, r1_p_cross=10):
        # 2 roots r1, r2 each with V=8 (28 pairs: 12 same, 16 cross, L=2 -> turan_min=12)
        recs = [
            {
                "root": "r1", "occurrences": 8, "verse_count": 8, "unique_lemmas": 2,
                "sahih_top_count": 4, "pickthall_top_count": 4,
                "same_lemma_pairs": 12, "cross_lemma_pairs": 16,
                "sahih_same_lost": s_same_l, "sahih_cross_lost": r1_s_cross,
                "pickthall_same_lost": p_same_l, "pickthall_cross_lost": r1_p_cross,
                "sahih_lost_pairs": s_same_l + r1_s_cross, "pickthall_lost_pairs": p_same_l + r1_p_cross,
            },
            {
                "root": "r2", "occurrences": 8, "verse_count": 8, "unique_lemmas": 2,
                "sahih_top_count": 4, "pickthall_top_count": 4,
                "same_lemma_pairs": 12, "cross_lemma_pairs": 16,
                "sahih_same_lost": s_same_l, "sahih_cross_lost": 12,
                "pickthall_same_lost": p_same_l, "pickthall_cross_lost": 12,
                "sahih_lost_pairs": s_same_l + 12, "pickthall_lost_pairs": p_same_l + 12,
            },
        ]
        lsn = {
            "sahih_ge_count": 0, "pickthall_ge_count": 0,
            "sahih_q025": [-1, 10], "sahih_q975": [1, 10],
            "pickthall_q025": [-1, 10], "pickthall_q975": [1, 10],
            "per_root_sahih_ge": {"r1": 0, "r2": 0}, "per_root_pickthall_ge": {"r1": 0, "r2": 0},
        }
        # Split 24 same & 32 cross evenly into 4 strata (6 same, 8 cross each)
        s_same_tot = 2 * s_same_l
        p_same_tot = 2 * p_same_l
        s_cross_tot = r1_s_cross + 12
        p_cross_tot = r1_p_cross + 12
        st = {}
        names = ("same_surah_near", "same_surah_far", "diff_surah_near", "diff_surah_far")
        for idx, nm in enumerate(names):
            ss = (s_same_tot // 4) + (1 if idx < (s_same_tot % 4) else 0)
            ps = (p_same_tot // 4) + (1 if idx < (p_same_tot % 4) else 0)
            sc = (s_cross_tot // 4) + (1 if idx < (s_cross_tot % 4) else 0)
            pc = (p_cross_tot // 4) + (1 if idx < (p_cross_tot % 4) else 0)
            st[nm] = {
                "same_pairs": 6, "cross_pairs": 8,
                "sahih_same_lost": ss, "sahih_cross_lost": sc,
                "pickthall_same_lost": ps, "pickthall_cross_lost": pc,
            }
        return oracle.audit_two_layer_projection_defect_exact(recs, [9, 10], [9, 10], lsn, st, n_shuffles=250)

    check(_tiny_p3()["passed"] is True, "tiny p3 base passes")
    # s_same_pool == 0 alone -> intra_lemma_nonzero False & passed False
    r_ss0 = _tiny_p3(s_same_l=0, p_same_l=1)
    check(r_ss0["intra_lemma_polysemy_nonzero"] is False and r_ss0["passed"] is False, "s_same_pool == 0 fails")
    # p_same_pool == 0 alone -> intra_lemma_nonzero False & passed False
    r_ps0 = _tiny_p3(s_same_l=1, p_same_l=0)
    check(r_ps0["intra_lemma_polysemy_nonzero"] is False and r_ps0["passed"] is False, "p_same_pool == 0 fails")
    # multi_lemma_s_strict < tested alone (r1 sahih same 1/12 vs cross 1/16 -> cross < same, while stratum0 sc = 1+12-9 = 4/8 > 2/6!)
    r_ms = _tiny_p3(s_same_l=1, p_same_l=1, r1_s_cross=1, r1_p_cross=10)
    check(r_ms["unanimous_cross_lemma_amplification"] is False and r_ms["passed"] is False, "multi_lemma_s_strict fails")
    # multi_lemma_p_strict < tested alone
    r_mp = _tiny_p3(s_same_l=1, p_same_l=1, r1_s_cross=10, r1_p_cross=1)
    check(r_mp["unanimous_cross_lemma_amplification"] is False and r_mp["passed"] is False, "multi_lemma_p_strict fails")


def test_pillar4_gate_mode_flag_and_rederivation():
    cert = audit.run_audit(live=False)
    check(cert["verdict"] == "AUDITED_ARABIC_LEXICON_HONEST_LEDGER", "verdict")
    check(cert["mode"] == "standalone_fixture_replay", "mode")
    check(cert["live_corpus_recounted"] is False, "standalone live flag False")
    check(cert["certificate_sha256"] == EXPECTED_STANDALONE_SHA, f"sha mismatch: {cert['certificate_sha256']}")

    p1 = cert["pillar1_wazn_agency_and_renyi2"]
    p2 = cert["pillar2_context_neighborhood_topology"]
    p3 = cert["pillar3_two_layer_projection_defect"]
    axes = dict(cert["five_axis_audit_checks"])
    pins = dict(audit.EXPECTED_CORPUS_SHA256)

    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, {"a": 1.0}, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "FLOAT_FORBIDDEN",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("bad", False, pins, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "INVALID_MODE",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", True, pins, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "MODE_MISMATCH",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, {}, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "MISSING_PROVENANCE",
    )
    for bp in ("/abs/p", "../esc", "FILE:///etc/passwd", "sub\\dir"):
        expect_error(
            lambda x=bp: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, {x: "a" * 64}, audit.AUDIT_FEATURES, p1, p2, p3, axes),
            "UNSAFE_PIN_PATH",
        )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, {"a": "a" * 64, " a ": "a" * 64}, audit.AUDIT_FEATURES, p1, p2, p3, axes),
        "DUPLICATE_PIN_PATH",
    )
    for bs in ("A" * 64, "a" * 64 + "\n", "0" * 64, 123):
        expect_error(
            lambda x=bs: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, {"x": x}, audit.AUDIT_FEATURES, p1, p2, p3, axes),
            "INVALID_SHA256",
        )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, p1, p2, p3, {"bad": True}),
        "INVALID_AXES",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, "bad", p2, p3, axes),
        "INVALID_PILLAR",
    )
    # Full re-derivation contradiction checks on P1, P2, P3, & Axes
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, {"passed": True}, p2, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    bp1c = copy.deepcopy(p1); bp1c["controls_renyi2"]["quran_stem"] = "bad"
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, bp1c, p2, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    bp1 = copy.deepcopy(p1); bp1["agency_matrix_nontrivial"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, bp1, p2, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, p1, {"passed": True}, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    bp2 = copy.deepcopy(p2); bp2["distinct_neighborhoods_vs_background"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, p1, bp2, p3, axes),
        "PILLAR_CONTRADICTION",
    )
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, p1, p2, {"passed": True}, axes),
        "PILLAR_CONTRADICTION",
    )
    bp3 = copy.deepcopy(p3); bp3["unanimous_cross_lemma_amplification"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, p1, p2, bp3, axes),
        "PILLAR_CONTRADICTION",
    )
    bax = dict(axes); bax["two_translator_agreement"] = False
    expect_error(
        lambda: oracle.certify_arabic_lexicon_own_terms_gate("standalone_fixture_replay", False, pins, audit.AUDIT_FEATURES, p1, p2, p3, bax),
        "AXIS_CONTRADICTION",
    )


def test_known_answer_live_pipeline_exact():
    """Finding #7: Hand-computed known-answer mini-corpus verifying exact integer counts
    through the ACTUAL live parser & compute_live_measurements() pipeline!
    """
    check(audit.default_corpus_dir().endswith("corpora"), "default corpus dir -> corpora")
    expect_error(lambda: audit.parse_tanzil_lines(["bad_line\n"]), "PARSE_ERROR")

    # Hand-constructed mini-corpus:
    # 2 surahs (1 odd, 2 even), 4 verses total: (1,1), (1,2), (2,1), (2,2)
    # Root 'sbH' in 3 verses:
    #   (1,1): V Form I  LEM:L1  Sahih="exalt water"    Pick="praise water"
    #   (1,2): V Form II LEM:L1  Sahih="exalt heaven"   Pick="praise heaven"
    #   (2,1): V Form IV LEM:L2  Sahih="glide cosmos"   Pick="float cosmos"
    # Hand-calculated exact counts for 'sbH':
    #   occurrences=3, verse_count=3, unique_lemmas=2
    #   pairs=3: same_lemma={(1,1)-(1,2)} => 1; cross_lemma={(1,1)-(2,1),(1,2)-(2,1)} => 2
    #   Sahih: (1,1)& (1,2) share 'exalt' (0 same_lost); (2,1) shares nothing with (1,1),(1,2) (2 cross_lost) -> total_lost=2
    #   Pick:  (1,1)& (1,2) share 'prais' (0 same_lost); (2,1) shares nothing with (1,1),(1,2) (2 cross_lost) -> total_lost=2
    #   Distance strata for 'sbH': (1,1)-(1,2) is same_surah_near (1 same, 0 lost);
    #     (1,1)-(2,1) & (1,2)-(2,1) are diff_surah_near (2 cross, 2 lost both)
    # Root 'flk' in 3 verses:
    #   (1,1): N LEM:F1  (shares verse with sbH -> cooccur!)
    #   (2,1): N LEM:F1
    #   (2,2): N LEM:F2  Sahih="orbit galaxy" Pick="orbit galaxy"
    #   Hand-calculated exact counts for 'flk':
    #   occurrences=3, verse_count=3, unique_lemmas=2, same=1 {(1,1)-(2,1)}, cross=2 {(1,1)-(2,2),(2,1)-(2,2)}
    #   Sahih: (1,1)={'exalt','water'}, (2,1)={'glid','cosmo'} -> NO overlap! same_lost=1; cross_lost=2 -> total_lost=3
    #   Pick:  (1,1)={'prais','water'}, (2,1)={'float','cosmo'} -> NO overlap! same_lost=1; cross_lost=2 -> total_lost=3
    # Within-root wazn Renyi-2 for ALL verb tokens:
    #   sbH has 3 verbs: Form I (1), Form II (1), Form IV (1) -> num = 1^2+1^2+1^2 = 3, den = 3^2 = 9!
    #   ktb in (2,2): V Form XII -> form_xii_tokens = 1 (excluded from I-X)
    #   Total unique roots = 3 (sbH, flk, ktb), verb_roots = 1 (sbH), poly_wazn_roots = 1, verb_tokens_i_x = 3
    #   op_class_counts: GROUND_I=1, CAUS_INTENS_II_III_IV=2
    morph = "\n".join([
        "LOCATION\tFORM\tTAG\tFEATURES",
        "(1:1:1:1)\tf\tV\tSTEM|POS:V|LEM:L1|ROOT:sbH",
        "(1:1:2:1)\tf\tN\tSTEM|POS:N|LEM:F1|ROOT:flk",
        "(1:2:1:1)\tf\tV\tSTEM|POS:V|(II)|LEM:L1|ROOT:sbH",
        "(2:1:1:1)\tf\tV\tSTEM|POS:V|(IV)|LEM:L2|ROOT:sbH",
        "(2:1:2:1)\tf\tN\tSTEM|POS:N|LEM:F1|ROOT:flk",
        "(2:2:1:1)\tf\tN\tSTEM|POS:N|LEM:F2|ROOT:flk",
        "(2:2:2:1)\tf\tV\tSTEM|POS:V|(XII)|LEM:K1|ROOT:ktb",
    ]) + "\n"
    # Uthmani: 8 Arabic tokens ("ktb ktb ktb sbh" x 2) -> W=4 blocks: block0={ktb:3,sbh:1}, block1={ktb:3,sbh:1}
    # Hand-calculated global_c2: ktb=6, sbh=2, N=8 -> num = 36+4 = 40, den = 64!
    # Hand-calculated W=4 cross-collision: 3*3 + 1*1 = 10, den = 1*4*4 = 16!
    w1 = "\u0643\u062a\u0628"
    w2 = "\u0633\u0628\u062d"
    uth = f"1|1|{w1} {w1}\n1|2|{w1} {w2}\n2|1|{w1} {w1}\n2|2|{w1} {w2}\n"
    sahih = "1|1|exalt water\n1|2|exalt heaven\n2|1|glide cosmos\n2|2|orbit galaxy\n"
    pick = "1|1|praise water\n1|2|praise heaven\n2|1|float cosmos\n2|2|orbit galaxy\n"
    openiti = f"#META#Header#End#\n### s1\n{w1} {w1} {w1} {w2}\n{w1} {w1} {w1} {w2}\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "arabic_morphology_quranic-corpus"))
        os.makedirs(os.path.join(tmpdir, "openiti_controls"))
        fmap = {
            "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt": morph,
            "tanzil-quran-uthmani.txt": uth,
            "tanzil-en.sahih.txt": sahih,
            "tanzil-en.pickthall.txt": pick,
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
        bad_pins = dict(pins); bad_pins["missing.txt"] = "a" * 64
        expect_error(lambda: audit.verify_corpus_hashes(tmpdir, expected_hashes=bad_pins), "CORPUS_MISSING")

        m = audit.compute_live_measurements(
            tmpdir, expected_hashes=pins, ctrl_window=4, bg_pair_count=2, min_multi_verses=3, n_shuffles=5
        )
        # Assert EVERY SINGLE HAND-CALCULATED KNOWN ANSWER!
        check(m["total_unique_roots"] == 3, f"roots: {m['total_unique_roots']}")
        check(m["verb_roots"] == 1 and m["poly_wazn_roots"] == 1, "verb roots")
        check(m["verb_tokens_i_x"] == 3 and m["form_xii_tokens"] == 1, "verb tokens")
        check(m["op_class_counts"] == {"GROUND_I": 1, "CAUS_INTENS_II_III_IV": 2}, f"ops: {m['op_class_counts']}")
        check(m["within_root_renyi2_pairs"]["all_obs"] == [3, 9], f"wr obs: {m['within_root_renyi2_pairs']['all_obs']}")
        check(m["control_renyi2_metrics"]["quran_stem"]["global_c2"] == [40, 64], "known-answer global_c2 40/64")
        check(m["control_renyi2_metrics"]["quran_stem"]["w20_obs"] == [10, 16], "known-answer w4 cross 10/16")
        by_r = {r["root"]: r for r in m["root_records"]}
        sbh = by_r["sbH"]
        check(
            (sbh["occurrences"], sbh["verse_count"], sbh["unique_lemmas"], sbh["same_lemma_pairs"], sbh["cross_lemma_pairs"],
             sbh["sahih_same_lost"], sbh["sahih_cross_lost"], sbh["pickthall_same_lost"], sbh["pickthall_cross_lost"])
            == (3, 3, 2, 1, 2, 0, 2, 0, 2),
            f"known-answer sbH: {sbh}",
        )
        flk = by_r["flk"]
        check(
            (flk["same_lemma_pairs"], flk["cross_lemma_pairs"], flk["sahih_same_lost"], flk["sahih_cross_lost"])
            == (1, 2, 1, 2),
            f"known-answer flk: {flk}",
        )
        # Co-occurrence: 4 verses have target roots; (1,1) and (2,1) have BOTH sbH & flk -> 2/4!
        check(m["context_metrics"]["cooccur_all"] == [2, 4], f"known-answer cooccur: {m['context_metrics']['cooccur_all']}")
        # Distance strata exact known answers:
        # sbH: (1,1)-(1,2) same_surah_near same=1 s_lost=0; (1,1)-(2,1) & (1,2)-(2,1) diff_surah_near cross=2 s_lost=2
        # flk: (1,1)-(2,1) diff_surah_near same=1 s_lost=1; (1,1)-(2,2) diff_surah_near cross=1 s_lost=1; (2,1)-(2,2) same_surah_near cross=1 s_lost=1
        check(m["distance_strata"]["same_surah_near"]["same_pairs"] == 1, "known-answer stratum same_surah_near same")
        check(m["distance_strata"]["same_surah_near"]["cross_pairs"] == 1, "known-answer stratum same_surah_near cross")
        check(m["distance_strata"]["diff_surah_near"]["same_pairs"] == 1, "known-answer stratum diff_surah_near same")
        check(m["distance_strata"]["diff_surah_near"]["cross_pairs"] == 3, "known-answer stratum diff_surah_near cross")

        # Exercise CLI standalone + --output + failing rc=1 + live error propagation
        out_p = os.path.join(tmpdir, "cert.json")
        buf = io.StringIO()
        old_out = sys.stdout
        try:
            sys.stdout = buf
            rc = audit.main(["--standalone", "--output", out_p])
        finally:
            sys.stdout = old_out
        check(rc == 0, "main rc=0")
        with open(out_p, "rb") as f:
            check(json.loads(f.read().decode("utf-8"))["certificate_sha256"] == EXPECTED_STANDALONE_SHA, "cli sha")

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
            sys.stdout = old_out
        check(rc_fail == 1, "main rc=1")
        expect_error(lambda: audit.run_audit(live=True, corpus_dir=tmpdir), "SHA256_MISMATCH")

    proc = subprocess.run(
        [sys.executable, "-I", "-B", "-W", "error", os.path.join(_SCRIPT_DIR, "arabic_lexicon_audit.py"), "--standalone"],
        capture_output=True, text=True, check=False,
    )
    check(proc.returncode == 0 and json.loads(proc.stdout)["certificate_sha256"] == EXPECTED_STANDALONE_SHA, "subproc -I")


def run_all_tests():
    test_primitives_holm_and_naming_guard()
    test_pillar1_pinning_every_conjunct_and_conservation()
    test_pillar2_context_topology_b250_and_conservation()
    test_pillar3_lemma_shuffle_distance_strata_and_both_translators()
    test_pillar4_gate_mode_flag_and_rederivation()
    test_known_answer_live_pipeline_exact()
    return "ALL_AUDIT094_V2_TESTS_PASSED"


if __name__ == "__main__":
    print(run_all_tests())
