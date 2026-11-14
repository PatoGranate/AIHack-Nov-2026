import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of ediz_slow: vpip 0.76 pfr 0.33 3b 0.25 af 0.48 ftb 0.48 (12000 hands)
    PARAMS = {'open': 0.371, 'threebet': 0.26, 'call': 0.398, 'call_cap': 0.235, 'open_size': 2.8, 'limp': 0.746, 'cbet': 0.867, 'bluff': 0.287, 'bet_min': 0, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.609}
