# Independent re-derivation (no use of the PR's scripts): dedup, zero-sum, WBot with/without the 7 worst bots,
# WBot attributed flow vs leaderboard top-21, using one-winner-proportional attribution.
import json,glob,os,collections,sys
root=sys.argv[1]
files=sorted(glob.glob(root+'/Hand_data/SaturdayRealRounds/*.json')+glob.glob(root+'/Hand_data/ExternalTeamData/*/SaturdayRealRounds/*.json'))
fin=json.load(open(root+'/ExternalAnalysis/SaturdayFieldPostmortem/data/final_standings_saturday.json',encoding='utf-8'))['saturday']['standings']
rank=[r['name'] for r in fin]; TOP21=set(rank[:21])
BIG7={"clanker","ediz_slow","AIl IN","Joca","YSL_TWIZZY","Anton","ND"}
seen=set(); T=0; H=0; nonzero=0; acc=collections.Counter()
wb={'with':[0,0,0],'without':[0,0,0]}  # chips, hands, tables
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
    g='with' if (BIG7 & set(P))-{'WBot'} else 'without'
    wb[g][0]+=chips; wb[g][1]+=len(d['hands']); wb[g][2]+=1
    for h in d['hands']:
        res=h['results']; G=sum(-x for x in res if x<0)
        for j,p in enumerate(P):
            if j==i: continue
            if p in TOP21: pairhands_top+=1
            if not G or p not in TOP21: continue
            if res[i]>0 and res[j]<0: fl_top+=res[i]*(-res[j])/G
            if res[j]>0 and res[i]<0: fl_top-=res[j]*(-res[i])/G
print('unique tables',T,'hands',H,'non-zero-sum hands',nonzero,'by observing account',dict(acc))
for g,(c,n,t) in wb.items(): print('WBot %-7s donors: %+.1f bb/100 over %d tables (%d hands)'%(g,c/n/20*100,t,n))
print('WBot vs top21 (x7 per-pair scaling): %+.1f bb/100'%(7*fl_top/pairhands_top/20*100))
