import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Vlad: vpip 0.22 pfr 0.14 3b 0.04 af 0.35 ftb 0.47 (11000 hands)
    PARAMS = {'open': 0.145, 'threebet': 0.061, 'call': 0.115, 'call_cap': 0.334, 'open_size': 3.7, 'limp': 0.0, 'cbet': 0.763, 'bluff': 0.131, 'bet_min': 1, 'call_min': 1, 'raise_min': 4, 'bet_frac': 1.0, 'semibluff': 0.395}
