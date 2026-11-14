"""Analyse downloaded hand histories (hands/*.json).

    python tools/analyze.py                 # every round in hands/
    python tools/analyze.py hands/x.json    # chosen rounds
    python tools/analyze.py --big 8         # also list our 8 biggest wins/losses

Per round: every seat's result and playing-style stats; then our own results
split by position, by how the hand ended, and by starting-hand strength.
"""
import argparse
import glob
import json
import os
import sys

RANKS = "23456789TJQKA"
POS8 = ["BTN", "SB", "BB", "UTG", "UTG1", "MP", "HJ", "CO"]


def pct(a, b):
    return "%3.0f" % (100.0 * a / b) if b else "  -"


def hand_class(cards):
    a, b = sorted((RANKS.index(c[0]) for c in cards), reverse=True)
    if a == b:
        return RANKS[a] * 2
    return RANKS[a] + RANKS[b] + ("s" if cards[0][1] == cards[1][1] else "o")


def strength_group(cards):
    a, b = sorted((RANKS.index(c[0]) for c in cards), reverse=True)
    s = cards[0][1] == cards[1][1]
    if (a == b and a >= 9) or (a == 12 and b == 11):
        return "1 premium (JJ+,AK)"
    if (a == b and a >= 5) or (a == 12 and b >= 9) or (a == 11 and b >= 10 and s):
        return "2 strong (77-TT,AJ+,KQs)"
    if a == b or (a == 12) or (a >= 9 and b >= 8) or (s and a - b == 1 and b >= 4):
        return "3 playable"
    return "4 weak"


def new_stats():
    return dict(hands=0, chips=0, vpip=0, pfr=0, three=0, three_opp=0, allin_pre=0, limp=0,
                f_raise=0, f_raise_opp=0, bet=0, call=0, check=0, f_bet=0, f_bet_opp=0,
                saw_flop=0, sd=0, sd_won=0, sd_chips=0, nosd_chips=0, big_pots=0,
                open_sizes=[], bet_fracs=[], fold_small=0)


def walk(hand, n):
    """Yield per-action context dicts for one hand."""
    street = "preflop"
    bets = [0] * n
    contrib = [0] * n
    cur = 0
    pot = 0
    raises = 0
    out = []
    for e in hand["events"]:
        k = e[0]
        if k == "post":
            bets[e[1]] += e[2]
            contrib[e[1]] += e[2]
            cur = max(cur, bets[e[1]])
            pot += e[2]
        elif k == "board":
            street = e[1]
            bets = [0] * n
            cur = 0
            raises = 0
        elif k == "act":
            s, a, amt = e[1], e[2], e[3]
            to_call = cur - bets[s]
            ctx = dict(seat=s, street=street, action=a, amount=amt, to_call=to_call,
                       pot=pot, raises_before=raises, contrib=contrib[s], cur=cur)
            if a == "call":
                bets[s] += amt
                contrib[s] += amt
                pot += amt
            elif a == "raise":
                add = amt - bets[s]
                bets[s] = amt
                contrib[s] += add
                pot += add
                cur = amt
                raises += 1
            ctx["contrib_after"] = contrib[s]
            out.append(ctx)
    return out


def analyse_round(d, big=0):
    n = len(d["players"])
    me = d["seat"]
    st = [new_stats() for _ in range(n)]
    mine = dict(pos={}, end={}, grp={}, hands=[])
    shown_allin = {}
    for h in d["hands"]:
        res = h["results"]
        acts = walk(h, n)
        sd_seats = set(int(x) for x in (h.get("showdown") or {}))
        flop_seen = len(h["board"]) >= 3
        folded = set()
        vp, pf, th, ai, lp = set(), set(), set(), set(), set()
        last_street = "preflop"
        for c in acts:
            s, a = c["seat"], c["action"]
            last_street = c["street"]
            S = st[s]
            if c["street"] == "preflop":
                if c["raises_before"] >= 1 and c["to_call"] > 0:
                    S["f_raise_opp"] += 1
                    if a == "fold":
                        S["f_raise"] += 1
                if c["raises_before"] == 1 and s not in pf:
                    S["three_opp"] += 1
                    if a == "raise":
                        th.add(s)
                if a in ("call", "raise"):
                    vp.add(s)
                if a == "call" and c["raises_before"] == 0:
                    lp.add(s)
                if a == "raise":
                    pf.add(s)
                    if c["raises_before"] == 0:
                        S["open_sizes"].append(c["amount"] / float(h["bb"]))
                    if c["contrib_after"] >= 0.95 * h["start_stacks"][s]:
                        ai.add(s)
                if a == "call" and c["contrib_after"] >= 0.95 * h["start_stacks"][s]:
                    ai.add(s)
            else:
                if a == "raise":
                    S["bet"] += 1
                    if c["pot"]:
                        S["bet_fracs"].append((c["amount"] - (c["cur"] - c["to_call"])) / float(c["pot"]))
                elif a == "call":
                    S["call"] += 1
                elif a == "check":
                    S["check"] += 1
                if c["to_call"] > 0:
                    S["f_bet_opp"] += 1
                    if a == "fold":
                        S["f_bet"] += 1
                        if c["to_call"] <= 0.25 * c["pot"]:
                            S["fold_small"] += 1
            if a == "fold":
                folded.add(s)
        for s in range(n):
            S = st[s]
            S["hands"] += 1
            S["chips"] += res[s]
            S["vpip"] += s in vp
            S["pfr"] += s in pf
            S["three"] += s in th
            S["allin_pre"] += s in ai
            S["limp"] += s in lp
            if flop_seen and s not in folded or (flop_seen and any(c["seat"] == s and c["street"] != "preflop" for c in acts)):
                S["saw_flop"] += 1
            if s in sd_seats:
                S["sd"] += 1
                S["sd_won"] += res[s] > 0
                S["sd_chips"] += res[s]
            else:
                S["nosd_chips"] += res[s]
            if abs(res[s]) >= 0.9 * h["start_stacks"][s]:
                S["big_pots"] += 1
            if s in ai and s in sd_seats and str(s) in h["hole"]:
                shown_allin.setdefault(s, []).append(hand_class(h["hole"][str(s)]))
        # ---- our own breakdown
        r = res[me]
        pos = POS8[(me - h["button"]) % n] if n == 8 else str((me - h["button"]) % n)
        if me in sd_seats:
            end = "showdown"
        elif me in folded:
            my_fold = next(c for c in acts if c["seat"] == me and c["action"] == "fold")
            end = "we fold " + my_fold["street"]
        else:
            end = "all fold to us (" + last_street + ")"
        if me in ai:
            end += " [preflop all-in]"
        cards = h["hole"].get(str(me))
        grp = strength_group(cards) if cards else "?"
        for key, val in (("pos", pos), ("end", end), ("grp", grp)):
            x = mine[key].setdefault(val, [0, 0])
            x[0] += 1
            x[1] += r
        mine["hands"].append((r, h["n"], pos, cards, h))

    hands = len(d["hands"])
    print("\n=== %s  (%d hands, we are seat %d: %s) ===" % (d.get("ref"), hands, me, d["players"][me]))
    print("%-26s %8s | %4s %4s %4s %4s %4s %5s | %4s %4s %5s | %4s %4s %7s %7s | %4s %5s %5s" % (
        "team", "bb/100", "VPIP", "PFR", "3bet", "limp", "AIpf", "FvR", "AF%", "FvB", "fsml",
        "WTSD", "W$SD", "SDchip", "nonSD", "big", "open", "bet/p"))
    order = sorted(range(n), key=lambda s: -st[s]["chips"])
    for s in order:
        S = st[s]
        ag = S["bet"] + S["call"]
        os_ = sorted(S["open_sizes"])
        bf = sorted(S["bet_fracs"])
        print("%-26s %+8.1f | %4s %4s %4s %4s %4s %5s | %4s %4s %5d | %4s %4s %+7d %+7d | %4d %5s %5s" % (
            ("* " if s == me else "") + d["players"][s][:22], S["chips"] / 20.0 / hands * 100,
            pct(S["vpip"], hands), pct(S["pfr"], hands), pct(S["three"], S["three_opp"]),
            pct(S["limp"], hands), pct(S["allin_pre"], hands), pct(S["f_raise"], S["f_raise_opp"]),
            pct(S["bet"], ag), pct(S["f_bet"], S["f_bet_opp"]), S["fold_small"],
            pct(S["sd"], S["saw_flop"]), pct(S["sd_won"], S["sd"]), S["sd_chips"], S["nosd_chips"],
            S["big_pots"], ("%.1f" % os_[len(os_) // 2]) if os_ else "-",
            ("%.2f" % bf[len(bf) // 2]) if bf else "-"))
    for s in order:
        if s in shown_allin and len(shown_allin[s]) >= 3:
            xs = shown_allin[s]
            print("  preflop all-in hands shown by %-22s (%d): %s" % (d["players"][s][:22], len(xs), " ".join(xs[:28])))
    print("\n  OUR RESULT split (hands, chips, bb/100 contribution):")
    for key, title in (("pos", "by position"), ("end", "by how the hand ended"), ("grp", "by starting hand")):
        print("  -- " + title)
        items = mine[key].items()
        items = sorted(items, key=(lambda kv: POS8.index(kv[0]) if kv[0] in POS8 else 0) if key == "pos" else (lambda kv: kv[0]))
        for k, (cnt, chips) in items:
            print("     %-44s %5d  %+8d  %+7.1f" % (k, cnt, chips, chips / 20.0 / hands * 100))
    if big:
        hs = sorted(mine["hands"], key=lambda x: x[0])
        for title, sel in (("biggest losses", hs[:big]), ("biggest wins", hs[::-1][:big])):
            print("  -- " + title)
            for r, num, pos, cards, h in sel:
                line = []
                for e in h["events"]:
                    if e[0] == "act" and e[2] != "fold":
                        line.append("%s%s%s" % ("US" if e[1] == me else "s%d" % e[1], {"raise": "r", "call": "c", "check": "x"}[e[2]], e[3] or ""))
                    elif e[0] == "board":
                        line.append("| " + "".join(e[2][-1:] if e[1] != "flop" else e[2]))
                shown = {k: "".join(v) for k, v in h["hole"].items() if int(k) != me}
                print("     #%-4d %+6d %-4s %s  %s  shown=%s" % (num, r, pos, "".join(cards or []), " ".join(line)[:230], shown))
    return st, d["players"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--big", type=int, default=0)
    a = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    files = a.files or sorted(glob.glob(os.path.join(root, "hands", "*.json")))
    if not files:
        sys.exit("no hand files found")
    for f in files:
        analyse_round(json.load(open(f, encoding="utf-8")), a.big)


if __name__ == "__main__":
    main()
