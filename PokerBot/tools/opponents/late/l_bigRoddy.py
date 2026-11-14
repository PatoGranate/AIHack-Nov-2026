import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of bigRoddy: vpip 0.17 pfr 0.12 3b 0.05 af 0.40 ftb 0.47 (2000 hands)
    PARAMS = {'open': 0.151, 'threebet': 0.06, 'call': 0.097, 'call_cap': 0.15, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.57, 'bluff': 0.18, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.4}
