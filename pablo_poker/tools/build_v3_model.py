"""Build data/v3_model.json from the real hand logs: what the v3 engine knows about the field.

    python tools/build_v3_model.py

Recency: each round is weighted 0.5 ** (age / HALF_LIFE rounds), so the model
follows bots as they change (and practice rounds barely count). Contents:

  pop.lvl[street][bucket]   P(level 0..3 | the bettor's last aggressive action this
                            street had this size bucket), from showdowns, level measured
                            on that street's board (same 4 levels as the engine)
  pop.base[street]          P(level) of a random hand from a ~40% preflop range there
                            (so lvl / base is the Bayes factor the engine applies)
  pop.fold/raise[street][bucket]   how the field responds to a bet of that size
  bots[name]                per-bot tendencies (vpip, pfr, ftb, af, f3, bluff ratio, ...)
                            plus fingerprints (open-raise amounts, postflop bet sizes)
                            for live identification at the table
"""
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pokerbot.v2 import ALLC, NC, level_street, size_bucket, to_int  # noqa: E402
from rsi.field import HANDS_DIR, _files  # noqa: E402

OUT = os.path.join(ROOT, "data", "v3_model.json")
HALF_LIFE = 10          # rounds
STREETS = ("flop", "turn", "river")


def slot_ts(meta):
    try:
        return time.mktime(time.strptime(meta["slot"][:19], "%Y-%m-%dT%H:%M:%S"))
    except (KeyError, TypeError, ValueError):
        return 0.0


def base_levels(iters=30000, frac=0.4, seed=1):
    rng = random.Random(seed)
    hi = int(frac * NC)
    out = {}
    for st, nb in (("flop", 3), ("turn", 4), ("river", 5)):
        c = [0, 0, 0, 0]
        for _ in range(iters):
            h1, h2 = ALLC[rng.randrange(hi)]
            deck = [x for x in range(52) if x != h1 and x != h2]
            bd = rng.sample(deck, nb)
            c[level_street(h1, h2, bd)] += 1
        out[st] = [x / float(iters) for x in c]
    return out


def build(before=None):
    """before: only rounds that started before this timestamp (to rebuild the model a past round had)."""
    files = []
    for f, _own in _files(HANDS_DIR):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        files.append((slot_ts(d.get("round") or {}), d))
    if before is not None:
        files = [(t, d) for t, d in files if t < before]
    latest = max(t for t, _ in files)
    lvl = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    resp = defaultdict(Counter)
    B = defaultdict(Counter)            # per-bot weighted counters
    opens = defaultdict(Counter)
    pbets = defaultdict(Counter)
    blvl = defaultdict(lambda: [0.0, 0.0])   # bot -> [weak-ish shown when aggressive, expected weak-ish under pop table]
    seen = set()
    for t, d in files:
        w = 0.5 ** (max(0.0, latest - t) / (300.0 * HALF_LIFE))
        pl = d["players"]
        n = len(pl)
        for h in d["hands"]:
            key = (tuple(pl), h["n"], tuple(h["board"]), json.dumps(h["events"][:6]))
            if key in seen:
                continue
            seen.add(key)
            street, pot, bets = "preflop", 0, [0] * n
            raised, nraise, opener = False, 0, None
            vp, pr = set(), set()
            last = {}                       # street -> (seat, bucket)
            facing = None
            for s in range(n):
                B[pl[s]]["hands"] += w
            for e in h["events"]:
                if e[0] == "post":
                    pot += e[2]
                    bets[e[1]] = e[2]
                elif e[0] == "board":
                    street, bets, facing = e[1], [0] * n, None
                elif e[0] == "act":
                    _, s, a, amt = e
                    name = pl[s]
                    cur = max(bets)
                    if street == "preflop":
                        if a in ("call", "raise"):
                            vp.add(s)
                        if a == "raise":
                            pr.add(s)
                            if not raised:
                                opens[name][str(amt)] += w
                                opener = s
                            if amt >= 600:
                                B[name]["big"] += w
                        if nraise >= 2 and s == opener and a in ("fold", "call", "raise"):
                            B[name]["o3"] += w
                            B[name]["o3fold"] += w * (a == "fold")
                        if nraise >= 1 and a in ("fold", "call", "raise") and s != opener:
                            B[name]["ftr_n"] += w
                            B[name]["ftr_f"] += w * (a == "fold")
                    else:
                        B[name]["pact"] += w
                        if a == "raise":
                            B[name]["pbet"] += w
                        if facing is not None and s != facing[0]:
                            resp[(street, facing[1])][a] += w
                            B[name]["faced"] += w
                            B[name]["ffold"] += w * (a == "fold")
                        if a == "raise":
                            frac = (amt - bets[s]) / float(max(1, pot))
                            b = size_bucket(frac, cur > 0)
                            facing = (s, b)
                            last[street] = (s, b)
                            if cur == 0:
                                pbets[name]["%.2f" % (round(frac / 0.05) * 0.05)] += w
                    if a == "raise":
                        raised = True
                        nraise += 1
                        pot += amt - bets[s]
                        bets[s] = amt
                    elif a == "call":
                        add = amt  # engine call amounts are incremental, not raise-to totals
                        pot += add
                        bets[s] += add
            for s in vp:
                B[pl[s]]["vpip"] += w
            for s in pr:
                B[pl[s]]["pfr"] += w
            board = h.get("board") or []
            if len(board) == 5 and h.get("showdown"):
                bd = [to_int(c) for c in board]
                for st, nb in (("flop", 3), ("turn", 4), ("river", 5)):
                    if st not in last:
                        continue
                    s, b = last[st]
                    hc = h["hole"].get(str(s))
                    if hc and str(s) in h["showdown"]:
                        L = level_street(to_int(hc[0]), to_int(hc[1]), bd[:nb])
                        lvl[(st, b)][L] += w
                        if st in ("turn", "river"):
                            blvl[pl[s]][0] += w * (L <= 1)
                            blvl[pl[s]][1] += w
    pop_lvl = {}
    for st in STREETS:
        pop_lvl[st] = {}
        for b in range(7):
            c = lvl[(st, b)]
            tot = sum(c)
            if tot >= 20:
                pop_lvl[st][str(b)] = [round((x + 0.5) / (tot + 2.0), 4) for x in c]
    pop_fold, pop_raise = {}, {}
    for st in STREETS:
        pop_fold[st], pop_raise[st] = {}, {}
        for b in range(7):
            r = resp[(st, b)]
            tot = sum(r.values())
            if tot >= 30:
                pop_fold[st][str(b)] = round(r["fold"] / tot, 4)
                pop_raise[st][str(b)] = round(r["raise"] / tot, 4)
    sd_all = sum(v[0] for v in blvl.values()) / max(1e-9, sum(v[1] for v in blvl.values()))
    bots = {}
    for name, c in B.items():
        H = c["hands"]
        if H < 150:
            continue
        r = lambda a, b, prior, k: (c[a] + prior * k) / (c[b] + k)   # noqa: E731
        ot = sum(opens[name].values())
        pt = sum(pbets[name].values())
        weak, nsd = blvl[name]
        bots[name] = {
            "w": round(H, 1), "vpip": round(c["vpip"] / H, 4), "pfr": round(c["pfr"] / H, 4),
            "big": round(c["big"] / H, 4), "f3": round(r("o3fold", "o3", 0.5, 4), 4),
            "ftr": round(r("ftr_f", "ftr_n", 0.75, 10), 4), "ftb": round(r("ffold", "faced", 0.45, 8), 4),
            "af": round(r("pbet", "pact", 0.3, 10), 4),
            "bluff": round(((weak + sd_all * 6) / (nsd + 6)) / sd_all, 4),
            "opens": {k: round(v / ot, 4) for k, v in opens[name].most_common(12)} if ot else {},
            "pbets": {k: round(v / pt, 4) for k, v in pbets[name].most_common(24)} if pt else {},
        }
    W = sum(b["w"] for b in bots.values()) or 1.0
    popstats = {k: round(sum(b[k] * b["w"] for b in bots.values()) / W, 4)
                for k in ("vpip", "pfr", "big", "f3", "ftr", "ftb", "af", "bluff")}
    return {"built": time.strftime("%Y-%m-%d %H:%M:%S"), "popstats": popstats, "latest_round": time.strftime("%H:%M", time.localtime(latest)),
            "half_life_rounds": HALF_LIFE, "sd_weak_share": round(sd_all, 4),
            "pop": {"lvl": pop_lvl, "base": base_levels(), "fold": pop_fold, "raise": pop_raise}, "bots": bots}


if __name__ == "__main__":
    m = build()
    json.dump(m, open(OUT, "w"), indent=0, sort_keys=True)
    print("v3 model: %d bots, latest round %s, %d KB -> %s" % (len(m["bots"]), m["latest_round"],
                                                             os.path.getsize(OUT) // 1024, OUT))
    for st in STREETS:
        print(st, "base", [round(x, 2) for x in m["pop"]["base"][st]])
        for b, v in sorted(m["pop"]["lvl"][st].items()):
            print("   bucket %s lvl %s  fold %s" % (b, v, m["pop"]["fold"][st].get(b)))
