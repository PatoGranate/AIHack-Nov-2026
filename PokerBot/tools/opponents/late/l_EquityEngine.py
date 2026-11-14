import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Equity Engine: vpip 0.23 pfr 0.16 3b 0.03 af 0.32 ftb 0.50 (1000 hands)
    PARAMS = {'open': 0.198, 'threebet': 0.043, 'call': 0.115, 'call_cap': 0.15, 'open_size': 3.5, 'limp': 0.0, 'cbet': 0.6, 'bluff': 0.11, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.32}
