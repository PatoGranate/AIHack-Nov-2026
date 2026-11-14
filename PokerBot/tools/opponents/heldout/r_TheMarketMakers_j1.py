import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of The Market Makers: vpip 0.19 pfr 0.12 3b 0.07 af 0.49 ftb 0.43 (19000 hands)
    PARAMS = {'open': 0.146, 'threebet': 0.075, 'call': 0.13, 'call_cap': 0.218, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.938, 'bluff': 0.329, 'bet_min': 1, 'call_min': 2, 'raise_min': 4, 'bet_frac': 1.0, 'semibluff': 0.63}
