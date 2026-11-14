import json,math,ast
from pathlib import Path
OUT=Path(__file__).resolve().parent/'Tournament'
VIS=Path('C:/Users/pelay/.codex/visualizations/2026/11/14/01a1da50-efb7-7ba0-b530-229f1b9ff62c/poker-comparison.html')
d=json.loads((OUT/'summary.json').read_text())
assert len(d['fast']['rows'])==7 and d['fast']['rounds']==56
assert d['strict']['rounds']==7
for mode in ('fast','strict'):
    assert sum(r['chips'] for r in d[mode]['rows'])==0
    for r in d[mode]['rows']:assert r['hands']==d[mode]['tableHands']
configs={}
for mode in ('fast','strict'):
    rows=[]
    for r in sorted(d[mode]['rows'],key=lambda r:-r['bb100']):
        margin=2.364624*r['se'] if r['se'] is not None else None
        rows.append({'bot':r['name'],'rate':r['bb100'],'lower':r['bb100']-margin if margin is not None else None,'upper':r['bb100']+margin if margin is not None else None,'chips':r['chips'],'hands':r['hands']})
    spec={'type':'horizontalBar','y':'bot','x':'rate','xLabel':'Big blinds won per 100 hands','showValues':True,'valueFormat':{'maximumFractionDigits':1},'tooltipFields':[{'field':'chips','label':'Net chips'},{'field':'hands','label':'Hands per bot'}]}
    if mode=='fast':spec['uncertainty']={'lower':'lower','upper':'upper','label':'Approximate 95% CI over 8 deck-seed blocks'}
    configs[mode]={'id':'poker-profit-chart','title':'Strategy winnings' if mode=='fast' else 'Winnings with enforced local deadlines','height':350,'spec':spec,'rows':rows,'description':'Seven bots at one table; higher is better. Results are specific to this field.'}
style=[]
for r in d['fast']['rows']:
    ac=r['actions'];post=sum(v for k,v in ac.items() if not k.startswith('preflop:'));raises=sum(v for k,v in ac.items() if not k.startswith('preflop:') and k.split(':')[1] in ('raise','all_in'))
    for label,num,den in [('Play preflop (VPIP)',r['vpip'],r['hands']),('Raise preflop (PFR)',r['pfr'],r['hands']),('Raise postflop / decisions',raises,post)]:style.append({'bot':r['name'],'metric':label,'rate':num/den,'events':num,'opportunities':den})
configs['style']={'id':'poker-style-chart','title':'Observed playing style','height':430,'spec':{'type':'horizontalBar','y':'bot','x':'rate','series':'metric','xLabel':'Share of hands / decisions','valueFormat':{'style':'percent','maximumFractionDigits':1}},'rows':style,'description':'VPIP and PFR: 56,000 hands per bot. Postflop raising uses postflop decisions as its denominator.'}
profiles=[]
for mf in d['manifest']:
    tree=ast.parse((OUT/mf['snapshot']).read_text());p={}
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='P' for t in node.targets):p=ast.literal_eval(node.value)
    if p:desc=f"Range-weighted simulation; BTN base cutoff {p['o_btn']:.0%}, 3-bet equity threshold {p['eq_3b']:.0%}, bet bonus {-p['bet_margin']:.0%} of pot."
    else:desc='Hand tiers / charts preflop; random-opponent equity with rule-based discounts and pot-odds thresholds postflop.'
    profiles.append(desc)
d['profiles']=profiles
for c in configs.values():
    c['spec'].get('valueFormat',{}).setdefault('style','decimal')
    if 'uncertainty' in c['spec']:c['spec']['uncertainty']['style']='bars'
for key in ('fast','strict','style'):(OUT/f'chart_{key}.json').write_text(json.dumps(configs[key]),encoding='utf-8')
template=VIS.read_text(encoding='utf-8')
for marker,val in [('__DATA__',d),('__FAST__',configs['fast']),('__STRICT__',configs['strict']),('__STYLE__',configs['style'])]:template=template.replace(marker,json.dumps(val).replace('<','\\u003c'))
VIS.write_text(template,encoding='utf-8')
lines=['COMPLETED SEVEN-BOT COMPARISON — 14 November 2026','', '56 league rounds + 7 enforced-deadline screening rounds, 1,000 hands each.', '63,000 table hands; 441,000 player-hand observations. Frozen sources and', 'methodology are in Tournament/manifest.json and Tournament_Method.txt.','']
for mode in ('fast','strict'):
    lines.append(mode.upper())
    for r in sorted(d[mode]['rows'],key=lambda r:-r['bb100']):
        ci=f"; approximate 95% CI [{r['bb100']-2.364624*r['se']:+.1f}, {r['bb100']+2.364624*r['se']:+.1f}]" if r['se'] is not None else '; single seed block, no CI'
        lines.append(f"{r['name']}: {r['bb100']:+.2f} bb/100{ci}; timeouts={r['timeouts']}, bank-outs={r['bankOut']}, errors={r['errors']}")
    lines.append('')
f=next(r for r in d['fast']['rows'] if r['id']==6)
lines.extend(['F leads the main league at +31.31 bb/100. Its paired advantage over E',
'is +17.71 with an approximate 95% interval of [-5.44, +40.85] bb/100;',
'over D it is +24.31 with interval [-8.51, +57.13]. These close comparisons',
'remain unresolved. Its comparisons against A/B/C and the v1 archive are',
'positive at unadjusted pairwise 95% intervals; multiple comparisons and this',
'specific field limit generalisation. Preserve F, E and D for confirmation.', ''])
base=next(r for r in d['fast']['rows'] if r['id']==1)
lines.extend(['PAIRED DIFFERENCES RELATIVE TO A_v2_safe', 'Within each seed, average the seven seat-rotation differences.'])
for r in d['fast']['rows']:
    if r['id']==1:continue
    differences=[sum(r['roundRates'][j]-base['roundRates'][j] for j in range(i,i+7))/7 for i in range(0,56,7)]
    mean=sum(differences)/8;se=math.sqrt(sum((x-mean)**2 for x in differences)/7/8)
    lines.append(f"{r['name']}: {mean:+.2f} bb/100; 95% t interval [{mean-2.364624*se:+.2f}, {mean+2.364624*se:+.2f}]")
lines.extend(['','Interpretation: ranks and intervals concern this seven-bot field only.', 'The timing screen is a local Windows check with one seed block; do not use', 'its ranking as a precise independent strength estimate. Internal bot exceptions', 'caught by act() can remain invisible to adapter error counts. No bot was modified.', 'Policy descriptions and identical-state decision probes are in summary.json.', 'Displayed equities are bot estimates with different opponent assumptions.', 'Follow up close rankings on untouched deck seeds and varied opponents.'])
(OUT.parent/'Tournament_Results.txt').write_text('\n'.join(lines),encoding='utf-8')
print('\n'.join(lines))
