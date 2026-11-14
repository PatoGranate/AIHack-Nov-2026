# Re: clone_line_mismatch

Agreed on both points. Results on the REFIT opponents (seed 6161, 200 x 300 hands,
all-seat error check on, no errors), frozen candidate G = v7 b8a22e4b...f0c16a:
  v7 - F   real(refit) +42.3 (se 5.4)   heldout(+a_trapper) +27.8 (se 5.7)
  v7 - E   real(refit) +46.5 (se 5.0)   heldout(+a_trapper) +24.2 (se 6.2)
Opponent snapshot for exactly these runs: tools/refit_results.opponents.sha256
(combined 9999bbe8...8bb4; _common.py 4bed2339...aadd). Earlier gates used earlier
replicas and are labelled as such; they are not re-validated by this.
Note: the "heldout" family was not refit (still jittered earlier clones) + a_trapper.

Lehman clone (exact): call_min 2, no air_call/station, so it would fold the r016h893
A-high river call; you're right that it cannot reproduce that line, and matching
VPIP/PFR does not make it a valid stand-in for value-extraction tests. Line-level
held-out tests from complete histories go on the post-15:00 list (replay each real
decision point to the clone and score agreement, keeping failures).
