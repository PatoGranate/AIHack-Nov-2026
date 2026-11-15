"""Styles per team, style vs result, pairwise flows, transitivity, donor concentration, table effects."""
import contextlib, glob, io, json, math, os, re, sys, collections
import numpy as np
from common import DATA, hand_files

import hand_stats as A

final = json.load(open(os.path.join(DATA, "final_standings_saturday.json")))["saturday"]["standings"]
LB = {r["name"]: r["bb100"] for r in final}
inc = json.load(open(os.path.join(DATA, "per_round_increments.json")))["inc"]

tables = {}
for f in sorted(hand_files()):
    d = json.load(open(f, encoding="utf-8"))
    if "practice" in d["ref"]:
        continue
    tables.setdefault((d["ref"], tuple(d["players"])), d)
T = list(tables.values())
rn = lambda d: int(re.search(r"r(\d+)$", d["ref"]).group(1))

# ---------- styles ----------
KEYS = ["hands", "chips", "vpip", "pfr", "three", "three_opp", "allin_pre", "limp", "f_raise", "f_raise_opp", "bet", "call",
        "check", "f_bet", "f_bet_opp", "saw_flop", "sd", "sd_won", "sd_chips", "nosd_chips", "big_pots"]
agg = collections.defaultdict(lambda: collections.Counter())
opens = collections.defaultdict(list); betf = collections.defaultdict(list)
tab_res = collections.defaultdict(list)
pos_res = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
for d in T:
    with contextlib.redirect_stdout(io.StringIO()):
        st, _ = A.analyse_round(d)
    n = len(d["players"])
    for s, p in enumerate(d["players"]):
        for k in KEYS:
            agg[p][k] += st[s][k]
        agg[p]["tables"] += 1
        opens[p] += st[s]["open_sizes"]; betf[p] += st[s]["bet_fracs"]
        tab_res[p].append(st[s]["chips"] / 20 / len(d["hands"]) * 100)
    for h in d["hands"]:
        for s, p in enumerate(d["players"]):
            rel = (s - h["button"]) % n  # 0 BTN 1 SB 2 BB, n-1 CO
            lab = {0: "BTN", 1: "SB", 2: "BB", n - 1: "CO"}.get(rel, "EP/MP")
            pos_res[p][lab][0] += 1; pos_res[p][lab][1] += h["results"][s]

def prof(p):
    a = agg[p]; H = a["hands"]; P = lambda x, y: 100.0 * x / y if y else float("nan")
    return dict(team=p, tables=a["tables"], hands=H, obs=a["chips"] / 20 / H * 100, lb=LB.get(p, float("nan")),
                vpip=P(a["vpip"], H), pfr=P(a["pfr"], H), three=P(a["three"], a["three_opp"]), aipf=P(a["allin_pre"], H),
                limp=P(a["limp"], H), fvr=P(a["f_raise"], a["f_raise_opp"]), fvb=P(a["f_bet"], a["f_bet_opp"]),
                af=P(a["bet"], a["bet"] + a["call"]), flop=P(a["saw_flop"], H), wtsd=P(a["sd"], a["saw_flop"]),
                wsd=P(a["sd_won"], a["sd"]), sdbb=a["sd_chips"] / 20 / H * 100, nsdbb=a["nosd_chips"] / 20 / H * 100,
                open=float(np.median(opens[p])) / 1 if opens[p] else float("nan"),
                betp=float(np.median(betf[p])) if betf[p] else float("nan"),
                sd_round=float(np.std(tab_res[p], ddof=1)) if len(tab_res[p]) > 2 else float("nan"),
                lb_sd=float(np.std(list(inc[p].values()), ddof=1)) if p in inc and len(inc[p]) > 5 else float("nan"))

profs = sorted([prof(p) for p in agg if agg[p]["hands"] >= 5000], key=lambda r: -(r["lb"] if not math.isnan(r["lb"]) else r["obs"]))
hdr = "%-22s %3s %6s %6s | %4s %4s %4s %4s %4s %4s %4s %4s %4s %4s %4s | %6s %6s | %4s %4s | %5s %5s"
print(hdr % ("team", "tab", "LB", "obs", "VPIP", "PFR", "3b", "AIpf", "limp", "FvR", "FvB", "AF", "flop", "WTSD", "W$SD", "SDbb", "nSDbb", "open", "betp", "sdR", "sdLB"))
for r in profs:
    print("%-22s %3d %6.1f %6.1f | %4.0f %4.0f %4.0f %4.1f %4.0f %4.0f %4.0f %4.0f %4.0f %4.0f %4.0f | %+6.1f %+6.1f | %4.1f %4.2f | %5.0f %5.0f" % (
        r["team"][:22], r["tables"], r["lb"], r["obs"], r["vpip"], r["pfr"], r["three"], r["aipf"], r["limp"], r["fvr"], r["fvb"], r["af"],
        r["flop"], r["wtsd"], r["wsd"], r["sdbb"], r["nsdbb"], r["open"], r["betp"], r["sd_round"], r["lb_sd"]))
json.dump(profs, open(os.path.join(DATA, "team_profiles.json"), "w"))

# style vs result (ranked teams only, use leaderboard bb/100 = less noisy)
R = [r for r in profs if not math.isnan(r["lb"])]
y = np.array([r["lb"] for r in R])
print("\ncorrelation of style stat with final bb/100 (n=%d):" % len(R))
for k in ["vpip", "pfr", "three", "aipf", "limp", "fvr", "fvb", "af", "wtsd", "wsd", "open", "betp", "sd_round"]:
    x = np.array([r[k] for r in R]); ok = ~np.isnan(x)
    print("  %-8s r=%+.2f" % (k, np.corrcoef(x[ok], y[ok])[0, 1]))
# VPIP bands
print("\nVPIP band -> mean final bb/100:")
for lo, hi in [(0, 18), (18, 24), (24, 30), (30, 40), (40, 101)]:
    g = [r for r in R if lo <= r["vpip"] < hi]
    if g: print("  VPIP %2d-%3d: n=%2d  mean %+6.1f  [%s]" % (lo, hi, len(g), np.mean([r["lb"] for r in g]), ", ".join("%s %.0f" % (r["team"][:12], r["lb"]) for r in g)))

# position profile for top / us
print("\nbb/100 by position (observed):")
for p in ["Attention Is All In", "Gherkers", "The Market Makers", "Resonance Qt", "WBot", "Red", "kaiserbot", "Joca", "AIl IN", "clanker"]:
    if p in pos_res:
        print("  %-20s " % p[:20] + "  ".join("%s %+6.0f" % (k, v[1] / 20 / v[0] * 100) for k, v in sorted(pos_res[p].items())))

# ---------- pairwise flows ----------
F = collections.defaultdict(float); N = collections.Counter(); SQ = collections.defaultdict(float)
for d in T:
    P = d["players"]; n = len(P)
    for h in d["hands"]:
        res = h["results"]; G = sum(-x for x in res if x < 0)
        net = collections.defaultdict(float)
        if G:
            for i in range(n):
                if res[i] > 0:
                    for j in range(n):
                        if res[j] < 0:
                            f = res[i] * (-res[j]) / G
                            net[(i, j)] += f; net[(j, i)] -= f
        for i in range(n):
            for j in range(i + 1, n):
                a, b = P[i], P[j]; v = net.get((i, j), 0.0)
                if a > b: a, b, v = b, a, -v
                F[(a, b)] += v; SQ[(a, b)] += v * v; N[(a, b)] += 1

names = sorted({p for k in N for p in k}); idx = {p: i for i, p in enumerate(names)}
pairs = [k for k in N if N[k] >= 2000]
rows, w, yv = [], [], []
for (a, b) in pairs:
    n_ = N[(a, b)]; m = F[(a, b)] / n_; var = SQ[(a, b)] / n_ - m * m; se = math.sqrt(var / n_)
    rows.append((a, b)); yv.append(m / 20 * 100); w.append(1 / (se / 20 * 100) ** 2)
X = np.zeros((len(rows), len(names)))
for r_, (a, b) in enumerate(rows):
    X[r_, idx[a]] = 1; X[r_, idx[b]] = -1
yv = np.array(yv); w = np.array(w); Wh = np.sqrt(w)
# anchor: sum of skills = 0
Xa = np.vstack([X * Wh[:, None], np.ones(len(names)) * 1e3]); ya = np.concatenate([yv * Wh, [0]])
s_hat, *_ = np.linalg.lstsq(Xa, ya, rcond=None)
pred = X @ s_hat; resid = yv - pred
chi2 = float(np.sum(w * resid ** 2)); df = len(rows) - (len(names) - 1)
wy = np.average(yv, weights=w)
R2 = 1 - np.sum(w * resid ** 2) / np.sum(w * (yv - wy) ** 2)
print("\nPAIRWISE: %d pairs with >=2000 hands together, %d teams" % (len(rows), len(names)))
print("additive (transitive) skill model: weighted R2 = %.2f; chi2 = %.0f on df %d (chi2/df = %.2f; 1.0 = residuals are pure noise)" % (R2, chi2, df, chi2 / df))
z = resid * Wh
print("residual |z|>3 pairs: %d (expected by chance ~%.1f)" % (int(np.sum(np.abs(z) > 3)), 0.0027 * len(rows)))
for k in np.argsort(-np.abs(z))[:8]:
    a, b = rows[k]
    print("   %-20s vs %-20s obs %+6.1f  pred %+6.1f  z %+.1f  hands %d" % (a[:20], b[:20], yv[k], pred[k], z[k], N[(a, b)]))
print("pairwise skill vs leaderboard corr: %.2f" % np.corrcoef([s_hat[idx[p]] for p in names if p in LB], [LB[p] for p in names if p in LB])[0, 1])

# cycles: count intransitive triads among pairs significant at |t|>2
sig = {}
for k, (a, b) in enumerate(rows):
    t = yv[k] * Wh[k]
    if abs(t) > 2: sig[(a, b)] = 1 if t > 0 else -1
beats = lambda a, b: sig.get((a, b)) if (a, b) in sig else (-sig[(b, a)] if (b, a) in sig else 0)
tri = cyc = 0
import itertools
for a, b, c in itertools.combinations(names, 3):
    x, y_, z_ = beats(a, b), beats(b, c), beats(c, a)
    if x and y_ and z_:
        tri += 1; cyc += (x == y_ == z_)
print("triads with all three edges significant: %d, of which cyclic (RPS): %d" % (tri, cyc))

# whom do the top teams win from?
print("\nwhere profits come from (net bb per 100 hands together, from pairwise flows):")
for p in ["Attention Is All In", "Gherkers", "The Market Makers", "WBot", "Red", "kaiserbot"]:
    L = []
    for (a, b) in N:
        if p in (a, b) and N[(a, b)] >= 1000:
            v = F[(a, b)] / 20 * 100 / N[(a, b)]
            L.append((b if a == p else a, v if a == p else -v, N[(a, b)]))
    L.sort(key=lambda t: -t[1])
    print("  %-20s best: %s" % (p, ", ".join("%s %+.1f" % (o[:10], v) for o, v, _ in L[:5])))
    print("  %-20s worst: %s" % ("", ", ".join("%s %+.1f" % (o[:10], v) for o, v, _ in L[-4:])))
    neg = sum(1 for _, v, _ in L if v < 0)
    print("  %-20s opponents with negative net: %d of %d" % ("", neg, len(L)))

# donor concentration: total chips lost by losers on the final leaderboard
loss = sorted([(r["chips"], r["name"]) for r in final])
tot_loss = -sum(c for c, _ in loss if c < 0); tot_win = sum(c for c, _ in loss if c > 0)
print("\nfinal standings: total won by winners %d, total lost by losers %d (diff = removed accounts etc.)" % (tot_win, tot_loss))
print("losers:", ", ".join("%s %d" % (nm[:12], c) for c, nm in loss if c < 0))
json.dump({"s": {p: float(s_hat[idx[p]]) for p in names}}, open(os.path.join(DATA, "pairwise_skill.json"), "w"))

# ---------- table composition effect ----------
# team result at table vs mean opponent pairwise-skill at that table
xs, ys = [], []
for d in T:
    P = d["players"]
    for s, p in enumerate(P):
        if p not in idx: continue
        opp = np.mean([s_hat[idx[q]] for q in P if q != p and q in idx])
        r_ = sum(h["results"][s] for h in d["hands"]) / 20 / len(d["hands"]) * 100
        xs.append((s_hat[idx[p]], opp)); ys.append(r_)
xs = np.array(xs); ys = np.array(ys)
Xm = np.column_stack([np.ones(len(ys)), xs])
b, *_ = np.linalg.lstsq(Xm, ys, rcond=None)
pr = Xm @ b
print("\ntable result ~ own skill + mean opp skill: coef own %.2f, opp %.2f; R2 %.3f" % (b[1], b[2], 1 - np.var(ys - pr) / np.var(ys)))
print("  -> each +10 bb/100 of average opponent skill changes your table result by %+.1f bb/100" % (10 * b[2]))
