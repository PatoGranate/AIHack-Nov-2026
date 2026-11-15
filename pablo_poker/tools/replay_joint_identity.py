"""Small temporal identity comparison, no simulated games or writes to live models."""
import argparse
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.validate_field import load
from tools.check_ident import histories
from tools.build_v3_model import build, slot_ts
from sunday.export_identity import export


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rounds',nargs='+',default=['052','053','054'])
    a=ap.parse_args()
    docs=[json.loads((ROOT/'hands/external/WBot'/('saturday_r%s.json'%r)).read_text()) for r in a.rounds]
    model=build(before=slot_ts(docs[0]['round']))
    rows=[]
    for d in docs:
        roster=[n for i,n in enumerate(d['players']) if i!=d['seat']]
        path=export(roster)  # evaluation knows membership, never seat mapping
        for label,source in [('old',ROOT/'sunday/v4_baseline.py'),('joint',path)]:
            m=load(source,'eval_'+label);m.MODEL=model;m._MODEL_SRC[0]=None
            agent=m.Agent(params={'use_historical_identity':True}) if label=='joint' else m.Agent()
            agent.seat=d['seat'];agent.n=len(d['players'])
            for i,h in enumerate(d['hands'],1):
                t=time.perf_counter();agent._learn(histories(h));elapsed=(time.perf_counter()-t)*1000
                if i in (25,100,250,1000):
                    for seat,true in enumerate(d['players']):
                        if seat==d['seat']:continue
                        if label=='joint':p=agent.identity_posteriors.get(seat,{'_unknown':1.})
                        else:
                            ll=agent.idll.get(seat,{})
                            if not ll:p={'_unknown':1.}
                            else:
                                import math
                                w=sum(b['w'] for b in model['bots'].values())
                                lp={n:v+math.log(.2 if n=='_pop' else .8*model['bots'][n]['w']/w) for n,v in ll.items()}
                                z=max(lp.values());ex={n:math.exp(v-z) for n,v in lp.items()};s=sum(ex.values());p={n:v/s for n,v in ex.items()}
                        pred=max(p,key=p.get);confidence=p[pred]
                        rows.append(dict(round=d['ref'],engine=label,hand=i,seat=seat,true=true,pred=pred,
                                         confidence=confidence,correct=pred==true,callback_ms=elapsed,
                                         true_probability=p.get(true,0)))
    summary={}
    for label in ('old','joint'):
        summary[label]={}
        for checkpoint in (25,100,250,1000):
            rs=[r for r in rows if r['engine']==label and r['hand']==checkpoint]
            summary[label][checkpoint]=dict(n=len(rs),correct=sum(r['correct'] for r in rs),
                confident_wrong=sum(not r['correct'] and r['confidence']>.9 for r in rs),
                max_checkpoint_callback_ms=max(r['callback_ms'] for r in rs))
    out=dict(training_before=docs[0]['ref'],membership='historical actual roster, not Sunday results',summary=summary,rows=rows)
    (ROOT/'sunday/identity_replay.json').write_text(json.dumps(out,indent=2))
    export() # restore Table D artifact after historical roster evaluations
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
