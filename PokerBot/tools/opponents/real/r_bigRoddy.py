import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of bigRoddy: vpip 0.30 pfr 0.20 3b 0.18 af 0.33 ftb 0.51 (18000 hands)
    PARAMS = {'open': 0.253, 'threebet': 0.21, 'call': 0.236, 'call_cap': 0.3, 'open_size': 3, 'limp': 0.0, 'cbet': 0.59, 'bluff': 0.12, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.33}
