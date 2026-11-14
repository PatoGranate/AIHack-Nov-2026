"""One guarded tuning cycle on frozen field; never writes live bot.py.

python -B tools/tune_field.py candidate/validation_733000.json
Requires field_gate approval, fresh seeds and complete paired results. A new
cycle records its seed allocation before simulation and keeps all artifacts.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.field_gate import check
from tools.validate_field import subprocess_run


def evaluate(variants,tables,hands,seed0,workers,held):
    jobs=[]
    for i in range(tables):
        d=held[i%len(held)];names=d['players'];seat=names.index('kaiserbot')
        for name,params in variants.items():
            jobs.append((name,(seed0+i,hands,names,seat,'candidate',params)))
    rows={}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for (name,job),result in zip(jobs,pool.map(subprocess_run,[j for _,j in jobs])):
            rows.setdefault(job[0],{})[name]=result
            print(name,job[0],result['chips'],flush=True)
    out={}
    for name in variants:
        if name=='reference':continue
        xs=[(r[name]['chips']-r['reference']['chips'])*5/hands for r in rows.values()]
        if len(xs)!=tables:raise RuntimeError('incomplete paired evaluation')
        out[name]=dict(mean=statistics.mean(xs),se=statistics.stdev(xs)/len(xs)**.5,n=len(xs))
    return out,rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('validation')
    ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--tables',type=int,default=24)
    a=ap.parse_args()
    report=json.loads(Path(a.validation).read_text())
    verdict=check(report)
    status=ROOT/'candidate/tuner_status.json'
    if not verdict['approved']:
        status.write_text(json.dumps(dict(status='calibration_failed',gate=verdict),indent=2))
        print(json.dumps(verdict,indent=2));return
    held=json.loads((ROOT/'candidate/cohort.json').read_text())['held']
    cursor=ROOT/'candidate/tuner_seeds.json'
    seed=json.loads(cursor.read_text())['next'] if cursor.exists() else 840000
    cursor.write_text(json.dumps({'next':seed+10000}))
    variants={'reference':{},'less_raise_margin':{'raise_margin':0.0},
              'more_threebets':{'eq_3b':.46},'less_bet_margin':{'bet_margin':0.0}}
    rec=dict(seed=seed,variants=variants,hashes=report['hashes'],tables=a.tables,hands=1000)
    path=ROOT/'candidate'/('tune_%d.json'%seed)
    path.write_text(json.dumps(dict(rec,status='preregistered'),indent=2))
    selection,rows=evaluate(variants,a.tables,1000,seed,a.workers,held)
    rec.update(selection=selection,selection_rows=rows)
    best=max(selection,key=lambda k:selection[k]['mean'])
    # Selection is only screening. One chosen candidate receives fresh holdout.
    if selection[best]['mean']>0:
        hold,rows=evaluate({'reference':{},best:variants[best]},a.tables*2,1000,seed+1000,a.workers,held)
        rec.update(holdout=hold,holdout_rows=rows)
        ev=hold[best]
        rec['approved']=ev['mean']>1.96*ev['se']
        if rec['approved']:
            (ROOT/'candidate/tuned_params.json').write_text(json.dumps(variants[best]))
    else:rec['approved']=False
    path.write_text(json.dumps(rec,indent=2))
    status.write_text(json.dumps(dict(status='holdout_passed' if rec['approved'] else 'no_promotion',result=str(path)),indent=2))
    print(json.dumps({k:v for k,v in rec.items() if not k.endswith('_rows')},indent=2))


if __name__=='__main__':main()
