import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of AIl IN: vpip 0.22 pfr 0.13 3b 0.07 af 0.29 ftb 0.30 (16000 hands)
    PARAMS = {'open': 0.161, 'threebet': 0.107, 'call': 0.172, 'call_cap': 0.236, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.518, 'bluff': 0.09, 'bet_min': 2, 'call_min': 0, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.308}
