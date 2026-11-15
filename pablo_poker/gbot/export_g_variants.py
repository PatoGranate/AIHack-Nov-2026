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
    for name, add in (("G_heroftb.py", HEROFTB), ("G_steal3b.py", STEAL3B), ("G_adaptA.py", ADAPT_A), ("G_adaptB.py", ADAPT_B)):
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
