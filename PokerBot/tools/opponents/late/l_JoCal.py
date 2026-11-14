import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of JoCal: vpip 0.13 pfr 0.10 3b 0.02 af 0.38 ftb 0.55 (1000 hands)
    PARAMS = {'open': 0.13, 'threebet': 0.035, 'call': 0.069, 'call_cap': 0.15, 'open_size': 3.0, 'limp': 0.0, 'cbet': 0.76, 'bluff': 0.16, 'bet_min': 2, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.38}
