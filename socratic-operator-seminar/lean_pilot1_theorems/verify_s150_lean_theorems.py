#!/usr/bin/env python3
"""
Fail-Closed Pure-Q + Lean 4.36.0 Verifier & Self-Bound Certificate Gate for
`S150Pilot1Theorems` (Bayt al-Hikma S^3 Seminar Unified Pilot-1 Theorems:
  1. Unified Fricke-Cayley Discriminant Across Definite Hurwitz & Split GL_2(Z),
  2. CRTVALVESEAL Bounded-Chatter Hysteresis TV & Khipu / Chiral Tree Checksum,
  3. Unified Schur-Witt-Fold Criterion, sqrt(2) Block-Drop Obstruction, & Mirror Billiard).

Zero IEEE-754 floats in AST, zero `ast.Div` or negative-exponent `ast.Pow` operators,
zero bare asserts, zero external dependencies, and 100% on-disk SHA-256 binding of all
9 Lean package files (`BOUND_PACKAGE_FILES`).
"""
from __future__ import annotations

import argparse
import ast
import errno
from fractions import Fraction
import hashlib
import json
from math import gcd, isqrt
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import tomllib
from typing import Any


PURE_CONSTRUCTIVE_AXIOMS: frozenset[str] = frozenset({"propext", "Quot.sound"})
EXPLICIT_BANNED_AXIOMS: frozenset[str] = frozenset(
    {"Classical.choice", "sorryAx", "Lean.ofReduceBool", "Lean.trustCompiler"}
)
EXPECTED_PUBLIC_THEOREMS: int = 36
ALLOWED_MATH_ATTRS: frozenset[str] = frozenset({"gcd", "isqrt"})
FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    {"builtins", "cmath", "ctypes", "decimal", "importlib", "mpmath", "numpy", "operator", "scipy", "sympy", "torch"}
)
FORBIDDEN_DYNAMIC_CALLS: frozenset[str] = frozenset(
    {"Decimal", "__import__", "complex", "eval", "exec", "float", "format", "format_map", "getattr", "globals", "literal_eval", "locals", "memoryview", "pow", "vars"}
)
FORBIDDEN_NAMES: frozenset[str] = frozenset(
    {
        "Decimal",
        "__annotations__",
        "__builtins__",
        "__import__",
        "__loader__",
        "__spec__",
        "compile",
        "complex",
        "eval",
        "exec",
        "float",
        "format",
        "format_map",
        "getattr",
        "globals",
        "literal_eval",
        "locals",
        "memoryview",
        "pow",
        "vars",
    }
)
FORBIDDEN_RATIONAL_METHODS: frozenset[str] = frozenset(
    {
        "__annotations__",
        "__builtins__",
        "__complex__",
        "__float__",
        "__globals__",
        "__itruediv__",
        "__pow__",
        "__rpow__",
        "__rtruediv__",
        "__subclasses__",
        "__truediv__",
        "format",
        "format_map",
        "from_decimal",
        "from_float",
        "literal_eval",
        "modules",
    }
)
MAX_FILE_BYTES: int = 16 * 1024 * 1024
MAX_JSON_DEPTH: int = 32
MAX_JSON_INT_DIGITS: int = 1024
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_IDENT_PRECEDING_RE = re.compile(r"[A-Za-z0-9_']")
_RAW_STR_START_RE = re.compile(r'r(#*)"')

BOUND_PACKAGE_FILES: tuple[str, ...] = (
    "AxiomAudit.lean",
    "S150Pilot1Theorems.lean",
    "S150Pilot1Theorems/IntPoly.lean",
    "S150Pilot1Theorems/Topic1FrickeCayley.lean",
    "S150Pilot1Theorems/Topic2ValveKhipu.lean",
    "S150Pilot1Theorems/Topic3SchurWittFold.lean",
    "lake-manifest.json",
    "lakefile.toml",
    "lean-toolchain",
)

EXPECTED_AXIOM_AUDIT_LINES: tuple[str, ...] = (
    "'S150Pilot1Theorems.evalPoly_norm' depends on axioms: [propext]",
    "'S150Pilot1Theorems.poly_eq_of_norm_eq' depends on axioms: [propext]",
    "'S150Pilot1Theorems.int_sq_nonneg' depends on axioms: [propext]",
    "'S150Pilot1Theorems.int_sq_eq_zero_iff' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.sum_two_sq_eq_zero_iff' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.nonneg_mul_nonneg' depends on axioms: [propext]",
    "'S150Pilot1Theorems.t1_fricke_homogeneity_16' depends on axioms: [propext]",
    "'S150Pilot1Theorems.t1_fricke_definite_commutator_exact' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t1_hurwitz_group_commutator_trace' depends on axioms: [propext]",
    "'S150Pilot1Theorems.t1_so3_frobenius_commutator_exact' depends on axioms: [propext]",
    "'S150Pilot1Theorems.t1_so3_parity_transfer_mod16' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t1_hurwitz_witnesses_and_spin_kernel' does not depend on any axioms",
    "'S150Pilot1Theorems.t1_fricke_split_transpose_factorization' depends on axioms: [propext]",
    "'S150Pilot1Theorems.t1_fricke_split_nonpos' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t1_fricke_split_vanishes_iff_symmetric' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t1_fricke_split_group_commutator_and_overshoot' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t1_split_cf_witnesses_exact' does not depend on any axioms",
    "'S150Pilot1Theorems.t2_valve_bounded_chatter_tv_universal' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_valve_zero_chatter_when_tv_lt_band' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_valve_strict_deadband_zero_flips' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_valve_flips_le_hi_plus_lo_hits' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_khipu_tree_sum_conservation' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_khipu_single_cord_tamper_detected' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_chiral_checksum_detects_single_and_swap' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_crt_two_moduli_necessity' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t2_seminar_crt_valve_seal_witnesses' does not depend on any axioms",
    "'S150Pilot1Theorems.t3_schur_fraction_free_congruence_2x2' depends on axioms: [propext]",
    "'S150Pilot1Theorems.t3_schur_fraction_free_congruence_3x3' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t3_glz_canonical_shear_iff_divides' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t3_glz_schur_integral_converse_counterexample' does not depend on any axioms",
    "'S150Pilot1Theorems.t3_two_mul_sq_ne_sq' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t3_block_drop_1x1_iff_square_class' depends on axioms: [propext]",
    "'S150Pilot1Theorems.t3_block_drop_obstruction_2111_and_witness_3334' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t3_gf2_inv_2x2_iff_det_odd' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t3_gf2_schur_preserves_even_diagonal' depends on axioms: [propext, Quot.sound]",
    "'S150Pilot1Theorems.t3_mirror_billiard_2_3_refutes_single_shear' depends on axioms: [propext]",
)

_FORBIDDEN_LEAN_CODE_RE = re.compile(
    r"[«»]"
    r"|\br#*\""
    r"|#[ \t]*(?:eval|reduce|guard_msgs|synth|test)\b"
    r"|\b(?:IO|System)\."
    r"|\b(?:sorry|admit|sorryAx|unsafe|native_decide|ofReduceBool|trustCompiler|"
    r"bv_decide|bv_check|bv_normalize|Classical|by_cases|grind|"
    r"implemented_by|extern|csimp|macro|macro_rules|elab|syntax|"
    r"run_cmd|run_elab|initialize|builtin_initialize|opaque|set_option|"
    r"notation|infix|infixl|infixr|prefix|postfix)\b"
    r"|\b[msf]!"
    r"|decide[ \t]*\+native"
    r"|native[ \t]*:="
    r"|(?<!\.)\baxiom\b"
    r"|(?<!\.)\bpartial\s+(?:def|abbrev|instance)\b"
    r"|\._native\."
)
_ANY_IMPORT_RE = re.compile(r"(?:^|\n)[ \t]*(?:(?:public|private|meta)[ \t]+)*import(?![A-Za-z0-9_'])([^\n]*)")
_VALID_IMPORT_MOD_RE = re.compile(r"S150Pilot1Theorems(?:\.[A-Za-z0-9_]+)*")
_PUB_THM_RE = re.compile(r"(?:^|\n)[ \t]*theorem[ \t]+([A-Za-z0-9_.']+)")
_PRINT_AXIOMS_RE = re.compile(r"(?:^|\n)[ \t]*#print[ \t]+axioms[ \t]+S150Pilot1Theorems\.([A-Za-z0-9_.']+)")


class S150LeanVerifyError(ValueError):
    """Typed fail-closed verification error for S150Pilot1Theorems."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def require_ok(cond: bool, code: str, message: str) -> None:
    if cond is not True:
        raise S150LeanVerifyError(code, message)


def _decode_utf8(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise S150LeanVerifyError("BAD_UTF8", f"{label} invalid UTF-8: {exc}") from exc


def _check_json_depth_pre_parse(text: str, max_depth: int = MAX_JSON_DEPTH) -> None:
    depth = 0
    in_str = False
    escaped = False
    for ch in text:
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "{[":
            depth += 1
            require_ok(depth <= max_depth, "CERT_JSON_DEPTH", "JSON nesting depth exceeded")
        elif ch in "}]":
            if depth > 0:
                depth -= 1


def refuse_symlink_path(path: Path) -> None:
    abs_path = path if path.is_absolute() else Path.cwd().joinpath(path)
    cur = Path(abs_path.anchor)
    for idx, part in enumerate(abs_path.parts[1:]):
        cur = cur.joinpath(part)
        if idx >= 1 or idx == len(abs_path.parts) - 2:
            require_ok(not cur.is_symlink(), "SYMLINK_FORBIDDEN", f"Symlink path or ancestor forbidden: {path.name}")


def read_regular_file_bytes(
    path: Path,
    missing_code: str = "MISSING_BOUND_FILE",
    max_bytes: int = MAX_FILE_BYTES,
) -> bytes:
    """Refuse symlinks/ancestors, open with O_NOFOLLOW|O_NONBLOCK, verify S_ISREG & byte cap."""
    refuse_symlink_path(path)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise S150LeanVerifyError("SYMLINK_FORBIDDEN", f"Symlink forbidden: {path.name}") from exc
        if exc.errno in (errno.ENOENT, errno.ENOTDIR):
            raise S150LeanVerifyError(missing_code, f"File not found: {path.name}") from exc
        raise S150LeanVerifyError("READ_ERROR", f"Failed to open {path.name}: {exc.strerror}") from exc
    try:
        try:
            st = os.fstat(fd)
            require_ok(stat.S_ISREG(st.st_mode), "NOT_REGULAR_FILE", f"Non-regular file forbidden: {path.name}")
            require_ok(st.st_size <= max_bytes, "FILE_TOO_LARGE", f"File exceeds byte cap: {path.name}")
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                total += len(chunk)
                require_ok(total <= max_bytes, "FILE_TOO_LARGE", f"Read exceeded byte cap: {path.name}")
                chunks.append(chunk)
            return b"".join(chunks)
        except OSError as exc:
            raise S150LeanVerifyError("READ_ERROR", f"Failed to read {path.name}: {exc.strerror}") from exc
    finally:
        os.close(fd)


def is_hex64(val: Any) -> bool:
    return isinstance(val, str) and HEX64_RE.fullmatch(val) is not None


def qdiv(num: Fraction, den: Fraction) -> Fraction:
    require_ok(den != Fraction(0), "QDIV_ZERO_DENOM", "Zero denominator in exact rational division")
    return Fraction(num.numerator * den.denominator, num.denominator * den.numerator)


def _is_safe_int_ast(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return type(node.value) is int
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_safe_int_ast(node.operand)
    if isinstance(node, ast.Attribute) and node.attr in ("numerator", "denominator"):
        return True
    if isinstance(node, ast.BinOp):
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
            return _is_safe_int_ast(node.left) and _is_safe_int_ast(node.right)
        if isinstance(node.op, ast.LShift):
            return _is_safe_int_ast(node.left) and (
                isinstance(node.right, ast.Name) or _is_safe_int_ast(node.right)
            )
    return False


def _is_fraction_ref(expr: ast.AST, fraction_aliases: set[str]) -> bool:
    return (isinstance(expr, ast.Name) and expr.id in fraction_aliases) or (
        isinstance(expr, ast.Attribute) and expr.attr == "Fraction"
    )


def verify_pure_q_ast(source_text: str) -> dict[str, Any]:
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise S150LeanVerifyError("AST_SYNTAX_ERROR", f"Invalid Python syntax: {exc}") from exc
    math_aliases: set[str] = set()
    fraction_aliases: set[str] = {"Fraction"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                require_ok(root not in FORBIDDEN_IMPORTS, "AST_FORBIDDEN_IMPORT", f"Forbidden import {alias.name}")
                if root == "math":
                    math_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            require_ok(node.level == 0, "AST_REL_IMPORT_FORBIDDEN", "Relative imports forbidden")
            mod_root = str(node.module).split(".")[0]
            require_ok(mod_root not in FORBIDDEN_IMPORTS, "AST_FORBIDDEN_IMPORT", f"Forbidden import from {node.module}")
            for alias in node.names:
                require_ok(alias.name != "*", "AST_WILDCARD_IMPORT", f"Wildcard import from {node.module} forbidden")
                if mod_root == "math":
                    require_ok(
                        alias.name in ALLOWED_MATH_ATTRS,
                        "AST_FORBIDDEN_MATH_SYM",
                        f"Forbidden math symbol {alias.name}",
                    )
                elif mod_root == "fractions":
                    require_ok(
                        alias.name == "Fraction",
                        "AST_FORBIDDEN_FRACTIONS_SYM",
                        f"Forbidden fractions symbol {alias.name}",
                    )
                    fraction_aliases.add(alias.asname or alias.name)

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            targets: list[ast.AST] = []
            val_expr: ast.AST | None = None
            if isinstance(node, ast.Assign):
                targets = list(node.targets)
                val_expr = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets = [node.target]
                val_expr = node.value
            elif isinstance(node, ast.NamedExpr):
                targets = [node.target]
                val_expr = node.value
            if val_expr is None:
                continue
            for tgt in targets:
                if isinstance(tgt, ast.Name):
                    if _is_fraction_ref(val_expr, fraction_aliases) and tgt.id not in fraction_aliases:
                        fraction_aliases.add(tgt.id)
                        changed = True
                    if isinstance(val_expr, ast.Name) and val_expr.id in math_aliases and tgt.id not in math_aliases:
                        math_aliases.add(tgt.id)
                        changed = True

    ann_ids: set[int] = set()
    called_fn_ids: set[int] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            called_fn_ids.add(id(n.func))
        elif isinstance(n, ast.FunctionDef) and n.returns is not None:
            ann_ids.update(id(s) for s in ast.walk(n.returns))
        elif isinstance(n, ast.arg) and n.annotation is not None:
            ann_ids.update(id(s) for s in ast.walk(n.annotation))
        elif isinstance(n, ast.AnnAssign) and n.annotation is not None:
            ann_ids.update(id(s) for s in ast.walk(n.annotation))

    for node in ast.walk(tree):
        require_ok(not isinstance(node, ast.Assert), "AST_BARE_ASSERT", "Bare assert forbidden")
        require_ok(not isinstance(node, ast.Div), "AST_DIV_FORBIDDEN", "Use qdiv(a, b) instead of '/' operator")
        require_ok(not isinstance(node, ast.FloorDiv), "AST_FLOORDIV_FORBIDDEN", "Use divmod(a, b)[0] instead of '//' operator")
        require_ok(not isinstance(node, ast.Mod), "AST_MOD_FORBIDDEN", "Use divmod(a, b)[1] instead of '%' operator")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            require_ok(
                isinstance(node.right, ast.Constant)
                and type(node.right.value) is int
                and node.right.value >= 0,
                "AST_POW_EXP_FORBIDDEN",
                "Exponent in '**' must be a non-negative integer literal",
            )
        elif isinstance(node, ast.FormattedValue):
            require_ok(node.format_spec is None, "AST_FORMAT_SPEC_FORBIDDEN", "Format specifiers forbidden in pure-Q f-strings")
        elif isinstance(node, ast.Constant):
            require_ok(
                type(node.value).__name__ not in ("float", "complex"),
                "AST_FLOAT_LITERAL",
                f"Forbidden float/complex literal {node.value!r}",
            )
        elif isinstance(node, ast.Name):
            require_ok(node.id not in FORBIDDEN_NAMES, "AST_FORBIDDEN_NAME", f"Forbidden name {node.id}")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                require_ok(node.attr in ("__init__", "__name__"), "AST_FROM_FLOAT_FORBIDDEN", f"Forbidden dunder .{node.attr}")
            require_ok(
                node.attr not in FORBIDDEN_RATIONAL_METHODS,
                "AST_FROM_FLOAT_FORBIDDEN",
                f"Forbidden attribute .{node.attr}",
            )
            if isinstance(node.value, ast.Name) and node.value.id in math_aliases:
                require_ok(
                    node.attr in ALLOWED_MATH_ATTRS,
                    "AST_FORBIDDEN_MATH_ATTR",
                    f"Forbidden math.{node.attr}",
                )
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set, ast.Dict, ast.Subscript)) and id(node) not in ann_ids:
            for sub in ast.walk(node):
                if id(sub) not in called_fn_ids:
                    require_ok(
                        not _is_fraction_ref(sub, fraction_aliases),
                        "AST_FRACTION_CONTAINER",
                        "Wrapping or indexing Fraction is forbidden",
                    )
        elif isinstance(node, ast.Call):
            fn_expr = node.func.value if isinstance(node.func, ast.NamedExpr) else node.func
            require_ok(
                isinstance(fn_expr, (ast.Name, ast.Attribute)),
                "AST_INDIRECT_CALL",
                "Indirect call expression forbidden in pure-Q code",
            )
            fn_name = ""
            is_frac_call = False
            if isinstance(fn_expr, ast.Name):
                fn_name = fn_expr.id
                if fn_name in fraction_aliases:
                    is_frac_call = True
            elif isinstance(fn_expr, ast.Attribute):
                fn_name = fn_expr.attr
                if fn_name == "Fraction":
                    is_frac_call = True
            require_ok(fn_name not in FORBIDDEN_DYNAMIC_CALLS, "AST_FLOAT_CALL", f"Forbidden call to {fn_name}()")
            if is_frac_call:
                require_ok(len(node.keywords) == 0, "AST_FRACTION_KW", "Keyword args to Fraction() forbidden")
                require_ok(1 <= len(node.args) <= 2, "AST_FRACTION_ARITY", "Fraction() must take 1 or 2 integer args")
                for arg in node.args:
                    require_ok(
                        _is_safe_int_ast(arg),
                        "AST_FRACTION_ARG_UNSAFE",
                        "Fraction() arguments must be proven integer AST expressions",
                    )
    return {"pure_q_ast_clean": True}


def _match_lean_char_literal_end(src: str, pos: int) -> int:
    n = len(src)
    if pos > 0 and _IDENT_PRECEDING_RE.fullmatch(src[pos - 1]) is not None:
        return -1
    if pos + 2 >= n:
        return -1
    nxt = src[pos + 1]
    if nxt in ("\n", "'"):
        return -1
    if nxt != "\\":
        return pos + 3 if src[pos + 2] == "'" else -1
    esc = src[pos + 2]
    close_idx = -1
    if esc in ("\\", "'", '"', "n", "t", "r", "0"):
        close_idx = pos + 3
    elif esc == "x":
        close_idx = pos + 5
    elif esc == "u":
        close_idx = pos + 7
    if close_idx > 0 and src[close_idx : close_idx + 1] == "'":
        return close_idx + 1
    return -1


def strip_lean_comments_and_strings(src: str) -> str:
    out: list[str] = []
    i = 0
    n = len(src)
    depth = 0
    in_str = False
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if depth > 0:
            if ch == "/" and nxt == "-":
                depth += 1
                out.append("  ")
                i += 2
            elif ch == "-" and nxt == "/":
                depth -= 1
                out.append("  ")
                i += 2
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
        elif in_str:
            if ch == "\\" and i + 1 < n:
                out.append("  ")
                i += 2
            elif ch == '"':
                in_str = False
                out.append(" ")
                i += 1
            else:
                out.append("\n" if ch == "\n" else " ")
                i += 1
        elif ch == "-" and nxt == "-":
            while i < n and src[i] != "\n":
                out.append(" ")
                i += 1
        elif ch == "/" and nxt == "-":
            depth = 1
            out.append("  ")
            i += 2
        elif ch == "'":
            end_pos = _match_lean_char_literal_end(src, i)
            if end_pos > i:
                out.append(" " * (end_pos - i))
                i = end_pos
            else:
                out.append(ch)
                i += 1
        elif ch == "r":
            m_raw = _RAW_STR_START_RE.match(src, i) if _IDENT_PRECEDING_RE.fullmatch(src[i - 1 : i]) is None else None
            if m_raw is not None:
                hashes = m_raw.group(1)
                closer = '"' + hashes
                end_raw = src.find(closer, m_raw.end())
                require_ok(end_raw != -1, "UNTERMINATED_STRING_LITERAL", "Unterminated raw string literal")
                out.append(m_raw.group(0))
                out.append(" " * (end_raw + len(closer) - m_raw.end()))
                i = end_raw + len(closer)
            else:
                out.append(ch)
                i += 1
        elif ch == '"':
            in_str = True
            out.append(" ")
            i += 1
        else:
            out.append(ch)
            i += 1
    require_ok(depth == 0, "UNTERMINATED_BLOCK_COMMENT", "Unterminated Lean block comment")
    require_ok(not in_str, "UNTERMINATED_STRING_LITERAL", "Unterminated Lean string literal")
    return "".join(out)


def fricke_disc_z(a: int, b: int, x: int, y: int, z: int) -> int:
    return 4 * a * b - b * x * x - a * y * y - z * z + x * y * z


def _cf_mat2(terms: tuple[int, ...]) -> tuple[int, int, int, int]:
    p, q, r, s = 1, 0, 0, 1
    for t in terms:
        p, q, r, s = p * t + q, p, r * t + s, r
    return (p, q, r, s)


def verify_topic1_fricke_cayley_q(
    fricke_fn: Any = fricke_disc_z,
    frob_cleared_fn: Any = None,
    overshoot_fn: Any = None,
    definite_cases: tuple[Any, ...] = (
        ((5, 3, 1, 1), (13, 5, 1, 1), 1, 7048, 440),
        ((4, 4, 2, 0), (12, 6, 4, 0), 2, 14080, 439),
        ((0, 2, 0, 0), (0, 0, 2, 0), 2, 0, -1),
    ),
    split_cases: tuple[Any, ...] = (
        ((1, 1, 2), -41, 144, False),
        ((2, 1, 2), 0, 324, True),
        ((1, 1, 1, 1, 2), -2421, 1024, False),
        ((3, 7, 16), -1153783449, 524176, False),
    ),
) -> dict[str, Any]:
    if frob_cleared_fn is None:
        frob_cleared_fn = lambda ab, d_val: 8 * d_val * (2 * ab - d_val)
    if overshoot_fn is None:
        overshoot_fn = lambda s_det, tr_w: 2 * (1 - s_det) * tr_w * tr_w

    for A, B, exp_d, exp_f, exp_rec in definite_cases:
        na4 = A[0] * A[0] + A[1] * A[1] + A[2] * A[2] + A[3] * A[3]
        nb4 = B[0] * B[0] + B[1] * B[1] + B[2] * B[2] + B[3] * B[3]
        ab = divmod(na4, 4)[0] * divmod(nb4, 4)[0]
        z_dbl = A[0] * B[0] - A[1] * B[1] - A[2] * B[2] - A[3] * B[3]
        kap16 = fricke_fn(na4, nb4, 2 * A[0], 2 * B[0], 2 * z_dbl)
        cx = A[2] * B[3] - A[3] * B[2]
        cy = A[3] * B[1] - A[1] * B[3]
        cz = A[1] * B[2] - A[2] * B[1]
        csq = cx * cx + cy * cy + cz * cz
        d_val = divmod(csq, 8)[0]
        require_ok(d_val == exp_d, "T1_DEFINITE_D_MISMATCH", f"Expected D={exp_d}, got {d_val}")
        require_ok(kap16 == 4 * csq, "T1_DEFINITE_KAPPA_FAIL", "frickeDisc != 4 * crossSq3")
        require_ok(ab - d_val == exp_rec, "T1_GROUP_COMM_REC_FAIL", f"Expected reC={exp_rec}")
        fc = frob_cleared_fn(ab, d_val)
        require_ok(fc == exp_f, "T1_FROB_CLEARED_FAIL", f"Expected F_cleared={exp_f}, got {fc}")
        require_ok(divmod(fc, 16)[1] == divmod(8 * d_val, 16)[1], "T1_PARITY_MOD16_FAIL", "mod-16 parity transfer failed")

    for terms, exp_kap, exp_ov, exp_sym in split_cases:
        p, q, r, s = _cf_mat2(terms)
        det_w = p * s - q * r
        tr_w = p + s
        z_tr = p * p + q * q + r * r + s * s
        kap = fricke_fn(det_w, det_w, tr_w, tr_w, z_tr)
        fac = -(((p - s) * (p - s) + (q + r) * (q + r)) * ((q - r) * (q - r)))
        require_ok(kap == fac, "T1_SPLIT_FACTOR_FAIL", "Split Fricke != transpose factor")
        require_ok(kap == exp_kap, "T1_SPLIT_KAPPA_MISMATCH", f"Expected kappa={exp_kap}, got {kap}")
        require_ok((kap == 0) == exp_sym, "T1_PALINDROME_IFF_FAIL", "Palindrome vanishing iff failed")
        tr_c = 2 - kap
        naive_sl2 = 2 * tr_w * tr_w + z_tr * z_tr - tr_w * tr_w * z_tr - 2
        ov = overshoot_fn(det_w, tr_w)
        require_ok(naive_sl2 - tr_c == ov, "T1_OVERSHOOT_LAW_FAIL", "Overshoot != 2*(1-s)*t^2")
        require_ok(ov == exp_ov, "T1_OVERSHOOT_VAL_FAIL", f"Expected overshoot={exp_ov}, got {ov}")

    return {"definite_witnesses": len(definite_cases), "split_cf_witnesses": len(split_cases)}


def _valve_flips_and_tv(lo: Fraction, hi: Fraction, init: int, stream: tuple[Fraction, ...]) -> tuple[int, Fraction]:
    cur = init
    flips = 0
    for v in stream:
        if v >= hi:
            nxt = 1
        elif v <= lo:
            nxt = 0
        else:
            nxt = cur
        if nxt != cur:
            flips += 1
        cur = nxt
    tv = Fraction(0)
    for idx in range(len(stream) - 1):
        diff = stream[idx + 1] - stream[idx]
        tv += diff if diff >= Fraction(0) else -diff
    return flips, tv


def _chiral_root(leaves: tuple[int, ...]) -> int:
    if len(leaves) == 1:
        return leaves[0]
    mid = divmod(len(leaves), 2)[0]
    return _chiral_root(leaves[:mid]) + 3 * _chiral_root(leaves[mid:])


def verify_topic2_valve_khipu_q(
    valve_eval_fn: Any = _valve_flips_and_tv,
    chiral_fn: Any = _chiral_root,
    witness_streams: tuple[Any, ...] = (
        (Fraction(0), Fraction(2), 0, (Fraction(3), Fraction(-1), Fraction(1)), 2, Fraction(6), (3, 4), 15),
        (Fraction(1), Fraction(3), 0, (Fraction(4), Fraction(2), Fraction(5), Fraction(0)), 2, Fraction(10), (7, 2), 13),
        (
            Fraction(1, 2),
            Fraction(3, 2),
            1,
            (Fraction(1), Fraction(0), Fraction(2), Fraction(1), Fraction(1, 3), Fraction(2)),
            4,
            Fraction(19, 3),
            (3, 2, 5, 2, 3),
            123,
        ),
        (Fraction(0), Fraction(10), 0, (Fraction(12), Fraction(8), Fraction(5)), 1, Fraction(7), (5,), 5),
    ),
    crt_pair: tuple[int, int, int, int] = (6, 10, 3, 8),
) -> dict[str, Any]:
    for lo, hi, init, stream, exp_f, exp_tv, leaves, exp_root in witness_streams:
        flips, tv = valve_eval_fn(lo, hi, init, stream)
        require_ok(flips == exp_f, "T2_FLIPS_MISMATCH", f"Expected flips={exp_f}, got {flips}")
        require_ok(tv == exp_tv, "T2_TV_MISMATCH", f"Expected tv={exp_tv}, got {tv}")
        require_ok((flips - 1) * (hi - lo) <= tv, "T2_TV_BOUND_FAIL", "(F - 1)*(hi - lo) > TV")
        root = chiral_fn(leaves)
        require_ok(root == exp_root, "T2_CHIRAL_ROOT_MISMATCH", f"Expected root={exp_root}, got {root}")

    require_ok(chiral_fn((3, 2)) != chiral_fn((2, 3)), "T2_CHIRAL_SWAP_BLIND", "Chiral checksum missed sibling swap")
    m1, m2, r1, r2 = crt_pair
    require_ok(divmod(r1 - r2, gcd(m1, m2))[1] != 0, "T2_CRT_INCONSISTENT_MISSED", "CRT witness must be inconsistent")
    return {"valve_streams_verified": len(witness_streams), "seminar_roots": [15, 13, 123]}


def _is_q_square(val: Fraction) -> bool:
    if val <= Fraction(0):
        return False
    rn = isqrt(val.numerator)
    rd = isqrt(val.denominator)
    return rn * rn == val.numerator and rd * rd == val.denominator


def verify_topic3_schur_witt_fold_q(
    q_square_fn: Any = _is_q_square,
    billiard_period_fn: Any = None,
    converse_triple: tuple[int, int, int] = (4, 2, 1),
    gf2_pair: tuple[int, int] = (3, 4),
    billiard_pair: tuple[int, int] = (2, 3),
) -> dict[str, Any]:
    if billiard_period_fn is None:
        def _default_period(p: int, q: int) -> int:
            w, h = 2 * p, 2 * q
            st0 = (1, 0, 1, 1)
            cur = st0
            steps = 0
            while steps == 0 or cur != st0:
                x, y, dx, dy = cur
                nx, ny = x + dx, y + dy
                ndx = -dx if (nx == 0 or nx == w) else dx
                ndy = -dy if (ny == 0 or ny == h) else dy
                cur = (nx, ny, ndx, ndy)
                steps += 1
            return steps
        billiard_period_fn = _default_period

    s_2111 = Fraction(1) - qdiv(Fraction(1), Fraction(2))
    require_ok(not q_square_fn(s_2111 * Fraction(1)), "T3_SQRT2_OBSTRUCTION_FAIL", "1/2 must not be a Q-square")

    s_3334 = Fraction(4) - qdiv(Fraction(9), Fraction(3))
    require_ok(q_square_fn(s_3334 * Fraction(4)), "T3_3334_WITNESS_FAIL", "4 must be a Q-square")

    ca, cb, cd = converse_triple
    require_ok(divmod(ca * cd - cb * cb, ca)[1] == 0 and divmod(cb, ca)[1] != 0, "T3_CONVERSE_CEX_FAIL", "Integral-Schur converse cex failed")

    det_a3, schur_num_a3 = gf2_pair
    require_ok(divmod(det_a3, 2)[1] == 1 and divmod(schur_num_a3, 2)[1] == 0, "T3_GF2_PARITY_FAIL", "GF(2) odd-det / even-Schur failed")

    bp, bq = billiard_pair
    per = billiard_period_fn(bp, bq)
    require_ok(per == 24 and divmod(bq, bp)[1] != 0, "T3_BILLIARD_23_FAIL", "Mirror billiard (2,3) check failed")
    return {"schur_witnesses_verified": 4, "mirror_billiard_2_3_period": per}


def read_package_snapshot(pkg_dir: Path) -> dict[str, bytes]:
    refuse_symlink_path(pkg_dir)
    require_ok(pkg_dir.is_dir(), "MISSING_LEAN_DIR", "lean_pilot1_theorems package directory missing")
    lean_files_disk = list(pkg_dir.rglob("*.lean"))
    for lf in lean_files_disk:
        refuse_symlink_path(lf)
    lean_on_disk = sorted(str(p.relative_to(pkg_dir)).replace("\\", "/") for p in lean_files_disk)
    expected_lean = sorted(r for r in BOUND_PACKAGE_FILES if r.endswith(".lean"))
    require_ok(
        lean_on_disk == expected_lean,
        "LEAN_FILE_SET_FAIL",
        f"Expected .lean files {expected_lean}, found {lean_on_disk}",
    )
    snap: dict[str, bytes] = {}
    for rel in BOUND_PACKAGE_FILES:
        fpath = Path(pkg_dir, rel)
        snap[rel] = read_regular_file_bytes(fpath, missing_code="MISSING_BOUND_FILE")
    return snap


def compute_bound_source_hashes(pkg_dir: Path, snap: dict[str, bytes] | None = None) -> dict[str, str]:
    data = snap if snap is not None else read_package_snapshot(pkg_dir)
    return {rel: hashlib.sha256(data[rel]).hexdigest() for rel in BOUND_PACKAGE_FILES}


def default_live_lean_runner(pkg_dir: Path, snap: dict[str, bytes] | None = None) -> dict[str, Any]:
    data = snap if snap is not None else read_package_snapshot(pkg_dir)
    home = os.path.expanduser("~")
    elan_bin = str(Path(home, ".elan", "bin"))
    extra_path = os.environ.get("PATH", "")
    env = {
        "PATH": f"{elan_bin}:/usr/local/bin:/usr/bin:/bin:{extra_path}",
        "HOME": home,
        "CUDA_VISIBLE_DEVICES": "",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp_lean = Path(td, "lean_pilot1_theorems")
            for rel, raw in data.items():
                dst = Path(tmp_lean, rel)
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(raw)
            r_build = subprocess.run(["lake", "build"], cwd=tmp_lean, env=env, capture_output=True, text=True, timeout=180, check=False)
            manifest_path = Path(tmp_lean, "lake-manifest.json")
            manifest_present = manifest_path.is_file()
            manifest_after = manifest_path.read_bytes() if manifest_present else b""
            config_unchanged = (
                Path(tmp_lean, "lakefile.toml").read_bytes() == data["lakefile.toml"]
                and Path(tmp_lean, "lean-toolchain").read_bytes() == data["lean-toolchain"]
            )
            r_lc = subprocess.run(
                ["lake", "env", "leanchecker", "--fresh", "S150Pilot1Theorems"],
                cwd=tmp_lean,
                env=env,
                capture_output=True,
                text=True,
                timeout=600,
                check=False,
            )
            r_ax = subprocess.run(
                ["lake", "env", "lean", "AxiomAudit.lean"],
                cwd=tmp_lean,
                env=env,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            return {
                "manifest_present": manifest_present,
                "manifest_unchanged": manifest_after == data["lake-manifest.json"],
                "config_unchanged": config_unchanged,
                "build_rc": r_build.returncode,
                "build_output": r_build.stdout + "\n" + r_build.stderr,
                "leanchecker_rc": r_lc.returncode,
                "leanchecker_output": r_lc.stdout + "\n" + r_lc.stderr,
                "axiom_rc": r_ax.returncode,
                "axiom_stdout": r_ax.stdout,
            }
    except subprocess.TimeoutExpired as exc:
        raise S150LeanVerifyError("LEAN_TIMEOUT", f"Lean subprocess timed out: {exc.timeout}s") from exc
    except OSError as exc:
        raise S150LeanVerifyError("LEAN_EXEC_ERROR", f"Failed to execute Lean toolchain: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise S150LeanVerifyError("LEAN_OUTPUT_BAD_UTF8", f"Lean subprocess emitted invalid UTF-8: {exc}") from exc


def validate_axiom_audit_lines(axiom_lines: list[str] | tuple[str, ...], expected_count: int) -> dict[str, int]:
    non_empty = [ln.strip() for ln in axiom_lines if ln.strip()]
    require_ok(
        len(non_empty) == expected_count,
        "AXIOM_LINE_COUNT_FAIL",
        f"Expected {expected_count} #print axioms lines, got {len(non_empty)}",
    )
    propext_only = 0
    propext_quot = 0
    zero_ax = 0
    for ln in non_empty:
        if "does not depend on any axioms" in ln:
            zero_ax += 1
            continue
        require_ok("depends on axioms:" in ln, "UNRECOGNIZED_AXIOM_LINE", f"Unrecognized axiom line: {ln}")
        rhs = ln.split("depends on axioms:", 1)[1].strip()
        require_ok(rhs.startswith("["), "MALFORMED_AXIOM_LBRACKET", f"Missing '[': {ln}")
        require_ok(rhs.endswith("]"), "MALFORMED_AXIOM_RBRACKET", f"Missing ']': {ln}")
        axs = [a.strip() for a in rhs[1:-1].split(",") if a.strip()]
        for ax in axs:
            require_ok(
                ax not in EXPLICIT_BANNED_AXIOMS and "._native." not in ax,
                "BANNED_AXIOM",
                f"Explicitly banned axiom {ax} in {ln}",
            )
            require_ok(ax in PURE_CONSTRUCTIVE_AXIOMS, "FORBIDDEN_AXIOM", f"Forbidden axiom {ax} in {ln}")
        if set(axs) == {"propext"}:
            propext_only += 1
        else:
            propext_quot += 1
    return {"zero_axiom_theorems": zero_ax, "propext_only_theorems": propext_only, "propext_quot_theorems": propext_quot}


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pairs:
        require_ok(k not in out, "CERT_DUPLICATE_KEY", f"Duplicate JSON key: {k}")
        out[k] = v
    return out


def _reject_json_float(tok: str) -> Any:
    raise S150LeanVerifyError("CERT_FORBIDDEN_JSON_NUM", f"Float literal forbidden in JSON: {tok}")


def _reject_json_constant(tok: str) -> Any:
    raise S150LeanVerifyError("CERT_FORBIDDEN_JSON_NUM", f"Non-finite constant forbidden in JSON: {tok}")


def _parse_bounded_int(tok: str) -> int:
    require_ok(
        len(tok.lstrip("+-")) <= MAX_JSON_INT_DIGITS,
        "CERT_INT_TOO_LARGE",
        "JSON integer exceeds digit cap",
    )
    return int(tok)


def loads_strict_json_bytes(raw_bytes: bytes, label: str) -> Any:
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise S150LeanVerifyError("CERT_INVALID_JSON", f"{label} invalid UTF-8: {exc}") from exc
    _check_json_depth_pre_parse(text)
    try:
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_float=_reject_json_float,
            parse_constant=_reject_json_constant,
            parse_int=_parse_bounded_int,
        )
    except S150LeanVerifyError:
        raise
    except RecursionError as exc:
        raise S150LeanVerifyError("CERT_JSON_DEPTH", f"{label} JSON nesting depth exceeded: {exc}") from exc
    except ValueError as exc:
        raise S150LeanVerifyError("CERT_INVALID_JSON", f"{label} invalid JSON: {exc}") from exc


def canonical_json_bytes(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def verify_lean_package(
    pkg_dir: Path,
    run_live_lean: bool = False,
    lean_runner: Any = None,
    snap: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    data = snap if snap is not None else read_package_snapshot(pkg_dir)

    toolchain = _decode_utf8(data["lean-toolchain"], "lean-toolchain").strip()
    require_ok(toolchain == "leanprover/lean4:v4.36.0", "BAD_TOOLCHAIN", f"Unexpected toolchain: {toolchain}")

    manifest = loads_strict_json_bytes(data["lake-manifest.json"], "lake-manifest.json")
    require_ok(isinstance(manifest, dict) and manifest.get("packages") == [], "NONEMPTY_LAKE_PACKAGES", "lake-manifest.json packages must be []")

    try:
        lake_cfg = tomllib.loads(data["lakefile.toml"].decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise S150LeanVerifyError("BAD_LAKEFILE_TOML", f"Invalid lakefile.toml: {exc}") from exc
    require_ok(
        lake_cfg.get("require", []) == [],
        "NONEMPTY_LAKEFILE_REQUIRE",
        "lakefile.toml must declare zero external [[require]] dependencies",
    )
    require_ok(
        set(lake_cfg.keys()) == {"name", "defaultTargets", "lean_lib"}
        and lake_cfg.get("name") == "S150Pilot1Theorems"
        and lake_cfg.get("defaultTargets") == ["S150Pilot1Theorems"]
        and lake_cfg.get("lean_lib") == [{"name": "S150Pilot1Theorems"}],
        "FORBIDDEN_LAKEFILE_OPT",
        "lakefile.toml must contain only pinned name, defaultTargets, and clean lean_lib (no moreLeanArgs/plugins)",
    )

    lean_rels = sorted(r for r in BOUND_PACKAGE_FILES if r.endswith(".lean"))
    total_loc = 0
    pub_thms: list[str] = []
    for rel in lean_rels:
        src = _decode_utf8(data[rel], rel)
        total_loc += len(src.splitlines())
        cleaned = strip_lean_comments_and_strings(src)
        require_ok(
            _FORBIDDEN_LEAN_CODE_RE.search(cleaned) is None,
            "LEAN_STATIC_ESCAPE",
            f"Forbidden tactic, axiom, #eval, IO, or macro escape in {rel}",
        )
        for m_imp in _ANY_IMPORT_RE.finditer(cleaned):
            mod = m_imp.group(1).strip()
            require_ok(
                _VALID_IMPORT_MOD_RE.fullmatch(mod) is not None,
                "FORBIDDEN_IMPORT",
                f"Non-Init or non-project import {mod} in {rel}",
            )
        if rel.startswith("S150Pilot1Theorems/"):
            pub_thms.extend(_PUB_THM_RE.findall(cleaned))

    audit_cleaned = strip_lean_comments_and_strings(_decode_utf8(data["AxiomAudit.lean"], "AxiomAudit.lean"))
    audited_thms = _PRINT_AXIOMS_RE.findall(audit_cleaned)
    require_ok(
        len(pub_thms) == EXPECTED_PUBLIC_THEOREMS,
        "PUB_THM_COUNT_FAIL",
        f"Expected {EXPECTED_PUBLIC_THEOREMS} public theorems, found {len(pub_thms)}",
    )
    require_ok(set(pub_thms) == set(audited_thms), "AXIOM_AUDIT_SET_MISMATCH", "AxiomAudit.lean != public theorems")
    require_ok(
        len(audited_thms) == EXPECTED_PUBLIC_THEOREMS,
        "AXIOM_AUDIT_DUP_OR_LEN",
        f"Expected {EXPECTED_PUBLIC_THEOREMS} #print axioms, got {len(audited_thms)}",
    )

    pinned_counts = validate_axiom_audit_lines(EXPECTED_AXIOM_AUDIT_LINES, EXPECTED_PUBLIC_THEOREMS)
    live_flag = bool(run_live_lean or lean_runner is not None)
    if live_flag:
        if lean_runner is not None:
            run_res = lean_runner(pkg_dir)
        else:
            run_res = default_live_lean_runner(pkg_dir, snap=data)
        require_ok(run_res.get("manifest_present") is True, "MISSING_SANDBOX_MANIFEST", "Sandbox omitted lake-manifest.json")
        require_ok(run_res.get("manifest_unchanged") is True, "SANDBOX_MANIFEST_MUTATED", "lake build mutated lake-manifest.json")
        require_ok(run_res.get("config_unchanged") is True, "SANDBOX_CONFIG_MUTATED", "lake build mutated lakefile.toml or lean-toolchain")
        require_ok(run_res["build_rc"] == 0, "LAKE_BUILD_FAIL", "lake build exited non-zero")
        require_ok("warning:" not in run_res["build_output"].lower(), "LAKE_BUILD_WARNING", "lake build emitted warning")
        require_ok(run_res["leanchecker_rc"] == 0, "LEANCHECKER_FAIL", "leanchecker --fresh failed")
        require_ok(run_res["axiom_rc"] == 0, "AXIOM_AUDIT_EXEC_FAIL", "AxiomAudit.lean failed")
        live_lines = [ln.strip() for ln in run_res["axiom_stdout"].splitlines() if ln.strip()]
        ax_counts = validate_axiom_audit_lines(live_lines, EXPECTED_PUBLIC_THEOREMS)
        require_ok(
            tuple(live_lines) == EXPECTED_AXIOM_AUDIT_LINES,
            "AXIOM_PIN_MISMATCH",
            "Live #print axioms output drifted from pinned 36-theorem axiom profile",
        )
    else:
        ax_counts = pinned_counts

    return {
        "lean_toolchain": toolchain,
        "lean_files": len(lean_rels),
        "lean_loc": total_loc,
        "public_theorems_audited": len(pub_thms),
        "live_lean_verified": live_flag,
        "axiom_breakdown": ax_counts,
    }


def build_certificate(
    pkg_dir: Path | None = None,
    run_live_lean: bool = False,
    lean_runner: Any = None,
) -> dict[str, Any]:
    base = pkg_dir if pkg_dir is not None else Path(__file__).resolve().parent
    snap = read_package_snapshot(base)
    verifier_src = _decode_utf8(
        read_regular_file_bytes(Path(base, "verify_s150_lean_theorems.py"), "MISSING_SELF"),
        "verify_s150_lean_theorems.py",
    )
    ast_info = verify_pure_q_ast(verifier_src)
    t1 = verify_topic1_fricke_cayley_q()
    t2 = verify_topic2_valve_khipu_q()
    t3 = verify_topic3_schur_witt_fold_q()
    lean_info = verify_lean_package(base, run_live_lean=run_live_lean, lean_runner=lean_runner, snap=snap)
    source_hashes = compute_bound_source_hashes(base, snap=snap)

    payload: dict[str, Any] = {
        "schema_version": "bayt_al_hikma.s150_pilot1_lean436.v1",
        "module": "S150Pilot1Theorems",
        "energy_power_status": "UNCONTROLLED_LAPTOP_NOT_CLAIMED",
        "pure_q_ast": ast_info,
        "topic1_fricke_cayley": t1,
        "topic2_valve_khipu": t2,
        "topic3_schur_witt_fold": t3,
        "lean_verification": lean_info,
        "source_files_sha256": source_hashes,
    }
    canon = canonical_json_bytes(payload)
    payload["payload_sha256"] = hashlib.sha256(canon).hexdigest()
    return payload


def validate_certificate(
    cert_obj: Any,
    pkg_dir: Path | None = None,
    run_live_lean: bool = False,
    lean_runner: Any = None,
) -> dict[str, Any]:
    base = pkg_dir if pkg_dir is not None else Path(__file__).resolve().parent
    require_ok(isinstance(cert_obj, dict), "CERT_NOT_OBJECT", "Certificate JSON must be an object")
    claimed_sha = cert_obj.get("payload_sha256")
    require_ok(is_hex64(claimed_sha), "CERT_BAD_PAYLOAD_HEX64", "Missing or malformed 64-hex payload_sha256")

    body = {k: v for k, v in cert_obj.items() if k != "payload_sha256"}
    recomputed_sha = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    require_ok(claimed_sha == recomputed_sha, "CERT_SELF_HASH_MISMATCH", "Certificate payload_sha256 self-hash mismatch")

    src_map = cert_obj.get("source_files_sha256")
    require_ok(isinstance(src_map, dict), "CERT_MISSING_SOURCE_MAP", "Missing source_files_sha256 map")
    require_ok(
        sorted(src_map.keys()) == sorted(BOUND_PACKAGE_FILES),
        "CERT_SOURCE_KEYS_MISMATCH",
        "source_files_sha256 keys do not match BOUND_PACKAGE_FILES",
    )
    snap = read_package_snapshot(base)
    live_hashes = compute_bound_source_hashes(base, snap=snap)
    for rel, digest in src_map.items():
        require_ok(is_hex64(digest), "CERT_BAD_FILE_HEX64", f"Malformed SHA-256 for {rel}")
        require_ok(digest == live_hashes[rel], "SOURCE_SHA256_MISMATCH", f"On-disk file {rel} drifted from certificate")

    lv_obj = cert_obj.get("lean_verification")
    require_ok(
        isinstance(lv_obj, dict) and lv_obj.get("live_lean_verified") is True,
        "CERT_NOT_LIVE_BUILT",
        "Committed certificate must attest live_lean_verified == true",
    )

    fresh = build_certificate(base, run_live_lean=run_live_lean, lean_runner=lean_runner)
    live_flag = bool(run_live_lean or lean_runner is not None)
    if live_flag:
        require_ok(
            canonical_json_bytes(cert_obj) == canonical_json_bytes(fresh),
            "CERTIFICATE_DRIFT",
            "Committed certificate drifted from freshly recomputed live-Lean witnesses",
        )
    else:
        cert_static = {k: v for k, v in cert_obj.items() if k not in ("payload_sha256", "lean_verification")}
        fresh_static = {k: v for k, v in fresh.items() if k not in ("payload_sha256", "lean_verification")}
        cert_lv_static = {k: v for k, v in lv_obj.items() if k != "live_lean_verified"}
        fresh_lv_static = {k: v for k, v in fresh["lean_verification"].items() if k != "live_lean_verified"}
        require_ok(
            canonical_json_bytes(cert_static) == canonical_json_bytes(fresh_static)
            and canonical_json_bytes(cert_lv_static) == canonical_json_bytes(fresh_lv_static),
            "CERTIFICATE_DRIFT",
            "Committed certificate drifted from freshly recomputed static and pure-Q witnesses",
        )
    return {
        "status": "PASS",
        "module": "S150Pilot1Theorems",
        "lean_live_replayed": live_flag,
        "verification_mode": "live_lean_kernel_and_pure_q" if live_flag else "offline_static_and_pure_q",
        "public_theorems_verified": fresh["lean_verification"]["public_theorems_audited"],
        "payload_sha256": cert_obj["payload_sha256"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="S150Pilot1Theorems Pure-Q + Lean 4.36.0 Self-Bound Certificate Verifier.")
    parser.add_argument("--live-lean", action="store_true", help="Run cold lake build + leanchecker --fresh + AxiomAudit.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true", help="Emit freshly computed certificate JSON to stdout.")
    mode.add_argument("--check", nargs="?", const="", default=None, help="Verify committed certificate JSON on disk.")
    mode.add_argument("--write-cert", nargs="?", const="", default=None, help="Write certificate JSON (requires --live-lean).")
    args = parser.parse_args(argv)

    base = Path(__file__).resolve().parent
    default_cert = Path(base, "s150_lean_theorems_certificate.json")

    try:
        refuse_symlink_path(Path(__file__))
        if args.check is not None:
            cpath = Path(args.check) if args.check else default_cert
            raw_bytes = read_regular_file_bytes(cpath, missing_code="MISSING_CERT_FILE")
            cert_data = loads_strict_json_bytes(raw_bytes, cpath.name)
            res = validate_certificate(cert_data, pkg_dir=base, run_live_lean=args.live_lean)
            expected_bytes = (json.dumps(cert_data, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")
            require_ok(raw_bytes == expected_bytes, "CERT_RAW_FORMAT_DRIFT", "Certificate raw file bytes are non-canonical")
            sys.stdout.write(json.dumps(res, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
            return 0

        if args.write_cert is not None:
            require_ok(
                args.live_lean,
                "WRITE_CERT_REQUIRES_LIVE_LEAN",
                "--write-cert requires --live-lean so committed certificates always reflect a live kernel replay",
            )
            out_path = Path(args.write_cert) if args.write_cert else default_cert
            refuse_symlink_path(out_path)
            cert = build_certificate(pkg_dir=base, run_live_lean=True)
            rendered = json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
            out_path.write_text(rendered, encoding="utf-8")
            sys.stdout.write(rendered)
            return 0

        cert = build_certificate(pkg_dir=base, run_live_lean=args.live_lean)
        sys.stdout.write(json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
        return 0
    except S150LeanVerifyError as exc:
        sys.stderr.write(json.dumps({"error_code": exc.code, "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2
    except OSError as exc:
        sys.stderr.write(json.dumps({"error_code": "IO_ERROR", "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
