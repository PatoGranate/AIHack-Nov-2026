# First counted round (LIVE, not simulated) + encoding fix

## Live: saturday/r001, website version 5 = G/v7 (b8a22e4b...f0c16a)
+36.7 bb/100 (+7,342 chips, 1,000 hands, 8-seat table), 2 timeouts, 0 errors, 0 bank-outs,
think 3.04 s/round. 2nd of 8 at the table. VPIP .24 / PFR .17; postflop AF .85, c-bet .99.
By where hands ended: showdown +504 bb (74 hands), flop +116, preflop -97, turn -77, river -79.
By hand class: premium +686, good -10, mid -195, weak -114 bb (earlier v2 lost -1,471 bb
with weak hands in one round). One round: no uncertainty claim; ~+/-100 bb/100 round noise.
Timeouts persist at a low rate (2) despite ~2 ms local worst case; server think time is
~5x local, so we will watch this per round.

## Encoding
Root cause: make_clones.py wrote files with the Windows default code page (0xEA for "ê").
Fixed: explicit UTF-8 writes everywhere in make_clones/arena; clone filenames ASCII-only
(r_matchamillecrpescake.py; old mojibake file removed). Regenerated clones including r001.
Strict UTF-8 decode of every clone file: 0 failures.
Full manifest: tools/opponents/real/MANIFEST.json
combined sha256 90597e1e25d26dc9577c2e5d332285de33419c80a9b4eeb6d2a5cc00d0276313 (32 files,
per-file sha256 inside, source rounds listed). Earlier A/B results stay attached to their
earlier snapshots. Hand-review builder is being fixed for strict UTF-8 by the subagent.
