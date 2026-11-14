# Submission versions

Each folder has a ready-to-upload `bot.py`. All passed the checks with 0 errors, 0 timeouts and 0 bank-outs under the real limits.

| Version | What it is | vs v2, weak-bot field | vs v2, strong field |
|---|---|---|---|
| A_v2_safe | First uploaded version: hand charts + win-chance simulation | baseline | baseline |
| B_v3_balanced | v3 opponent modelling, moderately aggressive | +79 bb/100 (z=3.5) | +2 (tie) |
| C_v3_aggressive | v3, very aggressive | +165 bb/100 (z=5.6) | −15 ± 13 (tie) |
| D_v3_max_aggressive | v3, extreme: opens almost every hand late, big bets | +14 ± 17 over C (not significant) | untested |

Tell Claude which one does best online and it will continue tuning from that one.
Sources: `tools/cands/agg2.py`, `agg4.py`, `agg6.py`; settings in each file's `P = {...}`.

## Later versions

| Version | What it is | Result |
|---|---|---|
| E_v3_balanced_fast | B + speed fix (timeouts) | live v3: r015 -17, r016 +32 |
| F_v3_tuned | E + first tuning step | reviewer league #1 (+31 bb/100) |
| **G_v7_final** | Corrected EV model (reviewer fixes), retuned, + check-raise trap, tiny value bet, river overbets. | vs F: +22 / +31 / +27; vs E: +27 / +26 / +36 bb/100 (held-out / real clones / strong), z 4.7-6.5; 0 timeouts under real limits incl. 5,000 hands |
| **H_v8_tuned** | G + 2x thinking budget, size sensitivity 0.575, bet sizes 0.4/0.75 pot, tuned vs strength-weighted opponents. | vs G: +9.0 late (r008-r010 opponents), +7.0 held-out, +7.3 real clones, +1.9 archive, +6.5 emulated slow server |
| **I_v9_25ms** | H + thinking time for the 25 ms limit (6 ms/decision, 14 ms hard stop, 7 s bank guard), open size 2.8 bb, calls re-raises slightly more. **Now in kit/bot.py** | vs G at server-equivalent speed: +11.6 newest-opponent clones, +22.5 real clones, +11.9 held-out, +35.7 archive (z 2.2-4.5) |

D (v4) lost -151 bb/100 live in r017; don't use it. Rollback order: G (proven live, +27.7 bb/100 over 18 rounds), then F. I needs the 25 ms decision limit; do not use it under a 10 ms limit.

| **N_v10_tuned** | I + 6 tuned settings (less bluffing, bets slightly more readily, tighter early-position opens, slightly tighter/looser calling) from run 3. Same 6 ms/14 ms/7 s timing as I. **Now in kit/bot.py** | vs I at server-scaled speed: +8.4 newest clones, +8.5 real, +8.8 held-out, +7.4 archive; vs G: +30.5 newest clones. Live: untested. |

Rollback for N: G (live +26.8 over 23 rounds). I live: +8.5 over 23 rounds, simulations over-rated it.

Website version numbers: v1=A, v2=C, v3=E, v4=D, v5=G, v6=I, **v7=G (re-uploaded)**, **v8=N**. When comparing live results, treat v5 and v7 as the same bot (G).
Update: v9 = G (re-uploaded again). v8 = N. Treat v5, v7, v9 as G.
