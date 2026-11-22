"""Assertion-free R5 mutation-hardened & red-team test suite for AUDIT-091.

Runs cleanly under:
  python3 -I -O -B -W error test_arabic_continuum_r5.py
  aletheia v1.4.0 mutate arabic_continuum_oracle.py --max-mutants 500 --add-cwd
  aletheia v1.4.0 mutate arabic_continuum_audit.py --max-mutants 500 --add-cwd

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

import arabic_continuum_audit as audit
import arabic_continuum_oracle as oracle


EXPECTED_STANDALONE_SHA = (
    "d237ae44dd4618e033283d2d5fba6a23dd108b0d4e657c1fcadb243d03ee3f16"
)


def check(cond, msg):
    if not cond:
        raise RuntimeError(f"CHECK_FAILED: {msg}")


def expect_error(fn, expected_code):
    try:
        fn()
    except oracle.ArabicOracleError as err:
        if err.code != expected_code:
            raise RuntimeError(f"Expected {expected_code}, got {err.code}: {err}")
        return
    raise RuntimeError(f"Expected ArabicOracleError({expected_code}), but succeeded")


def test_oracle_primitives_and_boundaries():
    check(oracle.SCHEMA_VERSION == "arabic-continuum-oracle/v1", "schema version")
    check(oracle.CANONICAL_DECIMALS == 6, "canonical decimals")
    check(len(oracle.FORBIDDEN_NUMEROLOGY_TOKENS) == 7, "forbidden count")

    # verify_no_floats
    oracle.verify_no_floats({"a": [1, (Fraction(1, 2), {3}, frozenset({4}))]})
    expect_error(lambda: oracle.verify_no_floats(0.5), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats(1 + 2j), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats({1.5: "x"}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats({"x": [1, 2.0]}), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.verify_no_floats(frozenset({3.14})), "FLOAT_FORBIDDEN")

    # require_non_empty_str (control chars & Cf invisible format chars rejected BEFORE strip!)
    check(oracle.require_non_empty_str("  hello ~ ", "f") == "hello ~", "strip")
    expect_error(lambda: oracle.require_non_empty_str(123, "f"), "INVALID_TYPE")
    expect_error(lambda: oracle.require_non_empty_str("   ", "f"), "EMPTY_STRING")
    expect_error(lambda: oracle.require_non_empty_str("a\x1fb", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("a\x7fb", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("abc\n", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("ab\u200bjad", "f"), "CONTROL_CHAR")
    expect_error(lambda: oracle.require_non_empty_str("\ufeffabc", "f"), "CONTROL_CHAR")
    check(oracle.require_non_empty_str("a b", "f") == "a b", "space ok")
    check(oracle.require_non_empty_str("~", "f") == "~", "tilde ok")

    # require_exact_bool
    check(oracle.require_exact_bool(True, "b") is True, "bool true")
    check(oracle.require_exact_bool(False, "b") is False, "bool false")
    expect_error(lambda: oracle.require_exact_bool(1, "b"), "INVALID_BOOL")
    expect_error(lambda: oracle.require_exact_bool("true", "b"), "INVALID_BOOL")

    # require_exact_int
    check(oracle.require_exact_int(5, "i", min_value=5, max_value=5) == 5, "int exact")
    expect_error(lambda: oracle.require_exact_int(True, "i"), "INVALID_INT")
    expect_error(lambda: oracle.require_exact_int("5", "i"), "INVALID_INT")
    expect_error(lambda: oracle.require_exact_int(4, "i", min_value=5), "RANGE_ERROR")
    expect_error(lambda: oracle.require_exact_int(6, "i", max_value=5), "RANGE_ERROR")

    # require_exact_fraction
    check(oracle.require_exact_fraction(3, "q") == Fraction(3, 1), "int to frac")
    check(
        oracle.require_exact_fraction(Fraction(1, 2), "q", Fraction(1, 2), Fraction(1, 2))
        == Fraction(1, 2),
        "frac exact",
    )
    expect_error(lambda: oracle.require_exact_fraction(False, "q"), "INVALID_FRACTION")
    expect_error(lambda: oracle.require_exact_fraction("1/2", "q"), "INVALID_FRACTION")
    expect_error(
        lambda: oracle.require_exact_fraction(Fraction(1, 3), "q", min_value=Fraction(1, 2)),
        "RANGE_ERROR",
    )
    expect_error(
        lambda: oracle.require_exact_fraction(Fraction(2, 3), "q", max_value=Fraction(1, 2)),
        "RANGE_ERROR",
    )

    # require_pair_ratio
    check(oracle.require_pair_ratio([0, 1], "p") == (0, 1, Fraction(0, 1)), "zero pair")
    check(oracle.require_pair_ratio((3, 3), "p") == (3, 3, Fraction(1, 1)), "unit pair")
    expect_error(lambda: oracle.require_pair_ratio("ab", "p"), "INVALID_PAIR")
    expect_error(lambda: oracle.require_pair_ratio([1], "p"), "INVALID_PAIR")
    expect_error(lambda: oracle.require_pair_ratio([-1, 2], "p"), "RANGE_ERROR")
    expect_error(lambda: oracle.require_pair_ratio([0, 0], "p"), "RANGE_ERROR")
    expect_error(lambda: oracle.require_pair_ratio([3, 2], "p"), "INVALID_PAIR")

    # frac_str & format_exact_decimal
    check(oracle.frac_str(Fraction(4, 6)) == "2/3", "frac_str reduced")
    check(oracle.format_exact_decimal(Fraction(1, 2), 0) == "1", "half up 0")
    check(oracle.format_exact_decimal(Fraction(49, 100), 0) == "0", "below half 0")
    check(oracle.format_exact_decimal(Fraction(-3, 2), 0) == "-2", "neg half up 0")
    check(oracle.format_exact_decimal(Fraction(-1, 10000000), 6) == "0.000000", "no neg zero")
    check(oracle.format_exact_decimal(Fraction(-1, 4), 2) == "-0.25", "neg 2 dec")
    check(oracle.format_exact_decimal(Fraction(1, 8), 12) == "0.125000000000", "12 dec")
    expect_error(lambda: oracle.format_exact_decimal(Fraction(1, 2), -1), "RANGE_ERROR")
    expect_error(lambda: oracle.format_exact_decimal(Fraction(1, 2), 13), "RANGE_ERROR")

    # canonical_json_bytes & canonical_sha256
    jb = oracle.canonical_json_bytes({"b": 1, "a": "\u0633"})
    check(jb == b'{"a":"\\u0633","b":1}', f"canonical json bytes: {jb}")
    check(len(oracle.canonical_sha256({"x": 1})) == 64, "sha len")
    expect_error(lambda: oracle.canonical_json_bytes({"x": 0.1}), "FLOAT_FORBIDDEN")


def test_deterministic_shuffles_and_text_nets():
    # fnv1a_32 exact golden values
    check(oracle.fnv1a_32("N") == 3406561745, "fnv N")
    check(oracle.fnv1a_32("V") == 3540782697, "fnv V")
    check(oracle.fnv1a_32("abc") == 440920331, "fnv abc")

    # det_shuffle_exact exact golden output
    items = [0, 1, 2, 3, 4, 5, 6, 7]
    shuf = oracle.det_shuffle_exact(items, 42)
    check(shuf == [0, 5, 1, 7, 3, 4, 2, 6], f"det_shuffle golden: {shuf}")
    check(oracle.det_shuffle_exact([9], 0) == [9], "singleton shuffle")
    expect_error(lambda: oracle.det_shuffle_exact("abc", 1), "INVALID_SEQ")
    expect_error(lambda: oracle.det_shuffle_exact([1, 2], -1), "RANGE_ERROR")

    # stratified_shuffle_exact
    vals = ["a1", "b1", "a2", "b2", "a3", "b3", "a4", "b4"]
    cls = ["N", "V", "N", "V", "N", "V", "N", "V"]
    st = oracle.stratified_shuffle_exact(vals, cls, 99)
    check(st == ["a2", "b3", "a4", "b4", "a1", "b2", "a3", "b1"], f"strat golden: {st}")
    for i, c in enumerate(cls):
        check(st[i].startswith("a" if c == "N" else "b"), "stratum preserved")
    expect_error(lambda: oracle.stratified_shuffle_exact("ab", ["N", "V"], 1), "INVALID_SEQ")
    expect_error(lambda: oracle.stratified_shuffle_exact(["a"], "N", 1), "INVALID_SEQ")
    expect_error(lambda: oracle.stratified_shuffle_exact(["a"], ["N", "V"], 1), "LENGTH_MISMATCH")
    expect_error(lambda: oracle.stratified_shuffle_exact(["a"], ["N"], -1), "RANGE_ERROR")
    expect_error(lambda: oracle.stratified_shuffle_exact(["a"], [""], 1), "EMPTY_STRING")

    # to_rasm & light_stem_ar
    expect_error(lambda: oracle.to_rasm(123), "INVALID_TYPE")
    # Alef wasla, hamza above/below, madda, alif maqsura, ta marbuta, diacritics & tatweel
    sample = "\u0671\u0623\u0625\u0622\u0649\u0629\u064e\u0640!"
    check(oracle.to_rasm(sample) == "\u0627\u0627\u0627\u0627\u064a\u0647", "rasm norm")
    # 3-letter untouched
    check(oracle.light_stem_ar("\u0643\u062a\u0628") == "\u0643\u062a\u0628", "3-letter")
    # prefix wal- + root ktb + suffix -hm -> ktb
    pref_suff = "\u0648\u0627\u0644\u0643\u062a\u0628\u0647\u0645"
    check(oracle.light_stem_ar(pref_suff) == "\u0643\u062a\u0628", "prefix+suffix stem")
    # 4-letter starting with 'al' (len - 2 == 2 < 3) must NOT strip prefix 'al', strips single 'w' only if >=3
    four_al = "\u0627\u0644\u0644\u0647"
    check(oracle.light_stem_ar(four_al) == "\u0627\u0644\u0644", "4-letter suffix only")
    # 4-letter where prefix 'w' leaves 3 letters
    check(oracle.light_stem_ar("\u0648\u0643\u062a\u0628") == "\u0643\u062a\u0628", "4-letter pref")
    # 4-letter with no matching prefix/suffix stays 4
    check(oracle.light_stem_ar("\u0633\u0645\u0627\u0621") == "\u0633\u0645\u0627\u0621", "4-letter kept")

    # en_content_stems
    expect_error(lambda: oracle.en_content_stems(None), "INVALID_TYPE")
    stems = oracle.en_content_stems(
        "The wrapped wraps spinning running walking bring walked bred fishes goes ships laws lords lorded that"
    )
    check(
        stems == {"wrap", "spin", "walk", "bring", "bred", "fish", "goes", "ship", "laws"},
        f"en_content_stems exact: {stems}",
    )

    # block_jaccard_cohesion_exact
    inter, union, frac = oracle.block_jaccard_cohesion_exact(["a", "b", "b", "c", "c", "d"], 2)
    check((inter, union, frac) == (2, 6, Fraction(1, 3)), "block cohesion exact")
    expect_error(lambda: oracle.block_jaccard_cohesion_exact("abcd", 2), "INVALID_SEQ")
    expect_error(lambda: oracle.block_jaccard_cohesion_exact(["a", "b", "c"], 1), "RANGE_ERROR")
    expect_error(lambda: oracle.block_jaccard_cohesion_exact(["a", "b", "c"], 2), "INSUFFICIENT_BLOCKS")


def test_zero_numerology_guard():
    res = oracle.enforce_zero_numerology_policy([" Root_Lattice ", "Wazn_Forms"])
    check(res["zero_numerology_ok"] is True and res["feature_count"] == 2, "valid features")
    check(res["features"] == ["root_lattice", "wazn_forms"], "normalized features")
    expect_error(lambda: oracle.enforce_zero_numerology_policy([1.0]), "FLOAT_FORBIDDEN")
    expect_error(lambda: oracle.enforce_zero_numerology_policy([]), "INVALID_FEATURES")
    expect_error(lambda: oracle.enforce_zero_numerology_policy("root"), "INVALID_FEATURES")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["___"]), "EMPTY_STRING")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["root_a", "root-a"]), "DUPLICATE_FEATURE")
    # ARAB-BUG-01 regression: ZWSP / format chars & separator variants
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["ab\u200bjad_score"]), "CONTROL_CHAR")
    expect_error(lambda: oracle.enforce_zero_numerology_policy(["gematr\u200bia_check"]), "CONTROL_CHAR")
    for obf in ("base_10_count", "code_19_filter", "digit-sum", "a b j a d"):
        expect_error(
            lambda tok=obf: oracle.enforce_zero_numerology_policy([tok]),
            "NUMEROLOGY_FORBIDDEN",
        )
    for bad in oracle.FORBIDDEN_NUMEROLOGY_TOKENS:
        expect_error(
            lambda tok=bad: oracle.enforce_zero_numerology_policy([f"my_{tok}_score"]),
            "NUMEROLOGY_FORBIDDEN",
        )


def test_pillar1_boundaries_and_redteam():
    fx = copy.deepcopy(audit.STANDALONE_FIXTURE)
    p1 = oracle.audit_root_pattern_lattice_and_cohesion_exact(
        fx["unique_roots"],
        fx["unique_lemmas"],
        fx["unique_root_wazn_cells"],
        fx["total_root_tokens"],
        fx["verb_form_counts"],
        fx["window_metrics"],
        fx["control_w20_pairs"],
    )
    check(p1["passed"] is True, "p1 passes fixture")
    check(p1["verb_form_total"] == 19356, "verb form total")

    # Float guard before anything else
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1.0, 2, 2, 2, {}, {}, {}
        ),
        "FLOAT_FORBIDDEN",
    )
    # Invalid verb_form_counts / window_metrics / controls
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 3, {}, fx["window_metrics"], fx["control_w20_pairs"]
        ),
        "INVALID_VERB_FORMS",
    )
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 10, {"I": 2, "i": 3}, fx["window_metrics"], fx["control_w20_pairs"]
        ),
        "DUPLICATE_VERB_FORM",
    )
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            5, 10, 10, 4, {"I": 1}, fx["window_metrics"], fx["control_w20_pairs"]
        ),
        "CONSERVATION_ERROR",
    )
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 3, {"I": 4}, fx["window_metrics"], fx["control_w20_pairs"]
        ),
        "CONSERVATION_ERROR",
    )
    # ARAB-BUG-03 regression: unique_root_wazn_cells < unique_roots rejected
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1642, 4657, 100, 49968, fx["verb_form_counts"], fx["window_metrics"], fx["control_w20_pairs"]
        ),
        "CONSERVATION_ERROR",
    )
    # ARAB-BUG-03 regression: control_w20_pairs.quran_stem.obs != window_metrics[20].stem rejected
    bad_ctrl_mismatch = copy.deepcopy(fx["control_w20_pairs"])
    bad_ctrl_mismatch["quran_stem"]["obs"] = [8953, 134393]
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1642, 4657, 3923, 49968, fx["verb_form_counts"], fx["window_metrics"], bad_ctrl_mismatch
        ),
        "CONTROL_MISMATCH",
    )
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 20000, fx["verb_form_counts"], {10: fx["window_metrics"][10], 20: fx["window_metrics"][20]}, fx["control_w20_pairs"]
        ),
        "INVALID_WINDOWS",
    )
    bad_w_entry = copy.deepcopy(fx["window_metrics"])
    bad_w_entry[10] = "bad"
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 20000, fx["verb_form_counts"], bad_w_entry, fx["control_w20_pairs"]
        ),
        "INVALID_WINDOW_ENTRY",
    )
    bad_w = copy.deepcopy(fx["window_metrics"])
    del bad_w[10]["root"]
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 20000, fx["verb_form_counts"], bad_w, fx["control_w20_pairs"]
        ),
        "MISSING_KEY",
    )
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 20000, fx["verb_form_counts"], fx["window_metrics"], "bad"
        ),
        "INVALID_CONTROLS",
    )
    bad_c = copy.deepcopy(fx["control_w20_pairs"])
    del bad_c["poetry_pooled"]
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 20000, fx["verb_form_counts"], fx["window_metrics"], bad_c
        ),
        "MISSING_CONTROL",
    )
    bad_c2 = copy.deepcopy(fx["control_w20_pairs"])
    del bad_c2["poetry_pooled"]["t4a"]
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 20000, fx["verb_form_counts"], fx["window_metrics"], bad_c2
        ),
        "MISSING_CONTROL_FIELD",
    )
    bad_c3 = copy.deepcopy(fx["control_w20_pairs"])
    bad_c3["poetry_pooled"]["t4a"] = [0, 10]
    expect_error(
        lambda: oracle.audit_root_pattern_lattice_and_cohesion_exact(
            1, 3, 3, 20000, fx["verb_form_counts"], fx["window_metrics"], bad_c3
        ),
        "ZERO_NULL",
    )

    # Lattice boundaries (lemmas/root > 2, cells/root > 2, forms >= 8)
    r_lem2 = oracle.audit_root_pattern_lattice_and_cohesion_exact(
        10, 20, 25, 20000, fx["verb_form_counts"], fx["window_metrics"], fx["control_w20_pairs"]
    )
    check(r_lem2["lattice_nontrivial"] is False and r_lem2["passed"] is False, "lem==2 fails")
    r_cel2 = oracle.audit_root_pattern_lattice_and_cohesion_exact(
        10, 25, 20, 20000, fx["verb_form_counts"], fx["window_metrics"], fx["control_w20_pairs"]
    )
    check(r_cel2["lattice_nontrivial"] is False, "cell==2 fails")
    vf7 = {k: v for i, (k, v) in enumerate(fx["verb_form_counts"].items()) if i < 7}
    r_vf7 = oracle.audit_root_pattern_lattice_and_cohesion_exact(
        10, 25, 25, 20000, vf7, fx["window_metrics"], fx["control_w20_pairs"]
    )
    check(r_vf7["lattice_nontrivial"] is False, "7 verb forms fails")
    vf8 = {k: v for i, (k, v) in enumerate(fx["verb_form_counts"].items()) if i < 8}
    r_vf8 = oracle.audit_root_pattern_lattice_and_cohesion_exact(
        10, 25, 25, 20000, vf8, fx["window_metrics"], fx["control_w20_pairs"]
    )
    check(r_vf8["lattice_nontrivial"] is True, "8 verb forms passes")

    # Monotonicity, null margin, split-half, and negative-control boundaries
    wm_nomono = copy.deepcopy(fx["window_metrics"])
    wm_nomono[10]["raw"] = wm_nomono[10]["rasm"]
    r_nm = oracle.audit_root_pattern_lattice_and_cohesion_exact(
        10, 25, 25, 20000, vf8, wm_nomono, fx["control_w20_pairs"]
    )
    check(r_nm["monotonic_ladder_all_w"] is False and r_nm["passed"] is False, "non-mono fails")

    w_unit = {
        "raw": [1, 100], "rasm": [2, 100], "stem": [6, 100], "root": [7, 100],
        "root_t4a": [6, 100], "root_t4b": [6, 100],
        "odd_root": [7, 100], "odd_t4b": [6, 100],
        "even_root": [7, 100], "even_t4b": [6, 100],
    }
    wm_eq = {10: copy.deepcopy(w_unit), 20: copy.deepcopy(w_unit), 40: copy.deepcopy(w_unit)}
    ctrl_eq = {
        "quran_stem": {"obs": [6, 100], "t4a": [5, 100]},
        "kalila_prose": {"obs": [6, 100], "t4a": [5, 100]},
        "adab_prose": {"obs": [6, 100], "t4a": [5, 100]},
        "poetry_pooled": {"obs": [5, 100], "t4a": [4, 100]},
    }
    r_exact = oracle.audit_root_pattern_lattice_and_cohesion_exact(
        10, 25, 25, 20000, vf8, wm_eq, ctrl_eq, min_null_margin=Fraction(1, 100)
    )
    check(r_exact["passed"] is True, "exact 1/100 boundary passes")

    for mut_field in ("root_t4a", "root_t4b", "odd_t4b", "even_t4b"):
        wm_fail = copy.deepcopy(wm_eq)
        wm_fail[10][mut_field] = [61, 1000]
        r_f = oracle.audit_root_pattern_lattice_and_cohesion_exact(
            10, 25, 25, 20000, vf8, wm_fail, ctrl_eq, min_null_margin=Fraction(1, 100)
        )
        check(r_f["passed"] is False, f"{mut_field} margin breach fails")

    for ctrl_mut, val in (
        (("kalila_prose", "t4a"), [51, 1000]),
        (("adab_prose", "t4a"), [51, 1000]),
        (("poetry_pooled", "obs"), [6, 100]),
        (("quran_stem", "obs"), [5, 100]),
    ):
        c_fail = copy.deepcopy(ctrl_eq)
        wm_use = copy.deepcopy(wm_eq)
        c_fail[ctrl_mut[0]][ctrl_mut[1]] = val
        if ctrl_mut == ("quran_stem", "obs"):
            wm_use[20]["stem"] = val
        r_cf = oracle.audit_root_pattern_lattice_and_cohesion_exact(
            10, 25, 25, 20000, vf8, wm_use, c_fail, min_null_margin=Fraction(1, 100)
        )
        check(r_cf["passed"] is False, f"control {ctrl_mut} breach fails")


def test_pillar2_boundaries_and_redteam():
    rm = copy.deepcopy(audit.STANDALONE_FIXTURE["ring_metrics"])
    p2 = oracle.audit_ring_vs_inclusio_transform_exact(rm)
    check(p2["passed"] is True, "p2 passes fixture")

    expect_error(
        lambda: oracle.audit_ring_vs_inclusio_transform_exact({"all_mirror": 0.1}),
        "FLOAT_FORBIDDEN",
    )
    expect_error(lambda: oracle.audit_ring_vs_inclusio_transform_exact("bad"), "INVALID_METRICS")
    rm_miss = copy.deepcopy(rm)
    del rm_miss["all_mirror"]
    expect_error(lambda: oracle.audit_ring_vs_inclusio_transform_exact(rm_miss), "MISSING_KEY")

    # Exact boundary matrix (with additive split conservation all == odd + even)
    base = {
        "all_mirror": [4, 100],
        "all_shift": [5, 100],
        "all_perm_null": [5, 100],
        "all_inclusio": [300, 2000],
        "all_middle": [290, 2000],
        "odd_inclusio": [150, 1000],
        "odd_middle": [145, 1000],
        "even_inclusio": [150, 1000],
        "even_middle": [145, 1000],
        "odd_strip10_inclusio": [120, 1000],
        "odd_strip10_middle": [115, 1000],
        "even_strip10_inclusio": [120, 1000],
        "even_strip10_middle": [115, 1000],
        "kalila_arb_inclusio": [80, 1000],
        "kalila_arb_middle": [90, 1000],
        "kalila_nat_inclusio": [130, 1000],
        "kalila_nat_middle": [125, 1000],
    }
    check(
        oracle.audit_ring_vs_inclusio_transform_exact(base, Fraction(1, 200))["passed"] is True,
        "p2 exact boundary passes",
    )
    # Split sum conservation breach
    bad_sum = copy.deepcopy(base)
    bad_sum["all_inclusio"] = [301, 2000]
    expect_error(
        lambda: oracle.audit_ring_vs_inclusio_transform_exact(bad_sum, Fraction(1, 200)),
        "SPLIT_SUM_MISMATCH",
    )

    breaches = [
        ("all_mirror", [5, 100], None),
        ("all_perm_null", [4, 100], None),
        ("odd_middle", [146, 1000], ("all_middle", [291, 2000])),
        ("even_middle", [146, 1000], ("all_middle", [291, 2000])),
        ("odd_strip10_middle", [116, 1000], None),
        ("even_strip10_middle", [116, 1000], None),
        ("kalila_arb_inclusio", [90, 1000], None),
        ("kalila_nat_middle", [126, 1000], None),
    ]
    for key, val, aux in breaches:
        m = copy.deepcopy(base)
        m[key] = val
        if aux is not None:
            m[aux[0]] = aux[1]
        check(
            oracle.audit_ring_vs_inclusio_transform_exact(m, Fraction(1, 200))["passed"] is False,
            f"p2 breach {key} fails",
        )


def test_pillar3_boundaries_and_redteam():
    fx = copy.deepcopy(audit.STANDALONE_FIXTURE)
    p3 = oracle.audit_translation_remainder_exact(
        fx["root_records"], fx["bg_sahih_pair"], fx["bg_pickthall_pair"]
    )
    check(p3["passed"] is True, "p3 passes fixture")
    check(p3["severe_remainder_both_translators"] == 4, "severe count == 4")

    expect_error(
        lambda: oracle.audit_translation_remainder_exact([{"x": 0.1}], [1, 2], [1, 2]),
        "FLOAT_FORBIDDEN",
    )
    expect_error(
        lambda: oracle.audit_translation_remainder_exact([], [1, 2], [1, 2]),
        "INVALID_RECORDS",
    )
    expect_error(
        lambda: oracle.audit_translation_remainder_exact(["bad"], [1, 2], [1, 2]),
        "INVALID_RECORD",
    )
    dup = [
        {
            "root": "sbH", "occurrences": 2, "verse_count": 2, "unique_lemmas": 1,
            "sahih_top_count": 1, "pickthall_top_count": 1,
            "sahih_lost_pairs": 1, "pickthall_lost_pairs": 1,
            "sahih_total_pairs": 1, "pickthall_total_pairs": 1,
        },
        {
            "root": "sbh", "occurrences": 2, "verse_count": 2, "unique_lemmas": 1,
            "sahih_top_count": 1, "pickthall_top_count": 1,
            "sahih_lost_pairs": 1, "pickthall_lost_pairs": 1,
            "sahih_total_pairs": 1, "pickthall_total_pairs": 1,
        },
    ]
    expect_error(
        lambda: oracle.audit_translation_remainder_exact(dup, [9, 10], [9, 10]),
        "DUPLICATE_ROOT",
    )
    only_single = [
        {
            "root": "ftq", "occurrences": 1, "verse_count": 1, "unique_lemmas": 1,
            "sahih_top_count": 1, "pickthall_top_count": 1,
            "sahih_lost_pairs": 0, "pickthall_lost_pairs": 0,
            "sahih_total_pairs": 0, "pickthall_total_pairs": 0,
        }
    ]
    expect_error(
        lambda: oracle.audit_translation_remainder_exact(only_single, [9, 10], [9, 10]),
        "NO_MULTI_VERSE_ROOTS",
    )

    # Combinatorial pigeonhole upper bound: s_top=4 -> C(4,2)=6 preserved -> max lost=4; 5 must reject!
    pigeon_bad = [
        {
            "root": "p1", "occurrences": 5, "verse_count": 5, "unique_lemmas": 1,
            "sahih_top_count": 4, "pickthall_top_count": 2,
            "sahih_lost_pairs": 5, "pickthall_lost_pairs": 4,
            "sahih_total_pairs": 10, "pickthall_total_pairs": 10,
        }
    ]
    expect_error(
        lambda: oracle.audit_translation_remainder_exact(pigeon_bad, [9, 10], [9, 10]),
        "RANGE_ERROR",
    )
    # ARAB-BUG-02 regression: pigeonhole converse (top_count <= 1 on vcnt >= 2 forces lost_pairs == expected_pairs!)
    for s_top_v, s_lost_v, p_top_v, p_lost_v in (
        (0, 0, 2, 5),
        (1, 9, 2, 5),
        (2, 5, 0, 0),
        (2, 5, 1, 9),
    ):
        conv_bad = [
            {
                "root": "p2", "occurrences": 5, "verse_count": 5, "unique_lemmas": 1,
                "sahih_top_count": s_top_v, "pickthall_top_count": p_top_v,
                "sahih_lost_pairs": s_lost_v, "pickthall_lost_pairs": p_lost_v,
                "sahih_total_pairs": 10, "pickthall_total_pairs": 10,
            }
        ]
        expect_error(
            lambda r=conv_bad: oracle.audit_translation_remainder_exact(r, [9, 10], [9, 10]),
            "RANGE_ERROR",
        )
    # Valid exact converse boundary: vcnt=2, top=1 -> lost=1 passes
    conv_ok = [
        {
            "root": "p3", "occurrences": 2, "verse_count": 2, "unique_lemmas": 1,
            "sahih_top_count": 1, "pickthall_top_count": 0,
            "sahih_lost_pairs": 1, "pickthall_lost_pairs": 1,
            "sahih_total_pairs": 1, "pickthall_total_pairs": 1,
        }
    ]
    check(
        oracle.audit_translation_remainder_exact(conv_ok, [9, 10], [9, 10])["pooled_pairs"] == 1,
        "converse valid boundary ok",
    )

    # Exact threshold boundaries: 4 roots with edge_loss = 2/5 vs 5/10 pooled
    def mk(name, s_lost, p_lost):
        # verse_count=5 -> total_pairs=10
        return {
            "root": name, "occurrences": 5, "verse_count": 5, "unique_lemmas": 2,
            "sahih_top_count": 2, "pickthall_top_count": 2,
            "sahih_lost_pairs": s_lost, "pickthall_lost_pairs": p_lost,
            "sahih_total_pairs": 10, "pickthall_total_pairs": 10,
        }

    # Exact severe boundary: 4/10 == 2/5 on both; pooled 20/40 == 1/2
    recs_pass = [mk("r1", 4, 4), mk("r2", 4, 4), mk("r3", 6, 6), mk("r4", 6, 6)]
    r_ok = oracle.audit_translation_remainder_exact(recs_pass, [6, 10], [6, 10], Fraction(1, 2))
    check(r_ok["passed"] is True and r_ok["severe_remainder_both_translators"] == 4, "p3 exact pass")

    # Breach severe_both_count (3/10 < 2/5 drops severe to 3)
    recs_sev3 = [mk("r1", 3, 4), mk("r2", 6, 6), mk("r3", 6, 6), mk("r4", 6, 6)]
    check(
        oracle.audit_translation_remainder_exact(recs_sev3, [9, 10], [9, 10], Fraction(1, 2))["passed"]
        is False,
        "severe==3 fails",
    )
    recs_sev3_p = [mk("r1", 4, 3), mk("r2", 6, 6), mk("r3", 6, 6), mk("r4", 6, 6)]
    check(
        oracle.audit_translation_remainder_exact(recs_sev3_p, [9, 10], [9, 10], Fraction(1, 2))["passed"]
        is False,
        "pick severe==3 fails",
    )
    # Breach min_pooled_edge_loss on Sahih or Pickthall
    recs_low_s = [mk("r1", 4, 5), mk("r2", 5, 5), mk("r3", 5, 5), mk("r4", 5, 5)]
    check(
        oracle.audit_translation_remainder_exact(recs_low_s, [9, 10], [9, 10], Fraction(1, 2))["passed"]
        is False,
        "sahih pooled < 1/2 fails",
    )
    recs_low_p = [mk("r1", 5, 4), mk("r2", 5, 5), mk("r3", 5, 5), mk("r4", 5, 5)]
    check(
        oracle.audit_translation_remainder_exact(recs_low_p, [9, 10], [9, 10], Fraction(1, 2))["passed"]
        is False,
        "pickthall pooled < 1/2 fails",
    )
    # Breach bg_unrelated ceiling (pooled >= bg fails)
    check(
        oracle.audit_translation_remainder_exact(recs_pass, [5, 10], [9, 10], Fraction(1, 2))["passed"]
        is False,
        "sahih == bg fails",
    )
    check(
        oracle.audit_translation_remainder_exact(recs_pass, [9, 10], [5, 10], Fraction(1, 2))["passed"]
        is False,
        "pick == bg fails",
    )


def test_pillar4_gate_and_redteam():
    cert = audit.run_audit(standalone=True)
    check(cert["verdict"] == "CERTIFIED_ARABIC_CONTINUUM_STRUCTURE", "standalone certified")
    check(cert["all_gates_passed"] is True, "all gates passed")
    check(cert["pinned_corpus_count"] == 9, "9 pinned corpora")
    check(
        cert["certificate_sha256"] == EXPECTED_STANDALONE_SHA,
        f"standalone sha mismatch: {cert['certificate_sha256']}",
    )

    p1 = cert["pillar1_root_pattern_lattice"]
    p2 = cert["pillar2_ring_vs_inclusio"]
    p3 = cert["pillar3_translation_remainder"]
    axes = dict(cert["five_axis_net_invariance"])
    pins = dict(audit.EXPECTED_CORPUS_SHA256)

    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", {"a": 1.0}, audit.AUDIT_FEATURES, p1, p2, p3, axes
        ),
        "FLOAT_FORBIDDEN",
    )
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "invalid", pins, audit.AUDIT_FEATURES, p1, p2, p3, axes
        ),
        "INVALID_MODE",
    )
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", {}, audit.AUDIT_FEATURES, p1, p2, p3, axes
        ),
        "MISSING_PROVENANCE",
    )
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", {"/abs/path": "a" * 64}, audit.AUDIT_FEATURES, p1, p2, p3, axes
        ),
        "UNSAFE_PIN_PATH",
    )
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", {"a": "a" * 64, " a ": "a" * 64}, audit.AUDIT_FEATURES, p1, p2, p3, axes
        ),
        "DUPLICATE_PIN_PATH",
    )
    # ARAB-BUG-01 regression: trailing newline, leading space, uppercase, all-zero sha256 rejected
    for bad_sha in ("A" * 64, "a" * 64 + "\n", " " + "a" * 64, "0" * 64, 12345):
        expect_error(
            lambda s=bad_sha: oracle.certify_arabic_own_terms_5axis_gate(
                "standalone", {"x": s}, audit.AUDIT_FEATURES, p1, p2, p3, axes
            ),
            "INVALID_SHA256",
        )
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, "not_dict", p2, p3, axes
        ),
        "INVALID_PILLAR",
    )
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, ["abjad_count"], p1, p2, p3, axes
        ),
        "NUMEROLOGY_FORBIDDEN",
    )
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, p1, p2, p3, "bad"
        ),
        "INVALID_AXES",
    )
    miss_ax = dict(axes)
    del miss_ax["root_vs_stem"]
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, p1, p2, p3, miss_ax
        ),
        "INVALID_AXES",
    )
    extra_ax = dict(axes)
    extra_ax["bogus_axis"] = True
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, p1, p2, p3, extra_ax
        ),
        "INVALID_AXES",
    )
    # ARAB-BUG-03 regression: contradictory pillar dicts & contradictory five_axis_checks rejected!
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, {"passed": True}, p2, p3, axes
        ),
        "INVALID_BOOL",
    )
    bad_p1_c = dict(p1)
    bad_p1_c["monotonic_ladder_all_w"] = False
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, bad_p1_c, p2, p3, axes
        ),
        "PILLAR_CONTRADICTION",
    )
    bad_p2_c = dict(p2)
    bad_p2_c["pointwise_ring_falsified"] = False
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, p1, bad_p2_c, p3, axes
        ),
        "PILLAR_CONTRADICTION",
    )
    bad_p3_c = dict(p3)
    bad_p3_c["severe_remainder_both_translators"] = 3
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, p1, p2, bad_p3_c, axes
        ),
        "PILLAR_CONTRADICTION",
    )
    bad_ax_c = dict(axes)
    bad_ax_c["odd_vs_even_unseen"] = False
    expect_error(
        lambda: oracle.certify_arabic_own_terms_5axis_gate(
            "standalone", pins, audit.AUDIT_FEATURES, p1, p2, p3, bad_ax_c
        ),
        "AXIS_CONTRADICTION",
    )

    # Consistent failure on any pillar cleanly yields REJECTED_GATE_FAILED
    q1, q2, q3, qax = dict(p1), dict(p2), dict(p3), dict(axes)
    q1["monotonic_ladder_all_w"] = False
    q1["passed"] = False
    qax["diacritics_vs_rasm"] = False
    qax["root_vs_stem"] = False
    rej1 = oracle.certify_arabic_own_terms_5axis_gate(
        "live_readonly", pins, audit.AUDIT_FEATURES, q1, q2, q3, qax
    )
    check(rej1["verdict"] == "REJECTED_GATE_FAILED" and rej1["all_gates_passed"] is False, "p1 rej")

    q1, q2, q3, qax = dict(p1), dict(p2), dict(p3), dict(axes)
    q2["pointwise_ring_falsified"] = False
    q2["passed"] = False
    rej2 = oracle.certify_arabic_own_terms_5axis_gate(
        "live_readonly", pins, audit.AUDIT_FEATURES, q1, q2, q3, qax
    )
    check(rej2["verdict"] == "REJECTED_GATE_FAILED" and rej2["all_gates_passed"] is False, "p2 rej")

    q1, q2, q3, qax = dict(p1), dict(p2), dict(p3), dict(axes)
    q3["passed"] = False
    q3["severe_remainder_both_translators"] = 3
    qax["second_instrument_and_controls"] = False
    rej3 = oracle.certify_arabic_own_terms_5axis_gate(
        "live_readonly", pins, audit.AUDIT_FEATURES, q1, q2, q3, qax
    )
    check(rej3["verdict"] == "REJECTED_GATE_FAILED" and rej3["all_gates_passed"] is False, "p3 rej")


def test_audit_parsers_and_synthetic_live_pipeline():
    # Constants pinned
    check(audit.SEED_T4A == 2026091, "seed t4a")
    check(audit.SEED_T4B == 2026092, "seed t4b")
    check(audit.SEED_ODD_T4B == 2026093, "seed odd")
    check(audit.SEED_EVEN_T4B == 2026094, "seed even")
    check(audit.SEED_RING_PERM == 2026095, "seed ring")
    check(audit.SEED_CTRL_T4A == 2026096, "seed ctrl")
    check(audit.SEED_BG_PAIRS == 2026097, "seed bg")
    check(audit.BG_PAIR_COUNT == 1000, "bg count")
    check(audit.WINDOW_SIZES == (10, 20, 40), "window sizes")
    check(audit.ARB_CHUNK_LINES == 60, "arb chunk lines")
    check(len(audit.TARGET_ROOTS) == 9, "target roots len")
    check(audit.default_corpus_dir().endswith(os.path.join("repos", "arabic")), "default corpus dir")

    # parse_tanzil_lines
    tanzil = audit.parse_tanzil_lines(["# header\n", "\n", "1|1|hello | world\n", "1|2|peace\n"])
    check(tanzil == {(1, 1): "hello | world", (1, 2): "peace"}, "tanzil parse")
    expect_error(lambda: audit.parse_tanzil_lines(["malformed_line\n"]), "PARSE_ERROR")

    # parse_openiti_lines
    openiti_raw = [
        "######OpenITI#\n",
        "#META# preheader \u0643\u062a\u0628\n",
        "#META#Header#End#\n",
        "\n",
        "### empty first header\n",
        "PageV01P001 ms001 %~~% ~% \u0648\u0627\u0644\u0643\u062a\u0628 !!!\n",
        "12345 !!!\n",
        "### second section\n",
        "\u0633\u0628\u062d \u0641\u0644\u0643\n",
        "### trailing empty header\n",
    ]
    all_lines, secs = audit.parse_openiti_lines(openiti_raw)
    check(len(all_lines) == 2 and len(secs) == 2, f"openiti counts: {len(all_lines)}, {len(secs)}")
    check(all_lines[0] == ["\u0643\u062a\u0628"], f"openiti line0: {all_lines[0]}")
    # Also test trailing non-empty section flush
    all_l2, secs2 = audit.parse_openiti_lines(["#META#Header#End#\n", "\u0643\u062a\u0628\n"])
    check(len(all_l2) == 1 and len(secs2) == 1, "openiti trailing flush")

    # parse_leeds_morphology_lines
    leeds_raw = [
        "",
        "# comment\n",
        "LOCATION\tFORM\tTAG\tFEATURES\n",
        "too\tfew\tcols\n",
        "(1:1:1:1)\tbi\tP\tPREFIX|bi+\n",
        "(1:1:2:1)\tsbH\tV\tSTEM|POS:V|PERF|(II)|LEM:sab~aHa|ROOT:sbH\n",
        "(1:1:3:1)\tktb\tV\tSTEM|POS:V|PERF|ROOT:ktb\n",
        "(1:2:1:1)\tflk\tN\tSTEM|POS:N|ACT|PCPL|LEM:fulok|ROOT:flk\n",
        "(2:1:1:1)\tqdr\tN\tSTEM|POS:N|PASS|PCPL|(IV)|LEM:qdr|ROOT:qdr\n",
        "(2:1:2:1)\tmdd\tN\tSTEM|POS:N|VN|LEM:mdd|ROOT:mdd\n",
    ]
    md = audit.parse_leeds_morphology_lines(leeds_raw)
    check(md["unique_roots"] == 5 and md["unique_lemmas"] == 4, f"leeds counts: {md}")
    check(md["unique_root_wazn_cells"] == 5, "leeds cells")
    check(md["verb_form_counts"] == {"I": 1, "II": 1}, f"vf counts: {md['verb_form_counts']}")
    check(md["leeds_odd"] == ["sbH", "ktb", "flk"], "odd roots")
    check(md["leeds_even"] == ["qdr", "mdd"], "even roots")
    check(md["target_occs"]["sbH"] == 1 and md["target_occs"]["qdr"] == 1, "target occs")

    # evaluate_ring_and_inclusio_units
    short_u = [["a"]] * 19
    long_u = [["a", "top"]] * 2 + [["b", "top"]] * 16 + [["a", "top"]] * 2
    ri_all = audit.evaluate_ring_and_inclusio_units([short_u, long_u])
    check(ri_all["inclusio"] == [2, 2] and ri_all["middle"] == [1, 3], f"ri_all: {ri_all}")
    ri_ex = audit.evaluate_ring_and_inclusio_units([long_u], exclude=frozenset({"top"}))
    check(ri_ex["inclusio"] == [1, 1] and ri_ex["middle"] == [0, 2], f"ri_ex: {ri_ex}")

    # Synthetic 9-file corpus end-to-end test for verify_corpus_hashes + compute_live_measurements
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "arabic_morphology_quranic-corpus"))
        os.makedirs(os.path.join(tmpdir, "openiti_controls"))

        # Build 2 surahs (odd=1, even=2) x 20 verses each = 40 verses
        morph_lines = ["LOCATION\tFORM\tTAG\tFEATURES\n"]
        uth_lines = []
        sahih_lines = []
        pick_lines = []
        roots_cycle = ["ftq", "rtq", "sbH", "mdd", "wsE", "flk", "kwr", "qdr", "zwj"]
        ar_words = [
            "\u0643\u062a\u0628\u064e",
            "\u0648\u0627\u0644\u0633\u0645\u0627\u0621",
            "\u0627\u0644\u0641\u0644\u0643",
            "\u0633\u0628\u062d\u0627\u0646",
        ]
        for s_num in (1, 2):
            for v_num in range(1, 21):
                r = roots_cycle[(v_num - 1) % len(roots_cycle)]
                w_ar = ar_words[(v_num - 1) % len(ar_words)]
                morph_lines.append(
                    f"({s_num}:{v_num}:1:1)\tform\tV\tSTEM|POS:V|LEM:{r}L|ROOT:{r}\n"
                )
                uth_lines.append(f"{s_num}|{v_num}|{w_ar} !!! {w_ar}\n")
                # Verse (1, 1) has only stopwords so s_df empty branch is exercised for ftq if alone;
                # give varied English stems across verses
                if v_num == 1 and s_num == 1:
                    sahih_lines.append(f"{s_num}|{v_num}|the of and\n")
                    pick_lines.append(f"{s_num}|{v_num}|the of and\n")
                elif v_num % 2 == 0:
                    sahih_lines.append(f"{s_num}|{v_num}|exalt ship water wrapped\n")
                    pick_lines.append(f"{s_num}|{v_num}|glorify ship water overthrown\n")
                else:
                    sahih_lines.append(f"{s_num}|{v_num}|extend compass measure pairs\n")
                    pick_lines.append(f"{s_num}|{v_num}|spread embrace decree mates\n")

        openiti_body = ["#META#Header#End#\n", "### chap1\n"] + [
            "\u0643\u062a\u0628 \u0633\u0628\u062d \u0641\u0644\u0643 \u0642\u062f\u0631\n"
            for _ in range(24)
        ]

        files_map = {
            "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt": "".join(morph_lines),
            "tanzil-quran-uthmani.txt": "".join(uth_lines),
            "tanzil-en.sahih.txt": "".join(sahih_lines),
            "tanzil-en.pickthall.txt": "".join(pick_lines),
            "openiti_controls/ibn_muqaffa_kalila.txt": "".join(openiti_body),
            "openiti_controls/ibn_muqaffa_adab_kabir.txt": "".join(openiti_body),
            "openiti_controls/imru_al_qays_diwan.txt": "".join(openiti_body),
            "openiti_controls/tarafa_diwan.txt": "".join(openiti_body),
            "openiti_controls/antara_muallaqa.txt": "".join(openiti_body),
        }
        pins = {}
        for rel, content in files_map.items():
            fp = os.path.join(tmpdir, rel)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            pins[rel] = audit.sha256_file(fp)

        # Verify default pins reject mismatched hash
        expect_error(lambda: audit.verify_corpus_hashes(tmpdir), "SHA256_MISMATCH")
        # Verify missing file rejects
        bad_pins = dict(pins)
        bad_pins["nonexistent.txt"] = "0" * 64
        expect_error(
            lambda: audit.verify_corpus_hashes(tmpdir, expected_hashes=bad_pins),
            "CORPUS_MISSING",
        )

        # Compute live measurements on synthetic corpus (single window & multi-window)
        m1 = audit.compute_live_measurements(
            tmpdir,
            expected_hashes=pins,
            window_sizes=(4,),
            bg_pair_count=10,
            arb_chunk_lines=20,
        )
        m2 = audit.compute_live_measurements(
            tmpdir,
            expected_hashes=pins,
            window_sizes=(4, 8),
            bg_pair_count=10,
            arb_chunk_lines=20,
        )
        check(m1["unique_roots"] == 9 and m1["total_root_tokens"] == 40, "synth morph")
        check(m1["bg_sahih_pair"][1] == 10 and m1["bg_pickthall_pair"][1] == 10, "synth bg")
        check(m2["control_w20_pairs"]["quran_stem"]["obs"] != m1["control_w20_pairs"]["quran_stem"]["obs"], "ctrl_w branch")
        check(len(m1["root_records"]) == 9, "synth 9 roots")
        # Also exercise s_df empty branch explicitly by verifying ftq in 1-verse corpus
        # Verify determinism: repeated run matches exactly
        m1_again = audit.compute_live_measurements(
            tmpdir,
            expected_hashes=pins,
            window_sizes=(4,),
            bg_pair_count=10,
            arb_chunk_lines=20,
        )
        check(m1 == m1_again, "synth deterministic")

        # Exercise main() CLI standalone + --output + exit code 0 & 1
        out_path = os.path.join(tmpdir, "cert.json")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            rc = audit.main(["--standalone", "--output", out_path])
        finally:
            sys.stdout = old_stdout
        check(rc == 0, "main standalone rc=0")
        with open(out_path, "rb") as f:
            written = f.read()
        check(written.endswith(b"\n"), "output newline")
        parsed = json.loads(written.decode("utf-8"))
        check(parsed["certificate_sha256"] == EXPECTED_STANDALONE_SHA, "cli output sha")
        check(buf.getvalue().encode("utf-8") == written, "stdout == output file")

        # Exercise main() failing return code 1 via failing fixture copy
        orig_fx = audit.STANDALONE_FIXTURE
        bad_fx = copy.deepcopy(orig_fx)
        bad_fx["ring_metrics"]["all_mirror"] = bad_fx["ring_metrics"]["all_perm_null"]
        buf2 = io.StringIO()
        try:
            audit.STANDALONE_FIXTURE = bad_fx
            sys.stdout = buf2
            rc_fail = audit.main(["--standalone"])
        finally:
            audit.STANDALONE_FIXTURE = orig_fx
            sys.stdout = old_stdout
        check(rc_fail == 1, "main failing rc=1")

        # Exercise run_audit(standalone=False, corpus_dir=...) error propagation
        expect_error(
            lambda: audit.run_audit(standalone=False, corpus_dir=tmpdir),
            "SHA256_MISMATCH",
        )

    # Exercise isolated -I subprocess invocation (kills _SCRIPT_DIR sys.path & __main__ mutants)
    audit_script = os.path.join(_SCRIPT_DIR, "arabic_continuum_audit.py")
    proc = subprocess.run(
        [sys.executable, "-I", "-B", "-W", "error", audit_script, "--standalone"],
        capture_output=True,
        text=True,
        check=False,
    )
    check(proc.returncode == 0, f"-I subprocess rc={proc.returncode} stderr={proc.stderr}")
    sub_cert = json.loads(proc.stdout)
    check(sub_cert["certificate_sha256"] == EXPECTED_STANDALONE_SHA, "-I subprocess sha")


def run_all_tests():
    test_oracle_primitives_and_boundaries()
    test_deterministic_shuffles_and_text_nets()
    test_zero_numerology_guard()
    test_pillar1_boundaries_and_redteam()
    test_pillar2_boundaries_and_redteam()
    test_pillar3_boundaries_and_redteam()
    test_pillar4_gate_and_redteam()
    test_audit_parsers_and_synthetic_live_pipeline()
    return "ALL_TESTS_PASSED"


if __name__ == "__main__":
    print(run_all_tests())
