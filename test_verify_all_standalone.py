#!/usr/bin/env python3
"""Assertion-free, float-free regression suite for verify_all_standalone.py.

Covers strict zero-float JSON parsing, failed-study formatting (including
missing study directories, file SHA-256 tamper plants, and legacy result rows
omitting `offline_scope` — regression for KeyError: 'offline_scope'), root-file
mismatch refusals, live-dir failure handling, and full JSON/text CLI paths.
Emits 0 stdout bytes on PASS across -I -B, -I -O -B, and -I -B -W error.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable

_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.append(_ROOT)

import verify_all_standalone as vas  # noqa: E402


def _fail(msg: str) -> None:
    raise RuntimeError(f"VERIFY_ALL_STANDALONE_TEST_FAIL: {msg}")


def _check(cond: bool, msg: str) -> None:
    if cond is not True:
        _fail(msg)


def _check_raises_val(fn: Callable[[], Any], label: str, match: str) -> None:
    raised = False
    text = ""
    try:
        fn()
    except ValueError as exc:
        raised = True
        text = str(exc)
    if not raised:
        _fail(f"Expected ValueError for {label}")
    if match not in text:
        _fail(f"Expected {match!r} in {text!r} for {label}")


def test_strict_json_parser() -> None:
    ok = vas.parse_strict_zero_float_json(b'{"a": 1, "b": "ok"}')
    _check(ok == {"a": 1, "b": "ok"}, "valid strict json failed")
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b'{"a": 1, "a": 2}'),
        "dup key",
        "DUPLICATE_JSON_KEY",
    )
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b'{"x": 0.5}'),
        "float token",
        "FLOAT_FORBIDDEN_IN_JSON",
    )
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b'{"x": NaN}'),
        "nan token",
        "NONFINITE_JSON_CONSTANT",
    )
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b"[1, 2]"),
        "non-dict root",
        "TOP_LEVEL_JSON_MUST_BE_OBJECT",
    )


def test_failed_study_paths_and_offline_scope_regression() -> None:
    atlas_spec = vas.STUDY_SPECS[4]
    arabic_spec = vas.STUDY_SPECS[0]

    with tempfile.TemporaryDirectory() as td:
        tmp_root = Path(td)

        # 1. Missing study directory must carry offline_scope and fail closed
        miss_atlas = vas.verify_study(atlas_spec, tmp_root, False, None)
        _check(miss_atlas["passed"] is False, "missing atlas dir must fail")
        _check(miss_atlas["offline_scope"] == "recomputed_from_scratch_pure_q", "missing atlas offline_scope")
        _check(any("MISSING_STUDY_DIR" in e for e in miss_atlas["errors"]), "missing atlas error tag")

        miss_arabic = vas.verify_study(arabic_spec, tmp_root, False, None)
        _check(miss_arabic["passed"] is False, "missing arabic dir must fail")
        _check(miss_arabic["offline_scope"] == "pinned_fixture_replay_no_corpus_read", "missing arabic offline_scope")

        # 2. Tampered file inside an existing study dir must carry offline_scope and report FILE_SHA256_MISMATCH
        sdir = tmp_root / atlas_spec["study_dir"]
        sdir.mkdir(parents=True, exist_ok=True)
        for fname in atlas_spec["expected_file_sha256"]:
            (sdir / fname).write_bytes(b"corrupted\n")
        tampered = vas.verify_study(atlas_spec, tmp_root, False, None)
        _check(tampered["passed"] is False, "tampered study must fail")
        _check(tampered["offline_scope"] == "recomputed_from_scratch_pure_q", "tampered offline_scope")
        _check(any("FILE_SHA256_MISMATCH" in e for e in tampered["errors"]), "tampered sha mismatch error")

        # 3. Missing file inside an existing study dir
        empty_spec = copy.deepcopy(atlas_spec)
        empty_dir = tmp_root / "empty-study"
        empty_dir.mkdir(parents=True, exist_ok=True)
        empty_spec["study_dir"] = "empty-study"
        miss_files = vas.verify_study(empty_spec, tmp_root, False, None)
        _check(miss_files["passed"] is False and any("MISSING_FILE" in e for e in miss_files["errors"]), "missing file")

        # 4. Invalid float JSON with matching SHA-256 must fail with COMMITTED_JSON_ERROR
        bad_json_bytes = b'{"x": 0.5}\n'
        bad_json_sha = hashlib.sha256(bad_json_bytes).hexdigest()
        bad_dir = tmp_root / "bad-json-study"
        bad_dir.mkdir(parents=True, exist_ok=True)
        (bad_dir / "bad.json").write_bytes(bad_json_bytes)
        bad_json_spec = {
            "audit_id": "BAD-JSON",
            "study_dir": "bad-json-study",
            "cert_script": "x.py",
            "cert_args": [],
            "test_script": "t.py",
            "committed_certificate_file": "bad.json",
            "recomputes_from_scratch_offline": True,
            "supports_live_corpus_recount": False,
            "expected_standalone_stdout_sha256": bad_json_sha,
            "expected_live_stdout_sha256": None,
            "expected_file_sha256": {"bad.json": bad_json_sha},
        }
        bad_json_res = vas.verify_study(bad_json_spec, tmp_root, False, None)
        _check(
            bad_json_res["passed"] is False
            and any("COMMITTED_JSON_ERROR" in e for e in bad_json_res["errors"]),
            "float json on disk not rejected",
        )

        # 5. Root check missing files + live missing corpus dir
        rc_miss = vas.verify_root_files_and_fetch_manifest(tmp_root, True, tmp_root / "no_corpora")
        _check(rc_miss["passed"] is False, "missing root files must fail")
        _check(any("MISSING_ROOT_FILE" in e for e in rc_miss["errors"]), "missing root file tag")
        _check(any("LIVE_CORPUS_DIR_MISSING" in e for e in rc_miss["errors"]), "missing live dir tag")

        for fname in vas.ROOT_FILES_EXPECTED_SHA256:
            (tmp_root / fname).write_bytes(b"wrong\n")
        rc_bad = vas.verify_root_files_and_fetch_manifest(tmp_root, False, None)
        _check(any("ROOT_FILE_SHA256_MISMATCH" in e for e in rc_bad["errors"]), "root sha mismatch tag")

    # 6. Direct regression for main() failed-study print path (both with & without `offline_scope` key)
    orig_verify_root = vas.verify_root_files_and_fetch_manifest
    orig_verify_study = vas.verify_study
    try:
        vas.verify_root_files_and_fetch_manifest = lambda root, live, cdir: {
            "passed": False,
            "root_files_verified": 0,
            "fetch_manifest_sha256": "",
            "fetch_manifest_count": 0,
            "live_corpora_verified": 0,
            "errors": ["ROOT_PLANT_ERR"],
        }

        def _fake_verify_study(spec: dict[str, Any], root: Path, live: bool, cdir: Path | None) -> dict[str, Any]:
            if spec["audit_id"] == "HERITAGE-OPS":
                # Deliberately omit `offline_scope` to prove row.get("offline_scope", "unknown") never raises KeyError
                return {
                    "audit_id": spec["audit_id"],
                    "study_dir": spec["study_dir"],
                    "passed": False,
                    "files_verified": 7,
                    "recomputes_from_scratch_offline": True,
                    "live_corpus_recounted": False,
                    "errors": ["FILE_SHA256_MISMATCH: planted"],
                }
            return {
                "audit_id": spec["audit_id"],
                "study_dir": spec["study_dir"],
                "passed": True,
                "files_verified": len(spec["expected_file_sha256"]),
                "offline_scope": "recomputed_from_scratch_pure_q",
                "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
                "standalone_stdout_sha256": "0" * 64,
                "cert_rc": 0,
                "live_corpus_recounted": False,
                "test_rc": 0,
                "errors": [],
            }

        vas.verify_study = _fake_verify_study
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vas.main([])
        out = buf.getvalue()
        _check(rc == 1, "failed main([]) must exit 1")
        _check("BAYT_AL_HIKMA_CHECK: FAIL" in out, "missing FAIL banner")
        _check("[FAIL] root: ERROR: ROOT_PLANT_ERR" in out, "missing root error line")
        _check("[FAIL] HERITAGE-OPS (heritage-exact-operators, unknown):" in out, "missing unknown offline_scope fallback")
        _check("ERROR: FILE_SHA256_MISMATCH: planted" in out, "missing failed study error reason")

        # Also test --json output on failure
        buf_j = io.StringIO()
        with redirect_stdout(buf_j):
            rc_j = vas.main(["--json"])
        _check(rc_j == 1, "failed main(['--json']) must exit 1")
        parsed_j = json.loads(buf_j.getvalue())
        _check(parsed_j["status"] == "FAIL" and parsed_j["passed"] is False, "json failure payload invalid")
    finally:
        vas.verify_root_files_and_fetch_manifest = orig_verify_root
        vas.verify_study = orig_verify_study


def test_mocked_subprocess_guards_full_coverage() -> None:
    """Exercise every subprocess error & live-verification guard path in verify_all_standalone.py."""
    orig_run = vas.subprocess.run

    class _FakeProc:
        def __init__(self, rc: int, stdout: bytes) -> None:
            self.returncode = rc
            self.stdout = stdout
            self.stderr = b""

    with tempfile.TemporaryDirectory() as td:
        tmp_root = Path(td)
        corpus_dir = tmp_root / "corpora"
        corpus_dir.mkdir(parents=True, exist_ok=True)
        for fname in vas.ROOT_FILES_EXPECTED_SHA256:
            (tmp_root / fname).write_bytes(b"placeholder\n")

        # 1. Root fetch manifest & live verify guards (M008, M010, M012, M013, M015-M020)
        orig_root_shas = dict(vas.ROOT_FILES_EXPECTED_SHA256)
        orig_mf_sha = vas.EXPECTED_FETCH_MANIFEST_SHA256
        try:
            vas.ROOT_FILES_EXPECTED_SHA256 = {
                fn: hashlib.sha256(b"placeholder\n").hexdigest() for fn in orig_root_shas
            }
            valid_mf = b'{"count": 9}\n'
            valid_mf_sha = hashlib.sha256(valid_mf).hexdigest()
            vas.EXPECTED_FETCH_MANIFEST_SHA256 = valid_mf_sha

            # Happy live path (kills boundary_cmp == 0 inversions)
            vas.subprocess.run = lambda cmd, **kw: _FakeProc(0, valid_mf)  # type: ignore[assignment]
            ok_live = vas.verify_root_files_and_fetch_manifest(tmp_root, True, corpus_dir)
            _check(ok_live["passed"] is True and ok_live["live_corpora_verified"] == 9, "mocked live root pass")

            # M008: manifest nonzero rc
            vas.subprocess.run = lambda cmd, **kw: _FakeProc(1, valid_mf)  # type: ignore[assignment]
            r = vas.verify_root_files_and_fetch_manifest(tmp_root, False, None)
            _check(any("FETCH_MANIFEST_NONZERO_EXIT" in e for e in r["errors"]), "M008 missed")

            # M010: manifest sha mismatch
            vas.subprocess.run = lambda cmd, **kw: _FakeProc(0, b'{"count": 9}')  # type: ignore[assignment]
            r = vas.verify_root_files_and_fetch_manifest(tmp_root, False, None)
            _check(any("FETCH_MANIFEST_SHA256_MISMATCH" in e for e in r["errors"]), "M010 missed")

            # M012: manifest count mismatch (even with matching sha)
            bad_cnt = b'{"count": 8}\n'
            vas.EXPECTED_FETCH_MANIFEST_SHA256 = hashlib.sha256(bad_cnt).hexdigest()
            vas.subprocess.run = lambda cmd, **kw: _FakeProc(0, bad_cnt)  # type: ignore[assignment]
            r = vas.verify_root_files_and_fetch_manifest(tmp_root, False, None)
            _check(any("FETCH_MANIFEST_COUNT_MISMATCH" in e for e in r["errors"]), "M012 missed")

            # M013: manifest invalid JSON
            bad_js = b'{"count": 1.5}\n'
            vas.EXPECTED_FETCH_MANIFEST_SHA256 = hashlib.sha256(bad_js).hexdigest()
            vas.subprocess.run = lambda cmd, **kw: _FakeProc(0, bad_js)  # type: ignore[assignment]
            r = vas.verify_root_files_and_fetch_manifest(tmp_root, False, None)
            _check(any("FETCH_MANIFEST_JSON_ERROR" in e for e in r["errors"]), "M013 missed")

            # M015-M020: live verify-only paths
            vas.EXPECTED_FETCH_MANIFEST_SHA256 = valid_mf_sha

            def _run_v_rc1(cmd: list[str], **kw: Any) -> _FakeProc:
                return _FakeProc(0, valid_mf) if "--manifest-json" in cmd else _FakeProc(2, valid_mf)

            vas.subprocess.run = _run_v_rc1  # type: ignore[assignment]
            r = vas.verify_root_files_and_fetch_manifest(tmp_root, True, corpus_dir)
            _check(any("LIVE_CORPUS_VERIFY_FAILED" in e for e in r["errors"]), "M015-M017 missed")

            def _run_v_cnt8(cmd: list[str], **kw: Any) -> _FakeProc:
                return _FakeProc(0, valid_mf) if "--manifest-json" in cmd else _FakeProc(0, b'{"count": 8}\n')

            vas.subprocess.run = _run_v_cnt8  # type: ignore[assignment]
            r = vas.verify_root_files_and_fetch_manifest(tmp_root, True, corpus_dir)
            _check(any("LIVE_CORPUS_COUNT_MISMATCH" in e for e in r["errors"]), "M018-M019 missed")

            def _run_v_badjson(cmd: list[str], **kw: Any) -> _FakeProc:
                return _FakeProc(0, valid_mf) if "--manifest-json" in cmd else _FakeProc(0, b"not-json")

            vas.subprocess.run = _run_v_badjson  # type: ignore[assignment]
            r = vas.verify_root_files_and_fetch_manifest(tmp_root, True, corpus_dir)
            _check(any("LIVE_CORPUS_VERIFY_JSON_ERROR" in e for e in r["errors"]), "M020 missed")

            # 2. Study subprocess guards (M027-M048)
            st_dir = tmp_root / "mock-study"
            st_dir.mkdir(parents=True, exist_ok=True)
            sa_bytes = b'{"mode":"standalone_fixture_replay","live_corpus_recounted":false}\n'
            lv_bytes = b'{"mode":"live_corpus_recount","live_corpus_recounted":true}\n'
            sa_sha = hashlib.sha256(sa_bytes).hexdigest()
            lv_sha = hashlib.sha256(lv_bytes).hexdigest()
            (st_dir / "cert.json").write_bytes(lv_bytes)
            base_spec: dict[str, Any] = {
                "audit_id": "MOCK-1",
                "study_dir": "mock-study",
                "cert_script": "audit.py",
                "cert_args": ["--standalone"],
                "test_script": "test.py",
                "committed_certificate_file": "cert.json",
                "recomputes_from_scratch_offline": False,
                "supports_live_corpus_recount": True,
                "expected_standalone_stdout_sha256": sa_sha,
                "expected_live_stdout_sha256": lv_sha,
                "expected_file_sha256": {"cert.json": lv_sha},
            }

            # M027: when file hash fails, subprocess must NOT be invoked
            called = {"n": 0}

            def _fail_if_called(cmd: list[str], **kw: Any) -> _FakeProc:
                called["n"] += 1
                return _FakeProc(0, sa_bytes)

            vas.subprocess.run = _fail_if_called  # type: ignore[assignment]
            bad_file_spec = copy.deepcopy(base_spec)
            bad_file_spec["expected_file_sha256"]["cert.json"] = "0" * 64
            r_early = vas.verify_study(bad_file_spec, tmp_root, False, None)
            _check(r_early["passed"] is False and called["n"] == 0, "M027 early return bypassed")

            def _mk_runner(
                sa_rc: int = 0,
                sa_out: bytes = sa_bytes,
                lv_rc: int = 0,
                lv_out: bytes = lv_bytes,
                tst_rc: int = 0,
            ) -> Callable[..., _FakeProc]:
                def _run(cmd: list[str], **kw: Any) -> _FakeProc:
                    if "--standalone" in cmd:
                        return _FakeProc(sa_rc, sa_out)
                    if "--corpus-dir" in cmd:
                        return _FakeProc(lv_rc, lv_out)
                    return _FakeProc(tst_rc, b"")

                return _run

            # Clean live pass (kills boundary_cmp inversions across M028, M030, M033, M037, M039, M043, M047)
            vas.subprocess.run = _mk_runner()  # type: ignore[assignment]
            r_ok = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(r_ok["passed"] is True and r_ok["live_corpus_recounted"] is True, f"clean mock live failed: {r_ok}")

            # M028-M029: cert_proc rc != 0
            vas.subprocess.run = _mk_runner(sa_rc=2)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, False, None)
            _check(any("CERTIFIER_NONZERO_EXIT" in e for e in r["errors"]), "M028-M029 missed")

            # M030-M031: standalone sha mismatch
            vas.subprocess.run = _mk_runner(sa_out=b'{"mode":"standalone_fixture_replay","live_corpus_recounted":false}')  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, False, None)
            _check(any("STANDALONE_SHA256_MISMATCH" in e for e in r["errors"]), "M030-M031 missed")

            # M032: standalone invalid JSON
            bad_sa = b'{"x": 0.5}\n'
            spec_bad_sa = copy.deepcopy(base_spec)
            spec_bad_sa["expected_standalone_stdout_sha256"] = hashlib.sha256(bad_sa).hexdigest()
            vas.subprocess.run = _mk_runner(sa_out=bad_sa)  # type: ignore[assignment]
            r = vas.verify_study(spec_bad_sa, tmp_root, False, None)
            _check(any("STRICT_JSON_ERROR" in e for e in r["errors"]), "M032 missed")

            # M033-M034: standalone wrong mode
            wrong_mode = b'{"mode":"wrong","live_corpus_recounted":false}\n'
            spec_wm = copy.deepcopy(base_spec)
            spec_wm["expected_standalone_stdout_sha256"] = hashlib.sha256(wrong_mode).hexdigest()
            vas.subprocess.run = _mk_runner(sa_out=wrong_mode)  # type: ignore[assignment]
            r = vas.verify_study(spec_wm, tmp_root, False, None)
            _check(any("UNEXPECTED_STANDALONE_MODE" in e for e in r["errors"]), "M033-M034 missed")

            # M035: standalone live_corpus_recounted != False
            wrong_flag = b'{"mode":"standalone_fixture_replay","live_corpus_recounted":true}\n'
            spec_wf = copy.deepcopy(base_spec)
            spec_wf["expected_standalone_stdout_sha256"] = hashlib.sha256(wrong_flag).hexdigest()
            vas.subprocess.run = _mk_runner(sa_out=wrong_flag)  # type: ignore[assignment]
            r = vas.verify_study(spec_wf, tmp_root, False, None)
            _check(any("STANDALONE_MUST_REPORT_LIVE_CORPUS_RECOUNTED_FALSE" in e for e in r["errors"]), "M035 missed")

            # M036: recomputes_from_scratch_offline bytes differ from committed json
            spec_off = copy.deepcopy(base_spec)
            spec_off["recomputes_from_scratch_offline"] = True
            spec_off["supports_live_corpus_recount"] = False
            vas.subprocess.run = _mk_runner(sa_out=sa_bytes)  # type: ignore[assignment]
            r = vas.verify_study(spec_off, tmp_root, False, None)
            _check(any("OFFLINE_CERT_MISMATCH_VS_COMMITTED_JSON" in e for e in r["errors"]), "M036 missed")

            # M037-M038: live missing corpus dir
            r = vas.verify_study(base_spec, tmp_root, True, tmp_root / "absent")
            _check(any("LIVE_CORPUS_DIR_UNAVAILABLE" in e for e in r["errors"]), "M037-M038 missed")

            # M039-M040: live_proc rc != 0
            vas.subprocess.run = _mk_runner(lv_rc=3)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(any("LIVE_CERTIFIER_NONZERO_EXIT" in e for e in r["errors"]), "M039-M040 missed")

            # M041 & M042: live sha mismatch & live bytes != committed
            alt_lv = b'{"mode":"live_corpus_recount","live_corpus_recounted":true} \n'
            vas.subprocess.run = _mk_runner(lv_out=alt_lv)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(any("LIVE_SHA256_MISMATCH" in e for e in r["errors"]), "M041 missed")
            _check(any("LIVE_STDOUT_MISMATCH_VS_COMMITTED_CERTIFICATE" in e for e in r["errors"]), "M042 missed")

            # M042 isolated (expected_live_stdout_sha256 matches alt_lv, committed differs)
            spec_m42 = copy.deepcopy(base_spec)
            spec_m42["expected_live_stdout_sha256"] = hashlib.sha256(alt_lv).hexdigest()
            vas.subprocess.run = _mk_runner(lv_out=alt_lv)  # type: ignore[assignment]
            r = vas.verify_study(spec_m42, tmp_root, True, corpus_dir)
            _check(any("LIVE_STDOUT_MISMATCH_VS_COMMITTED_CERTIFICATE" in e for e in r["errors"]), "M042 iso missed")

            # M043-M044: live wrong mode
            lv_wm = b'{"mode":"bad_live","live_corpus_recounted":true}\n'
            (st_dir / "cert.json").write_bytes(lv_wm)
            spec_lwm = copy.deepcopy(base_spec)
            lv_wm_sha = hashlib.sha256(lv_wm).hexdigest()
            spec_lwm["expected_live_stdout_sha256"] = lv_wm_sha
            spec_lwm["expected_file_sha256"]["cert.json"] = lv_wm_sha
            vas.subprocess.run = _mk_runner(lv_out=lv_wm)  # type: ignore[assignment]
            r = vas.verify_study(spec_lwm, tmp_root, True, corpus_dir)
            _check(any("UNEXPECTED_LIVE_MODE" in e for e in r["errors"]), "M043-M044 missed")

            # M045: live_corpus_recounted != True
            lv_wf = b'{"mode":"live_corpus_recount","live_corpus_recounted":false}\n'
            (st_dir / "cert.json").write_bytes(lv_wf)
            spec_lwf = copy.deepcopy(base_spec)
            lv_wf_sha = hashlib.sha256(lv_wf).hexdigest()
            spec_lwf["expected_live_stdout_sha256"] = lv_wf_sha
            spec_lwf["expected_file_sha256"]["cert.json"] = lv_wf_sha
            vas.subprocess.run = _mk_runner(lv_out=lv_wf)  # type: ignore[assignment]
            r = vas.verify_study(spec_lwf, tmp_root, True, corpus_dir)
            _check(any("LIVE_MUST_REPORT_LIVE_CORPUS_RECOUNTED_TRUE" in e for e in r["errors"]), "M045 missed")

            # M046: live invalid JSON
            (st_dir / "cert.json").write_bytes(lv_bytes)
            vas.subprocess.run = _mk_runner(lv_out=b"not-json")  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(any("LIVE_STRICT_JSON_ERROR" in e for e in r["errors"]), "M046 missed")

            # M047-M048: test_proc rc != 0
            vas.subprocess.run = _mk_runner(tst_rc=1)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, False, None)
            _check(any("R5_TEST_NONZERO_EXIT" in e for e in r["errors"]), "M047-M048 missed")
        finally:
            vas.subprocess.run = orig_run
            vas.ROOT_FILES_EXPECTED_SHA256 = orig_root_shas
            vas.EXPECTED_FETCH_MANIFEST_SHA256 = orig_mf_sha


def test_live_root_files_pass() -> None:
    root_res = vas.verify_root_files_and_fetch_manifest(vas.REPO_ROOT, False, None)
    _check(root_res["passed"] is True and root_res["errors"] == [], f"root files failed: {root_res}")
    _check(root_res["root_files_verified"] == len(vas.ROOT_FILES_EXPECTED_SHA256), "root file count mismatch")
    _check(root_res["fetch_manifest_count"] == vas.EXPECTED_FETCH_MANIFEST_COUNT, "manifest count mismatch")


def main() -> int:
    test_strict_json_parser()
    test_failed_study_paths_and_offline_scope_regression()
    test_mocked_subprocess_guards_full_coverage()
    test_live_root_files_pass()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
