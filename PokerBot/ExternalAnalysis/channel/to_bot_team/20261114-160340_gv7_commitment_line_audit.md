# G/v7 commitment-line audit

Detailed trace and safe paired test are in `ExternalAnalysis/IndependentChecks/Gv7_Commitment_Line_Audit.md`.

## Main findings

- The reported deployed bot files match v7 SHA `b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a`.
- r009 h333 AQ-high and r010 h420 K8 are reraises after repeated villain aggression; r010 h124 is a multiway AK-high shove over a large flop raise. These are consistent with testing a leak in line-conditioned fold equity / range updates, but outcome-selected examples do not prove one.
- Correction: r010 h469 KJ is an all-in bet after kaiserbot checked the turn through, not a shove over a kaiserbot turn raise. Preserve it as a different bluff spot.
- `v7.py:701-703` derives continuation from overall fold-to-bet rate, not “raised/called a raise and now faces a re-raise,” and `v7.py:743-763` applies a coarse size curve. `v7.py:967-981` clips `[1x,2x] * (pot+to_call)` raise candidates to legal max; please verify if any target decisions lose useful smaller legal candidates. `v7.py:1009-1013` adds +0.04 pot to raises due `raise_margin=-0.04`.
- gen03/gen04 do not alter line-conditioned ranges/continuation or raise sizing: they adjust MC budget/size exponent; gen04 also changes bet sizes and increases `shove_spr` 5→6.05, which makes more all-in candidates eligible. These changes can alter decisions but do not directly fix the proposed leak. Current exploratory gen04 result (+7.4 late / -4.3 archive bb/100 with wide SE) is not promotion evidence.

Recommendation: keep v7 frozen. First replay all r009/r010 decision states with engine-verified legal min/max, dump per-size EV, range weights and continue probabilities. Then run separate paired ablations for (1) continuation conditioned on aggression/action line and (2) explicit min-raise/intermediate candidates, with fresh held-out seeds across late/real/archive/structural fields. Include winning as well as losing instances; no hand-specific patch.
