#!/usr/bin/env python3
"""Exact pure-Q mathematical verification engine for Bayt al-Hikma polymath studies (AUDIT-092R2).

Covers 13 scholars (c. 780-1274 CE):
  al-Khwarizmi, al-Kindi, Banu Musa, Thabit ibn Qurra, al-Karaji, Ibn al-Haytham,
  al-Biruni, Ibn Sina, Umar al-Khayyam, al-Samaw'al, Ibn Rushd, Isma'il al-Jazari,
  and Nasir al-Din al-Tusi.

Edge Direction Convention (Active Voice):
  Every edge {source, target, relation, source_ref} is read in active voice
  ("source <relation> target"): for teacher_of, source taught target; for
  corresponded_with, source and target exchanged letters as contemporaries; for
  extended, commented_on, and critiqued, the later actor (source) engaged the
  prior subject (target)'s work.

Epistemic & Novelty Classification (Law 4):
  N0 (reproducible pure-Q software transcription and encoding-consistency checks
  over classical historical mathematics and published secondary editions).

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


SCHEMA_VERSION = "bayt-al-hikma-polymath-lineage-v2"
AUDIT_ID = "AUDIT-092R2"

EDGE_DIRECTION_CONVENTION = (
    "Active voice ('source <relation> target'): for teacher_of, source taught target; "
    "for corresponded_with, source and target corresponded as contemporaries; for extended, "
    "commented_on, and critiqued, the later actor (source) engaged the prior subject (target)."
)

ALLOWED_CITATION_KEYS = frozenset({"work", "edition", "location"})
ALLOWED_NODE_KEYS = frozenset(
    {"node_id", "name", "birth_year", "death_year", "city", "primary_work", "source"}
)
ALLOWED_EDGE_KEYS = frozenset({"source", "target", "relation", "citation"})
ALLOWED_RELATIONS = ("teacher_of", "corresponded_with", "commented_on", "extended", "critiqued")
DIRECTED_ENGAGEMENT_RELATIONS = frozenset({"commented_on", "extended", "critiqued"})

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

BAYT_AL_HIKMA_NODES: tuple[dict[str, Any], ...] = (
    {
        "node_id": "khwarizmi",
        "name": "Muhammad ibn Musa al-Khwarizmi",
        "birth_year": 780,
        "death_year": 850,
        "city": "Baghdad",
        "primary_work": "al-Kitab al-Mukhtasar fi Hisab al-Jabr wa-l-Muqabala",
        "source": {
            "work": "Al-Khwarizmi: The Beginnings of Algebra",
            "edition": "R. Rashed, Saqi Books (2009)",
            "location": "pp. 8-22, 94-110",
        },
    },
    {
        "node_id": "kindi",
        "name": "Abu Yusuf Yaqub ibn Ishaq al-Kindi",
        "birth_year": 801,
        "death_year": 873,
        "city": "Baghdad",
        "primary_work": "Risala fi Istikhraj al-Muamma; De Gradibus",
        "source": {
            "work": "Al-Kindi's Treatise on Cryptanalysis; Arnaldi Opera II (De Gradibus)",
            "edition": "Mrayati et al., KFCRIS (2003); M. McVaugh, Granada (1975)",
            "location": "pp. 121-158; De Gradibus pp. 269-280",
        },
    },
    {
        "node_id": "banu_musa",
        "name": "Banu Musa (Muhammad ibn Musa ibn Shakir)",
        "birth_year": 803,
        "death_year": 873,
        "city": "Baghdad",
        "primary_work": "Kitab al-Hiyal (Book of Ingenious Devices)",
        "source": {
            "work": "The Book of Ingenious Devices (Kitab al-Hiyal)",
            "edition": "D. R. Hill, Reidel (1979)",
            "location": "pp. 3-15, Models 1-100",
        },
    },
    {
        "node_id": "thabit",
        "name": "Thabit ibn Qurra",
        "birth_year": 836,
        "death_year": 901,
        "city": "Harran / Baghdad",
        "primary_work": "Maqala fi Istikhraj al-Adad al-Mutahabba; Parabola Quadrature",
        "source": {
            "work": "Thabit ibn Qurra: Science and Philosophy in Ninth-Century Baghdad",
            "edition": "R. Rashed (ed.), de Gruyter (2009)",
            "location": "pp. 3-14, 155-209, 259-290",
        },
    },
    {
        "node_id": "karaji",
        "name": "Abu Bakr al-Karaji",
        "birth_year": 953,
        "death_year": 1029,
        "city": "Baghdad",
        "primary_work": "al-Fakhri fi al-Jabr wa-l-Muqabala",
        "source": {
            "work": "The Development of Arabic Mathematics: Between Arithmetic and Algebra",
            "edition": "R. Rashed, Kluwer (1994)",
            "location": "ch. 1, pp. 22-45",
        },
    },
    {
        "node_id": "haytham",
        "name": "Ibn al-Haytham",
        "birth_year": 965,
        "death_year": 1040,
        "city": "Basra / Cairo",
        "primary_work": "Kitab al-Manazir; al-Shukuk ala Batlamyus; Sharh Musadarat Uqlidis",
        "source": {
            "work": "The Optics of Ibn al-Haytham (Books I-III); al-Shukuk ala Batlamyus",
            "edition": "A. I. Sabra, Warburg (1989); Sabra & Shehaby, Cairo (1971)",
            "location": "Optics vol. 2 pp. xix-xxxii; al-Shukuk pp. 3-42",
        },
    },
    {
        "node_id": "biruni",
        "name": "Abu Rayhan al-Biruni",
        "birth_year": 973,
        "death_year": 1048,
        "city": "Khwarazm / Ghazna",
        "primary_work": "Tahdid Nihayat al-Amakin; al-Qanun al-Masudi; al-Asilah wa-l-Ajwibah",
        "source": {
            "work": "The Determination of the Coordinates of Positions (Tahdid)",
            "edition": "J. Ali (tr.), AUB (1967); E. S. Kennedy, AUB (1973)",
            "location": "Ali pp. 187-190; Kennedy pp. 139-144",
        },
    },
    {
        "node_id": "ibn_sina",
        "name": "Ibn Sina",
        "birth_year": 980,
        "death_year": 1037,
        "city": "Bukhara / Isfahan",
        "primary_work": "al-Shifa; al-Asilah wa-l-Ajwibah",
        "source": {
            "work": "Al-Asilah wa-l-Ajwibah (Questions and Answers)",
            "edition": "S. H. Nasr & M. Mohaghegh, ISTAC (1995)",
            "location": "pp. 1-62",
        },
    },
    {
        "node_id": "khayyam",
        "name": "Umar al-Khayyam",
        "birth_year": 1048,
        "death_year": 1131,
        "city": "Nishapur / Isfahan",
        "primary_work": "Risala fi Sharh ma Ashkala min Musadarat Uqlidis; Risala fi al-Jabr",
        "source": {
            "work": "Omar Khayyam the Mathematician",
            "edition": "R. Rashed & B. Vahabzadeh, Bibliotheca Persica (2000)",
            "location": "pp. 113-162, 217-244",
        },
    },
    {
        "node_id": "ibn_rushd",
        "name": "Ibn Rushd",
        "birth_year": 1126,
        "death_year": 1198,
        "city": "Cordoba / Marrakesh",
        "primary_work": "Tafsir ma Bad al-Tabia (Book Lambda)",
        "source": {
            "work": "Ibn Rushd's Metaphysics (Book Lam)",
            "edition": "C. Genequand, Brill (1984)",
            "location": "pp. 176-181; A. I. Sabra (1984) pp. 133-153",
        },
    },
    {
        "node_id": "samawal",
        "name": "al-Samawal ibn Yahya al-Maghribi",
        "birth_year": 1130,
        "death_year": 1180,
        "city": "Baghdad / Maragheh",
        "primary_work": "al-Bahir fi al-Jabr",
        "source": {
            "work": "Al-Bahir en Algebre d'As-Samawal",
            "edition": "S. Ahmad & R. Rashed, Damascus (1972)",
            "location": "pp. 20-58",
        },
    },
    {
        "node_id": "jazari",
        "name": "Ismail al-Jazari",
        "birth_year": 1136,
        "death_year": 1206,
        "city": "Diyarbakir",
        "primary_work": "Kitab fi Marifat al-Hiyal al-Handasiyya",
        "source": {
            "work": "The Book of Knowledge of Ingenious Mechanical Devices",
            "edition": "D. R. Hill, Reidel (1974)",
            "location": "pp. 17-34, Category I ch. 1",
        },
    },
    {
        "node_id": "tusi",
        "name": "Nasir al-Din al-Tusi",
        "birth_year": 1201,
        "death_year": 1274,
        "city": "Maragheh",
        "primary_work": "al-Tadhkira fi Ilm al-Haya; al-Risala al-Shafiya",
        "source": {
            "work": "Nasir al-Din al-Tusi's Memoir on Astronomy (al-Tadhkira)",
            "edition": "F. J. Ragep, Springer (1993)",
            "location": "vol. 1 pp. 194-223 (II.11)",
        },
    },
)

# Active voice: {source} <relation> {target}
BAYT_AL_HIKMA_EDGES: tuple[dict[str, Any], ...] = (
    {
        "source": "karaji",
        "target": "khwarizmi",
        "relation": "extended",
        "citation": {
            "work": "al-Fakhri fi al-Jabr wa-l-Muqabala",
            "edition": "R. Rashed, Kluwer (1994)",
            "location": "ch. 1, pp. 22-31 (polynomial powers beyond x^2)",
        },
    },
    {
        "source": "samawal",
        "target": "karaji",
        "relation": "extended",
        "citation": {
            "work": "al-Bahir fi al-Jabr",
            "edition": "S. Ahmad & R. Rashed, Damascus (1972)",
            "location": "pp. 20-38 (negative powers x^-n extending al-Karaji)",
        },
    },
    {
        "source": "khayyam",
        "target": "khwarizmi",
        "relation": "extended",
        "citation": {
            "work": "Risala fi al-Jabr wa-l-Muqabala",
            "edition": "R. Rashed & B. Vahabzadeh (2000)",
            "location": "pp. 113-135 (cubic classification extending 6 quadratics)",
        },
    },
    {
        "source": "haytham",
        "target": "thabit",
        "relation": "commented_on",
        "citation": {
            "work": "Sharh Musadarat Uqlidis",
            "edition": "R. Rashed, de Gruyter (2009); B. Rosenfeld (1988)",
            "location": "History of Non-Euclidean Geometry pp. 58-64",
        },
    },
    {
        "source": "khayyam",
        "target": "haytham",
        "relation": "extended",
        "citation": {
            "work": "Risala fi Sharh ma Ashkala min Musadarat Uqlidis",
            "edition": "R. Rashed & B. Vahabzadeh (2000)",
            "location": "Book I, pp. 217-235 (quadrilateral parallel-postulate critique)",
        },
    },
    {
        "source": "tusi",
        "target": "khayyam",
        "relation": "extended",
        "citation": {
            "work": "al-Risala al-Shafiya an al-Shakk fi al-Khutut al-Mutawaziya",
            "edition": "B. Rosenfeld, Springer (1988)",
            "location": "pp. 73-84 (parallel-postulate quadrilateral synthesis)",
        },
    },
    {
        "source": "tusi",
        "target": "haytham",
        "relation": "extended",
        "citation": {
            "work": "al-Tadhkira fi Ilm al-Haya",
            "edition": "F. J. Ragep, Springer (1993)",
            "location": "vol. 1 pp. 194-223 (resolving al-Shukuk equant objections)",
        },
    },
    {
        "source": "ibn_rushd",
        "target": "haytham",
        "relation": "commented_on",
        "citation": {
            "work": "Tafsir ma Bad al-Tabia (Book Lambda)",
            "edition": "A. I. Sabra, JHA 15 (1984)",
            "location": "pp. 133-153 (Andalusian physical astronomy critique)",
        },
    },
    {
        "source": "ibn_rushd",
        "target": "ibn_sina",
        "relation": "critiqued",
        "citation": {
            "work": "Tahafut al-Tahafut",
            "edition": "S. van den Bergh, Gibb Memorial (1954)",
            "location": "vol. 1 pp. 316-333 (critique of Avicennan metaphysics)",
        },
    },
    {
        "source": "biruni",
        "target": "ibn_sina",
        "relation": "corresponded_with",
        "citation": {
            "work": "al-Asilah wa-l-Ajwibah (18 Questions and Answers)",
            "edition": "S. H. Nasr & M. Mohaghegh, ISTAC (1995)",
            "location": "Questions 1-18, pp. 1-62",
        },
    },
    {
        "source": "haytham",
        "target": "kindi",
        "relation": "critiqued",
        "citation": {
            "work": "Kitab al-Manazir (Book I) & Discourse on Light",
            "edition": "A. I. Sabra, Warburg (1989); D. Lindberg (1976)",
            "location": "Theories of Vision pp. 58-67 (intromission vs extramission)",
        },
    },
    {
        "source": "ibn_sina",
        "target": "kindi",
        "relation": "commented_on",
        "citation": {
            "work": "al-Qanun fi al-Tibb & al-Shifa",
            "edition": "M. McVaugh, Granada (1975)",
            "location": "De Gradibus introduction pp. 15-24 (degree proportionality)",
        },
    },
    {
        "source": "banu_musa",
        "target": "thabit",
        "relation": "teacher_of",
        "citation": {
            "work": "Kitab al-Fihrist (Ibn al-Nadim); Thabit ibn Qurra",
            "edition": "R. Rashed (ed.), de Gruyter (2009)",
            "location": "pp. 4-7 (Muhammad ibn Musa mentoring Thabit in Baghdad)",
        },
    },
    {
        "source": "jazari",
        "target": "banu_musa",
        "relation": "extended",
        "citation": {
            "work": "Kitab fi Marifat al-Hiyal al-Handasiyya",
            "edition": "D. R. Hill, Reidel (1974)",
            "location": "pp. 12-15, 272 (explicitly citing Banu Musa float valves)",
        },
    },
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


def _require_citation(value: Any, name: str) -> dict[str, str]:
    _require(isinstance(value, dict), f"citation-dict:{name}")
    _require(set(value.keys()) == ALLOWED_CITATION_KEYS, f"citation-keys:{name}")
    return {
        "work": _require_clean_ascii(value["work"], f"{name}.work"),
        "edition": _require_clean_ascii(value["edition"], f"{name}.edition"),
        "location": _require_clean_ascii(value["location"], f"{name}.location"),
    }


def frac_str(value: Fraction) -> str:
    v = _require_exact_fraction(value, "frac_str")
    return f"{v.numerator}/{v.denominator}"


def frac_dec6(value: Fraction) -> str:
    """Truncate exact Fraction toward zero to 6 decimal places (conservative lower bound for v >= 0)."""
    v = _require_exact_fraction(value, "frac_dec6")
    sign = "-" if v < 0 else ""
    av = abs(v)
    scaled = (av.numerator * 1_000_000) // av.denominator
    whole, rem = divmod(scaled, 1_000_000)
    return f"{sign}{whole}.{rem:06d}"


def frac_dec6_ceil(value: Fraction) -> str:
    """Round non-negative exact Fraction strictly UP to 6 decimal places (conservative upper bound)."""
    v = _require_exact_fraction(value, "frac_dec6_ceil")
    _require(v >= 0, "frac-dec6-ceil-nonneg")
    scaled = (v.numerator * 1_000_000 + v.denominator - 1) // v.denominator
    whole, rem = divmod(scaled, 1_000_000)
    return f"{whole}.{rem:06d}"


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
    sample_n = (1, 2, 3, 6, 12)
    v2_checks = []
    for nv in sample_n:
        lhs = 2 * nv * nv
        v2_lhs = _v2_exact(lhs)
        v2_checks.append({"N": nv, "2N^2": lhs, "v2_2N2": v2_lhs, "v2_odd": (v2_lhs % 2) == 1})

    euclid_diag_sq = Fraction(2, 1)
    linf_diag_sq = Fraction(1, 1)
    squared_metric_distortion = euclid_diag_sq / linf_diag_sq
    concentric_inner_step = Fraction(1, 2)

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
    """Exact coefficients (c4, c3, c2, c1, c0) of Alhazen's reflection quartic P(t) = 0 on unit circle."""
    ax, ay = _require_exact_fraction(a_pt[0], "ax"), _require_exact_fraction(a_pt[1], "ay")
    bx, by = _require_exact_fraction(b_pt[0], "bx"), _require_exact_fraction(b_pt[1], "by")

    def _poly_mul_deg2(
        u: tuple[Fraction, Fraction, Fraction], v: tuple[Fraction, Fraction, Fraction]
    ) -> list[Fraction]:
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
    comb = [p1[k] + p2[k] for k in range(5)]
    return (comb[4], comb[3], comb[2], comb[1], comb[0])


def _eval_poly_desc(coeffs: Sequence[Fraction], x: Fraction) -> Fraction:
    acc = Fraction(0, 1)
    for c in coeffs:
        acc = acc * x + c
    return acc


def analyze_pillar2_haytham_khayyam_rushd() -> dict[str, Any]:
    """Pillar 2: Alhazen quartic non-constructibility, Haytham-Khayyam curvature trichotomy, Ibn Rushd witness."""
    sym_coeffs = alhazen_quartic_coeffs((Fraction(2, 1), Fraction(1, 1)), (Fraction(2, 1), Fraction(-1, 1)))
    sym_at_zero = _eval_poly_desc(sym_coeffs, Fraction(0, 1))

    raw_coeffs = alhazen_quartic_coeffs((Fraction(2, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(3, 1)))
    sign_flip = Fraction(-1, 1) if raw_coeffs[0] < 0 else Fraction(1, 1)
    q_coeffs = tuple(sign_flip * c for c in raw_coeffs)

    rat_roots_p: list[str] = []
    for num in _positive_divisors(int(q_coeffs[-1])):
        for den in _positive_divisors(int(q_coeffs[0])):
            for sgn in (-1, 1):
                cand = Fraction(sgn * num, den)
                if _eval_poly_desc(q_coeffs, cand) == 0:
                    rat_roots_p.append(frac_str(cand))

    probe_pts = (Fraction(-3, 1), Fraction(-1, 1), Fraction(-1, 5), Fraction(1, 2), Fraction(3, 1))
    probe_signs = [1 if _eval_poly_desc(q_coeffs, x) > 0 else -1 for x in probe_pts]
    sign_changes = sum(1 for i in range(len(probe_signs) - 1) if probe_signs[i] * probe_signs[i + 1] < 0)

    shift = -q_coeffs[1] / (4 * q_coeffs[0])
    asc_orig = list(reversed(q_coeffs))
    dep_asc = [Fraction(0, 1)] * 5
    for k, ck in enumerate(asc_orig):
        for j in range(k + 1):
            dep_asc[j] += ck * math.comb(k, j) * (shift ** (k - j))
    dep_monic = [x / dep_asc[4] for x in dep_asc]
    r_d, q_d, p_d = dep_monic[0], dep_monic[1], dep_monic[2]
    res_frac = (Fraction(1, 1), 2 * p_d, p_d * p_d - 4 * r_d, -(q_d * q_d))
    lcm_den = math.lcm(*(c.denominator for c in res_frac))
    res_int = [int(c * lcm_den) for c in res_frac]
    gcd_all = math.gcd(*(abs(c) for c in res_int))
    res_int = [c // gcd_all for c in res_int]
    res_poly = tuple(Fraction(c, 1) for c in res_int)

    rat_roots_res: list[str] = []
    for num in _positive_divisors(res_int[-1]):
        for den in _positive_divisors(res_int[0]):
            for sgn in (-1, 1):
                cand = Fraction(sgn * num, den)
                if _eval_poly_desc(res_poly, cand) == 0:
                    rat_roots_res.append(frac_str(cand))

    cos_hyp = Fraction(3, 4) * Fraction(5, 12)
    cos_euc = Fraction(0, 1)
    cos_sph = -Fraction(3, 5) * Fraction(5, 13)

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
    """Exact pure-Q implementation of al-Khwarizmi's al-jabr (restoration) + al-muqabala (balancing)."""
    _require(isinstance(lhs, tuple) and len(lhs) == 3, "khwarizmi-lhs-len")
    _require(isinstance(rhs, tuple) and len(rhs) == 3, "khwarizmi-rhs-len")
    l_f = tuple(_require_exact_fraction(v, f"lhs[{i}]") for i, v in enumerate(lhs))
    r_f = tuple(_require_exact_fraction(v, f"rhs[{i}]") for i, v in enumerate(rhs))

    a = l_f[0] - r_f[0]
    b = l_f[1] - r_f[1]
    c = l_f[2] - r_f[2]
    _require(not (a == 0 and b == 0), "khwarizmi-degenerate-no-unknown")

    lead = a if a != 0 else b
    if lead < 0:
        a, b, c = -a, -b, -c

    if a == 0:
        _require(-c > 0, "khwarizmi-no-positive-root")
        root = (-c) / b
        return {"canonical_type": 3, "form": "bx = c", "p": frac_str(b), "q": frac_str(-c), "positive_root": frac_str(root)}

    p = b / a
    q = c / a
    if q == 0:
        _require(p < 0, "khwarizmi-no-positive-root")
        return {"canonical_type": 1, "form": "x^2 = px", "p": frac_str(-p), "q": "0/1", "positive_root": frac_str(-p)}
    if p == 0 and q < 0:
        return {"canonical_type": 2, "form": "x^2 = q", "p": "0/1", "q": frac_str(-q), "discriminant": frac_str(-q)}
    if p > 0 and q < 0:
        rhs_q = -q
        disc = (p / 2) ** 2 + rhs_q
        return {"canonical_type": 4, "form": "x^2 + px = q", "p": frac_str(p), "q": frac_str(rhs_q), "discriminant": frac_str(disc)}
    if p < 0 and q > 0:
        rhs_p = -p
        disc = (rhs_p / 2) ** 2 - q
        _require(disc >= 0, "khwarizmi-complex-roots")
        return {"canonical_type": 5, "form": "x^2 + q = px", "p": frac_str(rhs_p), "q": frac_str(q), "discriminant": frac_str(disc)}
    if p < 0 and q < 0:
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
    """Pillar 3: al-Khwarizmi 6-form reducer + al-Karaji/al-Samaw'al Laurent ring Q[x, x^-1]."""
    flagship = reduce_khwarizmi_quadratic(
        (Fraction(2, 1), Fraction(7, 1), Fraction(-9, 1)),
        (Fraction(1, 1), Fraction(-3, 1), Fraction(30, 1)),
    )
    flagship_root = Fraction(3, 1)
    flagship_check = flagship_root**2 + 10 * flagship_root == Fraction(39, 1)

    type1 = reduce_khwarizmi_quadratic((Fraction(3, 1), Fraction(0, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(15, 1), Fraction(0, 1)))
    type2 = reduce_khwarizmi_quadratic((Fraction(2, 1), Fraction(0, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(0, 1), Fraction(18, 1)))
    type3 = reduce_khwarizmi_quadratic((Fraction(0, 1), Fraction(4, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(0, 1), Fraction(12, 1)))
    type5 = reduce_khwarizmi_quadratic((Fraction(1, 1), Fraction(0, 1), Fraction(21, 1)), (Fraction(0, 1), Fraction(10, 1), Fraction(0, 1)))
    type6 = reduce_khwarizmi_quadratic((Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)), (Fraction(0, 1), Fraction(3, 1), Fraction(4, 1)))

    one_minus_inv = {0: Fraction(1, 1), -1: Fraction(-1, 1)}
    geom5 = {-k: Fraction(1, 1) for k in range(6)}
    prod_geom = laurent_mul(one_minus_inv, geom5)
    mon_prod = laurent_mul({-2: Fraction(3, 1)}, {2: Fraction(1, 3)})

    # Exact polynomial ring Q[q] Schur-complement numerator on K = [[q^2, q], [q, 1-q]]
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
        "samawal_laurent_ring_identities": {
            "geom_identity_prod": {str(k): frac_str(v) for k, v in sorted(prod_geom.items())},
            "geom_identity_exact": prod_geom == {0: Fraction(1, 1), -6: Fraction(-1, 1)},
            "negative_exponent_inverse_exact": mon_prod == {0: Fraction(1, 1)},
            "schur_numerator_k11_S": {str(k): frac_str(v) for k, v in sorted(schur_num.items())},
            "schur_numerator_exact_neg_q3": schur_num == {3: Fraction(-1, 1)},
        },
    }


def analyze_pillar4_kindi_biruni_tusi_jazari() -> dict[str, Any]:
    """Pillar 4: al-Kindi, al-Biruni Nandana sexagesimal sensitivity, al-Tusi couple, al-Jazari float valve."""
    # 4A. al-Kindi De Gradibus (2^n) + frequency-null permutation invariance
    de_gradibus = {f"degree_{n}": 2**n for n in range(5)}
    plain_freqs = (Fraction(1, 2), Fraction(1, 4), Fraction(1, 8), Fraction(1, 8))
    cipher_freqs = (plain_freqs[1], plain_freqs[2], plain_freqs[3], plain_freqs[0])
    unif = Fraction(1, 4)
    l1_plain = sum((abs(f - unif) for f in plain_freqs), Fraction(0, 1))
    l1_cipher = sum((abs(f - unif) for f in cipher_freqs), Fraction(0, 1))

    # 4B. al-Biruni Nandana horizon-dip geodesy (Tahdid, c. 1025 CE; Ali 1967 pp. 187-190; Kennedy 1973 pp. 139-144)
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

    # Exact base-60 truncation sensitivity table across 2, 3, 4, and 5 sexagesimal places of cos(34')
    # True base-60 expansion: cos(34') = 0; 59, 59, 49, 26, 09, 26, ...
    cos34_sex_digits = (59, 59, 49, 26, 9)
    trunc_sensitivity: dict[str, dict[str, Any]] = {}
    r_sex3 = Fraction(0, 1)
    cos_sex3 = Fraction(0, 1)
    for n_places in (2, 3, 4, 5):
        c_val = Fraction(0, 1)
        denom = 1
        for d in cos34_sex_digits[:n_places]:
            denom *= 60
            c_val += Fraction(d, denom)
        r_val = h_biruni * c_val / (Fraction(1, 1) - c_val)
        if n_places == 3:
            cos_sex3 = c_val
            r_sex3 = r_val
        trunc_sensitivity[f"places_{n_places}"] = {
            "sexagesimal_digits": list(cos34_sex_digits[:n_places]),
            "cos34_fraction": frac_str(c_val),
            "radius_fraction": frac_str(r_val),
            "radius_dec6": frac_dec6(r_val),
        }

    biruni_reported = 12_803_337
    a33 = Fraction(33, 10_800) * pi_lo
    a35 = Fraction(35, 10_800) * pi_lo
    c33 = Fraction(1, 1) - (a33 * a33) / 2 + (a33**4) / 24
    c35 = Fraction(1, 1) - (a35 * a35) / 2 + (a35**4) / 24
    r33 = h_biruni * c33 / (Fraction(1, 1) - c33)
    r35 = h_biruni * c35 / (Fraction(1, 1) - c35)
    refraction_bias_factor = Fraction(7, 6)

    # 4C. Nasir al-Din al-Tusi couple (1261 CE) via exact Weierstrass rational t = tan(theta/2)
    r_inner = Fraction(1, 1)
    t_grid = (Fraction(0, 1), Fraction(1, 3), Fraction(1, 2), Fraction(1, 1), Fraction(2, 1), Fraction(3, 1), Fraction(5, 1))
    tusi_rows = []
    for t in t_grid:
        cos_th = (Fraction(1, 1) - t * t) / (Fraction(1, 1) + t * t)
        sin_th = (2 * t) / (Fraction(1, 1) + t * t)
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

    jazari_monotone = _sim_valve(Fraction(1, 2), Fraction(1, 1), 4)
    jazari_osc = _sim_valve(Fraction(3, 2), Fraction(1, 1), 4)
    jazari_hunt = _sim_valve(Fraction(2, 1), Fraction(1, 1), 4)
    jazari_diverge = _sim_valve(Fraction(5, 2), Fraction(1, 1), 4)

    return {
        "kindi_de_gradibus_and_frequency_null": {
            "de_gradibus_2_pow_n": de_gradibus,
            "plain_l1_from_uniform": frac_str(l1_plain),
            "cipher_l1_from_uniform": frac_str(l1_cipher),
            "permutation_invariant_exact": l1_plain == l1_cipher and l1_plain > 0,
        },
        "biruni_nandana_geodesy_analysis": {
            "historical_input_sources": [
                "J. Ali (tr.), The Determination of the Coordinates of Positions (Beirut: AUB, 1967), pp. 187-190",
                "E. S. Kennedy, A Commentary upon Biruni's Kitab Tahdid al-Amakin (Beirut: AUB, 1973), pp. 139-144",
            ],
            "epistemic_status": "ARITHMETIC_FIT_HYPOTHESIS_SINGLE_NUMBER",
            "height_cubits": frac_str(h_biruni),
            "exact_r34_bracket_dec6_conservative": [frac_dec6(r34_lo), frac_dec6_ceil(r34_hi)],
            "sexagesimal_truncation_sensitivity": trunc_sensitivity,
            "sexagesimal_3place_cos34": frac_str(cos_sex3),
            "sexagesimal_3place_r": frac_str(r_sex3),
            "sexagesimal_3place_r_dec6": frac_dec6(r_sex3),
            "biruni_tahdid_reported_cubits": biruni_reported,
            "abs_diff_cubits_dec6": frac_dec6(abs(r_sex3 - biruni_reported)),
            "matches_reported_integer_within_1_cubit": abs(r_sex3 - biruni_reported) < Fraction(1, 1),
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
    """Fail-closed active-voice encoding-consistency checker for the Bayt al-Hikma lineage dataset.

    Edge direction convention (active voice): every edge {source, target, relation, citation}
    means `source <relation> target`. For extended, commented_on, and critiqued, source is the
    later actor engaging target's prior work; influence-order DAG edges therefore run
    teacher->student for teacher_of and target->source for engagement relations.
    """
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
        _require_citation(node["source"], f"node.source[{idx}]")
        birth = _require_exact_int(node["birth_year"], f"birth_year[{idx}]")
        death = _require_exact_int(node["death_year"], f"death_year[{idx}]")
        _require(birth < death, f"lineage-lifespan-order:{nid}")
        low = nid.lower()
        _require(low not in seen_lower, f"lineage-duplicate-node:{nid}")
        seen_lower.add(low)
        by_id[nid] = node

    # Influence-order adjacency (earlier -> later) for cycle checking
    influence_adj: dict[str, list[str]] = {nid: [] for nid in by_id}
    seen_edges: set[tuple[str, str, str]] = set()
    chronology_violations: list[str] = []

    for idx, edge in enumerate(edges):
        _require(isinstance(edge, dict), f"lineage-edge-dict:{idx}")
        _require(set(edge.keys()) == ALLOWED_EDGE_KEYS, f"lineage-edge-keys:{idx}")
        src = _require_clean_ascii(edge["source"], f"edge.source[{idx}]")
        dst = _require_clean_ascii(edge["target"], f"edge.target[{idx}]")
        rel = _require_exact_choice(edge["relation"], ALLOWED_RELATIONS, f"edge.relation[{idx}]")
        _require_citation(edge["citation"], f"edge.citation[{idx}]")
        _require(src in by_id, f"lineage-unknown-source:{src}")
        _require(dst in by_id, f"lineage-unknown-target:{dst}")
        _require(src != dst, f"lineage-self-loop:{src}")
        ekey = (min(src, dst), max(src, dst), rel) if rel == "corresponded_with" else (src, dst, rel)
        _require(ekey not in seen_edges, f"lineage-duplicate-edge:{src}->{dst}:{rel}")
        seen_edges.add(ekey)

        s_node, d_node = by_id[src], by_id[dst]
        if rel == "teacher_of":
            if s_node["birth_year"] + 10 > d_node["birth_year"]:
                chronology_violations.append(f"CHRONO_TEACHER_AGE_GAP:{src}->{dst}")
            elif d_node["birth_year"] + 12 > min(s_node["death_year"], d_node["death_year"]):
                chronology_violations.append(f"CHRONO_TEACHER_OVERLAP:{src}->{dst}")
            influence_adj[src].append(dst)
        elif rel == "corresponded_with":
            overlap = min(s_node["death_year"], d_node["death_year"]) - max(
                s_node["birth_year"], d_node["birth_year"]
            )
            if overlap < 15:
                chronology_violations.append(f"CHRONO_CORRESPONDENCE_NO_OVERLAP:{src}<->{dst}")
        else:
            # Active voice: actor=src engaged prior subject=dst
            if s_node["birth_year"] + 15 > s_node["death_year"]:
                chronology_violations.append(f"CHRONO_IMMATURE_ACTOR:{src}->{dst}")
            if d_node["birth_year"] + 15 > d_node["death_year"]:
                chronology_violations.append(f"CHRONO_IMMATURE_SUBJECT:{src}->{dst}")
            if s_node["death_year"] < d_node["birth_year"] + 15:
                chronology_violations.append(f"CHRONO_ACTOR_DIED_BEFORE_SUBJECT_MATURITY:{src}->{dst}")
            if s_node["birth_year"] < d_node["birth_year"]:
                chronology_violations.append(f"CHRONO_ACTOR_PRECEDES_SUBJECT:{src}->{dst}")
            influence_adj[dst].append(src)

    # Exact 3-color DFS cycle detection on forward-time influence graph
    color: dict[str, int] = {nid: 0 for nid in by_id}
    has_cycle = False

    def _dfs(u: str) -> bool:
        color[u] = 1
        for v in influence_adj[u]:
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
        "encoding_consistency_only": True,
        "edge_direction_convention": EDGE_DIRECTION_CONVENTION,
        "node_count": len(by_id),
        "edge_count": len(seen_edges),
        "all_nodes_and_edges_cited": True,
        "chronology_violations": chronology_violations,
        "directed_dag_acyclic": not has_cycle,
    }


def certify_bounded_feedback_and_anti_epicycle(spec: Any) -> dict[str, Any]:
    """Unified fail-closed anti-epicycle DOF/null gate + discrete float-valve stability gate."""
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
    """Pillar 5: 13-scholar active-voice encoding-consistency check + anti-epicycle & valve receipts."""
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


def build_certificate() -> dict[str, Any]:
    """Build self-contained canonical zero-float JSON certificate with deterministic SHA-256."""
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "execution_mode": "standalone_pure_q",
        "novelty_classification": {
            "honest_tier": "N0",
            "rationale": (
                "All mathematical theorems and historical reconstructions are N0 classical prior art; "
                "this package provides reproducible pure-Q stdlib verification scripts and encoding-"
                "consistency checks without claiming N1 mathematical novelty."
            ),
        },
        "pillar1_continuum_vs_atomism": analyze_pillar1_continuum_vs_atomism(),
        "pillar2_haytham_khayyam_rushd": analyze_pillar2_haytham_khayyam_rushd(),
        "pillar3_transformational_algebra_laurent": analyze_pillar3_transformational_algebra_laurent(),
        "pillar4_kindi_biruni_tusi_jazari": analyze_pillar4_kindi_biruni_tusi_jazari(),
        "pillar5_lineage_and_certifiers": analyze_pillar5_lineage_and_certifiers(),
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    body["certificate_sha256"] = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    return body


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bayt al-Hikma polymath pure-Q certifier (AUDIT-092R2).")
    parser.add_argument("--json", action="store_true", help="Emit canonical JSON to stdout.")
    parser.add_argument("--write-cert", type=Path, default=None, help="Write JSON certificate path.")
    args = parser.parse_args(argv)

    cert = build_certificate()
    rendered = json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.write_cert is not None:
        args.write_cert.write_text(rendered, encoding="utf-8")
    if args.json:
        sys.stdout.write(rendered)
    else:
        sys.stdout.write(
            f"{AUDIT_ID} | mode={cert['execution_mode']} | tier={cert['novelty_classification']['honest_tier']} "
            f"| sha256={cert['certificate_sha256']}\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
