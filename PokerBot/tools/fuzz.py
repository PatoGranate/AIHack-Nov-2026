"""Play many in-process hands with bot.py in every seat type, checking legality + time."""
import sys, os, random, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit"))
from engine import FixedHandsTable
from engine.players import LocalPlayer
import importlib.util as _u; _s=_u.spec_from_file_location("bot", sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","kit","bot.py")); bot=_u.module_from_spec(_s); _s.loader.exec_module(bot); bot.DEBUG=True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kit", "examples"))
import random_bot, calling_station, tight_aggressive

class Checked(LocalPlayer):
    worst = 0.0
    def act(self, state):
        t = time.perf_counter()
        out = super().act(state)
        Checked.worst = max(Checked.worst, (time.perf_counter() - t) * 1000)
        a = out["action"]
        assert a in ("fold", "check", "call", "raise", "all_in"), out
        if a == "check": assert state["to_call"] == 0, (out, state)
        if a == "raise": assert "raise" in state["legal_actions"] and state["min_raise_to"] <= out["amount"] <= state["max_raise_to"], (out, state)
        return out

for betting, cap in [("no_limit", 0), ("pot_limit", 0), ("fixed_limit", 0), ("no_limit", 2)]:
    for seed in range(2):
        pl = [Checked(bot.Agent) for _ in range(3)] + [LocalPlayer(random_bot.Agent), LocalPlayer(calling_station.Agent), LocalPlayer(tight_aggressive.Agent), LocalPlayer(random_bot.Agent)]
        res = FixedHandsTable(pl, hands=150, config={"betting": betting, "raise_cap": cap}, seed=seed).play()
        errs = sum(p.stats.errors for p in pl[:3])
        print(betting, cap, "errors", errs, "chips", res["chips"][:3], pl[0].stats.error_samples[:1])
print("worst ms", round(Checked.worst, 2))
