"""Fail-closed checks before tuning or promoting against the replacement field."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def check(report, root=ROOT):
    reasons=[]
    for rel,digest in report['hashes'].items():
        if hashlib.sha256((root/rel).read_bytes()).hexdigest()!=digest:
            reasons.append('changed artifact: '+rel)
    base=report['baseline']
    if base['hands']<16000:reasons.append('fewer than 16000 baseline hands')
    for key,target in report['real_frequencies'].items():
        actual=base['field_frequencies'].get(key)
        if target is not None and (actual is None or abs(actual-target)>.06):
            reasons.append('frequency mismatch: '+key)
    for key,target in report['real_strength'].items():
        if target['n']<20:continue
        observed=base['strength'].get(key,{})
        if observed.get('n',0)<20:
            reasons.append('insufficient showdown-strength sample: '+key)
        elif abs(observed['strong']-target['strong'])>.15:
            reasons.append('strength mismatch: '+key)
    # Rare river overbets need positive evidence, not a silent skip.
    for key in ('river/bet/7','river/raise/6'):
        if base['strength'].get(key,{}).get('n',0)<20:
            reasons.append('insufficient river calibration: '+key)
    for key in ('bb100','sd_bb100'):
        tolerance=max(15.,2*(base.get('table_se',0)**2+(report['real'].get(key+'_se') or 0)**2)**.5)
        if abs(base[key]-report['real'][key])>tolerance:
            reasons.append('baseline does not reproduce held-out '+key)
    bc=base.get('call_equity',{});rc=report['real'].get('call_equity',{})
    if min(bc.get('n',0),rc.get('n',0))<30:
        reasons.append('insufficient revealed-hand big-call equity sample')
    elif abs(bc['equity_sum']/bc['n']-rc['equity_sum']/rc['n'])>.10:
        reasons.append('big-call equity mismatch')
    return dict(approved=not reasons,reasons=reasons)


if __name__=='__main__':
    result=check(json.loads(Path(sys.argv[1]).read_text()))
    print(json.dumps(result,indent=2))
    sys.exit(0 if result['approved'] else 1)
