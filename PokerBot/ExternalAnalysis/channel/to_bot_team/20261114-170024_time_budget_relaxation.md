# User request: use more of the available decision time; relax conservative triggers

The user thinks we are playing too safely with missed opponent-exploit opportunities and wants to maximize useful thinking/action time (the bot does not need to be ultra-fast). Current checked time is 17:00:24 UTC / 17:00:24 London.

Please investigate with a controlled candidate sweep; do not edit the live submission directly. For I (`tools/cands/I.py`), the current config is `max_ms=6`, `hard_ms=14`, `max_sims=4000`, `q_min_obs=8`, and `bank=7.0`. The server-scaled `srv_I.py` is much tighter (`max_ms=1.2`, `hard_ms=2.8`, `bank=1.4`). The reported server decision cap is 25 ms, so this looks like a possible source of under-thinking, but please confirm exactly how the server wall-clock limit maps to local and `srv_*` tests before changing numbers.

Suggested experiment:
1. Keep an immutable I baseline. Sweep actual server-equivalent think-time budgets upward in measured steps, targeting roughly 80–90% of the verified 25 ms cap at p95/p99 (retain margin for serialization/scheduler overhead); include timeout/error/bank-out rates and decisions/simulations per action. Do not infer safety from configured budgets alone.
2. Separately test `q_min_obs` 8 vs 6 vs 4 for the steal/3-bet exploits, with posterior shrinkage left intact. Log how often each trigger is skipped for insufficient observations and counterfactual EV at those opportunities. Separate this threshold ablation from the time-budget sweep, then test a combined candidate only if both improve.
3. Use paired seeds/seats against G and I, plus real external snapshots and genuinely held-out tables. Report mean delta, SE/CI, sample size and runtime tails. Preserve G/I rollback. No promotion recommendation until the higher budget passes the real server limit with margin.

The intent is to reduce unnecessary conservatism while protecting against increased timeouts and noisy low-sample exploits. Please clarify the clock mapping and send back the actual sweep results before we change the live version.