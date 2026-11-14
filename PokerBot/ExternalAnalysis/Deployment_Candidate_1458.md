# Website candidate recommendation at 14:58 London, 14 Nov 2026

## Recommendation
Use **G / v7 frozen** as the current website candidate. Its exact SHA-256 is `b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a`. The team confirms `submissions/G_v7_final/bot.py` and `kit/bot.py` match this hash. This is the strongest current deployment choice by the team's field-weighted replacement tests; it is not proof that v7 is universally strongest against every field.

## Evidence inspected
- Archive-family replacement A/B (team reply `20261114-145000_archive_ab_results.md`): seed 5555, 96 x 1,000 hands per comparison; all-seat error check; v7-F +15.8 bb/100 (SE 5.6, z=2.81), v7-E +17.8 bb/100 (SE 5.7, z=3.10); no hero/opponent errors.
- Refit-clone A/B (team reply `20261114-145600_refit_results_frozen.md`): seed 6161, 200 x 300 hands; v7-F +42.3 (SE 5.4) on refit-real and +27.8 (SE 5.7) on heldout + a_trapper; v7-E +46.5 (SE 5.0) and +24.2 (SE 6.2); no errors. Opponent snapshot `tools/refit_results.opponents.sha256`, combined hash `9999bbe8...8bb4`.
- Competing update h_ftb35 (team deployment reply `20261114-145330_deployment_answer.md`) was rejected: against v7 it scored -0.7 (SE 4.4) in refit-real, -5.4 (SE 4.8) in heldout + a_trapper, and -2.4 (SE 6.0) vs archive A-F, seed 7272; no errors. Improved fold-probability Brier score did not translate to chips.
- Independent co-seated league pointed the other way on raw point estimates (E +30.08, F +27.60, v7 +16.04 bb/100), but its paired v7-minus-F and v7-minus-E confidence intervals crossed zero. It measured a different field composition and estimand; do not treat it as a clear loss or ignore its uncertainty.

## Deployment limit
The kit describes a single-file, stdlib-only upload contract and 10 s time bank. Team reports v7 is 54 KB, class `Agent`, single core, local worst decision around 2 ms with 0 timeouts, leaving a stated 3-5x margin; website upload/deployment itself is not verified here. Prior older builds had residual server-side timeouts, so inspect the first live-round timeout/error report before treating the deployment as certified.

## Audit caveat
The independent code review found no verified defect in v7 itself, but found real-opponent clone mismatches on external r016 hand893. Therefore refit-clone results are useful evidence but not a faithful full model of every real opponent. Keep v7 frozen as the candidate; improve clones separately and re-run held-out paired gates before changing it.

## Team response to independent code audit (received 14:54)
The team confirms these are opponent-clone fidelity issues, not a discovered v7 defect. It repaired the mojibake player name during ingestion and merged "matcha mille crêpes cake" as one identity (2,000 hands, no double weight), regenerated 27 opponents, and reports new combined clone hash `_common.py + real/*.py` `a04906eb...8fc8b`. Importantly, the cited v7 A/B runs used the previous clone hash `9999bbe8...8bb4`; results are correctly labelled to that version. The corrected clones have not yet produced new paired A/B results, so this does not change the current pick or validate it against the corrected field.
