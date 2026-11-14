"""Exact side-pot cases for layered_win (from the external review)."""
import sys, importlib.util
sp = importlib.util.spec_from_file_location("b", sys.argv[1]); b = importlib.util.module_from_spec(sp); sp.loader.exec_module(b)
W = b.layered_win
# everyone had 200 in. Hero & B add 500, A only 100 (all-in). A > hero > B.
parts = [(700, 50), (300, 90), (700, 10)]  # hero, A, B
got = W(parts, 0, [])
# main pot 3*300=900 -> A; side pot 2*400=800 -> hero
assert got == 800, got
# hero best: wins everything
assert W([(700, 99), (300, 90), (700, 10)], 0, []) == 1700
# tie hero/B in side pot, A wins main
assert W([(700, 50), (300, 90), (700, 50)], 0, []) == 400
# dead money 60 from folders goes into main pot
assert W([(700, 50), (300, 90), (700, 10)], 0, [30, 30]) == 800
assert W([(700, 99), (300, 90), (700, 10)], 0, [30, 30]) == 1760
# hero overbets a single short caller: excess refunded to hero
assert W([(1000, 10), (300, 90)], 0, []) == 700
# plain heads-up equal stacks, split
assert W([(500, 7), (500, 7)], 0, [40]) == 520
print("side-pot cases OK")
