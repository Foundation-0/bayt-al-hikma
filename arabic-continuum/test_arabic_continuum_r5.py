"""Assertion-free, -O-safe R5 verification suite for arabic-continuum (v2)
and ../fetch_corpora.py.

Pins every oracle primitive, statistical threshold, conjunct, Holm-Bonferroni
step-down rule, Pillar 4 full re-derivation, hand-computed known-answer
mini-corpus live path, and fail-closed corpus fetcher behavior.
"""

from contextlib import contextmanager
from fractions import Fraction
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, ".."))
for _p in (_HERE, _REPO_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arabic_continuum_oracle as o
import arabic_continuum_audit as a
import fetch_corpora as fc


def _cell(oi, ou, ni, nu, ge=0):
    return {"obs": [oi, ou], "null_pooled": [ni, nu], "ge_count": ge}


def _valid_p1_inputs():
    vf = {f"F{i}": 10 for i in range(1, 9)}
    # Raw lift > root lift at every W, W20 stem lift > root lift; all 12 cells ge=0
    wm = {
        10: {
            "raw": _cell(30, 100, 10, 100, 0),    # lift 3.0
            "rasm": _cell(25, 100, 12, 100, 0),   # lift 2.08
            "stem": _cell(26, 100, 13, 100, 0),   # lift 2.0
            "root": _cell(24, 100, 15, 100, 0),   # lift 1.6
            "root_t4b": _cell(24, 100, 16, 100, 0),
            "odd_split_root_t4b": _cell(23, 100, 16, 100, 0),
            "even_split_root_t4b": _cell(25, 100, 16, 100, 0),
        },
        20: {
            "raw": _cell(25, 100, 10, 100, 0),    # lift 2.5
            "rasm": _cell(22, 100, 12, 100, 0),   # lift 1.83
            "stem": _cell(20, 100, 12, 100, 0),   # lift 1.67
            "root": _cell(22, 100, 15, 100, 0),   # lift 1.47
            "root_t4b": _cell(22, 100, 16, 100, 0),
            "odd_split_root_t4b": _cell(21, 100, 16, 100, 0),
            "even_split_root_t4b": _cell(23, 100, 16, 100, 0),
        },
        40: {
            "raw": _cell(20, 100, 10, 100, 0),    # lift 2.0
            "rasm": _cell(19, 100, 12, 100, 0),   # lift 1.58
            "stem": _cell(18, 100, 12, 100, 0),   # lift 1.50
            "root": _cell(20, 100, 16, 100, 0),   # lift 1.25
            "root_t4b": _cell(20, 100, 17, 100, 0),
            "odd_split_root_t4b": _cell(19, 100, 17, 100, 0),
            "even_split_root_t4b": _cell(21, 100, 17, 100, 0),
        },
    }
    ctrl = {
        "quran_stem": _cell(20, 100, 12, 100, 0),    # lift 1.6667, obs 0.20
        "kalila_prose": _cell(22, 100, 11, 100, 0),  # lift 2.0000 > quran, obs 0.22
        "adab_prose": _cell(19, 100, 12, 100, 0),    # lift 1.5833, obs 0.19
        "poetry_pooled": _cell(10, 100, 6, 100, 0),  # obs 0.10 < all prose
    }
    return {
        "unique_roots": 100,
        "unique_lemmas": 201,
        "unique_root_wazn_cells": 201,
        "total_root_tokens": 500,
        "verb_form_counts": vf,
        "window_metrics": wm,
        "control_w20_metrics": ctrl,
        "n_shuffles": 250,
    }


def _valid_p2_metrics():
    def dn(ge, q025=(-1, 20), q975=(1, 20)):
        return {"ge_count": ge, "q025": list(q025), "q975": list(q975)}

    return {
        "all_mirror": [10, 100],
        "all_shift": [15, 100],
        "mirror_null_pooled": [14, 100],
        "mirror_ge_count": 248,
        "mirror_le_count": 2,
        "all_inclusio": [22, 100],
        "all_middle": [20, 100],
        "odd_inclusio": [11, 50],
        "odd_middle": [10, 50],
        "even_inclusio": [11, 50],
        "even_middle": [10, 50],
        "all_strip10_inclusio": [16, 100],
        "all_strip10_middle": [14, 100],
        "odd_strip10_inclusio": [8, 50],
        "odd_strip10_middle": [7, 50],
        "even_strip10_inclusio": [8, 50],
        "even_strip10_middle": [7, 50],
        "kalila_arb_inclusio": [10, 100],
        "kalila_arb_middle": [15, 100],
        "kalila_nat_inclusio": [25, 100],
        "kalila_nat_middle": [20, 100],
        "delta_nulls": {
            "all": dn(60),
            "odd": dn(70),
            "even": dn(80),
            "all_strip10": dn(40),
            "odd_strip10": dn(30),
            "even_strip10": dn(50),
            "kalila_arb": dn(240),
            "kalila_nat": dn(5),
        },
    }


def _valid_p3_records():
    # 4 multi-verse roots each with vcnt=5 (10 pairs), 6 lost (>= 0.6 > 0.5 and >= 0.4) + 1 single-verse root
    recs = []
    for name in ("r1", "r2", "r3", "r4"):
        recs.append({
            "root": name,
            "occurrences": 6,
            "verse_count": 5,
            "unique_lemmas": 2,
            "sahih_top_count": 2,
            "pickthall_top_count": 2,
            "sahih_lost_pairs": 6,
            "pickthall_lost_pairs": 7,
            "sahih_total_pairs": 10,
            "pickthall_total_pairs": 10,
        })
    recs.append({
        "root": "r_single",
        "occurrences": 2,
        "verse_count": 1,
        "unique_lemmas": 1,
        "sahih_top_count": 1,
        "pickthall_top_count": 1,
        "sahih_lost_pairs": 0,
        "pickthall_lost_pairs": 0,
        "sahih_total_pairs": 0,
        "pickthall_total_pairs": 0,
    })
    return recs


class TestOraclePrimitives(unittest.TestCase):
    def _assert_oracle_error(self, code, fn, *args, **kwargs):
        with self.assertRaises(o.ArabicOracleError) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_verify_no_floats(self):
        o.verify_no_floats({"a": [1, Fraction(1, 2), ("x", True, None)], "s": {1, 2}, "fs": frozenset([3])})
        self._assert_oracle_error("FLOAT_FORBIDDEN", o.verify_no_floats, 1.5)
        self._assert_oracle_error("FLOAT_FORBIDDEN", o.verify_no_floats, 1 + 2j)
        self._assert_oracle_error("FLOAT_FORBIDDEN", o.verify_no_floats, {1.0: "a"})
        self._assert_oracle_error("FLOAT_FORBIDDEN", o.verify_no_floats, {"k": [1, (2, 3.0)]})
        self._assert_oracle_error("FLOAT_FORBIDDEN", o.verify_no_floats, {1.5})

    def test_require_validators(self):
        self.assertEqual(o.require_non_empty_str(" ~a\u0080 ", "f"), "~a\u0080")
        self._assert_oracle_error("INVALID_TYPE", o.require_non_empty_str, 123, "f")
        self._assert_oracle_error("CONTROL_CHAR", o.require_non_empty_str, "a\x1fb", "f")
        self._assert_oracle_error("CONTROL_CHAR", o.require_non_empty_str, "a\nb", "f")
        self._assert_oracle_error("CONTROL_CHAR", o.require_non_empty_str, "a\x7fb", "f")
        self._assert_oracle_error("CONTROL_CHAR", o.require_non_empty_str, "a\u200bb", "f")
        self._assert_oracle_error("EMPTY_STRING", o.require_non_empty_str, "   ", "f")

        self.assertIs(o.require_exact_bool(True, "b"), True)
        self.assertIs(o.require_exact_bool(False, "b"), False)
        self._assert_oracle_error("INVALID_BOOL", o.require_exact_bool, 1, "b")
        self._assert_oracle_error("INVALID_BOOL", o.require_exact_bool, "true", "b")

        self.assertEqual(o.require_exact_int(5, "x", 5, 5), 5)
        self._assert_oracle_error("INVALID_INT", o.require_exact_int, True, "x")
        self._assert_oracle_error("INVALID_INT", o.require_exact_int, 1.0, "x")
        self._assert_oracle_error("RANGE_ERROR", o.require_exact_int, 4, "x", min_value=5)
        self._assert_oracle_error("RANGE_ERROR", o.require_exact_int, 6, "x", max_value=5)

        self.assertEqual(o.require_exact_fraction(3, "q", Fraction(3, 1), Fraction(3, 1)), Fraction(3, 1))
        self.assertEqual(o.require_exact_fraction(Fraction(1, 2), "q", Fraction(1, 2), Fraction(1, 2)), Fraction(1, 2))
        self._assert_oracle_error("INVALID_FRACTION", o.require_exact_fraction, False, "q")
        self._assert_oracle_error("INVALID_FRACTION", o.require_exact_fraction, "1/2", "q")
        self._assert_oracle_error("RANGE_ERROR", o.require_exact_fraction, Fraction(1, 3), "q", min_value=Fraction(1, 2))
        self._assert_oracle_error("RANGE_ERROR", o.require_exact_fraction, Fraction(2, 3), "q", max_value=Fraction(1, 2))

    def test_pair_ratios(self):
        self.assertEqual(o.require_pair_ratio((0, 1), "p"), (0, 1, Fraction(0, 1)))
        self.assertEqual(o.require_pair_ratio([3, 3], "p"), (3, 3, Fraction(1, 1)))
        self._assert_oracle_error("INVALID_PAIR", o.require_pair_ratio, "12", "p")
        self._assert_oracle_error("INVALID_PAIR", o.require_pair_ratio, [1], "p")
        self._assert_oracle_error("RANGE_ERROR", o.require_pair_ratio, [-1, 2], "p")
        self._assert_oracle_error("RANGE_ERROR", o.require_pair_ratio, [0, 0], "p")
        self._assert_oracle_error("INVALID_PAIR", o.require_pair_ratio, [4, 3], "p")

        self.assertEqual(o.require_signed_ratio_pair((-5, 5), "s"), (-5, 5, Fraction(-1, 1)))
        self.assertEqual(o.require_signed_ratio_pair([5, 5], "s"), (5, 5, Fraction(1, 1)))
        self.assertEqual(o.require_signed_ratio_pair([0, 1], "s"), (0, 1, Fraction(0, 1)))
        self._assert_oracle_error("INVALID_PAIR", o.require_signed_ratio_pair, (1,), "s")
        self._assert_oracle_error("INVALID_PAIR", o.require_signed_ratio_pair, "12", "s")
        self._assert_oracle_error("RANGE_ERROR", o.require_signed_ratio_pair, (0, 0), "s")
        self._assert_oracle_error("INVALID_PAIR", o.require_signed_ratio_pair, (6, 5), "s")
        self._assert_oracle_error("INVALID_PAIR", o.require_signed_ratio_pair, (-6, 5), "s")

    def test_formatting_and_empirical_p(self):
        self.assertEqual(o.frac_str(Fraction(4, 6)), "2/3")
        self.assertEqual(o.frac_str(5), "5/1")
        self.assertEqual(o.format_exact_decimal(Fraction(3, 2), 0), "2")
        self.assertEqual(o.format_exact_decimal(Fraction(-3, 2), 0), "-2")
        self.assertEqual(o.format_exact_decimal(Fraction(-1, 3), 0), "0")
        self.assertEqual(o.format_exact_decimal(Fraction(1, 20), 1), "0.1")
        self.assertEqual(o.format_exact_decimal(Fraction(49, 1000), 1), "0.0")
        self.assertEqual(o.format_exact_decimal(Fraction(-1, 200), 2), "-0.01")
        self.assertEqual(o.format_exact_decimal(Fraction(-1, 10000), 2), "0.00")
        self.assertEqual(o.format_exact_decimal(Fraction(1, 4), 12), "0.250000000000")
        self._assert_oracle_error("RANGE_ERROR", o.format_exact_decimal, Fraction(1, 2), -1)
        self._assert_oracle_error("RANGE_ERROR", o.format_exact_decimal, Fraction(1, 2), 13)

        self.assertEqual(o.empirical_rank_p_exact(0, 250), Fraction(1, 251))
        self.assertEqual(o.empirical_rank_p_exact(250, 250), Fraction(1, 1))
        self.assertEqual(o.empirical_rank_p_exact(5, 10), Fraction(6, 11))
        self._assert_oracle_error("RANGE_ERROR", o.empirical_rank_p_exact, 0, 0)
        self._assert_oracle_error("RANGE_ERROR", o.empirical_rank_p_exact, -1, 10)
        self._assert_oracle_error("RANGE_ERROR", o.empirical_rank_p_exact, 11, 10)

    def test_holm_bonferroni_exact(self):
        self._assert_oracle_error("FLOAT_FORBIDDEN", o.holm_bonferroni_exact, {"a": 0.01})
        self._assert_oracle_error("INVALID_PMAP", o.holm_bonferroni_exact, {})
        self._assert_oracle_error("INVALID_PMAP", o.holm_bonferroni_exact, [])
        self._assert_oracle_error("RANGE_ERROR", o.holm_bonferroni_exact, {"a": Fraction(1, 10)}, alpha=Fraction(1, 1001))
        self._assert_oracle_error("RANGE_ERROR", o.holm_bonferroni_exact, {"a": Fraction(1, 10)}, alpha=Fraction(51, 100))
        self._assert_oracle_error("RANGE_ERROR", o.holm_bonferroni_exact, {"a": Fraction(0, 1)})
        self._assert_oracle_error("RANGE_ERROR", o.holm_bonferroni_exact, {"a": Fraction(2, 1)})

        # Step-down running_max + exact alpha equality boundary + cap at 1/1
        res = o.holm_bonferroni_exact(
            {
                "t1": Fraction(1, 80),   # *4 = 1/20 == alpha -> True
                "t2": Fraction(1, 60),   # *3 = 1/20 == alpha -> True (running_max stays 1/20)
                "t3": Fraction(1, 50),   # *2 = 1/25 < running_max(1/20) -> clamped up to 1/20 -> True!
                "t4": Fraction(3, 5),    # *1 = 3/5 > alpha -> False
            },
            alpha=Fraction(1, 20),
        )
        self.assertEqual(res["test_count"], 4)
        self.assertEqual(res["alpha_exact"], "1/20")
        self.assertEqual(res["adjusted_p_exact"]["t1"], "1/20")
        self.assertEqual(res["adjusted_p_exact"]["t3"], "1/20")
        self.assertEqual(res["adjusted_p_dec6"]["t3"], "0.050000")
        self.assertTrue(res["rejected_at_alpha"]["t1"])
        self.assertTrue(res["rejected_at_alpha"]["t3"])
        self.assertFalse(res["rejected_at_alpha"]["t4"])

        # Cap at 1/1 when scaled > 1
        res_cap = o.holm_bonferroni_exact({"a": Fraction(3, 4), "b": Fraction(4, 5)}, alpha=Fraction(1, 2))
        self.assertEqual(res_cap["adjusted_p_exact"]["a"], "1/1")
        self.assertEqual(res_cap["adjusted_p_exact"]["b"], "1/1")
        self.assertFalse(res_cap["rejected_at_alpha"]["a"])

        # Alpha boundary exact (1/1000 and 1/2 accepted)
        r_lo = o.holm_bonferroni_exact({"a": Fraction(1, 1000000)}, alpha=Fraction(1, 1000))
        self.assertTrue(r_lo["rejected_at_alpha"]["a"])
        r_hi = o.holm_bonferroni_exact({"a": Fraction(1, 2)}, alpha=Fraction(1, 2))
        self.assertTrue(r_hi["rejected_at_alpha"]["a"])

    def test_hash_shuffles_and_text_layers(self):
        self.assertEqual(o.canonical_json_bytes({"b": 1, "a": "\u0627"}), b'{"a":"\\u0627","b":1}')
        self.assertEqual(o.canonical_sha256({"x": 1}), hashlib.sha256(b'{"x":1}').hexdigest())
        self.assertEqual(o.fnv1a_32("abc"), 0x1A47E90B)
        self.assertNotEqual(o.fnv1a_32("\u0643\u062a\u0628"), o.fnv1a_32("abc"))

        self.assertEqual(o.det_shuffle_exact([], 0), [])
        self.assertEqual(o.det_shuffle_exact([7], 0), [7])
        seq = list(range(12))
        s1 = o.det_shuffle_exact(seq, 42)
        s2 = o.det_shuffle_exact(seq, 42)
        s3 = o.det_shuffle_exact(seq, 43)
        self.assertEqual(s1, s2)
        self.assertEqual(sorted(s1), seq)
        self.assertNotEqual(s1, seq)
        self.assertNotEqual(s1, s3)
        self._assert_oracle_error("INVALID_SEQ", o.det_shuffle_exact, "abc", 1)
        self._assert_oracle_error("RANGE_ERROR", o.det_shuffle_exact, [1, 2], -1)

        items = ["n0", "v0", "n1", "v1", "n2", "v2", "n3", "v3"]
        classes = ["N", "V", "N", "V", "N", "V", "N", "V"]
        st = o.stratified_shuffle_exact(items, classes, 12345)
        self.assertEqual(sorted(st[0::2]), ["n0", "n1", "n2", "n3"])
        self.assertEqual(sorted(st[1::2]), ["v0", "v1", "v2", "v3"])
        self.assertEqual(st, o.stratified_shuffle_exact(items, classes, 12345))
        self.assertNotEqual(st, o.stratified_shuffle_exact(items, classes, 99999))
        self._assert_oracle_error("INVALID_SEQ", o.stratified_shuffle_exact, "ab", ["N", "V"], 1)
        self._assert_oracle_error("INVALID_SEQ", o.stratified_shuffle_exact, [1, 2], "NV", 1)
        self._assert_oracle_error("LENGTH_MISMATCH", o.stratified_shuffle_exact, [1, 2], ["N"], 1)

        # Arabic rasm & light stem
        self._assert_oracle_error("INVALID_TYPE", o.to_rasm, 123)
        self.assertEqual(o.to_rasm("\u0671\u0623\u0625\u0622\u0649\u0629\u064e\u0651\u0670\u0640!"), "\u0627\u0627\u0627\u0627\u064a\u0647")
        self.assertEqual(o.light_stem_ar("\u0643\u062a\u0628"), "\u0643\u062a\u0628")
        self.assertEqual(o.light_stem_ar("\u0648\u0627\u0644\u0643\u062a\u0627\u0628"), "\u0643\u062a\u0627\u0628")
        self.assertEqual(o.light_stem_ar("\u0627\u0644\u0645\u0633\u0644\u0645\u0648\u0646"), "\u0645\u0633\u0644\u0645")
        # Short word with prefix-like char must keep len >= 3
        self.assertEqual(o.light_stem_ar("\u0627\u0644\u0644\u0647"), "\u0627\u0644\u0644")

        # English content stems
        self._assert_oracle_error("INVALID_TYPE", o.en_content_stems, 5)
        stems = o.en_content_stems(
            "the cat planning creating seeing stopped walked loved fishes trees books gods theirs Allah"
        )
        self.assertEqual(
            stems,
            {"plan", "creat", "seeing", "stop", "walk", "loved", "fish", "tree", "book", "gods"},
        )
        # Verify post-strip <4 filtered out ("running" -> "run" len 3, "mapped" -> "map" len 3)
        self.assertEqual(o.en_content_stems("running mapped"), set())

    def test_block_jaccard_and_naming_guard(self):
        self.assertEqual(o.block_jaccard_cohesion_exact(["a", "b", "b", "c"], 2), (1, 3, Fraction(1, 3)))
        self.assertEqual(o.block_jaccard_cohesion_exact(["a", "b", "b", "c", "c", "d", "z"], 2), (2, 6, Fraction(1, 3)))
        self._assert_oracle_error("INVALID_SEQ", o.block_jaccard_cohesion_exact, "abcd", 2)
        self._assert_oracle_error("RANGE_ERROR", o.block_jaccard_cohesion_exact, ["a", "b", "c", "d"], 1)
        self._assert_oracle_error("INSUFFICIENT_BLOCKS", o.block_jaccard_cohesion_exact, ["a", "b", "c"], 2)

        ok = o.enforce_zero_numerology_policy(["Root_Wazn", "Context-Topology"])
        self.assertTrue(ok["naming_filter_ok"])
        self.assertEqual(ok["guard_scope"], "feature_label_filter_only_not_statistical_proof")
        self.assertEqual(ok["feature_count"], 2)
        self.assertEqual(ok["features"], ["root_wazn", "context-topology"])
        self._assert_oracle_error("INVALID_FEATURES", o.enforce_zero_numerology_policy, [])
        self._assert_oracle_error("INVALID_FEATURES", o.enforce_zero_numerology_policy, "abc")
        self._assert_oracle_error("EMPTY_STRING", o.enforce_zero_numerology_policy, ["---"])
        self._assert_oracle_error("DUPLICATE_FEATURE", o.enforce_zero_numerology_policy, ["a-b", "A_B"])
        for bad in ("\uff41\uff42\uff4a\uff41\uff44", "g_e_m_a_t_r_i_a", "digit-sum", "base-10", "miracle", "code_19", "numerology"):
            self._assert_oracle_error("NUMEROLOGY_FORBIDDEN", o.enforce_zero_numerology_policy, [bad])


class TestPillars1To4ThresholdsAndConjuncts(unittest.TestCase):
    def _assert_err(self, code, fn, *args, **kwargs):
        with self.assertRaises(o.ArabicOracleError) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_pillar1_happy_errors_and_every_conjunct(self):
        base = _valid_p1_inputs()
        res = o.audit_root_pattern_lattice_and_cohesion_exact(**base)
        self.assertTrue(res["passed"])
        self.assertEqual(res["n_shuffles"], 250)
        self.assertEqual(res["alpha_exact"], "1/20")
        self.assertEqual(res["verb_form_total"], 80)

        # Non-W20 custom windows cover `20 not in lifts_by_w` and string keys
        alt = _valid_p1_inputs()
        alt["window_metrics"] = {
            "8": alt["window_metrics"][10],
            "16": alt["window_metrics"][20],
            "32": alt["window_metrics"][40],
        }
        self.assertTrue(o.audit_root_pattern_lattice_and_cohesion_exact(**alt)["passed"])

        # Validation errors
        bad = _valid_p1_inputs(); bad["n_shuffles"] = 249
        self._assert_err("RANGE_ERROR", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["alpha"] = Fraction(1, 1001)
        self._assert_err("RANGE_ERROR", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["alpha"] = Fraction(11, 100)
        self._assert_err("RANGE_ERROR", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["verb_form_counts"] = {}
        self._assert_err("INVALID_VERB_FORMS", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["verb_form_counts"] = {"f1": 5, "F1": 6}
        self._assert_err("DUPLICATE_VERB_FORM", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        for field, val in [
            ("unique_roots", 501),
            ("unique_lemmas", 501),
            ("unique_root_wazn_cells", 501),
            ("unique_root_wazn_cells", 99),
        ]:
            bad = _valid_p1_inputs(); bad[field] = val
            self._assert_err("CONSERVATION_ERROR", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["verb_form_counts"] = {"F1": 501}
        self._assert_err("CONSERVATION_ERROR", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)

        bad = _valid_p1_inputs(); del bad["window_metrics"][40]
        self._assert_err("INVALID_WINDOWS", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); del bad["window_metrics"][10]["raw"]
        self._assert_err("INVALID_WINDOW_ENTRY", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["window_metrics"][10]["raw"] = {"obs": [1, 2]}
        self._assert_err("INVALID_CELL", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["window_metrics"][10]["raw"]["null_pooled"] = [0, 100]
        self._assert_err("ZERO_NULL", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["window_metrics"][10]["root_t4b"]["obs"] = [25, 100]
        self._assert_err("CONSERVATION_ERROR", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); del bad["control_w20_metrics"]["adab_prose"]
        self._assert_err("INVALID_CONTROLS", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["control_w20_metrics"]["quran_stem"]["obs"] = [21, 100]
        self._assert_err("CONTROL_MISMATCH", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)
        bad = _valid_p1_inputs(); bad["control_w20_metrics"]["quran_stem"]["null_pooled"] = [13, 100]
        self._assert_err("CONTROL_MISMATCH", o.audit_root_pattern_lattice_and_cohesion_exact, **bad)

        # Pin EVERY SINGLE lattice & cohesion threshold/conjunct individually
        # 1. lemmas_per_root == 2 -> False
        b = _valid_p1_inputs(); b["unique_lemmas"] = 200
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 2. cells_per_root == 2 -> False
        b = _valid_p1_inputs(); b["unique_root_wazn_cells"] = 200
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 3. len(verb_forms) == 7 -> False
        b = _valid_p1_inputs(); del b["verb_form_counts"]["F8"]
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 4. Holm 12 cells: ge=11 -> p=12/251 <= 1/20 PASSES; ge=12 -> p=13/251 > 1/20 FAILS
        b = _valid_p1_inputs(); b["window_metrics"][40]["root"]["ge_count"] = 11
        self.assertTrue(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        b = _valid_p1_inputs(); b["window_metrics"][40]["root"]["ge_count"] = 12
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 5. root_t4b boundary: ge=11 passes, ge=12 fails
        b = _valid_p1_inputs(); b["window_metrics"][20]["root_t4b"]["ge_count"] = 11
        self.assertTrue(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        b = _valid_p1_inputs(); b["window_metrics"][20]["root_t4b"]["ge_count"] = 12
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 6. odd_split & even_split boundary: ge=11 passes, ge=12 fails
        for sk in ("odd_split_root_t4b", "even_split_root_t4b"):
            b = _valid_p1_inputs(); b["window_metrics"][10][sk]["ge_count"] = 11
            self.assertTrue(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
            b = _valid_p1_inputs(); b["window_metrics"][10][sk]["ge_count"] = 12
            self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 7. lift_reverses_absolute: raw_lift == root_lift fails; W20 stem_lift == root_lift fails
        b = _valid_p1_inputs(); b["window_metrics"][40]["raw"] = _cell(20, 100, 16, 100, 0)
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        b = _valid_p1_inputs()
        b["window_metrics"][20]["stem"] = _cell(22, 100, 15, 100, 0)
        b["control_w20_metrics"]["quran_stem"] = _cell(22, 100, 15, 100, 0)
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 8. shared_classical_prose: each of 4 conjuncts
        for cn in ("quran_stem", "kalila_prose", "adab_prose"):
            b = _valid_p1_inputs()
            b["control_w20_metrics"][cn]["ge_count"] = 11
            self.assertTrue(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
            b = _valid_p1_inputs()
            b["control_w20_metrics"][cn]["ge_count"] = 12
            self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        b = _valid_p1_inputs()
        b["control_w20_metrics"]["kalila_prose"] = _cell(20, 100, 12, 100, 0)  # lift == quran
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        # 9. prose_exceeds_poetry: each of 3 conjuncts
        b = _valid_p1_inputs()
        b["control_w20_metrics"]["poetry_pooled"] = _cell(19, 100, 6, 100, 0)  # == adab
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        b = _valid_p1_inputs()
        b["control_w20_metrics"]["adab_prose"] = _cell(25, 100, 12, 100, 0)
        b["control_w20_metrics"]["poetry_pooled"] = _cell(20, 100, 6, 100, 0)  # == quran
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])
        b = _valid_p1_inputs()
        b["control_w20_metrics"]["kalila_prose"] = _cell(10, 100, 4, 100, 0)  # lift 2.5 > quran, obs == poetry
        self.assertFalse(o.audit_root_pattern_lattice_and_cohesion_exact(**b)["passed"])

    def test_pillar2_happy_errors_and_every_conjunct(self):
        base = _valid_p2_metrics()
        res = o.audit_ring_vs_inclusio_multishuffle_exact(base, n_shuffles=250)
        self.assertTrue(res["passed"])
        self.assertTrue(res["pointwise_mirror_falsified"])
        self.assertFalse(res["boundary_inclusio_holm_confirmed"])
        self.assertFalse(res["boundary_inclusio_separated_from_framed_prose"])
        self.assertEqual(res["boundary_inclusio_status"], "EXPLORATORY_INCONCLUSIVE_NOT_SEPARATED")
        self.assertTrue(res["arbitrary_prose_reverses_to_decay"])

        # Validation errors
        self._assert_err("RANGE_ERROR", o.audit_ring_vs_inclusio_multishuffle_exact, base, n_shuffles=249)
        self._assert_err("RANGE_ERROR", o.audit_ring_vs_inclusio_multishuffle_exact, base, alpha=Fraction(1, 1001))
        self._assert_err("INVALID_METRICS", o.audit_ring_vs_inclusio_multishuffle_exact, "bad")
        bad = _valid_p2_metrics(); del bad["all_mirror"]
        self._assert_err("INVALID_METRICS", o.audit_ring_vs_inclusio_multishuffle_exact, bad)
        for k, idx in [
            ("all_inclusio", 0), ("all_inclusio", 1),
            ("all_middle", 0), ("all_middle", 1),
            ("all_strip10_inclusio", 0), ("all_strip10_inclusio", 1),
            ("all_strip10_middle", 0), ("all_strip10_middle", 1),
        ]:
            bad = _valid_p2_metrics(); bad[k][idx] += 1
            self._assert_err("SPLIT_SUM_MISMATCH", o.audit_ring_vs_inclusio_multishuffle_exact, bad)
        bad = _valid_p2_metrics(); bad["mirror_ge_count"] = 100; bad["mirror_le_count"] = 149
        self._assert_err("CONSERVATION_ERROR", o.audit_ring_vs_inclusio_multishuffle_exact, bad)
        bad = _valid_p2_metrics(); bad["delta_nulls"] = {}
        self._assert_err("INVALID_DELTA_NULLS", o.audit_ring_vs_inclusio_multishuffle_exact, bad)
        bad = _valid_p2_metrics(); bad["delta_nulls"]["all"] = {"ge_count": 10}
        self._assert_err("INVALID_DELTA_ENTRY", o.audit_ring_vs_inclusio_multishuffle_exact, bad)
        bad = _valid_p2_metrics(); bad["delta_nulls"]["all"]["q025"] = [2, 20]; bad["delta_nulls"]["all"]["q975"] = [1, 20]
        self._assert_err("CONSERVATION_ERROR", o.audit_ring_vs_inclusio_multishuffle_exact, bad)
        eq_q = _valid_p2_metrics(); eq_q["delta_nulls"]["all"]["q025"] = [0, 1]; eq_q["delta_nulls"]["all"]["q975"] = [0, 1]
        self.assertTrue(o.audit_ring_vs_inclusio_multishuffle_exact(eq_q)["passed"])

        # Pin EVERY conjunct in Pillar 2
        # Mirror falsification 3 conjuncts + exact alpha boundary (11 -> 12/251 <= 1/20 passes; 12 -> 13/251 fails)
        b = _valid_p2_metrics(); b["all_shift"] = [10, 100]  # all_mirror == shift (< null_pooled!) isolates all_mirror < all_shift
        self.assertFalse(o.audit_ring_vs_inclusio_multishuffle_exact(b)["passed"])
        b = _valid_p2_metrics(); b["all_mirror"] = [14, 100]  # == mirror_null_pooled (< shift!) isolates all_mirror < null
        self.assertFalse(o.audit_ring_vs_inclusio_multishuffle_exact(b)["passed"])
        b = _valid_p2_metrics(); b["mirror_le_count"] = 11
        self.assertTrue(o.audit_ring_vs_inclusio_multishuffle_exact(b)["passed"])
        b = _valid_p2_metrics(); b["mirror_le_count"] = 12
        self.assertFalse(o.audit_ring_vs_inclusio_multishuffle_exact(b)["passed"])

        # boundary_inclusio_holm_confirmed flips passed to False
        b = _valid_p2_metrics(); b["delta_nulls"]["odd_strip10"]["ge_count"] = 1  # 6*(2/251)=12/251 <= 1/20 -> confirmed
        r = o.audit_ring_vs_inclusio_multishuffle_exact(b)
        self.assertTrue(r["boundary_inclusio_holm_confirmed"])
        self.assertFalse(r["passed"])
        self.assertEqual(r["boundary_inclusio_status"], "EXPLORATORY_INCONCLUSIVE_NOT_SEPARATED")

        # boundary_inclusio_separated (both delta > and p < required)
        b = _valid_p2_metrics()
        b["kalila_nat_inclusio"] = [21, 100]  # delta 0.01 < all delta 0.02
        b["delta_nulls"]["kalila_nat"]["ge_count"] = 60  # equal p -> NOT separated (isolates all_p < kalila_p)
        self.assertFalse(o.audit_ring_vs_inclusio_multishuffle_exact(b)["boundary_inclusio_separated_from_framed_prose"])
        b_eqd = _valid_p2_metrics()
        b_eqd["kalila_nat_inclusio"] = [22, 100]  # delta 0.02 == all delta 0.02, while all_p < kalila_p -> isolates delta >
        b_eqd["delta_nulls"]["kalila_nat"]["ge_count"] = 61
        self.assertFalse(o.audit_ring_vs_inclusio_multishuffle_exact(b_eqd)["boundary_inclusio_separated_from_framed_prose"])
        b["delta_nulls"]["kalila_nat"]["ge_count"] = 61  # all_p < kalila_p AND all_delta > kalila_delta -> separated!
        r = o.audit_ring_vs_inclusio_multishuffle_exact(b)
        self.assertTrue(r["boundary_inclusio_separated_from_framed_prose"])
        self.assertFalse(r["passed"])
        # Now ALSO make holm confirmed -> CONFIRMED_AND_SEPARATED
        b["delta_nulls"]["all"]["ge_count"] = 0
        r2 = o.audit_ring_vs_inclusio_multishuffle_exact(b)
        self.assertEqual(r2["boundary_inclusio_status"], "CONFIRMED_AND_SEPARATED")
        self.assertFalse(r2["passed"])

        # arbitrary prose fails decay
        b = _valid_p2_metrics(); b["kalila_arb_inclusio"] = [15, 100]
        self.assertFalse(o.audit_ring_vs_inclusio_multishuffle_exact(b)["passed"])

    def test_pillar3_happy_errors_and_every_conjunct(self):
        recs = _valid_p3_records()
        res = o.audit_translation_remainder_exact(recs, [90, 100], [92, 100])
        self.assertTrue(res["passed"])
        self.assertEqual(res["severe_remainder_both_translators"], 4)
        self.assertEqual(res["selection_rule"], "author_selected_thematic_set_disclosed")
        self.assertFalse(res["per_root"][-1]["multi_verse"])

        # Errors
        self._assert_err("RANGE_ERROR", o.audit_translation_remainder_exact, recs, [90, 100], [92, 100], Fraction(11, 10))
        self._assert_err("INVALID_RECORDS", o.audit_translation_remainder_exact, [], [90, 100], [92, 100])
        self._assert_err("INVALID_RECORD", o.audit_translation_remainder_exact, ["bad"], [90, 100], [92, 100])
        dup = _valid_p3_records(); dup[1]["root"] = "R1"
        self._assert_err("DUPLICATE_ROOT", o.audit_translation_remainder_exact, dup, [90, 100], [92, 100])
        bad = _valid_p3_records(); bad[0]["sahih_top_count"] = 1; bad[0]["sahih_lost_pairs"] = 9
        self._assert_err("RANGE_ERROR", o.audit_translation_remainder_exact, bad, [90, 100], [92, 100])
        bad = _valid_p3_records(); bad[0]["pickthall_top_count"] = 1; bad[0]["pickthall_lost_pairs"] = 9
        self._assert_err("RANGE_ERROR", o.audit_translation_remainder_exact, bad, [90, 100], [92, 100])
        bad = _valid_p3_records(); bad[0]["sahih_lost_pairs"] = 10  # max is 10 - 1 = 9
        self._assert_err("RANGE_ERROR", o.audit_translation_remainder_exact, bad, [90, 100], [92, 100])
        bad = _valid_p3_records(); bad[0]["sahih_total_pairs"] = 9
        self._assert_err("RANGE_ERROR", o.audit_translation_remainder_exact, bad, [90, 100], [92, 100])
        bad = _valid_p3_records(); bad[0]["pickthall_total_pairs"] = 9
        self._assert_err("RANGE_ERROR", o.audit_translation_remainder_exact, bad, [90, 100], [92, 100])
        self._assert_err("NO_MULTI_VERSE_ROOTS", o.audit_translation_remainder_exact, [_valid_p3_records()[-1]], [90, 100], [92, 100])

        # Pin EVERY conjunct in two_instrument_confirmed
        # 1. s_pool_edge == min_loss (0.6) passes, min_loss=61/100 fails
        self.assertTrue(o.audit_translation_remainder_exact(recs, [90, 100], [92, 100], Fraction(6, 10))["passed"])
        self.assertFalse(o.audit_translation_remainder_exact(recs, [90, 100], [92, 100], Fraction(61, 100))["passed"])
        # 2. p_pool_edge < min_loss fails
        recs_low_p = _valid_p3_records()
        for r in recs_low_p[:4]:
            r["pickthall_lost_pairs"] = 4  # 0.4 < 0.5
        self.assertFalse(o.audit_translation_remainder_exact(recs_low_p, [90, 100], [92, 100])["passed"])
        # 3. s_pool_edge >= bg_sahih fails
        self.assertFalse(o.audit_translation_remainder_exact(recs, [60, 100], [92, 100])["passed"])
        # 4. p_pool_edge >= bg_pick fails
        self.assertFalse(o.audit_translation_remainder_exact(recs, [90, 100], [70, 100])["passed"])
        # 5. severe_both_count == 3 fails (exact boundary s_edge=4/10 vs 3/10, p_edge=4/10 vs 3/10)
        recs_b = _valid_p3_records()
        recs_b[0]["sahih_lost_pairs"] = 4; recs_b[0]["pickthall_lost_pairs"] = 4
        self.assertEqual(o.audit_translation_remainder_exact(recs_b, [90, 100], [92, 100])["severe_remainder_both_translators"], 4)
        recs_b[0]["sahih_lost_pairs"] = 3
        self.assertFalse(o.audit_translation_remainder_exact(recs_b, [90, 100], [92, 100])["passed"])
        recs_b = _valid_p3_records()
        recs_b[0]["pickthall_lost_pairs"] = 3
        self.assertFalse(o.audit_translation_remainder_exact(recs_b, [90, 100], [92, 100])["passed"])

    def test_pillar4_cryptographic_binding_and_rederivation(self):
        p1 = o.audit_root_pattern_lattice_and_cohesion_exact(**_valid_p1_inputs())
        p2 = o.audit_ring_vs_inclusio_multishuffle_exact(_valid_p2_metrics())
        p3 = o.audit_translation_remainder_exact(_valid_p3_records(), [90, 100], [92, 100])
        pins = {"corpus/a.txt": "a" * 64}
        axes = {
            "per_layer_null_normalized_lift": True,
            "window_size_10_20_40_holm": True,
            "split_half_internal_consistency": True,
            "honest_boundary_inclusio_adjudication": True,
            "second_instrument_and_controls": True,
        }
        cert = o.certify_arabic_own_terms_5axis_gate(
            "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2, p3, axes
        )
        self.assertTrue(cert["all_gates_passed"])
        self.assertEqual(cert["verdict"], "AUDITED_ARABIC_CONTINUUM_HONEST_LEDGER")
        self.assertIs(cert["live_corpus_recounted"], False)
        body_no_sha = {k: v for k, v in cert.items() if k != "certificate_sha256"}
        self.assertEqual(cert["certificate_sha256"], o.canonical_sha256(body_no_sha))

        # Live mode valid
        cert_live = o.certify_arabic_own_terms_5axis_gate(
            "live_corpus_recount", True, pins, a.AUDIT_FEATURES, p1, p2, p3, axes
        )
        self.assertIs(cert_live["live_corpus_recounted"], True)
        self.assertNotEqual(cert_live["certificate_sha256"], cert["certificate_sha256"])

        # Honest REJECTED_GATE_FAILED when a real pillar fails and axes honestly match
        b2 = _valid_p2_metrics(); b2["kalila_arb_inclusio"] = [15, 100]
        p2_fail = o.audit_ring_vs_inclusio_multishuffle_exact(b2)
        axes_fail = dict(axes, honest_boundary_inclusio_adjudication=False, second_instrument_and_controls=False)
        cert_rej = o.certify_arabic_own_terms_5axis_gate(
            "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2_fail, p3, axes_fail
        )
        self.assertFalse(cert_rej["all_gates_passed"])
        self.assertEqual(cert_rej["verdict"], "REJECTED_GATE_FAILED")

        # All Pillar 4 fail-closed checks
        self._assert_err("INVALID_MODE", o.certify_arabic_own_terms_5axis_gate, "bad", False, pins, a.AUDIT_FEATURES, p1, p2, p3, axes)
        self._assert_err("MODE_MISMATCH", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", True, pins, a.AUDIT_FEATURES, p1, p2, p3, axes)
        self._assert_err("MODE_MISMATCH", o.certify_arabic_own_terms_5axis_gate, "live_corpus_recount", False, pins, a.AUDIT_FEATURES, p1, p2, p3, axes)
        self._assert_err("MISSING_PROVENANCE", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, {}, a.AUDIT_FEATURES, p1, p2, p3, axes)
        for bad_path in ("/etc/x", "a\\b", "a/../b", "file:///x"):
            self._assert_err("UNSAFE_PIN_PATH", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, {bad_path: "a" * 64}, a.AUDIT_FEATURES, p1, p2, p3, axes)
        self._assert_err("DUPLICATE_PIN_PATH", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, {"a": "a" * 64, " a ": "b" * 64}, a.AUDIT_FEATURES, p1, p2, p3, axes)
        for bad_sha in ("0" * 64, "A" * 64, "abc", 123):
            self._assert_err("INVALID_SHA256", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, {"a": bad_sha}, a.AUDIT_FEATURES, p1, p2, p3, axes)
        self._assert_err("INVALID_AXES", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2, p3, {"wrong": True})
        self._assert_err("INVALID_PILLAR", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, "bad", p2, p3, axes)

        # Forged pillar contradictions
        p1_bad = dict(p1); p1_bad["passed"] = False
        self._assert_err("PILLAR_CONTRADICTION", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1_bad, p2, p3, axes)
        p1_miss = dict(p1); p1_miss["window_metrics"] = None
        self._assert_err("PILLAR_CONTRADICTION", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1_miss, p2, p3, axes)
        p1_badw = dict(p1); p1_badw["window_metrics"] = {"10": "not_dict"}
        self._assert_err("PILLAR_CONTRADICTION", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1_badw, p2, p3, axes)
        p1_badc = dict(p1); p1_badc["window_metrics"] = dict(p1["window_metrics"], **{"10": dict(p1["window_metrics"]["10"], raw="bad")})
        self._assert_err("INVALID_CELL", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1_badc, p2, p3, axes)
        p1_badctrl = dict(p1); p1_badctrl["negative_controls_w20"] = dict(p1["negative_controls_w20"], quran_stem="bad")
        self._assert_err("INVALID_CELL", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1_badctrl, p2, p3, axes)

        p2_bad = dict(p2); p2_bad["passed"] = False
        self._assert_err("PILLAR_CONTRADICTION", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2_bad, p3, axes)
        p2_miss = dict(p2); p2_miss["pairs"] = None
        self._assert_err("PILLAR_CONTRADICTION", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2_miss, p3, axes)
        p2_baddn = dict(p2); p2_baddn["delta_null_reports"] = dict(p2["delta_null_reports"], all="bad")
        self._assert_err("INVALID_DELTA_ENTRY", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2_baddn, p3, axes)

        p3_bad = dict(p3); p3_bad["passed"] = False
        self._assert_err("PILLAR_CONTRADICTION", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2, p3_bad, axes)

        axes_bad = dict(axes, window_size_10_20_40_holm=False)
        self._assert_err("AXIS_CONTRADICTION", o.certify_arabic_own_terms_5axis_gate, "standalone_fixture_replay", False, pins, a.AUDIT_FEATURES, p1, p2, p3, axes_bad)


class TestAuditRunnerAndKnownAnswerMiniCorpus(unittest.TestCase):
    def test_parsers_and_hash_verification(self):
        # Tanzil parser
        verses = a.parse_tanzil_lines(["# comment\n", "\n", "1|1|hello world\n", "2|3|a|b\n"])
        self.assertEqual(verses, {(1, 1): "hello world", (2, 3): "a|b"})
        with self.assertRaises(o.ArabicOracleError) as ctx:
            a.parse_tanzil_lines(["malformed_line\n"])
        self.assertEqual(ctx.exception.code, "PARSE_ERROR")

        # OpenITI parser
        all_lines, secs = a.parse_openiti_lines([
            "######OpenITI#\n",
            "#META# ignored\n",
            "#META#Header#End#\n",
            "\n",
            "### | Section 1\n",
            "PageV01P001 \u0643\u062a\u0628 ms001 %~~% ~% \u0642\u0644\u0645\n",
            "### | Section 2\n",
            "12345 !!\n",
            "\u0639\u0644\u0645\n",
        ])
        self.assertEqual(all_lines, [["\u0643\u062a\u0628", "\u0642\u0644\u0645"], ["\u0639\u0644\u0645"]])
        self.assertEqual(secs, [[["\u0643\u062a\u0628", "\u0642\u0644\u0645"]], [["\u0639\u0644\u0645"]]])

        # Leeds parser (all derivative tags + odd/even + target roots)
        leeds = a.parse_leeds_morphology_lines([
            "# header\n",
            "LOCATION\tFORM\tTAG\tFEATURES\n",
            "bad_short_row\n",
            "(1:1:1:1)\tw\tP\tSTEM|POS:P\n",
            "(1:1:2:1)\tf\tV\tSTEM|POS:V|ROOT:ftq|LEM:fataqa\n",
            "(1:2:1:1)\tf\tV\tSTEM|POS:V|(II)|ACT|PCPL|ROOT:ftq|LEM:fattaqa\n",
            "(2:1:1:1)\tr\tN\tSTEM|POS:N|PASS|PCPL|ROOT:rtq\n",
            "(2:2:1:1)\tr\tN\tSTEM|POS:N|VN|ROOT:rtq|LEM:ratq\n",
        ])
        self.assertEqual(leeds["unique_roots"], 2)
        self.assertEqual(leeds["unique_lemmas"], 3)
        self.assertEqual(leeds["unique_root_wazn_cells"], 4)
        self.assertEqual(leeds["total_root_tokens"], 4)
        self.assertEqual(leeds["verb_form_counts"], {"I": 1, "II": 1})
        self.assertEqual(leeds["leeds_odd"], ["ftq", "ftq"])
        self.assertEqual(leeds["leeds_even"], ["rtq", "rtq"])
        self.assertEqual(leeds["target_occs"]["ftq"], 2)
        self.assertEqual(leeds["target_lems"]["ftq"], {"fataqa", "fattaqa"})
        self.assertEqual(leeds["target_verses"]["rtq"], {(2, 1), (2, 2)})

        # verify_corpus_hashes error branches
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(o.ArabicOracleError) as c1:
                a.verify_corpus_hashes(td, {"missing.txt": "a" * 64})
            self.assertEqual(c1.exception.code, "CORPUS_MISSING")
            p = os.path.join(td, "f.txt")
            with open(p, "wb") as fh:
                fh.write(b"abc")
            with self.assertRaises(o.ArabicOracleError) as c2:
                a.verify_corpus_hashes(td, {"f.txt": "0" * 64})
            self.assertEqual(c2.exception.code, "SHA256_MISMATCH")
            good_sha = hashlib.sha256(b"abc").hexdigest()
            self.assertEqual(a.verify_corpus_hashes(td, {"f.txt": good_sha}), {"f.txt": good_sha})

    def test_known_answer_mini_corpus_live_path(self):
        """Hand-computed mini-corpus proving compute_live_measurements computes
        exact known integers from raw text files (not just fixture replay)."""
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "arabic_morphology_quranic-corpus"))
            os.makedirs(os.path.join(td, "openiti_controls"))

            # Construct 20 verses in surah 1 (odd) and 20 verses in surah 2 (even):
            # In each 20-verse surah:
            # - Verses 1..2 (first 10%, k=2) have root "ftq"
            # - Verses 19..20 (last 10%, k=2) have root "ftq"  -> inclusio = (1, 1) per surah!
            # - Verses 10..11 (middle 10%, ms_start=9..10) have root "rtq" -> middle = (0, 2) per surah!
            # - Other verses have unique roots "u3".."u18"
            # Wait: check mirror pairs (i vs 19-i for i=0..9):
            #   i=0 (v1={ftq}) vs i=19 (v20={ftq}) -> inter=1, union=1
            #   i=1 (v2={ftq}) vs i=18 (v19={ftq}) -> inter=1, union=1
            #   i=2..8 (unique) vs i=17..11 (unique) -> inter=0, union=2 each (7 pairs -> 0/14)
            #   i=9 (v10={rtq}) vs i=10 (v11={rtq}) -> inter=1, union=1
            # Total mirror per surah = 3 / 17! Across 2 surahs = 6 / 34!
            # Shift pairs (i vs 10+i for i=0..9):
            #   all disjoint except none -> 0 / 20 per surah! Across 2 surahs = 0 / 40!
            # Inclusio per surah: fs={ftq}, ls={ftq} -> 1/1 -> across 2 surahs = 2/2!
            # Middle per surah: fs={ftq}, ms={rtq} -> 0/2 -> across 2 surahs = 0/4!
            leeds_rows = ["LOCATION\tFORM\tTAG\tFEATURES\n"]
            uth_rows = []
            sah_rows = []
            pic_rows = []
            ar_words = ["\u0643\u062a\u0628", "\u0642\u0644\u0645", "\u0639\u0644\u0645", "\u062d\u0643\u0645"]
            for s in (1, 2):
                for v in range(1, 21):
                    if v in (1, 2, 19, 20):
                        rt = "ftq"
                        tag = "V"
                        feat = f"STEM|POS:V|ROOT:{rt}|LEM:{rt}_lem"
                        s_en = "cleave heaven earth" if v in (1, 2) else "split sky world"
                        p_en = "sunder heaven earth" if v in (1, 2) else "sunder sky world"
                    elif v in (10, 11):
                        rt = "rtq"
                        tag = "N"
                        feat = f"STEM|POS:N|ROOT:{rt}|LEM:{rt}_lem"
                        s_en = "sewn solid"
                        p_en = "joined solid"
                    else:
                        rt = f"r{v}"
                        tag = "N"
                        feat = f"STEM|POS:N|ROOT:{rt}|LEM:{rt}_lem"
                        s_en = f"alpha{v} beta{v}"
                        p_en = f"gamma{v} delta{v}"
                    leeds_rows.append(f"({s}:{v}:1:1)\tx\t{tag}\t{feat}\n")
                    w = ar_words[(v - 1) % 4]
                    uth_rows.append(f"{s}|{v}|{w} {w}\n")
                    sah_rows.append(f"{s}|{v}|{s_en}\n")
                    pic_rows.append(f"{s}|{v}|{p_en}\n")
            # Add short surah 3 (<20 verses) to exercise `len < 20` skip branch
            # AND populate 10 high-frequency filler roots (hf0..hf9, 10 occs each) so top10_roots
            # never strips ftq/rtq during strip10 ring/inclusio evaluation.
            leeds_rows.append("(3:1:1:1)\tx\tN\tSTEM|POS:N|ROOT:sbH|LEM:sbH_lem\n")
            for h_idx in range(10):
                for occ_i in range(10):
                    leeds_rows.append(f"(3:1:{h_idx + 2}:{occ_i + 1})\tx\tN\tSTEM|POS:N|ROOT:hf{h_idx}|LEM:hf{h_idx}_lem\n")
            uth_rows.append("3|1|\u0643\u062a\u0628\n")
            sah_rows.append("3|1|praise\n")
            pic_rows.append("3|1|glory\n")

            openiti_body = ["#META#Header#End#\n", "### | Ch1\n"] + [
                f"{ar_words[i % 4]} {ar_words[(i + 1) % 4]}\n" for i in range(20)
            ]

            files = {
                "arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt": "".join(leeds_rows),
                "tanzil-quran-uthmani.txt": "".join(uth_rows),
                "tanzil-en.sahih.txt": "".join(sah_rows),
                "tanzil-en.pickthall.txt": "".join(pic_rows),
                "openiti_controls/ibn_muqaffa_kalila.txt": "".join(openiti_body),
                "openiti_controls/ibn_muqaffa_adab_kabir.txt": "".join(openiti_body),
                "openiti_controls/imru_al_qays_diwan.txt": "".join(openiti_body),
                "openiti_controls/tarafa_diwan.txt": "".join(openiti_body),
                "openiti_controls/antara_muallaqa.txt": "".join(openiti_body),
            }
            pins = {}
            for rel, txt in files.items():
                fp = os.path.join(td, rel)
                raw = txt.encode("utf-8")
                with open(fp, "wb") as fh:
                    fh.write(raw)
                pins[rel] = hashlib.sha256(raw).hexdigest()

            meas = a.compute_live_measurements(
                td,
                expected_hashes=pins,
                window_sizes=(2, 4, 6),
                bg_pair_count=4,
                arb_chunk_lines=20,
                n_shuffles=4,
            )
            # Verify hand-computed exact integers!
            self.assertEqual(meas["unique_roots"], 27)  # ftq, rtq, sbH (3) + r3..r9 (7) + r12..r18 (7) + hf0..hf9 (10) -> 27
            self.assertEqual(meas["total_root_tokens"], 141)
            self.assertEqual(meas["ring_metrics"]["all_mirror"], [6, 34])
            self.assertEqual(meas["ring_metrics"]["all_shift"], [0, 40])
            self.assertEqual(meas["ring_metrics"]["all_inclusio"], [2, 2])
            self.assertEqual(meas["ring_metrics"]["all_middle"], [0, 4])
            self.assertEqual(meas["ring_metrics"]["odd_inclusio"], [1, 1])
            self.assertEqual(meas["ring_metrics"]["even_inclusio"], [1, 1])
            # Check ftq translation lost pairs:
            # ftq appears in 8 verses (4 with "cleave heaven earth", 4 with "split sky world")
            # Total pairs = C(8,2) = 28. Sahih: 4*4=16 lost pairs! Pickthall: ALL 8 share "sunder" -> 0 lost pairs!
            ftq_rec = [r for r in meas["root_records"] if r["root"] == "ftq"][0]
            self.assertEqual(ftq_rec["verse_count"], 8)
            self.assertEqual(ftq_rec["sahih_total_pairs"], 28)
            self.assertEqual(ftq_rec["sahih_lost_pairs"], 16)
            self.assertEqual(ftq_rec["pickthall_lost_pairs"], 0)
            self.assertEqual(ftq_rec["sahih_top_count"], 4)
            self.assertEqual(ftq_rec["pickthall_top_count"], 8)
            # Check rtq: 4 verses all sharing "solid" -> 0 lost on both!
            rtq_rec = [r for r in meas["root_records"] if r["root"] == "rtq"][0]
            self.assertEqual(rtq_rec["verse_count"], 4)
            self.assertEqual(rtq_rec["sahih_lost_pairs"], 0)
            self.assertEqual(rtq_rec["pickthall_lost_pairs"], 0)

    def test_standalone_runner_live_dispatch_and_cli(self):
        st = a.run_audit(live=False)
        self.assertTrue(st["all_gates_passed"])
        self.assertEqual(st["mode"], "standalone_fixture_replay")
        self.assertIs(st["live_corpus_recounted"], False)
        self.assertEqual(st["boundary_inclusio_status"], "EXPLORATORY_INCONCLUSIVE_NOT_SEPARATED")
        self.assertTrue(st["cohesion_lift_reverses_absolute_ladder"])
        self.assertEqual(st["certificate_sha256"], "252e1dad44ab0d1c9653c41de28e0170f5a28dffc69ea1bea18f47bd9179b757")

        # default_corpus_dir points to ../corpora
        self.assertTrue(a.default_corpus_dir().endswith(os.sep + "corpora"))

        # run_audit(live=True) dispatches to compute_live_measurements and emits live_corpus_recount
        with mock.patch.object(a, "compute_live_measurements", return_value=a.STANDALONE_FIXTURE) as m_live:
            live_cert = a.run_audit(live=True, corpus_dir="/nonexistent_mocked")
            m_live.assert_called_once_with("/nonexistent_mocked")
            self.assertEqual(live_cert["mode"], "live_corpus_recount")
            self.assertIs(live_cert["live_corpus_recounted"], True)
            self.assertEqual(live_cert["certificate_sha256"], "99ec338fc7aec339c1ea5216afd2a0bcac4bff647d487a1a3f80c403b581b951")

        # live=True with corpus_dir=None uses default_corpus_dir()
        with mock.patch.object(a, "compute_live_measurements", return_value=a.STANDALONE_FIXTURE) as m_def:
            a.run_audit(live=True, corpus_dir=None)
            m_def.assert_called_once_with(a.default_corpus_dir())

        # CLI --standalone + --output + exit code 0 & exit code 1 when gate fails
        with tempfile.TemporaryDirectory() as td:
            out_path = os.path.join(td, "cert.json")
            buf = io.StringIO()
            with mock.patch.object(sys, "stdout", buf):
                rc = a.main(["--standalone", "--output", out_path])
            self.assertEqual(rc, 0)
            with open(out_path, "r", encoding="utf-8") as fh:
                written = fh.read()
            self.assertEqual(written, buf.getvalue())
            self.assertEqual(json.loads(written)["certificate_sha256"], st["certificate_sha256"])

        buf_fail = io.StringIO()
        with mock.patch.object(a, "run_audit", return_value={"all_gates_passed": False}), mock.patch.object(sys, "stdout", buf_fail):
            self.assertEqual(a.main(["--standalone"]), 1)

        # CLI --live passes live=True
        with mock.patch.object(a, "run_audit", return_value={"all_gates_passed": True}) as m_ra, mock.patch.object(sys, "stdout", io.StringIO()):
            self.assertEqual(a.main(["--live"]), 0)
            m_ra.assert_called_once_with(live=True, corpus_dir=None)


class TestFetchCorpora(unittest.TestCase):
    def _tiny_manifest(self):
        d1 = b"first corpus payload\n"
        d2 = b"second corpus payload\n"
        return (
            {
                "id": "c1",
                "rel_path": "c1.txt",
                "url": "https://example.invalid/c1.txt",
                "edition": "ed1",
                "upstream_source": "https://example.invalid",
                "licence": "CC0",
                "expected_bytes": len(d1),
                "sha256": hashlib.sha256(d1).hexdigest(),
            },
            {
                "id": "c2",
                "rel_path": "sub/c2.txt",
                "url": "https://example.invalid/c2.txt",
                "edition": "ed2",
                "upstream_source": "https://example.invalid",
                "licence": "CC0",
                "expected_bytes": len(d2),
                "sha256": hashlib.sha256(d2).hexdigest(),
            },
        ), {"https://example.invalid/c1.txt": d1, "https://example.invalid/c2.txt": d2}

    def test_manifest_matches_audit_pins(self):
        self.assertEqual(len(fc.CORPUS_MANIFEST), 9)
        m_pins = {item["rel_path"]: item["sha256"] for item in fc.CORPUS_MANIFEST}
        self.assertEqual(m_pins, a.EXPECTED_CORPUS_SHA256)

    def test_safe_dest_path_and_escape(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertTrue(fc._safe_dest_path(td, "sub/a.txt").endswith(os.path.join("sub", "a.txt")))
            for bad in ("/abs/x.txt", "a\\b.txt", "../escape.txt", "a/../b.txt"):
                with self.assertRaises(fc.FetchError) as ctx:
                    fc._safe_dest_path(td, bad)
                self.assertEqual(ctx.exception.code, "UNSAFE_REL_PATH")
            # Symlink pointing outside dest_dir triggers PATH_ESCAPE
            with tempfile.TemporaryDirectory() as outside:
                link_dir = os.path.join(td, "link")
                os.symlink(outside, link_dir)
                with self.assertRaises(fc.FetchError) as ctx:
                    fc._safe_dest_path(td, "link/escape.txt")
                self.assertEqual(ctx.exception.code, "PATH_ESCAPE")

    def test_fetch_verify_cache_force_and_errors(self):
        manifest, blobs = self._tiny_manifest()
        calls = []

        @contextmanager
        def fake_opener(req, timeout=30):
            calls.append((req.full_url, req.get_header("User-agent"), timeout))
            yield io.BytesIO(blobs[req.full_url])

        with tempfile.TemporaryDirectory() as td, mock.patch.object(fc, "CORPUS_MANIFEST", manifest):
            # Missing triggers CORPUS_MISSING in verify_directory
            with self.assertRaises(fc.FetchError) as cm:
                fc.verify_directory(td)
            self.assertEqual(cm.exception.code, "CORPUS_MISSING")

            # Download fresh
            res = fc.fetch_all(td, timeout=17, force=False, opener=fake_opener)
            self.assertEqual(res["count"], 2)
            self.assertEqual([f["status"] for f in res["files"]], ["downloaded_verified", "downloaded_verified"])
            self.assertEqual(len(calls), 2)
            self.assertEqual(calls[0][1], fc.USER_AGENT)
            self.assertEqual(calls[0][2], 17)

            # verify_directory succeeds
            v = fc.verify_directory(td)
            self.assertEqual(v["count"], 2)
            self.assertEqual([f["status"] for f in v["files"]], ["verified_existing", "verified_existing"])

            # Cached call skips opener
            calls.clear()
            res2 = fc.fetch_all(td, force=False, opener=fake_opener)
            self.assertEqual(calls, [])
            self.assertEqual([f["status"] for f in res2["files"]], ["cached_verified", "cached_verified"])

            # force=True re-downloads
            res3 = fc.fetch_all(td, force=True, opener=fake_opener)
            self.assertEqual(len(calls), 2)
            self.assertEqual([f["status"] for f in res3["files"]], ["downloaded_verified", "downloaded_verified"])

            # Corrupt cached file (same size, wrong hash) -> verify fails SHA256_MISMATCH, fetch_all re-downloads!
            c1_path = os.path.join(td, "c1.txt")
            with open(c1_path, "wb") as fh:
                fh.write(b"X" * len(blobs["https://example.invalid/c1.txt"]))
            with self.assertRaises(fc.FetchError) as csha:
                fc.verify_directory(td)
            self.assertEqual(csha.exception.code, "SHA256_MISMATCH")
            calls.clear()
            res_heal = fc.fetch_all(td, force=False, opener=fake_opener)
            self.assertEqual(len(calls), 1)
            self.assertEqual([f["status"] for f in res_heal["files"]], ["downloaded_verified", "cached_verified"])

            # Wrong size -> verify fails SIZE_MISMATCH
            with open(c1_path, "wb") as fh:
                fh.write(b"short")
            with self.assertRaises(fc.FetchError) as csz:
                fc.verify_directory(td)
            self.assertEqual(csz.exception.code, "SIZE_MISMATCH")

            # Download returning wrong size / wrong sha256 fails closed without writing
            @contextmanager
            def bad_size_opener(req, timeout=30):
                yield io.BytesIO(b"too_short")

            with self.assertRaises(fc.FetchError) as dsz:
                fc.fetch_all(td, force=True, opener=bad_size_opener)
            self.assertEqual(dsz.exception.code, "SIZE_MISMATCH")

            @contextmanager
            def bad_sha_opener(req, timeout=30):
                yield io.BytesIO(b"Z" * len(blobs[req.full_url]))

            with self.assertRaises(fc.FetchError) as dsha:
                fc.fetch_all(td, force=True, opener=bad_sha_opener)
            self.assertEqual(dsha.exception.code, "SHA256_MISMATCH")

            # os.replace failure cleans up temp file and re-raises
            with mock.patch.object(os, "replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    fc.fetch_all(td, force=True, opener=fake_opener)
            leftovers = [fn for fn in os.listdir(td) if fn.startswith(".fetch_")]
            self.assertEqual(leftovers, [])

    def test_fetch_cli_modes(self):
        # --manifest-json
        buf = io.StringIO()
        with mock.patch.object(sys, "stdout", buf):
            self.assertEqual(fc.main(["--manifest-json"]), 0)
        parsed = json.loads(buf.getvalue())
        self.assertEqual(parsed["count"], 9)

        # --verify-only and default download CLI dispatch
        with mock.patch.object(fc, "verify_directory", return_value={"count": 9}) as m_v, mock.patch.object(sys, "stdout", io.StringIO()):
            self.assertEqual(fc.main(["--verify-only", "--dest", "/tmp/x"]), 0)
            m_v.assert_called_once_with("/tmp/x")

        with mock.patch.object(fc, "fetch_all", return_value={"count": 9}) as m_f, mock.patch.object(sys, "stdout", io.StringIO()):
            self.assertEqual(fc.main(["--dest", "/tmp/y", "--force"]), 0)
            m_f.assert_called_once_with("/tmp/y", force=True)


def run_all():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
    print("ALL_AUDIT091_V2_AND_FETCH_TESTS_PASSED")


if __name__ == "__main__":
    run_all()
