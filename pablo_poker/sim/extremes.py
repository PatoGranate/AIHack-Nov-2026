"""Extreme / degenerate strategies for stress tests and field probes.

Equilibrium-style bots often lose to strategies their designers never
pictured (the classic example: shoving every hand). The lab plays the
champion against tables full of these and also uses them as *probe heroes*
to measure what the opponent field gives away.
"""
import random

RANKS = "23456789TJQKA"


def _pct_rank(hole):
    a, b = sorted((RANKS.index(c[0]) for c in hole), reverse=True)
    score = a * 2 + b + (6 if a == b else 0) + (2 if hole[0][1] == hole[1][1] else 0)
    return score / 44.0          # ~1.0 for AA, ~0.1 for 72o


class Jammer:
    """All in, every decision."""
    def act(self, s):
        return {"action": "all_in"} if "raise" in s["legal_actions"] else {"action": "call" if "call" in s["legal_actions"] else "check"}


class Folder:
    """Checks when free, otherwise folds (gives up the blinds every hand)."""
    def act(self, s):
        return {"action": "check" if "check" in s["legal_actions"] else "fold"}


class MinRaiser:
    """Min-raises every time it can, calls otherwise."""
    def act(self, s):
        if "raise" in s["legal_actions"]:
            return {"action": "raise", "amount": s["min_raise_to"]}
        return {"action": "call" if "call" in s["legal_actions"] else "check"}


class Overbettor:
    """5x opens, 2x-pot bets when checked to, calls any bet."""
    def act(self, s):
        legal = s["legal_actions"]
        if "raise" in legal and s["to_call"] <= s["big_blind"]:
            amt = 5 * s["big_blind"] if s["street"] == "preflop" else max(s["bets"]) + 2 * s["pot"]
            return {"action": "raise", "amount": amt}
        return {"action": "call" if "call" in legal else "check"}


class CheckRaiser:
    """Never bets first; raises any bet to 3x."""
    def act(self, s):
        legal = s["legal_actions"]
        if s["to_call"] > 0 and "raise" in legal and s["street"] != "preflop":
            return {"action": "raise", "amount": 3 * max(s["bets"])}
        if s["street"] == "preflop" and s["to_call"] <= s["big_blind"]:
            return {"action": "call" if "call" in legal else "check"}
        return {"action": "check" if "check" in legal else "call"}


class RandomSizer:
    """Random actions with random sizes up to all in."""
    def __init__(self):
        self.rng = random.Random()

    def act(self, s):
        a = self.rng.choice(s["legal_actions"])
        if a == "raise":
            return {"action": "raise", "amount": self.rng.randint(s["min_raise_to"], s["max_raise_to"])}
        return {"action": a}


class PushFold:
    """Shove the top ~30% of hands preflop, fold the rest; check/fold after."""
    def act(self, s):
        legal = s["legal_actions"]
        if s["street"] == "preflop":
            if _pct_rank(s["hole_cards"]) >= 0.55 and "raise" in legal:
                return {"action": "all_in"}
            if _pct_rank(s["hole_cards"]) >= 0.55 and "call" in legal:
                return {"action": "call"}
        return {"action": "check" if "check" in legal else "fold"}


EXTREMES = {"jammer": Jammer, "folder": Folder, "minraiser": MinRaiser, "overbettor": Overbettor,
            "checkraiser": CheckRaiser, "randomsizer": RandomSizer, "pushfold": PushFold}

# which strategy knobs are most likely to fix a losing matchup (the lab queues these)
COUNTER_PARAMS = {
    "jammer": [("jam_equity", 1), ("jam_call", 1)],
    "pushfold": [("jam_equity", 1), ("jam_call", 1)],
    "folder": [("open_btn", 1), ("open_co", 1), ("open_sb", 1)],
    "minraiser": [("call_open", 1), ("threebet_value", 1), ("raise_eq", -1)],
    "overbettor": [("call_margin", -1), ("agg_tighten", 1), ("value_river", -1)],
    "checkraiser": [("cbet_freq", -1), ("bet_bluff", -1), ("value_flop", 1)],
    "randomsizer": [("agg_tighten", 1), ("call_margin", -1)],
}
