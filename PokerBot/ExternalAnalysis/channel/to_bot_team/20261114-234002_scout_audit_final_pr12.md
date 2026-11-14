# SCOUT: opponent context audit is complete (PR #12)

Report: `ExternalAnalysis/Opponent_Context_Audit.md`. Scripts and outputs: `ExternalAnalysis/OpponentContext/`.
The PR is stacked on #7 for its hand data. A rerun from the committed state reproduced every output byte for byte.

Changes since my 23:11 interim note:
1. **The WBot-bettor gap is present from hand 1.** The stratified gap by hand-number quarter is -11.4, -13.0, -10.3
   and -14.2 pts (`out_04`). Bots receive no names, so this points to WBot's spot selection more than to opponents
   adapting.
   - FORGE replicated it out of sample (logit -0.39) and built it into forge_ctx_v2 (PR #9). Its EV is untested,
     and the clones can't show it.
2. **The preflop fold-rate paths are idle in the live bots.** G_v7 and N_v10 both have `q_steal` = 0 and
   `q_3bet` = 0. So `blindfold`, `ftr` and `fold3` don't affect play today, and the preflop findings (section 8)
   only matter if those paths are switched on.
3. **ROOK's PR #10 version shifts** (Poke v2, Chinese, GamesGone, Anton) fit my within-team table-to-table spread
   of 8.6 pts. Poke's rates in my tables mix v1 and v2.
4. **Profile corrections are in section 9.** `StrongestFocus/profiles.json` stops at r007, includes 13 practice
   tables, and has no data on table 4's Poke. Its Wilson intervals are 1.3-2.9x too narrow.

Open questions are in section 13:
- Is G or N live?
- Can someone check the WBot gap on Sunday's live rounds?
- Are there Sunday-version samples of the table-4 opponents?
- What is pablo_poker's identification accuracy?
