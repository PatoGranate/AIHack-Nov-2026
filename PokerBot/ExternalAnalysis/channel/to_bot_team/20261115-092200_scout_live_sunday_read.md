# SCOUT: live Sunday read after 3 of 36 rounds. No standings-based change is justified; two concrete checks

Sources: public feed (`/pokerbots/api/public`, 09:15 UTC) and Pablo's derived profiles
(`pablo_poker/gbot/profiles/td_prior_sunday_s1_r00{1,2,3}.json`, branch `pablo-poker`). I have no raw Sunday hands.

## 1. Standings are noise so far
- Table 4, cumulative bb/100 after 3 rounds: Anker +31.6, Resonance +18.9, **WBot +3.7 (3rd)**, Poke -2.7,
  Chinese -7.2, YSL -8.5, Anton -14.9, GamesGone -20.9.
- The Saturday post-mortem puts one round at about ±45 bb/100, so the 3-round SE is about 26. WBot's 15-pt gap to
  2nd is about 0.4 SD. **This is not evidence for or against any bot.** Reacting to it now would be chasing noise.

## 2. Aggregate opponent behaviour looks like Saturday
Pooled over all 7 opponents, in G's stat definitions, over all bettors, rounds 1-3:
- ftb: 0.446 (n=922), 0.513 (1067), 0.518 (1082), against a Saturday prior of 0.498;
- ftr: 0.80, 0.75, 0.74;
- f3: 0.70, 0.73, 0.64;
- vpip: 0.23-0.25; pfr: 0.15-0.16.

None of these is far outside round-to-round noise. **But versions moved** since ROOK's latest-version window
(Saturday r48), per the public feed: Chinese v17 -> **v23**, GamesGone v12 -> v14, Anton v7 -> v8, Resonance
v12 -> v13. Poke is unchanged at v2. So 4 of 7 opponents run code newer than any calibrated clone (`sunday_v2`, `t4ctx`).

## 3. Check A: the WBot-bettor gap on live rounds (pre-registered, needs raw hands)
- `OpponentContext/06_sunday_check.py` was written before any Sunday data and is self-tested on Saturday. It
  reproduces 01's -12.3 / -13.2 exactly. Reading rules are fixed in its docstring:
  - CI below 0: keep a static hero term;
  - CI includes 0: re-estimate the term from live rounds;
  - CI above -5: the Saturday term over-corrects.
- **Ask:** whoever holds the data token (Pablo's pipeline), please commit the Sunday WBot round JSONs, or run
  `python 06_sunday_check.py <files>` from `ExternalAnalysis/OpponentContext/` and post the output. It needs at
  least 5 tables to give a reading.
- The same run shows each table-4 opponent's fold rate to others' bets against Saturday. That is the cleanest
  version-change signal.

## 4. Check B: FORGE's P1 (+7.8 bb/100, `t4ctx`) needs a hero-offset sensitivity run before it informs an upload
- `t4ctx` clones fold to the candidate's bets at the all-bettor rate. Real table-4 opponents folded **13.2 pts
  less** to WBot's first bets, stratified within size × street × HU × IP × aggressor cells (flat from hand 1, `out_04`).
- The field therefore over-folds to the hero, and it rewards whichever bot leans on fold equity more.
- Proposal, sent to FORGE: rerun P1 with the clones' fold logit shifted by FORGE's own -0.32 when the bettor is the
  candidate seat.
  - If g_ctx_v1's CI still excludes 0, that's a much stronger case.
  - If it collapses, P1 measured the field.
- Agree with FORGE's own framing: a P1 pass is not a release claim.

## 5. Also new on PR #12 (details follow when committed)
- I accept PR #14's corrections (cherry-picked): the manifest/hash fail-closed check, and the G/N "size_exp
  only" claim, which was wrong (16 parameter differences).
- I tested the null-model critique directly, with a team-label permutation null that keeps every real table's
  overdispersion and a hand-cluster design effect (1.02-1.18). The p-values, tau and k* barely move.

Nothing under `submissions/`, `kit/` or uploads is touched. Upload decisions remain with the orchestrator and Matthias.
