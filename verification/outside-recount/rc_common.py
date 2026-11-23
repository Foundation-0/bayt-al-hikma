"""Independent recount helpers (own code; reads the PR only as data via ast, for target numbers)."""
import ast
import hashlib
import os
import re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))  # repository root (this folder is verification/outside-recount)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def load_fixture(path):
    with open(path, encoding="utf8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "STANDALONE_FIXTURE":
            seg = ast.get_source_segment(src, node.value)
            seg = seg.replace("dict(EXPECTED_CORPUS_SHA256)", "{}")
            return ast.literal_eval(seg)
    raise SystemExit("fixture not found")


# ---------- Arabic normalisation with switches ----------
DIAC_CP = (set(range(0x0610, 0x061B)) | set(range(0x064B, 0x0660)) | {0x0670}
           | set(range(0x06D6, 0x06EE)) | {0x0640})
LETTER_CP = set(range(0x0621, 0x063B)) | set(range(0x0641, 0x064B))
PREFIXES = ["وال", "فال", "بال", "كال",
            "لل", "ال", "وب", "فب", "ول", "فل",
            "و", "ف", "ب", "ك", "ل"]
SUFFIXES = ["هما", "هم", "هن", "كم", "كن",
            "نا", "ها", "ون", "ين", "ان", "ات",
            "وا", "تم", "تن", "ني", "ه", "ك", "ي", "ت"]
ALEF_FOLD = {0x0671: 0x0627, 0x0623: 0x0627, 0x0625: 0x0627, 0x0622: 0x0627}
YA_FOLD = {0x0649: 0x064A}
TA_FOLD = {0x0629: 0x0647}

DEFAULT_SW = {"diac": True, "alef": True, "ya": True, "ta": True, "letters_only": True,
              "stem": True, "noise": True, "min_core": 3}


def rasm(tok, sw=DEFAULT_SW):
    out = []
    for ch in tok:
        cp = ord(ch)
        if sw["diac"] and cp in DIAC_CP:
            continue
        if sw["alef"] and cp in ALEF_FOLD:
            cp = ALEF_FOLD[cp]
        if sw["ya"] and cp in YA_FOLD:
            cp = YA_FOLD[cp]
        if sw["ta"] and cp in TA_FOLD:
            cp = TA_FOLD[cp]
        out.append(cp)
    if sw["letters_only"]:
        out = [c for c in out if c in LETTER_CP]
    return "".join(chr(c) for c in out)


def stem(tok, sw=DEFAULT_SW):
    r = rasm(tok, sw)
    if not sw["stem"]:
        return r
    m = sw["min_core"]
    if len(r) <= 3:
        return r
    for p in PREFIXES:
        if r.startswith(p) and len(r) - len(p) >= m:
            r = r[len(p):]
            break
    for s in SUFFIXES:
        if r.endswith(s) and len(r) - len(s) >= m:
            r = r[:-len(s)]
            break
    return r


# ---------- deterministic shuffles used by the PR (re-implemented from their description) ----------
MASK = (1 << 64) - 1


def lcg_shuffle(items, seed):
    x = seed & MASK
    a = list(items)
    for i in range(len(a) - 1, 0, -1):
        x = (6364136223846793005 * x + 1442695040888963407) & MASK
        j = (x >> 33) % (i + 1)
        a[i], a[j] = a[j], a[i]
    return a


def fnv32(s):
    h = 2166136261
    for b in s.encode("utf-8"):
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return h


def strat_shuffle(items, classes, seed):
    buckets = defaultdict(list)
    for i, c in enumerate(classes):
        buckets[c].append(i)
    out = list(items)
    for c in sorted(buckets):
        idx = buckets[c]
        vals = lcg_shuffle([items[i] for i in idx], seed ^ fnv32(c))
        for i, v in zip(idx, vals):
            out[i] = v
    return out


# ---------- Leeds ----------
FORMS = ("II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII")


def read_leeds(path, verb_default="I"):
    recs = []
    with open(path, encoding="utf8") as f:
        for line in f:
            if not line.strip() or line.startswith("#") or line.startswith("LOCATION"):
                continue
            p = line.rstrip("\r\n").split("\t")
            if len(p) < 4:
                continue
            loc, _form, tag, feat = p[0], p[1], p[2], p[3]
            parts = feat.split("|")
            root = lem = None
            for q in parts:
                if q.startswith("ROOT:") and root is None:
                    root = q[5:]
                elif q.startswith("LEM:") and lem is None:
                    lem = q[4:]
            if root is None:
                continue
            nums = loc.strip("()").split(":")
            s, v = int(nums[0]), int(nums[1])
            vf = None
            for q in parts:
                if q.startswith("(") and q.endswith(")") and q[1:-1] in FORMS:
                    vf = q[1:-1]
                    break
            if vf is None and tag == "V":
                vf = verb_default
            recs.append({"s": s, "v": v, "tag": tag, "root": root, "lem": lem or "", "vf": vf, "parts": parts})
    return recs


# ---------- windows ----------
def jaccard_pair(seq, w):
    n = len(seq) // w
    inter = union = 0
    prev = set(seq[0:w])
    for i in range(1, n):
        cur = set(seq[i * w:(i + 1) * w])
        inter += len(prev & cur)
        union += len(prev | cur)
        prev = cur
    return inter, union


def renyi_cross_pair(seq, w):
    n = len(seq) // w
    num = 0
    prev = Counter(seq[0:w])
    for i in range(1, n):
        cur = Counter(seq[i * w:(i + 1) * w])
        for k in prev.keys() & cur.keys():
            num += prev[k] * cur[k]
        prev = cur
    return num, (n - 1) * w * w


# ---------- OpenITI ----------
NOISE = re.compile(r"PageV\d+P\d+|ms\d+|%~~%|~%")


def read_openiti(path, sw=DEFAULT_SW):
    """returns (lines, sections): lines = list of stem lists; sections = list of lists of lines."""
    in_body = False
    lines, sections, cur = [], [], []
    with open(path, encoding="utf8") as f:
        for raw in f:
            s = raw.strip()
            if not in_body:
                if s.startswith("#META#Header#End#"):
                    in_body = True
                continue
            if not s:
                continue
            if s.startswith("###"):
                if cur:
                    sections.append(cur)
                    cur = []
                continue
            if sw["noise"]:
                s = NOISE.sub(" ", s)
            st = [stem(t, sw) for t in s.split() if rasm(t, sw)]
            if st:
                cur.append(st)
                lines.append(st)
    if cur:
        sections.append(cur)
    return lines, sections


def flat(lines):
    return [t for ln in lines for t in ln]


def ratio_str(p):
    return "%d/%d=%.6f" % (p[0], p[1], p[0] / p[1])
