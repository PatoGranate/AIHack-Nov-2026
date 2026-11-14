import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of ND: vpip 0.21 pfr 0.11 3b 0.06 af 0.30 ftb 0.41 (15000 hands)
    PARAMS = {'open': 0.151, 'threebet': 0.091, 'call': 0.144, 'call_cap': 0.309, 'open_size': 3.1, 'limp': 0.0, 'cbet': 0.549, 'bluff': 0.097, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.335}
