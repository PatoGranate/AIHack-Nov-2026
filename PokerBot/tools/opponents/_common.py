"""Shared helpers for parametric archetype opponents (not uploaded)."""
import random

RANKS = "23456789TJQKA"


def _chen(hole):
    a, b = sorted((RANKS.index(c[0]) for c in hole), reverse=True)
    val = {12: 10, 11: 8, 10: 7, 9: 6}.get(a, (a + 2) / 2.0)
    if a == b:
        val = max(5, val * 2)
    if hole[0][1] == hole[1][1]:
        val += 2
    gap = a - b - 1
    if a != b:
        val -= [0, 1, 2, 4, 5][min(gap, 4)] if gap >= 0 else 0
        if gap <= 1 and a < 10:
            val += 1
    return val


# percentile table for all 169 classes (1.0 = best)
_ALL = []
for _i in range(13):
    for _j in range(13):
        if _i == _j:
            _ALL.append(((RANKS[_i] + "c", RANKS[_j] + "d"), 6))
        elif _i > _j:
            _ALL.append(((RANKS[_i] + "c", RANKS[_j] + "c"), 4))
            _ALL.append(((RANKS[_i] + "c", RANKS[_j] + "d"), 12))
_SC = sorted(((_chen(h), w) for h, w in _ALL), key=lambda x: x[0])
_PCT = {}
_cum = 0
for _s, _w in _SC:
    _cum += _w
    _PCT[_s] = _cum / 1326.0


def pf_pct(hole):
    """Fraction of hands this hand beats or ties by Chen score (1.0 = top)."""
    return _PCT.get(_chen(hole), 0.5)


def made(hole, board):
    """0 nothing, 1 weak pair, 2 middle/top pair weak kicker, 3 top pair good/overpair,
    4 two pair, 5 trips/set, 6 straight+.  Returns (cat, draw)."""
    hr = [RANKS.index(c[0]) for c in hole]
    br = [RANKS.index(c[0]) for c in board]
    allr = hr + br
    suits = [c[1] for c in hole + board]
    cat = 0
    # flush / straight
    for s in "cdhs":
        if suits.count(s) >= 5 and any(c[1] == s for c in hole):
            cat = 6
    rs = set(allr)
    if 12 in rs:
        rs.add(-1)
    for top in range(12, 2, -1):
        if all((top - k) in rs for k in range(5)):
            if any(r in range(top - 4, top + 1) or (r == 12 and top == 3) for r in hr):
                cat = max(cat, 6)
    cnt = {r: allr.count(r) for r in set(allr)}
    bcnt = {r: br.count(r) for r in set(br)}
    if cat < 6:
        mine = [r for r in set(hr) if cnt[r] > bcnt.get(r, 0)]
        trips = [r for r in mine if cnt[r] >= 3]
        pairs = [r for r in mine if cnt[r] == 2]
        if trips:
            cat = 5
        elif len(pairs) >= 2 or (pairs and any(v >= 2 for v in bcnt.values()) and False):
            cat = 4
        elif pairs:
            p = pairs[0]
            top = max(br) if br else 0
            if p > top:
                cat = 3  # overpair
            elif p == top:
                kick = [r for r in hr if r != p]
                cat = 3 if (not kick or kick[0] >= 9) else 2
            elif p >= sorted(br)[-2] if len(br) >= 2 else False:
                cat = 2
            else:
                cat = 1
    draw = False
    if len(board) < 5 and cat < 6:
        for s in "cdhs":
            if suits.count(s) == 4 and any(c[1] == s for c in hole):
                draw = True
        for lo in range(-1, 9):
            win = set(range(lo, lo + 5))
            if len(win & rs) >= 4 and any(r in win for r in hr):
                draw = True
    return cat, draw


class ParamBot:
    P = dict(open=0.2, limp=0.0, threebet=0.05, call=0.12, call_cap=0.15, open_size=3.0,
             shove=0.0, cbet=0.6, bet_min=2, bluff=0.05, call_min=2, raise_min=4,
             bet_frac=0.6, semibluff=0.5, station=False, never_raise=False, fold_all=False)

    def __init__(self):
        self.rng = random.Random()
        self.p = dict(ParamBot.P)
        self.p.update(self.PARAMS)

    def on_table_start(self, info):
        pass

    def on_hand_end(self, summary):
        pass

    def _r(self, state, amt):
        if "raise" not in state["legal_actions"] or self.p["never_raise"]:
            return {"action": "call"} if state["to_call"] > 0 else {"action": "check"}
        lo, hi = state["min_raise_to"], state["max_raise_to"]
        return {"action": "raise", "amount": int(max(lo, min(hi, amt)))}

    def _pass(self, state):
        return {"action": "check"} if state["to_call"] == 0 else {"action": "fold"}

    def act(self, state):
        p = self.p
        if p["fold_all"]:
            return self._pass(state)
        hole, board = state["hole_cards"], state["board"]
        bb = state["big_blind"]
        to_call = state["to_call"]
        me = state["seat"]
        stack = state["stacks"][me] + state["bets"][me]
        cur = max(state["bets"])
        rnd = self.rng.random()
        if state["street"] == "preflop":
            s = 1 - pf_pct(hole)  # 0 = best
            raises = sum(1 for h in state["history"] if h["street"] == "preflop" and h["action"] == "raise")
            if p.get("shove_mix") and s < p["shove_mix"] and raises < 3:
                return {"action": "all_in"}
            if p["shove"]:
                if s < p["shove"]:
                    return {"action": "all_in"}
                return self._pass(state)
            if raises == 0:
                if s < p["open"]:
                    return self._r(state, bb * p["open_size"] + bb * sum(1 for h in state["history"] if h["action"] == "call"))
                if s < p["limp"]:
                    return {"action": "call"}
                return self._pass(state)
            if s < p["threebet"] / (1 + raises - 1) and raises < 4:
                return self._r(state, cur * 3)
            if s < p["call"] and to_call <= p["call_cap"] * stack:
                return {"action": "call"}
            if s < p["threebet"] * 0.5:
                return {"action": "call"}
            if p.get("pf_station") and to_call <= 0.1 * stack:
                return {"action": "call"}
            return self._pass(state)
        cat, draw = made(hole, board)
        pot = state["pot"]
        if p.get("trapper") and cat >= p.get("trap_min", 2):
            if state["street"] != "river":
                return {"action": "call"} if to_call > 0 else {"action": "check"}
            return {"action": "all_in"} if cat >= p.get("trap_min", 2) + 1 or rnd < 0.6 else {"action": "call"}
        pf_raiser = None
        for h in state["history"]:
            if h["street"] == "preflop" and h["action"] == "raise":
                pf_raiser = h["seat"]
        if to_call == 0:
            if cat >= p["bet_min"] or (draw and rnd < p["semibluff"]) or rnd < p["bluff"] or \
                    (pf_raiser == me and state["street"] == "flop" and rnd < p["cbet"]):
                return self._r(state, cur + max(bb, pot * p["bet_frac"]))
            return {"action": "check"}
        size = to_call / float(max(1, pot))
        if cat >= p["raise_min"] or (cat >= p["raise_min"] - 1 and rnd < p["bluff"]):
            return self._r(state, cur * 2.5 + pot * 0.5)
        need = p["call_min"] + (1 if size > 0.6 else 0)
        if p["station"] or cat >= need or rnd < p.get("air_call", 0) or (draw and size < 0.5 and state["street"] != "river"):
            return {"action": "call"}
        return self._pass(state)
