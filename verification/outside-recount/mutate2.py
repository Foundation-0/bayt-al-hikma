"""Guard-removal sample (own code). Copies the tree per mutation into the scratch folder given on the command line, edits one guard, runs the package's own test suite under -I -O -B -W error in the sandbox."""
import os
import shutil
import subprocess
import sys

RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
SRC = RR
if len(sys.argv) < 2:
    raise SystemExit("usage: mutate2.py <empty scratch dir> [mutation ids ...]")
SCR = os.path.abspath(sys.argv[1])
SEL = sys.argv[2:]
PY = sys.executable
CO, LX, PL, VE = "arabic-continuum", "arabic-lexicon", "polymath-lineage", "veins-and-branches"
T = {CO: "test_arabic_continuum_r5.py", LX: "test_arabic_lexicon_r5.py", PL: "test_bayt_al_hikma_polymaths_r5.py", VE: "test_bayt_al_hikma_veins_r5.py"}
M = []


def m(mid, pkg, f, old, new, ctl=False):
    M.append(dict(id=mid, pkg=pkg, file=f, old=old, new=new, ctl=ctl))


m("C1_holm_multiplicity_removed", CO, "arabic_continuum_oracle.py", "scaled = pv * (m - rank_idx)", "scaled = pv")
m("C2_drop_not_confirmed_gate", CO, "arabic_continuum_oracle.py", "        and (not boundary_inclusio_holm_confirmed)\n", "")
m("C3_inclusio_confirmed_forced_true", CO, "arabic_continuum_oracle.py", 'boundary_inclusio_holm_confirmed = any(holm_quran["rejected_at_alpha"].values())', "boundary_inclusio_holm_confirmed = True")
m("C4_drop_mirror_vs_null", CO, "arabic_continuum_oracle.py", '        and ratios["all_mirror"] < ratios["mirror_null_pooled"]\n', "")
m("C5_drop_mirror_lower_tail_p", CO, "arabic_continuum_oracle.py", "        and m_p_le <= a_val\n", "")
m("C6_min_shuffles_to_one", CO, "arabic_continuum_oracle.py", "MIN_MULTISHUFFLE_B = 250", "MIN_MULTISHUFFLE_B = 1")
m("C7_drop_kalila_gt_quran", CO, "arabic_continuum_oracle.py", '        and ctrl_stats["kalila_prose"][2] > ctrl_stats["quran_stem"][2]\n', "")
m("C8_drop_adab_gt_poetry", CO, "arabic_continuum_oracle.py", '        and ctrl_stats["adab_prose"][0] > ctrl_stats["poetry_pooled"][0]\n', "")
m("C9_drop_root_beats_t4b", CO, "arabic_continuum_oracle.py", "                if p_t > a_val:\n                    root_beats_t4b_all = False", "                if False:\n                    root_beats_t4b_all = False")
m("C10_drop_split_half_t4b", CO, "arabic_continuum_oracle.py", "            elif p_t > a_val:\n                split_halves_beat_t4b_all = False", "            elif False:\n                split_halves_beat_t4b_all = False")
m("L1_drop_lemma_shuffle_sig", LX, "arabic_lexicon_oracle.py", "lemma_shuffle_sig_both = s_p_pooled <= a_val and p_p_pooled <= a_val", "lemma_shuffle_sig_both = True")
m("L2_drop_strata_positive", LX, "arabic_lexicon_oracle.py", "        and all_strata_positive_both\n", "")
m("L3_drop_pickthall_unanimity", LX, "arabic_lexicon_oracle.py", "        and multi_lemma_p_strict == multi_lemma_tested\n", "")
m("L4_drop_below_background_pickthall", LX, "arabic_lexicon_oracle.py", "below_bg_both = s_overall < bg_sahih and p_overall < bg_pick", "below_bg_both = s_overall < bg_sahih")
m("L5_holm_multiplicity_removed", LX, "arabic_lexicon_oracle.py", "scaled = pv * (m - rank_idx)", "scaled = pv")
m("P1_drop_actor_precedes_subject", PL, "bayt_al_hikma_polymath_certifier.py", '            if s_node["birth_year"] < d_node["birth_year"]:\n                chronology_violations.append(f"CHRONO_ACTOR_PRECEDES_SUBJECT:{src}->{dst}")', '            if False:\n                chronology_violations.append(f"CHRONO_ACTOR_PRECEDES_SUBJECT:{src}->{dst}")')
m("P2_drop_actor_died_before_maturity", PL, "bayt_al_hikma_polymath_certifier.py", '            if s_node["death_year"] < d_node["birth_year"] + 15:', "            if False:")
m("P3_drop_teacher_age_gap", PL, "bayt_al_hikma_polymath_certifier.py", '            if s_node["birth_year"] + 10 > d_node["birth_year"]:\n                chronology_violations.append(f"CHRONO_TEACHER_AGE_GAP', '            if False:\n                chronology_violations.append(f"CHRONO_TEACHER_AGE_GAP')
m("P4_drop_citation_keys_check", PL, "bayt_al_hikma_polymath_certifier.py", '    _require(set(value.keys()) == ALLOWED_CITATION_KEYS, f"citation-keys:{name}")\n', "")
m("V1_drop_actor_precedes_subject", VE, "bayt_al_hikma_veins_certifier.py", '            if s_node["birth_year"] < d_node["birth_year"]:\n                chronology_violations.append(f"CHRONO_ACTOR_PRECEDES_SUBJECT:{src}->{dst}")', '            if False:\n                chronology_violations.append(f"CHRONO_ACTOR_PRECEDES_SUBJECT:{src}->{dst}")')
m("V2_drop_tier_backward_engagement", VE, "bayt_al_hikma_veins_certifier.py", '            if s_rank < d_rank:\n                tier_violations.append(f"TIER_BACKWARD_FLOW:{src}->{dst}")', '            if False:\n                tier_violations.append(f"TIER_BACKWARD_FLOW:{src}->{dst}")')
m("V3_drop_cross_era_correspondence", VE, "bayt_al_hikma_veins_certifier.py", "            if s_rank != d_rank:\n", "            if False:\n")
m("C11_drop_mirror_lt_shift", CO, "arabic_continuum_oracle.py", 'ratios["all_mirror"] < ratios["all_shift"]\n        and ', "")
m("C12_arbitrary_decay_forced_true", CO, "arabic_continuum_oracle.py", 'arbitrary_prose_decays = ratios["kalila_arb_inclusio"] < ratios["kalila_arb_middle"]', "arbitrary_prose_decays = True")
m("C13_drop_quran_stem_p_gate", CO, "arabic_continuum_oracle.py", '        ctrl_stats["quran_stem"][3] <= a_val\n        and ', "        ")
m("C14_drop_separation_p_condition", CO, "arabic_continuum_oracle.py", 'deltas["all"] > deltas["kalila_nat"] and all_inc_p < kalila_nat_p', 'deltas["all"] > deltas["kalila_nat"]')
m("L6_drop_pickthall_same_floor", LX, "arabic_lexicon_oracle.py", "intra_lemma_nonzero = s_same_pool > 0 and p_same_pool > 0", "intra_lemma_nonzero = s_same_pool > 0")
m("L7_drop_adab_p_gate", LX, "arabic_lexicon_oracle.py", '        and ctrl_vals["adab_prose"][5] <= a_val\n', "")
m("L8_drop_poetry_d2", LX, "arabic_lexicon_oracle.py", "passed = agency_matrix_nontrivial and wazn_beats_nulls and shared_prose_lift and poetry_higher_d2", "passed = agency_matrix_nontrivial and wazn_beats_nulls and shared_prose_lift")
m("L9_drop_coupling_from_pass", LX, "arabic_lexicon_oracle.py", "passed = ctx_r2_specialized and distinct_neighborhoods and direct_coupling_enriched", "passed = ctx_r2_specialized and distinct_neighborhoods")
m("P5_drop_correspondence_overlap", PL, "bayt_al_hikma_polymath_certifier.py", "            if overlap < 15:", "            if False:")
m("P6_drop_cycle_detection", PL, "bayt_al_hikma_polymath_certifier.py", "            if color[v] == 1:\n                return True", "            if False:\n                return True")
m("V4_drop_tributary_epoch", VE, "bayt_al_hikma_veins_certifier.py", 'if tier == "tributary" and death > 750:', "if False:")
m("V5_drop_teacher_age_gap", VE, "bayt_al_hikma_veins_certifier.py", '            if s_node["birth_year"] + 10 > d_node["birth_year"]:\n                chronology_violations.append(f"CHRONO_TEACHER_AGE_GAP', '            if False:\n                chronology_violations.append(f"CHRONO_TEACHER_AGE_GAP')
m("V6_drop_no_path_check", VE, "bayt_al_hikma_veins_certifier.py", 'tier_violations.append("LINEAGE_NO_TRIBUTARY_CORE_BRANCH_PATH")', "pass")
for tag, pkg, fn in (("c", CO, "arabic_continuum_oracle.py"), ("l", LX, "arabic_lexicon_oracle.py")):
    m("N1%s_drop_wasla_fold" % tag, pkg, fn, '        w.replace("\\u0671", "\\u0627")\n        .replace', '        w.replace("\\u0671", "\\u0671")\n        .replace')
    m("N2%s_drop_hamza_alef_fold" % tag, pkg, fn, '        .replace("\\u0623", "\\u0627")\n', '')
    m("N3%s_drop_alef_maqsura_fold" % tag, pkg, fn, '        .replace("\\u0649", "\\u064a")\n', '')
    m("N4%s_drop_ta_marbuta_fold" % tag, pkg, fn, '        .replace("\\u0629", "\\u0647")\n', '')
    m("N5%s_english_min_len_3" % tag, pkg, fn, "if len(w) < 4 or w in EN_STOPWORDS:", "if len(w) < 3 or w in EN_STOPWORDS:")
m("N7c_middle_block_start", CO, "arabic_continuum_audit.py", "ms_start = (length - k) // 2", "ms_start = length // 2")
m("K1_CONTROL_lifespan_flip", PL, "bayt_al_hikma_polymath_certifier.py", '_require(birth < death, f"lineage-lifespan-order:{nid}")', '_require(birth > death, f"lineage-lifespan-order:{nid}")', True)
res = []
sel = SEL or [x["id"] for x in M]
for mu in M:
    if mu["id"] not in sel:
        continue
    d = "%s/mut_%s" % (SCR, mu["id"])
    if os.path.exists(d):
        raise SystemExit("scratch folder already exists, use a new one: " + d)
    shutil.copytree(SRC, d, ignore=shutil.ignore_patterns(".git", "verification", "corpora"))
    p = "%s/%s/%s" % (d, mu["pkg"], mu["file"])
    with open(p, encoding="utf-8") as fh:
        s = fh.read()
    n = s.count(mu["old"])
    if n != 1:
        res.append(dict(id=mu["id"], applied=n))
        print(mu["id"], "APPLY_COUNT", n, flush=True)
        continue
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(s.replace(mu["old"], mu["new"]))
    r = subprocess.run([PY, "-I", "-O", "-B", "-W", "error", T[mu["pkg"]]], cwd="%s/%s" % (d, mu["pkg"]), capture_output=True, text=True)
    tail = (r.stderr or r.stdout).strip().splitlines()[-1:]
    v = "CAUGHT" if r.returncode != 0 else "SURVIVED"
    res.append(dict(id=mu["id"], control=mu["ctl"], rc=r.returncode, verdict=v, last=tail))
    print(mu["id"], r.returncode, v, tail, flush=True)
print("summary: %d tried, %d caught, %d survived" % (len([r for r in res if "verdict" in r]), len([r for r in res if r.get("verdict") == "CAUGHT"]), len([r for r in res if r.get("verdict") == "SURVIVED"])))
