# Rook: Sunday clone-fidelity audit

Assignment: `channel/to_bot_team/20261114-231500_rook_sunday_clone_fidelity.md`. Branch `agent/rook-sunday-clone-fidelity`, based on `main`.

- **Old field:** `tools/opponents/real/` is unchanged.
- **New field:** `tools/opponents/sunday_v2/` sits alongside it, with its own `MANIFEST.json`.
- **Limits:** these clones copy public action frequencies only. They do not reproduce any opponent's actual code or strategic strength.

## Data and method
- **Data:** PR #7 head `f7fbac4` Hand_data, 159 files deduplicated to 135 counted tables using the PR #7 rule (ref + ordered players, practice rounds skipped). Each team's displayed version per round comes from `leaderboard_history_r13_r48.csv`.
- **Statistics:** computed with the same `tools/analyze.py` that generated the old clones (`make_clones.py`), so the definitions match.
  - Statistics are pooled over each opponent's tables, so these are aggregate profiles, not per-opponent tendencies.
  - ± values are binomial SEs per opportunity. They **understate** the true uncertainty, because hands cluster within tables and rounds.
- **"Latest version" window:** rounds where the team's displayed version at the previous and current leaderboard rows both equal its version at played = 48. Rounds 49–54 are included **by assumption**, since there is no per-round version data after r48.
- **Commands** (from `PokerBot/`):
  ```
  python tools/rook_clone_fidelity.py <DATA_ROOT>            # audit table (read-only)
  python tools/rook_clone_fidelity.py <DATA_ROOT> --write    # writes tools/opponents/sunday_v2 + MANIFEST.json
  python tools/rook_clone_behaviour_check.py tools/opponents/<field> <tmp_out> 2 1000
  ```
  `<DATA_ROOT>` is a `PokerBot/` checkout at PR #7 `f7fbac4`.
- **Outputs:** `rook_clone_fidelity_out.txt`, `rook_clone_fidelity_data.json` and `rook_clone_behaviour_check_out.txt`, all in this folder.

## Old clones (tools/opponents/real)

| Opponent | File | sha256 (first 16) | Old calibration sample |
|---|---|---|---|
| Poke | `r_Poke.py` | ef508b9fa4239036 | 8,000 hands |
| Resonance Qt | `r_ResonanceQt.py` | ac23638b64446fd2 | 17,000 |
| Anker Batteries | `r_AnkerBatteries.py` | 2afe4690ad384853 | 14,000 |
| Chinese people can fly | `r_Chinesepeoplecanfly.py` | dd6dfa7e1405d5e5 | 16,000 |
| GamesGone | `r_GamesGone.py` | 13239ee0fef1f351 | 16,000 |
| Anton | `r_Anton.py` | 7cc6f1522b8f780c | 16,000 |
| YSL_TWIZZY | `r_YSLTWIZZY.py` | 95ad7cb10ebd4fb9 | 15,000 |

The old clones were fitted only from tables WBot saw, at the time `make_clones.py` was last run. Its round window was not recorded.

## Ranked gaps

### 1. Poke: stale calibration, the worst gap
- **Old target:** VPIP 0.22, PFR 0.13, AF 0.39, no limps (8,000 hands).
- **All Saturday:** VPIP 0.337 ± 0.004, limp 0.197, AF 0.535.
- **Latest v2** (12 tables, r22–54): VPIP **0.426**, PFR 0.175, limp **0.293**, AF 0.578, FTB 0.546.
- **Cause:** a real behaviour change, by far more than sampling noise. The new v2 is a loose limper.
- **Tool limitation:** the mapping only enables limping when the limp rate is above 0.25. On the all-Saturday pool (0.197) it would still produce **no limps**. The new clone is calibrated on v2 (0.293), so it limps.

### 2. Chinese people can fly and GamesGone: postflop aggression dropped in the latest version
| | Old AF | All Saturday | Latest version |
|---|---|---|---|
| Chinese people can fly | 0.45 | 0.442 | **0.271 ± 0.009** (v17, 7 tables) |
| GamesGone | 0.51 | 0.505 | **0.307 ± 0.017** (v12, only 2 tables) |

- Chinese' latest-version profile is calibrated in `sunday_v2`.
- GamesGone's latest version has only 2,000 hands, below the 4,000 minimum, so `sunday_v2` **keeps the pooled profile, which is likely stale**. Re-fit it once more v12 hands exist.

### 3. Anton: changed versions
- **Latest v7** (4 tables): VPIP 0.27 (vs 0.32), 3-bet 0.29 (vs 0.25), AF 0.40 (vs 0.29), FTB 0.55 (vs 0.44).
- Moderate shifts, only 4 tables. Calibrated to v7 in `sunday_v2`.

### 4. Resonance Qt, Anker Batteries, YSL_TWIZZY: old clones are still accurate
- Every old-vs-new difference is within sampling noise, or ≤0.03, except Resonance AF (0.36 → 0.39).
- Resonance's latest v12 has only 3 tables, so it uses the pooled profile.
- YSL_TWIZZY's latest FTB is 0.234, below 0.25, so its new clone gains `air_call`.

### 5. Structural: the ParamBot mapping does not reproduce its own targets
The **4,000 table-hand** behaviour check ran both fields, each with 2 tables × 1,000 hands (7 clones plus a passive check/fold observer). It showed:

- **3-betting too often:**
  - Anton: target 0.25 / 0.29, realised 0.34 / 0.36.
  - Resonance Qt and Anker Batteries: targets 0.11–0.12, realised 0.16–0.18.
- **Anton far too loose:** VPIP target 0.27–0.32, realised 0.45–0.46.
- **Old Chinese clone too tight:** target VPIP 0.36, realised 0.24. The new clone realises 0.31 against a 0.33 target.
- **Postflop aggression and fold-to-bet** are off by about ±0.1–0.15 on several clones, both above and below target (e.g. new Poke AF 0.69 vs 0.58, new YSL FTB 0.17 vs 0.23).
- **The observer seat biases the test:** it always folds, so these tables are effectively 7-handed with one guaranteed folder. That biases opening and stealing upward. Treat these numbers as indicating direction, not as calibration.

The gaps in this section are **tool error**, separate from the stale calibration in sections 1–3. Recalibrating the inputs fixes Poke's limps and looseness but not these.

## New field: tools/opponents/sunday_v2
- **Mapping:** a verbatim copy of `make_clones.py`. Each clone is calibrated on its latest version when that version has ≥4,000 hands, otherwise on all Saturday tables.
- **Files:** listed in `MANIFEST.json`, with per-file sha256 values, the generator's sha256 and each clone's calibration window.

| Clone | Calibrated on |
|---|---|
| Poke | v2 |
| Anker Batteries | v4 |
| Chinese people can fly | v17 |
| Anton | v7 |
| YSL_TWIZZY | v6 |
| Resonance Qt | all Saturday |
| GamesGone | all Saturday |

**Old pilots stay reproducible.** `tools/opponents/real` and `tools/make_clones.py` are untouched. Note that `make_clones.py` **deletes** `tools/opponents/real/r_*.py` every time it runs, so it was not used.

## Recommended minimal tool changes (for the developer; none applied)
1. **Limp threshold:** in `make_clones.py`, enable `limp` from about 0.10, not 0.25, and set it from the measured limp rate instead of `vpip * 1.1`.
2. **Iterative fit:** fit `open`, `threebet` and `call` iteratively against a seeded clone simulation, in a *full-ring field*, not the passive-observer table. The open-loop mapping here overshoots 3-bet and VPIP for aggressive profiles.
3. **Write to a versioned output folder and record the round window** in the clone header. Do not delete existing fields.
4. **Re-fit GamesGone and Resonance Qt** once ≥4,000 hands of their latest versions exist, or at minimum report results for both the pooled and latest-version profiles.

## Not done
- No strength validation: action-frequency clones do not reproduce opponents' hidden code.
- No arena or profitability runs on the new field.
- Bet sizing, showdown and c-bet fidelity were not audited, beyond the c-bet value that the mapping carries over.
