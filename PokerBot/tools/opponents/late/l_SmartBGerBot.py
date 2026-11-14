import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of SmartBGerBot: vpip 0.14 pfr 0.10 3b 0.03 af 0.26 ftb 0.38 (2000 hands)
    PARAMS = {'open': 0.128, 'threebet': 0.043, 'call': 0.069, 'call_cap': 0.15, 'open_size': 3.1, 'limp': 0.0, 'cbet': 0.44, 'bluff': 0.05, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.26}
