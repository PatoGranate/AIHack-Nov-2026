import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of supernut: vpip 0.15 pfr 0.13 3b 0.08 af 0.34 ftb 0.31 (1000 hands)
    PARAMS = {'open': 0.158, 'threebet': 0.098, 'call': 0.119, 'call_cap': 0.15, 'open_size': 2.5, 'limp': 0.0, 'cbet': 0.64, 'bluff': 0.13, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.34}
