"""Regression checks for handover fixes; python -B tools/test_field_changes.py."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_field_model import collect, profile
from tools.validate_field import load
from sim.fieldbot import FieldBot, allocate_rates
from tools.call_equity import measure
from tools.field_gate import check


class Changes(unittest.TestCase):
    def test_gate_requires_strength_and_equity_evidence(self):
        report=dict(hashes={},baseline=dict(hands=20000,table_se=1,bb100=0,sd_bb100=-10,
                    field_frequencies={},strength={},call_equity={}),real_frequencies={},
                    real_strength={},real=dict(bb100=0,sd_bb100=-10,call_equity={}))
        self.assertFalse(check(report)['approved'])
        report['baseline']['strength']={'river/bet/7':{'n':30},'river/raise/6':{'n':30}}
        for row in (report['baseline'],report['real']):row['call_equity']={'n':40,'equity_sum':16}
        self.assertTrue(check(report)['approved'])
        report['baseline']['call_equity']['equity_sum']=28
        self.assertIn('big-call equity mismatch',check(report)['reasons'])

    def test_big_call_equity_uses_known_cards(self):
        h=dict(board=['2c','4d','7h','9s','Jc'],showdown={'0':'Pair','1':'Pair'},
               hole={'0':['As','Ah'],'1':['Ks','Kh']},events=[
                   ['board','river',['2c','4d','7h','9s','Jc']],
                   ['act',1,'raise',100],['act',0,'call',100]])
        result=measure([{'players':['kaiserbot','villain'],'hands':[h]}])
        self.assertEqual(result['n'],1)
        self.assertEqual(result['equity_sum'],1.)
        h['showdown']={}
        self.assertEqual(measure([{'players':['kaiserbot','villain'],'hands':[h]}]),{})
    def test_missing_strength_class_preserves_raise_rate(self):
        masses=[.1,.2,.3,0.]
        rates=allocate_rates(masses,[.05,.1,.15,.7],.13)
        self.assertAlmostEqual(sum(m*r for m,r in zip(masses,rates)),.13,places=6)
        self.assertEqual(rates[3],0)
    def test_incremental_calls_preserve_pot_bucket(self):
        # BB calls 40 more after posting 20. Correct flop pot is 130, not 110.
        h = dict(n=1, button=0, board=['2c','7d','Jh'], hole={}, showdown={},
                 events=[['post',1,10],['post',2,20],['act',0,'raise',60],
                         ['act',1,'fold',0],['act',2,'call',40],
                         ['board','flop',['2c','7d','Jh']],['act',2,'raise',80],
                         ['act',0,'fold',0]])
        c,_=collect(documents=[dict(players=['a','b','c','d'],hands=[h])])
        self.assertEqual(c['a']['post.flop.vs.2|fold'],1)
        self.assertEqual(c['a']['post.flop.vs.3|fold'],0)

    def test_strength_counts_and_size_choice(self):
        p=profile({})
        b=FieldBot('test',seed=1,profile=p)
        self.assertEqual(b._raise_to(dict(legal_actions=['raise'],min_raise_to=20,max_raise_to=2000),1200),
                         dict(action='raise',amount=1200))
        q=dict(sz={'0.5':.5,'3.0':.5},strength={'bet':{'2':[.4,.3,.25,.05],'7':[.01,.01,.08,.9]}})
        strong=sum(b._size_for_level(q,3)==3 for _ in range(2000))
        weak=sum(b._size_for_level(q,0)==3 for _ in range(2000))
        self.assertGreater(strong,1700)
        self.assertLess(weak,300)

    def test_small_particle_ranges_are_kept(self):
        b=FieldBot('test',profile=profile({}))
        b.parts=[(0,1),(2,3),(4,5)]
        b._keep([.1,.5,.9],0,.2)
        self.assertEqual(b.parts,[(0,1)])

    def test_candidate_parameters_and_terminal_check(self):
        m=load(ROOT/'candidate/engine.py','test_candidate')
        a=m.Agent(seed=1)
        self.assertGreaterEqual(a.P['bet_margin'],0)
        self.assertGreaterEqual(a.P['raise_margin'],0)
        self.assertLess(a.P['o_btn'],.5)
        self.assertLess(a.P['eq_3b'],.52)
        # Stub only MC to isolate decision comparison: a losing bet must not
        # beat a better check because of a bonus or river realization haircut.
        a.opp_models=lambda s,me:[(1,0,10,(1,)*4,(1,)*4,False,0,2000,100)]
        a.simulate=lambda *args:(.5,[45.]*len(args[3]))
        a.budget=lambda:.001
        s=dict(seat=0,button=0,pot=100,to_call=0,bets=[0,0],stacks=[1900,1900],
               street='river',min_raise_to=20,max_raise_to=1900,
               legal_actions=['check','raise'],hole_cards=['Ac','Kd'],board=['2c','4s','6d','9c','Jh'])
        self.assertEqual(a.postflop(s),{'action':'check'})


if __name__=='__main__':unittest.main()
