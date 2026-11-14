import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of gamblerlove: vpip 0.17 pfr 0.13 3b 0.05 af 0.42 ftb 0.40 (17000 hands)
    PARAMS = {'open': 0.162, 'threebet': 0.067, 'call': 0.096, 'call_cap': 0.15, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.67, 'bluff': 0.2, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.42}
