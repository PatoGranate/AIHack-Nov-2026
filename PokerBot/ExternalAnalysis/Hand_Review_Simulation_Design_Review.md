# Interactive Hand Review / What-if Simulator: independent design review

Date: 2026-11-14 15:02 London
Reviewed: `tools/review/hand_review.html`, `tools/review/build_review_data.py`, `tools/review/data.json`.

## Assessment
The Hand Review Room is a useful first deliverable: it has hand/bot/version views, filters, a step-by-step table replay, curated hands, and a simulation-results panel. From its code, it is a replay and analysis browser, not yet a what-if simulator. The current hand curation selects largest outcomes first, so a large loss can look like a mistake even when it is ordinary variance or a correct decision. The page should keep that distinction visible.

## Changes to prioritize before showing this as a mistake finder

1. **Protect decision-time information.** `hand_review.html:306` renders `h.ho[s]` for every seat at every replay step. The bundled histories have private cards for many players, so the replay exposes cards that were not public when the decision occurred. Default to showing only the hero's own cards and cards publicly revealed by the current step. Add a clearly marked `Reveal all cards (post-mortem)` toggle. Keep future board cards hidden until their board event. This is necessary if the user is meant to reason about what the bot could know.

2. **Separate result from decision quality.** `build_review_data.py:374-381` selects the bottom 8 and top 5 outcomes per version, then supplements them by outcome magnitude. Label these as `largest losses/wins` or `review examples`, not `worst mistakes`. Current tags at lines 331-337 infer `called down`, `top pair`, `bluff caught`, and `cooler` from simplified showdown/action heuristics; they can overclaim (a final river call is not necessarily a call-down, and a losing made hand is not by itself a cooler). Use neutral factual tags until a hand evaluator and line-aware review supports stronger labels.

3. **Show the bot's reason only when it was recorded or re-run.** Existing hand histories show actions and outcomes, not the v7 decision's internal estimates. Add a structured decision trace for future/replay runs: legal actions, chosen action and mixed-strategy probability, estimated equity/value per action, pot odds, bet size, opponent-model evidence/sample count, random seed, and exact bot hash. Mark old hands `reason unavailable`; do not invent a post-hoc explanation from the final result.

4. **Make “what if?” an estimate, not a hindsight result.** For each focal decision, replay legal alternatives from the exact decision state. Report expected chip value/regret using many paired future-board/opponent-range samples, with sample count and uncertainty. Keep the one realized alternate-line outcome in a separate field and label it `this hand's realized counterfactual`; it is not expected value. Avoid future-card leakage into the decision inputs.

5. **Fix the preflop opponent advice.** `build_review_data.py:159,185-187,285` pools preflop actions after any raise into one `fold to raise` rate, then may recommend `3-bet light against its opens`. This conflates cold defence vs an open with opener defence vs a 3-bet. The external-hand audit shows why it matters: Durahim folds 517/589 (87.8%) facing an open but only 14/63 (22.2%) as the opener facing a 3-bet. Split these contexts, display numerator/denominator and confidence interval, shrink small samples, and suppress recommendations when exposure is small.

## Make it useful to the player at a glance

- Open on **Biggest decision leaks**, grouped by recurring decision pattern and sorted by estimated EV loss (only when estimates exist). Show `hand count`, `estimated bb lost per opportunity`, total exposure, uncertainty, street/position, and whether evidence is observed, replayed, or modeled.
- Keep **Largest pots won/lost** as a separate result-only view, so variance and mistakes are not conflated.
- Add filters for WBot version/ref (use the team's rNvM version labels), position, street, pot size, action faced, multiway/heads-up, and opponent. Show the sample size after every filter.
- In version/bot comparisons, show each round/table and paired A/B differences with CI, hands, seeds, candidate hash, and opponent snapshot hash. A raw bb/100 rank across unlike table fields is not a trustworthy strength ranking.
- Change the source label `External (kaiserbot tables)` at `hand_review.html:167,286` to `Other-table hands`; data files contain multiple named bots/tables, not just kaiserbot.
- Include an `Evidence & limits` panel: data coverage/as-of timestamp, curated-hand selection rule, missing versions, small samples, and the fact that no online v7 result exists until actual round data arrives. Separate live results from simulated results.

## Acceptance checks for the next version

1. A replay fixture proves opponent holes remain hidden before the public reveal and no future board card appears early; the omniscient toggle is explicit.
2. The report uses `largest loss` for result ranking and only uses `mistake`/`regret` when based on a documented action-value comparison.
3. At a known decision, the counterfactual display names legal actions and provides paired sample count, assumptions, expected-value interval, and actual realized outcome separately.
4. The external profile for Durahim displays the two different preflop contexts above rather than one generic fold rate.
5. Every win-rate/skill comparison has source, version/hash, matchup, sample size, and uncertainty; otherwise label it descriptive only.
6. Strict UTF-8 validation passes for the HTML, JSON payload, and generated reports. `build_review_data.py` currently loads with `errors="replace"`; do not let that silently mask bad source bytes. A separate current clone audit still finds invalid UTF-8 in regenerated accented-name clone artifacts and `weights.txt`, so resolve that before relying on browser-generated downloads or text parsing.

The current candidate remains G/v7. The app should help the developer diagnose and test changes; it should not promote a candidate from a visually dramatic hand or a small set of curated examples.
