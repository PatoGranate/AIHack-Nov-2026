"""Public-action profiles; no opponent private cards used. Standard library only."""
from pathlib import Path
from collections import defaultdict,Counter
import json,math,hashlib
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
DATA=ROOT/'Hand_data'

def rate(k,n):
    if not n:return {'events':k,'opportunities':n,'rate':None,'wilson95':None}
    z=1.95996398454;p=k/n;den=1+z*z/n;center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return {'events':k,'opportunities':n,'rate':p,'wilson95':[center-half,center+half]}
def position(i,button,n):
    p=(i-button)%n
    if p in (0,1,2):return ('BTN','SB','BB')[p]
    if p==n-1:return 'CO'
    if p==n-2:return 'HJ'
    return 'UTG' if p==3 else ('MP' if p==n-3 else 'UTG+1')
def size_bucket(s):return '<=0.33' if s<=.335 else '<=0.67' if s<=.675 else '<=1.0' if s<=1.005 else '>1.0'
def fresh():return {'hands':0,'chips':0,'vpip':0,'pfr':0,'rfi':Counter(),'rfiPos':defaultdict(Counter),'foldOpen':Counter(),'open3':Counter(),'blind':Counter(),'post':defaultdict(Counter),'actions':Counter(),'rounds':[]}

datasets={};duplicates=[];conflicts=[]
files=list(sorted(DATA.rglob('*.json')))
for f in files:
    d=json.loads(f.read_text(encoding='utf-8'));key=(d['ref'],tuple(d['players']))
    source='external' if ('ExternalTeamData' in f.parts or 'ExternalData_OtherBots' in f.parts) else 'own'
    if key not in datasets:datasets[key]={'data':d,'sources':[str(f.relative_to(ROOT))],'groups':{source}}
    else:
        entry=datasets[key];entry['sources'].append(str(f.relative_to(ROOT)));entry['groups'].add(source)
        old={h['n']:h for h in entry['data']['hands']}
        for h in d['hands']:
            if h['n'] in old and (h['events']!=old[h['n']]['events'] or h['results']!=old[h['n']]['results']):conflicts.append({'ref':d['ref'],'hand':h['n'],'source':str(f)})
        duplicates.append({'ref':d['ref'],'roster':d['players'],'source':str(f.relative_to(ROOT))})
stats=defaultdict(fresh);validation=Counter();tableinfo=[]
for key,entry in datasets.items():
    d=entry['data'];names=d['players'];n=len(names);roundchips=[0]*n
    before={nm:{'rfi':Counter(stats[nm]['rfi']),'rfiPos':{k:Counter(v) for k,v in stats[nm]['rfiPos'].items()},'vpip':stats[nm]['vpip'],'pfr':stats[nm]['pfr'],'foldOpen':Counter(stats[nm]['foldOpen']),'open3':Counter(stats[nm]['open3']),'post':{k:Counter(v) for k,v in stats[nm]['post'].items()}} for nm in names}
    tableinfo.append({'ref':d['ref'],'roster':names,'hands':len(d['hands']),'sources':entry['sources'],'groups':sorted(entry['groups']),'publicEventSha256':hashlib.sha256(json.dumps([(h['n'],h['events'],h['results']) for h in sorted(d['hands'],key=lambda h:h['n'])],separators=(',',':'),ensure_ascii=True).encode('utf-8')).hexdigest()})
    for h in d['hands']:
        contrib=[0]*n;bets=[0]*n;folded=[False]*n;street='preflop';nr=0;opener=None;limpers=0;open_clean=False;firstbet=None
        vp=set();pr=set();openrespond=set();openerrespond=False;firstrespond=set();button=h['button'];start=h.get('start_stacks',h.get('stacks',[2000]*n))
        for i,nm in enumerate(names):stats[nm]['hands']+=1;stats[nm]['chips']+=h['results'][i];roundchips[i]+=h['results'][i]
        for e in h['events']:
            kind=e[0]
            if kind=='post':contrib[e[1]]+=e[2];bets[e[1]]+=e[2];continue
            if kind=='board':street=e[1];bets=[0]*n;nr=0;firstbet=None;firstrespond=set();continue
            if kind=='refund':
                contrib[e[1]]-=e[2];bets[e[1]]=max(0,bets[e[1]]-e[2]);validation['refunds']+=1;continue
            if kind!='act':continue
            _,i,a,amt=e;nm=names[i];o=stats[nm];cur=max(bets);pot=sum(contrib);pos=position(i,button,n)
            o['actions'][street+':'+a]+=1
            if street=='preflop':
                if nr==0 and limpers==0:
                    for c in (o['rfi'],o['rfiPos'][str(n)+'max '+pos]):c['opp']+=1;c['raise']+=int(a=='raise')
                if nr==1 and i!=opener and i not in openrespond and a in ('fold','call','raise') and cur>bets[i]:
                    o['foldOpen']['opp']+=1;o['foldOpen'][a]+=1;openrespond.add(i)
                    if open_clean and pos in ('SB','BB') and position(opener,button,n) in ('CO','BTN','SB'):
                        o['blind']['opp']+=1;o['blind'][a]+=1
                if nr==2 and i==opener and not openerrespond and a in ('fold','call','raise') and cur>bets[i]:
                    o['open3']['opp']+=1;o['open3'][a]+=1;openerrespond=True
                if a in ('call','raise'):vp.add(i)
                if a=='raise':
                    pr.add(i)
                    if nr==0:opener=i;open_clean=limpers==0
                elif a=='call' and nr==0:limpers+=1
            else:
                if nr==1 and firstbet is not None and i!=firstbet['seat'] and i not in firstrespond and cur>bets[i] and a in ('fold','call','raise'):
                    context='HU' if firstbet['live']==2 else 'multiway'
                    b=street+' '+size_bucket(firstbet['size'])+' '+context
                    for bucket in (o['post'][b],o['post'][street+' ALL '+context]):bucket['opp']+=1;bucket[a]+=1
                    firstrespond.add(i)
                if a=='raise' and nr==0:firstbet={'seat':i,'size':(amt-bets[i])/max(1,pot),'live':sum(not f for f in folded),'pot':pot}
            if a=='raise':
                inc=amt-bets[i]
                if inc<0:validation['negative_raise_increment']+=1
                contrib[i]+=inc;bets[i]=amt;nr+=1
            elif a=='call':contrib[i]+=amt;bets[i]+=amt
            elif a=='fold':folded[i]=True
            if any(c<0 for c in contrib):validation['negative_contribution']+=1
            if any(c>s for c,s in zip(contrib,start)):validation['overstack_contribution']+=1
        for i in vp:stats[names[i]]['vpip']+=1
        for i in pr:stats[names[i]]['pfr']+=1
        wins=sum(e[2] for e in h['events'] if e[0]=='win')
        if wins!=sum(contrib):validation['pot_vs_awards_mismatch']+=1
        if sum(h['results'])!=0:validation['nonzero_results_sum']+=1
        validation['hands']+=1
    for i,nm in enumerate(names):
        s=stats[nm];old=before[nm]
        s['rounds'].append({'ref':d['ref'],'roster':names,'hands':len(d['hands']),'chips':roundchips[i],'bb100':roundchips[i]/20/len(d['hands'])*100,'groups':sorted(entry['groups']),'rfiCounts':dict(s['rfi']-old['rfi']),'rfiPosCounts':{k:dict(v-old['rfiPos'].get(k,Counter())) for k,v in s['rfiPos'].items() if (v-old['rfiPos'].get(k,Counter()))},'vpipCount':s['vpip']-old['vpip'],'pfrCount':s['pfr']-old['pfr'],'foldOpenCounts':dict(s['foldOpen']-old['foldOpen']),'openerThreebetCounts':dict(s['open3']-old['open3']),'postCounts':{k:dict(v-old['post'].get(k,Counter())) for k,v in s['post'].items() if (v-old['post'].get(k,Counter()))}})

def response(c):return {**rate(c['fold'],c['opp']),'folds':c['fold'],'calls':c['call'],'raises':c['raise']}
profiles={}
for nm,s in stats.items():
    profiles[nm]={'hands':s['hands'],'chips':s['chips'],'bb100_descriptive':s['chips']/20/s['hands']*100,'tableRounds':len(s['rounds']),'vpip':rate(s['vpip'],s['hands']),'pfr':rate(s['pfr'],s['hands']),'raiseFirstIn':rate(s['rfi']['raise'],s['rfi']['opp']),'raiseFirstInByPosition':{p:rate(c['raise'],c['opp']) for p,c in s['rfiPos'].items()},'foldToSingleOpen':response(s['foldOpen']),'openerFoldToThreebet':response(s['open3']),'blindFoldToLateOpen':response(s['blind']),'postflopFirstBetResponse':{b:response(c) for b,c in s['post'].items()},'actions':dict(s['actions']),'roundResults':s['rounds']}
result={'datasets':tableinfo,'duplicateSources':duplicates,'conflicts':conflicts,'validation':dict(validation),'profiles':profiles,'method':{'dedup':'(round ref, ordered roster); compare public events/results; no hidden cards used','postflop':'Response to street first bet while still exactly one bet/raise; sizes are original bet added / pot BEFORE bet; HU/multiway at bet time','preflop':'RFI opportunity means no raise and no prior limper. Fold-to-single-open includes cold/limp responses; opener-facing-first-reraise measured separately. Blind late-open defence uses clean CO/BTN/SB opens.','uncertainty':'Wilson95 describes opportunity rates, not independent-hand formal inference; actions cluster by table/hand; profits descriptive only.'}}
groups={}
for group in ('external','own'):
    groups[group]={}
    for nm,p in profiles.items():
        rr=[r for r in p['roundResults'] if group in r['groups']]
        if not rr:continue
        h=sum(r['hands'] for r in rr);fo=Counter();f3=Counter();post=defaultdict(Counter)
        for r in rr:
            fo.update(r['foldOpenCounts']);f3.update(r['openerThreebetCounts'])
            for k,v in r['postCounts'].items():post[k].update(v)
        groups[group][nm]={'hands':h,'tableRounds':len(rr),'vpip':rate(sum(r['vpipCount'] for r in rr),h),'pfr':rate(sum(r['pfrCount'] for r in rr),h),'foldToSingleOpen':response(fo),'openerFoldToThreebet':response(f3),'postflopFirstBetResponse':{k:response(v) for k,v in post.items()}}
result['profilesBySourceGroup']=groups
result['method']['sourceGroups']='external and own subgroups overlap on the duplicate table seen from both perspectives; do not sum subgroup exposures. Global profiles count each unique table once.'
OUT.mkdir(exist_ok=True);(OUT/'profiles.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
def pct(r):
    if not r['opportunities']:return '0/0 (unknown)'
    lo,hi=r['wilson95'];return f"{r['events']}/{r['opportunities']}={r['rate']:.1%} [Wilson95 {lo:.1%},{hi:.1%}]"
lines=['PUBLIC-ACTION OPPONENT PROFILES','',f"{len(files)} files; {len(datasets)} unique table rounds; {validation['hands']} hands; {len(profiles)} player names.",f'Duplicate source copies: {len(duplicates)}; public-event/result conflicts: {len(conflicts)}.', 'No hidden cards used. Descriptive winnings are field-dependent; no universal ranking.', 'Rates include counts and Wilson95 intervals; clustered action opportunities make', 'these approximate descriptions, not formal independent evidence of future edge.', '', 'DATA VALIDATION',json.dumps(dict(validation),indent=2),'', 'OPPONENTS (alphabetical)']
for nm,p in sorted(profiles.items()):
    lines.extend(['',nm,f"Exposure {p['hands']} hands / {p['tableRounds']} table-rounds; descriptive {p['bb100_descriptive']:+.1f} bb/100",'VPIP '+pct(p['vpip'])+'; PFR '+pct(p['pfr']),'RFI '+pct(p['raiseFirstIn']),'Fold to single open '+pct(p['foldToSingleOpen']),'Opener fold to three-bet '+pct(p['openerFoldToThreebet']),'Blind fold to clean late open '+pct(p['blindFoldToLateOpen']),'RFI by position:'])
    lines.extend('  '+k+': '+pct(v) for k,v in sorted(p['raiseFirstInByPosition'].items()))
    lines.append('First postflop bet responses (folds/opportunities; calls/raises available in JSON):')
    lines.extend('  '+k+': '+pct(v) for k,v in sorted(p['postflopFirstBetResponse'].items()))
lines.extend(['','CLONE STRUCTURE TO PRESERVE', 'Keep opener-defence distinct from general fold-to-open. Preserve position and', 'HU/multiway, street and original size context. Do not infer a smooth size-response', 'curve from buckets with few opportunities. Responses after raises are excluded', 'from first-bet buckets; add separate raise-facing models rather than mixing them.', 'Public-action frequencies identify hypotheses; composition and selection effects', 'prevent treating showdown or net-winnings rankings as intrinsic skill.'])
(OUT/'Profiles_Report.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for p in (OUT/'profiles.json',OUT/'Profiles_Report.txt'):p.read_bytes().decode('utf-8',errors='strict')
print(json.dumps({'files':len(files),'tables':len(datasets),'hands':validation['hands'],'names':len(profiles),'duplicates':len(duplicates),'conflicts':len(conflicts),'validation':dict(validation)}))
