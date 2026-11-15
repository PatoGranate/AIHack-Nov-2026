# SCOUT: after round 5, WBot is 7th of 8. Which bot went up, and when?

Public feed at 09:23 UTC, 5 of 36 rounds played. Table 4, cumulative bb/100: Anker +42.9, Resonance +9.5,
Poke +4.9, Anton +0.6, Chinese -2.2, YSL -8.4, **WBot -19.1**, GamesGone -28.2. 2nd place is 28.6 bb/100 ahead,
with 31 rounds left.

- From the cumulative chips (+2,214 after r3, -19,055 after r5), **WBot's rounds 4-5 averaged about -53 bb/100**,
  against +3.7 over rounds 1-3.
- Noise (about ±45 bb/100 per round, from the post-mortem):
  - r4-5 vs r1-3: z ≈ -1.4;
  - the 5-round mean vs Saturday's +13.4: z ≈ -1.6.
  - **Not significant on its own.**
- **Timing matters, though.** FORGE refers to `G_profile_td_r003` as live. If a new build went up before r004, the
  drop coincides with a bot that has only clone evidence (+4.8 ± 1.9 on Table D clones; FORGE's L1 is still
  running). G has 54 real Saturday rounds behind it.
  - Under that asymmetry, the conservative default is the bot with real-opponent evidence, unless the new one shows
    a real-round reason to keep it.
  - That decision is the orchestrator's and Matthias's.
- **Ask (whoever has the data token):**
  1. Confirm which file is uploaded, and before which round.
  2. Post per-round WBot bb/100 and timeouts for r001-r005.
  3. Run `OpponentContext/06_sunday_check.py` on the Sunday round JSONs, which now meet its 5-table minimum.
- **Correction to my 09:22 note:** the "WBot v9" there comes from the feed's *Saturday* standings block. The
  feed exposes no Sunday version, so it can't confirm the live bot. The opponents' version numbers in that note
  come from the same block. They are the latest uploads as of Saturday's close, not confirmed Sunday versions.
