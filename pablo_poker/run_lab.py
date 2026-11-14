"""Start the autonomous lab: it researches, tests and promotes on its own.

    python run_lab.py                                   # run until data/STOP exists (or Ctrl+C)
    python run_lab.py --hours 8
    python run_lab.py --quick --iterations 6            # small samples, smoke test
    python run_lab.py --listen 0.0.0.0:50555 --key SECRET   # also accept teammates' laptops as workers

On a teammate's laptop (same commit of this repo):
    python worker.py --connect YOUR_IP:50555 --key SECRET

Watch it: python dashboard/server.py  ->  http://localhost:8765
Stop it:  create the file data/STOP (it finishes the current task first).

What it does each iteration (rsi/lab.py): fetch real hands and rebuild the
field clones, stress-test the champion against extreme strategies, probe the
field with extreme heroes, test literature ideas from research/ideas.json,
run RSI cycles, refresh practice data, and export + timing-check bot.py after
every promotion.
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from rsi import registry  # noqa: E402
from rsi.lab import QUICK, Lab  # noqa: E402
from sim.cluster import get_cluster  # noqa: E402
from storage import db as store  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--iterations", type=int, default=None)
    ap.add_argument("--quick", action="store_true", help="small samples (smoke test)")
    ap.add_argument("--workers", type=int, default=None, help="local worker processes (default: every core)")
    ap.add_argument("--slots", type=int, default=16, help="tables each worker keeps in play at once")
    ap.add_argument("--listen", default=None, help="host:port to accept remote workers, e.g. 0.0.0.0:50555")
    ap.add_argument("--key", default=None, help="shared secret for remote workers")
    ap.add_argument("--betting", choices=["no_limit", "pot_limit", "fixed_limit"], default="no_limit")
    ap.add_argument("--raise-cap", type=int, default=0)
    ap.add_argument("--db", default=None)
    a = ap.parse_args()

    db = store.connect(a.db)
    registry.ensure_champion(db)
    cluster = get_cluster(a.db or store.DEFAULT_PATH, a.workers, a.slots, a.listen, a.key)
    print("cluster: %d local workers x %d tables in flight%s" % (
        len(cluster.procs), a.slots, ", listening on %s:%d for remote workers" % cluster.address if a.listen else ""))
    cfg = {"workers": a.workers, "table_config": {"betting": a.betting, "raise_cap": a.raise_cap}}
    if a.quick:
        cfg.update(QUICK)
    lab = Lab(db, cfg)
    if a.quick:
        lab.sizes = dict(stress=(8, 200), probe=(12, 200), practice=(64, 200))
    try:
        lab.run(hours=a.hours, max_iterations=a.iterations)
    except KeyboardInterrupt:
        print("\n[lab] interrupted")


if __name__ == "__main__":
    main()
