import os, re
import sys
RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
base = RR
files = []
for root, _d, fs in os.walk(base):
    _d[:] = sorted(d for d in _d if d not in {".git", "verification", "corpora"})  # prune in place, fixed walk order
    for f in sorted(fs):
        if f.endswith((".md", ".py", ".json", ".txt")):
            files.append(os.path.join(root, f))
if len(sys.argv) > 1:
    files.append(os.path.abspath(sys.argv[1]))  # optional: a saved copy of the pull request body
pats = [("unseen/held-out", r"(?i)unseen|held-out|held out"), ("absolute ladder", r"raw\s*<\s*rasm|monotonic|raw_diacritics"), ("N1", r"\bN1\b"),
        ("334/334 or 100.0%", r"334/334|100\.0%"), ("VERIFIED", r"VERIFIED"), ("14-step", r"14`?-step|14-step"), ("2.42e-17", r"2\.42e-17"),
        ("anachronistic influences", r"0 anachron|zero anachron"), ("12/12 unanimous", r"12\s*/\s*12|unanimous"), ("thresholds 9/20 3/10", r"9/20|Fraction\(9, 20\)|3/10"),
        ("zero numerology claim", r"(?i)zero numerology"), ("bridges verified", r"(?i)cross-repository.*verified|3/3 vault|vault cross-link"),
        ("acyclic/forward flow", r"(?i)acyclic|forward tier flow"), ("novel", r"(?i)\bnovel\b|first")]
for name, rx in pats:
    r = re.compile(rx)
    hits = []
    for f in sorted(files):
        try:
            with open(f, encoding="utf8") as fh:
                for i, l in enumerate(fh, 1):
                    if r.search(l):
                        hits.append("%s:%d" % (os.path.relpath(f, RR) if f.startswith(RR) else os.path.basename(f), i))
        except Exception:
            pass
    print("%-26s %3d hits" % (name, len(hits)))
    byf = {}
    for h in hits:
        byf.setdefault(h.rsplit(":", 1)[0], []).append(h.rsplit(":", 1)[1])
    for f, ls in sorted(byf.items()):
        print("      %s : %s" % (f, ",".join(ls[:14]) + ("..." if len(ls) > 14 else "")))
