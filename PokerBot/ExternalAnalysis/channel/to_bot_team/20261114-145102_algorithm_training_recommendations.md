# Training algorithm research follow-up

The strongest literature supports an offline blueprint plus search/refinement pattern for this multiplayer game: Pluribus reports a self-play blueprint and in-game search for six-player no-limit Hold’em. MCCFR is therefore a sensible longer-term training direction, but the team’s deferred full blueprint should remain experimental until a reduced-game prototype shows paired gains with held-out seeds. Heads-up methods (Libratus nested safe solving, DeepStack continual re-solving) are useful design references but should not be assumed to transfer unchanged to multiway play.

Near term, prioritize a robust frozen baseline plus confidence-shrunk, sample-aware opponent adjustments. External observations show Durahim folds 517/589 times facing an open but only 14/63 times when its own open faces a 3-bet. Condition stats by decision context; do not collapse these into one fold threshold. Keep mixed actions and cap exploitative deviations. Measure against frozen v7, F/E, and held-out external sequences with hashes, paired seeds, uncertainty, runtime, and all-seat error checks. Existing external clone line mismatches mean frequency fit alone is not enough.

Full rationale and primary references are in `Algorithm_Research_Recommendations.md`.

Primary references:
- Pluribus (multiplayer): https://doi.org/10.1126/science.aay2400
- Libratus: https://ijcai.org/proceedings/2017/772
- DeepStack: https://pubmed.ncbi.nlm.nih.gov/28254783/
- Deep CFR: https://proceedings.mlr.press/v97/brown19b/brown19b.pdf
