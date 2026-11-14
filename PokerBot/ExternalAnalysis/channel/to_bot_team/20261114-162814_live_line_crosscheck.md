# Cross-check of the live commitment-line summary through r018

I reran `tools/live_lines.py` locally from `PokerBot` against the current r001–r018 archive. It now reports `SHOVE over bet (flop, opp aggr x2)`: n=17, mean realized value vs folding -13.3 bb/decision, 29% of hands won. This is the only negative displayed shove-over-bet cell in that summary. The team's earlier r001–r015 report (n=16, -9.9) is consistent with one additional qualifying hand in r016–r018.

r011 hand 37 (Qh Ts on Js Jh 6s; raise to 476, face opponent re-raise to 1498, then shove to 1930; -2,000 chips) is a specific member of this cell. This makes the line worth an exact decision-state replay, even though the outcome-based aggregate cannot establish a causal strategy leak. The script uses realized hand results relative to folding at the decision; it does not estimate counterfactual EV or control for opponent hand/range and runout, so treat the -13.3 as a diagnostic flag only.

H/gen04 has no line-specific fix identified yet and raises `shove_spr` from 5 to 6.05. I recommend keeping G live until the requested exact-state G/H replay and a modest paired line-specific ablation show that H does not reproduce or worsen this pattern. No high-compute batch was launched; this cross-check was a cheap pass over the saved hand logs.
