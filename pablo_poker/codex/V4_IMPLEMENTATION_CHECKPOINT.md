# V4 / Sunday learning checkpoint

**HANDOFF READY — 2026-11-15 01:35 UTC / Canary.** Claude is the requested completion owner after reset. Code is frozen at this checkpoint; no live promotion. Codex remains available and will check the reply mailbox every five minutes while this session is active. Post the issue #1 relay below and acknowledge the comment URL/ID; do not substitute branch-channel delivery.

- Task: CODEX-SUNDAY-01; owner Codex; backup Claude.
- Deadline: 2026-11-15 01:35 Atlantic/Canary (UTC).
- Authorization: user requested implementation; existing low-budget rule remains: no large simulations, unattended jobs, or extra agents.
- Branch/head: this local directory has no `.git`; relay to GitHub issue #1 through Claude. Remote branch/head not independently verified.
- Status: foundation implemented and tested; **not all requested work is finished**. Cold-start profiling is the default; G remains selected. Remaining conditional-range calibration, safe contextual action integration, real upload verification and full-stage profit comparison are not complete.
- Compute: contract tests, public-history replays, repeated 8-hand reproducibility checks, and 100-hand timing smoke tests only. No large simulations, unattended jobs or extra agents.
- Blockers: no GitHub access; exact WBot remote upload unverified; GBot source not found in this workspace; realistic hidden-range calibration remains research work.

## Handoff requirement

**Communication correction:** post the actual checkpoint to GitHub **issue #1** in `PatoGranate/AIHack-Nov-2026`. Branch channel files are not read by the orchestrator. Return the issue comment URL/ID in `externalanalysis/CLAUDE_REPLY.md`; readiness-only relays are insufficient. User reports independent V4 vs G: −15.2 bb/100, SE 9.5, reported 95% interval −34.5..+4.1. Preserve the decision to keep G. The interval does not establish an exact deficit, but offers no evidence to promote V4.

**Latest user steering:** opponents may upload entirely new policies. Default implementation must treat them as unseen seats, learn nonexclusive behavioural tags and detect drift. Historical name matching is optional research, not the main strategy.

Claude: finish any outstanding work at the 01:35 checkpoint; do not interpret a candidate export as a proven winner. Consider integrating the same opponent-identification interface into **GBot only if independently shown better than completed V4**, after completing the missing V4 work. Compare identical evidence, roster, field, seeds and timing; isolate engine gains from identification gains. Do not copy V4 betting heuristics blindly into GBot.

## Work log

- 00:52 UTC: read current source and GitHub relay rules. Final V4 is frozen as baseline; planned changes will not replace uploaded `bot.py` or running pipeline exports.
- Corrected `sim/fieldbot.py`: exact weighted fallback after rejection failure; large first-bet bucket borrows first-bet strength rather than raise strength; all live opponents enter absolute equity estimates; fold/call/raise probabilities normalize; betting/bluff mass no longer overlaps incorrectly; added full state reset with copied warm inputs.
- Added resets to `bench_fields.py`, `bench2.py`, `head_to_head.py`, and validation jobs. These entry points no longer silently retain warm state across variants. Legacy benchmarks still require frozen dependency manifests for trustworthy large comparisons.
- Added hero selection and additional dependency hashes to `validate_field.py`. Default hero is WBot; frozen-cohort hero mismatch raises rather than evaluating the wrong team.
- Added `opponent_identity.py`: exact joint subset-DP assignment with unknown alternatives, tempered evidence, per-hand cap and forgetting. **Optional only**, following the user's unseen-policy steering.
- Added `opponent_evidence.py`, `context_model.py`, `behavior_profile.py`, `cold_observer.py`: public-action opportunities; actual counts separate from prior mass; 100/500-hand rolling windows; anonymous, nonexclusive tags; change detection every 10 hands; engine-neutral callback wrapper. No private cards or real team labels enter cold tags.
- Integrated cold profiles into isolated V4: rolling current-policy VPIP/PFR/large-raise/fold/aggression estimates feed existing engine reads. Context-specific predictions are exposed but not fully integrated into a new range/EV solver. Historical team priors default OFF.
- Added `sunday/export_accounting.py`: separate ablation prevents phantom raises after effective all-ins and corrects double-counted villain investment in the heads-up raise branch. Independent forced-split test: old V4 says +75 chips; corrected branch says +50, the exact value.
- Hardened download/export helpers: validate existing round completeness, retry incomplete files, write atomically; compile exports and use Python literals rather than JSON booleans/null in Python source. No network fetch or live export was invoked during testing.
- `calib_skill.py` now requires an exclusive training cutoff and writes a candidate file by default, with a fit-only manifest. No skill fit was run.
- Built version-labelled evidence from 119,000 unique public hands before the explicit cutoff. Opponent versions not directly observed remain unknown. Historical contextual predictions are diagnostics only: GamesGone worsened versus the population and Anton lacked holdout coverage; no historical-prior promotion.
- Built `sunday/fixture/`: seven Table D profiles plus a training-only live model, complete file hashes. Unvalidated skill/adaptation/warm pools disabled explicitly. JSON files are present locally for Claude to commit/relay with the code.
- Created standalone `sunday/v4_identity_bot.py` (cold default) and `sunday/v4_cold_accounting_bot.py`. Neither replaces `bot.py`, `data/v4_bot.py` or G.
- Minor environment note: Python-created temporary directories acquired unusable permissions in this sandbox. Tests were changed to use unique files in the existing workspace directory; those checks now pass. Five `sunday/tmp*` test directories could not be removed under current permissions and must not be committed. No permission escalation was attempted.

## Validation evidence

- `pablo_poker/sunday/contract_checks.json`: 13 new tests + 7 existing tests, return codes 0. Covers exact joint marginals against brute force, unknown fingerprints, normalization/bucket contracts, rejection fallback, reset isolation, actual opportunity counts, cold policy-switch detection, neutral engine wrapper, download completeness and forced-split accounting.
- `sunday/reproducibility.json`: 8 hands/run, reset between runs, reversed engine job order; exact result hashes agree. This is a reproducibility test, not a profitability estimate.
- `sunday/identity_replay.json`: optional historical roster matcher 17/20 correct at 1,000 hands versus 15/20 baseline, confidently wrong 2 versus 4. Still uncalibrated and not the default. Historical roster is known but seat mapping is not supplied to the matcher.
- `sunday/cold_profile_replay.json`: three WBot rounds, anonymous-seat inputs only; names appear solely as evaluation labels.
- `sunday/cold_callback_replay.json`: 1,000 real-history summaries, zero context-learning failures; measured mean ~0.37 ms and max ~2.54 ms after reducing change checks to every 10 hands. Machine-specific diagnostic, not a server guarantee.
- `sunday/cold_timing.log`, `sunday/accounting_timing.log`: 100-hand subprocess checks at 25 ms, zero errors/timeouts/bank exhaustion. Timing smoke tests against house bots only; profits must not be relayed as evidence of a tournament edge.
- Parse checks passed for 41 Python files at the tested snapshot. Re-export/retest if any input changes.

## Exact reproduction commands (from pablo_poker)

```text
python -B sunday/export_accounting.py
python -B tools/run_sunday_checks.py
python -B tools/check_sunday_reproducibility.py --hands 8
python -B tools/replay_cold_profiles.py
python -B local_sim.py sunday/v4_cold_accounting_bot.py --rounds 1 --hands 100 --timeout 25 --seed 23091
```

Read `pablo_poker/sunday/README.md` for fixture/evidence builds and restrictions. Exact hashes will be in `externalanalysis/V4_CHANGE_MANIFEST.json`; the live V4 baseline remains `8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108` at last verification.

## Claude: work still requiring completion

1. **Communication first:** relay this actual checkpoint directly to issue #1. Acknowledge comment URL/ID in `CLAUDE_REPLY.md`. Keep G; do not relay only readiness.
2. Inspect G/GBot source and verify actual upload/hash. Adapt `ColdObserver` to its standard callbacks, then integrate predictions into its own range/EV model only behind tests. No assumption that G shares V4's private methods.
3. Calibrate cold tag/drift false positives, unknown policies and within-round switches on fresh temporal data. Intervals/repeated testing are not yet empirically calibrated.
4. Finish contextual range/reach/selection modelling and joint action/size/shown-strength validation. The original simulator mismatch is **not solved** by the engineering fixes.
5. Implement Sunday API/version parsing against an actual captured public response, with explicit stage/round keys; do not guess its schema. Add verified upload acknowledgements and activation timing. Cold defaults avoid stale named priors but do not create cross-round platform memory.
6. Obtain orchestrator approval for large work. Compare G, V3.1/V3.2, V4, and profiling/accounting ablations on identical robust Table D scenarios, including full 36-round lifecycles and policy changes. No profitable superiority has been established for these new candidates.
7. Commit reproducible source, fixture JSONs and manifests through GitHub. Exclude credentials, unrelated raw feeds and temporary test directories. This directory has no local Git metadata, so Codex could not push or verify remote head.

### Concise issue #1 relay

> CODEX-SUNDAY-01: keep G. Cold-start anonymous profiling + policy-change detection implemented in isolated V4 candidates; historical name matching optional. Fixed simulator reset/sampling/probability defects and a +75→+50 split-pot accounting error. 20 contract tests pass; tiny reversed-order reproducibility and 100-hand timing pass. No large runs or promotion. Simulator fidelity/contextual action integration remain unfinished. GBot source/access needed for portable observer integration. Checkpoint: externalanalysis/V4_IMPLEMENTATION_CHECKPOINT.md; please assign completion owner/budget and acknowledge here.

## Next steps

1. Reproducibility and sampler/probability fixes with regression tests.
2. Engine-neutral roster-aware joint identity model, standalone V4 candidate, temporal replay.
3. Versioned WBot evidence, explicit temporal cutoff, reproducible Table D fixtures.
4. Record measured limitations and exact commands/hashes; request budget before large comparisons.
