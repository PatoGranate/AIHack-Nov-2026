# To the orchestrator: check this work before anyone relies on it

Written by the agent that built kaiserbot v4 (branch `pablo-poker`). **Do not take my claims on
trust.** Each one below comes with the command that tests it. Treat anything you can't reproduce
as false.

## 1. Mandatory: play our best agents against your best models

**This is imperative and must happen before the Sunday entry is chosen.** All three bots (kaiserbot,
Red and WBot) are now one team, and only one goes forward. Until our bots have played at the same
tables, under the same cards, the choice between them is a guess. Real results are too noisy to
decide it: one round swings 35–50 bb/100, and the three bots' real results (+10.9, +5.2, −10.0)
each carry about ±11.

Run this from `pablo_poker/`, putting the paths of **your** strongest bot files after ours:

```bash
python tools/head_to_head.py bot.py bot_v32.py bot_v31.py <your_best_bot.py> <your_second_best.py> --tables 40 --hands 1000 --field A
```

```bash
python tools/head_to_head.py bot.py bot_v32.py bot_v31.py <your_best_bot.py> <your_second_best.py> --tables 40 --hands 1000 --field B
```

How it works:
- **Same cards for everyone.** It is duplicate style: every card seed is replayed once per rotation,
  and the bots move one seat along each time.
- **Free seats are filled** with data-driven clones of the real Saturday field. Add `--fill none` to
  play the files against each other only.
- **Output:** each bot's bb/100 with its standard error, and its paired difference from the first file.
- **Runtime:** 40 seeds × 8 rotations of 1,000 hands takes roughly 40–60 minutes on 8 cores.

Our candidates, best match to the winners' style first:

| File | What it is | Real evidence |
|---|---|---|
| `bot.py` | **v4**: plays in the winners' style | none yet (never played live) |
| `bot_v32.py` | v3.2: v3.1 plus preflop discipline | none yet (never played live) |
| `bot_v31.py` | v3.1, the live version 12 | +21.3 ± 16 bb/100 over 9 real rounds |

Decision rule I recommend:
- Enter the bot with the best head-to-head result **in both fields**.
- If the result is within about two standard errors, prefer the one with real results behind it.

## 2. Is v4 our best model? Best head-to-head, not proven against the field

v4 is the bot that **plays most like the winners**. It also **won the head-to-head** against v3.2,
v3.1, WBot's v10 code and Red's local code (section 5). But I have **not** shown that it wins more
than v3.2 or v3.1 **against the real field**:

| Evidence | v4 vs v3.2 |
|---|---|
| Replay on our real hands, judged against the cards opponents showed | about the same (−2.3 vs −2.4 bb/100 on judged spots, held-out rounds) |
| Simulated field A (clones answer every bettor alike) | about the same on average, runs from −4 to +8 bb/100, each ±4 |
| Simulated field B (clones adapt to aggressive bettors) | **7–18 bb/100 worse** |

My argument for v4 is that both simulated fields demonstrably over-reward the old always-bet style:
- Field A credits the real live bot with about 18 bb/100 too much from pots won without showdown.
- Field B credits it with about 42 bb/100 too much from showdowns.

That argument is an inference, not a measurement. **The head-to-head in section 1 is what should
decide.**

## 3. Claims to verify

1. **v4's style matches the winners.** Simulated: bets when checked to 76/55/35%, open 25%,
   3-bet 11.4%, showdowns won 54–56%, 8–10 stack-sized showdowns per 1,000 hands.
   Winners (real): 59/56/44, 24, 12.3, 57 and 10–13.
   Check: `python tools/bench2.py <variants.json> 96 600` prints these style columns per variant.
2. **The engine's old fold model was wrong.** For a ⅓-pot turn bet it assumed 36% folds and 0%
   raises; the real field folds 11% and raises 18% against our bots.
   Check: `python tools/build_v3_model.py`, then read `pop.ans_us` / `pop.ans_oth` in
   `data/v3_model.json`.
3. **Big-blind defence.** Our three bots' real hands show that calling a raise from the big blind
   with hands outside the top 25% loses 1.2–1.5 bb per call against folding (about 1,170 calls).
4. **Simulator fidelity.**
   - Clones' showdown win rates match the real bots to within 0.03 on average.
   - Big-pot equities match: 0.54 simulated vs 0.54 real when our big bet is called, and 0.42 vs
     0.43 when we call.
   - Per-bot results correlate only 0.2–0.3 with reality.
   - The simulator is still **18–35 bb/100 too generous** to our engines: live kaiserbot +29
     simulated vs +11 real; WBot's v10 code +15 vs −10 real; Red's older local code +41 vs +5 real.
   - Check: `python tools/calib_skill.py <simdir> 0` and `python tools/calib_adapt.py <simdir>`.
5. **Timing.** v4 thinks 2.1–2.5 s per round locally with 0 timeouts; v3.2 takes 2.9–3.1 s.
   The bank is 10 s and the server runs about 2× slower than local.
   Check: `python local_sim.py bot.py --rounds 5`.

## 4. Known gaps (not done)

- **Version tracking:** the field model only weights recent rounds more heavily; it cannot tell
  which version an opponent is running.
- **Red's current code** was not available to us, so the simulator was checked against an older
  version.
- **Field fidelity:** no single simulated field reproduces our real result split; reality sits
  between fields A and B.
- **Raising opponents' bets:** v4 still raises about 30% of flop bets (winners average 12%) and
  17–20% of river bets (winners about 5%).

## 5. Head-to-head already run by me (24 seeds × 8 rotations × 1,000 hands)

Five bots shared every table; the other 3 seats were field clones.

| Bot | Field A bb/100 | vs v4 | Field B bb/100 | vs v4 |
|---|---|---|---|---|
| `bot.py` (v4) | **+24.0** (se 3.1) | — | **+26.4** (se 3.1) | — |
| `bot_v32.py` (v3.2) | +8.3 (se 3.2) | −15.7 (se 4.3) | +16.5 (se 2.5) | −9.9 (se 3.7) |
| `bot_v31.py` (v3.1, live v12) | +11.6 (se 3.4) | −12.4 (se 4.4) | +19.3 (se 3.9) | −7.2 (se 4.5) |
| WBot v10 code (`PokerBot/kit/bot.py` on main) | +5.4 (se 3.4) | −18.7 (se 4.7) | +17.6 (se 3.7) | −8.8 (se 4.5) |
| Red local code (older than the live Red v4) | +14.6 (se 3.0) | −9.4 (se 4.2) | +14.5 (se 2.6) | −12.0 (se 4.1) |

**v4 beat every other bot in both fields, by 7–19 bb/100 (about 2–4 standard errors).**

Read this with one important caveat. Here 5 of the 8 seats were bots that bet 95%+ of the time when
checked to, and v4's more selective style profits from exactly those opponents. The real tables
mostly hold other teams. When each bot instead played alone in the clone field (`tools/bench2.py`),
v4 was about level with v3.2 in field A and 7–18 bb/100 worse in field B.

So: v4 is clearly best **when our bots meet each other**; against the field it is **not proven
better**. Please repeat this run with your current Red and WBot builds, and with more seeds.
