"""Latency profile of a bot's act(): python tools/latency.py BOT.py [hands] [tables]
Reports total act() ms by street, and overhead beyond the decide() loop."""
import sys, os, time, random, importlib.util, statistics as st
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "kit")); sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tools", "opponents"))
from engine import FixedHandsTable
from engine.players import LocalPlayer
import arena
bot = sys.argv[1]; hands = int(sys.argv[2]) if len(sys.argv) > 2 else 300; tables = int(sys.argv[3]) if len(sys.argv) > 3 else 6
A = arena.load(bot)
REC = []   # (street, total_ms, decide_ms)
class Timed(LocalPlayer):
    def act(self, state):
        t = time.perf_counter(); out = super().act(state); tot = (time.perf_counter() - t) * 1000
        REC.append((len(state.get("board") or []), tot, getattr(self.agent if hasattr(self, "agent") else None, "_dms", 0.0)))
        return out
fl = arena.field_list("real", bot, [])
for s in range(tables):
    rng = random.Random(s * 31 + 5)
    opps = [rng.choice(fl) for _ in range(6)]
    seats = list(opps); seats.insert(s % 7, None)
    pl = [Timed(A) if x is None else LocalPlayer(arena.load(x)) for x in seats]
    FixedHandsTable(pl, hands=hands, config={"betting": "no_limit", "raise_cap": 0}, seed=s).play()
def q(v, p): v = sorted(v); return v[min(len(v) - 1, int(len(v) * p))]
names = {0: "preflop", 3: "flop", 4: "turn", 5: "river"}
print("%-8s %6s %7s %7s %7s %7s %7s  >25ms %%" % ("street", "n", "p50", "p95", "p99", "p99.9", "max"))
for k in (0, 3, 4, 5, None):
    v = [r[1] for r in REC if k is None or r[0] == k]
    if v: print("%-8s %6d %7.2f %7.2f %7.2f %7.2f %7.2f  %.3f" % (names.get(k, "ALL"), len(v), st.median(v), q(v, .95), q(v, .99), q(v, .999), max(v), 100 * sum(x > 25 for x in v) / len(v)))
