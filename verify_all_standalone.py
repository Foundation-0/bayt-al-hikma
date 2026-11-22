#!/usr/bin/env python3
"""
Portable Zero-Dependency Standalone Verifier for Foundation-0/bayt-al-hikma.

Runs all committed standalone pure-Q certifiers and R5 mutation-hardened test suites
across all 4 verified studies:
  - `arabic-continuum/`   (AUDIT-091R, 5 files, 68/68 R5)
  - `arabic-lexicon/`     (AUDIT-094R, 5 files, 81/81 R5)
  - `polymath-lineage/`   (AUDIT-092R, 4 files, 75/75 R5)
  - `veins-and-branches/` (AUDIT-095,  4 files, 110/110 R5)

Executes every certifier under isolated `-I -B -W error` and every R5 test suite
under `-I -O -B -W error`, enforces strict zero-float JSON parsing (zero duplicate
keys, zero NaN/Infinity, zero IEEE-754 floats) on both committed JSON certificates
and standalone certifier outputs, and verifies exact SHA-256 parity on all 18/18
committed package files and 4/4 standalone outputs.

Pure Python 3 stdlib only. Zero bare `assert`s. Zero hardcoded absolute paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent

STUDY_SPECS: tuple[dict[str, Any], ...] = (
    {
        "audit_id": "AUDIT-091R",
        "study_dir": "arabic-continuum",
        "cert_script": "arabic_continuum_audit.py",
        "cert_args": ["--standalone"],
        "test_script": "test_arabic_continuum_r5.py",
        "expected_standalone_stdout_sha256": (
            "d723eab3b20097953f8cb31af95be7672cc84471c7691c56b8e731cae90d6c3f"
        ),
        "expected_file_sha256": {
            "ARABIC_CONTINUUM_AUDIT_REPORT.md": (
                "9679fcc687034d9fd8a33ac29f5c4bd5b8b8eea35b8e90a35c938f16decd3d39"
            ),
            "arabic_continuum_audit.py": (
                "4b27359c1ce3dfd8d6925170d011edf32cbccb441bac5ffb4886d93ae79cbd1d"
            ),
            "arabic_continuum_certificate.json": (
                "aa8608057664961c25c18dd52af0b98c25a2d990268e64d5e30547beb8ab16ec"
            ),
            "arabic_continuum_oracle.py": (
                "6ec92ef354e0c833183119a075d0543aefcb1147bd5ecde9df6b64f4e7979b71"
            ),
            "test_arabic_continuum_r5.py": (
                "e2f0705c74ea4bdcb4717fc0c1dc871dedcddd3cf20f1ff1ee6f785280bf537f"
            ),
        },
    },
    {
        "audit_id": "AUDIT-094R",
        "study_dir": "arabic-lexicon",
        "cert_script": "arabic_lexicon_audit.py",
        "cert_args": ["--standalone"],
        "test_script": "test_arabic_lexicon_r5.py",
        "expected_standalone_stdout_sha256": (
            "c81d5a6d4e5173b4b82c74dffe08f5612a68cd6b97f43acd763b5ef4815b2ebd"
        ),
        "expected_file_sha256": {
            "ARABIC_LEXICON_TOPOLOGY_REPORT.md": (
                "0f04afffd3942f4c5715c2ed6765f379f3bc9f49ff46b818084b75bae23d901d"
            ),
            "arabic_lexicon_audit.py": (
                "e34a5f80ff9e8cb2e47851159b1fa19da1f223e07e52ebcfe135f0c3e4f9f4d6"
            ),
            "arabic_lexicon_certificate.json": (
                "6dcfbc8bcef2d11992aed2883995cf705b3c4bad6b9ad518cd28c1447f10d60c"
            ),
            "arabic_lexicon_oracle.py": (
                "797dc7ece64a96a1fac9bb87a4f2a0ad9471838c9afc03b704ae512a17f4b56c"
            ),
            "test_arabic_lexicon_r5.py": (
                "5d1ccc8431d648ef0f59b65c69429f509e797583bde57812e2692f620b1bde8e"
            ),
        },
    },
    {
        "audit_id": "AUDIT-092R",
        "study_dir": "polymath-lineage",
        "cert_script": "bayt_al_hikma_polymath_certifier.py",
        "cert_args": ["--json"],
        "test_script": "test_bayt_al_hikma_polymaths_r5.py",
        "expected_standalone_stdout_sha256": (
            "898ee17e3f1ebee4fc91e71eef7c136e7ecc8029c85f84a6271ac608c3619bc2"
        ),
        "expected_file_sha256": {
            "BAYT_AL_HIKMA_POLYMATH_REPORT.md": (
                "ff42a9d18bd60c0d4706f725e234c2a6334a13b8ee568e19a11753d1f13b3bb3"
            ),
            "bayt_al_hikma_polymath_certificate.json": (
                "c052a62a77182fe0ec11accf9e8836e7df935a2aa62fd5f338442f2680a8d4d3"
            ),
            "bayt_al_hikma_polymath_certifier.py": (
                "40bd40dbf286d48c87c212f93d04cd5cf60796adc36098241f312dd1c68736d2"
            ),
            "test_bayt_al_hikma_polymaths_r5.py": (
                "f4c29cb9b9931abe7ccb887c939803ec8f04c5002b0e2ed2921bf89a5fd95ace"
            ),
        },
    },
    {
        "audit_id": "AUDIT-095",
        "study_dir": "veins-and-branches",
        "cert_script": "bayt_al_hikma_veins_certifier.py",
        "cert_args": ["--json"],
        "test_script": "test_bayt_al_hikma_veins_r5.py",
        "expected_standalone_stdout_sha256": (
            "df16a48ee68027eaa525bbe90ff1eb1f4aa3e540b60d155c503069101d573756"
        ),
        "expected_file_sha256": {
            "BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md": (
                "49e10bbab2cf7f45327f39ede25aaa6cc2bf5b6c0d04a7c39c897a4cfbb70393"
            ),
            "bayt_al_hikma_veins_certificate.json": (
                "12059e44b248c4579117c446a17679ce7043cb1f45f0c664aa80796aad725c77"
            ),
            "bayt_al_hikma_veins_certifier.py": (
                "efa0e702d29b5e5becd05fc9db59249f66f64b3d024a9ae1af14ddd904e81b25"
            ),
            "test_bayt_al_hikma_veins_r5.py": (
                "dc58bfb4e8898fab8308e251ecc4070d7631114c6b174a03e772efa725d43e23"
            ),
        },
    },
)


def _strict_no_dups_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"DUPLICATE_JSON_KEY: {k}")
        out[k] = v
    return out


def _forbid_constant(val: str) -> Any:
    raise ValueError(f"NONFINITE_JSON_CONSTANT: {val}")


def _forbid_float(val: str) -> Any:
    raise ValueError(f"FLOAT_FORBIDDEN_IN_JSON: {val}")


def parse_strict_zero_float_json(raw_bytes: bytes) -> dict[str, Any]:
    text = raw_bytes.decode("utf-8")
    parsed = json.loads(
        text,
        object_pairs_hook=_strict_no_dups_hook,
        parse_constant=_forbid_constant,
        parse_float=_forbid_float,
    )
    if not isinstance(parsed, dict):
        raise ValueError("TOP_LEVEL_JSON_MUST_BE_OBJECT")
    return parsed


def verify_study(spec: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    study_path = repo_root / spec["study_dir"]
    errors: list[str] = []

    if not study_path.is_dir():
        return {
            "audit_id": spec["audit_id"],
            "study_dir": spec["study_dir"],
            "passed": False,
            "files_verified": 0,
            "errors": [f"MISSING_STUDY_DIR: {spec['study_dir']}"],
        }

    # 1. Verify byte-identical SHA-256 on every pinned package file (and strict JSON on .json files)
    files_verified = 0
    for fname, expected_sha in sorted(spec["expected_file_sha256"].items()):
        fpath = study_path / fname
        if not fpath.is_file():
            errors.append(f"MISSING_FILE: {spec['study_dir']}/{fname}")
            continue
        raw = fpath.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != expected_sha:
            errors.append(
                f"FILE_SHA256_MISMATCH: {spec['study_dir']}/{fname} got={actual_sha} expected={expected_sha}"
            )
            continue
        if fname.endswith(".json"):
            try:
                parse_strict_zero_float_json(raw)
            except ValueError as exc:
                errors.append(f"COMMITTED_JSON_ERROR: {spec['study_dir']}/{fname}: {exc}")
                continue
        files_verified += 1

    if errors:
        return {
            "audit_id": spec["audit_id"],
            "study_dir": spec["study_dir"],
            "passed": False,
            "files_verified": files_verified,
            "errors": errors,
        }

    # 2. Run standalone certifier under isolated -I -B -W error
    cert_cmd = [sys.executable, "-I", "-B", "-W", "error", spec["cert_script"], *spec["cert_args"]]
    cert_proc = subprocess.run(cert_cmd, cwd=str(study_path), capture_output=True)
    cert_sha = hashlib.sha256(cert_proc.stdout).hexdigest()
    if cert_proc.returncode != 0:
        errors.append(f"CERTIFIER_NONZERO_EXIT: rc={cert_proc.returncode}")
    if cert_sha != spec["expected_standalone_stdout_sha256"]:
        errors.append(
            f"STANDALONE_SHA256_MISMATCH: got={cert_sha} expected={spec['expected_standalone_stdout_sha256']}"
        )
    try:
        parse_strict_zero_float_json(cert_proc.stdout)
    except ValueError as exc:
        errors.append(f"STRICT_JSON_ERROR: {exc}")

    # 3. Run assertion-free R5 test suite under -I -O -B -W error
    test_cmd = [sys.executable, "-I", "-O", "-B", "-W", "error", spec["test_script"]]
    test_proc = subprocess.run(test_cmd, cwd=str(study_path), capture_output=True)
    if test_proc.returncode != 0:
        errors.append(f"R5_TEST_NONZERO_EXIT: rc={test_proc.returncode}")

    return {
        "audit_id": spec["audit_id"],
        "study_dir": spec["study_dir"],
        "passed": len(errors) == 0,
        "files_verified": files_verified,
        "standalone_stdout_sha256": cert_sha,
        "cert_rc": cert_proc.returncode,
        "test_rc": test_proc.returncode,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify all committed Foundation-0/bayt-al-hikma standalone studies & R5 test suites."
    )
    parser.add_argument("--json", action="store_true", help="Emit canonical JSON report.")
    args = parser.parse_args(argv)

    results = [verify_study(spec, REPO_ROOT) for spec in STUDY_SPECS]
    all_passed = all(r["passed"] for r in results)
    summary = {
        "schema": "bayt_al_hikma.standalone_check.v1",
        "studies_checked": len(results),
        "studies_passed": sum(1 for r in results if r["passed"]),
        "total_files_verified": sum(int(r.get("files_verified", 0)) for r in results),
        "passed": all_passed,
        "status": "PASS" if all_passed else "FAIL",
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            f"BAYT_AL_HIKMA_STANDALONE_CHECK: {summary['status']} "
            f"({summary['studies_passed']}/{summary['studies_checked']} studies, "
            f"{summary['total_files_verified']} files)"
        )
        for r in results:
            tag = "PASS" if r["passed"] else "FAIL"
            sha16 = r.get("standalone_stdout_sha256", "")[:16]
            print(
                f"  [{tag}] {r['audit_id']} ({r['study_dir']}): "
                f"files={r.get('files_verified', 0)} sha256={sha16} "
                f"cert_rc={r.get('cert_rc')} test_rc={r.get('test_rc')}"
            )
            for err in r["errors"]:
                print(f"         ERROR: {err}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
