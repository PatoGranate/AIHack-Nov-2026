# Independent Sunday evaluation evidence

No tested challenger in this bundle establishes an improvement over frozen G. Keep G as the reference; these experiments do not prove that G is intrinsically superior. All results use fixed diagnostic work against public-frequency clones and do not certify server timing, bank usage, real-opponent strength or deployed artifact identity.

| Comparison | Fresh pairs | Table-hands | Difference vs G (bb/100) | Paired SE | Ordinary 95% t interval |
|---|---:|---:|---:|---:|---|
| I screen | 16 | 32,000 | +9.93 | 8.46 | [-8.10, +27.97] |
| N screen | 16 | 32,000 | -1.23 | 9.72 | [-21.94, +19.49] |
| I held-out confirmation | 64 | 128,000 | -0.84 | 4.46 | [-9.76, +8.07] |
| Pablo v4 confirmation | 32 | 64,000 | -15.23 | 9.47 | [-34.54, +4.08] |

The I/N screen additionally reports Bonferroni intervals for its two comparisons. I confirmation was one separately preregistered held-out test after the exploratory positive I evidence; its positive-lower-bound criterion failed, and that sequence stopped. Do not pool exploratory and confirmation outcomes or substitute favorable hand windows. The Pablo confirmation likewise failed to demonstrate improvement. Different comparisons use different seeds, so absolute returns across rows are not direct model rankings.

## What is included

- `reports/`: original completed reports, including limitations and input identities.
- `results/`: exact pre-run manifests, per-pair JSONL, machine summaries, G/I/N A-v-A traces and related summaries. No collector full-hand archive is included. The small QA traces contain synthetic simulation cards, not hidden live cards.
- `inputs/PokerBot/`: exact-byte snapshots of the frozen models, harnesses, engine, clone inputs and older control reports needed to inspect or reconstruct these runs. These snapshots are research evidence, not replacements for production files. Nested `.gitattributes` preserves their original line endings and SHA-256 identities.
- `dependency_manifest.json`: exact source-path hashes and independently recalculated raw means.
- `verify_evidence.py`: standard-library hash/statistics/A-v-A audit; it does not run matches.

Run `python verify_evidence.py` from this directory. This verifies all 29 dependency snapshots and all four primary effects, SEs and ordinary t intervals, raw/manifest identities, unique seeds, window totals, zero reported errors and archived G/I/N A-v-A engine trajectories. It does not replay the full matches.

## Frozen policy identities

| Policy | Original source path | Raw-byte SHA-256 |
|---|---|---|
| G | `submissions/G_v7_final/bot.py` | `b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a` |
| I | `submissions/I_v9_25ms/bot.py` | `d45a39b72c0e990efe06c8a233c7f2061f468a5c1f3279924c5ae07fc060f46c` |
| N | `submissions/N_v10_tuned/bot.py` | `5c2b4b2c0ed3ddd5177fe758959e1c32e3a113f8c500a373f6b5d11d5bb7845f` |
| Pablo v4 | `tools/independent_pablo/bot.py`, branch `pablo-poker` commit `24653c9` export | `8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108` |

The diagnostic loaders transform source in memory: fixed 32 Monte Carlo samples, identical budget override, per-decision RNG seeding for heroes and all seven clones, and DEBUG enabled. Frozen files remain unchanged. The players run in process; zero observed errors does not establish a reliable production internal-fallback count or subprocess deadline guarantee.

## Reconstructing a run without touching production

Copy `inputs/PokerBot/` into a new empty working directory. Its scripts expect that directory to be the PokerBot root. Do not copy published result directories into the output locations before executing, because the runners intentionally refuse to overwrite preregistered runs.

1. For the I/N screen, run `python tools/independent_g_in/run_gate.py`.
2. The I confirmation then reads the completed screen's unchanged dependency/control evidence: run `python tools/independent_g_in/run_confirmation.py`.
3. The Pablo confirmation uses the archived exploratory report's A-v-A records and checks unchanged model/loader/field hashes: run `python tools/independent_pablo/run_confirmation.py`.

These commands start new CPU simulations and should be run only deliberately; they were not re-executed while packaging evidence. New manifest timestamps and wall-clock fields will differ; compare deterministic policy outcomes, not whole timing-bearing output bytes. The older full `run_review.py` exploratory runner references extra historical Pablo exports not included here and is not part of this reproduction recipe; its loader prefix is included exactly because the confirmation imports that prefix. Likewise the earlier seven-block clock-budget I/G report is context, not pooled evidence, and is preserved as a dependency of the confirmation provenance check.

## Merge and release scope

This PR only adds an evidence folder. It changes no existing policy, kit, clone field, live upload or production setting. It does not promote any model. The remaining release gates are independent current-artifact correctness, complete-round subprocess timing/bank/fallback evidence under confirmed platform limits, and evidence against realistic fields. No further I/G retry is authorized by this bundle.
