#!/usr/bin/env python3
"""Unified fail-closed standalone verifier for all 4 pillars of socratic-operator-seminar.

Verifies before executing any sub-verifier:
  1. Ancestor & leaf symlink refusal + O_NOFOLLOW | O_NONBLOCK + S_ISREG + 16 MiB byte cap
     on SEMINAR_MANIFEST.json and all 42 pinned seminar package files.
  2. Cryptographic SHA-256 pinning of SEMINAR_MANIFEST.json, all 4 pillar verifiers,
     all 4 committed pillar certificates, and every bound Lean/transcript/dossier artifact.
  3. Isolated subprocess execution forwarding active `-O`/`-OO` and `-W` flags to every
     pillar sub-verifier while emitting bit-identical deterministic JSON across
     `-I -B`, `-I -O -B`, and `-I -B -W error`.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

SEMINAR_DIR = Path(__file__).resolve().parent
SCHEMA_MANIFEST = "bayt-al-hikma.socratic_seminar_manifest.v1"
SCHEMA_UNIFIED = "bayt-al-hikma.socratic_seminar_unified_verification.v1"
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_JSON_DEPTH = 32
MAX_JSON_INT_DIGITS = 1024

PINNED_MANIFEST_SHA256 = "f1862e224bd3c47c2c7727dd7a8e9c77e2a5a18c9eee4055927878b9025c5b45"

PINNED_PILLAR_FILES: Dict[str, str] = {
    "socratic_operator_seminar.py": "e4f39de6d9fbb1a16265e8622e2ccf988f96654973a9c0930ab29437185eb196",
    "verify_pilot1_theorems.py": "d927eff59ce74b8f4b31b994354b3cb40807caec226e5b2a349a7667bc77fc85",
    "verify_ablation_scorecard.py": "688106cdc2476e3f937eb34ff5c0995053692a3aebbd7012d14ab84cc242b237",
    "lean_pilot1_theorems/verify_s150_lean_theorems.py": "633c063f82e72a83bf3703219c427886401cd68b9b68f2c762f19797d91faf4e",
    "certificates/seminar_harness_certificate.json": "552467381026f06c74ebb804c3fdeeee0d97cb12e615734841e454326412fa27",
    "certificates/pilot1_theorems_certificate.json": "bf1a1b7f18fdc57ea58ad1a95eae80a2e10a6035447fd38ebed7ad31a544e8d2",
    "certificates/ablation_scorecard_certificate.json": "436ec03628a6f7ba00286c1297f4a39f36037735ca0fca0f81f16164a5f8f288",
    "lean_pilot1_theorems/s150_lean_theorems_certificate.json": "72f6d6733a454879dbb83507a0b7571992d8e227721b77dc9acd9fe11ee92fcf",
}


class SeminarAllError(ValueError):
    """Fail-closed unified seminar verification error."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


def require_ok(cond: bool, code: str, message: str) -> None:
    if cond is not True:
        raise SeminarAllError(code, message)


def refuse_symlink_path(path: Path) -> None:
    abs_path = path if path.is_absolute() else Path.cwd().joinpath(path)
    cur = Path(abs_path.anchor)
    for idx, part in enumerate(abs_path.parts[1:]):
        cur = cur.joinpath(part)
        if idx >= 1 or idx == len(abs_path.parts) - 2:
            require_ok(not cur.is_symlink(), "SYMLINK_FORBIDDEN", f"Symlink path or ancestor forbidden: {path.name}")


def read_regular_file_bytes(
    path: Path,
    missing_code: str = "MISSING_FILE",
    max_bytes: int = MAX_FILE_BYTES,
) -> bytes:
    """Refuse symlinks/ancestors, open with O_NOFOLLOW|O_NONBLOCK, verify S_ISREG & byte cap."""
    refuse_symlink_path(path)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise SeminarAllError("SYMLINK_FORBIDDEN", f"Symlink forbidden: {path.name}") from exc
        if exc.errno in (errno.ENOENT, errno.ENOTDIR):
            raise SeminarAllError(missing_code, f"File not found: {path.name}") from exc
        raise SeminarAllError("READ_ERROR", f"Failed to open {path.name}: {exc.strerror}") from exc
    try:
        try:
            st = os.fstat(fd)
            require_ok(stat.S_ISREG(st.st_mode), "NOT_REGULAR_FILE", f"Non-regular file forbidden: {path.name}")
            require_ok(st.st_size <= max_bytes, "FILE_TOO_LARGE", f"File exceeds byte cap: {path.name}")
            chunks: List[bytes] = []
            total = 0
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                total += len(chunk)
                require_ok(total <= max_bytes, "FILE_TOO_LARGE", f"Read exceeded byte cap: {path.name}")
                chunks.append(chunk)
            return b"".join(chunks)
        except OSError as exc:
            raise SeminarAllError("READ_ERROR", f"Failed to read {path.name}: {exc.strerror}") from exc
    finally:
        os.close(fd)


def _reject_dup_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in pairs:
        require_ok(k not in out, "DUPLICATE_JSON_KEY", f"Duplicate JSON key: {k}")
        out[k] = v
    return out


def _reject_float(token: str) -> Any:
    raise SeminarAllError("FLOAT_FORBIDDEN", f"Float forbidden in strict JSON: {token}")


def _reject_constant(token: str) -> Any:
    raise SeminarAllError("NONFINITE_JSON", f"Non-finite constant forbidden: {token}")


def _parse_bounded_int(token: str) -> int:
    require_ok(
        len(token.lstrip("+-")) <= MAX_JSON_INT_DIGITS,
        "JSON_INT_TOO_LARGE",
        "JSON integer exceeds digit cap",
    )
    return int(token)


def _check_json_depth_pre_parse(text: str, max_depth: int = MAX_JSON_DEPTH) -> None:
    depth = 0
    in_str = False
    escaped = False
    for ch in text:
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
            require_ok(depth <= max_depth, "JSON_DEPTH", "JSON nesting depth exceeded")
        elif ch in "}]":
            if depth > 0:
                depth -= 1


def loads_strict_json_bytes(raw: bytes, label: str) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SeminarAllError("BAD_JSON", f"{label} invalid UTF-8: {exc}") from exc
    _check_json_depth_pre_parse(text)
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_dup_keys,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
            parse_int=_parse_bounded_int,
        )
    except SeminarAllError:
        raise
    except RecursionError as exc:
        raise SeminarAllError("JSON_DEPTH", f"{label} JSON nesting depth exceeded: {exc}") from exc
    except ValueError as exc:
        raise SeminarAllError("BAD_JSON", f"{label} invalid JSON: {exc}") from exc


def verify_pinned_manifest_and_pillars(
    seminar_dir: Path,
    expected_manifest_sha256: str = PINNED_MANIFEST_SHA256,
    expected_pillar_files: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Verify SEMINAR_MANIFEST.json and all pinned pillar verifier & certificate files."""
    refuse_symlink_path(seminar_dir)
    manifest_path = seminar_dir.joinpath("SEMINAR_MANIFEST.json")
    manifest_bytes = read_regular_file_bytes(manifest_path, missing_code="MISSING_MANIFEST")
    manifest_file_sha = hashlib.sha256(manifest_bytes).hexdigest()
    require_ok(
        hmac.compare_digest(manifest_file_sha, expected_manifest_sha256),
        "MANIFEST_SHA256_MISMATCH",
        "SEMINAR_MANIFEST.json raw SHA-256 mismatch",
    )
    manifest = loads_strict_json_bytes(manifest_bytes, "SEMINAR_MANIFEST.json")
    require_ok(isinstance(manifest, dict), "BAD_MANIFEST", "Manifest must be a JSON object")
    require_ok(manifest.get("schema") == SCHEMA_MANIFEST, "BAD_MANIFEST_SCHEMA", "Unexpected manifest schema")

    claimed_self = manifest.get("manifest_sha256")
    body = {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    recomp_self = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")
    ).hexdigest()
    require_ok(
        type(claimed_self) is str and hmac.compare_digest(claimed_self, recomp_self),
        "MANIFEST_SELF_HASH_MISMATCH",
        "SEMINAR_MANIFEST.json self-hash mismatch",
    )

    files_map = manifest.get("files")
    require_ok(
        isinstance(files_map, dict) and manifest.get("file_count") == len(files_map) and len(files_map) > 0,
        "BAD_MANIFEST_FILES",
        "Manifest file_count or files map invalid",
    )
    for rel, meta in sorted(files_map.items()):
        require_ok(
            type(rel) is str and isinstance(meta, dict) and type(meta.get("sha256")) is str and type(meta.get("bytes")) is int,
            "BAD_MANIFEST_ENTRY",
            f"Malformed manifest entry for {rel}",
        )
        fpath = seminar_dir.joinpath(rel)
        raw = read_regular_file_bytes(fpath, missing_code="MISSING_MANIFEST_FILE")
        actual_sha = hashlib.sha256(raw).hexdigest()
        require_ok(len(raw) == meta["bytes"], "MANIFEST_SIZE_MISMATCH", f"Size drift on {rel}")
        require_ok(
            hmac.compare_digest(actual_sha, meta["sha256"]),
            "MANIFEST_FILE_SHA256_MISMATCH",
            f"SHA-256 drift on {rel}",
        )

    pillars = expected_pillar_files if expected_pillar_files is not None else PINNED_PILLAR_FILES
    for rel, exp_sha in sorted(pillars.items()):
        require_ok(rel in files_map, "PILLAR_NOT_IN_MANIFEST", f"Pillar file {rel} missing from manifest")
        fpath = seminar_dir.joinpath(rel)
        raw = read_regular_file_bytes(fpath, missing_code="MISSING_PILLAR_FILE")
        actual_sha = hashlib.sha256(raw).hexdigest()
        require_ok(
            hmac.compare_digest(actual_sha, exp_sha),
            "PILLAR_SHA256_MISMATCH",
            f"Pinned pillar SHA-256 mismatch on {rel}",
        )

    return {
        "manifest_file_sha256": manifest_file_sha,
        "manifest_files_verified": len(files_map),
        "pillar_files_verified": len(pillars),
    }


def _child_python_flags() -> List[str]:
    flags = ["-I", "-B"]
    if sys.flags.optimize >= 2:
        flags.append("-OO")
    elif sys.flags.optimize == 1:
        flags.append("-O")
    for opt in sys.warnoptions:
        flags.extend(["-W", opt])
    return flags


def _run_cmd(args: Sequence[str], cwd: Path) -> Dict[str, Any]:
    cmd = [sys.executable, *_child_python_flags(), *args]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "args": list(args),
        "rc": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def run_all_pillars(
    seminar_dir: Path = SEMINAR_DIR,
    live_lean: bool = False,
    runner: Any = _run_cmd,
) -> Dict[str, Any]:
    pin_info = verify_pinned_manifest_and_pillars(seminar_dir)
    checks: List[Dict[str, Any]] = [
        {
            "pillar": "seminar_harness",
            **runner(
                ["socratic_operator_seminar.py", "--check-cert", "certificates/seminar_harness_certificate.json"],
                seminar_dir,
            ),
        },
        {
            "pillar": "pilot1_theorems",
            **runner(
                ["verify_pilot1_theorems.py", "--check", "certificates/pilot1_theorems_certificate.json"],
                seminar_dir,
            ),
        },
        {
            "pillar": "ablation_scorecard",
            **runner(
                ["verify_ablation_scorecard.py", "--check", "certificates/ablation_scorecard_certificate.json"],
                seminar_dir,
            ),
        },
        {
            "pillar": "lean_pilot1_theorems",
            **runner(
                ["verify_s150_lean_theorems.py", "--check"] + (["--live-lean"] if live_lean else []),
                seminar_dir.joinpath("lean_pilot1_theorems"),
            ),
        },
    ]
    all_ok = all(item["rc"] == 0 for item in checks)
    summary: Dict[str, Any] = {
        "schema": SCHEMA_UNIFIED,
        "live_lean": live_lean,
        "manifest_file_sha256": pin_info["manifest_file_sha256"],
        "manifest_files_verified": pin_info["manifest_files_verified"],
        "pillar_files_verified": pin_info["pillar_files_verified"],
        "all_passed": all_ok,
        "pillars_passed": sum(1 for item in checks if item["rc"] == 0),
        "pillars_total": len(checks),
        "checks": checks,
    }
    canonical = json.dumps(summary, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
    summary["summary_sha256"] = hashlib.sha256(canonical).hexdigest()
    return summary


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Verify all 4 pillars of socratic-operator-seminar")
    parser.add_argument("--live-lean", action="store_true", help="Also run cold Lean 4.36.0 + leanchecker --fresh")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON summary")
    args = parser.parse_args(argv)

    try:
        refuse_symlink_path(Path(__file__))
        summary = run_all_pillars(SEMINAR_DIR, live_lean=args.live_lean)
    except SeminarAllError as exc:
        sys.stderr.write(json.dumps({"error_code": exc.code, "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2
    except OSError as exc:
        sys.stderr.write(json.dumps({"error_code": "IO_ERROR", "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=True))
    else:
        for item in summary["checks"]:
            tag = "PASS" if item["rc"] == 0 else "FAIL"
            print(f"[{tag}] {item['pillar']} (rc={item['rc']})")
        print(f"ALL_PASSED={summary['all_passed']} summary_sha256={summary['summary_sha256']}")
    return 0 if summary["all_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
