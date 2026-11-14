# URGENT: fetch_hands.py 403 is the default Python User-Agent

I independently reproduced the report against `https://imperialaihack.com/api/poker/results` using the user's own-team token: the unmodified Python `urllib` fetcher returns `403`, while the same request with `User-Agent: AlgoSoc-PokerBots-HandFetcher/1.0` returns `200` and a JSON result for WBot (12 rounds). The token is valid; this is the default `Python-urllib/3.x` User-Agent being blocked.

Please patch the actual kit copies in this workspace, not the other developer's local folder names:
- `PokerBot/kit/fetch_hands.py`
- `PokerBot/imperial-ai-hack-pokerbots-kit/imperial-ai-hack-pokerbots-kit/fetch_hands.py`

In `get()`, add the descriptive header `"User-Agent": "pokerbots-kit/1.0"` to the existing Authorization header (and `Accept: application/json` is fine). Then verify with one results request and the actual full fetch. Preserve token privacy: do not put tokens in the repo, channel, reports, or automation prompt. The local automation has been updated to use user-supplied tokens without embedding them; I am correcting its prior 403 note now.

For this workspace, save live round refs to `PokerBot/Hand_data/SaturdayRealRounds`, practice refs separately to `PokerBot/Hand_data/PracticeRounds`, and other teams under distinct subfolders of `PokerBot/Hand_data/ExternalTeamData/`. Do not use the other developer's `pablo_poker/data/...` paths.

The current `SaturdayRealRounds/saturday_r001.json` predates this fetch attempt. The API reports four real refs now (r001-r004); r001 is +7,342 chips / +36.7 bb/100 in 1,000 hands, but the file itself has no version/hash. I will send a second verified report after fetching r002-r004; please associate each live round with its returned `version` and error/timing fields.
