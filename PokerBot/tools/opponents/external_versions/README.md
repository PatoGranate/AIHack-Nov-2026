# External bot source snapshots

These are source snapshots supplied by the user for local review and optional opponent simulations. Their version labels are the user's labels from the supplied filenames; they have not been verified against the public website's current upload versions.

| Team | User label | Original filename | Local path | SHA-256 |
|---|---:|---|---|---|
| kaiserbot (`external_team_02`) | 4 | `bot (4).py` | `kaiserbot_bot4_source.py` | `83e4ba1bf98e95339fa846bec0bb7456ebc697155ea9757c2a4a58a8a9bb451b` |
| Red (`external_team_03`) | 6 | `bot (6).py` | `red_bot6_source.py` | `c9020921a61e9d6ff433c757c270da91c3293206b166f3d7efd0b6ed32413d58` |

The files are exact byte-for-byte copies of the supplied Downloads. The originals remain untouched. Static checks found valid UTF-8 Python syntax, an `Agent` class with `act(self, state)`, only standard-library imports (`gc`, `random`, `time`; and `base64` for Red), and no calls to dynamic code execution, networking, subprocesses, or filesystem operations. Red's source contains module-level evaluation-table setup loops. This is a static review, not a behavioral sandbox test; do not import/run them until the team has reviewed their policies and resource use.

They live outside the default `a_*.py` archived-opponent set. To include them explicitly in the arena's mixed strong field, pass both paths using `--extra` and use `--by-opp` for opponent-conditioned reporting. That field still contains the other built-in strong opponents, so it is not a pure one-on-one result.
