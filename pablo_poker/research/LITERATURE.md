# Poker AI literature: what we can use

Each idea from the literature becomes one of three things:

- **in the bot**: already part of the default strategy
- **lab idea**: implemented behind a parameter that defaults to off and is listed in
  [`research/ideas.json`](ideas.json). The autonomous lab tests it through the
  gate, and it reaches `bot.py` only if it wins on the holdout.
- **RL phase**: needs offline training ([`rl/PLAN.md`](../rl/PLAN.md)).

The constraints shape everything here: one stdlib file, 10 ms per decision,
7–8 players, 1,000 hands against the *same* opponents, ranked on chips won
against a mixed field (a "total bankroll" contest, not a contest to be unexploitable).

## 1. Equilibrium methods (what the superhuman bots do)

| Paper | Key idea | What we take |
|---|---|---|
| Zinkevich et al., *Regret Minimization in Games with Incomplete Information* (CFR), NIPS 2007 | Self-play regret minimisation converges to Nash in 2-player zero-sum games | RL phase: tabular MCCFR over an abstraction of the preflop / push-fold subgame |
| Lanctot et al., *Monte Carlo Sampling for Regret Minimization* (MCCFR), NIPS 2009 | Sample chance/actions so CFR scales | RL phase |
| Bowling et al., *Heads-up Limit Hold'em Poker is Solved* (CFR+), Science 2015 | CFR+ converges far faster | RL phase, if the organisers switch to fixed-limit |
| Moravčík et al., *DeepStack*, Science 2017 | Depth-limited re-solving with learned counterfactual value nets | Not feasible in 10 ms of pure Python |
| Brown & Sandholm, *Libratus*, Science 2018 | Blueprint + nested safe subgame solving + a **self-improver** that each night patches the parts of the blueprint opponents exploited most | **The model for our RSI loop**: our nightly self-improver is diagnosis → one-change candidates → gate |
| Brown & Sandholm, [*Superhuman AI for multiplayer poker* (Pluribus)](https://par.nsf.gov/servlets/purl/10119653), Science 2019 | 6-max NLHE beaten with a self-play MCCFR blueprint plus depth-limited search. Uses **mixed strategies**, frequent **donk bets**, large **overbets**; no multiplayer equilibrium guarantee, yet strong in practice | in the bot: randomised mixing (bluff/c-bet frequencies). Lab idea: `river_overbet` (polarised 1.5× pot river bets with the nuts) |
| Brown et al., *Deep CFR*, ICML 2019; Heinrich & Silver, *NFSP*, 2016; Brown et al., *ReBeL*, NeurIPS 2020 | Neural function approximation of CFR / fictitious self-play / RL+search | RL phase: NFSP-style league training (our league of former champions is the "average policy" population) |

**Takeaway.** Nash-style play in multiway NLHE requires compute we don't have
at play time, and it isn't even the goal here: against a weak, mixed field,
the ACPC "total bankroll" events were won by bots that *exploit*. So we keep a
sound game-theoretic baseline and spend the effort on safe exploitation.

## 2. Opponent modelling and exploitation (most valuable for this tournament)

| Paper | Key idea | What we take |
|---|---|---|
| Billings, Davidson, Schaeffer & Szafron, [*The Challenge of Poker*](https://www.cs.ualberta.ca/~games/poker/publications/AAAI98.pdf) (Poki), AIJ 2002 / AAAI 1998 | Effective hand strength EHS = HS + (1−HS)·PPot, and **re-weighting the opponent's hand distribution** by their actions | in the bot: Monte Carlo equity to the river (includes potential) against ranges re-weighted by each opponent's VPIP/PFR and narrowed by each bet |
| Southey et al., *Bayes' Bluff: Opponent Modelling in Poker*, UAI 2005 | Bayesian posterior over opponent strategies from few observations | in the bot: Beta-style smoothing of VPIP/PFR/fold-to-bet/aggression with priors (15-hand pseudo-counts) |
| Johanson, Zinkevich & Bowling, [*Computing Robust Counter-Strategies*](https://www.cs.ualberta.ca/~games/poker/publications/NIPS07-rnash.pdf) (RNR), NIPS 2007 | A pure best response is brittle; mix "exploit the model" with "stay near equilibrium" | in the bot: `exploit` ∈ [0,1] blends exploitation into a baseline; the lab tunes it |
| Ganzfried & Sandholm, *Game Theory-Based Opponent Modeling* (DBBR), AAMAS 2011; [*Safe Opponent Exploitation*](https://dblp.dagstuhl.de/rec/conf/sigecom/GanzfriedS12.html), EC 2012 | Exploit only as much as the model is trustworthy; risk only what you've won from the opponent | lab idea: `exploit_ramp` (exploitation grows with hands observed) |
| Bard, Johanson, Burch & Bowling, [*Online Implicit Agent Modelling*](https://webdocs.cs.ualberta.ca/~bowling/publications/b2hd-13aamas-implicitmodelling.html), AAMAS 2013 | Don't model the opponent explicitly: keep a **portfolio** of strategies and pick online (bandit) by how each performs at this table | lab idea: `portfolio`, an Exp3 choice per hand among {base, loose, tight, aggressive} |
| Chen & Ankenman, *The Mathematics of Poker*, 2006 (push/fold equilibria) | Against a shove, call iff equity vs the **shover's range** beats the price | lab idea: `jam_equity` (Monte Carlo equity vs each shover's observed shove range). This is the direct fix for "all-in every hand" bots |

## 3. Evaluating faster (so the lab iterates faster)

| Paper | Key idea | What we take |
|---|---|---|
| Zinkevich et al., *Optimal Unbiased Estimators for Evaluating Agent Performance* (DIVAT), AAAI 2006; Burch et al., [*AIVAT*](https://ojs.aaai.org/index.php/AAAI/article/view/11481), AAAI 2018 | Control variates on chance events (and known strategies) give unbiased estimates with up to **85% lower standard deviation** | in the arena: **all-in EV adjustment**, the chance-node part of AIVAT. When betting is over before the board is complete, the hero's result is replaced by its exact expected share over the remaining cards (side pots included). It is unbiased and removes the biggest source of luck |
| Duplicate poker (used in the man-machine matches) | Replay the same cards with the seats swapped | in the RSI loop: every candidate plays the same seeds and lineup as the champion |
| Ganzfried & Sandholm, *Action Translation in Extensive-Form Games* (pseudo-harmonic mapping), IJCAI 2013 | Map off-tree bet sizes into the abstraction without being exploited by odd sizes | RL phase: needed once a learned policy uses abstract bet sizes; also why we stress-test against odd sizers |

## 4. Stress testing against extreme strategies

Bots built from a fixed equilibrium can lose badly to degenerate strategies
the abstraction never anticipated (the classic case: an opponent who shoves
every hand). The lab runs a **stress suite** of extreme opponents (always
all-in, always fold, min-raise everything, 2× pot overbets, check-raise
everything, random sizing, push/fold) and **probe heroes** that play those
extremes against the field to find what the field gives away. A losing
matchup becomes a finding and queues the ideas that target it
([`rsi/lab.py`](../rsi/lab.py)).

## Sources

- [Superhuman AI for multiplayer poker (Pluribus), Science 2019](https://par.nsf.gov/servlets/purl/10119653)
- [AIVAT, AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11481) · [arXiv 1612.06915](https://www.arxiv.org/pdf/1612.06915)
- [Online Implicit Agent Modelling, AAMAS 2013](https://webdocs.cs.ualberta.ca/~bowling/publications/b2hd-13aamas-implicitmodelling.html)
- [Safe Opponent Exploitation, EC 2012 (dblp)](https://dblp.dagstuhl.de/rec/conf/sigecom/GanzfriedS12.html) · [AAMAS 2015 follow-up](https://aamas.csc.liv.ac.uk/Proceedings/aamas2015/aamas/p37.pdf)
- [Computing Robust Counter-Strategies, NIPS 2007](https://www.cs.ualberta.ca/~games/poker/publications/NIPS07-rnash.pdf)
- [Opponent Modeling in Poker / EHS, AAAI 1998](https://www.cs.ualberta.ca/~games/poker/publications/AAAI98.pdf) · [EHS summary](https://en.wikipedia.org/wiki/Effective_hand_strength_algorithm)
