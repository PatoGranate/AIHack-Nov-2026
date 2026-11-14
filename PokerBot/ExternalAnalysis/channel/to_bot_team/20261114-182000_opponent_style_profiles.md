# Observed opponent profiles for training/exploit tests

I have saved a full profile table for all 43 opponent names present in the local WBot round histories through r038 at `ExternalAnalysis/ExternalBot_Profiles_20261114.md`. It reports sample sizes and definitions for VPIP, PFR, 3-bet, fold-to-raise, and postflop aggression. WBot copies do not include opponent version IDs; use team-name aggregate unless you have version-tagged snapshots. Kaiserbot and Red do have separate version-tagged external archives.

Most actionable current pattern candidates (not yet proven profitable exploits):
- Red v3 (12k version-tagged hands): tighter VPIP/PFR than v2 (18.0/12.0 vs 23.7/17.9), 85.1% fold after a preflop raise, and 80.6% postflop raise share. Test position- and sizing-conditioned steals, but avoid extrapolating the aggregate fold rate blindly.
- Kaiserbot v9 (3k hands): 22.6 VPIP / 10.1 PFR, only 44.8% of VPIP hands raised, 4.3% 3-bet, 75.8% fold facing preflop raise, 65.2% postflop aggression share. This is more call-heavy preflop than Red; test value-oriented isolation separately.
- Gherkers: 6k seen hands at 22.8/16.7 VPIP/PFR, 9.8% 3-bet and 70% postflop aggression. Attention Is All In: 8k at 26.5/18.0, 8.8% 3-bet and 71.8% postflop aggression. Both show pressure, but Attention enters more often. AAST has only 2k observed hands so keep its label provisional.

These are pooled across seats/stacks and can mix versions. Do not change the live policy from these aggregate rates alone; use them to define segment-specific hypotheses and test on independent tables/seeds. Rates and additional teams are in the linked report.