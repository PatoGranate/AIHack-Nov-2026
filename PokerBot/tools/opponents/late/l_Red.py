import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Red: vpip 0.28 pfr 0.20 3b 0.04 af 0.79 ftb 0.35 (4000 hands)
    PARAMS = {'open': 0.248, 'threebet': 0.054, 'call': 0.141, 'call_cap': 0.3, 'open_size': 3.5, 'limp': 0.0, 'cbet': 0.95, 'bluff': 0.54, 'bet_min': 1, 'call_min': 2, 'raise_min': 3, 'bet_frac': 0.7, 'semibluff': 0.79}
