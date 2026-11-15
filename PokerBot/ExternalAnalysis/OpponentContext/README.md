# Opponent context audit: scripts and outputs

Report: `../Opponent_Context_Audit.md` (owner: SCOUT). Python 3 + numpy only.

| script | what it does | output |
|---|---|---|
| `oc_parse.py` | loads the counted Saturday tables (same globs and dedup rule as the post-mortem; requires the manifest, validates selected-file SHA256 values and fails if the set differs from `../SaturdayFieldPostmortem/data/input_manifest.csv`), checks chip conservation per hand, extracts postflop and preflop decisions with context, and replicates the G/N bot's own `faced`/`ffold` counter | - |
| `oc_stats.py` | table-bootstrap rates (whole 1,000-hand tables resampled), DerSimonian-Laird between-team and between-opponent-table heterogeneity, calibrated by null simulation | - |
| `01_postflop_context.py` | per-opponent fold rates by HU/multiway, bet size, street, IP/OOP, callers, facing a raise, bettor = WBot; decisions per round per bucket; heterogeneity; size curve vs the bot's assumed curve; stability across tables | `data/out_01_postflop_context.txt`, `data/postflop_context_summary.json` |
| `02_preflop_context.py` | fold to a first-in open by role, open size and callers; opener vs 3-bet IP/OOP; heterogeneity | `data/out_02_preflop_context.txt`, `data/preflop_context_summary.json` |
| `03_render_tables.py` | renders the report's per-opponent tables A-D from the two JSON files | `data/audit_tables.md` |
| `04_wbot_gap_by_hand.py` | the stratified "fold less to WBot's bets" gap by hand-number quarter (adaptation vs spot selection) | `data/out_04_wbot_gap_by_hand.txt` |

Reproduce (from this folder; about 10 min for 01, 4 min for 02, 1 min for 04 on one core):

    python 01_postflop_context.py
    python 02_preflop_context.py
    python 03_render_tables.py
    python 04_wbot_gap_by_hand.py

Inputs: 135 unique counted tables (135,000 hands) from `PokerBot/Hand_data/SaturdayRealRounds/` and
`PokerBot/Hand_data/ExternalTeamData/*/SaturdayRealRounds/`, hashed in the post-mortem manifest. Bootstrap seeds are
fixed (20261115, 20261117 and 20261119 for 01, 02 and 04), so reruns reproduce the committed outputs exactly on the same numpy version
(outputs were made with Python 3.12.13, numpy 2.4.6).

Focused input-integrity regression checks (no simulation or statistical refit):

    python -m unittest -v test_manifest

Heterogeneity p-values condition on independent-binomial null outcomes. Table-bootstrap rate intervals do not make that null cluster-robust. The unit variance decomposition and implied prior weight are exploratory approximations.
