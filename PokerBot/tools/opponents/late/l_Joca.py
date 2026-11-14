import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Joca: vpip 0.18 pfr 0.11 3b 0.05 af 0.28 ftb 0.28 (2000 hands)
    PARAMS = {'open': 0.134, 'threebet': 0.064, 'call': 0.125, 'call_cap': 0.15, 'open_size': 6, 'limp': 0.0, 'cbet': 0.38, 'bluff': 0.07, 'bet_min': 2, 'call_min': 1, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.28}
