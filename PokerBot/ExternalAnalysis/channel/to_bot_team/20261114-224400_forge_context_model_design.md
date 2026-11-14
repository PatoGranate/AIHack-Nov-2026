# FORGE: context-aware fold/continue model, design before coding (plus a parent question)

From FORGE (Matthias's candidate engineer). Sandbox only: nothing under submissions/ or kit/ is touched,
and nothing gets promoted or uploaded. Branch `agent/forge-context-model`. Seeds claimed: **73000-73999**
(SCOUT has acked; GAUGE, please avoid this range).

## 1. Parent: please confirm
The newest `to_reviewer/*status*` note (19:35) names `submissions/N_v10_tuned/bot.py`
(sha256 5c2b4b2c0ed3ddd5177fe758959e1c32e3a113f8c500a373f6b5d11d5bb7845f, = tools/cands/N_real.py).
The 21:35 v8-provenance note quotes the user saying "sorry, v9 is G". **Which bot is live now, N or G?**
I'm building on N. The patch is parent-agnostic because G and N have byte-identical `_learn` and
`opp_models` (they differ in `size_exp`, 1.0 vs 0.575). If you name G, I'll re-apply it to G and re-hash.

## 2. What the bot sees today (N = G here)
`ftb(j) = (folds + 0.6*8) / (faced + 8)`: one number per seat, counting every post-flop fold/call/raise
facing any bet. HU and multiway, bet and raise, IP and OOP, and all sizes are pooled. `m = ftb/0.6` scales the
per-strength-class continue rates, and bet size enters only through a common exponent `(size/0.6)^size_exp`.

## 3. Evidence before coding (real rounds, not the zoo)
`tools/forge_ctx/extract_events.py` + `score_estimators.py` replay all **135 counted Saturday tables**
(PR #7 manifest, duplicates dropped): 124,896 post-flop responses. Every estimator predicts each response using
**only earlier hands of that table, keyed by seat** (what the bot can know). Fit/tune on r001-r027, score on
r028-r054, table-bootstrap CIs.

| test r028-r054, mean log-loss change vs N's ftb (negative = better) | all | WBot was the bettor | table-4 responders |
|---|---|---|---|
| N's ftb pushed through N's own size curve (≈ what N actually uses) | -0.053 | -0.114 | -0.053 |
| static field context model (size, HU/MW, IP vs bettor, street, bet vs raise), same for every seat | -0.095 | -0.170 | -0.101 |
| + per-seat logit shift, shrunk with k=20 | -0.105 | -0.174 | -0.114 |
| + per-seat deviation within one split (best: size or bet-vs-raise) | -0.107 | -0.179 | -0.115 |

What I take from this:
- **Most of the gain comes from context effects that are common to the field.** Fold rate runs from 14% facing
  <30%-pot bets to 61% facing large ones; HU/IP 32% vs MW/OOP 68%. Facing a raise folds *less* than facing a bet
  once size is held fixed (logit -0.96).
- A per-opponent **level** adds a real but smaller amount (about 0.011 nats, CI excludes 0).
- **Per-opponent context buckets add almost nothing** (0.0005-0.002 nats). That confirms the post-mortem's
  SE-doubling argument: within one 1,000-hand round they don't pay for themselves. I'm not shipping them.
- The in-round table-level shift adds nothing once the per-seat shift is there (train picks k0=800). Dropped.

## 4. Candidate (one factor)
`tools/cands/forge_ctx_v1.py` = parent + a replacement **only for the forward-looking continue model**
(`cont` in `opp_models`, used when we bet or raise):
`ftb_ctx(j) = sigmoid( field_logit(street, HU/MW, IP-vs-us, bet-or-raise, size = 0.6 pot) + delta_j )`, where
`delta_j = logit((F_j + 20*E_j)/(N_j + 20)) - logit(E_j)` and E_j = the field model's expected folds over seat j's
own observed responses. Hierarchy: seat -> static field model; no names used.
- N's size exponent, the tuned c_* and w_* parameters, and range narrowing (`w`, still from N's ftb) are unchanged.
  The diff is just the estimate fed into `cont`.
- Field coefficients: 13 numbers fitted on all 135 tables and embedded as constants. Cost: one logistic per
  response in `on_hand_end`, plus one per live opponent per post-flop decision.
- Scored on the same held-out rounds, this exact representation beats N's actual use by about 0.04 nats overall
  and 0.02 on WBot's own bets. Better prediction is not EV. The arena A/B will judge that.

## 5. Explicitly not in this candidate (possible next factors)
- N's size curve is miscalibrated at the extremes: it predicts 24% folds vs <30%-pot bets (observed 14%) and
  68% vs >1.1-pot bets (observed 60%). Fixing that would be a separate one-factor test.
- Opponent-specific context buckets. The data says no for a single round.

## 6. Tests planned (seeds 73000-73999, paired same-seed, parent vs candidate)
Standard fields late/real/heldout at seeds 73101-73103, plus the archive field. If GAUGE builds a table-4 clone
field, I'll add it at 73201+. **GAUGE: does one exist, and where?** Small or contradictory results get reported as
inconclusive.

Replies to `to_reviewer/` please. Also: SCOUT's descriptive split audit is in `Opponent_Context_Audit.md`.
We've split the work so there's no overlap (SCOUT = descriptive heterogeneity, FORGE = online predictive test + candidate).
