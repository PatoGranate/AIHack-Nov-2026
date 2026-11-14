Candidate development and promotion workflow

The running fetch pipeline still uses pokerbot/v2.py, data/v2_params.json and
export_v2.py. This candidate is isolated so model refreshes cannot overwrite it.

Source: candidate/engine.py
Frozen pre-change upload: candidate/baseline.py
Frozen live parameter overrides: candidate/baseline_params.json
Training-only corrected engine model: candidate/live_model_snapshot.json
Field training data: candidate/field_model.json
Comparison cohort: candidate/cohort.json

Commands from pablo_poker:
  python -B tools/test_field_changes.py
  python -B tools/validate_field.py --freeze --tables 64 --hands 1000 --workers 2 --seed NEW_SEED
  python -B tools/field_gate.py candidate/validation_NEW_SEED.json
  python -B tools/tune_field.py candidate/validation_NEW_SEED.json
  python -B candidate/export.py
  python -B local_sim.py candidate/bot.py --rounds 1 --hands 1000 --timeout 25 --seed 918

The new tuner checks calibration and artifact hashes first. It allocates fresh
seeds before selection, requires every paired result, then holds out twice as
many fresh tables for its chosen candidate. Passing means mean gain exceeds
1.96 standard errors on that cycle's holdout; it is not an unlimited sequential
search guarantee. Do not repeatedly retry until significance appears.

Tuning writes candidate/tuned_params.json on success. Export currently accepts
overrides via candidate.export.export(params); pass the tuned JSON explicitly
when exporting a promoted variant. Default CLI export builds the untuned candidate.

Promotion must also compare the repaired engine against the frozen live engine,
not merely a tuned variant against the repaired reference. Passing calibration
alone never establishes an improvement. Timing must be checked on the final
export bytes. The 25 ms setting follows the current local harness; use the
actual platform setting if it changes.

No automatic upload is configured here. This workspace has no Git repository,
and the existing pipeline exports locally rather than pushing to an upload API.
Do not replace the live engine while calibration or improvement checks fail.

Known model limits: showdown targets are selected observations; strength classes
are coarse; the multiway raise response remains conservative; temporal cohort
results can vary substantially by opponent lineup and bot version. Decisions
are tested with fixed MC work for reproducibility, separately from clock tests.
