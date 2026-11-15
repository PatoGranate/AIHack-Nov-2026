# Re: PR #7 review (changes requested on b3097de): post-mortem revision 2

From: Matthias's Claude session. Report: `ExternalAnalysis/Saturday_Field_Postmortem_20261114.md` (revision 2); the changelog is at the end.

1. Reproducibility: the 60 missing rounds (Red r24-54, kaiserbot r24-53, WBot r54) are committed to the existing
   `Hand_data` folders. `00_manifest.py` writes `data/input_manifest.csv` (159 files: SHA-256, dedup key, used or
   duplicate; 135 unique tables). Exact commands and environment are in the report. All outputs were regenerated
   from committed inputs only, with the same numbers up to floating-point rounding.
2. Inference: accepted. Section 3 now reads "exploratory additive model, no cycles detected, low power". The
   independence and "better strategy overall" claims are removed. New `06_robustness.py`:
   - multi-winner hands are 0.3% of chips lost, so the allocation rule barely matters and the remaining limit is
     interpretation;
   - table-bootstrap SE / per-hand SE has median 1.01 on the 142 pairs that met at 6 or more tables;
   - 0 triads are testable under bootstrap SEs;
   - donor and top-21 figures now carry 90% intervals and are labelled allocation-dependent. The attribution-free
     with/without-donor table has intervals as well.
3. Forecasting: accepted. Draws are zero-sum, the edge scenario rebalances the other seats, and a sensitivity grid
   over tau, skill SD and round SD is added:
   - WBot's P(top 2) is 22-34% under the additive model, 59-66% if raw head-to-heads are taken at face value;
   - the edge needed for 50% is +12 to +20 under the additive model, +36 to +38 with raw head-to-heads.
   The "+20 target" is removed and the results are labelled illustrative. Sources for the rules:
   `PokerBot/kit/README.md:169-170` (top two by chips) plus the API's `sunday.stages[0] = {rounds: 36, advance: 2}`
   and the 20:46 announcement.

Opponent profiles stay available to SCOUT/FORGE as descriptive inputs (sections 6-7).
