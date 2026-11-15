"""FORGE t4ctx clone field: Sunday table-4 clones whose post-flop fold-to-bet follows the real data.

Why: the existing clones (tools/opponents/_common.py ParamBot, incl. sunday_v2) fold on hand strength
only, so they miss the real multiway / raise / size / street / position effects (clone_vs_real_t4real.txt).
A fold-model change can't show its value against them. Here each sunday_v2 clone keeps its own preflop,
betting and raising logic, but when it faces a post-flop bet its fold PROBABILITY is the per-player
logistic fitted on real Saturday events (t4ctx_coef.json: field features, shrunk to the field fit), and
it folds its WEAKEST hands first. Hand strength is mapped to an approximately uniform u by a randomised
probability-integral transform of score = 2*made_cat + draw, using per-clone CDFs by street x bet/raise
(pooled over clones where a cell has < 300 decisions) measured on this field (t4ctx_cdf.json, from calibrate_ctx.py). Fold iff u < p. If not folding and the base clone would
fold, the clone calls; otherwise the base clone's call/raise stands.

Variant "v2" is the plain sunday_v2 clone with the same deterministic per-decision RNG and score
recording (the paired control and the calibration source).

RNG: each decision reseeds from (hole, board, history length, seat), so cand and base runs share clone
randomness wherever the visible state is identical (better pairing than the unseeded ParamBot RNG).
The hero term (opponents fold less to WBot) is NOT in the generator: the clones can't tell who the hero is.
"""
import importlib.util
import json
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OPP = os.path.join(HERE, "..", "opponents")
_COEF = json.load(open(os.path.join(HERE, "t4ctx_coef.json"), encoding="utf-8"))
_CDF_PATH = os.path.join(HERE, "t4ctx_cdf.json")
_CDF = json.load(open(_CDF_PATH, encoding="utf-8")) if os.path.exists(_CDF_PATH) else None
_mods = {}


def _base_module(stem):
    if stem not in _mods:
        p = os.path.join(OPP, "sunday_v2", "r_%s.py" % stem)
        spec = importlib.util.spec_from_file_location("forge_sv2_" + stem, p)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _mods[stem] = m
    return _mods[stem]


def context(state):
    """(street, kind, size_ratio, mw, ip, allin) of the bet the acting seat faces. Same definitions
    as extract_events.py: size = aggressor's added chips / pot before that action; ip relative to the
    last aggressor in post-flop order (seat - button - 1) % n."""
    me, n, btn, street = state["seat"], len(state["stacks"]), state["button"], state["street"]
    contrib = [0] * n
    bets = [0] * n
    st, naggr, aggr, ratio = "preflop", 0, None, 0.0
    for h in state["history"]:
        if h["street"] != st:
            st, bets, naggr, aggr = h["street"], [0] * n, 0, None
        s, a, amt = h["seat"], h["action"], h["amount"]
        if a in ("small_blind", "big_blind", "call"):
            contrib[s] += amt
            bets[s] += amt
        elif a == "raise":
            add = amt - bets[s]
            ratio = add / float(max(1, sum(contrib)))
            contrib[s] += add
            bets[s] = amt
            naggr += 1
            aggr = s
    live_others = sum(1 for j in range(n) if not state["folded"][j] and j != me)
    order = lambda x: (x - btn - 1) % n
    ip = 1 if aggr is not None and order(me) > order(aggr) else 0
    allin = 1 if state["to_call"] >= state["stacks"][me] else 0
    return street, ("bet" if naggr == 1 else "raise"), ratio, (1 if live_others >= 2 else 0), ip, allin


def fold_prob(stem, ctx):
    street, kind, size, mw, ip, allin = ctx
    cols, edges = _COEF["columns"], _COEF["size_edges"]
    sb = sum(1 for e in edges if size >= e)
    v = {"const": 1.0, "raise": float(kind == "raise"), "mw": mw, "turn": float(street == "turn"),
         "river": float(street == "river"), "ip": ip, "allin": allin, "mw_ip": mw * ip}
    for k in range(1, len(edges) + 1):
        v["sz%d" % k] = float(sb == k)
    x = sum(b * v[c] for b, c in zip(_COEF["players"][stem]["coef"], cols))
    return 1 / (1 + math.exp(-x))


def make(stem, variant):
    base = _base_module(stem).Agent
    from _common import made  # importable once a sunday_v2 module has put tools/opponents on sys.path

    class Agent(base):
        def __init__(self):
            base.__init__(self)
            self.rec = []      # (street|kind, score, folded) for facing-bet decisions (calibration / fidelity)
            self.nfold = [0, 0.0, 0]  # ctx variant: folds, sum of target p, decisions

        def act(self, state):
            self.rng = random.Random("%s|%s|%d|%d" % ("".join(state["hole_cards"]), "".join(state["board"]),
                                                     len(state["history"]), state["seat"]))
            if state["street"] == "preflop" or state["to_call"] <= 0:
                return base.act(self, state)
            cat, draw = made(state["hole_cards"], state["board"])
            score = 2 * cat + (1 if draw else 0)
            ctx = context(state)
            key = "%s|%s" % (state["street"], ctx[1])  # CDF cell: street x bet/raise
            if variant == "v2":
                out = base.act(self, state)
                self.rec.append((key, score, out.get("action") == "fold"))
                return out
            p = fold_prob(stem, ctx)
            cdf = _CDF["cdf"][stem][key]
            lo = cdf[score - 1] if score > 0 else 0.0
            u = lo + self.rng.random() * (cdf[score] - lo)
            self.nfold[1] += p
            self.nfold[2] += 1
            if u < p:
                self.nfold[0] += 1
                self.rec.append((key, score, True))
                return {"action": "fold"}
            out = base.act(self, state)
            if out.get("action") == "fold":
                out = {"action": "call"}
            self.rec.append((key, score, False))
            return out

    Agent.__name__ = "%s_%s" % (variant, stem)
    return Agent
