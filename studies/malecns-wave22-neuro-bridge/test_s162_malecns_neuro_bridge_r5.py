#!/usr/bin/env python3
"""Track S162 (EXP-Q43a & EXP-Q43b) R5 Assertion-Free Verification Test Suite
(0 bare asserts, 0 skips, 0 production floats).

Covers:
  T01: Roundtrip CLI (--standalone, --write, --check, --json, default, 0o600, conflict)
  T02: Zone-B path/filesystem/hardlink/symlink/FIFO/size-cap/streaming/OSError hardening
  T03: Strict zero-float / zero-dup-key / bounded-depth / bounded-int JSON parsing
  T04: Pure-Q oracle math (LCG, LDL^T/congruence, matrix inv, Cayley-Routh, Bethe-Hessian,
       Hashimoto traces, 5 S102 operators, Wave-22 topologies, gate helpers, anchor tamper)
  T05: Field-complete re-signed certificate forgery resistance (0 bypasses)
  T06: R12 Lean 4 static trust-escape scanner + companion pins + live/mocked Lean 4.36.0
  T07: External MaleCNS read-only pin verification (mocked + tamper tests)
  T08: Subprocess CLI (-I -B, RC=2 single-line JSON errors, zero tracebacks, AST hygiene)
  T09: Read-only (chmod a-w) live Lean 4.36.0 staging with zero .lake/ artifacts
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
from typing import Any, Callable

_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import s162_malecns_neuro_bridge_oracle as oracle  # noqa: E402
import verify_s162_malecns_neuro_bridge as verifier  # noqa: E402


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def expect_s162_error(
    fn: Callable[[], Any], expected_code: str | None = None, msg: str = ""
) -> str:
    try:
        fn()
    except oracle.S162Error as exc:
        if expected_code is not None:
            check(
                exc.code == expected_code,
                f"{msg}: expected {expected_code!r}, got {exc.code!r} ({exc.message})",
            )
        return exc.code
    raise AssertionError(f"{msg}: expected S162Error({expected_code!r}), but succeeded")


def resign_cert(cert: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(cert)
    payload = out["payload"]
    p_sha = oracle.sha256_bytes(oracle.canonical_json_bytes(payload))
    out["payload_sha256"] = p_sha
    body = {
        "schema_version": out["schema_version"],
        "track_id": out["track_id"],
        "payload_sha256": p_sha,
        "payload": payload,
    }
    out["certificate_sha256"] = oracle.sha256_bytes(oracle.canonical_json_bytes(body))
    return out


def _run_cli_capture(argv: list[str]) -> tuple[int, str, str]:
    out_buf = io.StringIO()
    err_buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = out_buf, err_buf
        rc = verifier.main(argv)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _good_lean_runner(_tdir: Path) -> dict[str, Any]:
    lines = [
        f"'{name}' depends on axioms: [propext, Quot.sound]"
        for name in oracle.LEAN_THEOREM_NAMES[:-1]
    ]
    lines.append(f"'{oracle.LEAN_THEOREM_NAMES[-1]}' does not depend on any axioms")
    return {
        "version_rc": 0,
        "version_output": "Lean (version 4.36.0)",
        "build_rc": 0,
        "build_output": "Build completed successfully",
        "axiom_rc": 0,
        "axiom_stdout": "\n".join(lines) + "\n",
    }


def _copy_lean_bundle(dest: Path) -> Path:
    for fname in (
        oracle.PINNED_LEAN_FILES["lean_source"],
        "lean-toolchain",
        "lakefile.toml",
        "lake-manifest.json",
    ):
        (dest / fname).write_bytes((oracle.TRACK_DIR / fname).read_bytes())
    return dest


# ---------------------------------------------------------------------------
# T01: Roundtrip CLI, Write 0o600, Check, Standalone, Conflicts
# ---------------------------------------------------------------------------


def test_t01_cli_roundtrip() -> None:
    cert = oracle.build_certificate()
    raw = oracle.canonical_json_bytes(cert)

    rc_s, out_s, err_s = _run_cli_capture(["--standalone"])
    check(rc_s == 0 and err_s == "", f"standalone failed: {err_s}")
    check(out_s.encode("ascii") == raw, "standalone bytes mismatch")

    with tempfile.TemporaryDirectory(prefix="s162_t01_") as td:
        out_p = Path(td) / "cert.json"
        rc_w, out_w, err_w = _run_cli_capture(["--write", str(out_p), "--json"])
        check(rc_w == 0 and err_w == "", f"write json failed: {err_w}")
        w_obj = json.loads(out_w)
        check(w_obj["status"] == "WRITTEN", "write status")
        check(w_obj["certificate_sha256"] == cert["certificate_sha256"], "write sha")
        st = os.lstat(out_p)
        check(stat.S_IMODE(st.st_mode) == 0o600, f"expected 0o600, got {oct(st.st_mode)}")
        check(out_p.read_bytes() == raw, "written bytes != canonical")

        # Overwrite existing regular file in text mode
        rc_w2, out_w2, err_w2 = _run_cli_capture(["--write", str(out_p)])
        check(rc_w2 == 0 and err_w2 == "" and "WROTE" in out_w2, "write text failed")

        rc_c, out_c, err_c = _run_cli_capture(["--check", str(out_p), "--json"])
        check(rc_c == 0 and err_c == "", f"check json failed: {err_c}")
        c_obj = json.loads(out_c)
        check(c_obj["status"] == "PASS", "check PASS")
        check(c_obj["lean"]["theorems_verified"] == 16, "16 theorems")

        rc_c2, out_c2, err_c2 = _run_cli_capture(["--check", str(out_p)])
        check(rc_c2 == 0 and err_c2 == "" and "Track S162 PASS" in out_c2, "check text")

    # Default committed certificate check (relative path & default)
    rc_def, out_def, err_def = _run_cli_capture(["--json"])
    check(rc_def == 0 and err_def == "", f"default check failed: {err_def}")
    check(json.loads(out_def)["status"] == "PASS", "default check PASS")

    rc_rel, out_rel, err_rel = _run_cli_capture(["--check", oracle.DEFAULT_CERT_FILENAME])
    check(rc_rel == 0 and err_rel == "" and "PASS" in out_rel, "relative cert check")

    # Mode conflicts (modes == 2)
    rc_bad, _, err_bad = _run_cli_capture(["--check", "--standalone"])
    check(rc_bad == 2 and "MODE_CONFLICT" in err_bad, "mode conflict check+standalone")
    rc_bad2, _, err_bad2 = _run_cli_capture(["--write", "--standalone"])
    check(rc_bad2 == 2 and "MODE_CONFLICT" in err_bad2, "mode conflict write+standalone")


# ---------------------------------------------------------------------------
# T02: Zone-B Filesystem, Path, Symlink, Hardlink, Stream Cap Hardening
# ---------------------------------------------------------------------------


def test_t02_zone_b_filesystem() -> None:
    expect_s162_error(lambda: verifier.require_ok(1, "X", "m"), "X", "non-bool truthy")
    expect_s162_error(lambda: verifier.require_ok(False, "X", "m"), "X", "bool False")
    expect_s162_error(lambda: verifier._check_path_str("", "p"), "EMPTY_PATH", "empty")
    expect_s162_error(lambda: verifier._check_path_str("a\x00b", "p"), "NUL_BYTE_FORBIDDEN", "nul")
    expect_s162_error(lambda: verifier._check_path_str("a\ud800b", "p"), "INVALID_UTF8_SURROGATE", "surrogate")
    expect_s162_error(lambda: verifier._check_path_str(123, "p"), "TYPE_ERROR", "int path")
    check(verifier._check_path_str(Path("/tmp/ok"), "p") == Path("/tmp/ok"), "Path ok")

    with tempfile.TemporaryDirectory(prefix="s162_t02_") as td:
        tdir = Path(td)
        reg = tdir / "reg.json"
        reg.write_bytes(b"{}\n")
        sym = tdir / "sym.json"
        os.symlink(reg, sym)
        hard = tdir / "hard.json"
        os.link(reg, hard)
        sub = tdir / "sub"
        sub.mkdir()
        sym_dir = tdir / "sym_dir"
        os.symlink(sub, sym_dir)
        fifo = tdir / "pipe"
        os.mkfifo(fifo)

        expect_s162_error(lambda: verifier.read_regular_bytes_capped(sym, "s"), "SYMLINK_IN_PATH", "sym")
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(sym_dir / "x", "sd"), "SYMLINK_IN_PATH", "symdir")
        # Unnormalized dotdot traversal through symlink ancestor
        dotdot = str(sym_dir) + "/../reg.json"
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(dotdot, "dd"), "SYMLINK_IN_PATH", "dotdot sym")
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(hard, "h"), "HARDLINK_FORBIDDEN", "hardlink")
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(sub, "d"), "NOT_REGULAR_FILE", "dir")
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(fifo, "f"), "NOT_REGULAR_FILE", "fifo")
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(tdir / "missing", "m"), "IO_OPEN_ERROR", "missing")

        big = tdir / "big.json"
        big.write_bytes(b"a" * 32)
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(big, "b", max_bytes=16), "FILE_TOO_LARGE", "cap")
        check(len(verifier.read_regular_bytes_capped(big, "b", max_bytes=32)) == 32, "exact max_bytes")
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(big, "b", max_bytes=0), "RANGE_ERROR", "lo")
        expect_s162_error(lambda: verifier.read_regular_bytes_capped(big, "b", max_bytes=64 * 1024 * 1024 + 1), "RANGE_ERROR", "hi")

        # Streaming overflow check (st_size=0)
        orig_fstat = os.fstat
        class _ZeroStat:
            def __init__(self, st_obj: os.stat_result) -> None:
                self.st_mode = st_obj.st_mode
                self.st_nlink = st_obj.st_nlink
                self.st_size = 0
        try:
            os.fstat = lambda fd: _ZeroStat(orig_fstat(fd))  # type: ignore[assignment]
            expect_s162_error(
                lambda: verifier.read_regular_bytes_capped(big, "b", max_bytes=16),
                "FILE_STREAM_TOO_LARGE",
                "stream cap",
            )
            check(len(verifier.read_regular_bytes_capped(big, "b", max_bytes=32)) == 32, "exact stream")
        finally:
            os.fstat = orig_fstat

        # Relative path check via cwd (use big.json which has st_nlink == 1)
        orig_cwd = os.getcwd()
        try:
            os.chdir(td)
            check(verifier.read_regular_bytes_capped("big.json", "rel") == b"a" * 32, "rel read")
        finally:
            os.chdir(orig_cwd)

        # Simulated lstat OSError
        orig_lstat = os.lstat
        try:
            def _boom(_p: Any) -> Any:
                raise PermissionError("sim")
            os.lstat = _boom  # type: ignore[assignment]
            expect_s162_error(lambda: verifier._check_no_symlink_components(reg, "r"), "IO_STAT_ERROR", "lstat err")
        finally:
            os.lstat = orig_lstat

        # Write hardening
        expect_s162_error(lambda: verifier.write_regular_bytes_atomic_0600(tdir / "x", "str", "w"), "INVALID_BYTES", "str")
        expect_s162_error(lambda: verifier.write_regular_bytes_atomic_0600(tdir / "nope" / "x", b"{}", "w"), "PARENT_STAT_ERROR", "no parent")
        expect_s162_error(lambda: verifier.write_regular_bytes_atomic_0600(big / "child", b"{}", "w"), "PARENT_NOT_DIR", "parent file")
        expect_s162_error(lambda: verifier.write_regular_bytes_atomic_0600(sub, b"{}", "w"), "TARGET_NOT_REGULAR", "target dir")
        expect_s162_error(lambda: verifier.write_regular_bytes_atomic_0600(hard, b"{}", "w"), "TARGET_HARDLINK", "target hard")

        orig_lstat2 = os.lstat
        seen_boom = [0]
        try:
            def _boom_target(path_arg: Any) -> Any:
                if os.fspath(path_arg).endswith("boom.json"):
                    seen_boom[0] = seen_boom[0] + 1
                    if seen_boom[0] >= 2:
                        raise PermissionError("target stat fail")
                return orig_lstat2(path_arg)
            os.lstat = _boom_target  # type: ignore[assignment]
            expect_s162_error(lambda: verifier.write_regular_bytes_atomic_0600(tdir / "boom.json", b"{}", "w"), "TARGET_STAT_ERROR", "target stat")
        finally:
            os.lstat = orig_lstat2

        orig_replace = os.replace
        try:
            def _boom_replace(_a: Any, _b: Any) -> Any:
                raise OSError("disk full")
            os.replace = _boom_replace  # type: ignore[assignment]
            expect_s162_error(lambda: verifier.write_regular_bytes_atomic_0600(tdir / "wfail.json", b"{}", "w"), "IO_WRITE_ERROR", "replace fail")
        finally:
            os.replace = orig_replace


# ---------------------------------------------------------------------------
# T03: Strict JSON Parsing Hardening
# ---------------------------------------------------------------------------


def test_t03_strict_json() -> None:
    check(verifier.parse_strict_json_bytes(b'{"a":1,"s":"x\\"y"}\n', "ok") == {"a": 1, "s": 'x"y'}, "escaped str")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"\xff\n", "u"), "BAD_UTF8", "utf8")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes("\ufeff{}\n".encode("utf-8"), "b"), "BAD_BOM", "bom")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"{}\r\n", "cr"), "BAD_CRLF", "crlf")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"{}", "no_nl"), "BAD_TRAILING_NEWLINE", "missing lf")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"", "empty"), "BAD_TRAILING_NEWLINE", "empty")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"[]\n", "arr"), "JSON_NOT_OBJECT", "list root")
    expect_s162_error(lambda: verifier._scan_json_text_strict('{"a":1.5}\n'), "FLOAT_FORBIDDEN", "scan float dot")
    expect_s162_error(lambda: verifier._scan_json_text_strict('{"a":1e2}\n'), "FLOAT_FORBIDDEN", "scan float exp")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b'{"a":1.5}\n', "fl"), "FLOAT_FORBIDDEN", "float dot")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b'{"a":1e2}\n', "fe"), "FLOAT_FORBIDDEN", "float exp")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b'{"a":NaN}\n', "nan"), "JSON_CONSTANT_FORBIDDEN", "NaN")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b'{"a":1,"a":2}\n', "dup"), "DUPLICATE_JSON_KEY", "dup key")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"}\n", "ub"), "JSON_UNBALANCED", "neg depth")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"{\n", "uf"), "JSON_UNBALANCED_FINAL", "unclosed")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b'"unterm\n', "us"), "JSON_UNTERMINATED_STR", "unterm str")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(b"{bad}\n", "bad"), "JSON_INVALID", "bad json")

    # Exact depth boundary: 32 passes, 33 fails
    ok_d = ('{"a":' * 32 + "1" + "}" * 32 + "\n").encode("ascii")
    bad_d = ('{"a":' * 33 + "1" + "}" * 33 + "\n").encode("ascii")
    check(type(verifier.parse_strict_json_bytes(ok_d, "d32")) is dict, "depth 32 ok")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(bad_d, "d33"), "JSON_TOO_DEEP", "depth 33")

    # Exact integer digit boundary: 80 passes, 81 fails
    ok_i = ('{"a":' + "9" * 80 + "}\n").encode("ascii")
    bad_i = ('{"a":' + "9" * 81 + "}\n").encode("ascii")
    check(verifier.parse_strict_json_bytes(ok_i, "i80")["a"] == int("9" * 80), "80 digits ok")
    expect_s162_error(lambda: verifier.parse_strict_json_bytes(bad_i, "i81"), "JSON_INT_TOO_LARGE", "81 digits")


# ---------------------------------------------------------------------------
# T04: Pure-Q Oracle Operators, Boundary Guards, & All BoolOp Kill Paths
# ---------------------------------------------------------------------------


def test_t04_oracle_operators_and_boolops() -> None:
    # Oracle require_ok BoolOp (both sides) + require_exact_int + fmt_q
    expect_s162_error(lambda: oracle.require_ok(1, "C", "m"), "C", "non-bool truthy")
    expect_s162_error(lambda: oracle.require_ok(False, "C", "m"), "C", "bool False")
    expect_s162_error(lambda: oracle.require_exact_int(True, "x"), "TYPE_ERROR", "bool not int")
    expect_s162_error(lambda: oracle.require_exact_int(-1, "x", lo=0), "RANGE_ERROR", "lo")
    check(oracle.require_exact_int(0, "x", lo=0, hi=0) == 0, "exact lo/hi")
    expect_s162_error(lambda: oracle.require_exact_int(1, "x", hi=0), "RANGE_ERROR", "hi")
    expect_s162_error(lambda: oracle.fmt_q(1), "TYPE_ERROR", "fmt_q non-Fraction")  # type: ignore[arg-type]
    check(oracle.fmt_q(Fraction(4, 2)) == "2", "fmt_q int")
    check(oracle.fmt_q(Fraction(3, 4)) == "3/4", "fmt_q frac")

    # PureLCG boundaries
    expect_s162_error(lambda: oracle.PureLCG(-1), "RANGE_ERROR", "neg seed")
    lcg = oracle.PureLCG(0)
    expect_s162_error(lambda: lcg.randbelow(0), "RANGE_ERROR", "bound 0")
    check(lcg.randbelow(1) == 0, "bound 1")

    # Anchor parser refusal guards
    raw_anc = (oracle.DEFAULT_S102_DIR / oracle.S102_ANCHOR_FILENAME).read_bytes()
    anc_ok = oracle.load_s102_anchor_from_bytes(raw_anc, check_pinned_sha=True)
    check(type(anc_ok) is dict, "real anchor ok")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(raw_anc + b" ", check_pinned_sha=True), "ANCHOR_FILE_SHA_MISMATCH", "sha")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(b"\xff", check_pinned_sha=False), "ANCHOR_JSON_INVALID", "utf8")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(b'{"a":1.2}', check_pinned_sha=False), "FLOAT_FORBIDDEN", "float")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(b'{"a":NaN}', check_pinned_sha=False), "JSON_CONSTANT_FORBIDDEN", "const")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(('{"a":' + "1" * 81 + "}").encode(), check_pinned_sha=False), "ANCHOR_INT_TOO_LARGE", "int81")
    check(oracle._reject_large_int("-" + "1" * 80) == -int("1" * 80), "neg 80 digits ok")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(b'{"a":1,"a":2}', check_pinned_sha=False), "DUPLICATE_JSON_KEY", "dup")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(b"[]", check_pinned_sha=False), "ANCHOR_TYPE_ERROR", "list")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(('{"k":"' + "a" * 257 + '"}').encode(), check_pinned_sha=False), "ANCHOR_STR_TOO_LONG", "str257")
    expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(('{"' + "k" * 257 + '":1}').encode(), check_pinned_sha=False), "ANCHOR_STR_TOO_LONG", "key257")
    check(oracle._validate_anchor_tree({"k" * 256: "v" * 256}) is None, "len 256 ok")
    deep_obj: Any = 1
    for _ in range(32):
        deep_obj = [deep_obj]
    check(oracle._validate_anchor_tree(deep_obj) is None, "depth 32 ok")
    expect_s162_error(lambda: oracle._validate_anchor_tree([deep_obj]), "ANCHOR_TOO_DEEP", "depth 33")

    env_anc = json.loads(raw_anc.decode("utf-8"))
    for key, val, code in [
        ("schema_version", "wrong", "ANCHOR_SCHEMA_MISMATCH"),
        ("track_id", "S999", "ANCHOR_TRACK_MISMATCH"),
        ("payload", [], "ANCHOR_PAYLOAD_ERROR"),
        ("payload_sha256", "0" * 64, "ANCHOR_PAYLOAD_SHA_MISMATCH"),
    ]:
        bad = copy.deepcopy(env_anc)
        bad[key] = val
        expect_s162_error(
            lambda b=bad: oracle.load_s102_anchor_from_bytes(oracle.canonical_json_bytes(b), check_pinned_sha=False),
            code,
            f"anchor {key}",
        )
    # Test ANCHOR_PINNED_PAYLOAD_MISMATCH by patching PINNED_S102_ANCHOR_PAYLOAD_SHA256
    orig_pin = oracle.PINNED_S102_ANCHOR_PAYLOAD_SHA256
    try:
        oracle.PINNED_S102_ANCHOR_PAYLOAD_SHA256 = "0" * 64
        expect_s162_error(lambda: oracle.load_s102_anchor_from_bytes(raw_anc, check_pinned_sha=True), "ANCHOR_PINNED_PAYLOAD_MISMATCH", "pinned payload")
    finally:
        oracle.PINNED_S102_ANCHOR_PAYLOAD_SHA256 = orig_pin

    # Exact linear algebra & congruence inertia (incl 2x2 hyperbolic block [[0,1],[1,0]] and zero block)
    check(oracle.exact_congruence_inertia([[0, 1], [1, 0]]) == [1, 1, 0], "hyperbolic 2x2")
    check(oracle.exact_congruence_inertia([[0, 0], [0, 0]]) == [0, 0, 2], "zero 2x2")
    check(oracle.exact_congruence_inertia([[0, 0, 1], [0, 0, 0], [1, 0, 0]]) == [1, 1, 1], "swapped 2x2")
    check(oracle.exact_is_pd([[Fraction(0)]]) is False, "pd zero pivot")
    check(oracle.exact_is_pd([[Fraction(-1)]]) is False, "pd neg pivot")
    check(oracle.exact_is_pd([[Fraction(2), Fraction(1)], [Fraction(1), Fraction(2)]]) is True, "pd 2x2")
    expect_s162_error(lambda: oracle.exact_mat_inv([[Fraction(0)]]), "SINGULAR_MATRIX", "singular inv")

    # Cayley-Routh exact boundary tests (kills EVERY <= vs < boundary flip in is_schur_stable_poly_q!)
    # 1. p(1) == 0: (z - 1) -> [1, -1]; p(1) < 0: (z - 2) -> [1, -2]
    check(oracle.is_schur_stable_poly_q([Fraction(1), Fraction(-1)]) is False, "p(1)=0")
    check(oracle.is_schur_stable_poly_q([Fraction(1), Fraction(-2)]) is False, "p(1)<0")
    # 2. p(-1) == 0: (z + 1) -> [1, 1]; (-1)^n p(-1) < 0: (z + 2) -> [1, 2]
    check(oracle.is_schur_stable_poly_q([Fraction(1), Fraction(1)]) is False, "p(-1)=0")
    check(oracle.is_schur_stable_poly_q([Fraction(1), Fraction(2)]) is False, "p(-1)<0")
    # 3. Hurwitz coef a_1 == 0: (z^2 + 1) has p(1)=2>0, p(-1)=2>0, Cayley q(s)=2s^2 + 0*s + 2 -> coef == 0!
    check(oracle.is_schur_stable_poly_q([Fraction(1), Fraction(0), Fraction(1)]) is False, "unit circle coef=0")
    # 4. Routh piv == 0 / nxt[0] == 0 for degree 3: p(z) = (z^2 + 1)(z - 1/2) has roots +/-i, 1/2:
    #    p(1)=1>0, (-1)^3 p(-1) = -(-3) = 3 > 0; q(s) has all a_k > 0 except Routh row2[0] == 0!
    #    Let's verify: (z^2 + 1)(z - 1/2) = z^3 - 1/2 z^2 + z - 1/2
    check(
        oracle.is_schur_stable_poly_q([Fraction(1), Fraction(-1, 2), Fraction(1), Fraction(-1, 2)]) is False,
        "deg3 Routh zero pivot",
    )
    # 5. Deg3 all Hurwitz coefs > 0 with strictly negative Routh pivot (a=[8,8,8,16], row2[0]=-8 < 0)
    check(
        oracle.is_schur_stable_poly_q([Fraction(1), Fraction(3, 5), Fraction(7, 5), Fraction(1, 5)]) is False,
        "deg3 Routh neg nxt[0]",
    )
    # 6. Deg4 Routh piv == 0 in later iteration: (z^2 + 1)^2 = z^4 + 2z^2 + 1? No, that has a_1=0.
    #    (z^2 + 1)(z^2 + 1/4) = z^4 + 5/4 z^2 + 1/4 -> odd coefs = 0 -> a_1 > 0, a_3 > 0, Routh row2[0] == 0!
    #    Better: (z^2 + 1)(z - 1/2)^2 = z^4 - z^3 + 5/4 z^2 - z + 1/4: p(1)=1/2>0, p(-1)=9/2>0, all a_k>0, Routh hits 0!
    check(
        oracle.is_schur_stable_poly_q(
            [Fraction(1), Fraction(-1), Fraction(5, 4), Fraction(-1), Fraction(1, 4)]
        )
        is False,
        "deg4 Routh zero",
    )
    # 7. Strictly Schur-stable degree 2 & 3 & 4: (z - 1/2)^2, (z^2 + 1/4)(z - 1/2)
    check(oracle.is_schur_stable_q([[Fraction(1, 2), Fraction(0)], [Fraction(0), Fraction(-1, 2)]]) is True, "stable 2x2")
    check(
        oracle.is_schur_stable_poly_q([Fraction(1), Fraction(-1, 2), Fraction(1, 4), Fraction(-1, 8)]) is True,
        "stable deg3",
    )
    # Direct damped_charpoly_from_base_q == charpoly_q(damped_operator) parity check
    w6_s = anc_ok["central_complex_core_6x6"]["dale_signed_synapses_6x6"]
    m_norm = oracle.row_normalize_matrix(w6_s, zero_diag=True)
    cp_fast = oracle.damped_charpoly_from_base_q(oracle.charpoly_q(m_norm), Fraction(3, 2), Fraction(1, 2))
    cp_slow = oracle.charpoly_q(oracle.damped_operator(m_norm, Fraction(3, 2), Fraction(1, 2)))
    check(cp_fast == cp_slow, "fast shifted charpoly exact parity")

    # Domain refusal guards on graph operators
    expect_s162_error(lambda: oracle.signed_bethe_hessian_crit_r_q([[0, 0], [0, 0]]), "EMPTY_SYMMETRIC_GRAPH", "empty bh")
    # Force BH_HI_NOT_PD on a huge-degree pathological skew? No: H(2) = 3I - 2A + D; if A has d_bar=1, D_i can be small;
    # Wait: for 2-node [[0, 1], [1, 0]], S=[[0,2],[2,0]], d_bar=2, A=[[0,1],[1,0]], D=[1,1], H(2)=[[4,-2],[-2,4]] PD.
    # For 3-node star with tiny edge? Actually H_BH(2) fails PD if A has eigenvalue > 3/2? Let's test via a 4-node complete unsigned graph K4:
    # K4: d_bar = 3, A_ij = 1/3, D_i = 1, H(2) = 3I - (2/3)A + I = 4I - (2/3)A -> min eig = 4 - 2 = 2 > 0.
    # Use a 6-node matrix where one disconnected component has D_i=0 and another has huge A -> wait: row of all zeros has H(2)_ii = 3 > 0!
    # Wait: when is H_BH(2) NOT PD? When A has eigenvalue lam where 3 + D_i - 2*lam <= 0; for star graph K_{1,m}, max eig of A ~ sqrt(m) while d_bar = 2m/(m+1) ~ 2, so A/d_bar has eig ~ sqrt(m)/2! At m=40, sqrt(40)/2 > 3!
    # 10-node graph with one heavy edge (0,1): d_bar=40, A_01=5, D_0=5 -> H(2)_00=8, H(2)_01=-10 -> det=-36 < 0!
    iso_heavy = [[0] * 10 for _ in range(10)]
    iso_heavy[0][1] = 100
    iso_heavy[1][0] = 100
    expect_s162_error(lambda: oracle.signed_bethe_hessian_crit_r_q(iso_heavy), "BH_HI_NOT_PD", "heavy isolated pair violates H(2) PD")

    expect_s162_error(lambda: oracle.hashimoto_trace_moments_q([[5, 0], [0, 5]]), "ZERO_OFF_DIAG", "diag only")
    expect_s162_error(lambda: oracle.operator_commutator_q([[0, 0], [0, 0]]), "ZERO_FROBENIUS", "zero mat")
    expect_s162_error(lambda: oracle.evaluate_five_s102_operators([[1, 0], [0, 1]], (0,), (1,)), "EMPTY_GRAPH", "empty edges")
    # Zero boundary trace: node 0 isolated, edges only in interior (1,2) with L_II invertible? Use signed frustration on (1,2,3) and node 0 isolated!
    iso_mat = [[0, 0, 0, 0], [0, 0, 5, -5], [0, 5, 0, 5], [0, -5, 5, 0]]
    expect_s162_error(lambda: oracle.evaluate_five_s102_operators(iso_mat, (0,), (1, 2, 3)), "ZERO_BOUNDARY_TRACE", "zero L_BB")
    expect_s162_error(lambda: oracle.build_model_carving_folded(mode="invalid"), "BAD_CARVING_MODE", "bad mode")

    # CX_DALE_ROW_MISMATCH guard
    bad_anc = copy.deepcopy(anc_ok)
    bad_anc["central_complex_core_6x6"]["dale_signed_synapses_6x6"][0][0] *= -1
    expect_s162_error(lambda: oracle.build_exp_q43a(bad_anc), "CX_DALE_ROW_MISMATCH", "bad dale row")

    # Kill ALL 3 gate BoolOps (single-false-operand tests!)
    check(oracle.check_q43a_bethe_bp_gate(True, False, True, False) is True, "g1 all ok")
    check(oracle.check_q43a_bethe_bp_gate(False, False, True, False) is False, "g1 f0")
    check(oracle.check_q43a_bethe_bp_gate(True, True, True, False) is False, "g1 f1")
    check(oracle.check_q43a_bethe_bp_gate(True, False, False, False) is False, "g1 f2")
    check(oracle.check_q43a_bethe_bp_gate(True, False, True, True) is False, "g1 f3")

    t_hi = Fraction(1, 10)
    t_eq = Fraction(1, 20)
    check(oracle.check_q43a_separation_gate(t_hi, t_hi, True) is True, "g2 all ok")
    check(oracle.check_q43a_separation_gate(t_eq, t_hi, True) is False, "g2 f0 eq")
    check(oracle.check_q43a_separation_gate(t_hi, t_eq, True) is False, "g2 f1 eq")
    check(oracle.check_q43a_separation_gate(t_hi, t_hi, False) is False, "g2 f2")

    f1, f2 = Fraction(1, 10), Fraction(2, 10)
    check(oracle.check_q43b_dale_tail_dominance(f1, f2, f2, f2, f2) is True, "g3 all ok")
    check(oracle.check_q43b_dale_tail_dominance(f1, f1, f2, f2, f2) is False, "g3 f0 eq")
    check(oracle.check_q43b_dale_tail_dominance(f1, f2, f1, f2, f2) is False, "g3 f1 eq")
    check(oracle.check_q43b_dale_tail_dominance(f1, f2, f2, f1, f2) is False, "g3 f2 eq")
    check(oracle.check_q43b_dale_tail_dominance(f1, f2, f2, f2, f1) is False, "g3 f3 eq")


# ---------------------------------------------------------------------------
# T05: Field-Complete Re-Signed Forgery Resistance (SEC/FR0/FR1)
# ---------------------------------------------------------------------------


def test_t05_resigned_forgery_resistance() -> None:
    base = oracle.build_certificate()
    check(verifier.verify_certificate_object(base)["status"] == "PASS", "base PASS")

    # Rational & SHA helper unit guards + BoolOp kills
    check(verifier._parse_canon_q("0", "q") == Fraction(0), "q=0")
    check(verifier._parse_canon_q("-3/5", "q") == Fraction(-3, 5), "q=-3/5")
    expect_s162_error(lambda: verifier._parse_canon_q(1, "q"), "Q_TYPE_ERROR", "q int")
    expect_s162_error(lambda: verifier._parse_canon_q("1/0", "q"), "Q_FORMAT_ERROR", "q div0")
    expect_s162_error(lambda: verifier._parse_canon_q("2/4", "q"), "Q_NOT_REDUCED", "q 2/4")
    # Kills `val.numerator == num_i and val.denominator == den_i` BoolOp (left True, right False!)
    expect_s162_error(lambda: verifier._parse_canon_q("0/2", "q"), "Q_NOT_REDUCED", "q 0/2")
    expect_s162_error(lambda: verifier._check_sha256_field(1, "s"), "SHA_TYPE_ERROR", "sha int")
    expect_s162_error(lambda: verifier._check_sha256_field("abc", "s"), "SHA_FORMAT_ERROR", "sha short")

    # Envelope / SHA tamper checks
    expect_s162_error(lambda: verifier.verify_certificate_object([]), "CERT_NOT_DICT", "list")  # type: ignore[arg-type]
    bad_env = copy.deepcopy(base)
    bad_env["extra"] = 1
    expect_s162_error(lambda: verifier.verify_certificate_object(bad_env), "ENVELOPE_KEYS_MISMATCH", "extra key")

    for k, v, code in [
        ("schema_version", "bad", "SCHEMA_MISMATCH"),
        ("track_id", "S999", "TRACK_MISMATCH"),
        ("payload", [], "PAYLOAD_NOT_DICT"),
    ]:
        m = copy.deepcopy(base)
        m[k] = v
        expect_s162_error(lambda x=m: verifier.verify_certificate_object(x), code, f"env {k}")

    bad_pk = copy.deepcopy(base)
    bad_pk["payload"]["extra"] = 1
    expect_s162_error(lambda: verifier.verify_certificate_object(bad_pk), "PAYLOAD_KEYS_MISMATCH", "payload keys")

    bad_psha = copy.deepcopy(base)
    bad_psha["payload_sha256"] = "0" * 64
    expect_s162_error(lambda: verifier.verify_certificate_object(bad_psha), "PAYLOAD_SHA_MISMATCH", "payload sha")

    bad_csha = copy.deepcopy(base)
    bad_csha["certificate_sha256"] = "0" * 64
    expect_s162_error(lambda: verifier.verify_certificate_object(bad_csha), "CERT_SHA_MISMATCH", "cert sha")

    # Re-signed secondary mathematical forgery probes (each hits its exact secondary guard!)
    def _forge(mutator: Callable[[dict[str, Any]], None], expected_code: str, label: str) -> None:
        c = copy.deepcopy(base)
        mutator(c["payload"])
        c = resign_cert(c)
        expect_s162_error(lambda: verifier.verify_certificate_object(c), expected_code, label)

    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["malecns_cx_6x6"].__setitem__("signed_laplacian_inertia", [5, 0, 1]), "CX_NOT_FRUSTRATED", "cx frust")
    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["malecns_cx_6x6"].__setitem__("symmetrized_krein_inertia", [3, 3, 0]), "CX_KREIN_MISMATCH", "cx krein")
    # Kills BOTH operands of `g_lo > Fraction(0) and g_hi < Fraction(1)` AND `<` vs `<=` boundaries!
    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["malecns_cx_6x6"]["damped_bp_cavity_excluded"].__setitem__("gamma_lo_q", "0"), "CX_GAMMA_BRACKET", "g_lo=0")
    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["malecns_cx_6x6"]["damped_bp_cavity_excluded"].__setitem__("gamma_hi_q", "1"), "CX_GAMMA_BRACKET", "g_hi=1")
    _forge(
        lambda p: p["exp_q43a_bp_frustration_and_cavity"]["malecns_cx_6x6"]["damped_bp_cavity_excluded"].update(
            {"gamma_lo_q": "1/2", "gamma_hi_q": "1/2"}
        ),
        "CX_GAMMA_ORDER",
        "g_lo==g_hi",
    )
    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["kill_gates"].__setitem__("bethe_bp_stability_bound_pass", False), "Q43A_KILL_GATE_BP", "kg bp")
    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["kill_gates"].__setitem__("separation_gt_5pct_vs_shuf_and_ms_pass", False), "Q43A_KILL_GATE_SEP", "kg sep")
    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["cavity_exclusion_isomorphism_sop16"]["nafis_septal_leak_sweep"][0].__setitem__("det_L_red", 999), "NAFIS_DET_MISMATCH", "nafis det")
    _forge(lambda p: p["exp_q43a_bp_frustration_and_cavity"]["cavity_exclusion_isomorphism_sop16"]["nafis_septal_leak_sweep"][0].__setitem__("septal_echo_leak_q", "1/2"), "NAFIS_CONSERVATION", "nafis cons")
    _forge(lambda p: p["exp_q43b_five_operator_wave22_tomography"]["structural_separation_verdict"].__setitem__("unsigned_wave22_frustrated_count", 1), "UNSIGNED_W22_FRUST_NONZERO", "w22 unsigned")
    _forge(lambda p: p["exp_q43b_five_operator_wave22_tomography"]["structural_separation_verdict"].__setitem__("recurrent_folded_stock_frustrated_count", 1), "FOLDED_STOCK_FRUST_NONZERO", "w22 folded")
    _forge(lambda p: p["exp_q43b_five_operator_wave22_tomography"]["structural_separation_verdict"].__setitem__("dale_prior_restores_frustration", False), "DALE_PRIOR_FRUST_FAIL", "dale frust")
    _forge(lambda p: p["exp_q43b_five_operator_wave22_tomography"]["structural_separation_verdict"].__setitem__("dale_prior_beats_all_controls_on_worst_case_tail", False), "DALE_PRIOR_TAIL_FAIL", "dale tail")
    # Replay-only subtle forgery (passes all secondary checks, caught by ORACLE_REPLAY_MISMATCH!)
    _forge(lambda p: p.__setitem__("novelty_classification", "TAMPERED"), "ORACLE_REPLAY_MISMATCH", "replay mismatch")


# ---------------------------------------------------------------------------
# T06: R12 Lean 4 Scanner, Companion Pins, and Live/Mocked Lean 4.36.0
# ---------------------------------------------------------------------------


def test_t06_lean4_r12_and_pins() -> None:
    real_src = (oracle.TRACK_DIR / oracle.PINNED_LEAN_FILES["lean_source"]).read_text(encoding="utf-8")
    res = verifier.scan_lean_source_r12(real_src)
    check(res["static_r12_clean"] is True and res["theorems_verified"] == 16, "real lean clean")

    # Comment & string stripping (nested block comments, line comments, escaped strings -> 0 FP!)
    clean_comment_test = real_src + '\n-- sorry axiom\n/- outer /- sorry -/ native_decide -/\n'
    check(verifier.scan_lean_source_r12(clean_comment_test)["theorems_verified"] == 16, "comments stripped")
    clean_str_test = real_src.replace(
        "namespace MaleCNSNeuroBridge",
        'namespace MaleCNSNeuroBridge\n/- "sorry \\"axiom\\"\nline2" -/',
        1,
    )
    check(verifier.scan_lean_source_r12(clean_str_test)["theorems_verified"] == 16, "commented str")
    expect_s162_error(lambda: verifier.strip_lean_comments_and_strings("/- unclosed"), "LEAN_UNTERM_COMMENT", "unterm block")
    expect_s162_error(lambda: verifier.strip_lean_comments_and_strings('"unclosed'), "LEAN_UNTERM_STRING", "unterm str")
    # Valid string literal stripped without triggering banned word inside quotes
    stripped = verifier.strip_lean_comments_and_strings('def s := "sorry \\"ok\\"\nline2"')
    check("sorry" not in stripped, "str stripped")

    # Escape injections
    for bad_kw in ("sorry", "admit", "axiom x : Nat", "native_decide", "Classical.choice", "#eval 1", "IO.println", "import Mathlib", "panic!"):
        expect_s162_error(
            lambda kw=bad_kw: verifier.scan_lean_source_r12(real_src + "\n" + kw + "\n"),
            "LEAN_ESCAPE_FOUND",
            f"escape {bad_kw}",
        )

    # Missing theorem, renamed theorem, missing #print axioms
    expect_s162_error(
        lambda: verifier.scan_lean_source_r12(real_src.replace("theorem chain_bp_exact_finite_horizon_convergence", "private theorem chain_bp_exact_finite_horizon_convergence", 1)),
        "LEAN_THM_COUNT",
        "thm count",
    )
    expect_s162_error(
        lambda: verifier.scan_lean_source_r12(real_src.replace("theorem chain_bp_exact_finite_horizon_convergence", "theorem bogus_name", 1)),
        "LEAN_THM_SET_MISMATCH",
        "thm set",
    )
    expect_s162_error(
        lambda: verifier.scan_lean_source_r12(real_src.replace("#print axioms MaleCNSNeuroBridge.chain_bp_exact_finite_horizon_convergence", "", 1)),
        "LEAN_AXIOM_PRINT_MISMATCH",
        "print set",
    )

    # Live axiom stdout parser (incl multi-line wrapped output and forbidden axiom)
    good_run = _good_lean_runner(oracle.TRACK_DIR)
    check(verifier.validate_lean_axiom_stdout(good_run["axiom_stdout"])["live_axioms_verified"] == 16, "axiom stdout ok")
    wrapped = good_run["axiom_stdout"].replace("[propext, Quot.sound]", "[propext,\n Quot.sound]", 1)
    check(verifier.validate_lean_axiom_stdout(wrapped)["live_axioms_verified"] == 16, "wrapped ok")
    expect_s162_error(
        lambda: verifier.validate_lean_axiom_stdout(good_run["axiom_stdout"].replace("Quot.sound", "Classical.choice", 1)),
        "LEAN_FORBIDDEN_AXIOM",
        "Classical.choice",
    )
    expect_s162_error(
        lambda: verifier.validate_lean_axiom_stdout("'MaleCNSNeuroBridge.only_one' does not depend on any axioms\n"),
        "LEAN_AXIOM_SET_MISMATCH",
        "axiom count mismatch",
    )

    # Companion pins + unpinned toolchain/manifest tamper + mocked live runner failure modes
    with tempfile.TemporaryDirectory(prefix="s162_lean_") as td:
        tdir = _copy_lean_bundle(Path(td))
        check(verifier.verify_companion_pins_and_lean(tdir, lean_runner=_good_lean_runner)["live_axioms_verified"] == 16, "bundle pass")

        # Tampered pin
        (tdir / "lakefile.toml").write_bytes(b"tampered\n")
        expect_s162_error(lambda: verifier.verify_companion_pins_and_lean(tdir), "COMPANION_SHA_MISMATCH", "pin tamper")
        (tdir / "lakefile.toml").write_bytes((oracle.TRACK_DIR / "lakefile.toml").read_bytes())

        # Bad toolchain & non-empty lake packages (reachable with check_pins=False)
        (tdir / "lean-toolchain").write_text("leanprover/lean4:v4.0.0\n", encoding="utf-8")
        expect_s162_error(lambda: verifier.verify_companion_pins_and_lean(tdir, check_pins=False), "BAD_TOOLCHAIN", "bad tc")
        (tdir / "lean-toolchain").write_bytes((oracle.TRACK_DIR / "lean-toolchain").read_bytes())

        (tdir / "lake-manifest.json").write_text('{"packages": ["mathlib"]}\n', encoding="utf-8")
        expect_s162_error(lambda: verifier.verify_companion_pins_and_lean(tdir, check_pins=False), "NONEMPTY_LAKE_PACKAGES", "pkgs")
        (tdir / "lake-manifest.json").write_bytes((oracle.TRACK_DIR / "lake-manifest.json").read_bytes())

        # Mocked runner failure modes
        for code, patch in [
            ("LEAN_VERSION_RC", {"version_rc": 1}),
            ("BAD_LEAN_VERSION", {"version_output": "Lean (version 4.0.0)"}),
            ("LAKE_BUILD_FAIL", {"build_rc": 1}),
            ("LAKE_BUILD_WARNING", {"build_output": "warning: unused var"}),
            ("LEAN_AXIOM_RC", {"axiom_rc": 1}),
        ]:
            def _bad_run(_p: Path, kw: dict[str, Any] = patch) -> dict[str, Any]:
                out = _good_lean_runner(_p)
                out.update(kw)
                return out
            expect_s162_error(lambda r=_bad_run: verifier.verify_companion_pins_and_lean(tdir, lean_runner=r), code, code)


# ---------------------------------------------------------------------------
# T07: External MaleCNS Pin Verifier Hardening (Mocked + Tamper)
# ---------------------------------------------------------------------------


def test_t07_external_pins() -> None:
    with tempfile.TemporaryDirectory(prefix="s162_ext_") as td:
        tdir = Path(td)
        expect_s162_error(lambda: verifier.verify_external_malecns_pins(tdir / "nope"), "MALECNS_DIR_MISSING", "missing dir")
        expect_s162_error(lambda: verifier.verify_external_malecns_pins(tdir), "EXTERNAL_OPEN_ERROR", "missing file")

        # Create tiny mocked pins via temporary patch of oracle.MALECNS_EXTERNAL_PINS
        f1 = tdir / "f1.bin"
        f1.write_bytes(b"hello-malecns")
        orig_pins = oracle.MALECNS_EXTERNAL_PINS
        try:
            good_sha = oracle.sha256_bytes(b"hello-malecns")
            oracle.MALECNS_EXTERNAL_PINS = ({"id": "f1", "filename": "f1.bin", "bytes": 13, "sha256": good_sha},)  # type: ignore[assignment]
            res = verifier.verify_external_malecns_pins(tdir)
            check(len(res) == 1 and res[0]["sha256"] == good_sha, "mock ext pin ok")

            # Size mismatch
            oracle.MALECNS_EXTERNAL_PINS = ({"id": "f1", "filename": "f1.bin", "bytes": 99, "sha256": good_sha},)  # type: ignore[assignment]
            expect_s162_error(lambda: verifier.verify_external_malecns_pins(tdir), "EXTERNAL_SIZE_MISMATCH", "size")

            # SHA mismatch
            oracle.MALECNS_EXTERNAL_PINS = ({"id": "f1", "filename": "f1.bin", "bytes": 13, "sha256": "0" * 64},)  # type: ignore[assignment]
            expect_s162_error(lambda: verifier.verify_external_malecns_pins(tdir), "EXTERNAL_SHA_MISMATCH", "sha")

            # Non-regular file (directory named f1.bin)
            f1.unlink()
            f1.mkdir()
            oracle.MALECNS_EXTERNAL_PINS = ({"id": "f1", "filename": "f1.bin", "bytes": 0, "sha256": "0" * 64},)  # type: ignore[assignment]
            expect_s162_error(lambda: verifier.verify_external_malecns_pins(tdir), "EXTERNAL_NOT_REG", "dir not reg")
        finally:
            oracle.MALECNS_EXTERNAL_PINS = orig_pins


# ---------------------------------------------------------------------------
# T08: Subprocess CLI, RC=2 Error Handlers, & AST Zero-Float / Zero-Assert Audit
# ---------------------------------------------------------------------------


def test_t08_cli_and_ast_hygiene() -> None:
    # Exception handlers in main()
    orig_cli = verifier.run_cli
    try:
        verifier.run_cli = lambda _a=None: (_ for _ in ()).throw(RecursionError("rec"))  # type: ignore[assignment]
        rc_r, _, err_r = _run_cli_capture([])
        check(rc_r == 2 and "RECURSION_ERROR" in err_r, "recursion rc=2")
        verifier.run_cli = lambda _a=None: (_ for _ in ()).throw(UnicodeDecodeError("utf-8", b"\xff", 0, 1, "bad"))  # type: ignore[assignment]
        rc_u, _, err_u = _run_cli_capture([])
        check(rc_u == 2 and "UNICODE_DECODE_ERROR" in err_u, "unicode rc=2")
        verifier.run_cli = lambda _a=None: (_ for _ in ()).throw(subprocess.TimeoutExpired(["lean"], 1))  # type: ignore[assignment]
        rc_s, _, err_s = _run_cli_capture([])
        check(rc_s == 2 and "SUBPROCESS_ERROR" in err_s, "subprocess rc=2")
        verifier.run_cli = lambda _a=None: (_ for _ in ()).throw(OSError("os"))  # type: ignore[assignment]
        rc_o, _, err_o = _run_cli_capture([])
        check(rc_o == 2 and "OS_ERROR" in err_o, "os rc=2")
    finally:
        verifier.run_cli = orig_cli

    # AST hygiene across oracle, verifier, and test suite
    for fname in (
        "s162_malecns_neuro_bridge_oracle.py",
        "verify_s162_malecns_neuro_bridge.py",
        "test_s162_malecns_neuro_bridge_r5.py",
    ):
        src = (oracle.TRACK_DIR / fname).read_text(encoding="utf-8")
        tree = ast.parse(src)
        asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
        check(len(asserts) == 0, f"{fname}: bare asserts found")
        floats = [
            n.value
            for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, float)
        ]
        check(len(floats) == 0, f"{fname}: float literals found")
        check(("/ho" + "me/") not in src, f"{fname}: hardcoded home path found")

    # Isolated subprocess CLI check
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(
        [sys.executable, "-I", "-B", "verify_s162_malecns_neuro_bridge.py", "--check", "--json"],
        cwd=str(oracle.TRACK_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    check(run.returncode == 0, f"subprocess check failed: {run.stderr}")
    check("Traceback" not in run.stderr, "no traceback")
    parsed = json.loads(run.stdout)
    check(parsed["status"] == "PASS" and parsed["track_id"] == "S162", "subprocess PASS")

    # Tampered cert fails with RC=2 and single-line JSON error
    with tempfile.TemporaryDirectory(prefix="s162_sub_") as td:
        bad_p = Path(td) / "bad.json"
        bad_p.write_text('{"schema_version":"bad"}\n', encoding="utf-8")
        bad_run = subprocess.run(
            [sys.executable, "-I", "-B", "verify_s162_malecns_neuro_bridge.py", "--check", str(bad_p)],
            cwd=str(oracle.TRACK_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        check(bad_run.returncode == 2, f"expected rc=2, got {bad_run.returncode}")
        check("Traceback" not in bad_run.stderr, "no traceback on fail")
        err_obj = json.loads(bad_run.stderr.strip())
        check(err_obj["status"] == "FAIL" and err_obj["code"] == "ENVELOPE_KEYS_MISMATCH", "err json")


def test_t09_readonly_live_lean_no_lake() -> None:
    bundle_files = (
        "s162_malecns_neuro_bridge_oracle.py",
        "verify_s162_malecns_neuro_bridge.py",
        "s102_malecns_anchor.json",
        "s162_malecns_neuro_bridge_certificate.json",
        oracle.PINNED_LEAN_FILES["lean_source"],
        "lean-toolchain",
        "lakefile.toml",
        "lake-manifest.json",
    )
    with tempfile.TemporaryDirectory(prefix="s162_t09_ro_") as td:
        ro_dir = Path(td) / "ro_track"
        ro_dir.mkdir()
        for fname in bundle_files:
            (ro_dir / fname).write_bytes((oracle.TRACK_DIR / fname).read_bytes())
        for fname in bundle_files:
            fp = ro_dir / fname
            os.chmod(fp, stat.S_IMODE(fp.stat().st_mode) & ~0o222)
        os.chmod(ro_dir, stat.S_IMODE(ro_dir.stat().st_mode) & ~0o222)
        try:
            env = dict(os.environ)
            env["CUDA_VISIBLE_DEVICES"] = ""
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            run = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    str(ro_dir / "verify_s162_malecns_neuro_bridge.py"),
                    "--check",
                    "--json",
                    "--live-lean",
                ],
                cwd=str(ro_dir),
                env=env,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
            check(run.returncode == 0, f"ro live-lean failed: {run.stderr}")
            check(run.stderr == "", f"ro live-lean unexpected stderr: {run.stderr}")
            parsed = json.loads(run.stdout)
            check(parsed["status"] == "PASS", "ro live-lean status PASS")
            check(parsed["lean"]["theorems_verified"] == 16, "ro 16 static theorems")
            check(parsed["lean"]["live_axioms_verified"] == 16, "ro 16 live axioms")
            check(not (ro_dir / ".lake").exists(), ".lake created in ro_dir")
            check(not (ro_dir / "__pycache__").exists(), "__pycache__ created in ro_dir")
            check(not (oracle.TRACK_DIR / ".lake").exists(), ".lake created in TRACK_DIR")
            check(
                sorted(p.name for p in ro_dir.iterdir()) == sorted(bundle_files),
                "unexpected artifacts in ro_dir",
            )
        finally:
            os.chmod(ro_dir, 0o700)
            for p in ro_dir.iterdir():
                os.chmod(p, 0o700 if p.is_dir() else 0o600)


def main() -> int:
    tests = (
        test_t01_cli_roundtrip,
        test_t02_zone_b_filesystem,
        test_t03_strict_json,
        test_t04_oracle_operators_and_boolops,
        test_t05_resigned_forgery_resistance,
        test_t06_lean4_r12_and_pins,
        test_t07_external_pins,
        test_t08_cli_and_ast_hygiene,
        test_t09_readonly_live_lean_no_lake,
    )
    for fn in tests:
        fn()
    sys.stdout.write(f"Track S162 R5 suite: {len(tests)}/{len(tests)} OK\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
