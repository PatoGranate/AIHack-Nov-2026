"""Run the recursive self-improvement loop.

    python run_rsi.py --cycles 10                 # 10 cycles (~2-3 min each on 8 cores)
    python run_rsi.py --hours 6 --export          # overnight, then write the champion to bot.py
    python run_rsi.py --cycles 3 --quick          # small samples, for a smoke test

Every cycle: diagnose the champion -> propose one-parameter changes -> select
on fresh seeds -> pre-register the winner -> judge it once on a fresh holdout
and a different opponent pool -> the gate promotes or refuses. Promoted
champions' predecessors join the opponent league (self-play).
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from rsi import registry  # noqa: E402
from rsi.loop import DEFAULTS, research_loop  # noqa: E402
from storage import db as store  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", type=int, default=None)
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--quick", action="store_true", help="small samples (smoke test; the gate will mostly refuse)")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--candidates", type=int, default=DEFAULTS["candidates"])
    ap.add_argument("--holdout-tables", type=int, default=DEFAULTS["holdout_tables"])
    ap.add_argument("--betting", choices=["no_limit", "pot_limit", "fixed_limit"], default="no_limit")
    ap.add_argument("--raise-cap", type=int, default=0)
    ap.add_argument("--export", action="store_true", help="write the final champion to bot.py")
    ap.add_argument("--db", default=None)
    a = ap.parse_args()
    if a.cycles is None and a.hours is None:
        a.cycles = 5
    cfg = {"workers": a.workers, "candidates": a.candidates, "holdout_tables": a.holdout_tables,
           "table_config": {"betting": a.betting, "raise_cap": a.raise_cap}}
    if a.quick:
        cfg.update(selection_tables=16, selection_hands=200, holdout_tables=48, holdout_hands=200,
                   challenger_tables=16, challenger_hands=200, candidates=min(a.candidates, 3))
    db = store.connect(a.db)
    registry.ensure_champion(db)
    out = research_loop(db, cycles=a.cycles, hours=a.hours, cfg=cfg)
    promoted = [r for r in out if r.get("promoted")]
    champ = registry.champion(db)
    print("\n%d cycles, %d promotions. Champion: %s (generation %d)" % (len(out), len(promoted), champ["id"], champ["generation"]))
    if a.export:
        from export_bot import export
        print("wrote", export(db))


if __name__ == "__main__":
    main()
