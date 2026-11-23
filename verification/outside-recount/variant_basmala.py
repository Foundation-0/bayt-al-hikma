"""Convention variant: the Tanzil Uthmani file carries the basmala at the start of verse 1 of surahs 2-114 (except 9);
the Leeds root layer does not. Recompute the Qur'an layers without the repeated basmala (own code)."""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fractions import Fraction
import rc_common as C
import rc2_common as R
R.require_corpus()

ND = int(sys.argv[2]) if len(sys.argv) > 2 else 500
uth = R.read_tanzil(R.P["uth"])
b_rasm = [C.rasm(t) for t in uth[(1, 1)].split()]
print("basmala tokens (rasm):", len(b_rasm))
cnt_have = 0
cnt_expect = 0
for (s, v), txt in sorted(uth.items()):
    if v == 1 and s not in (1, 9):
        cnt_expect += 1
        toks = txt.split()
        if [C.rasm(t) for t in toks[:len(b_rasm)]] == b_rasm:
            cnt_have += 1
print("verse-1 starts in surahs 2-114 (not 9) that begin with the basmala: %d of %d" % (cnt_have, cnt_expect))
W3 = (10, 20, 40)


def layers(strip):
    raw, rasm, stem = [], [], []
    for (s, v) in sorted(uth):
        toks = uth[(s, v)].split()
        if strip and v == 1 and s not in (1, 9) and [C.rasm(t) for t in toks[:len(b_rasm)]] == b_rasm:
            toks = toks[len(b_rasm):]
        for t in toks:
            r = C.rasm(t)
            if r:
                raw.append(t); rasm.append(r); stem.append(C.stem(t))
    return {"raw": raw, "rasm": rasm, "stem": stem}


def lifts(seq, base):
    ids = R.enc(seq)
    obs = {w: C.jaccard_pair(ids, w) for w in W3}
    ni = {w: 0 for w in W3}; nu = {w: 0 for w in W3}
    for d in range(ND):
        rg = random.Random(base + d)
        sh = ids[:]; rg.shuffle(sh)
        for w in W3:
            i, u = C.jaccard_pair(sh, w)
            ni[w] += i; nu[w] += u
    return {w: (obs[w], Fraction(obs[w][0] * nu[w], obs[w][1] * ni[w])) for w in W3}


L = C.read_leeds(R.P["leeds"])
roots = R.enc([r["root"] for r in L])
obs = {w: C.jaccard_pair(roots, w) for w in W3}
ni = {w: 0 for w in W3}; nu = {w: 0 for w in W3}
for d in range(ND):
    rg = random.Random(5300000 + d)
    sh = roots[:]; rg.shuffle(sh)
    for w in W3:
        i, u = C.jaccard_pair(sh, w)
        ni[w] += i; nu[w] += u
root_lift = {w: Fraction(obs[w][0] * nu[w], obs[w][1] * ni[w]) for w in W3}
print("draws per null: %d (seeds random.Random(5000000 + 100000*k + d))" % ND)
print("root layer (unchanged by the variant): lift W10/20/40 = %s" % " ".join(R.fx(root_lift[w], 3) for w in W3))
for tag, strip in (("file as is (PR convention)", False), ("basmala removed from verse 1 of surahs 2-114 except 9", True)):
    lay = layers(strip)
    print("== %s ; tokens: %d" % (tag, len(lay["raw"])))
    for k, nm in enumerate(("raw", "rasm", "stem")):
        r = lifts(lay[nm], 5000000 + 100000 * k)
        print("   %-5s obs W10/20/40 = %s | lift = %s" % (nm, " ".join(R.fx(Fraction(*r[w][0]), 6) for w in W3), " ".join(R.fx(r[w][1], 3) for w in W3)))
