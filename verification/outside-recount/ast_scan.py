import ast, os
RR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repository root
tot = 0
for root, _d, fs in os.walk(RR):
    _d[:] = sorted(d for d in _d if d not in {".git", "verification", "corpora"})  # prune in place, fixed walk order
    for f in sorted(fs):
        if f.endswith(".py"):
            p = os.path.join(root, f)
            with open(p, encoding="utf8") as fh:
                t = ast.parse(fh.read())
            a = sum(1 for n in ast.walk(t) if isinstance(n, ast.Assert))
            fl = sum(1 for n in ast.walk(t) if isinstance(n, ast.Constant) and isinstance(n.value, float))
            tot += a
            print("%-70s Assert nodes=%d float literals=%d" % (os.path.relpath(p, RR), a, fl))
print("total bare assert statements:", tot)
