"""Phase 2 (reinforcement learning): export decision-level training data.

    python run_practice.py --tables 256 --hands 1000 --decisions --explore 0.05
    python rl/dataset.py --out data/rl_decisions.csv

Each row is one decision of our bot: the state features, the abstract action
taken, and the hand's final chip result (the Monte Carlo return). With
--explore > 0 a small share of actions is random, which gives the off-policy
learner counterfactual coverage (what would have happened had we raised here).

Features are computed with pokerbot.strategy (standard library only), so the
exact same `featurize` can run inside the uploaded bot at decision time.
"""
import argparse
import csv
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from pokerbot.strategy import card_int, evaluate, hole_pct, mc_equity  # noqa: E402
from storage import db as store  # noqa: E402

STREETS = {"preflop": 0, "flop": 1, "turn": 2, "river": 3}
POSITIONS = {"EP": 0, "MP": 1, "HJ": 2, "CO": 3, "BTN": 4, "SB": 5, "BB": 6}
ACTIONS = ["fold", "check", "call", "raise", "all_in"]


def featurize(hole, board, street, position, pot, to_call, stack, n_live, raises, rng=None, iters=60):
    """Numeric feature vector for one decision (hole/board as strings like 'AsKd')."""
    h = [card_int(hole[i:i + 2]) for i in range(0, len(hole), 2)]
    b = [card_int(board[i:i + 2]) for i in range(0, len(board), 2)]
    pct = hole_pct(h[0], h[1]) if len(h) == 2 else 0.5
    made = (evaluate(h + b) >> 20) if len(b) >= 3 else -1
    eq = mc_equity(h, b, [1.0] * max(1, min(3, n_live - 1)), rng or random.Random(0), iters, float("inf")) if len(h) == 2 else 0.5
    pot_odds = to_call / float(pot + to_call) if to_call else 0.0
    spr = stack / float(max(1, pot))
    return {
        "street": STREETS.get(street, 0), "position": POSITIONS.get(position, 0), "hole_pct": round(pct, 4),
        "made_hand": made, "equity_vs_random": round(eq, 4), "pot_bb": pot / 20.0, "to_call_bb": to_call / 20.0,
        "pot_odds": round(pot_odds, 4), "spr": round(min(spr, 50.0), 3), "n_live": n_live, "raises": raises,
    }


def abstract_action(action, amount, pot, to_call):
    if action in ("fold", "check", "call"):
        return action
    if action == "all_in":
        return "all_in"
    if action == "raise" and amount:
        frac = (amount - to_call) / float(max(1, pot))
        return "raise_small" if frac < 0.75 else "raise_big"
    return str(action)


def export(db, out, limit=None):
    q = ("SELECT d.*, h.delta FROM decisions d JOIN hands h ON h.table_id=d.table_id AND h.hand_no=d.hand_no "
         "AND h.seat=d.seat ORDER BY d.id")
    if limit:
        q += " LIMIT %d" % int(limit)
    rng = random.Random(1)
    n = 0
    with open(out, "w", newline="") as f:
        w = None
        for r in db.execute(q):
            feats = featurize(r["hole"], r["board"], r["street"], r["position"], r["pot"], r["to_call"],
                              r["stack"], r["n_live"], r["raises"], rng)
            row = dict(feats, action=abstract_action(r["action"], r["amount"], r["pot"], r["to_call"]),
                       reward_bb=r["delta"] / 20.0, strategy=r["strategy_id"])
            if w is None:
                w = csv.DictWriter(f, fieldnames=list(row))
                w.writeheader()
            w.writerow(row)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "rl_decisions.csv"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--db", default=None)
    a = ap.parse_args()
    db = store.connect(a.db)
    print("wrote %d decisions to %s" % (export(db, a.out, a.limit), a.out))


if __name__ == "__main__":
    main()
