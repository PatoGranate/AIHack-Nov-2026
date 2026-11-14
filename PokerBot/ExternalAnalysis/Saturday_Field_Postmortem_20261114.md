# Saturday field post-mortem (54 counted rounds) and what it means for Sunday table 4

Author: Matthias's Claude Code session (Red / kaiserbot side of the team), 2026-11-14 ~22:00.
Audience: every teammate and teammate agent (orchestrator, SCOUT, FORGE, GAUGE, ROOK, pablo_poker).
Scripts, inputs and full outputs: `SaturdayFieldPostmortem/` (see its README). Every number here is in
`SaturdayFieldPostmortem/data/out_*.txt` and can be regenerated.

**Please challenge this.** Reply in `channel/to_bot_team/` (new file, see `channel/README.md`) with what
you agree with, disagree with, or have counter-evidence for. Section 9 lists the claims that matter most.

## 0. Data

- 135 unique counted tables (rounds 1-54, 135,000 hands): the union of our three accounts' downloads
  (Red, WBot, kaiserbot), de-duplicated by (round ref, seat names). Every hand sums to zero; our seat's
  totals match the official per-round chips exactly (665 team-rounds checked, max diff 0).
- The repo's own `Hand_data/` gives 91 unique tables. Running the scripts on it gives slightly different
  numbers. The 135-table outputs are committed. The missing raw files are in Matthias's local
  `poker_bot/hands*/` and can be added on request (~600 KB each).
- Official standings: a per-minute archive of the public leaderboard for rounds 13-48
  (`data/leaderboard_history_r13_r48.csv`) gives **every team's exact result in every round 14-48**, not
  only the tables we sat at. This is the best data we have on noise.
- Final Saturday standings and the Sunday buckets: `data/final_standings_saturday.json`,
  `data/sunday_buckets.json` (public API, 21:53).

## 1. Facts to know first

- **Sunday seeding is a snake by Saturday rank**, 4 tables, 36 rounds, top 2 per table go through.
  **WBot is on table 4:** Resonance Qt (seed 4), Anker Batteries (5), Chinese people can fly (12),
  WBot (13), GamesGone (20), Poke (21), Anton (28), YSL_TWIZZY (29).
- Red, kaiserbot, AAST and SmartBGerBot were in the 19:00 standings (48 rounds) and are gone from the
  final ones (team merge for us). 31 teams were seeded.
- Round 41: SmartBGerBot lost **-1,552 bb/100** at one table (looks broken). That table handed
  The Market Makers +409, Attention Is All In +302, Durahim +281 and JoCal +271. The Market Makers'
  +409 alone is ~7.6 bb/100 of their 54-round average.
- ediz_slow (VPIP 77, limps 33%) lost -264 bb/100 over 13 rounds and left after r31. clanker
  (-97.5) played 31 rounds. Both are absent on Sunday.

## 2. Noise vs skill: what a result means

| quantity | value |
|---|---|
| SD of one team's bb/100 in one 1,000-hand round | **~45 typical; 65 pooled** (the broken-bot tables inflate it) |
| SD of true skill across teams | **~16 bb/100** |
| skill share of one round's variance | **~6%** |
| split-half reliability (odd vs even rounds, 37 teams) | 0.53 for half the rounds -> 0.69 for all 54 |
| first half (r14-31) vs second half (r32-48) team-mean correlation | 0.39 |
| SE of a 54-round Saturday average | **±8.8 bb/100** |

Consequences:
- Only the top 2 (Attention ~45, Gherkers ~43) and the bottom ~6 are clearly separated. **Ranks ~5-25 cannot be told apart.**
- A single live round tells you almost nothing (±45). Judging a version from 3-5 live rounds is still about ±20-25.
- A robust re-rank (10%-trimmed mean, r14-48) moves FisherMen 6 -> 3, Claudebot 14 -> 6 and The Market Makers 3 -> 5.

## 3. Is it rock-paper-scissors? No. Skill is transitive.

Pairwise flows: in every hand, each winner's gain is split across the losers in proportion to their
losses. That gives the net chips team A won from team B per 100 hands played together. 765 pairs have
2,000 or more hands together.

- Model "pair rate = s_A - s_B" (one skill number per team): residual chi2/df = **1.21** (1.0 = pure
  noise). 1 pair beyond |z|>3, against ~2 expected by chance.
- 7 triads have all three edges significant (|t|>2). **0 of them are cyclic.**
- The fitted s correlates **0.93** with the leaderboard.
- The small excess over noise (1.21) is consistent with teams uploading new versions during the day
  (Gherkers made 11 uploads in r13-48). The data show no material strategy-vs-strategy cycle.

**So there is a "better strategy overall".** Your result at a table is close to the sum of 7 independent
pairwise edges. A counter-strategy aimed at one opponent pays off only against that seat and costs
against the other six, and the opponents don't adapt to you specifically. In an 8-max field of fixed
bots the game reduces to "extract the most from whoever leaks, leak the least yourself".

## 4. Where the money comes from

- Winners' profit is mostly donors' losses. Share of net flow taken from the 7 worst bots: Attention
  55%, Gherkers 58%, The Market Makers 59%, Resonance 48%, Anker 48%, FisherMen 33%.
  **WBot 111%: WBot lost slightly, in aggregate, to everyone except the donors.**
- Result at tables with at least one of the 7 worst bots vs with none:

| account | with donors | no donors |
|---|---|---|
| Attention Is All In | +48.0 (15 tables) | +34.6 (7) |
| Gherkers | +51.9 (12) | +28.2 (12) |
| The Market Makers | +47.9 (15) | +3.6 (7) |
| FisherMen | +29.4 (15) | +16.7 (10) |
| WBot | +21.3 (40) | **-9.3 (14)** |
| Red | +6.3 (34) | -9.8 (18) |
| kaiserbot | +12.3 (35) | -0.2 (18) |

  The no-donor columns are small samples (±12 or worse).
- Edge vs the top 21 teams only, scaled to a table of 7 such opponents: Attention +32.5 ±12,
  AAST +30.6 ±11, FisherMen +25.5 ±11, Anker +16.6 ±10, Resonance +14.7 ±11, kaiserbot -6.3 ±8,
  **WBot -18.0 ±11, Red -22.6 ±9** (`out_03_bucket_edges.txt`).
- WBot's average fell from +26.9 (r14-31) to +4.5 (r32-48), after ediz_slow left and clanker was gone.

## 5. Style vs result (35 ranked teams, final bb/100)

| stat | corr with final bb/100 |
|---|---|
| went to showdown / saw flop (WTSD) | **-0.61** |
| won at showdown (W$SD) | **+0.60** |
| post-flop aggression | +0.36 |
| fold to post-flop bet | +0.35 |
| VPIP / PFR / 3-bet | -0.02 / +0.17 / 0.00 |

- The winners go to showdown rarely (~23%) and win there (~59%). Their profit is at showdown
  (Attention +56 at showdown, -12 without one). They are paid off by callers; they don't win by bluffing.
- Attention Is All In is the only bot that wins from the big blind (**+44**). Red lost **-91** in
  the BB and -56 in the SB.
- WBot: WTSD 32%, W$SD 47%, AF 87%, **median post-flop bet 18% of pot**. Red: WTSD 32%, W$SD 43%,
  loses at showdown (-11).
- How loose a bot plays doesn't decide its result. Profitable bots range from VPIP 19% to 36%.

## 6. Sunday table 4

Opponent styles (Saturday, every table we saw):

| team | LB | VPIP | PFR | 3b | limp | fold to bet | AF | WTSD | W$SD | read |
|---|---|---|---|---|---|---|---|---|---|---|
| Resonance Qt | +24.0 | 22 | 16 | 12 | 0 | 39 | 57 | 24 | 52 | solid |
| Anker Batteries | +23.1 | 23 | 17 | 13 | 0 | 46 | 61 | 24 | 58 | solid |
| Chinese people can fly | +13.6 | 36 | 22 | 7 | 0 | 46 | 63 | 27 | 51 | loose, profitable |
| GamesGone | +5.0 | 26 | 16 | 3 | 0 | 43 | 69 | 27 | 44 | loses at showdown (-19) |
| Poke | +4.5 | 34 | 16 | 4 | **10** | **55** | 78 | 27 | 51 | limper, over-folds to bets |
| Anton | -20.4 | 32 | 26 | **25** | 3 | 47 | 59 | 38 | 48 | 3-bet maniac; **-33 -> +17** in 2nd half |
| YSL_TWIZZY | -20.6 | 21 | 16 | 4 | 0 | **26** | 39 | **45** | 53 | calling station |

WBot's head-to-head with each of them (bb per 100 hands together; first number = model shrunk toward observed):
Resonance +3.5 (obs +8.8 ±6.7), Anker -5.5 (-9.9 ±7.0), Chinese -5.4 (-15.7 ±8.3), GamesGone +5.6
(+16.0 ±10.1), Poke +6.6 (+33.3 ±13.3), Anton +1.9 (+1.3 ±7.6), YSL +4.0 (+7.4 ±7.7).

P(top 2 after 36 rounds). Assumptions: per-round SD 45, plus SD 10 of uncertainty in every team's true
Sunday edge (estimation error and overnight uploads). The other seats use their Saturday bots.

| our seat | expected bb/100 | P(top 2) | favourites |
|---|---|---|---|
| WBot (as on Saturday) | +10.8 | **~29%** | Anker +29.6 (88%), Resonance +22.9 (75%) |
| kaiserbot | +12.4 | ~34% | |
| Red | -17.0 | ~0% | |
| AAST-like (reference, not ours) | +23.9 | ~69% | |

**Needed edge:** P(top 2) is ~27% at +10, **~51% at +20**, ~75% at +30.
Read this as a rough model, not a forecast. It shows the bar: **a bot that wins about +20 bb/100 at
this table is a coin flip to go through; WBot as it was is about 1 in 3.**

## 7. Implications for the per-opponent context model (SCOUT / FORGE)

- **A single pooled opponent fold rate is wrong at this table.** Fold-to-post-flop-bet ranges from 26%
  (YSL_TWIZZY) to 55% (Poke): about a 2x gap in the main bluff/value input.
- Sample size inside one 1,000-hand round: each table-4 opponent faces ~115-220 post-flop bets per
  round. A per-opponent fold rate reaches about **±4 points by the end of a round** and about ±8 after
  ~250 hands. A 3-4 bucket split by bet size or HU/multiway costs about 2x in SE per bucket. Use
  shrinkage (per-opponent estimate pulled toward the opponent's pooled rate, then the field rate),
  not raw per-bucket frequencies.
- Some opponents can be identified early from behaviour (the bot doesn't get names): Poke's 10% limps,
  Anton's 25% 3-bets, YSL's showdown rate. That is enough to switch exploit modes within a round.
- Testable exploits (frequency evidence only, not yet profitability evidence; verify in the arena with
  clones):
  1. vs YSL-type (low fold-to-bet, high WTSD): thinner value bets, larger value sizes, no bluffs.
  2. vs Poke-type (folds 55% to bets, limps): bet/raise more often when checked to; isolate limps.
  3. vs Anton-type (25% 3-bet): widen 4-bet value and call 3-bets wider in position; don't fold
     medium-strong opens at 3-bet frequencies built for a solid field.
  4. vs Resonance / Anker (solid): don't pay off. They win at showdown (W$SD 52-58%).
- WBot's 18%-of-pot median bet extracts little from stations and gives cheap prices to solid bots.
  Bet sizing deserves its own one-factor test.

## 8. Recommended approach for tonight

1. Gate candidates on **table 4's field**, not the Saturday field average. Build an arena field from
   clones of these 7 opponents (the repo already has clone tooling) and give it its own seeds.
2. Target **+20 bb/100 or better at that table**. Smaller gains don't change the outcome much.
3. Base before exploits: cut showdown calling with medium hands and fix blind defence, then add
   per-opponent adjustments with shrinkage.
4. Trust no live result under ~10 rounds. On Sunday, 36 rounds give ±7.5 per team.

## 9. Claims I most want challenged

1. "No rock-paper-scissors" (section 3). Do your arena results show any candidate that beats A but loses to B while B beats A?
2. "WBot's edge is almost entirely donor-driven" (section 4). Does your own WBot analysis agree?
3. The table-4 favourites (Anker, Resonance) and the ~+20 bar (section 6).
4. The pairwise attribution (proportional split of each pot's losers) is an approximation. Better attribution ideas are welcome.
