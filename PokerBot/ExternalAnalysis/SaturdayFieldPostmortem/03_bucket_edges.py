import csv, glob, json, math, os, re, sys, collections, random
import numpy as np
from common import DATA, hand_files

final = json.load(open(os.path.join(DATA, "final_standings_saturday.json")))["saturday"]["standings"]
LB = {r["name"]: r["bb100"] for r in final}
inc = json.load(open(os.path.join(DATA, "per_round_increments.json")))["inc"]
tables = {}
for f in sorted(hand_files()):
    d = json.load(open(f, encoding="utf-8"))
    if "practice" in d["ref"]: continue
    tables.setdefault((d["ref"], tuple(d["players"])), d)
T = list(tables.values())
rn = lambda d: int(re.search(r"r(\d+)$", d["ref"]).group(1))
bb = lambda c, H: c / 20 / H * 100

# 1. our observed per-table result vs leaderboard increment for same team/round
diffs = []; sel_obs = []; sel_lb_all = collections.defaultdict(list)
for d in T:
    r = rn(d)
    for s, p in enumerate(d["players"]):
        o = bb(sum(h["results"][s] for h in d["hands"]), len(d["hands"]))
        if p in inc and str(r) in inc[p]:
            diffs.append(o - inc[p][str(r)])
print("obs vs LB increment same team-round: n=%d, max |diff| %.3f" % (len(diffs), max(abs(x) for x in diffs)))
# are rounds where teams sat with us less variable than their other rounds?
seen = collections.defaultdict(set)
for d in T:
    for p in d["players"]: seen[p].add(rn(d))
a_in, a_out = [], []
for p in inc:
    if p in ("Red", "WBot", "kaiserbot"): continue
    i_ = [v for k, v in inc[p].items() if int(k) in seen[p]]; o_ = [v for k, v in inc[p].items() if int(k) not in seen[p]]
    if len(i_) > 5 and len(o_) > 5: a_in.append(np.var(i_, ddof=1)); a_out.append(np.var(o_, ddof=1))
print("team round-SD when at our tables %.1f vs when not %.1f (n teams %d)" % (math.sqrt(np.mean(a_in)), math.sqrt(np.mean(a_out)), len(a_in)))

# which tables had the huge donors? SD with/without clanker/ediz present
don = {"clanker", "ediz_slow"}
w_, wo = [], []
for p in inc:
    for k, v in inc[p].items():
        pass
for d in T:
    has = bool(don & set(d["players"]))
    for s, p in enumerate(d["players"]):
        if p in don: continue
        (w_ if has else wo).append(bb(sum(h["results"][s] for h in d["hands"]), 1000))
print("per-seat result SD at tables WITH clanker/ediz %.1f (mean %+.1f, n=%d) vs WITHOUT %.1f (mean %+.1f, n=%d)" % (
    np.std(w_), np.mean(w_), len(w_), np.std(wo), np.mean(wo), len(wo)))

# 2. SmartBGerBot / extreme increments
print("\nextreme single-round results on the leaderboard (|bb/100| > 250):")
for p in inc:
    for k, v in sorted(inc[p].items(), key=lambda kv: int(kv[0])):
        if abs(v) > 250: print("   r%s %-20s %+7.1f" % (k, p, v))

# 3. version churn and drift: displayed_version by round
rows = list(csv.DictReader(open(os.path.join(DATA, "leaderboard_history_r13_r48.csv"), encoding="utf-8-sig")))
ver = collections.defaultdict(dict)
for r in rows:
    if r["played"] not in ("", "None"): ver[r["team"]][int(r["played"])] = int(r["displayed_version"])
print("\nfirst-half (r14-31) vs second-half (r32-48) mean bb/100 and uploads during r13-48:")
for f in final[:16] + [x for x in final if x["name"] in ("Anton", "AIl IN", "Joca", "clanker")]:
    p = f["name"]
    if p not in inc: continue
    a = [v for k, v in inc[p].items() if int(k) <= 31]; b = [v for k, v in inc[p].items() if int(k) > 31]
    vv = ver[p]; ups = len(set(vv.values())) - 1 if vv else 0
    print("   %-22s %+6.1f -> %+6.1f   uploads %2d   v%s->v%s" % (p[:22], np.mean(a), np.mean(b), ups, vv.get(min(vv)) if vv else "?", vv.get(max(vv)) if vv else "?"))

# rolling top-10 vs field: does the top get stronger? field spread per block
print("\nspread of team means per block (SD across teams, top-5 mean, bottom-5 mean):")
for lo, hi in [(14, 25), (26, 37), (38, 48)]:
    ms = sorted([np.mean([v for k, v in inc[p].items() if lo <= int(k) <= hi]) for p in inc if sum(lo <= int(k) <= hi for k in inc[p]) >= 8])
    print("   r%d-%d: teams %d  SD %.1f  top5 %+.1f  bottom5 %+.1f" % (lo, hi, len(ms), np.std(ms), np.mean(ms[-5:]), np.mean(ms[:5])))

# 4. pairwise vs NON-donors only (opponents finishing >= 0 bb/100): bucket-relevant edge
F = collections.defaultdict(float); N = collections.Counter(); SQ = collections.defaultdict(float)
for d in T:
    P = d["players"]; n = len(P)
    for h in d["hands"]:
        res = h["results"]; G = sum(-x for x in res if x < 0)
        if not G:
            for i in range(n):
                for j in range(n):
                    if i != j: N[(P[i], P[j])] += 1
            continue
        for i in range(n):
            for j in range(n):
                if i == j: continue
                v = 0.0
                if res[i] > 0 and res[j] < 0: v = res[i] * (-res[j]) / G
                elif res[j] > 0 and res[i] < 0: v = -res[j] * (-res[i]) / G
                F[(P[i], P[j])] += v; SQ[(P[i], P[j])] += v * v; N[(P[i], P[j])] += 1
def edge(p, opps):
    tot = sum(F[(p, q)] for q in opps if N[(p, q)]); hn = sum(N[(p, q)] for q in opps if N[(p, q)])
    var = sum(SQ[(p, q)] for q in opps if N[(p, q)]) / hn - (tot / hn) ** 2 if hn else 0
    return (bb(tot, hn) * 7, bb(math.sqrt(var / hn), 1) * 7) if hn else (float("nan"), 0)  # scaled to "7 opponents like these"
rank = [r["name"] for r in final]
donors = [p for p in rank if LB[p] < 0] + ["ediz_slow"]
top21 = rank[:21]
print("\nedge vs groups, as bb/100 at a table of 7 such opponents (±1 SE):")
print("   %-22s %8s %16s %16s %16s" % ("team", "LB", "vs donors", "vs top-21", "vs ranks 8-16"))
mid = rank[7:16]
for p in rank[:22] + ["Red", "kaiserbot", "AAST"]:
    e1 = edge(p, [q for q in donors if q != p]); e2 = edge(p, [q for q in top21 if q != p]); e3 = edge(p, [q for q in mid if q != p])
    print("   %-22s %+8.1f  %+7.1f ±%5.1f  %+7.1f ±%5.1f  %+7.1f ±%5.1f" % (p[:22], LB.get(p, float('nan')), *e1, *e2, *e3))

# share of profit from donors
print("\nshare of each team's net flow that came from donors:")
for p in rank[:8] + ["WBot"]:
    tot = sum(F[(p, q)] for q in set(x for k in N for x in k) if q != p)
    fd = sum(F[(p, q)] for q in donors if q != p)
    print("   %-22s from donors %5.0f%%" % (p[:22], 100 * fd / tot if tot else float("nan")))

# 5. WBot direct vs likely bucket mates
print("\nWBot head-to-head (net bb per 100 hands together):")
for q in rank[6:17]:
    if q == "WBot": continue
    n_ = N[("WBot", q)]
    if n_: print("   vs %-22s %+6.1f  (%d hands)" % (q[:22], bb(F[("WBot", q)], n_), n_))

# 6. Sunday lottery: block buckets of 7 by rank, 36 rounds, top-2 by chips advance
sd_round = 50.0
skill = {p: LB[p] for p in rank}
blocks = [rank[i:i + 7] for i in range(0, 35, 7)]
print("\nSunday sim (assumes block buckets of 7, 36 rounds, per-round SD %.0f, skill = Saturday bb/100 shrunk 30%% to bucket mean):" % sd_round)
random.seed(1)
for bi, B in enumerate(blocks):
    mu = np.mean([skill[p] for p in B])
    sk = {p: mu + 0.7 * (skill[p] - mu) for p in B}  # shrink toward bucket mean (regression to the mean)
    sk = {p: v - np.mean(list(sk.values())) for p, v in sk.items()}  # zero-sum inside the bucket
    wins = collections.Counter()
    for _ in range(20000):
        tot = {p: sum(random.gauss(sk[p], sd_round) for _ in range(1)) for p in B}
        tot = {p: random.gauss(sk[p], sd_round / 6.0) for p in B}  # 36 rounds -> SD/6
        for p in sorted(tot, key=lambda x: -tot[x])[:2]: wins[p] += 1
    print("   bucket %d: " % (bi + 1) + ", ".join("%s %.0f%%" % (p[:14], 100 * wins[p] / 20000) for p in B))
