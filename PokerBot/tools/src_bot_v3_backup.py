"""AlgoSoc Pokerbot v3.

Preflop: hand ranking + offline equity tables vs ranges; opponents' ranges are
estimated from their observed VPIP / PFR / shove rate this round.
Postflop: Monte-Carlo vs each opponent's *weighted* range (preflop range,
narrowed by how they've bet this hand), plus a per-opponent continue model fit
to their observed fold-to-bet rate. Actions are chosen by approximate EV
(check / bet sizes, fold / call / raise sizes).
Everything is wrapped so act() always returns a legal action.
"""
import gc
import random
import time

#@@EVAL@@

#@@TABLES@@

DEBUG = False
_BUILT = [False]


def prebuild():
    """Fill the 5/6/7-card rank table (~1 s) so act() never misses."""
    if _BUILT[0]:
        return
    _BUILT[0] = True
    counts = [0] * 13

    def rec(n, start, prod):
        if n == 0:
            if prod not in RT:
                RT[prod] = _rank_score(counts)
            return
        for r in range(start, 13):
            if counts[r] < 4:
                counts[r] += 1
                rec(n - 1, r, prod * _PR[r])
                counts[r] -= 1
    for k in (5, 6, 7):
        rec(k, 0, 1)


P = {
    #@@PARAMS@@
}

# ---------------------------------------------------------------- tables
CLS_PCT = {}
ALLC = []
_cum = 0
for _c in RANK:
    _a, _b = RANKS.index(_c[0]), RANKS.index(_c[1])
    for _s1 in range(4):
        for _s2 in range(4):
            _x, _y = _a * 4 + _s1, _b * 4 + _s2
            if _x == _y:
                continue
            if len(_c) == 2 and _s1 >= _s2:
                continue
            if len(_c) == 3 and (_c[2] == "s") != (_s1 == _s2):
                continue
            ALLC.append((_x, _y))
    CLS_PCT[_c] = len(ALLC) / 1326.0
NC = len(ALLC)


def to_int(card):
    return RANKS.index(card[0]) * 4 + SUITS.index(card[1])


def hand_key(hole):
    a, b = RANKS.index(hole[0][0]), RANKS.index(hole[1][0])
    if a < b:
        a, b = b, a
    if a == b:
        return RANKS[a] + RANKS[b]
    return RANKS[a] + RANKS[b] + ("s" if hole[0][1] == hole[1][1] else "o")


def eq_vs_range(cls, f):
    row = EQR[cls]
    if f <= F[0]:
        return row[0]
    for i in range(1, len(F)):
        if f <= F[i]:
            t = (f - F[i - 1]) / (F[i] - F[i - 1])
            return row[i - 1] * (1 - t) + row[i] * t
    return row[-1]


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Stats:
    __slots__ = ("hands", "vpip", "pfr", "big", "pbet", "pcall", "pcheck", "faced", "ffold",
                 "f3", "f3fold", "sd", "sdwin")

    def __init__(self):
        for k in Stats.__slots__:
            setattr(self, k, 0)


# ---------------------------------------------------------------- agent
class Agent:
    def __init__(self):
        self.rng = random.Random()
        self.seat = 0
        self.n = 8
        self.total_hands = 1000
        self.spent = 0.0
        self.bank = 8.5
        self.hands_seen = 0
        self.st = {}
        self.post_decisions = 0

    def on_table_start(self, info):
        self.seat = info.get("seat", 0)
        self.n = info.get("num_players", 8)
        self.total_hands = info.get("hands", 1000) or 1000
        try:
            prebuild()
        except Exception:
            pass
        try:
            gc.collect()
            gc.freeze()
            gc.disable()   # avoid GC pauses inside act(); we collect between hands
        except Exception:
            pass

    def S(self, seat):
        s = self.st.get(seat)
        if s is None:
            s = self.st[seat] = Stats()
        return s

    # ------------------------------------------------------------- stats
    def on_hand_end(self, summary):
        try:
            self._learn(summary)
        except Exception:
            pass
        if self.hands_seen % 50 == 0:
            try:
                gc.collect()
            except Exception:
                pass

    def _learn(self, summary):
        self.hands_seen += 1
        hist = summary.get("history") or []
        seats = set(h.get("seat") for h in hist)
        bb = 20
        for h in hist:
            if h.get("action") == "big_blind":
                bb = h.get("amount") or 20
        for s in seats:
            self.S(s).hands += 1
        street = None
        cur = 0
        nraise = 0
        vp, pr = set(), set()
        for h in hist:
            a = h.get("action")
            s = h.get("seat")
            st = h.get("street")
            if st != street:
                street = st
                cur = bb if st == "preflop" else 0
                nraise = 0
                bets = {}
            if a in ("small_blind", "big_blind"):
                bets[s] = h.get("amount") or 0
                continue
            o = self.S(s)
            if st == "preflop":
                if a in ("call", "raise"):
                    vp.add(s)
                if nraise >= 1 and a in ("fold", "call", "raise"):
                    o.f3 += 1
                    if a == "fold":
                        o.f3fold += 1
                if a == "raise":
                    pr.add(s)
                    if (h.get("amount") or 0) >= 600:
                        o.big += 1
            else:
                if a == "raise":
                    o.pbet += 1
                elif a == "call":
                    o.pcall += 1
                elif a == "check":
                    o.pcheck += 1
                if cur > 0 and a in ("fold", "call", "raise"):
                    o.faced += 1
                    if a == "fold":
                        o.ffold += 1
            if a == "raise":
                cur = h.get("amount") or cur
                nraise += 1
        for s in vp:
            self.S(s).vpip += 1
        for s in pr:
            self.S(s).pfr += 1
        shown = summary.get("shown") or {}
        for k in shown:
            try:
                o = self.S(int(k))
                o.sd += 1
            except Exception:
                pass

    def vpip(self, s):
        o = self.S(s)
        return (o.vpip + P["pri_vpip"] * 12) / (o.hands + 12)

    def pfr(self, s):
        o = self.S(s)
        return (o.pfr + P["pri_pfr"] * 12) / (o.hands + 12)

    def bigrate(self, s):
        o = self.S(s)
        return (o.big + 0.05 * 10) / (o.hands + 10)

    def ftb(self, s):
        o = self.S(s)
        return (o.ffold + P["pri_ftb"] * 8) / (o.faced + 8)

    def af(self, s):
        o = self.S(s)
        return (o.pbet + 0.3 * 10) / (o.pbet + o.pcall + o.pcheck + 10)

    # ------------------------------------------------------------- time
    def budget(self):
        left = self.bank - self.spent
        if left <= 0.4:
            return 0.0
        hands_left = max(1, self.total_hands - self.hands_seen)
        per = left / (hands_left * 0.9 + 1)
        return clamp(per, 0.0, P["max_ms"] / 1000.0)

    # ------------------------------------------------------------- api
    def act(self, state):
        t0 = time.perf_counter()
        try:
            out = self.decide(state)
        except Exception:
            if DEBUG:
                raise
            out = None
        out = self.legalise(state, out)
        self.spent += time.perf_counter() - t0 + 0.0002
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
                if lo is None or hi is None:
                    return {"action": "all_in"}
                if a == "all_in":
                    return {"action": "raise", "amount": int(hi)}
                try:
                    amt = int(out.get("amount", lo))
                except Exception:
                    amt = lo
                return {"action": "raise", "amount": int(max(lo, min(hi, amt)))}
            a = "call"
        if a == "call":
            if to_call > 0 and "call" in legal:
                return {"action": "call"}
            return {"action": "check"} if to_call == 0 else {"action": "fold"}
        return {"action": "check"} if to_call == 0 else {"action": "fold"}

    def decide(self, state):
        if state["street"] == "preflop":
            return self.preflop(state)
        return self.postflop(state)

    # ------------------------------------------------------------- ranges
    def pf_range(self, state, j):
        """(lo, hi) fraction of ALLC that seat j's preflop actions suggest."""
        raised = False
        threeb = False
        called = False
        big = False
        nr = 0
        for h in state["history"]:
            if h["street"] != "preflop":
                break
            a = h["action"]
            if h["seat"] == j:
                if a == "raise":
                    raised = True
                    if nr >= 1:
                        threeb = True
                    if (h.get("amount") or 0) >= 600:
                        big = True
                elif a == "call":
                    called = True
            if a == "raise":
                nr += 1
        if big:
            f = clamp(max(self.bigrate(j), self.pfr(j) * 0.25), 0.025, 0.6)
            return 0.0, f
        if threeb:
            return 0.0, clamp(self.pfr(j) * P["r3_mult"], 0.025, 0.4)
        if raised:
            return 0.0, clamp(self.pfr(j), 0.04, 0.7)
        if called:
            hi = clamp(self.vpip(j), 0.1, 1.0)
            lo = clamp(self.pfr(j) * P["call_lo"], 0.0, hi * 0.5) if nr else 0.0
            return lo, hi
        return 0.0, 1.0

    # ------------------------------------------------------------- preflop
    def preflop(self, state):
        hole = state["hole_cards"]
        key = hand_key(hole)
        pct = CLS_PCT[key]
        bb = state["big_blind"]
        tc = state["to_call"]
        n = len(state["stacks"])
        me = state["seat"]
        btn = state["button"]
        pos = (me - btn) % n          # 0 BTN 1 SB 2 BB 3 UTG ...
        bets = state["bets"]
        stack = state["stacks"][me] + bets[me]
        cur = max(bets)
        pot = state["pot"]
        hist = [h for h in state["history"] if h["street"] == "preflop"]
        raises = [h for h in hist if h["action"] == "raise"]
        nlimp = sum(1 for h in hist if h["action"] == "call")
        folded = state["folded"]
        live = [i for i in range(n) if not folded[i] and i != me]
        acted = set(h["seat"] for h in hist if h["action"] not in ("small_blind", "big_blind"))
        behind = [i for i in live if i not in acted and i != me]

        if not raises:
            # open / iso / BB option
            if pos == 2 and tc == 0:
                if pct <= P["bb_raise"]:
                    return self.r(bb * (P["open_size"] + 1 + nlimp))
                return {"action": "check"}
            pk = {0: "o_btn", 1: "o_sb"}.get(pos)
            if pk is None:
                from_end = (n - pos) % n  # CO=1, HJ=2, ...
                pk = {1: "o_co", 2: "o_hj", 3: "o_mp"}.get(from_end, "o_ep")
            f = P[pk]
            if behind:
                av = sum(self.vpip(i) for i in behind) / len(behind)
                f *= clamp(1 + P["steal_k"] * (P["pri_vpip"] - av), 0.6, 2.2)
            if nlimp:
                f = max(f * P["iso_mult"], 0.06)
            if pct <= f:
                tabv = sum(self.vpip(i) for i in live) / max(1, len(live))
                size = P["open_size"] + (P["loose_add"] if tabv > 0.4 else 0) + nlimp
                if pos == 1:
                    size += 0.5
                return self.r(bb * size)
            if nlimp and tc <= bb and pct <= P["overlimp"] and pos in (0, 1, n - 1):
                return {"action": "call"}
            if pos == 1 and nlimp == 0 and tc <= bb // 2 and pct <= P["sb_limp"]:
                return {"action": "call"}
            return {"action": "check"} if tc == 0 else {"action": "fold"}

        # facing raise(s)
        raiser = raises[-1]["seat"]
        lo, hi = self.pf_range(state, raiser)
        e = eq_vs_range(key, hi)
        others = [i for i in live if i != raiser and (bets[i] > bb or i in acted and bets[i] >= cur)]
        extra = len([i for i in others if bets[i] >= cur])
        if extra:
            e = e ** (1 + P["multi_exp"] * extra)
        order = lambda s: (s - btn - 1) % n
        ip = order(me) > order(raiser)
        allin_call = tc >= state["stacks"][me]
        real = 1.0 if allin_call else (P["real_ip"] if ip else P["real_oop"])
        if pct <= 0.03:
            real = 1.0
        ev_call = e * real * (pot + tc) - tc
        nr = len(raises)
        if "raise" in state["legal_actions"] and nr < 4:
            thr = P["eq_3b"] if nr == 1 else P["eq_4b"]
            if e >= thr and not (extra and e < thr + 0.05):
                tgt = cur * (P["3b_ip"] if ip else P["3b_oop"]) + (pot - cur - bets[me]) * 0.5
                if nr >= 2 or tgt >= stack * 0.35:
                    return {"action": "all_in"}
                return self.r(tgt)
        if ev_call > P["pf_call_margin"] * bb:
            return {"action": "call"}
        return {"action": "fold"}

    def r(self, amt):
        return {"action": "raise", "amount": int(amt)}

    # ------------------------------------------------------------- postflop
    def opp_models(self, state, me):
        folded = state["folded"]
        stacks = state["stacks"]
        hist = state["history"]
        street = state["street"]
        models = []
        for j in range(len(folded)):
            if j == me or folded[j]:
                continue
            lo, hi = self.pf_range(state, j)
            agg = 0
            calls = 0
            raise_over = False
            for h in hist:
                if h["seat"] != j or h["street"] == "preflop":
                    continue
                if h["action"] == "raise":
                    agg += 1
                elif h["action"] == "call":
                    calls += 1
            # did j raise over someone else's bet this street?
            seen_bet = False
            for h in hist:
                if h["street"] != street:
                    continue
                if h["action"] == "raise":
                    if h["seat"] == j and seen_bet:
                        raise_over = True
                    seen_bet = True
            bl = clamp(P["bluff_base"] + (self.af(j) - 0.3) * P["bluff_af"], 0.04, 0.9)
            if agg >= 2 or raise_over:
                w = (bl * P["w_r_air"], P["w_r_weak"], P["w_r_mid"], 1.0)
            else:
                w = (bl, P["w_b_weak"], P["w_b_mid"], 1.0)
            m = self.ftb(j) / P["pri_ftb"]
            cont = (clamp(1 - (1 - P["c_air"]) * m, 0.0, 1), clamp(1 - (1 - P["c_weak"]) * m, 0.0, 1),
                    clamp(1 - (1 - P["c_mid"]) * m, 0.0, 1), 1.0)
            if agg >= 2 or raise_over:
                pass
            elif agg == 0 and calls:
                w = (max(0.02, cont[0]), max(0.05, cont[1]), max(0.1, cont[2]), 1.0)
            elif agg == 0:
                w = (1.0, 1.0, 1.0, 1.0)
            allin = stacks[j] == 0
            models.append((j, int(lo * NC), max(int(lo * NC) + 6, int(hi * NC)), w, cont, allin))
        return models

    def simulate(self, hole, board, models, sizes, budget):
        """Weighted MC. Returns eq, [(fold_prob, eq_when_called) per size]."""
        rng = self.rng
        my = [to_int(c) for c in hole]
        bd = [to_int(c) for c in board]
        dead = set(my) | set(bd)
        deck = [c for c in range(52) if c not in dead]
        need = 5 - len(bd)
        # current-board info for strength levels
        bprod = 1
        bsc = [0, 0, 0, 0]
        bsm = [0, 0, 0, 0]
        brc = [0] * 13
        for c in bd:
            bprod *= CP[c]
            bsc[c & 3] += 1
            bsm[c & 3] |= CB[c]
            brc[c >> 2] += 1
        top = max(c >> 2 for c in bd)
        bpairs = set(r for r in range(13) if brc[r] >= 2)
        draw_st = need > 0
        k = len(models)
        exps = [min(2.5, (s / 0.6) ** P["size_exp"]) for s in sizes]
        conts = []
        for (_, _, _, _, cont, allin) in models:
            row = []
            for e in exps:
                if allin:
                    row.append((1.0, 1.0, 1.0, 1.0))
                else:
                    row.append((cont[0] ** e, cont[1] ** e, cont[2] ** e, 1.0 if e < 2.0 else 0.92))
            conts.append(row)
        ns = len(sizes)
        W = 0.0
        E = 0.0
        FW = [0.0] * ns
        CW = [0.0] * ns
        CE = [0.0] * ns
        sims = 0
        t_end = time.perf_counter() + budget
        RTl = RT
        FLl = FL
        mp = CP[my[0]] * CP[my[1]]
        while True:
            for _ in range(4):
                used = set(dead)
                hands = []
                for (_, lo, hi, _, _, _) in models:
                    for _t in range(12):
                        h = ALLC[rng.randrange(lo, hi)]
                        if h[0] not in used and h[1] not in used:
                            break
                    else:
                        while True:
                            h = tuple(rng.sample(deck, 2))
                            if h[0] not in used and h[1] not in used:
                                break
                    used.add(h[0])
                    used.add(h[1])
                    hands.append(h)
                # strength levels on current board
                w = 1.0
                lv = []
                for idx in range(k):
                    h1, h2 = hands[idx]
                    v = RTl[bprod * CP[h1] * CP[h2]]
                    s1, s2 = h1 & 3, h2 & 3
                    for s in range(4):
                        cnt = bsc[s] + (s1 == s) + (s2 == s)
                        if cnt >= 5:
                            fv = FLl[bsm[s] | (CB[h1] if s1 == s else 0) | (CB[h2] if s2 == s else 0)]
                            if fv > v:
                                v = fv
                        elif cnt == 4 and draw_st and (s1 == s or s2 == s):
                            v = -1 if v < (1 << 20) else v  # flag flush draw w/ no pair
                    if v == -1:
                        L = 1
                    else:
                        cat = v >> 20
                        if cat >= 4:
                            L = 3
                        elif cat == 3:
                            L = 0 if brc[(v >> 8) & 15] >= 3 else 3
                        elif cat == 2:
                            p1, p2 = (v >> 8) & 15, (v >> 4) & 15
                            if p1 in bpairs and p2 in bpairs:
                                L = 0
                            elif p1 in bpairs or p2 in bpairs:
                                o = p2 if p1 in bpairs else p1
                                L = 2 if o >= top else 1
                            else:
                                L = 3
                        elif cat == 1:
                            p = (v >> 12) & 15
                            L = 0 if p in bpairs else (2 if p >= top else 1)
                        else:
                            L = 0
                    lv.append(L)
                    w *= models[idx][3][L]
                if w < 0.01:
                    w = 0.01
                # runout
                if need:
                    run = []
                    while len(run) < need:
                        c = deck[rng.randrange(len(deck))]
                        if c not in used:
                            used.add(c)
                            run.append(c)
                    full = bd + run
                else:
                    full = bd
                fp = 1
                fsc = [0, 0, 0, 0]
                fsm = [0, 0, 0, 0]
                for c in full:
                    fp *= CP[c]
                    fsc[c & 3] += 1
                    fsm[c & 3] |= CB[c]
                fs = -1
                for s in range(4):
                    if fsc[s] >= 3:
                        fs = s
                mv = RTl[fp * mp]
                if fs >= 0:
                    a, b = my
                    if fsc[fs] + ((a & 3) == fs) + ((b & 3) == fs) >= 5:
                        fv = FLl[fsm[fs] | (CB[a] if (a & 3) == fs else 0) | (CB[b] if (b & 3) == fs else 0)]
                        if fv > mv:
                            mv = fv
                best = 0
                ties = 0
                for (h1, h2) in hands:
                    v = RTl[fp * CP[h1] * CP[h2]]
                    if fs >= 0 and fsc[fs] + ((h1 & 3) == fs) + ((h2 & 3) == fs) >= 5:
                        fv = FLl[fsm[fs] | (CB[h1] if (h1 & 3) == fs else 0) | (CB[h2] if (h2 & 3) == fs else 0)]
                        if fv > v:
                            v = fv
                    if v > best:
                        best = v
                        ties = 0
                    elif v == best:
                        ties += 1
                if mv > best:
                    sh = 1.0
                elif mv == best:
                    sh = 1.0 / (ties + 2)
                else:
                    sh = 0.0
                W += w
                E += w * sh
                for si in range(ns):
                    pf = 1.0
                    for idx in range(k):
                        pf *= 1.0 - conts[idx][si][lv[idx]]
                    FW[si] += w * pf
                    wc = w * (1.0 - pf)
                    CW[si] += wc
                    CE[si] += wc * sh
                sims += 1
            if sims >= P["max_sims"] or (time.perf_counter() > t_end and sims >= 24):
                break
        self.last_sims = sims
        res = []
        for si in range(ns):
            res.append((FW[si] / W, CE[si] / CW[si] if CW[si] > 1e-9 else E / W))
        return E / W, res

    def postflop(self, state):
        me = state["seat"]
        pot = state["pot"]
        tc = state["to_call"]
        bets = state["bets"]
        my_bet = bets[me]
        cur = max(bets)
        stack = state["stacks"][me]
        n = len(bets)
        btn = state["button"]
        street = state["street"]
        lo_r, hi_r = state.get("min_raise_to"), state.get("max_raise_to")
        can_raise = "raise" in state["legal_actions"] and lo_r is not None
        models = self.opp_models(state, me)
        if not models:
            return {"action": "check"}
        # cap simulated opponents at 4
        models = models[:4]
        order = lambda s: (s - btn - 1) % n
        live = [m[0] for m in models]
        ip = all(order(me) > order(j) for j in live)
        cands = []
        if can_raise:
            if tc == 0:
                fr = P["bet_sizes"]
                base = pot
            else:
                fr = P["raise_sizes"]
                base = pot + tc
            seen = set()
            for f in fr:
                R = int(cur + tc * 0 + f * base) if tc == 0 else int(cur + f * base)
                R = max(lo_r, min(hi_r, R))
                if R not in seen:
                    seen.add(R)
                    cands.append(R)
            if hi_r not in seen and hi_r <= (my_bet + stack) and (hi_r - my_bet) <= P["shove_spr"] * pot:
                cands.append(hi_r)
        sizes = [max(0.05, (R - my_bet) / float(max(1, pot))) for R in cands]
        b = self.budget()
        if b <= 0:
            b = 0.0005
        e, res = self.simulate(state["hole_cards"], state["board"], models, sizes, b)
        if len(models) > 1:
            pass
        best_a = None
        if tc == 0:
            real = P["chk_ip"] if ip else P["chk_oop"]
            best_ev = e * pot * real
            best_a = {"action": "check"}
            for R, (f, ec) in zip(cands, res):
                add = R - my_bet
                ev = f * pot + (1 - f) * (ec * (pot + 2 * add) - add)
                if ev > best_ev + P["bet_margin"] * pot:
                    best_ev = ev
                    best_a = self.r(R)
            return best_a
        # facing a bet
        ev_call = e * (pot + tc) - tc
        if street != "river":
            ev_call -= P["call_tax"] * pot
        best_ev = 0.0
        best_a = {"action": "fold"}
        if ev_call > best_ev:
            best_ev = ev_call
            best_a = {"action": "call"}
        for R, (f, ec) in zip(cands, res):
            add = R - my_bet
            f2 = f * P["fold_vs_raise"]
            ev = f2 * pot + (1 - f2) * (ec * (pot + add + (R - cur)) - add)
            if ev > best_ev + P["raise_margin"] * pot:
                best_ev = ev
                best_a = self.r(R)
        return best_a
