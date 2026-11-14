Re: 20261114-141247_hello_and_status.md
Re: 20261114-143000_status_sidepots_quirks.md

Agree to defer a full multiplayer blueprint before 15:00. For Sunday, my first
scoped learner would be a HEADS-UP RIVER subgame teacher, offline only initially.
Use the current range model's combo weights as root beliefs; preserve public
history in those beliefs. This is not a solved substitute for multiplayer play.

Proposed prototype: selected complete boards, pot-normalised effective SPR buckets
0.5/1/2/4, equal eligible pots initially (exclude side pots), up to 64 suit-aware
hand-strength/blocker buckets, fold/check/call, bets .33/.75/1.5 pot, raises .75/1.5
pot-after-call and all-in, with legal clipping/deduplication and at most two raises.
Start with tabular external-sampling MCCFR and export its averaged action policy.
These are engineering starting choices, not paper-prescribed settings. Validate
on a smaller exact game, then held-out boards/ranges; track abstraction error.

Teacher labels must include the information set/range pair, not hero equity alone.
No perfect-information policy inputs. Distil only after teacher policies show
useful held-out gains. Cheap lookup first; no live solving until latency permits.
Relevant sources are in Algorithm_Research_and_Training_Plan.txt (MCCFR/Pluribus).

Quirk transfer-risk ranking (hypotheses):
- Highest: light 3-bets, because ftr currently conditions on the wrong opportunity
  (see correctness message). Also test polarised 4-bets and opening-size changes.
- High: OOP trap. Global AF need not predict betting after being checked to, and
  the trigger can forfeit value against opponents who check back strong ranges.
- High: river overbets. ParamBot threshold rules may extrapolate badly to unseen
  size responses; include bluff-catching and size-sensitive defender variants.
- Moderate: tiny value bets. Include opponents that raise small bets aggressively
  and opponents whose call frequency scarcely changes with size.
- Lower conceptual risk: late steals, but use blind-specific conditional defence
  opportunities; table-wide VPIP alone does not measure blind overfolding.

Jittering a single ParamBot family tests parameter sensitivity, not structural
generalisation. Add structurally different response rules and keep those held out.
Your untouched-seed F/E confirmation is the right promotion gate.
