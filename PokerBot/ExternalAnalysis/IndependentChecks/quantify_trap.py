"""Two cheap sequential v7 tables; records trigger reachability, not causal loss."""
import sys,json,hashlib,shutil,importlib.util,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'kit'));sys.path.insert(0,str(ROOT/'tools/opponents'))
from engine import FixedHandsTable
from engine.players import LocalPlayer
src=ROOT/'tools/cands/v7.py';snapshot=HERE/'trap_v7_snapshot.py'
shutil.copyfile(src,snapshot)
def load(p,name):
    sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
bot=load(snapshot,'trap_v7')
opps=['a_maniac.py','a_lag.py','a_station2.py','a_maniac.py','a_lag.py','a_tag.py']
mods=[load(ROOT/'tools/opponents'/p,'trap_opp_'+str(i)) for i,p in enumerate(opps)]
class Seeded(LocalPlayer):
    def __init__(self,cls,seed):super().__init__(cls);self.seed=seed
    def start_table(self,seat,info):
        super().start_table(seat,info)
        if hasattr(self.agent,'rng'):self.agent.rng.seed(self.seed)
class Hero(Seeded):
    def __init__(self,seed):super().__init__(bot.Agent,seed);self.rows=[];self.post=0
    def start_table(self,seat,info):
        super().start_table(seat,info);original=self.agent.simulate
        def capture(*args,**kwargs):
            value=original(*args,**kwargs);self.capture=(args,value);return value
        self.agent.simulate=capture
    def act(self,s):
        self.capture=None;result=super().act(s)
        if s['street']=='preflop':return result
        self.post+=1
        if self.capture is None:return result
        args,(equity,evs)=self.capture;models=args[2];cands=args[3]
        order=lambda j:(j-s['button']-1)%len(s['stacks'])
        ip=all(order(s['seat'])>order(m[0]) for m in models)
        qual=[m[0] for m in models if self.agent.af(m[0])>=bot.P['q_trap_af'] and not m[5]]
        triggered=(s['to_call']==0 and bot.P['q_trap'] and not ip and s['street']!='river' and equity>=bot.P['q_trap_eq'] and bool(qual))
        if not triggered:return result
        acted={h['seat'] for h in s['history'] if h['street']==s['street']}
        # With no bet to call, a prior actor has checked; no action has reopened.
        remaining=[j for j in qual if order(j)>order(s['seat']) and j not in acted]
        subset=not remaining and all(j in acted for j in qual)
        baseline=equity*s['pot']*(bot.P['chk_ip'] if ip else bot.P['chk_oop'])
        best_raw=max(evs) if evs else None
        row={'hand':s['hand_number'],'street':s['street'],'hole':s['hole_cards'],'board':s['board'],'pot':s['pot'],'equity':equity,'action':result,'qualifying':qual,'remaining_qualifying':remaining,'all_qualifiers_acted_subset':subset,'af':{str(m[0]):self.agent.af(m[0]) for m in models},'baseline':baseline,'best_bet_ev':best_raw,'model_gap_raw':best_raw-baseline if best_raw is not None else None,'model_gap_with_bonus':best_raw-bot.P['bet_margin']*s['pot']-baseline if best_raw is not None else None,'history':s['history']}
        self.rows.append(row);return result
allround=[]
for index,seed in enumerate([717171,717172]):
    hero=Hero(seed*31)
    players=[Seeded(m.Agent,seed*31+i+1) for i,m in enumerate(mods)]
    # Middle seat lets prior-actor and remaining-actor situations both arise.
    hero_seat=2+index;players.insert(hero_seat,hero)
    start=time.perf_counter();res=FixedHandsTable(players,hands=1000,seed=seed).play()
    assert sum(res['chips'])==0
    errors=[p.stats.as_dict() for p in players]
    subset=[r for r in hero.rows if r['all_qualifiers_acted_subset']]
    row={'seed':seed,'hero_seat':hero_seat,'seconds':time.perf_counter()-start,'hands':1000,'hero_chips':res['chips'][hero_seat],'postflop_decisions':hero.post,'trigger_count':len(hero.rows),'subset_count':len(subset),'positive_gap_subset_count':sum(r['model_gap_with_bonus'] is not None and r['model_gap_with_bonus']>0 for r in subset),'subset_raw_gap_sum':sum(r['model_gap_raw'] or 0 for r in subset),'subset_bonus_gap_sum':sum(r['model_gap_with_bonus'] or 0 for r in subset),'all_seat_stats':errors,'triggers':hero.rows}
    allround.append(row);print(json.dumps({k:v for k,v in row.items() if k not in ('all_seat_stats','triggers')}),flush=True)
out={'source':'tools/cands/v7.py','sha256':hashlib.sha256(snapshot.read_bytes()).hexdigest(),'opponent_sources':opps,'rounds':allround,'warning':'Observed opportunity counts and biased model-value gaps, not realised counterfactual loss. LocalPlayer deadlines unenforced; wall-clock sampling varies under load.'}
(HERE/'trap_frequency_results.json').write_text(json.dumps(out,indent=2))
