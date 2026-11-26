#!/usr/bin/env python3
"""Heritage Exact Operators: Zone-B Hardened Verifier, Field-Complete SEC/FR0/FR1 Semantic Auditor,
Full R12 Static Lean 4 Scanner, and Env-Scrubbed Live Lean 4.36.0 Kernel Verifier.

CLI modes:
  --check <path> [--json]   Verify certificate + full replay + live Lean 4.36.0
  --write <path> [--json]   Atomically write canonical certificate (0o600)
  --standalone              Emit canonical certificate JSON to stdout
  [--json]                  Default: check committed certificate in track dir
"""
from __future__ import annotations

from collections.abc import Sequence
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any

_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import s90_heritage_operators_oracle as oracle  # noqa: E402

MAX_JSON_BYTES = 512 * 1024
MAX_JSON_INT_DIGITS = 80
MAX_RATIONAL_STR_LEN = 162
_CANON_INT_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)$")
_CANON_Q_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)(?:/[1-9][0-9]*)?$")
_RAW_INT_SCAN_RE = re.compile(r"(?<![A-Za-z0-9_.\"])-?[0-9]+(?![A-Za-z0-9_.\"])")

# Full R12 fail-closed Lean 4 trust-escape scanner (0 bypasses, 0 FP on clean controls)
_LEAN4_BANNED_RE = re.compile(
    r"(?:"
    r'["«»]'
    r"|\b(?:sorry|admit|axiom|unsafe|partial|opaque|noncomputable|prelude|native_decide|bv_decide|decide_cbv"
    r"|sorryAx|ofReduceBool|ofReduceNat|trustCompiler|mkSorry|Classical"
    r"|extern|implemented_by|csimp|initialize|builtin_initialize"
    r"|macro|macro_rules|elab|elab_rules|syntax|declare_syntax_cat"
    r"|notation|prefix|infix|infixl|infixr|postfix|run_cmd|run_meta|import"
    r"|throwError|interpolatedStr|set_option"
    r"|dbg_trace|dbg_sleep|dbg_stack_trace"
    r"|dbgTrace|dbgTraceVal|dbgTraceValId|dbgTraceIfShared|dbgSleep|dbgStackTrace"
    r"|panicCore|panicWithPos|panicWithPosWithDecl)\b"
    r"|\b(?:panic|unreachable|assert|debug_assert)!"
    r"|\b(?:debug|warn)\s*\.\s*(?:skipKernelTC|byAsSorry|proofAsSorry|sorryAsError|terminalTacticsAsSorry|sorry)\b"
    r"|@\s*\[\s*(?:(?:local|scoped)\s+)?(?:[^\]\n]*,\s*)?(?:builtin_)?(?:init|export|term_elab|command_elab|tactic|macro(?:_rules)?)\b"
    r"|\battribute\s*\[\s*(?:(?:local|scoped)\s+)?(?:[^\]\n]*,\s*)?(?:builtin_)?(?:init|export|term_elab|command_elab|tactic|macro(?:_rules)?)\b"
    r"|#\s*(?:eval|reduce|exit|check|synth|guard(?:_msgs)?)\b"
    r"|#\s*print\s+(?!axioms\s+HeritageExactOperators\.[A-Za-z0-9_]+\b)"
    r"|(?<!\w)\+\s*native\b"
    r"|\bnative\s*:=(?!\s*(?:Bool\.)?false\b(?:\s*[},)]|\Z))"
    r"|\bDecide(?:Config|\.Config)\b"
    r"|\bconfig\s*:=(?!\s*\{\s*native\s*:=\s*(?:Bool\.)?false\s*\})"
    r")"
)

_LEAN4_AXIOM_NONE_RE = re.compile(r"^'([A-Za-z0-9_.]+)' does not depend on any axioms$")
_LEAN4_AXIOM_DEP_RE = re.compile(r"^'([A-Za-z0-9_.]+)' depends on axioms: \[([^\]]*)\]$")
_ALLOWED_LEAN_AXIOMS = frozenset({"propext", "Quot.sound"})

_ENVELOPE_KEYS = frozenset({"schema_version", "track_id", "payload_sha256", "payload", "certificate_sha256"})
_PAYLOAD_KEYS = frozenset({
    "schema_version", "track_id", "oracle_class", "novelty_classification",
    "heritage_dataset", "modern_anchor_bridges", "pinned_artifacts",
    "engine1_tusi_couple", "engine2_kashi_cubic_chords",
    "engine3_khayyam_curvature_cubics", "engine4_haytham_farisi_biruni",
    "engine5_thabit_khazini_nafis",
})
_PINNED_KEYS = frozenset({
    "lean_source", "lean_source_sha256", "lean_toolchain",
    "lean_toolchain_sha256", "lakefile_sha256",
    "lean_theorem_count", "lean_theorem_names",
})
_DS_KEYS = frozenset({"repo", "commit", "pinned_sources_count", "pinned_sources"})
_SRC_KEYS = frozenset({"id", "engine", "scholar", "work", "relpath", "bytes", "sha256", "live_word_count"})
_MOD_KEYS = frozenset({"track", "cert_file", "cert_sha256", "bridge"})

PINNED_LEAN_SOURCE_SHA256 = "4ac15befb87c774d6fa114e2b864639c68c32f5e170c65e3b6af2ef472cfede3"
PINNED_LEAN_TOOLCHAIN_SHA256 = "582a63f8f9c5128067b688778c1051cf1464c3ca9d57b9325025c051c29b774a"
PINNED_LAKEFILE_SHA256 = "70df68cd815c757ccb7461560b9765c2f206313449a0cbe3759ab5a42501dac9"


# ---------------------------------------------------------------------------
# Zone-B Path & Filesystem Hardening
# ---------------------------------------------------------------------------

def _normalize_darwin_private_prefix(raw: str) -> str:
    if raw == "/private/tmp" or raw.startswith("/private/tmp/"):
        return raw[len("/private"):]
    if raw == "/private/var" or raw.startswith("/private/var/"):
        return raw[len("/private"):]
    return raw


def _check_path_str(raw: Any, label: str) -> Path:
    if isinstance(raw, Path):
        s = os.fspath(raw)
    else:
        s = oracle.require_exact_str(raw, label)
    oracle.require_ok(len(s) > 0, "EMPTY_PATH", f"{label} empty")
    oracle.require_ok("\x00" not in s, "NUL_BYTE_FORBIDDEN", f"{label} contains NUL")
    try:
        s.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise oracle.S90Error("INVALID_UTF8_SURROGATE", f"{label} invalid UTF-8") from exc
    return Path(s)


def _check_no_symlink_components(path: Path, label: str) -> Path:
    abs_p = Path(os.path.abspath(os.fspath(path)))
    cur = Path(abs_p.anchor)
    for part in abs_p.parts[1:]:
        cur = cur / part
        try:
            st = os.lstat(cur)
        except (FileNotFoundError, NotADirectoryError):
            break
        except OSError as exc:
            raise oracle.S90Error("IO_STAT_ERROR", f"{label}: {exc}") from exc
        oracle.require_ok(not stat.S_ISLNK(st.st_mode), "SYMLINK_IN_PATH", f"{label}: symlink at {cur.name}")
    return abs_p


def _check_safe_cwd() -> None:
    try:
        cwd = os.getcwd()
    except OSError as exc:
        raise oracle.S90Error("CWD_ERROR", str(exc)) from exc
    _check_no_symlink_components(Path(cwd), "cwd")
    pwd = os.environ.get("PWD")
    if pwd is not None and pwd.startswith("/"):
        norm_pwd = Path(_normalize_darwin_private_prefix(pwd))
        try:
            pwd_st = os.stat(norm_pwd)
            cwd_st = os.stat(cwd)
        except OSError:
            return
        if pwd_st.st_dev == cwd_st.st_dev and pwd_st.st_ino == cwd_st.st_ino:
            _check_no_symlink_components(norm_pwd, "PWD")


def read_regular_bytes_capped(path: Path | str, label: str, max_bytes: int = MAX_JSON_BYTES) -> bytes:
    _check_safe_cwd()
    p = _check_path_str(path, label)
    abs_p = _check_no_symlink_components(p, label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(os.fspath(abs_p), flags)
    except OSError as exc:
        raise oracle.S90Error("IO_OPEN_ERROR", f"{label}: {exc}") from exc
    try:
        st = os.fstat(fd)
        oracle.require_ok(stat.S_ISREG(st.st_mode), "NON_REGULAR_FILE", f"{label} must be regular file")
        oracle.require_ok(st.st_nlink == 1, "HARDLINK_FORBIDDEN", f"{label} hardlink count {st.st_nlink} != 1")
        oracle.require_ok(st.st_size <= max_bytes, "FILE_TOO_LARGE", f"{label} exceeds {max_bytes} B")
        chunks: list[bytes] = []
        total = 0
        while True:
            blk = os.read(fd, 65536)
            if not blk:
                break
            total += len(blk)
            oracle.require_ok(total <= max_bytes, "FILE_TOO_LARGE", f"{label} grew past {max_bytes} B")
            chunks.append(blk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def write_regular_bytes_atomic_0600(path: Path | str, data: bytes, label: str) -> None:
    _check_safe_cwd()
    p = _check_path_str(path, label)
    abs_p = _check_no_symlink_components(p, label)
    parent = abs_p.parent
    try:
        pst = os.lstat(parent)
    except OSError as exc:
        raise oracle.S90Error("IO_PARENT_ERROR", f"{label} parent missing") from exc
    oracle.require_ok(stat.S_ISDIR(pst.st_mode), "PARENT_NOT_DIR", f"{label} parent not dir")
    try:
        est = os.lstat(abs_p)
    except FileNotFoundError:
        est = None
    except OSError as exc:
        raise oracle.S90Error("IO_STAT_ERROR", f"{label}: {exc}") from exc
    if est is not None:
        oracle.require_ok(stat.S_ISREG(est.st_mode), "NON_REGULAR_TARGET", f"{label} target non-regular")
        oracle.require_ok(est.st_nlink == 1, "HARDLINK_FORBIDDEN", f"{label} target hardlink")
    fd, tmp_name = tempfile.mkstemp(prefix=".s90-tmp-", dir=os.fspath(parent))
    try:
        os.fchmod(fd, 0o600)
        view = memoryview(data)
        written = 0
        while written < len(data):
            n = os.write(fd, view[written:])
            oracle.require_ok(n > 0, "IO_WRITE_SHORT", f"{label} short write")
            written += n
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(tmp_name, os.fspath(abs_p))
    except BaseException:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# Strict Zero-Float Canonical JSON & Rational Parsers
# ---------------------------------------------------------------------------

def _reject_float(token: str) -> Any:
    raise oracle.S90Error("FORBIDDEN_JSON_FLOAT", f"float token forbidden: {token[:32]}")


def _reject_constant(token: str) -> Any:
    raise oracle.S90Error("FORBIDDEN_JSON_CONSTANT", f"constant forbidden: {token[:32]}")


def _strict_int(token: str) -> int:
    digits = token[1:] if token.startswith("-") else token
    oracle.require_ok(len(digits) <= MAX_JSON_INT_DIGITS, "JSON_INT_TOO_LARGE", "int exceeds 80 digits")
    return int(token)


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        oracle.require_ok(k not in out, "DUPLICATE_JSON_KEY", f"duplicate key: {k}")
        out[k] = v
    return out


def parse_strict_json_bytes(raw: bytes, label: str, require_canonical: bool = True) -> dict[str, Any]:
    oracle.require_ok(len(raw) > 0, "EMPTY_JSON", f"{label} empty")
    oracle.require_ok(len(raw) <= MAX_JSON_BYTES, "FILE_TOO_LARGE", f"{label} oversized")
    oracle.require_ok(b"\x00" not in raw, "NUL_BYTE_FORBIDDEN", f"{label} contains NUL")
    oracle.require_ok(not raw.startswith(b"\xef\xbb\xbf"), "BOM_FORBIDDEN", f"{label} UTF-8 BOM forbidden")
    try:
        text = raw.decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise oracle.S90Error("NON_ASCII_JSON", f"{label} must be strict ASCII") from exc
    oracle.require_ok("\r" not in text, "CRLF_FORBIDDEN", f"{label} CR forbidden")
    for m in _RAW_INT_SCAN_RE.finditer(text):
        tok = m.group(0)
        dg = tok[1:] if tok.startswith("-") else tok
        oracle.require_ok(len(dg) <= MAX_JSON_INT_DIGITS, "JSON_INT_TOO_LARGE", "raw int > 80 digits")
    try:
        obj = json.loads(
            text,
            parse_float=_reject_float,
            parse_int=_strict_int,
            parse_constant=_reject_constant,
            object_pairs_hook=_no_duplicate_keys,
        )
    except oracle.S90Error:
        raise
    except Exception as exc:
        raise oracle.S90Error("INVALID_JSON", f"{label}: {exc}") from exc
    oracle.require_ok(type(obj) is dict, "JSON_ROOT_NOT_OBJECT", f"{label} root must be object")
    oracle.validate_strict_json_tree(obj, label)
    if require_canonical:
        canon = oracle.canonical_json_bytes(obj)
        oracle.require_ok(raw == canon, "NON_CANONICAL_JSON", f"{label} not canonical JSON")
    return obj


def parse_canonical_rational_str(val: Any, label: str) -> Fraction:
    s = oracle.require_exact_str(val, label)
    oracle.require_ok(len(s) <= MAX_RATIONAL_STR_LEN, "RATIONAL_TOO_LARGE", f"{label} exceeds {MAX_RATIONAL_STR_LEN} chars")
    oracle.require_ok(_CANON_Q_RE.match(s) is not None, "INVALID_RATIONAL_STR", f"{label}: {s!r}")
    if "/" not in s:
        oracle.require_ok(len(s.lstrip("-")) <= MAX_JSON_INT_DIGITS, "INT_TOO_LARGE", label)
        return Fraction(int(s), 1)
    n_s, d_s = s.split("/", 1)
    oracle.require_ok(len(n_s.lstrip("-")) <= MAX_JSON_INT_DIGITS and len(d_s) <= MAX_JSON_INT_DIGITS, "INT_TOO_LARGE", label)
    num, den = int(n_s), int(d_s)
    oracle.require_ok(den > 1, "NON_CANONICAL_RATIONAL", f"{label}: denominator must be > 1")
    fr = Fraction(num, den)
    oracle.require_ok(fr.denominator == den, "NON_REDUCED_RATIONAL", f"{label}: not reduced")
    return fr


def _require_exact_dict(obj: Any, expected: frozenset[str], label: str) -> dict[str, Any]:
    oracle.require_ok(type(obj) is dict, "INVALID_OBJECT", f"{label} must be dict")
    oracle.require_ok(frozenset(obj.keys()) == expected, "SCHEMA_KEYS_MISMATCH", f"{label} keys mismatch")
    return obj


def _is_prime_ind(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _sigma_ind(n: int) -> int:
    total = 0
    d = 1
    while d * d <= n:
        if n % d == 0:
            total += d
            if d * d != n:
                total += n // d
        d += 1
    return total


# ---------------------------------------------------------------------------
# R12 Static Lean 4 Scanner & Live Lean 4.36.0 Kernel Verifier
# ---------------------------------------------------------------------------

def _strip_lean4_for_static_gate(source: str) -> str:
    """Strip Lean 4 nested block comments and line comments fail-closed."""
    out: list[str] = []
    i = 0
    n = len(source)
    depth = 0
    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""
        if depth > 0:
            if ch == "/" and nxt == "-":
                depth += 1
                out.append("  ")
                i += 2
            elif ch == "-" and nxt == "/":
                depth -= 1
                out.append("  ")
                i += 2
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
            continue
        if ch == "/" and nxt == "-":
            depth = 1
            out.append("  ")
            i += 2
        elif ch == "-" and nxt == "-":
            out.append("  ")
            i += 2
            while i < n and source[i] != "\n":
                out.append(" ")
                i += 1
        else:
            out.append(ch)
            i += 1
    oracle.require_ok(depth == 0, "LEAN4_UNTERMINATED_LEX", "unterminated Lean block comment")
    return "".join(out)


def static_gate_lean4_source(source: str) -> None:
    s = oracle.require_exact_str(source, "lean_source")
    oracle.require_ok("\r" not in s and "\x00" not in s, "LEAN4_BAD_CHARS", "CR/NUL in Lean source")
    cleaned = _strip_lean4_for_static_gate(s)
    m = _LEAN4_BANNED_RE.search(cleaned)
    oracle.require_ok(m is None, "LEAN4_TRUST_ESCAPE", f"banned Lean construct: {m.group(0)!r}" if m else "")
    for thm in oracle.LEAN_THEOREM_NAMES:
        short = thm.split(".")[-1]
        oracle.require_ok(
            re.search(rf"\b(?:(?:private|protected)\s+)?theorem\s+{re.escape(short)}\b", cleaned) is not None,
            "LEAN4_MISSING_THEOREM",
            f"missing {short}",
        )
        oracle.require_ok(
            re.search(rf"(?m)^#print axioms {re.escape(thm)}$", cleaned) is not None,
            "LEAN4_MISSING_PRINT_AXIOMS",
            f"missing #print axioms {thm}",
        )


def resolve_lean_binary() -> str:
    env_bin = os.environ.get("ALETHEIA_LEAN_BIN")
    if env_bin is not None:
        oracle.require_exact_str(env_bin, "ALETHEIA_LEAN_BIN")
        p = Path(env_bin)
        oracle.require_ok(p.is_file() and os.access(str(p), os.X_OK), "LEAN_BINARY_UNAVAILABLE", "ALETHEIA_LEAN_BIN unusable")
        return str(p)
    found = shutil.which("lean")
    if found is not None and os.access(found, os.X_OK):
        return found
    env_home = os.environ.get("HOME")
    if env_home is not None and len(env_home) > 0:
        for rel in ((".local", "bin", "lean"), (".elan", "bin", "lean")):
            cand = Path(env_home).joinpath(*rel)
            if cand.is_file() and os.access(str(cand), os.X_OK):
                return str(cand)
    raise oracle.S90Error("LEAN_BINARY_UNAVAILABLE", "lean executable not found")


def _read_and_static_gate_lean4(lean_path: Path) -> tuple[bytes, str]:
    raw = read_regular_bytes_capped(lean_path, "lean_source", max_bytes=1024 * 1024)
    try:
        src = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise oracle.S90Error("INVALID_UTF8", "Lean source not UTF-8") from exc
    static_gate_lean4_source(src)
    return raw, src


def verify_lean4_file_live(lean_path: Path) -> dict[str, Any]:
    raw, src = _read_and_static_gate_lean4(lean_path)
    lean_bin = resolve_lean_binary()
    lean_env = {
        k: os.environ[k]
        for k in ("PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "LC_ALL")
        if k in os.environ
    }
    try:
        v_proc = subprocess.run([lean_bin, "--version"], env=lean_env, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise oracle.S90Error("LEAN_EXEC_ERROR", "lean --version failed") from exc
    oracle.require_ok(v_proc.returncode == 0 and "4.36.0" in v_proc.stdout, "LEAN_VERSION_MISMATCH", "Lean 4.36.0 required")
    try:
        proc = subprocess.run([lean_bin, "--stdin"], input=src, env=lean_env, capture_output=True, text=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise oracle.S90Error("LEAN_EXEC_ERROR", "lean elaboration failed") from exc
    oracle.require_ok(proc.returncode == 0, "LEAN_COMPILE_FAIL", f"lean rc={proc.returncode}")
    oracle.require_ok(proc.stderr.strip() == "", "LEAN_STDERR_NONEMPTY", "lean stderr must be empty")
    oracle.require_ok("warning:" not in proc.stdout.lower(), "LEAN_WARNING_FORBIDDEN", "lean warning forbidden")

    joined_lines: list[str] = []
    pending = ""
    for raw_line in proc.stdout.splitlines():
        s_line = raw_line.strip()
        if not s_line:
            continue
        if pending:
            pending = f"{pending} {s_line}"
            if "]" in s_line:
                joined_lines.append(pending)
                pending = ""
        elif "[" in s_line and "]" not in s_line:
            pending = s_line
        else:
            joined_lines.append(s_line)
    oracle.require_ok(pending == "", "LEAN_UNEXPECTED_STDOUT", "unterminated axiom list")

    seen: dict[str, list[str]] = {}
    for s_line in joined_lines:
        m_none = _LEAN4_AXIOM_NONE_RE.match(s_line)
        if m_none is not None:
            thm_name = m_none.group(1)
            oracle.require_ok(thm_name not in seen, "LEAN_DUPLICATE_THEOREM", f"duplicate axiom line: {thm_name}")
            seen[thm_name] = []
            continue
        m_dep = _LEAN4_AXIOM_DEP_RE.match(s_line)
        oracle.require_ok(m_dep is not None, "LEAN_UNEXPECTED_STDOUT", f"unexpected lean line: {s_line[:80]}")
        thm_name = m_dep.group(1)
        oracle.require_ok(thm_name not in seen, "LEAN_DUPLICATE_THEOREM", f"duplicate axiom line: {thm_name}")
        axs = [a.strip() for a in m_dep.group(2).split(",") if a.strip()]
        for ax in axs:
            oracle.require_ok(ax in _ALLOWED_LEAN_AXIOMS, "LEAN_FORBIDDEN_AXIOM", f"forbidden axiom {ax}")
        seen[thm_name] = axs
    oracle.require_ok(frozenset(seen.keys()) == frozenset(oracle.LEAN_THEOREM_NAMES), "LEAN_THEOREM_SET_MISMATCH", "axioms set mismatch")
    return {
        "lean_version": v_proc.stdout.strip().splitlines()[0],
        "theorems_verified": len(seen),
        "lean_source_sha256": oracle.sha256_hex(raw),
    }


# ---------------------------------------------------------------------------
# Fail-Closed Secondary Semantic Auditor (Enforced under BOTH FR1 and FR0)
# ---------------------------------------------------------------------------

def _audit_engine1(e1: dict[str, Any]) -> None:
    _require_exact_dict(e1, frozenset({
        "planar_samples", "planar_all_y_zero", "matrix_curl_annihilation",
        "spherical_phase_cos_q", "spherical_phase_sin_q",
        "spherical_hippopede_samples", "all_spherical_norms_exact_one",
        "all_spherical_deviations_nonzero",
    }), "engine1")
    oracle.require_ok(oracle.require_bool(e1["planar_all_y_zero"], "e1.planar") is True, "E1_PLANAR", "planar flag")
    oracle.require_ok(oracle.require_bool(e1["all_spherical_norms_exact_one"], "e1.snorm") is True, "E1_SPHERE", "norm flag")
    oracle.require_ok(oracle.require_bool(e1["all_spherical_deviations_nonzero"], "e1.sdev") is True, "E1_SPHERE", "dev flag")
    prows = e1["planar_samples"]
    oracle.require_ok(type(prows) is list and len(prows) == 6, "E1_PLANAR_LEN", "6 planar rows required")
    for idx, row in enumerate(prows):
        rr = _require_exact_dict(row, frozenset({"t_q", "cos_q", "sin_q", "x_q", "y_q"}), f"e1.p[{idx}]")
        t = parse_canonical_rational_str(rr["t_q"], "t_q")
        c = parse_canonical_rational_str(rr["cos_q"], "cos_q")
        s = parse_canonical_rational_str(rr["sin_q"], "sin_q")
        x = parse_canonical_rational_str(rr["x_q"], "x_q")
        y = parse_canonical_rational_str(rr["y_q"], "y_q")
        oracle.require_ok(
            c == (1 - t * t) / (1 + t * t)
            and s == (2 * t) / (1 + t * t)
            and x == 2 * c
            and y == 0,
            "E1_PLANAR_MATH", f"row {idx}",
        )
    oracle.require_ok([r["t_q"] for r in prows] == ["0", "1/3", "1/2", "1", "2", "3"], "E1_PLANAR_DOM", "planar domain")
    mc = _require_exact_dict(e1["matrix_curl_annihilation"], frozenset({
        "a_q", "b_q", "tusi_avg_diag_q", "tusi_avg_offdiag_q", "trace_preserved_q",
    }), "e1.mat")
    a_m = parse_canonical_rational_str(mc["a_q"], "a_q")
    b_m = parse_canonical_rational_str(mc["b_q"], "b_q")
    oracle.require_ok(
        a_m == Fraction(3, 5)
        and b_m == Fraction(4, 5)
        and parse_canonical_rational_str(mc["tusi_avg_diag_q"], "diag") == a_m
        and parse_canonical_rational_str(mc["tusi_avg_offdiag_q"], "off") == 0
        and parse_canonical_rational_str(mc["trace_preserved_q"], "tr") == 2 * a_m,
        "E1_MAT_MATH", "matrix curl cancellation failed",
    )
    ct = parse_canonical_rational_str(e1["spherical_phase_cos_q"], "ct")
    st = parse_canonical_rational_str(e1["spherical_phase_sin_q"], "st")
    oracle.require_ok(ct == Fraction(3, 5) and st == Fraction(4, 5), "E1_PHASE", "spherical phase mismatch")
    srows = e1["spherical_hippopede_samples"]
    oracle.require_ok(type(srows) is list and len(srows) == 3, "E1_SPHERE_LEN", "3 spherical rows required")
    for idx, row in enumerate(srows):
        rr = _require_exact_dict(row, frozenset({
            "cos_alpha_q", "sin_alpha_q", "px_transverse_q", "px_transverse_dec6",
            "py_longitudinal_q", "py_longitudinal_dec6", "pz_vertical_q", "pz_vertical_dec6", "unit_norm_q",
        }), f"e1.s[{idx}]")
        ca = parse_canonical_rational_str(rr["cos_alpha_q"], "ca")
        sa = parse_canonical_rational_str(rr["sin_alpha_q"], "sa")
        px = parse_canonical_rational_str(rr["px_transverse_q"], "px")
        py = parse_canonical_rational_str(rr["py_longitudinal_q"], "py")
        pz = parse_canonical_rational_str(rr["pz_vertical_q"], "pz")
        oracle.require_ok(
            ca * ca + sa * sa == 1
            and px == 2 * sa * (1 - ca) * st * st * ct
            and py == -2 * sa * st * (ct * ct + ca * st * st)
            and pz == 1 - 2 * sa * sa * st * st,
            "E1_SPHERE_MATH", f"s[{idx}]",
        )
        oracle.require_ok(px > 0 and rr["unit_norm_q"] == "1", "E1_SPHERE_NORM", f"s[{idx}]")
        oracle.require_ok(
            rr["px_transverse_dec6"] == oracle.fmt_dec_q(px, 6)
            and rr["py_longitudinal_dec6"] == oracle.fmt_dec_q(py, 6)
            and rr["pz_vertical_dec6"] == oracle.fmt_dec_q(pz, 6),
            "E1_SPHERE_DEC", f"s[{idx}]",
        )
    oracle.require_ok(
        [(r["cos_alpha_q"], r["sin_alpha_q"]) for r in srows] == [("4/5", "3/5"), ("12/13", "5/13"), ("24/25", "7/25")],
        "E1_SPHERE_DOM", "alpha domain",
    )


def _audit_engine2(e2: dict[str, Any]) -> None:
    _require_exact_dict(e2, frozenset({
        "sexagesimal_p_unit_q", "domain_bound_q", "lipschitz_bound_q",
        "sin3_lo_dec12", "sin3_hi_dec12", "banach_iterations",
        "sin1_final_lo_dec12", "sin1_final_hi_dec12",
        "cancellation_wall_schedule", "rationalized_chord_witnesses",
    }), "engine2")
    p_u = parse_canonical_rational_str(e2["sexagesimal_p_unit_q"], "p_unit")
    b_q = parse_canonical_rational_str(e2["domain_bound_q"], "domain_bound")
    lip = parse_canonical_rational_str(e2["lipschitz_bound_q"], "lipschitz")
    oracle.require_ok(
        p_u == Fraction(3, 4) and b_q == Fraction(1, 50) and lip == (3 * b_q * b_q) / p_u,
        "E2_LIP", "contraction invalid",
    )
    denom = 10 ** 12
    s2_l = Fraction(math.isqrt(2 * denom * denom), denom)
    s2_u = s2_l + Fraction(1, denom)
    s5_l = Fraction(math.isqrt(5 * denom * denom), denom)
    s5_u = s5_l + Fraction(1, denom)
    s6_l = Fraction(math.isqrt(6 * denom * denom), denom)
    s6_u = s6_l + Fraction(1, denom)
    f10_l = 10 + 2 * s5_l
    f10_u = 10 + 2 * s5_u
    s10_l = Fraction(math.isqrt((f10_l.numerator * denom * denom) // f10_l.denominator), denom)
    s10_u = Fraction(math.isqrt((f10_u.numerator * denom * denom) // f10_u.denominator) + 1, denom)
    sin3_lo = ((s5_l - 1) * (s6_l + s2_l) - s10_u * (s6_u - s2_l)) / 16
    sin3_hi = ((s5_u - 1) * (s6_u + s2_u) - s10_l * (s6_l - s2_u)) / 16
    oracle.require_ok(
        e2["sin3_lo_dec12"] == oracle.fmt_dec_q(sin3_lo, 12)
        and e2["sin3_hi_dec12"] == oracle.fmt_dec_q(sin3_hi, 12),
        "E2_SIN3", "sin3 enclosure mismatch",
    )
    iters = e2["banach_iterations"]
    oracle.require_ok(type(iters) is list and len(iters) == 4, "E2_ITER_LEN", "4 iterations required")
    xl, xu = Fraction(0), b_q
    for idx, row in enumerate(iters):
        rr = _require_exact_dict(row, frozenset({
            "iteration", "lo_dec12", "hi_dec12", "width_dec12", "strict_shrink_factor_dec2",
        }), f"e2.it[{idx}]")
        oracle.require_exact_int(rr["iteration"], "iteration", lo=idx + 1, hi=idx + 1)
        prev_w = xu - xl
        xl = (sin3_lo + 4 * xl * xl * xl) / 3
        xu = (sin3_hi + 4 * xu * xu * xu) / 3
        w = xu - xl
        oracle.require_ok(
            rr["lo_dec12"] == oracle.fmt_dec_q(xl, 12)
            and rr["hi_dec12"] == oracle.fmt_dec_q(xu, 12)
            and rr["width_dec12"] == oracle.fmt_dec_q(w, 12)
            and rr["strict_shrink_factor_dec2"] == oracle.fmt_dec_q(prev_w / w, 2),
            "E2_BRACKET", f"it[{idx}]",
        )
    oracle.require_ok(
        e2["sin1_final_lo_dec12"] == iters[-1]["lo_dec12"]
        and e2["sin1_final_hi_dec12"] == iters[-1]["hi_dec12"],
        "E2_SIN1", "sin1 enclosure mismatch",
    )
    sched = e2["cancellation_wall_schedule"]
    oracle.require_ok(type(sched) is list and len(sched) == 5, "E2_WALL_LEN", "5 wall steps required")
    for idx, row in enumerate(sched):
        rr = _require_exact_dict(row, frozenset({
            "halving_step_k", "bits_lost_naive", "exceeds_ieee754_53", "reaches_s47_wmax_64",
        }), f"e2.w[{idx}]")
        k = oracle.require_exact_int(rr["halving_step_k"], "k", lo=1, hi=64)
        lost = oracle.require_exact_int(rr["bits_lost_naive"], "lost", lo=4, hi=200)
        oracle.require_ok(
            lost == 2 * k + 2
            and oracle.require_bool(rr["exceeds_ieee754_53"], "e53") is (lost > 53)
            and oracle.require_bool(rr["reaches_s47_wmax_64"], "e64") is (lost >= 64),
            "E2_WALL_MATH", f"w[{idx}]",
        )
    oracle.require_ok([r["halving_step_k"] for r in sched] == [1, 5, 10, 26, 31], "E2_WALL_DOM", "wall k domain")
    chords = e2["rationalized_chord_witnesses"]
    oracle.require_ok(type(chords) is list and len(chords) == 3, "E2_CHORD_LEN", "3 chord rows")
    for idx, row in enumerate(chords):
        rr = _require_exact_dict(row, frozenset({"c_q", "s_q", "c_next_sq_q", "c_next_sq_dec6"}), f"e2.c[{idx}]")
        c_q = parse_canonical_rational_str(rr["c_q"], "c_q")
        s_q = parse_canonical_rational_str(rr["s_q"], "s_q")
        cn = parse_canonical_rational_str(rr["c_next_sq_q"], "cn")
        oracle.require_ok(s_q > 0 and s_q * s_q + c_q * c_q == 4 and cn == (c_q * c_q) / (2 + s_q), "E2_CHORD_MATH", f"c[{idx}]")
        oracle.require_ok(rr["c_next_sq_dec6"] == oracle.fmt_dec_q(cn, 6), "E2_CHORD_DEC", f"c[{idx}]")
    oracle.require_ok(
        [(r["c_q"], r["s_q"]) for r in chords] == [("6/5", "8/5"), ("10/13", "24/13"), ("14/25", "48/25")],
        "E2_CHORD_DOM", "chord domain",
    )


def _audit_engine3(e3: dict[str, Any]) -> None:
    _require_exact_dict(e3, frozenset({
        "khayyam_14_cubics_catalog_count", "klein_hyperbolic_samples",
        "flagship_exact_cos_summit_q", "euclidean_cos_summit_q", "spherical_obtuse_sign",
        "cubic_discriminant_trichotomy", "khayyam_x3_3x_1_mod2_obstruction",
        "s33_4x3_2x_1_mod8_even_q_count", "s33_all_even_q_residues_equal_4_mod8",
    }), "engine3")
    oracle.require_exact_int(e3["khayyam_14_cubics_catalog_count"], "e3.cat14", lo=14, hi=14)
    oracle.require_ok(
        parse_canonical_rational_str(e3["flagship_exact_cos_summit_q"], "fcos") == Fraction(1, 3)
        and parse_canonical_rational_str(e3["euclidean_cos_summit_q"], "ecos") == 0
        and e3["spherical_obtuse_sign"] == "NEGATIVE_COS",
        "E3_TRICHOTOMY", "curvature trichotomy mismatch",
    )
    krows = e3["klein_hyperbolic_samples"]
    oracle.require_ok(type(krows) is list and len(krows) == 4, "E3_KLEIN_LEN", "4 Klein rows")
    for idx, row in enumerate(krows):
        rr = _require_exact_dict(row, frozenset({"a_q", "h_q", "disk_radius_sq_q", "cos2_summit_q", "cos2_summit_dec6"}), f"e3.k[{idx}]")
        a_q = parse_canonical_rational_str(rr["a_q"], "a_q")
        h_q = parse_canonical_rational_str(rr["h_q"], "h_q")
        rsq = parse_canonical_rational_str(rr["disk_radius_sq_q"], "rsq")
        c2 = parse_canonical_rational_str(rr["cos2_summit_q"], "c2")
        oracle.require_ok(rsq == a_q * a_q + h_q * h_q and rsq < 1, "E3_DISK", f"k[{idx}]")
        oracle.require_ok(c2 == (a_q * a_q * h_q * h_q) / ((1 - a_q * a_q) * (1 - h_q * h_q)) and c2 > 0, "E3_ACUTE", f"k[{idx}]")
        oracle.require_ok(rr["cos2_summit_dec6"] == oracle.fmt_dec_q(c2, 6), "E3_DEC", f"k[{idx}]")
    oracle.require_ok(
        [(r["a_q"], r["h_q"]) for r in krows] == [("1/2", "1/2"), ("1/3", "1/2"), ("3/5", "3/5"), ("1/4", "3/4")],
        "E3_KLEIN_DOM", "Klein domain",
    )
    crows = e3["cubic_discriminant_trichotomy"]
    oracle.require_ok(type(crows) is list and len(crows) == 5, "E3_CUBIC_LEN", "5 cubic rows")
    for idx, row in enumerate(crows):
        rr = _require_exact_dict(row, frozenset({"label", "a", "b", "discriminant", "real_root_count", "regime"}), f"e3.c[{idx}]")
        oracle.require_exact_str(rr["label"], f"e3.c[{idx}].label")
        a_i = oracle.require_exact_int(rr["a"], "a")
        b_i = oracle.require_exact_int(rr["b"], "b")
        disc = oracle.require_exact_int(rr["discriminant"], "disc")
        rrc = oracle.require_exact_int(rr["real_root_count"], "rrc")
        reg = oracle.require_exact_str(rr["regime"], "regime")
        oracle.require_ok(disc == -4 * a_i * a_i * a_i - 27 * b_i * b_i, "E3_DISC_MATH", f"c[{idx}]")
        if disc < 0:
            exp_rrc, exp_reg = 1, "ONE_REAL_ROOT"
        elif disc == 0:
            exp_rrc, exp_reg = 2, "CONIC_TANGENCY_CUSP"
        else:
            exp_rrc, exp_reg = 3, "THREE_REAL_ROOTS_CASUS_IRREDUCIBILIS"
        oracle.require_ok(rrc == exp_rrc and reg == exp_reg, "E3_REGIME", f"c[{idx}]")
    oracle.require_ok(
        [(r["label"], r["a"], r["b"]) for r in crows] == [
            ("x^3 + x - 1", 1, -1),
            ("s33_depressed_u^3 - 2u - 2", -2, -2),
            ("tangency_cusp_x^3 - 3x + 2", -3, 2),
            ("khayyam_x^3 - 3x - 1", -3, -1),
            ("khayyam_x^3 - 3x + 1", -3, 1),
        ],
        "E3_CUBIC_DOM", "cubic domain",
    )
    m2 = e3["khayyam_x3_3x_1_mod2_obstruction"]
    oracle.require_ok(type(m2) is list and len(m2) == 3, "E3_MOD2_LEN", "3 mod-2 rows")
    for row in m2:
        rr = _require_exact_dict(row, frozenset({"p_mod2", "q_mod2", "poly_mod2"}), "e3.m2")
        pm = oracle.require_exact_int(rr["p_mod2"], "pm", lo=0, hi=1)
        qm = oracle.require_exact_int(rr["q_mod2"], "qm", lo=0, hi=1)
        pv = oracle.require_exact_int(rr["poly_mod2"], "pv", lo=1, hi=1)
        oracle.require_ok(pv == (pm * pm * pm - 3 * pm * qm * qm - qm * qm * qm) % 2, "E3_MOD2_MATH", "mod2 mismatch")
    oracle.require_ok([(r["p_mod2"], r["q_mod2"]) for r in m2] == [(0, 1), (1, 0), (1, 1)], "E3_MOD2_DOM", "mod2 domain")
    oracle.require_exact_int(e3["s33_4x3_2x_1_mod8_even_q_count"], "e3.m8", lo=16, hi=16)
    oracle.require_ok(oracle.require_bool(e3["s33_all_even_q_residues_equal_4_mod8"], "e3.m8f") is True, "E3_MOD8_FLAG", "mod8 flag")


def _audit_engine4(e4: dict[str, Any]) -> None:
    _require_exact_dict(e4, frozenset({"alhazen_witness", "al_farisi_rainbow", "al_biruni_geodesy_pole"}), "engine4")
    alh = _require_exact_dict(e4["alhazen_witness"], frozenset({
        "source_A", "eye_B", "quartic_coeffs", "primitive_quartic_coeffs",
        "rational_root_exhaustion", "ferrari_cubic_resolvent_coeffs",
        "resolvent_mod3_residues", "resolvent_mod5_residues",
        "galois_non_constructible_certified", "astroid_inside_point_q",
        "astroid_inside_val_q", "astroid_outside_point_q", "astroid_outside_val_q",
    }), "e4.alh")
    oracle.require_ok(
        alh["source_A"] == [2, 0]
        and alh["eye_B"] == [1, 2]
        and alh["quartic_coeffs"] == [6, 14, -24, -2, 2]
        and alh["primitive_quartic_coeffs"] == [3, 7, -12, -1, 1]
        and alh["ferrari_cubic_resolvent_coeffs"] == [1, 24, -76, -1568]
        and oracle.require_bool(alh["galois_non_constructible_certified"], "e4.gal") is True,
        "E4_ALHAZEN_POLY", "Alhazen quartic/resolvent mismatch",
    )
    rre = alh["rational_root_exhaustion"]
    oracle.require_ok(type(rre) is list and len(rre) == 4, "E4_RRE_LEN", "4 rational root checks")
    for idx, row in enumerate(rre):
        rr = _require_exact_dict(row, frozenset({"candidate_q", "value_q"}), f"e4.rre[{idx}]")
        cand = parse_canonical_rational_str(rr["candidate_q"], "cand")
        val = parse_canonical_rational_str(rr["value_q"], "val")
        exp_val = (((3 * cand + 7) * cand - 12) * cand - 1) * cand + 1
        oracle.require_ok(val == exp_val, "E4_RRE_MATH", f"rre[{idx}]")
    oracle.require_ok([r["candidate_q"] for r in rre] == ["-1", "-1/3", "1/3", "1"], "E4_RRE_DOM", "rre candidates")
    r3 = alh["resolvent_mod3_residues"]
    r5 = alh["resolvent_mod5_residues"]
    oracle.require_ok(type(r3) is list and len(r3) == 3, "E4_ALHAZEN_MOD", "resolvent mod3 len")
    for v in r3:
        oracle.require_exact_int(v, "r3", lo=1, hi=2)
    oracle.require_ok(type(r5) is list and len(r5) == 5, "E4_ALHAZEN_MOD", "resolvent mod5 len")
    for v in r5:
        oracle.require_exact_int(v, "r5", lo=1, hi=4)
    exp_r3 = [(y * y * y + 24 * y * y - 76 * y - 1568) % 3 for y in range(3)]
    exp_r5 = [(y * y * y + 24 * y * y - 76 * y - 1568) % 5 for y in range(5)]
    oracle.require_ok(r3 == exp_r3 and r5 == exp_r5, "E4_ALHAZEN_MOD_VAL", "resolvent residue mismatch")
    ipt = alh["astroid_inside_point_q"]
    opt = alh["astroid_outside_point_q"]
    oracle.require_ok(ipt == ["1/4", "1/4"] and opt == ["1/2", "1/2"], "E4_CAUSTIC_PT", "astroid pts")
    ix = parse_canonical_rational_str(ipt[0], "ix")
    iy = parse_canonical_rational_str(ipt[1], "iy")
    ox = parse_canonical_rational_str(opt[0], "ox")
    oy = parse_canonical_rational_str(opt[1], "oy")
    exp_ki = (ix * ix + iy * iy - 1) ** 3 + 27 * ix * ix * iy * iy
    exp_ko = (ox * ox + oy * oy - 1) ** 3 + 27 * ox * ox * oy * oy
    ki = parse_canonical_rational_str(alh["astroid_inside_val_q"], "ki")
    ko = parse_canonical_rational_str(alh["astroid_outside_val_q"], "ko")
    oracle.require_ok(ki == exp_ki and ko == exp_ko, "E4_CAUSTIC", "astroid caustic mismatch")

    far = _require_exact_dict(e4["al_farisi_rainbow"], frozenset({
        "water_index_n_q", "orders", "alexander_dark_band_cos2_gap_q", "alexander_dark_band_cos2_gap_dec6",
    }), "e4.far")
    n_w = parse_canonical_rational_str(far["water_index_n_q"], "n_w")
    oracle.require_ok(n_w == Fraction(4, 3), "E4_FARISI_N", "expected n=4/3")
    ords = far["orders"]
    oracle.require_ok(type(ords) is list and len(ords) == 3, "E4_FARISI_LEN", "3 orders")
    c2_vals: list[Fraction] = []
    for idx, row in enumerate(ords):
        rr = _require_exact_dict(row, frozenset({"order_k", "cos2_i_q", "cos2_i_dec6"}), f"e4.f[{idx}]")
        k = oracle.require_exact_int(rr["order_k"], "k", lo=idx + 1, hi=idx + 1)
        c2 = parse_canonical_rational_str(rr["cos2_i_q"], "c2")
        oracle.require_ok(c2 == (n_w * n_w - 1) / (k * (k + 2)) and rr["cos2_i_dec6"] == oracle.fmt_dec_q(c2, 6), "E4_FARISI_MATH", f"k={k}")
        c2_vals.append(c2)
    gap = parse_canonical_rational_str(far["alexander_dark_band_cos2_gap_q"], "gap")
    oracle.require_ok(gap == c2_vals[0] - c2_vals[1] and far["alexander_dark_band_cos2_gap_dec6"] == oracle.fmt_dec_q(gap, 6), "E4_FARISI_GAP", "gap mismatch")

    bir = _require_exact_dict(e4["al_biruni_geodesy_pole"], frozenset({
        "samples", "nandana_t1_q", "nandana_t2_q", "nandana_rel_radius_error_q",
        "nandana_rel_radius_error_pct_dec2", "nandana_amplification_ratio_q", "nandana_amplification_ratio_dec4",
    }), "e4.bir")
    bsamp = bir["samples"]
    oracle.require_ok(type(bsamp) is list and len(bsamp) == 4, "E4_BIRUNI_LEN", "4 samples")
    for idx, row in enumerate(bsamp):
        rr = _require_exact_dict(row, frozenset({
            "t_half_dip_q", "r_over_h_q", "r_over_h_dec4", "abs_dlnR_dlnt_q", "abs_dlnR_dlnt_dec6",
        }), f"e4.b[{idx}]")
        tq = parse_canonical_rational_str(rr["t_half_dip_q"], "tq")
        rq = parse_canonical_rational_str(rr["r_over_h_q"], "rq")
        sq = parse_canonical_rational_str(rr["abs_dlnR_dlnt_q"], "sq")
        oracle.require_ok(tq > 0 and tq < 1 and rq == (1 - tq * tq) / (2 * tq * tq) and sq == Fraction(2, 1) / (1 - tq * tq), "E4_BIRUNI_MATH", f"b[{idx}]")
        oracle.require_ok(rr["r_over_h_dec4"] == oracle.fmt_dec_q(rq, 4) and rr["abs_dlnR_dlnt_dec6"] == oracle.fmt_dec_q(sq, 6), "E4_BIRUNI_DEC", f"b[{idx}]")
    oracle.require_ok([r["t_half_dip_q"] for r in bsamp] == ["1/10", "1/50", "1/100", "1/200"], "E4_BIRUNI_DOM", "Biruni domain")
    t1 = parse_canonical_rational_str(bir["nandana_t1_q"], "t1")
    t2 = parse_canonical_rational_str(bir["nandana_t2_q"], "t2")
    rel_e = parse_canonical_rational_str(bir["nandana_rel_radius_error_q"], "rel_e")
    amp = parse_canonical_rational_str(bir["nandana_amplification_ratio_q"], "amp")
    oracle.require_ok(t1 == Fraction(1, 200) and t2 == Fraction(7, 1360), "E4_BIRUNI_POLE", "Nandana t1/t2 mismatch")
    r1 = (1 - t1 * t1) / (2 * t1 * t1)
    r2 = (1 - t2 * t2) / (2 * t2 * t2)
    oracle.require_ok(rel_e == (r1 - r2) / r2 and amp == rel_e / ((t2 - t1) / t2), "E4_BIRUNI_POLE", "pole failed")
    oracle.require_ok(
        bir["nandana_rel_radius_error_pct_dec2"] == oracle.fmt_dec_q(rel_e * 100, 2)
        and bir["nandana_amplification_ratio_dec4"] == oracle.fmt_dec_q(amp, 4),
        "E4_BIRUNI_PDEC", "pole dec mismatch",
    )


def _audit_engine5(e5: dict[str, Any]) -> None:
    _require_exact_dict(e5, frozenset({
        "thabit_amicable_cases", "thabit_n3_r_factorization",
        "khazini_alloy_inverse_cases", "nafis_pulmonary_conductance_q", "nafis_septal_rerouting_cases",
    }), "engine5")
    trows = e5["thabit_amicable_cases"]
    oracle.require_ok(type(trows) is list and len(trows) == 4, "E5_THABIT_LEN", "4 Thabit cases")
    for idx, row in enumerate(trows):
        rr = _require_exact_dict(row, frozenset({
            "n", "p", "q", "r", "p_prime", "q_prime", "r_prime",
            "A", "B", "sigma_A", "sigma_B", "amicable", "sigma_B_excess",
        }), f"e5.t[{idx}]")
        n = oracle.require_exact_int(rr["n"], "n", lo=1, hi=7)
        k = 1 << (n - 1)
        p = oracle.require_exact_int(rr["p"], "p")
        q = oracle.require_exact_int(rr["q"], "q")
        r = oracle.require_exact_int(rr["r"], "r")
        A = oracle.require_exact_int(rr["A"], "A")
        B = oracle.require_exact_int(rr["B"], "B")
        sA = oracle.require_exact_int(rr["sigma_A"], "sA")
        sB = oracle.require_exact_int(rr["sigma_B"], "sB")
        exc = oracle.require_exact_int(rr["sigma_B_excess"], "exc")
        pp = oracle.require_bool(rr["p_prime"], "p_prime")
        qp = oracle.require_bool(rr["q_prime"], "q_prime")
        rp = oracle.require_bool(rr["r_prime"], "r_prime")
        am = oracle.require_bool(rr["amicable"], "amicable")
        oracle.require_ok(p == 3 * k - 1 and q == 6 * k - 1 and r == 18 * k * k - 1, "E5_THABIT_PQR", f"n={n}")
        oracle.require_ok(A == 2 * k * p * q and B == 2 * k * r and exc == sB - (A + B), "E5_THABIT_AB", f"n={n}")
        oracle.require_ok(
            pp is _is_prime_ind(p) and qp is _is_prime_ind(q) and rp is _is_prime_ind(r),
            "E5_THABIT_PRIME", f"n={n}",
        )
        oracle.require_ok(sA == _sigma_ind(A) and sB == _sigma_ind(B), "E5_THABIT_SIGMA", f"n={n}")
        oracle.require_ok(am is (sA == A + B and sB == A + B), "E5_THABIT_AM", f"n={n}")
    oracle.require_ok([r["n"] for r in trows] == [2, 3, 4, 7], "E5_THABIT_DOM", "expected n=[2,3,4,7]")
    oracle.require_ok(e5["thabit_n3_r_factorization"] == [7, 41], "E5_THABIT_N3", "expected [7,41]")

    krows = e5["khazini_alloy_inverse_cases"]
    oracle.require_ok(type(krows) is list and len(krows) == 3, "E5_KHAZINI_LEN", "3 Khazini pairs")
    for idx, row in enumerate(krows):
        rr = _require_exact_dict(row, frozenset({
            "pair", "s1_q", "s2_q", "density_gap_q", "buoyancy_u_q",
            "recovered_w1_q", "recovered_w2_q", "perturbation_kappa_q", "perturbation_kappa_dec4",
        }), f"e5.k[{idx}]")
        oracle.require_exact_str(rr["pair"], f"e5.k[{idx}].pair")
        s1 = parse_canonical_rational_str(rr["s1_q"], "s1")
        s2 = parse_canonical_rational_str(rr["s2_q"], "s2")
        gap = parse_canonical_rational_str(rr["density_gap_q"], "gap")
        u = parse_canonical_rational_str(rr["buoyancy_u_q"], "u")
        w1 = parse_canonical_rational_str(rr["recovered_w1_q"], "w1")
        w2 = parse_canonical_rational_str(rr["recovered_w2_q"], "w2")
        kap = parse_canonical_rational_str(rr["perturbation_kappa_q"], "kap")
        oracle.require_ok(
            s2 > 0
            and s1 > s2
            and gap == s1 - s2
            and w1 == Fraction(3, 1)
            and w2 == Fraction(1, 1)
            and u == w1 / s1 + w2 / s2
            and kap == (s1 * s2) / gap,
            "E5_KHAZINI_MATH", f"k[{idx}]",
        )
        oracle.require_ok(rr["perturbation_kappa_dec4"] == oracle.fmt_dec_q(kap, 4), "E5_KHAZINI_DEC", f"k[{idx}]")
    oracle.require_ok(
        [(r["pair"], r["s1_q"], r["s2_q"]) for r in krows] == [
            ("Gold/Silver", "381/20", "103/10"),
            ("Gold/Copper", "381/20", "433/50"),
            ("Copper/Iron", "433/50", "387/50"),
        ],
        "E5_KHAZINI_DOM", "Khazini pair domain",
    )

    gp = parse_canonical_rational_str(e5["nafis_pulmonary_conductance_q"], "gp")
    oracle.require_ok(gp == Fraction(1, 1), "E5_NAFIS_GP", "g_pulm must be 1")
    nrows = e5["nafis_septal_rerouting_cases"]
    oracle.require_ok(type(nrows) is list and len(nrows) == 4, "E5_NAFIS_LEN", "4 Nafis rows")
    for idx, row in enumerate(nrows):
        rr = _require_exact_dict(row, frozenset({
            "septal_pore_w_q", "total_conductance_q", "pulmonary_fraction_q",
            "pulmonary_fraction_pct_dec2", "septal_leak_fraction_pct_dec2",
        }), f"e5.n[{idx}]")
        ws = parse_canonical_rational_str(rr["septal_pore_w_q"], "ws")
        gt = parse_canonical_rational_str(rr["total_conductance_q"], "gt")
        fp = parse_canonical_rational_str(rr["pulmonary_fraction_q"], "fp")
        oracle.require_ok(ws >= 0 and gt == ws + gp and fp == gp / gt, "E5_NAFIS_MATH", f"n[{idx}]")
        oracle.require_ok(
            rr["pulmonary_fraction_pct_dec2"] == oracle.fmt_dec_q(fp * 100, 2)
            and rr["septal_leak_fraction_pct_dec2"] == oracle.fmt_dec_q((ws / gt) * 100, 2),
            "E5_NAFIS_DEC", f"n[{idx}]",
        )
    oracle.require_ok([r["septal_pore_w_q"] for r in nrows] == ["0", "1/2", "1", "2"], "E5_NAFIS_DOM", "Nafis domain")


def secondary_audit_payload(payload: Any) -> dict[str, Any]:
    """Fail-closed semantic + algebraic auditor enforced under BOTH FR1 and FR0."""
    oracle.require_ok(type(payload) is dict, "INVALID_PAYLOAD_TYPE", "payload must be exact dict")
    oracle.validate_strict_json_tree(payload, "payload")
    _require_exact_dict(payload, _PAYLOAD_KEYS, "payload")
    oracle.require_ok(payload["schema_version"] == oracle.SCHEMA_VERSION, "SCHEMA_MISMATCH", "schema_version")
    oracle.require_ok(payload["track_id"] == oracle.TRACK_ID, "SCHEMA_MISMATCH", "track_id")
    oracle.require_ok(payload["oracle_class"] == "exact", "SCHEMA_MISMATCH", "oracle_class")
    oracle.require_ok(payload["novelty_classification"] == "N1", "SCHEMA_MISMATCH", "novelty")

    ds = _require_exact_dict(payload["heritage_dataset"], _DS_KEYS, "heritage_dataset")
    oracle.require_ok(ds["repo"] == oracle.HERITAGE_DATASET_REPO, "DS_REPO", "repo mismatch")
    oracle.require_ok(ds["commit"] == oracle.HERITAGE_DATASET_COMMIT, "DS_COMMIT", "commit mismatch")
    n_src = oracle.require_exact_int(ds["pinned_sources_count"], "n_src", lo=11, hi=11)
    srcs = ds["pinned_sources"]
    oracle.require_ok(type(srcs) is list and len(srcs) == n_src, "DS_SRCS_LEN", "11 heritage sources")
    for idx, src in enumerate(srcs):
        rr = _require_exact_dict(src, _SRC_KEYS, f"src[{idx}]")
        oracle.require_hex64(rr["sha256"], f"src[{idx}].sha256")
        oracle.require_exact_int(rr["bytes"], f"src[{idx}].bytes", lo=1)
        oracle.require_exact_int(rr["live_word_count"], f"src[{idx}].words", lo=0)
    oracle.require_ok(
        [(r["id"], r["engine"], r["scholar"], r["work"], r["relpath"], r["bytes"], r["sha256"], r["live_word_count"]) for r in srcs]
        == [(r["id"], r["engine"], r["scholar"], r["work"], r["relpath"], r["bytes"], r["sha256"], r["live_word_count"]) for r in oracle.HERITAGE_SOURCES],
        "DS_SRCS_PIN", "heritage source pins mismatch",
    )

    mods = payload["modern_anchor_bridges"]
    oracle.require_ok(type(mods) is list and len(mods) == 10, "MOD_LEN", "10 modern anchors")
    for idx, mb in enumerate(mods):
        rr = _require_exact_dict(mb, _MOD_KEYS, f"mod[{idx}]")
        oracle.require_hex64(rr["cert_sha256"], f"mod[{idx}].sha256")
    oracle.require_ok(
        [(r["track"], r["cert_file"], r["cert_sha256"], r["bridge"]) for r in mods]
        == [(r["track"], r["cert_file"], r["cert_sha256"], r["bridge"]) for r in oracle.MODERN_ANCHOR_CERTS],
        "MOD_PIN", "modern anchor pins mismatch",
    )

    pa = _require_exact_dict(payload["pinned_artifacts"], _PINNED_KEYS, "pinned_artifacts")
    oracle.require_ok(pa["lean_source"] == "HeritageExactOperators.lean", "SCHEMA_MISMATCH", "lean_source")
    oracle.require_hex64(pa["lean_source_sha256"], "lean_source_sha256")
    oracle.require_ok(pa["lean_toolchain"] == oracle.EXPECTED_LEAN_TOOLCHAIN, "SCHEMA_MISMATCH", "lean_toolchain")
    oracle.require_hex64(pa["lean_toolchain_sha256"], "lean_toolchain_sha256")
    oracle.require_hex64(pa["lakefile_sha256"], "lakefile_sha256")
    oracle.require_ok(
        (pa["lean_source_sha256"], pa["lean_toolchain_sha256"], pa["lakefile_sha256"])
        == (PINNED_LEAN_SOURCE_SHA256, PINNED_LEAN_TOOLCHAIN_SHA256, PINNED_LAKEFILE_SHA256),
        "PINNED_SHA_MISMATCH", "pinned artifact SHA mismatch",
    )
    thm_n = oracle.require_exact_int(
        pa["lean_theorem_count"], "lean_theorem_count", lo=len(oracle.LEAN_THEOREM_NAMES), hi=len(oracle.LEAN_THEOREM_NAMES)
    )
    thms = pa["lean_theorem_names"]
    oracle.require_ok(type(thms) is list and tuple(thms) == oracle.LEAN_THEOREM_NAMES, "THEOREM_LIST_MISMATCH", "lean_theorem_names")

    _audit_engine1(payload["engine1_tusi_couple"])
    _audit_engine2(payload["engine2_kashi_cubic_chords"])
    _audit_engine3(payload["engine3_khayyam_curvature_cubics"])
    _audit_engine4(payload["engine4_haytham_farisi_biruni"])
    _audit_engine5(payload["engine5_thabit_khazini_nafis"])

    return {
        "secondary_audit_passed": True,
        "heritage_sources_pinned": n_src,
        "modern_bridges_pinned": len(mods),
        "lean_theorem_count": thm_n,
    }


def _load_track_artifacts(
    track_dir: Path,
    *,
    live_lean: bool = True,
) -> tuple[str, str, str, dict[str, Any]]:
    lean_p = track_dir / "HeritageExactOperators.lean"
    tc_p = track_dir / "lean-toolchain"
    lk_p = track_dir / "lakefile.toml"
    tc_raw = read_regular_bytes_capped(tc_p, "lean-toolchain", max_bytes=4096)
    lk_raw = read_regular_bytes_capped(lk_p, "lakefile.toml", max_bytes=65536)
    try:
        tc_text = tc_raw.decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise oracle.S90Error("INVALID_UTF8", "lean-toolchain not UTF-8") from exc
    oracle.require_ok(tc_text == oracle.EXPECTED_LEAN_TOOLCHAIN, "TOOLCHAIN_MISMATCH", f"got {tc_text!r}")
    if live_lean:
        lean_res = verify_lean4_file_live(lean_p)
        l_sha = lean_res["lean_source_sha256"]
    else:
        lean_raw, _ = _read_and_static_gate_lean4(lean_p)
        l_sha = oracle.sha256_hex(lean_raw)
        lean_res = {"lean_source_sha256": l_sha, "mode": "static_r10_only"}
    return (
        l_sha,
        oracle.sha256_hex(tc_raw),
        oracle.sha256_hex(lk_raw),
        lean_res,
    )


def verify_certificate_dict(
    cert: Any,
    *,
    full_replay: bool = True,
    track_dir: Path | None = None,
) -> dict[str, Any]:
    oracle.require_bool(full_replay, "full_replay")
    oracle.require_ok(type(cert) is dict, "INVALID_CERT_TYPE", "certificate must be exact dict")
    oracle.validate_strict_json_tree(cert, "certificate")
    _require_exact_dict(cert, _ENVELOPE_KEYS, "certificate")
    oracle.require_ok(cert["schema_version"] == oracle.SCHEMA_VERSION, "SCHEMA_MISMATCH", "envelope schema_version")
    oracle.require_ok(cert["track_id"] == oracle.TRACK_ID, "SCHEMA_MISMATCH", "envelope track_id")

    payload = cert["payload"]
    sec = secondary_audit_payload(payload)

    expected_payload_sha = oracle.sha256_hex(oracle.canonical_json_bytes(payload))
    oracle.require_ok(
        oracle.require_hex64(cert["payload_sha256"], "payload_sha256") == expected_payload_sha,
        "PAYLOAD_SHA_MISMATCH", "payload_sha256 mismatch",
    )
    envelope_body = {
        "schema_version": cert["schema_version"],
        "track_id": cert["track_id"],
        "payload_sha256": cert["payload_sha256"],
        "payload": payload,
    }
    expected_cert_sha = oracle.sha256_hex(oracle.canonical_json_bytes(envelope_body))
    oracle.require_ok(
        oracle.require_hex64(cert["certificate_sha256"], "certificate_sha256") == expected_cert_sha,
        "CERT_SHA_MISMATCH", "certificate_sha256 mismatch",
    )

    out: dict[str, Any] = {
        "valid": True,
        "full_replay": full_replay,
        "certificate_sha256": expected_cert_sha,
        "payload_sha256": expected_payload_sha,
        "secondary_audit": sec,
    }
    if full_replay:
        root = Path(_THIS_DIR) if track_dir is None else track_dir
        l_sha, tc_sha, lk_sha, lean_live = _load_track_artifacts(root)
        rebuilt = oracle.build_certificate(
            lean_source_sha256=l_sha,
            toolchain_sha256=tc_sha,
            lakefile_sha256=lk_sha,
        )
        oracle.require_ok(
            oracle.canonical_json_bytes(rebuilt) == oracle.canonical_json_bytes(cert),
            "FULL_REPLAY_MISMATCH", "certificate disagrees with live deterministic replay",
        )
        out["lean_live"] = lean_live
    return out


def check_certificate_file(
    path: Path | str,
    *,
    full_replay: bool = True,
    track_dir: Path | None = None,
) -> dict[str, Any]:
    raw = read_regular_bytes_capped(path, "certificate", max_bytes=MAX_JSON_BYTES)
    cert = parse_strict_json_bytes(raw, "certificate", require_canonical=True)
    res = verify_certificate_dict(cert, full_replay=full_replay, track_dir=track_dir)
    res["file_sha256"] = oracle.sha256_hex(raw)
    return res


def write_certificate_file(path: Path | str, track_dir: Path | None = None) -> dict[str, Any]:
    root = Path(_THIS_DIR) if track_dir is None else track_dir
    l_sha, tc_sha, lk_sha, lean_live = _load_track_artifacts(root)
    cert = oracle.build_certificate(
        lean_source_sha256=l_sha,
        toolchain_sha256=tc_sha,
        lakefile_sha256=lk_sha,
    )
    raw = oracle.canonical_json_bytes(cert)
    write_regular_bytes_atomic_0600(path, raw, "certificate")
    return {
        "written": True,
        "bytes": len(raw),
        "file_sha256": oracle.sha256_hex(raw),
        "certificate_sha256": cert["certificate_sha256"],
        "payload_sha256": cert["payload_sha256"],
        "lean_live": lean_live,
    }


def _parse_cli_args(argv: Any) -> dict[str, Any]:
    oracle.require_ok(type(argv) is list, "INVALID_ARGV", "argv must be exact list")
    mode: str | None = None
    target_path: str | None = None
    want_json = False
    i = 0
    n = len(argv)
    while i < n:
        arg = oracle.require_exact_str(argv[i], "argv")
        oracle.require_ok("\x00" not in arg, "NUL_BYTE_FORBIDDEN", "NUL byte in argv")
        if arg == "--json":
            oracle.require_ok(not want_json, "DUPLICATE_FLAG", "--json repeated")
            want_json = True
            i += 1
        elif arg == "--standalone":
            oracle.require_ok(mode is None, "CONFLICTING_MODE", "conflicting mode flags")
            mode = "standalone"
            i += 1
        elif arg in ("--check", "--write"):
            oracle.require_ok(mode is None, "CONFLICTING_MODE", "conflicting mode flags")
            oracle.require_ok(i + 1 < n, "MISSING_PATH_ARG", f"{arg} requires a path")
            val = oracle.require_exact_str(argv[i + 1], f"{arg} path")
            oracle.require_ok("\x00" not in val, "NUL_BYTE_FORBIDDEN", f"NUL byte in {arg} path")
            oracle.require_ok(len(val) > 0 and not val.startswith("-"), "INVALID_PATH_ARG", f"invalid path {val!r}")
            mode = arg[2:]
            target_path = val
            i += 2
        elif arg.startswith("--check=") or arg.startswith("--write="):
            oracle.require_ok(mode is None, "CONFLICTING_MODE", "conflicting mode flags")
            flag_name, val = arg.split("=", 1)
            oracle.require_ok(len(val) > 0 and not val.startswith("-"), "INVALID_PATH_ARG", f"invalid path {val!r}")
            mode = flag_name[2:]
            target_path = val
            i += 1
        else:
            raise oracle.S90Error("UNKNOWN_FLAG", f"unsupported flag: {arg!r}")
    return {"mode": mode or "default", "target": target_path, "json": want_json}


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv: Any = list(sys.argv[1:]) if argv is None else argv
    try:
        opts = _parse_cli_args(raw_argv)
        mode = opts["mode"]
        if mode == "standalone":
            root = Path(_THIS_DIR)
            l_sha, tc_sha, lk_sha, _ = _load_track_artifacts(root, live_lean=False)
            oracle.require_ok(
                (l_sha, tc_sha, lk_sha)
                == (PINNED_LEAN_SOURCE_SHA256, PINNED_LEAN_TOOLCHAIN_SHA256, PINNED_LAKEFILE_SHA256),
                "PINNED_SHA_MISMATCH",
                "standalone Lean artifact digest mismatch",
            )
            cert = oracle.build_certificate(
                lean_source_sha256=l_sha,
                toolchain_sha256=tc_sha,
                lakefile_sha256=lk_sha,
            )
            sys.stdout.write(oracle.canonical_json_bytes(cert).decode("ascii"))
            return 0
        if mode == "write":
            res = write_certificate_file(Path(opts["target"]))
            if opts["json"]:
                sys.stdout.write(oracle.canonical_json_bytes(res).decode("ascii"))
            else:
                sys.stdout.write(f"WROTE {res['file_sha256']}\n")
            return 0
        if mode == "check":
            res = check_certificate_file(Path(opts["target"]), full_replay=True)
            if opts["json"]:
                sys.stdout.write(oracle.canonical_json_bytes(res).decode("ascii"))
            else:
                sys.stdout.write(f"OK {res['certificate_sha256']}\n")
            return 0
        res = check_certificate_file(Path(_THIS_DIR) / "s90_heritage_operators_certificate.json", full_replay=True)
        if opts["json"]:
            sys.stdout.write(oracle.canonical_json_bytes(res).decode("ascii"))
        else:
            sys.stdout.write(f"OK {res['certificate_sha256']}\n")
        return 0
    except oracle.S90Error as exc:
        err_obj = {"error": True, "code": exc.code, "detail": exc.detail}
        sys.stderr.write(json.dumps(err_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
