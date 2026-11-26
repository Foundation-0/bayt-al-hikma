#!/usr/bin/env python3
"""Independent Pure-Z/Q Verifier for the 3 Unified Pilot-1 Seminar Syntheses.

Independently re-certifies all three emergent Round-3 Chair syntheses from the 7-seat Pilot-1
trans-historical Socratic seminar (63/63 refereed turns) purely in Z/Q (0 ast.Div, 0 ast.Pow,
0 floats, 0 math.log, 0 bare asserts, 0 energy/power claims):

  T1 (Foundation-0/continuum): Unified Fricke-Cayley Discriminant across definite Hurwitz/Lipschitz
     quaternion orders (kappa = 2D >= 0, odd Hurwitz D=1 halving, SO(3) parity transfer F~ = 8D mod 16,
     SO(3) kernel D in {0, 2ab}) and split CF transpose pairs (kappa = -[(p-s')^2+(q+r)^2](q-r)^2 <= 0,
     palindromic kernel, naive-SL2 overshoot 2(1-s)t^2).
  T2 (Foundation-0/aletheion): Joint CRT -> Coprime Single-Cycle Stride -> Exact-Q TV Bounded-Chatter
     Inclusive Hysteresis Valve -> Half-Split Tree Checksum Certificate.
  T3 (Foundation-0/cave-expedition): Unified Schur-Witt-Fold Theorem (exact Q & fraction-free Z
     congruences, GL(Z) iff A^{-1}B integral, 1x1 block drop iff s*D is nonzero rational square refuting
     unconditional drop at [[3,3],[3,4]], GF(2) fold iff det A odd, mirror billiard gcd(p,q) refuting
     single-shear at (2,3)).

Also cryptographically verifies all 6 sanitized pilot1_transcripts/*.json files (raw-byte SHA-256
on-disk binding, strict duplicate-key/CRLF/BOM/float refusal, canonical transcript_sha256, causal
DAG depth=3, dynamic repairs=20, bidirectional SEAT-0 pollination).
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import hmac
import json
from math import gcd, isqrt
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

SEMINAR_DIR = Path(__file__).resolve().parent
if str(SEMINAR_DIR) not in sys.path:
    sys.path.insert(0, str(SEMINAR_DIR))

import socratic_operator_seminar as sos  # noqa: E402

SCHEMA_PILOT1_CERT = "bayt-al-hikma.pilot1_theorems_synthesis.v1"
ENERGY_POWER_STATUS = "UNCONTROLLED_LAPTOP_NOT_CLAIMED"

MAX_INT_ABS = 1000000000000000000
MAX_CRT_LCM = 4096
MAX_MIRROR_DIM = 40
MATCHED_TURN_BUDGET = 21

# (key, sess_rel, turns_rel, exp_sess_sha, exp_turns_sha, exp_tx_sha, pass, cex, rep, xseat, h2m, m2h)
PILOT1_EXPECTED_SESSIONS: Tuple[Tuple[str, str, str, str, str, str, int, int, int, int, int, int], ...] = (
    (
        "topic1_continuum",
        "pilot1_transcripts/topic1_continuum_session.json",
        "pilot1_transcripts/topic1_continuum_turns.json",
        "de1963774eabc3d6c74f96c3eca679063c54684b52efe2935d60b68da9c4906d",
        "c275b696239aab2a44b921fe6b45d2ceb54355df8c8657ded7c097b1aefe1ebc",
        "33895402c91b5328404f46788d37e5fab2db4a251df7069f48cd071a5effcfd9",
        16,
        5,
        5,
        9,
        2,
        3,
    ),
    (
        "topic2_aletheion",
        "pilot1_transcripts/topic2_aletheion_session.json",
        "pilot1_transcripts/topic2_aletheion_turns.json",
        "07ef6a712a1c8acd5186f27cd2c8d8232cd9128d0cb703a93f58d4ee6d745ea8",
        "d43632160c567f926a4bd37dc5b11f17bc5b976fcc9a24445d4d938ef4fdee58",
        "a2ef42a15ac872fdc923dab3a8c96565d18767458661baffb2880c5769a6c13b",
        16,
        5,
        8,
        8,
        2,
        1,
    ),
    (
        "topic3_cave_expedition",
        "pilot1_transcripts/topic3_cave_expedition_session.json",
        "pilot1_transcripts/topic3_cave_expedition_turns.json",
        "ebe554553716ef8fe37f3325541386489f17977e49a3e98904b600c579355c72",
        "874f5df78ce271b5856e832f163c7534cc9e00d1d14b8d53199606c23e664eda",
        "afff3a9cb98987772e51f30d92036b09f70b128246c4771b9848aef792df7aca",
        19,
        2,
        7,
        13,
        1,
        7,
    ),
)

EXPECTED_CERT_KEYS = frozenset(
    {
        "schema",
        "energy_power_status",
        "zero_floats",
        "pure_q_ast_clean",
        "pilot1_transcripts",
        "t1_fricke_signature_unified",
        "t2_crt_valve_seal",
        "t3_unified_schur_witt_fold",
        "all_passed",
        "payload_sha256",
        "certificate_sha256",
    }
)


class Pilot1Error(ValueError):
    """Fail-closed domain or verification error with deterministic code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def require_ok(cond: bool, code: str, message: str) -> None:
    if cond is not True:
        raise Pilot1Error(code, message)


def _canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    try:
        return sos.canonical_json_bytes(obj)
    except sos.SeminarError as exc:
        raise Pilot1Error(exc.code, exc.message) from exc


def check_int(val: Any, name: str) -> int:
    require_ok(type(val) is int and abs(val) <= MAX_INT_ABS, "BAD_INT", f"{name} must be bounded exact int")
    return val


def check_pos_int(val: Any, name: str) -> int:
    v = check_int(val, name)
    require_ok(v > 0, "BAD_POS_INT", f"{name} must be > 0")
    return v


def frac_str(f: Fraction) -> str:
    return f"{f.numerator}{chr(47)}{f.denominator}"


def qdiv(num: Fraction, den: Fraction) -> Fraction:
    require_ok(den != Fraction(0, 1), "QDIV_ZERO_DENOM", "Zero denominator in exact rational division")
    return Fraction(num.numerator * den.denominator, num.denominator * den.numerator)


def _egcd(a: int, b: int) -> Tuple[int, int, int]:
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        q = divmod(old_r, r)[0]
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return (old_r, old_s, old_t)


# ---------------------------------------------------------------------------
# T1: Unified Fricke-Discriminant Theorem (Definite Hurwitz & Split CF)
# ---------------------------------------------------------------------------


def fricke_discriminant(a: Fraction, b: Fraction, x: Fraction, y: Fraction, z: Fraction) -> Fraction:
    return 4 * a * b - b * x * x - a * y * y - z * z + x * y * z


def _qmul(p: Tuple[Fraction, Fraction, Fraction, Fraction], q: Tuple[Fraction, Fraction, Fraction, Fraction]) -> Tuple[Fraction, Fraction, Fraction, Fraction]:
    p0, p1, p2, p3 = p
    q0, q1, q2, q3 = q
    return (
        p0 * q0 - p1 * q1 - p2 * q2 - p3 * q3,
        p0 * q1 + p1 * q0 + p2 * q3 - p3 * q2,
        p0 * q2 - p1 * q3 + p2 * q0 + p3 * q1,
        p0 * q3 + p1 * q2 - p2 * q1 + p3 * q0,
    )


def _qconj(p: Tuple[Fraction, Fraction, Fraction, Fraction]) -> Tuple[Fraction, Fraction, Fraction, Fraction]:
    return (p[0], -p[1], -p[2], -p[3])


def _qnrd(p: Tuple[Fraction, Fraction, Fraction, Fraction]) -> Fraction:
    return p[0] * p[0] + p[1] * p[1] + p[2] * p[2] + p[3] * p[3]


def _so3_matrix(p: Tuple[Fraction, Fraction, Fraction, Fraction]) -> List[List[Fraction]]:
    n = _qnrd(p)
    w, x, y, z = p
    return [
        [qdiv(w * w + x * x - y * y - z * z, n), qdiv(2 * (x * y - w * z), n), qdiv(2 * (x * z + w * y), n)],
        [qdiv(2 * (x * y + w * z), n), qdiv(w * w - x * x + y * y - z * z, n), qdiv(2 * (y * z - w * x), n)],
        [qdiv(2 * (x * z - w * y), n), qdiv(2 * (y * z + w * x), n), qdiv(w * w - x * x - y * y + z * z, n)],
    ]


def _matmul(a: Sequence[Sequence[Fraction]], b: Sequence[Sequence[Fraction]]) -> List[List[Fraction]]:
    m, k, n = len(a), len(b), len(b[0])
    return [[sum((a[i][t] * b[t][j] for t in range(k)), Fraction(0, 1)) for j in range(n)] for i in range(m)]


def verify_fricke_definite(a_dbl: Sequence[int], b_dbl: Sequence[int]) -> Dict[str, Any]:
    """Certify definite Hurwitz/Lipschitz Fricke discriminant & SO(3) parity-transfer law."""
    require_ok(isinstance(a_dbl, (list, tuple)) and len(a_dbl) == 4, "BAD_QUAT", "A must have 4 doubled coords")
    require_ok(isinstance(b_dbl, (list, tuple)) and len(b_dbl) == 4, "BAD_QUAT", "B must have 4 doubled coords")
    A = tuple(check_int(v, f"A[{i}]") for i, v in enumerate(a_dbl))
    B = tuple(check_int(v, f"B[{i}]") for i, v in enumerate(b_dbl))
    pa = divmod(A[0], 2)[1]
    pb = divmod(B[0], 2)[1]
    require_ok(all(divmod(v, 2)[1] == pa for v in A) and all(divmod(v, 2)[1] == pb for v in B), "BAD_HURWITZ_PARITY", "uniform parity required")
    g = tuple(Fraction(v, 2) for v in A)
    h = tuple(Fraction(v, 2) for v in B)
    a_norm = _qnrd(g)
    b_norm = _qnrd(h)
    require_ok(a_norm > 0 and b_norm > 0, "ZERO_QUAT", "non-zero quaternions required")
    a_int = int(a_norm)
    b_int = int(b_norm)
    ab = a_int * b_int
    x = Fraction(A[0], 1)
    y = Fraction(B[0], 1)
    gh = _qmul(g, h)
    hg = _qmul(h, g)
    z = 2 * gh[0]
    kappa = fricke_discriminant(a_norm, b_norm, x, y, z)
    diff_comm = tuple(gh[i] - hg[i] for i in range(4))
    nrd_diff = _qnrd(diff_comm)

    cx = A[2] * B[3] - A[3] * B[2]
    cy = A[3] * B[1] - A[1] * B[3]
    cz = A[1] * B[2] - A[2] * B[1]
    cross_sq = cx * cx + cy * cy + cz * cz
    d_val = divmod(cross_sq, 8)[0]
    c_quat = _qmul(_qmul(g, h), _qmul(_qconj(g), _qconj(h)))
    re_c = c_quat[0]
    trd_group_comm = qdiv(2 * re_c, a_norm * b_norm)

    rp = _so3_matrix(g)
    rq = _so3_matrix(h)
    comm_so3 = _matmul(rp, rq)
    comm_qp = _matmul(rq, rp)
    frob_sq = sum(
        ((comm_so3[i][j] - comm_qp[i][j]) * (comm_so3[i][j] - comm_qp[i][j]) for i in range(3) for j in range(3)),
        Fraction(0, 1),
    )
    delta = Fraction(d_val, ab)
    frob_formula = 16 * delta * (1 - qdiv(delta, Fraction(2, 1)))
    f_cleared = 8 * d_val * (2 * ab - d_val)
    parity_transfer_ok = divmod(f_cleared, 16)[1] == divmod(8 * d_val, 16)[1]

    identities_ok = all(
        (
            divmod(cross_sq, 8)[1] == 0,
            kappa == nrd_diff,
            kappa == Fraction(2 * d_val, 1),
            re_c == Fraction(ab - d_val, 1),
            _qnrd(c_quat) == Fraction(ab * ab, 1),
            trd_group_comm == 2 - qdiv(kappa, Fraction(ab, 1)),
            frob_sq == frob_formula,
            frob_sq * ab * ab == Fraction(f_cleared, 1),
            parity_transfer_ok,
        )
    )
    return {
        "norm_product": ab,
        "D": d_val,
        "D_parity": divmod(d_val, 2)[1],
        "kappa": int(kappa),
        "reC": int(re_c),
        "F_cleared": f_cleared,
        "so3_invisible_kernel": f_cleared == 0,
        "identities_exact": identities_ok,
    }


def verify_fricke_split(num: int, den: int) -> Dict[str, Any]:
    """Certify split CF transpose-pair Fricke discriminant & exact naive-SL2 overshoot."""
    p_in = check_pos_int(num, "num")
    q_in = check_pos_int(den, "den")
    require_ok(gcd(p_in, q_in) == 1, "NOT_COPRIME", "num/den must be reduced")
    cf: List[int] = []
    a_cur, b_cur = p_in, q_in
    while b_cur != 0:
        q_step, r_step = divmod(a_cur, b_cur)
        cf.append(q_step)
        a_cur, b_cur = b_cur, r_step

    w = [[Fraction(1, 1), Fraction(0, 1)], [Fraction(0, 1), Fraction(1, 1)]]
    for term in cf:
        w = _matmul(w, [[Fraction(term, 1), Fraction(1, 1)], [Fraction(1, 1), Fraction(0, 1)]])
    v = [[w[0][0], w[1][0]], [w[0][1], w[1][1]]]
    s = int(w[0][0] * w[1][1] - w[0][1] * w[1][0])
    s_f = Fraction(s, 1)
    t = int(w[0][0] + w[1][1])
    wv = _matmul(w, v)
    vw = _matmul(v, w)
    z = int(wv[0][0] + wv[1][1])
    comm_diff = [[wv[i][j] - vw[i][j] for j in range(2)] for i in range(2)]
    kappa = int(comm_diff[0][0] * comm_diff[1][1] - comm_diff[0][1] * comm_diff[1][0])
    p0, q0, r0, s0 = int(w[0][0]), int(w[0][1]), int(w[1][0]), int(w[1][1])
    dp = p0 - s0
    s_qr = q0 + r0
    d_qr = q0 - r0
    kappa_factor = -((dp * dp + s_qr * s_qr) * (d_qr * d_qr))
    fricke_val = int(fricke_discriminant(s_f, s_f, Fraction(t, 1), Fraction(t, 1), Fraction(z, 1)))

    w_inv = [[qdiv(w[1][1], s_f), qdiv(-w[0][1], s_f)], [qdiv(-w[1][0], s_f), qdiv(w[0][0], s_f)]]
    v_inv = [[qdiv(v[1][1], s_f), qdiv(-v[0][1], s_f)], [qdiv(-v[1][0], s_f), qdiv(v[0][0], s_f)]]
    c_mat = _matmul(_matmul(w, v), _matmul(w_inv, v_inv))
    det_c = int(c_mat[0][0] * c_mat[1][1] - c_mat[0][1] * c_mat[1][0])
    tr_c = int(c_mat[0][0] + c_mat[1][1])
    naive_sl2 = 2 * t * t + z * z - t * t * z - 2
    overshoot = naive_sl2 - tr_c
    palindromic = cf == list(reversed(cf))
    exp_s = 1 if divmod(len(cf), 2)[1] == 0 else -1

    identities_ok = all(
        (
            s == exp_s,
            comm_diff[0][1] == comm_diff[1][0],
            comm_diff[0][0] + comm_diff[1][1] == 0,
            kappa == kappa_factor,
            kappa == fricke_val,
            kappa <= 0,
            det_c == 1,
            tr_c == 2 - kappa,
            overshoot == 2 * (1 - s) * t * t,
            (kappa == 0) == palindromic,
        )
    )
    return {
        "fraction": f"{p_in}{chr(47)}{q_in}",
        "cf": cf,
        "sector": s,
        "t": t,
        "z": z,
        "kappa": kappa,
        "trace": tr_c,
        "naive_sl2": naive_sl2,
        "overshoot": overshoot,
        "palindromic": palindromic,
        "identities_exact": identities_ok,
    }


def certify_t1_fricke_signature_unified() -> Dict[str, Any]:
    w_hurwitz = verify_fricke_definite((5, 3, 1, 1), (13, 5, 1, 1))
    w_lipschitz = verify_fricke_definite((4, 4, 2, 0), (12, 6, 4, 0))
    w_spin_kernel = verify_fricke_definite((0, 2, 0, 0), (0, 0, 2, 0))
    w_5_3 = verify_fricke_split(5, 3)
    w_355_113 = verify_fricke_split(355, 113)
    w_8_3 = verify_fricke_split(8, 3)
    w_13_8 = verify_fricke_split(13, 8)

    passed = all(
        (
            w_hurwitz["identities_exact"],
            w_hurwitz["D"] == 1,
            w_hurwitz["F_cleared"] == 7048,
            w_lipschitz["identities_exact"],
            w_lipschitz["D"] == 2,
            w_lipschitz["F_cleared"] == 14080,
            w_spin_kernel["identities_exact"],
            w_spin_kernel["so3_invisible_kernel"],
            w_spin_kernel["reC"] == -1,
            w_5_3["identities_exact"],
            w_5_3["kappa"] == -41,
            w_5_3["trace"] == 43,
            w_5_3["naive_sl2"] == 187,
            w_355_113["identities_exact"],
            w_355_113["naive_sl2"] == 1154307627,
            w_355_113["trace"] != 1154307627,
            w_8_3["identities_exact"],
            w_8_3["palindromic"],
            w_8_3["kappa"] == 0,
            w_13_8["identities_exact"],
            not w_13_8["palindromic"],
            w_13_8["kappa"] < 0,
        )
    )
    return {
        "gate": "T1_PILOT1_FRICKE_SIGNATURE_UNIFIED",
        "definite_hurwitz_odd_d1": w_hurwitz,
        "definite_lipschitz_d2": w_lipschitz,
        "definite_so3_kernel_ij": w_spin_kernel,
        "split_5_3": w_5_3,
        "split_355_113": w_355_113,
        "split_8_3_palindromic": w_8_3,
        "split_13_8_nonpalindromic": w_13_8,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# T2: Joint CRT -> Coprime Stride -> Exact-Q TV Valve -> Tree Checksum
# ---------------------------------------------------------------------------


def _tree_checksum(leaves: Sequence[int]) -> int:
    if len(leaves) == 1:
        return leaves[0]
    mid = divmod(len(leaves), 2)[0]
    return _tree_checksum(leaves[:mid]) + 3 * _tree_checksum(leaves[mid:])


def verify_crt_valve_seal(
    moduli: Sequence[int],
    residues: Sequence[int],
    stride: int,
    levels: Sequence[Tuple[int, int]],
    lo: Tuple[int, int],
    hi: Tuple[int, int],
    init: int,
) -> Dict[str, Any]:
    """Certify T2 CRT triple-agreement, single-cycle stride, TV hysteresis bounds, and tree root."""
    require_ok(isinstance(moduli, (list, tuple)) and len(moduli) >= 1, "BAD_CRT", "moduli must be non-empty")
    require_ok(isinstance(residues, (list, tuple)) and len(residues) == len(moduli), "BAD_CRT", "residues len mismatch")
    ms = [check_pos_int(m, f"m[{i}]") for i, m in enumerate(moduli)]
    rs = [check_int(r, f"r[{i}]") for i, r in enumerate(residues)]
    s_val = check_int(stride, "stride")
    require_ok(type(init) is int and init in (0, 1), "BAD_INIT", "init must be 0 or 1")
    lo_f = Fraction(check_int(lo[0], "lo_num"), check_pos_int(lo[1], "lo_den"))
    hi_f = Fraction(check_int(hi[0], "hi_num"), check_pos_int(hi[1], "hi_den"))
    require_ok(lo_f < hi_f, "BAD_BAND", "must satisfy lo < hi")

    lcm_m = 1
    prod_m = 1
    for m in ms:
        lcm_m = divmod(lcm_m, gcd(lcm_m, m))[0] * m
        prod_m *= m
    require_ok(lcm_m <= MAX_CRT_LCM, "LCM_TOO_LARGE", "lcm exceeds MAX_CRT_LCM")

    exhaustive = [x for x in range(lcm_m) if all(divmod(x - r, m)[1] == 0 for r, m in zip(rs, ms))]
    pairwise_ok = all(divmod(rs[i] - rs[j], gcd(ms[i], ms[j]))[1] == 0 for i in range(len(ms)) for j in range(i + 1, len(ms)))
    pairwise_coprime = all(gcd(ms[i], ms[j]) == 1 for i in range(len(ms)) for j in range(i + 1, len(ms)))

    fold_r, fold_m = divmod(rs[0], ms[0])[1], ms[0]
    fold_ok = True
    for a_i, m_i in zip(rs[1:], ms[1:]):
        g, u, _ = _egcd(fold_m, m_i)
        if divmod(a_i - fold_r, g)[1] != 0:
            fold_ok = False
            break
        m_red = divmod(m_i, g)[0]
        k = divmod(divmod(a_i - fold_r, g)[0] * u, m_red)[1]
        new_m = fold_m * m_red
        fold_r = divmod(fold_r + fold_m * k, new_m)[1]
        fold_m = new_m

    deciders_agree = all(
        (
            len(exhaustive) <= 1,
            (len(exhaustive) == 1) == pairwise_ok,
            fold_ok == pairwise_ok,
            (prod_m == lcm_m) == pairwise_coprime,
        )
    )
    if not pairwise_ok:
        return {
            "solvable": False,
            "deciders_agree": deciders_agree,
            "lcm": lcm_m,
            "single_cycle_moduli": pairwise_coprime,
        }

    x0 = exhaustive[0]
    require_ok(fold_r == x0 and fold_m == lcm_m, "CRT_FOLD_MISMATCH", "CRT fold mismatch")
    stride_coprime = gcd(divmod(s_val, lcm_m)[1], lcm_m) == 1
    if not stride_coprime:
        return {
            "solvable": True,
            "deciders_agree": deciders_agree,
            "timestamp": x0,
            "lcm": lcm_m,
            "stride_single_cycle": False,
        }

    require_ok(isinstance(levels, (list, tuple)) and len(levels) == lcm_m, "BAD_LEVELS", "levels length must equal lcm")
    lev_f = [Fraction(check_int(lv[0], "lv_num"), check_pos_int(lv[1], "lv_den")) for lv in levels]
    orbit = [divmod(x0 + k * s_val, lcm_m)[1] for k in range(lcm_m)]
    orbit_is_cycle = len(set(orbit)) == lcm_m
    stream = [lev_f[p] for p in orbit]

    states: List[int] = []
    cur = init
    flips = 0
    h_hits = 0
    l_hits = 0
    for v in stream:
        if v >= hi_f:
            h_hits += 1
            nxt = 1
        elif v <= lo_f:
            l_hits += 1
            nxt = 0
        else:
            nxt = cur
        if nxt != cur:
            flips += 1
        states.append(nxt)
        cur = nxt

    intervals: List[List[int]] = []
    idx = 0
    while idx < lcm_m:
        start = idx
        lbl = states[idx]
        while idx < lcm_m and states[idx] == lbl:
            idx += 1
        intervals.append([start, idx - start, lbl])

    tv = sum((abs(stream[k + 1] - stream[k]) for k in range(lcm_m - 1)), Fraction(0, 1))
    leaves = [2 * seg[1] + seg[2] for seg in intervals]
    root = _tree_checksum(leaves)
    on_count = sum(seg[1] for seg in intervals if seg[2] == 1)

    bounds_ok = all(
        (
            orbit_is_cycle,
            flips == len(intervals) - 1 + (1 if states[0] != init else 0),
            flips <= h_hits + l_hits,
            flips <= 2 * min(h_hits, l_hits) + 1,
            (flips - 1) * (hi_f - lo_f) <= tv,
            sum(seg[1] for seg in intervals) == lcm_m,
        )
    )
    return {
        "solvable": True,
        "deciders_agree": deciders_agree,
        "timestamp": x0,
        "lcm": lcm_m,
        "single_cycle_moduli": pairwise_coprime,
        "stride_single_cycle": True,
        "intervals": intervals,
        "flips": flips,
        "on_count": on_count,
        "tv": frac_str(tv),
        "root": root,
        "chatter_bounds_exact": bounds_ok,
    }


def certify_t2_crt_valve_seal() -> Dict[str, Any]:
    c0 = verify_crt_valve_seal([3], [0], 2, [(3, 1), (1, 1), (-1, 1)], (0, 1), (2, 1), 0)
    c2 = verify_crt_valve_seal([2, 4], [1, 3], 3, [(0, 1), (5, 1), (2, 1), (4, 1)], (1, 1), (3, 1), 0)
    c4_inconsistent = verify_crt_valve_seal([6, 10], [3, 8], 7, [], (0, 1), (1, 1), 0)
    c6_bad_stride = verify_crt_valve_seal([2, 4], [1, 3], 2, [(0, 1), (5, 1), (2, 1), (4, 1)], (1, 1), (3, 1), 0)
    c7_tight = verify_crt_valve_seal([2, 3], [1, 2], 5, [(2, 1), (1, 3), (1, 1), (2, 1), (0, 1), (1, 1)], (1, 2), (3, 2), 1)

    passed = all(
        (
            c0["deciders_agree"],
            c0["chatter_bounds_exact"],
            c0["root"] == 15,
            c0["tv"] == "6/1",
            c2["deciders_agree"],
            c2["chatter_bounds_exact"],
            not c2["single_cycle_moduli"],
            c2["timestamp"] == 3,
            c2["root"] == 13,
            c4_inconsistent["deciders_agree"],
            not c4_inconsistent["solvable"],
            c6_bad_stride["deciders_agree"],
            not c6_bad_stride["stride_single_cycle"],
            c7_tight["deciders_agree"],
            c7_tight["chatter_bounds_exact"],
            c7_tight["flips"] == 4,
            c7_tight["root"] == 123,
            c7_tight["tv"] == "19/3",
        )
    )
    return {
        "gate": "T2_PILOT1_CRT_STRIDE_VALVE_CHECKSUM",
        "r2_seat6_repaired_witness": c0,
        "noncoprime_crt_witness": c2,
        "r1_inconsistent_refutation": c4_inconsistent,
        "noncoprime_stride_refutation": c6_bad_stride,
        "tight_rational_band_witness": c7_tight,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# T3: Unified Schur-Witt-Fold Theorem (Q/Z Congruence, Block Drop, GF(2), Mirror)
# ---------------------------------------------------------------------------


def _mat_transpose(a: Sequence[Sequence[Fraction]]) -> List[List[Fraction]]:
    return [[a[i][j] for i in range(len(a))] for j in range(len(a[0]))]


def _mat_det_and_inv(a: Sequence[Sequence[Fraction]]) -> Tuple[Fraction, Optional[List[List[Fraction]]]]:
    n = len(a)
    w = [list(a[i]) + [Fraction(1 if i == j else 0, 1) for j in range(n)] for i in range(n)]
    det = Fraction(1, 1)
    for c in range(n):
        piv = -1
        for r in range(c, n):
            if w[r][c] != 0:
                piv = r
                break
        if piv == -1:
            return (Fraction(0, 1), None)
        if piv != c:
            w[c], w[piv] = w[piv], w[c]
            det = -det
        pv = w[c][c]
        det *= pv
        w[c] = [qdiv(v, pv) for v in w[c]]
        for r in range(n):
            if r != c and w[r][c] != 0:
                f = w[r][c]
                w[r] = [w[r][j] - f * w[c][j] for j in range(2 * n)]
    return (det, [row[n:] for row in w])


def _is_rational_square(q: Fraction) -> bool:
    if q < 0:
        return False
    rn = isqrt(q.numerator)
    rd = isqrt(q.denominator)
    return (rn * rn == q.numerator) and (rd * rd == q.denominator)


def verify_schur_block_system(
    a_int: Sequence[Sequence[int]],
    b_int: Sequence[Sequence[int]],
    d_int: Sequence[Sequence[int]],
) -> Dict[str, Any]:
    """Certify Q-congruence, fraction-free Z lift, GL(Z) shear, 1x1 block-drop, and GF(2) fold."""
    require_ok(isinstance(a_int, (list, tuple)) and len(a_int) >= 1, "BAD_BLOCK", "A must be non-empty")
    require_ok(isinstance(d_int, (list, tuple)) and len(d_int) >= 1, "BAD_BLOCK", "D must be non-empty")
    k, m = len(a_int), len(d_int)
    require_ok(isinstance(b_int, (list, tuple)) and len(b_int) == k, "BAD_BLOCK", "B rows must equal dim(A)")
    A = [[Fraction(check_int(a_int[i][j], "A"), 1) for j in range(k)] for i in range(k)]
    B = [[Fraction(check_int(b_int[i][j], "B"), 1) for j in range(m)] for i in range(k)]
    D = [[Fraction(check_int(d_int[i][j], "D"), 1) for j in range(m)] for i in range(m)]
    BT = _mat_transpose(B)
    M = [A[i] + B[i] for i in range(k)] + [BT[i] + D[i] for i in range(m)]
    det_a, a_inv = _mat_det_and_inv(A)
    require_ok(a_inv is not None, "SINGULAR_PIVOT", "det(A) must be non-zero")

    X = _matmul(a_inv, B)
    S = [[D[i][j] - _matmul(BT, X)[i][j] for j in range(m)] for i in range(m)]
    det_s, _ = _mat_det_and_inv(S)
    det_m, _ = _mat_det_and_inv(M)

    P = [
        [Fraction(1 if i == j else 0, 1) for j in range(k)] + [-X[i][j] for j in range(m)]
        for i in range(k)
    ] + [
        [Fraction(0, 1) for _ in range(k)] + [Fraction(1 if i == j else 0, 1) for j in range(m)]
        for i in range(m)
    ]
    ptmp = _matmul(_matmul(_mat_transpose(P), M), P)
    block_diag_as = [A[i] + [Fraction(0, 1)] * m for i in range(k)] + [[Fraction(0, 1)] * k + S[i] for i in range(m)]

    P_int = [[det_a * P[i][j] for j in range(k + m)] for i in range(k + m)]
    pint_m_pint = _matmul(_matmul(_mat_transpose(P_int), M), P_int)
    scaled_diag = [[det_a * det_a * block_diag_as[i][j] for j in range(k + m)] for i in range(k + m)]
    p_int_all_z = all(v.denominator == 1 for row in P_int for v in row)

    x_integral = all(v.denominator == 1 for row in X for v in row)
    s_integral = all(v.denominator == 1 for row in S for v in row)
    gf2_defined = divmod(int(det_a), 2)[1] != 0
    gf2_even_diag_ok = True
    if gf2_defined:
        even_m = all(divmod(int(M[i][i]), 2)[1] == 0 for i in range(k + m))
        if even_m:
            gf2_even_diag_ok = all(all((divmod(S[i][i].denominator, 2)[1] == 1, divmod(S[i][i].numerator, 2)[1] == 0)) for i in range(m))

    block_drop_q = False
    if m == 1:
        s_val = S[0][0]
        d_val = D[0][0]
        block_drop_q = (s_val == 0 and d_val == 0) or (s_val * d_val != 0 and _is_rational_square(s_val * d_val))

    return {
        "det_a": int(det_a),
        "det_m": frac_str(det_m),
        "q_congruence_exact": all((ptmp == block_diag_as, det_m == det_a * det_s)),
        "z_lift_exact": all((p_int_all_z, pint_m_pint == scaled_diag)),
        "gl_z_canonical_shear": x_integral,
        "s_integral": s_integral,
        "block_drop_1x1_q_congruent": block_drop_q,
        "gf2_fold_defined": gf2_defined,
        "gf2_even_diag_preserved": gf2_even_diag_ok,
        "S": [[frac_str(v) for v in row] for row in S],
    }


def verify_mirror_billiard(p: int, q: int) -> Dict[str, Any]:
    """Exact doubled-coordinate mirror-curve billiard cycle count == gcd(p, q) + Euclid U."""
    pp = check_pos_int(p, "p")
    qq = check_pos_int(q, "q")
    require_ok(pp <= MAX_MIRROR_DIM and qq <= MAX_MIRROR_DIM, "MIRROR_TOO_LARGE", "p, q must be <= 40")
    W, H = 2 * pp, 2 * qq
    states: List[Tuple[int, int, int, int]] = []
    for x in range(W + 1):
        for y in range(H + 1):
            if divmod(x + y, 2)[1] == 1:
                for dx in (1, -1):
                    for dy in (1, -1):
                        if 0 <= x + dx <= W and 0 <= y + dy <= H:
                            states.append((x, y, dx, dy))
    seen = set()
    directed_cycles = 0
    for st in states:
        if st in seen:
            continue
        cur = st
        while cur not in seen:
            seen.add(cur)
            x, y, dx, dy = cur
            nx, ny = x + dx, y + dy
            ndx = -dx if (nx == 0 or nx == W) else dx
            ndy = -dy if (ny == 0 or ny == H) else dy
            cur = (nx, ny, ndx, ndy)
        directed_cycles += 1
    curves = divmod(directed_cycles, 2)[0]
    g = gcd(pp, qq)
    u = [[1, 0], [0, 1]]
    a_e, b_e = pp, qq
    while b_e != 0:
        t_q = divmod(a_e, b_e)[0]
        u = [[u[1][0], u[1][1]], [u[0][0] - t_q * u[1][0], u[0][1] - t_q * u[1][1]]]
        a_e, b_e = b_e, a_e - t_q * b_e
    euclid_ok = all(
        (
            a_e == g,
            u[0][0] * pp + u[0][1] * qq == g,
            u[1][0] * pp + u[1][1] * qq == 0,
            u[0][0] * u[1][1] - u[0][1] * u[1][0] in (1, -1),
        )
    )
    return {
        "p": pp,
        "q": qq,
        "gcd": g,
        "curves": curves,
        "curves_equal_gcd": all((divmod(directed_cycles, 2)[1] == 0, curves == g)),
        "euclid_u": u,
        "euclid_unimodular_ok": euclid_ok,
        "single_shear_false_at_coprime": (curves == 1) and (divmod(qq, pp)[1] != 0),
    }


def certify_t3_unified_schur_witt_fold() -> Dict[str, Any]:
    c0_q = verify_schur_block_system([[2]], [[1]], [[1]])
    c1_glz = verify_schur_block_system([[2, 0], [0, 3]], [[4], [6]], [[5]])
    c2_converse_fail = verify_schur_block_system([[4]], [[2]], [[1]])
    c3_block_drop_refute = verify_schur_block_system([[3]], [[3]], [[4]])
    q_wit = [[Fraction(1, 1), Fraction(-2, 1)], [Fraction(0, 1), Fraction(2, 1)]]
    m_3334 = [[Fraction(3, 1), Fraction(3, 1)], [Fraction(3, 1), Fraction(4, 1)]]
    q_diag_ok = _matmul(_matmul(_mat_transpose(q_wit), m_3334), q_wit) == [[Fraction(3, 1), Fraction(0, 1)], [Fraction(0, 1), Fraction(4, 1)]]
    c5_gf2_a3 = verify_schur_block_system([[2, 1], [1, 2]], [[1], [0]], [[2]])
    c7_mirror_23 = verify_mirror_billiard(2, 3)

    passed = all(
        (
            c0_q["q_congruence_exact"],
            c0_q["z_lift_exact"],
            not c0_q["block_drop_1x1_q_congruent"],
            not c0_q["gf2_fold_defined"],
            c1_glz["gl_z_canonical_shear"],
            c1_glz["S"] == [["-15/1"]],
            c2_converse_fail["s_integral"],
            not c2_converse_fail["gl_z_canonical_shear"],
            c3_block_drop_refute["block_drop_1x1_q_congruent"],
            q_diag_ok,
            c5_gf2_a3["gf2_fold_defined"],
            c5_gf2_a3["gf2_even_diag_preserved"],
            c5_gf2_a3["S"] == [["4/3"]],
            c7_mirror_23["curves_equal_gcd"],
            c7_mirror_23["euclid_unimodular_ok"],
            c7_mirror_23["single_shear_false_at_coprime"],
        )
    )
    return {
        "gate": "T3_PILOT1_UNIFIED_SCHUR_WITT_FOLD",
        "schur_q_and_block_obstruction_2111": c0_q,
        "gl_z_canonical_shear_witness": c1_glz,
        "s_integral_converse_counterexample": c2_converse_fail,
        "block_drop_refutation_3334": c3_block_drop_refute,
        "explicit_q_witness_3334_verified": q_diag_ok,
        "gf2_fold_a3_witness": c5_gf2_a3,
        "mirror_billiard_2_3_refutation": c7_mirror_23,
        "passed": passed,
    }


# ---------------------------------------------------------------------------
# Pilot-1 Sanitized Transcript Integrity (Raw-Byte SHA-256 + Strict JSON)
# ---------------------------------------------------------------------------


def verify_pilot1_transcripts(seminar_dir: Path) -> Dict[str, Any]:
    """Cryptographically verify all 6 sanitized pilot1_transcripts/*.json files."""
    topics: List[Dict[str, Any]] = []
    tot_turns = 0
    tot_pass = 0
    tot_cex = 0
    tot_repairs = 0
    tot_cross = 0
    tot_h2m = 0
    tot_m2h = 0

    for (
        key,
        sess_rel,
        turns_rel,
        exp_ssha,
        exp_tsha_file,
        exp_tx_sha,
        exp_pass,
        exp_cex,
        exp_rep,
        exp_cross,
        exp_h2m,
        exp_m2h,
    ) in PILOT1_EXPECTED_SESSIONS:
        sp = seminar_dir.joinpath(sess_rel)
        tp = seminar_dir.joinpath(turns_rel)
        try:
            s_raw = sos.read_regular_file_bytes(sp, missing_code="PILOT1_MISSING")
            t_raw = sos.read_regular_file_bytes(tp, missing_code="PILOT1_MISSING")
        except sos.SeminarError as exc:
            raise Pilot1Error(exc.code, exc.message) from exc
        s_fsha = hashlib.sha256(s_raw).hexdigest()
        t_fsha = hashlib.sha256(t_raw).hexdigest()
        require_ok(hmac.compare_digest(s_fsha, exp_ssha), "INPUT_SHA_MISMATCH", f"session raw SHA mismatch on {key}")
        require_ok(hmac.compare_digest(t_fsha, exp_tsha_file), "INPUT_SHA_MISMATCH", f"turns raw SHA mismatch on {key}")

        try:
            s_obj = sos.loads_strict_json_bytes(s_raw, sess_rel)
            t_obj = sos.loads_strict_json_bytes(t_raw, turns_rel)
            sos.assert_clean_public_text(s_raw.decode("utf-8"), check_model_pollution=True)
            sos.assert_clean_public_text(t_raw.decode("utf-8"), check_model_pollution=True)
        except sos.SeminarError as exc:
            raise Pilot1Error(exc.code, exc.message) from exc

        body_no_sha = {k: v for k, v in s_obj.items() if k != "transcript_sha256"}
        recomp_sha = hashlib.sha256(_canonical_json_bytes(body_no_sha)).hexdigest()
        require_ok(
            hmac.compare_digest(str(s_obj.get("transcript_sha256", "")), recomp_sha)
            and hmac.compare_digest(recomp_sha, exp_tx_sha),
            "TRANSCRIPT_SHA_MISMATCH",
            f"transcript_sha256 mismatch on {key}",
        )
        require_ok(
            all(
                (
                    s_obj["turn_count"] == MATCHED_TURN_BUDGET,
                    isinstance(t_obj, list) and len(t_obj) == MATCHED_TURN_BUDGET,
                    s_obj["pass_witness_count"] == exp_pass,
                    s_obj["minimal_counterexample_count"] == exp_cex,
                    s_obj["max_dag_depth"] == 3,
                    len(s_obj["dag_edges"]) == 14,
                    len(s_obj["counterexample_repairs"]) == exp_rep,
                    len(s_obj["cross_seat_compositions"]) == exp_cross,
                    len(s_obj["historical_to_modern_edges"]) == exp_h2m,
                    len(s_obj["modern_to_historical_edges"]) == exp_m2h,
                    s_obj["s150_g2_dynamic_compounding_passed"] is True,
                    s_obj["s150_g5_bidirectional_pollination_passed"] is True,
                )
            ),
            "PILOT1_METRIC_MISMATCH",
            f"metric mismatch on {key}",
        )
        tot_turns += s_obj["turn_count"]
        tot_pass += exp_pass
        tot_cex += exp_cex
        tot_repairs += exp_rep
        tot_cross += exp_cross
        tot_h2m += exp_h2m
        tot_m2h += exp_m2h
        topics.append(
            {
                "topic_key": key,
                "session_file": sess_rel,
                "session_file_sha256": s_fsha,
                "turns_file": turns_rel,
                "turns_file_sha256": t_fsha,
                "transcript_sha256": recomp_sha,
                "pass_witness_count": exp_pass,
                "minimal_counterexample_count": exp_cex,
                "repairs": exp_rep,
                "cross_seat_compositions": exp_cross,
                "historical_to_modern": exp_h2m,
                "modern_to_historical": exp_m2h,
            }
        )

    return {
        "topics_verified": len(topics),
        "total_turns": tot_turns,
        "total_pass_witness": tot_pass,
        "total_minimal_counterexample": tot_cex,
        "total_repairs": tot_repairs,
        "total_cross_seat_compositions": tot_cross,
        "total_historical_to_modern": tot_h2m,
        "total_modern_to_historical": tot_m2h,
        "topics": topics,
        "passed": True,
    }


# ---------------------------------------------------------------------------
# Certificate Assembly, Tamper-Refusal Validation & CLI
# ---------------------------------------------------------------------------


def validate_certificate_payload(cert: Any) -> None:
    require_ok(isinstance(cert, dict), "BAD_CERT_TYPE", "certificate must be a dict")
    try:
        sos.validate_json_tree_no_floats(cert)
    except sos.SeminarError as exc:
        raise Pilot1Error(exc.code, exc.message) from exc
    require_ok(set(cert.keys()) == EXPECTED_CERT_KEYS, "BAD_CERT_KEYS", "certificate keys mismatch")
    require_ok(cert["schema"] == SCHEMA_PILOT1_CERT, "BAD_SCHEMA", "unexpected schema")
    require_ok(cert["energy_power_status"] == ENERGY_POWER_STATUS, "BAD_ENERGY", "energy_power_status mismatch")
    require_ok(cert["zero_floats"] is True, "BAD_ZERO_FLOATS", "zero_floats must be True")
    require_ok(cert["pure_q_ast_clean"] is True, "BAD_AST_FLAG", "pure_q_ast_clean must be True")
    require_ok(cert["all_passed"] is True, "GATES_NOT_ALL_PASSED", "all_passed must be True")
    try:
        sos.assert_clean_public_text(json.dumps(cert, sort_keys=True, ensure_ascii=True), check_model_pollution=True)
    except sos.SeminarError as exc:
        raise Pilot1Error(exc.code, exc.message) from exc

    payload = {k: v for k, v in cert.items() if k not in ("payload_sha256", "certificate_sha256")}
    exp_p = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    require_ok(
        type(cert["payload_sha256"]) is str and hmac.compare_digest(cert["payload_sha256"], exp_p),
        "PAYLOAD_SHA_MISMATCH",
        "payload_sha256 mismatch",
    )
    body = {k: v for k, v in cert.items() if k != "certificate_sha256"}
    exp_c = hashlib.sha256(_canonical_json_bytes(body)).hexdigest()
    require_ok(
        type(cert["certificate_sha256"]) is str and hmac.compare_digest(cert["certificate_sha256"], exp_c),
        "CERT_SHA_MISMATCH",
        "certificate_sha256 mismatch",
    )


def build_certificate(seminar_dir: Path) -> Dict[str, Any]:
    try:
        self_raw = sos.read_regular_file_bytes(Path(__file__), "MISSING_SELF")
        ast_res = sos.verify_pure_q_ast(self_raw.decode("utf-8"))
    except sos.SeminarError as exc:
        raise Pilot1Error(exc.code, exc.message) from exc
    except UnicodeDecodeError as exc:
        raise Pilot1Error("BAD_UTF8", f"Invalid UTF-8 in verifier source: {exc}") from exc
    live_tx = verify_pilot1_transcripts(seminar_dir)
    t1 = certify_t1_fricke_signature_unified()
    t2 = certify_t2_crt_valve_seal()
    t3 = certify_t3_unified_schur_witt_fold()
    all_passed = all((ast_res["pure_q_ast_clean"], live_tx["passed"], t1["passed"], t2["passed"], t3["passed"]))
    payload: Dict[str, Any] = {
        "schema": SCHEMA_PILOT1_CERT,
        "energy_power_status": ENERGY_POWER_STATUS,
        "zero_floats": True,
        "pure_q_ast_clean": ast_res["pure_q_ast_clean"],
        "pilot1_transcripts": live_tx,
        "t1_fricke_signature_unified": t1,
        "t2_crt_valve_seal": t2,
        "t3_unified_schur_witt_fold": t3,
        "all_passed": all_passed,
    }
    p_sha = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()
    cert = dict(payload)
    cert["payload_sha256"] = p_sha
    cert["certificate_sha256"] = hashlib.sha256(_canonical_json_bytes(cert)).hexdigest()
    validate_certificate_payload(cert)
    return cert


def check_certificate_file(path: Path, seminar_dir: Path) -> Dict[str, Any]:
    try:
        raw = sos.read_regular_file_bytes(path, missing_code="MISSING_CERT")
        data = sos.loads_strict_json_bytes(raw, path.name)
    except sos.SeminarError as exc:
        raise Pilot1Error(exc.code, exc.message) from exc
    validate_certificate_payload(data)
    expected = build_certificate(seminar_dir)
    require_ok(
        hmac.compare_digest(data["certificate_sha256"], expected["certificate_sha256"]),
        "LIVE_RECOMPUTE_MISMATCH",
        "Certificate does not match live recomputation",
    )
    return data


def default_seminar_dir() -> Path:
    return Path(__file__).resolve().parent


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Pure-Z/Q Verifier for Pilot-1 Seminar Syntheses")
    parser.add_argument("--seminar-dir", type=Path, default=default_seminar_dir(), help="Seminar package directory")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--standalone", action="store_true", help="Print canonical JSON certificate")
    group.add_argument("--write", type=Path, help="Write canonical JSON certificate")
    group.add_argument("--check", type=Path, help="Fail-closed verify certificate against live recomputation")
    args = parser.parse_args(argv)
    try:
        if args.check is not None:
            cert = check_certificate_file(args.check, args.seminar_dir)
            print(json.dumps({"status": "PASS", "certificate_sha256": cert["certificate_sha256"]}, sort_keys=True))
            return 0
        cert = build_certificate(args.seminar_dir)
        out_text = json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
        if args.write is not None:
            sos.refuse_symlink_path(args.write)
            args.write.write_text(out_text, encoding="utf-8")
            print(json.dumps({"status": "WRITTEN", "certificate_sha256": cert["certificate_sha256"]}, sort_keys=True))
            return 0
        sys.stdout.write(out_text)
        return 0
    except (Pilot1Error, sos.SeminarError) as exc:
        sys.stderr.write(json.dumps({"error_code": exc.code, "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2
    except OSError as exc:
        sys.stderr.write(json.dumps({"error_code": "IO_ERROR", "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
