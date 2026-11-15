"""Robustness of the section 3 heterogeneity results to the null model (answers the PR #14 review; exploratory).

01/02 estimate each team's variance by a bootstrap over that team's own tables, but calibrate Q against a null whose
tables are plain binomial (no table-level overdispersion). Two checks:

A. Team-label permutation null. Shuffle team labels across the real opponent-table rows (each team keeps its number
   of rows), re-run the same bootstrap/Q pipeline, 300 times. Every null table keeps its observed overdispersion and
   table mix. Also reports a noise-corrected tau: tau_adj^2 = max(0, (Q - median null Q) / c), with c the
   DerSimonian-Laird weight sum, and the k* and one-round reliability that tau_adj implies.
   For effects the permutation null also equalises team levels, so the effect test on the probability scale can still
   pick up level-driven differences; the logit-scale column is the cleaner one there.
B. Within-hand clustering of the opponent-table units (01 section 3b). A seat can answer a first bet on the flop,
   turn and river of one hand. The binomial variance treats those as independent. Here the variance is the
   hand-cluster (ratio-estimator) variance instead, and the unit tau is recomputed with it.

Rows and definitions mirror 01 section 3 / 3b and 02 section 3; per-team point estimates are checked against the
committed JSON summaries. Writes data/out_05_null_robustness.txt and data/null_robustness_summary.json.
"""
import json
import sys

import numpy as np

import oc_parse as P
import oc_stats as S

sys.stdout = S.Tee(S.out_path("out_05_null_robustness.txt"))
rng = np.random.default_rng(S.SEED + 6)

tables = P.load_tables()
post, pre, _bot = P.extract(tables)
FOLD = lambda r: r["action"] == "fold"
HERO = P.HERO
hero_tables = {ti for ti, (_, _, d) in enumerate(tables) if HERO in d["players"]}
fb = [r for r in post if r["facing"] == "bet" and r["first"]]
print("Null-model robustness of the heterogeneity results (exploratory)")
print("python %s, numpy %s; seed %d; %d permutations x %d bootstrap draws per row"
      % (sys.version.split()[0], np.__version__, S.SEED + 6, S.SIM, S.SIM_B))
print("inputs: %d unique counted tables (manifest + SHA256 checked by oc_parse)" % len(tables))

# ---- postflop families (as in 01)
SIZE2 = ["S<50%", "L>=50%"]
s2 = lambda r: SIZE2[0] if r["size_x"] < 0.5 else SIZE2[1]
FAM = {
    "all": (["all"], lambda r: "all", fb),
    "humw": (["HU", "MW"], lambda r: "HU" if r["hu"] else "MW", fb),
    "size2": (SIZE2, s2, fb),
    "humw_size2": (["HU S", "HU L", "MW S", "MW L"], lambda r: ("HU " if r["hu"] else "MW ") + s2(r)[0], fb),
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
POST_SPECS = [
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
# ---- preflop families (as in 02)
vo = [r for r in pre if r["kind"] == "vs_open" and not r["limped"]]
o3 = [r for r in pre if r["kind"] == "open_vs_3bet"]
LATE = ("CO", "BTN", "SB")
PFAM = {
    "role": (["blind vs late open", "blind vs early open", "cold (non-blind)"],
             lambda r: ("blind vs late open" if r["opener_pos"] in LATE else "blind vs early open")
             if r["pos"] in ("SB", "BB") else "cold (non-blind)", vo),
    "bb_late_size": (["<=3.0bb", ">=3.1bb"],
                     lambda r: (("<=3.0bb" if r["open_bb"] < 3.05 else ">=3.1bb")
                                if (r["pos"] == "BB" and r["cold"] == 0 and r["opener_pos"] in LATE) else None), vo),
    "callers": (["no caller yet", "1+ caller"], lambda r: "no caller yet" if r["cold"] == 0 else "1+ caller", vo),
    "vs_wbot": (["open by WBot", "open by others"],
                lambda r: None if r["name"] == HERO else ("open by WBot" if r["opener"] == HERO else "open by others"), vo),
    "o3": (["opener IP", "opener OOP"], lambda r: "opener IP" if r["ip"] else "opener OOP", o3),
}
PRE_SPECS = [("level: blind vs late open", "role", 0, None), ("level: blind vs early open", "role", 1, None),
             ("level: cold (non-blind)", "role", 2, None), ("level: opener vs 3-bet", "o3", 0, None),
             ("effect: blind early - late opener", "role", 1, 0),
             ("effect: BB >=3.1bb - <=3.0bb (late)", "bb_late_size", 1, 0),
             ("effect: 1+ caller - none", "callers", 1, 0), ("effect: opener OOP - IP", "o3", 1, 0),
             ("effect: WBot open - others", "vs_wbot", 0, 1)]


def field(fams):
    g = {f: S.counts(recs, labels, key, FOLD) for f, (labels, key, recs) in fams.items()}
    return {f: {nm: x for nm, x in g[f].items() if nm != HERO} for f in g}


def round_se2(groups, a):
    """Logit-scale binomial variance of one round's estimate in bucket a, at field median count and field rate (= 01)."""
    Ns = np.concatenate([x[2][:, a] for x in groups.values()])
    k = sum(x[1][:, a].sum() for x in groups.values())
    p = k / Ns.sum()
    return 1.0 / (max(1.0, float(np.median(Ns))) * p * (1 - p))


def run(title, fams, specs, committed, with_rel):
    fg = field(fams)
    print("\n== A. %s: binomial null (01/02) vs team-label permutation null ==" % title)
    print("Q/null = observed Q / median null Q. tau_adj = noise-corrected tau. pts; logit in brackets.")
    print("%-36s %3s %7s %6s %6s %6s %9s %9s %13s %13s %5s %5s %5s" % (
        "quantity", "k", "Q", "Qnull", "p_bin", "p_perm", "pL_bin", "pL_perm", "tau [logit]", "tau_adj [lg]",
        "k*", "k*adj", "rel1a" if with_rel else ""))
    out = {}
    for label, fam, a, b in specs:
        h = S.heterogeneity(fg[fam], a, b, rng=rng, null="perm")
        c0 = committed[label]
        if "per_team" in c0:  # deterministic point estimates must match the committed run exactly
            ref = {n: v[0] for n, v in c0["per_team"].items()}
            assert sorted(ref) == sorted(h["names"]), label
            assert all(abs(ref[n] - float(y)) < 1e-12 for n, y in zip(h["names"], h["y"])), label
        assert h["k"] == c0["k"], label
        t2a = max(0.0, (h["q"] - h["q_null_med"]) / h["c"])
        t2la = max(0.0, (h["q_logit"] - h["q_null_med_logit"]) / h["c_logit"])
        ks = (h["mean"] * (1 - h["mean"]) / h["tau"] ** 2) if (b is None and h["tau"] > 0) else None
        ksa = (h["mean"] * (1 - h["mean"]) / t2a) if (b is None and t2a > 0) else None
        rel1a = None
        if with_rel:
            se2 = round_se2(fg[fam], a) + (0.0 if b is None else round_se2(fg[fam], b))
            rel1a = t2la / (t2la + se2)
        out[label] = dict(k=h["k"], q=h["q"], q_null_median_perm=h["q_null_med"], p_bin=c0["p_sim"],
                          p_perm=h["p_sim"], p_bin_logit=c0["p_sim_logit"], p_perm_logit=h["p_sim_logit"],
                          tau=h["tau"], tau_adj=float(np.sqrt(t2a)), tau_logit=h["tau_logit"],
                          tau_logit_adj=float(np.sqrt(t2la)), kstar=ks, kstar_adj=ksa,
                          rel_one_round=c0.get("rel_one_round"), rel_one_round_adj=rel1a)
        f = lambda x: "-" if x is None else "%.0f" % x
        print("%-36s %3d %7.0f %6.0f %6.3f %6.3f %9.3f %9.3f %5.1f [%4.2f] %5.1f [%4.2f] %5s %5s %5s" % (
            label, h["k"], h["q"], h["q_null_med"], c0["p_sim"], h["p_sim"], c0["p_sim_logit"], h["p_sim_logit"],
            100 * h["tau"], h["tau_logit"], 100 * np.sqrt(t2a), np.sqrt(t2la), f(ks), f(ksa),
            "" if rel1a is None else "%.2f" % rel1a))
    return out


def load(name):
    with open(S.out_path(name), encoding="utf-8") as fh:
        return json.load(fh)


postj, prej = load("postflop_context_summary.json"), load("preflop_context_summary.json")
summary = {"postflop": run("postflop", FAM, POST_SPECS, postj["heterogeneity"], True),
           "preflop": run("preflop", PFAM, PRE_SPECS, prej["heterogeneity"], False)}

# ---------------------------------------------------------------- B. within-hand clustering of unit variances
print("\n== B. Opponent-table units (01 section 3b): binomial vs hand-cluster variance ==")
print("deff = pooled hand-cluster variance / pooled binomial variance over units. tau_bin reproduces 3b (binomial,")
print("same floor); tau_clu uses the hand-cluster variance with the same floor. Units: >=10 decisions.")
print("%-30s %5s %6s %7s %7s %7s %6s %6s" % ("bucket", "units", "deff", "tau_bin", "tau_clu", "within", "k*bin", "k*clu"))
UNIT = [("all first-bet", "all", 0), ("HU", "humw", 0), ("MW", "humw", 1), ("HU S<50%", "humw_size2", 0),
        ("HU L>=50%", "humw_size2", 1), ("MW S<50%", "humw_size2", 2), ("MW L>=50%", "humw_size2", 3),
        ("flop", "street", 0), ("turn", "street", 1), ("river", "street", 2), ("IP", "ip", 0),
        ("OOP", "ip", 1), ("facing raise", "facing", 1), ("vs WBot's bets", "bettor", 0),
        ("vs others' bets (WBot tables)", "bettor", 1)]
committed_unit = postj["opponent_table_heterogeneity"]
unit_out = {}
for label, fam, a in UNIT:
    labels, key, recs = FAM[fam]
    cells = {}
    for r in recs:
        if r["name"] == HERO or key(r) != labels[a]:
            continue
        u = cells.setdefault((r["name"], r["t"]), {})
        kh = u.setdefault(r["hand"], [0, 0])
        kh[0] += FOLD(r)
        kh[1] += 1
    k, n, vc, team = [], [], [], []
    names = sorted({nm for nm, _ in cells})
    for (nm, t), hands in sorted(cells.items()):
        arr = np.array(list(hands.values()), float)
        nn = arr[:, 1].sum()
        if nn < 10:
            continue
        y = arr[:, 0].sum() / nn
        k.append(arr[:, 0].sum())
        n.append(nn)
        vc.append(np.sum((arr[:, 0] - y * arr[:, 1]) ** 2) / nn ** 2 * len(arr) / max(1, len(arr) - 1))
        team.append(names.index(nm))
    k, n, vc, team = np.array(k), np.array(n), np.array(vc), np.array(team)
    p = k.sum() / n.sum()
    y = k / n
    floor = p * (1 - p) * 0.25 / n
    vb = np.maximum(y * (1 - y) / n, floor)
    vcl = np.maximum(vc, floor)
    deff = float(np.sum(np.maximum(vc, 0)) / np.sum(y * (1 - y) / n))
    t2b, _, _ = S.dl_tau2(y, vb)
    t2c, _, _ = S.dl_tau2(y, vcl)
    # within-team component with cluster variances (same moment estimator as unit_tau)
    pt = np.array([k[team == g].sum() / n[team == g].sum() for g in team])
    w = 1 / vcl
    teams = np.unique(team)
    q_w = float(np.sum(w * (y - pt) ** 2))
    c_w = sum(np.sum(w[team == g]) - np.sum(w[team == g] ** 2) / np.sum(w[team == g]) for g in teams)
    t2w = max(0.0, (q_w - (len(y) - len(teams))) / c_w)
    ref = committed_unit[label]
    assert len(k) == ref["units"] and abs(np.sqrt(t2b) - ref["tau"]) < 1e-9, label
    unit_out[label] = dict(units=len(k), deff=deff, tau_bin=float(np.sqrt(t2b)), tau_cluster=float(np.sqrt(t2c)),
                           tau_within_cluster=float(np.sqrt(t2w)),
                           kstar_bin=float(p * (1 - p) / t2b) if t2b > 0 else None,
                           kstar_cluster=float(p * (1 - p) / t2c) if t2c > 0 else None)
    print("%-30s %5d %6.2f %7.1f %7.1f %7.1f %6s %6s" % (
        label, len(k), deff, 100 * np.sqrt(t2b), 100 * np.sqrt(t2c), 100 * np.sqrt(t2w),
        "-" if t2b <= 0 else "%.0f" % (p * (1 - p) / t2b), "-" if t2c <= 0 else "%.0f" % (p * (1 - p) / t2c)))
summary["opponent_table_units"] = unit_out

with open(S.out_path("null_robustness_summary.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(summary, fh, indent=1, ensure_ascii=False)
print("\nwrote data/null_robustness_summary.json")
