# Results (2026-11-15, duplicate arena, 128 paired tables × 1,000 hands per row)

Positive = candidate wins more than frozen G with the same cards and seats. ± is one standard error.
Noise floor: frozen G vs itself on `td`: +3.5 ± 4.0 (G's Monte Carlo is clock-limited, so paired runs diverge).

## v4 does not beat G
| | td (sunday_v2 clones) | td_fb (FieldBot clones) |
|---|---|---|
| v4 (`bot.py`, 8458e3…) vs G | −9.9 ± 4.3 | −5.1 ± 4.3 |

Orchestrator's independent check on sunday_v2: −15.2 ± 9.5.

## G + profiling vs frozen G
| Candidate | td | td_switch | td_fb | mean (6 runs) |
|---|---|---|---|---|
| `G_profile.py` (400-hand window, generic priors) | −4.3 ± 3.6 | +1.2 ± 4.2 | — | — |
| `G_profile_td.py` (window + Table D priors) | +1.9 ± 4.2, −0.3 ± 3.5 | +10.4 ± 3.9, +0.2 ± 4.4 | +4.8 ± 3.8, +8.8 ± 4.0 | **+4.3 ± 1.6** |
| `G_profile_tdf.py` (whole round + Table D priors) | −2.4 ± 3.6, +4.3 ± 3.6 | +1.5 ± 3.2, +5.2 ± 3.5 | +8.4 ± 4.0, +2.7 ± 4.2 | **+3.3 ± 1.6** |

Seeds: td 13/23 then 31/41, td_switch 15/25 then 31/41, td_fb 17/27 then 31/41.

Reading: the rolling window alone does not help against steady opponents (it discards evidence).
Pooled Table D priors give a small, consistent edge (about +3 to +4 bb/100, z ≈ 2), most of it early
in each round, before G's own counts take over. That is roughly what priors with 8–12 hands of mass
can buy inside one 1,000-hand round. The bigger 36-round gain needs per-opponent memory carried
across rounds through re-uploads, which this does not do.

## Detector calibration (real Saturday rounds, 887 opponent-rounds)
z = 2.5: 59.2% false alarms · 3.0: 27.7% · 3.5: 9.6% · 4.0: 2.9% · **4.5: 1.0% (used)**.
At z = 4.5 the detector catches 29 of 140 simulated mid-round switches (21%), 0 false alarms in sim.
Codex's v4 detector on the same real rounds: 6.7% false alarms.

## Timing (official kit subprocess runner, 25 ms, 3 × 1,000 hands)
G_profile_tdf 1.3 s, G_profile_td 1.2 s, frozen G 1.1 s worst round; 0 timeouts, errors, bank-outs.

## Not established
- Clone fields are not the real Table D. sunday_v2 clones are simple frequency bots; FieldBot clones
  are richer but still about 18–35 bb/100 too generous to our engines.
- Roster priors were computed from the same Saturday data the clones were built from, so their
  benefit here is partly in-sample.
- No candidate is promoted; the orchestrator's independent test should decide.
