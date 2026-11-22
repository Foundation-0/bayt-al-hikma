"""Head-2 matched nulls, own code, fresh logged seeds (random.Random(family_base + draw)), ND draws (default 2000)."""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from fractions import Fraction
import rc_common as C
import rc2_common as R

ND = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
FA = R.fixture("arabic-continuum/arabic_continuum_audit.py")
FB = R.fixture("arabic-lexicon/arabic_lexicon_audit.py")
fx = R.fx
ALPHA = Fraction(1, 20)
print("draws per null: %d ; seeds: random.Random(base + d), d=0..%d ; bases listed per family" % (ND, ND - 1))


def praw(ge, n=ND):
    return Fraction(1 + ge, n + 1)


def band(vals):
    s = sorted(vals)
    n = len(s)
    return s[(n * 25) // 1000], s[(n * 975) // 1000 - 1]


def holm_report(label, ge_map, n=ND):
    ad = R.holm({k: praw(g, n) for k, g in ge_map.items()})
    m = len(ge_map)
    rej = sorted(k for k, v in ad.items() if v <= ALPHA)
    print("   %s Holm (M=%d, B=%d): min attainable adjusted p = %s/%d = %s ; rejection at 0.05 attainable: %s" %
          (label, m, n, m, n + 1, fx(Fraction(m, n + 1), 4), Fraction(m, n + 1) <= ALPHA))
    print("   %s raw ge counts: %s" % (label, dict(sorted(ge_map.items()))))
    print("   %s adjusted p: %s" % (label, {k: fx(v, 4) for k, v in sorted(ad.items())}))
    print("   %s rejected: %d of %d: %s" % (label, len(rej), m, rej))
    return ad


L = C.read_leeds(R.P["leeds"])
roots = [r["root"] for r in L]
pos = [r["tag"] for r in L]
odd_i = [i for i, r in enumerate(L) if r["s"] % 2 == 1]
even_i = [i for i, r in enumerate(L) if r["s"] % 2 == 0]
uth = R.read_tanzil(R.P["uth"])
raw, rasm, stem = [], [], []
for k in sorted(uth):
    for tk in uth[k].split():
        rr = C.rasm(tk)
        if rr:
            raw.append(tk); rasm.append(rr); stem.append(C.stem(tk))
W3 = (10, 20, 40)

# ---------------- F1 per-layer cohesion ----------------
print("\n== F1 per-layer cohesion, IID shuffle (bases 3000000 raw, 3100000 rasm, 3200000 stem, 3300000 root); POS-strat T4B (3400000 all, 3500000 odd, 3600000 even)")
WM = {int(k): v for k, v in FA["window_metrics"].items()}
LAY = {}


def run_layer(name, seq, base, classes=None):
    ids = R.enc(seq)
    obs = {w: C.jaccard_pair(ids, w) for w in W3}
    ni = {w: 0 for w in W3}; nu = {w: 0 for w in W3}; ge = {w: 0 for w in W3}
    bk = None
    if classes is not None:
        bk = defaultdict(list)
        for i, c in enumerate(classes):
            bk[c].append(i)
    for d in range(ND):
        rg = random.Random(base + d)
        if bk is None:
            sh = ids[:]
            rg.shuffle(sh)
        else:
            sh = ids[:]
            for c in sorted(bk):
                idx = bk[c]
                vals = [ids[i] for i in idx]
                rg.shuffle(vals)
                for i, v in zip(idx, vals):
                    sh[i] = v
        for w in W3:
            i, u = C.jaccard_pair(sh, w)
            ni[w] += i; nu[w] += u
            if i * obs[w][1] >= obs[w][0] * u:
                ge[w] += 1
    LAY[name] = {w: (obs[w], (ni[w], nu[w]), ge[w]) for w in W3}
    for w in W3:
        o, nl, g = LAY[name][w]
        lift = Fraction(o[0] * nl[1], o[1] * nl[0])
        print("%-20s W=%-2d obs=%s null(pooled mean)=%s lift=%s ge=%d/%d p=%s" % (name, w, fx(Fraction(*o)), fx(Fraction(*nl)), fx(lift, 4), g, ND, fx(praw(g), 5)))


run_layer("raw", raw, 3000000)
run_layer("rasm", rasm, 3100000)
run_layer("stem", stem, 3200000)
run_layer("root", roots, 3300000)
run_layer("root_t4b_all", roots, 3400000, pos)
run_layer("root_t4b_odd", [roots[i] for i in odd_i], 3500000, [pos[i] for i in odd_i])
run_layer("root_t4b_even", [roots[i] for i in even_i], 3600000, [pos[i] for i in even_i])
print("-- ordering of lifts (obs/null mean), mine:")
for w in W3:
    lf = {n: Fraction(LAY[n][w][0][0] * LAY[n][w][1][1], LAY[n][w][0][1] * LAY[n][w][1][0]) for n in ("raw", "rasm", "stem", "root")}
    print("   W=%d %s" % (w, " > ".join("%s %s" % (n, fx(v, 3)) for n, v in sorted(lf.items(), key=lambda kv: -kv[1]))))
ge12 = {"%s_W%d" % (n, w): LAY[n][w][2] for n in ("raw", "rasm", "stem", "root") for w in W3}
holm_report("12 cells", ge12)
tol = R.holm_tolerance({"%s_W%d" % (n, w): FA_ge for (n, w, FA_ge) in [(n, w, WM[w][n]["ge_count"]) for n in ("raw", "rasm", "stem", "root") for w in W3]}, 250)
print("   authors' B=250 family: reported ge counts all", sorted(set(WM[w][n]["ge_count"] for n in ("raw", "rasm", "stem", "root") for w in W3)),
      "; max extra exceedances each cell can absorb (others fixed) before Holm stops rejecting it:", sorted(set(tol.values())))

# ---------------- F2 ring / inclusio ----------------
print("\n== F2 ring and inclusio, within-surah verse permutation (base 3700000)")
surah = defaultdict(lambda: defaultdict(list))
for r in L:
    surah[r["s"]][r["v"]].append(r["root"])
freq = Counter(roots)
top10_all = frozenset(r for r, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:10])
oc = Counter(r["root"] for r in L if r["s"] % 2 == 1)
ec = Counter(r["root"] for r in L if r["s"] % 2 == 0)
top10_odd = frozenset(r for r, _ in sorted(oc.items(), key=lambda kv: (-kv[1], kv[0]))[:10])
top10_even = frozenset(r for r, _ in sorted(ec.items(), key=lambda kv: (-kv[1], kv[0]))[:10])
print("top-10 from whole text vs odd-only vs even-only; symmetric difference whole/odd:", sorted(top10_all ^ top10_odd), "whole/even:", sorted(top10_all ^ top10_even))
S_all = [s for s in sorted(surah) if len(surah[s]) >= 20]
unit_raw = {s: [surah[s][v] for v in sorted(surah[s])] for s in S_all}
SETS = {k: {s: [frozenset(x for x in v if x not in ex) for v in unit_raw[s]] for s in S_all}
        for k, ex in (("plain", frozenset()), ("strip_all", top10_all), ("strip_odd", top10_odd), ("strip_even", top10_even))}
ALL_ = S_all; ODD_ = [s for s in S_all if s % 2 == 1]; EVEN_ = [s for s in S_all if s % 2 == 0]
CASES = [("all", ALL_, "plain"), ("odd", ODD_, "plain"), ("even", EVEN_, "plain"), ("all_strip10", ALL_, "strip_all"),
         ("odd_strip10", ODD_, "strip_all"), ("even_strip10", EVEN_, "strip_all"),
         ("VARIANT even_strip10_top10_from_odd_only", EVEN_, "strip_odd"), ("VARIANT odd_strip10_top10_from_even_only", ODD_, "strip_even")]


def stat(unit_sets, order, subset):
    ii = iu = di = du = mi = mu = 0
    for s in subset:
        base = unit_sets[s]
        sets = base if order is None else [base[i] for i in order[s]]
        n = len(sets); h = n // 2; k = n // 10
        for i in range(h):
            a, b = sets[i], sets[n - 1 - i]
            mi += len(a & b); mu += len(a | b)
        f = set().union(*sets[:k]); l = set().union(*sets[n - k:])
        ms = (n - k) // 2
        m = set().union(*sets[ms:ms + k])
        ii += len(f & l); iu += len(f | l); di += len(f & m); du += len(f | m)
    return Fraction(ii, iu) - Fraction(di, du), Fraction(mi, mu)


obs = {c[0]: stat(SETS[c[2]], None, c[1]) for c in CASES}
nd = {c[0]: [] for c in CASES}
nm = []
for d in range(ND):
    rg = random.Random(3700000 + d)
    order = {}
    for s in S_all:
        o = list(range(len(unit_raw[s])))
        rg.shuffle(o)
        order[s] = o
    for c in CASES:
        dv, mv = stat(SETS[c[2]], order, c[1])
        nd[c[0]].append(dv)
        if c[0] == "all":
            nm.append(mv)
GE = {}
for c in CASES:
    n_ = c[0]
    ge = sum(1 for x in nd[n_] if x >= obs[n_][0])
    lo, hi = band(nd[n_])
    print("%-44s D=%s null band [%s, %s] ge=%d/%d raw p=%s" % (n_, fx(obs[n_][0], 6, True), fx(lo, 6, True), fx(hi, 6, True), ge, ND, fx(praw(ge), 5)))
    if not n_.startswith("VARIANT"):
        GE[n_] = ge
holm_report("6 Qur'an inclusio tests", GE)
tol = R.holm_tolerance({k: FA["ring_metrics"]["delta_nulls"][k]["ge_count"] for k in ("all", "odd", "even", "all_strip10", "odd_strip10", "even_strip10")}, 250)
print("   authors' B=250 reported ge counts (30,50,48,11,6,64): none rejected; exceedance count at which each WOULD still be rejected (largest ge keeping Holm<=0.05, others fixed):", tol)
mge = sum(1 for x in nm if x >= obs["all"][1]); mle = sum(1 for x in nm if x <= obs["all"][1])
print("mirror (all 79): obs %s ; null >= obs %d/%d, null <= obs %d/%d ; lower-tail p=%s upper-tail p=%s" % (fx(obs["all"][1]), mge, ND, mle, ND, fx(praw(mle), 5), fx(praw(mge), 5)))

# ---------------- F2b Kalila ----------------
print("\n== F2b Kalila units, within-unit line permutation (base 3800000)")
kal, ksec = C.read_openiti(R.P["kalila"])
arb = [[frozenset(x) for x in u] for u in [kal[i:i + 60] for i in range(0, len(kal) - 60 + 1, 60)]]
nat = [[frozenset(x) for x in u] for u in ksec if len(u) >= 20]


def dstat(units, perms):
    ii = iu = di = du = 0
    for ui, u in enumerate(units):
        sets = u if perms is None else [u[i] for i in perms[ui]]
        n = len(sets); k = n // 10
        f = set().union(*sets[:k]); l = set().union(*sets[n - k:])
        ms = (n - k) // 2
        m = set().union(*sets[ms:ms + k])
        ii += len(f & l); iu += len(f | l); di += len(f & m); du += len(f | m)
    return Fraction(ii, iu) - Fraction(di, du)


oa, on = dstat(arb, None), dstat(nat, None)
na, nn = [], []
for d in range(ND):
    rg = random.Random(3800000 + d)
    pa = []
    for u in arb:
        o = list(range(len(u))); rg.shuffle(o); pa.append(o)
    pn = []
    for u in nat:
        o = list(range(len(u))); rg.shuffle(o); pn.append(o)
    na.append(dstat(arb, pa)); nn.append(dstat(nat, pn))
for lab, o, nl in (("kalila_arb", oa, na), ("kalila_nat", on, nn)):
    ge = sum(1 for x in nl if x >= o)
    lo, hi = band(nl)
    print("%-12s D=%s null band [%s, %s] ge=%d/%d raw p=%s" % (lab, fx(o, 6, True), fx(lo, 6, True), fx(hi, 6, True), ge, ND, fx(praw(ge), 5)))

# ---------------- F3 controls ----------------
print("\n== F3 OpenITI controls W=20 Jaccard, IID shuffle (bases 3900000 kalila, 3910000 adab, 3920000 poetry); Qur'an stem from F1")
ada, _ = C.read_openiti(R.P["adab"]); imr, _ = C.read_openiti(R.P["imru"]); tar, _ = C.read_openiti(R.P["tarafa"]); ant, _ = C.read_openiti(R.P["antara"])
kf, af, pf = C.flat(kal), C.flat(ada), C.flat(imr) + C.flat(tar) + C.flat(ant)
CTL = {}
for nm_, seq, base in (("kalila", kf, 3900000), ("adab", af, 3910000), ("poetry", pf, 3920000)):
    ids = R.enc(seq)
    o = C.jaccard_pair(ids, 20)
    ni = nu = ge = 0
    vals = []
    for d in range(ND):
        rg = random.Random(base + d)
        sh = ids[:]
        rg.shuffle(sh)
        i, u = C.jaccard_pair(sh, 20)
        ni += i; nu += u
        vals.append(Fraction(i, u))
        if i * o[1] >= o[0] * u:
            ge += 1
    lift = Fraction(o[0] * nu, o[1] * ni)
    lo, hi = band(vals)
    CTL[nm_] = lift
    print("%-8s obs=%s null mean=%s band [%s,%s] lift=%s ge=%d/%d" % (nm_, fx(Fraction(*o)), fx(Fraction(ni, nu)), fx(lo), fx(hi), fx(lift, 4), ge, ND))
qs = LAY["stem"][20]
CTL["quran"] = Fraction(qs[0][0] * qs[1][1], qs[0][1] * qs[1][0])
print("lift ranking W=20: " + " > ".join("%s %s" % (k, fx(v, 3)) for k, v in sorted(CTL.items(), key=lambda kv: -kv[1])))

# ---------------- F4 wazn ----------------
print("\n== F4 within-root wazn Renyi-2: global shuffle (bases 4000000/4010000/4020000 all/odd/even) and freq-strat (4100000/4110000/4120000)")
verb = [(r["root"], r["vf"], r["s"]) for r in L if r["tag"] == "V" and r["vf"] in ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")]


def wr2(rs, vfs):
    byr = defaultdict(Counter)
    for a, b in zip(rs, vfs):
        byr[a][b] += 1
    return Fraction(sum(c * c for cnt in byr.values() for c in cnt.values()), sum(sum(cnt.values()) ** 2 for cnt in byr.values()))


GEW = {}
for lab, sel, bg, bs in (("all", lambda s: True, 4000000, 4100000), ("odd", lambda s: s % 2 == 1, 4010000, 4110000), ("even", lambda s: s % 2 == 0, 4020000, 4120000)):
    rs = [a for a, _, s in verb if sel(s)]; vs = [b for _, b, s in verb if sel(s)]
    f = Counter(rs)
    bins = ["B1" if f[r] <= 2 else "B2" if f[r] <= 10 else "B3" if f[r] <= 50 else "B4" for r in rs]
    bk = defaultdict(list)
    for i, b in enumerate(bins):
        bk[b].append(i)
    o = wr2(rs, vs)
    ga = []; gs = []
    for d in range(ND):
        rg = random.Random(bg + d)
        x = vs[:]; rg.shuffle(x); ga.append(wr2(rs, x))
        rg = random.Random(bs + d)
        y = vs[:]
        for b in sorted(bk):
            idx = bk[b]; vals = [vs[i] for i in idx]; rg.shuffle(vals)
            for i, v in zip(idx, vals):
                y[i] = v
        gs.append(wr2(rs, y))
    for tag, nl in (("global", ga), ("freq-strat", gs)):
        ge = sum(1 for z in nl if z >= o)
        lo, hi = band(nl)
        print("wazn R2 %-4s %-10s obs=%s null band [%s,%s] mean=%s ge=%d/%d" % (lab, tag, fx(o), fx(lo), fx(hi), fx(sum(nl) / len(nl)), ge, ND))
        GEW["%s_%s" % (lab, tag)] = ge
holm_report("wazn 6 tests", GEW)
print("   (the PR's family has 4 tests: all T4A, all T4B, odd T4B, even T4B; same Holm result when restricted to those)")

# ---------------- F5 Renyi controls ----------------
print("\n== F5 Renyi-2 W=20 cross-collision lift, IID shuffle (base 4200000 + 10000*k)")
uthstem = stem
for k, (nm_, seq) in enumerate((("quran_stem", uthstem), ("kalila", kf), ("adab", af), ("poetry", pf))):
    ids = R.enc(seq)
    on_, od = C.renyi_cross_pair(ids, 20)
    sn = sd = ge = 0
    for d in range(ND):
        rg = random.Random(4200000 + 10000 * k + d)
        sh = ids[:]; rg.shuffle(sh)
        a, b = C.renyi_cross_pair(sh, 20)
        sn += a; sd += b
        if a * od >= on_ * b:
            ge += 1
    print("%-10s obs=%s null mean=%s lift=%s ge=%d/%d" % (nm_, fx(Fraction(on_, od)), fx(Fraction(sn, sd)), fx(Fraction(on_ * sd, od * sn), 4), ge, ND))

# ---------------- F6 context ----------------
print("\n== F6 context topology, verse-slot shuffle (base 4400000)")
TARGETS = ("ftq", "rtq", "sbH", "flk", "kwr", "wsE", "mdd", "qdr", "zwj", "Erj", "nzl", "xlq", "Amr", "Hqq", "wzn")
tset = frozenset(TARGETS)
vroots = defaultdict(set)
rv = defaultdict(set)
for r in L:
    vroots[(r["s"], r["v"])].add(r["root"]); rv[r["root"]].add((r["s"], r["v"]))
vkeys = sorted(vroots)
flatr = []; lens = []
for k in vkeys:
    rs = sorted(vroots[k]); lens.append(len(rs)); flatr.extend(rs)
multi = sorted(r for r in TARGETS if len(rv[r]) >= 9)
oc_ = Counter(roots)
top10c = frozenset(r for r, _ in sorted(oc_.items(), key=lambda kv: (-kv[1], kv[0]))[:10])


def ctxs(verses):
    cx = {sp: {r: Counter() for r in tset} for sp in ("all", "odd", "even")}
    co = {sp: [0, 0] for sp in cx}
    for (s, _v), rs in verses.items():
        sp2 = "odd" if s % 2 == 1 else "even"
        hits = rs & tset
        if hits:
            for sp in ("all", sp2):
                co[sp][1] += 1
                if len(hits) >= 2:
                    co[sp][0] += 1
            for r in hits:
                for nb in rs:
                    if nb != r and nb not in top10c:
                        cx["all"][r][nb] += 1; cx[sp2][r][nb] += 1
    out = {}
    for sp in cx:
        n = dd = 0
        for c in cx[sp].values():
            t = sum(c.values())
            if t:
                n += sum(x * x for x in c.values()); dd += t * t
        i = u = 0
        for a in range(len(multi)):
            for b in range(a + 1, len(multi)):
                c1, c2 = cx[sp][multi[a]], cx[sp][multi[b]]
                for w in c1.keys() | c2.keys():
                    x, y = c1[w], c2[w]
                    i += min(x, y); u += max(x, y)
        out[sp] = (Fraction(n, dd), Fraction(i, u), Fraction(co[sp][0], co[sp][1]))
    return out


oc2 = ctxs(vroots)
nc = {sp: ([], [], []) for sp in oc2}
for d in range(ND):
    rg = random.Random(4400000 + d)
    sh = flatr[:]; rg.shuffle(sh)
    nv = {}; p = 0
    for k, ln in zip(vkeys, lens):
        nv[k] = set(sh[p:p + ln]); p += ln
    res = ctxs(nv)
    for sp in res:
        for j in range(3):
            nc[sp][j].append(res[sp][j])
GEC = {}
for sp in ("all", "odd", "even"):
    for j, nmj in enumerate(("ctx_r2", "ctx_jaccard", "cooccur")):
        o = oc2[sp][j]
        nl = nc[sp][j]
        ge = sum(1 for z in nl if (z <= o if nmj == "ctx_jaccard" else z >= o))
        lo, hi = band(nl)
        print("%-12s %-4s obs=%s null band [%s,%s] mean=%s extreme=%d/%d" % (nmj, sp, fx(o), fx(lo), fx(hi), fx(sum(nl) / len(nl)), ge, ND))
        GEC["%s_%s" % (nmj, sp)] = ge
holm_report("9 context tests", GEC)

# ---------------- F7 lemma shuffle + length-matched control ----------------
print("\n== F7 cross-vs-same lemma gap: within-root lemma-set shuffle (base 4500000), and a stem-count-matched control")
sah = R.read_tanzil(R.P["sahih"]); pik = R.read_tanzil(R.P["pick"])
ss = {k: R.en_stems(v) for k, v in sah.items()}; ps_ = {k: R.en_stems(v) for k, v in pik.items()}
vlem = defaultdict(lambda: defaultdict(set))
for r in L:
    if r["lem"]:
        vlem[(r["s"], r["v"])][r["root"]].add(r["lem"])
pre = {}
multi_roots = []
for rt in TARGETS:
    vs = sorted(rv[rt]); n = len(vs)
    lv = [frozenset(vlem[k][rt]) for k in vs]
    sz = [[False] * n for _ in range(n)]; pz = [[False] * n for _ in range(n)]
    ln_s = [[0] * n for _ in range(n)]; ln_p = [[0] * n for _ in range(n)]
    same = cross = 0
    for i in range(n):
        for j in range(i + 1, n):
            sz[i][j] = not (ss[vs[i]] & ss[vs[j]]); pz[i][j] = not (ps_[vs[i]] & ps_[vs[j]])
            ln_s[i][j] = len(ss[vs[i]]) + len(ss[vs[j]]); ln_p[i][j] = len(ps_[vs[i]]) + len(ps_[vs[j]])
            if lv[i] & lv[j]:
                same += 1
            else:
                cross += 1
    if same > 0 and cross > 0:
        multi_roots.append(rt)
        pre[rt] = (n, lv, sz, pz, ln_s, ln_p)
print("multi-lemma roots (same>0 and cross>0):", len(multi_roots), multi_roots)


def gaps(lmap):
    st = sl = ct = cl = pst = psl = pct = pcl = 0
    per = {}
    for mr in multi_roots:
        n, _, sz, pz, _, _ = pre[mr]
        lv = lmap[mr]
        a = b = c = d_ = e = f = 0
        for i in range(n):
            li = lv[i]; sr = sz[i]; pr = pz[i]
            for j in range(i + 1, n):
                if li & lv[j]:
                    a += 1
                    if sr[j]: b += 1
                    if pr[j]: e += 1
                else:
                    c += 1
                    if sr[j]: d_ += 1
                    if pr[j]: f += 1
        st += a; sl += b; ct += c; cl += d_; psl += e; pcl += f
        per[mr] = (Fraction(d_, c) - Fraction(b, a), Fraction(f, c) - Fraction(e, a))
    return Fraction(cl, ct) - Fraction(sl, st), Fraction(pcl, ct) - Fraction(psl, st), per


obs_map = {mr: pre[mr][1] for mr in multi_roots}
os_, op_, oper = gaps(obs_map)
print("observed pooled gap (12 multi-lemma roots): sahih %s pickthall %s" % (fx(os_, 6, True), fx(op_, 6, True)))
ng_s = []; ng_p = []
ge_pr_s = {mr: 0 for mr in multi_roots}; ge_pr_p = {mr: 0 for mr in multi_roots}
for d in range(ND):
    rg = random.Random(4500000 + d)
    m = {}
    for mr in multi_roots:
        x = list(obs_map[mr]); rg.shuffle(x); m[mr] = x
    gs_, gp_, per = gaps(m)
    ng_s.append(gs_); ng_p.append(gp_)
    for mr in multi_roots:
        if per[mr][0] >= oper[mr][0]: ge_pr_s[mr] += 1
        if per[mr][1] >= oper[mr][1]: ge_pr_p[mr] += 1
for lab, o, nl in (("sahih", os_, ng_s), ("pickthall", op_, ng_p)):
    ge = sum(1 for z in nl if z >= o)
    lo, hi = band(nl)
    print("pooled gap %-9s obs=%s null band [%s,%s] mean=%s ge=%d/%d raw p=%s" % (lab, fx(o, 6, True), fx(lo, 6, True), fx(hi, 6, True), fx(sum(nl) / len(nl), 6, True), ge, ND, fx(praw(ge), 5)))
holm_report("12 per-root sahih", ge_pr_s)
holm_report("12 per-root pickthall", ge_pr_p)
# stem-count matched control: strata by combined stem count (quartiles of all pairs), gap within stratum, weighted
allc_s = []; allc_p = []
for mr in multi_roots:
    n, _, _, _, ls, lp = pre[mr]
    for i in range(n):
        for j in range(i + 1, n):
            allc_s.append(ls[i][j]); allc_p.append(lp[i][j])
def cuts(v):
    s = sorted(v); n = len(s)
    return (s[n // 4], s[n // 2], s[(3 * n) // 4])
cs, cp = cuts(allc_s), cuts(allc_p)
def stratum(x, c):
    return 0 if x <= c[0] else 1 if x <= c[1] else 2 if x <= c[2] else 3
def matched(lmap, which):
    tab = [[0, 0, 0, 0] for _ in range(4)]  # same_n, same_lost, cross_n, cross_lost
    for mr in multi_roots:
        n, _, sz, pz, ls, lp = pre[mr]
        lv = lmap[mr]
        for i in range(n):
            for j in range(i + 1, n):
                z = (sz if which == "s" else pz)[i][j]
                q = stratum((ls if which == "s" else lp)[i][j], cs if which == "s" else cp)
                if lv[i] & lv[j]:
                    tab[q][0] += 1; tab[q][1] += 1 if z else 0
                else:
                    tab[q][2] += 1; tab[q][3] += 1 if z else 0
    tot = sum(t[0] + t[2] for t in tab)
    g = Fraction(0)
    per = []
    for t in tab:
        if t[0] and t[2]:
            gg = Fraction(t[3], t[2]) - Fraction(t[1], t[0])
            per.append(gg)
            g += gg * Fraction(t[0] + t[2], tot)
        else:
            per.append(None)
    return g, per
for which, lab, base in (("s", "sahih", 4600000), ("p", "pickthall", 4700000)):
    o, per = matched(obs_map, which)
    nl = []
    for d in range(ND):
        rg = random.Random(base + d)
        m = {}
        for mr in multi_roots:
            x = list(obs_map[mr]); rg.shuffle(x); m[mr] = x
        nl.append(matched(m, which)[0])
    ge = sum(1 for z in nl if z >= o)
    lo, hi = band(nl)
    print("stem-count-matched (4 quartile strata) gap %-9s obs=%s per-stratum=%s null band [%s,%s] ge=%d/%d" % (lab, fx(o, 6, True), [fx(x, 4, True) if x is not None else None for x in per], fx(lo, 6, True), fx(hi, 6, True), ge, ND))
print("\nnulls2 done")
