import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Red: vpip 0.21 pfr 0.14 3b 0.04 af 0.62 ftb 0.46 (35000 hands)
    PARAMS = {'open': 0.144, 'threebet': 0.057, 'call': 0.132, 'call_cap': 0.13, 'open_size': 3, 'limp': 0.0, 'cbet': 0.95, 'bluff': 0.392, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 0.4, 'semibluff': 0.657}
