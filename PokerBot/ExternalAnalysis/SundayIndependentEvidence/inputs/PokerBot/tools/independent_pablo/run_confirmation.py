"""One preregistered frozen Pablo-v4/G confirmation; no tuning or runtime claims.
Run once from PokerBot: python tools/independent_pablo/run_confirmation.py
"""
import collections
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import statistics
import types

ROOT=Path(__file__).resolve().parents[2]
old_report=ROOT/'ExternalAnalysis/Pablo_Model_Independent_Review.md'
old=json.loads(re.search(r'```json\n(.*?)\n```',old_report.read_text(encoding='utf-8'),re.S).group(1))
# Reuse the exact already-A-v-A-checked loader and play() definitions, but never
# execute that exploratory runner's top-level QA, smoke or exploratory pilot.
source=ROOT/'tools/independent_pablo/run_review.py'
module=types.ModuleType('frozen_pablo_harness');module.__file__=str(source)
prefix=source.read_text(encoding='utf-8').split('\nqa={}\n',1)[0]
exec(compile(prefix,str(source),'exec'),module.__dict__)
H=module
assert hashlib.sha256((ROOT/H.PABLO).read_bytes()).hexdigest()=='8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108'
assert hashlib.sha256((ROOT/H.G).read_bytes()).hexdigest()=='b8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a'
dependencies=[H.G,H.PABLO,'tools/independent_pablo/run_review.py','tools/sunday_early_adapt_pilot.py']+H.OPPS
for p in dependencies:
    assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==old['hashes'][p],('dependency changed',p)
dependencies+=['tools/independent_ctx_pr11/opponents/_common.py','tools/independent_ctx_pr11/opponents/sunday_v2/MANIFEST.json',
    'tools/arena.py','kit/engine/game.py','kit/engine/players.py','tools/independent_pablo/run_confirmation.py']
outdir=ROOT/'ExternalAnalysis/AgentReports/Pablo_V4_Confirmation_89100000'
outdir.mkdir(parents=True,exist_ok=True)
manifest_path=outdir/'preregistered_manifest.json'
assert not manifest_path.exists(),'This run was already preregistered; refuse automatic repeat.'
manifest={'registered_utc':datetime.now(timezone.utc).isoformat(),'candidate':H.PABLO,'baseline':H.G,
    'candidate_branch_commit':'24653c92256ad1b7b14c37b0b206254cf1a4c6c5','seeds':list(range(89100000,89100032)),
    'pairs':32,'hands_per_arm_table':1000,'total_table_hands':64000,'hero_rule':'pair_index % 8',
    'field':'exact seven sunday_v2 clones once per table; seeded opponent shuffle',
    'diagnostic_work':'32 MC simulations, per-decision deterministic RNG for hero and all clones, .001 budget override; no clock/bank influence',
    'primary_endpoint':'unweighted paired table difference Pablo minus G bb/100; SE=s_sample/sqrt(32); t95CI df31',
    'secondary_descriptive':'four preregistered consecutive8-pair blocks; hand windows1-50,51-200,201-1000; action counts',
    'decision_rule':'lower primary t95 bound >0 and zero observed errors is favorable evidence in this fixed-work clone field only; otherwise no demonstrated improvement. No promotion from this run alone.',
    'A_v_A':'reused unchanged-loader controls in original exploratory report; no new QA table-hands because frozen sources/loader/field files unchanged',
    'no_retries_or_tuning':True,'hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in dependencies}}
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
mh=hashlib.sha256(manifest_path.read_bytes()).hexdigest()
print('PREREGISTERED',manifest_path,'sha256',mh,flush=True)
raw=outdir/'paired_tables.jsonl'
rows=[]
with raw.open('x',encoding='utf-8') as f:
    for t,seed in enumerate(manifest['seeds']):
        _,c=H.play(H.PABLO,seed,t%8,1000);_,b=H.play(H.G,seed,t%8,1000)
        row={'pair_index':t,'seed':seed,'hero_seat':t%8,'pablo_v4':c,'G':b}
        rows.append(row);f.write(json.dumps(row,sort_keys=True)+'\n');f.flush()
        if (t+1)%8==0:print('completed',t+1,'of32pairs',flush=True)

def stats(subset,w='all',n=1000,tc=2.039513446396408):
    def chip(r,k):return r[k]['chips'] if w=='all' else r[k]['window_chips'].get(w,0)
    c=[chip(r,'pablo_v4')/20/n*100 for r in subset];b=[chip(r,'G')/20/n*100 for r in subset];d=[x-y for x,y in zip(c,b)]
    mean=statistics.mean(d);se=statistics.stdev(d)/math.sqrt(len(d))
    return {'pairs':len(d),'pablo_bb100':statistics.mean(c),'G_bb100':statistics.mean(b),
        'diff_bb100':mean,'paired_se':se,'t95_CI':[mean-tc*se,mean+tc*se],
        'positive_pairs':sum(x>0 for x in d),'negative_pairs':sum(x<0 for x in d),'zero_pairs':sum(x==0 for x in d)}
errors={k:sum(r[k]['all_seat_errors'] for r in rows) for k in ('pablo_v4','G')}
counts={}
for k in ('pablo_v4','G'):
    acc=collections.Counter()
    for r in rows:acc.update(r[k]['actions'])
    counts[k]=dict(sorted(acc.items()))
summary={'completed_utc':datetime.now(timezone.utc).isoformat(),'manifest_sha256':mh,
    'raw_path':str(raw),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
    'primary':stats(rows),'secondary_blocks':{f'{i+1}-{i+8}':stats(rows[i:i+8],tc=2.364624251592784) for i in (0,8,16,24)},
    'secondary_windows':{w:stats(rows,w,n) for w,n in [('1-50',50),('51-200',150),('201-1000',800)]},
    'all_seat_errors':errors,'action_counts':counts}
sp=outdir/'summary.json';sp.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
report=ROOT/'ExternalAnalysis/Pablo_V4_Confirmation_89100000.md'
report.write_text('# Frozen Pablo v4 versus G: preregistered32-pair confirmation\n\n'
    'This is one new confirmation run, separate from the earlier exploratory five-pair +2.249/SE25.386 result. '
    'Exact frozen v4 SHA8458e3b17263d808607917fcef1b1d3188b776bff912a9b097c3cce3ec749108; frozenG raw-byte SHAb8a22e4b9085cf8c634a129deba71faf479834cac7ab127b84f551e2b0f0c16a. '
    'Manifest was written before compute, all32fresh seeds89100000-89100031 used once, no parameter tuning or repeated seed fishing. '
    '32paired1000hand tables=64000total table-hands. Existing A-v-A evidence reused only after byte-hash checks of unchanged models, loader/helper and all seven field files. '
    'The same previously validated frozen loader applies fixed32MC work and per-decision seeding to both heroes and all clones; production clock/bank stopping is overridden only in diagnostic memory. '
    'Four complete hero seat rotations; every table contains each of seven sunday_v2 clones once. '
    'These are frequency-based opponent approximations, not actual opponent policies. No independent real-opponent holdout or production-runtime certification is established. '
    'Matching work isolates strategy from the original unequal G/v4 compute budgets but is itself a low-work approximation. '
    'Future production gate must restore exact exported runtime/bank settings, assess exceptions/timeouts/fallbacks in subprocesses over complete rounds, and confirm platform limits separately.\n\n'
    'Run command (once only): `python tools/independent_pablo/run_confirmation.py` from PokerBot. '
    'Raw per-table chips/window chips/actions/error samples: `ExternalAnalysis/AgentReports/Pablo_V4_Confirmation_89100000/paired_tables.jsonl`. '
    'Pre-run manifest: `preregistered_manifest.json`; machine-readable results: `summary.json`, same directory. '
    'Raw and manifest hashes are included below. Secondary blocks/windows/actions are descriptive; no favorable window is substituted for the preregistered primary endpoint.\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n',encoding='utf-8')
print('PRIMARY',json.dumps(summary['primary']), 'ERRORS',errors,flush=True)
