# Hand_data folder audit and cleanup recommendation

Audit of the current Hand_data tree found 54 JSON files but only 26 unique public table-rounds after keying on round ref plus ordered roster. Eighteen identity keys repeat across 28 perspectives/files; every repeated public action/result hash matches and no conflicts were found. The subagent also verified chip/pot reconciliation.

Specific exact hand-array duplicates:
- All 12 files in Hand_data/_fetched match WBot's organized PracticeRounds/SaturdayRealRounds copies; organized copies have round/team metadata. Please stop using _fetched and archive/remove it once you confirm no process consumes it.
- ExternalData_OtherBots practice r013-r017 exactly duplicate the kaiserbot team-token hand arrays.
- Legacy PracticeRounds/r1v1, r1v2, r1v3, r1v4, r2v1, r2v3, r3v1 exactly duplicate Saturday-practice filenames.

Preserve separate team-perspective files when private-card visibility differs (e.g., kaiserbot/Red share public r003/r004), but deduplicate public action statistics so each table is counted once. I did not delete files.

Please add Hand_data/README.md and a manifest mapping external_team_02=kaiserbot and external_team_03=Red, with round type, ref, site version, seat/viewpoint, file SHA and public-history SHA. Update tools/review/build_review_data.py to load the named PracticeRounds, SaturdayRealRounds and ExternalTeamData folders; it currently scans root r*v*.json plus ExternalData_OtherBots and misses the current live and new token data. Full audit is in ExternalAnalysis/Hand_Data_Storage_Audit.txt.
