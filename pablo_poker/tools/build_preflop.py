"""Build the 169-hand preflop ranking embedded in pokerbot/strategy.py.

    python tools/build_preflop.py --samples 4000

Each starting hand class (AA, AKs, AKo, ...) is scored by Monte Carlo equity
against 1 and against 3 random hands, blended 50/50 (8-max pots are often
multiway, which favours suited/connected hands over the heads-up ranking).
The result is printed as the PREFLOP_ORDER string and patched into
strategy.py when --write is given.
"""
import argparse
import os
import random
import re
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine.cards import evaluate  # noqa: E402

R = "23456789TJQKA"


def classes():
    out = []
    for i in range(12, -1, -1):
        for j in range(i, -1, -1):
            if i == j:
                out.append(R[i] + R[j])
            else:
                out.append(R[i] + R[j] + "s")
                out.append(R[i] + R[j] + "o")
    return out


def example(cls):
    a, b = R.index(cls[0]), R.index(cls[1])
    if len(cls) == 2:
        return [a * 4, b * 4 + 1]
    if cls[2] == "s":
        return [a * 4, b * 4]
    return [a * 4, b * 4 + 1]


def equity(args):
    cls, n_opp, samples, seed = args
    rng = random.Random(seed)
    hole = example(cls)
    deck = [c for c in range(52) if c not in hole]
    score = 0.0
    for _ in range(samples):
        cards = rng.sample(deck, 5 + 2 * n_opp)
        board = cards[:5]
        me = evaluate(hole + board)
        best, ties = 0, 0
        win = True
        for k in range(n_opp):
            o = evaluate(cards[5 + 2 * k: 7 + 2 * k] + board)
            if o > me:
                win = False
                break
            if o == me:
                ties += 1
        if win:
            score += 1.0 / (1 + ties)
    return cls, n_opp, score / samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=4000)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    jobs = [(c, n, a.samples, hash((c, n)) & 0xFFFF) for c in classes() for n in (1, 3)]
    with Pool() as p:
        res = p.map(equity, jobs, chunksize=4)
    eq = {}
    for cls, n, e in res:
        eq.setdefault(cls, {})[n] = e
    # normalise the 3-way equity onto the heads-up scale before blending
    blended = {c: 0.5 * v[1] + 0.5 * (v[3] * 2.0) for c, v in eq.items()}
    order = sorted(blended, key=lambda c: -blended[c])
    line = 'PREFLOP_ORDER = "%s"' % " ".join(order)
    print(line)
    if a.write:
        path = os.path.join(ROOT, "pokerbot", "strategy.py")
        src = open(path, encoding="utf-8").read()
        src = re.sub(r'^PREFLOP_ORDER = ".*"$', line, src, flags=re.M)
        open(path, "w", encoding="utf-8").write(src)
        print("patched", path)


if __name__ == "__main__":
    main()
