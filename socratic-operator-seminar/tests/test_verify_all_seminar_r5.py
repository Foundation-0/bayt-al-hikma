#!/usr/bin/env python3
"""Pure-Stdlib Assertion-Free R5 Test Suite for verify_all_seminar.py."""

from __future__ import annotations

import copy
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SEMINAR_DIR = Path(__file__).resolve().parent.parent
if str(SEMINAR_DIR) not in sys.path:
    sys.path.insert(0, str(SEMINAR_DIR))

import verify_all_seminar as vas  # noqa: E402


class TestVerifyAllSeminarR5(unittest.TestCase):
    def _assert_err(self, code: str, fn: object, *args: object, **kwargs: object) -> None:
        if not callable(fn):
            self.fail("fn must be callable")
        with self.assertRaises(vas.SeminarAllError) as cm:
            fn(*args, **kwargs)
        self.assertEqual(cm.exception.code, code)

    def test_01_live_manifest_pillar_pins_and_unified_certificate(self) -> None:
        pin_info = vas.verify_pinned_manifest_and_pillars(SEMINAR_DIR)
        self.assertEqual(pin_info["manifest_file_sha256"], vas.PINNED_MANIFEST_SHA256)
        self.assertEqual(pin_info["manifest_files_verified"], 42)
        self.assertEqual(pin_info["pillar_files_verified"], 8)

        buf = io.StringIO()
        with mock.patch("sys.stdout", buf):
            rc = vas.main(["--json"])
        self.assertEqual(rc, 0)
        parsed = json.loads(buf.getvalue())
        self.assertTrue(parsed["all_passed"])
        self.assertEqual(parsed["pillars_passed"], 4)
        self.assertEqual(parsed["pillars_total"], 4)
        cert_path = SEMINAR_DIR.joinpath("certificates", "seminar_unified_certificate.json")
        if cert_path.is_file():
            self.assertEqual(buf.getvalue().encode("utf-8"), cert_path.read_bytes())

    def test_02_regular_file_symlink_fifo_size_and_json_guards(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            f = tmp.joinpath("ok.json")
            f.write_bytes(b'{"a": 1}\n')
            self.assertEqual(vas.read_regular_file_bytes(f, max_bytes=9), b'{"a": 1}\n')

            # Leaf, parent, and grandparent symlinks
            sym_leaf = tmp.joinpath("sym.json")
            sym_leaf.symlink_to(f)
            self._assert_err("SYMLINK_FORBIDDEN", vas.read_regular_file_bytes, sym_leaf)

            real_gp = tmp.joinpath("real_gp")
            real_gp.joinpath("sub").mkdir(parents=True)
            real_gp.joinpath("sub", "x.json").write_bytes(b"{}\n")
            gp_sym = tmp.joinpath("gp_sym")
            gp_sym.symlink_to(real_gp)
            self._assert_err("SYMLINK_FORBIDDEN", vas.read_regular_file_bytes, gp_sym.joinpath("sub", "x.json"))

            # FIFO refused immediately
            fifo = tmp.joinpath("pipe.json")
            os.mkfifo(fifo)
            self._assert_err("NOT_REGULAR_FILE", vas.read_regular_file_bytes, fifo)

            # Missing file
            self._assert_err("MISSING_CUSTOM", vas.read_regular_file_bytes, tmp.joinpath("absent.json"), "MISSING_CUSTOM")

            # O(1) st_size cap & streaming overflow cap
            big = tmp.joinpath("big.json")
            big.write_bytes(b"{" + b" " * 100 + b"}")
            with mock.patch.object(vas.os, "read", side_effect=AssertionError("st_size must reject before read")):
                self._assert_err("FILE_TOO_LARGE", vas.read_regular_file_bytes, big, "MISSING_FILE", 64)
            fake_st = os.stat(big)
            with mock.patch.object(vas.os, "fstat", return_value=type("S", (), {"st_mode": fake_st.st_mode, "st_size": 10})()):
                self._assert_err("FILE_TOO_LARGE", vas.read_regular_file_bytes, big, "MISSING_FILE", 64)

            # ELOOP, open OSError, and read OSError
            with mock.patch.object(vas.os, "open", side_effect=OSError(errno.ELOOP, "loop")):
                self._assert_err("SYMLINK_FORBIDDEN", vas.read_regular_file_bytes, big)
            with mock.patch.object(vas.os, "open", side_effect=OSError(errno.EACCES, "denied")):
                self._assert_err("READ_ERROR", vas.read_regular_file_bytes, big)
            with mock.patch.object(vas.os, "read", side_effect=OSError(errno.EIO, "io")):
                self._assert_err("READ_ERROR", vas.read_regular_file_bytes, big)

            # Strict JSON controls
            self.assertEqual(vas.loads_strict_json_bytes(b'{"k": 1}', "ok"), {"k": 1})
            self.assertEqual(vas.MAX_JSON_DEPTH, 32)
            deep32 = b"[" * vas.MAX_JSON_DEPTH + b"1" + b"]" * vas.MAX_JSON_DEPTH
            self.assertIsInstance(vas.loads_strict_json_bytes(deep32, "ok32"), list)
            str_braces = b'{"s":"' + b"{" * 40 + b'\\"{[\\\\"}'
            self.assertEqual(vas.loads_strict_json_bytes(str_braces, "braces")["s"][:2], "{{")
            with mock.patch.object(vas.json, "loads", side_effect=AssertionError("pre-parse depth check must reject before json.loads")):
                self._assert_err(
                    "JSON_DEPTH",
                    vas.loads_strict_json_bytes,
                    b"[" * (vas.MAX_JSON_DEPTH + 1) + b"1" + b"]" * (vas.MAX_JSON_DEPTH + 1),
                    "deep33",
                )
            with mock.patch.object(vas.json, "loads", side_effect=RecursionError("deep")):
                self._assert_err("JSON_DEPTH", vas.loads_strict_json_bytes, b'{"a":1}', "rec")
            self.assertEqual(vas._parse_bounded_int("9" * vas.MAX_JSON_INT_DIGITS), int("9" * vas.MAX_JSON_INT_DIGITS))
            self._assert_err("DUPLICATE_JSON_KEY", vas.loads_strict_json_bytes, b'{"a":1,"a":2}', "dup")
            self._assert_err("FLOAT_FORBIDDEN", vas.loads_strict_json_bytes, b'{"a":1.5}', "flt")
            self._assert_err("NONFINITE_JSON", vas.loads_strict_json_bytes, b'{"a":NaN}', "nan")
            self._assert_err("JSON_INT_TOO_LARGE", vas.loads_strict_json_bytes, b'{"a":' + b"9" * 4400 + b"}", "big")
            self._assert_err("BAD_JSON", vas.loads_strict_json_bytes, b"\xff\xfe", "utf8")
            self._assert_err("BAD_JSON", vas.loads_strict_json_bytes, b"{bad", "bad")

    def test_03_manifest_and_pillar_tamper_refusals(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._assert_err("MISSING_MANIFEST", vas.verify_pinned_manifest_and_pillars, root)

            def write_m(obj: object) -> str:
                raw = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")
                root.joinpath("SEMINAR_MANIFEST.json").write_bytes(raw)
                return hashlib.sha256(raw).hexdigest()

            def signed_m(files: dict[str, dict[str, object]], **extra: object) -> str:
                body: dict[str, object] = {
                    "schema": vas.SCHEMA_MANIFEST,
                    "file_count": len(files),
                    "files": files,
                    **extra,
                }
                canon = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
                body["manifest_sha256"] = hashlib.sha256(canon).hexdigest()
                return write_m(body)

            # Wrong raw SHA
            write_m({"schema": vas.SCHEMA_MANIFEST})
            self._assert_err("MANIFEST_SHA256_MISMATCH", vas.verify_pinned_manifest_and_pillars, root, "0" * 64)

            # Non-dict manifest
            sha_list = write_m([1, 2])
            self._assert_err("BAD_MANIFEST", vas.verify_pinned_manifest_and_pillars, root, sha_list)

            # Wrong schema
            sha_bad_sc = write_m({"schema": "wrong"})
            self._assert_err("BAD_MANIFEST_SCHEMA", vas.verify_pinned_manifest_and_pillars, root, sha_bad_sc)

            # Bad self-hash (wrong value & non-str)
            sha_bad_sh = write_m({"schema": vas.SCHEMA_MANIFEST, "manifest_sha256": "0" * 64})
            self._assert_err("MANIFEST_SELF_HASH_MISMATCH", vas.verify_pinned_manifest_and_pillars, root, sha_bad_sh)
            sha_non_str = write_m({"schema": vas.SCHEMA_MANIFEST, "manifest_sha256": 123})
            self._assert_err("MANIFEST_SELF_HASH_MISMATCH", vas.verify_pinned_manifest_and_pillars, root, sha_non_str)

            # Empty / mismatched file_count / non-dict files
            sha_empty = signed_m({})
            self._assert_err("BAD_MANIFEST_FILES", vas.verify_pinned_manifest_and_pillars, root, sha_empty)
            sha_cnt = signed_m({"a.txt": {"sha256": "0" * 64, "bytes": 1}}, file_count=2)
            self._assert_err("BAD_MANIFEST_FILES", vas.verify_pinned_manifest_and_pillars, root, sha_cnt)
            bad_files_body = {"schema": vas.SCHEMA_MANIFEST, "file_count": 1, "files": ["bad"]}
            bad_files_body["manifest_sha256"] = hashlib.sha256(
                json.dumps(bad_files_body, sort_keys=True, separators=(",", ":")).encode("ascii")
            ).hexdigest()
            sha_nf = write_m(bad_files_body)
            self._assert_err("BAD_MANIFEST_FILES", vas.verify_pinned_manifest_and_pillars, root, sha_nf)

            # Malformed entry
            for bad_meta in ("bad", {"sha256": 123, "bytes": 1}, {"sha256": "0" * 64, "bytes": "1"}):
                sha_me = signed_m({"a.txt": bad_meta})  # type: ignore[dict-item]
                self._assert_err("BAD_MANIFEST_ENTRY", vas.verify_pinned_manifest_and_pillars, root, sha_me)

            # Valid file entry checks: missing, size drift, sha drift, pillar missing, pillar drift
            f_a = root.joinpath("a.txt")
            f_a.write_bytes(b"hello")
            sha_a = hashlib.sha256(b"hello").hexdigest()

            sha_miss_f = signed_m({"missing.txt": {"sha256": sha_a, "bytes": 5}})
            self._assert_err("MISSING_MANIFEST_FILE", vas.verify_pinned_manifest_and_pillars, root, sha_miss_f, {})

            sha_sz = signed_m({"a.txt": {"sha256": sha_a, "bytes": 6}})
            self._assert_err("MANIFEST_SIZE_MISMATCH", vas.verify_pinned_manifest_and_pillars, root, sha_sz, {})

            sha_dr = signed_m({"a.txt": {"sha256": "0" * 64, "bytes": 5}})
            self._assert_err("MANIFEST_FILE_SHA256_MISMATCH", vas.verify_pinned_manifest_and_pillars, root, sha_dr, {})

            sha_ok = signed_m({"a.txt": {"sha256": sha_a, "bytes": 5}})
            self._assert_err("PILLAR_NOT_IN_MANIFEST", vas.verify_pinned_manifest_and_pillars, root, sha_ok, {"b.txt": sha_a})
            self._assert_err("PILLAR_SHA256_MISMATCH", vas.verify_pinned_manifest_and_pillars, root, sha_ok, {"a.txt": "0" * 64})
            ok = vas.verify_pinned_manifest_and_pillars(root, sha_ok, {"a.txt": sha_a})
            self.assertEqual(ok["pillar_files_verified"], 1)

    def test_04_flag_forwarding_and_cli_fail_paths(self) -> None:
        fake_flags_o1 = type("F", (), {"optimize": 1})()
        with mock.patch.object(vas.sys, "flags", fake_flags_o1), mock.patch.object(vas.sys, "warnoptions", ["error"]):
            self.assertEqual(vas._child_python_flags(), ["-I", "-B", "-O", "-W", "error"])
        fake_flags_o2 = type("F", (), {"optimize": 2})()
        with mock.patch.object(vas.sys, "flags", fake_flags_o2), mock.patch.object(vas.sys, "warnoptions", []):
            self.assertEqual(vas._child_python_flags(), ["-I", "-B", "-OO"])
        fake_flags_o0 = type("F", (), {"optimize": 0})()
        with mock.patch.object(vas.sys, "flags", fake_flags_o0), mock.patch.object(vas.sys, "warnoptions", []):
            self.assertEqual(vas._child_python_flags(), ["-I", "-B"])

        # Mocked runner verifying PASS & FAIL text/JSON CLI paths and --live-lean forwarding
        seen_cmds: list[list[str]] = []

        def fake_runner_ok(args: list[str], cwd: Path) -> dict[str, object]:
            seen_cmds.append(list(args))
            return {"args": list(args), "rc": 0, "stdout": "ok", "stderr": ""}

        res_live = vas.run_all_pillars(SEMINAR_DIR, live_lean=True, runner=fake_runner_ok)
        self.assertTrue(res_live["all_passed"])
        self.assertIn("--live-lean", seen_cmds[-1])

        def fake_runner_fail(args: list[str], cwd: Path) -> dict[str, object]:
            rc = 2 if "verify_pilot1_theorems.py" in args else 0
            return {"args": list(args), "rc": rc, "stdout": "", "stderr": "err" if rc else ""}

        res_fail = vas.run_all_pillars(SEMINAR_DIR, live_lean=False, runner=fake_runner_fail)
        self.assertFalse(res_fail["all_passed"])
        self.assertEqual(res_fail["pillars_passed"], 3)

        buf_txt = io.StringIO()
        with mock.patch.object(vas, "run_all_pillars", return_value=res_fail), mock.patch("sys.stdout", buf_txt):
            self.assertEqual(vas.main([]), 2)
        self.assertIn("[FAIL] pilot1_theorems", buf_txt.getvalue())
        self.assertIn("ALL_PASSED=False", buf_txt.getvalue())

        buf_ok = io.StringIO()
        with mock.patch.object(vas, "run_all_pillars", return_value=res_live), mock.patch("sys.stdout", buf_ok):
            self.assertEqual(vas.main([]), 0)
        self.assertIn("ALL_PASSED=True", buf_ok.getvalue())

        err_buf = io.StringIO()
        with mock.patch.object(vas, "run_all_pillars", side_effect=vas.SeminarAllError("MANIFEST_SHA256_MISMATCH", "bad")), mock.patch("sys.stderr", err_buf):
            self.assertEqual(vas.main(["--json"]), 2)
        self.assertEqual(json.loads(err_buf.getvalue())["error_code"], "MANIFEST_SHA256_MISMATCH")

        err_io = io.StringIO()
        with mock.patch.object(vas, "run_all_pillars", side_effect=OSError("io fail")), mock.patch("sys.stderr", err_io):
            self.assertEqual(vas.main(["--json"]), 2)
        self.assertEqual(json.loads(err_io.getvalue())["error_code"], "IO_ERROR")

        with tempfile.TemporaryDirectory() as td_sym:
            sym_runner = Path(td_sym, "sym_verify_all.py")
            sym_runner.symlink_to(SEMINAR_DIR.joinpath("verify_all_seminar.py"))
            proc = subprocess.run(
                [sys.executable, "-I", "-B", str(sym_runner), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertNotIn("Traceback", proc.stderr)
            self.assertEqual(json.loads(proc.stderr)["error_code"], "SYMLINK_FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
