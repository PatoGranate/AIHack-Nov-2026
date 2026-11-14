"""Opponent tendencies from the REAL hands -> concrete, testable ideas.

Every time new rounds arrive the lab re-measures how the field plays and
turns exploitable tendencies into one-parameter ideas for the gate:

  fold_to_steal   players left to act fold to a single open from CO/BTN/SB
  fold_to_3bet    an opener folds when re-raised
  fold_to_cbet    players fold to the preflop raiser's flop bet
  river_bluff     river bets/raises that reach showdown holding only high card
  river_strong    river bets/raises that reach showdown with two pair or better

Classic exploitative poker: if the field over-folds, bluff/steal more; if it
never bluffs the river, fold more there; if it calls everything, value-bet
thinner and stop bluffing. The gate still decides whether each idea is real.

    python -m rsi.insights          print the tendencies and the ideas they produce
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rsi.field import HANDS_DIR, _files, self_names  # noqa: E402

MIN_N = 80

# (metric, low threshold, high threshold, ideas if high, ideas if low): ideas are (param, direction)
RULES = [
    ("fold_to_steal", 0.62, 0.80, [("open_btn", 1), ("open_co", 1), ("open_sb", 1)], [("open_btn", -1), ("open_sb", -1)]),
    ("fold_to_3bet", 0.38, 0.58, [("threebet_bluff", 1), ("threebet_size", -1)], [("threebet_bluff", -1), ("threebet_value", 1)]),
    ("fold_to_cbet", 0.40, 0.55, [("cbet_freq", 1), ("bet_bluff", -1)], [("cbet_freq", -1), ("value_flop", -1)]),
    ("river_bluff", 0.10, 0.25, [("call_margin", -1)], [("call_margin", 1), ("value_river", 1)]),
]


def _card(c):
    return "23456789TJQKA".index(c[0]) * 4 + "cdhs".index(c[1])


def tendencies(hands_dir=HANDS_DIR):
    from pokerbot.strategy import evaluate
    me = self_names(hands_dir)
    cnt = {k: [0, 0] for k in ("fold_to_steal", "fold_to_3bet", "fold_to_cbet", "river_bluff", "river_strong")}
    seen = set()
    for f, _own in _files(hands_dir):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        players = d.get("players") or []
        rnd = d.get("round") or {}
        ref, table = d.get("ref") or rnd.get("ref") or f, rnd.get("table")
        n = len(players)
        for h in d.get("hands", []):
            key = (ref, table, h.get("n"))
            if key in seen:
                continue
            seen.add(key)
            opp = lambda s: s < n and players[s] not in me      # noqa: E731
            button = h.get("button", 0)
            street, acts = "preflop", {"preflop": [], "flop": [], "turn": [], "river": []}
            for e in h.get("events", []):
                if e[0] == "board":
                    street = e[1]
                elif e[0] == "act":
                    acts[street].append((e[1], e[2], e[3]))
            pf = acts["preflop"]
            # --- steal: first voluntary action is a raise from CO/BTN/SB, then responses of the others
            raises = [i for i, a in enumerate(pf) if a[1] == "raise"]
            first_vol = next((i for i, a in enumerate(pf) if a[1] in ("call", "raise")), None)
            if raises and first_vol == raises[0]:
                opener = pf[raises[0]][0]
                off = (opener - button) % n
                late = off in (0, 1, n - 1)                       # BTN, SB, CO
                nxt = raises[1] if len(raises) > 1 else len(pf)
                if late:
                    for s, a, _ in pf[raises[0] + 1:nxt + (1 if len(raises) > 1 else 0)]:
                        if s != opener and opp(s) and a in ("fold", "call", "raise"):
                            cnt["fold_to_steal"][1] += 1
                            cnt["fold_to_steal"][0] += a == "fold"
                # --- 3-bet: opener's response to the first re-raise
                if len(raises) > 1 and opp(opener):
                    resp = next((a for s, a, _ in pf[raises[1] + 1:] if s == opener), None)
                    if resp in ("fold", "call", "raise"):
                        cnt["fold_to_3bet"][1] += 1
                        cnt["fold_to_3bet"][0] += resp == "fold"
            # --- c-bet: preflop aggressor makes the first flop bet; the others respond
            if raises:
                aggressor = pf[raises[-1]][0]
                fl = acts["flop"]
                first_bet = next((i for i, a in enumerate(fl) if a[1] == "raise"), None)
                if first_bet is not None and fl[first_bet][0] == aggressor:
                    for s, a, _ in fl[first_bet + 1:]:
                        if a == "raise" and s != aggressor:
                            if opp(s):
                                cnt["fold_to_cbet"][1] += 1
                            break
                        if s != aggressor and opp(s) and a in ("fold", "call"):
                            cnt["fold_to_cbet"][1] += 1
                            cnt["fold_to_cbet"][0] += a == "fold"
            # --- river bets that reached showdown: what did they hold?
            shown = h.get("hole") or {}
            board = h.get("board") or []
            if len(board) == 5 and len(h.get("showdown") or {}) >= 2:
                bettors = {s for s, a, _ in acts["river"] if a == "raise"}
                for s in bettors:
                    if opp(s) and str(s) in shown:
                        cat = evaluate([_card(c) for c in shown[str(s)] + board]) >> 20
                        cnt["river_bluff"][1] += 1
                        cnt["river_bluff"][0] += cat == 0
                        cnt["river_strong"][1] += 1
                        cnt["river_strong"][0] += cat >= 2
    return {k: {"rate": (v[0] / v[1]) if v[1] else None, "n": v[1]} for k, v in cnt.items()}


def ideas(tend=None):
    """Turn tendencies into ideas: {id, param, direction, steps, source, why}."""
    tend = tend or tendencies()
    out = []
    for metric, lo, hi, if_high, if_low in RULES:
        t = tend.get(metric) or {}
        r, n = t.get("rate"), t.get("n", 0)
        if r is None or n < MIN_N:
            continue
        side = "high" if r >= hi else "low" if r <= lo else None
        if side is None:
            continue
        for param, d in (if_high if side == "high" else if_low):
            out.append({"id": "auto-%s-%s-%s%s" % (metric, side, param, "+" if d > 0 else "-"), "param": param,
                        "direction": d, "steps": 1, "auto": True,
                        "source": "real field: %s %.0f%% (n=%d)" % (metric.replace("_", " "), 100 * r, n),
                        "why": "field %s is %s, so move %s %s" % (metric, side, param, "up" if d > 0 else "down")})
    return out


if __name__ == "__main__":
    t = tendencies()
    for k, v in t.items():
        print("%-14s %s  (n=%d)" % (k, "%.1f%%" % (100 * v["rate"]) if v["rate"] is not None else "  -  ", v["n"]))
    print()
    for i in ideas(t):
        print("idea %-40s %s" % (i["id"], i["source"]))
