"""Convention sensitivity of the translation-loss numbers to the English stemming rules (own code, exact integers)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from fractions import Fraction
import rc_common as C
import rc2_common as R

L = C.read_leeds(R.P["leeds"])
sah = R.read_tanzil(R.P["sahih"]); pik = R.read_tanzil(R.P["pick"])
rv = defaultdict(set); vlem = defaultdict(lambda: defaultdict(set))
for r in L:
    rv[r["root"]].add((r["s"], r["v"]))
    if r["lem"]:
        vlem[(r["s"], r["v"])][r["root"]].add(r["lem"])
TARGETS = ("ftq", "rtq", "sbH", "flk", "kwr", "wsE", "mdd", "qdr", "zwj", "Erj", "nzl", "xlq", "Amr", "Hqq", "wzn")
SEVEN = ("sbH", "mdd", "wsE", "flk", "kwr", "qdr", "zwj")


def stems(text, minlen, stop, suf):
    out = set()
    for w in R._words(text.lower()):
        if len(w) < minlen or (stop and w in R.STOP):
            continue
        if suf:
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
        if len(w) >= minlen and (not stop or w not in R.STOP):
            out.add(w)
    return out


def run(label, minlen, stop, suf):
    ss = {k: stems(v, minlen, stop, suf) for k, v in sah.items()}
    ps = {k: stems(v, minlen, stop, suf) for k, v in pik.items()}
    seven_s = seven_p = seven_t = 0
    same = cross = sl_s = sl_c = pl_s = pl_c = 0
    msame = mcross = msl_s = msl_c = mpl_s = mpl_c = 0
    for rt in TARGETS:
        vs = sorted(rv[rt]); n = len(vs)
        lv = [frozenset(vlem[k][rt]) for k in vs]
        a = b = c = d = e = f = 0
        for i in range(n):
            for j in range(i + 1, n):
                s0 = not (ss[vs[i]] & ss[vs[j]]); p0 = not (ps[vs[i]] & ps[vs[j]])
                if rt in SEVEN:
                    seven_t += 1; seven_s += s0; seven_p += p0
                if lv[i] & lv[j]:
                    a += 1; b += s0; e += p0
                else:
                    c += 1; d += s0; f += p0
        same += a; cross += c; sl_s += b; sl_c += d; pl_s += e; pl_c += f
        if a > 0 and c > 0:
            msame += a; mcross += c; msl_s += b; msl_c += d; mpl_s += e; mpl_c += f
    import random
    keys = sorted(sah.keys())
    sh = C.lcg_shuffle(keys, 2026097)
    bs = sum(1 for i in range(1000) if not (ss[sh[2 * i]] & ss[sh[2 * i + 1]]))
    bp = sum(1 for i in range(1000) if not (ps[sh[2 * i]] & ps[sh[2 * i + 1]]))
    liftS = Fraction(seven_t - seven_s, seven_t) / Fraction(1000 - bs, 1000)
    liftP = Fraction(seven_t - seven_p, seven_t) / Fraction(1000 - bp, 1000)
    print("%-34s | 7-root share-a-stem rate over background: S %sx P %sx | 7-root edge loss S %s P %s | background S %d/1000 P %d/1000 | 15-root overall S %s P %s | same S %s P %s | cross S %s P %s | 12-root gap S %s P %s" % (
        label, R.fx(liftS, 2), R.fx(liftP, 2), R.fx(Fraction(seven_s, seven_t), 4), R.fx(Fraction(seven_p, seven_t), 4), bs, bp,
        R.fx(Fraction(sl_s + sl_c, same + cross), 4), R.fx(Fraction(pl_s + pl_c, same + cross), 4),
        R.fx(Fraction(sl_s, same), 4), R.fx(Fraction(pl_s, same), 4), R.fx(Fraction(sl_c, cross), 4), R.fx(Fraction(pl_c, cross), 4),
        R.fx(Fraction(msl_c, mcross) - Fraction(msl_s, msame), 4, True), R.fx(Fraction(mpl_c, mcross) - Fraction(mpl_s, msame), 4, True)))


run("PR rules (min 4, stoplist, suffixes)", 4, True, True)
run("min length 3", 3, True, True)
run("min length 5", 5, True, True)
run("no stoplist", 4, False, True)
run("no suffix stripping", 4, True, False)
run("min 3, no stoplist, no suffixes", 3, False, False)
