"""Reproducible diagnostic, not a production runtime gate. Run from PokerBot.
Six pairs x 1000 hands = 12000 table-hands. Fixed 32 MC samples per postflop
decision, both builds; per-decision seeded RNGs for hero and all seven clones.
"""
import collections
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import arena

BASE = 'submissions/G_v7_final/bot.py'
CAND = 'tools/cands/sunday_early_adapt_v1.py'
NAMES = ['ResonanceQt', 'AnkerBatteries', 'Chinesepeoplecanfly', 'GamesGone', 'Poke', 'Anton', 'YSLTWIZZY']
OPPS = ['tools/opponents/real/r_' + n + '.py' for n in NAMES]
SEEDS = list(range(85100000, 85100006))
HANDS = 1000
def window(h):
    return '1-50' if h <= 50 else '51-200' if h <= 200 else '201-1000'
def decision_seed(seed, state):
    key = (seed, state['seat'], state['hand_number'], state['street'], len(state['history']))
    return int.from_bytes(hashlib.sha256(repr(key).encode()).digest()[:8], 'big')

def hero_class(path, seed):
    src = (ROOT / path).read_text(encoding='utf-8')
    old = 'if sims >= P["max_sims"] or now > hard or (now > t_end and sims >= 8):'
    assert src.count(old) == 1
    src = src.replace(old, 'if sims >= 32:')
    module = types.ModuleType('fixed_' + path.split('/')[-1]); exec(compile(src, str(ROOT / path), 'exec'), module.__dict__)
    parent = module.Agent
    class Diagnostic(parent):
        def __init__(self):
            super().__init__()
            self.window_chips = collections.Counter()
            self.snapshots = {}
            self.max_posterior_jump = collections.Counter()
            self.action_counts = collections.Counter()
        def budget(self):
            return .001
        def act(self, state):
            self.rng.seed(decision_seed(seed, state))
            out = super().act(state)
            self.action_counts[window(state['hand_number']) + '|' + state['street'] + '|' + out['action']] += 1
            return out
        def on_hand_end(self, summary):
            h = summary['hand_number']; w = window(h)
            before = {j:self.ftb(j) for j in range(8) if j != self.seat}
            super().on_hand_end(summary)
            self.window_chips[w] += summary['stacks'][self.seat] - self.start
            for j in before:
                self.max_posterior_jump[w] = max(self.max_posterior_jump[w], abs(self.ftb(j)-before[j]))
            if h in (50,200,1000):
                self.snapshots[h] = {j:dict(faced=self.S(j).faced, folds=self.S(j).ffold, posterior=self.ftb(j)) for j in before}
    return Diagnostic

def clone_class(path, seed):
    parent = arena.load(path)
    class Seeded(parent):
        def act(self, state):
            self.rng.seed(decision_seed(seed, state))
            return super().act(state)
    return Seeded


def run_pilot():
    rows = []
    for t, seed in enumerate(SEEDS):
        order=OPPS.copy(); random.Random(seed).shuffle(order)
        pair={}
        for label, path in [('candidate',CAND),('baseline',BASE)]:
            seats=[clone_class(p,seed) for p in order]; seats.insert(t,hero_class(path,seed))
            players=[arena.LocalPlayer(a) for a in seats]
            result=arena.FixedHandsTable(players,hands=HANDS,config={'betting':'no_limit','raise_cap':0},seed=seed).play()
            a=players[t].agent
            pair[label]={'window_chips':dict(a.window_chips),'snapshots':a.snapshots,
                'max_posterior_jump':dict(a.max_posterior_jump),'action_counts':dict(a.action_counts),
                'all_seat_errors':sum(p.stats.errors for p in players), 'chips':result['chips'][t]}
        rows.append({'seed':seed,'hero_seat':t,'opponents':order,**pair})
        print('completed pair',seed,flush=True)
    
    effects={}
    for w,n in [('1-50',50),('51-200',150),('201-1000',800),('all',1000)]:
        def chips(r,k): return r[k]['chips'] if w=='all' else r[k]['window_chips'].get(w,0)
        c=[chips(r,'candidate')/20/n*100 for r in rows];b=[chips(r,'baseline')/20/n*100 for r in rows]
        d=[x-y for x,y in zip(c,b)]
        effects[w]={'candidate_bb100':statistics.mean(c),'baseline_bb100':statistics.mean(b),
            'paired_diff_bb100':statistics.mean(d),'paired_se_bb100':statistics.stdev(d)/math.sqrt(len(d)), 'n_pairs':len(d)}
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [BASE,CAND]+OPPS}
    out=ROOT/'ExternalAnalysis/Sunday_Early_Adaptation_Pilot.md'
    out.write_text('# Sunday early adaptation pilot\n\nOne change: per-seat fold-to-bet prior weight 8 -> 4, mean stays 0.60. '
        'This changes learning speed, not a forced exploitation rule. Every round starts with a fresh Agent; public-action statistics persist across its 1000 hands. '
        'Only completed-hand public actions update these statistics.\n\nSandbox only: same fixed 32 MC samples and per-decision RNG seeding in both builds and all clones; '
        'budget() override .001 prevents accumulated wallclock spending from changing the strategy diagnostic. '
        'The production runtime and bank are NOT certified by this modified harness. Full histories/decisions can diverge after a strategy difference, '
        'so paired cards reduce noise without giving counterfactual identical histories.\n\n'
        'The seven profiles are old public-frequency clones, not opponent source; Poke clone comment (VPIP22/PFR13, no limps) disagrees with latest pooled report (VPIP34/PFR16,10% limps). '
        'This particularly limits early exploit inference. No name-based behavior enters the hero policy.\n\n'
        'Run: `C:/Anaconda/Anaconda2/python.exe tools/sunday_early_adapt_pilot.py` from PokerBot. '
        'Seeds 85100000-85100005, six pairs x1000 =12000 total table-hands.\n\n## Window results\n\n```json\n'+json.dumps(effects,indent=2)+
        '\n```\n\n## Inputs, opportunity denominators, posterior snapshots and stability\n\nSnapshot faced/fold counts are cumulative per seat at hand50/200/1000; subtract consecutive snapshots to obtain window denominators. '
        'Max posterior jump is the largest per-seat completed-hand update in a window.\n\n```json\n'+json.dumps({'hashes':hashes,'rows':rows},indent=2)+'\n```\n',encoding='utf-8')
    print(json.dumps(effects,indent=2),flush=True)


if __name__ == "__main__":
    run_pilot()
