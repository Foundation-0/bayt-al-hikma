#!/usr/bin/env python3
"""
Portable Zero-Dependency Verifier for Foundation-0/bayt-al-hikma.

Supports two explicitly distinguished modes:

1. Offline mode (default):
   - Verifies exact SHA-256 parity on all 20/20 pinned repository files
     (fetch_corpora.py, PREREGISTERED_HYPOTHESES.md, and all 18 study files).
   - Verifies fetch_corpora.py --manifest-json parses strictly zero-float
     (9 pinned primary corpora) and matches its pinned digest.
   - Recomputes every mathematical claim in polymath-lineage/ and
     veins-and-branches/ from scratch under isolated `-I -B -W error` and
     confirms byte-identical parity with their committed JSON certificates.
   - Runs arabic-continuum/ and arabic-lexicon/ in `--standalone` mode
     (pinned-fixture invariant replay; reads NO corpus file;
     `arabic_live_corpora_recounted: false`).
   - Runs all 4 assertion-free R5 + known-answer test suites under
     `-I -O -B -W error`.

2. Live corpus recount mode (`--live` or `--corpus-dir <path>`):
   - Performs every check in offline mode, PLUS:
   - Runs `fetch_corpora.py --verify-only --dest <corpus_dir>` to verify all
     9 primary corpora on disk against their pinned sizes and SHA-256s.
   - Runs both `arabic-continuum/arabic_continuum_audit.py` and
     `arabic-lexicon/arabic_lexicon_audit.py` in live recount mode against
     `<corpus_dir>`, recomputing every count and every B=250 multi-shuffle
     null from the raw primary texts, and confirms byte-identical parity with
     their committed JSON certificates (`arabic_live_corpora_recounted: true`).

Pure Python 3 stdlib only. Zero IEEE-754 floats. Zero bare `assert`s.
Zero hardcoded absolute paths.
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

ROOT_FILES_EXPECTED_SHA256: dict[str, str] = {
    "PREREGISTERED_HYPOTHESES.md": (
        "a28633cb95e66f6b8eb5e1d7cb9224f0ac95ad7aa191edbe8e5532cb08b2468d"
    ),
    "fetch_corpora.py": (
        "606353db2207ea75ad20d7b5f5b1f608242f617cae81ce8d434c5172d59677e0"
    ),
}

EXPECTED_FETCH_MANIFEST_SHA256 = (
    "0bb08a304fb4d200e1fd1cf81686e9a771917185e8c132d8ce25931df6329263"
)
EXPECTED_FETCH_MANIFEST_COUNT = 9

STUDY_SPECS: tuple[dict[str, Any], ...] = (
    {
        "audit_id": "AUDIT-091-V2",
        "study_dir": "arabic-continuum",
        "cert_script": "arabic_continuum_audit.py",
        "cert_args": ["--standalone"],
        "test_script": "test_arabic_continuum_r5.py",
        "committed_certificate_file": "arabic_continuum_certificate.json",
        "recomputes_from_scratch_offline": False,
        "supports_live_corpus_recount": True,
        "expected_standalone_stdout_sha256": (
            "817738b48b391a5e88b2dc927123e8fcd156376454ae1a197493900aa3040e41"
        ),
        "expected_live_stdout_sha256": (
            "7081c463ad8ce4cce12f61f29f31f0f4741bbbfb4d43d85824622bcc62ac9069"
        ),
        "expected_file_sha256": {
            "ARABIC_CONTINUUM_AUDIT_REPORT.md": (
                "e809204ecde8a0f6fd93b36f18e615552a6f348961ec62d2c7a55038306268a6"
            ),
            "arabic_continuum_audit.py": (
                "3f3aa47dad6397d6a4a5bef954d23a5bfa8eb5431a6d5b6d17f17a49eb4932ee"
            ),
            "arabic_continuum_certificate.json": (
                "7081c463ad8ce4cce12f61f29f31f0f4741bbbfb4d43d85824622bcc62ac9069"
            ),
            "arabic_continuum_oracle.py": (
                "24e3b164365b7d00fe22e067bcfbc4c298292d714c90491b1e944c344d26dea3"
            ),
            "test_arabic_continuum_r5.py": (
                "9f88ea2126424d8c130632b93818e66bda023f84e2d65ee0aadf482ebfd59a8b"
            ),
        },
    },
    {
        "audit_id": "AUDIT-094-V2",
        "study_dir": "arabic-lexicon",
        "cert_script": "arabic_lexicon_audit.py",
        "cert_args": ["--standalone"],
        "test_script": "test_arabic_lexicon_r5.py",
        "committed_certificate_file": "arabic_lexicon_certificate.json",
        "recomputes_from_scratch_offline": False,
        "supports_live_corpus_recount": True,
        "expected_standalone_stdout_sha256": (
            "4c562cf15bdcd09bb1965375569b888de9f68a17030e65e7f1314e67d0457513"
        ),
        "expected_live_stdout_sha256": (
            "96d855fac3d017f716adf67f4d8af1a6eb8b620372b93ae5a945ee6a1da62586"
        ),
        "expected_file_sha256": {
            "ARABIC_LEXICON_TOPOLOGY_REPORT.md": (
                "5b3527d80a5b5bc18500973a74bd02693ca7d72dd92deeb506a4ddb349fd7d52"
            ),
            "arabic_lexicon_audit.py": (
                "4f74dc39d23b00eeea6cd6ac265b9392ede2ecb5e93af4857302454be28c1d35"
            ),
            "arabic_lexicon_certificate.json": (
                "96d855fac3d017f716adf67f4d8af1a6eb8b620372b93ae5a945ee6a1da62586"
            ),
            "arabic_lexicon_oracle.py": (
                "9d6da97ba142f00b624e23635c6618df9238229425a86b20e427fc0c7e7a11c8"
            ),
            "test_arabic_lexicon_r5.py": (
                "1cf767cc51520784e73f2487b15c68bd1ec2b1a1871065e116ac144c8d168d05"
            ),
        },
    },
    {
        "audit_id": "AUDIT-092R2",
        "study_dir": "polymath-lineage",
        "cert_script": "bayt_al_hikma_polymath_certifier.py",
        "cert_args": ["--json"],
        "test_script": "test_bayt_al_hikma_polymaths_r5.py",
        "committed_certificate_file": "bayt_al_hikma_polymath_certificate.json",
        "recomputes_from_scratch_offline": True,
        "supports_live_corpus_recount": False,
        "expected_standalone_stdout_sha256": (
            "76fac8902c7f34a92f309f463a8f584bbc1d26e336791819f0adc722778a2688"
        ),
        "expected_live_stdout_sha256": None,
        "expected_file_sha256": {
            "BAYT_AL_HIKMA_POLYMATH_REPORT.md": (
                "309164abf64ea1a4bb4555f258197e72c439a06778c7d0cac42075bf1805e1b4"
            ),
            "bayt_al_hikma_polymath_certificate.json": (
                "76fac8902c7f34a92f309f463a8f584bbc1d26e336791819f0adc722778a2688"
            ),
            "bayt_al_hikma_polymath_certifier.py": (
                "a20b47d3adc021ca072afd0f398f94f63f3c215c28b5ff5b823390d692216b9a"
            ),
            "test_bayt_al_hikma_polymaths_r5.py": (
                "11080d5ade48bbf2ece189b314d0e0e647947bc776ba6c821bd301111156adde"
            ),
        },
    },
    {
        "audit_id": "AUDIT-095R",
        "study_dir": "veins-and-branches",
        "cert_script": "bayt_al_hikma_veins_certifier.py",
        "cert_args": ["--json"],
        "test_script": "test_bayt_al_hikma_veins_r5.py",
        "committed_certificate_file": "bayt_al_hikma_veins_certificate.json",
        "recomputes_from_scratch_offline": True,
        "supports_live_corpus_recount": False,
        "expected_standalone_stdout_sha256": (
            "236c165d9130cfca5565f57a553cdf5eb69b786a6850efda7d2239b6f99e5714"
        ),
        "expected_live_stdout_sha256": None,
        "expected_file_sha256": {
            "BAYT_AL_HIKMA_VEINS_AND_BRANCHES_REPORT.md": (
                "c016bb3f0d8a13128904147390f4dc9952bd8ec89b00b24c4f5d4f896290bef9"
            ),
            "bayt_al_hikma_veins_certificate.json": (
                "236c165d9130cfca5565f57a553cdf5eb69b786a6850efda7d2239b6f99e5714"
            ),
            "bayt_al_hikma_veins_certifier.py": (
                "ad431b4b4106204574ee039b532a97dd49f147a7695e86c3da7c9e0f4af1489e"
            ),
            "test_bayt_al_hikma_veins_r5.py": (
                "9405cadf70dc3dc26f99a6279aaca1f5713a603fa7af7797e9f7c7c809afb4f9"
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


def verify_root_files_and_fetch_manifest(
    repo_root: Path,
    live: bool,
    corpus_dir: Path | None,
) -> dict[str, Any]:
    errors: list[str] = []
    files_verified = 0

    for fname, expected_sha in sorted(ROOT_FILES_EXPECTED_SHA256.items()):
        fpath = repo_root / fname
        if not fpath.is_file():
            errors.append(f"MISSING_ROOT_FILE: {fname}")
            continue
        actual_sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            errors.append(
                f"ROOT_FILE_SHA256_MISMATCH: {fname} got={actual_sha} expected={expected_sha}"
            )
            continue
        files_verified += 1

    manifest_sha = ""
    manifest_count = 0
    fetch_script = repo_root / "fetch_corpora.py"
    if fetch_script.is_file():
        m_proc = subprocess.run(
            [sys.executable, "-I", "-B", "-W", "error", "fetch_corpora.py", "--manifest-json"],
            cwd=str(repo_root),
            capture_output=True,
        )
        manifest_sha = hashlib.sha256(m_proc.stdout).hexdigest()
        if m_proc.returncode != 0:
            errors.append(f"FETCH_MANIFEST_NONZERO_EXIT: rc={m_proc.returncode}")
        if manifest_sha != EXPECTED_FETCH_MANIFEST_SHA256:
            errors.append(
                f"FETCH_MANIFEST_SHA256_MISMATCH: got={manifest_sha} "
                f"expected={EXPECTED_FETCH_MANIFEST_SHA256}"
            )
        try:
            manifest_obj = parse_strict_zero_float_json(m_proc.stdout)
            manifest_count = int(manifest_obj.get("count", 0))
            if manifest_count != EXPECTED_FETCH_MANIFEST_COUNT:
                errors.append(
                    f"FETCH_MANIFEST_COUNT_MISMATCH: got={manifest_count} "
                    f"expected={EXPECTED_FETCH_MANIFEST_COUNT}"
                )
        except ValueError as exc:
            errors.append(f"FETCH_MANIFEST_JSON_ERROR: {exc}")

    live_corpora_verified = 0
    if live:
        if corpus_dir is None or not corpus_dir.is_dir():
            errors.append("LIVE_CORPUS_DIR_MISSING")
        elif fetch_script.is_file():
            v_proc = subprocess.run(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    "-W",
                    "error",
                    "fetch_corpora.py",
                    "--verify-only",
                    "--dest",
                    str(corpus_dir),
                ],
                cwd=str(repo_root),
                capture_output=True,
            )
            if v_proc.returncode != 0:
                errors.append(f"LIVE_CORPUS_VERIFY_FAILED: rc={v_proc.returncode}")
            else:
                try:
                    v_obj = parse_strict_zero_float_json(v_proc.stdout)
                    live_corpora_verified = int(v_obj.get("count", 0))
                    if live_corpora_verified != EXPECTED_FETCH_MANIFEST_COUNT:
                        errors.append(
                            f"LIVE_CORPUS_COUNT_MISMATCH: got={live_corpora_verified} "
                            f"expected={EXPECTED_FETCH_MANIFEST_COUNT}"
                        )
                except ValueError as exc:
                    errors.append(f"LIVE_CORPUS_VERIFY_JSON_ERROR: {exc}")

    return {
        "passed": len(errors) == 0,
        "root_files_verified": files_verified,
        "fetch_manifest_sha256": manifest_sha,
        "fetch_manifest_count": manifest_count,
        "live_corpora_verified": live_corpora_verified,
        "errors": errors,
    }


def verify_study(
    spec: dict[str, Any],
    repo_root: Path,
    live: bool,
    corpus_dir: Path | None,
) -> dict[str, Any]:
    study_path = repo_root / spec["study_dir"]
    errors: list[str] = []

    if not study_path.is_dir():
        return {
            "audit_id": spec["audit_id"],
            "study_dir": spec["study_dir"],
            "passed": False,
            "files_verified": 0,
            "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
            "live_corpus_recounted": False,
            "errors": [f"MISSING_STUDY_DIR: {spec['study_dir']}"],
        }

    # 1. Verify byte-identical SHA-256 on every pinned package file (and strict JSON on .json files)
    files_verified = 0
    committed_cert_bytes = b""
    committed_cert_name = spec["committed_certificate_file"]
    for fname, expected_sha in sorted(spec["expected_file_sha256"].items()):
        fpath = study_path / fname
        if not fpath.is_file():
            errors.append(f"MISSING_FILE: {spec['study_dir']}/{fname}")
            continue
        raw = fpath.read_bytes()
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != expected_sha:
            errors.append(
                f"FILE_SHA256_MISMATCH: {spec['study_dir']}/{fname} "
                f"got={actual_sha} expected={expected_sha}"
            )
            continue
        if fname.endswith(".json"):
            try:
                parse_strict_zero_float_json(raw)
            except ValueError as exc:
                errors.append(f"COMMITTED_JSON_ERROR: {spec['study_dir']}/{fname}: {exc}")
                continue
        if fname == committed_cert_name:
            committed_cert_bytes = raw
        files_verified += 1

    if errors:
        return {
            "audit_id": spec["audit_id"],
            "study_dir": spec["study_dir"],
            "passed": False,
            "files_verified": files_verified,
            "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
            "live_corpus_recounted": False,
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
            f"STANDALONE_SHA256_MISMATCH: got={cert_sha} "
            f"expected={spec['expected_standalone_stdout_sha256']}"
        )
    standalone_parsed: dict[str, Any] | None = None
    try:
        standalone_parsed = parse_strict_zero_float_json(cert_proc.stdout)
    except ValueError as exc:
        errors.append(f"STRICT_JSON_ERROR: {exc}")

    if spec["supports_live_corpus_recount"] and standalone_parsed is not None:
        if standalone_parsed.get("mode") != "standalone_fixture_replay":
            errors.append(
                f"UNEXPECTED_STANDALONE_MODE: {standalone_parsed.get('mode')}"
            )
        if standalone_parsed.get("live_corpus_recounted") is not False:
            errors.append("STANDALONE_MUST_REPORT_LIVE_CORPUS_RECOUNTED_FALSE")

    standalone_matches_committed = cert_proc.stdout == committed_cert_bytes
    if spec["recomputes_from_scratch_offline"] and not standalone_matches_committed:
        errors.append("OFFLINE_CERT_MISMATCH_VS_COMMITTED_JSON")

    # 3. Optional live recount for primary-corpus studies (`--live` / `--corpus-dir`)
    live_corpus_recounted = False
    live_stdout_sha: str | None = None
    live_rc: int | None = None
    live_matches_committed: bool | None = None
    if live and spec["supports_live_corpus_recount"]:
        if corpus_dir is None or not corpus_dir.is_dir():
            errors.append("LIVE_CORPUS_DIR_UNAVAILABLE")
        else:
            live_cmd = [
                sys.executable,
                "-I",
                "-B",
                "-W",
                "error",
                spec["cert_script"],
                "--corpus-dir",
                str(corpus_dir),
            ]
            live_proc = subprocess.run(live_cmd, cwd=str(study_path), capture_output=True)
            live_rc = live_proc.returncode
            live_stdout_sha = hashlib.sha256(live_proc.stdout).hexdigest()
            if live_proc.returncode != 0:
                errors.append(f"LIVE_CERTIFIER_NONZERO_EXIT: rc={live_proc.returncode}")
            expected_live_sha = spec["expected_live_stdout_sha256"]
            if expected_live_sha is not None and live_stdout_sha != expected_live_sha:
                errors.append(
                    f"LIVE_SHA256_MISMATCH: got={live_stdout_sha} expected={expected_live_sha}"
                )
            live_matches_committed = live_proc.stdout == committed_cert_bytes
            if not live_matches_committed:
                errors.append("LIVE_STDOUT_MISMATCH_VS_COMMITTED_CERTIFICATE")
            try:
                live_parsed = parse_strict_zero_float_json(live_proc.stdout)
                if live_parsed.get("mode") != "live_corpus_recount":
                    errors.append(f"UNEXPECTED_LIVE_MODE: {live_parsed.get('mode')}")
                if live_parsed.get("live_corpus_recounted") is not True:
                    errors.append("LIVE_MUST_REPORT_LIVE_CORPUS_RECOUNTED_TRUE")
                else:
                    live_corpus_recounted = True
            except ValueError as exc:
                errors.append(f"LIVE_STRICT_JSON_ERROR: {exc}")

    # 4. Run assertion-free R5 + known-answer test suite under -I -O -B -W error
    test_cmd = [sys.executable, "-I", "-O", "-B", "-W", "error", spec["test_script"]]
    test_proc = subprocess.run(test_cmd, cwd=str(study_path), capture_output=True)
    if test_proc.returncode != 0:
        errors.append(f"R5_TEST_NONZERO_EXIT: rc={test_proc.returncode}")

    offline_scope = (
        "recomputed_from_scratch_pure_q"
        if spec["recomputes_from_scratch_offline"]
        else "pinned_fixture_replay_no_corpus_read"
    )
    return {
        "audit_id": spec["audit_id"],
        "study_dir": spec["study_dir"],
        "passed": len(errors) == 0,
        "files_verified": files_verified,
        "offline_scope": offline_scope,
        "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
        "standalone_matches_committed_certificate": standalone_matches_committed,
        "standalone_stdout_sha256": cert_sha,
        "cert_rc": cert_proc.returncode,
        "live_corpus_recounted": live_corpus_recounted,
        "live_matches_committed_certificate": live_matches_committed,
        "live_stdout_sha256": live_stdout_sha,
        "live_rc": live_rc,
        "test_rc": test_proc.returncode,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify Foundation-0/bayt-al-hikma studies: offline standalone/fixture "
            "replay by default, or full live corpus recount with --live / --corpus-dir."
        )
    )
    parser.add_argument("--json", action="store_true", help="Emit canonical zero-float JSON report.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Also verify all 9 primary corpora and recount both Arabic studies live from disk.",
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=None,
        help="Path to downloaded primary corpora directory (implies --live; default ./corpora).",
    )
    args = parser.parse_args(argv)

    use_live = bool(args.live or args.corpus_dir is not None)
    resolved_corpus_dir: Path | None = None
    if use_live:
        resolved_corpus_dir = (
            (REPO_ROOT / "corpora") if args.corpus_dir is None else args.corpus_dir.resolve()
        )

    root_check = verify_root_files_and_fetch_manifest(REPO_ROOT, use_live, resolved_corpus_dir)
    results = [
        verify_study(spec, REPO_ROOT, use_live, resolved_corpus_dir) for spec in STUDY_SPECS
    ]

    study_files_verified = sum(int(r.get("files_verified", 0)) for r in results)
    root_files_verified = int(root_check["root_files_verified"])
    all_passed = bool(root_check["passed"] and all(r["passed"] for r in results))
    arabic_live_recounted = bool(
        use_live
        and all(
            r["live_corpus_recounted"]
            for r in results
            if not r["recomputes_from_scratch_offline"]
        )
    )
    execution_mode = (
        "live_corpus_recount_plus_standalone"
        if use_live
        else "offline_standalone_and_fixture_replay"
    )

    summary = {
        "schema": "bayt_al_hikma.verifier.v2",
        "execution_mode": execution_mode,
        "arabic_live_corpora_recounted": arabic_live_recounted,
        "offline_recomputed_studies": [
            r["study_dir"] for r in results if r["recomputes_from_scratch_offline"]
        ],
        "fixture_replayed_when_offline_studies": [
            r["study_dir"] for r in results if not r["recomputes_from_scratch_offline"]
        ],
        "root_check": root_check,
        "studies_checked": len(results),
        "studies_passed": sum(1 for r in results if r["passed"]),
        "root_files_verified": root_files_verified,
        "study_files_verified": study_files_verified,
        "total_files_verified": root_files_verified + study_files_verified,
        "passed": all_passed,
        "status": "PASS" if all_passed else "FAIL",
        "results": results,
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        live_tag = "true" if arabic_live_recounted else "false"
        extra = (
            f", {root_check['live_corpora_verified']}/{EXPECTED_FETCH_MANIFEST_COUNT} primary corpora verified"
            if use_live
            else ""
        )
        print(
            f"BAYT_AL_HIKMA_CHECK: {summary['status']} "
            f"[{execution_mode} | arabic_live_corpora_recounted={live_tag}] "
            f"({summary['studies_passed']}/{summary['studies_checked']} studies, "
            f"{summary['total_files_verified']} files{extra})"
        )
        if not use_live:
            print(
                "NOTE: Offline mode recomputes polymath-lineage & veins-and-branches from scratch, "
                "and replays pinned fixtures (reading NO corpus text) for arabic-continuum & arabic-lexicon."
            )
            print(
                "      Run `python3 fetch_corpora.py --dest ./corpora && "
                "python3 verify_all_standalone.py --live` for a full live recount from the 9 primary texts."
            )
        for err in root_check["errors"]:
            print(f"  [FAIL] root: ERROR: {err}")
        for r in results:
            tag = "PASS" if r["passed"] else "FAIL"
            sha16 = r.get("standalone_stdout_sha256", "")[:16]
            live_part = ""
            if use_live and r.get("live_stdout_sha256") is not None:
                live_part = f" live_sha256={r['live_stdout_sha256'][:16]} live_rc={r['live_rc']}"
            print(
                f"  [{tag}] {r['audit_id']} ({r['study_dir']}, {r['offline_scope']}): "
                f"files={r.get('files_verified', 0)} sha256={sha16} "
                f"cert_rc={r.get('cert_rc')}{live_part} test_rc={r.get('test_rc')}"
            )
            for err in r["errors"]:
                print(f"         ERROR: {err}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
