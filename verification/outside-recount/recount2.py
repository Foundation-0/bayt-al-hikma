"""Head-2 recount (own code, no PR code imported). Reproduces the authors' 250-draw numbers with their seeds, deterministic output."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from fractions import Fraction
import rc_common as C
import rc2_common as R

FA = R.fixture("arabic-continuum/arabic_continuum_audit.py")
FB = R.fixture("arabic-lexicon/arabic_lexicon_audit.py")
RES = []


def check(cid, name, mine, pr):
    ok = mine == pr
    RES.append((cid, ok))
    print("%-6s %-52s %s" % (cid, name, "MATCH" if ok else "DIFF"))
    if not ok:
        print("       mine=%s" % (mine,))
        print("       pr  =%s" % (pr,))


def sect(t):
    print("\n== " + t)


def L2(x):
    return list(x)


sect("hash gate (all nine pins)")
pins = {}
for rel, key in (("arabic_morphology_quranic-corpus/quranic-corpus-morphology-0.4.txt", "leeds"), ("tanzil-quran-uthmani.txt", "uth"),
                 ("tanzil-en.sahih.txt", "sahih"), ("tanzil-en.pickthall.txt", "pick"), ("openiti_controls/ibn_muqaffa_kalila.txt", "kalila"),
                 ("openiti_controls/ibn_muqaffa_adab_kabir.txt", "adab"), ("openiti_controls/imru_al_qays_diwan.txt", "imru"),
                 ("openiti_controls/tarafa_diwan.txt", "tarafa"), ("openiti_controls/antara_muallaqa.txt", "antara")):
    h = C.sha256_of(R.P[key])
    pin = FA["pinned_sha256s"].get(rel) if "pinned_sha256s" in FA else None
    print("%-8s %s" % (key, h[:16]))
import re
with open(R.REPO2 + "/arabic-continuum/arabic_continuum_audit.py", encoding="utf8") as fh:
    _pins = dict(re.findall(r'"([^"]+\.txt)": \(\s*"([0-9a-f]{64})"', fh.read()))
ok = all(C.sha256_of(R.CORP + "/" + rel) == h for rel, h in _pins.items())
print("all 9 files match the 9 pins in the head-2 continuum audit script:", ok, len(_pins))

W3 = (10, 20, 40)
WM = {int(k): v for k, v in FA["window_metrics"].items()}

sect("Leeds lattice and lexicon descriptive counts (A1-A5, B1-B3)")
L = C.read_leeds(R.P["leeds"])
roots = [r["root"] for r in L]
pos = [r["tag"] for r in L]
check("A1", "root-bearing segments", len(L), FA["total_root_tokens"])
check("A2", "unique roots", len(set(roots)), FA["unique_roots"])
check("A3", "unique (root, lem)", len({(r["root"], r["lem"]) for r in L if r["lem"]}), FA["unique_lemmas"])


def dtag(parts):
    ps = set(parts)
    if "ACT" in ps and "PCPL" in ps:
        return "ACT_PCPL"
    if "PASS" in ps and "PCPL" in ps:
        return "PASS_PCPL"
    if "VN" in ps:
        return "VN"
    return "BASE"


cells = {(r["root"], "%s:%s:%s" % (r["tag"], r["vf"] if r["vf"] else "BASE", dtag(r["parts"]))) for r in L}
check("A4", "unique (root, POS:WAZN:DERIV) cells", len(cells), FA["unique_root_wazn_cells"])
vfc = Counter(r["vf"] for r in L if r["tag"] == "V")
check("A5", "verb forms", dict(sorted(vfc.items())), dict(sorted(FA["verb_form_counts"].items())))
IX = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X")
verb = [(r["root"], r["vf"], r["s"]) for r in L if r["tag"] == "V" and r["vf"] in IX]
rvf = defaultdict(Counter)
for rt, vf, _ in verb:
    rvf[rt][vf] += 1
check("B1", "verb roots / tokens I-X / XII", (len(rvf), len(verb), sum(1 for r in L if r["tag"] == "V" and r["vf"] == "XII")),
      (FB["verb_roots"], FB["verb_tokens_i_x"], FB["form_xii_tokens"]))
check("B2", "multi-wazn roots", sum(1 for c in rvf.values() if len(c) >= 2), FB["poly_wazn_roots"])
tp = {"%s+%s" % (a, b): sum(1 for c in rvf.values() if a in c and b in c)
      for a, b in (("I", "IV"), ("I", "II"), ("II", "V"), ("III", "VI"), ("I", "VIII"), ("I", "X"), ("IV", "X"))}
check("B2", "transition counts", tp, FB["transition_pair_counts"])
OPC = {"I": "GROUND_I", "II": "CAUS_INTENS_II_III_IV", "III": "CAUS_INTENS_II_III_IV", "IV": "CAUS_INTENS_II_III_IV",
       "V": "REFL_RECIP_V_VI_VII_VIII", "VI": "REFL_RECIP_V_VI_VII_VIII", "VII": "REFL_RECIP_V_VI_VII_VIII",
       "VIII": "REFL_RECIP_V_VI_VII_VIII", "IX": "STAT_ESTIM_IX_X", "X": "STAT_ESTIM_IX_X"}
check("B3", "operator classes", dict(Counter(OPC[vf] for _, vf, _ in verb)), FB["op_class_counts"])

sect("N1-N2 per-layer window cohesion: observed, then 250 shuffles with the authors' seeds (own implementation)")
uth = R.read_tanzil(R.P["uth"])
raw, rasm, stem = [], [], []
for k in sorted(uth):
    for tk in uth[k].split():
        r = C.rasm(tk)
        if not r:
            continue
        raw.append(tk)
        rasm.append(r)
        stem.append(C.stem(tk))
print("Uthmani tokens: raw=%d" % len(raw), "(PR raw window union at W=10 implies 149959 per 10-token block pairs)")
odd_i = [i for i, r in enumerate(L) if r["s"] % 2 == 1]
even_i = [i for i, r in enumerate(L) if r["s"] % 2 == 0]
B = 250


def multishuffle(seq, base, classes=None):
    ids = R.enc(seq)
    obs = {w: C.jaccard_pair(ids, w) for w in W3}
    ni = {w: 0 for w in W3}
    nu = {w: 0 for w in W3}
    ge = {w: 0 for w in W3}
    for b in range(B):
        sh = C.lcg_shuffle(ids, base + b) if classes is None else C.strat_shuffle(ids, classes, base + b)
        for w in W3:
            i, u = C.jaccard_pair(sh, w)
            ni[w] += i
            nu[w] += u
            if i * obs[w][1] >= obs[w][0] * u:
                ge[w] += 1
    return {w: {"obs": list(obs[w]), "null_pooled": [ni[w], nu[w]], "ge_count": ge[w]} for w in W3}


layers = (("raw", raw, 20261000, None), ("rasm", rasm, 20262000, None), ("stem", stem, 20263000, None), ("root", roots, 20264000, None),
          ("root_t4b", roots, 20265000, pos),
          ("odd_split_root_t4b", [roots[i] for i in odd_i], 20266000, [pos[i] for i in odd_i]),
          ("even_split_root_t4b", [roots[i] for i in even_i], 20267000, [pos[i] for i in even_i]))
MS = {}
for name, seq, base, cls in layers:
    MS[name] = multishuffle(seq, base, cls)
    for w in W3:
        check("N1-2", "%s W=%d obs/null_pooled/ge" % (name, w), MS[name][w], WM[w][name])
print("lifts (obs / pooled null), recomputed:")
for name in ("raw", "rasm", "stem", "root", "root_t4b"):
    print("  %-9s" % name, " ".join("W%d=%s" % (w, R.fx(Fraction(MS[name][w]["obs"][0] * MS[name][w]["null_pooled"][1], MS[name][w]["obs"][1] * MS[name][w]["null_pooled"][0]))) for w in W3))
rev = all(Fraction(MS["raw"][w]["obs"][0] * MS["raw"][w]["null_pooled"][1], MS["raw"][w]["obs"][1] * MS["raw"][w]["null_pooled"][0]) >
          Fraction(MS["root"][w]["obs"][0] * MS["root"][w]["null_pooled"][1], MS["root"][w]["obs"][1] * MS["root"][w]["null_pooled"][0]) for w in W3)
print("raw lift > root lift at every W (the PR's 'reversal'):", rev)

sect("N1 Holm over the 12 (layer, W) cells, own implementation")
ge12 = {"%s_W%d" % (n, w): MS[n][w]["ge_count"] for n in ("raw", "rasm", "stem", "root") for w in W3}
ad = R.holm({k: Fraction(1 + g, B + 1) for k, g in ge12.items()})
print("ge counts:", ge12)
print("adjusted p (min, max):", R.fx(min(ad.values())), R.fx(max(ad.values())), "= 12/251?", max(ad.values()) == Fraction(12, 251))
print("rejected at 0.05:", sum(1 for v in ad.values() if v <= Fraction(1, 20)), "of", len(ad))

sect("A9/N3 controls at W=20 with the authors' seeds (Qur'an stem row reuses the stem layer null)")
CW = FA["control_w20_metrics"]
kal, ksec = C.read_openiti(R.P["kalila"])
ada, _ = C.read_openiti(R.P["adab"])
imr, _ = C.read_openiti(R.P["imru"])
tar, _ = C.read_openiti(R.P["tarafa"])
ant, _ = C.read_openiti(R.P["antara"])
kf, af, pf = C.flat(kal), C.flat(ada), C.flat(imr) + C.flat(tar) + C.flat(ant)
print("OpenITI tokens kalila/adab/poetry:", len(kf), len(af), len(pf))
check("N3", "quran_stem (=stem layer W=20)", MS["stem"][20], CW["quran_stem"])
for nm, seq, base in (("kalila_prose", kf, 20268000), ("adab_prose", af, 20268500), ("poetry_pooled", pf, 20269000)):
    m = multishuffle_one = None
    ids = R.enc(seq)
    o = C.jaccard_pair(ids, 20)
    ni = nu = ge = 0
    for b in range(B):
        i, u = C.jaccard_pair(C.lcg_shuffle(ids, base + b), 20)
        ni += i
        nu += u
        if i * o[1] >= o[0] * u:
            ge += 1
    check("N3", "%s W=20 obs/null/ge" % nm, {"obs": list(o), "null_pooled": [ni, nu], "ge_count": ge}, CW[nm])

sect("N4 ring and inclusio with 250 verse permutations and the authors' seeds")
surah = defaultdict(lambda: defaultdict(list))
for r in L:
    surah[r["s"]][r["v"]].append(r["root"])
freq = Counter(roots)
top10 = frozenset(r for r, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:10])
S_all = [s for s in sorted(surah) if len(surah[s]) >= 20]
units = {s: [surah[s][v] for v in sorted(surah[s])] for s in S_all}
RM = FA["ring_metrics"]


def measure(sets_list):
    mi = mu = si = su = ii = iu = di = du = 0
    for sets in sets_list:
        n = len(sets)
        h = n // 2
        for i in range(h):
            a, b, c = sets[i], sets[n - 1 - i], sets[h + i]
            mi += len(a & b); mu += len(a | b)
            si += len(a & c); su += len(a | c)
        k = n // 10
        f = set().union(*sets[:k]); l = set().union(*sets[n - k:])
        ms = (n - k) // 2
        m = set().union(*sets[ms:ms + k])
        ii += len(f & l); iu += len(f | l)
        di += len(f & m); du += len(f | m)
    return (mi, mu), (si, su), (ii, iu), (di, du)


def ring_case(subset, exclude, base):
    prep = [[frozenset(x for x in v if x not in exclude) for v in units[s]] for s in subset]
    mir, sft, inc, mid = measure(prep)
    mr = Fraction(*mir)
    do = Fraction(*inc) - Fraction(*mid)
    mn_i = mn_u = mge = mle = dge = 0
    dn = []
    for b in range(B):
        pu = [C.lcg_shuffle(sets, base + b * 1009 + idx * 97) for idx, sets in enumerate(prep)]
        m2, _, i2, d2 = measure(pu)
        mn_i += m2[0]; mn_u += m2[1]
        q = Fraction(*m2)
        if q >= mr:
            mge += 1
        if q <= mr:
            mle += 1
        d = Fraction(*i2) - Fraction(*d2)
        dn.append(d)
        if d >= do:
            dge += 1
    ds = sorted(dn)
    return {"mirror": L2(mir), "shift": L2(sft), "inclusio": L2(inc), "middle": L2(mid), "mn": [mn_i, mn_u], "mge": mge, "mle": mle,
            "dge": dge, "q025": ds[(B * 25) // 1000], "q975": ds[min(B - 1, (B * 975) // 1000)], "delta": do}


ALL = S_all
ODD = [s for s in S_all if s % 2 == 1]
EVEN = [s for s in S_all if s % 2 == 0]
cases = (("all", ALL, frozenset(), 20269500), ("odd", ODD, frozenset(), 20269500 + 100000), ("even", EVEN, frozenset(), 20269500 + 200000),
         ("all_strip10", ALL, top10, 20269500 + 300000), ("odd_strip10", ODD, top10, 20269500 + 400000), ("even_strip10", EVEN, top10, 20269500 + 500000))
RC = {}
for nm, sub, ex, base in cases:
    RC[nm] = ring_case(sub, ex, base)
    key_i = "%s_inclusio" % nm if nm != "all" else "all_inclusio"
    check("N4", "%s inclusio/middle" % nm, (RC[nm]["inclusio"], RC[nm]["middle"]), (RM[key_i], RM[key_i.replace("inclusio", "middle")]))
    dn = FA["ring_metrics"]["delta_nulls"][nm]
    check("N4", "%s delta ge_count / quantiles" % nm, (RC[nm]["dge"], [RC[nm]["q025"].numerator, RC[nm]["q025"].denominator], [RC[nm]["q975"].numerator, RC[nm]["q975"].denominator]),
          (dn["ge_count"], dn["q025"], dn["q975"]))
check("N4", "all mirror/shift", (RC["all"]["mirror"], RC["all"]["shift"]), (RM["all_mirror"], RM["all_shift"]))
check("N4", "mirror null pooled, ge, le", (RC["all"]["mn"], RC["all"]["mge"], RC["all"]["mle"]), (RM["mirror_null_pooled"], RM["mirror_ge_count"], RM["mirror_le_count"]))
for nm, units_k, base in (("kalila_arb", [kal[i:i + 60] for i in range(0, len(kal) - 60 + 1, 60)], 20269500 + 600000),
                          ("kalila_nat", [s for s in ksec if len(s) >= 20], 20269500 + 700000)):
    prep = [[frozenset(v) for v in u] for u in units_k]
    mir, sft, inc, mid = measure(prep)
    do = Fraction(*inc) - Fraction(*mid)
    dge = 0
    dn = []
    for b in range(B):
        pu = [C.lcg_shuffle(sets, base + b * 1009 + idx * 97) for idx, sets in enumerate(prep)]
        _, _, i2, d2 = measure(pu)
        d = Fraction(*i2) - Fraction(*d2)
        dn.append(d)
        if d >= do:
            dge += 1
    ds = sorted(dn)
    q1, q2 = ds[(B * 25) // 1000], ds[min(B - 1, (B * 975) // 1000)]
    RC[nm] = {"dge": dge, "delta": do}
    dd = FA["ring_metrics"]["delta_nulls"][nm]
    check("N4", "%s inclusio/middle" % nm, (L2(inc), L2(mid)), (RM[nm + "_inclusio"], RM[nm + "_middle"]))
    check("N4", "%s delta ge / quantiles" % nm, (dge, [q1.numerator, q1.denominator], [q2.numerator, q2.denominator]), (dd["ge_count"], dd["q025"], dd["q975"]))

sect("N4 Holm over the six Qur'an inclusio tests, own implementation")
gq = {n: RC[n]["dge"] for n in ("all", "odd", "even", "all_strip10", "odd_strip10", "even_strip10")}
adq = R.holm({k: Fraction(1 + g, B + 1) for k, g in gq.items()})
print("ge counts:", gq)
print("raw p:", {k: "%d/251" % (1 + g) for k, g in gq.items()})
print("Holm adjusted:", {k: "%s/251" % (v * 251) for k, v in adq.items()})
print("rejected at 0.05:", [k for k, v in adq.items() if v <= Fraction(1, 20)])

sect("Pillar 3 translation remainder (A18-A21), Tanzil English files")
sah = R.read_tanzil(R.P["sahih"])
pik = R.read_tanzil(R.P["pick"])
ss = {k: R.en_stems(v) for k, v in sah.items()}
ps_ = {k: R.en_stems(v) for k, v in pik.items()}
keys = sorted(sah.keys())
check("A18", "verse keys equal across Uthmani/Sahih/Pickthall/Leeds", (sorted(uth) == keys, sorted(pik) == keys, len(keys)), (True, True, 6236))
sh = C.lcg_shuffle(keys, 2026097)
bs = bp = 0
for i in range(1000):
    k1, k2 = sh[2 * i], sh[2 * i + 1]
    if not (ss[k1] & ss[k2]):
        bs += 1
    if not (ps_[k1] & ps_[k2]):
        bp += 1
check("A19", "background pairs sahih/pickthall", ([bs, 1000], [bp, 1000]), (FA["bg_sahih_pair"], FA["bg_pickthall_pair"]))
root_verses = defaultdict(set)
occ = Counter(roots)
root_lems = defaultdict(set)
for r in L:
    root_verses[r["root"]].add((r["s"], r["v"]))
    if r["lem"]:
        root_lems[r["root"]].add(r["lem"])
for rec in FA["root_records"]:
    rt = rec["root"]
    vs = sorted(root_verses[rt])
    n = len(vs)
    sdf = Counter(); pdf = Counter()
    for k in vs:
        for t in ss[k]:
            sdf[t] += 1
        for t in ps_[k]:
            pdf[t] += 1
    sl = pl = 0
    for i in range(n):
        for j in range(i + 1, n):
            if not (ss[vs[i]] & ss[vs[j]]):
                sl += 1
            if not (ps_[vs[i]] & ps_[vs[j]]):
                pl += 1
    mine = (occ[rt], n, len(root_lems[rt]), max(sdf.values()) if sdf else 0, max(pdf.values()) if pdf else 0, sl, pl, n * (n - 1) // 2)
    pr = (rec["occurrences"], rec["verse_count"], rec["unique_lemmas"], rec["sahih_top_count"], rec["pickthall_top_count"], rec["sahih_lost_pairs"], rec["pickthall_lost_pairs"], rec["sahih_total_pairs"])
    check("A20", "root %s row" % rt, mine, pr)
tg7 = [r for r in FA["root_records"] if r["verse_count"] > 1]
sh_lost = sum(r["sahih_lost_pairs"] for r in tg7); pk_lost = sum(r["pickthall_lost_pairs"] for r in tg7); tot = sum(r["sahih_total_pairs"] for r in tg7)
print("pooled (from my per-root rows above, which matched): sahih %d/%d pickthall %d/%d" % (sh_lost, tot, pk_lost, tot))
check("A18", "pooled edge loss (as reduced fractions 3734/7335, 1933/2934)", (Fraction(sh_lost, tot), Fraction(pk_lost, tot)), (Fraction(3734, 7335), Fraction(1933, 2934)))
sm = sum(r["verse_count"] - r["sahih_top_count"] for r in tg7); pm = sum(r["verse_count"] - r["pickthall_top_count"] for r in tg7); nv = sum(r["verse_count"] for r in tg7)
check("A21", "pooled single-gloss miss 167/365 and 220/365 (=44/73)", ((sm, nv), (pm, nv)), ((167, 365), (220, 365)))
sev = [r["root"] for r in tg7 if Fraction(r["sahih_lost_pairs"], r["sahih_total_pairs"]) >= Fraction(2, 5) and Fraction(r["pickthall_lost_pairs"], r["pickthall_total_pairs"]) >= Fraction(2, 5)]
print("roots losing >= 40% of edges in both translators:", sev, "(report says 4: mdd wsE qdr zwj)")
sev53 = [r["root"] for r in tg7 if Fraction(r["sahih_lost_pairs"], r["sahih_total_pairs"]) > Fraction(53, 100) and Fraction(r["pickthall_lost_pairs"], r["pickthall_total_pairs"]) > Fraction(53, 100)]
print("roots losing > 53% in both (head-1 wording):", sev53)

print("\nRESULT per head-2 claim ids so far; summary below")
bad = [c for c, ok in RES if not ok]
print("checks=%d match=%d diff=%d" % (len(RES), len(RES) - len(bad), len(bad)))
print("diff ids:", sorted(set(bad)))
