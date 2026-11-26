#!/usr/bin/env python3
"""Assertion-free R5 adversarial verification & 100% mutation/BoolOp suite for verify_pilot1_theorems.py."""

from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import io
import json
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

import socratic_operator_seminar as sos  # noqa: E402
import verify_pilot1_theorems as mod  # noqa: E402


class TestPilot1TheoremsR5(unittest.TestCase):
    def _assert_err(self, code: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(mod.Pilot1Error) as cm:
            fn(*args, **kwargs)
        self.assertEqual(cm.exception.code, code)

    def test_01_ast_pure_zq_and_primitive_guards(self) -> None:
        res = sos.verify_pure_q_ast(Path(mod.__file__).read_text(encoding="utf-8"))
        self.assertTrue(res["pure_q_ast_clean"])

        self.assertEqual(mod.check_int(0, "x"), 0)
        self.assertEqual(mod.check_int(-mod.MAX_INT_ABS, "x"), -mod.MAX_INT_ABS)
        self.assertEqual(mod.check_int(mod.MAX_INT_ABS, "x"), mod.MAX_INT_ABS)
        for bad in (True, 1.5, "1", mod.MAX_INT_ABS + 1, -(mod.MAX_INT_ABS + 1)):
            self._assert_err("BAD_INT", mod.check_int, bad, "x")

        self.assertEqual(mod.check_pos_int(1, "p"), 1)
        for bad in (0, -2):
            self._assert_err("BAD_POS_INT", mod.check_pos_int, bad, "p")

        self.assertEqual(mod.qdiv(Fraction(3, 4), Fraction(5, 2)), Fraction(3, 10))
        self._assert_err("QDIV_ZERO_DENOM", mod.qdiv, Fraction(1, 1), Fraction(0, 1))
        self.assertEqual(mod.frac_str(Fraction(3, 7)), "3/7")

    def test_02_t1_fricke_signature_and_guards(self) -> None:
        t1 = mod.certify_t1_fricke_signature_unified()
        self.assertTrue(t1["passed"])
        self.assertEqual(t1["definite_hurwitz_odd_d1"]["D"], 1)
        self.assertEqual(t1["definite_hurwitz_odd_d1"]["F_cleared"], 7048)
        self.assertEqual(t1["definite_lipschitz_d2"]["F_cleared"], 14080)
        self.assertTrue(t1["definite_so3_kernel_ij"]["so3_invisible_kernel"])
        self.assertEqual(t1["split_5_3"]["kappa"], -41)
        self.assertEqual(t1["split_5_3"]["overshoot"], 144)
        self.assertTrue(t1["split_8_3_palindromic"]["palindromic"])

        for bad_a, bad_b in (
            ({0: 1, 1: 1, 2: 1, 3: 1}, (2, 0, 0, 0)),
            ((2, 0, 0), (2, 0, 0, 0)),
            ((2, 0, 0, 0), {0: 1, 1: 1, 2: 1, 3: 1}),
            ((2, 0, 0, 0), (2, 0, 0)),
        ):
            self._assert_err("BAD_QUAT", mod.verify_fricke_definite, bad_a, bad_b)
        for bad_a, bad_b in (((1, 2, 0, 0), (2, 0, 0, 0)), ((2, 0, 0, 0), (1, 2, 0, 0))):
            self._assert_err("BAD_HURWITZ_PARITY", mod.verify_fricke_definite, bad_a, bad_b)
        for bad_a, bad_b in (((0, 0, 0, 0), (2, 0, 0, 0)), ((2, 0, 0, 0), (0, 0, 0, 0))):
            self._assert_err("ZERO_QUAT", mod.verify_fricke_definite, bad_a, bad_b)
        self._assert_err("NOT_COPRIME", mod.verify_fricke_split, 6, 4)

    def test_03_t2_crt_valve_seal_and_guards(self) -> None:
        t2 = mod.certify_t2_crt_valve_seal()
        self.assertTrue(t2["passed"])
        self.assertEqual(t2["r2_seat6_repaired_witness"]["root"], 15)
        self.assertEqual(t2["noncoprime_crt_witness"]["root"], 13)
        self.assertFalse(t2["r1_inconsistent_refutation"]["solvable"])
        self.assertFalse(t2["noncoprime_stride_refutation"]["stride_single_cycle"])
        self.assertEqual(t2["tight_rational_band_witness"]["root"], 123)

        self._assert_err("LCM_TOO_LARGE", mod.verify_crt_valve_seal, [mod.MAX_CRT_LCM + 1], [0], 1, [], (0, 1), (1, 1), 0)
        ok_max = mod.verify_crt_valve_seal([mod.MAX_CRT_LCM], [0], 2, [], (0, 1), (1, 1), 0)
        self.assertFalse(ok_max["stride_single_cycle"])

        for bad_m, bad_r in (({0: 3}, [0]), ([], []), ([3], {0: 0}), ([3, 5], [0])):
            self._assert_err("BAD_CRT", mod.verify_crt_valve_seal, bad_m, bad_r, 1, [(0, 1)], (0, 1), (1, 1), 0)
        for bad_init in (True, 2, -1):
            self._assert_err("BAD_INIT", mod.verify_crt_valve_seal, [3], [0], 1, [(0, 1)] * 3, (0, 1), (1, 1), bad_init)
        self._assert_err("BAD_BAND", mod.verify_crt_valve_seal, [3], [0], 1, [(0, 1)] * 3, (1, 1), (1, 1), 0)
        for bad_lv in ({0: (0, 1), 1: (0, 1), 2: (0, 1)}, [(0, 1)]):
            self._assert_err("BAD_LEVELS", mod.verify_crt_valve_seal, [3], [0], 1, bad_lv, (0, 1), (1, 1), 0)

        with mock.patch.object(mod, "_egcd", return_value=(1, 0, 0)):
            self._assert_err("CRT_FOLD_MISMATCH", mod.verify_crt_valve_seal, [2, 3], [1, 2], 1, [(0, 1)] * 6, (0, 1), (1, 1), 0)

    def test_04_t3_schur_witt_fold_mirror_and_guards(self) -> None:
        t3 = mod.certify_t3_unified_schur_witt_fold()
        self.assertTrue(t3["passed"])
        self.assertTrue(t3["block_drop_refutation_3334"]["block_drop_1x1_q_congruent"])
        self.assertTrue(t3["explicit_q_witness_3334_verified"])
        self.assertTrue(t3["mirror_billiard_2_3_refutation"]["single_shear_false_at_coprime"])

        self.assertTrue(mod.verify_schur_block_system([[0, 1], [1, 0]], [[1], [1]], [[0]])["q_congruence_exact"])
        self.assertTrue(mod.verify_schur_block_system([[1]], [[0]], [[0]])["block_drop_1x1_q_congruent"])
        self.assertFalse(mod.verify_schur_block_system([[1]], [[1]], [[1]])["block_drop_1x1_q_congruent"])
        m2_res = mod.verify_schur_block_system([[1]], [[1, 0]], [[2, 0], [0, 3]])
        self.assertTrue(m2_res["q_congruence_exact"])
        self.assertFalse(m2_res["block_drop_1x1_q_congruent"])

        self.assertFalse(mod._is_rational_square(Fraction(-1, 4)))
        self.assertTrue(mod._is_rational_square(Fraction(0, 1)))
        self.assertTrue(mod._is_rational_square(Fraction(9, 16)))
        self.assertFalse(mod._is_rational_square(Fraction(2, 9)))
        self.assertFalse(mod._is_rational_square(Fraction(9, 2)))

        for bad_a, bad_b, bad_d in (
            ({0: [1]}, [[1]], [[1]]),
            ([], [], [[1]]),
            ([[1]], [[1]], {0: [1]}),
            ([[1]], [[1]], []),
            ([[1]], {0: [1]}, [[1]]),
            ([[1]], [[1], [2]], [[1]]),
        ):
            self._assert_err("BAD_BLOCK", mod.verify_schur_block_system, bad_a, bad_b, bad_d)
        self._assert_err("SINGULAR_PIVOT", mod.verify_schur_block_system, [[0]], [[1]], [[1]])

        self.assertFalse(mod.verify_mirror_billiard(1, 3)["single_shear_false_at_coprime"])
        m_4_6 = mod.verify_mirror_billiard(4, 6)
        self.assertEqual(m_4_6["curves"], 2)
        self.assertFalse(m_4_6["single_shear_false_at_coprime"])
        self.assertEqual(mod.verify_mirror_billiard(1, mod.MAX_MIRROR_DIM)["curves"], 1)
        self.assertEqual(mod.verify_mirror_billiard(mod.MAX_MIRROR_DIM, 1)["curves"], 1)
        for bad_p, bad_q in ((mod.MAX_MIRROR_DIM + 1, 1), (1, mod.MAX_MIRROR_DIM + 1)):
            self._assert_err("MIRROR_TOO_LARGE", mod.verify_mirror_billiard, bad_p, bad_q)

    def test_05_transcripts_certificate_tamper_and_cli(self) -> None:
        cert = mod.build_certificate(SEMINAR_DIR)
        mod.validate_certificate_payload(cert)
        self.assertTrue(cert["all_passed"])
        self.assertEqual(cert["pilot1_transcripts"]["total_turns"], 63)
        self.assertEqual(cert["pilot1_transcripts"]["total_pass_witness"], 51)
        self.assertEqual(cert["pilot1_transcripts"]["total_repairs"], 20)
        self.assertEqual(cert["pilot1_transcripts"]["total_cross_seat_compositions"], 30)

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            self._assert_err("PILOT1_MISSING", mod.verify_pilot1_transcripts, tmp_dir)

            pt = tmp_dir.joinpath("pilot1_transcripts")
            pt.mkdir()
            shutil.copy(SEMINAR_DIR.joinpath("pilot1_transcripts/topic1_continuum_session.json"), pt.joinpath("topic1_continuum_session.json"))
            self._assert_err("PILOT1_MISSING", mod.verify_pilot1_transcripts, tmp_dir)

            # Symlink rejection on both session and turns
            sym_t = pt.joinpath("topic1_continuum_turns.json")
            sym_t.symlink_to(SEMINAR_DIR.joinpath("pilot1_transcripts/topic1_continuum_turns.json"))
            self._assert_err("SYMLINK_FORBIDDEN", mod.verify_pilot1_transcripts, tmp_dir)
            sym_t.unlink()
            pt.joinpath("topic1_continuum_session.json").unlink()
            pt.joinpath("topic1_continuum_session.json").symlink_to(SEMINAR_DIR.joinpath("pilot1_transcripts/topic1_continuum_session.json"))
            shutil.copy(SEMINAR_DIR.joinpath("pilot1_transcripts/topic1_continuum_turns.json"), pt.joinpath("topic1_continuum_turns.json"))
            self._assert_err("SYMLINK_FORBIDDEN", mod.verify_pilot1_transcripts, tmp_dir)
            pt.joinpath("topic1_continuum_session.json").unlink()
            shutil.copy(SEMINAR_DIR.joinpath("pilot1_transcripts/topic1_continuum_session.json"), pt.joinpath("topic1_continuum_session.json"))

            # Raw SHA mismatch on session & turns
            shutil.copy(SEMINAR_DIR.joinpath("pilot1_transcripts/topic1_continuum_turns.json"), pt.joinpath("topic1_continuum_turns.json"))
            orig_s = pt.joinpath("topic1_continuum_session.json").read_bytes()
            orig_t = pt.joinpath("topic1_continuum_turns.json").read_bytes()
            pt.joinpath("topic1_continuum_session.json").write_bytes(orig_s + b"\n")
            self._assert_err("INPUT_SHA_MISMATCH", mod.verify_pilot1_transcripts, tmp_dir)
            pt.joinpath("topic1_continuum_session.json").write_bytes(orig_s)
            pt.joinpath("topic1_continuum_turns.json").write_bytes(orig_t + b"\n")
            self._assert_err("INPUT_SHA_MISMATCH", mod.verify_pilot1_transcripts, tmp_dir)

            # Strict JSON error propagation via mocked raw SHA
            bad_json_bytes = b'{"a":1,"a":2}\n'
            pt.joinpath("topic1_continuum_session.json").write_bytes(bad_json_bytes)
            pt.joinpath("topic1_continuum_turns.json").write_bytes(orig_t)
            fake_dup = ((
                "topic1_continuum",
                "pilot1_transcripts/topic1_continuum_session.json",
                "pilot1_transcripts/topic1_continuum_turns.json",
                hashlib.sha256(bad_json_bytes).hexdigest(),
                hashlib.sha256(orig_t).hexdigest(),
                "0" * 64,
                16, 5, 5, 9, 2, 3,
            ),)
            with mock.patch.object(mod, "PILOT1_EXPECTED_SESSIONS", fake_dup):
                self._assert_err("DUPLICATE_JSON_KEY", mod.verify_pilot1_transcripts, tmp_dir)

            # Bad transcript_sha256 (left BoolOp arm) & rehashed-wrong-expected (right BoolOp arm) & metric mismatch
            s_obj = json.loads(orig_s.decode("utf-8"))
            s_bad = copy.deepcopy(s_obj)
            s_bad["transcript_sha256"] = "0" * 64
            sb_bytes = (json.dumps(s_bad) + "\n").encode("utf-8")
            pt.joinpath("topic1_continuum_session.json").write_bytes(sb_bytes)
            fake_bad_tx = ((
                "topic1_continuum",
                "pilot1_transcripts/topic1_continuum_session.json",
                "pilot1_transcripts/topic1_continuum_turns.json",
                hashlib.sha256(sb_bytes).hexdigest(),
                hashlib.sha256(orig_t).hexdigest(),
                s_obj["transcript_sha256"],
                16, 5, 5, 9, 2, 3,
            ),)
            with mock.patch.object(mod, "PILOT1_EXPECTED_SESSIONS", fake_bad_tx):
                self._assert_err("TRANSCRIPT_SHA_MISMATCH", mod.verify_pilot1_transcripts, tmp_dir)

            s_rehash = copy.deepcopy(s_obj)
            s_rehash["turn_count"] = 20
            b = {k: v for k, v in s_rehash.items() if k != "transcript_sha256"}
            s_rehash["transcript_sha256"] = hashlib.sha256(sos.canonical_json_bytes(b)).hexdigest()
            sr_bytes = (json.dumps(s_rehash) + "\n").encode("utf-8")
            pt.joinpath("topic1_continuum_session.json").write_bytes(sr_bytes)
            fake_wrong_exp = ((
                "topic1_continuum",
                "pilot1_transcripts/topic1_continuum_session.json",
                "pilot1_transcripts/topic1_continuum_turns.json",
                hashlib.sha256(sr_bytes).hexdigest(),
                hashlib.sha256(orig_t).hexdigest(),
                s_obj["transcript_sha256"],
                16, 5, 5, 9, 2, 3,
            ),)
            with mock.patch.object(mod, "PILOT1_EXPECTED_SESSIONS", fake_wrong_exp):
                self._assert_err("TRANSCRIPT_SHA_MISMATCH", mod.verify_pilot1_transcripts, tmp_dir)

            fake_metric = ((
                "topic1_continuum",
                "pilot1_transcripts/topic1_continuum_session.json",
                "pilot1_transcripts/topic1_continuum_turns.json",
                hashlib.sha256(sr_bytes).hexdigest(),
                hashlib.sha256(orig_t).hexdigest(),
                s_rehash["transcript_sha256"],
                16, 5, 5, 9, 2, 3,
            ),)
            with mock.patch.object(mod, "PILOT1_EXPECTED_SESSIONS", fake_metric):
                self._assert_err("PILOT1_METRIC_MISMATCH", mod.verify_pilot1_transcripts, tmp_dir)

            # Non-list turns triggers right side of isinstance(t_obj, list) and len(t_obj) == 21
            t_dict = b'{"0":1,"1":1,"2":1,"3":1,"4":1,"5":1,"6":1,"7":1,"8":1,"9":1,"10":1,"11":1,"12":1,"13":1,"14":1,"15":1,"16":1,"17":1,"18":1,"19":1,"20":1}\n'
            pt.joinpath("topic1_continuum_session.json").write_bytes(orig_s)
            pt.joinpath("topic1_continuum_turns.json").write_bytes(t_dict)
            fake_tdict = ((
                "topic1_continuum",
                "pilot1_transcripts/topic1_continuum_session.json",
                "pilot1_transcripts/topic1_continuum_turns.json",
                hashlib.sha256(orig_s).hexdigest(),
                hashlib.sha256(t_dict).hexdigest(),
                s_obj["transcript_sha256"],
                16, 5, 5, 9, 2, 3,
            ),)
            with mock.patch.object(mod, "PILOT1_EXPECTED_SESSIONS", fake_tdict):
                self._assert_err("PILOT1_METRIC_MISMATCH", mod.verify_pilot1_transcripts, tmp_dir)

        # Certificate tamper refusals
        self._assert_err("BAD_CERT_TYPE", mod.validate_certificate_payload, [])
        bad_flt = copy.deepcopy(cert)
        bad_flt["zero_floats"] = 1.5
        self._assert_err("FLOAT_FORBIDDEN", mod.validate_certificate_payload, bad_flt)
        bad_k = copy.deepcopy(cert)
        bad_k["extra"] = 1
        self._assert_err("BAD_CERT_KEYS", mod.validate_certificate_payload, bad_k)
        bad_poll = copy.deepcopy(cert)
        bad_poll["t1_fricke_signature_unified"]["gate"] = "used " + "clau" + "de"
        self._assert_err("MODEL_POLLUTION", mod.validate_certificate_payload, bad_poll)

        for field, val, code in (
            ("schema", "wrong", "BAD_SCHEMA"),
            ("energy_power_status", "CLAIMED", "BAD_ENERGY"),
            ("zero_floats", False, "BAD_ZERO_FLOATS"),
            ("pure_q_ast_clean", False, "BAD_AST_FLAG"),
            ("all_passed", False, "GATES_NOT_ALL_PASSED"),
            ("payload_sha256", 123, "PAYLOAD_SHA_MISMATCH"),
            ("payload_sha256", "0" * 64, "PAYLOAD_SHA_MISMATCH"),
            ("certificate_sha256", 123, "CERT_SHA_MISMATCH"),
            ("certificate_sha256", "0" * 64, "CERT_SHA_MISMATCH"),
        ):
            t = copy.deepcopy(cert)
            t[field] = val
            self._assert_err(code, mod.validate_certificate_payload, t)

        # CLI standalone, write, check, bad JSON check, forged mismatch, missing file rc=2
        with tempfile.TemporaryDirectory() as tmp:
            tp = Path(tmp)
            cp = tp.joinpath("cert.json")
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                self.assertEqual(mod.main(["--seminar-dir", str(SEMINAR_DIR), "--standalone"]), 0)
            self.assertEqual(json.loads(buf.getvalue())["certificate_sha256"], cert["certificate_sha256"])

            buf_w = io.StringIO()
            with mock.patch("sys.stdout", buf_w):
                self.assertEqual(mod.main(["--seminar-dir", str(SEMINAR_DIR), "--write", str(cp)]), 0)
            self.assertEqual(json.loads(buf_w.getvalue())["status"], "WRITTEN")

            buf_c = io.StringIO()
            with mock.patch("sys.stdout", buf_c):
                self.assertEqual(mod.main(["--seminar-dir", str(SEMINAR_DIR), "--check", str(cp)]), 0)
            self.assertEqual(json.loads(buf_c.getvalue())["status"], "PASS")

            sym_cp = tp.joinpath("sym_cert.json")
            sym_cp.symlink_to(cp)
            self._assert_err("SYMLINK_FORBIDDEN", mod.check_certificate_file, sym_cp, SEMINAR_DIR)
            err_sw = io.StringIO()
            with mock.patch("sys.stderr", err_sw):
                self.assertEqual(mod.main(["--seminar-dir", str(SEMINAR_DIR), "--write", str(sym_cp)]), 2)
            self.assertIn("SYMLINK_FORBIDDEN", err_sw.getvalue())

            bad_p = tp.joinpath("bad.json")
            bad_p.write_text('{"a":1,"a":2}\n', encoding="utf-8")
            self._assert_err("DUPLICATE_JSON_KEY", mod.check_certificate_file, bad_p, SEMINAR_DIR)

            forged = copy.deepcopy(cert)
            forged["pilot1_transcripts"]["total_turns"] = 99
            p = {k: v for k, v in forged.items() if k not in ("payload_sha256", "certificate_sha256")}
            forged["payload_sha256"] = hashlib.sha256(sos.canonical_json_bytes(p)).hexdigest()
            b = {k: v for k, v in forged.items() if k != "certificate_sha256"}
            forged["certificate_sha256"] = hashlib.sha256(sos.canonical_json_bytes(b)).hexdigest()
            fp = tp.joinpath("forged.json")
            fp.write_text(json.dumps(forged) + "\n", encoding="utf-8")
            self._assert_err("LIVE_RECOMPUTE_MISMATCH", mod.check_certificate_file, fp, SEMINAR_DIR)

            err = io.StringIO()
            with mock.patch("sys.stderr", err):
                self.assertEqual(mod.main(["--seminar-dir", str(SEMINAR_DIR), "--check", str(tp.joinpath("missing.json"))]), 2)
            self.assertIn("MISSING_CERT", err.getvalue())

            # MED-2: symlinked script invocation & sos.SeminarError / OSError wrapping must exit RC=2 with JSON, zero tracebacks
            sym_script = tp.joinpath("sym_pilot1.py")
            sym_script.symlink_to(SEMINAR_DIR.joinpath("verify_pilot1_theorems.py"))
            for cli_args in (["--standalone"], ["--check", str(cp)]):
                proc = subprocess.run(
                    [sys.executable, "-I", "-B", str(sym_script), *cli_args],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 2)
                self.assertNotIn("Traceback", proc.stderr)
                self.assertEqual(json.loads(proc.stderr)["error_code"], "SYMLINK_FORBIDDEN")

            with mock.patch.object(sos, "verify_pure_q_ast", side_effect=sos.SeminarError("AST_FORBIDDEN_NAME", "x")):
                self._assert_err("AST_FORBIDDEN_NAME", mod.build_certificate, SEMINAR_DIR)
            with mock.patch.object(sos, "read_regular_file_bytes", return_value=b"\xff\xfe"):
                self._assert_err("BAD_UTF8", mod.build_certificate, SEMINAR_DIR)
            with mock.patch.object(sos, "canonical_json_bytes", side_effect=sos.SeminarError("JSON_DEPTH", "deep")):
                self._assert_err("JSON_DEPTH", mod._canonical_json_bytes, {"a": 1})
            with mock.patch.object(mod, "build_certificate", side_effect=sos.SeminarError("SYMLINK_FORBIDDEN", "sym")):
                err_sos = io.StringIO()
                with mock.patch("sys.stderr", err_sos):
                    self.assertEqual(mod.main(["--seminar-dir", str(SEMINAR_DIR), "--standalone"]), 2)
                self.assertEqual(json.loads(err_sos.getvalue())["error_code"], "SYMLINK_FORBIDDEN")
            with mock.patch.object(mod, "build_certificate", return_value=cert):
                err_io = io.StringIO()
                with mock.patch("sys.stderr", err_io):
                    self.assertEqual(mod.main(["--seminar-dir", str(SEMINAR_DIR), "--write", str(tp.joinpath("missing_dir", "c.json"))]), 2)
                self.assertEqual(json.loads(err_io.getvalue())["error_code"], "IO_ERROR")

            self.assertEqual(mod.default_seminar_dir(), SEMINAR_DIR)


if __name__ == "__main__":
    unittest.main()
