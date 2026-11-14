# Table-bootstrap (within version group) of WBot's attributed result vs the leaderboard top 21.
import json,glob,collections,sys,random
root=sys.argv[1]
files=sorted(glob.glob(root+'/Hand_data/SaturdayRealRounds/*.json')+glob.glob(root+'/Hand_data/ExternalTeamData/*/SaturdayRealRounds/*.json'))
fin=json.load(open(root+'/ExternalAnalysis/SaturdayFieldPostmortem/data/final_standings_saturday.json',encoding='utf-8'))['saturday']['standings']
TOP21={r['name'] for r in fin[:21]}
seen=set(); per=collections.defaultdict(list)
for f in files:
    d=json.loads(open(f,'rb').read().decode('utf-8-sig')); k=(d['ref'],tuple(d['players']))
    if 'practice' in d['ref'] or k in seen: continue
    seen.add(k); P=d['players']
    if 'WBot' not in P: continue
    i=P.index('WBot'); rn=int(d['ref'].split('/')[-1][1:])
    ver='G(v5,v7,v9)' if rn<=23 or rn in (48,54) else ('I(v6)' if rn<=47 else 'N?(v8)')
    fl=0.0; ph=0
    for h in d['hands']:
        res=h['results']; G=sum(-x for x in res if x<0)
        for j,p in enumerate(P):
            if j==i or p not in TOP21: continue
            ph+=1
            if not G: continue
            if res[i]>0 and res[j]<0: fl+=res[i]*(-res[j])/G
            if res[j]>0 and res[i]<0: fl-=res[j]*(-res[i])/G
    per[ver].append((fl,ph))
rng=random.Random(20261114)
est=lambda t: 7*sum(a for a,_ in t)/sum(b for _,b in t)/20*100
for v,t in sorted(per.items()):
    bs=sorted(est([rng.choice(t) for _ in t]) for _ in range(2000))
    print('%-12s tables=%2d  WBot vs top21 %+6.1f bb/100  90%% table-bootstrap [%+6.1f, %+6.1f]'%(v,len(t),est(t),bs[100],bs[1899]))
