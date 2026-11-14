import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of matcha mille crêpes cake: vpip 0.16 pfr 0.10 3b 0.05 af 0.44 ftb 0.41 (1000 hands)
    PARAMS = {'open': 0.124, 'threebet': 0.07, 'call': 0.129, 'call_cap': 0.15, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.53, 'bluff': 0.21, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.44}
