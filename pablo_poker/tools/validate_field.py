"""Frozen temporal field validation; writes artifacts only in candidate/.

python -B tools/validate_field.py --tables 8 --hands 1000 --workers 2
Calibration is assessed against held-out logs, not against a desired profit.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import statistics
import sys
import subprocess
from contextlib import nullcontext

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_field_model import build, collect, slot_ts


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run(job):
    seed, count, names, hero_seat, engine = job[:5]
    overrides = job[5] if len(job)>5 else {}
    from engine import FixedHandsTable
    from sim import fieldbot
    fieldbot._MODEL.clear()
    fieldbot._MODEL.update(json.loads((ROOT / 'candidate/field_model.json').read_text()))
    mod = load(ROOT / ('candidate/baseline.py' if engine == 'baseline' else 'candidate/engine.py'), 'hero')
    # Fixed work makes paired comparisons reproducible. Runtime is tested separately.
    params = json.loads((ROOT / 'candidate/baseline_params.json').read_text())
    if engine == 'baseline':
        hero = mod.Agent()
    else:
        hero = mod.Agent(params=dict(params,**overrides))
    hero.P.update(max_sims=64, max_ms=100000., hard_ms=100000., bank_s=100000.)
    hero.bank = 100000.
    hero.rng.seed(seed)
    mod.DEBUG = True
    class Player:
        def __init__(self, agent):
            self.agent = agent
        def start_table(self, seat, info):
            self.agent.on_table_start(info)
        def act(self, state):
            return self.agent.act(state)
        def hand_end(self, summary):
            if hasattr(self.agent, 'on_hand_end'):
                self.agent.on_hand_end(summary)
    players = [Player(hero if i == hero_seat else fieldbot.FieldBot(n, seed=seed * 31 + i))
               for i, n in enumerate(names)]
    table = FixedHandsTable(players, hands=count, seed=seed, record=True)
    result = table.play()
    hands = []
    sd = 0
    for h in result['log']:
        h['results'] = [b-a for a,b in zip(h['stacks'], h['end'])]
        if str(hero_seat) in h.get('showdown', {}):
            sd += h['results'][hero_seat]
        # Match real visibility: only showdown cards or hero's cards are exposed.
        h['hole'] = {s:v for s,v in h['hole'].items() if s in h.get('showdown', {}) or s == str(hero_seat)}
        hands.append(h)
    doc = dict(players=names, hands=hands, ref='sim-%d-%s' % (seed, engine),
               round=dict(slot='2026-11-14T19:00:00'))
    counts, _ = collect(documents=[doc])
    from tools.call_equity import measure
    field = Counter()
    for name, c in counts.items():
        if name != 'kaiserbot':
            field.update(c)
    return dict(seed=seed, engine=engine, hands=count, chips=result['chips'][hero_seat],
                sd_chips=sd, field=dict(field), hero=dict(counts['kaiserbot']),call_equity=measure([doc]))


def subprocess_run(job):
    # Ordinary subprocess pipes work in restricted Windows environments where
    # multiprocessing's named pipes do not. Every job runs in a fresh process.
    done=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--job',json.dumps(job)],
                        capture_output=True,text=True,check=True)
    return json.loads(done.stdout)


def summarize(rows):
    n = sum(x['hands'] for x in rows)
    xs = [x['chips'] / x['hands'] * 5 for x in rows]
    return dict(hands=n, bb100=sum(x['chips'] for x in rows)*5/n,
                sd_bb100=sum(x['sd_chips'] for x in rows)*5/n,
                table_se=statistics.stdev(xs)/len(xs)**.5 if len(xs)>1 else None)


def strength(c):
    out = {}
    for st in ('flop','turn','river'):
        for kind in ('bet','raise'):
            for b in (5,6,7):
                prefix = 'post.%s.strength.%s.%d|' % (st,kind,b)
                ns = [c.get(prefix+str(i),0) for i in range(4)]
                if sum(ns):
                    out['%s/%s/%s'%(st,kind,b)] = dict(n=sum(ns), strong=ns[3]/sum(ns), levels=[v/sum(ns) for v in ns])
    return out


def frequencies(c):
    def rate(prefix, action):
        vals={k.split('|')[-1]:v for k,v in c.items() if k.startswith(prefix) and '|' in k}
        # Sum across position/context buckets, rather than overwriting duplicate actions.
        den=sum(v for k,v in c.items() if k.startswith(prefix) and '|' in k)
        num=sum(v for k,v in c.items() if k.startswith(prefix) and k.endswith('|'+action))
        return num/den if den else None
    out={'open':rate('pre.first.','raise'),'threebet':rate('pre.vs_open.','raise')}
    for street in ('flop','turn','river'):
        out[street+'_bet']=rate('post.'+street+'.bet.','bet')
        out[street+'_raise']=rate('post.'+street+'.vs.','raise')
        out[street+'_fold']=rate('post.'+street+'.vs.','fold')
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tables',type=int,default=8)
    ap.add_argument('--hands',type=int,default=1000)
    ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--seed',type=int,default=731000)
    ap.add_argument('--freeze',action='store_true',help='reuse saved model and real comparison cohort')
    ap.add_argument('--holdout-rounds',type=int,default=4)
    a=ap.parse_args()
    cohort_path=ROOT/'candidate/cohort.json'
    if a.freeze and cohort_path.exists():
        cohort=json.loads(cohort_path.read_text())
        held,cutoff,real_field=cohort['held'],cohort['cutoff'],Counter(cohort['field'])
    else:
        own=[json.loads(p.read_text()) for p in (ROOT/'hands').glob('*.json')]
        own.sort(key=lambda d:slot_ts(d.get('round',{})))
        held=own[-a.holdout_rounds:]
        cutoff=slot_ts(held[0]['round'])
        model=build(before=cutoff)
        (ROOT/'candidate/field_model.json').write_text(json.dumps(model,sort_keys=True))
        real_counts,_=collect(after=cutoff)
        real_field=Counter()
        for name,c in real_counts.items():
            if name!='kaiserbot':real_field.update(c)
        cohort_path.write_text(json.dumps(dict(held=held,cutoff=cutoff,field=dict(real_field))))
    jobs=[]
    for i in range(a.tables):
        d=held[i%len(held)]; names=d['players'];seat=names.index('kaiserbot')
        for engine in ('baseline','candidate'):
            jobs.append((a.seed+i,a.hands,names,seat,engine))
    rows=[]
    artifact_paths=('candidate/engine.py','candidate/baseline.py','candidate/field_model.json',
                    'candidate/live_model_snapshot.json','sim/fieldbot.py','tools/validate_field.py',
                    'tools/build_field_model.py','tools/call_equity.py')
    artifact_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in artifact_paths}
    with (ThreadPoolExecutor(max_workers=a.workers) if a.workers > 1 else nullcontext()) as pool:
        results = pool.map(subprocess_run,jobs) if pool else map(run,jobs)
        for r in results:
            rows.append(r)
            print(r['engine'],r['seed'],'bb100',round(r['chips']*5/r['hands'],1),flush=True)
    out=dict(cutoff=cutoff,seed=a.seed,rows=rows,real_strength=strength(real_field),
             real_frequencies=frequencies(real_field),heldout_rounds=[d['round'] for d in held])
    for engine in ('baseline','candidate'):
        selected=[x for x in rows if x['engine']==engine]
        c=Counter()
        for x in selected:c.update(x['field'])
        hc=Counter()
        ce=Counter()
        for x in selected:hc.update(x['hero'])
        for x in selected:ce.update(x.get('call_equity',{}))
        out[engine]=dict(**summarize(selected),strength=strength(c),
                         field_frequencies=frequencies(c),hero_frequencies=frequencies(hc),call_equity=dict(ce))
    real_hands=sum(len(d['hands']) for d in held)
    real_chips=sum(d['round']['chips'] for d in held)
    real_sd=sum(h['results'][d['seat']] for d in held for h in d['hands'] if str(d['seat']) in h.get('showdown',{}))
    out['real']=dict(hands=real_hands,bb100=real_chips*5/real_hands,sd_bb100=real_sd*5/real_hands)
    from tools.call_equity import measure
    out['real']['call_equity']=measure(held)
    for key in ('bb100','sd_bb100'):
        vals=[]
        for d in held:
            chips=(d['round']['chips'] if key=='bb100' else
                   sum(h['results'][d['seat']] for h in d['hands'] if str(d['seat']) in h.get('showdown',{})))
            vals.append(chips*5/len(d['hands']))
        out['real'][key+'_se']=statistics.stdev(vals)/len(vals)**.5 if len(vals)>1 else None
    diffs=[(next(r for r in rows if r['seed']==seed and r['engine']=='candidate')['chips']-
            next(r for r in rows if r['seed']==seed and r['engine']=='baseline')['chips'])*5/a.hands
           for seed in range(a.seed,a.seed+a.tables)]
    out['paired']=dict(mean=statistics.mean(diffs),se=statistics.stdev(diffs)/len(diffs)**.5 if len(diffs)>1 else None)
    out['hashes']=artifact_hashes
    if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=v for p,v in artifact_hashes.items()):
        raise RuntimeError('artifacts changed during validation; discard this comparison')
    path=ROOT/'candidate'/('validation_%d.json'%a.seed)
    path.write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k not in ('rows','real_strength')},indent=2),flush=True)


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--job':print(json.dumps(run(json.loads(sys.argv[2]))))
    else:main()
