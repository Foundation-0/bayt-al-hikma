"""Head-2 lineage certifier probes (own code). Loads the PR certifiers as third-party code; run inside the sandbox only."""
import importlib.util
import sys
import os
import copy

RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root


def load(name, rel):
    path = RR + "/" + rel
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


pl = load("pl", "polymath-lineage/bayt_al_hikma_polymath_certifier.py")
ve = load("ve", "veins-and-branches/bayt_al_hikma_veins_certifier.py")
CIT = {"work": "W", "edition": "E", "location": "L"}
NONSENSE = {"work": "no such book", "edition": "no such edition", "location": "page 0"}


def run(tag, fn, nodes, edges):
    try:
        r = fn(nodes, tuple(edges))
        print("  %-62s certified=%s chrono=%s tier=%s" % (tag, r["certified"], r["chronology_violations"], r.get("tier_violations", "-")))
        return r["certified"]
    except Exception as e:  # fail-closed errors are the point of the probe
        print("  %-62s REJECTED_BY_EXCEPTION %s: %s" % (tag, type(e).__name__, str(e)[:90]))
        return None


def suite(tag, mod, nodes, edges, fn, probes):
    print("== %s (%d nodes, %d edges)" % (tag, len(nodes), len(edges)))
    base = run("baseline committed dataset", fn, nodes, edges)
    by = {n["node_id"]: n for n in nodes}
    for label, extra, mutate in probes:
        e2 = copy.deepcopy(list(edges))
        if mutate:
            e2 = mutate(e2)
        if extra:
            e2.append(extra)
        run(label, fn, nodes, e2)


def reverse_first(rel, src, dst):
    def m(es):
        for e in es:
            if e["source"] == src and e["target"] == dst and e["relation"] == rel:
                e["source"], e["target"] = dst, src
                return es
        raise SystemExit("edge not found for reversal %s %s %s" % (rel, src, dst))
    return m


def swap_citation(src, dst, rel):
    def m(es):
        for e in es:
            if e["source"] == src and e["target"] == dst and e["relation"] == rel:
                e["citation"] = dict(NONSENSE)
                return es
        raise SystemExit("edge not found")
    return m


def dropkey(src, dst, rel):
    def m(es):
        for e in es:
            if e["source"] == src and e["target"] == dst and e["relation"] == rel:
                del e["citation"]
                return es
        raise SystemExit("edge not found")
    return m


common = [
    ("THEIR-STYLE PROBE: khwarizmi critiqued tusi (actor born 780, subject born 1201)", dict(source="khwarizmi", target="tusi", relation="critiqued", citation=CIT), None),
    ("MINE V1: tusi teacher_of kindi (student 400 years earlier)", dict(source="tusi", target="kindi", relation="teacher_of", citation=CIT), None),
    ("MINE V2: khwarizmi corresponded_with tusi (no overlap in lifetimes)", dict(source="khwarizmi", target="tusi", relation="corresponded_with", citation=CIT), None),
    ("MINE V3: tusi extended khwarizmi (correct direction, later->earlier)", dict(source="tusi", target="khwarizmi", relation="extended", citation=CIT), None),
    ("MINE V4: same legal edge with nonsense citation text", dict(source="tusi", target="khwarizmi", relation="extended", citation=NONSENSE), None),
    ("MINE V5: edge without citation key", dict(source="tusi", target="khwarizmi", relation="extended"), None),
    ("MINE V6: self loop kindi extended kindi", dict(source="kindi", target="kindi", relation="extended", citation=CIT), None),
]
pol_extra = [
    ("MINE V7: reverse existing extended edge karaji->khwarizmi", None, reverse_first("extended", "karaji", "khwarizmi")),
    ("MINE V8: existing edge's citation replaced by nonsense", None, swap_citation("karaji", "khwarizmi", "extended")),
    ("MINE V9: existing edge's citation key removed", None, dropkey("karaji", "khwarizmi", "extended")),
]
vei_extra = [
    ("MINE V7: reverse existing extended edge karaji->khwarizmi", None, reverse_first("extended", "karaji", "khwarizmi")),
    ("MINE V8: existing edge's citation replaced by nonsense", None, swap_citation("karaji", "khwarizmi", "extended")),
    ("MINE V10: tributary archimedes extended copernicus (earlier actor, backward tier)", dict(source="archimedes", target="copernicus", relation="extended", citation=CIT), None),
]
suite("polymath certifier", pl, pl.BAYT_AL_HIKMA_NODES, pl.BAYT_AL_HIKMA_EDGES, pl.certify_polymath_lineage_graph, common + pol_extra)
suite("veins certifier", ve, ve.EXTENDED_POLYMATH_NODES, ve.EXTENDED_POLYMATH_EDGES, ve.certify_extended_polymath_dag, common + vei_extra)
# direction facts at head 2
for tag, nodes, edges in (("polymath", pl.BAYT_AL_HIKMA_NODES, pl.BAYT_AL_HIKMA_EDGES), ("veins", ve.EXTENDED_POLYMATH_NODES, ve.EXTENDED_POLYMATH_EDGES)):
    by = {n["node_id"]: n for n in nodes}
    eng = [e for e in edges if e["relation"] in ("extended", "commented_on", "critiqued")]
    bad = [(e["source"], e["target"]) for e in eng if by[e["source"]]["birth_year"] < by[e["target"]]["birth_year"] or by[e["source"]]["death_year"] < by[e["target"]]["birth_year"] + 15]
    print("%s: engagement edges=%d, with actor born before subject or dead before subject's maturity: %d" % (tag, len(eng), len(bad)))
    tch = [e for e in edges if e["relation"] == "teacher_of"]
    print("%s: teacher_of edges=%d, with teacher not at least 10 years older: %d" % (tag, len(tch), sum(1 for e in tch if by[e["source"]]["birth_year"] + 10 > by[e["target"]]["birth_year"])))
print("citation keys required: %s ; node citation check content: only key set and ASCII-clean strings" % sorted(pl.ALLOWED_CITATION_KEYS))
