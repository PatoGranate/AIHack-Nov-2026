# pablo_poker: game-theory poker bot with recursive self-improvement

An automated No-Limit Hold'em bot for the AlgoSoc / Imperial AI Hack Pokerbots
tournament, plus the machinery to improve it:

- **many games at once**: 128+ tables in parallel on every CPU core (~2,000 hands/s on 8 cores)
- **a real-time database**: every hand, strategy, trial and promotion in SQLite
- **a live dashboard** over that database
- **an RSI loop** that proposes, tests and promotes strategy changes behind a
  statistical gate, with former champions joining the opponent pool (self-play)
- **a reinforcement-learning phase 2**, with data logging and featurization ready ([rl/PLAN.md](rl/PLAN.md))

Standard library only (Python 3.9+). Nothing to install.

```bash
cd pablo_poker
python run_practice.py                 # 128 tables x 1,000 hands -> data/poker.db
python dashboard/server.py             # http://localhost:8765 (run it in a second terminal)
python run_rsi.py --cycles 10 --export # improve the strategy, write the champion to bot.py
python local_sim.py bot.py --rounds 5  # check bot.py under real tournament limits (10 ms / 10 s bank)
```

Upload `bot.py`.

---

## 1. What the starter kit contains (and what was missing)

| Kit file | What it is | Used here |
|---|---|---|
| `engine/` | The exact tournament engine: `FixedHandsTable` (1,000 hands, stacks reset every hand, 10/20 blinds), side pots, NL/PL/FL, raise caps; `SubprocessPlayer` with the 10 ms / 10 s limits | copied unchanged, drives every simulation |
| `examples/` | House bots: tight-aggressive, calling station, random | opponents (seeded so runs repeat) |
| `bot.py` | Starter bot: raises with pairs or J+ high, calls ≤ 2 bb | kept as `examples/starter_bot.py`: many teams will upload variants of it, so it's a heavily weighted opponent |
| `local_sim.py` | Bot vs house bots in separate processes, real time limits | copied; the final timing check for `bot.py` |
| `fetch_hands.py` | Downloads your team's hand histories from the site | copied; for evaluating against real opponents |
| `lab/` | An RSI lab from a **different project** (a Solana memecoin trading desk, package `act`) | see below |

**About `lab/`.** It imports `act.config`, `act.risk`, `act.strategy`,
`act.execution.matcher` and others that aren't in the folder, and reads YAML
configs that aren't there either, so none of it runs as is. Its *design* is
what we want, so it was ported to poker:

| lab module | ported to | what carried over |
|---|---|---|
| `stats.py` | `rsi/stats.py` | **copied unchanged**: SHA-256 deterministic RNG, Bonferroni, bootstrap CI, minimum detectable effect |
| `gate.py` | `rsi/gate.py` | pre-registered thresholds; one change at a time; pre-registration hash; fresh holdout; sample/MDE; beats-baseline CI; fold stability; challenger; budget |
| `research.py` | `rsi/loop.py` | observe → diagnose → propose → select → holdout once → gate → promote |
| `diagnose.py` | `rsi/diagnose.py` | diagnose the training data only, then `prioritize` the proposal order (never approves) |
| `registry.py` | `rsi/registry.py` | champion pointer, lineage, environment hashing → strategy ids |
| `autonomy.py` | `rsi/registry.fresh_seeds` | "consumed until": each holdout is judged on never-seen data |
| `simulate.py`, `dataset.py`, `observe.py` | `sim/arena.py`, `storage/db.py` | shadow simulation and episode recording → duplicate-seed poker tables |

**What was missing** and is now here: a real strategy (equity, ranges, pot
odds, bluffing theory, opponent modelling), a fast evaluator, a parallel
arena, an opponent pool, a database, a dashboard, self-play, the poker-specific
lab adapters, export to `bot.py`, and RL data plumbing.

## 2. Layout

```
pablo_poker/
  bot.py                 the upload: strategy.py with champion parameters (export_bot.py)
  pokerbot/strategy.py   the bot (single file, stdlib): evaluator, ranges, Monte Carlo, decisions
  sim/arena.py           parallel tables, duplicate seeds, streams hands to the DB
  sim/opponents.py       opponent pool: house bots, starter, archetypes, former champions
  storage/db.py          SQLite schema (WAL) + writer
  rsi/                   stats, gate, registry, diagnose, propose, loop
  dashboard/             live web dashboard (server.py + index.html)
  rl/                    phase 2: dataset export + plan
  tools/                 build_preflop.py (169-hand ranking), compare.py (head-to-head diagnosis)
  run_practice.py  run_rsi.py  export_bot.py  local_sim.py  fetch_hands.py
  engine/ examples/      from the kit
```

## 3. The bot: game theory first, exploitation second

**Objective.** The leaderboard ranks on **bb/100** (chips won), not on how
often you win a hand. The bot maximises expected chips, which usually means
winning *fewer* hands: folding the bad ones and getting paid with the good ones.

- **Hand evaluator**: table-driven 7-card evaluator (2.4 µs/hand, 2× the
  engine's, verified identical on 180k random comparisons).
- **Preflop**: all 169 starting hands ranked by Monte Carlo equity (blend of
  heads-up and 4-way, `tools/build_preflop.py`). Ranges are "top x% of
  1,326 combos" by position (EP 13% → BTN 42%), with 3-bet value plus a
  bluff band just below the calling range (suited hands, i.e. blockers and
  playability), 4-bet / jam-call ranges, and big-blind defence that depends on price.
- **Postflop**: Monte Carlo equity against each opponent's *estimated range*
  instead of a random hand. A range is the opponent's VPIP or PFR this round
  (Bayesian-smoothed), narrowed every time they bet or raise. Then:
  - **call** when equity beats pot odds `to_call / (pot + to_call)` plus a
    margin and a stack-commitment cost, with an implied-odds discount before the river
  - **value-bet / raise** above equity thresholds, using heads-up-equivalent
    equity `E^(1/n)` for n opponents
  - **bluff only when it's +EV**: the break-even fold frequency for a bet of
    s × pot is `s / (1 + s)` (the GTO indifference condition). The bot bluffs
    when the opponents' observed fold-to-bet rate beats it, and keeps a small
    base frequency otherwise so it isn't too predictable.
- **Exploitation** (same opponents for all 1,000 hands): calling stations
  get thinner value bets and no bluffs, players who fold a lot get stolen
  from, and against maniacs the bot calls lighter and their range is narrowed less.
- **Time**: Monte Carlo is capped by iterations *and* by the time bank left
  (≈1.4 s used per 1,000 hands in `local_sim.py`, against a 10 s bank). Any
  exception falls back to check/fold.

All ~30 knobs live in `DEFAULT_PARAMS` / `PARAM_SPACE` in `pokerbot/strategy.py`.

## 4. Practice + real-time database

```bash
python run_practice.py --tables 128 --hands 1000   # default
python run_practice.py --tables 256 --hands 500 --workers 8
python run_practice.py --betting pot_limit --raise-cap 3 --seats 7
```

Tables are queued across a process pool, as many truly simultaneous as you
have cores. Each worker streams hands into a queue, and a single writer thread
inserts them into `data/poker.db` as they happen. Tables in the schema:
`batches, tables, seats, hands, decisions, strategies, trials, promotions, state`
([storage/db.py](storage/db.py)). Query it from anything:

```sql
SELECT position, COUNT(*), SUM(delta)/20.0/COUNT(*)*100 AS bb100 FROM hands GROUP BY position;
```

**Dashboard**: `python dashboard/server.py`, then open http://localhost:8765.
It shows totals and hands/s, tables in play, the cumulative result of the
current batch, our strategies, results by position, every opponent's bb/100,
RSI trials with the gate's verdicts, promotions and the champion's parameters.
It refreshes every 2 s.

## 5. Recursive self-improvement

```bash
python run_rsi.py --cycles 10            # ~2–3 min per cycle on 8 cores
python run_rsi.py --hours 8 --export     # overnight
```

One cycle:

1. **Diagnose** the champion on practice/selection hands only (VPIP, PFR,
   WTSD, W$SD, by position and street) → leaks such as `passive_postflop` or
   `wins_little_without_showdown`.
2. **Propose** K candidates, each the champion with **one** parameter moved
   one step. The order comes from the diagnosis, then a **UCB bandit** over
   (parameter, direction) arms fed by every past result: knobs that keep paying
   get bigger steps, dead knobs fade. This is how the loop learns which
   changes are worth testing.
3. **Select** on fresh seeds using **duplicate poker**: every table is played
   twice with identical cards and opponents, once with the champion and once
   with the candidate, and the per-table chip difference is the evidence.
4. **Pre-register** the single best candidate and its holdout seeds (hashes
   stored *before* looking).
5. **Holdout**: new seeds, looked at once. Bootstrap CI on the paired
   difference at α = 0.10 / (number of holdout looks for this parent).
6. **Challenger**: a different opponent pool with no self-play opponents,
   which catches a candidate that only learned to beat its ancestors.
7. **Gate** ([rsi/gate.py](rsi/gate.py)): CONFIG_ONLY, ONE_CHANGE,
   PREREGISTERED, HOLDOUT_FRESH, SAMPLE (MDE), BEATS_BASELINE, STABILITY (3 of
   4 folds), CHALLENGER, NO_ERRORS, BUDGET. Every refusal is recorded with reasons.
8. **Promote**: the old champion **joins the league** of opponents. Each new
   champion has to beat every former version of itself (the recursive part).

The gate is deliberately strict, so most cycles end in a refusal. To promote
more often, raise `--holdout-tables` for more statistical power, or relax
`LAB` in `rsi/gate.py`. Changing the thresholds changes `LAB_SHA`, so old
pre-registrations stop matching.

`python export_bot.py` writes the champion into `bot.py`. Check it afterwards
with `python local_sim.py bot.py --rounds 5`: zero timeouts, zero errors, and
`think s/rd` well under 10.

## 6. Phase 2: reinforcement learning

See [rl/PLAN.md](rl/PLAN.md). Already in place: `--decisions` logs every
hero decision (state → action → hand result), `--explore 0.05` adds random
abstract actions for off-policy coverage, and `rl/dataset.py` exports
featurized CSV with the same stdlib `featurize` the bot can run live. A learned
policy is promoted only through the same gate.

## 7. Suggested 20-hour schedule

| Hours | What |
|---|---|
| 0–1 | `run_practice.py` + dashboard, read the diagnosis, upload a first `bot.py` for the practice rounds |
| 1–6 | `run_rsi.py --hours 5 --export` running in the background; meanwhile `fetch_hands.py` after practice rounds and compare against real opponents |
| 6–7 | Upload the champion; add new archetypes to `sim/opponents.py` that resemble what you saw on the real tables |
| 7–19 | RL phase ([rl/PLAN.md](rl/PLAN.md)) with RSI still running on the parameters |
| 19–20 | Final `local_sim.py` timing check (NL, PL, FL, raise cap), upload |

## 8. Tournament checklist

- `bot.py` imports only the standard library, class `Agent`, `Agent()` with no args ✔
- 10 ms per decision / 10 s bank: adaptive Monte Carlo, about 1.4 s per round measured ✔
- errors fall back to check/fold; illegal sizes get clamped by the engine anyway ✔
- `pot_limit`, `fixed_limit` and `raise_cap` work through the same code paths
  (the engine clamps sizes); test with `local_sim.py --betting ...` ✔
