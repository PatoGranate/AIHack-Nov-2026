"""AlgoSoc Pokerbot v1.

Preflop: position-aware hand-tier chart.
Postflop: Monte-Carlo equity (time-budgeted) + pot-odds rules, with a light
per-seat aggression model so we call wider against maniacs.
Everything is wrapped so act() always returns a legal action.
"""
import random
import time

RANKS = "23456789TJQKA"
SUITS = "cdhs"

# ---------------------------------------------------------------- evaluator
# Precomputed: highest straight top rank per 13-bit rank mask (-1 if none).
_STRAIGHT = [-1] * 8192
for _m in range(8192):
    _x = (_m << 1) | (1 if _m & 4096 else 0)
    for _top in range(13, 3, -1):
        if (_x >> (_top - 4)) & 31 == 31:
            _STRAIGHT[_m] = _top - 1
            break
_POP = [bin(i).count("1") for i in range(8192)]


def _top_bits(mask, k):
    """Encode the k highest ranks of mask as 4-bit nibbles."""
    out = 0
    n = 0
    r = 12
    while n < k and r >= 0:
        if mask >> r & 1:
            out = (out << 4) | r
            n += 1
        r -= 1
    while n < k:
        out <<= 4
        n += 1
    return out


def evaluate(cards):
    """Integer score of the best 5-card hand among 5-7 int cards (higher wins)."""
    counts = [0] * 13
    smask = [0, 0, 0, 0]
    mask = 0
    for c in cards:
        r = c >> 2
        counts[r] += 1
        smask[c & 3] |= 1 << r
        mask |= 1 << r
    for fm in smask:
        if _POP[fm] >= 5:
            sh = _STRAIGHT[fm]
            if sh >= 0:
                return (8 << 20) | sh
            flush = (5 << 20) | _top_bits(fm, 5)
            break
    else:
        flush = 0
    quad = -1
    trips = []
    pairs = []
    for r in range(12, -1, -1):
        n = counts[r]
        if n == 4:
            quad = r
        elif n == 3:
            trips.append(r)
        elif n == 2:
            pairs.append(r)
    if quad >= 0:
        return (7 << 20) | (quad << 4) | _top_bits(mask & ~(1 << quad), 1)
    if trips and (len(trips) > 1 or pairs):
        second = trips[1] if len(trips) > 1 else -1
        if pairs and pairs[0] > second:
            second = pairs[0]
        return (6 << 20) | (trips[0] << 4) | second
    if flush:
        return flush
    sh = _STRAIGHT[mask]
    if sh >= 0:
        return (4 << 20) | sh
    if trips:
        t = trips[0]
        return (3 << 20) | (t << 8) | _top_bits(mask & ~(1 << t), 2)
    if len(pairs) >= 2:
        p1, p2 = pairs[0], pairs[1]
        return (2 << 20) | (p1 << 8) | (p2 << 4) | _top_bits(mask & ~(1 << p1) & ~(1 << p2), 1)
    if pairs:
        p = pairs[0]
        return (1 << 20) | (p << 12) | _top_bits(mask & ~(1 << p), 3)
    return _top_bits(mask, 5)


def to_int(card):
    return RANKS.index(card[0]) * 4 + SUITS.index(card[1])


# ---------------------------------------------------------------- preflop
def hand_key(hole):
    a, b = RANKS.index(hole[0][0]), RANKS.index(hole[1][0])
    if a < b:
        a, b = b, a
    if a == b:
        return RANKS[a] + RANKS[b]
    return RANKS[a] + RANKS[b] + ("s" if hole[0][1] == hole[1][1] else "o")


def _expand(spec):
    out = set()
    for tok in spec.split():
        out.add(tok)
    return out


# Tier 1: premium. Tier 2: strong. Tier 3: good. Tier 4: speculative. Tier 5: steal-only.
TIERS = {}
for _t, _spec in [
    (1, "AA KK QQ AKs AKo"),
    (2, "JJ TT AQs AQo AJs KQs"),
    (3, "99 88 77 ATs KJs QJs JTs KTs AJo KQo A9s QTs"),
    (4, "66 55 44 33 22 A8s A7s A6s A5s A4s A3s A2s T9s 98s 87s 76s 65s J9s K9s Q9s ATo KJo QJo T8s"),
    (5, "A9o A8o A7o A5o KTo QTo JTo K8s K7s K6s K5s Q8s J8s 97s 86s 75s 54s T9o 98o K9o"),
]:
    for _h in _expand(_spec):
        TIERS[_h] = _t


def tier_of(hole):
    return TIERS.get(hand_key(hole), 9)


# ---------------------------------------------------------------- agent
class Agent:
    def __init__(self):
        self.rng = random.Random()
        self.seat = 0
        self.n = 8
        self.spent = 0.0          # seconds of thinking this round (our estimate)
        self.bank = 9.0           # keep 1 s margin under the 10 s bank
        self.decisions = 0
        self.hands_seen = 0
        # per-seat stats: actions, aggressive actions, vpip hands
        self.acts = {}
        self.aggr = {}
        self.vpip = {}
        self.preflop_aggressor = None

    def on_table_start(self, info):
        self.seat = info.get("seat", 0)
        self.n = info.get("num_players", 8)
        self.total_hands = info.get("hands", 1000)

    def on_hand_end(self, summary):
        try:
            self.hands_seen += 1
            vp = set()
            for h in summary.get("history", []):
                a = h.get("action")
                if a in ("small_blind", "big_blind"):
                    continue
                s = h.get("seat")
                if h.get("street") == "preflop" and a in ("call", "raise"):
                    vp.add(s)
                self.acts[s] = self.acts.get(s, 0) + 1
                if a == "raise":
                    self.aggr[s] = self.aggr.get(s, 0) + 1
            for s in vp:
                self.vpip[s] = self.vpip.get(s, 0) + 1
        except Exception:
            pass

    # --------------------------------------------------------- helpers
    def looseness(self, state):
        """Average VPIP of opponents still in this hand (prior 0.3)."""
        me = state["seat"]
        vals = []
        for i, f in enumerate(state["folded"]):
            if i != me and not f:
                vals.append((self.vpip.get(i, 0) + 0.3 * 30) / (self.hands_seen + 30))
        return sum(vals) / len(vals) if vals else 0.3

    def aggression(self, seat):
        """Fraction of a seat's voluntary actions that are raises (shrunk to 0.2 prior)."""
        n = self.acts.get(seat, 0)
        return (self.aggr.get(seat, 0) + 0.2 * 20) / (n + 20)

    def budget(self):
        left = self.bank - self.spent
        if left <= 0.3:
            return 0.0
        hands_left = max(1, self.total_hands - self.hands_seen) if hasattr(self, "total_hands") else 500
        per = left / (hands_left * 0.8 + 1)
        return max(0.0, min(0.003, per))

    def equity(self, hole, board, n_opp, budget):
        """MC equity vs n_opp random hands, within `budget` seconds."""
        if budget <= 0:
            return None
        t_end = time.perf_counter() + budget
        my = [to_int(c) for c in hole]
        bd = [to_int(c) for c in board]
        used = set(my) | set(bd)
        deck = [c for c in range(52) if c not in used]
        k = min(n_opp, 3)
        need_board = 5 - len(bd)
        draw = need_board + 2 * k
        rng = self.rng
        wins = 0.0
        sims = 0
        ev = evaluate
        while True:
            for _ in range(8):
                s = rng.sample(deck, draw)
                full = bd + s[:need_board]
                me = ev(my + full)
                best = 0
                ties = 0
                for j in range(k):
                    o = ev(s[need_board + 2 * j:need_board + 2 * j + 2] + full)
                    if o > best:
                        best = o
                        ties = 0
                    elif o == best:
                        ties += 1
                if me > best:
                    wins += 1
                elif me == best:
                    wins += 1.0 / (ties + 2)
                sims += 1
            if time.perf_counter() > t_end or sims >= 2000:
                break
        e = wins / sims
        if n_opp > k:
            e = e ** (n_opp / float(k))
        return e

    # --------------------------------------------------------- api
    def act(self, state):
        t0 = time.perf_counter()
        try:
            out = self.decide(state)
        except Exception:
            out = None
        out = self.legalise(state, out)
        self.spent += time.perf_counter() - t0 + 0.0003  # + IPC estimate
        self.decisions += 1
        return out

    def legalise(self, state, out):
        legal = state.get("legal_actions") or []
        to_call = state.get("to_call") or 0
        if not isinstance(out, dict):
            out = {}
        a = out.get("action")
        if a == "raise" or a == "all_in":
            if "raise" in legal:
                lo, hi = state.get("min_raise_to"), state.get("max_raise_to")
                if a == "all_in" or lo is None:
                    return {"action": "all_in"}
                try:
                    amt = int(out.get("amount", lo))
                except Exception:
                    amt = lo
                return {"action": "raise", "amount": max(lo, min(hi, amt))}
            a = "call"
        if a == "call":
            return {"action": "call"} if to_call > 0 else {"action": "check"}
        if a == "check":
            return {"action": "check"} if to_call == 0 else {"action": "fold"}
        if a == "fold":
            return {"action": "check"} if to_call == 0 else {"action": "fold"}
        return {"action": "check"} if to_call == 0 else {"action": "fold"}

    def raise_to(self, state, amount):
        return {"action": "raise", "amount": int(amount)}

    def decide(self, state):
        if state["street"] == "preflop":
            return self.preflop(state)
        return self.postflop(state)

    # --------------------------------------------------------- preflop
    def position(self, state):
        n = len(state["stacks"])
        return (state["seat"] - state["button"]) % n  # 0=BTN 1=SB 2=BB 3=UTG ...

    def preflop(self, state):
        hole = state["hole_cards"]
        t = tier_of(hole)
        key = hand_key(hole)
        bb = state["big_blind"]
        to_call = state["to_call"]
        n = len(state["stacks"])
        pos = self.position(state)
        me = state["seat"]
        stack = state["stacks"][me] + state["bets"][me]
        raises = sum(1 for h in state["history"] if h["street"] == "preflop" and h["action"] == "raise")
        limpers = sum(1 for h in state["history"] if h["street"] == "preflop" and h["action"] == "call")
        current = max(state["bets"])
        live_after = 0  # unused in v1
        if pos == 0:
            open_tier = 5
        elif pos == n - 1:
            open_tier = 4
        elif pos == 1:
            open_tier = 4
        elif pos == 2:
            open_tier = 4
        elif pos >= n - 3:
            open_tier = 3
        else:
            open_tier = 2 if n >= 7 else 3

        loose = self.looseness(state)
        if loose > 0.4:
            open_tier = max(open_tier, 4)
        if raises == 0:
            if t <= open_tier or (t == 4 and limpers >= 2 and pos != 3):
                if t <= 3 or limpers == 0 or loose > 0.4:
                    size = 4 if loose > 0.4 else 3
                    return self.raise_to(state, bb * (size + limpers) + (bb if pos in (1, 2) else 0))
                return {"action": "call"}
            if to_call == 0:
                return {"action": "check"}
            # limp behind / complete with speculative hands when cheap
            if t <= 4 and to_call <= bb and limpers >= 1:
                return {"action": "call"}
            return {"action": "fold"}

        # facing a raise
        raiser = None
        for h in reversed(state["history"]):
            if h["action"] == "raise":
                raiser = h["seat"]
                break
        loose = raiser is not None and self.aggression(raiser) > 0.35
        call_frac = to_call / float(max(stack, 1))

        # Against maniacs the chart is too tight: use equity vs random hands.
        if loose and t > 1 and self.hands_seen >= 30:
            n_in = sum(1 for i, f in enumerate(state["folded"]) if i != me and not f
                       and (state["bets"][i] > bb or i == raiser))
            e = self.equity(hole, [], max(1, n_in), min(self.budget(), 0.002))
            if e is not None:
                pot_odds = to_call / float(state["pot"] + to_call)
                if e >= 0.62 and n_in == 1 and raises <= 2:
                    return self.raise_to(state, current * 3)
                if e - 0.04 >= pot_odds:
                    return {"action": "call"}
                return {"action": "fold"}

        if raises == 1:
            if t == 1:
                return self.raise_to(state, current * 3 + state["pot"] - current)
            if t == 2:
                if loose or key in ("JJ", "AQs"):
                    return self.raise_to(state, current * 3)
                return {"action": "call"} if call_frac < 0.15 else {"action": "fold"}
            if t == 3:
                if call_frac <= 0.05 or (loose and call_frac <= 0.1):
                    return {"action": "call"}
                return {"action": "fold"}
            if t == 4:
                if call_frac <= 0.04 and (pos in (0, 2, n - 1) or limpers + 1 >= 2):
                    return {"action": "call"}
                return {"action": "fold"}
            return {"action": "fold"}

        # 3-bet or more
        if key in ("AA", "KK"):
            return {"action": "all_in"}
        if key in ("QQ", "AKs", "AKo"):
            if call_frac <= 0.35 or loose:
                return {"action": "all_in"} if raises >= 3 or loose else {"action": "call"}
            return {"action": "call"} if call_frac <= 0.5 else {"action": "fold"}
        if key in ("JJ", "TT", "AQs") and (call_frac <= 0.12 or (loose and call_frac <= 0.5)):
            return {"action": "call"}
        return {"action": "fold"}

    # --------------------------------------------------------- postflop
    def postflop(self, state):
        me = state["seat"]
        folded = state["folded"]
        n_opp = sum(1 for i in range(len(folded)) if i != me and not folded[i])
        pot = state["pot"]
        to_call = state["to_call"]
        stack = state["stacks"][me]
        e = self.equity(state["hole_cards"], state["board"], max(1, n_opp), self.budget())
        if e is None:
            return {"action": "check"} if to_call == 0 else {"action": "fold"}
        street = state["street"]
        bets = state["bets"]
        current = max(bets)

        # Who was the last preflop raiser?
        pf_raiser = None
        for h in state["history"]:
            if h["street"] == "preflop" and h["action"] == "raise":
                pf_raiser = h["seat"]
        street_actions = [h for h in state["history"] if h["street"] == street]

        if to_call == 0:
            if e >= 0.75:
                return self.raise_to(state, current + max(state["big_blind"], int(pot * 0.9)))
            if e >= 0.55:
                return self.raise_to(state, current + max(state["big_blind"], int(pot * 0.6)))
            # c-bet heads-up as preflop raiser on the flop
            if street == "flop" and pf_raiser == me and n_opp == 1 and e >= 0.30 and not street_actions:
                return self.raise_to(state, current + max(state["big_blind"], int(pot * 0.4)))
            if street == "flop" and pf_raiser == me and n_opp == 1 and e >= 0.30:
                if all(h["action"] == "check" for h in street_actions):
                    return self.raise_to(state, current + max(state["big_blind"], int(pot * 0.4)))
            return {"action": "check"}

        # facing a bet
        bettor = None
        for h in reversed(street_actions):
            if h["action"] == "raise":
                bettor = h["seat"]
                break
        agg = self.aggression(bettor) if bettor is not None else 0.2
        pot_odds = to_call / float(pot + to_call)
        # Betting ranges are stronger than random: discount our equity,
        # less against aggressive bots who bet anything.
        n_raises = sum(1 for h in street_actions if h["action"] == "raise")
        discount = 0.12 if agg < 0.15 else (0.06 if agg < 0.3 else 0.0)
        discount += 0.05 * (n_raises - 1)
        size_ratio = to_call / float(max(pot - to_call, 1))
        if size_ratio > 0.8:
            discount += 0.04
        e_adj = e - discount

        if e >= 0.85 and "raise" in state["legal_actions"]:
            return self.raise_to(state, current * 2 + pot)
        if e_adj >= 0.72 and n_raises <= 1 and "raise" in state["legal_actions"]:
            return self.raise_to(state, current * 3)
        if e_adj >= pot_odds + 0.03:
            return {"action": "call"}
        return {"action": "fold"}
