import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Attention Is All In: vpip 0.27 pfr 0.19 3b 0.08 af 0.48 ftb 0.57 (18000 hands)
    PARAMS = {'open': 0.233, 'threebet': 0.097, 'call': 0.184, 'call_cap': 0.3, 'open_size': 2.8, 'limp': 0.0, 'cbet': 0.64, 'bluff': 0.26, 'bet_min': 1, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.48}
