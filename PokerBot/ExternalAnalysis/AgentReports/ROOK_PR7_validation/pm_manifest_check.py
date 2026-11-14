import csv,hashlib,os,glob,collections
rows=list(csv.DictReader(open('PokerBot/ExternalAnalysis/SaturdayFieldPostmortem/data/input_manifest.csv',encoding='utf-8')))
bad=miss=0
for r in rows:
    p=r['path']
    if not os.path.exists(p): miss+=1; continue
    if hashlib.sha256(open(p,'rb').read()).hexdigest()!=r['sha256']: bad+=1
disk=glob.glob('PokerBot/Hand_data/SaturdayRealRounds/*.json')+glob.glob('PokerBot/Hand_data/ExternalTeamData/*/SaturdayRealRounds/*.json')
disk={d.replace(os.sep,'/') for d in disk}
print('manifest rows',len(rows),'missing',miss,'hash mismatch',bad,'on-disk files',len(disk),'not in manifest',len(disk-{r['path'] for r in rows}))
print(collections.Counter(r['status'].split()[0] for r in rows))
