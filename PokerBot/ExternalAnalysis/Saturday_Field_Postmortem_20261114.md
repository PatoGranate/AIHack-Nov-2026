# Saturday field post-mortem (54 counted rounds) and Sunday table 4

Author: Matthias's Claude Code session (Red / kaiserbot side of the team).
Audience: every teammate and teammate agent (orchestrator, SCOUT, FORGE, GAUGE, ROOK, pablo_poker).
Status: **revision 2** (2026-11-14 ~23:00), answering the PR #7 review (`pelayo-claude-bot`, changes requested on
`b3097de`). What changed is listed at the end. All results are descriptive or exploratory unless stated otherwise.
None of them is release evidence.

**Interpretation correction:** all WBot totals, styles, head-to-head inputs and Sunday scenarios below
pool server versions v5-v9. They describe the account's historical mixture, not frozen G, I or N.
The version-separated check in section 4 is required before applying an account-level conclusion to G.

Reproduce from the repo alone (Python 3.12, numpy 2.x; the outputs were made with 3.12.13 / numpy 2.4.6):

    cd PokerBot/ExternalAnalysis/SaturdayFieldPostmortem
    python 00_manifest.py; python 01_noise_vs_skill.py; python 02_styles_pairwise.py
    python 03_bucket_edges.py; python 04_donor_dependence.py; python 05_sunday_table4.py; python 06_robustness.py

Each script's full output is in `SaturdayFieldPostmortem/data/out_*.txt`.

Please challenge this in `channel/to_bot_team/` (new file per topic). Section 9 lists the open questions.

## 0. Data

- **Every input is now committed.** I added the 60 rounds that were missing from `Hand_data` (Red r24-r54 to
  `ExternalTeamData/external_team_03`, kaiserbot r24-r53 to `external_team_02`, WBot r54 to
  `SaturdayRealRounds`). These are our own accounts' downloads, unchanged apart from an appended `"team"` key
  that follows the existing files' convention. Where a file was already in the repo, our copy has identical
  parsed content apart from the repo's metadata keys (`team`, `_status`).
- `data/input_manifest.csv`: 159 hand files with SHA-256, observing account, round, dedup key and status.
  135 files are used (unique counted tables, 135,000 hands) and 24 are duplicates of a table seen by two of our
  accounts. Dedup key = round ref + ordered seat names; the first file in sorted path order is used.
  Hashes are of the checked-out bytes. Analyses use parsed JSON, so line-ending conversion can't change a result.
- Integrity: every hand sums to zero, and our seat's totals match the official per-round chips (665
  team-rounds, max diff 0).
- `data/leaderboard_history_r13_r48.csv`: 39 archived leaderboard snapshots covering played rounds 13-48.
  Consecutive-round differences give exact chips for eligible team-rounds 14-48, including tables we did
  not sit at. Rounds 49-54 have no per-round leaderboard increments in this archive. Rook independently
  reconciled all 665 overlapping hand-derived team-rounds with zero discrepancies.

## 1. Facts and sources

- **Sunday rules.** Organiser kit `PokerBot/kit/README.md:169-170`: "Saturday's ranking seeds bucket tables. Each
  bucket table plays rounds 9:00-11:55 a.m.; the top two by chips go through to the final table." Public API
  snapshot (`data/sunday_buckets.json`): announcement at 20:46, "31 teams seeded from Saturday's average score into
  4 table(s). The top 2 at each table go through."; `sunday.stages[0]` = `{rounds: 36, advance: 2}`; the
  schedule says Sunday runs 09:00-12:00. The 36-round count comes from the API, not the kit.
- **WBot's table 4** (API buckets): Resonance Qt (seed 4), Anker Batteries (5), Chinese people can fly (12),
  WBot (13), GamesGone (20), Poke (21), Anton (28), YSL_TWIZZY (29). The seeds follow a snake pattern.
- Red, kaiserbot, AAST and SmartBGerBot were in the 19:00 standings (48 rounds) and are absent from the final ones.
- Round 41: SmartBGerBot lost -1,552 bb/100 at one table. That one table gave The Market Makers +409,
  Attention +302, Durahim +281 and JoCal +271 (about 7.6 bb/100 of The Market Makers' 54-round average).
- ediz_slow (VPIP 77) lost -264 bb/100 over 13 rounds and left after r31. Neither it nor clanker is seeded for Sunday.

## 2. Noise vs skill

| quantity | value |
|---|---|
| SD of one team's bb/100 in one 1,000-hand round | ~45 typical; 65 pooled (the broken-bot tables inflate it) |
| SD of true skill across teams (variance decomposition, r14-48) | ~16 bb/100 |
| skill share of one round's variance | ~6% |
| split-half reliability (odd vs even rounds) | 0.53 for half the rounds -> 0.69 (Spearman-Brown) for all 54 |
| first-half vs second-half team-mean correlation | 0.39 |
| SE of a 54-round Saturday average | ±8.8 bb/100 |

The top 2 and the bottom ~6 are separated; ranks ~5-25 mostly aren't. A version judged on 3-5 live rounds
is still about ±20-25.

## 3. Matchup effects: exploratory, none detected

Method: in every hand, each winner's gain is allocated to the losers in proportion to their losses. This is
**bookkeeping of multiway net results, not identified pairwise strategic EV**: A's take from B can depend on
who else is in the pot. Only 0.8% of hands (0.3% of chips lost) have more than one winner, so the allocation
choice itself barely matters. The interpretation is the limitation.

- An additive model (pair rate = s_A - s_B) fitted to the 765 pairs with 2,000 or more hands together:
  diagonal chi2/df 1.21, 1 pair beyond |z|>3, 0 cyclic among the 7 triads with all three edges |t|>2. The
  fitted s correlates 0.93 with the leaderboard. Pairs from the same tables are dependent, so **the chi2 is not
  a calibrated lack-of-fit test**.
- Resampling whole tables (`06_robustness.py`, B=1000), restricted to the 142 pairs that met at 6 or more
  tables (fewer clusters make the bootstrap SE unreliable): table-bootstrap SE / per-hand SE has median 1.01
  (IQR 0.83-1.24), so clustering doesn't visibly inflate the uncertainty. Residual chi2/df 1.58 (diagonal,
  still uncalibrated), 1 pair beyond |z|>3, 16 of 142 pairs with |t|>2 (7 expected by chance),
  **0 triads testable**.

**Conclusion:** this exploratory additive model found no cycles in the sample we have. The sample has little
power to detect them, so this does not establish that matchup effects are absent. The working hypothesis for
tonight: one skill ordering explains most of what we can see, and per-opponent adjustments (section 7)
should be judged by arena tests, not assumed from this result.

## 4. Where profits came from (allocation-dependent, descriptive)

Per 100 of the team's own hands, using the allocation above. Donors = the 11 teams that finished below 0 plus
ediz_slow. These are the `from_donors` / `from_others` sets, distinct from the fixed seven-bot
`BIG7` set used in the following with/without comparison. Brackets are 5th-95th bootstrap percentiles,
so they are **90% intervals**, not 95% intervals. Tables in the same five-minute slot share field and
version conditions; table resampling does not preserve that cross-table dependence, so uncertainty may
be understated. The top-21 column is seven times the exposure-weighted per-opponent rate: it is a
normalization, not an observed result at a table of seven top-21 opponents.

90% intervals from resampling whole tables:

| team | from donors | from everyone else | edge vs top 21, per 7 such opponents |
|---|---|---|---|
| Attention Is All In | +23.9 [+14.5, +35.1] | +19.9 [+8.9, +32.2] | +32.5 [+11.5, +55.1] |
| Gherkers | +23.1 [+10.5, +36.9] | +17.0 [+4.6, +30.3] | +12.7 [-7.9, +32.3] |
| The Market Makers | +20.0 [+8.8, +33.9] | +13.7 [+0.7, +27.1] | +15.0 [-6.4, +36.4] |
| Anker Batteries | +11.5 [+6.1, +17.5] | +12.6 [+1.6, +24.5] | +16.6 [-1.2, +36.7] |
| Resonance Qt | +7.1 [+1.1, +12.9] | +7.8 [-3.9, +18.8] | +14.7 [-6.4, +33.3] |
| FisherMen | +8.0 [-3.7, +20.1] | +16.4 [+3.1, +29.6] | +25.5 [+0.7, +49.0] |
| **WBot** | **+14.8 [+7.0, +22.8]** | **-1.5 [-12.1, +9.5]** | **-18.0 [-37.6, +3.9]** |
| Red | +14.1 [+5.7, +22.8] | -13.4 [-22.2, -4.4] | -22.6 [-38.0, -6.3] |
| kaiserbot | +11.7 [+4.9, +18.6] | -3.7 [-11.8, +4.6] | -6.3 [-22.8, +10.1] |

**Attribution-free check:** each team's own table result, at tables with at least one of the 7 worst bots
(clanker, ediz_slow, AIl IN, Joca, YSL_TWIZZY, Anton, ND) vs none, with 90% intervals:

| team | with donors | no donors |
|---|---|---|
| Attention Is All In | +48.0 [+29.3, +69.5] | +34.6 [+14.9, +55.7] |
| Gherkers | +51.9 [+27.9, +79.3] | +28.2 [+5.5, +49.5] |
| Anker Batteries | +29.1 [+18.0, +41.9] | +15.6 [-4.3, +37.8] |
| Resonance Qt | +11.7 [+2.4, +20.6] | +24.3 [-9.7, +51.9] |
| WBot | +21.3 [+6.3, +37.2] | -9.3 [-28.8, +10.8] |
| kaiserbot | +12.3 [+2.2, +23.1] | -0.2 [-20.1, +20.8] |

Reading: WBot's Saturday profit is consistent with coming mainly from the weakest bots. Its result against
everyone else is near zero, with wide intervals. This is a hypothesis about WBot's weakness against competent
opponents, supported by both views, not a proven fact. WBot's r14-31 vs r32-48 averages (+26.9 -> +4.5) fit it too.

### WBot split by server version

Rook's independent `pm_boot.py` output at validation commit
`c91fe39b11702caf9f3cec63b20228d2e1616c1e` separates the same top-21 normalization:

| Server versions / behavioral attribution | Tables | Top-21 normalization (bb/100) | 90% table-bootstrap interval |
|---|---:|---:|---|
| v5, v7, v9 / G-compatible | 25 | +2.0 | [-28.5, +38.0] |
| v6 / I-compatible | 24 | -34.3 | [-61.5, -5.7] |
| v8 / likely N | 5 | -20.2 | [-70.2, +16.6] |

The G-compatible window is r001-r023, r048 and r054; I-compatible is r024-r047; likely N is r049-r053.
These are behavioral/documentary source attributions, not deployed-artifact hash proofs. Rook's
`pm_byver.py` output separates r054 as `r54+`, whereas `pm_boot.py` includes it in the G-compatible group;
the table above uses the latter consistently. The pooled negative estimate is therefore not evidence
that frozen G has that same deficit. Calendar time, opponents and source versions are confounded;
the splits are not a controlled comparison of G versus I/N.

Evidence: `PokerBot/ExternalAnalysis/AgentReports/ROOK_PR7_validation/pm_boot_out.txt` and
`ROOK_PR7_validation.md` on the validation branch at the exact commit above. The validation artifacts
are external review evidence until separately integrated into main; do not mistake their branch paths
for files already added by this PR.

## 5. Style vs result (35 ranked teams, final bb/100; correlations, descriptive)

| stat | corr |
|---|---|
| went to showdown / saw flop (WTSD) | -0.61 |
| won at showdown (W$SD) | +0.60 |
| post-flop aggression | +0.36 |
| fold to post-flop bet | +0.35 |
| VPIP / PFR / 3-bet | -0.02 / +0.17 / 0.00 |

The top bots reach showdown rarely (~23%) and win there (~59%). Attention Is All In is the only bot that wins
from the big blind (+44); Red lost -91 there. WBot: WTSD 32%, W$SD 47%, AF 87%, median post-flop bet 18% of pot.

## 6. Sunday table 4: illustrative scenarios, not a forecast

Opponent styles (Saturday, every table we saw; frequencies, not profitability):

| team | LB | VPIP | PFR | 3b | limp | fold to bet | AF | WTSD | W$SD |
|---|---|---|---|---|---|---|---|---|---|
| Resonance Qt | +24.0 | 22 | 16 | 12 | 0 | 39 | 57 | 24 | 52 |
| Anker Batteries | +23.1 | 23 | 17 | 13 | 0 | 46 | 61 | 24 | 58 |
| Chinese people can fly | +13.6 | 36 | 22 | 7 | 0 | 46 | 63 | 27 | 51 |
| GamesGone | +5.0 | 26 | 16 | 3 | 0 | 43 | 69 | 27 | 44 |
| Poke | +4.5 | 34 | 16 | 4 | 10 | 55 | 78 | 27 | 51 |
| Anton | -20.4 | 32 | 26 | 25 | 3 | 47 | 59 | 38 | 48 |
| YSL_TWIZZY | -20.6 | 21 | 16 | 4 | 0 | 26 | 39 | 45 | 53 |

Scenario model (`05_sunday_table4.py`):
- **The WBot seat uses pooled historical G/I/likely-N inputs.** Its probabilities are not estimates for
  the currently selected frozen G artifact. A G-only scenario requires a separate recomputation; none
  is claimed here.
- Expected result = sum of pairwise rates (additive model, shrunk toward the observed head-to-head with
  tau = assumed SD of a pair's deviation).
- Sunday-edge uncertainty and round noise are both drawn **zero-sum across the table**.
- In the "edge X" scenarios the other seats are rebalanced so the table stays zero-sum.
- All of them assume the pooled Saturday tendencies remain stable. WBot already changed policy during
  Saturday; Sunday uploads and opponent adaptation can invalidate that assumption.

| assumption set | WBot's P(top 2) | our expected edge needed for 50% |
|---|---|---|
| additive model only (tau -> 0), skill SD 5-15, round SD 45-65 | 25-29% | +12 to +18 |
| shrunk, tau = 6 | 22-34% | +20 |
| observed head-to-heads only (each ±7-13; mostly noise) | 59-66% | +36 to +38 |

Under the additive model, with or without shrinkage, Anker and Resonance have the highest expected results
(tau 6: Anker +29.6, Resonance +22.9, WBot +10.8). With raw head-to-heads only, WBot ranks second
(Resonance +44, WBot +41, Anker +38), but each of those inputs is ±7-13, so that ordering is fragile.
These numbers show the scale of what it takes to qualify. **They are not a release objective or a validated forecast.**

## 7. For the per-opponent context model (SCOUT / FORGE): observations and testable hypotheses

- Fold to post-flop bet at table 4 ranges from 26% (YSL_TWIZZY) to 55% (Poke). That variation is large
  relative to a single pooled rate.
- Each table-4 opponent faces ~115-220 post-flop bets per 1,000-hand round. A per-opponent fold rate reaches
  about ±4 points by the end of a round and about ±8 after ~250 hands. Each extra split (bet size, HU vs
  multiway, street, position) roughly doubles the SE per bucket. That argues for shrinkage (bucket -> opponent
  -> field) over raw bucket frequencies.
- Distinctive in-round signatures (the bot doesn't get names): Poke's 10% limps, Anton's 25% 3-bets,
  YSL's 45% showdown rate.
- Hypotheses to test in the arena (frequency evidence only; no claim of profitability):
  thinner, larger value bets and fewer bluffs vs low fold-to-bet / high-WTSD opponents; more betting when
  checked to by high-fold opponents; wider 4-bet value and wider 3-bet calls in position vs very high 3-bet
  rates; less paying off vs high-W$SD solid opponents; WBot's 18%-of-pot sizing as its own one-factor test.

## 8. Suggested approach (opinion)

1. Build an arena field from clones of the 7 table-4 opponents (the repo has clone tooling) and give it its
   own seeds. Saturday's field average is a poorer proxy for this table.
2. Judge candidates on expected result at that table with honest uncertainty. Section 6 shows the scale
   needed, not a pass mark.
3. Treat a single live round as ±45; on Sunday, 36 rounds give about ±7.5 per team.

## 9. Open questions for teammates

1. Matchup effects: does any of your arena work show A beats B, B beats C, C beats A beyond noise?
2. WBot's weakness against competent bots (section 4): does your own WBot analysis agree?
3. Better pairwise attribution or covariance-aware tests: proposals welcome.
4. Clones of the table-4 opponents: does anyone already have them?

## Changes in revision 2 (answers to the PR #7 review)

1. Reproducibility: the missing raw inputs are committed, `00_manifest.py` writes a hashed manifest, the exact
   commands and environment are above, and every output was regenerated from committed inputs only (identical
   numbers to revision 1 up to floating-point rounding).
2. Inference: section 3 now says "exploratory, no cycles detected, low power". Removed the claims of
   independent edges and a "better strategy overall". Added the multi-winner share and table-bootstrap
   intervals, labelled donor shares and top-21 edges as allocation-dependent, and replaced the unstable
   donor-share percentage with an additive split (from donors / from everyone else).
3. Forecasting: zero-sum draws, the edge scenario rebalances the other seats, a tau / skill-SD / round-SD
   sensitivity grid, results labelled illustrative, the "+20 target" removed, and Sunday rules cited from the
   kit README and the API. The first Sunday simulation in `03_bucket_edges.py` assumed block seeding and is
   superseded.
