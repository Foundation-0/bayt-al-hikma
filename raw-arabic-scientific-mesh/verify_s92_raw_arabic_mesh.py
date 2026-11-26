#!/usr/bin/env python3
"""Zone-B & R10+ Hardened Verifier for Raw-Arabic K_12 Scientific Mesh.

Pure Python 3 standard library only:
- Zero floats anywhere on trust paths, zero bare asserts, zero RNG calls.
- Atomic dir_fd step-down + $PWD symlink guard + O_NONBLOCK + O_NOFOLLOW + S_ISREG
  + st_nlink == 1 + streaming 65,536-byte bounded read.
- Durable 0o600 atomic dir_fd writes (threading.Lock + secrets.token_hex).
- Pre-parse MAX_INT_DIGITS=80 & MAX_INT_BITS=256 strict JSON parser.
- Strict type(full_replay) is bool; raising field-complete secondary_audit_payload.
- Comment-only R10+ Lean static scanner + EXPECTED_LEAN_SHA256 pin + live lean --stdin
  axiom verification (fail-closed if lean binary missing).
- Optional --verify-datasets --heritage-root <dir> --bayt-root <dir> on-disk SHA check
  (zero hardcoded host paths).
"""

import argparse
import errno
from fractions import Fraction
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import threading
import unicodedata

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import s92_raw_arabic_mesh_oracle as O

MAX_JSON_BYTES = 1_048_576
MAX_LEAN_BYTES = 262_144
_READ_CHUNK_BYTES = 65_536
MAX_JSON_DEPTH = 64
MAX_INT_DIGITS = 80
MAX_INT_BITS = 256
_EXACT_PATH_TYPES = (Path, type(Path()))
_TEMP_NAME_LOCK = threading.Lock()
_HEX_LOWER = frozenset("0123456789abcdef")

EXPECTED_LEAN_SHA256 = "5218f72990f82c8aedd948daeac0bd105349dcc41848a455c824933a71235486"
EXPECTED_ANCHOR_INTERNAL_SHA256 = "b3ef0ec9ca71cb378a2d55c7d1364ee963acc2a13f7b19ec817422903a502474"
EXPECTED_BAYT_CONTINUUM_FILE_SHA256 = "7081c463ad8ce4cce12f61f29f31f0f4741bbbfb4d43d85824622bcc62ac9069"
EXPECTED_BAYT_CONTINUUM_INTERNAL_SHA256 = "99ec338fc7aec339c1ea5216afd2a0bcac4bff647d487a1a3f80c403b581b951"
EXPECTED_BAYT_LEXICON_FILE_SHA256 = "96d855fac3d017f716adf67f4d8af1a6eb8b620372b93ae5a945ee6a1da62586"
EXPECTED_BAYT_LEXICON_INTERNAL_SHA256 = "230441ac38e9f84719f3acf7c491f9b1e14f1360d892bd36802bca046ad4ff77"
CERT_KEYS = frozenset({"schema", "track_id", "payload_sha256", "certificate_sha256", "payload"})
PAYLOAD_KEYS = frozenset({
    "schema_version",
    "track_id",
    "novelty_classification",
    "anchor_pin",
    "n0_bayt_al_hikma_prior_art",
    "pillar1_raw_arabic_k12_mesh",
    "pillar2_bridges_and_law5_obstruction",
    "pillar3_bilingual_scientific_catalogs",
    "lean_companion_spec",
    "all_gates_passed",
    "verdict",
})
EXPECTED_P3_VARIANTS = frozenset({
    "stem_v1__en_pr_min4",
    "stem_v1__en_no_suffix",
    "stem_v1__en_min5",
    "stem_v2__en_pr_min4",
    "stem_v2__en_no_suffix",
    "stem_v2__en_min5",
})
EXPECTED_TREATISE_METADATA = (
    ("haytham_manazir", "optics", "Ibn al-Haytham", "Kitab al-Manazir", "04_physics_optics/openiti_classical_physics_optics/full_texts/02_\u0643\u062a\u0627\u0628_\u0627\u0644\u0645\u0646\u0627\u0638\u0631.md"),
    ("sina_shifa_phys", "physics", "Ibn Sina (ed. study + primary extracts)", "Tabiiyyat al-Shifa", "04_physics_optics/openiti_classical_physics_optics/full_texts/01_\u0637\u0628\u064a\u0639\u064a\u0627\u062a_\u0643\u062a\u0627\u0628_\u0627\u0644\u0634\u0641\u0627\u0621__\u0627\u0644\u0633\u0645\u0627\u0639_\u0627\u0644\u0637\u0628\u064a\u0639\u064a.md"),
    ("sina_qanun", "medicine", "Ibn Sina", "Al-Qanun fi al-Tibb", "01_medicine/openiti_classical_medicine/full_texts/01_\u0627\u0644\u0642\u0627\u0646\u0648\u0646_\u0641\u064a_\u0627\u0644\u0637\u0628.md"),
    ("nafis_tashrih", "medicine", "Ibn al-Nafis", "Sharh Tashrih al-Qanun", "01_medicine/openiti_classical_medicine/full_texts/02_\u0634\u0631\u062d_\u062a\u0634\u0631\u064a\u062d_\u0627\u0644\u0642\u0627\u0646\u0648\u0646.md"),
    ("battani_zij", "astronomy", "Al-Battani", "Al-Zij al-Sabi", "02_astronomy/openiti_classical_astronomy/full_texts/01_\u0632\u064a\u062c_\u0627\u0644\u0635\u0627\u0628\u0626__\u0627\u0644\u0632\u064a\u062c_.md"),
    ("biruni_masudi", "astronomy", "Al-Biruni", "Al-Qanun al-Masudi", "02_astronomy/abu_al_rayhan_al_biruni_362_440h/al_qanun_al_masudi/al_biruni_qanun_masudi.jsonl"),
    ("biruni_asturlab", "astronomy", "Al-Biruni", "Istiab al-Wujuh fi Sanat al-Asturlab", "02_astronomy/openiti_classical_astronomy/full_texts/02_\u0627\u0633\u062a\u064a\u0639\u0627\u0628_\u0627\u0644\u0648\u062c\u0648\u0647_\u0627\u0644\u0645\u0645\u0643\u0646\u0629_\u0641\u064a_\u0635\u0646\u0639\u0629_\u0627\u0644\u0623\u0633.md"),
    ("tusi_majisti", "astronomy", "Nasir al-Din al-Tusi", "Tahrir al-Majisti", "02_astronomy/ptolemaeus_arabus_corpus/full_texts/09_C.1.18_Ta\u1e25r\u012br_al-Majis\u1e6d\u012b.md"),
    ("biruni_zilal", "mathematics", "Al-Biruni", "Ifrad al-Maqal fi Amr al-Zilal", "03_mathematics/abu_al_rayhan_al_biruni_362_440h/ifrad_al_maqal_amr_al_zilal/al_biruni_amr_al_zilal.jsonl"),
    ("biruni_awtar", "mathematics", "Al-Biruni", "Istikhraj al-Awtar fi al-Daira", "03_mathematics/abu_al_rayhan_al_biruni_362_440h/istikhraj_al_awtar/al_biruni_istikhraj_al_awtar.jsonl"),
    ("thabit_niqumakhus", "mathematics", "Thabit ibn Qurra", "Madkhal Niqumakhus (Arithmetic)", "03_mathematics/thabit_ibn_qurra_al_harrani_221_288h/madkhal_niqumakhus/thabit_ibn_qurra_niqumakhus_arithmetic.jsonl"),
    ("biruni_jamahir", "natural_history", "Al-Biruni", "Al-Jamahir fi Marifat al-Jawahir", "05_natural_history/openiti_classical_natural_history/full_texts/02_\u0627\u0644\u062c\u0645\u0627\u0647\u0631_\u0641\u064a_\u0645\u0639\u0631\u0641\u0629_\u0627\u0644\u062c\u0648\u0627\u0647\u0631.md"),
)
EXPECTED_TREATISE_PINS = (
    ("haytham_manazir", 1381038, "778d6d3c416267b502e5c1af74dcce2457e63d36574fa6879316d7732bcd566e", 139788),
    ("sina_shifa_phys", 302719, "1fd43c42ddae471ae573e477a283109876b43178425393e6c63f745d1b082748", 29413),
    ("sina_qanun", 6988898, "0a673808f0d045ad237e386022df3300382035f0378b70efb893fa3c79a5694d", 703603),
    ("nafis_tashrih", 943264, "84e0a89b32a5f9d4ca95efae6c6ad0642bdff1ccb2fb085a472465897ba6ae8f", 97610),
    ("battani_zij", 699110, "1c5574ab55377c827e6258b0572ed8b26575ac2f14f33e435bf6f073a1d2c799", 73931),
    ("biruni_masudi", 2862364, "9b1a64b861902ba4498670603d46719f02433260f443ca73bf4fd0cc8d605bab", 280778),
    ("biruni_asturlab", 155978, "be393fecf6d0394af949c305d5c31e9621abd48d61b5537d6e83547d87eba666", 15907),
    ("tusi_majisti", 90814, "9001f397f43c51165276269aabaf188a954d156a89ceb7ab2c13a08f20d58aae", 8242),
    ("biruni_zilal", 422156, "16cc80fac1960c796834eeb8dc14ae58659237d6fac59b27c46562e3b443053f", 41006),
    ("biruni_awtar", 214663, "435ddfce3ea793ae8e2afd54da263576b676f099fe0f1c137dbdebe04d884480", 22253),
    ("thabit_niqumakhus", 282654, "3ea3a10398162948619ef77ab0971ebb0623f3d0cf8a0ceff603629127c1ef00", 29134),
    ("biruni_jamahir", 576978, "da7337857fb079cf0e87741546531ac98040e39f626eb65e93fa7635b1bc0e21", 58945),
)
EXPECTED_THEMATIC_ROOT_KEYS = ("w_t_r", "q_t_E", "j_b_r", "n_f_dh", "z_l_l", "E_k_s", "q_y_s", "E_d_l")

_DEC6_RE = re.compile(r"^-?[0-9]+\.[0-9]{6}$")
_FRAC_RE = re.compile(r"^-?[0-9]+/[1-9][0-9]*$")
_LEAN_IDENT_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_']*\b")
_LEAN_DECL_RE = re.compile(r"\b(?:(?:private|protected)\s+)?theorem\s+([A-Za-z_][A-Za-z0-9_]*)\b")
_LEAN_HASH_CMD_RE = re.compile(r"#\s*[A-Za-z_][A-Za-z0-9_]*")
_LEAN_DECIDE_OPT_RE = re.compile(r"\bdecide\s*\(")

BANNED_LEAN_TOKENS = frozenset({
    "import",
    "sorry",
    "admit",
    "axiom",
    "opaque",
    "unsafe",
    "unsafeRec",
    "partial",
    "implemented_by",
    "implementedBy",
    "extern",
    "export",
    "csimp",
    "native",
    "config",
    "revert",
    "native_decide",
    "decide_cbv",
    "bv_decide",
    "set_option",
    "macro",
    "macro_rules",
    "elab",
    "elab_rules",
    "syntax",
    "declare_syntax_cat",
    "notation",
    "prefix",
    "infix",
    "infixl",
    "infixr",
    "postfix",
    "attribute",
    "init",
    "builtin_init",
    "initialize",
    "builtin_initialize",
    "run_cmd",
    "run_meta",
    "dbg_trace",
    "dbgTrace",
    "dbgTraceVal",
    "dbgTraceIfShared",
    "dbgSleep",
    "dbgStackTrace",
    "panic",
    "panicCore",
    "panicWithPosWithDecl",
    "unreachable",
    "throwError",
    "interpolatedStr",
    "skipKernelTC",
    "byAsSorry",
    "proofAsSorry",
    "terminalTacticsAsSorry",
    "Classical",
    "Lean",
    "Meta",
    "Elab",
    "IO",
    "BaseIO",
    "System",
    "ofReduceBool",
    "ofReduceNat",
    "trustCompiler",
    "mkSorry",
    "lcProof",
    "sorryAx",
    "noncomputable",
    "local",
    "scoped",
})

BANNED_LEAN_CHARS = frozenset({'"', "'", "\u00ab", "\u00bb", "`"})


class S92VerifyError(ValueError):
    """Typed fail-closed error for Raw-Arabic Scientific Mesh verification."""

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def require_ok(cond, code, message):
    if not cond:
        raise S92VerifyError(code, message)


def _require_str_no_surrogate(val, label):
    require_ok(type(val) is str, "INVALID_STR", f"{label} must be strict str")
    try:
        val.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise S92VerifyError("INVALID_UNICODE_STR", f"{label} lone surrogate forbidden") from exc
    return val


def require_sha256_hex(val, label):
    _require_str_no_surrogate(val, label)
    require_ok(len(val) == 64, "INVALID_DIGEST_LEN", f"{label} must have length 64")
    require_ok(all(ch in _HEX_LOWER for ch in val), "INVALID_DIGEST_HEX", f"{label} must be lowercase ASCII hex")
    return val


def require_exact_int(val, label, min_val=None, max_val=None):
    require_ok(type(val) is int, "INVALID_INT", f"{label} must be strict int")
    require_ok(val.bit_length() <= MAX_INT_BITS, "INT_BIT_LIMIT", f"{label} exceeds {MAX_INT_BITS} bits")
    if min_val is not None:
        require_ok(val >= min_val, "INT_TOO_SMALL", f"{label} < {min_val}")
    if max_val is not None:
        require_ok(val <= max_val, "INT_TOO_LARGE", f"{label} > {max_val}")
    return val


def require_exact_bool(val, label, expected=None):
    require_ok(type(val) is bool, "INVALID_BOOL", f"{label} must be strict bool")
    if expected is not None:
        require_ok(val is expected, "BOOL_VALUE_MISMATCH", f"{label} expected {expected}")
    return val


def require_dec6_fraction(val, label):
    _require_str_no_surrogate(val, label)
    require_ok(_DEC6_RE.match(val) is not None, "INVALID_DEC6", f"{label} not dec6: {val}")
    neg = val.startswith("-")
    body = val[1:] if neg else val
    whole, frac = body.split(".")
    require_ok(len(whole) <= MAX_INT_DIGITS, "DEC6_WHOLE_DIGITS", f"{label} integer part too long")
    num = int(whole) * 1_000_000 + int(frac)
    return Fraction(-num if neg else num, 1_000_000)


def require_frac_str(val, label):
    _require_str_no_surrogate(val, label)
    require_ok(_FRAC_RE.match(val) is not None, "INVALID_FRAC_STR", f"{label} not exact fraction: {val}")
    num_s, den_s = val.split("/")
    require_ok(len(num_s.lstrip("-")) <= MAX_INT_DIGITS, "FRAC_NUM_DIGITS", f"{label} numerator too long")
    require_ok(len(den_s) <= MAX_INT_DIGITS, "FRAC_DEN_DIGITS", f"{label} denominator too long")
    return Fraction(int(num_s), int(den_s))


def validate_json_tree_iterative(obj, max_depth=MAX_JSON_DEPTH):
    limit = require_exact_int(max_depth, "max_depth", min_val=1, max_val=256)
    stack = [(obj, 0)]
    while stack:
        cur, depth = stack.pop()
        require_ok(depth <= limit, "JSON_DEPTH_EXCEEDED", f"depth > {limit}")
        t = type(cur)
        if t is dict:
            for k, v in cur.items():
                _require_str_no_surrogate(k, "dict_key")
                stack.append((v, depth + 1))
        elif t is list:
            for item in cur:
                stack.append((item, depth + 1))
        elif t is int:
            require_ok(cur.bit_length() <= MAX_INT_BITS, "INT_BIT_LIMIT", "int exceeds bit limit")
        elif t is str:
            _require_str_no_surrogate(cur, "str_val")
        elif t is bool or cur is None:
            continue
        else:
            raise S92VerifyError("FORBIDDEN_JSON_TYPE", f"forbidden type {t.__name__}")


def _no_dups_hook(pairs):
    out = {}
    for k, v in pairs:
        require_ok(k not in out, "DUPLICATE_JSON_KEY", f"duplicate key {k}")
        out[k] = v
    return out


def _forbid_float(token):
    raise S92VerifyError("FLOAT_FORBIDDEN", f"float literal forbidden: {token}")


def _forbid_constant(token):
    raise S92VerifyError("NONFINITE_CONSTANT", f"non-finite constant forbidden: {token}")


def _parse_capped_int_token(token):
    digits = token[1:] if token.startswith("-") else token
    require_ok(len(digits) <= MAX_INT_DIGITS, "INT_DIGIT_LIMIT", f"int exceeds {MAX_INT_DIGITS} digits")
    return int(token)


def parse_strict_json(text):
    _require_str_no_surrogate(text, "json_text")
    encoded = text.encode("utf-8")
    require_ok(len(encoded) <= MAX_JSON_BYTES, "JSON_TOO_LARGE", f"JSON exceeds {MAX_JSON_BYTES} bytes")
    try:
        parsed = json.loads(
            text,
            object_pairs_hook=_no_dups_hook,
            parse_int=_parse_capped_int_token,
            parse_float=_forbid_float,
            parse_constant=_forbid_constant,
        )
    except S92VerifyError:
        raise
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise S92VerifyError("JSON_DECODE_ERROR", f"invalid JSON: {exc}") from exc
    validate_json_tree_iterative(parsed)
    return parsed


def canonical_json_bytes(obj):
    validate_json_tree_iterative(obj)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


# ---------------------------------------------------------------------------
# Hardened Atomic dir_fd I/O (Zone-B Parity)
# ---------------------------------------------------------------------------

def _validate_path_obj(path):
    require_ok(type(path) in _EXACT_PATH_TYPES, "INVALID_PATH_TYPE", "path must be concrete Path")
    raw_s = _require_str_no_surrogate(str(path), "path")
    require_ok("\x00" not in raw_s, "INVALID_PATH_NUL", "NUL byte forbidden in path")
    return raw_s


def _is_symlink_at(dfd, name):
    try:
        return stat.S_ISLNK(os.lstat(name, dir_fd=dfd).st_mode)
    except OSError:
        return False


def _check_pwd_no_symlinks():
    pwd = os.environ.get("PWD")
    if pwd is None or not os.path.isabs(pwd):
        return
    _require_str_no_surrogate(pwd, "PWD")
    cur_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for comp in Path(pwd).parts[1:]:
            try:
                nxt = os.open(comp, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=cur_fd)
            except OSError as exc:
                if _is_symlink_at(cur_fd, comp):
                    raise S92VerifyError("SYMLINK_ANCESTOR_FORBIDDEN", f"symlink ancestor in PWD: {comp}") from exc
                return
            os.close(cur_fd)
            cur_fd = nxt
    finally:
        os.close(cur_fd)


def _open_parent_dir_fd(path, create_parents=False, not_found_code="FILE_NOT_FOUND"):
    _validate_path_obj(path)
    is_abs = path.is_absolute()
    if not is_abs:
        _check_pwd_no_symlinks()
    parts = path.parts[1:] if is_abs else path.parts
    require_ok(len(parts) > 0, not_found_code, "path must name a regular file")
    require_ok(parts[-1] != "..", "PARENT_REF_FORBIDDEN", "parent directory reference forbidden")
    ancestors, leaf = parts[:-1], parts[-1]
    cur_fd = os.open("/" if is_abs else ".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for comp in ancestors:
            if create_parents:
                try:
                    os.mkdir(comp, 0o700, dir_fd=cur_fd)
                except FileExistsError:
                    pass
                except OSError as exc:
                    raise S92VerifyError("MKDIR_ERROR", f"cannot create directory {comp}") from exc
            try:
                nxt = os.open(comp, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=cur_fd)
            except OSError as exc:
                if _is_symlink_at(cur_fd, comp):
                    raise S92VerifyError("SYMLINK_ANCESTOR_FORBIDDEN", f"symlink ancestor forbidden: {comp}") from exc
                if exc.errno in (errno.ENOENT, errno.ENOTDIR):
                    raise S92VerifyError(not_found_code, f"ancestor not found: {comp}") from exc
                raise S92VerifyError("FILE_READ_ERROR", f"cannot open ancestor {comp}") from exc
            os.close(cur_fd)
            cur_fd = nxt
        return cur_fd, leaf
    except BaseException:
        os.close(cur_fd)
        raise


def read_regular_bytes_atomic(path, max_bytes, not_found_code="FILE_NOT_FOUND", too_large_code="FILE_TOO_LARGE", allow_hardlink=False):
    dfd, leaf = _open_parent_dir_fd(path, not_found_code=not_found_code)
    try:
        try:
            fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=dfd)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise S92VerifyError("SYMLINK_FORBIDDEN", f"symlink forbidden: {leaf}") from exc
            if exc.errno in (errno.ENOENT, errno.ENOTDIR, errno.EISDIR):
                raise S92VerifyError(not_found_code, f"regular file not found: {leaf}") from exc
            raise S92VerifyError("FILE_READ_ERROR", f"cannot open file {leaf}") from exc
        try:
            st = os.fstat(fd)
            require_ok(stat.S_ISREG(st.st_mode), not_found_code, f"not a regular file: {leaf}")
            if not allow_hardlink:
                require_ok(st.st_nlink == 1, "HARDLINK_FORBIDDEN", f"hardlink forbidden: {leaf}")
            chunks = []
            total = 0
            while True:
                try:
                    chunk = os.read(fd, _READ_CHUNK_BYTES)
                except OSError as exc:
                    raise S92VerifyError("FILE_READ_ERROR", f"cannot read file {leaf}") from exc
                if not chunk:
                    break
                total += len(chunk)
                require_ok(total <= max_bytes, too_large_code, f"file exceeds {max_bytes} bytes")
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)
    finally:
        os.close(dfd)


def write_regular_bytes_atomic_0600(path, data):
    require_ok(type(data) is bytes, "INVALID_BYTES", "data must be bytes")
    dfd, leaf = _open_parent_dir_fd(path, create_parents=True, not_found_code="FILE_WRITE_ERROR")
    tmp_name = None
    try:
        try:
            lst = os.lstat(leaf, dir_fd=dfd)
            require_ok(not stat.S_ISLNK(lst.st_mode), "SYMLINK_FORBIDDEN", f"target is symlink: {leaf}")
            require_ok(stat.S_ISREG(lst.st_mode), "FILE_WRITE_ERROR", f"target not regular file: {leaf}")
            require_ok(lst.st_nlink <= 1, "HARDLINK_FORBIDDEN", f"target has hardlinks: {leaf}")
        except FileNotFoundError:
            pass
        with _TEMP_NAME_LOCK:
            tmp_name = f".{leaf}.tmp.{secrets.token_hex(8)}"
            fd = os.open(
                tmp_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_NONBLOCK,
                0o600,
                dir_fd=dfd,
            )
        try:
            os.fchmod(fd, 0o600)
            view = memoryview(data)
            written = 0
            while written < len(data):
                written += os.write(fd, view[written:])
            os.fsync(fd)
            tst = os.fstat(fd)
            require_ok(tst.st_nlink == 1, "HARDLINK_FORBIDDEN", "temp file hardlinked")
        finally:
            os.close(fd)
        os.replace(tmp_name, leaf, src_dir_fd=dfd, dst_dir_fd=dfd)
        tmp_name = None
        os.fsync(dfd)
    finally:
        if tmp_name is not None:
            try:
                os.unlink(tmp_name, dir_fd=dfd)
            except OSError:
                pass
        os.close(dfd)


# ---------------------------------------------------------------------------
# Raising Field-Complete Secondary Semantic Audit (SEC Surface)
# ---------------------------------------------------------------------------

def _require_dec6_close(actual_dec6, expected_frac, code, label):
    val = require_dec6_fraction(actual_dec6, label)
    require_ok(abs(val - expected_frac) < Fraction(1, 100000), code, f"{label} arithmetic drift")
    return val


def _require_non_empty_str(val, code, label):
    _require_str_no_surrogate(val, label)
    require_ok(len(val.strip()) > 0, code, f"{label} must be non-empty")
    return val


def _require_dec6_ratio_consistent(num_str, den_str, ratio_str, code, label):
    eps = Fraction(1, 1_000_000)
    num = require_dec6_fraction(num_str, f"{label}.num")
    den = require_dec6_fraction(den_str, f"{label}.den")
    rat = require_dec6_fraction(ratio_str, f"{label}.rat")
    require_ok(num > 0, f"{code}_NUM_POS", f"{label} numerator must be > 0")
    require_ok(den > eps, f"{code}_DEN_POS", f"{label} denominator must be > eps")
    lo = (num - eps) / (den + eps)
    hi = (num + eps) / (den - eps)
    require_ok(lo <= rat, f"{code}_LO", f"{label} ratio below dec6 interval")
    require_ok(rat <= hi, f"{code}_HI", f"{label} ratio above dec6 interval")
    return num, den, rat


def _require_exact_dict_keys(obj, req_keys, code, label):
    require_ok(type(obj) is dict, f"{code}_TYPE", f"{label} must be strict dict")
    require_ok(frozenset(obj.keys()) == req_keys, code, f"{label} keys mismatch")
    return obj


def _require_exact_list_len(obj, expected_len, code, label):
    require_ok(type(obj) is list, f"{code}_TYPE", f"{label} must be strict list")
    require_ok(len(obj) == expected_len, code, f"{label} length != {expected_len}")
    return obj


def _audit_ladder(ladder, label):
    req = frozenset({
        "edge_loss_pair",
        "edge_loss_exact",
        "edge_loss_dec6",
        "edge_retention_exact",
        "edge_retention_dec6",
        "k1_exp1_survival_dec6",
        "k1_exp1_collapse_dec6",
        "k2_exp3_survival_dec6",
        "k2_exp3_collapse_dec6",
        "k3_exp6_survival_dec6",
        "k3_exp6_collapse_dec6",
        "k4_exp10_survival_dec6",
        "k4_exp10_collapse_dec6",
    })
    _require_exact_dict_keys(ladder, req, "LADDER_KEYS", label)
    pair = _require_exact_list_len(ladder["edge_loss_pair"], 2, "LADDER_PAIR", f"{label}.pair")
    lost = require_exact_int(pair[0], f"{label}.lost", min_val=1)
    tot = require_exact_int(pair[1], f"{label}.tot", min_val=lost + 1)
    loss_f = Fraction(lost, tot)
    ret_f = Fraction(1, 1) - loss_f
    require_ok(require_frac_str(ladder["edge_loss_exact"], f"{label}.loss") == loss_f, "LADDER_LOSS_EQ", f"{label} loss mismatch")
    require_ok(require_frac_str(ladder["edge_retention_exact"], f"{label}.ret") == ret_f, "LADDER_RET_EQ", f"{label} ret mismatch")
    require_ok(ladder["edge_loss_dec6"] == O.format_exact_decimal(loss_f), "LADDER_LOSS_DEC", f"{label} loss dec6")
    require_ok(ladder["edge_retention_dec6"] == O.format_exact_decimal(ret_f), "LADDER_RET_DEC", f"{label} ret dec6")
    for k, exp in ((1, 1), (2, 3), (3, 6), (4, 10)):
        surv = ret_f ** exp
        coll = Fraction(1, 1) - surv
        require_ok(ladder[f"k{k}_exp{exp}_survival_dec6"] == O.format_exact_decimal(surv), "LADDER_SURV", f"{label} k{k}")
        require_ok(ladder[f"k{k}_exp{exp}_collapse_dec6"] == O.format_exact_decimal(coll), "LADDER_COLL", f"{label} k{k}")
    return loss_f


def _audit_holm_block(block, expected_m, label, expected_raw_p=None):
    req = frozenset({"test_count", "alpha_exact", "adjusted_p_exact", "adjusted_p_dec6", "rejected_at_alpha", "rejected_count"})
    _require_exact_dict_keys(block, req, "HOLM_KEYS", label)
    require_exact_int(block["test_count"], f"{label}.m", min_val=expected_m, max_val=expected_m)
    require_ok(require_frac_str(block["alpha_exact"], f"{label}.alpha") == Fraction(1, 20), "HOLM_ALPHA", f"{label} alpha")
    adj_ex = block["adjusted_p_exact"]
    adj_d6 = block["adjusted_p_dec6"]
    rej = block["rejected_at_alpha"]
    require_ok(type(adj_ex) is dict, "HOLM_EX_TYPE", f"{label} ex dict")
    require_ok(type(adj_d6) is dict, "HOLM_D6_TYPE", f"{label} d6 dict")
    require_ok(type(rej) is dict, "HOLM_REJ_TYPE", f"{label} rej dict")
    require_ok(len(adj_ex) == expected_m, "HOLM_EX_LEN", f"{label} ex len")
    require_ok(set(adj_ex.keys()) == set(adj_d6.keys()), "HOLM_D6_KEYS", f"{label} d6 keys")
    require_ok(set(adj_ex.keys()) == set(rej.keys()), "HOLM_REJ_KEYS", f"{label} rej keys")
    cnt = 0
    for k in adj_ex:
        pf = require_frac_str(adj_ex[k], f"{label}.{k}")
        require_ok(adj_d6[k] == O.format_exact_decimal(pf), "HOLM_DEC", f"{label}.{k} dec6")
        rb = require_exact_bool(rej[k], f"{label}.{k}.rej", expected=(pf <= Fraction(1, 20)))
        if rb:
            cnt += 1
    require_exact_int(block["rejected_count"], f"{label}.rej_cnt", min_val=cnt, max_val=cnt)
    if expected_raw_p is not None:
        recomp = O.holm_bonferroni_exact(expected_raw_p)
        require_ok(block == recomp, "HOLM_RECOMP_EQ", f"{label} Holm recomputation mismatch")
    return cnt


def secondary_audit_payload(payload):
    """Independent raising field-complete semantic validator for Raw-Arabic Scientific Mesh payload."""
    validate_json_tree_iterative(payload)
    _require_exact_dict_keys(payload, PAYLOAD_KEYS, "PAYLOAD_KEYS_MISMATCH", "payload")
    require_ok(payload["schema_version"] == O.SCHEMA_VERSION, "BAD_SCHEMA_VERSION", "schema_version mismatch")
    require_ok(payload["track_id"] == O.TRACK_ID, "BAD_TRACK_ID", "track_id mismatch")
    require_exact_bool(payload["all_gates_passed"], "all_gates_passed", expected=True)
    require_ok(
        payload["verdict"] == "S92_RAW_ARABIC_K12_MESH_AND_SILO_COLLAPSE_CERTIFIED",
        "BAD_VERDICT",
        "unexpected verdict",
    )

    nov = _require_exact_dict_keys(
        payload["novelty_classification"],
        frozenset({"prior_art_n0", "max_novelty", "n2_claims_count", "methodology"}),
        "NOVELTY_KEYS",
        "novelty_classification",
    )
    prior_n0 = _require_str_no_surrogate(nov["prior_art_n0"], "prior_art_n0")
    require_ok("bayt-al-hikma" in prior_n0, "MISSING_N0_CREDIT", "must credit bayt-al-hikma as N0")
    require_ok(nov["max_novelty"] == "N1", "BAD_NOVELTY_TIER", "max novelty must be N1")
    require_exact_int(nov["n2_claims_count"], "n2_claims_count", min_val=0, max_val=0)
    require_ok(nov["methodology"] == "OWN_TERMS_FIRST_PURE_ARABIC_PRIMARY_TEXTS", "BAD_METHOD", "bad methodology")

    ap = _require_exact_dict_keys(
        payload["anchor_pin"],
        frozenset({
            "anchor_schema_version",
            "anchor_internal_sha256",
            "multishuffle_b",
            "local_window_w",
            "matched_local_tokens",
            "top_func_stripped_count",
        }),
        "ANCHOR_PIN_KEYS",
        "anchor_pin",
    )
    require_ok(ap["anchor_schema_version"] == "s92-raw-arabic-anchor/v1", "ANCHOR_SCHEMA", "bad anchor schema")
    ap_sha = require_sha256_hex(ap["anchor_internal_sha256"], "anchor_internal_sha256")
    require_ok(
        hmac.compare_digest(ap_sha, EXPECTED_ANCHOR_INTERNAL_SHA256),
        "ANCHOR_INTERNAL_SHA_MISMATCH",
        "anchor_internal_sha256 pin mismatch",
    )
    require_exact_int(ap["multishuffle_b"], "multishuffle_b", min_val=250, max_val=250)
    require_exact_int(ap["local_window_w"], "local_window_w", min_val=20, max_val=20)
    require_exact_int(ap["matched_local_tokens"], "matched_local_tokens", min_val=1000)
    require_exact_int(ap["top_func_stripped_count"], "top_func_stripped_count", min_val=10)

    n0 = _require_exact_dict_keys(
        payload["n0_bayt_al_hikma_prior_art"],
        frozenset({
            "continuum_audit_id",
            "continuum_cert_file_sha256",
            "continuum_cert_internal_sha256",
            "lexicon_audit_id",
            "lexicon_cert_file_sha256",
            "lexicon_cert_internal_sha256",
            "higher_order_collapse_ladders",
        }),
        "N0_KEYS",
        "n0_bayt_al_hikma_prior_art",
    )
    require_ok(n0["continuum_audit_id"] == "AUDIT-091-V2", "N0_CONT_ID", "expected AUDIT-091-V2")
    require_ok(n0["lexicon_audit_id"] == "AUDIT-094-V2", "N0_LEX_ID", "expected AUDIT-094-V2")
    c_fsha = require_sha256_hex(n0["continuum_cert_file_sha256"], "continuum_cert_file_sha256")
    c_isha = require_sha256_hex(n0["continuum_cert_internal_sha256"], "continuum_cert_internal_sha256")
    l_fsha = require_sha256_hex(n0["lexicon_cert_file_sha256"], "lexicon_cert_file_sha256")
    l_isha = require_sha256_hex(n0["lexicon_cert_internal_sha256"], "lexicon_cert_internal_sha256")
    require_ok(hmac.compare_digest(c_fsha, EXPECTED_BAYT_CONTINUUM_FILE_SHA256), "N0_CONT_FILE_SHA", "continuum file sha mismatch")
    require_ok(hmac.compare_digest(c_isha, EXPECTED_BAYT_CONTINUUM_INTERNAL_SHA256), "N0_CONT_INT_SHA", "continuum internal sha mismatch")
    require_ok(hmac.compare_digest(l_fsha, EXPECTED_BAYT_LEXICON_FILE_SHA256), "N0_LEX_FILE_SHA", "lexicon file sha mismatch")
    require_ok(hmac.compare_digest(l_isha, EXPECTED_BAYT_LEXICON_INTERNAL_SHA256), "N0_LEX_INT_SHA", "lexicon internal sha mismatch")
    ladders = _require_exact_dict_keys(
        n0["higher_order_collapse_ladders"],
        frozenset({
            "sahih_7root",
            "pickthall_7root",
            "sahih_15root_same_lemma",
            "sahih_15root_cross_lemma",
            "pickthall_15root_same_lemma",
            "pickthall_15root_cross_lemma",
        }),
        "N0_LADDER_KEYS",
        "ladders",
    )
    s_same = _audit_ladder(ladders["sahih_15root_same_lemma"], "sahih_same")
    s_cross = _audit_ladder(ladders["sahih_15root_cross_lemma"], "sahih_cross")
    p_same = _audit_ladder(ladders["pickthall_15root_same_lemma"], "pick_same")
    p_cross = _audit_ladder(ladders["pickthall_15root_cross_lemma"], "pick_cross")
    s7_ret = Fraction(1, 1) - _audit_ladder(ladders["sahih_7root"], "sahih_7root")
    p7_ret = Fraction(1, 1) - _audit_ladder(ladders["pickthall_7root"], "pickthall_7root")
    require_ok(s_cross > s_same, "SAHIH_CROSS_AMPLIFICATION", "sahih cross must exceed same")
    require_ok(p_cross > p_same, "PICK_CROSS_AMPLIFICATION", "pickthall cross must exceed same")

    p1 = _require_exact_dict_keys(
        payload["pillar1_raw_arabic_k12_mesh"],
        frozenset({
            "treatise_count",
            "discipline_count",
            "total_raw_arabic_tokens",
            "rasm_c2_inflation_treatises",
            "treatises",
            "within_treatise_w20_b250",
            "local_dotless_rasm_lift_reversed_vs_raw",
            "k12_cross_treatise_layers",
            "holm_k12_vocab_null_4layers",
            "holm_k12_discipline_perm_4layers",
            "cross_treatise_full_4layer_lift_reversal",
            "k12_simplicial_complex",
            "schur_conductance_and_silo_collapse",
        }),
        "P1_KEYS",
        "pillar1",
    )
    require_exact_int(p1["treatise_count"], "treatise_count", min_val=12, max_val=12)
    require_exact_int(p1["discipline_count"], "discipline_count", min_val=6, max_val=6)
    require_exact_int(p1["rasm_c2_inflation_treatises"], "rasm_c2_inflation_treatises", min_val=12, max_val=12)
    require_exact_bool(p1["local_dotless_rasm_lift_reversed_vs_raw"], "local_rasm_rev", expected=True)
    require_exact_bool(p1["cross_treatise_full_4layer_lift_reversal"], "cross_4layer_rev", expected=True)

    t_list = _require_exact_list_len(p1["treatises"], 12, "P1_TREATISES_LEN", "treatises")
    t_req = frozenset({
        "id", "discipline", "author", "title_en", "rel_path", "bytes", "sha256",
        "token_count", "vocab_raw", "vocab_dotless_rasm", "vocab_stem_v1", "vocab_stem_v2",
        "rasm_c2_inflation_dec6",
    })
    tok_sum = 0
    seen_ids = set()
    seen_discs = set()
    for t in t_list:
        _require_exact_dict_keys(t, t_req, "TREATISE_KEYS", "treatise")
        tid = _require_non_empty_str(t["id"], "TREATISE_STR", "t.id")
        disc = _require_non_empty_str(t["discipline"], "TREATISE_STR", "t.discipline")
        _require_non_empty_str(t["author"], "TREATISE_STR", "t.author")
        _require_non_empty_str(t["title_en"], "TREATISE_STR", "t.title_en")
        _require_non_empty_str(t["rel_path"], "TREATISE_STR", "t.rel_path")
        require_ok(tid not in seen_ids, "DUP_TREATISE_ID", "duplicate treatise id")
        seen_ids.add(tid)
        seen_discs.add(disc)
        require_exact_int(t["bytes"], "t.bytes", min_val=1)
        require_sha256_hex(t["sha256"], "t.sha256")
        tok_cnt = require_exact_int(t["token_count"], "t.tokens", min_val=1000)
        tok_sum += tok_cnt
        vr = require_exact_int(t["vocab_raw"], "t.v_raw", min_val=1, max_val=tok_cnt)
        vm = require_exact_int(t["vocab_dotless_rasm"], "t.v_rasm", min_val=1)
        vs1 = require_exact_int(t["vocab_stem_v1"], "t.v_s1", min_val=1, max_val=vr)
        require_exact_int(t["vocab_stem_v2"], "t.v_s2", min_val=1, max_val=vs1)
        require_ok(vm < vr, "RASM_VOCAB_COLLAPSE", "dotless rasm vocab must shrink vs raw")
        require_ok(require_dec6_fraction(t["rasm_c2_inflation_dec6"], "t.infl") > Fraction(1, 1), "RASM_INFL_GT1", "infl <= 1")
    require_ok(len(seen_discs) == 6, "P1_DISCS", "expected 6 disciplines")
    actual_meta = tuple((t["id"], t["discipline"], t["author"], t["title_en"], t["rel_path"]) for t in t_list)
    require_ok(actual_meta == EXPECTED_TREATISE_METADATA, "TREATISE_META_MISMATCH", "treatise metadata pin mismatch")
    require_exact_int(p1["total_raw_arabic_tokens"], "total_tokens", min_val=tok_sum, max_val=tok_sum)
    actual_pins = tuple((t["id"], t["bytes"], t["sha256"], t["token_count"]) for t in t_list)
    require_ok(actual_pins == EXPECTED_TREATISE_PINS, "TREATISE_PIN_MISMATCH", "treatise bytes/sha256/token_count pin mismatch")

    w20 = _require_exact_dict_keys(p1["within_treatise_w20_b250"], frozenset(O.LAYERS), "W20_LAYERS", "w20")
    w20_req = frozenset({
        "pooled_jaccard_obs_dec6", "pooled_jaccard_null_dec6", "pooled_jaccard_lift_dec6",
        "pooled_r2_obs_dec6", "pooled_r2_null_dec6", "pooled_r2_lift_dec6",
        "holm_jaccard_rejected_count", "holm_r2_rejected_count", "holm_jaccard_battani_p_adj_dec6",
    })
    for lyr in O.LAYERS:
        wl = _require_exact_dict_keys(w20[lyr], w20_req, "W20_CELL_KEYS", f"w20.{lyr}")
        jo, jn, jl = _require_dec6_ratio_consistent(
            wl["pooled_jaccard_obs_dec6"],
            wl["pooled_jaccard_null_dec6"],
            wl["pooled_jaccard_lift_dec6"],
            "W20_JL_RATIO",
            f"w20.{lyr}.j",
        )
        ro, rn, rl = _require_dec6_ratio_consistent(
            wl["pooled_r2_obs_dec6"],
            wl["pooled_r2_null_dec6"],
            wl["pooled_r2_lift_dec6"],
            "W20_RL_RATIO",
            f"w20.{lyr}.r",
        )
        require_ok(jo <= Fraction(1, 1), "W20_JO_LE1", f"w20.{lyr} jaccard obs > 1")
        require_ok(jn < Fraction(1, 1), "W20_JN_LT1", f"w20.{lyr} jaccard null >= 1")
        require_ok(ro <= Fraction(1, 1), "W20_RO_LE1", f"w20.{lyr} r2 obs > 1")
        require_ok(rn < Fraction(1, 1), "W20_RN_LT1", f"w20.{lyr} r2 null >= 1")
        require_ok(jl > Fraction(1, 1), "W20_JL", f"w20.{lyr}")
        require_ok(rl > Fraction(1, 1), "W20_RL", f"w20.{lyr}")
        require_exact_int(wl["holm_jaccard_rejected_count"], f"w20.{lyr}.hj", min_val=11, max_val=12)
        require_exact_int(wl["holm_r2_rejected_count"], f"w20.{lyr}.hr", min_val=11, max_val=12)
        bat_p = require_dec6_fraction(wl["holm_jaccard_battani_p_adj_dec6"], f"w20.{lyr}.bat")
        require_ok(bat_p > 0 and bat_p <= Fraction(1, 1), "W20_BAT_P_RANGE", f"w20.{lyr} battani p out of (0,1]")
    require_ok(
        require_dec6_fraction(w20["dotless_rasm"]["pooled_jaccard_obs_dec6"], "w20.m.jo")
        > require_dec6_fraction(w20["raw"]["pooled_jaccard_obs_dec6"], "w20.r.jo"),
        "W20_RASM_ABS_ORDER",
        "dotless_rasm abs obs must exceed raw",
    )
    require_ok(
        require_dec6_fraction(w20["dotless_rasm"]["pooled_jaccard_lift_dec6"], "w20.m.jl")
        < require_dec6_fraction(w20["raw"]["pooled_jaccard_lift_dec6"], "w20.r.jl"),
        "W20_RASM_LIFT_REV",
        "dotless_rasm lift must drop below raw",
    )
    require_ok(
        require_dec6_fraction(w20["dotless_rasm"]["pooled_r2_obs_dec6"], "w20.m.ro")
        > require_dec6_fraction(w20["raw"]["pooled_r2_obs_dec6"], "w20.r.ro"),
        "W20_RASM_R2_ABS_ORDER",
        "dotless_rasm r2 abs obs must exceed raw",
    )
    require_ok(
        require_dec6_fraction(w20["dotless_rasm"]["pooled_r2_lift_dec6"], "w20.m.rl")
        < require_dec6_fraction(w20["raw"]["pooled_r2_lift_dec6"], "w20.r.rl"),
        "W20_RASM_R2_LIFT_REV",
        "dotless_rasm r2 lift must drop below raw",
    )

    k12l = _require_exact_dict_keys(p1["k12_cross_treatise_layers"], frozenset(O.LAYERS), "K12_LAYERS", "k12")
    k12_req = frozenset({
        "shared_vocab_size", "within_discipline_r2_dec6", "cross_discipline_r2_dec6",
        "within_to_cross_ratio_dec6", "discipline_perm_ge_count", "discipline_perm_raw_p_exact",
        "top500_obs_r2_dec6", "top500_null_r2_dec6", "top500_vocab_lift_dec6", "top500_vocab_ge_count",
    })
    cross_abs = {}
    cross_lift = {}
    k12_disc_raw_p = {}
    k12_voc_raw_p = {}
    for lyr in O.LAYERS:
        kl = _require_exact_dict_keys(k12l[lyr], k12_req, "K12_CELL_KEYS", f"k12.{lyr}")
        require_exact_int(kl["shared_vocab_size"], f"k12.{lyr}.vs", min_val=1000)
        wr, cr, rat = _require_dec6_ratio_consistent(
            kl["within_discipline_r2_dec6"],
            kl["cross_discipline_r2_dec6"],
            kl["within_to_cross_ratio_dec6"],
            "K12_RAT_EQ",
            f"k12.{lyr}.wc",
        )
        require_ok(wr > cr, "K12_WITHIN_GT_CROSS", f"k12.{lyr}")
        require_ok(rat > Fraction(1, 1), "K12_RAT", f"k12.{lyr}")
        dge = require_exact_int(kl["discipline_perm_ge_count"], f"k12.{lyr}.dge", min_val=0, max_val=250)
        dp = require_frac_str(kl["discipline_perm_raw_p_exact"], f"k12.{lyr}.dp")
        require_ok(dp == Fraction(dge + 1, 251), "K12_DISC_P_EQ", f"k12.{lyr} raw p != (ge+1)/251")
        vge = require_exact_int(kl["top500_vocab_ge_count"], f"k12.{lyr}.vge", min_val=0, max_val=0)
        _, _, vl = _require_dec6_ratio_consistent(
            kl["top500_obs_r2_dec6"],
            kl["top500_null_r2_dec6"],
            kl["top500_vocab_lift_dec6"],
            "K12_TOP500_RATIO",
            f"k12.{lyr}.t500",
        )
        cross_abs[lyr] = cr
        cross_lift[lyr] = vl
        k12_disc_raw_p[lyr] = dp
        k12_voc_raw_p[lyr] = Fraction(vge + 1, 251)
    require_ok(
        cross_abs["raw"] < cross_abs["dotless_rasm"] < cross_abs["stem_v1"] < cross_abs["stem_v2"],
        "K12_ABS_CHAIN",
        "abs chain mismatch",
    )
    require_ok(
        cross_lift["raw"] > cross_lift["dotless_rasm"] > cross_lift["stem_v1"] > cross_lift["stem_v2"],
        "K12_LIFT_REV_CHAIN",
        "lift reversal chain mismatch",
    )
    _audit_holm_block(p1["holm_k12_vocab_null_4layers"], 4, "holm_k12_vocab", expected_raw_p=k12_voc_raw_p)
    _audit_holm_block(p1["holm_k12_discipline_perm_4layers"], 4, "holm_k12_disc", expected_raw_p=k12_disc_raw_p)

    scx = _require_exact_dict_keys(
        p1["k12_simplicial_complex"],
        frozenset({"k1_edges", "k2_triangles", "k3_tetrahedra", "k4_five_cells"}),
        "SIMP_KEYS",
        "simplicial",
    )
    s_cell_req = frozenset({
        "total_simplices", "cross_discipline_simplices", "cross_discipline_share_exact",
        "cross_discipline_share_dec6", "min_bottleneck_weight", "max_bottleneck_weight",
        "mean_bottleneck_weight_dec6",
    })
    for key, exp_tot, exp_cross in (
        ("k1_edges", 66, 56),
        ("k2_triangles", 220, 215),
        ("k3_tetrahedra", 495, 494),
        ("k4_five_cells", 792, 792),
    ):
        cell = _require_exact_dict_keys(scx[key], s_cell_req, "SIMP_CELL_KEYS", key)
        require_exact_int(cell["total_simplices"], f"{key}.tot", min_val=exp_tot, max_val=exp_tot)
        require_exact_int(cell["cross_discipline_simplices"], f"{key}.cr", min_val=exp_cross, max_val=exp_cross)
        sh_f = Fraction(exp_cross, exp_tot)
        require_ok(
            require_frac_str(cell["cross_discipline_share_exact"], f"{key}.sh") == sh_f,
            "SIMP_SHARE",
            key,
        )
        require_ok(
            cell["cross_discipline_share_dec6"] == O.format_exact_decimal(sh_f),
            "SIMP_SHARE_DEC",
            key,
        )
        mean_b = require_dec6_fraction(cell["mean_bottleneck_weight_dec6"], f"{key}.mean")
        mn_b = require_exact_int(cell["min_bottleneck_weight"], f"{key}.min", min_val=1)
        mx_b = require_exact_int(cell["max_bottleneck_weight"], f"{key}.max", min_val=mn_b)
        require_ok(Fraction(mn_b, 1) <= mean_b, "SIMP_MEAN_LO", key)
        require_ok(mean_b <= Fraction(mx_b, 1), "SIMP_MEAN_HI", key)

    sch = _require_exact_dict_keys(
        p1["schur_conductance_and_silo_collapse"],
        frozenset({
            "raw_arabic_k12",
            "uniform_sahih_thinning",
            "uniform_pickthall_thinning",
            "uniform_bilingual_catalog_thinning",
            "heterogeneous_english_silo_cut_k12",
        }),
        "SCHUR_KEYS",
        "schur",
    )
    raw_s = _require_exact_dict_keys(
        sch["raw_arabic_k12"],
        frozenset({
            "laplacian_inertia", "foster_sum_exact", "strictly_compounded_edges",
            "min_compounding_ratio_dec6", "max_compounding_ratio_dec6",
            "min_ceff_dec6", "max_ceff_dec6", "mean_ceff_dec6",
            "mean_within_discipline_ceff_dec6", "mean_cross_discipline_ceff_dec6",
        }),
        "SCHUR_RAW_KEYS",
        "raw_schur",
    )
    require_ok(raw_s["laplacian_inertia"] == [11, 0, 1], "RAW_INERTIA", "inertia must be [11,0,1]")
    require_ok(raw_s["foster_sum_exact"] == "11/1", "RAW_FOSTER", "Foster sum must be 11/1")
    require_exact_int(raw_s["strictly_compounded_edges"], "comp_edges", min_val=66, max_val=66)
    min_comp = require_dec6_fraction(raw_s["min_compounding_ratio_dec6"], "min_comp")
    max_comp = require_dec6_fraction(raw_s["max_compounding_ratio_dec6"], "max_comp")
    require_ok(min_comp > Fraction(1, 1), "COMP_GT1", "comp <= 1")
    require_ok(min_comp <= max_comp, "COMP_RANGE", "min_comp > max_comp")
    min_ceff = require_dec6_fraction(raw_s["min_ceff_dec6"], "min_ceff")
    max_ceff = require_dec6_fraction(raw_s["max_ceff_dec6"], "max_ceff")
    raw_mean_ceff = require_dec6_fraction(raw_s["mean_ceff_dec6"], "raw_mean_ceff")
    raw_within_ceff = require_dec6_fraction(raw_s["mean_within_discipline_ceff_dec6"], "raw_within_ceff")
    raw_cross_ceff = require_dec6_fraction(raw_s["mean_cross_discipline_ceff_dec6"], "raw_cross_ceff")
    require_ok(min_ceff > 0, "RAW_MIN_CEFF_POS", "min_ceff <= 0")
    require_ok(min_ceff <= raw_mean_ceff, "RAW_CEFF_LO", "min_ceff > mean_ceff")
    require_ok(raw_mean_ceff <= max_ceff, "RAW_CEFF_HI", "mean_ceff > max_ceff")
    _require_dec6_close(
        raw_s["mean_ceff_dec6"],
        (10 * raw_within_ceff + 56 * raw_cross_ceff) / 66,
        "RAW_WEIGHTED_MEAN",
        "raw.mean",
    )

    uni_req = frozenset({"retention_exact", "retention_dec6", "mean_ceff_dec6", "effective_resistance_inflation_dec6"})
    uni_rets = {}
    for uk in ("uniform_sahih_thinning", "uniform_pickthall_thinning", "uniform_bilingual_catalog_thinning"):
        ub = _require_exact_dict_keys(sch[uk], uni_req, "UNI_SCHUR_KEYS", uk)
        rf = require_frac_str(ub["retention_exact"], f"{uk}.r")
        require_ok(rf > 0 and rf < 1, "UNI_R_RANGE", uk)
        require_ok(ub["retention_dec6"] == O.format_exact_decimal(rf), "UNI_R_DEC", uk)
        mc = require_dec6_fraction(ub["mean_ceff_dec6"], f"{uk}.mc")
        require_ok(mc < raw_mean_ceff, "UNI_COLLAPSE", uk)
        _require_dec6_close(ub["mean_ceff_dec6"], raw_mean_ceff * rf, "UNI_CEFF_SCALE", f"{uk}.mc")
        require_ok(
            ub["effective_resistance_inflation_dec6"] == O.format_exact_decimal(Fraction(1, 1) / rf),
            "UNI_RINFL",
            uk,
        )
        uni_rets[uk] = rf
    require_ok(uni_rets["uniform_sahih_thinning"] == s7_ret, "UNI_SAHIH_RET_PIN", "sahih uniform retention mismatch")
    require_ok(uni_rets["uniform_pickthall_thinning"] == p7_ret, "UNI_PICK_RET_PIN", "pickthall uniform retention mismatch")

    het = _require_exact_dict_keys(
        sch["heterogeneous_english_silo_cut_k12"],
        frozenset({
            "within_edge_retention_exact", "within_edge_retention_dec6",
            "cross_edge_retention_exact", "cross_edge_retention_dec6",
            "laplacian_inertia", "foster_sum_exact", "strictly_collapsed_edges",
            "mean_ceff_dec6", "mean_within_ceff_dec6", "mean_cross_ceff_dec6",
            "overall_ceff_collapse_dec6", "within_ceff_collapse_dec6", "cross_ceff_collapse_dec6",
        }),
        "HET_KEYS",
        "hetero",
    )
    require_ok(het["laplacian_inertia"] == [11, 0, 1], "HET_INERTIA", "het inertia")
    require_ok(het["foster_sum_exact"] == "11/1", "HET_FOSTER", "het foster")
    require_exact_int(het["strictly_collapsed_edges"], "het_coll_edges", min_val=66, max_val=66)
    het_rw = require_frac_str(het["within_edge_retention_exact"], "het.rw")
    het_rc = require_frac_str(het["cross_edge_retention_exact"], "het.rc")
    require_ok(het["within_edge_retention_dec6"] == O.format_exact_decimal(het_rw), "HET_RW_DEC", "het rw dec6")
    require_ok(het["cross_edge_retention_dec6"] == O.format_exact_decimal(het_rc), "HET_RC_DEC", "het rc dec6")
    require_ok(het_rc > 0, "HET_RC_POS", "cross retention must be > 0")
    require_ok(het_rc < het_rw, "HET_RET_ORDER", "cross retention must be < within retention")
    require_ok(het_rw < Fraction(1, 1), "HET_RW_LT1", "within retention must be < 1")
    het_m = require_dec6_fraction(het["mean_ceff_dec6"], "het.m")
    het_mw = require_dec6_fraction(het["mean_within_ceff_dec6"], "het.mw")
    het_mc = require_dec6_fraction(het["mean_cross_ceff_dec6"], "het.mc")
    require_ok(het_mw > 0, "HET_MW_POS", "het mean_within_ceff must be > 0")
    require_ok(het_mc > 0, "HET_MC_POS", "het mean_cross_ceff must be > 0")
    _require_dec6_close(
        het["mean_ceff_dec6"],
        (10 * het_mw + 56 * het_mc) / 66,
        "HET_WEIGHTED_MEAN",
        "het.mean",
    )
    het_ov_c = _require_dec6_close(
        het["overall_ceff_collapse_dec6"],
        Fraction(1, 1) - het_m / raw_mean_ceff,
        "HET_OV_COLL_EQ",
        "het.oc",
    )
    het_w_c = _require_dec6_close(
        het["within_ceff_collapse_dec6"],
        Fraction(1, 1) - het_mw / raw_within_ceff,
        "HET_W_COLL_EQ",
        "het.wc",
    )
    het_cr_c = _require_dec6_close(
        het["cross_ceff_collapse_dec6"],
        Fraction(1, 1) - het_mc / raw_cross_ceff,
        "HET_CR_COLL_EQ",
        "het.cc",
    )
    require_ok(het_w_c > 0, "HET_W_COLL_POS", "within collapse must be > 0")
    require_ok(het_cr_c > het_w_c, "HET_COLL_ORDER", "cross collapse must exceed within collapse")
    require_ok(het_cr_c < Fraction(1, 1), "HET_CR_COLL_LT1", "cross collapse must be < 1")
    require_ok(het_ov_c > 0, "HET_OV_COLL_POS", "overall collapse must be > 0")
    require_ok(het_ov_c < Fraction(1, 1), "HET_OV_COLL_LT1", "overall collapse must be < 1")

    p2 = _require_exact_dict_keys(
        payload["pillar2_bridges_and_law5_obstruction"],
        frozenset({
            "algorithmic_qualifying_stem_v1_count",
            "thematic_selection_rule",
            "thematic_root_count",
            "thematic_universal_12_of_12_count",
            "thematic_honest_partial_count",
            "thematic_roots",
            "rasm_homography_witnesses_verified",
            "rasm_top10_total_delta_s2",
        }),
        "P2_KEYS",
        "pillar2",
    )
    require_exact_int(p2["algorithmic_qualifying_stem_v1_count"], "alg_cnt", min_val=100)
    require_ok(p2["thematic_selection_rule"] == "author_selected_thematic_set_disclosed", "P2_RULE", "bad rule")
    require_exact_int(p2["thematic_root_count"], "tr_cnt", min_val=8, max_val=8)
    u12 = require_exact_int(p2["thematic_universal_12_of_12_count"], "u12", min_val=1, max_val=7)
    hp = require_exact_int(p2["thematic_honest_partial_count"], "hp", min_val=1, max_val=7)
    require_ok(u12 + hp == 8, "P2_ROOT_PARTITION", "u12 + hp != 8")
    t_roots = _require_exact_list_len(p2["thematic_roots"], 8, "P2_ROOTS_LEN", "thematic_roots")
    r_req = frozenset({
        "root_key", "stem_v1_total", "stem_v1_docs", "stem_v1_disciplines",
        "stem_v2_total", "stem_v2_docs", "zero_treatises_s1_count", "universal_all_12_s1",
    })
    u12_seen = 0
    seen_root_keys = set()
    for r in t_roots:
        _require_exact_dict_keys(r, r_req, "P2_ROOT_KEYS", "root")
        rk = _require_non_empty_str(r["root_key"], "P2_ROOT_KEY_STR", "r.root_key")
        require_ok(rk not in seen_root_keys, "DUP_ROOT_KEY", "duplicate root_key")
        seen_root_keys.add(rk)
        d1 = require_exact_int(r["stem_v1_docs"], "r.s1_docs", min_val=1, max_val=12)
        require_exact_int(r["stem_v1_total"], "r.s1_tot", min_val=d1)
        require_exact_int(r["stem_v1_disciplines"], "r.s1_discs", min_val=1, max_val=min(6, d1))
        d2 = require_exact_int(r["stem_v2_docs"], "r.s2_docs", min_val=1, max_val=12)
        require_exact_int(r["stem_v2_total"], "r.s2_tot", min_val=d2)
        require_exact_int(r["zero_treatises_s1_count"], "r.zero", min_val=12 - d1, max_val=12 - d1)
        is_u = require_exact_bool(r["universal_all_12_s1"], "r.u12", expected=(d1 == 12))
        if is_u:
            u12_seen += 1
    require_ok(u12_seen == u12, "P2_U12_COUNT", "u12 count mismatch")
    actual_rkeys = tuple(r["root_key"] for r in t_roots)
    require_ok(actual_rkeys == EXPECTED_THEMATIC_ROOT_KEYS, "P2_ROOT_KEYS_PIN", "thematic root keys mismatch")
    require_exact_int(p2["rasm_homography_witnesses_verified"], "rasm_w", min_val=10, max_val=10)
    require_exact_int(p2["rasm_top10_total_delta_s2"], "rasm_ds2", min_val=1)

    p3 = _require_exact_dict_keys(
        payload["pillar3_bilingual_scientific_catalogs"],
        frozenset({
            "catalog_count",
            "entry_count",
            "overall_loss_min_dec6",
            "overall_loss_max_dec6",
            "cross_disc_loss_min_dec6",
            "cross_disc_loss_max_dec6",
            "holm_6_variants",
            "sensitivity_variants",
        }),
        "P3_KEYS",
        "pillar3",
    )
    require_exact_int(p3["catalog_count"], "cat_cnt", min_val=12, max_val=12)
    require_exact_int(p3["entry_count"], "ent_cnt", min_val=148, max_val=148)
    sv = _require_exact_dict_keys(p3["sensitivity_variants"], EXPECTED_P3_VARIANTS, "P3_SV_KEYS", "sensitivity_variants")
    sv_req = frozenset({"overall_ladder", "cross_disc_ladder", "bg_en_loss_dec6", "en_perm_le_obs_count"})
    ov_by_var = {}
    cr_by_var = {}
    bi_raw_p = {}
    for vk, vv in sv.items():
        _require_exact_dict_keys(vv, sv_req, "P3_V_KEYS", vk)
        ov_f = _audit_ladder(vv["overall_ladder"], f"bi.{vk}.ov")
        cr_f = _audit_ladder(vv["cross_disc_ladder"], f"bi.{vk}.cr")
        bg_f = require_dec6_fraction(vv["bg_en_loss_dec6"], f"bi.{vk}.bg")
        require_ok(ov_f < bg_f, "P3_OV_LT_BG", vk)
        require_ok(bg_f <= Fraction(1, 1), "P3_BG_LE1", vk)
        require_ok(cr_f > ov_f, "P3_CR_GT_OV", vk)
        ple = require_exact_int(vv["en_perm_le_obs_count"], f"bi.{vk}.ple", min_val=0, max_val=0)
        ov_by_var[vk] = ov_f
        cr_by_var[vk] = cr_f
        bi_raw_p[vk] = Fraction(ple + 1, 251)
    _audit_holm_block(p3["holm_6_variants"], 6, "holm_bilingual", expected_raw_p=bi_raw_p)
    require_ok(
        uni_rets["uniform_bilingual_catalog_thinning"] == Fraction(1, 1) - ov_by_var["stem_v1__en_pr_min4"],
        "UNI_BI_RET_PIN",
        "bilingual uniform retention mismatch",
    )
    require_ok(
        het_rc == Fraction(1, 1) - cr_by_var["stem_v1__en_pr_min4"],
        "HET_CROSS_RET_PIN",
        "heterogeneous cross retention mismatch",
    )
    ov_vals = list(ov_by_var.values())
    cr_vals = list(cr_by_var.values())
    require_ok(p3["overall_loss_min_dec6"] == O.format_exact_decimal(min(ov_vals)), "P3_OV_MIN", "ov min")
    require_ok(p3["overall_loss_max_dec6"] == O.format_exact_decimal(max(ov_vals)), "P3_OV_MAX", "ov max")
    require_ok(p3["cross_disc_loss_min_dec6"] == O.format_exact_decimal(min(cr_vals)), "P3_CR_MIN", "cr min")
    require_ok(p3["cross_disc_loss_max_dec6"] == O.format_exact_decimal(max(cr_vals)), "P3_CR_MAX", "cr max")

    ls = _require_exact_dict_keys(
        payload["lean_companion_spec"],
        frozenset({"lean_file", "theorem_count", "allowed_axioms", "theorems"}),
        "LEAN_SPEC_KEYS",
        "lean_companion_spec",
    )
    require_ok(ls["lean_file"] == "RawArabicHigherOrderMesh.lean", "LEAN_FILE_NAME", "bad lean filename")
    require_exact_int(ls["theorem_count"], "thm_cnt", min_val=len(O.EXPECTED_LEAN_THEOREMS), max_val=len(O.EXPECTED_LEAN_THEOREMS))
    require_ok(ls["allowed_axioms"] == sorted(O.ALLOWED_LEAN_AXIOMS), "LEAN_AXIOMS", "bad allowed axioms")
    require_ok(ls["theorems"] == list(O.EXPECTED_LEAN_THEOREMS), "LEAN_THEOREMS", "bad theorems list")
    return True


# ---------------------------------------------------------------------------
# Certificate Verification (FR0 / FR1 Surfaces)
# ---------------------------------------------------------------------------

def verify_certificate_object(cert, full_replay=True, anchor_path=None):
    require_ok(type(full_replay) is bool, "INVALID_FULL_REPLAY", "full_replay must be strict bool")
    validate_json_tree_iterative(cert)
    _require_exact_dict_keys(cert, CERT_KEYS, "CERT_KEYS_MISMATCH", "certificate")
    require_ok(cert["schema"] == O.SCHEMA_VERSION, "CERT_SCHEMA_MISMATCH", "schema mismatch")
    require_ok(cert["track_id"] == O.TRACK_ID, "CERT_TRACK_MISMATCH", "track_id mismatch")

    p_sha = require_sha256_hex(cert["payload_sha256"], "payload_sha256")
    c_sha = require_sha256_hex(cert["certificate_sha256"], "certificate_sha256")
    payload = cert["payload"]
    require_ok(type(payload) is dict, "PAYLOAD_NOT_DICT", "payload must be strict dict")

    calc_p_sha = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    require_ok(hmac.compare_digest(p_sha, calc_p_sha), "PAYLOAD_SHA_MISMATCH", "payload_sha256 mismatch")

    body = {k: v for k, v in cert.items() if k != "certificate_sha256"}
    calc_c_sha = hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    require_ok(hmac.compare_digest(c_sha, calc_c_sha), "CERT_SHA_MISMATCH", "certificate_sha256 mismatch")

    secondary_audit_payload(payload)

    if full_replay:
        a_path = Path(anchor_path) if anchor_path is not None else (HERE / "s92_raw_arabic_anchor.json")
        a_bytes = read_regular_bytes_atomic(a_path, MAX_JSON_BYTES, not_found_code="ANCHOR_NOT_FOUND")
        a_sha = hashlib.sha256(a_bytes).hexdigest()
        require_ok(
            hmac.compare_digest(a_sha, O.EXPECTED_ANCHOR_FILE_SHA256),
            "ANCHOR_FILE_SHA_MISMATCH",
            "anchor file sha256 mismatch",
        )
        anchor = parse_strict_json(a_bytes.decode("utf-8"))
        replayed = O.build_certificate(anchor=anchor)
        require_ok(
            hmac.compare_digest(p_sha, replayed["payload_sha256"]),
            "REPLAY_PAYLOAD_SHA_MISMATCH",
            "replayed payload_sha256 mismatch",
        )
    return True


def verify_certificate_file(cert_path, full_replay=True, anchor_path=None):
    raw = read_regular_bytes_atomic(Path(cert_path), MAX_JSON_BYTES, not_found_code="CERT_NOT_FOUND")
    require_ok(b"\r" not in raw, "CRLF_FORBIDDEN", "CR/CRLF bytes forbidden in certificate")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise S92VerifyError("INVALID_UTF8", "invalid UTF-8 in certificate") from exc
    cert = parse_strict_json(text)
    canon = canonical_json_bytes(cert)
    require_ok(raw == canon, "NONCANONICAL_BYTES", "certificate bytes are not canonical JSON")
    verify_certificate_object(cert, full_replay=full_replay, anchor_path=anchor_path)
    return cert


# ---------------------------------------------------------------------------
# Comment-Only R10+ Lean Static Scanner & Live lean --stdin Axiom Gate
# ---------------------------------------------------------------------------

def _strip_lean_comments_only(src):
    """Strip nested Lean block comments /- ... -/ and line comments -- ... only."""
    out = []
    i = 0
    n = len(src)
    depth = 0
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if depth > 0:
            if ch == "/" and nxt == "-":
                depth += 1
                i += 2
            elif ch == "-" and nxt == "/":
                depth -= 1
                i += 2
            else:
                if ch == "\n":
                    out.append("\n")
                i += 1
        else:
            if ch == "/" and nxt == "-":
                depth = 1
                i += 2
            elif ch == "-" and nxt == "/":
                raise S92VerifyError("LEAN_STRAY_COMMENT_CLOSE", "stray -/ in Lean source")
            elif ch == "-" and nxt == "-":
                while i < n and src[i] != "\n":
                    i += 1
            else:
                out.append(ch)
                i += 1
    require_ok(depth == 0, "LEAN_UNCLOSED_COMMENT", "unclosed block comment in Lean source")
    return "".join(out)


def scan_lean_source(src):
    """R10+ comment-only static scanner forbidding escapes, quotes, guillemets, imports, and BiDi."""
    _require_str_no_surrogate(src, "lean_src")
    require_ok("\x00" not in src and "\r" not in src, "LEAN_BAD_CONTROL", "NUL or CR forbidden in Lean source")
    for ch in src:
        cat = unicodedata.category(ch)
        if ch not in ("\n", "\t"):
            require_ok(cat not in ("Cc", "Cf", "Cs"), "LEAN_FORBIDDEN_UNICODE", f"forbidden Unicode category {cat}")
        require_ok(ch not in BANNED_LEAN_CHARS, "LEAN_FORBIDDEN_CHAR", f"forbidden Lean char {ord(ch)}")
    code = _strip_lean_comments_only(src)
    require_ok(_LEAN_HASH_CMD_RE.search(code) is None, "LEAN_HASH_CMD_FORBIDDEN", "hash command forbidden in Lean file")
    require_ok(_LEAN_DECIDE_OPT_RE.search(code) is None, "LEAN_DECIDE_OPT_FORBIDDEN", "decide(...) options forbidden")
    for tok in _LEAN_IDENT_RE.findall(code):
        require_ok(tok not in BANNED_LEAN_TOKENS, "LEAN_BANNED_TOKEN", f"banned Lean token: {tok}")
    declared = set(_LEAN_DECL_RE.findall(code))
    for full_name in O.EXPECTED_LEAN_THEOREMS:
        short_name = full_name.split(".")[-1]
        require_ok(short_name in declared, "LEAN_MISSING_THEOREM", f"missing theorem {short_name}")
    return True


def _parse_lean_axioms_output(stdout_txt):
    seen_thms = set()
    for line in stdout_txt.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.endswith("does not depend on any axioms"):
            name = s.split("'")[1]
            seen_thms.add(name)
        elif "depends on axioms: [" in s and s.endswith("]"):
            name = s.split("'")[1]
            ax_str = s.split("depends on axioms: [", 1)[1][:-1]
            axioms = [a.strip() for a in ax_str.split(",") if a.strip()]
            for ax in axioms:
                require_ok(ax in O.ALLOWED_LEAN_AXIOMS, "LEAN_BANNED_AXIOM", f"banned axiom {ax} in {name}")
            seen_thms.add(name)
        else:
            raise S92VerifyError("LEAN_UNEXPECTED_OUTPUT", f"unexpected lean output: {s}")
    require_ok(seen_thms == set(O.EXPECTED_LEAN_THEOREMS), "LEAN_AXIOM_COUNT_MISMATCH", "missing theorem axiom output")
    return True


_LEAN_ENV_ALLOWLIST = ("PATH", "LANG", "LC_ALL", "TMPDIR")


def _scrubbed_lean_env():
    """Minimal environment allowlist stripping LEAN_PATH/LEAN_OPTS/LEAN_SRC_PATH/ELAN_*/LEAN_CC."""
    clean = {k: os.environ[k] for k in _LEAN_ENV_ALLOWLIST if k in os.environ}
    if "PATH" not in clean:
        clean["PATH"] = "/usr/bin:/bin"
    return clean


def _read_and_static_gate_lean(lean_path=None, check_pin=True):
    require_ok(type(check_pin) is bool, "INVALID_CHECK_PIN", "check_pin must be strict bool")
    lpath = Path(lean_path) if lean_path is not None else (HERE / "RawArabicHigherOrderMesh.lean")
    raw = read_regular_bytes_atomic(lpath, MAX_LEAN_BYTES, not_found_code="LEAN_NOT_FOUND")
    if check_pin:
        sha = hashlib.sha256(raw).hexdigest()
        require_ok(hmac.compare_digest(sha, EXPECTED_LEAN_SHA256), "LEAN_SHA_MISMATCH", "Lean file SHA-256 mismatch")
    try:
        src = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise S92VerifyError("LEAN_INVALID_UTF8", "invalid UTF-8 in Lean file") from exc
    scan_lean_source(src)
    return src


def verify_lean_proof(lean_path=None, check_pin=True):
    src = _read_and_static_gate_lean(lean_path=lean_path, check_pin=check_pin)

    lean_bin = shutil.which("lean")
    require_ok(lean_bin is not None, "LEAN_BINARY_NOT_FOUND", "lean binary not found on PATH")

    axiom_cmds = "\n".join(f"#print axioms {thm}" for thm in O.EXPECTED_LEAN_THEOREMS)
    stdin_src = f"{src}\n{axiom_cmds}\n"
    proc = subprocess.run(
        [lean_bin, "--stdin"],
        input=stdin_src.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_scrubbed_lean_env(),
        timeout=60,
        check=False,
    )
    require_ok(proc.returncode == 0, "LEAN_COMPILE_FAILED", f"lean exited {proc.returncode}")
    require_ok(proc.stderr == b"", "LEAN_STDERR_NONEMPTY", "lean emitted warnings/stderr")
    return _parse_lean_axioms_output(proc.stdout.decode("utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Optional On-Disk Primary Dataset Verification (26 Primary Files)
# ---------------------------------------------------------------------------

def verify_datasets_on_disk(heritage_root, bayt_root, anchor_path=None, check_anchor_pin=True):
    require_ok(type(check_anchor_pin) is bool, "INVALID_CHECK_ANCHOR_PIN", "check_anchor_pin must be strict bool")
    h_root = Path(heritage_root)
    b_root = Path(bayt_root)
    a_path = Path(anchor_path) if anchor_path is not None else (HERE / "s92_raw_arabic_anchor.json")
    a_bytes = read_regular_bytes_atomic(a_path, MAX_JSON_BYTES, not_found_code="ANCHOR_NOT_FOUND")
    if check_anchor_pin:
        a_sha = hashlib.sha256(a_bytes).hexdigest()
        require_ok(
            hmac.compare_digest(a_sha, O.EXPECTED_ANCHOR_FILE_SHA256),
            "ANCHOR_FILE_SHA_MISMATCH",
            "anchor file sha256 mismatch",
        )
    anchor = parse_strict_json(a_bytes.decode("utf-8"))
    require_ok(type(anchor) is dict, "ANCHOR_NOT_DICT", "anchor must be strict dict")
    require_ok("anchor_sha256" in anchor, "ANCHOR_MISSING_SHA", "anchor missing anchor_sha256")
    a_int_sha = require_sha256_hex(anchor["anchor_sha256"], "anchor.anchor_sha256")
    a_body = {k: v for k, v in anchor.items() if k != "anchor_sha256"}
    require_ok(
        hmac.compare_digest(a_int_sha, O.canonical_sha256(a_body)),
        "ANCHOR_INTERNAL_SHA_MISMATCH",
        "anchor internal sha256 mismatch",
    )

    verified = 0
    # 12 primary treatises
    for t in anchor["treatises"]:
        p = h_root / t["rel_path"]
        raw = read_regular_bytes_atomic(p, 16_777_216, not_found_code="DATASET_FILE_NOT_FOUND", allow_hardlink=True)
        require_ok(len(raw) == t["bytes"], "DATASET_SIZE_MISMATCH", f"size mismatch for {t['id']}")
        require_ok(
            hmac.compare_digest(hashlib.sha256(raw).hexdigest(), t["sha256"]),
            "DATASET_SHA_MISMATCH",
            f"sha mismatch for {t['id']}",
        )
        verified += 1
    # 2 bayt-al-hikma N0 certificates
    bp = anchor["bayt_prior_art"]
    for rel_k, sz_k, sha_k in (
        ("continuum_cert_rel", "continuum_cert_bytes", "continuum_cert_file_sha256"),
        ("lexicon_cert_rel", "lexicon_cert_bytes", "lexicon_cert_file_sha256"),
    ):
        p = b_root / bp[rel_k]
        raw = read_regular_bytes_atomic(p, MAX_JSON_BYTES, not_found_code="BAYT_FILE_NOT_FOUND", allow_hardlink=True)
        require_ok(len(raw) == bp[sz_k], "BAYT_SIZE_MISMATCH", rel_k)
        require_ok(hmac.compare_digest(hashlib.sha256(raw).hexdigest(), bp[sha_k]), "BAYT_SHA_MISMATCH", rel_k)
        verified += 1
    # 12 bilingual scientific catalogs
    for cat in anchor["bilingual_scientific_catalogs"]["catalog_pins"]:
        p = h_root / cat["rel_path"]
        raw = read_regular_bytes_atomic(p, MAX_JSON_BYTES, not_found_code="CATALOG_FILE_NOT_FOUND", allow_hardlink=True)
        require_ok(len(raw) == cat["bytes"], "CATALOG_SIZE_MISMATCH", cat["rel_path"])
        require_ok(
            hmac.compare_digest(hashlib.sha256(raw).hexdigest(), cat["sha256"]),
            "CATALOG_SHA_MISMATCH",
            cat["rel_path"],
        )
        verified += 1
    require_ok(verified == 26, "DATASET_COUNT_MISMATCH", "expected 26 verified primary files")
    return verified


def main(argv=None):
    parser = argparse.ArgumentParser(description="Zone-B hardened verifier for Raw-Arabic K_12 Scientific Mesh.")
    parser.add_argument("--standalone", action="store_true", help="Emit canonical certificate JSON to stdout after static Lean gate")
    parser.add_argument("--write", metavar="PATH", help="Write canonical 0o600 certificate atomically")
    parser.add_argument("--check", metavar="PATH", help="Verify canonical certificate file")
    parser.add_argument("--verify-lean", action="store_true", help="Run R10+ scan & live lean --stdin axiom check")
    parser.add_argument("--verify-datasets", action="store_true", help="Verify all 26 on-disk primary dataset SHAs")
    parser.add_argument("--heritage-root", metavar="DIR", help="Read-only islamic-scientific-heritage-text root")
    parser.add_argument("--bayt-root", metavar="DIR", help="Read-only bayt-al-hikma-ref root")
    args = parser.parse_args(argv)

    try:
        if args.standalone:
            _read_and_static_gate_lean(check_pin=True)
            cert = O.build_certificate()
            sys.stdout.buffer.write(canonical_json_bytes(cert))
            return 0
        if args.write:
            cert = O.build_certificate()
            verify_certificate_object(cert, full_replay=True)
            write_regular_bytes_atomic_0600(Path(args.write), canonical_json_bytes(cert))
            print(f"WROTE_OK certificate_sha256={cert['certificate_sha256']}")
            return 0
        if args.check:
            cert = verify_certificate_file(Path(args.check), full_replay=True)
            print(f"CHECK_OK certificate_sha256={cert['certificate_sha256']}")
            return 0
        if args.verify_lean:
            verify_lean_proof(check_pin=True)
            print(f"LEAN_OK theorems={len(O.EXPECTED_LEAN_THEOREMS)} sha256={EXPECTED_LEAN_SHA256}")
            return 0
        if args.verify_datasets:
            require_ok(
                args.heritage_root is not None and args.bayt_root is not None,
                "MISSING_DATASET_ROOTS",
                "--heritage-root and --bayt-root required with --verify-datasets",
            )
            n = verify_datasets_on_disk(args.heritage_root, args.bayt_root)
            print(f"DATASETS_OK verified_files={n}")
            return 0
        cert = verify_certificate_file(HERE / "s92_raw_arabic_mesh_certificate.json", full_replay=True)
        print(f"CHECK_OK certificate_sha256={cert['certificate_sha256']}")
        return 0
    except S92VerifyError as exc:
        print(f"VERIFY_FAIL: {exc}", file=sys.stderr)
        return 2
    except O.S92OracleError as exc:
        print(f"ORACLE_FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
