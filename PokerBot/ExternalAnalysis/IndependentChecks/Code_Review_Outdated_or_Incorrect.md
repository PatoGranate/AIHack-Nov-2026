CODE REVIEW: OUTDATED / INCORRECT POKERBOT MODEL CODE
Date: 2026-11-14
Scope: current v7 candidate and generated real-opponent clones, checked against validated external-hand reports and deterministic clone replay. No playing code modified.

PRIORITY 1 — REAL OPPONENT CLONES MISS OBSERVED DECISIONS (HIGH CONFIDENCE)
Evidence:
- tools/opponents/_common.py:44-98 ranks hands with a hand-made categorical heuristic. It only recognizes hole-card pairs/trips and does not score the best five-card hand against the board. A board pair with an ace kicker can therefore be categorized as “nothing”; board texture, kicker quality, range, pot odds, and prior line are not used in the call threshold.
- tools/opponents/_common.py:157-177 applies one coarse made-hand category threshold, with a single size adjustment only when to_call/pot > 0.6.
- tools/opponents/real/r_Gherkers.py:8 sets call_min=2 and trap_min=2; it does not call with category 1.
- tools/opponents/real/r_LehmanBrothers.py:8 has call_min=2, no station or air_call override.
- IndependentChecks/external_clone_replay_results.json records exact replay mismatches in external r016 hand893: real Gherkers calls 127 on flop Jc2s9h holding 6c6d; clone folds. Real Lehman calls 1554 on river Jc2s9h9d7c holding Ac3h; clone folds. In the latter, best hand is board pair of nines with ace kicker; the hole cards do not make a private pair.
Impact: Current “real” opponent field can misstate the exact postflop behaviors that determine whether v7’s value bets and bluffs get paid. Tuning against VPIP/PFR alone does not cover this error. This weakens claims based on clone-field results and could select the wrong value/bluff frequencies.
Suggested change: Replace the categorical postflop response rule with a calibrated response model conditioned on made-hand/equity bucket, kicker/board texture, street, bet-to-pot size, position, multiway status, and observed action line; derive hand strength via the shared evaluator or equity, not the board-relative category shortcut. Keep opponent-specific behavior and uncertainty/shrinkage so two replay examples do not become global loose calls.
Validation: Add deterministic unit fixtures for both recorded r016 h893 decisions; report action agreement across all complete-history decision points, stratified by street/size/hand class. Then compare old/new clones and frozen v7 on fresh seed blocks, including held-out tables, checking the v7-minus-baseline paired interval and all-seat errors. Do not treat replay agreement or cloning fidelity itself as proof of higher win rate.

PRIORITY 2 — INCOMPLETE CLONE REPRESENTATION OF RIVER ACTIONS (HIGH CONFIDENCE)
Evidence:
- tools/opponents/_common.py:157-160 short-circuits all non-river actions to check/call for trapper hands; its river action is a randomized all-in/call rule. This omits river size selection and line-dependent bluff/value frequencies.
- ExternalAnalysis/IndependentChecks/External_Bot_Hand_Evidence.txt and ExternalOpponents/Structural_Findings.txt describe Gherkers shoving 60/77 observed river bets, but include both successful thin-value examples and losing overplays. The current generic trapper rule does not represent that broad river-shove pattern (and must not turn it into a universal shove).
Impact: The clone field may not expose v7 to realistic large river bets or size-specific calls. This can bias postflop EV estimates and field-weighted A/B selection.
Suggested change: Fit separate opponent-conditioned river bet/raise size and call/fold curves from complete visible action sequences. Retain weak/strong and line context; test a broad-shove responder and a size-insensitive caller as separate structural archetypes, never a single global loosened policy.
Validation: Replay every river decision against clone predictions; publish per-player/size confusion tables and held-out likelihood/calibration. Then run paired win-rate tests against the revised structural field.

PRIORITY 3 — POSSIBLE DUPLICATE OPPONENT IDENTITY CAUSED BY TEXT ENCODING (MEDIUM CONFIDENCE; CONFIRM BEFORE CHANGING)
Evidence:
- tools/opponents/real/weights.txt includes both r_matchamillecrêpescake.py (line 9) and r_matchamillecrÃªpescake.py (line 28).
- The corresponding files describe the same visible display name with UTF-8 interpreted incorrectly in the second filename/comment; their fitted parameters differ (e.g. open .158 vs .131, call .153 vs .112).
Impact: If these entries represent the same player, they create two independently weighted candidate clones for one identity, potentially over-weighting that opponent family and fragmenting its sample. They could instead represent distinct source histories, so do not merge without tracing the source table/round provenance.
Suggested change: Normalize player names consistently at ingestion (Unicode NFC plus explicit decoding repair where justified), deduplicate exact identity/history records, and preserve genuinely distinct versioned policies using round/version IDs rather than mojibake spellings.
Validation: Trace each clone to source files and hand counts, establish whether histories overlap or reflect distinct versions, then verify the generated weights sum to the intended per-player exposure and that no duplicate/overlap enters train and held-out sets.

CURRENT CANDIDATE
- tools/cands/v7.py is the frozen candidate represented in existing league records (SHA-256 b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a). This review found evidence against clone fidelity, not a proven defect in v7’s own action code and not a finding that v7 loses to the tournament field.
- No concrete v7 simulation math defect is asserted from this review. The approximate equity/continuation calculation at tools/cands/v7.py:716-947 remains a candidate for separately instrumented validation, especially multiway and side-pot cases.

RECOMMENDED TEAM ACTION
1. Fix/validate opponent-model fidelity first, with the existing r016 h893 deterministic fixtures.
2. Preserve the already frozen candidate and compare paired against it on fresh, held-out seeds after any clone changes.
3. Resolve the accented-name duplicate by tracing provenance, not by blind merge.
