"""Replay two visible decisions through their statistical clone policies."""
import sys,json,importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/opponents'))
def load(file,name):
 sp=importlib.util.spec_from_file_location(name,ROOT/'tools/opponents/real'/file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
data=json.loads((ROOT/'Hand_data/ExternalData_OtherBots/saturday_practice_r016.json').read_text(encoding='utf-8'))
h=next(h for h in data['hands'] if h['n']==893)
names=data['players'];total=[0]*len(names);bets=[0]*len(names);folded=[False]*len(names);board=[];street='preflop';hist=[];results=[]
for e in h['events']:
 if e[0]=='board':street=e[1];board=e[2];bets=[0]*len(names);continue
 if e[0]=='post':
  _,seat,x=e;total[seat]+=x;bets[seat]+=x
  hist.append({'seat':seat,'street':'preflop','action':'small_blind' if x==10 else 'big_blind','amount':x});continue
 if e[0]!='act':continue
 _,seat,action,x=e
 if (names[seat],street,action) in [('Gherkers','flop','call'),('Lehman Brothers','river','call')]:
  stack=2000-total[seat];current=max(bets);tc=min(current-bets[seat],stack)
  canraise=any(not folded[j] and total[j]<2000 for j in range(len(names)) if j!=seat) and bets[seat]+stack>current
  state={'hole_cards':h['hole'][str(seat)],'board':board,'big_blind':20,'street':street,'seat':seat,'button':h['button'],'stacks':[2000-t for t in total],'bets':list(bets),'folded':list(folded),'pot':sum(total),'to_call':tc,'history':list(hist),'legal_actions':['fold','call']+(['raise'] if canraise else []),'min_raise_to':current+max(20,current) if canraise else None,'max_raise_to':bets[seat]+stack if canraise else None}
  clonefile='r_Gherkers.py' if names[seat]=='Gherkers' else 'r_LehmanBrothers.py'
  mod=load(clonefile,'gap_'+str(seat));clone=mod.Agent()
  got=clone.act(state)
  results.append({'name':names[seat],'hand':893,'street':street,'actual_action':action,'actual_added':x,'clone_action':got,'state':state,'source_clone':clonefile})
 if action=='raise':total[seat]+=x-bets[seat];bets[seat]=x
 elif action=='call':total[seat]+=x;bets[seat]+=x
 elif action=='fold':folded[seat]=True
 hist.append({'seat':seat,'street':street,'action':action,'amount':x})
assert len(results)==2
assert all(r['clone_action']['action']=='fold' for r in results)
(HERE/'external_clone_replay_results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in r.items() if k!='state'} for r in results]))
