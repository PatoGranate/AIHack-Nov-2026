# Rook: static runtime and fallback contract audit, PR #9 `026ed132f8ef728711cc629842d7c5ca1bd2de91`

Assignment: `channel/to_bot_team/20261114-232805_monitor_fixture_v3_runtime_task.md`. Branch `agent/rook-pr9-review`.

**Static review only.** I ran no arena, no timing benchmark and no harness, and made no production edits. Every measurement below is **PENDING**, for GAUGE to supply.

## Inputs (git-blob sha256 at the PR head)

| File | sha256 |
|---|---|
| `tools/cands/forge_ctx_v1.py` (candidate) | `7bed0d20b1226c9595ba329f5f63118491b1eaca2afc3ff08fa6e466b02aae2b` |
| `kit/engine/players.py` | `43ec0ded2f4ffefde7693b0b59a1a41c77bb3b6ebec20e1d7856e6fdbc133974` |
| `kit/engine/bot_runner.py` | `2be056d363f56b7f22a2065c68460a409934d18a119550e777543dc248df4d81` |
| `kit/engine/game.py` | `a55013f8453805d5e4d7fd5294bc31c003c83cbfd549191a11ac815553946533` |
| `kit/README.md` | `3c210d977173f88893c25c9733bf7819bc4ba3e953493521aa4884be20814f8c` |
| `tools/forge_ctx/arena_t4.py` | `e13457b36eef74350791e0d02994092afbb86caad3165c74576ddea638582b3e` |

**Inspection method:** `git show 026ed13:PokerBot/<path>`, then reading the line ranges cited. Line numbers below refer to the candidate unless a kit file is named.

## The runtime contract

### Engine side: subprocess player (`kit/engine/players.py`)
- **Per-decision limit:** `limit = min(timeout, bank)` (l.211–216). The clock starts **before** the state is sent and stops when the reply arrives (l.218–222), so time spent on inter-process messaging counts.
- **Bank charge:** `bank -= min(spent, limit)` (l.223–224). With the bank at or below 0, the decision is auto-played and counted in `bank_out` (l.213–215).
- **Timeouts:** a missing reply counts as a timeout and is auto-played (l.226–232).
- **`hand_end` is fire-and-forget:** it is sent without waiting (l.239–240).
- **The runner is single-threaded** (`bot_runner.py` l.64–78). `on_hand_end` runs inside the same loop that reads the next `act` message, so **time in `on_hand_end` delays the next `act` reply and is charged against the next decision's limit and the bank.**
- **Exceptions:** an exception from `agent.act` makes the runner send an `error` reply, which the engine counts in `note_error` and auto-plays (`bot_runner.py` l.65–70, `players.py` l.233–235). An exception from `on_hand_end` is silently swallowed (`bot_runner.py` l.73–77).
- **Documented limits:** the kit README says 10 ms per decision and a 10 s bank (l.150–152). The live server is reported at 25 ms per decision with a 10 s bank; that is the user's statement, not confirmed by this kit version.

### Bot side (candidate)
- **Hard stop:** `act` sets `hard_end = t0 + hard_ms` (14 ms; l.214, l.601–602).
- **Monte Carlo loop:** it checks `perf_counter` after **every** simulation and breaks on `now > hard`, or on `now > t_end` once at least 8 simulations have run (l.1065–1066). It is also capped at `max_sims` 4,000 (l.203).
- **Budget:** `budget()` spreads the remaining bank over the hands left, up to `max_ms` 6 ms, and returns 0 once fewer than 0.4 s remain (l.591–597). The bot's own bank is 7.0 s (l.227, l.356), against 10 s on the engine.
- **The bot undercounts its own time:** `spent` measures `act()` time plus a fixed 0.2 ms (l.611). It **excludes** messaging, JSON parsing and any `on_hand_end` time that delays the reply. The 3 s gap between the bot's 7 s and the engine's 10 s is the only margin for that.

## PASS / FAIL / PENDING matrix

| # | Check | Verdict | Evidence |
|---|---|---|---|
| R1 | The Monte Carlo loop is bounded by a hard deadline | **PASS** (static) | It checks after every simulation and breaks on `hard`, with `max_sims` 4,000 as a backstop (l.1065–1066, l.203). The worst overrun is one simulation past `hard`. |
| R2 | New decision-time work is bounded | **PASS** (static) | The context set-up is O(1) (l.782–787). `ftb_ctx` costs a few float operations plus one `exp` per live opponent (l.545–554), called once per opponent inside the `opp_models` loop (l.825–832). It runs before `simulate`, outside the Monte Carlo deadline check, but it is O(opponents) ≤ 7. |
| R3 | New learning work is bounded | **PASS** (static) | `_learn_ctx` makes one pass over the hand's `history` (l.483–543) with an O(n) multiway count per response, giving O(len(history) × n). Hands are finite, so this is bounded, but it is **not budgeted**: see R7. |
| R4 | Exceptions inside `act()` | **PASS**, with caveat | `decide()` is wrapped (l.603–609). On an exception, `fallbacks += 1`, `out = None`, and `legalise()` then returns check or fold (l.614–640). That is a legal action, but a **strategic fallback**. |
| R5 | Exceptions in the new `cont` path | **FAIL**: a silent fallback | `try: … except Exception: pass` (l.826–832) keeps the parent's `cont` with **no counter**. A systematic error, such as a `None` in state, would turn the factor off unnoticed while still playing legally. |
| R6 | Exceptions in `_learn_ctx` | **FAIL**: a silent fallback | `on_hand_end` wraps `_learn_ctx` in `try/except: pass` (l.392–395), with no counter. A failure leaves `xf`, `xn` and `xe` frozen, so `ftb_ctx` silently falls back to the pure field prior. The runner also swallows `on_hand_end` exceptions. |
| R7 | `on_hand_end` time is charged | **PENDING** (measurement) | Per the contract above, `_learn` plus `_learn_ctx` time delays the next reply and is charged by the engine but **not** counted in the bot's `spent`. GC also runs every 100 hands in `on_hand_end` (l.396–399). The size of this cost is unmeasured. |
| R8 | The `fallbacks` counter is observable | **FAIL** | `self.fallbacks` is incremented (l.608) but never logged, returned or exported, so neither the arena nor GAUGE can read it unless a harness inspects the Agent object. |
| R9 | Benchmark runner enforces time | **FAIL** as runtime evidence | `arena_t4.py` uses `LocalPlayer` (l.23, l.48), which has **no time limit** (`players.py` docstring l.4–5). Arena results therefore say nothing about timeouts or bank use. |
| R10 | Bank guard is consistent with the engine | **PENDING** (measurement) | Guard 7.0 s vs engine 10 s, with messaging, `on_hand_end` and GC excluded from `spent`. Inherited unchanged from parent N, which had 0 bank-outs in 5 live v8 rounds (5.5–7.1 s per round), but the candidate adds `_learn_ctx` work. |
| R11 | Per-decision timing against 14 ms and 25 ms | **PENDING** (measurement) | The 14 ms hard stop covers only the Monte Carlo loop. Pre-simulation work (`opp_models`, candidate sizes) and messaging add to it. The 25 ms server figure has not been confirmed for this kit. |

## Counters required (minimal, candidate-side, no behaviour change)
1. `ctx_cont_fallbacks`: increment in the `except` at l.831.
2. `ctx_learn_fallbacks`: increment in the `except` at l.394.
3. Export the existing `fallbacks` (l.608), together with 1 and 2, through a cheap `stats()` method or a `DEBUG`-gated stderr line at the end of the round, so harnesses can read them.
4. Optionally, `hand_end_ms`, the maximum and total time spent in `on_hand_end`.

## Minimal runtime scenarios for GAUGE (to measure; not run here)
- **S1:** a `SubprocessPlayer` run with `timeout_ms=25` and `bank_ms=10000` against the 7 Sunday clones, 1,000 hands, candidate and parent N on the same seeds. Record timeouts, `bank_out`, errors, the per-decision maximum, p99 and total thinking time per round.
- **S2:** the same run with `timeout_ms=10` (the kit README limit) as a worst-case check.
- **S3:** a run with `on_hand_end` time isolated: record `hand_end_ms` (counter 4), and the gap between engine-charged time (`stats.total_ms`) and bot `spent`.
- **S4:** fault injection in a sandbox copy. Make `ftb_ctx` raise, and separately make `_learn_ctx` raise. Confirm that legal play continues and that the new counters increment, so the failure is no longer silent.
- **S5:** a CPU-load check, for example 2 background CPU-bound processes, to repeat the earlier finding that load-induced timeouts come from OS pauses during thinking.

## Summary
- **Bounded:** all new work is bounded (R1–R3), and the decision path's fallback stays legal (R4).
- **Blockers before a release gate:** the silent fallbacks (R5, R6), the unexported counter (R8) and a benchmark runner that enforces no time (R9).
- **Still unmeasured:** `on_hand_end` cost, bank margin and per-decision timing (R7, R10, R11), all PENDING for GAUGE.
