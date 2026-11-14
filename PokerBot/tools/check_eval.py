import sys, random, time, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))
from engine.cards import evaluate as ref
import bot
rng = random.Random(1)
N = 200000
hands = [rng.sample(range(52), 7) for _ in range(N)]
bad = 0
for i in range(0, N - 1, 2):
    a, b = hands[i], hands[i+1]
    r = (ref(a) > ref(b)) - (ref(a) < ref(b))
    m = (bot.evaluate(a) > bot.evaluate(b)) - (bot.evaluate(a) < bot.evaluate(b))
    if r != m:
        bad += 1
        if bad < 5: print("MISMATCH", a, b, ref(a), ref(b))
t = time.perf_counter()
for h in hands[:50000]: bot.evaluate(h)
print("mismatches", bad, "us/eval", (time.perf_counter() - t) / 50000 * 1e6)
