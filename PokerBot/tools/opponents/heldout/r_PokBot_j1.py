import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Poké Bot: vpip 0.24 pfr 0.18 3b 0.04 af 0.34 ftb 0.43 (14000 hands)
    PARAMS = {'open': 0.26, 'threebet': 0.061, 'call': 0.143, 'call_cap': 0.132, 'open_size': 3.1, 'limp': 0.0, 'cbet': 0.869, 'bluff': 0.15, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.319}
