# FORGE results: context-aware fold model. Two sandbox candidates, real-round evidence, arena inconclusive but positive-leaning

Re: my `20261114-224400_forge_context_model_design.md` and SCOUT's `20261114-231106_scout_interim_context_findings.md`.
Full write-up: `ExternalAnalysis/Context_Model_Design.md`. PR #9 (branch `agent/forge-context-model`). Nothing promoted,
uploaded or merged.

**Parent question still open.** I built on `submissions/N_v10_tuned/bot.py`, sha256 5c2b4b2c… (CRLF) /
77ec8ca9… (LF), as the 19:35 status note names. If "v9 is G" means G is live, say so and I'll re-apply the
same diff to G. `_learn` and `opp_models` are byte-identical in the two.

## Candidates
| file | sha256 CRLF / LF | change |
|---|---|---|
| `tools/cands/forge_ctx_v1.py` | a6b222d1… / 7bed0d20… | vs parent: the forward-looking `cont` uses `ftb_ctx` = field logistic (street, HU/MW, IP vs us, bet vs raise, at 0.6 pot) + per-seat logit shift (k = 20). Range narrowing, size curve and all tuned params are unchanged. |
| `tools/cands/forge_ctx_v2.py` | 506b3ffd… / e81e20ab… | vs v1: adds a "bettor is us" term (logit -0.32), adopted from SCOUT item 4 |

## Real-round evidence (online, earlier hands only, by seat; test r028-r054; 95% table-bootstrap)
Mean log-loss vs what the parent effectively uses (pooled ftb through its size curve):
- v1 representation: -0.041 [-0.046, -0.037] all; -0.021 [-0.033, -0.011] on WBot's own bets; -0.044 table-4 responders.
- v2 representation: -0.046 all; **-0.047 [-0.058, -0.038] on WBot's own bets**; -0.050 table-4 responders.
- Calibration on WBot's bets: observed 26.4% fold. Parent 35.3%, v2 32.2%. The rest is the parent's size curve at small sizes.

## Arena (paired same-seed, seeds 73101-73402, no errors)
- v1 vs parent: late +1.2 (2.3), real +1.8 (2.5), heldout +4.4 (2.5), archive +4.1 (5.5), **table-4 clones
  t4real +3.9 (3.0), t4heldout +1.3 (3.0)**. All six positive, none conclusive (max z 1.79). The pooled
  +2.5 ± 1.1 is descriptive only, because the fields share clone families.
- v2 vs v1: -0.9, +0.2, -3.3, +2.8, +0.6, +1.6 (se 2.4-5.0). Inconclusive, about 0 pooled, as expected.
- Table-4 field: no GAUGE field existed, so `tools/forge_ctx/arena_t4.py` seats exactly the 7 table-4
  clones (real fits or heldout j0/j1), shuffled per table.
- **The arena is a weak instrument for this factor.** The clones don't reproduce the real context effects:
  multiway 45% vs 65% real, facing a raise 31% vs 50%, bets over 0.8 pot 43% vs 59%, turn 17% vs 38%, Poke
  41% vs 55%. Clone fold logic depends only on hand strength. They also can't show the fold-less-to-WBot
  effect. See `tools/forge_ctx/clone_vs_real_t4real.txt`.

## Runtime
+3.8 µs per post-flop decision and +12.7 µs per hand, measured directly. About +15 ms per round. Fuzz: 0 errors
(v1 and v2). End-to-end latency tails were machine jitter shared by both bots, since another session was
running. This is not a server or IPC certification.

## What I adopted or rejected from teammates
- Post-mortem section 7, shrinkage over raw buckets: **adopted**, and confirmed on held-out data.
  Per-opponent context buckets add only 0.0005-0.002 nats, so the hierarchy stops at seat level (seat -> field).
  Street and position enter only as common terms.
- SCOUT item 2, k* ≈ 19: **agrees** with my train-chosen k = 20; kept.
- SCOUT item 3, a facing-a-raise split: real but small in my harness (-0.0019 at table 4) and it only bites
  when we raise. **Not adopted** for now.
- SCOUT item 4, fold-less-to-WBot: **adopted** as v2. It roughly doubles the gain on our own bets. A per-seat
  hero shift on top adds only -0.002, so it was rejected.
- SCOUT item 5, don't re-centre `pri_ftb` alone: **respected**. Neither candidate touches `pri_ftb` or `c_*`.
  The v2 hero term does lower the input level on our bets. Clone-tuned `c_*` can't already contain that
  effect, but its EV impact is untested.

## Suggested next one-factor tests (not done)
1. Replace the parent's size curve with the fitted size bins. Biggest remaining calibration gap: it predicts
   24% folds against bets under 30% pot, 14% observed, and 66% of WBot's bets are small.
2. Whoever owns gating: if either candidate is considered, judge it on live or shadow rounds. The clone arena
   can't reproduce the effects it models.
