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
import os
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
    ok_int1024 = vas.parse_strict_zero_float_json(b'{"x": -' + b"9" * 1024 + b"}")
    _check(ok_int1024["x"] == -(10**1024 - 1), "1024-digit negative int must pass")
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b'{"x": ' + b"9" * 1025 + b"}"),
        "1025-digit int",
        "MAX_INT_DIGITS_EXCEEDED",
    )
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b'{"x": -' + b"9" * 1025 + b"}"),
        "1025-digit negative int",
        "MAX_INT_DIGITS_EXCEEDED",
    )
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b'{"x": ' + b"9" * 4400 + b"}"),
        "4400-digit int",
        "MAX_INT_DIGITS_EXCEEDED",
    )
    ok_max_raw = b'{"x":"' + b"a" * (vas.MAX_REGULAR_FILE_BYTES - 8) + b'"}'
    _check(len(ok_max_raw) == vas.MAX_REGULAR_FILE_BYTES, "exact MAX_REGULAR_FILE_BYTES len")
    _check(type(vas.parse_strict_zero_float_json(ok_max_raw)) is dict, "exact MAX_REGULAR_FILE_BYTES json")
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(ok_max_raw + b" "),
        "over MAX_REGULAR_FILE_BYTES json",
        "JSON_PAYLOAD_TOO_LARGE",
    )
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json(b"\xff\xfe"),
        "invalid utf8",
        "INVALID_STRICT_JSON",
    )
    _check(
        vas.parse_strict_zero_float_json(b'{"s": "\\"' + (b"{" * 70) + b'\\""}')["s"] == '"' + ("{" * 70) + '"',
        "string braces ignored by depth guard",
    )
    ok64 = vas.parse_strict_zero_float_json((b'{"a":' * 64) + b"1" + (b"}" * 64))
    _check(type(ok64) is dict, "depth 64 must pass")
    _check_raises_val(
        lambda: vas.parse_strict_zero_float_json((b'{"a":' * 65) + b"1" + (b"}" * 65)),
        "depth 65 exceeded",
        "MAX_JSON_DEPTH_EXCEEDED",
    )
    _check(vas._read_regular_nofol_bytes(Path("/"))[0] == "NOT_REGULAR_FILE", "root path read")
    _check(vas._read_regular_nofol_bytes(Path("/.."))[0] == "NOT_REGULAR_FILE", "root dotdot read")
    _check(vas._read_regular_nofol_bytes(Path("/dev/null/sub"))[0] == "NOT_REGULAR_FILE", "enotdir open")
    rel_readme = Path(os.path.relpath(vas.REPO_ROOT / "README.md", os.getcwd()))
    _check(vas._read_regular_nofol_bytes(rel_readme)[0] is None, "relative path read")
    _check(vas._lstat_is_dir(None) is False, "lstat_is_dir None")
    _check(vas._lstat_is_dir(Path("/dev/null/sub")) is False, "lstat_is_dir enotdir")
    _check(vas._lstat_is_reg(Path("/dev/null/sub")) is False, "lstat_is_reg enotdir")
    _check(vas._lstat_is_reg(vas.REPO_ROOT / "README.md") is True, "lstat_is_reg valid regular file")
    _check(vas._resolve_corpus_dir(vas.REPO_ROOT, None) is None, "resolve_corpus_dir None")
    _check(
        vas._resolve_corpus_dir(Path("/tmp/r"), Path("rel_c")) == Path("/tmp/r/rel_c"),
        "resolve_corpus_dir relative",
    )
    _check(
        vas._resolve_corpus_dir(Path("/tmp/r"), Path("/abs/c")) == Path("/abs/c"),
        "resolve_corpus_dir absolute",
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

        # 5b. Symlink & FIFO refusal via O_NOFOLLOW on root files, study dir, study files, and corpus dir
        sym_root = tmp_root / "sym_root"
        sym_root.mkdir(parents=True, exist_ok=True)
        for fname in vas.ROOT_FILES_EXPECTED_SHA256:
            (sym_root / fname).symlink_to(tmp_root / fname)
        rc_sym = vas.verify_root_files_and_fetch_manifest(sym_root, False, None)
        _check(rc_sym["passed"] is False and any("SYMLINK_FORBIDDEN" in e for e in rc_sym["errors"]), "root symlink")

        fifo_root = tmp_root / "fifo_root"
        fifo_root.mkdir(parents=True, exist_ok=True)
        for fname in vas.ROOT_FILES_EXPECTED_SHA256:
            os.mkfifo(fifo_root / fname)
        rc_fifo = vas.verify_root_files_and_fetch_manifest(fifo_root, False, None)
        _check(rc_fifo["passed"] is False and any("NOT_REGULAR_FILE" in e for e in rc_fifo["errors"]), "root fifo")

        real_cdir = tmp_root / "real_cdir"
        real_cdir.mkdir(parents=True, exist_ok=True)
        sym_cdir = tmp_root / "sym_cdir"
        sym_cdir.symlink_to(real_cdir)
        rc_scdir = vas.verify_root_files_and_fetch_manifest(sym_root, True, sym_cdir)
        _check(any("LIVE_CORPUS_DIR_MISSING" in e for e in rc_scdir["errors"]), "symlink corpus_dir not rejected")

        sym_study_dir = sym_root / atlas_spec["study_dir"]
        sym_study_dir.symlink_to(sdir)
        res_sdir = vas.verify_study(atlas_spec, sym_root, False, None)
        _check(res_sdir["passed"] is False and any("SYMLINK_FORBIDDEN" in e for e in res_sdir["errors"]), "study dir sym")

        sym_files_root = tmp_root / "sym_files_root"
        sf_dir = sym_files_root / atlas_spec["study_dir"]
        sf_dir.mkdir(parents=True, exist_ok=True)
        for fname in atlas_spec["expected_file_sha256"]:
            (sf_dir / fname).symlink_to(sdir / fname)
        res_sfile = vas.verify_study(atlas_spec, sym_files_root, False, None)
        _check(res_sfile["passed"] is False and any("SYMLINK_FORBIDDEN" in e for e in res_sfile["errors"]), "study file sym")

        fifo_files_root = tmp_root / "fifo_files_root"
        ff_dir = fifo_files_root / atlas_spec["study_dir"]
        ff_dir.mkdir(parents=True, exist_ok=True)
        for fname in atlas_spec["expected_file_sha256"]:
            os.mkfifo(ff_dir / fname)
        res_ffile = vas.verify_study(atlas_spec, fifo_files_root, False, None)
        _check(res_ffile["passed"] is False and any("NOT_REGULAR_FILE" in e for e in res_ffile["errors"]), "study file fifo")

        # 5c. Grandparent / ancestor symlink & size-cap & dotdot normalization checks
        real_gp = tmp_root / "real_gp"
        real_child = real_gp / "child_dir"
        real_child.mkdir(parents=True, exist_ok=True)
        (real_child / "hi.txt").write_bytes(b"hi")
        sym_gp = tmp_root / "sym_gp"
        sym_gp.symlink_to(real_gp)
        _check(vas._lstat_is_dir(sym_gp / "child_dir") is False, "grandparent symlink dir must be False")
        _check(
            vas._read_regular_nofol_bytes(sym_gp / "child_dir" / "hi.txt") == ("SYMLINK_FORBIDDEN", b""),
            "grandparent symlink file must return SYMLINK_FORBIDDEN",
        )
        _check(
            vas._read_regular_nofol_bytes(tmp_root / "no_such_parent" / "hi.txt") == ("MISSING", b""),
            "missing parent must return MISSING",
        )
        _check(
            vas._read_regular_nofol_bytes(real_child / ".." / "." / "child_dir" / "hi.txt") == (None, b"hi"),
            "dotdot norm read must succeed",
        )
        exact16 = tmp_root / "exact16.bin"
        exact16.write_bytes(b"a" * 16)
        _check(vas._read_regular_nofol_bytes(exact16, max_bytes=16) == (None, b"a" * 16), "size cap 16B exact")
        over17 = tmp_root / "over17.bin"
        over17.write_bytes(b"a" * 17)
        _check(vas._read_regular_nofol_bytes(over17, max_bytes=16) == ("FILE_TOO_LARGE", b""), "size cap 17B exceeded")
        _check(
            vas._read_regular_nofol_bytes(exact16 / "child.txt") == ("NOT_REGULAR_FILE", b""),
            "non-directory parent must return NOT_REGULAR_FILE",
        )

    # 6. Direct regression for main() failed-study & live/offline BoolOp paths
    orig_verify_root = vas.verify_root_files_and_fetch_manifest
    orig_verify_study = vas.verify_study
    orig_specs = vas.STUDY_SPECS
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
                    "supports_live_corpus_recount": False,
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
                "supports_live_corpus_recount": spec["supports_live_corpus_recount"],
                "standalone_stdout_sha256": "0" * 64,
                "cert_rc": 0,
                "live_corpus_recounted": bool(live and spec["supports_live_corpus_recount"]),
                "live_stdout_sha256": ("a" * 64) if spec["supports_live_corpus_recount"] else None,
                "live_rc": 0 if (live and spec["supports_live_corpus_recount"]) else None,
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
        _check("live_sha256=" not in out, "offline mode must not print live_sha256")

        # Root fails alone while all studies pass -> must STILL exit 1 and keep arabic_live_corpora_recounted=False
        def _all_ok_study(spec: dict[str, Any], root: Path, live: bool, cdir: Path | None) -> dict[str, Any]:
            has_lv = bool(spec["supports_live_corpus_recount"])
            return {
                "audit_id": spec["audit_id"],
                "study_dir": spec["study_dir"],
                "passed": True,
                "files_verified": 1,
                "offline_scope": "recomputed_from_scratch_pure_q",
                "recomputes_from_scratch_offline": spec["recomputes_from_scratch_offline"],
                "supports_live_corpus_recount": has_lv,
                "standalone_stdout_sha256": "b" * 64,
                "cert_rc": 0,
                "live_corpus_recounted": has_lv,
                "live_stdout_sha256": ("c" * 64) if has_lv else None,
                "live_rc": 0 if has_lv else None,
                "test_rc": 0,
                "errors": [],
            }

        vas.verify_study = _all_ok_study
        buf_rf = io.StringIO()
        with redirect_stdout(buf_rf):
            rc_rf = vas.main(["--live", "--json"])
        _check(rc_rf == 1, "root fail + studies ok must exit 1")
        j_rf = json.loads(buf_rf.getvalue())
        _check(j_rf["passed"] is False and j_rf["arabic_live_corpora_recounted"] is False, "root fail live flag")

        # Root passes, one study fails -> must exit 1 and keep arabic_live_corpora_recounted=False
        vas.verify_root_files_and_fetch_manifest = lambda root, live, cdir: {
            "passed": True,
            "root_files_verified": 3,
            "fetch_manifest_sha256": "d" * 64,
            "fetch_manifest_count": 9,
            "live_corpora_verified": 9 if live else 0,
            "errors": [],
        }
        vas.verify_study = _fake_verify_study
        buf_sf = io.StringIO()
        with redirect_stdout(buf_sf):
            rc_sf = vas.main(["--live", "--json"])
        _check(rc_sf == 1, "root ok + one study fail must exit 1")
        j_sf = json.loads(buf_sf.getvalue())
        _check(j_sf["passed"] is False and j_sf["arabic_live_corpora_recounted"] is False, "study fail live flag")

        # Both --live alone and --corpus-dir alone activate live mode; offline keeps arabic_live_corpora_recounted=False
        vas.verify_study = _all_ok_study
        buf_off_j = io.StringIO()
        with redirect_stdout(buf_off_j):
            rc_off_j = vas.main(["--json"])
        _check(rc_off_j == 0, "offline all-ok rc")
        j_off = json.loads(buf_off_j.getvalue())
        _check(j_off["arabic_live_corpora_recounted"] is False, "offline must not set arabic_live_corpora_recounted")

        buf_lv_txt = io.StringIO()
        with redirect_stdout(buf_lv_txt):
            rc_lv_txt = vas.main(["--live"])
        txt_lv = buf_lv_txt.getvalue()
        _check(rc_lv_txt == 0 and "arabic_live_corpora_recounted=true" in txt_lv, "--live text banner")
        _check("live_sha256=cccccccccccccccc live_rc=0" in txt_lv, "--live must print live_sha256 for live studies")
        _check("live_sha256=None" not in txt_lv, "--live must omit live_sha256 when None")

        buf_cd_j = io.StringIO()
        with redirect_stdout(buf_cd_j):
            rc_cd_j = vas.main(["--corpus-dir", "/nonexistent_custom_path", "--json"])
        j_cd = json.loads(buf_cd_j.getvalue())
        _check(rc_cd_j == 0 and j_cd["arabic_live_corpora_recounted"] is True, "--corpus-dir alone must enable live")

        # Vacuous empty live_studies & live_corpus_recounted=False with passed=True must both report False
        def _all_ok_unrecounted(spec: dict[str, Any], root: Path, live: bool, cdir: Path | None) -> dict[str, Any]:
            row = _all_ok_study(spec, root, live, cdir)
            row["live_corpus_recounted"] = False
            return row

        vas.verify_study = _all_ok_unrecounted
        buf_unrec = io.StringIO()
        with redirect_stdout(buf_unrec):
            rc_unrec = vas.main(["--live", "--json"])
        j_unrec = json.loads(buf_unrec.getvalue())
        _check(rc_unrec == 0 and j_unrec["arabic_live_corpora_recounted"] is False, "unrecounted live must be False")

        vas.verify_study = _all_ok_study
        vas.STUDY_SPECS = tuple(s for s in orig_specs if not s["supports_live_corpus_recount"])
        buf_vac = io.StringIO()
        with redirect_stdout(buf_vac):
            rc_vac = vas.main(["--live", "--json"])
        j_vac = json.loads(buf_vac.getvalue())
        _check(rc_vac == 0 and j_vac["arabic_live_corpora_recounted"] is False, "vacuous live_studies must be False")
    finally:
        vas.STUDY_SPECS = orig_specs
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

            # M013: manifest invalid JSON / non-dict root / non-int count (bool trap)
            for bad_js in (b'{"count": 1.5}\n', b"[1, 2]\n", b'{"count": true}\n', b'{"count": null}\n'):
                vas.EXPECTED_FETCH_MANIFEST_SHA256 = hashlib.sha256(bad_js).hexdigest()
                vas.subprocess.run = lambda cmd, b=bad_js, **kw: _FakeProc(0, b)  # type: ignore[assignment]
                r = vas.verify_root_files_and_fetch_manifest(tmp_root, False, None)
                _check(any("FETCH_MANIFEST_JSON_ERROR" in e for e in r["errors"]), f"M013 missed {bad_js!r}")

            # M015-M020: live verify-only paths (incl. non-dict root & bool count)
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

            for bad_v in (b"not-json", b"[1]\n", b'{"count": true}\n'):
                vas.subprocess.run = (  # type: ignore[assignment]
                    lambda cmd, b=bad_v, **kw: _FakeProc(0, valid_mf) if "--manifest-json" in cmd else _FakeProc(0, b)
                )
                r = vas.verify_root_files_and_fetch_manifest(tmp_root, True, corpus_dir)
                _check(any("LIVE_CORPUS_VERIFY_JSON_ERROR" in e for e in r["errors"]), f"M020 missed {bad_v!r}")

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

            # Clean live & clean offline pass (kills BoolOp on `if live and supports_live:`)
            vas.subprocess.run = _mk_runner()  # type: ignore[assignment]
            r_ok = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(r_ok["passed"] is True and r_ok["live_corpus_recounted"] is True, f"clean mock live failed: {r_ok}")
            no_exp_lv_spec = copy.deepcopy(base_spec)
            no_exp_lv_spec["expected_live_stdout_sha256"] = None
            r_no_exp = vas.verify_study(no_exp_lv_spec, tmp_root, True, corpus_dir)
            _check(r_no_exp["passed"] is True and r_no_exp["live_corpus_recounted"] is True, "expected_live_sha=None")
            r_off_ok = vas.verify_study(base_spec, tmp_root, False, None)
            _check(r_off_ok["passed"] is True and r_off_ok["live_corpus_recounted"] is False, "clean mock offline failed")

            # Live mode on a study with supports_live_corpus_recount=False must NOT invoke --corpus-dir
            off_pure_spec = copy.deepcopy(base_spec)
            off_pure_spec["recomputes_from_scratch_offline"] = True
            off_pure_spec["supports_live_corpus_recount"] = False
            off_pure_spec["expected_standalone_stdout_sha256"] = lv_sha

            def _forbid_corpus_call(cmd: list[str], **kw: Any) -> _FakeProc:
                if "--corpus-dir" in cmd:
                    _fail("supports_live_corpus_recount=False must never invoke --corpus-dir")
                return _FakeProc(0, lv_bytes if "--standalone" in cmd else b"")

            vas.subprocess.run = _forbid_corpus_call  # type: ignore[assignment]
            r_pure_lv = vas.verify_study(off_pure_spec, tmp_root, True, corpus_dir)
            _check(r_pure_lv["passed"] is True and r_pure_lv["live_corpus_recounted"] is False, "pure-q live pass")

            # M028-M029: cert_proc rc != 0
            vas.subprocess.run = _mk_runner(sa_rc=2)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, False, None)
            _check(any("CERTIFIER_NONZERO_EXIT" in e for e in r["errors"]), "M028-M029 missed")

            # M030-M031: standalone sha mismatch
            vas.subprocess.run = _mk_runner(sa_out=b'{"mode":"standalone_fixture_replay","live_corpus_recounted":false}')  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, False, None)
            _check(any("STANDALONE_SHA256_MISMATCH" in e for e in r["errors"]), "M030-M031 missed")

            # M032: standalone invalid JSON & non-dict JSON root (must NOT raise AttributeError)
            for bad_sa in (b'{"x": 0.5}\n', b"[1, 2]\n"):
                spec_bad_sa = copy.deepcopy(base_spec)
                spec_bad_sa["expected_standalone_stdout_sha256"] = hashlib.sha256(bad_sa).hexdigest()
                vas.subprocess.run = _mk_runner(sa_out=bad_sa)  # type: ignore[assignment]
                r = vas.verify_study(spec_bad_sa, tmp_root, False, None)
                _check(any("STRICT_JSON_ERROR" in e for e in r["errors"]), f"M032 missed {bad_sa!r}")

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

            # M037-M038: live missing or symlinked corpus dir
            r = vas.verify_study(base_spec, tmp_root, True, tmp_root / "absent")
            _check(any("LIVE_CORPUS_DIR_UNAVAILABLE" in e for e in r["errors"]), "M037-M038 missed")
            sym_cd2 = tmp_root / "sym_cd2"
            sym_cd2.symlink_to(corpus_dir)
            r = vas.verify_study(base_spec, tmp_root, True, sym_cd2)
            _check(any("LIVE_CORPUS_DIR_UNAVAILABLE" in e for e in r["errors"]), "symlink corpus_dir study missed")

            # M039-M040: live_proc rc != 0 MUST keep live_corpus_recounted == False
            vas.subprocess.run = _mk_runner(lv_rc=3)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(any("LIVE_CERTIFIER_NONZERO_EXIT" in e for e in r["errors"]), "M039-M040 missed")
            _check(r["live_corpus_recounted"] is False, "live_rc != 0 must keep live_corpus_recounted False")

            # M041 & M042: live sha mismatch & live bytes != committed MUST keep live_corpus_recounted == False
            alt_lv = b'{"mode":"live_corpus_recount","live_corpus_recounted":true} \n'
            vas.subprocess.run = _mk_runner(lv_out=alt_lv)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(any("LIVE_SHA256_MISMATCH" in e for e in r["errors"]), "M041 missed")
            _check(any("LIVE_STDOUT_MISMATCH_VS_COMMITTED_CERTIFICATE" in e for e in r["errors"]), "M042 missed")
            _check(r["live_corpus_recounted"] is False, "live_sha mismatch must keep live_corpus_recounted False")

            # M042 isolated (expected_live_stdout_sha256 matches alt_lv, committed differs)
            spec_m42 = copy.deepcopy(base_spec)
            spec_m42["expected_live_stdout_sha256"] = hashlib.sha256(alt_lv).hexdigest()
            vas.subprocess.run = _mk_runner(lv_out=alt_lv)  # type: ignore[assignment]
            r = vas.verify_study(spec_m42, tmp_root, True, corpus_dir)
            _check(any("LIVE_STDOUT_MISMATCH_VS_COMMITTED_CERTIFICATE" in e for e in r["errors"]), "M042 iso missed")
            _check(r["live_corpus_recounted"] is False, "committed mismatch must keep live_corpus_recounted False")

            # M043-M044: live wrong mode MUST keep live_corpus_recounted == False
            lv_wm = b'{"mode":"bad_live","live_corpus_recounted":true}\n'
            (st_dir / "cert.json").write_bytes(lv_wm)
            spec_lwm = copy.deepcopy(base_spec)
            lv_wm_sha = hashlib.sha256(lv_wm).hexdigest()
            spec_lwm["expected_live_stdout_sha256"] = lv_wm_sha
            spec_lwm["expected_file_sha256"]["cert.json"] = lv_wm_sha
            vas.subprocess.run = _mk_runner(lv_out=lv_wm)  # type: ignore[assignment]
            r = vas.verify_study(spec_lwm, tmp_root, True, corpus_dir)
            _check(any("UNEXPECTED_LIVE_MODE" in e for e in r["errors"]), "M043-M044 missed")
            _check(r["live_corpus_recounted"] is False, "wrong live mode must keep live_corpus_recounted False")

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

            # M046: live invalid JSON & non-dict JSON root (must NOT raise AttributeError)
            (st_dir / "cert.json").write_bytes(lv_bytes)
            for bad_lv_out in (b"not-json", b"[1, 2]\n"):
                vas.subprocess.run = _mk_runner(lv_out=bad_lv_out)  # type: ignore[assignment]
                r = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
                _check(any("LIVE_STRICT_JSON_ERROR" in e for e in r["errors"]), f"M046 missed {bad_lv_out!r}")
                _check(r["live_corpus_recounted"] is False, "bad live json must keep live_corpus_recounted False")

            # M047-M048: test_proc rc != 0 (including live mode resetting live_corpus_recounted -> False)
            vas.subprocess.run = _mk_runner(tst_rc=1)  # type: ignore[assignment]
            r = vas.verify_study(base_spec, tmp_root, False, None)
            _check(any("R5_TEST_NONZERO_EXIT" in e for e in r["errors"]), "M047-M048 missed")
            r_lv_tfail = vas.verify_study(base_spec, tmp_root, True, corpus_dir)
            _check(
                r_lv_tfail["passed"] is False and r_lv_tfail["live_corpus_recounted"] is False,
                "R5 test failure must reset live_corpus_recounted to False",
            )

            # Tampered fetch_corpora.py MUST NOT be executed in verify_root_files_and_fetch_manifest
            tampered_called = {"n": 0}

            def _forbid_tampered_fetch(cmd: list[str], **kw: Any) -> _FakeProc:
                tampered_called["n"] += 1
                return _FakeProc(0, valid_mf)

            vas.subprocess.run = _forbid_tampered_fetch  # type: ignore[assignment]
            bad_fetch_shas = dict(vas.ROOT_FILES_EXPECTED_SHA256)
            bad_fetch_shas["fetch_corpora.py"] = "0" * 64
            vas.ROOT_FILES_EXPECTED_SHA256 = bad_fetch_shas
            r_tampered_fetch = vas.verify_root_files_and_fetch_manifest(tmp_root, True, corpus_dir)
            _check(
                r_tampered_fetch["passed"] is False and tampered_called["n"] == 0,
                "tampered fetch_corpora.py must never be executed",
            )
        finally:
            vas.subprocess.run = orig_run
            vas.ROOT_FILES_EXPECTED_SHA256 = orig_root_shas
            vas.EXPECTED_FETCH_MANIFEST_SHA256 = orig_mf_sha

    # End-to-end relative `--corpus-dir ./rel_corpora` subprocess CWD regression test (MED-2)
    with tempfile.TemporaryDirectory() as td_rel:
        rel_root = Path(td_rel)
        rel_corpora = rel_root / "rel_corpora"
        rel_corpora.mkdir(parents=True, exist_ok=True)
        (rel_corpora / "marker.txt").write_bytes(b"ok\n")
        rel_study = rel_root / "arabic-rel-study"
        rel_study.mkdir(parents=True, exist_ok=True)
        sa_out = b'{"live_corpus_recounted": false, "mode": "standalone_fixture_replay"}\n'
        lv_out = b'{"live_corpus_recounted": true, "mode": "live_corpus_recount"}\n'
        audit_src = (
            "import os, sys\n"
            "from pathlib import Path\n"
            "if '--standalone' in sys.argv:\n"
            "    sys.stdout.write('{\"live_corpus_recounted\": false, \"mode\": \"standalone_fixture_replay\"}\\n')\n"
            "    raise SystemExit(0)\n"
            "idx = sys.argv.index('--corpus-dir')\n"
            "cdir = Path(sys.argv[idx + 1])\n"
            "if not cdir.is_absolute() or not (cdir / 'marker.txt').is_file():\n"
            "    raise SystemExit(1)\n"
            "sys.stdout.write('{\"live_corpus_recounted\": true, \"mode\": \"live_corpus_recount\"}\\n')\n"
        ).encode("utf-8")
        test_src = b"raise SystemExit(0)\n"
        (rel_study / "audit.py").write_bytes(audit_src)
        (rel_study / "test.py").write_bytes(test_src)
        (rel_study / "cert.json").write_bytes(lv_out)
        rel_spec: dict[str, Any] = {
            "audit_id": "REL-LIVE",
            "study_dir": "arabic-rel-study",
            "cert_script": "audit.py",
            "cert_args": ["--standalone"],
            "test_script": "test.py",
            "committed_certificate_file": "cert.json",
            "recomputes_from_scratch_offline": False,
            "supports_live_corpus_recount": True,
            "expected_standalone_stdout_sha256": hashlib.sha256(sa_out).hexdigest(),
            "expected_live_stdout_sha256": hashlib.sha256(lv_out).hexdigest(),
            "expected_file_sha256": {
                "audit.py": hashlib.sha256(audit_src).hexdigest(),
                "cert.json": hashlib.sha256(lv_out).hexdigest(),
                "test.py": hashlib.sha256(test_src).hexdigest(),
            },
        }
        # Direct verify_study with relative Path("rel_corpora") from unrelated CWD
        r_rel_direct = vas.verify_study(rel_spec, rel_root, True, Path("rel_corpora"))
        _check(
            r_rel_direct["passed"] is True and r_rel_direct["live_corpus_recounted"] is True,
            f"relative corpus_dir verify_study failed: {r_rel_direct}",
        )
        # CLI main(["--live", "--corpus-dir", "./rel_corpora", "--json"]) from rel_root
        orig_cwd = os.getcwd()
        orig_repo = vas.REPO_ROOT
        orig_specs2 = vas.STUDY_SPECS
        orig_vroot2 = vas.verify_root_files_and_fetch_manifest
        try:
            os.chdir(rel_root)
            vas.REPO_ROOT = rel_root
            vas.STUDY_SPECS = (rel_spec,)
            vas.verify_root_files_and_fetch_manifest = lambda root, live, cdir: {  # type: ignore[assignment]
                "passed": bool(cdir is not None and cdir.is_absolute() and (cdir / "marker.txt").is_file()),
                "root_files_verified": 3,
                "fetch_manifest_sha256": "0" * 64,
                "fetch_manifest_count": 9,
                "live_corpora_verified": 9,
                "errors": [],
            }
            buf_cli = io.StringIO()
            with redirect_stdout(buf_cli):
                rc_cli = vas.run_cli(["--live", "--corpus-dir", "./rel_corpora", "--json"])
            parsed_cli = vas.parse_strict_zero_float_json(buf_cli.getvalue().encode("utf-8"))
            _check(
                rc_cli == 0 and parsed_cli["arabic_live_corpora_recounted"] is True,
                f"CLI relative --corpus-dir failed: rc={rc_cli} out={parsed_cli}",
            )
            # Also exercise run_cli BrokenPipeError (in-process + real closed pipe EPIPE) and OSError handlers
            orig_main_fn = vas.main
            try:
                saved_fd1 = os.dup(1)
                try:
                    vas.main = lambda argv=None: (_ for _ in ()).throw(BrokenPipeError())  # type: ignore[assignment]
                    _check(vas.run_cli([]) == 2, "run_cli BrokenPipeError must return 2")
                finally:
                    os.dup2(saved_fd1, 1)
                    os.close(saved_fd1)
                vas.main = lambda argv=None: (_ for _ in ()).throw(OSError("disk err"))  # type: ignore[assignment]
                err_buf = io.StringIO()
                orig_stderr = sys.stderr
                try:
                    sys.stderr = err_buf
                    rc_os = vas.run_cli([])
                finally:
                    sys.stderr = orig_stderr
                _check(
                    rc_os == 2 and "BAYT_AL_HIKMA_RUNTIME_ERROR" in err_buf.getvalue(),
                    "run_cli OSError must return 2 and log BAYT_AL_HIKMA_RUNTIME_ERROR",
                )
            finally:
                vas.main = orig_main_fn
        finally:
            os.chdir(orig_cwd)
            vas.REPO_ROOT = orig_repo
            vas.STUDY_SPECS = orig_specs2
            vas.verify_root_files_and_fetch_manifest = orig_vroot2

    # Real subprocess closed-pipe EPIPE check on run_cli (kills flush & dup2(devnull, 1) mutants, 0 stderr, RC=2)
    r_fd, w_fd = os.pipe()
    os.close(r_fd)
    ep_proc = vas.subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import sys; sys.path.insert(0, '.'); import verify_all_standalone as v; "
            "v.main = lambda a=None: (print('small-buffered-line'), 0)[1]; raise SystemExit(v.run_cli([]))",
        ],
        cwd=str(vas.REPO_ROOT),
        stdout=w_fd,
        stderr=vas.subprocess.PIPE,
    )
    os.close(w_fd)
    _, ep_err = ep_proc.communicate(timeout=15)
    _check(
        ep_proc.returncode == 2 and ep_err == b"",
        f"run_cli live EPIPE failed: rc={ep_proc.returncode} err={ep_err!r}",
    )


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
