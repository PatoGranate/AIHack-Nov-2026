"""Capture deterministic contract-test evidence without PowerShell stderr effects."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
results=[]
for rel in ('tools/test_sunday.py','tools/test_field_changes.py'):
    r=subprocess.run([sys.executable,'-B',rel],cwd=ROOT,capture_output=True,text=True)
    results.append(dict(command=[sys.executable,'-B',rel],returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
out=dict(status='pass' if all(r['returncode']==0 for r in results) else 'fail',tests=results)
(ROOT/'sunday/contract_checks.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
if out['status']!='pass':raise SystemExit(1)
