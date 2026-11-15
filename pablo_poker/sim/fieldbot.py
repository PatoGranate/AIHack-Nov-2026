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
MODE = os.environ.get("FB_MODE", "abs")    # "abs": act on absolute hand strength (equity vs random hands); "rank": rank in own range
HS_FILE = os.path.join(ROOT, "data", "hs_pool.json")
_POOL = {}        # key -> recent HS values seen at that spot, all clones (warm start from HS_FILE)
_OWN = {}         # (bot, key) -> recent HS values of that clone at that spot
POOL_N, OWN_N, OWN_MIN = 3000, 500, 80
RAISE_BLUFF = {"flop": 0.12, "turn": 0.08, "river": 0.05}
PF3B_K = float(os.environ.get("FB_PF3B", "1.25"))


def _load_pool():
    if _POOL or not os.path.exists(HS_FILE):
        return
    try:
        with open(HS_FILE, encoding="utf-8") as f:
            for k, v in json.load(f).items():
                _POOL[k] = list(v)
    except (OSError, ValueError):
        pass


def save_pool(path=HS_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump({k: [round(x, 3) for x in v[-POOL_N:]] for k, v in _POOL.items()}, f)


def hand_strength(hole, bd, nopp, rng, m=72):
    """Equity of hole vs nopp uniformly random hands, random runout (draws count by their real equity)."""
    dead = set(hole) | set(bd)
    deck = [c for c in range(52) if c not in dead]
    need = 5 - len(bd)
    k = 2 * nopp + need
    tot = 0.0
    for _ in range(m):
        s = rng.sample(deck, k)
        full = bd + s[2 * nopp:]
        mv = evaluate(full + hole)
        best = 0
        ties = 0
        for i in range(nopp):
            v = evaluate(full + s[2 * i:2 * i + 2])
            if v > best:
                best, ties = v, 0
            elif v == best:
                ties += 1
        tot += 1.0 if mv > best else (1.0 / (ties + 2) if mv == best else 0.0)
    return tot / m


import bisect as _bisect
import math as _math
_SOFT = {}
SOFT_W = float(os.environ.get("FB_SOFT", "0.10"))      # width of the bet / check boundary in hand-strength quantile
TRAP = {"flop": 0.10, "turn": 0.25, "river": 0.35}    # share of strong hands checked to a known aggressive bettor behind


def _soft_t(target, w):
    """Centre t so that a hand at uniform quantile q bets with prob sigmoid((q - t) / w) at average rate target."""
    key = (round(target, 3), w)
    if key not in _SOFT:
        lo, hi = -1.0, 2.0
        for _ in range(30):
            t = (lo + hi) / 2
            m = sum(1.0 / (1.0 + _math.exp(-((i + 0.5) / 60.0 - t) / w)) for i in range(60)) / 60.0
            if m > target:
                lo = t
            else:
                hi = t
        _SOFT[key] = (lo + hi) / 2
    return _SOFT[key]


def _cdf(xs, v):
    if not xs:
        return None
    s = sorted(xs)
    return (_bisect.bisect_left(s, v) + _bisect.bisect_right(s, v)) * 0.5 / len(s)


def bet_probability(q,frequency,beta):
    if frequency<=0:return 0.
    if frequency>=1:return 1.
    bluff_mass=min(.99,frequency*max(0.,min(1.,beta)))
    if q<bluff_mass:return 1.
    value_target=max(0.,min(1.,(frequency-bluff_mass)/(1-bluff_mass)))
    value_q=max(0.,(q-bluff_mass)/(1-bluff_mass))
    return 1./(1.+_math.exp(-(value_q-_soft_t(value_target,SOFT_W))/SOFT_W))


_V3 = {}
SKILL_FILE = os.path.join(ROOT, "data", "field_skill.json")
_SKILL = {}


def reset_state(pool=None):
    """Start an independent experiment. Copy supplied frozen warm-start values."""
    for cache in (_MODEL, _POOL, _OWN, _SOFT, _SKILL, _V3):
        cache.clear()
    if pool is not None:
        _POOL.update({k: list(v) for k, v in pool.items()})


def normalize_response(pf, pr):
    pf = min(.97, max(.02, pf))
    pr = min(1.0-pf, max(0.0, pr))
    return pf, 1.0-pf-pr, pr


def strength_bucket(b):
    # The older live model has no overbet bucket. Borrow its largest first-bet
    # bucket, never its raise bucket, for a >=2-pot FIRST bet.
    return str(5 if b == 7 else b)


def v3pop():
    if not _V3:
        try:
            with open(os.path.join(ROOT, "data", "v3_model.json"), encoding="utf-8") as f:
                _V3.update(json.load(f)["pop"])
        except (OSError, ValueError, KeyError):
            _V3["lvl"] = {}
    return _V3


def skill_of(name):
    """Per-bot hand-reading skill in [-1, 1], fitted so the clone's showdown win rate matches the real bot's
    (tools/calib_skill.py). > 0: reads the bettor's range from the bet size; < 0: decides with noise."""
    if not _SKILL:
        _SKILL["_"] = 0.0
        if os.environ.get("FB_SKILL", "on") != "off" and os.path.exists(SKILL_FILE):
            with open(SKILL_FILE, encoding="utf-8") as f:
                _SKILL.update(json.load(f))
    return _SKILL.get(name, 0.0)


def hand_strength_vs(hole, bd, acc, nopp, rng, m=72):
    """Equity vs one bettor whose hand is drawn with acceptance acc[level] (its range as the bet size shows it)
    plus nopp-1 random hands."""
    dead = set(hole) | set(bd)
    deck = [c for c in range(52) if c not in dead]
    need = 5 - len(bd)
    tot = 0.0
    fallback = None
    for _ in range(m):
        for _t in range(8):
            a, b = rng.sample(deck, 2)
            if rng.random() < acc[level_street(a, b, bd)]:
                break
        else:
            # Exact weighted fallback; never accept a failed rejection sample.
            if fallback is None:
                combos = [(x,y) for i,x in enumerate(deck) for y in deck[i+1:]]
                weights = [acc[level_street(x,y,bd)] for x,y in combos]
                fallback = combos, weights
            combos,weights = fallback
            if sum(weights) <= 0:
                raise ValueError("opponent range has no feasible positive mass")
            a,b = rng.choices(combos, weights=weights, k=1)[0]
        rest = [c for c in deck if c != a and c != b]
        s = rng.sample(rest, 2 * (nopp - 1) + need)
        full = bd + s[2 * (nopp - 1):]
        mv = evaluate(full + hole)
        best = evaluate(full + [a, b])
        ties = 0
        for i in range(nopp - 1):
            v = evaluate(full + s[2 * i:2 * i + 2])
            if v > best:
                best, ties = v, 0
            elif v == best:
                ties += 1
        tot += 1.0 if mv > best else (1.0 / (ties + 2) if mv == best else 0.0)
    return tot / m


def _quantile(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    i = min(len(s) - 1, max(0, int(q * len(s))))
    return s[i]




def model():
    if not _MODEL:
        with open(MODEL_FILE, encoding="utf-8") as f:
            _MODEL.update(json.load(f))
        af = os.environ.get("FB_ADAPT", os.path.join(ROOT, "data", "field_adapt.json"))
        if af != "off" and os.path.exists(af):
            with open(af, encoding="utf-8") as f:
                _MODEL["adapt"] = json.load(f)
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
        _load_pool()
        self.name = name
        self.p = profile or m["bots"].get(name) or m["pop"]
        self.rng = random.Random(seed)
        self.hand = -1
        self.seat = 0
        self.level_counts = {}
        self.agg = {}         # seat -> [checked-to opportunities, bets] postflop (adaptation to aggressive bettors)
        self.hcur = 0

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
            # measured on rounds 38-53: clones 3-bet ~20% less often than the real field (0.048 vs 0.060)
            # (the slice logic loses part of the raise share); restore it out of the calls
            r2 = r * PF3B_K
            c = max(0.0, c - (r2 - r))
            return self._slice(s, r2, c, rsz)
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

    # ------------------------------------------------------------------ postflop, absolute strength
    def _q(self, key, q):
        """HS value at quantile q of what this clone (else all clones) held at this spot."""
        own = _OWN.get((self.name, key))
        if own and len(own) >= OWN_MIN:
            return _quantile(own, q)
        return _quantile(_POOL.get(key), q)

    def _note(self, key, hs):
        for d, k, cap in ((_POOL, key, POOL_N), (_OWN, (self.name, key), OWN_N)):
            v = d.setdefault(k, [])
            v.append(hs)
            if len(v) > cap + 200:
                del v[:200]

    def postflop_abs(self, s):
        me = s["seat"]
        street = s["street"]
        P = self.p["post"][street]
        bd = [to_int(c) for c in s["board"]]
        hole = [to_int(c) for c in s["hole_cards"]]
        pot, tc = s["pot"], s["to_call"]
        alive = sum(1 for f in s["folded"] if not f)
        nopp = max(1, alive - 1)
        hs = hand_strength(hole, bd, nopp, self.rng)
        sk = skill_of(self.name)
        if sk < 0:
            hs = min(1.0, max(0.0, hs + self.rng.gauss(0.0, 0.32 * -sk)))
        level = level_street(hole[0], hole[1], bd)
        hist = s["history"]
        hm = "hu" if alive == 2 else "mw"
        if tc <= 0:
            pfr = [h for h in hist if h["street"] == "preflop" and h["action"] == "raise"]
            cb = street == "flop" and bool(pfr) and pfr[-1]["seat"] == me
            F = P["bet"][("cb_" if cb else "") + hm]
            beta = BLUFF[street] * min(1.6, max(0.5, P["weak"] / max(0.05, model()["pop"]["post"][street]["weak"])))
            key = "%s|bet|%s%s" % (street, "cb_" if cb else "", hm)
            own = _OWN.get((self.name, key))
            q = _cdf(own if own and len(own) >= OWN_MIN else _POOL.get(key), hs)
            self._note(key, hs)
            if q is None:
                q = hs
            bet = self.rng.random() < bet_probability(q,F,beta)
            if bet and q > 0.8 and q >= F * beta:
                order = lambda x: (x - s["button"] - 1) % len(s["stacks"])
                behind = [j for j in range(len(s["stacks"])) if not s["folded"][j] and order(j) > order(me)]
                ad = model().get("adapt")
                if ad and behind:
                    lo, hi = ad["ref"]
                    a = 0.0
                    for j in behind:
                        g = self.agg.get(j, [0, 0])
                        a = max(a, ((g[1] + 3.0 * lo) / (g[0] + 3.0) - lo) / (hi - lo))
                    if self.rng.random() < min(1.0, max(0.0, a)) * TRAP[street]:
                        bet = False
            if "raise" in s["legal_actions"] and bet:
                frac = self._size_for_level(P, level)
                return self._raise_to(s, max(s["bets"]) + max(1, int(frac * pot)))
            return {"action": "check"}
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
        bettor = None
        for h in hist:
            if h["street"] == street and h["action"] == "raise":
                bettor = h["seat"]
        pf, pc, pr = self._adapt(street, b, bettor, pf, pc, pr)
        if sk > 0:
            tab = v3pop().get("lvl", {}).get(street, {}).get(strength_bucket(b))
            if tab:
                base = v3pop()["base"][street]
                f = [tab[L] / max(1e-3, base[L]) for L in range(4)]
                mx = max(f)
                acc = [(x / mx) ** max(1.0, sk) for x in f]      # skill above 1 reads the range more sharply
                hr = hand_strength_vs(hole, bd, acc, nopp, self.rng)
                k = min(1.0, sk)
                hs = (1 - k) * hs + k * hr
        can_raise = "raise" in s["legal_actions"]
        if not can_raise:
            pc, pr = pc + pr, 0.0
        key = "%s|vs|%d|%s" % (street, b, hm)
        tcont = self._q(key, pf)
        rb = RAISE_BLUFF[street]
        traise = self._q(key, 1.0 - pr * (1 - rb))
        self._note(key, hs)
        if tcont is None:
            tcont, traise = pf, 1.0 - pr * (1 - rb)
        bluff_r = can_raise and hs < tcont and self.rng.random() < pr * rb / max(0.05, pf)
        if can_raise and (hs >= traise or bluff_r):
            amt = max(s["bets"]) * P["rsz"]
            if self.rng.random() < P["rjam"] * (1.6 if level == 3 else 0.6):
                amt = 1e9
            return self._raise_to(s, amt)
        if hs >= tcont:
            return {"action": "call"}
        return {"action": "fold"}

    def _track(self, s):
        hist = s["history"]
        cur, street = None, None
        bets = {}
        for i, h in enumerate(hist):
            st = h["street"]
            if st != street:
                street, bets = st, {}
            a, j = h["action"], h["seat"]
            c = max(bets.values()) if bets else 0
            if i >= self.hcur and st != "preflop" and a in ("check", "raise") and c == 0:
                g = self.agg.setdefault(j, [0, 0])
                g[0] += 1
                g[1] += a == "raise"
            if a in ("raise", "small_blind", "big_blind"):
                bets[j] = h.get("amount") or 0
            elif a == "call":
                bets[j] = bets.get(j, 0) + (h.get("amount") or 0)
        self.hcur = len(hist)

    def _adapt(self, street, b, bettor, pf, pc, pr):
        """Shift the fold / raise rates toward how the real field answers a bettor of this observed aggression."""
        ad = model().get("adapt")
        if not ad or bettor is None:
            return pf, pc, pr
        g = self.agg.get(bettor, [0, 0])
        lo, hi = ad["ref"]
        bf = (g[1] + 3.0 * lo) / (g[0] + 3.0)
        a = min(1.0, max(0.0, (bf - lo) / (hi - lo)))
        if a <= 0:
            return pf, pc, pr
        d = ad[street].get(str(b))
        if not d:
            return pf, pc, pr
        return normalize_response(pf + a*d[0], min(.6, pr + a*d[1]))

    def act(self, s):
        if s["hand_number"] != self.hand:
            self.hcur = 0
            self.hand = s["hand_number"]
            self.lo, self.hi = 0.0, 1.0
            self.parts = None
            self.pct = CLS_PCT[hand_key(s["hole_cards"])]
        self._track(s)
        if s["street"] == "preflop":
            return self.preflop(s)
        if MODE == "abs":
            return self.postflop_abs(s)
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
