"""Robustness checks requested in the PR #7 review.

1. Attribution: how much chip volume comes from hands with more than one winner? Those are the only hands
   where splitting losers' chips between winners is a choice. With one winner, "A won x from B" is exact
   bookkeeping. It is still bookkeeping, not strategic EV: A's take from B can depend on who else is in the pot.
2. Table-block bootstrap (resampling whole tables): cluster-robust uncertainty for the pairwise rates, the
   additive model's cycle count, donor shares, edges vs the top 21, and the attribution-free
   "result at tables with vs without donors".
Uses committed inputs only (common.hand_files()). Deterministic seed.
"""
import collections, itertools, json, math, os, re
import numpy as np
from common import DATA, hand_files

B = 1000
rng = np.random.default_rng(20261114)
final = json.load(open(os.path.join(DATA, "final_standings_saturday.json")))["saturday"]["standings"]
LB = {r["name"]: r["bb100"] for r in final}
rank = [r["name"] for r in final]
DONORS = [p for p in rank if LB[p] < 0] + ["ediz_slow"]
TOP21 = rank[:21]
BIG7 = {"clanker", "ediz_slow", "AIl IN", "Joca", "YSL_TWIZZY", "Anton", "ND"}
FOCUS = ["Attention Is All In", "Gherkers", "The Market Makers", "Anker Batteries", "Resonance Qt", "FisherMen",
         "WBot", "Red", "kaiserbot"]

tables, seen = [], set()
multi_vol = tot_vol = multi_hands = n_hands = 0
for f in hand_files():
    d = json.load(open(f, encoding="utf-8-sig"))
    k = (d["ref"], tuple(d["players"]))
    if "practice" in d["ref"] or k in seen:
        continue
    seen.add(k)
    P = d["players"]; n = len(P)
    flow = collections.defaultdict(float); cnt = collections.Counter(); sq = collections.defaultdict(float)
    for h in d["hands"]:
        res = h["results"]; G = sum(-x for x in res if x < 0); W = [i for i in range(n) if res[i] > 0]
        n_hands += 1; tot_vol += G
        if len(W) > 1:
            multi_hands += 1; multi_vol += G
        for i in range(n):
            for j in range(n):
                if i != j:
                    cnt[(P[i], P[j])] += 1
        hf = collections.defaultdict(float)
        if G:
            for i in W:
                for j in range(n):
                    if res[j] < 0:
                        v = res[i] * (-res[j]) / G
                        hf[(i, j)] += v; hf[(j, i)] -= v
        for (i, j), v in hf.items():
            flow[(P[i], P[j])] += v; sq[(P[i], P[j])] += v * v
    seat_res = {p: sum(h["results"][s] for h in d["hands"]) for s, p in enumerate(P)}
    tables.append(dict(players=P, flow=flow, cnt=cnt, sq=sq, res=seat_res, H=len(d["hands"])))
T = len(tables)
print("unique counted tables: %d, hands: %d" % (T, n_hands))
print("hands with >1 winner: %.1f%% of hands, %.1f%% of chips lost" % (100 * multi_hands / n_hands, 100 * multi_vol / tot_vol))

names = sorted({p for t in tables for p in t["players"]}); idx = {p: i for i, p in enumerate(names)}; m = len(names)
Fm = np.zeros((T, m, m)); Nm = np.zeros((T, m, m)); SQm = np.zeros((T, m, m)); R = np.zeros((T, m)); Hm = np.zeros((T, m))
for t, tb in enumerate(tables):
    for (a, b), v in tb["flow"].items(): Fm[t, idx[a], idx[b]] = v
    for (a, b), c in tb["cnt"].items(): Nm[t, idx[a], idx[b]] = c
    for (a, b), v in tb["sq"].items(): SQm[t, idx[a], idx[b]] = v
    for p, c in tb["res"].items(): R[t, idx[p]] = c; Hm[t, idx[p]] = tb["H"]

def stats(w):
    """w = weight per table (bootstrap multiplicity). Returns pair-rate matrix and summary numbers."""
    F = np.tensordot(w, Fm, 1); N = np.tensordot(w, Nm, 1)
    with np.errstate(invalid="ignore", divide="ignore"):
        rate = np.where(N > 0, F / N / 20 * 100, np.nan)
    out = {}
    for p in FOCUS:
        i = idx[p]
        tot = F[i].sum()
        dj = [idx[q] for q in DONORS if q in idx and q != p]
        tj = [idx[q] for q in TOP21 if q in idx and q != p]
        hands_i = w @ Hm[:, i]
        oj = [j for j in range(m) if j != i and j not in dj]
        out[p + "|from_donors"] = F[i, dj].sum() / hands_i / 20 * 100
        out[p + "|from_others"] = F[i, oj].sum() / hands_i / 20 * 100
        out[p + "|vs_top21"] = 7 * F[i, tj].sum() / N[i, tj].sum() / 20 * 100 if N[i, tj].sum() else np.nan
        # attribution-free: own table result with vs without one of the 7 worst bots at the table
        has = np.array([bool(BIG7 & set(tb["players"]) - {p}) and p in tb["players"] for tb in tables])
        hasn = np.array([not (BIG7 & set(tb["players"]) - {p}) and p in tb["players"] for tb in tables])
        for lab, mask in (("with_donors", has), ("no_donors", hasn)):
            ww = w * mask
            out[p + "|" + lab] = (ww @ R[:, i]) / (ww @ Hm[:, i]) / 20 * 100 if (ww @ Hm[:, i]) else np.nan
    return rate, N, out

base_rate, base_N, base = stats(np.ones(T))
boots = []; rates = []
for _ in range(B):
    w = np.bincount(rng.integers(0, T, T), minlength=T).astype(float)
    r_, _, o = stats(w); boots.append(o); rates.append(r_)
rates = np.array(rates)
se = np.nanstd(rates, axis=0)

print("\nper team: point estimate [bootstrap 5%%, 95%%] (resampling whole tables, B=%d)" % B)
for key in ["from_donors", "from_others", "vs_top21", "with_donors", "no_donors"]:
    print("  %s:" % key)
    for p in FOCUS:
        v = np.array([b[p + "|" + key] for b in boots], dtype=float)
        lo, hi = np.nanpercentile(v, [5, 95])
        print("     %-22s %+7.1f  [%+7.1f, %+7.1f]" % (p[:22], base[p + "|" + key], lo, hi))

# additive model with cluster-bootstrap SEs
MIN_TABLES = 6
ntab = (Nm > 0).sum(axis=0)
Ft = Fm.sum(0); Nt = Nm.sum(0); SQt = SQm.sum(0)
with np.errstate(invalid="ignore", divide="ignore"):
    se_hand = np.sqrt((SQt / Nt - (Ft / Nt) ** 2) / Nt) / 20 * 100
pairs = [(i, j) for i in range(m) for j in range(i + 1, m) if ntab[i, j] >= MIN_TABLES and se[i, j] > 0]
deff = np.array([se[i, j] / se_hand[i, j] for i, j in pairs])
print("\npairs that met at >= %d tables: %d (of %d with >= 2 tables). table-bootstrap SE / per-hand SE: median %.2f, IQR %.2f-%.2f" % (
    MIN_TABLES, len(pairs), int(np.sum(np.triu(ntab, 1) >= 2)), np.median(deff), *np.percentile(deff, [25, 75])))
X = np.zeros((len(pairs), m)); y = np.array([base_rate[i, j] for i, j in pairs]); s = np.array([se[i, j] for i, j in pairs])
for r_, (i, j) in enumerate(pairs): X[r_, i] = 1; X[r_, j] = -1
Wh = 1 / s
sk, *_ = np.linalg.lstsq(np.vstack([X * Wh[:, None], np.ones(m) * 1e3]), np.concatenate([y * Wh, [0]]), rcond=None)
z = (y - X @ sk) * Wh
print("\nadditive model with table-bootstrap SEs: %d pairs; residual chi2/df %.2f (diagonal; ignores covariance between pairs, so NOT a calibrated test); |z|>3: %d" % (
    len(pairs), np.sum(z ** 2) / (len(pairs) - m + 1), int(np.sum(np.abs(z) > 3))))
sig = {}
for (i, j), yy, ss in zip(pairs, y, s):
    if abs(yy / ss) > 2: sig[(i, j)] = np.sign(yy); sig[(j, i)] = -np.sign(yy)
tri = cyc = 0
for a, b, c in itertools.combinations(range(m), 3):
    e = [sig.get((a, b)), sig.get((b, c)), sig.get((c, a))]
    if all(x is not None for x in e):
        tri += 1; cyc += e[0] == e[1] == e[2]
print("triads with all three edges |t|>2 under bootstrap SEs: %d, cyclic: %d" % (tri, cyc))
print("pairs with |t|>2: %d of %d (5%% expected by chance = %.0f)" % (sum(1 for k in sig) // 2, len(pairs), 0.05 * len(pairs)))
