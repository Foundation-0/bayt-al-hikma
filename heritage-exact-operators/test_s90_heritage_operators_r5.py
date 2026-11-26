#!/usr/bin/env python3
"""Heritage Exact Operators: Assertion-Free R5 Verification, Adversarial Tamper, Zone-B I/O,
R12 Lean Escape, Env-Scrubbed Subprocess, and Zero-Skip Dual-Environment Test Suite.
"""
from __future__ import annotations

import ast
import copy
from fractions import Fraction
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import s90_heritage_operators_oracle as oracle  # noqa: E402
import verify_s90_heritage_operators as verifier  # noqa: E402


class Test01StaticHygiene(unittest.TestCase):
    def test_ast_and_text_hygiene(self) -> None:
        home_tok = b"/" + b"home/"
        devnull_tok = b"/" + b"dev/null"
        for name in ("s90_heritage_operators_oracle.py", "verify_s90_heritage_operators.py"):
            raw = (_THIS_DIR / name).read_bytes()
            self.assertNotIn(b"\r", raw)
            self.assertNotIn(home_tok, raw)
            self.assertNotIn(devnull_tok, raw)
            tree = ast.parse(raw.decode("utf-8"))
            for node in ast.walk(tree):
                self.assertFalse(isinstance(node, ast.Assert), f"bare assert in {name}")
                if isinstance(node, ast.Constant):
                    self.assertFalse(type(node.value) is float, f"float literal in {name}")
                if isinstance(node, ast.Name):
                    self.assertNotEqual(node.id, "float")
                if isinstance(node, ast.Attribute):
                    self.assertNotEqual(node.attr, "isdigit")
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "random")
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(node.module, "random")
        test_raw = (_THIS_DIR / "test_s90_heritage_operators_r5.py").read_bytes()
        self.assertNotIn(b"\r", test_raw)
        self.assertNotIn(home_tok, test_raw)
        self.assertNotIn(devnull_tok, test_raw)
        for node in ast.walk(ast.parse(test_raw.decode("utf-8"))):
            self.assertFalse(isinstance(node, ast.Assert))

    def test_disk_certificate_canonical_zero_float(self) -> None:
        raw = (_THIS_DIR / "s90_heritage_operators_certificate.json").read_bytes()
        cert = verifier.parse_strict_json_bytes(raw, "disk_cert", require_canonical=True)
        self.assertEqual(cert["track_id"], oracle.TRACK_ID)
        self.assertEqual(cert["payload"]["pinned_artifacts"]["lean_theorem_count"], 20)
        self.assertEqual(cert["payload"]["heritage_dataset"]["pinned_sources_count"], 11)


class Test02OraclePrimitivesAndEngines(unittest.TestCase):
    def _assert_s90(self, code: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(oracle.S90Error) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_type_and_hex_guards(self) -> None:
        oracle.require_ok(True, "X", "x")
        self._assert_s90("X", oracle.require_ok, False, "X", "x")
        self._assert_s90("X", oracle.require_ok, 1, "X", "x")
        self.assertTrue(oracle.require_bool(True, "b"))
        self.assertFalse(oracle.require_bool(False, "b"))
        self._assert_s90("INVALID_BOOL", oracle.require_bool, 1, "b")
        self.assertEqual(oracle.require_exact_int(5, "n", lo=5, hi=5), 5)
        self._assert_s90("INVALID_INT", oracle.require_exact_int, True, "n")
        self._assert_s90("INT_OUT_OF_RANGE", oracle.require_exact_int, 4, "n", lo=5)
        self._assert_s90("INT_OUT_OF_RANGE", oracle.require_exact_int, 6, "n", hi=5)
        self.assertEqual(oracle.require_exact_str("ok", "s"), "ok")
        self._assert_s90("INVALID_STR", oracle.require_exact_str, 9, "s")
        good_hex = "0123456789abcdef" * 4
        self.assertEqual(oracle.require_hex64(good_hex, "h"), good_hex)
        self._assert_s90("INVALID_HEX64", oracle.require_hex64, "ab", "h")
        self._assert_s90("INVALID_HEX64", oracle.require_hex64, "A" * 64, "h")

    def test_validate_strict_json_tree_and_formatters(self) -> None:
        oracle.validate_strict_json_tree({"a": [1, "s", True, False, None]})
        self._assert_s90("INVALID_JSON_KEY", oracle.validate_strict_json_tree, {1: "a"})
        self._assert_s90("FORBIDDEN_JSON_TYPE", oracle.validate_strict_json_tree, {"a": (1, 2)})
        self._assert_s90("FORBIDDEN_JSON_TYPE", oracle.validate_strict_json_tree, object())
        deep: dict = {}
        cur = deep
        for _ in range(34):
            nxt: dict = {}
            cur["k"] = nxt
            cur = nxt
        self._assert_s90("JSON_DEPTH_EXCEEDED", oracle.validate_strict_json_tree, deep)
        # Boundary depth == 32 passes
        ok_deep: dict = {}
        cur2 = ok_deep
        for _ in range(32):
            nxt2: dict = {}
            cur2["k"] = nxt2
            cur2 = nxt2
        oracle.validate_strict_json_tree(ok_deep)

        self.assertEqual(oracle.fmt_q(Fraction(7, 1)), "7")
        self.assertEqual(oracle.fmt_q(Fraction(-3, 4)), "-3/4")
        self._assert_s90("INVALID_FRACTION", oracle.fmt_q, 7)

        self.assertEqual(oracle.fmt_dec_q(Fraction(1, 2), 0), "1")
        self.assertEqual(oracle.fmt_dec_q(Fraction(-1, 2), 0), "-1")
        self.assertEqual(oracle.fmt_dec_q(Fraction(-1, 100), 0), "0")
        self.assertEqual(oracle.fmt_dec_q(Fraction(0, 1), 0), "0")
        self.assertEqual(oracle.fmt_dec_q(Fraction(-1, 1000), 2), "0.00")
        self.assertEqual(oracle.fmt_dec_q(Fraction(-3, 4), 2), "-0.75")
        self.assertEqual(oracle.fmt_dec_q(Fraction(1, 8), 2), "0.13")
        self.assertEqual(oracle.fmt_dec_q(Fraction(1, 3), 4), "0.3333")
        self._assert_s90("INVALID_FRACTION", oracle.fmt_dec_q, 1, 2)
        self._assert_s90("INT_OUT_OF_RANGE", oracle.fmt_dec_q, Fraction(1, 2), -1)
        self._assert_s90("INT_OUT_OF_RANGE", oracle.fmt_dec_q, Fraction(1, 2), 19)

    def test_math_helpers_and_engines(self) -> None:
        lo, hi = oracle._isqrt_int_bracket(2, 100)
        self.assertTrue(lo * lo < 2 < hi * hi)
        self._assert_s90("ISQRT_DOMAIN", oracle._isqrt_int_bracket, 0, 10)
        self._assert_s90("ISQRT_DOMAIN", oracle._isqrt_int_bracket, 2, 0)
        self._assert_s90("ISQRT_NON_SQUARE", oracle._isqrt_int_bracket, 4, 10)

        flo, fhi = oracle._frac_sqrt_bracket(Fraction(3, 2), 100)
        self.assertTrue(flo * flo <= Fraction(3, 2) <= fhi * fhi)
        self._assert_s90("FSQRT_DOMAIN", oracle._frac_sqrt_bracket, Fraction(0), 10)
        self._assert_s90("FSQRT_DOMAIN", oracle._frac_sqrt_bracket, Fraction(3, 2), 0)

        self.assertFalse(oracle._is_prime(1))
        self.assertTrue(oracle._is_prime(2))
        self.assertFalse(oracle._is_prime(9))
        self.assertFalse(oracle._is_prime(287))
        self.assertTrue(oracle._is_prime(73727))
        self.assertEqual(oracle._sigma(1), 1)
        self.assertEqual(oracle._sigma(4), 7)
        self.assertEqual(oracle._sigma(220), 504)
        self.assertEqual(oracle._sigma(284), 504)
        self.assertEqual(oracle._sigma(2296), 5040)
        self.assertTrue(oracle.is_amicable_pair(220, 284))
        self.assertFalse(oracle.is_amicable_pair(2024, 2296))
        self.assertFalse(oracle.is_amicable_pair(2296, 2024))

        self.assertEqual(oracle._eval_int_poly((3, 7, -12, -1, 1), Fraction(1)), Fraction(-2))
        h = "a" * 64
        cert = oracle.build_certificate(h, h, h)
        self.assertEqual(cert["payload"]["engine1_tusi_couple"]["spherical_hippopede_samples"][0]["px_transverse_q"], "288/3125")
        self.assertEqual(cert["payload"]["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"]["alexander_dark_band_cos2_gap_q"], "35/216")
        self._assert_s90("INVALID_HEX64", oracle.build_certificate, "bad", h, h)
        self._assert_s90("INVALID_HEX64", oracle.build_certificate, h, "bad", h)
        self._assert_s90("INVALID_HEX64", oracle.build_certificate, h, h, "bad")


class Test03ZoneBIOAndParsers(unittest.TestCase):
    def _assert_s90(self, code: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(oracle.S90Error) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_path_and_darwin_normalization(self) -> None:
        self.assertEqual(verifier._normalize_darwin_private_prefix("/private/tmp"), "/tmp")
        self.assertEqual(verifier._normalize_darwin_private_prefix("/private/tmp/a"), "/tmp/a")
        self.assertEqual(verifier._normalize_darwin_private_prefix("/private/var"), "/var")
        self.assertEqual(verifier._normalize_darwin_private_prefix("/private/var/b"), "/var/b")
        self.assertEqual(verifier._normalize_darwin_private_prefix("/private/other"), "/private/other")
        self.assertEqual(verifier._normalize_darwin_private_prefix("/tmp/x"), "/tmp/x")

        self.assertEqual(verifier._check_path_str(Path("a.json"), "p"), Path("a.json"))
        self.assertEqual(verifier._check_path_str("a.json", "p"), Path("a.json"))
        self._assert_s90("INVALID_STR", verifier._check_path_str, 123, "p")
        self._assert_s90("EMPTY_PATH", verifier._check_path_str, "", "p")
        self._assert_s90("NUL_BYTE_FORBIDDEN", verifier._check_path_str, "a\x00b", "p")
        self._assert_s90("INVALID_UTF8_SURROGATE", verifier._check_path_str, "\ud800", "p")

    def test_safe_cwd_and_pwd_checks(self) -> None:
        verifier._check_safe_cwd()
        with mock.patch.object(verifier.os, "getcwd", side_effect=OSError("gone")):
            self._assert_s90("CWD_ERROR", verifier._check_safe_cwd)
        with tempfile.TemporaryDirectory() as td:
            real_d = Path(td) / "real"
            real_d.mkdir(mode=0o700)
            sym_cwd = Path(td) / "sym_cwd"
            os.symlink(os.getcwd(), sym_cwd)
            with mock.patch.dict(os.environ, {"PWD": str(sym_cwd)}):
                self._assert_s90("SYMLINK_IN_PATH", verifier._check_safe_cwd)
            with mock.patch.dict(os.environ, {"PWD": str(real_d)}):
                verifier._check_safe_cwd()
            with mock.patch.dict(os.environ, {"PWD": str(Path(td) / "missing_pwd")}):
                verifier._check_safe_cwd()
            # Exercise same st_dev different st_ino AND different st_dev same st_ino for BoolOp kill
            cwd_st = os.stat(os.getcwd())
            fake_dev = os.stat_result((cwd_st.st_mode, cwd_st.st_ino, cwd_st.st_dev + 999, 1, 0, 0, 0, 0, 0, 0))
            fake_ino = os.stat_result((cwd_st.st_mode, cwd_st.st_ino + 999, cwd_st.st_dev, 1, 0, 0, 0, 0, 0, 0))
            with mock.patch.dict(os.environ, {"PWD": str(sym_cwd)}), mock.patch.object(
                verifier.os, "stat", side_effect=[fake_dev, cwd_st]
            ):
                verifier._check_safe_cwd()
            with mock.patch.dict(os.environ, {"PWD": str(sym_cwd)}), mock.patch.object(
                verifier.os, "stat", side_effect=[fake_ino, cwd_st]
            ):
                verifier._check_safe_cwd()
            sym_other = Path(td) / "sym_other"
            os.symlink(real_d, sym_other)
            with mock.patch.dict(os.environ, {"PWD": str(sym_other)}):
                verifier._check_safe_cwd()
            with mock.patch.dict(os.environ, {"PWD": "rel_sym"}), mock.patch.object(
                verifier, "_check_no_symlink_components", side_effect=[Path(os.getcwd()), oracle.S90Error("SYMLINK_IN_PATH", "rel")]
            ), mock.patch.object(verifier.os, "stat", return_value=cwd_st):
                verifier._check_safe_cwd()
            with mock.patch.dict(os.environ, {"PWD": "relative/pwd"}):
                verifier._check_safe_cwd()
            env_nopwd = {k: v for k, v in os.environ.items() if k != "PWD"}
            with mock.patch.dict(os.environ, env_nopwd, clear=True):
                verifier._check_safe_cwd()

    def test_read_and_write_zone_b_adversarial(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            reg = tdp / "ok.json"
            verifier.write_regular_bytes_atomic_0600(reg, b"hello", "reg")
            self.assertEqual(stat.S_IMODE(os.lstat(reg).st_mode), 0o600)
            self.assertEqual(verifier.read_regular_bytes_capped(reg, "reg", max_bytes=16), b"hello")
            verifier.write_regular_bytes_atomic_0600(reg, b"updated", "reg")
            self.assertEqual(verifier.read_regular_bytes_capped(reg, "reg", max_bytes=7), b"updated")

            with mock.patch.object(verifier.os, "read", return_value=b""):
                self._assert_s90("FILE_TOO_LARGE", verifier.read_regular_bytes_capped, reg, "reg", max_bytes=4)
            self._assert_s90("IO_OPEN_ERROR", verifier.read_regular_bytes_capped, tdp / "missing.json", "m")

            sym = tdp / "sym.json"
            os.symlink(reg, sym)
            self._assert_s90("SYMLINK_IN_PATH", verifier.read_regular_bytes_capped, sym, "sym")
            self._assert_s90("SYMLINK_IN_PATH", verifier.write_regular_bytes_atomic_0600, sym, b"x", "sym")

            hard = tdp / "hard.json"
            os.link(reg, hard)
            self._assert_s90("HARDLINK_FORBIDDEN", verifier.read_regular_bytes_capped, hard, "hard")
            self._assert_s90("HARDLINK_FORBIDDEN", verifier.write_regular_bytes_atomic_0600, hard, b"x", "hard")
            os.unlink(hard)

            fifo = tdp / "pipe.fifo"
            os.mkfifo(fifo, 0o600)
            self._assert_s90("NON_REGULAR_FILE", verifier.read_regular_bytes_capped, fifo, "fifo")
            self._assert_s90("NON_REGULAR_TARGET", verifier.write_regular_bytes_atomic_0600, fifo, b"x", "fifo")

            sub = tdp / "sub"
            sub.mkdir(mode=0o700)
            self._assert_s90("NON_REGULAR_FILE", verifier.read_regular_bytes_capped, sub, "sub")
            self._assert_s90("NON_REGULAR_TARGET", verifier.write_regular_bytes_atomic_0600, sub, b"x", "sub")

            self._assert_s90("IO_PARENT_ERROR", verifier.write_regular_bytes_atomic_0600, tdp / "no_dir" / "a", b"x", "nd")
            self._assert_s90("PARENT_NOT_DIR", verifier.write_regular_bytes_atomic_0600, reg / "child", b"x", "pnd")

            with mock.patch.object(verifier.os, "lstat", side_effect=PermissionError("denied")):
                self._assert_s90("IO_STAT_ERROR", verifier._check_no_symlink_components, reg, "st")

            orig_lstat = os.lstat

            def fail_target_lstat(p):
                if str(p) == str(reg):
                    raise PermissionError("boom")
                return orig_lstat(p)

            with mock.patch.object(verifier, "_check_safe_cwd"), mock.patch.object(
                verifier, "_check_no_symlink_components", return_value=reg
            ), mock.patch.object(verifier.os, "lstat", side_effect=fail_target_lstat):
                self._assert_s90("IO_STAT_ERROR", verifier.write_regular_bytes_atomic_0600, reg, b"x", "st2")

            with mock.patch.object(verifier.os, "read", side_effect=[b"1234", b"5678", b""]):
                self._assert_s90("FILE_TOO_LARGE", verifier.read_regular_bytes_capped, reg, "grow", max_bytes=7)

            with mock.patch.object(verifier.os, "write", return_value=0):
                self._assert_s90("IO_WRITE_SHORT", verifier.write_regular_bytes_atomic_0600, tdp / "sw.json", b"abc", "sw")
            with mock.patch.object(verifier.os, "replace", side_effect=OSError("rep")):
                with self.assertRaises(OSError):
                    verifier.write_regular_bytes_atomic_0600(tdp / "rp.json", b"abc", "rp")
            with mock.patch.object(verifier.os, "replace", side_effect=OSError("rep2")), mock.patch.object(
                verifier.os, "unlink", side_effect=OSError("ul")
            ):
                with self.assertRaises(OSError):
                    verifier.write_regular_bytes_atomic_0600(tdp / "rp2.json", b"abc", "rp2")

    def test_strict_json_and_rational_parsers(self) -> None:
        self.assertEqual(verifier.parse_strict_json_bytes(b'{"a":1}', "ok"), {"a": 1})
        self.assertEqual(verifier.parse_strict_json_bytes(b'{"a": 1}', "nc", require_canonical=False), {"a": 1})
        self._assert_s90("NON_CANONICAL_JSON", verifier.parse_strict_json_bytes, b'{"a": 1}', "nc", require_canonical=True)
        self._assert_s90("EMPTY_JSON", verifier.parse_strict_json_bytes, b"", "e")
        self._assert_s90("FILE_TOO_LARGE", verifier.parse_strict_json_bytes, b"a" * (verifier.MAX_JSON_BYTES + 1), "big")
        exact_pad = verifier.MAX_JSON_BYTES - len(b'{"a":""}')
        self.assertEqual(len(verifier.parse_strict_json_bytes(b'{"a":"' + b"x" * exact_pad + b'"}', "exact_max")["a"]), exact_pad)
        self._assert_s90("NUL_BYTE_FORBIDDEN", verifier.parse_strict_json_bytes, b'{"a":"\x00"}', "nul")
        self._assert_s90("BOM_FORBIDDEN", verifier.parse_strict_json_bytes, b'\xef\xbb\xbf{"a":1}', "bom")
        self._assert_s90("NON_ASCII_JSON", verifier.parse_strict_json_bytes, b'{"a":"\xff"}', "na")
        self._assert_s90("CRLF_FORBIDDEN", verifier.parse_strict_json_bytes, b'{"a":1}\r\n', "cr")
        self.assertEqual(verifier.parse_strict_json_bytes(b'{"a":' + b"9" * 80 + b"}", "i80")["a"], int("9" * 80))
        with mock.patch.object(verifier.json, "loads", side_effect=RuntimeError("must pre-scan")):
            self._assert_s90("JSON_INT_TOO_LARGE", verifier.parse_strict_json_bytes, b'{"a":' + b"9" * 81 + b"}", "i81")
        self._assert_s90("JSON_INT_TOO_LARGE", verifier.parse_strict_json_bytes, b'{"a":-' + b"9" * 81 + b"}", "ni81")
        self.assertEqual(verifier._strict_int("9" * 80), int("9" * 80))
        self._assert_s90("JSON_INT_TOO_LARGE", verifier._strict_int, "9" * 81)
        self._assert_s90("JSON_INT_TOO_LARGE", verifier._strict_int, "-" + "9" * 81)
        self.assertEqual(verifier._strict_int("-42"), -42)
        self._assert_s90("FORBIDDEN_JSON_FLOAT", verifier.parse_strict_json_bytes, b'{"a":1.5}', "fl")
        self._assert_s90("FORBIDDEN_JSON_CONSTANT", verifier.parse_strict_json_bytes, b'{"a":NaN}', "nan")
        self._assert_s90("DUPLICATE_JSON_KEY", verifier.parse_strict_json_bytes, b'{"a":1,"a":2}', "dup")
        self._assert_s90("INVALID_JSON", verifier.parse_strict_json_bytes, b"{bad", "bad")
        self._assert_s90("JSON_ROOT_NOT_OBJECT", verifier.parse_strict_json_bytes, b"[1,2]", "arr")

        self.assertEqual(verifier.parse_canonical_rational_str("0", "q"), Fraction(0))
        self.assertEqual(verifier.parse_canonical_rational_str("-3", "q"), Fraction(-3))
        self.assertEqual(verifier.parse_canonical_rational_str("3/4", "q"), Fraction(3, 4))
        self.assertEqual(verifier.parse_canonical_rational_str("-5/7", "q"), Fraction(-5, 7))
        self.assertEqual(verifier.parse_canonical_rational_str("9" * 80, "q80"), Fraction(int("9" * 80), 1))
        self.assertEqual(verifier.parse_canonical_rational_str("9" * 80 + "/2", "q80n"), Fraction(int("9" * 80), 2))
        self.assertEqual(verifier.parse_canonical_rational_str("1/" + "9" * 80, "q80d"), Fraction(1, int("9" * 80)))
        max_q = "-" + "9" * 80 + "/" + "1" + "0" * 79
        self.assertEqual(len(max_q), verifier.MAX_RATIONAL_STR_LEN)
        self.assertEqual(verifier.parse_canonical_rational_str(max_q, "q162"), Fraction(-int("9" * 80), 10**79))
        for bad in (1, "", "01", "+1", "1/0", "3/1", "2/4", " 1/2", "1/2 ", "1/-2"):
            with self.assertRaises(oracle.S90Error):
                verifier.parse_canonical_rational_str(bad, "q")
        self._assert_s90("INT_TOO_LARGE", verifier.parse_canonical_rational_str, "9" * 81, "q")
        self._assert_s90("INT_TOO_LARGE", verifier.parse_canonical_rational_str, "9" * 81 + "/2", "q")
        self._assert_s90("INT_TOO_LARGE", verifier.parse_canonical_rational_str, "1/" + "9" * 81, "q")
        self._assert_s90("RATIONAL_TOO_LARGE", verifier.parse_canonical_rational_str, "9" * 163, "q")
        self._assert_s90("RATIONAL_TOO_LARGE", verifier.parse_canonical_rational_str, "-" + "9" * 80 + "/" + "1" + "0" * 80, "q")
        self._assert_s90("RATIONAL_TOO_LARGE", verifier.parse_canonical_rational_str, "9" * 5000, "q")
        self._assert_s90("RATIONAL_TOO_LARGE", verifier.parse_canonical_rational_str, "1/" + "9" * 5000, "q")
        self.assertFalse(verifier._is_prime_ind(1))
        self.assertTrue(verifier._is_prime_ind(2))
        self.assertFalse(verifier._is_prime_ind(287))
        self.assertEqual(verifier._sigma_ind(4), 7)


class Test04SecondaryAuditReplayAndCLI(unittest.TestCase):
    def setUp(self) -> None:
        raw = (_THIS_DIR / "s90_heritage_operators_certificate.json").read_bytes()
        self.cert = verifier.parse_strict_json_bytes(raw, "cert", require_canonical=True)

    def _assert_s90(self, code: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(oracle.S90Error) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_envelope_and_load_artifacts_errors(self) -> None:
        self._assert_s90("INVALID_BOOL", verifier.verify_certificate_dict, self.cert, full_replay=1)
        self._assert_s90("INVALID_CERT_TYPE", verifier.verify_certificate_dict, [], full_replay=False)
        c1 = copy.deepcopy(self.cert)
        c1["schema_version"] = "bad"
        self._assert_s90("SCHEMA_MISMATCH", verifier.verify_certificate_dict, c1, full_replay=False)
        c2 = copy.deepcopy(self.cert)
        c2["track_id"] = "bad"
        self._assert_s90("SCHEMA_MISMATCH", verifier.verify_certificate_dict, c2, full_replay=False)
        c3 = copy.deepcopy(self.cert)
        c3["payload_sha256"] = "0" * 64
        self._assert_s90("PAYLOAD_SHA_MISMATCH", verifier.verify_certificate_dict, c3, full_replay=False)
        c4 = copy.deepcopy(self.cert)
        c4["certificate_sha256"] = "0" * 64
        self._assert_s90("CERT_SHA_MISMATCH", verifier.verify_certificate_dict, c4, full_replay=False)

        c5 = copy.deepcopy(self.cert)
        drifted = copy.deepcopy(self.cert)
        drifted["certificate_sha256"] = "0" * 64
        stub = {
            "lean_source_sha256": verifier.PINNED_LEAN_SOURCE_SHA256,
            "theorems_verified": 20,
            "lean_version": "4.36.0",
        }
        with mock.patch.object(verifier, "verify_lean4_file_live", return_value=stub), mock.patch.object(
            verifier.oracle, "build_certificate", return_value=drifted
        ):
            self._assert_s90("FULL_REPLAY_MISMATCH", verifier.verify_certificate_dict, c5, full_replay=True)

        with tempfile.TemporaryDirectory() as td:
            tdp = Path(td)
            (tdp / "HeritageExactOperators.lean").write_text("", encoding="utf-8")
            (tdp / "lakefile.toml").write_text("x", encoding="utf-8")
            (tdp / "lean-toolchain").write_bytes(b"\xff\xfe")
            self._assert_s90("INVALID_UTF8", verifier._load_track_artifacts, tdp)
            (tdp / "lean-toolchain").write_text("leanprover/lean4:v4.0.0\n", encoding="utf-8")
            self._assert_s90("TOOLCHAIN_MISMATCH", verifier._load_track_artifacts, tdp)

    def _resign(self, payload: dict) -> dict:
        p_sha = oracle.sha256_hex(oracle.canonical_json_bytes(payload))
        body = {
            "schema_version": oracle.SCHEMA_VERSION,
            "track_id": oracle.TRACK_ID,
            "payload_sha256": p_sha,
            "payload": payload,
        }
        return {**body, "certificate_sha256": oracle.sha256_hex(oracle.canonical_json_bytes(body))}

    def test_secondary_audit_exhaustive_tamper_kills(self) -> None:
        def tamper(code: str, mutator) -> None:
            p = copy.deepcopy(self.cert["payload"])
            mutator(p)
            self._assert_s90(code, verifier.secondary_audit_payload, p)
            self._assert_s90(code, verifier.verify_certificate_dict, self._resign(p), full_replay=False)

        self._assert_s90("INVALID_PAYLOAD_TYPE", verifier.secondary_audit_payload, [])
        self._assert_s90("INVALID_OBJECT", verifier._require_exact_dict, [], frozenset(), "x")
        self._assert_s90("SCHEMA_KEYS_MISMATCH", verifier._require_exact_dict, {"a": 1}, frozenset({"b"}), "x")
        tamper("SCHEMA_MISMATCH", lambda p: p.__setitem__("schema_version", "x"))
        tamper("SCHEMA_MISMATCH", lambda p: p.__setitem__("track_id", "x"))
        tamper("SCHEMA_MISMATCH", lambda p: p.__setitem__("oracle_class", "x"))
        tamper("SCHEMA_MISMATCH", lambda p: p.__setitem__("novelty_classification", "N0"))
        tamper("DS_REPO", lambda p: p["heritage_dataset"].__setitem__("repo", "x"))
        tamper("DS_COMMIT", lambda p: p["heritage_dataset"].__setitem__("commit", "x"))
        tamper("DS_SRCS_LEN", lambda p: p["heritage_dataset"].__setitem__("pinned_sources", "x" * 11))
        tamper("DS_SRCS_LEN", lambda p: p["heritage_dataset"].__setitem__("pinned_sources", []))
        tamper("DS_SRCS_PIN", lambda p: p["heritage_dataset"]["pinned_sources"][0].__setitem__("sha256", "0" * 64))
        tamper("DS_SRCS_PIN", lambda p: p["heritage_dataset"]["pinned_sources"][0].__setitem__("work", ""))
        tamper("DS_SRCS_PIN", lambda p: p["heritage_dataset"]["pinned_sources"][0].__setitem__("work", "altered-work"))
        tamper("DS_SRCS_PIN", lambda p: p["heritage_dataset"]["pinned_sources"][0].__setitem__("engine", "altered-engine"))
        tamper("DS_SRCS_PIN", lambda p: p["heritage_dataset"]["pinned_sources"][0].__setitem__("scholar", "altered-scholar"))
        tamper("DS_SRCS_PIN", lambda p: p["heritage_dataset"]["pinned_sources"][0].__setitem__("relpath", "altered/path.json"))
        tamper("MOD_LEN", lambda p: p.__setitem__("modern_anchor_bridges", "x" * 10))
        tamper("MOD_LEN", lambda p: p.__setitem__("modern_anchor_bridges", []))
        tamper("MOD_PIN", lambda p: p["modern_anchor_bridges"][0].__setitem__("cert_sha256", "0" * 64))
        tamper("MOD_PIN", lambda p: p["modern_anchor_bridges"][0].__setitem__("bridge", ""))
        tamper("MOD_PIN", lambda p: p["modern_anchor_bridges"][0].__setitem__("bridge", "altered-bridge"))
        tamper("SCHEMA_MISMATCH", lambda p: p["pinned_artifacts"].__setitem__("lean_source", "x"))
        tamper("SCHEMA_MISMATCH", lambda p: p["pinned_artifacts"].__setitem__("lean_toolchain", "x"))
        tamper("PINNED_SHA_MISMATCH", lambda p: p["pinned_artifacts"].__setitem__("lean_source_sha256", "0" * 64))
        tamper("THEOREM_LIST_MISMATCH", lambda p: p["pinned_artifacts"].__setitem__("lean_theorem_names", {k: 1 for k in oracle.LEAN_THEOREM_NAMES}))
        tamper("THEOREM_LIST_MISMATCH", lambda p: p["pinned_artifacts"].__setitem__("lean_theorem_names", []))

        # Huge >4300-digit rational string rejected cleanly without ValueError traceback
        tamper("RATIONAL_TOO_LARGE", lambda p: p["engine1_tusi_couple"]["planar_samples"][0].__setitem__("t_q", "9" * 5000))

        # Engine 1 (incl. boundary & re-signed forgery regressions)
        tamper("E1_PLANAR", lambda p: p["engine1_tusi_couple"].__setitem__("planar_all_y_zero", False))
        tamper("E1_SPHERE", lambda p: p["engine1_tusi_couple"].__setitem__("all_spherical_norms_exact_one", False))
        tamper("E1_SPHERE", lambda p: p["engine1_tusi_couple"].__setitem__("all_spherical_deviations_nonzero", False))
        tamper("E1_PLANAR_LEN", lambda p: p["engine1_tusi_couple"].__setitem__("planar_samples", "123456"))
        tamper("E1_PLANAR_LEN", lambda p: p["engine1_tusi_couple"].__setitem__("planar_samples", []))
        tamper("E1_PLANAR_MATH", lambda p: p["engine1_tusi_couple"]["planar_samples"][0].__setitem__("t_q", "999999"))
        tamper("E1_PLANAR_MATH", lambda p: (
            p["engine1_tusi_couple"]["planar_samples"][0].__setitem__("cos_q", "0"),
            p["engine1_tusi_couple"]["planar_samples"][0].__setitem__("x_q", "0"),
        ))
        tamper("E1_PLANAR_MATH", lambda p: p["engine1_tusi_couple"]["planar_samples"][0].__setitem__("sin_q", "1"))
        tamper("E1_PLANAR_MATH", lambda p: p["engine1_tusi_couple"]["planar_samples"][0].__setitem__("x_q", "3"))
        tamper("E1_PLANAR_MATH", lambda p: p["engine1_tusi_couple"]["planar_samples"][0].__setitem__("y_q", "1"))
        tamper("E1_PLANAR_DOM", lambda p: p["engine1_tusi_couple"]["planar_samples"].__setitem__(0, {
            "t_q": "4", "cos_q": "-15/17", "sin_q": "8/17", "x_q": "-30/17", "y_q": "0",
        }))
        tamper("E1_MAT_MATH", lambda p: (
            p["engine1_tusi_couple"]["matrix_curl_annihilation"].__setitem__("a_q", "4/5"),
            p["engine1_tusi_couple"]["matrix_curl_annihilation"].__setitem__("tusi_avg_diag_q", "4/5"),
            p["engine1_tusi_couple"]["matrix_curl_annihilation"].__setitem__("trace_preserved_q", "8/5"),
        ))
        tamper("E1_MAT_MATH", lambda p: p["engine1_tusi_couple"]["matrix_curl_annihilation"].__setitem__("b_q", "3/5"))
        tamper("E1_MAT_MATH", lambda p: p["engine1_tusi_couple"]["matrix_curl_annihilation"].__setitem__("tusi_avg_diag_q", "0"))
        tamper("E1_MAT_MATH", lambda p: p["engine1_tusi_couple"]["matrix_curl_annihilation"].__setitem__("tusi_avg_offdiag_q", "1"))
        tamper("E1_MAT_MATH", lambda p: p["engine1_tusi_couple"]["matrix_curl_annihilation"].__setitem__("trace_preserved_q", "0"))
        tamper("E1_PHASE", lambda p: p["engine1_tusi_couple"].__setitem__("spherical_phase_cos_q", "4/5"))
        tamper("E1_PHASE", lambda p: p["engine1_tusi_couple"].__setitem__("spherical_phase_sin_q", "3/5"))
        tamper("E1_SPHERE_LEN", lambda p: p["engine1_tusi_couple"].__setitem__("spherical_hippopede_samples", "123"))
        tamper("E1_SPHERE_LEN", lambda p: p["engine1_tusi_couple"].__setitem__("spherical_hippopede_samples", []))
        tamper("E1_SPHERE_MATH", lambda p: (
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("cos_alpha_q", "0"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("sin_alpha_q", "2"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("px_transverse_q", "192/125"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("py_longitudinal_q", "-144/125"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("pz_vertical_q", "-103/25"),
        ))
        tamper("E1_SPHERE_MATH", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("px_transverse_q", "1"))
        tamper("E1_SPHERE_MATH", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("py_longitudinal_q", "0"))
        tamper("E1_SPHERE_MATH", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("pz_vertical_q", "0"))
        tamper("E1_SPHERE_NORM", lambda p: (
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("cos_alpha_q", "1"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("sin_alpha_q", "0"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("px_transverse_q", "0"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("py_longitudinal_q", "0"),
            p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("pz_vertical_q", "1"),
        ))
        tamper("E1_SPHERE_NORM", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("unit_norm_q", "2"))
        tamper("E1_SPHERE_DEC", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("px_transverse_dec6", "0.000000"))
        tamper("E1_SPHERE_DEC", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("py_longitudinal_dec6", "0.000000"))
        tamper("E1_SPHERE_DEC", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"][0].__setitem__("pz_vertical_dec6", "0.000000"))
        tamper("E1_SPHERE_DOM", lambda p: p["engine1_tusi_couple"]["spherical_hippopede_samples"].__setitem__(0, {
            "cos_alpha_q": "3/5", "sin_alpha_q": "4/5",
            "px_transverse_q": "768/3125", "px_transverse_dec6": "0.245760",
            "py_longitudinal_q": "-2976/3125", "py_longitudinal_dec6": "-0.952320",
            "pz_vertical_q": "113/625", "pz_vertical_dec6": "0.180800",
            "unit_norm_q": "1",
        }))

        # Engine 2 (incl. boundary & re-signed forgery regressions)
        tamper("E2_LIP", lambda p: (
            p["engine2_kashi_cubic_chords"].__setitem__("sexagesimal_p_unit_q", "1"),
            p["engine2_kashi_cubic_chords"].__setitem__("lipschitz_bound_q", "3/2500"),
        ))
        tamper("E2_LIP", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("lipschitz_bound_q", "1/2"))
        tamper("E2_LIP", lambda p: (
            p["engine2_kashi_cubic_chords"].__setitem__("domain_bound_q", "2/5"),
            p["engine2_kashi_cubic_chords"].__setitem__("lipschitz_bound_q", "16/25"),
        ))
        tamper("E2_SIN3", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("sin3_lo_dec12", "0.000000000000"))
        tamper("E2_SIN3", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("sin3_hi_dec12", "0.999999999999"))
        tamper("E2_ITER_LEN", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("banach_iterations", "1234"))
        tamper("E2_ITER_LEN", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("banach_iterations", []))
        tamper("E2_BRACKET", lambda p: p["engine2_kashi_cubic_chords"]["banach_iterations"][0].__setitem__("lo_dec12", "9.999999999999"))
        tamper("E2_BRACKET", lambda p: p["engine2_kashi_cubic_chords"]["banach_iterations"][0].__setitem__("hi_dec12", "9.999999999999"))
        tamper("E2_BRACKET", lambda p: p["engine2_kashi_cubic_chords"]["banach_iterations"][0].__setitem__("width_dec12", "999.000000000000"))
        tamper("E2_BRACKET", lambda p: p["engine2_kashi_cubic_chords"]["banach_iterations"][0].__setitem__("strict_shrink_factor_dec2", "0.00"))
        tamper("E2_SIN1", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("sin1_final_lo_dec12", "0.017452406430"))
        tamper("E2_SIN1", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("sin1_final_hi_dec12", "0.017452406439"))
        tamper("E2_WALL_LEN", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("cancellation_wall_schedule", "12345"))
        tamper("E2_WALL_LEN", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("cancellation_wall_schedule", []))
        tamper("E2_WALL_MATH", lambda p: p["engine2_kashi_cubic_chords"]["cancellation_wall_schedule"][0].__setitem__("bits_lost_naive", 5))
        tamper("E2_WALL_MATH", lambda p: p["engine2_kashi_cubic_chords"]["cancellation_wall_schedule"][0].__setitem__("exceeds_ieee754_53", True))
        tamper("E2_WALL_MATH", lambda p: p["engine2_kashi_cubic_chords"]["cancellation_wall_schedule"][0].__setitem__("reaches_s47_wmax_64", True))
        tamper("E2_WALL_DOM", lambda p: p["engine2_kashi_cubic_chords"]["cancellation_wall_schedule"].__setitem__(0, {
            "halving_step_k": 2, "bits_lost_naive": 6, "exceeds_ieee754_53": False, "reaches_s47_wmax_64": False,
        }))
        tamper("E2_CHORD_LEN", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("rationalized_chord_witnesses", "123"))
        tamper("E2_CHORD_LEN", lambda p: p["engine2_kashi_cubic_chords"].__setitem__("rationalized_chord_witnesses", []))
        tamper("E2_CHORD_MATH", lambda p: (
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_q", "0"),
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("s_q", "-2"),
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_next_sq_q", "0"),
        ))
        tamper("E2_CHORD_MATH", lambda p: (
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_q", "6/5"),
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("s_q", "-8/5"),
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_next_sq_q", "18/5"),
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_next_sq_dec6", "3.600000"),
        ))
        tamper("E2_CHORD_MATH", lambda p: (
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_q", "1"),
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("s_q", "1"),
            p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_next_sq_q", "1/3"),
        ))
        tamper("E2_CHORD_MATH", lambda p: p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_next_sq_q", "1"))
        tamper("E2_CHORD_DEC", lambda p: p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"][0].__setitem__("c_next_sq_dec6", "0.000000"))
        tamper("E2_CHORD_DOM", lambda p: p["engine2_kashi_cubic_chords"]["rationalized_chord_witnesses"].__setitem__(0, {
            "c_q": "8/5", "s_q": "6/5", "c_next_sq_q": "4/5", "c_next_sq_dec6": "0.800000",
        }))

        # Engine 3
        tamper("E3_TRICHOTOMY", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("flagship_exact_cos_summit_q", "1/2"))
        tamper("E3_TRICHOTOMY", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("euclidean_cos_summit_q", "1"))
        tamper("E3_TRICHOTOMY", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("spherical_obtuse_sign", "BAD"))
        tamper("E3_KLEIN_LEN", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("klein_hyperbolic_samples", "1234"))
        tamper("E3_KLEIN_LEN", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("klein_hyperbolic_samples", []))
        tamper("E3_DISK", lambda p: p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("disk_radius_sq_q", "1/3"))
        tamper("E3_DISK", lambda p: (
            p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("a_q", "1"),
            p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("h_q", "0"),
            p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("disk_radius_sq_q", "1"),
        ))
        tamper("E3_ACUTE", lambda p: p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("cos2_summit_q", "1/2"))
        tamper("E3_ACUTE", lambda p: (
            p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("a_q", "0"),
            p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("h_q", "1/2"),
            p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("disk_radius_sq_q", "1/4"),
            p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("cos2_summit_q", "0"),
        ))
        tamper("E3_DEC", lambda p: p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"][0].__setitem__("cos2_summit_dec6", "0.000000"))
        tamper("E3_KLEIN_DOM", lambda p: p["engine3_khayyam_curvature_cubics"]["klein_hyperbolic_samples"].__setitem__(0, {
            "a_q": "1/2", "h_q": "1/3", "disk_radius_sq_q": "13/36", "cos2_summit_q": "1/24", "cos2_summit_dec6": "0.041667",
        }))
        tamper("E3_CUBIC_LEN", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("cubic_discriminant_trichotomy", "12345"))
        tamper("E3_CUBIC_LEN", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("cubic_discriminant_trichotomy", []))
        tamper("E3_DISC_MATH", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"][0].__setitem__("discriminant", 0))
        tamper("E3_REGIME", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"][0].__setitem__("real_root_count", 999))
        tamper("E3_REGIME", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"][0].__setitem__("regime", "FAKE_REGIME"))
        tamper("E3_REGIME", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"][2].__setitem__("real_root_count", 1))
        tamper("E3_REGIME", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"][3].__setitem__("regime", "ONE_REAL_ROOT"))
        tamper("INVALID_STR", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"][0].__setitem__("label", 123))
        tamper("E3_CUBIC_DOM", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"][0].__setitem__("label", ""))
        tamper("E3_CUBIC_DOM", lambda p: p["engine3_khayyam_curvature_cubics"]["cubic_discriminant_trichotomy"].__setitem__(0, {
            "label": "x^3 + x - 1", "a": 2, "b": -1, "discriminant": -59, "real_root_count": 1, "regime": "ONE_REAL_ROOT",
        }))
        tamper("E3_MOD2_LEN", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("khayyam_x3_3x_1_mod2_obstruction", "123"))
        tamper("E3_MOD2_LEN", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("khayyam_x3_3x_1_mod2_obstruction", []))
        tamper("E3_MOD2_MATH", lambda p: (
            p["engine3_khayyam_curvature_cubics"]["khayyam_x3_3x_1_mod2_obstruction"][0].__setitem__("p_mod2", 0),
            p["engine3_khayyam_curvature_cubics"]["khayyam_x3_3x_1_mod2_obstruction"][0].__setitem__("q_mod2", 0),
        ))
        tamper("E3_MOD2_DOM", lambda p: (
            p["engine3_khayyam_curvature_cubics"]["khayyam_x3_3x_1_mod2_obstruction"].__setitem__(0, {"p_mod2": 1, "q_mod2": 0, "poly_mod2": 1}),
            p["engine3_khayyam_curvature_cubics"]["khayyam_x3_3x_1_mod2_obstruction"].__setitem__(1, {"p_mod2": 0, "q_mod2": 1, "poly_mod2": 1}),
        ))
        tamper("E3_MOD8_FLAG", lambda p: p["engine3_khayyam_curvature_cubics"].__setitem__("s33_all_even_q_residues_equal_4_mod8", False))

        # Engine 4 (incl. boundary & re-signed forgery regressions)
        tamper("E4_ALHAZEN_POLY", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("source_A", [0, 0]))
        tamper("E4_ALHAZEN_POLY", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("eye_B", [0, 0]))
        tamper("E4_ALHAZEN_POLY", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("quartic_coeffs", [1]))
        tamper("E4_ALHAZEN_POLY", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("primitive_quartic_coeffs", [1]))
        tamper("E4_ALHAZEN_POLY", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("ferrari_cubic_resolvent_coeffs", [1]))
        tamper("E4_ALHAZEN_POLY", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("galois_non_constructible_certified", False))
        tamper("E4_RRE_LEN", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("rational_root_exhaustion", "1234"))
        tamper("E4_RRE_LEN", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("rational_root_exhaustion", []))
        tamper("E4_RRE_MATH", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"]["rational_root_exhaustion"][0].__setitem__("value_q", "1"))
        tamper("E4_RRE_DOM", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"]["rational_root_exhaustion"].__setitem__(1, copy.deepcopy(p["engine4_haytham_farisi_biruni"]["alhazen_witness"]["rational_root_exhaustion"][0])))
        tamper("E4_ALHAZEN_MOD", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod3_residues", "123"))
        tamper("E4_ALHAZEN_MOD", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod3_residues", [1, 1]))
        tamper("INT_OUT_OF_RANGE", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod3_residues", [0, 1, 1]))
        tamper("E4_ALHAZEN_MOD", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod5_residues", "12345"))
        tamper("E4_ALHAZEN_MOD", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod5_residues", [1, 1]))
        tamper("INT_OUT_OF_RANGE", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod5_residues", [0, 1, 1, 1, 1]))
        tamper("E4_ALHAZEN_MOD_VAL", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod3_residues", [2, 2, 2]))
        tamper("E4_ALHAZEN_MOD_VAL", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("resolvent_mod5_residues", [1, 1, 1, 1, 1]))
        tamper("E4_CAUSTIC_PT", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_inside_point_q", "12"))
        tamper("E4_CAUSTIC_PT", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_inside_point_q", ["1/4"]))
        tamper("E4_CAUSTIC_PT", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_outside_point_q", "12"))
        tamper("E4_CAUSTIC_PT", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_outside_point_q", ["1/2"]))
        tamper("E4_CAUSTIC_PT", lambda p: (
            p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_inside_point_q", ["1/2", "1/2"]),
            p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_inside_val_q", "25/16"),
        ))
        tamper("E4_CAUSTIC_PT", lambda p: (
            p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_outside_point_q", ["1/4", "1/4"]),
            p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_outside_val_q", "-289/512"),
        ))
        tamper("E4_CAUSTIC", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_inside_val_q", "-999"))
        tamper("E4_CAUSTIC", lambda p: p["engine4_haytham_farisi_biruni"]["alhazen_witness"].__setitem__("astroid_outside_val_q", "999"))
        tamper("E4_FARISI_N", lambda p: p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"].__setitem__("water_index_n_q", "3/2"))
        tamper("E4_FARISI_LEN", lambda p: p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"].__setitem__("orders", "123"))
        tamper("E4_FARISI_LEN", lambda p: p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"].__setitem__("orders", []))
        tamper("E4_FARISI_MATH", lambda p: (
            p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"]["orders"][0].__setitem__("cos2_i_q", "1/2"),
            p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"]["orders"][0].__setitem__("cos2_i_dec6", "0.500000"),
        ))
        tamper("E4_FARISI_MATH", lambda p: p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"]["orders"][0].__setitem__("cos2_i_dec6", "0.000000"))
        tamper("E4_FARISI_GAP", lambda p: (
            p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"].__setitem__("alexander_dark_band_cos2_gap_q", "1/2"),
            p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"].__setitem__("alexander_dark_band_cos2_gap_dec6", "0.500000"),
        ))
        tamper("E4_FARISI_GAP", lambda p: p["engine4_haytham_farisi_biruni"]["al_farisi_rainbow"].__setitem__("alexander_dark_band_cos2_gap_dec6", "0.000000"))
        tamper("E4_BIRUNI_LEN", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("samples", "1234"))
        tamper("E4_BIRUNI_LEN", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("samples", []))
        tamper("E4_BIRUNI_MATH", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("t_half_dip_q", "-1/10"))
        tamper("E4_BIRUNI_MATH", lambda p: (
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("t_half_dip_q", "2"),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("r_over_h_q", "-3/8"),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("abs_dlnR_dlnt_q", "-2/3"),
        ))
        tamper("E4_BIRUNI_MATH", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("r_over_h_q", "1"))
        tamper("E4_BIRUNI_MATH", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("abs_dlnR_dlnt_q", "1"))
        tamper("E4_BIRUNI_DEC", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("r_over_h_dec4", "0.0000"))
        tamper("E4_BIRUNI_DEC", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"][0].__setitem__("abs_dlnR_dlnt_dec6", "0.000000"))
        tamper("E4_BIRUNI_DOM", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["samples"].__setitem__(0, {
            "t_half_dip_q": "1/20", "r_over_h_q": "399/2", "r_over_h_dec4": "199.5000",
            "abs_dlnR_dlnt_q": "800/399", "abs_dlnR_dlnt_dec6": "2.005013",
        }))
        def _bir_pole(t1_s: str, t2_s: str):
            t1v = verifier.parse_canonical_rational_str(t1_s, "t1")
            t2v = verifier.parse_canonical_rational_str(t2_s, "t2")
            r1v = (1 - t1v * t1v) / (2 * t1v * t1v)
            r2v = (1 - t2v * t2v) / (2 * t2v * t2v)
            rev = (r1v - r2v) / r2v
            amv = rev / ((t2v - t1v) / t2v)
            return oracle.fmt_q(rev), oracle.fmt_q(amv), oracle.fmt_dec_q(rev * 100, 2), oracle.fmt_dec_q(amv, 4)

        tamper("E4_BIRUNI_POLE", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_t1_q", "0"))
        re_neg, am_neg, rp_neg, ad_neg = _bir_pole("-1/200", self.cert["payload"]["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"]["nandana_t2_q"])
        tamper("E4_BIRUNI_POLE", lambda p: (
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_t1_q", "-1/200"),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_rel_radius_error_q", re_neg),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_amplification_ratio_q", am_neg),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_rel_radius_error_pct_dec2", rp_neg),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_amplification_ratio_dec4", ad_neg),
        ))
        re_t2, am_t2, rp_t2, ad_t2 = _bir_pole("1/200", "1/100")
        tamper("E4_BIRUNI_POLE", lambda p: (
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_t2_q", "1/100"),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_rel_radius_error_q", re_t2),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_amplification_ratio_q", am_t2),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_rel_radius_error_pct_dec2", rp_t2),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_amplification_ratio_dec4", ad_t2),
        ))
        tamper("E4_BIRUNI_POLE", lambda p: (
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_rel_radius_error_q", "1"),
            p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_amplification_ratio_q", "35"),
        ))
        tamper("E4_BIRUNI_POLE", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_amplification_ratio_q", "3"))
        tamper("E4_BIRUNI_PDEC", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_rel_radius_error_pct_dec2", "0.00"))
        tamper("E4_BIRUNI_PDEC", lambda p: p["engine4_haytham_farisi_biruni"]["al_biruni_geodesy_pole"].__setitem__("nandana_amplification_ratio_dec4", "0.0000"))

        # Engine 5 (incl. boundary & re-signed forgery regressions)
        tamper("E5_THABIT_LEN", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("thabit_amicable_cases", "1234"))
        tamper("E5_THABIT_LEN", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("thabit_amicable_cases", []))
        tamper("E5_THABIT_PQR", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("p", 99))
        tamper("E5_THABIT_PQR", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("q", 99))
        tamper("E5_THABIT_PQR", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("r", 99))
        tamper("E5_THABIT_AB", lambda p: (
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("A", 221),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("sigma_B_excess", -1),
        ))
        tamper("E5_THABIT_AB", lambda p: (
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("B", 285),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("sigma_B_excess", -1),
        ))
        tamper("E5_THABIT_AB", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("sigma_B_excess", 99))
        tamper("E5_THABIT_PRIME", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("p_prime", False))
        tamper("E5_THABIT_PRIME", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("q_prime", False))
        tamper("E5_THABIT_PRIME", lambda p: (
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("r_prime", True),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("sigma_A", 4320),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("sigma_B", 4320),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("amicable", True),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("sigma_B_excess", 0),
        ))
        tamper("E5_THABIT_SIGMA", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("sigma_A", 1))
        tamper("E5_THABIT_SIGMA", lambda p: (
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("sigma_B", 4320),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("sigma_B_excess", 0),
            p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("amicable", True),
        ))
        tamper("E5_THABIT_AM", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][0].__setitem__("amicable", False))
        tamper("E5_THABIT_AM", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"][1].__setitem__("amicable", True))
        # n=1: p=2, q=5, r=17 all prime, A=20, B=34, A+B=54, sA=42 != 54 while sB=54 == A+B
        tamper("E5_THABIT_AM", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"].__setitem__(1, {
            "n": 1, "p": 2, "q": 5, "r": 17,
            "p_prime": True, "q_prime": True, "r_prime": True,
            "A": 20, "B": 34, "sigma_A": 42, "sigma_B": 54,
            "amicable": True, "sigma_B_excess": 0,
        }))
        tamper("E5_THABIT_DOM", lambda p: p["engine5_thabit_khazini_nafis"]["thabit_amicable_cases"].__setitem__(1, {
            "n": 1, "p": 2, "q": 5, "r": 17,
            "p_prime": True, "q_prime": True, "r_prime": True,
            "A": 20, "B": 34, "sigma_A": 42, "sigma_B": 54,
            "amicable": False, "sigma_B_excess": 0,
        }))
        tamper("E5_THABIT_N3", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("thabit_n3_r_factorization", [1, 287]))
        tamper("INVALID_STR", lambda p: p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("pair", 123))
        tamper("E5_KHAZINI_DOM", lambda p: p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("pair", ""))

        tamper("E5_KHAZINI_LEN", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("khazini_alloy_inverse_cases", "123"))
        tamper("E5_KHAZINI_LEN", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("khazini_alloy_inverse_cases", []))
        tamper("E5_KHAZINI_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("s1_q", "0"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("s2_q", "-1"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("density_gap_q", "1"),
        ))
        tamper("E5_KHAZINI_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("s1_q", "2"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("s2_q", "-1"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("density_gap_q", "3"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("buoyancy_u_q", "1/2"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("perturbation_kappa_q", "-2/3"),
        ))
        tamper("E5_KHAZINI_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("s1_q", "2"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("s2_q", "4"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("density_gap_q", "-2"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("buoyancy_u_q", "7/4"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("perturbation_kappa_q", "-4"),
        ))
        tamper("E5_KHAZINI_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("density_gap_q", "1"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("perturbation_kappa_q", "39243/200"),
        ))
        tamper("E5_KHAZINI_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("recovered_w1_q", "4"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("buoyancy_u_q", oracle.fmt_q(Fraction(4, 1) / Fraction(381, 20) + Fraction(1, 1) / Fraction(103, 10))),
        ))
        tamper("E5_KHAZINI_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("recovered_w2_q", "2"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("buoyancy_u_q", oracle.fmt_q(Fraction(3, 1) / Fraction(381, 20) + Fraction(2, 1) / Fraction(103, 10))),
        ))
        tamper("E5_KHAZINI_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("recovered_w1_q", "-100"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("recovered_w2_q", "200"),
            p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("buoyancy_u_q", oracle.fmt_q(Fraction(-100, 1) / Fraction(381, 20) + Fraction(200, 1) / Fraction(103, 10))),
        ))
        tamper("E5_KHAZINI_MATH", lambda p: p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("buoyancy_u_q", "1"))
        tamper("E5_KHAZINI_MATH", lambda p: p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("perturbation_kappa_q", "1"))
        tamper("E5_KHAZINI_DEC", lambda p: p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"][0].__setitem__("perturbation_kappa_dec4", "0.0000"))
        tamper("E5_KHAZINI_DOM", lambda p: p["engine5_thabit_khazini_nafis"]["khazini_alloy_inverse_cases"].__setitem__(0, {
            "pair": "Gold/Silver", "s1_q": "10", "s2_q": "5", "density_gap_q": "5",
            "buoyancy_u_q": "1/2", "recovered_w1_q": "3", "recovered_w2_q": "1",
            "perturbation_kappa_q": "10", "perturbation_kappa_dec4": "10.0000",
        }))

        tamper("E5_NAFIS_GP", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("nafis_pulmonary_conductance_q", "0"))
        tamper("E5_NAFIS_GP", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("nafis_pulmonary_conductance_q", "2"))
        tamper("E5_NAFIS_LEN", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("nafis_septal_rerouting_cases", "1234"))
        tamper("E5_NAFIS_LEN", lambda p: p["engine5_thabit_khazini_nafis"].__setitem__("nafis_septal_rerouting_cases", []))
        tamper("E5_NAFIS_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("septal_pore_w_q", "-1/2"),
            p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("total_conductance_q", "1/2"),
            p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("pulmonary_fraction_q", "2"),
        ))
        tamper("E5_NAFIS_MATH", lambda p: (
            p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("total_conductance_q", "2"),
            p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("pulmonary_fraction_q", "1/2"),
        ))
        tamper("E5_NAFIS_MATH", lambda p: p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("pulmonary_fraction_q", "1/2"))
        tamper("E5_NAFIS_DEC", lambda p: p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("pulmonary_fraction_pct_dec2", "50.00"))
        tamper("E5_NAFIS_DEC", lambda p: p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"][0].__setitem__("septal_leak_fraction_pct_dec2", "50.00"))
        tamper("E5_NAFIS_DOM", lambda p: p["engine5_thabit_khazini_nafis"]["nafis_septal_rerouting_cases"].__setitem__(0, {
            "septal_pore_w_q": "3", "total_conductance_q": "4", "pulmonary_fraction_q": "1/4",
            "pulmonary_fraction_pct_dec2": "25.00", "septal_leak_fraction_pct_dec2": "75.00",
        }))

    def test_y_full_replay_and_fr0_pass(self) -> None:
        try:
            verifier.resolve_lean_binary()
            has_lean = True
        except oracle.S90Error:
            has_lean = False
        if has_lean or os.environ.get("ALETHEIA_REQUIRE_LEAN") == "1":
            r_full = verifier.verify_certificate_dict(self.cert, full_replay=True)
            self.assertTrue(r_full["valid"])
            self.assertTrue(r_full["full_replay"])
            self.assertIn("lean_live", r_full)
        else:
            self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.verify_certificate_dict, self.cert, full_replay=True)
            lean_sha = oracle.sha256_hex((_THIS_DIR / "HeritageExactOperators.lean").read_bytes())
            stub = {"lean_version": "4.36.0", "theorems_verified": len(oracle.LEAN_THEOREM_NAMES), "lean_source_sha256": lean_sha}
            with mock.patch.object(verifier, "verify_lean4_file_live", return_value=stub):
                r_full = verifier.verify_certificate_dict(self.cert, full_replay=True)
                self.assertTrue(r_full["valid"])
                self.assertTrue(r_full["full_replay"])
                self.assertIn("lean_live", r_full)

        r_fr0 = verifier.verify_certificate_dict(self.cert, full_replay=False)
        self.assertTrue(r_fr0["valid"])
        self.assertFalse(r_fr0["full_replay"])
        self.assertNotIn("lean_live", r_fr0)

    def test_z_cli_modes_and_rejections(self) -> None:
        def run_cli(argv) -> tuple[int, str, str]:
            out_buf = io.StringIO()
            err_buf = io.StringIO()
            with mock.patch.object(verifier.sys, "stdout", out_buf), mock.patch.object(verifier.sys, "stderr", err_buf):
                rc = verifier.main(argv)
            return rc, out_buf.getvalue(), err_buf.getvalue()

        with tempfile.TemporaryDirectory() as td:
            out_p = Path(td) / "cert.json"
            try:
                verifier.resolve_lean_binary()
                has_lean = True
            except oracle.S90Error:
                has_lean = False
            if has_lean or os.environ.get("ALETHEIA_REQUIRE_LEAN") == "1":
                rc, out, err = run_cli(["--check", str(_THIS_DIR / "s90_heritage_operators_certificate.json"), "--json"])
                self.assertEqual((rc, err), (0, ""))
                chk_obj = json.loads(out)
                self.assertTrue(chk_obj["valid"])
                live_receipt = chk_obj["lean_live"]
            else:
                rc, out, err = run_cli(["--check", str(_THIS_DIR / "s90_heritage_operators_certificate.json"), "--json"])
                self.assertEqual(rc, 2)
                self.assertEqual(out, "")
                self.assertEqual(json.loads(err)["code"], "LEAN_BINARY_UNAVAILABLE")
                live_receipt = {
                    "lean_version": "4.36.0",
                    "theorems_verified": len(oracle.LEAN_THEOREM_NAMES),
                    "lean_source_sha256": oracle.sha256_hex((_THIS_DIR / "HeritageExactOperators.lean").read_bytes()),
                }

            with mock.patch.object(verifier, "verify_lean4_file_live", return_value=live_receipt):
                rc, out, err = run_cli(["--write", str(out_p), "--json"])
                self.assertEqual((rc, err), (0, ""))
                self.assertEqual(stat.S_IMODE(os.lstat(out_p).st_mode), 0o600)
                self.assertTrue(json.loads(out)["written"])

                rc, out, err = run_cli(["--write=" + str(out_p)])
                self.assertEqual((rc, err), (0, ""))
                self.assertTrue(out.startswith("WROTE "))

                rc, out, err = run_cli(["--check=" + str(out_p)])
                self.assertEqual((rc, err), (0, ""))
                self.assertTrue(out.startswith("OK "))

                rc, out, err = run_cli(["--standalone"])
                self.assertEqual((rc, err), (0, ""))
                self.assertEqual(out.encode("ascii"), (_THIS_DIR / "s90_heritage_operators_certificate.json").read_bytes())

                for bad_tuple in (
                    ("0" * 64, verifier.PINNED_LEAN_TOOLCHAIN_SHA256, verifier.PINNED_LAKEFILE_SHA256, {}),
                    (verifier.PINNED_LEAN_SOURCE_SHA256, "0" * 64, verifier.PINNED_LAKEFILE_SHA256, {}),
                    (verifier.PINNED_LEAN_SOURCE_SHA256, verifier.PINNED_LEAN_TOOLCHAIN_SHA256, "0" * 64, {}),
                ):
                    with mock.patch.object(verifier, "_load_track_artifacts", return_value=bad_tuple):
                        rc, out, err = run_cli(["--standalone"])
                        self.assertEqual((rc, out), (2, ""))
                        self.assertEqual(json.loads(err)["code"], "PINNED_SHA_MISMATCH")

                rc, out, err = run_cli([])
                self.assertEqual((rc, err), (0, ""))
                self.assertTrue(out.startswith("OK "))

                rc, out, err = run_cli(["--json"])
                self.assertEqual((rc, err), (0, ""))
                self.assertTrue(json.loads(out)["valid"])

                with mock.patch.object(verifier.sys, "argv", ["verify_s90_heritage_operators.py", "--json"]):
                    rc, out, err = run_cli(None)
                    self.assertEqual((rc, err), (0, ""))
                    self.assertTrue(json.loads(out)["valid"])

            for bad_argv, code in (
                (123, "INVALID_ARGV"),
                (["--json", "--json"], "DUPLICATE_FLAG"),
                (["--standalone", "--check", str(out_p)], "CONFLICTING_MODE"),
                (["--check", str(out_p), "--standalone"], "CONFLICTING_MODE"),
                (["--check", str(out_p), "--write=" + str(out_p)], "CONFLICTING_MODE"),
                (["--check"], "MISSING_PATH_ARG"),
                (["--check", ""], "INVALID_PATH_ARG"),
                (["--check", "-bad"], "INVALID_PATH_ARG"),
                (["--check="], "INVALID_PATH_ARG"),
                (["--write=-bad"], "INVALID_PATH_ARG"),
                (["--unknown"], "UNKNOWN_FLAG"),
                (["--check\x00"], "NUL_BYTE_FORBIDDEN"),
                (["--check", "a\x00b"], "NUL_BYTE_FORBIDDEN"),
                (["--check", "\ud800"], "INVALID_UTF8_SURROGATE"),
            ):
                rc, out, err = run_cli(bad_argv)
                self.assertEqual(rc, 2, f"argv={bad_argv!r}")
                self.assertEqual(out, "")
                self.assertEqual(json.loads(err)["code"], code)
            self._assert_s90("NUL_BYTE_FORBIDDEN", verifier._parse_cli_args, ["--check", "a\x00b"])
            self.assertEqual(verifier._parse_cli_args([])["mode"], "default")


class Test05LeanGatesR12(unittest.TestCase):
    def _assert_s90(self, code: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(oracle.S90Error) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, code)

    def test_strip_and_r12_static_gate(self) -> None:
        lean_src = (_THIS_DIR / "HeritageExactOperators.lean").read_text(encoding="utf-8")
        verifier.static_gate_lean4_source(lean_src)
        # Clean controls must have zero false positives
        verifier.static_gate_lean4_source(lean_src + "\nprivate theorem _c1 : 1 = 1 := by decide (native := false)\n")
        verifier.static_gate_lean4_source(lean_src + "\nprivate theorem _c2 : 1 = 1 := by decide (native := Bool.false)\n")
        verifier.static_gate_lean4_source(lean_src + "\nprivate theorem _ctrl : 1 = 1 := by decide (config := { native := false })\n")
        verifier.static_gate_lean4_source(lean_src + "\nexport Nat (succ)\n")
        verifier.static_gate_lean4_source(lean_src + "\nprivate theorem init_eq : 1 = 1 := rfl\nattribute [simp] init_eq\n")

        stripped = verifier._strip_lean4_for_static_gate(
            "/- outer / - /- sorry -/ -/ -- axiom\n"
            "def x := a / b - c\n"
            "-- eof comment"
        )
        self.assertNotIn("sorry", stripped)
        self.assertNotIn("axiom", stripped)
        self.assertIn("a / b - c", stripped)
        s_dash = verifier._strip_lean4_for_static_gate("/- a - sorry -/\n")
        self.assertNotIn("sorry", s_dash)
        self.assertEqual(s_dash.strip(), "")
        s_slash = verifier._strip_lean4_for_static_gate("/- a / sorry -/\n")
        self.assertNotIn("sorry", s_slash)
        self.assertEqual(s_slash.strip(), "")
        self._assert_s90("LEAN4_UNTERMINATED_LEX", verifier._strip_lean4_for_static_gate, "/- unclosed")

        self._assert_s90("LEAN4_BAD_CHARS", verifier.static_gate_lean4_source, lean_src + "\r")
        self._assert_s90("LEAN4_BAD_CHARS", verifier.static_gate_lean4_source, lean_src + "\x00")

        for escape in (
            "\nsorry\n",
            "\nadmit\n",
            "\naxiom bad : Prop\n",
            "\nunsafe def u := 0\n",
            "\nnoncomputable def nc : Nat := 0\n",
            "\nprelude\n",
            "\ntheorem t : True := by native_decide\n",
            "\ntheorem t : True := by decide_cbv\n",
            "\ndef s := sorryAx\n",
            "\nset_option debug.skipKernelTC true\n",
            "\nset_option debug.byAsSorry true\n",
            "\nset_option debug.terminalTacticsAsSorry true\n",
            "\nset_option warn.sorry false\n",
            "\nset_option maxHeartbeats 0\n",
            "\ntheorem t : True := by bv_decide\n",
            "\nopen Classical in theorem evil_cl : True := by trivial\n",
            "\ndef evil_ch := @Classical.choice True ⟨trivial⟩\n",
            "\n#guard true\n",
            "\n#guard_msgs in theorem _gm : True := trivial\n",
            "\nset_option «debug».«skipKernelTC» true\n",
            "\n@[extern \"c_fn\"] def f : Nat := 0\n",
            "\nattribute [implemented_by f] g\n",
            "\n@[csimp] theorem c : True := trivial\n",
            "\n@[init] def h1 : IO Unit := pure ()\n",
            "\n@[builtin_init] def h2 : IO Unit := pure ()\n",
            "\nattribute [init] h1\n",
            "\nattribute [builtin_init] h2\n",
            "\n@[export bad_c_sym] def h3 : Nat := 0\n",
            "\nattribute [export bad_c_sym] h3\n",
            "\n@[term_elab bad] def h4 : Nat := 0\n",
            "\n@[command_elab bad] def h5 : Nat := 0\n",
            "\n@[tactic bad] def h6 : Nat := 0\n",
            "\n@[builtin_tactic bad] def h6b : Nat := 0\n",
            "\n@[macro bad] def h7 : Nat := 0\n",
            "\n@[macro_rules] def h8 : Nat := 0\n",
            "\nopaque hidden : Nat := 0\n",
            "\npartial def loop : Nat := loop\n",
            "\ndef dt1 := dbgTrace (toString 1) (fun _ => 0)\n",
            "\ndef dt2 := dbgTraceVal 1\n",
            "\ndef dt3 := dbgTraceValId 1\n",
            "\ndef dt4 := dbgTraceIfShared (toString 1) 0\n",
            "\ndef dt5 := dbgSleep 1 (fun _ => 0)\n",
            "\ndef dt6 := dbgStackTrace (fun _ => 0)\n",
            "\ndef dt7 := dbg_sleep 1\n",
            "\ndef dt8 := dbg_stack_trace\n",
            "\ndef dp1 : Nat := panic! (toString 1)\n",
            "\ndef dp2 : Nat := panicCore (toString 1)\n",
            "\ndef dp3 : Nat := panicWithPos (toString 1) 0 0 (toString 1)\n",
            "\ndef dp4 : Nat := panicWithPosWithDecl (toString 1) (toString 1) 0 0 (toString 1)\n",
            "\ndef dp5 : Nat := unreachable!\n",
            "\ndef dp6 : Nat := assert! true; 0\n",
            "\ndef dp7 : Nat := debug_assert! true; 0\n",
            "\ntheorem t : True := by decide +native\n",
            "\nprivate theorem _e1 : 1 = 1 := by decide -revert +native\n",
            "\nprivate theorem _e2 : 1 = 1 := by decide +revert +native\n",
            "\nprivate theorem _e3 : 1 = 1 := by decide -kernel +native\n",
            "\ntheorem t : 1 + 1 = 2 := by decide (native := false || true)\n",
            "\ntheorem t : 1 + 1 = 2 := by decide (native := false == false)\n",
            "\ntheorem t : 1 + 1 = 2 := by decide (native := false != true)\n",
            "\ntheorem t : 1 + 1 = 2 := by decide (native := false.not)\n",
            "\ntheorem t : 1 + 1 = 2 := by decide (native := Bool.false || true)\n",
            "\ntheorem t : 1 + 1 = 2 := by decide (native := false\n  || true)\n",
            "\ntheorem t : 1 = 1 := by decide (config := { native := false || true })\n",
            "\ntheorem t : 1 = 1 := by decide (config := myCfg)\n",
            "\ndef native : Bool := true\ntheorem t : 1 = 1 := by decide +revert (config := { native })\n",
            "\ndef native : Bool := true\ntheorem t : 1 = 1 := by decide (revert := false) (config := { native })\n",
            "\ndef native : Bool := true\ntheorem t : 1 = 1 := by decide +revert (config := { ({} : _) with native })\n",
            "\ndef cfg : DecideConfig := {}\n",
            "\ntheorem t : True := by decide (native := !false)\n",
            "\n#eval 1 + 1\n",
            "\n#reduce 1\n",
            "\n#exit\n",
            "\n#print Nat\n",
            "\nimport Mathlib\n",
            "\nimport Std\n",
            "\nmacro \"bad\" : term => `(sorry)\n",
            "\nmacro_rules | `(bad) => `(sorry)\n",
            "\nelab \"bad\" : command => pure ()\n",
            "\nsyntax \"bad\" : term\n",
            "\ndeclare_syntax_cat evil\n",
            '\nnotation "openq\\"" => 0\n',
            '\ndef x := s!"{(by sorry : String)}"\n',
            '\ndef x := f!"{(by sorry : String)}"\n',
            '\ndef _a := r#"""#\naxiom evil : False\ndef _b := r#"""#\n',
            "\ndef q1 : Char := '\"'\n#eval 1\ndef q2 : Char := '\"'\n",
            '\ndbg_trace "{(by sorry : Nat)}"\n',
            "\ntheorem t : False := by «sorry»\n",
        ):
            self._assert_s90("LEAN4_TRUST_ESCAPE", verifier.static_gate_lean4_source, lean_src + escape)

        self._assert_s90(
            "LEAN4_MISSING_THEOREM",
            verifier.static_gate_lean4_source,
            lean_src.replace("theorem tusi_planar_curl_annihilation", "theorem renamed_thm"),
        )
        self._assert_s90(
            "LEAN4_MISSING_PRINT_AXIOMS",
            verifier.static_gate_lean4_source,
            lean_src.replace("#print axioms HeritageExactOperators.tusi_planar_curl_annihilation", ""),
        )

    def test_resolve_and_verify_lean_live_and_mocked(self) -> None:
        try:
            verifier.resolve_lean_binary()
            has_lean = True
        except oracle.S90Error:
            has_lean = False
        if has_lean or os.environ.get("ALETHEIA_REQUIRE_LEAN") == "1":
            live = verifier.verify_lean4_file_live(_THIS_DIR / "HeritageExactOperators.lean")
            self.assertEqual(live["theorems_verified"], len(oracle.LEAN_THEOREM_NAMES))
            self.assertIn("4.36.0", live["lean_version"])
        else:
            self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.verify_lean4_file_live, _THIS_DIR / "HeritageExactOperators.lean")

        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "lean"
            fake_bin.write_text("#!/bin/sh\n", encoding="utf-8")
            os.chmod(fake_bin, 0o700)
            noexec_bin = Path(td) / "lean_noexec"
            noexec_bin.write_text("#!/bin/sh\n", encoding="utf-8")
            os.chmod(noexec_bin, 0o600)
            dir_bin = Path(td) / "lean_dir"
            dir_bin.mkdir(mode=0o700)
            with mock.patch.dict(os.environ, {"ALETHEIA_LEAN_BIN": str(fake_bin)}):
                self.assertEqual(verifier.resolve_lean_binary(), str(fake_bin))
            with mock.patch.dict(os.environ, {"ALETHEIA_LEAN_BIN": str(Path(td) / "missing")}):
                self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.resolve_lean_binary)
            with mock.patch.dict(os.environ, {"ALETHEIA_LEAN_BIN": str(noexec_bin)}):
                self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.resolve_lean_binary)
            with mock.patch.dict(os.environ, {"ALETHEIA_LEAN_BIN": str(dir_bin)}):
                self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.resolve_lean_binary)

            home_d = Path(td) / "h"
            (home_d / ".local" / "bin" / "lean").mkdir(parents=True)
            (home_d / ".elan" / "bin").mkdir(parents=True)
            elan_lean = home_d / ".elan" / "bin" / "lean"
            elan_lean.write_text("#!/bin/sh\n", encoding="utf-8")
            os.chmod(elan_lean, 0o600)
            with mock.patch.dict(os.environ, {"HOME": str(home_d)}, clear=True):
                with mock.patch.object(verifier.shutil, "which", return_value=str(fake_bin)):
                    self.assertEqual(verifier.resolve_lean_binary(), str(fake_bin))
                with mock.patch.object(verifier.shutil, "which", return_value=str(noexec_bin)):
                    self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.resolve_lean_binary)
                os.chmod(elan_lean, 0o700)
                with mock.patch.object(verifier.shutil, "which", return_value=None):
                    self.assertEqual(verifier.resolve_lean_binary(), str(elan_lean))
                os.unlink(elan_lean)
                with mock.patch.object(verifier.shutil, "which", return_value=None):
                    self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.resolve_lean_binary)
            elan_lean.write_text("#!/bin/sh\n", encoding="utf-8")
            os.chmod(elan_lean, 0o700)
            old_cwd = os.getcwd()
            try:
                os.chdir(home_d)
                with mock.patch.dict(os.environ, {"HOME": ""}, clear=True):
                    with mock.patch.object(verifier.shutil, "which", return_value=None):
                        self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.resolve_lean_binary)
            finally:
                os.chdir(old_cwd)
            os.unlink(elan_lean)
            with mock.patch.dict(os.environ, {}, clear=True):
                with mock.patch.object(verifier.shutil, "which", return_value=None):
                    self._assert_s90("LEAN_BINARY_UNAVAILABLE", verifier.resolve_lean_binary)

            bad_utf8 = Path(td) / "bad.lean"
            bad_utf8.write_bytes(b"\xff\xfe")
            self._assert_s90("INVALID_UTF8", verifier.verify_lean4_file_live, bad_utf8)

            base_lean = (_THIS_DIR / "HeritageExactOperators.lean").read_text(encoding="utf-8")
            for idx_e, exploit_tail in enumerate((
                "\nprivate theorem _e1 : 1 = 1 := by decide -revert +native\n",
                "\ndef q1 : Char := '\"'\n#eval 1\ndef q2 : Char := '\"'\n",
                "\nset_option «debug».«skipKernelTC» true\n",
            )):
                exp_p = Path(td) / f"exp_{idx_e}.lean"
                exp_p.write_text(base_lean + exploit_tail, encoding="utf-8")
                self._assert_s90("LEAN4_TRUST_ESCAPE", verifier.verify_lean4_file_live, exp_p)

        lean_path = _THIS_DIR / "HeritageExactOperators.lean"
        ok_ver = subprocess.CompletedProcess(["lean", "--version"], 0, "Lean (version 4.36.0, x86_64)\n", "")

        def run_mock(ver_res, comp_res):
            seq = [ver_res, comp_res]

            def side_eff(*a, **kw):
                item = seq.pop(0)
                if isinstance(item, BaseException):
                    raise item
                return item

            return mock.patch.object(verifier.subprocess, "run", side_effect=side_eff)

        with mock.patch.object(verifier, "resolve_lean_binary", return_value="lean"):
            with run_mock(OSError("no"), ok_ver):
                self._assert_s90("LEAN_EXEC_ERROR", verifier.verify_lean4_file_live, lean_path)
            with run_mock(subprocess.CompletedProcess(["lean"], 0, "Lean (version 4.10.0)\n", ""), ok_ver):
                self._assert_s90("LEAN_VERSION_MISMATCH", verifier.verify_lean4_file_live, lean_path)
            with run_mock(subprocess.CompletedProcess(["lean"], 1, "Lean (version 4.36.0)\n", ""), ok_ver):
                self._assert_s90("LEAN_VERSION_MISMATCH", verifier.verify_lean4_file_live, lean_path)
            with run_mock(ok_ver, subprocess.TimeoutExpired(["lean"], 120)):
                self._assert_s90("LEAN_EXEC_ERROR", verifier.verify_lean4_file_live, lean_path)
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 1, "", "")):
                self._assert_s90("LEAN_COMPILE_FAIL", verifier.verify_lean4_file_live, lean_path)
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, "", "err")):
                self._assert_s90("LEAN_STDERR_NONEMPTY", verifier.verify_lean4_file_live, lean_path)
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, "warning: unused\n", "")):
                self._assert_s90("LEAN_WARNING_FORBIDDEN", verifier.verify_lean4_file_live, lean_path)
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, "weird line\n", "")):
                self._assert_s90("LEAN_UNEXPECTED_STDOUT", verifier.verify_lean4_file_live, lean_path)

            lines_ok = [f"'{oracle.LEAN_THEOREM_NAMES[0]}' does not depend on any axioms", ""]
            lines_ok.append(f"'{oracle.LEAN_THEOREM_NAMES[1]}' depends on axioms: []")
            lines_ok.append(f"'{oracle.LEAN_THEOREM_NAMES[2]}' depends on axioms: [propext,")
            lines_ok.append("  ,")
            lines_ok.append("  Quot.sound]")
            for t in oracle.LEAN_THEOREM_NAMES[3:]:
                lines_ok.append(f"'{t}' depends on axioms: [propext, Quot.sound]")
            captured_envs: list[dict[str, str]] = []

            def run_env_capture(*a, **kw):
                captured_envs.append(kw.get("env"))
                if "--version" in a[0]:
                    return ok_ver
                return subprocess.CompletedProcess(["lean"], 0, "\n".join(lines_ok) + "\n", "")

            poisoned_env = {
                "PATH": "/usr/bin",
                "LEAN_PATH": "/tmp/evil_lean",
                "LEAN_OPTS": "-Ddebug.skipKernelTC=true",
                "LEAN_CC": "/tmp/evil_cc",
                "ELAN_HOME": "/tmp/evil_elan",
                "LAKE_HOME": "/tmp/evil_lake",
                "LD_PRELOAD": "/tmp/evil.so",
                "LD_LIBRARY_PATH": "/tmp/evil_lib",
            }
            with mock.patch.dict(os.environ, poisoned_env, clear=True), mock.patch.object(
                verifier.subprocess, "run", side_effect=run_env_capture
            ):
                res = verifier.verify_lean4_file_live(lean_path)
                self.assertEqual(res["theorems_verified"], len(oracle.LEAN_THEOREM_NAMES))
            self.assertEqual(len(captured_envs), 2)
            self.assertEqual(captured_envs[0], {"PATH": "/usr/bin"})
            self.assertEqual(captured_envs[1], {"PATH": "/usr/bin"})

            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, f"'{oracle.LEAN_THEOREM_NAMES[0]}' depends on axioms: [propext,\n", "")):
                self._assert_s90("LEAN_UNEXPECTED_STDOUT", verifier.verify_lean4_file_live, lean_path)
            dup_none = f"'{oracle.LEAN_THEOREM_NAMES[0]}' does not depend on any axioms\n" * 2
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, dup_none, "")):
                self._assert_s90("LEAN_DUPLICATE_THEOREM", verifier.verify_lean4_file_live, lean_path)
            dup_dep = f"'{oracle.LEAN_THEOREM_NAMES[0]}' depends on axioms: [propext]\n" * 2
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, dup_dep, "")):
                self._assert_s90("LEAN_DUPLICATE_THEOREM", verifier.verify_lean4_file_live, lean_path)

            bad_ax = f"'{oracle.LEAN_THEOREM_NAMES[0]}' depends on axioms: [Classical.choice]\n"
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, bad_ax, "")):
                self._assert_s90("LEAN_FORBIDDEN_AXIOM", verifier.verify_lean4_file_live, lean_path)
            with run_mock(ok_ver, subprocess.CompletedProcess(["lean"], 0, "\n".join(lines_ok[:-1]) + "\n", "")):
                self._assert_s90("LEAN_THEOREM_SET_MISMATCH", verifier.verify_lean4_file_live, lean_path)


if __name__ == "__main__":
    unittest.main()
