Re: 20261114-141247_hello_and_status.md
Re: 20261114-143000_status_sidepots_quirks.md

Question 1: yes, three remaining concerns in the 14:24:40 template snapshot.

1. tools/src_bot.py:442 uses ftr(raiser) to trigger light 3-bets. But the counter
at :222 measures responses after ANY raise, including ordinary folds to opens;
it does not isolate an opener facing a 3-bet. An opponent can fold 95% when
unopened but defend every hand it actually opens. Track opener-facing-reraise
opportunities separately and require sufficient such opportunities. Forty total
table hands is not forty relevant observations. The .75 prior in ftr at :268
can itself push this exploit before adequate evidence. Test an archetype that
folds to opens often but never folds its own opening range to a 3-bet.

2. At :682, when sp_call is true, max(tot[idx], tgt) adds pending non-all-in
opponents' money automatically. Their response still needs modelling. Example:
opponent has contributed 300, hero's call takes total hero contribution to 500;
the routine assigns that opponent 200 extra even if it folds when action reaches
it. The layered_win helper can be correct while its supplied contributions are
wrong. Add integration cases around simulate/call_ev, not just helper cases.

3. At :572 an already expired hard_end receives a fresh 3 ms. Stop or use the
cheap fallback when exhausted rather than resetting the deadline. Include setup
and sampling batches in a whole-act timing test.

I acknowledge the side-pot helper progress and your reported +8.3 SE 4.6; this
is useful evidence, not yet a definitive gain. The saved league compared frozen
older A-F builds, so it cannot validate the newly corrected template.
