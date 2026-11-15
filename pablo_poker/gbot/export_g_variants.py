"""Build one-factor G candidates from Matthias/SCOUT findings. Never touches G_frozen.py.

    python gbot/export_g_variants.py

G_heroftb.py  G + per-seat fold rate to OUR bets (SCOUT: opponents fold ~12 pts less to WBot's bets than to
              others' at the same size/street/position; G's pooled counter over-predicts folds to its bets).
              Reads use hero-bettor counts, shrunk (k = 20) toward that seat's pooled rate minus 0.12.
G_adaptA.py   G_heroftb + honest check value (chk 1.0 IP / 0.9 OOP) + no bet bonus, so fold rates decide bets.
G_adaptB.py   G_adaptA + c_mid 0.85 (top pair no longer always calls).
G_steal3b.py  G with its existing per-seat steal and light 3-bet paths switched on (q_steal = q_3bet = 1).
              Both are gated per seat by role-conditioned fold rates G already tracks (blinds vs a single
              open, opener vs a 3-bet), e.g. YSL / Chinese fold 81-91% as openers facing a 3-bet; Anton 32%.
"""
import ast
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
G_SHA = "1ee577f0e4fed6aef7fef55d1c6f2684e5f3a2a8ce777983bb9ace9ba55ffe12"

HEROFTB = '''

# ===================================================================== hero-bettor fold rate (SCOUT rec. 1)
HF_OFFSET = 0.12   # field: folds to WBot's bets ran 12.3 pts [10.7, 13.9] below folds to other bettors
HF_K = 20.0        # shrinkage weight (SCOUT section 3b: ~19 pseudo-decisions)
_HFBase = Agent


class Agent(_HFBase):
    def __init__(self):
        _HFBase.__init__(self)
        self.hf = {}   # seat -> [faced our bet, folded]

    def _learn(self, summary):
        _HFBase._learn(self, summary)
        try:
            street, cur, agg = None, 0, None
            for h in summary.get("history") or []:
                a, s, st = h.get("action"), h.get("seat"), h.get("street")
                if st != street:
                    street, cur, agg = st, 0, None
                if st == "preflop" or a in ("small_blind", "big_blind"):
                    continue
                if cur > 0 and agg == self.seat and s != self.seat and a in ("fold", "call", "raise"):
                    c = self.hf.setdefault(s, [0, 0])
                    c[0] += 1
                    c[1] += a == "fold"
                if a == "raise":
                    cur = h.get("amount") or cur
                    agg = s
        except Exception:
            pass

    def ftb(self, s):
        base = _HFBase.ftb(self, s)
        prior = max(0.02, base - HF_OFFSET)
        c = self.hf.get(s, (0, 0))
        return (c[1] + prior * HF_K) / (c[0] + HF_K)
'''

ADAPTC = '''

# ===================================================================== per-opponent bluff gate + value sizing
# What the winners do (real Saturday hands): vs a station (YSL) they bet 41% at 1.08 pot with 19% air shown;
# vs a folder (Poke) they bet more. G's value betting is kept as is; only heads-up, only when checked to:
#   opponent folds < AC_FLO to our bets: no bluffs (equity < AC_EBLUFF -> check); value (equity >= AC_EVAL)
#                                        uses the largest size up to AC_VSIZE x pot
#   opponent folds > AC_FHI:             a weak hand G would check is bet at about 0.6 pot instead
AC_FLO, AC_FHI = 0.30, 0.55
AC_EBLUFF, AC_EVAL = 0.40, 0.60
AC_VSIZE = 1.15
AC_MIN_N = 8          # our-bet observations of that seat before the gate acts
_ACBase = Agent


class Agent(_ACBase):
    def simulate(self, hole, board, models, cands, my_bet, pot, raising, budget):
        e, evs = _ACBase.simulate(self, hole, board, models, cands, my_bet, pot, raising, budget)
        self._ac = (e, list(cands))
        return e, evs

    def postflop(self, state):
        self._ac = None
        act = _ACBase.postflop(self, state)
        try:
            if state["to_call"] != 0 or self._ac is None:
                return act
            me = state["seat"]
            live = [j for j in range(len(state["folded"])) if j != me and not state["folded"][j]]
            if len(live) != 1:
                return act
            j = live[0]
            if self.hf.get(j, (0, 0))[0] < AC_MIN_N:
                return act
            f = self.ftb(j)
            e, cands = self._ac
            pot = state["pot"]
            my_bet = state["bets"][me]
            if f < AC_FLO:
                if act.get("action") == "raise" and e < AC_EBLUFF:
                    return {"action": "check"}
                if e >= AC_EVAL and cands:
                    big = [R for R in cands if R - my_bet <= AC_VSIZE * pot]
                    if big:
                        return self.r(max(big))
            elif f > AC_FHI and act.get("action") == "check" and e < AC_EBLUFF and cands:
                tgt = my_bet + 0.6 * pot
                return self.r(min(cands, key=lambda R: abs(R - tgt)))
        except Exception:
            pass
        return act
'''

STEAL3B = '''

# ===================================================================== per-seat steal + light 3-bet (SCOUT rec. 6)
P.update({"q_steal": 1, "q_3bet": 1})
'''


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    g = os.path.join(HERE, "G_frozen.py")
    assert sha(g) == G_SHA, "G_frozen.py is not frozen G"
    base = open(g, encoding="utf-8").read()
    out = {}
    ADAPT_A = HEROFTB + ("\n\n# honest check value, no bet bonus: lets the opponent's fold rate decide bet vs check\n"
                         "P.update({'chk_ip': 1.0, 'chk_oop': 0.9, 'bet_margin': 0.0})\n")
    ADAPT_B = ADAPT_A + "P.update({'c_mid': 0.85})   # top pair no longer always calls: fold rate scales more hands\n"
    ADAPT_C = HEROFTB + ADAPTC
    # combinations: profile layer (Table D priors, whole-round evidence, change detection) goes first so the
    # hero-bettor fold rate is built on top of its per-seat reads
    prof = open(os.path.join(HERE, "g_profile_adapter.py"), encoding="utf-8").read()
    prof = prof.replace("GP_ROSTER_PRIOR = False", "GP_ROSTER_PRIOR = True").replace("GP_WINDOW = 400", "GP_WINDOW = 1000")
    COMBO1 = HEROFTB + ADAPTC + STEAL3B
    COMBO2 = "\n" + prof + HEROFTB + ADAPTC + STEAL3B
    for name, add in (("G_heroftb.py", HEROFTB), ("G_steal3b.py", STEAL3B), ("G_adaptA.py", ADAPT_A), ("G_adaptB.py", ADAPT_B),
                      ("G_adaptC.py", ADAPT_C), ("G_combo1.py", COMBO1), ("G_combo2.py", COMBO2)):
        src = base + add
        ast.parse(src)
        p = os.path.join(HERE, name)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(src)
        out[name] = sha(p)
    m = os.path.join(HERE, "manifest.json")
    man = json.load(open(m)) if os.path.exists(m) else {}
    man.update(out)
    json.dump(man, open(m, "w"), indent=1)
    print(json.dumps(out, indent=1))
