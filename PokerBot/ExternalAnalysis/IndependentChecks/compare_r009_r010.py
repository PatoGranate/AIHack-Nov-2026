from pathlib import Path
from collections import defaultdict
import json
P=Path(__file__).resolve().parent;ROOT=P.parents[1]
audits={9:json.loads((P/'Round9TableE/Round9_Audit.json').read_text(encoding='utf-8')),10:json.loads((P/'Round10Audit/Round10_Audit.json').read_text(encoding='utf-8'))}
cum=[]
for i in range(1,11):
    f=ROOT/f'Hand_data/SaturdayRealRounds/saturday_r{i:03}.json';d=json.loads(f.read_text(encoding='utf-8'));s=d['players'].index('WBot');chips=sum(h['results'][s]for h in d['hands'])
    cum.append({'ref':d['ref'],'hands':len(d['hands']),'chips':chips,'bb100':chips/20/len(d['hands'])*100,'roundMetadataPresent':bool(d.get('round')),'roundMetadata':d.get('round')})
out={'rounds':{},'cumulative':{'hands':sum(r['hands']for r in cum),'chips':sum(r['chips']for r in cum),'perRound':cum}}
out['cumulative']['bb100']=out['cumulative']['chips']/20/out['cumulative']['hands']*100
lines=['ROUND 9 / ROUND 10 COMPARISON AND CUMULATIVE RECONCILIATION','14 November 2026','',
f"All ten own-table records: {out['cumulative']['chips']:+,} chips / {out['cumulative']['hands']:,} hands = {out['cumulative']['bb100']:+.4f} bb/100, rounding to screenshot +10.0.",
'Raw round 9 is -16,329 chips / -81.645 bb/100, rounding to cited -81.6.',
'Raw round 10 is -14,278 chips / -71.390 bb/100, rounding to -71.4.',
'R001-r007 retain API metadata (version 5, runtime summaries). R008-r010 do not.',
'No verified table letter, deployed version/hash, timeout/error/bank-out statistics',
'are attached to r009/r010. Do not infer that absence means zero incidents.',
'The earlier data-availability note was superseded when these raw files arrived.','',
'MAIN DECOMPOSITION']
for rnd,a in audits.items():
    groups=a['groups'];winner=defaultdict(lambda:{'losingHands':0,'grossHeroLoss':0});patterns=defaultdict(lambda:{'hands':0,'chips':0})
    for r in a['rows']:
        if r['result']<0:
            names=sorted(set(r['winners'])-{'WBot'});key=' + '.join(names) or 'no nonhero winner recorded';winner[key]['losingHands']+=1;winner[key]['grossHeroLoss']-=r['result']
        bc=0;over=False;raisebet=False
        for street in ('flop','turn','river'):
            acts=[x for x in r['heroActions']if x['street']==street];hasbet=False;found=False
            for x in acts:
                if x['action']=='raise':
                    hasbet=True
                    if x['toCall']>0:raisebet=True
                    if x['added']-x['toCall']>x['potBefore']+x['toCall']:over=True
                if x['action']=='call' and hasbet:found=True
            bc+=found
        for key,yes in [('bet/call on at least two streets',bc>=2),('postflop raise while facing bet',raisebet),('postflop over-pot bet/raise increment',over)]:
            if yes:patterns[key]['hands']+=1;patterns[key]['chips']+=r['result']
    out['rounds'][str(rnd)]={'groups':groups,'winnerContexts':dict(winner),'patterns':dict(patterns),'roster':a['players']}
    lines.extend([f"Round {rnd} ({len(a['players'])} seats):",'  Roster: '+', '.join(a['players']),f"  SD: {groups['showdown:True']['hands']} hands / {groups['showdown:True']['chips']:+,} chips; non-SD: {groups['showdown:False']['hands']} / {groups['showdown:False']['chips']:+,}.",f"  WBot pre-refund full-stack attempts: {groups['allin:True']['hands']} / {groups['allin:True']['chips']:+,}; no such attempt: {groups['allin:False']['hands']} / {groups['allin:False']['chips']:+,}.",f"  Full-stack losses {a['fullStackLosses']}; gross losses {a['grossLoss']:,}; gross wins {a['grossWin']:,}.",f"  Top10 losses {a['top10Loss']:,} ({a['top10Loss']/a['grossLoss']:.1%} of gross loss)."])
    lines.append('  Mutually exclusive FINAL contribution categories (after refunds):')
    finalcats={k:groups['finalRisk:'+k]for k in ('WBot full stack','opponent-only full stack','neither')}
    assert sum(g['hands']for g in finalcats.values())==1000
    assert sum(g['chips']for g in finalcats.values())==a['chips']
    for k,g in finalcats.items():lines.append(f"    {k}: {g['hands']} hands / {g['chips']:+,} chips.")
    refunded=[r for r in a['rows']if r['allin']is not None and r['finalRiskCategory']!='WBot full stack']
    lines.append(f"  Attempt-count excess: {len(refunded)} uncalled/refunded WBot shove attempts, net {sum(r['result']for r in refunded):+,}; not actual 2,000-chip exposure.")
    actualturn=[r for r in a['rows']if r['finalRiskCategory']=='WBot full stack' and r['allin']['street']=='turn']
    lines.append(f"  Actual WBot full-stack turn risk: {len(actualturn)} hands / {sum(r['result']for r in actualturn):+,} chips.")
    out['rounds'][str(rnd)]['finalRiskCategories']=finalcats
    for key,g in patterns.items():lines.append(f"  {key}: {g['hands']} hands / {g['chips']:+,} net chips.")
    lines.append('  Opponent WINNER CONTEXT for hero losing hands (not exact chip transfers):')
    for nm,g in sorted(winner.items(),key=lambda x:-x[1]['grossHeroLoss']):lines.append(f"    {nm}: {g['losingHands']} losing hands / {g['grossHeroLoss']:,} gross hero loss in those hands.")
lines.extend(['','VARIANCE / COOLERS THAT ARE OBSERVABLE',
'Round9 h145: KT top two on K-T-2 flop lost to AA after a 72.9% revealed-hand',
'runout equity; h915 AK lost from about 73.9% preflop (12k seeded samples);',
'h957 KT lost from 93.2% on turn (44 exact rivers).',
'Round10 h276 QQ lost from 88.6% on turn; h317 A2 from 75.0%; h865 KJ hearts',
'from 86.4% on turn, all exact 44-river enumeration against revealed contestants.',
'These are genuine adverse runouts conditioned on actual shown cards, not proof',
'the sizes or earlier range decisions were optimal. Unknown folded cards ignored.',
'Do not compute an unbiased all-in-adjusted win rate by looking only at losses:',
'favourable runouts in winning all-ins also exist and must be included for that aim.','',
'DECISION PATTERNS THAT WARRANT TESTS',
'R009 h60 QQ and h509 QJ repeatedly bet/call raises on flop, turn and river,',
'then lose 2,000 each to ND. h178 99 bet/calls turn and river versus Astra and',
'loses 1,235. These are evidence of a recurring line, not proof every call was bad.',
'R009 h333 AQ re-shoves turn after a flop bet/call; revealed-hand equity is zero.',
'That failed bluff still requires ex-ante fold-equity/range analysis.',
'R010 h420 K8 and h469 KJ raise flop and commit turn versus kaiserbot; shown-hand',
'turn equities are 9.1% and 13.6%. h124 AK raises a flop bet to all-in with 5.5%',
'against Mohil\'s revealed hand. h955 QJ turns two pair into a large shove while',
'the actual called hand leaves 4.5%; consider cooler/range composition and sizing.',
'A bluff that is called by a strong hand is not thereby always unprofitable.',
'Round10 turn all-in attempt segment is 17 attempts / -11,353 chips (including',
'uncalled/refunded attempts; actual final-risk subtotal is given above), while round9',
'showdowns without all-in are -8,937. The two losses have different compositions;',
'a single global tightening reaction is not justified.','',
'ACTIONABLE PAIRED TEST, NOT AN IMMEDIATE LIVE SWITCH',
'Freeze the actual deployed baseline hash once metadata confirms it. Compare one',
'candidate at a time: (A) sequential street-aware opponent action likelihoods /',
'stronger conditional range updates after repeated raises; (B) reduced commitment',
'for marginal made hands and weak semi-bluffs against observed continuing ranges;',
'(C) size-menu change tested separately from range changes. No hand-specific rules.',
'Use r009/r010 as diagnostic fixtures for state/range/EV accounting, not a training',
'set then a confirmatory test. Confirm on untouched seeds and diverse structurally',
'different opponents; all-seat errors, 1,000-hand time banks and deployed-build',
'parity remain gates. Include failed bluff/value opportunities as well as savings.',
'Retain v7/G and rollback until fresh paired chip EV evidence warrants promotion.',
'No playing code changed; exact hand lines/equities and source hashes are in the',
'per-round audit JSON/TXT. All amounts include refunds correctly.'])
(P/'R009_R010_Comparison.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
(P/'R009_R010_Comparison.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for p in (P/'R009_R010_Comparison.json',P/'R009_R010_Comparison.txt'):p.read_bytes().decode('utf-8','strict')
print('\n'.join(lines[:24]));print('UTF-8 validated.')
