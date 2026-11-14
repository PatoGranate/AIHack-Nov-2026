"""Frequency clone of a real opponent.

The earlier clones were our own equity-driven strategy with scaled ranges, so
they folded "correctly". Real bots over-fold (the field folds ~70% to steals
and ~55% to c-bets), and that is exactly the edge the winning teams take.
StatBot reproduces the measured frequencies of one real bot directly:

  preflop   open (steal when late), 3-bet, call, fold-to-steal, fold-to-3-bet
  postflop  c-bet frequency, fold-to-c-bet, aggression, river bluff rate

Hand strength decides WHICH hands take each action (the best hands raise,
the worst fold), so the frequencies come with realistic hand selection.
"""
import random
from statistics import NormalDist

from pokerbot.strategy import card_int, evaluate, hole_pct

_CAT = {0: 0.12, 1: 0.45, 2: 0.70, 3: 0.80, 4: 0.86, 5: 0.90, 6: 0.95, 7: 0.98, 8: 1.0}


def quick_strength(hole, board):
    """Cheap 0..1 strength (no Monte Carlo): made hand, whether the hole cards matter, pair rank, draws."""
    full = evaluate(hole + board)
    cat = full >> 20
    if len(board) >= 5 and evaluate(board) == full:
        return 0.08                                     # playing the board
    st = _CAT[cat]
    ranks = sorted((c >> 2 for c in board), reverse=True)
    if cat == 1:
        pair = (full >> 12) & 15
        st = 0.62 if pair >= ranks[0] else 0.47 if pair >= ranks[len(ranks) // 2] else 0.36
    elif cat == 0 and min(c >> 2 for c in hole) > ranks[0]:
        st = 0.25                                       # two overcards
    if len(board) < 5 and cat < 4:
        suits = [0, 0, 0, 0]
        for c in hole + board:
            suits[c & 3] += 1
        if max(suits) == 4 and any(suits[c & 3] == 4 for c in hole):
            st += 0.18                                  # flush draw
        m = 0
        for c in hole + board:
            m |= 1 << (c >> 2)
        m = (m << 1) | (1 if m & (1 << 12) else 0)
        if any((m >> i) & 0b1111 == 0b1111 for i in range(0, 11)):
            st += 0.10                                  # open-ended straight draw
    return min(1.0, st)


_Q = []

_Z = NormalDist()


def _strength_quantiles(n=4000, seed=7):
    """Distribution of quick_strength for random hands on random flops: maps a frequency to a threshold."""
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        cards = rng.sample(range(52), 5)
        vals.append(quick_strength(cards[:2], cards[2:]))
    return sorted(vals)


def _q(x):
    x = min(0.999, max(0.0, x))
    return _Q[int(x * (len(_Q) - 1))]


class StatBot:
    def __init__(self, profile, seed=None):
        p = dict(profile)
        self.vpip = p.get("vpip", 0.22)
        self.pfr = p.get("pfr", 0.14)
        self.steal = p.get("steal", 0.40)
        self.threebet = p.get("threebet", 0.04)
        self.cbet = p.get("cbet", 0.65)
        self.agg = p.get("agg", 0.30)
        self.f_steal = p.get("fold_to_steal", 0.70)
        self.f_3bet = p.get("fold_to_3bet", 0.50)
        self.f_cbet = p.get("fold_to_cbet", 0.55)
        self.r_bluff = p.get("river_bluff", 0.05)
        self.rng = random.Random(seed)
        # flop equity vs one random hand is roughly N(0.5, 0.2): fold the bottom f_cbet of it
        # fold the weakest f_cbet share of hands (quantile of the strength scale on random flops)
        if not _Q:
            _Q.extend(_strength_quantiles())
        self.fold_eq = _q(self.f_cbet)
        self.bet_eq = _q(1.0 - self.agg * 1.1)
        self.seat = 0

    def on_table_start(self, info):
        self.seat = info.get("seat", 0)

    @staticmethod
    def _pos_late(s):
        n = len(s["stacks"])
        off = (s["seat"] - s["button"]) % n
        return off in (0, 1, n - 1)

    def _raise(self, s, amount):
        lo, hi = s["min_raise_to"], s["max_raise_to"]
        return {"action": "raise", "amount": int(max(lo, min(hi, amount)))}

    def act(self, s):
        legal = s["legal_actions"]
        bb = s["big_blind"]
        hist = s.get("history") or []
        hole = [card_int(c) for c in s["hole_cards"]]
        pct = hole_pct(hole[0], hole[1])
        can_raise = "raise" in legal
        passive = {"action": "check"} if "check" in legal else {"action": "fold"}
        if s["street"] == "preflop":
            acts = [h for h in hist if h["street"] == "preflop" and h["action"] not in ("small_blind", "big_blind")]
            raises = [h for h in acts if h["action"] == "raise"]
            if not raises:
                width = self.steal if self._pos_late(s) else self.pfr * 0.9
                if pct <= width and can_raise:
                    return self._raise(s, 2.5 * bb + bb * sum(1 for h in acts if h["action"] == "call"))
                if "check" in legal:
                    return {"action": "check"}
                if pct <= self.vpip and s["to_call"] <= bb and self.vpip - self.pfr > 0.12:
                    return {"action": "call"}                       # loose-passive bots limp
                return {"action": "fold"}
            opener = raises[0]["seat"]
            if len(raises) == 1:
                if s["to_call"] >= 0.45 * (s["stacks"][s["seat"]] + s["bets"][s["seat"]]):
                    return {"action": "call"} if pct <= 0.06 else passive
                cont = 1.0 - self.f_steal
                if pct <= self.threebet and can_raise:
                    return self._raise(s, max(s["bets"]) * 3.2)
                if pct <= cont:
                    return {"action": "call"}
                return passive
            if opener == s["seat"]:                                 # we opened and got 3-bet
                my_width = self.steal if self._pos_late(s) else self.pfr
                keep = my_width * (1.0 - self.f_3bet)
                if pct <= min(keep, 0.025) and can_raise:
                    return {"action": "all_in"}
                return {"action": "call"} if pct <= keep else passive
            return {"action": "call"} if pct <= 0.03 else passive
        # ---------------------------------------------------------- postflop
        board = [card_int(c) for c in s["board"]]
        eq_hu = quick_strength(hole, board)
        pot, to_call = s["pot"], s["to_call"]
        r = self.rng.random()
        if to_call > 0:
            if eq_hu < self.fold_eq:
                return passive
            if eq_hu > 0.88 and can_raise and r < self.agg:
                return self._raise(s, max(s["bets"]) + pot)
            return {"action": "call"}
        if not can_raise:
            return passive
        pf_raises = [h for h in hist if h["street"] == "preflop" and h["action"] == "raise"]
        aggressor = bool(pf_raises) and pf_raises[-1]["seat"] == s["seat"]
        first_on_street = not any(h["street"] == s["street"] and h["action"] == "raise" for h in hist)
        if s["street"] == "flop" and aggressor and first_on_street:
            if r < self.cbet:
                return self._raise(s, max(s["bets"]) + 0.6 * pot)
            return passive
        if eq_hu >= self.bet_eq:
            return self._raise(s, max(s["bets"]) + 0.7 * pot)
        if s["street"] == "river" and eq_hu < 0.3 and r < self.r_bluff * 3:
            return self._raise(s, max(s["bets"]) + 0.7 * pot)
        return passive
