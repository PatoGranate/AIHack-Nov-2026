# FORGE pre-registration: g_ctx_v1 vs G on a field that folds like the real table 4

Re: PR #11 (ROOK `g_ctx_v1`), item 2 "paired G vs g_ctx_v1 on untouched seeds"; PR #16 (G is the reference).
Branch `agent/forge-ctx-field`. Nothing under `submissions/` or `kit/` is touched, and nothing is promoted.

## Why a new field
All existing clones, including `sunday_v2`, are `ParamBot`s: they fold on hand strength only. They can't
show what a fold-model change is worth (PR #9, `clone_vs_real_t4real.txt`). The new **`t4ctx`** field
(`tools/forge_ctx/ctx_clone.py`) works like this:
- It keeps each `sunday_v2` clone's preflop, betting and raising.
- Facing a post-flop bet, each clone folds with the probability given by its own logistic, fitted on real Saturday
  events: field features, ridge-shrunk to the field fit, with lambda chosen by 5-fold CV (`t4ctx_coef.json`).
- It folds its weakest hands first, using a randomised strength rank calibrated per clone × street × bet/raise
  (`t4ctx_cdf.json`, frozen after 3 passes; calibration seeds 73971-73974).
- **The control field is `t4v2`**: the same `sunday_v2` clones with the same deterministic per-decision RNG.

Fidelity on 48 tables (`clone_vs_real_t4ctx.txt`, seed 73976), real vs `t4ctx` (old `t4v2` in brackets):

| context | real | `t4ctx` | `t4v2` |
|---|---|---|---|
| heads-up | 39% | 40% | 47% |
| multiway | 65% | 64% | 49% |
| facing a raise | 50% | 48% | 37% |
| bets over 0.8 pot | 59% | 58% | 49% |
| turn | 38% | 36% | 18% |
| YSL | 26% | 29% | 16% |
| Anton | 47% | 48% | 64% |

- **Known distortion:** it exaggerates out-of-position folding (67% vs 54% real).
- **Known gap:** it under-folds to small bets (14% vs 21%).
- **Not modelled:** the bettor-is-us effect, because clones can't identify the hero. This is why v2 is not tested here.
- **Circularity:** the generator shares feature definitions with the candidate's model, so this field is an
  "if opponents fold like the data says" test. It is favourable to the candidate by construction, not a
  neutral one. Per-player coefficients give it more structure than the candidate's field-plus-seat-level model.

## Seeds claimed (FORGE range 73000-73999, block 735; none used before)
All runs are paired same-seed (`arena_t4.py`). The base is `submissions/G_v7_final/bot.py`, sha256 b8a22e4b… (raw).

| # | run | field | tables × hands | seed |
|---|---|---|---|---|
| A0 | G vs G (A-vs-A noise check) | t4ctx | 960 × 300 | 73501 |
| **P1** | **g_ctx_v1 vs G (primary)** | **t4ctx** | **1920 × 300** | **73502** |
| C1 | g_ctx_v1 vs G (control) | t4v2 | 1920 × 300 | 73503 |
| S1 | forge_ctx_v1 vs N_real (my N port) | t4ctx | 1920 × 300 | 73504 |
| S2 | g_ctx_v1 vs G, round length | t4ctx | 576 × 1000 | 73505 |

## Decision rule (fixed before running)
- **P1** shows improvement on this field only if its 95% CI (diff ± 1.96 se) excludes 0. Otherwise it is
  inconclusive. A0 must be consistent with 0, otherwise the pairing is broken and nothing counts.
- C1, S1 and S2 are descriptive. Nothing is pooled across fields.
- **Even a P1 pass is not a release claim.** It means only "under real-data fold behaviour the context model earns
  chips". Server timing, the 10 s bank and real opponents remain gated by GAUGE and the orchestrator.
