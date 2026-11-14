import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Peanut Cookies: vpip 0.18 pfr 0.12 3b 0.05 af 0.30 ftb 0.42 (12000 hands)
    PARAMS = {'open': 0.154, 'threebet': 0.068, 'call': 0.112, 'call_cap': 0.15, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.45, 'bluff': 0.09, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.3}
