#!/usr/bin/env python3
"""Track S162 (EXP-Q43a & EXP-Q43b) Zone-B Hardened Verifier, Field-Complete
Secondary Mathematical Auditor (SEC/FR0/FR1), R12-Grade Static Lean 4 Scanner,
and Live Lean 4.36.0 Kernel Verifier.

CLI modes:
  --check [path] [--json] [--live-lean]    Verify certificate + replay + Lean 4.36.0
  --write [path] [--json]                  Atomically write canonical certificate (0o600)
  --standalone                             Emit canonical certificate JSON to stdout
  --verify-data [malecns_dir] [--json]     Also re-hash external read-only MaleCNS .feather files
  [--json]                                 Default: check committed certificate in track dir
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Callable

_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import s162_malecns_neuro_bridge_oracle as oracle  # noqa: E402

MAX_JSON_BYTES = 512 * 1024
MAX_JSON_INT_DIGITS = 80
MAX_JSON_DEPTH = 32
_CANON_Q_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)(?:/[1-9][0-9]*)?$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_LEAN4_BANNED_RE = re.compile(
    r"""
    (?<![A-Za-z0-9_])(?:
        sorry | admit | axiom | unsafe | native_decide | sorryAx
        | Classical | ofReduceBool | ofReduceNat | trustCompiler
        | implemented_by | extern | initialize | builtin_initialize
        | run_cmd | run_meta | run_tac | syntax | declare_syntax_cat
        | macro | macro_rules | elab | elab_rules | notation
        | dbg_trace | dbgTrace | dbgTraceVal | dbgTraceIfShared
        | dbgSleep | dbgStackTrace | panicWithPosWithDecl | throwError
        | csimp | opaque | import | mkSorry | bv_decide | set_option
    )(?![A-Za-z0-9_])
    | (?<![A-Za-z0-9_])(?:panic|unreachable)!
    | (?:\#\s*(?:eval|reduce|exit|check|synth|guard(?:_msgs)?)\b)
    | (?:\bIO\s*\.)
    | (?:\bdebug\s*\.\s*(?:skipKernelTC|byAsSorry|proofAsSorry|sorryAsError)\b)
    | (?:\bwarn\s*\.\s*sorry\b)
    """,
    re.VERBOSE,
)

_PUB_THM_RE = re.compile(r"(?:^|\n)[ \t]*theorem[ \t]+([A-Za-z0-9_]+)\b")
_PRINT_AXIOMS_RE = re.compile(
    r"(?:^|\n)[ \t]*#print[ \t]+axioms[ \t]+MaleCNSNeuroBridge\.([A-Za-z0-9_]+)\b"
)
_AXIOM_ENTRY_RE = re.compile(
    r"'([A-Za-z0-9_.]+)'\s+(does not depend on any axioms|depends on axioms:\s*\[([^\]]*)\])",
    re.DOTALL,
)
_ALLOWED_LEAN_AXIOMS = frozenset({"propext", "Quot.sound"})

_ENVELOPE_KEYS = frozenset({
    "schema_version", "track_id", "payload_sha256", "certificate_sha256", "payload",
})
_PAYLOAD_KEYS = frozenset({
    "schema_version",
    "track_id",
    "oracle_class",
    "novelty_classification",
    "exp_q43a_bp_frustration_and_cavity",
    "exp_q43b_five_operator_wave22_tomography",
    "provenance_and_lean4",
})


def require_ok(cond: bool, code: str, message: str) -> None:
    if type(cond) is not bool or not cond:
        raise oracle.S162Error(code, message)


# ---------------------------------------------------------------------------
# Zone-B Path, Filesystem & Strict JSON Hardening
# ---------------------------------------------------------------------------


def _check_path_str(raw: Any, label: str) -> Path:
    if isinstance(raw, Path):
        s = os.fspath(raw)
    else:
        require_ok(type(raw) is str, "TYPE_ERROR", f"{label}: expected str or Path")
        s = raw
    require_ok(len(s) > 0, "EMPTY_PATH", f"{label}: empty path")
    require_ok("\x00" not in s, "NUL_BYTE_FORBIDDEN", f"{label}: NUL byte forbidden")
    try:
        s.encode("utf-8", "strict")
    except UnicodeEncodeError as exc:
        raise oracle.S162Error("INVALID_UTF8_SURROGATE", f"{label}: invalid UTF-8") from exc
    return Path(s)


def _unnormalized_parts(path: Path) -> tuple[str, ...]:
    if path.is_absolute():
        return path.parts
    return (Path(os.getcwd()) / path).parts


def _check_no_symlink_components(path: Path, label: str) -> Path:
    parts = _unnormalized_parts(path)
    cur = Path("/")
    for part in parts[1:]:
        cur = cur / part
        try:
            st = os.lstat(cur)
        except (FileNotFoundError, NotADirectoryError):
            break
        except OSError as exc:
            raise oracle.S162Error("IO_STAT_ERROR", f"{label}: {exc}") from exc
        require_ok(
            not stat.S_ISLNK(st.st_mode),
            "SYMLINK_IN_PATH",
            f"{label}: symlink rejected at {cur.name}",
        )
    return Path(os.path.abspath(os.fspath(path)))


def read_regular_bytes_capped(
    path_like: Any, label: str, max_bytes: int = MAX_JSON_BYTES
) -> bytes:
    oracle.require_exact_int(max_bytes, "max_bytes", lo=1, hi=64 * 1024 * 1024)
    p = _check_no_symlink_components(_check_path_str(path_like, label), label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(os.fspath(p), flags)
    except OSError as exc:
        raise oracle.S162Error("IO_OPEN_ERROR", f"{label}: {exc}") from exc
    try:
        st = os.fstat(fd)
        require_ok(stat.S_ISREG(st.st_mode), "NOT_REGULAR_FILE", f"{label}: not regular")
        require_ok(st.st_nlink == 1, "HARDLINK_FORBIDDEN", f"{label}: st_nlink={st.st_nlink}")
        require_ok(st.st_size <= max_bytes, "FILE_TOO_LARGE", f"{label}: exceeds {max_bytes}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total = total + len(chunk)
            require_ok(
                total <= max_bytes,
                "FILE_STREAM_TOO_LARGE",
                f"{label}: stream exceeds {max_bytes}",
            )
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def write_regular_bytes_atomic_0600(path_like: Any, data: bytes, label: str) -> Path:
    require_ok(type(data) is bytes, "INVALID_BYTES", f"{label}: data must be bytes")
    p = _check_no_symlink_components(_check_path_str(path_like, label), label)
    parent = p.parent
    try:
        pst = os.lstat(parent)
    except OSError as exc:
        raise oracle.S162Error("PARENT_STAT_ERROR", f"{label}: {exc}") from exc
    require_ok(stat.S_ISDIR(pst.st_mode), "PARENT_NOT_DIR", f"{label}: parent not dir")
    try:
        tst = os.lstat(p)
    except FileNotFoundError:
        tst = None
    except OSError as exc:
        raise oracle.S162Error("TARGET_STAT_ERROR", f"{label}: {exc}") from exc
    if tst is not None:
        require_ok(stat.S_ISREG(tst.st_mode), "TARGET_NOT_REGULAR", f"{label}: target not regular")
        require_ok(tst.st_nlink == 1, "TARGET_HARDLINK", f"{label}: target st_nlink={tst.st_nlink}")
    fd = -1
    tmp_name = ""
    try:
        fd, tmp_name = tempfile.mkstemp(prefix=".s162_tmp_", dir=os.fspath(parent))
        os.fchmod(fd, 0o600)
        view = memoryview(data)
        written = 0
        while written < len(view):
            written = written + os.write(fd, view[written:])
        os.fsync(fd)
        os.close(fd)
        fd = -1
        os.replace(tmp_name, os.fspath(p))
        tmp_name = ""
    except OSError as exc:
        raise oracle.S162Error("IO_WRITE_ERROR", f"{label}: {exc}") from exc
    finally:
        if fd >= 0:
            os.close(fd)
        if tmp_name:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
    return p


def _scan_json_text_strict(text: str) -> None:
    require_ok(not text.startswith("\ufeff"), "BAD_BOM", "UTF-8 BOM rejected")
    require_ok("\r" not in text, "BAD_CRLF", "CR line ending rejected")
    require_ok(text.endswith("\n"), "BAD_TRAILING_NEWLINE", "JSON must end with LF")
    depth = 0
    in_str = False
    escaped = False
    digit_run = 0
    prev_digit = False
    for ch in text:
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            digit_run = 0
            prev_digit = False
            continue
        if ch == '"':
            in_str = True
            digit_run = 0
            prev_digit = False
            continue
        if ch in "{[":
            depth = depth + 1
            require_ok(depth <= MAX_JSON_DEPTH, "JSON_TOO_DEEP", "JSON nesting exceeded")
        elif ch in "}]":
            depth = depth - 1
            require_ok(depth >= 0, "JSON_UNBALANCED", "JSON nesting negative")
        if ch.isdigit():
            digit_run = digit_run + 1
            require_ok(
                digit_run <= MAX_JSON_INT_DIGITS,
                "JSON_INT_TOO_LARGE",
                "JSON integer digit bound exceeded",
            )
            prev_digit = True
        else:
            if prev_digit:
                require_ok(ch not in ".eE", "FLOAT_FORBIDDEN", "JSON float token rejected")
            digit_run = 0
            prev_digit = False
    require_ok(depth == 0, "JSON_UNBALANCED_FINAL", "unbalanced JSON brackets")
    require_ok(not in_str, "JSON_UNTERMINATED_STR", "unterminated JSON string")


def parse_strict_json_bytes(raw: bytes, label: str) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise oracle.S162Error("BAD_UTF8", f"{label}: invalid UTF-8") from exc
    _scan_json_text_strict(text)
    try:
        obj = json.loads(
            text,
            parse_int=oracle._reject_large_int,
            parse_float=oracle._reject_float,
            parse_constant=oracle._reject_constant,
            object_pairs_hook=oracle._reject_dup_keys,
        )
    except oracle.S162Error:
        raise
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise oracle.S162Error("JSON_INVALID", f"{label}: {exc}") from exc
    require_ok(type(obj) is dict, "JSON_NOT_OBJECT", f"{label}: root must be dict")
    return obj


# ---------------------------------------------------------------------------
# R12-Grade Static Lean 4 Scanner & Live Lean 4.36.0 Kernel Verifier
# ---------------------------------------------------------------------------


def strip_lean_comments_and_strings(src: str) -> str:
    out: list[str] = []
    i = 0
    n = len(src)
    depth = 0
    in_str = False
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if (i + 1 < n) else ""
        if depth > 0:
            if ch == "/":
                if nxt == "-":
                    depth = depth + 1
                    out.append("  ")
                    i = i + 2
                    continue
            if ch == "-":
                if nxt == "/":
                    depth = depth - 1
                    out.append("  ")
                    i = i + 2
                    continue
            out.append("\n" if ch == "\n" else " ")
            i = i + 1
            continue
        if in_str:
            if ch == "\\":
                if i + 1 < n:
                    out.append("  ")
                    i = i + 2
                    continue
            if ch == '"':
                in_str = False
                out.append(" ")
                i = i + 1
                continue
            out.append("\n" if ch == "\n" else " ")
            i = i + 1
            continue
        if ch == "-":
            if nxt == "-":
                while i < n:
                    if src[i] == "\n":
                        break
                    out.append(" ")
                    i = i + 1
                continue
        if ch == "/":
            if nxt == "-":
                depth = 1
                out.append("  ")
                i = i + 2
                continue
        if ch == '"':
            in_str = True
            out.append(" ")
            i = i + 1
            continue
        out.append(ch)
        i = i + 1
    require_ok(depth == 0, "LEAN_UNTERM_COMMENT", "unterminated Lean block comment")
    require_ok(not in_str, "LEAN_UNTERM_STRING", "unterminated Lean string literal")
    return "".join(out)


def scan_lean_source_r12(src: str) -> dict[str, Any]:
    cleaned = strip_lean_comments_and_strings(src)
    require_ok(
        _LEAN4_BANNED_RE.search(cleaned) is None,
        "LEAN_ESCAPE_FOUND",
        "forbidden Lean 4 trust-escape keyword detected",
    )
    pub_thms = _PUB_THM_RE.findall(cleaned)
    printed = _PRINT_AXIOMS_RE.findall(cleaned)
    expected_short = [name.split(".", 1)[1] for name in oracle.LEAN_THEOREM_NAMES]
    require_ok(
        len(pub_thms) == len(expected_short),
        "LEAN_THM_COUNT",
        f"expected {len(expected_short)} public theorems, found {len(pub_thms)}",
    )
    require_ok(
        set(pub_thms) == set(expected_short),
        "LEAN_THM_SET_MISMATCH",
        "public theorem set does not match pinned names",
    )
    require_ok(
        set(printed) == set(expected_short),
        "LEAN_AXIOM_PRINT_MISMATCH",
        "#print axioms set does not match public theorems",
    )
    return {
        "static_r12_clean": True,
        "theorems_verified": len(pub_thms),
    }


def validate_lean_axiom_stdout(stdout_text: str) -> dict[str, Any]:
    seen: dict[str, list[str]] = {}
    for match in _AXIOM_ENTRY_RE.finditer(stdout_text):
        thm = match.group(1)
        body = match.group(2)
        if body.startswith("does not depend"):
            seen[thm] = []
        else:
            raw_list = match.group(3)
            axioms = [tok.strip() for tok in raw_list.split(",") if tok.strip() != ""]
            for ax in axioms:
                require_ok(
                    ax in _ALLOWED_LEAN_AXIOMS,
                    "LEAN_FORBIDDEN_AXIOM",
                    f"forbidden Lean axiom {ax} in {thm}",
                )
            seen[thm] = axioms
    expected_set = set(oracle.LEAN_THEOREM_NAMES)
    require_ok(
        set(seen.keys()) == expected_set,
        "LEAN_AXIOM_SET_MISMATCH",
        f"axiom audit matched {len(seen)}/{len(expected_set)} theorems",
    )
    return {"live_axioms_verified": len(seen), "zero_classical_choice": True}


def default_live_lean_runner(track_dir: Path) -> dict[str, Any]:
    home = os.environ.get("HOME", "")
    path_parts = [
        str(Path(home) / ".local" / "bin"),
        str(Path(home) / ".elan" / "bin"),
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
    ]
    env = {
        "PATH": ":".join(path_parts),
        "HOME": home,
        "CUDA_VISIBLE_DEVICES": "",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    lean_files = (
        oracle.PINNED_LEAN_FILES["lean_source"],
        "lean-toolchain",
        "lakefile.toml",
        "lake-manifest.json",
    )
    with tempfile.TemporaryDirectory(prefix="s162_live_lean_") as td:
        stage_dir = Path(td)
        for fname in lean_files:
            raw = read_regular_bytes_capped(track_dir / fname, f"lean_stage_{fname}")
            (stage_dir / fname).write_bytes(raw)
        ver = subprocess.run(
            ["lean", "--version"],
            cwd=str(stage_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        bld = subprocess.run(
            ["lake", "build"],
            cwd=str(stage_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        chk = subprocess.run(
            ["lean", oracle.PINNED_LEAN_FILES["lean_source"]],
            cwd=str(stage_dir),
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    return {
        "version_rc": ver.returncode,
        "version_output": ver.stdout + ver.stderr,
        "build_rc": bld.returncode,
        "build_output": bld.stdout + bld.stderr,
        "axiom_rc": chk.returncode,
        "axiom_stdout": chk.stdout,
    }


def verify_companion_pins_and_lean(
    track_dir: Path,
    *,
    check_pins: bool = True,
    run_live_lean: bool = False,
    lean_runner: Callable[[Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    pin_checks = (
        ("lean_source", oracle.PINNED_LEAN_FILES["lean_source"], oracle.PINNED_LEAN_FILES["lean_source_sha256"]),
        ("lean_toolchain", "lean-toolchain", oracle.PINNED_LEAN_FILES["lean_toolchain_sha256"]),
        ("lakefile", "lakefile.toml", oracle.PINNED_LEAN_FILES["lakefile_sha256"]),
        ("lake_manifest", "lake-manifest.json", oracle.PINNED_LEAN_FILES["lake_manifest_sha256"]),
    )
    lean_src = ""
    for key, fname, expected_sha in pin_checks:
        raw = read_regular_bytes_capped(track_dir / fname, key)
        if check_pins:
            got_sha = oracle.sha256_bytes(raw)
            require_ok(
                got_sha == expected_sha,
                "COMPANION_SHA_MISMATCH",
                f"{fname} sha mismatch: {got_sha}",
            )
        if key == "lean_source":
            lean_src = raw.decode("utf-8", "strict")
        elif key == "lean_toolchain":
            require_ok(
                raw.decode("utf-8", "strict").strip() == oracle.PINNED_LEAN_FILES["lean_toolchain"],
                "BAD_TOOLCHAIN",
                "unexpected lean-toolchain value",
            )
        elif key == "lake_manifest":
            manifest = parse_strict_json_bytes(raw, "lake-manifest.json")
            require_ok(
                manifest.get("packages") == [],
                "NONEMPTY_LAKE_PACKAGES",
                "lake-manifest.json packages must be empty",
            )
    info = scan_lean_source_r12(lean_src)
    runner = lean_runner
    if runner is None:
        if run_live_lean:
            runner = default_live_lean_runner
    if runner is not None:
        res = runner(track_dir)
        require_ok(res["version_rc"] == 0, "LEAN_VERSION_RC", "lean --version failed")
        require_ok("4.36.0" in res["version_output"], "BAD_LEAN_VERSION", "expected Lean 4.36.0")
        require_ok(res["build_rc"] == 0, "LAKE_BUILD_FAIL", "lake build failed")
        require_ok(
            "warning:" not in res["build_output"].lower(),
            "LAKE_BUILD_WARNING",
            "lake build emitted warnings",
        )
        require_ok(res["axiom_rc"] == 0, "LEAN_AXIOM_RC", "lean axiom check failed")
        live_info = validate_lean_axiom_stdout(res["axiom_stdout"])
        info["live_axioms_verified"] = live_info["live_axioms_verified"]
    return info


# ---------------------------------------------------------------------------
# Secondary Mathematical Cross-Audit (SEC/FR0/FR1)
# ---------------------------------------------------------------------------


def _parse_canon_q(raw: Any, label: str) -> Fraction:
    require_ok(type(raw) is str, "Q_TYPE_ERROR", f"{label}: expected str")
    require_ok(_CANON_Q_RE.fullmatch(raw) is not None, "Q_FORMAT_ERROR", f"{label}: {raw}")
    if "/" in raw:
        num_s, den_s = raw.split("/", 1)
        num_i = int(num_s)
        den_i = int(den_s)
        val = Fraction(num_i, den_i)
        require_ok(
            val.numerator == num_i and val.denominator == den_i,
            "Q_NOT_REDUCED",
            f"{label}: unreduced rational {raw}",
        )
        return val
    return Fraction(int(raw), 1)


def _check_sha256_field(val: Any, label: str) -> str:
    require_ok(type(val) is str, "SHA_TYPE_ERROR", f"{label}: expected str")
    require_ok(_SHA256_RE.fullmatch(val) is not None, "SHA_FORMAT_ERROR", f"{label}: bad hex")
    return val


def verify_certificate_object(
    cert: dict[str, Any],
    *,
    anchor_path: Path | None = None,
    track_dir: Path | None = None,
    run_live_lean: bool = False,
    lean_runner: Callable[[Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    require_ok(type(cert) is dict, "CERT_NOT_DICT", "certificate must be dict")
    require_ok(set(cert.keys()) == _ENVELOPE_KEYS, "ENVELOPE_KEYS_MISMATCH", "envelope keys invalid")
    require_ok(cert["schema_version"] == oracle.SCHEMA_VERSION, "SCHEMA_MISMATCH", "bad schema")
    require_ok(cert["track_id"] == oracle.TRACK_ID, "TRACK_MISMATCH", "bad track_id")

    p_sha = _check_sha256_field(cert["payload_sha256"], "payload_sha256")
    c_sha = _check_sha256_field(cert["certificate_sha256"], "certificate_sha256")
    payload = cert["payload"]
    require_ok(type(payload) is dict, "PAYLOAD_NOT_DICT", "payload must be dict")
    require_ok(set(payload.keys()) == _PAYLOAD_KEYS, "PAYLOAD_KEYS_MISMATCH", "payload keys invalid")

    got_p_sha = oracle.sha256_bytes(oracle.canonical_json_bytes(payload))
    require_ok(got_p_sha == p_sha, "PAYLOAD_SHA_MISMATCH", "payload sha256 mismatch")
    body = {
        "schema_version": cert["schema_version"],
        "track_id": cert["track_id"],
        "payload_sha256": p_sha,
        "payload": payload,
    }
    got_c_sha = oracle.sha256_bytes(oracle.canonical_json_bytes(body))
    require_ok(got_c_sha == c_sha, "CERT_SHA_MISMATCH", "certificate sha256 mismatch")

    # Independent secondary mathematical invariants on Q43a & Q43b
    q43a = payload["exp_q43a_bp_frustration_and_cavity"]
    cx = q43a["malecns_cx_6x6"]
    require_ok(cx["signed_laplacian_inertia"] == [6, 0, 0], "CX_NOT_FRUSTRATED", "CX L_sigma != [6,0,0]")
    require_ok(cx["symmetrized_krein_inertia"] == [4, 2, 0], "CX_KREIN_MISMATCH", "CX Krein != [4,2,0]")
    g_lo = _parse_canon_q(cx["damped_bp_cavity_excluded"]["gamma_lo_q"], "cx.gamma_lo")
    g_hi = _parse_canon_q(cx["damped_bp_cavity_excluded"]["gamma_hi_q"], "cx.gamma_hi")
    require_ok(g_lo > Fraction(0) and g_hi < Fraction(1), "CX_GAMMA_BRACKET", "CX gamma* not in (0,1)")
    require_ok(g_lo < g_hi, "CX_GAMMA_ORDER", "CX gamma_lo >= gamma_hi")
    require_ok(
        q43a["kill_gates"]["bethe_bp_stability_bound_pass"] is True,
        "Q43A_KILL_GATE_BP",
        "EXP-Q43a Bethe/BP kill gate failed",
    )
    require_ok(
        q43a["kill_gates"]["separation_gt_5pct_vs_shuf_and_ms_pass"] is True,
        "Q43A_KILL_GATE_SEP",
        "EXP-Q43a 5% separation kill gate failed",
    )

    # Independent Ibn al-Nafis septal firewall algebraic check
    cav = q43a["cavity_exclusion_isomorphism_sop16"]
    w1 = cav["nafis_2x2_conductances"]["w1"]
    w2 = cav["nafis_2x2_conductances"]["w2"]
    for row in cav["nafis_septal_leak_sweep"]:
        ws = row["w_sep"]
        det_exp = ws * (w1 + w2) + w1 * w2
        require_ok(row["det_L_red"] == det_exp, "NAFIS_DET_MISMATCH", "Nafis Schur det mismatch")
        fwd = _parse_canon_q(row["forward_cavity_throughput_q"], "nafis.fwd")
        leak = _parse_canon_q(row["septal_echo_leak_q"], "nafis.leak")
        require_ok(fwd + leak == Fraction(1), "NAFIS_CONSERVATION", "Nafis fwd + leak != 1")

    q43b = payload["exp_q43b_five_operator_wave22_tomography"]
    verdict = q43b["structural_separation_verdict"]
    require_ok(
        verdict["unsigned_wave22_frustrated_count"] == 0,
        "UNSIGNED_W22_FRUST_NONZERO",
        "unsigned Wave-22 topologies must have 0 frustration",
    )
    require_ok(
        verdict["recurrent_folded_stock_frustrated_count"] == 0,
        "FOLDED_STOCK_FRUST_NONZERO",
        "folded stock topologies must have 0 frustration",
    )
    require_ok(
        verdict["dale_prior_restores_frustration"] is True,
        "DALE_PRIOR_FRUST_FAIL",
        "MaleCNS Dale prior failed to restore frustration",
    )
    require_ok(
        verdict["dale_prior_beats_all_controls_on_worst_case_tail"] is True,
        "DALE_PRIOR_TAIL_FAIL",
        "MaleCNS Dale prior failed worst-case tail dominance",
    )

    # Exact canonical oracle replay
    expected = oracle.build_certificate(anchor_path=anchor_path)
    require_ok(cert == expected, "ORACLE_REPLAY_MISMATCH", "certificate differs from exact replay")

    # Companion SHA-256 pins + static R12 Lean scan (+ optional live Lean 4.36.0)
    tdir = oracle.TRACK_DIR if track_dir is None else track_dir
    lean_info = verify_companion_pins_and_lean(
        tdir, run_live_lean=run_live_lean, lean_runner=lean_runner
    )
    return {
        "status": "PASS",
        "track_id": oracle.TRACK_ID,
        "schema_version": oracle.SCHEMA_VERSION,
        "payload_sha256": p_sha,
        "certificate_sha256": c_sha,
        "lean": lean_info,
    }


def verify_external_malecns_pins(malecns_dir: Path) -> list[dict[str, Any]]:
    p_dir = _check_no_symlink_components(_check_path_str(malecns_dir, "malecns_dir"), "malecns_dir")
    require_ok(p_dir.is_dir(), "MALECNS_DIR_MISSING", f"external dataset dir missing: {p_dir.name}")
    verified: list[dict[str, Any]] = []
    for pin in oracle.MALECNS_EXTERNAL_PINS:
        fpath = p_dir / pin["filename"]
        _check_no_symlink_components(fpath, pin["id"])
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(os.fspath(fpath), flags)
        except OSError as exc:
            raise oracle.S162Error("EXTERNAL_OPEN_ERROR", f"{pin['id']}: {exc}") from exc
        h = hashlib.sha256()
        total = 0
        try:
            st = os.fstat(fd)
            require_ok(stat.S_ISREG(st.st_mode), "EXTERNAL_NOT_REG", f"{pin['id']}: not regular")
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                total = total + len(chunk)
                h.update(chunk)
        finally:
            os.close(fd)
        got_sha = h.hexdigest()
        require_ok(total == pin["bytes"], "EXTERNAL_SIZE_MISMATCH", f"{pin['id']}: bytes mismatch")
        require_ok(got_sha == pin["sha256"], "EXTERNAL_SHA_MISMATCH", f"{pin['id']}: sha mismatch")
        verified.append({"id": pin["id"], "bytes": total, "sha256": got_sha})
    return verified


def _emit_error(code: str, message: str) -> None:
    line = json.dumps(
        {"status": "FAIL", "code": code, "message": message},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ) + "\n"
    sys.stderr.write(line)


def _resolve_cert_path(given: str | None) -> Path:
    if given is None:
        return oracle.TRACK_DIR / oracle.DEFAULT_CERT_FILENAME
    cand = Path(given)
    if cand.is_absolute():
        return cand
    return oracle.TRACK_DIR / cand


def run_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track S162 MaleCNS x Wave-22 Neuro Bridge verifier")
    parser.add_argument("--check", nargs="?", const=oracle.DEFAULT_CERT_FILENAME, default=None)
    parser.add_argument("--write", nargs="?", const=oracle.DEFAULT_CERT_FILENAME, default=None)
    parser.add_argument("--standalone", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_out")
    parser.add_argument("--live-lean", action="store_true")
    parser.add_argument("--verify-data", nargs="?", const="__DEFAULT__", default=None)
    args = parser.parse_args(argv)

    modes = 0
    if args.check is not None:
        modes = modes + 1
    if args.write is not None:
        modes = modes + 1
    if args.standalone:
        modes = modes + 1
    require_ok(modes <= 1, "MODE_CONFLICT", "specify at most one of --check, --write, --standalone")

    if args.standalone:
        cert = oracle.build_certificate()
        sys.stdout.write(oracle.canonical_json_bytes(cert).decode("ascii"))
        return 0

    if args.write is not None:
        cert = oracle.build_certificate()
        raw = oracle.canonical_json_bytes(cert)
        out_p = write_regular_bytes_atomic_0600(_resolve_cert_path(args.write), raw, "write_cert")
        res = {
            "status": "WRITTEN",
            "path": out_p.name,
            "bytes": len(raw),
            "certificate_sha256": cert["certificate_sha256"],
        }
        if args.json_out:
            sys.stdout.write(oracle.canonical_json_bytes(res).decode("ascii"))
        else:
            sys.stdout.write(f"WROTE {out_p.name} ({len(raw)} bytes) sha256={cert['certificate_sha256']}\n")
        return 0

    cert_p = _resolve_cert_path(args.check)
    raw_cert = read_regular_bytes_capped(cert_p, "certificate")
    cert_obj = parse_strict_json_bytes(raw_cert, "certificate")
    summary = verify_certificate_object(cert_obj, run_live_lean=args.live_lean)
    if args.verify_data is not None:
        if args.verify_data == "__DEFAULT__":
            data_dir = Path(os.environ.get("HOME", ".")) / "hf-datasets" / "flyem-male-cns-v1"
        else:
            data_dir = Path(args.verify_data)
        summary["external_malecns_pins"] = verify_external_malecns_pins(data_dir)
    if args.json_out:
        sys.stdout.write(oracle.canonical_json_bytes(summary).decode("ascii"))
    else:
        sys.stdout.write(
            f"Track {oracle.TRACK_ID} PASS cert_sha256={summary['certificate_sha256']} "
            f"theorems={summary['lean']['theorems_verified']}\n"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run_cli(argv)
    except oracle.S162Error as exc:
        _emit_error(exc.code, exc.message)
        return 2
    except RecursionError:
        _emit_error("RECURSION_ERROR", "recursion limit exceeded")
        return 2
    except UnicodeDecodeError:
        _emit_error("UNICODE_DECODE_ERROR", "invalid UTF-8 input")
        return 2
    except subprocess.SubprocessError as exc:
        _emit_error("SUBPROCESS_ERROR", type(exc).__name__)
        return 2
    except OSError as exc:
        _emit_error("OS_ERROR", type(exc).__name__)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
