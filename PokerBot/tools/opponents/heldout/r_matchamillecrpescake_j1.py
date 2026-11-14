import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of matcha mille crêpes cake: vpip 0.19 pfr 0.12 3b 0.06 af 0.37 ftb 0.39 (16000 hands)
    PARAMS = {'open': 0.193, 'threebet': 0.067, 'call': 0.12, 'call_cap': 0.111, 'open_size': 3, 'limp': 0.0, 'cbet': 0.595, 'bluff': 0.158, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.275}
