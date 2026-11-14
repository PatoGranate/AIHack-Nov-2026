"""Analyse downloaded hand histories: python tools/analyze.py Hand_data/*.json [--me WBot]"""
import sys, json, glob, os
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preflop_tables as PT

RANKS = "23456789TJQKA"
PCT = {}
_c = 0
_W = lambda c: 6 if len(c) == 2 else (4 if c[2] == "s" else 12)
for c in PT.RANK:
    _c += _W(c); PCT[c] = _c / 1326.0


def key(h):
    a, b = RANKS.index(h[0][0]), RANKS.index(h[1][0])
    if a < b: a, b = b, a
    if a == b: return RANKS[a] * 2
    return RANKS[a] + RANKS[b] + ("s" if h[0][1] == h[1][1] else "o")


def fixname(nm):
    """Repair UTF-8 names that were decoded as Latin-1 somewhere upstream."""
    try:
        r = nm.encode("latin-1").decode("utf-8")
        return r if r != nm else nm
    except Exception:
        return nm


def new():
    return defaultdict(float)


def analyse(files, me="WBot"):
    S = defaultdict(new)
    showdowns = defaultdict(list)
    mine = defaultdict(float)
    mine_n = defaultdict(int)
    big_losses = []
    for f in files:
        d = json.load(open(f))
        names = [fixname(x) for x in d["players"]]
        me = names[d["seat"]] if "seat" in d else me
        bb = 20
        for h in d["hands"]:
            n = len(names)
            folded = [False] * n
            street = "preflop"
            cur = h["bb"]; nraise = 0
            pf = {}  # seat -> list of preflop actions
            agg_post = defaultdict(int)
            for i in range(n):
                S[names[i]]["hands"] += 1
                S[names[i]]["chips"] += h["results"][i]
            first_raiser = None
            cbet_chance = None
            for e in h["events"]:
                if e[0] == "board":
                    street = e[1]; cur = 0; nraise = 0
                    continue
                if e[0] != "act":
                    continue
                _, s, a, amt = e
                nm = names[s]; o = S[nm]
                if street == "preflop":
                    pf.setdefault(s, []).append(a)
                    if a in ("call", "raise"): o["_vp"] = 1
                    if a == "raise":
                        o["_pr"] = 1
                        first_raiser = s   # actually the LAST preflop raiser (c-bet attribution fix)
                        if nraise == 0:
                            o["open_sz"] += amt / bb; o["open_n"] += 1
                        if nraise >= 1: o["3b"] += 1
                        if amt >= 600: o["shove"] += 1
                    if nraise >= 1 and a in ("fold", "call", "raise"):
                        o["f_raise"] += 1
                        if a == "fold": o["fold_raise"] += 1
                    if nraise == 0 and a == "call" and s != None:
                        o["limp"] += 1
                    if nraise == 0 and a in ("fold", "call", "raise"):
                        o["unopened"] += 1
                else:
                    if a == "raise":
                        o["pbet"] += 1
                        o["bet_sz"] += 0  # sizes below
                        agg_post[s] += 1
                    elif a == "call":
                        o["pcall"] += 1
                    elif a == "check":
                        o["pcheck"] += 1
                    if cur > 0 and a in ("fold", "call", "raise"):
                        o["faced"] += 1
                        if a == "fold": o["ffold"] += 1
                        if a == "raise": o["fraise"] += 1
                    if street == "flop" and s == first_raiser and cur == 0:
                        o["cb_ch"] += 1
                        if a == "raise": o["cb"] += 1
                    if street == "river" and a == "raise": o["rbet"] += 1
                if a == "raise":
                    cur = amt; nraise += 1
                if a == "fold":
                    folded[s] = True
            for i in range(n):
                o = S[names[i]]
                o["vpip"] += o.pop("_vp", 0); o["pfr"] += o.pop("_pr", 0)
            for k, v in (h.get("hole") or {}).items():
                s = int(k)
                if names[s] == me:
                    continue
                if str(s) in (h.get("showdown") or {}):
                    showdowns[names[s]].append((key(v), "/".join(pf.get(s, [])), agg_post[s], h["results"][s]))
            # our results
            ms = names.index(me) if me in names else None
            if ms is not None:
                pos = (ms - h["button"]) % n
                pn = {0: "BTN", 1: "SB", 2: "BB"}.get(pos, "EP%d" % pos if pos < n - 1 else "CO")
                mine[pn] += h["results"][ms]; mine_n[pn] += 1
                myk = key(h["hole"][str(ms)])
                mine["cls_" + ("prem" if PCT[myk] <= 0.05 else "good" if PCT[myk] <= 0.15 else "mid" if PCT[myk] <= 0.35 else "weak")] += h["results"][ms]
                if h["results"][ms] <= -800:
                    big_losses.append((f[-9:], h["n"], h["hole"][str(ms)], h["board"], h["showdown"], [e for e in h["events"] if e[0] == "act" and e[2] != "fold"][:14]))
    return S, showdowns, mine, mine_n, big_losses


if __name__ == "__main__":
    files = [a for a in sys.argv[1:] if not a.startswith("--")] or glob.glob("Hand_data/*.json")
    S, sd, mine, mine_n, bl = analyse(files)
    print("%-22s %5s %6s %5s %5s %4s %4s %5s %5s %5s %5s %5s %5s" % ("bot", "hands", "bb/100", "vpip", "pfr", "3b", "shv", "opsz", "limp", "af", "ftb", "cbet", "frse"))
    for nm, o in sorted(S.items(), key=lambda kv: -kv[1]["chips"] / kv[1]["hands"]):
        H = o["hands"]
        af = o["pbet"] / max(1, o["pbet"] + o["pcall"] + o["pcheck"])
        print("%-22s %5d %+6.0f %5.2f %5.2f %4.2f %4.2f %5.1f %5.2f %5.2f %5.2f %5.2f %5.2f" % (
            nm[:22], H, o["chips"] / 20 / H * 100, o["vpip"] / H, o["pfr"] / H, o["3b"] / max(1, o["f_raise"]),
            o["shove"] / H, o["open_sz"] / max(1, o["open_n"]), o["limp"] / max(1, o["unopened"]), af,
            o["ffold"] / max(1, o["faced"]), o["cb"] / max(1, o["cb_ch"]), o["fold_raise"] / max(1, o["f_raise"])))
    print("\nWBot by position (bb/100):", {k: round(mine[k] / 20 / mine_n[k] * 100) for k in mine_n})
    print("WBot by hand class (total bb):", {k: round(v / 20) for k, v in mine.items() if k.startswith("cls")})
    print("\nshowdown samples:")
    for nm, v in sd.items():
        print(" ", nm, len(v), sorted(v, key=lambda x: PCT[x[0]])[:3], "... worst:", sorted(v, key=lambda x: -PCT[x[0]])[:4])
    print("\nbig losses:", len(bl))
    for x in bl[:25]:
        print(" ", x)
