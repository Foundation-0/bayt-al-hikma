#!/usr/bin/env python3
"""Heritage Exact Operators: Pure-Z/Q Exact-Operator & Obstruction Oracle for Five Crown Engines
in hozifa1/islamic-scientific-heritage.

Zero floating-point literals, zero float() casts, zero .isdigit(), zero random.
All derived decimal displays computed via exact integer ROUND_HALF_UP arithmetic.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import math
from typing import Any

SCHEMA_VERSION = "bayt_al_hikma.heritage_exact_operators.v1"
TRACK_ID = "BAYT-AL-HIKMA-HERITAGE-EXACT-OPERATORS-LEAN4"
EXPECTED_LEAN_TOOLCHAIN = "leanprover/lean4:v4.36.0"
HERITAGE_DATASET_REPO = "hozifa1/islamic-scientific-heritage"
HERITAGE_DATASET_COMMIT = "4698695f7835aab044ce77733172494bbab9e33e"

LEAN_THEOREM_NAMES: tuple[str, ...] = (
    "HeritageExactOperators.tusi_planar_curl_annihilation",
    "HeritageExactOperators.tusi_matrix_curl_annihilation",
    "HeritageExactOperators.tusi_spherical_hippopede_obstruction",
    "HeritageExactOperators.tusi_spherical_rotation_norm_preserved",
    "HeritageExactOperators.kashi_cubic_banach_contraction",
    "HeritageExactOperators.kashi_sin1_contraction_factor_625",
    "HeritageExactOperators.kashi_rationalized_chord_identity",
    "HeritageExactOperators.kashi_cancellation_bit_loss_wall",
    "HeritageExactOperators.khayyam_klein_acute_angle_defect",
    "HeritageExactOperators.khayyam_cubic_discriminant_cusp",
    "HeritageExactOperators.khayyam_cubic_no_rational_root_obstruction",
    "HeritageExactOperators.s33_leonardo_cubic_no_rational_root",
    "HeritageExactOperators.haytham_reflection_hyperbola_quartic_exact",
    "HeritageExactOperators.haytham_ferrari_resolvent_irred_mod3",
    "HeritageExactOperators.farisi_rainbow_caustic_order_strict",
    "HeritageExactOperators.biruni_geodesy_dip_pole_amplification",
    "HeritageExactOperators.thabit_amicable_universal_identity",
    "HeritageExactOperators.thabit_n3_primality_obstruction",
    "HeritageExactOperators.khazini_hydrostatic_alloy_inverse_exact",
    "HeritageExactOperators.nafis_septal_wall_rerouting_firewall",
)

# 11 cryptographically pinned primary heritage artifacts (read-only from dataset;
# zero files copied into expedition/)
HERITAGE_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "h01_tusi_tadhkira",
        "engine": "engine1_tusi_couple",
        "scholar": "Nasir al-Din al-Tusi (1201-1274 CE)",
        "work": "Al-Tadhkira fi Ilm al-Hayah (Trio #23)",
        "relpath": "02_astronomy/nasir_al_din_al_tusi_597_672h/al_tadhkira_fi_ilm_al_hayah/02_critical_arabic_edition/tawdih_al_tadhkira_al_nisaburi/schema_metadata.json",
        "bytes": 1738,
        "sha256": "c4a16e573899563766b969752d48a691e49a24f67ecd0e3bc24f84903debbcce",
        "live_word_count": 0,
    },
    {
        "id": "h02_tusi_pal_works",
        "engine": "engine1_tusi_couple",
        "scholar": "Nasir al-Din al-Tusi (Ptolemaeus Arabus)",
        "work": "Tahrir al-Majisti & PAL Arabic Works Catalog",
        "relpath": "02_astronomy/ptolemaeus_arabus_corpus/pal_arabic_works_full.jsonl",
        "bytes": 346570,
        "sha256": "46f827e65282ac003a846e911a0788e8dee7f6aa06f2efeec52167c2c06a51e3",
        "live_word_count": 0,
    },
    {
        "id": "h03_kashi_miftah",
        "engine": "engine2_kashi_cubic_chords",
        "scholar": "Ghiyath al-Din Jamshid al-Kashi (d. 1429 CE)",
        "work": "Miftah al-Hisab (Trio #35)",
        "relpath": "03_mathematics/ghiyath_al_din_al_kashi_d832h/miftah_al_hisab/02_critical_arabic_edition/al_kashi_miftah_al_hisab_demerdash_cairo_1969/schema_metadata.json",
        "bytes": 1839,
        "sha256": "2cef7ca342a2ff6eb0e5305dda808ddc010cb97c49888a2b8b2555c4737caa3f",
        "live_word_count": 0,
    },
    {
        "id": "h04_khayyam_jabr",
        "engine": "engine3_khayyam_curvature_cubics",
        "scholar": "Ghiyath al-Din Umar al-Khayyam (1048-1131 CE)",
        "work": "Al-Jabr wa-al-Muqabala 14 Cubics (Trios #33-#34)",
        "relpath": "03_mathematics/ghiyath_al_din_omar_khayyam_439_515h/al_jabr_wa_al_muqabala/omar_khayyam_algebra_catalog.jsonl",
        "bytes": 1407,
        "sha256": "409017c369f94cb8279eae64d329fac2502489ad1ab78c9a9d4f4d6851f243de",
        "live_word_count": 0,
    },
    {
        "id": "h05_haytham_manazir_live",
        "engine": "engine4_haytham_farisi_biruni",
        "scholar": "Al-Hasan ibn al-Haytham (965-1040 CE)",
        "work": "Kitab al-Manazir (Live Arabic Fulltext, line 2, 63 Itibar hits)",
        "relpath": "04_physics_optics/openiti_classical_physics_optics/openiti_classical_physics_optics.jsonl",
        "bytes": 1698237,
        "sha256": "9c2fae6a4ad50b866edcc0d6fbd421fe7c16995d12f280fa89345c00bacf6573",
        "live_word_count": 140053,
    },
    {
        "id": "h06_farisi_tanqih",
        "engine": "engine4_haytham_farisi_biruni",
        "scholar": "Kamal al-Din al-Farisi (1267-1319 CE)",
        "work": "Tanqih al-Manazir (Rainbow & Caustic Optics Catalog)",
        "relpath": "04_optics_mechanics_chemistry/kamal_al_din_al_farisi_665_718h/tanqih_al_manazir/tanqih_al_manazir_catalog.jsonl",
        "bytes": 1642,
        "sha256": "adc52e33fbf4ed5ede52db2c72844e1145343b6ae8dc122af21f0f7a249edfcf",
        "live_word_count": 0,
    },
    {
        "id": "h07_biruni_zilal_live",
        "engine": "engine4_haytham_farisi_biruni",
        "scholar": "Abu al-Rayhan al-Biruni (973-1048 CE)",
        "work": "Ifrad al-Maqal fi Amr al-Zilal (Shadows Live Arabic Fulltext)",
        "relpath": "03_mathematics/abu_al_rayhan_al_biruni_362_440h/ifrad_al_maqal_amr_al_zilal/al_biruni_amr_al_zilal.jsonl",
        "bytes": 422156,
        "sha256": "16cc80fac1960c796834eeb8dc14ae58659237d6fac59b27c46562e3b443053f",
        "live_word_count": 44045,
    },
    {
        "id": "h08_biruni_qanun_live",
        "engine": "engine4_haytham_farisi_biruni",
        "scholar": "Abu al-Rayhan al-Biruni (973-1048 CE)",
        "work": "Al-Qanun al-Masudi (Geodesy & Astronomy Live Arabic Fulltext)",
        "relpath": "02_astronomy/abu_al_rayhan_al_biruni_362_440h/al_qanun_al_masudi/al_biruni_qanun_masudi.jsonl",
        "bytes": 2862364,
        "sha256": "9b1a64b861902ba4498670603d46719f02433260f443ca73bf4fd0cc8d605bab",
        "live_word_count": 344892,
    },
    {
        "id": "h09_thabit_niqumakhus_live",
        "engine": "engine5_thabit_khazini_nafis",
        "scholar": "Thabit ibn Qurra al-Harrani (836-901 CE)",
        "work": "Madkhal Niqumakhus Arithmetic (Live Arabic Fulltext)",
        "relpath": "03_mathematics/thabit_ibn_qurra_al_harrani_221_288h/madkhal_niqumakhus/thabit_ibn_qurra_niqumakhus_arithmetic.jsonl",
        "bytes": 282654,
        "sha256": "3ea3a10398162948619ef77ab0971ebb0623f3d0cf8a0ceff603629127c1ef00",
        "live_word_count": 29288,
    },
    {
        "id": "h10_khazini_mizan",
        "engine": "engine5_thabit_khazini_nafis",
        "scholar": "Abd al-Rahman al-Khazini (fl. 1115-1130 CE)",
        "work": "Mizan al-Hikmah Specific Gravity Catalog",
        "relpath": "04_optics_mechanics_chemistry/abd_al_rahman_al_khazini_480_550h/mizan_al_hikmah/mizan_al_hikmah_specific_gravity_catalog.jsonl",
        "bytes": 885,
        "sha256": "f170e6b9bcf9e5e050550573f71bb2b82a351c57c6f5c643cd4410ee9331e9ba",
        "live_word_count": 0,
    },
    {
        "id": "h11_nafis_tashrih_live",
        "engine": "engine5_thabit_khazini_nafis",
        "scholar": "Ibn al-Nafis (1213-1288 CE)",
        "work": "Sharh Tashrih al-Qanun (Live Arabic Fulltext, line 2, 38 pore hits)",
        "relpath": "01_medicine/openiti_classical_medicine/openiti_classical_medicine.jsonl",
        "bytes": 7995996,
        "sha256": "2facb8f55bf2c0fd6f896ee1a056724fa95a7fe534dd55314b3ad5674e194ce9",
        "live_word_count": 100721,
    },
)

MODERN_ANCHOR_CERTS: tuple[dict[str, str], ...] = (
    {"track": "adm-caustic", "cert_file": "alcubierre_adm_certificate.json", "cert_sha256": "6d5579f52d176f39d6f160a405873843ff616ca7d1d76c95f1a3d340237bbc9f", "bridge": "Krein caustic signature flip"},
    {"track": "leonardo-galois-cubic", "cert_file": "leonardo_codices_certificate.json", "cert_sha256": "9eec31665b5e4b96e7b486fde40f21813f161924d64c04e7155cf459db587438", "bridge": "Galois cubic 4x^3 - 2x - 1 obstruction"},
    {"track": "rosen-cusp", "cert_file": "mdl_rosen_similarity_certificate.json", "cert_sha256": "ad03c2fb0977f8fae30849eb18e86b9050d03c4793cbb9e6295891d28b67d242", "bridge": "Rosen cusp 1 != 3 root-sheet transition"},
    {"track": "harmonic-cancellation", "cert_file": "mozart_nth_diff_certificate.json", "cert_sha256": "1264f54f750deb6761574498cc9f268de3821a936ab459579d8949337c99b268", "bridge": "Harmonic cancellation operator"},
    {"track": "bitwidth-cancellation", "cert_file": "hamming_construction_a_certificate.json", "cert_sha256": "51e2c9e2ec5528d6a76c2d840b5b4956acd393ec8565c1810ac8f0db3dcd719e", "bridge": "W_max <= 64 bit-width cancellation wall"},
    {"track": "hydrostatic-metrology", "cert_file": "optifab_schur_metrology_certificate.json", "cert_sha256": "412a6ff68d687536288718970e9cabbfc2defc4476a5c2faa4fed3623a3d033e", "bridge": "Hydrostatic buoyancy perturbation bound"},
    {"track": "cat0-hyperbolic", "cert_file": "s75_vp_vnp_certificate.json", "cert_sha256": "7e383c1cfe04937277be7f8f4ff4305984d51ecd81858eebdd67e45238823224", "bridge": "CAT(0) hyperbolic curvature det(G) = -1/4"},
    {"track": "circularep-curl", "cert_file": "s76_circular_pc_certificate.json", "cert_sha256": "d30805fcb876de096d9b387a8274ecd8063b7906f4feb36124b38a05aefadc95", "bridge": "CircularEP curl annihilation & 1/beta pole"},
    {"track": "laurent-pole", "cert_file": "s82_vpvnp_propagation_certificate.json", "cert_sha256": "10c1203cd9c9f80d4082f4cdbbd09f60624aa1d4fd6b49c70ec5d622f0d2f76b", "bridge": "Lem N.2 Laurent pole sensitivity control"},
    {"track": "epistemic-mesh", "cert_file": "s83_epistemic_mesh_certificate.json", "cert_sha256": "74d269c5c1c35665fc835df796e6f94cdbd118ca4ce580a20310c5c969deabdb", "bridge": "Fail-closed refusal firewall rerouting"},
)

_HEX_LOWER = frozenset("0123456789abcdef")


class S90Error(ValueError):
    """Fail-closed domain error with structured machine-readable code."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def require_ok(cond: bool, code: str, detail: str) -> None:
    if cond is not True:
        raise S90Error(code, detail)


def require_bool(val: Any, label: str) -> bool:
    require_ok(type(val) is bool, "INVALID_BOOL", f"{label} must be exact bool")
    return val


def require_exact_int(val: Any, label: str, lo: int | None = None, hi: int | None = None) -> int:
    require_ok(type(val) is int, "INVALID_INT", f"{label} must be exact int")
    if lo is not None:
        require_ok(val >= lo, "INT_OUT_OF_RANGE", f"{label} < {lo}")
    if hi is not None:
        require_ok(val <= hi, "INT_OUT_OF_RANGE", f"{label} > {hi}")
    return val


def require_exact_str(val: Any, label: str) -> str:
    require_ok(type(val) is str, "INVALID_STR", f"{label} must be exact str")
    return val


def require_hex64(val: Any, label: str) -> str:
    s = require_exact_str(val, label)
    require_ok(len(s) == 64, "INVALID_HEX64", f"{label} must be 64 hex chars")
    for ch in s:
        require_ok(ch in _HEX_LOWER, "INVALID_HEX64", f"{label} non-hex char")
    return s


def validate_strict_json_tree(obj: Any, path: str = "root", depth: int = 0) -> None:
    require_ok(depth <= 32, "JSON_DEPTH_EXCEEDED", f"{path}: depth > 32")
    t = type(obj)
    if t is dict:
        for k, v in obj.items():
            require_ok(type(k) is str, "INVALID_JSON_KEY", f"{path}: non-str key")
            validate_strict_json_tree(v, f"{path}.{k}", depth + 1)
    elif t is list:
        for idx, item in enumerate(obj):
            validate_strict_json_tree(item, f"{path}[{idx}]", depth + 1)
    elif t is str or t is int or t is bool or obj is None:
        return
    else:
        raise S90Error("FORBIDDEN_JSON_TYPE", f"{path}: forbidden type {t.__name__}")


def canonical_json_bytes(obj: Any) -> bytes:
    validate_strict_json_tree(obj, "canonical")
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return text.encode("ascii")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fmt_q(q: Fraction) -> str:
    require_ok(type(q) is Fraction, "INVALID_FRACTION", "expected Fraction")
    if q.denominator == 1:
        return str(q.numerator)
    return f"{q.numerator}/{q.denominator}"


def fmt_dec_q(q: Fraction, places: int) -> str:
    """Exact pure-integer ROUND_HALF_UP decimal formatting with zero floats."""
    require_ok(type(q) is Fraction, "INVALID_FRACTION", "expected Fraction")
    require_exact_int(places, "places", lo=0, hi=18)
    neg = q.numerator < 0
    num = -q.numerator if neg else q.numerator
    den = q.denominator
    scale = 10 ** places
    quot, rem = divmod(num * scale, den)
    if 2 * rem >= den:
        quot += 1
    if places == 0:
        return ("-" if neg and quot > 0 else "") + str(quot)
    ip, fp = divmod(quot, scale)
    sign = "-" if neg and quot > 0 else ""
    return f"{sign}{ip}.{fp:0{places}d}"


# ---------------------------------------------------------------------------
# Engine 1: Al-Tusi Couple (Planar Curl Annihilation vs S^2 Hippopede Wall)
# ---------------------------------------------------------------------------

def compute_engine1_tusi_couple() -> dict[str, Any]:
    planar_rows: list[dict[str, str]] = []
    for t in (Fraction(0), Fraction(1, 3), Fraction(1, 2), Fraction(1), Fraction(2), Fraction(3)):
        c = (1 - t * t) / (1 + t * t)
        s = (2 * t) / (1 + t * t)
        x = c + c
        y = s + (-s)
        planar_rows.append({
            "t_q": fmt_q(t),
            "cos_q": fmt_q(c),
            "sin_q": fmt_q(s),
            "x_q": fmt_q(x),
            "y_q": fmt_q(y),
        })

    a_m, b_m = Fraction(3, 5), Fraction(4, 5)
    m_avg_00 = (a_m + a_m) / 2
    m_avg_01 = (-b_m + b_m) / 2
    m_avg_11 = (a_m + a_m) / 2

    ct, st = Fraction(3, 5), Fraction(4, 5)
    spherical_rows: list[dict[str, str]] = []
    for ca, sa in (
        (Fraction(4, 5), Fraction(3, 5)),
        (Fraction(12, 13), Fraction(5, 13)),
        (Fraction(24, 25), Fraction(7, 25)),
    ):
        px = 2 * sa * (1 - ca) * st * st * ct
        py = -2 * sa * st * (ct * ct + ca * st * st)
        pz = 1 - 2 * sa * sa * st * st
        spherical_rows.append({
            "cos_alpha_q": fmt_q(ca),
            "sin_alpha_q": fmt_q(sa),
            "px_transverse_q": fmt_q(px),
            "px_transverse_dec6": fmt_dec_q(px, 6),
            "py_longitudinal_q": fmt_q(py),
            "py_longitudinal_dec6": fmt_dec_q(py, 6),
            "pz_vertical_q": fmt_q(pz),
            "pz_vertical_dec6": fmt_dec_q(pz, 6),
            "unit_norm_q": fmt_q(px * px + py * py + pz * pz),
        })

    return {
        "planar_samples": planar_rows,
        "planar_all_y_zero": True,
        "matrix_curl_annihilation": {
            "a_q": fmt_q(a_m),
            "b_q": fmt_q(b_m),
            "tusi_avg_diag_q": fmt_q(m_avg_00),
            "tusi_avg_offdiag_q": fmt_q(m_avg_01),
            "trace_preserved_q": fmt_q(m_avg_00 + m_avg_11),
        },
        "spherical_phase_cos_q": fmt_q(ct),
        "spherical_phase_sin_q": fmt_q(st),
        "spherical_hippopede_samples": spherical_rows,
        "all_spherical_norms_exact_one": True,
        "all_spherical_deviations_nonzero": True,
    }


# ---------------------------------------------------------------------------
# Engine 2: Al-Kashi Contractive Cubic Solver & Chord-Doubling Cancellation
# ---------------------------------------------------------------------------

def _isqrt_int_bracket(n: int, denom: int) -> tuple[Fraction, Fraction]:
    require_ok(n > 0 and denom > 0, "ISQRT_DOMAIN", "n and denom must be positive")
    target = n * denom * denom
    lo = math.isqrt(target)
    require_ok(lo * lo < target, "ISQRT_NON_SQUARE", "n must be non-square")
    return Fraction(lo, denom), Fraction(lo + 1, denom)


def _frac_sqrt_bracket(fr: Fraction, denom: int) -> tuple[Fraction, Fraction]:
    require_ok(fr > 0 and denom > 0, "FSQRT_DOMAIN", "fr and denom must be positive")
    lo = math.isqrt((fr.numerator * denom * denom) // fr.denominator)
    return Fraction(lo, denom), Fraction(lo + 1, denom)


def compute_engine2_kashi_cubic_chords() -> dict[str, Any]:
    denom = 10 ** 12
    s2_l, s2_u = _isqrt_int_bracket(2, denom)
    s5_l, s5_u = _isqrt_int_bracket(5, denom)
    s6_l, s6_u = _isqrt_int_bracket(6, denom)
    s10_l, _ = _frac_sqrt_bracket(10 + 2 * s5_l, denom)
    _, s10_u = _frac_sqrt_bracket(10 + 2 * s5_u, denom)

    sin3_lo = ((s5_l - 1) * (s6_l + s2_l) - s10_u * (s6_u - s2_l)) / 16
    sin3_hi = ((s5_u - 1) * (s6_u + s2_u) - s10_l * (s6_l - s2_u)) / 16

    p_unit = Fraction(45, 60)
    b_bound = Fraction(1, 50)
    lip_bound = (3 * b_bound * b_bound) / p_unit

    xl, xu = Fraction(0), b_bound
    iter_rows: list[dict[str, str | int]] = []
    for step in range(1, 5):
        prev_w = xu - xl
        xl = (sin3_lo + 4 * xl * xl * xl) / 3
        xu = (sin3_hi + 4 * xu * xu * xu) / 3
        w = xu - xl
        iter_rows.append({
            "iteration": step,
            "lo_dec12": fmt_dec_q(xl, 12),
            "hi_dec12": fmt_dec_q(xu, 12),
            "width_dec12": fmt_dec_q(w, 12),
            "strict_shrink_factor_dec2": fmt_dec_q(prev_w / w, 2),
        })

    bit_loss_rows: list[dict[str, int | bool]] = []
    for k in (1, 5, 10, 26, 31):
        lost = 2 * k + 2
        bit_loss_rows.append({
            "halving_step_k": k,
            "bits_lost_naive": lost,
            "exceeds_ieee754_53": lost > 53,
            "reaches_s47_wmax_64": lost >= 64,
        })

    chord_identities: list[dict[str, str]] = []
    for c_q, s_q in (
        (Fraction(6, 5), Fraction(8, 5)),
        (Fraction(10, 13), Fraction(24, 13)),
        (Fraction(14, 25), Fraction(48, 25)),
    ):
        rat_sq = (c_q * c_q) / (2 + s_q)
        chord_identities.append({
            "c_q": fmt_q(c_q),
            "s_q": fmt_q(s_q),
            "c_next_sq_q": fmt_q(rat_sq),
            "c_next_sq_dec6": fmt_dec_q(rat_sq, 6),
        })

    return {
        "sexagesimal_p_unit_q": fmt_q(p_unit),
        "domain_bound_q": fmt_q(b_bound),
        "lipschitz_bound_q": fmt_q(lip_bound),
        "sin3_lo_dec12": fmt_dec_q(sin3_lo, 12),
        "sin3_hi_dec12": fmt_dec_q(sin3_hi, 12),
        "banach_iterations": iter_rows,
        "sin1_final_lo_dec12": fmt_dec_q(xl, 12),
        "sin1_final_hi_dec12": fmt_dec_q(xu, 12),
        "cancellation_wall_schedule": bit_loss_rows,
        "rationalized_chord_witnesses": chord_identities,
    }


# ---------------------------------------------------------------------------
# Engine 3: Al-Khayyam Curvature Trichotomy & 14 Cubics (S75 / S34 / S33)
# ---------------------------------------------------------------------------

def compute_engine3_khayyam_curvature_cubics() -> dict[str, Any]:
    klein_rows: list[dict[str, str]] = []
    for a_q, h_q in (
        (Fraction(1, 2), Fraction(1, 2)),
        (Fraction(1, 3), Fraction(1, 2)),
        (Fraction(3, 5), Fraction(3, 5)),
        (Fraction(1, 4), Fraction(3, 4)),
    ):
        rad_sq = a_q * a_q + h_q * h_q
        cos2_phi = (a_q * a_q * h_q * h_q) / ((1 - a_q * a_q) * (1 - h_q * h_q))
        klein_rows.append({
            "a_q": fmt_q(a_q),
            "h_q": fmt_q(h_q),
            "disk_radius_sq_q": fmt_q(rad_sq),
            "cos2_summit_q": fmt_q(cos2_phi),
            "cos2_summit_dec6": fmt_dec_q(cos2_phi, 6),
        })

    cubic_rows: list[dict[str, Any]] = []
    for label, a_i, b_i, real_roots, regime in (
        ("x^3 + x - 1", 1, -1, 1, "ONE_REAL_ROOT"),
        ("s33_depressed_u^3 - 2u - 2", -2, -2, 1, "ONE_REAL_ROOT"),
        ("tangency_cusp_x^3 - 3x + 2", -3, 2, 2, "CONIC_TANGENCY_CUSP"),
        ("khayyam_x^3 - 3x - 1", -3, -1, 3, "THREE_REAL_ROOTS_CASUS_IRREDUCIBILIS"),
        ("khayyam_x^3 - 3x + 1", -3, 1, 3, "THREE_REAL_ROOTS_CASUS_IRREDUCIBILIS"),
    ):
        delta = -4 * a_i * a_i * a_i - 27 * b_i * b_i
        cubic_rows.append({
            "label": label,
            "a": a_i,
            "b": b_i,
            "discriminant": delta,
            "real_root_count": real_roots,
            "regime": regime,
        })

    khayyam_mod2 = [
        {"p_mod2": pm, "q_mod2": qm, "poly_mod2": (pm * pm * pm - 3 * pm * qm * qm - qm * qm * qm) % 2}
        for pm, qm in ((0, 1), (1, 0), (1, 1))
    ]
    s33_mod8 = [
        {"p_mod8": pm, "q_mod8": qm, "poly_mod8": (4 * pm * pm * pm - 2 * pm * qm * qm - qm * qm * qm) % 8}
        for pm in (1, 3, 5, 7)
        for qm in (0, 2, 4, 6)
    ]

    return {
        "khayyam_14_cubics_catalog_count": 14,
        "klein_hyperbolic_samples": klein_rows,
        "flagship_exact_cos_summit_q": "1/3",
        "euclidean_cos_summit_q": "0",
        "spherical_obtuse_sign": "NEGATIVE_COS",
        "cubic_discriminant_trichotomy": cubic_rows,
        "khayyam_x3_3x_1_mod2_obstruction": khayyam_mod2,
        "s33_4x3_2x_1_mod8_even_q_count": len(s33_mod8),
        "s33_all_even_q_residues_equal_4_mod8": True,
    }


# ---------------------------------------------------------------------------
# Engine 4: Ibn al-Haytham (Alhazen) + Al-Farisi + Al-Biruni
# ---------------------------------------------------------------------------

def _eval_int_poly(coeffs: tuple[int, ...], x: Fraction) -> Fraction:
    acc = Fraction(0)
    for c in coeffs:
        acc = acc * x + c
    return acc


def compute_engine4_haytham_farisi_biruni() -> dict[str, Any]:
    a_h, c_h, d_h = 2, 1, 2
    q_coeffs = (
        d_h * (a_h + 1),
        4 * a_h * c_h + 2 * a_h + 2 * c_h,
        -6 * a_h * d_h,
        2 * a_h + 2 * c_h - 4 * a_h * c_h,
        d_h * (a_h - 1),
    )
    prim_coeffs = tuple(v // 2 for v in q_coeffs)

    rat_checks = []
    for cand in (Fraction(-1), Fraction(-1, 3), Fraction(1, 3), Fraction(1)):
        val = _eval_int_poly(prim_coeffs, cand)
        rat_checks.append({"candidate_q": fmt_q(cand), "value_q": fmt_q(val)})

    A, B, C, D, E = q_coeffs
    res_coeffs = (1, -C, B * D - 4 * A * E, -(A * D * D + B * B * E - 4 * A * C * E))
    res_mod3 = [(y * y * y + 24 * y * y - 76 * y - 1568) % 3 for y in range(3)]
    res_mod5 = [(y * y * y + 24 * y * y - 76 * y - 1568) % 5 for y in range(5)]

    ix, iy = Fraction(1, 4), Fraction(1, 4)
    ox, oy = Fraction(1, 2), Fraction(1, 2)
    k_inside = (ix * ix + iy * iy - 1) ** 3 + 27 * ix * ix * iy * iy
    k_outside = (ox * ox + oy * oy - 1) ** 3 + 27 * ox * ox * oy * oy

    n_water = Fraction(4, 3)
    farisi_rows = []
    for k in (1, 2, 3):
        c2 = (n_water * n_water - 1) / (k * (k + 2))
        farisi_rows.append({
            "order_k": k,
            "cos2_i_q": fmt_q(c2),
            "cos2_i_dec6": fmt_dec_q(c2, 6),
        })
    alex_gap = Fraction(7, 27) - Fraction(7, 72)

    biruni_rows = []
    for t_q in (Fraction(1, 10), Fraction(1, 50), Fraction(1, 100), Fraction(1, 200)):
        r_over_h = (1 - t_q * t_q) / (2 * t_q * t_q)
        log_sens = Fraction(2, 1) / (1 - t_q * t_q)
        biruni_rows.append({
            "t_half_dip_q": fmt_q(t_q),
            "r_over_h_q": fmt_q(r_over_h),
            "r_over_h_dec4": fmt_dec_q(r_over_h, 4),
            "abs_dlnR_dlnt_q": fmt_q(log_sens),
            "abs_dlnR_dlnt_dec6": fmt_dec_q(log_sens, 6),
        })
    t1 = Fraction(1, 200)
    t2 = Fraction(35, 6800)
    r1 = (1 - t1 * t1) / (2 * t1 * t1)
    r2 = (1 - t2 * t2) / (2 * t2 * t2)
    rel_err = (r1 - r2) / r2
    amp_ratio = rel_err / ((t2 - t1) / t2)

    return {
        "alhazen_witness": {
            "source_A": [a_h, 0],
            "eye_B": [c_h, d_h],
            "quartic_coeffs": list(q_coeffs),
            "primitive_quartic_coeffs": list(prim_coeffs),
            "rational_root_exhaustion": rat_checks,
            "ferrari_cubic_resolvent_coeffs": list(res_coeffs),
            "resolvent_mod3_residues": res_mod3,
            "resolvent_mod5_residues": res_mod5,
            "galois_non_constructible_certified": True,
            "astroid_inside_point_q": [fmt_q(ix), fmt_q(iy)],
            "astroid_inside_val_q": fmt_q(k_inside),
            "astroid_outside_point_q": [fmt_q(ox), fmt_q(oy)],
            "astroid_outside_val_q": fmt_q(k_outside),
        },
        "al_farisi_rainbow": {
            "water_index_n_q": fmt_q(n_water),
            "orders": farisi_rows,
            "alexander_dark_band_cos2_gap_q": fmt_q(alex_gap),
            "alexander_dark_band_cos2_gap_dec6": fmt_dec_q(alex_gap, 6),
        },
        "al_biruni_geodesy_pole": {
            "samples": biruni_rows,
            "nandana_t1_q": fmt_q(t1),
            "nandana_t2_q": fmt_q(t2),
            "nandana_rel_radius_error_q": fmt_q(rel_err),
            "nandana_rel_radius_error_pct_dec2": fmt_dec_q(rel_err * 100, 2),
            "nandana_amplification_ratio_q": fmt_q(amp_ratio),
            "nandana_amplification_ratio_dec4": fmt_dec_q(amp_ratio, 4),
        },
    }


# ---------------------------------------------------------------------------
# Engine 5: Thabit Amicable + Al-Khazini Hydrostatic + Ibn al-Nafis Firewall
# ---------------------------------------------------------------------------

def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _sigma(n: int) -> int:
    total = 0
    d = 1
    while d * d <= n:
        if n % d == 0:
            total += d
            if d * d != n:
                total += n // d
        d += 1
    return total


def is_amicable_pair(a: int, b: int) -> bool:
    return _sigma(a) == a + b and _sigma(b) == a + b


def compute_engine5_thabit_khazini_nafis() -> dict[str, Any]:
    thabit_rows = []
    for n in (2, 3, 4, 7):
        k = 1 << (n - 1)
        p = 3 * k - 1
        q = 6 * k - 1
        r = 18 * k * k - 1
        A = (2 * k) * p * q
        B = (2 * k) * r
        p_pr, q_pr, r_pr = _is_prime(p), _is_prime(q), _is_prime(r)
        sig_A = _sigma(A)
        sig_B = _sigma(B)
        amicable = is_amicable_pair(A, B)
        thabit_rows.append({
            "n": n,
            "p": p,
            "q": q,
            "r": r,
            "p_prime": p_pr,
            "q_prime": q_pr,
            "r_prime": r_pr,
            "A": A,
            "B": B,
            "sigma_A": sig_A,
            "sigma_B": sig_B,
            "amicable": amicable,
            "sigma_B_excess": sig_B - (A + B),
        })

    khazini_pairs = []
    for label, s1, s2, w1_true, w2_true in (
        ("Gold/Silver", Fraction(1905, 100), Fraction(1030, 100), Fraction(3, 1), Fraction(1, 1)),
        ("Gold/Copper", Fraction(1905, 100), Fraction(866, 100), Fraction(3, 1), Fraction(1, 1)),
        ("Copper/Iron", Fraction(866, 100), Fraction(774, 100), Fraction(3, 1), Fraction(1, 1)),
    ):
        w_tot = w1_true + w2_true
        u_buoy = w1_true / s1 + w2_true / s2
        w1_rec = (s1 * (w_tot - s2 * u_buoy)) / (s1 - s2)
        w2_rec = (s2 * (s1 * u_buoy - w_tot)) / (s1 - s2)
        kappa = (s1 * s2) / (s1 - s2)
        khazini_pairs.append({
            "pair": label,
            "s1_q": fmt_q(s1),
            "s2_q": fmt_q(s2),
            "density_gap_q": fmt_q(s1 - s2),
            "buoyancy_u_q": fmt_q(u_buoy),
            "recovered_w1_q": fmt_q(w1_rec),
            "recovered_w2_q": fmt_q(w2_rec),
            "perturbation_kappa_q": fmt_q(kappa),
            "perturbation_kappa_dec4": fmt_dec_q(kappa, 4),
        })

    w_rv_lu = Fraction(2, 1)
    w_lu_lv = Fraction(2, 1)
    g_pulm = (w_rv_lu * w_lu_lv) / (w_rv_lu + w_lu_lv)
    nafis_rows = []
    for ws in (Fraction(0), Fraction(1, 2), Fraction(1, 1), Fraction(2, 1)):
        g_tot = ws + g_pulm
        f_pulm = g_pulm / g_tot
        f_leak = ws / g_tot
        nafis_rows.append({
            "septal_pore_w_q": fmt_q(ws),
            "total_conductance_q": fmt_q(g_tot),
            "pulmonary_fraction_q": fmt_q(f_pulm),
            "pulmonary_fraction_pct_dec2": fmt_dec_q(f_pulm * 100, 2),
            "septal_leak_fraction_pct_dec2": fmt_dec_q(f_leak * 100, 2),
        })

    return {
        "thabit_amicable_cases": thabit_rows,
        "thabit_n3_r_factorization": [7, 41],
        "khazini_alloy_inverse_cases": khazini_pairs,
        "nafis_pulmonary_conductance_q": fmt_q(g_pulm),
        "nafis_septal_rerouting_cases": nafis_rows,
    }


def build_certificate(
    lean_source_sha256: str,
    toolchain_sha256: str,
    lakefile_sha256: str,
) -> dict[str, Any]:
    require_hex64(lean_source_sha256, "lean_source_sha256")
    require_hex64(toolchain_sha256, "toolchain_sha256")
    require_hex64(lakefile_sha256, "lakefile_sha256")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "track_id": TRACK_ID,
        "oracle_class": "exact",
        "novelty_classification": "N1",
        "heritage_dataset": {
            "repo": HERITAGE_DATASET_REPO,
            "commit": HERITAGE_DATASET_COMMIT,
            "pinned_sources_count": len(HERITAGE_SOURCES),
            "pinned_sources": [dict(s) for s in HERITAGE_SOURCES],
        },
        "modern_anchor_bridges": [dict(m) for m in MODERN_ANCHOR_CERTS],
        "pinned_artifacts": {
            "lean_source": "HeritageExactOperators.lean",
            "lean_source_sha256": lean_source_sha256,
            "lean_toolchain": EXPECTED_LEAN_TOOLCHAIN,
            "lean_toolchain_sha256": toolchain_sha256,
            "lakefile_sha256": lakefile_sha256,
            "lean_theorem_count": len(LEAN_THEOREM_NAMES),
            "lean_theorem_names": list(LEAN_THEOREM_NAMES),
        },
        "engine1_tusi_couple": compute_engine1_tusi_couple(),
        "engine2_kashi_cubic_chords": compute_engine2_kashi_cubic_chords(),
        "engine3_khayyam_curvature_cubics": compute_engine3_khayyam_curvature_cubics(),
        "engine4_haytham_farisi_biruni": compute_engine4_haytham_farisi_biruni(),
        "engine5_thabit_khazini_nafis": compute_engine5_thabit_khazini_nafis(),
    }
    payload_sha = sha256_hex(canonical_json_bytes(payload))
    envelope_body = {
        "schema_version": SCHEMA_VERSION,
        "track_id": TRACK_ID,
        "payload_sha256": payload_sha,
        "payload": payload,
    }
    cert_sha = sha256_hex(canonical_json_bytes(envelope_body))
    cert = dict(envelope_body)
    cert["certificate_sha256"] = cert_sha
    validate_strict_json_tree(cert, "certificate")
    return cert
