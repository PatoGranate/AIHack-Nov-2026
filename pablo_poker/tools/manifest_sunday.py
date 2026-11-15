"""Hash review artifacts and ensure the protected final-V4 files were untouched."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=['sim/fieldbot.py','tools/validate_field.py','tools/bench_fields.py','tools/bench2.py',
       'tools/head_to_head.py','tools/calib_skill.py','fetch_hands.py','export_v2.py',
       'pokerbot/opponent_identity.py','pokerbot/opponent_evidence.py','pokerbot/context_model.py',
       'pokerbot/behavior_profile.py','pokerbot/cold_observer.py','tools/test_sunday.py',
       'tools/replay_joint_identity.py','tools/build_sunday_evidence.py','tools/validate_sunday_predictions.py',
       'tools/build_table_d_fixture.py','tools/replay_cold_profiles.py','tools/check_sunday_reproducibility.py',
       'tools/run_sunday_checks.py','tools/manifest_sunday.py']
paths=[ROOT/p for p in FILES]
for pattern in ('*.py','*.json','*.log','*.md'):
    paths+=list((ROOT/'sunday').glob(pattern))
paths+=list((ROOT/'sunday/fixture').glob('*.json'))
paths+=[ROOT/'sunday/.ignore',ROOT/'sunday/.gitignore']
hashes={str(p.relative_to(ROOT.parent)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
protected={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('bot.py','data/v4_bot.py','sunday/v4_baseline.py')}
expected='8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108'
if any(v!=expected for v in protected.values()):raise RuntimeError('protected V4 changed; investigate before relaying')
out=dict(task='CODEX-SUNDAY-01',owner='Codex',backup='Claude',timestamp=datetime.now(timezone.utc).isoformat(),
         status='tested_foundation_not_promoted',branch_head='no local Git metadata; remote head unverified',
         hashes=hashes,protected=protected,large_runs=False)
target=ROOT.parent/'externalanalysis/V4_CHANGE_MANIFEST.json'
target.write_text(json.dumps(out,indent=2));print(len(hashes),'hashed files; protected V4 unchanged')
