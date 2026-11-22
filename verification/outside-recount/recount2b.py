"""Head-2 lexicon-package recount (own code): reproduces the authors' 250-draw numbers with their seeds."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from fractions import Fraction
import rc_common as C
import rc2_common as R

FB = R.fixture("arabic-lexicon/arabic_lexicon_audit.py")
RES = []
B = 250


def check(cid, name, mine, pr):
    ok = mine == pr
    RES.append((cid, ok))
    print("%-6s %-56s %s" % (cid, name, "MATCH" if ok else "DIFF"))
    if not ok:
        print("       mine=%s" % (mine,))
        print("       pr  =%s" % (pr,))


def sect(t):
    print("\n== " + t)


L = C.read_leeds(R.P["leeds"])
roots = [r["root"] for r in L]
IX = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")
vp_all = [(r["root"], r["vf"]) for r in L if r["tag"] == "V" and r["vf"] in IX]
vp_odd = [(r["root"], r["vf"]) for r in L if r["tag"] == "V" and r["vf"] in IX and r["s"] % 2 == 1]
vp_even = [(r["root"], r["vf"]) for r in L if r["tag"] == "V" and r["vf"] in IX and r["s"] % 2 == 0]


def wr2(pairs):
    byr = defaultdict(Counter)
    for rt, vf in pairs:
        byr[rt][vf] += 1
    return [sum(c * c for cnt in byr.values() for c in cnt.values()), sum(sum(cnt.values()) ** 2 for cnt in byr.values())]


def ms_wazn(pairs, base, strat):
    ou, od = wr2(pairs)
    rc = [p[0] for p in pairs]
    vc = R.enc([p[1] for p in pairs])
    vcs = [p[1] for p in pairs]
    bins = None
    if strat:
        f = Counter(rc)
        bins = ["B1" if f[r] <= 2 else "B2" if f[r] <= 10 else "B3" if f[r] <= 50 else "B4" for r in rc]
    su = sd = ge = 0
    for b in range(B):
        sh = C.lcg_shuffle(vcs, base + b) if bins is None else C.strat_shuffle(vcs, bins, base + b)
        nu, nd = wr2(list(zip(rc, sh)))
        su += nu; sd += nd
        if nu * od >= ou * nd:
            ge += 1
    return [su, sd], ge


sect("L1 within-root wazn Renyi-2 with 250 shuffles and the authors' seeds")
WR = FB["within_root_renyi2_pairs"]
GE = FB["within_root_ge_counts"]
check("B4", "all obs", wr2(vp_all), WR["all_obs"])
check("B5", "odd obs, even obs", (wr2(vp_odd), wr2(vp_even)), (WR["odd_obs"], WR["even_obs"]))
for key, pairs, base, strat in (("all_t4a", vp_all, 20261100, False), ("all_t4b", vp_all, 20261500, True),
                                ("odd_t4b", vp_odd, 20262000, True), ("even_t4b", vp_even, 20262500, True)):
    pool, ge = ms_wazn(pairs, base, strat)
    check("B4-5", "%s pooled null / ge" % key, (pool, ge), (WR[key], GE[key]))

sect("L2 OpenITI and Qur'an Renyi-2 controls, 250 shuffles, seed 20263000 + 1000*k + b")
uth = R.read_tanzil(R.P["uth"])
qst = [C.stem(t) for k in sorted(uth) for t in uth[k].split() if C.rasm(t)]
kal, _ = C.read_openiti(R.P["kalila"]); ada, _ = C.read_openiti(R.P["adab"])
imr, _ = C.read_openiti(R.P["imru"]); tar, _ = C.read_openiti(R.P["tarafa"]); ant, _ = C.read_openiti(R.P["antara"])
CR = FB["control_renyi2_metrics"]
for k, (nm, seq) in enumerate((("quran_stem", qst), ("kalila_prose", C.flat(kal)), ("adab_prose", C.flat(ada)), ("poetry_pooled", C.flat(imr) + C.flat(tar) + C.flat(ant)))):
    ids = R.enc(seq)
    cnt = Counter(ids); N = sum(cnt.values())
    on, od = C.renyi_cross_pair(ids, 20)
    sn = sd = ge = 0
    for b in range(B):
        a, c = C.renyi_cross_pair(C.lcg_shuffle(ids, 20263000 + k * 1000 + b), 20)
        sn += a; sd += c
        if a * od >= on * c:
            ge += 1
    check("B6", "%s global C2 / W20 obs / pooled null / ge" % nm, ([sum(x * x for x in cnt.values()), N * N], [on, od], [sn, sd], ge),
          (CR[nm]["global_c2"], CR[nm]["w20_obs"], CR[nm]["w20_t4a_pooled"], CR[nm]["w20_ge_count"]))

sect("L3 context topology, 250 verse-slot shuffles, seed 20264000 + 251*b")
TARGETS = ("ftq", "rtq", "sbH", "flk", "kwr", "wsE", "mdd", "qdr", "zwj", "Erj", "nzl", "xlq", "Amr", "Hqq", "wzn")
tset = frozenset(TARGETS)
vroots = defaultdict(set); rv = defaultdict(set)
for r in L:
    vroots[(r["s"], r["v"])].add(r["root"]); rv[r["root"]].add((r["s"], r["v"]))
occ = Counter(roots)
top10 = frozenset(r for r, _ in sorted(occ.items(), key=lambda kv: (-kv[1], kv[0]))[:10])
multi = sorted(r for r in TARGETS if len(rv[r]) >= 9)


def bundle(verses):
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
                    if nb != r and nb not in top10:
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
        out["ctx_r2_" + sp] = [n, dd]
        out["ctx_jaccard_" + sp] = [i, u]
        out["cooccur_" + sp] = list(co[sp])
    return out


vkeys = sorted(vroots)
flatr = []; lens = []
for k in vkeys:
    rs = sorted(vroots[k]); lens.append(len(rs)); flatr.extend(rs)
ob = bundle(vroots)
ns = {k: [0, 0] for k in ob}
ex = {k: 0 for k in ob}
for b in range(B):
    sh = C.lcg_shuffle(flatr, 20264000 + b * 251)
    nv = {}; p = 0
    for k, ln in zip(vkeys, lens):
        nv[k] = set(sh[p:p + ln]); p += ln
    nb_ = bundle(nv)
    for k, pr in nb_.items():
        ns[k][0] += pr[0]; ns[k][1] += pr[1]
        on, od = ob[k]
        if k.startswith("ctx_jaccard_"):
            if pr[0] * od <= on * pr[1]:
                ex[k] += 1
        elif pr[0] * od >= on * pr[1]:
            ex[k] += 1
CM = FB["context_metrics"]
def nullkey(k):
    return {"ctx_r2_all": "ctx_r2_null_pooled", "ctx_jaccard_all": "ctx_jaccard_null_pooled", "cooccur_all": "cooccur_null_pooled"}.get(k, k + "_null_pooled")
check("B7-9", "9 observed pairs", {k: ob[k] for k in sorted(ob)}, {k: CM[k] for k in sorted(ob)})
check("B7-9", "9 pooled null pairs", {k: ns[k] for k in sorted(ob)}, {k: CM[nullkey(k)] for k in sorted(ob)})
check("B7-9", "9 extreme counts", {k: ex[k] for k in sorted(ob)}, {k: CM["extreme_counts"][k] for k in sorted(ob)})
print("   extreme counts:", {k: ex[k] for k in sorted(ex)})

sect("L4 two-translator projection defect: per-root rows, 250 within-root lemma shuffles (seed 20265000 + 131*b + idx), distance strata")
sah = R.read_tanzil(R.P["sahih"]); pik = R.read_tanzil(R.P["pick"])
ss = {k: R.en_stems(v) for k, v in sah.items()}; ps_ = {k: R.en_stems(v) for k, v in pik.items()}
vlem = defaultdict(lambda: defaultdict(set)); rlem = defaultdict(set)
for r in L:
    if r["lem"]:
        vlem[(r["s"], r["v"])][r["root"]].add(r["lem"]); rlem[r["root"]].add(r["lem"])
gidx = {k: i for i, k in enumerate(sorted(sah.keys()))}
names = ("same_surah_near", "same_surah_far", "diff_surah_near", "diff_surah_far")
strata = {n: {"same_pairs": 0, "cross_pairs": 0, "sahih_same_lost": 0, "sahih_cross_lost": 0, "pickthall_same_lost": 0, "pickthall_cross_lost": 0} for n in names}
recs = []
pre = {}
multi_roots = []
for rt in TARGETS:
    vs = sorted(rv[rt]); n = len(vs)
    sdf = Counter(); pdf = Counter()
    for k in vs:
        for t in ss[k]: sdf[t] += 1
        for t in ps_[k]: pdf[t] += 1
    lv = [frozenset(vlem[k][rt]) for k in vs]
    sa = sc = pa = pc = 0; sp = cp = 0
    sz = [[False] * n for _ in range(n)]; pz = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            s0 = not (ss[vs[i]] & ss[vs[j]]); p0 = not (ps_[vs[i]] & ps_[vs[j]])
            sz[i][j] = s0; pz[i][j] = p0
            if lv[i] & lv[j]:
                sp += 1; sa += s0; pa += p0
            else:
                cp += 1; sc += s0; pc += p0
    if sp > 0 and cp > 0:
        multi_roots.append(rt); pre[rt] = (n, lv, sz, pz)
        for i in range(n):
            for j in range(i + 1, n):
                d = abs(gidx[vs[j]] - gidx[vs[i]])
                if vs[i][0] == vs[j][0]:
                    sk = "same_surah_near" if d <= 10 else "same_surah_far"
                else:
                    sk = "diff_surah_near" if d <= 1000 else "diff_surah_far"
                t = strata[sk]
                if lv[i] & lv[j]:
                    t["same_pairs"] += 1; t["sahih_same_lost"] += sz[i][j]; t["pickthall_same_lost"] += pz[i][j]
                else:
                    t["cross_pairs"] += 1; t["sahih_cross_lost"] += sz[i][j]; t["pickthall_cross_lost"] += pz[i][j]
    recs.append({"root": rt, "occurrences": occ[rt], "verse_count": n, "unique_lemmas": len(rlem[rt]),
                 "sahih_top_count": max(sdf.values()) if sdf else 0, "pickthall_top_count": max(pdf.values()) if pdf else 0,
                 "same_lemma_pairs": sp, "cross_lemma_pairs": cp, "sahih_same_lost": sa, "sahih_cross_lost": sc,
                 "pickthall_same_lost": pa, "pickthall_cross_lost": pc, "sahih_lost_pairs": sa + sc, "pickthall_lost_pairs": pa + pc})
for mine, pr in zip(recs, FB["root_records"]):
    check("B10-14", "root %s row (15 fields)" % mine["root"], mine, pr)
check("B11-12", "pooled same/cross pair counts and losses",
      (sum(r["same_lemma_pairs"] for r in recs), sum(r["cross_lemma_pairs"] for r in recs), sum(r["sahih_same_lost"] for r in recs), sum(r["sahih_cross_lost"] for r in recs),
       sum(r["pickthall_same_lost"] for r in recs), sum(r["pickthall_cross_lost"] for r in recs)),
      (77081, 54262, 26520, 36842, 35423, 39773))
check("B10", "overall loss 63362/131343 and 75196/131343", (sum(r["sahih_lost_pairs"] for r in recs), sum(r["pickthall_lost_pairs"] for r in recs)), (63362, 75196))
check("B13p", "multi-lemma roots count", len(multi_roots), 12)
check("B-str", "4 distance strata", strata, FB["distance_strata"])


def gaps(lmap):
    st = sl = ct = cl = pst = psl = pct = pcl = 0
    per = {}
    for mr in multi_roots:
        n, _, sz, pz = pre[mr]
        lv = lmap[mr]
        a = b = c = d = e = f = 0
        for i in range(n):
            li = lv[i]; sr = sz[i]; pr = pz[i]
            for j in range(i + 1, n):
                if li & lv[j]:
                    a += 1; b += sr[j]; e += pr[j]
                else:
                    c += 1; d += sr[j]; f += pr[j]
        st += a; sl += b; ct += c; cl += d; psl += e; pcl += f
        per[mr] = (Fraction(d, c) - Fraction(b, a), Fraction(f, c) - Fraction(e, a))
    return Fraction(cl, ct) - Fraction(sl, st), Fraction(pcl, ct) - Fraction(psl, st), per


om = {mr: pre[mr][1] for mr in multi_roots}
og_s, og_p, oper = gaps(om)
ns_, np_ = [], []
sge = pge = 0
prs = {mr: 0 for mr in multi_roots}; prp = {mr: 0 for mr in multi_roots}
for b in range(B):
    m = {mr: C.lcg_shuffle(om[mr], 20265000 + b * 131 + idx) for idx, mr in enumerate(multi_roots)}
    gs, gp, per = gaps(m)
    ns_.append(gs); np_.append(gp)
    if gs >= og_s: sge += 1
    if gp >= og_p: pge += 1
    for mr in multi_roots:
        if per[mr][0] >= oper[mr][0]: prs[mr] += 1
        if per[mr][1] >= oper[mr][1]: prp[mr] += 1
sa_, pa_ = sorted(ns_), sorted(np_)
qi, qj = (B * 25) // 1000, min(B - 1, (B * 975) // 1000)
LS = FB["lemma_shuffle_null"]
mine = {"sahih_ge_count": sge, "pickthall_ge_count": pge,
        "sahih_q025": [sa_[qi].numerator, sa_[qi].denominator], "sahih_q975": [sa_[qj].numerator, sa_[qj].denominator],
        "pickthall_q025": [pa_[qi].numerator, pa_[qi].denominator], "pickthall_q975": [pa_[qj].numerator, pa_[qj].denominator],
        "per_root_sahih_ge": prs, "per_root_pickthall_ge": prp}
check("B13", "lemma-shuffle null (ge counts, quantiles, per-root ge)", mine, LS)
print("observed pooled gaps: sahih %s pickthall %s" % (R.fx(og_s, 6, True), R.fx(og_p, 6, True)))
print("per-root sahih ge:", prs)
print("per-root pickthall ge:", prp)
for lab, ge in (("sahih", prs), ("pickthall", prp)):
    ad = R.holm({k: Fraction(1 + g, B + 1) for k, g in ge.items()})
    print("Holm over 12 roots (%s), own implementation:" % lab, {k: "%s/251" % (v * 251) for k, v in sorted(ad.items())})
    print("   rejected at 0.05:", sorted(k for k, v in ad.items() if v <= Fraction(1, 20)))
    print("   min attainable adjusted p with B=250 and M=12: 12/251 = %s ; exceedance tolerance per root:" % R.fx(Fraction(12, 251), 4), R.holm_tolerance(ge, B))

sect("L5 per-root sign of the cross-minus-same gap (the '12 of 12' claim), both translators")
pos_s = pos_p = 0
for mr in multi_roots:
    n_, _, sz_, pz_ = pre[mr]
    lv_ = pre[mr][1]
    a = b = c = d = e = f = 0
    for i in range(n_):
        for j in range(i + 1, n_):
            if lv_[i] & lv_[j]:
                a += 1; b += sz_[i][j]; e += pz_[i][j]
            else:
                c += 1; d += sz_[i][j]; f += pz_[i][j]
    gs_ = Fraction(d, c) - Fraction(b, a); gp_ = Fraction(f, c) - Fraction(e, a)
    pos_s += gs_ > 0; pos_p += gp_ > 0
    print("   %-4s same=%d cross=%d gap sahih %s pickthall %s" % (mr, a, c, R.fx(gs_, 4, True), R.fx(gp_, 4, True)))
check("B13", "cross > same on all 12 multi-lemma roots (Sahih, Pickthall)", (pos_s, pos_p, len(multi_roots)), (12, 12, 12))
adx = R.holm({"ctx_r2_all": Fraction(1, 251)})
ge9 = {k: ex[k] for k in sorted(ex)}
ad9 = R.holm({k: Fraction(1 + g, B + 1) for k, g in ge9.items()})
print("Holm over 9 context tests:", {k: "%s/251" % (v * 251) for k, v in sorted(ad9.items())}, "rejected:", sum(1 for v in ad9.values() if v <= Fraction(1, 20)))
print("   exceedance tolerance:", R.holm_tolerance(ge9, B))
gw = {k: GE[k] for k in GE}
adw = R.holm({k: Fraction(1 + g, B + 1) for k, g in gw.items()})
print("Holm over 4 wazn tests:", {k: "%s/251" % (v * 251) for k, v in sorted(adw.items())}, "rejected:", sum(1 for v in adw.values() if v <= Fraction(1, 20)))
print("   exceedance tolerance:", R.holm_tolerance(gw, B))
bad = [c for c, ok in RES if not ok]
print("\nchecks=%d match=%d diff=%d" % (len(RES), len(RES) - len(bad), len(bad)))
print("diff ids:", sorted(set(bad)))
