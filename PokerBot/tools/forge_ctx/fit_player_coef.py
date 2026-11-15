"""FORGE: per-opponent fold-to-bet logistic for the 7 Sunday table-4 players, shrunk to the field model.

Feeds the t4ctx clone field (ctx_clone.py). Each player's coefficients are a MAP fit with a Gaussian
prior centred on the field coefficients (field_coef.json): penalty lam/2 * ||b - b_field||^2, lam
chosen per player by 5-fold CV (log-loss) over a small grid. Uses all Saturday rounds (this is a
generator for a test field, not a held-out claim). Features are exactly those of field_coef.json.

    python fit_player_coef.py --events events.csv --out t4ctx_coef.json      (needs numpy)
"""
import argparse
import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
# real-data name -> clone file stem (tools/opponents/sunday_v2/r_<stem>.py)
T4 = {"Resonance Qt": "ResonanceQt", "Anker Batteries": "AnkerBatteries",
      "Chinese people can fly": "Chinesepeoplecanfly", "GamesGone": "GamesGone", "Poke": "Poke",
      "Anton": "Anton", "YSL_TWIZZY": "YSLTWIZZY"}
LAMS = [2.0, 8.0, 32.0, 128.0, 512.0]


def features(r, cols, edges):
    sb = sum(1 for e in edges if float(r["size"]) >= e)
    v = {"const": 1.0, "raise": float(r["kind"] == "raise"), "mw": float(r["mw"]),
         "turn": float(r["street"] == "turn"), "river": float(r["street"] == "river"),
         "ip": float(r["ip"]), "allin": float(r["allin_call"]), "mw_ip": float(r["mw"]) * float(r["ip"])}
    for k in range(1, len(edges) + 1):
        v["sz%d" % k] = float(sb == k)
    return [v[c] for c in cols]


def fit(X, y, b0, lam, iters=50):
    b = b0.copy()
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b))
        g = X.T @ (p - y) + lam * (b - b0)
        H = (X * (p * (1 - p))[:, None]).T @ X + lam * np.eye(len(b))
        step = np.linalg.solve(H, g)
        b -= step
        if np.max(np.abs(step)) < 1e-9:
            break
    return b


def ll(X, y, b):
    p = np.clip(1 / (1 + np.exp(-X @ b)), 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "t4ctx_coef.json"))
    a = ap.parse_args()
    fc = json.load(open(os.path.join(HERE, "field_coef.json")))
    cols, edges = fc["columns"], fc["size_edges"]
    b0 = np.array(fc["coef"], dtype=float)
    rows = {n: [] for n in T4}
    for r in csv.DictReader(open(a.events, encoding="utf-8")):
        if r["name"] in rows:
            rows[r["name"]].append(r)
    out = {"columns": cols, "size_edges": edges, "field": fc["coef"], "players": {}}
    rng = np.random.default_rng(73999)
    for name, rs in rows.items():
        X = np.array([features(r, cols, edges) for r in rs])
        y = np.array([float(r["fold"]) for r in rs])
        fold_id = rng.integers(0, 5, len(y))
        cv = {}
        for lam in LAMS:
            cv[lam] = np.mean([ll(X[fold_id == k], y[fold_id == k], fit(X[fold_id != k], y[fold_id != k], b0, lam))
                               for k in range(5)])
        lam = min(cv, key=cv.get)
        b = fit(X, y, b0, lam)
        out["players"][T4[name]] = {"name": name, "n": int(len(y)), "fold_rate": round(float(y.mean()), 4),
                                    "lam": lam, "cv_logloss": {str(k): round(v, 5) for k, v in cv.items()},
                                    "field_logloss": round(ll(X, y, b0), 5), "fit_logloss": round(ll(X, y, b), 5),
                                    "coef": [round(float(x), 4) for x in b]}
        print("%-24s n=%5d fold=%.3f lam=%5.0f  ll field %.4f -> player %.4f" % (
            name, len(y), y.mean(), lam, ll(X, y, b0), ll(X, y, b)))
    json.dump(out, open(a.out, "w"), indent=1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
