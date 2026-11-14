import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of munchlax: vpip 0.17 pfr 0.08 3b 0.03 af 0.21 ftb 0.56 (2000 hands)
    PARAMS = {'open': 0.097, 'threebet': 0.042, 'call': 0.13, 'call_cap': 0.3, 'open_size': 3.4, 'limp': 0.0, 'cbet': 0.45, 'bluff': 0.01, 'bet_min': 3, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.21}
