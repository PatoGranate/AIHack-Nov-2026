import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import ParamBot


class Agent(ParamBot):
    # clone of Claudebot: vpip 0.20 pfr 0.15 3b 0.03 af 0.35 ftb 0.43 (18000 hands)
    PARAMS = {'open': 0.234, 'threebet': 0.035, 'call': 0.102, 'call_cap': 0.174, 'open_size': 3, 'limp': 0.0, 'cbet': 0.514, 'bluff': 0.111, 'bet_min': 3, 'call_min': 2, 'raise_min': 4, 'bet_frac': 0.75, 'semibluff': 0.414}
