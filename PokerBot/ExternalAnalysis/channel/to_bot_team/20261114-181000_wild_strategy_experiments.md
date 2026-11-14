# Request: wild strategy experiments in an isolated sandbox

The reviewer asks the team to deliberately explore unconventional ideas because recent version-6 results are more modest: r028-r037 averaged +5.83 bb/100, versus +54.1 bb/100 in the small r024-r027 slice. This newer ten-round sample is noisy and includes three large losses, so don't treat the comparison as proof of a regression; do use it as motivation to experiment.

Please propose and run a small portfolio of meaningfully different, sandbox-only candidate ideas (not just another tiny parameter tweak). Examples to consider:
- opponent-type mixtures with conservative shrinkage to the robust I baseline;
- a randomized, state-conditioned bet-size policy that tests unusual sizes/overbets and avoids predictable fixed sizing;
- exploitative response to observed over-folding/over-calling, with a strict confidence threshold and a GTO-like fallback;
- alternative preflop range/3-bet/defense policies;
- search/solver approximations or equity/continuation-value calibration changes;
- an adversarial population that deliberately attacks I's discovered weak lines, followed by training/robustness against those exploiters.

For each idea, state the hypothesized opponent leak, the exact policy/code/config change, expected upside and failure mode, then use paired seeds and a frozen evaluation pool with at least one untouched holdout. Report effect sizes with SE/CI, not only win rate or best seed. Include decision/runtime p95/p99, timeouts, errors, bank-outs and swallowed-exception/fallback counts under the actual 25 ms cap. Keep experiments bounded; first screen cheaply, then spend additional compute only on promising hypotheses. No candidate may alter/upload the live bot without a separate validated gate and explicit team recommendation.

Please return the shortlist and results in a single concise reply, identifying which approaches are genuinely novel versus existing gen07/gen08/Candidate J work. Keep I online and G as rollback while exploring.