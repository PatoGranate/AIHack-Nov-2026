"""Isolated policy-branch check with fixed simulation outputs, not strength test."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('review_v7',ROOT/'tools/cands/v7.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
a=m.Agent()
# Postflop order for button 6: seat 0 -> hero seat 1 -> seat 2.
# Aggressive seat 0 already checked; remaining seat 2 is passive.
models=[(0,0,1326,(1,1,1,1),(1,1,1,1),False,0,1900,100),
        (2,0,1326,(1,1,1,1),(1,1,1,1),False,0,1900,100)]
a.opp_models=lambda state,me:models
a.af=lambda seat:.8 if seat==0 else .1
a.simulate=lambda hole,board,models,cands,*args:(.9,[500.0+i for i in range(len(cands))])
s={'seat':1,'button':6,'street':'turn','pot':300,'to_call':0,'bets':[0]*7,
   'stacks':[1900,1900,1900,2000,2000,2000,2000],
   'folded':[False,False,False,True,True,True,True],
   'hole_cards':['As','Ah'],'board':['Ac','Kd','7s','2h'],
   'legal_actions':['check','raise'],'min_raise_to':20,'max_raise_to':1900,
   'history':[{'seat':0,'street':'turn','action':'check','amount':0}]}
with_trap=a.postflop(s)
m.P['q_trap']=0
without_trap=a.postflop(s)
assert with_trap['action']=='check' and without_trap['action']=='raise'
out={'trap_on':with_trap,'trap_off':without_trap,
     'aggressive_opponent':0,'already_checked':True,'remaining_opponent_af':.1,
     'note':'Stubbed equity/EV isolates branch; no measured profitability claim.'}
Path(__file__).with_name('trap_opportunity_results.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
