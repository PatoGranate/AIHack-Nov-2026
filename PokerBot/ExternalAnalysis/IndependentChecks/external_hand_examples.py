import json,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
stats=collections.defaultdict(lambda:collections.Counter());examples=[]
seen=set()
for f in sorted((ROOT/'Hand_data/ExternalData_OtherBots').glob('*.json')):
 d=json.loads(f.read_text(encoding='utf-8'));names=d['players'];key=(d['ref'],tuple(names))
 if key in seen:continue
 seen.add(key)
 for h in d['hands']:
  for i,nm in enumerate(names):stats[nm]['hands']+=1;stats[nm]['chips']+=h['results'][i]
  pot=0;bet=[0]*len(names);street='preflop';cur=20;lastinc=20;raises=0;opener=None;flags=set();openersfaced=set()
  for e in h['events']:
   if e[0]=='board':street=e[1];bet=[0]*len(names);cur=0;lastinc=20;continue
   if e[0]=='post':bet[e[1]]+=e[2];pot+=e[2];continue
   if e[0]!='act':continue
   _,s,a,amt=e;nm=names[s];tc=max(bet)-bet[s]
   if street=='preflop':
    if raises>=2 and s==opener and s not in openersfaced:
     stats[nm]['open_faces_reraise']+=1;stats[nm]['open_fold_reraise']+=int(a=='fold');openersfaced.add(s)
     flags.add('opener_response_to_reraise')
    if a=='raise':
     raises+=1
     if raises==1:opener=s
   if a=='raise':
    add=amt-bet[s];ratio=add/max(1,pot);inc=amt-cur
    if street!='preflop':
     stats[nm]['post_bets']+=1
     if ratio>=1.5:stats[nm]['overbets_1p5']+=1;flags.add('overbet_'+nm)
     if inc==lastinc and cur>0:stats[nm]['minraises']+=1;flags.add('minraise_'+nm)
     if ratio<=.2:stats[nm]['tinybets']+=1;flags.add('tinybet_'+nm)
    if inc>=lastinc:lastinc=inc
    cur=amt;bet[s]=amt;pot+=add
   elif a=='call':bet[s]+=amt;pot+=amt
  if flags:
   examples.append({'file':f.name,'ref':d['ref'],'roster':names,'hand':h,'flags':sorted(flags)})
rank=sorted(stats.items(),key=lambda kv:kv[1]['chips']/kv[1]['hands'],reverse=True)
(OUT/'external_examples_candidates.json').write_text(json.dumps(examples,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'external_examples_stats.json').write_text(json.dumps(dict(stats),ensure_ascii=False,indent=2),encoding='utf-8')
print('RANK')
for nm,s in rank:print(nm,dict(s),'bb100',round(s['chips']/20/s['hands']*100,2))
print('REVEALED UNUSUAL CANDIDATES')
for ex in examples:
 h=ex['hand'];shown=set(h.get('showdown',{}));names=ex['roster']
 actors=[i for i in range(len(names)) if str(i) in shown and any(names[i] in flag for flag in ex['flags'])]
 if actors and any(h['results'][i]>500 for i in actors):print(ex['file'],h['n'],ex['flags'],[(names[i],h['hole'].get(str(i)),h['results'][i]) for i in actors])
