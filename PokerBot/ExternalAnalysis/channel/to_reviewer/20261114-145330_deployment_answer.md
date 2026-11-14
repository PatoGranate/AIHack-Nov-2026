# Re: 20261114-145200_deployment_candidate_status.md (answer before 14:58)

1. YES: G/v7 (sha256 b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a,
   submissions/G_v7_final/bot.py == kit/bot.py) remains the intended website submission.
   No newer version has passed a gate. The only newer candidate, h_ftb35 (pri_ftb .6 -> .35,
   chosen because the new fold-calibration tool shows v7 under-predicts folds vs clones:
   pred .339 vs obs .470, n=2194, Brier .230 -> .213 for h_ftb35), did NOT beat v7:
     h_ftb35 - v7: real -0.7 (se 4.4), heldout(+a_trapper) -5.4 (se 4.8),
     archive(A-F, 64 x 1000 hands) -2.4 (se 6.0); seed 7272; no hero/opponent errors.
     Opponent snapshot = tools/refit_results.opponents.sha256 (combined 9999bbe8...8bb4).
   Rejected; calibration vs clones did not convert into chips.
2. Constraints not represented: server is a single sealed Python 3.12 core; earlier live
   rounds showed ~2x our local think time and residual timeouts (1-8 per round on older
   builds) from causes we can't reproduce locally (IPC/scheduling). v7's local worst
   decision is ~2 ms with a 3 ms hard stop, 0 timeouts in all subprocess runs, so margin
   is ~3-5x. Packaging: single file, stdlib only (gc, random, time), 54 KB, class Agent.
   Deployment state on the website is the user's action; we can't verify it.
3. No result changes the recommendation. Rollback order if live rounds go badly: F, then E.
