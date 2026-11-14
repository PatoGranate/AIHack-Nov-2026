"""Launch 100+ practice tables in parallel and stream every hand into the
real-time database (data/poker.db). Open the dashboard to watch it live.

    python run_practice.py                         # 128 tables x 1,000 hands, champion vs the league
    python run_practice.py --tables 256 --hands 500
    python run_practice.py --strategy default      # play the untuned baseline instead
    python run_practice.py --betting pot_limit --raise-cap 3

Every table is a different seed and lineup drawn from the opponent pool
(house bots, starter-bot clones, archetypes and former champions).
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from rsi import registry  # noqa: E402
from rsi.diagnose import diagnose, format_report  # noqa: E402
from sim import arena, opponents  # noqa: E402
from storage import db as store  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tables", type=int, default=128)
    ap.add_argument("--hands", type=int, default=1000)
    ap.add_argument("--seats", type=int, default=8, help="7 or 8, like the tournament")
    ap.add_argument("--workers", type=int, default=None, help="processes (default: every core)")
    ap.add_argument("--strategy", default="champion", help="'champion', 'default' or a strategy id")
    ap.add_argument("--betting", choices=["no_limit", "pot_limit", "fixed_limit"], default="no_limit")
    ap.add_argument("--raise-cap", type=int, default=0)
    ap.add_argument("--iters", type=int, default=150, help="Monte Carlo trials per hero decision")
    ap.add_argument("--decisions", action="store_true", help="also log every hero decision (RL training data)")
    ap.add_argument("--explore", type=float, default=0.0, help="random-action rate for RL data coverage (practice only)")
    ap.add_argument("--db", default=None)
    a = ap.parse_args()

    db = store.connect(a.db)
    registry.ensure_champion(db)
    if a.strategy == "champion":
        strat = registry.champion(db)
    elif a.strategy == "default":
        cid = registry.strategy_id(dict(__import__("pokerbot.strategy", fromlist=["x"]).DEFAULT_PARAMS))
        strat = store.load_strategy(db, cid) or registry.champion(db)
    else:
        strat = store.load_strategy(db, a.strategy)
        if strat is None:
            sys.exit("unknown strategy id %s" % a.strategy)
    hero = registry.spec(strat)
    if a.explore:
        hero = dict(hero, params=dict(hero["params"], explore=a.explore), strategy_id=strat["id"] + "+explore")
    league = registry.league(db)
    bid = store.new_batch(db, "practice", a.tables, a.hands, "hero %s" % strat["id"])
    seeds = registry.fresh_seeds(db, a.tables)
    cfg = {"betting": a.betting, "raise_cap": a.raise_cap}
    jobs = [arena.make_job("practice-%d-b%d" % (s, bid), bid, s, a.hands, hero,
                           opponents.lineup(s, a.seats - 1, league=league), config=cfg, fixed_iters=a.iters,
                           decisions=a.decisions)
            for s in seeds]
    print("batch %d: %d tables x %d hands, hero %s (gen %d), %s workers -> %s" % (
        bid, a.tables, a.hands, strat["id"], strat["generation"], a.workers or os.cpu_count(), a.db or store.DEFAULT_PATH))
    t0 = time.time()
    total = [0, 0]

    def prog(i, n, r):
        if not r.get("error"):
            total[0] += r["hero_chips"]
            total[1] += r["hands"]
        bb100 = total[0] / 20 / max(1, total[1]) * 100
        rate = total[1] / max(1e-9, time.time() - t0)
        print("\r  %d/%d tables  %d hands  %.0f hands/s  hero %+.1f bb/100" % (i, n, total[1], rate, bb100), end="", flush=True)

    arena.run_batch(jobs, db, workers=a.workers, progress=prog)
    store.finish_batch(db, bid)
    print("\n\n" + format_report(diagnose(db, strat["id"], batch_ids=[bid])))
    print("\n%.1fs. Watch live next time with: python dashboard/server.py" % (time.time() - t0))


if __name__ == "__main__":
    main()
