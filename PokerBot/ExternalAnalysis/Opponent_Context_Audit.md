# Opponent context audit: does one pooled fold rate miss useful context?

Author: SCOUT (Matthias's opponent-strategy analyst). Branch `agent/scout-opponents`.
Audience: the orchestrator and its reviewer, FORGE, GAUGE/ROOK, and teammates.
Status: 2026-11-14 ~23:30, first full version.
Everything here is a **frequency of public actions**. None of it is evidence that an exploit is profitable.
No hidden cards are used. Results marked *exploratory* use un-preregistered splits.

Reproduce from the repo alone (Python 3.12.13, numpy 2.4.6; about 15 min on one core):

    cd PokerBot/ExternalAnalysis/OpponentContext
    python 01_postflop_context.py; python 02_preflop_context.py; python 03_render_tables.py; python 04_wbot_gap_by_hand.py

Full outputs are in `OpponentContext/data/out_*.txt`; machine-readable rates for FORGE are in
`data/postflop_context_summary.json` and `data/preflop_context_summary.json`.

## 0. Answers in brief

1. **Yes, the pooled rate misses context, but mostly context that is common to the field.**
   - Field-wide, fold rates move by +23 pts multiway vs HU, +31 pts for bets of at least 50% pot vs smaller ones,
     +21 pts out of position vs in position, and -7 pts on the turn vs the flop (random-effects means across 43
     teams).
   - The bot (G_v7 and N_v10 share `_learn`) keeps one number per seat. It handles bet size only through a fixed
     exponent and doesn't condition on HU/multiway, position, street, or bet vs raise.
2. **The exploratory model estimates opponent-specific effects, with sparse evidence within one round.**
   - The model estimates between-team differences (SD about 6 pts, p < 0.004 against its independent-binomial null). These p-values are conditional on that null, not calibrated for shared-table dependence or table overdispersion.
   - The heuristic one-round reliability is 3-31% under binomial sampling and the fitted heterogeneity model. This is not a hard learnability ceiling. The buckets hold 4-60 decisions per round.
   - One per-seat level plus field context effects is a testable candidate shape, consistent with FORGE's out-of-sample
     result.
   - The exception worth testing is a separate per-seat **facing-a-raise** level: SD 24 pts per opponent-table,
     one-round reliability about 0.5.
3. **New finding: opponents fold about 12 pts less to WBot's bets than to other players' bets at the same tables**,
   even within the same size, street, HU/multiway, position and preflop-aggressor cell.
   - All opponents: -12.3 pts [90% CI -13.9, -10.7]. Table-4 opponents: -13.2 [-15.7, -10.6].
   - The gap is already full-size in hands 1-250 of a round. Bots don't receive names, so this points to *where and
     what WBot bets* more than to opponents adapting to WBot.
   - The bot's pooled `ftb` mixes all bettors, so it over-predicts folds to its own bets.
4. **The exploratory decomposition attributes substantial fold-rate variation to tables within teams.**
   - Estimated SD across opponent-tables is 11.3 pts; heuristic components are 8.6 within a team and 7.3 between teams, combined in quadrature, not added as SDs.
   - So Saturday team averages, or any identification of a seat's team, are a weak prior.
   - The approximate implied shrinkage weight is about 19 pseudo-decisions, close to FORGE's chosen k = 20; it is not a tuned or validated optimum.
5. **Samples per round (FORGE's key input).** The field median per opponent seat per 1,000-hand round is:
   - 100 first-bet decisions in total: 83 HU and 16 multiway;
   - 26 HU small (<50% pot), 54 HU large, **4 multiway small**, 11 multiway large;
   - 10 decisions facing a raise.
   - Table-4 opponents run about 20% higher (section 2).
6. **Corrections to existing profiles** (section 9):
   - `StrongestFocus/profiles.json` stops at r007 and 13 of its 31 tables are practice rounds.
   - It has no data on table 4's **Poke**. "Poké Bot" is a different team that isn't seeded Sunday.
   - Its Wilson intervals are too narrow by a factor of about 1.3-2.9, because per-table rates are over-dispersed.

## 1. Data and definitions

- **Inputs.**
  - Sources: the 135 unique counted Saturday tables (135,000 hands) in the PR #7 manifest, from WBot's, Red's and
    kaiserbot's downloads.
  - Practice rounds are excluded.
  - Tables are de-duplicated by (round ref, ordered seat names). `oc_parse.py` fails if its input set differs from
    `SaturdayFieldPostmortem/data/input_manifest.csv`; a missing manifest or a selected-file SHA256 mismatch fails closed.
  - Every hand passes chip conservation (results = wins - net contributions).
- **Post-flop decision (primary).** A player's *first* response to the *first* bet on a flop, turn or river, while
  exactly one bet is outstanding. There are 110,190 of these. Responses facing a raise (14,706) are a separate
  bucket.
  - Fold = fold; continue = call or raise.
  - **Size** = the bettor's added chips / pot before the bet. This is the bot's own size definition.
  - **HU** = exactly two live players. **IP** = the responder acts after the bettor post-flop.
  - **Callers** = calls of this bet before the decision.
- **The bot's counter** (`Stats.faced/ffold` in `_learn`, identical in G_v7_final and N_v10_tuned) is replicated
  exactly. It counts every post-flop fold/call/raise while any bet is outstanding, from any bettor, of any size,
  facing a bet or a raise.
- **Preflop.**
  - A non-opener's first response to an unlimped first-in open. Limped pots are excluded.
  - Roles: blind vs a CO/BTN/SB open, blind vs an earlier open, cold (non-blind).
  - Open size = raise-to in big blinds.
  - Separately, the opener's first response to a 3-bet.
- **Uncertainty.**
  - 90% intervals come from resampling whole tables (2,000 draws). Each opponent resamples its own tables.
  - **Between-team heterogeneity:** DerSimonian-Laird tau on the probability and logit scales.
    - Each team's variance comes from its table bootstrap, floored at the binomial variance at the field rate.
    - Q is calibrated by 300 null simulations that keep every table's real decision counts.
  - **Between-opponent-table heterogeneity:** binomial DerSimonian-Laird, calibrated by 1,000 simulations.

## 2. How many decisions a 1,000-hand round gives per bucket

Per opponent seat per round, median [10th-90th percentile] over 961 field opponent-tables (non-WBot seats) and 157
table-4 opponent-tables (`out_01`, section 1):

| bucket | field | table-4 opponents |
|---|---|---|
| all first-bet decisions | 100 [58-163] | 123 [72-189] |
| HU / multiway | 83 / 16 | 103 / 21 |
| HU <50% pot / HU >=50% | 26 [6-56] / 54 [31-94] | 32 / 62 |
| multiway <50% / multiway >=50% | **4 [0-14]** / 11 [5-24] | 4 / 13 |
| <40% / 40-75% / 75-110% / >110% pot | 27 / 40 / 22 / 6 | 35 / 47 / 26 / 7 |
| flop / turn / river | 58 / 27 / 14 | 69 / 35 / 19 |
| IP / OOP vs the bettor | 66 / 31 | 85 / 34 |
| multiway with 1+ callers already in | 3 [0-9] | 4 [1-11] |
| facing a raise | 10 [3-26] | 12 [4-40] |
| the bot's pooled `faced` counter | 111 [65-183] | 132 [80-215] |

The binomial SE of one round's raw rate at p = 0.45 is 16 pts at n = 10, 10 at n = 25, 7 at n = 50 and 5 at n = 100.
Preflop is far denser:
- blind vs a late open: 82 per round;
- blind vs an earlier open: 112;
- cold responses: 233;
- opener vs a 3-bet: about 23 (12 IP + 11 OOP).

## 3. What varies, and what can be learned within a round

### 3a. Between teams (43 non-WBot teams with at least 5 tables; `out_01` section 3)

| quantity | mean | between-team SD, pts [logit] | p (calibrated) | one-round reliability |
|---|---|---|---|---|
| level: all first-bet | 44.8% | 6.1 [0.24] | <0.004 | 0.59 |
| level: HU <50% / HU >=50% | 20.8% / 50.9% | 6.3 / 9.2 | <0.004 | 0.39 / 0.63 |
| level: MW <50% / MW >=50% | 41.5% / 74.7% | 9.8 / 5.0 | <0.004 | 0.12 / 0.12 |
| level: facing a raise | 47.9% | **16.1 [0.62]** | <0.004 | 0.49 |
| effect: multiway - HU | +23.3 pts | 6.0 [0.25] | <0.004 | 0.16 |
| effect: >=50% - <50% pot | +30.6 | 5.7 [0.26] | <0.004 | 0.23 |
| effect: same, HU flop only | +28.6 | 6.0 [0.32] | <0.004 | 0.14 |
| effect: OOP - IP | +21.2 | 7.8 [0.30] | <0.004 | 0.31 |
| effect: turn - flop / river - flop | -7.3 / +0.8 | 5.8 / 9.3 | <0.004 | 0.20 / 0.29 |
| effect: multiway, 1+ callers - none | -12.1 | 5.8 [0.22] | <0.004 | 0.03 |
| effect: facing a raise - facing a bet | +3.0 | 13.8 [0.55] | <0.004 | 0.41 |
| effect: Saturday r28-54 - r01-27 | -5.8 | 6.3 [0.26] | <0.004 | 0.02 |

**Heuristic one-round reliability** = tau_logit² / (tau_logit² + SE²). SE is the logit-scale binomial SE at the field-median per-round counts. Under those assumptions this suggests a shrinkage fraction; it does not empirically establish how much can be learned online from a round.

Reading:
- The main context effects are large: multiway, size and position are each 3-5 times their between-team spread.
- Every observed Q exceeds the independent-binomial null in this analysis. This is exploratory, model-conditional evidence; it does not establish real-world significance under clustered dependence.
- The binomial-based reliability heuristic is at most about one third for these buckets; sparse multiway sub-buckets suggest heavy shrinkage, to be assessed by online predictive tests.
- This **agrees with FORGE's out-of-sample test**: per-seat deviations within one split add only 0.0005-0.002
  nats (`tools/forge_ctx/results_predictive.txt`, branch `agent/forge-context-model`).
  Statistically significant differences and in-round learnability are different questions. The first uses about
  2,500 decisions per team across 20+ tables; the second has 4-60 per bucket.

### 3b. Between opponent-tables (one seat at one 1,000-hand table; `out_01` section 3b)

| bucket | units | median n | mean | SD (pts) | within team | between teams | implied k* |
|---|---|---|---|---|---|---|---|
| all first-bet | 961 | 100 | 45.0% | 11.3 | 8.6 | 7.3 | 19 |
| HU <50% / HU >=50% | 791 / 960 | 30 / 54 | 20% / 51% | 9.7 / 13.1 | 8.6 / 8.9 | 4.3 / 9.6 | 17 / 15 |
| MW <50% / MW >=50% | 210 / 566 | 13 / 16 | 41% / 75% | 19.9 / 10.2 | 15.2 / 9.5 | 12.9 / 3.8 | 6 / 18 |
| OOP | 899 | 33 | 59% | 17.3 | 12.3 | 12.2 | 8 |
| facing a raise | 490 | 16 | 51% | **24.3** | 17.0 | 17.4 | **4** |
| vs WBot's bets | 343 | 46 | 27% | 10.9 | 8.6 | 6.6 | 16 |

k* = p(1-p)/SD² is an approximate beta-prior weight, in pseudo-decisions, implied by that spread (the exact concentration subtracts 1). This is a heuristic from binomial unit variances and variance subtraction, not a fitted hierarchical decomposition. Units need at
least 10 decisions, which slightly favours busier seats.

- Within-team (table-to-table) spread is comparable to or larger than between-team spread in every bucket here. HU
  large bets are the closest case (8.9 vs 9.6). The within-team spread comes from overnight and in-day uploads and
  from table mix. Section 6 shows it per team: per-table
  over-dispersion phi = 1.7-3.9 for table-4 teams, against a simulated 90th percentile of about 1.5.
- Consequence for identification-based priors: if a bot inferred which team sits in a seat (pablo_poker's v3
  identification tries this; I haven't checked it), the postflop fold-rate prior it could gain is limited. A Saturday
  team average explains well under half of a seat's in-round spread. Sunday uploads will add more drift.

### 3c. Robustness to the null model (`out_05`, answering the PR #14 review)

The PR #14 review notes that the 3a nulls are independent-binomial, so they keep no table-level overdispersion. The
*observed* Q already uses each team's own table-bootstrap variance. Only the null was binomial. `05_null_robustness.py`
tests both remaining assumptions directly. Exploratory, like the rest.

- **Team-label permutation null.** Team labels are shuffled across the real opponent-table rows, within strata of
  rows with the same non-empty buckets, and the same bootstrap and Q pipeline is rerun (300 permutations). Every null
  table keeps its real overdispersion and table mix.
  - All 23 postflop and 9 preflop rows keep p_perm <= 0.003, except:
    - MW 1+ callers - 0 callers: 0.013 (logit 0.037);
    - MW L - S, logit scale: 0.007;
    - preflop WBot open - others: 0.010.
  - The median null Q is 47-58 for 40-43 teams, close to k - 1. So bootstrap-variance noise inflates Q very little.
- **Noise-corrected tau**, tau_adj² = max(0, (Q - median null Q) / c), is within 0.1-0.6 pts of tau in every row. So
  k* and the one-round reliabilities in 3a do not move materially.
  - Example: level all first-bet: tau 6.2 vs 6.1; k* 65 vs 66.
  - Example: level facing a raise: 16.1 vs 16.0.
- **Within-hand clustering of the 3b units.** A seat can answer a first bet on the flop, turn and river of one hand.
  - The hand-cluster variance is 1.02-1.18 times the binomial variance: 1.02 on the flop alone, 1.18 for all
    first-bet decisions.
  - Recomputed with it, unit tau moves by at most 0.4 pts: 11.3 -> 11.0 for all first-bet decisions. The
    within-team component is 8.3 and k* rises from 19 to 21.
- **What this does not test.** Opponents at one table share that table's mix, and permuting rows does not break
  that dependence. For effects, the permutation null also equalises team levels, so on the probability scale it can
  still pick up level-driven differences. Read the logit columns for effects.
- **Reading.** The qualitative 3a/3b conclusions survive a null that keeps table overdispersion. PR #14's wording
  that they are "conditional on an independent-binomial null" is now tested rather than assumed. The decomposition is
  still a moment estimator, not a fitted hierarchical model.

## 4. Opponents fold less to WBot's bets (exploratory, `out_01` section 5, `out_04`)

Same 54 tables, responders other than WBot. Fold rate by the bettor's size bucket:

| size | vs WBot's bets | vs other bettors | difference [90% CI] |
|---|---|---|---|
| <40% pot | 16% (n=11,500) | 27% (n=4,734) | -11 [-14, -9] |
| 40-75% | 37% (2,803) | 50% (12,431) | -12 [-15, -10] |
| 75-110% | 52% (2,134) | 62% (6,709) | -10 [-13, -8] |
| >110% | 68% (913) | 74% (1,869) | -6 [-10, -3] |

- **Stratified** by size x street x HU/MW x IP/OOP x preflop-aggressor role (144 cells; Mantel-Haenszel weights):
  **-12.3 pts [-13.9, -10.7]**. Table-4 opponents: **-13.2 [-15.7, -10.6]**.
- 66% of WBot's bets are under 40% pot. So the raw per-team gaps in table C below (e.g. Resonance 22% vs 46%) also
  reflect size mix. Use the stratified figure.
- **By hand number** (`out_04`), the stratified gap for all opponents is:
  - hands 1-250: -11.4 [-13.6, -9.2];
  - hands 251-500: -13.0;
  - hands 501-750: -10.3;
  - hands 751-1000: -14.2.

  The gap is there from the start and doesn't grow.
- **Interpretation (hypothesis).**
  - Bots only get seat indices (`kit/README.md`: `on_table_start` passes seat, num_players, hands). Any opponent
    adaptation to WBot would have to be learned in-round, and very fast adaptation within the first 250 hands
    can't be excluded.
  - The flat profile fits WBot's *spot and board selection* better. A high-frequency, small-size bettor bets more
    often into ranges that connected, and the responder's holding is unobserved.
  - Either way, the quantity the bot needs, the fold rate to *its own* bets, is about 12 pts below what a
    pooled-bettor estimate says.
- **Validity caveat.** The offset belongs to WBot's Saturday betting policy. A candidate that changes how often or
  how small it bets may change it.

## 5. The bot's size curve and prior (diagnostics, `out_01` sections 4 and 7)

- **Size curve.** Field fold rate by bet size is 22% (mean 0.24 pot), 48% (0.58), 61% (0.90) and 70% (3.48 pot).
  - The bot assumes continue(size) = continue(0.6 pot) ^ ((size/0.6)^e), with e = 1.0 in G and 0.575 in N, capped
    at an exponent of 2.5.
  - Reading the aggregate as a single class, the observed exponent is about 1.1 for small bets but **0.34
    [0.32, 0.37] for overbets**.
  - So real opponents fold to overbets far less than G's curve implies. That matters for G/N's river
    `q_river_extra` sizes (1.75 and 3.0 pot).
  - This is a diagnostic only. The bot applies the exponent per hand class, and the size-fold relation in the data
    is observational: bettors choose their sizes. FORGE independently reports N's curve predicting 24% folds to
    bets under 30% pot (observed 14%) and 68% to bets over 1.1 pot (observed 60%).
- **Prior.**
  - On the public histories, the bot's own counter has a field mean of **0.455** (per opponent-table 10-90%:
    0.33-0.61). `pri_ftb` is 0.60 with weight 8, so early-round estimates are pulled up by up to 15 pts.
  - The `c_*` continue parameters were tuned relative to m = ftb/0.60, so re-centring the prior alone would rescale
    every continue rate. Change it only with a re-fit or re-tune.

## 6. Table-4 opponents (priority), with the strong teams for comparison

Cells: fold rate % [90% table-bootstrap CI] n. Generated by `03_render_tables.py` (`data/audit_tables.md`).

**A. Post-flop fold rate, first response to the first bet: HU/multiway x size**

| team | all | HU <50% | HU >=50% | MW <50% | MW >=50% | >110% pot |
|---|---|---|---|---|---|---|
| Resonance Qt | 38 [36-40] 2474 | 14 [11-16] 705 | 43 [41-46] 1425 | 44 [37-54] 107 | 76 [72-81] 237 | 64 [57-72] 157 |
| Anker Batteries | 46 [44-48] 2754 | 20 [16-24] 805 | 51 [49-53] 1412 | 49 [43-58] 163 | 79 [75-83] 374 | 67 [61-74] 151 |
| Chinese people can fly | 44 [42-46] 4592 | 17 [14-21] 970 | 46 [43-49] 2522 | 40 [36-44] 313 | 70 [66-73] 787 | 69 [63-75] 320 |
| GamesGone | 40 [38-43] 2981 | 16 [13-19] 893 | 46 [43-48] 1375 | 37 [30-44] 213 | 71 [67-75] 500 | 69 [63-75] 183 |
| Poke | 56 [53-59] 2408 | 32 [28-38] 612 | 63 [61-65] 1412 | 51 [41-60] 122 | 79 [76-82] 262 | 76 [71-81] 173 |
| Anton | 47 [44-50] 2669 | 25 [21-29] 681 | 52 [48-57] 1662 | 53 [43-64] 101 | 72 [65-79] 225 | 67 [61-75] 187 |
| YSL_TWIZZY | 27 [25-29] 2315 | 5 [4-7] 676 | 32 [30-34] 1303 | 27 [19-37] 111 | 66 [58-72] 225 | 54 [48-58] 235 |
| Gherkers | 40 [38-43] 2298 | 14 [12-16] 653 | 49 [45-53] 1317 | 26 [15-38] 93 | 71 [66-77] 235 | 79 [73-86] 130 |
| Attention Is All In | 51 [47-55] 2654 | 21 [16-28] 683 | 57 [53-62] 1385 | 62 [57-68] 227 | 76 [72-79] 359 | 82 [76-87] 174 |
| AAST | 56 [53-60] 1610 | 28 [25-32] 393 | 63 [59-67] 956 | 48 [35-63] 48 | 79 [74-85] 213 | 77 [70-84] 112 |

**B. Post-flop fold rate by street, position vs the bettor, callers, and facing a raise**

| team | flop | turn | river | IP | OOP | MW, 1+ callers | facing raise |
|---|---|---|---|---|---|---|---|
| Resonance Qt | 42 [39-45] 1370 | 31 [28-34] 730 | 39 [34-44] 374 | 35 [32-37] 1722 | 46 [42-50] 752 | 64 [53-76] 77 | 46 [39-54] 162 |
| Anker Batteries | 49 [47-51] 1634 | 42 [39-46] 732 | 40 [35-45] 388 | 40 [38-42] 2163 | 68 [64-71] 591 | 56 [49-64] 113 | 45 [40-51] 306 |
| Chinese people can fly | 49 [46-51] 2738 | 35 [32-39] 1226 | 37 [34-41] 628 | 42 [39-44] 3460 | 49 [47-52] 1132 | 49 [44-55] 217 | 60 [56-64] 728 |
| GamesGone | 43 [40-46] 1701 | 36 [32-39] 779 | 39 [35-42] 501 | 33 [30-36] 2106 | 59 [55-63] 875 | 49 [43-57] 243 | 55 [50-61] 622 |
| Poke | 55 [52-59] 1253 | 54 [50-58] 740 | 64 [59-68] 415 | 46 [43-49] 1605 | 77 [73-81] 803 | 67 [56-78] 83 | 48 [44-53] 561 |
| Anton | 50 [47-53] 1537 | 42 [38-47] 735 | 43 [37-49] 397 | 39 [35-43] 1672 | 60 [56-64] 997 | 64 [54-76] 66 | 50 [38-62] 202 |
| YSL_TWIZZY | 25 [22-28] 1086 | 29 [26-32] 756 | 30 [27-33] 473 | 25 [22-27] 1362 | 31 [28-35] 953 | 27 [18-39] 102 | 12 [8-17] 154 |
| Gherkers | 41 [39-44] 1402 | 36 [32-41] 610 | 45 [40-49] 286 | 36 [33-40] 1474 | 48 [42-54] 824 | 51 [39-62] 78 | 62 [54-68] 252 |
| Attention Is All In | 57 [54-61] 1606 | 39 [34-45] 681 | 44 [36-53] 367 | 41 [37-46] 1765 | 70 [63-77] 889 | 75 [68-81] 124 | 72 [69-75] 439 |
| AAST | 59 [55-63] 1025 | 45 [39-50] 401 | 65 [57-73] 184 | 49 [45-53] 1033 | 70 [65-74] 577 | 71 [62-81] 55 | 52 [44-61] 205 |

**C. Bettor identity and drift** ("vs WBot" and "vs others" are raw, on WBot's tables only; use section 4's
stratified gap for inference).

| team | vs WBot | vs others | r01-27 | r28-54 | bot ftb counter |
|---|---|---|---|---|---|
| Resonance Qt | 22 [17-26] 388 | 46 [43-50] 646 | 42 [40-45] 1224 | 34 [32-36] 1250 | 39 [37-41] 2636 |
| Anker Batteries | 26 [23-29] 561 | 53 [50-55] 715 | 51 [46-56] 905 | 43 [42-45] 1849 | 46 [44-48] 3060 |
| Chinese people can fly | 27 [24-31] 878 | 45 [42-49] 1475 | 45 [42-48] 2375 | 42 [39-45] 2217 | 46 [44-48] 5320 |
| GamesGone | 24 [21-27] 630 | 51 [48-54] 628 | 44 [41-48] 1472 | 36 [33-39] 1509 | 43 [41-45] 3603 |
| Poke | 37 [35-40] 247 | 59 [53-65] 465 | 59 [54-63] 765 | 55 [51-60] 1643 | 55 [52-58] 2969 |
| Anton | 29 [24-33] 479 | 57 [52-61] 885 | 42 [39-44] 1562 | 54 [51-58] 1107 | 47 [44-51] 2871 |
| YSL_TWIZZY | 12 [9-15] 465 | 39 [36-42] 536 | 30 [28-32] 1307 | 24 [21-26] 1008 | 26 [24-28] 2469 |
| Gherkers | 28 [25-32] 313 | 43 [39-48] 555 | 45 [41-49] 1175 | 36 [34-38] 1123 | 43 [40-45] 2550 |
| Attention Is All In | 39 [34-45] 476 | 51 [45-60] 859 | 58 [52-65] 1344 | 43 [39-47] 1310 | 54 [50-58] 3093 |
| AAST | 28 [19-45] 123 | 59 [52-66] 255 | 58 [55-62] 873 | 54 [47-62] 737 | 56 [52-60] 1815 |

**What stands out at table 4** (observed frequencies; hypotheses to test, not exploits):
- **YSL_TWIZZY** is the most continue-heavy post-flop opponent everywhere:
  - 5% folds to HU bets under half pot, 32% to larger HU bets, 12% facing a raise.
  - It is the tightest preflop: it folds 80% in the blinds vs late opens and 86-91% as an opener facing a 3-bet
    (table D).
- **Poke** folds the most post-flop: 56% overall, 77% OOP, 64% on the river.
  - It is sharply size-sensitive in the BB vs late opens: 55% folds at 3.0 bb or less, 83% at 3.1 bb or more.
  - FORGE reports the arena clone folds 41% overall vs Poke's real 55%.
- **Anton** defends the BB vs small late opens very wide (26% fold at 3.0 bb or less, 56% at 3.1 bb or more). As an
  opener it rarely folds to a 3-bet (27-36%; 4-bets 42% of the time overall).
  - Its post-flop fold rate rose from 42% (r01-27) to 54% (r28-54). It is the one table-4 team whose behaviour
    moved up during Saturday.
- **Anker Batteries** has the largest position effect: 68% folds OOP vs 40% IP.
- **GamesGone** folds 89% to opens when cold but only 50% once someone has already called. It overcalls rather than
  defends alone.
- **Chinese people can fly** defends the blinds widely (54% fold vs late opens) but folds 81-83% as an opener facing
  a 3-bet.
- **Resonance Qt** is a low folder on the turn (31%) and fell from 42% to 34% across Saturday.
- **Drift.** Six of the seven table-4 teams folded less in the second half of Saturday; Anton is the exception. Their Sunday versions may
  differ again. Weight in-round evidence over these tables.

## 7. Strong teams (secondary; none sit at table 4, AAST doesn't play Sunday)

- **Gherkers** folds very little to small multiway bets (26% [15-38], n=93) but much more to overbets (79%). It
  folds 62% facing a raise and only 39-42% as an opener facing a 3-bet.
- **Attention Is All In** is the most over-dispersed team across tables (phi 8.3), which fits frequent version
  changes. It folds 72% facing a raise and dropped from 58% to 43% across Saturday.
- **AAST** is a high folder post-flop (56%), but at 18 tables and with no Sunday seat it's low priority.
- The post-mortem's style table covers their preflop profile. Nothing here changes it.

## 8. Preflop context (`out_02`)

| quantity (43 teams) | mean | between-team SD, pts [logit] |
|---|---|---|
| blind vs CO/BTN/SB open, fold | 68.8% | 9.5 [0.46] |
| blind vs earlier open, fold | 73.2% | 9.7 [0.56] |
| cold (non-blind), fold | 85.5% | 4.6 [0.44] |
| opener vs 3-bet, fold | 60.6% | **19.6 [1.53]** |
| effect: BB vs late open >=3.1 bb minus <=3.0 bb | +13.2 pts | **12.6 [0.46]** |
| effect: 1+ caller ahead minus none | -5.4 | 9.7 [0.63] |
| effect: opener OOP minus IP vs the 3-bettor | -3.2 | 8.1 [0.41] |
| effect: open by WBot minus by others (raw, unstratified) | +0.3 | 2.9 [0.19] |

All have p < 0.004 against the independent-binomial null. This is conditional model evidence; shared-table dependence and overdispersion are not preserved in that null.
- Preflop samples are dense (82-233 per round per role), so per-seat preflop levels are learnable within a round.
- The opener's response to a 3-bet varies most: from ediz_slow's 0% fold and Anton's 32% to YSL's 88%. At about 23
  per round it's learnable too.
- The open-size effect is strongly opponent-specific (Anton +30, Poke +28, GamesGone +21, Gherkers +1). But bots use
  fixed open sizes, so it's partly an opener-identity effect.
- **The live bots don't use preflop fold rates at all.** In both G_v7 and N_v10, `q_steal` = 0 and `q_3bet` = 0.
  The pooled estimators are therefore idle:
  - `blindfold` (prior 0.6, weight 6) pools every opener position and size;
  - `ftr` (prior 0.75, weight 10) mixes opens and re-raises;
  - `fold3` (prior 0.5, weight 4) covers the opener vs a 3-bet.

  Open widening uses only the average pooled VPIP of the players behind (`steal_k`). So these numbers matter only if
  someone switches the steal or 3-bet paths on.

## 9. Corrections to existing profiles

1. **`ExternalOpponents/StrongestFocus/profiles.json` and `Target_Profiles.json` are stale for table 4.**
   - They cover 31 tables, of which **13 are practice rounds**, and counted rounds only up to r007.
   - Table-4 opponents appear at 3-9 tables there; the counted archive now has 18-27.
   - Practice rounds shouldn't feed counted-round profiles.
2. **Poke is missing there; "Poké Bot" is a different team.**
   - Poké Bot played 20 counted tables (r001-r048) and isn't in the final standings or Sunday buckets.
   - Table 4's "Poke" (18 counted tables, r011-r054, v2) is absent from `profiles.json`.
   - Both names sat at some of the same rounds. Never map one onto the other.
3. **Wilson 95% intervals understate uncertainty.**
   - Per-table first-bet fold rates are over-dispersed relative to binomial: phi 1.7-3.9 for table-4 teams and 8.3
     for Attention.
   - So intervals that treat decisions as independent are roughly 1.3-2.9 times too narrow. Use table resampling.
4. **`ExternalBot_Profiles_20261114.md`** (through r038) labels Poke "provisional, 3 rounds". It now has 18 counted
   tables. Its "fold vs raise" pools re-raises (as its own caveat says). Table D gives the split by role.
5. **`Target_Profiles.json` round-level bb/100** (e.g. Gherkers 142.5 over 8 table-rounds) is dominated by early and
   practice tables. It isn't comparable with the final Saturday figure (+43.4 over 54 rounds) and shouldn't be used
   to rank threats.

## 10. Where I agree and disagree, with evidence

- **Post-mortem, section 7:**
  - *Agree:* fold-to-bet ranges from 26% (YSL) to 55% (Poke). It replicates on my first-bet definition (27% / 56%)
    and on the bot's counter definition (26% / 55%, table C).
  - *Agree:* "a pooled fold rate is wrong", and shrinkage is needed for finer buckets.
  - *Refine:* "±4 pts within one round" is binomial noise around a *fixed* rate. A seat's true rate also varies 8.6
    pts table to table within a team. A Saturday team average is therefore a weaker prior than that sentence implies.
  - *Refine:* "each split roughly doubles the SE". This holds for the first HU/multiway split, but the splits are
    very unbalanced. Multiway small bets give about 4 decisions per round (SE about 25 pts), so those buckets have to
    rely on the field effect.
  - *Not checked:* Poke's 10% limps and the other style signatures. I didn't recompute them.
  - *Nuance on the hypotheses:* "more betting when checked to by high-fold opponents" has to be re-based on folds to
    *our* bets. Poke folds 37% to WBot's bets raw, not 56% (table C).
- **FORGE:**
  - *Agree* that context effects are mainly common and opponents differ mainly in level. My heterogeneity numbers
    don't contradict the out-of-sample result. A large opponent-specific tau would have contradicted it; the estimated taus are small relative to the model's in-round noise assumption.
  - *Consistent as an exploratory starting point:* k = 20 versus approximate implied k* = 19. Sensitivity and online predictive tests are needed before treating either as optimal.
  - *Added and replicated:* FORGE's first field model had no bettor-identity term, and section 4 suggested one. FORGE
    has since tested it out of sample (PR #9, `channel/to_bot_team/20261114-233500_forge_context_model_results.md`):
    - a static `bettor == WBot` term of logit -0.39 (train) / -0.32 (all rounds);
    - on WBot's own bets, its candidate vs the parent's actual use improves from -0.021 to -0.047 nats [-0.058, -0.038];
    - a per-seat hero shift on top adds only -0.0019 and was rejected, matching the low one-round reliability here.
    - The facing-raise split (rec. 3) gave -0.0019 at table 4 in FORGE's harness and was not adopted.

    I haven't re-run FORGE's harness. These are its reported numbers.
- **Arena validity** (FORGE's finding, `tools/forge_ctx/clone_vs_real_t4real.txt`; I haven't re-derived it):
  - The table-4 clones match per-opponent fold levels (except Poke) and the IP effect.
  - They do **not** reproduce:
    - multiway: real 65% vs clone 45%;
    - facing a raise: 50% vs 31%;
    - bets over 0.8 pot: 59% vs 43%;
    - the turn: 38% vs 17%.
  - So the arena can't validate any candidate whose edge depends on those contexts, or on section 4's
    WBot-specific gap.
- **ROOK** (PR #10, Sunday clone-fidelity audit) reports version shifts. Poke's v2 has VPIP 0.43 with 29% limps,
  where the old clone has 0.22. Chinese people can fly and GamesGone show lower post-flop aggression in their latest
  versions, and Anton's v7 has shifted.
  - *Agree, and it explains part of section 3b:* my rates pool all versions of each team. Within-team table-to-table
    spread (8.6 pts) and per-table over-dispersion (phi 1.7-3.9) are what version changes would produce.
  - For Poke in particular, the table-4 rates above mix v1 and v2.
- **GAUGE:** I haven't seen a message from GAUGE about opponent context. Nothing to agree or disagree with yet.

## 11. Testable model recommendations

Each recommendation is a test with a stated comparison, not a target. Predictive tests use FORGE's online harness:
- seat-keyed;
- each prediction uses only earlier hands of that round;
- train on r001-027, score on r028-054;
- table-bootstrap CIs.

Better log-loss is not EV. Anything that passes still needs a paired same-seed arena A/B and real-round checks.

1. **Hero-bettor offset.** Add `bettor == self` to the field continue model, or a hero-only per-seat shift shrunk
   toward the pooled shift.
   - Test: log-loss on the bettor = WBot slice vs `ftb_ctx` without it.
   - Expected direction from section 4: folds to our bets run about 12 pts lower, roughly -0.5 logit at a 50% base.
   - Fit it offline: section 4 shows it's present from hand 1.
   - Re-estimate if the candidate's betting frequency or sizes change.
   - *Status:* FORGE ran the predictive test (section 10) and it passed: CI excludes 0. EV is untested, and the
     arena can't test it.
2. **Model shape: per-seat level plus field context effects.** No per-opponent context buckets, with one exception
   to test: a separate per-seat **facing-a-raise** shift (prior weight around 4-10 per section 3b). It is the only
   split with one-round reliability near 0.5. Pass rule: CI-excluded log-loss gain over FORGE's A model.
3. **Separate raises from bets in the bot's counter.** Today they're pooled and `fold_vs_raise` = 1.0. Facing a
   raise has between-team SD 16 pts against 6 for facing a bet. Test it inside rec. 2.
4. **Replace the fixed size exponent with an empirical field size effect** (logistic in size bins, like FORGE's
   field model), as its own one-factor change.
   - Check it on real rounds only: the clones don't reproduce the large-bet response.
   - Report separately the fold equity the bot assigns to the 1.75x and 3.0x pot river sizes. Section 5 suggests
     it's overstated.
5. **Prior centre.** If `pri_ftb` changes from 0.60 toward the observed 0.455, re-fit or re-tune `c_*` in the same
   change, and A/B the joint change.
6. **Preflop: only if the steal or 3-bet paths are switched on** (`q_steal` and `q_3bet` are 0 in G and N).
   - Feed them per-seat estimates conditioned on role: blind vs a late open, separately from cold responses and from
     re-raises. Don't feed them the pooled `ftr`.
   - Score them on preflop decisions in the same harness before any A/B.
   - Samples (about 82 blind decisions vs late opens and about 23 opener-vs-3-bet decisions per round) make per-seat
     levels learnable.
   - The open-size effect is opponent-specific, but the bot's open size is fixed, so only the level matters for it.
7. **Clone realism before arena gating of context changes.** Either add multiway, raise, size and street terms to
   the clone fold logic (`tools/opponents/_common.py`), fitted to the field model, or don't use arena results to
   judge recs. 1-4.

## 12. Limitations

- **Observational data.**
  - Bettors choose sizes and spots, so the size, position and bettor effects describe situations as they occurred.
    They are not causal responses to a size we choose.
  - Section 4's WBot gap may come from spot selection. If so, it is tied to WBot's Saturday policy.
- **Versions change.** Teams uploaded during Saturday (Resonance v13, Chinese v23, GamesGone v14) and will again
  overnight. Table-level drift is already 8.6 pts.
- **Coverage.**
  - Table-4 opponents were seen at 18-27 of our 135 tables, mostly not alongside each other.
  - WBot itself changed versions during Saturday (v1-v9).
- **Definitions.** The first-response definition excludes re-entries and checks. Heterogeneity tests treat decisions
  within a table as independent in the null simulations; the estimates' variances use table resampling.
  Opponent-table units need at least 10 decisions.
- **Missing inputs.** `High_Team_Behavior_Review_20261114.md` and its SVG aren't on any branch (I asked in
  `channel/to_bot_team/20261114-225613_scout_missing_high_team_review.md`). This audit doesn't use them.

## 13. Open questions

1. Which bot is live for Sunday, G or N? (FORGE asked the same.) The context findings apply to both: they share
   the audited `_learn`/`opp_models` structure, but their policies and budgets are not otherwise equivalent. Frozen G and N differ in 16 parameter entries, including preflop opens, bet sizes/bonus, realization, range weights and compute. The pooled historical WBot gap must be rechecked for a changed policy.
2. Can someone run section 4's comparison on the live Sunday rounds once a few exist? It's the one finding that the
   arena can't check.
3. Does anyone have Sunday-version samples of the table-4 opponents (practice or early rounds) to measure overnight
   drift?
4. pablo_poker: does the v3 identification change the conclusion in 3b? Its accuracy on real rounds would bound how
   much a team-level prior can add.
