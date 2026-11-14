"""WBot's Sunday table (stage 1, table 4): pairwise edges, opponent styles, P(top 2) by candidate style.

Uses data/pairwise_skill.json and data/team_profiles.json (written by 02_styles_pairwise.py) and the
hand files (for direct head-to-head flows). Expected result of team i at the table = sum over the
other seats j of the pairwise rate r_ij (bb per 100 hands played together). r_ij = the transitive
model s_i - s_j, shrunk toward the observed head-to-head when that pair met often.
"""
import collections, json, math, os, random
import numpy as np
from common import DATA, hand_files

TABLE = ["Resonance Qt", "Anker Batteries", "Chinese people can fly", "WBot", "GamesGone", "Poke", "Anton", "YSL_TWIZZY"]
# other bots we own; each is swapped into WBot's seat as a "what if this style sat here" check
STAND_INS = ["Red", "kaiserbot", "AAST"]
ROUNDS, SD_ROUND, SIMS = 36, 45.0, 20000
# each team's true Sunday edge is uncertain: Saturday estimate error (~±9) plus overnight uploads
SKILL_SD = 10.0

s = json.load(open(os.path.join(DATA, "pairwise_skill.json")))["s"]
prof = {p["team"]: p for p in json.load(open(os.path.join(DATA, "team_profiles.json")))}

# direct head-to-head flows (same attribution as 02_styles_pairwise.py)
F = collections.defaultdict(float); SQ = collections.defaultdict(float); N = collections.Counter(); seen = set()
for f in hand_files():
    d = json.load(open(f, encoding="utf-8"))
    if "practice" in d["ref"] or (d["ref"], tuple(d["players"])) in seen:
        continue
    seen.add((d["ref"], tuple(d["players"])))
    P = d["players"]; n = len(P)
    for h in d["hands"]:
        res = h["results"]; G = sum(-x for x in res if x < 0)
        for i in range(n):
            for j in range(n):
                if i == j: continue
                v = 0.0
                if G and res[i] > 0 and res[j] < 0: v = res[i] * (-res[j]) / G
                elif G and res[j] > 0 and res[i] < 0: v = -res[j] * (-res[i]) / G
                F[(P[i], P[j])] += v; SQ[(P[i], P[j])] += v * v; N[(P[i], P[j])] += 1

def rate(a, b):
    """bb/100 a wins from b while seated together: model, shrunk toward direct observation."""
    model = s[a] - s[b]
    n = N[(a, b)]
    if not n:
        return model, None, 0
    m = F[(a, b)] / n; var = max(SQ[(a, b)] / n - m * m, 1e-9)
    obs = m / 20 * 100; se = math.sqrt(var / n) / 20 * 100
    tau = 6.0  # prior SD of a pair's deviation from the transitive model (bb/100)
    w = tau ** 2 / (tau ** 2 + se ** 2)
    return model + w * (obs - model), (obs, se), n

print("Opponent styles at table 4 (observed Saturday, all tables we saw):")
print("%-22s %6s | %4s %4s %4s %4s %4s %4s %4s %4s | %s" % ("team", "LB", "VPIP", "PFR", "3b", "limp", "FvB", "AF", "WTSD", "W$SD", "note"))
notes = {"YSL_TWIZZY": "goes to showdown 45%, folds to bets 26%: calling station",
         "Anton": "3-bets 25%, pre-flop jam 1.9%; improved -33 -> +17 in 2nd half",
         "Poke": "limps 10% of hands; folds to bets 55%",
         "Chinese people can fly": "loose (VPIP 36) but profitable",
         "GamesGone": "loses at showdown (-19), wins without",
         "Resonance Qt": "solid, 3-bets 12%", "Anker Batteries": "solid, 3-bets 13%",
         "WBot": "tiny bets (median 18% pot), AF 87%"}
for p in TABLE:
    r = prof[p]
    print("%-22s %+6.1f | %4.0f %4.0f %4.0f %4.0f %4.0f %4.0f %4.0f %4.0f | %s" % (
        p[:22], r["lb"], r["vpip"], r["pfr"], r["three"], r["limp"], r["fvb"], r["af"], r["wtsd"], r["wsd"], notes.get(p, "")))

print("\nHead-to-head vs WBot (net bb per 100 hands together; + = WBot wins):")
for q in TABLE:
    if q == "WBot": continue
    est, ob, n = rate("WBot", q)
    print("   vs %-22s model+obs %+6.1f   observed %s" % (q[:22], est, "%+6.1f ±%4.1f (%d hands)" % (ob[0], ob[1], n) if ob else "none"))

def expect(table):
    return {p: sum(rate(p, q)[0] for q in table if q != p) for p in table}

random.seed(7)
def p_top2(table):
    mu = expect(table); wins = collections.Counter()
    se = SD_ROUND / math.sqrt(ROUNDS)
    for _ in range(SIMS):
        tot = {p: random.gauss(mu[p], math.hypot(se, SKILL_SD)) for p in table}
        for p in sorted(tot, key=tot.get, reverse=True)[:2]:
            wins[p] += 1
    return mu, wins

for who in ["WBot"] + STAND_INS:
    table = [who if p == "WBot" else p for p in TABLE]
    mu, wins = p_top2(table)
    print("\nwith %-10s in our seat: expected bb/100 and P(top 2 over %d rounds, skill uncertainty SD %.0f)" % (who, ROUNDS, SKILL_SD))
    for p in sorted(table, key=mu.get, reverse=True):
        print("   %-22s %+6.1f  %5.1f%%%s" % (p[:22], mu[p], 100 * wins[p] / SIMS, "   <- us" if p == who else ""))

print("\nWhat edge would we need? P(top 2) if our seat's expected bb/100 were X (others as in the WBot table):")
mu0 = expect(TABLE)
for X in [0, 10, 20, 30, 40]:
    mu = dict(mu0); mu["WBot"] = X; wins = 0; se = SD_ROUND / math.sqrt(ROUNDS)
    for _ in range(SIMS):
        tot = {p: random.gauss(mu[p], math.hypot(se, SKILL_SD)) for p in TABLE}
        wins += "WBot" in sorted(tot, key=tot.get, reverse=True)[:2]
    print("   X = %+3d  ->  %5.1f%%" % (X, 100 * wins / SIMS))
