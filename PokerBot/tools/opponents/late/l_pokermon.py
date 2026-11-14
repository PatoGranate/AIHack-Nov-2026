import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of pokermon: vpip 0.23 pfr 0.15 3b 0.05 af 0.46 ftb 0.51 (1000 hands)
    PARAMS = {'open': 0.188, 'threebet': 0.067, 'call': 0.142, 'call_cap': 0.3, 'open_size': 3.2, 'limp': 0.0, 'cbet': 0.72, 'bluff': 0.24, 'bet_min': 1, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.46}
