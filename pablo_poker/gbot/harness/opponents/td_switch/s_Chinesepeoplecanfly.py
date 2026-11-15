import os, sys, importlib.util
H = os.path.dirname(os.path.abspath(__file__))
def _l(n):
    s = importlib.util.spec_from_file_location("sw_"+n, os.path.join(H, "..", "sunday_v2", n + ".py"))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m.Agent
_A, _B = _l("r_Chinesepeoplecanfly"), _l("r_ResonanceQt")
SWITCH = 500
class Agent:
    """Plays clone r_Chinesepeoplecanfly for SWITCH hands, then switches to clone r_ResonanceQt (a new upload mid-round)."""
    def __init__(self):
        self.a, self.b, self.n, self.info = _A(), _B(), 0, None
    def on_table_start(self, info):
        self.info = info
        for x in (self.a, self.b):
            if hasattr(x, "on_table_start"): x.on_table_start(info)
    def _cur(self):
        return self.a if self.n < SWITCH else self.b
    def act(self, state):
        return self._cur().act(state)
    def on_hand_end(self, summary):
        self.n += 1
        for x in (self.a, self.b):
            if hasattr(x, "on_hand_end"): x.on_hand_end(summary)
