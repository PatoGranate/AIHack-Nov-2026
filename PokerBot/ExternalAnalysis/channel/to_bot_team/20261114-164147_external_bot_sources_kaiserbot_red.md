# User supplied Kaiserbot and Red source snapshots

The user provided source files for comparison with the actual bots: Downloads `bot (4).py` (identified by the user as Kaiserbot version 4) and `bot (6).py` (Red version 6). I copied them byte-for-byte to:

- `tools/opponents/external_versions/kaiserbot_bot4_source.py` — 37,196 bytes; SHA-256 `83e4ba1bf98e95339fa846bec0bb7456ebc697155ea9757c2a4a58a8a9bb451b`.
- `tools/opponents/external_versions/red_bot6_source.py` — 63,992 bytes; SHA-256 `c9020921a61e9d6ff433c757c270da91c3293206b166f3d7efd0b6ed32413d58`.

The copies match their source hashes; the original Downloads remain untouched. A concise provenance/static-inspection record is in `tools/opponents/external_versions/README.md`. The version labels are user supplied, not independently verified against the site.

Static inspection: both parse as UTF-8 Python and expose the kit interface `Agent.act(self, state)`. Imports are standard library only; static AST scanning found no dynamic `eval`/`exec`/imports, network, subprocess, or filesystem calls. Red has module-level evaluation-table setup loops. I have not imported or executed either source; please review resource cost and policy before running.

The files are deliberately outside `tools/opponents/a_*.py` so they do not silently alter the default archive pool. For an initial mixed strong-field comparison, use `--extra tools/opponents/external_versions/kaiserbot_bot4_source.py tools/opponents/external_versions/red_bot6_source.py --by-opp`; `--by-opp` reports performance conditioned on their presence, but the strong field also contains built-in opponents. Use a fixed-opponent paired setup before calling it a pure head-to-head. These files can also inform offline strategy/prediction review as their complete candidate implementations.
