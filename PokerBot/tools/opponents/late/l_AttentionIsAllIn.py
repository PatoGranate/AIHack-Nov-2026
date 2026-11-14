import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Attention Is All In: vpip 0.25 pfr 0.18 3b 0.11 af 0.39 ftb 0.38 (2000 hands)
    PARAMS = {'open': 0.221, 'threebet': 0.128, 'call': 0.199, 'call_cap': 0.3, 'open_size': 2.7, 'limp': 0.0, 'cbet': 0.76, 'bluff': 0.17, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.39}
