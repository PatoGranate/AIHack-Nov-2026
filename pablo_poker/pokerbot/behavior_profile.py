"""Cold-start public-action tags. Team names and historical profiles are unused.

Tags are diagnostic evidence, not automatic betting instructions. Compare recent
and preceding non-overlapping windows; abstain on sparse opportunities.
"""
from collections import Counter,deque
import math


def wilson(success,n,z=1.96):
    if not n:return 0.,1.
    p=success/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,center-half),min(1.,center+half)


def metrics(counts):
    def aggregate(prefix,outcome):
        pairs=[(k,v) for k,v in counts.items() if k.startswith(prefix) and k.endswith('/opportunities')]
        return sum(counts[k.rsplit('/',1)[0]+'/'+outcome] for k,v in pairs),sum(v for k,v in pairs)
    out={'vpip':(counts['vpip'],counts['hands']),'pfr':(counts['pfr'],counts['hands'])}
    for street in ('flop','turn','river'):
        keys=[k for k in counts if k.startswith(street+'/') and k.endswith('/checked_to/opportunities')]
        out[street+'_bet']=(sum(counts[k.rsplit('/',1)[0]+'/raise'] for k in keys),sum(counts[k] for k in keys))
    for metric,predicate,outcome in (
        ('small_bet_fold',lambda k:'/bet/' in k and k.split('/')[-2] in ('0','1','2'),'fold'),
        ('big_bet_fold',lambda k:'/bet/' in k and k.split('/')[-2] in ('4','5','6'),'fold'),
        ('postflop_raise',lambda k:k.startswith(('flop/','turn/','river/')) and ('/bet/' in k or '/raise/' in k),'raise')):
        keys=[k for k in counts if k.endswith('/opportunities') and predicate(k)]
        out[metric]=(sum(counts[k.rsplit('/',1)[0]+'/'+outcome] for k in keys),sum(counts[k] for k in keys))
    out['fold_to_3bet']=aggregate('vs_3bet/','fold')
    return out


class BehaviorProfile:
    def __init__(self,recent_hands=100,total_hands=500):
        self.recent_hands=recent_hands;self.total_hands=total_hands
        self.hands=deque();self.recent=Counter();self.previous=Counter();self.total_seen=0
        self.changed=[]

    def update(self,counts):
        counts=Counter(counts);self.hands.append(counts);self.recent.update(counts);self.total_seen+=1
        if len(self.hands)>self.recent_hands:
            moved=self.hands[-self.recent_hands-1];self.recent.subtract(moved);self.previous.update(moved)
        if len(self.hands)>self.total_hands:self.previous.subtract(self.hands.popleft())
        if self.total_seen % 10 == 0:self.changed=self._changes()

    def _changes(self):
        fast=metrics(self.recent);old=metrics(self.previous)
        changed=[]
        for key,(s,n) in fast.items():
            os,on=old[key]
            if n<30 or on<50:continue
            lo,hi=wilson(s,n,z=2.58);olo,ohi=wilson(os,on,z=2.58)
            if hi<olo or ohi<lo:changed.append(key)
        return changed

    def summary(self):
        changed=self.changed
        current=self.recent if changed else self.recent+self.previous
        estimates={}
        for key,(s,n) in metrics(current).items():
            lo,hi=wilson(s,n)
            estimates[key]=dict(success=s,observed_n=n,mean=s/n if n else None,low=lo,high=hi)
        tags=[]
        rules=[('loose_preflop','vpip','high',.35,80),('tight_preflop','vpip','low',.18,80),
               ('frequent_flop_bettor','flop_bet','high',.7,30),
               ('frequent_turn_bettor','turn_bet','high',.7,30),
               ('overfolds_small_bets','small_bet_fold','high',.65,40),
               ('rarely_folds_small_bets','small_bet_fold','low',.3,40),
               ('raise_prone','postflop_raise','high',.2,40),
               ('folds_to_3bets','fold_to_3bet','high',.7,30)]
        for label,metric,side,threshold,minimum in rules:
            e=estimates[metric]
            if e['observed_n']>=minimum and (e['low']>threshold if side=='high' else e['high']<threshold):tags.append(label)
        return dict(tags=tags or ['insufficient_distinctive_evidence'],metrics=estimates,
                    regime_change_suspected=changed,total_hands_seen=self.total_seen,
                    active_window='recent' if changed else 'rolling',
                    caveat='intervals assume Bernoulli samples; repeated testing and dependence require temporal calibration')
