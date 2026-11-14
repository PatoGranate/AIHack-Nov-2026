# G/v7 weak-equity commitment line audit
Date: 2026-11-14
Scope: deployed G/v7 clone, local gen03/gen04 candidates, and verified own-table r009/r010 logs. This is a hand-selection diagnostic, not an ex-ante EV estimate.

## Deployment identity

`submissions/G_v7_final/bot.py`, `kit/bot.py`, and `tools/cands/v7.py` hash identically: `b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a`. The team reports website version 5 is this G/v7 hash. The review therefore targets the reported deployed strategy source.

## Exact target hands

- **r009 h333, AQ-high turn re-raise all-in:** WBot opens to 70, flop-bets 170, calls ND's raise to 510 (340 more), then on 6c3s7dTh bets 178, faces ND's raise to 534, and reraises all-in to 1420 (1242 more) into a 1902 pot. ND calls with TdTc. WBot had 0% on the 44-card revealed-hand river set (hindsight only). Audit: `IndependentChecks/Round9TableE/Round9_Audit.json`, row 333.
- **r010 h124, AK-high flop all-in raise:** four players see Th6cTc; Mohil raises to 200 into 400, WBot raises all-in (1950 more), Mohil calls with KcTs. WBot's hindsight equity vs Mohil is 5.5% with 990 exact runouts. This is a multiway, high-variance decision; the shown hand does not reveal WBot's contemporaneous range estimate. Audit: `IndependentChecks/Round10Audit/Round10_Audit.json`, row 124.
- **r010 h420, K8 turn re-raise all-in:** after WBot open-raises BTN and raises/calls on 2s9d5s, kaiserbot bets 689 on 2s9d5s6c; WBot raises all-in to 1483 into 1733 holding Kc8c. kaiserbot calls with Kh9h (top pair); WBot has 9.1% hindsight equity (44 exact runouts). Audit row 420.
- **r010 h469, KJ turn all-in (correction to the premise):** after the flop raise/call on 3d4c7s, the turn Td checks through to WBot; WBot then shoves 1483 into 1044 with KsJs, first-in, and kaiserbot calls with Ac3c. This was not a shove over a kaiserbot turn raise. WBot had 13.6% hindsight equity (44 exact runouts). Audit row 469.

These four losses are striking and justify an action-line audit, but are outcome-selected and do not alone establish a systematic leak. The h333 / h420 spots include a prior bet/call-raise pattern; h124 is multiway and facing a large raise; h469 is an unraised checked-to turn bluff. They should not be pooled as one identical decision.

## Code path and likely risk

- `tools/cands/v7.py:667-714`: `opp_models` counts postflop raises (`agg`) and whether the villain raised over a bet (`raise_over`), then uses broad coarse hand-class weights (`w_r_air`, `w_r_weak`, `w_r_mid`; lines 696-700). This does partially recognize aggression.
- `tools/cands/v7.py:701-703`: opponent continue probabilities come from the smoothed overall fold-to-bet rate `ftb(j)` (lines 476-478), not a conditional response model for “I raised/bet, got called/raised, and now face a re-raise/all-in,” nor from size-specific continuation. This can overstate fold equity in h333/h420-like sequences. In h124, the model also has to estimate multiway calls from separately modeled opponents.
- `tools/cands/v7.py:743-763`: size dependence is applied by exponentiating the same coarse continue rates; `fold_vs_raise` is 1.0 by default, so it does not add a special fold adjustment for a raise candidate.
- `tools/cands/v7.py:967-981`: candidates are built from `[1.0, 2.0] * (pot + to_call)` for raises and clipped to the legal maximum; clipping can collapse them to the same near-all-in size. No explicit minimum-raise/intermediate candidate is added. In h333, a smaller legal raise (if present in the reconstructed state’s legal interval) may be missing; in h420, the legal raise interval itself may be narrow because the bet is already 689 into a large pot. Confirm by replaying exact engine states before calling this a defect.
- `tools/cands/v7.py:1009-1013`: `raise_margin=-0.04` yields a +0.04-pot bonus (`bonus = -raise_margin * pot`) to each raise EV. This can tilt marginal estimates toward aggression; it is an intentional parameter, not by itself a bug.

## Do gen03/gen04 fix the pattern?

No targeted opponent-response or commitment fix is present. The files retain the same `opp_models`, continuation model, `raise_sizes=[1.0,2.0]`, raise EV bonus and postflop logic as v7. Source diff shows gen03 only changes `size_exp` from 1.0 to .575, `max_sims` 1500 to 3000, `max_ms` 1.2 to 2.2, and `hard_ms` 3.0 to 4.5. Gen04 adds `bet_sizes=[0.4,0.75]` (instead of [.33,.6,1.0]) and raises `shove_spr` 5 to 6.05. Both retain the same raise candidate grid. Thus they may alter EV noise, continuation’s size curve, and which sizes are offered, but neither conditions folds on the current raise/call line; gen04 makes more max-shove candidates eligible, not fewer.

Team-reported exploratory result for gen04: late held-out clone field +7.4 bb/100, SE 4.2; archive field -4.3, SE 6.2. That split is not a robust positive result and gen04 has not passed the full gate. Do not promote it from these hands.

## Judgment / safe paired test

The strongest code-level risk is **continuation/range calibration after opponent aggression**, with a secondary candidate-grid risk where pot-scaled raise sizes clip to one maximum. The observed sequence supports testing that model; it does not prove the jams were necessarily bad when made. There is no evidence here of a simple illegal-size or stack-accounting bug. h469 specifically should not be described as a response to a turn raise.

Keep G/v7 frozen as baseline. Before changing source, replay all complete decisions in r009/r010 and log the exact v7/gen03/gen04 selected action, every candidate size and EV, opponent range weights, continue probabilities, sample count and seed; confirm action-state reconstruction (including legal min/max raise and live-player count) against the engine. Add an explicit legal min-raise/intermediate candidate as a single sizing ablation. Separately test a line-conditioned opponent continue model after bet/call-raise/raise sequences. Run each ablation as paired fresh seeds against the same held-out late, real, archive and structurally diverse fields; include winning and losing examples, report paired bb/100 intervals, all-seat errors and timeouts. Keep r009/r010 diagnostic, not tuning/confirmation data.
