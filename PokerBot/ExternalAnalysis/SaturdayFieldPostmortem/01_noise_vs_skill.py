"""Saturday post-mortem: dataset, noise vs skill, styles, pairwise flows, transitivity."""
import csv, glob, json, math, os, re, sys, random, collections
import numpy as np
from common import DATA, hand_files

import hand_stats as A

OURS = {"Red", "WBot", "kaiserbot"}
final = json.load(open(os.path.join(DATA, "final_standings_saturday.json")))["saturday"]["standings"]
LB = {r["name"]: r for r in final}

# ---------- load unique counted tables ----------
tables = {}
for f in sorted(hand_files()):
    d = json.load(open(f, encoding="utf-8"))
    if "practice" in d["ref"]:
        continue
    key = (d["ref"], tuple(d["players"]))
    if key in tables:
        continue
    d["_acct"] = os.path.basename(os.path.dirname(f))
    tables[key] = d
T = list(tables.values())
rn = lambda d: int(re.search(r"r(\d+)$", d["ref"]).group(1))
print("unique counted tables:", len(T), "rounds:", min(map(rn, T)), "-", max(map(rn, T)))
dup = collections.Counter(d["ref"] for d in T)
print("slots with 1/2/3 of our tables:", collections.Counter(dup.values()))
nplay = collections.Counter(len(d["players"]) for d in T)
print("table sizes:", nplay)

# name normalisation check vs leaderboard
seen_names = collections.Counter(p for d in T for p in d["players"])
print("names at our tables not on leaderboard:", [n for n in seen_names if n not in LB])
print("leaderboard teams never seen:", [n for n in LB if n not in seen_names])

# ---------- zero-sum / integrity ----------
bad = 0; nh = 0
for d in T:
    for h in d["hands"]:
        nh += 1
        if sum(h["results"]) != 0:
            bad += 1
print("hands:", nh, "non-zero-sum hands:", bad)
# our recorded round chips vs results sum
mism = 0
for d in T:
    me = d["seat"]; s = sum(h["results"][me] for h in d["hands"])
    if s != d["round"]["chips"]:
        mism += 1
print("round chip mismatches (own seat):", mism)

# ---------- per team-table results ----------
obs = collections.defaultdict(list)  # team -> list of (round, bb100 at table, hands)
for d in T:
    n = len(d["players"]); H = len(d["hands"])
    for s, p in enumerate(d["players"]):
        c = sum(h["results"][s] for h in d["hands"])
        obs[p].append((rn(d), c / 20 / H * 100, H))

# estimate per-1000-hand-round SD of a single bot from tables (within-team SD)
within = []
for p, L in obs.items():
    if len(L) >= 8:
        x = np.array([b for _, b, _ in L]); within.append((p, x.mean(), x.std(ddof=1), len(x)))
sds = np.array([w[2] for w in within])
print("\nper-round (1000 hands) SD of bb/100, median over teams: %.1f  (IQR %.1f-%.1f)" % (np.median(sds), *np.percentile(sds, [25, 75])))

# ---------- leaderboard history -> per-round increments for every team ----------
rows = list(csv.DictReader(open(os.path.join(DATA, "leaderboard_history_r13_r48.csv"), encoding="utf-8-sig")))
cum = collections.defaultdict(dict)  # played -> team -> chips (last capture)
for r in rows:
    if r["played"] in ("", "None"):
        continue
    cum[int(r["played"])][r["team"]] = (int(r["chips"]), int(r["rounds"]))
cum[54] = {r["name"]: (r["chips"], r["rounds"]) for r in final}
ps = sorted(cum)
inc = collections.defaultdict(dict)  # team -> round -> bb100
for a, b in zip(ps, ps[1:]):
    if b - a != 1:
        continue
    for t, (c, nr) in cum[b].items():
        if t in cum[a] and nr - cum[a][t][1] == 1:
            inc[t][b] = (c - cum[a][t][0]) / 20 / 1000 * 100
print("per-round increments from leaderboard: rounds", min(min(v) for v in inc.values() if v), "-", max(max(v) for v in inc.values() if v),
      "teams", len(inc))
allinc = np.array([x for t in inc for x in inc[t].values()])
print("leaderboard per-round SD (pooled within team): %.1f" % np.sqrt(np.mean([np.var(list(inc[t].values()), ddof=1) for t in inc if len(inc[t]) > 5])))

# split-half reliability on leaderboard increments (odd vs even rounds)
teams = [t for t in inc if len(inc[t]) >= 30]
odd = np.array([np.mean([v for k, v in inc[t].items() if k % 2]) for t in teams])
even = np.array([np.mean([v for k, v in inc[t].items() if not k % 2]) for t in teams])
r = np.corrcoef(odd, even)[0, 1]
print("split-half (odd vs even rounds) corr of team bb/100: %.2f over %d teams; Spearman-Brown full: %.2f" % (r, len(teams), 2 * r / (1 + r)))
# variance decomposition
m = np.array([np.mean(list(inc[t].values())) for t in teams]); nr = np.array([len(inc[t]) for t in teams])
wv = np.mean([np.var(list(inc[t].values()), ddof=1) for t in teams])
bv = np.var(m, ddof=1); noise = wv / np.mean(nr)
print("between-team var of means %.0f, of which noise %.0f -> true-skill SD %.1f bb/100; per-round noise SD %.1f" % (bv, noise, math.sqrt(max(bv - noise, 0)), math.sqrt(wv)))
print("=> one 1000-hand round: skill explains %.0f%% of variance of a team's result" % (100 * (bv - noise) / (bv - noise + wv)))
# first-half vs second-half
fh = np.array([np.mean([v for k, v in inc[t].items() if k <= 31]) for t in teams])
sh = np.array([np.mean([v for k, v in inc[t].items() if k > 31]) for t in teams])
print("first-half(14-31) vs second-half(32-48) corr: %.2f" % np.corrcoef(fh, sh)[0, 1])

# final standings spread and SE
sd_round = math.sqrt(wv)
print("\nFINAL standings with ±1 SE (SE = %.1f/sqrt(rounds)):" % sd_round)
for i, r in enumerate(final):
    se = sd_round / math.sqrt(max(r["rounds"], 1))
    print("%2d %-26s %6.1f ±%4.1f  rounds %2d  v%-2d to %3d" % (i + 1, r["name"][:26], r["bb100"], se, r["rounds"], r["version"], r["timeouts"]))
json.dump({"inc": inc, "teams": teams}, open(os.path.join(DATA, "per_round_increments.json"), "w"))
