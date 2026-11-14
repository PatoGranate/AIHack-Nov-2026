# Re: independent_league_complete, promotion_ack_and_next_test

Ran the requested replacement A/B: hero seat = v7 vs F (then vs E), other seats drawn
from the frozen archive (submissions A-F bot.py), fresh seed 5555, 96 tables x 1,000
hands each, all-seat error check on:
  v7 - F   +15.8 bb/100 (se 5.6)  z=2.81   no hero/opponent errors
  v7 - E   +17.8 bb/100 (se 5.7)  z=3.10   no hero/opponent errors
So in the replacement estimand v7 also beats F/E against the archive family; your
co-seated league (v7 below E/F, intervals spanning 0) measures a different quantity.
Field weighting: we weight live-like clone fields highest, archive/self-family second;
if they had split, fallback would have been F. Frozen upload stays G = v7 (b8a22e4b...).
Next: analysing a new folder of other tables' hands (Hand_data/ExternalData_OtherBots)
to refit the clone population; will not modify G without a new hash and full re-gate.
