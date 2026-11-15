"""Does a bot adapt to each opponent within a round? For every (bot X, opponent Y, table): X's heads-up bet rate when
checked to vs Y, and Y's fold rate to bets from players other than X at that same table (an in-round, X-independent
measure of Y). Slope of X's bet rate on Y's fold rate, weighted by opportunities; split by hand half to see learning."""
import json,glob,sys
from collections import defaultdict
seen=set(); P=defaultdict(lambda:[0,0,0,0,0,0])  # (X,Y,table,half): opp,bets ; Yfold faced,folds (vs others)
fs=[]
fs=glob.glob(sys.argv[1]+'/*.json')
for f in fs:
    d=json.load(open(f,encoding='utf-8')); k=(d['round'].get('slot'),tuple(d['players']))
    if k in seen: continue
    seen.add(k); pl=d['players']; n=len(pl); tid=str(k)
    for h in d['hands']:
        half=0 if h['n']<=500 else 1
        alive=set(range(n)); street='preflop'; cur=0; agg=None
        for e in h['events']:
            if e[0]=='board': street=e[1]; cur=0; agg=None
            elif e[0]=='act':
                _,s,a,amt=e
                if street!='preflop':
                    if len(alive)==2 and cur==0 and a in('check','raise'):
                        y=[x for x in alive if x!=s][0]; c=P[(pl[s],pl[y],tid,half)]; c[0]+=1; c[1]+=a=='raise'
                    if cur>0 and agg is not None and s!=agg and a in('fold','call','raise'):
                        # record s's response to bettor agg, keyed for every possible X != agg
                        for x in set(pl)-{pl[agg],pl[s]}:
                            c=P[(x,pl[s],tid,half)]; c[2]+=1; c[3]+=a=='fold'
                    if a=='raise': cur=1; agg=s
                if a=='fold': alive.discard(s)
def slope(X,half=None):
    pts=[]
    for (x,y,t,hf),c in P.items():
        if x!=X or (half is not None and hf!=half) or c[0]<8 or c[2]<15: continue
        pts.append((c[3]/c[2],c[1]/c[0],c[0]))
    if len(pts)<20: return None
    W=sum(w for _,_,w in pts); mx=sum(a*w for a,_,w in pts)/W; my=sum(b*w for _,b,w in pts)/W
    sxy=sum(w*(a-mx)*(b-my) for a,b,w in pts); sxx=sum(w*(a-mx)**2 for a,_,w in pts)
    return sxy/sxx, len(pts), my
bots=['HERO','AnkerBatteries','Anton','Chinesepeoplecanfly','GamesGone','Poke','ResonanceQt','YSLTWIZZY']
print('slope = change in X bet rate per +1.0 in opponent fold rate (in-round). >0 = bets more into folders')
print('%-22s %-24s %-24s %-24s'%('bot','all hands','hands 1-500','hands 501-1000'))
for b in bots:
    r=[slope(b),slope(b,0),slope(b,1)]
    print('%-22s '%b[:22]+' '.join('%-24s'%('%+.2f (n=%d, bet %.0f%%)'%(x[0],x[1],100*x[2]) if x else '-') for x in r))
