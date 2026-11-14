# No-jam aggression candidate and c-bet audit

Recorded: 2026-11-14 18:56:57 +00:00

## Isolated candidate
A sandbox copy is at 	ools/cands/aggressive_nojam_i.py (SHA-256 F25C7B10877F7DABEC0BEC87B619F6D0FD6131D0C5B5747A74B0CF988205B06C). It starts from deployed v6 source kit/bot.py, widens BTN/CO/HJ open thresholds from .70/.45/.36 to .78/.51/.40, and removes the preflop all-in branch. Preflop raises are capped at least one big blind below the total stack; if that is illegal it calls/folds. Postflop behavior and runtime caps are otherwise unchanged. This is a sandbox hypothesis only; it is not uploaded or recommended for live play.

Please freeze I3's moving artifacts before any comparison. Then run the candidate against the exact frozen v6/I baseline with paired seeds and identical opponent manifests. Report non-jam invariant violations, runtime/fallback/errors, and held-out plus real-like performance separately. Scale the gate only if the pilot is directionally promising. Python cannot currently run in the reviewer environment (python.exe is inaccessible), so I have not simulated this candidate here.

## Flop continuation-bet audit
Using Saturday real hand histories r024-r046 (all version 6), I counted an opportunity when WBot was the **last preflop raiser**, could act on the flop, and no opponent had bet before it acted. WBot bet on 1,087/1,124 opportunities: **96.7%**. The sampled rounds range from 86.5% (r032, 45/52) to 100% in several rounds. This is near-always continuation betting, not literally 100% over the full sample.

Please break this down by heads-up/multiway, position, board texture, and bet size, and estimate realized/paired EV of c-bet versus check lines before lowering it globally. 	ools/analyze.py attributes the opportunity to the *first* preflop raiser rather than the last raiser; stats using that definition can diverge on 3-bet/4-bet pots. The actual action policy is in kit/bot.py postflop(): it compares simulated bet EVs with check EV and applies a negative et_margin bonus, so a very high rate may be coming from range/fold-equity assumptions plus that bonus.

## Fresh real-round data
Local files now reach r046. The version 6 r024-r046 window is 23,000 hands, +39,161 chips / +8.51 bb/100, 18 timeouts, no reported errors or bank-outs. r039-r046 include +95.4, -34.5, +36.4, -54.6, -28.6, -61.0, -99.3, +28.6 bb/100 respectively. This is volatile and should not be interpreted as a controlled strategy change. Keep v6 live pending stronger candidate evidence.