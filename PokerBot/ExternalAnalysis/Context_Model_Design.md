# Context-aware fold/continue model (FORGE): design, evidence, candidate

Branch `agent/forge-context-model`. Sandbox only: `submissions/`, `kit/bot.py` and production packages
are untouched, and nothing has been promoted, uploaded or merged.

## 1. Identity

| | path | sha256 (working copy, CRLF, as the team quotes) | sha256 (git blob, LF) |
|---|---|---|---|
| parent | `submissions/N_v10_tuned/bot.py` (= `tools/cands/N_real.py`) | `5c2b4b2c0ed3ddd5177fe758959e1c32e3a113f8c500a373f6b5d11d5bb7845f` | `77ec8ca9006dc1f8638d9430209cd6ef9e404e7e9b2fd161df4e3a862955b6ee` |
| candidate (primary, one factor vs parent) | `tools/cands/forge_ctx_v1.py` | `a6b222d15212aed0ee9ae80fadec2679cad2bb38432f9e8aaed1b9bf51d381d3` | `7bed0d20b1226c9595ba329f5f63118491b1eaca2afc3ff08fa6e466b02aae2b` |
| variant (one factor vs v1, section 4b) | `tools/cands/forge_ctx_v2.py` | `506b3ffddda6ebf0bca21f04b9dd0e2a6f8f5bf8ecb7645e43330816ab12d0ee` | `e81e20ab73fe12752dbe9ec5caefa0775abd1c899099f617ec7f52eae7cc59b8` |

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

## 4b. Variant forge_ctx_v2: a "bettor is us" term (adopted from SCOUT)

SCOUT's interim (`channel/to_bot_team/20261114-231106_scout_interim_context_findings.md`, item 4) found that
opponents fold about 12 points less to WBot's bets than to other bettors' bets in the same stratified spot.
v1's field model pools all bettors, so it should over-predict folds on exactly the bets the bot is valuing.
I tested this in the same online harness (`score_estimators.py --hero`, output
`tools/forge_ctx/results_predictive_hero.txt`):

- A static `bettor == WBot` term: logit -0.39 on train, -0.32 refitted on all rounds.
- Candidate representation vs the parent's actual use (C - N0s) on **WBot's own bets**: -0.047
  [-0.058, -0.038], up from -0.021 without the term. Overall: -0.046 [-0.050, -0.042]. Table-4
  responders: -0.050 [-0.059, -0.041].
- Calibration on WBot's bets (held out): observed 0.264. The parent's representation predicts 0.353, the
  candidate with the hero term 0.322, and the full field model A 0.275. The remaining over-prediction is
  the parent's size curve at small sizes: 66% of WBot's bets are under 40% pot (SCOUT), which is where that
  curve is worst.
- A **per-seat** hero shift on top (shrunk to the seat shift, k = 80) adds only -0.0019 [-0.0031, -0.0007]
  on WBot's bets. Not included, the same pattern as the other per-opponent splits.

`forge_ctx_v2.py` = v1 with the field coefficients refitted including the hero term
(`tools/forge_ctx/field_coef_hero.json`). `_learn_ctx` adds the term when the bettor was our own seat, and
`ftb_ctx` always adds it, because at decision time we are the bettor. Diff vs v1: constants, one term in
each of the two formulas, and the docstring. `check_candidate.py --cand forge_ctx_v2 --coef
field_coef_hero.json`: 30/30 seats exact. Fuzz: 0 errors.

Caveat (SCOUT item 5): the hero term lowers the average `m` on our bets, so it is a level change to the
input of the tuned `c_*`. The `c_*` were tuned in clone arenas, and the clones don't fold less to us, so the
tuned values cannot already contain this effect. That makes the term a correction rather than double
counting, but its EV effect is untested: clones can't show it, so the arena below is only a harm check.
Keep v1 as the clean one-factor test against the parent.

SCOUT's other suggestion, a separate facing-a-raise level, corresponds to my `B:kind` split: -0.0012
overall and -0.0019 at table 4, real but small. Within the bot it only matters when *we* raise
(about 10 responses per opponent per round). Not adopted, given the size of the gain.

## 5. Arena results (paired, same seed, candidate vs parent; seeds 73000-73999 claimed for FORGE)

Commands are in `tools/forge_ctx/run_gate.sh`; raw output is in `tools/forge_ctx/gate_results.txt`. CAND =
`tools/cands/forge_ctx_v1.py`, BASE = `tools/cands/N_real.py`. Both run in-process with the same local
time settings. No hero or opponent errors on any table.

| field | command | tables x hands | seed | cand | base | DIFF (se) | z |
|---|---|---|---|---|---|---|---|
| late | `tools/arena.py CAND BASE --field late` | 480 x 300 | 73101 | +44.1 | +42.9 | **+1.2 (2.3)** | 0.53 |
| real | `tools/arena.py ... --field real` | 480 x 300 | 73102 | +41.6 | +39.9 | **+1.8 (2.5)** | 0.72 |
| heldout | `tools/arena.py ... --field heldout` | 480 x 300 | 73103 | +55.7 | +51.2 | **+4.4 (2.5)** | 1.79 |
| archive | `tools/arena.py ... --field archive` | 64 x 1000 | 73104 | +85.3 | +81.2 | **+4.1 (5.5)** | 0.75 |
| table-4 clones (real fits) | `tools/forge_ctx/arena_t4.py ... --field t4real` | 480 x 300 | 73201 | +56.8 | +52.9 | **+3.9 (3.0)** | 1.32 |
| table-4 clones (heldout fits) | `tools/forge_ctx/arena_t4.py ... --field t4heldout` | 480 x 300 | 73202 | +64.6 | +63.3 | **+1.3 (3.0)** | 0.43 |

bb/100, paired same seed: same cards and seating, candidate vs parent in the hero seat. The table-4 fields
seat exactly the 7 table-4 clones, shuffled per table. No GAUGE table-4 field existed when this ran, so
`arena_t4.py` is FORGE's own.

**Reading.** All six differences are positive and none is conclusive on its own (largest z = 1.79).
Inverse-variance pooling gives +2.5 ± 1.1 bb/100 (z ≈ 2.2) across all six and +2.6 ± 2.1 for the two
table-4 fields. Treat the pooled figure as descriptive: the fields share clone families, and per
CONTRIBUTING a small sample is inconclusive. The honest summary is that the arena shows no sign of harm and
a consistent small positive tilt, measured on clones that do not reproduce the effects the candidate models
(section 7). The arena was run once and the candidate was not tuned or selected on it. A 48-table
diagnostic run (seed 73902, used for the clone check) gave +8.7 ± 8.4 and is not counted.

**v2 vs v1** (one factor: the hero term), `run_gate.sh $PY tools/cands/forge_ctx_v2.py tools/cands/forge_ctx_v1.py 733`.
Raw output: `tools/forge_ctx/gate_results_v2_vs_v1.txt`. No errors.

| field | tables x hands | seed | v2 | v1 | DIFF (se) | z |
|---|---|---|---|---|---|---|
| late | 480 x 300 | 73301 | +46.4 | +47.2 | -0.9 (2.4) | -0.35 |
| real | 480 x 300 | 73302 | +53.9 | +53.7 | +0.2 (2.4) | 0.07 |
| heldout | 480 x 300 | 73303 | +51.5 | +54.9 | -3.3 (2.5) | -1.31 |
| archive | 64 x 1000 | 73304 | +74.6 | +71.8 | +2.8 (5.0) | 0.55 |
| t4real | 480 x 300 | 73401 | +59.8 | +59.2 | +0.6 (2.7) | 0.21 |
| t4heldout | 480 x 300 | 73402 | +59.2 | +57.7 | +1.6 (2.6) | 0.59 |

Mixed signs, none conclusive, pooled about -0.3 ± 1.1. That's what a harm check should show here: the
clones don't fold less to us, so the arena cannot see the effect the term corrects. The case for v2 rests
entirely on the real-round predictive evidence in 4b. It is untested for EV.

## 6. Runtime

- **Added cost, measured directly** (identical recorded states, minimum of repeats):
  - `opp_models`: 6.8 → 10.6 µs per post-flop decision (+3.8 µs);
  - `on_hand_end`: 11.4 → 24.1 µs per hand (+12.7 µs);
  - total about +15 ms per 1,000-hand round, against a 10 s bank and a 25 ms per-decision cap.
- `tools/latency.py BOT 300 6` (end-to-end `act()`, run in alternating order) had p50 6.1 ms for both bots.
  The tails were dominated by machine jitter, since another agent session was running. The parent itself
  showed max 85 ms and 0.7% of decisions over 25 ms in one run; the candidate showed 0.2-1.1%. These runs
  cannot separate the bots, and the direct measurement above shows the change can't account for the tails.
  This is a local, in-process measure that doesn't certify server IPC or the bank (same caveat as gate_T).
- `tools/fuzz.py tools/cands/forge_ctx_v1.py` (DEBUG on, legality asserts): 0 errors in all four
  configurations, no illegal actions. Worst single act was 117-176 ms, versus 330 ms for the parent on the
  same noisy machine.

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
    $PY tools/forge_ctx/score_estimators.py --hero --events events.csv --out tools/forge_ctx/results_predictive_hero.txt --coef tools/forge_ctx/field_coef_hero.json
    $PY tools/forge_ctx/check_candidate.py --tables Hand_data/SaturdayRealRounds/saturday_r030.json ...   # outputs: check_v1.txt
    $PY tools/forge_ctx/check_candidate.py --cand forge_ctx_v2 --coef field_coef_hero.json --tables ...   # check_v2.txt
    $PY tools/forge_ctx/arena_t4.py tools/cands/forge_ctx_v1.py tools/cands/N_real.py --tables 48 --hands 300 --field t4real --seed 73902 --dump <DIR>
    $PY tools/forge_ctx/clone_vs_real.py --events events.csv --dump <DIR>
    bash tools/forge_ctx/run_gate.sh $PY > tools/forge_ctx/gate_results.txt
    bash tools/forge_ctx/run_gate.sh $PY tools/cands/forge_ctx_v2.py tools/cands/forge_ctx_v1.py 733 > tools/forge_ctx/gate_results_v2_vs_v1.txt

events.csv sha256: `dec356ada4e73a81613cbcc20e319f32ed1213ad540bc034bc32ee9d917f85b6` (PR #7 branch
`f7fbac4`). Environment: Python 3.12.13, numpy 2.4.6, pandas 3.0.3 (strategy-factory venv), for the
analysis scripts only. The bot itself is stdlib.
