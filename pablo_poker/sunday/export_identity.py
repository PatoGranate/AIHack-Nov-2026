"""Export isolated final-V4 + joint identification. Never replaces live bot.py."""
import ast
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
ROSTER=['Resonance Qt','Anker Batteries','Chinese people can fly','GamesGone','Poke','Anton','YSL_TWIZZY']


def export(roster=ROSTER):
    base=HERE/'v4_baseline.py'
    src=base.read_text(encoding='utf-8')
    src+='\n\n'+(ROOT/'pokerbot/opponent_identity.py').read_text(encoding='utf-8')
    src+='\n\n'+(ROOT/'pokerbot/context_model.py').read_text(encoding='utf-8')
    src+='\n\n'+(ROOT/'pokerbot/opponent_evidence.py').read_text(encoding='utf-8')
    src+='\n\n'+(ROOT/'pokerbot/behavior_profile.py').read_text(encoding='utf-8')
    evidence_path=HERE/'evidence.json'
    profiles={};population={}
    if evidence_path.exists():
        evidence=json.loads(evidence_path.read_text())
        for row in evidence['groups']:
            if row['split']!='train':continue
            target=profiles.setdefault(row['team'],{})
            for key,value in row['counts'].items():
                target[key]=target.get(key,0)+value
                population[key]=population.get(key,0)+value
    src+='\nCONTEXT_PROFILES = '+repr(profiles)+'\nCONTEXT_POPULATION = '+repr(population)+'\n'
    src+='\nSUNDAY_ROSTER = '+repr(list(roster))+'\n'
    src+=(HERE/'identity_adapter.py').read_text(encoding='utf-8')
    ast.parse(src)
    path=HERE/'v4_identity_bot.py'
    tmp=path.with_suffix('.tmp');tmp.write_text(src,encoding='utf-8');tmp.replace(path)
    manifest={'status':'candidate_not_promoted','default_mode':'cold_start_no_named_history',
              'historical_identity':'optional_uncalibrated',
              'roster':list(roster),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                        (base,ROOT/'pokerbot/opponent_identity.py',ROOT/'pokerbot/context_model.py',
                         ROOT/'pokerbot/opponent_evidence.py',ROOT/'pokerbot/behavior_profile.py',HERE/'identity_adapter.py',HERE/'export_identity.py')}}
    if evidence_path.exists():manifest['inputs']['sunday/evidence.json']=hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    (HERE/'identity_manifest.json').write_text(json.dumps(manifest,indent=2))
    return path


if __name__=='__main__':print(export())
