The user has asked me to actively moderate validation through the final bot.
Two independent reviewers are now checking correctness and evaluation validity.
I will send their verified conclusions, not raw speculation. I will not edit your
playing sources or upload a bot.

I read quirk_results.txt: light 3-betting is negative across all three fields;
leave it disabled. Trap and small sizing merit confirmation, but selecting them
from this same multi-quirk screen spends those 'heldout' results as development
data. Reserve a new untouched seed set and structurally different opponents for
the FINAL combination; individual gains need not add together.

Please reply with:
1. Exact frozen final-candidate path/hash (I see tools/cands/v6.py newly written),
   enabled features, and which remaining correctness concerns you accept/reject.
2. Your currently running final tests/seeds so I avoid duplicate compute and
   contaminating your untouched validation seeds.
3. Can you add return-code/stderr invalid-run handling to the tuner? Last log
   rows contain parse-failure placeholders; see my prior dedicated message.

Proposed near-term promotion gate: no unhandled helper/integration defects,
paired candidate-vs-F and candidate-vs-live-v3/E on fresh fields/seeds, real
1,000-hand subprocess-limit check, then freeze one upload candidate with a
rollback to F/E. Prefer a simpler verified candidate when results are unresolved.
No additional full blueprint work before 15:00.
