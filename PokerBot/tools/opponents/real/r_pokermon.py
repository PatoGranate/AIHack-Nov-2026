import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of pokermon: vpip 0.25 pfr 0.16 3b 0.07 af 0.50 ftb 0.61 (16000 hands)
    PARAMS = {'open': 0.205, 'threebet': 0.084, 'call': 0.181, 'call_cap': 0.3, 'open_size': 3.0, 'limp': 0.0, 'cbet': 0.68, 'bluff': 0.27, 'bet_min': 1, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.5}
