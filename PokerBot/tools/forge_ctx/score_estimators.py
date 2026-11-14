"""FORGE context model, step 2: online predictive test of fold-to-bet estimators on real rounds.

Every estimator predicts P(fold) for each response event in hand h using only hands < h of the
same table (the bot updates its stats in on_hand_end), keyed by seat (bots never see names).

Estimators
  N0     N/G's ftb: (folds + 0.6*8) / (faced + 8), one number per seat, no context.
  N0s    N0 passed through N's common size curve: 1 - (1 - N0) ** min(2.5, (size/0.6) ** 0.575).
  FIELD  static field model only: logistic on context (size bin, kind, HU/MW, street, IP vs bettor,
         all-in call) fitted on the TRAIN rounds. Same for every seat.
  A      FIELD + per-seat logit shift, shrunk to 0 with weight k1 (observed vs FIELD-expected folds).
  AF     A, with an in-round table-level shift (weight k0) that the per-seat shift is measured against.
  B:<s>  AF + per-seat deviation within split <s> (mw, size3, kind, street, ip), shrunk with weight k2.
Hierarchy = bucket -> seat -> in-round field -> static field model.

Split: rounds <= 27 train (field model fit + k grid), rounds >= 28 test. Paired per-table mean log-loss
differences vs N0, with table-bootstrap 95% intervals (2,000 resamples, seed 73001).

Usage: python score_estimators.py --events events.csv [--out results.txt] [--coef field_coef.json]
"""
import argparse
import json
import math

import numpy as np
import pandas as pd

SIZE_EDGES = [0.3, 0.45, 0.6, 0.8, 1.1]
TABLE4 = ["Resonance Qt", "Anker Batteries", "Chinese people can fly", "GamesGone", "Poke", "Anton",
          "YSL_TWIZZY"]
SPLITS = ["mw", "size3", "kind", "street", "ip"]


def size_bin(x):
    return int(np.searchsorted(SIZE_EDGES, x, side="right"))


def design(e):
    sb = e["size"].map(size_bin)
    cols = {"const": np.ones(len(e))}
    for b in range(1, len(SIZE_EDGES) + 1):
        cols["sz%d" % b] = (sb == b).astype(float)
    cols["raise"] = (e["kind"] == "raise").astype(float)
    cols["mw"] = e["mw"].astype(float)
    cols["turn"] = (e["street"] == "turn").astype(float)
    cols["river"] = (e["street"] == "river").astype(float)
    cols["ip"] = e["ip"].astype(float)
    cols["allin"] = e["allin_call"].astype(float)
    cols["mw_ip"] = cols["mw"] * cols["ip"]
    return pd.DataFrame(cols)


def fit_logit(X, y, l2=1e-3, iters=50):
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ w)))
        g = X.T @ (p - y) + l2 * w
        H = (X * (p * (1 - p))[:, None]).T @ X + l2 * np.eye(X.shape[1])
        step = np.linalg.solve(H, g)
        w -= step
        if np.max(np.abs(step)) < 1e-9:
            break
    return w


def lg(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def sg(x):
    return 1 / (1 + np.exp(-x))


def counters(e, pf):
    """Per event: seat/table/bucket counts and expected-fold sums from previous hands only."""
    e = e.copy()
    e["pf"] = pf
    e["size3"] = e["size"].map(lambda x: 0 if x < 0.45 else (1 if x < 0.8 else 2))
    out = {k: np.zeros(len(e)) for k in
           ["Fj", "Nj", "Ej", "Fa", "Na", "Ea"] + ["%s_%s" % (a, s) for s in SPLITS for a in "FNE"]}
    idx = 0
    for _, t in e.groupby("table", sort=False):
        seat = {}
        tab = [0.0, 0, 0.0]
        bkt = {}
        for _, hgrp in t.groupby("hand", sort=True):
            rows = hgrp.index.values
            for r in rows:
                s = e.at[r, "seat"]
                a = seat.get(s, [0.0, 0, 0.0])
                out["Fj"][r], out["Nj"][r], out["Ej"][r] = a
                out["Fa"][r], out["Na"][r], out["Ea"][r] = tab
                for sp in SPLITS:
                    b = bkt.get((s, sp, e.at[r, sp]), [0.0, 0, 0.0])
                    out["F_" + sp][r], out["N_" + sp][r], out["E_" + sp][r] = b
            for r in rows:
                s, y, p = e.at[r, "seat"], e.at[r, "fold"], e.at[r, "pf"]
                a = seat.setdefault(s, [0.0, 0, 0.0])
                a[0] += y; a[1] += 1; a[2] += p
                tab[0] += y; tab[1] += 1; tab[2] += p
                for sp in SPLITS:
                    b = bkt.setdefault((s, sp, e.at[r, sp]), [0.0, 0, 0.0])
                    b[0] += y; b[1] += 1; b[2] += p
            idx += len(rows)
    return pd.DataFrame(out, index=e.index)


def preds(C, pf, size, k0, k1, k2, split=None):
    lpf = lg(pf)
    # in-round table shift
    Ea = np.where(C.Na > 0, C.Ea / np.maximum(C.Na, 1), pf)
    df = lg((C.Fa + k0 * Ea) / (C.Na + k0)) - lg(Ea) if k0 is not None else 0.0
    # per-seat shift relative to (field model + table shift)
    Ej = np.where(C.Nj > 0, C.Ej / np.maximum(C.Nj, 1), pf)
    Ej = sg(lg(Ej) + df)
    dj = lg((C.Fj + k1 * Ej) / (C.Nj + k1)) - lg(Ej)
    out = lpf + df + dj
    if split is not None:
        Eb = np.where(C["N_" + split] > 0, C["E_" + split] / np.maximum(C["N_" + split], 1), pf)
        Eb = sg(lg(Eb) + df + dj)
        db = lg((C["F_" + split] + k2 * Eb) / (C["N_" + split] + k2)) - lg(Eb)
        out = out + db
    return sg(out)


def ll(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def paired(e, mask, loss_a, loss_b, rng, nboot=2000):
    """Mean over events of (a - b) and table-bootstrap 95% CI. Negative = a better than b."""
    d = pd.DataFrame({"t": e.loc[mask, "table"].values, "d": (loss_a - loss_b)[mask]})
    g = d.groupby("t").d.agg(["sum", "size"])
    s, n = g["sum"].values, g["size"].values
    est = s.sum() / n.sum()
    bs = []
    for _ in range(nboot):
        i = rng.integers(0, len(s), len(s))
        bs.append(s[i].sum() / n[i].sum())
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return est, lo, hi, int(n.sum()), len(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--coef", default=None, help="write the all-rounds field model here (for the bot)")
    args = ap.parse_args()
    e = pd.read_csv(args.events)
    y = e["fold"].values.astype(float)
    train = (e["round"] <= 27).values
    test = ~train
    X = design(e)
    w = fit_logit(X[train], y[train])
    pf = sg(X.values @ w)
    C = counters(e, pf)
    lines = []
    P = lambda *a: lines.append(" ".join(str(x) for x in a))

    # N0 and N0s
    n0 = (C.Fj + 0.6 * 8) / (C.Nj + 8)
    ex = np.minimum(2.5, (np.maximum(0.05, e["size"].values) / 0.6) ** 0.575)
    n0s = 1 - (1 - n0) ** ex
    base = {"N0": n0.values, "N0s": n0s.values, "FIELD": pf}

    # grid on TRAIN
    best = {}
    K0 = [None, 50, 200, 800]
    K1 = [5, 10, 20, 40, 80, 160]
    K2 = [10, 20, 40, 80, 160, 320]
    g_a = min(((ll(y, preds(C, pf, None, None, k1, None))[train].mean(), k1) for k1 in K1))
    best["A"] = (None, g_a[1], None)
    g_af = min(((ll(y, preds(C, pf, None, k0, k1, None))[train].mean(), k0, k1)
                for k0 in K0 if k0 is not None for k1 in K1))
    best["AF"] = (g_af[1], g_af[2], None)
    for sp in SPLITS:
        g = min(((ll(y, preds(C, pf, None, best["AF"][0], best["AF"][1], k2, sp))[train].mean(), k2)
                 for k2 in K2))
        best["B:" + sp] = (best["AF"][0], best["AF"][1], g[1])
    for name, (k0, k1, k2) in best.items():
        sp = name.split(":")[1] if name.startswith("B:") else None
        base[name] = preds(C, pf, None, k0, k1, k2, sp).values
    # What the candidate bot implements: field model at the 0.6-pot reference size (no all-in term)
    # + per-seat shift (A's k1), then N's own common size curve.  C0 = same without the seat shift.
    Xr = X.copy()
    for b in range(1, len(SIZE_EDGES) + 1):
        Xr["sz%d" % b] = 0.0
    Xr["sz2"], Xr["sz3"], Xr["allin"] = 0.5, 0.5, 0.0
    lref = Xr.values @ w
    Ej = np.where(C.Nj > 0, C.Ej / np.maximum(C.Nj, 1), pf)
    k1a = best["A"][1]
    dj = (lg((C.Fj + k1a * Ej) / (C.Nj + k1a)) - lg(Ej)).values
    base["C0"] = 1 - (1 - sg(lref)) ** ex
    base["C"] = 1 - (1 - sg(lref + dj)) ** ex
    P("events", len(e), "tables", e.table.nunique(), "train events", int(train.sum()), "test events", int(test.sum()))
    P("field model coef (train):", dict(zip(X.columns, np.round(w, 3))))
    P("chosen shrinkage (train):", {k: v for k, v in best.items()})
    rng = np.random.default_rng(73001)
    losses = {k: ll(y, v) for k, v in base.items()}
    subsets = {
        "test: all": test,
        "test: hands<250": test & (e["hand"].values < 250),
        "test: bettor=WBot": test & (e["bettor"].values == "WBot"),
        "test: responder in table 4": test & e["name"].isin(TABLE4).values,
        "test: table4 & hands<250": test & e["name"].isin(TABLE4).values & (e["hand"].values < 250),
    }
    for sname, m in subsets.items():
        P("")
        P("== %s  (n=%d)" % (sname, int(m.sum())))
        P("%-10s %8s %8s   %s" % ("est", "logloss", "brier", "dLL vs N0 [95% table-bootstrap]"))
        for k in base:
            brier = ((base[k] - y) ** 2)[m].mean()
            est, lo, hi, n, nt = paired(e, m, losses[k], losses["N0"], rng, nboot=1000)
            P("%-10s %8.4f %8.4f   %+.4f [%+.4f, %+.4f]  tables=%d" % (k, losses[k][m].mean(), brier, est, lo, hi, nt))
    # opponent-specific vs common context effect, per split: B:<s> vs AF
    P("")
    P("== opponent-specific context deviation (B:<split> minus AF), test: all / table4")
    for sp in SPLITS:
        for sname in ("test: all", "test: responder in table 4"):
            m = subsets[sname]
            est, lo, hi, n, nt = paired(e, m, losses["B:" + sp], losses["AF"], rng, nboot=1000)
            P("B:%-7s %-28s %+.5f [%+.5f, %+.5f]" % (sp, sname, est, lo, hi))
    P("")
    P("== candidate representation vs N's actual use (C minus N0s); C minus C0 = value of the per-seat shift")
    for sname, m in subsets.items():
        est, lo, hi, n, nt = paired(e, m, losses["C"], losses["N0s"], rng, nboot=1000)
        est2, lo2, hi2, _, _ = paired(e, m, losses["C"], losses["C0"], rng, nboot=1000)
        P("%-28s C-N0s %+.4f [%+.4f, %+.4f]   C-C0 %+.4f [%+.4f, %+.4f]" % (sname, est, lo, hi, est2, lo2, hi2))
    # calibration of chosen models by size bin on test
    P("")
    P("== calibration on test by bet-size bin (observed vs mean predicted)")
    sb = e["size"].map(size_bin).values
    for b in range(len(SIZE_EDGES) + 1):
        m = test & (sb == b)
        P("bin %d n=%6d obs=%.3f N0=%.3f N0s=%.3f AF=%.3f C=%.3f" % (
            b, m.sum(), y[m].mean(), base["N0"][m].mean(), base["N0s"][m].mean(), base["AF"][m].mean(),
            base["C"][m].mean()))
    P("")
    P("== calibration on test by HU/MW x IP (observed vs mean predicted)")
    for mw in (0, 1):
        for ip in (0, 1):
            m = test & (e["mw"].values == mw) & (e["ip"].values == ip)
            P("mw=%d ip=%d n=%6d obs=%.3f N0s=%.3f C=%.3f AF=%.3f" % (
                mw, ip, m.sum(), y[m].mean(), base["N0s"][m].mean(), base["C"][m].mean(), base["AF"][m].mean()))
    txt = "\n".join(lines)
    print(txt)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(txt + "\n")
    if args.coef:
        wall = fit_logit(X, y)
        json.dump({"columns": list(X.columns), "coef": [round(float(v), 4) for v in wall],
                   "size_edges": SIZE_EDGES, "k": {k: v for k, v in best.items()}}, open(args.coef, "w"), indent=1)


if __name__ == "__main__":
    main()
