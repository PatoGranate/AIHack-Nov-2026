# Q independent audit: jam definition, evidence and EV limits

Audited 15 November 2026 before10:45 London. Exact source: `submissions/Q_P_x4/bot.py`, SHA256 `8233d8fa67ed0e8ff3fe10dfdffdcf09feb56ba6bdc60883a7455b9cb38109b1`. Source remains unchanged. No simulation or hidden-card information was used.

## Decision

Anton's high fold rate survives the stricter definition. It is a genuine descriptive signal worth testing, not a demonstrated +33bb/100 policy improvement. The known >=600 learner-label bug mixes non-all-in raises with jams, but this does not explain away the observed high fold rate here: strict jams have a higher fold rate. The strongest remaining EV concern is using a heads-up continuation payoff when other live seats can call. A deployment claim should also preserve uncertainty about response-range equity, recognition and policy-dependent changes in opponent behavior.

## Independently reconstructed public-action counts

Inputs: the original sixteen `Hand_data/SundayRaw/sunday_s1_r001.json` through `r016.json` files,16,000hands. File hashes, every qualifying four-bet event/opener-response opportunity and source-executed fixtures are saved in `ExternalAnalysis/AgentReports/Q_Independent_Audit/public_counts.json`.

Reproduce: `python -B tools/q_independent_audit.py` from PokerBot. Four-bet means the third preflop raise. Strict all-in means raise-to exhausts the bettor's publicly remaining stack, accounting for its existing wager. No shown or hidden cards enter the parser. Rates use the three-bettor's FIRST response with no intervening fifth raise, matching Q's nr==3 learning condition. Cold four-bets are counted separately from opener four-bets.

| Anton response context | Folds/responses | Fold rate | Wilson95% interval |
|---|---:|---:|---:|
| Any >=600 four-bet |158/172|91.86%|86.80–95.09%|
| Strict all-in four-bet |155/165|93.94%|89.20–96.68%|
| >=600 but not all-in |3/7|42.86%|15.82–74.95%|
| Strict all-in, WBot is four-bettor |32/34|94.12%|80.91–98.37%|
| Strict all-in, another team four-bets |123/131|93.89%|88.41–96.87%|
| Strict Q public filter: opener four-bets, prior target<600, no matched cold caller |132/140|94.29%|89.13–97.08%|
| Same strict Q filter, WBot opens and jams |30/31|96.77%|83.81–99.43%|
| Same strict Q filter, other opener jams |102/109|93.58%|87.33–96.85%|

WBot-as-opener and WBot-as-four-bettor are not interchangeable: Anton faced36strict jams in pots opened by WBot and folded35; some jams came from a different seat. The clearer policy-matched subset is31WBot opener jams,30folds. This is a selected historical range, not evidence that any two cards can profitably jam at that rate.

Actual opener-response opportunities after Anton re-raised WBot:592, with375folds/186calls/31raises. Of these,585meet the reconstructed Q public filters (cur<600,no matched caller,enough remaining chips beyond the call):368fold/186call/31raise. That is3.656opportunities per100hands, not an automatic jam frequency. It omits hidden legality/internal policy state and does not establish which hands satisfy Q's EV margin.553of585have no other live seat behind,31have one,and1has two. Existing31strict opener jams netted6,147chips across the whole hand; their selected results cannot be extrapolated to the other554opportunities.

Wilson intervals treat responses as independent and are descriptive; repeated opponents/rounds make that assumption optimistic. Rates are policy-,size- and selection-dependent. Current priors were built from these same sixteen rounds, so these counts validate descriptive extraction, not an independent holdout gain.

## Confirmed learner definition bug

`_pfx_learn` lines606–639 sets `jam = amount >=600`, not true stack exhaustion. Source-executed fixtures use identical open60/three-bet180/third-raise/fold histories: targets600,1999and2000all increase the same fold-to-jam denominator;599does not. In a2,000chip fixed-stack round,600and1999are not all-in.

Consequences: the f4 estimate and own-jam call/stop-loss counters include large non-jam four-bets. Correct the event definition using public starting stack/contributions, or explicitly rename and calibrate it as fold-to-large-four-bet. Do not claim that the current learner measures strict all-in responses. This correction should be separately frozen and evaluated; the inspected source was not edited.

## EV accounting and multiway risk

Q's heads-up formula uses `eff=min(hero total street capacity,raiser total capacity)`, `a_in=eff-hero_bet`, `final=pot+a_in+(eff-raiser_bet)`, then `fold_probability*pot + call_probability*(equity*final-a_in)`. For a sole caller and matched effective stacks, these are incremental chip amounts and existing wagers are counted once. A hero full shove above a shorter opponent's effective cap is economically equivalent after an unmatched refund when nobody else can call. No general sunk-cost/double-counting defect was established in that heads-up formula. The actual fixed2,000chip preflop format makes capacities equal before considering additional callers.

The code allows other live seats with wagers below cur. It multiplies the target's fold rate by `0.96**nbehind`, then assigns ALL non-fold branches the same equity versus Anton and the same heads-up final pot. This omits caller identity, stronger cold-call ranges, multiple callers, their added chips and possible unequal effective caps. The0.96factor is an unvalidated4% per-seat assumption, not a modeled multiway payoff. This is a material approximation rather than a complete EV calculation. A conservative `nbehind==0` restriction would retain553/585observed WBot/Anton public opportunities and remove this particular approximation, but still needs a separate frozen evaluation.

Executing Q's actual assignment block at pot330,hero wager60,Anton wager180,eff2000,equity0.25,target-fold0.92 gives EV230.2chips with no seat behind;184.292with one;140.22032with two. A separately constructed illustrative one-behind ledger, keeping the same4% behind-call probability but assigning hero equity0.10against that strong cold caller and0.08against both callers, gives160.42848instead of184.292. These equities are assumptions, not empirical estimates; the example demonstrates why the scalar penalty cannot establish multiway EV.

## Recognition, equity and stop-loss limits

Recognition starts affecting priors after only4fingerprint observations. `_w` is posterior membership in the known-team library versus `_pop`, not posterior certainty in the named `_best` team. A source-executed example of four common50chip opens gives `_w=0.82182` while the best named-team posterior is only0.36057(Anker) versus0.34964(Chinese), with f4prior0.60591. Calling that82% confident identification would be incorrect. Q blends team rates rather than exclusively trusting the best label, which partly mitigates this, but does not validate the resulting jam prior.

The call equity uses the top range fraction `t3*(1-f4)` clamped to1–20%. t3is conditional re-raise frequency after our opens, and f4is a size/line-dependent observed response; multiplying them into an unconditional top-combo range is a modeling assumption. No opponent hidden cards were used to validate this conversion. The deterministic equity tables and generated EV are not equivalent to measured policy profit.

The additional stop-loss requires at least2non-folds and non-folds greater than25%of our learned own jams. This is a behavioral-call-rate stop, not financial drawdown, and inherits the >=600mislabel. At2calls/8it does not trigger because the comparison is strict. The Bayesian f4update can reduce jam EV before that threshold, so the stop-loss is not the only adaptation. Nevertheless, a universal25%call threshold is not derived from each hand's pot/equity-dependent break-even fold rate; it should not be described as guaranteeing safety.

## What blocks a strength claim

The data support “Anton often folded to historical strict all-in four-bets,” including against WBot. They do not establish “Q adds33bb/100.” That number would require a correctly defined eligible opportunity distribution, decision-time conditioned caller ranges, all live seats' continuation/payoff models and a valid policy comparison to the currently uploaded Matthias bot. Existing historical jams were selected by other policies; hand-history outcome replay alone cannot create unobserved reactions to newly jammed hands. No replacement recommendation is made from this audit. Freeze the exact candidate and resolve/test the above issues independently.
