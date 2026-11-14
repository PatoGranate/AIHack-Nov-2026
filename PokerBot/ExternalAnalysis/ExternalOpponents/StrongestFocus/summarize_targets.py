from pathlib import Path
from collections import Counter,defaultdict
import json,math,hashlib,re
P=Path(__file__).resolve().parent;ROOT=P.parents[2]
d=json.loads((P/'profiles.json').read_text(encoding='utf-8'))
TARGETS=['Gherkers','Attention Is All In','AAST']
def rate(k,n):
    if not n:return {'events':k,'opportunities':n,'rate':None,'wilson95':None}
    z=1.95996398454;p=k/n;v=1+z*z/n;c=(p+z*z/(2*n))/v;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/v
    return {'events':k,'opportunities':n,'rate':p,'wilson95':[c-h,c+h]}
def response(c):return {**rate(c['fold'],c['opp']),'calls':c['call'],'raises':c['raise']}
def describe(r):
    if not r['opportunities']:return '0/0 (unknown)'
    a,b=r['wilson95'];return f"{r['events']}/{r['opportunities']}={r['rate']:.1%}; Wilson95 [{a:.1%},{b:.1%}]"
def aggregate(rr):
    h=sum(r['hands'] for r in rr);chips=sum(r['chips'] for r in rr)
    fo=Counter();f3=Counter();rfi=Counter();pos=defaultdict(Counter);post=defaultdict(Counter)
    for r in rr:
        fo.update(r['foldOpenCounts']);f3.update(r['openerThreebetCounts']);rfi.update(r['rfiCounts'])
        for k,v in r['rfiPosCounts'].items():pos[k].update(v)
        for k,v in r['postCounts'].items():post[k].update(v)
    b=[r['bb100'] for r in rr];mean=chips/20/h*100 if h else None;ci=None
    if len(b)>=2:
        assert len(set(r['hands'] for r in rr))==1
        tc={1:12.70620474,2:4.30265273,3:3.182446305,4:2.776445105,5:2.570581836,6:2.446911851}.get(len(b)-1,2.365)
        se=math.sqrt(sum((v-mean)**2 for v in b)/(len(b)-1)/len(b));ci=[mean-tc*se,mean+tc*se]
    return {'hands':h,'tableRounds':len(rr),'chips':chips,'bb100_descriptive':mean,'approxRoundT95':ci,'roundRates':b,'vpip':rate(sum(r['vpipCount'] for r in rr),h),'pfr':rate(sum(r['pfrCount'] for r in rr),h),'rfi':rate(rfi['raise'],rfi['opp']),'rfiPositions':{k:rate(v['raise'],v['opp']) for k,v in pos.items()},'foldToOpen':response(fo),'openerFoldToThreebet':response(f3),'postFirstBet':{k:response(v) for k,v in post.items()}}
out={'targets':{},'provenance':[],'method':d['method'],'validation':d['validation'],'conflicts':d['conflicts']}
for t in d['datasets']:
    src=[]
    for name in t['sources']:
        f=ROOT/name;x=json.loads(f.read_text(encoding='utf-8'))
        public=hashlib.sha256(json.dumps([(h['n'],h['events'],h['results']) for h in sorted(x['hands'],key=lambda h:h['n'])],separators=(',',':'),ensure_ascii=True).encode('utf-8')).hexdigest()
        assert public==t['publicEventSha256']
        src.append({'path':name,'fileSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'publicEventSha256':public})
    t={**t,'sourceHashes':src,'period':'practice' if '/practice/' in t['ref'] else 'live'}
    out['provenance'].append(t)
for nm in TARGETS:
    rr=d['profiles'][nm]['roundResults'];versions=[]
    for r in rr:
        table=next(t for t in d['datasets'] if t['ref']==r['ref'] and t['roster']==r['roster'])
        known=sorted({re.search(r'r\dv(\d+)\.json$',s).group(1) for s in table['sources'] if re.search(r'r\dv(\d+)\.json$',s)})
        versions.append({**r,'period':'practice' if '/practice/' in r['ref'] else 'live','opponentCodeVersion':'unknown','WBotVersionContext':known,'publicEventSha256':table['publicEventSha256'],'sourcePaths':table['sources']})
    out['targets'][nm]={'all':aggregate(rr),'practice':aggregate([r for r in rr if '/practice/' in r['ref']]),'live':aggregate([r for r in rr if '/practice/' not in r['ref']]),'perRound':versions}
(P/'Target_Profiles.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
lines=['FOCUSED AUDIT: GHERKERS, ATTENTION IS ALL IN, AAST','14 November 2026','',
f"{sum(len(t['sources']) for t in d['datasets'])} source JSON files -> {len(d['datasets'])} unique table-rounds / {d['validation']['hands']:,} table hands.",
'Dedup identity: (round ref, ordered roster), then verify public-history SHA256',
'over hand number, complete events and results. All duplicate perspectives match.',
f"{len(d['duplicateSources'])} duplicate files are not counted twice. Full file/public hashes in Target_Profiles.json.",
f"All pots reconcile to awards; {d['validation']['refunds']:,} refunds processed, no recorded arithmetic",
'anomalies. Only public actions/results used; no hidden-card assumptions.',
'Opponent code versions are UNKNOWN. Dataset rNvM labels identify WBot version',
'context only, not a target opponent revision. Per-round exposure is retained.',
'Rates include counts and Wilson95 intervals; opportunities cluster by hand/table.',
'Profit t intervals are illustrative across a tiny heterogeneous round sample,',
'not a guaranteed stationary win-rate confidence bound. Practice and live stay separate.','',
'THE GHERKERS LEADERBOARD CLAIM',
'Available records are selected table perspectives, not the complete leaderboard.',
'They neither reproduce nor refute a complete tournament-wide average.',
f"This snapshot has Gherkers {out['targets']['Gherkers']['all']['bb100_descriptive']:+.2f} over {out['targets']['Gherkers']['all']['hands']:,} hands; practice {out['targets']['Gherkers']['practice']['bb100_descriptive']:+.2f} / {out['targets']['Gherkers']['practice']['hands']:,} hands;",
f"live {out['targets']['Gherkers']['live']['bb100_descriptive']:+.2f} / {out['targets']['Gherkers']['live']['hands']:,} hands. One practice round is +470.62.",
'Do not use these selected tables to overwrite the complete event average.','']
for nm,p in out['targets'].items():
    lines.extend([nm.upper(),''])
    for period in ('practice','live','all'):
        a=p[period]
        if not a['hands']:lines.append(period+': no exposure');continue
        ci=a['approxRoundT95'];cs=f"; illustrative round-t95 [{ci[0]:+.1f},{ci[1]:+.1f}]" if ci else ''
        lines.extend([f"{period}: {a['hands']} hands, {a['tableRounds']} table-rounds, {a['bb100_descriptive']:+.2f} bb/100{cs}",
          '  VPIP '+describe(a['vpip']), '  PFR '+describe(a['pfr']), '  Clean RFI '+describe(a['rfi']),
          '  Fold facing single open '+describe(a['foldToOpen']), '  Opener fold facing three-bet '+describe(a['openerFoldToThreebet'])])
        if period!='all':
            lines.append('  Clean RFI by position (table sizes kept separate):')
            lines.extend('    '+k+': '+describe(v) for k,v in sorted(a['rfiPositions'].items()))
            lines.append('  First postflop bet responses: street x original bet/pot-before-bet x HU/multiway:')
            for k,v in sorted(a['postFirstBet'].items()):lines.append('    '+k+': fold '+describe(v)+f"; calls {v['calls']}, raises {v['raises']}")
    lines.append('Per-round exposure (opponent code version unknown):')
    for r in sorted(p['perRound'],key=lambda x:(x['period'],x['ref'])):
        lines.append(f"  {r['ref']} / {len(r['roster'])} seats / {r['hands']} hands: {r['bb100']:+.2f} bb/100, VPIP {r['vpipCount']/r['hands']:.1%}, PFR {r['pfrCount']/r['hands']:.1%}; WBot version context {','.join(r['WBotVersionContext']) or 'not supplied'}")
    lines.append('')
lines.extend(['TRAINING IMPLICATIONS',
'1. Do not implement one generic strong-bot clone. Use target-specific conditional',
'   profiles, including position, response context, street and size. Preserve',
'   multiple practice/live variants as a population instead of forcing one policy.',
'2. Add less-aggressive Gherkers live variants as well as its loose/aggressive',
'   practice variants. Test early-versus-late position response before increasing',
'   wide opening or three-betting globally. Its observed profit is not a mechanism.',
'3. Preserve separate open defence and opener-versus-threebet counters. Their',
'   denominators differ; pooled folds alone cannot establish light-threebet value.',
'4. Sample AAST from its live-only profile; there is no practice evidence here.',
'   Use shrinkage for small river/size cells, and avoid zero/one-rate hardcoding.',
'5. Add check-back/delayed-aggression and raise-vs-small-bet structural variants.',
'   First-bet fold statistics do not identify what opponents do after a check or',
'   facing later raises. Do not claim those counterfactuals were observed.',
'6. Fit on practice or an earlier live subset, freeze, and confirm on later live',
'   table rounds. Keep candidate source hashes, all-seat errors and timing gates.',
'   Reusing these same outcomes to choose then validate a clone overfits the sample.',
'7. Compare exploit changes by paired chip outcomes against these diverse variants,',
'   not only whether the clone matches VPIP/PFR. Match conditional responses too.',
'8. Gherkers live: inspect current opener-threebet counts above, including calls',
'   and raises in the JSON. Train a selective opener that both calls and four-bets;',
'   a generic overfolder clone is structurally wrong. Test value-heavy responses',
'   and four-bet defence before proposing wider three-bet bluffs.',
'9. AAST live: substantial raises facing heads-up flop/turn bets remain important.',
'   Inspect current counts above. A tight preflop clone with',
'   no postflop counter-aggression would miss this behaviour. Add raise pressure',
'   and test the candidate\'s response to it, preserving size/board uncertainty.',
'10. Attention live: use current street-specific first-bet fold counts above,',
'   with strong shrinkage on the small river sample. Opener fold-to-threebet',
'   frequency is a targeted',
'   hypothesis, not permission to reactivate globally losing light-threebet logic.',
'', 'No playing code modified. Reports are UTF-8; complete source provenance retained.'])
(P/'Strongest_Bots_Review.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for f in P.glob('*'):
    if f.is_file():f.read_bytes().decode('utf-8',errors='strict')
print('Target reports written; public hashes verified for all source perspectives; strict UTF-8 passed.')
