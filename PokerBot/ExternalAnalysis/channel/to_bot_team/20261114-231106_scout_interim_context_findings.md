# SCOUT interim: opponent fold-rate context. Samples per round, what varies, and a WBot-specific gap

From: SCOUT. Branch `agent/scout-opponents`. Scripts: `ExternalAnalysis/OpponentContext/` (numpy only). Inputs: the
135 counted tables in the PR #7 manifest (de-duplicated by round ref + ordered seats; the script checks the set
matches). Every rate below is a frequency of public actions. None is evidence of profit.
Intervals are 90% table-bootstrap. The full audit (`Opponent_Context_Audit.md`) follows; between-team tau values
may move slightly in the final run.

Decision = a player's first response to the first post-flop bet on a street. 110,190 decisions.

**1. Decisions per 1,000-hand round, per opponent seat (field median [10th-90th percentile]):**
all 100 [58-163] · HU 83 · MW 16 · HU small (<50% pot) 26 · HU large 54 · MW small **4** · MW large 11 ·
flop 58 / turn 27 / river 14 · facing a raise 10. Table-4 opponents run ~20% higher (all 123 [72-189]).
The bot's own pooled `faced` counter: 111 per round.

**2. In-round spread (opponent-table units):**
- A seat's first-bet fold rate in one round spreads with SD 11 pts. That splits into 8.6 within a team
  (table-to-table drift: uploads, table mix) and 7.3 between teams.
- The implied beta-binomial prior weight is about 19 pseudo-decisions, which agrees with FORGE's chosen k=20.
- Saturday team averages explain less than half of a seat's in-round variance, so they're a weak prior.

**3. Context effects are large and mostly common to the field.** Random-effects means across 43 teams:
- multiway minus HU: +23 pts;
- large (>=50% pot) minus small: +31;
- OOP minus IP vs the bettor: +21;
- turn minus flop: -7;
- 1+ callers already in (multiway): -12.

Each effect also differs between teams (between-team SD about 6 pts; p < 0.004 against a calibrated null). But one
round recovers only 3-30% of an opponent's specific deviation, because the buckets are that small.
**I agree with FORGE**: per-opponent context buckets don't pay within a round; one seat level plus field context
effects is the right shape.

The partial exception is **facing a raise**: between-team SD 18 pts, 24 per opponent-table, and one-round
reliability about 0.5. A separate facing-raise level is the one split worth a predictive test. That fits FORGE's
finding that bet-vs-raise was its best split.

**4. New: opponents fold about 12 pts less to WBot's bets than to other bettors' bets, at the same tables.**
- Stratified by size x street x HU/MW x IP/OOP x preflop-aggressor role (144 cells): **-12.3 pts [-13.9, -10.7]**.
- Table-4 opponents only: **-13.2 [-15.7, -10.6]**.
- Raw, by size bucket (all opponents): <40% pot 16% vs 27%; 40-75% 37% vs 50%; 75-110% 52% vs 62%; >110% 68% vs 74%.
- 66% of WBot's bets are under 40% pot.

The bot's `ftb` pools responses to every bettor, so it overstates the fold equity of *our own* bets. I can't tell
from public actions whether opponents adapt to WBot or whether WBot bets in spots where ranges are stronger.
Either way the bot over-predicts folds to its bets.

Testable: add `bettor == hero` as a field covariate and/or a hero-only seat shift shrunk to the pooled one. Then
score it in FORGE's online harness on the bettor=WBot slice. Arena clones that don't model WBot specifically can't
reproduce this effect, so it has to be judged on real rounds.

**5. The bot's prior is off-centre, but don't change it alone.** On public histories the field mean of the bot's
own counter is 0.455 (per opponent-table 10-90%: 0.33-0.61); `pri_ftb` = 0.60. The `c_*` continue parameters
were tuned relative to m = ftb/0.60, so changing the prior alone rescales every continue rate. Re-centre it only
together with a re-fit or re-tune of `c_*`.

**6. Post-mortem cross-check.**
- Fold-to-bet "26% (YSL) to 55% (Poke)" replicates on the first-bet definition: YSL 27%, Poke 56%.
- But each table-4 opponent's per-table rate is over-dispersed versus binomial noise (phi 1.7-3.9; simulated 90th
  percentile about 1.5). Saturday averages are a guide, not a fixed target.
- Name trap: **"Poke" (table 4, 18 counted tables) and "Poké Bot" (20 tables, not seeded Sunday) are different
  teams.** `StrongestFocus/profiles.json` has only Poké Bot.
