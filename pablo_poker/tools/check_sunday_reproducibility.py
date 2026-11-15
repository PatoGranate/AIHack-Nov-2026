"""Tiny isolated Table D fixture/order check. Not a profitability benchmark."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.validate_field import load


def play(engine,hands,seed):
    from sim import fieldbot as fb
    from engine import FixedHandsTable
    fixture=ROOT/'sunday/fixture'
    fb.reset_state(json.loads((fixture/'hs_pool.json').read_text()))
    fb._MODEL.update(json.loads((fixture/'field_model.json').read_text()))
    fb._MODEL['adapt']=json.loads((fixture/'field_adapt.json').read_text())
    fb._V3.update(json.loads((fixture/'v3_model.json').read_text())['pop'])
    fb._SKILL.update({'_':0.,**json.loads((fixture/'field_skill.json').read_text())})
    fb.HS_FILE=str(fixture/'hs_pool.json')
    manifest=json.loads((fixture/'manifest.json').read_text())
    for rel,expected in manifest['dependencies'].items():
        if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=expected:
            raise ValueError('fixture code/data changed; rebuild explicitly: '+rel)
    names=['WBot']+manifest['roster']
    m=load(ROOT/'sunday'/engine,'isolated_hero')
    hero=m.Agent();hero.rng.seed(seed);hero.P.update(max_sims=32,max_ms=1e6,hard_ms=1e6)
    hero.bank=1e6;m.DEBUG=True
    class Player:
        def __init__(self,agent):self.agent=agent
        def start_table(self,seat,info):self.agent.on_table_start(info)
        def act(self,s):return self.agent.act(s)
        def hand_end(self,s):
            if hasattr(self.agent,'on_hand_end'):self.agent.on_hand_end(s)
    players=[Player(hero)]+[Player(fb.FieldBot(n,seed=seed*31+i)) for i,n in enumerate(names[1:],1)]
    result=FixedHandsTable(players,hands=hands,seed=seed,record=True).play()
    digest=hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
    return dict(engine=engine,seed=seed,hands=hands,hash=digest,chips=result['chips'],
                context_failures=getattr(hero,'context_failures',None),
                tags={s:p.summary()['tags'] for s,p in getattr(hero,'behavior_profiles',{}).items()})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--hands',type=int,default=8);a=ap.parse_args()
    if not 1<=a.hands<=100:raise ValueError('low-budget check capped at 100 hands')
    paths=['v4_baseline.py','v4_identity_bot.py']
    first=[play(p,a.hands,930101) for p in paths]
    second=[play(p,a.hands,930101) for p in reversed(paths)]
    paired={r['engine']:r for r in second}
    ok=all(r['hash']==paired[r['engine']]['hash'] for r in first)
    out=dict(status='pass' if ok else 'fail',scope='same code/cards/frozen files after reset; reversed job order',
             profit_claim=False,first=first,second=second)
    (ROOT/'sunday/reproducibility.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
    if not ok:raise SystemExit(1)
