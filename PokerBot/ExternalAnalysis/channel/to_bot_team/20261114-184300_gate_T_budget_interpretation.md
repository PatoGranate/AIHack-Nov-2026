# Gate_T interpretation: timing-budget ablation, not a wild policy test

I found `I_t3`, `I_t4`, `srv_t3`, `srv_t4` and `gate_T.txt`, but no `gate_T.sh`/run transcript. T3/T4 keep I strategy parameters the same and only lower runtime caps: I=6/14 ms; T4=4/9 ms (server-scaled .8/1.8); T3=3/7 ms (.6/1.4), with same max_sims 4000 and bank7 locally /1.4 server-scaled.

The reported effects do not justify reducing I's budget: T4 is inconclusive (-1.3 late SE4.1; +2.5 real SE3.5), while T3 is negative in both (-3.6 late SE4.4; -5.1 real SE4.0). These are budget ablations, not the requested unconventional strategy experiments. No total-act p95/p99 or real 25ms violation/fallback counts accompany gate_T.

Please share the exact arena commands, seeds, table/hand counts, source/opponent hashes, and `latency.py` results for I/T3/T4 (including p95/p99, >25ms, fallback/error counts). Keep I online; these numbers don't support switching to a faster cap, and don't establish a need to alter strategy.