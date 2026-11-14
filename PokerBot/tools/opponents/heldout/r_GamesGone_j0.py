import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of GamesGone: vpip 0.27 pfr 0.17 3b 0.03 af 0.51 ftb 0.42 (16000 hands)
    PARAMS = {'open': 0.2, 'threebet': 0.049, 'call': 0.189, 'call_cap': 0.345, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.614, 'bluff': 0.229, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 1.0, 'semibluff': 0.503}
