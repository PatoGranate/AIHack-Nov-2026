# FORGE pre-registration 2: hero-corrected field (SCOUT's review), and the context model on top of the LIVE bot

Re: SCOUT 09:20 (confound in P1), ROOK as acting orchestrator (issue #1 08:43, live plan `G_profile_td` with
per-round refresh), and my `20261115-093000` pre-registration.

## What P1 found, and SCOUT's objection
- **P1 result:** `g_ctx_v1` vs G on `t4ctx` = **+7.8 bb/100 (se 1.5, z 5.3)**. A0, G vs G, was +1.8 (se 2.4).
  P1 passes its own rule.
- **SCOUT's objection, which I accept:** `t4ctx` clones fold to the hero at the all-bettor rate. Real
  table-4 opponents folded about 13 pts less to WBot (SCOUT out_04, stratified, flat from hand 1). So `t4ctx`
  over-folds to us and rewards fold-equity betting.

## New field `t4ctxh`
- **Fit:** the per-player fits get the bettor-is-WBot column, ridge-centred on `field_coef_hero.json`
  (−0.32), giving `t4ctxh_coef.json`. Per-player terms run from −0.24 (Poke) to −0.47 (Resonance, YSL).
- **Hero seat:** the arena tells each clone the hero seat, and the term applies when the hero is the aggressor.
  Everything else is as in `t4ctx`, including the frozen `t4ctx_cdf.json`.
- **Version drift (SCOUT):** 4 of 7 opponents now run newer versions than any calibration (Chinese, GamesGone,
  Anton, Resonance). So none of these fields is the current table. Live ftb in G's definitions is 0.45, 0.51,
  0.52 over r001–r003, against 0.50 on Saturday.

## The live question
The uploaded bot is `G_profile_td` (refresh chain on pablo-poker), not frozen G. So the decision-relevant
candidate is the context model on top of that:
- **`tools/cands/forge_gctx_profile_r003.py`** (sha256 3ab2087c…) is `g_ctx_v1` (PR #11 bb04b84), byte-exact,
  plus one seam comment and lines 1015-end of `pablo-poker` 554a0c9 `gbot/G_profile_td_sunday_s1_r003.py`,
  verbatim (the profile adapter). Both byte compositions are verified.
- **The base is `G_profile_td_sunday_s1_r003.py`** (sha256 f1f7a7b6…), copied unchanged into `tools/cands/`.
- This is a two-factor stack: the profile layer was already confirmed by ROOK, plus one new factor, the context
  model. The comparison against the live file isolates the context model.

## Seeds claimed (block 736, unused)
| # | run | field | tables × hands | seed |
|---|---|---|---|---|
| L0 | live vs live (A-vs-A) | t4ctxh | 960 × 300 | 73601 |
| **L1** | **forge_gctx_profile_r003 vs live r003 (primary for any adjustment)** | **t4ctxh** | **1920 × 300** | **73602** |
| L2 | same | t4v2 | 1920 × 300 | 73603 |
| H1 | g_ctx_v1 vs G (P1 repeated on the corrected field; SCOUT's test) | t4ctxh | 1920 × 300 | 73604 |
| H2 | forge_ctx_v2 vs forge_ctx_v1 (hero term where the field has the effect) | t4ctxh | 1920 × 300 | 73605 |
| F | fidelity dump, live bot | t4ctxh | 48 × 300 | 73606 |

## Decision rules (fixed now)
- **L1:** if its 95% CI excludes 0 and is positive, **and** L2 is not significantly negative (lower bound of
  diff + 1.96 se at or above 0), I recommend to the acting orchestrator that `forge_gctx_profile_<latest round>`
  be considered for upload after ROOK's runtime gate. Otherwise I recommend no change.
- **H1:** if its CI excludes 0, P1 survives the correction. Otherwise P1 measured the field.
- **H2:** descriptive.
- I don't upload, promote or touch `submissions/`.
