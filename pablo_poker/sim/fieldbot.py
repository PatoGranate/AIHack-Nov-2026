"""FieldBot: a behavioural clone of one real bot, driven by data/field_model.json.

Every decision reproduces the real bot's measured frequency for that situation
(tools/build_field_model.py), and WHICH hands take each action is decided by where
the hand sits inside the clone's own current range:

  preflop   the range is a slice [lo, hi] of the hand ranking; "raise 9%, call 12%" means the
            top 9% of the slice raises and the next 12% calls, and the slice narrows accordingly
  postflop  the range is a set of sampled hands (particles) consistent with every action so far;
            the hand's rank among them (draws count before the river) is compared with the
            frequencies: the top of the range bets / raises, a measured share of the bottom
            bluffs, the bottom folds to a bet of that size

So a clone that folds 75% to a 2x-pot shove calls with the top quarter of its range only,
which is what makes its showdown ranges (and the price of bluffing or thin value) realistic.
"""
import json
import os
import random

from pokerbot.v2 import ALLC, CLS_PCT, NC, evaluate, hand_key, level_street, size_bucket, to_int

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_FILE = os.path.join(ROOT, "data", "field_model.json")
_MODEL = {}
N_PART = 80
BLUFF = {"flop": 0.30, "turn": 0.28, "river": 0.24}       # share of a betting range taken from the bottom
DRAW = {3: (0.60, 0.50, 0.74), 4: (0.47, 0.38, 0.56)}     # percentile floor: flush draw, straight draw, both


def model():
    if not _MODEL:
        with open(MODEL_FILE, encoding="utf-8") as f:
            _MODEL.update(json.load(f))
    return _MODEL


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


def allocate_rates(masses, target, frequency):
    """Project desired strength mix onto available hands at the measured rate.

    A class absent on this board cannot supply its target share. Redistribute
    that share among feasible classes rather than silently reducing aggression.
    """
    goal=min(frequency,sum(masses))
    weights=[max(.001,t)/m if m else 0. for m,t in zip(masses,target)]
    lo,hi=0.,1.
    while sum(m*min(1.,hi*w) for m,w in zip(masses,weights))<goal-1e-10:
        hi*=2
    for _ in range(24):
        mid=(lo+hi)/2
        if sum(m*min(1.,mid*w) for m,w in zip(masses,weights))<goal:lo=mid
        else:hi=mid
    return [min(1.,hi*w) for w in weights]


def _draw_floor(a, b, bd, bsc, bmask, val):
    """Percentile floor for a drawing hand on a flop/turn board (0 if none)."""
    fl, stt, both = DRAW[len(bd)]
    fd = False
    if val < (5 << 20):
        sa, sb = a & 3, b & 3
        if bsc[sa] + 1 + (sb == sa) == 4 or bsc[sb] + 1 + (sa == sb) == 4:
            fd = True
    sd = False
    if val < (4 << 20):
        m = bmask | (1 << (a >> 2)) | (1 << (b >> 2))
        if m != bmask:
            m2 = (m << 1) | (1 if m & (1 << 12) else 0)
            b2 = (bmask << 1) | (1 if bmask & (1 << 12) else 0)
            for i in range(0, 10):
                w = 0b1111 << i
                if (m2 & w) == w and (b2 & w) != w:
                    sd = True
                    break
    if fd and sd:
        return both
    if fd:
        return fl
    if sd:
        return stt
    return 0.0


class FieldBot:
    def __init__(self, name, seed=None, profile=None):
        m = model()
        self.name = name
        self.p = profile or m["bots"].get(name) or m["pop"]
        self.rng = random.Random(seed)
        self.hand = -1
        self.seat = 0
        self.level_counts = {}

    def on_table_start(self, info):
        self.seat = info.get("seat", 0)

    # ------------------------------------------------------------------ helpers
    def _raise_to(self, s, amount):
        lo, hi = s.get("min_raise_to"), s.get("max_raise_to")
        if "raise" not in s["legal_actions"] or lo is None or hi is None:
            return {"action": "call"} if "call" in s["legal_actions"] else {"action": "check"}
        amount = int(max(lo, min(hi, amount)))
        return {"action": "raise", "amount": amount}

    def _passive(self, s):
        return {"action": "check"} if "check" in s["legal_actions"] else {"action": "fold"}

    def _pick(self, dist, u=None):
        """Sample a key of {value: share}; with u in [0,1] take that quantile of the sorted values instead."""
        items = sorted(((float(k), v) for k, v in dist.items()), key=lambda kv: kv[0])
        tot = sum(v for _, v in items) or 1.0
        x = (self.rng.random() if u is None else min(0.999, max(0.0, u))) * tot
        for k, v in items:
            x -= v
            if x <= 0:
                return k
        return items[-1][0]

    # ------------------------------------------------------------------ preflop
    def _slice(self, s, p_raise, p_call, raise_amount):
        """Top p_raise of the current slice raises, the next p_call calls, the rest folds."""
        w = self.hi - self.lo
        r = (self.pct - self.lo) / w if w > 1e-9 else 1.0
        if r <= p_raise and "raise" in s["legal_actions"]:
            self.hi = self.lo + max(p_raise, 0.004) * w
            return self._raise_to(s, raise_amount)
        if r <= p_raise + p_call:
            if r > p_raise:
                self.lo, self.hi = self.lo + p_raise * w, self.lo + (p_raise + p_call) * w
            return {"action": "call"} if "call" in s["legal_actions"] else {"action": "check"}
        if "check" in s["legal_actions"]:
            self.lo = self.lo + p_raise * w
            return {"action": "check"}
        return {"action": "fold"}

    def preflop(self, s):
        pre = self.p["pre"]
        me = s["seat"]
        n = len(s["stacks"])
        bb = s.get("big_blind", 20)
        acts = [h for h in s["history"] if h["street"] == "preflop" and h["action"] not in ("small_blind", "big_blind")]
        raises = [h for h in acts if h["action"] == "raise"]
        cur = max(s["bets"])
        tc = s["to_call"]
        g = pos_group(me, s["button"], n)
        if tc >= 1000:
            f, c = pre["vs_jam"]
            return self._slice(s, 0.0, c, 0)
        if not raises:
            limpers = sum(1 for h in acts if h["action"] == "call")
            amt = self._pick(pre["open_sz"]) + bb * limpers
            return self._slice(s, pre["rfi"][g], pre["limp"][g], amt)
        mine = [h for h in raises if h["seat"] == me]
        rsz = cur * pre["rsz"]
        if self.rng.random() < pre["rjam"]:
            rsz = 1e9
        if len(raises) == 1:
            f, c, r = pre["vs_open"]["bb" if g == "BB" else ("sb" if g == "SB" else "other")]
            return self._slice(s, r, c, rsz)
        if len(raises) == 2:
            f, c, r = pre["vs_3b"]["opener" if mine else "cold"]
            return self._slice(s, r, c, rsz)
        f, c, r = pre["vs_4b"]
        if not mine:
            c, r = c * 0.3, r * 0.3
        return self._slice(s, r, c, 1e9)

    # ------------------------------------------------------------------ postflop
    def _particles(self, bd):
        lo = int(self.lo * NC)
        hi = max(lo + 24, int(self.hi * NC))
        hi = min(NC, hi)
        lo = max(0, min(lo, hi - 24))
        dead = set(bd)
        out = []
        rng = self.rng
        for _ in range(N_PART * 3):
            h = ALLC[rng.randrange(lo, hi)]
            if h[0] not in dead and h[1] not in dead:
                out.append(h)
                if len(out) >= N_PART:
                    break
        return out

    def _rank(self, hole, bd):
        """(my rank in my range: 0 = best .. 1 = worst, per-particle ranks)."""
        parts = self.parts
        vals = [evaluate(bd + [a, b]) for a, b in parts]
        mine = evaluate(bd + hole)
        n = len(parts)
        order = sorted(vals)
        import bisect
        q = [(bisect.bisect_left(order, v) + bisect.bisect_right(order, v)) * 0.5 / n for v in vals]
        mq = (bisect.bisect_left(order, mine) + bisect.bisect_right(order, mine)) * 0.5 / n
        if len(bd) < 5:
            bsc = [0, 0, 0, 0]
            bmask = 0
            for c in bd:
                bsc[c & 3] += 1
                bmask |= 1 << (c >> 2)
            for i, (a, b) in enumerate(parts):
                fl = _draw_floor(a, b, bd, bsc, bmask, vals[i])
                if fl > q[i]:
                    q[i] = fl
            fl = _draw_floor(hole[0], hole[1], bd, bsc, bmask, mine)
            if fl > mq:
                mq = fl
        r = [0.0] * n
        oq = sorted(q)
        for i in range(n):
            r[i] = 1.0 - (bisect.bisect_left(oq, q[i]) + bisect.bisect_right(oq, q[i])) * 0.5 / n
        mr = 1.0 - (bisect.bisect_left(oq, mq) + bisect.bisect_right(oq, mq)) * 0.5 / n
        return mr, r

    def _keep(self, ranks, lo, hi, lo2=None, hi2=None):
        """Narrow the range to the particles whose rank falls in [lo, hi] (or the second band)."""
        kept = [p for p, r in zip(self.parts, ranks) if lo <= r <= hi or (lo2 is not None and lo2 <= r <= hi2)]
        if kept:
            self.parts = kept

    def _size_for_level(self, P, level, kind="bet"):
        """Couple measured sizes with observed strength; validation remains mandatory.

        Use a bounded likelihood ratio, not a hard showdown-strength constraint:
        shown hands are selected by opponents' calls and future streets.
        """
        dist = P["sz"]
        strength = P.get("strength", {}).get(kind, {})
        if not strength:
            return self._pick(dist)
        base = sum(w * strength.get(str(7 if float(sz) >= 2 else size_bucket(float(sz), False)),
                                     [.25] * 4)[level] for sz, w in dist.items())
        weights = {}
        for sz, w in dist.items():
            b = str(7 if float(sz) >= 2 else size_bucket(float(sz), False))
            ratio = strength.get(b, [.25] * 4)[level] / max(.02, base)
            weights[sz] = w * max(.05, min(12., ratio))
        return self._pick(weights)

    def postflop(self, s):
        me = s["seat"]
        street = s["street"]
        P = self.p["post"][street]
        bd = [to_int(c) for c in s["board"]]
        hole = [to_int(c) for c in s["hole_cards"]]
        if self.parts is None:
            self.parts = self._particles(bd)
        else:
            dead = set(bd)
            self.parts = [p for p in self.parts if p[0] not in dead and p[1] not in dead] or self._particles(bd)
        mr, ranks = self._rank(hole, bd)
        pot, tc = s["pot"], s["to_call"]
        alive = sum(1 for f in s["folded"] if not f)
        hist = s["history"]
        if tc <= 0:
            pfr = [h for h in hist if h["street"] == "preflop" and h["action"] == "raise"]
            cb = street == "flop" and bool(pfr) and pfr[-1]["seat"] == me
            F = P["bet"][("cb_" if cb else "") + ("hu" if alive == 2 else "mw")]
            beta = BLUFF[street] * min(1.6, max(0.5, P["weak"] / max(0.05, model()["pop"]["post"][street]["weak"])))
            v_hi = F * (1 - beta)
            b_lo = 1 - F * beta
            if "raise" in s["legal_actions"] and (mr <= v_hi or mr >= b_lo):
                frac = self._size_for_level(P, level_street(hole[0], hole[1], bd))
                self._keep(ranks, 0.0, v_hi, b_lo, 1.0)
                return self._raise_to(s, max(s["bets"]) + max(1, int(frac * pot)))
            self._keep(ranks, v_hi, b_lo)
            return {"action": "check"}
        # facing a bet: its size bucket, as measured in the model
        sb = [0] * len(s["stacks"])
        last_add, n_raise = tc, 0
        for h in hist:
            if h["street"] != street:
                continue
            if h["action"] == "raise":
                last_add = h["amount"] - sb[h["seat"]]
                sb[h["seat"]] = h["amount"]
                n_raise += 1
            elif h["action"] == "call":
                sb[h["seat"]] += h["amount"]
        frac = last_add / float(max(1, pot - last_add))
        b = 7 if frac >= 2.0 else size_bucket(frac, n_raise >= 2)
        pf, pc, pr = P["vs"][str(b)]
        can_raise = "raise" in s["legal_actions"]
        if not can_raise:
            pc, pr = pc + pr, 0.0
        cont = 1.0 - pf
        levels = [level_street(a, b, bd) for a,b in self.parts]
        level = level_street(hole[0], hole[1], bd)
        targets = P.get("strength", {}).get("raise", {})
        ordinary = targets.get("6", [.1,.1,.2,.6])
        jam = targets.get("7", ordinary)
        target = [(1-P["rjam"])*v + P["rjam"]*j for v,j in zip(ordinary,jam)]
        # Allocate raises to observed strength classes, constrained by hands
        # actually present in the continuing range. Never manufacture monsters.
        # Rates are conditional on the distribution of hands across opportunities,
        # not each individual narrow range. Otherwise a range without strong
        # hands is forced to supply its full quota as weak raises.
        counts = self.level_counts.setdefault((street, b), [7.,6.,4.,3.])
        if can_raise:
            counts[level] += 1
        total = sum(counts)
        masses = [x/total for x in counts]
        rates = [min(1., pr*t/m) for t,m in zip(target,masses)]
        if can_raise and self.rng.random() < rates[level]:
            weights = [rates[L] for L in levels]
            if sum(weights):
                self.parts = self.rng.choices(self.parts, weights=weights, k=N_PART)
            amt = max(s["bets"]) * P["rsz"]
            jam_prob = min(1., P["rjam"]*jam[level]/max(.01,target[level]))
            if self.rng.random() < jam_prob:
                amt = 1e9
            return self._raise_to(s, amt)
        if mr <= cont:
            weights = [(1-rates[L]) if r <= cont else 0. for r,L in zip(ranks,levels)]
            if sum(weights):
                self.parts = self.rng.choices(self.parts, weights=weights, k=N_PART)
            return {"action": "call"}
        return {"action": "fold"}

    def act(self, s):
        if s["hand_number"] != self.hand:
            self.hand = s["hand_number"]
            self.lo, self.hi = 0.0, 1.0
            self.parts = None
            self.pct = CLS_PCT[hand_key(s["hole_cards"])]
        if s["street"] == "preflop":
            return self.preflop(s)
        return self.postflop(s)


def mix(kind="recent", weight_total=40, exclude=("kaiserbot",)):
    """Opponent mix for a simulated table: one clone per real bot, weighted by its (recency-weighted) presence."""
    m = model()
    bots = {k: v for k, v in m["bots"].items() if k not in exclude}
    tot = sum(v["w"] for v in bots.values()) or 1.0
    out = []
    for k, v in bots.items():
        w = weight_total * v["w"] / tot
        if w >= 0.3:
            out.append((w, {"kind": "fieldbot", "name": k, "strategy_id": "fb:" + k[:24]}))
    return out
