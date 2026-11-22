"""Holm/permutation-test attainability tables (own code, exact rational arithmetic). Reads the committed certificates as data."""
import json
import os
import sys
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rc2_common as R
RR = R.REPO2
ALPHA = Fraction(1, 20)
with open(RR + "/arabic-continuum/arabic_continuum_certificate.json", encoding="utf8") as fh:
    ca = json.load(fh)
with open(RR + "/arabic-lexicon/arabic_lexicon_certificate.json", encoding="utf8") as fh:
    cb = json.load(fh)
fam = {}
wm = ca["pillar1_root_pattern_lattice"]["window_metrics"]
fam["continuum 12 cells (layer x W)"] = {"%s_W%s" % (l, w): wm[w][l]["ge_count"] for w in wm for l in ("raw", "rasm", "stem", "root")}
dn = ca["pillar2_ring_vs_inclusio_multishuffle"]["delta_null_reports"]
fam["continuum 6 Qur'an inclusio tests"] = {k: dn[k]["ge_count"] for k in ("all", "odd", "even", "all_strip10", "odd_strip10", "even_strip10")}
fam["lexicon 4 wazn tests"] = dict(cb["pillar1_wazn_agency_and_renyi2"]["within_root_ge_counts"])
fam["lexicon 9 context tests"] = dict(cb["pillar2_context_neighborhood_topology"]["extreme_counts"])
ls = cb["pillar3_two_layer_projection_defect"]["lemma_shuffle_null"]
fam["lexicon 12 per-root lemma tests (Sahih)"] = dict(ls["per_root_sahih_ge"])
fam["lexicon 12 per-root lemma tests (Pickthall)"] = dict(ls["per_root_pickthall_ge"])
for name, ge in fam.items():
    for B in (250, 2000):
        M = len(ge)
        print("== %s | B=%d | M=%d" % (name, B, M))
        pmin = Fraction(1, B + 1)
        print("   smallest raw p = 1/%d = %s ; smallest Holm-adjusted p over the family = %d/%d = %s ; rejection at 0.05 attainable: %s" %
              (B + 1, R.fx(pmin, 5), M, B + 1, R.fx(Fraction(M, B + 1), 5), Fraction(M, B + 1) <= ALPHA))
        # exceedance ceiling for rank j (1-based) so that Holm still rejects it, assuming ranks before it also rejected
        ceil = []
        for j in range(1, M + 1):
            g = 0
            while Fraction(1 + g + 1, B + 1) * (M - j + 1) <= ALPHA:
                g += 1
            ceil.append(g if Fraction(1, B + 1) * (M - j + 1) <= ALPHA else None)
        print("   max exceedances still rejected at sorted rank 1..%d (ge ceiling): %s" % (M, ceil))
        if B == 250:
            ad = R.holm({k: Fraction(1 + g, B + 1) for k, g in ge.items()})
            tol = R.holm_tolerance(ge, B)
            print("   reported ge counts: %s" % dict(sorted(ge.items())))
            print("   adjusted p: %s" % {k: "%s/251" % (v * 251) for k, v in sorted(ad.items())})
            print("   rejected now: %s" % sorted(k for k, v in ad.items() if v <= ALPHA))
            print("   largest exceedance count (out of B) at which each hypothesis would still be rejected, others held at their reported counts (None = cannot be rejected at any count): %s" % dict(sorted(tol.items())))
            # uniform flip: smallest g such that if EVERY hypothesis had g exceedances, nothing is rejected
            for g in range(0, B + 1):
                a2 = R.holm({k: Fraction(1 + g, B + 1) for k in ge})
                if not any(v <= ALPHA for v in a2.values()):
                    print("   if every test in the family had %d exceedances (of %d), none would be rejected" % (g, B))
                    break
            for g in range(0, B + 1):
                a2 = R.holm({k: Fraction(1 + g, B + 1) for k in ge})
                if not all(v <= ALPHA for v in a2.values()):
                    print("   if every test had %d exceedances, not all would be rejected (largest uniform count that still rejects all: %d)" % (g, g - 1))
                    break
