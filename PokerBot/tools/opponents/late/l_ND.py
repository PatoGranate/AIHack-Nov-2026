import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of ND: vpip 0.17 pfr 0.08 3b 0.04 af 0.31 ftb 0.37 (1000 hands)
    PARAMS = {'open': 0.101, 'threebet': 0.055, 'call': 0.149, 'call_cap': 0.3, 'open_size': 3.1, 'limp': 0.0, 'cbet': 0.6, 'bluff': 0.1, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.31}
