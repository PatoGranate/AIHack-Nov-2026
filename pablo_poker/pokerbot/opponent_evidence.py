"""Public-action sufficient statistics. No hidden cards or action recommendations.

All counters store observed opportunities, not prior pseudo-counts. Stage/round
and opponent version belong in the outer record; unknown versions remain unknown.
"""
from collections import Counter


def round_identity(ref):
    parts=str(ref).strip('/').split('/')
    if not parts or not parts[-1].startswith('r') or not parts[-1][1:].isdigit():
        raise ValueError('unknown round reference: '+str(ref))
    return '/'.join(parts[:-1]),int(parts[-1][1:])


def position(seat,button,n):
    off=(seat-button)%n
    if off in (0,1,2):return ('BTN','SB','BB')[off]
    return {n-1:'CO',n-2:'HJ'}.get(off,'EP')


def size_band(frac):
    return next((str(i) for i,edge in enumerate((.25,.45,.7,1.,1.5,2.)) if frac<edge),'6')


def hand_counts(hand,players,hero='WBot'):
    out={name:Counter(hands=1) for name in players}
    n=len(players);bets=[0]*n;pot=0;raises=0;street='preflop';alive=set(range(n))
    facing=None;vol=set();opener=None;vp=set();pfr=set()
    for e in hand['events']:
        if e[0]=='post':bets[e[1]]+=e[2];pot+=e[2]
        elif e[0]=='refund':bets[e[1]]-=e[2];pot-=e[2]
        elif e[0]=='board':street=e[1];bets=[0]*n;raises=0;facing=None
        elif e[0]=='act':
            _,seat,action,amount=e;cur=max(bets);owed=max(0,cur-bets[seat])
            name=players[seat];c=out[name];pos=position(seat,hand['button'],n)
            if street=='preflop':
                if raises==0 and not vol and seat not in (opener,):
                    c['open/'+pos+'/opportunities']+=1
                    c['open/'+pos+'/'+action]+=1
                if raises==1 and owed>0:
                    c['vs_open/'+pos+'/opportunities']+=1;c['vs_open/'+pos+'/'+action]+=1
                if raises==2 and seat==opener and owed>0:
                    c['vs_3bet/opportunities']+=1;c['vs_3bet/'+action]+=1
                if action in ('call','raise'):vp.add(seat);vol.add(seat)
                if action=='raise':
                    pfr.add(seat)
                    if amount>=600:c['big']+=1
                    if raises==0:opener=seat
            else:
                context=street+('/hu' if len(alive)==2 else '/mw')
                if owed>0 and facing:
                    bettor,band,is_raise=facing
                    target='/vs_WBot' if players[bettor]==hero else '/vs_other'
                    key=context+target+('/raise/' if is_raise else '/bet/')+band
                    c[key+'/opportunities']+=1;c[key+'/'+action]+=1
                elif cur==0:
                    key=context+'/checked_to'
                    c[key+'/opportunities']+=1;c[key+'/'+action]+=1
            if action=='raise':
                add=amount-bets[seat]
                facing=(seat,size_band(add/max(1,pot)),cur>0)
                pot+=add;bets[seat]=amount;raises+=1
            elif action=='call':pot+=amount;bets[seat]+=amount
            elif action=='fold':alive.discard(seat)
    for s in vp:out[players[s]]['vpip']+=1
    for s in pfr:out[players[s]]['pfr']+=1
    return out


def posterior(success,opportunities,prior=.5,prior_mass=12):
    if not 0<=success<=opportunities:raise ValueError('invalid opportunity counts')
    a=success+prior*prior_mass;b=opportunities-success+(1-prior)*prior_mass
    mean=a/(a+b);sd=(a*b/((a+b)**2*(a+b+1)))**.5
    # Normal approximation is diagnostic only; retain a,b for exact downstream work.
    return dict(alpha=a,beta=b,mean=mean,sd=sd,observed_n=opportunities,prior_mass=prior_mass)
