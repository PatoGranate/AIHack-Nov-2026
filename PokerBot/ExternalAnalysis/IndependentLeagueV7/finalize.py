from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
d=json.loads((P/'summary.json').read_text(encoding='utf-8'))
m=json.loads((P/'manifest.json').read_text(encoding='utf-8'))
assert d['rounds']==32 and d['completeSeeds']==list(range(616161,616165))
assert d['allSeatErrors']==0
for bot in m:assert hashlib.sha256((P/bot['snapshot']).read_bytes()).hexdigest()==bot['sha256']
for f in P.glob('round_*.json'):
    r=json.loads(f.read_text(encoding='utf-8'));assert len(r['rows'])==8 and sum(x['chips'] for x in r['rows'])==0
lines=['INDEPENDENT EIGHT-BOT LEAGUE WITH FROZEN V7','',
'Completed 32 rounds x 1,000 hands, 32,000 hands per bot, 256,000 player-hand observations.',
'Four independent deck seeds 616161..616164, each with all eight seat rotations.',
'One process and cached modules; agent RNG seeded by deck seed and identity.',
'No externally enforced timing limit or time bank. Original bot budgets retained.',
'Surface errors across ALL seats: '+str(d['allSeatErrors']),
'V7 SHA256: '+m[7]['sha256'],'',
'LEAGUE RETURNS (bb/100; approximate 95% t(3) intervals from four seed blocks)']
for r in sorted(d['rows'],key=lambda x:-x['bb100']):
    lo,hi=r['ci95'];lines.append(f"{r['name']}: {r['bb100']:+.2f}; SE {r['se']:.2f}; CI [{lo:+.2f}, {hi:+.2f}]")
lines.extend(['','V7 MINUS PEERS (co-seated league-return differences, not replacement A/B)'])
for r in d['pairedLeagueDifferences']:
    lo,hi=r['ci95'];lines.append(f"{r['comparison']}: {r['difference']:+.2f}; SE {r['se']:.2f}; CI [{lo:+.2f}, {hi:+.2f}]")
lines.extend(['','INTERPRETATION',
'This field differs structurally from the ParamBot clone fields. It tests v7',
'against seven archived strategies simultaneously. It does not replace the team',
'field-weighted A/B experiment or establish a universally strongest bot.',
'A confidence interval crossing zero leaves the corresponding comparison',
'unresolved. Only four independent deck blocks were used; intervals can be wide.',
'Do not compare absolute bb/100 directly to the earlier seven-bot league, because',
'adding v7 changes every bot\'s opponents, and these use different deck seeds.',
'Surface error counts cannot detect exceptions swallowed inside bot act().',
'Elapsed-time-limited Monte Carlo remains dependent on machine load despite RNG',
'seeding. No timing-reliability or deployment certification is claimed.',
'Raw rounds, exact frozen snapshots, hashes and seed-block differences are saved',
'beside this report. No playing source or uploaded bot was modified.'])
(P/'Results.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
validated=[]
for p in P.iterdir():
    if p.is_file() and p.suffix in ('.json','.txt','.py'):
        p.read_bytes().decode('utf-8',errors='strict');validated.append(p.name)
print('\n'.join(lines));print('Strict UTF-8 validation passed for',len(validated),'files.')
