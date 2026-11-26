#!/usr/bin/env python3
"""Assertion-free R5 verification & 100% mutation-killing test suite for Raw-Arabic K_12 Scientific Mesh.

- Zero bare assert statements anywhere.
- Zero special-device path dependencies (uses scratch os.mkfifo for non-regular file tests).
- Zero skips in both live Lean and Lean-less env -i PATH=/usr/bin:/bin modes.
- Targets every require_ok guard, boundary comparison, and BoolOp branch in both
  s92_raw_arabic_mesh_oracle.py and verify_s92_raw_arabic_mesh.py.
"""

import copy
import errno
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import s92_raw_arabic_mesh_oracle as O
import verify_s92_raw_arabic_mesh as V

CERT_PATH = HERE / "s92_raw_arabic_mesh_certificate.json"
ANCHOR_PATH = HERE / "s92_raw_arabic_anchor.json"
LEAN_PATH = HERE / "RawArabicHigherOrderMesh.lean"
VERIFIER_PATH = HERE / "verify_s92_raw_arabic_mesh.py"


def _resign_cert(payload, schema=O.SCHEMA_VERSION, track_id=O.TRACK_ID):
    p_sha = hashlib.sha256(V.canonical_json_bytes(payload)).hexdigest()
    body = {
        "schema": schema,
        "track_id": track_id,
        "payload_sha256": p_sha,
        "payload": payload,
    }
    c_sha = hashlib.sha256(V.canonical_json_bytes(body)).hexdigest()
    out = dict(body)
    out["certificate_sha256"] = c_sha
    return out


def _resign_anchor(anchor):
    body = {k: v for k, v in anchor.items() if k != "anchor_sha256"}
    out = dict(body)
    out["anchor_sha256"] = O.canonical_sha256(body)
    return out


class TestS92RawArabicMeshR5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anchor_raw = ANCHOR_PATH.read_bytes()
        cls.anchor = json.loads(cls.anchor_raw.decode("utf-8"))
        cls.cert_raw = CERT_PATH.read_bytes()
        cls.cert = json.loads(cls.cert_raw.decode("utf-8"))
        cls.lean_src = LEAN_PATH.read_text("utf-8")

    def _expect_oracle_err(self, fn, expected_code=None):
        with self.assertRaises(O.S92OracleError) as ctx:
            fn()
        if expected_code is not None:
            self.assertEqual(ctx.exception.code, expected_code)

    def _expect_verify_err(self, fn, expected_code=None):
        with self.assertRaises(V.S92VerifyError) as ctx:
            fn()
        if expected_code is not None:
            self.assertEqual(ctx.exception.code, expected_code)

    # ------------------------------------------------------------------
    # 1. End-to-End Baseline, CLI Modes, Atomic Write, & Exact Determinism
    # ------------------------------------------------------------------
    def test_01_baseline_and_cli_modes(self):
        self.assertTrue(V.verify_certificate_object(copy.deepcopy(self.cert), full_replay=True))
        self.assertTrue(V.verify_certificate_object(copy.deepcopy(self.cert), full_replay=False))
        self.assertTrue(V.secondary_audit_payload(copy.deepcopy(self.cert["payload"])))
        replayed = O.build_certificate()
        self.assertEqual(V.canonical_json_bytes(replayed), self.cert_raw)

        p_st = subprocess.run(
            [sys.executable, "-I", "-B", str(VERIFIER_PATH), "--standalone"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(p_st.returncode, 0)
        self.assertEqual(p_st.stdout, self.cert_raw)

        self.assertEqual(V.main(["--check", str(CERT_PATH)]), 0)

        with tempfile.TemporaryDirectory() as td:
            out_p = Path(td) / "sub" / "cert.json"
            self.assertEqual(V.main(["--write", str(out_p)]), 0)
            self.assertEqual(stat.S_IMODE(os.stat(out_p).st_mode), 0o600)
            self.assertEqual(out_p.read_bytes(), self.cert_raw)
            self.assertEqual(V.main(["--write", str(out_p)]), 0)
            self.assertEqual(V.main(["--check", str(out_p)]), 0)
            self.assertEqual(V.main([]), 0)
            self.assertEqual(V.main(["--verify-datasets"]), 2)
            self.assertEqual(V.main(["--verify-datasets", "--heritage-root", td]), 2)
            self.assertEqual(V.main(["--verify-datasets", "--bayt-root", td]), 2)

    # ------------------------------------------------------------------
    # 2. Oracle Primitives & Exact Pure-Q Algebra Guards
    # ------------------------------------------------------------------
    def test_02_oracle_primitives_and_algebra_guards(self):
        # Exact bit-length boundary (512 passes, 513 fails)
        self.assertEqual(O.require_exact_int((1 << 512) - 1, "x"), (1 << 512) - 1)
        self._expect_oracle_err(lambda: O.require_exact_int(True, "x"), "INVALID_INT")
        self._expect_oracle_err(lambda: O.require_exact_int(1 << 512, "x"), "INT_BIT_LIMIT")
        self._expect_oracle_err(lambda: O.require_exact_int(2, "x", min_val=3), "INT_TOO_SMALL")
        self._expect_oracle_err(lambda: O.require_exact_int(5, "x", max_val=4), "INT_TOO_LARGE")

        self._expect_oracle_err(lambda: O.require_exact_bool(1, "b"), "INVALID_BOOL")
        self._expect_oracle_err(lambda: O.require_non_empty_str(123, "s"), "INVALID_STR")
        self._expect_oracle_err(lambda: O.require_non_empty_str("   ", "s"), "INVALID_STR")

        self._expect_oracle_err(lambda: O.require_pair_ratio((1, 2), "p"), "INVALID_PAIR")
        self._expect_oracle_err(lambda: O.require_pair_ratio([1], "p"), "INVALID_PAIR")
        self._expect_oracle_err(lambda: O.require_pair_ratio([3, 2], "p"), "PAIR_EXCEEDS_ONE")

        self._expect_oracle_err(lambda: O.frac_str(1), "INVALID_FRACTION")
        self._expect_oracle_err(lambda: O.format_exact_decimal(1), "INVALID_FRACTION")
        self.assertEqual(O.format_exact_decimal(Fraction(-3, 2), 2), "-1.50")
        self.assertEqual(O.format_exact_decimal(Fraction(-1, 10**9), 6), "0.000000")
        self.assertEqual(O.format_exact_decimal(Fraction(5, 2), 0), "3")

        O.verify_no_floats_iterative({"a": [1, "s", True, None]})
        self._expect_oracle_err(lambda: O.verify_no_floats_iterative({1: "x"}), "NON_STR_KEY")
        self._expect_oracle_err(lambda: O.verify_no_floats_iterative({"x": Fraction(1, 2)}), "FORBIDDEN_TYPE")

        self._expect_oracle_err(lambda: O.holm_bonferroni_exact([("a", Fraction(1, 2))]), "INVALID_PMAP")
        self._expect_oracle_err(lambda: O.holm_bonferroni_exact({}), "INVALID_PMAP")
        self._expect_oracle_err(lambda: O.holm_bonferroni_exact({"a": 1}), "INVALID_PVAL")
        self._expect_oracle_err(lambda: O.holm_bonferroni_exact({"a": Fraction(0, 1)}), "INVALID_PVAL")
        self._expect_oracle_err(lambda: O.holm_bonferroni_exact({"a": Fraction(2, 1)}), "INVALID_PVAL")
        h_cap = O.holm_bonferroni_exact({"a": Fraction(3, 4), "b": Fraction(4, 5)})
        self.assertEqual(h_cap["adjusted_p_exact"]["a"], "1/1")

        self._expect_oracle_err(lambda: O._round_div_half_up(1, 0), "INVALID_DIV")
        self._expect_oracle_err(lambda: O._round_div_half_up(-1, 2), "INVALID_DIV")

        self.assertEqual(O.exact_ldlt_inertia([[-1, 0], [0, 1]]), [1, 1, 0])
        self._expect_oracle_err(lambda: O.exact_ldlt_inertia([[0, 1], [1, 0]]), "INDEFINITE_ZERO_PIVOT")

        inv_swap = O.exact_invert_matrix([[0, 1], [1, 0]])
        self.assertEqual(inv_swap, [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]])
        self._expect_oracle_err(lambda: O.exact_invert_matrix([[1, 1], [1, 1]]), "SINGULAR_MATRIX")

        self._expect_oracle_err(lambda: O.compute_schur_mesh_exact(11, []), "INVALID_NODE_COUNT")
        self._expect_oracle_err(lambda: O.compute_schur_mesh_exact(12, []), "INVALID_EDGE_COUNT")
        bad_w = [(i, j, 0 if (i, j) == (0, 1) else 1, False) for i in range(12) for j in range(i + 1, 12)]
        self._expect_oracle_err(lambda: O.compute_schur_mesh_exact(12, bad_w), "NONPOSITIVE_WEIGHT")
        dup_e = [(0, 1, 1, False) for _ in range(66)]
        self._expect_oracle_err(lambda: O.compute_schur_mesh_exact(12, dup_e), "BAD_INERTIA")
        self._expect_oracle_err(lambda: O.compute_higher_order_simplices_k12(["a"] * 11, {}), "INVALID_K12")

        self._expect_oracle_err(lambda: O.higher_order_retention_ladder([0, 10], "l"), "RETENTION_OUT_OF_RANGE")
        self._expect_oracle_err(lambda: O.higher_order_retention_ladder([10, 10], "l"), "RETENTION_OUT_OF_RANGE")

    # ------------------------------------------------------------------
    # 3. Oracle Anchor Tamper & Scientific Gate Guards (100% Killed)
    # ------------------------------------------------------------------
    def test_03_oracle_anchor_gates(self):
        self._expect_oracle_err(lambda: O.build_payload_from_anchor([]), "INVALID_ANCHOR")

        a = copy.deepcopy(self.anchor)
        a["schema_version"] = "wrong"
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(a), "BAD_ANCHOR_SCHEMA")

        a = copy.deepcopy(self.anchor)
        a["anchor_sha256"] = "0" * 64
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(a), "ANCHOR_SHA_MISMATCH")

        a = copy.deepcopy(self.anchor)
        a["treatises"] = {str(i): i for i in range(12)}
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_TREATISES")

        a = copy.deepcopy(self.anchor)
        a["treatises"].pop()
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_TREATISES")

        a = copy.deepcopy(self.anchor)
        for t in a["treatises"]:
            t["discipline"] = "optics"
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_DISCIPLINES")

        a = copy.deepcopy(self.anchor)
        a["treatises"][0]["global_c2_pairs"]["raw"] = [0, 100]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "ZERO_C2")

        a = copy.deepcopy(self.anchor)
        a["treatises"][0]["global_c2_pairs"]["dotless_rasm"] = list(a["treatises"][0]["global_c2_pairs"]["raw"])
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "RASM_INFLATION_FAIL")

        a = copy.deepcopy(self.anchor)
        a["within_treatise_w20_b250"]["raw"] = [0] * 12
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_W20_LAYER")

        a = copy.deepcopy(self.anchor)
        del a["within_treatise_w20_b250"]["raw"]["haytham_manazir"]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_W20_LAYER")

        a = copy.deepcopy(self.anchor)
        for tid in a["within_treatise_w20_b250"]["dotless_rasm"]:
            a["within_treatise_w20_b250"]["dotless_rasm"][tid]["jaccard_obs"] = [1, 100]
            a["within_treatise_w20_b250"]["dotless_rasm"][tid]["jaccard_null_pooled"] = [1, 100]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "LOCAL_RASM_REVERSAL_FAIL")

        a = copy.deepcopy(self.anchor)
        for tid in a["within_treatise_w20_b250"]["dotless_rasm"]:
            a["within_treatise_w20_b250"]["dotless_rasm"][tid]["jaccard_null_pooled"] = [1, 1000]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "LOCAL_RASM_REVERSAL_FAIL")

        a = copy.deepcopy(self.anchor)
        for tid in a["within_treatise_w20_b250"]["dotless_rasm"]:
            a["within_treatise_w20_b250"]["dotless_rasm"][tid]["r2_null_pooled"] = [1, 1000000]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "LOCAL_RASM_REVERSAL_FAIL")

        a = copy.deepcopy(self.anchor)
        a["k12_cross_treatise_layers"]["raw"]["cross_discipline_pooled"] = [0, 100]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "ZERO_K12_RATE")

        a = copy.deepcopy(self.anchor)
        a["k12_cross_treatise_layers"]["raw"]["top500_vocab_null_pooled"] = [0, 100]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "ZERO_K12_RATE")

        a = copy.deepcopy(self.anchor)
        a["k12_cross_treatise_layers"]["raw"]["top500_vocab_ge_count"] = 200
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "K12_VOCAB_HOLM_FAIL")

        for lo, hi in (("raw", "dotless_rasm"), ("dotless_rasm", "stem_v1"), ("stem_v1", "stem_v2")):
            a = copy.deepcopy(self.anchor)
            a["k12_cross_treatise_layers"][lo]["cross_discipline_pooled"] = list(
                a["k12_cross_treatise_layers"][hi]["cross_discipline_pooled"]
            )
            self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "CROSS_LIFT_REVERSAL_FAIL")
        for hi, lo in (("raw", "dotless_rasm"), ("dotless_rasm", "stem_v1"), ("stem_v1", "stem_v2")):
            a = copy.deepcopy(self.anchor)
            a["k12_cross_treatise_layers"][hi]["top500_obs_pooled"] = list(
                a["k12_cross_treatise_layers"][lo]["top500_obs_pooled"]
            )
            a["k12_cross_treatise_layers"][hi]["top500_vocab_null_pooled"] = list(
                a["k12_cross_treatise_layers"][lo]["top500_vocab_null_pooled"]
            )
            self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "CROSS_LIFT_REVERSAL_FAIL")

        a = copy.deepcopy(self.anchor)
        a["k12_cross_treatise_layers"]["stem_v1"]["edges"].pop()
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_S1_EDGES")

        # Test exact equality i == j (kills i < j -> i <= j)
        a = copy.deepcopy(self.anchor)
        a["k12_cross_treatise_layers"]["stem_v1"]["edges"][0]["i"] = 1
        a["k12_cross_treatise_layers"]["stem_v1"]["edges"][0]["j"] = 1
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "EDGE_ORDER")

        a = copy.deepcopy(self.anchor)
        a["k12_cross_treatise_layers"]["stem_v1"]["edges"][0]["same_discipline"] = True
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_DISC_SPLIT")

        a = copy.deepcopy(self.anchor)
        a["thematic_root_probes"]["roots"] = {str(i): i for i in range(8)}
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_THEMATIC_ROOTS")

        a = copy.deepcopy(self.anchor)
        a["thematic_root_probes"]["roots"].pop()
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_THEMATIC_ROOTS")

        a = copy.deepcopy(self.anchor)
        a["thematic_root_probes"]["roots"][0]["stem_v1_counts"] = {}
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "ROOT_VEC_TYPE")

        a = copy.deepcopy(self.anchor)
        a["thematic_root_probes"]["roots"][0]["stem_v1_counts"].pop()
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "ROOT_VEC_LEN")

        a = copy.deepcopy(self.anchor)
        a["thematic_root_probes"]["roots"][0]["stem_v1_counts"][0] += 1
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "ROOT_CONSERVATION")

        # Exact boundary honest_partial_count == 1 MUST PASS (kills >= 1 -> > 1); 0 MUST FAIL
        a = copy.deepcopy(self.anchor)
        for idx, r in enumerate(a["thematic_root_probes"]["roots"]):
            r["stem_v1_docs"] = 11 if idx == 0 else 12
        out_one_partial = O.build_payload_from_anchor(_resign_anchor(a))
        self.assertEqual(out_one_partial["pillar2_bridges_and_law5_obstruction"]["thematic_honest_partial_count"], 1)

        a = copy.deepcopy(self.anchor)
        for r in a["thematic_root_probes"]["roots"]:
            r["stem_v1_docs"] = 12
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "NO_HONEST_PARTIAL_ROOT")

        a = copy.deepcopy(self.anchor)
        a["rasm_homography_witnesses"] = {str(i): i for i in range(10)}
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_RASM_WITNESSES")

        a = copy.deepcopy(self.anchor)
        a["rasm_homography_witnesses"].pop()
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_RASM_WITNESSES")

        a = copy.deepcopy(self.anchor)
        a["rasm_homography_witnesses"][0]["collision_excess_delta_s2"] += 1
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "RASM_ALGEBRA_MISMATCH")

        a = copy.deepcopy(self.anchor)
        a["bilingual_scientific_catalogs"]["sensitivity_sweep"] = [0] * 6
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_BI_SWEEP")

        a = copy.deepcopy(self.anchor)
        del a["bilingual_scientific_catalogs"]["sensitivity_sweep"]["stem_v1__en_min5"]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BAD_BI_SWEEP")

        # Exact equality ov_f == bg_r (kills ov_f < bg_r -> <=)
        a = copy.deepcopy(self.anchor)
        v0 = a["bilingual_scientific_catalogs"]["sensitivity_sweep"]["stem_v1__en_min5"]
        v0["all_pairs_bg_en_lost"] = [v0["en_lost_pairs"], v0["ar_linked_pairs"]]
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BI_ABOVE_BG")

        # Exact equality cr_f == ov_f (kills cr_f > ov_f -> >=)
        a = copy.deepcopy(self.anchor)
        v0 = a["bilingual_scientific_catalogs"]["sensitivity_sweep"]["stem_v1__en_min5"]
        v0["ar_linked_pairs"] = 200
        v0["en_lost_pairs"] = 100
        v0["cross_disc_ar_pairs"] = 50
        v0["cross_disc_en_lost"] = 25
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BI_CROSS_NOT_WORSE")

        a = copy.deepcopy(self.anchor)
        a["bilingual_scientific_catalogs"]["sensitivity_sweep"]["stem_v1__en_min5"]["en_perm_le_obs_count"] = 200
        self._expect_oracle_err(lambda: O.build_payload_from_anchor(_resign_anchor(a)), "BI_HOLM_FAIL")

    # ------------------------------------------------------------------
    # 4. Verifier Hardened I/O, JSON Boundary, & Exact Boundary Killers
    # ------------------------------------------------------------------
    def test_04_verifier_io_and_json_guards(self):
        # Exact boundaries: 256-bit int, 80-digit frac num/den, depth == limit, MAX_JSON_BYTES, total == max_bytes
        self.assertEqual(V.require_exact_int((1 << 256) - 1, "i"), (1 << 256) - 1)
        self.assertEqual(V.require_frac_str("1" * 80 + "/1", "f"), Fraction(int("1" * 80), 1))
        self.assertEqual(V.require_frac_str("1/" + "1" * 80, "f"), Fraction(1, int("1" * 80)))
        V.validate_json_tree_iterative({"a": (1 << 256) - 1}, max_depth=1)
        self.assertEqual(V._parse_capped_int_token("1" * 80), int("1" * 80))
        exact_json = '"' + "a" * (V.MAX_JSON_BYTES - 2) + '"'
        self.assertEqual(len(V.parse_strict_json(exact_json)), V.MAX_JSON_BYTES - 2)
        self.assertEqual(len(V.read_regular_bytes_atomic(CERT_PATH, len(self.cert_raw))), len(self.cert_raw))

        self._expect_verify_err(lambda: V.require_sha256_hex(123, "d"), "INVALID_STR")
        self._expect_verify_err(lambda: V.require_sha256_hex("a" * 63, "d"), "INVALID_DIGEST_LEN")
        self._expect_verify_err(lambda: V.require_sha256_hex("A" * 64, "d"), "INVALID_DIGEST_HEX")
        self._expect_verify_err(lambda: V.require_sha256_hex("\ud800" + "a" * 63, "d"), "INVALID_UNICODE_STR")
        self._expect_verify_err(lambda: V.require_exact_int(True, "i"), "INVALID_INT")
        self._expect_verify_err(lambda: V.require_exact_int(1 << 256, "i"), "INT_BIT_LIMIT")
        self._expect_verify_err(lambda: V.require_exact_int(0, "i", min_val=1), "INT_TOO_SMALL")
        self._expect_verify_err(lambda: V.require_exact_int(5, "i", max_val=4), "INT_TOO_LARGE")
        self._expect_verify_err(lambda: V.require_exact_bool(1, "b"), "INVALID_BOOL")
        self._expect_verify_err(lambda: V.require_exact_bool(False, "b", expected=True), "BOOL_VALUE_MISMATCH")
        self._expect_verify_err(lambda: V.require_dec6_fraction("1.23", "f"), "INVALID_DEC6")
        self.assertEqual(V.require_dec6_fraction("-0.250000", "f"), Fraction(-1, 4))
        self.assertEqual(V.require_dec6_fraction("9" * 80 + ".000000", "f"), Fraction(int("9" * 80), 1))
        self.assertEqual(V.require_dec6_fraction("-" + "9" * 80 + ".000000", "f"), Fraction(-int("9" * 80), 1))
        self._expect_verify_err(lambda: V.require_dec6_fraction("9" * 81 + ".000000", "f"), "DEC6_WHOLE_DIGITS")
        self._expect_verify_err(lambda: V.require_dec6_fraction("9" * 4301 + ".000000", "f"), "DEC6_WHOLE_DIGITS")
        self._expect_verify_err(lambda: V.require_frac_str("1/0", "f"), "INVALID_FRAC_STR")
        self._expect_verify_err(lambda: V.require_frac_str("1" * 81 + "/1", "f"), "FRAC_NUM_DIGITS")
        self._expect_verify_err(lambda: V.require_frac_str("1/" + "1" * 81, "f"), "FRAC_DEN_DIGITS")

        deep = {}
        cur = deep
        for _ in range(70):
            cur["a"] = {}
            cur = cur["a"]
        self._expect_verify_err(lambda: V.validate_json_tree_iterative(deep), "JSON_DEPTH_EXCEEDED")
        self._expect_verify_err(lambda: V.validate_json_tree_iterative({"x": 1 << 256}), "INT_BIT_LIMIT")
        self._expect_verify_err(lambda: V.validate_json_tree_iterative({"x": (1, 2)}), "FORBIDDEN_JSON_TYPE")
        V.validate_json_tree_iterative({"a": True, "b": None, "c": [1, "ok"]})

        self._expect_verify_err(lambda: V.parse_strict_json('{"a":1,"a":2}'), "DUPLICATE_JSON_KEY")
        self._expect_verify_err(lambda: V.parse_strict_json('{"a":1.5}'), "FLOAT_FORBIDDEN")
        self._expect_verify_err(lambda: V.parse_strict_json('{"a":NaN}'), "NONFINITE_CONSTANT")
        self._expect_verify_err(lambda: V.parse_strict_json('{"a":' + "9" * 81 + '}'), "INT_DIGIT_LIMIT")
        self._expect_verify_err(lambda: V.parse_strict_json('{"a":' + str(1 << 260) + '}'), "INT_BIT_LIMIT")
        self._expect_verify_err(lambda: V.parse_strict_json("{"), "JSON_DECODE_ERROR")
        self._expect_verify_err(lambda: V.parse_strict_json('"' + "a" * (V.MAX_JSON_BYTES + 1) + '"'), "JSON_TOO_LARGE")

        self._expect_verify_err(lambda: V.read_regular_bytes_atomic("not_a_path", 100), "INVALID_PATH_TYPE")
        self._expect_verify_err(lambda: V.read_regular_bytes_atomic(Path("a\x00b"), 100), "INVALID_PATH_NUL")
        self._expect_verify_err(lambda: V.read_regular_bytes_atomic(Path("/"), 100), "FILE_NOT_FOUND")
        self._expect_verify_err(lambda: V.read_regular_bytes_atomic(Path("a/.."), 100), "PARENT_REF_FORBIDDEN")
        self._expect_verify_err(lambda: V.write_regular_bytes_atomic_0600(Path("x"), "not_bytes"), "INVALID_BYTES")

        # Strict False return from _is_symlink_at on missing file (kills except OSError: pass)
        dfd = os.open(".", os.O_RDONLY | os.O_DIRECTORY)
        try:
            self.assertIs(V._is_symlink_at(dfd, "__definitely_absent_s92__"), False)
        finally:
            os.close(dfd)

        # Mocked os.read OSError kills M054
        with mock.patch("os.read", side_effect=OSError(errno.EIO, "io")):
            self._expect_verify_err(lambda: V.read_regular_bytes_atomic(CERT_PATH, V.MAX_JSON_BYTES), "FILE_READ_ERROR")

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            # Missing ancestor directory -> FILE_NOT_FOUND (kills M045)
            self._expect_verify_err(
                lambda: V.read_regular_bytes_atomic(tdp / "no_such_dir" / "f.json", 100),
                "FILE_NOT_FOUND",
            )

            # Read-only parent directory on mkdir -> MKDIR_ERROR (kills M040!)
            ro_dir = tdp / "ro_dir"
            ro_dir.mkdir()
            os.chmod(ro_dir, 0o500)
            try:
                self._expect_verify_err(
                    lambda: V.write_regular_bytes_atomic_0600(ro_dir / "nested" / "f.json", b"x"),
                    "MKDIR_ERROR",
                )
            finally:
                os.chmod(ro_dir, 0o700)

            # Temp file st_nlink != 1 during atomic write -> HARDLINK_FORBIDDEN (kills M063)
            with mock.patch("os.fstat", return_value=SimpleNamespace(st_nlink=2)):
                self._expect_verify_err(
                    lambda: V.write_regular_bytes_atomic_0600(tdp / "hl_tmp.json", b"x"),
                    "HARDLINK_FORBIDDEN",
                )

            # Scratch FIFO (non-regular file without relying on host device paths)
            fifo = tdp / "pipe.fifo"
            os.mkfifo(fifo)
            self._expect_verify_err(lambda: V.read_regular_bytes_atomic(fifo, 100), "FILE_NOT_FOUND")
            self._expect_verify_err(lambda: V.write_regular_bytes_atomic_0600(fifo, b"x"), "FILE_WRITE_ERROR")

            # Symlink target & symlink ancestor
            real_f = tdp / "real.json"
            real_f.write_bytes(self.cert_raw)
            sym_f = tdp / "sym.json"
            os.symlink(real_f, sym_f)
            self._expect_verify_err(lambda: V.read_regular_bytes_atomic(sym_f, V.MAX_JSON_BYTES), "SYMLINK_FORBIDDEN")
            self._expect_verify_err(lambda: V.write_regular_bytes_atomic_0600(sym_f, b"x"), "SYMLINK_FORBIDDEN")

            real_dir = tdp / "rdir"
            real_dir.mkdir()
            (real_dir / "c.json").write_bytes(self.cert_raw)
            sym_dir = tdp / "sdir"
            os.symlink(real_dir, sym_dir)
            self._expect_verify_err(
                lambda: V.read_regular_bytes_atomic(sym_dir / "c.json", V.MAX_JSON_BYTES),
                "SYMLINK_ANCESTOR_FORBIDDEN",
            )

            # Logical $PWD symlink check on relative path (and PWD unset vs relative)
            old_pwd = os.environ.get("PWD")
            try:
                os.environ["PWD"] = str(sym_dir)
                self._expect_verify_err(
                    lambda: V.read_regular_bytes_atomic(Path("c.json"), V.MAX_JSON_BYTES),
                    "SYMLINK_ANCESTOR_FORBIDDEN",
                )
                os.environ["PWD"] = "rel" + str(sym_dir)
                self._expect_verify_err(
                    lambda: V.read_regular_bytes_atomic(Path("definitely_missing_xyz"), 100),
                    "FILE_NOT_FOUND",
                )
                os.environ.pop("PWD", None)
                self._expect_verify_err(
                    lambda: V.read_regular_bytes_atomic(Path("definitely_missing_xyz"), 100),
                    "FILE_NOT_FOUND",
                )
            finally:
                if old_pwd is None:
                    os.environ.pop("PWD", None)
                else:
                    os.environ["PWD"] = old_pwd

            hl_f = tdp / "hardlink.json"
            os.link(real_f, hl_f)
            self._expect_verify_err(lambda: V.read_regular_bytes_atomic(hl_f, V.MAX_JSON_BYTES), "HARDLINK_FORBIDDEN")
            self._expect_verify_err(lambda: V.write_regular_bytes_atomic_0600(hl_f, b"x"), "HARDLINK_FORBIDDEN")
            hl_f.unlink()

            self._expect_verify_err(lambda: V.read_regular_bytes_atomic(real_f, 10), "FILE_TOO_LARGE")

            crlf_f = tdp / "crlf.json"
            crlf_f.write_bytes(self.cert_raw + b"\r\n")
            self._expect_verify_err(lambda: V.verify_certificate_file(crlf_f), "CRLF_FORBIDDEN")

            badu_f = tdp / "badu.json"
            badu_f.write_bytes(b"\xff\xfe")
            self._expect_verify_err(lambda: V.verify_certificate_file(badu_f), "INVALID_UTF8")

            nonc_f = tdp / "nonc.json"
            nonc_f.write_bytes(self.cert_raw + b"\n")
            self._expect_verify_err(lambda: V.verify_certificate_file(nonc_f), "NONCANONICAL_BYTES")

    # ------------------------------------------------------------------
    # 5. Secondary Semantic Audit (SEC) & FR0/FR1 Exhaustive Guard Killers
    # ------------------------------------------------------------------
    def test_05_secondary_audit_and_fr_guards(self):
        # Exact boundary test for _require_dec6_close, _require_non_empty_str, & _require_dec6_ratio_consistent
        self.assertEqual(V._require_dec6_close("0.500000", Fraction(1, 2), "C", "l"), Fraction(1, 2))
        self._expect_verify_err(
            lambda: V._require_dec6_close("0.500010", Fraction(1, 2), "DRIFT_EXACT", "l"),
            "DRIFT_EXACT",
        )
        self.assertEqual(V._require_non_empty_str("x", "NE", "l"), "x")
        self._expect_verify_err(lambda: V._require_non_empty_str("   ", "NE", "l"), "NE")
        self._expect_verify_err(lambda: V._require_non_empty_str(None, "NE", "l"), "INVALID_STR")
        # Exact interval boundaries with eps=1e-6: num=5e-6, den=3e-6 -> lo=4/4=1.000000, hi=6/2=3.000000
        V._require_dec6_ratio_consistent("0.000005", "0.000003", "1.000000", "R", "l")
        V._require_dec6_ratio_consistent("0.000005", "0.000003", "3.000000", "R", "l")
        self._expect_verify_err(lambda: V._require_dec6_ratio_consistent("0.000000", "0.000003", "1.000000", "R", "l"), "R_NUM_POS")
        self._expect_verify_err(lambda: V._require_dec6_ratio_consistent("0.000005", "0.000001", "1.000000", "R", "l"), "R_DEN_POS")
        self._expect_verify_err(lambda: V._require_dec6_ratio_consistent("0.000005", "0.000003", "0.999999", "R", "l"), "R_LO")
        self._expect_verify_err(lambda: V._require_dec6_ratio_consistent("0.000005", "0.000003", "3.000001", "R", "l"), "R_HI")

        self._expect_verify_err(lambda: V.verify_certificate_object(self.cert, full_replay=1), "INVALID_FULL_REPLAY")
        self._expect_verify_err(lambda: V.verify_certificate_object([], full_replay=False), "CERT_KEYS_MISMATCH_TYPE")
        c = copy.deepcopy(self.cert)
        c["extra"] = 1
        self._expect_verify_err(lambda: V.verify_certificate_object(c, full_replay=False), "CERT_KEYS_MISMATCH")

        c = copy.deepcopy(self.cert)
        c["schema"] = "wrong"
        self._expect_verify_err(lambda: V.verify_certificate_object(c, full_replay=False), "CERT_SCHEMA_MISMATCH")

        c = copy.deepcopy(self.cert)
        c["track_id"] = "wrong"
        self._expect_verify_err(lambda: V.verify_certificate_object(c, full_replay=False), "CERT_TRACK_MISMATCH")

        c = copy.deepcopy(self.cert)
        c["payload"] = []
        self._expect_verify_err(lambda: V.verify_certificate_object(c, full_replay=False), "PAYLOAD_NOT_DICT")

        c = copy.deepcopy(self.cert)
        c["payload_sha256"] = "0" * 64
        self._expect_verify_err(lambda: V.verify_certificate_object(c, full_replay=False), "PAYLOAD_SHA_MISMATCH")

        c = copy.deepcopy(self.cert)
        c["certificate_sha256"] = "0" * 64
        self._expect_verify_err(lambda: V.verify_certificate_object(c, full_replay=False), "CERT_SHA_MISMATCH")

        with tempfile.TemporaryDirectory() as td:
            bad_a = Path(td) / "anchor.json"
            bad_a.write_bytes(b"{}")
            self._expect_verify_err(
                lambda: V.verify_certificate_object(copy.deepcopy(self.cert), full_replay=True, anchor_path=bad_a),
                "ANCHOR_FILE_SHA_MISMATCH",
            )

        p_mod = copy.deepcopy(self.cert["payload"])
        p_mod["anchor_pin"]["matched_local_tokens"] = 3001
        c_mod = _resign_cert(p_mod)
        self.assertTrue(V.verify_certificate_object(c_mod, full_replay=False))
        self._expect_verify_err(
            lambda: V.verify_certificate_object(c_mod, full_replay=True),
            "REPLAY_PAYLOAD_SHA_MISMATCH",
        )

        self._expect_verify_err(lambda: V.secondary_audit_payload([]), "PAYLOAD_KEYS_MISMATCH_TYPE")
        self._expect_verify_err(lambda: V.secondary_audit_payload({}), "PAYLOAD_KEYS_MISMATCH")

        def tamper(mutator, code):
            p = copy.deepcopy(self.cert["payload"])
            mutator(p)
            self._expect_verify_err(lambda: V.secondary_audit_payload(p), code)

        tamper(lambda p: p.__setitem__("schema_version", "bad"), "BAD_SCHEMA_VERSION")
        tamper(lambda p: p.__setitem__("track_id", "bad"), "BAD_TRACK_ID")
        tamper(lambda p: p.__setitem__("all_gates_passed", False), "BOOL_VALUE_MISMATCH")
        tamper(lambda p: p.__setitem__("verdict", "bad"), "BAD_VERDICT")

        tamper(lambda p: p["novelty_classification"].__setitem__("prior_art_n0", "none"), "MISSING_N0_CREDIT")
        tamper(lambda p: p["novelty_classification"].__setitem__("max_novelty", "N2"), "BAD_NOVELTY_TIER")
        tamper(lambda p: p["anchor_pin"].__setitem__("anchor_internal_sha256", "ab" * 32), "ANCHOR_INTERNAL_SHA_MISMATCH")
        # B3 regression: re-hashed treatise sha256 & token_count bumps must fail closed on BOTH FR0 and FR1
        p_tsha = copy.deepcopy(self.cert["payload"])
        p_tsha["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["sha256"] = "ab" * 32
        c_tsha = _resign_cert(p_tsha)
        self._expect_verify_err(lambda: V.verify_certificate_object(c_tsha, full_replay=False), "TREATISE_PIN_MISMATCH")
        self._expect_verify_err(lambda: V.verify_certificate_object(c_tsha, full_replay=True), "TREATISE_PIN_MISMATCH")
        p_ttok = copy.deepcopy(self.cert["payload"])
        p_ttok["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["token_count"] += 1
        p_ttok["pillar1_raw_arabic_k12_mesh"]["total_raw_arabic_tokens"] += 1
        c_ttok = _resign_cert(p_ttok)
        self._expect_verify_err(lambda: V.verify_certificate_object(c_ttok, full_replay=False), "TREATISE_PIN_MISMATCH")
        self._expect_verify_err(lambda: V.verify_certificate_object(c_ttok, full_replay=True), "TREATISE_PIN_MISMATCH")
        tamper(lambda p: p["novelty_classification"].__setitem__("methodology", "bad"), "BAD_METHOD")
        tamper(lambda p: p["anchor_pin"].__setitem__("anchor_schema_version", "bad"), "ANCHOR_SCHEMA")

        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"].__setitem__("continuum_audit_id", "X"), "N0_CONT_ID")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"].__setitem__("lexicon_audit_id", "X"), "N0_LEX_ID")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"].__setitem__("continuum_cert_file_sha256", "0" * 64), "N0_CONT_FILE_SHA")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"].__setitem__("continuum_cert_internal_sha256", "0" * 64), "N0_CONT_INT_SHA")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"].__setitem__("lexicon_cert_file_sha256", "0" * 64), "N0_LEX_FILE_SHA")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"].__setitem__("lexicon_cert_internal_sha256", "0" * 64), "N0_LEX_INT_SHA")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("edge_loss_pair", "x"), "LADDER_PAIR_TYPE")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("edge_loss_pair", [1]), "LADDER_PAIR")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("edge_loss_exact", "1/2"), "LADDER_LOSS_EQ")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("edge_retention_exact", "1/2"), "LADDER_RET_EQ")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("edge_loss_dec6", "0.500000"), "LADDER_LOSS_DEC")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("edge_retention_dec6", "0.500000"), "LADDER_RET_DEC")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("k1_exp1_survival_dec6", "0.500000"), "LADDER_SURV")
        tamper(lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("k1_exp1_collapse_dec6", "0.500000"), "LADDER_COLL")

        def swap_sahih_same_cross(p):
            ld = p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]
            ld["sahih_15root_cross_lemma"] = copy.deepcopy(ld["sahih_15root_same_lemma"])
        tamper(swap_sahih_same_cross, "SAHIH_CROSS_AMPLIFICATION")

        def swap_pick_same_cross(p):
            ld = p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]
            ld["pickthall_15root_cross_lemma"] = copy.deepcopy(ld["pickthall_15root_same_lemma"])
        tamper(swap_pick_same_cross, "PICK_CROSS_AMPLIFICATION")

        def mut_holm(fn, code):
            tamper(lambda p: fn(p["pillar1_raw_arabic_k12_mesh"]["holm_k12_vocab_null_4layers"]), code)
        mut_holm(lambda h: h.__setitem__("alpha_exact", "1/10"), "HOLM_ALPHA")
        mut_holm(lambda h: h.__setitem__("adjusted_p_exact", []), "HOLM_EX_TYPE")
        mut_holm(lambda h: h.__setitem__("adjusted_p_dec6", []), "HOLM_D6_TYPE")
        mut_holm(lambda h: h.__setitem__("rejected_at_alpha", []), "HOLM_REJ_TYPE")
        mut_holm(lambda h: h["adjusted_p_exact"].pop("raw"), "HOLM_EX_LEN")
        mut_holm(lambda h: h["adjusted_p_dec6"].pop("raw"), "HOLM_D6_KEYS")
        mut_holm(lambda h: h["rejected_at_alpha"].pop("raw"), "HOLM_REJ_KEYS")
        mut_holm(lambda h: h["adjusted_p_dec6"].__setitem__("raw", "0.999999"), "HOLM_DEC")
        def fail_vocab_holm(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["holm_k12_vocab_null_4layers"]
            h["adjusted_p_exact"]["raw"] = "1/1"
            h["adjusted_p_dec6"]["raw"] = "1.000000"
            h["rejected_at_alpha"]["raw"] = False
            h["rejected_count"] = 3
        tamper(fail_vocab_holm, "HOLM_RECOMP_EQ")

        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("author", None), "INVALID_STR")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("title_en", 12345), "INVALID_STR")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("rel_path", []), "INVALID_STR")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("author", "   "), "TREATISE_STR")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][1].__setitem__("id", p["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["id"]), "DUP_TREATISE_ID")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("vocab_dotless_rasm", p["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["vocab_raw"]), "RASM_VOCAB_COLLAPSE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("rasm_c2_inflation_dec6", "1.000000"), "RASM_INFL_GT1")
        def collapse_discs(p):
            for t in p["pillar1_raw_arabic_k12_mesh"]["treatises"]:
                t["discipline"] = "optics"
        tamper(collapse_discs, "P1_DISCS")

        # Exact equality boundaries on W=20 (preserving ratio consistency so W20_JL / W20_RL / W20_RASM_* fire!)
        def eq_w20_jl(p):
            wl = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"]
            wl["pooled_jaccard_obs_dec6"] = wl["pooled_jaccard_null_dec6"]
            wl["pooled_jaccard_lift_dec6"] = "1.000000"
        tamper(eq_w20_jl, "W20_JL")
        def eq_w20_rl(p):
            wl = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"]
            wl["pooled_r2_obs_dec6"] = wl["pooled_r2_null_dec6"]
            wl["pooled_r2_lift_dec6"] = "1.000000"
        tamper(eq_w20_rl, "W20_RL")
        def eq_w20_rasm_abs(p):
            w20 = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]
            w20["dotless_rasm"]["pooled_jaccard_obs_dec6"] = w20["raw"]["pooled_jaccard_obs_dec6"]
            jo = V.require_dec6_fraction(w20["dotless_rasm"]["pooled_jaccard_obs_dec6"], "jo")
            jn = V.require_dec6_fraction(w20["dotless_rasm"]["pooled_jaccard_null_dec6"], "jn")
            w20["dotless_rasm"]["pooled_jaccard_lift_dec6"] = O.format_exact_decimal(jo / jn)
        tamper(eq_w20_rasm_abs, "W20_RASM_ABS_ORDER")
        def eq_w20_rasm_lift(p):
            w20 = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]
            raw_jl = V.require_dec6_fraction(w20["raw"]["pooled_jaccard_lift_dec6"], "jl")
            m_jo = V.require_dec6_fraction(w20["dotless_rasm"]["pooled_jaccard_obs_dec6"], "mjo")
            w20["dotless_rasm"]["pooled_jaccard_null_dec6"] = O.format_exact_decimal(m_jo / raw_jl)
            w20["dotless_rasm"]["pooled_jaccard_lift_dec6"] = w20["raw"]["pooled_jaccard_lift_dec6"]
        tamper(eq_w20_rasm_lift, "W20_RASM_LIFT_REV")

        # Exact equality boundaries on K_12 (preserving ratio consistency!)
        def eq_k12_wc(p):
            kl = p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]["raw"]
            kl["within_discipline_r2_dec6"] = kl["cross_discipline_r2_dec6"]
            kl["within_to_cross_ratio_dec6"] = "1.000000"
        tamper(eq_k12_wc, "K12_WITHIN_GT_CROSS")
        def eq_k12_rat(p):
            kl = p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]["raw"]
            kl["within_discipline_r2_dec6"] = "10.000001"
            kl["cross_discipline_r2_dec6"] = "10.000000"
            kl["within_to_cross_ratio_dec6"] = "1.000000"
        tamper(eq_k12_rat, "K12_RAT")
        tamper(
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]["raw"].__setitem__("discipline_perm_raw_p_exact", "1/251"),
            "K12_DISC_P_EQ",
        )
        for lo, hi in (("raw", "dotless_rasm"), ("dotless_rasm", "stem_v1"), ("stem_v1", "stem_v2")):
            def eq_k12_abs(p, lo=lo, hi=hi):
                k12 = p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]
                k12[lo]["cross_discipline_r2_dec6"] = k12[hi]["cross_discipline_r2_dec6"]
                wr = V.require_dec6_fraction(k12[lo]["within_discipline_r2_dec6"], "wr")
                cr = V.require_dec6_fraction(k12[lo]["cross_discipline_r2_dec6"], "cr")
                if wr <= cr:
                    wr = cr + Fraction(1, 1000)
                    k12[lo]["within_discipline_r2_dec6"] = O.format_exact_decimal(wr)
                k12[lo]["within_to_cross_ratio_dec6"] = O.format_exact_decimal(wr / cr)
            tamper(eq_k12_abs, "K12_ABS_CHAIN")
            def eq_k12_lift(p, lo=lo, hi=hi):
                k12 = p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]
                k12[lo]["top500_obs_r2_dec6"] = k12[hi]["top500_obs_r2_dec6"]
                k12[lo]["top500_null_r2_dec6"] = k12[hi]["top500_null_r2_dec6"]
                k12[lo]["top500_vocab_lift_dec6"] = k12[hi]["top500_vocab_lift_dec6"]
            tamper(eq_k12_lift, "K12_LIFT_REV_CHAIN")

        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_simplicial_complex"]["k1_edges"].__setitem__("cross_discipline_share_exact", "1/2"), "SIMP_SHARE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_simplicial_complex"]["k1_edges"].__setitem__("cross_discipline_share_dec6", "0.500000"), "SIMP_SHARE_DEC")
        # Exact boundaries for SIMP_MEAN_LO / SIMP_MEAN_HI (== passes, out-of-range fails)
        p_simp_lo = copy.deepcopy(self.cert["payload"])
        p_simp_lo["pillar1_raw_arabic_k12_mesh"]["k12_simplicial_complex"]["k1_edges"]["mean_bottleneck_weight_dec6"] = "22.000000"
        self.assertTrue(V.secondary_audit_payload(p_simp_lo))
        p_simp_hi = copy.deepcopy(self.cert["payload"])
        p_simp_hi["pillar1_raw_arabic_k12_mesh"]["k12_simplicial_complex"]["k1_edges"]["mean_bottleneck_weight_dec6"] = "390.000000"
        self.assertTrue(V.secondary_audit_payload(p_simp_hi))
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_simplicial_complex"]["k1_edges"].__setitem__("mean_bottleneck_weight_dec6", "21.999999"), "SIMP_MEAN_LO")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_simplicial_complex"]["k1_edges"].__setitem__("mean_bottleneck_weight_dec6", "390.000001"), "SIMP_MEAN_HI")

        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("laplacian_inertia", [10, 1, 1]), "RAW_INERTIA")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("foster_sum_exact", "10/1"), "RAW_FOSTER")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("min_compounding_ratio_dec6", "1.000000"), "COMP_GT1")
        # Exact boundaries for COMP_RANGE, RAW_MIN_CEFF_POS, RAW_CEFF_LO, RAW_CEFF_HI, RAW_WEIGHTED_MEAN
        p_raw_eq = copy.deepcopy(self.cert["payload"])
        rs_eq = p_raw_eq["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"]
        rs_eq["max_compounding_ratio_dec6"] = rs_eq["min_compounding_ratio_dec6"]
        rs_eq["min_ceff_dec6"] = rs_eq["mean_ceff_dec6"]
        rs_eq["max_ceff_dec6"] = rs_eq["mean_ceff_dec6"]
        self.assertTrue(V.secondary_audit_payload(p_raw_eq))
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("max_compounding_ratio_dec6", "2.000000"), "COMP_RANGE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("min_ceff_dec6", "0.000000"), "RAW_MIN_CEFF_POS")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("min_ceff_dec6", "500.000000"), "RAW_CEFF_LO")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("max_ceff_dec6", "300.000000"), "RAW_CEFF_HI")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("mean_within_discipline_ceff_dec6", "1000.000000"), "RAW_WEIGHTED_MEAN")

        # Uniform thinning exact boundaries & cross-arithmetic checks (kills M154 + UNI_R_DEC + UNI_CEFF_SCALE + UNI_RINFL)
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["uniform_sahih_thinning"].__setitem__("retention_exact", "0/1"), "UNI_R_RANGE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["uniform_sahih_thinning"].__setitem__("retention_exact", "1/1"), "UNI_R_RANGE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["uniform_sahih_thinning"].__setitem__("retention_dec6", "0.500000"), "UNI_R_DEC")
        tamper(
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["uniform_sahih_thinning"].__setitem__(
                "mean_ceff_dec6",
                p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"]["mean_ceff_dec6"],
            ),
            "UNI_COLLAPSE",
        )
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["uniform_sahih_thinning"].__setitem__("mean_ceff_dec6", "100.000000"), "UNI_CEFF_SCALE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["uniform_sahih_thinning"].__setitem__("effective_resistance_inflation_dec6", "1.000000"), "UNI_RINFL")

        # Heterogeneous silo-cut exact boundaries & cross-arithmetic checks (kills M162, M164 + HET_*_DEC/EQ)
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("laplacian_inertia", [10, 1, 1]), "HET_INERTIA")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("foster_sum_exact", "10/1"), "HET_FOSTER")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("within_edge_retention_dec6", "0.500000"), "HET_RW_DEC")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("cross_edge_retention_dec6", "0.500000"), "HET_RC_DEC")
        def eq_het_ret(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            h["cross_edge_retention_exact"] = h["within_edge_retention_exact"]
            h["cross_edge_retention_dec6"] = h["within_edge_retention_dec6"]
        tamper(eq_het_ret, "HET_RET_ORDER")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("mean_ceff_dec6", "10.000000"), "HET_WEIGHTED_MEAN")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("overall_ceff_collapse_dec6", "0.100000"), "HET_OV_COLL_EQ")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("within_ceff_collapse_dec6", "0.100000"), "HET_W_COLL_EQ")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("cross_ceff_collapse_dec6", "0.100000"), "HET_CR_COLL_EQ")
        def eq_het_coll(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            raw_s = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"]
            # Make cross collapse equal within collapse while preserving weighted-mean & collapse arithmetic!
            w_c = V.require_dec6_fraction(h["within_ceff_collapse_dec6"], "wc")
            rc = V.require_dec6_fraction(raw_s["mean_cross_discipline_ceff_dec6"], "rc")
            rm = V.require_dec6_fraction(raw_s["mean_ceff_dec6"], "rm")
            hmw = V.require_dec6_fraction(h["mean_within_ceff_dec6"], "hmw")
            hmc = rc * (Fraction(1, 1) - w_c)
            hm = (10 * hmw + 56 * hmc) / 66
            h["mean_cross_ceff_dec6"] = O.format_exact_decimal(hmc)
            h["mean_ceff_dec6"] = O.format_exact_decimal(hm)
            h["overall_ceff_collapse_dec6"] = O.format_exact_decimal(Fraction(1, 1) - hm / rm)
            h["cross_ceff_collapse_dec6"] = h["within_ceff_collapse_dec6"]
        tamper(eq_het_coll, "HET_COLL_ORDER")

        tamper(lambda p: p["pillar2_bridges_and_law5_obstruction"].__setitem__("thematic_selection_rule", "bad"), "P2_RULE")
        tamper(lambda p: p["pillar2_bridges_and_law5_obstruction"].__setitem__("thematic_universal_12_of_12_count", 4), "P2_ROOT_PARTITION")
        tamper(lambda p: p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][0].__setitem__("root_key", None), "INVALID_STR")
        tamper(
            lambda p: p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][1].__setitem__(
                "root_key",
                p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][0]["root_key"],
            ),
            "DUP_ROOT_KEY",
        )
        def mismatch_u12(p):
            p["pillar2_bridges_and_law5_obstruction"]["thematic_universal_12_of_12_count"] = 2
            p["pillar2_bridges_and_law5_obstruction"]["thematic_honest_partial_count"] = 6
        tamper(mismatch_u12, "P2_U12_COUNT")

        def fail_bi_holm(p):
            h = p["pillar3_bilingual_scientific_catalogs"]["holm_6_variants"]
            k0 = next(iter(h["adjusted_p_exact"]))
            h["adjusted_p_exact"][k0] = "1/1"
            h["adjusted_p_dec6"][k0] = "1.000000"
            h["rejected_at_alpha"][k0] = False
            h["rejected_count"] = 5
        tamper(fail_bi_holm, "HOLM_RECOMP_EQ")
        tamper(lambda p: p["pillar3_bilingual_scientific_catalogs"].__setitem__("sensitivity_variants", []), "P3_SV_KEYS_TYPE")
        tamper(lambda p: p["pillar3_bilingual_scientific_catalogs"]["sensitivity_variants"].pop("stem_v1__en_min5"), "P3_SV_KEYS")
        # Exact boundary P3_BG_LE1 (1.000000 passes, 1.000001 fails)
        p_bg_eq = copy.deepcopy(self.cert["payload"])
        p_bg_eq["pillar3_bilingual_scientific_catalogs"]["sensitivity_variants"]["stem_v1__en_min5"]["bg_en_loss_dec6"] = "1.000000"
        self.assertTrue(V.secondary_audit_payload(p_bg_eq))
        tamper(
            lambda p: p["pillar3_bilingual_scientific_catalogs"]["sensitivity_variants"]["stem_v1__en_min5"].__setitem__("bg_en_loss_dec6", "1.000001"),
            "P3_BG_LE1",
        )
        # Exact equality ov_f == bg_f == Fraction(1, 2) (kills M183!)
        def eq_bi_ov_bg(p):
            v = p["pillar3_bilingual_scientific_catalogs"]["sensitivity_variants"]["stem_v1__en_min5"]
            v["overall_ladder"] = O.higher_order_retention_ladder([1, 2], "half")
            v["bg_en_loss_dec6"] = "0.500000"
        tamper(eq_bi_ov_bg, "P3_OV_LT_BG")
        def swap_bi_cr_ov(p):
            v = p["pillar3_bilingual_scientific_catalogs"]["sensitivity_variants"]["stem_v1__en_min5"]
            v["cross_disc_ladder"] = copy.deepcopy(v["overall_ladder"])
        tamper(swap_bi_cr_ov, "P3_CR_GT_OV")
        tamper(lambda p: p["pillar3_bilingual_scientific_catalogs"].__setitem__("overall_loss_min_dec6", "0.000001"), "P3_OV_MIN")
        tamper(lambda p: p["pillar3_bilingual_scientific_catalogs"].__setitem__("overall_loss_max_dec6", "0.999999"), "P3_OV_MAX")
        tamper(lambda p: p["pillar3_bilingual_scientific_catalogs"].__setitem__("cross_disc_loss_min_dec6", "0.000001"), "P3_CR_MIN")
        tamper(lambda p: p["pillar3_bilingual_scientific_catalogs"].__setitem__("cross_disc_loss_max_dec6", "0.999999"), "P3_CR_MAX")

        tamper(lambda p: p["lean_companion_spec"].__setitem__("lean_file", "bad.lean"), "LEAN_FILE_NAME")
        tamper(lambda p: p["lean_companion_spec"].__setitem__("allowed_axioms", ["Classical.choice"]), "LEAN_AXIOMS")
        tamper(lambda p: p["lean_companion_spec"].__setitem__("theorems", []), "LEAN_THEOREMS")

        # Re-Signed Semantic Forgery Regressions (F01..F14): MUST fail on SEC, FR0, AND FR1!
        def _mut_f03(p):
            wl = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["stem_v1"]
            wl["pooled_jaccard_obs_dec6"] = "0.010000"
            wl["pooled_jaccard_null_dec6"] = "0.990000"
            wl["pooled_jaccard_lift_dec6"] = "999.000000"
        def _mut_f14(p):
            sch = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]
            sch["raw_arabic_k12"]["mean_within_discipline_ceff_dec6"] = "1000.000000"
            sch["heterogeneous_english_silo_cut_k12"]["mean_within_ceff_dec6"] = "261.805000"
        forgeries = (
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"].__setitem__("pooled_jaccard_null_dec6", "GARBAGE"),
            lambda p: (p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"].__setitem__("pooled_r2_obs_dec6", None), p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"].__setitem__("pooled_r2_null_dec6", 999)),
            _mut_f03,
            lambda p: (p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]["raw"].__setitem__("top500_obs_r2_dec6", "NOPE"), p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]["raw"].__setitem__("top500_null_r2_dec6", None)),
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]["raw"].__setitem__("within_to_cross_ratio_dec6", "999.999999"),
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_simplicial_complex"]["k1_edges"].__setitem__("cross_discipline_share_dec6", "NOT_A_NUMBER"),
            lambda p: (p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("min_ceff_dec6", "GARBAGE"), p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("max_ceff_dec6", None), p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("max_compounding_ratio_dec6", [])),
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["raw_arabic_k12"].__setitem__("mean_within_discipline_ceff_dec6", "10.000000"),
            lambda p: (p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("author", None), p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("title_en", 12345), p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("rel_path", [])),
            lambda p: [r.__setitem__("root_key", None) for r in p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"]],
            lambda p: p["n0_bayt_al_hikma_prior_art"].__setitem__("continuum_cert_file_sha256", "0" * 64),
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["k12_cross_treatise_layers"]["raw"].__setitem__("discipline_perm_raw_p_exact", "1/251"),
            lambda p: p["n0_bayt_al_hikma_prior_art"]["higher_order_collapse_ladders"]["sahih_7root"].__setitem__("edge_loss_pair", [1, 2]),
            _mut_f14,
        )
        for fn in forgeries:
            p_f = copy.deepcopy(self.cert["payload"])
            fn(p_f)
            c_f = _resign_cert(p_f)
            self._expect_verify_err(lambda pf=p_f: V.secondary_audit_payload(pf))
            self._expect_verify_err(lambda cf=c_f: V.verify_certificate_object(cf, full_replay=False))
            self._expect_verify_err(lambda cf=c_f: V.verify_certificate_object(cf, full_replay=True))

        # Strict str check (C01..C04): strict str on prior_art_n0 across SEC, FR0, FR1, and CLI --check (rc=2)
        with tempfile.TemporaryDirectory() as td_c:
            for idx_c, bad_n0 in enumerate((None, 12345, {"bayt-al-hikma": 1}, ["bayt-al-hikma"])):
                p_c = copy.deepcopy(self.cert["payload"])
                p_c["novelty_classification"]["prior_art_n0"] = bad_n0
                c_c = _resign_cert(p_c)
                self._expect_verify_err(lambda pc=p_c: V.secondary_audit_payload(pc), "INVALID_STR")
                self._expect_verify_err(lambda cc=c_c: V.verify_certificate_object(cc, full_replay=False), "INVALID_STR")
                self._expect_verify_err(lambda cc=c_c: V.verify_certificate_object(cc, full_replay=True), "INVALID_STR")
                cf_p = Path(td_c) / f"c0{idx_c + 1}.json"
                cf_p.write_bytes(V.canonical_json_bytes(c_c))
                self.assertEqual(V.main(["--check", str(cf_p)]), 2)

        # Extended semantic forgery (F15..F23) & exact mutation-killing boundaries on SEC, FR0, and FR1!
        # F23 boundaries: vocab_raw <= token_count, vocab_stem_v1 <= vocab_raw, vocab_stem_v2 <= vocab_stem_v1
        p_voc_eq = copy.deepcopy(self.cert["payload"])
        t0 = p_voc_eq["pillar1_raw_arabic_k12_mesh"]["treatises"][0]
        t0["vocab_raw"] = t0["token_count"]
        t0["vocab_stem_v1"] = t0["vocab_raw"]
        t0["vocab_stem_v2"] = t0["vocab_stem_v1"]
        self.assertTrue(V.secondary_audit_payload(p_voc_eq))
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("vocab_raw", p["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["token_count"] + 1), "INT_TOO_LARGE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("vocab_stem_v1", p["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["vocab_raw"] + 1), "INT_TOO_LARGE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("vocab_stem_v2", p["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["vocab_stem_v1"] + 1), "INT_TOO_LARGE")

        # F17 & F18 exact boundaries on W=20 rates in (0, 1], Battani p in (0, 1], and dotless_rasm local R^2 reversal
        p_w20_eq = copy.deepcopy(self.cert["payload"])
        w_s2 = p_w20_eq["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["stem_v2"]
        w_s2["pooled_jaccard_obs_dec6"] = "1.000000"
        w_s2["pooled_jaccard_null_dec6"] = "0.500000"
        w_s2["pooled_jaccard_lift_dec6"] = "2.000000"
        w_s2["pooled_r2_obs_dec6"] = "1.000000"
        w_s2["pooled_r2_null_dec6"] = "0.500000"
        w_s2["pooled_r2_lift_dec6"] = "2.000000"
        w_s2["holm_jaccard_battani_p_adj_dec6"] = "1.000000"
        self.assertTrue(V.secondary_audit_payload(p_w20_eq))
        def mut_w20_jo_gt1(p):
            w = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["stem_v2"]
            w["pooled_jaccard_obs_dec6"] = "1.000001"
            w["pooled_jaccard_null_dec6"] = "0.500000"
            w["pooled_jaccard_lift_dec6"] = "2.000002"
        tamper(mut_w20_jo_gt1, "W20_JO_LE1")
        def mut_w20_jn_ge1(p):
            w = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["stem_v2"]
            w["pooled_jaccard_obs_dec6"] = "1.000000"
            w["pooled_jaccard_null_dec6"] = "1.000000"
            w["pooled_jaccard_lift_dec6"] = "1.000001"
        tamper(mut_w20_jn_ge1, "W20_JN_LT1")
        def mut_w20_ro_gt1(p):
            w = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["stem_v2"]
            w["pooled_r2_obs_dec6"] = "1.000001"
            w["pooled_r2_null_dec6"] = "0.500000"
            w["pooled_r2_lift_dec6"] = "2.000002"
        tamper(mut_w20_ro_gt1, "W20_RO_LE1")
        def mut_w20_rn_ge1(p):
            w = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["stem_v2"]
            w["pooled_r2_obs_dec6"] = "1.000000"
            w["pooled_r2_null_dec6"] = "1.000000"
            w["pooled_r2_lift_dec6"] = "1.000001"
        tamper(mut_w20_rn_ge1, "W20_RN_LT1")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"].__setitem__("holm_jaccard_battani_p_adj_dec6", "0.000000"), "W20_BAT_P_RANGE")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"].__setitem__("holm_jaccard_battani_p_adj_dec6", "1.000001"), "W20_BAT_P_RANGE")
        def eq_w20_rasm_r2_abs(p):
            w20 = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]
            w20["dotless_rasm"]["pooled_r2_obs_dec6"] = w20["raw"]["pooled_r2_obs_dec6"]
            ro = V.require_dec6_fraction(w20["dotless_rasm"]["pooled_r2_obs_dec6"], "ro")
            rn = V.require_dec6_fraction(w20["dotless_rasm"]["pooled_r2_null_dec6"], "rn")
            w20["dotless_rasm"]["pooled_r2_lift_dec6"] = O.format_exact_decimal(ro / rn)
        tamper(eq_w20_rasm_r2_abs, "W20_RASM_R2_ABS_ORDER")
        def eq_w20_rasm_r2_lift(p):
            w20 = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]
            raw_rl = V.require_dec6_fraction(w20["raw"]["pooled_r2_lift_dec6"], "rl")
            m_ro = V.require_dec6_fraction(w20["dotless_rasm"]["pooled_r2_obs_dec6"], "mro")
            w20["dotless_rasm"]["pooled_r2_null_dec6"] = O.format_exact_decimal(m_ro / raw_rl)
            w20["dotless_rasm"]["pooled_r2_lift_dec6"] = w20["raw"]["pooled_r2_lift_dec6"]
        tamper(eq_w20_rasm_r2_lift, "W20_RASM_R2_LIFT_REV")

        # F19 exact pins: uniform Sahih/Pickthall/bilingual & het cross retention pinned to N0/P3 ladders
        def _mut_uni_ret(p, uk):
            sch = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]
            rm = V.require_dec6_fraction(sch["raw_arabic_k12"]["mean_ceff_dec6"], "rm")
            ub = sch[uk]
            rf = Fraction(1, 2)
            ub["retention_exact"] = "1/2"
            ub["retention_dec6"] = "0.500000"
            ub["mean_ceff_dec6"] = O.format_exact_decimal(rm * rf)
            ub["effective_resistance_inflation_dec6"] = "2.000000"
        tamper(lambda p: _mut_uni_ret(p, "uniform_sahih_thinning"), "UNI_SAHIH_RET_PIN")
        tamper(lambda p: _mut_uni_ret(p, "uniform_pickthall_thinning"), "UNI_PICK_RET_PIN")
        tamper(lambda p: _mut_uni_ret(p, "uniform_bilingual_catalog_thinning"), "UNI_BI_RET_PIN")
        def _mut_het_rc_pin(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            h["cross_edge_retention_exact"] = "1/10"
            h["cross_edge_retention_dec6"] = "0.100000"
        tamper(_mut_het_rc_pin, "HET_CROSS_RET_PIN")

        # F15 & F16 exact boundaries on het retentions (0,1), positive mean_ceffs, and collapses in (0,1)
        def _mut_het_rc_zero(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            h["cross_edge_retention_exact"] = "0/1"
            h["cross_edge_retention_dec6"] = "0.000000"
        tamper(_mut_het_rc_zero, "HET_RC_POS")
        def _mut_het_rw_one(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            h["within_edge_retention_exact"] = "1/1"
            h["within_edge_retention_dec6"] = "1.000000"
        tamper(_mut_het_rw_one, "HET_RW_LT1")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("mean_within_ceff_dec6", "0.000000"), "HET_MW_POS")
        tamper(lambda p: p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"].__setitem__("mean_cross_ceff_dec6", "0.000000"), "HET_MC_POS")
        def _mut_het_w_zero(p):
            sch = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]
            rs = sch["raw_arabic_k12"]
            h = sch["heterogeneous_english_silo_cut_k12"]
            rw = V.require_dec6_fraction(rs["mean_within_discipline_ceff_dec6"], "rw")
            rm = V.require_dec6_fraction(rs["mean_ceff_dec6"], "rm")
            hmc = V.require_dec6_fraction(h["mean_cross_ceff_dec6"], "hmc")
            hm = (10 * rw + 56 * hmc) / 66
            h["mean_within_ceff_dec6"] = rs["mean_within_discipline_ceff_dec6"]
            h["mean_ceff_dec6"] = O.format_exact_decimal(hm)
            h["within_ceff_collapse_dec6"] = "0.000000"
            h["overall_ceff_collapse_dec6"] = O.format_exact_decimal(Fraction(1, 1) - hm / rm)
        tamper(_mut_het_w_zero, "HET_W_COLL_POS")
        def _mut_het_cr_one(p):
            sch = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]
            rs = sch["raw_arabic_k12"]
            h = sch["heterogeneous_english_silo_cut_k12"]
            rm = V.require_dec6_fraction(rs["mean_ceff_dec6"], "rm")
            hmw = V.require_dec6_fraction(h["mean_within_ceff_dec6"], "hmw")
            hmc = Fraction(1, 1_000_000)
            hm = (10 * hmw + 56 * hmc) / 66
            h["mean_cross_ceff_dec6"] = "0.000001"
            h["mean_ceff_dec6"] = O.format_exact_decimal(hm)
            h["overall_ceff_collapse_dec6"] = O.format_exact_decimal(Fraction(1, 1) - hm / rm)
            h["cross_ceff_collapse_dec6"] = "1.000000"
        tamper(_mut_het_cr_one, "HET_CR_COLL_LT1")
        def _mut_het_ov_zero(p):
            sch = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]
            rs = sch["raw_arabic_k12"]
            h = sch["heterogeneous_english_silo_cut_k12"]
            rw = V.require_dec6_fraction(rs["mean_within_discipline_ceff_dec6"], "rw")
            rc = V.require_dec6_fraction(rs["mean_cross_discipline_ceff_dec6"], "rc")
            hmw = rw - Fraction(6, 10000)
            hmc = rc - Fraction(9, 10000)
            hm = (10 * hmw + 56 * hmc) / 66
            h["mean_within_ceff_dec6"] = O.format_exact_decimal(hmw)
            h["mean_cross_ceff_dec6"] = O.format_exact_decimal(hmc)
            h["mean_ceff_dec6"] = O.format_exact_decimal(hm)
            h["within_ceff_collapse_dec6"] = "0.000001"
            h["cross_ceff_collapse_dec6"] = "0.000002"
            h["overall_ceff_collapse_dec6"] = "0.000000"
        tamper(_mut_het_ov_zero, "HET_OV_COLL_POS")
        def _mut_het_ov_one(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            h["mean_within_ceff_dec6"] = "0.000001"
            h["mean_cross_ceff_dec6"] = "0.000001"
            h["mean_ceff_dec6"] = "0.000001"
            h["within_ceff_collapse_dec6"] = "0.999998"
            h["cross_ceff_collapse_dec6"] = "0.999999"
            h["overall_ceff_collapse_dec6"] = "1.000000"
        tamper(_mut_het_ov_one, "HET_OV_COLL_LT1")

        # F22 exact boundaries on thematic_roots (stem_v1_total >= d1, stem_v1_disciplines <= min(6, d1), stem_v2_total >= d2)
        p_r_eq = copy.deepcopy(self.cert["payload"])
        r2 = p_r_eq["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][2]
        r2["stem_v1_total"] = r2["stem_v1_docs"]
        r2["stem_v2_total"] = r2["stem_v2_docs"]
        self.assertTrue(V.secondary_audit_payload(p_r_eq))
        tamper(lambda p: p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][2].__setitem__("stem_v1_total", 4), "INT_TOO_SMALL")
        tamper(lambda p: p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][2].__setitem__("stem_v1_disciplines", 6), "INT_TOO_LARGE")
        tamper(lambda p: p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][2].__setitem__("stem_v2_total", 4), "INT_TOO_SMALL")

        # Full Re-Signed Forgery Regressions (F15..F23): MUST fail on SEC, FR0, AND FR1!
        def _mut_f15(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            h["mean_within_ceff_dec6"] = "2000.000000"
            h["mean_cross_ceff_dec6"] = "1000.000000"
            h["mean_ceff_dec6"] = "1151.515152"
            h["overall_ceff_collapse_dec6"] = "-1.633451"
            h["within_ceff_collapse_dec6"] = "-2.551631"
            h["cross_ceff_collapse_dec6"] = "-1.410201"
        def _mut_f16(p):
            h = p["pillar1_raw_arabic_k12_mesh"]["schur_conductance_and_silo_collapse"]["heterogeneous_english_silo_cut_k12"]
            h["within_edge_retention_exact"] = "5/1"
            h["within_edge_retention_dec6"] = "5.000000"
            h["cross_edge_retention_exact"] = "-1/1"
            h["cross_edge_retention_dec6"] = "-1.000000"
        def _mut_f18(p):
            w = p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["dotless_rasm"]
            w["pooled_r2_obs_dec6"] = "0.020000"
            w["pooled_r2_null_dec6"] = "0.005000"
            w["pooled_r2_lift_dec6"] = "4.000000"
        def _mut_f21(p):
            p3 = p["pillar3_bilingual_scientific_catalogs"]
            old_sv = p3["sensitivity_variants"]
            vals = list(old_sv.values())
            p3["sensitivity_variants"] = {f"fake_{i}": vals[i] for i in range(6)}
            p3["holm_6_variants"] = O.holm_bonferroni_exact({f"fake_{i}": Fraction(1, 251) for i in range(6)})
        def _mut_f22(p):
            r = p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][0]
            r["stem_v1_docs"] = 1
            r["zero_treatises_s1_count"] = 11
            r["stem_v1_disciplines"] = 6
        def _mut_f23(p):
            t = p["pillar1_raw_arabic_k12_mesh"]["treatises"][0]
            t["vocab_raw"] = t["token_count"] + 100000
            t["vocab_dotless_rasm"] = t["token_count"] + 50000
        forgeries_r2 = (
            _mut_f15,
            _mut_f16,
            lambda p: p["pillar1_raw_arabic_k12_mesh"]["within_treatise_w20_b250"]["raw"].__setitem__("holm_jaccard_battani_p_adj_dec6", "-999.000000"),
            _mut_f18,
            lambda p: _mut_uni_ret(p, "uniform_sahih_thinning"),
            lambda p: p["pillar3_bilingual_scientific_catalogs"]["sensitivity_variants"]["stem_v1__en_min5"].__setitem__("bg_en_loss_dec6", "999.000000"),
            _mut_f21,
            _mut_f22,
            _mut_f23,
        )
        for fn in forgeries_r2:
            p_f = copy.deepcopy(self.cert["payload"])
            fn(p_f)
            c_f = _resign_cert(p_f)
            self._expect_verify_err(lambda pf=p_f: V.secondary_audit_payload(pf))
            self._expect_verify_err(lambda cf=c_f: V.verify_certificate_object(cf, full_replay=False))
            self._expect_verify_err(lambda cf=c_f: V.verify_certificate_object(cf, full_replay=True))

        # 4,301-digit dec6 DoS fails closed (rc=2, DEC6_WHOLE_DIGITS) & FR0 narrative pins
        with tempfile.TemporaryDirectory() as td_r4:
            p_dos = copy.deepcopy(self.cert["payload"])
            p_dos["pillar1_raw_arabic_k12_mesh"]["treatises"][0]["rasm_c2_inflation_dec6"] = "9" * 4301 + ".000000"
            c_dos = _resign_cert(p_dos)
            self._expect_verify_err(lambda: V.secondary_audit_payload(p_dos), "DEC6_WHOLE_DIGITS")
            self._expect_verify_err(lambda: V.verify_certificate_object(c_dos, full_replay=False), "DEC6_WHOLE_DIGITS")
            dos_p = Path(td_r4) / "dec6_dos.json"
            dos_p.write_bytes(V.canonical_json_bytes(c_dos))
            self.assertEqual(V.main(["--check", str(dos_p)]), 2)

        for narr_fn, narr_code in (
            (lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("title_en", "Forged Title"), "TREATISE_META_MISMATCH"),
            (lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("author", "Forged Author"), "TREATISE_META_MISMATCH"),
            (lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][2].__setitem__("discipline", "optics"), "TREATISE_META_MISMATCH"),
            (lambda p: p["pillar1_raw_arabic_k12_mesh"]["treatises"][0].__setitem__("rel_path", "forged.md"), "TREATISE_META_MISMATCH"),
            (lambda p: p["pillar2_bridges_and_law5_obstruction"]["thematic_roots"][0].__setitem__("root_key", "forged_root"), "P2_ROOT_KEYS_PIN"),
        ):
            p_n = copy.deepcopy(self.cert["payload"])
            narr_fn(p_n)
            c_n = _resign_cert(p_n)
            self._expect_verify_err(lambda pn=p_n: V.secondary_audit_payload(pn), narr_code)
            self._expect_verify_err(lambda cn=c_n: V.verify_certificate_object(cn, full_replay=False), narr_code)
            self._expect_verify_err(lambda cn=c_n: V.verify_certificate_object(cn, full_replay=True), narr_code)

    # ------------------------------------------------------------------
    # 6. R10+ Comment-Only Lean Scanner, Axiom Parser, & Live/Lean-Less Parity
    # ------------------------------------------------------------------
    def test_06_lean_r10_scanner_axioms_and_leanless_parity(self):
        self.assertTrue(V.scan_lean_source(self.lean_src))
        # Leading line comment, nested block comment, standalone / and -, and EOF line comment without trailing newline
        nested_ok = (
            "-- head line comment\n"
            + self.lean_src
            + "\n/- outer /- inner / - -/ outer -/\n-- tail comment no newline"
        )
        self.assertTrue(V.scan_lean_source(nested_ok))
        # Single '-' in code must NOT swallow subsequent banned token on same line (kills ch=='-' and nxt=='-'!)
        self._expect_verify_err(
            lambda: V.scan_lean_source(self.lean_src + "\ntheorem bad_sub : Nat := 1 - 1 + sorry\n"),
            "LEAN_BANNED_TOKEN",
        )

        self._expect_verify_err(lambda: V.scan_lean_source(self.lean_src + "\x00"), "LEAN_BAD_CONTROL")
        self._expect_verify_err(lambda: V.scan_lean_source(self.lean_src + "\r\n"), "LEAN_BAD_CONTROL")
        self._expect_verify_err(lambda: V.scan_lean_source(self.lean_src + "\u202e"), "LEAN_FORBIDDEN_UNICODE")
        for bad_ch in ('"', "'", "\u00ab", "\u00bb", "`"):
            self._expect_verify_err(lambda: V.scan_lean_source(self.lean_src + bad_ch), "LEAN_FORBIDDEN_CHAR")
        self._expect_verify_err(lambda: V.scan_lean_source(self.lean_src + "\n-/\n"), "LEAN_STRAY_COMMENT_CLOSE")
        self._expect_verify_err(lambda: V.scan_lean_source(self.lean_src + "\n/- unclosed\n"), "LEAN_UNCLOSED_COMMENT")
        self._expect_verify_err(lambda: V.scan_lean_source(self.lean_src + "\n#eval 1\n"), "LEAN_HASH_CMD_FORBIDDEN")
        # R10+ decide (native := ...) & multiline bypass regressions (R10+ static guard)
        for dec_atk in (
            "theorem t : 1 + 1 = 2 := by decide (native := false || true)",
            "theorem t : 1 + 1 = 2 := by decide (native := false\n || true)",
            "theorem t : 1 + 1 = 2 := by decide (native := false == false)",
            "theorem t : 1 + 1 = 2 := by decide (native := false != true)",
            "theorem t : 1 + 1 = 2 := by decide (native := false.not)",
            "theorem t : 1 + 1 = 2 := by decide (config := {})",
        ):
            self._expect_verify_err(
                lambda a=dec_atk: V.scan_lean_source(self.lean_src + f"\n{a}\n"),
                "LEAN_DECIDE_OPT_FORBIDDEN",
            )
        for tok in (
            "import Init", "sorry", "axiom foo : Prop", "native_decide", "Classical", "native",
            "theorem t : 1 = 1 := by decide +native",
            "def p (n : Nat) : Nat := dbg_trace (toString n); n",
            "def p1 (n : Nat) : Nat := dbgTrace (Nat.repr n) (fun _ => n)",
            "def p2 (n : Nat) : Nat := dbgTraceVal n",
            "def p3 (n : Nat) : Nat := dbgTraceIfShared (Nat.repr n) n",
            "def p4 (n : Nat) : Nat := dbgSleep 0 (fun _ => n)",
            "def p5 (n : Nat) : Nat := dbgStackTrace (fun _ => n)",
            "def p6 (n : Nat) : Nat := _root_.dbgTrace (Nat.repr n) (fun _ => n)",
            "def p7 : Nat := panicWithPosWithDecl (Nat.repr 0) (Nat.repr 0) 0 0 (Nat.repr 0)",
            "def p8 : Nat := panic! (String.ofList [])",
            "def p9 : Nat := unreachable!",
            "def p10 : Nat := panicCore 0 (Nat.repr 0)",
            "@[init] def i1 : BaseIO Unit := pure ()",
            "@[builtin_init] def i2 : BaseIO Unit := pure ()",
            "declare_syntax_cat mycat",
            "macro_rules",
            "elab_rules",
            "ofReduceNat", "mkSorry", "bv_decide", "notation", "prefix", "infixl", "export",
            "terminalTacticsAsSorry",
        ):
            self._expect_verify_err(lambda t=tok: V.scan_lean_source(self.lean_src + f"\n{t}\n"), "LEAN_BANNED_TOKEN")
        # Clean controls & private/protected theorem discovery (0 FP)
        self.assertTrue(V.scan_lean_source(self.lean_src + "\nprivate theorem _clean_priv : 1 = 1 := rfl\nprotected theorem _clean_prot : 2 = 2 := rfl\n"))
        priv_decl = self.lean_src.replace("theorem rasm_lift_reversal_criterion", "private theorem rasm_lift_reversal_criterion")
        self.assertTrue(V.scan_lean_source(priv_decl))
        prot_decl = self.lean_src.replace("theorem rasm_lift_reversal_criterion", "protected theorem rasm_lift_reversal_criterion")
        self.assertTrue(V.scan_lean_source(prot_decl))
        missing_thm = self.lean_src.replace("theorem rasm_lift_reversal_criterion", "theorem renamed_thm")
        self._expect_verify_err(lambda: V.scan_lean_source(missing_thm), "LEAN_MISSING_THEOREM")

        ok_lines = []
        for idx, thm in enumerate(O.EXPECTED_LEAN_THEOREMS):
            if idx % 2 == 0:
                ok_lines.append(f"'{thm}' does not depend on any axioms")
            else:
                ok_lines.append(f"'{thm}' depends on axioms: [propext, Quot.sound]")
        self.assertTrue(V._parse_lean_axioms_output("\n" + "\n".join(ok_lines) + "\n"))

        bad_ax = list(ok_lines)
        bad_ax[1] = f"'{O.EXPECTED_LEAN_THEOREMS[1]}' depends on axioms: [Classical.choice]"
        self._expect_verify_err(lambda: V._parse_lean_axioms_output("\n".join(bad_ax)), "LEAN_BANNED_AXIOM")

        bad_fmt = list(ok_lines)
        bad_fmt[1] = f"'{O.EXPECTED_LEAN_THEOREMS[1]}' depends on axioms: [propext"
        self._expect_verify_err(lambda: V._parse_lean_axioms_output("\n".join(bad_fmt)), "LEAN_UNEXPECTED_OUTPUT")
        self._expect_verify_err(lambda: V._parse_lean_axioms_output("bogus line ending with ]"), "LEAN_UNEXPECTED_OUTPUT")

        self._expect_verify_err(lambda: V._parse_lean_axioms_output("\n".join(ok_lines[:-1])), "LEAN_AXIOM_COUNT_MISMATCH")

        self._expect_verify_err(lambda: V.verify_lean_proof(LEAN_PATH, check_pin=1), "INVALID_CHECK_PIN")
        with tempfile.TemporaryDirectory() as td:
            bad_pin = Path(td) / "t.lean"
            bad_pin.write_text(self.lean_src + "\n", encoding="utf-8")
            self._expect_verify_err(lambda: V.verify_lean_proof(bad_pin, check_pin=True), "LEAN_SHA_MISMATCH")
            bad_utf8 = Path(td) / "u.lean"
            bad_utf8.write_bytes(b"\xff\xfe")
            self._expect_verify_err(lambda: V.verify_lean_proof(bad_utf8, check_pin=False), "LEAN_INVALID_UTF8")

        # Scrubbed Lean env allowlist unit test (kills _scrubbed_lean_env mutants in all CI modes!)
        hostile_keys = ("LEAN_PATH", "LEAN_OPTS", "LEAN_SRC_PATH", "LEAN_SYSROOT", "LEAN_CC", "ELAN_TOOLCHAIN", "ELAN_HOME")
        with mock.patch.dict(os.environ, {k: "/hostile" for k in hostile_keys}, clear=False):
            clean_env = V._scrubbed_lean_env()
            for hk in hostile_keys:
                self.assertNotIn(hk, clean_env)
            self.assertIn("PATH", clean_env)
        with mock.patch.dict(os.environ, {"LEAN_PATH": "/hostile"}, clear=True):
            clean_bare = V._scrubbed_lean_env()
            self.assertEqual(clean_bare, {"PATH": "/usr/bin:/bin"})

        # Non-empty stderr & env-scrubbing guard killer (works in both live & Lean-less CI!)
        with mock.patch.dict(os.environ, {"LEAN_PATH": "/hostile", "LEAN_OPTS": "-Ddebug.skipKernelTC=true"}, clear=False):
            with mock.patch("shutil.which", return_value="/usr/bin/true"):
                with mock.patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=b"", stderr=b"warn")) as m_run:
                    self._expect_verify_err(lambda: V.verify_lean_proof(LEAN_PATH, check_pin=True), "LEAN_STDERR_NONEMPTY")
                    passed_env = m_run.call_args.kwargs.get("env")
                    self.assertIsNotNone(passed_env)
                    self.assertNotIn("LEAN_PATH", passed_env)
                    self.assertNotIn("LEAN_OPTS", passed_env)
                with mock.patch("subprocess.run", return_value=SimpleNamespace(returncode=1, stdout=b"", stderr=b"err")):
                    self._expect_verify_err(lambda: V.verify_lean_proof(LEAN_PATH, check_pin=True), "LEAN_COMPILE_FAILED")

        # Live vs Lean-less 0-skip parity (single fast live lean call + live LEAN_PATH Init.olean hijack immunity)
        lean_bin = shutil.which("lean")
        require_lean = os.environ.get("ALETHEIA_REQUIRE_LEAN") == "1"
        if lean_bin is not None:
            self.assertEqual(V.main(["--verify-lean"]), 0)
            with tempfile.TemporaryDirectory() as td_hij:
                hij_dir = Path(td_hij)
                (hij_dir / "Init.lean").write_text(
                    "prelude\ninductive HijackInitProof : Prop where | intro : HijackInitProof\ndef hijackTrivial : HijackInitProof := HijackInitProof.intro\n",
                    encoding="utf-8",
                )
                r_init = subprocess.run(
                    [lean_bin, "-R", str(hij_dir), "-o", str(hij_dir / "Init.olean"), str(hij_dir / "Init.lean")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=V._scrubbed_lean_env(),
                    check=False,
                )
                self.assertEqual(r_init.returncode, 0)
                fake_s92 = hij_dir / "FakeS92.lean"
                fake_body = ["namespace RawArabicHigherOrderMesh"]
                for thm in O.EXPECTED_LEAN_THEOREMS:
                    fake_body.append(f"theorem {thm.split('.')[-1]} : HijackInitProof := hijackTrivial")
                fake_body.append("end RawArabicHigherOrderMesh\n")
                fake_s92.write_text("\n".join(fake_body), encoding="utf-8")
                with mock.patch.dict(os.environ, {"LEAN_PATH": str(hij_dir)}, clear=False):
                    # Real pinned proof still passes despite hostile LEAN_PATH; hijacked fake fails closed!
                    self.assertTrue(V.verify_lean_proof(LEAN_PATH, check_pin=True))
                    self._expect_verify_err(lambda: V.verify_lean_proof(fake_s92, check_pin=False), "LEAN_COMPILE_FAILED")
            old_path = os.environ.get("PATH", "")
            try:
                os.environ["PATH"] = "/usr/bin:/bin"
                if shutil.which("lean") is None:
                    self._expect_verify_err(
                        lambda: V.verify_lean_proof(LEAN_PATH, check_pin=True),
                        "LEAN_BINARY_NOT_FOUND",
                    )
            finally:
                os.environ["PATH"] = old_path
        else:
            self.assertFalse(require_lean, "ALETHEIA_REQUIRE_LEAN=1 set but lean binary absent")
            self._expect_verify_err(lambda: V.verify_lean_proof(LEAN_PATH, check_pin=True), "LEAN_BINARY_NOT_FOUND")
            self.assertEqual(V.main(["--verify-lean"]), 2)

    # ------------------------------------------------------------------
    # 7. Synthetic Standalone Primary-Dataset SHA Verification (26 Files)
    # ------------------------------------------------------------------
    def test_07_verify_datasets_on_disk_synthetic(self):
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            h_root = tdp / "heritage"
            b_root = tdp / "bayt"
            a_syn = copy.deepcopy(self.anchor)

            for idx, t in enumerate(a_syn["treatises"]):
                rel = f"t_{idx}.txt"
                data = f"treatise_{idx}".encode("utf-8")
                (h_root / rel).parent.mkdir(parents=True, exist_ok=True)
                (h_root / rel).write_bytes(data)
                t["rel_path"] = rel
                t["bytes"] = len(data)
                t["sha256"] = hashlib.sha256(data).hexdigest()

            bp = a_syn["bayt_prior_art"]
            for idx, (rk, sk, hk) in enumerate((
                ("continuum_cert_rel", "continuum_cert_bytes", "continuum_cert_file_sha256"),
                ("lexicon_cert_rel", "lexicon_cert_bytes", "lexicon_cert_file_sha256"),
            )):
                rel = f"b_{idx}.json"
                data = f'{{"b":{idx}}}'.encode("utf-8")
                (b_root / rel).parent.mkdir(parents=True, exist_ok=True)
                (b_root / rel).write_bytes(data)
                bp[rk] = rel
                bp[sk] = len(data)
                bp[hk] = hashlib.sha256(data).hexdigest()

            for idx, cat in enumerate(a_syn["bilingual_scientific_catalogs"]["catalog_pins"]):
                rel = f"c_{idx}.jsonl"
                data = f'{{"c":{idx}}}\n'.encode("utf-8")
                (h_root / rel).parent.mkdir(parents=True, exist_ok=True)
                (h_root / rel).write_bytes(data)
                cat["rel_path"] = rel
                cat["bytes"] = len(data)
                cat["sha256"] = hashlib.sha256(data).hexdigest()

            a_path = tdp / "syn_anchor.json"
            a_path.write_bytes(V.canonical_json_bytes(_resign_anchor(a_syn)))

            # strict check_anchor_pin default fails closed on synthetic/forged anchor!
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=1), "INVALID_CHECK_ANCHOR_PIN")
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path), "ANCHOR_FILE_SHA_MISMATCH")
            list_a = tdp / "list_anchor.json"
            list_a.write_bytes(b"[]")
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=list_a, check_anchor_pin=False), "ANCHOR_NOT_DICT")
            nosha_a = tdp / "nosha_anchor.json"
            nosha_a.write_bytes(b"{}")
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=nosha_a, check_anchor_pin=False), "ANCHOR_MISSING_SHA")
            badsha_a = copy.deepcopy(a_syn)
            badsha_a["anchor_sha256"] = "0" * 64
            badsha_p = tdp / "badsha_anchor.json"
            badsha_p.write_bytes(V.canonical_json_bytes(badsha_a))
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=badsha_p, check_anchor_pin=False), "ANCHOR_INTERNAL_SHA_MISMATCH")

            self.assertEqual(V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=False), 26)

            (h_root / "t_0.txt").write_bytes(b"Xreatise_0")
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=False), "DATASET_SHA_MISMATCH")
            (h_root / "t_0.txt").write_bytes(b"short")
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=False), "DATASET_SIZE_MISMATCH")
            (h_root / "t_0.txt").write_bytes(b"treatise_0")

            (b_root / "b_0.json").write_bytes(b'{"b":9}')
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=False), "BAYT_SHA_MISMATCH")
            (b_root / "b_0.json").write_bytes(b"{}")
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=False), "BAYT_SIZE_MISMATCH")
            (b_root / "b_0.json").write_bytes(b'{"b":0}')

            (h_root / "c_0.jsonl").write_bytes(b'{"c":9}\n')
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=False), "CATALOG_SHA_MISMATCH")
            (h_root / "c_0.jsonl").write_bytes(b"{}\n")
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_path, check_anchor_pin=False), "CATALOG_SIZE_MISMATCH")
            (h_root / "c_0.jsonl").write_bytes(b'{"c":0}\n')

            a_short = copy.deepcopy(a_syn)
            a_short["bilingual_scientific_catalogs"]["catalog_pins"].pop()
            a_short_p = tdp / "syn_short.json"
            a_short_p.write_bytes(V.canonical_json_bytes(_resign_anchor(a_short)))
            self._expect_verify_err(lambda: V.verify_datasets_on_disk(h_root, b_root, anchor_path=a_short_p, check_anchor_pin=False), "DATASET_COUNT_MISMATCH")


if __name__ == "__main__":
    unittest.main(verbosity=2)
