import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Mohil'sPokerBot: vpip 0.24 pfr 0.18 3b 0.14 af 0.52 ftb 0.48 (12000 hands)
    PARAMS = {'open': 0.249, 'threebet': 0.193, 'call': 0.17, 'call_cap': 0.307, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.656, 'bluff': 0.315, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 0.4, 'semibluff': 0.584}
