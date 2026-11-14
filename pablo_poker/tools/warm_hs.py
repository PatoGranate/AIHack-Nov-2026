"""Warm-start the clones' hand-strength quantile pools (data/hs_pool.json) by playing clone tables.

    python tools/warm_hs.py [tables] [hands]

Each spot's pool is the distribution of hand strength (equity vs random hands) that clones held there;
a clone acts on the quantile matching its measured frequency, so pools must be warm before benchmarks.
"""
import multiprocessing as mp
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def one(job):
    seed, hands = job
    from sim import arena, opponents
    import sim.fieldbot as fb
    from engine import FixedHandsTable
    opps = opponents.lineup(seed, 8, mix=fb.mix("recent", exclude=()))
    players = [arena.SeatPlayer(opponents.make(sp, seed * 31 + i), record=False, strategy_id="x") for i, sp in enumerate(opps)]
    FixedHandsTable(players, hands=hands, config={"betting": "no_limit", "raise_cap": 0}, seed=seed).play()
    return {k: v for k, v in fb._POOL.items()}


if __name__ == "__main__":
    T = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    H = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    import sim.fieldbot as fb
    for rnd in range(2):          # second pass acts on the first pass's pools
        merged = {}
        with mp.Pool(max(2, mp.cpu_count() - 1)) as pool:
            for d in pool.imap_unordered(one, [(700000 + rnd * 1000 + i, H) for i in range(T)]):
                for k, v in d.items():
                    merged.setdefault(k, []).extend(v)
        fb._POOL.clear()
        fb._POOL.update({k: v[-fb.POOL_N:] for k, v in merged.items()})
        fb.save_pool()
        print("pass %d: %d spots, %d values" % (rnd, len(merged), sum(len(v) for v in merged.values())), flush=True)
