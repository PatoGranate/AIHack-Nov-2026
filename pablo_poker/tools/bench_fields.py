"""Paired benchmark of v2-engine parameter sets on simulated fields (same seeds, seats and cards per pair).

    python tools/bench_fields.py VARIANTS.json [tables] [hands]

VARIANTS.json: {"name": {param overrides}, ...}; the first entry is the reference.
Fields: "field" = data-driven clones of every real bot (sim/fieldbot.py), "old" = teammates' real code + legacy clones.
The simulated fields are softer than the real one, so read this as a regression check, not a forecast.
"""
import json
import multiprocessing as mp
import os
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def one(job):
    field, seed, name, params, hands = job
    from sim import arena, opponents
    if field == "field":
        from sim.fieldbot import mix as fbmix
        mix = fbmix("recent")
    else:
        from rsi.field import _equity_clone_mix
        mix = [(6, s) for s in opponents.real_bot_specs()] + _equity_clone_mix()
    opps = opponents.lineup(seed, 7, mix=mix)
    hs = seed % 8
    specs = list(opps)
    specs.insert(hs, {"kind": "v2", "params": dict(params, max_sims=400, max_ms=500.0, hard_ms=2000.0, bank_s=1e9)})
    players = []
    for i, spec in enumerate(specs):
        agent = opponents.make(spec, seed * 31 + i * 1009 + 7, fixed_iters=64 if i == hs else 40)
        players.append(arena.SeatPlayer(agent, record=False, strategy_id="x"))
    from engine import FixedHandsTable
    res = FixedHandsTable(players, hands=hands, config={"betting": "no_limit", "raise_cap": 0}, seed=seed).play()
    return field, seed, name, res["chips"][hs] / 20.0 / hands * 100


if __name__ == "__main__":
    variants = json.load(open(sys.argv[1]))
    T = int(sys.argv[2]) if len(sys.argv) > 2 else 48
    H = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    fields = os.environ.get("FIELDS", "field,old").split(",")
    seed0 = int(os.environ.get("SEED0", 880000))
    jobs = [(f, seed0 + fi * 10000 + s, n, p, H) for fi, f in enumerate(fields) for s in range(T) for n, p in variants.items()]
    out = {}
    with mp.Pool(max(2, mp.cpu_count() - 1)) as pool:
        for f, seed, n, bb in pool.imap_unordered(one, jobs):
            out.setdefault((f, seed), {})[n] = bb
    names = list(variants)
    for f in fields:
        rows = [v for (ff, _), v in out.items() if ff == f and len(v) == len(names)]
        print("\n%s field: %d paired tables x %d hands" % (f, len(rows), H))
        for n in names:
            x = [r[n] for r in rows]
            d = [r[n] - r[names[0]] for r in rows]
            print("   %-22s %+7.1f bb/100   vs %s: %+6.1f (se %.1f)" % (n, st.mean(x), names[0], st.mean(d),
                                                                       st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else 0))
