"""Ground truth: what each kind of decision of OUR bot actually won or lost on the real tables.

    python tools/real_leaks.py                 # all our rounds
    python tools/real_leaks.py --recent 3      # only the last 3 rounds

For every spot (river call vs a bet, flop c-bet, facing a 3-bet, steal, ...)
it reports how often it happened and the average result of those hands in big
blinds, so a leak shows up as a spot that loses money.
"""
import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from rsi.evolution import round_key  # noqa: E402


def analyse(files):
    spots = {}

    def add(name, bb):
        s = spots.setdefault(name, [0, 0.0])
        s[0] += 1
        s[1] += bb

    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        me, n = d["seat"], len(d["players"])
        for h in d["hands"]:
            res = h["results"][me] / 20.0
            street, acts = "preflop", {"preflop": [], "flop": [], "turn": [], "river": []}
            for e in h["events"]:
                if e[0] == "board":
                    street = e[1]
                elif e[0] == "act":
                    acts[street].append((e[1], e[2]))
            pf = acts["preflop"]
            raises = [i for i, a in enumerate(pf) if a[1] == "raise"]
            off = (me - h["button"]) % n
            pos = {0: "BTN", 1: "SB", 2: "BB"}.get(off, "CO" if off == n - 1 else "EP/MP")
            add("all hands", res)
            add("position " + pos, res)
            mine = [(i, a) for i, (x, a) in enumerate(pf) if x == me]
            if not mine:
                continue
            first_i, first_a = mine[0]
            before = sum(1 for (_, a) in pf[:first_i] if a == "raise")
            limpers = sum(1 for (_, a) in pf[:first_i] if a == "call")
            if before == 0 and limpers == 0 and first_a == "raise":
                add("open-raise (%s)" % ("steal CO/BTN/SB" if pos in ("CO", "BTN", "SB") else "EP/MP/BB"), res)
            if before == 1:
                add("facing 1 raise: %s" % first_a, res)
            if len(raises) >= 2 and pf[raises[0]][0] == me:
                resp = next((a for (x, a) in pf[raises[1] + 1:] if x == me), None)
                if resp:
                    add("I opened, got 3-bet: %s" % resp, res)
            agg = pf[raises[-1]][0] if raises else None
            fl = acts["flop"]
            if agg == me and fl:
                idx = next((i for i, (x, _) in enumerate(fl) if x == me), None)
                if idx is not None and not any(a == "raise" for (_, a) in fl[:idx]):
                    add("flop as aggressor: %s" % ("c-bet" if fl[idx][1] == "raise" else "check"), res)
            for st in ("flop", "turn", "river"):
                seq = acts[st]
                for i, (x, a) in enumerate(seq):
                    if x != me:
                        continue
                    facing = any(b == "raise" for (y, b) in seq[:i] if y != me)
                    if facing and a in ("call", "fold", "raise"):
                        add("%s facing a bet: %s" % (st, a), res)
                    if not facing and a == "raise":
                        add("%s bet first" % st, res)
            if str(me) in (h.get("showdown") or {}):
                add("went to showdown", res)
    return spots


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recent", type=int, default=None, help="only the last N rounds")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(ROOT, "hands", "*.json")),
                   key=lambda f: round_key(json.load(open(f, encoding="utf-8")).get("ref", f)))
    if a.recent:
        files = files[-a.recent:]
    spots = analyse(files)
    hands = spots["all hands"][0]
    print("%d rounds, %d hands\n%-34s %7s %10s %12s" % (len(files), hands, "spot", "count", "avg bb", "bb/100 total"))
    for k, (c, t) in sorted(spots.items(), key=lambda kv: kv[1][1]):
        print("%-34s %7d %+10.2f %+12.1f" % (k, c, t / c, t / hands * 100))


if __name__ == "__main__":
    main()
