import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of gamblerlove: vpip 0.18 pfr 0.14 3b 0.07 af 0.37 ftb 0.30 (2000 hands)
    PARAMS = {'open': 0.174, 'threebet': 0.089, 'call': 0.125, 'call_cap': 0.15, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.61, 'bluff': 0.16, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.37}
