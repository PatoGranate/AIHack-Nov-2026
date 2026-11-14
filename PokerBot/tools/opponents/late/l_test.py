import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of test: vpip 0.17 pfr 0.09 3b 0.04 af 0.17 ftb 0.48 (2000 hands)
    PARAMS = {'open': 0.117, 'threebet': 0.051, 'call': 0.12, 'call_cap': 0.15, 'open_size': 2.8, 'limp': 0.0, 'cbet': 0.87, 'bluff': 0.0, 'bet_min': 3, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.17}
