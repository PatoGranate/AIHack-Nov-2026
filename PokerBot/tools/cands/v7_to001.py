"""G (v7) with simulated server timeouts: a share of postflop decisions become check-else-fold."""
import importlib.util, os, random
_s = importlib.util.spec_from_file_location("v7base", os.path.join(os.path.dirname(os.path.abspath(__file__)), "v7.py"))
_m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
P_TO = 0.01


class Agent(_m.Agent):
    def act(self, state):
        if state.get("street") != "preflop" and random.random() < P_TO:
            self.misses = getattr(self, "misses", 0) + 1
            return {"action": "check"} if (state.get("to_call") or 0) == 0 else {"action": "fold"}
        return super().act(state)
