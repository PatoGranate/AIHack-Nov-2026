import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Kojack: vpip 0.16 pfr 0.12 3b 0.06 af 0.23 ftb 0.36 (1000 hands)
    PARAMS = {'open': 0.146, 'threebet': 0.075, 'call': 0.108, 'call_cap': 0.15, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.58, 'bluff': 0.03, 'bet_min': 3, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.23}
