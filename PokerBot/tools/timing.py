"""Per-decision timing distribution for a bot in-process."""
import sys, os, time, importlib.util
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))
from engine import FixedHandsTable
from engine.players import LocalPlayer
sp = importlib.util.spec_from_file_location("b", sys.argv[1]); bot = importlib.util.module_from_spec(sp); sp.loader.exec_module(bot)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "opponents"))
ts = []
class T(LocalPlayer):
    def act(self, state):
        t = time.perf_counter(); o = super().act(state); ts.append(((time.perf_counter() - t) * 1000, state["street"])); return o
def ld(p):
    s = importlib.util.spec_from_file_location(os.path.basename(p)[:-3], p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m.Agent
opp = [ld("tools/opponents/" + x) for x in ["a_fish.py", "a_lag.py", "a_tag.py", "a_maniac.py", "a_station2.py", "v2_uploaded.py", "a_nit.py"]]
pl = [T(bot.Agent)] + [LocalPlayer(o) for o in opp]
t0 = time.perf_counter()
FixedHandsTable(pl, hands=1000, seed=int(sys.argv[2]) if len(sys.argv) > 2 else 1).play()
ag = pl[0].agent
v = sorted(x[0] for x in ts)
print("decisions", len(v), "total s", round(sum(v) / 1000, 2), "agent.spent", round(ag.spent, 2), "p50 %.2f p99 %.2f max %.2f" % (v[len(v) // 2], v[int(len(v) * .99)], v[-1]))
print("top", [(round(a, 1), s) for a, s in sorted(ts, reverse=True)[:8]])
