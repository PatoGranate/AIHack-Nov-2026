# G + opponent profiling (candidates, not promoted)

v4 does not beat G (orchestrator: −15.2 ± 9.5 bb/100 on sunday_v2; here −9.9 ± 4.3 on Table D
clones and −5.1 ± 4.3 on FieldBot Table D clones). So the profiling goes into G instead.
G's betting and EV code is untouched. Only the opponent reads G already consumes change
(vpip, pfr, bigrate, fold3, blindfold, ftr, ftb, af).

| File | What it is |
|---|---|
| `G_frozen.py` | verbatim `PokerBot/submissions/G_v7_final/bot.py`, sha256 `1ee577f0…fe12` |
| `g_profile_adapter.py` | the layer appended to G (rolling evidence, change detection, roster priors) |
| `G_profile.py` | G + last-400-hand window + policy-change detection, generic priors |
| `G_profile_td.py` | same + pooled Table D priors for unseen seats |
| `G_profile_tdf.py` | Table D priors + whole-round evidence; old hands dropped only on a detected change |
| `manifest.json` | sha256 of every file above |

Build: `python gbot/export_g_profile.py` (checks the G hash). Tests: `python gbot/test_g_profile.py`.

## Design choices, each measured

- **No name matching.** Table D priors are the pooled tendencies of the seven known opponents, so a
  seat is never assigned a wrong identity (Codex's replay: 4 of 20 seats confidently wrong).
- **Change detector threshold z = 4.5.** On 887 real Saturday opponent-rounds (code cannot change
  mid-round) the false-alarm rate is 59% at z = 2.5, 28% at z = 3.0, 9.6% at z = 3.5, 2.9% at z = 4.0,
  1.0% at z = 4.5 (`calib_drift_real.py`, `drift_calibration.json`). Synthetic tests understate this badly.
- **Reads are O(1).** G calls them many times inside `act()` under a 3 ms hard deadline; an early
  version re-summed the window per call and lost 40 bb/100 because Monte Carlo ran out of time.
  `test_reads_cost_like_G` guards this.

## Codex's v4 candidates (sunday/)

- Same defect found and fixed: after a round of evidence, reads cost 199 µs vs 5.9 µs per seat
  (34× slower) inside v4's 4–8 ms budget; now 2.3 µs via a per-hand cache
  (`sunday/identity_adapter.py`, guarded by `test_codex_cache.py`).
- Codex's change detector false-alarm rate on the same real rounds: 6.7% (`calib_codex_drift_real.py`).

## Harness

The WBot team's own duplicate arena (`PokerBot/tools/arena.py`) plus three Table D fields
(`tdarena.py`): `td` = the seven `sunday_v2` clones, `td_switch` = each clone switches to another
Table D clone's policy at hand 500, `td_fb` = the seven FieldBot clones from `sim/fieldbot.py`.
Results: see `results.md`.
