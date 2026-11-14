from pathlib import Path
import json
P=Path(__file__).resolve().parent
d=json.loads((P/'profiles.json').read_text(encoding='utf-8'))
external=d['profilesBySourceGroup']['external'];combined=d['profiles']
def fmt(r):
    if not r['opportunities']:return '0/0; unknown'
    a,b=r['wilson95'];return f"{r['events']}/{r['opportunities']} = {r['rate']:.1%} (Wilson95 {a:.1%}..{b:.1%})"
lines=['EXTERNAL OPPONENTS: STRUCTURAL FINDINGS','14 November 2026','',
'SCOPE AND DEDUPLICATION',
'New other-table data: 5 files, 5,000 table hands, 21 distinct names, 6/7/8-seat tables.',
'Combined with 7 own-table files: 11 unique table-rounds / 11,000 table hands /',
'29 names. Dedup key is (round ref, ordered player roster), not round ref alone.',
'External r015 and own r1v3 are the same table from different perspectives:',
'identical public events/results, counted once globally. No public conflicts.',
'Source subgroups intentionally overlap on that shared table; do not sum their',
'exposures. This report labels external-only versus combined estimates explicitly.',
'Pot reconstruction: raises total-to, calls/posts incremental, refunds subtract.',
'All 11,000 pots reconcile to awards; no negative/overstack contributions or',
'nonzero-sum chip results. 8,321 refunds processed. No hidden cards were used.','',
'1. GENERAL FOLD-TO-OPEN IS NOT OPENER FOLD-TO-THREEBET',
'This is directly visible in public actions. The combined estimates use historical',
'own + external observations; external-only estimates isolate the new 5 files.']
for nm in ('Durahim 1453','Claudebot','FisherMen','Lehman Brothers','Attention Is All In','gamblerlove','YSL_TWIZZY'):
    lines.extend(['',nm])
    for label,profiles in [('External only',external),('Combined unique tables',combined)]:
        p=profiles[nm];lines.append(f"  {label}: {p['hands']} hands; fold vs single open {fmt(p['foldToSingleOpen'])}; opener fold vs three-bet {fmt(p['openerFoldToThreebet'])}")
lines.extend(['','Clone recommendation: preserve opportunity conditioning. Durahim can be highly',
'selective against opens while strongly defending hands it opens. FisherMen and',
'Lehman exhibit the same general issue. A single generic fold threshold cannot',
'faithfully represent both situations. Split cold/limp defence from opener defence',
'and retain sample-aware priors. These rates do not reveal unseen holding ranges.','',
'2. OVERBET FOLD RESPONSE HAS LITTLE GENERAL SUPPORT',
'External-only heads-up river, first bet >1 pot:'])
for nm,p in sorted(external.items()):
    r=p['postflopFirstBetResponse'].get('river >1.0 HU')
    if r:lines.append('  '+nm+': '+fmt(r)+f"; calls={r['calls']}, raises={r['raises']}")
lines.extend(['Most cells have 1-6 opportunities. Lehman Brothers has 0 folds in 17,',
'which supports a low-fold response hypothesis for that historical exposure,',
'not a field-wide overbet rule. The mean of player percentages would overweight',
'tiny cells. Do not infer complete size curves or make universal overbet claims.','',
'3. TINY BETS: OBSERVE CALL/RAISE RESPONSE, NOT JUST FOLD RATE',
'External-only heads-up flop, first bet <=0.33 pot:'])
for nm in ("Mohil'sPokerBot",'Lehman Brothers','Phil AIvey','kaiserbot','Claudebot'):
    r=external[nm]['postflopFirstBetResponse'].get('flop <=0.33 HU')
    if r:lines.append('  '+nm+': '+fmt(r)+f"; calls={r['calls']}, raises={r['raises']}")
lines.extend(['Low folds to small bets can support thin value while undermining air bluffs.',
'Category/range composition and chosen-bet selection confound this inference.',
'Add opponents with small-bet raises and size-insensitive calls, not only jittered',
'ParamBot thresholds. Full per-street/size HU/multiway counts are in profiles.json.','',
'4. HISTORICAL MIX AND ROUND DRIFT',
'Same display name need not mean unchanged policy across practice rounds. WBot',
'definitely represents multiple versions. Field composition can also cause drift.',
'The following external-only histories show >=15 percentage-point VPIP range or',
'>=12 percentage-point PFR range; these are behavioural changes, not causal proof',
'of code changes:'])
drifts=[]
for nm,p in combined.items():
    rr=[r for r in p['roundResults'] if 'external' in r['groups']]
    if len(rr)<2:continue
    vv=[r['vpipCount']/r['hands'] for r in rr];pp=[r['pfrCount']/r['hands'] for r in rr]
    if max(vv)-min(vv)>=.15 or max(pp)-min(pp)>=.12:
        drifts.append(nm);lines.append('  '+nm+': '+'; '.join(f"{r['ref'].split('/')[-1]} VPIP {r['vpipCount']/r['hands']:.1%}, PFR {r['pfrCount']/r['hands']:.1%}" for r in rr))
if not drifts:lines.append('  None cross those descriptive thresholds in the external-only subset.')
lines.append('Largest external-only VPIP spreads below/alongside that screen:')
histories=[]
for nm,p in combined.items():
    rr=sorted([r for r in p['roundResults'] if 'external' in r['groups']],key=lambda r:r['ref'])
    if len(rr)>1:histories.append((max(r['vpipCount']/r['hands'] for r in rr)-min(r['vpipCount']/r['hands'] for r in rr),nm,rr))
for spread,nm,rr in sorted(histories,key=lambda x:-x[0])[:3]:
    lines.append('  '+nm+': '+'; '.join(f"{r['ref'].split('/')[-1]} VPIP {r['vpipCount']/r['hands']:.1%}, PFR {r['pfrCount']/r['hands']:.1%}" for r in rr))
lines.extend(['WBot combined version history (do not treat as one stable opponent):'])
for r in combined['WBot']['roundResults']:
    lines.append(f"  {r['ref'].split('/')[-1]}: VPIP {r['vpipCount']/r['hands']:.1%}; PFR {r['pfrCount']/r['hands']:.1%}; {r['bb100']:+.1f} bb/100")
lines.extend(['','LIMITS',
'Wilson intervals describe opportunity counts and do not model table/hand clustering.',
'Profit figures are descriptive, with different table fields and policy versions.',
'No net-winnings ranking establishes universal skill; no counterfactual responses',
'to unchosen sizes can be recovered from these public histories. First-bet response',
'buckets exclude facing later raises and distinguish heads-up from multiway.',
'All-position RFI denominators mean no earlier raise OR limper; opening/isolating',
'over limpers is a separate context, not silently counted as a clean open.'])
(P/'Structural_Findings.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(P/'Structural_Findings.txt').read_bytes().decode('utf-8',errors='strict')
print('Wrote Structural_Findings.txt with',len(lines),'lines; UTF-8 strict validation passed.')
