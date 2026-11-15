"""Build version-labelled, deduplicated Table D evidence and chronological split.

python -B tools/build_sunday_evidence.py --before 2026-11-15T00:00:00 --heldout-rounds 3
Only writes sunday/evidence.json. No secret values, hidden cards or live updates.
"""
import argparse
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from pokerbot.opponent_evidence import hand_counts,round_identity
from sunday.export_identity import ROSTER


def timestamp(text):
    # Tournament's supplied November schedule is UK/Canary UTC; explicit in output.
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp() if '+' not in text and not text.endswith('Z') else datetime.fromisoformat(text.replace('Z','+00:00')).timestamp()


def build(before,heldout_rounds=3):
    files=list((ROOT/'hands').glob('*.json'))+list((ROOT/'hands/external').rglob('*.json'))
    docs=[];versions=defaultdict(set);inputs={}
    for path in sorted(files):
        raw=path.read_bytes()
        try:d=json.loads(raw);meta=d['round'];ref=d.get('ref') or meta['ref'];ts=timestamp(meta['slot'])
        except (ValueError,KeyError,TypeError):continue
        if ts>=before or not set(d.get('players',[]))&set(ROSTER):continue
        if meta.get('hands')!=len(d.get('hands',[])):raise ValueError('incomplete round: '+str(path))
        round_identity(ref);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
        docs.append((ts,ref,d))
        seat=d.get('seat')
        if isinstance(seat,int) and seat<len(d['players']) and meta.get('version') is not None:
            versions[d['players'][seat],ref].add(str(meta['version']))
    refs=sorted({(ts,ref) for ts,ref,d in docs})
    held={ref for _,ref in refs[-heldout_rounds:]} if heldout_rounds else set()
    seen={};groups=defaultdict(Counter);conflicts=0
    for ts,ref,d in docs:
        table=d['round'].get('table')
        if table is None:table=hashlib.sha256(json.dumps(d['players']).encode()).hexdigest()[:12]
        stage,_=round_identity(ref)
        for h in d['hands']:
            key=(ref,str(table),h['n'])
            # Only public fields: perspective-specific hole cards never affect the digest.
            digest=hashlib.sha256(json.dumps([d['players'],h['button'],h['board'],h['events']],sort_keys=True).encode()).hexdigest()
            if key in seen:
                if seen[key]!=digest:conflicts+=1
                continue
            seen[key]=digest
            counts=hand_counts(h,d['players'])
            for name in ROSTER:
                if name not in counts:continue
                values=versions.get((name,ref),set())
                version=next(iter(values)) if len(values)==1 else 'unknown'
                groups[('heldout' if ref in held else 'train',stage,name,version)].update(counts[name])
    if conflicts:raise ValueError('conflicting public hand records: '+str(conflicts))
    return dict(schema=1,hero='WBot',roster=ROSTER,before=before,timezone='UTC (explicit schedule assumption)',
                heldout_refs=sorted(held),inputs=inputs,unique_hands=len(seen),
                version_policy='Only directly observed own-team round metadata; unknown remains unknown',
                groups=[dict(split=s,stage=st,team=n,version=v,counts=dict(c)) for (s,st,n,v),c in sorted(groups.items())])


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--before',required=True);ap.add_argument('--heldout-rounds',type=int,default=3)
    a=ap.parse_args();out=build(timestamp(a.before),a.heldout_rounds)
    path=ROOT/'sunday/evidence.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2));tmp.replace(path)
    print(json.dumps({k:v for k,v in out.items() if k not in ('groups','inputs')},indent=2))
