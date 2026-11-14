import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of 85p: vpip 0.12 pfr 0.09 3b 0.04 af 0.35 ftb 0.44 (1000 hands)
    PARAMS = {'open': 0.117, 'threebet': 0.054, 'call': 0.075, 'call_cap': 0.15, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.6, 'bluff': 0.14, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.35}
