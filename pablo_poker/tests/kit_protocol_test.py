# Run from PokerBot/kit after: cp ../../pablo_poker/bot.py v4.py; cp v4.py v4b.py
"""Short-handed protocol test of v4 through the official engine and subprocess runner.
Checks timeouts/errors/bank-outs and chip conservation (sum of results == 0)."""
import sys
from engine.game import FixedHandsTable
from engine.players import SubprocessPlayer
cases = [("heads-up v4 vs v4", ["v4.py", "v4b.py"], {"betting": "no_limit", "raise_cap": 0}),
         ("heads-up v4 vs TAG", ["v4.py", "examples/tight_aggressive.py"], {"betting": "no_limit", "raise_cap": 0}),
         ("heads-up v4 vs station, pot limit", ["v4.py", "examples/calling_station.py"], {"betting": "pot_limit", "raise_cap": 0}),
         ("3-handed fixed limit cap 3", ["v4.py", "v4b.py", "examples/random_bot.py"], {"betting": "fixed_limit", "raise_cap": 3})]
for name, seats, cfg in cases:
    ps = [SubprocessPlayer(p, timeout_ms=25.0, bank_ms=10000) for p in seats]
    try:
        res = FixedHandsTable(ps, hands=300, config=cfg, seed=7).play()
    finally:
        for p in ps:
            p.close()
    st = [(p.stats.timeouts, p.stats.errors, p.stats.bank_out, round(p.stats.total_ms / 1000, 2)) for p in ps]
    print("%-36s chips %s sum %d | v4 (timeouts, errors, bank_out, think s) %s" % (name, res["chips"], sum(res["chips"]), st[0]))
    for p in ps:
        if p.stats.error_samples:
            print("   first error:", p.stats.error_samples[0][:300])
