# Adversarial strategy candidate: status and evidence request

Our independent review found no standalone adversarial bot/source or benchmark result in the current workspace. The documented work appears to be the five quirk/exploit switches listed in `to_reviewer/20261114-143000_status_sidepots_quirks.md` (late steals, light 3-bets vs overfolders, river overbets, tiny value bets, OOP check-raise traps). The later `to_reviewer/20261114-143900_replies_and_quirk_results.md` may have relevant numbers; please clarify the latest status and point us to the authoritative artifacts.

Please report for each quirk/combined candidate:
- paired chip EV or bb/100 against G and I, with standard errors/confidence intervals and seeds/table counts;
- performance on real external bots and held-out tables, separated from clone/jitter fields;
- whether opponents were allowed to adapt/respond, and whether the candidate is a best response to a fixed pool or a robust adversarial policy;
- runtime/timeout/error and bank-out results under the actual server limits;
- exact source path, hash, and a reproducible command/result artifact.

Recommendation pending evidence: keep adversarial strategies isolated as a candidate; do not promote to live based on exploit ablations or clone-only results. Use the same seeds/seats for paired comparisons, then fresh seeds and actual external bot snapshots. Compare versus G and I and evaluate the candidate across a diverse pool to avoid overfitting to our own agents.