"""How bettors play heads-up postflop against a specific opponent: bet freq when checked to, size, bluff share at
showdown, and net chips per hand vs that opponent. Groups: winners vs WBot/Red/kaiserbot. Targets: YSL, Anton, others."""
import json,glob,sys,os
from collections import defaultdict
sys.path.insert(0,'.')
from pokerbot.v2 import to_int,level_street
WIN={'Gherkers','Equity Engine',"Mohil'sPokerBot",'Attention Is All In','The Market Makers','Anton_','AAST','FisherMen','Anker Batteries','Resonance Qt'}
OURS={'WBot','Red','kaiserbot'}
TGT={'YSL_TWIZZY':'YSL','Anton':'Anton','Poke':'Poke'}
seen=set(); C=defaultdict(lambda: defaultdict(float))
fs=[]
for p in ('hands/saturday_r0*.json','hands/external/*/saturday_r0*.json'): fs+=glob.glob(p)
for f in fs:
    d=json.load(open(f,encoding='utf-8')); k=(d['round'].get('slot'),tuple(d['players']))
    if k in seen: continue
    seen.add(k); pl=d['players']; n=len(pl)
    for h in d['hands']:
        alive=set(range(n)); street='preflop'; bets=[0]*n; pot=0; board=[]
        sd=h.get('showdown') or {}; full=[to_int(c) for c in h['board']]
        for e in h['events']:
            if e[0]=='post': bets[e[1]]=e[2]; pot+=e[2]
            elif e[0]=='board': street=e[1]; bets=[0]*n; board=e[2]
            elif e[0]=='act':
                _,s,a,amt=e; cur=max(bets); add=amt-bets[s] if a=='raise' else (amt if a=='call' else 0)
                if street!='preflop' and len(alive)==2 and cur==0 and a in('check','raise'):
                    opp=[x for x in alive if x!=s][0]
                    g='winners' if pl[s] in WIN else ('ours' if pl[s] in OURS else None)
                    t=TGT.get(pl[opp],'others')
                    if g:
                        G=C[(g,t)]; G['opp']+=1
                        if a=='raise':
                            G['bet']+=1; G['size']+=add/max(1,pot)
                            if str(s) in sd and len(full)==5:
                                hc=[to_int(c) for c in h['hole'][str(s)]]; nb={'flop':3,'turn':4,'river':5}[street]
                                L=level_street(hc[0],hc[1],full[:nb]); G['shown']+=1; G['air']+=L==0; G['strong']+=L>=2
                if a=='fold': alive.discard(s)
                if a=='raise': bets[s]=amt
                else: bets[s]+=add
                pot+=add
        # net per hand in HU-to-showdown-or-not pots vs target: skip
print('%-8s %-7s %6s %7s %6s %6s %8s %8s'%('group','vs','opps','bet%','size','shown','air%','top+%'))
for g in ('winners','ours'):
    for t in ('YSL','Anton','Poke','others'):
        G=C[(g,t)]
        if G['opp']<30: continue
        print('%-8s %-7s %6d %6.0f%% %6.2f %6d %7.0f%% %7.0f%%'%(g,t,G['opp'],100*G['bet']/G['opp'],G['size']/max(1,G['bet']),G['shown'],100*G['air']/max(1,G['shown']),100*G['strong']/max(1,G['shown'])))
