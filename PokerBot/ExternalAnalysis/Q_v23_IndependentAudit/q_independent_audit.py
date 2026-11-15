"""Public-action-only Q audit; no policy edits, replay or simulation."""
import ast
import collections
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
Q=ROOT/'submissions/Q_P_x4/bot.py'
assert hashlib.sha256(Q.read_bytes()).hexdigest()=='8233d8fa67ed0e8ff3fe10dfdf fdcf09feb56ba6bdc60883a7455b9cb38109b1'.replace(' ','')
files=sorted((ROOT/'Hand_data/SundayRaw').glob('sunday_s1_r*.json'))[:16]
events=[];opportunities=[];inputs=[]
for p in files:
 d=json.loads(p.read_text(encoding='utf-8'));names=d['players'];n=len(names)
 inputs.append({'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'ref':d['ref'],'hands':len(d['hands'])})
 for hand in d['hands']:
  bets=[0]*n;contrib=[0]*n;folded=[False]*n;nr=0;opener=tb=None;three_target=None;pending=None;seen_opener_response=False
  for index,e in enumerate(hand['events']):
   if e[0]=='board':break
   if e[0]=='post':bets[e[1]]+=e[2];contrib[e[1]]+=e[2];continue
   if e[0]!='act':continue
   _,s,a,amt=e;cur=max(bets);tc=cur-bets[s];remaining=hand['start_stacks'][s]-contrib[s]
   if nr==2 and s==opener and not seen_opener_response and a in ('fold','call','raise'):
    seen_opener_response=True
    extras=[j for j in range(n) if j not in (opener,tb) and not folded[j] and bets[j]>=cur]
    behind=[j for j in range(n) if j not in (opener,tb) and not folded[j] and bets[j]<cur]
    opportunities.append({'round':d['ref'],'hand':hand['n'],'opener':names[opener],'threebettor':names[tb],
     'action':a,'threebet_target':cur,'pot':sum(contrib),'remaining':remaining,'extra_matched_callers':len(extras),
     'other_live_behind':len(behind),'Q_public_filter':cur<600 and not extras and remaining>tc})
   if pending is not None and pending['response'] is None and s==pending['tb_seat'] and a in ('fold','call','raise') and tc>0 and remaining>0:
    pending.update(response=a,response_raise_count=nr,responds_without_intervening_raise=nr==3,
     response_to_call=tc,response_amount=amt,folded=a=='fold')
   if a=='raise':
    if nr==0:opener=s
    elif nr==1:tb=s;three_target=amt
    elif nr==2:
     behind=[j for j in range(n) if j not in (s,tb) and not folded[j] and bets[j]<cur]
     extras=[j for j in range(n) if j not in (s,tb) and not folded[j] and bets[j]>=cur]
     pending={'round':d['ref'],'hand':hand['n'],'event_index':index,'opener':names[opener],
      'threebettor':names[tb],'fourbettor':names[s],'tb_seat':tb,'target':amt,'threebet_target':three_target,
      'strict_allin':amt>=bets[s]+remaining,'broad_ge600':amt>=600,'opener_fourbet':s==opener,
      'other_live_behind':len(behind),'extra_matched_callers':len(extras),'pot_before':sum(contrib),
      'Q_public_filter':s==opener and cur<600 and not extras,'fourbettor_net_chips':hand['results'][s],
      'response':None,'folded':None}
     events.append(pending)
    nr+=1;add=amt-bets[s];bets[s]=amt;contrib[s]+=add
   elif a=='call':bets[s]+=amt;contrib[s]+=amt
   elif a=='fold':folded[s]=True

def stat(rows):
 n=len(rows);f=sum(x['folded'] for x in rows);rate=f/n if n else None
 if n:
  z=1.96;den=1+z*z/n;mid=(rate+z*z/(2*n))/den;rad=z*math.sqrt(rate*(1-rate)/n+z*z/(4*n*n))/den;ci=[mid-rad,mid+rad]
 else:ci=None
 return {'responses':n,'folds':f,'calls':sum(x['response']=='call' for x in rows),'raises':sum(x['response']=='raise' for x in rows),'fold_rate':rate,'Wilson95':ci}
eligible=[x for x in events if x['response'] is not None and x['responds_without_intervening_raise']]
definitions={'all_fourbets':lambda x:True,'ge600':lambda x:x['broad_ge600'],
 'strict_allin':lambda x:x['strict_allin'],'ge600_non_allin':lambda x:x['broad_ge600'] and not x['strict_allin'],
 'ge600_Q_filter':lambda x:x['broad_ge600'] and x['Q_public_filter'],
 'strict_Q_filter':lambda x:x['strict_allin'] and x['Q_public_filter']}
summary={}
for definition,pred in definitions.items():
 rows=[x for x in eligible if pred(x)];per={}
 for name in sorted({x['threebettor'] for x in rows}):per[name]=stat([x for x in rows if x['threebettor']==name])
 anton=[x for x in rows if x['threebettor']=='Anton']
 summary[definition]={'all_teams':per,'Anton':stat(anton),
  'Anton_opener_WBot':stat([x for x in anton if x['opener']=='WBot']),
  'Anton_opener_other':stat([x for x in anton if x['opener']!='WBot']),
  'Anton_fourbettor_WBot':stat([x for x in anton if x['fourbettor']=='WBot']),
  'Anton_fourbettor_other':stat([x for x in anton if x['fourbettor']!='WBot']),
  'Anton_no_other_live':stat([x for x in anton if x['other_live_behind']==0]),
  'Anton_other_live':stat([x for x in anton if x['other_live_behind']>0])}
opp_summary={}
for label,pred in [('Anton_reraises_WBot',lambda x:x['opener']=='WBot' and x['threebettor']=='Anton'),
                   ('Anton_reraises_others',lambda x:x['opener']!='WBot' and x['threebettor']=='Anton')]:
 rows=[x for x in opportunities if pred(x)];flt=[x for x in rows if x['Q_public_filter']]
 opp_summary[label]={'observed_opener_responses':len(rows),'response_actions':dict(collections.Counter(x['action'] for x in rows)),
  'Q_public_filter_opportunities':len(flt),'Q_filter_actions':dict(collections.Counter(x['action'] for x in flt))}

# Source-executed online learner fixture: >=600 is learned even if not all-in.
sp=importlib.util.spec_from_file_location('audited_Q',Q);M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
def hist(target):
 return [{'seat':s,'street':'preflop','action':a,'amount':v} for s,a,v in [(0,'raise',60),(1,'raise',180),(0,'raise',target),(1,'fold',0)]]
learner={}
for target in (599,600,1999,2000):
 a=M.Agent();a.seat=0;a._pfx_learn(hist(target));learner[str(target)]=a.pfx.get(1)
assert learner['599'][2]==0 and all(learner[str(x)][2]==1 for x in (600,1999,2000))
# Multiway arithmetic fixture uses exact source assignment block with controlled inputs.
tree=ast.parse(Q.read_text(encoding='utf-8'));pf=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='preflop')
branch=next(n for n in ast.walk(pf) if isinstance(n,ast.If) and 'nr == 2' in ast.unparse(n.test) and 'cur < 600' in ast.unparse(n.test))
assigns=[n for n in branch.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('a_in','final','pfx','ev_jam') for t in n.targets)]
code=compile(ast.Module(body=assigns,type_ignores=[]),str(Q),'exec')
math_cases=[]
for nb in (0,1,2):
 env={'eff':2000,'bets':[60,180,60,0],'me':0,'raiser':1,'pot':330,'pfj':.92,'nbehind':nb,'ec':.25};exec(code,{'__builtins__':{}},env)
 math_cases.append({k:env[k] for k in ('nbehind','a_in','final','pfx','ev_jam')})
a=M.Agent()
for _ in range(4):a._id_obs(1,'opens','50')
a._id_post(1)
ll=a.idll[1]
lp={b:M.ID_T*v+(math.log(.8/len(M.IDLIB)) if b!='_pop' else math.log(.2)) for b,v in ll.items()}
mx=max(lp.values());ex={b:math.exp(v-mx) for b,v in lp.items()};z=sum(ex.values())
id_fixture={'reported':a.post[1],'full_posterior':{b:v/z for b,v in ex.items()},'f4_prior':a.f4(1)}
toy=(.92*.96*330+.08*.96*(.25*4090-1940)+.92*.04*(.10*4210-1940)+.08*.04*(.08*6030-1940))
payload={'source_sha256':hashlib.sha256(Q.read_bytes()).hexdigest(),'inputs':inputs,'rounds':len(files),'hands':sum(x['hands'] for x in inputs),
 'definition_note':'Fourbet is third preflop raise. Strict all-in means raise-to equals prior street bet plus publicly remaining stack. Responses exclude intervening fifth raises for Q-compatible conditional rate. No hole cards used.',
 'summary':summary,'opportunities':opp_summary,'fourbet_events':events,'opener_response_events':opportunities,
 'learner_fixture':learner,'source_EV_math_cases':math_cases,'ambiguous_identity_fixture':id_fixture,
 'illustrative_multiway_ledger_fixture':{'ledger_ev':toy,'Q_ev':math_cases[1]['ev_jam'],'assumption_note':'Illustrative equity inputs .25/.10/.08, not empirical equity estimates'}}
out=ROOT/'ExternalAnalysis/AgentReports/Q_Independent_Audit';out.mkdir(parents=True,exist_ok=True)
(out/'public_counts.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'hands':payload['hands'],'summary':{k:v['Anton'] for k,v in summary.items()},'opportunities':opp_summary,
 'vs_WBot':{k:v['Anton_fourbettor_WBot'] for k,v in summary.items()},'math':math_cases,'learner':learner},indent=2))
