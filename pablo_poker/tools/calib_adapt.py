"""Calibrate the clones' adaptation to aggressive bettors (data/field_adapt.json).

    python tools/calib_adapt.py init            # delta = real answer to our bots' bets - real answer to others'
    python tools/calib_adapt.py SIMDIR          # delta += real answer to our bots - simulated answer to kaiserbot

The delta [fold, raise] per street and bet-size bucket is applied by sim/fieldbot.py in proportion to the
bettor's observed postflop bet-when-checked-to frequency, between ref[0] (field average) and ref[1] (our bots).
"""
import glob
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tools.build_field_model import bucket  # noqa: E402

OUT = os.path.join(ROOT, "data", "field_adapt.json")
REF = [0.48, 0.92]          # postflop bet-when-checked-to: field average, our three bots (real rounds 38-53)
STREETS = ("flop", "turn", "river")


def sim_answers(simdir, hero="kaiserbot"):
    C = defaultdict(lambda: [0, 0, 0])
    for f in glob.glob(os.path.join(simdir, "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        pl = d["players"]
        n = len(pl)
        for h in d["hands"]:
            street, bets, pot, facing = "preflop", [0] * n, 0, None
            for e in h["events"]:
                if e[0] == "post":
                    bets[e[1]] = e[2]
                    pot += e[2]
                elif e[0] == "board":
                    street, bets, facing = e[1], [0] * n, None
                elif e[0] == "act":
                    _, s, a, amt = e
                    cur = max(bets)
                    add = amt - bets[s] if a == "raise" else (amt if a == "call" else 0)
                    if street != "preflop" and facing is not None and s != facing[0] and pl[facing[0]] == hero:
                        if a in ("fold", "call", "raise"):
                            C[(street, facing[1])][("fold", "call", "raise").index(a)] += 1
                    if a == "raise" and street != "preflop":
                        facing = (s, bucket(add / float(max(1, pot)), cur > 0))
                    if a == "raise":
                        bets[s] = amt
                    else:
                        bets[s] += add
                    pot += add
    return C


if __name__ == "__main__":
    m = json.load(open(os.path.join(ROOT, "data", "field_model.json"), encoding="utf-8"))
    post = m["pop"]["post"]
    if sys.argv[1] == "init":
        ad = {"ref": REF}
        for st in STREETS:
            ad[st] = {}
            for b, v in post[st]["vsus"].items():
                base = post[st]["vs"][b]
                ad[st][b] = [round(v[0] - base[0], 4), round(v[2] - base[2], 4)]
    else:
        ad = json.load(open(OUT, encoding="utf-8"))
        C = sim_answers(sys.argv[1])
        for st in STREETS:
            for b, v in post[st]["vsus"].items():
                c = C.get((st, int(b)))
                if not c or sum(c) < 40:
                    continue
                t = float(sum(c))
                k = min(1.0, min(v[3], t) / 300.0)          # trust small cells less
                d = ad[st].setdefault(b, [0.0, 0.0])
                df, dr = v[0] - c[0] / t, v[2] - c[2] / t
                d[0] = round(d[0] + k * df, 4)
                d[1] = round(d[1] + k * dr, 4)
                print("%-5s b%s real fold %.2f raise %.2f | sim fold %.2f raise %.2f (n=%d) -> delta %s" % (
                    st, b, v[0], v[2], c[0] / t, c[2] / t, t, d))
    json.dump(ad, open(OUT, "w"), indent=1, sort_keys=True)
    print(json.dumps(ad))
