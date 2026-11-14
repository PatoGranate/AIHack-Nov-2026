"""Preflop fold rates by context: first response to a first-in open, and the opener's response to a 3-bet.

vs_open: a non-opener's FIRST response while exactly one raise is outstanding (fold vs call/3-bet). Limped pots
(a limper before the open) are reported separately. Open size = the opener's raise-to amount in big blinds.
open_vs_3bet: the original opener's first response to a 3-bet. IP = the opener acts after the 3-bettor postflop.
Frequencies of public actions only; nothing here measures profitability.
Writes data/out_02_preflop_context.txt and data/preflop_context_summary.json.
"""
import json
import sys

import numpy as np

import oc_parse as P
import oc_stats as S

sys.stdout = S.Tee(S.out_path("out_02_preflop_context.txt"))
rng = np.random.default_rng(S.SEED + 2)

tables = P.load_tables()
_post, pre, _bot = P.extract(tables)
FOLD = lambda r: r["action"] == "fold"
HERO = P.HERO
vo = [r for r in pre if r["kind"] == "vs_open" and not r["limped"]]
o3 = [r for r in pre if r["kind"] == "open_vs_3bet"]
LATE = ("CO", "BTN", "SB")
print("Opponent context audit, preflop (exploratory, descriptive)")
print("first responses to an unlimped first-in open: %d; limped-pot responses (excluded): %d; opener vs 3-bet: %d"
      % (len(vo), sum(r["kind"] == "vs_open" and r["limped"] for r in pre), len(o3)))

FAM = {
    "role": (["blind vs late open", "blind vs early open", "cold (non-blind)"],
             lambda r: ("blind vs late open" if r["opener_pos"] in LATE else "blind vs early open")
             if r["pos"] in ("SB", "BB") else "cold (non-blind)", vo),
    "bb_size": (P.OPEN_LABELS, lambda r: r["size"] if (r["pos"] == "BB" and r["cold"] == 0) else None, vo),
    "bb_late_size": (["<=3.0bb", ">=3.1bb"],
                     lambda r: (("<=3.0bb" if r["open_bb"] < 3.05 else ">=3.1bb")
                                if (r["pos"] == "BB" and r["cold"] == 0 and r["opener_pos"] in LATE) else None), vo),
    "callers": (["no caller yet", "1+ caller"], lambda r: "no caller yet" if r["cold"] == 0 else "1+ caller", vo),
    "vs_wbot": (["open by WBot", "open by others"],
                lambda r: None if r["name"] == HERO else ("open by WBot" if r["opener"] == HERO else "open by others"), vo),
    "o3": (["opener IP", "opener OOP"], lambda r: "opener IP" if r["ip"] else "opener OOP", o3),
}
G = {f: S.counts(recs, lab, key, FOLD) for f, (lab, key, recs) in FAM.items()}
LAB = {f: FAM[f][0] for f in FAM}
summary = {"opponents": {}}

print("\n== 1. Decisions per 1,000-hand round (per opponent-table): median [10th, 90th] ==")
field = [nm for nm in G["role"] if nm != HERO]
for fam in ["role", "bb_size", "callers", "o3"]:
    for j, l in enumerate(LAB[fam]):
        v = np.concatenate([G[fam][nm][2][:, j] for nm in field if nm in G[fam]])
        v4 = np.concatenate([G[fam][nm][2][:, j] for nm in P.TABLE4 if nm in G[fam]])
        print("  %-24s field %3.0f [%3.0f,%3.0f]   T4 %3.0f [%3.0f,%3.0f]" % (
            fam + ": " + l if fam in ("bb_size",) else l, np.median(v), np.percentile(v, 10), np.percentile(v, 90),
            np.median(v4), np.percentile(v4, 10), np.percentile(v4, 90)))

print("\n== 2. Fold rate by context: rate [90% table-bootstrap CI] n ==")
for nm in P.TABLE4 + P.STRONG:
    print("\n%s" % nm)
    out = {}
    for fam in FAM:
        if nm not in G[fam]:
            continue
        ts, K, N = G[fam][nm]
        point, draws, _ = S.boot_rates(K, N, rng)
        lo, hi = S.ci(draws)
        for j, l in enumerate(LAB[fam]):
            n = int(N[:, j].sum())
            out[fam + ":" + l] = dict(rate=None if n == 0 else float(point[j]), lo=float(lo[j]), hi=float(hi[j]), n=n)
            if n:
                print("  %-34s %2.0f%% [%2.0f,%2.0f] n=%d" % (fam + ":" + l, 100 * point[j], 100 * lo[j], 100 * hi[j], n))
    summary["opponents"][nm] = out

print("\n== 3. Between-team heterogeneity (non-WBot teams, >=5 tables, >=30 decisions per bucket) ==")
print("%-34s %3s %7s %13s %6s %7s" % ("quantity", "k", "mean", "tau [logit]", "p_sim", "p_simL"))
specs = [("level: blind vs late open", "role", 0, None), ("level: blind vs early open", "role", 1, None),
         ("level: cold (non-blind)", "role", 2, None), ("level: opener vs 3-bet", "o3", 0, None),
         ("effect: blind early - late opener", "role", 1, 0),
         ("effect: BB >=3.1bb - <=3.0bb (late)", "bb_late_size", 1, 0),
         ("effect: 1+ caller - none", "callers", 1, 0), ("effect: opener OOP - IP", "o3", 1, 0),
         ("effect: WBot open - others", "vs_wbot", 0, 1)]
fg = {f: {nm: g for nm, g in G[f].items() if nm != HERO} for f in G}
het = {}
for label, fam, a, b in specs:
    h = S.heterogeneity(fg[fam], a, b, rng=rng)
    if h is None:
        print("%-34s too few teams" % label)
        continue
    het[label] = dict(k=h["k"], mean=h["mean"], tau=h["tau"], tau_logit=h["tau_logit"], p_sim=h["p_sim"],
                      p_sim_logit=h["p_sim_logit"])
    print("%-34s %3d %+6.1f%s %5.1f [%4.2f] %6.3f %7.3f" % (label, h["k"], 100 * h["mean"], " " if b is None else "p",
                                                         100 * h["tau"], h["tau_logit"], h["p_sim"], h["p_sim_logit"]))
summary["heterogeneity"] = het
print("Open size is largely fixed per bot, so the size effect is partly an opener-identity effect.")

with open(S.out_path("preflop_context_summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=1, ensure_ascii=False)
print("\nwrote data/preflop_context_summary.json")
