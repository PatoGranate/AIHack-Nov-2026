import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of 85p: vpip 0.13 pfr 0.10 3b 0.04 af 0.39 ftb 0.34 (4000 hands)
    PARAMS = {'open': 0.116, 'threebet': 0.055, 'call': 0.087, 'call_cap': 0.168, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.588, 'bluff': 0.184, 'bet_min': 3, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.321}
