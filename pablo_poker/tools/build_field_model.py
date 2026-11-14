"""Build data/field_model.json: a full behavioural profile of every real bot, from the hand logs.

    python tools/build_field_model.py

Unlike data/v3_model.json (what the live engine carries), this drives the SIMULATED field
(sim/fieldbot.FieldBot): each clone reproduces one real bot's measured decision frequencies,
with hand selection by strength inside its own range. Rounds are recency-weighted.

Per bot (and "pop", the weighted field average used to fill thin cells):
  pre.rfi[pos]          open-raise frequency when first in, by position group
  pre.limp[pos]         limp frequency when first in
  pre.open_sz           {amount: share}
  pre.vs_open[who]      [fold, call, raise] facing one raise (who: bb / sb / other)
  pre.vs_3b[who]        [fold, call, raise] facing a 3-bet (who: opener / cold)
  pre.vs_4b             [fold, call, raise] facing a 4-bet or more
  pre.vs_jam            [fold, call] facing a raise of 50+ bb
  pre.rsz               average re-raise size as a multiple of the bet faced; pre.rjam share of all-ins
  post[street].bet[k]   bet frequency when checked to (k: cb_hu, cb_mw, hu, mw; cb = as preflop aggressor)
  post[street].sz       {bet / pot (0.05 steps): share}
  post[street].vs[b]    [fold, call, raise] facing a bet of size bucket b (0..5 by size, 6 raise, 7 jam >= 2x pot)
  post[street].rsz/rjam raise size (multiple of the bet faced) and all-in share
  post[street].weak     share of this bot's shown-down bets on the street that were weak pair or worse
"""
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pokerbot.v2 import level_street, size_bucket, to_int  # noqa: E402
from rsi.field import HANDS_DIR, _files  # noqa: E402
from tools.build_v3_model import HALF_LIFE, slot_ts  # noqa: E402

OUT = os.path.join(ROOT, "data", "field_model.json")
STREETS = ("flop", "turn", "river")
JAM = 2.0            # a bet or raise of at least this many pots is its own bucket (7)


def bucket(frac, over_bet):
    return 7 if frac >= JAM else size_bucket(frac, over_bet)


def pos_group(seat, button, n):
    p = (seat - button) % n
    if p == 0:
        return "BTN"
    if p == 1:
        return "SB"
    if p == 2:
        return "BB"
    if p == n - 1:
        return "CO"
    if p == n - 2:
        return "HJ"
    return "EP"


def collect(before=None, after=None, documents=None):
    files = []
    for f, _own in ([] if documents is not None else _files(HANDS_DIR)):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        files.append((slot_ts(d.get("round") or {}), d))
    if documents is not None:
        files = [(slot_ts(d.get("round") or {}), d) for d in documents]
    if before is not None:
        files = [(t, d) for t, d in files if t < before]
    if after is not None:
        files = [(t, d) for t, d in files if t >= after]
    latest = max((t for t, _ in files), default=0)
    C = defaultdict(Counter)          # bot -> counter of "key|outcome"
    seen = set()
    for t, d in files:
        w = 0.5 ** (max(0.0, latest - t) / (300.0 * HALF_LIFE))
        pl = d["players"]
        n = len(pl)
        if n < 4:
            continue
        for h in d["hands"]:
            key = (tuple(pl), h["n"], tuple(h["board"]), json.dumps(h["events"][:6]))
            if key in seen:
                continue
            seen.add(key)
            btn = h["button"]
            street, pot, bets = "preflop", 0, [0] * n
            nraise, opener, pfagg, vol = 0, None, None, set()
            alive = set(range(n))
            facing = None                      # postflop: (seat, bucket) of the bet to answer
            lastbet = {}                       # street -> {seat: (size bucket, first bet)}
            board_now = []
            for s in range(n):
                C[pl[s]]["hands"] += w
            for e in h["events"]:
                if e[0] == "post":
                    pot += e[2]
                    bets[e[1]] = e[2]
                elif e[0] == "board":
                    street, bets, facing = e[1], [0] * n, None
                    board_now = e[2]
                elif e[0] == "act":
                    _, s, a, amt = e
                    c = C[pl[s]]
                    cur = max(bets)
                    add = 0
                    if a == "raise":
                        add = amt - bets[s]
                    elif a == "call":
                        add = amt              # engine logs calls as chips ADDED
                    if street == "preflop":
                        g = pos_group(s, btn, n)
                        tc = cur - bets[s]
                        if tc >= 1000 and a in ("fold", "call"):
                            c["pre.vs_jam|" + a] += w
                        elif nraise == 0:
                            k = "raise" if a == "raise" else ("limp" if a == "call" else "fold")   # BB check = no raise
                            c["pre.first.%s|%s" % (g, k)] += w
                            if a == "raise":
                                c["pre.open_sz|%d" % amt] += w
                        elif nraise == 1:
                            who = "bb" if g == "BB" else ("sb" if g == "SB" else "other")
                            c["pre.vs_open.%s|%s" % (who, a)] += w
                        elif nraise == 2:
                            c["pre.vs_3b.%s|%s" % ("opener" if s == opener else "cold", a)] += w
                        else:
                            c["pre.vs_4b|" + a] += w
                        if a == "raise" and nraise >= 1:
                            c["pre.rsz_sum"] += w * min(8.0, amt / float(max(1, cur)))
                            c["pre.rsz_n"] += w
                            c["pre.rjam"] += w * (amt >= 1500)
                        if a == "raise":
                            if nraise == 0:
                                opener = s
                            nraise += 1
                            pfagg = s
                        if a in ("call", "raise"):
                            vol.add(s)
                    else:
                        hu = "hu" if len(alive) == 2 else "mw"
                        if cur == 0:
                            k = ("cb_" if (street == "flop" and s == pfagg) else "") + hu
                            c["post.%s.bet.%s|%s" % (street, k, "bet" if a == "raise" else "check")] += w
                            if a == "raise":
                                frac = add / float(max(1, pot))
                                c["post.%s.sz|%.2f" % (street, min(6.0, round(frac / 0.05) * 0.05))] += w
                        elif facing is not None and s != facing[0]:
                            c["post.%s.vs.%d|%s" % (street, facing[1], a)] += w
                            if a == "raise":
                                c["post.%s.rsz_sum" % street] += w * min(8.0, amt / float(max(1, cur)))
                                c["post.%s.rsz_n" % street] += w
                                c["post.%s.rjam" % street] += w * (add >= 0.9 * 2000 or amt >= 1900)
                        if a == "raise":
                            frac = add / float(max(1, pot))
                            facing = (s, bucket(frac, cur > 0))
                            lastbet.setdefault(street, {})[s] = (facing[1], cur == 0)
                    if a == "raise":
                        pot += add
                        bets[s] = amt
                    elif a == "call":
                        pot += add
                        bets[s] += add
                    elif a == "fold":
                        alive.discard(s)
            board = h.get("board") or []
            sd = h.get("showdown") or {}
            if len(board) == 5 and len(sd) > 1:
                bd = [to_int(x) for x in board]
                for st, nb in (("flop", 3), ("turn", 4), ("river", 5)):
                    for s, (b, first) in lastbet.get(st, {}).items():
                        hc = h["hole"].get(str(s))
                        if hc and str(s) in sd:
                            L = level_street(to_int(hc[0]), to_int(hc[1]), bd[:nb])
                            C[pl[s]]["post.%s.shown" % st] += w
                            C[pl[s]]["post.%s.shown_weak" % st] += w * (L <= 1)
                            kind = "bet" if first else "raise"
                            C[pl[s]]["post.%s.strength.%s.%d|%d" % (st, kind, b, L)] += w
    return C, latest


def _dist(c, prefix, top=None):
    items = [(k.split("|", 1)[1], v) for k, v in c.items() if k.startswith(prefix + "|")]
    tot = sum(v for _, v in items)
    if tot <= 0:
        return {}
    items.sort(key=lambda kv: -kv[1])
    if top is not None:
        items = items[:top]
    tot = sum(v for _, v in items)
    return {k: round(v / tot, 4) for k, v in items}


def _rates(c, prefix, outcomes, prior=None, k=12.0):
    """Shares of each outcome, shrunk towards `prior` (a list) with weight k."""
    v = [c.get("%s|%s" % (prefix, o), 0.0) for o in outcomes]
    tot = sum(v)
    if prior is None:
        return [round(x / tot, 4) for x in v] if tot > 0 else None
    return [round((x + k * p) / (tot + k), 4) for x, p in zip(v, prior)]


def profile(c, pop=None):
    """pop: the population profile (same shape) used as the prior for thin cells; None when building pop itself."""
    def rate(prefix, outcomes, path, default):
        prior = default
        if pop is not None:
            node = pop
            for p in path:
                node = node[p]
            prior = node
        r = _rates(c, prefix, outcomes, prior)
        return r if r is not None else default
    pre = {"rfi": {}, "limp": {}, "vs_open": {}, "vs_3b": {}}
    for g in ("EP", "HJ", "CO", "BTN", "SB", "BB"):
        r = rate("pre.first.%s" % g, ("fold", "limp", "raise"), ("pre", "_first", g), [0.75, 0.01, 0.24])
        pre.setdefault("_first", {})[g] = r
        pre["rfi"][g], pre["limp"][g] = r[2], r[1]
    for who in ("bb", "sb", "other"):
        pre["vs_open"][who] = rate("pre.vs_open.%s" % who, ("fold", "call", "raise"), ("pre", "vs_open", who), [0.8, 0.12, 0.08])
    for who in ("opener", "cold"):
        pre["vs_3b"][who] = rate("pre.vs_3b.%s" % who, ("fold", "call", "raise"), ("pre", "vs_3b", who), [0.65, 0.25, 0.10])
    pre["vs_4b"] = rate("pre.vs_4b", ("fold", "call", "raise"), ("pre", "vs_4b"), [0.55, 0.3, 0.15])
    pre["vs_jam"] = rate("pre.vs_jam", ("fold", "call"), ("pre", "vs_jam"), [0.9, 0.1])
    pre["open_sz"] = _dist(c, "pre.open_sz", 8) or (pop["pre"]["open_sz"] if pop else {"60": 1.0})
    n = c.get("pre.rsz_n", 0.0)
    pp = pop["pre"] if pop else {"rsz": 3.3, "rjam": 0.1}
    pre["rsz"] = round((c.get("pre.rsz_sum", 0.0) + 6 * pp["rsz"]) / (n + 6), 3)
    pre["rjam"] = round((c.get("pre.rjam", 0.0) + 6 * pp["rjam"]) / (n + 6), 4)
    post = {}
    for st in STREETS:
        P = {"bet": {}, "vs": {}}
        for k in ("cb_hu", "cb_mw", "hu", "mw"):
            if st != "flop" and k.startswith("cb"):
                continue
            P["bet"][k] = rate("post.%s.bet.%s" % (st, k), ("check", "bet"), ("post", st, "_bet", k), [0.5, 0.5])[1]
            P.setdefault("_bet", {})[k] = [round(1 - P["bet"][k], 4), P["bet"][k]]
        for b in range(8):
            P["vs"][str(b)] = rate("post.%s.vs.%d" % (st, b), ("fold", "call", "raise"), ("post", st, "vs", str(b)),
                                   [0.45, 0.45, 0.10])
        P["sz"] = _dist(c, "post.%s.sz" % st) or (pop["post"][st]["sz"] if pop else {"0.60": 1.0})
        pq = pop["post"][st] if pop else {"rsz": 3.0, "rjam": 0.2, "weak": 0.4}
        n = c.get("post.%s.rsz_n" % st, 0.0)
        P["rsz"] = round((c.get("post.%s.rsz_sum" % st, 0.0) + 6 * pq["rsz"]) / (n + 6), 3)
        P["rjam"] = round((c.get("post.%s.rjam" % st, 0.0) + 6 * pq["rjam"]) / (n + 6), 4)
        n = c.get("post.%s.shown" % st, 0.0)
        P["weak"] = round((c.get("post.%s.shown_weak" % st, 0.0) + 8 * pq["weak"]) / (n + 8), 4)
        # Shown ranges are selected observations, not unconditional betting ranges.
        # Keep counts so calibration can apply the same showdown filter in simulation.
        P["strength"] = {}
        P["strength_n"] = {}
        for kind in ("bet", "raise"):
            P["strength"][kind], P["strength_n"][kind] = {}, {}
            for b in range(8):
                prefix = "post.%s.strength.%s.%d" % (st, kind, b)
                prior = (pop["post"][st]["strength"][kind][str(b)] if pop else
                         [0.1, 0.15, 0.25, 0.5])
                P["strength"][kind][str(b)] = _rates(c, prefix, range(4), prior, k=12)
                P["strength_n"][kind][str(b)] = sum(c.get(prefix + "|" + str(i), 0) for i in range(4))
        post[st] = P
    return {"w": round(c.get("hands", 0.0), 1), "pre": pre, "post": post}


def build(before=None, after=None, min_w=150, documents=None):
    C, latest = collect(before, after, documents)
    tot = Counter()
    for name, c in C.items():
        tot.update(c)
    pop = profile(tot)
    bots = {name: profile(c, pop) for name, c in C.items() if c["hands"] >= min_w}
    return {"built": time.strftime("%Y-%m-%d %H:%M:%S"), "latest_round": time.strftime("%H:%M", time.localtime(latest)),
            "half_life_rounds": HALF_LIFE, "pop": pop, "bots": bots}


if __name__ == "__main__":
    m = build()
    json.dump(m, open(OUT, "w"), indent=0, sort_keys=True)
    print("field model: %d bots, latest round %s, %d KB -> %s" % (len(m["bots"]), m["latest_round"],
                                                                 os.path.getsize(OUT) // 1024, OUT))
    p = m["pop"]
    print("pop rfi", p["pre"]["rfi"])
    print("pop vs_open", p["pre"]["vs_open"], "vs_3b", p["pre"]["vs_3b"], "vs_4b", p["pre"]["vs_4b"], "vs_jam", p["pre"]["vs_jam"])
    for st in STREETS:
        print(st, "bet", p["post"][st]["bet"], "weak share of shown bets", p["post"][st]["weak"], "raise x", p["post"][st]["rsz"],
              "jam", p["post"][st]["rjam"])
        print("    vs bet by size bucket [fold, call, raise]:", {b: v for b, v in sorted(p["post"][st]["vs"].items())})
