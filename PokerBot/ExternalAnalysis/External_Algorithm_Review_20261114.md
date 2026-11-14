# External algorithm review — 14 November 2026

## What the literature suggests for this bot

The relevant target is multi-player no-limit Hold'em under a strict per-action deadline, so results from heads-up poker are useful methods references but not direct evidence that a method will improve this bot.

### Practical training direction

1. **Keep a robust blueprint and improve it offline with sampled regret minimization.** CFR+ and Monte Carlo CFR are established approaches for imperfect-information games. Pluribus is the closest landmark for six-player no-limit Hold'em: it used an offline blueprint strategy and depth-limited search, with the paper's supplement identifying depth-limited search as the key ingredient for scaling to multiplayer. This makes the team's deferred MCCFR blueprint a strategically sound long-term direction, but implementation should be staged and benchmarked against the current policy rather than treated as a quick switch.
2. **Spend a small, fixed online budget on imperfect-information subgame search.** A depth-limited solver can refine decisions using a learned continuation/value model, while retaining the blueprint outside the searched tree. This resembles the direction in Pluribus and DeepStack/Libratus, but their strongest results are not all in this exact multiplayer/server setting. Enforce the actual action cap and validate tail latency and failure behavior.
3. **Treat action abstraction and bet sizing as a first-class experiment.** Candidate J's wider bet-size menu is a plausible abstraction improvement. The current K/L data is positive but inconclusive; run the actual J artifact with frozen hashes, paired seeds, fresh held-out opponents and I/G controls before promotion.
4. **Avoid unvalidated opponent-specific exploitation.** Use opponent statistics only with minimum sample sizes, shrinkage toward the robust blueprint, and held-out cross-validation. A few rounds or one external bot family are not reliable evidence of a general exploit.
5. **Use evaluation that separates signal from poker variance.** Prefer paired duplicate deals/seeds and report effect size with standard error/confidence intervals, recent/real/held-out/archive populations, source hashes and failure/runtime tails. Promotion should require repeatable benefit and no reliability regression.

## Current evidence and recommendation

- Candidate J source SHA `1c2686…06576` has not been gate-tested directly. Its strategy parameters match gen08 `best.py` (`64ecb4…24b47`); J's differences are its real runtime budget fields. Therefore K/L only provide indirect strategy evidence if the 5× local/server time scaling is accurate.
- K and L are positive but each below z=2. Approximate combined z is 1.63 late, 1.80 real, 1.63 held-out; archive is weak and only K has an archive run. There is no G comparator. The legacy `gate_J.txt` tests gen05 real-IP versus I and is unrelated to Candidate J.
- Independent review found K/L scripts are not fail-closed and their text outputs do not preserve complete command status/log evidence. Run a bounded exact J-vs-I/G gate with full logs, hashes, independent seeds and actual 25 ms runtime/failure checks before considering a switch. Keep I online and G as rollback meanwhile.
- None of these papers establishes that a candidate will win this particular tournament. The recommendation above is to adopt research methods as measured training experiments, not to copy a headline algorithm or make a live deployment on literature alone.

## Primary research references

- Brown & Sandholm, **Superhuman AI for multiplayer poker**, *Science* (2019), [paper DOI](https://doi.org/10.1126/science.aay2400) and [supplementary material](https://noambrown.com/papers/19-Science-Superhuman_Supp.pdf).
- Brown & Sandholm, **Superhuman AI for heads-up no-limit poker: Libratus beats top professionals**, IJCAI (2017), [paper PDF](https://www.ijcai.org/proceedings/2017/0004.pdf).
- Moravčík et al., **DeepStack: Expert-level artificial intelligence in heads-up no-limit poker**, *Science* (2017), [paper](https://doi.org/10.1126/science.aam6960) / [arXiv](https://arxiv.org/abs/1701.01724).
- Brown et al., **Deep Counterfactual Regret Minimization**, ICML (2019), [paper](https://arxiv.org/abs/1811.00164).
- Brown et al., **Combining Deep Reinforcement Learning and Search for Imperfect-Information Games (ReBeL)**, NeurIPS (2020), [paper](https://arxiv.org/abs/2007.13544). ReBeL's cited guarantee is for two-player zero-sum games; do not assume it transfers unchanged to multiplayer poker.
- Tammelin et al., **Solving Large Imperfect Information Games Using CFR+**, [paper](https://arxiv.org/abs/1407.5042).