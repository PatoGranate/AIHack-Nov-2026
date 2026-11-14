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
ROUNDS, SD_ROUND, SIMS = 36, 45.0, 8000
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

def rate(a, b, tau=6.0):
    """bb/100 a wins from b while seated together: model, shrunk toward direct observation.
    tau = assumed SD of a pair's deviation from the additive model (bb/100). tau -> 0 uses the
    additive model only; tau -> inf uses the observed head-to-head only. 6 is a judgement call,
    so the sensitivity grid below varies it."""
    model = s[a] - s[b]
    n = N[(a, b)]
    if not n:
        return model, None, 0
    m = F[(a, b)] / n; var = max(SQ[(a, b)] / n - m * m, 1e-9)
    obs = m / 20 * 100; se = math.sqrt(var / n) / 20 * 100
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

def expect(table, tau=6.0):
    # rate() is antisymmetric, so these expectations sum to zero over the table
    return {p: sum(rate(p, q, tau)[0] for q in table if q != p) for p in table}

rng = np.random.default_rng(7)
def zero_sum_normal(sd, size):
    """Normal draws per seat that sum to zero across the table, each with marginal SD `sd`."""
    z = rng.normal(0.0, sd, size)
    n = size[1]
    return (z - z.mean(axis=1, keepdims=True)) * math.sqrt(n / (n - 1))

def p_top2(mu, us, skill_sd=SKILL_SD, sd_round=SD_ROUND):
    """mu: expected bb/100 per seat (zero-sum). Sunday edge uncertainty and round noise both zero-sum."""
    names = list(mu); n = len(names); m = np.array([mu[p] for p in names])
    tot = m + zero_sum_normal(skill_sd, (SIMS, n)) + zero_sum_normal(sd_round / math.sqrt(ROUNDS), (SIMS, n))
    top2 = np.argsort(-tot, axis=1)[:, :2]
    return {p: float(np.mean(np.any(top2 == k, axis=1))) for k, p in enumerate(names)}

print("\nILLUSTRATIVE SCENARIOS, not a validated qualification forecast. Assumptions: every seat keeps its")
print("Saturday bot; %d rounds; per-round SD %.0f; Sunday-edge uncertainty SD %.0f; tau 6; zero-sum draws." % (ROUNDS, SD_ROUND, SKILL_SD))
for who in ["WBot"] + STAND_INS:
    table = [who if p == "WBot" else p for p in TABLE]
    mu = expect(table); pr = p_top2(mu, who)
    print("\nwith %-10s in our seat: expected bb/100 and P(top 2)" % who)
    for p in sorted(table, key=mu.get, reverse=True):
        print("   %-22s %+6.1f  %5.1f%%%s" % (p[:22], mu[p], 100 * pr[p], "   <- us" if p == who else ""))

def with_edge(mu, us, X):
    """Our seat's expected result set to X; the difference comes evenly out of the other seats (stays zero-sum)."""
    out = dict(mu); d = X - mu[us]; out[us] = X
    for p in out:
        if p != us: out[p] -= d / (len(mu) - 1)
    return out

print("\nScenario: P(top 2) if our seat's expected bb/100 were X (others rebalanced to stay zero-sum):")
mu0 = expect(TABLE)
for X in [0, 10, 20, 30, 40]:
    print("   X = %+3d  ->  %5.1f%%" % (X, 100 * p_top2(with_edge(mu0, "WBot", X), "WBot")["WBot"]))

print("\nSensitivity: WBot's P(top 2), and the X that gives 50%, across assumptions")
print("   %-14s %-9s %-9s %10s %10s" % ("tau", "skill_sd", "sd_round", "P(WBot)", "X for 50%"))
for tau in (1e-3, 6.0, 1e6):
    mu_t = expect(TABLE, tau)
    for ssd in (5.0, 10.0, 15.0):
        for sdr in (45.0, 65.0):
            p = p_top2(mu_t, "WBot", ssd, sdr)["WBot"]
            xs = [x for x in range(-10, 61, 2) if p_top2(with_edge(mu_t, "WBot", x), "WBot", ssd, sdr)["WBot"] >= 0.5]
            lab = {1e-3: "model only", 6.0: "6", 1e6: "observed only"}[tau]
            print("   %-14s %-9.0f %-9.0f %9.1f%% %10s" % (lab, ssd, sdr, 100 * p, ("%+d" % xs[0]) if xs else ">60"))
