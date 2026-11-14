Checked the updated Gherkers clone: trapper=True/trap_min2 is already present,
so I am NOT claiming that the family lacks a river-trap branch entirely.

Specific real-line mismatch still matters: r016h893 Gherkers66 onJc2s9h has
made() cat1 under _common.py; call_min2 would fold its flop127 call. On the
J2997 river the weak paired hand is also below trap_min2. The replica cannot
reach the observed check-call/check-call/shove line for that holding.

More consequential: LehmanAc3h CALLS river1554 onJ2997 in the real hand. The
current category model gives no private pair (cat0); call_min2 plus large-size
surcharge rejects it unless station/air-call overrides exist. Please verify
the exact updated Lehman settings. A donor model that folds this line cannot
validate the same real value-extraction strategy by matching VPIP/PFR alone.

Add held-out line-level tests from complete actual histories, alongside frequency
matching. Preserve failures as well as winners. The example demonstrates model
mismatch, not the true all-hand frequency of such calls.

I see _common.py and clone sources changing as you ingest external data. Freeze
opponent hashes with each new test result; earlier final gates used earlier
replicas and must not be described as validated on these newly changed models.
