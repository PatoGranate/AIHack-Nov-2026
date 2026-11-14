"""Server emulation of config S3 (server max_ms=3.5 hard_ms=6.5), 5.0x slower server."""
import importlib.util, os, time
_s = importlib.util.spec_from_file_location("core_S3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "emu_S3_core.py"))
_m = importlib.util.module_from_spec(_s); _s.loader.exec_module(_m)
SLOW = 5.0
LIMIT = 0.0095


class Agent(_m.Agent):
    def __init__(self):
        super().__init__()
        self.bank = 8.5 / SLOW
        self.late = 0

    def act(self, state):
        t0 = time.perf_counter()
        out = super().act(state)
        if (time.perf_counter() - t0) * SLOW + 0.0003 > LIMIT:
            self.late += 1
            return {"action": "check"} if (state.get("to_call") or 0) == 0 else {"action": "fold"}
        return out
