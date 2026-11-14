import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Poké Bot: vpip 0.24 pfr 0.18 3b 0.04 af 0.34 ftb 0.43 (14000 hands)
    PARAMS = {'open': 0.22, 'threebet': 0.048, 'call': 0.15, 'call_cap': 0.146, 'open_size': 3.1, 'limp': 0.0, 'cbet': 0.599, 'bluff': 0.096, 'bet_min': 2, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.4, 'semibluff': 0.352}
