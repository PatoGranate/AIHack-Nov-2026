from pathlib import Path
import json,re
root=Path(__file__).resolve().parent
league=json.loads((root/'IndependentLeagueV7/summary.json').read_text(encoding='utf-8'))
assert league['rounds']==32 and len(league['completeSeeds'])==4
assert league['allSeatErrors']==0
rows=[]
labels={0:'v1 archive (older)',1:'v1 · A safe',2:'B balanced',3:'v2 · C aggressive',4:'v4 · D max aggression',5:'v3 · E fast',6:'F tuned',7:'v7 candidate'}
for r in sorted(league['rows'],key=lambda r:-r['bb100']):
    chips=sum(next(x['chips'] for x in json.loads(p.read_text(encoding='utf-8'))['rows'] if x['id']==r['id']) for p in (root/'IndependentLeagueV7').glob('round_*.json'))
    rows.append({'bot':labels[r['id']],'rate':r['bb100'],'lower':r['ci95'][0],'upper':r['ci95'][1],'chips':chips,'hands':32000})
config={'id':'v7-league-chart','title':'Independent eight-bot league','height':380,'spec':{'type':'horizontalBar','y':'bot','x':'rate','xLabel':'Big blinds won per 100 hands','showValues':True,'valueFormat':{'maximumFractionDigits':1},'uncertainty':{'lower':'lower','upper':'upper','label':'Approximate 95% t interval across four deck-seed blocks'},'tooltipFields':[{'field':'chips','label':'Net chips'},{'field':'hands','label':'Hands per bot'}]},'rows':rows}
raw=(root.parent/'tools/final_results.txt').read_text(encoding='utf-8');comparisons={}
for baseline,token in [('F','F_gen01'),('E','b3')]:
    matches=re.findall(r'v7 vs '+token+r' (\w+)\s+DIFF\s+([+-][\d.]+) bb/100 \(se ([\d.]+)\)',raw)
    assert len(matches)==3
    rr=[{'field':{'real':'Observed-stat clones','heldout':'Jittered clone family','strong':'Strong mixed field'}[field],'difference':float(mean),'lower':float(mean)-1.96*float(se),'upper':float(mean)+1.96*float(se)} for field,mean,se in matches]
    comparisons[baseline]={'id':'v7-field-chart','title':'V7 advantage over '+baseline,'height':230,'spec':{'type':'horizontalBar','y':'field','x':'difference','xLabel':'Difference in bb/100','showValues':True,'valueFormat':{'maximumFractionDigits':1},'uncertainty':{'lower':'lower','upper':'upper','label':'Approximate 95% normal interval; team-reported SE'}},'rows':rr}
vis=Path('C:/Users/pelay/.codex/visualizations/2026/11/14/01a1da50-efb7-7ba0-b530-229f1b9ff62c/poker-v7-validation.html')
for c in (config,*comparisons.values()):
    c['spec']['valueFormat']['style']='decimal'
    c['spec']['uncertainty']['style']='bars'
text=vis.read_text(encoding='utf-8')
for marker,data in [('__DATA__',league),('__LEAGUE__',config),('__F__',comparisons['F']),('__E__',comparisons['E'])]:text=text.replace(marker,json.dumps(data).replace('<','\\u003c'))
vis.write_text(text,encoding='utf-8')
assert vis.read_bytes().decode('utf-8',errors='strict')
assert '__LEAGUE__' not in text
assert all(r['lower']<=r['rate']<=r['upper'] for r in config['rows'])
script=re.search(r'<script type="module">(.*?)</script>',text,re.S).group(1)
(root/'IndependentLeagueV7/visual_script.mjs').write_text(script,encoding='utf-8')
print('Wrote UTF-8 v7 visual with 3 chart payloads and complete 32-round data.')
