"""Small deterministic contract tests, no tournament simulations."""
import itertools
import math
from pathlib import Path
import random
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pokerbot.opponent_identity import JointIdentity
from sim import fieldbot as f
from pokerbot.opponent_evidence import hand_counts, round_identity, posterior
from pokerbot.context_model import ContextModel
from fetch_hands import complete_round, write_round
from pokerbot.behavior_profile import BehaviorProfile
from pokerbot.cold_observer import wrap_engine
from tools.validate_field import load


class SundayTests(unittest.TestCase):
    def test_bet_mixture_has_no_overlapping_probability_mass(self):
        for target in (.1,.5,.9):
            actual=sum(f.bet_probability((i+.5)/10000,target,.3) for i in range(10000))/10000
            self.assertAlmostEqual(actual,target,delta=.002)
        self.assertEqual(f.bet_probability(.1,0,.3),0)
        self.assertEqual(f.bet_probability(.1,1,.3),1)
    def test_raise_branch_preserves_exact_split_pot_value(self):
        # Any called bet/raise on this board splits. Raising cannot create extra
        # value by counting villain's existing 50-chip bet twice.
        m=load(ROOT/'sunday/v4_cold_accounting_bot.py','accounting_test')
        m.MODEL={'pop':{'base':{'river':[0,0,0,1]},'agg_ref':[.48,.92],
                       'ans_us':{'river':{'6':[0,1]}},'ans_oth':{'river':{'6':[0,1]}}}}
        a=m.Agent(params={'ans_cal':1,'max_sims':8});a.hard_end=float('inf')
        a.my_stack=200;a.ctx=(50,[],50)
        models=[(1,0,m.NC,(1,1,1,1),(1,1,1,1),False,50,200,100)]
        _,values=a.simulate(['2c','3d'],['As','Ks','Qs','Js','Ts'],models,[100],0,150,True,1)
        self.assertAlmostEqual(values[0],50.)
        old=load(ROOT/'sunday/v4_baseline.py','uncorrected_accounting_test');old.MODEL=m.MODEL
        before=old.Agent(params={'ans_cal':1,'max_sims':8});before.hard_end=float('inf')
        before.my_stack=200;before.ctx=(50,[],50)
        _,wrong=before.simulate(['2c','3d'],['As','Ks','Qs','Js','Ts'],models,[100],0,150,True,1)
        self.assertAlmostEqual(wrong[0],75.)
    def test_engine_neutral_adapter_does_not_change_actions_or_double_count(self):
        class Dummy:
            def act(self,state):return {'action':'check'}
        a=wrap_engine(Dummy)()
        state={'hand_number':1,'button':0,'seat':0,'stacks':[2000]*4}
        self.assertEqual(a.act(state),{'action':'check'})
        summary={'hand_number':1,'board':[],'history':[
            {'seat':1,'street':'preflop','action':'small_blind','amount':10},
            {'seat':2,'street':'preflop','action':'big_blind','amount':20},
            {'seat':3,'street':'preflop','action':'fold','amount':0},
            {'seat':0,'street':'preflop','action':'fold','amount':0}]}
        a.on_hand_end(summary);a.on_hand_end(summary)
        self.assertEqual(a.opponent_observer.profiles[1].total_seen,1)
    def test_cold_tags_and_new_policy_detection(self):
        p=BehaviorProfile()
        self.assertEqual(p.summary()['tags'],['insufficient_distinctive_evidence'])
        for _ in range(500):p.update({'hands':1,'vpip':1,'pfr':1})
        self.assertIn('loose_preflop',p.summary()['tags'])
        for _ in range(100):p.update({'hands':1})
        summary=p.summary()
        self.assertIn('vpip',summary['regime_change_suspected'])
        self.assertIn('tight_preflop',summary['tags'])
        self.assertNotIn('loose_preflop',summary['tags'])
    def test_context_actual_counts_not_identity_prior_counts(self):
        m=ContextModel({'nit':{'x/fold':90,'x/call':10}})
        p=m.predict(0,'x',('fold','call'),{'nit':1})
        self.assertEqual(p['observed_n'],0)
        self.assertGreater(p['probabilities']['fold'],.8)
        m.update(0,{'x/call':10})
        p=m.predict(0,'x',('fold','call'),{'nit':1})
        self.assertEqual(p['observed_n'],10)
        self.assertAlmostEqual(sum(p['probabilities'].values()),1.)

    def test_incomplete_download_is_not_complete(self):
        meta={'ref':'sunday/D/r001','hands':2,'version':1}
        d={'round':meta,'hands':[{'n':1,'events':[]}]}
        self.assertFalse(complete_round(d,meta))
        d['hands'].append({'n':2,'events':[]})
        self.assertTrue(complete_round(d,meta))
        import uuid
        path=ROOT/'sunday'/('round-test-'+uuid.uuid4().hex+'.json')
        try:
            write_round(str(path),d)
            import json
            self.assertEqual(json.loads(path.read_text()),d)
        finally:
            if path.exists():path.unlink()
    def test_stage_and_prior_mass_are_separate(self):
        self.assertEqual(round_identity('sunday/bucket/D/r001'),('sunday/bucket/D',1))
        p=posterior(8,10,prior=.5,prior_mass=20)
        self.assertEqual(p['observed_n'],10);self.assertEqual(p['prior_mass'],20)
        self.assertAlmostEqual(p['mean'],.6)

    def test_public_counters_incremental_and_actual_opportunities(self):
        h=dict(button=0,events=[['post',1,10],['post',2,20],['act',0,'raise',60],
               ['act',1,'fold',0],['act',2,'call',40],['board','flop',['2c','4d','8h']],
               ['act',2,'raise',80],['act',0,'call',80]])
        cs=hand_counts(h,['WBot','b','c','d'])
        self.assertEqual(cs['WBot']['flop/mw/vs_other/bet/2/opportunities'],1)
        self.assertEqual(cs['c']['vs_open/BB/call'],1)
        self.assertEqual(cs['WBot']['vpip'],1)

    def test_joint_marginals_match_bruteforce(self):
        model=JointIdentity(['a','b'],{})
        model.scores={0:[2.,1.,0.],1:[2.,-.5,0.]}
        out=model.posterior([0,1]);mass={};z=0.
        for assignment in itertools.product(range(3),repeat=2):
            names=[x for x in assignment if x<2]
            if len(names)!=len(set(names)):continue
            w=math.prod(math.exp(model.scores[s][i])*(.2 if i==2 else .4) for s,i in enumerate(assignment))
            z+=w
            for s,i in enumerate(assignment):mass[s,i]=mass.get((s,i),0)+w
        for s in out:
            self.assertAlmostEqual(sum(out[s].values()),1.)
            for i,name in enumerate(['a','b','_unknown']):self.assertAlmostEqual(out[s][name],mass.get((s,i),0)/z)
        self.assertLessEqual(sum(out[s]['a'] for s in out),1.)

    def test_unknown_accepts_unseen_fingerprint(self):
        m=JointIdentity(['a'],{'a':{'opens':{'50':1.}}})
        for _ in range(30):m.observe(0,'opens','123');m.finish_hand()
        self.assertGreater(m.posterior([0])[0]['_unknown'],.9)

    def test_response_and_bucket_contracts(self):
        for pf,pr in [(2,2),(-1,-1),(.5,.2),(.9,.6)]:
            p=f.normalize_response(pf,pr)
            self.assertAlmostEqual(sum(p),1.)
            self.assertTrue(all(0<=x<=1 for x in p))
        self.assertEqual(f.strength_bucket(7),'5')
        self.assertEqual(f.strength_bucket(6),'6')

    def test_reset_copies_frozen_state(self):
        warm={'x':[.2,.4]};f._OWN['bad']=[1];f._SKILL['a']=2
        f.reset_state(warm);f._POOL['x'].append(.9)
        self.assertEqual(warm['x'],[.2,.4]);self.assertEqual(f._OWN,{})
        self.assertEqual(f._SKILL,{})
        f.reset_state()

    def test_rejection_fallback_never_injects_forbidden_class(self):
        # Force every rejection to fail. Only level 3 is legal in fallback.
        original=f.level_street
        f.level_street=lambda a,b,bd: 3 if (a,b)==(0,1) else 0
        class R(random.Random):
            def random(self):return .999
            def sample(self,pop,k):return list(pop)[-k:]
            def choices(self,pop,weights,k):
                positive=[h for h,w in zip(pop,weights) if w>0]
                assert positive==[(0,1)]
                return [positive[0]]
        try:f.hand_strength_vs([48,49],[8,12,16,20,24],[0,0,0,1],1,R(1),m=1)
        finally:f.level_street=original


if __name__=='__main__':unittest.main()
