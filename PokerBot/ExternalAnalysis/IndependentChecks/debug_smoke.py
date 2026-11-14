import sys,json,importlib.util,hashlib,shutil
from pathlib import Path
BASE=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE/'kit'))
from engine import FixedHandsTable
from engine.players import LocalPlayer
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
source=BASE/'tools/cands/v7.py';frozen=OUT/'v7_smoke_snapshot.py';shutil.copyfile(source,frozen)
m=load(frozen,'candidate');m.DEBUG=True
opps=['a_maniac.py','a_shover_wide.py','a_station2.py','a_tag.py','a_lag.py','a_minraiser.py']
mods=[load(BASE/'tools/opponents'/x,'o'+str(i)) for i,x in enumerate(opps)]
rows=[]
for seed in (515151,515152):
    ps=[LocalPlayer(m.Agent)]+[LocalPlayer(o.Agent) for o in mods]
    result=FixedHandsTable(ps,hands=1000,seed=seed).play()
    rows.append({'seed':seed,'chips':result['chips'],'allSeatStats':[p.stats.as_dict() for p in ps]})
out={'sha256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'handsPerRound':1000,'debug':True,'mode':'LocalPlayer; no external deadline enforcement','results':rows}
(OUT/'debug_smoke_results.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'sha256':out['sha256'],'allSeatErrors':[sum(p['errors'] for p in r['allSeatStats']) for r in rows],'heroErrors':[r['allSeatStats'][0]['errors'] for r in rows]}),flush=True)
