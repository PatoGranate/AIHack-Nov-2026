import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Equity Engine: vpip 0.26 pfr 0.18 3b 0.03 af 0.41 ftb 0.48 (19000 hands)
    PARAMS = {'open': 0.226, 'threebet': 0.048, 'call': 0.137, 'call_cap': 0.3, 'open_size': 3.6, 'limp': 0.0, 'cbet': 0.71, 'bluff': 0.19, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.41}
