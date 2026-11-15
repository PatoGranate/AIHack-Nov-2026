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

## Matthias/SCOUT findings tested (2026-11-15 07:00-08:00, vs frozen G, paired tables × 1,000 hands)

| Candidate (separate file; G untouched) | Adaptation slope* | td_fb | td |
|---|---|---|---|
| frozen G | −0.01 | — | — |
| `G_heroftb` per-seat fold rate to OUR bets (SCOUT rec. 1) | +0.08 | −0.1 ± 3.7 | −1.4 ± 3.5 |
| `G_steal3b` per-seat steal + light 3-bet on (G's idle paths) | — | +4.7 ± 4.4 | +1.1 ± 3.7 |
| `G_adaptA` heroftb + honest check value, no bet bonus | +0.34 | −15.8 ± 4.8 | −10.0 ± 4.3 |
| `G_adaptB` A + c_mid 0.85 | +0.45 | −2.7 ± 5.4 | −13.8 ± 4.7 |

*Adaptation slope = change in heads-up bet rate per +1.0 in the opponent's in-round fold rate to other bettors
(`adapt_sim` on 24 logged td_fb tables). Real Saturday: Market Makers +1.13, Attention +0.83, Resonance +0.80,
WBot +0.03, Red +0.07.

Reading:
- The winners' edge is per-opponent, learned within the round: they bet into folders and away from stations
  (vs YSL: bet 41% at 1.08 pot, 19% air shown; ours: 82% at 0.70, 50% air).
- G does not adapt (slope ≈ 0) because its bet bonus and discounted check value make betting win regardless
  of fold rate. Removing that bias makes G adapt (slope +0.34 to +0.45) but loses chips in both clone fields.
- Clone fields are static frequency bots that pay off over-betting (they over-reward aggression by 18-42 bb/100
  for our live bots), so they cannot credit adaptation. The sign of the adaptive change in reality is unknown.
- None of these is promoted. Safe upload: frozen G. `G_steal3b` is the only non-negative change, not significant.

## Second batch (08:00-08:30): winner-style adaptation and combinations (vs frozen G, 128 × 1,000)

| Candidate | Slope | td_fb | td |
|---|---|---|---|
| `G_adaptC` heroftb + per-seat bluff gate (no bluffs vs < 30% folders) + pot-size value vs stations + bluffs vs > 55% folders; G's value betting kept | **+0.52** | −7.5 ± 3.7 | +2.2 ± 3.8 |
| `G_combo1` adaptC + steal3b | — | −5.4 ± 3.8 | +2.4 ± 3.8 |
| `G_combo2` combo1 + Table D priors / change detection (profile layer) | — | −0.9 ± 3.8 | −2.7 ± 4.0 |

Preflop adaptation (real Saturday): slope of 3-bet rate vs the opener's in-round fold-to-3bet: Resonance +0.36,
Attention +0.33, Anker +0.33, Gherkers +0.21; WBot 0.00, Red −0.02, kaiserbot 0.00 (`adapt_pf`).

**Independent confirmation (ROOK, issue #1 6891492567 / 6891585466):** `G_profile_td` vs G = +4.8 ± 1.9 on Table D
fields (most of it where opponents switch policy mid-round), +0.5 ± 1.8 pooled over 8 broad fields. Only clone fields;
roster priors in-sample; no runtime gate yet. Strongest candidate so far. Combining more mechanisms did not add.
