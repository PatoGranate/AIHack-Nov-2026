# Re: correctness_followup, tuning_invalid_runs, first_diagnostic, scoped_training_and_quirks

## Invalid tuning rows (it47-59): diagnosed
All share one timestamp, 14:23:36 = the moment we stopped the tuner. Killing it took down
its arena subprocesses first, so the remaining iterations parsed nothing and the loop ran
to the end in the same second. Nothing was accepted from them; no process survived; params
file unchanged. Your point stands, so tune.py now fails closed: return code, stdout and
stderr go to tools/tune_failures.txt, any non-zero rc / missing DIFF / "invalid" / ERR
line raises and stops the search with an explicit INVALID log row.

## Correctness follow-ups: all three adopted
1. Light 3-bet now uses an opener-facing-reraise counter (o3/o3fold, prior .5 x 4) and
   requires >= 8 such opportunities. Steal now uses blind-specific defence vs a single
   open (bdef/bfold, prior .6 x 6), >= 8 observations per blind.
2. Side-pot call EV: pending non-all-in players are no longer auto-matched; each samples
   continue/fold from its continue model; folders' money becomes dead.
3. Expired hard deadline no longer gets a fresh 3 ms (only a missing deadline does).

## Quirk A/B (built before fixes 1-2; each vs same bot with it off; 200x300 hands)
              real     heldout   strong
  trap OOP    +9.3     +10.3     +5.3    keep
  tiny bet    +4.4      +6.7    +11.7    keep
  river over  +3.2      +4.9     -1.3    keep (marginal)
  late steal  -4.7      +5.2     -2.7    drop
  light 3bet -10.0     -11.0     -3.9    drop (consistent with your diagnosis)
Noted your transfer-risk ranking: trap and overbets are the ones we'd most expect to
mislead us. Held-out field is still one ParamBot family; structurally different
responders are on the list.

## Now
Final promotion gate running: v7 (fixed model + side pots + trap/tiny/overbet) vs F and
vs E on untouched seed 4242, heldout/real/strong, 240x300 hands each.

## Sunday
Your heads-up river MCCFR teacher scoping is the plan we'd follow. The fold-calibration
diagnostic (heads-up first bets, street x size buckets, Brier + reliability bins,
raises logged separately) is next after the counted rounds start.
