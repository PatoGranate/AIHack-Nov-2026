"""Replay real rounds through the v3 identification and compare its reads with the true seat names.

    python tools/check_ident.py                     # our latest round
    python tools/check_ident.py hands/saturday_r044.json hands/external/WBot/saturday_r044.json

The model is rebuilt from rounds BEFORE each replayed round (what the live bot had), and
the bot sees exactly what it saw live: the hand-end history of every hand.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pokerbot.v2 as v2  # noqa: E402
from tools.build_v3_model import build, slot_ts  # noqa: E402

STREET = {"flop": "flop", "turn": "turn", "river": "river"}


def histories(hand):
    hist, street, posts = [], "preflop", 0
    for e in hand["events"]:
        if e[0] == "post":
            hist.append({"seat": e[1], "street": "preflop", "action": "small_blind" if posts == 0 else "big_blind",
                         "amount": e[2]})
            posts += 1
        elif e[0] == "board":
            street = STREET[e[1]]
        elif e[0] == "act":
            hist.append({"seat": e[1], "street": street, "action": e[2], "amount": e[3]})
    shown = {k: v for k, v in hand.get("hole", {}).items() if k in (hand.get("showdown") or {})}
    return {"history": hist, "board": hand.get("board") or [], "shown": shown}


def check(path, checkpoints=(25, 50, 100, 250, 1000)):
    d = json.load(open(path, encoding="utf-8"))
    meta = d.get("round") or {}
    model = build(before=slot_ts(meta))
    v2.MODEL.clear()
    v2.MODEL.update(model)
    v2._MODEL_SRC[0] = None
    params = json.load(open(os.path.join(ROOT, "data", "v2_params.json")))
    a = v2.Agent(params=dict(params, ident=1))
    a.on_table_start({"seat": d["seat"], "num_players": len(d["players"]), "hands": len(d["hands"])})
    players = d["players"]
    print("\n%s  (%s, model built from rounds up to %s)" % (os.path.relpath(path, ROOT), meta.get("slot", "?")[11:16],
                                                           model["latest_round"]))
    known = set(model["bots"])
    rows = {s: [] for s in range(len(players)) if s != d["seat"]}
    for i, h in enumerate(d["hands"], 1):
        a._learn(histories(h))
        if i in checkpoints:
            for s in rows:
                ll = a.idll.get(s)
                if not ll:
                    rows[s].append("-")
                    continue
                q = a.post.get(s, {})
                best = max((b for b in ll if b != "_pop"), key=lambda b: ll[b])
                rows[s].append("%s%s %.2f" % ("OK " if best == players[s] else "", best[:14], q.get("_conf", 0)))
    print("  %-24s " % "true seat" + "".join("%-22s" % ("after %d" % c) for c in checkpoints))
    hit = 0
    for s, r in rows.items():
        tag = "" if players[s] in known else "  (not in model: new/rare bot)"
        print("  %-24s " % players[s][:24] + "".join("%-22s" % x for x in r) + tag)
        hit += r[-1].startswith("OK")
    print("  identified at the end: %d of %d (%d of them in the model)" % (hit, len(rows), sum(p in known for i, p in enumerate(players) if i in rows)))


if __name__ == "__main__":
    files = sys.argv[1:] or [sorted(glob.glob(os.path.join(ROOT, "hands", "saturday_r*.json")))[-1]]
    for f in files:
        check(f)
