# AIHack Nov 2026 PokerBots

This repository contains the PokerBot tournament workspace and independent strategy review materials. It is public so teammates can inspect the agents, run comparisons, and contribute candidates.

## Project map

- `PokerBot/submissions/` — bot packages and candidate versions.
- `PokerBot/tools/` — arena runner, hand analysis, calibration, gate scripts, and candidate experiments.
- `PokerBot/Hand_data/` — downloaded real-round and external-table hand records used for analysis.
- `PokerBot/ExternalAnalysis/` — reviewer reports, algorithm research, simulation results, external-bot profiles, visualisation tools, and the reviewer/team discussion record. Start with its `README.md` and `Break_Summary_20261114.md`.
- `PokerBot/kit/` and `PokerBot/imperial-ai-hack-pokerbots-kit/` — starter kit copies and examples.

## Compare candidates locally

Install a compatible Python runtime, then from the repository root run:

```bash
python PokerBot/tools/arena.py --help
```

The arena accepts candidate and baseline bot paths, plus table count, hands per table, seed, and a historical field. For example:

```bash
python PokerBot/tools/arena.py CANDIDATE.py BASELINE.py --tables 480 --hands 300 --field late --seed 5501
```

A local arena result is comparative evidence; it does not certify production IPC, server deadlines, or runtime-bank behavior. Use the tournament release gate before recommending a live switch.

## Credentials

Never commit API or hand-fetch tokens. Use a local environment variable or an untracked local file for credentials. `.gitignore` excludes common token and Python cache files.
