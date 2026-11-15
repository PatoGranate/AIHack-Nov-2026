"""Bounded independent official-engine Pablo v4 review. No lab/network code.
Run from PokerBot: python tools/independent_pablo/run_review.py
"""
import ast
import collections
import difflib
import hashlib
import json
import math
from pathlib import Path
import random
import statistics
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import sunday_early_adapt_pilot as H
from engine.players import SubprocessPlayer

G='submissions/G_v7_final/bot.py'
PABLO='tools/independent_pablo/bot.py'
OPPS=['tools/independent_ctx_pr11/opponents/sunday_v2/r_'+n+'.py' for n in H.NAMES]
def agent(path,seed):
    src=(ROOT/path).read_text(encoding='utf-8')
    endings=['if sims >= P["max_sims"] or now > hard or (now > t_end and sims >= 8):',
        'if sims >= self.P["max_sims"] or now > hard or (now > t_end and sims >= 8):']
    old=next(x for x in endings if x in src);assert src.count(old)==1
    src=src.replace(old,'if sims >= 32:').replace('DEBUG = False','DEBUG = True')
    m=types.ModuleType('diagnostic_'+path.replace('/','_'));m.__file__=str(ROOT/path);exec(compile(src,m.__file__,'exec'),m.__dict__)
    class Fixed(m.Agent):
        def __init__(self):
            super().__init__();self.window_chips=collections.Counter();self.actions=collections.Counter()
        def budget(self):return .001
        def act(self,state):
            self.rng.seed(H.decision_seed(seed,state));out=super().act(state)
            self.actions[H.window(state['hand_number'])+'|'+state['street']+'|'+out['action']]+=1
            return out
        def on_hand_end(self,summary):
            super().on_hand_end(summary)
            self.window_chips[H.window(summary['hand_number'])]+=summary['stacks'][self.seat]-self.start
    return Fixed

def play(path,seed,hero,hands,record=False):
    order=OPPS.copy();random.Random(seed).shuffle(order)
    seats=[H.clone_class(p,seed) for p in order];seats.insert(hero,agent(path,seed))
    players=[H.arena.LocalPlayer(a) for a in seats]
    r=H.arena.FixedHandsTable(players,hands=hands,config={'betting':'no_limit','raise_cap':0},seed=seed,record=record).play()
    a=players[hero].agent
    return r,{'chips':r['chips'][hero],'window_chips':dict(a.window_chips),'actions':dict(a.actions),
        'all_seat_errors':sum(p.stats.errors for p in players),'hero_error_samples':players[hero].stats.error_samples}

qa={}
for path in [G,PABLO]:
    a,sa=play(path,87100000,0,20,True);b,sb=play(path,87100000,0,20,True)
    assert a==b and sa==sb and sa['all_seat_errors']==0
    qa[path]={'full_trajectory_and_result_match':True,'result_log_sha256':hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest()}
print('A-v-A PASS before pilot',flush=True)

# Official subprocess protocol smoke on exact, unmodified export bytes. Not a full runtime gate.
players=[H.arena.LocalPlayer(H.clone_class(p,87100000)) for p in OPPS]
sub=SubprocessPlayer(str(ROOT/PABLO),timeout_ms=25.0,bank_ms=10000)
players.insert(0,sub)
try:
    smoke=H.arena.FixedHandsTable(players,hands=20,config={'betting':'no_limit','raise_cap':0},seed=87100000).play()
    smoke={'hands':smoke['hands'],'hero_chips':smoke['chips'][0],'stats':sub.stats.as_dict()}
finally:
    for p in players:p.close()
print('protocol smoke',smoke,flush=True)

rows=[]
for t,seed in enumerate(range(87100000,87100005)):
    _,c=play(PABLO,seed,t,1000);_,b=play(G,seed,t,1000)
    rows.append({'seed':seed,'hero_seat':t,'pablo_v4':c,'G':b})
    print('pair',seed,'diff',(c['chips']-b['chips'])/200,flush=True)
effects={}
for w,n in [('1-50',50),('51-200',150),('201-1000',800),('all',1000)]:
    def chips(r,k):return r[k]['chips'] if w=='all' else r[k]['window_chips'].get(w,0)
    cs=[chips(r,'pablo_v4')/20/n*100 for r in rows];bs=[chips(r,'G')/20/n*100 for r in rows];ds=[a-b for a,b in zip(cs,bs)]
    effects[w]={'pablo_bb100':statistics.mean(cs),'G_bb100':statistics.mean(bs),'diff_bb100':statistics.mean(ds),
        'paired_se':statistics.stdev(ds)/math.sqrt(len(ds)),'pair_diffs':ds}

def config(p):
    src=(ROOT/p).read_text(encoding='utf-8');tr=ast.parse(src);out={}
    for n in tr.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('P','DEFAULT_PARAMS') for t in n.targets):
            out.update(ast.literal_eval(n.value))
        elif isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='P.update':
            out.update(ast.literal_eval(n.value.args[0]))
    return out
files=[PABLO,'tools/independent_pablo/bot_gen7.py','tools/independent_pablo/bot_v31.py','tools/independent_pablo/bot_v32.py',
    'tools/independent_pablo/pokerbot/v2.py','tools/independent_pablo/pokerbot/strategy.py','tools/independent_pablo/candidate/engine.py',
    'tools/independent_pablo/candidate/export.py','tools/independent_pablo/tools/bench2.py','tools/independent_pablo/data/v4_params.json',
    G,'submissions/I_v9_25ms/bot.py','submissions/N_v10_tuned/bot.py',
    'tools/independent_pablo/run_review.py','tools/sunday_early_adapt_pilot.py']+OPPS
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
inventory={}
for p in files[:7]:
    pc=config(p);gc=config(G)
    inventory[p]={'params':pc,'config_diff_vs_G':{k:[gc.get(k),pc.get(k)] for k in sorted(set(pc)|set(gc)) if gc.get(k)!=pc.get(k)}}
data={'branch_commit':'24653c92256ad1b7b14c37b0b206254cf1a4c6c5','hashes':hashes,'inventory':inventory,
    'A_v_A':qa,'official_subprocess_smoke':smoke,'effects':effects,'rows':rows}
out=ROOT/'ExternalAnalysis/Pablo_Model_Independent_Review.md'
out.write_text('# Pablo models: independent inventory and bounded review\n\nReviewed pablo-poker commit24653c92256ad1b7b14c37b0b206254cf1a4c6c5. '
    'No AGENTS.md exists in this branch inventory. README and candidate/README.txt were read; autonomous lab, fetchers, workers, dashboard and exporters were not launched. '
    'Selected current root bot.py (v4 export), not a claim of strongest proven model. Other exports are distinct policies: bot_gen7.py, bot_v31.py and bot_v32.py. '
    'No online-result identity is established for these bytes.\n\n'
    'The latest root export is a self-contained stdlib Agent compatible with the official engine loader. '
    'candidate/export.py instead requires baseline_params.json and live_model_snapshot.json absent from the branch, so that path is not reproducible from committed inputs; no replacement model was invented. '
    'README describes earlier strategy/lab workflows and is partly stale relative to v4.\n\n'
    'Reviewed bench2.py before running anything: it uses its own fieldbot simulator, seeded lineup,500MC with very large clock limits, and adaptation fieldsA/B. '
    'Such tuning results are not independent confirmation of v4, especially when policy and simulator are updated together. This review uses the official PokerBot engine and independently fitted sunday_v2 frequency clones instead.\n\n'
    'Run: `python tools/independent_pablo/run_review.py` from PokerBot. Imported fixed diagnostic helper and input hashes are below. '
    'Both builds and all clones receive per-decision RNG seeding. Hero simulate exits after32samples, budget override.001 in both builds; DEBUG=True exposes swallowed exceptions in this sandbox only. '
    'These modified diagnostic conditions do not certify the unmodified export\'s timing or live strength. '
    'Before the pilot, G and v4 each passed20hand A-v-A twice (80hands). Exact v4 bytes also received a20hand official SubprocessPlayer protocol smoke at25ms/10s bank. '
    'Five paired1000hand tables fresh87100000-87100004 add10000hands; total10100 table-hands. '
    'Every table contains the seven sunday_v2 clones once; hero seats0-4 rotate, opponents seeded-shuffle. Clones remain imperfect public-frequency approximations.\n\n'
    'Protocol smoke is intentionally small and cannot establish full1000hand bank performance or a safe deployment deadline margin. '
    'Subprocess errors/timeouts are distinct from legal-action success and generic internal silent fallbacks.\n\n```json\n'+json.dumps(data,indent=2)+'\n```\n',encoding='utf-8')
print(json.dumps(effects,indent=2),flush=True)
