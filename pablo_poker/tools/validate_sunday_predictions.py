"""Held-out public-action prediction checks, no simulated play or profit claims."""
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def evaluate(bundle):
    train=defaultdict(Counter);test=defaultdict(Counter);pop=Counter()
    for row in bundle['groups']:
        if row['split']=='train':train[row['team']].update(row['counts']);pop.update(row['counts'])
        else:test[row['team']].update(row['counts'])
    output={}
    for team in bundle['roster']:
        counts=test[team];loss=base_loss=n=0;contexts=[]
        for key,opportunities in counts.items():
            if not key.endswith('/opportunities'):continue
            context=key.rsplit('/',1)[0]
            actions=('check','raise') if context.endswith('/checked_to') else (('fold','call','raise','check') if context.startswith('open/') else ('fold','call','raise'))
            observed=[counts[context+'/'+a] for a in actions]
            if sum(observed)!=opportunities:raise ValueError('action counts disagree: '+context)
            pc=[pop[context+'/'+a] for a in actions];pt=sum(pc)
            prior=[(v+1)/(pt+len(actions)) for v in pc]
            tc=[train[team][context+'/'+a] for a in actions];tn=sum(tc)
            pred=[(v+20*p)/(tn+20) for v,p in zip(tc,prior)]
            loss-=sum(o*math.log(max(1e-9,p)) for o,p in zip(observed,pred))
            base_loss-=sum(o*math.log(max(1e-9,p)) for o,p in zip(observed,prior))
            n+=opportunities
            contexts.append(dict(context=context,train_n=tn,test_n=opportunities,actions=actions,
                                 predicted=pred,actual=[o/opportunities for o in observed]))
        output[team]=dict(opportunities=n,heldout_hands=counts.get('hands',0),
            log_loss=loss/n if n else None,population_log_loss=base_loss/n if n else None,
            status='measured' if n else 'no_heldout_coverage',contexts=contexts)
    return dict(status='prediction_diagnostic_not_simulator_validation',teams=output)


if __name__=='__main__':
    bundle=json.loads((ROOT/'sunday/evidence.json').read_text())
    result=evaluate(bundle)
    (ROOT/'sunday/prediction_validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({n:{k:v for k,v in r.items() if k!='contexts'} for n,r in result['teams'].items()},indent=2))
