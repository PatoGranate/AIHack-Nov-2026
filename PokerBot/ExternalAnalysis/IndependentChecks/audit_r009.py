from pathlib import Path
from collections import Counter,defaultdict
from itertools import combinations
import sys,json,math,hashlib,random
ROUND=int(sys.argv[1]) if len(sys.argv)>1 else 9
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'ExternalAnalysis/IndependentChecks'/('Round9TableE' if ROUND==9 else f'Round{ROUND}Audit');OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'kit'))
from engine.cards import evaluate,to_int,full_deck
F=ROOT/f'Hand_data/SaturdayRealRounds/saturday_r{ROUND:03}.json';D=json.loads(F.read_text(encoding='utf-8'));ME=D['players'].index('WBot');N=len(D['players'])
def position(seat,button):
    p=(seat-button)%N
    if p in (0,1,2):return ('BTN','SB','BB')[p]
    if p==N-1:return 'CO'
    if p==N-2:return 'HJ'
    return 'UTG' if p==3 else 'MP' if p==N-3 else 'UTG+1'
groups=defaultdict(lambda:{'hands':0,'chips':0,'grossLoss':0,'grossWin':0});rows=[];errors=Counter()
for h in D['hands']:
    c=[0]*N;b=[0]*N;st='preflop';board=[];folded=[False]*N;nr=0;opener=None;heroOpen=False;call3=False;heroCallOpen=False;hero3bet=False;heroFold=None;allin=None;line=[];lastopp=None;vp=False;pr=False
    for ei,e in enumerate(h['events']):
        if e[0]=='post':c[e[1]]+=e[2];b[e[1]]+=e[2]
        elif e[0]=='refund':c[e[1]]-=e[2];b[e[1]]=max(0,b[e[1]]-e[2])
        elif e[0]=='board':st=e[1];board=e[2];b=[0]*N;nr=0
        elif e[0]=='act':
            _,s,a,amt=e;pot=sum(c);cur=max(b);tc=min(h['start_stacks'][s]-c[s],cur-b[s]);inc=amt-b[s] if a=='raise' else amt if a=='call' else 0
            if s==ME:
                line.append({'event':ei,'street':st,'board':list(board),'action':a,'amount':amt,'added':inc,'potBefore':pot,'toCall':tc,'potOdds':tc/(pot+tc) if tc else None,'livePlayers':sum(not x for x in folded),'lastOpponentAggressor':D['players'][lastopp] if lastopp is not None else None})
                if st=='preflop':
                    if a in ('call','raise'):vp=True
                    if a=='raise':pr=True;heroOpen|=nr==0;hero3bet|=nr>=1
                    if a=='call':call3|=heroOpen and nr>=2;heroCallOpen|=not heroOpen and nr==1
                if a=='fold':heroFold=st
            c[s]+=inc;b[s]+=inc
            if s==ME and c[s]>=h['start_stacks'][s] and allin is None:allin={'street':st,'board':list(board),'event':ei,'action':a,'potBefore':pot,'toCall':tc,'added':inc}
            if a=='raise':
                if st=='preflop' and nr==0:opener=s
                nr+=1
                if s!=ME:lastopp=s
            if a=='fold':folded[s]=True
    win=sum(e[2] for e in h['events'] if e[0]=='win')
    if win!=sum(c):errors['potMismatch']+=1
    if sum(h['results']):errors['chipSum']+=1
    result=h['results'][ME];shown=str(ME) in h.get('showdown',{})
    pf='fold preflop' if heroFold=='preflop' else 'open/call reraise' if call3 else 'hero reraise' if hero3bet else 'call initial open' if heroCallOpen else 'open without later call-reraise' if heroOpen else 'limp/check other'
    terminal='fold '+heroFold if heroFold else ('all-in '+allin['street'] if allin else 'showdown no all-in' if shown else 'win without showdown')
    winners=[D['players'][e[1]] for e in h['events'] if e[0]=='win']
    finalrisk='WBot full stack' if c[ME]>=2000 else 'opponent-only full stack' if any(v>=2000 for i,v in enumerate(c)if i!=ME)else 'neither'
    row={'hand':h['n'],'position':position(ME,h['button']),'heroHole':h.get('hole',{}).get(str(ME)),'board':h['board'],'result':result,'showdown':shown,'allin':allin,'finalRiskCategory':finalrisk,'preflopLine':pf,'terminalLine':terminal,'heroActions':line,'winners':winners,'contributions':c,'shownHoles':{s:v for s,v in h.get('hole',{}).items() if s in h.get('showdown',{})},'vpip':vp,'pfr':pr}
    rows.append(row)
    for k in ('position:'+row['position'],'preflop:'+pf,'terminal:'+terminal,'showdown:'+str(shown),'allin:'+str(allin is not None),'finalRisk:'+finalrisk):
        g=groups[k];g['hands']+=1;g['chips']+=result;g['grossLoss']+=max(0,-result);g['grossWin']+=max(0,result)
def equity(row):
    ai=row['allin'];holes=row['shownHoles']
    if not ai or str(ME) not in holes or len(holes)<2:return None
    seats=[int(s) for s in holes];hands={int(s):[to_int(x) for x in h] for s,h in holes.items()};board=[to_int(x) for x in ai['board']];known=set(board)|{c for h in hands.values() for c in h};deck=[c for c in full_deck() if c not in known];need=5-len(board)
    if need>2:
        rng=random.Random(9000+row['hand']);runouts=(rng.sample(deck,need) for _ in range(12000));mode='12000 sampled runouts'
    else:runouts=combinations(deck,need);mode='exact runouts'
    count=0;share=0
    for run in runouts:
        full=board+list(run);scores={s:evaluate(full+h) for s,h in hands.items()};best=max(scores.values());ws=[s for s,v in scores.items() if v==best];share+=(1/len(ws) if ME in ws else 0);count+=1
    return {'equityVsRevealedFinalContestants':share/count,'mode':mode,'runouts':count,'opponents':[D['players'][s] for s in seats if s!=ME],'warning':'Hindsight revealed hands, unknown folded cards ignored; not ex-ante range EV or a decision-quality score.'}
loss=sorted([r for r in rows if r['result']<0],key=lambda r:r['result']);wins=sorted([r for r in rows if r['result']>0],key=lambda r:-r['result']);grossloss=-sum(r['result'] for r in loss);grosswin=sum(r['result']for r in wins)
for r in loss[:20]+wins[:10]:r['runoutDiagnostic']=equity(r)
result={'ref':D['ref'],'players':D['players'],'heroSeat':ME,'allinDefinition':'allin marks WBot reaching full-stack contribution before refunds, including uncalled shove attempts. finalRiskCategory uses final contributions after refunds and is mutually exclusive. No opponent-only event is included in WBot attempt count.','fileSha256':hashlib.sha256(F.read_bytes()).hexdigest(),'publicEventSha256':hashlib.sha256(json.dumps([(h['n'],h['events'],h['results'])for h in D['hands']],separators=(',',':')).encode()).hexdigest(),'hands':len(rows),'chips':sum(r['result']for r in rows),'bb100':sum(r['result']for r in rows)/20/len(rows)*100,'grossLoss':grossloss,'grossWin':grosswin,'losingHands':len(loss),'winningHands':len(wins),'zeroHands':sum(r['result']==0 for r in rows),'top5Loss':-sum(r['result']for r in loss[:5]),'top10Loss':-sum(r['result']for r in loss[:10]),'fullStackLosses':sum(r['result']==-2000 for r in rows),'groups':dict(groups),'largestLosses':loss[:20],'largestWins':wins[:10],'validationErrors':dict(errors),'rows':rows}
(OUT/f'Round{ROUND}_Audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
lines=[f'ROUND {ROUND} WBot RAW-HAND AUDIT','',f"Verified ref {D['ref']}; WBot seat {ME}; {len(rows)} hands; net {result['chips']:+,} chips = {result['bb100']:+.3f} bb/100 (rounds to {result['bb100']:+.1f}).",'Roster: '+', '.join(D['players']), 'Round metadata/table letter/uploaded version/timeouts are absent from this hand JSON.',
'Thus the score and ref are independently matched; displayed table letter and version need result metadata.','',f"Gross wins {grosswin:,}; gross losses {grossloss:,}; {len(wins)} winning / {len(loss)} losing / {result['zeroHands']} zero-result hands.",f"Full-stack losses: {result['fullStackLosses']}. Top5 losses {result['top5Loss']:,} ({result['top5Loss']/grossloss:.1%} of gross losses); top10 {result['top10Loss']:,} ({result['top10Loss']/grossloss:.1%}).", 'Losses as a proportion of NET loss are not a useful concentration statistic because wins offset losses.', '', 'SEGMENTS (descriptive net chips, not causal attribution)']
for k,g in sorted(groups.items()):lines.append(f"{k}: {g['hands']} hands, net {g['chips']:+,}; gross loss {g['grossLoss']:,}, gross win {g['grossWin']:,}")
lines.extend(['The allin/terminal all-in labels mark WBot pre-refund shove/call attempts,',
'including uncalled excess later returned. They do NOT mark opponent-only all-ins.',
'Use finalRisk categories for mutually exclusive actual full-stack exposure:',
'WBot final contribution 2,000; else any opponent final 2,000; else neither.'])
lines.extend(['','LARGEST LOSSES'])
for r in loss[:20]:
    lines.append(f"Hand {r['hand']} {r['position']} {' '.join(r['heroHole'])} / board {' '.join(r['board'])}: {r['result']:+}; {r['preflopLine']}; {r['terminalLine']}; winners {', '.join(r['winners'])}")
    lines.append('  Hero line: '+'; '.join(f"{a['street']} {a['action']} {a['amount']} (add {a['added']}, pot {a['potBefore']}, call {a['toCall']})" for a in r['heroActions']))
    q=r.get('runoutDiagnostic')
    if q:lines.append(f"  Hindsight all-in runout equity vs revealed contestants {q['equityVsRevealedFinalContestants']:.1%}; {q['mode']} ({q['runouts']}); NOT range EV.")
lines.extend(['','INTERPRETATION LIMITS','Both bad runouts and potentially costly decision patterns can coexist. A losing all-in',
'does not establish a leak; the revealed hand equity is hindsight, not what hero knew.',
'Review repeated raise/call lines and large pot commitments against observed opponent',
'ranges, with earlier actions and available information. Do not promote a new candidate',
'on this round alone. Runtime counts and tested deployed hash are still needed.',
'No playing source or strategy changed. Pot/refund totals and zero-sum results validated.'])
(OUT/f'Round{ROUND}_Audit.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for p in OUT.iterdir():p.read_bytes().decode('utf-8','strict')
print(json.dumps({k:result[k]for k in ('chips','bb100','grossLoss','grossWin','losingHands','winningHands','zeroHands','top5Loss','top10Loss','fullStackLosses','validationErrors')}))
