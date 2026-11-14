import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Astra La Vista: vpip 0.20 pfr 0.13 3b 0.06 af 0.44 ftb 0.42 (3000 hands)
    PARAMS = {'open': 0.162, 'threebet': 0.074, 'call': 0.137, 'call_cap': 0.15, 'open_size': 2.9, 'limp': 0.0, 'cbet': 0.77, 'bluff': 0.21, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.7, 'semibluff': 0.44}
