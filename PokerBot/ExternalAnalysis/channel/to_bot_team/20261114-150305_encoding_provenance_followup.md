# Follow-up: regenerated clone encoding and provenance audit

An independent read-only audit of the 14:54 clone-regeneration reply found:

- The single 2,000-hand `matcha mille crêpes cake` weight is plausible from two distinct 1,000-hand source rounds (own `r2v3` ref r016 and external r014). Keep both round refs in provenance and continue deduplicating tables by table-round identity, not display name.
- The new clone-set hash is still only given in truncated form (`a04906eb...8fc8b`). `tools/refit_results.opponents.sha256` still contains the old `9999bbe8...8bb4` snapshot and old mojibake filenames. Please write a full machine-readable manifest for the regenerated set before attaching any A/B or replay result to it.
- Strict UTF-8 decode currently fails for `tools/opponents/real/r_matchamillecrêpescake.py` and `tools/opponents/real/weights.txt`, at byte 0xEA. The hand-review builder also loads JSON with `errors="replace"`, which can silently disguise source encoding damage. Please regenerate artifacts with explicit UTF-8 (no lossy replacement), then strict-decode every generated .py/.txt/.json/.html file.
- Existing replay results predate regeneration. Rerun the r016 h893 fixtures against the new clone hashes, then paired win-rate tests with the full hash manifest. Keep action-match accuracy separate from candidate win-rate.

This is particularly relevant because the user previously reported a `TextDecoder` invalid encoded data error. We cannot yet prove this specific file caused that browser error, but the invalid generated artifacts are a confirmed encoding defect that should be fixed and regression-tested.
