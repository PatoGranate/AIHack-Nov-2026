"""Frozen eight-bot league: one process, 4 seeds x 8 seats, 1000 hands/round."""
from pathlib import Path
import sys,json,hashlib,shutil,importlib.util,time,math
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
OLD=OUT.parent/'Tournament'
sys.path.insert(0,str(ROOT/'kit'))
from engine import FixedHandsTable
from engine.players import LocalPlayer
SEEDS=list(range(616161,616165))
N=8;HANDS=1000;T3=3.182446305
EXPECTED='b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a'
CACHE={}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def freeze():
    if (OUT/'manifest.json').exists():return json.loads((OUT/'manifest.json').read_text())
    manifest=json.loads((OLD/'manifest.json').read_text())
    for i,m in enumerate(manifest):
        src=OLD/m['snapshot'];assert digest(src)==m['sha256']
        shutil.copyfile(src,OUT/f'bot_{i}.py');m['snapshot']=f'bot_{i}.py'
    src=ROOT/'tools/cands/v7.py';assert digest(src)==EXPECTED
    shutil.copyfile(src,OUT/'bot_7.py')
    manifest.append({'name':'v7 frozen','source':'tools/cands/v7.py','snapshot':'bot_7.py','sha256':EXPECTED})
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return manifest

class Seeded(LocalPlayer):
    def __init__(self,cls,seed):super().__init__(cls);self.seed=seed
    def start_table(self,seat,info):
        super().start_table(seat,info)
        if hasattr(self.agent,'rng'):self.agent.rng.seed(self.seed)

def load(m):
    path=OUT/m['snapshot'];assert digest(path)==m['sha256']
    if str(path) not in CACHE:
        sp=importlib.util.spec_from_file_location('league_'+path.stem,path)
        mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod);CACHE[str(path)]=mod
    return CACHE[str(path)].Agent

def aggregate(manifest):
    rounds=[json.loads(p.read_text()) for p in sorted(OUT.glob('round_*.json'))]
    complete=[s for s in SEEDS if sum(r['seed']==s for r in rounds)==N]
    valid=[r for r in rounds if r['seed'] in complete]
    rows=[]
    for i,m in enumerate(manifest):
        blocks=[sum(next(x for x in r['rows'] if x['id']==i)['chips']/20/HANDS*100 for r in valid if r['seed']==s)/N for s in complete]
        mean=sum(blocks)/len(blocks) if blocks else None
        se=math.sqrt(sum((x-mean)**2 for x in blocks)/(len(blocks)-1)/len(blocks)) if len(blocks)>1 else None
        rows.append({'id':i,'name':m['name'],'blocks':blocks,'bb100':mean,'se':se,'ci95':[mean-T3*se,mean+T3*se] if len(blocks)==4 else None,'errors':sum(next(x for x in r['rows'] if x['id']==i)['stats']['errors'] for r in rounds)})
    paired=[]
    if len(complete)==4:
        for i in (6,5,4):
            diffs=[a-b for a,b in zip(rows[7]['blocks'],rows[i]['blocks'])];mean=sum(diffs)/4;se=math.sqrt(sum((x-mean)**2 for x in diffs)/3/4)
            paired.append({'comparison':'v7 minus '+manifest[i]['name'],'blockDifferences':diffs,'difference':mean,'se':se,'ci95':[mean-T3*se,mean+T3*se]})
    result={'rounds':len(rounds),'completeSeeds':complete,'handsPerBot':len(rounds)*HANDS,'timingEnforced':False,'rows':rows,'pairedLeagueDifferences':paired,'allSeatErrors':sum(x['stats']['errors'] for r in rounds for x in r['rows'])}
    (OUT/'summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result

if __name__=='__main__':
    manifest=freeze();classes=[load(m) for m in manifest]
    (OUT/'method.txt').write_text('One process; cached modules; 4 independent deck seeds 616161..616164; all eight seat rotations per seed; 1000 hands each; 100 BB reset stacks; 10/20 blinds. LocalPlayer: NO externally enforced deadlines or time bank. Original bot budgets retained, agent RNG seeded by deck seed and bot identity; elapsed-time sampling remains machine-dependent. All-seat surfaced errors checked. Block means use 8 rotations. Approximate 95% t(3) intervals use four block means. v7-minus-peer differences compare co-seated league returns, not replacement A/B or heads-up matchups. No promotion claim from a positive mean alone.\n',encoding='utf-8')
    for si,seed in enumerate(SEEDS):
        for rot in range(N):
            r=si*N+rot;path=OUT/f'round_{r:03}.json'
            if path.exists():continue
            order=[(j+rot)%N for j in range(N)]
            players=[Seeded(classes[i],seed*31+i) for i in order]
            start=time.perf_counter()
            try:
                res=FixedHandsTable(players,hands=HANDS,seed=seed).play()
                assert sum(res['chips'])==0
                rows=[{'id':i,'seat':seat,'chips':res['chips'][seat],'stats':players[seat].stats.as_dict()} for seat,i in enumerate(order)]
                result={'round':r,'seed':seed,'rotation':rot,'hands':HANDS,'seconds':time.perf_counter()-start,'rows':rows,'errors':sum(x['stats']['errors'] for x in rows)}
                path.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps({'round':r,'seconds':round(result['seconds'],1),'errors':result['errors']}),flush=True)
                aggregate(manifest)
            finally:
                for p in players:p.close()
    result=aggregate(manifest);print(json.dumps(result),flush=True)
