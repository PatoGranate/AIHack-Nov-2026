# H single-round live test: recommendation and request

The reviewer checked the current gate and live archive. Recommendation: H is promising enough for one clearly labeled live round if the user chooses to test it, but not proven enough to call it the new best bot. G/v7 remains the live baseline until an upload is explicitly chosen by the user.

Evidence:
- G/v7 played r001–r015; mean +30.59 bb/100 overall and +71.87 over r011–r015. Recent r014/r015 were +160.91/+63.94, but five rounds are a noisy estimate.
- H is identical to gen04, SHA-256 `08ae3fef8a34c27454c4562505f06ba3d6fd5e513e7546aa04692d2971b6b639`; there are no H real rounds.
- H−G paired results: late +9.0 (SE 4.1), held-out +7.0 (SE 3.8), real clones +7.3 (SE 3.9), archive +1.9 (SE 5.8), emulated-slow +6.5 (SE 4.6). Fuzz 8/8; two-round smoke test only. Promising direction, but the archive and slow-server results are inconclusive.

If the user elects to test H, please confirm the exact upload artifact/version label and expected round boundary, and preserve G for immediate rollback. Do not change the live upload on the user's behalf. Report the resulting site version, timeouts/errors/bank-outs, and hand archive path. A single round is useful for runtime and field behavior, but cannot settle the win-rate comparison.
