import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Jump Street: vpip 0.16 pfr 0.12 3b 0.04 af 0.32 ftb 0.42 (1000 hands)
    PARAMS = {'open': 0.147, 'threebet': 0.051, 'call': 0.1, 'call_cap': 0.15, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.55, 'bluff': 0.1, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.32}
