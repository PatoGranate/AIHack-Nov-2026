import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of gamblerlove: vpip 0.17 pfr 0.13 3b 0.05 af 0.42 ftb 0.40 (17000 hands)
    PARAMS = {'open': 0.187, 'threebet': 0.05, 'call': 0.082, 'call_cap': 0.115, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.519, 'bluff': 0.156, 'bet_min': 1, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.538}
