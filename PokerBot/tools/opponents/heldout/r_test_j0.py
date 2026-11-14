import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of test: vpip 0.15 pfr 0.08 3b 0.02 af 0.22 ftb 0.69 (13000 hands)
    PARAMS = {'open': 0.099, 'threebet': 0.028, 'call': 0.08, 'call_cap': 0.13, 'open_size': 3.1, 'limp': 0.0, 'cbet': 0.437, 'bluff': 0.016, 'bet_min': 3, 'call_min': 3, 'raise_min': 4, 'bet_frac': 0.6, 'semibluff': 0.171}
