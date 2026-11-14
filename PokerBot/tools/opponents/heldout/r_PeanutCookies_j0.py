import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Peanut Cookies: vpip 0.18 pfr 0.12 3b 0.05 af 0.30 ftb 0.42 (12000 hands)
    PARAMS = {'open': 0.118, 'threebet': 0.084, 'call': 0.114, 'call_cap': 0.125, 'open_size': 2.6, 'limp': 0.0, 'cbet': 0.4, 'bluff': 0.112, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.359}
