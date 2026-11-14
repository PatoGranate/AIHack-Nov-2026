# Adversarial strategy status — 14 November 2026

## What exists
There is no separate adversarial bot or candidate in the current workspace. The closest work is v7's five switchable opponent-exploit ideas. The team’s `to_reviewer/20261114-143000_status_sidepots_quirks.md` and `20261114-143900_replies_and_quirk_results.md` document single-quirk A/B results against clone fields. v7 (`tools/cands/v7.py`) combines the three retained quirks with broader correctness and parameter changes; it is not a separately trained adversarial policy.

## Reported quirk A/B
Each row compares the same bot with one quirk on/off, 200 tables x 300 hands:

| Exploit | Real-clone | Held-out | Strong field | Team decision |
|---|---:|---:|---:|---|
| OOP check-raise trap | +9.3 | +10.3 | +5.3 | Keep |
| Tiny value bet | +4.4 | +6.7 | +11.7 | Keep |
| River overbet sizes | +3.2 | +4.9 | -1.3 | Keep, marginal |
| Late-position steal | -4.7 | +5.2 | -2.7 | Drop |
| Light 3-bet | -10.0 | -11.0 | -3.9 | Drop |

Values are reported in the team reply; no standard errors or confidence intervals are included there. These screens predate the blind-specific steal and opener-facing 3-bet fixes. The held-out population is still one ParamBot family, so these numbers do not establish transfer to actual external bots or the live tournament. Also, per-quirk gains do not prove the combined v7 bundle's gain (interactions can change it).

## Current read
The most credible adversarial components are the OOP check-raise trap and tiny value bets: both were positive across all three reported fields. River overbetting is not robust on the strong field. Late steals and light 3-bets should stay disabled unless fresh data reverses the negative results. There is no basis here to upload a standalone adversarial bot or replace G/I.

## What to require next
The final v7 gate in the reviewer exchange was still marked running; no later result is present in the current channel snapshot. I sent the team a request for the latest artifact and for paired results against G and I, actual external bot snapshots, a fresh held-out set, standard errors, exact source hash, and server runtime/failure counts. Keep any future adversarial policy isolated and compare on identical seeds/seats, with separate exploit-by-exploit and bundle results. A pool-adaptive or opponent-modeling policy must also be evaluated against varied responders rather than only ParamBot clones.

## Provenance
- `PokerBot/ExternalAnalysis/channel/to_reviewer/20261114-143000_status_sidepots_quirks.md`
- `PokerBot/ExternalAnalysis/channel/to_reviewer/20261114-143900_replies_and_quirk_results.md`
- `PokerBot/ExternalAnalysis/channel/to_reviewer/20261114-143339_frozen_candidate.md`