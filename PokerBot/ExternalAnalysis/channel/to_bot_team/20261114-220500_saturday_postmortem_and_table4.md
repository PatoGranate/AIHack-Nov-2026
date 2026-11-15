# Saturday post-mortem + Sunday table 4: please review and reply

From: Matthias's Claude session (Red/kaiserbot side). Full report: `ExternalAnalysis/Saturday_Field_Postmortem_20261114.md`,
reproducible scripts and outputs in `ExternalAnalysis/SaturdayFieldPostmortem/`. Branch `agent/saturday-postmortem`.

**Superseded interpretation:** this historical dispatch predates revision 2 and the independent
version-split review. Points 2, 4 and 5 below must not be used as current conclusions: cycles were not
detected in a low-power exploratory analysis; donor dependence is descriptive with wide intervals;
and the Sunday scenarios pool G/I/likely-N inputs rather than forecasting frozen G. See the corrected
report, especially sections 3, 4 and 6. The original text is retained below as a record of the request.

Original headline points (historical):
1. Sunday is snake-seeded. **WBot's table 4:** Resonance Qt, Anker Batteries, Chinese people can fly, GamesGone, Poke, Anton, YSL_TWIZZY. 36 rounds, top 2 go through.
2. No rock-paper-scissors: pairwise flows fit one transitive skill number per team (chi2/df 1.21, 0 of 7 significant triads cyclic, corr 0.93 with the leaderboard).
3. Noise: one round is ±45 bb/100. Skill is ~6% of one round's variance; Saturday ranks ~5-25 can't be told apart.
4. **WBot's Saturday profit came entirely from donors** (111% of net flow). WBot vs the top 21: -18 ±11. At tables with no donors: -9.3.
5. Table 4 model: Anker and Resonance are favourites. WBot as it was has ~29% to finish top 2. ~+20 bb/100 at this table is a coin flip.
6. Context model: fold-to-bet at table 4 ranges from 26% (YSL) to 55% (Poke). A pooled fold rate is wrong. A per-opponent rate reaches ±4 pts within one round, so use shrinkage for finer buckets.

Asks:
- Challenge section 9 of the report, especially points 2 and 4 above, against your own data and arena results.
- Tell us if you have Sunday-table clones or a better pot attribution than the proportional split.
- Reply with a new file in `to_reviewer/` or here (`to_bot_team/`), one topic per file.
