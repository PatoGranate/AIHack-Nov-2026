# V4: what blocks a trustworthy edge, and the Table D opportunity

Read-only assessment, 2026-11-15. No strategy or simulator changes, no large runs. This combines inspected code with Claude's supplied handover; the handover's benchmark claims were not independently rerun. Earlier snapshot findings must not be treated as current without verification.

## Finding

The system can reproduce some observed frequencies, but cannot yet reproduce the conditional decisions that generate opponents' profits. Its largest problem is not Monte Carlo noise: important parts of the real strategies are outside the clone model's representation. The live policy then optimizes against those errors. More games cannot fix this structural bias.

Repeated Table D membership is a real advantage. It reduces uncertainty about who is present and gives repeated observations of the same seven opponents. It does not reveal folded cards, fix the simulator automatically, preserve runtime memory, or freeze opponents' code and adaptation.

## 1. Determinism does not imply that a strategy is identifiable

A deterministic policy chooses an action from its full input and internal state. We do not observe its hole cards except selected showdowns, all its internal state, or necessarily its current source/version. We also do not observe what it would do after our counterfactual actions. The same observed history can be explained by multiple deterministic policies that differ on unobserved hands.

The current implementation is also not simply a deterministic lookup: it uses seeded random sampling and wall-clock MC deadlines. A fixed seed only reproduces a run if the work budget, opponent lineup, state initialization, model snapshots, global caches, and execution order are controlled. Deterministic source can still produce different outcomes on different dealt cards. Exact source access to WBot does not grant exact source access to its opponents.

Target: predict decision-relevant behaviour with calibrated uncertainty. Exact strategy reconstruction is neither established nor necessary for profitable exploitation.

## 2. The principal blockers

| Blocker | Evidence / status | Why it matters | Remedy |
|---|---|---|---|
| Marginal frequencies are mistaken for strategy fidelity | Confirmed: FieldBot uses contextual quotas and hand-strength quantiles | Same fold/raise rates can select very different cards and produce different EV | Fit joint action–size–strength–sequence predictions and test out of time |
| Default clone does not carry a full inferred range history | Confirmed: `postflop_abs` mostly recomputes strength against random hands or one size-weighted bettor | Preflop selection, previous checks/calls and multi-street filtering determine what reaches river | Propagate a legal weighted range through the whole hand; contextual likelihoods |
| Coarse skill knob has insufficient degrees of freedom | Confirmed: positive skill adjusts facing-bet equity; negative skill adds noise | Cannot represent sizing, traps, preflop construction, selective pressure, and future planning as one scalar | Separate measurable components; use residual errors to choose features |
| Showdown selection and policy-dependent missingness | Fundamental data limitation | Shown strength is conditional on being called and reaching showdown, not unconditional betting strength | Match visibility filters; model reach/showdown; retain bounds for unseen actions |
| Adaptation changes quotas, not necessarily the distribution reaching a decision | Confirmed: aggression interpolation shifts fold/raise rates | Wider continuation can dilute hand strength when the model lacks traps/context | Condition on sequence, board, image, position, range; predict responses jointly |
| Hidden global state changes the experiment | Confirmed: `_POOL`, `_OWN`, `_SKILL`, `_V3`, warm files and environment modes | Candidate order and worker lifetime can change the field | Freeze/hash inputs; reset per-run state; isolate paired runs; order-invariance check |
| Identity confidence is not calibrated | Prior temporal replay: 15/20 correct, four confidently wrong after 1,000 hands | Strong exploits can target the wrong player | Table D-only joint matching, uncertainty, new-version escape state |
| Coarse EV model can turn a good read into a bad action | Confirmed source: scalar realization, four hand levels, simplified raises | Style corrections do not establish profitable bets/calls | Audit action values and range updates separately from matching frequencies |
| Tests differ from deployment | Confirmed: benchmark caps MC at 400 while final configs allow more under clocks | Different decision noise or code/model versions invalidate attribution | Exact final bytes and realistic budget, plus controlled fixed-work comparisons |
| Version, seat, timing and hero identity are fragmented | Confirmed: several scripts hard-code kaiserbot; Saturday parsing remains | WBot can receive the wrong priors, model or evaluation | One explicit team/stage/roster/version manifest; confirmed upload activation |
| Evidence target changes while fitting | Claude reports different fields and tuning choices | Selection on favorable metrics produces optimistic conclusions | Frozen temporal splits, preregistered metrics and held-out policy comparisons |
| Insufficient evidence in important rare cells | Confirmed earlier observations; Claude reports tens of river examples | Point-estimated exploits can be expensive mistakes | Hierarchical posteriors, actual opportunity counts and confidence-sensitive actions |

These blockers interact. There is no justified single correction factor to subtract from simulated profit, especially when WBot, Red, and kaiserbot have different biases.

## 3. Concrete current-code concerns beyond the handover

1. `postflop_abs` caps equity opponents at three, treating larger multiway situations with a reduced opponent count. Even when used as a ranking signal rather than literal equity, this changes relevant strength ordering and context.
2. `hand_strength_vs` draws one bettor through a four-level acceptance rule and treats the remaining opponents as random hands. It does not reconstruct each opponent's actual preflop and postflop range.
3. The acceptance loop tries eight candidates and then uses the last candidate even if it failed acceptance. When acceptance is rare, this injects hands outside the intended distribution. This is a concrete candidate for a cheap sampler-distribution test.
4. The absolute-strength mode looks up `str(min(b, 6))`: the rich model's >=2-pot bucket 7 is mapped to live-model bucket 6, which describes raises, not specifically large first bets. The live and rich model bucket schemas need explicit reconciliation.
5. The quantile thresholds force continuation/raising frequencies against a pooled strength distribution. Improving hand reading can change ranks without reproducing actual decision quality; it cannot magically supply missing conditional range structure. Unconditional quotas are not a complete policy.
6. The betting branch's low-quantile bluff rule overlaps its sigmoid value-bet probability. The resulting marginal betting rate is not automatically the nominal rate, especially with nonuniform or drifting quantiles. Validate the actual emitted rates, including trap suppression.
7. The adaptation code clips fold and raise probabilities separately and computes call as `max(0,1-fold-raise)`. The code does not generally guarantee the three numbers sum to one after shifts. Check realized action probabilities under extreme calibration deltas.
8. `calib_skill.py` fits from Saturday rounds 38 onward without a supplied temporal holdout boundary. As written, using that fitted file in validation of overlapping rounds leaks target information. Its showdown win definition is positive net chips, not exact pot-share or best-hand frequency; ties and side pots can matter.
9. The positive skill mechanism uses population size-to-strength tables. A bot-specific scalar cannot create bot-specific sequence/range knowledge. A parameter saturating while the residual remains systematic is evidence of missing model structure, not necessarily a request for a wider parameter bound.
10. Several consequential facts are inferred from shown hands alone. A board-level class of “strong” does not distinguish weak trips from dominant trips, or a vulnerable straight from the nuts. Selection by relative equity and blockers can differ materially from four-level selection.
11. V4's response-to-raise model uses a strong/not-strong split. Multiway strong-hand handling does not fully model the additional raise investment and subsequent decisions; weak hands can be treated as automatically surrendering to a raise. Action-value accounting needs direct tests, not HUD-rate matching.
12. Current source defaults still have a negative `raise_margin`, with newer street adjustments. Inspect the exact combined exported values before attributing excessive raises to range inference alone. The betting exponent cap and high top-pair continuation also remain potential causes of oversized thin value.

These are source-level mechanisms and test targets. Their individual bb/100 impact has not been measured. Some affect calibration more than direct live play.

## 4. Why “fold less but call stronger” is not a contradiction in reality

Holding the same distribution of opportunities fixed, if a clone already calls the strongest hands, adding weaker hands generally weakens its average calling range. That is a property of this particular threshold construction.

Real observations need not hold the distribution fixed. Opponents may:

- Arrive at that street with stronger ranges due to earlier folds, calls, and raises.
- Check strong hands to a frequent bettor, then call or raise.
- Continue more often against small weak bets, while remaining selective against large bets.
- Raise strong hands and selected bluffs instead of merely widening calls.
- React to position, board, blockers, earlier actions and an opponent's visible tendencies.

Aggregating these contexts can show lower folds and stronger revealed hands simultaneously. The current adaptation slider changes one rate without representing all those mechanisms. If the real target lies outside both calibrated endpoints, interpolation cannot reach it; the model family needs new dimensions.

Cheap next test: decompose the discrepancy by street × first bet/raise × size × HU/multiway × initiative × board family. Compare opportunity counts and reach rates before adjusting call thresholds. Determine whether the mismatch is who reaches the decision, hand selection at that decision, or later showdown filtering.

## 5. What “behave like a winner” should mean

The primary objective is profitable decisions and ultimately top-two qualification. A winner's HUD rates are diagnostic references, not goals to duplicate. High showdown win percentage can be manufactured by folding too often. Aggressive pressure can lower showdown win rate while increasing profit. Two profitable strategies may have different opening, betting, and three-bet frequencies.

Also, a real winner's +26.5 bb/100 is measured against a particular changing population, not an absolute skill rating transferable to every lineup. Replacing a participant changes everyone's opportunities and payoffs. Compare policies on the same specified field, seats, cards, model versions and work budget; use held-out results with uncertainty.

Separate four claims:

1. Reproducible: repeated experiments have controlled inputs and state.
2. Predictive: model forecasts held-out actions/sizes/strength and reach frequencies.
3. Calibrated: aggregate outcomes are compatible with held-out evidence under uncertainty.
4. Profitable: candidate improves the actual decision objective against robust independent opponents.

Passing an earlier claim does not establish a later one. We do not currently have independent proof of claim 4 for V4.

## 6. Table D: exploit the seven actual opponents

The seven opponents are Resonance Qt, Anker Batteries, Chinese people can fly, GamesGone, Poke, Anton, and YSL_TWIZZY. WBot is the eighth participant, not another model to clone as an opponent. Membership is supplied by the user; do not assume physical seats or opponent code are fixed.

### Before round one

- Confirm the actual WBot upload and hash. Local `bot.py` and `data/v4_bot.py` now match: SHA-256 `8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108`. This resolves the earlier local-artifact mismatch, not remote upload verification.
- Keep a known-good fallback; do not declare V4 superior based on style or favorable simulations.
- Assemble current-version Table D priors from existing history. Do not start from zero: all seven already have profiles. Audit which history belongs to their present versions.
- Restrict identity candidates to this roster plus unknown/new version. Jointly assign seven names to seven seats, carrying alternatives; do not force certainty.
- Confirm ingestion and upload turnaround. The format text supplied by the user says uploads close at 12:00, which indicates uploads are open during the bucket stage. Verify activation timing operationally; there is no need to treat the published closing time as absent.

### During round one

Observe every public action, including after WBot folds. Use existing historical priors, update broad per-opponent tendencies, and exploit only sufficiently supported differences. Do not spend 1,000 hands doing nothing but classification. Keep identity and behavioural confidence separate: an uncertain name may still imply a robust shared tendency.

Prioritize frequent, cheap-to-estimate situations: positional opening, response to normal opens and three-bets, small flop bets, and ordinary continuation patterns. Rare river raise rates require pooling and uncertainty; a thousand hands is not a thousand river observations.

### Between rounds

Persist evidence outside the reset sandbox, keyed by team/version/context. Reconcile hand IDs, count actual opportunities, exclude future information, and maintain training watermarks to prevent double counting. Bake posterior sufficient statistics into the next approved upload and record its effective round. If the deadline is missed, use the last valid model and record the delay.

Seat identity must be reassessed each fresh round. If position mapping is explicitly available and stable, verify it; otherwise do not persist seat numbers as team identities. Confirmed uploads or behaviour changes should reduce confidence in old tendencies selectively.

### Rounds 2–36

Repeat learning and revision rather than freeze the round-one interpretation. Track how each opponent answers WBot, not only a pooled average against kaiserbot/WBot/Red. Watch for counter-adaptation and code changes. Spend exploration only on close-EV actions whose information is likely to affect many future opportunities; do not buy expensive river information indiscriminately.

### Initial hypotheses, not automatic exploits

Existing pooled profiles suggest investigating:

- Chinese people can fly / YSL_TWIZZY: selective preflop re-raise pressure if their high fold-to-three-bet estimates persist in the relevant context.
- Poke: wide passive entry ranges; investigate isolation and value opportunities.
- Anton: lower fold-to-re-raise than the two names above; avoid applying the same bluff strategy universally.
- YSL_TWIZZY: low postflop fold rate despite tight preflop style; do not equate “tight opener” with “easy postflop bluff target”.

Verify current-version counts, sizes, positions and players behind before using these. A leak against one opponent does not justify a bet that another opponent will punish.

## 7. A practical validation sequence under the low-budget constraint

Do not run millions of hands yet. Respect the existing large-run restriction; changing it requires the orchestrator's authorization, not reinterpretation.

1. **Reproduce:** freeze complete input manifest, including field model, skill file, adaptation file, live size model, HS pool, environment modes, hero bytes and parameters. Reset caches. Check paired-run order invariance on a small sample.
2. **Contract tests:** incremental calls, legal sizing, sampler acceptance distributions, bucket mappings, probability normalization, side pots, all-ins, and raising investment. These are cheap and can find defects without noisy tournaments.
3. **Temporal prediction:** train on earlier rounds and predict later Table D actions. Report proper scoring metrics and confidence calibration, not just rate agreement. Evaluate identity at 25/100/250/1,000 hands.
4. **Joint calibration:** compare actions, sizes, strength, board/context reach and showdown selection together. Test WBot-specific response separately from aggregate response. Use comparable visibility filters and sample uncertainty.
5. **Model disagreement:** build several plausible opponent models consistent with data. Prefer improvements whose EV direction is stable across them; flag decisions that depend on unidentifiable hidden ranges.
6. **Small policy ablations:** identification only, contextual priors only, EV corrections only; compare V3.1/V3.2/V4 with full provenance and confidence intervals. Do not use a changed benchmark to erase an unfavorable result.
7. **Authorized large runs:** only after the field passes independent checks, run full-stage comparisons with fresh agents, realistic uploads, rotated seats and adaptive opponents. Evaluate total chips and top-two probability, clustering uncertainty over complete bucket runs.

A perfect per-opponent real-profit match is not a sensible hard requirement on a tiny sample. Real profit is noisy and depends on lineup. Require compatible held-out outcomes and well-calibrated conditional predictions across multiple policies/lineups, with uncertainty. Matching three historical hero returns is useful evidence, but not sufficient proof of a faithful simulator either.

## 8. Qualification, coordination and remaining unknowns

Early in the stage maximize well-supported chip EV. Near the end, qualification probability may depend on the gap to third place and remaining rounds. This is not standard elimination-poker ICM: stacks reset each hand. Avoid arbitrary survival penalties on profitable calls. Standings-aware variance choices need full-table simulation, since opponents win chips from each other.

Important unknowns to resolve before promotion:

- Which exact artifact is uploaded as WBot, and when does a replacement become effective?
- Which versions of the seven opponents are current? Are their fingerprints stable?
- What are the existing orchestrator's exact benchmark and budget rules, and the status of its independent run?
- Which model files, seeds and source commits generated each published comparison?
- How much of the error is range reach, continuation selection, sizing, future play or accounting? Current aggregates cannot identify the breakdown.
- How soon can a completed Sunday's round be fetched and an updated upload confirmed?
- Do correct identity/contextual predictions materially change decisions in the current EV engine, or get overridden by its approximations?

We should not require access to unseen opponent cards or exact code to make progress. We should require that uncertainty about them is carried into the decision, rather than silently replaced by a convenient threshold model.

## Recommendation

The immediate opportunity is a reliable WBot-specific learning loop against seven known opponents. The immediate blocker is a misspecified and incompletely reproducible evaluation model, not a shortage of simulated games. First diagnose conditional range/reach errors and the cheap source-level defects; in parallel establish roster-aware identity, persistent versioned evidence and confirmed uploads. Then evaluate conservative exploits that survive plausible opponent models. Stronger claims about V4 require independent profit evidence, not stylistic resemblance to winners.
