# Rook: independent validation of PR #7, revision 2 (head `f7fbac4f71c1f07e787a6f4a4fe7462e0409c7ae`)

Assignment: `channel/to_bot_team/20261114-222600_rook_validate_pr7_revision2.md`. This review was done in an isolated worktree on branch `agent/rook-postmortem-validation`, created at the PR head. No bot code was touched.
Environment: Python 3.13.14, numpy 2.5.3, Windows-11-10.0.26200. The author used Python 3.12.13 and numpy 2.4.6.

## Verdict

**The pipeline reproduces, and the headline totals check out independently.** One blocker remains for using the WBot conclusions: **"WBot" here pools three different bots** (G, I and likely N), so WBot-level findings are not findings about any single bot we might run on Sunday. The forecast assumptions are coded as described and are correctly labelled illustrative.

## 1. Manifest and input hashes: agree

`pm_manifest_check.py` is my own code; it does not use the PR's scripts. It re-hashes every file listed in `data/input_manifest.csv` and also globs the disk:

- 159 manifest rows, 0 missing, **0 sha256 mismatches**.
- 159 files on disk, **0 not in the manifest**.
- Status counts: 135 used, 24 duplicates. This matches the author's numbers.

## 2. Re-running the author's scripts: byte-identical

```
cd PokerBot/ExternalAnalysis/SaturdayFieldPostmortem
PYTHONIOENCODING=utf-8 python 00_manifest.py   # ... and so on through 06_robustness.py, in README order
```

- Outputs 01–06 match the committed `data/out_*.txt` **byte for byte**, apart from line endings.
- `out_00` differs only in the line that records the environment.
- `pairwise_skill.json` differs by at most 2e-12, which is floating-point noise.
- **Minor reproducibility bug:** without `PYTHONIOENCODING=utf-8`, Windows console encoding garbles "Poké Bot", "crêpes" and "±" in 01, 02 and 05. Fix: add `sys.stdout.reconfigure(encoding="utf-8")`, or document the variable in the README.

## 3. Headline totals, recomputed independently: agree

`pm_indep.py` has its own parser and dedup rule (ref plus ordered players, practice rounds skipped, first file in sorted order wins). It does not use `hand_stats` or `common`.

| Quantity | Author | Rook |
|---|---|---|
| Unique counted tables / hands | 135 / 135,000 | 135 / 135,000 |
| Non-zero-sum hands | 0 | 0 |
| Observing accounts | — | kaiserbot 53, Red 44, WBot 38 |
| WBot with ≥1 of the 7 worst bots at the table | +21.3 (n=40) | +21.3 over 40 tables |
| WBot with none of them | −9.3 (n=14) | −9.3 over 14 tables |
| WBot vs top 21 (×7 per-pair scaling) | −18.0 | −18.0 |

## 4. `06_robustness.py` resampling: correct as a table-cluster bootstrap, with caveats

- Each replicate resamples whole tables with replacement: `bincount(rng.integers(0,T,T))` weights tables, and every statistic is recomputed from the weighted table sums. That is the correct clustered resampling. The seed is fixed and the output reproduces exactly.
- The bracketed intervals are **5–95 percentiles, so they are 90% intervals**. The report should say "90%".
- **Clusters are not fully independent.** Tables in the same 5-minute slot share opponents, and bot versions drift over the day, so the true uncertainty is somewhat larger. Slot-level resampling would be more conservative.
- **Two different "donor" definitions:**
  - `from_donors` / `from_others` use teams with a negative final leaderboard score, plus ediz_slow.
  - `with_donors` / `no_donors` use the fixed 7-bot set `BIG7`.
  - The report should name both definitions wherever it uses them.
- **`vs_top21` multiplies the per-opponent rate by 7.** Tables have 6–8 seats, so this is a normalisation, not an observed result. Label it as such.
- The additive-model chi²/df is already labelled "not a calibrated test". Good.

## 5. Blocker: "WBot" is three different bots

The website version labels and the provenance audit (#2) show who held WBot's seat:

| Seat holder | Rounds |
|---|---|
| G (v5, v7, v9) | r001–023, r048, r054 |
| I (v6) | r024–047 |
| Likely N, by behaviour (v8) | r049–053 |

Splitting the same quantities by version (`pm_boot.py`, `pm_byver.py`):

| WBot vs top 21, ×7 scaling | Tables | Estimate | 90% table bootstrap |
|---|---|---|---|
| G (v5, v7, v9) | 25 | **+2.0** | [−28.5, +38.0] |
| I (v6) | 24 | **−34.3** | [−61.5, −5.7] |
| N? (v8) | 5 | −20.2 | [−70.2, +16.6] |

| WBot at tables with donors / without donors | G | I | N? |
|---|---|---|---|
| With | +40.3 (18 tables) | +10.7 (19) | −25.1 (3) |
| Without | −15.2 (6) | −8.5 (5) | −5.9 (2) |

- The pooled −18 vs the top 21 is driven by I's rounds. G's own estimate is about zero, with a very wide interval.
- Claim 3, "WBot's profit came entirely from donors", fits I. For G it is plausible but not established.
- These splits are descriptive. Versions also played at different times of day against changing fields.
- **The Sunday "WBot in our seat" scenario uses this pooled profile.** It needs to state that, or be rerun with the profile of the bot that will actually play, most likely G.

## 6. Sunday scenarios (05): assumptions are as described

- **Zero-sum noise is right.** Each draw is centred, then rescaled by √(n/(n−1)), so each seat keeps the stated SD and the table sums to zero.
- **Edge scenarios are rebalanced correctly.** Our seat's change is taken evenly out of the other seats.
- **Assumptions are printed**, along with a sensitivity grid over τ, skill SD and round SD.
- **Not a forecast:** every seat is assumed to keep its Saturday bot, and the head-to-head numbers come from pooled WBot. Keep it labelled illustrative, as the report already does.
- **Wording mismatches:**
  - The report says the "+20 target" was removed, but its sensitivity table still prints "+20" as the edge needed for 50%. This is fine as a scenario output; just don't call it a target.
  - **The PR description is stale:** it still states the original claims (strong transitivity, "+20 is a coin flip").

## 7. Not checked

- I did not audit the leaderboard-diff increments in 01 and 03. They come from the public leaderboard, not hand files.
- I did not rerun the style-profile parser `hand_stats.py` line by line; I compared only its outputs, which match.
- Data note: the PR adds `saturday_r054.json` (WBot v9, sha256 `ee3a36fb…6eac40`). It is consistent with G (see #2) and is not yet in the local workspace.

## Reproduce

From `PokerBot/`:

```
python -I ExternalAnalysis/AgentReports/ROOK_PR7_validation/pm_indep.py .
python -I ExternalAnalysis/AgentReports/ROOK_PR7_validation/pm_byver.py .
python -I ExternalAnalysis/AgentReports/ROOK_PR7_validation/pm_boot.py .
```

From the repo root:

```
python -I PokerBot/ExternalAnalysis/AgentReports/ROOK_PR7_validation/pm_manifest_check.py
```

Outputs are saved next to the scripts as `*_out.txt`.

Script sha256:

| Script | sha256 |
|---|---|
| `pm_manifest_check.py` | 868b8964c8b3be9ca45ec5ebc92688cfca04f9fadd42e50e002ef5f8fecc30b5 |
| `pm_indep.py` | 7a19c6c0ef1c091a93c2761654c951513731ebe5f0cec71ec45a4b62b966ef1b |
| `pm_byver.py` | 91469edb58732815d4fa8908cf9b39df485a0e48e6d1e7da922c5830a7a96bfd |
| `pm_boot.py` | 3df4e8fd61782e0b384acef65b4bdd7f8a0765040ab95f1a19b8cd8290e22666 |

`pm_byver.py` groups r054 separately as `r54+`. `pm_boot.py` counts r054 as G.
