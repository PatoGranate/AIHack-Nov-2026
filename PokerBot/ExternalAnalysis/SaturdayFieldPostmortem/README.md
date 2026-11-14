# Saturday field post-mortem: scripts and data

Report: `../Saturday_Field_Postmortem_20261114.md`. Needs Python 3 with numpy (no other dependencies).

| script | what it does | output |
|---|---|---|
| `00_manifest.py` | lists every input hand file with SHA-256, account, round, dedup key and used/duplicate status; prints environment | `data/input_manifest.csv`, `data/out_00_manifest.txt` |
| `01_noise_vs_skill.py` | data integrity, per-round noise, split-half reliability, final standings ±SE; writes `data/per_round_increments.json` | `data/out_01_noise_vs_skill.txt` |
| `02_styles_pairwise.py` | per-team style profile, style vs result, position results, pairwise flows, transitivity test, donor concentration; writes `data/team_profiles.json`, `data/pairwise_skill.json` | `data/out_02_styles_pairwise.txt` |
| `03_bucket_edges.py` | broken-bot outliers, version churn and drift, edge vs donors / top-21 / ranks 8-16, a first Sunday sim (it assumed block seeding; superseded by 05) | `data/out_03_bucket_edges.txt` |
| `04_donor_dependence.py` | result with vs without donors at the table, robust re-rank | `data/out_04_donor_dependence.txt` |
| `05_sunday_table4.py` | WBot's Sunday table: opponent styles, head-to-head, illustrative zero-sum P(top 2) scenarios with a sensitivity grid | `data/out_05_sunday_table4.txt` |
| `06_robustness.py` | multi-winner share, table-bootstrap intervals for donor/non-donor splits, top-21 edges, with/without-donor results, additive-model check | `data/out_06_robustness.txt` |

Run in order from this folder (01 and 02 write the JSON files that 03-06 read):

    python 00_manifest.py; python 01_noise_vs_skill.py; python 02_styles_pairwise.py
    python 03_bucket_edges.py; python 04_donor_dependence.py; python 05_sunday_table4.py; python 06_robustness.py

The default inputs are the committed `Hand_data` archives (159 files, 135 unique counted tables after
dedup). Every committed output was generated from them with no overrides (Python 3.12.13, numpy 2.4.6).
`POSTMORTEM_HANDS` (globs separated by `;` on Windows or `:` elsewhere) points the scripts at other files.
`hand_stats.py` is the Red team's hand parser (`analyse_round`), copied unchanged.

`data/leaderboard_history_r13_r48.csv` holds the public leaderboard, captured every minute; diffs give
every team's exact chips per round for rounds 14-48. `data/final_standings_saturday.json` and
`data/sunday_buckets.json` are snapshots of the public API.
