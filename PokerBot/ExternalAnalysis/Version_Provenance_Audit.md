# Version Provenance Audit — Saturday real rounds r001–r053

Audited 2026-11-14 (~21:30). This is a read-only audit: no bot code was changed, nothing was uploaded, and no hand data left the machine.
Note: `C:\Users\pelay\AIHack\PokerBot` is **not a git repository**, so the requested branch `agent/rook-provenance` and GitHub PRs could not be created. Coordination is through the local channel (`ExternalAnalysis/channel/`).

## Bottom line

**The v8 rounds (r049–r053) were not played by G.** The deployed bot's behaviour matches the I/N family on two parameters that differ by design and need no source hash:

| Fingerprint | G (`G_v7_final`) | I (`I_v9_25ms`) | N (`N_v10_tuned`) | Observed v5 / v7 | Observed v6 | **Observed v8** |
|---|---|---|---|---|---|---|
| `open_size` param (bb) | 3.5 | 2.8 | 2.8 | 3.5 (3,802 / 183 opens) | 2.8 (3,886) | **2.8 (860 of 928 first-in raises; 67 at 3.3 bb, 1 at 4.1 bb, none at 3.5)** |
| Thinking budget `max_ms` / `hard_ms` | 1.2 / 3.0 | 6 / 14, bank 7 | 6 / 14, bank 7 | think 1.9–3.2 s/round | 4.6–7.1 s | **5.5–7.1 s** |
| `o_ep` (EP open looseness) | 0.22 | 0.22 | **0.176** | EP open 26.2% (n=6,252) / 28.8% (n=344) | 26.8% (n=7,226) | **22.1% (n=1,604)** |

- v8 made zero 3.5 bb first-in raises (928 raises: 860 at 2.8 bb, 67 at 3.3 bb, which is the I/N family's raise over limpers, and 1 at 4.1 bb). A G build never opens 2.8 bb first-in, so v8 cannot be `G_v7_final`, and it cannot be H either (H also uses 3.5).
- Within the 2.8 bb family, v8's early-position open rate is lower than v6 (I) by 4.7 points (two-proportion z = 3.9). That matches N's tighter `o_ep`: the parameter ratio is 0.176/0.22 = 0.80 and the observed ratio is 0.221/0.268 = 0.82.
- This is strong support for **v8 = N**, but it is not proof. Only authoritative upload or download identity from the site can prove the exact source (see "Limits" below).

## Round ranges and numeric version labels (from `Hand_data/SaturdayRealRounds/*.json`, field `round.version`)

| Server version | Rounds | Hands | Sum of round bb/100 ÷ rounds | Think s/round | Timeouts |
|---|---|---|---|---|---|
| v5 | r001–r023 (15:00–16:50) | 23,000 | +26.8 | 1.87–3.22 | 33 (18 in r003) |
| v6 | r024–r047 (16:55–18:50) | 24,000 | +6.7 | 4.61–7.13 | 19 |
| v7 | r048 (18:55) | 1,000 | +17.2 | 2.95 | 2 |
| v8 | r049–r053 (19:00–19:20) | 5,000 | −17.4 | 5.49–7.12 | 4 |
| v9 | none in local data (newest file is r053, fetched 19:22) | — | — | — | — |

Errors and bank-outs were 0 in all 53 rounds.

## Bot-name mappings and evidence

| Version | Mapping | Evidence | Strength |
|---|---|---|---|
| v5 | **G** | open 3.5 bb, think ~2.6 s; `submissions/README.md` says v5=G | Behaviour plus documentation agree. G vs H is distinguishable only through tuned postflop params (both open 3.5); the README and the H "not uploaded" notes favour G. |
| v6 | **I** | open 2.8 bb, think ~6 s, EP open 26.8% (= `o_ep` 0.22) | Behaviour plus documentation agree. Not N (EP rate too loose), not G/H (size). |
| v7 | **G** (re-upload) | open 3.5 bb (183/199 opens), think 2.95 s | Behaviour plus documentation agree. Only 1 round. |
| v8 | **likely N by behaviour** (known G snapshot excluded) | open 2.8 bb, think 5.5–7.1 s, EP open 22.1% | G is **excluded**. N is favoured over I (EP z≈3.9, descriptive only). |
| v9 | G per the user's later message | no rounds yet | Unverified until v9 rounds arrive: expect 3.5 bb opens and ~2–3 s think. |

## Hashes of likely submitted artifacts (sha256, first 16 hex; size; local mtime)

| File | sha256 | Bytes | mtime | Notes |
|---|---|---|---|---|
| `submissions/G_v7_final/bot.py` | b8a22e4b9085cf8c | 54,260 | 14:39 | Likely v5, v7 and v9. Full: b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a |
| `submissions/H_v8_tuned/bot.py` | 08ae3fef8a34c274 | 54,260 | 16:03 | Never matched live behaviour. Its folder name "v8" is a **local** label, not server v8. |
| `submissions/I_v9_25ms/bot.py` | d45a39b72c0e990e | 54,294 | 16:39 | Likely v6. Its folder name "v9" is a local label, not server v9. |
| `submissions/N_v10_tuned/bot.py` = `kit/bot.py` = `tools/cands/N_real.py` | 5c2b4b2c0ed3ddd5 | 54,365 | 18:55–18:57 | Likely v8 (built 3 min before r049 started). |
| `tools/cands/N.py` | e87596f2acdc2086 | 54,364 | 18:51 | Test build (server-scaled caps), not for upload. |
| `tools/cands/cI.py`, `cN.py` | 187e1e6d715c2b88, b4cb0a88b61b3e55 | — | 19:20 | Test builds only. |
| `tools/cands/J.py` | 1c2686c1a62ba59e | 54,305 | 17:31 | Never uploaded. |
| Earlier: A 64f1d9bbc25e0a77, C 1cf1c99d8a29c591, D 0e7202890a9fdd31, E 243c408c9b2e7489, F 60b5ccb0ccb6c559 | | | | v1–v4 era |

## Conflicts and how to resolve them

1. **"v8 = G" (channel notes from 19:26 onward, attributed to the user) vs "v8 = N" (README, plus the bot team's record of the user's messages "v7 was G, v8 will be N" and then "sorry, v9 is G").**
   - The round data contradicts v8 = G on two independent fingerprints, open size and thinking time.
   - Most likely cause: the "sorry, v9 is G" correction was read as a correction to v8.
   - Consequence: the channel analyses that treat r049–r053 as G must be re-attributed:
     - `20261114-192625_upload_cutoff_N_vs_G.md`
     - `20261114-200119_high_commit_allin_audit.md`, which says "G's r049-r053"
     - the G ablation pilot's live framing
2. **Local folder labels vs server versions.** `G_v7_final`, `H_v8_tuned`, `I_v9_25ms` and `N_v10_tuned` carry local generation numbers that collide with server numbers (H_v8 ≠ server v8, I_v9 ≠ server v9). Refer to bots by letter plus hash, never by "vN" alone.
3. **Hash not proven.** The round JSON has no source hash.
   - **What would close the gap:** only authoritative upload or download identity, meaning the website's upload history or the downloadable copy of each version, hashed against the table above.
   - **What would add behavioural support only** (neither closes the gap):
     - a v9 round showing 3.5 bb opens and ~2–3 s think;
     - a replay of r049–r053 preflop decisions through I and N, with both bots' opponent models fed the same history, measuring agreement. Not done; ask before spending the compute.

## Limits of this evidence

- **The z statistics are descriptive.** Hands are not independent (the same opponents and tables repeat), and versions played at different times against changing fields. The z values show the play patterns differ; they are not a randomized comparison, and they establish nothing about whether one strategy is better.
- **Behaviour cannot prove which exact file was deployed.** That includes a future v9 match and any replay agreement. Only authoritative upload or download identity from the site can close that gap. Until then, label server v8 (r049–r053) as **"likely N by behaviour; the known G snapshot is excluded"**, not as exact-source proof.

## Method and reproducibility

Each claim, and where it comes from:
- **Round metadata, timing, open rates, raise sizes and the EP z statistic** come from `ExternalAnalysis/provenance/fp.py` (stdlib only, read-only).
  - Run `python -I fp.py Hand_data/SaturdayRealRounds`.
  - Its output is preserved in `provenance/fp_output_r001-r053.txt`.
- **Definitions used by the script:**
  - Raise size is the raise target ÷ the hand's `bb` field (20).
  - "First-in" means no raise before hero. The script prints two versions: *unopened* excludes pots with limpers, and *incl. limped pots* counts them. For v6–v8 the EP counts are identical under both definitions. For v5 they differ (6,148 vs 6,252 opportunities), but both rates round to 0.262. The conclusions hold under either definition.
  - Positions: EP = first to act after the BB up to HJ; HJ = two seats before the button; CO = one seat before the button.
- **Source parameters** (`open_size`, `max_ms`, `hard_ms`, `bank`, `o_ep`) were read from each `bot.py`'s `P = {...}` dict with `ast.literal_eval`.
- **Hashes** are `sha256sum` of the listed files.

Neither the parameters nor the hashes come from `fp.py`.
