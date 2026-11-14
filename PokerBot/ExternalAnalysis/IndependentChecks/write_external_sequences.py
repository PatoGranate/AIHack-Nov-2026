import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
selection={
 'r014':[(568,'Market Makers top pair versus bigRoddy gutshot/overcards, full flop stack-off.'),(718,'Market Makers set; late tiny fraction is all remaining chips.'),(362,'Counterexample: Market Makers QTs top pair loses full stack to bigRoddy AQ.')],
 'r015':[(492,'Phil AIvey turns two pair versus FisherMen one pair; turn stack-off.')],
 'r016':[(893,'Gherkers 66 river shove called by Lehman A3 high card; success.'),(963,'Gherkers A5 river shove called by Lehman K7; success.'),(978,'Counterexample: Gherkers 95 river shove called by Lehman KK; failure.'),(242,'Counterexample: Gherkers TT river shove runs into Lehman K9 straight.')],
 'r017':[(500,'Durahim turns set; river 405 bet is the entire remaining stack, not evidence of deliberate tiny sizing.'),(694,'Durahim flops two pair and calls flop reraise; turn 578 is its entire remaining stack.'),(258,'Market Makers KQ top pair calls Lehman large flop reraise and small turn all-in.'),(115,'Counterexample: Durahim AJ four-bet/calls preflop and loses to Lehman AQ.'),(979,'Kojack AK trips with stronger kicker than GamesGone A9; turn stack-off.'),(441,'Kojack T9 draw flop raise then turned straight stack-off versus GamesGone JT.')]
}
lines=['EXTERNAL TABLES — EXACT VISIBLE HAND SEQUENCES','',
       'UTF-8. Raise amounts are street-total RAISE TO; call amounts are increments.',
       'Pot/remaining-stack values below are reconstructed immediately before each act.',
       'Only cards present in the JSON are listed. Unknown hidden cards remain unknown.',
       'kaiserbot is the source viewpoint and has its own hole cards even when it folds.',
       'For other actors, listed cards generally come from visible showdown data.',
       'Round refs identify time, not unique tables; identity is (ref, ordered roster).',
       'These are deliberately selected illustrative wins AND failures, not an unbiased',
       'performance sample. r015 is an alternate viewpoint of the WBot v3 table; do not',
       'count its action/results a second time when combining datasets.','']
for ref,cases in selection.items():
 f=next((ROOT/'Hand_data/ExternalData_OtherBots').glob('*'+ref+'.json'))
 d=json.loads(f.read_text(encoding='utf-8'));names=d['players']
 lines.extend(['='*76,'FILE '+str(f.relative_to(ROOT)),'REF '+d['ref'],'ROSTER '+json.dumps(dict(enumerate(names)),ensure_ascii=False),''])
 for n,note in cases:
  h=next(x for x in d['hands'] if x['n']==n);total=[0]*len(names);bets=[0]*len(names);pot=0;street='preflop'
  lines.extend(['HAND '+str(n)+' — '+note,'Button '+str(h['button'])+'; board '+str(h['board']),
    'VISIBLE CARDS '+json.dumps({names[int(k)]:v for k,v in h['hole'].items()},ensure_ascii=False),
    'SHOWDOWN '+json.dumps({names[int(k)]:v for k,v in h.get('showdown',{}).items()},ensure_ascii=False)])
  for e in h['events']:
   if e[0]=='board':street=e[1];bets=[0]*len(names);lines.append('  '+street.upper()+' '+str(e[2]))
   elif e[0]=='post':s,x=e[1:];total[s]+=x;bets[s]+=x;pot+=x;lines.append(f'  {names[s]} posts {x}')
   elif e[0]=='act':
    _,s,a,x=e;add=x-bets[s] if a=='raise' else x if a=='call' else 0
    desc=f'raise TO {x} (adds {add})' if a=='raise' else f'{a} {x}' if a=='call' else a
    lines.append(f'  {names[s]}: {desc}; pot before={pot}; stack before={2000-total[s]}')
    total[s]+=add;bets[s]+=add;pot+=add
   elif e[0]=='refund':s,x=e[1:];pot-=x;total[s]-=x;lines.append(f'  Refund {names[s]} {x}')
   elif e[0]=='win':lines.append(f'  Award {names[e[1]]}: {e[2]} ({e[3]})')
  lines.extend(['NET RESULTS '+json.dumps(dict(zip(names,h['results'])),ensure_ascii=False),''])
(HERE/'External_Visible_Hand_Sequences.txt').write_text('\n'.join(lines),encoding='utf-8')
print('Wrote',sum(len(x) for x in selection.values()),'complete visible sequences')
