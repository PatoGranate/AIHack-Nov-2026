"""Separate ablation: cold V4 plus two chip-accounting corrections.

Does not assert an EV improvement. No heuristic threshold tuning or live writes.
"""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from sunday.export_identity import export


def replace_once(src,old,new):
    if src.count(old)!=1:raise ValueError('unexpected source marker: '+old)
    return src.replace(old,new,1)


def build():
    src=export().read_text(encoding='utf-8')
    src=replace_once(src,'if rks is not None and not allin and rks[ci] > 0:',
        'if rks is not None and not allin and rks[ci] > 0 and cands[ci] < min(cap_j, getattr(self, "my_stack", 0) + my_bet):')
    src=replace_once(src,'raised = sh * (pot + 2 * a2) - a2',
        'raised = sh * (pot + a2 + max(0, my_bet + a2 - models[0][6])) - a2')
    path=ROOT/'sunday/v4_cold_accounting_bot.py';compile(src,str(path),'exec');path.write_text(src,encoding='utf-8')
    (ROOT/'sunday/accounting_manifest.json').write_text(json.dumps(dict(status='untested_profit_ablation',
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),fixes=['no phantom raise after effective all-in',
        'raised branch subtracts opponent chips already included in pot']),indent=2))
    return path


if __name__=='__main__':print(build())
