from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parent/'channel'
read=['20261114-141247_hello_and_status.md','20261114-143000_status_sidepots_quirks.md','20261114-143900_replies_and_quirk_results.md','20261114-143339_frozen_candidate.md','20261114-143700_re_independent_correction.md','20261114-144500_v7_promoted.md']
record={'readReplies':{name:hashlib.sha256((root/'to_reviewer'/name).read_bytes()).hexdigest() for name in read},'sentMessages':[p.name for p in sorted((root/'to_bot_team').glob('*.md'))]}
(root/'reviewer_state.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
lines=['Reviewer channel record — 14 November 2026','Read reply files (hashes in reviewer_state.json):']+read+['','Sent messages:']+record['sentMessages']+['','Latest independent evidence: IndependentLeagueV7/Results.txt; promotion packaged G matches tested hash.','ExternalData_OtherBots analysis underway. Do not deduplicate distinct tables by ref alone.']
(root/'Review_Log.txt').write_text('\n'.join(lines),encoding='utf-8')
print('Recorded',len(read),'read replies and',len(record['sentMessages']),'sent messages.')
