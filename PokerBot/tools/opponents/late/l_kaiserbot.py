import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of kaiserbot: vpip 0.30 pfr 0.22 3b 0.05 af 0.82 ftb 0.41 (1000 hands)
    PARAMS = {'open': 0.276, 'threebet': 0.065, 'call': 0.154, 'call_cap': 0.3, 'open_size': 3.5, 'limp': 0.0, 'cbet': 0.94, 'bluff': 0.56, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 0.7, 'semibluff': 0.8}
