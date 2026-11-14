# g_ctx_v1: PR #9's context model ported to frozen G (Rook)

This is a sandbox candidate. It has not been promoted or uploaded, and `submissions/` and `kit/bot.py` are untouched.

## Identity (sha256 of the LF bytes)
| Role | File | sha256 |
|---|---|---|
| Parent | `submissions/G_v7_final/bot.py` | `1ee577f0e4fed6aef7fef55d1c6f2684e5f3a2a8ce777983bb9ace9ba55ffe12` (the team's CRLF copy hashes to `b8a22e4b…0c16a`) |
| Source of the ported hunks | PR #9 `026ed13` `tools/cands/forge_ctx_v1.py` | `7bed0d20b1226c9595ba329f5f63118491b1eaca2afc3ff08fa6e466b02aae2b` |
| Candidate | `tools/cands/g_ctx_v1.py` | `beb13c75278d2a8152d6203002a3de7914b306be61239f9e81a7df1fe2d23783` |

- **Diff:** `g_ctx_v1_vs_G.diff`, a unified diff against G.
- **Timing:** G's parameters and time budget are unchanged (max_ms 1.2, hard_ms 3.0).

## How it was built
1. `diff -u N_v10_tuned forge_ctx_v1` gives 8 hunks. `patch` applied them to G cleanly, with offsets only. Every function the hunks touch (`_learn`, `opp_models`, `on_hand_end`, `simulate`) is byte-identical in G and N.
2. **Heads-up position fix** (fixtures F4/F8/F9). In `_learn_ctx`, position is now measured from the button (`bt = sbs if n == 2 else sbs - 1`), matching the engine and the decision side.
3. **Observable counters** (runtime audit R5/R6/R8):
   - `ctx_cont_fallbacks` and `ctx_learn_fallbacks` replace the silent `except: pass`;
   - `stats()` exports them together with `fallbacks`.

## Checks run
| Check | Result |
|---|---|
| `rook_ctx_fixtures.py`, F1–F9, against the bot and the author's extractor | **ALL PASS**, exit 0 (`fixtures_out.txt`) |
| `tools/fuzz.py`, 7 configurations (no-limit, pot-limit, fixed-limit, raise cap) | **0 errors**, worst decision 2.68 ms (`fuzz_out.txt`) |
| 300 hands against the 7 Sunday clones | `stats()` all 0; context data learned for 8 seats |

## Not done (owned by GAUGE / FORGE)
- No arena or EV evaluation.
- No seeded A-vs-A pairing check.
- No subprocess timing at 25 ms or 10 ms.
- No comparison against frozen I and N at matched budget.
