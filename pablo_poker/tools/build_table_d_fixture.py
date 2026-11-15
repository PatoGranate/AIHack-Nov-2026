"""Frozen Table D simulator bundle, built strictly before evidence holdout.

Copies/hash-records runtime dependencies. Skill/adaptation/warm pool are disabled
in the isolated fixture unless separately rebuilt before the cutoff; no leakage
is silently accepted. No live model is overwritten.
"""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.build_field_model import build
from tools.build_v3_model import build as live_build
from tools.build_sunday_evidence import timestamp


def main():
    evidence=json.loads((ROOT/'sunday/evidence.json').read_text());refs=set(evidence['heldout_refs'])
    slots=[]
    for rel in evidence['inputs']:
        d=json.loads((ROOT/rel).read_text());ref=d.get('ref',d['round']['ref'])
        if ref in refs:slots.append(timestamp(d['round']['slot']))
    if not slots:raise ValueError('need held-out rounds')
    cutoff=min(slots);field=build(before=cutoff);live=live_build(before=cutoff)
    roster=evidence['roster'];field['bots']={n:field['bots'][n] for n in roster}
    fixture=ROOT/'sunday/fixture';fixture.mkdir(exist_ok=True)
    files={'field_model.json':field,'v3_model.json':live,'field_skill.json':{},
           'field_adapt.json':{'ref':[.48,.92],'flop':{},'turn':{},'river':{}},'hs_pool.json':{}}
    for name,obj in files.items():(fixture/name).write_text(json.dumps(obj,sort_keys=True))
    code=['sim/fieldbot.py','engine/game.py','engine/cards.py','pokerbot/v2.py','sunday/v4_baseline.py']
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [fixture/n for n in files]+[ROOT/n for n in code]}
    manifest=dict(status='uncalibrated_fixture_no_promotion',roster=roster,training_before=cutoff,
        dependencies=hashes,disabled=['skill: no independent temporal fit','adaptation: no independent temporal fit','warm pool: no independent temporal fit'])
    (fixture/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
