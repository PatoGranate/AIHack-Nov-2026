"""Postflop fold/continue rates by context, per opponent, with table-bootstrap intervals; heterogeneity across the field.

Decision definition (primary): a player's FIRST response to the FIRST bet on a flop/turn/river while exactly one
bet is outstanding (fold vs continue = call or raise). "Facing a raise" decisions are reported separately.
Size = bettor's added chips / pot before the bet. HU = exactly two live players at the decision.
IP = the responder acts after the bettor postflop. Callers = calls of this bet before the decision.

Everything here is a frequency of observed public actions. Nothing measures profitability.
Writes data/out_01_postflop_context.txt and data/postflop_context_summary.json.
"""
import json
import sys

import numpy as np

import oc_parse as P
import oc_stats as S

sys.stdout = S.Tee(S.out_path("out_01_postflop_context.txt"))
rng = np.random.default_rng(S.SEED)

tables = P.load_tables()
post, pre, bot = P.extract(tables)
fb = [r for r in post if r["facing"] == "bet" and r["first"]]
FOLD = lambda r: r["action"] == "fold"
HERO = P.HERO
hero_tables = {ti for ti, (_, _, d) in enumerate(tables) if HERO in d["players"]}

print("Opponent context audit, postflop (exploratory, descriptive)")
print("python %s, numpy %s" % (sys.version.split()[0], np.__version__))
print("inputs: %d unique counted tables, %d hands (same set as the post-mortem manifest; checked)"
      % (len(tables), sum(len(d["hands"]) for _, _, d in tables)))
print("first responses to a first postflop bet: %d; facing-a-raise decisions: %d"
      % (len(fb), sum(r["facing"] == "raise" for r in post)))
print("bootstrap: %d table resamples per estimate, 90%% percentile intervals; seed %d" % (S.B, S.SEED))

SIZE2 = ["S<50%", "L>=50%"]
s2 = lambda r: SIZE2[0] if r["size_x"] < 0.5 else SIZE2[1]
FAM = {
    "all": (["all"], lambda r: "all", fb),
    "humw": (["HU", "MW"], lambda r: "HU" if r["hu"] else "MW", fb),
    "size4": (P.SIZE_LABELS, lambda r: r["size"], fb),
    "size2": (SIZE2, s2, fb),
    "humw_size2": (["HU S", "HU L", "MW S", "MW L"],
                   lambda r: ("HU " if r["hu"] else "MW ") + s2(r)[0], fb),
    "hu_flop_size2": (SIZE2, lambda r: s2(r) if (r["hu"] and r["street"] == "flop") else None, fb),
    "street": (["flop", "turn", "river"], lambda r: r["street"], fb),
    "ip": (["IP", "OOP"], lambda r: "IP" if r["ip"] else "OOP", fb),
    "hu_ip": (["HU IP", "HU OOP"], lambda r: None if not r["hu"] else ("HU IP" if r["ip"] else "HU OOP"), fb),
    "mw_callers": (["MW 0 callers", "MW 1+ callers"],
                   lambda r: None if r["hu"] else ("MW 0 callers" if r["callers"] == 0 else "MW 1+ callers"), fb),
    "facing": (["bet", "raise"], lambda r: r["facing"] if (r["facing"] == "raise" or r["first"]) else None, post),
    "bettor": (["vs WBot", "vs others"],
               lambda r: None if (r["t"] not in hero_tables or r["name"] == HERO)
               else ("vs WBot" if r["bettor"] == HERO else "vs others"), fb),
    "half": (["r01-27", "r28-54"], lambda r: "r01-27" if r["rnd"] <= 27 else "r28-54", fb),
}
G = {f: S.counts(recs, labels, key, FOLD) for f, (labels, key, recs) in FAM.items()}
LAB = {f: FAM[f][0] for f in FAM}
BOT = {}
for r in bot:
    BOT.setdefault(r["name"], {})[r["t"]] = (r["ffold"], r["faced"])

# ---------------------------------------------------------------- 1. samples per round
print("\n== 1. Decisions per 1,000-hand round (per opponent-table): median [10th, 90th percentile] ==")
print("Field = every non-WBot seat at every counted table; T4 = the seven table-4 opponents only.")


def per_round(fam, names):
    rows = {l: [] for l in LAB[fam]}
    for nm in names:
        if nm not in G[fam]:
            continue
        _, _, N = G[fam][nm]
        for j, l in enumerate(LAB[fam]):
            rows[l].extend(N[:, j].tolist())
    return rows


field_names = [nm for nm in G["all"] if nm != HERO]
samples = {}
for fam in ["all", "humw", "size2", "humw_size2", "size4", "street", "ip", "mw_callers", "facing"]:
    for scope, names in (("field", field_names), ("T4", P.TABLE4)):
        pr = per_round(fam, names)
        for l, v in pr.items():
            v = np.array(v)
            samples.setdefault(scope, {})[l if fam != "all" else "all first-bet"] = dict(
                median=float(np.median(v)), p10=float(np.percentile(v, 10)), p90=float(np.percentile(v, 90)),
                opp_tables=int(len(v)))
bf = np.array([BOT[nm][t][1] for nm in field_names for t in BOT[nm]])
b4 = np.array([BOT[nm][t][1] for nm in P.TABLE4 for t in BOT[nm]])
for scope, v in (("field", bf), ("T4", b4)):
    samples[scope]["bot 'faced' counter"] = dict(median=float(np.median(v)), p10=float(np.percentile(v, 10)),
                                                 p90=float(np.percentile(v, 90)), opp_tables=int(len(v)))
print("%-24s %-22s %-22s" % ("bucket", "field", "T4"))
for l in samples["field"]:
    f, t = samples["field"][l], samples["T4"][l]
    print("%-24s %4.0f [%3.0f,%4.0f] (%4d)    %4.0f [%3.0f,%4.0f] (%3d)" % (
        l, f["median"], f["p10"], f["p90"], f["opp_tables"], t["median"], t["p10"], t["p90"], t["opp_tables"]))
print("Binomial SE of a raw in-round rate at p=0.45: n=10 -> 16 pts, n=25 -> 10, n=50 -> 7, n=100 -> 5.")

# ---------------------------------------------------------------- 2. per-opponent profiles
summary = {"samples_per_round": samples, "opponents": {}}


def profile(nm, fams):
    out = {}
    for fam in fams:
        if nm not in G[fam]:
            continue
        ts, K, N = G[fam][nm]
        point, draws, _ = S.boot_rates(K, N, rng)
        lo, hi = S.ci(draws)
        for j, l in enumerate(LAB[fam]):
            out[fam + ":" + l] = dict(rate=None if np.isnan(point[j]) else float(point[j]),
                                      lo=float(lo[j]), hi=float(hi[j]), n=int(N[:, j].sum()),
                                      tables=int((N[:, j] > 0).sum()))
    if nm in BOT:
        k = np.array([BOT[nm][t][0] for t in sorted(BOT[nm])], float)[:, None]
        n = np.array([BOT[nm][t][1] for t in sorted(BOT[nm])], float)[:, None]
        point, draws, _ = S.boot_rates(k, n, rng)
        lo, hi = S.ci(draws)
        out["bot_ftb_raw"] = dict(rate=float(point[0]), lo=float(lo[0]), hi=float(hi[0]), n=int(n.sum()),
                                  tables=len(k))
    return out


SHOW = ["all", "humw", "humw_size2", "size4", "street", "ip", "mw_callers", "facing", "bettor", "half"]
for nm in P.TABLE4 + P.STRONG + [HERO]:
    summary["opponents"][nm] = profile(nm, SHOW + ["size2", "hu_flop_size2", "hu_ip"])

print("\n== 2. Fold rate by context: rate [90% table-bootstrap CI] n=decisions ==")
for block, names in (("Table-4 opponents", P.TABLE4), ("Strong teams (not at our table)", P.STRONG),
                     ("WBot itself (for reference)", [HERO])):
    print("\n-- %s --" % block)
    for nm in names:
        pr = summary["opponents"][nm]
        print("\n%s  (%d tables)" % (nm, pr["all:all"]["tables"]))
        line = []
        for key in [k for k in pr if k != "bot_ftb_raw"]:
            v = pr[key]
            line.append("  %-26s %s" % (key, "- (n=0)" if v["rate"] is None else
                                       "%2.0f%% [%2.0f,%2.0f] n=%d" % (100 * v["rate"], 100 * v["lo"], 100 * v["hi"], v["n"])))
        v = pr["bot_ftb_raw"]
        line.append("  %-26s %2.0f%% [%2.0f,%2.0f] n=%d" % ("bot's pooled ftb counter", 100 * v["rate"], 100 * v["lo"],
                                                            100 * v["hi"], v["n"]))
        print("\n".join(line))

# ---------------------------------------------------------------- 3. heterogeneity
print("\n== 3. Does it vary between opponents? (all non-WBot teams with >=5 tables and >=30 decisions per bucket) ==")
print("tau = DerSimonian-Laird between-team SD (pts, probability scale; logit scale in brackets).")
print("p_sim = share of %d null simulations (no between-team variation, real per-table counts) with Q >= observed." % S.SIM)
print("k* = p(1-p)/tau^2 = the beta-binomial prior weight (pseudo-decisions) that this tau implies; exploratory.")
print("rel1 = tau_logit^2 / (tau_logit^2 + SE^2), SE = logit-scale binomial SE of ONE round's estimate at the field")
print("median per-round counts: the share of an opponent's true deviation that one round of data can recover.")
print("mean = random-effects mean across teams (p = percentage-point effect).")
specs = [
    ("level: all first-bet", "all", 0, None), ("level: HU", "humw", 0, None), ("level: MW", "humw", 1, None),
    ("level: HU S<50%", "humw_size2", 0, None), ("level: HU L>=50%", "humw_size2", 1, None),
    ("level: MW S<50%", "humw_size2", 2, None), ("level: MW L>=50%", "humw_size2", 3, None),
    ("level: flop", "street", 0, None), ("level: turn", "street", 1, None), ("level: river", "street", 2, None),
    ("level: facing raise", "facing", 1, None),
    ("effect: MW - HU", "humw", 1, 0), ("effect: L - S (all)", "size2", 1, 0),
    ("effect: L - S (HU flop)", "hu_flop_size2", 1, 0),
    ("effect: L - S (HU)", "humw_size2", 1, 0), ("effect: L - S (MW)", "humw_size2", 3, 2),
    ("effect: turn - flop", "street", 1, 0), ("effect: river - flop", "street", 2, 0),
    ("effect: OOP - IP", "ip", 1, 0), ("effect: HU OOP - HU IP", "hu_ip", 1, 0),
    ("effect: MW 1+ callers - 0", "mw_callers", 1, 0), ("effect: raise - bet", "facing", 1, 0),
    ("effect: late - early half", "half", 1, 0),
]
field_groups = {f: {nm: g for nm, g in G[f].items() if nm != HERO} for f in G}
het = {}
print("%-28s %3s %7s %13s %6s %7s %8s %5s %5s" % ("quantity", "k", "mean", "tau [logit]", "p_sim", "p_simL", "Q/null",
                                                 "k*", "rel1"))


def round_se2(fam, a):
    """Logit-scale binomial variance of one round's estimate in bucket a, at field median count and field rate."""
    Ns = np.concatenate([g[2][:, a] for g in field_groups[fam].values()])
    k = sum(g[1][:, a].sum() for g in field_groups[fam].values())
    p = k / Ns.sum()
    nmed = max(1.0, float(np.median(Ns)))
    return 1.0 / (nmed * p * (1 - p))


for label, fam, a, b in specs:
    h = S.heterogeneity(field_groups[fam], a, b, rng=rng)
    if h is None:
        print("%-28s too few teams" % label)
        continue
    kstar = (h["mean"] * (1 - h["mean"]) / h["tau"] ** 2) if (b is None and h["tau"] > 0) else float("nan")
    se2 = round_se2(fam, a) + (0.0 if b is None else round_se2(fam, b))
    rel1 = h["tau_logit"] ** 2 / (h["tau_logit"] ** 2 + se2)
    het[label] = dict(k=h["k"], mean=h["mean"], tau=h["tau"], tau_logit=h["tau_logit"], p_sim=h["p_sim"],
                      p_sim_logit=h["p_sim_logit"], q=h["q"], q_null_median=h["q_null_med"],
                      kstar=None if np.isnan(kstar) else kstar, rel_one_round=float(rel1),
                      per_team={n: [float(y), float(s)] for n, y, s in zip(h["names"], h["y"], h["se"])})
    print("%-28s %3d %+6.1f%s %5.1f [%4.2f] %6.3f %7.3f %4.0f/%-4.0f %5s %5.2f" % (
        label, h["k"], 100 * h["mean"], " " if b is None else "p", 100 * h["tau"], h["tau_logit"], h["p_sim"],
        h["p_sim_logit"], h["q"], h["q_null_med"], "-" if np.isnan(kstar) else "%.0f" % kstar, rel1))
summary["heterogeneity"] = het

print("\n== 3b. Same question per opponent-TABLE (one seat in one 1,000-hand round; units with >=10 decisions) ==")
print("This is the spread an in-round estimate has to learn. tau_within = table-to-table drift inside a team")
print("(uploads, table mix); tau_between = team-level spread. p_sim from 1,000 binomial null simulations.")
print("%-22s %5s %6s %6s %6s %7s %7s %6s %6s" % ("bucket", "units", "med n", "mean", "tau", "within", "between", "p_sim", "k*"))
unit = {}
for label, fam, a in [("all first-bet", "all", 0), ("HU", "humw", 0), ("MW", "humw", 1), ("HU S<50%", "humw_size2", 0),
                      ("HU L>=50%", "humw_size2", 1), ("MW S<50%", "humw_size2", 2), ("MW L>=50%", "humw_size2", 3),
                      ("flop", "street", 0), ("turn", "street", 1), ("river", "street", 2), ("IP", "ip", 0),
                      ("OOP", "ip", 1), ("facing raise", "facing", 1), ("vs WBot's bets", "bettor", 0),
                      ("vs others' bets (WBot tables)", "bettor", 1)]:
    u = S.unit_tau(field_groups[fam], a, rng=rng)
    if u is None:
        print("%-22s too few units" % label)
        continue
    unit[label] = u
    print("%-22s %5d %6.0f %5.1f%% %5.1f %7.1f %7.1f %6.3f %6s" % (
        label[:22], u["units"], u["median_n"], 100 * u["mean"], 100 * u["tau"], 100 * u["tau_within"],
        100 * u["tau_between"], u["p_sim"], "-" if u["kstar"] is None else "%.0f" % u["kstar"]))
summary["opponent_table_heterogeneity"] = unit

# ---------------------------------------------------------------- 4. size response vs the bot's assumed curve
print("\n== 4. Field fold rate by bet size vs the bot's fixed size curve (diagnostic) ==")
print("Bot: continue_class(size) = continue_class(0.6 pot) ** ((size/0.6) ** size_exp); G_v7 size_exp=1.0, N_v10 0.575.")
print("Implied exponent e: log(c_b)/log(c_ref) = (s_b/s_ref)**e with ref = the 40-75% bucket (single-class reading).")
for scope, keyf in (("all first-bet", lambda r: r["size"]), ("HU flop only", lambda r: r["size"] if (r["hu"] and r["street"] == "flop") else None)):
    recs = [dict(r, name="FIELD") for r in fb if r["name"] != HERO]
    K = S.counts(recs, P.SIZE_LABELS, keyf, FOLD)["FIELD"]
    ssum = S.counts(recs, P.SIZE_LABELS, keyf, lambda r: r["size_x"])["FIELD"]
    _, Kf, Nf = K
    point, draws, W = S.boot_rates(Kf, Nf, rng)
    lo, hi = S.ci(draws)
    smean = ssum[1].sum(0) / Nf.sum(0)
    print("\n%s" % scope)
    ref = 1
    cd = 1 - draws
    with np.errstate(invalid="ignore", divide="ignore"):
        e_draw = np.log(np.log(cd) / np.log(cd[:, [ref]])) / np.log(smean / smean[ref])
        e_pt = np.log(np.log(1 - point) / np.log(1 - point[ref])) / np.log(smean / smean[ref])
    e_draw[:, ref] = 0.0
    elo, ehi = S.ci(e_draw)
    for j, l in enumerate(P.SIZE_LABELS):
        print("  %-8s mean size %.2f  fold %2.0f%% [%2.0f,%2.0f] n=%d  %s" % (
            l, smean[j], 100 * point[j], 100 * lo[j], 100 * hi[j], Nf[:, j].sum(),
            "(reference)" if j == ref else "implied e %.2f [%.2f,%.2f]" % (e_pt[j], elo[j], ehi[j])))
    summary.setdefault("size_curve", {})[scope] = dict(
        labels=P.SIZE_LABELS, mean_size=smean.tolist(), fold=point.tolist(), lo=lo.tolist(), hi=hi.tolist(),
        n=Nf.sum(0).tolist(), implied_e=[None if j == ref else float(e_pt[j]) for j in range(4)])

# ---------------------------------------------------------------- 5. responses to WBot's bets, by size
print("\n== 5. Opponents' fold rate vs WBot's bets vs other bettors, same tables, by size bucket ==")
for scope, names in (("all opponents", None), ("table-4 opponents", set(P.TABLE4))):
    recs = [dict(r, name="X") for r in fb if r["t"] in hero_tables and r["name"] != HERO
            and (names is None or r["name"] in names)]
    labels = [b + w for b in P.SIZE_LABELS for w in (" WBot", " other")]
    g = S.counts(recs, labels, lambda r: r["size"] + (" WBot" if r["bettor"] == HERO else " other"), FOLD)
    if "X" not in g:
        continue
    _, K, N = g["X"]
    point, draws, _ = S.boot_rates(K, N, rng)
    print("\n%s (%d tables with WBot)" % (scope, K.shape[0]))
    for j in range(0, len(labels), 2):
        d = draws[:, j] - draws[:, j + 1]
        dlo, dhi = S.ci(d)
        print("  %-8s vs WBot %2.0f%% n=%-5d vs others %2.0f%% n=%-5d diff %+3.0f [%+3.0f,%+3.0f]" % (
            P.SIZE_LABELS[j // 2], 100 * point[j], N[:, j].sum(), 100 * point[j + 1], N[:, j + 1].sum(),
            100 * (point[j] - point[j + 1]), 100 * dlo, 100 * dhi))
    sh = N[:, 0::2].sum(0) / N[:, 0::2].sum()
    print("  WBot's bet-size mix faced by these responders: " + ", ".join(
        "%s %.0f%%" % (l, 100 * x) for l, x in zip(P.SIZE_LABELS, sh)))
    # stratified: size bucket x street x HU/MW x IP/OOP cells; Mantel-Haenszel-weighted mean difference
    cell = lambda r: "%s|%s|%s|%s|%s" % (r["size"], r["street"], r["hu"], r["ip"], r["pfr"])
    cells = sorted({cell(r) for r in recs})
    labs = [c + w for c in cells for w in ("#W", "#O")]
    g = S.counts(recs, labs, lambda r: cell(r) + ("#W" if r["bettor"] == HERO else "#O"), FOLD)["X"]
    _, K, N = g
    Wt = S.weights(K.shape[0], S.B, rng)
    allw = np.vstack([np.ones((1, K.shape[0])), Wt])
    k, n = allw @ K, allw @ N
    kw, nw, ko, no = k[:, 0::2], n[:, 0::2], k[:, 1::2], n[:, 1::2]
    with np.errstate(invalid="ignore", divide="ignore"):
        wmh = nw * no / (nw + no)
        diff = np.nansum(wmh * (kw / nw - ko / no), axis=1) / np.nansum(np.where(nw * no > 0, wmh, 0), axis=1)
    dlo, dhi = S.ci(diff[1:])
    print("  stratified by size x street x HU/MW x IP/OOP x preflop-aggressor role (%d cells): vs WBot minus vs others %+.1f pts [%+.1f,%+.1f]"
          % (len(cells), 100 * diff[0], 100 * dlo, 100 * dhi))
    summary.setdefault("vs_wbot_stratified", {})[scope] = dict(diff=float(diff[0]), lo=float(dlo), hi=float(dhi),
                                                               cells=len(cells))

# ---------------------------------------------------------------- 6. stability across tables
print("\n== 6. Stability of each table-4 opponent's first-bet fold rate across its tables ==")
print("phi = Pearson chi2 / (tables-1) of per-table rates vs the pooled rate (1 = binomial noise only).")
print("phi_sim = 90th percentile of phi under binomial simulation with the same table counts.")
for nm in P.TABLE4 + P.STRONG:
    ts, K, N = G["all"][nm]
    k, n = K[:, 0], N[:, 0]
    p = k.sum() / n.sum()
    phi = np.sum((k - n * p) ** 2 / (n * p * (1 - p))) / (len(n) - 1)
    sims = [np.sum((x - n * p) ** 2 / (n * p * (1 - p))) / (len(n) - 1)
            for x in (rng.binomial(n.astype(int), p) for _ in range(2000))]
    rates = k / n
    print("  %-24s tables %2d  pooled %2.0f%%  per-table range %2.0f-%2.0f%%  phi %.2f (phi_sim90 %.2f)" % (
        nm, len(n), 100 * p, 100 * rates.min(), 100 * rates.max(), phi, np.percentile(sims, 90)))

# ---------------------------------------------------------------- 7. the bot's own pooled counter
print("\n== 7. The bot's pooled ftb counter (G_v7 / N_v10 _learn) replicated on the public histories ==")
print("Counts every postflop fold/call/raise while any bet is outstanding (bets AND raises, any bettor, any size).")
allk = sum(BOT[nm][t][0] for nm in field_names for t in BOT[nm])
alln = sum(BOT[nm][t][1] for nm in field_names for t in BOT[nm])
rates = np.array([BOT[nm][t][0] / BOT[nm][t][1] for nm in field_names for t in BOT[nm] if BOT[nm][t][1] >= 20])
print("  field pooled raw counter: %.3f (n=%d); per opponent-table (n>=20): median %.3f, 10-90%% %.3f-%.3f"
      % (allk / alln, alln, np.median(rates), np.percentile(rates, 10), np.percentile(rates, 90)))
print("  bot prior pri_ftb = 0.60 with weight 8; the continue multiplier is m = ftb / 0.60.")

with open(S.out_path("postflop_context_summary.json"), "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=1, ensure_ascii=False)
print("\nwrote data/postflop_context_summary.json")
