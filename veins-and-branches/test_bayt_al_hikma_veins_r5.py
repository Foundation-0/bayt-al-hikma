#!/usr/bin/env python3
"""R5 Mutation-Killing & Red-Team Verification Suite for AUDIT-095 (Bayt al-Hikma Veins & Branches)."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bayt_al_hikma_veins_certifier as bvh


class TestHelpersAndCoreMath(unittest.TestCase):
    def test_exact_primitives_and_refusals(self) -> None:
        self.assertEqual(bvh._require_exact_int(0, "z"), 0)
        self.assertEqual(bvh._require_exact_fraction(3, "i"), Fraction(3, 1))
        self.assertEqual(bvh._require_exact_fraction(Fraction(2, 3), "f"), Fraction(2, 3))
        self.assertEqual(bvh.frac_str(Fraction(4, 2)), "2/1")
        self.assertEqual(bvh.frac_dec(Fraction(-3, 2), 1), "-1.5")
        self.assertEqual(bvh.frac_dec(Fraction(1, 4), 2), "0.25")
        self.assertEqual(bvh._isqrt_scaled_bounds(0, 1, 10), (0, 0))
        self.assertEqual(bvh._isqrt_scaled_bounds(4, 1, 10), (20, 20))
        self.assertEqual(bvh._isqrt_scaled_bounds(2, 1, 10), (14, 15))
        self.assertEqual(bvh._to_sexagesimal_digits(Fraction(0, 1), 1), [0])
        self.assertEqual(bvh._to_sexagesimal_digits(Fraction(59, 60), 1), [59])
        self.assertEqual(bvh._sexagesimal_to_fraction(1, [0, 59]), Fraction(3659, 3600))

        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-int:b"):
            bvh._require_exact_int(True, "b")
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-fraction:fl"):
            bvh._require_exact_fraction(Fraction(1, 2).numerator / 2, "fl")
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-fraction:bl"):
            bvh._require_exact_fraction(False, "bl")
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"digits-pos"):
            bvh.frac_dec(Fraction(1, 2), 0)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"isqrt-bounds-domain"):
            bvh._isqrt_scaled_bounds(-1, 1, 10)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"isqrt-bounds-domain"):
            bvh._isqrt_scaled_bounds(1, 0, 10)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"isqrt-bounds-domain"):
            bvh._isqrt_scaled_bounds(1, 1, 0)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-domain"):
            bvh._to_sexagesimal_digits(Fraction(-1, 60), 1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-domain"):
            bvh._to_sexagesimal_digits(Fraction(1, 1), 1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-domain"):
            bvh._to_sexagesimal_digits(Fraction(1, 2), 0)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-digit-range"):
            bvh._sexagesimal_to_fraction(0, [-1])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-digit-range"):
            bvh._sexagesimal_to_fraction(0, [60])

    def test_chakravala_archimedes_and_cent_boundaries(self) -> None:
        # Exact boundary D=2 (minimum allowed non-square D) -> (3, 2, 1)
        st2 = bvh.run_chakravala_exact(2)
        self.assertEqual(st2[-1], (3, 2, 1))
        # D=7 hits r0 == 0 branch? Check D=13 and D=29 and D=61
        st13 = bvh.run_chakravala_exact(13)
        self.assertEqual(st13[-1][0] ** 2 - 13 * st13[-1][1] ** 2, 1)
        st7 = bvh.run_chakravala_exact(7)
        self.assertEqual(st7[-1], (8, 3, 1))
        # D=10 has m0=3, 3^2-10=-1 -> absk=1 so r0 == 0 -> r0=absk=1!
        st10 = bvh.run_chakravala_exact(10)
        self.assertEqual(st10[-1], (19, 6, 1))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"chakravala-nonsquare-D"):
            bvh.run_chakravala_exact(1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"chakravala-nonsquare-D"):
            bvh.run_chakravala_exact(9)

        # Archimedes exact boundaries doublings=1, scale_exp=12
        arch1 = bvh.archimedean_polygon_pi_bracket(1, 12)
        self.assertEqual(arch1["sides"], 12)
        self.assertTrue(arch1["pi_lo"] < Fraction(22, 7))
        self.assertTrue(arch1["pi_hi"] > Fraction(3, 1))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"archimedes-params"):
            bvh.archimedean_polygon_pi_bracket(0, 12)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"archimedes-params"):
            bvh.archimedean_polygon_pi_bracket(1, 11)

        # Exact cent floor boundaries 1/1 -> 0, 2/1 -> 1200
        self.assertEqual(bvh.exact_cent_floor(Fraction(1, 1)), 0)
        self.assertEqual(bvh.exact_cent_floor(Fraction(2, 1)), 1200)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"ratio-octave-range"):
            bvh.exact_cent_floor(Fraction(99, 100))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"ratio-octave-range"):
            bvh.exact_cent_floor(Fraction(201, 100))


class TestFourMathematicalPillars(unittest.TestCase):
    def test_pillar1_tributaries(self) -> None:
        p1 = bvh.analyze_pillar1_tributary_veins()
        bq = p1["brahmagupta_cyclic_quadrilateral"]
        self.assertEqual(bq["area_exact"], "1764/1")
        self.assertTrue(bq["area_formula_exact"])
        self.assertTrue(bq["diagonal_formulas_exact"])
        self.assertTrue(bq["ptolemy_identity_exact"])
        self.assertTrue(bq["circumdiameter_sq_both_pairs_65sq"])
        self.assertEqual(bq["perpendicular_bisector_dot"], "0/1")

        bh = p1["brahmagupta_bhavana_and_chakravala"]
        self.assertTrue(bh["bhavana_norm_multiplicativity_exact"])
        self.assertEqual(bh["pell_D92_fundamental"], [1151, 120])
        self.assertTrue(bh["pell_D92_verified"])
        self.assertEqual(bh["pell_D61_fundamental"], [1766319049, 226153980])
        self.assertTrue(bh["pell_D61_verified"])

        gr = p1["greek_syriac_baghdad_veins"]
        self.assertTrue(gr["heron_area_84_exact"])
        self.assertTrue(gr["heron_sqrt720_certified"])
        self.assertTrue(gr["archimedes_223_71_to_22_7_nested"])
        self.assertTrue(gr["apollonius_on_ellipse"])
        self.assertTrue(gr["apollonius_focal_sum_10_exact"])
        self.assertTrue(gr["apollonius_equal_angle_reflection_exact"])

    def test_pillar2_shatir_copernicus_and_ghazali_rushd(self) -> None:
        p2 = bvh.analyze_pillar2_shatir_copernicus_and_ghazali_rushd()
        sc = p2["shatir_copernicus_lunar_and_mercury"]
        self.assertEqual(sc["ptolemy_distance_ratio"], "3915/2047")
        self.assertEqual(sc["shatir_distance_ratio"], "17/13")
        self.assertEqual(sc["copernicus_distance_ratio"], "5667/4333")
        self.assertEqual(sc["published_param_l1_diff"], "1/9000")
        self.assertTrue(sc["normalized_lunar_vector_zero_residual"])
        self.assertTrue(sc["mercury_tusi_couple_zero_residual"])
        self.assertTrue(sc["eliminates_ptolemy_distance_artifact"])

        gr = p2["ghazali_rushd_causal_witness"]
        self.assertEqual(gr["observational_l1_distance"], "0/1")
        self.assertEqual(gr["ate_rushd_direct_mechanism"], "9/25")
        self.assertEqual(gr["ate_ghazali_confounded_iqtiran"], "0/1")
        self.assertTrue(gr["ghazali_nonidentifiability_certified"])
        self.assertTrue(gr["rushd_intervention_separates_models"])

    def test_pillar3_kashi(self) -> None:
        p3 = bvh.analyze_pillar3_kashi_banach_and_pi()
        kb = p3["kashi_banach_sin1_cubic"]
        self.assertEqual(kb["lipschitz_constant_exact"], "1/625")
        self.assertTrue(kb["first_9_sexagesimal_places_exact_match"])
        self.assertTrue(kb["max_diff_from_kashi_1427_lt_1e17"])
        self.assertTrue(kb["cubic_residual_lt_1e18"])

        kp = p3["kashi_3_times_2_28_gon_pi"]
        self.assertEqual(kp["polygon_sides"], 805306368)
        self.assertTrue(kp["kashi_1424_value_strictly_inside_3x2_28_bracket"])
        self.assertTrue(kp["agrees_to_16_decimal_digits"])
        self.assertTrue(kp["bracket_width_lt_1e16"])

    def test_pillar4_farabi(self) -> None:
        p4 = bvh.analyze_pillar4_farabi_acoustic_continuum()
        self.assertTrue(p4["zalzal_product_9_8_times_12_11_exact"])
        self.assertTrue(p4["farabi_tetrachord_4_3_exact"])
        self.assertTrue(p4["superparticular_tetrachord_4_3_exact"])
        self.assertEqual(p4["pythagorean_comma"], "531441/524288")
        self.assertTrue(p4["pythagorean_comma_gt_1"])
        self.assertTrue(p4["neutral_third_27_22_defect_ge_45c"])
        self.assertTrue(p4["three_quarter_12_11_defect_ge_49c"])
        self.assertTrue(p4["western_fifth_3_2_defect_le_2c"])
        for row in p4["intervals"].values():
            self.assertFalse(row["exact_in_12tet"])

    def test_pillar5_receipts(self) -> None:
        p5 = bvh.analyze_pillar5_lineage_and_certifiers()
        dag = p5["extended_lineage_dag_receipt"]
        self.assertTrue(dag["certified"])
        self.assertEqual(dag["node_count"], 23)
        self.assertEqual(dag["edge_count"], 28)
        self.assertEqual(dag["tier_counts"], {"tributary": 4, "core": 15, "branch": 4})
        self.assertTrue(dag["directed_dag_acyclic"])
        self.assertTrue(dag["reaches_branch_from_tributary_via_core"])
        self.assertTrue(p5["certified_kashi_banach_and_ghazali_rushd"]["certified"])
        self.assertFalse(p5["rejected_noncontractive_and_unseparated"]["certified"])
        self.assertEqual(
            p5["rejected_noncontractive_and_unseparated"]["violations"],
            [
                "KASHI_NON_CONTRACTIVE_MAP",
                "GHAZALI_OBS_MODELS_NOT_EQUIVALENT",
                "RUSHD_INTERVENTION_UNSEPARATED",
            ],
        )


class TestRedTeamExtendedDagCertifier(unittest.TestCase):
    def _three_tier_nodes(self) -> list[dict[str, object]]:
        return [
            {
                "node_id": "T1",
                "name": "Tributary One",
                "birth_year": 600,
                "death_year": 750,
                "tier": "tributary",
                "city": "Bhillamala",
                "primary_work": "Work T1",
            },
            {
                "node_id": "C1",
                "name": "Core One",
                "birth_year": 750,
                "death_year": 810,
                "tier": "core",
                "city": "Baghdad",
                "primary_work": "Work C1",
            },
            {
                "node_id": "C2",
                "name": "Core Two",
                "birth_year": 760,
                "death_year": 820,
                "tier": "core",
                "city": "Baghdad",
                "primary_work": "Work C2",
            },
            {
                "node_id": "C3",
                "name": "Core Three",
                "birth_year": 1150,
                "death_year": 1210,
                "tier": "core",
                "city": "Cordoba",
                "primary_work": "Work C3",
            },
            {
                "node_id": "B1",
                "name": "Branch One",
                "birth_year": 1200,
                "death_year": 1270,
                "tier": "branch",
                "city": "Maragheh",
                "primary_work": "Work B1",
            },
        ]

    def test_valid_closed_boundaries_and_epoch_tier_violations(self) -> None:
        # Exact closed epoch boundaries: tributary death==750, core birth==750 & 1150, branch birth==1200
        nodes = self._three_tier_nodes()
        ok = bvh.certify_extended_polymath_dag(
            nodes,
            [
                {"source": "T1", "target": "C1", "relation": "extended"},
                {"source": "C1", "target": "C2", "relation": "teacher_of"},
                {"source": "C1", "target": "C2", "relation": "corresponded_with"},
                {"source": "C2", "target": "C3", "relation": "extended"},
                {"source": "C3", "target": "B1", "relation": "extended"},
            ],
        )
        self.assertTrue(ok["certified"])

        # Exact closed maturity boundaries: teacher (750-772 -> 760-810), corr overlap == 15,
        # influence s_birth+15 == d_death AND d_birth+15 == d_death
        bd_nodes = [
            {"node_id": "T", "name": "T", "birth_year": 600, "death_year": 650, "tier": "tributary", "city": "A", "primary_work": "W"},
            {"node_id": "CT", "name": "CT", "birth_year": 800, "death_year": 822, "tier": "core", "city": "A", "primary_work": "W"},
            {"node_id": "CS", "name": "CS", "birth_year": 810, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W"},
            {"node_id": "CC", "name": "CC", "birth_year": 807, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W"},
            {"node_id": "CI", "name": "CI", "birth_year": 800, "death_year": 815, "tier": "core", "city": "A", "primary_work": "W"},
            {"node_id": "B", "name": "B", "birth_year": 1200, "death_year": 1250, "tier": "branch", "city": "A", "primary_work": "W"},
        ]
        ok_bd = bvh.certify_extended_polymath_dag(
            bd_nodes,
            [
                {"source": "T", "target": "CT", "relation": "extended"},
                {"source": "CT", "target": "CS", "relation": "teacher_of"},
                {"source": "CT", "target": "CC", "relation": "corresponded_with"},  # 822 - 807 == 15
                {"source": "CT", "target": "CI", "relation": "commented_on"},       # 800+15 == 815
                {"source": "CS", "target": "B", "relation": "extended"},
            ],
        )
        self.assertTrue(ok_bd["certified"])

        # Epoch violations (1 year outside closed epoch bounds) + disconnected path
        bad_epoch = bvh.certify_extended_polymath_dag(
            [
                {"node_id": "Tlate", "name": "T", "birth_year": 600, "death_year": 751, "tier": "tributary", "city": "A", "primary_work": "W"},
                {"node_id": "Cearly", "name": "C", "birth_year": 749, "death_year": 800, "tier": "core", "city": "A", "primary_work": "W"},
                {"node_id": "Clate", "name": "C2", "birth_year": 1151, "death_year": 1200, "tier": "core", "city": "A", "primary_work": "W"},
                {"node_id": "Bearly", "name": "B", "birth_year": 1199, "death_year": 1250, "tier": "branch", "city": "A", "primary_work": "W"},
            ],
            [],
        )
        self.assertFalse(bad_epoch["certified"])
        self.assertEqual(
            bad_epoch["tier_violations"],
            [
                "EPOCH_TRIBUTARY_LATE:Tlate",
                "EPOCH_CORE_OUT_OF_RANGE:Cearly",
                "EPOCH_CORE_OUT_OF_RANGE:Clate",
                "EPOCH_BRANCH_EARLY:Bearly",
                "LINEAGE_NO_TRIBUTARY_CORE_BRANCH_PATH",
            ],
        )

        # Tier backward flow, cross-era correspondence, and ALL isolated 1-yr-under chronology fails
        bad_rel = bvh.certify_extended_polymath_dag(
            [
                {"node_id": "T", "name": "T", "birth_year": 680, "death_year": 740, "tier": "tributary", "city": "A", "primary_work": "W"},
                {"node_id": "C1", "name": "C1", "birth_year": 800, "death_year": 821, "tier": "core", "city": "A", "primary_work": "W"},
                {"node_id": "C2", "name": "C2", "birth_year": 801, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W"},
                {"node_id": "C3", "name": "C3", "birth_year": 810, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W"},
                {"node_id": "C4", "name": "C4", "birth_year": 807, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W"},
                {"node_id": "C5", "name": "C5", "birth_year": 801, "death_year": 815, "tier": "core", "city": "A", "primary_work": "W"},
                {"node_id": "B", "name": "B", "birth_year": 1201, "death_year": 1274, "tier": "branch", "city": "A", "primary_work": "W"},
            ],
            [
                {"source": "T", "target": "C1", "relation": "extended"},
                {"source": "C3", "target": "B", "relation": "extended"},
                {"source": "C1", "target": "C3", "relation": "teacher_of"},      # 810+12=822 > 821
                {"source": "C2", "target": "C3", "relation": "teacher_of"},      # 801+10=811 > 810
                {"source": "C1", "target": "C4", "relation": "corresponded_with"},  # 821-807=14 < 15
                {"source": "B", "target": "C3", "relation": "extended"},         # backward tier + anachronistic
                {"source": "C1", "target": "C5", "relation": "commented_on"},    # target immature 801+15=816 > 815
                {"source": "T", "target": "C1", "relation": "corresponded_with"},  # cross-era corr
            ],
        )
        self.assertFalse(bad_rel["certified"])
        self.assertIn("TIER_BACKWARD_FLOW:B->C3", bad_rel["tier_violations"])
        self.assertIn("TIER_CROSS_ERA_CORRESPONDENCE:T<->C1", bad_rel["tier_violations"])
        self.assertIn("CHRONO_TEACHER_OVERLAP:C1->C3", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_TEACHER_AGE_GAP:C2->C3", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_CORRESPONDENCE_NO_OVERLAP:C1<->C4", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_ANACHRONISTIC_INFLUENCE:B->C3", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_IMMATURE_TARGET:C1->C5", bad_rel["chronology_violations"])

        # Directed cycle detection
        bad_cyc = bvh.certify_extended_polymath_dag(
            nodes,
            [
                {"source": "T1", "target": "C1", "relation": "extended"},
                {"source": "C1", "target": "C2", "relation": "extended"},
                {"source": "C2", "target": "C1", "relation": "critiqued"},
                {"source": "C2", "target": "B1", "relation": "extended"},
            ],
        )
        self.assertFalse(bad_cyc["certified"])
        self.assertFalse(bad_cyc["directed_dag_acyclic"])

        # Hard refusals
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-nodes-nonempty"):
            bvh.certify_extended_polymath_dag([], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-edges-seq"):
            bvh.certify_extended_polymath_dag(nodes, "bad")  # type: ignore[arg-type]
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-node-dict:0"):
            bvh.certify_extended_polymath_dag(["bad"], [])  # type: ignore[list-item]
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-node-keys:0"):
            bvh.certify_extended_polymath_dag([{"node_id": "X"}], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"clean-ascii:node_id\[0\]"):
            bvh.certify_extended_polymath_dag([dict(nodes[0], node_id=" T1 ")], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-choice:tier\[0\]"):
            bvh.certify_extended_polymath_dag([dict(nodes[0], tier="unknown")], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-lifespan-order:T1"):
            bvh.certify_extended_polymath_dag([dict(nodes[0], birth_year=700, death_year=700)], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-duplicate-node:t1"):
            bvh.certify_extended_polymath_dag([nodes[0], dict(nodes[1], node_id="t1")], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-edge-dict:0"):
            bvh.certify_extended_polymath_dag(nodes, ["bad"])  # type: ignore[list-item]
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-edge-keys:0"):
            bvh.certify_extended_polymath_dag(nodes, [{"source": "T1"}])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-choice:edge.relation\[0\]"):
            bvh.certify_extended_polymath_dag(nodes, [{"source": "T1", "target": "C1", "relation": "bad"}])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-unknown-source:Z"):
            bvh.certify_extended_polymath_dag(nodes, [{"source": "Z", "target": "C1", "relation": "extended"}])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-unknown-target:Z"):
            bvh.certify_extended_polymath_dag(nodes, [{"source": "T1", "target": "Z", "relation": "extended"}])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-self-loop:T1"):
            bvh.certify_extended_polymath_dag(nodes, [{"source": "T1", "target": "T1", "relation": "extended"}])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-duplicate-edge"):
            e = {"source": "T1", "target": "C1", "relation": "extended"}
            bvh.certify_extended_polymath_dag(nodes, [e, e])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-duplicate-edge"):
            bvh.certify_extended_polymath_dag(
                nodes,
                [
                    {"source": "C1", "target": "C2", "relation": "corresponded_with"},
                    {"source": "C2", "target": "C1", "relation": "corresponded_with"},
                ],
            )


class TestRedTeamUnifiedBanachAndCausalCertifier(unittest.TestCase):
    def _valid_spec(self, **overrides: object) -> dict[str, object]:
        joint = {
            "p11": Fraction(17, 50),
            "p10": Fraction(4, 25),
            "p01": Fraction(4, 25),
            "p00": Fraction(17, 50),
        }
        base: dict[str, object] = {
            "domain_lo": Fraction(0, 1),
            "domain_hi": Fraction(2, 1),
            "x0": Fraction(1, 1),
            "lipschitz_L": Fraction(1, 2),
            "step0_gap": Fraction(1, 2),
            "iterations": 1,
            "target_tol": Fraction(1, 2),  # exact boundary: (1/2)^1 * (1/2) / (1/2) == 1/2
            "obs_joint_direct": dict(joint),
            "obs_joint_confounded": dict(joint),
            "confounder_p_u1": Fraction(1, 2),
            "confounder_p_f_given_u1": Fraction(4, 5),
            "confounder_p_f_given_u0": Fraction(1, 5),
            "confounder_p_c_given_u1": Fraction(4, 5),
            "confounder_p_c_given_u0": Fraction(1, 5),
            "min_ate_separation": Fraction(9, 25),  # exact boundary: ate_sep == 9/25
        }
        base.update(overrides)
        return base

    def test_boundaries_and_violations(self) -> None:
        # Exact closed boundaries: ball_radius == 1 hits BOTH dom_lo=0 and dom_hi=2,
        # a_priori == target_tol == 1/2, ate_sep == min_sep == 9/25, iterations == 1
        ok = bvh.certify_contraction_and_causal_identifiability(self._valid_spec())
        self.assertTrue(ok["certified"])
        self.assertEqual(ok["banach_ball_radius"], "1/1")
        self.assertEqual(ok["banach_a_priori_error"], "1/2")

        # Exact closed boundary L == 0, x0 == domain_lo (with ball_radius == 0? step0_gap > 0 so test L=0)
        ok_l0 = bvh.certify_contraction_and_causal_identifiability(
            self._valid_spec(lipschitz_L=Fraction(0, 1), step0_gap=Fraction(1, 1))
        )
        self.assertTrue(ok_l0["certified"])
        self.assertEqual(ok_l0["banach_a_priori_error"], "0/1")

        # Exact closed boundary pf_u1=1, pf_u0=0, pc_u1=1, pc_u0=0, min_sep=1/1 -> joint (1/2, 0, 0, 1/2), ATE=1!
        det_joint = {
            "p11": Fraction(1, 2),
            "p10": Fraction(0, 1),
            "p01": Fraction(0, 1),
            "p00": Fraction(1, 2),
        }
        ok_det = bvh.certify_contraction_and_causal_identifiability(
            self._valid_spec(
                obs_joint_direct=det_joint,
                obs_joint_confounded=det_joint,
                confounder_p_f_given_u1=Fraction(1, 1),
                confounder_p_f_given_u0=Fraction(0, 1),
                confounder_p_c_given_u1=Fraction(1, 1),
                confounder_p_c_given_u0=Fraction(0, 1),
                min_ate_separation=Fraction(1, 1),
            )
        )
        self.assertTrue(ok_det["certified"])
        self.assertEqual(ok_det["ate_separation"], "1/1")

        # Symmetric closed boundary pf_u1=0, pf_u0=1, pc_u1=0, pc_u0=1 -> identical joint, ATE=1!
        ok_det_flip = bvh.certify_contraction_and_causal_identifiability(
            self._valid_spec(
                obs_joint_direct=det_joint,
                obs_joint_confounded=det_joint,
                confounder_p_f_given_u1=Fraction(0, 1),
                confounder_p_f_given_u0=Fraction(1, 1),
                confounder_p_c_given_u1=Fraction(0, 1),
                confounder_p_c_given_u0=Fraction(1, 1),
                min_ate_separation=Fraction(1, 1),
            )
        )
        self.assertTrue(ok_det_flip["certified"])
        self.assertEqual(ok_det_flip["ate_separation"], "1/1")

        # x0 == domain_lo & x0 == domain_hi (allowed by domain check, triggers escape since ball_radius > 0!)
        esc_lo = bvh.certify_contraction_and_causal_identifiability(self._valid_spec(x0=Fraction(0, 1)))
        self.assertEqual(esc_lo["violations"], ["KASHI_ITERATES_ESCAPE_DOMAIN"])
        esc_hi = bvh.certify_contraction_and_causal_identifiability(self._valid_spec(x0=Fraction(2, 1)))
        self.assertEqual(esc_hi["violations"], ["KASHI_ITERATES_ESCAPE_DOMAIN"])

        # Tolerance not certified (a_priori = 1/2 > 49/100)
        bad_tol = bvh.certify_contraction_and_causal_identifiability(
            self._valid_spec(target_tol=Fraction(49, 100))
        )
        self.assertEqual(bad_tol["violations"], ["KASHI_TOLERANCE_NOT_CERTIFIED"])

        # Spoofed confounded joint mismatch
        spoof_joint = {
            "p11": Fraction(1, 4),
            "p10": Fraction(1, 4),
            "p01": Fraction(1, 4),
            "p00": Fraction(1, 4),
        }
        bad_spoof = bvh.certify_contraction_and_causal_identifiability(
            self._valid_spec(obs_joint_direct=spoof_joint, obs_joint_confounded=spoof_joint)
        )
        self.assertEqual(
            bad_spoof["violations"],
            ["GHAZALI_CONFOUNDED_JOINT_MISMATCH", "RUSHD_INTERVENTION_UNSEPARATED"],
        )

        # Hard refusals
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"unified-spec-dict"):
            bvh.certify_contraction_and_causal_identifiability([])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"unified-spec-keys"):
            bvh.certify_contraction_and_causal_identifiability({"domain_lo": 0})
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"banach-domain-order"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(domain_lo=Fraction(2, 1)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"banach-x0-in-domain"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(x0=Fraction(-1, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"banach-x0-in-domain"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(x0=Fraction(21, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"banach-L-nonneg"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(lipschitz_L=Fraction(-1, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"banach-step0-pos"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(step0_gap=Fraction(0, 1)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"banach-iters-pos"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(iterations=0))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"banach-tol-pos"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(target_tol=Fraction(0, 1)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"joint-dict"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(obs_joint_direct=[]))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"joint-keys"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(obs_joint_direct={"p11": 1}))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"joint-nonneg"):
            bvh.certify_contraction_and_causal_identifiability(
                self._valid_spec(
                    obs_joint_direct={"p11": Fraction(-1, 4), "p10": Fraction(3, 4), "p01": Fraction(1, 4), "p00": Fraction(1, 4)}
                )
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"joint-sum-one"):
            bvh.certify_contraction_and_causal_identifiability(
                self._valid_spec(
                    obs_joint_direct={"p11": Fraction(1, 4), "p10": Fraction(1, 4), "p01": Fraction(1, 4), "p00": Fraction(1, 2)}
                )
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pu1-open"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_u1=Fraction(0, 1)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pu1-open"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_u1=Fraction(1, 1)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pf-u1-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_f_given_u1=Fraction(-1, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pf-u1-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_f_given_u1=Fraction(11, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pf-u0-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_f_given_u0=Fraction(-1, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pf-u0-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_f_given_u0=Fraction(11, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pc-u1-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_c_given_u1=Fraction(-1, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pc-u1-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_c_given_u1=Fraction(11, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pc-u0-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_c_given_u0=Fraction(-1, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-pc-u0-prob"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(confounder_p_c_given_u0=Fraction(11, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-min-sep-range"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(min_ate_separation=Fraction(0, 1)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-min-sep-range"):
            bvh.certify_contraction_and_causal_identifiability(self._valid_spec(min_ate_separation=Fraction(11, 10)))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-marginal-degenerate"):
            bvh.certify_contraction_and_causal_identifiability(
                self._valid_spec(
                    obs_joint_direct={"p11": Fraction(0, 1), "p10": Fraction(0, 1), "p01": Fraction(1, 2), "p00": Fraction(1, 2)}
                )
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"causal-marginal-degenerate"):
            bvh.certify_contraction_and_causal_identifiability(
                self._valid_spec(
                    obs_joint_direct={"p11": Fraction(1, 2), "p10": Fraction(1, 2), "p01": Fraction(0, 1), "p00": Fraction(0, 1)}
                )
            )


class TestVaultAnchorsAndCLI(unittest.TestCase):
    def test_vault_verifier_tamper_symlink_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "symbiosis"
            with self.assertRaisesRegex(bvh.VeinsAuditError, r"symbiosis-root-missing"):
                bvh.audit_live_vault_anchors(root)

            root.mkdir()
            digests: dict[str, dict[str, object]] = {}
            for rel, meta in bvh.PINNED_VAULT_DIGESTS.items():
                p = root / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("content\n", encoding="utf-8")
                raw = p.read_bytes()
                digests[rel] = {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "role": meta["role"],
                }

            with patch.object(bvh, "PINNED_VAULT_DIGESTS", digests):
                ok = bvh.audit_live_vault_anchors(root)
                self.assertEqual(ok["verified_vault_anchors"], 3)

            first_rel = next(iter(digests))
            target = root / first_rel
            outside = Path(tmp) / "escape.txt"
            outside.write_text("content\n", encoding="utf-8")
            target.unlink()
            target.symlink_to(outside)
            with patch.object(bvh, "PINNED_VAULT_DIGESTS", digests):
                with self.assertRaisesRegex(bvh.VeinsAuditError, r"vault-path-escape"):
                    bvh.audit_live_vault_anchors(root)
            target.unlink()
            with patch.object(bvh, "PINNED_VAULT_DIGESTS", digests):
                with self.assertRaisesRegex(bvh.VeinsAuditError, r"vault-file-missing"):
                    bvh.audit_live_vault_anchors(root)

            target.write_text("Content\n", encoding="utf-8")
            with patch.object(bvh, "PINNED_VAULT_DIGESTS", digests):
                with self.assertRaisesRegex(bvh.VeinsAuditError, r"vault-sha256-mismatch"):
                    bvh.audit_live_vault_anchors(root)
            target.write_text("content!!\n", encoding="utf-8")
            with patch.object(bvh, "PINNED_VAULT_DIGESTS", digests):
                with self.assertRaisesRegex(bvh.VeinsAuditError, r"vault-bytes-mismatch"):
                    bvh.audit_live_vault_anchors(root)

            # Standalone zero-float JSON & CLI
            c1 = bvh.build_certificate(symbiosis_root=None)
            c2 = bvh.build_certificate(symbiosis_root=None)
            self.assertEqual(c1["certificate_sha256"], c2["certificate_sha256"])

            def _reject_float(tok: str) -> None:
                raise AssertionError(f"float:{tok}")

            out_p = Path(tmp) / "cert.json"
            buf_j = io.StringIO()
            with patch("sys.stdout", buf_j):
                rc_j = bvh.main(["--json", "--write-cert", str(out_p)])
            self.assertEqual(rc_j, 0)
            written = out_p.read_text(encoding="utf-8")
            self.assertEqual(buf_j.getvalue(), written)
            parsed = json.loads(written, parse_float=_reject_float)
            self.assertEqual(parsed["audit_id"], "AUDIT-095")

            buf_h = io.StringIO()
            with patch("sys.stdout", buf_h):
                rc_h = bvh.main([])
            self.assertEqual(rc_h, 0)
            self.assertIn("AUDIT-095 | mode=standalone_pure_math", buf_h.getvalue())


if __name__ == "__main__":
    unittest.main()
