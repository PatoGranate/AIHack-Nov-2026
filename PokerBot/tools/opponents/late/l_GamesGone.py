import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of GamesGone: vpip 0.26 pfr 0.17 3b 0.01 af 0.55 ftb 0.37 (1000 hands)
    PARAMS = {'open': 0.21, 'threebet': 0.022, 'call': 0.119, 'call_cap': 0.3, 'open_size': 2.2, 'limp': 0.0, 'cbet': 0.82, 'bluff': 0.32, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 0.7, 'semibluff': 0.55}
