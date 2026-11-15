# Sunday cold-start candidate — not promoted

The selected reference remains **G**. None of these changes demonstrates that V4
beats G. Large runs remain prohibited pending orchestrator approval.

## What to use

- `v4_baseline.py`: frozen final V4, protected source for comparisons.
- `v4_identity_bot.py`: V4 with **cold-start per-seat behavioural profiling by
  default**; the historical name matcher is opt-in (`use_historical_identity`).
- `v4_cold_accounting_bot.py`: same, plus two separate raise-accounting fixes.
- `identity_adapter.py`: V4-specific integration. Current VPIP/PFR/large-raise,
  fold-to-three-bet, fold-to-bet and aggression reads use rolling observations;
  suspected drift switches to recent observations. No historical team prior is
  used by default. Context predictions/tags are exposed, but are not a complete
  contextual betting/range solver.
- `pokerbot/cold_observer.py`: engine-neutral offline wrapper for G/GBot research.
  It preserves actions while collecting public-history features. Integrating its
  predictions into GBot's EV model needs GBot source and independent tests.
  A standalone GBot exporter must inline these modules/remove package imports.

## Cold-start behaviour

Each fresh agent treats opponents as unseen seats. Public action counts feed
rolling 100/500-hand windows. Wilson intervals gate nonexclusive tags; sparse
contexts abstain. A comparison of non-overlapping windows flags sharp shifts,
checked every 10 hands to limit overhead. These thresholds remain uncalibrated
under repeated testing; a tag is not permission to make a large exploit.

Known names, yesterday's behaviour and current policy are distinct. New uploads
or adaptation invalidate assumptions about continuity. Persisted evidence is
version-labelled externally; unknown versions are not silently guessed. There
is no untested automatic upload loop or hidden persistence inside the sandbox.

## Reproduce small checks

From `pablo_poker`:

```text
python -B sunday/export_accounting.py
python -B tools/run_sunday_checks.py
python -B tools/check_sunday_reproducibility.py --hands 8
python -B tools/replay_cold_profiles.py
python -B local_sim.py sunday/v4_cold_accounting_bot.py --rounds 1 --hands 100 --timeout 25 --seed 23091
```

Optional historical-name comparison (not the default cold-start policy):

```text
python -B tools/replay_joint_identity.py
```

Evidence preparation, no live model writes:

```text
python -B tools/build_sunday_evidence.py --before 2026-11-15T00:00:00 --heldout-rounds 3
python -B tools/validate_sunday_predictions.py
python -B tools/build_table_d_fixture.py
```

The fixture contains the seven Table D clones and a training-only live model.
Unvalidated skill/adaptation/warm pools are explicitly disabled, not borrowed
from data fitted on holdout rounds. This makes an experiment reproducible; it
does **not** make those clones realistic. Commit fixture JSONs and manifests with
the code when relaying, not credentials or unrelated `data/` contents.

## Evidence and limits

- `contract_checks.json`: 13 new tests plus 7 existing tests, all passing.
- `reproducibility.json`: same hash with reset state and reversed job order;
  only 8 hands per run. Not a win-rate estimate.
- `identity_replay.json`: optional historical roster matcher, 17/20 correct at
  hand 1000 versus 15/20 old; still 2 confidently wrong. Do not promote it based
  on that development sample.
- `cold_profile_replay.json`: anonymous-seat profiling of three WBot rounds;
  real names are evaluation labels only, not tagger inputs.
- `prediction_validation.json`: contextual historical priors improved heldout
  log loss for some teams, worsened GamesGone, and had no Anton holdout coverage.
  This is why historical assumptions are not made the default.
- `cold_timing.log`, `accounting_timing.log`: 100-hand house-opponent timing smoke
  tests only; zero errors/timeouts at the inspected snapshot. Their profits are
  not validation against the tournament field.

## Claude's remaining work

1. Relay the real checkpoint directly to GitHub issue #1 and acknowledge its URL.
2. Verify G's actual code/upload. Test the cold observer on it, then decide whether
   and how predictions should influence its existing range/EV machinery.
3. Calibrate drift/tag confidence, conditional ranges, joint size/strength/reach
   distributions, and own-image responses on independent temporal data.
4. Finish Sunday public-version/API parsing using an actual captured response;
   do not invent its schema. Implement verified upload/activation handling.
5. With compute approval, compare engines/ablation variants across realistic
   36-round stages. Keep G unless evidence supports a replacement.

See `externalanalysis/V4_IMPLEMENTATION_CHECKPOINT.md` for status, ownership,
deadline, hashes and communication requirements.
