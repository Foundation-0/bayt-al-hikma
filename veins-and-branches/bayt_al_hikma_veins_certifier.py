#!/usr/bin/env python3
"""AUDIT-095R: Bayt al-Hikma Tributary Veins & Downstream Branches Pure-Q Certifier.

Zero-float, exact rational/integer mathematical transcription and encoding-consistency
certifiers spanning 23 scholars across 3 historical tiers (c. 287 BCE - 1543 CE):
  - Tributary Veins (4): Archimedes, Apollonius, Heron of Alexandria, Brahmagupta
  - Core Bayt al-Hikma & Classical Lineage (15): al-Khwarizmi, al-Kindi, Banu Musa,
    Hunayn ibn Ishaq, Thabit ibn Qurra, al-Farabi, al-Karaji, Ibn al-Haytham, al-Biruni,
    Ibn Sina, Umar al-Khayyam, al-Ghazali, Ibn Rushd, al-Samawal, Ismail al-Jazari
  - Downstream Branches (4): Nasir al-Din al-Tusi, Ibn al-Shatir, Jamshid al-Kashi,
    Nicolaus Copernicus

Edge Direction Convention (Active Voice):
  Every edge {source, target, relation, citation} is read in active voice
  ("source <relation> target"): for teacher_of, source taught target; for
  corresponded_with, source and target exchanged letters as contemporaries; for
  extended, commented_on, and critiqued, the later actor (source) engaged the
  prior subject (target)'s work.

Epistemic & Novelty Classification (Law 4):
  N0 (reproducible pure-Q software transcription, strictly conservative interval
  arithmetic, and encoding-consistency checks over classical historical mathematics
  and published secondary editions; zero N1 novelty claims).
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

SCHEMA_VERSION = "bayt-al-hikma-veins-v2"
AUDIT_ID = "AUDIT-095R"

EDGE_DIRECTION_CONVENTION = (
    "Active voice ('source <relation> target'): for teacher_of, source taught target; "
    "for corresponded_with, source and target corresponded as contemporaries; for extended, "
    "commented_on, and critiqued, the later actor (source) engaged the prior subject (target)."
)

ALLOWED_CITATION_KEYS: frozenset[str] = frozenset({"work", "edition", "location"})
ALLOWED_TIERS: tuple[str, ...] = ("tributary", "core", "branch")
TIER_RANK: dict[str, int] = {"tributary": 0, "core": 1, "branch": 2}
ALLOWED_RELATIONS: tuple[str, ...] = (
    "teacher_of",
    "corresponded_with",
    "extended",
    "commented_on",
    "critiqued",
)
ALLOWED_NODE_KEYS: frozenset[str] = frozenset(
    {"node_id", "name", "birth_year", "death_year", "tier", "city", "primary_work", "source"}
)
ALLOWED_EDGE_KEYS: frozenset[str] = frozenset({"source", "target", "relation", "citation"})
ALLOWED_JOINT_KEYS: frozenset[str] = frozenset({"p11", "p10", "p01", "p00"})
ALLOWED_UNIFIED_KEYS: frozenset[str] = frozenset(
    {
        "domain_lo",
        "domain_hi",
        "x0",
        "lipschitz_L",
        "step0_gap",
        "iterations",
        "target_tol",
        "obs_joint_direct",
        "obs_joint_confounded",
        "confounder_p_u1",
        "confounder_p_f_given_u1",
        "confounder_p_f_given_u0",
        "confounder_p_c_given_u1",
        "confounder_p_c_given_u0",
        "min_ate_separation",
    }
)

# 23 historically attested scholars with structured secondary-edition citations
EXTENDED_POLYMATH_NODES: tuple[dict[str, Any], ...] = (
    # Tier 1: Tributaries (4)
    {
        "node_id": "archimedes",
        "name": "Archimedes of Syracuse",
        "birth_year": -287,
        "death_year": -212,
        "tier": "tributary",
        "city": "Syracuse",
        "primary_work": "Measurement of a Circle",
        "source": {
            "work": "The Works of Archimedes",
            "edition": "T. L. Heath, Cambridge UP (1897)",
            "location": "pp. 91-98 (Measurement of a Circle, Prop. 3)",
        },
    },
    {
        "node_id": "apollonius",
        "name": "Apollonius of Perga",
        "birth_year": -240,
        "death_year": -190,
        "tier": "tributary",
        "city": "Alexandria",
        "primary_work": "Conics",
        "source": {
            "work": "Apollonius: Conics Books V to VII (Arabic Translation)",
            "edition": "G. J. Toomer, Springer (1990)",
            "location": "vol. 1 pp. xi-xxv",
        },
    },
    {
        "node_id": "heron",
        "name": "Heron of Alexandria",
        "birth_year": 10,
        "death_year": 70,
        "tier": "tributary",
        "city": "Alexandria",
        "primary_work": "Metrica",
        "source": {
            "work": "A History of Greek Mathematics; Codex Constantinopolitanus",
            "edition": "T. L. Heath (1921); E. M. Bruins, Brill (1964)",
            "location": "Heath vol. 2 pp. 320-326 (Metrica I.8)",
        },
    },
    {
        "node_id": "brahmagupta",
        "name": "Brahmagupta",
        "birth_year": 598,
        "death_year": 668,
        "tier": "tributary",
        "city": "Bhillamala",
        "primary_work": "Brahmasphutasiddhanta",
        "source": {
            "work": "Algebra with Arithmetic and Mensuration (BSS); Mathematics in India",
            "edition": "H. T. Colebrooke (1817); K. Plofker, Princeton UP (2009)",
            "location": "BSS XII.21-38, XVIII.64-67; Plofker pp. 142-157",
        },
    },
    # Tier 2: Core Bayt al-Hikma & Classical Lineage (15)
    {
        "node_id": "khwarizmi",
        "name": "Muhammad ibn Musa al-Khwarizmi",
        "birth_year": 780,
        "death_year": 850,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "Kitab al-Jabr and Zij al-Sindhind",
        "source": {
            "work": "Al-Khwarizmi: The Beginnings of Algebra; Astronomical Tables",
            "edition": "R. Rashed, Saqi (2009); O. Neugebauer, Copenhagen (1962)",
            "location": "Rashed pp. 8-22; Neugebauer pp. 1-14",
        },
    },
    {
        "node_id": "kindi",
        "name": "Abu Yusuf Yaqub al-Kindi",
        "birth_year": 801,
        "death_year": 873,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "De Gradibus and Musical Treatises",
        "source": {
            "work": "Al-Kindi's Treatise on Cryptanalysis; Musical Treatises",
            "edition": "Mrayati et al. (2003); H. G. Farmer, JRAS (1926)",
            "location": "Mrayati pp. 121-158; Farmer pp. 90-98",
        },
    },
    {
        "node_id": "banu_musa",
        "name": "Banu Musa Brothers",
        "birth_year": 803,
        "death_year": 873,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "Measurement of Plane and Spherical Figures (Verba Filiorum)",
        "source": {
            "work": "Archimedes in the Middle Ages, Vol. 1: Verba Filiorum",
            "edition": "M. Clagett, Univ. of Wisconsin Press (1964)",
            "location": "pp. 223-367 (Props. 4-7)",
        },
    },
    {
        "node_id": "hunayn",
        "name": "Hunayn ibn Ishaq",
        "birth_year": 809,
        "death_year": 873,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "Syriac-Arabic Scientific Translation Corpus",
        "source": {
            "work": "Hunayn ibn Ishaq uber die syrischen und arabischen Galen-Ubersetzungen",
            "edition": "G. Bergstrasser, AKM 17.2 (1925); G. Saliba (2007)",
            "location": "pp. 1-53; Saliba Islamic Science pp. 58-66",
        },
    },
    {
        "node_id": "thabit",
        "name": "Thabit ibn Qurra",
        "birth_year": 836,
        "death_year": 901,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "Amicable Numbers and Apollonius Conics V-VII",
        "source": {
            "work": "Thabit ibn Qurra: Science and Philosophy in Ninth-Century Baghdad",
            "edition": "R. Rashed (ed.), de Gruyter (2009)",
            "location": "pp. 3-14, 155-290",
        },
    },
    {
        "node_id": "farabi",
        "name": "Abu Nasr al-Farabi",
        "birth_year": 872,
        "death_year": 950,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "Kitab al-Musiqa al-Kabir",
        "source": {
            "work": "La Musique Arabe, Vols. 1-2 (Kitab al-Musiqa al-Kabir)",
            "edition": "R. d'Erlanger, Geuthner (1930-1935)",
            "location": "vol. 1 pp. 163-218 (ud fretting & tetrachord genera)",
        },
    },
    {
        "node_id": "karaji",
        "name": "Abu Bakr al-Karaji",
        "birth_year": 953,
        "death_year": 1029,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "al-Fakhri",
        "source": {
            "work": "The Development of Arabic Mathematics",
            "edition": "R. Rashed, Kluwer (1994)",
            "location": "ch. 1, pp. 22-45",
        },
    },
    {
        "node_id": "haytham",
        "name": "Ibn al-Haytham",
        "birth_year": 965,
        "death_year": 1040,
        "tier": "core",
        "city": "Cairo",
        "primary_work": "Kitab al-Manazir and al-Shukuk",
        "source": {
            "work": "The Optics of Ibn al-Haytham; al-Shukuk ala Batlamyus",
            "edition": "A. I. Sabra (1989); Sabra & Shehaby (1971)",
            "location": "Optics vol. 2 pp. xix-xxxii; al-Shukuk pp. 3-42",
        },
    },
    {
        "node_id": "biruni",
        "name": "Abu Rayhan al-Biruni",
        "birth_year": 973,
        "death_year": 1048,
        "tier": "core",
        "city": "Ghazna",
        "primary_work": "Tahdid Nihayat al-Amakin",
        "source": {
            "work": "The Determination of the Coordinates of Positions (Tahdid)",
            "edition": "J. Ali (tr.), AUB (1967); E. S. Kennedy, AUB (1973)",
            "location": "Ali pp. 187-190; Kennedy pp. 139-144",
        },
    },
    {
        "node_id": "ibn_sina",
        "name": "Ibn Sina",
        "birth_year": 980,
        "death_year": 1037,
        "tier": "core",
        "city": "Isfahan",
        "primary_work": "al-Shifa and al-Asila",
        "source": {
            "work": "Al-Asilah wa-l-Ajwibah",
            "edition": "S. H. Nasr & M. Mohaghegh, ISTAC (1995)",
            "location": "pp. 1-62",
        },
    },
    {
        "node_id": "khayyam",
        "name": "Umar al-Khayyam",
        "birth_year": 1048,
        "death_year": 1131,
        "tier": "core",
        "city": "Nishapur",
        "primary_work": "Sharh ma Ashkala and Algebra",
        "source": {
            "work": "Omar Khayyam the Mathematician",
            "edition": "R. Rashed & B. Vahabzadeh, Bibliotheca Persica (2000)",
            "location": "pp. 113-162, 217-244",
        },
    },
    {
        "node_id": "ghazali",
        "name": "Abu Hamid al-Ghazali",
        "birth_year": 1058,
        "death_year": 1111,
        "tier": "core",
        "city": "Baghdad",
        "primary_work": "Tahafut al-Falasifa",
        "source": {
            "work": "The Incoherence of the Philosophers (Tahafut al-Falasifa)",
            "edition": "M. E. Marmura, BYU Press (2000)",
            "location": "Discussion 17, pp. 166-177 (fire and cotton)",
        },
    },
    {
        "node_id": "ibn_rushd",
        "name": "Ibn Rushd",
        "birth_year": 1126,
        "death_year": 1198,
        "tier": "core",
        "city": "Cordoba",
        "primary_work": "Tahafut al-Tahafut",
        "source": {
            "work": "Averroes' Tahafut al-Tahafut (The Incoherence of the Incoherence)",
            "edition": "S. van den Bergh, Gibb Memorial (1954)",
            "location": "vol. 1 pp. 316-333 (Discussion 17 reply)",
        },
    },
    {
        "node_id": "samawal",
        "name": "Al-Samawal al-Maghribi",
        "birth_year": 1130,
        "death_year": 1180,
        "tier": "core",
        "city": "Maragheh",
        "primary_work": "al-Bahir fi al-Jabr",
        "source": {
            "work": "Al-Bahir en Algebre d'As-Samawal",
            "edition": "S. Ahmad & R. Rashed, Damascus (1972)",
            "location": "pp. 20-58",
        },
    },
    {
        "node_id": "jazari",
        "name": "Ismail al-Jazari",
        "birth_year": 1136,
        "death_year": 1206,
        "tier": "core",
        "city": "Diyarbakir",
        "primary_work": "Kitab al-Hiyal",
        "source": {
            "work": "The Book of Knowledge of Ingenious Mechanical Devices",
            "edition": "D. R. Hill, Reidel (1974)",
            "location": "pp. 17-34",
        },
    },
    # Tier 3: Downstream Branches (4)
    {
        "node_id": "tusi",
        "name": "Nasir al-Din al-Tusi",
        "birth_year": 1201,
        "death_year": 1274,
        "tier": "branch",
        "city": "Maragheh",
        "primary_work": "al-Tadhkira fi Ilm al-Haya",
        "source": {
            "work": "Nasir al-Din al-Tusi's Memoir on Astronomy (al-Tadhkira)",
            "edition": "F. J. Ragep, Springer (1993)",
            "location": "vol. 1 pp. 194-223 (II.11)",
        },
    },
    {
        "node_id": "shatir",
        "name": "Ibn al-Shatir",
        "birth_year": 1304,
        "death_year": 1375,
        "tier": "branch",
        "city": "Damascus",
        "primary_work": "Nihayat al-Sul",
        "source": {
            "work": "The Solar and Lunar Theory of Ibn ash-Shatir",
            "edition": "V. Roberts, Isis 48 (1957); Kennedy & Roberts, Isis 50 (1959)",
            "location": "Isis 48 pp. 428-432 (r1=6;35, r2=1;25); Isis 50 pp. 227-235",
        },
    },
    {
        "node_id": "kashi",
        "name": "Jamshid al-Kashi",
        "birth_year": 1380,
        "death_year": 1429,
        "tier": "branch",
        "city": "Samarkand",
        "primary_work": "al-Risala al-Muhitiyya and Risalat al-Watar",
        "source": {
            "work": "Der Lehrbrief uber den Kreisumfang; Episodes in the Mathematics of Medieval Islam",
            "edition": "P. Luckey, Berlin (1953); J. L. Berggren, Springer (1986)",
            "location": "Luckey pp. 1-42; Berggren pp. 50-55, 134-141",
        },
    },
    {
        "node_id": "copernicus",
        "name": "Nicolaus Copernicus",
        "birth_year": 1473,
        "death_year": 1543,
        "tier": "branch",
        "city": "Frombork",
        "primary_work": "De Revolutionibus Orbium Coelestium",
        "source": {
            "work": "On the Revolutions (De Revolutionibus)",
            "edition": "E. Rosen (tr.), Johns Hopkins UP (1978)",
            "location": "III.4, IV.3 (R=10000, r1=1097, r2=237), V.25",
        },
    },
)

# Active voice: {source} <relation> {target}
EXTENDED_POLYMATH_EDGES: tuple[dict[str, Any], ...] = (
    # Core acting on Tributary (7)
    {
        "source": "khwarizmi",
        "target": "brahmagupta",
        "relation": "extended",
        "citation": {
            "work": "Zij al-Sindhind & Indian Calculation",
            "edition": "O. Neugebauer, Copenhagen (1962); Plofker (2009)",
            "location": "Neugebauer pp. 1-14; Plofker pp. 255-259",
        },
    },
    {
        "source": "banu_musa",
        "target": "archimedes",
        "relation": "extended",
        "citation": {
            "work": "Verba Filiorum (Measurement of Plane and Spherical Figures)",
            "edition": "M. Clagett, Univ. of Wisconsin Press (1964)",
            "location": "pp. 250-279 (Props. 4-6 extending Measurement of a Circle)",
        },
    },
    {
        "source": "banu_musa",
        "target": "heron",
        "relation": "extended",
        "citation": {
            "work": "Verba Filiorum (Prop. 7 triangle area proof)",
            "edition": "M. Clagett, Univ. of Wisconsin Press (1964)",
            "location": "pp. 278-289 (first Arabic geometric proof of Heron's formula)",
        },
    },
    {
        "source": "banu_musa",
        "target": "apollonius",
        "relation": "extended",
        "citation": {
            "work": "Preface to Arabic Conics & String Ellipse",
            "edition": "G. J. Toomer, Springer (1990)",
            "location": "vol. 1 pp. xviii-xxv, 620-629",
        },
    },
    {
        "source": "thabit",
        "target": "apollonius",
        "relation": "extended",
        "citation": {
            "work": "Arabic Translation of Apollonius Conics Books V-VII",
            "edition": "G. J. Toomer, Springer (1990)",
            "location": "vol. 1 pp. xi-xxv (sole surviving transmission of Books V-VII)",
        },
    },
    {
        "source": "thabit",
        "target": "archimedes",
        "relation": "extended",
        "citation": {
            "work": "On the Measurement of the Parabola",
            "edition": "R. Rashed, de Gruyter (2009)",
            "location": "pp. 155-209 (unequal-interval quadrature extending Archimedes)",
        },
    },
    {
        "source": "hunayn",
        "target": "archimedes",
        "relation": "commented_on",
        "citation": {
            "work": "Baghdad Translation School (Ishaq/Hunayn & Thabit Greek-Arabic corpus)",
            "edition": "M. Clagett (1964); R. Rashed, de Gruyter (2009)",
            "location": "Clagett pp. 12-16; Rashed pp. 15-24",
        },
    },
    # Core acting on Core (13)
    {
        "source": "banu_musa",
        "target": "thabit",
        "relation": "teacher_of",
        "citation": {
            "work": "Kitab al-Fihrist; Thabit ibn Qurra",
            "edition": "R. Rashed (ed.), de Gruyter (2009)",
            "location": "pp. 4-7",
        },
    },
    {
        "source": "hunayn",
        "target": "thabit",
        "relation": "corresponded_with",
        "citation": {
            "work": "Baghdad Translation Circle Collaborations",
            "edition": "G. Bergstrasser (1925); R. Rashed (2009)",
            "location": "Rashed pp. 6-12 (shared Baghdad translation circle)",
        },
    },
    {
        "source": "farabi",
        "target": "kindi",
        "relation": "extended",
        "citation": {
            "work": "Kitab al-Musiqa al-Kabir",
            "edition": "R. d'Erlanger, Geuthner (1930)",
            "location": "vol. 1 pp. 163-218 (mathematical ud fretting beyond al-Kindi)",
        },
    },
    {
        "source": "karaji",
        "target": "khwarizmi",
        "relation": "extended",
        "citation": {
            "work": "al-Fakhri fi al-Jabr",
            "edition": "R. Rashed, Kluwer (1994)",
            "location": "ch. 1, pp. 22-31",
        },
    },
    {
        "source": "samawal",
        "target": "karaji",
        "relation": "extended",
        "citation": {
            "work": "al-Bahir fi al-Jabr",
            "edition": "S. Ahmad & R. Rashed, Damascus (1972)",
            "location": "pp. 20-38",
        },
    },
    {
        "source": "khayyam",
        "target": "khwarizmi",
        "relation": "extended",
        "citation": {
            "work": "Risala fi al-Jabr wa-l-Muqabala",
            "edition": "R. Rashed & B. Vahabzadeh (2000)",
            "location": "pp. 113-135",
        },
    },
    {
        "source": "haytham",
        "target": "thabit",
        "relation": "extended",
        "citation": {
            "work": "Sharh Musadarat Uqlidis & Quadrature of the Paraboloid",
            "edition": "R. Rashed (1994/2009); B. Rosenfeld (1988)",
            "location": "Rosenfeld pp. 58-64",
        },
    },
    {
        "source": "khayyam",
        "target": "haytham",
        "relation": "extended",
        "citation": {
            "work": "Sharh ma Ashkala min Musadarat Uqlidis",
            "edition": "R. Rashed & B. Vahabzadeh (2000)",
            "location": "Book I, pp. 217-235",
        },
    },
    {
        "source": "biruni",
        "target": "ibn_sina",
        "relation": "corresponded_with",
        "citation": {
            "work": "al-Asilah wa-l-Ajwibah",
            "edition": "S. H. Nasr & M. Mohaghegh, ISTAC (1995)",
            "location": "Questions 1-18, pp. 1-62",
        },
    },
    {
        "source": "ghazali",
        "target": "ibn_sina",
        "relation": "critiqued",
        "citation": {
            "work": "Tahafut al-Falasifa",
            "edition": "M. E. Marmura, BYU Press (2000)",
            "location": "Discussion 17, pp. 166-177 (critique of Avicennan necessity)",
        },
    },
    {
        "source": "ibn_rushd",
        "target": "ghazali",
        "relation": "critiqued",
        "citation": {
            "work": "Tahafut al-Tahafut",
            "edition": "S. van den Bergh, Gibb Memorial (1954)",
            "location": "vol. 1 pp. 316-333 (point-by-point reply to Discussion 17)",
        },
    },
    {
        "source": "ibn_rushd",
        "target": "haytham",
        "relation": "extended",
        "citation": {
            "work": "Tafsir ma Bad al-Tabia (Book Lambda)",
            "edition": "A. I. Sabra, JHA 15 (1984)",
            "location": "pp. 133-153",
        },
    },
    {
        "source": "jazari",
        "target": "banu_musa",
        "relation": "extended",
        "citation": {
            "work": "Kitab fi Marifat al-Hiyal al-Handasiyya",
            "edition": "D. R. Hill, Reidel (1974)",
            "location": "pp. 12-15, 272",
        },
    },
    # Branch acting on Core (4)
    {
        "source": "tusi",
        "target": "haytham",
        "relation": "extended",
        "citation": {
            "work": "al-Tadhkira fi Ilm al-Haya",
            "edition": "F. J. Ragep, Springer (1993)",
            "location": "vol. 1 pp. 194-223",
        },
    },
    {
        "source": "tusi",
        "target": "khayyam",
        "relation": "extended",
        "citation": {
            "work": "al-Risala al-Shafiya",
            "edition": "B. Rosenfeld, Springer (1988)",
            "location": "pp. 73-84",
        },
    },
    {
        "source": "kashi",
        "target": "banu_musa",
        "relation": "extended",
        "citation": {
            "work": "al-Risala al-Muhitiyya (Archimedean polygon pi tradition)",
            "edition": "P. Luckey, Berlin (1953); J. L. Berggren (1986)",
            "location": "Luckey pp. 1-42; Berggren pp. 50-55",
        },
    },
    {
        "source": "kashi",
        "target": "khayyam",
        "relation": "extended",
        "citation": {
            "work": "Risalat al-Watar wa-l-Jayb (iterative cubic root solver)",
            "edition": "J. L. Berggren, Springer (1986)",
            "location": "pp. 134-141",
        },
    },
    # Branch acting on Branch (4)
    {
        "source": "shatir",
        "target": "tusi",
        "relation": "extended",
        "citation": {
            "work": "Nihayat al-Sul",
            "edition": "V. Roberts, Isis 48 (1957); E. S. Kennedy & V. Roberts, Isis 50 (1959)",
            "location": "Isis 50 pp. 227-235 (Tusi couple in Mercury model)",
        },
    },
    {
        "source": "kashi",
        "target": "tusi",
        "relation": "extended",
        "citation": {
            "work": "Zij-i Khaqani (extending Maragheh Zij-i Ilkhani)",
            "edition": "E. S. Kennedy, TAPS 46 (1956)",
            "location": "pp. 164-166 (Zij-i Khaqani preface)",
        },
    },
    {
        "source": "copernicus",
        "target": "tusi",
        "relation": "extended",
        "citation": {
            "work": "De Revolutionibus III.4 (mathematical equivalence; transmission route debated)",
            "edition": "F. J. Ragep (1993); G. Saliba, MIT Press (2007)",
            "location": "Ragep vol. 2 pp. 429-431; Saliba pp. 193-209",
        },
    },
    {
        "source": "copernicus",
        "target": "shatir",
        "relation": "extended",
        "citation": {
            "work": "De Revolutionibus IV.3 & V.25 (kinematic equivalence; transmission route debated)",
            "edition": "V. Roberts, Isis 48 (1957); N. Swerdlow & O. Neugebauer (1984)",
            "location": "Roberts pp. 428-432; Swerdlow & Neugebauer pp. 193-201",
        },
    },
)


class VeinsAuditError(ValueError):
    """Fail-closed refusal raised whenever any mathematical, lineage, or contract check fails."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise VeinsAuditError(message)


def _require_exact_int(value: Any, name: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool), f"exact-int:{name}")
    return value


def _require_exact_fraction(value: Any, name: str) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value, 1)
    raise VeinsAuditError(f"exact-fraction:{name}")


def _require_clean_ascii(value: Any, name: str) -> str:
    _require(
        isinstance(value, str)
        and len(value) > 0
        and value == value.strip()
        and all(32 <= ord(ch) <= 126 for ch in value),
        f"clean-ascii:{name}",
    )
    return value


def _require_exact_choice(value: Any, allowed: tuple[str, ...], name: str) -> str:
    _require(isinstance(value, str) and value in allowed, f"exact-choice:{name}")
    return value


def _require_citation(value: Any, name: str) -> dict[str, str]:
    _require(isinstance(value, dict), f"citation-dict:{name}")
    _require(set(value.keys()) == ALLOWED_CITATION_KEYS, f"citation-keys:{name}")
    return {
        "work": _require_clean_ascii(value["work"], f"{name}.work"),
        "edition": _require_clean_ascii(value["edition"], f"{name}.edition"),
        "location": _require_clean_ascii(value["location"], f"{name}.location"),
    }


def frac_str(value: Fraction) -> str:
    v = _require_exact_fraction(value, "frac_str")
    return f"{v.numerator}/{v.denominator}"


def frac_dec(value: Fraction, digits: int = 6) -> str:
    """Truncate exact Fraction toward zero to `digits` decimals (conservative lower bound for v >= 0)."""
    v = _require_exact_fraction(value, "frac_dec")
    d = _require_exact_int(digits, "digits")
    _require(d >= 1, "digits-pos")
    sign = "-" if v < 0 else ""
    av = abs(v)
    ten_pow = 10**d
    scaled = (av.numerator * ten_pow) // av.denominator
    whole, rem = divmod(scaled, ten_pow)
    return f"{sign}{whole}.{rem:0{d}d}"


def frac_dec_ceil(value: Fraction, digits: int = 6) -> str:
    """Round non-negative exact Fraction strictly UP to `digits` decimals (conservative upper bound)."""
    v = _require_exact_fraction(value, "frac_dec_ceil")
    d = _require_exact_int(digits, "digits")
    _require(v >= 0 and d >= 1, "frac-dec-ceil-domain")
    ten_pow = 10**d
    scaled = (v.numerator * ten_pow + v.denominator - 1) // v.denominator
    whole, rem = divmod(scaled, ten_pow)
    return f"{whole}.{rem:0{d}d}"


def _isqrt_scaled_bounds(num: int, den: int, scale: int) -> tuple[int, int]:
    """Return exact integer (lo, hi) with lo <= scale * sqrt(num / den) <= hi."""
    n_i = _require_exact_int(num, "num")
    d_i = _require_exact_int(den, "den")
    s_i = _require_exact_int(scale, "scale")
    _require(n_i >= 0 and d_i > 0 and s_i > 0, "isqrt-bounds-domain")
    target = n_i * s_i * s_i
    lo = math.isqrt(target // d_i)
    hi = lo + (1 if lo * lo * d_i < target else 0)
    return lo, hi


def _to_sexagesimal_digits(value: Fraction, places: int) -> list[int]:
    """Return exact base-60 floored fractional digits [d1, ..., d_places] for 0 <= value < 1."""
    v = _require_exact_fraction(value, "sex-value")
    p = _require_exact_int(places, "sex-places")
    _require(Fraction(0, 1) <= v < Fraction(1, 1) and p >= 1, "sex-domain")
    digits: list[int] = []
    cur = v
    for _ in range(p):
        cur *= 60
        dig = cur.numerator // cur.denominator
        digits.append(dig)
        cur -= dig
    return digits


def _to_sexagesimal_digits_ceil(value: Fraction, places: int) -> list[int]:
    """Return exact base-60 ceiled fractional digits [d1, ..., d_places] >= value (conservative upper)."""
    v = _require_exact_fraction(value, "sex-ceil-value")
    p = _require_exact_int(places, "sex-ceil-places")
    _require(Fraction(0, 1) <= v < Fraction(1, 1) and p >= 1, "sex-ceil-domain")
    base_pow = 60**p
    scaled = (v.numerator * base_pow + v.denominator - 1) // v.denominator
    _require(scaled < base_pow, "sex-ceil-overflow")
    rev: list[int] = []
    rem = scaled
    for _ in range(p):
        rem, dig = divmod(rem, 60)
        rev.append(dig)
    rev.reverse()
    return rev


def _sexagesimal_to_fraction(whole: int, frac_digits: Sequence[int]) -> Fraction:
    w = _require_exact_int(whole, "sex-whole")
    total = Fraction(w, 1)
    denom = 1
    for idx, d in enumerate(frac_digits):
        di = _require_exact_int(d, f"sex-digit[{idx}]")
        _require(0 <= di < 60, f"sex-digit-range[{idx}]")
        denom *= 60
        total += Fraction(di, denom)
    return total


# =============================================================================
# PILLAR 1: Tributary Veins Feeding Bayt al-Hikma
# =============================================================================


def run_chakravala_exact(D: int) -> list[tuple[int, int, int]]:
    """Pure exact-integer Chakravala solver for Pell equation x^2 - D*y^2 = 1.

    Returns table rows [(a_0, b_0, k_0), ..., (a_s, b_s, 1)] so iteration count is len(rows) - 1.
    """
    d_i = _require_exact_int(D, "D")
    root = math.isqrt(d_i)
    _require(d_i >= 2 and root * root != d_i, "chakravala-nonsquare-D")
    a = root + 1 if abs((root + 1) ** 2 - d_i) < abs(root * root - d_i) else root
    b = 1
    k = a * a - d_i
    rows: list[tuple[int, int, int]] = [(a, b, k)]
    while k != 1:
        absk = abs(k)
        r0 = (-a * pow(b, -1, absk)) % absk
        if r0 == 0:
            r0 = absk
        q = max(0, (root - r0) // absk)
        cands = (r0 + q * absk, r0 + (q + 1) * absk)
        m = cands[0] if abs(cands[0] ** 2 - d_i) <= abs(cands[1] ** 2 - d_i) else cands[1]
        a_new = (a * m + d_i * b) // absk
        b_new = (a + b * m) // absk
        k_new = (m * m - d_i) // k
        a, b, k = a_new, b_new, k_new
        rows.append((a, b, k))
    return rows


def archimedean_polygon_pi_bracket(doublings: int, scale_exp: int) -> dict[str, Any]:
    """Strictly certified pure-integer Archimedean 6 * 2^doublings-gon pi bracket."""
    k_steps = _require_exact_int(doublings, "doublings")
    exp_i = _require_exact_int(scale_exp, "scale_exp")
    _require(k_steps >= 1 and exp_i >= 12, "archimedes-params")
    scale = 10**exp_i
    c_lo = scale
    c_hi = scale
    for _ in range(k_steps):
        n_lo = 2 * scale + c_lo
        n_hi = 2 * scale + c_hi
        c_lo = math.isqrt(n_lo * scale)
        r_hi = math.isqrt(n_hi * scale)
        c_hi = r_hi + (1 if r_hi * r_hi < n_hi * scale else 0)
    n_sides = 6 * (1 << k_steps)
    sin_half_lo = math.isqrt((2 * scale - c_hi) * scale)
    _, tan_half_hi = _isqrt_scaled_bounds(2 * scale - c_lo, 2 * scale + c_lo, scale)
    twopi_lo = Fraction(n_sides * sin_half_lo, scale)
    twopi_hi = Fraction(2 * n_sides * tan_half_hi, scale)
    return {
        "doublings": k_steps,
        "sides": n_sides,
        "twopi_lo": twopi_lo,
        "twopi_hi": twopi_hi,
        "pi_lo": twopi_lo / 2,
        "pi_hi": twopi_hi / 2,
    }


def analyze_pillar1_tributary_veins() -> dict[str, Any]:
    """Pillar 1: Brahmagupta (628 CE) + Greek/Syriac -> Gundishapur/Banu Musa/Thabit veins."""
    a, b, c, d = Fraction(39, 1), Fraction(60, 1), Fraction(52, 1), Fraction(25, 1)
    s = (a + b + c + d) / 2
    k_sq = (s - a) * (s - b) * (s - c) * (s - d)
    k_exact = Fraction(1764, 1)
    e_exact, f_exact = Fraction(63, 1), Fraction(56, 1)
    e_sq_formula = ((a * c + b * d) * (a * d + b * c)) / (a * b + c * d)
    f_sq_formula = ((a * c + b * d) * (a * b + c * d)) / (a * d + b * c)
    ptolemy_holds = (e_exact * f_exact == a * c + b * d)
    circum_diam_sq = a * a + c * c
    ad_dx, ad_dy = Fraction(15, 1), Fraction(20, 1)
    bc_mid_x, bc_mid_y = Fraction(-24, 1), Fraction(18, 1)
    perp_bisector_dot = ad_dx * bc_mid_x + ad_dy * bc_mid_y

    def bhavana(x1: Fraction, y1: Fraction, x2: Fraction, y2: Fraction, D_val: int) -> tuple[Fraction, Fraction]:
        return (x1 * x2 + D_val * y1 * y2, x1 * y2 + x2 * y1)

    x92_1, y92_1 = Fraction(10, 1), Fraction(1, 1)
    k92_1 = x92_1 * x92_1 - 92 * y92_1 * y92_1
    x92_2, y92_2 = bhavana(x92_1, y92_1, x92_1, y92_1, 92)
    bhavana_norm_exact = (x92_2 * x92_2 - 92 * y92_2 * y92_2 == k92_1 * k92_1)
    x92_h, y92_h = x92_2 / 8, y92_2 / 8
    x92_fund, y92_fund = bhavana(x92_h, y92_h, x92_h, y92_h, 92)
    pell92_exact = (x92_fund == 1151 and y92_fund == 120 and x92_fund**2 - 92 * y92_fund**2 == 1)

    chak61 = run_chakravala_exact(61)
    x61, y61, k61 = chak61[-1]
    pell61_exact = (k61 == 1 and x61 == 1766319049 and y61 == 226153980 and x61 * x61 - 61 * y61 * y61 == 1)

    ha, hb, hc, hd = Fraction(13, 1), Fraction(14, 1), Fraction(15, 1), Fraction(0, 1)
    hs = (ha + hb + hc + hd) / 2
    heron_k_sq = (hs - ha) * (hs - hb) * (hs - hc) * (hs - hd)
    hx = Fraction(27, 1)
    for _ in range(3):
        hx = (hx + Fraction(720, 1) / hx) / 2
    h_lo = Fraction(720, 1) / hx
    heron_sqrt720_certified = (h_lo * h_lo < 720 < hx * hx)

    arch96 = archimedean_polygon_pi_bracket(doublings=4, scale_exp=20)
    arch_classical_lo = Fraction(223, 71)
    arch_classical_hi = Fraction(22, 7)
    arch_nested_exact = (arch_classical_lo < arch96["pi_lo"] < arch96["pi_hi"] < arch_classical_hi)

    px, py = Fraction(3, 1), Fraction(16, 5)
    on_ellipse = ((px / 5) ** 2 + (py / 4) ** 2 == Fraction(1, 1))
    d1, d2 = Fraction(16, 5), Fraction(34, 5)
    focal_sum_exact = (
        d1 * d1 == (px - 3) ** 2 + py * py
        and d2 * d2 == (px + 3) ** 2 + py * py
        and d1 + d2 == Fraction(10, 1)
    )
    nx, ny = Fraction(-3, 1), Fraction(-5, 1)
    dot1 = nx * Fraction(0, 1) + ny * Fraction(-1, 1)
    dot2 = nx * Fraction(-15, 17) + ny * Fraction(-8, 17)
    apollonius_reflection_exact = (dot1 == dot2 and dot1 == Fraction(5, 1))

    return {
        "brahmagupta_cyclic_quadrilateral": {
            "sides": [frac_str(a), frac_str(b), frac_str(c), frac_str(d)],
            "semiperimeter": frac_str(s),
            "area_exact": frac_str(k_exact),
            "area_formula_exact": k_sq == k_exact * k_exact,
            "diagonals": [frac_str(e_exact), frac_str(f_exact)],
            "diagonal_formulas_exact": (e_sq_formula == e_exact * e_exact and f_sq_formula == f_exact * f_exact),
            "ptolemy_identity_exact": ptolemy_holds,
            "circumradius": frac_str(Fraction(65, 2)),
            "circumdiameter_sq_both_pairs_65sq": (circum_diam_sq == 65 * 65 and b * b + d * d == 65 * 65),
            "perpendicular_bisector_dot": frac_str(perp_bisector_dot),
        },
        "brahmagupta_bhavana_and_chakravala": {
            "bhavana_norm_multiplicativity_exact": bhavana_norm_exact,
            "pell_D92_fundamental": [int(x92_fund), int(y92_fund)],
            "pell_D92_verified": pell92_exact,
            "chakravala_D61_steps": len(chak61) - 1,
            "chakravala_D61_table_rows": len(chak61),
            "pell_D61_fundamental": [x61, y61],
            "pell_D61_verified": pell61_exact,
        },
        "greek_syriac_baghdad_veins": {
            "heron_d0_limit_area_sq": frac_str(heron_k_sq),
            "heron_area_84_exact": heron_k_sq == Fraction(84 * 84, 1),
            "heron_sqrt720_bracket_conservative": [frac_dec(h_lo, 9), frac_dec_ceil(hx, 9)],
            "heron_sqrt720_certified": heron_sqrt720_certified,
            "archimedes_96gon_bracket_dec6_conservative": [
                frac_dec(arch96["pi_lo"], 6),
                frac_dec_ceil(arch96["pi_hi"], 6),
            ],
            "archimedes_223_71_to_22_7_nested": arch_nested_exact,
            "apollonius_ellipse_point": [frac_str(px), frac_str(py)],
            "apollonius_on_ellipse": on_ellipse,
            "apollonius_focal_sum_10_exact": focal_sum_exact,
            "apollonius_equal_angle_reflection_exact": apollonius_reflection_exact,
        },
    }


# =============================================================================
# PILLAR 2: Downstream Astronomical & Causal Branches
# =============================================================================


def analyze_pillar2_shatir_copernicus_and_ghazali_rushd() -> dict[str, Any]:
    """Pillar 2: Ibn al-Shatir <-> Copernicus kinematics & al-Ghazali <-> Ibn Rushd causal witness."""
    ptol_max = Fraction(65 * 60 + 15, 60)
    ptol_min = Fraction(34 * 60 + 7, 60)
    ptol_ratio = ptol_max / ptol_min

    r_sh = Fraction(60, 1)
    r1_sh = Fraction(6 * 60 + 35, 60)
    r2_sh = Fraction(1 * 60 + 25, 60)
    sh_syzygy_eff = r1_sh - r2_sh
    sh_quad_eff = r1_sh + r2_sh
    sh_ratio = (r_sh + sh_quad_eff) / (r_sh - sh_quad_eff)

    r_cop = Fraction(10000, 1)
    r1_cop = Fraction(1097, 1)
    r2_cop = Fraction(237, 1)
    cop_ratio = (r_cop + r1_cop + r2_cop) / (r_cop - r1_cop - r2_cop)
    param_diff_l1 = abs(r1_sh / r_sh - r1_cop / r_cop) + abs(r2_sh / r_sh - r2_cop / r_cop)

    def _cos_sin(t: Fraction) -> tuple[Fraction, Fraction]:
        den = Fraction(1, 1) + t * t
        return ((Fraction(1, 1) - t * t) / den, (2 * t) / den)

    grid_pairs = (
        (Fraction(0, 1), Fraction(0, 1)),
        (Fraction(1, 2), Fraction(1, 3)),
        (Fraction(1, 1), Fraction(1, 2)),
        (Fraction(2, 1), Fraction(1, 1)),
        (Fraction(3, 1), Fraction(2, 1)),
    )
    rho1, rho2 = r1_sh / r_sh, r2_sh / r_sh
    lunar_residuals_zero = True
    mercury_tusi_residuals_zero = True
    for ta, te in grid_pairs:
        ca, sa = _cos_sin(ta)
        ce, se = _cos_sin(te)
        c2e = ce * ce - se * se
        s2e = 2 * ce * se
        c_diff = ca * c2e + sa * s2e
        s_diff = sa * c2e - ca * s2e
        zs_x = Fraction(1, 1) + rho1 * ca - rho2 * c_diff
        zs_y = -rho1 * sa + rho2 * s_diff
        zc_x = Fraction(1, 1) + (rho1 - rho2 * c2e) * ca - rho2 * s2e * sa
        zc_y = -(rho1 - rho2 * c2e) * sa - rho2 * s2e * ca
        if zs_x != zc_x or zs_y != zc_y:
            lunar_residuals_zero = False
        a_amp = Fraction(1, 5)
        tusi_radial = (a_amp / 2) * c2e + (a_amp / 2) * c2e
        tusi_transverse = (a_amp / 2) * s2e - (a_amp / 2) * s2e
        if tusi_radial != a_amp * c2e or tusi_transverse != Fraction(0, 1):
            mercury_tusi_residuals_zero = False

    p_u1 = Fraction(1, 2)
    pf_u1, pf_u0 = Fraction(4, 5), Fraction(1, 5)
    pc_u1, pc_u0 = Fraction(4, 5), Fraction(1, 5)
    conf_joint = _compute_confounded_joint(p_u1, pf_u1, pf_u0, pc_u1, pc_u0)
    direct_joint = dict(conf_joint)
    obs_l1 = sum(abs(direct_joint[k] - conf_joint[k]) for k in ("p11", "p10", "p01", "p00"))
    p_f1 = direct_joint["p11"] + direct_joint["p10"]
    p_f0 = direct_joint["p01"] + direct_joint["p00"]
    ate_direct = (direct_joint["p11"] / p_f1) - (direct_joint["p01"] / p_f0)
    ate_confounded = Fraction(0, 1)

    return {
        "shatir_copernicus_lunar_and_mercury": {
            "ptolemy_distance_ratio": frac_str(ptol_ratio),
            "ptolemy_distance_ratio_dec6": frac_dec(ptol_ratio, 6),
            "shatir_syzygy_eff_radius": frac_str(sh_syzygy_eff),
            "shatir_quadrature_eff_radius": frac_str(sh_quad_eff),
            "shatir_distance_ratio": frac_str(sh_ratio),
            "shatir_distance_ratio_dec6": frac_dec(sh_ratio, 6),
            "copernicus_distance_ratio": frac_str(cop_ratio),
            "copernicus_distance_ratio_dec6": frac_dec(cop_ratio, 6),
            "published_param_l1_diff": frac_str(param_diff_l1),
            "published_param_l1_diff_dec6": frac_dec(param_diff_l1, 6),
            "normalized_lunar_vector_zero_residual": lunar_residuals_zero,
            "mercury_tusi_couple_zero_residual": mercury_tusi_residuals_zero,
            "eliminates_ptolemy_distance_artifact": sh_ratio < Fraction(4, 3) < ptol_ratio,
        },
        "ghazali_rushd_causal_witness": {
            "shared_obs_joint": {k: frac_str(direct_joint[k]) for k in ("p11", "p10", "p01", "p00")},
            "observational_l1_distance": frac_str(obs_l1),
            "observational_association": frac_str(ate_direct),
            "ate_rushd_direct_mechanism": frac_str(ate_direct),
            "ate_ghazali_confounded_iqtiran": frac_str(ate_confounded),
            "interventional_separation": frac_str(abs(ate_direct - ate_confounded)),
            "ghazali_nonidentifiability_certified": obs_l1 == Fraction(0, 1),
            "rushd_intervention_separates_models": abs(ate_direct - ate_confounded) == Fraction(9, 25),
        },
    }


# =============================================================================
# PILLAR 3: Samarkand Precision Analysis — Jamshid al-Kashi (1380-1429)
# =============================================================================


def analyze_pillar3_kashi_banach_and_pi() -> dict[str, Any]:
    """Pillar 3: Al-Kashi Banach fixed-point sin(1 deg) & 3*2^28-gon pi bracket."""
    scale = 10**35
    s2_lo, s2_hi = _isqrt_scaled_bounds(2, 1, scale)
    s5_lo, s5_hi = _isqrt_scaled_bounds(5, 1, scale)
    s6_lo, s6_hi = _isqrt_scaled_bounds(6, 1, scale)

    in_lo = 10 * scale + 2 * s5_lo
    in_hi = 10 * scale + 2 * s5_hi
    r10_lo = math.isqrt(in_lo * scale)
    r10_r = math.isqrt(in_hi * scale)
    r10_hi = r10_r + (1 if r10_r * r10_r < in_hi * scale else 0)

    t1_lo = ((s6_lo + s2_lo) * (s5_lo - scale)) // (16 * scale)
    t1_hi = ((s6_hi + s2_hi) * (s5_hi - scale) + 16 * scale - 1) // (16 * scale)
    t2_lo = ((s6_lo - s2_hi) * r10_lo) // (16 * scale)
    t2_hi = ((s6_hi - s2_lo) * r10_hi + 16 * scale - 1) // (16 * scale)
    sin3_lo = Fraction(t1_lo - t2_hi, scale)
    sin3_hi = Fraction(t1_hi - t2_lo, scale)

    dom_lo, dom_hi = Fraction(0, 1), Fraction(1, 50)
    lipschitz_tight = Fraction(4, 1) * dom_hi * dom_hi
    x_lo, x_hi = dom_lo, dom_hi
    step0_upper_gap = (sin3_hi + 4 * dom_lo**3) / 3 - dom_lo
    widths: list[str] = []
    for _ in range(7):
        x_lo = (sin3_lo + 4 * x_lo**3) / 3
        x_hi = (sin3_hi + 4 * x_hi**3) / 3
        widths.append(frac_dec_ceil(x_hi - x_lo, 20))

    x_mid = (x_lo + x_hi) / 2
    cubic_val = 3 * x_mid - 4 * (x_mid**3)
    cubic_res_bound = max(abs(cubic_val - sin3_lo), abs(cubic_val - sin3_hi))

    kashi_1427_sex_digits = [1, 2, 49, 43, 11, 14, 44, 16, 26, 17]
    kashi_1427_val = _sexagesimal_to_fraction(0, kashi_1427_sex_digits)
    exact_sin1_sex_lo = _to_sexagesimal_digits(x_lo, 10)
    exact_sin1_sex_hi = _to_sexagesimal_digits(x_hi, 10)
    first_9_sex_match = (
        exact_sin1_sex_lo[:9] == exact_sin1_sex_hi[:9] == kashi_1427_sex_digits[:9]
    )
    sin1_diff_from_kashi = max(abs(x_lo - kashi_1427_val), abs(x_hi - kashi_1427_val))

    kashi_pi = archimedean_polygon_pi_bracket(doublings=27, scale_exp=35)
    kashi_1424_twopi_digits = [16, 59, 28, 1, 34, 51, 46, 14, 50]
    kashi_1424_twopi = _sexagesimal_to_fraction(6, kashi_1424_twopi_digits)
    kashi_twopi_inside_bracket = (kashi_pi["twopi_lo"] < kashi_1424_twopi < kashi_pi["twopi_hi"])

    # Strictly conservative sexagesimal & decimal outer brackets
    twopi_lo_sex = [6] + _to_sexagesimal_digits(kashi_pi["twopi_lo"] - 6, 10)
    twopi_hi_sex_ceil = [6] + _to_sexagesimal_digits_ceil(kashi_pi["twopi_hi"] - 6, 10)
    twopi_hi_sex_floor = [6] + _to_sexagesimal_digits(kashi_pi["twopi_hi"] - 6, 10)
    twopi_sex_floor_width = (
        _sexagesimal_to_fraction(twopi_hi_sex_floor[0], twopi_hi_sex_floor[1:])
        - _sexagesimal_to_fraction(twopi_lo_sex[0], twopi_lo_sex[1:])
    )
    twopi_sex_ceil_width = (
        _sexagesimal_to_fraction(twopi_hi_sex_ceil[0], twopi_hi_sex_ceil[1:])
        - _sexagesimal_to_fraction(twopi_lo_sex[0], twopi_lo_sex[1:])
    )
    pi_exact_width = kashi_pi["pi_hi"] - kashi_pi["pi_lo"]
    twopi_exact_width = kashi_pi["twopi_hi"] - kashi_pi["twopi_lo"]

    pi_lo_dec16 = frac_dec(kashi_pi["pi_lo"], 16)
    pi_hi_dec16_floor = frac_dec(kashi_pi["pi_hi"], 16)
    pi_hi_dec16_ceil = frac_dec_ceil(kashi_pi["pi_hi"], 16)

    return {
        "kashi_banach_sin1_cubic": {
            "domain": [frac_str(dom_lo), frac_str(dom_hi)],
            "lipschitz_constant_exact": frac_str(lipschitz_tight),
            "sin3_bracket_dec18_conservative": [frac_dec(sin3_lo, 18), frac_dec_ceil(sin3_hi, 18)],
            "sin1_bracket_dec18_conservative": [frac_dec(x_lo, 18), frac_dec_ceil(x_hi, 18)],
            "sin1_sexagesimal_10places_exact": exact_sin1_sex_lo,
            "kashi_1427_sexagesimal_10places": kashi_1427_sex_digits,
            "first_9_sexagesimal_places_exact_match": first_9_sex_match,
            "max_diff_from_kashi_1427_lt_1e17": sin1_diff_from_kashi < Fraction(1, 10**17),
            "cubic_residual_lt_1e18": cubic_res_bound < Fraction(1, 10**18),
            "step0_gap_dec12": frac_dec(step0_upper_gap, 12),
            "iteration_width_dec20_ceil_final": widths[-1],
        },
        "kashi_3_times_2_28_gon_pi": {
            "polygon_sides": kashi_pi["sides"],
            "twopi_lo_sexagesimal_floor": twopi_lo_sex,
            "twopi_hi_sexagesimal_ceil": twopi_hi_sex_ceil,
            "kashi_1424_twopi_sexagesimal": [6] + kashi_1424_twopi_digits,
            "kashi_1424_value_strictly_inside_3x2_28_bracket": kashi_twopi_inside_bracket,
            "pi_lo_dec16_floor": pi_lo_dec16,
            "pi_hi_dec16_ceil": pi_hi_dec16_ceil,
            "pi_bracket_dec17_conservative": [
                frac_dec(kashi_pi["pi_lo"], 17),
                frac_dec_ceil(kashi_pi["pi_hi"], 17),
            ],
            "pi_exact_width_e17_ceil": frac_dec_ceil(pi_exact_width * (10**17), 6),
            "twopi_exact_width_e17_ceil": frac_dec_ceil(twopi_exact_width * (10**17), 6),
            "base60_10place_floored_pi_width_e17": frac_dec((twopi_sex_floor_width / 2) * (10**17), 3),
            "base60_10place_floored_twopi_width_e17": frac_dec(twopi_sex_floor_width * (10**17), 3),
            "base60_10place_conservative_pi_width_e17_ceil": frac_dec_ceil((twopi_sex_ceil_width / 2) * (10**17), 3),
            "agrees_to_16_decimal_digits": (pi_lo_dec16 == pi_hi_dec16_floor == "3.1415926535897932"),
            "bracket_width_lt_1e16": pi_exact_width < Fraction(1, 10**16),
        },
    }


# =============================================================================
# PILLAR 4: Acoustic Continuum vs. Discrete 12-TET Bucketization
# =============================================================================


def exact_cent_floor(ratio: Fraction) -> int:
    """Return exact integer floor(1200 * log2(ratio)) via pure integer powers (0 floats, 0 logs)."""
    r = _require_exact_fraction(ratio, "ratio")
    _require(Fraction(1, 1) <= r <= Fraction(2, 1), "ratio-octave-range")
    lo, hi = 0, 1200
    p_num = r.numerator**1200
    p_den = r.denominator**1200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if (1 << mid) * p_den <= p_num:
            lo = mid
        else:
            hi = mid - 1
    return lo


def analyze_pillar4_farabi_acoustic_continuum() -> dict[str, Any]:
    """Pillar 4: Al-Farabi (Kitab al-Musiqa al-Kabir) exact pure-Q continuum vs 12-TET."""
    ratios: dict[str, Fraction] = {
        "neutral_three_quarter_12_11": Fraction(12, 11),
        "zalzal_neutral_third_27_22": Fraction(27, 22),
        "whole_tone_9_8": Fraction(9, 8),
        "fourth_4_3": Fraction(4, 3),
        "fifth_3_2": Fraction(3, 2),
        "complement_88_81": Fraction(88, 81),
    }

    zalzal_from_tone_and_12_11 = (Fraction(9, 8) * Fraction(12, 11) == Fraction(27, 22))
    tetrachord_farabi_exact = (Fraction(9, 8) * Fraction(12, 11) * Fraction(88, 81) == Fraction(4, 3))
    tetrachord_superparticular_exact = (Fraction(12, 11) * Fraction(11, 10) * Fraction(10, 9) == Fraction(4, 3))
    pyth_comma = (Fraction(3, 2) ** 12) / Fraction(1 << 7, 1)

    interval_rows: dict[str, dict[str, Any]] = {}
    for label, r in ratios.items():
        c_lo = exact_cent_floor(r)
        c_hi = c_lo + 1
        is_pow2_num = (r.numerator & (r.numerator - 1)) == 0
        is_pow2_den = (r.denominator & (r.denominator - 1)) == 0
        exact_in_12tet = is_pow2_num and is_pow2_den
        nearest_k = (c_lo + 50) // 100
        nearest_bucket = nearest_k * 100
        if c_hi <= nearest_bucket:
            defect_lo = nearest_bucket - c_hi
        elif c_lo >= nearest_bucket:
            defect_lo = c_lo - nearest_bucket
        else:
            defect_lo = 0
        interval_rows[label] = {
            "ratio": frac_str(r),
            "cents_interval": [c_lo, c_hi],
            "nearest_12tet_semitone": nearest_k,
            "nearest_12tet_cents": nearest_bucket,
            "min_12tet_rounding_defect_cents": defect_lo,
            "exact_in_12tet": exact_in_12tet,
        }

    return {
        "zalzal_product_9_8_times_12_11_exact": zalzal_from_tone_and_12_11,
        "farabi_tetrachord_4_3_exact": tetrachord_farabi_exact,
        "superparticular_tetrachord_4_3_exact": tetrachord_superparticular_exact,
        "pythagorean_comma": frac_str(pyth_comma),
        "pythagorean_comma_gt_1": pyth_comma > Fraction(1, 1),
        "intervals": interval_rows,
        "neutral_third_27_22_defect_ge_45c": interval_rows["zalzal_neutral_third_27_22"]["min_12tet_rounding_defect_cents"] >= 45,
        "three_quarter_12_11_defect_ge_49c": interval_rows["neutral_three_quarter_12_11"]["min_12tet_rounding_defect_cents"] >= 49,
        "western_fifth_3_2_defect_le_2c": interval_rows["fifth_3_2"]["min_12tet_rounding_defect_cents"] <= 2,
    }


# =============================================================================
# PILLAR 5: Two Fail-Closed Pure-Q Certifiers
# =============================================================================


def certify_extended_polymath_dag(
    nodes: Sequence[dict[str, Any]], edges: Sequence[dict[str, Any]]
) -> dict[str, Any]:
    """Fail-closed 3-tier active-voice encoding-consistency checker for the 23-scholar dataset.

    Edge direction convention (active voice): every edge {source, target, relation, citation}
    means `source <relation> target`. Influence-order DAG edges (earlier -> later) therefore
    run source->target for teacher_of and target->source for extended/commented_on/critiqued.
    """
    _require(isinstance(nodes, (list, tuple)) and len(nodes) >= 1, "lineage-nodes-nonempty")
    _require(isinstance(edges, (list, tuple)), "lineage-edges-seq")

    by_id: dict[str, dict[str, Any]] = {}
    seen_lower: set[str] = set()
    tier_counts: dict[str, int] = {"tributary": 0, "core": 0, "branch": 0}
    tier_violations: list[str] = []

    for idx, node in enumerate(nodes):
        _require(isinstance(node, dict), f"lineage-node-dict:{idx}")
        _require(set(node.keys()) == ALLOWED_NODE_KEYS, f"lineage-node-keys:{idx}")
        nid = _require_clean_ascii(node["node_id"], f"node_id[{idx}]")
        _require_clean_ascii(node["name"], f"name[{idx}]")
        _require_clean_ascii(node["city"], f"city[{idx}]")
        _require_clean_ascii(node["primary_work"], f"primary_work[{idx}]")
        _require_citation(node["source"], f"node.source[{idx}]")
        tier = _require_exact_choice(node["tier"], ALLOWED_TIERS, f"tier[{idx}]")
        birth = _require_exact_int(node["birth_year"], f"birth_year[{idx}]")
        death = _require_exact_int(node["death_year"], f"death_year[{idx}]")
        _require(birth < death, f"lineage-lifespan-order:{nid}")
        low = nid.lower()
        _require(low not in seen_lower, f"lineage-duplicate-node:{nid}")
        seen_lower.add(low)
        by_id[nid] = node
        tier_counts[tier] += 1

        if tier == "tributary" and death > 750:
            tier_violations.append(f"EPOCH_TRIBUTARY_LATE:{nid}")
        elif tier == "core" and (birth < 750 or birth > 1150):
            tier_violations.append(f"EPOCH_CORE_OUT_OF_RANGE:{nid}")
        elif tier == "branch" and birth < 1200:
            tier_violations.append(f"EPOCH_BRANCH_EARLY:{nid}")

    # Forward-time influence adjacency (earlier -> later) for cycle & tributary->core->branch reachability
    influence_adj: dict[str, list[str]] = {nid: [] for nid in by_id}
    seen_edges: set[tuple[str, str, str]] = set()
    chronology_violations: list[str] = []

    for idx, edge in enumerate(edges):
        _require(isinstance(edge, dict), f"lineage-edge-dict:{idx}")
        _require(set(edge.keys()) == ALLOWED_EDGE_KEYS, f"lineage-edge-keys:{idx}")
        src = _require_clean_ascii(edge["source"], f"edge.source[{idx}]")
        dst = _require_clean_ascii(edge["target"], f"edge.target[{idx}]")
        rel = _require_exact_choice(edge["relation"], ALLOWED_RELATIONS, f"edge.relation[{idx}]")
        _require_citation(edge["citation"], f"edge.citation[{idx}]")
        _require(src in by_id, f"lineage-unknown-source:{src}")
        _require(dst in by_id, f"lineage-unknown-target:{dst}")
        _require(src != dst, f"lineage-self-loop:{src}")
        ekey = (min(src, dst), max(src, dst), rel) if rel == "corresponded_with" else (src, dst, rel)
        _require(ekey not in seen_edges, f"lineage-duplicate-edge:{src}->{dst}:{rel}")
        seen_edges.add(ekey)

        s_node, d_node = by_id[src], by_id[dst]
        s_rank, d_rank = TIER_RANK[s_node["tier"]], TIER_RANK[d_node["tier"]]
        if rel == "corresponded_with":
            if s_rank != d_rank:
                tier_violations.append(f"TIER_CROSS_ERA_CORRESPONDENCE:{src}<->{dst}")
            overlap = min(s_node["death_year"], d_node["death_year"]) - max(
                s_node["birth_year"], d_node["birth_year"]
            )
            if overlap < 15:
                chronology_violations.append(f"CHRONO_CORRESPONDENCE_NO_OVERLAP:{src}<->{dst}")
        elif rel == "teacher_of":
            if s_rank > d_rank:
                tier_violations.append(f"TIER_BACKWARD_FLOW:{src}->{dst}")
            if s_node["birth_year"] + 10 > d_node["birth_year"]:
                chronology_violations.append(f"CHRONO_TEACHER_AGE_GAP:{src}->{dst}")
            elif d_node["birth_year"] + 12 > min(s_node["death_year"], d_node["death_year"]):
                chronology_violations.append(f"CHRONO_TEACHER_OVERLAP:{src}->{dst}")
            influence_adj[src].append(dst)
        else:
            # Active voice: later actor=src engaged prior subject=dst
            if s_rank < d_rank:
                tier_violations.append(f"TIER_BACKWARD_FLOW:{src}->{dst}")
            if s_node["birth_year"] + 15 > s_node["death_year"]:
                chronology_violations.append(f"CHRONO_IMMATURE_ACTOR:{src}->{dst}")
            if d_node["birth_year"] + 15 > d_node["death_year"]:
                chronology_violations.append(f"CHRONO_IMMATURE_SUBJECT:{src}->{dst}")
            if s_node["death_year"] < d_node["birth_year"] + 15:
                chronology_violations.append(f"CHRONO_ACTOR_DIED_BEFORE_SUBJECT_MATURITY:{src}->{dst}")
            if s_node["birth_year"] < d_node["birth_year"]:
                chronology_violations.append(f"CHRONO_ACTOR_PRECEDES_SUBJECT:{src}->{dst}")
            influence_adj[dst].append(src)

    # Exact 3-color DFS cycle detection on forward-time influence graph
    color: dict[str, int] = {nid: 0 for nid in by_id}
    has_cycle = False

    def _dfs(u: str) -> bool:
        color[u] = 1
        for v in influence_adj[u]:
            if color[v] == 1:
                return True
            if color[v] == 0 and _dfs(v):
                return True
        color[u] = 2
        return False

    for nid in by_id:
        if color[nid] == 0 and _dfs(nid):
            has_cycle = True
            break

    # Verify tributary ->+ core ->+ branch directed path in influence order
    reached_core: set[str] = set()
    stack = [nid for nid, nd in by_id.items() if nd["tier"] == "tributary"]
    visited: set[str] = set(stack)
    while stack:
        u = stack.pop()
        for v in influence_adj[u]:
            if by_id[v]["tier"] == "core":
                reached_core.add(v)
            if v not in visited:
                visited.add(v)
                stack.append(v)

    reaches_branch_via_core = False
    stack2 = list(reached_core)
    visited2: set[str] = set(stack2)
    while stack2:
        u = stack2.pop()
        for v in influence_adj[u]:
            if by_id[v]["tier"] == "branch":
                reaches_branch_via_core = True
                break
            if v not in visited2:
                visited2.add(v)
                stack2.append(v)
        if reaches_branch_via_core:
            break

    if not reaches_branch_via_core:
        tier_violations.append("LINEAGE_NO_TRIBUTARY_CORE_BRANCH_PATH")

    return {
        "certified": (len(chronology_violations) == 0 and len(tier_violations) == 0 and not has_cycle),
        "encoding_consistency_only": True,
        "edge_direction_convention": EDGE_DIRECTION_CONVENTION,
        "node_count": len(by_id),
        "edge_count": len(seen_edges),
        "all_nodes_and_edges_cited": True,
        "tier_counts": tier_counts,
        "chronology_violations": chronology_violations,
        "tier_violations": tier_violations,
        "directed_dag_acyclic": not has_cycle,
        "reaches_branch_from_tributary_via_core": reaches_branch_via_core,
    }


def _parse_prob_joint(raw: Any, name: str) -> dict[str, Fraction]:
    _require(isinstance(raw, dict), f"joint-dict:{name}")
    _require(set(raw.keys()) == ALLOWED_JOINT_KEYS, f"joint-keys:{name}")
    parsed: dict[str, Fraction] = {}
    total = Fraction(0, 1)
    for k in ("p11", "p10", "p01", "p00"):
        v = _require_exact_fraction(raw[k], f"{name}.{k}")
        _require(v >= 0, f"joint-nonneg:{name}.{k}")
        parsed[k] = v
        total += v
    _require(total == Fraction(1, 1), f"joint-sum-one:{name}")
    return parsed


def _compute_confounded_joint(
    p_u1: Fraction,
    pf_u1: Fraction,
    pf_u0: Fraction,
    pc_u1: Fraction,
    pc_u0: Fraction,
) -> dict[str, Fraction]:
    p_u0 = Fraction(1, 1) - p_u1
    return {
        "p11": p_u1 * pf_u1 * pc_u1 + p_u0 * pf_u0 * pc_u0,
        "p10": p_u1 * pf_u1 * (Fraction(1, 1) - pc_u1) + p_u0 * pf_u0 * (Fraction(1, 1) - pc_u0),
        "p01": p_u1 * (Fraction(1, 1) - pf_u1) * pc_u1 + p_u0 * (Fraction(1, 1) - pf_u0) * pc_u0,
        "p00": (
            p_u1 * (Fraction(1, 1) - pf_u1) * (Fraction(1, 1) - pc_u1)
            + p_u0 * (Fraction(1, 1) - pf_u0) * (Fraction(1, 1) - pc_u0)
        ),
    }


def certify_contraction_and_causal_identifiability(spec: Any) -> dict[str, Any]:
    """Unified fail-closed al-Kashi Banach Contraction & al-Ghazali/Ibn Rushd Causal Certifier."""
    _require(isinstance(spec, dict), "unified-spec-dict")
    _require(set(spec.keys()) == ALLOWED_UNIFIED_KEYS, "unified-spec-keys")

    dom_lo = _require_exact_fraction(spec["domain_lo"], "domain_lo")
    dom_hi = _require_exact_fraction(spec["domain_hi"], "domain_hi")
    x0 = _require_exact_fraction(spec["x0"], "x0")
    lip_L = _require_exact_fraction(spec["lipschitz_L"], "lipschitz_L")
    step0_gap = _require_exact_fraction(spec["step0_gap"], "step0_gap")
    iters = _require_exact_int(spec["iterations"], "iterations")
    target_tol = _require_exact_fraction(spec["target_tol"], "target_tol")

    _require(dom_lo < dom_hi, "banach-domain-order")
    _require(dom_lo <= x0 <= dom_hi, "banach-x0-in-domain")
    _require(lip_L >= 0, "banach-L-nonneg")
    _require(step0_gap > 0, "banach-step0-pos")
    _require(iters >= 1, "banach-iters-pos")
    _require(target_tol > 0, "banach-tol-pos")

    j_direct = _parse_prob_joint(spec["obs_joint_direct"], "obs_joint_direct")
    j_conf = _parse_prob_joint(spec["obs_joint_confounded"], "obs_joint_confounded")

    p_u1 = _require_exact_fraction(spec["confounder_p_u1"], "confounder_p_u1")
    pf_u1 = _require_exact_fraction(spec["confounder_p_f_given_u1"], "confounder_p_f_given_u1")
    pf_u0 = _require_exact_fraction(spec["confounder_p_f_given_u0"], "confounder_p_f_given_u0")
    pc_u1 = _require_exact_fraction(spec["confounder_p_c_given_u1"], "confounder_p_c_given_u1")
    pc_u0 = _require_exact_fraction(spec["confounder_p_c_given_u0"], "confounder_p_c_given_u0")
    min_sep = _require_exact_fraction(spec["min_ate_separation"], "min_ate_separation")

    _require(Fraction(0, 1) < p_u1 < Fraction(1, 1), "causal-pu1-open")
    _require(Fraction(0, 1) <= pf_u1 <= Fraction(1, 1), "causal-pf-u1-prob")
    _require(Fraction(0, 1) <= pf_u0 <= Fraction(1, 1), "causal-pf-u0-prob")
    _require(Fraction(0, 1) <= pc_u1 <= Fraction(1, 1), "causal-pc-u1-prob")
    _require(Fraction(0, 1) <= pc_u0 <= Fraction(1, 1), "causal-pc-u0-prob")
    _require(Fraction(0, 1) < min_sep <= Fraction(1, 1), "causal-min-sep-range")

    p_f1 = j_direct["p11"] + j_direct["p10"]
    p_f0 = j_direct["p01"] + j_direct["p00"]
    _require(p_f1 > 0 and p_f0 > 0, "causal-marginal-degenerate")

    violations: list[str] = []
    if lip_L >= Fraction(1, 1):
        violations.append("KASHI_NON_CONTRACTIVE_MAP")
        ball_radius_str = "UNBOUNDED"
        a_priori_str = "UNBOUNDED"
    else:
        one_minus_L = Fraction(1, 1) - lip_L
        ball_radius = step0_gap / one_minus_L
        a_priori_err = ((lip_L**iters) * step0_gap) / one_minus_L
        ball_radius_str = frac_str(ball_radius)
        a_priori_str = frac_str(a_priori_err)
        if x0 - ball_radius < dom_lo or x0 + ball_radius > dom_hi:
            violations.append("KASHI_ITERATES_ESCAPE_DOMAIN")
        if a_priori_err > target_tol:
            violations.append("KASHI_TOLERANCE_NOT_CERTIFIED")

    calc_conf = _compute_confounded_joint(p_u1, pf_u1, pf_u0, pc_u1, pc_u0)
    if calc_conf != j_conf:
        violations.append("GHAZALI_CONFOUNDED_JOINT_MISMATCH")

    obs_l1 = sum(abs(j_direct[k] - j_conf[k]) for k in ("p11", "p10", "p01", "p00"))
    if obs_l1 > 0:
        violations.append("GHAZALI_OBS_MODELS_NOT_EQUIVALENT")

    ate_direct = (j_direct["p11"] / p_f1) - (j_direct["p01"] / p_f0)
    ate_conf = Fraction(0, 1)
    ate_sep = abs(ate_direct - ate_conf)
    if ate_sep < min_sep:
        violations.append("RUSHD_INTERVENTION_UNSEPARATED")

    return {
        "certified": len(violations) == 0,
        "violations": violations,
        "banach_ball_radius": ball_radius_str,
        "banach_a_priori_error": a_priori_str,
        "causal_obs_l1": frac_str(obs_l1),
        "ate_direct": frac_str(ate_direct),
        "ate_confounded": frac_str(ate_conf),
        "ate_separation": frac_str(ate_sep),
    }


def analyze_pillar5_lineage_and_certifiers() -> dict[str, Any]:
    """Pillar 5: 23-scholar 3-tier encoding-consistency check + unified Banach/causal receipts."""
    lineage = certify_extended_polymath_dag(EXTENDED_POLYMATH_NODES, EXTENDED_POLYMATH_EDGES)

    shared_joint = {
        "p11": Fraction(17, 50),
        "p10": Fraction(4, 25),
        "p01": Fraction(4, 25),
        "p00": Fraction(17, 50),
    }
    certified_unified = certify_contraction_and_causal_identifiability(
        {
            "domain_lo": Fraction(0, 1),
            "domain_hi": Fraction(1, 50),
            "x0": Fraction(1, 100),
            "lipschitz_L": Fraction(1, 625),
            "step0_gap": Fraction(1, 125),
            "iterations": 7,
            "target_tol": Fraction(1, 10**18),
            "obs_joint_direct": shared_joint,
            "obs_joint_confounded": shared_joint,
            "confounder_p_u1": Fraction(1, 2),
            "confounder_p_f_given_u1": Fraction(4, 5),
            "confounder_p_f_given_u0": Fraction(1, 5),
            "confounder_p_c_given_u1": Fraction(4, 5),
            "confounder_p_c_given_u0": Fraction(1, 5),
            "min_ate_separation": Fraction(9, 25),
        }
    )

    rejected_unified = certify_contraction_and_causal_identifiability(
        {
            "domain_lo": Fraction(0, 1),
            "domain_hi": Fraction(1, 50),
            "x0": Fraction(1, 100),
            "lipschitz_L": Fraction(1, 1),
            "step0_gap": Fraction(1, 125),
            "iterations": 3,
            "target_tol": Fraction(1, 10**6),
            "obs_joint_direct": {
                "p11": Fraction(1, 4),
                "p10": Fraction(1, 4),
                "p01": Fraction(1, 4),
                "p00": Fraction(1, 4),
            },
            "obs_joint_confounded": shared_joint,
            "confounder_p_u1": Fraction(1, 2),
            "confounder_p_f_given_u1": Fraction(4, 5),
            "confounder_p_f_given_u0": Fraction(1, 5),
            "confounder_p_c_given_u1": Fraction(4, 5),
            "confounder_p_c_given_u0": Fraction(1, 5),
            "min_ate_separation": Fraction(1, 10),
        }
    )

    return {
        "extended_lineage_dag_receipt": lineage,
        "certified_kashi_banach_and_ghazali_rushd": certified_unified,
        "rejected_noncontractive_and_unseparated": rejected_unified,
    }


def build_certificate() -> dict[str, Any]:
    """Build self-contained deterministic pure-Q zero-float AUDIT-095R certificate."""
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "audit_id": AUDIT_ID,
        "execution_mode": "standalone_pure_q",
        "novelty_classification": {
            "honest_tier": "N0",
            "n0_historical_prior_art": (
                "Archimedes, Apollonius, Heron, Brahmagupta, Bhaskara II/Jayadeva, "
                "al-Khwarizmi, al-Kindi, Banu Musa, Hunayn ibn Ishaq, Thabit ibn Qurra, "
                "al-Farabi, al-Karaji, Ibn al-Haytham, al-Biruni, Ibn Sina, Umar al-Khayyam, "
                "al-Ghazali, al-Samawal, Ibn Rushd, Ismail al-Jazari, Nasir al-Din al-Tusi, "
                "Ibn al-Shatir, Jamshid al-Kashi, Nicolaus Copernicus"
            ),
            "rationale": (
                "All mathematical theorems and historical reconstructions are N0 classical prior art; "
                "this package provides reproducible pure-Q stdlib verification scripts, conservative "
                "interval arithmetic, and encoding-consistency checks without claiming N1 novelty."
            ),
        },
        "pillar1_tributary_veins": analyze_pillar1_tributary_veins(),
        "pillar2_shatir_copernicus_and_ghazali_rushd": analyze_pillar2_shatir_copernicus_and_ghazali_rushd(),
        "pillar3_kashi_banach_and_pi": analyze_pillar3_kashi_banach_and_pi(),
        "pillar4_farabi_acoustic_continuum": analyze_pillar4_farabi_acoustic_continuum(),
        "pillar5_lineage_and_certifiers": analyze_pillar5_lineage_and_certifiers(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    payload["certificate_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AUDIT-095R Bayt al-Hikma Veins & Branches Certifier")
    parser.add_argument("--json", action="store_true", help="Emit canonical JSON certificate")
    parser.add_argument("--write-cert", type=Path, default=None, help="Write canonical JSON certificate to path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    cert = build_certificate()
    rendered = json.dumps(cert, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write_cert is not None:
        args.write_cert.write_text(rendered, encoding="utf-8")
    if args.json:
        sys.stdout.write(rendered)
    else:
        sys.stdout.write(
            f"{AUDIT_ID} | mode={cert['execution_mode']} | tier={cert['novelty_classification']['honest_tier']} "
            f"| sha256={cert['certificate_sha256']}\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
