# Saturday field post-mortem: scripts and data

Report: `../Saturday_Field_Postmortem_20261114.md`. Needs Python 3 with numpy (no other dependencies).

| script | what it does | output |
|---|---|---|
| `01_noise_vs_skill.py` | data integrity, per-round noise, split-half reliability, final standings ±SE; writes `data/per_round_increments.json` | `data/out_01_noise_vs_skill.txt` |
| `02_styles_pairwise.py` | per-team style profile, style vs result, position results, pairwise flows, transitivity test, donor concentration; writes `data/team_profiles.json`, `data/pairwise_skill.json` | `data/out_02_styles_pairwise.txt` |
| `03_bucket_edges.py` | broken-bot outliers, version churn and drift, edge vs donors / top-21 / ranks 8-16, a first Sunday sim (it assumed block seeding; superseded by 05) | `data/out_03_bucket_edges.txt` |
| `04_donor_dependence.py` | result with vs without donors at the table, robust re-rank | `data/out_04_donor_dependence.txt` |
| `05_sunday_table4.py` | WBot's real Sunday table: opponent styles, head-to-head, P(top 2) with stand-in bots, edge needed | `data/out_05_sunday_table4.txt` |

Run in order from this folder (01 and 02 write the JSON files that 03-05 read):

    python 01_noise_vs_skill.py

By default the scripts read the repo's `Hand_data` (91 unique counted tables). The committed outputs
use the full 135-table set from our three accounts. To point the scripts at other files, set
`POSTMORTEM_HANDS` to globs separated by `;` (Windows) or `:`. `hand_stats.py` is the Red team's hand
parser (`analyse_round`), copied unchanged.

`data/leaderboard_history_r13_r48.csv` holds the public leaderboard, captured every minute; diffs give
every team's exact chips per round for rounds 14-48. `data/final_standings_saturday.json` and
`data/sunday_buckets.json` are snapshots of the public API.
