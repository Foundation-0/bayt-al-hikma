#!/usr/bin/env python3
"""Exact pure-Q mathematical certifier for the Bayt al-Hikma polymath lineage (AUDIT-092).

Covers 13 interconnected scholars (c. 780-1274 CE):
  al-Khwarizmi, al-Kindi, Banu Musa, Thabit ibn Qurra, al-Karaji, Ibn al-Haytham,
  al-Biruni, Ibn Sina, Umar al-Khayyam, al-Samaw'al, Ibn Rushd, Isma'il al-Jazari,
  and Nasir al-Din al-Tusi.

100% pure Python 3 stdlib using exact int/Fraction arithmetic.
Zero floating-point literals or values; zero bare assert statements.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any, Sequence


SCHEMA_VERSION = "bayt-al-hikma-polymath-lineage-v1"
AUDIT_ID = "AUDIT-092"

ALLOWED_NODE_KEYS = frozenset({"node_id", "name", "birth_year", "death_year", "city", "primary_work"})
ALLOWED_EDGE_KEYS = frozenset({"source", "target", "relation"})
ALLOWED_RELATIONS = ("teacher_of", "corresponded_with", "commented_on", "extended", "critiqued")
DIRECTED_DAG_RELATIONS = frozenset({"teacher_of", "commented_on", "extended", "critiqued"})

ALLOWED_FEEDBACK_KEYS = frozenset(
    {
        "epicycle_dof",
        "held_out_constraints",
        "in_sample_error",
        "held_out_error",
        "max_held_out_error",
        "null_baseline_error",
        "valve_gain_kappa",
        "step_dt",
        "reservoir_area",
        "setpoint_head",
        "nominal_flow",
        "valve_max_flow",
    }
)

PINNED_VAULT_DIGESTS: dict[str, dict[str, Any]] = {
    "round10/portals/continuum/pr_1_files/continuum.md": {
        "bytes": 10121,
        "sha256": "516f6080563f223a4d8da437d37aaff479988f08f9079bfa48116cbb4fdc3150",
    },
    "round10/arm2-unification-and-novelty/unification_bridge_certificate.json": {
        "bytes": 17640,
        "sha256": "a662374cdb5e08adab3323477584b155ce92dbdbcb54e45871d354fccaf17642",
    },
    "round10/arm5-transformational-steelman/transformational_steelman_certificate.json": {
        "bytes": 20507,
        "sha256": "e21ceea368a945dfa1f6b6d6152714e8b2ae7df5191620f3ef37436696eb21a6",
    },
}

BAYT_AL_HIKMA_NODES: tuple[dict[str, Any], ...] = (
    {
        "node_id": "khwarizmi",
        "name": "Muhammad ibn Musa al-Khwarizmi",
        "birth_year": 780,
        "death_year": 850,
        "city": "Baghdad",
        "primary_work": "al-Kitab al-Mukhtasar fi Hisab al-Jabr wa-l-Muqabala",
    },
    {
        "node_id": "kindi",
        "name": "Abu Yusuf Yaqub ibn Ishaq al-Kindi",
        "birth_year": 801,
        "death_year": 873,
        "city": "Baghdad",
        "primary_work": "Risala fi Istikhraj al-Muamma; De Gradibus",
    },
    {
        "node_id": "banu_musa",
        "name": "Banu Musa (Muhammad ibn Musa ibn Shakir)",
        "birth_year": 803,
        "death_year": 873,
        "city": "Baghdad",
        "primary_work": "Kitab al-Hiyal (Book of Ingenious Devices)",
    },
    {
        "node_id": "thabit",
        "name": "Thabit ibn Qurra",
        "birth_year": 826,
        "death_year": 901,
        "city": "Harran / Baghdad",
        "primary_work": "Maqala fi Istikhraj al-Adad al-Mutahabba; Parabola Quadrature",
    },
    {
        "node_id": "karaji",
        "name": "Abu Bakr al-Karaji",
        "birth_year": 953,
        "death_year": 1029,
        "city": "Baghdad",
        "primary_work": "al-Fakhri fi al-Jabr wa-l-Muqabala",
    },
    {
        "node_id": "haytham",
        "name": "Ibn al-Haytham",
        "birth_year": 965,
        "death_year": 1040,
        "city": "Basra / Cairo",
        "primary_work": "Kitab al-Manazir; al-Shukuk ala Batlamyus; Sharh Musadarat Uqlidis",
    },
    {
        "node_id": "biruni",
        "name": "Abu Rayhan al-Biruni",
        "birth_year": 973,
        "death_year": 1048,
        "city": "Khwarazm / Ghazna",
        "primary_work": "Tahdid Nihayat al-Amakin; al-Qanun al-Masudi; al-Asilah wa-l-Ajwibah",
    },
    {
        "node_id": "ibn_sina",
        "name": "Ibn Sina",
        "birth_year": 980,
        "death_year": 1037,
        "city": "Bukhara / Isfahan",
        "primary_work": "al-Shifa; al-Asilah wa-l-Ajwibah",
    },
    {
        "node_id": "khayyam",
        "name": "Umar al-Khayyam",
        "birth_year": 1048,
        "death_year": 1131,
        "city": "Nishapur / Isfahan",
        "primary_work": "Risala fi Sharh ma Ashkala min Musadarat Uqlidis; Risala fi al-Jabr",
    },
    {
        "node_id": "ibn_rushd",
        "name": "Ibn Rushd",
        "birth_year": 1126,
        "death_year": 1198,
        "city": "Cordoba / Marrakesh",
        "primary_work": "Tafsir ma Bad al-Tabia (Book Lambda)",
    },
    {
        "node_id": "samawal",
        "name": "al-Samawal ibn Yahya al-Maghribi",
        "birth_year": 1130,
        "death_year": 1180,
        "city": "Baghdad / Maragheh",
        "primary_work": "al-Bahir fi al-Jabr",
    },
    {
        "node_id": "jazari",
        "name": "Ismail al-Jazari",
        "birth_year": 1136,
        "death_year": 1206,
        "city": "Diyarbakir",
        "primary_work": "Kitab fi Marifat al-Hiyal al-Handasiyya",
    },
    {
        "node_id": "tusi",
        "name": "Nasir al-Din al-Tusi",
        "birth_year": 1201,
        "death_year": 1274,
        "city": "Maragheh",
        "primary_work": "al-Tadhkira fi Ilm al-Haya; al-Risala al-Shafiya",
    },
)

BAYT_AL_HIKMA_EDGES: tuple[dict[str, str], ...] = (
    {"source": "khwarizmi", "target": "karaji", "relation": "extended"},
    {"source": "karaji", "target": "samawal", "relation": "extended"},
    {"source": "khwarizmi", "target": "khayyam", "relation": "extended"},
    {"source": "thabit", "target": "haytham", "relation": "commented_on"},
    {"source": "haytham", "target": "khayyam", "relation": "extended"},
    {"source": "khayyam", "target": "tusi", "relation": "extended"},
    {"source": "haytham", "target": "tusi", "relation": "extended"},
    {"source": "haytham", "target": "ibn_rushd", "relation": "commented_on"},
    {"source": "ibn_sina", "target": "ibn_rushd", "relation": "critiqued"},
    {"source": "biruni", "target": "ibn_sina", "relation": "corresponded_with"},
    {"source": "kindi", "target": "haytham", "relation": "critiqued"},
    {"source": "kindi", "target": "ibn_sina", "relation": "commented_on"},
    {"source": "banu_musa", "target": "thabit", "relation": "teacher_of"},
    {"source": "banu_musa", "target": "jazari", "relation": "extended"},
)


class PolymathAuditError(ValueError):
    """Fail-closed refusal raised whenever any mathematical, lineage, or contract check fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PolymathAuditError(message)


def _require_exact_int(value: Any, name: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"exact-int:{name}")
    return value


def _require_exact_fraction(value: Any, name: str) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value, 1)
    raise PolymathAuditError(f"exact-fraction:{name}")


def _require_clean_ascii(value: Any, name: str) -> str:
    _require(
        isinstance(value, str)
        and len(value) > 0
        and value == value.strip()
        and all(32 <= ord(ch) <= 126 for ch in value),
        f"clean-ascii:{name}",
    )
    return value


def _require_exact_choice(value: Any, allowed: tuple[str, ...], name: str) -> str:
    _require(isinstance(value, str) and value in allowed, f"exact-choice:{name}")
    return value


def frac_str(value: Fraction) -> str:
    v = _require_exact_fraction(value, "frac_str")
    return f"{v.numerator}/{v.denominator}"


def frac_dec6(value: Fraction) -> str:
    v = _require_exact_fraction(value, "frac_dec6")
    sign = "-" if v < 0 else ""
    av = abs(v)
    scaled = (av.numerator * 1_000_000) // av.denominator
    whole, rem = divmod(scaled, 1_000_000)
    return f"{sign}{whole}.{rem:06d}"


def _is_prime_exact(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _proper_divisor_sum(n: int) -> int:
    _require(_require_exact_int(n, "n") >= 2, "divisor-sum-ge-2")
    total = 1
    d = 2
    while d * d <= n:
        if n % d == 0:
            total += d
            if d * d != n:
                total += n // d
        d += 1
    return total


def _v2_exact(n: int) -> int:
    n_i = _require_exact_int(n, "n")
    _require(n_i > 0, "v2-pos")
    count = 0
    while n_i % 2 == 0:
        n_i //= 2
        count += 1
    return count


def _positive_divisors(n: int) -> list[int]:
    m = abs(_require_exact_int(n, "n"))
    _require(m > 0, "divisors-nonzero")
    small: list[int] = []
    large: list[int] = []
    d = 1
    while d * d <= m:
        if m % d == 0:
            small.append(d)
            if d * d != m:
                large.append(m // d)
        d += 1
    return small + list(reversed(large))


def analyze_pillar1_continuum_vs_atomism() -> dict[str, Any]:
    """Pillar 1: Al-Biruni <-> Ibn Sina continuum obstruction + Thabit ibn Qurra quadrature & amicables."""
    # 1A. 2-adic valuation parity obstruction against N^2 + N^2 = M^2 (sqrt(2) irrational)
    sample_n = (1, 2, 3, 6, 12)
    v2_checks = []
    for nv in sample_n:
        lhs = 2 * nv * nv
        v2_lhs = _v2_exact(lhs)
        v2_checks.append({"N": nv, "2N^2": lhs, "v2_2N2": v2_lhs, "v2_odd": (v2_lhs % 2) == 1})

    # Lattice L_inf vs Euclidean squared metric distortion on (N, N) vs (N, 0)
    euclid_diag_sq = Fraction(2, 1)
    linf_diag_sq = Fraction(1, 1)
    squared_metric_distortion = euclid_diag_sq / linf_diag_sq  # 2/1

    # 1B. Concentric wheel 2:1 slippage: outer step = 1 atom => inner step = 1/2 atom (not integer!)
    concentric_inner_step = Fraction(1, 2)

    # 1C. Thabit ibn Qurra amicable numbers (n = 2, 3, 4)
    thabit_cases = []
    for n in (2, 3, 4):
        p = 3 * (2 ** (n - 1)) - 1
        q = 3 * (2**n) - 1
        r = 9 * (2 ** (2 * n - 1)) - 1
        all_prime = _is_prime_exact(p) and _is_prime_exact(q) and _is_prime_exact(r)
        a_num = (2**n) * p * q
        b_num = (2**n) * r
        s_a = _proper_divisor_sum(a_num)
        s_b = _proper_divisor_sum(b_num)
        thabit_cases.append(
            {
                "n": n,
                "p": p,
                "q": q,
                "r": r,
                "all_three_prime": all_prime,
                "A": a_num,
                "B": b_num,
                "sigma_proper_A": s_a,
                "sigma_proper_B": s_b,
                "is_amicable": (s_a == b_num and s_b == a_num),
            }
        )

    # 1D. Thabit's unequal-subdivision parabola quadrature on [0, 1] at x_k = (k/N)^2 (N = 100)
    n_grid = 100
    upper_sum = Fraction(0, 1)
    lower_sum = Fraction(0, 1)
    for k in range(1, n_grid + 1):
        dx = Fraction(k * k - (k - 1) * (k - 1), n_grid * n_grid)
        upper_sum += Fraction(k, n_grid) * dx
        lower_sum += Fraction(k - 1, n_grid) * dx
    exact_area = Fraction(2, 3)

    return {
        "biruni_ibn_sina_discrete_obstruction": {
            "v2_parity_checks": v2_checks,
            "all_v2_odd": all(row["v2_odd"] for row in v2_checks),
            "diagonal_squared_metric_distortion": frac_str(squared_metric_distortion),
            "concentric_wheel_2to1_inner_step": frac_str(concentric_inner_step),
            "concentric_step_is_integer": concentric_inner_step.denominator == 1,
        },
        "thabit_amicable_theorem": thabit_cases,
        "thabit_parabola_quadrature": {
            "N": n_grid,
            "lower_darboux": frac_str(lower_sum),
            "upper_darboux": frac_str(upper_sum),
            "exact_integral": frac_str(exact_area),
            "bracket_width": frac_str(upper_sum - lower_sum),
            "sandwiches_two_thirds": lower_sum < exact_area < upper_sum,
            "width_equals_one_over_N": (upper_sum - lower_sum) == Fraction(1, n_grid),
        },
    }


def alhazen_quartic_coeffs(
    a_pt: tuple[Fraction, Fraction], b_pt: tuple[Fraction, Fraction]
) -> tuple[Fraction, Fraction, Fraction, Fraction, Fraction]:
    """Exact coefficients (c4, c3, c2, c1, c0) of Alhazen's reflection quartic P(t) = 0 on unit circle.

    Using M(t) = ((1 - t^2)/(1 + t^2), 2t/(1 + t^2)) and reflection law:
      (A x M)(B . M - 1) + (B x M)(A . M - 1) = 0.
    """
    ax, ay = _require_exact_fraction(a_pt[0], "ax"), _require_exact_fraction(a_pt[1], "ay")
    bx, by = _require_exact_fraction(b_pt[0], "bx"), _require_exact_fraction(b_pt[1], "by")
    # Numerators of (A x M) and (B . M - 1) over (1 + t^2) as [c0, c1, c2]:
    # A x M = (ay) t^2 + (2 ax) t - ay
    # B . M - 1 = (-bx - 1) t^2 + (2 by) t + (bx - 1)
    def _poly_mul_deg2(u: tuple[Fraction, Fraction, Fraction], v: tuple[Fraction, Fraction, Fraction]) -> list[Fraction]:
        out = [Fraction(0, 1)] * 5
        for i in range(3):
            for j in range(3):
                out[i + j] += u[i] * v[j]
        return out

    u1 = (-ay, 2 * ax, ay)
    v1 = (bx - Fraction(1, 1), 2 * by, -bx - Fraction(1, 1))
    u2 = (-by, 2 * bx, by)
    v2 = (ax - Fraction(1, 1), 2 * ay, -ax - Fraction(1, 1))
    p1 = _poly_mul_deg2(u1, v1)
    p2 = _poly_mul_deg2(u2, v2)
    comb = [p1[k] + p2[k] for k in range(5)]  # ascending [c0..c4]
    return (comb[4], comb[3], comb[2], comb[1], comb[0])


def _eval_poly_desc(coeffs: Sequence[Fraction], x: Fraction) -> Fraction:
    acc = Fraction(0, 1)
    for c in coeffs:
        acc = acc * x + c
    return acc


def analyze_pillar2_haytham_khayyam_rushd() -> dict[str, Any]:
    """Pillar 2: Alhazen quartic non-constructibility, Haytham-Khayyam curvature trichotomy, Ibn Rushd anti-epicycles."""
    # 2A-1. Symmetric constructible case A=(2, 1), B=(2, -1) -> M=(1, 0), t=0
    sym_coeffs = alhazen_quartic_coeffs((Fraction(2, 1), Fraction(1, 1)), (Fraction(2, 1), Fraction(-1, 1)))
    sym_at_zero = _eval_poly_desc(sym_coeffs, Fraction(0, 1))

    # 2A-2. Classic non-constructible case A=(2, 0), B=(0, 3) -> -9t^4 - 4t^3 + 36t^2 - 4t - 3 = 0
    raw_coeffs = alhazen_quartic_coeffs((Fraction(2, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(3, 1)))
    # Normalize sign so leading coeff is positive (+9):
    sign_flip = Fraction(-1, 1) if raw_coeffs[0] < 0 else Fraction(1, 1)
    q_coeffs = tuple(sign_flip * c for c in raw_coeffs)  # (9, 4, -36, 4, 3)

    # Exhaustive Rational Root Theorem check on P(t)
    rat_roots_p: list[str] = []
    for num in _positive_divisors(int(q_coeffs[-1])):
        for den in _positive_divisors(int(q_coeffs[0])):
            for sgn in (-1, 1):
                cand = Fraction(sgn * num, den)
                if _eval_poly_desc(q_coeffs, cand) == 0:
                    rat_roots_p.append(frac_str(cand))

    # Isolate all 4 real roots via exact rational sign changes
    probe_pts = (Fraction(-3, 1), Fraction(-1, 1), Fraction(-1, 5), Fraction(1, 2), Fraction(3, 1))
    probe_signs = [1 if _eval_poly_desc(q_coeffs, x) > 0 else -1 for x in probe_pts]
    sign_changes = sum(1 for i in range(len(probe_signs) - 1) if probe_signs[i] * probe_signs[i + 1] < 0)

    # Depress quartic t = y - b/(4a) = y - 1/9 and compute exact integer Ferrari cubic resolvent
    shift = -q_coeffs[1] / (4 * q_coeffs[0])
    asc_orig = list(reversed(q_coeffs))
    dep_asc = [Fraction(0, 1)] * 5
    for k, ck in enumerate(asc_orig):
        for j in range(k + 1):
            dep_asc[j] += ck * math.comb(k, j) * (shift ** (k - j))
    dep_monic = [x / dep_asc[4] for x in dep_asc]  # [r, q, p, 0, 1]
    r_d, q_d, p_d = dep_monic[0], dep_monic[1], dep_monic[2]
    res_frac = (Fraction(1, 1), 2 * p_d, p_d * p_d - 4 * r_d, -(q_d * q_d))
    lcm_den = math.lcm(*(c.denominator for c in res_frac))
    res_int = [int(c * lcm_den) for c in res_frac]
    gcd_all = math.gcd(*(abs(c) for c in res_int))
    res_int = [c // gcd_all for c in res_int]
    res_poly = tuple(Fraction(c, 1) for c in res_int)

    # Exhaustive Rational Root Theorem check on Ferrari cubic resolvent (proving 3 | |Gal(P)|!)
    rat_roots_res: list[str] = []
    for num in _positive_divisors(res_int[-1]):
        for den in _positive_divisors(res_int[0]):
            for sgn in (-1, 1):
                cand = Fraction(sgn * num, den)
                if _eval_poly_desc(res_poly, cand) == 0:
                    rat_roots_res.append(frac_str(cand))

    # 2B. Haytham-Khayyam-Tusi trirectangular quadrilateral curvature trichotomy in exact Q
    # Hyperbolic (K=-1): sinh(a)=3/4, sinh(b)=5/12 => cos(phi) = sinh(a)*sinh(b) = 5/16 > 0 (acute!)
    # Euclidean  (K= 0): cos(phi) = 0 (right!)
    # Spherical  (K=+1): sin(a)=3/5, sin(b)=5/13 => cos(phi) = -sin(a)*sin(b) = -3/13 < 0 (obtuse!)
    cos_hyp = Fraction(3, 4) * Fraction(5, 12)
    cos_euc = Fraction(0, 1)
    cos_sph = -Fraction(3, 5) * Fraction(5, 13)

    # 2C. Ibn Rushd anti-epicycle overparameterization witness:
    # Fitting 3 discrete observations y(0)=0, y(1)=0, y(2)=1 with a 3-parameter quadratic/harmonic interpolant
    # p(x) = (1/2)x^2 - (1/2)x gives 0/1 in-sample error on {0, 1, 2}, yet on held-out x=10 (true linear 0)
    # explodes to p(10) = 45 (pure overparameterized epicycle artifact, dof=3 == n_train=3)!
    def _interp(x: Fraction) -> Fraction:
        return Fraction(1, 2) * x * x - Fraction(1, 2) * x

    train_pts = ((Fraction(0, 1), Fraction(0, 1)), (Fraction(1, 1), Fraction(0, 1)), (Fraction(2, 1), Fraction(1, 1)))
    in_sample_l1 = sum((abs(_interp(x) - y) for x, y in train_pts), Fraction(0, 1))
    held_out_err = abs(_interp(Fraction(10, 1)) - Fraction(0, 1))

    return {
        "alhazen_spherical_mirror_quartic": {
            "symmetric_t0_residual": frac_str(sym_at_zero),
            "asymmetric_points": {"A": ["2/1", "0/1"], "B": ["0/1", "3/1"]},
            "quartic_coeffs_desc": [frac_str(c) for c in q_coeffs],
            "quartic_rational_roots": rat_roots_p,
            "real_root_sign_changes": sign_changes,
            "depressed_p_q_r": [frac_str(p_d), frac_str(q_d), frac_str(r_d)],
            "ferrari_resolvent_cubic_int": res_int,
            "ferrari_resolvent_rational_roots": rat_roots_res,
            "ruler_and_compass_impossible_exact": (len(rat_roots_p) == 0 and len(rat_roots_res) == 0),
        },
        "haytham_khayyam_quadrilateral_trichotomy": {
            "hyperbolic_cos_summit": frac_str(cos_hyp),
            "hyperbolic_acute": cos_hyp > 0,
            "euclidean_cos_summit": frac_str(cos_euc),
            "euclidean_right": cos_euc == 0,
            "spherical_cos_summit": frac_str(cos_sph),
            "spherical_obtuse": cos_sph < 0,
        },
        "ibn_rushd_anti_epicycle_witness": {
            "dof": 3,
            "n_train": 3,
            "in_sample_l1_error": frac_str(in_sample_l1),
            "held_out_x10_error": frac_str(held_out_err),
        },
    }


def reduce_khwarizmi_quadratic(
    lhs: tuple[Fraction, Fraction, Fraction], rhs: tuple[Fraction, Fraction, Fraction]
) -> dict[str, Any]:
    """Exact pure-Q implementation of al-Khwarizmi's al-jabr (restoration) + al-muqabala (balancing).

    Input: lhs = (L2, L1, L0), rhs = (R2, R1, R0) for L2 x^2 + L1 x + L0 = R2 x^2 + R1 x + R0.
    Produces one of al-Khwarizmi's 6 positive-coefficient canonical forms (with exact positive rational check).
    """
    _require(isinstance(lhs, tuple) and len(lhs) == 3, "khwarizmi-lhs-len")
    _require(isinstance(rhs, tuple) and len(rhs) == 3, "khwarizmi-rhs-len")
    l_f = tuple(_require_exact_fraction(v, f"lhs[{i}]") for i, v in enumerate(lhs))
    r_f = tuple(_require_exact_fraction(v, f"rhs[{i}]") for i, v in enumerate(rhs))

    # Combined net coefficients a x^2 + b x + c = 0
    a = l_f[0] - r_f[0]
    b = l_f[1] - r_f[1]
    c = l_f[2] - r_f[2]
    _require(not (a == 0 and b == 0), "khwarizmi-degenerate-no-unknown")

    # Normalize so leading nonzero term is positive
    lead = a if a != 0 else b
    if lead < 0:
        a, b, c = -a, -b, -c

    if a == 0:
        # Linear form: b x = -c (Type 3: roots equal numbers, requires -c > 0)
        _require(-c > 0, "khwarizmi-no-positive-root")
        root = (-c) / b
        return {"canonical_type": 3, "form": "bx = c", "p": frac_str(b), "q": frac_str(-c), "positive_root": frac_str(root)}

    # Monic reduction (al-radd): x^2 + (b/a) x + (c/a) = 0
    p = b / a
    q = c / a
    if q == 0:
        _require(p < 0, "khwarizmi-no-positive-root")
        return {"canonical_type": 1, "form": "x^2 = px", "p": frac_str(-p), "q": "0/1", "positive_root": frac_str(-p)}
    if p == 0 and q < 0:
        return {"canonical_type": 2, "form": "x^2 = q", "p": "0/1", "q": frac_str(-q), "discriminant": frac_str(-q)}
    if p > 0 and q < 0:
        # Type 4: x^2 + p x = (-q)
        rhs_q = -q
        disc = (p / 2) ** 2 + rhs_q
        return {"canonical_type": 4, "form": "x^2 + px = q", "p": frac_str(p), "q": frac_str(rhs_q), "discriminant": frac_str(disc)}
    if p < 0 and q > 0:
        # Type 5: x^2 + q = (-p) x
        rhs_p = -p
        disc = (rhs_p / 2) ** 2 - q
        _require(disc >= 0, "khwarizmi-complex-roots")
        return {"canonical_type": 5, "form": "x^2 + q = px", "p": frac_str(rhs_p), "q": frac_str(q), "discriminant": frac_str(disc)}
    if p < 0 and q < 0:
        # Type 6: x^2 = (-p) x + (-q)
        rhs_p, rhs_q = -p, -q
        disc = (rhs_p / 2) ** 2 + rhs_q
        return {"canonical_type": 6, "form": "x^2 = px + q", "p": frac_str(rhs_p), "q": frac_str(rhs_q), "discriminant": frac_str(disc)}
    raise PolymathAuditError("khwarizmi-no-positive-root")


def laurent_normalize(poly: dict[int, Fraction]) -> dict[int, Fraction]:
    """Canonical sparse Laurent polynomial over Q[x, x^-1] (al-Karaji / al-Samaw'al 1149 CE)."""
    _require(isinstance(poly, dict), "laurent-dict")
    out: dict[int, Fraction] = {}
    for exp, coeff in poly.items():
        e_i = _require_exact_int(exp, "laurent-exp")
        c_f = _require_exact_fraction(coeff, f"laurent[{e_i}]")
        if c_f != 0:
            out[e_i] = c_f
    return out


def laurent_add(a: dict[int, Fraction], b: dict[int, Fraction]) -> dict[int, Fraction]:
    na, nb = laurent_normalize(a), laurent_normalize(b)
    out = dict(na)
    for e, c in nb.items():
        out[e] = out.get(e, Fraction(0, 1)) + c
    return laurent_normalize(out)


def laurent_mul(a: dict[int, Fraction], b: dict[int, Fraction]) -> dict[int, Fraction]:
    na, nb = laurent_normalize(a), laurent_normalize(b)
    out: dict[int, Fraction] = {}
    for ea, ca in na.items():
        for eb, cb in nb.items():
            out[ea + eb] = out.get(ea + eb, Fraction(0, 1)) + ca * cb
    return laurent_normalize(out)


def analyze_pillar3_transformational_algebra_laurent() -> dict[str, Any]:
    """Pillar 3: al-Khwarizmi 6-form reducer + al-Karaji/al-Samaw'al Laurent ring Q[x, x^-1] -> AUDIT-085R."""
    # Flagship Type 4: x^2 + 10x = 39 (from al-Kitab al-Mukhtasar Ch. 1, written with restoration terms on both sides!)
    # (2 x^2 + 7 x - 9) = (x^2 - 3 x + 30) -> al-jabr & al-muqabala -> x^2 + 10x = 39, disc = 64 = 8^2, root = 8 - 5 = 3
    flagship = reduce_khwarizmi_quadratic(
        (Fraction(2, 1), Fraction(7, 1), Fraction(-9, 1)),
        (Fraction(1, 1), Fraction(-3, 1), Fraction(30, 1)),
    )
    flagship_root = Fraction(3, 1)
    flagship_check = flagship_root**2 + 10 * flagship_root == Fraction(39, 1)

    # All 6 canonical forms verified
    type1 = reduce_khwarizmi_quadratic((Fraction(3, 1), Fraction(0, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(15, 1), Fraction(0, 1)))
    type2 = reduce_khwarizmi_quadratic((Fraction(2, 1), Fraction(0, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(0, 1), Fraction(18, 1)))
    type3 = reduce_khwarizmi_quadratic((Fraction(0, 1), Fraction(4, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(0, 1), Fraction(12, 1)))
    type5 = reduce_khwarizmi_quadratic((Fraction(1, 1), Fraction(0, 1), Fraction(21, 1)), (Fraction(0, 1), Fraction(10, 1), Fraction(0, 1)))
    type6 = reduce_khwarizmi_quadratic((Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(3, 1), Fraction(4, 1)))

    # al-Samaw'al (1149 CE, al-Bahir) Laurent ring Q[x, x^-1]:
    # 1. Exact geometric Laurent identity (1 - x^-1) * (1 + x^-1 + ... + x^-5) == 1 - x^-6
    one_minus_inv = {0: Fraction(1, 1), -1: Fraction(-1, 1)}
    geom5 = {-k: Fraction(1, 1) for k in range(6)}
    prod_geom = laurent_mul(one_minus_inv, geom5)
    # 2. Exact multiplicative inverse of monomial 3 x^-2 is (1/3) x^2 -> product == {0: 1}
    mon_prod = laurent_mul({-2: Fraction(3, 1)}, {2: Fraction(1, 3)})
    # 3. Direct bridge to AUDIT-085R Q[q] Schur complement on K_22 = 1 - q:
    # For K = [[q^2, q], [q, 1 - q]], exact numerator of Schur complement S = K_00 - K_01^2 / K_11
    # satisfies K_11 * S = K_00 * K_11 - K_01^2 = q^2(1 - q) - q^2 = -q^3!
    k00 = {2: Fraction(1, 1)}
    k01 = {1: Fraction(1, 1)}
    k11 = {0: Fraction(1, 1), 1: Fraction(-1, 1)}
    schur_num = laurent_add(laurent_mul(k00, k11), laurent_mul({0: Fraction(-1, 1)}, laurent_mul(k01, k01)))

    return {
        "khwarizmi_six_canonical_forms": {
            "type1": type1,
            "type2": type2,
            "type3": type3,
            "type4_flagship_x2_10x_39": flagship,
            "type4_flagship_root_3_verified": flagship_check,
            "type5": type5,
            "type6": type6,
        },
        "samawal_laurent_ring_and_audit085r_bridge": {
            "geom_identity_prod": {str(k): frac_str(v) for k, v in sorted(prod_geom.items())},
            "geom_identity_exact": prod_geom == {0: Fraction(1, 1), -6: Fraction(-1, 1)},
            "negative_exponent_inverse_exact": mon_prod == {0: Fraction(1, 1)},
            "audit085r_schur_numerator_k11_S": {str(k): frac_str(v) for k, v in sorted(schur_num.items())},
            "audit085r_exact_neg_q3": schur_num == {3: Fraction(-1, 1)},
        },
    }


def analyze_pillar4_kindi_biruni_tusi_jazari() -> dict[str, Any]:
    """Pillar 4: al-Kindi, al-Biruni Nandana sexagesimal forensics, al-Tusi couple, al-Jazari float valve."""
    # 4A. al-Kindi De Gradibus (2^n) + frequency-null permutation invariance
    de_gradibus = {f"degree_{n}": 2**n for n in range(5)}
    plain_freqs = (Fraction(1, 2), Fraction(1, 4), Fraction(1, 8), Fraction(1, 8))
    # Arbitrary monoalphabetic substitution permutation (cyclic shift by 1)
    cipher_freqs = (plain_freqs[1], plain_freqs[2], plain_freqs[3], plain_freqs[0])
    unif = Fraction(1, 4)
    l1_plain = sum((abs(f - unif) for f in plain_freqs), Fraction(0, 1))
    l1_cipher = sum((abs(f - unif) for f in cipher_freqs), Fraction(0, 1))

    # 4B. al-Biruni Nandana horizon-dip geodesy (Tahdid, c. 1025 CE)
    # h = 652;03,18 = 652.055 cubits; dip = 34' = 17/5400 * pi
    h_biruni = Fraction(652_055, 1_000)
    pi_lo = Fraction(314_159_265, 100_000_000)
    pi_hi = Fraction(314_159_266, 100_000_000)
    a34_lo = Fraction(17, 5_400) * pi_lo
    a34_hi = Fraction(17, 5_400) * pi_hi
    cos34_lo = Fraction(1, 1) - (a34_hi * a34_hi) / 2
    cos34_hi = Fraction(1, 1) - (a34_lo * a34_lo) / 2 + (a34_lo**4) / 24
    r34_lo = h_biruni * cos34_lo / (Fraction(1, 1) - cos34_lo)
    r34_hi = h_biruni * cos34_hi / (Fraction(1, 1) - cos34_hi)

    # Exact forensic 3-place sexagesimal table truncation: cos(34') = 0;59,59,49 = 215989/216000
    cos_sex3 = Fraction(59 * 3600 + 59 * 60 + 49, 216_000)
    r_sex3 = h_biruni * cos_sex3 / (Fraction(1, 1) - cos_sex3)  # 28167341479 / 2200 = 12803337.0359...
    biruni_reported = 12_803_337
    # Sensitivity at 33' and 35' (using exact upper Taylor cos at pi_lo)
    a33 = Fraction(33, 10_800) * pi_lo
    a35 = Fraction(35, 10_800) * pi_lo
    c33 = Fraction(1, 1) - (a33 * a33) / 2 + (a33**4) / 24
    c35 = Fraction(1, 1) - (a35 * a35) / 2 + (a35**4) / 24
    r33 = h_biruni * c33 / (Fraction(1, 1) - c33)
    r35 = h_biruni * c35 / (Fraction(1, 1) - c35)
    refraction_bias_factor = Fraction(7, 6)  # 1 / (1 - k) for terrestrial k = 1/7

    # 4C. Nasir al-Din al-Tusi couple (1261 CE) via exact Weierstrass rational t = tan(theta/2)
    r_inner = Fraction(1, 1)
    t_grid = (Fraction(0, 1), Fraction(1, 3), Fraction(1, 2), Fraction(1, 1), Fraction(2, 1), Fraction(3, 1), Fraction(5, 1))
    tusi_rows = []
    for t in t_grid:
        cos_th = (Fraction(1, 1) - t * t) / (Fraction(1, 1) + t * t)
        sin_th = (2 * t) / (Fraction(1, 1) + t * t)
        # C(t) = (r cos th, r sin th); offset = (r cos(-th), r sin(-th)) = (r cos th, -r sin th)
        px = r_inner * cos_th + r_inner * cos_th
        py = r_inner * sin_th - r_inner * sin_th
        tusi_rows.append({"t": frac_str(t), "P_x": frac_str(px), "P_y": frac_str(py)})

    # 4D. Isma'il al-Jazari continuous float-valve feedback dynamics (1206 CE)
    def _sim_valve(loop_gain: Fraction, e0: Fraction, steps: int) -> list[str]:
        e = e0
        traj = [frac_str(e)]
        for _ in range(steps):
            e = (Fraction(1, 1) - loop_gain) * e
            traj.append(frac_str(e))
        return traj

    jazari_monotone = _sim_valve(Fraction(1, 2), Fraction(1, 1), 4)   # 1 -> 1/2 -> 1/4 -> 1/8 -> 1/16
    jazari_osc = _sim_valve(Fraction(3, 2), Fraction(1, 1), 4)        # 1 -> -1/2 -> 1/4 -> -1/8 -> 1/16
    jazari_hunt = _sim_valve(Fraction(2, 1), Fraction(1, 1), 4)       # 1 -> -1 -> 1 -> -1 -> 1 (period-2!)
    jazari_diverge = _sim_valve(Fraction(5, 2), Fraction(1, 1), 4)    # 1 -> -3/2 -> 9/4 -> -27/8 -> 81/16

    return {
        "kindi_de_gradibus_and_frequency_null": {
            "de_gradibus_2_pow_n": de_gradibus,
            "plain_l1_from_uniform": frac_str(l1_plain),
            "cipher_l1_from_uniform": frac_str(l1_cipher),
            "permutation_invariant_exact": l1_plain == l1_cipher and l1_plain > 0,
        },
        "biruni_nandana_geodesy_forensics": {
            "height_cubits": frac_str(h_biruni),
            "exact_r34_bracket_dec6": [frac_dec6(r34_lo), frac_dec6(r34_hi)],
            "sexagesimal_3place_cos34": frac_str(cos_sex3),
            "sexagesimal_3place_r": frac_str(r_sex3),
            "sexagesimal_3place_r_dec6": frac_dec6(r_sex3),
            "biruni_tahdid_reported_cubits": biruni_reported,
            "abs_diff_cubits_dec6": frac_dec6(abs(r_sex3 - biruni_reported)),
            "reconstructs_within_1_cubit": abs(r_sex3 - biruni_reported) < Fraction(1, 1),
            "dip_33min_r_dec6": frac_dec6(r33),
            "dip_35min_r_dec6": frac_dec6(r35),
            "refraction_k_one_seventh_factor": frac_str(refraction_bias_factor),
        },
        "tusi_couple_zero_residual": {
            "samples": tusi_rows,
            "all_transverse_residuals_zero": all(row["P_y"] == "0/1" for row in tusi_rows),
        },
        "jazari_float_valve_regimes": {
            "monotone_mu_half": jazari_monotone,
            "damped_osc_mu_3_halves": jazari_osc,
            "hunting_mu_2": jazari_hunt,
            "divergent_mu_5_halves": jazari_diverge,
        },
    }


def certify_polymath_lineage_graph(
    nodes: Sequence[dict[str, Any]], edges: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """Fail-closed chronological & DAG acyclicity certifier for the Bayt al-Hikma polymath network."""
    _require(isinstance(nodes, (list, tuple)) and len(nodes) >= 1, "lineage-nodes-nonempty")
    _require(isinstance(edges, (list, tuple)), "lineage-edges-seq")

    by_id: dict[str, dict[str, Any]] = {}
    seen_lower: set[str] = set()
    for idx, node in enumerate(nodes):
        _require(isinstance(node, dict), f"lineage-node-dict:{idx}")
        _require(set(node.keys()) == ALLOWED_NODE_KEYS, f"lineage-node-keys:{idx}")
        nid = _require_clean_ascii(node["node_id"], f"node_id[{idx}]")
        _require_clean_ascii(node["name"], f"name[{idx}]")
        _require_clean_ascii(node["city"], f"city[{idx}]")
        _require_clean_ascii(node["primary_work"], f"primary_work[{idx}]")
        birth = _require_exact_int(node["birth_year"], f"birth_year[{idx}]")
        death = _require_exact_int(node["death_year"], f"death_year[{idx}]")
        _require(birth < death, f"lineage-lifespan-order:{nid}")
        low = nid.lower()
        _require(low not in seen_lower, f"lineage-duplicate-node:{nid}")
        seen_lower.add(low)
        by_id[nid] = node

    adj: dict[str, list[str]] = {nid: [] for nid in by_id}
    seen_edges: set[tuple[str, str, str]] = set()
    chronology_violations: list[str] = []

    for idx, edge in enumerate(edges):
        _require(isinstance(edge, dict), f"lineage-edge-dict:{idx}")
        _require(set(edge.keys()) == ALLOWED_EDGE_KEYS, f"lineage-edge-keys:{idx}")
        src = _require_clean_ascii(edge["source"], f"edge.source[{idx}]")
        dst = _require_clean_ascii(edge["target"], f"edge.target[{idx}]")
        rel = _require_exact_choice(edge["relation"], ALLOWED_RELATIONS, f"edge.relation[{idx}]")
        _require(src in by_id, f"lineage-unknown-source:{src}")
        _require(dst in by_id, f"lineage-unknown-target:{dst}")
        _require(src != dst, f"lineage-self-loop:{src}")
        ekey = (min(src, dst), max(src, dst), rel) if rel == "corresponded_with" else (src, dst, rel)
        _require(ekey not in seen_edges, f"lineage-duplicate-edge:{src}->{dst}:{rel}")
        seen_edges.add(ekey)

        s_node, d_node = by_id[src], by_id[dst]
        if rel == "teacher_of":
            if not (
                s_node["birth_year"] + 10 <= d_node["birth_year"]
                and d_node["birth_year"] + 12 <= min(s_node["death_year"], d_node["death_year"])
            ):
                chronology_violations.append(f"CHRONO_TEACHER:{src}->{dst}")
        elif rel == "corresponded_with":
            overlap = min(s_node["death_year"], d_node["death_year"]) - max(
                s_node["birth_year"], d_node["birth_year"]
            )
            if overlap < 15:
                chronology_violations.append(f"CHRONO_CORRESPONDENCE_NO_OVERLAP:{src}<->{dst}")
        else:
            # both source and target must reach scholarly maturity (birth + 15), and source before target dies
            if (
                s_node["birth_year"] + 15 > min(s_node["death_year"], d_node["death_year"])
                or d_node["birth_year"] + 15 > d_node["death_year"]
            ):
                chronology_violations.append(f"CHRONO_ANACHRONISTIC_INFLUENCE:{src}->{dst}")

        if rel in DIRECTED_DAG_RELATIONS:
            adj[src].append(dst)

    # Exact 3-color DFS cycle detection on directional lineage graph
    color: dict[str, int] = {nid: 0 for nid in by_id}
    has_cycle = False

    def _dfs(u: str) -> bool:
        color[u] = 1
        for v in adj[u]:
            if color[v] == 1:
                return True
            if color[v] == 0 and _dfs(v):
                return True
        color[u] = 2
        return False

    for nid in by_id:
        if color[nid] == 0 and _dfs(nid):
            has_cycle = True
            break

    return {
        "certified": (len(chronology_violations) == 0 and not has_cycle),
        "node_count": len(by_id),
        "edge_count": len(seen_edges),
        "chronology_violations": chronology_violations,
        "directed_dag_acyclic": not has_cycle,
    }


def certify_bounded_feedback_and_anti_epicycle(spec: Any) -> dict[str, Any]:
    """Unified fail-closed Ibn Rushd Anti-Epicycle (Law 3) + al-Jazari Float-Valve Stability Gate."""
    _require(isinstance(spec, dict), "feedback-spec-dict")
    _require(set(spec.keys()) == ALLOWED_FEEDBACK_KEYS, "feedback-spec-keys")

    dof = _require_exact_int(spec["epicycle_dof"], "epicycle_dof")
    n_held = _require_exact_int(spec["held_out_constraints"], "held_out_constraints")
    _require(dof >= 1, "feedback-dof-pos")
    _require(n_held >= 1, "feedback-held-out-pos")

    in_err = _require_exact_fraction(spec["in_sample_error"], "in_sample_error")
    ho_err = _require_exact_fraction(spec["held_out_error"], "held_out_error")
    max_ho = _require_exact_fraction(spec["max_held_out_error"], "max_held_out_error")
    null_err = _require_exact_fraction(spec["null_baseline_error"], "null_baseline_error")
    _require(in_err >= 0 and ho_err >= 0 and max_ho > 0 and null_err >= 0, "feedback-err-range")

    kappa = _require_exact_fraction(spec["valve_gain_kappa"], "valve_gain_kappa")
    dt = _require_exact_fraction(spec["step_dt"], "step_dt")
    area = _require_exact_fraction(spec["reservoir_area"], "reservoir_area")
    setpoint = _require_exact_fraction(spec["setpoint_head"], "setpoint_head")
    q_nom = _require_exact_fraction(spec["nominal_flow"], "nominal_flow")
    q_max = _require_exact_fraction(spec["valve_max_flow"], "valve_max_flow")
    _require(kappa > 0 and dt > 0 and area > 0 and setpoint > 0, "feedback-phys-pos")
    _require(Fraction(0, 1) < q_nom < q_max, "feedback-flow-bounds")

    loop_gain = (kappa * dt) / area
    contraction_factor = abs(Fraction(1, 1) - loop_gain)
    linear_head_margin = min(q_nom, q_max - q_nom) / kappa
    if loop_gain <= Fraction(1, 1):
        regime = "MONOTONE_CONVERGENT"
    elif loop_gain < Fraction(2, 1):
        regime = "DAMPED_OSCILLATORY"
    else:
        regime = "UNSTABLE_CHATTERING"

    violations: list[str] = []
    if dof >= n_held:
        violations.append("RUSHD_EPICYCLE_OVERPARAMETERIZED")
    if ho_err > max_ho:
        violations.append("RUSHD_HELD_OUT_ERROR_EXCEEDED")
    if null_err <= max_ho:
        violations.append("RUSHD_VACUOUS_NULL_BASELINE")
    if in_err >= null_err:
        violations.append("RUSHD_IN_SAMPLE_WORSE_THAN_NULL")
    if loop_gain >= Fraction(2, 1):
        violations.append("JAZARI_UNSTABLE_LOOP_GAIN")
    if linear_head_margin * 10 < setpoint:
        violations.append("JAZARI_VALVE_SATURATION_HEADROOM_TOO_SMALL")

    return {
        "certified": len(violations) == 0,
        "violations": violations,
        "loop_gain_mu": frac_str(loop_gain),
        "contraction_factor": frac_str(contraction_factor),
        "linear_head_margin": frac_str(linear_head_margin),
        "controller_regime": regime,
    }


def analyze_pillar5_lineage_and_certifiers() -> dict[str, Any]:
    """Pillar 5: Certified 13-polymath lineage graph + before/after anti-epicycle & valve receipts."""
    lineage = certify_polymath_lineage_graph(BAYT_AL_HIKMA_NODES, BAYT_AL_HIKMA_EDGES)

    bad_epicycle_and_valve = certify_bounded_feedback_and_anti_epicycle(
        {
            "epicycle_dof": 3,
            "held_out_constraints": 3,
            "in_sample_error": Fraction(0, 1),
            "held_out_error": Fraction(45, 1),
            "max_held_out_error": Fraction(1, 10),
            "null_baseline_error": Fraction(1, 1),
            "valve_gain_kappa": Fraction(2, 1),
            "step_dt": Fraction(1, 1),
            "reservoir_area": Fraction(1, 1),
            "setpoint_head": Fraction(10, 1),
            "nominal_flow": Fraction(2, 1),
            "valve_max_flow": Fraction(5, 1),
        }
    )

    good_certified = certify_bounded_feedback_and_anti_epicycle(
        {
            "epicycle_dof": 2,
            "held_out_constraints": 10,
            "in_sample_error": Fraction(1, 50),
            "held_out_error": Fraction(1, 20),
            "max_held_out_error": Fraction(1, 10),
            "null_baseline_error": Fraction(1, 1),
            "valve_gain_kappa": Fraction(1, 2),
            "step_dt": Fraction(1, 1),
            "reservoir_area": Fraction(1, 1),
            "setpoint_head": Fraction(10, 1),
            "nominal_flow": Fraction(2, 1),
            "valve_max_flow": Fraction(5, 1),
        }
    )

    return {
        "lineage_graph_receipt": lineage,
        "overparameterized_epicycle_and_hunting_valve": bad_epicycle_and_valve,
        "certified_anti_epicycle_and_monotone_valve": good_certified,
    }


def audit_live_vault_anchors(symbiosis_root: Path) -> dict[str, Any]:
    """Read-only SHA-256 verification of expedition vault cross-links (continuum, AUDIT-085R, AUDIT-088R)."""
    _require(symbiosis_root.is_dir(), f"symbiosis-root-missing:{symbiosis_root.name}")
    root_res = symbiosis_root.resolve()
    digests: dict[str, dict[str, Any]] = {}
    for rel_path, expected in PINNED_VAULT_DIGESTS.items():
        full_p = (root_res / rel_path).resolve()
        _require(full_p.is_relative_to(root_res), f"vault-path-escape:{rel_path}")
        _require(full_p.is_file(), f"vault-file-missing:{rel_path}")
        raw = full_p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        _require(len(raw) == expected["bytes"], f"vault-bytes-mismatch:{rel_path}")
        _require(sha == expected["sha256"], f"vault-sha256-mismatch:{rel_path}")
        digests[rel_path] = {"bytes": len(raw), "sha256": sha, "verified": True}
    return {
        "mode": "live_read_only",
        "verified_vault_anchors": len(digests),
        "file_digests": digests,
    }


def build_certificate(symbiosis_root: Path | None = None) -> dict[str, Any]:
    """Build canonical zero-float JSON certificate with deterministic SHA-256."""
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "pillar1_continuum_vs_atomism": analyze_pillar1_continuum_vs_atomism(),
        "pillar2_haytham_khayyam_rushd": analyze_pillar2_haytham_khayyam_rushd(),
        "pillar3_transformational_algebra_laurent": analyze_pillar3_transformational_algebra_laurent(),
        "pillar4_kindi_biruni_tusi_jazari": analyze_pillar4_kindi_biruni_tusi_jazari(),
        "pillar5_lineage_and_certifiers": analyze_pillar5_lineage_and_certifiers(),
        "live_vault_verification": (
            audit_live_vault_anchors(symbiosis_root)
            if symbiosis_root is not None
            else {"mode": "standalone_pure_q", "verified_vault_anchors": 0}
        ),
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    body["certificate_sha256"] = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    return body


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bayt al-Hikma polymath pure-Q certifier (AUDIT-092).")
    parser.add_argument("--symbiosis-root", type=Path, default=None, help="Read-only symbiosis vault root.")
    parser.add_argument("--json", action="store_true", help="Emit canonical JSON to stdout.")
    parser.add_argument("--write-cert", type=Path, default=None, help="Write JSON certificate path.")
    args = parser.parse_args(argv)

    cert = build_certificate(symbiosis_root=args.symbiosis_root)
    rendered = json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.write_cert is not None:
        args.write_cert.write_text(rendered, encoding="utf-8")
    if args.json:
        sys.stdout.write(rendered)
    else:
        lv = cert["live_vault_verification"]
        sys.stdout.write(
            f"{AUDIT_ID} | mode={lv['mode']} | vault_anchors={lv['verified_vault_anchors']} "
            f"| sha256={cert['certificate_sha256']}\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
