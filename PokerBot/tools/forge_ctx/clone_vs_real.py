"""FORGE: do the arena's table-4 clones reproduce real table-4 fold-to-bet by context?

Compares fold rates by opponent and by context (HU/MW, IP vs bettor, size, bet vs raise, street)
between real Saturday responses (events.csv from extract_events.py) and arena hand logs dumped by
arena_t4.py --dump.  Usage: python clone_vs_real.py --events events.csv --dump DIR
"""
import argparse
import glob
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_events as X  # noqa: E402

NAMES = {"Resonance Qt": "ResonanceQt", "Anker Batteries": "AnkerBatteries", "Chinese people can fly":
         "Chinesepeoplecanfly", "GamesGone": "GamesGone", "Poke": "Poke", "Anton": "Anton", "YSL_TWIZZY": "YSLTWIZZY"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--dump", required=True)
    a = ap.parse_args()
    rows = []
    for p in glob.glob(os.path.join(a.dump, "*.json")):
        rows += X.table_events(p)
    c = pd.DataFrame(rows)
    c = c[c.name != "HERO"].copy()
    c["name"] = c.name.str.replace(r"^r_|_j\d$", "", regex=True)
    r = pd.read_csv(a.events)
    r = r[r.name.isin(NAMES)].copy()
    r["name"] = r.name.map(NAMES)
    for df in (r, c):
        df["sz"] = pd.cut(df["size"], [0, .45, .8, 99], labels=["<.45", ".45-.8", ">.8"])
    tab = lambda df, by: df.groupby(by, observed=True).fold.agg(["mean", "size"]).round(3)
    print("real = Saturday responses by the 7 table-4 teams (all tables); clone = arena dump (%d tables)"
          % len(glob.glob(os.path.join(a.dump, "*.json"))))
    for by in ["name", "mw", "ip", "sz", "kind", "street", ["mw", "ip"]]:
        t = tab(r, by).join(tab(c, by), lsuffix="_real", rsuffix="_clone")
        print(t.to_string())
        print()


if __name__ == "__main__":
    main()
