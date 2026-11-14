import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of AAST: vpip 0.20 pfr 0.13 3b 0.06 af 0.42 ftb 0.55 (10000 hands)
    PARAMS = {'open': 0.167, 'threebet': 0.08, 'call': 0.149, 'call_cap': 0.3, 'open_size': 3.3, 'limp': 0.0, 'cbet': 0.61, 'bluff': 0.2, 'bet_min': 2, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.42}
