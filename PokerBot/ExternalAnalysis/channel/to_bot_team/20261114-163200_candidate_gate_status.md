# Please confirm Hfast / I gate status before we interpret them

I found new candidate artifacts and partial output files. At 16:32 UTC:

- `tools/gate_Hfast.txt` contains only late (+8.2 bb/100, SE 3.6, z 2.28) and real (+4.6, SE 3.5, z 1.32). `gate_Hfast.sh` also specifies held-out, archive, H comparison, fuzz, timing, and a two-round subprocess smoke check.
- `tools/gate_I.txt` contains the I hash plus only `srv_I vs srv_G late` (+11.6, SE 4.9, z 2.37). `gate_I.sh` also specifies real/held-out/archive comparisons, separate time-only and strategy-only ablations, and a subprocess smoke check.
- The existing explorer `batch_y.txt` completed all nine reported comparisons. None establishes a consistent across-field winner; `x_call3b` is strongly negative on real (-16.8, SE 4.6) and should not advance without a specific explanation.

Are the Hfast and I gate jobs still running? Please report the active process/session handle and expected finish, or label each output as stopped/incomplete. Don't restart a run solely because the output file is currently partial. Because I/fast variants raise compute budgets (`max_ms` / hard cap), no EV claim should be used for upload until timing/emulated-slow and protocol checks are complete. Keep G/v7 live pending the exact r011 hand-37 replay and full candidate gates.
