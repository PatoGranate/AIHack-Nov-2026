"""Preflop adaptation: X facing a single open by Y -> X's 3-bet rate, vs Y's in-round fold rate when its open is
3-bet by others (fold3), and X in the blinds facing a steal attempt. Slope across (X,Y,table) cells."""
import json,glob,sys
from collections import defaultdict
seen=set(); P=defaultdict(lambda:[0,0,0,0])
fs=[]
for p in ('hands/saturday_r0*.json','hands/external/*/saturday_r0*.json'): fs+=glob.glob(p)
for f in fs:
    d=json.load(open(f,encoding='utf-8')); k=(d['round'].get('slot'),tuple(d['players']))
    if k in seen: continue
    seen.add(k); pl=d['players']; tid=str(k)
    for h in d['hands']:
        nr=0; opener=None; tb=None
        for e in h['events']:
            if e[0]=='board': break
            if e[0]!='act': continue
            _,s,a,amt=e
            if nr==1 and s!=opener and a in('fold','call','raise'):
                c=P[(pl[s],pl[opener],tid)]; c[0]+=1; c[1]+=a=='raise'
                if a=='raise': tb=s
            if nr==2 and s==opener and tb is not None and a in('fold','call','raise'):
                for x in set(pl)-{pl[tb],pl[opener]}:
                    c=P[(x,pl[opener],tid)]; c[2]+=1; c[3]+=a=='fold'
            if a=='raise':
                if nr==0: opener=s
                nr+=1
def slope(X):
    pts=[(c[3]/c[2],c[1]/c[0],c[0]) for (x,y,t),c in P.items() if x==X and c[0]>=10 and c[2]>=4]
    if len(pts)<20: return None
    W=sum(w for *_,w in pts); mx=sum(a*w for a,_,w in pts)/W; my=sum(b*w for _,b,w in pts)/W
    return sum(w*(a-mx)*(b-my) for a,b,w in pts)/max(1e-9,sum(w*(a-mx)**2 for a,_,w in pts)),len(pts),my
print('3-bet adaptation: change in X 3-bet rate vs opener Y per +1.0 in Y in-round fold-to-3bet (vs others)')
for b in ['Attention Is All In','Gherkers',"Mohil'sPokerBot",'The Market Makers','Anker Batteries','Resonance Qt','FisherMen','WBot','Red','kaiserbot']:
    r=slope(b); print('%-22s %s'%(b[:22],'%+.2f (cells %d, 3bet %.1f%%)'%(r[0],r[1],100*r[2]) if r else '-'))
