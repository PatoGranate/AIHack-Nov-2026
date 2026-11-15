# Rook: Pablo v4 raise-response EV review (24653c9, pablo_poker/bot.py sha256 8458e3…)

This is a static review plus arithmetic fixtures (`rook_pablo_v4_ev_fixtures.py`, exit 1). No simulation was run.

**Arithmetic bug, heads-up `raised` term** (bot.py l.1263): `sh*(pot + 2*a2) - a2`.
- `pot` already includes the opponent's current bet (game.py l.314), but `2*a2` assumes the opponent adds as much as we do.
- When we raise over a bet (tc > 0), the opponent adds `a2 - tc`. The formula therefore overstates the pot by `tc`, inflating that branch's EV by `sh*tc`.
- Fixtures: A1–A2 (tc = 0) PASS; A3–A5 (tc = 100 / 60) FAIL by +100 / +50 / +60.
- Fix: `sh*(pot + 2*a2 - (bet_j - my_bet)) - a2`.
- Effect: raising looks slightly too good when we are strong.

**Model approximations** (no arithmetic error):
1. Heads-up, when the opponent's stack cap is ≤ our target, it can still "raise" (`r > 0`), and `a2` falls back to `add`, so the branch ignores the side pot.
2. Multiway, when we're strong, a raiser is treated as a plain caller, so the extra raise chips are ignored and EV is understated.
3. Multiway, when we're not strong, any raiser means we fold and lose `add`, whatever the order of action.
4. We never re-raise; the model only covers calling or folding to a single raise.

**Heads-up `called` term and multiway side pots:** contributions are capped by `min(cand, cap_j) - bet_j`, with `layered_win` used when caps bind. Correct on inspection; not fixtured.
