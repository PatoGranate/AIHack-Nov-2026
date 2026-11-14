"""Quick head-to-head diagnosis: play the same seeds with different heroes and
print each hero's diagnosis from the database.

    python tools/compare.py --tables 32 --hands 500 --heroes default starter
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rsi.diagnose import diagnose, format_report  # noqa: E402
from sim import arena, opponents  # noqa: E402
from storage import db as store  # noqa: E402


def hero_spec(name):
    if name == "starter":
        return {"kind": "starter", "strategy_id": "starter"}
    if name.startswith("house:"):
        return {"kind": "house", "name": name[6:], "strategy_id": name}
    if name == "default":
        return {"kind": "strategy", "params": {}, "strategy_id": "default"}
    return {"kind": "arch", "name": name, "strategy_id": "arch:" + name}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", type=int, default=32)
    ap.add_argument("--hands", type=int, default=500)
    ap.add_argument("--heroes", nargs="+", default=["default", "starter"])
    ap.add_argument("--db", default=os.path.join(ROOT, "data", "compare.db"))
    ap.add_argument("--seed", type=int, default=1000)
    a = ap.parse_args()
    if os.path.exists(a.db):
        os.remove(a.db)
    db = store.connect(a.db)
    jobs = []
    bid = store.new_batch(db, "compare", a.tables * len(a.heroes), a.hands)
    for t in range(a.tables):
        seed = a.seed + t
        opps = opponents.lineup(seed, 7)
        for h in a.heroes:
            jobs.append(arena.make_job("c%d-%s" % (seed, h), bid, seed, a.hands, hero_spec(h), opps))
    arena.run_batch(jobs, db, progress=lambda i, n, r: print("\r%d/%d" % (i, n), end="", flush=True))
    store.finish_batch(db, bid)
    print()
    for h in a.heroes:
        print(format_report(diagnose(db, hero_spec(h)["strategy_id"])))
        print()


if __name__ == "__main__":
    main()
