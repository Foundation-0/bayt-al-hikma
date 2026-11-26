#!/usr/bin/env python3
"""
Portable Zero-Dependency Verifier for Foundation-0/bayt-al-hikma.

Supports two explicitly distinguished modes:

1. Offline mode (default):
   - Verifies exact SHA-256 parity on all 47/47 pinned repository files
     (fetch_corpora.py, PREREGISTERED_HYPOTHESES.md, test_verify_all_standalone.py,
     and all 44 study files).
   - Verifies fetch_corpora.py --manifest-json parses strictly zero-float
     (9 pinned primary corpora) and matches its pinned digest.
   - Recomputes every mathematical claim in polymath-lineage/,
     veins-and-branches/, heritage-corpus-atlas/, heritage-exact-operators/,
     and raw-arabic-scientific-mesh/ from scratch under isolated `-I -B -W error`
     and confirms byte-identical parity with their committed JSON certificates.
   - Runs arabic-continuum/ and arabic-lexicon/ in `--standalone` mode
     (pinned-fixture invariant replay; reads NO corpus file;
     `arabic_live_corpora_recounted: false`).
   - Runs all 7 assertion-free R5 + known-answer test suites under
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
import errno
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent

ROOT_FILES_EXPECTED_SHA256: dict[str, str] = {
    "PREREGISTERED_HYPOTHESES.md": (
        "8513d403963041c6996818218f4d6f389bd92fd2c048f1fc4b99119c7f2087b7"
    ),
    "fetch_corpora.py": (
        "606353db2207ea75ad20d7b5f5b1f608242f617cae81ce8d434c5172d59677e0"
    ),
    "test_verify_all_standalone.py": (
        "d7a0aaa214443ef990954af0b1d0f0fa09cc28b8d6c79292e461ed2b8b9d0637"
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
                "1bbd30afb89d91585c6c31112afe9e8fea9e05246623786fb929e9b0f543ded4"
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
    {
        "audit_id": "HERITAGE-ATLAS",
        "study_dir": "heritage-corpus-atlas",
        "cert_script": "verify_s89_heritage_atlas.py",
        "cert_args": ["--standalone"],
        "test_script": "test_s89_heritage_atlas_r5.py",
        "committed_certificate_file": "s89_heritage_atlas_certificate.json",
        "recomputes_from_scratch_offline": True,
        "supports_live_corpus_recount": False,
        "expected_standalone_stdout_sha256": (
            "c1516abf5cf57882db13190a2176ed68c40da02305f6cb37f1bffd0729513f0d"
        ),
        "expected_live_stdout_sha256": None,
        "expected_file_sha256": {
            "ClassicalHeritageAtlas.lean": (
                "55832d30fe3af2ef1c5f2d22b638d4f927d9f1e3bef09729c81ec2bbf24f239a"
            ),
            "REPORT.md": (
                "9b6c4b56e687b4c6d5f052b683d46e61a9444ec54848719c23fc30c2dc4dccf8"
            ),
            "lakefile.toml": (
                "40cebcde95ef89e4034c818723423eaed660e6a957930e608b8586315343891b"
            ),
            "lean-toolchain": (
                "582a63f8f9c5128067b688778c1051cf1464c3ca9d57b9325025c051c29b774a"
            ),
            "s89_heritage_atlas_certificate.json": (
                "c1516abf5cf57882db13190a2176ed68c40da02305f6cb37f1bffd0729513f0d"
            ),
            "s89_heritage_atlas_oracle.py": (
                "5ccf7b8b016a68e0cbf0719098a610619a4f8d319f3bd56c1caa3f287f1bf911"
            ),
            "test_s89_heritage_atlas_r5.py": (
                "f3588deedb9dc20e4da412f2cfca1392c4f465621266daa828619a4c5f29909d"
            ),
            "verify_s89_heritage_atlas.py": (
                "69aac984fa264be52a4d62b0da2238ebcfe1aa1773a0c4a75e10a32c22be332f"
            ),
        },
    },
    {
        "audit_id": "HERITAGE-OPS",
        "study_dir": "heritage-exact-operators",
        "cert_script": "verify_s90_heritage_operators.py",
        "cert_args": ["--standalone"],
        "test_script": "test_s90_heritage_operators_r5.py",
        "committed_certificate_file": "s90_heritage_operators_certificate.json",
        "recomputes_from_scratch_offline": True,
        "supports_live_corpus_recount": False,
        "expected_standalone_stdout_sha256": (
            "51430e59d32471e0cbafd3836a8d4438511a41fc89aac5594a9b9b1adcddd2bd"
        ),
        "expected_live_stdout_sha256": None,
        "expected_file_sha256": {
            "HeritageExactOperators.lean": (
                "4ac15befb87c774d6fa114e2b864639c68c32f5e170c65e3b6af2ef472cfede3"
            ),
            "REPORT.md": (
                "4ab46f8315774158a343d37ee613689cb6bb2c400585d1d2e6bc8b2bd46c2fca"
            ),
            "lakefile.toml": (
                "70df68cd815c757ccb7461560b9765c2f206313449a0cbe3759ab5a42501dac9"
            ),
            "lean-toolchain": (
                "582a63f8f9c5128067b688778c1051cf1464c3ca9d57b9325025c051c29b774a"
            ),
            "s90_heritage_operators_certificate.json": (
                "51430e59d32471e0cbafd3836a8d4438511a41fc89aac5594a9b9b1adcddd2bd"
            ),
            "s90_heritage_operators_oracle.py": (
                "222120eabcb2b478ca8210e0b1f1abf6e252aa83989cf3feaf26035fc6500aaf"
            ),
            "test_s90_heritage_operators_r5.py": (
                "a3f74718261b80a0ce57e017aa527c2a8dc59b50312ab1dadce1387e8d8df571"
            ),
            "verify_s90_heritage_operators.py": (
                "a1782054c798f252bbf98ddcff82c8a1ff0c674b342d97fae5d2d2fc6ffc1551"
            ),
        },
    },
    {
        "audit_id": "ARABIC-MESH",
        "study_dir": "raw-arabic-scientific-mesh",
        "cert_script": "verify_s92_raw_arabic_mesh.py",
        "cert_args": ["--standalone"],
        "test_script": "test_s92_raw_arabic_mesh_r5.py",
        "committed_certificate_file": "s92_raw_arabic_mesh_certificate.json",
        "recomputes_from_scratch_offline": True,
        "supports_live_corpus_recount": False,
        "expected_standalone_stdout_sha256": (
            "687ef58006d5032692af01c8607d5c0c0f873f925cbd1bed4c43eb8fe9f0bfb9"
        ),
        "expected_live_stdout_sha256": None,
        "expected_file_sha256": {
            "REPORT.md": (
                "47562abc925bfb74fd821439c8cbb66bddbb4449e89e36e19ddecd67b7a250c4"
            ),
            "RawArabicHigherOrderMesh.lean": (
                "5218f72990f82c8aedd948daeac0bd105349dcc41848a455c824933a71235486"
            ),
            "lakefile.toml": (
                "f4cccdd80678ecc5aa12fdc85f19ab8eee1f784f49c514c76b6329c7d24fcf40"
            ),
            "lean-toolchain": (
                "582a63f8f9c5128067b688778c1051cf1464c3ca9d57b9325025c051c29b774a"
            ),
            "s92_raw_arabic_anchor.json": (
                "eeffe3c912d8f4037b5e04cfc06abbe6fd9145802ca9009ac0a2ae184621db89"
            ),
            "s92_raw_arabic_capture.py": (
                "2fe9edbf5055a205cf1fa454746548487c1e98f22ee37caa27209551cbed9c58"
            ),
            "s92_raw_arabic_mesh_certificate.json": (
                "687ef58006d5032692af01c8607d5c0c0f873f925cbd1bed4c43eb8fe9f0bfb9"
            ),
            "s92_raw_arabic_mesh_oracle.py": (
                "1c3bf140a065a4a584599b1d6ab64faec9655dc0c42014275c390ecd8023aac4"
            ),
            "test_s92_raw_arabic_mesh_r5.py": (
                "0f63459d875981d01af0a0638e77092aaff91dded258304537a68eb684dad38b"
            ),
            "verify_s92_raw_arabic_mesh.py": (
                "f5d736ecf50e36eda4fcd71cf528cf804650d0de9bd7d0e82da4df3b8c588965"
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


MAX_REGULAR_FILE_BYTES = 16 * 1024 * 1024
MAX_JSON_INT_DIGITS = 1024


def _is_strict_int(val: Any) -> bool:
    return type(val) is int


def _parse_bounded_int(token: str) -> int:
    digits = token[1:] if token.startswith("-") else token
    if len(digits) > MAX_JSON_INT_DIGITS:
        raise ValueError("MAX_INT_DIGITS_EXCEEDED")
    return int(token)


def _norm_abs_parts(path: Path) -> list[str]:
    full = path if path.is_absolute() else (Path(os.getcwd()) / path)
    parts: list[str] = []
    for part in full.parts[1:]:
        if part == "..":
            if parts:
                parts.pop()
        elif part != ".":
            parts.append(part)
    return parts


def _open_dir_chain_nofol(dir_parts: list[str]) -> tuple[str | None, int]:
    """Traverse every directory component from '/' with O_DIRECTORY | O_NOFOLLOW."""
    dflags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    dfd = os.open("/", dflags)
    for comp in dir_parts:
        try:
            st_c = os.lstat(comp, dir_fd=dfd)
            if stat.S_ISLNK(st_c.st_mode):
                os.close(dfd)
                return "SYMLINK_FORBIDDEN", -1
            nxt = os.open(comp, dflags, dir_fd=dfd)
        except FileNotFoundError:
            os.close(dfd)
            return "MISSING", -1
        except OSError:
            os.close(dfd)
            return "NOT_REGULAR_FILE", -1
        os.close(dfd)
        dfd = nxt
    return None, dfd


def _check_dir_nofol(path: Path | None) -> str | None:
    if path is None:
        return "MISSING"
    err, dfd = _open_dir_chain_nofol(_norm_abs_parts(path))
    if dfd >= 0:
        os.close(dfd)
    return err


def _lstat_is_dir(path: Path | None) -> bool:
    return _check_dir_nofol(path) is None


def _lstat_is_reg(path: Path) -> bool:
    ferr, _ = _read_regular_nofol_bytes(path, max_bytes=MAX_REGULAR_FILE_BYTES)
    return ferr is None


def _read_regular_nofol_bytes(
    path: Path,
    *,
    max_bytes: int = MAX_REGULAR_FILE_BYTES,
) -> tuple[str | None, bytes]:
    """Read regular file bytes with root-to-leaf O_NOFOLLOW ancestor walk and size cap."""
    parts = _norm_abs_parts(path)
    if not parts:
        return "NOT_REGULAR_FILE", b""
    derr, dfd = _open_dir_chain_nofol(parts[:-1])
    if derr is not None:
        return derr, b""
    oflags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_NOCTTY", 0)
    )
    fd = -1
    try:
        try:
            fd = os.open(parts[-1], oflags, dir_fd=dfd)
        except FileNotFoundError:
            return "MISSING", b""
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                return "SYMLINK_FORBIDDEN", b""
            return "NOT_REGULAR_FILE", b""
        st_f = os.fstat(fd)
        if not stat.S_ISREG(st_f.st_mode):
            return "NOT_REGULAR_FILE", b""
        chunks: list[bytes] = []
        total = 0
        while True:
            blk = os.read(fd, min(65536, max_bytes - total + 1))
            if not blk:
                break
            total += len(blk)
            if total > max_bytes:
                return "FILE_TOO_LARGE", b""
            chunks.append(blk)
        return None, b"".join(chunks)
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(dfd)


MAX_JSON_DEPTH = 64


def _check_json_depth(text: str) -> None:
    depth = 0
    in_str = False
    esc = False
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ValueError("MAX_JSON_DEPTH_EXCEEDED")
        elif ch in "}]":
            if depth > 0:
                depth -= 1


def parse_strict_zero_float_json(raw_bytes: bytes) -> dict[str, Any]:
    if len(raw_bytes) > MAX_REGULAR_FILE_BYTES:
        raise ValueError("JSON_PAYLOAD_TOO_LARGE")
    try:
        text = raw_bytes.decode("utf-8")
        _check_json_depth(text)
        parsed = json.loads(
            text,
            object_pairs_hook=_strict_no_dups_hook,
            parse_constant=_forbid_constant,
            parse_float=_forbid_float,
            parse_int=_parse_bounded_int,
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise ValueError(f"INVALID_STRICT_JSON: {exc}") from exc
    if type(parsed) is not dict:
        raise ValueError("TOP_LEVEL_JSON_MUST_BE_OBJECT")
    return parsed


def _resolve_corpus_dir(repo_root: Path, corpus_dir: Path | None) -> Path | None:
    if corpus_dir is None:
        return None
    if corpus_dir.is_absolute():
        return corpus_dir
    return Path(os.path.abspath(repo_root / corpus_dir))


def verify_root_files_and_fetch_manifest(
    repo_root: Path,
    live: bool,
    corpus_dir: Path | None,
) -> dict[str, Any]:
    errors: list[str] = []
    files_verified = 0
    fetch_script_verified = False
    abs_corpus_dir = _resolve_corpus_dir(repo_root, corpus_dir)

    for fname, expected_sha in sorted(ROOT_FILES_EXPECTED_SHA256.items()):
        fpath = repo_root / fname
        ferr, raw = _read_regular_nofol_bytes(fpath)
        if ferr is not None:
            tag = "MISSING_ROOT_FILE" if ferr == "MISSING" else ferr
            errors.append(f"{tag}: {fname}")
            continue
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != expected_sha:
            errors.append(
                f"ROOT_FILE_SHA256_MISMATCH: {fname} got={actual_sha} expected={expected_sha}"
            )
            continue
        files_verified += 1
        if fname == "fetch_corpora.py":
            fetch_script_verified = True

    manifest_sha = ""
    manifest_count = 0
    if fetch_script_verified:
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
            raw_cnt = manifest_obj.get("count")
            if not _is_strict_int(raw_cnt):
                raise ValueError("MANIFEST_COUNT_NOT_STRICT_INT")
            manifest_count = raw_cnt
            if manifest_count != EXPECTED_FETCH_MANIFEST_COUNT:
                errors.append(
                    f"FETCH_MANIFEST_COUNT_MISMATCH: got={manifest_count} "
                    f"expected={EXPECTED_FETCH_MANIFEST_COUNT}"
                )
        except ValueError as exc:
            errors.append(f"FETCH_MANIFEST_JSON_ERROR: {exc}")

    live_corpora_verified = 0
    if live:
        if not _lstat_is_dir(abs_corpus_dir):
            errors.append("LIVE_CORPUS_DIR_MISSING")
        elif fetch_script_verified:
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
                    str(abs_corpus_dir),
                ],
                cwd=str(repo_root),
                capture_output=True,
            )
            if v_proc.returncode != 0:
                errors.append(f"LIVE_CORPUS_VERIFY_FAILED: rc={v_proc.returncode}")
            else:
                try:
                    v_obj = parse_strict_zero_float_json(v_proc.stdout)
                    raw_lcnt = v_obj.get("count")
                    if not _is_strict_int(raw_lcnt):
                        raise ValueError("LIVE_COUNT_NOT_STRICT_INT")
                    live_corpora_verified = raw_lcnt
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
    supports_live = bool(spec["supports_live_corpus_recount"])
    offline_scope = (
        "recomputed_from_scratch_pure_q"
        if spec["recomputes_from_scratch_offline"]
        else "pinned_fixture_replay_no_corpus_read"
    )

    sdir_err = _check_dir_nofol(study_path)
    if sdir_err is not None:
        err_tag = "SYMLINK_FORBIDDEN" if sdir_err == "SYMLINK_FORBIDDEN" else "MISSING_STUDY_DIR"
        return {
            "audit_id": spec["audit_id"],
            "study_dir": spec["study_dir"],
            "passed": False,
            "files_verified": 0,
            "offline_scope": offline_scope,
            "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
            "supports_live_corpus_recount": supports_live,
            "live_corpus_recounted": False,
            "errors": [f"{err_tag}: {spec['study_dir']}"],
        }

    # 1. Verify byte-identical SHA-256 on every pinned package file (and strict JSON on .json files)
    files_verified = 0
    committed_cert_bytes = b""
    committed_cert_name = spec["committed_certificate_file"]
    for fname, expected_sha in sorted(spec["expected_file_sha256"].items()):
        fpath = study_path / fname
        ferr, raw = _read_regular_nofol_bytes(fpath)
        if ferr is not None:
            tag = "MISSING_FILE" if ferr == "MISSING" else ferr
            errors.append(f"{tag}: {spec['study_dir']}/{fname}")
            continue
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
            "offline_scope": offline_scope,
            "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
            "supports_live_corpus_recount": supports_live,
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

    if supports_live and standalone_parsed is not None:
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
    if live and supports_live:
        abs_corpus_dir = _resolve_corpus_dir(repo_root, corpus_dir)
        if not _lstat_is_dir(abs_corpus_dir):
            errors.append("LIVE_CORPUS_DIR_UNAVAILABLE")
        else:
            live_err_start = len(errors)
            live_cmd = [
                sys.executable,
                "-I",
                "-B",
                "-W",
                "error",
                spec["cert_script"],
                "--corpus-dir",
                str(abs_corpus_dir),
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
                elif len(errors) == live_err_start:
                    live_corpus_recounted = True
            except ValueError as exc:
                errors.append(f"LIVE_STRICT_JSON_ERROR: {exc}")

    # 4. Run assertion-free R5 + known-answer test suite under -I -O -B -W error
    test_cmd = [sys.executable, "-I", "-O", "-B", "-W", "error", spec["test_script"]]
    test_proc = subprocess.run(test_cmd, cwd=str(study_path), capture_output=True)
    if test_proc.returncode != 0:
        errors.append(f"R5_TEST_NONZERO_EXIT: rc={test_proc.returncode}")
        live_corpus_recounted = False

    return {
        "audit_id": spec["audit_id"],
        "study_dir": spec["study_dir"],
        "passed": len(errors) == 0,
        "files_verified": files_verified,
        "offline_scope": offline_scope,
        "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
        "supports_live_corpus_recount": supports_live,
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
        raw_corpus_dir = (
            (REPO_ROOT / "corpora") if args.corpus_dir is None else args.corpus_dir
        )
        resolved_corpus_dir = Path(os.path.abspath(raw_corpus_dir))

    root_check = verify_root_files_and_fetch_manifest(REPO_ROOT, use_live, resolved_corpus_dir)
    results = [
        verify_study(spec, REPO_ROOT, use_live, resolved_corpus_dir) for spec in STUDY_SPECS
    ]

    study_files_verified = sum(int(r.get("files_verified", 0)) for r in results)
    root_files_verified = int(root_check["root_files_verified"])
    all_passed = bool(root_check["passed"] and all(r["passed"] for r in results))
    live_studies = [r for r in results if r.get("supports_live_corpus_recount") is True]
    arabic_live_recounted = bool(
        use_live
        and all_passed
        and len(live_studies) > 0
        and all(r.get("live_corpus_recounted") is True for r in live_studies)
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
                "NOTE: Offline mode recomputes polymath-lineage, veins-and-branches, "
                "heritage-corpus-atlas, heritage-exact-operators & raw-arabic-scientific-mesh "
                "from scratch, and replays pinned fixtures (reading NO corpus text) for "
                "arabic-continuum & arabic-lexicon."
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
                live_part = (
                    f" live_sha256={r.get('live_stdout_sha256', '')[:16]}"
                    f" live_rc={r.get('live_rc')}"
                )
            print(
                f"  [{tag}] {r['audit_id']} ({r['study_dir']}, {r.get('offline_scope', 'unknown')}): "
                f"files={r.get('files_verified', 0)} sha256={sha16} "
                f"cert_rc={r.get('cert_rc')}{live_part} test_rc={r.get('test_rc')}"
            )
            for err in r["errors"]:
                print(f"         ERROR: {err}")

    return 0 if all_passed else 1


def run_cli(argv: list[str] | None = None) -> int:
    try:
        rc = main(argv)
        sys.stdout.flush()
        return rc
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(devnull, 1)
        finally:
            os.close(devnull)
        return 2
    except (OSError, MemoryError) as exc:
        try:
            sys.stderr.write(f"BAYT_AL_HIKMA_RUNTIME_ERROR: {exc}\n")
            sys.stderr.flush()
        except OSError:
            pass
        return 2


if __name__ == "__main__":
    raise SystemExit(run_cli())
