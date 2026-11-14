"""pablo_poker: game-theory No-Limit Hold'em bot (single file, standard library only).

This file is BOTH the source of truth for the strategy and an uploadable bot:
`python export_bot.py` copies it to bot.py with the current champion's
parameters written into DEFAULT_PARAMS. The platform calls `Agent()` with no
arguments; the simulator and the RSI loop call `Agent(params=..., seed=...)`.

How it decides
--------------
Preflop    position-aware ranges from a 169-hand Monte Carlo ranking
           (open / 3-bet value + bluff / call / 4-bet / jam-call), widened or
           tightened by the raiser's observed PFR (Bayesian-smoothed).
Postflop   Monte Carlo equity against each live opponent's *estimated range*
           (their VPIP/PFR this round, narrowed every time they bet/raise),
           then:
             - call when equity beats pot odds (+ margin, + commitment cost)
             - value-bet / raise above equity thresholds
             - bluff only where it is +EV: when the opponents' smoothed
               fold-to-bet rate beats the break-even s/(1+s) for bet size s
               (classic GTO indifference), at a base mixing frequency.
Exploit    every opponent is tracked for the round (1,000 hands, same
           table): calling stations get thinner value bets and no bluffs,
           nits get stolen from, maniacs get looser calls.
Time       10 ms per decision, 10 s bank per round: the Monte Carlo budget
           adapts to the bank left, and every error falls back to check/fold.
"""
import gc
import random
import time

HARD_MS = 1.6          # never let one decision's own thinking exceed this (the limit is 10 ms incl. transport)

# ----------------------------------------------------------------- parameters
# Every tunable knob. The RSI loop changes ONE of these at a time and only
# keeps the change when it beats the champion on held-out games.
DEFAULT_PARAMS = {
    # preflop opening range (fraction of all 1,326 combos) by position
    "open_ep": 0.13, "open_mp": 0.18, "open_co": 0.27, "open_btn": 0.42, "open_sb": 0.36,
    "open_size": 2.5,          # open raise size in big blinds (+1 bb per limper)
    "iso_tighten": 0.80,       # open range multiplier per limper
    "threebet_value": 0.035,   # 3-bet for value with the top x of combos
    "threebet_bluff": 0.03,    # width of the 3-bet bluff band just below the call range
    "threebet_size": 3.2,      # 3-bet to x times the open (+0.6x out of position)
    "call_open": 0.11,         # flat-call band width vs a single raise
    "bb_defend": 0.22,         # extra defending width in the big blind
    "fourbet_value": 0.02,     # 4-bet / jam range facing a 3-bet
    "call_3bet": 0.05,         # call a 3-bet with the top x
    "jam_call": 0.03,          # call a large all-in with the top x
    # postflop (equities are heads-up-equivalent: E ** (1 / opponents))
    "value_flop": 0.64, "value_turn": 0.68, "value_river": 0.72,
    "raise_eq": 0.82,          # raise a bet with at least this equity
    "call_margin": 0.02,       # extra equity required over pot odds to call
    "draw_discount": 0.04,     # implied-odds discount before the river
    "commit_penalty": 0.10,    # extra equity needed per stack fraction committed
    "bet_value": 0.66,         # value bet size, fraction of pot
    "bet_bluff": 0.55,         # bluff / c-bet size, fraction of pot
    "cbet_freq": 0.55,         # flop c-bet frequency as preflop aggressor (heads-up)
    "bluff_freq": 0.30,        # mixing frequency for +EV bluffs
    "semibluff_eq": 0.38,      # min heads-up equity to semi-bluff flop / turn
    "agg_tighten": 0.55,       # opponent range multiplier per postflop bet/raise
    "exploit": 0.70,           # 0 = pure baseline, 1 = full opponent exploitation
    # compute
    "mc_iters": 260,           # Monte Carlo cap per decision
    "mc_ms": 1.0,              # Monte Carlo wall-clock cap per decision (tournament servers are ~2x slower than a laptop)
    # ideas from the literature (research/LITERATURE.md); 0 = off until the lab's gate approves them
    "jam_equity": 0,           # vs a shove: call iff MC equity vs the shover's observed shove range beats the price
    "exploit_ramp": 0,         # safe exploitation: exploitation grows over the first N hands (0 = off)
    "portfolio": 0,            # implicit modelling: Exp3 picks base/loose/tight/aggro per hand at this table
    "river_overbet": 0.0,      # Pluribus-style polarised 1.5x pot river bets with near-nut hands
    # data collection for the RL phase (keep 0 for the tournament)
    "explore": 0.0,            # probability of a random abstract action (fold/call/half-pot/pot)
}

# Search space for the RSI loop: (low, high, step). Kept next to the defaults
# so the uploaded bot and the lab can never disagree on what a knob means.
PARAM_SPACE = {
    "open_ep": (0.06, 0.25, 0.02), "open_mp": (0.08, 0.32, 0.02), "open_co": (0.12, 0.45, 0.03),
    "open_btn": (0.20, 0.70, 0.04), "open_sb": (0.15, 0.60, 0.04), "open_size": (2.0, 4.0, 0.25),
    "iso_tighten": (0.5, 1.0, 0.05), "threebet_value": (0.015, 0.08, 0.008),
    "threebet_bluff": (0.0, 0.08, 0.01), "threebet_size": (2.6, 4.2, 0.2), "call_open": (0.03, 0.30, 0.02),
    "bb_defend": (0.05, 0.50, 0.04), "fourbet_value": (0.008, 0.05, 0.005), "call_3bet": (0.02, 0.12, 0.01),
    "jam_call": (0.01, 0.08, 0.005), "value_flop": (0.52, 0.80, 0.02), "value_turn": (0.55, 0.82, 0.02),
    "value_river": (0.58, 0.86, 0.02), "raise_eq": (0.70, 0.93, 0.02), "call_margin": (-0.06, 0.12, 0.015),
    "draw_discount": (0.0, 0.10, 0.015), "commit_penalty": (0.0, 0.25, 0.03), "bet_value": (0.33, 1.20, 0.08),
    "bet_bluff": (0.30, 1.00, 0.08), "cbet_freq": (0.0, 1.0, 0.08), "bluff_freq": (0.0, 0.80, 0.06),
    "semibluff_eq": (0.25, 0.55, 0.03), "agg_tighten": (0.30, 0.90, 0.05), "exploit": (0.0, 1.0, 0.1),
    "jam_equity": (0, 1, 1), "exploit_ramp": (0, 400, 50), "portfolio": (0, 1, 1), "river_overbet": (0.0, 1.0, 0.25),
}

# Portfolio arms (Bard et al. 2013): multipliers (or offsets for value_*) applied to the base parameters.
PORTFOLIO = [
    {},
    {"open_*": 1.3, "call_open": 1.4, "bb_defend": 1.3, "value_*": -0.03, "call_margin": 1.0},    # loose
    {"open_*": 0.75, "call_open": 0.7, "bb_defend": 0.7, "value_*": 0.03, "call_margin": 1.0},    # tight
    {"bluff_freq": 1.6, "cbet_freq": 1.3, "bet_value": 1.2, "threebet_bluff": 1.5},               # aggressive
]

# 169 starting-hand classes, best first (tools/build_preflop.py: Monte Carlo
# equity vs 1 and vs 3 random hands, blended).
PREFLOP_ORDER = "AA KK QQ JJ TT 99 AKs AQs 88 AJs AKo ATs KQs AQo KJs AJo 77 KTs QJs KQo ATo A9s A8s QTs KJo 66 A7s K9s JTs KTo A5s QJo A6s A9o K8s A4s Q9s QTo A8o J9s 55 K7s A7o A3s T9s A2s Q8s K9o JTo K6s A6o A5o Q9o J8s K5s K8o T8s A4o K4s J9o 44 Q7s Q6s K3s K7o A3o 98s Q5s Q8o J7s A2o T9o K2s T7s K6o 97s Q4s J8o 33 87s K5o Q3s Q2s J6s T8o J5s Q7o K4o T6s 98o 96s Q6o J4s J7o K3o K2o 86s J3s 76s T7o Q5o 22 T5s J2s 97o T4s Q4o 95s 75s 85s J6o 65s T3s 87o Q3o J5o T6o Q2o 96o T2s 94s 54s 84s 86o 76o 64s 93s 74s J4o J3o J2o 92s 53s T5o T4o 63s 83s 75o 85o 95o 65o 73s 82s 43s T3o 52s 62s 94o 54o T2o 74o 72s 84o 42s 64o 93o 32s 53o 92o 63o 43o 73o 83o 82o 52o 62o 72o 42o 32o"

RANKS = "23456789TJQKA"
SUITS = "cdhs"


# ------------------------------------------------------------- hand evaluator
# 7-card evaluator returning one int (bigger is better), table driven over
# 13-bit rank masks so a Monte Carlo trial costs a few microseconds.
def _build_tables():
    n = 1 << 13
    straight = [-1] * n
    topn = [0] * n
    pop = [0] * n
    high = [-1] * n
    for m in range(n):
        ranks = [r for r in range(12, -1, -1) if m >> r & 1]
        pop[m] = len(ranks)
        high[m] = ranks[0] if ranks else -1
        packed = 0
        for k in range(5):
            packed = (packed << 4) | (ranks[k] if k < len(ranks) else 0)
        topn[m] = packed
        w = (m << 1) | (1 if m & (1 << 12) else 0)
        for top in range(13, 3, -1):
            if (w >> (top - 4)) & 0b11111 == 0b11111:
                straight[m] = top - 1
                break
    return straight, topn, pop, high


_STRAIGHT, _TOPN, _POP, _HIGH = _build_tables()


def evaluate(cards):
    rc = [0] * 13
    sm = [0, 0, 0, 0]
    m = 0
    for c in cards:
        r = c >> 2
        rc[r] += 1
        sm[c & 3] |= 1 << r
        m |= 1 << r
    for fm in sm:
        if _POP[fm] >= 5:
            sh = _STRAIGHT[fm]
            if sh >= 0:
                return (8 << 20) | sh
            flush = (5 << 20) | _TOPN[fm]
            break
    else:
        flush = 0
    quad = -1
    trips = []
    pairs = []
    for r in range(12, -1, -1):
        k = rc[r]
        if k >= 2:
            if k == 4:
                quad = r
            elif k == 3:
                trips.append(r)
            else:
                pairs.append(r)
    if quad >= 0:
        return (7 << 20) | (quad << 4) | _HIGH[m & ~(1 << quad)]
    if trips and (len(trips) > 1 or pairs):
        second = max(trips[1] if len(trips) > 1 else -1, pairs[0] if pairs else -1)
        return (6 << 20) | (trips[0] << 4) | second
    if flush:
        return flush
    sh = _STRAIGHT[m]
    if sh >= 0:
        return (4 << 20) | sh
    if trips:
        t = trips[0]
        return (3 << 20) | (t << 8) | (_TOPN[m & ~(1 << t)] >> 12)
    if len(pairs) >= 2:
        p0, p1 = pairs[0], pairs[1]
        return (2 << 20) | (p0 << 8) | (p1 << 4) | _HIGH[m & ~(1 << p0) & ~(1 << p1)]
    if pairs:
        p = pairs[0]
        return (1 << 20) | (p << 12) | (_TOPN[m & ~(1 << p)] >> 8)
    return _TOPN[m]


def card_int(s):
    return RANKS.index(s[0]) * 4 + SUITS.index(s[1])


# ------------------------------------------------------------ preflop ranking
def _hand_class(c1, c2):
    r1, r2 = c1 >> 2, c2 >> 2
    if r1 < r2:
        r1, r2 = r2, r1
    if r1 == r2:
        return RANKS[r1] * 2
    return RANKS[r1] + RANKS[r2] + ("s" if (c1 & 3) == (c2 & 3) else "o")


def _build_preflop():
    order = PREFLOP_ORDER.split()
    weight = {c: (6 if len(c) == 2 else 4 if c[2] == "s" else 12) for c in order}
    pct, cum = {}, 0
    for c in order:
        cum += weight[c]
        pct[c] = cum / 1326.0
    combos = []
    for a in range(52):
        for b in range(a + 1, 52):
            combos.append((pct[_hand_class(a, b)], a, b))
    combos.sort()
    cum_pct = [x[0] for x in combos]
    return pct, [(a, b) for _, a, b in combos], cum_pct


CLASS_PCT, COMBOS, COMBO_PCT = _build_preflop()


def hole_pct(c1, c2):
    """Fraction of all combos at least as good as this hand (0 = best)."""
    return CLASS_PCT[_hand_class(c1, c2)]


def _prefix_len(pct):
    """Number of combos in the top `pct` of hands (binary search)."""
    lo, hi = 0, len(COMBO_PCT)
    while lo < hi:
        mid = (lo + hi) >> 1
        if COMBO_PCT[mid] <= pct:
            lo = mid + 1
        else:
            hi = mid
    return max(lo, 6)


# --------------------------------------------------------------- Monte Carlo
def mc_equity(hole, board, ranges, rng, max_iters, deadline):
    """Share of the pot won against opponents drawn from top-x% ranges."""
    dead = set(hole) | set(board)
    deck = [c for c in range(52) if c not in dead]
    nd = len(deck)
    need = 5 - len(board)
    prefixes = [_prefix_len(p) for p in ranges]
    rand = rng.random
    perf = time.perf_counter
    total = 0.0
    n = 0
    while n < max_iters:
        if n >= 8 and (n & 3) == 0 and perf() > deadline:
            break
        used = set(dead)
        opps = []
        for plen in prefixes:
            for _ in range(12):
                a, b = COMBOS[int(rand() * plen)]
                if a not in used and b not in used:
                    break
            else:
                while True:
                    a = deck[int(rand() * nd)]
                    b = deck[int(rand() * nd)]
                    if a != b and a not in used and b not in used:
                        break
            used.add(a)
            used.add(b)
            opps.append((a, b))
        extra = []
        while len(extra) < need:
            c = deck[int(rand() * nd)]
            if c not in used:
                used.add(c)
                extra.append(c)
        full = board + extra
        me = evaluate(hole + full)
        win, ties = True, 0
        for a, b in opps:
            o = evaluate([a, b] + full)
            if o > me:
                win = False
                break
            if o == me:
                ties += 1
        if win:
            total += 1.0 / (1 + ties)
        n += 1
    return total / n if n else 0.5


def mc_call_ev(hole, fixed, maybe, pot_after_call, rng, max_iters, deadline):
    """Expected chips back from calling a preflop shove (all in, so no more decisions).

    fixed: ranges of players already in.  maybe: (probability, range, extra_chips) for each
    player still to act, who overcalls with that probability holding a top-`range` hand and
    adds `extra_chips` to the pot. Returns mean (pot share x final pot)."""
    deck = [c for c in range(52) if c not in hole]
    nd = len(deck)
    rand = rng.random
    perf = time.perf_counter
    total = 0.0
    n = 0
    while n < max_iters:
        if n >= 8 and (n & 3) == 0 and perf() > deadline:
            break
        ranges = list(fixed)
        pot = pot_after_call
        for prob, rng_pct, extra in maybe:
            if rand() < prob:
                ranges.append(rng_pct)
                pot += extra
        used = set(hole)
        opps = []
        for pct in ranges:
            plen = _prefix_len(pct)
            for _ in range(12):
                a, b = COMBOS[int(rand() * plen)]
                if a not in used and b not in used:
                    break
            else:
                while True:
                    a, b = deck[int(rand() * nd)], deck[int(rand() * nd)]
                    if a != b and a not in used and b not in used:
                        break
            used.add(a)
            used.add(b)
            opps.append((a, b))
        board = []
        while len(board) < 5:
            c = deck[int(rand() * nd)]
            if c not in used:
                used.add(c)
                board.append(c)
        me = evaluate(hole + board)
        win, ties = True, 0
        for a, b in opps:
            o = evaluate([a, b] + board)
            if o > me:
                win = False
                break
            if o == me:
                ties += 1
        if win:
            total += pot / (1 + ties)
        n += 1
    return total / n if n else 0.0


# ----------------------------------------------------------- opponent model
class OppStats:
    __slots__ = ("hands", "vpip", "pfr", "aggr", "passive", "faced", "folded", "acts", "jams")

    def __init__(self):
        self.hands = self.vpip = self.pfr = self.aggr = self.passive = self.faced = self.folded = self.acts = 0
        self.jams = 0

    def jam_rate(self):
        """Share of hands this player shoves preflop (prior 4% over 20 hands)."""
        return (self.jams + 0.04 * 20) / (self.hands + 20)

    # Bayesian smoothing toward typical 8-max values with a 15-hand prior
    def vpip_rate(self):
        return (self.vpip + 0.28 * 15) / (self.hands + 15)

    def pfr_rate(self):
        return (self.pfr + 0.16 * 15) / (self.hands + 15)

    def fold_to_bet(self):
        return (self.folded + 0.45 * 10) / (self.faced + 10)

    def aggression(self):
        return (self.aggr + 1.0 * 5) / (self.passive + 5)

    def agg_freq(self):
        """Share of voluntary actions that are bets/raises (TAG ~0.2, maniac 0.4+)."""
        return (self.aggr + 0.2 * 10) / (self.acts + 10)

    def looseness(self):
        """0 for a solid player, up to 1 for one who bets/raises with anything."""
        return max(0.0, min(1.0, (self.agg_freq() - 0.22) / 0.18))


# ---------------------------------------------------------------------- agent
class Agent:
    def __init__(self, params=None, seed=None, fixed_iters=None):
        p = dict(DEFAULT_PARAMS)
        if params:
            p.update(params)
        self.p = p
        self.rng = random.Random(seed)
        self.fixed_iters = fixed_iters        # simulator: fixed MC work, no clock (repeatable)
        self.opp = {}
        self.seat = 0
        self.n_players = 8
        self.hands_total = 1000
        self.spent = 0.0                      # seconds of thinking used this round
        self.bank = 10.0
        self.start_stack = 2000
        self.cur = p
        self.cur_hand = None
        self.arm = 0
        self.arm_w = [1.0] * len(PORTFOLIO)
        self.arm_p = [1.0 / len(PORTFOLIO)] * len(PORTFOLIO)

    # ------------------------------------------------------------ callbacks
    def on_table_start(self, info):
        self.seat = info.get("seat", 0)
        self.n_players = info.get("num_players", 8)
        self.hands_total = info.get("hands", 1000) or 1000
        self.start_stack = info.get("starting_stack", 2000) or 2000
        try:                                   # move start-up objects out of the collector: no GC pauses mid-decision
            gc.collect()
            gc.freeze()
        except Exception:
            pass

    def act(self, state):
        t0 = time.perf_counter()
        self.t0 = t0
        try:
            if self.p["explore"] and self.rng.random() < self.p["explore"]:
                return self._explore(state)
            return self._act(state, t0)
        except Exception:
            return {"action": "check"} if "check" in state.get("legal_actions", ()) else {"action": "fold"}
        finally:
            self.spent += time.perf_counter() - t0

    def on_hand_end(self, summary):
        try:
            self._learn(summary)
            if self.p["portfolio"] and self.cur_hand == summary.get("hand_number"):
                self._portfolio_update(summary["stacks"][self.seat] - self.start_stack)
        except Exception:
            pass

    # ----------------------------------------------- per-hand parameter set
    def _hand_params(self, hand_no):
        """Parameters for this hand: portfolio arm (Exp3) and the safe-exploitation ramp."""
        if self.cur_hand == hand_no:
            return self.cur
        self.cur_hand = hand_no
        p = self.p
        if p["portfolio"]:
            k, g = len(PORTFOLIO), 0.1
            tot = sum(self.arm_w)
            self.arm_p = [(1 - g) * w / tot + g / k for w in self.arm_w]
            x, acc = self.rng.random(), 0.0
            self.arm = k - 1
            for i, pr in enumerate(self.arm_p):
                acc += pr
                if x <= acc:
                    self.arm = i
                    break
            p = dict(p)
            for key, v in PORTFOLIO[self.arm].items():
                targets = [n for n in p if n.startswith(key[:-1])] if key.endswith("*") else [key]
                for n in targets:
                    p[n] = p[n] + v if key.startswith("value_") else p[n] * v
        if p["exploit_ramp"]:
            p = dict(p)
            p["exploit"] = p["exploit"] * min(1.0, hand_no / float(p["exploit_ramp"]))
        self.cur = p
        return p

    def _portfolio_update(self, delta):
        k, g = len(PORTFOLIO), 0.1
        x = max(0.0, min(1.0, (delta / 20.0 + 50.0) / 100.0))
        self.arm_w[self.arm] *= 2.718281828 ** (g * x / (self.arm_p[self.arm] * k))
        top = max(self.arm_w)
        self.arm_w = [w / top for w in self.arm_w]

    def _explore(self, state):
        legal = state["legal_actions"]
        opts = [self._passive(legal)]
        if "call" in legal:
            opts.append({"action": "call"})
        if "raise" in legal:
            cur, pot = max(state["bets"]), state["pot"]
            opts.append(self._raise(state, cur + 0.5 * pot + state["to_call"]))
            opts.append(self._raise(state, cur + pot + state["to_call"]))
        return self.rng.choice(opts)

    # -------------------------------------------------------------- helpers
    def _stats(self, seat):
        s = self.opp.get(seat)
        if s is None:
            s = self.opp[seat] = OppStats()
        return s

    def _learn(self, summary):
        hist = summary.get("history") or []
        seen, vp, pr, jm = set(), set(), set(), set()
        street_bet = {}
        for h in hist:
            seat, act, st = h["seat"], h["action"], h["street"]
            seen.add(seat)
            if act in ("small_blind", "big_blind"):
                continue
            if st == "preflop":
                if act in ("call", "raise"):
                    vp.add(seat)
                if act == "raise":
                    pr.add(seat)
                    if h.get("amount", 0) >= 0.45 * self.start_stack and seat != self.seat:
                        jm.add(seat)
            if seat != self.seat:
                self._stats(seat).acts += 1
            if act == "raise":
                if seat != self.seat:
                    self._stats(seat).aggr += 1
            elif act == "call" and seat != self.seat:
                self._stats(seat).passive += 1
            if st != "preflop" and seat != self.seat:
                if street_bet.get(st) is not None and street_bet[st] != seat:
                    s = self._stats(seat)
                    if act in ("fold", "call", "raise"):
                        s.faced += 1
                        if act == "fold":
                            s.folded += 1
            if act == "raise" and st != "preflop":
                street_bet[st] = seat
        for seat in seen:
            if seat == self.seat:
                continue
            s = self._stats(seat)
            s.hands += 1
            if seat in vp:
                s.vpip += 1
            if seat in pr:
                s.pfr += 1
            if seat in jm:
                s.jams += 1

    def _budget(self, hand_no):
        if self.fixed_iters:
            return self.fixed_iters, float("inf")
        left = self.bank - 1.5 - self.spent
        hands_left = max(1, self.hands_total - hand_no + 1)
        per_hand = left / hands_left
        ms = min(self.p["mc_ms"], max(0.3, per_hand * 1000 * 0.6))
        if left < 0.5:
            ms = 0.3
        return int(self.p["mc_iters"]), min(time.perf_counter() + ms / 1000.0, getattr(self, "t0", 0) + HARD_MS / 1000.0)

    # -------------------------------------------------------------- decide
    def _act(self, state, t0):
        legal = state["legal_actions"]
        me = state["seat"]
        self.seat = me
        hole = [card_int(c) for c in state["hole_cards"]]
        board = [card_int(c) for c in state["board"]]
        hist = state.get("history") or []
        self._hand_params(state["hand_number"])
        if state["street"] == "preflop":
            return self._preflop(state, legal, hole, hist)
        return self._postflop(state, legal, hole, board, hist)

    @staticmethod
    def _raise(state, amount):
        lo, hi = state["min_raise_to"], state["max_raise_to"]
        amount = int(max(lo, min(hi, amount)))
        stack_total = state["stacks"][state["seat"]] + state["bets"][state["seat"]]
        if amount >= 0.6 * stack_total:
            amount = hi
        return {"action": "raise", "amount": amount}

    @staticmethod
    def _passive(legal):
        return {"action": "check"} if "check" in legal else {"action": "fold"}

    def _positions(self, state, hist):
        n = len(state["stacks"])
        bb_seat = next((h["seat"] for h in hist if h["action"] == "big_blind"), (state["button"] + 2) % n)
        sb_seat = next((h["seat"] for h in hist if h["action"] == "small_blind"), (state["button"] + 1) % n)
        order = [(bb_seat + 1 + k) % n for k in range(n)]
        order = [s for s in order if not state["folded"][s] or any(h["seat"] == s for h in hist)]
        return order, sb_seat, bb_seat

    # -------------------------------------------------------------- preflop
    def _preflop(self, state, legal, hole, hist):
        p = self.cur
        me, bb = state["seat"], state["big_blind"]
        pct = hole_pct(hole[0], hole[1])
        can_raise = "raise" in legal
        to_call = state["to_call"]
        acts = [h for h in hist if h["street"] == "preflop" and h["action"] not in ("small_blind", "big_blind")]
        raises = [h for h in acts if h["action"] == "raise"]
        limpers = sum(1 for h in acts if h["action"] == "call") if not raises else 0
        order, sb_seat, bb_seat = self._positions(state, hist)
        behind = len(order) - 1 - order.index(me) if me in order else 0
        stack_total = state["stacks"][me] + state["bets"][me]
        current = max(state["bets"])
        r = self.rng.random()

        if not raises:
            if me == sb_seat:
                width = p["open_sb"]
            elif behind >= 5:
                width = p["open_ep"]
            elif behind >= 3:
                width = p["open_mp"]
            elif behind == 2:
                width = p["open_co"]
            elif behind == 1 and me != bb_seat:
                width = p["open_btn"]
            else:
                width = p["open_btn"]
            width *= p["iso_tighten"] ** limpers
            # steal more when the players left to act fold a lot (exploit)
            folders = [self._stats(s).fold_to_bet() for s in order[order.index(me) + 1:]] if me in order else []
            if folders:
                avg_fold = sum(folders) / len(folders)
                width *= 1 + p["exploit"] * max(-0.3, min(0.4, (avg_fold - 0.45) * 1.5))
            if pct <= width and can_raise:
                return self._raise(state, (p["open_size"] + limpers) * bb)
            if "check" in legal:
                return {"action": "check"}
            if me == sb_seat and not limpers and pct <= width * 1.5:
                return {"action": "call"}            # complete the small blind
            if limpers and pct <= width * 1.6 and to_call <= bb:
                return {"action": "call"}            # over-limp, great price
            return {"action": "fold"}

        raiser = raises[-1]["seat"]
        rs = self._stats(raiser)
        price_bb = to_call / float(bb)
        all_in_faced = to_call >= 0.45 * stack_total

        if len(raises) == 1 and not all_in_faced:
            scale = max(0.6, min(3.0, rs.pfr_rate() / 0.16))
            scale = 1 + (scale - 1) * p["exploit"]
            tv = p["threebet_value"] * scale
            width = p["call_open"] * scale + (p["bb_defend"] if me == bb_seat else 0.0)
            width *= max(0.5, min(1.5, 3.0 / max(price_bb, 0.5)))
            in_pos = behind <= 2 and me not in (sb_seat, bb_seat)
            if pct <= tv and can_raise:
                size = p["threebet_size"] + (0.0 if in_pos else 0.6)
                return self._raise(state, current * size)
            if pct <= tv + width:
                return {"action": "call"}
            suited = (hole[0] & 3) == (hole[1] & 3)
            if can_raise and suited and pct <= tv + width + p["threebet_bluff"] * scale and r < 0.65:
                size = p["threebet_size"] + (0.0 if in_pos else 0.6)
                return self._raise(state, current * size)
            return self._passive(legal)

        if len(raises) == 2 and not all_in_faced:
            opened = any(h["seat"] == me for h in raises)
            fv = p["fourbet_value"] * (1.0 if opened else 0.7)
            cv = p["call_3bet"] * (1.0 if opened else 0.5)
            if pct <= fv and can_raise:
                return self._raise(state, current * 2.3)
            if pct <= cv and to_call <= 0.35 * stack_total:
                return {"action": "call"}
            return self._passive(legal)

        if all_in_faced and p["jam_equity"]:
            return self._call_shove(state, legal, hole, stack_total)

        # 4-bet+ or facing a big all-in: only the very top continues
        jam_scale = 1 + p["exploit"] * (3.0 * rs.looseness() - 0.2)
        if pct <= p["jam_call"] * jam_scale:
            if can_raise and pct <= p["jam_call"] * 0.5:
                return {"action": "all_in"}
            return {"action": "call"}
        return self._passive(legal)

    def _call_shove(self, state, legal, hole, stack_total):
        """Push/fold game theory: call a shove iff equity vs the shovers' ranges beats the price."""
        p = self.cur
        me = state["seat"]
        fixed, maybe = [], []
        current = max(state["bets"])
        for s in range(len(state["stacks"])):
            if s == me or state["folded"][s]:
                continue
            st = self._stats(s)
            put_in = state["bets"][s]
            # a big raise is a "shove range" for maniacs and a value range for everyone else
            all_in = state["stacks"][s] == 0
            if put_in >= current or all_in:
                # committed to the shove: a shove range for maniacs, a value range for everyone else
                fixed.append(max(0.02, min(1.0, max(st.jam_rate() * 1.1, st.pfr_rate() * (0.35 + 0.65 * st.looseness())))))
            else:
                # has not answered the shove yet (limpers, the original raiser, blinds, players behind):
                # its chips are already in the pot; it calls with its shove/strong range, adding the rest
                c = max(0.02, min(1.0, max(st.jam_rate(), st.pfr_rate() * (0.2 + 0.4 * st.looseness()))))
                extra = min(current, state["stacks"][s] + put_in) - put_in
                maybe.append((c, c, extra))
        if not fixed:
            return self._passive(legal)
        iters, deadline = self._budget(state["hand_number"])
        to_call, pot = state["to_call"], state["pot"]
        back = mc_call_ev(hole, sorted(fixed)[:3], maybe[:3], pot + to_call, self.rng, iters, deadline)
        if back - to_call > max(0.0, p["call_margin"]) * (pot + to_call):
            return {"action": "call"}
        return self._passive(legal)

    # ------------------------------------------------------------- postflop
    def _ranges(self, state, hist):
        p = self.cur
        me = state["seat"]
        ranges = {}
        for s in range(len(state["stacks"])):
            if s == me or state["folded"][s]:
                continue
            st = self._stats(s)
            pf = [h for h in hist if h["seat"] == s and h["street"] == "preflop"]
            n_raise = sum(1 for h in pf if h["action"] == "raise")
            if n_raise >= 2:
                rng = st.pfr_rate() * 0.3
            elif n_raise == 1:
                rng = st.pfr_rate()
            elif any(h["action"] == "call" for h in pf):
                rng = min(0.65, st.vpip_rate())
            else:
                rng = 1.0                           # checked the big blind
            loosen = p["exploit"] * st.looseness()
            factor = p["agg_tighten"] + (1 - p["agg_tighten"]) * loosen
            for h in hist:
                if h["seat"] == s and h["street"] != "preflop" and h["action"] == "raise":
                    rng *= factor
            ranges[s] = max(0.03, min(1.0, rng))
        return ranges

    def _postflop(self, state, legal, hole, board, hist):
        p = self.cur
        me, street = state["seat"], state["street"]
        ranges = self._ranges(state, hist)
        if not ranges:
            return self._passive(legal)
        opps = sorted(ranges, key=lambda s: ranges[s])[:4]
        n_opp = len(ranges)
        iters, deadline = self._budget(state["hand_number"])
        eq = mc_equity(hole, board, [ranges[s] for s in opps], self.rng, iters, deadline)
        eq_hu = eq ** (1.0 / n_opp) if eq > 0 else 0.0

        pot, to_call = state["pot"], state["to_call"]
        stack_total = state["stacks"][me] + state["bets"][me]
        current = max(state["bets"])
        can_raise = "raise" in legal
        r = self.rng.random()
        value_thr = {"flop": p["value_flop"], "turn": p["value_turn"], "river": p["value_river"]}[street]

        # opponents' tendencies (exploit layer)
        fold_est = 1.0
        call_rate = 0.0
        for s in ranges:
            st = self._stats(s)
            f = st.fold_to_bet()
            fold_est *= f
            call_rate += 1 - f
        call_rate /= n_opp
        station = max(0.0, call_rate - 0.55)        # > 0 vs players who rarely fold
        value_thr -= p["exploit"] * station * 0.25

        pf_aggr = [h for h in hist if h["street"] == "preflop" and h["action"] == "raise"]
        i_was_aggressor = bool(pf_aggr) and pf_aggr[-1]["seat"] == me
        acted_this_street = any(h["seat"] == me and h["street"] == street for h in hist)

        if to_call == 0:
            if can_raise and street == "river" and eq_hu > 0.92 and r < p["river_overbet"]:
                return self._raise(state, current + 1.5 * pot)
            if can_raise and eq_hu >= value_thr:
                frac = p["bet_value"] * (1.25 if eq_hu > 0.88 else 1.0)
                return self._raise(state, current + frac * pot)
            if can_raise and n_opp <= 2 and not acted_this_street:
                s_b = p["bet_bluff"]
                breakeven = s_b / (1 + s_b)
                plus_ev = fold_est > breakeven
                mix = p["bluff_freq"] * ((1 + p["exploit"]) if plus_ev else (1 - p["exploit"]) * 0.5)
                if street == "flop" and i_was_aggressor and n_opp == 1:
                    cb = p["cbet_freq"] * (1.2 if plus_ev else 0.8)
                    if r < cb and eq_hu >= 0.30:
                        return self._raise(state, current + s_b * pot)
                if street != "river" and eq_hu >= p["semibluff_eq"] and r < mix:
                    return self._raise(state, current + s_b * pot)
                if street == "river" and eq_hu < 0.30 and r < mix * 0.8:
                    return self._raise(state, current + s_b * pot)
            return self._passive(legal)

        pot_odds = to_call / float(pot + to_call)
        commit = to_call / float(max(1, stack_total))
        need = pot_odds + p["call_margin"] + p["commit_penalty"] * commit
        if street != "river":
            need -= p["draw_discount"]
        if can_raise and eq_hu >= p["raise_eq"]:
            return self._raise(state, current + p["bet_value"] * (pot + to_call))
        if eq >= need:
            return {"action": "call"}
        return self._passive(legal)
