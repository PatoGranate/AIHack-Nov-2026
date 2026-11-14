User supplied new other-table histories under
Hand_data/ExternalData_OtherBots (r013-r017). Two independent reviewers and I
are analysing actual opponent actions now, not just cloning aggregate results.

Important data identity rule: ref alone is insufficient across tables. Dedup
by (ref, ordered player roster), verifying hand events. External r015 includes
WBot at -3314 chips and appears to be the same table as r1v3 from another
observer. It may add visible card information, but is not another independent
1000-hand performance sample. Six-, seven- and eight-seat tables appear.

Descriptive results in external-only data: Market Makers +121.83bb/100 over2k,
Gherkers +104.20 over2k, Kojack +96.69 over2k. Very large losses from Lehman
Brothers -408.88 over2k, FisherMen -150.40 over2k, bigRoddy -237.87 over1k.
Do not infer universal strength: opponent composition/stack-off donations matter.

I will send conditional-response rates, sizes and exact examples shortly, with
counts and uncertainty. This should guide structurally better test opponents
and exploitation choices after validating G's rollout; avoid blind changes to
the frozen pre15:00 candidate based solely on these raw scores.
