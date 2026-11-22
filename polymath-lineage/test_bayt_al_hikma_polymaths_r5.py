#!/usr/bin/env python3
"""R1-R5, boundary, red-team bypass, and 100% mutation-kill test suite for AUDIT-092R2.

Runs cleanly under `python3 -I -O -B -W error test_bayt_al_hikma_polymaths_r5.py`.
Zero floats; zero bare assert statements.
"""

from __future__ import annotations

from fractions import Fraction
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

_THIS_DIR = str(Path(__file__).resolve().parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)

import bayt_al_hikma_polymath_certifier as bah


def _cite(tag: str = "Ref") -> dict[str, str]:
    return {"work": f"Work {tag}", "edition": "Ed. 2000", "location": "p. 1"}


class TestPrimitivesAndAlgebra(unittest.TestCase):
    def test_type_and_number_theory_primitives(self) -> None:
        self.assertEqual(bah.frac_str(Fraction(7, 3)), "7/3")
        self.assertEqual(bah.frac_str(4), "4/1")
        self.assertEqual(bah.frac_dec6(Fraction(-3, 8)), "-0.375000")
        self.assertEqual(bah.frac_dec6(Fraction(0, 1)), "0.000000")
        self.assertEqual(bah.frac_dec6_ceil(Fraction(0, 1)), "0.000000")
        self.assertEqual(bah.frac_dec6_ceil(Fraction(1, 2_000_000)), "0.000001")
        with self.assertRaisesRegex(bah.PolymathAuditError, r"frac-dec6-ceil-nonneg"):
            bah.frac_dec6_ceil(Fraction(-1, 10))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"exact-fraction:frac_str"):
            bah.frac_str(True)  # type: ignore[arg-type]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"exact-fraction:frac_str"):
            bah.frac_str("1/2")  # type: ignore[arg-type]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"exact-int:n"):
            bah._v2_exact(False)  # type: ignore[arg-type]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"v2-pos"):
            bah._v2_exact(0)
        with self.assertRaisesRegex(bah.PolymathAuditError, r"divisor-sum-ge-2"):
            bah._proper_divisor_sum(1)
        self.assertEqual(bah._proper_divisor_sum(4), 3)
        self.assertEqual(bah._proper_divisor_sum(2), 1)
        self.assertFalse(bah._is_prime_exact(1))
        self.assertTrue(bah._is_prime_exact(2))
        self.assertFalse(bah._is_prime_exact(9))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"divisors-nonzero"):
            bah._positive_divisors(0)
        self.assertEqual(bah._positive_divisors(-4), [1, 2, 4])

    def test_khwarizmi_reducer_and_laurent_refusals(self) -> None:
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-lhs-len"):
            bah.reduce_khwarizmi_quadratic((Fraction(1, 1),), (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)))  # type: ignore[arg-type]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-rhs-len"):
            bah.reduce_khwarizmi_quadratic((Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)), (Fraction(0, 1),))  # type: ignore[arg-type]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-degenerate-no-unknown"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(1, 1), Fraction(2, 1), Fraction(3, 1)),
                (Fraction(1, 1), Fraction(2, 1), Fraction(5, 1)),
            )
        neg_lin = bah.reduce_khwarizmi_quadratic(
            (Fraction(0, 1), Fraction(-2, 1), Fraction(6, 1)),
            (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
        )
        self.assertEqual(neg_lin["positive_root"], "3/1")
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-no-positive-root"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(0, 1), Fraction(2, 1), Fraction(6, 1)),
                (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-no-positive-root"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(0, 1), Fraction(2, 1), Fraction(0, 1)),
                (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-no-positive-root"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(1, 1), Fraction(2, 1), Fraction(0, 1)),
                (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-no-positive-root"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)),
                (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-no-positive-root"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(1, 1), Fraction(0, 1), Fraction(4, 1)),
                (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
            )
        t5_zero = bah.reduce_khwarizmi_quadratic(
            (Fraction(1, 1), Fraction(0, 1), Fraction(4, 1)),
            (Fraction(0, 1), Fraction(4, 1), Fraction(0, 1)),
        )
        self.assertEqual(t5_zero["discriminant"], "0/1")
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-complex-roots"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(1, 1), Fraction(0, 1), Fraction(5, 1)),
                (Fraction(0, 1), Fraction(2, 1), Fraction(0, 1)),
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"khwarizmi-no-positive-root"):
            bah.reduce_khwarizmi_quadratic(
                (Fraction(1, 1), Fraction(3, 1), Fraction(2, 1)),
                (Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)),
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"laurent-dict"):
            bah.laurent_normalize([1, 2])  # type: ignore[arg-type]


class TestFivePillarsExactValues(unittest.TestCase):
    def test_pillar1_continuum_and_thabit(self) -> None:
        p1 = bah.analyze_pillar1_continuum_vs_atomism()
        obs = p1["biruni_ibn_sina_discrete_obstruction"]
        self.assertTrue(obs["all_v2_odd"])
        self.assertEqual(obs["diagonal_squared_metric_distortion"], "2/1")
        self.assertEqual(obs["concentric_wheel_2to1_inner_step"], "1/2")
        self.assertFalse(obs["concentric_step_is_integer"])

        th = {r["n"]: r for r in p1["thabit_amicable_theorem"]}
        self.assertTrue(th[2]["all_three_prime"] and th[2]["is_amicable"])
        self.assertEqual((th[2]["A"], th[2]["B"]), (220, 284))
        self.assertFalse(th[3]["all_three_prime"] or th[3]["is_amicable"])
        self.assertTrue(th[4]["all_three_prime"] and th[4]["is_amicable"])
        self.assertEqual((th[4]["A"], th[4]["B"]), (17296, 18416))

        q = p1["thabit_parabola_quadrature"]
        self.assertTrue(q["sandwiches_two_thirds"])
        self.assertTrue(q["width_equals_one_over_N"])
        self.assertEqual(q["bracket_width"], "1/100")

    def test_pillar2_haytham_khayyam_rushd(self) -> None:
        p2 = bah.analyze_pillar2_haytham_khayyam_rushd()
        alh = p2["alhazen_spherical_mirror_quartic"]
        self.assertEqual(alh["symmetric_t0_residual"], "0/1")
        self.assertEqual(alh["quartic_coeffs_desc"], ["9/1", "4/1", "-36/1", "4/1", "3/1"])
        self.assertEqual(alh["quartic_rational_roots"], [])
        self.assertEqual(alh["real_root_sign_changes"], 4)
        self.assertEqual(alh["ferrari_resolvent_cubic_int"], [531441, -4330260, 8323236, -960400])
        self.assertEqual(alh["ferrari_resolvent_rational_roots"], [])
        self.assertTrue(alh["ruler_and_compass_impossible_exact"])

        hk = p2["haytham_khayyam_quadrilateral_trichotomy"]
        self.assertEqual(hk["hyperbolic_cos_summit"], "5/16")
        self.assertTrue(hk["hyperbolic_acute"])
        self.assertEqual(hk["euclidean_cos_summit"], "0/1")
        self.assertTrue(hk["euclidean_right"])
        self.assertEqual(hk["spherical_cos_summit"], "-3/13")
        self.assertTrue(hk["spherical_obtuse"])

        ir = p2["ibn_rushd_anti_epicycle_witness"]
        self.assertEqual(ir["in_sample_l1_error"], "0/1")
        self.assertEqual(ir["held_out_x10_error"], "45/1")

    def test_pillar3_khwarizmi_and_samawal(self) -> None:
        p3 = bah.analyze_pillar3_transformational_algebra_laurent()
        k6 = p3["khwarizmi_six_canonical_forms"]
        self.assertEqual(k6["type1"]["canonical_type"], 1)
        self.assertEqual(k6["type2"]["canonical_type"], 2)
        self.assertEqual(k6["type3"]["canonical_type"], 3)
        self.assertEqual(k6["type4_flagship_x2_10x_39"]["discriminant"], "64/1")
        self.assertTrue(k6["type4_flagship_root_3_verified"])
        self.assertEqual(k6["type5"]["canonical_type"], 5)
        self.assertEqual(k6["type6"]["canonical_type"], 6)

        sm = p3["samawal_laurent_ring_identities"]
        self.assertTrue(sm["geom_identity_exact"])
        self.assertTrue(sm["negative_exponent_inverse_exact"])
        self.assertTrue(sm["schur_numerator_exact_neg_q3"])

    def test_pillar4_kindi_biruni_tusi_jazari(self) -> None:
        p4 = bah.analyze_pillar4_kindi_biruni_tusi_jazari()
        kd = p4["kindi_de_gradibus_and_frequency_null"]
        self.assertEqual(kd["de_gradibus_2_pow_n"]["degree_4"], 16)
        self.assertEqual(kd["plain_l1_from_uniform"], "1/2")
        self.assertTrue(kd["permutation_invariant_exact"])

        br = p4["biruni_nandana_geodesy_analysis"]
        self.assertEqual(br["epistemic_status"], "ARITHMETIC_FIT_HYPOTHESIS_SINGLE_NUMBER")
        self.assertEqual(br["sexagesimal_3place_cos34"], "215989/216000")
        self.assertEqual(br["sexagesimal_3place_r"], "28167341479/2200")
        self.assertEqual(br["sexagesimal_3place_r_dec6"], "12803337.035909")
        self.assertTrue(br["matches_reported_integer_within_1_cubit"])
        sens = br["sexagesimal_truncation_sensitivity"]
        self.assertEqual(sens["places_2"]["radius_dec6"], "2346745.945000")
        self.assertEqual(sens["places_3"]["radius_dec6"], "12803337.035909")
        self.assertEqual(sens["places_4"]["radius_dec6"], "13328421.762034")
        self.assertEqual(sens["places_5"]["radius_dec6"], "13331576.074683")
        self.assertEqual(br["refraction_k_one_seventh_factor"], "7/6")

        ts = p4["tusi_couple_zero_residual"]
        self.assertTrue(ts["all_transverse_residuals_zero"])
        self.assertEqual(len(ts["samples"]), 7)

        jz = p4["jazari_float_valve_regimes"]
        self.assertEqual(jz["monotone_mu_half"][-1], "1/16")
        self.assertEqual(jz["damped_osc_mu_3_halves"][-1], "1/16")
        self.assertEqual(jz["hunting_mu_2"], ["1/1", "-1/1", "1/1", "-1/1", "1/1"])
        self.assertEqual(jz["divergent_mu_5_halves"][-1], "81/16")

    def test_pillar5_receipts(self) -> None:
        p5 = bah.analyze_pillar5_lineage_and_certifiers()
        lg = p5["lineage_graph_receipt"]
        self.assertTrue(lg["certified"])
        self.assertTrue(lg["encoding_consistency_only"])
        self.assertTrue(lg["all_nodes_and_edges_cited"])
        self.assertEqual(lg["node_count"], 13)
        self.assertEqual(lg["edge_count"], 14)
        self.assertTrue(lg["directed_dag_acyclic"])
        self.assertFalse(p5["overparameterized_epicycle_and_hunting_valve"]["certified"])
        self.assertEqual(
            p5["overparameterized_epicycle_and_hunting_valve"]["violations"],
            [
                "RUSHD_EPICYCLE_OVERPARAMETERIZED",
                "RUSHD_HELD_OUT_ERROR_EXCEEDED",
                "JAZARI_UNSTABLE_LOOP_GAIN",
            ],
        )
        self.assertTrue(p5["certified_anti_epicycle_and_monotone_valve"]["certified"])
        self.assertEqual(
            p5["certified_anti_epicycle_and_monotone_valve"]["controller_regime"], "MONOTONE_CONVERGENT"
        )


class TestRedTeamLineageAndFeedbackCertifiers(unittest.TestCase):
    def _sample_nodes(self) -> list[dict[str, object]]:
        return [
            {"node_id": "A", "name": "Scholar A", "birth_year": 800, "death_year": 860, "city": "Baghdad", "primary_work": "Work A", "source": _cite("A")},
            {"node_id": "B", "name": "Scholar B", "birth_year": 830, "death_year": 900, "city": "Baghdad", "primary_work": "Work B", "source": _cite("B")},
            {"node_id": "C", "name": "Scholar C", "birth_year": 910, "death_year": 980, "city": "Cairo", "primary_work": "Work C", "source": _cite("C")},
        ]

    def _valid_feedback(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "epicycle_dof": 1,
            "held_out_constraints": 2,
            "in_sample_error": Fraction(0, 1),
            "held_out_error": Fraction(1, 10),
            "max_held_out_error": Fraction(1, 10),
            "null_baseline_error": Fraction(1, 5),
            "valve_gain_kappa": Fraction(1, 1),
            "step_dt": Fraction(1, 1),
            "reservoir_area": Fraction(1, 1),
            "setpoint_head": Fraction(1, 1),
            "nominal_flow": Fraction(1, 1),
            "valve_max_flow": Fraction(2, 1),
        }
        base.update(overrides)
        return base

    def test_lineage_active_voice_chronology_citations_and_refusals(self) -> None:
        nodes = self._sample_nodes()
        # Valid active-voice edges: A teacher_of B, A corresponded_with B, C extended B
        ok = bah.certify_polymath_lineage_graph(
            nodes,
            [
                {"source": "A", "target": "B", "relation": "teacher_of", "citation": _cite("e1")},
                {"source": "A", "target": "B", "relation": "corresponded_with", "citation": _cite("e2")},
                {"source": "C", "target": "B", "relation": "extended", "citation": _cite("e3")},
            ],
        )
        self.assertTrue(ok["certified"])

        # Exact closed pass boundaries:
        # - teacher_of: 800-822 -> 810-860 (gap==10, overlap==12)
        # - corresponded_with: 800-830 <-> 815-860 (overlap==15)
        # - extended (active voice actor->subject): I2(800-815) -> I1(800-815)
        #   (actor_birth+15==actor_death, subj_birth+15==subj_death, actor_death==subj_birth+15, actor_birth==subj_birth)
        nodes_bd_ok = [
            {"node_id": "T", "name": "T", "birth_year": 800, "death_year": 822, "city": "Baghdad", "primary_work": "W", "source": _cite("T")},
            {"node_id": "S", "name": "S", "birth_year": 810, "death_year": 860, "city": "Baghdad", "primary_work": "W", "source": _cite("S")},
            {"node_id": "C1", "name": "C1", "birth_year": 800, "death_year": 830, "city": "Baghdad", "primary_work": "W", "source": _cite("C1")},
            {"node_id": "C2", "name": "C2", "birth_year": 815, "death_year": 860, "city": "Baghdad", "primary_work": "W", "source": _cite("C2")},
            {"node_id": "I1", "name": "I1", "birth_year": 800, "death_year": 815, "city": "Baghdad", "primary_work": "W", "source": _cite("I1")},
            {"node_id": "I2", "name": "I2", "birth_year": 800, "death_year": 815, "city": "Baghdad", "primary_work": "W", "source": _cite("I2")},
        ]
        ok_bd = bah.certify_polymath_lineage_graph(
            nodes_bd_ok,
            [
                {"source": "T", "target": "S", "relation": "teacher_of", "citation": _cite("1")},
                {"source": "C1", "target": "C2", "relation": "corresponded_with", "citation": _cite("2")},
                {"source": "I2", "target": "I1", "relation": "extended", "citation": _cite("3")},
            ],
        )
        self.assertTrue(ok_bd["certified"])

        # Review #6 repro (850-death critiqued 1201-birth!) + EVERY isolated 1-year-under clause
        nodes_bad = [
            {"node_id": "Khw", "name": "Khw", "birth_year": 780, "death_year": 850, "city": "Baghdad", "primary_work": "W", "source": _cite("1")},
            {"node_id": "Tusi", "name": "Tusi", "birth_year": 1201, "death_year": 1274, "city": "Maragheh", "primary_work": "W", "source": _cite("2")},
            {"node_id": "T2", "name": "T2", "birth_year": 800, "death_year": 821, "city": "Baghdad", "primary_work": "W", "source": _cite("3")},
            {"node_id": "T3", "name": "T3", "birth_year": 801, "death_year": 860, "city": "Baghdad", "primary_work": "W", "source": _cite("4")},
            {"node_id": "S2", "name": "S2", "birth_year": 810, "death_year": 860, "city": "Baghdad", "primary_work": "W", "source": _cite("5")},
            {"node_id": "C3", "name": "C3", "birth_year": 807, "death_year": 860, "city": "Baghdad", "primary_work": "W", "source": _cite("6")},
            {"node_id": "ImmA", "name": "ImmA", "birth_year": 900, "death_year": 914, "city": "Baghdad", "primary_work": "W", "source": _cite("7")},
            {"node_id": "ImmS", "name": "ImmS", "birth_year": 850, "death_year": 864, "city": "Baghdad", "primary_work": "W", "source": _cite("8")},
            {"node_id": "Older", "name": "Older", "birth_year": 800, "death_year": 880, "city": "Baghdad", "primary_work": "W", "source": _cite("9")},
            {"node_id": "Younger", "name": "Younger", "birth_year": 801, "death_year": 860, "city": "Baghdad", "primary_work": "W", "source": _cite("10")},
            {"node_id": "DeadEarly", "name": "DeadEarly", "birth_year": 800, "death_year": 815, "city": "Baghdad", "primary_work": "W", "source": _cite("11")},
            {"node_id": "Subj801", "name": "Subj801", "birth_year": 801, "death_year": 850, "city": "Baghdad", "primary_work": "W", "source": _cite("12")},
        ]
        bad_chrono = bah.certify_polymath_lineage_graph(
            nodes_bad,
            [
                {"source": "Khw", "target": "Tusi", "relation": "critiqued", "citation": _cite("e1")},       # 850-death critiqued 1201-birth!
                {"source": "T2", "target": "S2", "relation": "teacher_of", "citation": _cite("e2")},         # overlap 821 < 822
                {"source": "T3", "target": "S2", "relation": "teacher_of", "citation": _cite("e3")},         # age gap 9 < 10
                {"source": "T2", "target": "C3", "relation": "corresponded_with", "citation": _cite("e4")},  # overlap 14 < 15
                {"source": "ImmA", "target": "Khw", "relation": "extended", "citation": _cite("e5")},        # actor age 14 < 15
                {"source": "Tusi", "target": "ImmS", "relation": "commented_on", "citation": _cite("e6")},   # subject age 14 < 15
                {"source": "Older", "target": "Younger", "relation": "critiqued", "citation": _cite("e7")},  # actor born 1 yr before subject
                {"source": "DeadEarly", "target": "Subj801", "relation": "extended", "citation": _cite("e8")},  # actor died at 815 < 801+15=816
            ],
        )
        self.assertFalse(bad_chrono["certified"])
        self.assertIn("CHRONO_ACTOR_DIED_BEFORE_SUBJECT_MATURITY:Khw->Tusi", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_ACTOR_PRECEDES_SUBJECT:Khw->Tusi", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_TEACHER_OVERLAP:T2->S2", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_TEACHER_AGE_GAP:T3->S2", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_CORRESPONDENCE_NO_OVERLAP:T2<->C3", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_IMMATURE_ACTOR:ImmA->Khw", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_IMMATURE_SUBJECT:Tusi->ImmS", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_ACTOR_PRECEDES_SUBJECT:Older->Younger", bad_chrono["chronology_violations"])
        self.assertIn("CHRONO_ACTOR_DIED_BEFORE_SUBJECT_MATURITY:DeadEarly->Subj801", bad_chrono["chronology_violations"])

        # Exact directed cycle detection (A -> B and B -> A in influence order)
        bad_cycle = bah.certify_polymath_lineage_graph(
            nodes[:2],
            [
                {"source": "A", "target": "B", "relation": "commented_on", "citation": _cite("c1")},
                {"source": "B", "target": "A", "relation": "critiqued", "citation": _cite("c2")},
            ],
        )
        self.assertFalse(bad_cycle["certified"])
        self.assertFalse(bad_cycle["directed_dag_acyclic"])

        # Hard refusals (including mandatory citation enforcement!)
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-nodes-nonempty"):
            bah.certify_polymath_lineage_graph([], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-edges-seq"):
            bah.certify_polymath_lineage_graph(nodes, "bad")  # type: ignore[arg-type]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-node-dict:0"):
            bah.certify_polymath_lineage_graph(["bad"], [])  # type: ignore[list-item]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-node-keys:0"):
            bah.certify_polymath_lineage_graph([{"node_id": "A"}], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"citation-dict:node.source\[0\]"):
            bah.certify_polymath_lineage_graph([dict(nodes[0], source="string-not-dict")], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"citation-keys:node.source\[0\]"):
            bah.certify_polymath_lineage_graph([dict(nodes[0], source={"work": "W"})], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"clean-ascii:node_id\[0\]"):
            bah.certify_polymath_lineage_graph([dict(nodes[0], node_id=" A ")], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"clean-ascii:node_id\[0\]"):
            bah.certify_polymath_lineage_graph([dict(nodes[0], node_id="A\u200b")], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-lifespan-order:A"):
            bah.certify_polymath_lineage_graph([dict(nodes[0], birth_year=860, death_year=860)], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-duplicate-node:a"):
            bah.certify_polymath_lineage_graph([nodes[0], dict(nodes[1], node_id="a")], [])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-edge-dict:0"):
            bah.certify_polymath_lineage_graph(nodes, ["bad"])  # type: ignore[list-item]
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-edge-keys:0"):
            bah.certify_polymath_lineage_graph(nodes, [{"source": "A"}])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"exact-choice:edge.relation\[0\]"):
            bah.certify_polymath_lineage_graph(
                nodes, [{"source": "B", "target": "A", "relation": "invented", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"citation-dict:edge.citation\[0\]"):
            bah.certify_polymath_lineage_graph(
                nodes, [{"source": "B", "target": "A", "relation": "extended", "citation": "missing-struct"}]
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-unknown-source:Z"):
            bah.certify_polymath_lineage_graph(
                nodes, [{"source": "Z", "target": "B", "relation": "extended", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-unknown-target:Z"):
            bah.certify_polymath_lineage_graph(
                nodes, [{"source": "B", "target": "Z", "relation": "extended", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-self-loop:A"):
            bah.certify_polymath_lineage_graph(
                nodes, [{"source": "A", "target": "A", "relation": "extended", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-duplicate-edge"):
            e = {"source": "B", "target": "A", "relation": "extended", "citation": _cite("x")}
            bah.certify_polymath_lineage_graph(nodes, [e, e])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"lineage-duplicate-edge"):
            bah.certify_polymath_lineage_graph(
                nodes,
                [
                    {"source": "A", "target": "B", "relation": "corresponded_with", "citation": _cite("1")},
                    {"source": "B", "target": "A", "relation": "corresponded_with", "citation": _cite("2")},
                ],
            )

    def test_feedback_anti_epicycle_boundaries_and_refusals(self) -> None:
        ok_m1 = bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback())
        self.assertTrue(ok_m1["certified"])
        self.assertEqual(ok_m1["controller_regime"], "MONOTONE_CONVERGENT")

        bd_n1 = bah.certify_bounded_feedback_and_anti_epicycle(
            self._valid_feedback(epicycle_dof=1, held_out_constraints=1)
        )
        self.assertEqual(bd_n1["violations"], ["RUSHD_EPICYCLE_OVERPARAMETERIZED"])

        bad_in = bah.certify_bounded_feedback_and_anti_epicycle(
            self._valid_feedback(in_sample_error=Fraction(1, 5), null_baseline_error=Fraction(1, 5))
        )
        self.assertEqual(bad_in["violations"], ["RUSHD_IN_SAMPLE_WORSE_THAN_NULL"])

        ok_margin_bd = bah.certify_bounded_feedback_and_anti_epicycle(
            self._valid_feedback(setpoint_head=Fraction(10, 1), nominal_flow=Fraction(1, 1), valve_max_flow=Fraction(2, 1))
        )
        self.assertTrue(ok_margin_bd["certified"])
        self.assertEqual(ok_margin_bd["linear_head_margin"], "1/1")

        bad_sat = bah.certify_bounded_feedback_and_anti_epicycle(
            self._valid_feedback(
                setpoint_head=Fraction(1000, 1),
                nominal_flow=Fraction(1, 1_000_000),
                valve_max_flow=Fraction(2, 1_000_000),
                valve_gain_kappa=Fraction(1, 2),
            )
        )
        self.assertFalse(bad_sat["certified"])
        self.assertEqual(bad_sat["violations"], ["JAZARI_VALVE_SATURATION_HEADROOM_TOO_SMALL"])

        ok_osc = bah.certify_bounded_feedback_and_anti_epicycle(
            self._valid_feedback(valve_gain_kappa=Fraction(3, 2))
        )
        self.assertTrue(ok_osc["certified"])
        self.assertEqual(ok_osc["controller_regime"], "DAMPED_OSCILLATORY")

        bad_null = bah.certify_bounded_feedback_and_anti_epicycle(
            self._valid_feedback(null_baseline_error=Fraction(1, 10))
        )
        self.assertEqual(bad_null["violations"], ["RUSHD_VACUOUS_NULL_BASELINE"])

        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-spec-dict"):
            bah.certify_bounded_feedback_and_anti_epicycle([])
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-spec-keys"):
            bah.certify_bounded_feedback_and_anti_epicycle({"epicycle_dof": 1})
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-dof-pos"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(epicycle_dof=0))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-held-out-pos"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(held_out_constraints=0))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-err-range"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(in_sample_error=Fraction(-1, 10)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-err-range"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(held_out_error=Fraction(-1, 10)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-err-range"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(max_held_out_error=Fraction(0, 1)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-err-range"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(null_baseline_error=Fraction(-1, 10)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-phys-pos"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(valve_gain_kappa=Fraction(0, 1)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-phys-pos"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(step_dt=Fraction(0, 1)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-phys-pos"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(reservoir_area=Fraction(0, 1)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-phys-pos"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(setpoint_head=Fraction(0, 1)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-flow-bounds"):
            bah.certify_bounded_feedback_and_anti_epicycle(self._valid_feedback(nominal_flow=Fraction(0, 1)))
        with self.assertRaisesRegex(bah.PolymathAuditError, r"feedback-flow-bounds"):
            bah.certify_bounded_feedback_and_anti_epicycle(
                self._valid_feedback(nominal_flow=Fraction(2, 1), valve_max_flow=Fraction(2, 1))
            )


class TestStandaloneCertificateAndCLI(unittest.TestCase):
    def test_deterministic_zero_float_json_and_cli(self) -> None:
        c1 = bah.build_certificate()
        c2 = bah.build_certificate()
        self.assertEqual(c1["certificate_sha256"], c2["certificate_sha256"])
        self.assertEqual(c1["novelty_classification"]["honest_tier"], "N0")
        self.assertEqual(c1["execution_mode"], "standalone_pure_q")

        def _reject_float(tok: str) -> None:
            raise AssertionError(f"float:{tok}")

        with tempfile.TemporaryDirectory() as tmp:
            out_p = Path(tmp) / "cert.json"
            buf_j = io.StringIO()
            with patch("sys.stdout", buf_j):
                rc_j = bah.main(["--json", "--write-cert", str(out_p)])
            self.assertEqual(rc_j, 0)
            written = out_p.read_text(encoding="utf-8")
            self.assertEqual(buf_j.getvalue(), written)
            parsed = json.loads(written, parse_float=_reject_float)
            self.assertEqual(parsed["certificate_sha256"], c1["certificate_sha256"])

            buf_h = io.StringIO()
            with patch("sys.stdout", buf_h):
                rc_h = bah.main([])
            self.assertEqual(rc_h, 0)
            self.assertIn(bah.AUDIT_ID, buf_h.getvalue())


if __name__ == "__main__":
    unittest.main()
