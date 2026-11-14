from pathlib import Path
import json
P=Path(__file__).resolve().parent
d=json.loads((P/'profiles.json').read_text(encoding='utf-8'))
t=json.loads((P/'Target_Profiles.json').read_text(encoding='utf-8'))
old=json.loads((P/'Target_Profiles_before_r006_r007.json').read_text(encoding='utf-8'))
leader={'Gherkers':86.0,'Attention Is All In':62.8,'AAST':51.0,'Equity Engine':40.8,'WBot':35.4}
compare=[]
for nm,official in leader.items():
    rr=[r for r in d['profiles'][nm]['roundResults'] if '/practice/' not in r['ref']]
    h=sum(r['hands'] for r in rr);chips=sum(r['chips'] for r in rr);local=chips/20/h*100
    compare.append({'name':nm,'leaderboardBb100_userScreenshot':official,'leaderboardHands':7000,'localLiveHands':h,'localLiveTableRounds':len(rr),'localLiveBb100':local,'localMinusScreenshot':local-official,'missingTableRounds':7-len(rr),'liveRounds':[r['ref'] for r in rr]})
changes=[]
for nm,p in t['targets'].items():
    new=[r for r in p['perRound'] if r['ref'] in ('saturday/r006','saturday/r007')]
    changes.append({'name':nm,'newExposure':new,'beforeLive':old['targets'][nm]['live'],'afterLive':p['live']})
result={'source':'User-provided current leaderboard screenshot, supplied values; not independently queried online','leaderboardComparison':compare,'newTargetExposures':changes,'dedup':{'files':sum(len(x['sources']) for x in d['datasets']),'uniqueTableRounds':len(d['datasets']),'hands':d['validation']['hands'],'duplicateCopies':len(d['duplicateSources']),'conflicts':len(d['conflicts'])}}
(P/'Live_Leaderboard_Comparison_r007.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
def frac(x):return f"{x['events']}/{x['opportunities']} ({x['rate']:.1%})" if x['rate'] is not None else '0/0 unknown'
lines=['LIVE LEADERBOARD RECONCILIATION AFTER R006/R007','14 November 2026','',
'The screenshot supplied by the user gives seven counted rounds / 7,000 hands',
'for every listed bot. It is the broader performance source; the local hand',
'sample covers selected tables, except WBot now has all seven own rounds.',
'Practice results are excluded from every local value in the comparison below.',
'Screenshot values are transcribed observations, not independently queried online.','',
'Name | Screenshot bb/100 over 7k | Local live bb/100 | Local coverage | Missing rounds']
for r in compare:lines.append(f"{r['name']} | {r['leaderboardBb100_userScreenshot']:+.1f} | {r['localLiveBb100']:+.2f} | {r['localLiveHands']:,} hands / {r['localLiveTableRounds']} rounds | {r['missingTableRounds']}")
lines.extend(['',
'WBot: local +35.4207 rounds to screenshot +35.4, a useful reconciliation check.',
'The other differences are NOT discrepancies proven in the leaderboard: their',
'local coverage is incomplete and selected by available table perspectives.',
'Do not average the screenshot rate with the overlapping local rate or mix in',
'practice hands. Do not replace +86/+62.8/+51/+40.8 with incomplete local averages.',
'Gherkers +86 updates the earlier approximate +85 claim; neither is contradicted',
'by a different selected-table average. No universal skill change is inferred.','',
f"Current inventory: {result['dedup']['files']} files -> {result['dedup']['uniqueTableRounds']} unique table-rounds / {result['dedup']['hands']:,} hands; {result['dedup']['duplicateCopies']} duplicate perspectives; 0 public-hash conflicts.",
'R006 WBot and kaiserbot are the SAME ordered-roster table, counted once.',
'Other equal round refs with different ordered rosters remain distinct tables.',
'Full public-history and file hashes remain in Target_Profiles.json.','',
'NEW TARGET EXPOSURES'])
for c in changes:
    nm=c['name'];lines.append(nm)
    if not c['newExposure']:lines.append('  No new r006/r007 local exposure. Existing target estimates unchanged.')
    for r in c['newExposure']:
        lines.append(f"  {r['ref']}: {r['hands']} hands, {r['bb100']:+.3f} bb/100; VPIP {r['vpipCount']}/{r['hands']}={r['vpipCount']/r['hands']:.1%}, PFR {r['pfrCount']}/{r['hands']}={r['pfrCount']/r['hands']:.1%}.")
        fo=r['foldOpenCounts'];f3=r['openerThreebetCounts'];lines.append(f"  Single-open defence: folds {fo.get('fold',0)}/{fo.get('opp',0)}; opener vs three-bet folds {f3.get('fold',0)}/{f3.get('opp',0)}, calls {f3.get('call',0)}, raises {f3.get('raise',0)}.")
    a=c['afterLive'];b=c['beforeLive'];lines.append(f"  Live VPIP {frac(b['vpip'])} -> {frac(a['vpip'])}; PFR {frac(b['pfr'])} -> {frac(a['pfr'])}.")
    lines.append(f"  Live opener folds vs three-bet {frac(b['openerFoldToThreebet'])} -> {frac(a['openerFoldToThreebet'])}.")
    lo,hi=a['openerFoldToThreebet']['wilson95'];lines.append(f"  Updated opener-fold Wilson95 [{lo:.1%},{hi:.1%}]; opportunity clusters and changing contexts still matter.")
lines.extend(['','TRAINING PRIORITIES AND V7',
'The new selected rounds refine target profiles; they do not warrant replacing',
'the v7 policy from unlike-table profit comparisons. Preserve frozen v7,',
'its promotion evidence and rollback baseline. No direct v7-versus-target',
'counterfactual performance can be inferred from target net results alone.',
'Gherkers remains a selective live opener with meaningful call/four-bet defence;',
'keep it structurally separate from blind overfolders and aggressive practice variants.',
'Attention needs conditional opener-defence and street/size models, not one global',
'fold rate. Preserve fresh held-out confirmation before enabling targeted exploits.',
'AAST received no new exposure, so retain its tight preflop / active postflop',
'raising archetype with uncertainty. The screenshot validates its broad strong',
'standing, not a particular inferred mechanism.',
'Use new public action counts as additional training-data candidates, holding out',
'later rounds to assess calibration. Do not train and test on the same r007 responses.',
'Full practice/live action profiles and Wilson intervals are in Strongest_Bots_Review.txt;',
'the before-r006/r007 report/JSON are preserved for audit. All reports are UTF-8.'])
(P/'Live_Leaderboard_Comparison_r007.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for f in P.glob('*'):
    if f.is_file():f.read_bytes().decode('utf-8',errors='strict')
print('\n'.join(lines[:22]));print('Strict UTF-8 validation passed.')
