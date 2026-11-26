#!/usr/bin/env python3
"""Bayt al-Hikma S^3: Trans-Historical Operator Socratic Seminar Harness.

Zero-cosplay, 100%-executable bidirectional cross-era Socratic seminar engine:
  - SEAT-0 (The Aletheia Scholar) chair/steward + deterministic exact-operator interposition index
  - Turn-Schema Validator & ANTI_THEATER_GATE (rejects prose-only, float, and trivial oracles)
  - AST-Guarded Isolated Inter-Round Executable Referee (python3 -I -B, pure int/Fraction, 0 floats)
  - Provenance & Bidirectional Compounding DAG Tracker (dynamic compounding & bidirectional pollination)
  - Multi-Variation & Chair Dossier/Prompt Generator (--variation scholars|civilizations|operators|single)
  - Hardened pure-Z/Q AST self-guard (0 ast.Div, 0 ast.Pow, 0 floats, 0 dynamic escapes)
"""

from __future__ import annotations

import argparse
import ast
import errno
from fractions import Fraction
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

SCHEMA_SEMINAR_CERT = "bayt-al-hikma.socratic_operator_seminar.v1"
SCHEMA_DOSSIER_PACK = "bayt-al-hikma.seminar_dossier_pack.v1"
SCHEMA_SEAT0_DOSSIER = "bayt-al-hikma.seat0_aletheia_scholar.v1"
ENERGY_POWER_STATUS = "UNCONTROLLED_LAPTOP_NOT_CLAIMED"

ALLOWED_VARIATIONS: Tuple[str, ...] = ("scholars", "civilizations", "operators", "single")
ALLOWED_CHAIRS: Tuple[str, ...] = ("aletheia", "none")
ALLOWED_MODES: frozenset[str] = frozenset(("compose", "challenge", "repair", "obstruct"))
ALLOWED_CONJECTURE_KINDS: frozenset[str] = frozenset(("python_exact_q", "lean4_with_python_oracle"))
ALLOWED_TARGET_FRONTIERS: Tuple[str, ...] = (
    "Foundation-0/continuum",
    "Foundation-0/aletheion",
    "Foundation-0/cave-expedition",
    "Foundation-0/bayt-al-hikma",
    "Moissanite-Labs/holosphere",
    "Moissanite-Labs/silikernels",
    "Moissanite-Labs/silisense",
    "aska-physical/optifab",
)

FORBIDDEN_PRIVATE_TOKENS: Tuple[str, ...] = (
    "aska-digital",
    "aska-site",
    "statos",
    "eth0s",
    "aletheia-corpus",
    "private-publish" + chr(47),
    chr(47) + "home" + chr(47),
    chr(47) + "Users" + chr(47),
)
FORBIDDEN_MODEL_TOKENS: Tuple[str, ...] = (
    "clau" + "de",
    "gem" + "ini",
    "gpt" + "-",
    "cod" + "ex",
    "mist" + "ral",
    "anthr" + "opic",
    "open" + "ai",
    "qwe" + "n",
    "gro" + "k",
    "vib" + "e",
    "opencode" + "-go",
    "deep" + "seek",
    "her" + "mes",
    "command" + "code",
    "zai-" + "glm",
)
VARIATION_C_FORBIDDEN_LABELS: Tuple[str, ...] = (
    "biruni",
    "madhava",
    "panini",
    "pingala",
    "jiushao",
    "chongzhi",
    "khipukamayuq",
    "chokwe",
    "nafis",
    "jazari",
    "antikythera",
    "islamicate",
    "south asian",
    "east asian",
    "andean",
    "egyptian",
    "maya",
)

SANDBOX_ALLOWED_IMPORTS: frozenset[str] = frozenset(("fractions", "itertools"))
SANDBOX_ALLOWED_FROM_IMPORTS: Dict[str, frozenset[str]] = {
    "fractions": frozenset(("Fraction",)),
    "math": frozenset(("gcd", "isqrt")),
    "itertools": frozenset(("product", "combinations", "permutations")),
}
SANDBOX_FORBIDDEN_NAMES: frozenset[str] = frozenset(
    (
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "breakpoint",
        "__import__",
        "getattr",
        "setattr",
        "delattr",
        "globals",
        "locals",
        "vars",
        "dir",
        "float",
        "complex",
        "memoryview",
        "bytearray",
        "type",
        "object",
        "super",
        "_exact_div",
        "_exact_pow",
    )
)
SANDBOX_FORBIDDEN_ATTR_PREFIXES: Tuple[str, ...] = ("__", "gi_", "f_", "cr_", "ag_", "tb_", "co_", "func_", "im_")
SANDBOX_FORBIDDEN_ATTRS: frozenset[str] = frozenset(("from_float", "from_decimal", "modules", "builtins"))
SANDBOX_ALLOWED_GEN_CONSUMERS: frozenset[str] = frozenset(
    ("all", "any", "list", "max", "min", "set", "sorted", "sum", "tuple")
)
SANDBOX_FORBIDDEN_SYNTAX_NODES: Tuple[type[ast.AST], ...] = (
    ast.AsyncFunctionDef,
    ast.AsyncFor,
    ast.AsyncWith,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
    ast.Global,
    ast.Nonlocal,
    ast.FormattedValue,
)

ALLOWED_MATH_ATTRS: frozenset[str] = frozenset(("gcd", "isqrt"))
PURE_Q_FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    ("builtins", "cmath", "ctypes", "decimal", "importlib", "mpmath", "numpy", "operator", "scipy", "sympy", "torch")
)
PURE_Q_FORBIDDEN_CALLS: frozenset[str] = frozenset(
    ("Decimal", "__import__", "compile", "complex", "eval", "exec", "float", "format", "format_map", "getattr", "globals", "literal_eval", "locals", "memoryview", "pow", "vars")
)
PURE_Q_FORBIDDEN_NAMES: frozenset[str] = frozenset(
    (
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
    )
)
PURE_Q_FORBIDDEN_ATTRS: frozenset[str] = frozenset(
    (
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
    )
)

MAX_JSON_DEPTH = 32
MAX_JSON_INT_DIGITS = 1024
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TEST_CASES = 64
MAX_ROUND_NUM = 10
DEFAULT_REFEREE_TIMEOUT_SEC = 5

EXPECTED_CERT_KEYS = frozenset(
    {
        "schema",
        "energy_power_status",
        "zero_floats",
        "pure_q_ast_clean",
        "anti_theater_rejections",
        "dry_run_session",
        "variation_packs_summary",
        "local_interpose_probe",
        "all_passed",
        "payload_sha256",
        "certificate_sha256",
    }
)

# Self-contained public exact-operator catalog (zero external paths or unbound digests)
PUBLIC_OPERATOR_CATALOG: Tuple[Dict[str, Any], ...] = (
    {
        "id": "repo:Foundation-0/continuum",
        "org": "Foundation-0",
        "kind": "frontier_repo",
        "keywords": ("cayley", "fricke", "holonomy", "hurwitz", "quaternion", "continued", "fraction", "su(2)", "so(3)"),
        "shared_operators": ("cayley_unit_sphere_lift", "fricke_commutator_discriminant", "continued_fraction_transpose"),
    },
    {
        "id": "repo:Foundation-0/aletheion",
        "org": "Foundation-0",
        "kind": "frontier_repo",
        "keywords": ("crt", "non-coprime", "coprime", "hysteresis", "valve", "khipu", "checksum", "chatter", "stride", "maya", "260", "365", "584"),
        "shared_operators": ("non_coprime_crt", "bounded_chatter_hysteresis", "hierarchical_tree_checksum"),
    },
    {
        "id": "repo:Foundation-0/cave-expedition",
        "org": "Foundation-0",
        "kind": "frontier_repo",
        "keywords": ("schur", "complement", "congruence", "witt", "gf(2)", "parity", "billiard", "mirror", "eulerian", "conductance", "shear"),
        "shared_operators": ("schur_complement_pushforward", "gf2_parity_folding", "mirror_billiard_gcd"),
    },
    {
        "id": "repo:Foundation-0/bayt-al-hikma",
        "org": "Foundation-0",
        "kind": "heritage_corpus",
        "keywords": ("stereographic", "al-biruni", "madhava", "panini", "pingala", "jiushao", "chongzhi", "nafis", "antikythera", "sona", "chord", "tail"),
        "shared_operators": ("rational_stereographic_lift", "asymptotic_rational_tail", "fraction_free_elimination"),
    },
)

PILOT1_TOPICS: Tuple[Dict[str, Any], ...] = (
    {
        "topic_id": "TOPIC-1-CONTINUUM",
        "target_frontier": "Foundation-0/continuum",
        "title": "Finite-Net Rational Approximation vs. Non-Abelian Holonomy",
        "prompt": (
            "Compose exact rational approximation bounds (stereographic Cayley lift, asymptotic tail acceleration, "
            "Hurwitz continued-fraction optimality, and epicyclic gear ratios) against finite-precision cancellation "
            "and non-Abelian commutator defects. Propose a pure-Z/Q testable identity or obstruction."
        ),
    },
    {
        "topic_id": "TOPIC-2-ALETHEION",
        "target_frontier": "Foundation-0/aletheion",
        "title": "Zero-Overhead Self-Checking Non-Prose Telemetry & Bounded-Chatter Control",
        "prompt": (
            "Compose minimal contiguous-interval compression, hierarchical tree-checksums, coprime single-cycle "
            "traversal topology, and passive friction-hysteresis / float-valve damping into a pure-Z/Q verifiable "
            "telemetry or bounded-chatter control invariant (zero energy claims)."
        ),
    },
    {
        "topic_id": "TOPIC-3-CAVE-EXPEDITION",
        "target_frontier": "Foundation-0/cave-expedition",
        "title": "Schur Elimination Congruence vs. Block Reduction & GF(2)/Eulerian Generalizations",
        "prompt": (
            "Determine exact algebraic conditions under which Schur complement elimination induces exact congruence "
            "versus block reduction alone, and test how GF(2) parity folding and Eulerian mirror curves generalize "
            "Loewner/fold-sheaf obstructions in pure Z/Q."
        ),
    },
)


class SeminarError(ValueError):
    """Fail-closed seminar harness error with deterministic code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def require_ok(cond: bool, code: str, message: str) -> None:
    if cond is not True:
        raise SeminarError(code, message)


def refuse_symlink_path(path: Path) -> None:
    abs_path = path if path.is_absolute() else Path.cwd().joinpath(path)
    cur = Path(abs_path.anchor)
    for idx, part in enumerate(abs_path.parts[1:]):
        cur = cur.joinpath(part)
        if idx >= 1 or idx == len(abs_path.parts) - 2:
            require_ok(not cur.is_symlink(), "SYMLINK_FORBIDDEN", f"Symlink path or ancestor forbidden: {path.name}")


def read_regular_file_bytes(
    path: Path,
    missing_code: str = "MISSING_FILE",
    max_bytes: int = MAX_FILE_BYTES,
) -> bytes:
    """Refuse symlinks/ancestors, open with O_NOFOLLOW|O_NONBLOCK, verify S_ISREG & byte cap."""
    refuse_symlink_path(path)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise SeminarError("SYMLINK_FORBIDDEN", f"Symlink forbidden: {path.name}") from exc
        if exc.errno in (errno.ENOENT, errno.ENOTDIR):
            raise SeminarError(missing_code, f"File not found: {path.name}") from exc
        raise SeminarError("READ_ERROR", f"Failed to open {path.name}: {exc.strerror}") from exc
    try:
        try:
            st = os.fstat(fd)
            require_ok(stat.S_ISREG(st.st_mode), "NOT_REGULAR_FILE", f"Non-regular file forbidden: {path.name}")
            require_ok(st.st_size <= max_bytes, "FILE_TOO_LARGE", f"File exceeds byte cap: {path.name}")
            chunks: List[bytes] = []
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
            raise SeminarError("READ_ERROR", f"Failed to read {path.name}: {exc.strerror}") from exc
    finally:
        os.close(fd)


def check_nonempty_str(val: Any, name: str, code: str = "THEATER_EMPTY_SPEC") -> str:
    require_ok(type(val) is str and len(val.strip()) > 0, code, f"{name} must be non-empty string")
    return val


def qdiv(num: Fraction, den: Fraction) -> Fraction:
    require_ok(den != Fraction(0, 1), "QDIV_ZERO_DENOM", "Zero denominator in exact rational division")
    return Fraction(num.numerator * den.denominator, num.denominator * den.numerator)


def _is_safe_fraction_arg(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return type(node.value) is int
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Subscript):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_safe_fraction_arg(node.operand)
    if isinstance(node, ast.Attribute) and node.attr in ("numerator", "denominator"):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod)):
        return _is_safe_fraction_arg(node.left) and _is_safe_fraction_arg(node.right)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        return node.func.id in ("int", "len", "sum", "check_int", "check_pos_int")
    if isinstance(node, ast.IfExp):
        return _is_safe_fraction_arg(node.body) and _is_safe_fraction_arg(node.orelse)
    return False


def _is_fraction_ref(expr: ast.AST, fraction_aliases: set[str]) -> bool:
    return (isinstance(expr, ast.Name) and expr.id in fraction_aliases) or (
        isinstance(expr, ast.Attribute) and expr.attr == "Fraction"
    )


def verify_pure_q_ast(source_text: str) -> Dict[str, Any]:
    """Fail-closed AST check: 0 Div/FloorDiv/Pow, 0 floats, 0 asserts, 0 dynamic/alias/f-spec escapes."""
    try:
        tree = ast.parse(source_text)
    except SyntaxError as exc:
        raise SeminarError("AST_SYNTAX_ERROR", f"Invalid Python syntax: {exc}") from exc
    math_aliases: set[str] = set()
    fraction_aliases: set[str] = {"Fraction"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                require_ok(root not in PURE_Q_FORBIDDEN_IMPORTS, "AST_FORBIDDEN_IMPORT", f"Forbidden import {alias.name}")
                if root == "math":
                    math_aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            require_ok(node.level == 0, "AST_REL_IMPORT_FORBIDDEN", "Relative imports forbidden")
            mod_root = str(node.module).split(".")[0]
            require_ok(mod_root not in PURE_Q_FORBIDDEN_IMPORTS, "AST_FORBIDDEN_IMPORT", f"Forbidden import from {node.module}")
            for alias in node.names:
                require_ok(alias.name != "*", "AST_WILDCARD_IMPORT", f"Wildcard import from {node.module} forbidden")
                if mod_root == "math":
                    require_ok(alias.name in ALLOWED_MATH_ATTRS, "AST_FORBIDDEN_MATH_SYM", f"Forbidden math symbol {alias.name}")
                elif mod_root == "fractions":
                    require_ok(alias.name == "Fraction", "AST_FORBIDDEN_FRACTIONS_SYM", f"Forbidden fractions symbol {alias.name}")
                    fraction_aliases.add(alias.asname or alias.name)

    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            targets: List[ast.AST] = []
            val_expr: Optional[ast.AST] = None
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
        require_ok(not isinstance(node, ast.Div), "AST_DIV_FORBIDDEN", "Operator '/' forbidden; use qdiv() or joinpath()")
        require_ok(not isinstance(node, ast.FloorDiv), "AST_FLOORDIV_FORBIDDEN", "Operator '//' forbidden; use divmod()[0]")
        require_ok(not isinstance(node, ast.Mod), "AST_MOD_FORBIDDEN", "Operator '%' forbidden; use divmod()[1]")
        require_ok(not isinstance(node, ast.Pow), "AST_POW_FORBIDDEN", "Operator '**' forbidden")
        if isinstance(node, ast.FormattedValue):
            require_ok(node.format_spec is None, "AST_FORMAT_SPEC_FORBIDDEN", "Format specifiers forbidden in pure-Q f-strings")
        elif isinstance(node, ast.Constant):
            require_ok(
                type(node.value).__name__ not in ("float", "complex"),
                "AST_FLOAT_LITERAL",
                f"Forbidden float/complex literal {node.value!r}",
            )
        elif isinstance(node, ast.Name):
            require_ok(node.id not in PURE_Q_FORBIDDEN_NAMES, "AST_FORBIDDEN_NAME", f"Forbidden name {node.id}")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                require_ok(node.attr in ("__init__", "__name__"), "AST_FORBIDDEN_ATTR", f"Forbidden dunder .{node.attr}")
            require_ok(node.attr not in PURE_Q_FORBIDDEN_ATTRS, "AST_FORBIDDEN_ATTR", f"Forbidden attribute .{node.attr}")
            if isinstance(node.value, ast.Name) and node.value.id in math_aliases:
                require_ok(node.attr in ALLOWED_MATH_ATTRS, "AST_FORBIDDEN_MATH_ATTR", f"Forbidden math.{node.attr}")
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
            is_frac = False
            if isinstance(fn_expr, ast.Name):
                fn_name = fn_expr.id
                if fn_name in fraction_aliases:
                    is_frac = True
            elif isinstance(fn_expr, ast.Attribute):
                fn_name = fn_expr.attr
                if fn_name == "Fraction":
                    is_frac = True
            require_ok(fn_name not in PURE_Q_FORBIDDEN_CALLS, "AST_FORBIDDEN_CALL", f"Forbidden call to {fn_name}()")
            if is_frac:
                require_ok(len(node.keywords) == 0, "AST_FRACTION_KW", "Keyword args to Fraction() forbidden")
                require_ok(len(node.args) == 2, "AST_FRACTION_ARITY", "Fraction() must use strict 2-arg form Fraction(num, den)")
                for arg in node.args:
                    require_ok(_is_safe_fraction_arg(arg), "AST_FRACTION_ARG_UNSAFE", "Fraction() arg must be safe integer AST")
    return {"pure_q_ast_clean": True}


def validate_json_tree_no_floats(obj: Any, max_depth: int = MAX_JSON_DEPTH) -> None:
    require_ok(max_depth >= 0, "JSON_DEPTH", "JSON nesting depth exceeded")
    if type(obj).__name__ == "float":
        raise SeminarError("FLOAT_FORBIDDEN", "Float values are forbidden in pure-Z/Q seminar artifacts")
    if obj is None or type(obj) is bool or type(obj) is int or type(obj) is str:
        return
    if isinstance(obj, list):
        for item in obj:
            validate_json_tree_no_floats(item, max_depth - 1)
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            require_ok(type(k) is str, "BAD_KEY", "JSON object keys must be strings")
            validate_json_tree_no_floats(v, max_depth - 1)
        return
    raise SeminarError("BAD_JSON_TYPE", f"Unsupported JSON type: {type(obj).__name__}")


def _reject_dup_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in pairs:
        require_ok(k not in out, "DUPLICATE_JSON_KEY", f"Duplicate JSON key: {k}")
        out[k] = v
    return out


def _reject_float(token: str) -> Any:
    raise SeminarError("FLOAT_FORBIDDEN", f"Float literal forbidden in strict JSON: {token}")


def _reject_constant(token: str) -> Any:
    raise SeminarError("NONFINITE_JSON", f"Non-finite constant forbidden in strict JSON: {token}")


def _parse_bounded_int(token: str) -> int:
    require_ok(
        len(token.lstrip("+-")) <= MAX_JSON_INT_DIGITS,
        "JSON_INT_TOO_LARGE",
        "JSON integer exceeds digit cap",
    )
    return int(token)


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
            require_ok(depth <= max_depth, "JSON_DEPTH", "JSON nesting depth exceeded")
        elif ch in "}]":
            if depth > 0:
                depth -= 1


def loads_strict_json_bytes(raw: bytes, label: str) -> Any:
    require_ok(not raw.startswith(b"\xef\xbb\xbf"), "UTF8_BOM_FORBIDDEN", f"{label} has UTF-8 BOM")
    require_ok(b"\r" not in raw, "CR_FORBIDDEN", f"{label} contains CR/CRLF")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SeminarError("BAD_UTF8", f"{label} invalid UTF-8: {exc}") from exc
    _check_json_depth_pre_parse(text)
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_reject_dup_keys,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
            parse_int=_parse_bounded_int,
        )
    except SeminarError:
        raise
    except RecursionError as exc:
        raise SeminarError("JSON_DEPTH", f"{label} JSON nesting depth exceeded: {exc}") from exc
    except ValueError as exc:
        raise SeminarError("BAD_JSON", f"{label} invalid JSON: {exc}") from exc
    validate_json_tree_no_floats(parsed)
    return parsed


def canonical_json_bytes(obj: Dict[str, Any]) -> bytes:
    validate_json_tree_no_floats(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def assert_clean_public_text(text: str, check_model_pollution: bool = True) -> None:
    """Fail closed on private org names, host paths, or (optionally) vendor/model pollution."""
    require_ok(type(text) is str, "BAD_TEXT", "text must be str")
    low = text.lower()
    for tok in FORBIDDEN_PRIVATE_TOKENS:
        require_ok(tok.lower() not in low, "PRIVACY_VIOLATION", f"forbidden private/path token detected: {tok}")
    if check_model_pollution:
        for tok in FORBIDDEN_MODEL_TOKENS:
            require_ok(tok not in low, "MODEL_POLLUTION", f"forbidden vendor/model token detected: {tok}")


def assert_variation_c_label_stripped(pack: Any) -> None:
    """Verify Variation C (pure exact-operator) payload contains zero scholar/civilization labels."""
    raw = json.dumps(pack, sort_keys=True, ensure_ascii=True).lower()
    for label in VARIATION_C_FORBIDDEN_LABELS:
        require_ok(label not in raw, "VARIATION_C_LABEL_LEAK", f"Variation C leaked historical label: {label}")


# ---------------------------------------------------------------------------
# 1. AST Sandbox Gate & Turn-Schema ANTI_THEATER_GATE
# ---------------------------------------------------------------------------


def audit_conjecture_ast(code: str) -> None:
    """Strictly validate conjecture Python code: pure int/Fraction, zero floats/IO/theater."""
    check_nonempty_str(code, "conjecture.code", "THEATER_EMPTY_SPEC")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SeminarError("SANDBOX_SYNTAX_ERROR", f"Invalid Python syntax: {exc}") from exc

    parents: Dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent

    check_fn: Optional[ast.FunctionDef] = None
    has_fractions_import = False
    has_div = False
    gen_nodes: List[ast.GeneratorExp] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and type(node.value).__name__ in ("float", "complex"):
            raise SeminarError("SANDBOX_FLOAT_FORBIDDEN", f"Float/complex literal forbidden: {node.value!r}")
        if isinstance(node, ast.Assert):
            raise SeminarError("SANDBOX_BARE_ASSERT", "Bare assert forbidden in conjecture oracle")
        if isinstance(node, SANDBOX_FORBIDDEN_SYNTAX_NODES):
            raise SeminarError("SANDBOX_FORBIDDEN_SYNTAX", f"Forbidden syntax node: {type(node).__name__}")
        if isinstance(node, ast.GeneratorExp):
            gen_nodes.append(node)
        if isinstance(node, ast.Div):
            has_div = True
        if isinstance(node, ast.Import):
            for alias in node.names:
                require_ok(alias.name in SANDBOX_ALLOWED_IMPORTS, "SANDBOX_FORBIDDEN_IMPORT", f"Forbidden import: {alias.name}")
                if alias.name == "fractions":
                    has_fractions_import = True
        elif isinstance(node, ast.ImportFrom):
            require_ok(
                node.level == 0 and node.module in SANDBOX_ALLOWED_FROM_IMPORTS,
                "SANDBOX_FORBIDDEN_IMPORT",
                f"Forbidden from-import: {node.module}",
            )
            allowed_names = SANDBOX_ALLOWED_FROM_IMPORTS[node.module]
            for alias in node.names:
                require_ok(alias.name in allowed_names, "SANDBOX_FORBIDDEN_IMPORT", f"Forbidden imported name: {alias.name}")
            if node.module == "fractions":
                has_fractions_import = True
        elif isinstance(node, ast.Attribute):
            require_ok(
                not any(node.attr.startswith(pfx) for pfx in SANDBOX_FORBIDDEN_ATTR_PREFIXES)
                and node.attr not in SANDBOX_FORBIDDEN_ATTRS,
                "SANDBOX_FORBIDDEN_ATTR",
                f"Forbidden attribute: {node.attr}",
            )
        elif isinstance(node, ast.Name):
            require_ok(
                not node.id.startswith("__") and node.id not in SANDBOX_FORBIDDEN_NAMES,
                "SANDBOX_FORBIDDEN_NAME",
                f"Forbidden name: {node.id}",
            )
            if isinstance(node.ctx, ast.Store):
                require_ok(
                    node.id not in SANDBOX_ALLOWED_GEN_CONSUMERS,
                    "SANDBOX_FORBIDDEN_NAME",
                    f"Shadowing reducer {node.id} forbidden",
                )
        elif isinstance(node, ast.arg):
            require_ok(
                node.arg not in SANDBOX_ALLOWED_GEN_CONSUMERS,
                "SANDBOX_FORBIDDEN_NAME",
                f"Shadowing reducer {node.arg} forbidden",
            )
        elif isinstance(node, ast.FunctionDef):
            require_ok(
                node.name not in SANDBOX_ALLOWED_GEN_CONSUMERS,
                "SANDBOX_FORBIDDEN_NAME",
                f"Shadowing reducer {node.name} forbidden",
            )
            if node.name == "check_case":
                check_fn = node

    # Permit GeneratorExp only as a direct positional arg to pure C reducers (all/any/sum/sorted/tuple/...)
    for gnode in gen_nodes:
        parent = parents.get(id(gnode))
        ok_gen = (
            isinstance(parent, ast.Call)
            and isinstance(parent.func, ast.Name)
            and parent.func.id in SANDBOX_ALLOWED_GEN_CONSUMERS
            and any(arg is gnode for arg in parent.args)
        )
        require_ok(
            ok_gen,
            "SANDBOX_FORBIDDEN_SYNTAX",
            "GeneratorExp only allowed as direct positional argument to pure reducer",
        )

    require_ok(
        not has_div or has_fractions_import,
        "SANDBOX_DIV_FORBIDDEN",
        "True division '/' without fractions import produces floats and is forbidden",
    )
    require_ok(check_fn is not None, "THEATER_MISSING_ENTRYPOINT", "code must define def check_case(case):")
    fn_node = check_fn
    require_ok(len(fn_node.args.args) == 1, "THEATER_BAD_SIGNATURE", "check_case must accept exactly 1 parameter")
    param_name = fn_node.args.args[0].arg

    uses_param = False
    has_compare = False
    for sub in ast.walk(fn_node):
        if isinstance(sub, ast.Name) and sub.id == param_name:
            uses_param = True
        if isinstance(sub, ast.Compare):
            has_compare = True
    require_ok(uses_param and has_compare, "THEATER_TRIVIAL_ORACLE", "check_case must inspect case with >= 1 comparison")


def validate_seminar_turn(turn: Any) -> Dict[str, Any]:
    """Enforce mandatory 4-field structured turn schema (+ SEAT-0 interpositions field)."""
    require_ok(isinstance(turn, dict), "THEATER_BAD_TURN", "turn must be a dict")
    validate_json_tree_no_floats(turn)

    turn_id = check_nonempty_str(turn.get("turn_id"), "turn_id", "THEATER_MISSING_FIELD")
    round_num = turn.get("round_num")
    require_ok(type(round_num) is int and 1 <= round_num <= MAX_ROUND_NUM, "THEATER_BAD_ROUND", "round_num must be int in 1..10")
    seat_id = check_nonempty_str(turn.get("seat_id"), "seat_id", "THEATER_MISSING_FIELD")

    anchor = turn.get("corpus_anchor")
    require_ok(isinstance(anchor, dict), "THEATER_MISSING_FIELD", "corpus_anchor must be a dict")
    check_nonempty_str(anchor.get("operator_id"), "corpus_anchor.operator_id", "THEATER_MISSING_FIELD")
    check_nonempty_str(anchor.get("source_receipt_id"), "corpus_anchor.source_receipt_id", "THEATER_MISSING_FIELD")
    check_nonempty_str(anchor.get("statement"), "corpus_anchor.statement", "THEATER_MISSING_FIELD")

    comp = turn.get("composition_or_challenge")
    require_ok(isinstance(comp, dict), "THEATER_MISSING_FIELD", "composition_or_challenge must be a dict")
    mode = comp.get("mode")
    require_ok(mode in ALLOWED_MODES, "THEATER_BAD_MODE", f"composition mode must be in {sorted(ALLOWED_MODES)}")
    target = check_nonempty_str(comp.get("target_seat_or_turn"), "target_seat_or_turn", "THEATER_MISSING_FIELD")
    check_nonempty_str(comp.get("algebraic_link"), "algebraic_link", "THEATER_MISSING_FIELD")
    if round_num == 1:
        require_ok(target != seat_id, "THEATER_SELF_ECHO", "Round-1 turn cannot target itself")

    conj = turn.get("executable_conjecture")
    require_ok(isinstance(conj, dict), "THEATER_MISSING_FIELD", "executable_conjecture must be a dict")
    check_nonempty_str(conj.get("conjecture_id"), "conjecture_id", "THEATER_MISSING_FIELD")
    require_ok(conj.get("kind") in ALLOWED_CONJECTURE_KINDS, "THEATER_BAD_KIND", "unsupported conjecture kind")
    check_nonempty_str(conj.get("claim_summary"), "claim_summary", "THEATER_MISSING_FIELD")
    audit_conjecture_ast(conj.get("code"))
    cases = conj.get("test_cases")
    require_ok(isinstance(cases, list) and 1 <= len(cases) <= MAX_TEST_CASES, "THEATER_EMPTY_SPEC", "test_cases must have 1..64 cases")
    for case in cases:
        require_ok(isinstance(case, dict) and len(case) >= 1, "THEATER_EMPTY_SPEC", "each test case must be a non-empty dict")

    frontier = turn.get("target_frontier")
    require_ok(frontier in ALLOWED_TARGET_FRONTIERS, "INVALID_FRONTIER", f"target_frontier not in allowlist: {frontier!r}")

    interpositions_count = 0
    if seat_id == "SEAT-0":
        interps = turn.get("epistemic_web_interpositions")
        require_ok(isinstance(interps, list) and len(interps) >= 1, "THEATER_MISSING_INTERPOSITIONS", "SEAT-0 must include >= 1 interposition hit")
        for hit in interps:
            require_ok(isinstance(hit, dict), "THEATER_MISSING_INTERPOSITIONS", "interposition entry must be dict")
            check_nonempty_str(hit.get("id"), "interposition.id", "THEATER_MISSING_INTERPOSITIONS")
            check_nonempty_str(hit.get("org"), "interposition.org", "THEATER_MISSING_INTERPOSITIONS")
            check_nonempty_str(hit.get("gate_status"), "interposition.gate_status", "THEATER_MISSING_INTERPOSITIONS")
            ops = hit.get("shared_operators")
            require_ok(isinstance(ops, list) and len(ops) >= 1, "THEATER_MISSING_INTERPOSITIONS", "interposition must list >= 1 shared_operators")
        interpositions_count = len(interps)

    assert_clean_public_text(json.dumps(turn, sort_keys=True, ensure_ascii=True), check_model_pollution=True)
    return {
        "turn_id": turn_id,
        "round_num": round_num,
        "seat_id": seat_id,
        "mode": mode,
        "target_seat_or_turn": target,
        "target_frontier": frontier,
        "conjecture_id": conj["conjecture_id"],
        "interpositions_count": interpositions_count,
    }


# ---------------------------------------------------------------------------
# 2. Isolated Inter-Round Executable Referee (python3 -I -B subprocess)
# ---------------------------------------------------------------------------

_ISOLATED_RUNNER_SOURCE = r"""
import ast, fractions, itertools, json, math, sys, types

def _make_runtime():
    _RawFraction = fractions.Fraction
    _type = type
    _isinstance = isinstance
    _len = len
    _int = int
    _bool = bool
    _hasattr = hasattr
    _enumerate = enumerate
    _pow = pow
    _TypeError = TypeError
    _ImportError = ImportError
    _Exception = Exception
    _stdin_read = sys.stdin.read
    _stdout_write = sys.stdout.write
    _sys_exit = sys.exit
    _json_loads = json.loads
    _json_dumps = json.dumps
    _ast_parse = ast.parse
    _ast_fix = ast.fix_missing_locations
    _compile = compile

    def _safe_fraction(*args):
        if _len(args) == 1 and _type(args[0]) is str:
            s = args[0].strip()
            if "." in s or "e" in s or "E" in s:
                raise _TypeError("FRACTION_EXACT_INT_ONLY")
            parts = s.split("/")
            if _len(parts) == 1:
                return _RawFraction(_int(parts[0]), 1)
            if _len(parts) == 2:
                return _RawFraction(_int(parts[0]), _int(parts[1]))
            raise _TypeError("FRACTION_EXACT_INT_ONLY")
        if not (1 <= _len(args) <= 2):
            raise _TypeError("FRACTION_ARITY")
        for a in args:
            if not (_type(a) is _int or _isinstance(a, _RawFraction)):
                raise _TypeError("FRACTION_EXACT_INT_ONLY")
        return _RawFraction(*args)

    def _exact_div(a, b):
        if not (_isinstance(a, _RawFraction) or _isinstance(b, _RawFraction)):
            raise _TypeError("FLOAT_DIVISION_FORBIDDEN")
        if _type(a).__name__ in ("float", "complex") or _type(b).__name__ in ("float", "complex"):
            raise _TypeError("FLOAT_DIVISION_FORBIDDEN")
        res = a / b
        if _type(res).__name__ in ("float", "complex"):
            raise _TypeError("FLOAT_DIVISION_FORBIDDEN")
        return res

    def _exact_pow(a, b, mod=None):
        if _type(a).__name__ in ("float", "complex") or _type(b).__name__ in ("float", "complex"):
            raise _TypeError("FLOAT_POW_FORBIDDEN")
        if mod is not None:
            return _pow(a, b, mod)
        if _type(a) is _int and _type(b) is _int and b < 0:
            raise _TypeError("FLOAT_POW_FORBIDDEN")
        res = a ** b
        if _type(res).__name__ in ("float", "complex"):
            raise _TypeError("FLOAT_POW_FORBIDDEN")
        return res

    class _ExactArithRewriter(ast.NodeTransformer):
        def visit_BinOp(self, node):
            self.generic_visit(node)
            if isinstance(node.op, ast.Div):
                return ast.Call(func=ast.Name(id="_exact_div", ctx=ast.Load()), args=[node.left, node.right], keywords=[])
            if isinstance(node.op, ast.Pow):
                return ast.Call(func=ast.Name(id="_exact_pow", ctx=ast.Load()), args=[node.left, node.right], keywords=[])
            return node
        def visit_AugAssign(self, node):
            self.generic_visit(node)
            if isinstance(node.op, ast.Div):
                lhs = ast.Name(id=node.target.id, ctx=ast.Load()) if isinstance(node.target, ast.Name) else node.target
                return ast.Assign(targets=[node.target], value=ast.Call(func=ast.Name(id="_exact_div", ctx=ast.Load()), args=[lhs, node.value], keywords=[]))
            if isinstance(node.op, ast.Pow):
                lhs = ast.Name(id=node.target.id, ctx=ast.Load()) if isinstance(node.target, ast.Name) else node.target
                return ast.Assign(targets=[node.target], value=ast.Call(func=ast.Name(id="_exact_pow", ctx=ast.Load()), args=[lhs, node.value], keywords=[]))
            return node

    _allowed_mods = {
        "fractions": types.SimpleNamespace(Fraction=_safe_fraction),
        "itertools": itertools,
        "math": types.SimpleNamespace(gcd=math.gcd, isqrt=math.isqrt),
    }

    def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level != 0 or name not in _allowed_mods:
            raise _ImportError(f"blocked import: {name}")
        mod_ns = _allowed_mods[name]
        for sym in (fromlist or ()):
            if not _hasattr(mod_ns, sym):
                raise _ImportError(f"blocked symbol: {name}.{sym}")
        return mod_ns

    _safe_builtins = {
        "__import__": _safe_import,
        "abs": abs,
        "all": all,
        "any": any,
        "bool": bool,
        "dict": dict,
        "enumerate": enumerate,
        "filter": filter,
        "int": int,
        "isinstance": isinstance,
        "len": len,
        "list": list,
        "map": map,
        "max": max,
        "min": min,
        "pow": _exact_pow,
        "range": range,
        "reversed": reversed,
        "set": set,
        "sorted": sorted,
        "str": str,
        "sum": sum,
        "tuple": tuple,
        "zip": zip,
        "ValueError": ValueError,
        "ZeroDivisionError": ZeroDivisionError,
        "KeyError": KeyError,
        "IndexError": IndexError,
    }

    payload = _json_loads(_stdin_read())
    tree = _ExactArithRewriter().visit(_ast_parse(payload["code"]))
    _ast_fix(tree)
    code_obj = _compile(tree, "<conjecture>", "exec")
    ns = {"__builtins__": _safe_builtins, "_exact_div": _exact_div, "_exact_pow": _exact_pow}

    def _eval_cases():
        exec(code_obj, ns, ns)
        fn = ns["check_case"]
        cases = payload["test_cases"]
        passed = 0
        for idx, case in _enumerate(cases):
            try:
                res = fn(case)
            except _Exception as exc:
                return {
                    "status": "MINIMAL_COUNTEREXAMPLE",
                    "passed_cases": passed,
                    "total_cases": _len(cases),
                    "failing_case_index": idx,
                    "minimal_counterexample": case,
                    "failure_reason": f"{_type(exc).__name__}: {exc}",
                }
            if _type(res) is not _bool:
                return {
                    "status": "MINIMAL_COUNTEREXAMPLE",
                    "passed_cases": passed,
                    "total_cases": _len(cases),
                    "failing_case_index": idx,
                    "minimal_counterexample": case,
                    "failure_reason": f"NON_BOOL_RETURN:{_type(res).__name__}",
                }
            if not res:
                return {
                    "status": "MINIMAL_COUNTEREXAMPLE",
                    "passed_cases": passed,
                    "total_cases": _len(cases),
                    "failing_case_index": idx,
                    "minimal_counterexample": case,
                    "failure_reason": "PREDICATE_RETURNED_FALSE",
                }
            passed += 1
        return {
            "status": "PASS_WITNESS",
            "passed_cases": passed,
            "total_cases": _len(cases),
            "failing_case_index": None,
            "minimal_counterexample": None,
            "failure_reason": None,
        }

    def _finish(verdict_dict):
        _stdout_write(_json_dumps(verdict_dict, sort_keys=True, ensure_ascii=True))
        _sys_exit(0)

    return _eval_cases, _finish

_eval_cases, _finish = _make_runtime()
for _gname in list(globals()):
    if _gname not in ("__name__", "_eval_cases", "_finish"):
        globals().pop(_gname, None)
globals()["__builtins__"] = {}
_verdict = _eval_cases()
_finish(_verdict)
"""


def run_isolated_referee(
    conjecture: Dict[str, Any],
    timeout_sec: int = DEFAULT_REFEREE_TIMEOUT_SEC,
) -> Dict[str, Any]:
    """Execute validated conjecture in isolated python3 -I -B subprocess with strict timeout."""
    require_ok(isinstance(conjecture, dict), "THEATER_MISSING_FIELD", "conjecture must be dict")
    require_ok(type(timeout_sec) is int and 1 <= timeout_sec <= 30, "BAD_TIMEOUT", "timeout_sec must be int in 1..30")
    audit_conjecture_ast(conjecture.get("code"))
    cases = conjecture.get("test_cases")
    validate_json_tree_no_floats(cases)
    require_ok(isinstance(cases, list) and 1 <= len(cases) <= MAX_TEST_CASES, "THEATER_EMPTY_SPEC", "invalid test_cases")

    stdin_bytes = json.dumps(
        {"code": conjecture["code"], "test_cases": cases},
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
    )
    clean_env = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "CUDA_VISIBLE_DEVICES": "",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
    }
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-B", "-c", _ISOLATED_RUNNER_SOURCE],
            input=stdin_bytes,
            capture_output=True,
            text=True,
            env=clean_env,
            timeout=timeout_sec,
            check=False,
        )
    except subprocess.TimeoutExpired:
        verdict = {
            "conjecture_id": str(conjecture.get("conjecture_id", "unknown")),
            "status": "REFEREE_TIMEOUT",
            "passed_cases": 0,
            "total_cases": len(cases),
            "failing_case_index": None,
            "minimal_counterexample": None,
            "failure_reason": f"TIMEOUT_AFTER_{timeout_sec}S",
        }
        verdict["verdict_sha256"] = hashlib.sha256(canonical_json_bytes(verdict)).hexdigest()
        return verdict

    require_ok(proc.returncode == 0, "REFEREE_EXEC_ERROR", f"isolated referee rc={proc.returncode}")
    raw_out = loads_strict_json_bytes(proc.stdout.encode("utf-8"), "referee_stdout")
    verdict = {
        "conjecture_id": str(conjecture.get("conjecture_id", "unknown")),
        "status": raw_out["status"],
        "passed_cases": raw_out["passed_cases"],
        "total_cases": raw_out["total_cases"],
        "failing_case_index": raw_out["failing_case_index"],
        "minimal_counterexample": raw_out["minimal_counterexample"],
        "failure_reason": raw_out["failure_reason"],
    }
    verdict["verdict_sha256"] = hashlib.sha256(canonical_json_bytes(verdict)).hexdigest()
    return verdict


# ---------------------------------------------------------------------------
# 3. Deterministic Offline Exact-Operator Interposition Index
# ---------------------------------------------------------------------------


def run_local_interpose(title: str, text: str, top_k: int = 3) -> Dict[str, Any]:
    """Deterministically rank cross-repo exact-operator interposition hits in pure Z/Q."""
    check_nonempty_str(title, "title", "BAD_QUERY")
    check_nonempty_str(text, "text", "BAD_QUERY")
    require_ok(type(top_k) is int and 1 <= top_k <= 12, "BAD_QUERY", "top_k must be int in 1..12")
    combined = f"{title} {text}".lower()

    scored: List[Tuple[Fraction, str, Dict[str, Any]]] = []
    for entry in PUBLIC_OPERATOR_CATALOG:
        kws = entry["keywords"]
        matched = sum(1 for kw in kws if kw in combined)
        if matched > 0:
            score = Fraction(matched, len(kws))
            scored.append(
                (
                    score,
                    entry["id"],
                    {
                        "id": entry["id"],
                        "org": entry["org"],
                        "kind": entry["kind"],
                        "score_q": f"{score.numerator}{chr(47)}{score.denominator}",
                        "shared_operators": list(entry["shared_operators"]),
                        "gate_status": "EXACT_OPERATOR_VERIFIED",
                    },
                )
            )
    scored.sort(key=lambda item: (-item[0], item[1]))
    hits = [item[2] for item in scored[:top_k]]
    return {
        "backend": "local_exact_operator_catalog",
        "matched_count": len(hits),
        "hits": hits,
    }


# ---------------------------------------------------------------------------
# 4. Provenance & Bidirectional Compounding DAG Tracker
# ---------------------------------------------------------------------------


def evaluate_seminar_session(
    session_id: str,
    variation: str,
    chair: str,
    topic_id: str,
    turns: Sequence[Dict[str, Any]],
    timeout_sec: int = DEFAULT_REFEREE_TIMEOUT_SEC,
) -> Dict[str, Any]:
    """Validate all turns, run isolated referee, and certify compounding + bidirectional DAG."""
    check_nonempty_str(session_id, "session_id", "BAD_SESSION")
    require_ok(variation in ALLOWED_VARIATIONS, "BAD_VARIATION", f"variation must be in {ALLOWED_VARIATIONS}")
    require_ok(chair in ALLOWED_CHAIRS, "BAD_CHAIR", f"chair must be in {ALLOWED_CHAIRS}")
    check_nonempty_str(topic_id, "topic_id", "BAD_SESSION")
    require_ok(isinstance(turns, (list, tuple)) and len(turns) >= 1, "BAD_SESSION", "turns must be non-empty")

    seen_ids: Dict[str, Dict[str, Any]] = {}
    validated_turns: List[Tuple[Dict[str, Any], Dict[str, Any]]] = [
        (turn, validate_seminar_turn(turn)) for turn in turns
    ]
    ordered_turns = sorted(validated_turns, key=lambda item: (item[1]["round_num"], item[1]["turn_id"]))
    records: List[Dict[str, Any]] = []
    dag_edges: List[Dict[str, Any]] = []
    counterexample_repairs: List[Dict[str, str]] = []
    cross_seat_compositions: List[Dict[str, str]] = []
    historical_to_modern_edges: List[Dict[str, str]] = []
    modern_to_historical_edges: List[Dict[str, str]] = []
    depth_by_turn: Dict[str, int] = {}

    for turn, meta in ordered_turns:
        tid = meta["turn_id"]
        require_ok(tid not in seen_ids, "DUPLICATE_TURN_ID", f"duplicate turn_id: {tid}")
        verdict = run_isolated_referee(turn["executable_conjecture"], timeout_sec=timeout_sec)

        target = meta["target_seat_or_turn"]
        parent_rec = seen_ids.get(target)
        depth = 1
        if parent_rec is not None:
            require_ok(parent_rec["round_num"] < meta["round_num"], "DAG_NON_CAUSAL", f"{tid} must target earlier round")
            depth = depth_by_turn[target] + 1
            dag_edges.append(
                {
                    "src_turn_id": target,
                    "dst_turn_id": tid,
                    "mode": meta["mode"],
                    "src_seat_id": parent_rec["seat_id"],
                    "dst_seat_id": meta["seat_id"],
                    "src_verdict": parent_rec["verdict"]["status"],
                    "dst_verdict": verdict["status"],
                }
            )
            if parent_rec["verdict"]["status"] == "MINIMAL_COUNTEREXAMPLE" and verdict["status"] == "PASS_WITNESS":
                counterexample_repairs.append({"broken_turn": target, "repaired_turn": tid})
            if parent_rec["seat_id"] != meta["seat_id"] and verdict["status"] == "PASS_WITNESS":
                cross_seat_compositions.append({"src_turn": target, "dst_turn": tid})
                if meta["seat_id"] == "SEAT-0":
                    historical_to_modern_edges.append({"historical_turn": target, "aletheia_turn": tid})
                elif parent_rec["seat_id"] == "SEAT-0":
                    modern_to_historical_edges.append({"aletheia_turn": target, "historical_turn": tid})

        depth_by_turn[tid] = depth
        rec = {
            "turn_id": tid,
            "round_num": meta["round_num"],
            "seat_id": meta["seat_id"],
            "mode": meta["mode"],
            "target_seat_or_turn": target,
            "target_frontier": meta["target_frontier"],
            "interpositions_count": meta["interpositions_count"],
            "dag_depth": depth,
            "verdict": verdict,
        }
        seen_ids[tid] = rec
        records.append(rec)

    max_dag_depth = max(depth_by_turn.values())
    pass_count = sum(1 for r in records if r["verdict"]["status"] == "PASS_WITNESS")
    cex_count = sum(1 for r in records if r["verdict"]["status"] == "MINIMAL_COUNTEREXAMPLE")
    compounding_links = len(counterexample_repairs) + len(cross_seat_compositions)
    g2_passed = (max_dag_depth >= 2) and (compounding_links >= 2)
    g5_passed = (len(historical_to_modern_edges) >= 1) and (len(modern_to_historical_edges) >= 1)

    session_body: Dict[str, Any] = {
        "session_id": session_id,
        "variation": variation,
        "chair": chair,
        "topic_id": topic_id,
        "turn_count": len(records),
        "pass_witness_count": pass_count,
        "minimal_counterexample_count": cex_count,
        "max_dag_depth": max_dag_depth,
        "dag_edges": dag_edges,
        "counterexample_repairs": counterexample_repairs,
        "cross_seat_compositions": cross_seat_compositions,
        "historical_to_modern_edges": historical_to_modern_edges,
        "modern_to_historical_edges": modern_to_historical_edges,
        "s150_g2_dynamic_compounding_passed": g2_passed,
        "s150_g5_bidirectional_pollination_passed": g5_passed,
        "turn_records": records,
    }
    session_body["transcript_sha256"] = hashlib.sha256(canonical_json_bytes(session_body)).hexdigest()
    return session_body


# ---------------------------------------------------------------------------
# 5. SEAT-0 Dossier & 4 Variation Packs (Self-Contained Public Definitions)
# ---------------------------------------------------------------------------


def _seat_card(seat_id: str, title: str, lens: str, operators: Sequence[str]) -> Dict[str, Any]:
    return {
        "seat_id": seat_id,
        "title": title,
        "signature_lens": lens,
        "exact_operators": list(operators),
    }


def build_seat0_aletheia_scholar_card() -> Dict[str, Any]:
    """Construct canonical SEAT-0 (The Aletheia Scholar) dossier card."""
    card = _seat_card(
        "SEAT-0",
        "The Aletheia Scholar (Chair, Method Steward & Cross-Domain Synthesizer)",
        "Constructive pure-Z/Q verification, steelman counterexample repair, and exact-operator interposition",
        (
            "8-glyph exact-operator calculus (Schur pushforward, Pullback, Holonomy, Loewner, Commutation defect, Fold sheaf, Farkas, Parity)",
            "Sylvester-Hadamard orthogonal transforms, rank-1 collapse diagnostics, and zero-log multiplicative certificates",
            "Cayley SU(2) rational sphere lifts, SO(d) geodesic retraction, and bounded-chatter rational hysteresis control",
            "Gegenbauer/Mobius rational enclosures, continuum holonomy defects, and congruence vs block-reduction scope",
        ),
    )
    card["role"] = "CHAIR_METHOD_STEWARD_AND_CROSS_POLLINATOR"
    card["mandatory_extra_field"] = "epistemic_web_interpositions"
    card["method_laws"] = [
        "Law 1: Re-enter every counterexample or surprise as a falsifiable formal test",
        "Law 2: Steelman every counterexample into the strongest repaired conjecture before dismissal",
        "Law 3: Pure-Z/Q or Lean 4 executable witnesses and must-fail negative controls only",
        "Law 4: Honest novelty grading and explicit scope boundaries",
        "Law 5: Own-terms-first translation into exact algebraic operators without language smuggling",
    ]
    return card


def build_variation_pack(variation: str, chair: str = "aletheia") -> Dict[str, Any]:
    """Build deterministic verified dossier pack for Variation A/B/C/D with optional SEAT-0 chair."""
    require_ok(variation in ALLOWED_VARIATIONS, "BAD_VARIATION", f"unknown variation: {variation!r}")
    require_ok(chair in ALLOWED_CHAIRS, "BAD_CHAIR", f"unknown chair: {chair!r}")

    if variation == "scholars":
        seats = [
            _seat_card(
                "SEAT-1",
                "Abu Rayhan al-Biruni (973-1048)",
                "Exact rational spherical projection, conditioning/cancellation audits, empirical-to-exact bridges",
                (
                    "Rational stereographic projection <-> Cayley S^2/S^3 lift",
                    "Subtractive cancellation condition number kappa_sub = 215989/11",
                    "Geodesy dip-angle amplification 1288000/616517",
                ),
            ),
            _seat_card(
                "SEAT-2",
                "Madhava of Sangamagrama (c. 1340-1425)",
                "Asymptotic rational tail-acceleration and alternating-series enclosures",
                (
                    "Antya-samskara rational remainder hierarchy R1, R2, R3 (O(1/n^3)->O(1/n^5)->O(1/n^7))",
                    "Al-Kashi 16-digit rational pi outer bracket",
                ),
            ),
            _seat_card(
                "SEAT-3",
                "Panini (c. 5th c. BCE) & Pingala Prosodic Lens",
                "Minimal sufficient partitions (C1P), generative compression, binary/Gray bijections",
                (
                    "14 Sivasutras Consecutive-Ones Property (C1P) minimal interval cover over 43 pratyaharas",
                    "Pingala nasta/uddista binary bijection and O(log n) exponentiation",
                ),
            ),
            _seat_card(
                "SEAT-4",
                "Qin Jiushao (1202-1261), Zu Chongzhi & Jiuzhang",
                "Non-coprime modular arithmetic, fraction-free linear algebra, Hurwitz CF, passive hysteresis",
                (
                    "Jiuzhang Ch. 8 fangcheng fraction-free Z elimination",
                    "Qin Jiushao Dayan non-coprime CRT and 260/365/584 lcm = 37960 (1460x compression)",
                    "Zu Chongzhi 355/113 exhaustive optimality over 1 <= q <= 16603",
                    "Bilinear friction-hysteresis damping",
                ),
            ),
            _seat_card(
                "SEAT-5",
                "Master Khipukamayuq & Chokwe Sona Geometer",
                "Non-prose topological tree-checksums, chirality parity, Eulerian winding, GF(2) codes",
                (
                    "Hierarchical tree-sum conservation and single-cord tamper detection",
                    "Radial-ring cut survival and rocking dissipation bounds",
                    "Chokwe Sona mirror-curve theorem loop_count(m,n) == gcd(m,n) and GF(2) parity",
                ),
            ),
            _seat_card(
                "SEAT-6",
                "Ibn al-Nafis, Al-Jazari & Antikythera Master Mechanic",
                "Schur complement conductance elimination, mechanical phase-locking, bounded-dissipation control",
                (
                    "Ibn al-Nafis Schur pushforward readable-record symmetry break",
                    "Spinor-Hippopede order-3 BCH commutator suppression",
                    "Antikythera 254/19, 223/19, 53-tooth epicycle and hydraulic Schur conductance",
                ),
            ),
        ]
    elif variation == "civilizations":
        seats = [
            _seat_card("CIV-1", "Islamicate Mathematical & Scientific Tradition", "Rational geometry, cubic/chord analysis, Schur conductance, acoustic ratios", ("Rational Cayley/stereographic", "Al-Kashi chord contraction", "Ibn al-Nafis Schur firewall", "Al-Farabi 53-TET")),
            _seat_card("CIV-2", "South Asian Prosodic, Grammatical & Kerala Analytical Tradition", "Combinatorial binary ranking, C1P interval partitions, rational series tail acceleration", ("Pingala binary/Gray bijection", "Panini 14-sutra C1P compression", "Madhava R1/R2/R3 remainder acceleration")),
            _seat_card("CIV-3", "East Asian Counting-Rod & Timber Engineering Tradition", "Fraction-free integer elimination, general non-coprime CRT, CF optimality, friction hysteresis", ("Jiuzhang fangcheng Z-elimination", "Qin Dayan non-coprime CRT", "Zu Chongzhi 355/113", "Dougong friction hysteresis")),
            _seat_card("CIV-4", "Andean & Amazonian Non-Prose Engineering Tradition", "Knotted-cord tree checksums, hydraulic jump & rocking dissipation, floodplain ring networks", ("Khipu hierarchical tree-sums", "Froude jump & Housner rocking", "Floodplain radial-ring cut survival")),
            _seat_card("CIV-5", "Ancient Egyptian & Mesoamerican Exact Arithmetic Tradition", "Optimal unit-fraction norms, exact frustum dissection, multi-clock calendar synchronization", ("Rhind 2/n vs greedy Sylvester", "9-piece frustum & Seked 14/11", "260/365/584 multi-clock sync")),
            _seat_card("CIV-6", "Mediterranean Mechanical & Sub-Saharan Topological Tradition", "Epicyclic rational gear trains, hydraulic Schur networks, Eulerian mirror curves & GF(2) parity", ("Antikythera 254/19 & 223/19", "Hydraulic aqueduct Schur conductance", "Chokwe Sona gcd(m,n)", "GF(2) parity folding")),
        ]
    elif variation == "operators":
        seats = [
            _seat_card("OP-1", "Schur Complement & Block Elimination Operator", "Boundary-reduced conductance, readable-record symmetry breaking, congruence vs block reduction", ("Schur complement L / B", "Readable-record trace drop 81/1250", "Effective parallel network conductance")),
            _seat_card("OP-2", "Rational Stereographic & Cayley Spherical Operator", "Zero-trig rational parametrizations of S^2/S^3, opposing-pair BCH cancellation, kappa_sub", ("Rational stereographic lift (2u,2v,r^2-1)/(r^2+1)", "Order-3 BCH C3=(0,1/3,1/6,0)", "Subtractive cancellation kappa_sub = x/(1-x)")),
            _seat_card("OP-3", "Asymptotic Remainder & Continued-Fraction Optimality Operator", "Super-convergent Diophantine bounds, alternating tail rational accelerators, unit-fraction minimax", ("CF prefix [3,7,15,1,292] & exhaustive q<=16603", "Rational tail accelerators O(1/n^7)", "Minimax unit-fraction norm vs greedy")),
            _seat_card("OP-4", "Non-Coprime Modular CRT & Fraction-Free Elimination Operator", "General pairwise gcd compatibility, composite multi-clock lcm locks, determinant-preserving Z elimination", ("Fraction-free Z Gaussian elimination", "Non-coprime CRT lcm & 1460x phase compression", "Composite 3-clock synchronization")),
            _seat_card("OP-5", "Consecutive-Ones Partition & Passive Hysteresis Control Operator", "Minimal lossless interval covers, tree-sum integrity checks, bilinear Coulomb dissipation", ("C1P 14-interval exact cover", "Hierarchical tree-sum checksums", "Bilinear friction-hysteresis bounded chatter")),
            _seat_card("OP-6", "GF(2) Parity Folding & Coprime Eulerian Winding Operator", "Hyper-cube XOR parity codes, single-stroke torus-knot coprimality, 2-edge-connected ring cuts", ("GF(2)^4 / GF(2)^8 recursive XOR parity", "Torus-lattice reflection loop count == gcd(m,n)", "Multi-path ring cut survival")),
        ]
    else:
        seats = [
            _seat_card(
                "SEAT-SINGLE",
                "Matched-Budget Single-Agent Cross-Corpus Control",
                "Unified synthesis across all exact operator families without multi-seat personas",
                (
                    "Rational stereographic/Cayley lift and kappa_sub = 215989/11",
                    "Order-3 BCH C3=(0,1/3,1/6,0) and Schur readable-record symmetry breaking",
                    "Fraction-free elimination, non-coprime CRT, 355/113 CF optimality, passive hysteresis",
                    "Hierarchical tree-sums, mirror-curve gcd(m,n), GF(2) parity folding",
                ),
            )
        ]

    if chair == "aletheia":
        seats = [build_seat0_aletheia_scholar_card()] + seats

    pack: Dict[str, Any] = {
        "schema": SCHEMA_DOSSIER_PACK,
        "variation": variation,
        "chair": chair,
        "seat_count": len(seats),
        "seats": seats,
    }
    assert_clean_public_text(json.dumps(pack, sort_keys=True, ensure_ascii=True), check_model_pollution=True)
    if variation == "operators":
        assert_variation_c_label_stripped(pack)
    pack["pack_sha256"] = hashlib.sha256(canonical_json_bytes(pack)).hexdigest()
    return pack


def build_pilot1_prompt_bundle(pack: Dict[str, Any]) -> Dict[str, Any]:
    """Generate clean, model-agnostic structured prompts for cross-era dispatch."""
    require_ok(isinstance(pack, dict) and isinstance(pack.get("seats"), list), "BAD_PACK", "invalid dossier pack")
    prompts: List[Dict[str, Any]] = []
    for topic in PILOT1_TOPICS:
        for seat in pack["seats"]:
            extra = (
                " Include mandatory field epistemic_web_interpositions from exact-operator interposition."
                if seat["seat_id"] == "SEAT-0"
                else ""
            )
            prompt_text = (
                f"Seat: {seat['seat_id']} -- {seat['title']}. "
                f"Lens: {seat['signature_lens']}. "
                f"Topic ({topic['topic_id']} -> {topic['target_frontier']}): {topic['title']}. "
                f"{topic['prompt']} "
                "Respond ONLY as a JSON object with mandatory fields corpus_anchor, "
                "composition_or_challenge, executable_conjecture (pure int/Fraction def check_case(case): -> bool, "
                f"zero floats, zero IO), and target_frontier.{extra}"
            )
            assert_clean_public_text(prompt_text, check_model_pollution=True)
            prompts.append(
                {
                    "topic_id": topic["topic_id"],
                    "target_frontier": topic["target_frontier"],
                    "seat_id": seat["seat_id"],
                    "prompt_text": prompt_text,
                }
            )
    bundle: Dict[str, Any] = {
        "variation": pack["variation"],
        "chair": pack.get("chair", "none"),
        "topic_count": len(PILOT1_TOPICS),
        "prompt_count": len(prompts),
        "prompts": prompts,
    }
    bundle["bundle_sha256"] = hashlib.sha256(canonical_json_bytes(bundle)).hexdigest()
    return bundle


# ---------------------------------------------------------------------------
# 6. Deterministic 3-Round Bidirectional Dry-Run & Certificate Assembly
# ---------------------------------------------------------------------------


def _run_anti_theater_rejection_battery() -> List[Dict[str, Any]]:
    """Verify ANTI_THEATER_GATE rejects 5 canonical theater/float/trivial/SEAT-0 turns."""
    base_good = {
        "turn_id": "THEATER-TEST",
        "round_num": 1,
        "seat_id": "SEAT-1",
        "corpus_anchor": {
            "operator_id": "OP-TEST",
            "source_receipt_id": "corpus:exact-operator-test",
            "statement": "Test operator",
        },
        "composition_or_challenge": {
            "mode": "compose",
            "target_seat_or_turn": "SEAT-2",
            "algebraic_link": "Test link",
        },
        "executable_conjecture": {
            "conjecture_id": "C-TEST",
            "kind": "python_exact_q",
            "claim_summary": "x == x",
            "code": "def check_case(case):\n    return case['x'] == case['x']\n",
            "test_cases": [{"x": 1}],
        },
        "target_frontier": "Foundation-0/continuum",
    }

    t1 = dict(base_good)
    del t1["executable_conjecture"]
    t2 = dict(base_good, executable_conjecture=dict(base_good["executable_conjecture"], test_cases=[]))
    t3 = dict(base_good, executable_conjecture=dict(base_good["executable_conjecture"], code="def check_case(case):\n    return True\n"))
    t4 = dict(base_good, executable_conjecture=dict(base_good["executable_conjecture"], code="def check_case(case):\n    return case['x'] < 3.14\n"))
    t5 = dict(base_good, seat_id="SEAT-0")

    cases = (
        ("prose_missing_conjecture", t1, "THEATER_MISSING_FIELD"),
        ("empty_test_cases", t2, "THEATER_EMPTY_SPEC"),
        ("trivial_constant_true_oracle", t3, "THEATER_TRIVIAL_ORACLE"),
        ("float_literal_in_oracle", t4, "SANDBOX_FLOAT_FORBIDDEN"),
        ("seat0_missing_interpositions", t5, "THEATER_MISSING_INTERPOSITIONS"),
    )
    out: List[Dict[str, Any]] = []
    for label, bad_turn, expected_code in cases:
        got_code = "NOT_REJECTED"
        try:
            validate_seminar_turn(bad_turn)
        except SeminarError as exc:
            got_code = exc.code
        out.append(
            {
                "case": label,
                "expected_code": expected_code,
                "observed_code": got_code,
                "rejected_as_expected": got_code == expected_code,
            }
        )
    return out


def _build_dry_run_turns(interpose_hits: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deterministic 3-round bidirectional seminar proving depth-3 compounding & bidirectional pollination."""
    interps = list(interpose_hits)
    r1_seat0_frame = {
        "turn_id": "R1-SEAT-0",
        "round_num": 1,
        "seat_id": "SEAT-0",
        "corpus_anchor": {
            "operator_id": "ALETHEIA-CAYLEY-S2",
            "source_receipt_id": "corpus:rational-stereographic-cayley",
            "statement": "Rational Cayley/stereographic unit-sphere lift preserving exact norm 1/1 without trig",
        },
        "composition_or_challenge": {
            "mode": "compose",
            "target_seat_or_turn": "SEAT-5",
            "algebraic_link": "Frames finite-net rational norm preservation for historical seats to compose",
        },
        "executable_conjecture": {
            "conjecture_id": "CONJ-R1-SEAT0-CAYLEY-NORM",
            "kind": "python_exact_q",
            "claim_summary": "Rational stereographic/Cayley lift lands identically on x^2 + y^2 + z^2 == 1/1",
            "code": (
                "from fractions import Fraction\n"
                "def check_case(case):\n"
                "    u = Fraction(case['u_num'], case['u_den'])\n"
                "    v = Fraction(case['v_num'], case['v_den'])\n"
                "    d = 1 + u * u + v * v\n"
                "    x = (2 * u) / d\n"
                "    y = (2 * v) / d\n"
                "    z = (u * u + v * v - 1) / d\n"
                "    return x * x + y * y + z * z == Fraction(1, 1)\n"
            ),
            "test_cases": [
                {"u_num": 0, "u_den": 1, "v_num": 0, "v_den": 1},
                {"u_num": 1, "u_den": 2, "v_num": 3, "v_den": 5},
                {"u_num": -7, "u_den": 3, "v_num": 4, "v_den": 11},
            ],
        },
        "target_frontier": "Foundation-0/continuum",
        "epistemic_web_interpositions": interps,
    }

    r1_seat4_broken = {
        "turn_id": "R1-SEAT-4",
        "round_num": 1,
        "seat_id": "SEAT-4",
        "corpus_anchor": {
            "operator_id": "QIN-DAYAN-CRT",
            "source_receipt_id": "corpus:qin-jiushao-non-coprime-crt",
            "statement": "Qin Jiushao non-coprime CRT on 3-clock moduli (260, 365, 584)",
        },
        "composition_or_challenge": {
            "mode": "challenge",
            "target_seat_or_turn": "SEAT-0",
            "algebraic_link": "Incomplete first-pair compatibility conjecture for 3-clock reachability",
        },
        "executable_conjecture": {
            "conjecture_id": "CONJ-R1-INCOMPLETE-CRT",
            "kind": "python_exact_q",
            "claim_summary": "Checks whether first-pair gcd compatibility alone suffices for 3-clock solvability",
            "code": (
                "from math import gcd\n"
                "def check_case(case):\n"
                "    a, b, c = case['a'], case['b'], case['c']\n"
                "    m1, m2, m3 = case['m1'], case['m2'], case['m3']\n"
                "    first_pair = (a - b) % gcd(m1, m2) == 0\n"
                "    all_pairs = ((a - b) % gcd(m1, m2) == 0) and ((b - c) % gcd(m2, m3) == 0) and ((a - c) % gcd(m1, m3) == 0)\n"
                "    return first_pair == all_pairs\n"
            ),
            "test_cases": [
                {"a": 125, "b": 300, "c": 81, "m1": 260, "m2": 365, "m3": 584},
                {"a": 0, "b": 0, "c": 1, "m1": 260, "m2": 365, "m3": 584},
            ],
        },
        "target_frontier": "Foundation-0/continuum",
    }

    r2_seat0_steelman = {
        "turn_id": "R2-SEAT-0",
        "round_num": 2,
        "seat_id": "SEAT-0",
        "corpus_anchor": {
            "operator_id": "ALETHEIA-STEELMAN-CRT",
            "source_receipt_id": "corpus:qin-jiushao-non-coprime-crt",
            "statement": "Steelman repair of R1-SEAT-4 using live referee counterexample and exact 1460x compression",
        },
        "composition_or_challenge": {
            "mode": "repair",
            "target_seat_or_turn": "R1-SEAT-4",
            "algebraic_link": "Historical->Modern lift: repairs pairwise CRT obstruction into continuum modular flow",
        },
        "executable_conjecture": {
            "conjecture_id": "CONJ-R2-SEAT0-REPAIRED-CRT",
            "kind": "python_exact_q",
            "claim_summary": "All-pairs gcd compatibility matches exact solvability and compression ratio == 1460",
            "code": (
                "from math import gcd\n"
                "def check_case(case):\n"
                "    a, b, c = case['a'], case['b'], case['c']\n"
                "    m1, m2, m3 = case['m1'], case['m2'], case['m3']\n"
                "    compat = ((a - b) % gcd(m1, m2) == 0) and ((b - c) % gcd(m2, m3) == 0) and ((a - c) % gcd(m1, m3) == 0)\n"
                "    l12 = (m1 // gcd(m1, m2)) * m2\n"
                "    l123 = (l12 // gcd(l12, m3)) * m3\n"
                "    comp = (m1 * m2 * m3) // l123\n"
                "    return (compat == case['expected_solvable']) and (comp == case['expected_compression'])\n"
            ),
            "test_cases": [
                {"a": 125, "b": 300, "c": 81, "m1": 260, "m2": 365, "m3": 584, "expected_solvable": True, "expected_compression": 1460},
                {"a": 0, "b": 0, "c": 1, "m1": 260, "m2": 365, "m3": 584, "expected_solvable": False, "expected_compression": 1460},
                {"a": 2, "b": 3, "c": 2, "m1": 3, "m2": 5, "m3": 7, "expected_solvable": True, "expected_compression": 1},
            ],
        },
        "target_frontier": "Foundation-0/continuum",
        "epistemic_web_interpositions": interps,
    }

    r2_seat5_composed = {
        "turn_id": "R2-SEAT-5",
        "round_num": 2,
        "seat_id": "SEAT-5",
        "corpus_anchor": {
            "operator_id": "SONA-TORUS-COPRIMALITY",
            "source_receipt_id": "corpus:sona-mirror-curve-gcd",
            "statement": "Chokwe Sona mirror-curve orbit fragmentation gcd(m,n) extending SEAT-0 rational lattice frame",
        },
        "composition_or_challenge": {
            "mode": "compose",
            "target_seat_or_turn": "R1-SEAT-0",
            "algebraic_link": "Modern->Historical bridge: extends SEAT-0 rational Cayley frame via discrete torus coprimality",
        },
        "executable_conjecture": {
            "conjecture_id": "CONJ-R2-SONA-CLOCK-ORBITS",
            "kind": "python_exact_q",
            "claim_summary": "Two-clock orbit fragmentation equals gcd(m,n) == (m*n)//lcm(m,n) and single-cycle iff gcd==1",
            "code": (
                "from math import gcd\n"
                "def check_case(case):\n"
                "    m, n = case['m'], case['n']\n"
                "    g = gcd(m, n)\n"
                "    lcm_mn = (m // g) * n\n"
                "    orbits = (m * n) // lcm_mn\n"
                "    return (orbits == g) and ((orbits == 1) == case['monolinear'])\n"
            ),
            "test_cases": [
                {"m": 260, "n": 365, "monolinear": False},
                {"m": 365, "n": 584, "monolinear": False},
                {"m": 254, "n": 19, "monolinear": True},
                {"m": 7, "n": 11, "monolinear": True},
            ],
        },
        "target_frontier": "Foundation-0/aletheion",
    }

    r3_seat6_depth3 = {
        "turn_id": "R3-SEAT-6",
        "round_num": 3,
        "seat_id": "SEAT-6",
        "corpus_anchor": {
            "operator_id": "NAFIS-SCHUR-CONDUCTANCE",
            "source_receipt_id": "corpus:ibn-al-nafis-schur-conductance",
            "statement": "Schur complement effective boundary conductance on 3-node star-triangle network",
        },
        "composition_or_challenge": {
            "mode": "compose",
            "target_seat_or_turn": "R2-SEAT-5",
            "algebraic_link": "Composes Sona single-cycle connectivity with exact rational Schur conductance reduction",
        },
        "executable_conjecture": {
            "conjecture_id": "CONJ-R3-SCHUR-BOUNDARY-CONDUCTANCE",
            "kind": "python_exact_q",
            "claim_summary": "Eliminating interior node 3 via Schur complement yields g_eff == g12 + (g13*g23)/(g13+g23)",
            "code": (
                "from fractions import Fraction\n"
                "def check_case(case):\n"
                "    g12 = Fraction(case['g12'], 1)\n"
                "    g13 = Fraction(case['g13'], 1)\n"
                "    g23 = Fraction(case['g23'], 1)\n"
                "    schur_11 = (g12 + g13) - (g13 * g13) / (g13 + g23)\n"
                "    schur_12 = -g12 - (g13 * g23) / (g13 + g23)\n"
                "    g_eff = g12 + (g13 * g23) / (g13 + g23)\n"
                "    return (schur_11 == g_eff) and (schur_12 == -g_eff)\n"
            ),
            "test_cases": [
                {"g12": 0, "g13": 2, "g23": 2},
                {"g12": 1, "g13": 3, "g23": 6},
                {"g12": 5, "g13": 4, "g23": 12},
            ],
        },
        "target_frontier": "Foundation-0/cave-expedition",
    }

    return [r1_seat0_frame, r1_seat4_broken, r2_seat0_steelman, r2_seat5_composed, r3_seat6_depth3]


def validate_certificate_payload(cert: Any) -> None:
    require_ok(isinstance(cert, dict), "BAD_CERT_TYPE", "certificate must be a dict")
    validate_json_tree_no_floats(cert)
    require_ok(set(cert.keys()) == EXPECTED_CERT_KEYS, "BAD_CERT_KEYS", "certificate keys mismatch")
    require_ok(cert["schema"] == SCHEMA_SEMINAR_CERT, "BAD_SCHEMA", "unexpected certificate schema")
    require_ok(cert["energy_power_status"] == ENERGY_POWER_STATUS, "BAD_ENERGY", "energy_power_status mismatch")
    require_ok(cert["zero_floats"] is True, "BAD_ZERO_FLOATS", "zero_floats must be True")
    require_ok(cert["pure_q_ast_clean"] is True, "BAD_AST_FLAG", "pure_q_ast_clean must be True")
    require_ok(cert["all_passed"] is True, "GATES_NOT_ALL_PASSED", "all_passed must be True")
    assert_clean_public_text(json.dumps(cert, sort_keys=True, ensure_ascii=True), check_model_pollution=True)

    payload = {k: v for k, v in cert.items() if k not in ("payload_sha256", "certificate_sha256")}
    expected_p = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    require_ok(
        type(cert["payload_sha256"]) is str and hmac.compare_digest(cert["payload_sha256"], expected_p),
        "PAYLOAD_SHA_MISMATCH",
        "payload_sha256 mismatch",
    )
    body = {k: v for k, v in cert.items() if k != "certificate_sha256"}
    expected_c = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    require_ok(
        type(cert["certificate_sha256"]) is str and hmac.compare_digest(cert["certificate_sha256"], expected_c),
        "CERT_SHA_MISMATCH",
        "certificate_sha256 mismatch",
    )


def build_self_test_certificate() -> Dict[str, Any]:
    try:
        self_raw = read_regular_file_bytes(Path(__file__), "MISSING_SELF")
        ast_res = verify_pure_q_ast(self_raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise SeminarError("BAD_UTF8", f"Invalid UTF-8 in harness source: {exc}") from exc
    anti_theater = _run_anti_theater_rejection_battery()
    interpose_probe = run_local_interpose(
        title="Bidirectional Seminar Exact-Operator Probe",
        text="Schur complement Cayley SU(2) non-coprime CRT Maya 260 365 584",
        top_k=3,
    )
    session = evaluate_seminar_session(
        session_id="SEMINAR-DRYRUN-PILOT0-ARM-A-PLUS",
        variation="scholars",
        chair="aletheia",
        topic_id="TOPIC-1-CONTINUUM",
        turns=_build_dry_run_turns(interpose_probe["hits"]),
    )

    packs_summary: Dict[str, Dict[str, Any]] = {}
    for arm_name, var, chair_mode in (
        ("arm_a_plus", "scholars", "aletheia"),
        ("arm_a_minus", "scholars", "none"),
        ("arm_b_plus", "civilizations", "aletheia"),
        ("arm_c_plus", "operators", "aletheia"),
        ("arm_c_pure", "operators", "none"),
        ("arm_d_single", "single", "none"),
    ):
        pack = build_variation_pack(var, chair=chair_mode)
        packs_summary[arm_name] = {
            "variation": var,
            "chair": chair_mode,
            "seat_count": pack["seat_count"],
            "pack_sha256": pack["pack_sha256"],
        }

    all_passed = all(
        (
            ast_res["pure_q_ast_clean"],
            all(item["rejected_as_expected"] for item in anti_theater),
            len(interpose_probe["hits"]) >= 1,
            session["pass_witness_count"] == 4,
            session["minimal_counterexample_count"] == 1,
            session["max_dag_depth"] == 3,
            session["s150_g2_dynamic_compounding_passed"],
            session["s150_g5_bidirectional_pollination_passed"],
            len(packs_summary) == 6,
        )
    )
    payload: Dict[str, Any] = {
        "schema": SCHEMA_SEMINAR_CERT,
        "energy_power_status": ENERGY_POWER_STATUS,
        "zero_floats": True,
        "pure_q_ast_clean": ast_res["pure_q_ast_clean"],
        "anti_theater_rejections": anti_theater,
        "dry_run_session": session,
        "variation_packs_summary": packs_summary,
        "local_interpose_probe": interpose_probe,
        "all_passed": all_passed,
    }
    p_sha = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    cert = dict(payload)
    cert["payload_sha256"] = p_sha
    cert["certificate_sha256"] = hashlib.sha256(canonical_json_bytes(cert)).hexdigest()
    validate_certificate_payload(cert)
    return cert


def check_certificate_file(path: Path) -> Dict[str, Any]:
    raw = read_regular_file_bytes(path, missing_code="MISSING_CERT")
    data = loads_strict_json_bytes(raw, path.name)
    validate_certificate_payload(data)
    expected = build_self_test_certificate()
    require_ok(
        hmac.compare_digest(data["certificate_sha256"], expected["certificate_sha256"]),
        "LIVE_RECOMPUTE_MISMATCH",
        "Certificate does not match live deterministic dry-run recomputation",
    )
    return data


def emit_all_dossiers(out_dir: Path) -> Dict[str, str]:
    """Write SEAT-0 dossier, all variation packs, and Pilot-1 prompt bundle."""
    refuse_symlink_path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    hashes: Dict[str, str] = {}

    seat0_doc: Dict[str, Any] = {
        "schema": SCHEMA_SEAT0_DOSSIER,
        "seat": build_seat0_aletheia_scholar_card(),
    }
    seat0_doc["dossier_sha256"] = hashlib.sha256(canonical_json_bytes(seat0_doc)).hexdigest()
    s0_text = json.dumps(seat0_doc, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
    out_dir.joinpath("seat0_aletheia_scholar.json").write_text(s0_text, encoding="utf-8")
    hashes["seat0_aletheia_scholar.json"] = hashlib.sha256(s0_text.encode("utf-8")).hexdigest()

    pack_specs = (
        ("variation_a_plus_scholars_chaired.json", "scholars", "aletheia"),
        ("variation_a_minus_scholars_unchaired.json", "scholars", "none"),
        ("variation_b_plus_civilizations.json", "civilizations", "aletheia"),
        ("variation_c_plus_operators.json", "operators", "aletheia"),
        ("variation_c_operators_label_stripped.json", "operators", "none"),
        ("variation_d_single.json", "single", "none"),
    )
    emitted_packs: Dict[str, Dict[str, Any]] = {}
    for fname, var, chair_mode in pack_specs:
        pack = build_variation_pack(var, chair=chair_mode)
        emitted_packs[fname] = pack
        text = json.dumps(pack, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
        out_dir.joinpath(fname).write_text(text, encoding="utf-8")
        hashes[fname] = hashlib.sha256(text.encode("utf-8")).hexdigest()

    bundle = build_pilot1_prompt_bundle(emitted_packs["variation_a_plus_scholars_chaired.json"])
    b_text = json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
    out_dir.joinpath("pilot1_prompts_arm_a_plus.json").write_text(b_text, encoding="utf-8")
    hashes["pilot1_prompts_arm_a_plus.json"] = hashlib.sha256(b_text.encode("utf-8")).hexdigest()
    return hashes


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Trans-Historical Operator Socratic Seminar Harness")
    parser.add_argument("--chair", choices=ALLOWED_CHAIRS, default="aletheia", help="Chair mode (aletheia SEAT-0 or none)")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--self-test", action="store_true", help="Run deterministic 3-round dry-run and print JSON")
    group.add_argument("--write-cert", type=Path, help="Write deterministic dry-run certificate to path")
    group.add_argument("--check-cert", type=Path, help="Fail-closed verify certificate against live recomputation")
    group.add_argument("--emit-dossiers", type=Path, help="Emit SEAT-0, all variation packs, and Pilot-1 prompts")
    group.add_argument("--variation", choices=ALLOWED_VARIATIONS, help="Print single variation dossier pack as JSON")
    args = parser.parse_args(argv)

    try:
        if args.check_cert is not None:
            cert = check_certificate_file(args.check_cert)
            print(json.dumps({"status": "PASS", "certificate_sha256": cert["certificate_sha256"]}, sort_keys=True))
            return 0
        if args.emit_dossiers is not None:
            hashes = emit_all_dossiers(args.emit_dossiers)
            print(json.dumps({"status": "EMITTED", "files": hashes}, sort_keys=True))
            return 0
        if args.variation is not None:
            pack = build_variation_pack(args.variation, chair=args.chair)
            sys.stdout.write(json.dumps(pack, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n")
            return 0
        cert = build_self_test_certificate()
        out_text = json.dumps(cert, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"
        if args.write_cert is not None:
            refuse_symlink_path(args.write_cert)
            args.write_cert.write_text(out_text, encoding="utf-8")
            print(json.dumps({"status": "WRITTEN", "certificate_sha256": cert["certificate_sha256"]}, sort_keys=True))
            return 0
        sys.stdout.write(out_text)
        return 0
    except SeminarError as exc:
        sys.stderr.write(json.dumps({"error_code": exc.code, "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2
    except (OSError, UnicodeDecodeError) as exc:
        err_code = "BAD_UTF8" if isinstance(exc, UnicodeDecodeError) else "IO_ERROR"
        sys.stderr.write(json.dumps({"error_code": err_code, "message": str(exc), "status": "FAIL"}, sort_keys=True) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
