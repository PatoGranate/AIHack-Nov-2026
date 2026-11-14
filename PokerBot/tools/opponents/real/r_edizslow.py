import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of ediz_slow: vpip 0.76 pfr 0.33 3b 0.25 af 0.48 ftb 0.48 (12000 hands)
    PARAMS = {'open': 0.407, 'threebet': 0.289, 'call': 0.501, 'call_cap': 0.3, 'open_size': 2.8, 'limp': 0.836, 'cbet': 1.0, 'bluff': 0.25, 'bet_min': 1, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.48}
