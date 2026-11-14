from pathlib import Path
import subprocess,sys
base=Path(__file__).resolve().parent
dest=base/'StrongestFocus';dest.mkdir(exist_ok=True)
s=(base/'profile_actions.py').read_text(encoding='utf-8')
s=s.replace("ROOT=OUT.parents[1]","ROOT=OUT.parents[2]")
s=s.replace("files=list(sorted((DATA/'ExternalData_OtherBots').glob('*.json')))+list(sorted(DATA.glob('*.json')))","files=list(sorted(DATA.rglob('*.json')))")
s=s.replace("source='external' if f.parent.name=='ExternalData_OtherBots' else 'own'","source='external' if ('ExternalTeamData' in f.parts or 'ExternalData_OtherBots' in f.parts) else 'own'")
s=s.replace("'vpip':stats[nm]['vpip'],'pfr':stats[nm]['pfr']", "'rfi':Counter(stats[nm]['rfi']),'rfiPos':{k:Counter(v) for k,v in stats[nm]['rfiPos'].items()},'vpip':stats[nm]['vpip'],'pfr':stats[nm]['pfr']")
s=s.replace("'vpipCount':s['vpip']-old['vpip']", "'rfiCounts':dict(s['rfi']-old['rfi']),'rfiPosCounts':{k:dict(v-old['rfiPos'].get(k,Counter())) for k,v in s['rfiPos'].items() if (v-old['rfiPos'].get(k,Counter()))},'vpipCount':s['vpip']-old['vpip']")
s=s.replace("'sources':entry['sources'],'groups':sorted(entry['groups'])}","'sources':entry['sources'],'groups':sorted(entry['groups']),'publicEventSha256':hashlib.sha256(json.dumps([(h['n'],h['events'],h['results']) for h in sorted(d['hands'],key=lambda h:h['n'])],separators=(',',':'),ensure_ascii=True).encode('utf-8')).hexdigest()}")
(dest/'profile_actions.py').write_text(s,encoding='utf-8')
subprocess.run([sys.executable,str(dest/'profile_actions.py')],check=True)
