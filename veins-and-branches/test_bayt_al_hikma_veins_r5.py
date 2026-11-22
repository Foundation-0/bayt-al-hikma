#!/usr/bin/env python3
"""R5 Mutation-Killing & Red-Team Verification Suite for AUDIT-095R (Bayt al-Hikma Veins & Branches)."""

from __future__ import annotations

from fractions import Fraction
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bayt_al_hikma_veins_certifier as bvh


def _cite(tag: str = "Ref") -> dict[str, str]:
    return {"work": f"Work {tag}", "edition": "Ed. 2000", "location": "p. 1"}


class TestHelpersAndCoreMath(unittest.TestCase):
    def test_exact_primitives_and_refusals(self) -> None:
        self.assertEqual(bvh._require_exact_int(0, "z"), 0)
        self.assertEqual(bvh._require_exact_fraction(3, "i"), Fraction(3, 1))
        self.assertEqual(bvh._require_exact_fraction(Fraction(2, 3), "f"), Fraction(2, 3))
        self.assertEqual(bvh.frac_str(Fraction(4, 2)), "2/1")
        self.assertEqual(bvh.frac_dec(Fraction(-3, 2), 1), "-1.5")
        self.assertEqual(bvh.frac_dec(Fraction(1, 4), 2), "0.25")
        self.assertEqual(bvh.frac_dec_ceil(Fraction(0, 1), 1), "0.0")
        self.assertEqual(bvh.frac_dec_ceil(Fraction(1, 200), 2), "0.01")
        self.assertEqual(bvh._isqrt_scaled_bounds(0, 1, 10), (0, 0))
        self.assertEqual(bvh._isqrt_scaled_bounds(4, 1, 10), (20, 20))
        self.assertEqual(bvh._isqrt_scaled_bounds(2, 1, 10), (14, 15))
        self.assertEqual(bvh._to_sexagesimal_digits(Fraction(0, 1), 1), [0])
        self.assertEqual(bvh._to_sexagesimal_digits(Fraction(59, 60), 1), [59])
        self.assertEqual(bvh._to_sexagesimal_digits_ceil(Fraction(0, 1), 1), [0])
        self.assertEqual(bvh._to_sexagesimal_digits_ceil(Fraction(1, 120), 1), [1])
        self.assertEqual(bvh._to_sexagesimal_digits_ceil(Fraction(59, 60), 1), [59])
        self.assertEqual(bvh._sexagesimal_to_fraction(1, [0, 59]), Fraction(3659, 3600))

        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-int:b"):
            bvh._require_exact_int(True, "b")
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-fraction:fl"):
            bvh._require_exact_fraction(Fraction(1, 2).numerator / 2, "fl")
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-fraction:bl"):
            bvh._require_exact_fraction(False, "bl")
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"digits-pos"):
            bvh.frac_dec(Fraction(1, 2), 0)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"frac-dec-ceil-domain"):
            bvh.frac_dec_ceil(Fraction(-1, 2), 1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"frac-dec-ceil-domain"):
            bvh.frac_dec_ceil(Fraction(1, 2), 0)
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
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-ceil-domain"):
            bvh._to_sexagesimal_digits_ceil(Fraction(-1, 60), 1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-ceil-domain"):
            bvh._to_sexagesimal_digits_ceil(Fraction(1, 1), 1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-ceil-domain"):
            bvh._to_sexagesimal_digits_ceil(Fraction(1, 2), 0)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-ceil-overflow"):
            bvh._to_sexagesimal_digits_ceil(Fraction(119, 120), 1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-digit-range"):
            bvh._sexagesimal_to_fraction(0, [-1])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"sex-digit-range"):
            bvh._sexagesimal_to_fraction(0, [60])

    def test_chakravala_archimedes_and_cent_boundaries(self) -> None:
        st2 = bvh.run_chakravala_exact(2)
        self.assertEqual(st2[-1], (3, 2, 1))
        st13 = bvh.run_chakravala_exact(13)
        self.assertEqual(st13[-1][0] ** 2 - 13 * st13[-1][1] ** 2, 1)
        st7 = bvh.run_chakravala_exact(7)
        self.assertEqual(st7[-1], (8, 3, 1))
        st10 = bvh.run_chakravala_exact(10)
        self.assertEqual(st10[-1], (19, 6, 1))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"chakravala-nonsquare-D"):
            bvh.run_chakravala_exact(1)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"chakravala-nonsquare-D"):
            bvh.run_chakravala_exact(9)

        arch1 = bvh.archimedean_polygon_pi_bracket(1, 12)
        self.assertEqual(arch1["sides"], 12)
        self.assertTrue(arch1["pi_lo"] < Fraction(22, 7))
        self.assertTrue(arch1["pi_hi"] > Fraction(3, 1))
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"archimedes-params"):
            bvh.archimedean_polygon_pi_bracket(0, 12)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"archimedes-params"):
            bvh.archimedean_polygon_pi_bracket(1, 11)

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
        self.assertEqual(bh["chakravala_D61_steps"], 13)
        self.assertEqual(bh["chakravala_D61_table_rows"], 14)
        self.assertEqual(bh["pell_D61_fundamental"], [1766319049, 226153980])
        self.assertTrue(bh["pell_D61_verified"])

        gr = p1["greek_syriac_baghdad_veins"]
        self.assertTrue(gr["heron_area_84_exact"])
        self.assertTrue(gr["heron_sqrt720_certified"])
        self.assertEqual(gr["archimedes_96gon_bracket_dec6_conservative"], ["3.141031", "3.142715"])
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
        self.assertEqual(kp["twopi_hi_sexagesimal_ceil"][-1], 15)
        self.assertEqual(kp["base60_10place_floored_pi_width_e17"], "2.398")
        self.assertEqual(kp["base60_10place_floored_twopi_width_e17"], "4.796")
        self.assertEqual(kp["pi_exact_width_e17_ceil"], "2.416352")
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
        self.assertTrue(dag["encoding_consistency_only"])
        self.assertTrue(dag["all_nodes_and_edges_cited"])
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
                "source": _cite("T1"),
            },
            {
                "node_id": "C1",
                "name": "Core One",
                "birth_year": 750,
                "death_year": 810,
                "tier": "core",
                "city": "Baghdad",
                "primary_work": "Work C1",
                "source": _cite("C1"),
            },
            {
                "node_id": "C2",
                "name": "Core Two",
                "birth_year": 760,
                "death_year": 820,
                "tier": "core",
                "city": "Baghdad",
                "primary_work": "Work C2",
                "source": _cite("C2"),
            },
            {
                "node_id": "C3",
                "name": "Core Three",
                "birth_year": 1150,
                "death_year": 1210,
                "tier": "core",
                "city": "Cordoba",
                "primary_work": "Work C3",
                "source": _cite("C3"),
            },
            {
                "node_id": "B1",
                "name": "Branch One",
                "birth_year": 1200,
                "death_year": 1270,
                "tier": "branch",
                "city": "Maragheh",
                "primary_work": "Work B1",
                "source": _cite("B1"),
            },
        ]

    def test_valid_closed_boundaries_and_epoch_tier_violations(self) -> None:
        # Exact closed epoch boundaries & active-voice edges: C1 extended T1, C1 teacher_of C2, B1 extended C3
        nodes = self._three_tier_nodes()
        ok = bvh.certify_extended_polymath_dag(
            nodes,
            [
                {"source": "C1", "target": "T1", "relation": "extended", "citation": _cite("1")},
                {"source": "C1", "target": "C2", "relation": "teacher_of", "citation": _cite("2")},
                {"source": "C1", "target": "C2", "relation": "corresponded_with", "citation": _cite("3")},
                {"source": "C3", "target": "C2", "relation": "extended", "citation": _cite("4")},
                {"source": "B1", "target": "C3", "relation": "extended", "citation": _cite("5")},
            ],
        )
        self.assertTrue(ok["certified"])

        # Exact closed maturity boundaries: teacher (800-822 -> 810-860), corr overlap == 15,
        # active-voice commented_on: CI2(800-815) -> CI1(800-815) (all 4 engagement bounds tight!)
        bd_nodes = [
            {"node_id": "T", "name": "T", "birth_year": 600, "death_year": 650, "tier": "tributary", "city": "A", "primary_work": "W", "source": _cite("T")},
            {"node_id": "CT", "name": "CT", "birth_year": 800, "death_year": 822, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("CT")},
            {"node_id": "CS", "name": "CS", "birth_year": 810, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("CS")},
            {"node_id": "CC", "name": "CC", "birth_year": 807, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("CC")},
            {"node_id": "CI1", "name": "CI1", "birth_year": 800, "death_year": 815, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("CI1")},
            {"node_id": "CI2", "name": "CI2", "birth_year": 800, "death_year": 815, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("CI2")},
            {"node_id": "B", "name": "B", "birth_year": 1200, "death_year": 1250, "tier": "branch", "city": "A", "primary_work": "W", "source": _cite("B")},
        ]
        ok_bd = bvh.certify_extended_polymath_dag(
            bd_nodes,
            [
                {"source": "CT", "target": "T", "relation": "extended", "citation": _cite("1")},
                {"source": "CT", "target": "CS", "relation": "teacher_of", "citation": _cite("2")},
                {"source": "CT", "target": "CC", "relation": "corresponded_with", "citation": _cite("3")},
                {"source": "CI2", "target": "CI1", "relation": "commented_on", "citation": _cite("4")},
                {"source": "B", "target": "CS", "relation": "extended", "citation": _cite("5")},
            ],
        )
        self.assertTrue(ok_bd["certified"])

        # Epoch violations + disconnected path
        bad_epoch = bvh.certify_extended_polymath_dag(
            [
                {"node_id": "Tlate", "name": "T", "birth_year": 600, "death_year": 751, "tier": "tributary", "city": "A", "primary_work": "W", "source": _cite("1")},
                {"node_id": "Cearly", "name": "C", "birth_year": 749, "death_year": 800, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("2")},
                {"node_id": "Clate", "name": "C2", "birth_year": 1151, "death_year": 1200, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("3")},
                {"node_id": "Bearly", "name": "B", "birth_year": 1199, "death_year": 1250, "tier": "branch", "city": "A", "primary_work": "W", "source": _cite("4")},
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

        # Tier backward flow (both teacher_of and active-voice engagement!), cross-era corr,
        # review #6 repro (850-death critiqued 1201-birth!), and ALL isolated 1-yr-under chronology fails
        bad_rel = bvh.certify_extended_polymath_dag(
            [
                {"node_id": "T", "name": "T", "birth_year": 680, "death_year": 740, "tier": "tributary", "city": "A", "primary_work": "W", "source": _cite("T")},
                {"node_id": "Khw", "name": "Khw", "birth_year": 780, "death_year": 850, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("K")},
                {"node_id": "C1", "name": "C1", "birth_year": 800, "death_year": 821, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("1")},
                {"node_id": "C2", "name": "C2", "birth_year": 801, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("2")},
                {"node_id": "C3", "name": "C3", "birth_year": 810, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("3")},
                {"node_id": "C4", "name": "C4", "birth_year": 807, "death_year": 860, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("4")},
                {"node_id": "ImmA", "name": "ImmA", "birth_year": 900, "death_year": 914, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("5")},
                {"node_id": "ImmS", "name": "ImmS", "birth_year": 850, "death_year": 864, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("6")},
                {"node_id": "Dead815", "name": "Dead815", "birth_year": 800, "death_year": 815, "tier": "core", "city": "A", "primary_work": "W", "source": _cite("7")},
                {"node_id": "B", "name": "B", "birth_year": 1201, "death_year": 1274, "tier": "branch", "city": "A", "primary_work": "W", "source": _cite("B")},
            ],
            [
                {"source": "C1", "target": "T", "relation": "extended", "citation": _cite("e1")},
                {"source": "B", "target": "C3", "relation": "extended", "citation": _cite("e2")},
                {"source": "C1", "target": "C3", "relation": "teacher_of", "citation": _cite("e3")},
                {"source": "C2", "target": "C3", "relation": "teacher_of", "citation": _cite("e4")},
                {"source": "B", "target": "C3", "relation": "teacher_of", "citation": _cite("e5")},
                {"source": "C1", "target": "C4", "relation": "corresponded_with", "citation": _cite("e6")},
                {"source": "T", "target": "C1", "relation": "corresponded_with", "citation": _cite("e7")},
                {"source": "Khw", "target": "B", "relation": "critiqued", "citation": _cite("e8")},
                {"source": "ImmA", "target": "Khw", "relation": "extended", "citation": _cite("e9")},
                {"source": "B", "target": "ImmS", "relation": "commented_on", "citation": _cite("e10")},
                {"source": "Dead815", "target": "C2", "relation": "extended", "citation": _cite("e11")},
            ],
        )
        self.assertFalse(bad_rel["certified"])
        self.assertIn("TIER_BACKWARD_FLOW:B->C3", bad_rel["tier_violations"])
        self.assertIn("TIER_BACKWARD_FLOW:Khw->B", bad_rel["tier_violations"])
        self.assertIn("TIER_CROSS_ERA_CORRESPONDENCE:T<->C1", bad_rel["tier_violations"])
        self.assertIn("CHRONO_TEACHER_OVERLAP:C1->C3", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_TEACHER_AGE_GAP:C2->C3", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_CORRESPONDENCE_NO_OVERLAP:C1<->C4", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_ACTOR_DIED_BEFORE_SUBJECT_MATURITY:Khw->B", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_ACTOR_PRECEDES_SUBJECT:Khw->B", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_IMMATURE_ACTOR:ImmA->Khw", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_IMMATURE_SUBJECT:B->ImmS", bad_rel["chronology_violations"])
        self.assertIn("CHRONO_ACTOR_DIED_BEFORE_SUBJECT_MATURITY:Dead815->C2", bad_rel["chronology_violations"])

        # Directed cycle detection in influence order
        bad_cyc = bvh.certify_extended_polymath_dag(
            nodes,
            [
                {"source": "C1", "target": "T1", "relation": "extended", "citation": _cite("1")},
                {"source": "C2", "target": "C1", "relation": "extended", "citation": _cite("2")},
                {"source": "C1", "target": "C2", "relation": "critiqued", "citation": _cite("3")},
                {"source": "B1", "target": "C2", "relation": "extended", "citation": _cite("4")},
            ],
        )
        self.assertFalse(bad_cyc["certified"])
        self.assertFalse(bad_cyc["directed_dag_acyclic"])

        # Hard refusals (including mandatory citation enforcement)
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-nodes-nonempty"):
            bvh.certify_extended_polymath_dag([], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-edges-seq"):
            bvh.certify_extended_polymath_dag(nodes, "bad")  # type: ignore[arg-type]
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-node-dict:0"):
            bvh.certify_extended_polymath_dag(["bad"], [])  # type: ignore[list-item]
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-node-keys:0"):
            bvh.certify_extended_polymath_dag([{"node_id": "X"}], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"citation-dict:node.source\[0\]"):
            bvh.certify_extended_polymath_dag([dict(nodes[0], source="not-dict")], [])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"citation-keys:node.source\[0\]"):
            bvh.certify_extended_polymath_dag([dict(nodes[0], source={"work": "W"})], [])
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
            bvh.certify_extended_polymath_dag(nodes, [{"source": "C1"}])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"exact-choice:edge.relation\[0\]"):
            bvh.certify_extended_polymath_dag(
                nodes, [{"source": "C1", "target": "T1", "relation": "bad", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"citation-dict:edge.citation\[0\]"):
            bvh.certify_extended_polymath_dag(
                nodes, [{"source": "C1", "target": "T1", "relation": "extended", "citation": "not-dict"}]
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-unknown-source:Z"):
            bvh.certify_extended_polymath_dag(
                nodes, [{"source": "Z", "target": "T1", "relation": "extended", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-unknown-target:Z"):
            bvh.certify_extended_polymath_dag(
                nodes, [{"source": "C1", "target": "Z", "relation": "extended", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-self-loop:T1"):
            bvh.certify_extended_polymath_dag(
                nodes, [{"source": "T1", "target": "T1", "relation": "extended", "citation": _cite("x")}]
            )
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-duplicate-edge"):
            e = {"source": "C1", "target": "T1", "relation": "extended", "citation": _cite("x")}
            bvh.certify_extended_polymath_dag(nodes, [e, e])
        with self.assertRaisesRegex(bvh.VeinsAuditError, r"lineage-duplicate-edge"):
            bvh.certify_extended_polymath_dag(
                nodes,
                [
                    {"source": "C1", "target": "C2", "relation": "corresponded_with", "citation": _cite("1")},
                    {"source": "C2", "target": "C1", "relation": "corresponded_with", "citation": _cite("2")},
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
            "target_tol": Fraction(1, 2),
            "obs_joint_direct": dict(joint),
            "obs_joint_confounded": dict(joint),
            "confounder_p_u1": Fraction(1, 2),
            "confounder_p_f_given_u1": Fraction(4, 5),
            "confounder_p_f_given_u0": Fraction(1, 5),
            "confounder_p_c_given_u1": Fraction(4, 5),
            "confounder_p_c_given_u0": Fraction(1, 5),
            "min_ate_separation": Fraction(9, 25),
        }
        base.update(overrides)
        return base

    def test_boundaries_and_violations(self) -> None:
        ok = bvh.certify_contraction_and_causal_identifiability(self._valid_spec())
        self.assertTrue(ok["certified"])
        self.assertEqual(ok["banach_ball_radius"], "1/1")
        self.assertEqual(ok["banach_a_priori_error"], "1/2")

        ok_l0 = bvh.certify_contraction_and_causal_identifiability(
            self._valid_spec(lipschitz_L=Fraction(0, 1), step0_gap=Fraction(1, 1))
        )
        self.assertTrue(ok_l0["certified"])
        self.assertEqual(ok_l0["banach_a_priori_error"], "0/1")

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

        esc_lo = bvh.certify_contraction_and_causal_identifiability(self._valid_spec(x0=Fraction(0, 1)))
        self.assertEqual(esc_lo["violations"], ["KASHI_ITERATES_ESCAPE_DOMAIN"])
        esc_hi = bvh.certify_contraction_and_causal_identifiability(self._valid_spec(x0=Fraction(2, 1)))
        self.assertEqual(esc_hi["violations"], ["KASHI_ITERATES_ESCAPE_DOMAIN"])

        bad_tol = bvh.certify_contraction_and_causal_identifiability(
            self._valid_spec(target_tol=Fraction(49, 100))
        )
        self.assertEqual(bad_tol["violations"], ["KASHI_TOLERANCE_NOT_CERTIFIED"])

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


class TestStandaloneCertificateAndCLI(unittest.TestCase):
    def test_deterministic_zero_float_json_and_cli(self) -> None:
        c1 = bvh.build_certificate()
        c2 = bvh.build_certificate()
        self.assertEqual(c1["certificate_sha256"], c2["certificate_sha256"])
        self.assertEqual(c1["novelty_classification"]["honest_tier"], "N0")
        self.assertEqual(c1["execution_mode"], "standalone_pure_q")

        def _reject_float(tok: str) -> None:
            raise AssertionError(f"float:{tok}")

        with tempfile.TemporaryDirectory() as tmp:
            out_p = Path(tmp) / "cert.json"
            buf_j = io.StringIO()
            with patch("sys.stdout", buf_j):
                rc_j = bvh.main(["--json", "--write-cert", str(out_p)])
            self.assertEqual(rc_j, 0)
            written = out_p.read_text(encoding="utf-8")
            self.assertEqual(buf_j.getvalue(), written)
            parsed = json.loads(written, parse_float=_reject_float)
            self.assertEqual(parsed["audit_id"], "AUDIT-095R")

            buf_h = io.StringIO()
            with patch("sys.stdout", buf_h):
                rc_h = bvh.main([])
            self.assertEqual(rc_h, 0)
            self.assertIn("AUDIT-095R | mode=standalone_pure_q", buf_h.getvalue())


if __name__ == "__main__":
    unittest.main()
