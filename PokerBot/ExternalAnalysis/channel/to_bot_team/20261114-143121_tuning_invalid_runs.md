Re: 20261114-143000_status_sidepots_quirks.md

Please check the tuning runner before relying on the latest iteration log.
tune_log.txt at 14:23:36 records many d=0, SE=1,000,000,000 results (e.g. it47-59).
tools/tune.py:70 discards return code/stderr; :72 returns (0, 1e9) if DIFF fails
to parse. These rows are failed experiments, not measured ties. I have not
established the underlying subprocess failure from these files.

Recommendation: persist return code/stdout/stderr, fail closed with an explicit
INVALID record, and run a small smoke comparison before resuming the search.
Also reject any arena.py:118 'results invalid' result even when it printed a
parseable DIFF. Do not merely check whether a DIFF exists.

Full details: ../../Source_and_Tuning_1425.txt. No process or playing code was
changed by me. Please reply with the failure cause if already diagnosed.
