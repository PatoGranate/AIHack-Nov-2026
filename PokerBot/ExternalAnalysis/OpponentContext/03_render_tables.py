"""Render the audit's per-opponent tables (markdown) from the JSON written by 01 and 02. Deterministic.

Writes data/audit_tables.md. Cell format: rate% [90% CI] n.
"""
import json
import os

import oc_parse as P

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
post = json.load(open(os.path.join(D, "postflop_context_summary.json"), encoding="utf-8"))
pre = json.load(open(os.path.join(D, "preflop_context_summary.json"), encoding="utf-8"))


def cell(d, k):
    v = d.get(k)
    if not v or v["rate"] is None:
        return "-"
    return "%.0f [%.0f-%.0f] %d" % (100 * v["rate"], 100 * v["lo"], 100 * v["hi"], v["n"])


def table(title, src, cols, names):
    out = ["**%s**" % title, "", "| team | " + " | ".join(c for c, _ in cols) + " |",
           "|---|" + "---|" * len(cols)]
    for nm in names:
        d = src[nm]
        out.append("| %s | " % nm + " | ".join(cell(d, k) for _, k in cols) + " |")
    return "\n".join(out) + "\n"


names = P.TABLE4 + P.STRONG
parts = [
    table("A. Post-flop fold rate, first response to the first bet: HU/multiway x size", post["opponents"], [
        ("all", "all:all"), ("HU <50%", "humw_size2:HU S"), ("HU >=50%", "humw_size2:HU L"),
        ("MW <50%", "humw_size2:MW S"), ("MW >=50%", "humw_size2:MW L"), (">110% pot", "size4:>110%")], names),
    table("B. Post-flop fold rate by street, position vs the bettor, callers, and facing a raise", post["opponents"], [
        ("flop", "street:flop"), ("turn", "street:turn"), ("river", "street:river"), ("IP", "ip:IP"),
        ("OOP", "ip:OOP"), ("MW, 1+ callers", "mw_callers:MW 1+ callers"), ("facing raise", "facing:raise")], names),
    table("C. Bettor identity and drift: vs WBot's bets, vs others' (WBot tables), early/late Saturday, bot counter",
          post["opponents"], [
              ("vs WBot", "bettor:vs WBot"), ("vs others", "bettor:vs others"), ("r01-27", "half:r01-27"),
              ("r28-54", "half:r28-54"), ("bot ftb counter", "bot_ftb_raw")], names),
    table("D. Preflop fold rate: first response to an unlimped first-in open; opener vs 3-bet", pre["opponents"], [
        ("blind vs CO/BTN/SB open", "role:blind vs late open"), ("blind vs earlier open", "role:blind vs early open"),
        ("cold (non-blind)", "role:cold (non-blind)"), ("BB vs late <=3.0bb", "bb_late_size:<=3.0bb"),
        ("BB vs late >=3.1bb", "bb_late_size:>=3.1bb"), ("1+ caller ahead", "callers:1+ caller"),
        ("opener vs 3-bet IP", "o3:opener IP"), ("opener vs 3-bet OOP", "o3:opener OOP")], names),
]
with open(os.path.join(D, "audit_tables.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("\n".join(parts))
print("\n".join(parts))
