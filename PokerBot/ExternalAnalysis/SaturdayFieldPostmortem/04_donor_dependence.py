import glob, json, os, re, collections
import numpy as np
from common import DATA, hand_files
final = json.load(open(os.path.join(DATA, "final_standings_saturday.json")))["saturday"]["standings"]; LB = {r["name"]: r["bb100"] for r in final}
inc = json.load(open(os.path.join(DATA, "per_round_increments.json")))["inc"]
tables = {}
for f in sorted(hand_files()):
    d = json.load(open(f, encoding="utf-8"))
    if "practice" not in d["ref"]: tables.setdefault((d["ref"], tuple(d["players"])), d)
BIG = {"clanker", "ediz_slow", "AIl IN", "Joca", "YSL_TWIZZY", "Anton", "ND"}
print("result with >=1 of the 7 worst bots at the table vs none:")
for p in ["Attention Is All In", "Gherkers", "The Market Makers", "Kojack", "FisherMen", "WBot", "Red", "kaiserbot"]:
    w, wo = [], []
    for d in tables.values():
        if p not in d["players"]: continue
        s = d["players"].index(p); r = sum(h["results"][s] for h in d["hands"]) / 200
        (w if BIG & set(d["players"]) - {p} else wo).append(r)
    print("  %-20s with donors %+6.1f (n%2d)   no donors %+6.1f (n%2d)" % (p[:20], np.mean(w), len(w), np.mean(wo) if wo else float('nan'), len(wo)))
print("\nrobust re-rank over r14-48 (mean / mean excl. r41 / 10%-trimmed mean):")
rows = []
for p in LB:
    if p not in inc or len(inc[p]) < 30: continue
    v = {int(k): x for k, x in inc[p].items()}; a = np.array(sorted(v.values())); k = int(len(a) * .1)
    rows.append((p, a.mean(), np.mean([x for r, x in v.items() if r != 41]), a[k:len(a) - k].mean()))
for i, (p, m, m41, tm) in enumerate(sorted(rows, key=lambda r: -r[3])[:18]):
    print("  %2d %-22s %+6.1f  %+6.1f  %+6.1f   (final rank %d)" % (i + 1, p[:22], m, m41, tm, [r["name"] for r in final].index(p) + 1))
