# Rook: independent static review of PR #9 (FORGE context model), head `026ed132f8ef728711cc629842d7c5ca1bd2de91`

Assignment: `channel/to_bot_team/20261114-230254_monitor_pr9_audit_assignment.md`. Branch `agent/rook-pr9-review`, cut at the PR head.

- **Static review**, plus one bounded rerun of the author's learning-replay check.
- **Not done:** the author's arena battery and the developer's ftb 8→4 / A-vs-A work.
- **Not changed:** no bot, submission or author file.

## Artifact identity (git blob sha256, LF, at the PR head)

| Artifact | sha256 |
|---|---|
| Candidate `tools/cands/forge_ctx_v1.py` | `7bed0d20b1226c9595ba329f5f63118491b1eaca2afc3ff08fa6e466b02aae2b` (CRLF working copy `a6b222d1…81d3`) |
| Parent `submissions/N_v10_tuned/bot.py` | `77ec8ca9006dc1f8638d9430209cd6ef9e404e7e9b2fd161df4e3a862955b6ee` (CRLF `5c2b4b2c…845f`) |
| Frozen G `submissions/G_v7_final/bot.py` | `1ee577f0e4fed6aef7fef55d1c6f2684e5f3a2a8ce777983bb9ace9ba55ffe12` (CRLF `b8a22e4b…0c16a`) |
| `tools/forge_ctx/arena_t4.py` | `e13457b36eef74350791e0d02994092afbb86caad3165c74576ddea638582b3e` |
| `tools/forge_ctx/check_candidate.py` | `799fef37a3bd1e88a4decb200a0e2ce464337cadc1e26acc40ee5a2748b34492` |
| `tools/forge_ctx/clone_vs_real.py` | `60e706c02e6da6527a524a18fe1460174021776102fce9402aa8076f66100861` |
| `tools/forge_ctx/extract_events.py` | `d7e30dd2c4c4b853ce146ab549ba118e8e4f8b1ddf92989042348dfb195f3e98` |
| `tools/forge_ctx/score_estimators.py` | `c7d3067de00f2e06e9bc6af60ad1655676155f95fbc2c315f08ec3d57cc446fd` |
| `tools/forge_ctx/run_gate.sh` | `ce1fd66c18b6a3ac61d8ffb4d3fc5de4980520b88503972793a49644320b3382` |
| `tools/forge_ctx/field_coef.json` | `b731271d53a41971d7d915ed5f07e9716ac99602068f54c9d3df0912cf34f269` |
| `tools/forge_ctx/results_predictive.txt` | `3d0b29a787996b7fad87378020b1b98bc261000fbeb23c2c3473a50130532c0e` |
| `ExternalAnalysis/Context_Model_Design.md` | `1676e2a86d92d42575e52b8022f3fb5eaabb35041797151390b0aef2fc83e7e4` |

- Inputs: PR #7 `f7fbac4` Hand_data and manifest (my PR #7 validation confirmed 159/159 hashes).
- `events.csv` (author-reported `dec356ad…85b6`) is not committed, so I did not verify it.

## Gates

| # | Gate | Verdict | Evidence |
|---|---|---|---|
| 1 | Exact lineage | **PASS** as stated. **FAIL vs the frozen-G mandate** | The candidate is N plus a patch: 122 added lines and 1 changed. It inherits N's tuned parameters and N's 6 ms / 14 ms / 7 s timing (`max_ms` 6.0 at line 204, `hard_ms` 14.0, `bank` 7.0). Any arena result is "N+ctx vs N", **not a G gain**. |
| 1a | Is the patch portable to G? | **PASS** (verified) | `_learn`, `opp_models`, `on_hand_end` and `simulate` are byte-identical in G and N; AST source segments hash the same. Applying the 8 diff hunks to `G_v7_final` gives a clean isolated "G+ctx" port, but that file needs its own hash and its own test. **Required before any G-iteration claim.** |
| 2 | Diff scope matches the description | **PASS** | The `diff` hunks are the docstring and `import math` (l.10–18), the `CTX_*` constants and `_sig`/`_logit` (l.315–338), the `Stats` slots (l.341), the `on_hand_end` hook (l.392–395), `_learn_ctx` and `ftb_ctx` (l.483–554), and the `opp_models` set-up and `cont` replacement (l.782–787, l.825–832). Nothing else. |
| 3 | Observation and persistence | **PASS** | Learning runs only in `on_hand_end → _learn_ctx` over the completed hand's public `history`. Stats are keyed by seat inside the per-round Agent (kit: state lasts one round). There is no cross-round memory and no names. |
| 4 | Hidden-information leakage | **PASS** | `_learn_ctx` reads seat, street, action and amount only, never hole cards or `shown`. At decision time `ftb_ctx` uses public state plus statistics from earlier hands only. |
| 5 | Feature correctness: learning vs decision consistency | **PASS** | **"Facing a raise":** at learning time `naggr > 1` (the kit logs a bet as `raise`); at decision time `to_call > 0` (our action is a raise). **Position:** at learning time `(s - sbs) % n > (aggr - sbs) % n`; at decision time `(j - btn - 1) % nf > order_me`. Both mean "responder acts after the bettor" in postflop order. **Bet size:** taken before `contrib` is updated, so it is relative to the pot before the bet. **All-in:** `to_call >= start - contrib[s]`. **Accounting:** call adds the call amount and raise sets the street total, matching the kit's semantics. |
| 5a | Replay consistency (rerun) | **PASS** | `check_candidate.py` on r030 and r041 reproduces the extractor's per-seat (xf, xn, xe) exactly, max \|xe diff\| 0.0. This checks the bot against the author's own extractor; it is consistency, not independent ground truth. |
| 6 | Predictive split validity | **PASS**, with caveats | Train on r001–027, test on r028–054. Predictions use only earlier hands of the same table. Intervals are from a table bootstrap. Caveats: (a) the same teams appear in train and test, so this is a temporal split, not new opponents; (b) the **shipped** `CTX_*` constants equal `field_coef.json` refitted on **all** rounds, so they were never evaluated out of sample, although the method was; (c) the target is fold prediction for *all* bettors' bets, not EV for ours. The WBot-bettor subset is 27 tables of mixed G/I/N. |
| 7 | Mechanism compared with G/I/N | **NOTE** | G, I and N all use one pooled per-seat `ftb` (Beta prior 0.6, weight 8). The candidate replaces only the forward `cont` with a field logistic (street, HU/MW, IP, raise) plus a shrunk per-seat logit shift (k = 20). `w` range narrowing and the size curve are unchanged. The ftb prior weight is the developer's ftb 8→4 experiment; these two **interact**: the parent's pooled `ftb` still feeds `w`. Keep the experiments separate, and test their combination separately. |
| 8 | Runtime and fallback risk | **PASS** (static), **PENDING** (measured) | Per hand: O(history) plus one `exp` per response. Per decision: a few float operations per live opponent. Every new path is wrapped in `try/except: pass` and falls back to the parent's `cont`. **Minor:** that fallback is silent, with no counter, so a systematic exception would disable the factor unnoticed. Add a counter. There is no measured timing or server-bank evidence yet (design doc §6 is a placeholder). |
| 9 | Benchmark reproducibility | **PENDING** | Arena results are a placeholder (§5). `arena_t4.py` pairs seed, seating and cards like `tools/arena.py`. Its pairing has **not** been validated by a seeded A-vs-A equality test, and the hero and clone Monte Carlo are wall-clock-limited (the same issue as the parked river pilot). `events.csv` is not committed. |
| 10 | Evidence of improvement | **PENDING** | The prediction gain is real and its CI excludes 0 (C − N0s −0.041 nats overall). Prediction is not EV. The author says the arena clones cannot reproduce the context effects (clone folds depend only on strength and a 0.6-pot step), so a positive arena result needs untouched paired seeds **on a G+ctx port**, compared at matched budget with frozen I and N. |

## Ranked findings
1. **(Blocking for G iteration)** The parent is N, not frozen G. Port the 8 hunks to `G_v7_final` as a separate candidate with its own hash, and test that. Do not read N+ctx results as G gains.
2. **(Blocking for evidence)** The arena pairing is unvalidated: no seeded A-vs-A run, and wall-clock-limited Monte Carlo. Run A-vs-A (diff must be ≡ 0) before reading any paired result.
3. **(Design)** The shipped constants include the test rounds. That is fine for deployment, but state that the out-of-sample number belongs to the train-only refit.
4. **(Robustness)** The `try/except` fallback is silent. Add a counter to the candidate, and report it in the arena output.
5. **(Interaction)** Pooled `ftb` still drives `w`. The developer's prior-weight change (8→4) changes `w` but not `cont`, so the two factors overlap only partly. Allocate them as separate one-factor variants.
6. **(Minor)** `ctx_mw` at decision time counts all-in opponents, who cannot fold, as live. Learning time counts any non-folded player. That is consistent, but it slightly overstates multiway pressure.

## Questions for the author (posted on PR #9)
1. Will you supply a G-parented port (`forge_ctx_g1.py`, hash and diff against `G_v7_final`)?
2. Does `arena_t4.py` pass seeded A-vs-A equality (same file in both seats, diff ≡ 0)? If not, will you seed the hero and clone Monte Carlo per decision?
3. Will you commit `events.csv`, or its generator invocation with a hash check, so the predictive numbers can be rerun without pandas drift?
4. Will you add a fallback or exception counter to the candidate and report it?
