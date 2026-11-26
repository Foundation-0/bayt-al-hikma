#!/usr/bin/env python3
"""Assertion-free R5 adversarial verification & 100% mutation/BoolOp suite for verify_ablation_scorecard.py."""

from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SEMINAR_DIR = Path(__file__).resolve().parent.parent
if str(SEMINAR_DIR) not in sys.path:
    sys.path.insert(0, str(SEMINAR_DIR))

import socratic_operator_seminar as sos  # noqa: E402
import verify_ablation_scorecard as sc  # noqa: E402


class TestAblationScorecardR5(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cert = sc.build_scorecard_certificate(SEMINAR_DIR)
        cls.pm_doc = sos.loads_strict_json_bytes(
            SEMINAR_DIR.joinpath(sc.PROVENANCE_REL_PATH).read_bytes(),
            "provenance_map.json",
        )

    def _assert_err(self, expected_code: str, fn, *args, **kwargs) -> None:
        with self.assertRaises(sc.AblationScorecardError) as ctx:
            fn(*args, **kwargs)
        self.assertEqual(ctx.exception.code, expected_code)

    def test_01_ast_pure_zq_and_primitive_guards(self) -> None:
        res = sos.verify_pure_q_ast(SEMINAR_DIR.joinpath("verify_ablation_scorecard.py").read_text(encoding="utf-8"))
        self.assertTrue(res["pure_q_ast_clean"])

        self.assertEqual(sc.check_int(0, "z"), 0)
        self.assertEqual(sc.check_int(sc.MAX_INT_ABS, "hi"), sc.MAX_INT_ABS)
        self.assertEqual(sc.check_int(-sc.MAX_INT_ABS, "lo"), -sc.MAX_INT_ABS)
        self._assert_err("BAD_INT", sc.check_int, True, "b")
        self._assert_err("BAD_INT", sc.check_int, sc.MAX_INT_ABS + 1, "over")
        self._assert_err("BAD_INT", sc.check_int, -sc.MAX_INT_ABS - 1, "under")
        self.assertEqual(sc.frac_str(Fraction(3, 7)), "3/7")

    def test_02_live_5arm_scorecard_exact_values(self) -> None:
        c = self.cert
        self.assertTrue(c["all_passed"])
        self.assertTrue(c["zero_floats"])
        self.assertTrue(c["pure_q_ast_clean"])
        self.assertEqual(c["arm_count"], 5)
        self.assertEqual(c["matched_turn_budget_per_arm"], 21)
        self.assertEqual(c["total_refereed_turns"], 105)
        self.assertEqual(len(c["input_manifest_sha256"]), 7)
        self.assertEqual(c["energy_power_status"], "UNCONTROLLED_LAPTOP_NOT_CLAIMED")

        by_id = {a["arm_id"]: a for a in c["arms"]}
        self.assertEqual(set(by_id.keys()), {"Arm_A_plus", "Arm_A_minus", "Arm_B_plus", "Arm_C_plus", "Arm_D_single"})

        expected_rows = {
            "Arm_A_plus": ("16/21", "5/21", 5, "1/1", 9, "9/14", 14, "2/3", 15, "5/7", 2, 3, True, True, True, (3, 7, 7, 7, 6, 7, "6/7"), False),
            "Arm_A_minus": ("6/7", "1/7", 7, "7/3", 9, "3/5", 16, "16/21", 0, "0/1", 0, 0, True, False, False, (6, 6, 4, 6, 8, 9, "8/9"), True),
            "Arm_B_plus": ("6/7", "1/7", 4, "4/3", 9, "9/14", 13, "13/21", 12, "4/7", 1, 0, True, False, False, (7, 7, 6, 7, 5, 7, "5/7"), True),
            "Arm_C_plus": ("6/7", "1/7", 3, "1/1", 9, "9/14", 12, "4/7", 12, "4/7", 2, 0, True, False, False, (7, 7, 6, 7, 5, 7, "5/7"), True),
            "Arm_D_single": ("19/21", "2/21", 7, "7/2", 0, "0/1", 7, "1/3", 0, "0/1", 0, 0, True, False, False, (5, 7, 7, 7, 7, 7, "1/1"), True),
        }
        for aid, (pr, cr, rep, rpc, xs, xsr, comp, cpt, it, ipt, h2m, m2h, g2, g5, struct_ok, rb, prov_ok) in expected_rows.items():
            row = by_id[aid]
            self.assertEqual(row["pass_rate_q"], pr)
            self.assertEqual(row["cex_rate_q"], cr)
            self.assertEqual(row["counterexample_repairs_count"], rep)
            self.assertEqual(row["repairs_per_cex_q"], rpc)
            self.assertEqual(row["cross_seat_compositions_count"], xs)
            self.assertEqual(row["cross_seat_edge_rate_q"], xsr)
            self.assertEqual(row["compounding_links_count"], comp)
            self.assertEqual(row["compounding_per_turn_q"], cpt)
            self.assertEqual(row["epistemic_web_interpositions_count"], it)
            self.assertEqual(row["interpositions_per_turn_q"], ipt)
            self.assertEqual(row["historical_to_modern_count"], h2m)
            self.assertEqual(row["modern_to_historical_count"], m2h)
            self.assertEqual(row["dynamic_compounding_passed"], g2)
            self.assertEqual(row["bidirectional_pollination_passed"], g5)
            self.assertEqual(row["passes_all_structural_gates"], struct_ok)
            self.assertEqual(
                (
                    row["round_breakdown"]["r1_pass"],
                    row["round_breakdown"]["r1_total"],
                    row["round_breakdown"]["r2_pass"],
                    row["round_breakdown"]["r2_total"],
                    row["round_breakdown"]["r3_pass"],
                    row["round_breakdown"]["r3_total"],
                    row["round_breakdown"]["r3_pass_rate_q"],
                ),
                rb,
            )
            self.assertEqual(row["routing_covariates"]["provenance_available"], prov_ok)
            self.assertEqual(row["max_dag_depth"], 3)
            self.assertTrue(row["live_referee_exact_match"])
            self.assertTrue(row["public_text_hygiene_verified"])

        self.assertIs(by_id["Arm_C_plus"]["label_strip_verified"], True)
        self.assertIsNone(by_id["Arm_A_plus"]["label_strip_verified"])
        self.assertEqual(by_id["Arm_A_plus"]["turns_file_sha256"], sc.ARM_SPECS[0][7])
        self.assertIsNone(by_id["Arm_B_plus"]["turns_file_sha256"])

        a_m_cov = by_id["Arm_A_minus"]["routing_covariates"]
        self.assertEqual(a_m_cov["fallback_turns_count"], 7)
        self.assertEqual(a_m_cov["cross_route_fallback_turns_count"], 7)
        self.assertEqual(a_m_cov["same_route_retry_turns_count"], 0)
        self.assertEqual(a_m_cov["fallback_rate_q"], "1/3")
        self.assertEqual(a_m_cov["first_try_success_rate_q"], "2/3")
        self.assertEqual(a_m_cov["total_attempts_count"], 29)
        self.assertEqual(a_m_cov["failed_attempts_count"], 8)
        self.assertEqual(a_m_cov["distinct_route_count"], 9)
        self.assertEqual(a_m_cov["elapsed_ok_ms"], 2421270)
        self.assertEqual(a_m_cov["elapsed_total_ms"], 4194880)
        self.assertEqual(a_m_cov["mean_ok_ms_q"], "807090/7")

        d_cov = by_id["Arm_D_single"]["routing_covariates"]
        self.assertEqual(d_cov["fallback_turns_count"], 2)
        self.assertEqual(d_cov["cross_route_fallback_turns_count"], 0)
        self.assertEqual(d_cov["same_route_retry_turns_count"], 2)
        self.assertEqual(d_cov["fallback_rate_q"], "2/21")
        self.assertEqual(d_cov["first_try_success_rate_q"], "19/21")
        self.assertEqual(d_cov["total_attempts_count"], 23)
        self.assertEqual(d_cov["failed_attempts_count"], 2)
        self.assertEqual(d_cov["distinct_route_count"], 1)
        self.assertEqual(d_cov["elapsed_ok_ms"], 2095120)
        self.assertEqual(d_cov["elapsed_total_ms"], 2459920)
        self.assertEqual(d_cov["mean_ok_ms_q"], "2095120/21")

        ct = c["pairwise_contrasts_q"]
        self.assertEqual(ct["chair_effect_a_plus_minus_a_minus"]["pass_rate_delta_q"], "-2/21")
        self.assertEqual(ct["chair_effect_a_plus_minus_a_minus"]["interpositions_delta"], 15)
        self.assertTrue(ct["chair_effect_a_plus_minus_a_minus"]["bidirectional_gained"])
        self.assertEqual(ct["scholars_vs_civilizations_a_plus_minus_b_plus"]["interpositions_delta"], 3)
        self.assertTrue(ct["scholars_vs_civilizations_a_plus_minus_b_plus"]["bidirectional_gained"])
        self.assertTrue(ct["scholars_vs_label_stripped_operators_a_plus_minus_c_plus"]["label_strip_parity_confirmed"])
        self.assertEqual(ct["multi_seat_mean_vs_single_control"]["multi_seat_mean_pass_rate_q"], "5/6")
        self.assertEqual(ct["multi_seat_mean_vs_single_control"]["pass_rate_delta_q"], "-1/14")
        self.assertEqual(ct["multi_seat_mean_vs_single_control"]["cross_seat_delta_q"], "9/1")
        self.assertEqual(ct["multi_seat_mean_vs_single_control"]["chaired_mean_interpositions_q"], "13/1")

        fb = c["fallback_sensitivity_disclosure"]
        self.assertEqual(fb["multi_seat_ablation_fallback_rate_q"], "22/63")
        self.assertEqual(fb["multi_seat_ablation_cross_route_fallbacks"], 22)
        self.assertEqual(fb["single_control_fallback_rate_q"], "2/21")
        self.assertEqual(fb["single_control_cross_route_fallbacks"], 0)
        self.assertEqual(fb["fallback_rate_gap_q"], "16/63")

        v = c["variation_ablation_verdict"]
        self.assertEqual(v["structural_gate_winners"], ["Arm_A_plus"])
        self.assertEqual(v["overall_structural_winner"], "Arm_A_plus")
        self.assertEqual(v["raw_pass_rate_leader"], "Arm_D_single")
        self.assertTrue(v["raw_pass_leader_lacks_cross_pollination"])
        self.assertEqual(v["recommended_permanent_seminar_mode"], "HYBRID_A_PLUS_C_PLUS_WITH_MANDATORY_R2_SEAT0_TARGET")
        self.assertTrue(v["passed"])

    def test_03_provenance_parser_adversarial_and_boolop_branches(self) -> None:
        self._assert_err("BAD_PROVENANCE", sc.parse_provenance_covariates, [])

        for mutator, code in (
            (lambda d: d.__setitem__("schema", "wrong"), "BAD_PROVENANCE_SCHEMA"),
            (lambda d: d.__setitem__("topic_id", "WRONG"), "BAD_PROVENANCE_TOPIC"),
            (lambda d: d.__setitem__("energy_power_status", "CLAIMED"), "BAD_ENERGY_POLICY"),
            (lambda d: d.__setitem__("anonymization_note", "used " + "clau" + "de"), "MODEL_POLLUTION"),
            (lambda d: d.__setitem__("arms", []), "BAD_PROVENANCE_ARMS"),
            (lambda d: d["arms"].pop("Arm_A_plus"), "BAD_PROVENANCE_ARMS"),
            (lambda d: d.__setitem__("arm_count", 99), "BAD_PROVENANCE_COUNT"),
            (lambda d: d["arms"].__setitem__("Arm_D_single", []), "BAD_PROVENANCE_ENTRY"),
            (lambda d: d["arms"]["Arm_A_plus"].__setitem__("file_sha256", 123), "BAD_PROV_SHA"),
            (lambda d: d["arms"]["Arm_A_plus"].__setitem__("transcript_sha256", 123), "BAD_PROV_SHA"),
            (lambda d: d["arms"]["Arm_A_plus"].__setitem__("provenance_scope_note", 123), "BAD_PROV_NOTE"),
            (lambda d: d["arms"]["Arm_A_plus"].__setitem__("provenance_scope_note", ""), "BAD_PROV_NOTE"),
            (lambda d: d["arms"]["Arm_D_single"].__setitem__("turns", "bad"), "BAD_PROV_TURNS"),
            (lambda d: d["arms"]["Arm_D_single"].__setitem__("turns", d["arms"]["Arm_D_single"]["turns"][:20]), "BAD_PROV_TURNS"),
            (lambda d: d["arms"]["Arm_D_single"].__setitem__("route_histogram", []), "BAD_ROUTE_HIST"),
            (lambda d: d["arms"]["Arm_D_single"].__setitem__("route_histogram", {}), "BAD_ROUTE_HIST"),
            (lambda d: d["arms"]["Arm_D_single"]["turns"].__setitem__(0, "bad"), "BAD_PROV_TURN"),
            (lambda d: d["arms"]["Arm_D_single"]["turns"][0].__setitem__("attempts", "bad"), "BAD_ATTEMPTS"),
            (lambda d: d["arms"]["Arm_D_single"]["turns"][0].__setitem__("attempts", []), "BAD_ATTEMPTS"),
            (lambda d: d["arms"]["Arm_D_single"]["turns"][0]["attempts"][0].__setitem__("route", 123), "BAD_ROUTE"),
            (lambda d: d["arms"]["Arm_A_minus"]["turns"][0]["attempts"][-1].__setitem__("route", 456), "BAD_ROUTE"),
            (lambda d: d["arms"]["Arm_D_single"]["turns"][0]["attempts"][0].__setitem__("ok", 1), "BAD_OK_FLAG"),
            (lambda d: d["arms"]["Arm_D_single"].__setitem__("fallback_turns_count", 99), "FALLBACK_COUNT_MISMATCH"),
            (lambda d: d["arms"]["Arm_D_single"].__setitem__("route_histogram", {"r1": 20}), "HIST_SUM_MISMATCH"),
        ):
            bad = copy.deepcopy(self.pm_doc)
            mutator(bad)
            self._assert_err(code, sc.parse_provenance_covariates, bad)

        zero_ms = copy.deepcopy(self.pm_doc)
        zero_ms["arms"]["Arm_D_single"]["turns"][0]["attempts"] = [
            {"attempt": 1, "elapsed_ms": 0, "ok": True, "rc": 0, "route": "route-1"}
        ]
        self.assertGreaterEqual(sc.parse_provenance_covariates(zero_ms)["Arm_D_single"]["elapsed_ok_ms"], 0)
        zero_ms["arms"]["Arm_D_single"]["turns"][0]["attempts"][0]["elapsed_ms"] = -1
        self._assert_err("NEG_ELAPSED", sc.parse_provenance_covariates, zero_ms)

        bad_mid = copy.deepcopy(self.pm_doc)
        bad_mid["arms"]["Arm_D_single"]["turns"][0]["attempts"] = [
            {"attempt": 1, "elapsed_ms": 10, "ok": False, "rc": 1, "route": "route-1"},
            "not-a-dict",
            {"attempt": 2, "elapsed_ms": 10, "ok": True, "rc": 0, "route": "route-2"},
        ]
        self._assert_err("BAD_ATTEMPT", sc.parse_provenance_covariates, bad_mid)

    def test_04_arm_metrics_contrasts_and_boundaries(self) -> None:
        arm_d_doc = sos.loads_strict_json_bytes(
            SEMINAR_DIR.joinpath("ablation_transcripts/arm_d.json").read_bytes(),
            "arm_d.json",
        )
        d_sha = sc.ARM_SPECS[4][6]
        prov = sc.parse_provenance_covariates(self.pm_doc)["Arm_D_single"]

        class StubSeminar:
            def __init__(self, sess_out, strip_err=False):
                self._sess = sess_out
                self._strip_err = strip_err

            def evaluate_seminar_session(self, **kwargs):
                return self._sess

            def assert_variation_c_label_stripped(self, s):
                if self._strip_err:
                    raise sos.SeminarError("VARIATION_C_LABEL_LEAK", "forbidden label")
                return None

        stub_ok = StubSeminar(arm_d_doc["session"])

        bad_sess = copy.deepcopy(arm_d_doc["session"])
        bad_sess["pass_witness_count"] = 18
        self._assert_err(
            "LIVE_REFEREE_DRIFT",
            sc.compute_arm_metrics,
            "Arm_D_single", "single", "none", 1, bad_sess, arm_d_doc["turns"], sos, d_sha, None, prov,
        )

        self._assert_err(
            "VARIATION_C_LABEL_LEAK",
            sc.compute_arm_metrics,
            "Arm_C_plus", "operators", "none", 1,
            {**arm_d_doc["session"], "variation": "operators"},
            arm_d_doc["turns"], StubSeminar({**arm_d_doc["session"], "variation": "operators"}, strip_err=True), d_sha, None, None,
        )

        class ErrEvalSeminar(StubSeminar):
            def evaluate_seminar_session(self, **kwargs):
                raise sos.SeminarError("SANDBOX_FORBIDDEN_ATTR", "probe")

        self._assert_err(
            "SANDBOX_FORBIDDEN_ATTR",
            sc.compute_arm_metrics,
            "Arm_D_single", "single", "none", 1,
            arm_d_doc["session"], arm_d_doc["turns"], ErrEvalSeminar(arm_d_doc["session"]), d_sha, None, prov,
        )

        self._assert_err("BAD_SESSION", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, [], arm_d_doc["turns"], stub_ok, d_sha, None, prov)
        self._assert_err("BAD_TURN_BUDGET", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, arm_d_doc["session"], "not-list", stub_ok, d_sha, None, prov)
        self._assert_err("BAD_TURN_BUDGET", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, arm_d_doc["session"], arm_d_doc["turns"][:20], stub_ok, d_sha, None, prov)
        self._assert_err("BAD_VARIATION", sc.compute_arm_metrics, "Arm_D_single", "scholars", "none", 1, arm_d_doc["session"], arm_d_doc["turns"], stub_ok, d_sha, None, prov)
        self._assert_err("BAD_CHAIR", sc.compute_arm_metrics, "Arm_D_single", "single", "aletheia", 1, arm_d_doc["session"], arm_d_doc["turns"], stub_ok, d_sha, None, prov)
        bad_topic = copy.deepcopy(arm_d_doc["session"])
        bad_topic["topic_id"] = "OTHER"
        self._assert_err("BAD_TOPIC", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, bad_topic, arm_d_doc["turns"], StubSeminar(bad_topic), d_sha, None, prov)
        self._assert_err("BAD_PROVENANCE_ENTRY", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, arm_d_doc["session"], arm_d_doc["turns"], stub_ok, d_sha, None, None)
        bad_prov = dict(prov)
        bad_prov["file_sha256"] = "0" * 64
        self._assert_err("PROV_FILE_SHA_MISMATCH", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, arm_d_doc["session"], arm_d_doc["turns"], stub_ok, d_sha, None, bad_prov)
        bad_prov = dict(prov)
        bad_prov["transcript_sha256"] = "0" * 64
        self._assert_err("PROV_TX_SHA_MISMATCH", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, arm_d_doc["session"], arm_d_doc["turns"], stub_ok, d_sha, None, bad_prov)
        self._assert_err("SEAT_COUNT_MISMATCH", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 2, arm_d_doc["session"], arm_d_doc["turns"], stub_ok, d_sha, None, prov)

        stub_sess = copy.deepcopy(arm_d_doc["session"])
        stub_sess["pass_witness_count"] = 21
        stub_sess["minimal_counterexample_count"] = 0
        stub_sess["dag_edges"] = []
        stub_sess["s150_g2_dynamic_compounding_passed"] = True
        stub_sess["s150_g5_bidirectional_pollination_passed"] = True
        stub_sess["cross_seat_compositions"] = [{"src_turn": "a", "dst_turn": "b"}]
        for r in stub_sess["turn_records"]:
            r["verdict"]["status"] = "PASS_WITNESS"
            r["interpositions_count"] = 0
        stub_sess["turn_records"][0]["interpositions_count"] = 1
        m_pass_edge = sc.compute_arm_metrics(
            "Arm_D_single", "single", "none", 1, stub_sess, arm_d_doc["turns"], StubSeminar(stub_sess), d_sha, None, prov,
        )
        self.assertEqual(m_pass_edge["repairs_per_cex_q"], "0/1")
        self.assertEqual(m_pass_edge["cross_seat_edge_rate_q"], "0/1")
        self.assertTrue(m_pass_edge["passes_all_structural_gates"])

        stub_no_interp = copy.deepcopy(stub_sess)
        stub_no_interp["turn_records"][0]["interpositions_count"] = 0
        self.assertFalse(
            sc.compute_arm_metrics("Arm_D_single", "single", "none", 1, stub_no_interp, arm_d_doc["turns"], StubSeminar(stub_no_interp), d_sha, None, prov)["passes_all_structural_gates"]
        )
        stub_no_xs = copy.deepcopy(stub_sess)
        stub_no_xs["cross_seat_compositions"] = []
        self.assertFalse(
            sc.compute_arm_metrics("Arm_D_single", "single", "none", 1, stub_no_xs, arm_d_doc["turns"], StubSeminar(stub_no_xs), d_sha, None, prov)["passes_all_structural_gates"]
        )

        bad_sum = copy.deepcopy(stub_sess)
        bad_sum["pass_witness_count"] = 20
        self._assert_err("VERDICT_SUM_MISMATCH", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, bad_sum, arm_d_doc["turns"], StubSeminar(bad_sum), d_sha, None, prov)
        bad_r3 = copy.deepcopy(stub_sess)
        for r in bad_r3["turn_records"]:
            if r["round_num"] == 3:
                r["round_num"] = 2
        self._assert_err("BAD_ROUNDS", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, bad_r3, arm_d_doc["turns"], StubSeminar(bad_r3), d_sha, None, prov)
        bad_r4 = copy.deepcopy(stub_sess)
        bad_r4["turn_records"][0]["round_num"] = 4
        self._assert_err("BAD_ROUNDS", sc.compute_arm_metrics, "Arm_D_single", "single", "none", 1, bad_r4, arm_d_doc["turns"], StubSeminar(bad_r4), d_sha, None, prov)

        arms_map = {a["arm_id"]: copy.deepcopy(a) for a in self.cert["arms"]}
        arms_eq = copy.deepcopy(arms_map)
        arms_eq["Arm_C_plus"]["pass_witness_count"] = arms_eq["Arm_A_plus"]["pass_witness_count"]
        ct_eq, _, _ = sc.compute_contrasts_and_verdict(arms_eq)
        self.assertTrue(ct_eq["scholars_vs_label_stripped_operators_a_plus_minus_c_plus"]["label_strip_parity_confirmed"])
        arms_eq["Arm_C_plus"]["pass_witness_count"] = arms_eq["Arm_A_plus"]["pass_witness_count"] - 1
        ct_lo, _, _ = sc.compute_contrasts_and_verdict(arms_eq)
        self.assertFalse(ct_lo["scholars_vs_label_stripped_operators_a_plus_minus_c_plus"]["label_strip_parity_confirmed"])

        arms_alt = copy.deepcopy(arms_map)
        arms_alt["Arm_A_minus"]["bidirectional_pollination_passed"] = True
        arms_alt["Arm_A_minus"]["passes_all_structural_gates"] = True
        arms_alt["Arm_B_plus"]["bidirectional_pollination_passed"] = True
        ct_alt, _, v_alt = sc.compute_contrasts_and_verdict(arms_alt)
        self.assertFalse(ct_alt["chair_effect_a_plus_minus_a_minus"]["bidirectional_gained"])
        self.assertFalse(ct_alt["scholars_vs_civilizations_a_plus_minus_b_plus"]["bidirectional_gained"])
        self.assertEqual(v_alt["overall_structural_winner"], "INCONCLUSIVE")
        self.assertFalse(v_alt["passed"])

        arms_alt2 = copy.deepcopy(arms_map)
        arms_alt2["Arm_A_plus"]["bidirectional_pollination_passed"] = False
        arms_alt2["Arm_A_plus"]["passes_all_structural_gates"] = False
        arms_alt2["Arm_B_plus"]["passes_all_structural_gates"] = True
        ct_alt2, _, v_alt2 = sc.compute_contrasts_and_verdict(arms_alt2)
        self.assertFalse(ct_alt2["chair_effect_a_plus_minus_a_minus"]["bidirectional_gained"])
        self.assertFalse(ct_alt2["scholars_vs_civilizations_a_plus_minus_b_plus"]["bidirectional_gained"])
        self.assertEqual(v_alt2["overall_structural_winner"], "Arm_B_plus")
        self.assertFalse(v_alt2["passed"])

    def test_05_certificate_validation_loader_and_cli_roundtrip(self) -> None:
        sc.validate_certificate_payload(self.cert)
        self._assert_err("BAD_CERT_TYPE", sc.validate_certificate_payload, [])

        bad_flt = copy.deepcopy(self.cert)
        bad_flt["zero_floats"] = 1.5
        self._assert_err("FLOAT_FORBIDDEN", sc.validate_certificate_payload, bad_flt)

        bad_poll = copy.deepcopy(self.cert)
        bad_poll["fallback_sensitivity_disclosure"]["disclosure_note"] = "used " + "clau" + "de"
        self._assert_err("MODEL_POLLUTION", sc.validate_certificate_payload, bad_poll)

        bad = copy.deepcopy(self.cert)
        bad["extra"] = 1
        self._assert_err("BAD_CERT_KEYS", sc.validate_certificate_payload, bad)

        for field, val, code in (
            ("schema", "bad", "BAD_SCHEMA"),
            ("benchmark_topic_id", "OTHER", "BAD_TOPIC"),
            ("energy_power_status", "CLAIMED", "BAD_ENERGY"),
            ("zero_floats", False, "BAD_ZERO_FLOATS"),
            ("pure_q_ast_clean", False, "BAD_AST_FLAG"),
            ("arm_count", 4, "BAD_ARM_COUNT"),
            ("matched_turn_budget_per_arm", 20, "BAD_BUDGET"),
            ("total_refereed_turns", 104, "BAD_TOTAL_TURNS"),
            ("all_passed", False, "GATES_NOT_ALL_PASSED"),
            ("payload_sha256", 123, "PAYLOAD_SHA_MISMATCH"),
            ("payload_sha256", "0" * 64, "PAYLOAD_SHA_MISMATCH"),
            ("certificate_sha256", 123, "CERT_SHA_MISMATCH"),
            ("certificate_sha256", "0" * 64, "CERT_SHA_MISMATCH"),
        ):
            t = copy.deepcopy(self.cert)
            t[field] = val
            self._assert_err(code, sc.validate_certificate_payload, t)

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            self._assert_err("MISSING_INPUT", sc._read_pinned_json, tmp.joinpath("missing.json"), "0" * 64, "missing")
            f = tmp.joinpath("a.json")
            f.write_text('{"x":1}\n', encoding="utf-8")
            self._assert_err("INPUT_SHA_MISMATCH", sc._read_pinned_json, f, "0" * 64, "a.json")
            sym_f = tmp.joinpath("sym_a.json")
            sym_f.symlink_to(f)
            self._assert_err("SYMLINK_FORBIDDEN", sc._read_pinned_json, sym_f, "0" * 64, "sym_a.json")

            bad_dup = tmp.joinpath("dup.json")
            bad_dup.write_text('{"x":1,"x":2}\n', encoding="utf-8")
            self._assert_err("DUPLICATE_JSON_KEY", sc._read_pinned_json, bad_dup, hashlib.sha256(bad_dup.read_bytes()).hexdigest(), "dup.json")

            f_sha = hashlib.sha256(f.read_bytes()).hexdigest()
            self._assert_err("BAD_SPEC", sc._load_arm_inputs, tmp, "Arm_A_plus", "a.json", "t.json", f_sha, None, {})
            self._assert_err("BAD_ARM_ID", sc._load_arm_inputs, tmp, "Arm_D_single", "a.json", None, f_sha, None, {})
            f_list = tmp.joinpath("lst.json")
            f_list.write_text("[1,2]\n", encoding="utf-8")
            fl_sha = hashlib.sha256(f_list.read_bytes()).hexdigest()
            self._assert_err("BAD_ARM_DOC", sc._load_arm_inputs, tmp, "Arm_D_single", "lst.json", None, fl_sha, None, {})

            with mock.patch.object(sc, "build_scorecard_certificate", return_value=self.cert):
                cert_path = tmp.joinpath("cert.json")
                out_buf = io.StringIO()
                with redirect_stdout(out_buf):
                    rc_w = sc.main(["--seminar-dir", str(SEMINAR_DIR), "--write", str(cert_path)])
                self.assertEqual(rc_w, 0)
                self.assertEqual(json.loads(out_buf.getvalue())["status"], "WRITTEN")

                chk_buf = io.StringIO()
                with redirect_stdout(chk_buf):
                    rc_c = sc.main(["--seminar-dir", str(SEMINAR_DIR), "--check", str(cert_path)])
                self.assertEqual(rc_c, 0)
                self.assertEqual(json.loads(chk_buf.getvalue())["status"], "PASS")

                sym_c = tmp.joinpath("sym_cert.json")
                sym_c.symlink_to(cert_path)
                self._assert_err("SYMLINK_FORBIDDEN", sc.check_certificate_file, sym_c, SEMINAR_DIR)
                err_sw = io.StringIO()
                with redirect_stderr(err_sw):
                    self.assertEqual(sc.main(["--seminar-dir", str(SEMINAR_DIR), "--write", str(sym_c)]), 2)
                self.assertIn("SYMLINK_FORBIDDEN", err_sw.getvalue())

                self._assert_err("DUPLICATE_JSON_KEY", sc.check_certificate_file, bad_dup, SEMINAR_DIR)

                tampered = copy.deepcopy(self.cert)
                tampered["arms"][0]["pass_witness_count"] = 17
                payload = {k: v for k, v in tampered.items() if k not in ("payload_sha256", "certificate_sha256")}
                tampered["payload_sha256"] = hashlib.sha256(sos.canonical_json_bytes(payload)).hexdigest()
                body = {k: v for k, v in tampered.items() if k != "certificate_sha256"}
                tampered["certificate_sha256"] = hashlib.sha256(sos.canonical_json_bytes(body)).hexdigest()
                tampered_path = tmp.joinpath("tampered.json")
                tampered_path.write_text(json.dumps(tampered, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                err_buf = io.StringIO()
                with redirect_stderr(err_buf):
                    rc_bad = sc.main(["--seminar-dir", str(SEMINAR_DIR), "--check", str(tampered_path)])
                self.assertEqual(rc_bad, 2)
                self.assertIn("LIVE_RECOMPUTE_MISMATCH", err_buf.getvalue())

                err_buf2 = io.StringIO()
                with redirect_stderr(err_buf2):
                    rc_miss = sc.main(["--seminar-dir", str(SEMINAR_DIR), "--check", str(tmp.joinpath("nope.json"))])
                self.assertEqual(rc_miss, 2)
                self.assertIn("MISSING_CERT", err_buf2.getvalue())

                st_buf = io.StringIO()
                with redirect_stdout(st_buf):
                    rc_s = sc.main(["--seminar-dir", str(SEMINAR_DIR), "--standalone"])
                self.assertEqual(rc_s, 0)
                self.assertEqual(json.loads(st_buf.getvalue())["certificate_sha256"], self.cert["certificate_sha256"])

                err_io = io.StringIO()
                with redirect_stderr(err_io):
                    self.assertEqual(sc.main(["--seminar-dir", str(SEMINAR_DIR), "--write", str(tmp.joinpath("missing_dir", "c.json"))]), 2)
                self.assertEqual(json.loads(err_io.getvalue())["error_code"], "IO_ERROR")

            # MED-2: symlinked script invocation & sos.SeminarError / OSError wrapping must exit RC=2 with JSON, zero tracebacks
            sym_script = tmp.joinpath("sym_ablation.py")
            sym_script.symlink_to(SEMINAR_DIR.joinpath("verify_ablation_scorecard.py"))
            for cli_args in (["--standalone"], ["--check", str(cert_path)]):
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
                self._assert_err("AST_FORBIDDEN_NAME", sc.build_scorecard_certificate, SEMINAR_DIR)
            with mock.patch.object(sos, "read_regular_file_bytes", return_value=b"\xff\xfe"):
                self._assert_err("BAD_UTF8", sc.build_scorecard_certificate, SEMINAR_DIR)
            with mock.patch.object(sos, "canonical_json_bytes", side_effect=sos.SeminarError("JSON_DEPTH", "deep")):
                self._assert_err("JSON_DEPTH", sc._canonical_json_bytes, {"a": 1})
            with mock.patch.object(sc, "build_scorecard_certificate", side_effect=sos.SeminarError("SYMLINK_FORBIDDEN", "sym")):
                err_sos = io.StringIO()
                with redirect_stderr(err_sos):
                    self.assertEqual(sc.main(["--seminar-dir", str(SEMINAR_DIR), "--standalone"]), 2)
                self.assertEqual(json.loads(err_sos.getvalue())["error_code"], "SYMLINK_FORBIDDEN")

            self.assertEqual(sc.default_seminar_dir(), SEMINAR_DIR)


if __name__ == "__main__":
    unittest.main()
