# HU raised-response EV: count existing opponent wager once

Base: `pablo-poker` commit `24653c92256ad1b7b14c37b0b206254cf1a4c6c5`.
Original standalone export LF SHA256: `8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108`.
Corrected standalone export LF SHA256: `7a280cbeb3f526d62750916dd747a6ecdd97cb4968b4fcfdaf8752dcfe74474f`.

When hero faces an existing opponent wager, the pot already contains that wager.
If hero eventually adds `a2` to match a re-raise, villain's new contribution is
`my_bet + a2 - bet_j`. The former `pot + 2*a2` terminal pot double-counted
`bet_j - my_bet`. Both the current export and `pokerbot/v2.py` now subtract that
gap, so `export_v2.py` preserves the repair. This changes one arithmetic line in
each file; no parameters, models, raise thresholds or runtime caps change.

Run from the repository root:

```text
python pablo_poker/tools/test_raise_ev_accounting.py
```

The stdlib fixtures extract and execute each actual source AST expression. Each
file passes 16 independent contribution-ledger cases: shares 0, 0.5, 0.6 and 1;
no existing call and positive existing calls; and matched hero/villain capped
contributions. For a 100-chip existing call, the old expression overstated EV by
100/50/60 chips at shares 1/0.5/0.6. Zero-call and zero-share cases are unchanged.
Unmatched excess/refunds/side pots and broader raise-size approximations are not
certified by these fixtures.

## Existing bounded diagnostic evidence

Before this integration PR, the isolated corrected export was compared with the
exact original export on fresh seeds `92100000` through `92100007`: eight paired
1,000-hand tables, fixed 32 Monte Carlo samples, per-decision seeded heroes and
all seven `sunday_v2` clones. Both builds passed A-v-A before the pilot. Total
16,080 table-hands including QA; no new simulations were run for this PR.

All eight paired outcomes were identical. Each arm had 1,374 postflop decisions;
35 had corrected raised-response EV terms, but no selected action changed. Mean
paired effect and sample SE were both zero. The resulting degenerate empirical
interval does not prove the true policy-value effect is zero. This is a
correctness repair, not a measured strength improvement or deployment approval.

Existing detailed report, to be published by the orchestrator:
`PokerBot/ExternalAnalysis/Pablo_Raise_EV_Correction.md`.
Raw fixtures, A-v-A hashes, preregistered manifest and eight paired outputs:
`PokerBot/ExternalAnalysis/AgentReports/Pablo_Raise_EV_Fix_92100000/`.
Raw paired-output SHA256:
`e3ab0236e228dbcd0fadd41884f86fffb055dea0e6890df555f3252d57bc5637`.

The frozen local collector export was not edited. Exact production-runtime and
fallback observability checks remain separate gates. No promotion is claimed.
