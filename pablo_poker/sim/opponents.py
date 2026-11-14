"""Opponent pool ("league") for practice and RSI.

Every opponent is deterministic given its seed, so two runs of a table with
the same seed deal the same cards to the same opponents playing the same way
(duplicate poker: the only difference between a champion run and a candidate
run is the hero).

Kinds
  house:*     the kit's three house bots (seeded)
  starter     the kit's starter bot.py (many teams will upload variants of it)
  arch:*      archetypes built from our own strategy with extreme parameters
              (nit, maniac, loose-passive station, loose-aggressive)
  extreme:*   degenerate strategies (sim/extremes.py): always all-in, always
              fold, min-raise, overbet, check-raise, random sizing, push/fold
  strategy    any parameter set from the strategies table: past champions
              join the league, so the bot keeps playing its former selves
              (the recursive part of RSI)
"""
import importlib.util
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARCHETYPES = {
    "nit": {"open_ep": 0.07, "open_mp": 0.09, "open_co": 0.13, "open_btn": 0.2, "open_sb": 0.15,
            "call_open": 0.05, "bb_defend": 0.08, "bluff_freq": 0.0, "cbet_freq": 0.3,
            "value_flop": 0.72, "value_turn": 0.75, "value_river": 0.78, "call_margin": 0.08},
    "maniac": {"open_ep": 0.35, "open_mp": 0.4, "open_co": 0.5, "open_btn": 0.65, "open_sb": 0.55,
               "threebet_value": 0.08, "threebet_bluff": 0.08, "call_open": 0.3, "bluff_freq": 0.8,
               "cbet_freq": 1.0, "semibluff_eq": 0.25, "bet_bluff": 1.0, "bet_value": 1.0,
               "value_flop": 0.55, "value_turn": 0.58, "value_river": 0.6, "call_margin": -0.05,
               "exploit": 0.0},
    "station": {"open_ep": 0.25, "open_mp": 0.3, "open_co": 0.35, "open_btn": 0.45, "open_sb": 0.4,
                "call_open": 0.35, "bb_defend": 0.45, "bluff_freq": 0.0, "cbet_freq": 0.2,
                "call_margin": -0.08, "draw_discount": 0.1, "commit_penalty": 0.0,
                "value_flop": 0.78, "value_turn": 0.8, "value_river": 0.82, "exploit": 0.0},
    "lag": {"open_ep": 0.18, "open_mp": 0.24, "open_co": 0.34, "open_btn": 0.55, "open_sb": 0.45,
            "threebet_value": 0.05, "threebet_bluff": 0.06, "bluff_freq": 0.5, "cbet_freq": 0.8},
}


def _load_agent_class(path):
    spec = importlib.util.spec_from_file_location("bot_%d" % abs(hash(path)), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Agent


_CACHE = {}


def _cls(rel):
    path = os.path.join(ROOT, rel)
    if path not in _CACHE:
        _CACHE[path] = _load_agent_class(path)
    return _CACHE[path]


def strategy_class():
    from pokerbot.strategy import Agent
    return Agent


def make(spec, seed, fixed_iters=80):
    """Build an agent from a seat spec: {"kind": ..., "name": ..., "params": ...}."""
    kind = spec["kind"]
    if kind == "house":
        rel = {"tag": "examples/tight_aggressive.py", "station": "examples/calling_station.py",
               "random": "examples/random_bot.py"}[spec["name"]]
        agent = _cls(rel)()
        if hasattr(agent, "rng"):
            agent.rng = random.Random(seed)
        return agent
    if kind == "starter":
        agent = _cls("examples/starter_bot.py")()
        if hasattr(agent, "rng"):
            agent.rng = random.Random(seed)
        return agent
    if kind == "statbot":
        from sim.statbot import StatBot
        return StatBot(spec["profile"], seed=seed)
    if kind == "extreme":
        from sim.extremes import EXTREMES
        agent = EXTREMES[spec["name"]]()
        if hasattr(agent, "rng"):
            agent.rng = random.Random(seed)
        return agent
    if kind == "arch":
        return strategy_class()(params=ARCHETYPES[spec["name"]], seed=seed, fixed_iters=fixed_iters)
    if kind == "strategy":
        return strategy_class()(params=spec["params"], seed=seed, fixed_iters=fixed_iters)
    raise ValueError("unknown seat kind %r" % kind)


def label(spec):
    if spec["kind"] in ("house", "arch", "extreme"):
        return "%s:%s" % (spec["kind"], spec["name"])
    if spec["kind"] == "starter":
        return "starter"
    sid = spec.get("strategy_id", "?")
    return sid if sid.startswith(("clone:", "stat:")) else "pablo:%s" % sid


# ---------------------------------------------------------------- lineups
DEFAULT_MIX = [  # (weight, spec)
    (3, {"kind": "house", "name": "tag"}),
    (2, {"kind": "house", "name": "station"}),
    (2, {"kind": "house", "name": "random"}),
    (5, {"kind": "starter"}),
    (1, {"kind": "arch", "name": "nit"}),
    (1, {"kind": "arch", "name": "maniac"}),
    (1, {"kind": "arch", "name": "station"}),
    (2, {"kind": "arch", "name": "lag"}),
    # degenerate strategies: rare at the table, but the bot must not bleed to them
    (1, {"kind": "extreme", "name": "jammer"}),
    (1, {"kind": "extreme", "name": "minraiser"}),
    (1, {"kind": "extreme", "name": "overbettor"}),
    (1, {"kind": "extreme", "name": "pushfold"}),
]


def lineup(seed, n_opponents, league=(), league_weight=4, mix=None):
    """Deterministic list of opponent specs for a table seed.

    league: strategy specs (past champions) added to the mix with total weight
    `league_weight`, so self-play grows as the bot improves.
    """
    rng = random.Random(seed * 7919 + 13)
    pool = list(mix or DEFAULT_MIX)
    if league:
        w = max(1, league_weight // max(1, len(league))) if len(league) <= league_weight else 1
        pool += [(w, s) for s in league[-league_weight:]]
    total = sum(w for w, _ in pool)
    out = []
    for _ in range(n_opponents):
        x = rng.random() * total
        for w, s in pool:
            x -= w
            if x <= 0:
                out.append(s)
                break
        else:
            out.append(pool[-1][1])
    return out
