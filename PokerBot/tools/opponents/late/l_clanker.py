import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of clanker: vpip 0.21 pfr 0.06 3b 0.03 af 0.30 ftb 0.28 (1000 hands)
    PARAMS = {'open': 0.075, 'threebet': 0.038, 'call': 0.129, 'call_cap': 0.3, 'open_size': 3.0, 'limp': 0.0, 'cbet': 0.53, 'bluff': 0.09, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.3}
