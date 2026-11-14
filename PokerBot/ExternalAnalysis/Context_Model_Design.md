# Context-aware fold/continue model (FORGE): design, evidence, candidate

Branch `agent/forge-context-model`. Sandbox only: `submissions/`, `kit/bot.py` and production packages
are untouched, and nothing has been promoted, uploaded or merged.

## 1. Identity

| | path | sha256 (working copy, CRLF, as the team quotes) | sha256 (git blob, LF) |
|---|---|---|---|
| parent | `submissions/N_v10_tuned/bot.py` (= `tools/cands/N_real.py`) | `5c2b4b2c0ed3ddd5177fe758959e1c32e3a113f8c500a373f6b5d11d5bb7845f` | `77ec8ca9006dc1f8638d9430209cd6ef9e404e7e9b2fd161df4e3a862955b6ee` |
| candidate | `tools/cands/forge_ctx_v1.py` | `a6b222d15212aed0ee9ae80fadec2679cad2bb38432f9e8aaed1b9bf51d381d3` | `7bed0d20b1226c9595ba329f5f63118491b1eaca2afc3ff08fa6e466b02aae2b` |

**Parent choice.** The newest `to_reviewer/*status*` note (19:35) names `N_v10_tuned`. The later 21:35
provenance note quotes the user saying "sorry, v9 is G". I asked the bot team to confirm in
`to_bot_team/20261114-224400_forge_context_model_design.md`, and no reply had arrived when this was written.
The patch doesn't depend on the parent: G and N have byte-identical `_learn` and `opp_models`. If G is
named, the same diff applies, but it needs re-hashing and re-testing.

Candidate: 59,246 bytes, stdlib only (adds `import math`), class `Agent` unchanged.

## 2. What the parent does

`Stats` keeps one post-flop fold-to-bet count per seat: `ftb = (folds + 0.6*8)/(faced + 8)` over every
fold/call/raise that faced any post-flop bet. Heads-up and multiway, bet and raise, in and out of position, all
streets and all sizes are pooled. In `opp_models`, `m = ftb/0.6` scales per-strength-class continue
probabilities `cont = 1 - (1 - c_L) * m`. `simulate` then applies a common size exponent
`cont ** (size/0.6)^size_exp`. The same `cont` is also used to narrow the range (`w`) of a seat that has
called earlier bets.

What the public history supports (checked against `kit/engine/game.py`): every action carries seat,
street, action and amount (raise = raise-to for the street, call = chips added, blinds as
`small_blind`/`big_blind`). From that you can rebuild pot before each bet, bet/pot ratio, bet vs raise,
how many players are still in, street, and relative position (from the small-blind seat; `summary` has
no `button`). Names are not available. Identity is the seat within the round.

## 3. Evidence: online predictive test on real rounds

Scripts in `tools/forge_ctx/`:
- `extract_events.py` replays the **135 counted Saturday tables** (PR #7 manifest; 24 duplicate files
  dropped) into 124,896 post-flop responses.
- `score_estimators.py` predicts every response from **earlier hands of the same table only, keyed by
  seat**, which is what the bot can know. It fits the field model and the shrinkage grid on r001-r027,
  scores on r028-r054 (64,542 responses, 66 tables), and puts 95% table-bootstrap intervals on paired
  log-loss differences.
- Output: `tools/forge_ctx/results_predictive.txt`. Field coefficients refitted on all rounds:
  `tools/forge_ctx/field_coef.json`.

Held-out results, mean log-loss change vs the parent's `ftb` (negative = better):

| estimator | all | first 250 hands | WBot was the bettor | table-4 responders |
|---|---|---|---|---|
| N0s: parent `ftb` through the parent's size curve (≈ what N uses) | -0.053 | -0.055 | -0.114 | -0.053 |
| FIELD: static logistic on context, identical for every seat | -0.095 | -0.111 | -0.170 | -0.101 |
| A: FIELD + per-seat logit shift, k1 = 20 | -0.105 | -0.117 | -0.174 | -0.114 |
| B: A + per-seat deviation in one split (best split) | -0.107 | -0.117 | -0.179 | -0.115 |
| **C: the candidate's representation** (FIELD at 0.6 pot + seat shift, then the parent's size curve) | **-0.094** | -0.107 | -0.135 | -0.097 |

The direct paired comparison **C - N0s** is -0.041 [-0.046, -0.037] overall, -0.021 [-0.033, -0.011] on
WBot's own bets, and -0.044 [-0.054, -0.034] for table-4 responders. The seat shift alone (C - C0) is
-0.010 [-0.013, -0.008] overall, -0.013 [-0.020, -0.008] at table 4, and -0.005 [-0.011, +0.001] on WBot's
bets, where it is inconclusive.

What this establishes:
1. **The big context effects are common to the field.** Size: 14% fold against bets under 30% pot, about 61%
   against bets over 0.8 pot. Multiway raises the log-odds of a fold by +1.06. Being in position vs the
   bettor lowers it by -0.89, so "checked to us" means weak. Facing a raise lowers it by -0.96 once size is
   held fixed. River adds +0.52. Calibration on held-out data: HU/IP observed 0.324, parent 0.450,
   candidate 0.360; MW/OOP observed 0.678, parent 0.457, candidate 0.717.
2. **Opponents differ mainly in level.** The shrunk per-seat shift is worth about 0.01 nats and its CI
   excludes 0.
3. **Opponent-specific context buckets are not worth it within a round.** They add 0.0005-0.002 nats
   (`B:<split>` minus AF in the results file). That supports the post-mortem's SE argument, so the
   hierarchy stops at seat level: bucket -> seat -> field.
4. An in-round table-level shift between seat and field adds nothing; training picks k0 = 800. Dropped.

Street and position: the history supports both reliably. Position enters only as "in or out of position
relative to the bettor", which has a large common effect. Street enters only as a common term. Neither is
split per opponent (see 3).

## 4. The candidate: one factor

Only the forward-looking continue model changes. `cont`, which `simulate` uses to value our bets and raises,
now comes from

    ftb_ctx(j) = sigmoid( CTX_C + CTX_REF + raise*CTX_RAISE + mw*CTX_MW + CTX_ST[street]
                          + ip*CTX_IP + mw*ip*CTX_MWIP + delta_j )
    delta_j    = logit((F_j + 20*E_j) / (N_j + 20)) - logit(E_j)

- `mw` = at least 2 live opponents when we act. `ip` = seat j acts after us on this street.
  `raise` = we face a bet (`to_call > 0`), so our action is a raise.
- `CTX_REF` sets size to the 0.6-pot anchor that the parent's size exponent is relative to. That keeps size
  handled exactly as in the parent.
- `F_j, N_j, E_j` = seat j's observed folds, responses, and field-expected folds, accumulated in
  `_learn_ctx` from `on_hand_end` histories. E_j uses the actual context and size of each response.

Unchanged: `w` range narrowing (still from the parent's pooled `ftb`), the size exponent, every tuned
parameter, preflop, time budgeting and legalisation. New code is wrapped in try/except and falls back to the
parent's `cont`.

Diff vs parent (`diff tools/cands/N_real.py tools/cands/forge_ctx_v1.py`): 122 lines added, 1 changed.
- docstring note; `import math`;
- module constants `CTX_*` (13 fitted numbers) plus `_sig`/`_logit`;
- three `Stats` slots `xf xn xe`;
- `on_hand_end` calls the new `_learn_ctx` and `ftb_ctx`;
- in `opp_models`: context set-up and the replacement `cont`.

Checks run:
- `tools/forge_ctx/check_candidate.py`: replaying 4 real tables (7- and 8-handed) through `on_hand_end`
  reproduces the offline extractor's per-seat folds, responses and expected folds exactly. 30/30 seats,
  max |xe diff| 0.0.
- In play against the table-4 clones (300 hands): 148 `ftb_ctx` calls, 0 exceptions, 0 hero errors.
  Values by context: HU, opponent in position 0.36; HU, opponent checked to us 0.53; MW 0.67-0.75;
  facing our raise 0.20-0.58.
- Runtime and fuzz: see section 6.

## 5. Arena results (paired, same seed, candidate vs parent; seeds 73000-73999 claimed for FORGE)

RESULTS_PLACEHOLDER

## 6. Runtime

RUNTIME_PLACEHOLDER

## 7. Assumptions and known limitations

- **Prediction is not EV.** Section 3 shows better fold prediction, including on WBot's own bets. Whether
  N's tuned bet/bluff thresholds turn that into chips is what the arena tests, and the arena is a weak
  instrument for this factor:
- **The arena clones don't reproduce the context effects** (`tools/forge_ctx/clone_vs_real.py`, 48 t4real
  tables vs real table-4 responses). Clone fold logic (`tools/opponents/_common.py`) depends only on hand
  strength and a 0.6-pot step.

  | context | real fold rate | clone fold rate |
  |---|---|---|
  | multiway | 65% | 45% |
  | facing a raise | 50% | 31% |
  | bets over 0.8 pot | 59% | 43% |
  | turn | 38% | 17% |
  | heads-up, in position | 33% | 35% (close) |
  | Poke's level | 55% | 41% |

  Expect the arena to punish the candidate's extra multiway aggression and its smaller raise-bluffing
  frequency. A negative arena result is therefore weak evidence against the candidate. A positive one holds
  despite the bias.
- Field model fitted on Saturday's field. Sunday table 4 has overnight uploads. The seat shift adapts the
  level within a round (k = 20, so about half weight after 20 responses), but the common context shape is
  assumed to carry over.
- The bettor's range is a confound. Real-field "multiway folds more" partly reflects the bettor's range when
  betting into several players. If WBot's own multiway betting range differs from the field's, the field
  effect may not transfer. The WBot-was-the-bettor subset still improves (C - N0s -0.021, CI excludes 0),
  but it's 27 tables of mixed G/I/N versions.
- Only the marginal fold is modelled. The mapping into the parent's strength classes
  (`m = ftb_ctx/0.6`) inherits the parent's tuned `c_*` values, which were tuned with the pooled `ftb` as
  input. Re-tuning was deliberately not done, to keep this one factor.
- The all-in term is used for learning only (expected folds), not in the 0.6-pot reference at decision time.
- The parent's size curve is miscalibrated at the extremes. It predicts 24% folds against bets under 30% pot,
  where 14% is observed, and 68% against bets over 1.1 pot, where 60% is observed. The candidate keeps that
  curve on purpose. Replacing it with the fitted size bins is the obvious next one-factor test: the A-vs-C
  gap is 0.011 nats overall and 0.039 on WBot's bets.
- Not a release gate: no live protocol/IPC test and no server-bank test. The decision-time cost is a few
  float operations per live opponent, and the hand-end cost is one `exp` per observed response.
- Parent identity (section 1) is still to be confirmed by the bot team.

## 8. Reproduce

    # data: PR #7's Hand_data + manifest (git archive origin/agent/saturday-postmortem PokerBot/Hand_data
    #       PokerBot/ExternalAnalysis/SaturdayFieldPostmortem/data/input_manifest.csv | tar -x -C <ROOT>)
    PY=<python with numpy+pandas>
    $PY tools/forge_ctx/extract_events.py --root <ROOT> --manifest <ROOT>/PokerBot/ExternalAnalysis/SaturdayFieldPostmortem/data/input_manifest.csv --out events.csv
    $PY tools/forge_ctx/score_estimators.py --events events.csv --out tools/forge_ctx/results_predictive.txt --coef tools/forge_ctx/field_coef.json
    $PY tools/forge_ctx/check_candidate.py --tables Hand_data/SaturdayRealRounds/saturday_r030.json ...
    $PY tools/forge_ctx/arena_t4.py tools/cands/forge_ctx_v1.py tools/cands/N_real.py --tables 48 --hands 300 --field t4real --seed 73902 --dump <DIR>
    $PY tools/forge_ctx/clone_vs_real.py --events events.csv --dump <DIR>
    bash tools/forge_ctx/run_gate.sh $PY > tools/forge_ctx/gate_results.txt

events.csv sha256: `dec356ada4e73a81613cbcc20e319f32ed1213ad540bc034bc32ee9d917f85b6` (PR #7 branch
`f7fbac4`). Environment: Python 3.12.13, numpy 2.4.6, pandas 3.0.3 (strategy-factory venv), for the
analysis scripts only. The bot itself is stdlib.
