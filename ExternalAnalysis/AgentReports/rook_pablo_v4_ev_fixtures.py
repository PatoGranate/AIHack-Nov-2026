"""Rook: arithmetic fixtures for Pablo v4 (24653c9, pablo_poker/bot.py sha 8458e3) heads-up raise-response EV.
Replicates bot.py l.1256-1264 'raised' term vs exact chip accounting. pot = sum(contrib) incl. current bets
(engine/game.py l.314). No MC. Exit 1 if any arithmetic case fails."""
import sys
def bot_raised(sh, pot, add, a2):            # bot.py l.1263
    return sh * (pot + 2 * a2) - a2
def exact_raised(sh, pot, my_bet, bet_j, a2):
    # we end at my_bet+a2; opponent raised to that total, adding (my_bet+a2-bet_j); pot already holds bet_j
    return sh * (pot + a2 + (my_bet + a2 - bet_j)) - a2
cases = [  # name, sh, pot, my_bet, bet_j, add, a2
    ("A1 HU bet, checked to us (tc=0)", 1.0, 200, 0, 0, 100, 350),
    ("A2 HU bet, we lose showdown", 0.0, 200, 0, 0, 100, 350),
    ("A3 HU raise over a 100 bet (tc=100)", 1.0, 300, 0, 100, 300, 750),
    ("A4 HU raise, split pot", 0.5, 300, 0, 100, 300, 750),
    ("A5 HU raise over 100 after our 40 lead (tc=60)", 1.0, 340, 40, 100, 260, 700),
]
bad = 0
for nm, sh, pot, mb, bj, add, a2 in cases:
    b, e = bot_raised(sh, pot, add, a2), exact_raised(sh, pot, mb, bj, a2)
    ok = abs(b - e) < 1e-9; bad += not ok
    print("%-46s bot %8.1f exact %8.1f diff %+7.1f %s" % (nm, b, e, b - e, "PASS" if ok else "FAIL"))
sys.exit(1 if bad else 0)
