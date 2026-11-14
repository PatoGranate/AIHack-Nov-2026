Independent checks completed:

1. My frozen-v7 DEBUG=True smoke: 2 x 1,000 hands versus maniacs, wide shover,
station, TAG, LAG and minraiser. ZERO surfaced exceptions at ALL seven seats.
Snapshot SHA256 b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a.
LocalPlayer only: this does not validate external timing or establish win rate.
Evidence: IndependentChecks/debug_smoke_results.json and script.

2. Independent reachable-state audit: 3,000 reset-stack hands, 45,356 states,
15,732 postflop, 2,872 postflop facing all-in. No short-total-all-in call trigger
and no live opponent street cap below hero max_raise_to. This confirms the
earlier short-stack concerns do not occur in this game's equal-reset format.
See check_reset_stack_invariants.py and its results under IndependentChecks.

3. Reachable TRAP strategy concern: any aggressive live opponent currently
satisfies the AF trigger, including an earlier actor who has ALREADY CHECKED,
while only passive opponents remain behind hero. A controlled policy test
confirmed the trap checks solely due to the earlier actor's AF. Consider gating
the trigger to opponents still to act after hero, or separately model their
check-raise likelihood. Classify this as a strategy-model weakness, not a proven
negative-EV correctness bug. Avoid silently modifying the frozen v7 during its
final comparison: any change creates a new candidate requiring revalidation.

The independent evaluation audit reiterates all-seat errors and exact artifact
hashes at promotion. Reports: Evaluation_Audit_1433.txt and Promotion_Gate_v7.txt.
