# Phase 2: reinforcement learning (plan for the remaining hours)

Phase 1, in this folder now, is a game-theory bot with ~30 tunable knobs and an
RSI loop that tunes them one at a time behind a statistical gate. Phase 2
replaces hand-written decision rules with a learned policy, while keeping the
same arena, database and gate. **An RL policy reaches `bot.py` only by winning
a holdout through `rsi/gate.py`, the same way a parameter change does.**

## Hard constraints that shape the design

- `bot.py` is one file, standard library only: no numpy or torch at play time.
  Anything learned has to be exported as plain Python numbers (lookup tables or
  a small MLP evaluated in pure Python; ~0.1 ms for a 32×32 net).
- 10 ms per decision, 10 s per 1,000 hands. The Monte Carlo equity (≈2–3 ms) is
  already the dominant cost. Keep model inference well under 1 ms.
- Training can use anything offline (numpy, PyTorch, scikit-learn) on the
  logged data.

## Approach: learn a residual on top of the game-theory policy

Training from scratch (Deep CFR, NFSP) won't converge in ~15 hours on a laptop.
Instead, learn **action values for an abstract action set** and let them
*override* the rule-based choice only where the model is confident:

    actions = {fold, check/call, raise ½ pot, raise pot, all-in}
    features = rl/dataset.py featurize()  (equity, position, pot odds, SPR, street, ...)

## Steps and time budget (≈15 h)

| # | Step | Hours | Output |
|---|------|------:|--------|
| 1 | Collect data: `run_practice.py --tables 512 --hands 1000 --decisions --explore 0.05` (≈4 M decisions) | 1 | `decisions` table |
| 2 | `rl/dataset.py` → CSV; fit Q(s,a) per abstract action (gradient-boosted trees or a 2-layer MLP) on the Monte Carlo return, with importance weights for explored actions | 3 | `rl/q_model.pkl` |
| 3 | Distil to a stdlib policy: a small MLP (weights as Python lists) or a binned lookup table over (street, equity bucket, pot-odds bucket, position) | 2 | `rl/policy_weights.py` |
| 4 | `pokerbot/strategy.py`: `if rl_weight > 0 and Q-gap > margin: take the RL action`; add `rl_weight` and `rl_margin` to `PARAM_SPACE` so the **RSI loop tunes how much to trust the model** | 2 | new knobs |
| 5 | Self-play iterations: champion + RL → collect more data against the league (which now includes RL versions) → refit → gate. That's fitted Q-iteration with a population, close to NFSP | 5 | 3–4 generations |
| 6 | Robustness: `--betting pot_limit`, `--raise-cap 3`, 7-seat tables; `local_sim.py bot.py` timing check; upload | 2 | final `bot.py` |

## What already exists for it

- `decisions` table and `--decisions` / `--explore` flags (`run_practice.py`).
- `rl/dataset.py`: featurization (stdlib, shared with the bot) and CSV export.
- Arena, league (former champions as opponents), duplicate-seed evaluation and
  the promotion gate: an RL candidate is just another strategy spec.

## Pitfalls to avoid

- **Reward noise**: a hand's chip result is very high-variance. Use many hands
  and paired (duplicate) evaluation, and don't trust in-sample Q-values.
- **Off-policy bias**: only explored actions give unbiased counterfactuals;
  weight them by 1/explore and cap the weights.
- **Overfitting to the league**: the gate's CHALLENGER check uses a pool
  without self-play opponents; keep it.
- **Tournament drift**: real opponents are other teams' bots. After each
  practice round, `fetch_hands.py` downloads your table histories; import
  them as an extra evaluation set before trusting any promotion.
