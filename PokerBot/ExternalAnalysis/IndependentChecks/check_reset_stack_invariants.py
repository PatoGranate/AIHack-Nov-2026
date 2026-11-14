"""Independent reachable-state checks; no playing code edits."""
from pathlib import Path
import sys,random,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'kit'))
from engine import FixedHandsTable

counts={'states':0,'postflop_states':0,'facing_allin':0,'sp_call_true':0,'candidate_below_cap':0}
class Player:
    def __init__(self,seed):self.rng=random.Random(seed)
    def start_table(self,seat,info):self.start=info['starting_stack']
    def hand_end(self,summary):pass
    def close(self):pass
    def act(self,s):
        counts['states']+=1
        me=s['seat'];hc=self.start-s['stacks'][me];tgt=hc+s['to_call']
        assert tgt<=self.start
        live=[i for i in range(len(s['stacks'])) if not s['folded'][i] and i!=me]
        if s['street']!='preflop':
            counts['postflop_states']+=1
            allin=[j for j in live if s['stacks'][j]==0]
            if allin and s['to_call']>0:counts['facing_allin']+=1
            sp=any(self.start-s['stacks'][j]<tgt for j in allin) and s['to_call']>0
            counts['sp_call_true']+=int(sp);assert not sp
            if 'raise' in s['legal_actions']:
                for j in live:
                    cap=s['bets'][j]+s['stacks'][j]
                    if cap<s['max_raise_to']:counts['candidate_below_cap']+=1
                    assert cap>=s['max_raise_to'],(s,j)
        legal=s['legal_actions'];r=self.rng.random()
        if 'raise' in legal and r<.25:
            lo=s['min_raise_to'];hi=s['max_raise_to']
            return {'action':'raise','amount':hi if r<.07 else min(hi,lo+int((hi-lo)*self.rng.random()*.15))}
        if s['to_call']>0:return {'action':'call' if r<.75 else 'fold'}
        return {'action':'check'}

for seed in range(12):
    players=[Player(seed*100+j) for j in range(7)]
    result=FixedHandsTable(players,hands=250,seed=170001+seed).play()
    assert sum(result['chips'])==0
source=ROOT/'tools/src_bot.py'
counts.update(hands=3000,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
target=Path(__file__).with_name('reset_stack_invariants_results.json')
target.write_text(json.dumps(counts,indent=2))
print(json.dumps(counts))
