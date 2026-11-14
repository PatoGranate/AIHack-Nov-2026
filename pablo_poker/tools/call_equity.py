"""Like-for-like revealed-hand equity on big calls; diagnostic, selection biased.

Only showdowns with every live opponent revealed are included. Folded cards and
future board cards are not used to compute equity at the call decision.
"""
from collections import Counter
import random
from pokerbot.v2 import evaluate, to_int


def measure(documents, hero_name='kaiserbot', samples=64):
    out=Counter()
    rng=random.Random(91837)
    for d in documents:
        if hero_name not in d['players']:continue
        me=d['players'].index(hero_name)
        for h in d['hands']:
            street='preflop';board=[];pot=0;bets=[0]*len(d['players'])
            live=set(range(len(bets)));fraction=0
            for e in h['events']:
                if e[0]=='post':pot+=e[2];bets[e[1]]+=e[2]
                elif e[0]=='board':street=e[1];board=e[2];bets=[0]*len(bets);fraction=0
                elif e[0]=='act':
                    _,s,a,amt=e
                    if a=='call' and s==me and street!='preflop' and fraction>=1:
                        sd=h.get('showdown',{})
                        if all(str(j) in sd and str(j) in h['hole'] for j in live):
                            holes={j:list(map(to_int,h['hole'][str(j)])) for j in live}
                            bd=list(map(to_int,board));dead=set(bd)
                            for cards in holes.values():dead.update(cards)
                            deck=[c for c in range(52) if c not in dead]
                            shares=[]
                            for _ in range(samples if len(bd)<5 else 1):
                                full=bd+rng.sample(deck,5-len(bd))
                                scores={j:evaluate(cards+full) for j,cards in holes.items()}
                                best=max(scores.values());wins=[j for j,v in scores.items() if v==best]
                                shares.append(1/len(wins) if me in wins else 0.)
                            out['n']+=1;out['equity_sum']+=sum(shares)/len(shares)
                            out[street+'_n']+=1;out[street+'_equity_sum']+=sum(shares)/len(shares)
                    if a=='raise':
                        add=amt-bets[s];fraction=add/max(1,pot);pot+=add;bets[s]=amt
                    elif a=='call':pot+=amt;bets[s]+=amt
                    elif a=='fold':live.discard(s)
    return dict(out)
