# Training algorithm research: practical next steps

Date: 2026-11-14

This is a research-backed suggestion, not a claim that a full solver will beat the current G/v7 candidate without an A/B. The latest independent league was against archived versions, and the team’s newer replacement A/B is against its opponent clones; neither alone establishes tournament-field superiority.

## What the strongest poker systems establish

- **Multiplayer, closest match:** Pluribus used offline self-play to build a blueprint strategy and real-time search during play; its paper reports superhuman six-player no-limit Hold’em. The practical lesson is a staged architecture, not necessarily copying its compute-heavy implementation: train a robust baseline offline, then spend a bounded runtime budget refining decisions. [Brown & Sandholm, Science 2019](https://doi.org/10.1126/science.aay2400)
- **Heads-up techniques:** Libratus combined an abstract-game blueprint, nested safe subgame solving, and continual self-improvement; DeepStack continually re-solved with a learned value function. These are strong references for two-player settings, but their claims do not transfer directly to multiway play. [Libratus, IJCAI 2017](https://ijcai.org/proceedings/2017/772) [DeepStack, Science 2017](https://pubmed.ncbi.nlm.nih.gov/28254783/)
- **Training methods:** Counterfactual regret minimization (CFR) and variants underpin these systems. Deep CFR approximates CFR with neural networks in large games, but brings data, model, and evaluation costs. [Deep CFR, ICML/PMLR 2019](https://proceedings.mlr.press/v97/brown19b/brown19b.pdf)

## Recommendation for this codebase

1. Keep the frozen v7/G strategy as the safe baseline and train an experimental CFR-derived policy offline on a reduced, explicitly documented game abstraction. Given the project’s multiplayer tables, MCCFR is the research direction most aligned with Pluribus; treat the already-deferred full blueprint as a longer-term project, not an unmeasured rewrite.
2. In the near term, put effort into a **sample-aware opponent model with a bounded exploitative adjustment** around the baseline. External evidence shows that general fold-vs-open rates do not predict opener fold-to-three-bet rates (e.g. Durahim: 517/589 folds vs opens, 14/63 folds as opener facing a three-bet). Use separate conditional stats and shrink small samples toward the baseline. Do not encode a global lighter-call or overbet rule from small samples.
3. Preserve mixed actions. Avoid deterministic rules that become exploitable; any exploit should be confidence-gated, capped, and backed off when evidence is sparse or contradictory.
4. Benchmark each change with frozen source/opponent hashes, held-out seeds and rounds, all-seat action/error checks, and paired comparisons against frozen v7 plus the best current opponent (F/E). Report uncertainty and per-opponent results; do not select on the training opponents alone.
5. Before trying neural Deep CFR or real-time subgame solving, measure the runtime budget and build parity/replay tests. The latest v7 league explicitly lacked an enforced runtime limit, so it does not certify that a search-heavy policy can ship.

The current external-hand review also finds clone/action mismatches (for example the real Gherkers and Lehman lines in r016 hand 893); validate opponent models on held-out decision sequences before using them as training targets or performance evidence.
