"""Frozen seven-bot league, round-clustered uncertainty and decision probes."""
import os, sys, json, shutil, hashlib, importlib.util, random, time, math
from pathlib import Path
from multiprocessing import Pool
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(__file__).resolve().parent/'Tournament'
sys.path.insert(0,str(ROOT/'kit'))
from engine import FixedHandsTable
from engine.players import LocalPlayer, SubprocessPlayer
FILES=[('v1 archive','tools/opponents/v1.py')]+[(p.parent.name,str(p.relative_to(ROOT))) for p in sorted((ROOT/'submissions').glob('*/bot.py'))]
_CACHE={}

def load(path,tag):
    key=str(path)
    if key in _CACHE:return _CACHE[key]
    sp=importlib.util.spec_from_file_location('bot_'+str(tag),path)
    m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
    _CACHE[key]=m
    return m

class Observed(LocalPlayer):
    def __init__(self,cls,seed):
        super().__init__(cls);self.seed=seed;self.actions={};self.vp=set();self.pr=set();self.probes=[];self.times=[]
    def start_table(self,seat,info):
        super().start_table(seat,info)
        if hasattr(self.agent,'rng'):self.agent.rng.seed(self.seed)
    def act(self,s):
        t=time.perf_counter();a=super().act(s);self.times.append((time.perf_counter()-t)*1000)
        ac=(a or {}).get('action','invalid');key=s['street']+':'+str(ac)
        self.actions[key]=self.actions.get(key,0)+1
        if s['street']=='preflop':
            if ac in ('call','raise','all_in'):self.vp.add(s['hand_number'])
            if ac in ('raise','all_in'):self.pr.add(s['hand_number'])
        elif len(self.probes)<3 and s['to_call']>0:
            self.probes.append(json.loads(json.dumps(s)))
        return a

def run(job):
    mode,r,hands=job
    manifest=json.loads((OUT/'manifest.json').read_text())
    n=len(manifest);order=[(i+r)%n for i in range(n)]
    mods=[load(OUT/manifest[i]['snapshot'],i) for i in order]
    # Seeds shared by a rotation block: every bot sees every seat on these deals.
    seed=871003+r//n
    if mode=='fast':players=[Observed(m.Agent,seed*31+i) for i,m in enumerate(mods)]
    else:players=[SubprocessPlayer(str(OUT/manifest[i]['snapshot']),timeout_ms=10,bank_ms=10000) for i in order]
    t=time.perf_counter()
    try:
        res=FixedHandsTable(players,hands=hands,seed=seed).play()
        rows=[]
        for seat,i in enumerate(order):
            p=players[seat];row={'id':i,'chips':res['chips'][seat],'stats':p.stats.as_dict()}
            if mode=='fast':
                row.update(vpip=len(p.vp),pfr=len(p.pr),actions=p.actions,p99=sorted(p.times)[int(.99*(len(p.times)-1))],probes=p.probes if r==0 else [])
            rows.append(row)
        out={'mode':mode,'round':r,'seed':seed,'hands':hands,'seconds':time.perf_counter()-t,'rows':rows}
        (OUT/f'{mode}_{r:03}.json').write_text(json.dumps(out))
        return {'mode':mode,'round':r,'seconds':round(out['seconds'],1),'errors':sum(x['stats']['errors'] for x in rows)}
    finally:
        for p in players:p.close()

def probes():
    mfest=json.loads((OUT/'manifest.json').read_text());first=json.loads((OUT/'fast_000.json').read_text())
    modules=[load(OUT/mf['snapshot'],f'probe_{i}') for i,mf in enumerate(mfest)]
    states=[]
    for row in first['rows']:
        for s in row['probes']:
            if len(states)<6 and not any(x['hole_cards']==s['hole_cards'] and x['board']==s['board'] for x in states):states.append(s)
    results=[]
    for pi,s in enumerate(states):
        rr=[]
        for i,mf in enumerate(mfest):
            mod=modules[i];a=mod.Agent()
            a.on_table_start({'seat':s['seat'],'num_players':len(s['stacks']),'hands':1000})
            if hasattr(a,'rng'):a.rng.seed(9941+pi)
            captured={}
            method='simulate' if hasattr(a,'simulate') else 'equity' if hasattr(a,'equity') else None
            if method:
                original=getattr(a,method)
                def wrapped(*args,_orig=original,**kw):
                    val=_orig(*args,**kw);captured['estimate']=val;return val
                setattr(a,method,wrapped)
            action=a.act(s)
            rr.append({'id':i,'action':action,'equity':captured.get('estimate',[None])[0] if method=='simulate' else captured.get('estimate'),'samples':getattr(a,'last_sims',None)})
        results.append({'state':s,'bots':rr})
    (OUT/'decision_probes.json').write_text(json.dumps(results))

def aggregate():
    manifest=json.loads((OUT/'manifest.json').read_text());summary={}
    for mode in ('fast','strict'):
        rounds=[json.loads(p.read_text()) for p in sorted(OUT.glob(mode+'_*.json'))]
        if not rounds:continue
        rows=[]
        for i,mf in enumerate(manifest):
            vals=[next(z for z in r['rows'] if z['id']==i) for r in rounds]
            rates=[v['chips']/20/r['hands']*100 for v,r in zip(vals,rounds)]
            # Seat rotations share cards: uncertainty clustered over seed blocks.
            groups={}
            for rate,r in zip(rates,rounds):groups.setdefault(r['seed'],[]).append(rate)
            blocks=[sum(v)/len(v) for v in groups.values()];mean=sum(rates)/len(rates)
            se=math.sqrt(sum((x-sum(blocks)/len(blocks))**2 for x in blocks)/(len(blocks)-1)/len(blocks)) if len(blocks)>1 else None
            actions={}
            for v in vals:
                for k,c in v.get('actions',{}).items():actions[k]=actions.get(k,0)+c
            rows.append({'id':i,'name':mf['name'],'bb100':mean,'se':se,'blocks':len(blocks),'hands':sum(r['hands'] for r in rounds),'roundRates':rates,'chips':sum(v['chips'] for v in vals),'vpip':sum(v.get('vpip',0) for v in vals),'pfr':sum(v.get('pfr',0) for v in vals),'actions':actions,'errors':sum(v['stats']['errors'] for v in vals),'timeouts':sum(v['stats']['timeouts'] for v in vals),'bankOut':sum(v['stats']['bank_out'] for v in vals),'maxMs':max(v['stats']['max_ms'] for v in vals),'thinkSeconds':sum(v['stats']['avg_ms']*v['stats']['decisions']/1000 for v in vals)})
        summary[mode]={'rounds':len(rounds),'tableHands':sum(r['hands'] for r in rounds),'rows':rows}
    summary['probes']=json.loads((OUT/'decision_probes.json').read_text()) if (OUT/'decision_probes.json').exists() else []
    summary['manifest']=manifest
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({m:[(r['name'],round(r['bb100'],2),r['timeouts'],r['errors']) for r in d['rows']] for m,d in summary.items() if m in ('fast','strict')}),flush=True)

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    if '--aggregate' in sys.argv:aggregate();sys.exit()
    if '--probes' in sys.argv:probes();aggregate();sys.exit()
    if not (OUT/'manifest.json').exists():
        manifest=[]
        for i,(name,path) in enumerate(FILES):
            dest=OUT/f'bot_{i}.py';shutil.copyfile(ROOT/path,dest)
            manifest.append({'name':name,'source':path,'snapshot':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
        (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    mode='strict' if '--strict' in sys.argv else 'fast'
    count=7 if mode=='strict' else 56
    jobs=[(mode,r,1000) for r in range(count) if not (OUT/f'{mode}_{r:03}.json').exists()]
    if mode=='strict':
        for job in jobs:print(run(job),flush=True)
    else:
        with Pool(2) as pool:
            for row in pool.imap_unordered(run,jobs):print(row,flush=True)
    aggregate()
