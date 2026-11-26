"""Live read-only primary-source capture for Raw-Arabic K_12 Scientific Mesh.

Reads directly and strictly read-only from:
  --heritage-root <path to islamic-scientific-heritage-text>
  --bayt-root     <path to bayt-al-hikma-ref>

Zero floats anywhere on trust paths, zero bare asserts, zero random module
(pure 64-bit integer LCG Fisher-Yates shuffles matching Foundation-0/bayt-al-hikma),
zero hardcoded user paths, and canonical 0o600 zero-float JSON output.
"""

from collections import Counter
import argparse
from fractions import Fraction
import hashlib
import json
import os
import pathlib
import re
import sys

SCHEMA_VERSION = "s92-raw-arabic-anchor/v1"
MULTISHUFFLE_B = 250
LOCAL_WINDOW_W = 20
MATCHED_LOCAL_TOKENS = 3000
TOP_FUNC_STRIP = 50
LCG_SEED_BASE = 202609201

DIAC_STRIP_RE = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]")
AR_TOK_RE = re.compile(
    r"[\u0621-\u064a\u0671\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0640]+"
)
AR_LETTER_RE = re.compile(r"[\u0621-\u063a\u0641-\u064a]")
EN_WORD_RE = re.compile(r"[a-z]+")

DOTLESS_RASM_MAP = str.maketrans({
    "\u0623": "\u0627",
    "\u0625": "\u0627",
    "\u0622": "\u0627",
    "\u0671": "\u0627",
    "\u0628": "\u066e",
    "\u062a": "\u066e",
    "\u062b": "\u066e",
    "\u0646": "\u066e",
    "\u064a": "\u066e",
    "\u0649": "\u066e",
    "\u0626": "\u066e",
    "\u062c": "\u062d",
    "\u062e": "\u062d",
    "\u0630": "\u062f",
    "\u0632": "\u0631",
    "\u0634": "\u0633",
    "\u0636": "\u0635",
    "\u0638": "\u0637",
    "\u063a": "\u0639",
    "\u0641": "\u06a1",
    "\u0642": "\u06a1",
    "\u0629": "\u0647",
    "\u0624": "\u0648",
})

# Exact bayt-al-hikma v2 prefix/suffix tables (stem_v1)
AR_PREF_V1 = (
    "\u0648\u0627\u0644", "\u0641\u0627\u0644", "\u0628\u0627\u0644", "\u0643\u0627\u0644",
    "\u0644\u0644", "\u0627\u0644", "\u0648\u0628", "\u0641\u0628", "\u0648\u0644",
    "\u0641\u0644", "\u0648", "\u0641", "\u0628", "\u0643", "\u0644",
)
AR_SUFF_V1 = (
    "\u0647\u0645\u0627", "\u0647\u0645", "\u0647\u0646", "\u0643\u0645", "\u0643\u0646",
    "\u0646\u0627", "\u0647\u0627", "\u0648\u0646", "\u064a\u0646", "\u0627\u0646",
    "\u0627\u062a", "\u0648\u0627", "\u062a\u0645", "\u062a\u0646", "\u0646\u064a",
    "\u0647", "\u0643", "\u064a", "\u062a",
)

# Extended deterministic Arabic light stemmer (stem_v2, sensitivity sweep per bayt-al-hikma#8)
AR_PREF_V2 = (
    "\u0648\u0628\u0627\u0644", "\u0648\u0641\u0627\u0644", "\u0648\u0643\u0627\u0644",
    "\u0648\u0644\u0644", "\u0641\u0628\u0627\u0644", "\u0641\u0643\u0627\u0644",
    "\u0641\u0644\u0644", "\u0648\u0627\u0644", "\u0641\u0627\u0644", "\u0628\u0627\u0644",
    "\u0643\u0627\u0644", "\u0644\u0644", "\u0627\u0644", "\u0648\u0628", "\u0641\u0628",
    "\u0648\u0644", "\u0641\u0644", "\u0648\u0643", "\u0641\u0643", "\u0648\u0633",
    "\u0641\u0633", "\u0648", "\u0641", "\u0628", "\u0643", "\u0644", "\u0633",
)
AR_SUFF_V2 = (
    "\u062a\u0645\u0627", "\u0647\u0645\u0627", "\u0643\u0645", "\u0643\u0646",
    "\u0647\u0645", "\u0647\u0646", "\u0646\u0627", "\u0647\u0627", "\u0648\u0646",
    "\u064a\u0646", "\u0627\u0646", "\u0627\u062a", "\u0648\u0627", "\u062a\u0645",
    "\u062a\u0646", "\u0646\u064a", "\u064a\u0647", "\u0647", "\u0643", "\u064a",
    "\u062a", "\u0627",
)

EN_STOPWORDS = frozenset({
    "that", "this", "with", "from", "have", "were", "they", "them", "their",
    "then", "than", "when", "what", "which", "will", "would", "there", "been",
    "into", "upon", "unto", "over", "only", "also", "more", "most", "some",
    "such", "your", "ours", "shall", "should", "could", "those", "these",
    "being", "about", "after", "before", "against", "between", "through",
    "during", "without", "because", "while", "where", "whom", "whose",
    "book", "part", "chapter", "section", "other", "under", "first", "second",
    "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth",
})

CATALOG_AR_STOP = frozenset({
    "\u0641\u064a", "\u0645\u0646", "\u0639\u0644\u0649", "\u0627\u0644\u0649",
    "\u0639\u0646", "\u0645\u0639", "\u0628\u064a\u0646", "\u0639\u0646\u062f",
    "\u0645\u0627", "\u0627\u0644\u062a\u064a", "\u0627\u0644\u0630\u064a",
    "\u0647\u0630\u0627", "\u0647\u0630\u0647", "\u0630\u0644\u0643",
    "\u0639\u0645\u0644", "\u0643\u062a\u0627\u0628", "\u0628\u0627\u0628",
    "\u0641\u0635\u0644",
})

TREATISE_SPECS = (
    (
        "haytham_manazir", "optics", "Ibn al-Haytham", "Kitab al-Manazir",
        "04_physics_optics/openiti_classical_physics_optics/full_texts/02_\u0643\u062a\u0627\u0628_\u0627\u0644\u0645\u0646\u0627\u0638\u0631.md",
    ),
    (
        "sina_shifa_phys", "physics", "Ibn Sina (ed. study + primary extracts)", "Tabiiyyat al-Shifa",
        "04_physics_optics/openiti_classical_physics_optics/full_texts/01_\u0637\u0628\u064a\u0639\u064a\u0627\u062a_\u0643\u062a\u0627\u0628_\u0627\u0644\u0634\u0641\u0627\u0621__\u0627\u0644\u0633\u0645\u0627\u0639_\u0627\u0644\u0637\u0628\u064a\u0639\u064a.md",
    ),
    (
        "sina_qanun", "medicine", "Ibn Sina", "Al-Qanun fi al-Tibb",
        "01_medicine/openiti_classical_medicine/full_texts/01_\u0627\u0644\u0642\u0627\u0646\u0648\u0646_\u0641\u064a_\u0627\u0644\u0637\u0628.md",
    ),
    (
        "nafis_tashrih", "medicine", "Ibn al-Nafis", "Sharh Tashrih al-Qanun",
        "01_medicine/openiti_classical_medicine/full_texts/02_\u0634\u0631\u062d_\u062a\u0634\u0631\u064a\u062d_\u0627\u0644\u0642\u0627\u0646\u0648\u0646.md",
    ),
    (
        "battani_zij", "astronomy", "Al-Battani", "Al-Zij al-Sabi",
        "02_astronomy/openiti_classical_astronomy/full_texts/01_\u0632\u064a\u062c_\u0627\u0644\u0635\u0627\u0628\u0626__\u0627\u0644\u0632\u064a\u062c_.md",
    ),
    (
        "biruni_masudi", "astronomy", "Al-Biruni", "Al-Qanun al-Masudi",
        "02_astronomy/abu_al_rayhan_al_biruni_362_440h/al_qanun_al_masudi/al_biruni_qanun_masudi.jsonl",
    ),
    (
        "biruni_asturlab", "astronomy", "Al-Biruni", "Istiab al-Wujuh fi Sanat al-Asturlab",
        "02_astronomy/openiti_classical_astronomy/full_texts/02_\u0627\u0633\u062a\u064a\u0639\u0627\u0628_\u0627\u0644\u0648\u062c\u0648\u0647_\u0627\u0644\u0645\u0645\u0643\u0646\u0629_\u0641\u064a_\u0635\u0646\u0639\u0629_\u0627\u0644\u0623\u0633.md",
    ),
    (
        "tusi_majisti", "astronomy", "Nasir al-Din al-Tusi", "Tahrir al-Majisti",
        "02_astronomy/ptolemaeus_arabus_corpus/full_texts/09_C.1.18_Ta\u1e25r\u012br_al-Majis\u1e6d\u012b.md",
    ),
    (
        "biruni_zilal", "mathematics", "Al-Biruni", "Ifrad al-Maqal fi Amr al-Zilal",
        "03_mathematics/abu_al_rayhan_al_biruni_362_440h/ifrad_al_maqal_amr_al_zilal/al_biruni_amr_al_zilal.jsonl",
    ),
    (
        "biruni_awtar", "mathematics", "Al-Biruni", "Istikhraj al-Awtar fi al-Daira",
        "03_mathematics/abu_al_rayhan_al_biruni_362_440h/istikhraj_al_awtar/al_biruni_istikhraj_al_awtar.jsonl",
    ),
    (
        "thabit_niqumakhus", "mathematics", "Thabit ibn Qurra", "Madkhal Niqumakhus (Arithmetic)",
        "03_mathematics/thabit_ibn_qurra_al_harrani_221_288h/madkhal_niqumakhus/thabit_ibn_qurra_niqumakhus_arithmetic.jsonl",
    ),
    (
        "biruni_jamahir", "natural_history", "Al-Biruni", "Al-Jamahir fi Marifat al-Jawahir",
        "05_natural_history/openiti_classical_natural_history/full_texts/02_\u0627\u0644\u062c\u0645\u0627\u0647\u0631_\u0641\u064a_\u0645\u0639\u0631\u0641\u0629_\u0627\u0644\u062c\u0648\u0627\u0647\u0631.md",
    ),
)

BILINGUAL_CATALOG_RELS = (
    "01_medicine/abu_ali_ibn_sina_370_428h/al_qanun_fi_al_tibb/al_qanun_fi_al_tibb_books_catalog.jsonl",
    "01_medicine/abu_bakr_al_razi_251_313h/al_judari_wa_al_hasbah/al_judari_wa_al_hasbah_catalog.jsonl",
    "02_astronomy/abd_al_rahman_al_sufi_291_376h/suwar_al_kawakib_al_thabitah/suwar_al_kawakib_catalog.jsonl",
    "02_astronomy/abu_abdallah_al_battani_244_317h/al_zij_al_sabi/al_zij_al_sabi_catalog.jsonl",
    "02_astronomy/abu_al_rayhan_al_biruni_362_440h/al_tafhim_li_awail_al_tanjim/al_tafhim_chapters_catalog.jsonl",
    "03_mathematics/muhammad_ibn_musa_al_khwarizmi_164_232h/al_jabr_wa_al_muqabala/al_jabr_wa_al_muqabala_catalog.jsonl",
    "03_mathematics/nasir_al_din_al_tusi_597_672h/kitab_shakl_al_qatta/shakl_al_qatta_catalog.jsonl",
    "04_optics_mechanics_chemistry/al_hasan_ibn_al_haytham_354_430h/kitab_al_manazir/kitab_al_manazir_maqalat_catalog.jsonl",
    "04_optics_mechanics_chemistry/badi_al_zaman_al_jazari_530_602h/al_hiyal_mechanical_devices/al_jazari_machines_catalog.jsonl",
    "04_optics_mechanics_chemistry/banu_musa_ibn_shakir_d265h/kitab_al_hiyal/banu_musa_hiyal_catalog.jsonl",
    "04_optics_mechanics_chemistry/kamal_al_din_al_farisi_665_718h/tanqih_al_manazir/tanqih_al_manazir_catalog.jsonl",
    "04_optics_mechanics_chemistry/taqi_al_din_al_dimashqi_932_993h/al_turuq_al_saniyyah/al_turuq_al_saniyyah_catalog.jsonl",
)

# Explicitly disclosed author-specified thematic cross-discipline root probes
THEMATIC_ROOT_PROBES = (
    ("w_t_r", "\u0648-\u062a-\u0631", (
        "\u0648\u062a\u0631", "\u0627\u0648\u062a\u0627\u0631", "\u0648\u062a\u0627\u0631",
        "\u0645\u062a\u0648\u062a\u0631", "\u062a\u0648\u062a\u0631", "\u0648\u062a\u0631\u064a",
        "\u0648\u062a\u0631\u0647",
    )),
    ("q_t_E", "\u0642-\u0637-\u0639", (
        "\u0642\u0637\u0639", "\u0642\u0637\u0648\u0639", "\u0642\u0627\u0637\u0639",
        "\u0645\u0642\u0637\u0648\u0639", "\u0645\u0642\u0637\u0639", "\u0645\u0642\u0627\u0637\u0639",
        "\u0627\u0646\u0642\u0637\u0627\u0639", "\u0645\u0646\u0642\u0637\u0639", "\u062a\u0642\u0627\u0637\u0639",
        "\u0645\u062a\u0642\u0627\u0637\u0639", "\u0642\u0637\u0639\u0647", "\u0627\u0642\u0637\u0639",
        "\u064a\u0642\u0637\u0639", "\u062a\u0642\u0637\u0639", "\u0646\u0642\u0637\u0639",
    )),
    ("j_b_r", "\u062c-\u0628-\u0631", (
        "\u062c\u0628\u0631", "\u0627\u062c\u0628\u0627\u0631", "\u0645\u062c\u0628\u0648\u0631",
        "\u0645\u062c\u0628\u0631", "\u0646\u062c\u0628\u0631", "\u064a\u062c\u0628\u0631",
        "\u062a\u062c\u0628\u0631", "\u0627\u0646\u062c\u0628\u0627\u0631", "\u062c\u0628\u0627\u0631",
    )),
    ("n_f_dh", "\u0646-\u0641-\u0630", (
        "\u0646\u0641\u0630", "\u0646\u0641\u0648\u0630", "\u0646\u0627\u0641\u0630",
        "\u0645\u0646\u0641\u0630", "\u0645\u0646\u0627\u0641\u0630", "\u064a\u0646\u0641\u0630",
        "\u062a\u0646\u0641\u0630", "\u0627\u0646\u0641\u0627\u0630", "\u0645\u0646\u0641\u0648\u0630",
        "\u0646\u0641\u0627\u0630",
    )),
    ("z_l_l", "\u0638-\u0644-\u0644", (
        "\u0638\u0644", "\u0638\u0644\u0627\u0644", "\u0627\u0638\u0644\u0627\u0644",
        "\u0638\u0644\u0644", "\u0645\u0638\u0644", "\u0645\u0638\u0644\u0644",
        "\u062a\u0638\u0644\u064a\u0644", "\u064a\u0638\u0644", "\u062a\u0638\u0644",
        "\u0638\u0644\u0647",
    )),
    ("E_k_s", "\u0639-\u0643-\u0633", (
        "\u0639\u0643\u0633", "\u0627\u0646\u0639\u0643\u0627\u0633", "\u0645\u0646\u0639\u0643\u0633",
        "\u0639\u0627\u0643\u0633", "\u0645\u0639\u0643\u0648\u0633", "\u062a\u0639\u0627\u0643\u0633",
        "\u0645\u062a\u0639\u0627\u0643\u0633", "\u064a\u0646\u0639\u0643\u0633",
        "\u062a\u0646\u0639\u0643\u0633", "\u064a\u0639\u0643\u0633", "\u062a\u0639\u0643\u0633",
    )),
    ("q_y_s", "\u0642-\u064a-\u0633", (
        "\u0642\u064a\u0627\u0633", "\u0645\u0642\u064a\u0627\u0633", "\u0645\u0642\u0627\u064a\u064a\u0633",
        "\u0642\u064a\u0633", "\u0645\u0642\u064a\u0633", "\u064a\u0642\u064a\u0633",
        "\u062a\u0642\u064a\u0633", "\u0646\u0642\u064a\u0633", "\u0645\u0642\u0627\u064a\u0633\u0647",
        "\u0642\u064a\u0627\u0633\u064a", "\u0627\u0642\u064a\u0633\u0647",
    )),
    ("E_d_l", "\u0639-\u062f-\u0644", (
        "\u0639\u062f\u0644", "\u0627\u0639\u062a\u062f\u0627\u0644", "\u0645\u0639\u062a\u062f\u0644",
        "\u062a\u0639\u062f\u064a\u0644", "\u0645\u0639\u062f\u0644", "\u0645\u0639\u0627\u062f\u0644",
        "\u0645\u0639\u0627\u062f\u0644\u0647", "\u0639\u0627\u062f\u0644", "\u064a\u0639\u062f\u0644",
        "\u062a\u0639\u062f\u0644", "\u064a\u062a\u0639\u062f\u0644", "\u0645\u062a\u0639\u0627\u062f\u0644",
    )),
)


def norm_ar(tok):
    w = DIAC_STRIP_RE.sub("", tok)
    w = (
        w.replace("\u0671", "\u0627")
        .replace("\u0623", "\u0627")
        .replace("\u0625", "\u0627")
        .replace("\u0622", "\u0627")
        .replace("\u0649", "\u064a")
        .replace("\u0629", "\u0647")
    )
    return "".join(AR_LETTER_RE.findall(w))


def to_dotless_rasm(norm_tok):
    return norm_tok.translate(DOTLESS_RASM_MAP)


def to_stem_v1(norm_tok):
    r = norm_tok
    if len(r) <= 3:
        return r
    for p in AR_PREF_V1:
        if r.startswith(p) and len(r) - len(p) >= 3:
            r = r[len(p):]
            break
    for s in AR_SUFF_V1:
        if r.endswith(s) and len(r) - len(s) >= 3:
            r = r[:-len(s)]
            break
    return r


def to_stem_v2(norm_tok):
    r = norm_tok
    if len(r) <= 3:
        return r
    for p in AR_PREF_V2:
        if r.startswith(p) and len(r) - len(p) >= 3:
            r = r[len(p):]
            break
    for s in AR_SUFF_V2:
        if r.endswith(s) and len(r) - len(s) >= 3:
            r = r[:-len(s)]
            break
    if len(r) >= 4 and r.endswith("\u0647"):
        r = r[:-1]
    return r


def en_content_stems(text, minlen=4, use_stop=True, use_suffix=True):
    out = set()
    for w in EN_WORD_RE.findall(text.lower()):
        if len(w) < minlen or (use_stop and w in EN_STOPWORDS):
            continue
        if use_suffix:
            if len(w) >= 7 and w.endswith("ing"):
                w = w[:-3]
                if len(w) >= 2 and w[-1] == w[-2]:
                    w = w[:-1]
            elif len(w) >= 6 and w.endswith("ed"):
                w = w[:-2]
                if len(w) >= 2 and w[-1] == w[-2]:
                    w = w[:-1]
            elif len(w) >= 6 and w.endswith("es"):
                w = w[:-2]
            elif len(w) >= 5 and w.endswith("s"):
                w = w[:-1]
        if len(w) >= minlen and (not use_stop or w not in EN_STOPWORDS):
            out.add(w)
    return out


def det_shuffle_exact(items, seed):
    x = seed & 0xFFFFFFFFFFFFFFFF
    arr = list(items)
    for i in range(len(arr) - 1, 0, -1):
        x = (6364136223846793005 * x + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        j = (x >> 33) % (i + 1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr


def window_jaccard_and_r2(seq, w):
    n_blocks = len(seq) // w
    inter_sum = 0
    union_sum = 0
    r2_num = 0
    r2_den = (n_blocks - 1) * w * w
    prev = {}
    for x in seq[0:w]:
        prev[x] = prev.get(x, 0) + 1
    prev_len = len(prev)
    for b in range(1, n_blocks):
        cur = {}
        start = b * w
        for x in seq[start:start + w]:
            cur[x] = cur.get(x, 0) + 1
        cur_len = len(cur)
        inter = 0
        for k, cv in cur.items():
            pv = prev.get(k)
            if pv is not None:
                inter += 1
                r2_num += pv * cv
        inter_sum += inter
        union_sum += prev_len + cur_len - inter
        prev = cur
        prev_len = cur_len
    return inter_sum, union_sum, r2_num, r2_den


def read_treatise_body(path):
    raw_bytes = path.read_bytes()
    sha = hashlib.sha256(raw_bytes).hexdigest()
    txt = raw_bytes.decode("utf-8", errors="replace")
    if path.suffix == ".jsonl":
        body = json.loads(txt.splitlines()[0]).get("full_text", "")
    else:
        parts = txt.split("\n---\n", 1)
        body = parts[1] if len(parts) > 1 else txt
    return len(raw_bytes), sha, body


def capture_all(heritage_root, bayt_root):
    h_root = pathlib.Path(heritage_root)
    b_root = pathlib.Path(bayt_root)

    # 1. Pin Bayt al-Hikma N0 prior art
    bc_rel = "arabic-continuum/arabic_continuum_certificate.json"
    bl_rel = "arabic-lexicon/arabic_lexicon_certificate.json"
    bc_bytes = (b_root / bc_rel).read_bytes()
    bl_bytes = (b_root / bl_rel).read_bytes()
    bc_obj = json.loads(bc_bytes.decode("utf-8"))
    bl_obj = json.loads(bl_bytes.decode("utf-8"))

    p3c = bc_obj["pillar3_translation_remainder"]
    p3l = bl_obj["pillar3_two_layer_projection_defect"]
    w20c = bc_obj["pillar1_root_pattern_lattice"]["window_metrics"]["20"]

    bayt_prior_art = {
        "continuum_cert_rel": bc_rel,
        "continuum_cert_bytes": len(bc_bytes),
        "continuum_cert_file_sha256": hashlib.sha256(bc_bytes).hexdigest(),
        "continuum_cert_internal_sha256": bc_obj["certificate_sha256"],
        "continuum_audit_id": bc_obj["audit_id"],
        "lexicon_cert_rel": bl_rel,
        "lexicon_cert_bytes": len(bl_bytes),
        "lexicon_cert_file_sha256": hashlib.sha256(bl_bytes).hexdigest(),
        "lexicon_cert_internal_sha256": bl_obj["certificate_sha256"],
        "lexicon_audit_id": bl_obj["audit_id"],
        "sahih_7root_edge_loss_pair": [
            int(p3c["sahih_pooled_edge_loss_exact"].split("/")[0]),
            int(p3c["sahih_pooled_edge_loss_exact"].split("/")[1]),
        ],
        "pickthall_7root_edge_loss_pair": [
            int(p3c["pickthall_pooled_edge_loss_exact"].split("/")[0]),
            int(p3c["pickthall_pooled_edge_loss_exact"].split("/")[1]),
        ],
        "sahih_15root_same_loss_pair": [
            int(p3l["sahih_same_lemma_loss_exact"].split("/")[0]),
            int(p3l["sahih_same_lemma_loss_exact"].split("/")[1]),
        ],
        "sahih_15root_cross_loss_pair": [
            sum(r["sahih_cross_lost"] for r in p3l["per_root"]),
            p3l["pooled_cross_lemma_pairs"],
        ],
        "sahih_15root_overall_loss_pair": [
            int(p3l["sahih_overall_loss_exact"].split("/")[0]),
            int(p3l["sahih_overall_loss_exact"].split("/")[1]),
        ],
        "pickthall_15root_same_loss_pair": [
            int(p3l["pickthall_same_lemma_loss_exact"].split("/")[0]),
            int(p3l["pickthall_same_lemma_loss_exact"].split("/")[1]),
        ],
        "pickthall_15root_cross_loss_pair": [
            int(p3l["pickthall_cross_lemma_loss_exact"].split("/")[0]),
            int(p3l["pickthall_cross_lemma_loss_exact"].split("/")[1]),
        ],
        "pickthall_15root_overall_loss_pair": [
            int(p3l["pickthall_overall_loss_exact"].split("/")[0]),
            int(p3l["pickthall_overall_loss_exact"].split("/")[1]),
        ],
        "quran_w20_layers": {
            lyr: {
                "obs": list(w20c[lyr]["obs"]),
                "null_pooled": list(w20c[lyr]["null_pooled"]),
            }
            for lyr in ("raw", "rasm", "stem", "root")
        },
    }

    # 2. Extract 12 live raw-Arabic treatises with memoized normalization + layer maps
    layers = ("raw", "dotless_rasm", "stem_v1", "stem_v2")
    norm_cache = {}
    rasm_cache = {}
    s1_cache = {}
    s2_cache = {}

    def map_raw_type(w):
        if w not in rasm_cache:
            rasm_cache[w] = to_dotless_rasm(w)
            s1_cache[w] = to_stem_v1(w)
            s2_cache[w] = to_stem_v2(w)
        return rasm_cache[w], s1_cache[w], s2_cache[w]

    treatise_records = []
    full_counts = {lyr: [] for lyr in layers}
    matched_seqs = {lyr: [] for lyr in layers}
    corpus_raw_counts = Counter()

    for idx, (tid, disc, author, title_en, rel) in enumerate(TREATISE_SPECS):
        p = h_root / rel
        n_bytes, sha, body = read_treatise_body(p)
        raw_toks = []
        for t in AR_TOK_RE.findall(body):
            w = norm_cache.get(t)
            if w is None:
                w = norm_ar(t)
                norm_cache[t] = w
            if len(w) >= 2:
                raw_toks.append(w)
        n_tok = len(raw_toks)
        c_raw = Counter(raw_toks)
        corpus_raw_counts.update(c_raw)

        c_rasm = Counter()
        c_s1 = Counter()
        c_s2 = Counter()
        for w, cnt in c_raw.items():
            rm, st1, st2 = map_raw_type(w)
            c_rasm[rm] += cnt
            c_s1[st1] += cnt
            c_s2[st2] += cnt

        full_counts["raw"].append(c_raw)
        full_counts["dotless_rasm"].append(c_rasm)
        full_counts["stem_v1"].append(c_s1)
        full_counts["stem_v2"].append(c_s2)

        sub = raw_toks[:MATCHED_LOCAL_TOKENS]
        matched_seqs["raw"].append(sub)
        matched_seqs["dotless_rasm"].append([rasm_cache[w] for w in sub])
        matched_seqs["stem_v1"].append([s1_cache[w] for w in sub])
        matched_seqs["stem_v2"].append([s2_cache[w] for w in sub])

        layer_map = {
            "raw": c_raw,
            "dotless_rasm": c_rasm,
            "stem_v1": c_s1,
            "stem_v2": c_s2,
        }
        treatise_records.append({
            "index": idx,
            "id": tid,
            "discipline": disc,
            "author": author,
            "title_en": title_en,
            "rel_path": rel,
            "bytes": n_bytes,
            "sha256": sha,
            "token_count": n_tok,
            "vocab_sizes": {lyr: len(layer_map[lyr]) for lyr in layers},
            "global_c2_pairs": {
                lyr: [sum(v * v for v in layer_map[lyr].values()), n_tok * n_tok]
                for lyr in layers
            },
        })

    # 3. Within-treatise W=20 local cohesion & Renyi-2 with B=250 paired-seed LCG shuffles
    within_treatise_w20 = {lyr: {} for lyr in layers}
    base_positions = list(range(MATCHED_LOCAL_TOKENS))
    for t_idx, spec in enumerate(TREATISE_SPECS):
        tid = spec[0]
        enc_by_layer = {}
        obs_by_layer = {}
        acc_by_layer = {}
        for lyr in layers:
            seq = matched_seqs[lyr][t_idx]
            vocab = {}
            enc = []
            for tok in seq:
                code = vocab.get(tok)
                if code is None:
                    code = len(vocab)
                    vocab[tok] = code
                enc.append(code)
            enc_by_layer[lyr] = enc
            obs_by_layer[lyr] = window_jaccard_and_r2(enc, LOCAL_WINDOW_W)
            acc_by_layer[lyr] = [0, 0, 0, 0, 0, 0]

        base_seed = LCG_SEED_BASE + t_idx * 1000
        for b in range(MULTISHUFFLE_B):
            perm = det_shuffle_exact(base_positions, base_seed + b)
            for lyr in layers:
                enc = enc_by_layer[lyr]
                sh = [enc[idx_p] for idx_p in perm]
                si, su, sr2n, sr2d = window_jaccard_and_r2(sh, LOCAL_WINDOW_W)
                oi, ou, or2n, or2d = obs_by_layer[lyr]
                acc = acc_by_layer[lyr]
                acc[0] += si
                acc[1] += su
                acc[2] += sr2n
                acc[3] += sr2d
                if si * ou >= oi * su:
                    acc[4] += 1
                if sr2n * or2d >= or2n * sr2d:
                    acc[5] += 1

        for lyr in layers:
            oi, ou, or2n, or2d = obs_by_layer[lyr]
            ni_s, nu_s, nr2n_s, nr2d_s, j_ge, r2_ge = acc_by_layer[lyr]
            within_treatise_w20[lyr][tid] = {
                "jaccard_obs": [oi, ou],
                "jaccard_null_pooled": [ni_s, nu_s],
                "jaccard_ge_count": j_ge,
                "r2_obs": [or2n, or2d],
                "r2_null_pooled": [nr2n_s, nr2d_s],
                "r2_ge_count": r2_ge,
            }

    # 4. Full-text algorithmic K_12 (66 pairs) cross-treatise Renyi-2 matrix
    # Algorithmic top-50 corpus-ubiquitous function-word strip per layer (zero cherry-picking)
    k12_layers = {}
    n_t = len(TREATISE_SPECS)
    disc_list = [spec[1] for spec in TREATISE_SPECS]

    for l_idx, lyr in enumerate(layers):
        tot_c = Counter()
        for c in full_counts[lyr]:
            tot_c.update(c)
        top_func = frozenset(w for w, _ in tot_c.most_common(TOP_FUNC_STRIP))

        content_counts = []
        content_totals = []
        content_sq = []
        for c in full_counts[lyr]:
            fc = {w: v for w, v in c.items() if w not in top_func}
            content_counts.append(fc)
            content_totals.append(sum(fc.values()))
            content_sq.append(sum(v * v for v in fc.values()))

        pair_edges = []
        within_dot_sum = 0
        within_den_sum = 0
        cross_dot_sum = 0
        cross_den_sum = 0
        for i in range(n_t):
            ci = content_counts[i]
            for j in range(i + 1, n_t):
                cj = content_counts[j]
                if len(ci) <= len(cj):
                    dot = sum(v * cj[k] for k, v in ci.items() if k in cj)
                else:
                    dot = sum(v * ci[k] for k, v in cj.items() if k in ci)
                den = content_totals[i] * content_totals[j]
                same_disc = disc_list[i] == disc_list[j]
                pair_edges.append({
                    "i": i,
                    "j": j,
                    "same_discipline": same_disc,
                    "content_dot": dot,
                    "content_den": den,
                    "shared_types": len(ci.keys() & cj.keys()),
                })
                if same_disc:
                    within_dot_sum += dot
                    within_den_sum += den
                else:
                    cross_dot_sum += dot
                    cross_den_sum += den

        # B=250 Discipline-label permutation null on exact 66-pair content R2 matrix
        obs_gap = Fraction(within_dot_sum, within_den_sum) - Fraction(cross_dot_sum, cross_den_sum)
        disc_ge = 0
        for b in range(MULTISHUFFLE_B):
            perm_disc = det_shuffle_exact(disc_list, LCG_SEED_BASE + 500000 + l_idx * 1000 + b)
            wd = wden = cd = cden = 0
            for e in pair_edges:
                if perm_disc[e["i"]] == perm_disc[e["j"]]:
                    wd += e["content_dot"]
                    wden += e["content_den"]
                else:
                    cd += e["content_dot"]
                    cden += e["content_den"]
            if Fraction(wd, wden) - Fraction(cd, cden) >= obs_gap:
                disc_ge += 1

        # B=250 Vocabulary-label permutation null preserving each treatise's exact top-500 frequency spectrum
        # over the shared union content vocabulary appearing in >= 2 treatises
        shared_df = Counter()
        for fc in content_counts:
            for w in fc:
                shared_df[w] += 1
        shared_vocab = sorted(w for w, df in shared_df.items() if df >= 2)
        v_shared = len(shared_vocab)
        # Take exact full content counts restricted to shared_vocab for clean exact comparison
        v_idx = {w: k for k, w in enumerate(shared_vocab)}
        # Top-500 heaviest content terms per treatise (deterministic tie-break)
        top_k = 500
        t_top = []
        for fc in content_counts:
            items = sorted(
                ((v_idx[w], cnt) for w, cnt in fc.items() if w in v_idx),
                key=lambda kv: (-kv[1], kv[0]),
            )[:top_k]
            t_top.append(items)
        # Observed pooled 66-pair dot over top-500 shared content terms
        t_top_dicts = [dict(items) for items in t_top]
        obs_top_dot = 0
        obs_top_den = 0
        t_top_totals = [sum(cnt for _, cnt in items) for items in t_top]
        for i in range(n_t):
            di = t_top_dicts[i]
            for j in range(i + 1, n_t):
                dj = t_top_dicts[j]
                obs_top_dot += sum(v * dj[k] for k, v in di.items() if k in dj)
                obs_top_den += t_top_totals[i] * t_top_totals[j]

        # B=250 independent random-vocabulary-slot placement nulls (without replacement in 0..v_shared-1)
        null_top_dot_sum = 0
        null_top_den_sum = 0
        vocab_ge = 0
        for b in range(MULTISHUFFLE_B):
            sh_dicts = []
            for t_i in range(n_t):
                cnts = [cnt for _, cnt in t_top[t_i]]
                k_len = len(cnts)
                # Partial Fisher-Yates draw of k_len distinct slots from v_shared
                x = (LCG_SEED_BASE + 900000 + l_idx * 10000 + b * 29 + t_i) & 0xFFFFFFFFFFFFFFFF
                chosen = {}
                swaps = {}
                for pos in range(k_len):
                    x = (6364136223846793005 * x + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
                    r = pos + ((x >> 33) % (v_shared - pos))
                    val_r = swaps.get(r, r)
                    val_p = swaps.get(pos, pos)
                    swaps[r] = val_p
                    chosen[val_r] = cnts[pos]
                sh_dicts.append(chosen)
            s_dot = 0
            for i in range(n_t):
                di = sh_dicts[i]
                for j in range(i + 1, n_t):
                    dj = sh_dicts[j]
                    s_dot += sum(v * dj[k] for k, v in di.items() if k in dj)
            null_top_dot_sum += s_dot
            null_top_den_sum += obs_top_den
            if s_dot >= obs_top_dot:
                vocab_ge += 1

        k12_layers[lyr] = {
            "top_func_stripped_count": TOP_FUNC_STRIP,
            "content_totals": content_totals,
            "content_sq": content_sq,
            "edges": pair_edges,
            "within_discipline_pooled": [within_dot_sum, within_den_sum],
            "cross_discipline_pooled": [cross_dot_sum, cross_den_sum],
            "discipline_perm_ge_count": disc_ge,
            "shared_vocab_size": v_shared,
            "top500_obs_pooled": [obs_top_dot, obs_top_den],
            "top500_vocab_null_pooled": [null_top_dot_sum, null_top_den_sum],
            "top500_vocab_ge_count": vocab_ge,
        }

    # 5. Algorithmic top cross-discipline Arabic stems (stem_v1, zero cherry-picking)
    tot_s1 = Counter()
    for c in full_counts["stem_v1"]:
        tot_s1.update(c)
    top50_s1 = frozenset(w for w, _ in tot_s1.most_common(TOP_FUNC_STRIP))
    all_s1_types = sorted(w for w in tot_s1 if w not in top50_s1 and len(w) >= 3)
    cross_disc_all6_ge10 = []
    for w in all_s1_types:
        vec = [c.get(w, 0) for c in full_counts["stem_v1"]]
        docs = sum(1 for v in vec if v > 0)
        if docs < 10:
            continue
        discs = len({disc_list[i] for i, v in enumerate(vec) if v > 0})
        if discs == 6:
            cross_disc_all6_ge10.append((docs, min(vec), sum(vec), w, vec))
    cross_disc_all6_ge10.sort(key=lambda row: (-row[0], -row[1], -row[2], row[3]))
    algorithmic_bridges = {
        "selection_rule": "algorithmic_non_top50_len_ge3_all6_disciplines_ge10_treatises",
        "qualifying_stem_v1_count": len(cross_disc_all6_ge10),
        "top20_stems": [
            {
                "stem_v1": w,
                "docs_present": docs,
                "min_treatise_count": mn,
                "total_count": tot,
                "treatise_counts": vec,
            }
            for docs, mn, tot, w, vec in cross_disc_all6_ge10[:20]
        ],
    }

    # 6. Explicitly disclosed 8-root thematic probe table (stem_v1 & stem_v2)
    thematic_rows = []
    for key, root_ar, forms in THEMATIC_ROOT_PROBES:
        fset = frozenset(forms)
        vec_s1 = [sum(v for k, v in c.items() if k in fset) for c in full_counts["stem_v1"]]
        vec_s2 = [sum(v for k, v in c.items() if k in fset) for c in full_counts["stem_v2"]]
        docs_s1 = sum(1 for v in vec_s1 if v > 0)
        discs_s1 = len({disc_list[i] for i, v in enumerate(vec_s1) if v > 0})
        docs_s2 = sum(1 for v in vec_s2 if v > 0)
        discs_s2 = len({disc_list[i] for i, v in enumerate(vec_s2) if v > 0})
        zero_treatises_s1 = [TREATISE_SPECS[i][0] for i, v in enumerate(vec_s1) if v == 0]
        thematic_rows.append({
            "root_key": key,
            "root_ar": root_ar,
            "stem_v1_total": sum(vec_s1),
            "stem_v1_docs": docs_s1,
            "stem_v1_disciplines": discs_s1,
            "stem_v1_counts": vec_s1,
            "stem_v2_total": sum(vec_s2),
            "stem_v2_docs": docs_s2,
            "stem_v2_disciplines": discs_s2,
            "stem_v2_counts": vec_s2,
            "zero_treatises_s1": zero_treatises_s1,
            "universal_all_12_s1": docs_s1 == 12,
        })

    # 7. Law-5 Dotless Rasm Homography Collision-Inflation Witnesses (live corpus)
    rasm_groups = {}
    for w, cnt in corpus_raw_counts.items():
        if len(w) < 3 or cnt < 20:
            continue
        rm = rasm_cache[w]
        rasm_groups.setdefault(rm, []).append((w, cnt))
    homography_list = []
    for rm, members in rasm_groups.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda x: (-x[1], x[0]))
        sum_c = sum(c for _, c in members)
        sum_sq = sum(c * c for _, c in members)
        excess = sum_c * sum_c - sum_sq
        homography_list.append((excess, rm, members[:5], len(members), sum_c, sum_sq))
    homography_list.sort(key=lambda x: (-x[0], x[1]))
    rasm_witnesses = [
        {
            "dotless_rasm": rm,
            "merged_distinct_raw_forms": n_mem,
            "top_members": [[w, c] for w, c in top_m],
            "merged_sum": sum_c,
            "sum_of_squares": sum_sq,
            "collision_excess_delta_s2": excess,
        }
        for excess, rm, top_m, n_mem, sum_c, sum_sq in homography_list[:10]
    ]

    # 8. Real Bilingual Parallel Scientific Catalog Loss (12 JSONL files, 148 entries, 6 sensitivity variants)
    catalog_pins = []
    bilingual_entries = []
    for rel in BILINGUAL_CATALOG_RELS:
        p = h_root / rel
        raw_b = p.read_bytes()
        lines = [ln for ln in raw_b.decode("utf-8").splitlines() if ln.strip()]
        kept = 0
        for ln in lines:
            r = json.loads(ln)
            ar = " ".join(str(r[k]) for k in sorted(r) if k.endswith("_ar") and r[k])
            en = " ".join(str(r[k]) for k in sorted(r) if k.endswith("_en") and r[k])
            if ar.strip() and en.strip():
                bilingual_entries.append((rel.split("/")[0], ar, en))
                kept += 1
        catalog_pins.append({
            "rel_path": rel,
            "bytes": len(raw_b),
            "sha256": hashlib.sha256(raw_b).hexdigest(),
            "bilingual_rows": kept,
        })

    en_variants = (
        ("en_pr_min4", 4, True, True),
        ("en_min5", 5, True, True),
        ("en_no_suffix", 4, True, False),
    )
    ar_variants = (
        ("stem_v1", to_stem_v1),
        ("stem_v2", to_stem_v2),
    )
    bilingual_sweep = {}
    n_bi = len(bilingual_entries)
    for a_name, a_fn in ar_variants:
        ar_sets = [
            frozenset(
                a_fn(norm_ar(t))
                for t in AR_TOK_RE.findall(ar)
                if len(a_fn(norm_ar(t))) >= 3 and norm_ar(t) not in CATALOG_AR_STOP
            )
            for _, ar, _ in bilingual_entries
        ]
        for e_name, minlen, use_stop, use_suf in en_variants:
            en_sets = [
                en_content_stems(en, minlen=minlen, use_stop=use_stop, use_suffix=use_suf)
                for _, _, en in bilingual_entries
            ]
            ar_links = en_lost = cross_ar = cross_lost = 0
            all_pairs = 0
            bg_en_lost = 0
            for i in range(n_bi):
                for j in range(i + 1, n_bi):
                    all_pairs += 1
                    has_ar = bool(ar_sets[i] & ar_sets[j])
                    has_en = bool(en_sets[i] & en_sets[j])
                    if not has_en:
                        bg_en_lost += 1
                    if has_ar:
                        ar_links += 1
                        if not has_en:
                            en_lost += 1
                        if bilingual_entries[i][0] != bilingual_entries[j][0]:
                            cross_ar += 1
                            if not has_en:
                                cross_lost += 1
            # B=250 permutation null on English-label assignment across the 148 entries
            en_ge = 0
            en_null_lost_sum = 0
            en_null_den_sum = 0
            idxs = list(range(n_bi))
            # Precompute ar_link pairs for fast B=250 shuffle
            ar_pair_list = [
                (i, j)
                for i in range(n_bi)
                for j in range(i + 1, n_bi)
                if bool(ar_sets[i] & ar_sets[j])
            ]
            seed_bi = LCG_SEED_BASE + 777000 + len(bilingual_sweep) * 1000
            for b in range(MULTISHUFFLE_B):
                perm = det_shuffle_exact(idxs, seed_bi + b)
                lost_b = sum(1 for i, j in ar_pair_list if not (en_sets[perm[i]] & en_sets[perm[j]]))
                en_null_lost_sum += lost_b
                en_null_den_sum += ar_links
                # Lower loss = better preservation; count how many null shuffles achieve <= obs loss
                if lost_b <= en_lost:
                    en_ge += 1

            bilingual_sweep[f"{a_name}__{e_name}"] = {
                "ar_variant": a_name,
                "en_variant": e_name,
                "ar_linked_pairs": ar_links,
                "en_lost_pairs": en_lost,
                "cross_disc_ar_pairs": cross_ar,
                "cross_disc_en_lost": cross_lost,
                "all_pairs_bg_en_lost": [bg_en_lost, all_pairs],
                "en_perm_null_lost_pooled": [en_null_lost_sum, en_null_den_sum],
                "en_perm_le_obs_count": en_ge,
            }

    anchor = {
        "schema_version": SCHEMA_VERSION,
        "multishuffle_b": MULTISHUFFLE_B,
        "local_window_w": LOCAL_WINDOW_W,
        "matched_local_tokens": MATCHED_LOCAL_TOKENS,
        "top_func_stripped_count": TOP_FUNC_STRIP,
        "bayt_prior_art": bayt_prior_art,
        "treatises": treatise_records,
        "within_treatise_w20_b250": within_treatise_w20,
        "k12_cross_treatise_layers": k12_layers,
        "algorithmic_cross_discipline_bridges": algorithmic_bridges,
        "thematic_root_probes": {
            "selection_rule": "author_selected_thematic_set_disclosed",
            "roots": thematic_rows,
        },
        "rasm_homography_witnesses": rasm_witnesses,
        "bilingual_scientific_catalogs": {
            "catalog_count": len(catalog_pins),
            "entry_count": n_bi,
            "catalog_pins": catalog_pins,
            "sensitivity_sweep": bilingual_sweep,
        },
    }
    raw_json = json.dumps(anchor, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    anchor["anchor_sha256"] = hashlib.sha256(raw_json).hexdigest()
    return anchor


def write_canonical_0600(path, obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
    except Exception:
        os.close(fd)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Capture live raw-Arabic primary anchor.")
    parser.add_argument("--heritage-root", required=True, help="Read-only path to islamic-scientific-heritage-text")
    parser.add_argument("--bayt-root", required=True, help="Read-only path to bayt-al-hikma-ref")
    parser.add_argument("--output", required=True, help="Output path for canonical s92_raw_arabic_anchor.json")
    args = parser.parse_args(argv)
    anchor = capture_all(args.heritage_root, args.bayt_root)
    write_canonical_0600(args.output, anchor)
    print(f"CAPTURE_OK anchor_sha256={anchor['anchor_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
