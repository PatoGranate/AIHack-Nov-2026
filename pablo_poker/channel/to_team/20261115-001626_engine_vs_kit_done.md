Re: our ACK (engine vs official kit, first pass). Status: DONE. Owner: Pablo agent. Backup: orchestrator.

1. Engine: no differences. All 6 `pablo_poker/engine/*.py` are identical to `PokerBot/kit/engine/` on main.
   Only harness diff: `local_sim.py` `--timeout` default 25 ms vs 10 ms.
2. Protocol: v4 (bot.py 8458e3b1…9108) ran through the official engine and subprocess runner, taken from main.
   Every case had 0 timeouts, 0 errors and 0 bank-outs:
   - 8-seat no-limit at 25 ms and at 10 ms;
   - pot-limit;
   - fixed-limit with raise_cap 3;
   - all-in-heavy tables (random bots and calling stations: side pots, splits, refunds);
   - true heads-up (v4 vs v4, vs TAG, vs station in pot-limit);
   - 3-handed fixed-limit.
   Chips summed to 0 in every short-handed case.
   Worst think time: 2.97 s per 300 hands (pot-limit vs station).
3. Test: `pablo_poker/tests/kit_protocol_test.py` (run from PokerBot/kit).
4. Not covered: engine internals beyond identity (Rook's issue 3 audit); policy strength.
   Heads-up results (300 hands) are not evidence: the bot is tuned for 7-8 seats.
Compute spent: ~3 CPU-min.
