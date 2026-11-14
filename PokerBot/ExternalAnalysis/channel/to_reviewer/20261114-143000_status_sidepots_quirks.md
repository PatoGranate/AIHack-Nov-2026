# Status 14:30: side pots in, quirk experiments running

- Side-pot layering applied (bet EV and call EV; contribution = start - stack). Your
  A/B/hero case and 6 others pass exactly (tools/test_sidepot.py). Paired A/B vs the
  same params without it: +8.3 bb/100 (se 4.6) on the real-clone field.
- Retuned fixed model accepted 2 changes: c_mid 0.88->1 with o_co .45; bet_sizes
  [.6,1,1.5]->[.33,.6,1] with o_sb .6->.487 (screen+confirm z 3.0 and 2.8; we know these
  are adaptive-search z's, hence the held-out check below).
- Now testing 5 switchable "quirk" exploits against LLM-built bots, each vs the same bot
  with it off, on real-clone / held-out-jittered / strong fields (200 tables x 300 hands):
  late-position steal vs overfolders, light 3-bet vs openers who overfold, river
  overbet sizes, tiny value-bet size, OOP check-raise trap vs aggressive bettors.
  Only sizes are added as candidates for the bet-size quirks: EV still chooses.
- Then: final untouched-seed comparison of the best build vs F (old code) and E (live v3).

Thoughts welcome on which quirks you expect to fail against real bots but look fine
against ParamBot clones; that is our biggest blind spot.
