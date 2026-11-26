#!/usr/bin/env python3
"""
Deterministic Negative-Control & Certificate-Binding Test Suite for
`S150Pilot1Theorems` (`verify_s150_lean_theorems.py` & `s150_lean_theorems_certificate.json`).

Pure Python 3 standard library. Zero floats in AST, zero bare asserts, zero test skips.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
PKG_DIR = Path(__file__).resolve().parent
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))
import verify_s150_lean_theorems as vmod


def _rehash_cert(cert_dict: dict[str, object]) -> dict[str, object]:
    body = {k: v for k, v in cert_dict.items() if k != "payload_sha256"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    out = dict(body)
    out["payload_sha256"] = hashlib.sha256(canon).hexdigest()
    return out


class TestS150LeanTheoremsCert(unittest.TestCase):
    def test_01_pure_q_ast_guard_and_qdiv_controls(self) -> None:
        self.assertEqual(vmod.qdiv(Fraction(3, 5), Fraction(9, 10)), Fraction(2, 3))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^QDIV_ZERO_DENOM:"):
            vmod.qdiv(Fraction(1), Fraction(0))

        good_src = (
            "from fractions import Fraction\n"
            "import math\n"
            "from math import gcd, isqrt\n"
            "k = 2\n"
            "x = Fraction(3, 5) * Fraction(-2) * Fraction(+1, 1 << 3) * Fraction(1, 1 << k)\n"
            "p = (2 ** 9) + (1 << 4)\n"
            "y = Fraction(x.numerator * 2 + 1 - 0, x.denominator)\n"
            "g = math.gcd(6, 9) + isqrt(16) + gcd(4, 8)\n"
        )
        res_ast = vmod.verify_pure_q_ast(good_src)
        self.assertTrue(res_ast["pure_q_ast_clean"])

        bad_snippets = (
            ("def (\n", r"^AST_SYNTAX_ERROR:"),
            ("assert True\n", r"^AST_BARE_ASSERT:"),
            ("x = 1 / 2\n", r"^AST_DIV_FORBIDDEN:"),
            ("x = 1 // 2\n", r"^AST_FLOORDIV_FORBIDDEN:"),
            ("x = 2 ** -1\n", r"^AST_POW_EXP_FORBIDDEN:"),
            ("x = 2 ** (-2)\n", r"^AST_POW_EXP_FORBIDDEN:"),
            ("k = 3\nx = 2 ** k\n", r"^AST_POW_EXP_FORBIDDEN:"),
            ("x = 2 ** True\n", r"^AST_POW_EXP_FORBIDDEN:"),
            ("x = f'{1:.3f}'\n", r"^AST_FORMAT_SPEC_FORBIDDEN:"),
            ("x = 0.25\n", r"^AST_FLOAT_LITERAL:"),
            (f"x = {chr(49)}{chr(106)}\n", r"^AST_FLOAT_LITERAL:"),
            ("f = float\nx = f(1)\n", r"^AST_FORBIDDEN_NAME:"),
            ("x = float(1)\n", r"^AST_FLOAT_CALL:"),
            ("x = Decimal(1)\n", r"^AST_FLOAT_CALL:"),
            ("x = mod.Decimal(1)\n", r"^AST_FLOAT_CALL:"),
            ("x = getattr(obj, 'a')\n", r"^AST_FLOAT_CALL:"),
            ("x = eval('1')\n", r"^AST_FLOAT_CALL:"),
            ("x = pow(2, -1)\n", r"^AST_FLOAT_CALL:"),
            ("x = __builtins__['float']\n", r"^AST_FORBIDDEN_NAME:"),
            ("x = __builtins__['float']('1')\n", r"^AST_INDIRECT_CALL:"),
            ("from fractions import Fraction\nx = '%.2f' % Fraction(1, 3)\n", r"^AST_MOD_FORBIDDEN:"),
            ("import fractions\nx = fractions.__dict__\n", r"^AST_FROM_FLOAT_FORBIDDEN:"),
            ("import fractions\nx = fractions.__dict__['Fraction']('0.5')\n", r"^AST_INDIRECT_CALL:"),
            ("from fractions import Fraction\nx = '{:.2f}'.format(Fraction(1, 3))\n", r"^AST_FLOAT_CALL:"),
            ("from fractions import Fraction\nx = format(Fraction(1, 3), '.2f')\n", r"^AST_FLOAT_CALL:"),
            ("from fractions import Fraction\nx = type(Fraction(1, 1))('1.5')\n", r"^AST_INDIRECT_CALL:"),
            ("from fractions import Fraction\nlst = [Fraction]\n", r"^AST_FRACTION_CONTAINER:"),
            ("x = (1).__truediv__(2)\n", r"^AST_FROM_FLOAT_FORBIDDEN:"),
            ("import sys\nm = sys.modules['math']\n", r"^AST_FROM_FLOAT_FORBIDDEN:"),
            ("from . import foo\n", r"^AST_REL_IMPORT_FORBIDDEN:"),
            ("import builtins\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("import operator\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("import importlib\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("from fractions import Fraction\ny = Fraction.from_float(1)\n", r"^AST_FROM_FLOAT_FORBIDDEN:"),
            ("from fractions import Fraction\ny = Fraction.from_decimal(1)\n", r"^AST_FROM_FLOAT_FORBIDDEN:"),
            ("import decimal\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("import sympy\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("import mpmath\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("import numpy as np\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("from decimal import Decimal\n", r"^AST_FORBIDDEN_IMPORT:"),
            ("from math import *\n", r"^AST_WILDCARD_IMPORT:"),
            ("from math import cos\n", r"^AST_FORBIDDEN_MATH_SYM:"),
            ("from fractions import gcd\n", r"^AST_FORBIDDEN_FRACTIONS_SYM:"),
            ("import math\nx = math.sin(0)\n", r"^AST_FORBIDDEN_MATH_ATTR:"),
            ("import math as m\nx = m.log(2)\n", r"^AST_FORBIDDEN_MATH_ATTR:"),
            ("import math\nM = math\nx = M.sqrt(2)\n", r"^AST_FORBIDDEN_MATH_ATTR:"),
            ("import math\nM: object = math\nx = M.sqrt(2)\n", r"^AST_FORBIDDEN_MATH_ATTR:"),
            ("import math\n(M := math)\nx = M.sqrt(2)\n", r"^AST_FORBIDDEN_MATH_ATTR:"),
            ("from fractions import Fraction\nx = Fraction('1/2')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nF = Fraction\nG = F\nx = G('0.5')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("import fractions\nF = fractions.Fraction\nx = F('0.5')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("import fractions\nF: object = fractions.Fraction\nx = F('0.5')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = (F := Fraction)('0.5')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("import fractions\nx = (F := fractions.Fraction)('0.5')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction as F\nx = F('1/2')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("import fractions as fr\nx = fr.Fraction('1/2')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\ns = '1/2'\nx = Fraction(s)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(~1)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(y.real)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(1 + s)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(s + 1)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(True, 2)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(-True, 2)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(s << 1)\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction(1 << 'a')\n", r"^AST_FRACTION_ARG_UNSAFE:"),
            ("from fractions import Fraction\nx = Fraction()\n", r"^AST_FRACTION_ARITY:"),
            ("from fractions import Fraction\nx = Fraction(1, 2, 3)\n", r"^AST_FRACTION_ARITY:"),
            ("from fractions import Fraction\nx = Fraction(numerator=1)\n", r"^AST_FRACTION_KW:"),
        )
        for snippet, pat in bad_snippets:
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, pat, msg=snippet):
                vmod.verify_pure_q_ast(snippet)

    def test_02_topic1_topic2_topic3_negative_controls(self) -> None:
        r1 = vmod.verify_topic1_fricke_cayley_q()
        self.assertEqual(r1["definite_witnesses"], 3)
        self.assertEqual(r1["split_cf_witnesses"], 4)

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_DEFINITE_D_MISMATCH:"):
            vmod.verify_topic1_fricke_cayley_q(definite_cases=(((5, 3, 1, 1), (13, 5, 1, 1), 99, 7048, 440),))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_DEFINITE_KAPPA_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(fricke_fn=lambda _a, _b, _x, _y, _z: 0)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_GROUP_COMM_REC_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(definite_cases=(((5, 3, 1, 1), (13, 5, 1, 1), 1, 7048, 999),))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_FROB_CLEARED_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(frob_cleared_fn=lambda _ab, _d: 99)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_PARITY_MOD16_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(
                definite_cases=(((5, 3, 1, 1), (13, 5, 1, 1), 1, 7049, 440),),
                frob_cleared_fn=lambda _ab, _d: 7049,
            )
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_SPLIT_KAPPA_MISMATCH:"):
            vmod.verify_topic1_fricke_cayley_q(split_cases=(((1, 1, 2), -999, 144, False),))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_PALINDROME_IFF_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(split_cases=(((1, 1, 2), -41, 144, True),))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_OVERSHOOT_LAW_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(overshoot_fn=lambda _s, _t: 999)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_OVERSHOOT_VAL_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(split_cases=(((1, 1, 2), -41, 999, False),))

        f_cnt = {"n": 0}

        def _bad_split_fricke(a: int, b: int, x: int, y: int, z: int) -> int:
            f_cnt["n"] += 1
            val = vmod.fricke_disc_z(a, b, x, y, z)
            return val + 1 if f_cnt["n"] == 4 else val

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T1_SPLIT_FACTOR_FAIL:"):
            vmod.verify_topic1_fricke_cayley_q(fricke_fn=_bad_split_fricke)

        r2 = vmod.verify_topic2_valve_khipu_q()
        self.assertEqual(r2["seminar_roots"], [15, 13, 123])

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T2_FLIPS_MISMATCH:"):
            vmod.verify_topic2_valve_khipu_q(valve_eval_fn=lambda _lo, _hi, _init, _st: (99, Fraction(6)))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T2_TV_MISMATCH:"):
            vmod.verify_topic2_valve_khipu_q(valve_eval_fn=lambda _lo, _hi, _init, _st: (2, Fraction(999)))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T2_TV_BOUND_FAIL:"):
            vmod.verify_topic2_valve_khipu_q(
                witness_streams=((Fraction(0), Fraction(4), 0, (), 3, Fraction(7), (5,), 5),),
                valve_eval_fn=lambda _lo, _hi, _init, _st: (3, Fraction(7)),
            )
        # Boundary equality (flips - 1)*(hi - lo) == tv must PASS (kills <= -> < mutant!)
        res_tight_tv = vmod.verify_topic2_valve_khipu_q(
            witness_streams=((Fraction(0), Fraction(4), 0, (), 3, Fraction(8), (5,), 5),),
            valve_eval_fn=lambda _lo, _hi, _init, _st: (3, Fraction(8)),
        )
        self.assertEqual(res_tight_tv["valve_streams_verified"], 1)

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T2_CHIRAL_ROOT_MISMATCH:"):
            vmod.verify_topic2_valve_khipu_q(chiral_fn=lambda _lv: 0)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T2_CHIRAL_SWAP_BLIND:"):
            vmod.verify_topic2_valve_khipu_q(
                chiral_fn=lambda lv: vmod._chiral_root(lv) if lv not in ((3, 2), (2, 3)) else 7
            )
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T2_CRT_INCONSISTENT_MISSED:"):
            vmod.verify_topic2_valve_khipu_q(crt_pair=(6, 10, 3, 5))

        r3 = vmod.verify_topic3_schur_witt_fold_q()
        self.assertEqual(r3["mirror_billiard_2_3_period"], 24)
        self.assertFalse(vmod._is_q_square(Fraction(0)))
        self.assertFalse(vmod._is_q_square(Fraction(-4)))
        self.assertFalse(vmod._is_q_square(Fraction(4, 3)))
        self.assertFalse(vmod._is_q_square(Fraction(3, 4)))
        self.assertTrue(vmod._is_q_square(Fraction(9, 16)))

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_SQRT2_OBSTRUCTION_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(q_square_fn=lambda _v: True)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_3334_WITNESS_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(q_square_fn=lambda _v: False)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_CONVERSE_CEX_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(converse_triple=(4, 4, 4))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_CONVERSE_CEX_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(converse_triple=(4, 1, 1))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_GF2_PARITY_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(gf2_pair=(2, 4))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_GF2_PARITY_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(gf2_pair=(3, 3))
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_BILLIARD_23_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(billiard_period_fn=lambda _p, _q: 12)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^T3_BILLIARD_23_FAIL:"):
            vmod.verify_topic3_schur_witt_fold_q(billiard_pair=(2, 4), billiard_period_fn=lambda _p, _q: 24)

    def test_03_lean_char_lexer_and_axiom_validator_controls(self) -> None:
        cleaned = vmod.strip_lean_comments_and_strings(
            "-- sorry in line comment\n/- nested /- bv_decide -/ comment -/\ndef s := \"quote \\\" sorry\"\ndef xr\"sorry\" := 1\n"
        )
        self.assertNotIn("sorry", cleaned)
        self.assertNotIn("bv_decide", cleaned)
        sub_cleaned = vmod.strip_lean_comments_and_strings("theorem t : 2 - 1 = 1 := by bv_decide\n")
        self.assertIn("bv_decide", sub_cleaned)

        char_desync_payloads = (
            "def x := '\"'\ntheorem cheat : 1 = 2 := by sorry\ndef y := '\"'\n",
            "def x := '\\\"'\ntheorem cheat : 1 = 2 := by sorry\ndef y := '\\''\n",
            "def x := '\\x22'\ntheorem cheat : 1 = 2 := by sorry\ndef y := '\\u0022'\n",
            "theorem t' (x' : Nat) : x' = x' := by sorry\n",
            'def raw := r#"sorry"#\n',
        )
        for payload in char_desync_payloads:
            sc = vmod.strip_lean_comments_and_strings(payload)
            self.assertIsNotNone(vmod._FORBIDDEN_LEAN_CODE_RE.search(sc), msg=payload)

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^UNTERMINATED_BLOCK_COMMENT:"):
            vmod.strip_lean_comments_and_strings("/- open comment")
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^UNTERMINATED_STRING_LITERAL:"):
            vmod.strip_lean_comments_and_strings('def x := "open')
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^UNTERMINATED_STRING_LITERAL:"):
            vmod.strip_lean_comments_and_strings("def x' := \"open")
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^UNTERMINATED_STRING_LITERAL:"):
            vmod.strip_lean_comments_and_strings('def p := \'\\"x"ok"\n')
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^UNTERMINATED_STRING_LITERAL:"):
            vmod.strip_lean_comments_and_strings('def raw := r#"open\n')

        good_lines = [
            "'A.t0' does not depend on any axioms",
            "'A.t1' depends on axioms: [propext]",
            "'A.t2' depends on axioms: [propext, Quot.sound]",
        ]
        counts = vmod.validate_axiom_audit_lines(good_lines, 3)
        self.assertEqual(counts["zero_axiom_theorems"], 1)
        self.assertEqual(counts["propext_only_theorems"], 1)
        self.assertEqual(counts["propext_quot_theorems"], 1)

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^AXIOM_LINE_COUNT_FAIL:"):
            vmod.validate_axiom_audit_lines(good_lines, 4)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^UNRECOGNIZED_AXIOM_LINE:"):
            vmod.validate_axiom_audit_lines(["garbage line"], 1)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^MALFORMED_AXIOM_LBRACKET:"):
            vmod.validate_axiom_audit_lines(["'A.t' depends on axioms: propext]"], 1)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^MALFORMED_AXIOM_RBRACKET:"):
            vmod.validate_axiom_audit_lines(["'A.t' depends on axioms: [propext"], 1)
        for banned_ax in ("Classical.choice", "Foo._native.bv_decide.ax_1", "sorryAx", "Lean.ofReduceBool", "Lean.trustCompiler"):
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^BANNED_AXIOM:"):
                vmod.validate_axiom_audit_lines([f"'A.t' depends on axioms: [propext, {banned_ax}]"], 1)
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^FORBIDDEN_AXIOM:"):
            vmod.validate_axiom_audit_lines(["'A.t' depends on axioms: [propext, customAx]"], 1)

    def test_04_on_disk_certificate_self_binding_and_tamper_controls(self) -> None:
        cert_path = Path(PKG_DIR, "s150_lean_theorems_certificate.json")
        self.assertTrue(cert_path.is_file(), msg="Committed s150_lean_theorems_certificate.json missing on disk")
        on_disk_cert = json.loads(cert_path.read_text(encoding="utf-8"))

        check_res = vmod.validate_certificate(on_disk_cert, pkg_dir=PKG_DIR)
        self.assertEqual(check_res["status"], "PASS")
        self.assertFalse(check_res["lean_live_replayed"])
        self.assertEqual(check_res["verification_mode"], "offline_static_and_pure_q")
        self.assertEqual(check_res["public_theorems_verified"], 36)

        buf_check = io.StringIO()
        with patch("sys.stdout", buf_check):
            rc_check = vmod.main(["--check"])
        self.assertEqual(rc_check, 0)
        parsed_check = json.loads(buf_check.getvalue())
        self.assertFalse(parsed_check["lean_live_replayed"])
        self.assertEqual(parsed_check["payload_sha256"], on_disk_cert["payload_sha256"])

        buf_json = io.StringIO()
        with patch("sys.stdout", buf_json):
            rc_json = vmod.main(["--json"])
        self.assertEqual(rc_json, 0)
        offline_cert = json.loads(buf_json.getvalue())
        self.assertFalse(offline_cert["lean_verification"]["live_lean_verified"])
        self.assertTrue(on_disk_cert["lean_verification"]["live_lean_verified"])
        self.assertNotEqual(offline_cert["payload_sha256"], on_disk_cert["payload_sha256"])

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_NOT_LIVE_BUILT:"):
            vmod.validate_certificate(offline_cert, pkg_dir=PKG_DIR)
        bad_lv = copy.deepcopy(on_disk_cert)
        bad_lv["lean_verification"] = "bad"
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_NOT_LIVE_BUILT:"):
            vmod.validate_certificate(_rehash_cert(bad_lv), pkg_dir=PKG_DIR)

        err_w = io.StringIO()
        with patch("sys.stderr", err_w):
            self.assertEqual(vmod.main(["--write-cert"]), 2)
        self.assertEqual(json.loads(err_w.getvalue())["error_code"], "WRITE_CERT_REQUIRES_LIVE_LEAN")

        err_m = io.StringIO()
        with patch("sys.stderr", err_m):
            self.assertEqual(vmod.main(["--check", str(Path(PKG_DIR, "nonexistent_cert.json"))]), 2)
        self.assertEqual(json.loads(err_m.getvalue())["error_code"], "MISSING_CERT_FILE")

        with tempfile.TemporaryDirectory() as td_c:
            dup_p = Path(td_c, "dup.json")
            dup_p.write_text('{"module": "A", "module": "B"}\n', encoding="utf-8")
            err_d = io.StringIO()
            with patch("sys.stderr", err_d):
                self.assertEqual(vmod.main(["--check", str(dup_p)]), 2)
            self.assertEqual(json.loads(err_d.getvalue())["error_code"], "CERT_DUPLICATE_KEY")

            noncanon_p = Path(td_c, "noncanon.json")
            noncanon_p.write_bytes(cert_path.read_bytes().replace(b"\n", b"\r\n"))
            err_nc = io.StringIO()
            with patch("sys.stderr", err_nc):
                self.assertEqual(vmod.main(["--check", str(noncanon_p)]), 2)
            self.assertEqual(json.loads(err_nc.getvalue())["error_code"], "CERT_RAW_FORMAT_DRIFT")

            sym_p = Path(td_c, "sym_cert.json")
            sym_p.symlink_to(cert_path)
            err_sym = io.StringIO()
            with patch("sys.stderr", err_sym):
                self.assertEqual(vmod.main(["--check", str(sym_p)]), 2)
            self.assertEqual(json.loads(err_sym.getvalue())["error_code"], "SYMLINK_FORBIDDEN")

            big_p = Path(td_c, "big4400.json")
            big_p.write_text('{"x":' + "9" * 4400 + "}\n", encoding="utf-8")
            err_big = io.StringIO()
            with patch("sys.stderr", err_big):
                self.assertEqual(vmod.main(["--check", str(big_p)]), 2)
            self.assertEqual(json.loads(err_big.getvalue())["error_code"], "CERT_INT_TOO_LARGE")
            self.assertEqual(vmod._parse_bounded_int("9" * vmod.MAX_JSON_INT_DIGITS), int("9" * vmod.MAX_JSON_INT_DIGITS))

            # Grandparent symlink, FIFO, size cap, ELOOP, & os.read OSError coverage
            real_gp = Path(td_c, "real_gp")
            Path(real_gp, "sub").mkdir(parents=True)
            Path(real_gp, "sub", "c.json").write_bytes(cert_path.read_bytes())
            gp_sym = Path(td_c, "gp_sym")
            gp_sym.symlink_to(real_gp)
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SYMLINK_FORBIDDEN:"):
                vmod.read_regular_file_bytes(Path(gp_sym, "sub", "c.json"))
            fifo_p = Path(td_c, "pipe.json")
            vmod.os.mkfifo(fifo_p)
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^NOT_REGULAR_FILE:"):
                vmod.read_regular_file_bytes(fifo_p)
            small_p = Path(td_c, "small.json")
            small_p.write_bytes(b"{" + b" " * 100 + b"}")
            self.assertEqual(len(vmod.read_regular_file_bytes(small_p, max_bytes=102)), 102)
            with patch.object(vmod.os, "read", side_effect=AssertionError("st_size must reject before read")):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^FILE_TOO_LARGE:"):
                    vmod.read_regular_file_bytes(small_p, max_bytes=64)
            fake_st = vmod.os.stat(small_p)
            with patch.object(vmod.os, "fstat", return_value=type("S", (), {"st_mode": fake_st.st_mode, "st_size": 10})()):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^FILE_TOO_LARGE:"):
                    vmod.read_regular_file_bytes(small_p, max_bytes=64)
            with patch.object(vmod.os, "open", side_effect=OSError(vmod.errno.ELOOP, "loop")):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SYMLINK_FORBIDDEN:"):
                    vmod.read_regular_file_bytes(small_p)
            with patch.object(vmod.os, "open", side_effect=OSError(vmod.errno.EACCES, "denied")):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^READ_ERROR:"):
                    vmod.read_regular_file_bytes(small_p)
            with patch.object(vmod.os, "read", side_effect=OSError(vmod.errno.EIO, "io error")):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^READ_ERROR:"):
                    vmod.read_regular_file_bytes(small_p)

            for raw_bad, exp_code in (
                (b"\xff\xfe", "CERT_INVALID_JSON"),
                (b"{bad", "CERT_INVALID_JSON"),
                (b'{"a":1.5}', "CERT_FORBIDDEN_JSON_NUM"),
                (b'{"a":NaN}', "CERT_FORBIDDEN_JSON_NUM"),
            ):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, rf"^{exp_code}:"):
                    vmod.loads_strict_json_bytes(raw_bad, "t")

            self.assertEqual(vmod.MAX_JSON_DEPTH, 32)
            deep32 = b"[" * vmod.MAX_JSON_DEPTH + b"1" + b"]" * vmod.MAX_JSON_DEPTH
            self.assertIsInstance(vmod.loads_strict_json_bytes(deep32, "ok32"), list)
            str_braces = b'{"s":"' + b"{" * 40 + b'\\"{[\\\\"}'
            self.assertEqual(vmod.loads_strict_json_bytes(str_braces, "braces")["s"][:2], "{{")
            with patch.object(vmod.json, "loads", side_effect=AssertionError("pre-parse depth check must reject before json.loads")):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_JSON_DEPTH:"):
                    vmod.loads_strict_json_bytes(b"[" * (vmod.MAX_JSON_DEPTH + 1) + b"1" + b"]" * (vmod.MAX_JSON_DEPTH + 1), "d33")
            with patch.object(vmod.json, "loads", side_effect=RecursionError("deep")):
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_JSON_DEPTH:"):
                    vmod.loads_strict_json_bytes(b'{"a":1}', "rec")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^BAD_UTF8:"):
                vmod._decode_utf8(b"\xff\xfe", "bad")

            sym_script = Path(td_c, "sym_lean_verifier.py")
            sym_script.symlink_to(Path(PKG_DIR, "verify_s150_lean_theorems.py"))
            proc_sym = subprocess.run(
                [sys.executable, "-I", "-B", str(sym_script), "--check"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc_sym.returncode, 2)
            self.assertNotIn("Traceback", proc_sym.stderr)
            self.assertEqual(json.loads(proc_sym.stderr)["error_code"], "SYMLINK_FORBIDDEN")

        with patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                vmod.main(["--check", "--json"])

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_NOT_OBJECT:"):
            vmod.validate_certificate(["not", "a", "dict"], pkg_dir=PKG_DIR)
        for bad_hex in (None, 123, "abc", "Z" * 64, "a" * 63):
            bad_c = dict(on_disk_cert)
            bad_c["payload_sha256"] = bad_hex
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_BAD_PAYLOAD_HEX64:"):
                vmod.validate_certificate(bad_c, pkg_dir=PKG_DIR)

        bad_self = dict(on_disk_cert)
        bad_self["payload_sha256"] = "0" * 64
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_SELF_HASH_MISMATCH:"):
            vmod.validate_certificate(bad_self, pkg_dir=PKG_DIR)

        no_src = _rehash_cert({k: v for k, v in on_disk_cert.items() if k != "source_files_sha256"})
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_MISSING_SOURCE_MAP:"):
            vmod.validate_certificate(no_src, pkg_dir=PKG_DIR)

        extra_src = copy.deepcopy(on_disk_cert)
        extra_src["source_files_sha256"]["extra.lean"] = "a" * 64
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_SOURCE_KEYS_MISMATCH:"):
            vmod.validate_certificate(_rehash_cert(extra_src), pkg_dir=PKG_DIR)

        for bad_fhex in (123, "abc"):
            bad_file_hex = copy.deepcopy(on_disk_cert)
            bad_file_hex["source_files_sha256"]["S150Pilot1Theorems.lean"] = bad_fhex
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERT_BAD_FILE_HEX64:"):
                vmod.validate_certificate(_rehash_cert(bad_file_hex), pkg_dir=PKG_DIR)

        wrong_file_sha = copy.deepcopy(on_disk_cert)
        wrong_file_sha["source_files_sha256"]["S150Pilot1Theorems.lean"] = "f" * 64
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SOURCE_SHA256_MISMATCH:"):
            vmod.validate_certificate(_rehash_cert(wrong_file_sha), pkg_dir=PKG_DIR)

        forged_witness = copy.deepcopy(on_disk_cert)
        forged_witness["topic3_schur_witt_fold"]["mirror_billiard_2_3_period"] = 12
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERTIFICATE_DRIFT:"):
            vmod.validate_certificate(_rehash_cert(forged_witness), pkg_dir=PKG_DIR)

    def test_05_lean_package_sandbox_manifest_and_negative_controls(self) -> None:
        ax_stdout = "\n".join(vmod.EXPECTED_AXIOM_AUDIT_LINES) + "\n"

        def _ok_runner(_p: Path, snap: object = None) -> dict[str, object]:
            _ = snap
            return {
                "manifest_present": True,
                "manifest_unchanged": True,
                "config_unchanged": True,
                "build_rc": 0,
                "build_output": "Build completed successfully.",
                "leanchecker_rc": 0,
                "leanchecker_output": "",
                "axiom_rc": 0,
                "axiom_stdout": ax_stdout,
            }

        on_disk_cert = json.loads(Path(PKG_DIR, "s150_lean_theorems_certificate.json").read_text(encoding="utf-8"))
        live_check = vmod.validate_certificate(on_disk_cert, pkg_dir=PKG_DIR, run_live_lean=False, lean_runner=_ok_runner)
        self.assertTrue(live_check["lean_live_replayed"])
        self.assertEqual(live_check["verification_mode"], "live_lean_kernel_and_pure_q")

        live_drift = copy.deepcopy(on_disk_cert)
        live_drift["topic3_schur_witt_fold"]["mirror_billiard_2_3_period"] = 12
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^CERTIFICATE_DRIFT:"):
            vmod.validate_certificate(_rehash_cert(live_drift), pkg_dir=PKG_DIR, run_live_lean=False, lean_runner=_ok_runner)

        with patch.object(vmod.subprocess, "run", side_effect=subprocess.TimeoutExpired(["lake"], 10)):
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LEAN_TIMEOUT:"):
                vmod.default_live_lean_runner(PKG_DIR)

        with patch.object(vmod.subprocess, "run", side_effect=FileNotFoundError("No such file: 'lake'")):
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LEAN_EXEC_ERROR:"):
                vmod.default_live_lean_runner(PKG_DIR)
            err_lake = io.StringIO()
            with patch("sys.stderr", err_lake):
                self.assertEqual(vmod.main(["--live-lean", "--json"]), 2)
            self.assertEqual(json.loads(err_lake.getvalue())["error_code"], "LEAN_EXEC_ERROR")

        with patch.object(vmod.subprocess, "run", side_effect=UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad utf8")):
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LEAN_OUTPUT_BAD_UTF8:"):
                vmod.default_live_lean_runner(PKG_DIR)
            err_u = io.StringIO()
            with patch("sys.stderr", err_u):
                self.assertEqual(vmod.main(["--live-lean", "--json"]), 2)
            self.assertEqual(json.loads(err_u.getvalue())["error_code"], "LEAN_OUTPUT_BAD_UTF8")

        with patch.object(vmod, "default_live_lean_runner", _ok_runner):
            err_io_w = io.StringIO()
            with patch("sys.stderr", err_io_w):
                self.assertEqual(vmod.main(["--live-lean", "--write-cert", str(Path(PKG_DIR, "nonexistent_dir_xyz", "c.json"))]), 2)
            self.assertEqual(json.loads(err_io_w.getvalue())["error_code"], "IO_ERROR")

        observed_files: list[str] = []

        def _fake_subproc_run(cmd: list[str], cwd: Path, **kwargs: object) -> subprocess.CompletedProcess[str]:
            _ = kwargs
            if cmd[:2] == ["lake", "build"]:
                observed_files.extend(sorted(str(p.relative_to(cwd)).replace("\\", "/") for p in cwd.rglob("*") if p.is_file()))
                return subprocess.CompletedProcess(cmd, 0, stdout="Build completed.", stderr="")
            if "leanchecker" in cmd:
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            return subprocess.CompletedProcess(cmd, 0, stdout=ax_stdout, stderr="")

        with patch.object(vmod.subprocess, "run", side_effect=_fake_subproc_run):
            res_sandbox = vmod.default_live_lean_runner(PKG_DIR)
        self.assertIn("lake-manifest.json", observed_files)
        self.assertEqual(observed_files, sorted(vmod.BOUND_PACKAGE_FILES))
        self.assertTrue(res_sandbox["manifest_unchanged"])
        self.assertTrue(res_sandbox["config_unchanged"])

        for mutate_file in ("lakefile.toml", "lean-toolchain"):
            def _mutating_run(cmd: list[str], cwd: Path, mf: str = mutate_file, **kwargs: object) -> subprocess.CompletedProcess[str]:
                _ = kwargs
                if cmd[:2] == ["lake", "build"]:
                    Path(cwd, mf).write_text("tampered\n", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, stdout=ax_stdout if "lean" in cmd else "", stderr="")
            with patch.object(vmod.subprocess, "run", side_effect=_mutating_run):
                self.assertFalse(vmod.default_live_lean_runner(PKG_DIR)["config_unchanged"])

        with patch.object(vmod, "default_live_lean_runner", _ok_runner):
            with tempfile.TemporaryDirectory() as td_w:
                out_cert_tmp = Path(td_w, "s150_test_write_cert.json")
                with patch("sys.stdout", io.StringIO()):
                    rc_w = vmod.main(["--live-lean", "--write-cert", str(out_cert_tmp)])
                self.assertEqual(rc_w, 0)
                self.assertTrue(out_cert_tmp.is_file())
                sym_w = Path(td_w, "sym_out.json")
                sym_w.symlink_to(out_cert_tmp)
                err_sw = io.StringIO()
                with patch("sys.stderr", err_sw):
                    self.assertEqual(vmod.main(["--live-lean", "--write-cert", str(sym_w)]), 2)
                self.assertEqual(json.loads(err_sw.getvalue())["error_code"], "SYMLINK_FORBIDDEN")

        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^MISSING_SANDBOX_MANIFEST:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {k: v for k, v in _ok_runner(p).items() if k != "manifest_present"})
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SANDBOX_MANIFEST_MUTATED:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {k: v for k, v in _ok_runner(p).items() if k != "manifest_unchanged"})
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SANDBOX_CONFIG_MUTATED:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {k: v for k, v in _ok_runner(p).items() if k != "config_unchanged"})
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LAKE_BUILD_FAIL:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {**_ok_runner(p), "build_rc": 1})
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LAKE_BUILD_WARNING:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {**_ok_runner(p), "build_output": "Warning: unused"})
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LEANCHECKER_FAIL:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {**_ok_runner(p), "leanchecker_rc": 1})
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^AXIOM_AUDIT_EXEC_FAIL:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {**_ok_runner(p), "axiom_rc": 1})
        drifted_ax = list(vmod.EXPECTED_AXIOM_AUDIT_LINES)
        drifted_ax[0] = "'S150Pilot1Theorems.evalPoly_norm' depends on axioms: [propext, Quot.sound]"
        with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^AXIOM_PIN_MISMATCH:"):
            vmod.verify_lean_package(PKG_DIR, lean_runner=lambda p: {**_ok_runner(p), "axiom_stdout": "\n".join(drifted_ax)})

        with tempfile.TemporaryDirectory() as td:
            missing_dir = Path(td, "missing_pkg")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^MISSING_LEAN_DIR:"):
                vmod.verify_lean_package(missing_dir)

            cp = Path(td, "pkg")
            shutil.copytree(PKG_DIR, cp)

            orig_cert = json.loads(Path(cp, "s150_lean_theorems_certificate.json").read_text(encoding="utf-8"))
            root_lean = Path(cp, "S150Pilot1Theorems.lean")
            orig_root = root_lean.read_text(encoding="utf-8")
            root_lean.write_text(orig_root + "-- comment edit\n", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SOURCE_SHA256_MISMATCH:"):
                vmod.validate_certificate(orig_cert, pkg_dir=cp)
            root_lean.write_text(orig_root, encoding="utf-8")

            tc_p = Path(cp, "lean-toolchain")
            tc_p.unlink()
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^MISSING_BOUND_FILE:"):
                vmod.verify_lean_package(cp)
            tc_p.write_text("leanprover/lean4:v4.35.0\n", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^BAD_TOOLCHAIN:"):
                vmod.verify_lean_package(cp)
            tc_p.write_text("leanprover/lean4:v4.36.0\n", encoding="utf-8")

            mf_p = Path(cp, "lake-manifest.json")
            orig_mf = mf_p.read_text(encoding="utf-8")
            mf_p.write_text('{"packages": [{"name": "mathlib"}]}', encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^NONEMPTY_LAKE_PACKAGES:"):
                vmod.verify_lean_package(cp)
            mf_p.write_text("[]", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^NONEMPTY_LAKE_PACKAGES:"):
                vmod.verify_lean_package(cp)
            mf_p.write_text(orig_mf, encoding="utf-8")

            lk_p = Path(cp, "lakefile.toml")
            orig_lk = lk_p.read_text(encoding="utf-8")
            lk_p.write_text("=invalid toml", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^BAD_LAKEFILE_TOML:"):
                vmod.verify_lean_package(cp)
            lk_p.write_text(orig_lk + '\n[[require]]\nname = "mathlib"\n', encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^NONEMPTY_LAKEFILE_REQUIRE:"):
                vmod.verify_lean_package(cp)
            for bad_lk in (
                orig_lk + '\nmoreLeanArgs = ["-DwarningAsError=false"]\n',
                orig_lk + '\nmoreLeanArgs = ["-Dfoo=true"]\n',
                'name = "Wrong"\ndefaultTargets = ["S150Pilot1Theorems"]\n[[lean_lib]]\nname = "S150Pilot1Theorems"\n',
                'name = "S150Pilot1Theorems"\ndefaultTargets = ["Other"]\n[[lean_lib]]\nname = "S150Pilot1Theorems"\n',
                'name = "S150Pilot1Theorems"\ndefaultTargets = ["S150Pilot1Theorems"]\n[[lean_lib]]\nname = "S150Pilot1Theorems"\nmoreLeanArgs = ["-Dx=1"]\n',
            ):
                lk_p.write_text(bad_lk, encoding="utf-8")
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^FORBIDDEN_LAKEFILE_OPT:"):
                    vmod.verify_lean_package(cp)
            lk_p.write_text(orig_lk, encoding="utf-8")

            sym_dir = Path(td, "sym_pkg")
            sym_dir.symlink_to(cp)
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SYMLINK_FORBIDDEN:"):
                vmod.read_package_snapshot(sym_dir)
            sym_lean = Path(cp, "ExtraSym.lean")
            sym_lean.symlink_to(root_lean)
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SYMLINK_FORBIDDEN:"):
                vmod.read_package_snapshot(cp)
            sym_lean.unlink()
            lk_p.unlink()
            lk_p.symlink_to(Path(PKG_DIR, "lakefile.toml"))
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^SYMLINK_FORBIDDEN:"):
                vmod.read_package_snapshot(cp)
            lk_p.unlink()
            lk_p.write_text(orig_lk, encoding="utf-8")

            ex = Path(cp, "Extra.lean")
            ex.write_text("def x : Nat := 0\n", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LEAN_FILE_SET_FAIL:"):
                vmod.verify_lean_package(cp)
            ex.unlink()

            for esc_snippet in (
                'theorem ok : 1 = 1 := rfl\n#eval IO.println "BAYT_EVAL_PROBE"\n',
                "#reduce 1 + 1\n",
                'def probe := IO.println "hi"\n',
                "def p := System.FilePath.mk \"a\"\n",
                "theorem bad : 1 = 1 := by bv_decide\n",
                "theorem bad : 1 = 1 := by decide +native\n",
                'def bad := m!"{sorry}"\n',
                "import«Std».Tactic.BVDecide\n",
                "@[implemented_by foo] def bar : Nat := 0\n",
                "@[csimp] theorem bad_c : 1 = 1 := rfl\n",
                "open Classical\n",
                "def x := '\"'\ntheorem cheat : 1 = 2 := by sorry\ndef y := '\"'\n",
                "run_cmd pure ()\n",
                "opaque secretVal : Nat\n",
                "set_option maxRecDepth 999999\n",
            ):
                root_lean.write_text(esc_snippet, encoding="utf-8")
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^LEAN_STATIC_ESCAPE:"):
                    vmod.verify_lean_package(cp)

            for bad_imp in ("import Std.Tactic.BVDecide\n", "import S150Pilot1Theorems Std\n"):
                root_lean.write_text(bad_imp, encoding="utf-8")
                with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^FORBIDDEN_IMPORT:"):
                    vmod.verify_lean_package(cp)
            root_lean.write_text(orig_root, encoding="utf-8")

            ax_p = Path(cp, "AxiomAudit.lean")
            orig_ax_lean = ax_p.read_text(encoding="utf-8")
            ax_p.write_text(orig_ax_lean + "\n#print axioms S150Pilot1Theorems.evalPoly_norm\n", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^AXIOM_AUDIT_DUP_OR_LEN:"):
                vmod.verify_lean_package(cp)

            lines_ax = [ln for ln in orig_ax_lean.splitlines() if ln.strip().startswith("#print")]
            lines_ax[0] = "#print axioms S150Pilot1Theorems.nonexistent_thm"
            ax_p.write_text("import S150Pilot1Theorems\n" + "\n".join(lines_ax) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^AXIOM_AUDIT_SET_MISMATCH:"):
                vmod.verify_lean_package(cp)
            ax_p.write_text(orig_ax_lean, encoding="utf-8")

            t1_p = Path(cp, "S150Pilot1Theorems", "Topic1FrickeCayley.lean")
            t1_txt = t1_p.read_text(encoding="utf-8")
            t1_p.write_text(t1_txt.replace("end S150Pilot1Theorems", "theorem extra_t : 1 = 1 := rfl\nend S150Pilot1Theorems"), encoding="utf-8")
            ax_p.write_text(orig_ax_lean + "\n#print axioms S150Pilot1Theorems.extra_t\n", encoding="utf-8")
            with self.assertRaisesRegex(vmod.S150LeanVerifyError, r"^PUB_THM_COUNT_FAIL:"):
                vmod.verify_lean_package(cp)


if __name__ == "__main__":
    unittest.main()
