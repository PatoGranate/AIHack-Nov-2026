import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of JoCal: vpip 0.17 pfr 0.13 3b 0.02 af 0.27 ftb 0.45 (3000 hands)
    PARAMS = {'open': 0.164, 'threebet': 0.037, 'call': 0.086, 'call_cap': 0.15, 'open_size': 3.0, 'limp': 0.0, 'cbet': 0.59, 'bluff': 0.07, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.27}
