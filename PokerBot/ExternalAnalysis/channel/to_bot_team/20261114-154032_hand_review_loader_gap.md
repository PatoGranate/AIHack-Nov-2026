# Hand-review loader: remaining external-data coverage gap

Thanks for the partial loader update. I checked the current `tools/review/build_review_data.py`: it now loads `PracticeRounds` and `SaturdayRealRounds`, so that part of the earlier audit is resolved. The updated inventory has 60 JSON files -> 31 unique table-rounds / 31,000 hands, 29 repeated perspectives, zero public-history hash conflicts.

The remaining coverage issue is that the loader reads only `ExternalData_OtherBots` for external tables. It does not scan the 21 JSON files currently under `Hand_data/ExternalTeamData` (kaiserbot and Red token downloads). It also deduplicates by `(ref, ordered players)` and drops later copies, which cannot preserve distinct source-team viewpoints/private-card provenance if you add those folders directly.

Please add a source manifest/label (team, live/practice, ref, upload version, viewpoint/seat, file hash, public-history hash); include `ExternalTeamData`; retain each viewpoint as a source record; deduplicate the public action summary by canonical table identity/hash. Preserve the viewer's existing hidden-card/showdown gating. `Hand_data/README.md` is still absent, `_fetched` remains present, and no source data was deleted. Current audit: `ExternalAnalysis/Hand_Data_Storage_Audit.txt`.
