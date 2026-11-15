# Matched-budget I vs G simulation

**Status:** local paired simulation only; not a live submission or runtime certification.

## Setup

- Candidate `tools/cands/srv_I.py` (I strategy, SHA-256 `117adab218b509302b805f5cdf2066054ea60cb1de382082a4ab37fc7ce99b89`). It differs from `submissions/I_v9_25ms/bot.py` only in timing/bank parameters: max_ms 1.2, hard_ms 2.8, bank 1.4 instead of 6.0, 14.0, 7.0.
- Baseline `tools/cands/g_matched_srv_i.py` (G strategy from `submissions/G_v7_final/bot.py`, SHA-256 `7e7f7c7e68b1af3e27b835dae211190b13d4d84d52f12094b055fe1bfb6fdb4d`). It keeps G policy settings and changes only max_sims 1500->4000, hard_ms 3.0->2.8, bank 8.5->1.4; max_ms was already 1.2. This matches the I run caps/bank and simulator cap.
- Pairing: `tools/arena.py`, same cards and sampled opponents for each candidate/base pair; 320 tables x 300 hands in real/late/heldout blocks, plus 64 tables x 1,000 in the archive screen; one seed per row. Fields are local `real`, `late`, `heldout` opponent clones. No ERR/WARN output.
- This estimates the effect of the two strategy snapshots under one matched local budget; it does not certify website version mapping. README and user mapping conflict for rounds r049-r053; exact deployed G source hash remains unconfirmed.

![I minus G results by field](I_vs_G_Matched_Budget_20261114.svg)

## Results

| Field / seed | I return | G return | I - G (bb/100) | SE | z |
|---|---:|---:|---:|---:|---:|
| real / 6901 | +32.3 | +24.8 | +7.5 | 4.2 | 1.79 |
| late / 6902 | +22.4 | +13.5 | +8.9 | 4.1 | 2.17 |
| heldout / 6903 | +32.3 | +18.6 | +13.8 | 4.5 | 3.07 |
| real / 6904 | +24.3 | +14.0 | +10.2 | 4.0 | 2.55 |
| heldout / 6905 | +43.8 | +35.4 | +8.3 | 4.3 | 1.93 |
| late / 6906 | +9.2 | +7.1 | +2.1 | 4.3 | 0.49 |
| archive / 6907 | +29.1 | +18.6 | +10.6 | 8.3 | 1.27 |

## Readout

- I outperformed matched G in all seven blocks, including the archive screen (+10.6/SE8.3). Real-field results were +7.5/SE4.2 and +10.2/SE4.0; heldout +13.8/SE4.5 and +8.3/SE4.3; late +8.9/SE4.1 and +2.1/SE4.3. Late seed 6906 was close to even; each block is a noisy estimate.
- The repeated real/heldout positives make I a strong candidate for a frozen server-equivalent release gate. This still does not validate a live switch: source identity, deadline/fallback behavior, and a final untouched field gate are required.
- Since both candidates used the same max_ms, hard_ms, bank and max_sims, the difference is not explained by those compute settings. It reflects the different strategy snapshots as a bundle; this test does not identify which I parameter caused the gain.
- Do not claim this proves I beats G online. It is evidence to prioritize I for the next controlled gate, with current G retained as rollback.
