"""Helpers for head-2 recount (own code). Fixture/convention data are read from the PR as DATA via ast."""
import ast
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from fractions import Fraction
import rc_common as C

REPO2 = C.REPO
CORP = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ""
P = {
    "leeds": CORP + "/arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt",
    "uth": CORP + "/tanzil-quran-uthmani.txt",
    "sahih": CORP + "/tanzil-en.sahih.txt",
    "pick": CORP + "/tanzil-en.pickthall.txt",
    "kalila": CORP + "/openiti_controls/ibn_muqaffa_kalila.txt",
    "adab": CORP + "/openiti_controls/ibn_muqaffa_adab_kabir.txt",
    "imru": CORP + "/openiti_controls/imru_al_qays_diwan.txt",
    "tarafa": CORP + "/openiti_controls/tarafa_diwan.txt",
    "antara": CORP + "/openiti_controls/antara_muallaqa.txt",
}


def fixture(rel):
    return C.load_fixture(REPO2 + "/" + rel)


def const_from(path, name):
    with open(path, encoding="utf8") as fh:
        src = fh.read()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == name:
            v = node.value
            if isinstance(v, ast.Call):
                return ast.literal_eval(v.args[0])
            return ast.literal_eval(v)
    raise SystemExit("const not found " + name)


STOP = frozenset(const_from(REPO2 + "/arabic-continuum/arabic_continuum_oracle.py", "EN_STOPWORDS"))


def en_stems(text):
    out = set()
    for w in _words(text.lower()):
        if len(w) < 4 or w in STOP:
            continue
        if len(w) >= 7 and w.endswith("ing"):
            w = w[:-3]
            if w[-1] == w[-2]:
                w = w[:-1]
        elif len(w) >= 6 and w.endswith("ed"):
            w = w[:-2]
            if w[-1] == w[-2]:
                w = w[:-1]
        elif len(w) >= 6 and w.endswith("es"):
            w = w[:-2]
        elif len(w) >= 5 and w.endswith("s"):
            w = w[:-1]
        if len(w) >= 4 and w not in STOP:
            out.add(w)
    return out


def _words(s):
    cur = []
    for ch in s:
        if "a" <= ch <= "z":
            cur.append(ch)
        else:
            if cur:
                yield "".join(cur)
                cur = []
    if cur:
        yield "".join(cur)


def read_tanzil(path):
    d = {}
    with open(path, encoding="utf8") as fh:
        for raw in fh:
            s = raw.strip()
            if not s or s.startswith("#"):
                continue
            a, b, c = s.split("|", 2)
            d[(int(a), int(b))] = c
    return d


def enc(seq):
    mp = {}
    out = []
    for x in seq:
        i = mp.get(x)
        if i is None:
            i = len(mp)
            mp[x] = i
        out.append(i)
    return out


def jac_ids(seq, w):
    return C.jaccard_pair(seq, w)


def holm(ps):
    """ps: dict name -> Fraction raw p. returns dict name -> Fraction adjusted (Holm step-down, monotone)."""
    items = sorted(ps.items(), key=lambda kv: (kv[1], kv[0]))
    m = len(items)
    out = {}
    run = Fraction(0)
    for j, (k, p) in enumerate(items):
        run = max(run, min(Fraction(1), (m - j) * p))
        out[k] = run
    return out


def holm_tolerance(ge_counts, B, alpha=Fraction(1, 20)):
    """For each hypothesis, the largest exceedance count k (others fixed) at which it is still rejected by Holm; and rejection now."""
    res = {}
    base = {k: Fraction(1 + g, B + 1) for k, g in ge_counts.items()}
    for k in ge_counts:
        last = None
        for g in range(0, B + 1):
            t = dict(base)
            t[k] = Fraction(1 + g, B + 1)
            if holm(t)[k] <= alpha:
                last = g
            else:
                break
        res[k] = last
    return res


def fx(q, places=6, plus=False):
    q = Fraction(q)
    neg = q < 0
    q = abs(q)
    sc = (q * 10 ** places + Fraction(1, 2)).__floor__()
    t = "%d.%0*d" % (sc // 10 ** places, places, sc % 10 ** places)
    return ("-" if neg else ("+" if plus else "")) + t
