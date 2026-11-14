import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of kaiserbot: vpip 0.22 pfr 0.11 3b 0.04 af 0.33 ftb 0.44 (29000 hands)
    PARAMS = {'open': 0.174, 'threebet': 0.053, 'call': 0.185, 'call_cap': 0.264, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.628, 'bluff': 0.13, 'bet_min': 1, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.396}
