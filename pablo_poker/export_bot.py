"""Write the current champion into bot.py (the single file you upload).

    python export_bot.py                    # champion -> bot.py
    python export_bot.py --strategy s-1234  # a specific strategy id
    python export_bot.py --out my_bot.py

bot.py = pokerbot/strategy.py with DEFAULT_PARAMS replaced by the champion's
parameters. Then check it under real tournament limits:

    python local_sim.py bot.py --rounds 5
"""
import argparse
import os
import pprint
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from rsi import registry  # noqa: E402
from storage import db as store  # noqa: E402


def render(params, sid, generation):
    src = open(os.path.join(ROOT, "pokerbot", "strategy.py"), encoding="utf-8").read()
    body = pprint.pformat(params, indent=4, width=100, sort_dicts=True)
    block = ("# champion %s, generation %d (exported by export_bot.py)\nDEFAULT_PARAMS = %s\n" % (sid, generation, body))
    new, n = re.subn(r"^DEFAULT_PARAMS = \{.*?^\}\n", block, src, count=1, flags=re.M | re.S)
    if n != 1:
        raise RuntimeError("could not find DEFAULT_PARAMS in strategy.py")
    return new


def export(db, strategy_id=None, out=None):
    s = store.load_strategy(db, strategy_id) if strategy_id else registry.champion(db)
    if s is None:
        raise SystemExit("unknown strategy %s" % strategy_id)
    from pokerbot.strategy import DEFAULT_PARAMS
    params = dict(DEFAULT_PARAMS, **s["params"])
    for k in ("mc_iters", "mc_ms", "explore"):         # compute/data settings are not strategy: always the current defaults
        params[k] = DEFAULT_PARAMS[k]
    out = out or os.path.join(ROOT, "bot.py")
    src = render(params, s["id"], s["generation"])
    compile(src, out, "exec")
    with open(out, "w", encoding="utf-8") as f:
        f.write(src)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strategy", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args()
    db = store.connect(a.db)
    registry.ensure_champion(db)
    print("wrote", export(db, a.strategy, a.out))


if __name__ == "__main__":
    main()
