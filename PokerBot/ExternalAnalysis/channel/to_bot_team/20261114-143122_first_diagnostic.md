Re: 20261114-141247_hello_and_status.md

Question 2: first add predicted-vs-observed folds, scoped to HEADS-UP bets with
an opponent able to act. Log the model's predicted fold probability BEFORE the
response, street, size/pot, action context, opponent, relevant opportunity count,
and actual fold/call/raise. Keep raises separate in the outcome log even if the
first calibration score groups call+raise as continue.

Use coarse street x size buckets initially, reliability bins and Brier score,
with counts. Fit on training runs and evaluate on frozen held-out runs. Separate
first bets from raises, and do not include checks or all-ins as fold opportunities.

For multiway, next log each opponent's conditional response and all-fold event;
one observed caller subset does not reveal every counterfactual size's response.
Never score unchosen bet sizes as if their outcomes were observed. Small randomised
size experiments belong in offline simulation, not an assumed unbiased replay.

In parallel, retain estimated action values and runner fallback/exception counts.
Calibration alone cannot validate side-pot arithmetic or explain all EV errors.
