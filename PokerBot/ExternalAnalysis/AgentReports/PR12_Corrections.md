# PR12 input-integrity and inference corrections

Base: exact PR12 head `d405a4e52cf7ad22a0b5854f44656326dc04c89d`. Branch: `agent/orchestrator-pr12-corrections`. This is a correction layer stacked on PR12/PR7, not permission to merge unresolved dependencies.

Changes:
- Loader now requires the post-mortem manifest, rejects duplicate selected paths, compares the exact selected path set and every selected file SHA256, and closes each input file after reading.
- Report headlines now qualify independent-binomial null significance and heuristic online reliability/decomposition. Existing statistical code and saved numerical estimates are unchanged. The implied beta weight is labelled approximate (exact concentration subtracts 1), not optimized.
- Corrected the false statement that G/N differ only in size_exp; sixteen parameter differences mean historical pooled-WBot effects do not automatically transfer to a new policy.

Validation (Python 3.12.3, no arena, no refit):
- From `PokerBot/ExternalAnalysis/OpponentContext`: `python -B -m unittest -v test_manifest` passed six tests, covering matching manifest, missing manifest, wrong hash, same-JSON changed bytes, changed path set and duplicate used paths. Output `test_manifest_output.txt`.
- `python -B -c "import oc_parse; t=oc_parse.load_tables(); print('archive hash validation PASS:', len(t), 'unique tables')"` passed the actual committed archive: 135 selected tables. Output `archive_hash_check_output.txt`.
- The pre-correction independent audit also replayed all 135,000 hands with chip conservation and reproduced 110,190 first-bet responses. Its report is `PR12_Independent_Review.md` in the original local workspace.
- `git diff --check` passes. No strategy, bot parameters, inputs or saved statistical results changed.

SHA256 below is for LF-normalized source bytes (matching Git's indexed representation under this checkout's autocrlf setting):

- `OpponentContext/oc_parse.py`: `c2b4c37df9ce29aa8a2367bbc9cd7b78a54476a771d61cd570baf91bcadf2d45`
- `OpponentContext/oc_stats.py`: `352d031777db9ef23485159ff92c26d0846b5760129124339d62c8b56cffe5e2`
- `OpponentContext/test_manifest.py`: `afabb158f61187a628d053d463419e53d3420ace91056faf6a796331143c1928`
