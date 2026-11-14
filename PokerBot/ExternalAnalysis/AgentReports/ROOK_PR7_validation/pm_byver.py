# Independent re-derivation (no use of the PR's scripts): dedup, zero-sum, WBot with/without the 7 worst bots,
# WBot attributed flow vs leaderboard top-21, using one-winner-proportional attribution.
import json,glob,os,collections,sys
root=sys.argv[1]
files=sorted(glob.glob(root+'/Hand_data/SaturdayRealRounds/*.json')+glob.glob(root+'/Hand_data/ExternalTeamData/*/SaturdayRealRounds/*.json'))
fin=json.load(open(root+'/ExternalAnalysis/SaturdayFieldPostmortem/data/final_standings_saturday.json',encoding='utf-8'))['saturday']['standings']
rank=[r['name'] for r in fin]; TOP21=set(rank[:21])
BIG7={"clanker","ediz_slow","AIl IN","Joca","YSL_TWIZZY","Anton","ND"}
seen=set(); T=0; H=0; nonzero=0; acc=collections.Counter()
wb=collections.defaultdict(lambda:[0,0,0]); FT=collections.defaultdict(float); PT=collections.Counter()
fl_top=0.0; pairhands_top=0
for f in files:
    d=json.loads(open(f,'rb').read().decode('utf-8-sig'))
    k=(d['ref'],tuple(d['players']))
    if 'practice' in d['ref'] or k in seen: continue
    seen.add(k); T+=1; P=d['players']; acc[P[d['seat']]]+=1
    for h in d['hands']:
        H+=1; nonzero+= sum(h['results'])!=0
    if 'WBot' not in P: continue
    i=P.index('WBot'); chips=sum(h['results'][i] for h in d['hands'])
    rn=int(d['ref'].split('/')[-1][1:]); ver='G(v5/v7)' if rn<=23 or rn==48 else ('I(v6)' if rn<=47 else ('N?(v8)' if rn<=53 else 'r54+'))
    g=ver+('|with' if (BIG7 & set(P))-{'WBot'} else '|without')
    wb[g][0]+=chips; wb[g][1]+=len(d['hands']); wb[g][2]+=1
    for h in d['hands']:
        res=h['results']; G=sum(-x for x in res if x<0)
        for j,p in enumerate(P):
            if j==i: continue
            if p in TOP21: PT[ver]+=1
            if not G or p not in TOP21: continue
            if res[i]>0 and res[j]<0: FT[ver]+=res[i]*(-res[j])/G
            if res[j]>0 and res[i]<0: FT[ver]-=res[j]*(-res[i])/G
print('unique tables',T,'hands',H,'non-zero-sum hands',nonzero,'by observing account',dict(acc))
for g,(c,n,t) in sorted(wb.items()): print('WBot %-18s donors: %+.1f bb/100 over %d tables'%(g,c/n/20*100,t))
[print('WBot vs top21 %s: %+.1f bb/100 (%d pair-hands)'%(v,7*FT[v]/PT[v]/20*100,PT[v])) for v in sorted(PT)]
