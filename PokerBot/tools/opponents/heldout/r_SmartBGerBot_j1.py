import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of SmartBGerBot: vpip 0.13 pfr 0.09 3b 0.03 af 0.27 ftb 0.45 (14000 hands)
    PARAMS = {'open': 0.123, 'threebet': 0.037, 'call': 0.054, 'call_cap': 0.173, 'open_size': 3.1, 'limp': 0.0, 'cbet': 0.595, 'bluff': 0.05, 'bet_min': 2, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.276}
